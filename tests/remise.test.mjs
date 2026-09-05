// Tests de la logique de remise, hors navigateur.
//
// Le module vit dans _chrome.py, sous forme de source JavaScript : c'est lui
// qui part dans toutes les pages qui affichent un prix. On l'extrait et on
// l'execute ici, plutot que d'en recopier les regles — un test qui recopie la
// logique qu'il verifie ne verifie rien.
//
// Lance depuis la racine du depot :  node tests/remise.test.mjs
import { readFileSync } from 'node:fs';

const SRC = (() => {
  const py = readFileSync('site/_chrome.py', 'utf8');
  const debut = py.indexOf('REMISE_JS = r"""');
  if (debut < 0) throw new Error('REMISE_JS introuvable dans _chrome.py');
  const apres = debut + 'REMISE_JS = r"""'.length;
  const fin = py.indexOf('"""', apres);
  return py.slice(apres, fin);
})();

/** Charge le module avec une reponse d'API donnee. `null` simule une API muette. */
function charger(promotions) {
  const win = {};
  const faux = async () => (promotions === null
    ? { ok: false }
    : { ok: true, json: async () => ({ promotions, evenements: [], campagnes: [] }) });
  new Function('window', 'fetch', SRC)(win, faux);
  return new Promise((ok) => win.EVN_REMISE.quand(ok));
}

const PRIX = {
  'chambre-standard': 67000,
  'deluxe-baldaquin': 82000,
  'suite-anglaise': 107000,
  'suite-arabe': 280000,
};

function promo(remise, cible) {
  return [{
    id: 'p1', titre: 'Essai', remise,
    cible: cible || { toutes: true, chambres: [], services: [] },
    pastille: true, publie: true,
  }];
}

let echecs = 0;
/* toLocaleString separe les milliers par une espace insecable etroite. C'est
   un detail de format, pas un comportement : on compare a espaces egales. */
const esp = (v) => (typeof v === 'string' ? v.replace(/[   ]/g, ' ') : v);
function verifier(nom, obtenu, attendu) {
  obtenu = esp(obtenu); attendu = esp(attendu);
  const ok = JSON.stringify(obtenu) === JSON.stringify(attendu);
  if (!ok) echecs++;
  console.log((ok ? '  ok   ' : '  ECHEC') + '  ' + nom
    + (ok ? '' : `\n         attendu ${JSON.stringify(attendu)}, obtenu ${JSON.stringify(obtenu)}`));
}

/** Le prix de chaque chambre, apres remise. */
const tous = (R) => Object.fromEntries(
  Object.entries(PRIX).map(([s, p]) => [s, R.prix(p, s)]));

console.log('\nRemise en pourcentage, toutes les chambres');
{
  const R = await charger(promo({ type: 'pourcentage', valeur: 20 }));
  verifier('les quatre prix baissent de 20 %', tous(R), {
    'chambre-standard': 53600, 'deluxe-baldaquin': 65600,
    'suite-anglaise': 85600, 'suite-arabe': 224000,
  });
  verifier('l’etiquette dit le pourcentage', R.etiquette(), '−20 %');
  verifier('le titre est celui saisi', R.titre(), 'Essai');
}

console.log('\nRemise en montant fixe, toutes les chambres');
{
  const R = await charger(promo({ type: 'montant', valeur: 15000 }));
  verifier('chaque chambre perd 15 000 F, pas un pourcentage', tous(R), {
    'chambre-standard': 52000, 'deluxe-baldaquin': 67000,
    'suite-anglaise': 92000, 'suite-arabe': 265000,
  });
  verifier('l’etiquette dit le montant', R.etiquette(), '−15 000 F');
}

console.log('\nCiblage sur une seule chambre');
{
  const R = await charger(promo(
    { type: 'montant', valeur: 15000 },
    { toutes: false, chambres: ['suite-arabe'], services: [] }));
  verifier('seule la chambre visee baisse', tous(R), {
    'chambre-standard': 67000, 'deluxe-baldaquin': 82000,
    'suite-anglaise': 107000, 'suite-arabe': 265000,
  });
  verifier('pour() ne rend rien hors cible', R.pour('chambre-standard'), null);
  verifier('pour() rend la promotion sur la cible', !!R.pour('suite-arabe'), true);
}

console.log('\nRemises inapplicables — le garde-fou');
{
  const R = await charger(promo({ type: 'montant', valeur: 100000 }));
  verifier('sous 100 000 F le prix ne bouge pas, au-dessus si', tous(R), {
    'chambre-standard': 67000,   // 67 000 - 100 000 serait negatif
    'deluxe-baldaquin': 82000,   // idem
    'suite-anglaise': 7000,
    'suite-arabe': 180000,
  });
}
{
  const R = await charger(promo({ type: 'montant', valeur: 300000 }));
  verifier('une remise superieure a tous les prix ne change rien', tous(R), PRIX);
}
{
  const R = await charger(promo({ type: 'pourcentage', valeur: 100 }));
  verifier('cent pour cent ne met rien a zero', tous(R), PRIX);
}

console.log('\nAbsence de promotion, et repli');
{
  const R = await charger([]);
  verifier('aucune promotion : prix pleins', tous(R), PRIX);
  verifier('l’etiquette est vide', R.etiquette(), '');
  verifier('pour() ne rend rien', R.pour('chambre-standard'), null);
}
{
  const R = await charger(null);   // l'API ne repond pas
  verifier('API muette : prix pleins', tous(R), PRIX);
  verifier('aucune etiquette', R.etiquette(), '');
}
{
  const R = await charger(promo({ type: 'pourcentage', valeur: 0 }));
  verifier('remise nulle : prix pleins', tous(R), PRIX);
  verifier('aucune etiquette', R.etiquette(), '');
}

console.log('\nDeux promotions actives');
{
  const R = await charger([
    ...promo({ type: 'pourcentage', valeur: 20 }),
    { id: 'p2', titre: 'Seconde', remise: { type: 'montant', valeur: 50000 },
      cible: { toutes: true, chambres: [], services: [] }, pastille: true, publie: true },
  ]);
  verifier('la premiere s’applique, jamais les deux', R.prix(67000, 'chambre-standard'), 53600);
  verifier('le titre est celui de la premiere', R.titre(), 'Essai');
}

console.log('');
if (echecs) { console.error(echecs + ' test(s) en echec'); process.exit(1); }
console.log('Tous les tests de remise passent.');
