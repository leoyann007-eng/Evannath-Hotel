// Le plafond des retenues sans paiement (site/api/admin.js, plafondAtteint).
// Sans lui, de fausses demandes envoyees depuis quelques adresses retenaient
// tout l'hotel, et le site annoncait complet a chaque vrai client.
//
// Lance depuis la racine du depot :  node tests/retenues.test.mjs
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { plafondAtteint, RETENUES_PAR_IP } = require('../site/api/admin.js').surete;

let echecs = 0, total = 0;
function verifier(nom, obtenu, attendu) {
  total++;
  const ok = JSON.stringify(obtenu) === JSON.stringify(attendu);
  if (!ok) echecs++;
  console.log((ok ? '  ok   ' : '  ECHEC') + '  ' + nom
    + (ok ? '' : '\n         obtenu  ' + JSON.stringify(obtenu) + '\n         attendu ' + JSON.stringify(attendu)));
}

const MAINTENANT = Date.parse('2026-10-02T12:00:00Z');
const DANS_UNE_HEURE = '2026-10-02T13:00';
// 6 standard + 2 suites : 8 chambres, sous le seuil du plafond d'hotel (10).
const chambres = [
  ...Array.from({ length: 6 }, (_, i) => ({ id: 's' + i, categorie: 'standard' })),
  { id: 'a0', categorie: 'suite' }, { id: 'a1', categorie: 'suite' },
];
let n = 0;
const retenue = (cible, ip, debut = '2026-12-10', fin = '2026-12-11', autre = {}) => ({ id: 'f' + (++n), cible, ip, debut, fin,
  nature: 'client', statut: 'attente', expire: DANS_UNE_HEURE, ...autre });
const plafond = (fermetures, categorie, ip, du = '2026-12-10', au = '2026-12-12', ch = chambres) =>
  plafondAtteint({ chambres: ch, fermetures }, categorie, ip, MAINTENANT, du, au);

console.log('\nPar adresse');
verifier('libre au depart', plafond([], 'standard', 'ipA'), '');
verifier(RETENUES_PAR_IP + ' retenues en cours, a n importe quelles dates : limite',
  plafond([retenue('s0', 'ipA'), retenue('s1', 'ipA', '2027-01-01', '2027-01-02'), retenue('a0', 'ipA', '2027-03-01', '2027-03-02')], 'standard', 'ipA'), 'limite');
verifier('une autre adresse n est pas concernee',
  plafond([retenue('s0', 'ipA'), retenue('s1', 'ipA', '2027-01-01', '2027-01-02'), retenue('a0', 'ipA', '2027-03-01', '2027-03-02')], 'standard', 'ipB'), '');

console.log('\nPar categorie (des 4 chambres) : la moitie, sur les memes nuits');
const deux = [retenue('s0', 'x1'), retenue('s1', 'x2')];
verifier('2 retenues sur 6 standard : encore une', plafond(deux, 'standard', 'ipB'), '');
verifier('3 retenues sur 6 standard : saturation', plafond([...deux, retenue('s2', 'x3')], 'standard', 'ipB'), 'saturation');
verifier('les memes 3 retenues, mais pour d autres nuits : rien a voir',
  plafond([...deux, retenue('s2', 'x3')], 'standard', 'ipB', '2027-01-10', '2027-01-12'), '');
verifier('2 suites : petite categorie, les deux restent reservables', plafond([retenue('a0', 'x1')], 'suite', 'ipB'), '');

console.log('\nCe qui ne compte pas (2 retenues + une troisieme qui ne compte pas)');
verifier('une retenue payee', plafond([...deux, retenue('s2', 'x3', undefined, undefined, { paiement: { statut: 'paye' } })], 'standard', 'ipB'), '');
verifier('une retenue expiree', plafond([...deux, retenue('s2', 'x3', undefined, undefined, { expire: '2026-10-02T11:00' })], 'standard', 'ipB'), '');
verifier('un paiement refuse', plafond([...deux, retenue('s2', 'x3', undefined, undefined, { paiement: { statut: 'echoue' } })], 'standard', 'ipB'), '');
verifier('une reservation confirmee par la reception', plafond([...deux, retenue('s2', 'x3', undefined, undefined, { statut: 'confirmee', expire: '' })], 'standard', 'ipB'), '');

console.log('\nTout l hotel (des 10 chambres) : la moitie');
// 12 chambres en 4 categories de 3 : aucune n'atteint le seuil de categorie,
// seul le plafond d'hotel peut jouer.
const grand = Array.from({ length: 12 }, (_, i) => ({ id: 'g' + i, categorie: 'petite' + (i % 4) }));
const six = grand.slice(0, 6).map((c, i) => retenue(c.id, 'y' + i));
verifier('6 retenues sur 12 chambres : saturation partout', plafond(six, 'petite3', 'ipB', undefined, undefined, grand), 'saturation');
verifier('5 sur 12 : encore une', plafond(six.slice(1), 'petite3', 'ipB', undefined, undefined, grand), '');
verifier('8 chambres seulement : pas de plafond d hotel',
  plafond([retenue('s0', 'x1'), retenue('a0', 'x3'), retenue('a1', 'x4'), retenue('s1', 'x5')], 'suite', 'ipB'), '');

console.log('\n' + total + ' controles, ' + (total - echecs) + ' passes, ' + echecs + ' en echec');
process.exit(echecs ? 1 : 0);
