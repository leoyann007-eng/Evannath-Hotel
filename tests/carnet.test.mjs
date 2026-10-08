// Tests du Carnet d'Assinie, hors Vercel : on simule req et res.
// Lance depuis la racine du depot :  node tests/carnet.test.mjs
//
// CE QUI SE JOUE ICI. Un article est ecrit par un compte Communication, puis
// servi a tout le monde — et aux moteurs de recherche. Quatre choses ne
// doivent jamais arriver :
//
//   1. UN BROUILLON EN LIGNE. Non publie, ou date de demain, veut dire
//      invisible : ni dans la liste, ni par son adresse, ni dans le plan.
//   2. DU CODE DANS LA PAGE. Le texte est mis en forme par le serveur, et
//      tout ce qui ressemble a du HTML y est echappe.
//   3. UN LIEN QUI CASSE. L'adresse d'un article se fixe a sa creation :
//      retoucher le titre ne la change pas.
//   4. UN ARTICLE AMPUTE. Trop long, il est refuse — pas coupe en silence.

process.env.ADMIN_MDP = 'essai';
delete process.env.BLOB_READ_WRITE_TOKEN;

const handler = (await import('../site/api/admin.js')).default;

let cookie = '';
function appel(query, { methode = 'GET', body = null, avecCookie = true, ip } = {}) {
  const req = {
    method: methode, query, body,
    headers: Object.assign({}, avecCookie && cookie ? { cookie } : {}, ip ? { 'x-forwarded-for': ip } : {}),
  };
  const out = { entetes: {} };
  const res = {
    statusCode: 0,
    setHeader(k, v) { out.entetes[k] = v; },
    getHeader(k) { return out.entetes[k]; },
    status(c) { out.code = c; return res; },
    json(j) { out.json = j; return res; },
    send(t) { out.texte = String(t); return res; },
  };
  return Promise.resolve(handler(req, res)).then(() => out);
}

let ok = 0, ko = 0;
function verifie(nom, condition, detail) {
  if (condition) { ok++; console.log('  ok     ', nom); }
  else { ko++; console.log('  ECHEC  ', nom, detail === undefined ? '' : JSON.stringify(detail).slice(0, 400)); }
}

const poser = (entree) => appel({ a: 'enregistrer' }, { methode: 'POST', body: { type: 'article', entree } });
const liste = () => appel({ a: 'carnet' }, { avecCookie: false, ip: '10.0.0.7' });
const article = (s) => appel({ a: 'article', s }, { avecCookie: false, ip: '10.0.0.7' });
const pageDe = (s) => appel({ a: 'page-article', s }, { avecCookie: false, ip: '10.0.0.7' });
const plan = () => appel({ a: 'plan-carnet' }, { avecCookie: false, ip: '10.0.0.7' });
const jour = (n) => { const d = new Date(); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };

// ── Connexion ──────────────────────────────────────────────────────────────
{
  const r = await appel({ a: 'entrer' }, { methode: 'POST', body: { mdp: 'essai' } });
  cookie = String(r.entetes['Set-Cookie'] || '').split(';')[0];
  verifie('connexion acceptee', r.code === 200 && cookie.startsWith('evn_adm='), r.json);
}

// ── Au depart : une liste vide, pas une erreur ─────────────────────────────
{
  const r = await liste();
  verifie('la liste publique existe et est vide', r.code === 200 && Array.isArray(r.json.articles)
    && r.json.articles.length === 0, r.json);
}

// ── Ce qu'il faut pour enregistrer ─────────────────────────────────────────
{
  const r = await poser({ titre: 'Sans texte' });
  verifie('sans chapô ni texte : refuse, et le refus nomme les champs', r.code === 422
    && r.json.champs.includes('chapô') && r.json.champs.includes('texte'), r.json);
}
{
  const r = await poser({ titre: 'Trop long', chapo: 'x', texte: 'y'.repeat(30001) });
  verifie('un texte trop long est refuse, pas tronque', r.code === 422 && /30\s?000/.test(r.json.message), r.json);
}
{
  const r = await poser({ titre: 'Image tierce', chapo: 'x', texte: 'y', image: 'https://exemple.com/pixel.gif' });
  verifie('une image hors du site est refusee', r.code === 422 && r.json.champs.includes('image'), r.json);
}

// ── Un brouillon, puis sa publication ─────────────────────────────────────
let id = '';
{
  const r = await poser({ titre: 'Que faire à Assinie ? Le guide du week-end',
    chapo: 'Plages, lagune et tables : deux jours bien remplis.',
    texte: '## Samedi\nLa lagune au matin.\n\n- Pirogue\n- Plage\n\nVoir [nos expériences](experiences.html) et **réserver**.',
    image: 'gal-lag-ponton', alt: 'La paillote', publie: false });
  id = r.json.entree && r.json.entree.id;
  verifie('le brouillon est enregistre', r.code === 200 && !!id, r.json);
  verifie('son adresse vient du titre, sans accents ni ponctuation',
    r.json.entree.slug === 'que-faire-a-assinie-le-guide-du-week-end', r.json.entree.slug);
  const l = await liste();
  verifie('un brouillon ne sort pas dans la liste', l.json.articles.length === 0, l.json);
  const a = await article('que-faire-a-assinie-le-guide-du-week-end');
  verifie('un brouillon ne sort pas par son adresse (404)', a.code === 404, a.json);
}
{
  const r = await poser({ id, titre: 'Que faire à Assinie ? (titre retouché)',
    chapo: 'Plages, lagune et tables : deux jours bien remplis.',
    texte: '## Samedi\nLa lagune au matin.\n\n- Pirogue\n- Plage\n\nVoir [nos expériences](experiences.html) et **réserver**.',
    image: 'gal-lag-ponton', alt: 'La paillote', publie: true, date: jour(0) });
  verifie('retoucher le titre ne change pas l adresse',
    r.json.entree && r.json.entree.slug === 'que-faire-a-assinie-le-guide-du-week-end', r.json.entree);
  const l = await liste();
  verifie('publie : il sort dans la liste, sans son texte', l.json.articles.length === 1
    && !('texte' in l.json.articles[0]) && !('html' in l.json.articles[0]), l.json);
  const a = await article('que-faire-a-assinie-le-guide-du-week-end');
  verifie('le texte est mis en forme : intertitre, liste, lien, gras', a.code === 200
    && a.json.article.html.includes('<h2>Samedi</h2>') && a.json.article.html.includes('<li>Pirogue</li>')
    && a.json.article.html.includes('<a href="experiences.html">nos expériences</a>')
    && a.json.article.html.includes('<strong>réserver</strong>'), a.json.article && a.json.article.html);
}

// ── Un meme titre : deux adresses ─────────────────────────────────────────
{
  const r = await poser({ titre: 'Que faire à Assinie ? Le guide du week-end', chapo: 'b', texte: 'c', publie: false });
  verifie('un second article au meme titre recoit une autre adresse',
    r.json.entree && r.json.entree.slug === 'que-faire-a-assinie-le-guide-du-week-end-2', r.json.entree);
}

// ── Programme pour demain : invisible aujourd'hui ─────────────────────────
{
  await poser({ titre: 'Le réveillon sur la lagune', chapo: 'Bientôt.', texte: 'Texte.', publie: true, date: jour(1) });
  const l = await liste();
  verifie('un article date de demain ne sort pas encore',
    !l.json.articles.some((x) => x.slug === 'le-reveillon-sur-la-lagune'), l.json.articles.map((x) => x.slug));
  const p = await plan();
  verifie('ni dans le plan du site', p.code === 200 && !p.texte.includes('le-reveillon-sur-la-lagune')
    && p.texte.includes('/carnet-que-faire-a-assinie-le-guide-du-week-end'), p.texte);
}

// ── Rien d'executable ne passe ────────────────────────────────────────────
{
  const r = await poser({ titre: 'Piège <script>alert(1)</script> $& fin', chapo: 'Chapô "guillemets" <b>gras</b>',
    texte: '<img src=x onerror=alert(1)>\n\n[clic](javascript:alert(1)) et [ok](https://example.com)',
    publie: true, date: jour(0) });
  const slug = r.json.entree && r.json.entree.slug;
  verifie('l adresse ne garde que lettres, chiffres et tirets', /^[a-z0-9-]+$/.test(slug || ''), slug);
  const a = await article(slug);
  const h = a.json.article.html;
  verifie('le HTML saisi est echappe, jamais interprete', !h.includes('<img') && h.includes('&lt;img'), h);
  verifie('un lien javascript: devient du texte', !h.includes('href="javascript') && h.includes('clic'), h);
  verifie('un lien externe s ouvre a part, en noopener', h.includes('href="https://example.com" target="_blank" rel="noopener"'), h);
  const p = await pageDe(slug);
  verifie('la page rendue : 200, en HTML', p.code === 200 && /text\/html/.test(p.entetes['Content-Type']), p.code);
  const t = p.texte || '';
  verifie('aucun script injecte par le titre', !t.includes('<script>alert(1)'), '');
  verifie('« $& » dans le titre est ecrit tel quel', t.includes('$&amp; fin'), (t.match(/<title>[^<]*/) || [''])[0]);
  verifie('les donnees ne peuvent pas fermer leur balise <script>', !/<script type="application\/json" id="art-data">[^]*?<\/script>[^]*?alert\(1\)<\/script>/.test(t)
    && !t.split('id="art-data">')[1].split('</script>')[0].includes('<'), '');
}

// ── La page d'un article, cote serveur ────────────────────────────────────
{
  const p = await pageDe('que-faire-a-assinie-le-guide-du-week-end');
  const t = p.texte || '';
  verifie('le titre de la page est celui de l article', /<title>Que faire à Assinie \? \(titre retouché\) — Le Carnet/.test(t),
    (t.match(/<title>[^<]*/) || [''])[0]);
  verifie('la description est le chapô', t.includes('<meta name="description" content="Plages, lagune et tables'), '');
  verifie('l adresse canonique est celle de l article',
    /<link rel="canonical" href="[^"]+\/carnet-que-faire-a-assinie-le-guide-du-week-end">/.test(t), '');
  verifie('le texte est deja dans le HTML (pas ecrit par un script)', t.includes('<h2>Samedi</h2>')
    && t.includes('<h1 id="art-titre">Que faire à Assinie ? (titre retouché)</h1>'), '');
  verifie('un seul h1', (t.match(/<h1[\s>]/g) || []).length === 1, (t.match(/<h1[\s>]/g) || []).length);
  verifie('le JSON-LD BlogPosting est pose', t.includes('"@type":"BlogPosting"'), '');
  const n = await pageDe('n-existe-pas');
  verifie('une adresse inconnue : 404, page « introuvable »', n.code === 404 && n.texte.includes('Article introuvable'), n.code);
}

// ── Supprimer ─────────────────────────────────────────────────────────────
{
  const r = await appel({ a: 'supprimer' }, { methode: 'POST', body: { type: 'article', id } });
  const a = await article('que-faire-a-assinie-le-guide-du-week-end');
  verifie('supprime : il disparait', r.code === 200 && a.code === 404, a.code);
}

// ── Sans session : rien ne s'ecrit ────────────────────────────────────────
{
  const r = await appel({ a: 'enregistrer' }, { methode: 'POST', avecCookie: false,
    body: { type: 'article', entree: { titre: 'x', chapo: 'y', texte: 'z', publie: true } } });
  verifie('sans session : refuse (401)', r.code === 401, r.code);
}

console.log(`\n${ok} verifications passees, ${ko} en echec`);
process.exit(ko ? 1 : 0);
