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
 * STOCKAGE : un fichier a part (evannath/comptes), jamais melange aux
 * donnees du site. Une connexion ecrit la date de derniere visite : dans le
 * fichier principal, elle aurait pu ecraser une reservation enregistree au
 * meme instant. Les mots de passe n'y sont jamais en clair : scrypt, sel
 * propre a chaque compte.
 */

const crypto = require('crypto');

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
  let memoire = null;               // sans stockage durable : la memoire de l'instance
  let cache = null, cacheA = 0;

  async function lire(frais) {
    if (!jeton) {
      if (!memoire) memoire = VIDE();
      return { ok: true, d: structuredClone(memoire) };
    }
    if (!frais && cache && Date.now() - cacheA < CACHE_MS) return { ok: true, d: structuredClone(cache) };
    try {
      const { list } = await import('@vercel/blob');
      const { blobs } = await list({ prefix: PREFIXE, token: jeton });
      if (!blobs.length) { cache = VIDE(); cacheA = Date.now(); return { ok: true, d: VIDE() }; }
      const versions = blobs.slice().sort((x, y) => new Date(y.uploadedAt) - new Date(x.uploadedAt));
      for (const b of versions) {
        try {
          const r = await fetch(b.url, { cache: 'no-store' });
          if (r.ok) {
            const d = await r.json();
            d.comptes = d.comptes || []; d.journal = d.journal || [];
            cache = d; cacheA = Date.now();
            return { ok: true, d: structuredClone(d) };
          }
        } catch (e) { /* version suivante */ }
      }
      return { ok: false, message: 'Le fichier des comptes est illisible pour l’instant. Réessayez dans un instant.' };
    } catch (e) {
      return { ok: false, message: 'Le stockage ne répond pas : ' + e.message };
    }
  }

  async function ecrire(d) {
    d.journal = (d.journal || []).slice(-JOURNAL_MAX);
    if (!jeton) { memoire = structuredClone(d); return { ok: true }; }
    try {
      const { put, list, del } = await import('@vercel/blob');
      const avant = await list({ prefix: PREFIXE, token: jeton });
      await put(PREFIXE + '.json', JSON.stringify(d), {
        access: 'public', token: jeton, contentType: 'application/json',
      });
      cache = structuredClone(d); cacheA = Date.now();
      const surplus = avant.blobs.slice()
        .sort((x, y) => new Date(y.uploadedAt) - new Date(x.uploadedAt))
        .slice(GARDE - 1).map((b) => b.url);
      if (surplus.length) { try { await del(surplus, { token: jeton }); } catch (e) { /* menage */ } }
      return { ok: true };
    } catch (e) {
      return { ok: false, message: 'L’enregistrement des comptes a échoué : ' + e.message };
    }
  }

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
      const l = await lire(true);
      if (l.ok) { noter(l.d, { id: 'secours', nom: 'Accès de secours' }, 'Connexion par l’accès de secours'); await ecrire(l.d); }
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
    c.derniere = new Date().toISOString();
    noter(l.d, c, 'Connexion');
    await ecrire(l.d);   // une date de visite perdue ne doit pas empecher d'entrer
    return { code: 200, cookie: cookie(jeton_(c.id, c.version), DUREE), corps: { ok: true } };
  }

  const sortie = () => cookie('', 0);

  // ── Son propre mot de passe ──────────────────────────────────────────────
  async function changerMdp(qui, { ancien, nouveau }) {
    if (qui.secours) return { code: 403, corps: { ok: false, message: 'L’accès de secours se change dans Vercel (ADMIN_MDP).' } };
    const l = await lire(true);
    if (!l.ok) return { code: 503, corps: { ok: false, message: l.message } };
    const c = l.d.comptes.find((x) => x.id === qui.id);
    if (!c) return { code: 401, corps: { ok: false, message: 'Session expirée.' } };
    if (!(await verifier(ancien, c.empreinte))) {
      return { code: 422, corps: { ok: false, champs: ['ancien'], message: 'Le mot de passe actuel est incorrect.' } };
    }
    const r = mdpRefuse(nouveau, c);
    if (r) return { code: 422, corps: { ok: false, champs: ['nouveau'], message: r } };
    if (String(nouveau) === String(ancien)) {
      return { code: 422, corps: { ok: false, champs: ['nouveau'], message: 'Choisissez un mot de passe différent de l’actuel.' } };
    }
    c.empreinte = await hacher(nouveau);
    c.provisoire = false;
    c.version = (c.version || 1) + 1;        // coupe les AUTRES sessions…
    noter(l.d, c, 'A changé son mot de passe');
    const w = await ecrire(l.d);
    if (!w.ok) return { code: 502, corps: { ok: false, message: w.message } };
    // …et celle-ci repart avec la nouvelle version.
    return { code: 200, cookie: cookie(jeton_(c.id, c.version), DUREE), corps: { ok: true } };
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
    const l = await lire(true);
    if (!l.ok) return { code: 503, corps: { ok: false, message: l.message } };
    const d = l.d;
    const nom = propre(e.nom, 80);
    const role = ROLES[e.role] ? e.role : '';
    if (!nom) return { code: 422, corps: { ok: false, champs: ['nom'], message: 'Indiquez le nom de la personne.' } };
    if (!role) return { code: 422, corps: { ok: false, champs: ['role'], message: 'Choisissez un profil.' } };

    if (!e.id) {
      const courriel = propre(e.courriel, 254).toLowerCase();
      if (!courrielValide(courriel)) return { code: 422, corps: { ok: false, champs: ['courriel'], message: 'Cette adresse e-mail n’est pas valide.' } };
      if (d.comptes.some((x) => x.courriel === courriel)) {
        return { code: 409, corps: { ok: false, champs: ['courriel'], message: 'Un compte existe déjà pour ' + courriel + '.' } };
      }
      if (d.comptes.length >= 50) return { code: 422, corps: { ok: false, message: '50 comptes au maximum.' } };
      const mdp = provisoire();
      const c = { id: crypto.randomUUID(), nom, courriel, role, actif: true, provisoire: true,
        empreinte: await hacher(mdp), version: 1, cree: new Date().toISOString(), creePar: qui.nom };
      d.comptes.push(c);
      noter(d, qui, 'A créé le compte de ' + nom + ' (' + ROLES[role].nom + ')');
      const w = await ecrire(d);
      if (!w.ok) return { code: 502, corps: { ok: false, message: w.message } };
      // Le seul moment ou le mot de passe provisoire existe en clair.
      return { code: 200, corps: { ok: true, compte: public_(c), provisoire: mdp } };
    }

    const c = d.comptes.find((x) => x.id === e.id);
    if (!c) return { code: 404, corps: { ok: false, message: 'Ce compte n’existe plus.' } };
    const actif = e.actif !== false;
    if (c.id === qui.id && (role !== c.role || !actif)) {
      return { code: 409, corps: { ok: false, message: 'Vous ne pouvez pas changer votre propre profil ni vous désactiver : demandez-le à un autre administrateur.' } };
    }
    if (c.role === 'admin' && c.actif && (role !== 'admin' || !actif) && !adminsActifs(d, c.id)) {
      return { code: 409, corps: { ok: false, message: 'C’est le dernier administrateur actif : nommez-en un autre d’abord.' } };
    }
    const changements = [];
    if (nom !== c.nom) changements.push('nom');
    if (role !== c.role) changements.push('profil ' + ROLES[c.role].nom + ' → ' + ROLES[role].nom);
    if (actif !== c.actif) changements.push(actif ? 'réactivé' : 'désactivé');
    if (!changements.length) return { code: 200, corps: { ok: true, compte: public_(c) } };
    // Un profil retire ou un compte coupe ne doit pas survivre dans une session ouverte.
    if (role !== c.role || actif !== c.actif) c.version = (c.version || 1) + 1;
    Object.assign(c, { nom, role, actif });
    noter(d, qui, 'A modifié le compte de ' + nom + ' : ' + changements.join(', '));
    const w = await ecrire(d);
    if (!w.ok) return { code: 502, corps: { ok: false, message: w.message } };
    return { code: 200, corps: { ok: true, compte: public_(c) } };
  }

  async function reinitialiser(qui, id) {
    const l = await lire(true);
    if (!l.ok) return { code: 503, corps: { ok: false, message: l.message } };
    const c = l.d.comptes.find((x) => x.id === id);
    if (!c) return { code: 404, corps: { ok: false, message: 'Ce compte n’existe plus.' } };
    const mdp = provisoire();
    c.empreinte = await hacher(mdp);
    c.provisoire = true;
    c.version = (c.version || 1) + 1;
    noter(l.d, qui, 'A réinitialisé le mot de passe de ' + c.nom);
    const w = await ecrire(l.d);
    if (!w.ok) return { code: 502, corps: { ok: false, message: w.message } };
    return { code: 200, corps: { ok: true, compte: public_(c), provisoire: mdp } };
  }

  async function supprimer(qui, id) {
    const l = await lire(true);
    if (!l.ok) return { code: 503, corps: { ok: false, message: l.message } };
    const c = l.d.comptes.find((x) => x.id === id);
    if (!c) return { code: 404, corps: { ok: false, message: 'Ce compte n’existe plus.' } };
    if (c.id === qui.id) return { code: 409, corps: { ok: false, message: 'Vous ne pouvez pas supprimer votre propre compte.' } };
    if (c.role === 'admin' && c.actif && !adminsActifs(l.d, c.id)) {
      return { code: 409, corps: { ok: false, message: 'C’est le dernier administrateur actif : nommez-en un autre d’abord.' } };
    }
    l.d.comptes = l.d.comptes.filter((x) => x.id !== id);
    noter(l.d, qui, 'A supprimé le compte de ' + c.nom + ' (' + c.courriel + ')');
    const w = await ecrire(l.d);
    if (!w.ok) return { code: 502, corps: { ok: false, message: w.message } };
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
