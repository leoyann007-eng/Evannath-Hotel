/* Capture une page en image, via le protocole DevTools de Chrome.
 *
 * --screenshot en ligne de commande ne sait ni se connecter, ni faire defiler,
 * ni attendre : impossible de photographier une page derriere un mot de passe.
 * Le protocole, lui, permet d'executer du JavaScript avant de declencher.
 *
 *   node .outils/capturer.js <url> <sortie.png> [largeur] [hauteur] \
 *        [apres.js] [amont.js]
 *
 * apres.js est evalue dans la page une fois chargee — c'est la qu'on se
 * connecte, qu'on defile ou qu'on ouvre un menu.
 *
 * amont.js est injecte AVANT que la page n'execute la moindre ligne. C'est le
 * seul moyen d'essayer en local une page qui interroge une API distante : on y
 * remplace fetch, et la page consomme les donnees qu'on lui donne.
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
// Port tire au sort : un port fixe rattacherait le script a une instance de
// Chrome deja ouverte, dont l'onglet montre une autre page.
const PORT = 9000 + Math.floor(Math.random() * 900);

const [url, sortie, larg, haut, avant, amont] = process.argv.slice(2);
if (!url || !sortie) {
  console.error('usage : node .outils/capturer.js <url> <sortie.png>'
    + ' [largeur] [hauteur] [apres.js] [amont.js]');
  process.exit(2);
}
const L = Number(larg) || 1280;
const H = Number(haut) || 900;

const profil = path.join(os.tmpdir(), 'chr-cap-' + Date.now());
const chrome = spawn(CHROME, [
  '--headless=old', '--disable-gpu', '--no-sandbox',
  '--remote-debugging-port=' + PORT,
  '--user-data-dir=' + profil,
  '--window-size=' + L + ',' + H,
  'about:blank',
], { stdio: 'ignore' });

const dodo = (ms) => new Promise((r) => setTimeout(r, ms));

async function cible() {
  for (let i = 0; i < 40; i++) {
    try {
      const r = await fetch('http://127.0.0.1:' + PORT + '/json/list');
      const p = (await r.json()).find((x) => x.type === 'page' && x.webSocketDebuggerUrl);
      if (p) return p.webSocketDebuggerUrl;
    } catch (e) { /* pas encore la */ }
    await dodo(250);
  }
  throw new Error("Chrome n'a pas ouvert son port de debogage.");
}

(async () => {
  const ws = new WebSocket(await cible());
  await new Promise((ok, ko) => { ws.onopen = ok; ws.onerror = ko; });

  let n = 0;
  const attentes = new Map();
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.id && attentes.has(m.id)) {
      const { ok, ko } = attentes.get(m.id);
      attentes.delete(m.id);
      m.error ? ko(new Error(m.error.message)) : ok(m.result);
    }
  };
  const cmd = (method, params) => new Promise((ok, ko) => {
    const id = ++n;
    attentes.set(id, { ok, ko });
    ws.send(JSON.stringify({ id, method, params: params || {} }));
  });

  await cmd('Page.enable');
  await cmd('Emulation.setDeviceMetricsOverride', {
    width: L, height: H, deviceScaleFactor: 1, mobile: false,
  });
  if (amont) {
    // Pose le script avant toute navigation : il s'executera en tete de
    // chaque document, donc avant le code de la page.
    await cmd('Page.addScriptToEvaluateOnNewDocument', {
      source: fs.readFileSync(amont, 'utf8'),
    });
  }
  await cmd('Page.navigate', { url });
  await dodo(2500);
  await cmd('Runtime.evaluate', { expression: 'document.fonts.ready', awaitPromise: true });

  if (avant) {
    const code = fs.readFileSync(avant, 'utf8');
    const r = await cmd('Runtime.evaluate', {
      expression: '(async () => {' + code + '})()',
      awaitPromise: true, returnByValue: true,
    });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.text);
    if (r.result && r.result.value !== undefined) {
      console.log('script :', JSON.stringify(r.result.value));
    }
  }

  const img = await cmd('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(sortie, Buffer.from(img.data, 'base64'));
  console.log('ecrit : %s (%d Ko)', sortie, Math.round(fs.statSync(sortie).size / 1024));

  ws.close();
  chrome.kill();
  try { fs.rmSync(profil, { recursive: true, force: true }); } catch (e) { /* tant pis */ }
  process.exit(0);
})().catch((e) => {
  console.error('echec :', e.message);
  chrome.kill();
  process.exit(1);
});
