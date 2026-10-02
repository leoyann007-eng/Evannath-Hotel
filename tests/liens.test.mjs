// Les liens et images qu'un compte peut poser sur le site public
// (site/api/admin.js, lienSur / imageSure). Un lien « javascript: » sur un
// bouton d'offre executait du code avec la session de l'administrateur qui
// cliquait : un compte Communication pouvait ainsi se faire administrateur.
//
// Lance depuis la racine du depot :  node tests/liens.test.mjs
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { lienSur, imageSure } = require('../site/api/admin.js').surete;

let echecs = 0, total = 0;
function verifier(nom, obtenu, attendu) {
  total++;
  const ok = JSON.stringify(obtenu) === JSON.stringify(attendu);
  if (!ok) echecs++;
  console.log((ok ? '  ok   ' : '  ECHEC') + '  ' + nom
    + (ok ? '' : '\n         obtenu  ' + JSON.stringify(obtenu) + '\n         attendu ' + JSON.stringify(attendu)));
}

console.log('\nLes liens acceptes, tels quels');
for (const v of ['#demande', 'reserver?chambre=suite-arabe&du=2026-12-24', '/contact', 'contact.html',
  'https://wa.me/2250700000000?text=Bonjour', 'http://exemple.ci', 'mailto:reservation@evannath.ci', 'tel:+2250700000000']) {
  verifier(v, lienSur(v), v);
}

console.log('\nLes liens refuses');
for (const v of ['javascript:alert(1)', 'JaVaScRiPt:alert(1)', 'java\tscript:alert(1)', 'java\nscript:alert(1)',
  ' javascript:alert(1)', '\u0001javascript:alert(1)', 'javascript&#58;alert(1)', 'data:text/html,<script>alert(1)</script>',
  'vbscript:msgbox(1)', '//evil.example', 'file:///etc/passwd', 'x:y']) {
  verifier(JSON.stringify(v), lienSur(v), '');
}

console.log('\nLes images');
const BLOB = 'https://qjatdj8uw2dzupim.public.blob.vercel-storage.com/evannath/affiches/1788350142765-4d5d6712-Uw.jpeg';
verifier('une photo du site', imageSure('r-standard'), 'r-standard');
verifier('une affiche deposee dans notre magasin', imageSure(BLOB), BLOB);
for (const v of ['https://evil.example/pixel.png', 'http://qjatdj8uw2dzupim.public.blob.vercel-storage.com/x.jpg',
  'https://evil.example/?u=.public.blob.vercel-storage.com/x', 'javascript:alert(1)', '"><img src=x onerror=alert(1)>',
  '../../admin', 'r-standard.jpg?x=<y>']) {
  verifier('refusee : ' + JSON.stringify(v), imageSure(v), '');
}

console.log('\n' + total + ' controles, ' + (total - echecs) + ' passes, ' + echecs + ' en echec');
process.exit(echecs ? 1 : 0);
