/* ──────────────────────────────────────────────────────────────────────
   Module « Referencement » — ce que Google affiche pour chaque page.

   Tenu par l'agence de communication (profil Communication), qui regle et
   PUBLIE elle-meme. Quatre ecrans :
   - la liste des pages (et celle des chambres) : le titre et la
     description tels que Google les montrera, le mot-cle vise, un etat ;
   - la fiche d'une page : le formulaire, les apercus Google et WhatsApp,
     les verifications ;
   - les redirections : les anciennes adresses et ou elles menent ;
   - l'historique des publications, et le retour a une version precedente.

   DEUX TEMPS : enregistrer prepare, « Publier » met en ligne (voir
   api/_seo.js). Les valeurs par defaut — ce que le site ecrit sans
   reglage — viennent de /donnees/seo-pages.json (build-sitemap.py).

   CE QUI PROTEGE, C'EST LE SERVEUR : il revérifie le droit
   « referencement » a chaque ecriture. Ici on n'affiche que ce qui servira.
   ────────────────────────────────────────────────────────────────────── */

const RF = {
  manifeste: null,     // /donnees/seo-pages.json ; null : pas encore charge
  enLigne: undefined,  // /seo-publication.json : { id, t } ou null si absent
  onglet: 'pages',     // pages | chambres | carnet | redirections | historique
  edite: null,         // l'identifiant de la page ouverte
  saisie: null,        // ce que le formulaire contient
  photos: false,       // la grille des photos est ouverte
  attendue: null,      // { id, depuis, message } : publication envoyee, pas encore vue en ligne
  veille: null,        // le minuteur qui guette la mise en ligne
  erreur: '',
};

/* Doit rester identique a api/_seo.js. */
const RF_SUFFIXE = ' — Hôtel Evannath';
const RF_TITRE_MAX = 60, RF_DESC_MIN = 70, RF_DESC_MAX = 160;
const RF_CHAMPS_SITE = ['titre', 'description', 'image', 'masquer'];
const rfEmpreinte = (p) => JSON.stringify(RF_CHAMPS_SITE.map((k) => (p && p[k]) || ''));

const rfPeut = () => (typeof peut === 'function' ? peut('referencement') : false);
const rfSeo = () => ETAT.seo || {};
const rfDerniere = () => { const l = rfSeo().publications || []; return l.length ? l[l.length - 1] : null; };

/** Ce qui attend d'etre publie (meme calcul que le serveur). */
function rfAttente() {
  const seo = rfSeo();
  const pub = rfDerniere() || { pages: {}, redirections: [] };
  const actuel = seo.pages || {};
  const ids = new Set(Object.keys(actuel).concat(Object.keys(pub.pages || {})));
  const pages = [...ids].filter((id) => rfEmpreinte(actuel[id]) !== rfEmpreinte((pub.pages || {})[id]));
  const cle = (l) => (l || []).map((r) => r.de + ' → ' + r.vers);
  const avant = new Set(cle(pub.redirections)), apres = new Set(cle(seo.redirections));
  const ajoutees = [...apres].filter((x) => !avant.has(x)).length;
  const retirees = [...avant].filter((x) => !apres.has(x)).length;
  return { pages, ajoutees, retirees, total: pages.length + ajoutees + retirees };
}

/* ── Chargement ───────────────────────────────────────────────────────── */
async function rfCharger() {
  const [m, l] = await Promise.all([
    fetch('/donnees/seo-pages.json', { cache: 'no-store' }).then((r) => (r.ok ? r.json() : null)).catch(() => null),
    rfLireEnLigne(),
  ]);
  RF.manifeste = m || { pages: [], site: '', prospection: false };
  RF.enLigne = l;
  if (VUE === 'seo') rendre();
}
/* Ce que le site en ligne porte : seo-publication.json est ecrit par
   l'etape de construction (api/_seo_appliquer.js). Absent : rien de publie
   n'est encore en ligne. */
async function rfLireEnLigne() {
  try {
    const r = await fetch('/seo-publication.json?t=' + Date.now(), { cache: 'no-store' });
    if (!r.ok) return null;
    return await r.json();
  } catch (e) { return null; }
}
/* Guetter la mise en ligne d'une publication : toutes les 10 secondes,
   six minutes au plus. Un deploiement prend une a deux minutes. */
function rfGuetter() {
  clearTimeout(RF.veille);
  if (!RF.attendue) return;
  RF.veille = setTimeout(async () => {
    RF.enLigne = await rfLireEnLigne();
    if (RF.enLigne && RF.attendue && RF.enLigne.id === RF.attendue.id) {
      RF.attendue = null;
      if (typeof notifier === 'function') notifier('Publication en ligne');
    } else if (RF.attendue && Date.now() - RF.attendue.depuis > 6 * 60_000) {
      RF.attendue.lente = true;
    }
    if (VUE === 'seo' && !RF.edite) rendre();
    if (RF.attendue && !RF.attendue.lente) rfGuetter();
  }, 10_000);
}

/* ── Les valeurs d'une page : reglage publie ou saisi, sinon le site ────── */
function rfReglage(id) { return (rfSeo().pages || {})[id] || {}; }
function rfVaut(p, r) {
  r = r || {};
  return {
    titre: r.titre ? r.titre + RF_SUFFIXE : p.titre,
    description: r.description || p.description,
    image: r.image || p.image,
    masquee: !!r.masquer || p.hors_index,
    motcle: r.motcle || '',
  };
}

/* Les mots qui comptent dans un mot-cle : « hôtel à Assinie » -> hotel, assinie. */
const RF_VIDES = new Set(['a', 'au', 'aux', 'de', 'des', 'du', 'la', 'le', 'les', 'l', 'd', 'en', 'et',
  'pour', 'sur', 'un', 'une', 'avec', 'pres', 'the', 'in', 'of']);
const rfPlat = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
  .replace(/[’']/g, ' ');
const rfMots = (s) => rfPlat(s).split(/[^a-z0-9]+/).filter((w) => w.length > 1 && !RF_VIDES.has(w));
/* Les mots tels que l'agence les a tapes, accents compris : c'est ce qu'on
   lui montre. La comparaison, elle, se fait sans accents. */
const rfMotsTapes = (s) => String(s || '').split(/[\s'’,;:.!?()-]+/).filter((w) => rfMots(w).length);
/* Un mot est present, au singulier ou au pluriel : « chambre » trouve « chambres ». */
const rfContient = (texte, mot) => new RegExp('(^|[^a-z0-9])' + mot.replace(/s$/, '') + 's?($|[^a-z0-9])')
  .test(rfPlat(texte));
const rfManquants = (texte, motcle) => rfMotsTapes(motcle).filter((m) => rfMots(m).some((x) => !rfContient(texte, x)));

/** L'etat d'une page dans la liste : la chose la plus urgente a dire. */
function rfEtat(p, attente, titres) {
  const r = rfReglage(p.id);
  const v = rfVaut(p, r);
  if (attente.pages.includes(p.id)) return ['attend', 'Modifiée · à publier'];
  if (v.masquee) return ['dort', 'Masquée de Google'];
  if (v.titre.length > RF_TITRE_MAX) return ['fini', 'Titre trop long', v.titre.length + ' caractères pour ' + RF_TITRE_MAX];
  if (!v.description) return ['fini', 'Description vide'];
  if ((titres.get(v.titre) || 0) > 1) return ['fini', 'Titre en double'];
  if (v.description.length > RF_DESC_MAX) return ['ambre', 'Description longue',
    v.description.length + ' caractères : Google coupe vers ' + (RF_DESC_MAX - 5)];
  if (!v.motcle) return ['ambre', 'Mot-clé non choisi'];
  if (rfManquants(v.titre, v.motcle).length) return ['ambre', 'Mot-clé absent du titre'];
  return ['vif', 'Correct'];
}

const rfQuand = (iso) => {
  const d = new Date(iso);
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' }).replace(/^1 /, '1er ')
    + ' à ' + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }).replace(':', ' h ');
};
const rfCourt = (iso) => {
  const d = new Date(iso);
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }) + ' · '
    + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }).replace(':', ' h ');
};
const rfHote = () => { try { return new URL(RF.manifeste.site).host; } catch (e) { return location.host; } };
const rfPluriel = (n, un, plusieurs) => n + ' ' + (n > 1 ? plusieurs : un);

/* ── La vue ───────────────────────────────────────────────────────────── */
function vueReferencement() {
  if (!RF.manifeste) {
    rfCharger();
    return '<div class="entete"><div><h1 class="t">Référencement</h1></div></div><p class="sous">Chargement…</p>';
  }
  if (RF.edite) return rfFiche();
  const attente = rfAttente();
  const pub = rfDerniere();
  const ecrire = rfPeut();
  const pages = RF.manifeste.pages;
  const nb = (g) => pages.filter((p) => p.groupe === g).length;
  const articles = (ETAT.carnet || []).filter((a) => a.publie !== false);

  let h = `<div class="entete">
      <div><h1 class="t">Référencement</h1>
      <p class="sous">Ce que Google affiche pour chaque page du site : le titre, la description et l'image de partage.</p></div>
      ${ecrire ? `<button class="btn plein" id="rf-publier" ${attente.total && !RF.attendue ? '' : 'disabled style="opacity:.55"'}
        >${RF.attendue ? 'Publication en cours…' : 'Publier les modifications'}</button>` : ''}
    </div>
    ${avertissement()}`;

  if (RF.manifeste.prospection) {
    h += `<div class="rf-bandeau demo"><p><b>Le site est encore en démonstration</b> : Google ne l'indexe pas.
      Vos réglages s'appliquent quand même aux pages, et compteront dès la mise en ligne.</p></div>`;
  }
  h += rfBandeauPublication(attente, pub);
  if (RF.erreur) h += `<div class="rf-bandeau mal"><p>${ech(RF.erreur)}</p></div>`;

  if (pub) {
    const vu = RF.enLigne && RF.enLigne.id === pub.id;
    h += `<div class="rf-pub"><span><i class="rf-pt${vu ? '' : ' non'}"></i>Dernière publication :
      <b>${ech(rfQuand(pub.t))}</b>, par <b>${ech(pub.par)}</b></span>
      <button data-rf-onglet="historique">Historique des publications</button></div>`;
  }

  const onglets = [['pages', 'Pages', nb('pages')], ['chambres', 'Chambres', nb('chambres')],
    ['carnet', 'Carnet', articles.length], ['redirections', 'Redirections', (rfSeo().redirections || []).length]];
  h += '<div class="rf-onglets" role="tablist">' + onglets.map(([k, l, n]) =>
    `<button role="tab" data-rf-onglet="${k}" class="${RF.onglet === k ? 'on' : ''}"
      aria-selected="${RF.onglet === k}">${l} <i>${n}</i></button>`).join('') + '</div>';

  if (RF.onglet === 'pages' || RF.onglet === 'chambres') h += rfListe(RF.onglet, attente);
  else if (RF.onglet === 'carnet') h += rfCarnet(articles);
  else if (RF.onglet === 'redirections') h += rfRedirections();
  else h += rfHistorique();
  return h;
}

function rfBandeauPublication(attente, pub) {
  if (RF.attendue) {
    if (RF.attendue.lente) {
      return `<div class="rf-bandeau mal"><p><b>La publication n'est pas encore en ligne</b> après six minutes.
        Le déploiement a peut-être échoué : prévenez le développeur. Rien n'est perdu, elle est enregistrée.</p></div>`;
    }
    return `<div class="rf-bandeau encours"><div class="rf-roue"></div><p><b>Publication en cours</b> :
      ${ech(RF.attendue.message || '')} Vous pouvez continuer à travailler.</p></div>`;
  }
  let h = '';
  if (attente.total) {
    const noms = attente.pages.map((id) => (RF.manifeste.pages.find((p) => p.id === id) || { nom: id }).nom);
    const red = [attente.ajoutees ? rfPluriel(attente.ajoutees, 'redirection ajoutée', 'redirections ajoutées') : '',
      attente.retirees ? rfPluriel(attente.retirees, 'redirection retirée', 'redirections retirées') : '']
      .filter(Boolean);
    h += `<div class="rf-bandeau attente"><p><b>${rfPluriel(attente.total, 'modification enregistrée',
      'modifications enregistrées')}, pas encore en ligne</b> (${ech(noms.concat(red).join(', '))}).
      ${rfPeut() ? 'Elles apparaîtront sur le site une à deux minutes après « Publier les modifications ».'
        : 'L’agence ou un administrateur les publiera.'}</p></div>`;
  }
  /* Publiee, mais jamais vue en ligne : sans crochet de deploiement, elle
     attend le prochain deploiement. On le dit, plutot que de laisser croire. */
  if (pub && RF.enLigne !== undefined && !(RF.enLigne && RF.enLigne.id === pub.id)) {
    h += `<div class="rf-bandeau mal"><p><b>La dernière publication n'est pas encore sur le site.</b>
      ${ETAT.seoCrochet === false
        ? 'Le crochet de déploiement (SEO_DEPLOY_HOOK) n’est pas réglé : elle partira au prochain déploiement du site.'
        : 'Si cela dure plus de quelques minutes, prévenez le développeur.'}</p></div>`;
  }
  return h;
}

function rfListe(groupe, attente) {
  const toutes = RF.manifeste.pages;
  const titres = new Map();
  for (const p of toutes) { const t = rfVaut(p, rfReglage(p.id)).titre; titres.set(t, (titres.get(t) || 0) + 1); }
  const lignes = toutes.filter((p) => p.groupe === groupe).map((p) => {
    const v = rfVaut(p, rfReglage(p.id));
    const [cl, mot, detail] = rfEtat(p, attente, titres);
    return `<div class="rf-ligne">
      <div class="pg"><b>${ech(p.nom)}</b><span>${ech(p.chemin)}</span></div>
      <div class="gt"><div class="t">${ech(v.titre)}</div>
        <div class="d${v.description ? '' : ' vide'}">${v.description ? ech(v.description)
          : 'Aucune description : Google choisira un extrait au hasard.'}</div></div>
      <div class="mc-col"><span class="rf-mc${v.motcle ? '' : ' vide'}" title="${ech(v.motcle)}">${
        v.motcle ? ech(v.motcle) : 'aucun mot-clé'}</span></div>
      <span class="etat ${cl}"${detail ? ' title="' + ech(detail) + '"' : ''}>${ech(mot)}</span>
      <div class="rf-gestes"><a class="rf-voir" href="${ech(p.chemin)}" target="_blank" rel="noopener">Voir ${ic('externe')}</a>
        <button class="btn mince" data-rf-page="${ech(p.id)}">${rfPeut() ? 'Modifier' : 'Détails'}</button></div>
    </div>`;
  }).join('');
  return `<div class="carte" style="padding:18px 20px">
    <h2 class="bloc-t" style="margin-bottom:6px">${groupe === 'pages' ? 'Les pages du site' : 'Les fiches des chambres'}</h2>
    <p class="aide" style="margin:0 0 14px">En bleu : le titre tel qu'il apparaîtra dans Google. En gris : la
    description. Puis le mot-clé visé par la page, et ce qu'il reste à faire.</p>
    ${lignes}</div>`;
}

function rfCarnet(articles) {
  const etat = (a) => (a.date && a.date > new Date().toISOString().slice(0, 10)
    ? ['dort', 'Programmé'] : ['vif', 'En ligne']);
  const lignes = articles.slice().sort((a, b) => String(b.date || '').localeCompare(String(a.date || ''))).map((a) => {
    const titre = a.titre + ' — Le Carnet d’Assinie · Hôtel Evannath';
    const [cl, mot] = (a.chapo || '').length > RF_DESC_MAX ? ['ambre', 'Chapô long'] : etat(a);
    return `<div class="rf-ligne">
      <div class="pg"><b>Article</b><span>/carnet-${ech(a.slug)}</span></div>
      <div class="gt"><div class="t">${ech(titre)}</div><div class="d">${ech(a.chapo)}</div></div>
      <div class="mc-col"></div>
      <span class="etat ${cl}">${ech(mot)}</span>
      <div class="rf-gestes">${a.slug ? `<a class="rf-voir" href="/carnet-${ech(a.slug)}" target="_blank" rel="noopener">Voir ${ic('externe')}</a>` : ''}
        <button class="btn mince" data-rf-article="${ech(a.id)}">Modifier dans Le Carnet</button></div>
    </div>`;
  }).join('');
  return `<div class="carte" style="padding:18px 20px">
    <h2 class="bloc-t" style="margin-bottom:6px">Les articles du Carnet</h2>
    <p class="aide" style="margin:0 0 14px">Le titre et le chapô d'un article sont son titre et sa description dans
    Google. Ils se règlent dans « Le Carnet », et sont en ligne dès l'enregistrement : rien à publier ici.</p>
    ${lignes || '<p class="aide">Aucun article publié pour le moment.</p>'}</div>`;
}

function rfRedirections() {
  const liste = (rfSeo().redirections || []).slice().sort((a, b) => String(b.ajoute || '').localeCompare(String(a.ajoute || '')));
  const pub = rfDerniere();
  const publiees = new Set(((pub && pub.redirections) || []).map((r) => r.de + ' → ' + r.vers));
  const lignes = liste.map((r) => `<div class="rf-red">
      <code>${ech(r.de)}</code><span class="fleche">→</span><code>${ech(r.vers)}</code>
      <span class="n">${publiees.has(r.de + ' → ' + r.vers) ? '' : '<b style="color:var(--bronze-2)">À publier</b> · '}Ajoutée le
        ${ech(new Date(r.ajoute).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }))} par ${ech(r.par || '')}</span>
      ${rfPeut() ? `<button class="btn mince danger" data-rf-retirer="${ech(r.id)}">Retirer</button>` : '<span></span>'}
    </div>`).join('');
  const chemins = RF.manifeste.pages.map((p) => `<option value="${ech(p.chemin)}">${ech(p.nom)}</option>`).join('')
    + '<option value="/carnet">Le Carnet</option><option value="/reserver">Réserver</option>';
  return `<div class="carte" style="padding:18px 20px">
    <h2 class="bloc-t" style="margin-bottom:6px">Redirections</h2>
    <p class="aide" style="margin:0 0 14px">Quand une ancienne adresse est visitée — un lien de l'ancien site,
    partagé ou gardé par Google —, le visiteur et Google sont envoyés vers la nouvelle. Elles fonctionnent dès
    leur publication.</p>
    ${lignes || '<p class="aide">Aucune redirection pour le moment.</p>'}
    ${rfPeut() ? `<form class="rf-ajout" id="rf-form-red">
      <div class="champ"><label for="rf-de">Ancienne adresse</label>
        <input id="rf-de" placeholder="/nos-chambres.html" autocomplete="off" required></div>
      <div class="champ"><label for="rf-vers">Nouvelle adresse</label>
        <input id="rf-vers" list="rf-chemins" placeholder="/chambres" autocomplete="off" required>
        <datalist id="rf-chemins">${chemins}</datalist></div>
      <button class="btn" type="submit">Ajouter</button>
    </form><p class="msg" id="rf-msg-red"></p>` : ''}
  </div>`;
}

function rfHistorique() {
  const l = (rfSeo().publications || []).slice().reverse();
  const ecrire = rfPeut();
  const lignes = l.map((p, i) => {
    const vu = RF.enLigne && RF.enLigne.id === p.id;
    const etat = i === 0 ? (vu ? ['vif', 'En ligne'] : ['attend', 'Pas encore en ligne'])
      : (vu ? ['vif', 'En ligne'] : ['dort', 'Remplacée']);
    return `<div class="rf-hist">
      <div class="q">${ech(rfCourt(p.t))}<span>par ${ech(p.par)}</span></div>
      <div class="c">${ech(p.resume)}</div>
      <span class="etat ${etat[0]}">${etat[1]}</span>
      <div>${i > 0 && ecrire ? `<button class="btn mince" data-rf-retablir="${ech(p.id)}">Revenir à cette version</button>` : ''}</div>
    </div>`;
  }).join('');
  return `<div class="carte" style="padding:18px 20px">
    <h2 class="bloc-t" style="margin-bottom:6px">Historique des publications</h2>
    <p class="aide" style="margin:0 0 14px">Chaque publication est conservée (les ${l.length > 1 ? l.length + ' dernières' : 'dernières'}).
    En cas d'erreur, un clic remet le site dans l'état d'une publication précédente.</p>
    ${lignes || '<p class="aide">Rien n’a encore été publié.</p>'}</div>
    <p class="aide">Qui peut publier : les profils <b>Communication</b> (l'agence) et <b>Administrateur</b>.
    Chaque publication est aussi notée dans le journal d'activité.</p>`;
}

/* ── La fiche d'une page ─────────────────────────────────────────────── */
function rfOuvrir(id) {
  const p = RF.manifeste.pages.find((x) => x.id === id);
  if (!p) return;
  const r = rfReglage(id);
  RF.edite = id;
  RF.photos = false;
  RF.saisie = { motcle: r.motcle || '', titre: r.titre || rfDebutSite(p), description: r.description || p.description,
    image: r.image || p.image, masquer: !!r.masquer };
}

function rfFiche() {
  const p = RF.manifeste.pages.find((x) => x.id === RF.edite);
  const s = RF.saisie;
  const ecrire = rfPeut();
  const dis = ecrire ? '' : ' disabled';
  return `<div class="entete">
      <div><p class="sous" style="margin:0 0 4px"><a href="#" data-rf-retour style="color:inherit">Référencement</a>
        › ${p.groupe === 'chambres' ? 'Chambres' : 'Pages'}</p>
      <h1 class="t">${ech(p.nom)}</h1>
      <p class="sous">${ech(RF.manifeste.site + (p.chemin === '/' ? '/' : p.chemin))} ·
        <a class="rf-voir" href="${ech(p.chemin)}" target="_blank" rel="noopener">Voir la page ${ic('externe')}</a></p></div>
    </div>
    <div class="rf-grille">
    <form class="carte" id="rf-form" autocomplete="off">
      <h2 class="bloc-t">Ce que Google affiche</h2>
      <div class="champ"><label for="rf-motcle">Mot-clé visé</label>
        <input id="rf-motcle" value="${ech(s.motcle)}" placeholder="hôtel Assinie" maxlength="60"${dis}>
        <p class="aide">Ce que vos clients tapent dans Google pour trouver cette page. Un seul par page, et pas le même
        sur deux pages.</p></div>
      <div class="champ"><label for="rf-titre">Titre Google <span class="rf-cpt" id="rf-cpt-t"></span></label>
        <div class="rf-prefixe"><input id="rf-titre" value="${ech(s.titre)}" maxlength="80"
          placeholder="${ech(rfDebutSite(p) ? '' : 'Vide : le titre actuel est gardé')}"${dis}><span>${ech(RF_SUFFIXE.trim())}</span></div>
        <p class="aide">La fin « ${ech(RF_SUFFIXE.trim())} » est ajoutée automatiquement. Le compteur la prend en compte.</p>
        <p class="rf-defaut">Titre actuel du site : « ${ech(p.titre)} »</p></div>
      <div class="champ"><label for="rf-desc">Description <span class="rf-cpt" id="rf-cpt-d"></span></label>
        <textarea id="rf-desc" style="min-height:92px" maxlength="300"${dis}>${ech(s.description)}</textarea>
        <p class="aide">Deux phrases qui donnent envie de cliquer. Elles s'affichent sous le titre.</p></div>
      <div class="champ"><label>Image de partage</label>
        <div class="rf-img"><img id="rf-img" src="/img/opt/${ech(s.image)}.jpg" alt="">
          <div>${ecrire ? `<button type="button" class="btn mince" data-rf-photos>${RF.photos ? 'Fermer' : 'Changer l’image'}</button>` : ''}
          <p class="aide">Affichée quand le lien est partagé sur WhatsApp ou Facebook.</p></div></div>
        ${RF.photos ? `<div class="grille-img" style="margin-top:12px;max-height:320px;overflow:auto">${(ETAT.images || []).map((n) =>
          `<button type="button" data-rf-img="${ech(n)}" class="${s.image === n ? 'on' : ''}"><img src="/img/opt/${ech(n)}.jpg"
            alt="" loading="lazy"></button>`).join('')}</div>` : ''}</div>
      <div class="champ" style="margin-top:8px">
        <label style="display:flex;align-items:center;gap:10px;text-transform:none;letter-spacing:0;font-size:14px;color:var(--cream)">
        <input type="checkbox" id="rf-masquer" style="width:auto" ${s.masquer || p.hors_index ? 'checked' : ''}
          ${p.hors_index || !ecrire ? 'disabled' : ''}> Ne pas afficher cette page dans Google</label>
        ${p.hors_index ? '<p class="aide">Cette page est toujours masquée : elle n’a pas sa place dans les résultats.</p>' : ''}</div>
      <div class="champ"><label>Vérifications</label><ul class="rf-verifs" id="rf-verifs"></ul></div>
      <div class="pied">
        ${ecrire ? '<button class="btn plein" type="submit">Enregistrer</button>' : ''}
        <button class="btn" type="button" data-rf-retour>${ecrire ? 'Annuler' : 'Retour'}</button>
        ${ecrire && Object.keys(rfReglage(p.id)).length ? '<button class="btn mince" type="button" data-rf-defaut>Revenir au texte du site</button>' : ''}
        <span class="msg" id="rf-msg"></span>
      </div>
      ${ecrire ? '<p class="aide">Enregistrer ne publie pas encore : utilisez ensuite « Publier les modifications ».</p>' : ''}
    </form>
    <div id="rf-apercus"></div>
    </div>`;
}

/** Ce que le formulaire contient, tel que Google le verra. */
function rfLire() {
  const f = $('#rf-form');
  if (!f) return;
  RF.saisie.motcle = $('#rf-motcle').value;
  RF.saisie.titre = $('#rf-titre').value;
  RF.saisie.description = $('#rf-desc').value;
  const m = $('#rf-masquer');
  if (m && !m.disabled) RF.saisie.masquer = m.checked;
}

/* Les apercus, les compteurs et les verifications suivent la frappe, sans
   redessiner le formulaire (le curseur resterait sinon en route). */
function rfApres() {
  if (VUE !== 'seo' || !RF.edite || !$('#rf-form')) return;
  const p = RF.manifeste.pages.find((x) => x.id === RF.edite);
  const s = RF.saisie;
  /* Vide : ce que le site ecrit. C'est aussi ce que le serveur fera. */
  const titre = s.titre.trim() ? s.titre.trim() + RF_SUFFIXE : p.titre;
  const desc = s.description.trim() || p.description;
  const masquee = s.masquer || p.hors_index;

  const ct = $('#rf-cpt-t'), cd = $('#rf-cpt-d');
  ct.textContent = titre.length + ' / ' + RF_TITRE_MAX;
  ct.className = 'rf-cpt ' + (titre.length <= RF_TITRE_MAX ? 'ok' : 'trop');
  cd.textContent = desc.length + ' / ' + (RF_DESC_MAX - 5);
  cd.className = 'rf-cpt ' + (desc.length >= RF_DESC_MIN && desc.length <= RF_DESC_MAX ? 'ok' : 'trop');

  const court = desc.length > RF_DESC_MAX - 5 ? desc.slice(0, RF_DESC_MAX - 7).replace(/\s+\S*$/, '') + '…' : desc;
  const host = rfHote();
  $('#rf-apercus').innerHTML = `<div class="carte">
      <span class="rf-lbl">Aperçu dans Google</span>
      ${masquee ? '<p class="aide" style="margin:0 0 10px;color:var(--err)">Masquée : cette page n’apparaîtra pas dans Google.</p>' : ''}
      <div class="rf-serp${masquee ? ' masque' : ''}"><div class="site"><div class="ic">E</div><div><b>Hôtel Evannath</b>
        <span>https://${ech(host)}${p.chemin === '/' ? '' : ech(p.chemin)}</span></div></div>
      <div class="t">${ech(titre.length > 65 ? titre.slice(0, 62) + '…' : titre)}</div>
      <div class="d">${ech(court)}</div></div>
    </div>
    <div class="carte">
      <span class="rf-lbl">Aperçu d'un partage WhatsApp</span>
      <div class="rf-wa"><div class="bulle"><img src="/img/opt/${ech(s.image)}.jpg" alt="">
        <div class="c"><b>${ech(titre)}</b><span>${ech(desc.length > 70 ? desc.slice(0, 68).replace(/\s+\S*$/, '') + '…' : desc)}</span>
        <em>${ech(host)}</em></div>
        <div class="lien">https://${ech(host)}${p.chemin === '/' ? '' : ech(p.chemin)}</div></div></div>
    </div>`;

  // Les verifications
  const v = [];
  const ok = (t, petit) => v.push(['ok', ic('check'), t, petit]);
  const ko = (t, petit) => v.push(['ko', ic('x'), t, petit]);
  const mc = s.motcle.trim();
  if (!mc) {
    ko('Aucun mot-clé choisi', 'Choisissez ce que les clients tapent pour trouver cette page : les vérifications en dépendent.');
  } else {
    const dansTitre = rfManquants(titre, mc);
    if (!dansTitre.length) ok('« ' + mc + ' » est dans le titre');
    else ko('Absent du titre : ' + dansTitre.map((m) => '« ' + m + ' »').join(', '),
      'Le mot-clé, au début du titre si possible : c’est ce que Google lit en premier.');
    const dansDesc = rfManquants(desc, mc);
    if (!dansDesc.length) ok('« ' + mc + ' » est dans la description');
    else ko('Absent de la description : ' + dansDesc.map((m) => '« ' + m + ' »').join(', '),
      'Google met en gras les mots cherchés : une description qui les contient attire l’œil.');
    const dansH1 = rfManquants(p.h1, mc);
    if (!dansH1.length) ok('« ' + mc + ' » est dans le grand titre de la page');
    else ko('Absent du grand titre de la page : ' + dansH1.map((m) => '« ' + m + ' »').join(', '),
      'Grand titre actuel : « ' + p.h1 + ' ». Il fait partie de la mise en page : c’est le développeur qui le modifie, sur demande.');
    const autre = RF.manifeste.pages.find((x) => x.id !== p.id && rfPlat(rfReglage(x.id).motcle || '') === rfPlat(mc));
    if (autre) ko('Le même mot-clé que la page « ' + autre.nom + ' »',
      'Deux pages sur le même mot-clé se font concurrence : Google n’en montrera qu’une.');
  }
  const double = RF.manifeste.pages.find((x) => x.id !== p.id && rfVaut(x, rfReglage(x.id)).titre === titre);
  if (double) ko('Même titre que la page « ' + double.nom + ' »', 'Chaque page a besoin de son propre titre.');
  if (titre.length > RF_TITRE_MAX) ko('Titre trop long : ' + titre.length + ' caractères',
    'Google coupe au-delà de ' + RF_TITRE_MAX + ' caractères environ, et la fin disparaît.');
  if (desc.length < RF_DESC_MIN) ko('Description courte : ' + desc.length + ' caractères',
    'Entre ' + RF_DESC_MIN + ' et ' + (RF_DESC_MAX - 5) + ' : assez pour donner envie, sans être coupée.');
  else if (desc.length > RF_DESC_MAX) ko('Description longue : ' + desc.length + ' caractères',
    'Google la coupera vers ' + (RF_DESC_MAX - 5) + ' caractères.');
  if (!double && titre.length <= RF_TITRE_MAX && desc.length >= RF_DESC_MIN && desc.length <= RF_DESC_MAX) {
    ok('Titre unique sur le site · longueurs correctes');
  }
  $('#rf-verifs').innerHTML = v.map(([cl, s1, t, petit]) =>
    `<li class="${cl}">${s1} <span>${ech(t)}${petit ? '<small>' + ech(petit) + '</small>' : ''}</span></li>`).join('');
}

/* ── Les gestes ───────────────────────────────────────────────────────── */
async function rfRafraichir() {
  const t = await appel('tout');
  if (t.ok && t.donnees) { ETAT.seo = t.donnees.seo || {}; ETAT.carnet = t.donnees.articles || ETAT.carnet; }
}

document.addEventListener('click', async (e) => {
  if (VUE !== 'seo') return;
  const o = e.target.closest('[data-rf-onglet]');
  if (o) { RF.onglet = o.dataset.rfOnglet; RF.erreur = ''; return rendre(); }
  const pg = e.target.closest('[data-rf-page]');
  if (pg) { rfOuvrir(pg.dataset.rfPage); rendre(); window.scrollTo(0, 0); return; }
  if (e.target.closest('[data-rf-retour]')) { e.preventDefault(); RF.edite = null; return rendre(); }
  const art = e.target.closest('[data-rf-article]');
  if (art) {
    const a = (ETAT.carnet || []).find((x) => x.id === art.dataset.rfArticle);
    if (!a) return;
    VUE = 'carnet'; EDITE = JSON.parse(JSON.stringify(a)); EDITE.infos = EDITE.infos || [];
    [...$('#menu').querySelectorAll('button[data-v]')].forEach((x) => x.classList.toggle('on', x.dataset.v === VUE));
    rendre(); window.scrollTo(0, 0); return;
  }
  if (e.target.closest('[data-rf-photos]')) { rfLire(); RF.photos = !RF.photos; rendre(); return; }
  const im = e.target.closest('[data-rf-img]');
  if (im) { rfLire(); RF.saisie.image = im.dataset.rfImg; RF.photos = false; rendre(); return; }
  if (e.target.closest('[data-rf-defaut]')) {
    if (!confirm('Revenir au titre, à la description et à l’image que le site écrit lui-même ?\n\n'
      + 'Le mot-clé est gardé. Il faudra ensuite publier.')) return;
    const r = await appel('seo-page', { entree: { id: RF.edite, motcle: RF.saisie.motcle }, nom: rfNom(RF.edite) });
    if (!r.ok) return notifier(r.message || 'Rien n’a été enregistré', true);
    await rfRafraichir();
    RF.edite = null;
    notifier('Texte du site rétabli — à publier');
    return rendre();
  }
  if (e.target.closest('#rf-publier')) return rfPublier();
  const ret = e.target.closest('[data-rf-retirer]');
  if (ret) {
    const x = (rfSeo().redirections || []).find((y) => y.id === ret.dataset.rfRetirer);
    if (!x || !confirm('Retirer la redirection ' + x.de + ' → ' + x.vers + ' ?\n\nAprès publication, '
      + 'l’ancienne adresse mènera à la page « introuvable ».')) return;
    const r = await appel('seo-redirection-retirer', { id: x.id });
    if (!r.ok) return notifier(r.message || 'Rien n’a été retiré', true);
    await rfRafraichir();
    notifier('Redirection retirée — à publier');
    return rendre();
  }
  const rt = e.target.closest('[data-rf-retablir]');
  if (rt) {
    const p = (rfSeo().publications || []).find((x) => x.id === rt.dataset.rfRetablir);
    if (!p || !confirm('Remettre le site dans l’état du ' + rfQuand(p.t) + ' ?\n\n« ' + p.resume + ' »\n\n'
      + 'Les réglages actuels sont remplacés, et publiés aussitôt. Ils restent dans l’historique : '
      + 'on peut y revenir de la même façon.')) return;
    const r = await appel('retablir-seo', { id: p.id });
    if (!r.ok) return notifier(r.message || 'Rien n’a été publié', true);
    return rfApresPublication(r);
  }
});

/* Le debut du titre du site, quand il s'ecrit « … — Hôtel Evannath ».
   Sinon (« Suite Arabe — Hôtel Evannath, Assinie | 280 000 FCFA la nuit »)
   il n'a pas de debut a reprendre : le champ part vide, et vide veut dire
   « le titre du site est garde ». Le pre-remplir avec un morceau aurait
   change le titre de la page des qu'on enregistrait un simple mot-cle. */
function rfDebutSite(p) {
  return p.titre.endsWith(RF_SUFFIXE) ? p.titre.slice(0, -RF_SUFFIXE.length) : '';
}

const rfNom = (id) => ((RF.manifeste && RF.manifeste.pages.find((p) => p.id === id)) || { nom: id }).nom;

async function rfPublier() {
  const a = rfAttente();
  if (!a.total) return;
  const resume = a.pages.map(rfNom).join(', ')
    + (a.ajoutees ? (a.pages.length ? ' · ' : '') + rfPluriel(a.ajoutees, 'redirection ajoutée', 'redirections ajoutées') : '')
    + (a.retirees ? (a.pages.length || a.ajoutees ? ' · ' : '') + rfPluriel(a.retirees, 'redirection retirée', 'redirections retirées') : '');
  const b = $('#rf-publier');
  if (b) { b.disabled = true; b.textContent = 'Publication…'; }
  const r = await appel('publier-seo', { resume });
  if (!r.ok) { RF.erreur = r.message || 'La publication n’a pas abouti.'; return rendre(); }
  return rfApresPublication(r);
}

async function rfApresPublication(r) {
  RF.erreur = '';
  await rfRafraichir();
  RF.onglet = RF.onglet === 'historique' ? 'historique' : RF.onglet;
  if (r.deploiement === 'demande') {
    RF.attendue = { id: r.publication.id, depuis: Date.now(), message: r.message };
    rfGuetter();
  } else {
    /* Sans crochet, le bandeau « pas encore sur le site » le dit deja. */
    RF.attendue = null;
    RF.erreur = r.deploiement === 'echec' ? (r.message || '') : '';
  }
  notifier(r.deploiement === 'demande' ? 'Publication envoyée' : 'Publication enregistrée', r.deploiement === 'echec');
  rendre();
}

document.addEventListener('input', (e) => {
  if (VUE !== 'seo' || !e.target.closest('#rf-form')) return;
  rfLire();
  rfApres();
});
document.addEventListener('change', (e) => {
  if (VUE !== 'seo' || e.target.id !== 'rf-masquer') return;
  rfLire();
  rfApres();
});

document.addEventListener('submit', async (e) => {
  if (VUE !== 'seo') return;
  if (e.target.id === 'rf-form') {
    e.preventDefault();
    rfLire();
    const s = RF.saisie;
    const p = RF.manifeste.pages.find((x) => x.id === RF.edite);
    /* Ce qui n'a pas change par rapport au site n'est pas enregistre : la
       page garde alors ce que le site ecrit, et suivra ses mises a jour. */
    const entree = { id: p.id, motcle: s.motcle.trim(),
      titre: s.titre.trim() === rfDebutSite(p) ? '' : s.titre.trim(),
      description: s.description.trim() === p.description ? '' : s.description.trim(),
      image: s.image === p.image ? '' : s.image,
      masquer: !!s.masquer && !p.hors_index };
    const m = $('#rf-msg');
    m.className = 'msg'; m.textContent = 'Enregistrement…';
    const r = await appel('seo-page', { entree, nom: p.nom });
    if (!r.ok) { m.className = 'msg mal'; m.textContent = r.message || 'Rien n’a été enregistré.'; return; }
    await rfRafraichir();
    RF.edite = null;
    notifier(rfAttente().pages.includes(p.id) ? p.nom + ' enregistrée — à publier' : p.nom + ' enregistrée');
    rendre();
    return;
  }
  if (e.target.id === 'rf-form-red') {
    e.preventDefault();
    const de = $('#rf-de').value.trim(), vers = $('#rf-vers').value.trim();
    const m = $('#rf-msg-red');
    /* Une page qui existe ne passe jamais par la redirection : la refuser
       ici evite d'en ajouter une qui ne fera rien. */
    const chemin = de.replace(/^https?:\/\/[^/]+/i, '').replace(/\/+$/, '').toLowerCase() || '/';
    const existe = RF.manifeste.pages.find((p) => p.chemin === chemin || p.chemin + '.html' === chemin);
    if (existe) {
      m.className = 'msg mal';
      m.textContent = chemin + ' est une page du site (« ' + existe.nom + ' ») : elle ne peut pas être redirigée.';
      return;
    }
    const r = await appel('seo-redirection', { entree: { de, vers } });
    if (!r.ok) { m.className = 'msg mal'; m.textContent = r.message || 'Rien n’a été ajouté.'; return; }
    await rfRafraichir();
    notifier('Redirection ajoutée — à publier');
    rendre();
  }
});
