// Le vrai paquet @vercel/blob contre un faux Vercel Blob.
//
// Les autres tests remplacent @vercel/blob par une imitation (outils.blob) :
// ils ne verraient pas un changement de comportement du paquet lui-meme.
// C'est arrive : depuis la version 1.0, put() n'ajoute plus de suffixe
// aleatoire par defaut et refuse d'ecraser un fichier existant. Le magasin,
// qui ecrit chaque version sous le meme nom (evannath/donnees.json) et compte
// sur le suffixe pour les distinguer, aurait refuse sa seconde ecriture.
//
// Ici, le paquet installe parle HTTP a un serveur local qui se comporte
// comme Blob sur ce point : sans suffixe demande, un nom deja pris est refuse.
//
// Lance depuis la racine du depot :  node tests/blob.test.mjs
import crypto from 'node:crypto';
import http from 'node:http';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

let ok = 0, ko = 0;
function verifie(nom, condition, detail) {
  if (condition) { ok++; console.log('  ok     ', nom); }
  else { ko++; console.log('  ECHEC  ', nom, detail === undefined ? '' : JSON.stringify(detail)); }
}

// ── Le faux Vercel Blob ─────────────────────────────────────────────────────
const fichiers = new Map();          // pathname -> { contenu, type, uploadedAt }
const requetes = [];                 // les PUT recus, pour verifier leurs en-tetes
let t = Date.parse('2026-10-01T00:00:00Z');
let base = '';
const lireCorps = (req) => new Promise((fin) => {
  const morceaux = []; req.on('data', (m) => morceaux.push(m)); req.on('end', () => fin(Buffer.concat(morceaux)));
});
const repondre = (res, code, objet) => {
  res.writeHead(code, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(objet));
};
const decrire = (p) => ({ url: base + '/f/' + p, downloadUrl: base + '/f/' + p + '?download=1', pathname: p,
  size: fichiers.get(p).contenu.length, uploadedAt: new Date(fichiers.get(p).uploadedAt).toISOString(), etag: '"' + p + '"' });

const serveur = http.createServer(async (req, res) => {
  const u = new URL(req.url, base);
  if (u.pathname.startsWith('/f/')) {                          // lecture publique
    const f = fichiers.get(decodeURIComponent(u.pathname.slice(3)));
    if (!f) return repondre(res, 404, {});
    res.writeHead(200, { 'Content-Type': f.type }); return res.end(f.contenu);
  }
  if (!/^Bearer vercel_blob_rw_/.test(req.headers.authorization || '')) {
    return repondre(res, 403, { error: { code: 'forbidden', message: 'Access denied' } });
  }
  if (req.method === 'PUT') {                                  // put()
    let p = u.searchParams.get('pathname');
    const corps = await lireCorps(req);
    requetes.push({ pathname: p, suffixe: req.headers['x-add-random-suffix'], ecrase: req.headers['x-allow-overwrite'] });
    if (req.headers['x-add-random-suffix'] === '1') {
      const point = p.lastIndexOf('.');
      p = p.slice(0, point) + '-' + crypto.randomBytes(10).toString('hex') + p.slice(point);
    } else if (fichiers.has(p) && req.headers['x-allow-overwrite'] !== '1') {
      return repondre(res, 400, { error: { code: 'bad_request',
        message: 'This blob already exists, use `allowOverwrite: true` if you want to overwrite it. Or `addRandomSuffix: true` to generate a unique filename.' } });
    }
    fichiers.set(p, { contenu: corps, type: req.headers['x-content-type'] || 'application/octet-stream', uploadedAt: (t += 60_000) });
    return repondre(res, 200, { ...decrire(p), contentType: fichiers.get(p).type, contentDisposition: 'inline' });
  }
  if (req.method === 'GET') {                                  // list()
    const prefixe = u.searchParams.get('prefix') || '';
    const blobs = [...fichiers.keys()].filter((p) => p.startsWith(prefixe)).map(decrire);
    return repondre(res, 200, { blobs, hasMore: false });
  }
  if (req.method === 'POST' && u.pathname === '/delete') {     // del()
    const { urls } = JSON.parse(String(await lireCorps(req)));
    for (const x of urls) fichiers.delete(decodeURIComponent(String(x).replace(base + '/f/', '')));
    return repondre(res, 200, {});
  }
  repondre(res, 404, { error: { code: 'not_found', message: 'route' } });
});
await new Promise((fin) => serveur.listen(0, '127.0.0.1', fin));
base = 'http://127.0.0.1:' + serveur.address().port;

process.env.VERCEL_BLOB_API_URL = base;
process.env.VERCEL_ENV = 'production';
delete process.env.EVN_ENV;
delete process.env.DATABASE_URL;
delete process.env.POSTGRES_URL;
const JETON = 'vercel_blob_rw_essai_secret';

// Le paquet tel qu'il est installe pour les fonctions : site/node_modules.
const duSite = createRequire(new URL('../site/api/_magasin.js', import.meta.url));
const { put } = duSite('@vercel/blob');
const { version } = JSON.parse(require('node:fs').readFileSync(
  new URL('../site/node_modules/@vercel/blob/package.json', import.meta.url), 'utf8'));
console.log('\n@vercel/blob ' + version + ' contre un faux Vercel Blob');

console.log('\nLe faux serveur se comporte comme Blob (sinon ce test ne prouverait rien)');
{
  await put('essai/sans-suffixe.json', '{}', { access: 'public', token: JETON, addRandomSuffix: false });
  let refuse = null;
  try { await put('essai/sans-suffixe.json', '{}', { access: 'public', token: JETON, addRandomSuffix: false }); }
  catch (e) { refuse = e; }
  verifie('un nom deja pris, sans suffixe, est refuse', refuse && /already exists/.test(refuse.message), refuse && refuse.message);
}

console.log('\nLe magasin en mode Blob, avec le vrai paquet');
{
  const magasin = require('../site/api/_magasin.js');
  const doc = magasin.document({ cle: 'donnees', prefixeBlob: 'evannath/donnees', garde: 3,
    vide: () => ({ evenements: [] }), jeton: JETON, nom: 'du fichier de données' });
  verifie('le mode est bien Blob', doc.mode === 'blob', doc.mode);

  const ecritures = [];
  for (let i = 1; i <= 4; i++) ecritures.push(await doc.modifier((d) => { d.evenements.push({ titre: 'n' + i }); }));
  verifie('quatre ecritures successives passent', ecritures.every((r) => r.ok), ecritures);

  const l = await doc.lire();
  verifie('la lecture rend la derniere version', l.ok && l.d.evenements.length === 4
    && l.d.evenements[3].titre === 'n4', l);
  const versions = [...fichiers.keys()].filter((p) => p.startsWith('evannath/donnees-'));
  verifie('les sauvegardes sont limitees a « garde » (3)', versions.length === 3, versions);
  verifie('chaque version porte un suffixe aleatoire', versions.every((p) => /^evannath\/donnees-[0-9a-f]{20}\.json$/.test(p)), versions);
  verifie('aucun fichier a l adresse fixe, devinable', !fichiers.has('evannath/donnees.json'));
  const puts = requetes.filter((r) => r.pathname === 'evannath/donnees.json');
  verifie('chaque ecriture demande le suffixe', puts.length === 4 && puts.every((r) => r.suffixe === '1'), puts);
}

console.log('\nLe depot d une affiche (api/admin.js) demande aussi le suffixe');
{
  const src = require('node:fs').readFileSync(new URL('../site/api/admin.js', import.meta.url), 'utf8');
  const appel = (src.match(/await put\(nom, octets, \{[\s\S]*?\}\);/) || [''])[0];
  verifie('put(nom, octets, { … addRandomSuffix: true })', /addRandomSuffix:\s*true/.test(appel), appel);
}

serveur.close();
console.log('\n  %d verifications, %d echec(s)\n', ok + ko, ko);
process.exit(ko ? 1 : 0);
