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
    champs: ['societe', 'nom', 'email', 'tel', 'type', 'formule', 'configuration',
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
  paiement: 'Moyen de paiement souhaité', type: 'Type d’événement', formule: 'Formule',
  configuration: 'Configuration de salle', participants: 'Participants',
  chambres: 'Chambres souhaitées',
  date: 'Date', heure: 'Heure', couverts: 'Couverts', soin: 'Soin',
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
      to: dest.split(',').map((s) => s.trim()).filter(Boolean),
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

  return res.status(200).json({ ok: true, reference: ref });
}
