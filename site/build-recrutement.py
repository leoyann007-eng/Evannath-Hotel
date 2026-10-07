# -*- coding: utf-8 -*-
"""Genere recrutement.html : les postes ouverts, tels que l'hotel les publie.

POURQUOI CETTE PAGE EXISTE, ET CE QU'ELLE N'EST PAS.

Elle ne TROUVE pas de candidats. Les visiteurs de ce site cherchent une
chambre, pas un emploi, et le site est en mode prospection — invisible des
moteurs. En Cote d'Ivoire, pour un poste en hotellerie a Assinie, les
candidats viennent de Facebook, de WhatsApp et du bouche-a-oreille ; le pied
de page annonce 21 000 abonnes sur Facebook, et cette page part de zero.

Facebook reste donc le CANAL. Cette page est la DESTINATION : une
publication disparait du fil en trois jours, les details se perdent dans les
commentaires, et six mois plus tard plus personne ne retrouve l'annonce. Ici
l'offre est entiere, le lien est permanent, et un seul endroit dit comment
postuler.

TROIS CONSEQUENCES, ecrites dans le code plus bas :

  1. CHAQUE OFFRE A SON ANCRE. recrutement.html#poste-receptionniste-de-nuit :
     une publication pointe sur UN poste, pas sur la liste.
  2. LE TELEPHONE D'ABORD. Le trafic viendra d'un lien ouvert dans le
     navigateur d'un telephone.
  3. PAS DANS LE MENU PRINCIPAL. Le menu est le parcours d'un client qui
     reserve. Le lien vit dans le pied de page ; les candidats arrivent par
     un lien direct.

LE CONTENU N'EST PAS DANS CETTE PAGE. Les offres vivent dans le magasin et
se lisent a l'ouverture, comme les promotions. Une offre publiee apparait
sans regenerer le site, et une offre dont la date de fin est passee ne sort
meme pas du serveur.

TROIS ETATS, ET LE TROISIEME EST LA RAISON D'ETRE DU RESTE. Aucune offre
n'est pas la meme chose qu'une panne : un reseau coupe qui afficherait
« aucun poste ouvert » ferait croire a un candidat qu'il n'y a rien. On dit
alors qu'on n'arrive pas a afficher, et on donne le contact.
"""
import io
import json
import _schema
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV, WA, MAIL, medaillon, PAGNE_CSS

CSS = """
body{background:var(--bark)}
.head{padding-top:150px;padding-bottom:10px}
.head h1{margin:10px 0 16px;font-size:clamp(2.1rem,4.6vw,3.1rem)}
.head h1 em{font-style:italic;color:var(--bronze-2)}
.head .lede{max-width:58ch;font-size:1.02rem;color:var(--prose)}

.postes{padding:34px 0 96px}
/* Une offre par bloc, pleine largeur : une grille de cartes obligerait a
   resumer, et un resume d'offre d'emploi est une offre incomplete. */
.poste{border:1px solid var(--line);background:var(--bark-2);padding:30px 32px;
  margin-bottom:18px;scroll-margin-top:110px}
.poste:target{border-color:var(--bronze);box-shadow:0 0 0 1px rgba(185,138,80,.35)}
.poste h2{font-size:1.5rem;font-weight:400;margin-bottom:8px}
.poste .meta{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px}
/* La date limite : sous l'intitule, discrete. Un candidat la cherche avant
   de lire le reste. */
.poste .fin{font-size:13px;color:var(--muted);margin:-8px 0 18px}
.poste .fin time{color:var(--cream);font-weight:600}
.poste .meta span{font-size:10px;letter-spacing:.16em;text-transform:uppercase;
  font-weight:700;color:var(--bronze-2);border:1px solid var(--line);padding:5px 11px}
/* white-space:pre-line — l'hotel ecrit ses missions une par ligne. Les
   ecraser en un pave rendrait l'offre illisible sur un telephone. */
.poste .corps{white-space:pre-line;font-size:15.5px;color:var(--prose);
  max-width:72ch;margin-bottom:18px}
.poste h3{font-size:10px;letter-spacing:.2em;text-transform:uppercase;
  color:var(--bronze);font-weight:700;margin:22px 0 8px}
.poste .post{border-top:1px solid var(--line);margin-top:24px;padding-top:20px;
  display:flex;flex-wrap:wrap;gap:14px;align-items:center}
.poste .post p{font-size:15px;margin:0}
.poste .post b{color:var(--cream);font-weight:600}
.poste .lien{font-size:12.5px;color:var(--muted);border:0;background:none;
  cursor:pointer;padding:0;letter-spacing:.04em}
.poste .lien:hover{color:var(--bronze-2)}
.poste .lien.fait{color:var(--palm)}

/* Les trois etats de la liste. Le dernier n'est pas une politesse : un
   reseau coupe qui dirait « aucun poste » ferait croire qu'il n'y a rien. */
.etat{border:1px solid var(--line);background:var(--bark-2);padding:44px 32px;
  text-align:center}
/* Signature textile — touche 3 sur 5. Le medaillon coiffe le bloc vide.
   Le padding du bloc l'ecarte deja du bord ; le margin-bottom pose les
   12 px demandes entre lui et la premiere ligne. */
.pagne-vide{width:96px;margin:0 auto 14px;color:#A88560}
.etat p{color:var(--muted);font-size:15.5px;margin:0 auto;max-width:48ch}
.etat .g{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:24px}
.etat.mal{border-color:rgba(166,58,37,.4)}

@media(max-width:720px){
  .head{padding-top:120px;padding-bottom:6px}
  .postes{padding:24px 0 70px}
  .poste{padding:24px 20px}
  .poste .post{flex-direction:column;align-items:flex-start;gap:10px}
}
"""
# Les cinq touches textiles : ce morceau ne part que sur les pages qui
# en portent une.
# Les utilitaires D'ABORD, les placements ensuite : a specificite egale
# c'est la derniere regle qui gagne, et ce sont les placements qui
# doivent gagner. Dans l'autre sens, `.pagne-damas{position:absolute}`
# ecrasait le `position:relative` du placement, et le motif sortait du
# flux — largeur zero, invisible, et le test passait au vert.
CSS = PAGNE_CSS + CSS


b = [header('index.html#reserver', 'Réserver'), drawer(''), '''
<section class="head">
  <div class="wrap narrow">
    <span class="eyebrow" data-t="eb">Nous rejoindre</span>
    <h1 data-t="h1">Travailler à <em data-t="h1e">l'Evannath</em></h1>
    <p class="lede" data-t="lede">Les postes ouverts en ce moment. Chaque offre indique
    comment postuler — il n'y a pas de formulaire à remplir ici.</p>
  </div>
</section>

<section class="postes">
  <div class="wrap narrow">
    <div id="liste">
      <div class="etat"><p data-t="charge">Chargement des offres…</p></div>
    </div>
  </div>
</section>

''' + FOOTER]

# Le rendu se fait a l'ouverture : les offres vivent dans le magasin, pas
# dans cette page. Aucun cache — une offre retiree doit disparaitre a la
# seconde, et la reponse fait quelques centaines d'octets.
JS = NAV_JS + '''

(function () {
  /* Le medaillon est pose a la GENERATION, pas recopie ici : une seule
     source, le fichier SVG. */
  var MED = ''' + json.dumps(medaillon('carre', 'pagne-vide')) + ''';
  var liste = document.getElementById('liste');
  if (!liste) return;

  function ech(t) {
    return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  /* L'ancre d'une offre : son intitule, reduit a ce qui tient dans une URL.
     Elle doit survivre a une modification du texte, d'ou l'identifiant en
     secours si le titre ne donne rien d'utilisable. */
  function ancre(o) {
    var s = String(o.titre || '').toLowerCase()
      .normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    return 'poste-' + (s || String(o.id || '').slice(0, 8));
  }

  function bloc(o) {
    var id = ancre(o);
    var meta = [o.contrat, o.departement].filter(Boolean)
      .map(function (m) { return '<span>' + ech(m) + '</span>'; }).join('');
    var profil = o.profil
      ? '<h3 data-t="pr">Profil recherché</h3><div class="corps">' + ech(o.profil) + '</div>'
      : '';
    /* « Comment postuler » est ecrit par l'hotel, et affiche tel quel. Si
       une adresse y figure, on en fait un lien ; sinon c'est une consigne,
       et une consigne ne se clique pas. */
    var p = String(o.postuler || '').trim();
    var mail = p.match(/[\\w.+-]+@[\\w-]+\\.[\\w.-]+/);
    var tel = p.match(/\\+?[0-9][0-9 ().-]{7,}/);
    var comment;
    if (mail) {
      comment = '<p><b data-t="cp">Pour postuler</b> — <a href="mailto:' + ech(mail[0])
        + '?subject=' + encodeURIComponent('Candidature — ' + (o.titre || ''))
        + '">' + ech(mail[0]) + '</a></p>';
    } else if (tel) {
      comment = '<p><b data-t="cp">Pour postuler</b> — <a href="tel:'
        + ech(tel[0].replace(/[^+0-9]/g, '')) + '">' + ech(p) + '</a></p>';
    } else if (p) {
      comment = '<p><b data-t="cp">Pour postuler</b> — ' + ech(p) + '</p>';
    } else {
      /* Rien n'a ete precise : on renvoie vers le chemin que le site porte
         deja, plutot que d'inventer une adresse de recrutement. */
      comment = '<p><b data-t="cp">Pour postuler</b> — <a href="contact.html"'
        + ' data-t="cc">écrivez-nous par la page Contact</a></p>';
    }
    /* La date limite, si l'hotel en a pose une. Le texte de la date est ecrit
       par EVN_LANG, dans la langue de la page. */
    var fin = /^\\d{4}-\\d{2}-\\d{2}$/.test(o.fin || '')
      ? '<p class="fin"><span data-t="jq">Candidatures jusqu\\'au</span> '
        + '<time datetime="' + o.fin + '"></time></p>'
      : '';
    return '<article class="poste" id="' + id + '">'
      + '<h2>' + ech(o.titre) + '</h2>'
      + (meta ? '<div class="meta">' + meta + '</div>' : '')
      + fin
      + '<div class="corps">' + ech(o.texte) + '</div>'
      + profil
      + '<div class="post">' + comment
      + '<button type="button" class="lien" data-copier="' + id + '"'
      + ' data-t="cl">Copier le lien de cette offre</button>'
      + '</div></article>';
  }

  var VIDE = '<div class="etat">' + MED
    + '<p data-t="vide">Aucun poste n\\'est ouvert en ce moment. '
    + 'Les offres paraissent ici et sur notre page Facebook.</p>'
    + '<div class="g"><a class="btn" href="https://www.facebook.com/evannathhotel"'
    + ' target="_blank" rel="noopener" data-t="fb">Suivre sur Facebook</a></div></div>';

  /* La panne se dit. Elle ne se deguise pas en « aucun poste ». */
  var PANNE = '<div class="etat mal"><p data-t="panne">Nous n\\'arrivons pas à afficher '
    + 'les offres pour le moment. Réessayez dans un instant, ou écrivez-nous.</p>'
    + '<div class="g"><a class="btn" href="https://wa.me/''' + WA + '''"'
    + ' target="_blank" rel="noopener" data-t="wa">Écrire sur WhatsApp</a>'
    + '<a class="btn" href="mailto:''' + MAIL + '''" data-t="ml">''' + MAIL + '''</a></div></div>';

  fetch('/api/admin?a=public', { cache: 'no-store' })
    .then(function (r) { if (!r.ok) throw new Error('indisponible'); return r.json(); })
    .then(function (j) {
      var offres = (j && j.emplois) || [];
      if (!offres.length) { liste.innerHTML = VIDE; return; }
      liste.innerHTML = offres.map(bloc).join('');
      /* Arrive par un lien vers une offre precise : on l'amene dessus une
         fois la liste posee. L'ancre du document a ete lue avant que le
         bloc n'existe, le navigateur n'a donc rien pu faire. */
      if (location.hash) {
        var cible = document.getElementById(location.hash.slice(1));
        if (cible) cible.scrollIntoView();
      }
    })
    .catch(function () { liste.innerHTML = PANNE; })
    .then(function () {
      /* 01 · Le medaillon n'existe qu'APRES la reponse du serveur : il est
         dans le bloc vide, injecte ici. L'observateur doit donc tourner
         maintenant — lance au chargement, il n'aurait rien trouve, et le
         medaillon serait reste invisible, bloque a son etat de depart. */
      if (window.EVN_AU_SCROLL) window.EVN_AU_SCROLL('.pagne-vide', 'vu');
      /* Les offres arrivent APRES la traduction de la page : un visiteur
         venu en anglais voyait « Profil recherche », « Pour postuler » en
         francais. Leurs libelles rejoignent le dictionnaire francais (pour
         revenir au francais), puis la langue courante est reappliquee. */
      liste.querySelectorAll('[data-t]').forEach(function (e) {
        if (!(e.dataset.t in FR)) FR[e.dataset.t] = e.innerHTML;
      });
      if (document.documentElement.lang === 'en') EVN_LANGUE('en', false);
      else EVN_LANG('fr');
    });

  /* Les dates limites, dans la langue de la page. Appelee par le chassis a
     chaque changement de langue. Midi, et non minuit : une date seule lue
     a minuit UTC tomberait la veille selon le fuseau. */
  window.EVN_LANG = function (lg) {
    var loc = lg === 'en' ? 'en-GB' : 'fr-FR';
    liste.querySelectorAll('time[datetime]').forEach(function (t) {
      t.textContent = new Date(t.getAttribute('datetime') + 'T12:00:00')
        .toLocaleDateString(loc, { day: 'numeric', month: 'long', year: 'numeric' });
    });
  };

  /* Copier le lien d'une offre : c'est le geste qui sert a la publier sur
     Facebook ou a l'envoyer par WhatsApp. */
  liste.addEventListener('click', function (e) {
    var b = e.target.closest('[data-copier]');
    if (!b) return;
    var url = location.origin + location.pathname + '#' + b.dataset.copier;
    var fait = function () {
      b.textContent = b.dataset.ok || 'Lien copié';
      b.classList.add('fait');
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(fait, function () { location.hash = b.dataset.copier; });
    } else {
      location.hash = b.dataset.copier;
    }
  });
}());

var EN={''' + EN_NAV + '''cta:"Book now",
eb:"Join us",h1:"Working at <em data-t=\\'h1e\\'>the Evannath</em>",h1e:"the Evannath",
lede:"The positions open right now. Each listing says how to apply — there is no form to fill in here.",
charge:"Loading the listings…",
pr:"Who we are looking for",jq:"Applications until",cp:"To apply",cc:"write to us from the Contact page",
cl:"Copy the link to this listing",
vide:"No position is open at the moment. Listings appear here and on our Facebook page.",
fb:"Follow on Facebook",
panne:"We cannot display the listings right now. Try again in a moment, or write to us.",
wa:"Message on WhatsApp",ml:"''' + MAIL + '''"};

''' + LANG_JS

LD = _schema.bloc(
    _schema.hotel(),
    _schema.fil([('Accueil', 'index'), ('Nous rejoindre', None)]))

# PAS de noindex, contrairement a reserver, mentions-legales et 404. C'est la
# page du site qui gagne le PLUS a etre indexee : on cherche un emploi sur
# Google. Tant que le site est en mode prospection, le chassis pose le
# noindex global — le jour ou il tombe, cette page est prete.
html = page(
 "Nous rejoindre — Hôtel Evannath, Assinie",
 "Les postes ouverts à l'Hôtel Evannath, Assinie PK 19. Réception, "
 "restauration, spa : les offres en cours et comment postuler.",
 "g-entree", CSS, '\n'.join(b), JS, slug="recrutement", jsonld=LD)

io.open('recrutement.html', 'w', encoding='utf-8').write(html)
print('recrutement.html      ok')
