// Tests du verrou anti-collision.  node tests/collision.test.mjs
//
// CE QUI EST EPROUVE ICI, ET POURQUOI CA N'ETAIT PAS TESTABLE AVANT.
//
// Le magasin n'a pas d'ecriture conditionnelle : chaque enregistrement ecrit
// le document entier, et la lecture prend le plus recent. Deux demandes
// simultanees lisent donc le meme etat, choisissent la MEME chambre — car
// premiereLibre() rend toujours le plus petit numero libre — puis ecrivent
// chacune son instantane. La seconde efface la retenue de la premiere.
//
// Ce defaut etait INVISIBLE en local. En memoire, lire() rendait la
// reference vivante : deux requetes partageaient le meme objet et se
// voyaient l'une l'autre instantanement. Il ne se produisait qu'en
// production, ou chaque lecture est un instantane. lire() rend desormais une
// copie dans les deux modes — et la course devient reproductible ici.
//
// LA GARANTIE TENUE. Ce n'est pas un vrai verrou : Blob ne sait pas
// comparer-et-echanger, et seul un magasin transactionnel le pourrait. La
// garantie est plus faible, et c'est elle qu'on teste :
//
//   ON NE DIT JAMAIS « GARDEE » A UN CLIENT DONT LA RETENUE N'EXISTE PAS.
//
// Tant qu'on n'encaisse pas, elle suffit. Le jour du paiement en ligne, il
// faudra davantage — voir notre-comprehension.md.

process.env.ADMIN_MDP = 'essai';
delete process.env.BLOB_READ_WRITE_TOKEN;

const mod = await import('../site/api/admin.js');
const handler = mod.default;
const { plusAncienne, nuitsSeCroisent, retenueGagne } = mod.default.regles;

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

// ── La regle qui departage, eprouvee seule ────────────────────────────────
// Une regle de course doit rendre le MEME verdict des deux cotes. Si
// plusAncienne(a,b) et plusAncienne(b,a) valaient vrai tous les deux, les
// deux demandes se croiraient gagnantes et le verrou ne servirait a rien.

console.log('\n── La regle qui departage ──');

{
  const a = { id: 'aaa', cree: '2026-09-24T10:00:00.000Z' };
  const b = { id: 'bbb', cree: '2026-09-24T10:00:00.001Z' };
  verifie('la plus ancienne gagne', plusAncienne(a, b) === true);
  verifie('et la plus recente perd', plusAncienne(b, a) === false);
}
{
  // Egalite a la milliseconde : l'identifiant tranche, et il tranche dans un
  // seul sens.
  const a = { id: 'aaa', cree: '2026-09-24T10:00:00.000Z' };
  const b = { id: 'bbb', cree: '2026-09-24T10:00:00.000Z' };
  verifie('a egalite, l identifiant tranche', plusAncienne(a, b) === true);
  verifie('et il tranche dans un seul sens', plusAncienne(b, a) === false);
}
{
  // L'ordre est TOTAL : jamais deux gagnantes, jamais deux perdantes.
  const instants = ['2026-09-24T10:00:00.000Z', '2026-09-24T10:00:00.001Z', ''];
  const ids = ['aaa', 'bbb', 'ccc'];
  let symetrique = true;
  for (const ca of instants) for (const ia of ids) {
    for (const cb of instants) for (const ib of ids) {
      if (ca === cb && ia === ib) continue;
      const a = { id: ia, cree: ca }, b = { id: ib, cree: cb };
      if (plusAncienne(a, b) === plusAncienne(b, a)) symetrique = false;
    }
  }
  verifie('l ordre est total sur 36 paires : jamais deux gagnantes', symetrique);
}
{
  // Une fermeture posee par la reception l'emporte toujours. Meme creee
  // apres, meme tres apres : elle decide, le formulaire demande.
  const nous = { id: 'aaa', cree: '2026-09-24T10:00:00.000Z', nature: 'client' };
  const reception = { id: 'zzz', cree: '2027-01-01T00:00:00.000Z', nature: 'vente' };
  verifie('la reception l emporte meme creee apres',
    retenueGagne(nous, [reception]) === false);
  const horsService = Object.assign({}, reception, { nature: 'hors-service' });
  verifie('une chambre hors service l emporte aussi',
    retenueGagne(nous, [horsService]) === false);
  const plusRecente = { id: 'bbb', cree: '2026-09-24T10:00:00.001Z', nature: 'client' };
  verifie('face a une demande plus recente, on gagne',
    retenueGagne(nous, [plusRecente]) === true);
  verifie('une seule rivale gagnante suffit a nous faire perdre',
    retenueGagne(nous, [plusRecente, reception]) === false);

  /* Une reservation CONFIRMEE est ferme : elle l'emporte meme creee apres.
     La comparer par l'age laisserait une demande venue du site deloger un
     client dont la chambre est acquise. */
  const confirmee = { id: 'ccc', cree: '2027-06-01T00:00:00.000Z',
    nature: 'client', statut: 'confirmee' };
  verifie('une reservation confirmee l emporte meme creee apres',
    retenueGagne(nous, [confirmee]) === false);
  const attenteRecente = { id: 'ddd', cree: '2027-06-01T00:00:00.000Z',
    nature: 'client', statut: 'attente' };
  verifie('mais une simple demande plus recente, non',
    retenueGagne(nous, [attenteRecente]) === true);
}

console.log('\n── Les nuits qui se croisent ──');
{
  const n = (debut, fin) => ({ debut, fin });
  verifie('deux sejours disjoints ne se croisent pas',
    nuitsSeCroisent(n('2026-09-10', '2026-09-12'), n('2026-09-13', '2026-09-15')) === false);
  verifie('deux sejours qui se touchent d une nuit se croisent',
    nuitsSeCroisent(n('2026-09-10', '2026-09-12'), n('2026-09-12', '2026-09-15')) === true);
  verifie('une fermeture sans fin croise tout ce qui suit',
    nuitsSeCroisent(n('2026-09-10', null), n('2030-01-01', '2030-01-02')) === true);
  verifie('mais pas ce qui la precede',
    nuitsSeCroisent(n('2026-09-10', null), n('2026-01-01', '2026-01-02')) === false);
  verifie('le croisement est symetrique',
    nuitsSeCroisent(n('2026-09-10', '2026-09-20'), n('2026-09-15', '2026-09-16'))
    === nuitsSeCroisent(n('2026-09-15', '2026-09-16'), n('2026-09-10', '2026-09-20')));
}

// ── La course, pour de vrai ───────────────────────────────────────────────

console.log('\n── La course ──');

const entrer = await appel({ a: 'entrer' },
  { methode: 'POST', body: { mdp: 'essai' }, avecCookie: false });
cookie = String(entrer.entetes['Set-Cookie'] || '').split(';')[0];
verifie('session ouverte', !!cookie);

const poserChambre = (numero, categorie) => appel({ a: 'enregistrer' },
  { methode: 'POST', body: { type: 'chambre', entree: { numero, categorie, etage: '1' } } });

const demande = (nom, categorie, du, au, ip) => appel({ a: 'demande' },
  { methode: 'POST', avecCookie: false, ip,
    body: { nom, categorie, du, au } });

const tout = () => appel({ a: 'tout' }).then((r) => r.json.donnees);

/** Les retenues vivantes qui visent une chambre donnee. */
const retenuesVivantes = (d, idChambre) => (d.fermetures || []).filter(
  (f) => f.cible === idChambre && f.nature === 'client' && f.statut !== 'annulee'
    && (!f.expire || Date.parse(f.expire) >= Date.now()));

// UNE seule chambre, DEUX demandes simultanees.
await poserChambre('101', 'test-une');
{
  const [a, b] = await Promise.all([
    demande('Client A', 'test-une', '2026-10-01', '2026-10-03', '10.0.0.1'),
    demande('Client B', 'test-une', '2026-10-01', '2026-10-03', '10.0.0.2'),
  ]);
  const gardees = [a, b].filter((r) => r.json.retenue).length;
  verifie('une chambre, deux demandes : une seule est gardee', gardees === 1,
    { a: a.json, b: b.json });
  verifie('celle qui echoue dit « complet », pas une raison inventee',
    [a, b].every((r) => r.json.retenue || r.json.raison === 'complet'),
    [a.json, b.json]);

  const d = await tout();
  const ch = d.chambres.find((c) => c.numero === '101');
  const vivantes = retenuesVivantes(d, ch.id);
  verifie('et le magasin ne porte QU UNE retenue vivante sur cette chambre',
    vivantes.length === 1, vivantes.map((f) => f.client));

  // L'invariant qui compte : ce qu'on a promis existe.
  const promis = [a, b].filter((r) => r.json.retenue).length;
  verifie('autant de retenues en magasin que de clients a qui on a promis',
    vivantes.length === promis);
}

// DEUX chambres libres, DEUX demandes simultanees : les deux doivent
// aboutir, sur des chambres DIFFERENTES. C'est le chemin de reprise : les
// deux visent d'abord le plus petit numero, l'une perd, relit, et prend
// l'autre chambre.
await poserChambre('201', 'test-deux');
await poserChambre('202', 'test-deux');
{
  const [a, b] = await Promise.all([
    demande('Client C', 'test-deux', '2026-10-01', '2026-10-03', '10.0.0.3'),
    demande('Client D', 'test-deux', '2026-10-01', '2026-10-03', '10.0.0.4'),
  ]);
  verifie('deux chambres, deux demandes : les deux sont gardees',
    a.json.retenue === true && b.json.retenue === true, [a.json, b.json]);

  const d = await tout();
  const ids = d.chambres.filter((c) => c.categorie === 'test-deux').map((c) => c.id);
  const parChambre = ids.map((id) => retenuesVivantes(d, id).length);
  verifie('une retenue par chambre, pas deux sur la meme',
    parChambre.length === 2 && parChambre.every((n) => n === 1), parChambre);
}

// QUATRE demandes simultanees pour TROIS chambres : trois gardees, une
// refusee — et jamais deux retenues sur la meme chambre.
await poserChambre('301', 'test-trois');
await poserChambre('302', 'test-trois');
await poserChambre('303', 'test-trois');
{
  const rs = await Promise.all([1, 2, 3, 4].map((i) =>
    demande('Client ' + i, 'test-trois', '2026-11-01', '2026-11-03', '10.0.1.' + i)));
  const gardees = rs.filter((r) => r.json.retenue).length;
  verifie('quatre demandes pour trois chambres : trois gardees', gardees === 3,
    rs.map((r) => r.json));

  const d = await tout();
  const ids = d.chambres.filter((c) => c.categorie === 'test-trois').map((c) => c.id);
  const parChambre = ids.map((id) => retenuesVivantes(d, id).length);
  verifie('aucune chambre ne porte deux retenues',
    parChambre.every((n) => n <= 1), parChambre);
  verifie('autant de retenues que de promesses',
    parChambre.reduce((s, n) => s + n, 0) === gardees);
}

// Une categorie SANS chambre libre : la course ne doit rien inventer.
await poserChambre('401', 'test-pleine');
{
  await demande('Occupant', 'test-pleine', '2026-12-01', '2026-12-05', '10.0.2.1');
  const rs = await Promise.all([1, 2].map((i) =>
    demande('Tardif ' + i, 'test-pleine', '2026-12-02', '2026-12-04', '10.0.2.' + (i + 1))));
  verifie('sur une categorie deja prise, aucune retenue',
    rs.every((r) => r.json.retenue === false && r.json.raison === 'complet'),
    rs.map((r) => r.json));
}

// ── `cree` ne rajeunit pas ────────────────────────────────────────────────
// Le formulaire de l'administration ne renvoie pas ce champ. Sans
// precaution, chaque enregistrement lui donnerait un instant neuf — et une
// reservation confirmee rajeunirait a chaque correction de faute de frappe.

console.log('\n── L instant de creation survit aux modifications ──');
{
  await poserChambre('501', 'test-age');
  await demande('Client E', 'test-age', '2027-03-01', '2027-03-03', '10.0.3.1');

  const avant = await tout();
  const f = (avant.fermetures || []).find((x) => x.client === 'Client E');
  verifie('la retenue porte un instant de creation', !!(f && f.cree), f && f.cree);

  // On la confirme, comme le ferait la reception.
  await appel({ a: 'enregistrer' }, { methode: 'POST', body: { type: 'fermeture',
    entree: { id: f.id, cible: f.cible, debut: f.debut, fin: f.fin,
      nature: 'client', statut: 'confirmee', client: f.client } } });

  const apres = await tout();
  const g = (apres.fermetures || []).find((x) => x.id === f.id);
  verifie('confirmee par la reception, elle garde son instant de creation',
    !!g && g.cree === f.cree, { avant: f.cree, apres: g && g.cree });
  verifie('et elle est bien passee en confirmee', !!g && g.statut === 'confirmee');
}

// ── Les deux routes disent la meme chose ──────────────────────────────────
// « Complet » est une AFFIRMATION : l'hotel est plein. Sans aucune chambre
// saisie dans la categorie, on ne sait rien — et `a=dispo` repond deja
// `inconnu`. Deux routes qui repondent differemment sur le meme etat sont
// deux verites, et l'une des deux est fausse.

console.log('\n── Sans chambre saisie, les deux routes s accordent ──');
{
  const vue = await appel({ a: 'dispo', du: '2028-01-01', au: '2028-01-03',
    chambre: 'categorie-jamais-saisie' }, { avecCookie: false });
  verifie('a=dispo ne sait rien',
    vue.json.etats['categorie-jamais-saisie'] === 'inconnu',
    vue.json.etats);

  const d = await demande('Client F', 'categorie-jamais-saisie',
    '2028-01-01', '2028-01-03', '10.0.4.1');
  verifie('a=demande ne sait rien non plus, et n affirme pas « complet »',
    d.json.retenue === false && d.json.raison === 'inconnu', d.json);
}
{
  // Mais quand la categorie EXISTE et qu'elle est prise, « complet » est vrai.
  await poserChambre('601', 'test-vraiment-pleine');
  await demande('Occupant', 'test-vraiment-pleine', '2028-02-01', '2028-02-05', '10.0.5.1');
  const d = await demande('Tardif', 'test-vraiment-pleine',
    '2028-02-02', '2028-02-04', '10.0.5.2');
  verifie('une categorie saisie et prise dit bien « complet »',
    d.json.retenue === false && d.json.raison === 'complet', d.json);
}

console.log('\n%d verification(s) passee(s), %d en echec.', ok, ko);
process.exit(ko ? 1 : 0);
