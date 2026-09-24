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

/* Les categories, telles que le site les vend. On les lit au lieu de les
   recopier : le courriel de confirmation doit dire « Chambre Standard », pas
   « chambre-standard », et un nom recopie ici divergerait au premier
   renommage. Le require est statique, donc Vercel embarque le fichier. */
let CATEGORIES = [];
try { CATEGORIES = require('../donnees/chambres.json'); } catch (e) { /* le slug fera */ }
const nomDeCategorie = (slug) =>
  (CATEGORIES.find((c) => c && c.slug === slug) || {}).nom || slug;

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

/* Combien de temps une demande venue du site retient une chambre.
 *
 * Deux heures, et pas davantage : une demande n'est PAS une reservation.
 * Quelqu'un qui remplit le tunnel et n'envoie jamais son message ne doit pas
 * condamner une chambre jusqu'a la fin des temps. Passe ce delai la retenue
 * cesse de peser, mais reste visible — la demande a eu lieu, et l'effacer
 * perdrait le nom du client et ses dates.
 *
 * La reception transforme la retenue en reservation d'un clic, et celle-la
 * n'expire pas. */
const RETENUE_MINUTES = 120;

/* Le debit de la route publique qui ECRIT. Les autres ne font que lire.
 *
 * Le seuil est volontairement haut, pour la meme raison que dans
 * envoyer.js : en Cote d'Ivoire une grande partie du trafic mobile passe par
 * du NAT operateur, et des dizaines de visiteurs partagent une seule IP
 * publique. Un seuil serre refuserait des clients legitimes, ce qui coute
 * plus cher que le spam qu'il evite. La peremption fait le reste du travail :
 * meme un flot de fausses demandes se vide tout seul en deux heures. */
const DEMANDES = new Map();
const FENETRE_DEMANDE = 60_000;
const MAX_DEMANDES = 12;

function tropDeDemandes(ip) {
  const t = Date.now();
  const liste = (DEMANDES.get(ip) || []).filter((x) => t - x < FENETRE_DEMANDE);
  liste.push(t);
  DEMANDES.set(ip, liste);
  if (DEMANDES.size > 500) {
    for (const [k, v] of DEMANDES) {
      if (!v.some((x) => t - x < FENETRE_DEMANDE)) DEMANDES.delete(k);
    }
  }
  return liste.length > MAX_DEMANDES;
}

/* `chambres` et `fermetures` portent le calendrier de disponibilite.
   `chambres`, ce sont les chambres PHYSIQUES — la 25, la 26 — chacune
   rattachee a une categorie. Voir le bloc « Disponibilite » plus bas. */
const VIDE = { evenements: [], promotions: [], campagnes: [], medias: [],
               chambres: [], fermetures: [], maj: null };

/* La derniere lecture en echec, en clair. Vide quand tout va bien.
   Sans elle, une lecture qui echoue rendait exactement la meme chose qu un
   magasin vide : zero evenement, zero promotion, zero campagne, et pas un
   mot. On croit alors avoir tout perdu — alors que les donnees dorment
   intactes de l autre cote d un jeton qui ne repond plus. */
let PANNE = '';
// Combien de versions du fichier coexistent. Une seule en temps normal.
let FICHIERS = 0;

async function lire() {
  /* Un INSTANTANE, pas la reference vivante. Le stockage durable en rend un
     forcement : chaque ecriture cree un nouveau fichier, et la lecture prend
     le plus recent. Rendre ici l'objet vivant faisait que deux requetes
     simultanees partageaient la meme memoire, et se voyaient donc l'une
     l'autre instantanement — la course a l'ecriture etait INVISIBLE en local
     et en test, et n'apparaissait qu'en production. */
  if (!JETON_BLOB) {
    if (!memoire) memoire = structuredClone(VIDE);
    return structuredClone(memoire);
  }
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
/** Un instant complet, a la milliseconde. `instant()` tronque a la minute,
 *  ce qui suffit a une echeance mais pas a departager deux demandes arrivees
 *  dans la meme seconde. */
function horodatage(v) {
  const t = String(v || '').trim();
  return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(t) ? t : null;
}

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
    : type === 'campagne' ? 'campagnes'
    : type === 'fermeture' ? 'fermetures'
    : type === 'chambre' ? 'chambres' : 'evenements';
}

// ── Disponibilite ───────────────────────────────────────────────
/* ON RAISONNE PAR CHAMBRE PHYSIQUE, PAS PAR CATEGORIE.
 *
 * C'est la facon de voir de la reception : elle a un cahier avec des
 * numeros. « La 25 est prise du 24 au 26 », pas « les Standards sont
 * pris ». Le site, lui, vend des CATEGORIES : il demande donc « reste-t-il
 * au moins une chambre de cette categorie ces nuits-la ? ».
 *
 * QUATRE ETATS :
 *
 *   inconnu   aucune chambre de cette categorie n'a ete saisie. Le site ne
 *             promet rien et redit que la reception confirme sous 24 h.
 *   complet   toutes ses chambres sont prises ou hors service.
 *   derniere  il en reste EXACTEMENT une.
 *   libre     il en reste au moins deux.
 *
 * `derniere` est le seul chiffre qui sort d'ici. « Il reste sept chambres »
 * publierait le taux d'occupation de l'hotel a qui sait lire du JSON ; « il
 * en reste une » est utile au visiteur et ne dit rien de plus que ce qu'il
 * va decouvrir en reservant.
 *
 * La regle de secours : tout ce qui rate — stockage muet, jeton absent,
 * date illisible, categorie sans chambre — retombe sur `inconnu`, JAMAIS
 * sur `libre`. Annoncer libre a tort, c'est vendre une chambre qui n'existe
 * pas.
 *
 * LES DATES SONT DES NUITS. Une fermeture du 24 au 26 ferme les nuits du
 * 24, du 25 et du 26. Un sejour du 24 au 26 occupe les nuits du 24 et du
 * 25 — pas celle du 26, le client part ce matin-la. */

const courrielValide = (v) => /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i.test(String(v || ''));

/** La veille d'un jour. On passe par midi UTC : a minuit, un decalage
    d'une heure fait changer de date, et la nuit se decalerait d'un jour. */
function veille(j) {
  const d = new Date(j + 'T12:00:00Z');
  d.setUTCDate(d.getUTCDate() - 1);
  return d.toISOString().slice(0, 10);
}

/** Un jour 'AAAA-MM-JJ', ou null. */
function jour(v) {
  const t = String(v || '').trim();
  return /^\d{4}-\d{2}-\d{2}$/.test(t) ? t : null;
}

/* Le slug d'une categorie, ou '*' pour l'hotel entier. On valide la FORME,
   pas une liste fermee : les slugs vivent dans _chambres.py, et une liste
   recopiee ici divergerait au premier renommage. Un slug inconnu ne ferme
   rien et ne s'affiche nulle part. */
const slug = (v) => {
  const t = String(v || '').trim().toLowerCase();
  return t === '*' || /^[a-z0-9][a-z0-9-]{1,48}$/.test(t) ? t : '';
};

/** Une chambre physique : un numero, une categorie, en service ou non. */
function nettoyerChambre(e) {
  const o = {
    id: propre(e.id, 40) || crypto.randomUUID(),
    /* Le numero tel que l'hotel l'ecrit : « 25 », « B12 »,
       « Bungalow 3 ». On ne lui impose pas notre facon de numeroter. */
    numero: propre(e.numero, 20),
    categorie: slug(e.categorie),
    /* L'etage, tel que l'hotel le nomme : « 1 », « RDC », « Bungalows ».
       Facultatif — personne ne nous l'a donne, et la colonne ne s'affiche
       que si au moins une chambre en porte un. */
    etage: propre(e.etage, 20),
    /* HORS SERVICE : indisponible sans dates, jusqu'a nouvel ordre. Une
       climatisation en panne n'a pas de date de fin connue, et obliger a en
       inventer une ferait rouvrir la chambre toute seule ce jour-la. */
    service: e.service !== false,
    note: propre(e.note, 120),
  };
  const manque = [];
  if (!o.numero) manque.push('numéro');
  if (!o.categorie || o.categorie === '*') manque.push('catégorie');
  return { objet: o, manque };
}

/** Le sejour [du, au[ touche-t-il les nuits [debut, fin] ?
 *
 *  Les quatre bornes sont des chaines 'AAAA-MM-JJ' : leur ordre
 *  lexicographique EST leur ordre chronologique, aucune conversion en date
 *  n'est necessaire — et aucun fuseau horaire ne vient s'en meler.
 *
 *  Le sejour occupe les nuits du .. au-1. Il chevauche donc la fermeture si
 *  elle commence avant le depart ET se termine a l'arrivee ou apres.
 *
 *  `fin` a null vaut « sans date de fin » : la fermeture court indefiniment
 *  a partir de son debut. */
function chevauche(du, au, debut, fin) {
  if (debut >= au) return false;
  return fin === null || fin === undefined || fin >= du;
}

/** Une fermeture : ce qu'elle vise, des nuits, et un motif qui reste interne.
 *
 *  `cible` vaut l'un des trois :
 *    - l'identifiant d'une chambre  — « la 25 est prise »
 *    - le slug d'une categorie      — « toutes les Standards, travaux »
 *    - '*'                          — l'hotel entier, fermeture annuelle
 *  Les identifiants sont des UUID et les slugs sont en minuscules a tirets :
 *  aucune confusion possible entre les deux. */
function nettoyerFermeture(e) {
  const brut = String(e.cible == null ? '' : e.cible).trim();
  const o = {
    id: propre(e.id, 40) || crypto.randomUUID(),
    cible: /^[0-9a-f-]{36}$/i.test(brut) ? brut.toLowerCase() : slug(brut),
    debut: jour(e.debut),
    /* null = sans date de fin. Voir chevauche(). */
    fin: jour(e.fin),
    /* Pourquoi c'est ferme. Jamais publie : « groupe Sonatel » ou
       « travaux salle de bain » regarde l'hotel, pas ses visiteurs. Le site
       ne dit que « complet ». */
    motif: propre(e.motif, 120),
    /* Ce qu'est la fermeture : un sejour client, une chambre hors service,
       ou des nuits retirees de la vente. Vide pour les fermetures d'avant :
       elles restent des fermetures, et comptent comme telles. Listes
       fermees — rien d'invente ne doit s'afficher. */
    nature: ['client', 'hors-service', 'vente'].includes(e.nature) ? e.nature : '',
    client: propre(e.client, 60),
    /* L'adresse du client, pour le prevenir quand la reception confirme.
       Elle ne sort JAMAIS par la route publique — voir a=dispo, qui ne rend
       que des verdicts. Seule l'administration la voit. */
    courriel: courrielValide(propre(e.courriel, 160)) ? propre(e.courriel, 160) : '',
    statut: ['confirmee', 'attente', 'annulee', 'terminee'].includes(e.statut)
      ? e.statut : '',
    /* L'instant ou une retenue cesse de bloquer. Il n'existe que pour les
       demandes venues du site, qui ne sont pas encore des reservations : on
       ne peut pas condamner une chambre parce que quelqu'un a rempli un
       formulaire. Une reservation confirmee par la reception n'en a pas. */
    expire: instant(e.expire),
    /* L'instant exact de la creation. Il ne sert qu'a une chose : departager
       deux demandes tombees sur la meme chambre au meme moment. Le premier
       arrive gagne, et cette regle doit rendre le MEME verdict des deux
       cotes de la course. Preserve tel quel a chaque modification : le
       remettre a jour ferait vieillir une demande a l'envers. */
    cree: horodatage(e.cree) || new Date().toISOString(),
  };
  // Une periode a l'envers fermerait zero nuit sans le dire.
  if (o.debut && o.fin && o.debut > o.fin) {
    const t = o.debut; o.debut = o.fin; o.fin = t;
  }
  // `sansFin` a vrai laisse fin a null ; sinon, une fin absente veut dire
  // une seule nuit. Sans cette distinction, oublier la date de fin fermait
  // la chambre pour toujours.
  if (o.debut && !o.fin && e.sansFin !== true) o.fin = o.debut;
  const manque = [];
  if (!o.cible) manque.push('chambre');
  if (!o.debut) manque.push('date de début');
  return { objet: o, manque };
}

/** Cette fermeture vise-t-elle cette chambre ? */
function vise(f, ch) {
  return f.cible === '*' || f.cible === ch.id || f.cible === ch.categorie;
}

/** Cette fermeture compte-t-elle encore ?
 *
 *  Une retenue perimee cesse de bloquer AU MOMENT DE LA LECTURE, pas au
 *  passage d'un menage nocturne : il n'y a pas de menage nocturne ici, et
 *  une chambre qui resterait bloquee jusqu'au prochain deploiement serait
 *  une chambre invendable sans que personne ne sache pourquoi.
 *
 *  Elle reste dans le magasin : la demande a bien eu lieu, et effacer
 *  perdrait le nom du client et ses dates. Elle cesse simplement de peser. */
function vivante(f, maintenant) {
  if (!f || !f.debut) return false;
  if (f.statut === 'annulee') return false;
  if (f.expire && Date.parse(f.expire) < maintenant) return false;
  return true;
}

/** L'etat d'une CATEGORIE sur un sejour. Voir le commentaire du bloc. */
function etatDe(d, categorie, du, au) {
  const chambres = (Array.isArray(d.chambres) ? d.chambres : [])
    .filter((c) => c && c.categorie === categorie);
  // Categorie dont aucune chambre n'a ete saisie : on ne sait rien.
  if (!chambres.length) return 'inconnu';

  /* Une reservation annulee, et une retenue perimee, ne ferment plus rien. */
  const maintenant = Date.now();
  const fermetures = (Array.isArray(d.fermetures) ? d.fermetures : [])
    .filter((f) => vivante(f, maintenant));

  const libres = chambres.filter((ch) => {
    // Hors service : indisponible, quelles que soient les dates.
    if (ch.service === false) return false;
    return !fermetures.some((f) => vise(f, ch) && chevauche(du, au, f.debut, f.fin));
  }).length;

  if (!libres) return 'complet';
  return libres === 1 ? 'derniere' : 'libre';
}

/* ── Le verrou anti-collision ───────────────────────────────────────────
 *
 * LE PROBLEME, ET IL EST PIRE QU'UN DOUBLE ENGAGEMENT.
 *
 * Le magasin n'a pas d'ecriture conditionnelle : chaque enregistrement ecrit
 * le document ENTIER, et la lecture prend le plus recent. Deux demandes
 * simultanees lisent donc le meme etat, choisissent la meme chambre — car
 * premiereLibre() est deterministe et rend toujours le plus petit numero —
 * puis ecrivent chacune SON instantane. La seconde ecriture ne contient pas
 * la retenue de la premiere : elle l'efface.
 *
 * Deux clients s'entendent alors dire « une chambre vous est gardee », une
 * seule retenue existe, et la reception ne voit jamais la demande perdue.
 *
 * CE QU'ON PEUT FAIRE, ET CE QU'ON NE PEUT PAS.
 *
 * On ne peut pas poser un vrai verrou : il faudrait un magasin qui sache
 * comparer-et-echanger, ce que Blob ne sait pas faire. Un magasin
 * transactionnel — Redis, Postgres — ou l'outil de gestion de l'hotel
 * lui-meme, reste la seule reponse complete. C'est ecrit dans
 * `notre-comprehension.md` et ca ne doit pas etre escamote.
 *
 * On peut en revanche tenir une garantie plus faible, mais SUFFISANTE tant
 * qu'on n'encaisse pas : ne jamais dire « gardee » a un client dont la
 * retenue n'a pas survecu. On ecrit, on RELIT, et on ne repond que sur ce
 * que le magasin contient vraiment.
 *
 * LA REGLE QUI DEPARTAGE. Elle doit rendre le meme verdict des deux cotes de
 * la course, sinon les deux se croient gagnantes ou les deux perdantes :
 *   - une fermeture posee par la reception l'emporte TOUJOURS sur une
 *     demande venue du site ;
 *   - entre deux demandes, la plus ancienne gagne ;
 *   - a egalite a la milliseconde, l'identifiant tranche.
 */

/** Deux fermetures touchent-elles une nuit commune ? `fin` a null vaut
 *  « sans fin ». */
function nuitsSeCroisent(a, b) {
  const SANS_FIN = '9999-12-31';
  const fa = a.fin == null ? SANS_FIN : a.fin;
  const fb = b.fin == null ? SANS_FIN : b.fin;
  return a.debut <= fb && b.debut <= fa;
}

/** Laquelle des deux a ete creee la premiere. Totalement ordonnee : deux
 *  appels symetriques ne peuvent pas rendre « oui » tous les deux. */
function plusAncienne(a, b) {
  const ca = a.cree || '', cb = b.cree || '';
  if (ca !== cb) return ca < cb;
  return String(a.id) < String(b.id);
}

/** Tout ce qui, dans cet etat, disputerait cette chambre a cette retenue. */
function concurrentes(d, entree, ch, maintenant) {
  return (Array.isArray(d.fermetures) ? d.fermetures : []).filter(
    (f) => f && f.id !== entree.id && vivante(f, maintenant)
      && vise(f, ch) && nuitsSeCroisent(f, entree));
}

/** Notre retenue survit-elle a toutes ses concurrentes ? */
function retenueGagne(entree, rivales) {
  for (const f of rivales) {
    // La reception decide ; le formulaire demande.
    if (f.nature !== 'client') return false;
    /* Une reservation CONFIRMEE est ferme. Elle l'emporte quelle que soit
       son anciennete : la comparer par l'age reviendrait a laisser une
       demande venue du site deloger un client dont la chambre est acquise. */
    if (f.statut === 'confirmee') return false;
    if (!plusAncienne(entree, f)) return false;
  }
  return true;
}

/** Retire une fermeture du magasin, sur l'etat le plus frais.
 *
 *  Au mieux. Si cette ecriture est a son tour ecrasee, la retenue perdante
 *  reste — elle expire d'elle-meme en deux heures, et la reception la voit.
 *  Mieux vaut une retenue de trop, visible et perissable, qu'un client a qui
 *  on a promis une chambre qu'il n'a pas. */
async function retirerFermeture(id) {
  try {
    const frais = await lire();
    if (PANNE) return;
    frais.fermetures = (frais.fermetures || []).filter((f) => f && f.id !== id);
    await ecrire(frais);
  } catch (e) { /* elle expirera */ }
}

/** Pose la retenue, puis verifie qu'elle a bien survecu. */
async function poserRetenue(d, entree, ch) {
  d.fermetures = Array.isArray(d.fermetures) ? d.fermetures : [];
  d.fermetures.push(entree);
  const w = await ecrire(d);
  if (!w.ok) return { ok: false, raison: 'ecriture' };

  /* On RELIT. Sans cette relecture, on repondrait sur ce qu'on croit avoir
     ecrit, pas sur ce que le magasin contient. */
  const apres = await lire();
  if (PANNE) return { ok: false, raison: 'indisponible' };

  const mienne = (apres.fermetures || []).find((f) => f && f.id === entree.id);
  // Absente : une ecriture concurrente est passee par-dessus la notre.
  if (!mienne) return { ok: false, raison: 'ecrasee' };

  const rivales = concurrentes(apres, entree, ch, Date.now());
  if (!rivales.length || retenueGagne(entree, rivales)) return { ok: true };

  await retirerFermeture(entree.id);
  return { ok: false, raison: 'perdue' };
}

/** La premiere chambre libre d'une categorie sur ces nuits, ou null.
 *
 *  « La premiere » se decide sur le NUMERO, dans l'ordre ou un humain le
 *  lit : 2 avant 10. Deux demandes simultanees tombent donc sur la meme
 *  chambre libre — mais la seconde ne la trouvera plus libre, puisque la
 *  premiere l'aura retenue. La reception peut deplacer la retenue ensuite.
 */
function premiereLibre(d, categorie, du, au) {
  const maintenant = Date.now();
  const fermetures = (Array.isArray(d.fermetures) ? d.fermetures : [])
    .filter((f) => vivante(f, maintenant));
  return (Array.isArray(d.chambres) ? d.chambres : [])
    .filter((c) => c && c.categorie === categorie && c.service !== false)
    .sort((a, b) => String(a.numero).localeCompare(String(b.numero), 'fr',
      { numeric: true, sensitivity: 'base' }))
    .find((ch) => !fermetures.some((f) => vise(f, ch) && chevauche(du, au, f.debut, f.fin)))
    || null;
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

/* ── L'e-mail de confirmation au client ────────────────────────────────
   Le meme fournisseur que api/envoyer.js, mais un autre destinataire et un
   autre texte : celui-la part a l'hotel, celui-ci au client. On ne partage
   que dix lignes d'appel HTTP, et un module partage dans /api deviendrait
   une fonction servie par Vercel.

   Il rend TOUJOURS une raison. Une confirmation qui reussit pendant que le
   courriel echoue en silence, c'est un client qui n'est prevenu par
   personne — et la reception qui croit que si. */
async function courrielAuClient(f, nomCategorie) {
  if (!f.courriel) return 'sans-adresse';
  const cle = process.env.RESEND_API_KEY;
  const exp = process.env.MAIL_EXP;
  if (!cle || !exp) return 'non-configure';

  const d = (j) => {
    try {
      return new Date(j + 'T12:00:00Z').toLocaleDateString('fr-FR',
        { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    } catch (e) { return j; }
  };
  /* Les nuits se recomptent en arrivee/depart : le client a demande a
     partir le lendemain de sa derniere nuit. */
  const depart = (() => {
    const x = new Date(f.fin + 'T12:00:00Z');
    x.setUTCDate(x.getUTCDate() + 1);
    return x.toISOString().slice(0, 10);
  })();

  const lignes = [
    ['Catégorie', nomCategorie],
    ['Arrivée', d(f.debut)],
    ['Départ', d(depart)],
  ];
  if (f.motif) lignes.push(['Référence', f.motif]);

  const html = `<div style="font:400 15px/1.6 Georgia,serif;color:#1b1b1b;max-width:520px">
    <p>Bonjour ${echappe(f.client)},</p>
    <p><strong>Votre réservation à l'Hôtel Evannath est confirmée.</strong></p>
    <table style="border-collapse:collapse;margin:18px 0">${lignes.map(
      ([k, v]) => `<tr><td style="padding:6px 18px 6px 0;color:#8a7d6c;white-space:nowrap">${k}</td>`
        + `<td style="padding:6px 0">${echappe(v)}</td></tr>`).join('')}</table>
    <p>La réception vous recontacte pour les modalités de règlement.</p>
    <p style="color:#8a7d6c;font-size:13.5px">Hôtel Evannath — Assinie PK 19,
      Côte d'Ivoire<br>Pour toute question, répondez simplement à ce message.</p>
  </div>`;

  try {
    const r = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${cle}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: `Hôtel Evannath <${exp}>`,
        to: [f.courriel],
        reply_to: process.env.MAIL_DEST || undefined,
        subject: "Votre réservation à l'Hôtel Evannath est confirmée"
          + (f.motif ? ' — ' + f.motif : ''),
        html,
      }),
    });
    return r.ok ? 'envoye' : 'refuse';
  } catch (e) {
    return 'echec';
  }
}

const echappe = (v) => String(v == null ? '' : v)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;');

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

  /* ── Disponibilite, en lecture publique ────────────────────────────────
     On rend un VERDICT, pas le calendrier. Deux raisons :
       - le taux d'occupation d'un hotel regarde l'hotel. Servir la liste
         des fermetures, c'est publier son planning a qui sait lire du JSON ;
       - la regle des nuits se decide une fois, ici, et pas dans chacune des
         pages qui l'afficheraient chacune a sa facon.

     Cette route ne demande PAS de session : c'est ce que le visiteur lit.
     Le motif d'une fermeture n'en sort jamais. */
  if (action === 'dispo') {
    const du = jour(req.query.du);
    const au = jour(req.query.au);
    res.setHeader('Cache-Control', 'no-store, max-age=0');
    // Des dates absentes ou a l'envers ne sont pas une erreur a signaler :
    // le visiteur n'a simplement pas fini de choisir. On ne promet rien.
    if (!du || !au || au <= du) {
      return res.status(200).json({ ok: true, du, au, etats: {}, raison: 'dates' });
    }
    const d = await lire();
    /* Le stockage muet ne vaut pas « tout est libre ». Il vaut « je ne sais
       pas », et le site le dira comme il le dit deja. */
    if (PANNE) {
      return res.status(200).json({ ok: true, du, au, etats: {}, raison: 'indisponible' });
    }
    /* Le parametre s'appelle `chambre` et porte un slug de CATEGORIE : c'est
       ce que le site vend, et ce que le visiteur choisit. Les chambres
       physiques ne sortent jamais d'ici. */
    const demandee = slug(req.query.chambre);
    const slugs = demandee && demandee !== '*'
      ? [demandee]
      : [...new Set((Array.isArray(d.chambres) ? d.chambres : [])
          .map((c) => c && c.categorie).filter(Boolean))];
    const etats = {};
    for (const s of slugs) etats[s] = etatDe(d, s, du, au);
    return res.status(200).json({ ok: true, du, au, etats });
  }

  /* ── Une demande venue du site ─────────────────────────────────────────
     C'est la SEULE route publique qui ecrive. Elle existe parce que sans
     elle le serveur n'apprenait jamais qu'un client avait demande une
     chambre : la demande partait sur le telephone de la reception, et si
     celle-ci ne la recopiait pas, le site continuait d'annoncer la chambre
     libre. Deux clients pouvaient demander la derniere.

     Ce qu'elle NE REND PAS : le numero de la chambre retenue, le nombre de
     chambres restantes, quoi que ce soit de l'inventaire. Le visiteur
     apprend seulement qu'une chambre lui est gardee, ou non. */
  if (action === 'demande') {
    if (req.method !== 'POST') return json(res, 405, { ok: false });
    res.setHeader('Cache-Control', 'no-store');

    const ip = (req.headers['x-forwarded-for'] || '').split(',')[0].trim()
      || req.socket?.remoteAddress || 'inconnue';
    if (tropDeDemandes(ip)) {
      return json(res, 429, { ok: false, retenue: false, raison: 'debit' });
    }

    let corps = req.body;
    if (typeof corps === 'string') { try { corps = JSON.parse(corps); } catch { corps = {}; } }
    corps = corps || {};

    const categorie = slug(corps.categorie);
    const du = jour(corps.du);
    const au = jour(corps.au);
    const nom = propre(corps.nom, 60);
    /* Sans nom, la reception verrait une chambre retenue par personne.
       Sans dates lisibles, on ne sait pas quelles nuits garder. Dans les
       deux cas on ne retient rien — et on ne fait pas echouer le formulaire
       pour autant : la demande part quand meme vers la reception. */
    if (!categorie || categorie === '*' || !du || !au || au <= du || !nom) {
      return json(res, 200, { ok: true, retenue: false, raison: 'incomplet' });
    }

    /* Les dates du client sont une ARRIVEE et un DEPART ; une fermeture se
       compte en NUITS. Il dort du 24 au 26 : les nuits du 24 et du 25. */
    const derniere = veille(au);

    /* Trois essais. Une collision n'est pas un echec : elle veut dire qu'une
       autre demande a pris CETTE chambre. On relit, et la chambre apparait
       alors occupee — on en propose une autre. Ce n'est qu'apres trois
       collisions d'affilee qu'on renonce, et on dit alors « complet » plutot
       que d'inventer une raison. */
    for (let essai = 0; essai < 3; essai++) {
      const d = await lire();
      if (PANNE) {
        return json(res, 200, { ok: true, retenue: false, raison: 'indisponible' });
      }
      const ch = premiereLibre(d, categorie, du, au);
      if (!ch) return json(res, 200, { ok: true, retenue: false, raison: 'complet' });

      const entree = nettoyerFermeture({
        cible: ch.id, debut: du, fin: derniere,
        nature: 'client', statut: 'attente', client: nom,
        courriel: propre(corps.courriel, 160),
        expire: new Date(Date.now() + RETENUE_MINUTES * 60000).toISOString().slice(0, 16),
        motif: propre(corps.reference, 40),
      }).objet;

      const r = await poserRetenue(d, entree, ch);
      if (r.ok) {
        return json(res, 200, { ok: true, retenue: true, minutes: RETENUE_MINUTES });
      }
      /* Une panne d'ecriture ne se retente pas : elle ne vient pas d'une
         course, et reessayer l'aggraverait. */
      if (r.raison === 'ecriture' || r.raison === 'indisponible') {
        return json(res, 200, { ok: true, retenue: false, raison: r.raison });
      }
    }
    return json(res, 200, { ok: true, retenue: false, raison: 'complet' });
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
      chambres: (d.chambres || []).length,
      fermetures: (d.fermetures || []).length,
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
      : corps.type === 'fermeture'
      ? nettoyerFermeture(corps.entree || {})
      : corps.type === 'chambre'
      ? nettoyerChambre(corps.entree || {})
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
    if (corps.type === 'chambre') {
      const pareil = (v) => String(v || '').trim().toLowerCase();
      const double = d.chambres.find((x) => x.id !== objet.id
        && pareil(x.numero) === pareil(objet.numero));
      if (double) {
        return json(res, 409, { ok: false, champs: ['numéro'],
          message: 'La chambre ' + objet.numero + ' existe déjà. Deux fois le '
            + 'même numéro, et le site croirait que vous en avez deux.' });
      }
    }
    const i = d[type].findIndex((x) => x.id === objet.id);
    /* Une retenue qui passe de « attente » a « confirmee » : c'est LE moment
       ou le client doit apprendre que sa demande est acceptee. Avant, il
       n'avait que sa reference, et personne ne le prevenait. */
    const avant = i >= 0 ? d[type][i] : null;
    /* `cree` date la DEMANDE, pas sa derniere modification. Le formulaire ne
       le renvoie pas, et nettoyerFermeture en fabriquerait alors un neuf a
       chaque enregistrement : une reservation confirmee rajeunirait, et
       perdrait une course contre une demande venue du site. */
    if (avant && avant.cree && objet.cree) objet.cree = avant.cree;
    const aConfirmer = corps.type === 'fermeture' && objet.nature === 'client'
      && objet.statut === 'confirmee'
      && (!avant || avant.statut !== 'confirmee');
    if (i >= 0) d[type][i] = objet; else d[type].push(objet);
    const w = await ecrire(d);
    if (!w.ok) return json(res, 502, { ok: false, message: w.message });

    /* L'envoi vient APRES l'ecriture : une confirmation enregistree vaut
       mieux qu'un courriel parti pour une reservation qu'on n'a pas su
       ecrire. Et son resultat remonte toujours — un courriel qui echoue en
       silence, c'est un client que personne ne previent pendant que la
       reception croit le contraire. */
    let courriel;
    if (aConfirmer) {
      const ch = (d.chambres || []).find((x) => x.id === objet.cible);
      courriel = await courrielAuClient(objet, nomDeCategorie(ch && ch.categorie));
    }
    return json(res, 200, { ok: true, entree: objet, courriel });
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

/* Les trois regles qui departagent une collision, exposees pour les tests.
   Elles sont pures : meme entree, meme verdict, sans magasin ni reseau. Une
   regle de course qui ne rend pas le MEME verdict des deux cotes laisse
   passer deux gagnantes ou deux perdantes, et c'est precisement ce qu'un
   test doit pouvoir eprouver directement.

   Vercel ne lit que la fonction elle-meme ; ces proprietes ne le genent
   pas. */
module.exports.regles = { plusAncienne, nuitsSeCroisent, retenueGagne };
