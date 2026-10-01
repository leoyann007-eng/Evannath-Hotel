// Les comptes de l'administration (site/api/_comptes.js) : qui a le droit de
// quoi, les mots de passe, les sessions et ce qui les coupe. Hors reseau : le
// module tourne en memoire, sans magasin Blob.
//
// Lance depuis la racine du depot :  node tests/comptes.test.mjs
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const comptes = require('../site/api/_comptes.js');
const { ROLES, droitRequis, peut, interne } = comptes;

let echecs = 0, total = 0;
function verifier(nom, obtenu, attendu) {
  total++;
  const ok = JSON.stringify(obtenu) === JSON.stringify(attendu);
  if (!ok) echecs++;
  console.log((ok ? '  ok   ' : '  ECHEC') + '  ' + nom
    + (ok ? '' : '\n         obtenu  ' + JSON.stringify(obtenu) + '\n         attendu ' + JSON.stringify(attendu)));
}

console.log('\nLa matrice des droits : chaque ecriture, chaque profil');
const ECRITURES = [
  ['enregistrer', 'fermeture'], ['supprimer', 'fermeture'],
  ['enregistrer', 'chambre'], ['chambres-serie'], ['chambres-lot'], ['supprimer', 'chambre'],
  ['enregistrer', 'evenement'], ['enregistrer', 'promotion'], ['enregistrer', 'campagne'],
  ['enregistrer', 'emploi'], ['televerser'], ['ordonner', 'evenement'],
  ['tarifs'], ['reglages'], ['comptes'], ['compte'], ['compte-reinitialiser'], ['compte-supprimer'], ['journal'],
];
const ATTENDU = {
  admin: ECRITURES.map(() => true),
  reception: ECRITURES.map(([a, t]) => ['fermeture', 'chambre'].includes(t) || a.startsWith('chambres-')),
  communication: ECRITURES.map(([a, t]) => ['evenement', 'promotion', 'campagne', 'emploi'].includes(t) || a === 'televerser'),
  lecture: ECRITURES.map(() => false),
};
for (const role of Object.keys(ROLES)) {
  verifier(ROLES[role].nom, ECRITURES.map(([a, t]) => peut(role, droitRequis(a, t))), ATTENDU[role]);
}
verifier('les lectures ne demandent aucun droit', ['etat', 'tout', 'mot-de-passe'].map((a) => droitRequis(a)), [null, null, null]);
verifier('un type inconnu tombe sur le contenu, pas sur rien', droitRequis('enregistrer', 'bizarre'), 'contenu');
verifier('un profil inconnu n a aucun droit', peut('patron', 'contenu'), false);
verifier('Mon compte est ouvert a tous', Object.values(ROLES).every((r) => r.vues.includes('compte')), true);
verifier('comptes et journal : administrateurs seulement',
  Object.entries(ROLES).filter(([, r]) => r.vues.includes('utilisateurs') || r.vues.includes('journal')).map(([k]) => k), ['admin']);

console.log('\nLes mots de passe');
const h = await interne.hacher('La lagune Aby au matin');
verifier('empreinte scrypt, jamais le mot de passe', [h.startsWith('scrypt$'), h.includes('lagune')], [true, false]);
verifier('le bon mot de passe passe', await interne.verifier('La lagune Aby au matin', h), true);
verifier('un autre ne passe pas', await interne.verifier('La lagune Aby au soir', h), false);
verifier('deux empreintes du meme mot de passe different (sel)', h !== await interne.hacher('La lagune Aby au matin'), true);
verifier('une empreinte abimee ne passe pas', await interne.verifier('x', 'md5$abc'), false);
const p = interne.provisoire();
verifier('provisoire : 3 groupes de 4, sans 0 O 1 l I', /^[a-km-zA-HJ-NP-Z2-9]{4}-[a-km-zA-HJ-NP-Z2-9]{4}-[a-km-zA-HJ-NP-Z2-9]{4}$/.test(p), true);
verifier('trop court refuse', !!interne.mdpRefuse('court'), true);
verifier('reprend l e-mail : refuse', !!interne.mdpRefuse('awa-et-la-lagune', { courriel: 'awa@hotel.ci' }), true);
verifier('une phrase passe', interne.mdpRefuse('La lagune Aby au matin', { courriel: 'awa@hotel.ci' }), '');

console.log('\nLe parcours, en memoire');
const C = comptes.creer({ jeton: '', secours: 'secours-de-test-123', secret: 'secret-de-test' });
const cookieDe = (r) => (r.cookie || '').split(';')[0];
const req = (cookie) => ({ headers: { cookie } });

let r = await C.entrer({ courriel: '', mdp: 'faux' });
verifier('secours : mauvais mot de passe', r.code, 401);
r = await C.entrer({ courriel: '', mdp: 'secours-de-test-123' });
verifier('secours : bon mot de passe', r.code, 200);
const sec = await C.session(req(cookieDe(r)));
verifier('la session de secours est administrateur', [sec.role, sec.secours], ['admin', true]);
verifier('cookie HttpOnly, Secure, SameSite=Strict', /HttpOnly/.test(r.cookie) && /Secure/.test(r.cookie) && /SameSite=Strict/.test(r.cookie), true);

r = await C.enregistrer(sec, { nom: 'Awa', courriel: 'Awa@Hotel.ci', role: 'reception' });
verifier('creation : provisoire rendu une fois, e-mail en minuscules', [r.code, !!r.corps.provisoire, r.corps.compte.courriel], [200, true, 'awa@hotel.ci']);
const awa = r.corps.compte, prov = r.corps.provisoire;
r = await C.enregistrer(sec, { nom: 'Bis', courriel: 'awa@hotel.ci', role: 'lecture' });
verifier('meme adresse : refusee', r.code, 409);

r = await C.entrer({ courriel: 'awa@hotel.ci', mdp: prov });
let sa = await C.session(req(cookieDe(r)));
verifier('connexion au provisoire : session provisoire', [sa.role, sa.provisoire], ['reception', true]);
r = await C.changerMdp(sa, { ancien: prov, nouveau: 'Le comptoir du matin' });
verifier('premier mot de passe choisi', r.code, 200);
const cookieAwa = cookieDe(r);
sa = await C.session(req(cookieAwa));
verifier('la nouvelle session n est plus provisoire', sa.provisoire, false);

r = await C.enregistrer(sec, { id: awa.id, nom: 'Awa', role: 'communication', actif: true });
verifier('changement de profil', r.corps.compte.role, 'communication');
verifier('… coupe la session ouverte', (await C.session(req(cookieAwa))).erreur, 401);

r = await C.entrer({ courriel: 'awa@hotel.ci', mdp: 'Le comptoir du matin' });
const cookieAwa2 = cookieDe(r);
r = await C.reinitialiser(sec, awa.id);
verifier('reinitialisation : nouveau provisoire', [r.code, r.corps.compte.provisoire], [200, true]);
verifier('… coupe la session ouverte', (await C.session(req(cookieAwa2))).erreur, 401);
verifier('… et l ancien mot de passe ne vaut plus', (await C.entrer({ courriel: 'awa@hotel.ci', mdp: 'Le comptoir du matin' })).code, 401);

r = await C.enregistrer(sec, { nom: 'Directrice', courriel: 'dir@hotel.ci', role: 'admin' });
const dir = r.corps.compte;
r = await C.enregistrer(sec, { id: dir.id, nom: 'Directrice', role: 'lecture', actif: true });
verifier('le dernier administrateur ne se retrograde pas', r.code, 409);
r = await C.supprimer(sec, dir.id);
verifier('ni ne se supprime', r.code, 409);
r = await C.enregistrer({ ...sec, id: dir.id }, { id: dir.id, nom: 'Directrice', role: 'admin', actif: false });
verifier('on ne se desactive pas soi-meme', r.code, 409);
r = await C.enregistrer(sec, { id: awa.id, nom: 'Awa', role: 'communication', actif: false });
verifier('desactivation', r.corps.compte.actif, false);
r = await C.entrer({ courriel: 'awa@hotel.ci', mdp: 'nimporte' });
verifier('desactive + mauvais mot de passe : rien n est revele', r.code, 401);

for (let i = 0; i < 5; i++) await C.entrer({ courriel: 'dir@hotel.ci', mdp: 'faux' + i });
r = await C.entrer({ courriel: 'dir@hotel.ci', mdp: 'faux' });
verifier('cinq echecs : l adresse se ferme', r.code, 429);

const forge = Buffer.from(JSON.stringify({ u: dir.id, v: 1, e: 9e9 })).toString('base64url') + '.faux';
verifier('un cookie forge ne vaut rien', (await C.session(req('evn_adm=' + forge))).erreur, 401);

const j = await C.journal();
verifier('le journal garde les gestes', ['Connexion par l’accès de secours', 'A créé le compte de Awa (Réception)',
  'A changé son mot de passe', 'A réinitialisé le mot de passe de Awa'].every((x) => j.some((l) => l.x === x)), true);

console.log('\n' + total + ' controles, ' + (total - echecs) + ' passes, ' + echecs + ' en echec');
process.exit(echecs ? 1 : 0);
