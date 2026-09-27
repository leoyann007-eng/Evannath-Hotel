// Tests des offres d'emploi, hors Vercel : on simule req et res.
// Lance depuis la racine du depot :  node tests/emplois.test.mjs
//
// Sans jeton de stockage, api/admin.js garde tout en memoire d'instance : le
// test s'execute dans un seul processus, et l'etat survit d'un appel a
// l'autre.
//
// CE QUI SE JOUE ICI. Une offre d'emploi n'est pas une affiche : elle
// s'adresse a quelqu'un qui cherche du travail, et qui prepare un dossier.
// Trois facons de lui faire perdre son temps, et ce fichier les couvre :
//
//   1. UNE OFFRE POURVUE QUI RESTE EN LIGNE. Personne ne pense a retirer une
//      annonce. Elle porte donc une date de fin, et passee cette date le
//      SERVEUR ne la sert plus — pas le navigateur. Une annonce masquee a
//      l'ecran mais lisible dans le JSON reste une annonce publiee.
//
//   2. UNE OFFRE TRONQUEE. Les descriptifs sont longs. Couper a la limite
//      sans rien dire rend une offre amputee de ses conditions : on refuse,
//      et on le dit.
//
//   3. UNE OFFRE QUI FUITE AVANT L'HEURE. Non publiee veut dire invisible,
//      y compris pour qui sait ouvrir du JSON.

process.env.ADMIN_MDP = 'essai';
delete process.env.BLOB_READ_WRITE_TOKEN;

const handler = (await import('../site/api/admin.js')).default;

let cookie = '';

function appel(query, { methode = 'GET', body = null, avecCookie = true, ip } = {}) {
  const req = {
    method: methode,
    query,
    body,
    headers: Object.assign({},
      avecCookie && cookie ? { cookie } : {},
      ip ? { 'x-forwarded-for': ip } : {}),
  };
  const out = { entetes: {} };
  const res = {
    statusCode: 0,
    setHeader(k, v) { out.entetes[k] = v; },
    getHeader(k) { return out.entetes[k]; },
    status(c) { out.code = c; return res; },
    json(j) { out.json = j; return res; },
  };
  return Promise.resolve(handler(req, res)).then(() => out);
}

let ok = 0, ko = 0;
function verifie(nom, condition, detail) {
  if (condition) { ok++; console.log('  ok     ', nom); }
  else { ko++; console.log('  ECHEC  ', nom, detail === undefined ? '' : JSON.stringify(detail)); }
}

const poser = (entree) =>
  appel({ a: 'enregistrer' }, { methode: 'POST', body: { type: 'emploi', entree } });
const retirer = (id) =>
  appel({ a: 'supprimer' }, { methode: 'POST', body: { type: 'emploi', id } });
const publiques = () => appel({ a: 'public' }, { avecCookie: false, ip: '10.0.0.9' });
const titres = (r) => ((r.json && r.json.emplois) || []).map((e) => e.titre);

const jour = (decalage) => {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() + decalage);
  return d.toISOString().slice(0, 10);
};

// ── Connexion ──────────────────────────────────────────────────────────────
{
  const r = await appel({ a: 'entrer' }, { methode: 'POST', body: { mdp: 'essai' } });
  verifie('connexion acceptee', r.code === 200, r.json);
  cookie = String(r.entetes['Set-Cookie'] || '').split(';')[0];
  verifie('un cookie de session est pose', cookie.startsWith('evn_adm='), cookie);
}

// ── Rien de publie : la liste existe et elle est vide ──────────────────────
{
  const r = await publiques();
  verifie('la route publique porte une liste emplois',
    Array.isArray(r.json && r.json.emplois), r.json);
  verifie('aucune offre au depart', titres(r).length === 0, titres(r));
}

// ── Ce qu'il faut pour enregistrer ────────────────────────────────────────
{
  const r = await poser({ contrat: 'CDI' });
  verifie('sans titre ni descriptif : refuse', r.code === 422, r.json);
  verifie('le refus nomme les deux champs manquants',
    (r.json.champs || []).includes('titre')
    && (r.json.champs || []).includes('descriptif'), r.json);
}
{
  const r = await poser({ titre: 'Réceptionniste de nuit' });
  verifie('un titre sans descriptif : refuse', r.code === 422, r.json);
}

// ── Une offre complete ────────────────────────────────────────────────────
let idNuit = '';
{
  const r = await poser({
    titre: 'Réceptionniste de nuit',
    contrat: 'CDI',
    departement: 'Réception',
    texte: 'Accueil des clients arrivant après 22 h.\nClôture de la journée.',
    profil: 'Une première expérience en hôtellerie.',
    postuler: 'recrutement@evannathhotel.com',
  });
  verifie('offre enregistree', r.code === 200, r.json);
  idNuit = r.json.entree && r.json.entree.id;
  verifie('elle recoit un identifiant', !!idNuit, r.json);
  verifie('les retours a la ligne du descriptif sont gardes',
    (r.json.entree.texte.match(/\n/g) || []).length === 1, r.json.entree.texte);
  verifie('elle est publiee par defaut', r.json.entree.publie === true, r.json.entree);
  verifie('elle porte une date de creation', !!r.json.entree.cree, r.json.entree);
}
{
  const r = await publiques();
  verifie('elle sort de la route publique',
    titres(r).includes('Réceptionniste de nuit'), titres(r));
}

// ── Non publiee : invisible, meme dans le JSON ────────────────────────────
{
  const r = await poser({
    titre: 'Chef de partie', texte: 'Poste en cuisine.', publie: false,
  });
  verifie('brouillon enregistre', r.code === 200, r.json);
  const p = await publiques();
  verifie("un brouillon ne sort pas de la route publique",
    !titres(p).includes('Chef de partie'), titres(p));
}

// ── La date de fin : le jour dit, l'offre tient encore ────────────────────
{
  const r = await poser({
    titre: 'Extra banquet', texte: 'Renfort pour un mariage.', fin: jour(0),
  });
  verifie('offre du jour meme enregistree', r.code === 200, r.json);
  const p = await publiques();
  verifie("le dernier jour, l'offre est encore visible",
    titres(p).includes('Extra banquet'), titres(p));
}
{
  const r = await poser({
    titre: 'Poste pourvu hier', texte: 'Ne doit plus paraitre.', fin: jour(-1),
  });
  verifie('offre expiree enregistree', r.code === 200, r.json);
  const p = await publiques();
  verifie("une offre expiree ne sort pas du serveur",
    !titres(p).includes('Poste pourvu hier'), titres(p));
}
{
  const r = await poser({
    titre: 'Ouvert demain encore', texte: 'Toujours ouvert.', fin: jour(1),
  });
  const p = await publiques();
  verifie('une offre qui court encore reste visible',
    titres(p).includes('Ouvert demain encore'), titres(p));
  verifie('date de fin mal formee : ramenee a null',
    (await poser({ titre: 'Sans fin', texte: 'x', fin: '15/10/2026' }))
      .json.entree.fin === null);
}

// ── On refuse plutot que de tronquer ──────────────────────────────────────
{
  const r = await poser({ titre: 'Trop long', texte: 'a'.repeat(2001) });
  verifie('un descriptif de plus de 2 000 signes : refuse', r.code === 422, r.code);
  verifie('le refus dit pourquoi, et dit que rien n a ete enregistre',
    /2 000/.test(r.json.message || '') && /rien/i.test(r.json.message || ''),
    r.json.message);
  const p = await publiques();
  verifie("l'offre refusee n'est nulle part", !titres(p).includes('Trop long'), titres(p));
}
{
  const r = await poser({ titre: 'Profil long', texte: 'ok', profil: 'b'.repeat(1201) });
  verifie('un profil de plus de 1 200 signes : refuse', r.code === 422, r.code);
}

// ── Modifier ne rajeunit pas l'offre ──────────────────────────────────────
{
  const avant = await publiques();
  const orig = (avant.json.emplois || []).find((e) => e.id === idNuit);
  const r = await poser({
    id: idNuit, titre: 'Réceptionniste de nuit', contrat: 'CDD',
    texte: 'Accueil des clients arrivant après 22 h.', cree: new Date().toISOString(),
  });
  verifie('modification enregistree', r.code === 200, r.json);
  verifie('le contrat a bien change', r.json.entree.contrat === 'CDD', r.json.entree);
  verifie("la date de creation d'origine est conservee",
    r.json.entree.cree === orig.cree, [orig.cree, r.json.entree.cree]);
  const p = await publiques();
  verifie("la modification n'a pas cree de doublon",
    titres(p).filter((t) => t === 'Réceptionniste de nuit').length === 1, titres(p));
}

// ── Supprimer ─────────────────────────────────────────────────────────────
{
  const r = await retirer(idNuit);
  verifie('suppression acceptee', r.code === 200, r.json);
  const p = await publiques();
  verifie("l'offre supprimee ne sort plus",
    !titres(p).includes('Réceptionniste de nuit'), titres(p));
}

// ── Les autres collections n'ont pas bouge ────────────────────────────────
{
  const p = await publiques();
  verifie('evenements, promotions et campagnes sont toujours servis',
    Array.isArray(p.json.evenements) && Array.isArray(p.json.promotions)
    && Array.isArray(p.json.campagnes), Object.keys(p.json));
}

console.log('\n  %d verifications, %d echec(s)\n', ok + ko, ko);
process.exit(ko ? 1 : 0);
