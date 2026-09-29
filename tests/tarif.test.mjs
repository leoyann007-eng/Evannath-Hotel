// Le montant encaisse (serveur, site/api/_tarif.js) contre le montant affiche
// (page, REMISE_JS de _chrome.py). Le client doit payer EXACTEMENT ce qu'il a
// lu : un franc d'ecart, et c'est une reclamation.
//
// La remise de la page n'est pas recopiee ici : on execute son vrai code,
// extrait de _chrome.py, comme tests/remise.test.mjs.
//
// Lance depuis la racine du depot :  node tests/tarif.test.mjs
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { devis, prixRemise, promotionDuJour, GRILLE } = require('../site/api/_tarif.js');

const SRC = (() => {
  const py = readFileSync('site/_chrome.py', 'utf8');
  const debut = py.indexOf('REMISE_JS = r"""');
  if (debut < 0) throw new Error('REMISE_JS introuvable dans _chrome.py');
  const apres = debut + 'REMISE_JS = r"""'.length;
  return py.slice(apres, py.indexOf('"""', apres));
})();

/** Le module de la page, nourri comme par /api/admin?a=public. */
function page(promotions) {
  const win = {};
  const faux = async () => ({ ok: true, json: async () => ({ promotions, evenements: [], campagnes: [] }) });
  new Function('window', 'fetch', SRC)(win, faux);
  return new Promise((ok) => win.EVN_REMISE.quand(ok));
}

let echecs = 0;
function verifier(nom, obtenu, attendu) {
  const ok = JSON.stringify(obtenu) === JSON.stringify(attendu);
  if (!ok) echecs++;
  console.log((ok ? '  ok   ' : '  ECHEC') + '  ' + nom
    + (ok ? '' : `\n         attendu ${JSON.stringify(attendu)}, obtenu ${JSON.stringify(obtenu)}`));
}

const CHAMBRES = Object.keys(GRILLE.chambres);
const cible = (toutes, chambres) => ({ toutes, chambres: chambres || [], services: [] });
const CAS = {
  'aucune promotion': [],
  'pourcentage, toutes': [{ id: 'a', remise: { type: 'pourcentage', valeur: 15 }, cible: cible(true), publie: true }],
  'pourcentage impair (arrondi)': [{ id: 'b', remise: { type: 'pourcentage', valeur: 7 }, cible: cible(true), publie: true }],
  'montant fixe, toutes': [{ id: 'c', remise: { type: 'montant', valeur: 12500 }, cible: cible(true), publie: true }],
  'montant plus grand que le prix': [{ id: 'd', remise: { type: 'montant', valeur: 90000 }, cible: cible(true), publie: true }],
  'cible partielle': [{ id: 'e', remise: { type: 'pourcentage', valeur: 20 }, cible: cible(false, ['suite-arabe', 'chambre-standard']), publie: true }],
  'valeur nulle': [{ id: 'f', remise: { type: 'pourcentage', valeur: 0 }, cible: cible(true), publie: true }],
  'deux promotions : la premiere seule': [
    { id: 'g', remise: { type: 'pourcentage', valeur: 10 }, cible: cible(true), publie: true },
    { id: 'h', remise: { type: 'montant', valeur: 40000 }, cible: cible(true), publie: true }],
};

console.log('\nLe prix par nuit : serveur contre page, chaque chambre, chaque forme de remise');
for (const [nom, promos] of Object.entries(CAS)) {
  const R = await page(promos);
  const cotePage = CHAMBRES.map((s) => R.prix(GRILLE.chambres[s].prix, s));
  const coteServeur = CHAMBRES.map((s) => prixRemise(GRILLE.chambres[s].prix, s, promotionDuJour(promos)));
  verifier(nom, coteServeur, cotePage);
}

console.log('\nLe choix de la promotion : ce que /api/admin?a=public laisse passer');
{
  const t = Date.parse('2026-10-10T12:00:00Z');
  const brouillon = { id: 'x', publie: false, remise: { type: 'pourcentage', valeur: 50 }, cible: cible(true) };
  const finie = { id: 'y', fin: '2026-10-01T00:00', remise: { type: 'pourcentage', valeur: 40 }, cible: cible(true) };
  const future = { id: 'z', debut: '2026-11-01T00:00', remise: { type: 'pourcentage', valeur: 30 }, cible: cible(true) };
  const bonne = { id: 'ok', debut: '2026-10-01T00:00', fin: '2026-10-31T23:59', remise: { type: 'pourcentage', valeur: 10 }, cible: cible(true) };
  verifier('ni brouillon, ni finie, ni future : la bonne', (promotionDuJour([brouillon, finie, future, bonne], t) || {}).id, 'ok');
  verifier('aucune en cours : aucune', promotionDuJour([brouillon, finie, future], t), null);
}

console.log('\nLe devis : la formule de la page (tarif x nuits + taxe x personnes x nuits, 30 %)');
{
  const t = Date.parse('2026-10-10T08:00:00Z');
  const d = devis({ categorie: 'chambre-standard', du: '2026-10-20', au: '2026-10-23', pax: 2 }, [], t);
  // 67 000 x 3 = 201 000 ; taxe 1 500 x 2 x 3 = 9 000 ; total 210 000 ; 30 % = 63 000
  verifier('Chambre Standard, 3 nuits, 2 personnes', [d.nuits, d.sejour, d.taxe, d.total, d.acompte], [3, 201000, 9000, 210000, 63000]);
  const r = devis({ categorie: 'suite-arabe', du: '2026-10-20', au: '2026-10-21', pax: 5 }, CAS['pourcentage impair (arrondi)'], t);
  // 280 000 x 0,93 = 260 400 ; taxe 7 500 ; total 267 900 ; 30 % = 80 370
  verifier('Suite Arabe remisee de 7 %, 1 nuit, 5 personnes', [r.tarif, r.total, r.acompte, r.promotion], [260400, 267900, 80370, 'b']);
}

console.log('\nLe devis refuse ce qu\'on ne peut pas vendre');
{
  const t = Date.parse('2026-10-10T08:00:00Z');
  const base = { categorie: 'chambre-standard', du: '2026-10-20', au: '2026-10-22', pax: 2 };
  verifier('categorie inconnue', devis({ ...base, categorie: 'penthouse' }, [], t).raison, 'categorie');
  verifier('depart avant l\'arrivee', devis({ ...base, au: '2026-10-19' }, [], t).raison, 'dates');
  verifier('zero nuit', devis({ ...base, au: '2026-10-20' }, [], t).raison, 'dates');
  verifier('date illisible', devis({ ...base, du: '20/10/2026' }, [], t).raison, 'dates');
  verifier('arrivee passee', devis({ ...base, du: '2026-10-01', au: '2026-10-03' }, [], t).raison, 'passe');
  verifier('plus de 30 nuits', devis({ ...base, au: '2026-12-01' }, [], t).raison, 'duree');
  verifier('trop de personnes pour la chambre', devis({ ...base, pax: 3 }, [], t).raison, 'personnes');
  verifier('personnes non entieres', devis({ ...base, pax: 1.5 }, [], t).raison, 'personnes');
  verifier('arrivee aujourd\'hui : acceptee', devis({ ...base, du: '2026-10-10', au: '2026-10-11' }, [], t).ok, true);
}

console.log('');
if (echecs) { console.error(echecs + ' test(s) en echec'); process.exit(1); }
console.log('Le serveur encaisse exactement ce que la page affiche.');
