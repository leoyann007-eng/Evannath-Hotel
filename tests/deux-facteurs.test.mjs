// La double authentification, de bout en bout, par la fonction elle-meme.
// Lance depuis la racine du depot :  node tests/deux-facteurs.test.mjs
//
// CE QUI SE JOUE ICI. La double authentification est obligatoire pour tous
// les comptes. Cinq choses ne doivent jamais arriver :
//
//   1. UN MOT DE PASSE QUI SUFFIT. Avec la double authentification
//      activee, le mot de passe seul n'ouvre aucune session.
//   2. UN COMPTE QUI L'EVITE. Tant qu'elle n'est pas activee, la session
//      n'ouvre que l'ecran qui l'active.
//   3. UN CODE QUI SERT DEUX FOIS. Ni un code de l'application (rejeu), ni
//      un code de secours.
//   4. DES ESSAIS SANS FIN. Cinq codes faux ferment le compte un quart
//      d'heure.
//   5. UNE SESSION DETOURNEE QUI CHANGE DE TELEPHONE. Remplacer le secret
//      demande le code actuel.

import { createRequire } from 'node:module';

process.env.ADMIN_MDP = 'essai';
delete process.env.BLOB_READ_WRITE_TOKEN;

const require = createRequire(import.meta.url);
const handler = (await import('../site/api/admin.js')).default;
const { interne } = require('../site/api/_comptes.js');

const UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1';
function appel(query, { methode = 'GET', body = null, cookie = '', origine, ip = '41.202.1.10' } = {}) {
  const headers = { host: 'evannath.test', 'user-agent': UA, 'x-forwarded-for': ip };
  if (cookie) headers.cookie = cookie;
  if (origine) headers.origin = origine;
  const req = { method: methode, query, body, headers };
  const out = { entetes: {} };
  const res = {
    statusCode: 0,
    setHeader(k, v) { out.entetes[k] = v; },
    getHeader(k) { return out.entetes[k]; },
    status(c) { out.code = c; return res; },
    json(j) { out.json = j; return res; },
    send(t) { out.texte = String(t); return res; },
  };
  return Promise.resolve(handler(req, res)).then(() => {
    out.cookie = String(out.entetes['Set-Cookie'] || '').split(';')[0];
    return out;
  });
}
const post = (a, body, o) => appel({ a }, { methode: 'POST', body, ...o });

let ok = 0, ko = 0;
function verifie(nom, condition, detail) {
  if (condition) { ok++; console.log('  ok     ', nom); }
  else { ko++; console.log('  ECHEC  ', nom, detail === undefined ? '' : JSON.stringify(detail).slice(0, 400)); }
}
const codeDe = (secret, decalage = 0) => interne.codeTotp(secret, Math.floor(Date.now() / 30000) + decalage);

// ── L'acces de secours cree un compte ──────────────────────────────────────
const secours = (await post('entrer', { mdp: 'essai' })).cookie;
let r = await post('compte', { nom: 'Awa K.', courriel: 'awa@agence.ci', role: 'communication' }, { cookie: secours });
const awa = r.json.compte, provisoire = r.json.provisoire;
verifie('compte cree, sans double authentification', r.code === 200 && awa.mfa === false, r.json);

// ── Une ecriture d'une autre origine ───────────────────────────────────────
r = await post('compte', { nom: 'Pirate', courriel: 'x@x.ci', role: 'admin' }, { cookie: secours, origine: 'https://ailleurs.example' });
verifie('une ecriture venue d un autre site est refusee (403)', r.code === 403, r.json);
r = await post('compte', { nom: 'Bis', courriel: 'bis@agence.ci', role: 'lecture' }, { cookie: secours, origine: 'https://evannath.test' });
verifie('la meme, depuis le site : acceptee', r.code === 200, r.json);

// ── Premiere connexion : mot de passe, puis double authentification ─────────
r = await post('entrer', { courriel: 'awa@agence.ci', mdp: provisoire });
let c = r.cookie;
r = await post('mot-de-passe', { ancien: provisoire, nouveau: 'La paillote au matin' }, { cookie: c });
c = r.cookie;
verifie('mot de passe personnel choisi', r.code === 200 && !!c, r.json);
r = await appel({ a: 'etat' }, { cookie: c });
verifie('l etat dit : double authentification a faire', r.json.moi && r.json.moi.mfaAFaire === true, r.json.moi);
r = await appel({ a: 'tout' }, { cookie: c });
verifie('sans elle, rien d autre ne s ouvre (403)', r.code === 403 && r.json.mfa === true, r.json);
r = await post('enregistrer', { type: 'evenement', entree: { titre: 'x' } }, { cookie: c });
verifie('… ni ne s ecrit', r.code === 403 && r.json.mfa === true, r.json);

r = await post('2fa-preparer', {}, { cookie: c });
const secret = r.json.secret;
verifie('le secret et son QR code (otpauth)', r.code === 200 && /^[A-Z2-7]{32}$/.test(secret)
  && r.json.uri.startsWith('otpauth://totp/') && r.json.uri.includes('secret=' + secret), r.json);
r = await post('2fa-activer', { code: '000000' }, { cookie: c });
verifie('un code faux n active rien', r.code === 422, r.json);
r = await post('2fa-activer', { code: codeDe(secret) }, { cookie: c });
const codeActivation = codeDe(secret);
const codes = r.json.codes || [];
verifie('le bon code active, et rend dix codes de secours', r.code === 200 && codes.length === 10
  && codes.every((x) => /^[A-Z2-9]{4}-[A-Z2-9]{4}$/.test(x)), r.json);
const cAvant = c;
c = r.cookie;
verifie('l ancienne session tombe, la nouvelle s ouvre', (await appel({ a: 'tout' }, { cookie: cAvant })).code === 401
  && (await appel({ a: 'tout' }, { cookie: c })).code === 200, '');

// ── Se reconnecter : le mot de passe ne suffit plus ────────────────────────
r = await post('entrer', { courriel: 'awa@agence.ci', mdp: 'La paillote au matin' });
let defi = r.json.defi;
verifie('le mot de passe seul : aucune session, une seconde etape', r.code === 200 && r.json.etape === 'code'
  && !r.cookie && !!defi, { code: r.code, json: r.json, cookie: r.cookie });
r = await post('entrer-code', { defi: defi + 'x', code: codeDe(secret) });
verifie('un defi falsifie ne vaut rien', r.code === 401 && !r.cookie, r.json);
r = await post('entrer-code', { defi, code: '123456' });
verifie('un code faux : refuse', r.code === 401 && !r.cookie, r.json);
// Le code de l'activation vient de servir : on prend celui des 30 secondes
// suivantes, que le serveur accepte d'avance (decalage d'horloge).
const code1 = codeDe(secret, 1);
r = await post('entrer-code', { defi, code: code1 });
verifie('le bon code : la session s ouvre', r.code === 200 && r.cookie.startsWith('evn_adm='), r.json);
r = await post('entrer', { courriel: 'awa@agence.ci', mdp: 'La paillote au matin' });
r = await post('entrer-code', { defi: r.json.defi, code: code1 });
verifie('le meme code ne sert pas deux fois (rejeu)', r.code === 401 && !r.cookie, r.json);
r = await post('entrer', { courriel: 'awa@agence.ci', mdp: 'La paillote au matin' });
r = await post('entrer-code', { defi: r.json.defi, code: codeActivation });
verifie('ni celui de l activation', r.code === 401 && !r.cookie, r.json);

// ── Les codes de secours ───────────────────────────────────────────────────
r = await post('entrer', { courriel: 'awa@agence.ci', mdp: 'La paillote au matin' });
defi = r.json.defi;
r = await post('entrer-code', { defi, code: codes[0].toLowerCase().replace('-', ' '), secours: true });
verifie('un code de secours ouvre une session (casse et tiret indifferents)', r.code === 200 && !!r.cookie
  && r.json.codesRestants === 9, r.json);
r = await post('entrer', { courriel: 'awa@agence.ci', mdp: 'La paillote au matin' });
r = await post('entrer-code', { defi: r.json.defi, code: codes[0], secours: true });
verifie('… une seule fois', r.code === 401, r.json);

// ── Cinq erreurs ferment le compte ─────────────────────────────────────────
r = await post('entrer', { courriel: 'awa@agence.ci', mdp: 'La paillote au matin' });
defi = r.json.defi;
for (let i = 0; i < 4; i++) await post('entrer-code', { defi, code: '00000' + i });
r = await post('entrer-code', { defi, code: codeDe(secret, 1) });
verifie('apres cinq codes faux, meme le bon est refuse (429)', r.code === 429, r.json);

// ── Changer de telephone, renouveler les codes ─────────────────────────────
c = (await post('entrer', { mdp: 'essai' })).cookie; // la suite se fait depuis l'acces de secours…
r = await post('compte-2fa', { id: awa.id }, { cookie: c });
verifie('un administrateur remet a zero la double authentification', r.code === 200 && r.json.compte.mfa === false, r.json);
r = await post('entrer', { courriel: 'awa@agence.ci', mdp: 'La paillote au matin' });
verifie('… le compte revient a l ecran d activation', r.code === 200 && !r.json.etape && !!r.cookie, r.json);
let ca = r.cookie;
r = await post('2fa-preparer', {}, { cookie: ca });
const secret2 = r.json.secret;
r = await post('2fa-activer', { code: codeDe(secret2) }, { cookie: ca });
ca = r.cookie;
verifie('… et se reactive avec un nouveau telephone', r.code === 200, r.json);
r = await post('2fa-preparer', {}, { cookie: ca });
verifie('changer de telephone sans le code actuel : refuse', r.code === 422, r.json);
r = await post('2fa-codes', { code: '999999' }, { cookie: ca });
verifie('renouveler les codes sans le bon code : refuse', r.code === 422, r.json);

// ── Les autres appareils, le journal ───────────────────────────────────────
r = await post('sessions-fermer', {}, { cookie: ca });
const caNeuf = r.cookie;
verifie('deconnecter les autres appareils : celui-ci reste ouvert', r.code === 200
  && (await appel({ a: 'tout' }, { cookie: caNeuf })).code === 200
  && (await appel({ a: 'tout' }, { cookie: ca })).code === 401, r.json);
r = await appel({ a: 'mes-connexions' }, { cookie: caNeuf });
verifie('« Mon compte » voit ses connexions, avec l appareil', r.code === 200
  && r.json.connexions.some((x) => /Connexion.*Safari sur iPhone/.test(x.x)), r.json.connexions);
await post('entrer', { courriel: 'awa@agence.ci', mdp: 'mauvais mot de passe' }, { ip: '102.67.3.3' });
r = await appel({ a: 'journal' }, { cookie: c });
const echecJ = (r.json.journal || []).find((x) => /Échec de connexion/.test(x.x));
verifie('un echec sur un compte existant va au journal, avec l adresse IP', !!echecJ && echecJ.ip === '102.67.3.3', echecJ);

// ── L'acces de secours, reserve au developpeur ─────────────────────────────
r = await appel({ a: 'tout' }, { cookie: c });
verifie('l acces de secours n est pas bloque par la double authentification', r.code === 200, r.json);
r = await post('2fa-preparer', {}, { cookie: c });
verifie('… et n en a pas', r.code === 403, r.json);

console.log(`\n${ok} verifications passees, ${ko} en echec`);
process.exit(ko ? 1 : 0);
