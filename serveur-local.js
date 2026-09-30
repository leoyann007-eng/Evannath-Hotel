/* Serveur de developpement — sert le site ET execute les fonctions /api.
 *
 * `python -m http.server` sert les fichiers mais ignore le dossier api/ :
 * impossible d'essayer l'administration ou les formulaires en local. Ce
 * serveur comble ce trou, sans compte Vercel ni installation.
 *
 *   node serveur-local.js
 *   ADMIN_MDP=... node serveur-local.js        (pour ouvrir /admin)
 *
 * Les variables se lisent aussi dans un fichier .env.local a la racine, une
 * ligne par variable :  NOM=valeur
 *
 * Ce fichier ne part pas en production : Vercel execute site/api/*.js
 * lui-meme. Il n'existe que pour essayer avant de deployer.
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const RACINE = path.join(__dirname, 'site');
const PORT = Number(process.env.PORT || 5599);

// ── Variables d'environnement ──────────────────────────────────────────────
// On lit .env.local sans ecraser ce qui est deja defini : la ligne de commande
// l'emporte toujours sur le fichier.
const ENV = path.join(__dirname, '.env.local');
if (fs.existsSync(ENV)) {
  for (const ligne of fs.readFileSync(ENV, 'utf8').split(/\r?\n/)) {
    const t = ligne.trim();
    if (!t || t.startsWith('#')) continue;
    const i = t.indexOf('=');
    if (i < 1) continue;
    const nom = t.slice(0, i).trim();
    if (!(nom in process.env)) process.env[nom] = t.slice(i + 1).trim();
  }
  console.log('.env.local lu');
}

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
  '.webp': 'image/webp', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
  '.mp4': 'video/mp4', '.webmanifest': 'application/manifest+json',
  '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml; charset=utf-8',
  '.woff2': 'font/woff2',
};

/* Les fonctions attendent l'interface de Vercel : req.query, req.body deja
   analyse, res.status().json(). On la reconstitue. */
function habiller(req, res, requete) {
  req.query = Object.fromEntries(requete.searchParams);
  res.status = (c) => { res.statusCode = c; return res; };
  res.json = (o) => {
    if (!res.getHeader('Content-Type')) res.setHeader('Content-Type', TYPES['.json']);
    res.end(JSON.stringify(o));
    return res;
  };
  res.send = (t) => { res.end(t); return res; };
}

const modules = new Map();

/** Charge une fonction une seule fois, puis la reutilise. */
async function charger(fichier) {
  if (!modules.has(fichier)) {
    const mod = await import('file://' + fichier.replace(/\\/g, '/'));
    modules.set(fichier, mod.default || mod);
  }
  return modules.get(fichier);
}

/* Le corps, BRUT (Buffer) : une signature se verifie sur les octets exacts —
   voir api/lomi.mjs. L'analyse JSON vient apres, pour les fonctions (req, res). */
function corps(req) {
  return new Promise((resoudre) => {
    const morceaux = [];
    let taille = 0;
    req.on('data', (c) => { morceaux.push(c); taille += c.length; if (taille > 1e6) req.destroy(); });
    req.on('end', () => resoudre(Buffer.concat(morceaux)));
  });
}
function analyser(brut) {
  if (!brut.length) return undefined;
  const d = brut.toString('utf8');
  try { return JSON.parse(d); } catch { return d; }
}

const serveur = http.createServer(async (req, res) => {
  const requete = new URL(req.url, 'http://' + (req.headers.host || 'localhost'));
  let chemin = decodeURIComponent(requete.pathname);

  // ── Les fonctions ────────────────────────────────────────────────────────
  if (chemin.startsWith('/api/')) {
    const nom = chemin.slice(5).split('/')[0].replace(/[^\w-]/g, '');
    let fichier = path.join(RACINE, 'api', nom + '.js');
    if (!fs.existsSync(fichier)) fichier = path.join(RACINE, 'api', nom + '.mjs');
    if (!fs.existsSync(fichier)) {
      res.writeHead(404, { 'Content-Type': TYPES['.json'] });
      return res.end(JSON.stringify({ ok: false, message: 'Fonction inconnue : ' + nom }));
    }
    try {
      const brut = await corps(req);
      req.body = analyser(brut);
      habiller(req, res, requete);
      // Le module est charge UNE fois et reutilise. Le recharger a chaque
      // appel remettrait a zero son etat interne — et le stockage de
      // demonstration de l'administration vit precisement la : chaque
      // evenement cree etait perdu dans la seconde.
      // Consequence : une modification du code demande un redemarrage.
      const fn = await charger(fichier);
      if (typeof fn === 'function') { await fn(req, res); return; }
      /* Forme « Web » : export POST(request) / GET(request), comme Vercel
         l'accepte. On lui donne une vraie Request, corps brut compris. */
      const methode = req.method.toUpperCase();
      if (typeof fn[methode] !== 'function') {
        res.writeHead(405, { 'Content-Type': TYPES['.json'] });
        return res.end(JSON.stringify({ ok: false }));
      }
      const reponse = await fn[methode](new Request(requete.href, {
        method: methode, headers: req.headers,
        body: methode === 'GET' || methode === 'HEAD' ? undefined : brut,
      }));
      res.writeHead(reponse.status, Object.fromEntries(reponse.headers));
      /* Le corps passe morceau par morceau, comme chez Vercel : une reponse
         en flux (api/chat.mjs) doit s'ecrire a mesure, pas a la fin. */
      if (!reponse.body) return res.end();
      const lecteur = reponse.body.getReader();
      for (;;) {
        const { done, value } = await lecteur.read();
        if (done) break;
        res.write(Buffer.from(value));
      }
      res.end();
    } catch (e) {
      console.error('api/' + nom, e);
      if (!res.headersSent) res.writeHead(500, { 'Content-Type': TYPES['.json'] });
      res.end(JSON.stringify({ ok: false, message: String(e && e.message) }));
    }
    return;
  }

  // ── Les fichiers ─────────────────────────────────────────────────────────
  if (chemin.endsWith('/')) chemin += 'index.html';
  let fichier = path.join(RACINE, chemin);

  // cleanUrls : /contact sert contact.html, comme en production.
  // Un dossier existant — /admin — doit servir son index.html : tester
  // seulement l'absence du chemin laissait passer ce cas, et /admin
  // repondait 404 alors que la page etait bien la.
  if (!path.extname(fichier)) {
    if (fs.existsSync(fichier + '.html')) fichier += '.html';
    else if (fs.existsSync(path.join(fichier, 'index.html'))) fichier = path.join(fichier, 'index.html');
  }

  // On ne sort pas de site/ : un chemin qui remonte est refuse.
  if (!fichier.startsWith(RACINE) || !fs.existsSync(fichier) || fs.statSync(fichier).isDirectory()) {
    const p404 = path.join(RACINE, '404.html');
    res.writeHead(404, { 'Content-Type': TYPES['.html'] });
    return res.end(fs.existsSync(p404) ? fs.readFileSync(p404) : 'Introuvable');
  }

  res.writeHead(200, {
    'Content-Type': TYPES[path.extname(fichier).toLowerCase()] || 'application/octet-stream',
    'Cache-Control': 'no-store',
  });
  fs.createReadStream(fichier).pipe(res);
});

serveur.listen(PORT, () => {
  console.log('');
  console.log('  Site           http://localhost:' + PORT);
  console.log('  Administration http://localhost:' + PORT + '/admin/');
  console.log('');
  console.log('  ADMIN_MDP  ' + (process.env.ADMIN_MDP ? 'défini' : 'ABSENT — /admin refusera la connexion'));
  console.log('  Stockage   ' + (process.env.BLOB_READ_WRITE_TOKEN ? 'durable (Vercel Blob)' : 'mémoire — perdu à chaque redémarrage'));
  console.log('');
});
