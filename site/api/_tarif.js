/**
 * Le montant d'un sejour, calcule par le SERVEUR.
 *
 * C'est ce montant que l'on encaisse. Il ne vient jamais de la page : un
 * navigateur se modifie, et l'on encaisserait ce qu'il annonce. La page fait
 * le meme calcul pour l'afficher — tests/tarif.test.mjs verifie que les deux
 * tombent juste, sur toutes les chambres et toutes les formes de remise.
 *
 * Les prix, la taxe de sejour et la part d'acompte viennent de _grille.json,
 * ecrit par build-reserver.py a partir de la MEME source que la page.
 *
 * Le prefixe « _ » : Vercel n'en fait pas une fonction publique.
 */
const GRILLE = require('./_grille.json');

const JOUR = 864e5;
const NUITS_MAX = 30;

/* ── La remise : les regles de REMISE_JS (_chrome.py), a l'identique ───── */

function vise(p, slug) {
  const c = p.cible || {};
  if (c.toutes !== false) return true;
  return (c.chambres || []).indexOf(slug) >= 0;
}

function prixRemise(montant, slug, p) {
  if (!p || !vise(p, slug)) return montant;
  const r = p.remise || {};
  if (!r.valeur) return montant;
  const n = r.type === 'montant'
    ? montant - Number(r.valeur)
    : Math.round(montant * (1 - r.valeur / 100));
  /* Une remise qui depasse le prix : on garde le prix d'origine. */
  return n > 0 ? n : montant;
}

/** La promotion que la page applique : la premiere publiee dont la periode
 *  court — le filtre de /api/admin?a=public, puis « la premiere ». */
function promotionDuJour(promotions, maintenant) {
  const t = maintenant || Date.now();
  const enCours = (p) => {
    const d1 = p.debut ? Date.parse(p.debut) : null;
    const d2 = p.fin ? Date.parse(p.fin) : null;
    if (d1 && t < d1) return false;
    if (d2 && t > d2) return false;
    return true;
  };
  return (promotions || []).filter((p) => p && p.publie !== false).filter(enCours)[0] || null;
}

/* ── Le devis ─────────────────────────────────────────────────────────── */

const ISO = /^\d{4}-\d{2}-\d{2}$/;

/**
 * { categorie, du, au, pax } -> le detail du montant, ou { ok:false, raison }.
 * du et au sont une ARRIVEE et un DEPART (AAAA-MM-JJ) ; on paie les nuits
 * entre les deux.
 */
function devis(demande, promotions, maintenant) {
  const t = maintenant || Date.now();
  const c = GRILLE.chambres[demande && demande.categorie];
  if (!c) return { ok: false, raison: 'categorie' };
  const du = String(demande.du || ''), au = String(demande.au || '');
  if (!ISO.test(du) || !ISO.test(au)) return { ok: false, raison: 'dates' };
  const nuits = Math.round((Date.parse(au) - Date.parse(du)) / JOUR);
  if (!(nuits >= 1)) return { ok: false, raison: 'dates' };
  if (nuits > NUITS_MAX) return { ok: false, raison: 'duree' };
  /* Abidjan est a UTC+0 : la date ISO du serveur est la date ici. */
  if (du < new Date(t).toISOString().slice(0, 10)) return { ok: false, raison: 'passe' };
  const pax = Number(demande.pax);
  if (!Number.isInteger(pax) || pax < 1 || pax > c.max) return { ok: false, raison: 'personnes' };

  const promo = promotionDuJour(promotions, t);
  const tarif = prixRemise(c.prix, demande.categorie, promo);
  const sejour = tarif * nuits;
  const taxe = GRILLE.taxe * pax * nuits;
  const total = sejour + taxe;
  return {
    ok: true,
    categorie: demande.categorie, nom: c.nom, du, au, nuits, pax,
    plein: c.prix, tarif, sejour, taxe, total,
    acompte: Math.round(total * GRILLE.acompte),
    promotion: promo && tarif !== c.prix ? (promo.id || null) : null,
  };
}

module.exports = { devis, prixRemise, promotionDuJour, GRILLE };
