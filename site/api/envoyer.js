// Point d'entree unique des cinq formulaires du site.
//
// Vercel expose automatiquement ce fichier sur /api/envoyer. Aucune dependance :
// l'envoi passe par l'API HTTP de Resend, appelee avec le fetch natif de Node.
//
// Variables d'environnement a definir dans Vercel (Settings > Environment Variables) :
//   RESEND_API_KEY   cle API Resend (commence par re_)
//   MAIL_DEST        destinataire, ex. bonjour@evannathhotel.com
//   MAIL_EXP         expediteur verifie chez Resend, ex. site@evannathhotel.com
//
// Tant qu'elles ne sont pas definies, l'endpoint repond 503 avec
// { configure: false } : le formulaire bascule alors sur WhatsApp et sur les
// numeros de la reception, sans jamais laisser le visiteur dans le vide.

const TYPES = {
  reservation: {
    sujet: 'Demande de réservation',
    requis: ['nom', 'email', 'tel'],
    champs: ['chambre', 'arrivee', 'depart', 'nuits', 'personnes', 'total',
             'acompte', 'paiement', 'nom', 'email', 'tel', 'message'],
  },
  devis: {
    sujet: 'Demande de devis — séminaires & groupes',
    requis: ['societe', 'nom', 'email', 'tel'],
    champs: ['societe', 'nom', 'email', 'tel', 'evenement', 'formule', 'configuration',
             'participants', 'chambres', 'date', 'message'],
  },
  contact: {
    sujet: 'Message depuis le site',
    requis: ['nom', 'email', 'message'],
    champs: ['nom', 'email', 'tel', 'sujet', 'message'],
  },
  table: {
    sujet: 'Demande de table — La table',
    requis: ['nom', 'tel'],
    champs: ['nom', 'tel', 'email', 'date', 'heure', 'couverts', 'message'],
  },
  forfait: {
    sujet: 'Demande de forfait — Offres',
    requis: ['nom', 'tel'],
    champs: ['forfait', 'date', 'quantite', 'total', 'nom', 'tel', 'email', 'message'],
  },
  spa: {
    sujet: 'Demande de rendez-vous — Le spa',
    requis: ['nom', 'tel'],
    champs: ['nom', 'tel', 'email', 'soin', 'date', 'heure', 'message'],
  },
};

const LIMITES = { nom: 120, email: 160, tel: 40, message: 4000, defaut: 200 };

// Limitation de debit, au mieux : une instance serverless est ephemere, donc
// ce garde-fou arrete les rafales sans pretendre etre une protection complete.
//
// Le seuil est volontairement haut. En Cote d'Ivoire, une grande partie du
// trafic mobile passe par du NAT operateur : des dizaines de visiteurs
// partagent alors une seule IP publique. Un seuil serre bloquerait des clients
// legitimes, ce qui coute plus cher que le spam qu'il evite.
const vus = new Map();
const FENETRE = 60_000;
const MAX_PAR_FENETRE = 20;

function trop_frequent(ip) {
  const t = Date.now();
  const liste = (vus.get(ip) || []).filter((x) => t - x < FENETRE);
  liste.push(t);
  vus.set(ip, liste);
  if (vus.size > 500) for (const [k, v] of vus) if (!v.some((x) => t - x < FENETRE)) vus.delete(k);
  return liste.length > MAX_PAR_FENETRE;
}

const propre = (v, max) => String(v == null ? '' : v).replace(/\s+/g, ' ').trim().slice(0, max);
const email_valide = (v) => /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i.test(v);
const tel_valide = (v) => (v.match(/\d/g) || []).length >= 8;

const echappe = (s) => String(s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;');

const ETIQUETTES = {
  societe: 'Société', nom: 'Nom', email: 'E-mail', tel: 'Téléphone',
  chambre: 'Chambre', arrivee: 'Arrivée', depart: 'Départ', nuits: 'Nuits',
  personnes: 'Personnes', total: 'Total estimé', acompte: 'Acompte (30 %)',
  paiement: 'Moyen de paiement souhaité', evenement: 'Type d’événement', formule: 'Formule',
  configuration: 'Configuration de salle', participants: 'Participants',
  chambres: 'Chambres souhaitées',
  date: 'Date', heure: 'Heure', couverts: 'Couverts', soin: 'Soin',
  forfait: 'Forfait', quantite: 'Quantité',
  sujet: 'Sujet', message: 'Message',
};

function corps(type, d, ref, meta) {
  const def = TYPES[type];
  const lignes = def.champs
    .filter((c) => d[c])
    .map((c) => `<tr><td style="padding:7px 16px 7px 0;color:#8a7d6c;white-space:nowrap;vertical-align:top">${ETIQUETTES[c] || c}</td>`
               + `<td style="padding:7px 0;color:#1b1b1b">${echappe(d[c]).replace(/\n/g, '<br>')}</td></tr>`)
    .join('');
  return `<div style="font:15px/1.6 -apple-system,Segoe UI,Roboto,sans-serif;color:#1b1b1b">
<p style="margin:0 0 4px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#B98A50"><strong>${def.sujet}</strong></p>
<p style="margin:0 0 18px;font-size:13px;color:#8a7d6c">Référence ${ref}</p>
<table style="border-collapse:collapse">${lignes}</table>
<p style="margin:22px 0 0;padding-top:14px;border-top:1px solid #e6e0d6;font-size:12px;color:#8a7d6c">
Envoyé depuis evannathhotel.com · ${meta.date}${meta.page ? ' · ' + echappe(meta.page) : ''}</p>
</div>`;
}

async function envoyer_mail(payload) {
  const cle = process.env.RESEND_API_KEY;
  const dest = process.env.MAIL_DEST;
  const exp = process.env.MAIL_EXP;
  if (!cle || !dest || !exp) return { ok: false, raison: 'non_configure' };

  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: `Bearer ${cle}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from: `Hôtel Evannath <${exp}>`,
      to: payload.a || dest.split(',').map((s) => s.trim()).filter(Boolean),
      reply_to: payload.replyTo || undefined,
      subject: payload.sujet,
      html: payload.html,
    }),
  });
  if (!r.ok) {
    const texte = await r.text().catch(() => '');
    return { ok: false, raison: 'refus_fournisseur', detail: texte.slice(0, 400) };
  }
  return { ok: true };
}

// ── L'accuse de reception au client ────────────────────────────────────
// Le client qui laisse son adresse recoit, des l'envoi, le recapitulatif de
// ce qu'il vient de demander et sa reference. Jusqu'ici, il n'avait que
// l'ecran de confirmation : une fois l'onglet ferme, plus aucune trace.
//
// Ce n'est PAS une confirmation de reservation : la chambre n'est confirmee
// que par la reception (voir courrielAuClient dans api/admin.js). Le texte
// le dit, pour qu'aucun client ne se croie attendu sans l'etre.
//
// Le message libre du visiteur n'y est pas recopie : sinon n'importe qui
// pourrait faire envoyer par l'hotel le texte de son choix a l'adresse de
// son choix. Le reste (dates, chambre, nombre...) est borne et echappe.
const POUR_CLIENT = {
  fr: {
    objet: { reservation: 'Votre demande de réservation', devis: 'Votre demande de devis',
             contact: 'Votre message', table: 'Votre demande de table', spa: 'Votre demande de rendez-vous au spa',
             forfait: 'Votre demande de forfait' },
    bonjour: (n) => `Bonjour ${n},`,
    recu: (o) => `Nous avons bien reçu ${o.charAt(0).toLowerCase() + o.slice(1)} à l'Hôtel Evannath. Voici ce que vous nous avez transmis.`,
    attente: {
      reservation: 'Ce n’est pas encore une confirmation : la réception vérifie la disponibilité et vous répond sous 24 h. La chambre est confirmée à réception de l’acompte.',
      devis: 'Le service commercial vous envoie un devis détaillé sous 24 h.',
      contact: 'La réception vous répond sous 24 h.',
      table: 'La réception vous confirme la table rapidement.',
      spa: 'La réception vous confirme le créneau rapidement.',
      forfait: 'Ce n’est pas encore une confirmation : la réception vérifie la date et vous répond sous 24 h. Aucun paiement n’a été demandé à cette étape.',
    },
    ref: 'Référence', repondre: 'Pour toute question, répondez simplement à ce message ou écrivez-nous sur WhatsApp au',
  },
  en: {
    objet: { reservation: 'Your booking request', devis: 'Your quote request',
             contact: 'Your message', table: 'Your table request', spa: 'Your spa appointment request',
             forfait: 'Your package request' },
    bonjour: (n) => `Dear ${n},`,
    recu: (o) => `We have received ${o.charAt(0).toLowerCase() + o.slice(1)} at Hôtel Evannath. Here is what you sent us.`,
    attente: {
      reservation: 'This is not a confirmation yet: the front desk checks availability and replies within 24 hours. The room is confirmed once the deposit is received.',
      devis: 'Our sales team will send you a detailed quote within 24 hours.',
      contact: 'The front desk will reply within 24 hours.',
      table: 'The front desk will confirm your table shortly.',
      spa: 'The front desk will confirm your slot shortly.',
      forfait: 'This is not a confirmation yet: the front desk checks the date and replies within 24 hours. No payment has been taken at this stage.',
    },
    ref: 'Reference', repondre: 'For any question, simply reply to this message or write to us on WhatsApp at',
  },
};
const ETIQUETTES_EN = {
  societe: 'Company', nom: 'Name', email: 'E-mail', tel: 'Phone', chambre: 'Room', arrivee: 'Arrival',
  depart: 'Departure', nuits: 'Nights', personnes: 'Guests', total: 'Estimated total', acompte: 'Deposit (30%)',
  paiement: 'Preferred payment', evenement: 'Type of event', formule: 'Package', configuration: 'Room layout',
  participants: 'Participants', chambres: 'Rooms needed', date: 'Date', heure: 'Time', couverts: 'Covers',
  soin: 'Treatment', sujet: 'Subject', forfait: 'Package', quantite: 'Quantity',
};
// Ce que le client ne revoit pas dans son recapitulatif : ses propres
// coordonnees n'y apprennent rien, et le message libre ne repart pas (plus haut).
const HORS_RECAP = new Set(['email', 'message']);

// Une date saisie dans un champ date arrive en 2026-12-19 : le client la lit
// « 19 décembre 2026 ». Le reste passe tel quel.
function lisible(v, langue) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(v)) return v;
  const j = new Date(v + 'T12:00:00Z');
  return isNaN(j) ? v : j.toLocaleDateString(langue === 'en' ? 'en-GB' : 'fr-FR',
    { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
}

function corpsClient(type, d, ref, langue) {
  const T = POUR_CLIENT[langue], def = TYPES[type];
  const lib = langue === 'en' ? ETIQUETTES_EN : ETIQUETTES;
  const lignes = def.champs
    .filter((c) => d[c] && !HORS_RECAP.has(c))
    .map((c) => `<tr><td style="padding:6px 18px 6px 0;color:#8a7d6c;white-space:nowrap;vertical-align:top">${lib[c] || c}</td>`
               + `<td style="padding:6px 0">${echappe(lisible(d[c], langue))}</td></tr>`)
    .join('');
  const wa = '+225 01 51 52 75 75';   // la ligne Reservations de l'hotel
  return `<div style="font:400 15px/1.6 Georgia,serif;color:#1b1b1b;max-width:520px">
<p>${T.bonjour(echappe(d.nom))}</p>
<p>${T.recu(T.objet[type])}</p>
<table style="border-collapse:collapse;margin:18px 0">
<tr><td style="padding:6px 18px 6px 0;color:#8a7d6c;white-space:nowrap">${T.ref}</td><td style="padding:6px 0"><strong>${ref}</strong></td></tr>
${lignes}</table>
<p><strong>${T.attente[type]}</strong></p>
<p style="color:#8a7d6c;font-size:13.5px">${T.repondre} ${echappe(wa)}.<br>
Hôtel Evannath — Assinie PK 19, Côte d'Ivoire</p>
</div>`;
}

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');

  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ ok: false, message: 'Méthode non autorisée.' });
  }

  const ip = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'inconnue';
  if (trop_frequent(ip)) {
    return res.status(429).json({ ok: false, message: 'Trop de demandes envoyées coup sur coup. Patientez une minute.' });
  }

  let d = req.body;
  if (typeof d === 'string') { try { d = JSON.parse(d); } catch { d = null; } }
  if (!d || typeof d !== 'object') {
    return res.status(400).json({ ok: false, message: 'Requête illisible.' });
  }

  const def = TYPES[d.type];
  if (!def) return res.status(400).json({ ok: false, message: 'Type de demande inconnu.' });

  // Piege a robots : champ invisible qu'un humain ne remplit jamais, et delai
  // minimum de remplissage. On repond 200 pour ne rien apprendre au robot.
  if (propre(d.website, 80) !== '' || Number(d.duree) < 2500) {
    return res.status(200).json({ ok: true, reference: 'EVN-000000' });
  }

  const donnees = {};
  for (const c of def.champs) {
    const v = propre(d[c], LIMITES[c] || LIMITES.defaut);
    if (v) donnees[c] = v;
  }

  const manquants = def.requis.filter((c) => !donnees[c]);
  if (manquants.length) {
    return res.status(422).json({ ok: false, champs: manquants, message: 'Il manque des informations obligatoires.' });
  }
  if (donnees.email && !email_valide(donnees.email)) {
    return res.status(422).json({ ok: false, champs: ['email'], message: "Cette adresse e-mail n'est pas valide." });
  }
  if (donnees.tel && !tel_valide(donnees.tel)) {
    return res.status(422).json({ ok: false, champs: ['tel'], message: 'Ce numéro de téléphone est trop court.' });
  }

  const ref = 'EVN-' + Date.now().toString(36).slice(-6).toUpperCase();
  const meta = {
    date: new Date().toLocaleString('fr-FR', { timeZone: 'Africa/Abidjan', dateStyle: 'full', timeStyle: 'short' }),
    page: propre(d.page, 120),
  };

  const envoi = await envoyer_mail({
    sujet: `${def.sujet} — ${donnees.nom}${donnees.societe ? ' (' + donnees.societe + ')' : ''} — ${ref}`,
    html: corps(d.type, donnees, ref, meta),
    replyTo: donnees.email || undefined,
  });

  if (!envoi.ok) {
    const code = envoi.raison === 'non_configure' ? 503 : 502;
    return res.status(code).json({
      ok: false,
      configure: envoi.raison !== 'non_configure',
      reference: ref,
      message: envoi.raison === 'non_configure'
        ? "L'envoi automatique n'est pas encore activé sur ce site."
        : "L'envoi a échoué côté serveur.",
    });
  }

  /* L'accuse de reception part apres celui de la reception, et son echec
     ne change rien a la reponse : la demande, elle, est bien arrivee. On
     dit seulement au navigateur si le client a recu son recapitulatif. */
  let accuse = 'sans-adresse';
  if (donnees.email) {
    const langue = String(d.langue || '').slice(0, 2) === 'en' ? 'en' : 'fr';
    const r = await envoyer_mail({
      a: [donnees.email],
      sujet: `${POUR_CLIENT[langue].objet[d.type]} — ${ref}`,
      html: corpsClient(d.type, donnees, ref, langue),
      replyTo: process.env.MAIL_DEST ? process.env.MAIL_DEST.split(',')[0].trim() : undefined,
    }).catch(() => ({ ok: false }));
    accuse = r.ok ? 'envoye' : 'echec';
  }

  return res.status(200).json({ ok: true, reference: ref, accuse });
}
