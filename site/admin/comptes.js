/* ──────────────────────────────────────────────────────────────────────
   Module « Comptes » — qui entre, avec quel profil, et ce qu'il a fait.

   Trois ecrans :
   - Utilisateurs (administrateurs) : creer un compte, changer un profil,
     desactiver, reinitialiser un mot de passe, supprimer ;
   - Journal d'activite (administrateurs) : connexions et modifications ;
   - Mon compte (tout le monde) : changer son mot de passe.

   Et l'ecran de la premiere connexion, qui remplace le mot de passe
   provisoire avant de laisser voir quoi que ce soit.

   CE QUI PROTEGE, C'EST LE SERVEUR (api/_comptes.js). Ce fichier n'affiche
   que ce que le profil ouvre, pour ne pas laisser cliquer sur des boutons
   qui seraient refuses — rien de plus.
   ────────────────────────────────────────────────────────────────────── */

const CP = {
  comptes: null,          // null : pas encore charges
  roles: {},
  journal: null,
  enCours: false,
  ajout: false,           // le formulaire d'ajout est ouvert
  cree: null,             // { compte, provisoire, reinit } : a montrer UNE fois
  erreur: '',
  filtre: '',             // journal : l'id d'une personne, ou ''
  cherche: '',
};

/** Le profil connecte a-t-il ce droit ? (affichage seulement) */
function peut(droit) {
  return !!(ETAT.moi && ETAT.moi.droits && ETAT.moi.droits.includes(droit));
}

const ROLES_LOCAUX = {
  admin: { nom: 'Administrateur', resume: 'Tout, plus les comptes, les prix et les paramètres.' },
  reception: { nom: 'Réception', resume: 'Disponibilités, réservations et chambres.' },
  communication: { nom: 'Communication', resume: 'Événements, promotions, campagnes, recrutement et affiches.' },
  lecture: { nom: 'Lecture seule', resume: 'Consulte tout, ne modifie rien.' },
};
const roles = () => (Object.keys(CP.roles).length ? CP.roles : ROLES_LOCAUX);

/* ── Le menu selon le profil ─────────────────────────────────────────── */
function appliquerProfil() {
  const moi = ETAT.moi;
  if (!moi) return;
  const vues = moi.vues || [];
  const menu = $('#menu');
  [...menu.querySelectorAll('button[data-v]')].forEach((b) => { b.hidden = !vues.includes(b.dataset.v); });
  /* Un intertitre sans aucune rubrique visible sous lui disparait aussi. */
  let titre = null, vu = false;
  const fermer = () => { if (titre) titre.hidden = !vu; };
  [...menu.children].forEach((el) => {
    if (el.tagName === 'H2' && el.id !== 'moi-nom') { fermer(); titre = el; vu = false; }
    else if (el.tagName === 'H2') { fermer(); titre = null; }
    else if (el.matches('button[data-v]') && !el.hidden) vu = true;
  });
  fermer();
  $('#moi-nom').textContent = moi.nom + ' · ' + moi.profil;
  document.body.classList.toggle('cp-ro', !(moi.droits || []).length);
  if (!vues.includes(VUE)) {
    VUE = 'bord';
    [...menu.querySelectorAll('button[data-v]')].forEach((x) => x.classList.toggle('on', x.dataset.v === VUE));
  }
}

/* ── Premiere connexion ──────────────────────────────────────────────── */
function montrerPremier() {
  $('#porte').style.display = 'grid';
  $('#cadre').classList.remove('on');
  $('#fporte').hidden = true;
  $('#fpremier').hidden = false;
  $('#premier-qui').textContent = 'Bonjour ' + ETAT.moi.nom + '. Le mot de passe qu’on vous a '
    + 'transmis est provisoire : remplacez-le par le vôtre. Personne d’autre ne le connaîtra.';
  $('#errpremier').textContent = '';
  setTimeout(() => $('#p-ancien').focus(), 50);
}

$('#fpremier').addEventListener('submit', async (e) => {
  e.preventDefault();
  const err = $('#errpremier');
  err.textContent = '';
  if ($('#p-nouveau').value !== $('#p-confirme').value) {
    err.textContent = 'Les deux saisies du nouveau mot de passe ne sont pas identiques.';
    return $('#p-confirme').focus();
  }
  const r = await appel('mot-de-passe', { ancien: $('#p-ancien').value, nouveau: $('#p-nouveau').value });
  if (!r.ok) { err.textContent = r.message || 'Le changement a échoué.'; return; }
  ['#p-ancien', '#p-nouveau', '#p-confirme'].forEach((s) => { $(s).value = ''; });
  $('#fpremier').hidden = true;
  $('#fporte').hidden = false;
  montrerCadre();
});

$('#sortir').addEventListener('click', () => {
  ETAT.moi = null;
  Object.assign(CP, { comptes: null, journal: null, cree: null, ajout: false, erreur: '' });
  document.body.classList.remove('cp-ro');
});

/* ── Outils ──────────────────────────────────────────────────────────── */
const quand = (iso) => (iso ? new Date(iso).toLocaleString('fr-FR',
  { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '');
const heure = (iso) => new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
const jourDe = (iso) => new Date(iso).toLocaleDateString('fr-FR',
  { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).replace(/(^|\s)1(\s)/, '$11er$2');

/* Chaque ecran charge ses donnees a son premier affichage, puis se redessine. */
async function cpApres() {
  if (CP.enCours) return;
  if (VUE === 'utilisateurs' && CP.comptes === null) {
    CP.enCours = true;
    const r = await appel('comptes').catch(() => ({}));
    CP.enCours = false;
    CP.comptes = r.ok ? r.comptes : [];
    CP.roles = r.roles || {};
    CP.erreur = r.ok ? '' : (r.message || 'La liste des comptes n’a pas pu être lue.');
    if (VUE === 'utilisateurs') rendre();
  } else if (VUE === 'journal' && CP.journal === null) {
    CP.enCours = true;
    const r = await appel('journal').catch(() => ({}));
    CP.enCours = false;
    CP.journal = r.ok ? r.journal : [];
    CP.erreur = r.ok ? '' : (r.message || 'Le journal n’a pas pu être lu.');
    if (VUE === 'journal') rendre();
  }
}

/* ── Utilisateurs ────────────────────────────────────────────────────── */
function optionsProfil(choisi) {
  return Object.entries(roles()).map(([k, r]) =>
    `<option value="${k}"${k === choisi ? ' selected' : ''}>${ech(r.nom)}</option>`).join('');
}

/* Le message tout pret a transmettre. On ne l'envoie pas nous-memes : pas
   d'expediteur e-mail verifie tant que rien n'est signe, et un mot de passe
   se transmet de toute facon mieux de vive voix ou en message direct. */
function messageAcces(c, mdp) {
  return 'Bonjour ' + c.nom + ',\n\nVotre accès à l’administration du site de l’Hôtel Evannath '
    + 'est ouvert (profil ' + (roles()[c.role] || {}).nom + ').\n\n'
    + 'Adresse : ' + location.origin + '/admin\n'
    + 'E-mail : ' + c.courriel + '\n'
    + 'Mot de passe provisoire : ' + mdp + '\n\n'
    + 'À la première connexion, il vous sera demandé de choisir votre propre mot de passe.';
}

function carteCree() {
  const { compte: c, provisoire: mdp, reinit } = CP.cree;
  const msg = messageAcces(c, mdp);
  return `<div class="carte cp-cree" role="status">
    <h2 class="bloc-t">${reinit ? 'Mot de passe réinitialisé' : 'Compte créé'} — ${ech(c.nom)}</h2>
    <p class="aide" style="margin-bottom:14px">Mot de passe provisoire, affiché <b>une seule fois</b>.
      Transmettez-le de vive voix ou par message direct ; ${ech(c.nom)} le remplacera à sa première
      connexion.</p>
    <div class="cp-mdp"><code>${ech(mdp)}</code>
      <button type="button" class="btn mince cp-garde" data-cp-copier="${ech(mdp)}">Copier</button></div>
    <details class="cp-message"><summary>Message prêt à envoyer</summary>
      <pre>${ech(msg)}</pre>
      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px">
        <button type="button" class="btn mince cp-garde" data-cp-copier="${ech(msg)}">Copier le message</button>
        <a class="btn mince" href="https://wa.me/?text=${encodeURIComponent(msg)}" target="_blank"
          rel="noopener">Ouvrir dans WhatsApp</a>
      </div></details>
    <button type="button" class="btn mince cp-garde" data-cp-fermer-cree style="margin-top:16px">C’est transmis</button>
  </div>`;
}

function vueUtilisateurs() {
  const moi = ETAT.moi || {};
  const tete = `<div class="entete"><div>
      <h1 class="t">Utilisateurs</h1>
      <p class="sous">Qui peut entrer dans l’administration, et avec quel profil.</p></div>
      ${CP.ajout ? '' : '<button class="btn plein" data-cp-ajouter>+ Ajouter une personne</button>'}</div>`;
  if (CP.comptes === null) return tete + '<p class="aide">Chargement…</p>';

  const ajout = !CP.ajout ? '' : `<form class="carte" id="cp-form-ajout" novalidate>
      <h2 class="bloc-t">Nouvelle personne</h2>
      <div class="duo">
        <div class="champ"><label for="cp-nom">Nom</label>
          <input id="cp-nom" autocomplete="off" maxlength="80" required></div>
        <div class="champ"><label for="cp-courriel">Adresse e-mail</label>
          <input id="cp-courriel" type="email" autocomplete="off" autocapitalize="none" spellcheck="false" required></div>
      </div>
      <fieldset class="cp-profils"><legend>Profil</legend>
        ${Object.entries(roles()).map(([k, r], i) => `<label class="cp-profil">
          <input type="radio" name="cp-role" value="${k}"${(i === 1) ? ' checked' : ''}>
          <span><b>${ech(r.nom)}</b><small>${ech(r.resume)}</small></span></label>`).join('')}
      </fieldset>
      <p class="aide">Un mot de passe provisoire sera créé, à transmettre à la personne.</p>
      <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:16px">
        <button class="btn plein">Créer le compte</button>
        <button type="button" class="btn mince" data-cp-annuler>Annuler</button>
        <p class="msg mal" id="cp-msg-ajout" role="alert"></p>
      </div>
    </form>`;

  const lignes = CP.comptes.slice().sort((a, b) => a.nom.localeCompare(b.nom, 'fr')).map((c) => {
    const soi = c.id === moi.id;
    return `<tr class="${c.actif ? '' : 'cp-inactif'}">
      <td><b>${ech(c.nom)}</b>${soi ? ' <span class="cp-badge">vous</span>' : ''}
        <span class="cp-sous">${ech(c.courriel)}</span></td>
      <td>${soi ? ech((roles()[c.role] || {}).nom)
        : `<select data-cp-role="${c.id}" aria-label="Profil de ${ech(c.nom)}">${optionsProfil(c.role)}</select>`}</td>
      <td>${!c.actif ? '<span class="etat fini">Désactivé</span>'
        : c.provisoire ? '<span class="etat attend">À activer</span>'
        : '<span class="etat vif">Actif</span>'}</td>
      <td class="cp-sous">${c.derniere ? quand(c.derniere) : 'Jamais connecté'}</td>
      <td class="cp-actions">${soi ? '' : `
        <button type="button" class="btn mince" data-cp-reinit="${c.id}" title="Créer un nouveau mot de passe provisoire">Mot de passe</button>
        <button type="button" class="btn mince" data-cp-actif="${c.id}">${c.actif ? 'Désactiver' : 'Réactiver'}</button>
        <button type="button" class="btn mince danger" data-cp-suppr="${c.id}">Supprimer</button>`}</td>
    </tr>`;
  }).join('');

  const liste = CP.comptes.length ? `<div class="carte cp-table-zone"><table class="cp-table">
      <thead><tr><th>Personne</th><th>Profil</th><th>État</th><th>Dernière connexion</th><th><span class="cp-vh">Actions</span></th></tr></thead>
      <tbody>${lignes}</tbody></table>
      <p class="msg mal" id="cp-msg-liste" role="alert" style="margin-top:12px"></p></div>`
    : `<div class="carte"><p><b>Aucun compte pour l’instant.</b></p>
       <p class="aide">Vous êtes entré par l’accès de secours. Créez d’abord votre propre compte
       Administrateur, puis ceux de l’équipe.</p></div>`;

  const profils = `<div class="carte"><h2 class="bloc-t">Les profils</h2>
      ${Object.entries(roles()).map(([, r]) => `<div class="ligne" style="margin:0 0 8px"><div class="txt">
        <b>${ech(r.nom)}</b><span>${ech(r.resume)}</span></div></div>`).join('')}
      <p class="aide" style="margin-top:12px">Changer le profil d’une personne, la désactiver ou lui
      donner un nouveau mot de passe ferme aussitôt ses sessions ouvertes. Il reste toujours au moins
      un administrateur actif.</p>
      <p class="aide">Accès de secours : e-mail vide et mot de passe principal (ADMIN_MDP, dans Vercel).
      Il sert à créer le premier compte, ou à rentrer si le dernier administrateur a perdu le sien.</p></div>`;

  return tete + (CP.erreur ? `<div class="alerte"><b>Comptes indisponibles</b><span>${ech(CP.erreur)}</span></div>` : '')
    + (CP.cree ? carteCree() : '') + ajout + liste + profils;
}

/* ── Journal ─────────────────────────────────────────────────────────── */
function vueJournal() {
  const tete = `<div class="entete"><div>
      <h1 class="t">Journal d’activité</h1>
      <p class="sous">Qui a fait quoi, et quand. Les 90 derniers jours.</p></div>
      <button class="btn mince" data-cp-rafraichir>Actualiser</button></div>`;
  if (CP.journal === null) return tete + '<p class="aide">Chargement…</p>';
  const personnes = [...new Map(CP.journal.map((l) => [l.u, l.n])).entries()]
    .sort((a, b) => String(a[1]).localeCompare(String(b[1]), 'fr'));
  const q = CP.cherche.trim().toLowerCase();
  const vues = CP.journal.filter((l) => (!CP.filtre || l.u === CP.filtre)
    && (!q || (l.x + ' ' + l.n).toLowerCase().includes(q)));
  let jour = '', html = '';
  vues.slice(0, 400).forEach((l) => {
    const j = jourDe(l.t);
    if (j !== jour) { html += `<h3 class="cp-jour">${ech(j)}</h3>`; jour = j; }
    html += `<div class="cp-entree"><time datetime="${ech(l.t)}">${heure(l.t)}</time>
      <span><b>${ech(l.n)}</b> — ${ech(l.x)}</span></div>`;
  });
  return tete + (CP.erreur ? `<div class="alerte"><b>Journal indisponible</b><span>${ech(CP.erreur)}</span></div>` : '')
    + `<div class="carte"><div class="duo" style="margin-bottom:6px">
        <div class="champ"><label for="cp-filtre">Personne</label>
          <select id="cp-filtre"><option value="">Tout le monde</option>${personnes.map(([u, n]) =>
            `<option value="${ech(u)}"${u === CP.filtre ? ' selected' : ''}>${ech(n)}</option>`).join('')}</select></div>
        <div class="champ"><label for="cp-cherche">Rechercher</label>
          <input id="cp-cherche" type="search" value="${ech(CP.cherche)}" placeholder="chambre 104, Martin, prix…"></div>
      </div>
      ${vues.length ? html : '<p class="aide">Rien à afficher.</p>'}
      ${vues.length > 400 ? '<p class="aide">Les 400 plus récentes sont affichées : affinez la recherche.</p>' : ''}
    </div>`;
}

/* ── Mon compte ──────────────────────────────────────────────────────── */
function vueCompte() {
  const m = ETAT.moi || {};
  return `<div class="entete"><div>
      <h1 class="t">Mon compte</h1>
      <p class="sous">${ech(m.nom)} · ${ech(m.profil)}</p></div></div>
    <div class="carte">
      <div class="ligne" style="margin:0 0 8px"><div class="txt"><b>Nom</b><span>${ech(m.nom)}</span></div></div>
      ${m.courriel ? `<div class="ligne" style="margin:0 0 8px"><div class="txt"><b>E-mail</b><span>${ech(m.courriel)}</span></div></div>` : ''}
      <div class="ligne" style="margin:0"><div class="txt"><b>Profil</b><span>${ech((roles()[m.role] || {}).resume || '')}</span></div>
        <span class="etat vif">${ech(m.profil)}</span></div>
    </div>
    ${m.secours ? `<div class="carte"><p>Vous êtes entré par <b>l’accès de secours</b>. Son mot de passe
      se change dans Vercel (variable ADMIN_MDP). Pour travailler au quotidien, créez-vous un compte
      nominatif dans Utilisateurs.</p></div>` : `<form class="carte" id="cp-form-mdp" novalidate>
      <h2 class="bloc-t">Changer mon mot de passe</h2>
      <div class="champ"><label for="cm-ancien">Mot de passe actuel</label>
        <input type="password" id="cm-ancien" autocomplete="current-password" required></div>
      <div class="duo">
        <div class="champ"><label for="cm-nouveau">Nouveau mot de passe</label>
          <input type="password" id="cm-nouveau" autocomplete="new-password" minlength="10" required>
          <p class="aide">10 caractères au moins.</p></div>
        <div class="champ"><label for="cm-confirme">Confirmez-le</label>
          <input type="password" id="cm-confirme" autocomplete="new-password" required></div>
      </div>
      <p class="aide">Vos autres sessions ouvertes (un autre ordinateur, un téléphone) seront fermées.</p>
      <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:14px">
        <button class="btn plein cp-garde">Changer le mot de passe</button>
        <p class="msg" id="cp-msg-mdp" role="status"></p>
      </div>
    </form>`}`;
}

/* ── Les gestes ──────────────────────────────────────────────────────── */
const trouver = (id) => (CP.comptes || []).find((c) => c.id === id);
function direListe(t) { const m = $('#cp-msg-liste'); if (m) m.textContent = t || ''; }

document.addEventListener('click', async (e) => {
  const b = e.target.closest('[data-cp-ajouter],[data-cp-annuler],[data-cp-fermer-cree],[data-cp-copier],'
    + '[data-cp-reinit],[data-cp-actif],[data-cp-suppr],[data-cp-rafraichir]');
  if (!b) return;
  if (b.hasAttribute('data-cp-ajouter')) { CP.ajout = true; CP.cree = null; rendre(); $('#cp-nom').focus(); return; }
  if (b.hasAttribute('data-cp-annuler')) { CP.ajout = false; rendre(); return; }
  if (b.hasAttribute('data-cp-fermer-cree')) { CP.cree = null; rendre(); return; }
  if (b.hasAttribute('data-cp-rafraichir')) { CP.journal = null; rendre(); return; }
  if (b.hasAttribute('data-cp-copier')) {
    try { await navigator.clipboard.writeText(b.dataset.cpCopier); b.textContent = 'Copié ✓'; }
    catch (err) { b.textContent = 'Copie impossible : sélectionnez le texte'; }
    return;
  }
  const id = b.dataset.cpReinit || b.dataset.cpActif || b.dataset.cpSuppr;
  const c = trouver(id);
  if (!c) return;
  direListe('');
  let r;
  if (b.hasAttribute('data-cp-reinit')) {
    if (!confirm('Créer un nouveau mot de passe provisoire pour ' + c.nom + ' ?\n\n'
      + 'L’ancien cesse de fonctionner tout de suite, et ses sessions ouvertes sont fermées.')) return;
    r = await appel('compte-reinitialiser', { id });
    if (r.ok) CP.cree = { compte: r.compte, provisoire: r.provisoire, reinit: true };
  } else if (b.hasAttribute('data-cp-actif')) {
    if (c.actif && !confirm('Désactiver le compte de ' + c.nom + ' ?\n\nLa personne ne pourra plus '
      + 'entrer, et ses sessions ouvertes sont fermées. Rien n’est effacé : vous pourrez le réactiver.')) return;
    r = await appel('compte', { id, nom: c.nom, role: c.role, actif: !c.actif });
  } else {
    if (!confirm('Supprimer définitivement le compte de ' + c.nom + ' (' + c.courriel + ') ?\n\n'
      + 'Ce qu’il a fait reste dans le journal. Pour couper l’accès sans effacer, préférez « Désactiver ».')) return;
    r = await appel('compte-supprimer', { id });
  }
  if (!r.ok) return direListe(r.message || 'L’opération a échoué.');
  CP.comptes = null;     // relu tel que le serveur l'a enregistre
  CP.journal = null;
  rendre();
  if (CP.cree) window.scrollTo({ top: 0, behavior: 'smooth' });
});

document.addEventListener('change', async (e) => {
  const s = e.target.closest('[data-cp-role]');
  if (s) {
    const c = trouver(s.dataset.cpRole);
    if (!c) return;
    const vers = (roles()[s.value] || {}).nom;
    if (!confirm('Passer ' + c.nom + ' au profil « ' + vers + ' » ?\n\nSes sessions ouvertes seront fermées : '
      + 'il devra se reconnecter.')) { s.value = c.role; return; }
    const r = await appel('compte', { id: c.id, nom: c.nom, role: s.value, actif: c.actif });
    if (!r.ok) { s.value = c.role; return direListe(r.message || 'Le changement a échoué.'); }
    CP.comptes = null; CP.journal = null; rendre();
    return;
  }
  if (e.target.id === 'cp-filtre') { CP.filtre = e.target.value; rendre(); }
});

document.addEventListener('input', (e) => {
  if (e.target.id !== 'cp-cherche') return;
  CP.cherche = e.target.value;
  const pos = e.target.selectionStart;
  rendre();
  const champ = $('#cp-cherche');
  if (champ) { champ.focus(); champ.setSelectionRange(pos, pos); }
});

document.addEventListener('submit', async (e) => {
  if (e.target.id === 'cp-form-ajout') {
    e.preventDefault();
    const m = $('#cp-msg-ajout');
    m.textContent = '';
    const choix = document.querySelector('input[name="cp-role"]:checked');
    const r = await appel('compte', { nom: $('#cp-nom').value, courriel: $('#cp-courriel').value,
      role: choix ? choix.value : '' });
    if (!r.ok) {
      m.textContent = r.message || 'La création a échoué.';
      const champ = r.champs && { nom: '#cp-nom', courriel: '#cp-courriel' }[r.champs[0]];
      if (champ) $(champ).focus();
      return;
    }
    CP.ajout = false;
    CP.cree = { compte: r.compte, provisoire: r.provisoire, reinit: false };
    CP.comptes = null; CP.journal = null;
    rendre();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
  if (e.target.id === 'cp-form-mdp') {
    e.preventDefault();
    const m = $('#cp-msg-mdp');
    m.className = 'msg mal';
    if ($('#cm-nouveau').value !== $('#cm-confirme').value) {
      m.textContent = 'Les deux saisies du nouveau mot de passe ne sont pas identiques.';
      return;
    }
    const r = await appel('mot-de-passe', { ancien: $('#cm-ancien').value, nouveau: $('#cm-nouveau').value });
    if (!r.ok) { m.textContent = r.message || 'Le changement a échoué.'; return; }
    ['#cm-ancien', '#cm-nouveau', '#cm-confirme'].forEach((s) => { $(s).value = ''; });
    m.className = 'msg bon';
    m.textContent = 'Mot de passe changé. Vos autres sessions sont fermées.';
  }
});
