/* Mesure le contraste de CHAQUE texte, sur CHAQUE page, dans un vrai
 * navigateur.
 *
 *   node .outils/contraste.js [http://localhost:5599]
 *
 * Pourquoi cet outil existe : le site est passe du noir au creme le
 * 24 septembre 2026. Le seul remplacement des jetons a produit quarante et
 * un defauts sur la seule page d'accueil — des gris clairs ecrits en dur,
 * prevus pour un fond sombre, tombes jusqu'a 1,24:1. Relire vingt et une
 * pages a l'oeil ne les aurait pas trouves.
 *
 * CE QU'IL NE VOIT PAS, ET C'EST IMPORTANT. Il compare la couleur d'un texte
 * a la couleur de FOND heritee. Une photographie n'est pas une couleur : un
 * titre pose sur un hero est donc ECARTE du verdict et seulement COMPTE. Sur
 * l'accueil, la mesure annonçait zero defaut pendant que le titre etait
 * illisible sur l'eau de la piscine. Ces textes-la se jugent a l'oeil, sur
 * capture, et le rapport dit combien il y en a par page.
 *
 * Les seuils sont ceux du WCAG AA : 4,5:1 pour du texte courant, 3:1 a
 * partir de 24 px, ou de 18,66 px en gras.
 */
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9000 + Math.floor(Math.random() * 900);
const BASE = (process.argv[2] || 'http://localhost:5599').replace(/\/$/, '');

const PAGES = [
  '', 'chambres', 'chambre-standard', 'deluxe-baldaquin', 'deluxe-superieure',
  'suite-anglaise', 'chambre-mezzanine', 'mezzanine-superieure', 'suite-arabe',
  'reserver', 'galerie', 'circuits', 'carte', 'spa', 'a-propos', 'contact',
  'experiences', 'seminaires', 'informations-utiles', 'mentions-legales', '404',
];

const MESURE = `(function(){
  var lum = function (c) {
    var m = (c || '').match(/\\d+(\\.\\d+)?/g);
    if (!m) return null;
    var v = m.slice(0, 3).map(function (x) {
      x = Number(x) / 255;
      return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
  };
  /* Le fond REELLEMENT vu.

     Un fond a 6 % d'opacite n'est pas un fond : c'est une teinte posee sur
     ce qu'il y a dessous. Le prendre pour opaque faisait annoncer 3:1 la ou
     l'oeil voit 9:1 — dix-huit faux defauts sur la seule page des mentions
     legales. On empile donc les couches jusqu'a l'opacite, et on compose. */
  var couches = function (e) {
    var pile = [], n = e;
    while (n && n !== document.documentElement) {
      var m = (getComputedStyle(n).backgroundColor || '').match(/[\\d.]+/g);
      if (m) {
        var a = m.length > 3 ? Number(m[3]) : 1;
        if (a > 0.004) {
          pile.push([Number(m[0]), Number(m[1]), Number(m[2]), a]);
          if (a >= 0.999) return pile;
        }
      }
      n = n.parentElement;
    }
    var r = (getComputedStyle(document.documentElement).backgroundColor || '').match(/[\\d.]+/g);
    pile.push(r && r.length >= 3 ? [Number(r[0]), Number(r[1]), Number(r[2]), 1] : [255, 255, 255, 1]);
    return pile;
  };
  var fond = function (e) {
    var pile = couches(e), c = pile[pile.length - 1].slice(0, 3);
    for (var i = pile.length - 2; i >= 0; i--) {
      var l = pile[i];
      c = [0, 1, 2].map(function (k) { return l[k] * l[3] + c[k] * (1 - l[3]); });
    }
    return 'rgb(' + c.map(Math.round).join(', ') + ')';
  };
  /* Un texte pose sur une PHOTOGRAPHIE : sa lisibilite ne se calcule pas
     ici. Mais un DEGRADE n'est pas une photographie, et les confondre a
     coute cher : « .carte » porte un voile blanc a 2,4 %, et cette seule
     ligne retirait du verdict chaque texte de chaque carte — 604 sur la
     seule vue des disponibilites. Le verdict annoncait zero defaut sur ce
     qu'il n'avait pas regarde.

     On n'ecarte donc que sur url() : une image reference. Un degrade se
     mesure contre la couleur composee du dessous. C'est une approximation
     — un degrade franc la rendrait fausse — mais mesurer approximativement
     vaut mieux que ne pas mesurer du tout. */
  var surImage = function (e) {
    var n = e;
    while (n && n !== document.documentElement) {
      var cs = getComputedStyle(n);
      if ((cs.backgroundImage || '').indexOf('url(') >= 0) return true;
      if (n.querySelector && n.matches('.hero, .bandeau, .lb, .mosaic, .slides')) return true;
      n = n.parentElement;
    }
    return false;
  };

  var defauts = [], mesures = 0, ecartes = 0;
  document.querySelectorAll('body *').forEach(function (e) {
    var propre = false;
    e.childNodes.forEach(function (n) {
      if (n.nodeType === 3 && n.textContent.trim()) propre = true;
    });
    if (!propre) return;
    var t = e.textContent.trim();
    if (!t || t.length > 300) return;
    var cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return;
    var r = e.getBoundingClientRect();
    if (!r.width || !r.height) return;
    if (surImage(e)) { ecartes++; return; }
    mesures++;
    var px = parseFloat(cs.fontSize), gras = parseInt(cs.fontWeight, 10) >= 700;
    var seuil = (px >= 24 || (px >= 18.66 && gras)) ? 3 : 4.5;
    var L1 = lum(cs.color), L2 = lum(fond(e));
    if (L1 === null || L2 === null) return;
    var c = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
    if (c < seuil) {
      defauts.push({ t: t.slice(0, 44), px: Math.round(px),
        c: Math.round(c * 100) / 100, seuil: seuil,
        couleur: cs.color, fond: fond(e) });
    }
  });
  return { mesures: mesures, ecartes: ecartes, defauts: defauts };
})()`;

const dodo = (ms) => new Promise((r) => setTimeout(r, ms));
const profil = path.join(os.tmpdir(), 'chr-ct-' + Date.now());
const chrome = spawn(CHROME, [
  '--headless=old', '--disable-gpu', '--no-sandbox',
  '--remote-debugging-port=' + PORT,
  '--user-data-dir=' + profil,
  '--window-size=1400,1000', 'about:blank',
], { stdio: 'ignore' });

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
  await cmd('Emulation.setDeviceMetricsOverride',
    { width: 1400, height: 1000, deviceScaleFactor: 1, mobile: false });

  let total = 0, pb = 0, surPhoto = 0;
  for (const p of PAGES) {
    await cmd('Page.navigate', { url: BASE + '/' + p });
    await dodo(1400);
    const r = await cmd('Runtime.evaluate',
      { expression: MESURE, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.text);
    const v = r.result.value;
    total += v.mesures;
    surPhoto += v.ecartes;
    pb += v.defauts.length;
    const nom = (p || 'index') + '.html';
    if (!v.defauts.length) {
      console.log('  %s ok    %d textes, %d sur photo',
        nom.padEnd(24), v.mesures, v.ecartes);
    } else {
      console.log('  %s %d defaut(s) sur %d', nom.padEnd(24), v.defauts.length, v.mesures);
      /* On groupe : vingt lignes qui disent la meme couleur ne valent qu'une
         correction, et une liste illisible ne se corrige pas. */
      const par = new Map();
      v.defauts.forEach((d) => {
        const k = d.couleur + ' sur ' + d.fond;
        const e = par.get(k) || { n: 0, pire: 99, ex: '' };
        e.n++;
        if (d.c < e.pire) { e.pire = d.c; e.ex = d.t; }
        par.set(k, e);
      });
      [...par.entries()].sort((a, b) => b[1].n - a[1].n).forEach(([k, e]) => {
        console.log('      %d\u00d7 %s \u2192 %s:1  \u00ab %s \u00bb', e.n, k, e.pire, e.ex);
      });
    }
  }
  console.log('\n%d textes mesures sur %d pages, %d defaut(s).',
    total, PAGES.length, pb);
  console.log('%d textes poses sur une photo : ecartes du verdict, a juger '
    + 'sur capture.', surPhoto);

  ws.close();
  chrome.kill();
  try { fs.rmSync(profil, { recursive: true, force: true }); } catch (e) { /* tant pis */ }
  process.exit(pb ? 1 : 0);
})().catch((e) => {
  console.error('echec :', e.message);
  chrome.kill();
  process.exit(1);
});
