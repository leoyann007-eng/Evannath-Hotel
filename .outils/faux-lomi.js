/* Un faux lomi, pour essayer le paiement de bout en bout SANS cle ni reseau.
 *
 * Il imite ce que la documentation de lomi decrit :
 *   POST /checkout-sessions        (X-API-KEY lomi_sk_test_...) -> { id, checkout_url, status }
 *   GET  /checkout-sessions/{id}   -> { id, status }
 *   GET  /payer/{id}               une page de paiement : Payer / Echec / Abandonner
 * et la notification signee (X-Lomi-Signature : HMAC-SHA256 hexadecimal du
 * corps brut) envoyee au site, comme le ferait lomi.
 *
 *   PORT_FAUX=5620 WEBHOOK_URL=http://localhost:5598/api/lomi \
 *   WEBHOOK_SECRET=whsec_faux node .outils/faux-lomi.js
 *
 * Il ne parle qu'a localhost : c'est un outil de poste, pas un service.
 */
const http = require('http');
const crypto = require('crypto');

const PORT = Number(process.env.PORT_FAUX || 5620);
const WEBHOOK_URL = process.env.WEBHOOK_URL || 'http://localhost:5598/api/lomi';
const SECRET = process.env.WEBHOOK_SECRET || 'whsec_faux_local';
if (!/^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?\//.test(WEBHOOK_URL)) {
  console.error('WEBHOOK_URL doit viser localhost : ' + WEBHOOK_URL); process.exit(1);
}

const sessions = new Map();
const journal = [];   // ce que le faux lomi a recu et envoye, pour les tests

function lireCorps(req) {
  return new Promise((ok) => { const m = []; req.on('data', (c) => m.push(c)); req.on('end', () => ok(Buffer.concat(m).toString('utf8'))); });
}
function json(res, code, o) { res.writeHead(code, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(o)); }

async function notifier(evenement, s, options) {
  const corps = JSON.stringify({
    id: crypto.randomUUID(), event: evenement, timestamp: new Date().toISOString(),
    data: { id: 'txn_' + crypto.randomBytes(6).toString('hex'), amount: (options && options.montant) || s.amount,
      currency_code: s.currency_code, checkout_session_id: s.id, metadata: s.metadata, status: evenement === 'PAYMENT_SUCCEEDED' ? 'completed' : 'failed' },
    lomi_environment: 'test',
  });
  const signature = (options && options.fausseSignature) ? 'deadbeef'
    : crypto.createHmac('sha256', SECRET).update(corps).digest('hex');
  const envois = (options && options.doublon) ? 2 : 1;
  for (let i = 0; i < envois; i++) {
    try {
      const r = await fetch(WEBHOOK_URL, { method: 'POST', body: corps,
        headers: { 'Content-Type': 'application/json', 'X-Lomi-Signature': signature, 'X-Lomi-Event': evenement } });
      journal.push({ envoi: evenement, statut: r.status, reponse: await r.text() });
    } catch (e) { journal.push({ envoi: evenement, erreur: String(e.message) }); }
  }
}

http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://localhost:' + PORT);
  const p = u.pathname;

  if (req.method === 'POST' && p === '/checkout-sessions') {
    const cle = req.headers['x-api-key'] || '';
    if (!String(cle).startsWith('lomi_sk_test_')) return json(res, 401, { error: 'cle invalide' });
    let b = {}; try { b = JSON.parse(await lireCorps(req)); } catch (e) { return json(res, 400, { error: 'json' }); }
    journal.push({ recu: 'checkout-sessions', corps: b });
    if (!b.amount || b.currency_code !== 'XOF') return json(res, 422, { error: 'montant ou devise' });
    const id = 'cs_test_' + crypto.randomBytes(8).toString('hex');
    const s = { id, status: 'open', amount: b.amount, currency_code: b.currency_code, metadata: b.metadata || {},
      success_url: b.success_url, cancel_url: b.cancel_url, title: b.title, description: b.description };
    sessions.set(id, s);
    return json(res, 200, { id, checkout_url: 'http://localhost:' + PORT + '/payer/' + id, status: 'open',
      amount: s.amount, currency_code: s.currency_code, expires_at: new Date(Date.now() + 3600e3).toISOString() });
  }

  let m = p.match(/^\/checkout-sessions\/([\w-]+)$/);
  if (req.method === 'GET' && m) {
    const s = sessions.get(m[1]);
    return s ? json(res, 200, { id: s.id, status: s.status, amount: s.amount }) : json(res, 404, { error: 'inconnue' });
  }

  m = p.match(/^\/payer\/([\w-]+)$/);
  if (req.method === 'GET' && m) {
    const s = sessions.get(m[1]);
    if (!s) { res.writeHead(404); return res.end('session inconnue'); }
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    return res.end(`<!doctype html><meta charset="utf-8"><title>Faux lomi</title>
      <body style="font:16px system-ui;max-width:520px;margin:60px auto">
      <p style="background:#fde68a;padding:8px 12px">FAUX LOMI — poste de developpement</p>
      <h1>${s.title || 'Paiement'}</h1><p>${s.description || ''}</p>
      <p><b id="montant">${s.amount} ${s.currency_code}</b></p>
      <form method="post" action="/payer/${s.id}/ok"><button id="ok">Payer (reussite)</button></form>
      <form method="post" action="/payer/${s.id}/ok?sans-webhook=1"><button id="ok-sans">Payer, sans notification</button></form>
      <form method="post" action="/payer/${s.id}/echec"><button id="echec">Paiement refuse</button></form>
      <a id="abandon" href="${s.cancel_url}">Abandonner</a></body>`);
  }

  m = p.match(/^\/payer\/([\w-]+)\/(ok|echec)$/);
  if (req.method === 'POST' && m) {
    const s = sessions.get(m[1]);
    if (!s) { res.writeHead(404); return res.end(); }
    if (m[2] === 'ok') {
      s.status = 'completed';
      if (!u.searchParams.has('sans-webhook')) await notifier('PAYMENT_SUCCEEDED', s, { doublon: u.searchParams.has('doublon') });
      res.writeHead(303, { Location: s.success_url }); return res.end();
    }
    s.status = 'failed';
    await notifier('PAYMENT_FAILED', s);
    res.writeHead(303, { Location: s.cancel_url.replace('&abandon=1', '') }); return res.end();
  }

  // Pour les tests : rejouer une notification (doublon, fausse signature, montant faux)
  m = p.match(/^\/rejouer\/([\w-]+)$/);
  if (req.method === 'POST' && m) {
    const s = sessions.get(m[1]);
    if (!s) return json(res, 404, {});
    await notifier(u.searchParams.get('evenement') || 'PAYMENT_SUCCEEDED', s, {
      fausseSignature: u.searchParams.has('fausse'), montant: Number(u.searchParams.get('montant')) || null });
    return json(res, 200, journal[journal.length - 1]);
  }
  if (p === '/journal') return json(res, 200, journal);
  res.writeHead(404); res.end();
}).listen(PORT, () => console.log('faux lomi sur http://localhost:' + PORT + ' -> notifications vers ' + WEBHOOK_URL));
