// Le passage de Vercel Blob a la base Postgres (site/api/_magasin.js).
//
// C'est la partie la plus delicate du magasin : en production, une fois les
// donnees recopiees dans la base, la copie PUBLIQUE de Blob est effacee —
// noms, e-mails et telephones des clients n'ont rien a faire dans un magasin
// public. Ce qui ne doit jamais arriver :
//   - effacer sans avoir recopie ;
//   - qu'un apercu (preview) efface les donnees que la production lit encore ;
//   - qu'un deploiement sans la base reparte d'un magasin vide ;
//   - qu'une production branchee sur la mauvaise base reparte de zero.
//
// Il faut une base Postgres :
//   DATABASE_URL=postgres://... node tests/migration.test.mjs
// Blob est simule : un magasin en memoire, aux memes fonctions.
import crypto from 'node:crypto';
import { createRequire } from 'node:module';

if (!process.env.DATABASE_URL) {
  console.log('\n  Passage Blob -> Postgres : ignore, DATABASE_URL absent.\n');
  process.exit(0);
}
const require = createRequire(import.meta.url);
const CHEMIN = require.resolve('../site/api/_magasin.js');
const magasin = require(CHEMIN);

let ok = 0, ko = 0;
function verifie(nom, condition, detail) {
  if (condition) { ok++; console.log('  ok     ', nom); }
  else { ko++; console.log('  ECHEC  ', nom, detail === undefined ? '' : JSON.stringify(detail)); }
}

/** Un faux Vercel Blob : list, put (avec suffixe aleatoire), del, et le fetch
 *  des adresses publiques. `illisible` : une adresse qui repond 403. */
function fauxBlob() {
  const fichiers = new Map();
  let t = Date.parse('2026-09-01T00:00:00Z');
  const poser = (pathname, contenu) => {
    const p = pathname.replace(/\.json$/, '') + '-' + crypto.randomBytes(8).toString('hex') + '.json';
    const b = { pathname: p, url: 'https://faux.blob/' + p, uploadedAt: new Date(t += 60_000).toISOString(), contenu };
    fichiers.set(p, b);
    return b;
  };
  const illisibles = new Set();
  return {
    fichiers, poser, illisibles,
    donnees: (prefixe) => [...fichiers.values()].filter((b) => b.pathname.startsWith(prefixe + '-')),
    marques: (prefixe) => [...fichiers.values()].filter((b) => b.pathname.startsWith(prefixe + '.deplacees')),
    outils: {
      blob: {
        async list({ prefix }) {
          return { blobs: [...fichiers.values()].filter((b) => b.pathname.startsWith(prefix))
            .map(({ contenu, ...b }) => b) };
        },
        async put(pathname, corps) { const b = poser(pathname, corps); return { url: b.url, pathname: b.pathname }; },
        async del(urls) {
          for (const u of [].concat(urls)) for (const [k, b] of fichiers) if (b.url === u) fichiers.delete(k);
        },
      },
      async fetch(url) {
        const b = [...fichiers.values()].find((x) => x.url === url);
        if (!b || illisibles.has(b.pathname)) return { ok: false, status: b ? 403 : 404 };
        return { ok: true, status: 200, json: async () => JSON.parse(b.contenu) };
      },
    },
  };
}

const PREFIXE = 'evannath/donnees';
const vide = () => ({ evenements: [], fermetures: [] });
const amorcer = (fb) => {
  fb.poser(PREFIXE + '.json', JSON.stringify({ evenements: [{ titre: 'ancien 1' }], fermetures: [] }));
  fb.poser(PREFIXE + '.json', JSON.stringify({ evenements: [{ titre: 'ancien 2' }], fermetures: [] }));
  fb.poser(PREFIXE + '.json', JSON.stringify({ evenements: [{ titre: 'actuel' }],
    fermetures: [{ client: 'Awa Kone', courriel: 'awa@exemple.ci' }] }));
};
const cle = 'donnees-' + crypto.randomBytes(4).toString('hex');
const doc = (fb, c = cle) => magasin.document({ cle: c, prefixeBlob: PREFIXE, garde: 10, vide,
  jeton: 'vercel_blob_rw_faux', nom: 'du fichier de données', outils: fb.outils });

console.log('\nUn apercu (preview) recopie, mais n efface rien');
const fb = fauxBlob();
amorcer(fb);
{
  process.env.VERCEL_ENV = 'preview';
  const l = await doc(fb).lire();
  verifie('il lit la version la plus recente', l.ok && l.d.evenements[0].titre === 'actuel', l);
  verifie('les donnees publiques sont toujours la (la production les lit encore)', fb.donnees(PREFIXE).length === 3);
  verifie('aucune marque posee', fb.marques(PREFIXE).length === 0);
}

console.log('\nLa production recopie, puis efface la copie publique');
{
  process.env.VERCEL_ENV = 'production';
  const d = doc(fb);
  const l = await d.lire();
  verifie('la production lit la version la plus recente', l.ok && l.d.evenements[0].titre === 'actuel', l);
  verifie('ses donnees sont dans la base (avec leurs sauvegardes : 2 anciennes + la courante)',
    (await d.sauvegardes()) === 3, await d.sauvegardes());
  verifie('la copie publique est effacee', fb.donnees(PREFIXE).length === 0, fb.donnees(PREFIXE).map((b) => b.pathname));
  verifie('une marque la remplace', fb.marques(PREFIXE).length === 1);
  verifie('la marque ne porte aucune donnee personnelle',
    !/Awa|@/.test(fb.marques(PREFIXE)[0].contenu), fb.marques(PREFIXE)[0].contenu);
  verifie('Parametres : plus d ancienne copie', (await d.ancienneCopie()) === 0);

  const m = await d.modifier((x) => { x.evenements.push({ titre: 'nouveau' }); });
  const l2 = await d.lire();
  verifie('ensuite, on ecrit dans la base', m.ok && l2.d.evenements.length === 2, l2.d.evenements);
  verifie('et rien ne revient dans Blob', fb.donnees(PREFIXE).length === 0);
  verifie('l apercu, lui, garde sa propre copie', ((process.env.VERCEL_ENV = 'preview'),
    (await doc(fb).lire()).d.evenements.length === 1));
  process.env.VERCEL_ENV = 'production';
}

console.log('\nHors de Vercel, EVN_ENV=production lit les donnees de la production');
{
  delete process.env.VERCEL_ENV;
  process.env.EVN_ENV = 'production';
  const l = await doc(fb).lire();
  verifie('sans VERCEL_ENV, EVN_ENV suffit', magasin.environnement() === 'production'
    && l.ok && l.d.evenements.length === 2, l.d && l.d.evenements);
  delete process.env.EVN_ENV;
  const local = await doc(fb).lire();
  verifie('sans l une ni l autre, le site se croit en local (et ne voit pas la production)',
    local.ok && local.d.evenements.length === 0, local.d && local.d.evenements);
  process.env.EVN_ENV = 'production';
  process.env.VERCEL_ENV = 'preview';
  verifie('EVN_ENV l emporte sur VERCEL_ENV', magasin.environnement() === 'production');
  delete process.env.EVN_ENV;
  process.env.VERCEL_ENV = 'production';
}

console.log('\nUn deploiement sans la base ne repart pas d un magasin vide');
{
  const url = process.env.DATABASE_URL;
  delete process.env.DATABASE_URL;
  delete require.cache[CHEMIN];
  const sansBase = require(CHEMIN);
  process.env.DATABASE_URL = url;
  delete require.cache[CHEMIN];
  const d = sansBase.document({ cle, prefixeBlob: PREFIXE, garde: 10, vide,
    jeton: 'vercel_blob_rw_faux', nom: 'du fichier de données', outils: fb.outils });
  verifie('il est bien en mode Blob', d.mode === 'blob', d.mode);
  const l = await d.lire();
  verifie('il lit la marque et refuse', !l.ok && /déplacées/.test(l.panne), l);
  const m = await d.modifier((x) => { x.evenements.push({ titre: 'perdu' }); });
  verifie('il n ecrit rien', !m.ok && fb.donnees(PREFIXE).length === 0, m);
}

console.log('\nUne production branchee sur la mauvaise base ne repart pas de zero');
{
  const d = doc(fb, 'donnees-autre-' + crypto.randomBytes(4).toString('hex'));
  const l = await d.lire();
  verifie('elle le dit, au lieu de rendre un document vide', !l.ok && /ne les contient pas/.test(l.panne), l);
  const m = await d.modifier((x) => { x.evenements.push({ titre: 'perdu' }); });
  verifie('et n ecrit rien', !m.ok, m);
  process.env.VERCEL_ENV = 'preview';
  const p = await doc(fb, 'donnees-autre-' + crypto.randomBytes(4).toString('hex')).lire();
  verifie('un apercu, lui, repart d un document vide', p.ok && p.version === 0, p);
  process.env.VERCEL_ENV = 'production';
}

console.log('\nUne version recente illisible : on ne recopie pas du vieux');
{
  const fb2 = fauxBlob();
  amorcer(fb2);
  const recente = [...fb2.fichiers.values()].sort((a, b) => (a.uploadedAt < b.uploadedAt ? 1 : -1))[0];
  fb2.illisibles.add(recente.pathname);
  const c = 'donnees-' + crypto.randomBytes(4).toString('hex');
  const d = doc(fb2, c);
  const l = await d.lire();
  verifie('la lecture le dit', !l.ok && /n’ont pas pu être recopiées/.test(l.panne), l);
  verifie('rien n est efface', fb2.donnees(PREFIXE).length === 3);
  fb2.illisibles.clear();
  const l2 = await d.lire();
  verifie('des que la version recente se lit, le passage se fait', l2.ok && l2.d.evenements[0].titre === 'actuel', l2);
}

console.log('\nDeux instances qui font le passage au meme instant');
{
  const fb3 = fauxBlob();
  amorcer(fb3);
  const c = 'donnees-' + crypto.randomBytes(4).toString('hex');
  const [a, b] = await Promise.all([doc(fb3, c).lire(), doc(fb3, c).lire()]);
  verifie('les deux lisent la meme chose', a.ok && b.ok && a.d.evenements[0].titre === 'actuel'
    && b.d.evenements[0].titre === 'actuel', [a, b]);
  verifie('un seul document, des sauvegardes non doublees', (await doc(fb3, c).sauvegardes()) === 3,
    await doc(fb3, c).sauvegardes());
}

console.log('\n  %d verifications, %d echec(s)\n', ok + ko, ko);
process.exit(ko ? 1 : 0);
