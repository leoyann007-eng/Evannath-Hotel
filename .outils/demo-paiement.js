/* Demonstration du paiement en ligne, SANS cle lomi : le site (port 5598)
 * branche sur le faux lomi (port 5620), memoire vierge, chambres d'essai.
 *
 *   node .outils/demo-paiement.js
 *
 * La page de paiement est jaune et porte « FAUX LOMI » : aucun argent ne
 * bouge, rien ne sort du poste. Pour le vrai bac a sable de lomi, il faut
 * LOMI_SECRET_KEY=lomi_sk_test_... dans .env.local et `node serveur-local.js`.
 */
const { spawn, execFileSync } = require('child_process');
const path = require('path');

const RACINE = path.join(__dirname, '..');
const SITE = 'http://localhost:5598', FAUX = 'http://localhost:5620';
const SECRET = 'whsec_demo_local';

const enfants = [
  spawn('node', ['.outils/faux-lomi.js'], { cwd: RACINE, stdio: 'inherit',
    env: { ...process.env, PORT_FAUX: '5620', WEBHOOK_URL: SITE + '/api/lomi', WEBHOOK_SECRET: SECRET } }),
  spawn('node', ['serveur-local.js'], { cwd: RACINE, stdio: 'inherit',
    env: { ...process.env, PORT: '5598', BLOB_READ_WRITE_TOKEN: '', RESEND_API_KEY: '',
      LOMI_SECRET_KEY: 'lomi_sk_test_demo', LOMI_API_URL: FAUX, LOMI_WEBHOOK_SECRET: SECRET } }),
];
const fin = () => { enfants.forEach((e) => { try { e.kill(); } catch (x) {} }); process.exit(0); };
process.on('SIGINT', fin); process.on('SIGTERM', fin);

setTimeout(() => {
  try {
    execFileSync('node', ['.outils/semer-chambres.js'], { cwd: RACINE, env: { ...process.env, BASE: SITE }, stdio: 'ignore' });
    console.log('Demonstration prete : ' + SITE + '/reserver (paiement par le FAUX lomi)');
  } catch (e) { console.error('Chambres d\'essai non semees : ' + e.message); }
}, 1500);
