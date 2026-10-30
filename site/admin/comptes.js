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
  connexions: null,       // Mon compte : ses dernieres connexions
  mfa: null,              // Mon compte : null | 'tel' | 'codes' | { prep } | { codes }
};

/** Le profil connecte a-t-il ce droit ? (affichage seulement) */
function peut(droit) {
  return !!(ETAT.moi && ETAT.moi.droits && ETAT.moi.droits.includes(droit));
}

const ROLES_LOCAUX = {
  admin: { nom: 'Administrateur', resume: 'Tout, plus les comptes, les prix et les paramètres.' },
  reception: { nom: 'Réception', resume: 'Disponibilités, réservations et chambres.' },
  communication: { nom: 'Communication', resume: 'Événements, promotions, campagnes, recrutement, affiches et référencement.' },
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
  ecranPorte('#fpremier');
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
  PREMIERE = true;
  montrerCadre();
});

/* ── La double authentification ────────────────────────────────────────
   Obligatoire pour tous les comptes : tant qu'elle n'est pas activee, le
   serveur n'ouvre que cet ecran. Trois temps — installer une application,
   scanner le QR code, saisir le premier code — puis les codes de secours,
   montres une seule fois.

   Le QR code est dessine ICI, dans la page, par qrcode.js (MIT, Kazuhiko
   Arase) : le secret ne part chez aucun service exterieur. La bibliotheque
   ne se charge que lorsqu'on en a besoin. */
let PREMIERE = false;          // on vient de choisir son mot de passe
let QR_PRET = null;
function chargerQr() {
  if (!QR_PRET) {
    QR_PRET = new Promise((ok, ko) => {
      const sc = document.createElement('script');
      sc.src = '/admin/qrcode.js';
      sc.onload = ok;
      sc.onerror = () => { QR_PRET = null; ko(new Error('qr')); };
      document.head.appendChild(sc);
    });
  }
  return QR_PRET;
}
async function poserQr(img, uri) {
  try {
    await chargerQr();
    const q = qrcode(0, 'M');
    q.addData(uri);
    q.make();
    img.src = q.createDataURL(6, 2);
  } catch (e) { img.alt = 'QR code indisponible : saisissez la clé à la main.'; }
}
const cleLisible = (s) => String(s || '').replace(/(.{4})/g, '$1 ').trim();

/** Les trois etapes. `pre` prefixe les identifiants (porte ou Mon compte). */
function etapesActivation(prep, pre) {
  return `<div class="cp-etapes">
    <div class="cp-etape"><span class="cp-no">1</span><div><b>Installez une application d’authentification</b>
      <p>Google Authenticator, Microsoft Authenticator, ou l’application Mots de passe de l’iPhone.
      Elle est gratuite.</p></div></div>
    <div class="cp-etape"><span class="cp-no">2</span><div><b>Scannez ce QR code avec l’application</b>
      <div class="cp-qr"><img id="${pre}-qr" alt="QR code à scanner"></div>
      <p>Pas d’appareil photo ? Saisissez cette clé à la main :</p>
      <div class="cp-cle"><code>${ech(cleLisible(prep.secret))}</code>
        <button type="button" class="btn-ic cp-garde" data-cp-copier="${ech(prep.secret)}" title="Copier la clé"
          aria-label="Copier la clé">${ic('copie')}</button></div></div></div>
    <div class="cp-etape"><span class="cp-no">3</span><div style="flex:1;min-width:0"><b>Entrez le code affiché</b>
      <input id="${pre}-code" class="code6" inputmode="numeric" autocomplete="one-time-code" maxlength="6"
        placeholder="······" aria-label="Code à 6 chiffres" required style="margin-top:10px">
      <button class="btn plein cp-garde" style="width:100%;margin-top:12px">${ic('bouclier')} Activer la protection</button>
      </div></div>
  </div>`;
}

/** Les codes de secours, et de quoi les garder. */
function blocCodes(codes) {
  const texte = 'Hôtel Evannath — codes de secours de ' + ((ETAT.moi && ETAT.moi.courriel) || '') + '\n'
    + 'Chaque code ne sert qu’une fois.\n\n' + codes.join('\n') + '\n';
  return `<div class="cp-codes codes-imprimables">${codes.map((c) => `<code>${ech(c)}</code>`).join('')}</div>
    <div class="cp-codes-gestes">
      <button type="button" class="btn mince cp-garde" data-cp-copier="${ech(codes.join('\n'))}">${ic('copie')} Copier</button>
      <a class="btn mince" download="codes-de-secours-evannath.txt"
        href="data:text/plain;charset=utf-8,${encodeURIComponent(texte)}">${ic('tele')} Télécharger</a>
      <button type="button" class="btn mince cp-garde" data-cp-imprimer>${ic('impr')} Imprimer</button>
    </div>`;
}

async function montrerActivation() {
  ecranPorte('#factiver');
  $('#act-etape').textContent = PREMIERE ? 'Première connexion · étape 2 sur 2' : 'Dernière étape';
  $('#erractiver').textContent = '';
  $('#act-zone').innerHTML = '<p class="aide">Préparation…</p>';
  const r = await appel('2fa-preparer', {}).catch(() => ({}));
  if (!r.ok) { $('#erractiver').textContent = r.message || 'La préparation a échoué. Rechargez la page.'; return; }
  $('#act-zone').innerHTML = etapesActivation(r, 'act');
  poserQr($('#act-qr'), r.uri);
}

$('#factiver').addEventListener('submit', async (e) => {
  e.preventDefault();
  $('#erractiver').textContent = '';
  const r = await appel('2fa-activer', { code: $('#act-code').value });
  if (!r.ok) { $('#erractiver').textContent = r.message || 'L’activation a échoué.'; $('#act-code').value = ''; return; }
  $('#codes-zone').innerHTML = blocCodes(r.codes);
  $('#codes-ok').checked = false;
  ecranPorte('#fcodes');
});
$('#fcodes').addEventListener('submit', (e) => {
  e.preventDefault();
  PREMIERE = false;
  $('#codes-zone').innerHTML = '';
  montrerCadre();
});
$('#act-sortir').addEventListener('click', async () => {
  await appel('sortir', {}).catch(() => {});
  ETAT.moi = null;
  montrerPorte();
});

$('#sortir').addEventListener('click', () => {
  ETAT.moi = null;
  Object.assign(CP, { comptes: null, journal: null, cree: null, ajout: false, erreur: '', connexions: null, mfa: null });
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
  } else if (VUE === 'compte' && CP.connexions === null && ETAT.moi && !ETAT.moi.secours) {
    CP.enCours = true;
    const r = await appel('mes-connexions').catch(() => ({}));
    CP.enCours = false;
    CP.connexions = r.ok ? r.connexions : [];
    if (VUE === 'compte') rendre();
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
    + 'À la première connexion, il vous sera demandé de choisir votre propre mot de passe, '
    + 'puis d’activer la double authentification : installez d’avance Google Authenticator '
    + '(ou Microsoft Authenticator) sur votre téléphone.';
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
      ${CP.ajout ? '' : `<button class="btn plein" data-cp-ajouter>${ic('plus')} Ajouter une personne</button>`}</div>`;
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
      <td>${c.mfa ? '<span class="etat vif">Activée</span>' : '<span class="etat attend">À activer</span>'}</td>
      <td class="cp-sous">${c.derniere ? quand(c.derniere) : 'Jamais connecté'}</td>
      <td class="cp-actions">${soi ? '' : `
        <button type="button" class="btn mince" data-cp-reinit="${c.id}" title="Créer un nouveau mot de passe provisoire">Mot de passe</button>
        ${c.mfa ? `<button type="button" class="btn mince" data-cp-2fa="${c.id}" title="Téléphone perdu : la personne réactivera la double authentification à sa prochaine connexion">Double auth.</button>` : ''}
        <button type="button" class="btn mince" data-cp-actif="${c.id}">${c.actif ? 'Désactiver' : 'Réactiver'}</button>
        <button type="button" class="btn mince danger" data-cp-suppr="${c.id}">Supprimer</button>`}</td>
    </tr>`;
  }).join('');

  const liste = CP.comptes.length ? `<div class="carte cp-table-zone"><table class="cp-table">
      <thead><tr><th>Personne</th><th>Profil</th><th>État</th><th>Double auth.</th><th>Dernière connexion</th><th><span class="cp-vh">Actions</span></th></tr></thead>
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
      <p class="aide">La double authentification est obligatoire pour tout le monde : chaque personne
      l’active à sa première connexion. Téléphone perdu et plus de codes de secours ? « Double auth. »
      la remet à zéro ; la personne la réactivera en se reconnectant.</p>
      <p class="aide">Accès de secours : réservé au développeur (mot de passe ADMIN_MDP, dans Vercel).
      Il sert à créer le premier compte, ou à rentrer si plus aucun administrateur ne le peut.</p></div>`;

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
const initiales = (nom) => String(nom || '?').split(/\s+/).filter(Boolean).slice(0, 2)
  .map((x) => x[0].toUpperCase()).join('');

/** La carte de la double authentification, selon ou on en est. */
function carteMfa(m) {
  const etat = CP.mfa;
  let corps;
  if (etat && etat.prep) {
    corps = `<form id="cp-form-tel">${etapesActivation(etat.prep, 'mc')}
      <p class="msg mal" id="cp-msg-mfa" role="alert"></p>
      <button type="button" class="btn mince" data-cp-mfa-annuler style="margin-top:6px">Annuler</button></form>`;
  } else if (etat && etat.codes) {
    corps = `<p class="aide" style="margin:0 0 4px">Vos nouveaux codes de secours. Les anciens ne valent plus.
      Ils ne seront plus affichés : gardez-les hors du téléphone.</p>${blocCodes(etat.codes)}
      <button type="button" class="btn plein mince cp-garde" data-cp-mfa-annuler style="margin-top:14px">C’est noté</button>`;
  } else if (etat === 'tel' || etat === 'codes') {
    corps = `<form id="cp-form-code-actuel">
      <p class="aide" style="margin:0 0 12px">${etat === 'tel'
        ? 'Pour passer sur un nouveau téléphone, entrez d’abord le code affiché sur l’ancien.'
        : 'Entrez le code affiché par votre application pour recevoir de nouveaux codes de secours.'}</p>
      <input id="cp-code-actuel" class="code6" inputmode="numeric" autocomplete="one-time-code" maxlength="6"
        placeholder="······" aria-label="Code actuel" required style="max-width:280px">
      <div style="display:flex;gap:10px;margin-top:12px;flex-wrap:wrap">
        <button class="btn plein cp-garde">Continuer</button>
        <button type="button" class="btn" data-cp-mfa-annuler>Annuler</button></div>
      <p class="msg mal" id="cp-msg-mfa" role="alert"></p></form>`;
  } else {
    const n = m.codesRestants || 0;
    corps = `<div class="cp-mfa-etat">
        <i>${ic('bouclier')}</i>
        <div><b>Votre compte est protégé</b><span>À chaque connexion, un code de votre téléphone est demandé
        en plus du mot de passe. ${n} code${n > 1 ? 's' : ''} de secours restant${n > 1 ? 's' : ''}.</span></div>
      </div>
      ${n <= 3 ? `<div class="alerte or" style="margin:14px 0 0"><i>${ic('alerte')}</i><div><b>Plus que ${n} code${n > 1 ? 's' : ''} de secours</b>
        <span>Demandez-en de nouveaux avant de perdre votre téléphone.</span></div></div>` : ''}
      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:16px">
        <button type="button" class="btn mince cp-garde" data-cp-mfa="tel">${ic('tel')} Changer de téléphone</button>
        <button type="button" class="btn mince cp-garde" data-cp-mfa="codes">${ic('cle')} Nouveaux codes de secours</button>
      </div>`;
  }
  return `<div class="carte"><div class="cp-tete"><h2 class="bloc-t" style="margin:0">Double authentification</h2>
    <span class="etat vif">Activée</span></div>${corps}</div>`;
}

function vueCompte() {
  const m = ETAT.moi || {};
  const profil = `<div class="carte cp-profil-carte"><span class="cp-av">${ech(initiales(m.nom))}</span>
      <div><b>${ech(m.nom)}</b><span>${ech(m.courriel || 'Accès de secours')}</span></div>
      <span class="etat dort" style="margin-left:auto">${ech(m.profil)}</span></div>`;
  const tete = `<div class="entete"><div>
      <h1 class="t">Mon compte</h1>
      <p class="sous">Votre profil, la protection de votre compte et vos connexions.</p></div></div>`;
  if (m.secours) {
    return tete + profil + `<div class="carte"><p>Vous êtes entré par <b>l’accès de secours</b>, réservé au
      développeur. Son mot de passe se change dans Vercel (variable ADMIN_MDP). Pour travailler au quotidien,
      créez-vous un compte nominatif dans Utilisateurs.</p></div>`;
  }
  const connexions = CP.connexions === null ? '<p class="aide">Chargement…</p>'
    : !CP.connexions.length ? '<p class="aide">Aucune connexion enregistrée.</p>'
    : CP.connexions.map((c) => {
      const echec = /^(Échec|Connexion bloquée)/.test(c.x);
      const [quoi, ...ou] = c.x.split(' · ');
      return `<div class="cp-connexion${echec ? ' echec' : ''}"><i>${ic(echec ? 'alerte' : /iPhone|Android|iPad/.test(c.x) ? 'tel' : 'ordi')}</i>
        <div><b>${ech(ou.length ? ou.join(' · ') : quoi)}</b>
        <span>${ech(quand(c.t))}${ou.length ? ' · ' + ech(quoi) : ''}</span></div></div>`;
    }).join('');
  return tete + profil + `<div class="cp-deux">
    <div>${carteMfa(m)}
    <form class="carte" id="cp-form-mdp" novalidate>
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
    </form></div>
    <div class="carte"><h2 class="bloc-t">Dernières connexions</h2>
      <p class="aide" style="margin:-6px 0 8px">Un appareil ou une ville que vous ne reconnaissez pas ?
      Changez votre mot de passe, puis déconnectez les autres appareils.</p>
      ${connexions}
      <button type="button" class="btn mince danger cp-garde" data-cp-sessions style="margin-top:14px">${ic('sortie')}
        Déconnecter mes autres appareils</button>
      <p class="msg" id="cp-msg-sessions" role="status"></p></div>
  </div>`;
}

/* ── Les gestes ──────────────────────────────────────────────────────── */
const trouver = (id) => (CP.comptes || []).find((c) => c.id === id);
function direListe(t) { const m = $('#cp-msg-liste'); if (m) m.textContent = t || ''; }

document.addEventListener('click', async (e) => {
  const g = e.target.closest('[data-cp-mfa],[data-cp-mfa-annuler],[data-cp-sessions],[data-cp-imprimer]');
  if (g) {
    if (g.hasAttribute('data-cp-imprimer')) { window.print(); return; }
    if (g.hasAttribute('data-cp-mfa')) { CP.mfa = g.dataset.cpMfa; rendre(); const c = $('#cp-code-actuel'); if (c) c.focus(); return; }
    if (g.hasAttribute('data-cp-mfa-annuler')) { CP.mfa = null; rendre(); return; }
    if (!confirm('Déconnecter tous vos autres appareils ?\n\nCelui-ci reste connecté. Les autres devront '
      + 'se reconnecter, avec le mot de passe et le code.')) return;
    const r = await appel('sessions-fermer', {});
    const m = $('#cp-msg-sessions');
    if (m) { m.className = 'msg ' + (r.ok ? 'bon' : 'mal'); m.textContent = r.ok ? 'Vos autres appareils sont déconnectés.' : (r.message || 'Échec.'); }
    return;
  }
  const b = e.target.closest('[data-cp-ajouter],[data-cp-annuler],[data-cp-fermer-cree],[data-cp-copier],'
    + '[data-cp-reinit],[data-cp-actif],[data-cp-suppr],[data-cp-rafraichir],[data-cp-2fa]');
  if (!b) return;
  if (b.hasAttribute('data-cp-ajouter')) { CP.ajout = true; CP.cree = null; rendre(); $('#cp-nom').focus(); return; }
  if (b.hasAttribute('data-cp-annuler')) { CP.ajout = false; rendre(); return; }
  if (b.hasAttribute('data-cp-fermer-cree')) { CP.cree = null; rendre(); return; }
  if (b.hasAttribute('data-cp-rafraichir')) { CP.journal = null; rendre(); return; }
  if (b.hasAttribute('data-cp-copier')) {
    const avant = b.innerHTML;
    try { await navigator.clipboard.writeText(b.dataset.cpCopier); b.innerHTML = ic('check') + (b.classList.contains('btn-ic') ? '' : ' Copié'); }
    catch (err) { b.textContent = 'Copie impossible : sélectionnez le texte'; }
    setTimeout(() => { b.innerHTML = avant; }, 1800);
    return;
  }
  const id = b.dataset.cpReinit || b.dataset.cpActif || b.dataset.cpSuppr || b.dataset.cp2fa;
  const c = trouver(id);
  if (!c) return;
  direListe('');
  let r;
  if (b.hasAttribute('data-cp-reinit')) {
    if (!confirm('Créer un nouveau mot de passe provisoire pour ' + c.nom + ' ?\n\n'
      + 'L’ancien cesse de fonctionner tout de suite, et ses sessions ouvertes sont fermées.')) return;
    r = await appel('compte-reinitialiser', { id });
    if (r.ok) CP.cree = { compte: r.compte, provisoire: r.provisoire, reinit: true };
  } else if (b.hasAttribute('data-cp-2fa')) {
    if (!confirm('Remettre à zéro la double authentification de ' + c.nom + ' ?\n\nÀ faire quand la personne '
      + 'a perdu son téléphone ET ses codes de secours. Ses sessions sont fermées ; elle la réactivera '
      + 'à sa prochaine connexion, avec son mot de passe.')) return;
    r = await appel('compte-2fa', { id });
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
  if (e.target.id === 'cp-form-code-actuel') {
    e.preventDefault();
    const code = $('#cp-code-actuel').value;
    const m = $('#cp-msg-mfa');
    if (CP.mfa === 'tel') {
      const r = await appel('2fa-preparer', { code });
      if (!r.ok) { m.textContent = r.message || 'Code refusé.'; return; }
      CP.mfa = { prep: r };
      rendre();
      poserQr($('#mc-qr'), r.uri);
    } else {
      const r = await appel('2fa-codes', { code });
      if (!r.ok) { m.textContent = r.message || 'Code refusé.'; return; }
      CP.mfa = { codes: r.codes };
      ETAT.moi.codesRestants = r.codes.length;
      rendre();
    }
    return;
  }
  if (e.target.id === 'cp-form-tel') {
    e.preventDefault();
    const r = await appel('2fa-activer', { code: $('#mc-code').value });
    if (!r.ok) { $('#cp-msg-mfa').textContent = r.message || 'Code refusé.'; return; }
    CP.mfa = { codes: r.codes };
    ETAT.moi.codesRestants = r.codes.length;
    CP.connexions = null;
    rendre();
    return;
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
