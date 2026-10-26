// L'etape de construction de Vercel : pose dans les pages le referencement
// publie depuis l'administration (onglet Referencement). Voir _seo.js.
//
//   vercel.json  "buildCommand": "node api/_seo_appliquer.js"
//
// Elle tourne a CHAQUE deploiement : celui que demande « Publier » (crochet
// SEO_DEPLOY_HOOK) et ceux qui suivent un changement de code. Les pages du
// depot gardent ce que les generateurs Python ont ecrit ; la publication de
// l'agence se pose par-dessus, dans la copie qui part en ligne. Le depot ne
// change jamais.
//
// CE QU'ELLE TOUCHE, et rien d'autre : <title>, la description, og:title,
// og:description, og:image, la balise robots, et l'entree d'une page masquee
// dans sitemap.xml. Pas un script : les empreintes CSP de vercel.json restent
// justes. Elle ecrit aussi seo-publication.json — l'onglet le lit pour dire
// quand la publication est en ligne.
//
// SI LA BASE NE REPOND PAS : en production, le deploiement echoue, et le site
// en ligne reste celui d'avant, publication comprise. Deployer sans elle
// remettrait les titres d'origine sans que personne ne le voie. Ailleurs
// (apercus), on continue avec les pages telles quelles.
//
// Essai local, sur une copie :
//   node site/api/_seo_appliquer.js --dossier /tmp/copie --instantane pub.json

const fs = require('fs');
const path = require('path');
const seo = require('./_seo.js');

function argument(nom) {
  const i = process.argv.indexOf('--' + nom);
  return i > 0 ? process.argv[i + 1] : '';
}

/** Pose la publication `pub` dans les pages de `dossier`. Rend le compte rendu. */
function appliquer(dossier, pub) {
  const lignes = [];
  let plan = null;
  const fichierPlan = path.join(dossier, 'sitemap.xml');
  if (fs.existsSync(fichierPlan)) plan = fs.readFileSync(fichierPlan, 'utf8');
  const imageExiste = (nom) => fs.existsSync(path.join(dossier, 'img', 'opt', nom + '.jpg'));

  for (const [id, r] of Object.entries(pub.pages || {})) {
    /* L'identifiant est deja controle a l'enregistrement ; on le revérifie :
       c'est un nom de fichier. */
    if (!/^[a-z0-9-]{1,60}$/.test(id)) continue;
    const f = path.join(dossier, id + '.html');
    if (!fs.existsSync(f)) { lignes.push('  ' + id + ' : page absente, ignorée'); continue; }
    const avant = fs.readFileSync(f, 'utf8');
    const { html, poses } = seo.appliquerPage(avant, r, { imageExiste });
    if (r.image && !imageExiste(r.image)) lignes.push('  ' + id + ' : photo « ' + r.image + ' » absente, image gardée');
    if (html !== avant) fs.writeFileSync(f, html);
    if (poses.length) lignes.push('  ' + id + ' : ' + poses.join(', '));
    if (r.masquer && plan !== null) {
      const canon = (html.match(/<link rel="canonical" href="([^"]+)"/) || [])[1];
      if (canon) plan = seo.retirerDuPlan(plan, canon);
    }
  }
  if (plan !== null) fs.writeFileSync(fichierPlan, plan);
  fs.writeFileSync(path.join(dossier, 'seo-publication.json'),
    JSON.stringify({ id: pub.id, t: pub.t, par: pub.par }));
  return lignes;
}

/** La derniere publication, lue dans le magasin de CET environnement. */
async function publicationDuMagasin() {
  const magasin = require('./_magasin.js');
  /* Le jeton Blob, reconnu a sa forme comme dans admin.js : un magasin
     connecte avec un prefixe s'appelle MONPREFIXE_READ_WRITE_TOKEN. */
  let jeton = process.env.BLOB_READ_WRITE_TOKEN || '';
  if (!jeton) {
    for (const nom of Object.keys(process.env)) {
      if (/READ_WRITE_TOKEN$/.test(nom) && /^vercel_blob_rw_/.test(process.env[nom] || '')) {
        jeton = process.env[nom]; break;
      }
    }
  }
  const doc = magasin.document({ cle: 'donnees', prefixeBlob: 'evannath/donnees', garde: 10,
    vide: () => ({}), jeton, nom: 'du fichier de données' });
  if (doc.mode === 'memoire') return { pub: null, note: 'aucun magasin configuré' };
  const l = await doc.lire();
  if (!l.ok) return { panne: l.panne || 'lecture impossible' };
  return { pub: seo.derniere(l.d && l.d.seo) };
}

async function principal() {
  const dossier = argument('dossier') || path.join(__dirname, '..');
  /* Sur un poste, jamais dans le depot lui-meme : les pages generees sont
     commitees, et la publication n'a rien a y faire. */
  if (!process.env.VERCEL && !argument('dossier')) {
    console.error('Hors de Vercel, indiquez une copie : --dossier <chemin>.');
    return 1;
  }
  let pub;
  if (argument('instantane')) {
    pub = JSON.parse(fs.readFileSync(argument('instantane'), 'utf8'));
  } else {
    const r = await publicationDuMagasin();
    if (r.panne) {
      const env = process.env.EVN_ENV || process.env.VERCEL_ENV || '';
      console.error('Référencement : la base ne répond pas (' + r.panne + ').');
      if (env === 'production') {
        console.error('Déploiement arrêté : le site en ligne reste celui d’avant, avec sa publication.');
        return 1;
      }
      console.error('Aperçu : les pages partent telles que le site les écrit.');
      return 0;
    }
    if (!r.pub) { console.log('Référencement : rien de publié (' + (r.note || 'aucune publication') + ').'); return 0; }
    pub = r.pub;
  }
  const lignes = appliquer(dossier, pub);
  console.log('Référencement : publication du ' + pub.t + ' par ' + pub.par + ' posée.');
  for (const l of lignes) console.log(l);
  return 0;
}

if (require.main === module) {
  principal().then((code) => process.exit(code), (e) => {
    console.error('Référencement :', e && e.message);
    process.exit((process.env.EVN_ENV || process.env.VERCEL_ENV) === 'production' ? 1 : 0);
  });
}

module.exports = { appliquer };
