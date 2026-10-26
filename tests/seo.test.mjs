// Tests du Referencement, hors Vercel : on simule req et res.
// Lance depuis la racine du depot :  node tests/seo.test.mjs
//
// CE QUI SE JOUE ICI. L'agence de communication regle ce que Google affiche,
// et le publie elle-meme. Cinq choses ne doivent jamais arriver :
//
//   1. UN ENREGISTREMENT QUI CHANGE LE SITE. Seule « Publier » le change ;
//      enregistrer prepare.
//   2. UN PROFIL SANS LE DROIT QUI PUBLIE. Reception et Lecture seule voient
//      peut-etre l'onglet ; ils n'ecrivent rien.
//   3. UNE PAGE ABIMEE. Le reglage se pose dans le HTML sans toucher a un
//      script (les empreintes CSP en dependent), et rien de saisi n'y entre
//      comme du code.
//   4. UNE ADRESSE QUI CASSE. Une ancienne adresse publiee redirige ; une
//      adresse inconnue rend la vraie page 404, avec le statut 404.
//   5. UN RETOUR EN ARRIERE IMPOSSIBLE. Chaque publication se republie.

import fs from 'fs';
import os from 'os';
import path from 'path';
import { createRequire } from 'module';

process.env.ADMIN_MDP = 'essai';
delete process.env.BLOB_READ_WRITE_TOKEN;
delete process.env.SEO_DEPLOY_HOOK;

const require = createRequire(import.meta.url);
const RACINE = path.join(path.dirname(new URL(import.meta.url).pathname), '..', 'site');
const handler = (await import('../site/api/admin.js')).default;
const seo = require('../site/api/_seo.js');
const { appliquer, preparerPublic } = require('../site/api/_seo_appliquer.js');

let cookie = '';
function appel(query, { methode = 'GET', body = null, avecCookie = true, avec } = {}) {
  const c = avec !== undefined ? avec : (avecCookie ? cookie : '');
  const req = { method: methode, query, body, headers: c ? { cookie: c } : {} };
  const out = { entetes: {} };
  const res = {
    statusCode: 0,
    setHeader(k, v) { out.entetes[k] = v; },
    getHeader(k) { return out.entetes[k]; },
    status(x) { out.code = x; return res; },
    json(j) { out.json = j; return res; },
    send(t) { out.texte = String(t); return res; },
  };
  return Promise.resolve(handler(req, res)).then(() => out);
}

let ok = 0, ko = 0;
function verifie(nom, condition, detail) {
  if (condition) { ok++; console.log('  ok     ', nom); }
  else { ko++; console.log('  ECHEC  ', nom, detail === undefined ? '' : JSON.stringify(detail).slice(0, 400)); }
}
const poser = (entree, o) => appel({ a: 'seo-page' }, { methode: 'POST', body: { entree, nom: 'Accueil' }, ...o });
const publier = (resume, o) => appel({ a: 'publier-seo' }, { methode: 'POST', body: { resume }, ...o });
const etat = async () => (await appel({ a: 'tout' })).json.donnees.seo || {};

// ── Connexion (le compte de secours est administrateur) ────────────────────
{
  const r = await appel({ a: 'entrer' }, { methode: 'POST', body: { mdp: 'essai' } });
  cookie = String(r.entetes['Set-Cookie'] || '').split(';')[0];
  verifie('connexion acceptee', r.code === 200 && cookie.startsWith('evn_adm='), r.json);
}

// ── Ce que le serveur refuse ───────────────────────────────────────────────
{
  const r = await poser({ id: '../etc/passwd', titre: 'x' });
  verifie('une page au nom impossible est refusee', r.code === 422, r.json);
  const r2 = await poser({ id: 'index', titre: 'x'.repeat(81) });
  verifie('un titre absurde est refuse, pas coupe', r2.code === 422 && /80/.test(r2.json.message), r2.json);
  const r3 = await poser({ id: 'index', image: 'https://ailleurs.com/pixel.gif' });
  verifie('une image hors du site est refusee', r3.code === 422 && r3.json.champs.includes('image'), r3.json);
}

// ── Enregistrer ne publie pas ──────────────────────────────────────────────
{
  const r = await poser({ id: 'index', motcle: 'hôtel Assinie', titre: 'Hôtel à Assinie au bord de la lagune — Hôtel Evannath',
    description: 'Piscine, spa et paillote sur la lagune Aby.', image: 'gal-lag-ponton' });
  verifie('le reglage est enregistre', r.code === 200 && r.json.reglage && r.json.reglage.par, r.json);
  verifie('la fin « — Hôtel Evannath » recopiee est retiree (elle est ajoutee seule)',
    r.json.reglage.titre === 'Hôtel à Assinie au bord de la lagune', r.json.reglage.titre);
  const s = await etat();
  verifie('rien n est encore publie', !(s.publications || []).length, s.publications);
  verifie('l onglet voit une page en attente', seo.enAttente(s).pages.join() === 'index', seo.enAttente(s));
}

// ── Le mot-cle seul n'a rien a publier ─────────────────────────────────────
{
  await poser({ id: 'contact', motcle: 'hôtel près d Abidjan' });
  const s = await etat();
  verifie('un mot-cle (invisible pour Google) n attend pas de publication',
    !seo.enAttente(s).pages.includes('contact'), seo.enAttente(s));
}

// ── Les redirections ───────────────────────────────────────────────────────
let idRedir = '';
{
  const mauvais = await appel({ a: 'seo-redirection' }, { methode: 'POST', body: { entree: { de: 'nos-chambres', vers: '/chambres' } } });
  verifie('une ancienne adresse sans « / » est refusee', mauvais.code === 422, mauvais.json);
  const boucle = await appel({ a: 'seo-redirection' }, { methode: 'POST', body: { entree: { de: '/chambres/', vers: '/chambres' } } });
  verifie('une adresse vers elle-meme est refusee', boucle.code === 422, boucle.json);
  const piege = await appel({ a: 'seo-redirection' }, { methode: 'POST', body: { entree: { de: '/x', vers: 'javascript:alert(1)' } } });
  verifie('une destination « javascript: » est refusee', piege.code === 422, piege.json);
  const r = await appel({ a: 'seo-redirection' }, { methode: 'POST',
    body: { entree: { de: 'https://evannathhotel.com/Nos-Chambres.html/', vers: '/chambres' } } });
  idRedir = r.json.redirection && r.json.redirection.id;
  verifie('l adresse complete collee est ramenee a son chemin', r.code === 200
    && r.json.redirection.de === '/nos-chambres.html', r.json);
  const avant = await appel({ a: 'introuvable', p: '/nos-chambres.html' }, { avecCookie: false });
  verifie('non publiee : l ancienne adresse rend encore la page 404', avant.code === 404, avant.code);
}

// ── Sans le droit, rien ne s'ecrit ─────────────────────────────────────────
{
  const r = await publier('x', { avec: '' });
  verifie('sans session : refuse (401)', r.code === 401, r.code);
  const { droitRequis, peut, ROLES } = require('../site/api/_comptes.js');
  verifie('publier demande le droit « referencement »', droitRequis('publier-seo') === 'referencement'
    && droitRequis('seo-page') === 'referencement' && droitRequis('retablir-seo') === 'referencement', '');
  verifie('l agence (Communication) peut publier', peut('communication', 'referencement')
    && ROLES.communication.vues.includes('seo'), ROLES.communication);
  verifie('Reception et Lecture seule ne le peuvent pas',
    !peut('reception', 'referencement') && !peut('lecture', 'referencement'), '');
}

// ── Publier ────────────────────────────────────────────────────────────────
let premiere = null;
{
  const r = await publier('Accueil : titre et description');
  premiere = r.json.publication;
  verifie('la publication est enregistree, datee et signee', r.code === 200 && premiere
    && premiere.par && premiere.t && premiere.pages.index, r.json);
  verifie('sans crochet de deploiement, on le dit en clair',
    r.json.deploiement === 'sans-crochet' && /prochain déploiement/.test(r.json.message), r.json);
  const s = await etat();
  verifie('plus rien en attente', seo.enAttente(s).total === 0, seo.enAttente(s));
  const encore = await publier('');
  verifie('republier sans changement : refuse, avec une raison', encore.code === 409, encore.json);
  const red = await appel({ a: 'introuvable', p: '/NOS-CHAMBRES.HTML' }, { avecCookie: false });
  verifie('publiee : l ancienne adresse redirige (301)', red.code === 301 && red.entetes.Location === '/chambres',
    { code: red.code, loc: red.entetes.Location });
  const inconnue = await appel({ a: 'introuvable', p: '/wp-login.php' }, { avecCookie: false });
  verifie('une adresse inconnue : la page 404, statut 404', inconnue.code === 404
    && inconnue.texte === fs.readFileSync(path.join(RACINE, '404.html'), 'utf8'), inconnue.code);
}

// ── Revenir en arriere ─────────────────────────────────────────────────────
{
  await poser({ id: 'index', titre: 'Un titre malheureux', description: 'Oups.' });
  await appel({ a: 'seo-redirection-retirer' }, { methode: 'POST', body: { id: idRedir } });
  const r2 = await publier('Erreur');
  verifie('une seconde publication', r2.code === 200, r2.json);
  const r = await appel({ a: 'retablir-seo' }, { methode: 'POST', body: { id: premiere.id } });
  verifie('revenir a la premiere version la republie', r.code === 200 && /Retour à la version/.test(r.json.publication.resume), r.json);
  const s = await etat();
  verifie('le titre de la premiere version est revenu',
    s.pages.index.titre === 'Hôtel à Assinie au bord de la lagune', s.pages.index);
  verifie('la redirection retiree est revenue', (s.redirections || []).length === 1, s.redirections);
  verifie('l historique s allonge, il n est jamais reecrit', s.publications.length === 3, s.publications.length);
  const deja = await appel({ a: 'retablir-seo' }, { methode: 'POST', body: { id: premiere.id } });
  verifie('revenir a la version deja en ligne : refuse', deja.code === 409, deja.json);
}

// ── Poser une publication dans les pages (l'etape de construction) ─────────
{
  const copie = fs.mkdtempSync(path.join(os.tmpdir(), 'seo-'));
  for (const f of ['index.html', 'mentions-legales.html', 'spa.html']) fs.copyFileSync(path.join(RACINE, f), path.join(copie, f));
  fs.mkdirSync(path.join(copie, 'img', 'opt'), { recursive: true });
  fs.copyFileSync(path.join(RACINE, 'img/opt/gal-lag-ponton.jpg'), path.join(copie, 'img/opt/gal-lag-ponton.jpg'));
  const canonSpa = fs.readFileSync(path.join(RACINE, 'spa.html'), 'utf8').match(/<link rel="canonical" href="([^"]+)"/)[1];
  fs.writeFileSync(path.join(copie, 'sitemap.xml'), '<urlset>\n  <url>\n    <loc>' + canonSpa
    + '</loc>\n  </url>\n  <url>\n    <loc>https://x/autre</loc>\n  </url>\n</urlset>\n');
  const pub = { id: 'p1', t: '2026-10-26T10:00:00Z', par: 'Awa K.', pages: {
    index: { titre: 'Piège </title><script>alert(1)</script> $& fin', description: 'Une "description" <b>sûre</b>', image: 'gal-lag-ponton' },
    spa: { masquer: true, image: 'photo-absente' },
    'n-existe-pas': { titre: 'x' },
  } };
  const avant = fs.readFileSync(path.join(copie, 'index.html'), 'utf8');
  const lignes = appliquer(copie, pub);
  const h = fs.readFileSync(path.join(copie, 'index.html'), 'utf8');
  const scripts = (x) => (x.match(/<script\b[^>]*>[\s\S]*?<\/script>/g) || []).join('');
  verifie('le titre est pose, avec sa fin', h.includes('<title>Piège &lt;/title&gt;&lt;script&gt;alert(1)&lt;/script&gt; $&amp; fin — Hôtel Evannath</title>'),
    (h.match(/<title>[^<]*<\/title>/) || [''])[0]);
  verifie('og:title suit le titre', h.includes('<meta property="og:title" content="Piège &lt;/title&gt;'), '');
  verifie('la description est posee, echappee', h.includes('<meta name="description" content="Une &quot;description&quot; &lt;b&gt;sûre&lt;/b&gt;">')
    && h.includes('<meta property="og:description" content="Une &quot;description&quot;'), '');
  verifie('l image de partage change, et ses anciennes dimensions partent',
    /<meta property="og:image" content="[^"]+\/img\/opt\/gal-lag-ponton\.jpg">/.test(h) && !h.includes('og:image:width'), '');
  verifie('aucun script de la page n a bouge (empreintes CSP intactes)', scripts(h) === scripts(avant), '');
  const s = fs.readFileSync(path.join(copie, 'spa.html'), 'utf8');
  verifie('une page masquee porte noindex', /<meta name="robots" content="[^"]*noindex/.test(s), '');
  verifie('une photo absente ne remplace pas l image', s.includes('/img/opt/gal-spa-couchant.jpg')
    && lignes.some((l) => /absente/.test(l)), lignes);
  const plan = fs.readFileSync(path.join(copie, 'sitemap.xml'), 'utf8');
  verifie('une page masquee sort du plan du site', !plan.includes(canonSpa) && plan.includes('https://x/autre'), plan);
  verifie('une page inconnue est ignoree, sans erreur', lignes.some((l) => /n-existe-pas : page absente/.test(l)), lignes);
  const marque = JSON.parse(fs.readFileSync(path.join(copie, 'seo-publication.json'), 'utf8'));
  verifie('seo-publication.json dit quelle publication est en ligne', marque.id === 'p1', marque);
  const sansRobots = seo.appliquerPage('<meta name="viewport" content="x">\n<title>a</title>', { masquer: true });
  verifie('noindex est ajoute quand la page n a pas de balise robots',
    sansRobots.html.includes('<meta name="robots" content="noindex, follow">'), sansRobots.html);
  fs.rmSync(copie, { recursive: true, force: true });
}

// ── public/ : ce que Vercel sert apres la construction ────────────────────
{
  const src = fs.mkdtempSync(path.join(os.tmpdir(), 'seo-src-'));
  for (const f of ['index.html', 'robots.txt', 'package.json', 'vercel.json', 'build-index.py',
    'index-template.html', '.vercelignore']) fs.writeFileSync(path.join(src, f), 'x');
  for (const d of ['api', 'node_modules', 'img/opt', 'admin', 'donnees']) fs.mkdirSync(path.join(src, d), { recursive: true });
  fs.writeFileSync(path.join(src, 'img/opt/a.jpg'), 'x');
  fs.writeFileSync(path.join(src, 'admin/index.html'), 'x');
  fs.writeFileSync(path.join(src, 'api/admin.js'), 'x');
  fs.mkdirSync(path.join(src, 'public'));
  fs.writeFileSync(path.join(src, 'public/ancien.html'), 'x');
  const pub = preparerPublic(src);
  const a = (f) => fs.existsSync(path.join(pub, f));
  verifie('public/ recoit les pages, les images, l administration et les donnees',
    a('index.html') && a('robots.txt') && a('img/opt/a.jpg') && a('admin/index.html') && a('donnees'), fs.readdirSync(pub));
  verifie('ni les fonctions, ni les dependances, ni la configuration, ni les sources',
    !a('api') && !a('node_modules') && !a('package.json') && !a('vercel.json') && !a('build-index.py')
    && !a('index-template.html') && !a('.vercelignore') && !a('public'), fs.readdirSync(pub));
  verifie('un ancien public/ est remplace, pas complete', !a('ancien.html'), '');
  verifie('le depot n est pas touche', fs.existsSync(path.join(src, 'api/admin.js')) && fs.existsSync(path.join(src, 'index.html')), '');
  fs.rmSync(src, { recursive: true, force: true });
}

// ── Les fichiers generes sont a jour ──────────────────────────────────────
{
  verifie('api/_page_404.js est la copie exacte de 404.html (build-404.py)',
    require('../site/api/_page_404.js') === fs.readFileSync(path.join(RACINE, '404.html'), 'utf8'), '');
  const m = JSON.parse(fs.readFileSync(path.join(RACINE, 'donnees/seo-pages.json'), 'utf8'));
  const accueil = m.pages.find((p) => p.id === 'index');
  const html = fs.readFileSync(path.join(RACINE, 'index.html'), 'utf8');
  verifie('le manifeste des pages dit le titre que porte la page (build-sitemap.py)',
    accueil && html.includes('<title>' + accueil.titre.replace(/&/g, '&amp;') + '</title>'), accueil);
  verifie('toutes les pages du manifeste existent', m.pages.every((p) => fs.existsSync(path.join(RACINE, p.id + '.html'))), '');
  const vc = JSON.parse(fs.readFileSync(path.join(RACINE, 'vercel.json'), 'utf8'));
  const derniere = vc.rewrites[vc.rewrites.length - 1];
  verifie('la reecriture « tout le reste » est la DERNIERE (sinon elle masquerait le Carnet)',
    derniere.source === '/(.*)' && /a=introuvable/.test(derniere.destination), derniere);
  verifie('Vercel lance l etape de construction', vc.buildCommand === 'node api/_seo_appliquer.js', vc.buildCommand);
}

console.log(`\n${ok} verifications passees, ${ko} en echec`);
process.exit(ko ? 1 : 0);
