/**
 * La notification de lomi : « ce paiement a reussi » (ou echoue).
 *
 * C'est la seule voie par laquelle un paiement devient une reservation sans
 * que le client revienne sur le site — il peut fermer l'onglet des qu'il a
 * paye. Elle doit donc etre SURE : n'importe qui peut envoyer une requete a
 * cette adresse. On ne croit que ce que lomi a signe.
 *
 * La signature (X-Lomi-Signature) est un HMAC-SHA256, en hexadecimal, calcule
 * sur les OCTETS EXACTS du corps avec le secret du webhook (whsec_...). D'ou
 * la forme « Web » de cette fonction — POST(request) — plutot que (req, res) :
 * elle donne le corps brut. Relu puis re-serialise, le JSON ne reproduirait
 * pas les memes octets, et aucune signature ne passerait.
 *
 * lomi coupe au bout de quatre secondes environ et renvoie en cas d'echec :
 * les doublons sont normaux. marquerPaye() est idempotente.
 */
import crypto from 'node:crypto';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const admin = require('./admin.js');

const repondre = (code, corps) => new Response(JSON.stringify(corps), {
  status: code, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
});

/** La signature est-elle celle de lomi ? Comparaison a temps constant. */
export function signatureValide(brut, signature, secret) {
  if (!secret || !signature) return false;
  const attendue = crypto.createHmac('sha256', secret).update(brut).digest('hex');
  const a = Buffer.from(String(signature).trim().toLowerCase());
  const b = Buffer.from(attendue);
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

export async function POST(request) {
  const secret = process.env.LOMI_WEBHOOK_SECRET || '';
  const brut = Buffer.from(await request.arrayBuffer());
  if (!signatureValide(brut, request.headers.get('x-lomi-signature'), secret)) {
    return repondre(401, { ok: false });
  }
  let ev;
  try { ev = JSON.parse(brut.toString('utf8')); } catch (e) { return repondre(400, { ok: false }); }

  const donnees = (ev && ev.data) || {};
  const meta = donnees.metadata || {};
  const cle = {
    ref: String(meta.reference || '').toUpperCase(),
    session: String(donnees.checkout_session_id || donnees.checkout_session || ''),
  };

  if (ev.event === 'PAYMENT_SUCCEEDED') {
    const montant = donnees.amount != null ? donnees.amount
      : donnees.gross_amount != null ? donnees.gross_amount : null;
    const r = await admin.paiement.marquerPaye({ ...cle,
      transaction: donnees.id || donnees.transaction_id, montant });
    /* Un paiement que l'on ne retrouve pas n'est pas une erreur de lomi :
       on accuse reception, sinon il renverrait sans fin la meme chose. */
    return repondre(200, { ok: true, suite: r.ok ? (r.deja ? 'deja' : 'confirme') : r.raison });
  }
  if (ev.event === 'PAYMENT_FAILED') {
    await admin.paiement.marquerEchec(cle);
    return repondre(200, { ok: true, suite: 'echec' });
  }
  // test.webhook et le reste : recu, rien a faire.
  return repondre(200, { ok: true, suite: 'ignore' });
}
