/* Mesure le contraste de CHAQUE texte du BACK-OFFICE, dans un vrai
 * navigateur.
 *
 *   node .outils/contraste-admin.js [http://localhost:5599]
 *
 * Pourquoi un second outil. Celui du site parcourt vingt et une pages
 * statiques : il suffit de les visiter. L'administration est UNE page qui
 * repeint son contenu en JavaScript, derriere un mot de passe, et dont
 * certaines couleurs ne s'affichent qu'une fois un tiroir ouvert. Une
 * conversion au creme mesuree seulement sur l'ecran d'accueil laisserait
 * sept vues et deux panneaux derriere.
 *
 * Il se connecte donc, clique les huit entrees du menu, ouvre le tiroir
 * d'une chambre et la fenetre de reservation, et mesure a chaque etape.
 *
 * Le mot de passe se lit dans .env.local, comme le fait le serveur local.
 * Il n'est jamais affiche.
 *
 * CE QU'IL NE VOIT PAS. Comme celui du site, il compare la couleur d'un
 * texte a la couleur de FOND composee. Il ne juge pas un texte pose sur une
 * photographie — la vignette d'un evenement, l'image d'une categorie — et
 * compte ces textes a part.
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

/* Le mot de passe local, lu comme le fait le serveur. Jamais journalise. */
function motDePasse() {
  if (process.env.ADMIN_MDP) return process.env.ADMIN_MDP;
  const f = path.join(__dirname, '..', '.env.local');
  if (!fs.existsSync(f)) return '';
  for (const l of fs.readFileSync(f, 'utf8').split(/\r?\n/)) {
    const i = l.indexOf('=');
    if (i > 0 && l.slice(0, i).trim() === 'ADMIN_MDP') return l.slice(i + 1).trim();
  }
  return '';
}

/* La mesure est celle du site, mot pour mot : meme composition des voiles,
   meme mise a l'ecart des textes sur photo, memes seuils. Deux mesures
   differentes donneraient deux verdicts, et l'un des deux serait faux. */
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
  /* Un fond a 6 % d'opacite n'est pas un fond : c'est une teinte posee sur
     ce qu'il y a dessous. On empile jusqu'a l'opacite, et on compose. */
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
const profil = path.join(os.tmpdir(), 'chr-adm-' + Date.now());

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

const mdp = motDePasse();
if (!mdp) {
  console.error("\n  ADMIN_MDP est introuvable. Definissez-le, ou mettez-le\n"
    + '  dans .env.local a cote du serveur local.\n');
  process.exit(2);
}

const chrome = spawn(CHROME, [
  '--headless=old', '--disable-gpu', '--no-sandbox',
  '--remote-debugging-port=' + PORT,
  '--user-data-dir=' + profil,
  '--window-size=1500,1000', 'about:blank',
], { stdio: 'ignore' });

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
  const evaluer = async (expr) => {
    const r = await cmd('Runtime.evaluate',
      { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.text
      + ' — ' + ((r.exceptionDetails.exception || {}).description || '').slice(0, 200));
    return r.result.value;
  };

  await cmd('Page.enable');
  await cmd('Emulation.setDeviceMetricsOverride',
    { width: 1500, height: 1000, deviceScaleFactor: 1, mobile: false });

  await cmd('Page.navigate', { url: BASE + '/admin/' });
  await dodo(1800);

  /* La connexion passe par la meme route que le formulaire. Le mot de passe
     traverse le pont de debogage, pas la console : il n'est pas journalise. */
  const entre = await evaluer(`(async () => {
    const r = await fetch('/api/admin?a=entrer', { method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ mdp: ${JSON.stringify(mdp)} }) });
    return r.ok;
  })()`);
  if (!entre) throw new Error('Le mot de passe a ete refuse.');
  await cmd('Page.navigate', { url: BASE + '/admin/' });
  await dodo(2200);

  const vues = await evaluer(
    "[...document.querySelectorAll('#menu button[data-v]')].map((b) => b.dataset.v)");
  if (!vues || !vues.length) throw new Error("Le menu est vide : la connexion n'a pas pris.");

  /* Les etapes : les huit vues, puis les deux panneaux qui portent leurs
     propres couleurs et qu'aucune visite de vue ne fait apparaitre. */
  const etapes = vues.map((v) => ({
    nom: v,
    aller: `(async () => { document.querySelector('#menu button[data-v="${v}"]').click();
      await new Promise((r) => setTimeout(r, 700)); return true; })()`,
  }));
  etapes.push({
    nom: 'disponibilites + tiroir',
    aller: `(async () => {
      document.querySelector('#menu button[data-v="disponibilites"]').click();
      await new Promise((r) => setTimeout(r, 700));
      const c = document.querySelector('#dsp-zone [data-dsp-ch]');
      if (!c) return 'absent';
      c.click();
      await new Promise((r) => setTimeout(r, 700));
      return !!document.querySelector('#dsp-tiroir');
    })()`,
  });
  etapes.push({
    nom: 'disponibilites + fenetre',
    aller: `(async () => {
      const x = document.querySelector('#dsp-tiroir .dsp-x');
      if (x) { x.click(); await new Promise((r) => setTimeout(r, 400)); }
      const b = document.querySelector('#dsp-resa-btn');
      if (!b) return 'absent';
      b.click();
      await new Promise((r) => setTimeout(r, 700));
      return true;
    })()`,
  });

  let total = 0, pb = 0, surPhoto = 0, absentes = [];
  for (const e of etapes) {
    const r = await evaluer(e.aller);
    if (r === 'absent') { absentes.push(e.nom); continue; }
    const v = await evaluer(MESURE);
    total += v.mesures;
    surPhoto += v.ecartes;
    pb += v.defauts.length;
    if (!v.defauts.length) {
      console.log('  %s ok    %d textes, %d sur photo',
        e.nom.padEnd(26), v.mesures, v.ecartes);
    } else {
      console.log('  %s %d defaut(s) sur %d', e.nom.padEnd(26), v.defauts.length, v.mesures);
      /* On groupe : vingt lignes qui disent la meme couleur ne valent qu'une
         correction, et une liste illisible ne se corrige pas. */
      const par = new Map();
      v.defauts.forEach((d) => {
        const k = d.couleur + ' sur ' + d.fond;
        const g = par.get(k) || { n: 0, pire: 99, ex: '' };
        g.n++;
        if (d.c < g.pire) { g.pire = d.c; g.ex = d.t; }
        par.set(k, g);
      });
      [...par.entries()].sort((a, b) => b[1].n - a[1].n).forEach(([k, g]) => {
        console.log('      %d\u00d7 %s \u2192 %s:1  \u00ab %s \u00bb', g.n, k, g.pire, g.ex);
      });
    }
  }
  console.log('\n%d textes mesures sur %d etapes, %d defaut(s).',
    total, etapes.length - absentes.length, pb);
  if (surPhoto) {
    console.log('%d textes poses sur une image : ecartes du verdict, a juger '
      + 'sur capture.', surPhoto);
  }
  /* Une etape sautee n'est PAS une etape reussie. Sans chambres saisies, le
     tiroir n'existe pas — et ses couleurs n'ont ete mesurees par personne. */
  if (absentes.length) {
    console.log('\n  %d etape(s) NON MESUREE(S) : %s', absentes.length, absentes.join(', '));
    console.log('  Semez des chambres (node .outils/semer-chambres.js) et relancez.');
  }

  ws.close();
  chrome.kill();
  try { fs.rmSync(profil, { recursive: true, force: true }); } catch (e) { /* tant pis */ }
  process.exit(pb || absentes.length ? 1 : 0);
})().catch((e) => {
  console.error('echec :', e.message);
  chrome.kill();
  try { fs.rmSync(profil, { recursive: true, force: true }); } catch (x) { /* tant pis */ }
  process.exit(1);
});
