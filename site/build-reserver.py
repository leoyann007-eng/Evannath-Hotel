# -*- coding: utf-8 -*-
"""Genere reserver.html : le tunnel de reservation en trois etapes.

Remplace les alert() qui terminaient chaque formulaire. La page lit les
parametres passes par les fiches chambres (?chambre=&du=&au=&pax=), calcule
le sejour, collecte les coordonnees et simule le paiement de l'acompte.
"""
import io, json
from _chrome import PROSPECTION
from _chrome import ENVOI_JS, PIEGE, secours
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

CSS = """
.head{padding:150px 0 30px}
.head h1{margin:10px 0 14px}
.head p{max-width:56ch;font-size:1.04rem}

/* fil des etapes */
.steps{display:flex;gap:0;border:1px solid var(--line);margin-bottom:48px}
.steps div{flex:1;padding:18px 20px;border-right:1px solid var(--line);display:flex;gap:14px;align-items:center;transition:.4s}
.steps div:last-child{border-right:0}
.steps div.on{background:var(--bark-2)}
.steps div.done{background:rgba(143,174,99,.07)}
.steps i{font-style:normal;width:26px;height:26px;border:1px solid var(--line);display:grid;place-items:center;
  font-size:11px;font-weight:700;color:var(--muted);flex:0 0 auto;transition:.4s}
.steps div.on i{border-color:var(--bronze);color:var(--bronze)}
.steps div.done i{border-color:var(--palm);color:var(--palm)}
.steps b{font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;font-weight:700;color:var(--muted)}
.steps div.on b{color:var(--cream)}
.steps div.done b{color:var(--palm)}

.grid{display:grid;grid-template-columns:1fr 400px;gap:56px;align-items:start;padding-bottom:100px}
.pane{display:none}
.pane.on{display:block}
.pane h2{margin-bottom:8px}
.pane>p.sub{color:#B4A794;margin-bottom:30px}

.f{display:flex;flex-direction:column;margin-bottom:18px}
/* Largeur explicite : sans elle, un <select> reclame la largeur de son
   option la plus longue — « Mezzanine superieure … » poussait la colonne,
   donc la page, de 34 px sur un ecran de 320. min-width:0 ne suffit pas :
   le navigateur garde la taille intrinseque comme plancher. */
.f input,.f select,.f textarea{width:100%}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
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
.recap .row span:last-child{color:#CFC3B2;text-align:right;font-variant-numeric:tabular-nums}
.recap .tot{display:flex;justify-content:space-between;align-items:baseline;gap:14px;margin-top:18px;padding-top:16px;border-top:1px solid var(--line)}
.recap .tot span{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:700}
.recap .tot b{font-family:var(--f-display);font-size:1.9rem;color:var(--bronze-2);font-variant-numeric:tabular-nums;font-weight:400}
.recap .acompte{margin-top:14px;padding:14px 16px;border:1px solid var(--line);font-size:13px;color:var(--muted)}
.recap .acompte b{color:var(--bronze-2);font-weight:600}

/* confirmation */
.done-box{text-align:center;padding:20px 0 60px}
.done-box .tick{width:72px;height:72px;border:1px solid var(--palm);border-radius:50%;display:grid;place-items:center;
  margin:0 auto 28px;color:var(--palm);font-size:32px}
.done-box h2{margin-bottom:14px}
.done-box>p{max-width:50ch;margin:0 auto 12px}
.ref{display:inline-block;margin-top:20px;border:1px solid var(--line);padding:14px 22px;
  font-family:var(--f-display);font-size:1.3rem;color:var(--bronze-2);letter-spacing:.1em}
.done-box .g{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:34px}
.next-steps{border:1px solid var(--line);margin-top:44px;text-align:left;max-width:560px;margin-inline:auto}
.next-steps div{padding:16px 22px;border-bottom:1px solid var(--line);display:flex;gap:16px;font-size:14.5px;color:#CFC3B2}
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
  <div class="steps" id="steps">
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
      <p class="sub" data-t="sub3">Trente pour cent pour bloquer la chambre, le solde à l'arrivée. Indiquez le moyen qui vous arrange : la réception vous envoie le lien de paiement une fois la disponibilité confirmée.</p>

      <div class="pay">
        <label><input type="radio" name="pay" value="Wave" checked><span>Wave<em data-t="py0">Le plus utilisé en Côte d'Ivoire</em></span></label>
        <label><input type="radio" name="pay" value="Orange Money"><span>Orange Money<em data-t="py1">Paiement par téléphone</em></span></label>
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
      </div>
    </section>

    <!-- 4 ─────────────────────────────────────── -->
    <section class="pane" id="p4">
      <div class="done-box">
        <div class="tick">✓</div>
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
      <div class="row"><span data-t="rr4">Taxe de séjour</span><span id="rt">—</span></div>
      <div class="row"><span data-t="rr5">Petit-déjeuner</span><span style="color:var(--palm)" data-t="rr5v">Inclus</span></div>
      <div class="tot"><span data-t="rr6">Total séjour</span><b id="rtot">—</b></div>
      <div class="acompte"><span data-t="rac">Acompte à régler aujourd'hui :</span> <b id="racc">—</b><br>
        <span style="font-size:12px"><span data-t="rso">Solde à l'arrivée :</span> <b id="rsolde" style="color:#CFC3B2;font-weight:600">—</b></span></div>
    </div>
  </aside>
</div>

''' + FOOTER]

JS = NAV_JS + ENVOI_JS + '''

var CH=''' + json.dumps(CHAMBRES, ensure_ascii=False) + ''';
var TAX=1500; // taxe de séjour par personne et par nuit

var cat=document.getElementById('cat'),d1=document.getElementById('d1'),
    d2=document.getElementById('d2'),pax=document.getElementById('pax');

Object.keys(CH).forEach(function(k){
  var o=document.createElement('option');
  o.value=k; o.textContent=CH[k][0]+' — '+fmt(CH[k][1])+' FCFA';
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
           merci:'{{CG}}Merci ',dem:'. Votre demande pour la ',du:' du ',au:' au ',
           part:"{{PART}}",
           solde:"Le solde se règle à l'arrivée, sur place.",
           nav1:'Votre navette aéroport est notée (',nav2:"). Le solde se règle à l'arrivée."},
     en:{loc:'en-GB',p1:' guest',pp:' guests',n1:'Night',nn:'Nights',tarif:'Rate',
           merci:'{{CG_EN}}Thank you ',dem:'. Your request for the ',du:' from ',au:' to ',
           part:'{{PART_EN}}',
           solde:'The balance is settled on arrival, at the hotel.',
           nav1:'Your airport shuttle is noted (',nav2:'). The balance is settled on arrival.'}};
function jour(v){return v?new Date(v).toLocaleDateString(T[LG].loc,{weekday:'long',day:'numeric',month:'long'}):'—'}
function EVN_LANG(lg){ LG=T[lg]?lg:'fr'; remplirPax(); calc(); }

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
  var sejour=c[1]*n, taxe=TAX*p*n, total=sejour+taxe, acc=Math.round(total*0.3);

  document.getElementById('rimg').src='img/opt/'+c[3]+'.jpg';
  document.getElementById('rimg').alt=c[0];
  document.getElementById('rnom').textContent=c[0];
  document.getElementById('rd1').textContent=jour(d1.value);
  document.getElementById('rd2').textContent=jour(d2.value);
  document.getElementById('rnl').textContent=n>1?T[LG].nn:T[LG].n1;
  document.getElementById('rn').textContent=n;
  document.getElementById('rp').textContent=p+(p>1?T[LG].pp:T[LG].p1);
  document.getElementById('rul').textContent=fmt(c[1])+' × '+n;
  document.getElementById('ru').textContent=fmt(sejour);
  document.getElementById('rt').textContent=fmt(taxe);
  document.getElementById('rtot').textContent=fmt(total);
  document.getElementById('racc').textContent=fmt(acc)+' FCFA';
  document.getElementById('rsolde').textContent=fmt(total-acc)+' FCFA';
}
cat.addEventListener('change',function(){remplirPax();calc()});
[d1,d2,pax].forEach(function(e){e.addEventListener('change',calc)});
calc();

// ── etapes ────────────────────────────────────
function etape(n){
  [1,2,3,4].forEach(function(i){
    var p=document.getElementById('p'+i);
    if(p)p.classList.toggle('on',i===n);
  });
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
document.getElementById('pay').onclick=function(){
  var moyen=document.querySelector('input[name=pay]:checked').value;
  var c=CH[cat.value];
  var nv=document.getElementById('nav').value;
  var navette = nv==='non' ? 'non' : (nv==='ar' ? 'aller et retour' : 'aller simple');

  var d={nom:document.getElementById('fn').value.trim()+' '+document.getElementById('ln').value.trim(),
         email:document.getElementById('em').value.trim(),
         tel:document.getElementById('tl').value.trim(),
         chambre:c[0], arrivee:jour(d1.value), depart:jour(d2.value),
         nuits:document.getElementById('rn').textContent, personnes:pax.value,
         total:document.getElementById('rtot').textContent+' FCFA',
         acompte:document.getElementById('racc').textContent,
         paiement:moyen,
         message:'Navette a\u00e9roport : '+navette
                 +(document.getElementById('note') && document.getElementById('note').value
                   ? N+document.getElementById('note').value : '')};

  function resume(){
    return "Bonjour, je souhaite r\u00e9server \u00e0 l\\'H\u00f4tel Evannath."+N+N
      +'Nom : '+d.nom+N+'T\u00e9l\u00e9phone : '+d.tel+N+'E-mail : '+d.email+N+N
      +'Chambre : '+d.chambre+N+'Arriv\u00e9e : '+d.arrivee+N+'D\u00e9part : '+d.depart+N
      +'Nuits : '+d.nuits+N+'Personnes : '+d.personnes+N+N
      +'Total estim\u00e9 : '+d.total+N+'Acompte (30 %) : '+d.acompte+N
      +'Paiement souhait\u00e9 : '+d.paiement+N+d.message;
  }
  var CHAMP={nom:'fn',email:'em',tel:'tl'};

  EVN.envoyer('reservation',d,{
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
};

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
py0:"The most used in Côte d\u2019Ivoire",py1:"Payment by phone",py2:"Payment by phone",
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
 "Réservez en direct à l'Hôtel Evannath, Assinie PK 19 : sept catégories de 67 000 à 280 000 FCFA la nuit, acompte de 30 % par Wave, Orange Money, MTN ou carte bancaire.",
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
