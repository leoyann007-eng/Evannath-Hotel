/* ─────────────────────────────────────────────────────────────────────────
   Calendrier des disponibilités.

   Le calendrier n est jamais la source de vérité : il se calcule, en une
   passe, à partir de ETAT.chambres et ETAT.fermetures déjà chargés par
   charger(). Aucune requête par case. Les écritures passent par les routes
   existantes — enregistrer / supprimer une fermeture — et rien d autre.

   Mêmes règles que api/admin.js : les dates d une fermeture sont des NUITS,
   bornes incluses ; fin à null = sans date de fin. Un séjour arrivé le 24 et
   parti le 27 occupe les nuits du 24, du 25 et du 26 : fin = 26.

   `nature` distingue un séjour client ('client') d un blocage
   ('hors-service', 'vente'). Une fermeture plus ancienne, sans nature, reste
   une fermeture client : c est ce qu elle était.

   Ce fichier se charge après le script de la page, dont il emploie ETAT,
   appel, ech, $, AUJ, jourIso et FCFA.
   ───────────────────────────────────────────────────────────────────────── */
const DSP = { vue: 'mois', mode: 'calendrier', focus: null, ouvertes: {},
              tiroir: null, modal: null,
              voirTout: false, seuil: 0.3, defiler: true,
              f: { texte: '', cat: '', etage: '', statut: '', libres: false } };

/* La colonne d'une case et le bloc de gauche, tels que la feuille de style
   les pose. Ils ne servent plus a decider combien de jours afficher — le
   mois montre le mois, la semaine sept jours, le jour un — mais le test de
   largeur les verifie toujours. */
const DSP_COL = 34, DSP_LIB = 140;

/* Les glyphes des compteurs. Des caracteres, pas des images : le reste de
   l'administration fait deja ainsi, et une icone qui ne se telecharge pas
   laisse un carre vide au milieu d'un chiffre. */
const ICONES = { lit: '▤', ok: '✓', qui: '●', cal: '◱',
                 cle: '⚒', net: '✦' };
/* La vignette d'une categorie vient de donnees/chambres.json, donc de
   _chambres.py : c'est la premiere photo que le site montre sur sa fiche.
   La carte ecrite a la main qu'il y avait ici se trompait sur SIX categories
   sur sept — elle donnait a « Deluxe · lits a baldaquin » une photo de
   textiles wax, qui est celle de la Deluxe Superieure, et intervertissait
   les deux Mezzanines. Une carte recopiee diverge ; celle-ci se deduit. */
const DTON = { dispo: ['var(--et-libre)', 'Disponible'], faible: ['var(--et-res)', 'Peu de chambres'],
  complet: ['var(--et-bloq)', 'Complet'], hs: ['var(--et-hs)', 'Hors service'],
  inconnu: ['var(--et-hs)', 'Aucune chambre saisie'], libre: ['var(--et-libre)', 'Disponible'],
  occ: ['var(--et-occ)', 'Occupée'], res: ['var(--et-res)', 'Réservée'],
  vente: ['var(--et-bloq)', 'Bloquée'], net: ['var(--et-net)', 'Nettoyage'] };

/* DTON donne la couleur du TEXTE : elle sert aux pastilles, aux legendes et
   aux listes de choix, ou la couleur se pose sur le creme. DAPLAT donne le
   couple fond/texte des CASES du calendrier, qui sont des aplats pleins.
   Deux usages, deux tables — les melanger rendait l'un des deux illisible. */
const DAPLAT = { libre: ['var(--f-libre)', 'var(--t-libre)'],
  res: ['var(--f-res)', 'var(--t-res)'], occ: ['var(--f-occ)', 'var(--t-occ)'],
  vente: ['var(--f-bloq)', 'var(--t-bloq)'], net: ['var(--f-net)', 'var(--t-net)'],
  hs: ['var(--f-hs)', 'var(--t-hs)'], inconnu: ['var(--f-hs)', 'var(--t-hs)'] };

const jDt = (j) => new Date(j + 'T12:00:00');
const jPlus = (j, n) => { const d = jDt(j); d.setDate(d.getDate() + n); return jourIso(d); };
const jMaj = (s) => s.charAt(0).toUpperCase() + s.slice(1);
/* « 1 janvier » n'existe pas en francais : le premier du mois prend son
   rang. Le navigateur ne le sait pas, nous si. */
const rang = (t) => t.replace(/(^|\s)1(\s)/, '$11er$2');
const jCourt = (j) => rang(jDt(j).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }));
/* L'instant ou une retenue tombe. On dit l'heure, pas « dans 118 minutes » :
   la reception regarde sa pendule, pas un compte a rebours. */
const heureDe = (t) => {
  const d = new Date(t);
  if (isNaN(d)) return '';
  const auj = new Date();
  const memeJour = d.toDateString() === auj.toDateString();
  return (memeJour ? '' : jCourt(jourIso(d)) + ' a ')
    + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
};
/* Pas `perimee` : index.html declare deja une fonction de ce nom — le
   bandeau de page perimee. Deux scripts classiques partagent la meme
   portee globale, et la collision ne se voit qu'au navigateur. */
const retenueTombee = (f) => !!f.expire && Date.parse(f.expire) < Date.now();
/* Paiement en ligne refuse, interrompu, ou remplace par un nouvel essai du
   meme client : la chambre est rendue (voir vivante() dans api/admin.js).
   La trace reste dans les donnees, mais ne s'affiche plus comme un sejour. */
const paiementLache = (f) => f.statut !== 'confirmee' && !!f.paiement
  && ['echoue', 'abandonne', 'remplace'].includes(f.paiement.statut);
const jLong = (j) => jMaj(rang(jDt(j).toLocaleDateString('fr-FR',
  { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })));
const fCouvre = (f, n) => f.debut && f.debut <= n && (f.fin == null || f.fin >= n);
const fChevauche = (f, a, b) => f.debut && f.debut <= b && (f.fin == null || f.fin >= a);
const fVise = (f, ch) => f.cible === '*' || f.cible === ch.id || f.cible === ch.categorie;
const fClient = (f) => f.nature === 'client' || !f.nature;
const parNum = (a, b) => String(a.numero).localeCompare(String(b.numero), 'fr',
  { numeric: true, sensitivity: 'base' });

function dspIndex(F, chambres) {
  const ids = new Set(chambres.map((c) => c.id)), par = {}, larges = [];
  F.forEach((f) => {
    if (!f || !f.debut) return;
    if (ids.has(f.cible)) (par[f.cible] = par[f.cible] || []).push(f); else larges.push(f);
  });
  return { par, larges };
}

/** L état d une chambre, une nuit. Un séjour l emporte sur un blocage : si
    les deux se chevauchent, c est le client qu il faut voir. */
function dspEtat(ch, n, idx, auj) {
  if (ch.service === false) return { k: 'hs', motif: ch.note
    || (ch.statut === 'maintenance' ? 'Maintenance' : 'Hors service') };
  const l = (idx.par[ch.id] || []).concat(idx.larges.filter((f) => fVise(f, ch)));
  let bloc = null;
  for (const f of l) {
    if (!fCouvre(f, n)) continue;
    if (fClient(f)) {
      if (f.statut === 'annulee' || paiementLache(f)) continue;
      return { k: f.debut <= auj ? 'occ' : 'res', f };
    }
    bloc = bloc || f;
  }
  if (!bloc) return { k: 'libre' };
  /* Trois blocages qui ne se valent pas : une chambre bloquee a la vente se
     rouvre d'un clic, une chambre en nettoyage se reloue ce soir, une chambre
     hors service attend un reparateur. Les confondre faisait perdre a la
     reception la seule information qui l'interesse. */
  const k = bloc.nature === 'vente' ? 'vente'
    : bloc.nature === 'nettoyage' ? 'net' : 'hs';
  return { k, f: bloc };
}

/** Disponibles = chambres saisies − réservées − bloquées, par catégorie et
    par nuit. Rend aussi l état de chaque chambre, pour les lignes détaillées. */
function calculerDisponibilites(categories, chambres, F, jours, auj, seuil) {
  const idx = dspIndex(F, chambres), parCat = {}, parChambre = {};
  categories.forEach((c) => {
    parCat[c.slug] = {};
    const siennes = chambres.filter((ch) => ch.categorie === c.slug);
    siennes.forEach((ch) => { parChambre[ch.id] = {}; });
    jours.forEach((j) => {
      const x = { total: siennes.length, libres: 0, reserves: 0, hs: 0, vente: 0 };
      siennes.forEach((ch) => {
        const e = dspEtat(ch, j, idx, auj);
        parChambre[ch.id][j] = e;
        if (e.k === 'libre') x.libres++;
        else if (e.k === 'occ' || e.k === 'res') x.reserves++;
        else if (e.k === 'hs') x.hs++; else x.vente++;
      });
      x.bloques = x.hs + x.vente;
      x.etat = !x.total ? 'inconnu'
        : !x.libres ? ((!x.reserves && x.hs && !x.vente) ? 'hs' : 'complet')
        : (x.libres / x.total <= seuil ? 'faible' : 'dispo');
      parCat[c.slug][j] = x;
    });
  });
  return { parCat, parChambre };
}

function joursDsp() {
  const f = DSP.focus;
  if (DSP.vue === 'jour') return [f];
  if (DSP.vue === 'semaine') {
    const a = jPlus(f, -((jDt(f).getDay() + 6) % 7));
    return [0, 1, 2, 3, 4, 5, 6].map((i) => jPlus(a, i));
  }
  /* LE MOIS ENTIER, du premier au dernier jour.
     Avant, « mois » n'etait pas un mois : c'etait une fenetre glissante
     d'autant de jours qu'il en tenait a l'ecran — neuf ici, treize ailleurs,
     a partir du jour vise. On ne voyait donc jamais un mois, et le nombre de
     colonnes dependait de la largeur de la fenetre. */
  const d = jDt(f);
  const premier = jourIso(new Date(d.getFullYear(), d.getMonth(), 1));
  const combien = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
  return Array.from({ length: combien }, (_, i) => jPlus(premier, i));
}

const vignette = (slug) => {
  const c = (ETAT.categories || []).find((x) => x.slug === slug);
  return c && c.photo
    ? `<img class="vig" src="/img/opt/${c.photo}.jpg" alt="" loading="lazy">`
    : '<div class="vig"></div>';
};

function detailSejour(e) {
  if (e.f && fClient(e.f)) {
    return (e.f.client || e.f.motif || 'Fermeture') + ' · départ ' + jCourt(jPlus(e.f.fin, 1))
      + (e.f.statut === 'attente' ? ' · en attente' : '');
  }
  return (e.f ? e.f.motif : e.motif) || '';
}

/* ── Le calendrier ────────────────────────────────────────────────────
   LES LIGNES SONT DES CHAMBRES, pas des categories.

   La maquette precedente rangeait les chambres sous leur categorie,
   repliees derriere un « Details » : il fallait deux clics pour voir la
   chambre 25, et on ne voyait jamais deux categories a la fois. Une
   reception tient un cahier de numeros — on lui rend son cahier.

   Les categories ne disparaissent pas pour autant : chaque ligne porte la
   sienne, et le filtre du haut permet de s'y ramener.

   CE QU'ON NE REPREND PAS DE LA MAQUETTE, et pourquoi :

     - ses numeros de chambre (101, 102, 201...) : L'HOTEL NE NOUS LES A PAS
       ENCORE DONNES. L'ecran part donc vide, et le dit.
     - ses categories (Standard, Deluxe, Suite, Executive) et ses tarifs
       (45 000 F) : les vraies sont dans donnees/chambres.json, sept
       categories de 67 000 a 280 000 F.
     - « 1 lit king size » : une seule de nos sept categories declare son
       type de lit. Afficher les six autres serait inventer.
     - l'etage : personne ne nous l'a donne non plus. La colonne n'apparait
       que si au moins une chambre en porte un.
     - le statut « Nettoyage » : c'est de la gouvernante, un autre metier et
       un autre rythme. Une chambre restee sur « Nettoyage » depuis mardi
       dernier se vend comme indisponible sans que personne ne l'ait decide. */
/** Les nuits d'une chambre, regroupees en BLOCS.
 *
 *  Un sejour de trois nuits est UN sejour, pas trois cases identiques posees
 *  cote a cote. On relie donc les nuits consecutives qui portent la MEME
 *  fermeture, et on en fait un seul bloc qui porte le nom du client une fois.
 *
 *  Les nuits LIBRES restent distinctes : il n'y a rien a relier, et deux
 *  nuits libres cote a cote ne forment pas un evenement. C'est aussi ce qui
 *  permet de cliquer une nuit precise pour la reserver.
 *
 *  `n` est le nombre de nuits couvertes. La grille etant en flex, un bloc de
 *  n nuits prend n fois la base d'une case — voir --n dans la feuille. */
function blocsDe(ch, jours, calc) {
  const out = [];
  for (let i = 0; i < jours.length; i++) {
    const e = calc.parChambre[ch.id][jours[i]];
    let n = 1;
    if (e && e.f && e.f.id) {
      while (i + n < jours.length) {
        const suite = calc.parChambre[ch.id][jours[i + n]];
        if (!suite || !suite.f || suite.f.id !== e.f.id) break;
        n++;
      }
    }
    out.push({ e, jour: jours[i], n });
    i += n - 1;
  }
  return out;
}

/** LE MOIS : un calendrier mensuel, pas un planning.
 *
 *  A l'echelle du mois on ne cherche pas une chambre, on cherche un JOUR —
 *  « suis-je plein le 14 ? ». Une grille de quarante-six lignes ne repond
 *  pas a cette question : il faut la lire ligne a ligne et compter.
 *
 *  Chaque case porte donc le compte de la journee entiere : le taux
 *  d'occupation, une barre empilee, et les quatre etats. Les filtres
 *  s'appliquent aux compteurs — filtrer sur un etage montre le taux DE CET
 *  ETAGE, ce qui est exactement ce qu'on veut savoir.
 *
 *  Un clic sur un jour bascule en mode Jour sur cette date. */
function htmlMois(retenues, idx, auj) {
  const f = DSP.focus, d = jDt(f);
  const premier = new Date(d.getFullYear(), d.getMonth(), 1);
  const combien = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
  const moisVise = jourIso(premier).slice(0, 7);

  /* Les semaines vont du LUNDI au dimanche : on recule jusqu'au lundi qui
     precede ou ouvre le mois, et on avance par sept jusqu'a l'avoir couvert. */
  const debut = jPlus(jourIso(premier), -((premier.getDay() + 6) % 7));
  const dernier = jPlus(jourIso(premier), combien - 1);
  const cases = [];
  for (let j = debut; ; j = jPlus(j, 1)) {
    cases.push(j);
    if (j >= dernier && cases.length % 7 === 0) break;
    if (cases.length > 42) break;
  }

  const total = retenues.length;
  const jours = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    .map((n) => `<div class="m-jn">${n}</div>`).join('');

  const corps = cases.map((j) => {
    const dedans = j.slice(0, 7) === moisVise;
    const n = jDt(j).getDate();
    if (!dedans) return `<div class="m-c hors"><span class="m-n">${n}</span></div>`;

    let libres = 0, occ = 0, res = 0, indisp = 0;
    retenues.forEach((ch) => {
      const k = dspEtat(ch, j, idx, auj).k;
      if (k === 'libre') libres++;
      else if (k === 'occ') occ++;
      else if (k === 'res') res++;
      else indisp++;
    });
    const taux = total ? Math.round(((occ + res) / total) * 100) : 0;
    const pc = (v) => (total ? (v / total) * 100 : 0);

    return `<button class="m-c${j === auj ? ' auj' : ''}" data-dsp-jour="${j}"
      aria-label="${jLong(j)} : ${taux} % d'occupation, ${libres} libre${
        libres > 1 ? 's' : ''}">
      <div class="m-h"><span class="m-n">${n}</span><span class="m-t">${taux}&nbsp;%</span></div>
      <div class="m-b"><i style="width:${pc(occ)}%;background:var(--f-occ)"></i
        ><i style="width:${pc(res)}%;background:var(--f-res)"></i
        ><i style="width:${pc(indisp)}%;background:var(--f-hs)"></i></div>
      <div class="m-g">
        <span><i style="background:var(--f-libre)"></i>${libres} libres</span>
        <span><i style="background:var(--f-occ)"></i>${occ} occ.</span>
        <span><i style="background:var(--f-res)"></i>${res} rés.</span>
        <span><i style="background:var(--f-hs)"></i>${indisp} indisp.</span>
      </div></button>`;
  }).join('');

  return `<div class="dsp-mois">
      <div class="m-tete">${jours}</div>
      <div class="m-grille">${corps}</div>
      <p class="aide m-note">Le pourcentage est le taux d'occupation
        — occupées et réservées rapportées au total.
        <strong>Cliquez sur un jour pour l'ouvrir.</strong>${
        total ? '' : ' Aucune chambre ne correspond à ce filtre.'}</p>
    </div>`;
}

/** LE JOUR : des cartes, groupees par etage.
 *
 *  Une seule colonne de quarante-six lignes gaspillait toute la largeur de
 *  l'ecran. A l'echelle d'une journee on ne compare pas des dates : on fait
 *  le tour de l'hotel, etage par etage, comme la reception le fait a pied.
 *
 *  Chaque carte porte son etat en bandeau, et les deux echeances du jour —
 *  qui arrive, qui part demain. */
function htmlJour(retenues, idx, auj) {
  const j = DSP.focus;
  const nomCat = (slug) => ((ETAT.categories || []).find((c) => c.slug === slug) || {}).nom || slug;

  /* Par etage, dans l'ordre ou un humain les lit. Les chambres sans etage
     saisi se rassemblent a la fin plutot que de disparaitre. */
  const groupes = {};
  retenues.forEach((ch) => {
    const e = String(ch.etage || '');
    (groupes[e] = groupes[e] || []).push(ch);
  });
  const ordre = Object.keys(groupes).sort((a, b) => {
    if (!a) return 1;
    if (!b) return -1;
    return a.localeCompare(b, 'fr', { numeric: true });
  });

  if (!ordre.length) {
    return `<p class="aide" style="padding:28px 18px;margin:0">Aucune chambre ne
      correspond à ce filtre.</p>`;
  }

  return `<div class="dsp-jour">${ordre.map((et) => {
    const lot = groupes[et];
    const libres = lot.filter((ch) => dspEtat(ch, j, idx, auj).k === 'libre').length;
    return `<div class="j-groupe">
      <div class="j-tete"><span class="lb" style="margin:0">${
        et ? 'Étage ' + ech(et) : 'Étage non renseigné'}</span>
        <span class="aide" style="margin:0">${libres} libre${libres > 1 ? 's' : ''}
          sur ${lot.length}</span></div>
      <div class="j-cartes">${lot.map((ch) => {
        const e = dspEtat(ch, j, idx, auj);
        const [fond, encre] = DAPLAT[e.k] || DAPLAT.hs;
        const [, mot] = DTON[e.k];
        const f = e.f;
        /* Les nuits que couvre ce qui est pose, et les deux echeances du
           jour : une arrivee se prepare, un depart libere une chambre. */
        const nuits = f && f.debut
          ? (f.fin ? Math.round((jDt(f.fin) - jDt(f.debut)) / 86400000) + 1 : null)
          : null;
        const arrive = !!(f && f.nature === 'client' && f.debut === j);
        const part = !!(f && f.nature === 'client' && f.fin === j);
        const client = f && f.nature === 'client' ? (f.client || '—') : '';
        return `<button class="j-c" data-dsp-ch="${ech(ch.id)}" data-nuit="${j}"
          aria-label="Chambre ${ech(ch.numero)} : ${mot}">
          <span class="j-b" style="background:${fond};color:${encre}">${mot}${
            nuits ? `<em>${nuits} nuit${nuits > 1 ? 's' : ''}</em>` : ''}</span>
          <span class="j-n">${ech(ch.numero)}</span>
          <span class="j-cat">${ech(nomCat(ch.categorie))}</span>
          <span class="j-qui">${client ? ech(client) : 'Aucun client'}</span>
          ${f && f.debut ? `<span class="j-d">${jCourt(f.debut)}${
            f.fin ? ' → ' + jCourt(jPlus(f.fin, 1)) : ''}</span>` : ''}
          ${arrive ? '<span class="j-badge arrive">Arrivée aujourd\'hui</span>' : ''}
          ${part ? '<span class="j-badge part">Départ demain</span>' : ''}
        </button>`;
      }).join('')}</div></div>`;
  }).join('')}</div>`;
}

function htmlDsp() {
  const cats = ETAT.categories || [], chambres = ETAT.chambres || [];
  const F = ETAT.fermetures || [], auj = AUJ();
  if (!DSP.focus) DSP.focus = auj;
  if (!cats.length) {
    return `<div class="carte" style="text-align:center;padding:48px">
      <p class="bloc-t" style="margin-bottom:6px">Aucune catégorie de chambre</p>
      <p class="aide">Les catégories viennent du site : elles se déclarent dans
      <code>_chambres.py</code>.</p></div>`;
  }
  const jours = joursDsp();
  const calc = calculerDisponibilites(cats, chambres, F, jours.concat([auj]), auj, DSP.seuil);
  const col = (j) => 'dsp-j' + (j === auj ? ' auj' : '');
  const nomCat = (slug) => (cats.find((c) => c.slug === slug) || {}).nom || slug;

  /* ── L'inventaire n'existe pas encore ─────────────────────────────── */
  if (!chambres.length) {
    return `<div class="carte dsp-vide">
      <h2 class="bloc-t" style="margin-bottom:6px">Commencez par saisir vos chambres</h2>
      <p class="aide" style="margin-bottom:22px">Le calendrier affiche une ligne par
      chambre. Tant qu'aucune n'est saisie, <strong>le site n'annonce aucune
      disponibilité</strong> : il redit à chaque visiteur que la réception confirme
      sous 24 h. Ajoutez-les avec les numéros que vous leur donnez déjà — 25, B12,
      Bungalow 3.${ETAT.annoncees ? ` Votre site annonce <strong>${ETAT.annoncees}
      chambres et suites</strong> : c'est le compte à atteindre.` : ''}</p>
      <div class="dsp-cats">
        ${cats.map((c) => `<div>
          <div class="v">${vignette(c.slug)}</div>
          <div style="flex:1;min-width:0">
            <b>${ech(c.nom)}</b>
            <span>${FCFA(c.prix)} / nuit · jusqu'à ${c.pax || '?'} personne${
              (c.pax || 0) > 1 ? 's' : ''}</span>
            <span class="rien">aucune chambre saisie</span>
          </div>
          <button class="btn mince" data-dsp-ajout="${ech(c.slug)}">Ajouter</button>
        </div>`).join('')}
      </div></div>`;
  }

  /* ── Les compteurs, pour cette nuit ───────────────────────────────── */
  const idx = dspIndex(F, chambres);
  const etatsAuj = chambres.map((ch) => dspEtat(ch, auj, idx, auj).k);
  const combien = (k) => etatsAuj.filter((x) => x === k).length;
  const CARTES = [
    ['Total chambres', chambres.length, '', 'lit'],
    ['Disponibles', combien('libre'), 'var(--et-libre)', 'ok'],
    ['Occupées', combien('occ'), 'var(--et-occ)', 'qui'],
    ['Réservées', combien('res'), 'var(--et-res)', 'cal'],
    ['Indisponibles', combien('hs') + combien('vente'), 'var(--et-hs)', 'cle'],
  ];

  /* ── Le filtre ────────────────────────────────────────────────────── */
  const f = DSP.f;
  const texte = f.texte.trim().toLowerCase();
  const retenues = chambres.filter((ch) => {
    if (f.cat && ch.categorie !== f.cat) return false;
    if (f.etage && String(ch.etage || '') !== f.etage) return false;
    /* Le numero d'abord, toujours. La categorie seulement a partir de trois
       lettres : « B » rendait six chambres sur sept, parce que « Chambre
       Standard » contient un b. On cherche une chambre, pas une lettre. */
    if (texte && !(String(ch.numero).toLowerCase().includes(texte)
      || (texte.length >= 3 && nomCat(ch.categorie).toLowerCase().includes(texte)))) return false;
    const k = dspEtat(ch, DSP.focus, idx, auj).k;
    if (f.libres && k !== 'libre') return false;
    if (f.statut && k !== f.statut) return false;
    return true;
  }).sort((a, b) => (a.categorie === b.categorie
    ? parNum(a, b)
    : cats.findIndex((c) => c.slug === a.categorie)
      - cats.findIndex((c) => c.slug === b.categorie)));

  const avecEtage = chambres.some((ch) => ch.etage);
  /* Les etages reellement saisis, dans l'ordre ou un humain les lit. */
  const etages = [...new Set(chambres.map((ch) => String(ch.etage || '')).filter(Boolean))]
    .sort((a, b) => String(a).localeCompare(String(b), 'fr', { numeric: true }));

  const filtres = `<div class="carte dsp-filtres">
    <input id="dsp-q" class="fl" placeholder="Rechercher une chambre…"
      value="${ech(f.texte)}" aria-label="Rechercher une chambre">
    <select id="dsp-fcat" aria-label="Catégorie">
      <option value="">Toutes les catégories</option>
      ${cats.map((c) => `<option value="${ech(c.slug)}" ${c.slug === f.cat ? 'selected' : ''}
        >${ech(c.nom)}</option>`).join('')}
    </select>
    ${etages.length ? `<select id="dsp-fetage" aria-label="Étage">
      <option value="">Tous les étages</option>
      ${etages.map((e) => `<option value="${ech(e)}" ${e === f.etage ? 'selected' : ''}
        >Étage ${ech(e)}</option>`).join('')}
    </select>` : ''}
    <select id="dsp-fstat" aria-label="Statut">
      <option value="">Tous les statuts</option>
      ${[['libre', 'Libre'], ['res', 'Réservée'], ['occ', 'Occupée'],
         ['vente', 'Bloquée'], ['net', 'Nettoyage'], ['hs', 'Hors service']].map(([v, l]) =>
        `<option value="${v}" ${v === f.statut ? 'selected' : ''}>${l}</option>`).join('')}
    </select>
    <label class="prise"><input type="checkbox" id="dsp-flibres" ${f.libres ? 'checked' : ''}>
      Uniquement les disponibles</label>
  </div>`;

  /* ── La grille ────────────────────────────────────────────────────── */
  const tete = jours.map((j) => {
    const d = jDt(j);
    /* Le mois, sauf en vue mois ou il n'y a ni la place ni le besoin : la
       periode le dit deja, et toutes les colonnes sont du meme mois. Une
       semaine a cheval sur deux mois montrait « 30 » puis « 1 » sans dire
       de quoi. */
    const mois = DSP.vue === 'mois' ? ''
      : d.toLocaleDateString('fr-FR', { month: 'short' }).replace(/\.$/, '');
    return `<div class="${col(j)} dsp-t" data-jour="${j}">
      <span>${jMaj(d.toLocaleDateString('fr-FR', { weekday: 'short' }).replace('.', ''))}</span>
      <b>${d.getDate()}${mois ? ` <i>${mois}</i>` : ''}</b></div>`;
  }).join('');

  /* La categorie s'ecrit UNE FOIS par groupe, en intertitre, au lieu d'etre
     repetee sur chacune des quarante-six lignes. Elle occupait 202 des
     330 px du bloc gele de gauche — c'est elle qui empechait le mois de
     tenir a l'ecran.
     Le tri place deja les chambres par categorie puis par numero : les
     groupes sont donc contigus, filtres compris. */
  let groupe = null;
  const lignes = retenues.map((ch) => {
    let tete = '';
    if (ch.categorie !== groupe) {
      groupe = ch.categorie;
      tete = `<div class="dsp-cat"><b>${ech(nomCat(ch.categorie))}</b></div>`;
    }
    const cases = blocsDe(ch, jours, calc).map(({ e, jour: j, n }) => {
      const [, mot] = DTON[e.k], det = detailSejour(e);
      const [fond, encre] = DAPLAT[e.k] || DAPLAT.hs;
      /* Un bloc qui couvre aujourd'hui porte la teinte du jour : la colonne
         entiere ne peut pas etre encadree quand les cases se chevauchent. */
      const dedans = n === 1 ? j === auj : (j <= auj && jours[jours.indexOf(j) + n - 1] >= auj);
      const nuits = n === 1 ? jLong(j)
        : 'du ' + jCourt(j) + ' au ' + jCourt(jours[jours.indexOf(j) + n - 1])
          + ' (' + n + ' nuits)';
      const aria = 'Chambre ' + ech(ch.numero) + ', ' + nuits + ' : ' + mot
        + (det ? ' — ' + ech(det) : '');
      /* La case ouverte dans le panneau porte un contour. Tant que le
         panneau recouvrait le calendrier, on savait forcement laquelle on
         modifiait ; a cote, plus rien ne le disait. */
      const ouverte = !!(DSP.tiroir && DSP.tiroir.id === ch.id && DSP.tiroir.nuit === j);
      return `<div class="dsp-j${dedans ? ' auj' : ''}"${n > 1 ? ` style="--n:${n}"` : ''}
        ><button class="dsp-b${ouverte ? ' sel' : ''}" style="--f:${fond};--t:${encre}"
        aria-current="${ouverte ? 'true' : 'false'}" data-dsp-ch="${ech(ch.id)}"
        data-nuit="${j}" aria-label="${aria}" title="${aria}">${mot}${
        det && DSP.vue !== 'mois' ? '<small>' + ech(det) + '</small>' : ''}</button></div>`;
    }).join('');
    return `${tete}<div class="dsp-l dsp-r">
      <div class="dsp-g dsp-ch">
        <div style="min-width:0">
          <button class="dsp-num" data-dsp-fiche="${ech(ch.id)}"
            aria-label="Chambre ${ech(ch.numero)}, ${ech(nomCat(ch.categorie))} — voir et modifier"
            >${ech(ch.numero)}</button>
          ${ch.service === false ? '<span class="sc">hors service</span>' : ''}
        </div>
        ${avecEtage ? `<span class="et">${ech(ch.etage || '—')}</span>` : ''}
      </div>${cases}</div>`;
  }).join('');

  /* Les categories dont aucune chambre n'est saisie : le site n'en dit rien,
     et c'est le trou le plus couteux — invisible dans une liste de chambres
     qui n'existent pas. */
  const manquantes = cats.filter((c) => !chambres.some((ch) => ch.categorie === c.slug));

  const mois = [];
  for (let i = -3; i <= 9; i++) {
    const d = jDt(auj.slice(0, 8) + '01'); d.setMonth(d.getMonth() + i);
    mois.push(jourIso(d).slice(0, 7));
  }
  if (!mois.includes(DSP.focus.slice(0, 7))) mois.push(DSP.focus.slice(0, 7));
  const optMois = mois.sort().map((m) => `<option value="${m}" ${m === DSP.focus.slice(0, 7)
    ? 'selected' : ''}>${jMaj(jDt(m + '-01').toLocaleDateString('fr-FR',
      { month: 'long', year: 'numeric' }))}</option>`).join('');
  const vues = [['jour', 'Jour'], ['semaine', 'Semaine'], ['mois', 'Mois']]
    .map(([v, l]) => `<button class="opt ${DSP.vue === v ? 'on' : ''}" data-dsp-vue="${v}"
      aria-pressed="${DSP.vue === v}">${l}</button>`).join('');
  /* Un libelle par mode, comme le document le demande. */
  const periode = DSP.vue === 'jour' ? jLong(DSP.focus)
    : DSP.vue === 'mois'
      ? jMaj(jDt(DSP.focus).toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' }))
      : 'Du ' + jCourt(jours[0]) + ' au ' + jCourt(jours[jours.length - 1]);

  /* Les prochaines arrivees. Plusieurs chambres au meme nom, aux memes dates
     et dans la meme categorie font une seule reservation. */
  const groupes = {};
  F.filter((x) => x.nature === 'client' && x.statut !== 'annulee' && !paiementLache(x) && x.debut >= auj).forEach((x) => {
    const ch = chambres.find((c) => c.id === x.cible);
    if (!ch) return;
    const k = [x.client, x.debut, x.fin, ch.categorie].join('|');
    (groupes[k] = groupes[k] || { f: x, cat: ch.categorie, n: 0 }).n++;
  });
  const toutes = Object.values(groupes).sort((a, b) => a.f.debut.localeCompare(b.f.debut));
  const resas = toutes.slice(0, DSP.voirTout ? 40 : 4).map((g) => {
    const att = g.f.statut === 'attente';
    return `<div class="dsp-resa"><div><b>${ech(g.f.client || '—')}</b>
      <span>${ech(nomCat(g.cat))} — ${g.n} chambre${g.n > 1 ? 's' : ''}</span>
      <span class="quand">Arrivée ${jCourt(g.f.debut)} → Départ ${jCourt(jPlus(g.f.fin, 1))}</span>
      ${att && g.f.expire ? `<span class="quand" style="color:${retenueTombee(g.f)
        ? 'var(--et-bloq)' : 'var(--bronze-2)'}">${retenueTombee(g.f) ? 'retenue expirée'
        : 'gardée jusqu\'à ' + heureDe(g.f.expire)}</span>` : ''}</div>
      <span class="etat ${att ? 'attend' : 'vif'}">${att ? 'En attente' : 'Confirmée'}</span></div>`;
  }).join('');

  /* ── Les demandes venues du site, en tete d'ecran ──────────────────
     Elles passent AVANT les compteurs : une chambre gardee dont personne ne
     s'occupe se remet en vente toute seule, et le client n'aura jamais de
     reponse. C'est la seule chose de cet ecran qui ait une echeance. */
  const aTraiter = (F || [])
    .filter((x) => x.nature === 'client' && x.statut === 'attente' && x.expire && !paiementLache(x))
    .map((x) => ({ f: x, ch: chambres.find((c) => c.id === x.cible) }))
    .filter((x) => x.ch)
    .sort((a, b) => String(a.f.expire).localeCompare(String(b.f.expire)));

  const demandes = !aTraiter.length ? '' : `<div class="carte dsp-traiter">
    <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:10px">
      <h2 class="bloc-t" style="margin-bottom:4px">${aTraiter.length} demande${
        aTraiter.length > 1 ? 's' : ''} venue${aTraiter.length > 1 ? 's' : ''} du site</h2>
    </div>
    <p class="aide" style="margin:0 0 16px">La chambre leur est gardée jusqu'à
      l'heure indiquée. Passé ce délai elle se remet en vente, et le client
      n'aura pas de réponse. <strong>Confirmez celles que vous honorez.</strong></p>
    ${aTraiter.map(({ f, ch }) => `<div class="dsp-dem">
      <div style="flex:1;min-width:0">
        <b>${ech(f.client)}</b>
        <span>${ech(nomCat(ch.categorie))} · chambre ${ech(ch.numero)}</span>
        <span class="quand">Arrivée ${jCourt(f.debut)} → Départ ${jCourt(jPlus(f.fin, 1))}${
          f.motif ? ' · réf. ' + ech(f.motif) : ''}</span>
        <span style="color:${retenueTombee(f) ? 'var(--et-bloq)' : 'var(--bronze-2)'};font-size:12.5px">${
          retenueTombee(f) ? 'Retenue expirée — la chambre est redevenue disponible'
            : 'Gardée jusqu\'à ' + heureDe(f.expire)}</span>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;flex:none">
        <button class="btn mince plein" data-dsp-confirmer="${ech(f.id)}">Confirmer</button>
        <button class="btn mince danger" data-rouvrir="${ech(f.id)}">Refuser</button>
      </div>
    </div>`).join('')}
  </div>`;

  /* La vue liste : la meme selection de chambres, mais l'etat d'UN jour —
     celui sur lequel la periode est posee. Elle sert a lire vite, pas a
     naviguer dans le temps : le calendrier est la pour ca. */
  const liste = `<table class="dsp-liste">
    <thead><tr>
      <th>Chambre</th><th>Catégorie</th>${avecEtage ? '<th>Étage</th>' : ''}
      <th>État ${DSP.focus === auj ? 'ce soir' : 'le ' + jCourt(DSP.focus)}</th><th>Client</th>
    </tr></thead>
    <tbody>${retenues.length ? retenues.map((ch) => {
      const e = dspEtat(ch, DSP.focus, idx, auj), [teinte, mot] = DTON[e.k];
      const qui = e.f && e.f.nature === 'client' ? (e.f.client || '—')
        : e.f && e.f.motif ? e.f.motif : '—';
      return `<tr data-dsp-ch="${ech(ch.id)}" data-nuit="${DSP.focus}" tabindex="0"
        aria-label="Chambre ${ech(ch.numero)} : ${mot}">
        <td><button class="dsp-num" data-dsp-fiche="${ech(ch.id)}"
          aria-label="Chambre ${ech(ch.numero)}, ${ech(nomCat(ch.categorie))} — voir et modifier"
          >${ech(ch.numero)}</button></td>
        <td>${ech(nomCat(ch.categorie))}</td>
        ${avecEtage ? `<td>${ech(ch.etage || '—')}</td>` : ''}
        <td><span class="etat" style="color:${teinte};border-color:${teinte}">${mot}</span></td>
        <td>${ech(qui)}</td></tr>`;
    }).join('') : `<tr><td colspan="${avecEtage ? 5 : 4}">
      <p class="aide" style="margin:0">Aucune chambre ne correspond à ce filtre.</p></td></tr>`}
    </tbody></table>`;

  return `${demandes}<div class="dsp-chiffres-h">
      ${CARTES.map(([l, n, c, ic]) => `<div class="carte"${c ? ` style="--c:${c}"` : ''}>
        <i class="rond">${ICONES[ic] || ''}</i>
        <div><b>${n}</b><span>${l}</span></div></div>`).join('')}
    </div>
    ${filtres}
    <section class="dsp-cal v-${DSP.vue}" aria-label="Calendrier des disponibilités">
      <div class="dsp-barre">
        <div class="dsp-vues" role="group" aria-label="Affichage">
          ${[['calendrier', 'Vue calendrier'], ['liste', 'Vue liste']].map(([v, l]) =>
            `<button class="opt ${DSP.mode === v ? 'on' : ''}" data-dsp-mode="${v}"
              aria-pressed="${DSP.mode === v}">${l}</button>`).join('')}
        </div>
        <div class="dsp-nav">
          <button class="fl2" data-dsp-pas="-1" aria-label="Période précédente">‹</button>
          <button class="fl2" data-dsp-pas="1" aria-label="Période suivante">›</button>
          <button class="btn mince" data-dsp-auj="1">Aujourd'hui</button>
          <select id="dsp-mois" class="dsp-mois" aria-label="Mois affiché">${optMois}</select>
          ${DSP.vue === 'mois' ? '' : `<span class="aide" style="margin:0 0 0 6px"
            >${periode}</span>`}
        </div>
        <div class="dsp-vues" role="group" aria-label="Vue du calendrier">${vues}</div>
      </div>
      ${DSP.mode === 'liste' ? liste
        : DSP.vue === 'mois' ? htmlMois(retenues, idx, auj)
        : DSP.vue === 'jour' ? htmlJour(retenues, idx, auj)
        : `<div class="dsp-defil" id="dsp-defil">
        <div class="dsp-l dsp-tete"><div class="dsp-g dsp-ch">
          <span class="lb" style="margin:0;flex:1">Chambre</span>
          ${avecEtage ? '<span class="lb" style="margin:0">Étage</span>' : ''}</div>${tete}</div>
        ${lignes || `<div class="dsp-l dsp-r"><div class="dsp-g" style="flex:1;max-width:none">
          <p class="aide" style="margin:0">Aucune chambre ne correspond à ce filtre.</p></div></div>`}
      </div>`}
      <div class="dsp-pied">
        ${cats.map((c) => `<button class="dsp-lien" data-dsp-ajout="${ech(c.slug)}"
          >+ ${ech(c.nom)}</button>`).join('')}
      </div>
    </section>
    ${manquantes.length ? `<div class="alerte ambre" style="margin-top:18px">
      <b>${manquantes.length} catégorie${manquantes.length > 1 ? 's' : ''} sans aucune chambre saisie</b>
      <span>${manquantes.map((c) => ech(c.nom)).join(', ')} — le site n'annonce rien
      pour ${manquantes.length > 1 ? 'ces catégories' : 'cette catégorie'} et redit que
      la réception confirme sous 24 h.</span></div>` : ''}
    <div class="dsp-bas" style="margin-top:20px">
      <section class="carte">
        <div style="display:flex;justify-content:space-between;align-items:baseline">
          <h2 class="bloc-t" style="margin-bottom:8px">Prochaines réservations</h2>
          ${toutes.length > 4 ? `<button class="dsp-lien" style="padding:0" data-dsp-voirtout>${
            DSP.voirTout ? 'Réduire' : 'Voir tout (' + toutes.length + ')'}</button>` : ''}
        </div>
        ${resas || '<p class="aide" style="padding:10px 0 4px">Aucune réservation à venir</p>'}
      </section>
      <section class="carte">
        <h2 class="bloc-t">Ce que veut dire chaque couleur</h2>
        <ul class="dsp-legende">
          <li><span class="pt" style="--c:var(--et-libre)"></span>Libre</li>
          <li><span class="pt" style="--c:var(--et-res)"></span>Réservée — le client arrive</li>
          <li><span class="pt" style="--c:var(--et-occ)"></span>Occupée — le client est là</li>
          <li><span class="pt" style="--c:var(--et-bloq)"></span>Bloquée à la vente</li>
          <li><span class="pt" style="--c:var(--et-net)"></span>Nettoyage</li>
          <li><span class="pt" style="--c:var(--et-hs)"></span>Hors service</li>
        </ul>
        <p class="aide" style="margin-top:16px;padding-top:14px;border-top:1px solid var(--line)">
          <b style="color:var(--cream);font-weight:600">Ce que le client lit sur le site</b><br>
          « Disponible à ces dates » s'il reste au moins deux chambres,
          « Dernière chambre à ces dates » s'il n'en reste qu'une,
          « Complet à ces dates » s'il n'en reste aucune. Tant qu'aucune chambre
          n'est saisie dans une catégorie, le site ne promet rien :
          « Disponibilité confirmée sous 24 h ».</p>
      </section>
    </div>`;
}

function rendreDsp() {
  const z = $('#dsp-zone');
  if (!z) return;
  z.innerHTML = htmlDsp();
  apresDsp();
}

/** Remesure la fenetre une fois la zone posee, et redessine si le compte a
    change. La recursion s'arrete d'elle-meme : au second passage le compte
    est celui qu'on vient d'employer. */
function apresDsp() {
  /* Mois, semaine et jour ne demandent pas la meme largeur : passer de l'un
     a l'autre peut donc replier la barre, ou la rouvrir. */
  ajusterMenu();
  const el = $('#dsp-defil');
  if (!el) return;
  el.scrollLeft = 0;
}

/* ── Voir arriver les demandes ────────────────────────────────────────
   Une retenue ne dure que deux heures. Une reception qui laisse l'onglet
   ouvert — c'est ce qu'elle fait — ne verrait jamais une demande arriver, et
   la chambre se remettrait en vente sans que personne n'ait rien vu.

   On relit donc le magasin toutes les minutes, et on ne redessine QUE s'il a
   change : redessiner pour rien ferait sauter le curseur de la recherche.
   Et jamais pendant qu'un tiroir ou une fenetre est ouverte — on effacerait
   ce que la reception est en train de saisir. */
let DSP_VU = null;
setInterval(async () => {
  if (VUE !== 'disponibilites' || DSP.tiroir || DSP.modal) return;
  if (document.hidden) return;
  try {
    const r = await appel('tout');
    if (!r.ok || !r.donnees) return;
    if (r.donnees.maj === DSP_VU) return;
    DSP_VU = r.donnees.maj;
    ETAT.chambres = r.donnees.chambres || [];
    ETAT.fermetures = r.donnees.fermetures || [];
    rendre();
  } catch (e) { /* le reseau reviendra */ }
}, 60000);


function allerDsp(focus, vue) {
  DSP.focus = focus;
  if (vue) DSP.vue = vue;
  DSP.defiler = true;
  rendreDsp();
}
function decalerDsp(sens) {
  if (DSP.vue === 'jour') return allerDsp(jPlus(DSP.focus, sens));
  if (DSP.vue === 'semaine') return allerDsp(jPlus(DSP.focus, 7 * sens));
  /* Un MOIS, pas une fenetre : « suivant » depuis septembre donne octobre,
     et non « trente jours plus loin » — ce qui tombait au milieu du mois
     suivant et decalait un peu plus a chaque clic. */
  const d = jDt(DSP.focus);
  allerDsp(jourIso(new Date(d.getFullYear(), d.getMonth() + sens, 1)));
}

/* ── Couche : tiroir, fenêtre, notification ─────────────────────────── */
function couche() {
  let c = $('#dsp-couche');
  if (!c) {
    c = document.createElement('div');
    c.id = 'dsp-couche';
    c.innerHTML = '<div id="dsp-voile" data-dsp-fermer></div>'
      + '<aside id="dsp-tiroir" role="dialog" aria-modal="true" aria-label="Modifier la disponibilité"></aside>'
      + '<div id="dsp-modal"></div><div id="dsp-toast" role="status" aria-live="polite"></div>';
    document.body.appendChild(c);
  }
  return c;
}

let TOAST_T = null;
function notifier(texte, mal) {
  couche();
  const t = $('#dsp-toast');
  t.textContent = (mal ? '! ' : '✓ ') + texte;
  t.className = 'on' + (mal ? ' mal' : '');
  clearTimeout(TOAST_T);
  TOAST_T = setTimeout(() => { t.className = mal ? 'mal' : ''; }, 3200);
}

const radio = (nom, liste, cur) => liste.map(([v, l, c]) => `<label class="dsp-radio ${cur === v ? 'on' : ''}">
  <input type="radio" name="${nom}" value="${v}" ${cur === v ? 'checked' : ''}>
  ${c ? `<span class="pt" style="--c:${c}"></span>` : ''}${l}</label>`).join('');

function rendreTiroir() {
  couche();
  const tr = DSP.tiroir, el = $('#dsp-tiroir');
  $('#dsp-voile').classList.toggle('on', !!tr);
  el.classList.toggle('on', !!tr);
  el.setAttribute('aria-hidden', tr ? 'false' : 'true');
  /* A cote, et non par-dessus, quand l'ecran le permet. La feuille decide
     du seuil ; on se contente de dire que le panneau est ouvert, et
     `aria-modal` tombe : ce n'est plus une boite de dialogue qui capture,
     c'est un panneau a cote de son contenu. */
  document.querySelectorAll('.dsp-b.sel').forEach((b) => {
    b.classList.remove('sel'); b.setAttribute('aria-current', 'false');
  });
  if (tr && tr.id && tr.nuit) {
    const cible = document.querySelector('.dsp-b[data-dsp-ch="' + tr.id
      + '"][data-nuit="' + tr.nuit + '"]');
    if (cible) { cible.classList.add('sel'); cible.setAttribute('aria-current', 'true'); }
  }

  const cote = !!tr && window.matchMedia('(min-width:1200px)').matches;
  document.body.classList.toggle('dsp-cote', cote);
  /* Ancre, le panneau prend 320 px au calendrier : c'est souvent lui, et non
     la fenetre, qui decide que la barre doit se replier. */
  ajusterMenu();
  if (cote) el.removeAttribute('aria-modal');
  else el.setAttribute('aria-modal', 'true');
  if (!tr) return;
  const chambres = ETAT.chambres || [], F = ETAT.fermetures || [], auj = AUJ();
  let qui, corps, statuts, avert = '', bloque = false;

  if (tr.mode === 'cat') {
    const c = ETAT.categories.find((x) => x.slug === tr.slug);
    const x = calculerDisponibilites([c], chambres, F, [tr.nuit], auj, DSP.seuil).parCat[tr.slug][tr.nuit];
    const perm = chambres.filter((ch) => ch.categorie === tr.slug && ch.service === false).length;
    const max = x.total - x.reserves - perm, v = tr.ajust;
    tr.max = max;
    qui = [vignette(c.slug), c.nom];
    corps = `<div class="dsp-chiffres">
        <div><span>Total des chambres</span><b>${x.total}</b></div>
        <div><span>Réservées</span><b>${x.reserves}</b></div>
        <div><span>Hors service</span><b>${x.bloques}</b></div>
        <div class="fort"><span style="display:flex;align-items:center;gap:10px"><span class="pt"
          style="--c:${DTON[x.etat][0]}"></span>Disponibles</span><b>${x.libres}</b></div>
      </div>
      <div class="dsp-ajust"><span class="lb" id="dsp-aj" style="margin:0">Ajuster la disponibilité</span>
        <div class="dsp-pas" role="group" aria-labelledby="dsp-aj">
          <button data-dsp-ajust="-1" ${v <= 0 ? 'disabled' : ''} aria-label="Une chambre disponible de moins">−</button>
          <output aria-live="polite">${v}</output>
          <button data-dsp-ajust="1" ${v >= max ? 'disabled' : ''} aria-label="Une chambre disponible de plus">+</button>
        </div></div>
      <p class="aide" style="margin:0 0 20px">Entre 0 et ${max} : les chambres réservées${perm
        ? ' et hors service' : ''} ne se libèrent pas ici.</p>`;
    statuts = radio('dsp-statut', [['dispo', 'Disponible', 'var(--et-libre)'], ['complet', 'Complet', 'var(--et-bloq)'],
      ['hs', 'Hors service', 'var(--et-hs)']], tr.statut);
    if (tr.statut === 'hs' && x.reserves > 0) {
      avert = x.reserves + (x.reserves > 1 ? ' chambres sont réservées' : ' chambre est réservée')
        + ' cette nuit. Seules les chambres libres seront mises hors service : pour les autres, '
        + 'traitez d’abord la réservation.';
    }
  } else {
    const ch = chambres.find((x) => x.id === tr.id);
    const c = ETAT.categories.find((x) => x.slug === ch.categorie) || { nom: '' };
    const e = dspEtat(ch, tr.nuit, dspIndex(F, chambres), auj), [teinte, mot] = DTON[e.k];
    const client = e.k === 'occ' || e.k === 'res';
    const det = client
      ? (e.f.client || 'Fermeture') + ' — arrivée ' + jCourt(e.f.debut) + ', départ '
        + jCourt(jPlus(e.f.fin, 1)) + ' · ' + (e.f.statut === 'attente' ? 'en attente' : 'confirmée') + '.'
      : e.k === 'hs' || e.k === 'vente' || e.k === 'net' ? (e.f ? e.f.motif + ' — ' + nuitsEnClair(e.f).toLowerCase() + '.'
        : (e.motif || '') + ' — sans date de fin.') : '';
    qui = [vignette(ch.categorie), 'Chambre ' + ch.numero + (c.nom ? ' · ' + c.nom : '')];
    corps = `<div class="dsp-chiffres"><div><span>État cette nuit</span>
        <span class="etat" style="color:${teinte};border-color:${teinte}">${mot}</span></div>
        ${det ? `<div><span style="color:var(--prose);font-size:13px">${ech(det)}</span></div>` : ''}
        ${c.prix ? `<div><span>Tarif par nuit</span><b>${FCFA(c.prix)} FCFA</b></div>` : ''}
        ${ch.etage ? `<div><span>Étage</span><b>${ech(ch.etage)}</b></div>` : ''}</div>`;
    statuts = radio('dsp-statut', [['dispo', 'Disponible', 'var(--et-libre)'],
      ['complet', 'Bloquée à la vente', 'var(--et-bloq)'],
      ['nettoyage', 'Nettoyage', 'var(--et-net)'],
      ['hs', 'Hors service', 'var(--et-hs)']], tr.statut);
    if (client && tr.statut === 'hs') {
      bloque = true;
      avert = 'Cette chambre possède une réservation ' + (e.f.statut === 'attente' ? 'en attente'
        : 'confirmée') + ' sur cette période. Vous ne pouvez pas la mettre hors service sans '
        + 'traiter d’abord la réservation.';
    }
  }

  if (tr.mode === 'fiche') return rendreFiche(el, tr);

  el.innerHTML = `<div class="dsp-th"><h2>Modifier la disponibilité</h2>
      <button class="dsp-x" data-dsp-fermer aria-label="Fermer">×</button></div>
    <div class="dsp-tc">
      <div class="dsp-qui">${qui[0]}<div><b>${ech(qui[1])}</b><span>${jLong(tr.nuit)}</span></div></div>
      ${corps}
      <span class="lb" style="margin-top:0">Statut</span>
      <div role="radiogroup" aria-label="Statut" style="margin-bottom:18px">${statuts}</div>
      ${avert ? `<div class="alerte ambre" role="alert"><b>Attention</b><span>${avert}</span></div>` : ''}
      <label for="dsp-com">Commentaire (facultatif)</label>
      <textarea id="dsp-com" maxlength="120" style="min-height:80px"
        placeholder="Ex. : maintenance, travaux, problème technique...">${ech(tr.commentaire || '')}</textarea>
      <p class="aide">Pour vous seuls : le site écrit « Complet », jamais le motif.</p>
      ${tr.erreur !== undefined && tr.erreur !== false ? `<p class="msg mal" role="alert" style="margin-top:14px">
        Impossible d'enregistrer les modifications. Vérifiez votre connexion puis réessayez.
        ${tr.erreur ? '<br>' + ech(tr.erreur) : ''}</p>` : ''}
    </div>
    <div class="dsp-tp">
      <button class="btn" data-dsp-fermer>Annuler</button>
      <button class="btn plein" id="dsp-enreg" ${bloque ? 'disabled style="opacity:.4;cursor:default"' : ''}>
        Enregistrer les modifications</button>
    </div>`;
}

/* ── La fiche d'une chambre ───────────────────────────────────────────
   On clique son NUMERO, et tout se fait la : reserver, bloquer, mettre hors
   service, rouvrir, retirer. Avant, il fallait savoir que la case du
   calendrier ouvrait un tiroir, que le bouton du haut ouvrait une fenetre, et
   qu'un depliant en bas de page cachait le reste. Personne ne devinait. */
function rendreFiche(el, tr) {
  const ch = (ETAT.chambres || []).find((x) => x.id === tr.id);
  if (!ch) { DSP.tiroir = null; el.classList.remove('on'); return; }
  const cat = (ETAT.categories || []).find((c) => c.slug === ch.categorie) || { nom: '' };
  const auj = AUJ();
  const e = dspEtat(ch, auj, dspIndex(ETAT.fermetures, ETAT.chambres), auj);
  const [teinte, mot] = DTON[e.k];

  /* Ce qui est pose sur cette chambre, du plus proche au plus lointain. Les
     fermetures passees ne servent plus a rien ici. */
  const siennes = (ETAT.fermetures || [])
    .filter((f) => f.debut && fVise(f, ch) && (!f.fin || f.fin >= auj)
      && f.statut !== 'annulee' && !paiementLache(f))
    .sort((a, b) => a.debut.localeCompare(b.debut));

  const datee = tr.statut === 'reservee' || tr.statut === 'vente'
    || tr.statut === 'nettoyage';
  el.innerHTML = `<div class="dsp-th"><h2>Chambre ${ech(ch.numero)}</h2>
      <button class="dsp-x" data-dsp-fermer aria-label="Fermer">×</button></div>
    <div class="dsp-tc">
      <div class="dsp-qui">${vignette(ch.categorie)}<div>
        <b>Chambre ${ech(ch.numero)}</b><span>${ech(cat.nom)}</span></div></div>

      <div class="dsp-chiffres"><div><span>Ce soir</span>
        <span class="etat" style="color:${teinte};border-color:${teinte}">${mot}</span></div>
        ${ch.service === false ? `<div><span style="color:var(--prose);font-size:13px">Hors
          service${ch.note ? ' — ' + ech(ch.note) : ''}, jusqu'à nouvel ordre.</span></div>` : ''}
      </div>

      <span class="lb" style="margin-top:0">Que voulez-vous en faire&nbsp;?</span>
      <div role="radiogroup" aria-label="Statut" style="margin-bottom:16px">${radio('dsp-fstatut', [
        ['dispo', 'La rendre disponible', 'var(--et-libre)'],
        ['reservee', 'La réserver pour un client', 'var(--et-res)'],
        ['vente', 'La bloquer à la vente', 'var(--et-bloq)'],
        ['nettoyage', 'La mettre en nettoyage', 'var(--et-net)'],
        ['hs', 'La mettre hors service', 'var(--et-hs)']], tr.statut)}</div>

      ${datee ? `<div class="duo">
          <div class="champ"><label for="fi-d">Première nuit</label>
            <input type="date" id="fi-d" data-dsp-fchamp="debut" value="${ech(tr.debut)}"></div>
          <div class="champ"><label for="fi-f">Dernière nuit</label>
            <input type="date" id="fi-f" data-dsp-fchamp="fin" value="${ech(tr.fin)}"></div>
        </div>
        <p class="aide" style="margin:-10px 0 16px">Ce sont des nuits : du 24 au 26,
          le client repart le matin du 27.</p>` : ''}

      ${tr.statut === 'reservee' ? `<div class="champ">
          <label for="fi-c">Au nom de</label>
          <input id="fi-c" maxlength="60" data-dsp-fchamp="client" placeholder="M. Koné"
            value="${ech(tr.client)}"></div>` : ''}
      ${tr.statut === 'vente' || tr.statut === 'hs' ? `<div class="champ">
          <label for="fi-m">Pourquoi — pour vous seuls</label>
          <input id="fi-m" maxlength="120" data-dsp-fchamp="motif"
            placeholder="Maintenance, travaux, problème technique…" value="${ech(tr.motif)}">
          <p class="aide">Le site écrit « Complet », jamais le motif.</p></div>` : ''}
      ${tr.statut === 'hs' ? `<p class="aide" style="margin:-8px 0 16px">Sans dates :
        la chambre ne compte plus, jusqu'à ce que vous la remettiez en service.</p>` : ''}

      ${siennes.length ? `<span class="lb">Ce qui est posé sur cette chambre</span>
        ${siennes.map((f) => `<div class="dsp-resa" style="padding:10px 0">
          <div><b>${ech(f.client || f.motif || 'Fermeture')}</b>
            <span class="quand">${ech(nuitsEnClair(f))}</span>
            ${f.statut === 'attente' && f.expire ? `<span style="color:${
              retenueTombee(f) ? 'var(--et-bloq)' : 'var(--bronze-2)'};font-size:12.5px">${
              retenueTombee(f)
                ? 'Retenue expirée : la chambre est redevenue disponible.'
                : 'Demande venue du site — la chambre lui est gardée jusqu\'à '
                  + heureDe(f.expire) + '.'}</span>` : ''}</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;flex:none">
            ${f.statut === 'attente'
              ? `<button class="btn mince" data-dsp-confirmer="${ech(f.id)}"
                  >Confirmer</button>` : ''}
            <button class="btn mince danger" data-rouvrir="${ech(f.id)}">Rouvrir</button>
          </div>
        </div>`).join('')}` : `<p class="aide">Rien n'est posé sur cette chambre :
          elle compte à toutes les dates.</p>`}

      ${tr.erreur ? `<p class="msg mal" role="alert" style="margin-top:14px">${ech(tr.erreur)}</p>` : ''}

      <div style="margin-top:24px;padding-top:16px;border-top:1px solid var(--line)">
        <button class="btn" data-cm-ouvrir="${ech(ch.id)}">Fiche de la chambre</button>
        <p class="aide" style="margin-top:8px">Numéro, catégorie, équipements, photos,
          publication, suppression : tout cela se gère dans le module Chambres.</p>
      </div>
    </div>
    <div class="dsp-tp">
      <button class="btn" data-dsp-fermer>Annuler</button>
      <button class="btn plein" id="dsp-fenreg">Enregistrer</button>
    </div>`;
}

function ouvrirFiche(id) {
  const auj = AUJ();
  const ch = (ETAT.chambres || []).find((x) => x.id === id);
  if (!ch) return;
  DSP.tiroir = { mode: 'fiche', id, statut: ch.service === false ? 'hs' : 'dispo',
    debut: auj, fin: auj, client: '', motif: '', erreur: '' };
  rendreTiroir();
  setTimeout(() => { const b = $('#dsp-tiroir .dsp-x'); if (b) b.focus(); }, 60);
}

/** Enregistre la fiche. Chaque statut a son ecriture, et une seule. */
async function enregistrerFiche() {
  const tr = DSP.tiroir;
  const ch = (ETAT.chambres || []).find((x) => x.id === tr.id);
  if (!ch) return;
  const dire = (t) => { tr.erreur = t; rendreTiroir(); };
  const datee = tr.statut === 'reservee' || tr.statut === 'vente'
    || tr.statut === 'nettoyage';
  if (datee) {
    if (!tr.debut || !tr.fin) return dire('Indiquez la première et la dernière nuit.');
    if (tr.fin < tr.debut) return dire('La dernière nuit précède la première.');
  }
  if (tr.statut === 'reservee' && !tr.client.trim()) return dire('Au nom de qui ?');

  const btn = $('#dsp-fenreg');
  if (btn) { btn.disabled = true; btn.textContent = 'Enregistrement…'; }
  try {
    if (tr.statut === 'hs') {
      const r = await appel('enregistrer', { type: 'chambre',
        entree: Object.assign({}, ch, { service: false, statut: 'hors-service', note: tr.motif.trim() }) });
      if (!r.ok) throw new Error(r.message);
      ETAT.chambres = ETAT.chambres.map((x) => (x.id === ch.id ? r.entree : x));
    } else if (tr.statut === 'dispo') {
      if (ch.service === false) {
        const r = await appel('enregistrer', { type: 'chambre',
          entree: Object.assign({}, ch, { service: true, statut: 'active' }) });
        if (!r.ok) throw new Error(r.message);
        ETAT.chambres = ETAT.chambres.map((x) => (x.id === ch.id ? r.entree : x));
      } else {
        /* Rien de date a rendre disponible : on libere ce qui est pose
           aujourd'hui, pas tout l'avenir — retirer une reservation se fait
           par « Rouvrir », qui nomme ce qu'il retire. */
        await libererF([ch.id], AUJ(), AUJ());
      }
    } else if (tr.statut === 'reservee') {
      await poserF({ cible: ch.id, debut: tr.debut, fin: tr.fin, nature: 'client',
        client: tr.client.trim(), statut: 'confirmee', motif: '' });
    } else if (tr.statut === 'nettoyage') {
      await poserF({ cible: ch.id, debut: tr.debut, fin: tr.fin, nature: 'nettoyage',
        motif: tr.motif.trim() || 'Nettoyage' });
    } else {
      await poserF({ cible: ch.id, debut: tr.debut, fin: tr.fin, nature: 'vente',
        motif: tr.motif.trim() || 'Fermée à la vente' });
    }
    DSP.tiroir = null;
    rendreTiroir();
    rendre();
    notifier('Chambre ' + ch.numero + ' mise à jour');
  } catch (err) {
    if (err.message === 'session') return;
    dire('Impossible d’enregistrer. ' + (err.message || ''));
    rendre();
  }
}

/** Une retenue devient une reservation : elle perd sa peremption, donc elle
    ne se rouvrira plus toute seule. C'est le geste que la reception fait en
    reconnaissant la demande arrivee sur son WhatsApp — la reference est la
    meme des deux cotes. */
async function confirmerRetenue(id) {
  const f = (ETAT.fermetures || []).find((x) => x.id === id);
  if (!f) return;
  try {
    const e = await poserF({ id: f.id, cible: f.cible, debut: f.debut, fin: f.fin,
      nature: 'client', client: f.client, motif: f.motif,
      courriel: f.courriel, statut: 'confirmee' });
    rendreTiroir();
    rendre();
    /* Ce que le client a recu, ou pas. Une confirmation qui reussit pendant
       que le courriel echoue en silence, c'est un client que personne ne
       previent — et une reception qui croit le contraire. */
    const dit = {
      envoye: ' — le client est prévenu par e-mail',
      'sans-adresse': ' — aucune adresse : prévenez-le vous-même',
      'non-configure': " — l'envoi d'e-mails n'est pas encore branché :"
        + ' prévenez-le vous-même',
      refuse: " — l'e-mail a été refusé : prévenez-le vous-même",
      echec: " — l'e-mail n'est pas parti : prévenez-le vous-même",
    }[e.__courriel] || '';
    notifier('Réservation de ' + (f.client || 'ce client') + ' confirmée' + dit,
      e.__courriel !== 'envoye' && e.__courriel !== undefined);
  } catch (err) {
    if (err.message === 'session') return;
    notifier('Impossible de confirmer. ' + (err.message || ''), true);
  }
}

function ouvrirCat(slug, nuit) {
  const c = ETAT.categories.find((x) => x.slug === slug);
  const x = calculerDisponibilites([c], ETAT.chambres, ETAT.fermetures, [nuit], AUJ(), DSP.seuil)
    .parCat[slug][nuit];
  DSP.tiroir = { mode: 'cat', slug, nuit, ajust: x.libres, commentaire: '', erreur: false,
    statut: x.libres ? 'dispo' : x.etat === 'hs' ? 'hs' : 'complet' };
  rendreTiroir();
  setTimeout(() => { const b = $('#dsp-tiroir .dsp-x'); if (b) b.focus(); }, 60);
}
function ouvrirChambre(id, nuit) {
  const ch = ETAT.chambres.find((x) => x.id === id);
  const e = dspEtat(ch, nuit, dspIndex(ETAT.fermetures, ETAT.chambres), AUJ());
  DSP.tiroir = { mode: 'chambre', id, nuit, commentaire: '', erreur: false,
    statut: e.k === 'hs' ? 'hs' : e.k === 'vente' ? 'complet' : 'dispo' };
  rendreTiroir();
  setTimeout(() => { const b = $('#dsp-tiroir .dsp-x'); if (b) b.focus(); }, 60);
}

/* ── Écritures ────────────────────────────────────────────────────────
   Toujours par les routes existantes. Une fermeture qui doit rouvrir une
   nuit est découpée : les morceaux qui restent sont écrits AVANT que
   l original soit retiré, pour qu un échec en route ne rouvre jamais plus
   que prévu. */
async function poserF(f) {
  const entree = Object.assign({}, f, { sansFin: f.fin == null });
  const r = await appel('enregistrer', { type: 'fermeture', entree });
  if (!r.ok) throw new Error(r.message || 'Échec de l’enregistrement.');
  ETAT.fermetures = (ETAT.fermetures || []).filter((x) => x.id !== r.entree.id).concat([r.entree]);
  /* `courriel` ne remonte que sur une confirmation. On le colle a l'entree
     pour que l'appelant puisse le dire — voir confirmerRetenue(). */
  if (r.courriel) r.entree.__courriel = r.courriel;
  return r.entree;
}
async function oterF(id) {
  const r = await appel('supprimer', { type: 'fermeture', id });
  if (!r.ok) throw new Error(r.message || 'Échec de la suppression.');
  ETAT.fermetures = (ETAT.fermetures || []).filter((x) => x.id !== id);
}
async function libererF(ids, a, b) {
  const S = new Set(ids), chambres = ETAT.chambres || [];
  const visees = (ETAT.fermetures || []).filter((f) => !fClient(f) && fChevauche(f, a, b)
    && chambres.some((c) => fVise(f, c) && S.has(c.id)));
  for (const f of visees) {
    const base = { cible: f.cible, nature: f.nature, motif: f.motif };
    if (f.debut < a) await poserF(Object.assign({}, base, { debut: f.debut, fin: jPlus(a, -1) }));
    if (f.fin == null || f.fin > b) await poserF(Object.assign({}, base, { debut: jPlus(b, 1), fin: f.fin }));
    const s0 = f.debut > a ? f.debut : a, e0 = (f.fin == null || f.fin > b) ? b : f.fin;
    for (const c of chambres.filter((c) => fVise(f, c) && !S.has(c.id))) {
      await poserF(Object.assign({}, base, { cible: c.id, debut: s0, fin: e0 }));
    }
    await oterF(f.id);
  }
}

async function enregistrerTiroir() {
  const tr = DSP.tiroir;
  if (!tr) return;
  const btn = $('#dsp-enreg');
  if (btn) { btn.disabled = true; btn.textContent = 'Enregistrement…'; }
  const chambres = ETAT.chambres, auj = AUJ(), motif = (tr.commentaire || '').trim();
  const bloc = (ch, nature) => ({ cible: ch.id, debut: tr.nuit, fin: tr.nuit, nature,
    motif: motif || (nature === 'hors-service' ? 'Hors service' : 'Fermée à la vente') });
  try {
    if (tr.mode === 'cat') {
      const idx = dspIndex(ETAT.fermetures, chambres);
      const etats = chambres.filter((c) => c.categorie === tr.slug).sort(parNum)
        .map((ch) => ({ ch, e: dspEtat(ch, tr.nuit, idx, auj) }));
      const libres = etats.filter((x) => x.e.k === 'libre');
      const bloquees = etats.filter((x) => (x.e.k === 'hs' || x.e.k === 'vente') && x.ch.service !== false);
      const cible = tr.statut === 'dispo' ? tr.ajust : 0;
      if (cible < libres.length) {
        for (const x of libres.slice(cible)) await poserF(bloc(x.ch, tr.statut === 'hs' ? 'hors-service' : 'vente'));
      } else if (cible > libres.length) {
        await libererF(bloquees.slice(0, cible - libres.length).map((x) => x.ch.id), tr.nuit, tr.nuit);
      }
    } else {
      const ch = chambres.find((x) => x.id === tr.id);
      const e = dspEtat(ch, tr.nuit, dspIndex(ETAT.fermetures, chambres), auj);
      if (e.k !== 'occ' && e.k !== 'res') {
        if (tr.statut === 'dispo') {
          if (ch.service === false) {
            const r = await appel('enregistrer', { type: 'chambre',
              entree: Object.assign({}, ch, { service: true, statut: 'active' }) });
            if (!r.ok) throw new Error(r.message);
            ETAT.chambres = ETAT.chambres.map((x) => (x.id === ch.id ? r.entree : x));
          } else await libererF([ch.id], tr.nuit, tr.nuit);
        } else if (ch.service !== false) {
          await libererF([ch.id], tr.nuit, tr.nuit);
          await poserF(bloc(ch, tr.statut === 'hs' ? 'hors-service' : 'vente'));
        }
      }
    }
    DSP.tiroir = null;
    rendreTiroir();
    rendre();
    notifier('Disponibilité mise à jour');
  } catch (err) {
    if (err.message === 'session') return;
    tr.erreur = err.message || '';
    rendreTiroir();
    rendre();
    notifier('Impossible d’enregistrer les modifications.', true);
  }
}

/* ── Modifier en lot, Nouvelle réservation ──────────────────────────── */
function ouvrirLot() {
  const cat = (ETAT.categories[0] || {}).slug, auj = AUJ();
  DSP.modal = { type: 'lot', etape: 'form', cat, action: 'hs', raison: '', erreur: '',
    ids: ETAT.chambres.filter((c) => c.categorie === cat).map((c) => c.id),
    debut: jPlus(auj, 1), fin: jPlus(auj, 3) };
  rendreModal();
}
function ouvrirResa() {
  const auj = AUJ();
  DSP.modal = { type: 'resa', cat: (ETAT.categories[0] || {}).slug, debut: auj, fin: jPlus(auj, 2),
    n: '1', client: '', statut: 'confirmee', erreur: '' };
  rendreModal();
}
function analyseLot() {
  const m = DSP.modal;
  const choisies = ETAT.chambres.filter((c) => m.ids.includes(c.id)).sort(parNum);
  const conflits = m.action === 'dispo' ? [] : choisies.map((ch) => {
    const f = ETAT.fermetures.find((x) => fClient(x) && x.statut !== 'annulee' && !paiementLache(x)
      && fVise(x, ch) && fChevauche(x, m.debut, m.fin));
    return f ? { ch, f } : null;
  }).filter(Boolean);
  const exclues = new Set(conflits.map((x) => x.ch.id));
  return { conflits, retenues: choisies.filter((c) => !exclues.has(c.id)) };
}
function libresResa() {
  const m = DSP.modal;
  if (!m.debut || !m.fin || m.fin <= m.debut) return [];
  const der = jPlus(m.fin, -1);
  return ETAT.chambres.filter((ch) => ch.categorie === m.cat && ch.service !== false
    && !ETAT.fermetures.some((f) => f.statut !== 'annulee' && !paiementLache(f) && fVise(f, ch) && fChevauche(f, m.debut, der)))
    .sort(parNum);
}

function rendreModal() {
  couche();
  const m = DSP.modal, el = $('#dsp-modal');
  el.classList.toggle('on', !!m);
  if (!m) { el.innerHTML = ''; return; }
  const catOpt = ETAT.categories.map((c) => `<option value="${ech(c.slug)}" ${c.slug === m.cat
    ? 'selected' : ''}>${ech(c.nom)}</option>`).join('');
  const choix = (liste, cur, cle, cols) => `<div class="choix ${cols === 3 ? 'trois' : ''}"
    style="margin-bottom:18px">${liste.map(([v, l]) => `<button type="button"
      class="opt ${cur === v ? 'on' : ''}" data-dsp-opt="${cle}" data-v="${v}">${l}</button>`).join('')}</div>`;
  let titre, corps, pied;

  if (m.type === 'chambre') {
    const cat = ETAT.categories.find((c) => c.slug === m.cat) || { nom: '' };
    const siennes = (ETAT.chambres || []).filter((c) => c.categorie === m.cat).sort(parNum);
    titre = 'Ajouter une chambre';
    corps = `<div class="dsp-qui">${vignette(m.cat)}<div><b>${ech(cat.nom)}</b>
        <span>${siennes.length ? siennes.length + ' chambre'
          + (siennes.length > 1 ? 's' : '') + ' : ' + siennes.map((c) => ech(c.numero)).join(', ')
          : 'aucune chambre saisie'}</span></div></div>
      <div class="champ"><label for="ac-n">Numéro</label>
        <input id="ac-n" maxlength="20" data-dsp-champ="numero" value="${ech(m.numero)}"
          placeholder="25" autofocus>
        <p class="aide">Le numéro que vous lui donnez déjà : 25, B12, Bungalow 3.</p></div>`;
    pied = `<button class="btn" data-dsp-fermer>Annuler</button>
      <button class="btn plein" id="dsp-valider">Ajouter</button>`;
  } else if (m.type === 'resa') {
    const libres = libresResa();
    titre = 'Nouvelle réservation';
    corps = `<div class="champ"><label for="rs-cat">Catégorie</label>
        <select id="rs-cat" data-dsp-champ="cat" data-rerendre>${catOpt}</select></div>
      <div class="duo" style="margin-bottom:0">
        <div class="champ" style="margin-bottom:6px"><label for="rs-a">Arrivée</label>
          <input type="date" id="rs-a" data-dsp-champ="debut" data-rerendre value="${m.debut}"></div>
        <div class="champ" style="margin-bottom:6px"><label for="rs-d">Départ</label>
          <input type="date" id="rs-d" data-dsp-champ="fin" data-rerendre value="${m.fin}"></div>
      </div>
      <p class="aide" style="margin:0 0 18px">${m.fin > m.debut ? libres.length + ' chambre'
        + (libres.length > 1 ? 's libres' : ' libre') + ' sur ces nuits. Le client repart le matin '
        + 'du départ : cette nuit-là reste libre.' : 'Le départ doit suivre l’arrivée.'}</p>
      <div class="duo">
        <div class="champ"><label for="rs-c">Client</label>
          <input id="rs-c" data-dsp-champ="client" maxlength="60" placeholder="M. Koné" value="${ech(m.client)}"></div>
        <div class="champ"><label for="rs-n">Chambres</label>
          <input id="rs-n" type="number" min="1" max="${Math.max(1, libres.length)}"
            data-dsp-champ="n" value="${ech(m.n)}"></div>
      </div>
      <span class="lb" style="margin-top:0">Statut</span>
      ${choix([['confirmee', 'Confirmée'], ['attente', 'En attente']], m.statut, 'statut')}`;
    pied = `<button class="btn" data-dsp-fermer>Annuler</button>
      <button class="btn plein" id="dsp-valider">Enregistrer la réservation</button>`;
  } else if (m.etape === 'form') {
    const siennes = ETAT.chambres.filter((c) => c.categorie === m.cat).sort(parNum);
    const toutes = siennes.length && siennes.every((c) => m.ids.includes(c.id));
    titre = 'Modifier en lot';
    corps = `<div class="champ"><label for="lot-cat">Catégorie</label>
        <select id="lot-cat" data-dsp-lotcat>${catOpt}</select></div>
      <div style="display:flex;justify-content:space-between;align-items:baseline">
        <span class="lb" style="margin-top:0">Chambres</span>
        <button class="dsp-lien" style="padding:0" data-dsp-toutes>${toutes ? 'Aucune' : 'Toutes'}</button></div>
      <div class="dsp-coches">${siennes.map((ch) => `<label class="dsp-radio ${m.ids.includes(ch.id)
        ? 'on' : ''}"><input type="checkbox" data-dsp-coche="${ech(ch.id)}" ${m.ids.includes(ch.id)
        ? 'checked' : ''}>${ech(ch.numero)}</label>`).join('')
        || '<p class="aide">Aucune chambre saisie dans cette catégorie.</p>'}</div>
      <div class="duo" style="margin-bottom:0">
        <div class="champ" style="margin-bottom:6px"><label for="lot-d">Première nuit</label>
          <input type="date" id="lot-d" data-dsp-champ="debut" value="${m.debut}"></div>
        <div class="champ" style="margin-bottom:6px"><label for="lot-f">Dernière nuit</label>
          <input type="date" id="lot-f" data-dsp-champ="fin" value="${m.fin}"></div>
      </div>
      <p class="aide" style="margin:0 0 18px">Les dates sont des nuits : du 24 au 26, ce sont les
        nuits du 24, du 25 et du 26.</p>
      <span class="lb" style="margin-top:0">Action</span>
      ${choix([['hs', 'Mettre hors service'], ['dispo', 'Rendre disponible'], ['vente', 'Bloquer']],
        m.action, 'action', 3)}
      <div class="champ" style="margin:0"><label for="lot-r">Raison</label>
        <input id="lot-r" data-dsp-champ="raison" maxlength="120" value="${ech(m.raison)}"
          placeholder="Ex. : maintenance, travaux, problème technique..."></div>`;
    pied = `<button class="btn" data-dsp-fermer>Annuler</button>
      <button class="btn plein" id="dsp-valider">Voir le résumé</button>`;
  } else {
    const a = analyseLot(), c = ETAT.categories.find((x) => x.slug === m.cat), n = a.retenues.length;
    const quoi = { hs: 'hors service', dispo: 'disponibles à la vente', vente: 'bloquées à la vente' }[m.action];
    const nuits = Math.round((jDt(m.fin) - jDt(m.debut)) / 864e5) + 1;
    titre = 'Modifier en lot';
    corps = `<p style="margin-bottom:10px">Vous êtes sur le point de mettre :</p>
      <div class="dsp-recap"><b>${n} chambre${n > 1 ? 's' : ''} ${ech(c.nom)}${n
        ? ' (' + a.retenues.map((x) => ech(x.numero)).join(', ') + ')' : ''}</b>
        <span>${m.debut === m.fin ? 'la nuit du ' + jLong(m.debut).toLowerCase()
          : 'du ' + jCourt(m.debut) + ' au ' + jCourt(m.fin) + ' inclus — ' + nuits + ' nuits'}</span>
        <span style="color:var(--bronze-2);margin-top:4px">${quoi}${m.raison.trim()
          ? ' — ' + ech(m.raison.trim()) : ''}.</span></div>
      ${a.conflits.length ? `<div class="alerte ambre" role="alert"><b>Attention</b>
        <span>Ces chambres ont une réservation sur cette période. Vous ne pouvez pas les mettre
        ${quoi} sans traiter d'abord la réservation : elles sont écartées.<br>${a.conflits.map((x) =>
          'Chambre ' + ech(x.ch.numero) + ' — ' + ech(x.f.client || x.f.motif || 'Fermeture') + ', du '
          + jCourt(x.f.debut) + ' au ' + jCourt(jPlus(x.f.fin, 1))).join('<br>')}</span></div>` : ''}`;
    pied = `<button class="btn" data-dsp-retour>${n ? 'Retour' : 'Annuler'}</button>
      ${n ? '<button class="btn plein" id="dsp-valider">Confirmer</button>' : ''}`;
  }
  el.innerHTML = `<div class="fond" data-dsp-fermer></div>
    <div class="dsp-boite" role="dialog" aria-modal="true" aria-label="${titre}">
      <div class="dsp-th"><h2>${titre}</h2>
        <button class="dsp-x" data-dsp-fermer aria-label="Fermer">×</button></div>
      <div class="dsp-tc">${corps}
        ${m.erreur ? `<p class="msg mal" role="alert" style="margin-top:14px">${ech(m.erreur)}</p>` : ''}</div>
      <div class="dsp-tp">${pied}</div>
    </div>`;
}

async function validerModal() {
  const m = DSP.modal;
  const dire = (t) => { m.erreur = t; rendreModal(); };
  if (m.type === 'chambre') {
    if (!String(m.numero || '').trim()) return dire('Donnez-lui son numéro.');
    const b0 = $('#dsp-valider');
    if (b0) { b0.disabled = true; b0.textContent = 'Enregistrement…'; }
    const r = await appel('enregistrer', { type: 'chambre',
      entree: { numero: String(m.numero).trim(), categorie: m.cat } });
    if (!r.ok) return dire(r.message || "Ça n'a pas pu être enregistré.");
    ETAT.chambres = (ETAT.chambres || []).concat([r.entree]);
    /* La categorie s'ouvre pour qu'on voie la chambre qu'on vient de poser. */
    DSP.ouvertes[m.cat] = true;
    DSP.modal = null; rendreModal(); rendre();
    return notifier('Chambre ' + r.entree.numero + ' ajoutée');
  }
  const echec = (err) => { if (err.message !== 'session') dire('Impossible d’enregistrer les modifications. '
    + 'Vérifiez votre connexion puis réessayez. ' + (err.message || '')); rendre(); };
  const btn = $('#dsp-valider');
  if (m.type === 'resa') {
    const libres = libresResa(), n = Number(m.n) || 0;
    if (!m.client.trim()) return dire('Indiquez le nom du client.');
    if (!m.debut || !m.fin || m.fin <= m.debut) return dire('Le départ doit suivre l’arrivée d’au moins une nuit.');
    if (n < 1 || n > libres.length) {
      return dire(libres.length ? 'Il ne reste que ' + libres.length + ' chambre'
        + (libres.length > 1 ? 's libres' : ' libre') + ' sur ces nuits.' : 'Aucune chambre libre sur ces nuits.');
    }
    if (btn) { btn.disabled = true; btn.textContent = 'Enregistrement…'; }
    try {
      for (const ch of libres.slice(0, n)) {
        await poserF({ cible: ch.id, debut: m.debut, fin: jPlus(m.fin, -1), nature: 'client',
          client: m.client.trim(), statut: m.statut, motif: '' });
      }
    } catch (err) { return echec(err); }
    DSP.modal = null; rendreModal(); rendre();
    return notifier('Réservation enregistrée');
  }
  if (m.etape === 'form') {
    if (!m.ids.length) return dire('Choisissez au moins une chambre.');
    if (!m.debut || !m.fin) return dire('Indiquez la première et la dernière nuit.');
    if (m.fin < m.debut) return dire('La dernière nuit précède la première.');
    m.etape = 'recap'; m.erreur = '';
    return rendreModal();
  }
  const { retenues } = analyseLot();
  if (btn) { btn.disabled = true; btn.textContent = 'Enregistrement…'; }
  try {
    await libererF(retenues.map((c) => c.id), m.debut, m.fin);
    if (m.action !== 'dispo') {
      const nature = m.action === 'hs' ? 'hors-service' : 'vente';
      for (const ch of retenues) {
        await poserF({ cible: ch.id, debut: m.debut, fin: m.fin, nature,
          motif: m.raison.trim() || (nature === 'hors-service' ? 'Hors service' : 'Fermée à la vente') });
      }
    }
  } catch (err) { return echec(err); }
  DSP.modal = null; rendreModal(); rendre();
  notifier('Modifications enregistrées');
}

/* ── Événements ───────────────────────────────────────────────────────
   Appelée en tête de l écouteur de clics de la page : rend true si le clic
   concernait le calendrier. */
function clicDsp(e) {
  const t = e.target, q = (s) => t.closest(s);
  let b;
  if ((b = q('[data-dsp-fermer]'))) { DSP.tiroir = null; DSP.modal = null; rendreTiroir(); rendreModal(); return true; }
  if ((b = q('[data-dsp-pas]'))) { decalerDsp(Number(b.dataset.dspPas)); return true; }
  if ((b = q('[data-dsp-vue]'))) { allerDsp(DSP.focus, b.dataset.dspVue); return true; }
  if ((b = q('[data-dsp-auj]'))) { allerDsp(AUJ()); return true; }
  if ((b = q('[data-dsp-jour]'))) { allerDsp(b.dataset.dspJour, 'jour'); return true; }
  if ((b = q('[data-dsp-mode]'))) { DSP.mode = b.dataset.dspMode; rendreDsp(); return true; }
  if ((b = q('[data-dsp-ouvrir]'))) {
    const s = b.dataset.dspOuvrir;
    DSP.ouvertes[s] = b.getAttribute('aria-expanded') !== 'true';
    rendreDsp(); return true;
  }
  if ((b = q('[data-dsp-fiche]'))) { ouvrirFiche(b.dataset.dspFiche); return true; }
  if ((b = q('[data-dsp-ajout]'))) {
    DSP.modal = { type: 'chambre', cat: b.dataset.dspAjout, numero: '', erreur: '' };
    rendreModal(); return true;
  }
  /* Retirer une chambre et rouvrir une fermeture passent par les
     gestionnaires de la page, qui les portent deja. On ferme seulement le
     tiroir avant, sinon il resterait ouvert sur une chambre disparue. */
  if (q('[data-oter]') && DSP.tiroir) { DSP.tiroir = null; rendreTiroir(); return false; }
  if (q('[data-rouvrir]') && DSP.tiroir) { DSP.tiroir = null; rendreTiroir(); return false; }
  if ((b = q('[data-dsp-cat]'))) { ouvrirCat(b.dataset.dspCat, b.dataset.nuit); return true; }
  if ((b = q('[data-dsp-ch]'))) { ouvrirChambre(b.dataset.dspCh, b.dataset.nuit); return true; }
  if (q('[data-dsp-voirtout]')) { DSP.voirTout = !DSP.voirTout; rendreDsp(); return true; }
  if (t.id === 'dsp-resa-btn') { ouvrirResa(); return true; }
  if (t.id === 'dsp-lot-btn') { ouvrirLot(); return true; }
  if ((b = q('[data-dsp-ajust]')) && DSP.tiroir) {
    const tr = DSP.tiroir, v = Math.max(0, Math.min(tr.max, tr.ajust + Number(b.dataset.dspAjust)));
    tr.ajust = v;
    tr.statut = v > 0 ? 'dispo' : (tr.statut === 'hs' ? 'hs' : 'complet');
    rendreTiroir(); return true;
  }
  if (t.id === 'dsp-enreg') { enregistrerTiroir(); return true; }
  if (t.id === 'dsp-fenreg') { enregistrerFiche(); return true; }
  if ((b = q('[data-dsp-confirmer]'))) { confirmerRetenue(b.dataset.dspConfirmer); return true; }
  if ((b = q('[data-dsp-opt]')) && DSP.modal) { DSP.modal[b.dataset.dspOpt] = b.dataset.v; DSP.modal.erreur = ''; rendreModal(); return true; }
  if (q('[data-dsp-toutes]') && DSP.modal) {
    const siennes = ETAT.chambres.filter((c) => c.categorie === DSP.modal.cat).map((c) => c.id);
    DSP.modal.ids = siennes.every((id) => DSP.modal.ids.includes(id)) ? [] : siennes;
    rendreModal(); return true;
  }
  if (q('[data-dsp-retour]') && DSP.modal) { DSP.modal.etape = 'form'; rendreModal(); return true; }
  if (t.id === 'dsp-valider') { validerModal(); return true; }
  return false;
}

document.addEventListener('input', (e) => {
  /* La recherche redessine a chaque frappe, mais le champ est recree par le
     rendu : on lui rend le curseur, sinon on tape une lettre et on perd le
     focus. */
  if (e.target.id === 'dsp-q') {
    DSP.f.texte = e.target.value;
    rendreDsp();
    const c = $('#dsp-q');
    if (c) { c.focus(); c.setSelectionRange(c.value.length, c.value.length); }
    return;
  }
  if (e.target.id === 'dsp-com' && DSP.tiroir) DSP.tiroir.commentaire = e.target.value;
  const fc = e.target.dataset && e.target.dataset.dspFchamp;
  if (fc && DSP.tiroir) { DSP.tiroir[fc] = e.target.value; DSP.tiroir.erreur = ''; }
  const k = e.target.dataset && e.target.dataset.dspChamp;
  if (k && DSP.modal && !e.target.hasAttribute('data-rerendre')) DSP.modal[k] = e.target.value;
});
document.addEventListener('change', (e) => {
  const t = e.target;
  if (t.id === 'dsp-fcat') { DSP.f.cat = t.value; return rendreDsp(); }
  if (t.id === 'dsp-fetage') { DSP.f.etage = t.value; return rendreDsp(); }
  if (t.id === 'dsp-fstat') { DSP.f.statut = t.value; return rendreDsp(); }
  if (t.id === 'dsp-flibres') { DSP.f.libres = t.checked; return rendreDsp(); }
  if (t.id === 'dsp-mois') {
    const v = t.value, auj = AUJ();
    return allerDsp(v === auj.slice(0, 7) ? auj : v + '-01');
  }
  if (t.name === 'dsp-fstatut' && DSP.tiroir) {
    DSP.tiroir.statut = t.value; DSP.tiroir.erreur = '';
    return rendreTiroir();
  }
  if (t.dataset && t.dataset.dspFchamp && DSP.tiroir) {
    DSP.tiroir[t.dataset.dspFchamp] = t.value;
    return;
  }
  if (t.name === 'dsp-statut' && DSP.tiroir) {
    const tr = DSP.tiroir;
    tr.statut = t.value;
    if (tr.mode === 'cat') tr.ajust = t.value === 'dispo' ? (tr.ajust > 0 ? tr.ajust : tr.max) : 0;
    return rendreTiroir();
  }
  if (!DSP.modal) return;
  if (t.hasAttribute('data-dsp-lotcat')) {
    DSP.modal.cat = t.value;
    DSP.modal.ids = ETAT.chambres.filter((c) => c.categorie === t.value).map((c) => c.id);
    return rendreModal();
  }
  if (t.dataset.dspCoche) {
    const id = t.dataset.dspCoche, ids = DSP.modal.ids;
    DSP.modal.ids = t.checked ? ids.concat([id]) : ids.filter((x) => x !== id);
    return rendreModal();
  }
  const k = t.dataset && t.dataset.dspChamp;
  if (k) { DSP.modal[k] = t.value; DSP.modal.erreur = ''; if (t.hasAttribute('data-rerendre')) rendreModal(); }
});
document.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape' || (!DSP.tiroir && !DSP.modal)) return;
  DSP.tiroir = null; DSP.modal = null; rendreTiroir(); rendreModal();
});
