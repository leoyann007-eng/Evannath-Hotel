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

/* La version du deploiement. Vercel la fournit ; en local elle est fixee au
   demarrage du serveur, ce qui suffit : redemarrer simule un deploiement.

   Elle sert a une seule chose, mais elle est necessaire : une page
   d administration ouverte AVANT un deploiement continue d executer l ancien
   code. On coche une case que l ancienne version ne connait pas, on publie,
   rien ne se passe, et personne ne peut le savoir. C est arrive. */
const VERSION = (process.env.VERCEL_GIT_COMMIT_SHA
  || process.env.VERSION || 'local-' + Date.now()).slice(0, 12);

const MDP = process.env.ADMIN_MDP || '';
const SECRET = process.env.ADMIN_SECRET || MDP || 'evannath-sans-secret';
/* Connecter un magasin Blob a un projet permet de choisir un prefixe de
   variables : le jeton s'appelle alors MONPREFIXE_READ_WRITE_TOKEN. Chercher
   le seul nom BLOB_READ_WRITE_TOKEN laissait le stockage invisible alors qu'il
   etait bien branche. On reconnait le jeton a sa forme, quel que soit son nom. */
function trouverJeton() {
  if (process.env.BLOB_READ_WRITE_TOKEN)
    return { valeur: process.env.BLOB_READ_WRITE_TOKEN, nom: 'BLOB_READ_WRITE_TOKEN' };
  for (const nom of Object.keys(process.env)) {
    const v = process.env[nom] || '';
    if (/READ_WRITE_TOKEN$/.test(nom) && /^vercel_blob_rw_/.test(v))
      return { valeur: v, nom };
  }
  return { valeur: '', nom: '' };
}
const { valeur: JETON_BLOB, nom: NOM_JETON } = trouverJeton();
const DUREE = 12 * 3600;                     // 12 h de session

// ── Stockage ───────────────────────────────────────────────────────────────
// Le fichier de donnees porte un suffixe aleatoire, ajoute par Blob.
// Ecrit a une adresse fixe, son URL serait devinable — et publique, puisque
// le magasin l'est : n'importe qui lirait tout, brouillons non publies
// compris. On le retrouve par prefixe, cote serveur, jeton en main.
const PREFIXE = 'evannath/donnees';
/* Combien d exemplaires du fichier on conserve. Il pese deux kilo-octets :
   en garder dix coute vingt kilo-octets, et transforme une catastrophe en un
   retour en arriere. Le 3 septembre 2026, une ecriture par-dessus une lecture
   en echec a efface deux affiches ; il n existait alors qu un seul
   exemplaire, et rien derriere. */
const GARDE = 10;
let memoire = null;                          // mode demonstration

const VIDE = { evenements: [], promotions: [], campagnes: [], medias: [],
               maj: null };

/* La derniere lecture en echec, en clair. Vide quand tout va bien.
   Sans elle, une lecture qui echoue rendait exactement la meme chose qu un
   magasin vide : zero evenement, zero promotion, zero campagne, et pas un
   mot. On croit alors avoir tout perdu — alors que les donnees dorment
   intactes de l autre cote d un jeton qui ne repond plus. */
let PANNE = '';
// Combien de versions du fichier coexistent. Une seule en temps normal.
let FICHIERS = 0;

async function lire() {
  if (!JETON_BLOB) return memoire || (memoire = structuredClone(VIDE));
  try {
    const { list } = await import('@vercel/blob');
    const { blobs } = await list({ prefix: PREFIXE, token: JETON_BLOB });
    PANNE = '';
    FICHIERS = blobs.length;
    if (!blobs.length) return structuredClone(VIDE);
    /* Si un menage a echoue, plusieurs versions coexistent : on prend la plus
       recente. Mais l inventaire est a consistance differee — il rend parfois
       une version tout juste supprimee, dont l adresse repond 403. On essaie
       donc les suivantes au lieu d abandonner a la premiere : abandonner
       revenait a dire « rien a lire », et le 403 tombait au hasard des
       instants, une fois sur deux. */
    const versions = blobs.slice().sort(
      (x, y) => new Date(y.uploadedAt) - new Date(x.uploadedAt));
    let dernier = '';
    for (let i = 0; i < versions.length; i++) {
      const b = versions[i];
      try {
        const r = await fetch(b.url, { cache: 'no-store' });
        if (r.ok) {
          /* Se rabattre sur une version anterieure sauve l affichage, mais ce
             qu on montre alors n est PAS l etat courant. Enregistrer par-dessus
             ecraserait des modifications plus recentes avec du vieux : on
             previent, et les ecritures refusent. */
          if (i > 0) {
            PANNE = 'La version la plus récente du fichier de données n’a pas '
              + 'pu être lue. Ce qui s’affiche date du '
              + new Date(b.uploadedAt).toLocaleString('fr-FR')
              + '. N’enregistrez rien : vous écraseriez des modifications plus '
              + 'récentes. Rechargez dans un instant.';
          }
          return await r.json();
        }
        dernier = 'erreur ' + r.status;
      } catch (e) {
        dernier = e.message;
      }
    }
    PANNE = 'Aucune des ' + versions.length + ' versions du fichier de données '
      + 'n’a pu être lue (' + dernier + '). Rien n’est perdu : réessayez dans '
      + 'un instant.';
    return structuredClone(VIDE);
  } catch (e) {
    PANNE = expliquer(e);
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
    const { put, list, del } = await import('@vercel/blob');
    const avant = await list({ prefix: PREFIXE, token: JETON_BLOB });
    await put(PREFIXE + '.json', JSON.stringify(donnees), {
      access: 'public', token: JETON_BLOB, contentType: 'application/json',
    });
    /* Les versions precedentes partent APRES l'ecriture : si celle-ci echoue,
       l'ancienne reste en place plutot que de tout perdre. On n'enleve que le
       surplus — les GARDE-1 plus recentes restent, et forment avec la nouvelle
       les GARDE exemplaires conserves. */
    const surplus = avant.blobs.slice()
      .sort((x, y) => new Date(y.uploadedAt) - new Date(x.uploadedAt))
      .slice(GARDE - 1)
      .map((b) => b.url);
    if (surplus.length) {
      try { await del(surplus, { token: JETON_BLOB }); }
      catch (e) { /* du menage rate ne doit pas faire echouer la publication */ }
    }
    return { ok: true };
  } catch (e) {
    return { ok: false, message: expliquer(e) };
  }
}

/* Les pannes de stockage ont des causes precises et des gestes precis. Une
   erreur brute — « This store does not exist » — n'aide personne : on traduit
   celles qu'on connait en ce qu'il faut aller faire. */
function expliquer(e) {
  const m = String(e && e.message);
  if (/Cannot find module/.test(m))
    return "Le paquet @vercel/blob n'est pas installé. Ajoutez-le aux dépendances.";
  if (/private access|private store/i.test(m))
    return "Le magasin Blob est en accès privé. Les affiches d'un site public "
      + 'doivent être lisibles par les visiteurs : créez un magasin en accès '
      + 'public et connectez-le à la place.';
  // Cas typique : BLOB_READ_WRITE_TOKEN a ete saisi a la main, puis le magasin
  // supprime. La variable manuelle survit a la suppression du magasin et
  // l'emporte sur celle qu'ajoute la connexion du nouveau.
  if (/store does not exist|no such store|store not found/i.test(m))
    return "Le jeton désigne un magasin qui n'existe plus. Si "
      + 'BLOB_READ_WRITE_TOKEN a été saisi à la main dans les variables '
      + "d'environnement, supprimez cette variable : celle du magasin connecté "
      + 'prendra le relais. Puis redéployez.';
  if (/unauthorized|forbidden|invalid token/i.test(m))
    return 'Le jeton de stockage est refusé. Reconnectez le magasin au projet, '
      + 'puis redéployez.';
  return "Le stockage a refusé l'opération : " + m.slice(0, 140);
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

/* Un texte de plusieurs lignes. propre() ecrase les retours a la ligne et
   coupe a la longueur maximale sans rien dire : une accroche ecrite en liste
   revenait en un bloc, amputee de sa fin en plein mot. Ici les lignes sont
   gardees, les blancs en trop reduits, et la longueur n est PAS tronquee —
   c est a l appelant de refuser, pour que rien ne disparaisse en silence. */
function texteLong(v) {
  return String(v == null ? '' : v)
    .replace(/\r\n?/g, '\n')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .split('\n').map((l) => l.trim()).join('\n')
    .trim();
}

/* Les services qu'une promotion peut viser en plus des chambres. La liste est
   fermee : une valeur inventee par un appel malveillant ne doit pas se
   retrouver affichee sur le site. */
const SERVICES = ['spa', 'restaurant', 'experiences'];

/* Les unites d une formule a prix fixe. Liste fermee, comme les services :
   ce qui s affiche sur le site ne doit jamais venir d une valeur inventee
   par un appel exterieur. */
const UNITES = ['forfait', 'personne', 'enfant', 'nuit'];

/** Un nombre positif, ou zero. Une chaine vide, un texte, un signe moins :
    tout cela vaut zero plutot qu'un NaN qui contaminerait l'affichage. */
function nombre(v) {
  const n = Math.round(Math.abs(Number(v)));
  return Number.isFinite(n) ? n : 0;
}

/** Un instant 'AAAA-MM-JJTHH:MM', ou null. */
function instant(v) {
  const t = String(v || '').trim();
  return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(t) ? t : null;
}

/** Une liste de chaines courtes, bornee en nombre et en longueur. */
function listeDe(v, combien, taille) {
  return Array.isArray(v)
    ? v.slice(0, combien).map((x) => propre(x, taille)).filter(Boolean)
    : [];
}

const LIMITES = {
  titre: 80, accent: 40, categorie: 60, badge: 40, texte: 400,
  cta: 40, href: 200, fond: 120, quand: 60, libelle: 30, valeur: 60,
  // L accroche d une campagne : de quoi presenter quatre packs.
  accroche: 1200,
};

/** La collection ou vit un type d entree. Trois objets, une seule
    traduction : la deduire a trois endroits differents finissait par en
    oublier un. */
function collection(type) {
  return type === 'promotion' ? 'promotions'
    : type === 'campagne' ? 'campagnes' : 'evenements';
}

/** Une campagne saisonniere : un titre, une periode, et les packs qu elle
    annonce. Chaque pack a sa photo — c est elle qui fait la carte.

    Ce n est ni un evenement (pas de date unique) ni une promotion (rien a
    remiser : les prix sont fermes). D ou son propre objet. */
function nettoyerCampagne(e) {
  const o = {
    id: propre(e.id, 40) || crypto.randomUUID(),
    titre: propre(e.titre, LIMITES.titre),
    // L affiche de la campagne — celle publiee sur Facebook. Nom d une
    // photo du site, ou URL d un visuel depose.
    visuel: propre(e.visuel, 400),
    accroche: texteLong(e.accroche),
    note: propre(e.note, 120),
    debut: instant(e.debut),
    fin: instant(e.fin),
    publie: e.publie !== false,
    // Mise en avant sur la page d accueil.
    avant: e.avant === true,
    packs: (Array.isArray(e.packs) ? e.packs : []).slice(0, 8)
      .map((p) => ({
        nom: propre(p && p.nom, 60),
        prix: nombre(p && p.prix),
        unite: UNITES.includes(p && p.unite) ? p.unite : 'forfait',
        // Nom d une photo du site, ou URL d un visuel depose.
        image: propre(p && p.image, 400),
      }))
      // Un pack sans nom ni prix n a rien a montrer.
      .filter((p) => p.nom && p.prix),
  };
  if (o.debut && o.fin && o.debut > o.fin) {
    const t = o.debut; o.debut = o.fin; o.fin = t;
  }
  const manque = [];
  if (!o.titre) manque.push('titre');
  if (!o.packs.length) manque.push('pack');
  if (o.accroche.length > LIMITES.accroche) {
    return { objet: o, manque: ['accroche'],
      message: 'L’accroche fait ' + o.accroche.length + ' caractères pour '
        + LIMITES.accroche + ' au maximum. Retirez-en '
        + (o.accroche.length - LIMITES.accroche) + '.' };
  }
  return { objet: o, manque };
}

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
    /* Une promotion n'est pas un evenement avec un prix barre. Elle a une
       remise, un perimetre — sur quelles chambres — et une periode qui
       commence : un evenement se retire, une promotion se programme. */
    o.message = propre(e.message, LIMITES.texte);
    o.remise = {
      type: e.remise && e.remise.type === 'montant' ? 'montant' : 'pourcentage',
      valeur: nombre(e.remise && e.remise.valeur),
    };
    // Une remise en pourcentage au-dela de 100 n'a pas de sens, et une remise
    // nulle non plus : on borne plutot que d'accepter une aberration.
    if (o.remise.type === 'pourcentage') {
      o.remise.valeur = Math.min(o.remise.valeur, 100);
    }
    o.cible = {
      toutes: !(e.cible && e.cible.toutes === false),
      chambres: listeDe(e.cible && e.cible.chambres, 20, 60),
      services: listeDe(e.cible && e.cible.services, 6, 30)
        .filter((x) => SERVICES.includes(x)),
    };
    if (o.cible.toutes) { o.cible.chambres = []; o.cible.services = []; }
    o.debut = instant(e.debut);
    o.fin = instant(e.fin);
    // Une periode a l'envers masquerait la promotion sans rien dire : on la
    // remet a l'endroit.
    if (o.debut && o.fin && o.debut > o.fin) {
      const t = o.debut; o.debut = o.fin; o.fin = t;
    }
    o.avant = e.avant === true;          // mise en avant sur l'accueil
    o.pastille = e.pastille !== false;   // badge PROMO sur les chambres visees
    o.code = propre(e.code, 24).toUpperCase();
    delete o.infos; delete o.accent; delete o.categorie; delete o.quand;
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
    /* 503 et non 200 avec des listes vides : le site garde alors ce qui est
       fige dans ses pages au lieu d effacer les affiches de l hotel parce
       que le stockage n a pas repondu. */
    if (PANNE) return json(res, 503, { ok: false, message: PANNE });
    // Aucun cache. Une affiche publiee doit apparaitre a la seconde : un
    // cache d'une minute, c'est une minute a se demander si l'enregistrement
    // a fonctionne. La reponse fait quelques centaines d'octets, la depense
    // est negligeable.
    res.setHeader('Cache-Control', 'no-store, max-age=0');
    const visible = (x) => x.publie !== false;
    /* Une promotion programmee ne doit pas sortir d'ici : son contenu
       serait lisible par n'importe qui avant l'heure, et une promotion
       terminee resterait affichee sur une page ouverte depuis longtemps.
       Le tri se fait donc cote serveur, pas cote navigateur. */
    const maintenant = Date.now();
    const enCours = (p) => {
      const d1 = p.debut ? Date.parse(p.debut) : null;
      const d2 = p.fin ? Date.parse(p.fin) : null;
      if (d1 && maintenant < d1) return false;
      if (d2 && maintenant > d2) return false;
      return true;
    };
    return res.status(200).json({
      evenements: (d.evenements || []).filter(visible),
      promotions: (d.promotions || []).filter(visible).filter(enCours),
      campagnes: (d.campagnes || []).filter(visible).filter(enCours),
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
      version: VERSION,
      stockage: JETON_BLOB ? 'durable' : 'demonstration',
      // Vide quand la lecture s est bien passee.
      panne: PANNE || null,
      fichiers: FICHIERS,
      // L'identifiant du magasin vise, lisible dans le jeton. Il se compare a
      // celui affiche par Vercel : c'est ainsi qu'on voit a quel magasin on
      // parle. Ce n'est pas la partie secrete, et l'etat demande une session.
      magasin: (JETON_BLOB.split('_')[3] || '').slice(0, 24) || null,
      // Le nom de la variable d'ou vient le jeton : il dit quelle variable le
      // deploiement voit reellement, ce que la liste de Vercel ne montre pas
      // toujours pour les magasins connectes.
      variable: NOM_JETON || null,
      evenements: (d.evenements || []).length,
      promotions: (d.promotions || []).length,
      medias: (d.medias || []).length,
      maj: d.maj,
    });
  }

  if (action === 'tout') {
    const d = await lire();
    if (PANNE) return json(res, 503, { ok: false, message: PANNE });
    return json(res, 200, { ok: true, donnees: d });
  }

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
      return json(res, 502, { ok: false, message: expliquer(e) });
    }
  }

  if (action === 'enregistrer') {
    if (req.method !== 'POST') return json(res, 405, { ok: false });
    let corps = req.body;
    if (typeof corps === 'string') { try { corps = JSON.parse(corps); } catch { corps = {}; } }
    const type = collection(corps.type);
    const { objet, manque, message } = corps.type === 'campagne'
      ? nettoyerCampagne(corps.entree || {})
      : nettoyer(corps.entree || {}, corps.type);
    if (manque.length) {
      return json(res, 422, { ok: false, champs: manque,
        message: message || 'Il manque le ' + manque.join(' et le ') + '.' });
    }
    const d = await lire();
    /* JAMAIS d ecriture par-dessus une lecture en echec. lire() rend un objet
       vide quand elle echoue ; on inserait l entree dedans, puis ecrire()
       ecrasait le fichier et supprimait la version precedente. Deux affiches
       ont disparu comme ca. */
    if (PANNE) return json(res, 503, { ok: false, message: PANNE
      + ' Rien n a ete enregistre : ecrire maintenant effacerait le reste.' });
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
    const type = collection(corps.type);
    const d = await lire();
    /* JAMAIS d ecriture par-dessus une lecture en echec. lire() rend un objet
       vide quand elle echoue ; on inserait l entree dedans, puis ecrire()
       ecrasait le fichier et supprimait la version precedente. Deux affiches
       ont disparu comme ca. */
    if (PANNE) return json(res, 503, { ok: false, message: PANNE
      + ' Rien n a ete enregistre : ecrire maintenant effacerait le reste.' });
    d[type] = (d[type] || []).filter((x) => x.id !== corps.id);
    const w = await ecrire(d);
    if (!w.ok) return json(res, 502, { ok: false, message: w.message });
    return json(res, 200, { ok: true });
  }

  if (action === 'ordonner') {
    if (req.method !== 'POST') return json(res, 405, { ok: false });
    let corps = req.body;
    if (typeof corps === 'string') { try { corps = JSON.parse(corps); } catch { corps = {}; } }
    const type = collection(corps.type);
    const d = await lire();
    if (PANNE) return json(res, 503, { ok: false, message: PANNE
      + ' Rien n a ete enregistre : ecrire maintenant effacerait le reste.' });
    const par = new Map((d[type] || []).map((x) => [x.id, x]));
    d[type] = (corps.ordre || []).map((id) => par.get(id)).filter(Boolean);
    const w = await ecrire(d);
    if (!w.ok) return json(res, 502, { ok: false, message: w.message });
    return json(res, 200, { ok: true });
  }

  return json(res, 400, { ok: false, message: 'Action inconnue.' });
};
