# -*- coding: utf-8 -*-
"""Genere reserver.html : le tunnel de reservation en trois etapes.

Remplace les alert() qui terminaient chaque formulaire. La page lit les
parametres passes par les fiches chambres (?chambre=&du=&au=&pax=), calcule
le sejour, collecte les coordonnees et simule le paiement de l'acompte.
"""
import io, json
from _chrome import PROSPECTION
from _chrome import ENVOI_JS, PIEGE, secours
from _chrome import REMISE_JS, REMISE_CSS, DISPO_JS
from _chrome import CONF_SVG, CONF_CSS
from _chrome import (page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV, EN_SECOURS,
                     CONF_TITRE, CONF_TITRE_EN, CONF_GESTE, CONF_GESTE_EN,
                     ENVOI_WHATSAPP)

CHAMBRES = {
 'chambre-standard':     ('Chambre Standard', 67000, 2, 'r-standard'),
 'deluxe-baldaquin':     ('Deluxe · lits à baldaquin', 82000, 2, 'ig-baldaquin'),
 'deluxe-superieure':    ('Deluxe Supérieure', 97000, 3, 'r-wax'),
 'suite-anglaise':       ('Suite Anglaise', 107000, 2, 'r-anglaise'),
 'chambre-mezzanine':    ('Chambre en Mezzanine', 127000, 2, 'r-mezz2'),
 'mezzanine-superieure': ('Mezzanine Supérieure', 142000, 4, 'r-mezzanine'),
 'suite-arabe':          ('Suite Arabe', 280000, 6, 'sa-main'),
}

# Taxe de sejour, par personne et par nuit, et part de l'acompte. Ecrites UNE
# fois : la page les affiche, le serveur les encaisse (api/_grille.json).
TAXE_SEJOUR = 1500
PART_ACOMPTE = 0.3

CSS = REMISE_CSS + CONF_CSS + """
.head{padding:150px 0 30px}
.head h1{margin:10px 0 14px}
.head p{max-width:56ch;font-size:1.04rem}

/* fil des etapes */
.steps{display:flex;gap:0;border:1px solid var(--line);margin-bottom:48px;position:relative}
.steps div{flex:1 1 0;min-width:0;padding:18px 20px;border-right:1px solid var(--line);display:flex;gap:14px;align-items:center;transition:.4s}
.steps div:last-child{border-right:0}
.steps div.on{background:var(--bark-2)}
.steps div.done{background:rgba(143,174,99,.07)}
.steps i{font-style:normal;width:26px;height:26px;border:1px solid var(--line);display:grid;place-items:center;
  font-size:11px;font-weight:700;color:var(--muted);flex:0 0 auto;
  transition:background-color .5s ease,border-color .5s ease,color .5s ease}
/* 47 · Le fil des etapes (maquette « Motion design III »). Sous la barre,
   un galon pagne avance jusqu'a la pastille de l'etape atteinte, en 1,1 s ;
   la pastille se remplit de bois a son arrivee (.9 s). Au retour, le galon
   recule et la pastille se vide tout de suite : le delai n'est porte QUE
   par l'etat atteint — une transition prend les reglages de sa destination.
   La pointe est calee sur le centre des pastilles : 20 px de marge de
   cellule + 13 px de demi-pastille + 1 px de bordure = 34 px, dans des
   cellules rendues strictement egales (flex:1 1 0 ; min-width:0). */
.steps div.on i,.steps div.done i{background:var(--bronze);border-color:var(--bronze);color:#fff;transition-delay:.9s}
.steps .fil{position:absolute;left:-1px;right:-1px;top:calc(100% + 1px);height:12px;background:var(--bark-3);pointer-events:none}
.steps .fil::before{content:"";position:absolute;inset:0;background:url(img/pagne/galon-pagne.svg) repeat-x left center;
  background-size:29px 12px;clip-path:inset(0 calc(100% - 34px) 0 0);transition:clip-path 1.1s var(--ease-inout)}
.steps[data-n="2"] .fil::before{clip-path:inset(0 calc(66.667% - 34px) 0 0)}
.steps[data-n="3"] .fil::before{clip-path:inset(0 calc(33.333% - 34px) 0 0)}
.steps[data-n="4"] .fil::before{clip-path:inset(0)}
.steps b{font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;font-weight:700;color:var(--muted)}
.steps div.on b{color:var(--cream)}
.steps div.done b{color:var(--palm)}

.grid{display:grid;grid-template-columns:1fr 400px;gap:56px;align-items:start;padding-bottom:100px}
.pane{display:none}
.pane.on{display:block}
.pane h2{margin-bottom:8px}
.pane>p.sub{color:var(--muted);margin-bottom:30px}

.f{display:flex;flex-direction:column;margin-bottom:18px}
/* Largeur explicite : sans elle, un <select> reclame la largeur de son
   option la plus longue — « Mezzanine superieure … » poussait la colonne,
   donc la page, de 34 px sur un ecran de 320. min-width:0 ne suffit pas :
   le navigateur garde la taille intrinseque comme plancher. */
.f input,.f select,.f textarea{width:100%}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
/* La disponibilite, dite la ou le visiteur choisit ses dates — et non
   trois ecrans plus loin, apres qu'il a saisi son nom et son telephone.
   `hidden` doit l'emporter sur `display:flex`, sinon la note reste a
   l'ecran alors qu'on n'a rien a annoncer. */
.dnote{display:flex;gap:11px;align-items:flex-start;border:1px solid var(--line);
  padding:13px 15px;margin-bottom:18px;font-size:13.5px;line-height:1.55;
  color:var(--prose)}
.dnote[hidden]{display:none}
.dnote i{width:7px;height:7px;border-radius:50%;flex:0 0 auto;margin-top:6px}
.dnote b{font-weight:600}
label{font-size:9.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--bronze);margin-bottom:8px;font-weight:700}
input,select,textarea{min-height:48px;background:transparent;border:1px solid var(--line);color:var(--cream);
  font:400 15px/1.5 var(--f-body);padding:12px 14px;outline:none;transition:.3s;min-width:0;font-family:var(--f-body)}
textarea{min-height:96px;resize:vertical}
input:focus,select:focus,textarea:focus{border-color:var(--bronze)}
select option{background:var(--bark-2);color:var(--cream)}
input::placeholder,textarea::placeholder{color:#6E6154}
.f.bad input,.f.bad select{border-color:var(--err)}
.msg{display:none;font-size:12.5px;color:var(--err);margin-top:7px}
.f.bad .msg{display:block}

.pay{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:8px 0 26px}
.pay label{display:flex;align-items:center;gap:14px;border:1px solid var(--line);padding:20px;cursor:pointer;
  margin:0;font-size:15px;letter-spacing:0;text-transform:none;color:var(--cream);font-weight:400;transition:.3s}
.pay label:hover{border-color:rgba(185,138,80,.5)}
.pay input{min-height:0;width:18px;height:18px;accent-color:var(--bronze);flex:0 0 auto;padding:0}
.pay label:has(input:checked){border-color:var(--bronze);background:rgba(185,138,80,.06)}
.pay em{font-style:normal;font-size:12px;color:var(--muted);display:block;margin-top:3px}

.nav-btn{display:flex;gap:14px;flex-wrap:wrap;margin-top:10px}
.ghost{background:none;border:1px solid var(--line);color:var(--muted)}
.ghost:hover{border-color:var(--bronze);color:var(--bronze);background:none;transform:none}

/* recapitulatif */
.recap{position:sticky;top:110px;background:var(--bark-2);border:1px solid var(--line)}
.recap .ph{aspect-ratio:16/10;overflow:hidden;background:var(--bark-3)}
.recap .ph img{width:100%;height:100%;object-fit:cover}
.recap .in{padding:26px}
.recap h3{font-size:1.35rem;margin-bottom:4px}
.recap .cat{font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--bronze);font-weight:700;margin-bottom:20px}
.recap .row{display:flex;justify-content:space-between;gap:14px;font-size:14px;color:var(--muted);padding:10px 0;border-bottom:1px solid var(--line-2)}
.recap .row span:last-child{color:var(--prose);text-align:right;font-variant-numeric:tabular-nums}
.recap .tot{display:flex;justify-content:space-between;align-items:baseline;gap:14px;margin-top:18px;padding-top:16px;border-top:1px solid var(--line)}
.recap .tot span{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:700}
.recap .tot b{font-family:var(--f-display);font-size:1.9rem;color:var(--bronze-2);font-variant-numeric:tabular-nums;font-weight:400}
.recap .acompte{margin-top:14px;padding:14px 16px;border:1px solid var(--line);font-size:13px;color:var(--muted)}
.recap .acompte b{color:var(--bronze-2);font-weight:600}

/* paiement en ligne */
/* `hidden` doit gagner : sans cela, .pay{display:grid} et .btn gardaient
   les choix de moyen et le bouton « Envoyer » a l'ecran en mode paiement. */
[hidden]{display:none!important}
.test-pay{border:1px dashed var(--bronze);padding:12px 16px;font-size:13.5px;color:var(--bronze-2);margin:0 0 22px}
.retour{margin-top:8px}
.retour p{font-size:15.5px;color:var(--prose);margin-bottom:22px}

/* confirmation */
.done-box{text-align:center;padding:20px 0 60px}
.done-box h2{margin-bottom:14px}
.done-box .conf-msg>p{max-width:50ch;margin:0 auto 12px}
.ref{display:inline-block;margin-top:20px;border:1px solid var(--line);padding:14px 22px;
  font-family:var(--f-display);font-size:1.3rem;color:var(--bronze-2);letter-spacing:.1em}
.done-box .g{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:34px}
.next-steps{border:1px solid var(--line);margin-top:44px;text-align:left;max-width:560px;margin-inline:auto}
.next-steps div{padding:16px 22px;border-bottom:1px solid var(--line);display:flex;gap:16px;font-size:14.5px;color:var(--prose)}
.next-steps div:last-child{border-bottom:0}
.next-steps i{font-style:normal;color:var(--bronze);font-weight:700;flex:0 0 auto}

@media(max-width:1080px){
  .grid{grid-template-columns:minmax(0,1fr);gap:40px}
  .recap{position:static;order:-1}
}
@media(max-width:720px){
  .head{padding:126px 0 24px}
  .steps{flex-direction:column}
  .steps div{border-right:0;border-bottom:1px solid var(--line)}
  .steps div:last-child{border-bottom:0}
  /* Les etapes s'empilent : un galon horizontal n'y dit plus rien. Les
     pastilles, elles, continuent de se remplir. */
  .steps .fil{display:none}
  .two,.pay{grid-template-columns:minmax(0,1fr)}
}
"""

body = [header('index.html#chambres', 'Nos chambres', 'navch'), drawer('index.html#chambres'), '''
<div class="wrap head">
  <nav class="crumb" aria-label="Fil d'Ariane">
    <a href="index.html" data-t="c1">Accueil</a> &nbsp;·&nbsp;
    <a href="index.html#chambres" data-t="c2">Chambres &amp; Suites</a> &nbsp;·&nbsp;
    <span data-t="c3">Réservation</span>
  </nav>
  <span class="eyebrow" data-t="eb">Réservation directe · meilleur tarif garanti</span>
  <h1 data-t="h1">Votre séjour</h1>
  <p data-t="lede">Trois étapes, deux minutes. L'acompte confirme la chambre ; le solde se règle à l'arrivée.</p>
</div>

<div class="wrap">
  <div class="steps" id="steps" data-n="1">
    <span class="fil" aria-hidden="true"></span>
    <div class="on" data-s="1"><i>1</i><b data-t="st1">Votre séjour</b></div>
    <div data-s="2"><i>2</i><b data-t="st2">Vos coordonnées</b></div>
    <div data-s="3"><i>3</i><b data-t="st3">Acompte</b></div>
  </div>
</div>

<div class="wrap grid">
  <div>

    <!-- 1 ─────────────────────────────────────── -->
    <section class="pane on" id="p1">
      <h2 data-t="h2a">Vos dates</h2>
      <p class="sub" data-t="sub1">Modifiez si besoin — le total se met à jour immédiatement.</p>

      <div class="f"><label for="cat" data-t="lcat">Catégorie</label><select id="cat"></select></div>
      <div class="two">
        <div class="f"><label for="d1" data-t="ld1">Arrivée</label><input type="date" id="d1"></div>
        <div class="f"><label for="d2" data-t="ld2">Départ</label><input type="date" id="d2"></div>
      </div>
      <div class="dnote" id="dnote" hidden><i></i><span></span></div>
      <div class="f"><label for="pax" data-t="lpax">Voyageurs</label><select id="pax"></select></div>
      <div class="f"><label for="note" data-t="lnote">Une demande particulière&nbsp;? (facultatif)</label>
        <textarea id="note" placeholder="Heure d'arrivée tardive, lit d'appoint, occasion à fêter…"></textarea></div>

      <div class="nav-btn"><button class="btn btn-solid" id="go2" data-t="suiv">Continuer</button></div>
    </section>

    <!-- 2 ─────────────────────────────────────── -->
    <section class="pane" id="p2">
      <h2 data-t="h2b">Vos coordonnées</h2>
      <p class="sub" data-t="sub2">Pour vous envoyer la confirmation et vous accueillir à l'arrivée.</p>

      <div class="two">
        <div class="f"><label for="fn" data-t="lfn">Prénom *</label><input type="text" id="fn" autocomplete="given-name" placeholder="Aya">
          <span class="msg" data-t="mfn">Merci d'indiquer votre prénom.</span></div>
        <div class="f"><label for="ln" data-t="lln">Nom *</label><input type="text" id="ln" autocomplete="family-name" placeholder="Kouassi">
          <span class="msg" data-t="mln">Merci d'indiquer votre nom.</span></div>
      </div>
      <div class="two">
        <div class="f"><label for="em" data-t="lem">E-mail *</label><input type="email" id="em" autocomplete="email" placeholder="vous@exemple.com">
          <span class="msg" data-t="mem">Cette adresse e-mail ne semble pas valide.</span></div>
        <div class="f"><label for="tl" data-t="ltl">Téléphone / WhatsApp *</label><input type="tel" id="tl" autocomplete="tel" placeholder="+225 01 02 03 04 05">
          <span class="msg" data-t="mtl">Indiquez un numéro d'au moins 8 chiffres.</span></div>
      </div>
      <div class="f"><label for="nav" data-t="lnav">Navette aéroport gratuite</label>
        <select id="nav">
          <option value="non" data-t="nv0">Je viens par mes propres moyens</option>
          <option value="aller" data-t="nv1">Aller — venez me chercher à l'aéroport</option>
          <option value="ar" data-t="nv2">Aller et retour</option>
        </select></div>

      <div class="nav-btn">
        <button class="btn ghost" id="back1" data-t="retr">Retour</button>
        <button class="btn btn-solid" id="go3" data-t="suiv2">Continuer</button>
      </div>
    </section>

    <!-- 3 ─────────────────────────────────────── -->
    <section class="pane" id="p3">
      <h2 data-t="h2c">L'acompte</h2>
      <p class="sub" id="sub3" data-t="sub3">Trente pour cent pour bloquer la chambre, le solde à l'arrivée. Indiquez le moyen qui vous arrange : la réception vous envoie le lien de paiement une fois la disponibilité confirmée.</p>

      <p class="sub" id="sub3p" data-t="sub3p" hidden>Trente pour cent pour réserver la chambre, le solde à l'arrivée. Vous réglez sur la page sécurisée de lomi, notre prestataire de paiement : Wave, MTN Mobile Money ou carte bancaire.</p>
      <p class="test-pay" id="testpay" data-t="testp" hidden><b>Mode test.</b> Aucun argent ne bouge : utilisez les numéros et cartes de test de lomi.</p>

      <div class="pay" id="payopts">
        <label><input type="radio" name="pay" value="Wave" checked><span>Wave<em data-t="py0">Le plus utilisé en Côte d'Ivoire</em></span></label>
        <label><input type="radio" name="pay" value="MTN Money"><span>MTN Money<em data-t="py2">Paiement par téléphone</em></span></label>
        <label><input type="radio" name="pay" value="Carte bancaire"><span data-t="py3n">Carte bancaire<em>Visa · Mastercard</em></span></label>
      </div>

      <p style="font-size:13.5px;color:var(--muted);border-left:2px solid var(--bronze);padding:6px 0 6px 20px">
        <span data-t="annul">Annulation gratuite jusqu'à 48 h avant l'arrivée, acompte intégralement remboursé.
        Au-delà, l'acompte reste acquis à l'établissement.</span>
      </p>

      ''' + PIEGE + '''
      <p class="err-envoi" id="err" role="alert"></p>''' + secours('sec') + '''
      <div class="nav-btn" style="margin-top:26px">
        <button class="btn ghost" id="back2" data-t="retr2">Retour</button>
        <button class="btn btn-solid" id="pay" data-t="env">Envoyer ma demande</button>
        <button class="btn btn-solid" id="payer" data-t="envp" hidden>Payer l'acompte</button>
      </div>
      <div class="retour" id="retour" role="status" hidden>
        <p id="retourm"></p>
        <button class="btn btn-solid" id="reprendre" data-t="repr" hidden>Reprendre le paiement</button>
      </div>
    </section>

    <!-- 4 ─────────────────────────────────────── -->
    <section class="pane" id="p4">
      <div class="done-box">
        ''' + CONF_SVG + '''
        <div class="conf-msg">
        <h2 data-t="h2d">{{CT}}</h2>
        <p id="dm">{{CG}}</p>
        <p style="color:var(--muted);font-size:14px" data-t="refn">Notez cette référence : elle identifie votre dossier.</p>
        <div class="ref" id="ref">EVN-000000</div>

        <div class="next-steps">
          <div><i>1</i><span data-t="ns1">La réception vérifie la disponibilité et vous répond sous 24 h, par e-mail et par WhatsApp.</span></div>
          <div><i>2</i><span data-t="ns2">Une fois la chambre confirmée, vous recevez le lien pour régler l'acompte de 30 %.</span></div>
          <div><i>3</i><span id="nv">Le solde se règle à l'arrivée, sur place.</span></div>
        </div>

        <div class="g">
          <a href="index.html" class="btn btn-solid" data-t="fb1">Retour à l'accueil</a>
          <a href="circuits.html" class="btn" data-t="fb2">Ajouter une expérience</a>
        </div>
        </div>
      </div>
    </section>

  </div>

  <!-- recapitulatif ───────────────────────────── -->
  <aside class="recap">
    <div class="ph"><img id="rimg" src="img/opt/r-standard.jpg" alt=""></div>
    <div class="in">
      <div class="cat" data-t="rcat">Votre chambre</div>
      <h3 id="rnom">Chambre Standard</h3>
      <div class="row"><span data-t="rr1">Arrivée</span><span id="rd1">—</span></div>
      <div class="row"><span data-t="rr2">Départ</span><span id="rd2">—</span></div>
      <div class="row"><span id="rnl">Nuits</span><span id="rn">—</span></div>
      <div class="row"><span data-t="rr3">Voyageurs</span><span id="rp">—</span></div>
      <div class="row"><span id="rul">Tarif</span><span id="ru">—</span></div>
      <!-- Vide et masquee tant qu'aucune promotion ne court. -->
      <div class="row" id="rrem" hidden><span id="rreml">Remise</span>
        <span id="rremv" style="color:var(--palm)">—</span></div>
      <div class="row"><span data-t="rr4">Taxe de séjour</span><span id="rt">—</span></div>
      <div class="row"><span data-t="rr5">Petit-déjeuner</span><span style="color:var(--palm)" data-t="rr5v">Inclus</span></div>
      <div class="tot"><span data-t="rr6">Total séjour</span><b id="rtot">—</b></div>
      <div class="acompte"><span data-t="rac">Acompte à régler aujourd'hui :</span> <b id="racc">—</b><br>
        <span style="font-size:12px"><span data-t="rso">Solde à l'arrivée :</span> <b id="rsolde" style="color:var(--prose);font-weight:600">—</b></span></div>
    </div>
  </aside>
</div>

''' + FOOTER]

JS = NAV_JS + ENVOI_JS + REMISE_JS + DISPO_JS + '''

var CH=''' + json.dumps(CHAMBRES, ensure_ascii=False) + ''';
var TAX=''' + str(TAXE_SEJOUR) + '''; // taxe de séjour par personne et par nuit

var cat=document.getElementById('cat'),d1=document.getElementById('d1'),
    d2=document.getElementById('d2'),pax=document.getElementById('pax');

function libelleCat(k){
  var t=EVN_REMISE.prix(CH[k][1],k);
  return CH[k][0]+' — '+fmt(t)+' FCFA'
    +(t<CH[k][1]?' ('+T[LG].aulieu+' '+fmt(CH[k][1])+')':'');
}
Object.keys(CH).forEach(function(k){
  var o=document.createElement('option');
  o.value=k; o.textContent=libelleCat(k);
  cat.appendChild(o);
});

function fmt(n){return n.toLocaleString('fr-FR').replace(/ | |,/g,' ')}
function iso(d){return new Date(d.getTime()-d.getTimezoneOffset()*6e4).toISOString().slice(0,10)}
/* Tout ce que ce script ecrit lui-meme est hors de portee de [data-t] :
   les options de menus, le recapitulatif, la date en toutes lettres et le
   message de confirmation. LANG_JS appelle EVN_LANG a chaque bascule — c'est
   le point d'extension prevu pour ce cas. */
var LG='fr';
var T={fr:{loc:'fr-FR',p1:' personne',pp:' personnes',n1:'Nuit',nn:'Nuits',tarif:'Tarif',
           aulieu:'au lieu de',
           merci:'{{CG}}Merci ',dem:'. Votre demande pour la ',du:' du ',au:' au ',
           part:"{{PART}}",
           solde:"Le solde se règle à l'arrivée, sur place.",
           dlibre:'<b>Disponible à ces dates.</b> La réception vous le confirmera par écrit.',
           dderniere:"<b>Il ne reste qu'une chambre de cette catégorie sur ces nuits.</b> "
                     +"Elle n'est pas retenue tant que la réception n'a pas confirmé.",
           dcomplet:"<b>Cette catégorie est complète sur ces nuits.</b> Changez de dates "
                    +"ou de catégorie ci-dessus. Vous pouvez aussi envoyer votre demande "
                    +"telle quelle : la réception vous dira ce qu'elle peut faire.",
           nav1:'Votre navette aéroport est notée (',nav2:"). Le solde se règle à l'arrivée.",
           dlibreP:'<b>Disponible à ces dates.</b> La chambre est à vous dès l’acompte réglé.',
           dderniereP:"<b>Il ne reste qu'une chambre de cette catégorie sur ces nuits.</b> "
                     +"Elle est à vous dès l’acompte réglé.",
           redir:'Ouverture de la page de paiement…',
           complet:"Plus aucune chambre libre dans cette catégorie à ces dates : quelqu'un vient de la réserver. "
                   +"Changez de dates ou de catégorie à l'étape 1.",
           lomiKO:"Le paiement en ligne ne répond pas pour l'instant. Vous pouvez envoyer votre demande à la réception à la place.",
           verif:'Nous vérifions votre paiement auprès de lomi…',
           tarde:"La confirmation de lomi tarde. Votre référence : #. Elle arrivera d'elle-même ; "
                 +'en cas de doute, la réception la retrouve avec cette référence.',
           echec:"Le paiement n'a pas abouti. Vous pouvez recommencer.",
           abandon:"Le paiement a été interrompu. Votre sélection est conservée : vous pouvez le reprendre.",
           averif:'La réception vérifie votre paiement. Référence : #.',
           inconnue:'Cette référence de paiement est introuvable.',
           payeT:'Acompte reçu : votre chambre est réservée',
           payeM:function(j){ return 'Merci. '+j.categorie+', '+j.nuits+(j.nuits>1?' nuits':' nuit')
             +' à partir du '+jour(j.du)+', '+j.pax+(j.pax>1?' personnes':' personne')
             +'. Acompte réglé : '+fmt(j.montant)+' FCFA.'; },
           payeN1:'Votre réservation est enregistrée et confirmée auprès de la réception.',
           payeN2:function(j){ return 'Le solde, '+fmt(j.total-j.montant)+' FCFA, se règle à l’arrivée, sur place.'; },
           payeN3:'Pour toute question, la réception retrouve votre dossier avec cette référence.'},
     en:{loc:'en-GB',p1:' guest',pp:' guests',n1:'Night',nn:'Nights',tarif:'Rate',
           aulieu:'instead of',
           merci:'{{CG_EN}}Thank you ',dem:'. Your request for the ',du:' from ',au:' to ',
           part:'{{PART_EN}}',
           solde:'The balance is settled on arrival, at the hotel.',
           dlibre:'<b>Available on these dates.</b> The front desk will confirm in writing.',
           dderniere:'<b>Only one room left in this category on these nights.</b> '
                     +'It is not held until the front desk confirms.',
           dcomplet:'<b>This category is fully booked on these nights.</b> Change your '
                    +'dates or category above. You may also send your request as it is: '
                    +'the front desk will tell you what it can do.',
           nav1:'Your airport shuttle is noted (',nav2:'). The balance is settled on arrival.',
           dlibreP:'<b>Available on these dates.</b> The room is yours once the deposit is paid.',
           dderniereP:'<b>Only one room left in this category on these nights.</b> '
                     +'It is yours once the deposit is paid.',
           redir:'Opening the payment page…',
           complet:'No room left in this category on these dates: someone has just booked it. '
                   +'Change your dates or category at step 1.',
           lomiKO:'Online payment is not responding right now. You can send your request to the front desk instead.',
           verif:'We are checking your payment with lomi…',
           tarde:'The confirmation from lomi is taking a while. Your reference: #. It will arrive on its own; '
                 +'if in doubt, the front desk can find it with this reference.',
           echec:'The payment did not go through. You can try again.',
           abandon:'The payment was interrupted. Your selection is kept: you can resume it.',
           averif:'The front desk is checking your payment. Reference: #.',
           inconnue:'This payment reference cannot be found.',
           payeT:'Deposit received: your room is booked',
           payeM:function(j){ return 'Thank you. '+j.categorie+', '+j.nuits+(j.nuits>1?' nights':' night')
             +' from '+jour(j.du)+', '+j.pax+(j.pax>1?' guests':' guest')
             +'. Deposit paid: '+fmt(j.montant)+' FCFA.'; },
           payeN1:'Your booking is recorded and confirmed with the front desk.',
           payeN2:function(j){ return 'The balance, '+fmt(j.total-j.montant)+' FCFA, is settled on arrival, at the hotel.'; },
           payeN3:'For any question, the front desk finds your file with this reference.'}};
function jour(v){return v?new Date(v).toLocaleDateString(T[LG].loc,{weekday:'long',day:'numeric',month:'long'}):'—'}
/* Le recapitulatif a la place d'etre compact ; une demande relue en janvier
   pour un sejour de decembre, non. Le message porte donc l'annee. */
function jourAn(v){return v?new Date(v).toLocaleDateString(T[LG].loc,{weekday:'long',day:'numeric',month:'long',year:'numeric'}):'—'}
/* La disponibilite ---------------------------------------------------
   Elle se dit LA, sous les dates, et non trois ecrans plus loin : apprendre
   que la chambre est prise apres avoir saisi son nom, son e-mail et son
   telephone, c'est du travail perdu et un client de moins.

   Rien n'empeche d'envoyer la demande malgre un « complet » : la reception
   a des annulations, et une demande refusee par le site ne lui parvient
   jamais. */
var ETAT='inconnu';
function peindre(){
  var n=document.getElementById('dnote');
  if(!n)return;
  var cle={libre:'dlibre',derniere:'dderniere',complet:'dcomplet'}[ETAT];
  /* Paiement en ligne ouvert : plus de « la reception confirmera », la
     chambre se reserve des l'acompte regle. */
  if(cle && PAY.actif && T[LG][cle+'P']) cle=cle+'P';
  /* `inconnu` ne montre rien : le tunnel dit deja, sur son ecran de
     confirmation, que la reception repond sous 24 h. Une note qui repete
     « on ne sait pas » a chaque changement de date n'apprend rien. */
  if(!cle){n.hidden=true;return}
  n.hidden=false;
  n.querySelector('span').innerHTML=T[LG][cle];
  var c=EVN_DISPO.couleur(ETAT);
  n.style.borderColor=c;
  n.querySelector('i').style.background=c;
}
function interroger(){
  EVN_DISPO.pour(cat.value,d1.value,d2.value,function(e){ETAT=e;peindre()});
}
function EVN_LANG(lg){ LG=T[lg]?lg:'fr'; peindre(); peindrePaye();
  /* Les libelles des categories sont ecrits par ce script : [data-t] ne
     les atteint pas, il faut les refaire a la main a chaque bascule. */
  [].forEach.call(cat.options,function(o){o.textContent=libelleCat(o.value)});
  remplirPax(); calc(); }

// on reprend ce qui a été choisi sur la fiche chambre
var q=new URLSearchParams(location.search);
var slug=q.get('chambre'); if(!CH[slug])slug=Object.keys(CH)[0];
cat.value=slug;
d1.value=q.get('du')||iso(new Date(Date.now()+864e5));
d2.value=q.get('au')||iso(new Date(Date.now()+864e5*3));
d1.min=iso(new Date()); d2.min=iso(new Date());

function remplirPax(){
  var max=CH[cat.value][2], ancien=+pax.value||2;
  pax.innerHTML='';
  for(var i=1;i<=max;i++){
    var o=document.createElement('option');
    o.value=i; o.textContent=i+(i>1?T[LG].pp:T[LG].p1);
    pax.appendChild(o);
  }
  pax.value=Math.min(ancien,max);
}
remplirPax();
var wanted=+q.get('pax'); if(wanted&&wanted<=CH[cat.value][2])pax.value=wanted;

function calc(){
  var a=new Date(d1.value),b=new Date(d2.value);
  var n=Math.round((b-a)/864e5);
  if(!n||n<1){n=1;d2.value=iso(new Date(a.getTime()+864e5))}
  var c=CH[cat.value],p=+pax.value;
  /* PLEIN est le tarif de la grille, TARIF ce qu'on facture. Une promotion en
     cours les separe. On calcule sur TARIF : afficher une remise sans la
     deduire du total serait la pire des deux versions. */
  var plein=c[1], tarif=EVN_REMISE.prix(plein, cat.value), remise=plein-tarif;
  var brut=plein*n, sejour=tarif*n, taxe=TAX*p*n,
      total=sejour+taxe, acc=Math.round(total*''' + str(PART_ACOMPTE) + ''');

  document.getElementById('rimg').src='img/opt/'+c[3]+'.jpg';
  document.getElementById('rimg').alt=c[0];
  document.getElementById('rnom').textContent=c[0];
  document.getElementById('rd1').textContent=jour(d1.value);
  document.getElementById('rd2').textContent=jour(d2.value);
  document.getElementById('rnl').textContent=n>1?T[LG].nn:T[LG].n1;
  document.getElementById('rn').textContent=n;
  document.getElementById('rp').textContent=p+(p>1?T[LG].pp:T[LG].p1);
  /* La ligne de tarif reste au prix de la grille, et la remise se deduit en
     dessous : c'est la seule presentation ou la colonne s'additionne. Un
     sous-total deja remise suivi d'une ligne de remise se lit comme une
     double deduction — le client additionne, et ne retombe pas sur le
     total. */
  document.getElementById('rul').textContent=fmt(plein)+' × '+n;
  /* La ligne de remise dit combien elle retire, en francs : « −20 % » ne se
     verifie pas de tete, « −26 800 F » se verifie. */
  var lr=document.getElementById('rrem');
  if(remise>0){
    lr.hidden=false;
    document.getElementById('rreml').textContent=EVN_REMISE.titre();
    document.getElementById('rremv').textContent='−'+fmt(remise*n)+' FCFA';
  }else{
    lr.hidden=true;
  }
  document.getElementById('ru').textContent=fmt(brut);
  document.getElementById('rt').textContent=fmt(taxe);
  document.getElementById('rtot').textContent=fmt(total);
  document.getElementById('racc').textContent=fmt(acc)+' FCFA';
  document.getElementById('rsolde').textContent=fmt(total-acc)+' FCFA';
  /* calc() corrige parfois la date de depart : on interroge APRES, sinon on
     demanderait l'etat de dates que le visiteur ne voit deja plus. */
  interroger();
}
/* La remise arrive apres le premier calcul : on refait le menu et le
   recapitulatif des qu'elle est la. Si l'API se tait, tout reste au tarif
   plein — le repli sur. */
EVN_REMISE.quand(function(R){
  /* On renomme TOUTES les options, pas seulement si la chambre affichee au
     depart est ciblee : une promotion sur une seule chambre laissait sinon
     son option au tarif plein, et le menu contredisait le recapitulatif.
     libelleCat rend le libelle nu quand aucune remise ne s'applique. */
  [].forEach.call(cat.options,function(o){o.textContent=libelleCat(o.value)});
  calc();
});

cat.addEventListener('change',function(){remplirPax();calc()});
/* Venu d'une fiche chambre avec ses dates ET ses voyageurs : l'etape 1 est
   deja faite, on ouvre les coordonnees. Sans le nombre de voyageurs — le
   lien de l'accueil n'en porte pas — on reste a l'etape 1 : on ne facturerait
   pas une taxe de sejour sur un nombre de personnes que le client n'a pas vu.
   Des dates passees ou a l'envers : etape 1 aussi, pour qu'il les corrige. */
var DEJA_CHOISI=(function(){
  var du=q.get('du')||'',au=q.get('au')||'',J=/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/;
  return !q.get('paiement') && !!CH[q.get('chambre')] && q.get('chambre')===cat.value
    && wanted>=1 && wanted<=CH[cat.value][2] && +pax.value===wanted
    && J.test(du) && J.test(au) && au>du && du>=iso(new Date());
})();
[d1,d2,pax].forEach(function(e){e.addEventListener('change',calc)});
calc();
if(DEJA_CHOISI)etape(2);

// ── etapes ────────────────────────────────────
function etape(n){
  [1,2,3,4].forEach(function(i){
    var p=document.getElementById('p'+i);
    if(p)p.classList.toggle('on',i===n);
  });
  document.getElementById('steps').setAttribute('data-n',n);
  [].slice.call(document.querySelectorAll('#steps div')).forEach(function(d){
    var s=+d.dataset.s;
    d.classList.toggle('on',s===n);
    d.classList.toggle('done',s<n);
  });
  window.scrollTo({top:0,behavior:'smooth'});
}
document.getElementById('go2').onclick=function(){etape(2)};
document.getElementById('back1').onclick=function(){etape(1)};
document.getElementById('back2').onclick=function(){etape(2)};

// ── validation de l'etape 2 ───────────────────
var champs=[
  {id:'fn',test:function(v){return v.trim().length>=2}},
  {id:'ln',test:function(v){return v.trim().length>=2}},
  {id:'em',test:function(v){return /^[^\\s@]+@[^\\s@]+\\.[a-z]{2,}$/i.test(v.trim())}},
  {id:'tl',test:function(v){return v.replace(/\\D/g,'').length>=8}}
];
function verifier(c,montrer){
  var el=document.getElementById(c.id),ok=c.test(el.value);
  if(montrer||el.closest('.f').classList.contains('bad'))el.closest('.f').classList.toggle('bad',!ok);
  el.setAttribute('aria-invalid',ok?'false':'true');
  return ok;
}
champs.forEach(function(c){
  var el=document.getElementById(c.id);
  el.addEventListener('blur',function(){verifier(c,true)});
  el.addEventListener('input',function(){if(el.closest('.f').classList.contains('bad'))verifier(c,true)});
});
document.getElementById('go3').onclick=function(){
  var premier=null;
  champs.forEach(function(c){if(!verifier(c,true)&&!premier)premier=document.getElementById(c.id)});
  if(premier){premier.focus();premier.scrollIntoView({behavior:'smooth',block:'center'});return}
  etape(3);
};

// ── paiement ──────────────────────────────────
var N='\\n';
/* ── Paiement en ligne (lomi) ─────────────────────────────────────────
   Ouvert quand le serveur a sa cle (a=public le dit). Sinon, ou si lomi
   ne repond pas, ou si les chambres ne sont pas encore saisies, la demande
   part a la reception comme avant : on ne bloque jamais un client. */
var PAY={actif:false,test:false,paye:null};
function majPaiement(){
  var on=PAY.actif;
  document.getElementById('sub3').hidden=on;
  document.getElementById('sub3p').hidden=!on;
  document.getElementById('payopts').hidden=on;
  document.getElementById('testpay').hidden=!(on&&PAY.test);
  document.getElementById('pay').hidden=on;
  document.getElementById('payer').hidden=!on;
  peindre();
}
fetch('/api/admin?a=public',{cache:'no-store'})
  .then(function(r){return r.ok?r.json():null})
  .then(function(j){ if(j&&j.paiement){PAY.actif=!!j.paiement.actif;PAY.test=!!j.paiement.test} majPaiement(); })
  .catch(function(){});

function champ(id){var e=document.getElementById(id);return e?e.value.trim():''}
function garder(){
  try{ sessionStorage.setItem('evn-tunnel',JSON.stringify({cat:cat.value,d1:d1.value,d2:d2.value,
    pax:pax.value,fn:champ('fn'),ln:champ('ln'),em:champ('em'),tl:champ('tl'),
    nav:champ('nav'),note:champ('note')})); }catch(e){}
}
function repli(){ PAY.actif=false; majPaiement(); }

function payer(){
  var b=document.getElementById('payer'),err=document.getElementById('err'),lib=b.textContent;
  err.classList.remove('on'); b.disabled=true; b.textContent=T[LG].redir;
  function rendre(){ b.disabled=false; b.textContent=lib; }
  fetch('/api/admin?a=payer',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({categorie:cat.value,du:d1.value,au:d2.value,pax:+pax.value,
      prenom:champ('fn'),nom:champ('ln'),courriel:champ('em'),telephone:champ('tl')})})
  .then(function(r){return r.json().catch(function(){return {ok:false}})})
  .then(function(j){
    if(j&&j.ok&&j.url){ garder(); location.href=j.url; return; }
    rendre();
    var r=j&&j.raison;
    if(r==='complet'){ err.textContent=T[LG].complet; err.classList.add('on'); return; }
    if(r==='coordonnees'){ etape(2); return; }
    /* Chambres pas encore saisies, ou paiement ferme : la demande d'avant,
       sans rien dire — le client n'a rien a changer. */
    if(r==='inconnu'||r==='hors-ligne'){ repli(); demander(); return; }
    repli(); err.textContent=T[LG].lomiKO; err.classList.add('on');
  })
  .catch(function(){ rendre(); repli(); err.textContent=T[LG].lomiKO; err.classList.add('on'); });
}
document.getElementById('payer').onclick=payer;

/* ── Le retour de lomi : reserver?paiement=EVN-XXXXXX ───────────────────
   On ne croit pas l'URL : on demande l'etat au serveur, qui relit lomi. */
function retour(msg,reprise){
  document.getElementById('retour').hidden=false;
  document.getElementById('retourm').textContent=msg;
  document.getElementById('reprendre').hidden=!reprise;
  ['sub3','sub3p','payopts','testpay','pay','payer'].forEach(function(id){document.getElementById(id).hidden=true});
}
function confirmer(j,ref){
  PAY.paye={j:j,ref:ref};
  try{ sessionStorage.removeItem('evn-tunnel'); }catch(e){}
  document.getElementById('ref').textContent=ref;
  peindrePaye();
  etape(4);
}
function peindrePaye(){
  if(!PAY.paye)return;
  var j=PAY.paye.j,t=T[LG];
  document.querySelector('#p4 h2').textContent=t.payeT;
  document.getElementById('dm').textContent=t.payeM(j);
  var ns=document.querySelectorAll('#p4 .next-steps span');
  if(ns[0])ns[0].textContent=t.payeN1;
  if(ns[1])ns[1].textContent=t.payeN2(j);
  if(ns[2])ns[2].textContent=t.payeN3;
}
(function(){
  var q=new URLSearchParams(location.search),ref=(q.get('paiement')||'').toUpperCase();
  if(!/^EVN-[A-Z0-9]{6}$/.test(ref))return;
  try{ var m=JSON.parse(sessionStorage.getItem('evn-tunnel')||'null');
    if(m){ cat.value=m.cat; remplirPax(); d1.value=m.d1; d2.value=m.d2; pax.value=m.pax;
      ['fn','ln','em','tl','nav','note'].forEach(function(id){var e=document.getElementById(id); if(e&&m[id]!=null)e.value=m[id]});
      calc(); } }catch(e){}
  etape(3); retour(T[LG].verif,false);
  var abandon=q.get('abandon')==='1',essais=0;
  document.getElementById('reprendre').onclick=function(){
    document.getElementById('retour').hidden=true; majPaiement();
    history.replaceState(null,'',location.pathname);
  };
  function lire(){
    fetch('/api/admin?a=paiement&ref='+ref,{cache:'no-store'})
    .then(function(r){return r.json().catch(function(){return null})})
    .then(function(j){
      if(!j||!j.ok){ retour(T[LG].inconnue,false); return; }
      if(j.statut==='paye'){ confirmer(j,ref); return; }
      if(j.statut==='a-verifier'){ retour(T[LG].averif.replace('#',ref),false); return; }
      if(j.statut==='echoue'){ retour(T[LG].echec,true); return; }
      if(abandon){
        /* Interrompu : on libere tout de suite la chambre retenue, pour
           qu'elle ne manque pas au prochain essai — le sien compris. */
        fetch('/api/admin?a=abandon',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({ref:ref})}).catch(function(){});
        retour(T[LG].abandon,true); return;
      }
      if(++essais<20) setTimeout(lire,2500); else retour(T[LG].tarde.replace('#',ref),false);
    })
    .catch(function(){ if(++essais<20) setTimeout(lire,2500); else retour(T[LG].tarde.replace('#',ref),false); });
  }
  lire();
})();

/* La demande a la reception, telle qu'elle existait avant le paiement en
   ligne : c'est le repli, et le seul chemin tant qu'il est ferme. */
function demander(){
  var moyen=document.querySelector('input[name=pay]:checked').value;
  var c=CH[cat.value];
  var nv=document.getElementById('nav').value;
  var navette = nv==='non' ? 'non' : (nv==='ar' ? 'aller et retour' : 'aller simple');

  /* Le detail se lit dans le recapitulatif affiche, pas recalcule ici : le
     message et l'ecran ne peuvent donc pas diverger. Un client qui lit
     177 200 a l'ecran et 214 000 dans son message n'appelle pas pour
     comprendre — il renonce. */
  var lu=function(id){var e=document.getElementById(id);
    return e?e.textContent.replace(/\s+/g,' ').trim():''};
  var lrem=document.getElementById('rrem');

  var d={nom:document.getElementById('fn').value.trim()+' '+document.getElementById('ln').value.trim(),
         email:document.getElementById('em').value.trim(),
         tel:document.getElementById('tl').value.trim(),
         chambre:c[0], arrivee:jourAn(d1.value), depart:jourAn(d2.value),
         tarif:lu('rul')+' = '+lu('ru')+' FCFA',
         taxe:lu('rt')+' FCFA',
         solde:lu('rsolde'),
         nuits:document.getElementById('rn').textContent, personnes:pax.value,
         total:document.getElementById('rtot').textContent+' FCFA',
         acompte:document.getElementById('racc').textContent,
         /* Sans cette ligne, la reception recoit un total qui ne correspond
            pas a sa grille et croit a une erreur du client. */
         remise:(lrem && !lrem.hidden)
                ? lu('rreml')+' ('+EVN_REMISE.etiquette()+') — '+lu('rremv') : '',
         paiement:moyen,
         message:'Navette a\u00e9roport : '+navette
                 +(document.getElementById('note') && document.getElementById('note').value
                   ? N+document.getElementById('note').value : '')};

  function resume(){
    return "Bonjour, je souhaite r\u00e9server \u00e0 l\\'H\u00f4tel Evannath."+N+N
      +'Nom : '+d.nom+N+'T\u00e9l\u00e9phone : '+d.tel+N+'E-mail : '+d.email+N+N
      +'Chambre : '+d.chambre+N+'Arriv\u00e9e : '+d.arrivee+N+'D\u00e9part : '+d.depart+N
      +'Nuits : '+d.nuits+N+'Personnes : '+d.personnes+N+N
      +'Tarif : '+d.tarif+N
      +(d.remise?'Remise : '+d.remise+N:'')
      +'Taxe de s\u00e9jour : '+d.taxe+N
      +'Total estim\u00e9 : '+d.total+N
      +'Acompte (30 %) : '+d.acompte+N
      /* Apostrophe typographique : ce bloc est une chaine Python normale,
         elle interprete les echappements, et un \\' y deviendrait une
         apostrophe nue qui fermerait la chaine JavaScript. */
      +'Solde \u00e0 l\u2019arriv\u00e9e : '+d.solde+N+N
      +'Paiement souhait\u00e9 : '+d.paiement+N+d.message;
  }
  var CHAMP={nom:'fn',email:'em',tel:'tl'};

  EVN.envoyer('reservation',d,{
    /* Ce qu'il faut au serveur pour retenir une chambre : la CATEGORIE
       choisie (le client ne choisit jamais un numero), les dates brutes, et
       le nom. Le reste du message ne l'interesse pas. */
    retenue:{categorie:cat.value, du:d1.value, au:d2.value, nom:d.nom,
             courriel:d.email},
    bouton:document.getElementById('pay'),
    secours:document.getElementById('sec'),
    erreur:document.getElementById('err'),
    resume:resume,
    marquer:function(cs){
      etape(2);
      cs.forEach(function(x){var el=document.getElementById(CHAMP[x]);
        if(el)el.closest('.f').classList.add('bad')});
      var pr=document.getElementById(CHAMP[cs[0]]); if(pr)pr.focus();
    }
  },function(rep){
    document.getElementById('ref').textContent=rep.reference;
    document.getElementById('dm').textContent=
      T[LG].merci+document.getElementById('fn').value.trim()+T[LG].dem+c[0]
      +T[LG].du+jour(d1.value)+T[LG].au+jour(d2.value)+T[LG].part;
    document.getElementById('nv').textContent = nv==='non'
      ? T[LG].solde
      : T[LG].nav1+navette+T[LG].nav2;
    etape(4);
  });
}
document.getElementById('pay').onclick=demander;

var EN={''' + EN_NAV + EN_SECOURS + '''navch:"Our rooms",
c1:"Home",c2:"Rooms &amp; Suites",c3:"Booking",
eb:"Direct booking · best rate guaranteed",h1:"Your stay",
lede:"Three steps, two minutes. The deposit confirms the room; the balance is settled on arrival.",
st1:"Your stay",st2:"Your details",st3:"Deposit",
h2a:"Your dates",sub1:"Change them if you need to — the total updates immediately.",
lcat:"Category",ld1:"Check-in",ld2:"Check-out",lpax:"Guests",
lnote:"Any particular request? (optional)",suiv:"Continue",
h2b:"Your details",sub2:"So we can send your confirmation and welcome you on arrival.",
lfn:"First name *",mfn:"Please give your first name.",
lln:"Surname *",mln:"Please give your surname.",
lem:"E-mail *",mem:"This e-mail address does not look valid.",
ltl:"Phone / WhatsApp *",mtl:"Please give a number of at least 8 digits.",
lnav:"Free airport shuttle",
nv0:"I am making my own way",nv1:"One way — collect me at the airport",nv2:"Both ways",
retr:"Back",suiv2:"Continue",
h2c:"The deposit",
sub3:"Thirty per cent to hold the room, the balance on arrival. Tell us which method suits you: the front desk sends the payment link once availability is confirmed.",
py0:"The most used in Côte d\u2019Ivoire",py2:"Payment by phone",
sub3p:"Thirty per cent to book the room, the balance on arrival. You pay on the secure page of lomi, our payment provider: Wave, MTN Mobile Money or bank card.",
testp:"<b>Test mode.</b> No money moves: use lomi\u2019s test numbers and cards.",
envp:"Pay the deposit",repr:"Resume the payment",
py3n:"Bank card<em>Visa · Mastercard</em>",
annul:"Free cancellation up to 48 h before arrival, deposit refunded in full. After that, the deposit is retained by the property.",
retr2:"Back",env:"Send my request",
h2d:"{{CT_EN}}",refn:"Note this reference: it identifies your file.",
ns1:"The front desk checks availability and replies within 24 h, by e-mail and by WhatsApp.",
ns2:"Once the room is confirmed, you receive the link to pay the 30 % deposit.",
fb1:"Back to home",fb2:"Add an experience",
rcat:"Your room",rr1:"Check-in",rr2:"Check-out",rr3:"Guests",rr4:"Tourist tax",
rr5:"Breakfast",rr5v:"Included",rr6:"Total stay",
rac:"Deposit to pay today:",rso:"Balance on arrival:"};

''' + LANG_JS

HTML = (page(
 "Réserver votre séjour — Hôtel Evannath, Assinie",
 "Réservez en direct à l'Hôtel Evannath, Assinie PK 19 : sept catégories de 67 000 à 280 000 FCFA la nuit, acompte de 30 % par Wave, MTN ou carte bancaire.",
 "r-standard", CSS, '\n'.join(body), JS, slug="reserver").replace(
 '<meta property="og:image"', (('' if PROSPECTION else '<meta name="robots" content="noindex, follow">\n') + '<meta property="og:image"')))
print('reserver.html         ok — tunnel en 3 etapes')

# Les textes de confirmation suivent ENVOI_WHATSAPP : voir _chrome.py.
# L'echappement couvre les dictionnaires JS, delimites par des apostrophes.
for _m, _v in (('{{CT}}',    CONF_TITRE    or 'Demande envoyée'),
               ('{{CT_EN}}', CONF_TITRE_EN or 'Request sent'),
               ('{{CG}}',    CONF_GESTE    or 'Merci, votre demande est partie à la réception.'),
               ('{{CG_EN}}', CONF_GESTE_EN or ''),
               ('{{PART}}',    ' part sur WhatsApp.' if ENVOI_WHATSAPP
                               else ' est partie à la réception.'),
               ('{{PART_EN}}', ' goes out on WhatsApp.' if ENVOI_WHATSAPP
                               else ' has gone to the front desk.')):
    HTML = HTML.replace(_m, _v.replace("'", "\'"))

io.open('reserver.html', 'w', encoding='utf-8').write(HTML)

NL_ = chr(10)
# La grille que le SERVEUR lit pour calculer l'acompte a encaisser. Le montant
# ne vient jamais de la page : un navigateur se modifie, et l'on encaisserait
# ce qu'il annonce. Meme source que la page, pour que les deux tombent juste.
io.open('api/_grille.json', 'w', encoding='utf-8').write(json.dumps({
    'taxe': TAXE_SEJOUR,
    'acompte': PART_ACOMPTE,
    'chambres': {slug: {'nom': nom, 'prix': prix, 'max': mx}
                 for slug, (nom, prix, mx, _img) in CHAMBRES.items()},
}, ensure_ascii=False, indent=1) + NL_)
