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
      'emplois', 'carnet', 'seo', 'galerie', 'parametres', 'utilisateurs', 'journal', 'compte'],
    droits: ['reservations', 'chambres', 'contenu', 'referencement', 'tarifs', 'reglages', 'comptes'],
  },
  reception: {
    nom: 'Réception',
    resume: 'Disponibilités, réservations et chambres.',
    vues: ['bord', 'disponibilites', 'chambres', 'compte'],
    droits: ['reservations', 'chambres'],
  },
  communication: {
    nom: 'Communication',
    resume: 'Événements, promotions, campagnes, recrutement, affiches et référencement.',
    vues: ['bord', 'evenements', 'promotions', 'campagnes', 'emplois', 'carnet', 'seo', 'galerie', 'compte'],
    /* « referencement » : l'agence de communication regle et PUBLIE ce que
       Google affiche (onglet Referencement). */
    droits: ['contenu', 'referencement'],
  },
  lecture: {
    nom: 'Lecture seule',
    resume: 'Consulte tout, ne modifie rien.',
    vues: ['bord', 'disponibilites', 'chambres', 'evenements', 'promotions', 'campagnes',
      'emplois', 'carnet', 'seo', 'galerie', 'compte'],
    droits: [],
  },
};

/* Le droit qu'exige chaque ecriture. `type` departage enregistrer,
   supprimer et ordonner, qui servent plusieurs collections. */
const DROIT_DU_TYPE = {
  fermeture: 'reservations', chambre: 'chambres',
  evenement: 'contenu', promotion: 'contenu', campagne: 'contenu', emploi: 'contenu',
  article: 'contenu',
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
    'seo-page': 'referencement', 'seo-redirection': 'referencement',
    'seo-redirection-retirer': 'referencement', 'publier-seo': 'referencement',
    'retablir-seo': 'referencement',
    // Remettre a zero la double authentification d'un autre (telephone perdu).
    'compte-2fa': 'comptes',
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

// ── La double authentification ─────────────────────────────────────────────
/* Un code a 6 chiffres qui change toutes les 30 secondes (TOTP, RFC 6238),
   calcule par une application du telephone — Google Authenticator,
   Microsoft Authenticator, Mots de passe de l'iPhone — a partir d'un secret
   partage une fois, par QR code. Pas de SMS : rien a payer, rien qui se
   detourne en clonant une puce, et ca marche sans reseau.

   Un mot de passe vole ne suffit plus : il faut aussi le telephone. */
const B32 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
function enBase32(buf) {
  let bits = 0, val = 0, out = '';
  for (const o of buf) {
    val = (val << 8) | o; bits += 8;
    while (bits >= 5) { out += B32[(val >>> (bits - 5)) & 31]; bits -= 5; }
  }
  if (bits > 0) out += B32[(val << (5 - bits)) & 31];
  return out;
}
function deBase32(s) {
  const t = String(s || '').toUpperCase().replace(/[^A-Z2-7]/g, '');
  let bits = 0, val = 0;
  const out = [];
  for (const c of t) {
    val = (val << 5) | B32.indexOf(c); bits += 5;
    if (bits >= 8) { out.push((val >>> (bits - 8)) & 255); bits -= 8; }
  }
  return Buffer.from(out);
}
const PAS_TOTP = 30_000;
/** Le code d'un pas de 30 secondes. */
function codeTotp(secret, pas) {
  const msg = Buffer.alloc(8);
  msg.writeBigUInt64BE(BigInt(pas));
  const h = crypto.createHmac('sha1', deBase32(secret)).update(msg).digest();
  const o = h[h.length - 1] & 15;
  return String((h.readUInt32BE(o) & 0x7fffffff) % 1e6).padStart(6, '0');
}
/**
 * Le code saisi vaut-il ? On accepte le pas courant et ses deux voisins
 * (30 secondes d'ecart d'horloge de chaque cote). Rend le pas reconnu, ou
 * null. `dejaVu` : le dernier pas accepte pour ce compte — un code deja
 * utilise ne rouvre pas une seconde session (rejeu).
 */
function verifierTotp(secret, code, dejaVu, maintenant) {
  const c = String(code || '').replace(/\D/g, '');
  if (c.length !== 6 || !secret) return null;
  const p = Math.floor((maintenant || Date.now()) / PAS_TOTP);
  for (const q of [p, p - 1, p + 1]) {
    if (dejaVu && q <= dejaVu) continue;
    if (crypto.timingSafeEqual(Buffer.from(codeTotp(secret, q)), Buffer.from(c))) return q;
  }
  return null;
}
/* Les codes de secours : dix, a usage unique, pour le jour ou le telephone
   est perdu. Lisibles et sans ambiguite, comme les mots de passe provisoires. */
function codesDeSecours() {
  const g = () => Array.from(crypto.randomBytes(4), (o) => ALPHABET_CODES[o % ALPHABET_CODES.length]).join('');
  return Array.from({ length: 10 }, () => g() + '-' + g());
}
const ALPHABET_CODES = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
const normaliserCode = (c) => String(c || '').toUpperCase().replace(/[^A-Z0-9]/g, '');

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
    /* `mfaAFaire` : la double authentification est obligatoire. Tant
       qu'elle n'est pas activee, la session n'ouvre que l'ecran qui
       l'active (admin.js). */
    return { id: c.id, nom: c.nom, courriel: c.courriel, role: c.role, provisoire: !!c.provisoire,
      mfa: !!c.mfa, mfaAFaire: !c.mfa, codesRestants: c.mfa ? (c.mfa.codes || []).length : 0 };
  }

  const public_ = (c) => ({ id: c.id, nom: c.nom, courriel: c.courriel, role: c.role,
    actif: c.actif, provisoire: !!c.provisoire, cree: c.cree, derniere: c.derniere || null,
    mfa: !!c.mfa });

  // ── Le secret de la double authentification, chiffre ──────────────────────
  /* Le secret d'un compte permet de fabriquer ses codes. Il est chiffre
     (AES-256-GCM) avec une cle tiree de la cle des sessions : une copie du
     fichier des comptes ne suffit pas a s'en servir. */
  const cleMfa = () => crypto.createHash('sha256').update('evn-mfa:' + secret).digest();
  function chiffrer(t) {
    const iv = crypto.randomBytes(12);
    const c = crypto.createCipheriv('aes-256-gcm', cleMfa(), iv);
    const x = Buffer.concat([c.update(String(t), 'utf8'), c.final()]);
    return [iv, c.getAuthTag(), x].map((b) => b.toString('base64url')).join('.');
  }
  function dechiffrer(v) {
    try {
      const [iv, tag, x] = String(v || '').split('.').map((b) => Buffer.from(b, 'base64url'));
      const d = crypto.createDecipheriv('aes-256-gcm', cleMfa(), iv);
      d.setAuthTag(tag);
      return Buffer.concat([d.update(x), d.final()]).toString('utf8');
    } catch (e) { return ''; }
  }
  // Les codes de secours ne sont gardes qu'en empreinte.
  const empreinteCode = (code) => crypto.createHmac('sha256', secret).update('secours:' + normaliserCode(code)).digest('hex');

  /* L'adresse IP accompagne les connexions et leurs echecs : c'est ce qui
     permet de dire d'ou vient une attaque. Seuls les administrateurs lisent
     le journal. */
  const noter = (d, qui, texte, ip) => d.journal.push(Object.assign({ t: new Date().toISOString(), u: qui.id, n: qui.nom, x: texte },
    ip ? { ip: String(ip).slice(0, 45) } : {}));

  // ── Connexion ────────────────────────────────────────────────────────────
  /* Les echecs comptent dans la BASE (evn_compteurs), pas dans la memoire
     d'une instance : Vercel en fait tourner plusieurs, et un compteur par
     instance se contournait en insistant. Cinq echecs en quinze minutes
     ferment l'adresse ; vingt depuis une meme adresse IP la ferment aussi,
     quelle que soit l'adresse e-mail essayee. */
  const FENETRE = 15 * 60_000, MAX_ECHECS = 5, MAX_IP = 20;
  const bloque = async (k) => (await magasin.valeur('echec:' + k)) >= (k.startsWith('ip:') ? MAX_IP : MAX_ECHECS);
  const echec = (k) => magasin.compter('echec:' + k, FENETRE);
  const remettre = (k) => magasin.effacer('echec:' + k);
  const TROP = { code: 429, corps: { ok: false, message: 'Trop d’essais. Réessayez dans un quart d’heure.' } };

  /* Le defi de la seconde etape : signe, cinq minutes, lie a la version du
     compte. Il prouve que le mot de passe a ete donne — rien de plus : sans
     le code, il n'ouvre rien. */
  const DUREE_DEFI = 300;
  function defi_(u, v) {
    const charge = Buffer.from(JSON.stringify({ k: 'mfa', u, v, e: Math.floor(Date.now() / 1000) + DUREE_DEFI })).toString('base64url');
    return charge + '.' + signe('defi:' + charge);
  }
  function lireDefi(d) {
    const [charge, sig] = String(d || '').split('.');
    if (!charge || !sig) return null;
    const a = Buffer.from(signe('defi:' + charge)), b = Buffer.from(sig);
    if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return null;
    try {
      const p = JSON.parse(Buffer.from(charge, 'base64url').toString());
      return p.k === 'mfa' && p.e > Math.floor(Date.now() / 1000) ? p : null;
    } catch (e) { return null; }
  }

  /**
   * Premiere etape : e-mail et mot de passe.
   *   { appareil, ip, ville } : ce que le journal retient de la connexion.
   * Rend un cookie (pas encore de double authentification : la session
   * n'ouvre que l'ecran qui l'active), ou { etape: 'code', defi }.
   */
  async function entrer({ courriel, mdp, appareil, ip, ville }) {
    if (!secret) {
      return { code: 503, corps: { ok: false, message: 'L’administration n’est pas configurée : '
        + 'définissez ADMIN_SECRET (ou ADMIN_MDP) dans les variables Vercel.' } };
    }
    const adresse = String(courriel || '').trim().toLowerCase();
    const donne = String(mdp || '');
    const refus = { code: 401, corps: { ok: false, message: 'E-mail ou mot de passe incorrect.' } };
    const ou = [appareil, ville].filter(Boolean).join(' · ');
    if (ip && await bloque('ip:' + ip)) return TROP;

    // L'acces de secours (developpeur) : e-mail vide, ADMIN_MDP.
    if (!adresse) {
      if (!secours) {
        return { code: 503, corps: { ok: false, message: "L'accès de secours n'est pas configuré "
          + '(ADMIN_MDP dans les variables Vercel). Entrez votre e-mail.' } };
      }
      if (await bloque('secours')) return TROP;
      const a = crypto.createHash('sha256').update(donne).digest();
      const b = crypto.createHash('sha256').update(secours).digest();
      if (!crypto.timingSafeEqual(a, b)) {
        await echec('secours'); if (ip) await echec('ip:' + ip);
        return refus;
      }
      await remettre('secours');
      await modifier((d) => { noter(d, { id: 'secours', nom: 'Accès de secours' }, 'Connexion par l’accès de secours' + (ou ? ' · ' + ou : ''), ip); });
      return { code: 200, cookie: cookie(jeton_('secours', versionSecours()), DUREE), corps: { ok: true } };
    }

    if (await bloque(adresse)) return { code: 429, corps: { ok: false, message: 'Trop d’essais pour cette adresse. Réessayez dans un quart d’heure.' } };
    const l = await lire(true);
    if (!l.ok) return { code: 503, corps: { ok: false, message: l.message } };
    const c = l.d.comptes.find((x) => x.courriel === adresse);
    // On hache meme sans compte : la duree ne dit pas si l'adresse existe.
    const bon = await verifier(donne, c ? c.empreinte : 'scrypt$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=');
    if (!c || !bon) {
      const n = await echec(adresse);
      if (ip) await echec('ip:' + ip);
      /* Les echecs sur un compte qui existe vont au journal : c'est la
         trace d'une attaque. Une adresse inconnue n'y va pas — sans quoi
         n'importe qui remplirait le journal. */
      if (c) {
        await modifier((d) => {
          noter(d, { id: c.id, nom: c.nom }, (n >= MAX_ECHECS ? 'Connexion bloquée 15 minutes après ' + n + ' échecs'
            : 'Échec de connexion (mot de passe)') + (ou ? ' · ' + ou : ''), ip);
        });
      }
      return refus;
    }
    if (!c.actif) return { code: 403, corps: { ok: false, message: 'Ce compte est désactivé. Voyez avec un administrateur.' } };
    await remettre(adresse);

    // La double authentification est activee : il faut le code.
    if (c.mfa) return { code: 200, corps: { ok: true, etape: 'code', defi: defi_(c.id, c.version) } };
    return ouvrir(c.id, 'Connexion' + (ou ? ' · ' + ou : ''), ip);
  }

  /** Ouvre la session : date de visite et journal sur l'etat FRAIS.
   *  `avant(x)` controle le compte frais : il rend { annuler } pour
   *  refuser, ou le texte du journal. */
  async function ouvrir(id, texte, ip, avant) {
    let version = null, restants = null;
    const r = await modifier((d) => {
      const x = d.comptes.find((y) => y.id === id);
      if (!x || !x.actif) return { annuler: 'coupe' };
      let t = texte;
      if (avant) { const v = avant(x); if (v && v.annuler) return v; t = v; }
      x.derniere = new Date().toISOString();
      noter(d, x, t, ip);
      version = x.version;
      restants = x.mfa ? (x.mfa.codes || []).length : null;
    });
    if (r.ok && r.annule) {
      return r.valeur && r.valeur.code ? r.valeur
        : { code: 403, corps: { ok: false, message: 'Ce compte est désactivé. Voyez avec un administrateur.' } };
    }
    if (!r.ok) return refusModif(r);
    return { code: 200, cookie: cookie(jeton_(id, version), DUREE), corps: { ok: true, codesRestants: restants } };
  }

  /**
   * Seconde etape : le code de l'application, ou un code de secours.
   * Cinq erreurs ferment le compte un quart d'heure, comme le mot de passe.
   */
  async function entrerCode({ defi, code, secoursCode, appareil, ip, ville }) {
    const p = lireDefi(defi);
    if (!p) return { code: 401, corps: { ok: false, expire: true, message: 'La vérification a expiré. Reprenez la connexion.' } };
    if (await bloque('mfa:' + p.u)) return TROP;
    const ou = [appareil, ville].filter(Boolean).join(' · ');
    let mauvais = false;
    const suite = ou ? ' · ' + ou : '';
    const r = await ouvrir(p.u, '', ip, (x) => {
      if (x.version !== p.v || !x.mfa) {
        return { annuler: { code: 401, corps: { ok: false, expire: true, message: 'La vérification a expiré. Reprenez la connexion.' } } };
      }
      if (secoursCode) {
        const h = empreinteCode(code);
        const i = (x.mfa.codes || []).indexOf(h);
        if (i < 0) { mauvais = true; return { annuler: { code: 401, corps: { ok: false, message: 'Ce code de secours n’est pas valable, ou a déjà servi.' } } }; }
        x.mfa.codes.splice(i, 1);
        return 'Connexion avec un code de secours (' + x.mfa.codes.length + ' restants)' + suite;
      } else {
        const pas = verifierTotp(dechiffrer(x.mfa.s), code, x.mfa.pas);
        if (!pas) { mauvais = true; return { annuler: { code: 401, corps: { ok: false, message: 'Code incorrect. Vérifiez l’heure du téléphone et réessayez.' } } }; }
        x.mfa.pas = pas;
        return 'Connexion' + suite;
      }
    });
    if (mauvais) {
      await echec('mfa:' + p.u);
      if (ip) await echec('ip:' + ip);
      return r;
    }
    if (r.code === 200) await remettre('mfa:' + p.u);
    return r;
  }

  // ── Activer, changer, remettre a zero ────────────────────────────────────
  const ISSUER = 'Hôtel Evannath';
  /** Prepare un secret : il n'est actif qu'une fois un premier code saisi. */
  async function mfaPreparer(qui, { code } = {}) {
    if (qui.secours) return { code: 403, corps: { ok: false, message: 'L’accès de secours n’a pas de double authentification.' } };
    const brut = enBase32(crypto.randomBytes(20));
    const w = await modifier((d) => {
      const c = d.comptes.find((x) => x.id === qui.id);
      if (!c) return { annuler: { code: 401, corps: { ok: false, message: 'Session expirée.' } } };
      /* Changer de telephone, c'est remplacer le secret : il faut alors le
         code ACTUEL. Une session laissee ouverte sur un poste ne suffit pas
         a detourner la double authentification. */
      if (c.mfa && !verifierTotp(dechiffrer(c.mfa.s), code, null)) {
        return { annuler: { code: 422, corps: { ok: false, champs: ['code'], message: 'Entrez d’abord le code actuel de votre application.' } } };
      }
      c.mfa_attente = { s: chiffrer(brut), t: new Date().toISOString() };
    });
    if (!w.ok) return refusModif(w);
    if (w.annule) return w.valeur;
    const label = encodeURIComponent(ISSUER + ':' + qui.courriel);
    const uri = 'otpauth://totp/' + label + '?secret=' + brut + '&issuer=' + encodeURIComponent(ISSUER)
      + '&algorithm=SHA1&digits=6&period=30';
    return { code: 200, corps: { ok: true, secret: brut, uri } };
  }

  /** Confirme le secret prepare par un premier code, et rend les codes de secours. */
  async function mfaActiver(qui, { code }) {
    if (qui.secours) return { code: 403, corps: { ok: false, message: 'L’accès de secours n’a pas de double authentification.' } };
    const codes = codesDeSecours();
    let version = 0;
    const w = await modifier((d) => {
      const c = d.comptes.find((x) => x.id === qui.id);
      if (!c) return { annuler: { code: 401, corps: { ok: false, message: 'Session expirée.' } } };
      const att = c.mfa_attente;
      if (!att || Date.now() - Date.parse(att.t) > 15 * 60_000) {
        return { annuler: { code: 409, corps: { ok: false, message: 'Le QR code a expiré : recommencez l’activation.' } } };
      }
      const pas = verifierTotp(dechiffrer(att.s), code, null);
      if (!pas) return { annuler: { code: 422, corps: { ok: false, champs: ['code'], message: 'Code incorrect. Vérifiez que l’heure du téléphone est à jour.' } } };
      const change = !!c.mfa;
      c.mfa = { s: att.s, depuis: new Date().toISOString(), pas, codes: codes.map(empreinteCode) };
      delete c.mfa_attente;
      // Les autres sessions ont ete ouvertes sans ce telephone : elles tombent.
      c.version = (c.version || 1) + 1;
      noter(d, c, change ? 'A changé de téléphone pour la double authentification' : 'A activé la double authentification');
      version = c.version;
    });
    if (!w.ok) return refusModif(w);
    if (w.annule) return w.valeur;
    return { code: 200, cookie: cookie(jeton_(qui.id, version), DUREE), corps: { ok: true, codes } };
  }

  /** De nouveaux codes de secours (les anciens ne valent plus). Demande le code actuel. */
  async function mfaCodes(qui, { code }) {
    const codes = codesDeSecours();
    const w = await modifier((d) => {
      const c = d.comptes.find((x) => x.id === qui.id);
      if (!c || !c.mfa) return { annuler: { code: 409, corps: { ok: false, message: 'La double authentification n’est pas activée.' } } };
      const pas = verifierTotp(dechiffrer(c.mfa.s), code, c.mfa.pas);
      if (!pas) return { annuler: { code: 422, corps: { ok: false, champs: ['code'], message: 'Code incorrect.' } } };
      c.mfa.pas = pas;
      c.mfa.codes = codes.map(empreinteCode);
      noter(d, c, 'A renouvelé ses codes de secours');
    });
    if (!w.ok) return refusModif(w);
    if (w.annule) return w.valeur;
    return { code: 200, corps: { ok: true, codes } };
  }

  /** Telephone perdu, plus de codes : un administrateur remet a zero. */
  async function mfaReinitialiser(qui, id) {
    let rendu = null;
    const w = await modifier((d) => {
      const c = d.comptes.find((x) => x.id === id);
      if (!c) return { annuler: { code: 404, corps: { ok: false, message: 'Ce compte n’existe plus.' } } };
      if (c.id === qui.id) return { annuler: { code: 409, corps: { ok: false, message: 'Pour changer de téléphone, passez par « Mon compte ».' } } };
      delete c.mfa; delete c.mfa_attente;
      c.version = (c.version || 1) + 1;
      noter(d, qui, 'A remis à zéro la double authentification de ' + c.nom);
      rendu = public_(c);
    });
    if (!w.ok) return refusModif(w);
    if (w.annule) return w.valeur;
    return { code: 200, corps: { ok: true, compte: rendu } };
  }

  /** Ferme toutes les AUTRES sessions du compte. */
  async function sessionsFermer(qui) {
    if (qui.secours) return { code: 403, corps: { ok: false, message: 'L’accès de secours se coupe en changeant ADMIN_MDP dans Vercel.' } };
    let version = 0;
    const w = await modifier((d) => {
      const c = d.comptes.find((x) => x.id === qui.id);
      if (!c) return { annuler: { code: 401, corps: { ok: false, message: 'Session expirée.' } } };
      c.version = (c.version || 1) + 1;
      noter(d, c, 'A déconnecté ses autres appareils');
      version = c.version;
    });
    if (!w.ok) return refusModif(w);
    if (w.annule) return w.valeur;
    return { code: 200, cookie: cookie(jeton_(qui.id, version), DUREE), corps: { ok: true } };
  }

  /** Ses propres connexions et echecs recents, pour « Mon compte ». */
  async function mesConnexions(qui) {
    const l = await lire(true);
    if (!l.ok) return { code: 503, corps: { ok: false, message: l.message } };
    const liste = l.d.journal.filter((x) => x.u === qui.id && /^(Connexion|Échec de connexion)/.test(x.x))
      .slice(-12).reverse().map((x) => ({ t: x.t, x: x.x }));
    return { code: 200, corps: { ok: true, connexions: liste } };
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

  return { session, entrer, entrerCode, sortie, changerMdp, lister, enregistrer, reinitialiser,
    supprimer, journal, combien, mfaPreparer, mfaActiver, mfaCodes, mfaReinitialiser,
    sessionsFermer, mesConnexions };
}

module.exports = { ROLES, droitRequis, peut, creer,
  interne: { hacher, verifier, provisoire, mdpRefuse, codeTotp, verifierTotp, enBase32, deBase32 } };
