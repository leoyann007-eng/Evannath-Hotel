/**
 * Le chatbot du site : un concierge qui repond aux visiteurs, en francais ou
 * en anglais, et passe la main a la reception quand il ne sait pas.
 *
 *   POST /api/chat   { messages: [{ role: 'user'|'assistant', text }], langue }
 *   ->               { ok, texte, actions: [{ type, url, libelle }] }
 *
 * CE QU'IL SAIT, ET D'OU :
 *   - le texte des pages publiques du site (api/_chatbot.json, ecrit par
 *     build-chatbot.py). Rien d'autre : un chatbot qui invente un horaire ou
 *     un tarif fait plus de tort que pas de chatbot ;
 *   - en direct, par ses outils : les disponibilites et les prix du jour
 *     (memes regles que les pages : api/admin.js, api/_tarif.js), et les
 *     offres publiees depuis l'administration.
 *
 * CE QU'IL NE FAIT PAS : reserver ou encaisser. Il ouvre la page Reserver,
 * dates et chambre deja remplies, ou WhatsApp, resume deja ecrit. Le client
 * finit toujours lui-meme, sur une page qui affiche le vrai prix.
 *
 * LA CONVERSATION VIT DANS LE NAVIGATEUR. Le serveur ne garde rien : chaque
 * appel renvoie tout l'historique, en texte seul. Les blocs de reflexion du
 * modele ne quittent jamais cette fonction, ce qui les met hors de portee
 * d'une modification cote client.
 *
 * Sans ANTHROPIC_API_KEY, le chatbot repond 503 « hors-ligne » : la bulle
 * propose alors WhatsApp, rien ne casse.
 */
const Anthropic = require('@anthropic-ai/sdk');
const tarif = require('./_tarif.js');
const admin = require('./admin.js');
const CHATBOT = require('./_chatbot.json');

const MODELE = 'claude-opus-5-5';
/* Au plus : 30 tours d'historique, 1 500 signes par message, 5 allers-
   retours d'outils par reponse. Au-dela, la conversation n'est plus une
   question de visiteur. */
const TOURS_MAX = 30, SIGNES_MAX = 1500, OUTILS_MAX = 5;

/* Un visiteur tape vite ; un robot tape tres vite. 20 questions par
   tranche de 10 minutes et par adresse, sur cette instance. */
const FENETRE = 10 * 60 * 1000, PLAFOND = 20;
const VUS = new Map();
function tropVite(ip) {
  const t = Date.now();
  const l = (VUS.get(ip) || []).filter((x) => t - x < FENETRE);
  l.push(t); VUS.set(ip, l);
  if (VUS.size > 1000) for (const [k, v] of VUS) if (!v.some((x) => t - x < FENETRE)) VUS.delete(k);
  return l.length > PLAFOND;
}

const CATEGORIES = Object.entries(tarif.GRILLE.chambres)
  .map(([slug, c]) => ({ slug, nom: c.nom, max: c.max }));
const NOM = Object.fromEntries(CATEGORIES.map((c) => [c.slug, c.nom]));
const ISO = /^\d{4}-\d{2}-\d{2}$/;
const fcfa = (n) => Number(n).toLocaleString('fr-FR').replace(/\s/g, ' ') + ' FCFA';

/* ── La consigne ─────────────────────────────────────────────────────────
   Elle ne change qu'avec le site : c'est le prefixe mis en cache. La date
   du jour vient APRES, dans un second bloc, pour ne pas le casser. */
const CONSIGNE = `Tu es le concierge en ligne de l'Hôtel Evannath, à Assinie (Côte d'Ivoire), sur le site de l'hôtel. Tu réponds aux visiteurs qui préparent un séjour.

Ta règle première : tu ne dis que ce que le site dit. Tes seules sources sont les pages du site ci-dessous et les résultats de tes outils. Si une information n'y figure pas — un horaire, un prix, un service, une politique —, dis simplement que tu ne l'as pas et propose de passer la main à la réception (outil passer_a_la_reception). N'invente jamais, n'arrondis pas, ne suppose pas.

Les prix et les disponibilités changent : pour une disponibilité ou un prix à des dates données, appelle toujours consulter_disponibilites ; les prix écrits dans les pages peuvent être dépassés. Pour les promotions, événements et offres saisonnières du moment, appelle offres_du_moment. Donne les dates au visiteur sous une forme lisible (« du vendredi 3 au dimanche 5 octobre »).

Quand le visiteur veut réserver, ou qu'une chambre libre correspond à sa demande, appelle proposer_reservation : un bouton ouvre la page de réservation déjà remplie. Tu ne prends pas de réservation et n'encaisses rien toi-même ; l'acompte de 30 % se règle sur cette page. Quand tu ne sais pas, quand la demande sort de ton rôle (groupe, séminaire, réclamation, demande particulière), ou quand le visiteur veut parler à quelqu'un, appelle passer_a_la_reception avec un résumé utile de sa demande.

Style : réponds dans la langue du visiteur (français ou anglais). Sois chaleureux, précis et bref — trois à six phrases le plus souvent. Pas de titres, pas de tableaux, pas de liens écrits dans le texte : les boutons s'affichent d'eux-mêmes sous ta réponse. Tu peux mettre en gras un prix ou une date avec **ainsi**. Ne répète pas la question. Si le visiteur parle d'autre chose que l'hôtel et son séjour, ramène poliment la conversation au séjour.

Les catégories de chambres, et leur identifiant pour les outils :
${CATEGORIES.map((c) => `- ${c.nom} : « ${c.slug} » (${c.max} personne${c.max > 1 ? 's' : ''} au plus)`).join('\n')}

Les pages du site :

${CHATBOT.savoir}`;

/* ── Les outils ───────────────────────────────────────────────────────── */
const OUTILS = [
  {
    name: 'consulter_disponibilites',
    description: "Disponibilité et prix réels d'une ou de toutes les catégories de chambres, pour un séjour. "
      + "Sans dates, rend seulement les prix de la nuit en vigueur (promotion comprise). Avec les dates, rend "
      + "pour chaque catégorie : libre, dernière chambre, complet, ou inconnu (la réception confirme alors sous 24 h), "
      + "et le total du séjour si le nombre de personnes est donné.",
    input_schema: {
      type: 'object',
      properties: {
        categorie: { type: 'string', enum: CATEGORIES.map((c) => c.slug), description: 'Omettre pour toutes les catégories.' },
        arrivee: { type: 'string', description: "Date d'arrivée, AAAA-MM-JJ." },
        depart: { type: 'string', description: 'Date de départ, AAAA-MM-JJ.' },
        personnes: { type: 'integer', minimum: 1, maximum: 12 },
      },
      additionalProperties: false,
    },
  },
  {
    name: 'offres_du_moment',
    description: "Les promotions en cours, les événements à venir et les offres saisonnières publiés aujourd'hui par l'hôtel.",
    input_schema: { type: 'object', properties: {}, additionalProperties: false },
  },
  {
    name: 'proposer_reservation',
    description: 'Affiche sous ta réponse un bouton qui ouvre la page de réservation du site, catégorie, dates et voyageurs déjà remplis.',
    input_schema: {
      type: 'object',
      properties: {
        categorie: { type: 'string', enum: CATEGORIES.map((c) => c.slug) },
        arrivee: { type: 'string', description: 'AAAA-MM-JJ' },
        depart: { type: 'string', description: 'AAAA-MM-JJ' },
        personnes: { type: 'integer', minimum: 1, maximum: 12 },
      },
      required: ['categorie'],
      additionalProperties: false,
    },
  },
  {
    name: 'passer_a_la_reception',
    description: "Affiche sous ta réponse un bouton WhatsApp vers la réception, avec un message déjà écrit qui résume la demande du visiteur.",
    input_schema: {
      type: 'object',
      properties: {
        resume: { type: 'string', description: 'Le message que le visiteur enverra, à la première personne, dans sa langue : sa demande, ses dates, le nombre de personnes si connus. 400 signes au plus.' },
      },
      required: ['resume'],
      additionalProperties: false,
    },
  },
];

function aujourdhui() { return new Date().toISOString().slice(0, 10); }

/** Chaque outil rend un objet JSON ; `actions` recoit les boutons a afficher. */
async function executer(nom, e, actions, langue) {
  const en = langue === 'en';
  if (nom === 'consulter_disponibilites') {
    const d = await admin.chatbot.lire();
    if (admin.chatbot.panne()) return { erreur: 'Les disponibilités sont momentanément illisibles. Propose la réception.' };
    const promos = d.promotions || [];
    const cats = e.categorie ? CATEGORIES.filter((c) => c.slug === e.categorie) : CATEGORIES;
    const avecDates = !!(e.arrivee || e.depart);
    if (avecDates && (!ISO.test(e.arrivee || '') || !ISO.test(e.depart || '') || e.depart <= e.arrivee)) {
      return { erreur: "Dates invalides : il faut une arrivée et un départ, au format AAAA-MM-JJ, départ après l'arrivée." };
    }
    if (avecDates && e.arrivee < aujourdhui()) return { erreur: "L'arrivée est dans le passé." };
    const rendu = cats.map((c) => {
      const plein = tarif.prixDe(c.slug, d.tarifs);
      const promo = tarif.promotionDuJour(promos, Date.now());
      const nuit = tarif.prixRemise(plein, c.slug, promo);
      const o = { categorie: c.nom, identifiant: c.slug, personnes_max: c.max, prix_nuit: fcfa(nuit) };
      if (nuit !== plein) { o.prix_nuit_sans_promotion = fcfa(plein); o.promotion = promo.titre || 'Promotion en cours'; }
      if (avecDates) {
        const etat = admin.chatbot.etatDe(d, c.slug, e.arrivee, e.depart);
        o.disponibilite = {
          libre: 'disponible', derniere: 'disponible, dernière chambre', complet: 'complet à ces dates',
          inconnu: 'non connue en ligne : la réception confirme sous 24 h',
        }[etat] || etat;
        if (e.personnes) {
          const q = tarif.devis({ categorie: c.slug, du: e.arrivee, au: e.depart, pax: e.personnes }, promos, Date.now(), d.tarifs);
          if (q.ok) {
            o.sejour = { nuits: q.nuits, total: fcfa(q.total), dont_taxe_de_sejour: fcfa(q.taxe), acompte_30_pourcent: fcfa(q.acompte) };
          } else if (q.raison === 'personnes') {
            o.sejour = `trop de personnes pour cette catégorie (${c.max} au plus)`;
          } else if (q.raison === 'duree') {
            o.sejour = 'séjour de plus de 30 nuits : à voir avec la réception';
          }
        }
      }
      return o;
    });
    return { date_du_jour: aujourdhui(), categories: rendu,
      rappel: 'Petit-déjeuner et navette aéroport compris. Taxe de séjour : 1 500 FCFA par personne et par nuit.' };
  }

  if (nom === 'offres_du_moment') {
    const d = await admin.chatbot.lire();
    if (admin.chatbot.panne()) return { erreur: 'Offres momentanément illisibles.' };
    const p = admin.chatbot.publiees(d, Date.now());
    const auj = aujourdhui();
    const remise = (r) => (!r || !r.valeur ? '' : r.type === 'montant' ? '-' + fcfa(r.valeur) + ' par nuit' : '-' + r.valeur + ' %');
    return {
      promotions: p.promotions.map((x) => ({ titre: x.titre, remise: remise(x.remise), texte: x.texte,
        chambres: !x.cible || x.cible.toutes !== false ? 'toutes' : (x.cible.chambres || []).map((s) => NOM[s] || s),
        jusqu_au: x.fin || null })),
      evenements: p.evenements.filter((x) => !x.fin || x.fin >= auj)
        .map((x) => ({ titre: [x.titre, x.accent].filter(Boolean).join(' '), quand: x.quand, texte: x.texte })),
      offres_saisonnieres: p.campagnes.map((x) => ({ titre: x.titre, accroche: x.accroche, jusqu_au: x.fin || null,
        packs: (x.packs || []).filter((k) => k.nom).map((k) => ({ nom: k.nom, prix: k.prix ? fcfa(k.prix) + (k.unite ? ' ' + k.unite : '') : '' })) })),
    };
  }

  if (nom === 'proposer_reservation') {
    if (!NOM[e.categorie]) return { erreur: 'Catégorie inconnue.' };
    const q = new URLSearchParams({ chambre: e.categorie });
    if (ISO.test(e.arrivee || '') && ISO.test(e.depart || '') && e.depart > e.arrivee) { q.set('du', e.arrivee); q.set('au', e.depart); }
    if (Number.isInteger(e.personnes)) q.set('pax', String(e.personnes));
    actions.push({ type: 'reserver', url: '/reserver?' + q.toString(),
      libelle: (en ? 'Book — ' : 'Réserver — ') + NOM[e.categorie] });
    return { ok: true, bouton: 'affiché' };
  }

  if (nom === 'passer_a_la_reception') {
    const texte = String(e.resume || '').slice(0, 400);
    actions.push({ type: 'whatsapp', url: 'https://wa.me/' + CHATBOT.whatsapp + '?text=' + encodeURIComponent(texte),
      libelle: en ? 'Continue on WhatsApp with reception' : 'Continuer avec la réception sur WhatsApp' });
    return { ok: true, bouton: 'affiché' };
  }
  return { erreur: 'Outil inconnu.' };
}

/* ── La conversation ─────────────────────────────────────────────────── */
function nettoyer(messages) {
  const l = (Array.isArray(messages) ? messages : [])
    .filter((m) => m && (m.role === 'user' || m.role === 'assistant') && typeof m.text === 'string' && m.text.trim())
    .map((m) => ({ role: m.role, content: m.text.trim().slice(0, SIGNES_MAX) }))
    .slice(-TOURS_MAX);
  // L'API veut commencer par le visiteur, et finir sur sa question.
  while (l.length && l[0].role !== 'user') l.shift();
  return l.length && l[l.length - 1].role === 'user' ? l : null;
}

/* La page que le visiteur a sous les yeux. Sur la fiche de la Suite Arabe,
   « elle est libre ce week-end ? » parle de la Suite Arabe : le modele doit
   le savoir sans redemander. Seul le chemin est accepte, jamais un texte
   libre venu du navigateur. */
const PAGES = {
  '': 'Accueil', chambres: 'Chambres & Suites (liste des sept catégories)', carte: 'La table (restaurant)',
  spa: 'Le spa', experiences: 'Expériences', circuits: 'Offres & Événements', seminaires: 'Séminaires & groupes',
  galerie: 'Galerie', 'a-propos': 'À propos', 'informations-utiles': 'Informations utiles', contact: 'Contact',
  reserver: 'Réserver (le tunnel de réservation)',
};
function contextePage(chemin) {
  const p = String(chemin || '').toLowerCase();
  if (!/^\/[a-z0-9-]*(\.html)?$/.test(p)) return '';
  const slug = p.slice(1).replace(/\.html$/, '').replace(/^index$/, '');
  if (NOM[slug]) {
    return ` Le visiteur lit la fiche de la ${NOM[slug]} (identifiant « ${slug} ») : « cette chambre », « elle », « celle-ci » désignent la ${NOM[slug]}.`;
  }
  return PAGES[slug] !== undefined ? ` Le visiteur lit la page « ${PAGES[slug]} ».` : '';
}

/* L'interrupteur du back-office (Parametres) : d.reglages.chatbot.actif.
   Absent, le chatbot est allume. Une lecture du magasin en panne ne
   l'eteint pas : on ne coupe pas le concierge parce que le stockage a
   hoquete. */
async function allume() {
  try {
    const d = await admin.chatbot.lire();
    return !(d && d.reglages && d.reglages.chatbot && d.reglages.chatbot.actif === false);
  } catch (e) { return true; }
}
const cle = () => !!(process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_AUTH_TOKEN);

/** Une reponse complete : le texte, et les boutons. `surTexte`, s'il est
 *  donne, recoit le texte au fil de l'ecriture (flux). */
async function converser({ messages, langue, page, surTexte }) {
  /* Une cle creee au niveau de l'organisation, et non dans un espace de
     travail (workspace), doit dire quel espace utiliser. ANTHROPIC_WORKSPACE_ID
     le donne ; une cle creee DANS un espace n'en a pas besoin. */
  const espace = process.env.ANTHROPIC_WORKSPACE_ID;
  const client = new Anthropic.Anthropic(espace ? { defaultHeaders: { 'anthropic-workspace-id': espace } } : {});
  const actions = [];
  const jour = new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Africa/Abidjan' });
  const system = [
    { type: 'text', text: CONSIGNE, cache_control: { type: 'ephemeral' } },
    { type: 'text', text: `Aujourd'hui : ${jour} (${aujourdhui()}). La page du visiteur est en ${langue === 'en' ? 'anglais' : 'français'}.${contextePage(page)}` },
  ];
  /* En flux, les outils recoivent leurs arguments au fil de l'ecriture
     (eager_input_streaming) ; le serveur ne les valide plus, executer() le
     fait : categorie connue, dates au bon format, texte tronque. */
  const outils = surTexte ? OUTILS.map((o) => ({ ...o, eager_input_streaming: true })) : OUTILS;

  let reponse;
  /* Tout le texte ecrit par le modele, a chaque tour : il repond souvent
     AVANT d'appeler un outil (« Nous n'acceptons pas les animaux ; pour
     le tennis, je vous mets en relation… »), puis n'ecrit plus rien
     apres. Ne garder que le dernier tour rendait une bulle vide. */
  const textes = [];
  let ecrit = false;
  const question = messages[messages.length - 1].content;
  for (let tour = 0; tour <= OUTILS_MAX; tour++) {
    const params = {
      model: MODELE,
      max_tokens: 4000,
      /* Une conversation de concierge n'a pas besoin de reflechir
         longtemps : effort bas, reponse en quelques secondes. */
      output_config: { effort: 'low' },
      /* Si le modele decline une demande (filtre de securite), l'API la
         rejoue d'elle-meme sur le modele de secours adapte. */
      betas: ['server-side-fallback-2026-07-01'],
      fallbacks: 'default',
      system,
      tools: outils,
      messages,
    };
    if (surTexte) {
      const flux = client.beta.messages.stream(params);
      let debut = true;
      flux.on('text', (d) => {
        // Deux tours d'ecriture se separent d'une ligne vide, comme a l'ecran.
        if (debut && ecrit) surTexte('\n\n');
        debut = false; ecrit = true;
        surTexte(d);
      });
      reponse = await flux.finalMessage();
    } else {
      reponse = await client.beta.messages.create(params);
    }
    for (const b of reponse.content) if (b.type === 'text' && b.text.trim()) textes.push(b.text.trim());
    if (reponse.stop_reason !== 'tool_use') break;
    /* Le tour de l'assistant est renvoye TEL QUEL (reflexion comprise) :
       dans une meme reponse, l'historique ne fait que s'allonger. */
    messages.push({ role: 'assistant', content: reponse.content });
    const resultats = [];
    for (const b of reponse.content) {
      if (b.type !== 'tool_use') continue;
      let r;
      try { r = await executer(b.name, (b.input && typeof b.input === 'object') ? b.input : {}, actions, langue); }
      catch (e) { r = { erreur: 'Outil indisponible.' }; }
      resultats.push({ type: 'tool_result', tool_use_id: b.id, content: JSON.stringify(r), ...(r.erreur ? { is_error: true } : {}) });
    }
    messages.push({ role: 'user', content: resultats });
  }

  let texte;
  if (reponse.stop_reason === 'refusal') {
    actions.length = 0;
    await executer('passer_a_la_reception', { resume: langue === 'en' ? 'Hello, I have a question about my stay.' : 'Bonjour, j\'ai une question sur mon séjour.' }, actions, langue);
    texte = langue === 'en' ? 'I can’t help with that here — our reception will be happy to answer you on WhatsApp.'
      : 'Je ne peux pas vous aider sur ce point ici — la réception vous répondra volontiers sur WhatsApp.';
  } else {
    texte = textes.join('\n\n').trim();
    if (!texte) {
      if (!actions.length) await executer('passer_a_la_reception', { resume: question.slice(0, 300) }, actions, langue);
      texte = langue === 'en' ? 'I’m not sure about that one — our reception will answer you on WhatsApp.'
        : 'Je préfère ne pas vous répondre au hasard — la réception vous répondra sur WhatsApp.';
    }
  }
  // Un bouton de chaque sorte, pas davantage : le dernier propose est le bon.
  const uniques = [];
  for (const a of actions.reverse()) if (!uniques.some((u) => u.type === a.type)) uniques.unshift(a);
  return { texte, actions: uniques };
}

/** Ce qu'on peut dire d'une erreur, sans rien de secret. */
function diagnostic(e) {
  const code = e instanceof Anthropic.RateLimitError ? 'surcharge' : e instanceof Anthropic.APIError ? 'ia' : 'erreur';
  console.error('chat', e && e.status, e && e.message);
  /* Le statut et le type d'erreur d'Anthropic (401 cle refusee, 400 credit
     epuise...) : ce qu'il faut pour savoir quoi corriger — la cle
     n'apparait jamais dans ces messages. */
  const detail = e instanceof Anthropic.APIError
    ? { statut: e.status, type: e.error && e.error.error && e.error.error.type,
        /* Oui ou non, jamais la valeur : la fonction voit-elle l'espace ? */
        espace_de_travail: !!process.env.ANTHROPIC_WORKSPACE_ID,
        message: String((e.error && e.error.error && e.error.error.message) || '').slice(0, 200) }
    : undefined;
  return { ok: false, raison: code, detail };
}

/** La requete du navigateur, verifiee. Rend soit { refus: { code, corps } }
 *  a renvoyer tel quel, soit ce qu'il faut pour converser. Aucune reponse
 *  HTTP ici : c'est api/chat.mjs qui l'ecrit (en flux ou non). */
async function preparer(corps, ip) {
  if (!cle()) return { refus: { code: 503, corps: { ok: false, raison: 'hors-ligne' } } };
  if (!(await allume())) return { refus: { code: 503, corps: { ok: false, raison: 'eteint' } } };
  if (tropVite(ip || 'inconnue')) return { refus: { code: 429, corps: { ok: false, raison: 'debit' } } };
  if (typeof corps === 'string') { try { corps = JSON.parse(corps); } catch { corps = {}; } }
  const langue = corps && corps.langue === 'en' ? 'en' : 'fr';
  const page = corps && typeof corps.page === 'string' ? corps.page.slice(0, 80) : '';
  const messages = nettoyer(corps && corps.messages);
  if (!messages) return { refus: { code: 422, corps: { ok: false, raison: 'message' } } };
  return { messages, langue, page, flux: !!(corps && corps.flux) };
}

/** GET : la bulle demande si elle doit s'afficher. Allume dans le
 *  back-office ET cle presente — sinon elle ne se montre pas du tout. */
async function etat() { return { ok: true, actif: cle() && await allume() }; }

module.exports = { preparer, converser, diagnostic, etat,
  // Pour les tests : la consigne et les outils, sans appel reseau.
  interne: { CONSIGNE, OUTILS, executer, nettoyer, contextePage } };
