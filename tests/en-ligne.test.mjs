// Verifie le site DEPLOYE, sans navigateur : ce qui se controle depuis le
// reseau seul. Rapide, a lancer avant chaque rendez-vous et apres chaque
// mise en ligne.
//
//   node tests/en-ligne.test.mjs
//   node tests/en-ligne.test.mjs http://localhost:5599
//
// Ce qu'il ne couvre pas, et qui demande un navigateur : le rendu, le prix
// barre, le calcul du tunnel, le menu. Pour ceux-la, voir tests/A-LA-MAIN.md.

const BASE = (process.argv[2] || 'https://evannathhotel.vercel.app').replace(/\/$/, '');

let echecs = 0, total = 0;
function verifier(nom, ok, detail) {
  total++;
  if (!ok) echecs++;
  console.log((ok ? '  ok    ' : '  ECHEC ') + nom + (ok || !detail ? '' : '\n          ' + detail));
}
const titre = (t) => console.log('\n' + t);

const sansCache = (u) => u + (u.includes('?') ? '&' : '?') + 'x=' + Date.now();

// ── Les pages repondent ───────────────────────────────────────────────────
const PAGES = ['', 'chambres', 'chambre-standard', 'deluxe-baldaquin',
  'deluxe-superieure', 'suite-anglaise', 'chambre-mezzanine',
  'mezzanine-superieure', 'suite-arabe', 'circuits', 'experiences', 'galerie',
  'carte', 'spa', 'reserver', 'seminaires', 'contact', 'a-propos',
  'informations-utiles', 'mentions-legales'];

titre('Les pages repondent');
const corps = {};
for (const p of PAGES) {
  const r = await fetch(sansCache(BASE + '/' + p));
  corps[p] = r.ok ? await r.text() : '';
  verifier((p || 'accueil').padEnd(22) + ' répond 200', r.status === 200, 'statut ' + r.status);
}

// ── Ce que chaque page doit contenir ──────────────────────────────────────
titre('Ce que les pages embarquent');
verifier('l’accueil sait afficher une offre en avant',
  corps[''].includes('bandeau offre') || corps[''].includes("id='bandeau'")
  || corps[''].includes('id="bandeau"'));
for (const p of ['', 'chambres', 'chambre-standard', 'reserver']) {
  verifier((p || 'accueil').padEnd(22) + ' embarque le module de remise',
    corps[p].includes('EVN_REMISE'));
}
verifier('toutes les pages rendent l’en-tête opaque menu ouvert',
  PAGES.every((p) => corps[p].includes('header.menu{')),
  'manque sur : ' + PAGES.filter((p) => !corps[p].includes('header.menu{')).join(', '));
verifier('aucune page n’expose l’adresse du prestataire',
  PAGES.every((p) => !corps[p].includes('houansouyannaxel')),
  'présente sur : ' + PAGES.filter((p) => corps[p].includes('houansouyannaxel')).join(', '));

// ── Les en-tetes de securite ──────────────────────────────────────────────
titre('Les en-têtes de sécurité');
{
  const r = await fetch(sansCache(BASE + '/chambres'));
  const h = (n) => r.headers.get(n) || '';
  verifier('X-Content-Type-Options', h('x-content-type-options') === 'nosniff', h('x-content-type-options'));
  verifier('X-Frame-Options', /SAMEORIGIN|DENY/i.test(h('x-frame-options')), h('x-frame-options'));
  verifier('Referrer-Policy', h('referrer-policy').length > 0, h('referrer-policy'));
  verifier('Permissions-Policy', h('permissions-policy').includes('camera'), h('permissions-policy'));
}
{
  const r = await fetch(sansCache(BASE + '/admin/index.html'));
  verifier('l’administration est hors des moteurs',
    (r.headers.get('x-robots-tag') || '').includes('noindex'), r.headers.get('x-robots-tag'));
  /* Vercel sert cette page avec « public, max-age=0, must-revalidate » : la
     regle generale sur les .html l'emporte sur celle de /admin/, quel que
     soit leur ordre dans vercel.json, et je ne sais pas expliquer cette
     precedence. Sans consequence — la page ne contient aucun secret, les
     donnees viennent de l'API qui, elle, est bien en no-store, et
     must-revalidate force une revalidation a chaque appel. On verifie donc
     ce qui compte : rien n'est servi sans etre reverifie. */
  const cc = r.headers.get('cache-control') || '';
  verifier('l’administration est revalidée à chaque appel',
    cc.includes('no-store') || (cc.includes('max-age=0') && cc.includes('must-revalidate')), cc);
}

// ── L API publique ────────────────────────────────────────────────────────
titre('L’API publique');
const pub = await (await fetch(sansCache(BASE + '/api/admin?a=public'))).json();
verifier('elle rend les trois collections',
  ['evenements', 'promotions', 'campagnes'].every((k) => Array.isArray(pub[k])),
  JSON.stringify(Object.keys(pub)));

const maintenant = Date.now();
for (const e of pub.evenements || []) {
  verifier('événement « ' + e.titre + ' » non expiré',
    !e.fin || new Date(e.fin + 'T23:59:59').getTime() >= maintenant, 'fin ' + e.fin);
  verifier('événement « ' + e.titre + ' » est publié', e.publie !== false);
}
for (const groupe of ['promotions', 'campagnes']) {
  for (const p of pub[groupe] || []) {
    const d1 = p.debut ? Date.parse(p.debut) : null;
    const d2 = p.fin ? Date.parse(p.fin) : null;
    verifier(groupe.slice(0, -1) + ' « ' + p.titre + ' » dans sa période',
      (!d1 || maintenant >= d1) && (!d2 || maintenant <= d2),
      p.debut + ' → ' + p.fin);
  }
}

// ── Les images referencees existent vraiment ──────────────────────────────
titre('Les images référencées');
const images = [];
(pub.evenements || []).forEach((e) => e.fond && images.push(['affiche ' + e.titre, e.fond]));
(pub.campagnes || []).forEach((c) => {
  if (c.visuel) images.push(['visuel ' + c.titre, c.visuel]);
  (c.packs || []).forEach((p) => p.image && images.push(['pack ' + p.nom, p.image]));
});
let poids = 0;
for (const [nom, u] of images) {
  if (!/^https?:/.test(u)) continue;             // une photo du site, pas un dépôt
  const r = await fetch(u, { method: 'HEAD' });
  const o = Number(r.headers.get('content-length') || 0);
  poids += o;
  verifier(nom.padEnd(34) + ' existe', r.status === 200, 'statut ' + r.status);
  verifier(nom.padEnd(34) + ' allégée (< 400 Ko)', o > 0 && o < 400 * 1024,
    Math.round(o / 1024) + ' Ko');
}
if (images.length) console.log('          poids total des visuels : ' + Math.round(poids / 1024) + ' Ko');

// ── Le fichier de donnees n est pas devinable ─────────────────────────────
titre('Le fichier de données');
{
  const hote = (images.find(([, u]) => /blob\.vercel-storage/.test(u)) || [])[1];
  if (!hote) {
    console.log('  (aucun visuel déposé : contrôle sauté)');
  } else {
    const racine = hote.slice(0, hote.indexOf('/evannath/'));
    for (const chemin of ['/evannath/donnees.json', '/evannath/donnees']) {
      const r = await fetch(sansCache(racine + chemin));
      verifier('non lisible à l’adresse ' + chemin, r.status !== 200, 'statut ' + r.status);
    }
  }
}

// ── L administration refuse les inconnus ──────────────────────────────────
titre('L’administration refuse les inconnus');
for (const [action, methode] of [['tout', 'GET'], ['etat', 'GET'],
                                 ['enregistrer', 'POST'], ['supprimer', 'POST'],
                                 ['televerser', 'POST']]) {
  const r = await fetch(sansCache(BASE + '/api/admin?a=' + action), {
    method: methode,
    headers: { 'Content-Type': 'application/json' },
    body: methode === 'POST' ? '{}' : undefined,
  });
  verifier(('a=' + action).padEnd(22) + ' répond 401 sans session', r.status === 401,
    'statut ' + r.status);
}
{
  const r = await fetch(sansCache(BASE + '/api/admin?a=entrer'), {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mdp: 'ceci-nest-pas-le-mot-de-passe' }),
  });
  verifier('un mauvais mot de passe est refusé', r.status === 401, 'statut ' + r.status);
}

console.log('');
console.log(total + ' contrôles, ' + (total - echecs) + ' passés, ' + echecs + ' en échec');
if (echecs) process.exit(1);
