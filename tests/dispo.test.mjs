// Tests du calendrier de disponibilite, hors Vercel : on simule req et res.
// Lance depuis la racine du depot :  node tests/dispo.test.mjs
//
// Sans jeton de stockage, api/admin.js garde tout en memoire d'instance. Le
// test s'execute donc dans un seul processus, et l'etat survit d'un appel a
// l'autre — c'est exactement ce qu'il faut ici.
//
// DEUX CHOSES SE JOUENT DANS CE FICHIER.
//
// 1. LE DECOMPTE. Le site vend des categories, la reception tient des
//    chambres. « Reste-t-il au moins une Standard ces nuits-la ? » est une
//    question de comptage, et un decompte faux d'une unite annonce complet
//    quand il reste une chambre, ou libre quand il n'en reste aucune.
//
// 2. LA REGLE DES NUITS. Un sejour du 24 au 26 occupe les nuits du 24 et du
//    25, pas celle du 26. Une borne decalee d'un jour, et l'hotel refuse une
//    chambre libre ou en vend une occupee. Les cas limites sont tous ecrits,
//    y compris ceux qui ont l'air evidents.

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
      /* Le debit de la route publique se compte par IP : sans adresse
         distincte, les tests se bloqueraient les uns les autres. */
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

const etat = (r, slug) => (r.json && r.json.etats) ? r.json.etats[slug] : undefined;

const dispo = (du, au, categorie) =>
  appel({ a: 'dispo', du, au, chambre: categorie }, { avecCookie: false });

const poser = (type, entree) =>
  appel({ a: 'enregistrer' }, { methode: 'POST', body: { type, entree } });

const retirer = (type, id) =>
  appel({ a: 'supprimer' }, { methode: 'POST', body: { type, id } });

// ── Connexion ──────────────────────────────────────────────────────────────
{
  const r = await appel({ a: 'entrer' }, { methode: 'POST', body: { mdp: 'essai' } });
  verifie('connexion acceptee', r.code === 200, r.json);
  cookie = String(r.entetes['Set-Cookie'] || '').split(';')[0];
  verifie('un cookie de session est pose', cookie.startsWith('evn_adm='), cookie);
}

// ── Aucune chambre saisie : le site ne promet rien ─────────────────────────
{
  const r = await dispo('2026-12-24', '2026-12-26', 'chambre-standard');
  verifie('categorie sans chambre : inconnu, pas libre',
    etat(r, 'chambre-standard') === 'inconnu', r.json);
}

// ── Trois chambres Standard ────────────────────────────────────────────────
const STD = {};
for (const numero of ['25', '26', '27']) {
  const r = await poser('chambre', { numero, categorie: 'chambre-standard' });
  verifie(`chambre ${numero} enregistree`, r.code === 200, r.json);
  STD[numero] = r.json.entree.id;
}
{
  const r = await dispo('2026-12-24', '2026-12-26', 'chambre-standard');
  verifie('trois chambres libres : libre', etat(r, 'chambre-standard') === 'libre', r.json);
}

// ── Le decompte, chambre par chambre ───────────────────────────────────────
{
  await poser('fermeture', { id: 'f25', cible: STD['25'],
    debut: '2026-12-24', fin: '2026-12-26', motif: 'groupe Sonatel' });
  let r = await dispo('2026-12-24', '2026-12-26', 'chambre-standard');
  verifie('une prise sur trois : encore libre', etat(r, 'chambre-standard') === 'libre', r.json);

  await poser('fermeture', { id: 'f26', cible: STD['26'],
    debut: '2026-12-24', fin: '2026-12-26' });
  r = await dispo('2026-12-24', '2026-12-26', 'chambre-standard');
  verifie('deux prises sur trois : derniere chambre',
    etat(r, 'chambre-standard') === 'derniere', r.json);

  await poser('fermeture', { id: 'f27', cible: STD['27'],
    debut: '2026-12-24', fin: '2026-12-26' });
  r = await dispo('2026-12-24', '2026-12-26', 'chambre-standard');
  verifie('les trois prises : complet', etat(r, 'chambre-standard') === 'complet', r.json);

  // On en rouvre une : le decompte doit remonter.
  await retirer('fermeture', 'f27');
  r = await dispo('2026-12-24', '2026-12-26', 'chambre-standard');
  verifie('une rouverte : de nouveau derniere chambre',
    etat(r, 'chambre-standard') === 'derniere', r.json);
}

// ── Hors service : indisponible sans dates ─────────────────────────────────
// Les trois chambres sont libres a ces dates : aucune fermeture n'y touche.
// Ce qui les retire du decompte ici, c'est le seul interrupteur hors service.
{
  const horsService = (n, note) => poser('chambre', { id: STD[n], numero: n,
    categorie: 'chambre-standard', service: false, note });
  const enService = (n) => poser('chambre', { id: STD[n], numero: n,
    categorie: 'chambre-standard', service: true });

  const r = await horsService('27', 'climatisation');
  verifie('chambre passee hors service', r.code === 200, r.json);
  let d = await dispo('2027-08-10', '2027-08-12', 'chambre-standard');
  verifie('une sur trois hors service : il en reste deux, donc libre',
    etat(d, 'chambre-standard') === 'libre', d.json);

  await horsService('26');
  d = await dispo('2027-08-10', '2027-08-12', 'chambre-standard');
  verifie('deux sur trois hors service : derniere chambre',
    etat(d, 'chambre-standard') === 'derniere', d.json);

  await horsService('25');
  d = await dispo('2027-08-10', '2027-08-12', 'chambre-standard');
  verifie('les trois hors service : complet, a n importe quelles dates',
    etat(d, 'chambre-standard') === 'complet', d.json);

  const loin = await dispo('2030-01-01', '2030-01-05', 'chambre-standard');
  verifie('hors service n a pas de date de fin : complet en 2030 aussi',
    etat(loin, 'chambre-standard') === 'complet', loin.json);

  for (const n of ['25', '26', '27']) await enService(n);
  const e = await dispo('2027-08-10', '2027-08-12', 'chambre-standard');
  verifie('remises en service : les trois comptent de nouveau',
    etat(e, 'chambre-standard') === 'libre', e.json);
}

// ── La regle des nuits, sur une categorie d'une seule chambre ──────────────
{
  const r = await poser('chambre', { numero: 'S1', categorie: 'suite-arabe' });
  const suite = r.json.entree.id;
  await poser('fermeture', { id: 'fs', cible: suite,
    debut: '2026-12-24', fin: '2026-12-26' });

  const CAS = [
    ['2026-12-24', '2026-12-25', 'complet', 'la nuit du 24, fermee'],
    ['2026-12-26', '2026-12-27', 'complet', 'la nuit du 26, derniere nuit fermee'],
    ['2026-12-23', '2026-12-24', 'derniere', 'la seule nuit du 23 — on part le 24'],
    ['2026-12-27', '2026-12-28', 'derniere', 'la nuit du 27, le lendemain'],
    ['2026-12-20', '2026-12-30', 'complet', 'dix nuits, dont trois fermees'],
    ['2026-12-25', '2026-12-26', 'complet', 'la nuit du 25, au milieu'],
    ['2026-12-22', '2026-12-23', 'derniere', 'bien avant'],
    ['2027-01-05', '2027-01-08', 'derniere', 'bien apres'],
  ];
  for (const [du, au, attendu, quoi] of CAS) {
    const d = await dispo(du, au, 'suite-arabe');
    verifie(`${du} → ${au} : ${attendu} (${quoi})`,
      etat(d, 'suite-arabe') === attendu, d.json);
  }
}

// ── Une fermeture sans date de fin ─────────────────────────────────────────
{
  await poser('chambre', { numero: 'M1', categorie: 'chambre-mezzanine' });
  const r = await poser('fermeture', { id: 'fm', cible: 'chambre-mezzanine',
    debut: '2027-02-01', sansFin: true, motif: 'travaux, durée inconnue' });
  verifie('fermeture sans date de fin acceptee',
    r.code === 200 && r.json.entree.fin === null, r.json);

  const avant = await dispo('2027-01-30', '2027-01-31', 'chambre-mezzanine');
  verifie('sans fin : la veille reste libre',
    etat(avant, 'chambre-mezzanine') === 'derniere', avant.json);
  for (const [du, au] of [['2027-02-01', '2027-02-02'], ['2029-06-01', '2029-06-03']]) {
    const d = await dispo(du, au, 'chambre-mezzanine');
    verifie(`sans fin : ${du} est ferme, meme des annees apres`,
      etat(d, 'chambre-mezzanine') === 'complet', d.json);
  }
}

// ── Une fin oubliee ne ferme QU'UNE nuit ───────────────────────────────────
{
  await poser('chambre', { numero: 'A1', categorie: 'suite-anglaise' });
  const r = await poser('fermeture', { id: 'fa', cible: 'suite-anglaise',
    debut: '2027-04-02' });
  verifie('fin absente sans sansFin : une seule nuit',
    r.json.entree.fin === '2027-04-02', r.json);
  const nuit = await dispo('2027-04-02', '2027-04-03', 'suite-anglaise');
  verifie('fin oubliee : la nuit du 2 est fermee',
    etat(nuit, 'suite-anglaise') === 'complet', nuit.json);
  const suivante = await dispo('2027-04-03', '2027-04-04', 'suite-anglaise');
  verifie('fin oubliee : la nuit du 3 est libre — pas fermee pour toujours',
    etat(suivante, 'suite-anglaise') === 'derniere', suivante.json);
}

// ── Fermer une categorie entiere, puis l'hotel ─────────────────────────────
{
  await poser('fermeture', { id: 'fcat', cible: 'chambre-standard',
    debut: '2027-05-10', fin: '2027-05-12', motif: 'peinture' });
  const r = await dispo('2027-05-11', '2027-05-12', 'chambre-standard');
  verifie('fermeture par categorie : les trois chambres tombent',
    etat(r, 'chambre-standard') === 'complet', r.json);
  const autre = await dispo('2027-05-11', '2027-05-12', 'suite-arabe');
  verifie('fermeture par categorie : les autres ne bougent pas',
    etat(autre, 'suite-arabe') === 'derniere', autre.json);

  await poser('fermeture', { id: 'fhotel', cible: '*',
    debut: '2027-06-05', fin: '2027-06-20', motif: 'fermeture annuelle' });
  for (const s of ['chambre-standard', 'suite-arabe', 'suite-anglaise']) {
    const d = await dispo('2027-06-10', '2027-06-12', s);
    verifie(`fermeture « * » : ${s} est complet`, etat(d, s) === 'complet', d.json);
  }
  const apres = await dispo('2027-06-20', '2027-06-21', 'suite-arabe');
  verifie('fermeture « * » : la nuit du 20 est encore fermee',
    etat(apres, 'suite-arabe') === 'complet', apres.json);
  const fini = await dispo('2027-06-21', '2027-06-22', 'suite-arabe');
  verifie('fermeture « * » : la nuit du 21 est libre',
    etat(fini, 'suite-arabe') === 'derniere', fini.json);
}

// ── Ce que le visiteur ne doit jamais recevoir ─────────────────────────────
{
  const r = await dispo('2026-12-24', '2026-12-26', 'chambre-standard');
  const texte = JSON.stringify(r.json);
  verifie('le motif d une fermeture ne sort pas', !/Sonatel/.test(texte), texte);
  verifie('les numeros de chambre ne sortent pas', !/"25"|numero/.test(texte), texte);
  verifie('le nombre de chambres restantes ne sort pas',
    !/libres|restantes|"chambres"/.test(texte), texte);
}

// ── Des dates qui ne veulent rien dire ne promettent rien ──────────────────
for (const [du, au, quoi] of [
  ['2026-12-24', '2026-12-24', 'zero nuit'],
  ['2026-12-26', '2026-12-24', 'depart avant l arrivee'],
  ['', '2026-12-26', 'arrivee absente'],
  ['pas-une-date', '2026-12-26', 'arrivee illisible'],
]) {
  const r = await dispo(du, au, 'chambre-standard');
  verifie(`${quoi} : aucun etat rendu`,
    r.code === 200 && Object.keys(r.json.etats || {}).length === 0, r.json);
}

// ── Saisies de travers ─────────────────────────────────────────────────────
{
  const r = await poser('chambre', { numero: '25', categorie: 'chambre-standard' });
  verifie('numero deja pris : refuse (409)', r.code === 409, r.json);
  verifie('le refus nomme le numero', /25/.test(r.json.message || ''), r.json);

  const casse = await poser('chambre', { numero: ' 25 ', categorie: 'chambre-standard' });
  verifie('meme numero avec des espaces : refuse aussi', casse.code === 409, casse.json);

  const sansNum = await poser('chambre', { categorie: 'chambre-standard' });
  verifie('chambre sans numero refusee', sansNum.code === 422, sansNum.json);

  const sansCat = await poser('chambre', { numero: '99' });
  verifie('chambre sans categorie refusee', sansCat.code === 422, sansCat.json);

  const etoile = await poser('chambre', { numero: '98', categorie: '*' });
  verifie('une chambre ne peut pas etre de categorie « * »', etoile.code === 422, etoile.json);

  const sansCible = await poser('fermeture', { debut: '2027-05-01' });
  verifie('fermeture sans cible refusee', sansCible.code === 422, sansCible.json);

  const sansDate = await poser('fermeture', { cible: STD['25'] });
  verifie('fermeture sans date refusee', sansDate.code === 422, sansDate.json);

  const envers = await poser('fermeture', { id: 'fenv', cible: STD['25'],
    debut: '2027-03-10', fin: '2027-03-05' });
  verifie('periode a l envers remise a l endroit',
    envers.json.entree.debut === '2027-03-05' && envers.json.entree.fin === '2027-03-10',
    envers.json);
}

// ── Retirer une chambre la retire du decompte ──────────────────────────────
{
  const r = await retirer('chambre', STD['26']);
  verifie('chambre retiree', r.code === 200, r.json);
  const d = await dispo('2027-09-01', '2027-09-03', 'chambre-standard');
  verifie('deux chambres restantes : toujours libre',
    etat(d, 'chambre-standard') === 'libre', d.json);
  await retirer('chambre', STD['25']);
  await retirer('chambre', STD['27']);
  const vide = await dispo('2027-09-01', '2027-09-03', 'chambre-standard');
  verifie('plus aucune chambre saisie : retour a inconnu',
    etat(vide, 'chambre-standard') === 'inconnu', vide.json);
}

// ── La nature d'une fermeture, et la reservation annulee ───────────────────
// Le calendrier de l'administration distingue un sejour client d'un blocage.
// Ces trois champs vivent dans le magasin ; s'ils n'y survivaient pas, toute
// reservation redeviendrait une fermeture anonyme au premier rechargement.
{
  const r = await poser('chambre', { numero: 'N1', categorie: 'deluxe-superieure' });
  const ch = r.json.entree.id;

  const resa = await poser('fermeture', { id: 'r1', cible: ch,
    debut: '2027-07-10', fin: '2027-07-12',
    nature: 'client', client: 'M. Koné', statut: 'confirmee' });
  verifie('une reservation garde sa nature, son client et son statut',
    resa.json.entree.nature === 'client' && resa.json.entree.client === 'M. Koné'
      && resa.json.entree.statut === 'confirmee', resa.json);

  const d = await dispo('2027-07-11', '2027-07-12', 'deluxe-superieure');
  verifie('une reservation confirmee ferme bien la chambre',
    etat(d, 'deluxe-superieure') === 'complet', d.json);

  /* Annuler ne doit pas obliger a supprimer : la trace reste, la nuit se
     rouvre. Supprimer perdrait qui avait reserve, et quand. */
  await poser('fermeture', { id: 'r1', cible: ch, debut: '2027-07-10',
    fin: '2027-07-12', nature: 'client', client: 'M. Koné', statut: 'annulee' });
  const apres = await dispo('2027-07-11', '2027-07-12', 'deluxe-superieure');
  verifie('une reservation annulee ne ferme plus rien',
    etat(apres, 'deluxe-superieure') === 'derniere', apres.json);

  /* Listes fermees : une valeur inventee par un appel exterieur ne doit pas
     se retrouver dans le magasin, ou le calendrier la peindrait n'importe
     comment. */
  const faux = await poser('fermeture', { id: 'r2', cible: ch,
    debut: '2027-08-01', nature: 'inventee', statut: 'bidon' });
  verifie('une nature inventee est ecartee',
    faux.json.entree.nature === '' && faux.json.entree.statut === '', faux.json);
  const bloque = await dispo('2027-08-01', '2027-08-02', 'deluxe-superieure');
  verifie('sans nature, la fermeture ferme quand meme',
    etat(bloque, 'deluxe-superieure') === 'complet', bloque.json);

  // Et rien de tout cela ne sort par la route publique.
  const texte = JSON.stringify(bloque.json);
  verifie('ni le client ni la nature ne sortent de l API publique',
    !/Kon|client|nature|statut/.test(texte), texte);

  await retirer('fermeture', 'r1');
  await retirer('fermeture', 'r2');
  await retirer('chambre', ch);
}

// ── Une demande venue du site retient une chambre ──────────────────────────
// C'est le chainon qui manquait : sans lui, un client demandait une chambre,
// la demande partait sur le telephone de la reception, et le site continuait
// de la compter libre. Deux clients pouvaient demander la derniere.
{
  const demande = (corps, ip) =>
    appel({ a: 'demande' }, { methode: 'POST', body: corps, avecCookie: false,
      ip: ip || '10.0.0.' + Math.floor(Math.random() * 250) });

  // Une categorie neuve, pour ne rien devoir a ce qui precede.
  const NUM = {};
  for (const n of ['10', '2', '3']) {
    const r = await poser('chambre', { numero: n, categorie: 'deluxe-baldaquin' });
    NUM[n] = r.json.entree.id;
  }

  const r = await demande({ categorie: 'deluxe-baldaquin', du: '2027-11-10',
    au: '2027-11-13', nom: 'M. Konan' });
  verifie('une demande retient une chambre',
    r.code === 200 && r.json.ok && r.json.retenue === true, r.json);

  /* La retenue tombe sur la PREMIERE chambre dans l'ordre ou un humain lit :
     2, puis 3, puis 10. Pas l'ordre de saisie. */
  const t = await appel({ a: 'tout' });
  const posee = t.json.donnees.fermetures.find((f) => f.client === 'M. Konan');
  verifie('elle tombe sur la premiere chambre, lue comme un humain lit',
    posee && posee.cible === NUM['2'], posee);
  verifie('elle porte les bonnes nuits — depart le 13, donc derniere nuit le 12',
    posee && posee.debut === '2027-11-10' && posee.fin === '2027-11-12', posee);
  verifie('elle est en attente, et elle a une peremption',
    posee && posee.statut === 'attente' && !!posee.expire, posee);

  // Ce que le visiteur recoit ne dit rien de l'inventaire.
  const texte = JSON.stringify(r.json);
  verifie('la reponse ne dit ni le numero, ni combien il en reste',
    !/numero|cible|"2"|chambres|libres/.test(texte), texte);

  // Et la chambre est bien retenue : il n'en reste que deux sur trois.
  const d = await dispo('2027-11-11', '2027-11-12', 'deluxe-baldaquin');
  verifie('la chambre retenue ne compte plus comme libre',
    etat(d, 'deluxe-baldaquin') === 'libre', d.json);

  // Deux demandes de plus : la categorie doit finir complete.
  await demande({ categorie: 'deluxe-baldaquin', du: '2027-11-10', au: '2027-11-13',
    nom: 'Mme Ba' });
  const d2 = await dispo('2027-11-11', '2027-11-12', 'deluxe-baldaquin');
  verifie('deux demandes : il ne reste qu une chambre',
    etat(d2, 'deluxe-baldaquin') === 'derniere', d2.json);

  await demande({ categorie: 'deluxe-baldaquin', du: '2027-11-10', au: '2027-11-13',
    nom: 'M. Cisse' });
  const d3 = await dispo('2027-11-11', '2027-11-12', 'deluxe-baldaquin');
  verifie('trois demandes : complet', etat(d3, 'deluxe-baldaquin') === 'complet', d3.json);

  // La quatrieme ne retient rien, et le dit — sans faire echouer le formulaire.
  const q = await demande({ categorie: 'deluxe-baldaquin', du: '2027-11-10',
    au: '2027-11-13', nom: 'M. Tard' });
  verifie('plus rien de libre : aucune retenue, mais la demande n echoue pas',
    q.code === 200 && q.json.ok === true && q.json.retenue === false
      && q.json.raison === 'complet', q.json);
  const apres = await appel({ a: 'tout' });
  verifie('et rien n a ete ecrit pour elle',
    !apres.json.donnees.fermetures.some((f) => f.client === 'M. Tard'), 'ecrit');
}

// ── Une retenue perimee cesse de peser, mais reste visible ─────────────────
{
  const r = await poser('chambre', { numero: 'P1', categorie: 'mezzanine-superieure' });
  const id = r.json.entree.id;
  /* Une peremption dans le passe : c'est la demande de quelqu'un qui a
     rempli le tunnel il y a trois heures et n'a jamais envoye son message. */
  await poser('fermeture', { id: 'perimee', cible: id, debut: '2027-12-01',
    fin: '2027-12-05', nature: 'client', statut: 'attente', client: 'M. Oublie',
    expire: '2020-01-01T00:00' });

  const d = await dispo('2027-12-02', '2027-12-03', 'mezzanine-superieure');
  verifie('une retenue perimee ne ferme plus la chambre',
    etat(d, 'mezzanine-superieure') === 'derniere', d.json);

  const t = await appel({ a: 'tout' });
  verifie('mais elle reste dans le magasin, avec le nom et les dates',
    t.json.donnees.fermetures.some((f) => f.id === 'perimee' && f.client === 'M. Oublie'),
    'perdue');

  /* La meme, pas encore perimee, ferme bien. */
  await poser('fermeture', { id: 'perimee', cible: id, debut: '2027-12-01',
    fin: '2027-12-05', nature: 'client', statut: 'attente', client: 'M. Oublie',
    expire: '2099-01-01T00:00' });
  const e = await dispo('2027-12-02', '2027-12-03', 'mezzanine-superieure');
  verifie('la meme retenue, encore valable, ferme la chambre',
    etat(e, 'mezzanine-superieure') === 'complet', e.json);

  /* Confirmee par la reception, elle n'expire plus. */
  await poser('fermeture', { id: 'perimee', cible: id, debut: '2027-12-01',
    fin: '2027-12-05', nature: 'client', statut: 'confirmee', client: 'M. Oublie' });
  const c = await appel({ a: 'tout' });
  const f = c.json.donnees.fermetures.find((x) => x.id === 'perimee');
  verifie('confirmee, elle perd sa peremption', f && !f.expire, f);
  const g = await dispo('2027-12-02', '2027-12-03', 'mezzanine-superieure');
  verifie('et elle ferme toujours', etat(g, 'mezzanine-superieure') === 'complet', g.json);
}

// ── Ce que la route publique refuse ────────────────────────────────────────
{
  const demande = (corps, ip) =>
    appel({ a: 'demande' }, { methode: 'POST', body: corps, avecCookie: false,
      ip: ip || '10.1.0.' + Math.floor(Math.random() * 250) });

  const g = await appel({ a: 'demande' }, { methode: 'GET', avecCookie: false, ip: '10.2.0.1' });
  verifie('en lecture : refuse (405)', g.code === 405, g.json);

  for (const [corps, quoi] of [
    [{ categorie: 'chambre-standard', du: '2027-05-01', au: '2027-05-03' }, 'sans nom'],
    [{ categorie: '', du: '2027-05-01', au: '2027-05-03', nom: 'X' }, 'sans categorie'],
    [{ categorie: 'chambre-standard', du: '2027-05-03', au: '2027-05-01', nom: 'X' }, 'dates a l envers'],
    [{ categorie: 'chambre-standard', du: '2027-05-01', au: '2027-05-01', nom: 'X' }, 'zero nuit'],
  ]) {
    const r = await demande(corps);
    verifie(`${quoi} : rien retenu, et le formulaire n echoue pas`,
      r.code === 200 && r.json.ok === true && r.json.retenue === false, r.json);
  }

  /* Le debit. Une route publique qui ECRIT doit etre bornee : sans cela,
     quelques milliers d'appels condamnent tout l'hotel. La peremption fait
     le reste — meme un flot se vide en deux heures. */
  let refus = 0;
  for (let i = 0; i < 20; i++) {
    const r = await demande({ categorie: 'suite-anglaise', du: '2027-06-01',
      au: '2027-06-02', nom: 'Rafale ' + i }, '10.9.9.9');
    if (r.code === 429) refus++;
  }
  verifie('une rafale depuis une seule adresse finit par etre refusee', refus > 0, refus);
}

// ── La route publique reste publique, les ecritures non ────────────────────
{
  const r = await appel({ a: 'dispo', du: '2027-09-01', au: '2027-09-03' },
    { avecCookie: false });
  verifie('la lecture ne demande pas de session', r.code === 200, r.json);
  verifie('sans categorie precisee : celles qui ont des chambres',
    Object.keys(r.json.etats).length >= 2, r.json);

  const c = await appel({ a: 'enregistrer' }, { methode: 'POST', avecCookie: false,
    body: { type: 'chambre', entree: { numero: '404', categorie: 'suite-arabe' } } });
  verifie('enregistrer une chambre demande une session', c.code === 401, c.json);

  const f = await appel({ a: 'enregistrer' }, { methode: 'POST', avecCookie: false,
    body: { type: 'fermeture', entree: { cible: 'suite-arabe', debut: '2027-08-01' } } });
  verifie('enregistrer une fermeture demande une session', f.code === 401, f.json);
}

console.log(`\n${ok} verification(s) passee(s), ${ko} en echec.`);
if (ko) process.exit(1);
