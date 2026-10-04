/* Le plafond du concierge : combien de messages par jour, tous visiteurs
 * confondus. Partage par api/_chat.js, qui compte, et api/admin.js, qui
 * l'affiche dans Parametres.
 *
 * Chaque message coute quelques francs, factures par Anthropic. La limite
 * par adresse arrete un visiteur trop pressé ; elle n'arrete pas un robot
 * qui change d'adresse a chaque question. Celle-ci, si : passe le plafond,
 * la bulle s'efface jusqu'au lendemain et le bouton WhatsApp prend le
 * relais. Le compteur vit dans la base quand elle est branchee — le meme
 * pour toutes les instances, donc un vrai plafond. Sans base, chaque
 * instance compte de son cote.
 *
 * CHAT_MAX_JOUR (Vercel) le change. La limite de depense posee dans la
 * console Anthropic reste le dernier rempart : elle, aucun bug ne la
 * contourne.
 *
 * Le prefixe « _ » : Vercel n'en fait pas une fonction publique.
 */
const magasin = require('./_magasin.js');

const PAR_JOUR = Math.max(1, Math.floor(Number(process.env.CHAT_MAX_JOUR)) || 200);
// Abidjan est a UTC+0 : la date ISO du serveur est la date ici.
const cle = () => 'chat:jour:' + new Date().toISOString().slice(0, 10);

/** Compte un message ; rend faux si le plafond du jour est depasse. */
async function compterMessage() {
  return (await magasin.compter(cle(), 2 * 864e5)) <= PAR_JOUR;
}

/** Le plafond est-il deja atteint ? (sans compter de message) */
async function atteint() {
  return (await magasin.valeur(cle())) >= PAR_JOUR;
}

/** Combien de messages aujourd'hui. */
const aujourdhui = () => magasin.valeur(cle());

module.exports = { PAR_JOUR, compterMessage, atteint, aujourdhui };
