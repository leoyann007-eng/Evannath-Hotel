// Tests du calendrier de disponibilite, hors Vercel : on simule req et res.
// Lance depuis la racine du depot :  node tests/dispo.test.mjs
//
// Sans jeton de stockage, api/admin.js garde tout en memoire d'instance. Le
// test s'execute donc dans un seul processus, et l'etat survit d'un appel a
// l'autre — c'est exactement ce qu'il faut ici.
//
// CE QUI SE JOUE DANS CE FICHIER : la regle des nuits. Un sejour du 24 au 26
// occupe les nuits du 24 et du 25, pas celle du 26. Une borne decalee d'un
// jour, et l'hotel refuse une chambre libre ou en vend une occupee. Les cas
// limites sont donc tous ecrits, y compris ceux qui ont l'air evidents.

process.env.ADMIN_MDP = 'essai';
delete process.env.BLOB_READ_WRITE_TOKEN;

const handler = (await import('../site/api/admin.js')).default;

let cookie = '';

function appel(query, { methode = 'GET', body = null, avecCookie = true } = {}) {
  const req = {
    method: methode,
    query,
    body,
    headers: avecCookie && cookie ? { cookie } : {},
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

const etat = (r, slug) => (r.json && r.json.etats) ? r.json.etats[slug] : undefined;

const dispo = (du, au, chambre) =>
  appel({ a: 'dispo', du, au, chambre }, { avecCookie: false });

// ── Connexion ──────────────────────────────────────────────────────────────
{
  const r = await appel({ a: 'entrer' }, { methode: 'POST', body: { mdp: 'essai' } });
  verifie('connexion acceptee', r.code === 200, r.json);
  cookie = String(r.entetes['Set-Cookie'] || '').split(';')[0];
  verifie('un cookie de session est pose', cookie.startsWith('evn_adm='), cookie);
}

// ── Avant toute saisie, le site ne promet rien ─────────────────────────────
{
  const r = await dispo('2026-12-24', '2026-12-26', 'chambre-standard');
  verifie('calendrier vide : l etat est inconnu, pas libre',
    etat(r, 'chambre-standard') === 'inconnu', r.json);
}

// ── La reception declare la categorie ouverte ──────────────────────────────
{
  const r = await appel({ a: 'ouvrir' },
    { methode: 'POST', body: { chambre: 'chambre-standard', ouverte: true } });
  verifie('categorie declaree ouverte', r.code === 200, r.json);

  const d = await dispo('2026-12-24', '2026-12-26', 'chambre-standard');
  verifie('declaree ouverte : libre', etat(d, 'chambre-standard') === 'libre', d.json);

  const autre = await dispo('2026-12-24', '2026-12-26', 'suite-arabe');
  verifie('une autre categorie reste inconnue',
    etat(autre, 'suite-arabe') === 'inconnu', autre.json);
}

// ── Une fermeture, et la regle des nuits ───────────────────────────────────
{
  const r = await appel({ a: 'enregistrer' }, { methode: 'POST', body: {
    type: 'fermeture',
    entree: { id: 'f-noel', chambre: 'chambre-standard',
              debut: '2026-12-24', fin: '2026-12-26', motif: 'groupe Sonatel' },
  } });
  verifie('fermeture enregistree', r.code === 200, r.json);
}

const CAS = [
  // [arrivee,      depart,       attendu,   ce que le sejour occupe]
  ['2026-12-24', '2026-12-25', 'complet', 'la nuit du 24, fermee'],
  ['2026-12-26', '2026-12-27', 'complet', 'la nuit du 26, derniere nuit fermee'],
  ['2026-12-23', '2026-12-24', 'libre',   'la seule nuit du 23 — on part le 24'],
  ['2026-12-27', '2026-12-28', 'libre',   'la nuit du 27, le lendemain de la fermeture'],
  ['2026-12-20', '2026-12-30', 'complet', 'dix nuits, dont trois fermees'],
  ['2026-12-25', '2026-12-26', 'complet', 'la nuit du 25, au milieu'],
  ['2026-12-22', '2026-12-23', 'libre',   'bien avant'],
  ['2027-01-05', '2027-01-08', 'libre',   'bien apres'],
];

for (const [du, au, attendu, quoi] of CAS) {
  const r = await dispo(du, au, 'chambre-standard');
  verifie(`${du} → ${au} : ${attendu} (${quoi})`,
    etat(r, 'chambre-standard') === attendu, r.json);
}

// ── Ce que le visiteur ne doit jamais recevoir ─────────────────────────────
{
  const r = await dispo('2026-12-24', '2026-12-26', 'chambre-standard');
  const texte = JSON.stringify(r.json);
  verifie('le motif de la fermeture ne sort pas', !/Sonatel/.test(texte), texte);
  verifie('les dates de la fermeture ne sortent pas',
    !/"debut"|"fin"|fermetures/.test(texte), texte);
}

// ── Des dates qui ne veulent rien dire ne promettent rien ──────────────────
for (const [du, au, quoi] of [
  ['2026-12-24', '2026-12-24', 'zero nuit'],
  ['2026-12-26', '2026-12-24', 'depart avant l arrivee'],
  ['', '2026-12-26', 'arrivee absente'],
  ['pas-une-date', '2026-12-26', 'arrivee illisible'],
  ['2026-13-45', '2026-12-26', 'arrivee au format juste mais impossible'],
]) {
  const r = await dispo(du, au, 'chambre-standard');
  verifie(`${quoi} : aucun etat rendu`,
    r.code === 200 && Object.keys(r.json.etats || {}).length === 0, r.json);
}

// ── Une fermeture de tout l hotel ──────────────────────────────────────────
{
  await appel({ a: 'ouvrir' },
    { methode: 'POST', body: { chambre: 'suite-arabe', ouverte: true } });
  await appel({ a: 'enregistrer' }, { methode: 'POST', body: {
    type: 'fermeture',
    entree: { id: 'f-travaux', chambre: '*',
              debut: '2027-06-05', fin: '2027-06-20', motif: 'travaux' },
  } });
  for (const slug of ['chambre-standard', 'suite-arabe']) {
    const r = await dispo('2027-06-10', '2027-06-12', slug);
    verifie(`fermeture « * » : ${slug} est complet`,
      etat(r, slug) === 'complet', r.json);
  }
  const apres = await dispo('2027-06-20', '2027-06-21', 'suite-arabe');
  verifie('fermeture « * » : la nuit du 20 est encore fermee',
    etat(apres, 'suite-arabe') === 'complet', apres.json);
  const fini = await dispo('2027-06-21', '2027-06-22', 'suite-arabe');
  verifie('fermeture « * » : la nuit du 21 est libre',
    etat(fini, 'suite-arabe') === 'libre', fini.json);
}

// ── Une fermeture l emporte toujours sur une ouverture ─────────────────────
{
  await appel({ a: 'ouvrir' },
    { methode: 'POST', body: { chambre: 'chambre-standard', ouverte: true } });
  const r = await dispo('2026-12-25', '2026-12-26', 'chambre-standard');
  verifie('rouvrir une categorie ne rouvre pas ses nuits fermees',
    etat(r, 'chambre-standard') === 'complet', r.json);
}

// ── Saisies de travers ─────────────────────────────────────────────────────
{
  const r = await appel({ a: 'enregistrer' }, { methode: 'POST', body: {
    type: 'fermeture',
    entree: { id: 'f-envers', chambre: 'suite-anglaise',
              debut: '2027-03-10', fin: '2027-03-05' },
  } });
  verifie('periode a l envers acceptee et remise a l endroit', r.code === 200, r.json);
  await appel({ a: 'ouvrir' },
    { methode: 'POST', body: { chambre: 'suite-anglaise', ouverte: true } });
  const d = await dispo('2027-03-07', '2027-03-08', 'suite-anglaise');
  verifie('periode remise a l endroit : la nuit du 7 est bien fermee',
    etat(d, 'suite-anglaise') === 'complet', d.json);
}

{
  const r = await appel({ a: 'enregistrer' }, { methode: 'POST', body: {
    type: 'fermeture',
    entree: { id: 'f-une-nuit', chambre: 'suite-anglaise', debut: '2027-04-02' },
  } });
  verifie('fin absente : une seule nuit', r.code === 200, r.json);
  const nuit = await dispo('2027-04-02', '2027-04-03', 'suite-anglaise');
  verifie('une seule nuit : la nuit du 2 est fermee',
    etat(nuit, 'suite-anglaise') === 'complet', nuit.json);
  const suivante = await dispo('2027-04-03', '2027-04-04', 'suite-anglaise');
  verifie('une seule nuit : la nuit du 3 est libre',
    etat(suivante, 'suite-anglaise') === 'libre', suivante.json);
}

{
  const r = await appel({ a: 'enregistrer' }, { methode: 'POST', body: {
    type: 'fermeture', entree: { chambre: '', debut: '2027-05-01' },
  } });
  verifie('fermeture sans categorie refusee', r.code === 422, r.json);

  const s = await appel({ a: 'enregistrer' }, { methode: 'POST', body: {
    type: 'fermeture', entree: { chambre: 'chambre-standard', debut: '' },
  } });
  verifie('fermeture sans date refusee', s.code === 422, s.json);
}

// ── La route publique reste publique, les ecritures non ────────────────────
{
  const r = await appel({ a: 'dispo', du: '2026-12-24', au: '2026-12-26' },
    { avecCookie: false });
  verifie('la lecture ne demande pas de session', r.code === 200, r.json);
  verifie('sans chambre precisee : toutes les categories declarees',
    Object.keys(r.json.etats).length >= 2, r.json);

  const w = await appel({ a: 'ouvrir' }, { methode: 'POST', avecCookie: false,
    body: { chambre: 'suite-arabe', ouverte: true } });
  verifie('ouvrir une categorie demande une session', w.code === 401, w.json);

  const f = await appel({ a: 'enregistrer' }, { methode: 'POST', avecCookie: false,
    body: { type: 'fermeture', entree: { chambre: 'suite-arabe', debut: '2027-08-01' } } });
  verifie('enregistrer une fermeture demande une session', f.code === 401, f.json);
}

// ── Revenir a « je ne sais pas » ───────────────────────────────────────────
{
  await appel({ a: 'ouvrir' },
    { methode: 'POST', body: { chambre: 'suite-arabe', ouverte: false } });
  const r = await dispo('2027-09-01', '2027-09-03', 'suite-arabe');
  verifie('categorie refermee : retour a inconnu',
    etat(r, 'suite-arabe') === 'inconnu', r.json);
}

console.log(`\n${ok} verification(s) passee(s), ${ko} en echec.`);
if (ko) process.exit(1);
