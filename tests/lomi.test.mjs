// La notification de lomi (site/api/lomi.mjs) : on ne croit que ce que lomi
// a signe, sur les octets exacts du corps.
//
// Lance depuis la racine du depot :  node tests/lomi.test.mjs
import crypto from 'node:crypto';

process.env.LOMI_WEBHOOK_SECRET = 'whsec_essai';
process.env.BLOB_READ_WRITE_TOKEN = '';        // magasin en memoire, jamais la production
const { POST, signatureValide } = await import('../site/api/lomi.mjs');

let echecs = 0;
function verifier(nom, obtenu, attendu) {
  const ok = JSON.stringify(obtenu) === JSON.stringify(attendu);
  if (!ok) echecs++;
  console.log((ok ? '  ok   ' : '  ECHEC') + '  ' + nom
    + (ok ? '' : `\n         attendu ${JSON.stringify(attendu)}, obtenu ${JSON.stringify(obtenu)}`));
}
const signer = (corps, secret) => crypto.createHmac('sha256', secret || 'whsec_essai').update(corps).digest('hex');
const envoyer = (corps, signature) => POST(new Request('http://localhost/api/lomi', {
  method: 'POST', body: corps,
  headers: signature == null ? { 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json', 'X-Lomi-Signature': signature },
}));

console.log('\nLa signature');
{
  const c = Buffer.from('{"event":"PAYMENT_SUCCEEDED"}');
  verifier('la bonne signature passe', signatureValide(c, signer(c), 'whsec_essai'), true);
  verifier('en majuscules aussi (hexadecimal)', signatureValide(c, signer(c).toUpperCase(), 'whsec_essai'), true);
  verifier('un autre secret : refuse', signatureValide(c, signer(c, 'whsec_autre'), 'whsec_essai'), false);
  verifier('un octet de plus dans le corps : refuse',
    signatureValide(Buffer.from('{"event":"PAYMENT_SUCCEEDED"} '), signer(c), 'whsec_essai'), false);
  verifier('signature tronquee : refusee', signatureValide(c, signer(c).slice(0, 20), 'whsec_essai'), false);
  verifier('sans secret configure : tout est refuse', signatureValide(c, signer(c), ''), false);
}

console.log('\nLa route');
{
  const corps = JSON.stringify({ id: 'e1', event: 'PAYMENT_SUCCEEDED',
    data: { metadata: { reference: 'EVN-ZZZZZZ' }, amount: 1000 } });
  let r = await envoyer(corps, 'deadbeef');
  verifier('fausse signature : 401', r.status, 401);
  r = await envoyer(corps, null);
  verifier('sans signature : 401', r.status, 401);
  r = await envoyer(corps, signer(corps));
  verifier('signee, reference inconnue : 200 (sinon lomi renverrait sans fin)', [r.status, (await r.json()).suite], [200, 'inconnu']);
  const test = JSON.stringify({ id: 'e2', event: 'test.webhook', data: {} });
  r = await envoyer(test, signer(test));
  verifier('test.webhook : recu, ignore', [r.status, (await r.json()).suite], [200, 'ignore']);
  r = await envoyer('pas du json', signer('pas du json'));
  verifier('corps illisible mais signe : 400', r.status, 400);
}

console.log('');
if (echecs) { console.error(echecs + ' test(s) en echec'); process.exit(1); }
console.log('La notification lomi ne croit que ce qui est signe.');
