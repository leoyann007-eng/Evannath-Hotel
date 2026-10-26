// Le referencement : ce que Google affiche pour chaque page du site.
//
// L'onglet Referencement de l'administration est tenu par l'agence de
// communication. Elle y regle, page par page, le titre, la description et
// l'image de partage, et declare les anciennes adresses a rediriger. Ce
// module ne lit ni n'ecrit rien : admin.js lui passe les donnees, et
// _seo_appliquer.js s'en sert au deploiement. Teste sans serveur :
// tests/seo.test.mjs.
//
// DEUX TEMPS, VOULUS. Enregistrer ne change pas le site ; « Publier »
// le change. Une page dont on retouche le titre trois fois dans l'apres-midi
// ne doit pas partir trois fois chez Google, et l'agence doit pouvoir relire
// l'ensemble avant de l'envoyer. Chaque publication est un INSTANTANE complet,
// conserve : revenir a une version precedente, c'est republier son instantane.
//
// POURQUOI AU DEPLOIEMENT. Les pages sont statiques : c'est ce qui les rend
// rapides et ce qui fait que le robot de Google lit le bon titre du premier
// coup. Publier declenche donc un deploiement (crochet Vercel), et
// _seo_appliquer.js pose l'instantane dans les pages avant leur mise en
// ligne. Un deploiement ordinaire, apres un changement de code, le repose
// aussi : ce que l'agence a publie survit aux mises a jour du site.
//
// LES REDIRECTIONS, elles, se decident a la demande : une adresse qui ne
// correspond a aucun fichier passe par admin.js (a=introuvable), qui lit la
// derniere publication. Une ancienne adresse publiee redirige donc des la
// publication, sans attendre le deploiement.

const crypto = require('crypto');

/* La fin de chaque titre. Elle est posee ici et non saisie : l'agence ecrit
   ce qui change d'une page a l'autre, la marque reste la meme partout. */
const SUFFIXE = ' — Hôtel Evannath';

/* Les bornes DURES. Les bornes conseillees (60 caracteres de titre, 155 de
   description) sont des avertissements dans l'onglet : Google coupe au-dela,
   il ne refuse rien. Ici on refuse seulement l'absurde. */
const LIMITES = { motcle: 60, titre: 80, description: 300, de: 200, vers: 300 };
const MAX_REDIRECTIONS = 300;
const MAX_PUBLICATIONS = 12;

const propre = (v, max) => String(v == null ? '' : v).replace(/\s+/g, ' ').trim().slice(0, max);

/* Ce qui, dans le reglage d'une page, change le site. Le mot-cle n'en est
   pas : il guide l'agence, Google ne le voit jamais. Le modifier n'a donc
   rien a publier. */
const CHAMPS_SITE = ['titre', 'description', 'image', 'masquer'];
const empreinte = (p) => JSON.stringify(CHAMPS_SITE.map((k) => (p && p[k]) || ''));

/**
 * Le reglage d'une page, saisi -> { objet, manque, message }.
 * Un reglage vide (rien de saisi, page visible) veut dire « comme le site
 * l'a ecrit » : admin.js le retire plutot que de le garder.
 */
function nettoyerPage(e) {
  e = e || {};
  const id = String(e.id || '');
  if (!/^[a-z0-9-]{1,60}$/.test(id)) return { objet: null, manque: ['page'], message: 'Page inconnue.' };
  let titre = propre(e.titre, 400);
  /* L'agence qui recopie un titre complet le recopie avec sa fin : on
     l'enleve, sans quoi elle apparaitrait deux fois. */
  if (titre.endsWith(SUFFIXE.trim())) titre = titre.slice(0, -SUFFIXE.trim().length).replace(/[\s—–-]+$/, '');
  const description = propre(e.description, 2000);
  if (titre.length > LIMITES.titre) {
    return { objet: null, manque: ['titre'],
      message: 'Titre trop long : ' + titre.length + ' caractères pour ' + LIMITES.titre + ' au maximum.' };
  }
  if (description.length > LIMITES.description) {
    return { objet: null, manque: ['description'],
      message: 'Description trop longue : ' + description.length + ' caractères pour '
        + LIMITES.description + ' au maximum.' };
  }
  const image = String(e.image || '');
  /* Une photo du site, par son nom (img/opt/<nom>.jpg) : jamais une adresse.
     L'image de partage est servie a WhatsApp et Facebook au nom de l'hotel. */
  if (image && !/^[a-z0-9-]{1,80}$/.test(image)) {
    return { objet: null, manque: ['image'], message: 'Choisissez une photo du site.' };
  }
  return { objet: { id, motcle: propre(e.motcle, LIMITES.motcle), titre, description, image,
    masquer: e.masquer === true }, manque: [] };
}
const reglageVide = (o) => !o.motcle && !o.titre && !o.description && !o.image && !o.masquer;

/* Une adresse, ramenee a la forme sous laquelle on la compare :
   « /Nos-Chambres.html/ » et « /nos-chambres.html » sont la meme. */
function normaliser(chemin) {
  let p = String(chemin || '');
  try { p = decodeURIComponent(p); } catch (e) { /* telle quelle */ }
  p = p.split(/[?#]/)[0].replace(/\/{2,}/g, '/').toLowerCase();
  if (!p.startsWith('/')) p = '/' + p;
  return p.length > 1 ? p.replace(/\/+$/, '') : p;
}

/**
 * Une redirection saisie -> { objet, manque, message }.
 * `de` : une adresse du site (on accepte l'adresse complete collee depuis le
 * navigateur). `vers` : une page du site, ou une adresse https.
 */
function nettoyerRedirection(e) {
  e = e || {};
  let de = String(e.de || '').trim();
  const vers = String(e.vers || '').trim();
  if (/^https?:\/\//i.test(de)) {
    try { const u = new URL(de); de = u.pathname + u.search; } catch (x) { de = ''; }
  }
  if (!de || !de.startsWith('/') || /\s/.test(de) || de.length > LIMITES.de) {
    return { objet: null, manque: ['ancienne adresse'],
      message: 'L’ancienne adresse commence par « / », par exemple /nos-chambres.html.' };
  }
  /* « /?page_id=12 » : l'adresse « / » existe (l'accueil). Elle ne passera
     jamais par la redirection, qui ne voit que les adresses inconnues. */
  if (de.includes('?')) {
    return { objet: null, manque: ['ancienne adresse'],
      message: 'Une adresse avec « ? » ne peut pas être redirigée : la page avant le « ? » existe.' };
  }
  if (normaliser(de) === '/') {
    return { objet: null, manque: ['ancienne adresse'], message: 'L’accueil ne se redirige pas.' };
  }
  const versOk = /^\/[^\s]*$/.test(vers) || /^https:\/\/[^\s/]+\.[^\s]+$/i.test(vers);
  if (!versOk || vers.length > LIMITES.vers || vers.startsWith('//')) {
    return { objet: null, manque: ['nouvelle adresse'],
      message: 'La nouvelle adresse est une page du site (/chambres) ou une adresse https://.' };
  }
  if (vers.startsWith('/') && normaliser(vers) === normaliser(de)) {
    return { objet: null, manque: ['nouvelle adresse'], message: 'Une adresse ne se redirige pas vers elle-même.' };
  }
  return { objet: { id: crypto.randomUUID(), de: normaliser(de), vers }, manque: [] };
}

/** La derniere publication, ou null. */
function derniere(seo) {
  const l = (seo && seo.publications) || [];
  return l.length ? l[l.length - 1] : null;
}

/* Les redirections, sous une forme comparable. */
const listeRedir = (l) => (l || []).map((r) => r.de + ' → ' + r.vers).sort();

/**
 * Ce qui attend d'etre publie : les pages dont le reglage differe de la
 * derniere publication, et les redirections ajoutees ou retirees.
 */
function enAttente(seo) {
  seo = seo || {};
  const pub = derniere(seo) || { pages: {}, redirections: [] };
  const actuel = seo.pages || {};
  const ids = new Set(Object.keys(actuel).concat(Object.keys(pub.pages || {})));
  const pages = [...ids].filter((id) => empreinte(actuel[id]) !== empreinte((pub.pages || {})[id])).sort();
  const avant = new Set(listeRedir(pub.redirections));
  const apres = new Set(listeRedir(seo.redirections));
  const ajoutees = [...apres].filter((x) => !avant.has(x)).length;
  const retirees = [...avant].filter((x) => !apres.has(x)).length;
  return { pages, ajoutees, retirees, total: pages.length + ajoutees + retirees };
}

/** L'instantane a publier : une copie, que les modifications suivantes ne touchent pas. */
function instantane(seo) {
  return { pages: structuredClone((seo && seo.pages) || {}),
    redirections: structuredClone((seo && seo.redirections) || []) };
}

/** Ajoute une publication en ne gardant que les plus recentes. */
function ajouterPublication(seo, pub) {
  seo.publications = (seo.publications || []).concat(pub).slice(-MAX_PUBLICATIONS);
  return pub;
}

/** La redirection d'une adresse inconnue, d'apres la liste publiee. */
function trouverRedirection(liste, chemin) {
  const p = normaliser(chemin);
  return (liste || []).find((r) => r && r.de === p) || null;
}

// ── Poser un reglage dans une page ───────────────────────────────────────
const attr = (v) => String(v).replace(/&/g, '&amp;').replace(/"/g, '&quot;')
  .replace(/</g, '&lt;').replace(/>/g, '&gt;');
const texte = (v) => String(v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/* Remplace le contenu d'une balise meta, si elle est la. Une fonction de
   remplacement, jamais une chaine : « $& » dans un titre s'ecrirait sinon
   comme la balise entiere. */
function poserMeta(html, motif, valeur) {
  return html.replace(motif, (m, avant, apres) => avant + attr(valeur) + apres);
}

/**
 * Pose le reglage `r` dans le HTML d'une page.
 *   r = { titre, description, image, masquer }   (vides : on n'y touche pas)
 *   imageExiste(nom) : la photo est-elle dans le site ? Une image absente
 *                      laisserait WhatsApp sans vignette : on garde l'ancienne.
 * Rend { html, poses: [ce qui a change] }.
 */
function appliquerPage(html, r, { imageExiste } = {}) {
  const poses = [];
  if (r.titre) {
    const t = r.titre + SUFFIXE;
    html = html.replace(/<title>[^<]*<\/title>/, () => '<title>' + texte(t) + '</title>');
    html = poserMeta(html, /(<meta property="og:title" content=")[^"]*(">)/, t);
    poses.push('titre');
  }
  if (r.description) {
    html = poserMeta(html, /(<meta name="description" content=")[^"]*(">)/, r.description);
    html = poserMeta(html, /(<meta property="og:description" content=")[^"]*(">)/, r.description);
    poses.push('description');
  }
  if (r.image && (!imageExiste || imageExiste(r.image))) {
    html = html.replace(/(<meta property="og:image" content=")([^"]*\/img\/opt\/)[\w-]+(\.jpg">)/,
      (m, a, b, c) => a + b + r.image + c);
    /* Les dimensions et la description de l'ancienne image ne valent plus
       pour la nouvelle : mieux vaut rien qu'une information fausse. */
    html = html.replace(/<meta property="og:image:(width|height|alt)" content="[^"]*">\n?/g, '');
    poses.push('image');
  }
  if (r.masquer) {
    const robots = /<meta name="robots" content="([^"]*)">/;
    const m = html.match(robots);
    if (!m) {
      html = html.replace(/(<meta name="viewport"[^>]*>\n?)/, (x) => x + '<meta name="robots" content="noindex, follow">\n');
    } else if (!/noindex/.test(m[1])) {
      html = html.replace(robots, '<meta name="robots" content="noindex, follow">');
    }
    poses.push('masquée');
  }
  return { html, poses };
}

/** Retire une adresse du plan du site (sitemap.xml). */
function retirerDuPlan(xml, url) {
  return xml.replace(/ *<url>\s*<loc>([^<]*)<\/loc>[\s\S]*?<\/url>\n?/g,
    (bloc, loc) => (loc === url ? '' : bloc));
}

module.exports = { SUFFIXE, LIMITES, MAX_REDIRECTIONS, nettoyerPage, reglageVide, nettoyerRedirection,
  normaliser, derniere, enAttente, instantane, ajouterPublication, trouverRedirection,
  appliquerPage, retirerDuPlan };
