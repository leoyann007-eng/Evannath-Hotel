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

// ── Avec un faux Resend : la reception, puis l'accuse de reception ────────
// fetch est remplace : chaque appel est garde, et `refuser` fait echouer
// les envois vers une adresse donnee.
const envois = [];
let refuser = null;
function brancher() {
  process.env.RESEND_API_KEY = 're_essai';
  process.env.MAIL_DEST = 'reception@evannathhotel.com';
  process.env.MAIL_EXP = 'site@evannathhotel.com';
  globalThis.fetch = async (url, o) => {
    const corps = JSON.parse(o.body);
    envois.push(corps);
    const ko = refuser && corps.to.includes(refuser);
    return { ok: !ko, text: async () => (ko ? 'refuse' : '') };
  };
}
const versClient = (adr) => envois.filter((e) => e.to.length === 1 && e.to[0] === adr);

t.push(async () => {
  brancher(); envois.length = 0;
  const r = await faux({ ...base, type: 'reservation', nom: 'Aya <b>Kouassi</b>', email: 'aya@example.ci',
    tel: '0102030405', chambre: 'Suite Arabe', arrivee: '12 décembre 2026', depart: '14 décembre 2026',
    message: 'Achetez mes produits sur http://spam.example' }, 'POST', '5.0.0.1');
  const c = versClient('aya@example.ci')[0];
  verifie('reservation : 200, accuse envoye', r.code === 200 && r.json.accuse === 'envoye', r.json);
  verifie('deux e-mails : la reception, puis le client', envois.length === 2
    && envois[0].to[0] === 'reception@evannathhotel.com' && !!c, envois.map((e) => e.to));
  verifie('l objet du client porte la reference', c && c.subject.includes(r.json.reference), c && c.subject);
  verifie('le recapitulatif reprend la chambre et les dates', c && c.html.includes('Suite Arabe')
    && c.html.includes('12 décembre 2026'), c && c.html);
  verifie('il dit que ce n est pas encore une confirmation', c && c.html.includes('pas encore une confirmation'));
  verifie('le message libre n est pas recopie au client', c && !c.html.includes('spam.example'));
  verifie('le nom est echappe', c && c.html.includes('Aya &lt;b&gt;Kouassi&lt;/b&gt;') && !c.html.includes('<b>Kouassi'));
  verifie('repondre au client ecrit a la reception', c && c.reply_to === 'reception@evannathhotel.com', c && c.reply_to);
});

t.push(async () => {
  envois.length = 0;
  const r = await faux({ ...base, type: 'devis', langue: 'en', societe: 'Orange CI', nom: 'Jane Doe',
    email: 'jane@example.com', tel: '0102030405', evenement: 'Mariage', chambres: '12', participants: '80' }, 'POST', '5.0.0.2');
  const c = versClient('jane@example.com')[0];
  verifie('anglais : objet et texte en anglais', c && c.subject.startsWith('Your quote request')
    && c.html.includes('Type of event'), c && c.subject);
  verifie('le type d evenement arrive a la reception (et pas « devis »)', r.code === 200
    && envois[0].html.includes('Mariage') && envois[0].html.includes('Chambres souhaitées'), envois[0] && envois[0].html);
});

t.push(async () => {
  envois.length = 0;
  const r = await faux({ ...base, type: 'table', nom: 'Koffi', tel: '0102030405', couverts: '4' }, 'POST', '5.0.0.3');
  verifie('sans adresse : seul l e-mail de la reception part', r.code === 200 && envois.length === 1
    && r.json.accuse === 'sans-adresse', { n: envois.length, j: r.json });
});

t.push(async () => {
  envois.length = 0; refuser = 'rate@example.ci';
  const r = await faux({ ...base, type: 'contact', nom: 'Awa', email: 'rate@example.ci', message: 'Bonjour' }, 'POST', '5.0.0.4');
  refuser = null;
  verifie('accuse refuse : la demande reste acceptee (200), accuse = echec',
    r.code === 200 && r.json.ok && r.json.accuse === 'echec', r.json);
});

for (const f of t) await f();
console.log(`\n${ok} verifications passees, ${ko} en echec`);
process.exit(ko ? 1 : 0);
