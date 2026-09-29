# -*- coding: utf-8 -*-
"""Blocs partages par toutes les pages : nav unique, tiroir plein ecran, pied de page.
Utilise par les generateurs de pages. Aucune expression reguliere destructrice ici :
les pages sont ecrites en entier a partir de ces briques.
"""
import io
import os
import re

# Domaine de production. Une seule ligne a changer le jour ou le site passe
# sur evannathhotel.com : og:image, og:url, canonical et sitemap.xml en decoulent.
SITE = "https://evannathhotel.vercel.app"

# ---------------------------------------------------------------------------
# Mode prospection
# ---------------------------------------------------------------------------
# True  : la maquette porte la marque de l'hotel sur une URL qu'il ne controle
#         pas. Elle ne doit apparaitre dans aucun moteur de recherche, sous
#         peine de concurrencer leur propre site et d'exploiter publiquement
#         leur marque sans accord ecrit. Le visiteur qui a le lien voit tout
#         normalement : seuls les robots sont ecartes.
# False : le jour de la signature. Repasser a False, relancer tous les
#         generateurs et build-sitemap.py, puis retirer la regle
#         X-Robots-Tag de vercel.json (elle est commentee sur place).
PROSPECTION = True

# Ce que le site annonce publiquement. Le chiffre est repete en clair dans
# cinq fichiers ; celui-ci sert a l'administration, qui compare l'inventaire
# saisi a ce qui est promis. A rassembler ici un jour, pour que « 46 » ne
# vive qu'a un seul endroit.
CHAMBRES_ANNONCEES = 46

# ---------------------------------------------------------------------------
# Ou partent les demandes des formulaires
# ---------------------------------------------------------------------------
# True  : elles partent directement sur WhatsApp, avec le recapitulatif deja
#         redige et une reference. Aucune API, aucune cle, rien a configurer —
#         ce qui tombe bien : MAIL_EXP doit etre un expediteur verifie chez
#         Resend, donc un domaine que l'on ne possede pas tant que rien n'est
#         signe. Et en Cote d'Ivoire WhatsApp est de toute facon le canal le
#         plus rapide vers une reception.
# False : elles passent par /api/envoyer, qui les met en e-mail via Resend.
#         Le panneau WhatsApp redevient alors le repli, pas la voie normale.
#
# Independant de PROSPECTION : on peut signer et rester sur WhatsApp le temps
# que le domaine soit verifie.
ENVOI_WHATSAPP = True

# ---------------------------------------------------------------------------
# La remise en cours, pour toutes les pages qui affichent un prix
# ---------------------------------------------------------------------------
# Une promotion publiee depuis l administration ne peut pas s appliquer a une
# page et pas a la suivante : un prix barre sur la carte et intact sur la fiche
# est pire que pas de remise du tout. Un seul module decide, toutes les
# surfaces l interrogent — les cartes, le comparateur, les sept fiches et le
# tunnel de reservation.
REMISE_JS = r"""
window.EVN_REMISE = (function () {
  var P = null;                  /* la promotion retenue, une fois chargee */
  var attentes = [];
  var pret = false;

  function vise(p, slug) {
    var c = p.cible || {};
    if (c.toutes !== false) return true;
    return (c.chambres || []).indexOf(slug) >= 0;
  }

  var API = {
    /* La promotion applicable a cette chambre, ou null. */
    pour: function (slug) {
      return (P && vise(P, slug)) ? P : null;
    },
    /* Le prix apres remise. Rend le prix d origine si rien ne s applique :
       aucun appelant n a besoin de savoir s il y a une promotion. */
    prix: function (montant, slug) {
      var p = API.pour(slug);
      if (!p) return montant;
      var r = p.remise || {};
      if (!r.valeur) return montant;
      var n = r.type === 'montant'
        ? montant - Number(r.valeur)
        : Math.round(montant * (1 - r.valeur / 100));
      /* Une remise qui depasse le prix rendrait un tarif nul ou negatif :
         on garde le prix d origine plutot que d afficher une aberration. */
      return n > 0 ? n : montant;
    },
    /* « −20 % » ou « −10 000 F », pour l etiquette. */
    etiquette: function () {
      if (!P) return '';
      var r = P.remise || {};
      if (!r.valeur) return '';
      return r.type === 'montant'
        ? '−' + Number(r.valeur).toLocaleString('fr-FR') + ' F'
        : '−' + r.valeur + ' %';
    },
    titre: function () { return P ? (P.titre || 'Promotion en cours') : ''; },
    /* Appelle f des que la reponse est la — tout de suite si elle l est deja.
       Chaque page passe par ici : personne n attend le reseau a la main. */
    quand: function (f) {
      if (pret) { try { f(API); } catch (e) {} return; }
      attentes.push(f);
    }
  };

  function fini() {
    pret = true;
    attentes.forEach(function (f) { try { f(API); } catch (e) {} });
    attentes = [];
  }

  fetch('/api/admin?a=public', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (j) {
      /* Le serveur ne renvoie que les promotions dont la periode court. On
         retient la premiere : deux remises cumulees sur une meme chambre
         n auraient pas de sens, et personne ne saurait laquelle s applique. */
      P = ((j && j.promotions) || [])[0] || null;
    })
    .catch(function () { P = null; })
    .then(fini, fini);

  return API;
})();
"""

# La disponibilite, telle que le site la lit et la dit.
#
# Le verdict se calcule sur le serveur (api/admin.js, etatDe) : la regle des
# nuits ne doit exister qu'a un seul endroit. Ce module ne fait que demander,
# retenir, et donner le mot juste.
#
# QUATRE ETATS, ET LE DERNIER EST LA REGLE DE SECOURS :
#
#   libre     il reste au moins deux chambres de cette categorie. C'est la
#             SEULE facon dont « Disponible a ces dates » revient a l'ecran.
#   derniere  il en reste exactement une. C'est le seul chiffre que le
#             serveur laisse sortir, et il est vrai.
#   complet   il n'en reste aucune.
#   inconnu   tout le reste — aucune chambre saisie, reseau coupe, API
#             absente, dates incompletes. Le site redit alors ce qu'il
#             disait deja : la reception confirme sous 24 h.
#
# Rien ne retombe jamais sur `libre`. Un site qui annonce libre parce que le
# reseau a hoquete vend une chambre qui n'existe pas.
DISPO_JS = r"""
window.EVN_DISPO = (function () {
  var cache = {};   /* 'slug|du|au' -> { etat, a } */
  var rang = {};    /* par categorie : le numero du dernier appel emis */

  /* Le cache existe pour absorber le va-et-vient du visiteur sur ses dates,
     pas pour survivre a la journee. Une page laissee ouverte pendant que la
     reception ferme la chambre afficherait sinon « Disponible » jusqu'au
     rechargement — exactement le mensonge qu'on est en train de retirer. */
  var DUREE = 60000;

  var MOTS = {
    libre:    { fr: 'Disponible à ces dates',
                en: 'Available on these dates' },
    derniere: { fr: 'Dernière chambre à ces dates',
                en: 'Last room at these dates' },
    complet:  { fr: 'Complet à ces dates',
                en: 'Fully booked on these dates' },
    inconnu:  { fr: 'Disponibilité confirmée sous 24 h',
                en: 'Availability confirmed within 24 h' }
  };

  /* La couleur porte autant que le mot : une pastille verte dit « c'est
     libre » a qui ne lit pas. Elle ne sort donc que pour `libre`.
     `derniere` prend l'accent chaud de la maison, pas le rouge : il reste
     une chambre, ce n'est pas une alerte. */
  var COULEURS = { libre: 'var(--palm)', derniere: 'var(--bronze-2)',
                   complet: 'var(--err)', inconnu: 'var(--muted)' };

  var API = {
    libelle: function (etat, lg) {
      var m = MOTS[etat] || MOTS.inconnu;
      return m[lg || document.documentElement.lang] || m.fr;
    },
    couleur: function (etat) { return COULEURS[etat] || COULEURS.inconnu; },

    /* Demande l'etat d'une categorie sur un sejour, et appelle f(etat).
       f est appele TOUT DE SUITE avec 'inconnu' si les dates ne disent rien
       encore — l'affichage ne reste jamais vide en attendant le reseau. */
    pour: function (slug, du, au, f) {
      if (!slug || !du || !au || au <= du) { f('inconnu'); return; }
      var cle = slug + '|' + du + '|' + au;
      var vu = cache[cle];
      if (vu && Date.now() - vu.a < DUREE) { f(vu.etat); return; }

      /* Le visiteur change ses dates plus vite que le reseau ne repond. Sans
         ce numero, une reponse partie en premier et arrivee en dernier
         ecrasait l'etat des dates courantes par celui des precedentes. */
      var n = (rang[slug] = (rang[slug] || 0) + 1);

      fetch('/api/admin?a=dispo&chambre=' + encodeURIComponent(slug)
            + '&du=' + du + '&au=' + au, { cache: 'no-store' })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) {
          var e = (j && j.etats && j.etats[slug]) || 'inconnu';
          cache[cle] = { etat: e, a: Date.now() };
          if (n === rang[slug]) f(e);
        })
        .catch(function () { if (n === rang[slug]) f('inconnu'); });
    }
  };
  return API;
})();
"""

# Le prix barre, partout ou il s affiche. Les memes regles sur les quatre
# surfaces : ce qui change, c est la taille du texte, pas la facon de dire.
REMISE_CSS = """
.avant{text-decoration:line-through;text-decoration-thickness:1px;
  color:var(--muted);font-weight:400;margin-right:.45em;
  font-variant-numeric:tabular-nums}
.apres{color:var(--bronze-2)}
"""

# ---------------------------------------------------------------------------
# Le numero WhatsApp
# ---------------------------------------------------------------------------
# Tant que WA_EN_TEST vaut True, TOUS les liens WhatsApp du site pointent sur
# WA_TEST : la destination des cinq formulaires, mais aussi le bouton flottant,
# le pied de page, la page Contact et les fiches chambres.
#
# C'est voulu. Pendant les tests, rien ne doit atteindre la reception d'un
# etablissement qui n'a rien signe — ni une demande de reservation, ni un
# visiteur curieux qui clique sur le bouton flottant.
#
# Le jour de la signature : WA_EN_TEST = False, relancer les generateurs. Le
# numero de l'hotel revient partout, il n'a jamais quitte le fichier.
WA_EN_TEST = True

# Le numero WhatsApp de l'etablissement, confirme par la direction. Il ne se
# deduit PAS du site d'origine : celui-ci n'a aucun lien WhatsApp — c'est un
# des constats de l'audit. Sa page Contact liste trois numeros sans dire
# lequel porte WhatsApp ; le 05 46 01 73 77 avait ete suppose ici, a tort.
WA_HOTEL       = '2250151527575'        # la reception de l'hotel
WA_HOTEL_TEXTE = '+225 01 51 52 75 75'
WA_TEST        = '2250758408079'        # Leonardo HOUANSOU, pendant les tests

# L'adresse e-mail suit la meme logique. Elle non plus ne se deduit pas du
# site d'origine : « votre adresse e-mail n'est pas sur votre site » est un
# des constats de l'audit. {{MAIL}} etait prise sur leur
# page Facebook ; l'adresse que la reception releve reellement est celle-ci.
#
# Laquelle afficher en production reste a trancher avec l'etablissement :
# bonjour@evannathhotel.com porte la marque, celle-ci est relevee. Voir le
# point 8 de « A valider » dans le README. En attendant, on garde celle qui
# est lue.
MAIL_HOTEL = 'receptionhotelevannath@gmail.com'
# Ou arrivent les essais tant que l e-mail sert de canal : c est la valeur a
# donner a la variable MAIL_DEST chez Vercel. Elle n est PAS affichee.
MAIL_TEST  = 'houansouyannaxel@gmail.com'
WA_TEST_TEXTE  = '+225 07 58 40 80 79'

# Les deux seules valeurs que le reste du code doit employer.
WA       = WA_TEST       if WA_EN_TEST else WA_HOTEL
WA_TEXTE = WA_TEST_TEXTE if WA_EN_TEST else WA_HOTEL_TEXTE

# L adresse AFFICHEE est toujours celle de l hotel — un visiteur qui lit une
# page de l hotel doit y trouver l adresse de l hotel, pas celle de son
# prestataire. Le mode d essai ne passe pas par elle : les cinq formulaires
# partent sur WhatsApp, donc sur WA, qui pointe sur mon numero tant que
# WA_EN_TEST vaut True. Si l envoi par e-mail est un jour rallume
# (ENVOI_WHATSAPP a False), le destinataire est la variable MAIL_DEST chez
# Vercel — pas cette constante-ci.
MAIL     = MAIL_HOTEL

# En mode WhatsApp, la demande n'est transmise QUE si le visiteur appuie sur
# envoyer dans l'application. Les ecrans de confirmation doivent donc le dire :
# annoncer « Demande envoyee » des l'ouverture de WhatsApp ferait repartir en
# croyant avoir reserve celui qui n'est pas alle au bout.
# Le jour ou ENVOI_WHATSAPP repasse a False, les textes d'origine reviennent
# seuls — ils sont choisis ici, pas recopies dans les pages.
if ENVOI_WHATSAPP:
    CONF_TITRE    = "Votre demande vous attend dans WhatsApp"
    CONF_TITRE_EN = "Your request is waiting in WhatsApp"
    # Sans apostrophe : ces textes sont injectes tels quels dans des chaines
    # JavaScript delimitees par des apostrophes (le dictionnaire de seminaires).
    # Le point d'insertion echappe aussi, mais autant ne pas dependre des deux.
    CONF_GESTE    = ("Appuyez sur envoyer dans WhatsApp : ce geste transmet "
                     "votre demande à la réception. ")
    CONF_GESTE_EN = ("Tap send in the app — that is what delivers it to "
                     "reception. ")
    # Les recapitulatifs disent « est transmise ». Tant que le visiteur n'a
    # pas appuye sur envoyer, c'est un futur.
    CONF_VERBE    = 'sera transmise'
    CONF_VERBE_EN = 'will be sent'
else:
    CONF_TITRE = CONF_TITRE_EN = None   # chaque page garde son propre titre
    CONF_GESTE = CONF_GESTE_EN = ''
    CONF_VERBE    = 'est transmise'
    CONF_VERBE_EN = 'has been sent'

# On laisse volontairement les robots CRAWLER, tout en leur servant `noindex`.
# Un simple « Disallow: / » serait un contresens ici : Google ne lirait alors
# jamais la directive noindex, et pourrait tout de meme indexer l'URL nue en la
# decouvrant par un lien externe. Pour disparaitre vraiment, il faut etre lu.
ROBOTS_META = ('<meta name="robots" content="noindex, nofollow">\n'
               '<meta name="googlebot" content="noindex, nofollow">\n') if PROSPECTION else ''


ICONS = """<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#17100A">"""

# Les jetons de couleur et de typographie. Extraits pour que les pages
# ecrites a la main (la table, le spa) les partagent au lieu de les
# recopier : une variable ajoutee ici arrive partout.
TOKENS = """:root{
  /* ── Creme chaud ────────────────────────────────────────────────────
     La direction n'aimait pas le fond noir. Le site est passe au creme le
     24 septembre 2026, apres validation de l'accueil.

     Ce qui n'a PAS change : le bronze, le bois, Marcellus et Karla, « Le
     Reve Africain ». La palette vient toujours de leur logo — c'est le
     FOND qui a change, pas l'identite.

     --night ne devient PAS clair : ce n'est pas « le fond le plus noir »,
     c'est CE QUI CONTRASTE AVEC LE BRONZE. Il sert au texte pose sur un
     aplat bronze, et aux voiles poses sur les photos.

     --bronze sert de TEXTE et de FOND. Il lui faut donc etre assez sombre
     pour se lire sur le creme, et assez sombre pour porter du texte clair :
     #8A5F2B tient les deux. Mesure dans les deux sens.

     La table et Le spa redeclarent leur nuit : un restaurant et un spa se
     montrent en lumiere basse, c'est un parti pris. */
  --night:#100B06; --bark:#FBF7F0; --bark-2:#F4EDE1; --bark-3:#EDE3D4;
  --bronze:#7F5524; --bronze-2:#653F13;
  /* --cream garde son nom et designe le TEXTE principal. Le renommer
     voudrait dire toucher trente-neuf declarations dans onze fichiers. */
  --cream:#2A231E; --prose:#4C423B; --muted:#6E6154;
  --palm:#4F6B32; --err:#A63A25;
  --line:rgba(138,95,43,.22); --line-2:rgba(138,95,43,.12);
  /* ── Mouvement ──────────────────────────────────────────────────────
     Les trois courbes de la remise motion, declarees une fois. Elles ne
     decrivent pas une couleur : elles decrivent une MANIERE de bouger, et
     deux effets qui n'emploient pas la meme courbe ne se ressemblent pas.
       --ease-out    ce qui arrive et se pose
       --ease-draw   ce qui se trace, un trait qui avance
       --ease-inout  ce qui part et arrive au meme rythme */
  --ease-out:cubic-bezier(.2,.7,.2,1);
  --ease-draw:cubic-bezier(.3,.6,.2,1);
  --ease-inout:cubic-bezier(.6,0,.2,1);
  --max:1240px;
  /* Hauteur de l'en-tete fixe une fois compacte. Cette valeur n'est qu'un REPLI : devinee a 83 px alors que
     l'en-tete compacte en fait 75 a 77 selon la page, la bordure basse de
     La table s'ajoutant aux autres. Un interstice de 6 a 8 px laissait donc
     defiler le contenu a decouvert sous l'en-tete. NAV_BASE remplace cette
     valeur au chargement par la hauteur reellement mesuree ; elle ne sert
     que le temps que le script tourne, ou s'il ne tourne pas du tout. */
  --h-nav:76px;
  --f-display:"Marcellus",Georgia,"Times New Roman",serif;
  --f-body:"Karla",system-ui,-apple-system,sans-serif;
}
"""

# ---------------------------------------------------------------------------
# Le pied de page
# ---------------------------------------------------------------------------
# Une brique a part, parce que DEUX pages ne consomment pas HEAD_CSS :
# La table et Le spa surchargent des regles de base, et une fusion
# complete avait ete tentee puis abandonnee — elle neutralisait
# .btn-solid et rendait l'en-tete de La table opaque.
#
# Elles en portaient donc une COPIE, qui a diverge : le copyright y
# etait a 3,1:1 deja sur le site noir, et le passage au creme l'a
# laisse derriere. Une correction au chassis manquait ces deux pages,
# en silence. Il n'y a plus qu'une source.
#
# Leur fond de pied reste plus profond que --bark-2 : elles
# redeclarent cette seule ligne, chez elles, en clair.
FOOTER_CSS = """
footer{background:var(--bark-2);border-top:1px solid var(--line);padding:74px 0 28px}
.f-grid{display:grid;grid-template-columns:1.6fr 1fr 1fr 1.2fr;gap:44px}
.f-grid h4{font-size:10.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--bronze);margin-bottom:20px;font-weight:700}
.f-grid p{display:block;font-size:13.5px;color:var(--muted);margin-bottom:11px}
.f-grid a{display:block;font-size:13.5px;color:var(--muted);padding:9px 0;transition:.3s}
.f-grid a:hover{color:var(--bronze)}
.f-bot{border-top:1px solid var(--line);margin-top:54px;padding-top:26px;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-size:11.5px;color:var(--muted)}
/* Bouton flottant. NE PAS reutiliser la classe .wa ailleurs : elle impose
   position:fixed et 56x56 en rond. Le lien du panneau de repli la portait,
   et se retrouvait donc arrache du panneau, en pastille au coin de l'ecran —
   le bouton le plus utile du repli etait invisible. Il porte .wa-envoi. */
/* 32 · Le bouton WhatsApp s'etire.
   VERT, a la demande de la cliente (la remise le voulait brun, trait or) :
   c'est le bouton qu'on cherche des yeux, il doit se reconnaitre. Pas le
   vert vif de la marque (#25D366) : le libelle blanc n'y lisait qu'a 2:1.
   #15803D porte le blanc a 5,0:1, et se detache a 4,7:1 du creme, a 3,9:1
   de la nuit. Le pictogramme officiel, en blanc.

   PAS D'ANIMATION DE `width`, malgre la maquette qui en fait une : la
   remise l'interdit noir sur blanc, et une largeur qui bouge relance la
   mise en page a chaque image. La pastille fait donc TOUJOURS 270 px ;
   c'est un clip-path qui n'en montre que 58 au repos, et qui s'ouvre vers
   la gauche au survol. Meme mouvement a l'ecran, rien a recalculer.

   `round 29px` dans le clip : sans lui le bord gauche serait coupe droit
   et la pastille ne serait plus ronde au repos.

   Le libelle entre APRES la pastille — .4s de fondu, .3s de retard — et
   sort tout de suite : au depart on n'attend pas. */
.wa{position:fixed;right:22px;bottom:22px;z-index:90;
  width:270px;height:58px;border-radius:29px;background:#15803D;
  display:flex;align-items:center;justify-content:flex-end;
  box-shadow:0 12px 30px -14px rgba(21,128,61,.7);
  clip-path:inset(0 0 0 212px round 29px);
  transition:clip-path .7s var(--ease-inout)}
.wa .lbl{white-space:nowrap;font-size:11px;letter-spacing:.2em;font-weight:600;
  color:#fff;padding-left:24px;opacity:0;transition:opacity .4s ease}
.wa .rond{flex:none;width:58px;height:58px;display:grid;place-items:center}
/* evenodd : le telephone est un trace DANS la bulle ; rempli comme elle,
   il disparaissait. En creux, il apparait en vert, comme sur le logo. */
.wa svg{width:26px;height:26px;fill:#fff;fill-rule:evenodd}
/* Le survol n'existe pas sur un ecran tactile : la pastille y resterait
   ouverte sur un effleurement, ou ne s'ouvrirait jamais. */
@media(hover:hover){
  .wa:hover,.wa:focus-visible{clip-path:inset(0 0 0 0 round 29px)}
  .wa:hover .lbl,.wa:focus-visible .lbl{opacity:1;transition:opacity .4s ease .3s}
}
@media(max-width:1080px){ .f-grid{grid-template-columns:repeat(2,1fr)} }
@media(max-width:720px){ .f-grid{grid-template-columns:1fr} }
"""

HEAD_CSS = TOKENS + """
/* ── TOUT HERO GARDE DU TEXTE CLAIR ─────────────────────────────────────
   Un hero est pose sur une PHOTOGRAPHIE, sombree par son propre voile —
   pas sur le fond de la page. Le site est passe au creme le 24 septembre :
   sans cette regle, le titre suit --cream, devenu sombre, et disparait dans
   l image.

   LA MESURE DE CONTRASTE NE LE VOIT PAS. .outils/contraste.js compare a une
   couleur de fond, et une photo n en est pas une : il annonçait zero defaut
   sur les 2 806 textes du site pendant que « Ou vous allez dormir »
   s effaçait dans un canape. Ces textes-la se jugent sur capture.

   Une seule regle : les huit heros du site ont le meme defaut, donc la meme
   correction. Les jetons sont redeclares POUR L INTERIEUR du hero, et
   `color` reaffirme — sans quoi la couleur heritee de body, deja calculee,
   ne suit pas. --bark y redevient « ce qui contraste » : sombre. */
.hero{--cream:#F6EEE2;--prose:#D7CBBA;--muted:#C8BAA8;
  --bronze:#DFBB84;--bronze-2:#E8CDA3;--bark:#17100A;color:var(--cream)}

*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
/* L en-tete est fixe : sans ce decalage, un lien vers #reserver amene le haut
   du bloc DERRIERE l en-tete, qui le recouvre. On croit alors que la page a
   trop defile. --h-nav porte la hauteur reellement mesuree au chargement. */
[id]{scroll-margin-top:calc(var(--h-nav) + 18px)}
body{background:var(--bark);color:var(--cream);font-family:var(--f-body);font-size:16.5px;line-height:1.7;overflow-x:hidden;-webkit-font-smoothing:antialiased}
img{max-width:100%;height:auto;display:block}
a{color:inherit;text-decoration:none}
/* Une adresse e-mail est un seul mot de 200 px, qu aucun espace ne coupe.
   Dans une colonne etroite elle n elargit pas seulement sa case : elle
   elargit la grille, puis la page, qui se met a glisser lateralement sous le
   doigt. Invisible sur un grand ecran. Et body{overflow-x:hidden} n y change
   rien : c est html qui porte le defilement de la fenetre, pas body. */
a[href^="mailto:"],a[href^="tel:"]{overflow-wrap:anywhere}
/* Un <select> prend la largeur de son option la plus longue et refuse de
   descendre en dessous : il pousse sa colonne, puis la page. */
input,select,textarea{min-width:0;max-width:100%}
:focus-visible{outline:2px solid var(--bronze);outline-offset:3px}
.wrap{max-width:var(--max);margin:0 auto;padding:0 24px}
.narrow{max-width:900px;margin:0 auto;padding:0 24px}
.eyebrow{font-size:10.5px;letter-spacing:.36em;text-transform:uppercase;color:var(--bronze);font-weight:700;display:block}
h1,h2,h3{font-family:var(--f-display);font-weight:400;line-height:1.1;text-wrap:balance}
h1{font-size:clamp(2.4rem,5.4vw,4rem)}
h2{font-size:clamp(1.7rem,3.2vw,2.5rem)}
h3{font-size:1.2rem}
p{color:var(--prose)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:10px;padding:16px 32px;font-size:11px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;border:1px solid var(--bronze);color:var(--bronze);background:transparent;cursor:pointer;transition:.4s cubic-bezier(.2,.8,.2,1);font-family:var(--f-body)}
.btn:hover{background:var(--bronze);color:var(--bark);transform:translateY(-2px)}
.btn-solid{background:var(--bronze);color:var(--bark)}
.btn-solid:hover{background:var(--bronze-2);border-color:var(--bronze-2)}

/* NAV : un seul element */
/* 08 · Le header se condense. Au-dela de 80 px de defilement il perd sa
   hauteur, son fond devient opaque et un filet le detache du contenu.
   .8s, courbe --ease-out, et REVERSIBLE : la meme transition joue en
   remontant, parce qu'elle porte sur les proprietes, pas sur un sens.

   Mesure a 1440 px : 104 -> 76 px, soit exactement ce que la remise
   annonce a deux pixels pres. Une mesure faite d'abord dans un volet de
   612 px avait donne 96 -> 75 et m'avait fait croire a un ecart : a cette
   largeur la mise en page n'est plus la meme. Une hauteur de header se
   mesure a la largeur ou elle est vue. */
/* A3 · Le header ne change plus de DIMENSION. Sa boite fait 104 px, tout
   le temps. Ce qui se contracte est un CALQUE de fond, par transform :
   scaleY(.75) le ramene a 78 px vus, exactement la valeur de la remise. Le
   contenu remonte de 13 px pour rester centre dans la bande.

   Pourquoi ce detour : animer `padding` ou `height` relance la mise en page
   a chaque image, et la remise l'interdit. Un transform ne coute qu'une
   composition.

   getBoundingClientRect() tient compte du transform : le script qui mesure
   --h-nav lit donc 78 px sur ce calque, et les ancres gardent le bon
   decalage. C'est pour cela que le fond est un ELEMENT et non un
   pseudo-element, qu'on ne peut pas mesurer. */
header{position:fixed;top:0;left:0;right:0;z-index:100;height:104px;
  display:flex;align-items:center}
.hd-fond{position:absolute;left:0;top:0;right:0;height:104px;z-index:0;
  transform-origin:top;background:rgba(251,247,240,.90);backdrop-filter:blur(14px);
  transition:transform .9s var(--ease-inout),background-color .9s ease,
             box-shadow .8s ease}
header.scrolled .hd-fond{transform:scaleY(.75);background:rgba(251,247,240,.97);
  box-shadow:0 1px 0 var(--line)}
.nav{position:relative;z-index:1;width:100%;
  transition:transform .9s var(--ease-inout)}
header.scrolled .nav{transform:translateY(-13px)}
/* Le temps d'une mesure, rien ne bouge — voir le script de --h-nav. */
header.sans-transition,header.sans-transition *{transition:none!important}

/* Menu ouvert : l en-tete devient opaque, et de la couleur du tiroir.
   Sinon le contenu du menu defile DESSOUS et transparait par les 10 pour cent
   qui restent — le logo se melangeait au premier lien. La page, elle, ne
   defile plus quand le menu est ouvert : l en-tete ne passait donc jamais en
   mode defile, et gardait son fond translucide. */
header.menu .hd-fond{background:var(--bark);backdrop-filter:none;
  box-shadow:0 1px 0 var(--line)}
.nav{display:flex;align-items:center;justify-content:space-between;gap:20px}
/* 08 · Au defilement, le logo se reduit a l'EMBLEME — maquette « Motion
   design I » : le logo n'est ni agrandi ni reduit, il est RECADRE par la
   droite, de 177 a 66 px (37 %). Le nom s'efface en glissant vers la
   gauche et l'embleme reste, a sa place exacte.

   1,1 s en --ease-inout, et le bandeau en .9 s --ease-inout, et non le
   --ease-out de la remise : mesure a la molette, --ease-out faisait 90 %
   du mouvement dans les 500 premieres ms — pendant que la page defile
   sous les yeux. L'oeil suit le contenu et rate le logo : la cliente ne
   voyait « pas le mouvement ». En ease-inout, l'essentiel se joue juste
   APRES le coup de molette, quand le regard revient en haut.

   L'embleme est pris DANS le logo, pas dans un second fichier : superpose
   (embleme.svg en masque), il ne tombait jamais pile, et parut tronque.
   Mesure sur le logo bronze comme sur le blanc (729 px) : les
   quatre pieces vont de 0 a 264 px, le nom commence a 285. On coupe au
   milieu du blanc, a 274 px : 62,4 % masques a droite.

   clip-path et non largeur : la regle « pas d'animation de dimensions ». */
.brand img{width:168px;clip-path:inset(0 0 0 0);transition:clip-path 1.1s var(--ease-inout)}
header.scrolled .brand img{clip-path:inset(0 62.4% 0 0)}
/* La signature sous le logo s'efface avec le nom. */
.brand small{transition:opacity .8s ease}
header.scrolled .brand small{opacity:0}

.brand small{display:block;font-size:8px;letter-spacing:.42em;color:var(--bronze);margin-top:6px;padding-left:2px;font-weight:700}
.nav-right{display:flex;align-items:center;gap:18px}
/* 51 · La pastille glisse d'une langue a l'autre (maquette « Motion
   design III » : .6 s, la courbe --ease-inout). Elle est UN calque, pose
   sous les deux boutons, qui se deplace par transform ; les boutons ne
   portent plus de fond. La grille 1fr 1fr rend FR et EN strictement egaux :
   la pastille fait 50 %, elle doit tomber pile sur chacun. */
.lang{display:grid;grid-template-columns:1fr 1fr;position:relative;border:1px solid var(--line)}
.lang::before{content:"";position:absolute;top:0;bottom:0;left:0;width:50%;background:var(--bronze);
  transition:transform .6s var(--ease-inout)}
.lang.en::before{transform:translateX(100%)}
.lang button{position:relative;background:none;border:0;color:var(--muted);font:700 10.5px/1 var(--f-body);letter-spacing:.12em;padding:9px 11px;cursor:pointer;transition:color .3s}
.lang button.on{color:var(--bark)}
.burger{display:flex;align-items:center;gap:12px;background:none;border:0;cursor:pointer;padding:10px 4px;position:relative;z-index:101}
.burger .bars{display:block;width:26px}
.burger .bars span{display:block;height:1.5px;background:var(--cream);margin:6px 0;transition:.35s}
.burger .lbl{font-size:10.5px;letter-spacing:.24em;text-transform:uppercase;font-weight:700;color:var(--cream)}
.burger.open .bars span:nth-child(1){transform:translateY(7.5px) rotate(45deg)}
.burger.open .bars span:nth-child(2){opacity:0}
.burger.open .bars span:nth-child(3){transform:translateY(-7.5px) rotate(-45deg)}
/* 07 · Le menu s'ouvre comme un rideau.
   Le panneau DESCEND — translateY(-101% -> 0) — au lieu d'apparaitre en
   fondu. Les 101 % plutot que 100 : a 100 le bord haut du panneau reste
   sur la ligne de l'ecran et laisse un liseré d'un pixel selon l'arrondi.

   Timings releves dans la maquette, pas devines :
     panneau     transform .9s cubic-bezier(.7,0,.2,1)
     rubriques   transform 1s --ease-out, delai .5s + .07s par rang
     colonne     opacity 1s ease, delai 1s
   La fermeture est plus rapide et sans delai : on ne fait pas attendre
   quelqu'un qui veut partir. */
.drawer{position:fixed;inset:0;background:var(--bark);z-index:99;
  visibility:hidden;overflow-y:auto;
  transform:translateY(-101%);
  transition:transform .55s cubic-bezier(.7,0,.2,1),visibility 0s .55s}
.drawer.open{visibility:visible;transform:translateY(0);
  transition:transform .9s cubic-bezier(.7,0,.2,1),visibility 0s}
.dw-in{min-height:100svh;display:grid;grid-template-columns:1.25fr 1fr;align-items:center;gap:60px;max-width:var(--max);margin:0 auto;padding:130px 24px 60px}
.dw-in nav{display:flex;flex-direction:column}
/* A2 · Chaque rubrique monte derriere SA PROPRE fenetre.
   Le masque etait pose sur le <nav> entier : les liens glissaient les uns
   sur les autres au lieu de surgir chacun de sa ligne, et la bordure du
   dernier coupait le mouvement des autres. C'est donc le lien qui masque,
   et son CONTENU qui translate — la bordure, elle, reste en place. */
.dw-in nav a{
  display:flex;align-items:baseline;gap:22px;padding:16px 0;border-bottom:1px solid var(--line-2);
  font-family:var(--f-display);font-size:clamp(1.45rem,3.2vw,2.4rem);color:var(--cream);
  overflow:hidden;transition:color .3s
}
.dw-in nav a>*{display:inline-block;transform:translateY(110%);
  transition:transform .5s var(--ease-out)}
.drawer.open .dw-in nav a>*{transform:none;transition:transform 1s var(--ease-out)}
.dw-in nav a:hover,.dw-in nav a.on{color:var(--bronze-2)}
.dw-in nav a i{font-style:normal;font-family:var(--f-body);font-size:10px;letter-spacing:.2em;color:var(--bronze);font-weight:700;flex:0 0 auto;opacity:.7}
/* A2 · Le medaillon se trace a l'ouverture du tiroir — la mecanique de
   l'effet 01, avec les delais de la maquette 07 : les filets d'abord a
   1,2 s, le losange a 1,7 s, le signe en fondu a 2,2 s. Le panneau a fini
   de descendre a .9 s : le dessin commence donc apres, pas pendant.

   stroke-dasharray:1 avec pathLength="1" veut dire « un tiret long comme
   tout le trace ». L'offset le pousse hors du cadre, et le ramener a zero
   dessine le trait. */
/* La frise est la DERNIERE du tiroir : rubriques et colonne de droite
   partagent la premiere rangee, qui prend toute la hauteur libre (1fr) ;
   la frise se pose en bas, comme dans la maquette 07. Placee entre les
   deux colonnes, elle ouvrait une rangee et renvoyait la photo dessous. */
.dw-in{grid-template-rows:1fr auto}
.dw-med{grid-column:1/-1;width:360px;max-width:100%;margin:0 auto;
  color:var(--bronze);opacity:.85}
/* Les delais ne vivent que dans l'etat OUVERT. Une transition prend les
   reglages de l'etat d'ARRIVEE : poses sur l'etat de repos, les 1,2 s de
   delai jouaient aussi a la fermeture, et un menu rouvert dans la seconde
   retrouvait son medaillon deja trace, sans le voir se dessiner. */
.dw-med [pathLength]{stroke-dasharray:1;stroke-dashoffset:1;transition:stroke-dashoffset .3s ease}
.dw-med g g [pathLength]{stroke-dashoffset:0}
.dw-med>svg>g>circle,.dw-med>svg>g>g{opacity:0;transition:opacity .3s ease}
.drawer.open .dw-med>svg>g>path{stroke-dashoffset:0}
.drawer.open .dw-med>svg>g>path:nth-last-of-type(2){transition:stroke-dashoffset 1.2s var(--ease-draw) 1.2s}
.drawer.open .dw-med>svg>g>path:nth-last-of-type(1){transition:stroke-dashoffset 1s var(--ease-draw) 1.7s}
.drawer.open .dw-med>svg>g>circle{opacity:1;transition:opacity 1.2s ease 1.2s}
.drawer.open .dw-med>svg>g>g{opacity:1;transition:opacity 1s ease 2.2s}

.dw-side{display:flex;flex-direction:column;gap:26px;
  opacity:0;transition:opacity .3s ease}
.drawer.open .dw-side{opacity:1;transition:opacity 1s ease 1s}
.dw-side .ph{aspect-ratio:4/3;overflow:hidden;background:var(--bark-2)}
.dw-side .ph img{width:100%;height:100%;object-fit:cover}
.dw-side b{display:block;font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:var(--bronze);font-weight:700;margin-bottom:12px}
.dw-side a{display:block;font-size:15px;color:var(--prose);padding:7px 0;transition:.3s}
.dw-side a:hover{color:var(--bronze)}
.dw-side p{font-size:13.5px;color:var(--muted);margin-top:12px}
.dw-side .lang{margin-top:6px;width:max-content}
.dw-side .lang button{padding:15px 20px;font-size:11px}

/* Etats d'envoi des formulaires */
.piege{position:absolute!important;left:-9999px!important;width:1px;height:1px;overflow:hidden}
button[aria-busy="true"]{opacity:.62;cursor:progress}
.secours{display:none;border:1px solid var(--bronze);background:rgba(185,138,80,.07);padding:24px 26px;margin-top:20px}
.secours.on{display:block}
.secours b{display:block;font-family:var(--f-display);font-size:1.2rem;color:var(--bronze-2);margin-bottom:8px}
.secours p{font-size:14px;margin-bottom:16px}
.secours .liens{display:flex;gap:12px;flex-wrap:wrap}
.secours .liens a{display:inline-flex;align-items:center;gap:9px;border:1px solid var(--line);padding:12px 18px;
  font-size:11px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--cream);transition:.3s}
.secours .liens a:hover{border-color:var(--bronze);color:var(--bronze-2)}
.secours .liens a.wa-envoi{background:var(--palm);border-color:var(--palm);color:#0F1508}
.secours .liens a.wa-envoi:hover{filter:brightness(1.1);color:#0F1508}
.err-envoi{display:none;color:var(--err);font-size:13.5px;margin-top:14px}
.err-envoi.on{display:block}

/* Les barres de filtres ne sont plus collantes. Le rideau qui les
   accompagnait — sentinelle, classe « epinglee », 100vh opaques — a resiste
   a trois corrections : une bande de bouts d'images restait visible entre
   l'en-tete et la barre. Le mecanisme dependait de --h-nav, mesuree au
   chargement, alors que la hauteur de l'en-tete varie pendant sa transition
   de 0,45 s. Supprime plutot que reparé une quatrieme fois : une barre qui
   defile avec la page ne peut pas laisser d'intervalle. */

.skip{position:absolute;left:-9999px;top:0;z-index:200;background:var(--bronze);color:var(--bark);
  padding:14px 22px;font-size:11px;font-weight:700;letter-spacing:.2em;text-transform:uppercase}
.skip:focus{left:0}
main{display:block}

.crumb{font-size:11.5px;letter-spacing:.1em;color:var(--muted);margin-bottom:22px}
.crumb a{padding:6px 0;display:inline-block}
.crumb a:hover{color:var(--bronze)}
.crumb span{color:var(--bronze)}

""" + FOOTER_CSS + """

.js .reveal{opacity:0;transform:translateY(28px);transition:opacity .9s cubic-bezier(.2,.8,.2,1),transform .9s cubic-bezier(.2,.8,.2,1)}
.js .reveal.in{opacity:1;transform:none}
/* transition-delay aussi. Couper la seule duree laissait vivre les delais :
   sous « reduire les animations », le losange d'un medaillon attendait ses
   0,9 s avant de sauter a l'etat final. Ce n'est pas un etat final
   immediat, c'est un etat final en retard.

   Et *::before, *::after : l'etoile seule ne selectionne PAS les
   pseudo-elements. Le galon, qui se tisse dans son ::before, gardait ses
   1,4 s sous « reduire les animations ». */
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition-duration:.01ms!important;transition-delay:0s!important}.js .reveal,.dw-in nav a{opacity:1;transform:none}}

@media(max-width:1080px){
  .dw-in{grid-template-columns:1fr;grid-template-rows:none;gap:40px;align-content:start}
  .dw-side .ph{display:none}
}
@media(max-width:720px){
  .burger .lbl{display:none}
  .nav-right .lang{display:none}
  .dw-in{padding:110px 24px 50px}
}
"""

# ── 18 · Le logo se construit ────────────────────────────────────────────
# L'ecran de chargement, une fois par session. Timings de la maquette
# « Motion design I » : les quatre pieces de l'embleme montent une a une
# (translateY 18 % -> 0, 1,1 s --ease-out ; opacite .9 s ; .16 s d'ecart),
# puis le nom se devoile en clip-path (1,3 s --ease-inout). La signature
# « Le reve africain » suit en fondu. La maquette va jusqu'a 3,1 s ; la
# remise plafonne l'ecran a 2,5 s. Le nom part donc a .7 s (maquette .8),
# la signature a 1,4 s pour .6 s : tout est pose a 2 s, l'ecran s'efface
# en .3 s. Le navigateur demarre les animations 0,1 a 0,15 s apres avoir
# peint l'ecran quand la page charge encore : ce dixieme gagne les absorbe.
#
# Il ne joue PAS :
#   - apres la premiere page de la session (sessionStorage) ;
#   - sous « reduire les animations » : l'etat final d'un ecran de
#     chargement, c'est pas d'ecran du tout ;
#   - sur un retour arriere ou un rechargement : la page est deja connue ;
#   - si la page a fini de charger avant que le logo n'arrive.
#
# Le logo (104 Ko) n'est telecharge que s'il doit jouer : l'integrer a
# chaque page l'aurait fait payer a toutes les visites, pour une seule.
# S'il n'est pas la en 900 ms, on n'attend pas. Un clic, un toucher ou une
# touche levent l'ecran tout de suite.
#
# Tant que le logo n'est pas arrive, un simple aplat (html.intro::after)
# cache la page, pour qu'on ne la voie pas surgir PUIS disparaitre. Si le
# script casse, cet aplat se retire seul a 3 s : on ne bloque jamais la
# page derriere un ecran fige. Les calques sont animes par un <g> parent,
# qui n'ecrase pas le transform que chaque trace porte deja.
INTRO = """<style>
html.intro::after{content:"";position:fixed;inset:0;z-index:1000;background:var(--bark);animation:intro-secours 0s linear 3s forwards}
@keyframes intro-secours{to{visibility:hidden}}
.intro-ecran{position:fixed;inset:0;z-index:1000;display:grid;place-items:center;background:var(--bark);color:var(--bronze);transition:opacity .3s ease}
.intro-ecran.part{opacity:0;pointer-events:none}
.intro-ecran svg{width:min(480px,76vw);height:auto;overflow:visible}
.intro-ecran .i0,.intro-ecran .i1,.intro-ecran .i2,.intro-ecran .i3{animation:intro-monte 1.1s var(--ease-out) both,intro-parait .9s ease both}
.intro-ecran .i1{animation-delay:.16s}.intro-ecran .i2{animation-delay:.32s}.intro-ecran .i3{animation-delay:.48s}
.intro-ecran .i4{animation:intro-devoile 1.3s var(--ease-inout) .7s both}
.intro-ecran .i5{animation:intro-signe .6s var(--ease-out) 1.4s both,intro-parait .6s ease 1.4s both}
@keyframes intro-monte{from{transform:translateY(18%)}}
@keyframes intro-signe{from{transform:translateY(30%)}}
@keyframes intro-parait{from{opacity:0}}
@keyframes intro-devoile{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0)}}
</style>
<script>(function(){
var d=document,h=d.documentElement;
try{
  if(sessionStorage.getItem('evn-intro'))return;
  if(!window.fetch||!window.matchMedia||matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  var nav=performance.getEntriesByType?performance.getEntriesByType('navigation')[0]:null;
  if(nav&&nav.type&&nav.type!=='navigate')return;
  if(d.readyState==='complete')return;
  sessionStorage.setItem('evn-intro','1');
}catch(e){return}
h.classList.add('intro');h.setAttribute('data-intro','');
/* Tant que data-intro est la, les effets au defilement (EVN_AU_SCROLL)
   attendent : ce qui est deja a l'ecran jouerait SOUS l'ecran de
   chargement, et serait fini avant qu'on le voie. */
function finIntro(){if(h.hasAttribute('data-intro')){h.removeAttribute('data-intro');d.dispatchEvent(new Event('evn-intro-fin'))}}
var fini=false;
function lever(){if(!fini){fini=true;h.classList.remove('intro')}finIntro()}
var limite=setTimeout(lever,900);
fetch('img/logo-calques.svg').then(function(r){return r.ok?r.text():Promise.reject(r.status)}).then(function(svg){
  function poser(){
    if(fini)return;
    clearTimeout(limite);
    if(d.readyState==='complete'){lever();return}
    fini=true;
    var e=d.createElement('div');
    e.className='intro-ecran';
    e.setAttribute('aria-hidden','true');
    e.innerHTML=svg;
    ['pilier-1','traverse','pilier-2','pilier-3','nom','signature'].forEach(function(id,i){
      var p=e.querySelector('#'+id);if(!p)return;
      p.removeAttribute('id');
      var g=d.createElementNS('http://www.w3.org/2000/svg','g');
      g.setAttribute('class','i'+i);
      p.parentNode.insertBefore(g,p);g.appendChild(p);
    });
    var s=e.querySelector('svg');if(s){s.removeAttribute('role');s.removeAttribute('aria-label')}
    d.body.appendChild(e);
    h.classList.remove('intro');
    /* Le depart suit la FIN de l'animation, pas une minuterie : le
       navigateur ne peint rien avant d'avoir ses polices, et les
       animations attendent cette premiere image. Une minuterie partie a
       l'insertion coupait le logo a mi-construction. Deux filets : 2,2 s
       apres la premiere image peinte (2,5 s fondu compris, quoi qu'il
       arrive), et 3,5 s si l'onglet est en arriere-plan et ne peint rien. */
    var parti=false,t=setTimeout(partir,3500);
    requestAnimationFrame(function(){if(!parti){clearTimeout(t);t=setTimeout(partir,2200)}});
    var sig=e.querySelector('.i5');if(sig)sig.addEventListener('animationend',partir);
    function partir(){
      if(parti)return;parti=true;clearTimeout(t);
      e.classList.add('part');finIntro();
      setTimeout(function(){if(e.parentNode)e.parentNode.removeChild(e)},300);
    }
    e.addEventListener('pointerdown',partir);
    d.addEventListener('keydown',partir,{once:true});
  }
  if(d.body)poser();else d.addEventListener('DOMContentLoaded',poser);
}).catch(lever);
})();</script>"""

# Garde-fou : voir « Le contenu ne depend pas du JavaScript » dans le README.
HEAD = """<script>document.documentElement.className+=" js";setTimeout(function(){if(!window.__reveal){document.querySelectorAll(".reveal").forEach(function(e){e.classList.add("in")})}},3000)</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Karla:wght@300;400;500;600;700&display=swap" rel="stylesheet">"""
HEAD += '\n' + INTRO

NL_ = chr(10)

LINKS = [
 ('01','chambres.html','n1','Chambres &amp; Suites'),
 ('02','experiences.html','n2','Expériences'),
 ('03','carte.html','n3','La table'),
 ('04','spa.html','n4','Le spa'),
 # Une seule entree pour tout ce qui est offre. Une page « Evenements »
 # separee a ete essayee puis retiree : trois de ses cinq entrees etaient
 # deja ici, et deux libelles de menu disaient « offres ».
 ('05','circuits.html','n5','Offres &amp; Événements'),
 ('06','seminaires.html','n6','Séminaires &amp; groupes'),
 ('07','galerie.html','n7','Galerie'),
 ('08','a-propos.html','n8','À propos'),
 ('09','informations-utiles.html','n9','Informations utiles'),
 ('10','contact.html','n10','Contact'),
 ('11','reserver.html','n11','Réserver'),
]


# ── Signature textile ───────────────────────────────────────────────────
# CE MORCEAU N'EST PAS DANS HEAD_CSS. Les cinq pages qui portent une
# touche l'ajoutent a leur propre feuille ; les dix-sept autres n'en
# recoivent pas un octet, et ne changent donc pas d'une ligne.
#
# L'or des motifs est declare ICI, une fois. Ce n'est pas un jeton de
# la palette : un jeton se declare dans :root, donc dans TOKENS, donc
# dans les vingt-deux pages — pour un ornement qui n'en concerne que
# cinq, et qui ne porte jamais de texte.
PAGNE_CSS = """/* ── Signature textile ────────────────────────────────────────────────
   Cinq touches, sur cinq pages, et nulle part ailleurs. Ces utilitaires
   vivent ici pour qu'il n'y en ait qu'un exemplaire ; les emplacements,
   eux, sont ecrits dans chaque generateur.

   TROIS REGLES QUI NE SE NEGOCIENT PAS :
     - jamais sous un texte, un bouton ou un champ ;
     - decoratif : aria-hidden, et aucun evenement de pointeur ;
     - pas d'animation en boucle. L'apparition reutilise .reveal, qui
       respecte deja prefers-reduced-motion. */
.pagne{pointer-events:none;-webkit-user-select:none;user-select:none}

/* Le damas : un ton sur ton a 9 %, pose DERRIERE, dans un vide. Le fondu
   le fait disparaitre avant d'atteindre la colonne de texte — sans lui, le
   motif s'arrete net et se voit. */
/* z-index:-1, et non 0. Dans un contexte d'empilement, un element POSITIONNE
   a z-index:0 se peint AU-DESSUS du texte statique voisin : le damas serait
   passe par-dessus le titre. A -1 il reste derriere le contenu et devant le
   fond — a condition que son parent ouvre un contexte, d'ou le
   `position:relative;z-index:0` pose sur chaque bloc d'accueil. */
.pagne-damas{position:absolute;z-index:-1;opacity:.09;
  background:url(img/pagne/damas-pagne.svg) repeat;background-size:252px 158px}
.pagne-damas.vers-gauche{-webkit-mask-image:linear-gradient(90deg,transparent,#000 50%);
  mask-image:linear-gradient(90deg,transparent,#000 50%)}
.pagne-damas.au-centre{-webkit-mask-image:radial-gradient(ellipse 50% 50% at 50% 50%,#000 30%,transparent 100%);
  mask-image:radial-gradient(ellipse 50% 50% at 50% 50%,#000 30%,transparent 100%)}

/* Le galon : une bande de 20 px, en haut d'une carte, DANS sa bordure. */
.pagne-galon{position:absolute;top:0;left:0;right:0;height:20px;opacity:.8}
/* Le dessin vit dans un pseudo-element, et c'est LUI qui se decoupe.
   L'element, lui, garde une boite entiere : c'est elle qu'observe
   EVN_AU_SCROLL. Chrome applique le clip-path au calcul d'intersection —
   un galon entierement « detisse » etait donc juge invisible, ratio 0, et
   ne recevait jamais `vu` : il attendait d'etre vu pour se tisser, et ne
   pouvait etre vu que tisse. Sur un ecran ou la carte est sous la ligne
   de flottaison, il ne serait jamais apparu. */
.pagne-galon::before{content:"";position:absolute;inset:0;
  background:url(img/pagne/galon-pagne.svg) repeat-x center;background-size:48px 20px}

/* Les medaillons sont en SVG inline : leur trait suit `color`. */
.pagne-med{display:block;margin:0 auto;color:#A88560}
.pagne-med svg{display:block;width:100%;height:auto}
.pagne-med.or-logo{color:var(--bronze)}

/* ══ Etape 3 du motion ═══════════════════════════════════════════════
   Les motifs ne sont plus la au chargement : ils ARRIVENT, une fois,
   quand on les atteint. EVN_AU_SCROLL pose la classe `vu` au seuil de
   0,3 et cesse d'observer.

   01 · LE MEDAILLON SE DESSINE. stroke-dasharray:1 avec pathLength="1"
   veut dire « un tiret long comme tout le trace » ; l'offset le pousse
   hors du cadre, et le ramener a zero dessine le trait.

   Les deux familles de medaillon n'ont pas la meme structure : le
   compact n'a qu'un losange, les larges ont deux filets PUIS un losange.
   D'ou nth-last-of-type, qui compte depuis la fin : le losange est
   toujours le dernier trace direct, les filets l'avant-dernier quand ils
   existent. Un nth-of-type(1) aurait dessine le losange du compact au
   rythme des filets des autres. */
/* :where(:not(.dw-med)) — le medaillon du TIROIR est aussi un .pagne-med,
   mais il obeit a l'ouverture du menu, pas au defilement. :where exclut
   SANS ajouter de specificite : un simple :not() en ajoutait, et la regle
   « masque » passait devant la regle « vu -> trace ». Les medaillons
   recevaient `vu` et restaient invisibles.

   On vise la STRUCTURE, pas les balises : le signe est le groupe imbrique
   (g>g). Dans le medaillon soleil il n'est fait que d'un cercle et de huit
   <line> — viser `g g path` laissait ses rayons masques pour toujours. */
.pagne-med:where(:not(.dw-med)) [pathLength]{stroke-dasharray:1;stroke-dashoffset:1}
.pagne-med:where(:not(.dw-med)) g g [pathLength]{stroke-dashoffset:0}
.pagne-med:where(:not(.dw-med))>svg>g>path:nth-last-of-type(2){transition:stroke-dashoffset 1.2s var(--ease-draw) .15s}
.pagne-med:where(:not(.dw-med))>svg>g>path:nth-last-of-type(1){transition:stroke-dashoffset 1s var(--ease-draw) .9s}
.pagne-med:where(:not(.dw-med))>svg>g>circle{opacity:0;transition:opacity 1.2s ease .15s}
/* Le signe n'est pas dessine : il apparait, trop court et trop replie pour
   qu'un trace s'y lise. */
.pagne-med:where(:not(.dw-med))>svg>g>g{opacity:0;transition:opacity 1s ease 1.5s}
.pagne-med.vu>svg>g>path{stroke-dashoffset:0}
.pagne-med.vu>svg>g>circle,.pagne-med.vu>svg>g>g{opacity:1}

/* 02 · LE DAMAS SE REVELE. Il monte de 16 px en s'allumant — 2,8 s, le
   temps qu'il faut pour qu'un ton sur ton a 9 % ne surgisse pas. */
.pagne-damas{opacity:0;transform:translateY(16px);
  transition:opacity 2.8s var(--ease-draw),transform 2.8s var(--ease-out)}
.pagne-damas.vu{opacity:.09;transform:none}

/* 03 · LE GALON SE TISSE, de gauche a droite. */
.pagne-galon::before{clip-path:inset(0 100% 0 0);
  transition:clip-path 1.4s var(--ease-inout) .2s}
.pagne-galon.vu::before{clip-path:inset(0)}

/* 43 · LE DAMAS SOUS LA LAMPE. Un second calque, plus dense, que l'on ne
   voit que sous la souris : le masque est un rond de 220 px qui la suit.
   Invisible hors survol, et absent partout ou il n'y a pas de souris. */
.pagne-lampe{display:none}
@media(hover:hover) and (min-width:768px){
  /* Pas de classe .pagne-damas sur ce calque : l'observateur lui poserait
     `vu`, et .pagne-damas.vu le ramenerait a .09 par-dessus son .16. */
  .pagne-lampe{display:block;position:absolute;z-index:-1;opacity:.16;
    background:url(img/pagne/damas-pagne.svg) repeat;background-size:252px 158px;
    -webkit-mask-image:radial-gradient(circle 220px at var(--x,-999px) var(--y,-999px),#000,transparent);
    mask-image:radial-gradient(circle 220px at var(--x,-999px) var(--y,-999px),#000,transparent)}
}

@media(max-width:767px){
  /* Sur un telephone il n'y a plus de vide : le damas n'a plus d'endroit
     ou vivre sans passer sous le texte. On le retire. */
  .pagne-damas{display:none}
  .pagne-med.large{max-width:240px}
}
"""


# Le JS des motifs. Il va avec PAGNE_CSS : les cinq pages qui portent une
# touche l'ajoutent, les dix-sept autres n'en recoivent pas un octet.
PAGNE_JS = """
/* Les motifs arrivent au defilement, une fois. EVN_AU_SCROLL tient le
   seuil et l'unicite — voir la base du mouvement. */
EVN_AU_SCROLL('.pagne-med:not(.dw-med),.pagne-damas,.pagne-galon','vu');

/* 43 · Le damas sous la lampe. Le masque suit la souris, mais AVEC DU
   RETARD : on interpole de 12 % par image vers la position reelle. Sans
   ce lissage le rond colle au curseur et le motif clignote a chaque
   saccade de la main ; avec, il traine comme une lampe qu'on deplace.

   Une seule boucle, qui s'arrete quand la souris quitte le bloc : pas
   d'animation en boucle, la remise l'interdit. */
(function(){
  var l = document.querySelector('.pagne-lampe');
  if (!l || !matchMedia('(hover: hover) and (min-width: 768px)').matches) return;
  var hote = l.parentNode, x = 0, y = 0, cx = 0, cy = 0, tourne = false;
  function image(){
    cx += (x - cx) * .12; cy += (y - cy) * .12;
    l.style.setProperty('--x', cx.toFixed(1) + 'px');
    l.style.setProperty('--y', cy.toFixed(1) + 'px');
    /* On s'arrete des que le rond a rejoint la souris : une boucle qui
       tourne sur un dixieme de pixel ne sert plus qu'a chauffer. */
    if (Math.abs(x - cx) > .5 || Math.abs(y - cy) > .5) requestAnimationFrame(image);
    else tourne = false;
  }
  hote.addEventListener('pointermove', function(e){
    var r = l.getBoundingClientRect();
    x = e.clientX - r.left; y = e.clientY - r.top;
    if (!tourne) { tourne = true; requestAnimationFrame(image); }
  });
  hote.addEventListener('pointerleave', function(){
    x = -999; y = -999;
    if (!tourne) { tourne = true; requestAnimationFrame(image); }
  });
}());
"""


# ── 33 · La confirmation se dessine ─────────────────────────────────────
# Un cercle se trace, puis la coche, puis le message arrive. Timings de la
# maquette « Motion design II » : cercle 1,2 s --ease-inout des .2 s, coche
# .7 s --ease-out a 1,2 s, message en fondu et 10 px de montee a 1,7 s.
#
# Pose UNE fois ici, employe par le tunnel, le contact et les seminaires.
# Les textes ne changent pas — CONF_TITRE et CONF_GESTE restent ce qu'ils
# sont, en particulier en mode WhatsApp : seul le dessin s'ajoute.
CONF_SVG = ('<svg class="conf-trait" viewBox="0 0 80 80" aria-hidden="true" focusable="false">'
            '<circle cx="40" cy="40" r="38" pathLength="1"/>'
            '<path d="M26 41L36 51L55 30" pathLength="1"/></svg>')
CONF_CSS = """
/* 33 · Des @keyframes et non des transitions, pour deux raisons :
   - l'ecran de confirmation passe de display:none a visible, et une
     transition ne part pas d'un element qui n'etait pas rendu ;
   - l'etat de BASE est l'etat final. Sous « reduire les animations », la
     garde pose animation:none, et l'on voit directement le cercle ferme,
     la coche et le message — sans rien a attendre. */
.conf-trait{display:block;width:72px;height:72px;margin:0 auto 26px;fill:none;
  stroke:var(--bronze);stroke-width:1.2;stroke-linecap:round;stroke-linejoin:round}
.conf-trait circle{stroke-dasharray:1;transform:rotate(-90deg);transform-origin:40px 40px;
  animation:conf-trace 1.2s var(--ease-inout) .2s both}
.conf-trait path{stroke-dasharray:1;animation:conf-trace .7s var(--ease-out) 1.2s both}
/* Dans l'encadre du contact et des seminaires, le dessin se fait plus
   petit et s'aligne sur le texte, a gauche. */
.sent .conf-trait{width:52px;height:52px;margin:0 0 14px}
.conf-msg{animation:conf-apparait 1s ease 1.7s both,conf-monte 1s var(--ease-out) 1.7s both}
@keyframes conf-trace{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes conf-apparait{from{opacity:0}}
@keyframes conf-monte{from{transform:translateY(10px)}}
"""

# ── Les medaillons de la signature textile ───────────────────────────────
# Ils sont INLINES, et non poses en <img>, parce que leur trait est en
# currentColor : c'est ce qui leur permet de prendre l'or des motifs a un
# endroit et le brun du logo a un autre, sans deuxieme fichier.
#
# Le dessin se LIT dans le fichier au moment de la generation plutot que
# d'etre recopie ici. Une copie diverge ; celle-ci se deduit, et le jour ou
# le SVG change, les pages changent avec lui a la regeneration.
_MEDAILLONS = {
    'carre':       'medaillon-spirale-carree.svg',       # 120 x 40
    'carre-large': 'medaillon-spirale-carree-large.svg',  # 360 x 40, avec filets
    'soleil':      'medaillon-soleil-large.svg',          # 360 x 40, avec filets
}
_MED_CACHE = {}


def medaillon(variante, classes='', style=''):
    """Un medaillon en SVG inline, decoratif et hors du flux de lecture."""
    if variante not in _MEDAILLONS:
        raise ValueError('medaillon inconnu : %s' % variante)
    if variante not in _MED_CACHE:
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'img', 'pagne', _MEDAILLONS[variante])
        svg = io.open(chemin, encoding='utf-8').read().strip()
        # Ni largeur ni hauteur en dur : c'est le conteneur qui decide, et
        # le viewBox qui garde les proportions.
        svg = re.sub(r'\s(width|height)="\d+"', '', svg, count=2)
        svg = svg.replace('<svg ', '<svg focusable="false" ', 1)
        # pathLength="1" sur chaque trace : stroke-dasharray:1 vaut alors
        # « toute la longueur », quelle que soit la longueur reelle. C'est
        # ce qui permet de dessiner le medaillon d'un seul reglage.
        svg = re.sub(r'<(path|line|polyline|rect)\b', r'<\1 pathLength="1"', svg)
        _MED_CACHE[variante] = svg
    return '<span class="pagne pagne-med %s" aria-hidden="true"%s>%s</span>' % (
        classes, (' style="%s"' % style) if style else '', _MED_CACHE[variante])


# Le logo BRONZE, pas le blanc. L'en-tete est rgba(251,247,240,.90) a
# toutes les hauteurs de defilement, et le pied est --bark-2 : deux fonds
# clairs. Le logo blanc y avait disparu depuis le passage au creme — un
# fantome sur l'accueil, rien du tout sur les dix-huit autres pages.
# La table et Le spa gardent le blanc : leurs deux fonds restent nocturnes.
def header(cta_href, cta_label, cta_key='cta'):
    return '''<a class="skip" href="#contenu">Aller au contenu</a>
<header id="hd">
  <div class="hd-fond" aria-hidden="true"></div>
  <div class="wrap nav">
    <a href="index.html" class="brand" aria-label="Hôtel Evannath, accueil">
      <img src="img/opt/logo-bronze.png" alt="Hôtel Evannath" width="729" height="176">
      <small>LE RÊVE AFRICAIN</small>
    </a>
    <div class="nav-right">
      <div class="lang"><button class="on" data-lang="fr">FR</button><button data-lang="en">EN</button></div>
      <a href="%s" class="btn btn-solid" data-t="%s">%s</a>
      <button class="burger" id="bg" aria-label="Ouvrir le menu" aria-expanded="false" aria-controls="dw">
        <span class="lbl" data-t="mn">Menu</span>
        <span class="bars"><span></span><span></span><span></span></span>
      </button>
    </div>
  </div>
</header>''' % (cta_href, cta_key, cta_label)

def liens_nav(current=''):
    """Les entrees du tiroir, rendues depuis LINKS.

    Les trois pages a gabarit — accueil, La table, Le spa — recopiaient ce
    bloc en dur. Ajouter une entree a la navigation les manquait donc en
    silence, et le controle 10 du verificateur ne le voyait qu'apres coup.
    Elles consomment desormais le meme rendu que les autres.
    """
    return NL_.join(
        '      <a href="%s"%s><i>%s</i><span data-t="%s">%s</span></a>'
        % (href, ' class="on"' if href == current else '', num, key, lab)
        for num, href, key, lab in LINKS)


def drawer(current='', photo='gal-art-lanterne', alt='Lanterne de rotin de l\'Hôtel Evannath'):
    rows = []
    for num, href, key, label in LINKS:
        cls = ' class="on"' if href == current else ''
        rows.append('      <a href="%s"%s><i>%s</i><span data-t="%s">%s</span></a>' % (href, cls, num, key, label))
    return '''<div class="drawer" id="dw">
  <div class="dw-in">
    <nav aria-label="Navigation principale">
%s
    </nav>
    <aside class="dw-side">
      <div class="ph"><picture><source srcset="img/opt/%s.webp" type="image/webp">
        <img src="img/opt/%s.jpg" width="1100" height="733" alt="%s" loading="lazy"></picture></div>
      <div>
        <b data-t="dr">Réservations</b>
        <a href="tel:+2250151527575">+225 01 51 52 75 75</a>
        <a href="mailto:{{MAIL}}">{{MAIL}}</a>
        <a href="https://wa.me/{{WA}}" target="_blank" rel="noopener">WhatsApp</a>
        <p>Assinie PK 19 · Comoé · Côte d'Ivoire</p>
      </div>
      <div class="lang"><button class="on" data-lang="fr">FR</button><button data-lang="en">EN</button></div>
    </aside>
%s
  </div>
</div>

<main id="contenu">'''.replace('{{WA}}', WA).replace('{{MAIL}}', MAIL) % ('\n'.join(rows), photo, photo, alt, medaillon('carre-large', 'dw-med'))

# Le bouton WhatsApp flottant, ecrit UNE fois : l'accueil, La table et le
# Spa en portaient une copie ancienne, sans libelle — la pastille s'y
# deployait vide au survol.
WA_BOUTON = '''<a class="wa" href="https://wa.me/{{WA}}" target="_blank" rel="noopener" aria-label="Nous écrire sur WhatsApp">
  <span class="lbl" aria-hidden="true">ÉCRIRE SUR WHATSAPP</span>
  <span class="rond"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.5 14.4c-.3-.1-1.7-.9-2-1-.3-.1-.5-.1-.7.1-.2.3-.7 1-.9 1.2-.2.2-.3.2-.6.1-1.7-.9-2.9-1.6-4-3.5-.3-.5.3-.5.9-1.6.1-.2 0-.4 0-.5s-.7-1.6-.9-2.2c-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.5s1.1 2.9 1.2 3.1c.1.2 2.1 3.3 5.2 4.6 1.9.8 2.7.9 3.6.8.6-.1 1.7-.7 2-1.4.2-.7.2-1.2.2-1.4-.1-.1-.3-.2-.6-.3M12 2a10 10 0 00-8.6 15L2 22l5.2-1.4A10 10 0 1012 2z"/></svg></span>
</a>'''

FOOTER = '''</main>

<footer>
  <div class="wrap">
    <div class="f-grid">
      <div>
        <img src="img/opt/logo-bronze.png" alt="Hôtel Evannath" width="729" height="176" style="width:180px;margin-bottom:8px">
        <p style="font-size:8.5px;letter-spacing:.42em;color:var(--bronze);font-weight:700;margin-bottom:18px">LE RÊVE AFRICAIN</p>
        <p style="max-width:300px">46 chambres et suites face à la lagune Aby, à Assinie. Réservation directe, meilleur tarif garanti, réception ouverte 24 h/24.</p>
      </div>
      <div><h4>Navigation</h4><a href="chambres.html">Chambres</a><a href="experiences.html">Expériences</a><a href="carte.html">La table</a><a href="circuits.html">Offres &amp; Événements</a><a href="spa.html">Spa</a><a href="a-propos.html">À propos</a><a href="contact.html">Contact</a></div>
      <div><h4>Informations</h4><a href="informations-utiles.html">Informations utiles</a><a href="seminaires.html">Séminaires &amp; groupes</a><a href="informations-utiles.html#reserver">Conditions d'annulation</a><a href="recrutement.html">Nous rejoindre</a><a href="mentions-legales.html">Mentions légales</a></div>
      <div><h4>Contact</h4>
        <a href="tel:+2252721731265">+225 27 21 73 12 65</a>
        <a href="tel:+2250151527575">+225 01 51 52 75 75</a>
        <a href="mailto:{{MAIL}}">{{MAIL}}</a>
        <a href="https://www.facebook.com/evannathhotel" target="_blank" rel="noopener">Facebook — 21 K abonnés</a>
      </div>
    </div>
    <div class="f-bot"><span>© 2026 Hôtel Evannath — Assinie, Côte d'Ivoire</span><span>Assinie · Comoé · Côte d'Ivoire</span></div>
  </div>
</footer>

''' + WA_BOUTON

# Le JS de navigation est decoupe pour que chaque page ne prenne que ce dont
# elle a besoin, sans qu aucune n ait a en recopier une ligne.
#   NAV_BASE     en-tete qui se compacte, tiroir plein ecran, touche Echap
#   COLLANTE_JS  rideau des barres collantes (inerte s il n y a pas de barre)
#   REVEAL_JS    apparition au defilement, version standard
# NAV_JS reste la somme des trois : les generateurs existants ne changent pas.

# Le pied de page et le bouton flottant portent le numero du moment.
FOOTER = FOOTER.replace('{{WA}}', WA).replace('{{MAIL}}', MAIL)

NAV_BASE = r"""/* ── Base du mouvement ────────────────────────────────────────────────
   Un seul observateur pour tous les effets au defilement : seuil 0,3, et
   UNE SEULE FOIS par element — il cesse d'observer des qu'il a pose sa
   classe. Sans cela un element qui entre et ressort rejouerait, et la
   remise l'interdit : « aucune boucle ».

   Sous prefers-reduced-motion, la classe est posee tout de suite : l'etat
   final, sans transition. La feuille coupe deja les durees ; ici on
   s'assure que l'etat final EXISTE, meme si l'observateur ne tourne pas.

   Aucun effet ne s'en sert encore — 01, 02 et 03 viendront a l'etape 3.
   Il est pose maintenant parce que c'est lui qui decide du seuil et de
   l'unicite, et que trois effets qui s'observent chacun a leur facon ne
   se declenchent jamais ensemble. */
window.EVN_AU_SCROLL=function(selecteur,classe){
  /* L'ecran de chargement (18) couvre la page : on attend qu'il se leve.
     6 s : filet, si son script s'est arrete en route. */
  if(document.documentElement.hasAttribute('data-intro')){
    var fait=false,rel=function(){if(fait)return;fait=true;document.documentElement.removeAttribute('data-intro');EVN_AU_SCROLL(selecteur,classe)};
    document.addEventListener('evn-intro-fin',rel);setTimeout(rel,6000);return;
  }
  var els=[].slice.call(document.querySelectorAll(selecteur));
  if(!els.length)return;
  var c=classe||'vu';
  if(!('IntersectionObserver' in window)||matchMedia('(prefers-reduced-motion: reduce)').matches){
    els.forEach(function(e){e.classList.add(c)});return;
  }
  /* isIntersecting est vrai des le PREMIER pixel visible : le tester seul
     declenchait l'effet quand l'element pointait a peine en bas de
     l'ecran — les lanternes etaient deja allumees quand on arrivait
     devant. C'est le seuil de 30 % qui decide. Un element plus haut que
     l'ecran n'atteint jamais 30 % de lui-meme : on compte alors 30 % de
     l'ecran. D'ou plusieurs seuils, pour etre rappele en chemin. */
  var io=new IntersectionObserver(function(es){
    es.forEach(function(e){
      var vu=e.intersectionRatio>=.299||(e.rootBounds&&e.intersectionRect.height>=e.rootBounds.height*.3);
      if(!vu)return;
      e.target.classList.add(c);io.unobserve(e.target);
    })
  },{threshold:[0,.1,.2,.3]});
  els.forEach(function(e){io.observe(e)});
};

var hd=document.getElementById('hd');
addEventListener('scroll',function(){hd.classList.toggle('scrolled',scrollY>80)},{passive:true});

var bg=document.getElementById('bg'),dw=document.getElementById('dw');
var dwLinks=[].slice.call(dw.querySelectorAll('nav a'));
function toggleMenu(){
  var o=dw.classList.toggle('open');
  hd.classList.toggle('menu',o);
  bg.classList.toggle('open',o);
  bg.setAttribute('aria-expanded',o);
  bg.setAttribute('aria-label',o?'Fermer le menu':'Ouvrir le menu');
  document.body.style.overflow=o?'hidden':'';
  /* .5s puis .07s par rang — maquette « Motion design I », effet 07.
     Le delai va sur le CONTENU du lien, qui est ce qui bouge : le lien,
     lui, ne fait plus que masquer. A la fermeture, aucun delai — on ne
     retient pas quelqu'un qui part. */
  dwLinks.forEach(function(a,i){
    [].forEach.call(a.children,function(c){c.style.transitionDelay=o?(500+i*70)+'ms':'0ms'});
  });
  if(o){
    /* Le focus entre dans le tiroir. Sans cela, la tabulation continue
       dans la page qui est DERRIERE, invisible et bloquee au defilement :
       on tabule a l'aveugle. */
    setTimeout(function(){var p=dw.querySelector('nav a');if(p)p.focus()},120);
  }else{
    bg.focus();
  }
}
bg.onclick=toggleMenu;
dwLinks.forEach(function(a){a.onclick=function(){if(dw.classList.contains('open'))toggleMenu()}});

/* Le piege a focus. Tant que le tiroir est ouvert, la tabulation tourne
   entre ses elements : le bouton Menu, les rubriques, les liens de la
   colonne contact. Echap rend la main, et le focus retourne au bouton. */
addEventListener('keydown',function(e){
  if(!dw.classList.contains('open'))return;
  if(e.key==='Escape'){toggleMenu();return}
  if(e.key!=='Tab')return;
  var f=[bg].concat([].slice.call(dw.querySelectorAll('a[href],button:not([disabled])')))
    .filter(function(n){return n.offsetParent!==null||n===bg});
  if(!f.length)return;
  var premier=f[0],dernier=f[f.length-1];
  if(e.shiftKey&&document.activeElement===premier){e.preventDefault();dernier.focus()}
  else if(!e.shiftKey&&document.activeElement===dernier){e.preventDefault();premier.focus()}
});

/* Films d'ambiance -------------------------------------------------------
   On ne charge un film que si cela a du sens : ecran large, connexion qui
   n'est ni en 2G ni en economie de donnees, et pas de demande de mouvement
   reduit. Sinon l'affiche du <video> reste affichee et pas un octet ne part.
   L'appel se fait apres le chargement de la page : au moment ou le script
   est lu, la largeur de la fenetre n'est pas toujours connue. */
function filmAmbiance(el, sources, alors){
  if(!el || el.dataset.decide) return;
  el.dataset.decide='1';
  var co=navigator.connection||{};
  var maigre=co.saveData===true||/(^|-)2g$/.test(co.effectiveType||'');
  if(!matchMedia('(min-width:900px)').matches || maigre
     || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  /* L'affiche n'est posee qu'ici. Sur un fond superpose a un carrousel elle
     n'est jamais visible : la declarer dans le HTML ferait partir son poids
     sur tous les telephones pour rien. Une video dont l'affiche doit rester
     visible garde son attribut poster — voir le spa. */
  if(el.dataset.affiche){ el.poster=el.dataset.affiche; }
  var choisi=null;
  for(var i=0;i<sources.length;i++){
    if(el.canPlayType(sources[i].type)){ choisi=sources[i]; break; }
  }
  if(!choisi) return;
  var s=document.createElement('source');
  s.type=choisi.type.split(';')[0]; s.src=choisi.src;
  el.appendChild(s);
  el.addEventListener('playing', function(){
    el.classList.add('on'); if(alors) alors();
  }, {once:true});
  el.load();
  var p=el.play();
  if(p && p.catch) p.catch(function(){});   /* lecture refusee : l'affiche reste */
}

/* Visionneuse : servir le WebP quand le navigateur le gere. Sur les photos
   ouvertes en plein ecran, cela represente environ 30 % de moins a
   telecharger. build-images.py garantit qu'un .webp existe pour chaque
   image ouvrable, et verifier.py le controle. */
var _webp = document.createElement('canvas')
              .toDataURL('image/webp').indexOf('data:image/webp') === 0;
function plein(el){
  var u = el.dataset.full || el.src;
  return _webp ? u.replace(/\.jpg$/, '.webp') : u;
}

/* Hauteur reelle de l'en-tete compacte -> --h-nav.
   Une valeur ecrite a la main derive des qu'on touche au rembourrage ou a la
   taille du logo : celle-ci avait 24 px de retard. On la mesure en posant brievement la classe « scrolled »,
   transition coupee pour ne rien faire clignoter, puis on remesure au
   redimensionnement et une fois les polices chargees. */
(function(){
  var h = document.querySelector('header');
  if (!h) return;
  /* Une transition de l'en-tete vient de partir (on a defile) : la mesure
     couperait les transitions et la figerait net — le logo sautait a
     l'embleme au lieu de glisser, quand « load » tombait juste apres le
     premier defilement, ce qui arrive en ligne. On note l'heure de chaque
     depart et la mesure attend la fin (.9 s). Un simple evenement, et non
     getAnimations() : l'interroger pendant le chargement retardait d'une
     demi-seconde le depart des animations de l'ecran de chargement. */
  var bouge = 0;
  h.addEventListener('transitionrun', function(){ bouge = Date.now(); });
  function mesurer(){
    if (Date.now() - bouge < 950) {
      clearTimeout(mesurer.t); mesurer.t = setTimeout(mesurer, 950); return;
    }
    /* On mesure le CALQUE DE FOND, pas la boite. Depuis que le header a une
       hauteur fixe de 104 px, sa boite ne bouge plus : c'est le calque qui
       se contracte par transform, et getBoundingClientRect en tient compte.
       Mesurer le header rendrait 104 quoi qu'il arrive, et toutes les
       ancres se caleraient 26 px trop bas. */
    var fond = h.querySelector('.hd-fond') || h;
    var etait = h.classList.contains('scrolled');
    /* TOUT le header, pas seulement le calque. Couper la seule transition
       du fond laissait le logo et l'embleme demarrer leur fondu pendant la
       mesure : un battement visible a chaque chargement de page. */
    h.classList.add('sans-transition');
    h.classList.add('scrolled');
    var v = Math.round(fond.getBoundingClientRect().height);
    if (!etait) h.classList.remove('scrolled');
    void h.offsetHeight;
    h.classList.remove('sans-transition');
    if (v > 0) document.documentElement.style.setProperty('--h-nav', v + 'px');
  }
  mesurer();
  addEventListener('resize', mesurer);
  addEventListener('load', mesurer);
})();"""

REVEAL_JS = """
window.__reveal=1;   /* le secours du <head> sait qu'il n'a rien a faire */
var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
if(!('IntersectionObserver' in window)||reduce){document.querySelectorAll('.reveal').forEach(function(e){e.classList.add('in')})}
else{var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.1});
 document.querySelectorAll('.reveal').forEach(function(el){io.observe(el)});
 setTimeout(function(){document.querySelectorAll('.reveal:not(.in)').forEach(function(el){if(el.getBoundingClientRect().top<innerHeight)el.classList.add('in')})},1200)}"""

NAV_JS = NAV_BASE + '\n\n' + REVEAL_JS


LANG_JS = """var FR={};document.querySelectorAll('[data-t]').forEach(function(e){FR[e.dataset.t]=e.innerHTML});
/* 51 · Les titres VISIBLES roulent vers leur traduction : l'ancien texte
   sort vers le haut, le nouveau entre par le bas, .7 s, --ease-inout. Le
   reste du texte change sans animation.

   Les noeuds du nouveau titre sont DEPLACES dans une couche, jamais
   recrees : ce qu'un autre script tient en main reste le meme noeud. La
   copie de l'ancien est muette (aria-hidden, sans id ni data-t). Un clic
   pendant un roulement termine d'abord celui-ci. */
var ROULEMENTS=[];
function EVN_TITRES(){
  ROULEMENTS.slice().forEach(function(f){f()});
  if(!window.matchMedia||matchMedia('(prefers-reduced-motion: reduce)').matches||!Element.prototype.animate)return [];
  var h=innerHeight,out=[];
  document.querySelectorAll('h1,h2').forEach(function(e){
    if(!(e.matches('[data-t]')||e.querySelector('[data-t]')))return;
    var r=e.getBoundingClientRect();
    if(r.width&&r.bottom>0&&r.top<h)out.push([e,e.innerHTML]);
  });
  return out;
}
function EVN_ROULER(liste){
  liste.forEach(function(p){
    var e=p[0],avant=p[1];
    if(e.innerHTML===avant)return;
    var cs=getComputedStyle(e),entre=document.createElement('span'),sort=document.createElement('span');
    /* La couche reprend la mise en page du titre : certains sont en flex. */
    [entre,sort].forEach(function(c){
      c.style.cssText='display:'+(cs.display.indexOf('flex')>-1?'flex':'block')+';gap:'+cs.gap+
        ';align-items:'+cs.alignItems+';justify-content:'+cs.justifyContent+';flex-wrap:'+cs.flexWrap+';width:100%';
    });
    while(e.firstChild)entre.appendChild(e.firstChild);
    sort.innerHTML=avant;
    sort.setAttribute('aria-hidden','true');
    [].slice.call(sort.querySelectorAll('[id],[data-t]')).forEach(function(x){x.removeAttribute('id');x.removeAttribute('data-t')});
    sort.style.position='absolute';sort.style.left='0';sort.style.top='0';
    var pos=e.style.position,clip=e.style.clipPath;
    if(cs.position==='static')e.style.position='relative';
    e.style.clipPath='inset(0 -1em)';
    e.appendChild(entre);e.appendChild(sort);
    var o={duration:700,easing:'cubic-bezier(.6,0,.2,1)'};
    var a1=entre.animate([{transform:'translateY(100%)'},{transform:'none'}],o);
    var a2=sort.animate([{transform:'none'},{transform:'translateY(-100%)'}],o);
    function fin(){
      var i=ROULEMENTS.indexOf(fin);if(i<0)return;ROULEMENTS.splice(i,1);
      a1.cancel();a2.cancel();
      if(sort.parentNode)sort.parentNode.removeChild(sort);
      while(entre.firstChild)e.insertBefore(entre.firstChild,entre);
      if(entre.parentNode)entre.parentNode.removeChild(entre);
      e.style.position=pos;e.style.clipPath=clip;
    }
    ROULEMENTS.push(fin);a1.onfinish=fin;
  });
}
document.querySelectorAll('.lang button').forEach(function(b){b.onclick=function(){
  var lg=b.dataset.lang;
  document.querySelectorAll('.lang button').forEach(function(x){x.classList.toggle('on',x.dataset.lang===lg)});
  document.querySelectorAll('.lang').forEach(function(l){l.classList.toggle('en',lg==='en')});
  var titres=EVN_TITRES();
  var dict=lg==='en'?EN:FR;
  document.querySelectorAll('[data-t]').forEach(function(e){if(dict[e.dataset.t])e.innerHTML=dict[e.dataset.t]});
  EVN_ROULER(titres);
  document.documentElement.lang=lg;
  /* Point d'extension : une page qui a du texte hors [data-t] — un
     placeholder de champ, par exemple — declare window.EVN_LANG. */
  if(typeof EVN_LANG==='function')EVN_LANG(lg);
}});"""

ENVOI_JS = """
/* Envoi des formulaires -------------------------------------------------
   Un seul point d'entree cote serveur : /api/envoyer.
   Si l'envoi automatique n'est pas configure ou echoue, on ne perd jamais le
   visiteur : on lui propose WhatsApp avec le message deja redige, plus les
   numeros de la reception. */
var SAUT = String.fromCharCode(10);

var EVN = {
  wa: '{{WA}}',
  tel: '+2250151527575',
  mail: '{{MAIL}}',
  ouvert: Date.now(),

  lienWhatsApp: function (texte) {
    return 'https://wa.me/' + this.wa + '?text=' + encodeURIComponent(texte);
  },

  /* Voir ENVOI_WHATSAPP dans _chrome.py. */
  parWhatsApp: {{PAR_WHATSAPP}},

  /* Meme format que le serveur (api/envoyer.js), pour que la reference lue
     au telephone soit la meme que celle affichee a l'ecran. */
  reference: function () {
    return 'EVN-' + Date.now().toString(36).slice(-6).toUpperCase();
  },

  /* o : {bouton, secours, erreur, resume} */
  envoyer: function (type, donnees, o, alors) {
    var b = o.bouton, libelle = b ? b.textContent : '';
    if (o.erreur) o.erreur.classList.remove('on');
    if (o.secours) o.secours.classList.remove('on');

    /* La reference, generee ici pour que la retenue et le message portent la
       MEME : la reception lit « EVN-EIMWJG » dans son WhatsApp et retrouve
       la meme a cote du nom, dans le calendrier. */
    var ref = EVN.reference();

    /* Une demande de chambre previent le serveur, qui en retient une pendant
       deux heures — le temps que la reception la voie. Sans ca, la demande
       partait sur son telephone et le site continuait d'annoncer la chambre
       libre : deux clients pouvaient demander la derniere.

       Envoi SANS ATTENDRE la reponse, et l'echec est sans consequence : la
       demande part de toute facon, elle n'a jamais dependu de ce serveur. Ce
       qui compte pour le visiteur, c'est que son message arrive. */
    if (o.retenue && window.fetch) {
      try {
        fetch('/api/admin?a=demande', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            categorie: o.retenue.categorie, du: o.retenue.du,
            au: o.retenue.au, nom: o.retenue.nom,
            /* L'adresse sert a une seule chose : prevenir le client quand la
               reception confirme. Elle ne ressort par aucune route publique. */
            courriel: o.retenue.courriel, reference: ref })
        }).catch(function () {});
      } catch (e) { /* le formulaire continue */ }
    }

    /* La demande part sur WhatsApp.

       On n'appelle PAS window.open : les navigateurs le bloquent largement,
       et il ne se passait alors plus rien du tout au clic. On ne peut pas
       parier la seule voie d'envoi sur une API que le visiteur peut refuser.

       Le panneau s'ouvre donc avec le lien deja rempli, et c'est le visiteur
       qui le touche : un vrai clic sur un vrai lien, qu'aucun bloqueur
       n'arrete, sur telephone comme sur ordinateur.

       La confirmation s'affiche juste apres ce clic — pas avant. Elle est
       donc derriere lui quand il revient de WhatsApp, avec sa reference. */
    if (EVN.parWhatsApp) {
      var texte = (o.resume ? o.resume() : 'Bonjour, je souhaite vous contacter.')
                + SAUT + SAUT + 'Référence : ' + ref;
      var url = EVN.lienWhatsApp(texte);
      var a = o.secours ? o.secours.querySelector('a.wa-envoi') : null;

      if (!a) {                       /* pas de panneau : on n'a que ce recours */
        location.href = url;
        return;
      }
      a.href = url;
      a.addEventListener('click', function () {
        /* Le temps que l'onglet ou l'application prenne la main. */
        setTimeout(function () { alors({ ok: true, reference: ref }); }, 500);
      }, { once: true });
      o.secours.classList.add('on');
      o.secours.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }

    if (b) { b.setAttribute('aria-busy', 'true'); b.disabled = true; b.textContent = 'Envoi en cours…'; }

    var charge = Object.assign({}, donnees, {
      type: type,
      website: (document.querySelector('[name=website]') || {}).value || '',
      duree: Date.now() - EVN.ouvert,
      page: location.pathname
    });

    var fini = function (etat, reponse) {
      if (b) { b.removeAttribute('aria-busy'); b.disabled = false; b.textContent = libelle; }
      if (etat === 'ok') { alors(reponse); return; }
      if (etat === 'champs') {
        if (o.erreur) { o.erreur.textContent = reponse.message; o.erreur.classList.add('on'); }
        if (o.marquer) o.marquer(reponse.champs || []);
        return;
      }
      /* Ni succes ni faute du visiteur : on bascule sur WhatsApp. */
      if (o.secours) {
        var lien = o.secours.querySelector('a.wa-envoi');
        if (lien) lien.href = EVN.lienWhatsApp(o.resume ? o.resume() : 'Bonjour, je souhaite vous contacter.');
        o.secours.classList.add('on');
        o.secours.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    };

    if (!('fetch' in window)) { fini('secours', {}); return; }

    var minuteur = setTimeout(function () { fini('secours', {}); }, 12000);
    var repondu = false;
    fetch('/api/envoyer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(charge)
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) { return { s: r.status, j: j }; });
    }).then(function (x) {
      if (repondu) return; repondu = true; clearTimeout(minuteur);
      if (x.s === 200 && x.j.ok) fini('ok', x.j);
      else if (x.s === 422) fini('champs', x.j);
      else fini('secours', x.j);
    }).catch(function () {
      if (repondu) return; repondu = true; clearTimeout(minuteur);
      fini('secours', {});
    });
  }
};
"""

ENVOI_JS = ENVOI_JS.replace('{{WA}}', WA).replace('{{MAIL}}', MAIL)
ENVOI_JS = ENVOI_JS.replace('{{PAR_WHATSAPP}}',
                            'true' if ENVOI_WHATSAPP else 'false')

PIEGE = ('<div class="piege" aria-hidden="true">'
         '<label>Ne pas remplir<input type="text" name="website" tabindex="-1" autocomplete="off"></label>'
         '</div>')


def secours(id_='sec', phrase="Votre demande est prête — il ne reste qu'à l'envoyer."):
    """Panneau de repli : WhatsApp pre-rempli, telephone, e-mail.

    Le texte ne s'excuse pas. Il annoncait l'echec avant de proposer la suite
    (« Nous n'avons pas pu transmettre votre demande automatiquement »), et se
    lisait comme une panne du formulaire alors que le visiteur a, juste sous
    les yeux, le canal le plus rapide du pays. On mene donc par l'action.

    Il reste explicite sur un point : la demande n'est PAS partie. « il ne
    reste qu'a l'envoyer » le dit sans detour — sans quoi le visiteur
    fermerait la page en croyant avoir reserve.
    """
    return ('''<div class="secours" id="%s" role="alert">
  <b data-t="sc1">Terminons sur WhatsApp</b>
  <p data-t="sc2">%s Un clic, et elle arrive à la réception, qui répond 24 h/24. Vous pouvez aussi appeler ou écrire.</p>
  <div class="liens">
    <a class="wa-envoi" data-t="sc3" href="https://wa.me/{{WA}}" target="_blank" rel="noopener">Envoyer sur WhatsApp</a>
    <a data-t="sc4" href="tel:+2250151527575">Appeler la réception</a>
    <a data-t="sc5" href="mailto:{{MAIL}}">Écrire un e-mail</a>
  </div>
</div>''' % (id_, phrase)).replace('{{WA}}', WA).replace('{{MAIL}}', MAIL)

EN_NAV = ('mn:"Menu",n1:"Rooms &amp; Suites",n2:"Experiences",n3:"The table",n4:"The spa",'
          'n5:"Offers &amp; Events",n6:"Meetings &amp; groups",n7:"Gallery",n8:"About",'
          'n9:"Useful information",n10:"Contact",n11:"Book",dr:"Reservations",')

# Le panneau de repli des cinq formulaires. Il vit ici, et non dans chaque
# page, pour la meme raison que le panneau lui-meme : une seule source.
# Les cles sc1-sc5 ont ete choisies libres sur les cinq pages concernees —
# une cle reutilisee ecraserait l'autre texte, cf. controle 7 quater.
EN_SECOURS = ('sc1:"Finish on WhatsApp",'
              'sc2:"Your request is ready — it just needs sending. One tap and it '
              'reaches reception, who answer 24/7. You can also call or write.",'
              'sc3:"Send on WhatsApp",sc4:"Call reception",sc5:"Write an email",')


# ---------------------------------------------------------------------------
# Images responsives
# ---------------------------------------------------------------------------
# build-images.py produit les variantes NOM-640, NOM-1024, NOM-1600 en webp et
# en jpeg. Cette fonction les declare dans les balises deja ecrites.
#
# Les motifs sont volontairement etroits : ils ne remplacent qu'une VALEUR
# d'attribut, ne traversent jamais une balise et ne peuvent donc rien effacer.
# `data-full`, `href`, `content` et les URL absolues du JSON-LD ne matchent pas.
import os as _os
import re as _re

_W = (640, 1024, 1600)
# Un hero occupe toute la largeur ; le reste ne depasse jamais la colonne.
SIZES_HERO = '100vw'
SIZES_DEFAUT = '(max-width:720px) 100vw, (max-width:1100px) 60vw, 700px'


_largeur_cache = {}


def _largeur(chemin):
    """Largeur reelle du fichier, lue une seule fois. Sans elle, le dernier
    candidat du srcset n'aurait pas de descripteur `w` — or on ne peut pas
    melanger descripteurs `w` et candidats nus dans un meme srcset."""
    if chemin not in _largeur_cache:
        try:
            from PIL import Image
            _largeur_cache[chemin] = Image.open(chemin).size[0]
        except Exception:
            _largeur_cache[chemin] = None
    return _largeur_cache[chemin]


def _variantes(nom, ext):
    v = [(w, 'img/opt/%s-%d.%s' % (nom, w, ext)) for w in _W]
    v = [(w, p) for w, p in v if _os.path.exists(p)]
    plein = 'img/opt/%s.%s' % (nom, ext)
    w0 = _largeur(plein)
    if w0:
        v = [(w, p) for w, p in v if w < w0] + [(w0, plein)]
    return v


_taille_cache = {}


def _taille(nom, ext):
    """Dimensions reelles du fichier, lues une seule fois."""
    cle = (nom, ext)
    if cle not in _taille_cache:
        try:
            from PIL import Image
            _taille_cache[cle] = Image.open('img/opt/%s.%s' % (nom, ext)).size
        except Exception:
            _taille_cache[cle] = None
    return _taille_cache[cle]


def dimensionner(html):
    """Donne a chaque <img> ses dimensions intrinseques.

    Sans width/height, une image ne reserve aucune place tant qu'elle n'est pas
    chargee. Combine au chargement differe et a une grille en colonnes, cela
    fait sauter la mise en page sous les yeux du visiteur pendant qu'il defile :
    chaque photo qui arrive rebat les colonnes. Les attributs donnent au
    navigateur le rapport largeur/hauteur avant tout telechargement.
    """
    def f(m):
        balise = m.group(0)
        d = _taille(m.group(1), m.group(2))
        if not d:
            return balise
        # Une dimension fausse est pire qu'absente : le navigateur reserve la
        # mauvaise hauteur, puis corrige quand l'image arrive. On remplace donc
        # ce qui est declare au lieu de se contenter de completer.
        balise = _re.sub(r'\s(?:width|height)="\d+"', '', balise)
        return '<img width="%d" height="%d"' % d + balise[4:]

    return _re.sub(r'<img[^<>]*?src="img/opt/([\w-]+)\.(jpg|png|webp)"[^<>]*?>', f, html)


def responsive(html, hero=None, sizes=None):
    """Ajoute srcset + sizes aux <picture>/<img> qui ont des variantes.

    `sizes` : dictionnaire {nom d'image: declaration}, pour les mises en page
    dont la largeur d'affichage ne ressemble pas a SIZES_DEFAUT. Sans lui, une
    vignette de mosaique de 293 px se faisait servir le palier 1024 — le
    navigateur ne peut pas deviner la geometrie d'une grille, il croit ce
    qu'on lui declare.
    """
    sizes = sizes or {}

    def sizes_de(nom):
        if nom in sizes:
            return sizes[nom]
        return SIZES_HERO if hero and nom == hero else SIZES_DEFAUT

    def source(m):
        nom = m.group(1)
        v = _variantes(nom, 'webp')
        if len(v) < 2:
            return m.group(0)
        jeu = ', '.join('%s %dw' % (p, w) for w, p in v)
        return 'srcset="%s" sizes="%s"' % (jeu, sizes_de(nom))

    def image(m):
        avant, nom, apres = m.group(1), m.group(2), m.group(3)
        v = _variantes(nom, 'jpg')
        if len(v) < 2:
            return m.group(0)
        jeu = ', '.join('%s %dw' % (p, w) for w, p in v)
        return ('<img%ssrc="img/opt/%s.jpg" srcset="%s" sizes="%s"%s'
                % (avant, nom, jeu, sizes_de(nom), apres))

    html = _re.sub(r'srcset="img/opt/([\w-]+)\.webp"', source, html)
    html = _re.sub(r'<img([^<>]*?)src="img/opt/([\w-]+)\.jpg"([^<>]*?>)', image, html)
    return html


# --- Empreinte de contenu sur les medias re-encodables ------------------------
#
# vercel.json sert /video/ en « immutable, un an » : le navigateur a l'ordre
# de garder le fichier et de ne PLUS JAMAIS redemander cette URL. Cette
# promesse n'est tenable que si l'URL change quand le contenu change.
#
# Elle ne l'etait pas : le film du hero a ete re-encode trois fois sous le
# meme nom. Tout visiteur ayant vu une version precedente restait dessus,
# pendant un an, sans aucun moyen de recevoir la correction.
#
# Les URL des videos et des affiches portent donc desormais une empreinte de
# leur propre contenu. Re-encoder un fichier change l'empreinte, donc l'URL,
# donc le navigateur le retelecharge — sans rien avoir a purger.
import hashlib as _hashlib

_EMPREINTES = {}

def empreinte(chemin):
    if chemin not in _EMPREINTES:
        with open(chemin, 'rb') as f:
            _EMPREINTES[chemin] = _hashlib.md5(f.read()).hexdigest()[:8]
    return _EMPREINTES[chemin]


# Les affiches sont concernees au meme titre : elles sont refabriquees a
# chaque re-encodage du film qu'elles illustrent.
_MEDIA = _re.compile(r'(video/[\w-]+\.(?:mp4|webm)|img/opt/[\w-]+-affiche\.(?:jpg|webp))'
                    r'(?:\?v=[0-9a-f]+)?')


def versionner(html):
    """Ajoute ?v=<empreinte> aux URL des medias re-encodables.

    Idempotent : une empreinte deja presente est recalculee, jamais empilee.
    Une URL dont le fichier est absent est laissee telle quelle — c'est a
    verifier.py de signaler le lien mort, pas a cette fonction de le masquer.
    """
    def remplace(m):
        chemin = m.group(1)
        if not _os.path.exists(chemin):
            return m.group(0)
        return '%s?v=%s' % (chemin, empreinte(chemin))
    return _MEDIA.sub(remplace, html)


def page(title, desc, og, css, body, script, preload=None, slug=None, jsonld='', sizes=None):
    pre = '\n<link rel="preload" as="image" href="img/opt/%s.webp" type="image/webp">' % preload if preload else ''
    if slug is not None:
        url = SITE + ('/' if slug in ('index', '') else '/' + slug)
        can = '\n<link rel="canonical" href="%s">\n<meta property="og:url" content="%s">' % (url, url)
    else:
        can = ''
    return ('''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
%s<title>%s</title>
<meta name="description" content="%s">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="Hôtel Evannath">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:image" content="%s/img/opt/%s.jpg">
<meta name="twitter:card" content="summary_large_image">
%s%s
%s%s
%s
<style>
%s
%s
</style>
</head>
<body>

%s

<script>
%s
</script>
</body>
</html>
''' % (ROBOTS_META, title, desc, title, desc, SITE, og, ICONS, can, HEAD, pre, jsonld, HEAD_CSS, css,
       versionner(responsive(dimensionner(body), hero=preload, sizes=sizes)), versionner(script))).replace('{{MAIL}}', MAIL)
