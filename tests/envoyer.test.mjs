// Tests de la fonction /api/envoyer, hors Vercel : on simule req et res.
// Lance depuis la racine du depot :  node tests/envoyer.test.mjs
import handler from '../site/api/envoyer.js';

function faux(body, methode = 'POST', ip = '1.2.3.4') {
  const req = { method: methode, body, headers: { 'x-forwarded-for': ip } };
  let out = {};
  const res = {
    statusCode: 0,
    setHeader() {},
    status(c) { out.code = c; return res; },
    json(j) { out.json = j; return res; },
  };
  return handler(req, res).then(() => out);
}

const base = { duree: 9999, website: '' };
let ok = 0, ko = 0;
function verifie(nom, condition, detail) {
  if (condition) { ok++; console.log('  ok    ', nom); }
  else { ko++; console.log('  ECHEC ', nom, detail === undefined ? '' : JSON.stringify(detail)); }
}

const t = [];

t.push(async () => {
  const r = await faux(null, 'GET');
  verifie('GET refuse (405)', r.code === 405, r);
});

t.push(async () => {
  const r = await faux({ ...base, type: 'inconnu' }, 'POST', '2.0.0.1');
  verifie('type inconnu refuse (400)', r.code === 400, r);
});

t.push(async () => {
  const r = await faux('pas du json', 'POST', '2.0.0.2');
  verifie('corps illisible refuse (400)', r.code === 400, r);
});

t.push(async () => {
  const r = await faux({ ...base, type: 'contact' }, 'POST', '2.0.0.3');
  verifie('champs requis manquants (422)', r.code === 422 && r.json.champs.length === 3, r.json);
});

t.push(async () => {
  const r = await faux({ ...base, type: 'contact', nom: 'Aya', email: 'pasunemail', message: 'bonjour tout le monde' }, 'POST', '2.0.0.4');
  verifie('e-mail invalide refuse (422)', r.code === 422 && r.json.champs[0] === 'email', r.json);
});

t.push(async () => {
  const r = await faux({ ...base, type: 'table', nom: 'Aya', tel: '123' }, 'POST', '2.0.0.5');
  verifie('telephone trop court refuse (422)', r.code === 422 && r.json.champs[0] === 'tel', r.json);
});

t.push(async () => {
  const r = await faux({ ...base, type: 'contact', website: 'robot', nom: 'x', email: 'a@b.co', message: 'y' }, 'POST', '2.0.0.6');
  verifie('piege a robots : reponse 200 muette', r.code === 200 && r.json.ok === true, r.json);
});

t.push(async () => {
  const r = await faux({ type: 'contact', duree: 100, nom: 'Aya', email: 'a@b.co', message: 'bonjour' }, 'POST', '2.0.0.7');
  verifie('remplissage trop rapide : 200 muet', r.code === 200, r.json);
});

t.push(async () => {
  const r = await faux({ ...base, type: 'contact', nom: 'Aya Kouassi', email: 'aya@example.ci', message: 'Bonjour, une question.' }, 'POST', '2.0.0.8');
  verifie('sans cle API : 503 non configure', r.code === 503 && r.json.configure === false, r.json);
  verifie('une reference est tout de meme rendue', /^EVN-[A-Z0-9]{6}$/.test(r.json.reference || ''), r.json);
});

t.push(async () => {
  const ip = '3.3.3.3';
  let dernier;
  for (let i = 0; i < 22; i++) {
    dernier = await faux({ ...base, type: 'contact', nom: 'A', email: 'a@b.co', message: 'x' }, 'POST', ip);
  }
  verifie('limitation de debit apres 20 envois (429)', dernier.code === 429, dernier);
});

t.push(async () => {
  const long = 'x'.repeat(9000);
  const r = await faux({ ...base, type: 'contact', nom: long, email: 'a@b.co', message: long }, 'POST', '4.4.4.4');
  verifie('champs surdimensionnes acceptes apres troncature', r.code === 503, r.json);
});

for (const f of t) await f();
console.log(`\n${ok} verifications passees, ${ko} en echec`);
process.exit(ko ? 1 : 0);
