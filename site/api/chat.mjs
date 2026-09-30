/**
 * /api/chat — l'enveloppe HTTP du concierge. Toute la logique est dans
 * _chat.js ; ici, seulement la requete et la reponse.
 *
 * POURQUOI LA FORME « WEB » (export GET/POST, Request -> Response), comme
 * api/lomi.mjs : c'est elle que Vercel diffuse AU FIL DE L'EAU. Avec la forme
 * (req, res), Vercel gardait toute la reponse et l'envoyait a la fin : les
 * morceaux de texte arrivaient d'un coup, apres dix secondes d'attente.
 *
 *   GET  /api/chat                  -> { ok, actif }  la bulle doit-elle s'afficher ?
 *   POST /api/chat { flux:false }   -> { ok, texte, actions }
 *   POST /api/chat { flux:true }    -> NDJSON, une ligne par evenement :
 *        { t:'texte', d }              un morceau de reponse
 *        { t:'fin', texte, actions }   le texte definitif (il fait foi), les boutons
 *        { t:'erreur', raison, detail }
 */
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const chat = require('./_chat.js');

const ENTETES = { 'Cache-Control': 'no-store' };
const repondre = (code, corps) => Response.json(corps, { status: code, headers: ENTETES });

export async function GET() {
  return repondre(200, await chat.etat());
}

export async function POST(request) {
  let corps = {};
  try { corps = await request.json(); } catch (e) { corps = {}; }
  const ip = (request.headers.get('x-forwarded-for') || '').split(',')[0].trim() || 'inconnue';
  const p = await chat.preparer(corps, ip);
  if (p.refus) return repondre(p.refus.code, p.refus.corps);

  if (!p.flux) {
    try { return repondre(200, { ok: true, ...(await chat.converser(p)) }); }
    catch (e) { return repondre(502, chat.diagnostic(e)); }
  }

  const code = new TextEncoder();
  const flux = new ReadableStream({
    async start(ctrl) {
      const ligne = (o) => ctrl.enqueue(code.encode(JSON.stringify(o) + '\n'));
      try {
        const fin = await chat.converser({ ...p, surTexte: (d) => ligne({ t: 'texte', d }) });
        ligne({ t: 'fin', ...fin });
      } catch (e) {
        ligne({ t: 'erreur', ...chat.diagnostic(e) });
      }
      ctrl.close();
    },
  });
  return new Response(flux, { status: 200, headers: {
    ...ENTETES, 'Content-Type': 'application/x-ndjson; charset=utf-8', 'X-Accel-Buffering': 'no' } });
}
