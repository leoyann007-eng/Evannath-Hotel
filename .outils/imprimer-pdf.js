/* Imprime une page HTML en PDF, via le protocole DevTools de Chrome.
 *
 * Les drapeaux en ligne de commande — --print-to-pdf-no-header,
 * --no-pdf-header-footer — ne sont pas honores par le Chrome installe ici :
 * le PDF sortait avec la date, le titre, l'URL du fichier et un numero de
 * page imprimes par-dessus la mise en page. Le protocole, lui, expose
 * displayHeaderFooter, et il obeit.
 *
 *   node .outils/imprimer-pdf.js <fichier.html> <sortie.pdf>
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
/* Un port fixe rattachait le script a une instance de Chrome deja ouverte,
   dont l'onglet portait une ANCIENNE version de la page : le PDF sortait
   perime sans que rien ne le signale. Port tire au sort, et on navigue
   nous-memes vers l'URL avant d'imprimer. */
const PORT = 9000 + Math.floor(Math.random() * 900);

const entree = process.argv[2];
const sortie = process.argv[3];
if (!entree || !sortie) {
  console.error('usage : node .outils/imprimer-pdf.js <fichier.html> <sortie.pdf>');
  process.exit(2);
}

const url = 'file:///' + path.resolve(entree).replace(/\\/g, '/').replace(/ /g, '%20');
const profil = path.join(os.tmpdir(), 'chr-cdp-' + Date.now());

const chrome = spawn(CHROME, [
  '--headless=old', '--disable-gpu', '--no-sandbox',
  '--remote-debugging-port=' + PORT,
  '--user-data-dir=' + profil,
  url,
], { stdio: 'ignore' });

const dodo = (ms) => new Promise((r) => setTimeout(r, ms));

/** Le port met un instant a repondre : on reessaie plutot que de deviner. */
async function cible() {
  for (let i = 0; i < 40; i++) {
    try {
      const r = await fetch('http://127.0.0.1:' + PORT + '/json/list');
      const l = await r.json();
      const p = l.find((x) => x.type === 'page' && x.webSocketDebuggerUrl);
      if (p) return p.webSocketDebuggerUrl;
    } catch (e) { /* pas encore la */ }
    await dodo(250);
  }
  throw new Error("Chrome n'a pas ouvert son port de debogage.");
}

(async () => {
  const ws = new WebSocket(await cible());
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });

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

  // On charge la page nous-memes : c'est la seule facon de savoir QUELLE
  // version est imprimee.
  await cmd('Page.enable');
  const charge = new Promise((r) => {
    const avant = ws.onmessage;
    ws.onmessage = (e) => {
      avant(e);
      if (JSON.parse(e.data).method === 'Page.loadEventFired') r();
    };
  });
  await cmd('Page.navigate', { url });
  await Promise.race([charge, dodo(15000)]);

  // Les polices distantes doivent etre arrivees, sinon la page sort en
  // polices de secours.
  await dodo(1500);
  await cmd('Runtime.evaluate', { expression: 'document.fonts.ready', awaitPromise: true });

  // Preuve que la page imprimee est bien celle du disque.
  const t = await cmd('Runtime.evaluate', {
    expression: 'document.body.innerText.length', returnByValue: true });
  console.log('page chargee : %d caracteres', t.result.value);

  const r = await cmd('Page.printToPDF', {
    printBackground: true,
    displayHeaderFooter: false,      // le point de tout l'exercice
    preferCSSPageSize: true,
    marginTop: 0.55, marginBottom: 0.55, marginLeft: 0.47, marginRight: 0.47,
  });

  fs.writeFileSync(sortie, Buffer.from(r.data, 'base64'));
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
