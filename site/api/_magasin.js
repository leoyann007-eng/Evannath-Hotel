/* Le magasin : ou vivent les donnees du site et les comptes.
 *
 * Chaque usage est UN document JSON (« donnees », « comptes »), relu puis
 * reecrit en entier. Le defaut d'avant tenait en une phrase : deux
 * enregistrements simultanes lisaient le meme etat, et le second effacait le
 * premier. Une confirmation de paiement ecrasee par la reception, une
 * desactivation de compte defaite par une connexion au meme instant.
 *
 * LA REGLE, desormais : on n'ecrit QUE si personne n'a ecrit depuis notre
 * lecture. Sinon on relit, on rejoue la modification sur l'etat frais, et on
 * reessaie (modifier). Une modification ne peut plus en effacer une autre.
 *
 * TROIS MODES, decides par l'environnement :
 *
 *   postgres  DATABASE_URL (ou POSTGRES_URL) present. Une base PRIVEE, et une
 *             ecriture conditionnelle exacte (UPDATE ... WHERE version = n).
 *             C'est le mode a viser.
 *   blob      seulement le jeton Vercel Blob. Le magasin est PUBLIC (adresses
 *             indevinables, mais publiques) et n'a pas d'ecriture
 *             conditionnelle : on verifie juste avant d'ecrire, ce qui
 *             resserre la fenetre sans la fermer. Mode d'attente.
 *   memoire   ni l'un ni l'autre : la memoire de l'instance, pour les tests
 *             et la demonstration. Exacte, mais perdue au redemarrage.
 *
 * LE PASSAGE DE BLOB A POSTGRES est automatique : a la premiere lecture, si
 * la base n'a pas encore le document, il est recopie depuis Blob avec ses
 * versions precedentes. En production, la copie publique est ensuite
 * effacee — c'est tout l'interet de la base — et remplacee par une marque
 * sans donnee personnelle : un deploiement qui retomberait sur Blob la lit
 * et refuse de travailler, plutot que de repartir d'un magasin vide.
 *
 * Chaque environnement Vercel a ses propres documents (« donnees »,
 * « donnees:preview », « donnees:local ») : un apercu branche sur la meme
 * base ne touche jamais aux reservations de la production.
 *
 * Le prefixe « _ » : Vercel n'en fait pas une fonction publique.
 */

const URL_BASE = process.env.DATABASE_URL || process.env.POSTGRES_URL || '';
/* L'environnement : production, preview, ou rien (poste local).

   EVN_ENV d'abord, VERCEL_ENV ensuite. Vercel pose VERCEL_ENV de lui-meme ;
   un autre hebergeur, non. Sans EVN_ENV=production chez lui, le site se
   croirait sur un poste local, chercherait « donnees:local » dans la base
   et demarrerait VIDE — les vraies donnees intactes, mais invisibles. */
const environnement = () => process.env.EVN_ENV || process.env.VERCEL_ENV || '';
const production = () => environnement() === 'production';
const suffixe = () => (production() ? '' : ':' + (environnement() || 'local'));

/* ── Postgres : une seule reserve de connexions par instance ──────────── */
let reserve = null;
let schemaPret = null;

function connexions() {
  if (!reserve) {
    const { Pool } = require('pg');
    /* Peu de connexions, vite rendues : une fonction serverless n'en a
       besoin que d'une a la fois, et la base en compte un nombre limite. */
    reserve = new Pool({ connectionString: URL_BASE, max: 3,
      idleTimeoutMillis: 10_000, connectionTimeoutMillis: 8_000, allowExitOnIdle: true });
    // Une connexion inactive que la base coupe ne doit pas faire tomber la fonction.
    reserve.on('error', () => {});
  }
  return reserve;
}

/** Les tables, creees a la premiere utilisation. Le verrou consultatif
 *  empeche deux instances de les creer au meme instant — ce qui echoue en
 *  Postgres, meme avec IF NOT EXISTS. */
function schema() {
  if (!schemaPret) {
    schemaPret = (async () => {
      const c = await connexions().connect();
      try {
        await c.query('BEGIN');
        await c.query("SELECT pg_advisory_xact_lock(hashtext('evn_schema'))");
        await c.query(`CREATE TABLE IF NOT EXISTS evn_documents (
          cle text PRIMARY KEY, version bigint NOT NULL, donnees jsonb NOT NULL,
          maj timestamptz NOT NULL DEFAULT now())`);
        await c.query(`CREATE TABLE IF NOT EXISTS evn_historique (
          id bigserial PRIMARY KEY, cle text NOT NULL, version bigint NOT NULL,
          donnees jsonb NOT NULL, maj timestamptz NOT NULL DEFAULT now())`);
        await c.query('CREATE INDEX IF NOT EXISTS evn_historique_cle ON evn_historique (cle, version)');
        await c.query(`CREATE TABLE IF NOT EXISTS evn_compteurs (
          cle text PRIMARY KEY, n integer NOT NULL, expire timestamptz NOT NULL)`);
        await c.query('COMMIT');
      } catch (e) {
        await c.query('ROLLBACK').catch(() => {});
        schemaPret = null;          // on retentera a la prochaine requete
        throw e;
      } finally { c.release(); }
    })();
  }
  return schemaPret;
}

/* ── Vercel Blob : les erreurs traduites en gestes ─────────────────────── */
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

function expliquerBase(e) {
  const m = String(e && e.message);
  if (/Cannot find module 'pg'/.test(m))
    return "Le paquet pg n'est pas installé. Ajoutez-le aux dépendances.";
  if (/password authentication|no pg_hba|role .* does not exist/i.test(m))
    return 'La base de données refuse la connexion : vérifiez DATABASE_URL dans Vercel, puis redéployez.';
  if (/ENOTFOUND|ECONNREFUSED|timeout|terminated/i.test(m))
    return 'La base de données ne répond pas. Rien n’est perdu : réessayez dans un instant.';
  return 'La base de données a refusé l’opération : ' + m.slice(0, 140);
}

const recent = (x, y) => new Date(y.uploadedAt) - new Date(x.uploadedAt);
const pause = (ms) => new Promise((ok) => setTimeout(ok, ms));

/**
 * Un document du magasin.
 *
 *   cle          « donnees », « comptes »
 *   prefixeBlob  ou il vivait dans Vercel Blob (« evannath/donnees »)
 *   garde        combien de versions conserver (sauvegardes)
 *   vide         () => le document de depart
 *   jeton        le jeton Vercel Blob, ou ''
 *   nom          ce qu'est ce document, pour les messages (« du fichier de données »)
 *   outils       pour les tests seulement : { blob, fetch } a la place de
 *                @vercel/blob et du fetch global
 */
function document({ cle, prefixeBlob, garde, vide, jeton, nom, outils }) {
  const mode = URL_BASE ? 'postgres' : jeton ? 'blob' : 'memoire';
  const PRODUCTION = production();
  const CLE = cle + suffixe();
  const blob = () => (outils && outils.blob ? Promise.resolve(outils.blob) : import('@vercel/blob'));
  const charger = (url, o) => (outils && outils.fetch ? outils.fetch(url, o) : fetch(url, o));
  const MARQUE = prefixeBlob + '.deplacees';
  const estDonnee = (p) => p === prefixeBlob + '.json'
    || (p.startsWith(prefixeBlob + '-') && p.endsWith('.json'));

  // ── memoire ──────────────────────────────────────────────────────────
  /* Un INSTANTANE a chaque lecture, jamais la reference vivante : deux
     requetes simultanees ne doivent pas se voir l'une l'autre, sans quoi la
     course a l'ecriture serait invisible en local et en test. */
  let mem = null, memVersion = 0;

  // ── blob ─────────────────────────────────────────────────────────────
  /* Le fichier porte un suffixe aleatoire, ajoute par Blob : ecrit a une
     adresse fixe dans un magasin public, son URL serait devinable. On le
     retrouve par prefixe, cote serveur, jeton en main.

     `toutes` : rendre aussi le contenu des versions precedentes (pour les
     recopier dans la base au passage a Postgres). */
  async function lireBlob(toutes) {
    try {
      const { list } = await blob();
      const { blobs } = await list({ prefix: prefixeBlob, token: jeton });
      if (blobs.some((b) => b.pathname.startsWith(MARQUE))) {
        return { ok: false, marque: true, panne: 'Les données ont été déplacées dans la base de données '
          + '(Postgres), et ce déploiement ne la voit pas : DATABASE_URL manque. Rien n’est lu ni écrit '
          + 'ici. Reconnectez la base au projet dans Vercel, puis redéployez.' };
      }
      const versions = blobs.filter((b) => estDonnee(b.pathname)).sort(recent);
      if (!versions.length) return { ok: true, existe: false, d: vide(), version: null, fichiers: 0, blobs: [] };
      /* Si un menage a echoue, plusieurs versions coexistent : on prend la
         plus recente. Mais l'inventaire est a consistance differee — il rend
         parfois une version tout juste supprimee, dont l'adresse repond 403.
         On essaie donc les suivantes au lieu d'abandonner a la premiere. */
      let dernier = '';
      for (let i = 0; i < versions.length; i++) {
        const b = versions[i];
        try {
          const r = await charger(b.url, { cache: 'no-store' });
          if (!r.ok) { dernier = 'erreur ' + r.status; continue; }
          const d = await r.json();
          const res = { ok: true, existe: true, d, version: versions[0].pathname,
            fichiers: versions.length, blobs: versions };
          /* Se rabattre sur une version anterieure sauve l'affichage, mais ce
             qu'on montre alors n'est PAS l'etat courant. Enregistrer par-dessus
             ecraserait des modifications plus recentes avec du vieux : on
             previent, et les ecritures refusent. */
          if (i > 0) {
            res.ok = false;
            res.panne = 'La version la plus récente ' + nom + ' n’a pas pu être lue. Ce qui '
              + 's’affiche date du ' + new Date(b.uploadedAt).toLocaleString('fr-FR')
              + '. N’enregistrez rien : vous écraseriez des modifications plus récentes. '
              + 'Rechargez dans un instant.';
          }
          if (toutes) {
            res.anciennes = [];
            for (const a of versions.slice(i + 1).reverse()) {
              try {
                const ra = await charger(a.url, { cache: 'no-store' });
                if (ra.ok) res.anciennes.push({ d: await ra.json(), le: a.uploadedAt });
              } catch (e) { /* une sauvegarde illisible n'empeche pas le passage */ }
            }
          }
          return res;
        } catch (e) { dernier = e.message; }
      }
      return { ok: false, panne: 'Aucune des ' + versions.length + ' versions ' + nom
        + ' n’a pu être lue (' + dernier + '). Rien n’est perdu : réessayez dans un instant.' };
    } catch (e) {
      return { ok: false, panne: expliquer(e) };
    }
  }

  /** Ecrit si la version la plus recente est toujours celle qu'on a lue.
   *  Blob ne sait pas le faire de facon atomique : la verification juste
   *  avant l'ecriture resserre la fenetre, elle ne la ferme pas. */
  async function ecrireBlob(d, version) {
    try {
      const { put, list, del } = await blob();
      const avant = await list({ prefix: prefixeBlob, token: jeton });
      if (avant.blobs.some((b) => b.pathname.startsWith(MARQUE))) {
        return { ok: false, message: 'Les données ont été déplacées dans la base de données : rien n’a été écrit ici.' };
      }
      const versions = avant.blobs.filter((b) => estDonnee(b.pathname)).sort(recent);
      if ((versions[0] ? versions[0].pathname : null) !== version) return { ok: false, conflit: true };
      /* addRandomSuffix : chaque ecriture est un NOUVEAU fichier (prefixe-xxxx.json),
         c'est ce qui fait les versions. Depuis @vercel/blob 1.0 le suffixe n'est
         plus mis par defaut : sans lui, la seconde ecriture serait refusee
         (« blob already exists »). */
      const r = await put(prefixeBlob + '.json', JSON.stringify(d), {
        access: 'public', token: jeton, contentType: 'application/json', addRandomSuffix: true,
      });
      /* Les versions precedentes partent APRES l'ecriture : si celle-ci
         echoue, l'ancienne reste en place plutot que de tout perdre. On
         n'enleve que le surplus — les garde-1 plus recentes restent, et
         forment avec la nouvelle les exemplaires conserves. */
      const surplus = versions.slice(garde - 1).map((b) => b.url);
      if (surplus.length) {
        try { await del(surplus, { token: jeton }); } catch (e) { /* du menage rate n'est pas un echec */ }
      }
      return { ok: true, version: r.pathname };
    } catch (e) {
      return { ok: false, message: expliquer(e) };
    }
  }

  // ── postgres ─────────────────────────────────────────────────────────
  /* Le passage de Blob a la base : une seule fois, a la premiere lecture.
     Deux instances qui s'y mettent ensemble ne font qu'un document — la
     seconde insertion ne fait rien (ON CONFLICT DO NOTHING). */
  async function migrer() {
    if (!jeton) return null;
    const anc = await lireBlob(true);
    if (!anc.ok) {
      /* Blob porte la marque : le document a deja ete deplace dans une base.
         Un apercu repart d'un document vide ; la production, elle, ne doit
         surtout pas repartir de zero — la base visee n'est pas la bonne. */
      if (anc.marque) {
        if (!PRODUCTION) return null;
        return { panne: 'Les données ont été déplacées dans une base de données, mais celle-ci ne les '
          + 'contient pas : vérifiez que DATABASE_URL désigne la bonne base, puis redéployez.' };
      }
      return { panne: 'Les données de Vercel Blob n’ont pas pu être recopiées dans la base : '
        + anc.panne + ' Rien n’est perdu : réessayez dans un instant.' };
    }
    if (!anc.existe) return null;
    const c = await connexions().connect();
    let gagne = false;
    try {
      await c.query('BEGIN');
      const ins = await c.query('INSERT INTO evn_documents (cle, version, donnees) VALUES ($1, 1, $2) '
        + 'ON CONFLICT (cle) DO NOTHING', [CLE, JSON.stringify(anc.d)]);
      if (ins.rowCount === 1) {
        gagne = true;
        // Les sauvegardes suivent : versions precedentes (0), puis la courante (1).
        for (const a of anc.anciennes || []) {
          await c.query('INSERT INTO evn_historique (cle, version, donnees, maj) VALUES ($1, 0, $2, $3)',
            [CLE, JSON.stringify(a.d), a.le]);
        }
        await c.query('INSERT INTO evn_historique (cle, version, donnees) VALUES ($1, 1, $2)',
          [CLE, JSON.stringify(anc.d)]);
      }
      await c.query('COMMIT');
    } catch (e) {
      await c.query('ROLLBACK').catch(() => {});
      throw e;
    } finally { c.release(); }
    /* La copie publique part — mais en production seulement, et la marque
       d'abord : un apercu ne doit jamais retirer ses donnees a la
       production, qui peut encore les lire. */
    if (gagne && PRODUCTION) {
      try {
        const { put, del } = await blob();
        await put(MARQUE + '.json', JSON.stringify({ vers: 'postgres', le: new Date().toISOString(),
          note: 'Données déplacées dans la base Postgres du projet.' }),
          { access: 'public', token: jeton, contentType: 'application/json', addRandomSuffix: true });
        await del(anc.blobs.map((b) => b.url), { token: jeton });
      } catch (e) { /* elles restent : Parametres le dit (ancienne copie) */ }
    }
    return null;
  }

  async function lireBase() {
    try {
      await schema();
      const db = connexions();
      const sel = () => db.query('SELECT version, donnees FROM evn_documents WHERE cle = $1', [CLE]);
      let r = await sel();
      if (!r.rowCount) {
        const m = await migrer();
        if (m && m.panne) return { ok: false, panne: m.panne, d: vide(), version: null };
        r = await sel();
        if (!r.rowCount) return { ok: true, d: vide(), version: 0, fichiers: 0 };
      }
      return { ok: true, d: r.rows[0].donnees, version: Number(r.rows[0].version) };
    } catch (e) {
      return { ok: false, panne: expliquerBase(e), d: vide(), version: null };
    }
  }

  /** UPDATE ... WHERE version = celle lue : une seule ecriture passe. Une
   *  seconde, partie de la meme lecture, attend la premiere puis ne trouve
   *  plus la version qu'elle attendait — conflit, elle relira. */
  async function ecrireBase(d, version) {
    let c;
    try {
      await schema();
      c = await connexions().connect();
      await c.query('BEGIN');
      const json = JSON.stringify(d);
      const r = version === 0
        ? await c.query('INSERT INTO evn_documents (cle, version, donnees) VALUES ($1, 1, $2) '
          + 'ON CONFLICT (cle) DO NOTHING', [CLE, json])
        : await c.query('UPDATE evn_documents SET donnees = $3, version = version + 1, maj = now() '
          + 'WHERE cle = $1 AND version = $2', [CLE, version, json]);
      if (r.rowCount !== 1) {
        await c.query('ROLLBACK');
        return { ok: false, conflit: true };
      }
      const nouvelle = version + 1;
      // Les sauvegardes : chaque version ecrite, les `garde` plus recentes.
      await c.query('INSERT INTO evn_historique (cle, version, donnees) VALUES ($1, $2, $3)', [CLE, nouvelle, json]);
      await c.query('DELETE FROM evn_historique WHERE cle = $1 AND version <= $2', [CLE, nouvelle - garde]);
      await c.query('COMMIT');
      return { ok: true, version: nouvelle };
    } catch (e) {
      if (c) await c.query('ROLLBACK').catch(() => {});
      return { ok: false, message: expliquerBase(e) };
    } finally { if (c) c.release(); }
  }

  // ── l'interface commune ──────────────────────────────────────────────
  /** { ok, d, version, panne, fichiers }. `ok` faux : `panne` dit pourquoi,
   *  et `d` est un document vide qu'il ne faut JAMAIS reecrire. */
  async function lire() {
    if (mode === 'postgres') return lireBase();
    if (mode === 'blob') {
      const r = await lireBlob(false);
      if (!r.ok && !r.d) r.d = vide();
      return r;
    }
    if (!mem) mem = vide();
    return { ok: true, d: structuredClone(mem), version: memVersion, fichiers: 1 };
  }

  /** { ok, version } | { ok:false, conflit:true } | { ok:false, message } */
  async function ecrire(d, version) {
    if (mode === 'postgres') return ecrireBase(d, version);
    if (mode === 'blob') return ecrireBlob(d, version);
    if (version !== memVersion) return { ok: false, conflit: true };
    mem = structuredClone(d);
    memVersion++;
    return { ok: true, version: memVersion };
  }

  /**
   * Relire, appliquer, ecrire — et recommencer si quelqu'un a ecrit entre-temps.
   *
   * `appliquer(d)` modifie le document et peut rendre une valeur. Elle peut
   * tourner PLUSIEURS FOIS : rien d'exterieur dedans (ni courriel, ni appel
   * reseau) — seulement des changements sur `d`. Pour s'arreter sans rien
   * ecrire, elle rend { annuler: valeur }.
   *
   * Rend { ok:true, valeur, d } | { ok:true, annule:true, valeur }
   *    | { ok:false, panne } (lecture impossible) | { ok:false, message }.
   */
  // Combien de fois repartir apres un conflit. Chaque conflit veut dire
  // qu'une autre ecriture a abouti : avec n ecritures simultanees, la
  // derniere peut en perdre n - 1. A 6, vingt-cinq ecritures lancees
  // ensemble passaient sur un poste rapide (il en fallait 5) mais pas
  // toujours sur la machine plus lente de GitHub. 15 laisse de la marge ;
  // l'attente entre deux essais plafonne a 15 + 40 x 5 ms.
  async function modifier(appliquer, essais = 15) {
    for (let i = 0; i < essais; i++) {
      const l = await lire();
      if (!l.ok) return { ok: false, panne: l.panne || 'Lecture impossible.' };
      const valeur = await appliquer(l.d);
      if (valeur && typeof valeur === 'object' && 'annuler' in valeur) {
        return { ok: true, annule: true, valeur: valeur.annuler };
      }
      const w = await ecrire(l.d, l.version);
      if (w.ok) return { ok: true, valeur, d: l.d };
      if (!w.conflit) return { ok: false, message: w.message };
      // Un autre enregistrement est passe : on repart de l'etat frais.
      await pause(15 + Math.floor(Math.random() * 40) * Math.min(i + 1, 5));
    }
    return { ok: false, message: 'Trop de modifications au même instant : rien n’a été enregistré. Réessayez.' };
  }

  /** Combien de sauvegardes sont conservees (Parametres). */
  async function sauvegardes() {
    if (mode === 'postgres') {
      try {
        await schema();
        const r = await connexions().query('SELECT count(*)::int AS n FROM evn_historique WHERE cle = $1', [CLE]);
        return r.rows[0].n;
      } catch (e) { return null; }
    }
    if (mode === 'blob') { const r = await lireBlob(false); return r.fichiers || 0; }
    return mem ? 1 : 0;
  }

  /** L'ancienne copie publique dans Blob existe-t-elle encore ? (Parametres) */
  async function ancienneCopie() {
    if (mode !== 'postgres' || !jeton) return 0;
    try {
      const { list } = await blob();
      const { blobs } = await list({ prefix: prefixeBlob, token: jeton });
      return blobs.filter((b) => estDonnee(b.pathname)).length;
    } catch (e) { return null; }
  }

  return { mode, transactionnel: mode !== 'blob', lire, ecrire, modifier, sauvegardes, ancienneCopie };
}

/* ── Les compteurs (le plafond du concierge) ───────────────────────────
   Dans la base, un compteur est le MEME pour toutes les instances : c'est ce
   qui fait d'un plafond quotidien un vrai plafond. Sans base, chaque
   instance compte de son cote — mieux que rien, sans plus. */
const COMPTEURS = new Map();

/** Ajoute 1 au compteur `cle` (qui expire apres `dureeMs`) et rend sa valeur. */
async function compter(cle, dureeMs) {
  const k = cle + suffixe();
  if (URL_BASE) {
    try {
      await schema();
      const r = await connexions().query(`INSERT INTO evn_compteurs (cle, n, expire) VALUES ($1, 1, $2)
        ON CONFLICT (cle) DO UPDATE SET
          n = CASE WHEN evn_compteurs.expire < now() THEN 1 ELSE evn_compteurs.n + 1 END,
          expire = CASE WHEN evn_compteurs.expire < now() THEN EXCLUDED.expire ELSE evn_compteurs.expire END
        RETURNING n`, [k, new Date(Date.now() + dureeMs).toISOString()]);
      if (Math.random() < 0.02) connexions().query('DELETE FROM evn_compteurs WHERE expire < now()').catch(() => {});
      return r.rows[0].n;
    } catch (e) { /* la base hoquette : on compte en memoire */ }
  }
  const t = Date.now();
  const c = COMPTEURS.get(k);
  if (!c || c.expire < t) {
    COMPTEURS.set(k, { n: 1, expire: t + dureeMs });
    if (COMPTEURS.size > 2000) for (const [x, v] of COMPTEURS) if (v.expire < t) COMPTEURS.delete(x);
    return 1;
  }
  c.n++;
  return c.n;
}

/** La valeur d'un compteur, sans l'augmenter. */
async function valeur(cle) {
  const k = cle + suffixe();
  if (URL_BASE) {
    try {
      await schema();
      const r = await connexions().query('SELECT n FROM evn_compteurs WHERE cle = $1 AND expire >= now()', [k]);
      return r.rowCount ? r.rows[0].n : 0;
    } catch (e) { /* en memoire, ci-dessous */ }
  }
  const c = COMPTEURS.get(k);
  return c && c.expire >= Date.now() ? c.n : 0;
}

module.exports = { document, compter, valeur, expliquer, environnement };
