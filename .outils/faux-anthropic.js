/* Un faux serveur Anthropic, pour eprouver le chatbot (site/api/chat.js)
 * SANS cle ni depense : il repond au format de l'API Messages, et joue les
 * outils du chatbot selon des mots-cles de la question.
 *
 *   PORT_FAUX=5630 node .outils/faux-anthropic.js
 *   puis : ANTHROPIC_API_KEY=faux ANTHROPIC_BASE_URL=http://localhost:5630 node serveur-local.js
 *
 * GET /journal rend les requetes recues (modele, outils, consigne...), pour
 * que les tests verifient ce que le site envoie vraiment.
 * Il ne parle qu'a localhost : c'est un outil de poste, pas un service.
 */
const http = require('http');
const PORT = Number(process.env.PORT_FAUX || 5630);
const journal = [];

const iso = (j) => new Date(Date.now() + j * 864e5).toISOString().slice(0, 10);
let n = 0;
const msg = (content, stop) => ({
  id: 'msg_faux_' + (++n), type: 'message', role: 'assistant', model: 'claude-opus-5-5',
  content, stop_reason: stop, stop_sequence: null,
  usage: { input_tokens: 10, output_tokens: 10, cache_read_input_tokens: 0, cache_creation_input_tokens: 0 },
});
const outil = (name, input) => ({ type: 'tool_use', id: 'toolu_faux_' + (++n), name, input });
const texte = (t) => ({ type: 'text', text: t });

function repondre(corps) {
  const m = corps.messages || [];
  const dernier = m[m.length - 1] || {};
  // Retour d'outil : on resume ce que l'outil a rendu.
  if (Array.isArray(dernier.content) && dernier.content.some((b) => b.type === 'tool_result')) {
    const r = dernier.content.map((b) => { try { return JSON.parse(b.content); } catch (e) { return {}; } });
    const dispo = r.find((x) => x.categories);
    if (dispo) {
      const c = dispo.categories[0];
      return msg([texte(`La **${c.categorie}** est ${c.disponibilite || 'à ' + c.prix_nuit + ' la nuit'}`
        + (c.sejour && c.sejour.total ? `, pour un total de **${c.sejour.total}**.` : '.'))], 'end_turn');
    }
    if (r.some((x) => x.promotions)) {
      const o = r.find((x) => x.promotions);
      return msg([texte(`Offres du moment : ${o.promotions.length} promotion(s), ${o.evenements.length} événement(s).`)], 'end_turn');
    }
    return msg([texte('Voici le bouton pour continuer.')], 'end_turn');
  }
  const q = String(typeof dernier.content === 'string' ? dernier.content : '').toLowerCase();
  if (/r[ée]serv|book/.test(q)) {
    return msg([texte('Je prépare la page.'), outil('proposer_reservation', { categorie: 'suite-anglaise', arrivee: iso(20), depart: iso(22), personnes: 2 })], 'tool_use');
  }
  if (/libre|dispo|free|available/.test(q)) {
    return msg([outil('consulter_disponibilites', { categorie: 'suite-anglaise', arrivee: iso(20), depart: iso(22), personnes: 2 })], 'tool_use');
  }
  if (/offre|promo|événement|evenement/.test(q)) return msg([outil('offres_du_moment', {})], 'tool_use');
  if (/réception|reception|parler|humain/.test(q)) {
    return msg([outil('passer_a_la_reception', { resume: 'Bonjour, je voudrais parler à la réception.' })], 'tool_use');
  }
  if (/interdit/.test(q)) return msg([], 'refusal');
  return msg([texte('Bonjour ! Le petit-déjeuner est **inclus** dans toutes nos catégories.')], 'end_turn');
}

http.createServer((req, res) => {
  const u = new URL(req.url, 'http://localhost');
  if (req.method === 'GET' && u.pathname === '/journal') {
    res.writeHead(200, { 'Content-Type': 'application/json' }); return res.end(JSON.stringify(journal));
  }
  if (req.method === 'POST' && u.pathname === '/v1/messages') {
    const morceaux = [];
    req.on('data', (c) => morceaux.push(c));
    req.on('end', () => {
      let corps = {};
      try { corps = JSON.parse(Buffer.concat(morceaux).toString('utf8')); } catch (e) {}
      journal.push({ beta: req.headers['anthropic-beta'] || '', cle: !!req.headers['x-api-key'],
        espace: req.headers['anthropic-workspace-id'] || '', corps });
      const m = repondre(corps);
      if (!corps.stream) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify(m));
      }
      /* En flux (Server-Sent Events), comme l'API : le texte arrive par
         morceaux de quelques lettres, espaces de 30 ms. */
      res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' });
      const ev = (type, data) => res.write('event: ' + type + '\ndata: ' + JSON.stringify({ type, ...data }) + '\n\n');
      const pause = (ms) => new Promise((r) => setTimeout(r, ms));
      (async () => {
        ev('message_start', { message: { ...m, content: [], stop_reason: null } });
        for (let i = 0; i < m.content.length; i++) {
          const b = m.content[i];
          if (b.type === 'text') {
            ev('content_block_start', { index: i, content_block: { type: 'text', text: '' } });
            for (let k = 0; k < b.text.length; k += 8) {
              ev('content_block_delta', { index: i, delta: { type: 'text_delta', text: b.text.slice(k, k + 8) } });
              await pause(30);
            }
          } else {
            ev('content_block_start', { index: i, content_block: { type: 'tool_use', id: b.id, name: b.name, input: {} } });
            ev('content_block_delta', { index: i, delta: { type: 'input_json_delta', partial_json: JSON.stringify(b.input) } });
          }
          ev('content_block_stop', { index: i });
        }
        ev('message_delta', { delta: { stop_reason: m.stop_reason, stop_sequence: null }, usage: { output_tokens: 10 } });
        ev('message_stop', {});
        res.end();
      })();
    });
    return;
  }
  res.writeHead(404); res.end();
}).listen(PORT, '127.0.0.1', () => console.log('faux Anthropic sur http://localhost:' + PORT));
