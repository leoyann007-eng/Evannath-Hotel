/* ──────────────────────────────────────────────────────────────────────
   Module « Chambres » — le referentiel des chambres physiques de l'hotel.

   Ce qu'il gere : ce qu'EST une chambre. Son numero, sa categorie, son
   etage, sa capacite, son lit, sa surface, ses equipements, sa description,
   ses photos, son statut (active / maintenance / hors service) et sa
   publication sur le site.

   Ce qu'il NE gere PAS : le calendrier. Sejours, retenues et fermetures
   datees restent exclusivement dans Disponibilites. D'ici, on y renvoie.

   Deux regles qu'il faut connaitre pour lire l'ecran :
   - Le PRIX DE BASE est celui de la categorie. Le site vend des categories,
     et l'acompte se calcule sur leur prix : un prix propre a la chambre 104
     serait affiche ici et ignore partout ailleurs. On le montre, et on
     envoie le modifier la ou il vaut — l'onglet « Categories et prix ».
   - PUBLIEE veut dire « le site peut la vendre en ligne ». Une chambre non
     publiee, en maintenance ou hors service ne compte plus dans les
     disponibilites du site (api/admin.js, vendable) ; elle reste au
     calendrier, ou la reception la gere a la main.

   Les chambres enregistrees avant ce module n'ont ni `statut` ni `publie` :
   `service:false` vaut « hors service », et l'absence de `publie` vaut
   « publiee » — exactement ce que le serveur en deduit.
   ────────────────────────────────────────────────────────────────────── */

const CM = {
  onglet: 'inventaire',      // 'inventaire' | 'categories'
  mode: 'liste',             // 'liste' | 'voir' | 'form'
  id: null,                  // la chambre vue ou modifiee (null : ajout)
  brouillon: null,           // le formulaire en cours
  erreurs: [],               // les champs a reprendre
  photoVue: 0,               // la photo affichee dans la fiche
  filtres: { q: '', cat: '', statut: '', site: '' },
  occupe: new Set(),         // les ids dont une bascule est en cours
};

/** Remis a zero quand on arrive par le menu : on retombe sur la liste. */
function cmReinit() {
  CM.mode = 'liste'; CM.id = null; CM.brouillon = null; CM.erreurs = [];
}

const CM_STATUTS = {
  'active':       { lib: 'Active',       aide: 'Elle se loue normalement.' },
  'maintenance':  { lib: 'Maintenance',  aide: 'Temporairement indisponible — travaux, réparation.' },
  'hors-service': { lib: 'Hors service', aide: 'Désactivée jusqu’à nouvel ordre.' },
};

/* Des suggestions, pas des affirmations : rien n'est coche d'office. Le
   site ne dit pas, chambre par chambre, ce qu'il y a dedans. */
const CM_EQUIPEMENTS = ['Climatisation', 'Wi-Fi', 'Télévision', 'Salle d’eau privative',
  'Baignoire', 'Douche à l’italienne', 'Minibar', 'Coffre-fort', 'Bureau', 'Coin salon',
  'Terrasse', 'Balcon', 'Vue lagune', 'Vue jardin', 'Vue piscine', 'Moustiquaire',
  'Sèche-cheveux', 'Bouilloire'];

const CM_LITS = ['Queen', 'King', 'Double', 'Deux lits simples', 'Simple', 'Baldaquin', 'Canapé-lit'];

/* ── Lecture ───────────────────────────────────────────────────────── */

const cmStatut = (ch) => (CM_STATUTS[ch.statut] ? ch.statut
  : (ch.service === false ? 'hors-service' : 'active'));
const cmPubliee = (ch) => ch.publie !== false;
const cmCat = (slug) => (ETAT.grille || []).find((c) => c.slug === slug) || null;
const cmNomCat = (slug) => (cmCat(slug) || {}).nom || slug || '—';
const cmPrix = (slug) => { const c = cmCat(slug); return c ? prixActuel(c) : null; };
const cmParNum = (a, b) => String(a.numero).localeCompare(String(b.numero), 'fr',
  { numeric: true, sensitivity: 'base' });
/** Une photo : le nom d'une image du site, ou l'adresse d'un depot. */
const cmSrc = (p, petit) => (/^https?:/.test(p) ? p
  : '/img/opt/' + p + (petit && ETAT.images640 && ETAT.images640.has(p) ? '-640' : '') + '.jpg');
function cmCouverture(ch) {
  if (ch.photos && ch.photos.length) return { src: cmSrc(ch.photos[0], true), propre: true };
  const c = cmCat(ch.categorie);
  return { src: c ? '/img/opt/' + c.photo + '.jpg' : '', propre: false };
}
const cmChambre = (id) => (ETAT.chambres || []).find((x) => x.id === id) || null;
const cmPl = (n, un, plus) => n + ' ' + (n > 1 ? plus : un);

/** Les sejours a venir poses sur cette chambre (lecture seule : c'est le
 *  calendrier qui les gere). Sert a prevenir avant une action sensible. */
function cmSejours(id) {
  const auj = new Date().toISOString().slice(0, 10);
  const lache = (f) => f.statut !== 'confirmee' && f.paiement
    && ['echoue', 'abandonne', 'remplace'].includes(f.paiement.statut);
  return (ETAT.fermetures || []).filter((f) => f && f.cible === id && f.nature === 'client'
    && f.statut !== 'annulee' && !lache(f) && (f.fin == null || f.fin >= auj));
}

/* ── La vue ────────────────────────────────────────────────────────── */

function vueChambresModule() {
  const onglets = `<div class="cm-onglets" role="tablist">
      <button role="tab" data-cm-onglet="inventaire" aria-selected="${CM.onglet === 'inventaire'}">Chambres</button>
      <button role="tab" data-cm-onglet="categories" aria-selected="${CM.onglet === 'categories'}">Catégories et prix</button>
    </div>`;
  if (CM.onglet === 'categories') {
    /* La liste des categories et leur prix : voir vueChambres() dans
       index.html. On y glisse les onglets sous l'entete. */
    return vueChambres(onglets);
  }
  if (CM.mode === 'form') return cmFormulaire();
  if (CM.mode === 'voir' && cmChambre(CM.id)) return cmFiche(cmChambre(CM.id));
  return cmListe(onglets);
}

function cmListe(onglets) {
  const toutes = (ETAT.chambres || []).slice().sort(cmParNum);
  const n = toutes.length;
  const st = { active: 0, maintenance: 0, 'hors-service': 0 };
  toutes.forEach((c) => { st[cmStatut(c)]++; });
  const pub = toutes.filter(cmPubliee).length;
  const annoncees = ETAT.annoncees || 0;
  const parCat = (ETAT.grille || []).map((c) => ({ c, n: toutes.filter((x) => x.categorie === c.slug).length }));
  const maxCat = Math.max(1, ...parCat.map((x) => x.n));
  const pct = (k) => (n ? (100 * k / n).toFixed(1) : 0) + '%';

  const kpis = `<div class="cm-kpis">
    <div class="cm-kpi"><span>Chambres</span>
      <div class="cm-grand">${n}${annoncees ? `<small>sur ${annoncees} annoncées</small>` : ''}</div>
      <div class="cm-jauge" title="${n} saisies sur ${annoncees || n}"><i style="--c:var(--bronze);width:${
        annoncees ? Math.min(100, 100 * n / annoncees) : (n ? 100 : 0)}%"></i></div>
    </div>
    <div class="cm-kpi"><span>Statut</span>
      <div class="cm-jauge">${['active', 'maintenance', 'hors-service'].map((k) =>
        `<i class="cm-s-${k}" style="width:${pct(st[k])}"></i>`).join('')}</div>
      <div class="cm-repart">
        <div><span class="cm-pt cm-s-active"></span>Actives<b>${st.active}</b></div>
        <div><span class="cm-pt cm-s-maintenance"></span>En maintenance<b>${st.maintenance}</b></div>
        <div><span class="cm-pt cm-s-hors-service"></span>Hors service<b>${st['hors-service']}</b></div>
      </div></div>
    <div class="cm-kpi"><span>Sur le site</span>
      <div class="cm-jauge"><i style="--c:var(--palm);width:${pct(pub)}"></i></div>
      <div class="cm-repart">
        <div><span class="cm-pt" style="--c:var(--palm)"></span>Publiées<b>${pub}</b></div>
        <div><span class="cm-pt" style="--c:#C9CFD8"></span>Non publiées<b>${n - pub}</b></div>
      </div></div>
    <div class="cm-kpi cm-kpi-cats"><span>Par catégorie</span>
      <div class="cm-cats">${parCat.map(({ c, n: k }) => `<div title="${ech(c.nom)} : ${k}">
        <span>${ech(c.nom)}</span><i style="--w:${100 * k / maxCat}%"></i><b>${k}</b></div>`).join('')}</div>
    </div></div>`;

  const f = CM.filtres;
  const q = f.q.trim().toLowerCase();
  const vues = toutes.filter((c) => (!q || String(c.numero).toLowerCase().includes(q)
      || cmNomCat(c.categorie).toLowerCase().includes(q) || String(c.etage || '').toLowerCase().includes(q))
    && (!f.cat || c.categorie === f.cat)
    && (!f.statut || cmStatut(c) === f.statut)
    && (!f.site || (f.site === 'oui') === cmPubliee(c)));

  const opt = (v, l, cur) => `<option value="${ech(v)}" ${cur === v ? 'selected' : ''}>${ech(l)}</option>`;
  const outils = `<div class="cm-outils">
    <input type="search" id="cm-q" placeholder="N°, catégorie, étage…" value="${ech(f.q)}" aria-label="Rechercher une chambre">
    <select id="cm-f-cat" aria-label="Catégorie">${opt('', 'Toutes les catégories', f.cat)}${
      (ETAT.grille || []).map((c) => opt(c.slug, c.nom, f.cat)).join('')}</select>
    <select id="cm-f-statut" aria-label="Statut">${opt('', 'Tous les statuts', f.statut)}${
      Object.entries(CM_STATUTS).map(([k, s]) => opt(k, s.lib, f.statut)).join('')}</select>
    <select id="cm-f-site" aria-label="Visibilité">${opt('', 'Publiées et non publiées', f.site)}${
      opt('oui', 'Publiées', f.site)}${opt('non', 'Non publiées', f.site)}</select>
    <span class="cm-compte">${vues.length === n ? cmPl(n, 'chambre', 'chambres')
      : vues.length + ' sur ' + n}</span></div>`;

  const lignes = vues.map((c) => {
    const cat = cmCat(c.categorie), s = cmStatut(c), p = cmPubliee(c);
    const cap = c.capacite ? c.capacite
      : (cat ? `<span class="cm-hors">${cat.pax}</span><span class="cm-herite" title="Capacité de la catégorie">cat.</span>` : '—');
    const prix = cmPrix(c.categorie);
    return `<tr data-cm-ligne="${ech(c.id)}">
      <td><button class="cm-no" data-cm-voir="${ech(c.id)}" aria-label="Voir la chambre ${ech(c.numero)}">${ech(c.numero)}</button></td>
      <td><div class="cm-cat"><img src="${ech(cmCouverture(c).src)}" alt="" loading="lazy"><span>${ech(cmNomCat(c.categorie))}</span></div></td>
      <td class="cm-col-etage">${c.etage ? ech(c.etage) : '<span class="cm-hors">—</span>'}</td>
      <td class="num">${cap}</td>
      <td class="cm-col-lit">${c.lit ? ech(c.lit) : '<span class="cm-hors">—</span>'}</td>
      <td class="num">${prix ? FCFA(prix) + 'CFA' : '—'}</td>
      <td><span class="cm-statut cm-s-${s}">${CM_STATUTS[s].lib}</span></td>
      <td><button class="cm-bascule" role="switch" aria-checked="${p}" data-cm-publier="${ech(c.id)}"
        ${CM.occupe.has(c.id) ? 'disabled' : ''}
        aria-label="Chambre ${ech(c.numero)} publiée sur le site"><i></i>${p ? 'Publiée' : 'Masquée'}</button></td>
      <td style="text-align:right"><button class="cm-plus" data-cm-menu="${ech(c.id)}" aria-haspopup="menu"
        aria-expanded="false" aria-label="Actions pour la chambre ${ech(c.numero)}">⋯</button></td>
    </tr>`;
  }).join('');

  const vide = !n
    ? `<tr class="cm-vide-l"><td colspan="9"><b style="display:block;font-family:var(--f-t);font-weight:400;font-size:20px;color:var(--cream);margin-bottom:6px">Aucune chambre saisie</b>
        Ajoutez les chambres de l’hôtel une par une : numéro, catégorie, et le reste quand vous l’avez.<br>
        <button class="btn plein" data-cm-ajouter style="margin-top:16px">+ Ajouter une chambre</button></td></tr>`
    : `<tr class="cm-vide-l"><td colspan="9">Aucune chambre ne correspond à ces filtres.</td></tr>`;

  return `<div class="entete"><div>
      <h1 class="t">Chambres</h1>
      <p class="sous">Le référentiel des chambres de l’hôtel : ce qu’elles sont, et si le site peut les vendre.
        Le calendrier se gère dans Disponibilités.</p></div>
      <button class="btn plein" data-cm-ajouter>+ Ajouter une chambre</button></div>
    ${onglets}
    <p class="cm-explique"><b>Les chambres physiques de l’hôtel</b> — 101, B12… Chacune appartient à une
      catégorie, dont elle reprend le prix. Quand elles sont libres : voir Disponibilités.</p>
    ${avertissement()}
    ${kpis}
    ${outils}
    <div class="cm-table-cadre"><table class="cm-table">
      <thead><tr><th>N°</th><th>Catégorie</th><th class="cm-col-etage">Étage</th><th>Capacité</th>
        <th class="cm-col-lit">Lit</th><th>Prix de base</th><th>Statut</th><th>Sur le site</th>
        <th><span style="position:absolute;left:-9999px">Actions</span></th></tr></thead>
      <tbody>${lignes || vide}</tbody></table></div>`;
}

/* ── La fiche ──────────────────────────────────────────────────────── */

function cmFiche(ch) {
  const cat = cmCat(ch.categorie), s = cmStatut(ch), p = cmPubliee(ch);
  const photos = (ch.photos || []).length ? ch.photos : [];
  const i = Math.min(CM.photoVue, Math.max(0, photos.length - 1));
  const une = photos.length ? cmSrc(photos[i]) : (cat ? '/img/opt/' + cat.photo + '.jpg' : '');
  const sejours = cmSejours(ch.id);
  const prix = cmPrix(ch.categorie);
  const val = (v, rien) => (v ? v : `<span class="cm-hors">${rien || 'Non renseigné'}</span>`);

  return `<button class="btn mince cm-retour" data-cm-liste>← Toutes les chambres</button>
    <div class="cm-tete"><div>
        <div class="cm-sur">${ech(cmNomCat(ch.categorie))}${ch.etage ? ' · Étage ' + ech(ch.etage) : ''}</div>
        <h1>Chambre <span class="cm-chiffre">${ech(ch.numero)}</span></h1>
        <div class="cm-etats"><span class="cm-statut cm-s-${s}">${CM_STATUTS[s].lib}${
          ch.note && s !== 'active' ? ' — ' + ech(ch.note) : ''}</span>
          <button class="cm-bascule" role="switch" aria-checked="${p}" data-cm-publier="${ech(ch.id)}"
            aria-label="Publiée sur le site"><i></i>${p ? 'Publiée sur le site' : 'Masquée du site'}</button></div>
      </div>
      <div class="cm-actions">
        <button class="btn" data-cm-photos="${ech(ch.id)}">Photos</button>
        <button class="btn plein" data-cm-modifier="${ech(ch.id)}">Modifier</button>
        <button class="cm-plus" data-cm-menu="${ech(ch.id)}" aria-haspopup="menu" aria-expanded="false"
          aria-label="Autres actions">⋯</button>
      </div></div>
    ${avertissement()}
    <div class="cm-fiche">
      <div style="display:flex;flex-direction:column;gap:22px;min-width:0">
        <div class="cm-galerie">
          ${une ? `<img class="cm-une" src="${ech(une)}" alt="Chambre ${ech(ch.numero)}">` : ''}
          ${photos.length > 1 ? `<div class="cm-vignettes">${photos.map((ph, k) => `<button
            data-cm-vue-photo="${k}" aria-current="${k === i}" aria-label="Photo ${k + 1}">
            <img src="${ech(cmSrc(ph, true))}" alt="" loading="lazy"></button>`).join('')}</div>` : ''}
          <p class="cm-legende">${photos.length ? cmPl(photos.length, 'photo', 'photos') + ' de cette chambre'
            : 'Aucune photo propre à cette chambre : c’est celle de la catégorie.'}</p>
        </div>
        <div class="carte"><h2 class="bloc-t">Description</h2>
          ${ch.description ? `<div class="cm-texte">${ech(ch.description)}</div>`
            : '<p class="cm-hors" style="margin:0">Aucune description pour cette chambre.</p>'}</div>
        <div class="carte"><h2 class="bloc-t">Équipements</h2>
          ${(ch.equipements || []).length ? `<div class="cm-puces">${ch.equipements.map((e) => `<span>${ech(e)}</span>`).join('')}</div>`
            : '<p class="cm-hors" style="margin:0">Aucun équipement renseigné.</p>'}</div>
      </div>
      <div style="display:flex;flex-direction:column;gap:22px;min-width:0">
        <div class="carte"><h2 class="bloc-t">Caractéristiques</h2>
          <dl class="cm-carac">
            <dt>Numéro</dt><dd>${ech(ch.numero)}</dd>
            <dt>Catégorie</dt><dd>${ech(cmNomCat(ch.categorie))}</dd>
            <dt>Étage</dt><dd>${val(ech(ch.etage))}</dd>
            <dt>Capacité</dt><dd>${ch.capacite ? cmPl(ch.capacite, 'personne', 'personnes')
              : (cat ? `<span class="cm-hors">${cmPl(cat.pax, 'personne', 'personnes')} (catégorie)</span>` : val(''))}</dd>
            <dt>Lit</dt><dd>${val(ech(ch.lit))}</dd>
            <dt>Superficie</dt><dd>${ch.superficie ? ch.superficie + ' m²' : val('')}</dd>
            <dt>Prix de base</dt><dd>${prix ? FCFA(prix) + 'CFA / nuit' : '—'}<br>
              <span class="cm-hors" style="font-size:12px">prix de la catégorie</span></dd>
          </dl></div>
        <div class="cm-lien-dispo">
          <p>${sejours.length ? `<b>${cmPl(sejours.length, 'séjour à venir', 'séjours à venir')}</b> sur cette chambre. `
            : 'Aucun séjour à venir sur cette chambre. '}Les réservations et les fermetures datées se gèrent dans Disponibilités.</p>
          <button class="btn mince" data-cm-dispo>Disponibilités</button>
        </div>
        ${ch.note && s === 'active' ? `<div class="carte"><h2 class="bloc-t">Note interne</h2>
          <p class="cm-texte" style="margin:0">${ech(ch.note)}</p></div>` : ''}
      </div>
    </div>`;
}

/* ── Le formulaire ─────────────────────────────────────────────────── */

function cmNouveau(cat) {
  return { id: '', numero: '', categorie: cat || '', etage: '', capacite: '', lit: '',
    superficie: '', equipements: [], description: '', photos: [], statut: 'active',
    publie: true, note: '' };
}

function cmFormulaire() {
  const b = CM.brouillon;
  const cat = cmCat(b.categorie);
  const mal = (k) => (CM.erreurs.includes(k) ? ' mal' : '');
  const prix = cmPrix(b.categorie);
  const neuf = !b.id;
  if (neuf) return cmFormulaireAjout(b, cat, prix, mal);
  const eqs = CM_EQUIPEMENTS.concat((b.equipements || []).filter((e) => !CM_EQUIPEMENTS.includes(e)));

  return `<button class="btn mince cm-retour" data-cm-annuler>← ${neuf ? 'Toutes les chambres' : 'Chambre ' + ech(b.numero)}</button>
    <div class="entete"><div>
      <h1 class="t">${neuf ? 'Ajouter une chambre' : 'Modifier la chambre ' + ech(cmChambre(b.id) ? cmChambre(b.id).numero : b.numero)}</h1>
      <p class="sous">Seuls le numéro et la catégorie sont obligatoires. Le reste peut attendre :
        rien n’est rempli à votre place.</p></div></div>
    ${avertissement()}
    <div class="cm-form">
      <div class="cm-form-g">
        <div class="carte"><h2 class="bloc-t">Identité</h2>
          <div class="cm-trois">
            <div class="champ${mal('numero')}"><label for="cm-numero">Numéro *</label>
              <input id="cm-numero" data-cm-champ="numero" maxlength="20" value="${ech(b.numero)}" placeholder="101"></div>
            <div class="champ${mal('categorie')}"><label for="cm-categorie">Catégorie *</label>
              <select id="cm-categorie" data-cm-champ="categorie">
                <option value="">Choisir…</option>
                ${(ETAT.grille || []).map((c) => `<option value="${ech(c.slug)}" ${c.slug === b.categorie ? 'selected' : ''}>${ech(c.nom)}</option>`).join('')}
              </select></div>
            <div class="champ"><label for="cm-etage">Étage</label>
              <input id="cm-etage" data-cm-champ="etage" maxlength="20" value="${ech(b.etage)}" placeholder="1, RDC…"></div>
          </div>
        </div>

        <div class="carte"><h2 class="bloc-t">Configuration</h2>
          <div class="cm-trois">
            <div class="champ${mal('capacite')}"><label for="cm-capacite">Capacité</label>
              <div class="cm-unite"><input id="cm-capacite" data-cm-champ="capacite" inputmode="numeric" value="${ech(b.capacite)}"
                placeholder="${cat ? cat.pax : ''}"><span>pers.</span></div>
              <p class="aide">${cat ? 'Vide : celle de la catégorie, ' + cat.pax + '.' : ''}</p></div>
            <div class="champ"><label for="cm-lit">Type de lit</label>
              <input id="cm-lit" data-cm-champ="lit" maxlength="60" list="cm-lits" value="${ech(b.lit)}"
                placeholder="${cat && cat.lit ? 'Ex. ' + ech(cat.lit) : 'Queen, King…'}">
              <datalist id="cm-lits">${CM_LITS.map((l) => `<option value="${ech(l)}"></option>`).join('')}</datalist></div>
            <div class="champ${mal('superficie')}"><label for="cm-superficie">Superficie</label>
              <div class="cm-unite"><input id="cm-superficie" data-cm-champ="superficie" inputmode="numeric" value="${ech(b.superficie)}"><span>m²</span></div></div>
          </div>
          <label style="margin-top:4px">Prix de base</label>
          <div class="cm-prix"><div><b>${prix ? FCFA(prix) + 'CFA' : '—'}</b> <span class="cm-hors">/ nuit</span>
            <div class="aide" style="margin-top:2px">${cat ? 'Le prix de la catégorie ' + ech(cat.nom) + ' : le site le facture à toutes ses chambres.'
              : 'Choisissez une catégorie.'}</div></div>
            ${cat ? `<button type="button" data-cm-prix-cat="${ech(cat.slug)}">Modifier le prix de la catégorie</button>` : ''}</div>
        </div>

        <div class="carte"><h2 class="bloc-t">Équipements</h2>
          <div class="cm-sugg">${eqs.map((e) => `<button type="button" data-cm-eq="${ech(e)}"
            aria-pressed="${(b.equipements || []).includes(e)}">${ech(e)}</button>`).join('')}</div>
          <div class="cm-ajout-eq"><input id="cm-eq-autre" maxlength="40" placeholder="Autre équipement…"
            aria-label="Ajouter un équipement"><button type="button" class="btn mince" data-cm-eq-ajout>Ajouter</button></div>
        </div>

        <div class="carte"><h2 class="bloc-t">Description</h2>
          <textarea id="cm-description" data-cm-champ="description" maxlength="1200" style="min-height:140px"
            placeholder="Ce qui distingue cette chambre des autres de sa catégorie : exposition, vue, aménagement…">${ech(b.description)}</textarea>
          <p class="aide">Pour la réception. Les pages du site décrivent la catégorie, pas la chambre.</p>
        </div>

        <div class="carte" id="cm-bloc-photos"><h2 class="bloc-t">Photos</h2>
          <div class="cm-photos">
            ${(b.photos || []).map((p, k) => `<div class="cm-photo">
              <img src="${ech(cmSrc(p, true))}" alt="">
              ${k === 0 ? '<span class="cm-couv">Couverture</span>' : ''}
              <div class="cm-ph-act">
                ${k > 0 ? `<button type="button" data-cm-ph-gauche="${k}" title="Avancer" aria-label="Avancer la photo">←</button>` : ''}
                ${k < b.photos.length - 1 ? `<button type="button" data-cm-ph-droite="${k}" title="Reculer" aria-label="Reculer la photo">→</button>` : ''}
                <button type="button" data-cm-ph-oter="${k}" title="Retirer" aria-label="Retirer la photo">✕</button>
              </div></div>`).join('')}
            ${(b.photos || []).length < 12 ? `<div class="cm-photo-vide">${(b.photos || []).length
              ? 'La première photo sert de couverture.' : 'Sans photo, la chambre montre celle de sa catégorie.'}</div>` : ''}
          </div>
          <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">
            <button type="button" class="btn mince" data-cm-galerie>Choisir dans la galerie</button>
            <label class="btn mince" style="margin:0;cursor:${ETAT.stockage === 'durable' ? 'pointer' : 'not-allowed'};
              opacity:${ETAT.stockage === 'durable' ? 1 : .5}">Téléverser
              <input type="file" id="cm-fichier" accept="image/jpeg,image/png,image/webp" hidden
                ${ETAT.stockage === 'durable' ? '' : 'disabled'}></label>
            <span class="aide" id="cm-aide-photo" style="margin:0">${ETAT.stockage === 'durable'
              ? '12 photos au plus. JPEG, PNG ou WebP.' : 'Le téléversement demande le stockage durable.'}</span>
          </div>
        </div>
      </div>

      <div class="cm-form-d">
        <div class="carte"><h2 class="bloc-t">Statut</h2>
          <div class="cm-seg" role="radiogroup" aria-label="Statut">${Object.entries(CM_STATUTS).map(([k, s]) => `
            <label class="${b.statut === k ? 'on' : ''}"><input type="radio" name="cm-statut" value="${k}"
              ${b.statut === k ? 'checked' : ''}><span><span class="cm-statut cm-s-${k}">${s.lib}</span><small>${s.aide}</small></span></label>`).join('')}
          </div>
          <div class="champ" style="margin:14px 0 0"><label for="cm-note">Motif — interne</label>
            <input id="cm-note" data-cm-champ="note" maxlength="120" value="${ech(b.note)}"
              placeholder="${b.statut === 'active' ? 'Une remarque pour la réception' : 'Climatisation en panne…'}"></div>
        </div>
        <div class="carte"><h2 class="bloc-t">Sur le site</h2>
          <button type="button" class="cm-bascule" role="switch" aria-checked="${b.publie}" data-cm-publie-form>
            <i></i>${b.publie ? 'Publiée' : 'Non publiée'}</button>
          <p class="aide" style="margin-top:10px">${b.publie
            ? 'Le site peut la vendre en ligne, si elle est active et libre.'
            : 'Le site ne la vend pas. Elle reste au calendrier : la réception peut la louer elle-même.'}</p>
        </div>
      </div>
    </div>
    <div class="cm-pied-form">
      <p class="msg mal" id="cm-msg" role="alert">${CM.erreurs.length ? ech(CM.message || '') : ''}</p>
      <button class="btn" data-cm-annuler>Annuler</button>
      <button class="btn plein" data-cm-enregistrer>${neuf ? 'Ajouter la chambre' : 'Enregistrer'}</button>
    </div>`;
}

/** L'AJOUT ne demande que l'essentiel : numero, categorie, etage, capacite,
 *  statut. La categorie apporte le prix et la capacite habituelle ; le lit,
 *  les equipements, la description et les photos se completent ensuite par
 *  « Modifier ». Une chambre ajoutee est publiee : elle se vend comme ses
 *  voisines, sauf a la masquer depuis le tableau. */
function cmFormulaireAjout(b, cat, prix, mal) {
  return `<button class="btn mince cm-retour" data-cm-annuler>← Toutes les chambres</button>
    <div class="entete"><div>
      <h1 class="t">Ajouter une chambre</h1>
      <p class="sous">Une chambre physique de l’hôtel. Sa catégorie lui donne son prix ;
        le reste de la fiche se complète ensuite, par « Modifier ».</p></div></div>
    ${avertissement()}
    <div class="cm-form">
      <div class="cm-form-g">
        <div class="carte"><h2 class="bloc-t">La chambre</h2>
          <div class="cm-deux">
            <div class="champ${mal('numero')}"><label for="cm-numero">Numéro *</label>
              <input id="cm-numero" data-cm-champ="numero" maxlength="20" value="${ech(b.numero)}" placeholder="101, B12…"></div>
            <div class="champ${mal('categorie')}"><label for="cm-categorie">Catégorie *</label>
              <select id="cm-categorie" data-cm-champ="categorie">
                <option value="">Choisir…</option>
                ${(ETAT.grille || []).map((c) => `<option value="${ech(c.slug)}" ${c.slug === b.categorie ? 'selected' : ''}>${ech(c.nom)}</option>`).join('')}
              </select></div>
            <div class="champ"><label for="cm-etage">Étage</label>
              <input id="cm-etage" data-cm-champ="etage" maxlength="20" value="${ech(b.etage)}" placeholder="1, RDC…"></div>
            <div class="champ${mal('capacite')}"><label for="cm-capacite">Capacité</label>
              <div class="cm-unite"><input id="cm-capacite" data-cm-champ="capacite" inputmode="numeric" value="${ech(b.capacite)}"
                placeholder="${cat ? cat.pax : ''}"><span>pers.</span></div>
              <p class="aide">${cat ? 'Vide : celle de la catégorie, ' + cat.pax + '.' : 'Si elle diffère de celle de sa catégorie.'}</p></div>
          </div>
          <label style="margin-top:4px">Prix de base</label>
          <div class="cm-prix"><div><b>${prix ? FCFA(prix) + 'CFA' : '—'}</b> <span class="cm-hors">/ nuit</span>
            <div class="aide" style="margin-top:2px">${cat ? 'Hérité de la catégorie ' + ech(cat.nom)
              + '. Il se modifie dans l’onglet « Catégories et prix ».' : 'Choisissez une catégorie : elle donne le prix.'}</div></div></div>
        </div>
      </div>
      <div class="cm-form-d">
        <div class="carte"><h2 class="bloc-t">Statut</h2>
          <div class="cm-seg" role="radiogroup" aria-label="Statut">${Object.entries(CM_STATUTS).map(([k, s]) => `
            <label class="${b.statut === k ? 'on' : ''}"><input type="radio" name="cm-statut" value="${k}"
              ${b.statut === k ? 'checked' : ''}><span><span class="cm-statut cm-s-${k}">${s.lib}</span><small>${s.aide}</small></span></label>`).join('')}
          </div>
        </div>
      </div>
    </div>
    <div class="cm-pied-form">
      <p class="msg mal" id="cm-msg" role="alert">${CM.erreurs.length ? ech(CM.message || '') : ''}</p>
      <button class="btn" data-cm-annuler>Annuler</button>
      <button class="btn plein" data-cm-enregistrer>Ajouter la chambre</button>
    </div>`;
}

/** Recopie la saisie dans le brouillon : chaque re-rendu repart de lui. */
function cmLire() {
  const b = CM.brouillon;
  if (!b) return;
  document.querySelectorAll('[data-cm-champ]').forEach((el) => { b[el.dataset.cmChamp] = el.value; });
  const r = document.querySelector('input[name=cm-statut]:checked');
  if (r) b.statut = r.value;
}

function cmValider(b) {
  const err = [];
  if (!String(b.numero).trim()) err.push('numero');
  if (!b.categorie) err.push('categorie');
  const ent = (v, min, max) => v === '' || v == null || (/^\d+$/.test(String(v).trim())
    && +v >= min && +v <= max);
  if (!ent(b.capacite, 1, 20)) err.push('capacite');
  if (!ent(b.superficie, 1, 1000)) err.push('superficie');
  const pareil = (v) => String(v || '').trim().toLowerCase();
  const double = (ETAT.chambres || []).some((x) => x.id !== b.id && pareil(x.numero) === pareil(b.numero));
  if (double) err.push('numero');
  CM.message = double ? 'La chambre ' + String(b.numero).trim() + ' existe déjà.'
    : err.includes('numero') || err.includes('categorie') ? 'Le numéro et la catégorie sont obligatoires.'
    : err.includes('capacite') ? 'La capacité est un nombre de personnes, de 1 à 20.'
    : err.includes('superficie') ? 'La superficie s’écrit en mètres carrés, sans virgule.' : '';
  return err;
}

async function cmEnregistrer() {
  cmLire();
  const b = CM.brouillon;
  CM.erreurs = cmValider(b);
  if (CM.erreurs.length) { rendre(); return; }
  const btn = document.querySelector('[data-cm-enregistrer]');
  if (btn) { btn.disabled = true; btn.textContent = 'Enregistrement…'; }
  const entree = Object.assign({}, b, {
    numero: String(b.numero).trim(),
    capacite: b.capacite === '' ? null : Number(b.capacite),
    superficie: b.superficie === '' ? null : Number(b.superficie),
  });
  if (!entree.id) delete entree.id;
  const r = await cmEcrire(entree);
  if (!r.ok) {
    CM.erreurs = r.champs && r.champs.includes('numéro') ? ['numero'] : ['_'];
    CM.message = r.message || 'Rien n’a été enregistré.';
    rendre();
    return;
  }
  CM.brouillon = null; CM.erreurs = []; CM.photoVue = 0;
  if (b.id) {
    CM.mode = 'voir'; CM.id = r.entree.id;
    rendre(); window.scrollTo(0, 0);
    notifier('Chambre ' + r.entree.numero + ' enregistrée');
    return;
  }
  /* Une chambre AJOUTEE se montre dans le tableau, a sa place, mise en
     evidence. Les filtres sont leves : elle ne doit pas s'y cacher. */
  CM.mode = 'liste'; CM.id = null;
  CM.filtres = { q: '', cat: '', statut: '', site: '' };
  rendre();
  const ligne = document.querySelector('tr[data-cm-ligne="' + r.entree.id + '"]');
  if (ligne) { ligne.classList.add('cm-neuve'); ligne.scrollIntoView({ block: 'center' }); }
  notifier('Chambre ' + r.entree.numero + ' ajoutée');
}

/** Ecrit une chambre, et met l'etat local a jour sur la reponse. */
async function cmEcrire(entree) {
  const r = await appel('enregistrer', { type: 'chambre', entree });
  if (r.ok) {
    const i = ETAT.chambres.findIndex((x) => x.id === r.entree.id);
    if (i >= 0) ETAT.chambres[i] = r.entree; else ETAT.chambres.push(r.entree);
  }
  return r;
}

/* ── Les fenetres ──────────────────────────────────────────────────── */

/** Une confirmation. Rend une promesse : true si l'on confirme. `champ`
 *  ajoute un motif facultatif, rendu dans la promesse ({ ok, motif }). */
function cmDemander({ titre, texte, attention, bouton, danger, champ }) {
  return new Promise((fin) => {
    const v = document.createElement('div');
    v.className = 'cm-voile';
    v.innerHTML = `<div class="cm-fenetre${danger ? ' cm-danger' : ''}" role="alertdialog" aria-modal="true"
        aria-labelledby="cm-f-t" aria-describedby="cm-f-p">
      <h2 id="cm-f-t">${titre}</h2><p id="cm-f-p">${texte}</p>
      ${attention ? `<p class="cm-attention">${attention}</p>` : ''}
      ${champ ? `<div class="champ" style="margin:14px 0 0"><label for="cm-f-motif">${champ}</label>
        <input id="cm-f-motif" maxlength="120"></div>` : ''}
      <div class="cm-boutons"><button class="btn" data-non>Annuler</button>
        <button class="btn ${danger ? 'cm-rouge' : 'plein'}" data-oui>${bouton}</button></div></div>`;
    const avant = document.activeElement;
    const fermer = (ok) => {
      const motif = champ ? (v.querySelector('#cm-f-motif').value || '').trim() : '';
      v.remove(); document.removeEventListener('keydown', clavier, true);
      if (avant && avant.focus) avant.focus();
      fin(champ ? { ok, motif } : ok);
    };
    const clavier = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); fermer(false); }
      if (e.key === 'Tab') {   // le focus reste dans la fenetre
        const f = [...v.querySelectorAll('button,input')];
        const i = f.indexOf(document.activeElement);
        if (e.shiftKey && i <= 0) { e.preventDefault(); f[f.length - 1].focus(); }
        else if (!e.shiftKey && i === f.length - 1) { e.preventDefault(); f[0].focus(); }
      }
    };
    v.addEventListener('click', (e) => {
      if (e.target === v || e.target.closest('[data-non]')) fermer(false);
      else if (e.target.closest('[data-oui]')) fermer(true);
    });
    document.addEventListener('keydown', clavier, true);
    document.body.appendChild(v);
    (v.querySelector('#cm-f-motif') || v.querySelector(danger ? '[data-non]' : '[data-oui]')).focus();
  });
}

/** Le choix de photos parmi celles du site. */
function cmGalerie() {
  const b = CM.brouillon;
  const choisies = new Set(b.photos || []);
  const cat = cmCat(b.categorie);
  /* Les photos de la categorie d'abord : ce sont les plus probables. */
  const toutes = (ETAT.images || []).slice();
  if (cat) {
    const racine = cat.photo.replace(/-640$/, '');
    toutes.sort((x, y) => (y === racine) - (x === racine));
  }
  const v = document.createElement('div');
  v.className = 'cm-voile';
  v.innerHTML = `<div class="cm-fenetre cm-large-f" role="dialog" aria-modal="true" aria-labelledby="cm-g-t">
    <h2 id="cm-g-t">Photos du site</h2>
    <p>Choisissez celles qui montrent cette chambre. Elles s’ajoutent dans l’ordre du clic.</p>
    <div class="cm-choix">${toutes.map((n) => `<button type="button" data-g="${ech(n)}" aria-pressed="${choisies.has(n)}"
      title="${ech(n)}"><img src="/img/opt/${ech(n)}.jpg" alt="${ech(n)}" loading="lazy"></button>`).join('')}</div>
    <div class="cm-boutons"><button class="btn" data-non>Annuler</button><button class="btn plein" data-oui>Valider</button></div></div>`;
  const ordre = (b.photos || []).slice();
  const fermer = (ok) => {
    v.remove(); document.removeEventListener('keydown', clavier, true);
    if (ok) { cmLire(); b.photos = ordre.slice(0, 12); rendre(); document.getElementById('cm-bloc-photos').scrollIntoView({ block: 'start' }); }
  };
  const clavier = (e) => { if (e.key === 'Escape') { e.preventDefault(); fermer(false); } };
  v.addEventListener('click', (e) => {
    const g = e.target.closest('[data-g]');
    if (g) {
      const n = g.dataset.g, i = ordre.indexOf(n);
      if (i >= 0) ordre.splice(i, 1); else if (ordre.length < 12) ordre.push(n);
      g.setAttribute('aria-pressed', String(ordre.includes(n)));
      return;
    }
    if (e.target === v || e.target.closest('[data-non]')) fermer(false);
    else if (e.target.closest('[data-oui]')) fermer(true);
  });
  document.addEventListener('keydown', clavier, true);
  document.body.appendChild(v);
  v.querySelector('[data-oui]').focus();
}

/* ── Le menu « ⋯ » ─────────────────────────────────────────────────── */

function cmFermerMenu() {
  const m = document.getElementById('cm-menu');
  if (m) m.remove();
  document.querySelectorAll('[data-cm-menu][aria-expanded="true"]').forEach((b) => b.setAttribute('aria-expanded', 'false'));
}

function cmOuvrirMenu(bouton) {
  const ouvert = bouton.getAttribute('aria-expanded') === 'true';
  cmFermerMenu();
  if (ouvert) return;
  const ch = cmChambre(bouton.dataset.cmMenu);
  if (!ch) return;
  const s = cmStatut(ch), p = cmPubliee(ch);
  const m = document.createElement('div');
  m.id = 'cm-menu'; m.className = 'cm-menu'; m.setAttribute('role', 'menu');
  const it = (act, ico, lib, danger) => `<button role="menuitem" data-cm-act="${act}" data-id="${ech(ch.id)}"
    ${danger ? 'class="cm-danger"' : ''}><i>${ico}</i>${lib}</button>`;
  m.innerHTML = it('voir', '◎', 'Voir la fiche') + it('modifier', '✎', 'Modifier') + it('photos', '▣', 'Photos')
    + '<hr>' + it('publier', p ? '◌' : '●', p ? 'Dépublier du site' : 'Publier sur le site')
    + (s === 'maintenance' ? it('activer', '↺', 'Fin de maintenance') : it('maintenance', '⚒', 'Mettre en maintenance'))
    + (s === 'hors-service' ? it('activer', '↺', 'Réactiver') : it('desactiver', '⊘', 'Désactiver'))
    + '<hr>' + it('supprimer', '✕', 'Supprimer', true);
  document.body.appendChild(m);
  const r = bouton.getBoundingClientRect();
  const h = m.offsetHeight, w = m.offsetWidth;
  const bas = r.bottom + 6 + h > window.innerHeight ? r.top - h - 6 : r.bottom + 6;
  m.style.top = Math.max(8, bas) + 'px';
  m.style.left = Math.max(8, Math.min(r.right - w, window.innerWidth - w - 8)) + 'px';
  bouton.setAttribute('aria-expanded', 'true');
  m.querySelector('button').focus();
  m.addEventListener('keydown', (e) => {
    const f = [...m.querySelectorAll('button')], i = f.indexOf(document.activeElement);
    if (e.key === 'ArrowDown') { e.preventDefault(); f[(i + 1) % f.length].focus(); }
    if (e.key === 'ArrowUp') { e.preventDefault(); f[(i - 1 + f.length) % f.length].focus(); }
    if (e.key === 'Escape' || e.key === 'Tab') { e.preventDefault(); cmFermerMenu(); bouton.focus(); }
  });
}

/* ── Les actions ───────────────────────────────────────────────────── */

async function cmPublier(id) {
  const ch = cmChambre(id);
  if (!ch || CM.occupe.has(id)) return;
  CM.occupe.add(id); rendre();
  const r = await cmEcrire(Object.assign({}, ch, { publie: !cmPubliee(ch) }));
  CM.occupe.delete(id); rendre();
  if (!r.ok) return notifier(r.message || 'Rien n’a été enregistré', true);
  notifier('Chambre ' + ch.numero + (r.entree.publie ? ' publiée sur le site' : ' retirée du site'));
}

async function cmChangerStatut(id, statut) {
  const ch = cmChambre(id);
  if (!ch) return;
  const sej = cmSejours(id);
  const att = sej.length ? cmPl(sej.length, 'séjour à venir reste posé', 'séjours à venir restent posés')
    + ' sur cette chambre. Ce changement ne les annule pas : déplacez-les dans Disponibilités si besoin.' : '';
  let motif = ch.note || '';
  if (statut !== 'active') {
    const q = statut === 'maintenance'
      ? { titre: 'Mettre la chambre ' + ech(ch.numero) + ' en maintenance ?',
          texte: 'Le site cesse de la vendre jusqu’à ce que vous la remettiez en service.',
          bouton: 'Mettre en maintenance' }
      : { titre: 'Désactiver la chambre ' + ech(ch.numero) + ' ?',
          texte: 'Elle passe hors service : le site ne la vend plus, jusqu’à nouvel ordre. '
            + 'Elle reste dans le référentiel, et se réactive d’un clic.',
          bouton: 'Désactiver', danger: true };
    const rep = await cmDemander(Object.assign(q, { attention: att, champ: 'Motif — interne, facultatif' }));
    if (!rep.ok) return;
    motif = rep.motif || '';
  }
  const r = await cmEcrire(Object.assign({}, ch, { statut, note: statut === 'active' ? '' : motif }));
  rendre();
  if (!r.ok) return notifier(r.message || 'Rien n’a été enregistré', true);
  notifier('Chambre ' + ch.numero + ' : ' + CM_STATUTS[statut].lib.toLowerCase());
}

async function cmSupprimer(id) {
  const ch = cmChambre(id);
  if (!ch) return;
  const sej = cmSejours(id);
  const ok = await cmDemander({
    titre: 'Supprimer la chambre ' + ech(ch.numero) + ' ?',
    texte: 'Elle disparaît du référentiel et du calendrier. Cette action ne s’annule pas.',
    attention: sej.length ? cmPl(sej.length, 'séjour à venir est posé', 'séjours à venir sont posés')
      + ' sur elle : la suppression sera refusée tant qu’ils y sont. Pour une panne, préférez « Désactiver ».'
      : 'Pour une panne ou des travaux, préférez « Mettre en maintenance » ou « Désactiver » : la chambre reste chez vous.',
    bouton: 'Supprimer définitivement', danger: true });
  if (!ok) return;
  const r = await appel('supprimer', { type: 'chambre', id });
  if (!r.ok) return notifier(r.message || 'La chambre n’a pas été supprimée', true);
  ETAT.chambres = ETAT.chambres.filter((x) => x.id !== id);
  cmReinit(); rendre();
  notifier('Chambre ' + ch.numero + ' supprimée');
}

function cmOuvrirForm(id, versPhotos) {
  const ch = id ? cmChambre(id) : null;
  CM.brouillon = ch ? Object.assign(cmNouveau(), ch, {
    statut: cmStatut(ch), publie: cmPubliee(ch),
    capacite: ch.capacite == null ? '' : String(ch.capacite),
    superficie: ch.superficie == null ? '' : String(ch.superficie),
    equipements: (ch.equipements || []).slice(), photos: (ch.photos || []).slice(),
  }) : cmNouveau(CM.filtres.cat);
  CM.mode = 'form'; CM.id = id || null; CM.erreurs = [];
  rendre();
  if (versPhotos) { const p = document.getElementById('cm-bloc-photos'); if (p) p.scrollIntoView({ block: 'start' }); }
  else { window.scrollTo(0, 0); const n = document.getElementById('cm-numero'); if (n && !id) n.focus(); }
}

/** Ouvre une chambre depuis un autre ecran (Disponibilites). */
function cmAller(id, mode) {
  VUE = 'chambres';
  CM.onglet = 'inventaire';
  document.querySelectorAll('#menu button').forEach((x) => x.classList.toggle('on', x.dataset.v === 'chambres'));
  if (mode === 'form') { cmOuvrirForm(id); return; }
  CM.mode = 'voir'; CM.id = id; CM.photoVue = 0;
  rendre(); window.scrollTo(0, 0);
}

document.addEventListener('click', async (e) => {
  const q = (s) => e.target.closest(s);
  let b;
  if (!q('#cm-menu') && !q('[data-cm-menu]')) cmFermerMenu();
  if ((b = q('[data-cm-ouvrir]'))) {   // depuis Disponibilites
    if (typeof DSP !== 'undefined' && DSP.tiroir) { DSP.tiroir = null; if (typeof rendreTiroir === 'function') rendreTiroir(); }
    cmAller(b.dataset.cmOuvrir); return;
  }
  if (VUE !== 'chambres') return;
  if ((b = q('[data-cm-onglet]'))) { CM.onglet = b.dataset.cmOnglet; cmReinit(); CAT_OUVERTE = null; rendre(); return; }
  if ((b = q('[data-cm-menu]'))) { cmOuvrirMenu(b); return; }
  if ((b = q('[data-cm-act]'))) {
    const id = b.dataset.id, a = b.dataset.cmAct;
    cmFermerMenu();
    if (a === 'voir') { CM.mode = 'voir'; CM.id = id; CM.photoVue = 0; rendre(); window.scrollTo(0, 0); }
    else if (a === 'modifier') cmOuvrirForm(id);
    else if (a === 'photos') cmOuvrirForm(id, true);
    else if (a === 'publier') cmPublier(id);
    else if (a === 'maintenance') cmChangerStatut(id, 'maintenance');
    else if (a === 'desactiver') cmChangerStatut(id, 'hors-service');
    else if (a === 'activer') cmChangerStatut(id, 'active');
    else if (a === 'supprimer') cmSupprimer(id);
    return;
  }
  if ((b = q('[data-cm-publier]'))) { cmPublier(b.dataset.cmPublier); return; }
  if ((b = q('[data-cm-voir]'))) { CM.mode = 'voir'; CM.id = b.dataset.cmVoir; CM.photoVue = 0; rendre(); window.scrollTo(0, 0); return; }
  if (q('[data-cm-ajouter]')) { cmOuvrirForm(null); return; }
  if ((b = q('[data-cm-modifier]'))) { cmOuvrirForm(b.dataset.cmModifier); return; }
  if ((b = q('[data-cm-photos]'))) { cmOuvrirForm(b.dataset.cmPhotos, true); return; }
  if ((b = q('[data-cm-vue-photo]'))) { CM.photoVue = +b.dataset.cmVuePhoto; rendre(); return; }
  if (q('[data-cm-liste]')) { cmReinit(); rendre(); return; }
  if (q('[data-cm-dispo]')) { const m = document.querySelector('#menu button[data-v="disponibilites"]'); if (m) m.click(); return; }
  if (q('[data-cm-annuler]')) {
    const retour = CM.brouillon && CM.brouillon.id;
    CM.brouillon = null; CM.erreurs = [];
    if (retour) { CM.mode = 'voir'; CM.id = retour; } else cmReinit();
    rendre(); window.scrollTo(0, 0); return;
  }
  if (q('[data-cm-enregistrer]')) { cmEnregistrer(); return; }
  if ((b = q('[data-cm-prix-cat]'))) {
    CM.onglet = 'categories'; cmReinit(); CAT_OUVERTE = b.dataset.cmPrixCat; rendre(); window.scrollTo(0, 0); return;
  }
  /* Le formulaire : tout geste passe par le brouillon, puis re-rendu. */
  if (!CM.brouillon) return;
  if ((b = q('[data-cm-eq]'))) {
    cmLire();
    const eq = CM.brouillon.equipements, v = b.dataset.cmEq, i = eq.indexOf(v);
    if (i >= 0) eq.splice(i, 1); else eq.push(v);
    b.setAttribute('aria-pressed', String(i < 0));
    return;
  }
  if (q('[data-cm-eq-ajout]')) {
    const inp = document.getElementById('cm-eq-autre');
    const v = (inp.value || '').trim().slice(0, 40);
    if (!v) { inp.focus(); return; }
    cmLire();
    if (!CM.brouillon.equipements.some((x) => x.toLowerCase() === v.toLowerCase())) CM.brouillon.equipements.push(v);
    rendre(); document.getElementById('cm-eq-autre').focus(); return;
  }
  if (q('[data-cm-publie-form]')) { cmLire(); CM.brouillon.publie = !CM.brouillon.publie; rendre(); return; }
  if (q('[data-cm-galerie]')) { cmLire(); cmGalerie(); return; }
  const ph = CM.brouillon.photos;
  if ((b = q('[data-cm-ph-oter]'))) { cmLire(); ph.splice(+b.dataset.cmPhOter, 1); rendre(); return; }
  if ((b = q('[data-cm-ph-gauche]'))) { cmLire(); const k = +b.dataset.cmPhGauche; [ph[k - 1], ph[k]] = [ph[k], ph[k - 1]]; rendre(); return; }
  if ((b = q('[data-cm-ph-droite]'))) { cmLire(); const k = +b.dataset.cmPhDroite; [ph[k + 1], ph[k]] = [ph[k], ph[k + 1]]; rendre(); return; }
});

/* Le statut se choisit par des boutons radio : on repeint l'encadre. */
document.addEventListener('change', async (e) => {
  if (VUE !== 'chambres') return;
  if (e.target.name === 'cm-statut') { cmLire(); rendre(); return; }
  if (e.target.id === 'cm-f-cat' || e.target.id === 'cm-f-statut' || e.target.id === 'cm-f-site') {
    CM.filtres[{ 'cm-f-cat': 'cat', 'cm-f-statut': 'statut', 'cm-f-site': 'site' }[e.target.id]] = e.target.value;
    rendre(); return;
  }
  if (e.target.id === 'cm-categorie') { cmLire(); rendre(); return; }
  if (e.target.id === 'cm-fichier') { cmTeleverser(e.target); }
});

document.addEventListener('input', (e) => {
  if (VUE !== 'chambres') return;
  /* Un champ signale se corrige : l'alerte s'efface avec la faute. */
  const champ = e.target.closest('.champ.mal');
  if (champ) {
    champ.classList.remove('mal');
    CM.erreurs = CM.erreurs.filter((k) => k !== e.target.dataset.cmChamp);
    if (!document.querySelector('.cm-form .champ.mal')) { const m = document.getElementById('cm-msg'); if (m) m.textContent = ''; }
  }
  if (e.target.id !== 'cm-q') return;
  CM.filtres.q = e.target.value;
  const pos = e.target.selectionStart;
  rendre();
  const n = document.getElementById('cm-q');
  if (n) { n.focus(); n.setSelectionRange(pos, pos); }
});

document.addEventListener('keydown', (e) => {
  if (VUE === 'chambres' && e.key === 'Enter' && e.target.id === 'cm-eq-autre') {
    e.preventDefault(); document.querySelector('[data-cm-eq-ajout]').click();
  }
});
window.addEventListener('resize', cmFermerMenu);
window.addEventListener('scroll', cmFermerMenu, true);

async function cmTeleverser(input) {
  const f = input.files && input.files[0];
  const aide = document.getElementById('cm-aide-photo');
  const dire = (t, mal) => { if (aide) { aide.textContent = t; aide.style.color = mal ? 'var(--err)' : ''; } };
  if (!f) return;
  if ((CM.brouillon.photos || []).length >= 12) return dire('12 photos au plus.', true);
  if (f.size > 4 * 1024 * 1024) return dire('Photo trop lourde : 4 Mo au maximum.', true);
  dire('Envoi en cours…');
  const donnee = await new Promise((r) => { const l = new FileReader(); l.onload = () => r(l.result); l.readAsDataURL(f); });
  const im = await new Promise((r) => { const i = new Image(); i.onload = () => r(i); i.onerror = () => r(null); i.src = donnee; });
  const envoi = alleger(im, donnee, f.size);
  const rep = await appel('televerser', { fichier: envoi });
  if (!rep.ok) return dire(rep.message || 'Le dépôt a échoué.', true);
  cmLire();
  CM.brouillon.photos.push(rep.url);
  rendre();
  document.getElementById('cm-bloc-photos').scrollIntoView({ block: 'start' });
  const a2 = document.getElementById('cm-aide-photo');
  if (a2) a2.textContent = 'Photo ajoutée. Enregistrez la chambre pour la garder.';
}
