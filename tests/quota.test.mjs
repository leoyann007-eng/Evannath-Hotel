// Le plafond du concierge (site/api/_quota.js, api/_chat.js).
//
// Chaque message coute quelques francs chez Anthropic. La limite par adresse
// arrete un visiteur trop pressé, pas un robot qui change d'adresse a chaque
// question : il faut aussi un plafond par jour, tous visiteurs confondus.
// Passe le plafond, la bulle disparait jusqu'au lendemain.
//
// Lance depuis la racine du depot :  node tests/quota.test.mjs
// (la partie api/_chat.js demande les dependances : cd site && npm install)
import { createRequire } from 'node:module';

process.env.CHAT_MAX_JOUR = '25';
process.env.ANTHROPIC_API_KEY = 'sk-ant-essai';      // jamais appele : on s'arrete avant
delete process.env.BLOB_READ_WRITE_TOKEN;

const require = createRequire(import.meta.url);
const quota = require('../site/api/_quota.js');

let ok = 0, ko = 0;
function verifie(nom, condition, detail) {
  if (condition) { ok++; console.log('  ok     ', nom); }
  else { ko++; console.log('  ECHEC  ', nom, detail === undefined ? '' : JSON.stringify(detail)); }
}

console.log('\nLe plafond lu dans CHAT_MAX_JOUR');
verifie('25 messages par jour', quota.PAR_JOUR === 25, quota.PAR_JOUR);

let chat = null;
try {
  require.resolve('@anthropic-ai/sdk', { paths: [new URL('../site/api/', import.meta.url).pathname] });
  chat = require('../site/api/_chat.js');
} catch (e) {
  console.log('\n  api/_chat.js : ignore, dependances absentes (cd site && npm install).');
}

if (chat) {
  const question = (texte) => ({ messages: [{ role: 'user', text: texte }], langue: 'fr', flux: false });
  console.log('\nLa limite par adresse : 20 questions par tranche de 10 minutes');
  const r = [];
  for (let i = 0; i < 21; i++) r.push(await chat.preparer(question('Bonjour ' + i), '10.9.0.1'));
  verifie('les 20 premieres passent', r.slice(0, 20).every((x) => !x.refus), r.find((x) => x.refus));
  verifie('la 21e est refusee (429)', r[20].refus && r[20].refus.code === 429 && r[20].refus.corps.raison === 'debit', r[20]);
  verifie('une autre adresse passe encore', !(await chat.preparer(question('Salut'), '10.9.0.2')).refus);
  verifie('un message vide ne compte pas', (await chat.preparer({ messages: [] }, '10.9.0.3')).refus.code === 422);

  console.log('\nLe plafond du jour, tous visiteurs confondus');
  verifie('21 messages comptes, pas le refus ni le message vide', (await quota.aujourdhui()) === 21, await quota.aujourdhui());
  const suite = [];
  for (let i = 0; i < 5; i++) suite.push(await chat.preparer(question('Encore ' + i), '10.9.1.' + i));
  verifie('jusqu a 25, ca passe', suite.slice(0, 4).every((x) => !x.refus), suite);
  verifie('le 26e est refuse, quelle que soit l adresse (503 quota)',
    suite[4].refus && suite[4].refus.code === 503 && suite[4].refus.corps.raison === 'quota', suite[4]);
  verifie('la bulle ne se montre plus', (await chat.etat()).actif === false, await chat.etat());
  verifie('Parametres le dit : plafond atteint', await quota.atteint(), await quota.aujourdhui());
}

console.log('\n  %d verifications, %d echec(s)\n', ok + ko, ko);
process.exit(ko ? 1 : 0);
