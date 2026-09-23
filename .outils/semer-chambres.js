/* Remplit le magasin LOCAL de chambres d'essai, pour pouvoir eprouver
 * l'ecran Disponibilites sans saisir quarante-six chambres a la main.
 *
 *   node .outils/semer-chambres.js
 *   node .outils/semer-chambres.js --vider
 *
 * ────────────────────────────────────────────────────────────────────────
 * CES NUMEROS SONT INVENTES. L'hotel ne nous a pas donne les siens.
 *
 * Le total — 46 — est le seul chiffre vrai ici : c'est ce que le site
 * annonce publiquement. La repartition entre les sept categories, elle, est
 * une supposition : personne ne nous a dit combien il y a de Suites Arabes.
 * Ces donnees servent a voir l'ecran vivre, jamais a decider quoi que ce
 * soit.
 * ────────────────────────────────────────────────────────────────────────
 *
 * LE GARDE-FOU : ce script REFUSE toute cible autre que localhost. Ecrire
 * ces chambres dans la production, dont le stockage est durable, obligerait
 * a les retirer une par une — et on ne saurait plus lesquelles sont vraies.
 */
const BASE = process.env.BASE || 'http://localhost:5599';

if (!/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(BASE)) {
  console.error('\n  Refus : ' + BASE + " n'est pas un serveur local.\n"
    + "  Ce script ne sert qu'a garnir une memoire de demonstration.\n"
    + "  Les vraies chambres se saisissent dans l'administration.\n");
  process.exit(1);
}

/* Le mot de passe local, lu dans .env.local comme le fait le serveur. */
const fs = require('fs');
const path = require('path');
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

/* La repartition. Elle est INVENTEE — voir l'avertissement en tete. Les
   numeros suivent l'usage le plus courant : centaine = etage. */
const PLAN = [
  ['chambre-standard', 1, 101, 16],
  ['deluxe-baldaquin', 1, 121, 8],
  ['deluxe-superieure', 2, 201, 8],
  ['suite-anglaise', 2, 221, 6],
  ['chambre-mezzanine', 3, 301, 4],
  ['mezzanine-superieure', 3, 311, 2],
  ['suite-arabe', 3, 321, 2],
];

let COOKIE = '';
async function appel(action, corps) {
  const o = { method: corps ? 'POST' : 'GET', headers: {} };
  if (corps) { o.headers['Content-Type'] = 'application/json'; o.body = JSON.stringify(corps); }
  if (COOKIE) o.headers.cookie = COOKIE;
  const r = await fetch(BASE + '/api/admin?a=' + action, o);
  const s = r.headers.get('set-cookie');
  if (s) COOKIE = s.split(';')[0];
  return { code: r.status, ...(await r.json().catch(() => ({}))) };
}

const jour = (n) => {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return new Date(d.getTime() - d.getTimezoneOffset() * 6e4).toISOString().slice(0, 10);
};

(async () => {
  const mdp = motDePasse();
  if (!mdp) {
    console.error("\n  ADMIN_MDP est introuvable. Definissez-le, ou mettez-le dans"
      + ' .env.local.\n');
    process.exit(1);
  }
  const e = await appel('entrer', { mdp });
  if (!e.ok) { console.error('\n  Connexion refusee : ' + (e.message || e.code) + '\n'); process.exit(1); }

  const avant = await appel('tout');
  const existantes = (avant.donnees && avant.donnees.chambres) || [];

  if (process.argv.includes('--vider')) {
    for (const c of existantes) await appel('supprimer', { type: 'chambre', id: c.id });
    for (const f of (avant.donnees && avant.donnees.fermetures) || []) {
      await appel('supprimer', { type: 'fermeture', id: f.id });
    }
    console.log('\n  %d chambre(s) et %d fermeture(s) retirees.\n',
      existantes.length, ((avant.donnees && avant.donnees.fermetures) || []).length);
    return;
  }

  if (existantes.length) {
    console.log('\n  %d chambre(s) deja saisie(s). Relancez avec --vider pour repartir'
      + ' de zero.\n', existantes.length);
    return;
  }

  const ids = {};
  let n = 0;
  for (const [slug, etage, debut, combien] of PLAN) {
    for (let i = 0; i < combien; i++) {
      const numero = String(debut + i);
      const r = await appel('enregistrer', {
        type: 'chambre', entree: { numero, categorie: slug, etage: String(etage) } });
      if (!r.ok) { console.error('  echec sur %s : %s', numero, r.message); continue; }
      ids[numero] = r.entree.id;
      n++;
    }
  }

  /* De quoi voir les cinq etats a l'ecran, et pas seulement du vert. */
  const POSES = [
    ['101', jour(-1), jour(1), 'client', 'M. Koné', 'confirmee'],
    ['102', jour(-1), jour(1), 'client', 'M. Koné', 'confirmee'],
    ['103', jour(2), jour(5), 'client', 'Mme Traoré', 'attente'],
    ['121', jour(0), jour(3), 'client', 'M. Diallo', 'confirmee'],
    ['201', jour(1), jour(2), 'client', 'Mme Bamba', 'confirmee'],
    ['221', jour(0), jour(6), 'vente', 'peinture', ''],
    ['321', jour(3), jour(9), 'client', 'Famille Yao', 'confirmee'],
  ];
  let p = 0;
  for (const [numero, debut, fin, nature, qui, statut] of POSES) {
    if (!ids[numero]) continue;
    const r = await appel('enregistrer', { type: 'fermeture', entree: {
      cible: ids[numero], debut, fin, nature,
      client: nature === 'client' ? qui : '',
      motif: nature === 'client' ? '' : qui,
      statut } });
    if (r.ok) p++;
  }

  /* Une chambre hors service, sans dates : le cas qui n'a pas de fin connue. */
  if (ids['301']) {
    const c = (await appel('tout')).donnees.chambres.find((x) => x.id === ids['301']);
    await appel('enregistrer', { type: 'chambre',
      entree: Object.assign({}, c, { service: false, note: 'climatisation' }) });
  }

  console.log('\n  %d chambres d essai, %d reservations, 1 hors service.', n, p);
  console.log('  Le site en annonce 46 : le compte tombe juste.');
  console.log('\n  CES NUMEROS SONT INVENTES. Les vrais viendront de l hotel.');
  console.log('  Pour tout retirer :  node .outils/semer-chambres.js --vider\n');
})().catch((e) => { console.error('\n  echec : ' + e.message + '\n'); process.exit(1); });
