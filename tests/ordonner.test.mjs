// Tests du reordonnancement (a=ordonner), hors Vercel : on simule req et res.
// Lance depuis la racine du depot :  node tests/ordonner.test.mjs
//
// LE DEFAUT. Le serveur reconstruisait la liste a partir des seuls
// identifiants recus, et jetait le reste. Une page d'administration ouverte
// AVANT qu'un collegue cree un evenement envoyait un ordre sans lui : le
// nouvel evenement disparaissait, et le journal ne disait que « a change
// l'ordre ». Pire, appele a la main avec type 'fermeture' ou 'chambre' et
// une liste vide, il effacait toutes les reservations, ou toutes les
// chambres, sans le garde-fou de « supprimer ».

process.env.ADMIN_MDP = 'essai';
delete process.env.BLOB_READ_WRITE_TOKEN;

const handler = (await import('../site/api/admin.js')).default;

let cookie = '';

function appel(query, { methode = 'GET', body = null } = {}) {
  const req = { method: methode, query, body, headers: cookie ? { cookie } : {} };
  const out = { entetes: {} };
  const res = {
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

const poser = (type, entree) =>
  appel({ a: 'enregistrer' }, { methode: 'POST', body: { type, entree } }).then((r) => r.json.entree);
const ordonner = (type, ordre) =>
  appel({ a: 'ordonner' }, { methode: 'POST', body: { type, ordre } });
const tout = () => appel({ a: 'tout' }).then((r) => r.json.donnees);
const titres = (l) => (l || []).map((x) => x.titre);

{
  const r = await appel({ a: 'entrer' }, { methode: 'POST', body: { mdp: 'essai' } });
  cookie = String(r.entetes['Set-Cookie'] || '').split(';')[0];
  verifie('connexion acceptee', r.code === 200, r.json);
}

// ── Un ordre complet est applique tel quel ─────────────────────────────────
const a = await poser('evenement', { titre: 'A' });
const b = await poser('evenement', { titre: 'B' });
const c = await poser('evenement', { titre: 'C' });
{
  const r = await ordonner('evenement', [c.id, a.id, b.id]);
  verifie('ordre complet accepte', r.code === 200, r.json);
  verifie('ordre complet applique', titres((await tout()).evenements).join() === 'C,A,B',
    titres((await tout()).evenements));
}

// ── Une page perimee ne supprime rien ─────────────────────────────────────
{
  const d = await poser('evenement', { titre: 'D, cree entre-temps' });
  await ordonner('evenement', [a.id, c.id, b.id]);   // la page ne connait pas D
  const l = titres((await tout()).evenements);
  verifie('l entree absente de l ordre est conservee', l.includes(d.titre), l);
  verifie('elle garde sa place, a la suite', l.join() === 'A,C,B,' + d.titre, l);
}

// ── Doublons et inconnus ne fabriquent ni copie ni trou ───────────────────
{
  await ordonner('evenement', [b.id, b.id, 'inconnu', a.id]);
  const l = (await tout()).evenements;
  verifie('aucun doublon', new Set(l.map((x) => x.id)).size === l.length, titres(l));
  verifie('rien de perdu', l.length === 4, titres(l));
  verifie('les doublons comptent une fois', titres(l).slice(0, 2).join() === 'B,A', titres(l));
}

// ── Une liste vide ne vide rien ───────────────────────────────────────────
{
  await ordonner('evenement', []);
  verifie('ordre vide : rien n est efface', (await tout()).evenements.length === 4);
}

// ── Promotions et campagnes suivent la meme regle ─────────────────────────
{
  const p1 = await poser('promotion', { titre: 'P1', remise: { valeur: 10 } });
  await poser('promotion', { titre: 'P2', remise: { valeur: 5 } });
  const r = await ordonner('promotion', [p1.id]);
  verifie('promotion : reordonnee', r.code === 200, r.json);
  verifie('promotion : rien de perdu', (await tout()).promotions.length === 2);
}

// ── Les chambres et les sejours n ont pas d ordre ─────────────────────────
{
  const ch = await poser('chambre', { numero: '101', categorie: 'chambre-standard' });
  await poser('fermeture', { cible: ch.id, debut: '2099-01-01', fin: '2099-01-02', motif: 'test' });
  const r1 = await ordonner('chambre', []);
  const r2 = await ordonner('fermeture', []);
  verifie('chambre : refuse', r1.code === 422, r1.json);
  verifie('fermeture : refuse', r2.code === 422, r2.json);
  const d = await tout();
  verifie('les chambres sont intactes', d.chambres.length === 1);
  verifie('les fermetures sont intactes', d.fermetures.length === 1);
}

console.log('\n  %d verifications, %d echec(s)\n', ok + ko, ko);
process.exit(ko ? 1 : 0);
