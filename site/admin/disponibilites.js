/* ─────────────────────────────────────────────────────────────────────────
   Calendrier des disponibilités.

   Le calendrier n est jamais la source de vérité : il se calcule, en une
   passe, à partir de ETAT.chambres et ETAT.fermetures déjà chargés par
   charger(). Aucune requête par case. Les écritures passent par les routes
   existantes — enregistrer / supprimer une fermeture — et rien d autre.

   Mêmes règles que api/admin.js : les dates d une fermeture sont des NUITS,
   bornes incluses ; fin à null = sans date de fin. Un séjour arrivé le 24 et
   parti le 27 occupe les nuits du 24, du 25 et du 26 : fin = 26.

   `nature` distingue un séjour client ('client') d un blocage
   ('hors-service', 'vente'). Une fermeture plus ancienne, sans nature, reste
   une fermeture client : c est ce qu elle était.

   Ce fichier se charge après le script de la page, dont il emploie ETAT,
   appel, ech, $, AUJ, jourIso et FCFA.
   ───────────────────────────────────────────────────────────────────────── */
const DSP = { vue: 'mois', focus: null, ouvertes: {}, tiroir: null, modal: null,
              voirTout: false, seuil: 0.3, defiler: true };
const DSP_IMG = { 'chambre-standard': 'r-standard-640', 'deluxe-baldaquin': 'gal-ch-wax-t360',
  'deluxe-superieure': 'g-chambre-t', 'suite-anglaise': 'gal-ch-salon-t360',
  'chambre-mezzanine': 'r-mezzanine-640', 'mezzanine-superieure': 'r-mezz2-640',
  'suite-arabe': 'sa-chambre2-640' };
const DTON = { dispo: ['#8FAE63', 'Disponible'], faible: ['#E0A955', 'Peu de chambres'],
  complet: ['#E08A7B', 'Complet'], hs: ['#9C8B78', 'Hors service'],
  inconnu: ['#9C8B78', 'Aucune chambre saisie'], libre: ['#8FAE63', 'Disponible'],
  occ: ['#86A9C9', 'Occupée'], res: ['#E0A955', 'Réservée'], vente: ['#E08A7B', 'Bloquée'] };

const jDt = (j) => new Date(j + 'T12:00:00');
const jPlus = (j, n) => { const d = jDt(j); d.setDate(d.getDate() + n); return jourIso(d); };
const jMaj = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const jCourt = (j) => jDt(j).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
const jLong = (j) => jMaj(jDt(j).toLocaleDateString('fr-FR',
  { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }));
const fCouvre = (f, n) => f.debut && f.debut <= n && (f.fin == null || f.fin >= n);
const fChevauche = (f, a, b) => f.debut && f.debut <= b && (f.fin == null || f.fin >= a);
const fVise = (f, ch) => f.cible === '*' || f.cible === ch.id || f.cible === ch.categorie;
const fClient = (f) => f.nature === 'client' || !f.nature;
const parNum = (a, b) => String(a.numero).localeCompare(String(b.numero), 'fr',
  { numeric: true, sensitivity: 'base' });

function dspIndex(F, chambres) {
  const ids = new Set(chambres.map((c) => c.id)), par = {}, larges = [];
  F.forEach((f) => {
    if (!f || !f.debut) return;
    if (ids.has(f.cible)) (par[f.cible] = par[f.cible] || []).push(f); else larges.push(f);
  });
  return { par, larges };
}

/** L état d une chambre, une nuit. Un séjour l emporte sur un blocage : si
    les deux se chevauchent, c est le client qu il faut voir. */
function dspEtat(ch, n, idx, auj) {
  if (ch.service === false) return { k: 'hs', motif: ch.note || 'Hors service' };
  const l = (idx.par[ch.id] || []).concat(idx.larges.filter((f) => fVise(f, ch)));
  let bloc = null;
  for (const f of l) {
    if (!fCouvre(f, n)) continue;
    if (fClient(f)) {
      if (f.statut === 'annulee') continue;
      return { k: f.debut <= auj ? 'occ' : 'res', f };
    }
    bloc = bloc || f;
  }
  return bloc ? { k: bloc.nature === 'vente' ? 'vente' : 'hs', f: bloc } : { k: 'libre' };
}

/** Disponibles = chambres saisies − réservées − bloquées, par catégorie et
    par nuit. Rend aussi l état de chaque chambre, pour les lignes détaillées. */
function calculerDisponibilites(categories, chambres, F, jours, auj, seuil) {
  const idx = dspIndex(F, chambres), parCat = {}, parChambre = {};
  categories.forEach((c) => {
    parCat[c.slug] = {};
    const siennes = chambres.filter((ch) => ch.categorie === c.slug);
    siennes.forEach((ch) => { parChambre[ch.id] = {}; });
    jours.forEach((j) => {
      const x = { total: siennes.length, libres: 0, reserves: 0, hs: 0, vente: 0 };
      siennes.forEach((ch) => {
        const e = dspEtat(ch, j, idx, auj);
        parChambre[ch.id][j] = e;
        if (e.k === 'libre') x.libres++;
        else if (e.k === 'occ' || e.k === 'res') x.reserves++;
        else if (e.k === 'hs') x.hs++; else x.vente++;
      });
      x.bloques = x.hs + x.vente;
      x.etat = !x.total ? 'inconnu'
        : !x.libres ? ((!x.reserves && x.hs && !x.vente) ? 'hs' : 'complet')
        : (x.libres / x.total <= seuil ? 'faible' : 'dispo');
      parCat[c.slug][j] = x;
    });
  });
  return { parCat, parChambre };
}

function joursDsp() {
  const f = DSP.focus;
  if (DSP.vue === 'jour') return [f];
  if (DSP.vue === 'semaine') {
    const a = jPlus(f, -((jDt(f).getDay() + 6) % 7));
    return [0, 1, 2, 3, 4, 5, 6].map((i) => jPlus(a, i));
  }
  const o = []; let j = f.slice(0, 8) + '01';
  while (j.slice(0, 7) === f.slice(0, 7)) { o.push(j); j = jPlus(j, 1); }
  return o;
}

const vignette = (slug) => DSP_IMG[slug]
  ? `<img class="vig" src="/img/opt/${DSP_IMG[slug]}.jpg" alt="">` : '<div class="vig"></div>';

function detailSejour(e) {
  if (e.f && fClient(e.f)) {
    return (e.f.client || e.f.motif || 'Fermeture') + ' · départ ' + jCourt(jPlus(e.f.fin, 1))
      + (e.f.statut === 'attente' ? ' · en attente' : '');
  }
  return (e.f ? e.f.motif : e.motif) || '';
}

/* ── Rendu du calendrier et de ses panneaux ─────────────────────────── */
function htmlDsp() {
  const cats = ETAT.categories || [], chambres = ETAT.chambres || [];
  const F = ETAT.fermetures || [], auj = AUJ();
  if (!DSP.focus) DSP.focus = auj;
  if (!cats.length) {
    return `<div class="carte" style="text-align:center;padding:48px">
      <p class="bloc-t" style="margin-bottom:6px">Aucune catégorie de chambre</p>
      <p class="aide">Commencez par créer une catégorie pour gérer ses disponibilités.
      Les catégories viennent du site : elles se déclarent dans <code>_chambres.py</code>.</p></div>`;
  }
  const jours = joursDsp();
  const calc = calculerDisponibilites(cats, chambres, F, jours.concat([auj]), auj, DSP.seuil);
  const col = (j) => 'dsp-j' + (j === auj ? ' auj' : '');

  const tete = jours.map((j) => {
    const d = jDt(j);
    return `<div class="${col(j)} dsp-t" data-jour="${j}">
      <span>${jMaj(d.toLocaleDateString('fr-FR', { weekday: 'short' }).replace('.', ''))}</span>
      <b>${d.getDate()}</b></div>`;
  }).join('');

  const premiere = cats.findIndex((c) => chambres.some((ch) => ch.categorie === c.slug));
  const lignes = cats.map((c, ci) => {
    const siennes = chambres.filter((ch) => ch.categorie === c.slug).sort(parNum);
    const t = calc.parCat[c.slug][auj];
    const ouverte = (DSP.ouvertes[c.slug] ?? ci === premiere) && siennes.length > 0;
    const cases = jours.map((j) => {
      const x = calc.parCat[c.slug][j], [teinte, mot] = DTON[x.etat];
      const aria = ech(c.nom) + ', ' + jLong(j) + ' : ' + (x.total
        ? x.libres + ' sur ' + x.total + ' disponibles — ' + mot : 'aucune chambre saisie');
      return `<div class="${col(j)}"><button class="dsp-case" style="--c:${teinte}"
        data-dsp-cat="${ech(c.slug)}" data-nuit="${j}" aria-label="${aria}" title="${aria}"
        ${x.total ? '' : 'disabled'}>${x.total ? x.libres + '/' + x.total + '<i></i>' : '—'}</button></div>`;
    }).join('');
    const rangs = !ouverte ? '' : siennes.map((ch) => `<div class="dsp-l dsp-r">
      <div class="dsp-g"><span>Chambre ${ech(ch.numero)}</span>${ch.service === false
        ? '<span class="aide" style="margin:0">hors service</span>' : ''}</div>
      ${jours.map((j) => {
        const e = calc.parChambre[ch.id][j], [teinte, mot] = DTON[e.k], det = detailSejour(e);
        const aria = 'Chambre ' + ech(ch.numero) + ', ' + jLong(j) + ' : ' + mot
          + (det ? ' — ' + ech(det) : '');
        return `<div class="${col(j)}"><button class="dsp-b" style="--c:${teinte}"
          data-dsp-ch="${ech(ch.id)}" data-nuit="${j}" aria-label="${aria}" title="${aria}">${mot}${
          DSP.vue === 'jour' && det ? '<small>' + ech(det) + '</small>' : ''}</button></div>`;
      }).join('')}</div>`).join('');
    return `<div class="dsp-bloc"><div class="dsp-l">
      <div class="dsp-g dsp-cat">${vignette(c.slug)}<div style="flex:1;min-width:0">
        <b class="nom">${ech(c.nom)}</b>
        <span class="prix">À partir de ${FCFA(c.prix)} / nuit</span>
        ${siennes.length ? `<div class="dsp-stats">
            <div><b>${t.total}</b><span>Total</span></div>
            <div><b>${t.reserves}</b><span>Occupées</span></div>
            <div><b style="color:var(--palm)">${t.libres}</b><span>Disponibles</span></div>
          </div>
          <button class="dsp-lien" data-dsp-ouvrir="${ech(c.slug)}" aria-expanded="${ouverte}">${
            ouverte ? 'Masquer ▴' : 'Détails ▾'}</button>`
        : `<p class="aide" style="margin-top:6px">Aucune chambre saisie : le site
            n'annonce rien pour cette catégorie.</p>`}
      </div></div>${cases}</div>${rangs}</div>`;
  }).join('');

  const mois = [];
  for (let i = -3; i <= 9; i++) {
    const d = jDt(auj.slice(0, 8) + '01'); d.setMonth(d.getMonth() + i);
    mois.push(jourIso(d).slice(0, 7));
  }
  if (!mois.includes(DSP.focus.slice(0, 7))) mois.push(DSP.focus.slice(0, 7));
  const optMois = mois.sort().map((m) => `<option value="${m}" ${m === DSP.focus.slice(0, 7)
    ? 'selected' : ''}>${jMaj(jDt(m + '-01').toLocaleDateString('fr-FR',
      { month: 'long', year: 'numeric' }))}</option>`).join('');
  const vues = [['mois', 'Vue mois'], ['semaine', 'Vue semaine'], ['jour', 'Vue jour']]
    .map(([v, l]) => `<button class="opt ${DSP.vue === v ? 'on' : ''}" data-dsp-vue="${v}"
      aria-pressed="${DSP.vue === v}">${l}</button>`).join('');
  const periode = DSP.vue === 'semaine' ? 'Semaine du ' + jCourt(jours[0]) + ' au ' + jCourt(jours[6])
    : DSP.vue === 'jour' ? jLong(DSP.focus) : '';

  const apercu = cats.map((c) => {
    const x = calc.parCat[c.slug][auj];
    const pct = x.total ? Math.round(x.libres / x.total * 100) : 0;
    return `<div><b>${ech(c.nom)}</b><span>${x.total ? x.libres + ' / ' + x.total
      + ' disponibles' : 'Aucune chambre saisie'}</span>
      <div class="dsp-jauge" style="--c:${DTON[x.etat][0]}"><div role="progressbar"
        aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"
        aria-label="${ech(c.nom)} : ${pct} % disponibles"><i style="width:${pct}%"></i></div>${pct} %</div></div>`;
  }).join('');

  const aujCats = cats.map((c) => calc.parCat[c.slug][auj]).filter((x) => x.total);
  const nb = (f) => aujCats.filter(f).length;
  const hs = chambres.filter((c) => c.service === false).length;

  /* Les prochaines arrivées. Plusieurs chambres au même nom, aux mêmes dates
     et dans la même catégorie font une seule réservation. */
  const groupes = {};
  F.filter((f) => f.nature === 'client' && f.statut !== 'annulee' && f.debut >= auj).forEach((f) => {
    const ch = chambres.find((c) => c.id === f.cible);
    if (!ch) return;
    const k = [f.client, f.debut, f.fin, ch.categorie].join('|');
    (groupes[k] = groupes[k] || { f, cat: ch.categorie, n: 0 }).n++;
  });
  const toutes = Object.values(groupes).sort((a, b) => a.f.debut.localeCompare(b.f.debut));
  const resas = toutes.slice(0, DSP.voirTout ? 40 : 4).map((g) => {
    const att = g.f.statut === 'attente';
    const cat = cats.find((c) => c.slug === g.cat);
    return `<div class="dsp-resa"><div><b>${ech(g.f.client || '—')}</b>
      <span>${ech(cat ? cat.nom : g.cat)} — ${g.n} chambre${g.n > 1 ? 's' : ''}</span>
      <span class="quand">Arrivée ${jCourt(g.f.debut)} → Départ ${jCourt(jPlus(g.f.fin, 1))}</span></div>
      <span class="etat ${att ? 'attend' : 'vif'}">${att ? 'En attente' : 'Confirmée'}</span></div>`;
  }).join('');

  return `<div class="dsp"><div style="min-width:0">
    <section class="dsp-cal v-${DSP.vue}" aria-label="Calendrier des disponibilités">
      <div class="dsp-barre">
        <div class="dsp-nav">
          <button class="fl2" data-dsp-pas="-1" aria-label="Période précédente">‹</button>
          <button class="fl2" data-dsp-pas="1" aria-label="Période suivante">›</button>
          <select id="dsp-mois" class="dsp-mois" aria-label="Mois affiché">${optMois}</select>
          <span class="aide" style="margin:0 0 0 6px">${periode}</span>
        </div>
        <div class="dsp-vues" role="group" aria-label="Vue du calendrier">${vues}</div>
      </div>
      <div class="dsp-defil" id="dsp-defil">
        <div class="dsp-l dsp-tete"><div class="dsp-g"><span class="lb" style="margin:0">
          Catégorie / Chambre</span></div>${tete}</div>
        ${lignes}
      </div>
    </section>
    <div class="dsp-bas">
      <section class="carte">
        <h2 class="bloc-t" style="margin-bottom:2px">Vue d'ensemble rapide</h2>
        <p class="aide" style="margin:0 0 16px">État de l'occupation pour aujourd'hui</p>
        <div class="dsp-apercu">${apercu}</div>
      </section>
      <section class="carte">
        <h2 class="bloc-t">Statut des chambres</h2>
        <ul class="dsp-legende">
          <li><span class="pt" style="--c:#8FAE63"></span>Disponible</li>
          <li><span class="pt" style="--c:#E0A955"></span>Peu de chambres
            <span class="aide" style="margin:0">— ${Math.round(DSP.seuil * 100)} % ou moins</span></li>
          <li><span class="pt" style="--c:#E08A7B"></span>Complet</li>
          <li><span class="pt" style="--c:#9C8B78"></span>Hors service</li>
        </ul>
        <div class="dsp-total"><span>Total des chambres</span><b>${chambres.length}</b></div>
        <p class="aide" style="margin-top:2px">${hs ? 'dont ' + hs + ' hors service jusqu’à nouvel ordre'
          : 'toutes en service'}</p>
      </section>
    </div>
  </div>
  <div class="dsp-cote">
    <section class="carte">
      <h2 class="bloc-t">Aujourd'hui — ${jDt(auj).toLocaleDateString('fr-FR',
        { day: 'numeric', month: 'short', year: 'numeric' })}</h2>
      <div class="dsp-auj">
        <div><b><span class="pt" style="--c:#8FAE63;margin-right:8px;vertical-align:4px"></span>${
          nb((x) => x.etat === 'dispo')}</b><span>Disponibles</span></div>
        <div><b><span class="pt" style="--c:#E0A955;margin-right:8px;vertical-align:4px"></span>${
          nb((x) => x.etat === 'faible')}</b><span>Peu de chambres</span></div>
        <div><b><span class="pt" style="--c:#E08A7B;margin-right:8px;vertical-align:4px"></span>${
          nb((x) => x.etat === 'complet' || x.etat === 'hs')}</b><span>Complet</span></div>
      </div>
      <p class="aide" style="margin-top:14px">Catégories, selon les chambres libres cette nuit.</p>
    </section>
    <section class="carte">
      <div style="display:flex;justify-content:space-between;align-items:baseline">
        <h2 class="bloc-t" style="margin-bottom:8px">Prochaines réservations</h2>
        ${toutes.length > 4 ? `<button class="dsp-lien" style="padding:0" data-dsp-voirtout>${
          DSP.voirTout ? 'Réduire' : 'Voir tout (' + toutes.length + ')'}</button>` : ''}
      </div>
      ${resas || '<p class="aide" style="padding:10px 0 4px">Aucune réservation à venir</p>'}
    </section>
  </div></div>`;
}

function rendreDsp() {
  const z = $('#dsp-zone');
  if (!z) return;
  z.innerHTML = htmlDsp();
  apresDsp();
}

/** Le mois s ouvre sur aujourd hui, pas sur le 1er. */
function apresDsp() {
  const el = $('#dsp-defil');
  if (!el || !DSP.defiler) return;
  DSP.defiler = false;
  const c = el.querySelector('[data-jour="' + AUJ() + '"]');
  el.scrollLeft = c && DSP.vue === 'mois' ? Math.max(0, c.offsetLeft - 330 - 192) : 0;
}

function allerDsp(focus, vue) {
  DSP.focus = focus;
  if (vue) DSP.vue = vue;
  DSP.defiler = true;
  rendreDsp();
}
function decalerDsp(sens) {
  const auj = AUJ();
  if (DSP.vue === 'jour') return allerDsp(jPlus(DSP.focus, sens));
  if (DSP.vue === 'semaine') return allerDsp(jPlus(DSP.focus, 7 * sens));
  const d = jDt(DSP.focus.slice(0, 8) + '01'); d.setMonth(d.getMonth() + sens);
  const m = jourIso(d);
  allerDsp(m.slice(0, 7) === auj.slice(0, 7) ? auj : m);
}

/* ── Couche : tiroir, fenêtre, notification ─────────────────────────── */
function couche() {
  let c = $('#dsp-couche');
  if (!c) {
    c = document.createElement('div');
    c.id = 'dsp-couche';
    c.innerHTML = '<div id="dsp-voile" data-dsp-fermer></div>'
      + '<aside id="dsp-tiroir" role="dialog" aria-modal="true" aria-label="Modifier la disponibilité"></aside>'
      + '<div id="dsp-modal"></div><div id="dsp-toast" role="status" aria-live="polite"></div>';
    document.body.appendChild(c);
  }
  return c;
}

let TOAST_T = null;
function notifier(texte, mal) {
  couche();
  const t = $('#dsp-toast');
  t.textContent = (mal ? '! ' : '✓ ') + texte;
  t.className = 'on' + (mal ? ' mal' : '');
  clearTimeout(TOAST_T);
  TOAST_T = setTimeout(() => { t.className = mal ? 'mal' : ''; }, 3200);
}

const radio = (nom, liste, cur) => liste.map(([v, l, c]) => `<label class="dsp-radio ${cur === v ? 'on' : ''}">
  <input type="radio" name="${nom}" value="${v}" ${cur === v ? 'checked' : ''}>
  ${c ? `<span class="pt" style="--c:${c}"></span>` : ''}${l}</label>`).join('');

function rendreTiroir() {
  couche();
  const tr = DSP.tiroir, el = $('#dsp-tiroir');
  $('#dsp-voile').classList.toggle('on', !!tr);
  el.classList.toggle('on', !!tr);
  el.setAttribute('aria-hidden', tr ? 'false' : 'true');
  if (!tr) return;
  const chambres = ETAT.chambres || [], F = ETAT.fermetures || [], auj = AUJ();
  let qui, corps, statuts, avert = '', bloque = false;

  if (tr.mode === 'cat') {
    const c = ETAT.categories.find((x) => x.slug === tr.slug);
    const x = calculerDisponibilites([c], chambres, F, [tr.nuit], auj, DSP.seuil).parCat[tr.slug][tr.nuit];
    const perm = chambres.filter((ch) => ch.categorie === tr.slug && ch.service === false).length;
    const max = x.total - x.reserves - perm, v = tr.ajust;
    tr.max = max;
    qui = [vignette(c.slug), c.nom];
    corps = `<div class="dsp-chiffres">
        <div><span>Total des chambres</span><b>${x.total}</b></div>
        <div><span>Réservées</span><b>${x.reserves}</b></div>
        <div><span>Hors service</span><b>${x.bloques}</b></div>
        <div class="fort"><span style="display:flex;align-items:center;gap:10px"><span class="pt"
          style="--c:${DTON[x.etat][0]}"></span>Disponibles</span><b>${x.libres}</b></div>
      </div>
      <div class="dsp-ajust"><span class="lb" id="dsp-aj" style="margin:0">Ajuster la disponibilité</span>
        <div class="dsp-pas" role="group" aria-labelledby="dsp-aj">
          <button data-dsp-ajust="-1" ${v <= 0 ? 'disabled' : ''} aria-label="Une chambre disponible de moins">−</button>
          <output aria-live="polite">${v}</output>
          <button data-dsp-ajust="1" ${v >= max ? 'disabled' : ''} aria-label="Une chambre disponible de plus">+</button>
        </div></div>
      <p class="aide" style="margin:0 0 20px">Entre 0 et ${max} : les chambres réservées${perm
        ? ' et hors service' : ''} ne se libèrent pas ici.</p>`;
    statuts = radio('dsp-statut', [['dispo', 'Disponible', '#8FAE63'], ['complet', 'Complet', '#E08A7B'],
      ['hs', 'Hors service', '#9C8B78']], tr.statut);
    if (tr.statut === 'hs' && x.reserves > 0) {
      avert = x.reserves + (x.reserves > 1 ? ' chambres sont réservées' : ' chambre est réservée')
        + ' cette nuit. Seules les chambres libres seront mises hors service : pour les autres, '
        + 'traitez d’abord la réservation.';
    }
  } else {
    const ch = chambres.find((x) => x.id === tr.id);
    const c = ETAT.categories.find((x) => x.slug === ch.categorie) || { nom: '' };
    const e = dspEtat(ch, tr.nuit, dspIndex(F, chambres), auj), [teinte, mot] = DTON[e.k];
    const client = e.k === 'occ' || e.k === 'res';
    const det = client
      ? (e.f.client || 'Fermeture') + ' — arrivée ' + jCourt(e.f.debut) + ', départ '
        + jCourt(jPlus(e.f.fin, 1)) + ' · ' + (e.f.statut === 'attente' ? 'en attente' : 'confirmée') + '.'
      : e.k === 'hs' || e.k === 'vente' ? (e.f ? e.f.motif + ' — ' + nuitsEnClair(e.f).toLowerCase() + '.'
        : (e.motif || '') + ' — sans date de fin.') : '';
    qui = [vignette(ch.categorie), 'Chambre ' + ch.numero + (c.nom ? ' · ' + c.nom : '')];
    corps = `<div class="dsp-chiffres"><div><span>État cette nuit</span>
        <span class="etat" style="color:${teinte};border-color:${teinte}">${mot}</span></div>
        ${det ? `<div><span style="color:#D6CBBB;font-size:13px">${ech(det)}</span></div>` : ''}</div>`;
    statuts = radio('dsp-statut', [['dispo', 'Disponible', '#8FAE63'],
      ['complet', 'Bloquée à la vente', '#E08A7B'], ['hs', 'Hors service', '#9C8B78']], tr.statut);
    if (client && tr.statut === 'hs') {
      bloque = true;
      avert = 'Cette chambre possède une réservation ' + (e.f.statut === 'attente' ? 'en attente'
        : 'confirmée') + ' sur cette période. Vous ne pouvez pas la mettre hors service sans '
        + 'traiter d’abord la réservation.';
    }
  }

  el.innerHTML = `<div class="dsp-th"><h2>Modifier la disponibilité</h2>
      <button class="dsp-x" data-dsp-fermer aria-label="Fermer">×</button></div>
    <div class="dsp-tc">
      <div class="dsp-qui">${qui[0]}<div><b>${ech(qui[1])}</b><span>${jLong(tr.nuit)}</span></div></div>
      ${corps}
      <span class="lb" style="margin-top:0">Statut</span>
      <div role="radiogroup" aria-label="Statut" style="margin-bottom:18px">${statuts}</div>
      ${avert ? `<div class="alerte ambre" role="alert"><b>Attention</b><span>${avert}</span></div>` : ''}
      <label for="dsp-com">Commentaire (facultatif)</label>
      <textarea id="dsp-com" maxlength="120" style="min-height:80px"
        placeholder="Ex. : maintenance, travaux, problème technique...">${ech(tr.commentaire || '')}</textarea>
      <p class="aide">Pour vous seuls : le site écrit « Complet », jamais le motif.</p>
      ${tr.erreur !== undefined && tr.erreur !== false ? `<p class="msg mal" role="alert" style="margin-top:14px">
        Impossible d'enregistrer les modifications. Vérifiez votre connexion puis réessayez.
        ${tr.erreur ? '<br>' + ech(tr.erreur) : ''}</p>` : ''}
    </div>
    <div class="dsp-tp">
      <button class="btn" data-dsp-fermer>Annuler</button>
      <button class="btn plein" id="dsp-enreg" ${bloque ? 'disabled style="opacity:.4;cursor:default"' : ''}>
        Enregistrer les modifications</button>
    </div>`;
}

function ouvrirCat(slug, nuit) {
  const c = ETAT.categories.find((x) => x.slug === slug);
  const x = calculerDisponibilites([c], ETAT.chambres, ETAT.fermetures, [nuit], AUJ(), DSP.seuil)
    .parCat[slug][nuit];
  DSP.tiroir = { mode: 'cat', slug, nuit, ajust: x.libres, commentaire: '', erreur: false,
    statut: x.libres ? 'dispo' : x.etat === 'hs' ? 'hs' : 'complet' };
  rendreTiroir();
  setTimeout(() => { const b = $('#dsp-tiroir .dsp-x'); if (b) b.focus(); }, 60);
}
function ouvrirChambre(id, nuit) {
  const ch = ETAT.chambres.find((x) => x.id === id);
  const e = dspEtat(ch, nuit, dspIndex(ETAT.fermetures, ETAT.chambres), AUJ());
  DSP.tiroir = { mode: 'chambre', id, nuit, commentaire: '', erreur: false,
    statut: e.k === 'hs' ? 'hs' : e.k === 'vente' ? 'complet' : 'dispo' };
  rendreTiroir();
  setTimeout(() => { const b = $('#dsp-tiroir .dsp-x'); if (b) b.focus(); }, 60);
}

/* ── Écritures ────────────────────────────────────────────────────────
   Toujours par les routes existantes. Une fermeture qui doit rouvrir une
   nuit est découpée : les morceaux qui restent sont écrits AVANT que
   l original soit retiré, pour qu un échec en route ne rouvre jamais plus
   que prévu. */
async function poserF(f) {
  const entree = Object.assign({}, f, { sansFin: f.fin == null });
  const r = await appel('enregistrer', { type: 'fermeture', entree });
  if (!r.ok) throw new Error(r.message || 'Échec de l’enregistrement.');
  ETAT.fermetures = (ETAT.fermetures || []).filter((x) => x.id !== r.entree.id).concat([r.entree]);
  return r.entree;
}
async function oterF(id) {
  const r = await appel('supprimer', { type: 'fermeture', id });
  if (!r.ok) throw new Error(r.message || 'Échec de la suppression.');
  ETAT.fermetures = (ETAT.fermetures || []).filter((x) => x.id !== id);
}
async function libererF(ids, a, b) {
  const S = new Set(ids), chambres = ETAT.chambres || [];
  const visees = (ETAT.fermetures || []).filter((f) => !fClient(f) && fChevauche(f, a, b)
    && chambres.some((c) => fVise(f, c) && S.has(c.id)));
  for (const f of visees) {
    const base = { cible: f.cible, nature: f.nature, motif: f.motif };
    if (f.debut < a) await poserF(Object.assign({}, base, { debut: f.debut, fin: jPlus(a, -1) }));
    if (f.fin == null || f.fin > b) await poserF(Object.assign({}, base, { debut: jPlus(b, 1), fin: f.fin }));
    const s0 = f.debut > a ? f.debut : a, e0 = (f.fin == null || f.fin > b) ? b : f.fin;
    for (const c of chambres.filter((c) => fVise(f, c) && !S.has(c.id))) {
      await poserF(Object.assign({}, base, { cible: c.id, debut: s0, fin: e0 }));
    }
    await oterF(f.id);
  }
}

async function enregistrerTiroir() {
  const tr = DSP.tiroir;
  if (!tr) return;
  const btn = $('#dsp-enreg');
  if (btn) { btn.disabled = true; btn.textContent = 'Enregistrement…'; }
  const chambres = ETAT.chambres, auj = AUJ(), motif = (tr.commentaire || '').trim();
  const bloc = (ch, nature) => ({ cible: ch.id, debut: tr.nuit, fin: tr.nuit, nature,
    motif: motif || (nature === 'hors-service' ? 'Hors service' : 'Fermée à la vente') });
  try {
    if (tr.mode === 'cat') {
      const idx = dspIndex(ETAT.fermetures, chambres);
      const etats = chambres.filter((c) => c.categorie === tr.slug).sort(parNum)
        .map((ch) => ({ ch, e: dspEtat(ch, tr.nuit, idx, auj) }));
      const libres = etats.filter((x) => x.e.k === 'libre');
      const bloquees = etats.filter((x) => (x.e.k === 'hs' || x.e.k === 'vente') && x.ch.service !== false);
      const cible = tr.statut === 'dispo' ? tr.ajust : 0;
      if (cible < libres.length) {
        for (const x of libres.slice(cible)) await poserF(bloc(x.ch, tr.statut === 'hs' ? 'hors-service' : 'vente'));
      } else if (cible > libres.length) {
        await libererF(bloquees.slice(0, cible - libres.length).map((x) => x.ch.id), tr.nuit, tr.nuit);
      }
    } else {
      const ch = chambres.find((x) => x.id === tr.id);
      const e = dspEtat(ch, tr.nuit, dspIndex(ETAT.fermetures, chambres), auj);
      if (e.k !== 'occ' && e.k !== 'res') {
        if (tr.statut === 'dispo') {
          if (ch.service === false) {
            const r = await appel('enregistrer', { type: 'chambre',
              entree: Object.assign({}, ch, { service: true }) });
            if (!r.ok) throw new Error(r.message);
            ETAT.chambres = ETAT.chambres.map((x) => (x.id === ch.id ? r.entree : x));
          } else await libererF([ch.id], tr.nuit, tr.nuit);
        } else if (ch.service !== false) {
          await libererF([ch.id], tr.nuit, tr.nuit);
          await poserF(bloc(ch, tr.statut === 'hs' ? 'hors-service' : 'vente'));
        }
      }
    }
    DSP.tiroir = null;
    rendreTiroir();
    rendre();
    notifier('Disponibilité mise à jour');
  } catch (err) {
    if (err.message === 'session') return;
    tr.erreur = err.message || '';
    rendreTiroir();
    rendre();
    notifier('Impossible d’enregistrer les modifications.', true);
  }
}

/* ── Modifier en lot, Nouvelle réservation ──────────────────────────── */
function ouvrirLot() {
  const cat = (ETAT.categories[0] || {}).slug, auj = AUJ();
  DSP.modal = { type: 'lot', etape: 'form', cat, action: 'hs', raison: '', erreur: '',
    ids: ETAT.chambres.filter((c) => c.categorie === cat).map((c) => c.id),
    debut: jPlus(auj, 1), fin: jPlus(auj, 3) };
  rendreModal();
}
function ouvrirResa() {
  const auj = AUJ();
  DSP.modal = { type: 'resa', cat: (ETAT.categories[0] || {}).slug, debut: auj, fin: jPlus(auj, 2),
    n: '1', client: '', statut: 'confirmee', erreur: '' };
  rendreModal();
}
function analyseLot() {
  const m = DSP.modal;
  const choisies = ETAT.chambres.filter((c) => m.ids.includes(c.id)).sort(parNum);
  const conflits = m.action === 'dispo' ? [] : choisies.map((ch) => {
    const f = ETAT.fermetures.find((x) => fClient(x) && x.statut !== 'annulee'
      && fVise(x, ch) && fChevauche(x, m.debut, m.fin));
    return f ? { ch, f } : null;
  }).filter(Boolean);
  const exclues = new Set(conflits.map((x) => x.ch.id));
  return { conflits, retenues: choisies.filter((c) => !exclues.has(c.id)) };
}
function libresResa() {
  const m = DSP.modal;
  if (!m.debut || !m.fin || m.fin <= m.debut) return [];
  const der = jPlus(m.fin, -1);
  return ETAT.chambres.filter((ch) => ch.categorie === m.cat && ch.service !== false
    && !ETAT.fermetures.some((f) => f.statut !== 'annulee' && fVise(f, ch) && fChevauche(f, m.debut, der)))
    .sort(parNum);
}

function rendreModal() {
  couche();
  const m = DSP.modal, el = $('#dsp-modal');
  el.classList.toggle('on', !!m);
  if (!m) { el.innerHTML = ''; return; }
  const catOpt = ETAT.categories.map((c) => `<option value="${ech(c.slug)}" ${c.slug === m.cat
    ? 'selected' : ''}>${ech(c.nom)}</option>`).join('');
  const choix = (liste, cur, cle, cols) => `<div class="choix ${cols === 3 ? 'trois' : ''}"
    style="margin-bottom:18px">${liste.map(([v, l]) => `<button type="button"
      class="opt ${cur === v ? 'on' : ''}" data-dsp-opt="${cle}" data-v="${v}">${l}</button>`).join('')}</div>`;
  let titre, corps, pied;

  if (m.type === 'resa') {
    const libres = libresResa();
    titre = 'Nouvelle réservation';
    corps = `<div class="champ"><label for="rs-cat">Catégorie</label>
        <select id="rs-cat" data-dsp-champ="cat" data-rerendre>${catOpt}</select></div>
      <div class="duo" style="margin-bottom:0">
        <div class="champ" style="margin-bottom:6px"><label for="rs-a">Arrivée</label>
          <input type="date" id="rs-a" data-dsp-champ="debut" data-rerendre value="${m.debut}"></div>
        <div class="champ" style="margin-bottom:6px"><label for="rs-d">Départ</label>
          <input type="date" id="rs-d" data-dsp-champ="fin" data-rerendre value="${m.fin}"></div>
      </div>
      <p class="aide" style="margin:0 0 18px">${m.fin > m.debut ? libres.length + ' chambre'
        + (libres.length > 1 ? 's libres' : ' libre') + ' sur ces nuits. Le client repart le matin '
        + 'du départ : cette nuit-là reste libre.' : 'Le départ doit suivre l’arrivée.'}</p>
      <div class="duo">
        <div class="champ"><label for="rs-c">Client</label>
          <input id="rs-c" data-dsp-champ="client" maxlength="60" placeholder="M. Koné" value="${ech(m.client)}"></div>
        <div class="champ"><label for="rs-n">Chambres</label>
          <input id="rs-n" type="number" min="1" max="${Math.max(1, libres.length)}"
            data-dsp-champ="n" value="${ech(m.n)}"></div>
      </div>
      <span class="lb" style="margin-top:0">Statut</span>
      ${choix([['confirmee', 'Confirmée'], ['attente', 'En attente']], m.statut, 'statut')}`;
    pied = `<button class="btn" data-dsp-fermer>Annuler</button>
      <button class="btn plein" id="dsp-valider">Enregistrer la réservation</button>`;
  } else if (m.etape === 'form') {
    const siennes = ETAT.chambres.filter((c) => c.categorie === m.cat).sort(parNum);
    const toutes = siennes.length && siennes.every((c) => m.ids.includes(c.id));
    titre = 'Modifier en lot';
    corps = `<div class="champ"><label for="lot-cat">Catégorie</label>
        <select id="lot-cat" data-dsp-lotcat>${catOpt}</select></div>
      <div style="display:flex;justify-content:space-between;align-items:baseline">
        <span class="lb" style="margin-top:0">Chambres</span>
        <button class="dsp-lien" style="padding:0" data-dsp-toutes>${toutes ? 'Aucune' : 'Toutes'}</button></div>
      <div class="dsp-coches">${siennes.map((ch) => `<label class="dsp-radio ${m.ids.includes(ch.id)
        ? 'on' : ''}"><input type="checkbox" data-dsp-coche="${ech(ch.id)}" ${m.ids.includes(ch.id)
        ? 'checked' : ''}>${ech(ch.numero)}</label>`).join('')
        || '<p class="aide">Aucune chambre saisie dans cette catégorie.</p>'}</div>
      <div class="duo" style="margin-bottom:0">
        <div class="champ" style="margin-bottom:6px"><label for="lot-d">Première nuit</label>
          <input type="date" id="lot-d" data-dsp-champ="debut" value="${m.debut}"></div>
        <div class="champ" style="margin-bottom:6px"><label for="lot-f">Dernière nuit</label>
          <input type="date" id="lot-f" data-dsp-champ="fin" value="${m.fin}"></div>
      </div>
      <p class="aide" style="margin:0 0 18px">Les dates sont des nuits : du 24 au 26, ce sont les
        nuits du 24, du 25 et du 26.</p>
      <span class="lb" style="margin-top:0">Action</span>
      ${choix([['hs', 'Mettre hors service'], ['dispo', 'Rendre disponible'], ['vente', 'Bloquer']],
        m.action, 'action', 3)}
      <div class="champ" style="margin:0"><label for="lot-r">Raison</label>
        <input id="lot-r" data-dsp-champ="raison" maxlength="120" value="${ech(m.raison)}"
          placeholder="Ex. : maintenance, travaux, problème technique..."></div>`;
    pied = `<button class="btn" data-dsp-fermer>Annuler</button>
      <button class="btn plein" id="dsp-valider">Voir le résumé</button>`;
  } else {
    const a = analyseLot(), c = ETAT.categories.find((x) => x.slug === m.cat), n = a.retenues.length;
    const quoi = { hs: 'hors service', dispo: 'disponibles à la vente', vente: 'bloquées à la vente' }[m.action];
    const nuits = Math.round((jDt(m.fin) - jDt(m.debut)) / 864e5) + 1;
    titre = 'Modifier en lot';
    corps = `<p style="margin-bottom:10px">Vous êtes sur le point de mettre :</p>
      <div class="dsp-recap"><b>${n} chambre${n > 1 ? 's' : ''} ${ech(c.nom)}${n
        ? ' (' + a.retenues.map((x) => ech(x.numero)).join(', ') + ')' : ''}</b>
        <span>${m.debut === m.fin ? 'la nuit du ' + jLong(m.debut).toLowerCase()
          : 'du ' + jCourt(m.debut) + ' au ' + jCourt(m.fin) + ' inclus — ' + nuits + ' nuits'}</span>
        <span style="color:var(--bronze-2);margin-top:4px">${quoi}${m.raison.trim()
          ? ' — ' + ech(m.raison.trim()) : ''}.</span></div>
      ${a.conflits.length ? `<div class="alerte ambre" role="alert"><b>Attention</b>
        <span>Ces chambres ont une réservation sur cette période. Vous ne pouvez pas les mettre
        ${quoi} sans traiter d'abord la réservation : elles sont écartées.<br>${a.conflits.map((x) =>
          'Chambre ' + ech(x.ch.numero) + ' — ' + ech(x.f.client || x.f.motif || 'Fermeture') + ', du '
          + jCourt(x.f.debut) + ' au ' + jCourt(jPlus(x.f.fin, 1))).join('<br>')}</span></div>` : ''}`;
    pied = `<button class="btn" data-dsp-retour>${n ? 'Retour' : 'Annuler'}</button>
      ${n ? '<button class="btn plein" id="dsp-valider">Confirmer</button>' : ''}`;
  }
  el.innerHTML = `<div class="fond" data-dsp-fermer></div>
    <div class="dsp-boite" role="dialog" aria-modal="true" aria-label="${titre}">
      <div class="dsp-th"><h2>${titre}</h2>
        <button class="dsp-x" data-dsp-fermer aria-label="Fermer">×</button></div>
      <div class="dsp-tc">${corps}
        ${m.erreur ? `<p class="msg mal" role="alert" style="margin-top:14px">${ech(m.erreur)}</p>` : ''}</div>
      <div class="dsp-tp">${pied}</div>
    </div>`;
}

async function validerModal() {
  const m = DSP.modal;
  const dire = (t) => { m.erreur = t; rendreModal(); };
  const echec = (err) => { if (err.message !== 'session') dire('Impossible d’enregistrer les modifications. '
    + 'Vérifiez votre connexion puis réessayez. ' + (err.message || '')); rendre(); };
  const btn = $('#dsp-valider');
  if (m.type === 'resa') {
    const libres = libresResa(), n = Number(m.n) || 0;
    if (!m.client.trim()) return dire('Indiquez le nom du client.');
    if (!m.debut || !m.fin || m.fin <= m.debut) return dire('Le départ doit suivre l’arrivée d’au moins une nuit.');
    if (n < 1 || n > libres.length) {
      return dire(libres.length ? 'Il ne reste que ' + libres.length + ' chambre'
        + (libres.length > 1 ? 's libres' : ' libre') + ' sur ces nuits.' : 'Aucune chambre libre sur ces nuits.');
    }
    if (btn) { btn.disabled = true; btn.textContent = 'Enregistrement…'; }
    try {
      for (const ch of libres.slice(0, n)) {
        await poserF({ cible: ch.id, debut: m.debut, fin: jPlus(m.fin, -1), nature: 'client',
          client: m.client.trim(), statut: m.statut, motif: '' });
      }
    } catch (err) { return echec(err); }
    DSP.modal = null; rendreModal(); rendre();
    return notifier('Réservation enregistrée');
  }
  if (m.etape === 'form') {
    if (!m.ids.length) return dire('Choisissez au moins une chambre.');
    if (!m.debut || !m.fin) return dire('Indiquez la première et la dernière nuit.');
    if (m.fin < m.debut) return dire('La dernière nuit précède la première.');
    m.etape = 'recap'; m.erreur = '';
    return rendreModal();
  }
  const { retenues } = analyseLot();
  if (btn) { btn.disabled = true; btn.textContent = 'Enregistrement…'; }
  try {
    await libererF(retenues.map((c) => c.id), m.debut, m.fin);
    if (m.action !== 'dispo') {
      const nature = m.action === 'hs' ? 'hors-service' : 'vente';
      for (const ch of retenues) {
        await poserF({ cible: ch.id, debut: m.debut, fin: m.fin, nature,
          motif: m.raison.trim() || (nature === 'hors-service' ? 'Hors service' : 'Fermée à la vente') });
      }
    }
  } catch (err) { return echec(err); }
  DSP.modal = null; rendreModal(); rendre();
  notifier('Modifications enregistrées');
}

/* ── Événements ───────────────────────────────────────────────────────
   Appelée en tête de l écouteur de clics de la page : rend true si le clic
   concernait le calendrier. */
function clicDsp(e) {
  const t = e.target, q = (s) => t.closest(s);
  let b;
  if ((b = q('[data-dsp-fermer]'))) { DSP.tiroir = null; DSP.modal = null; rendreTiroir(); rendreModal(); return true; }
  if ((b = q('[data-dsp-pas]'))) { decalerDsp(Number(b.dataset.dspPas)); return true; }
  if ((b = q('[data-dsp-vue]'))) { allerDsp(DSP.focus, b.dataset.dspVue); return true; }
  if ((b = q('[data-dsp-ouvrir]'))) {
    const s = b.dataset.dspOuvrir;
    DSP.ouvertes[s] = b.getAttribute('aria-expanded') !== 'true';
    rendreDsp(); return true;
  }
  if ((b = q('[data-dsp-cat]'))) { ouvrirCat(b.dataset.dspCat, b.dataset.nuit); return true; }
  if ((b = q('[data-dsp-ch]'))) { ouvrirChambre(b.dataset.dspCh, b.dataset.nuit); return true; }
  if (q('[data-dsp-voirtout]')) { DSP.voirTout = !DSP.voirTout; rendreDsp(); return true; }
  if (t.id === 'dsp-resa-btn') { ouvrirResa(); return true; }
  if (t.id === 'dsp-lot-btn') { ouvrirLot(); return true; }
  if ((b = q('[data-dsp-ajust]')) && DSP.tiroir) {
    const tr = DSP.tiroir, v = Math.max(0, Math.min(tr.max, tr.ajust + Number(b.dataset.dspAjust)));
    tr.ajust = v;
    tr.statut = v > 0 ? 'dispo' : (tr.statut === 'hs' ? 'hs' : 'complet');
    rendreTiroir(); return true;
  }
  if (t.id === 'dsp-enreg') { enregistrerTiroir(); return true; }
  if ((b = q('[data-dsp-opt]')) && DSP.modal) { DSP.modal[b.dataset.dspOpt] = b.dataset.v; DSP.modal.erreur = ''; rendreModal(); return true; }
  if (q('[data-dsp-toutes]') && DSP.modal) {
    const siennes = ETAT.chambres.filter((c) => c.categorie === DSP.modal.cat).map((c) => c.id);
    DSP.modal.ids = siennes.every((id) => DSP.modal.ids.includes(id)) ? [] : siennes;
    rendreModal(); return true;
  }
  if (q('[data-dsp-retour]') && DSP.modal) { DSP.modal.etape = 'form'; rendreModal(); return true; }
  if (t.id === 'dsp-valider') { validerModal(); return true; }
  return false;
}

document.addEventListener('input', (e) => {
  if (e.target.id === 'dsp-com' && DSP.tiroir) DSP.tiroir.commentaire = e.target.value;
  const k = e.target.dataset && e.target.dataset.dspChamp;
  if (k && DSP.modal && !e.target.hasAttribute('data-rerendre')) DSP.modal[k] = e.target.value;
});
document.addEventListener('change', (e) => {
  const t = e.target;
  if (t.id === 'dsp-mois') {
    const v = t.value, auj = AUJ();
    return allerDsp(v === auj.slice(0, 7) ? auj : v + '-01');
  }
  if (t.name === 'dsp-statut' && DSP.tiroir) {
    const tr = DSP.tiroir;
    tr.statut = t.value;
    if (tr.mode === 'cat') tr.ajust = t.value === 'dispo' ? (tr.ajust > 0 ? tr.ajust : tr.max) : 0;
    return rendreTiroir();
  }
  if (!DSP.modal) return;
  if (t.hasAttribute('data-dsp-lotcat')) {
    DSP.modal.cat = t.value;
    DSP.modal.ids = ETAT.chambres.filter((c) => c.categorie === t.value).map((c) => c.id);
    return rendreModal();
  }
  if (t.dataset.dspCoche) {
    const id = t.dataset.dspCoche, ids = DSP.modal.ids;
    DSP.modal.ids = t.checked ? ids.concat([id]) : ids.filter((x) => x !== id);
    return rendreModal();
  }
  const k = t.dataset && t.dataset.dspChamp;
  if (k) { DSP.modal[k] = t.value; DSP.modal.erreur = ''; if (t.hasAttribute('data-rerendre')) rendreModal(); }
});
document.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape' || (!DSP.tiroir && !DSP.modal)) return;
  DSP.tiroir = null; DSP.modal = null; rendreTiroir(); rendreModal();
});
