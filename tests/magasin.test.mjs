// Le magasin (site/api/_magasin.js) : une modification ne peut plus en
// ecraser une autre.
//
// LE DEFAUT. Chaque enregistrement relisait le document entier puis le
// reecrivait. Deux enregistrements simultanes lisaient le meme etat ; le
// second effacait le premier. Les cas qui comptent :
//   - lomi confirme un paiement pendant que la reception enregistre une
//     modification : le paiement disparaissait, la retenue expirait, la
//     chambre se revendait alors que le client avait paye ;
//   - quelqu'un se connecte pendant qu'un administrateur desactive son
//     compte : la connexion reecrivait le compte encore actif.
//
// Lance depuis la racine du depot :  node tests/magasin.test.mjs
// En memoire par defaut ; contre une vraie base avec
//   DATABASE_URL=postgres://... node tests/magasin.test.mjs
import crypto from 'node:crypto';
import http from 'node:http';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

// ── Un faux lomi : il ouvre des sessions de paiement, rien d'autre ─────────
let n = 0;
const faux = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  if (req.method === 'POST') {
    const id = 'cs_' + (++n);
    return res.end(JSON.stringify({ id, checkout_url: 'http://127.0.0.1/payer/' + id, status: 'open' }));
  }
  res.end(JSON.stringify({ status: 'open' }));
});
await new Promise((ok) => faux.listen(0, '127.0.0.1', ok));

process.env.ADMIN_MDP = 'essai-du-magasin';
process.env.LOMI_SECRET_KEY = 'lomi_sk_test_essai';
process.env.LOMI_WEBHOOK_SECRET = 'whsec_essai';
process.env.LOMI_API_URL = 'http://127.0.0.1:' + faux.address().port;
delete process.env.BLOB_READ_WRITE_TOKEN;

const magasin = require('../site/api/_magasin.js');
const handler = (await import('../site/api/admin.js')).default;
const { POST: notifier } = await import('../site/api/lomi.mjs');

let ok = 0, ko = 0;
function verifie(nom, condition, detail) {
  if (condition) { ok++; console.log('  ok     ', nom); }
  else { ko++; console.log('  ECHEC  ', nom, detail === undefined ? '' : JSON.stringify(detail)); }
}

function appel(query, { methode = 'GET', body = null, cookie = '', ip = '10.1.0.1' } = {}) {
  const req = { method: methode, query, body, headers: { cookie, 'x-forwarded-for': ip } };
  const out = { entetes: {} };
  const res = {
    setHeader(k, v) { out.entetes[k] = v; },
    getHeader(k) { return out.entetes[k]; },
    status(c) { out.code = c; return res; },
    json(j) { out.json = j; return res; },
  };
  return Promise.resolve(handler(req, res)).then(() => out);
}
const cookieDe = (r) => String(r.entetes['Set-Cookie'] || '').split(';')[0];

console.log('\nLe magasin seul (' + (process.env.DATABASE_URL ? 'base Postgres' : 'memoire') + ')');
{
  const doc = magasin.document({ cle: 'essai-' + crypto.randomUUID(), prefixeBlob: 'essai/x', garde: 3,
    vide: () => ({ liste: [] }), jeton: '', nom: 'du document d essai' });
  // Vingt-cinq modifications lancees ensemble, chacune ajoute son element.
  const r = await Promise.all(Array.from({ length: 25 }, (_, i) =>
    doc.modifier((d) => { d.liste.push(i); })));
  const l = await doc.lire();
  verifie('25 modifications simultanees : toutes abouties', r.every((x) => x.ok), r.filter((x) => !x.ok));
  verifie('25 modifications simultanees : aucune perdue', l.d.liste.length === 25 && new Set(l.d.liste).size === 25, l.d.liste);

  const vieille = await doc.lire();
  await doc.modifier((d) => { d.liste.push('apres'); });
  const w = await doc.ecrire({ liste: ['par-dessus'] }, vieille.version);
  verifie('ecrire sur une lecture perimee : refuse (conflit)', w.conflit === true, w);
  verifie('...et rien n est ecrase', (await doc.lire()).d.liste.includes('apres'));

  const avant = await doc.lire();
  const a = await doc.modifier(() => ({ annuler: 'non' }));
  verifie('annuler : rien n est ecrit', a.annule && a.valeur === 'non' && (await doc.lire()).version === avant.version, a);

  if (process.env.DATABASE_URL) {
    const s = await doc.sauvegardes();
    verifie('base : 3 sauvegardes gardees, pas davantage', s === 3, s);
  }
}

// ── La connexion de secours, une chambre, puis un client qui paie ─────────
const entree = await appel({ a: 'entrer' }, { methode: 'POST', body: { mdp: 'essai-du-magasin' } });
const admin = cookieDe(entree);
verifie('connexion de secours', entree.code === 200, entree.json);

const jour = (dans) => new Date(Date.now() + dans * 864e5).toISOString().slice(0, 10);
const enregistrer = (type, e, cookie = admin) =>
  appel({ a: 'enregistrer' }, { methode: 'POST', body: { type, entree: e }, cookie });
const tout = async () => (await appel({ a: 'tout' }, { cookie: admin })).json.donnees;

console.log('\nDes enregistrements simultanes dans l administration');
{
  const r = await Promise.all(Array.from({ length: 12 }, (_, i) =>
    enregistrer('evenement', { titre: 'Soiree ' + i })));
  const titres = (await tout()).evenements.map((e) => e.titre);
  verifie('12 evenements crees ensemble : 12 enregistres', r.every((x) => x.code === 200) && titres.length === 12, titres);
}

console.log('\nlomi confirme un paiement pendant que la reception enregistre');
for (let essai = 0; essai < 4; essai++) {
  const numero = String(200 + essai);
  await enregistrer('chambre', { numero, categorie: 'suite-arabe' });
  // Une chambre par essai : les precedentes sont prises par leurs retenues.
  const du = jour(20 + essai * 5), au = jour(22 + essai * 5);
  const p = await appel({ a: 'payer' }, { methode: 'POST', ip: '10.2.0.' + essai, body: {
    prenom: 'Awa', nom: 'Kone', courriel: 'awa' + essai + '@exemple.ci', telephone: '0700000000',
    categorie: 'suite-arabe', du, au, pax: 2 } });
  verifie('essai ' + essai + ' : session de paiement ouverte', p.json && p.json.ok, p.json);
  if (!(p.json && p.json.ok)) continue;
  const reference = p.json.reference;

  // La reception a ouvert la retenue AVANT le paiement : son formulaire date.
  const perimee = (await tout()).fermetures.find((f) => f.paiement && f.paiement.reference === reference);
  const corps = JSON.stringify({ id: 'evt_' + essai, event: 'PAYMENT_SUCCEEDED', data: {
    id: 'txn_' + essai, amount: p.json.montant, checkout_session_id: 'x', metadata: { reference } } });
  const signature = crypto.createHmac('sha256', 'whsec_essai').update(corps).digest('hex');
  const webhook = () => notifier(new Request('http://localhost/api/lomi', { method: 'POST', body: corps,
    headers: { 'Content-Type': 'application/json', 'X-Lomi-Signature': signature } }));
  const reception = () => enregistrer('fermeture', { ...perimee, client: 'Awa Kone (chambre vue mer)' });

  // Les deux en meme temps, dans un ordre puis dans l'autre.
  const [w, r] = essai % 2 ? await Promise.all([reception(), webhook()]).then((x) => x.reverse())
    : await Promise.all([webhook(), reception()]);
  verifie('essai ' + essai + ' : la notification est acceptee', w.status === 200, w.status);
  verifie('essai ' + essai + ' : l enregistrement de la reception aussi', r.code === 200, r.json);
  const f = (await tout()).fermetures.find((x) => x.paiement && x.paiement.reference === reference);
  verifie('essai ' + essai + ' : le paiement est garde', f && f.paiement.statut === 'paye', f && f.paiement);
  verifie('essai ' + essai + ' : la reservation est confirmee et n expire plus',
    f && f.statut === 'confirmee' && f.expire === null, f && { statut: f.statut, expire: f.expire });
  verifie('essai ' + essai + ' : la modification de la reception est gardee aussi',
    f && f.client === 'Awa Kone (chambre vue mer)', f && f.client);

  // Le meme formulaire perime, renvoye APRES le paiement : il ne rouvre rien.
  await enregistrer('fermeture', { ...perimee, client: 'Awa Kone' });
  const g = (await tout()).fermetures.find((x) => x.paiement && x.paiement.reference === reference);
  verifie('essai ' + essai + ' : un formulaire perime ne rouvre pas une reservation payee',
    g && g.statut === 'confirmee' && g.expire === null && g.paiement.statut === 'paye', g && { statut: g.statut, expire: g.expire });
}

console.log('\nUne connexion pendant qu un administrateur desactive le compte');
{
  const cree = await appel({ a: 'compte' }, { methode: 'POST', cookie: admin,
    body: { nom: 'Yao Koffi', courriel: 'yao@exemple.ci', role: 'reception' } });
  verifie('compte cree', cree.code === 200, cree.json);
  const id = cree.json.compte.id, mdp = cree.json.provisoire;
  const [connexion, coupe] = await Promise.all([
    appel({ a: 'entrer' }, { methode: 'POST', body: { courriel: 'yao@exemple.ci', mdp } }),
    appel({ a: 'compte' }, { methode: 'POST', cookie: admin,
      body: { id, nom: 'Yao Koffi', role: 'reception', actif: false } }),
  ]);
  verifie('la desactivation aboutit', coupe.code === 200, coupe.json);
  const liste = (await appel({ a: 'comptes' }, { cookie: admin })).json.comptes;
  verifie('le compte reste desactive', liste.find((c) => c.id === id).actif === false, liste);
  const apres = connexion.code === 200
    ? await appel({ a: 'etat' }, { cookie: cookieDe(connexion) }) : { code: connexion.code };
  verifie('et la session ouverte au meme instant ne vaut rien', apres.code !== 200, apres.code);
}

faux.close();
console.log('\n  %d verifications, %d echec(s)\n', ok + ko, ko);
process.exit(ko ? 1 : 0);
