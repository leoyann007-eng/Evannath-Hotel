/* Administration — evenements, promotions, medias.
 *
 * Une seule fonction pour tout l'espace d'administration. Elle sert aussi les
 * donnees publiques en lecture : la page Offres & Evenements les recupere au
 * chargement, ce qui evite de reconstruire le site a chaque affiche publiee.
 *
 * STOCKAGE — deux modes, decides par la presence du jeton :
 *
 *   BLOB_READ_WRITE_TOKEN present  ->  Vercel Blob. Les donnees survivent aux
 *                                      redeploiements. C'est le mode reel.
 *   absent                         ->  memoire de l'instance. Tout se perd au
 *                                      redemarrage. Suffisant pour montrer
 *                                      l'outil, jamais pour s'en servir.
 *
 * Le mode est annonce dans /api/admin?a=etat : l'interface le dit en clair
 * plutot que de laisser croire que les donnees sont conservees.
 *
 * AUTHENTIFICATION — un mot de passe, defini par ADMIN_MDP, echange contre un
 * cookie signe. Ce n'est pas un systeme multi-utilisateurs : c'est le strict
 * necessaire pour que l'acces ne soit pas ouvert a tous. La gestion de
 * plusieurs comptes viendra avec le stockage reel.
 */

const crypto = require('crypto');

const MDP = process.env.ADMIN_MDP || '';
const SECRET = process.env.ADMIN_SECRET || MDP || 'evannath-sans-secret';
const JETON_BLOB = process.env.BLOB_READ_WRITE_TOKEN || '';
const DUREE = 12 * 3600;                     // 12 h de session

// ── Stockage ───────────────────────────────────────────────────────────────
const CLE = 'evannath/donnees.json';
let memoire = null;                          // mode demonstration

const VIDE = { evenements: [], promotions: [], medias: [], maj: null };

async function lire() {
  if (!JETON_BLOB) return memoire || (memoire = structuredClone(VIDE));
  try {
    const { list } = await import('@vercel/blob');
    const { blobs } = await list({ prefix: CLE, token: JETON_BLOB });
    if (!blobs.length) return structuredClone(VIDE);
    const r = await fetch(blobs[0].url, { cache: 'no-store' });
    return r.ok ? await r.json() : structuredClone(VIDE);
  } catch (e) {
    return structuredClone(VIDE);
  }
}

/** Rend une erreur explicite plutot que de laisser croire a un enregistrement.
 *  Un echec silencieux ici, c'est une affiche qu'on croit publiee et qui ne
 *  l'est pas — le pire des defauts pour cet outil. */
async function ecrire(donnees) {
  donnees.maj = new Date().toISOString();
  if (!JETON_BLOB) { memoire = donnees; return { ok: true }; }
  try {
    const { put } = await import('@vercel/blob');
    await put(CLE, JSON.stringify(donnees), {
      access: 'public', token: JETON_BLOB,
      contentType: 'application/json', addRandomSuffix: false,
    });
    return { ok: true };
  } catch (e) {
    return {
      ok: false,
      message: /Cannot find module/.test(String(e && e.message))
        ? "Le paquet @vercel/blob n'est pas installé. Ajoutez-le aux dépendances."
        : "Le stockage n'a pas accepté l'enregistrement : " + String(e && e.message).slice(0, 120),
    };
  }
}

// ── Session ────────────────────────────────────────────────────────────────
const signe = (v) => crypto.createHmac('sha256', SECRET).update(v).digest('hex').slice(0, 32);

function creerJeton() {
  const exp = Math.floor(Date.now() / 1000) + DUREE;
  return exp + '.' + signe(String(exp));
}

function jetonValide(j) {
  if (!j || !j.includes('.')) return false;
  const [exp, sig] = j.split('.');
  if (signe(exp) !== sig) return false;
  return Number(exp) > Math.floor(Date.now() / 1000);
}

function cookieSession(req) {
  const c = req.headers.cookie || '';
  const m = c.match(/(?:^|;\s*)evn_adm=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : '';
}

const authentifie = (req) => jetonValide(cookieSession(req));

// ── Validation ─────────────────────────────────────────────────────────────
const propre = (v, max) => String(v == null ? '' : v).replace(/\s+/g, ' ').trim().slice(0, max);

const LIMITES = {
  titre: 80, accent: 40, categorie: 60, badge: 40, texte: 400,
  cta: 40, href: 200, fond: 120, quand: 60, libelle: 30, valeur: 60,
};

/** Une entree nettoyee. On refuse plutot que de corriger en silence :
 *  un evenement sans titre ni date n'a rien a faire en ligne. */
function nettoyer(e, type) {
  const o = {
    id: propre(e.id, 40) || crypto.randomUUID(),
    titre: propre(e.titre, LIMITES.titre),
    accent: propre(e.accent, LIMITES.accent),
    categorie: propre(e.categorie, LIMITES.categorie),
    badge: propre(e.badge, LIMITES.badge),
    texte: propre(e.texte, LIMITES.texte),
    cta: propre(e.cta, LIMITES.cta) || 'En savoir plus',
    href: propre(e.href, LIMITES.href) || '#demande',
    // Soit un nom de photo du site, soit l'URL d'une affiche televersee.
    fond: propre(e.fond, 400),
    // 'affiche' : le visuel est montre ENTIER, a cote du texte. C'est le cas
    //   des carres publies sur les reseaux, qui portent deja l'information.
    // 'fond'    : une photo large, recadree derriere le texte.
    format: e.format === 'affiche' ? 'affiche' : 'fond',
    quand: propre(e.quand, LIMITES.quand),
    fin: /^\d{4}-\d{2}-\d{2}$/.test(e.fin || '') ? e.fin : null,
    publie: e.publie !== false,
    infos: Array.isArray(e.infos)
      ? e.infos.slice(0, 4)
          .map((i) => [propre(i[0], LIMITES.libelle), propre(i[1], LIMITES.valeur)])
          .filter((i) => i[0] && i[1])
      : [],
  };
  if (type === 'promotion') {
    o.reduction = propre(e.reduction, 20);
    o.code = propre(e.code, 24).toUpperCase();
  }
  // Seul le titre est exige. Le texte ne l'est pas : quand l'evenement est
  // annonce par une affiche, celle-ci porte deja les dates, le tarif et le
  // telephone. Le redemander serait faire saisir deux fois la meme chose.
  const manque = [];
  if (!o.titre) manque.push('titre');
  return { objet: o, manque };
}

// ── Reponses ───────────────────────────────────────────────────────────────
const json = (res, code, corps) => {
  res.setHeader('Cache-Control', 'no-store');
  return res.status(code).json(corps);
};

module.exports = async function handler(req, res) {
  const action = (req.query.a || '').toString();

  // ── Lecture publique : ce que la page Offres & Evenements consomme ──────
  if (action === 'public') {
    const d = await lire();
    // Aucun cache. Une affiche publiee doit apparaitre a la seconde : un
    // cache d'une minute, c'est une minute a se demander si l'enregistrement
    // a fonctionne. La reponse fait quelques centaines d'octets, la depense
    // est negligeable.
    res.setHeader('Cache-Control', 'no-store, max-age=0');
    const visible = (x) => x.publie !== false;
    return res.status(200).json({
      evenements: (d.evenements || []).filter(visible),
      promotions: (d.promotions || []).filter(visible),
      maj: d.maj,
    });
  }

  // ── Connexion ───────────────────────────────────────────────────────────
  if (action === 'entrer') {
    if (req.method !== 'POST') return json(res, 405, { ok: false });
    if (!MDP) {
      return json(res, 503, {
        ok: false,
        message: "L'administration n'est pas encore configurée. "
               + 'Définissez ADMIN_MDP dans les variables Vercel.',
      });
    }
    let corps = req.body;
    if (typeof corps === 'string') { try { corps = JSON.parse(corps); } catch { corps = {}; } }
    const donne = String((corps && corps.mdp) || '');
    // Comparaison a duree constante : une comparaison naive laisse deviner le
    // mot de passe caractere par caractere.
    const a = crypto.createHash('sha256').update(donne).digest();
    const b = crypto.createHash('sha256').update(MDP).digest();
    if (!crypto.timingSafeEqual(a, b)) {
      return json(res, 401, { ok: false, message: 'Mot de passe incorrect.' });
    }
    res.setHeader('Set-Cookie',
      `evn_adm=${encodeURIComponent(creerJeton())}; Path=/; HttpOnly; SameSite=Lax; Secure; Max-Age=${DUREE}`);
    return json(res, 200, { ok: true });
  }

  if (action === 'sortir') {
    res.setHeader('Set-Cookie', 'evn_adm=; Path=/; HttpOnly; SameSite=Lax; Secure; Max-Age=0');
    return json(res, 200, { ok: true });
  }

  // ── Tout le reste demande une session ───────────────────────────────────
  if (!authentifie(req)) return json(res, 401, { ok: false, message: 'Session expirée.' });

  if (action === 'etat') {
    const d = await lire();
    return json(res, 200, {
      ok: true,
      stockage: JETON_BLOB ? 'durable' : 'demonstration',
      evenements: (d.evenements || []).length,
      promotions: (d.promotions || []).length,
      medias: (d.medias || []).length,
      maj: d.maj,
    });
  }

  if (action === 'tout') return json(res, 200, { ok: true, donnees: await lire() });

  /* Televersement d'une affiche.
     L'etablissement communique par des visuels carres qui portent deja
     l'information — dates, tarif, telephone. C'est ce fichier-la qu'il faut
     pouvoir deposer, pas une photo choisie dans la banque du site. */
  if (action === 'televerser') {
    if (req.method !== 'POST') return json(res, 405, { ok: false });
    if (!JETON_BLOB) {
      return json(res, 503, { ok: false,
        message: 'Le stockage durable est nécessaire pour déposer une affiche.' });
    }
    let corps = req.body;
    if (typeof corps === 'string') { try { corps = JSON.parse(corps); } catch { corps = {}; } }
    const donnee = String((corps && corps.fichier) || '');
    const m = donnee.match(/^data:(image\/(png|jpeg|jpg|webp));base64,(.+)$/);
    if (!m) return json(res, 422, { ok: false, message: 'Formats acceptés : JPEG, PNG, WebP.' });
    const octets = Buffer.from(m[3], 'base64');
    if (octets.length > 4 * 1024 * 1024) {
      return json(res, 413, { ok: false,
        message: 'Affiche trop lourde : ' + Math.round(octets.length / 1048576) + ' Mo pour 4 Mo au maximum.' });
    }
    const ext = m[2] === 'jpg' ? 'jpeg' : m[2];
    const nom = 'evannath/affiches/' + Date.now() + '-'
              + crypto.randomBytes(4).toString('hex') + '.' + ext;
    try {
      const { put } = await import('@vercel/blob');
      const r = await put(nom, octets, {
        access: 'public', token: JETON_BLOB, contentType: m[1],
      });
      return json(res, 200, { ok: true, url: r.url });
    } catch (e) {
      return json(res, 502, { ok: false,
        message: "Le dépôt a échoué : " + String(e && e.message).slice(0, 120) });
    }
  }

  if (action === 'enregistrer') {
    if (req.method !== 'POST') return json(res, 405, { ok: false });
    let corps = req.body;
    if (typeof corps === 'string') { try { corps = JSON.parse(corps); } catch { corps = {}; } }
    const type = corps.type === 'promotion' ? 'promotions' : 'evenements';
    const { objet, manque } = nettoyer(corps.entree || {}, corps.type);
    if (manque.length) {
      return json(res, 422, { ok: false, champs: manque, message: 'Il manque le ' + manque.join(' et le ') + '.' });
    }
    const d = await lire();
    d[type] = d[type] || [];
    const i = d[type].findIndex((x) => x.id === objet.id);
    if (i >= 0) d[type][i] = objet; else d[type].push(objet);
    const w = await ecrire(d);
    if (!w.ok) return json(res, 502, { ok: false, message: w.message });
    return json(res, 200, { ok: true, entree: objet });
  }

  if (action === 'supprimer') {
    if (req.method !== 'POST') return json(res, 405, { ok: false });
    let corps = req.body;
    if (typeof corps === 'string') { try { corps = JSON.parse(corps); } catch { corps = {}; } }
    const type = corps.type === 'promotion' ? 'promotions' : 'evenements';
    const d = await lire();
    d[type] = (d[type] || []).filter((x) => x.id !== corps.id);
    const w = await ecrire(d);
    if (!w.ok) return json(res, 502, { ok: false, message: w.message });
    return json(res, 200, { ok: true });
  }

  if (action === 'ordonner') {
    if (req.method !== 'POST') return json(res, 405, { ok: false });
    let corps = req.body;
    if (typeof corps === 'string') { try { corps = JSON.parse(corps); } catch { corps = {}; } }
    const type = corps.type === 'promotion' ? 'promotions' : 'evenements';
    const d = await lire();
    const par = new Map((d[type] || []).map((x) => [x.id, x]));
    d[type] = (corps.ordre || []).map((id) => par.get(id)).filter(Boolean);
    const w = await ecrire(d);
    if (!w.ok) return json(res, 502, { ok: false, message: w.message });
    return json(res, 200, { ok: true });
  }

  return json(res, 400, { ok: false, message: 'Action inconnue.' });
};
