/* Les comptes de l'administration : qui entre, avec quel profil, et ce que
 * ce profil a le droit de faire.
 *
 * AVANT : un mot de passe unique (ADMIN_MDP), partage par toute l'equipe.
 * Impossible de savoir qui avait fait quoi, ni de couper l'acces d'une seule
 * personne sans changer le mot de passe de toutes les autres.
 *
 * MAINTENANT :
 *   - des comptes nominatifs (nom, e-mail, profil), crees par un
 *     administrateur avec un mot de passe PROVISOIRE, a changer a la premiere
 *     connexion ;
 *   - quatre profils, verifies ICI, cote serveur — masquer un bouton dans
 *     l'interface n'a jamais protege quoi que ce soit ;
 *   - ADMIN_MDP reste l'ACCES DE SECOURS : e-mail vide + ce mot de passe.
 *     C'est par lui qu'on cree le premier compte, et par lui qu'on rentre si
 *     le seul administrateur oublie le sien. Changer ADMIN_MDP dans Vercel
 *     coupe toutes les sessions de secours ouvertes.
 *
 * STOCKAGE : un document a part (« comptes »), jamais melange aux donnees
 * du site — voir _magasin.js : base Postgres privee quand elle est branchee,
 * Vercel Blob en attendant. Chaque modification relit l'etat frais et
 * n'ecrit que si personne n'a ecrit entre-temps : une connexion qui note sa
 * date de visite ne peut plus defaire une desactivation faite au meme
 * instant. Les mots de passe n'y sont jamais en clair : scrypt, sel propre a
 * chaque compte.
 */

const crypto = require('crypto');
const magasin = require('./_magasin.js');

// ── Les profils ────────────────────────────────────────────────────────────
/* `vues` : les rubriques du menu. `droits` : ce que le profil peut ECRIRE.
   Les deux listes sont lues par l'interface (pour n'afficher que l'utile) et
   par le serveur (pour refuser le reste). La seconde seule fait foi. */
const ROLES = {
  admin: {
    nom: 'Administrateur',
    resume: 'Tout, plus les comptes, les prix et les paramètres.',
    vues: ['bord', 'disponibilites', 'chambres', 'evenements', 'promotions', 'campagnes',
      'emplois', 'galerie', 'parametres', 'utilisateurs', 'journal', 'compte'],
    droits: ['reservations', 'chambres', 'contenu', 'tarifs', 'reglages', 'comptes'],
  },
  reception: {
    nom: 'Réception',
    resume: 'Disponibilités, réservations et chambres.',
    vues: ['bord', 'disponibilites', 'chambres', 'compte'],
    droits: ['reservations', 'chambres'],
  },
  communication: {
    nom: 'Communication',
    resume: 'Événements, promotions, campagnes, recrutement et affiches.',
    vues: ['bord', 'evenements', 'promotions', 'campagnes', 'emplois', 'galerie', 'compte'],
    droits: ['contenu'],
  },
  lecture: {
    nom: 'Lecture seule',
    resume: 'Consulte tout, ne modifie rien.',
    vues: ['bord', 'disponibilites', 'chambres', 'evenements', 'promotions', 'campagnes',
      'emplois', 'galerie', 'compte'],
    droits: [],
  },
};

/* Le droit qu'exige chaque ecriture. `type` departage enregistrer,
   supprimer et ordonner, qui servent plusieurs collections. */
const DROIT_DU_TYPE = {
  fermeture: 'reservations', chambre: 'chambres',
  evenement: 'contenu', promotion: 'contenu', campagne: 'contenu', emploi: 'contenu',
};
function droitRequis(action, type) {
  if (action === 'enregistrer' || action === 'supprimer' || action === 'ordonner') {
    return DROIT_DU_TYPE[type] || 'contenu';
  }
  return {
    televerser: 'contenu',
    'chambres-serie': 'chambres', 'chambres-lot': 'chambres',
    tarifs: 'tarifs', reglages: 'reglages',
    comptes: 'comptes', compte: 'comptes', 'compte-reinitialiser': 'comptes',
    'compte-supprimer': 'comptes', journal: 'comptes',
  }[action] || null;
}
const peut = (role, droit) => !!(ROLES[role] && ROLES[role].droits.includes(droit));

// ── Mots de passe ──────────────────────────────────────────────────────────
const MDP_MIN = 10;
const SCRYPT = { N: 16384, r: 8, p: 1 };

function hacher(mdp) {
  const sel = crypto.randomBytes(16);
  return new Promise((ok, ko) => crypto.scrypt(String(mdp), sel, 32, SCRYPT, (e, h) =>
    (e ? ko(e) : ok('scrypt$' + sel.toString('base64') + '$' + h.toString('base64')))));
}

function verifier(mdp, empreinte) {
  const [algo, sel64, h64] = String(empreinte || '').split('$');
  if (algo !== 'scrypt' || !sel64 || !h64) return Promise.resolve(false);
  const attendu = Buffer.from(h64, 'base64');
  return new Promise((ok) => crypto.scrypt(String(mdp), Buffer.from(sel64, 'base64'),
    attendu.length, SCRYPT, (e, h) => ok(!e && crypto.timingSafeEqual(h, attendu))));
}

/* Lisible a voix haute et sans ambiguite : ni 0/O, ni 1/l/I. Trois groupes
   de quatre, soit environ 70 bits — et il ne vit que jusqu'a la premiere
   connexion. */
const ALPHABET = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789';
function provisoire() {
  const g = () => Array.from(crypto.randomBytes(4), (o) => ALPHABET[o % ALPHABET.length]).join('');
  return g() + '-' + g() + '-' + g();
}

/** Un nouveau mot de passe acceptable ? Rend le message de refus, ou ''. */
function mdpRefuse(mdp, compte) {
  const m = String(mdp || '');
  if (m.length < MDP_MIN) return 'Le mot de passe doit compter au moins ' + MDP_MIN + ' caractères.';
  if (m.length > 200) return 'Le mot de passe est trop long.';
  if (compte && m.toLowerCase().includes(String(compte.courriel).split('@')[0].toLowerCase())) {
    return 'Le mot de passe ne doit pas reprendre votre adresse e-mail.';
  }
  if (/^(.)\1+$/.test(m)) return 'Ce mot de passe est trop simple.';
  return '';
}

// ── Le fichier des comptes ─────────────────────────────────────────────────
const PREFIXE = 'evannath/comptes';
const GARDE = 5;
const VIDE = () => ({ comptes: [], journal: [] });
const JOURNAL_MAX = 500;
const CACHE_MS = 30_000;

function creer({ jeton, secours, secret }) {
  const DOC = magasin.document({ cle: 'comptes', prefixeBlob: PREFIXE, garde: GARDE,
    vide: VIDE, jeton, nom: 'du fichier des comptes' });
  /* Les sessions se verifient a chaque appel : une lecture gardee trente
     secondes evite de relire le fichier a chaque clic. Les modifications,
     elles, repartent toujours de l'etat frais. */
  let cache = null, cacheA = 0;

  async function lire(frais) {
    if (!frais && cache && Date.now() - cacheA < CACHE_MS) return { ok: true, d: structuredClone(cache) };
    const l = await DOC.lire();
    if (!l.ok) {
      return { ok: false, message: l.panne || 'Le fichier des comptes est illisible pour l’instant. Réessayez dans un instant.' };
    }
    l.d.comptes = l.d.comptes || []; l.d.journal = l.d.journal || [];
    cache = structuredClone(l.d); cacheA = Date.now();
    return { ok: true, d: l.d };
  }

  /** Relire, appliquer, ecrire si personne n'a ecrit entre-temps (voir
   *  _magasin.js). `appliquer(d)` peut tourner plusieurs fois : rien
   *  d'exterieur dedans. Elle rend { annuler: reponse } pour s'arreter. */
  async function modifier(appliquer) {
    const r = await DOC.modifier(async (d) => {
      d.comptes = d.comptes || []; d.journal = d.journal || [];
      const v = await appliquer(d);
      d.journal = d.journal.slice(-JOURNAL_MAX);
      return v;
    });
    if (r.ok && !r.annule) { cache = structuredClone(r.d); cacheA = Date.now(); }
    return r;
  }

  /** La reponse d'une modification qui n'a pas abouti. */
  const refusModif = (r) => (r.panne !== undefined
    ? { code: 503, corps: { ok: false, message: r.panne } }
    : { code: 502, corps: { ok: false, message: 'L’enregistrement des comptes a échoué : ' + r.message } });

  // ── Sessions ─────────────────────────────────────────────────────────────
  /* Le cookie porte { u: compte, v: version, e: expiration }, signe. La
     VERSION du compte monte a chaque changement qui doit couper les sessions
     ouvertes : mot de passe change ou reinitialise, profil change, compte
     desactive. Un cookie d'une version anterieure ne vaut plus rien. */
  const DUREE = 12 * 3600;
  const signe = (v) => crypto.createHmac('sha256', secret).update(v).digest('base64url');
  // La « version » de l'acces de secours : une empreinte du mot de passe.
  // Changer ADMIN_MDP dans Vercel invalide donc les sessions de secours.
  const versionSecours = () => crypto.createHash('sha256').update('secours:' + secours).digest('hex').slice(0, 12);

  function jeton_(u, v) {
    const charge = Buffer.from(JSON.stringify({ u, v, e: Math.floor(Date.now() / 1000) + DUREE })).toString('base64url');
    return charge + '.' + signe(charge);
  }
  const cookie = (valeur, age) =>
    `evn_adm=${encodeURIComponent(valeur)}; Path=/; HttpOnly; SameSite=Strict; Secure; Max-Age=${age}`;

  function lireCookie(req) {
    const m = (req.headers.cookie || '').match(/(?:^|;\s*)evn_adm=([^;]+)/);
    if (!m) return null;
    const [charge, sig] = decodeURIComponent(m[1]).split('.');
    if (!charge || !sig) return null;
    const a = Buffer.from(signe(charge)), b = Buffer.from(sig);
    if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return null;
    try {
      const p = JSON.parse(Buffer.from(charge, 'base64url').toString());
      return p.e > Math.floor(Date.now() / 1000) ? p : null;
    } catch (e) { return null; }
  }

  /** La personne derriere la requete, ou { erreur } : 401 sans session
      valable, 503 quand le fichier des comptes ne repond pas. */
  async function session(req) {
    if (!secret) return { erreur: 503, message: 'L’administration n’est pas configurée : définissez ADMIN_SECRET dans Vercel.' };
    const p = lireCookie(req);
    if (!p) return { erreur: 401 };
    if (p.u === 'secours') {
      if (!secours || p.v !== versionSecours()) return { erreur: 401 };
      return { id: 'secours', nom: 'Accès de secours', courriel: '', role: 'admin', provisoire: false, secours: true };
    }
    const l = await lire();
    if (!l.ok) return { erreur: 503, message: l.message };
    const c = l.d.comptes.find((x) => x.id === p.u);
    if (!c || !c.actif || c.version !== p.v) return { erreur: 401 };
    return { id: c.id, nom: c.nom, courriel: c.courriel, role: c.role, provisoire: !!c.provisoire };
  }

  const public_ = (c) => ({ id: c.id, nom: c.nom, courriel: c.courriel, role: c.role,
    actif: c.actif, provisoire: !!c.provisoire, cree: c.cree, derniere: c.derniere || null });

  const noter = (d, qui, texte) => d.journal.push({ t: new Date().toISOString(), u: qui.id, n: qui.nom, x: texte });

  // ── Connexion ────────────────────────────────────────────────────────────
  /* Les echecs comptent par adresse : cinq en quinze minutes et l'adresse
     se ferme un quart d'heure. Le compteur vit dans l'instance — scrypt, qui
     coute ~50 ms par essai, fait le reste. */
  const ECHECS = new Map();
  const FENETRE = 15 * 60_000, MAX_ECHECS = 5;
  const bloque = (k) => {
    const e = ECHECS.get(k);
    return e && e.n >= MAX_ECHECS && Date.now() - e.t < FENETRE;
  };
  const echec = (k) => {
    const e = ECHECS.get(k);
    ECHECS.set(k, !e || Date.now() - e.t > FENETRE ? { n: 1, t: Date.now() } : { n: e.n + 1, t: e.t });
  };

  async function entrer({ courriel, mdp }) {
    if (!secret) {
      return { code: 503, corps: { ok: false, message: 'L’administration n’est pas configurée : '
        + 'définissez ADMIN_SECRET (ou ADMIN_MDP) dans les variables Vercel.' } };
    }
    const adresse = String(courriel || '').trim().toLowerCase();
    const donne = String(mdp || '');
    const refus = { code: 401, corps: { ok: false, message: 'E-mail ou mot de passe incorrect.' } };

    // L'acces de secours : e-mail vide, ADMIN_MDP.
    if (!adresse) {
      if (!secours) {
        return { code: 503, corps: { ok: false, message: "L'accès de secours n'est pas configuré "
          + '(ADMIN_MDP dans les variables Vercel). Entrez votre e-mail.' } };
      }
      if (bloque('secours')) return { code: 429, corps: { ok: false, message: 'Trop d’essais. Réessayez dans un quart d’heure.' } };
      const a = crypto.createHash('sha256').update(donne).digest();
      const b = crypto.createHash('sha256').update(secours).digest();
      if (!crypto.timingSafeEqual(a, b)) { echec('secours'); return refus; }
      ECHECS.delete('secours');
      await modifier((d) => { noter(d, { id: 'secours', nom: 'Accès de secours' }, 'Connexion par l’accès de secours'); });
      return { code: 200, cookie: cookie(jeton_('secours', versionSecours()), DUREE), corps: { ok: true } };
    }

    if (bloque(adresse)) return { code: 429, corps: { ok: false, message: 'Trop d’essais pour cette adresse. Réessayez dans un quart d’heure.' } };
    const l = await lire(true);
    if (!l.ok) return { code: 503, corps: { ok: false, message: l.message } };
    const c = l.d.comptes.find((x) => x.courriel === adresse);
    // On hache meme sans compte : la duree ne dit pas si l'adresse existe.
    const bon = await verifier(donne, c ? c.empreinte : 'scrypt$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=');
    if (!c || !bon) { echec(adresse); return refus; }
    if (!c.actif) return { code: 403, corps: { ok: false, message: 'Ce compte est désactivé. Voyez avec un administrateur.' } };
    ECHECS.delete(adresse);
    /* La date de visite s'ecrit sur l'etat FRAIS : un compte desactive ou
       reinitialise a l'instant le reste, et la session s'ouvre avec la
       version la plus recente du compte. */
    let version = c.version;
    const r = await modifier((d) => {
      const x = d.comptes.find((y) => y.id === c.id);
      if (!x || !x.actif) return { annuler: 'coupe' };
      x.derniere = new Date().toISOString();
      noter(d, x, 'Connexion');
      version = x.version;
    });
    if (r.ok && r.annule) return { code: 403, corps: { ok: false, message: 'Ce compte est désactivé. Voyez avec un administrateur.' } };
    // Une date de visite perdue ne doit pas empecher d'entrer.
    return { code: 200, cookie: cookie(jeton_(c.id, version), DUREE), corps: { ok: true } };
  }

  const sortie = () => cookie('', 0);

  // ── Son propre mot de passe ──────────────────────────────────────────────
  async function changerMdp(qui, { ancien, nouveau }) {
    if (qui.secours) return { code: 403, corps: { ok: false, message: 'L’accès de secours se change dans Vercel (ADMIN_MDP).' } };
    const r = mdpRefuse(nouveau, { courriel: qui.courriel });
    if (r) return { code: 422, corps: { ok: false, champs: ['nouveau'], message: r } };
    if (String(nouveau) === String(ancien)) {
      return { code: 422, corps: { ok: false, champs: ['nouveau'], message: 'Choisissez un mot de passe différent de l’actuel.' } };
    }
    const empreinte = await hacher(nouveau);
    let version = 0;
    const w = await modifier(async (d) => {
      const c = d.comptes.find((x) => x.id === qui.id);
      if (!c) return { annuler: { code: 401, corps: { ok: false, message: 'Session expirée.' } } };
      if (!(await verifier(ancien, c.empreinte))) {
        return { annuler: { code: 422, corps: { ok: false, champs: ['ancien'], message: 'Le mot de passe actuel est incorrect.' } } };
      }
      c.empreinte = empreinte;
      c.provisoire = false;
      c.version = (c.version || 1) + 1;        // coupe les AUTRES sessions…
      noter(d, c, 'A changé son mot de passe');
      version = c.version;
    });
    if (!w.ok) return refusModif(w);
    if (w.annule) return w.valeur;
    // …et celle-ci repart avec la nouvelle version.
    return { code: 200, cookie: cookie(jeton_(qui.id, version), DUREE), corps: { ok: true } };
  }

  // ── Gestion des comptes (administrateurs) ────────────────────────────────
  const adminsActifs = (d, sauf) => d.comptes.filter((x) => x.role === 'admin' && x.actif && x.id !== sauf).length;
  const courrielValide = (v) => /^[^\s@]{1,64}@[^\s@]{1,190}\.[a-z]{2,24}$/i.test(v);
  const propre = (v, max) => String(v == null ? '' : v).replace(/\s+/g, ' ').trim().slice(0, max);

  async function lister() {
    const l = await lire(true);
    if (!l.ok) return { code: 503, corps: { ok: false, message: l.message } };
    return { code: 200, corps: { ok: true, comptes: l.d.comptes.map(public_),
      roles: Object.fromEntries(Object.entries(ROLES).map(([k, r]) => [k, { nom: r.nom, resume: r.resume }])) } };
  }

  /** Cree (sans id) ou modifie (nom, profil, actif) un compte. */
  async function enregistrer(qui, e) {
    const nom = propre(e.nom, 80);
    const role = ROLES[e.role] ? e.role : '';
    if (!nom) return { code: 422, corps: { ok: false, champs: ['nom'], message: 'Indiquez le nom de la personne.' } };
    if (!role) return { code: 422, corps: { ok: false, champs: ['role'], message: 'Choisissez un profil.' } };

    if (!e.id) {
      const courriel = propre(e.courriel, 254).toLowerCase();
      if (!courrielValide(courriel)) return { code: 422, corps: { ok: false, champs: ['courriel'], message: 'Cette adresse e-mail n’est pas valide.' } };
      // Tire et hache une seule fois : la modification peut se rejouer.
      const mdp = provisoire();
      const c = { id: crypto.randomUUID(), nom, courriel, role, actif: true, provisoire: true,
        empreinte: await hacher(mdp), version: 1, cree: new Date().toISOString(), creePar: qui.nom };
      const w = await modifier((d) => {
        if (d.comptes.some((x) => x.courriel === courriel)) {
          return { annuler: { code: 409, corps: { ok: false, champs: ['courriel'], message: 'Un compte existe déjà pour ' + courriel + '.' } } };
        }
        if (d.comptes.length >= 50) return { annuler: { code: 422, corps: { ok: false, message: '50 comptes au maximum.' } } };
        d.comptes.push(structuredClone(c));
        noter(d, qui, 'A créé le compte de ' + nom + ' (' + ROLES[role].nom + ')');
      });
      if (!w.ok) return refusModif(w);
      if (w.annule) return w.valeur;
      // Le seul moment ou le mot de passe provisoire existe en clair.
      return { code: 200, corps: { ok: true, compte: public_(c), provisoire: mdp } };
    }

    let rendu = null;
    const w = await modifier((d) => {
      const c = d.comptes.find((x) => x.id === e.id);
      if (!c) return { annuler: { code: 404, corps: { ok: false, message: 'Ce compte n’existe plus.' } } };
      const actif = e.actif !== false;
      if (c.id === qui.id && (role !== c.role || !actif)) {
        return { annuler: { code: 409, corps: { ok: false, message: 'Vous ne pouvez pas changer votre propre profil ni vous désactiver : demandez-le à un autre administrateur.' } } };
      }
      if (c.role === 'admin' && c.actif && (role !== 'admin' || !actif) && !adminsActifs(d, c.id)) {
        return { annuler: { code: 409, corps: { ok: false, message: 'C’est le dernier administrateur actif : nommez-en un autre d’abord.' } } };
      }
      const changements = [];
      if (nom !== c.nom) changements.push('nom');
      if (role !== c.role) changements.push('profil ' + ROLES[c.role].nom + ' → ' + ROLES[role].nom);
      if (actif !== c.actif) changements.push(actif ? 'réactivé' : 'désactivé');
      if (!changements.length) return { annuler: { code: 200, corps: { ok: true, compte: public_(c) } } };
      // Un profil retire ou un compte coupe ne doit pas survivre dans une session ouverte.
      if (role !== c.role || actif !== c.actif) c.version = (c.version || 1) + 1;
      Object.assign(c, { nom, role, actif });
      noter(d, qui, 'A modifié le compte de ' + nom + ' : ' + changements.join(', '));
      rendu = public_(c);
    });
    if (!w.ok) return refusModif(w);
    if (w.annule) return w.valeur;
    return { code: 200, corps: { ok: true, compte: rendu } };
  }

  async function reinitialiser(qui, id) {
    const mdp = provisoire();
    const empreinte = await hacher(mdp);
    let rendu = null;
    const w = await modifier((d) => {
      const c = d.comptes.find((x) => x.id === id);
      if (!c) return { annuler: { code: 404, corps: { ok: false, message: 'Ce compte n’existe plus.' } } };
      c.empreinte = empreinte;
      c.provisoire = true;
      c.version = (c.version || 1) + 1;
      noter(d, qui, 'A réinitialisé le mot de passe de ' + c.nom);
      rendu = public_(c);
    });
    if (!w.ok) return refusModif(w);
    if (w.annule) return w.valeur;
    return { code: 200, corps: { ok: true, compte: rendu, provisoire: mdp } };
  }

  async function supprimer(qui, id) {
    const w = await modifier((d) => {
      const c = d.comptes.find((x) => x.id === id);
      if (!c) return { annuler: { code: 404, corps: { ok: false, message: 'Ce compte n’existe plus.' } } };
      if (c.id === qui.id) return { annuler: { code: 409, corps: { ok: false, message: 'Vous ne pouvez pas supprimer votre propre compte.' } } };
      if (c.role === 'admin' && c.actif && !adminsActifs(d, c.id)) {
        return { annuler: { code: 409, corps: { ok: false, message: 'C’est le dernier administrateur actif : nommez-en un autre d’abord.' } } };
      }
      d.comptes = d.comptes.filter((x) => x.id !== id);
      noter(d, qui, 'A supprimé le compte de ' + c.nom + ' (' + c.courriel + ')');
    });
    if (!w.ok) return refusModif(w);
    if (w.annule) return w.valeur;
    return { code: 200, corps: { ok: true } };
  }

  /** Le journal des comptes (connexions, gestion des acces). */
  async function journal() {
    const l = await lire(true);
    return l.ok ? l.d.journal : [];
  }

  async function combien() {
    const l = await lire();
    return l.ok ? l.d.comptes.length : null;
  }

  return { session, entrer, sortie, changerMdp, lister, enregistrer, reinitialiser,
    supprimer, journal, combien };
}

module.exports = { ROLES, droitRequis, peut, creer, interne: { hacher, verifier, provisoire, mdpRefuse } };
