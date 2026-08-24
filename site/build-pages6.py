# -*- coding: utf-8 -*-
"""Genere circuits.html : Packs Vacances (campagne Facebook) + circuits + Mechoui Party."""
import io
import _schema
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV

CSS = """
.head{padding:150px 0 46px}
.head h1{margin:10px 0 20px}
.head .lede{font-size:1.1rem;max-width:60ch}
.camp{border:1px solid var(--bronze);background:var(--bark-2);padding:34px;margin-bottom:56px}
.camp .top{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;flex-wrap:wrap;margin-bottom:26px}
.camp .live{display:inline-flex;align-items:center;gap:9px;font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--palm);font-weight:700}
.camp .live i{width:7px;height:7px;border-radius:50%;background:var(--palm);display:inline-block;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
.camp h2{margin:12px 0 0}
.camp>p{max-width:62ch}
.packs{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:26px}
.pack{border:1px solid var(--line);overflow:hidden;background:var(--bark);transition:.45s}
.pack:hover{border-color:rgba(185,138,80,.55);transform:translateY(-4px)}
.pack .ph{aspect-ratio:3/2;overflow:hidden}
.pack .ph img{width:100%;height:100%;object-fit:cover;transition:1s cubic-bezier(.2,.8,.2,1)}
.pack:hover .ph img{transform:scale(1.07)}
.pack .in{padding:20px}
.pack h3{font-size:1.12rem;margin-bottom:10px}
.pack b{font-family:var(--f-display);font-size:1.55rem;color:var(--bronze);display:block;line-height:1;font-variant-numeric:tabular-nums;font-weight:400}
.pack span{font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600;display:block;margin-top:5px}
.pack .pick{width:100%;margin-top:16px;text-align:center}
.star{display:grid;grid-template-columns:1.15fr 1fr;border:1px solid var(--line);margin-bottom:64px;background:var(--bark-2)}
.star .ph{position:relative;overflow:hidden;min-height:420px}
.star .ph img{width:100%;height:100%;object-fit:cover}
.star .badge{position:absolute;top:20px;left:20px;background:var(--bronze);color:var(--night);font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;padding:8px 14px}
.star .txt{padding:48px}
.star h2{margin:12px 0 16px}
.star .incl{list-style:none;margin:24px 0}
.star .incl li{padding:11px 0;border-bottom:1px solid var(--line);font-size:14.5px;color:#CFC3B2;display:flex;gap:13px}
.star .incl i{color:var(--palm);font-style:normal}
.star .foot{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;flex-wrap:wrap;margin-top:28px}
.star .pr b{font-family:var(--f-display);font-size:2.7rem;color:var(--bronze);display:block;line-height:1;font-variant-numeric:tabular-nums;font-weight:400}
.star .pr span{font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:600}
.filters{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:34px}
.filters button{background:none;border:1px solid var(--line);color:var(--muted);font:700 10.5px/1 var(--f-body);letter-spacing:.16em;text-transform:uppercase;padding:14px 20px;cursor:pointer;transition:.3s}
.filters button.on,.filters button:hover{border-color:var(--bronze);color:var(--bronze)}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.c{background:var(--bark-2);border:1px solid var(--line);display:flex;flex-direction:column;overflow:hidden;transition:.5s cubic-bezier(.2,.8,.2,1)}
.c.hide{display:none}
.c:hover{transform:translateY(-6px);border-color:rgba(185,138,80,.5)}
.c .ph{aspect-ratio:16/10;overflow:hidden;position:relative}
.c .ph img{width:100%;height:100%;object-fit:cover;transition:1s cubic-bezier(.2,.8,.2,1)}
.c:hover .ph img{transform:scale(1.07)}
.c .tag{position:absolute;top:13px;left:13px;background:rgba(23,16,10,.88);backdrop-filter:blur(6px);color:var(--bronze);font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;padding:7px 12px;font-weight:700}
.c .in{padding:24px;display:flex;flex-direction:column;flex:1}
.c h3{margin-bottom:12px}
.c ul{list-style:none;margin:0 0 20px;flex:1}
.c li{font-size:13.5px;color:#B7A894;padding:6px 0 6px 18px;position:relative}
.c li::before{content:"";position:absolute;left:0;top:14px;width:6px;height:6px;background:var(--bronze);opacity:.65}
.c .foot{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;border-top:1px solid var(--line);padding-top:16px}
.c .pr b{font-family:var(--f-display);font-size:1.7rem;color:var(--bronze);display:block;line-height:1;font-variant-numeric:tabular-nums;font-weight:400}
.c .pr span{font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.pick{font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--bronze);border:1px solid var(--bronze);padding:13px 16px;cursor:pointer;background:none;font-family:var(--f-body);font-weight:700;white-space:nowrap;transition:.3s}
.pick:hover{background:var(--bronze);color:var(--night)}
.weekly{margin:78px 0;border:1px solid var(--line);display:grid;grid-template-columns:1fr 1.3fr;background:var(--bark-2)}
.weekly .ph{overflow:hidden;min-height:280px}
.weekly .ph img{width:100%;height:100%;object-fit:cover}
.weekly .txt{padding:44px}
.weekly .when{display:inline-flex;align-items:center;gap:10px;border:1px solid var(--line);padding:9px 15px;font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--bronze);font-weight:700;margin-bottom:20px}
.weekly .when i{width:7px;height:7px;border-radius:50%;background:var(--palm);display:inline-block}
.weekly h2{margin-bottom:14px}
.weekly .perks{display:flex;gap:26px;flex-wrap:wrap;margin-top:24px;font-size:14px;color:#CFC3B2}
.weekly .perks span{display:flex;gap:9px;align-items:center}
.weekly .perks em{color:var(--palm);font-style:normal}
.req{background:var(--bark-2);padding:88px 0;border-top:1px solid var(--line)}
.req-grid{display:grid;grid-template-columns:1fr 400px;gap:56px;align-items:start;margin-top:40px}
.form .f{margin-bottom:18px}
.form label{display:block;font-size:9.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--bronze);margin-bottom:7px;font-weight:700}
.form input,.form select,.form textarea{width:100%;min-height:46px;background:transparent;border:1px solid var(--line);color:var(--cream);font:400 15px/1.5 var(--f-body);padding:11px 13px;outline:none;transition:.3s}
.form textarea{min-height:96px;resize:vertical}
.form input:focus,.form select:focus,.form textarea:focus{border-color:var(--bronze)}
.form select option{background:var(--bark-2);color:var(--cream)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.recap{background:var(--bark);border:1px solid var(--line);padding:28px;position:sticky;top:110px}
.recap h3{margin-bottom:18px}
.recap .row{display:flex;justify-content:space-between;gap:14px;font-size:14px;color:var(--muted);padding:9px 0;border-bottom:1px solid var(--line)}
.recap .row span:last-child{color:#CFC3B2;text-align:right;font-variant-numeric:tabular-nums}
.recap .tot{display:flex;justify-content:space-between;align-items:baseline;gap:14px;margin-top:18px;padding-top:16px;border-top:1px solid var(--line)}
.recap .tot span{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:700}
.recap .tot b{font-family:var(--f-display);font-size:1.9rem;color:var(--bronze-2);font-variant-numeric:tabular-nums;font-weight:400}
.recap .btn{width:100%;margin-top:20px}
.recap .note{font-size:12.5px;color:var(--muted);text-align:center;margin-top:14px;line-height:1.5}
@media(max-width:1080px){
  .grid,.packs{grid-template-columns:repeat(2,1fr)}
  .star,.weekly{grid-template-columns:1fr}
  .star .ph,.weekly .ph{min-height:280px}
  .req-grid{grid-template-columns:1fr;gap:34px}
  .recap{position:static}
}
@media(max-width:720px){
  .head{padding:126px 0 34px}
  .grid,.packs,.two{grid-template-columns:1fr}
  .star .txt,.weekly .txt,.camp{padding:24px}
  .c .foot{flex-direction:column;align-items:stretch;gap:14px}
  .pick{text-align:center}
}
"""

PACKS = [
 ('Pack Famille','250000','forfait','g-aerien-t','Vue aérienne du domaine Evannath','p1','uf','FCFA · le forfait','250 000'),
 ('Pack Couple','150000','forfait','c-ponton','Le ponton sur la lagune au couchant','p2','uf','FCFA · le forfait','150 000'),
 ('Pack Chillday','50000','personne','g-terrasse-t','Terrasse et transats de l\'hôtel','p3','up','FCFA · par personne','50 000'),
 ('Pack Enfant','15000','enfant','ig-enfants',"Des enfants dans la piscine de l'hôtel",'p4','ue','FCFA · par enfant','15 000'),
]

CARDS = [
 ('duo','c-ponton','Le ponton de bois sur la lagune, au couchant','g1','Romantique','t1','Évasion Romantique',
  [('s11','Cocktails de charme'),('s12','Balade dînatoire aux chandelles'),('s13','Petit-déjeuner au lit'),('s14','Duo de massages')],
  '100 000','100000','forfait','pf','FCFA · le forfait'),
 ('duo','r-standard','Chambre Standard de l\'Hôtel Evannath','g2','Week-end','t2','Week-End Intense',
  [('s21','Chambre Standard + 2 petits-déjeuners'),('s22','Apéro, puis dîner ou déjeuner'),('s23','Balade lagunaire ou jet ski'),('s24','Baignade, fitness et massage')],
  '155 000','155000','forfait','pf','FCFA · le forfait'),
 ('fam grp','g-lagune','La lagune Aby et les îles environnantes','g3','Découverte','t3','Découvertes Touristiques',
  [('s31','Découverte des îles environnantes'),('s32','Balade touristique guidée'),('s33','Histoire de la commune d\'Assinie'),('s34','En-cas à emporter')],
  '35 000','35000','personne','pp','FCFA · par personne'),
 ('fam','c-piscine','La piscine de l\'hôtel en fin de journée','g4','Enfants','t4','Découvertes Junior',
  [('s41','Maquillage enfant et accès aux jeux'),('s42','Atelier cuisine et atelier peinture'),('s43','Conte en bordure d\'eau, le soir'),('s44','Soins princes &amp; princesses')],
  '25 000','25000','enfant','pe','FCFA · par enfant'),
 ('long fam','g-vue','Vue sur la lagune et les cocotiers d\'Assinie','g5','Long séjour','t5','Long Holidays',
  [('s51','−10 % sur chaque nuitée supplémentaire'),('s52','Balade lagunaire offerte dès 3 jours'),('s53','Applicable à toutes les catégories'),('s54','Cumulable avec la navette aéroport')],
  '25 000','25000','forfait','pf','FCFA · le forfait'),
 ('grp fam','g-resto','Salle de restaurant dressée pour un groupe','g6','Dès 10 personnes','t6','Coffret Anniversaire',
  [('s61','Salle privatisée, offerte'),('s62','Buffet : entrées, plats chauds, dessert'),('s63','Boissons comprises'),('s64','Sonorisation et technicien son offerts')],
  '28 000','28000','personne','pp','FCFA · par personne'),
]

b = [header('#demande','Réserver'), drawer('circuits.html'), '''
<div class="wrap head">
  <nav class="crumb" aria-label="Fil d'Ariane">
    <a href="index.html" data-t="c1">Accueil</a> &nbsp;·&nbsp; <span data-t="c2">Circuits &amp; Offres</span>
  </nav>
  <span class="eyebrow" data-t="eb">Onze offres &amp; un rendez-vous hebdomadaire</span>
  <h1 data-t="h1">Circuits &amp; Offres</h1>
  <p class="lede" data-t="lede">Des séjours déjà composés — chambre, repas, activités et attentions comprises. Choisissez, indiquez vos dates, et la réception s'occupe du reste.</p>
</div>

<div class="wrap">

  <!-- Campagne relevée sur la page Facebook (21 000 abonnés) : absente du site actuel -->
  <section class="camp reveal">
    <div class="top">
      <div>
        <span class="live"><i></i><span data-t="cl">Campagne en cours</span></span>
        <h2 data-t="ct">Packs Vacances</h2>
      </div>
      <p style="font-size:13px;color:var(--muted);max-width:30ch;text-align:right" data-t="cs">Annoncés sur notre page Facebook · +225 01 51 52 75 75</p>
    </div>
    <p data-t="cp">« Les vacances qui vous ressemblent. » Quatre formules pensées pour la saison, réservables directement ici.</p>
    <div class="packs">''']

for name, price, unit, img, alt, key, ukey, ulab, disp in PACKS:
    b.append('''      <article class="pack">
        <div class="ph"><picture><source srcset="img/opt/%s.webp" type="image/webp"><img loading="lazy" src="img/opt/%s.jpg" width="700" height="467" alt="%s"></picture></div>
        <div class="in"><h3 data-t="%s">%s</h3><b>%s</b><span data-t="%s">%s</span>
        <button class="pick pickbtn" data-c="%s" data-p="%s" data-u="%s" data-t="ch">Choisir</button></div>
      </article>''' % (img, img, alt, key, name, disp, ukey, ulab, name, price, unit))

b.append('''    </div>
  </section>

  <article class="star reveal">
    <div class="ph">
      <picture><source srcset="img/opt/r-mezzanine.webp" type="image/webp">
      <img src="img/opt/r-mezzanine.jpg" width="900" height="600" alt="Mezzanine Supérieure décorée pour une lune de miel"></picture>
      <span class="badge" data-t="bd">Le plus demandé</span>
    </div>
    <div class="txt">
      <span class="eyebrow" data-t="e0">Pour deux</span>
      <h2 data-t="t0">Lune de miel<br>inoubliable</h2>
      <p data-t="d0">Deux nuits en Mezzanine Supérieure, décorée pour l'occasion avant votre arrivée. La catégorie duplex, avec terrasse privative et vue sur le domaine.</p>
      <ul class="incl">
        <li><i>✓</i><span data-t="s01">2 nuits en Mezzanine Supérieure</span></li>
        <li><i>✓</i><span data-t="s02">Décoration de la chambre à votre arrivée</span></li>
        <li><i>✓</i><span data-t="s03">Petits-déjeuners inclus</span></li>
        <li><i>✓</i><span data-t="s04">Navette aéroport gratuite</span></li>
      </ul>
      <div class="foot">
        <div class="pr"><b>340 000</b><span data-t="pf">FCFA · le forfait</span></div>
        <button class="btn btn-solid pickbtn" data-c="Lune de miel inoubliable" data-p="340000" data-u="forfait" data-t="cta">Réserver ce circuit</button>
      </div>
    </div>
  </article>

  <div class="filters reveal">
    <button class="on" data-f="all" data-t="fa">Tout voir</button>
    <button data-f="duo" data-t="fb">Pour deux</button>
    <button data-f="fam" data-t="fc">En famille</button>
    <button data-f="grp" data-t="fd">Groupes</button>
    <button data-f="long" data-t="fe">Séjours longs</button>
  </div>

  <div class="grid" id="gr">''')

for cat, img, alt, gkey, glab, tkey, tlab, items, disp, price, unit, ukey, ulab in CARDS:
    b.append('''    <article class="c reveal" data-cat="%s">
      <div class="ph"><picture><source srcset="img/opt/%s.webp" type="image/webp">
        <img loading="lazy" src="img/opt/%s.jpg" width="900" height="562" alt="%s"></picture>
        <span class="tag" data-t="%s">%s</span></div>
      <div class="in">
        <h3 data-t="%s">%s</h3>
        <ul>''' % (cat, img, img, alt, gkey, glab, tkey, tlab))
    for k, t in items:
        b.append('          <li data-t="%s">%s</li>' % (k, t))
    b.append('''        </ul>
        <div class="foot"><div class="pr"><b>%s</b><span data-t="%s">%s</span></div>
        <button class="pick pickbtn" data-c="%s" data-p="%s" data-u="%s" data-t="ch">Choisir</button></div>
      </div>
    </article>''' % (disp, ukey, ulab, tlab, price, unit))

b.append('''  </div>

  <section class="weekly reveal">
    <div class="ph"><picture><source srcset="img/opt/c-bar.webp" type="image/webp">
      <img loading="lazy" src="img/opt/c-bar.jpg" width="900" height="600" alt="Le bar et la salle en rotin de l'Hôtel Evannath"></picture></div>
    <div class="txt">
      <span class="when"><i></i><span data-t="w0">Chaque samedi, dès 15 h</span></span>
      <h2 data-t="w1">Méchoui Party</h2>
      <p data-t="w2">Ce n'est pas un forfait : c'est le rendez-vous du samedi après-midi, ouvert à tous — clients de l'hôtel comme visiteurs de passage. Méchoui au bord de l'eau, puis la soirée continue au night-club.</p>
      <div class="perks">
        <span><em>✓</em><span data-t="w3">Un cocktail offert</span></span>
        <span><em>✓</em><span data-t="w4">Happy hour au night-club</span></span>
        <span><em>✓</em><span data-t="w5">−10 % sur toutes les boissons</span></span>
      </div>
      <div style="margin-top:28px"><a href="#demande" class="btn" data-t="w6">Réserver une table</a></div>
    </div>
  </section>

</div>

<section class="req" id="demande">
 <div class="wrap">
  <span class="eyebrow" data-t="e9">Votre demande</span>
  <h2 data-t="h9">Réserver un circuit</h2>
  <div class="req-grid">
    <form class="form" id="rf">
      <div class="f"><label for="circ" data-t="l1">Circuit choisi</label>
        <select id="circ">
          <option value="340000|forfait">Lune de miel inoubliable — 340 000 FCFA</option>
          <option value="250000|forfait">Pack Famille — 250 000 FCFA</option>
          <option value="155000|forfait">Week-End Intense — 155 000 FCFA</option>
          <option value="150000|forfait">Pack Couple — 150 000 FCFA</option>
          <option value="100000|forfait">Évasion Romantique — 100 000 FCFA</option>
          <option value="50000|personne">Pack Chillday — 50 000 FCFA / pers.</option>
          <option value="35000|personne">Découvertes Touristiques — 35 000 FCFA / pers.</option>
          <option value="28000|personne">Coffret Anniversaire — 28 000 FCFA / pers.</option>
          <option value="25000|enfant">Découvertes Junior — 25 000 FCFA / enfant</option>
          <option value="25000|forfait">Long Holidays — 25 000 FCFA</option>
          <option value="15000|enfant">Pack Enfant — 15 000 FCFA / enfant</option>
        </select>
      </div>
      <div class="two">
        <div class="f"><label for="dt" data-t="l2">Date souhaitée</label><input type="date" id="dt"></div>
        <div class="f"><label for="qt" data-t="l3">Nombre</label><input type="number" id="qt" min="1" max="40" value="2"></div>
      </div>
      <div class="two">
        <div class="f"><label for="nm" data-t="l4">Nom complet</label><input type="text" id="nm" placeholder="Aya Kouassi" required></div>
        <div class="f"><label for="tel" data-t="l5">Téléphone / WhatsApp</label><input type="tel" id="tel" placeholder="+225 01 02 03 04 05" required></div>
      </div>
      <div class="f"><label for="em" data-t="l6">E-mail</label><input type="email" id="em" placeholder="vous@exemple.com" required></div>
      <div class="f"><label for="msg" data-t="l7">Précisions (facultatif)</label><textarea id="msg" placeholder="Occasion particulière, allergies, heure d'arrivée…"></textarea></div>
    </form>

    <aside class="recap">
      <h3 data-t="r0">Votre récapitulatif</h3>
      <div class="row"><span data-t="r1">Circuit</span><span id="rc">Lune de miel inoubliable</span></div>
      <div class="row"><span data-t="r2">Date</span><span id="rd">—</span></div>
      <div class="row"><span id="rql">Quantité</span><span id="rq">1 forfait</span></div>
      <div class="row"><span data-t="r4">Tarif unitaire</span><span id="ru">340 000</span></div>
      <div class="tot"><span data-t="r5">Total</span><b id="rt">340 000</b></div>
      <button type="submit" form="rf" class="btn btn-solid" data-t="r6">Envoyer la demande</button>
      <p class="note" data-t="r7">Réponse de la réception sous 24 h. Aucun paiement à cette étape.</p>
    </aside>
  </div>
 </div>
</section>

''' + FOOTER)

JS = NAV_JS + '''

document.querySelectorAll('.filters button').forEach(function(b){b.onclick=function(){
  document.querySelectorAll('.filters button').forEach(function(x){x.classList.remove('on')});b.classList.add('on');
  var f=b.dataset.f;
  document.querySelectorAll('.c').forEach(function(c){c.classList.toggle('hide',f!=='all'&&c.dataset.cat.split(' ').indexOf(f)<0)});
}});

var circ=document.getElementById('circ'),dt=document.getElementById('dt'),qt=document.getElementById('qt');
function iso(d){return new Date(d.getTime()-d.getTimezoneOffset()*6e4).toISOString().slice(0,10)}
dt.value=iso(new Date(Date.now()+864e5*7)); dt.min=iso(new Date());
function fmt(n){return n.toLocaleString('fr-FR').replace(/ | |,/g,' ')}
var UNITS={forfait:['forfait','forfaits'],personne:['personne','personnes'],enfant:['enfant','enfants']};
function recap(){
  var parts=circ.value.split('|'),prix=+parts[0],unite=parts[1];
  var label=circ.options[circ.selectedIndex].text.split('—')[0].trim();
  var n=Math.max(1,Math.min(40,+qt.value||1));
  // un forfait couple ne se multiplie pas : on ne compte que les unités facturables
  var facturable=(unite==='forfait')?1:n;
  var mots=UNITS[unite];
  document.getElementById('rc').textContent=label;
  document.getElementById('rd').textContent=dt.value?new Date(dt.value).toLocaleDateString('fr-FR',{day:'numeric',month:'long',year:'numeric'}):'—';
  document.getElementById('rql').textContent=(unite==='forfait')?'Forfait':'Quantité';
  document.getElementById('rq').textContent=facturable+' '+(facturable>1?mots[1]:mots[0]);
  document.getElementById('ru').textContent=fmt(prix);
  document.getElementById('rt').textContent=fmt(prix*facturable);
  qt.disabled=(unite==='forfait');
  qt.style.opacity=(unite==='forfait')?.45:1;
}
[circ,dt,qt].forEach(function(e){e.addEventListener('input',recap);e.addEventListener('change',recap)});
recap();

document.querySelectorAll('.pickbtn').forEach(function(b){b.onclick=function(){
  var want=b.dataset.p+'|'+b.dataset.u;
  for(var i=0;i<circ.options.length;i++){if(circ.options[i].value===want){circ.selectedIndex=i;break}}
  recap();
  document.getElementById('demande').scrollIntoView({behavior:'smooth',block:'start'});
}});

document.getElementById('rf').addEventListener('submit',function(e){e.preventDefault();
  alert("Démonstration : la demande partirait à la réception et à bonjour@evannathhotel.com, avec une confirmation automatique au client.")});

var EN={''' + EN_NAV + '''cta:"Book this package",
c1:"Home",c2:"Packages &amp; Offers",eb:"Eleven offers &amp; one weekly gathering",h1:"Packages &amp; Offers",
lede:"Stays already put together — room, meals, activities and small touches included. Pick one, give us your dates, and the front desk handles the rest.",
cl:"Live campaign",ct:"Holiday Packs",cs:"Announced on our Facebook page · +225 01 51 52 75 75",
cp:"“Holidays that look like you.” Four seasonal packages, bookable right here.",
p1:"Family Pack",p2:"Couples Pack",p3:"Chillday Pack",p4:"Kids Pack",
uf:"FCFA · package",up:"FCFA · per person",ue:"FCFA · per child",
bd:"Most requested",e0:"For two",t0:"An unforgettable<br>honeymoon",
d0:"Two nights in a Superior Mezzanine, decorated before you arrive. The duplex category, with a private terrace overlooking the estate.",
s01:"2 nights in a Superior Mezzanine",s02:"Room decorated on arrival",s03:"Breakfasts included",s04:"Free airport shuttle",
pf:"FCFA · package",pp:"FCFA · per person",pe:"FCFA · per child",ch:"Select",
fa:"View all",fb:"For two",fc:"Family",fd:"Groups",fe:"Long stays",
g1:"Romantic",t1:"Romantic Escape",s11:"Signature cocktails",s12:"Candlelit dinner cruise",s13:"Breakfast in bed",s14:"Couples massage",
g2:"Weekend",t2:"Intense Weekend",s21:"Standard room + 2 breakfasts",s22:"Aperitif, then dinner or lunch",s23:"Lagoon cruise or jet ski",s24:"Swimming, gym and massage",
g3:"Discovery",t3:"Sightseeing Tours",s31:"The surrounding islands",s32:"Guided walking tour",s33:"The history of Assinie",s34:"Snack to take along",
g4:"Children",t4:"Junior Discovery",s41:"Face painting and play area",s42:"Cooking and painting workshops",s43:"Waterside storytelling at dusk",s44:"Little prince &amp; princess treatments",
g5:"Long stay",t5:"Long Holidays",s51:"−10 % on every extra night",s52:"Free lagoon cruise from 3 days",s53:"Valid on every category",s54:"Combines with the airport shuttle",
g6:"From 10 guests",t6:"Birthday Box",s61:"Private room, free of charge",s62:"Buffet: starters, mains, dessert",s63:"Drinks included",s64:"PA system and sound engineer included",
w0:"Every Saturday, from 3 pm",w1:"Méchoui Party",
w2:"This one is not a package: it is the Saturday afternoon gathering, open to everyone — hotel guests and visitors alike. Méchoui by the water, then the evening carries on at the night club.",
w3:"A complimentary cocktail",w4:"Happy hour at the night club",w5:"−10 % on all drinks",w6:"Book a table",
e9:"Your request",h9:"Book a package",l1:"Chosen package",l2:"Preferred date",l3:"Number",l4:"Full name",l5:"Phone / WhatsApp",l6:"Email",l7:"Notes (optional)",
r0:"Your summary",r1:"Package",r2:"Date",r4:"Unit price",r5:"Total",r6:"Send request",
r7:"The front desk replies within 24 h. No payment at this stage."};

''' + LANG_JS

LD = _schema.bloc(
    _schema.service('Circuits et forfaits', "Packs Vacances, lune de miel, week-end intense, circuits touristiques et coffret anniversaire à l'Hôtel Evannath, Assinie.", 'circuits', image='r-mezzanine'),
    _schema.hotel(),
    _schema.fil([('Accueil','index'),('Circuits & Offres',None)]))

io.open('circuits.html','w',encoding='utf-8').write(page(
 "Circuits &amp; Offres — Hôtel Evannath, Assinie",
 "Les forfaits de l'Hôtel Evannath à Assinie : Packs Vacances, lune de miel, évasion romantique, week-end intense, découvertes touristiques et junior, coffret anniversaire.",
 "r-mezzanine", CSS, '\n'.join(b), JS, slug="circuits", jsonld=LD))
print('circuits.html         ok')
