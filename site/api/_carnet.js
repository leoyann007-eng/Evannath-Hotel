// Le Carnet d'Assinie : les articles publies depuis l'administration.
//
// Ce module ne lit ni n'ecrit rien : admin.js lui passe les donnees. Il
// fait trois choses, et on les teste ici sans serveur (tests/carnet.test.mjs) :
//   - nettoyer un article saisi dans l'administration ;
//   - dire ce qui est publie, a cet instant ;
//   - fabriquer la page d'un article, cote serveur.
//
// POURQUOI COTE SERVEUR. Le Carnet sert le referencement : « que faire a
// Assinie », « mariage Assinie ». Un article ecrit dans la page par un
// script arrive tard aux moteurs, et son titre de page reste celui du
// gabarit. Ici le titre, la description, l'adresse canonique et le texte
// sont deja dans le HTML que recoit le robot.
//
// LE GABARIT est carnet-article.html, la page statique (build-carnet.py).
// _carnet_gabarit.js en est la copie exacte, ecrite par le meme script :
// les scripts de la page sont donc ceux dont vercel.json connait les
// empreintes (_csp.py), et rien de ce qu'on insere ici n'est un script
// executable — seulement du JSON-LD et des donnees (type application/json).

const crypto = require('crypto');

let GABARIT = '';
try { GABARIT = require('./_carnet_gabarit.js'); } catch (e) { /* construit par build-carnet.py */ }

const LIMITES = { titre: 120, chapo: 320, alt: 160, texte: 30000 };

/* L'adresse d'un article : « Que faire à Assinie ? » -> que-faire-a-assinie.
   Elle ne change plus une fois l'article cree : un lien partage sur Facebook
   ou indexe par Google ne doit pas casser parce qu'on a retouche le titre. */
function slugDe(titre) {
  const s = String(titre || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 70)
    .replace(/-+$/, '');
  return s || 'article';
}
/* « article » est pris : /carnet-article est la page statique (le gabarit). */
const RESERVES = new Set(['article']);

const propre = (v, max) => String(v == null ? '' : v).replace(/\s+/g, ' ').trim().slice(0, max);
function texteLong(v) {
  return String(v == null ? '' : v)
    .replace(/\r\n?/g, '\n').replace(/[ \t]+/g, ' ').replace(/\n{3,}/g, '\n\n')
    .split('\n').map((l) => l.trimEnd()).join('\n').trim();
}

/**
 * Un article saisi -> { objet, manque, message }.
 * `imageSure` et `lienSur` viennent d'admin.js : les memes regles que pour
 * les affiches (pas d'image tierce, pas de lien « javascript: »).
 */
function nettoyerArticle(e, { imageSure }) {
  const o = {
    id: propre(e.id, 40) || crypto.randomUUID(),
    slug: '',
    titre: propre(e.titre, 400),
    chapo: propre(e.chapo, 2000),
    texte: texteLong(e.texte),
    image: imageSure(e.image),
    alt: propre(e.alt, LIMITES.alt),
    titre_en: propre(e.titre_en, 400),
    chapo_en: propre(e.chapo_en, 2000),
    texte_en: texteLong(e.texte_en),
    date: /^\d{4}-\d{2}-\d{2}$/.test(e.date || '') ? e.date : new Date().toISOString().slice(0, 10),
    publie: e.publie === true,
    cree: propre(e.cree, 40) || new Date().toISOString(),
  };
  const manque = [];
  let message = '';
  if (!o.titre) manque.push('titre');
  if (!o.chapo) manque.push('chapô');
  if (!o.texte) manque.push('texte');
  /* On REFUSE au-dela des bornes, sans tronquer : un article ampute de sa fin
     en silence est pire qu'un article refuse avec la raison. */
  const trop = (champ, n, nom) => {
    if (o[champ].length > n) { manque.push(nom); message = 'Le ' + nom + ' dépasse '
      + n.toLocaleString('fr-FR') + ' caractères. Raccourcissez-le : rien n’a été enregistré.'; }
  };
  trop('titre', LIMITES.titre, 'titre'); trop('chapo', LIMITES.chapo, 'chapô');
  trop('texte', LIMITES.texte, 'texte');
  trop('titre_en', LIMITES.titre, 'titre anglais'); trop('chapo_en', LIMITES.chapo, 'chapô anglais');
  trop('texte_en', LIMITES.texte, 'texte anglais');
  if (e.image && String(e.image).trim() && !o.image) {
    manque.push('image');
    message = 'Cette image n’est pas acceptée : choisissez une photo du site ou déposez-la depuis l’administration.';
  }
  return { objet: o, manque, message };
}

/** Donne a `o` une adresse libre parmi `articles` (les autres que lui). */
function attribuerSlug(o, articles, avant) {
  if (avant && avant.slug) { o.slug = avant.slug; return; }
  const pris = new Set(articles.filter((x) => x.id !== o.id).map((x) => x.slug));
  const base = slugDe(o.titre);
  let s = RESERVES.has(base) ? base + '-1' : base, n = 2;
  while (pris.has(s)) s = base + '-' + n++;
  o.slug = s;
}

/** Ce qui est en ligne a cet instant : publie, et date de publication atteinte.
    Le tri se fait cote serveur : un article programme ne sort pas d'ici. */
function enLigne(articles, maintenant) {
  const auj = new Date(maintenant).toISOString().slice(0, 10);
  return (articles || []).filter((a) => a && a.publie === true && a.slug && a.date <= auj)
    .sort((a, b) => (b.date + b.cree).localeCompare(a.date + a.cree));
}

/** La liste publique : sans les textes, qui peuvent etre longs. */
function liste(articles, maintenant) {
  return enLigne(articles, maintenant).map((a) => ({
    slug: a.slug, titre: a.titre, chapo: a.chapo, image: a.image, alt: a.alt, date: a.date,
    titre_en: a.titre_en, chapo_en: a.chapo_en,
  }));
}

// ── Le texte ────────────────────────────────────────────────────────────
/* Une mise en forme volontairement courte, expliquee sous le champ dans
   l'administration :
     une ligne vide         nouveau paragraphe
     ## Titre               intertitre        ### Titre   sous-intertitre
     - element              liste a puces
     **gras**  *italique*   [texte du lien](adresse)
   Tout le reste est du texte : le HTML saisi est echappe, jamais interprete.
   Un compte Communication ne peut donc rien injecter dans la page. */
const echappe = (v) => String(v == null ? '' : v)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function enLigneMd(t, lienSur) {
  let s = echappe(t);
  s = s.replace(/\[([^\]]{1,200})\]\(([^)\s]{1,300})\)/g, (m, txt, href) => {
    const h = lienSur(href.replace(/&amp;/g, '&'));
    if (!h) return txt;
    const ext = /^https?:\/\//i.test(h);
    return '<a href="' + echappe(h) + '"' + (ext ? ' target="_blank" rel="noopener"' : '') + '>' + txt + '</a>';
  });
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/(^|[^*])\*([^*\s][^*]*)\*/g, '$1<em>$2</em>');
  return s;
}

function rendre(texte, lienSur) {
  const blocs = String(texte || '').split(/\n\s*\n/);
  const out = [];
  for (const b of blocs) {
    const lignes = b.split('\n').filter((l) => l.trim());
    if (!lignes.length) continue;
    let liste = [], para = [];
    const vider = () => {
      if (para.length) { out.push('<p>' + para.map((l) => enLigneMd(l.trim(), lienSur)).join('<br>') + '</p>'); para = []; }
      if (liste.length) { out.push('<ul>' + liste.map((l) => '<li>' + enLigneMd(l, lienSur) + '</li>').join('') + '</ul>'); liste = []; }
    };
    for (const l of lignes) {
      const t = l.trim();
      let m;
      if ((m = /^(#{2,3})\s+(.+)$/.exec(t))) {
        vider();
        const n = m[1].length;
        out.push('<h' + n + '>' + enLigneMd(m[2], lienSur) + '</h' + n + '>');
      } else if ((m = /^[-•]\s+(.+)$/.exec(t))) {
        if (para.length) vider();
        liste.push(m[1]);
      } else {
        if (liste.length) vider();
        para.push(t);
      }
    }
    vider();
  }
  return out.join('\n');
}

/** L'article complet, tel que la page l'affiche (FR et EN). */
function complet(a, lienSur) {
  return {
    slug: a.slug, date: a.date, image: a.image, alt: a.alt,
    titre: a.titre, chapo: a.chapo, html: rendre(a.texte, lienSur),
    titre_en: a.titre_en, chapo_en: a.chapo_en, html_en: a.texte_en ? rendre(a.texte_en, lienSur) : '',
  };
}

// ── La page ─────────────────────────────────────────────────────────────
function urlImage(image, site) {
  if (!image) return site + '/img/opt/gal-lag-ponton.jpg';
  return /^https:/.test(image) ? image : site + '/img/opt/' + image + '.jpg';
}
function dateLisible(iso, langue) {
  const j = new Date(iso + 'T12:00:00Z');
  return isNaN(j) ? iso : j.toLocaleDateString(langue === 'en' ? 'en-GB' : 'fr-FR',
    { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
}
/* Du JSON place dans <script> : « </script> » ou « <!-- » dans un titre
   fermerait la balise. \u003c ne change rien au JSON lu. */
const jsonSur = (o) => JSON.stringify(o).replace(/</g, '\\u003c').replace(/\u2028|\u2029/g, '');

/** Le corps de l'article, insere entre <!--ART--> et <!--/ART-->. */
function corpsArticle(c) {
  const img = c.image
    ? (/^https:/.test(c.image)
      ? '<img src="' + echappe(c.image) + '" alt="' + echappe(c.alt) + '" width="1200" height="800">'
      : '<picture><source srcset="img/opt/' + echappe(c.image) + '.webp" type="image/webp"><img src="img/opt/'
        + echappe(c.image) + '.jpg" alt="' + echappe(c.alt) + '" width="1200" height="800"></picture>')
    : '';
  return '<article class="art" id="art">\n'
    + '  <p class="art-date" id="art-date">' + echappe(dateLisible(c.date, 'fr')) + '</p>\n'
    + '  <h1 id="art-titre">' + echappe(c.titre) + '</h1>\n'
    + '  <p class="art-chapo" id="art-chapo">' + echappe(c.chapo) + '</p>\n'
    + (img ? '  <figure class="art-img">' + img + '</figure>\n' : '')
    + '  <div class="art-texte" id="art-texte">\n' + c.html + '\n  </div>\n</article>';
}

/**
 * La page HTML d'un article, ou null s'il n'y a pas de gabarit.
 * `c` : l'article complet (complet()), ou null pour « introuvable ».
 */
function page(c, site, gabarit = GABARIT) {
  if (!gabarit) return null;
  let h = gabarit;
  if (!c) {
    return h.replace(/<!--ART-->[\s\S]*?<!--\/ART-->/, '<!--ART--><article class="art" id="art"><h1>Article introuvable</h1>'
      + '<p class="art-chapo">Cet article n’existe pas, ou n’est plus en ligne.</p>'
      + '<p><a href="carnet" class="btn">Tous les récits du Carnet</a></p></article><!--/ART-->')
      .replace('<!--ART-LD-->', '');
  }
  const url = site + '/carnet-' + c.slug;
  const titre = echappe(c.titre) + ' — Le Carnet d’Assinie · Hôtel Evannath';
  const desc = echappe(c.chapo);
  /* Toujours par une fonction : un « $& » ecrit dans un titre serait lu
     comme un motif de remplacement par String.replace. */
  const remplacer = (re, v) => { h = h.replace(re, (m, a, z) => a + v + z); };
  remplacer(/(<title>)[^<]*(<\/title>)/, titre);
  remplacer(/(<meta name="description" content=")[^"]*(")/, desc);
  remplacer(/(<meta property="og:title" content=")[^"]*(")/, titre);
  remplacer(/(<meta property="og:description" content=")[^"]*(")/, desc);
  remplacer(/(<meta property="og:image" content=")[^"]*(")/, echappe(urlImage(c.image, site)));
  remplacer(/(<meta property="og:type" content=")[^"]*(")/, 'article');
  remplacer(/(<link rel="canonical" href=")[^"]*(")/, echappe(url));
  remplacer(/(<meta property="og:url" content=")[^"]*(")/, echappe(url));
  const ld = {
    '@context': 'https://schema.org', '@type': 'BlogPosting',
    headline: c.titre, description: c.chapo, datePublished: c.date, inLanguage: 'fr',
    image: urlImage(c.image, site), mainEntityOfPage: url,
    author: { '@type': 'Organization', name: 'Hôtel Evannath' },
    publisher: { '@type': 'Organization', name: 'Hôtel Evannath' },
  };
  h = h.replace('<!--ART-LD-->', () => '<script type="application/ld+json">' + jsonSur(ld) + '</script>\n'
    + '<script type="application/json" id="art-data">' + jsonSur(c) + '</script>');
  h = h.replace(/<!--ART-->[\s\S]*?<!--\/ART-->/, () => '<!--ART-->' + corpsArticle(c) + '<!--/ART-->');
  return h;
}

/** Le plan du site des articles, pour la Search Console. */
function plan(articles, site, maintenant) {
  const urls = enLigne(articles, maintenant).map((a) =>
    '  <url><loc>' + echappe(site + '/carnet-' + a.slug) + '</loc><lastmod>' + a.date + '</lastmod></url>');
  return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + '  <url><loc>' + echappe(site + '/carnet') + '</loc></url>\n' + urls.join('\n') + (urls.length ? '\n' : '') + '</urlset>\n';
}

module.exports = { nettoyerArticle, attribuerSlug, enLigne, liste, complet, rendre, page, plan, slugDe, LIMITES };
