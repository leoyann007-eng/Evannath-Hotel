# -*- coding: utf-8 -*-
"""Genere suite-arabe.html (fiche chambre)."""
import io
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV

CSS = """
.head{padding:150px 0 34px}
.head-top{display:flex;justify-content:space-between;align-items:flex-end;gap:30px;flex-wrap:wrap}
.head h1{margin:10px 0 0}
.facts{display:flex;gap:26px;flex-wrap:wrap;margin-top:22px;font-size:13.5px;color:var(--muted)}
.facts b{color:var(--cream);font-weight:500}
.head-price{text-align:right}
.head-price b{font-family:var(--f-display);font-size:2.6rem;color:var(--bronze);display:block;line-height:1;font-variant-numeric:tabular-nums}
.head-price span{font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:600}
.mosaic{display:grid;grid-template-columns:2fr 1fr 1fr;grid-auto-rows:172px;gap:10px;margin-bottom:76px}
.mosaic figure{overflow:hidden;position:relative;cursor:pointer;background:var(--bark-2)}
.mosaic figure:first-child{grid-column:span 1;grid-row:span 2}
.mosaic img{width:100%;height:100%;object-fit:cover;transition:1s cubic-bezier(.2,.8,.2,1)}
.mosaic figure:hover img{transform:scale(1.07)}
.mosaic figcaption{position:absolute;left:0;right:0;bottom:0;padding:26px 14px 10px;
  background:linear-gradient(transparent,rgba(16,11,6,.94));
  font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--cream);font-weight:700;
  text-shadow:0 2px 10px rgba(10,6,3,.9)}
.body-grid{display:grid;grid-template-columns:1fr 372px;gap:56px;align-items:start;padding-bottom:100px}
.block{margin-bottom:56px}
.block .eyebrow{margin-bottom:14px}
.block h2{margin-bottom:18px}
.block p+p{margin-top:16px}
.amen{display:grid;grid-template-columns:repeat(2,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin-top:24px}
.amen div{background:var(--bark);padding:16px 18px;font-size:14px;display:flex;align-items:center;gap:12px;color:#CFC3B2}
.amen svg{width:17px;height:17px;stroke:var(--bronze);fill:none;stroke-width:1.4;flex:0 0 auto}
.incl{list-style:none;margin-top:22px}
.incl li{padding:15px 0;border-bottom:1px solid var(--line);display:flex;gap:16px;align-items:flex-start}
.incl b{display:block;color:var(--cream);font-weight:600;font-size:14.5px;margin-bottom:3px}
.incl p{font-size:13.5px;margin:0;color:var(--muted)}
.incl .chk{color:var(--palm);font-size:15px;line-height:1.5}
.cond{border:1px solid var(--line);margin-top:22px}
.cond div{padding:15px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:18px;font-size:14px}
.cond div:last-child{border-bottom:0}
.cond span:first-child{color:var(--muted);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;font-weight:600}
.panel{position:sticky;top:110px;background:var(--bark-2);border:1px solid var(--line);padding:28px}
.panel .from{font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);font-weight:600}
.panel .rate{font-family:var(--f-display);font-size:2.3rem;color:var(--bronze);line-height:1;margin:6px 0 2px;font-variant-numeric:tabular-nums}
.panel .per{font-size:12px;color:var(--muted);margin-bottom:24px}
.pf{margin-bottom:16px}
.pf label{display:block;font-size:9.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--bronze);margin-bottom:7px;font-weight:700}
.pf input,.pf select{width:100%;min-width:0;min-height:46px;background:transparent;border:1px solid var(--line);color:var(--cream);font:400 15px/1.4 var(--f-body);padding:10px 12px;outline:none;transition:.3s}
.pf input:focus,.pf select:focus{border-color:var(--bronze)}
.pf select option{background:var(--bark-2);color:var(--cream)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.calc{border-top:1px solid var(--line);margin-top:22px;padding-top:18px}
.calc .row{display:flex;justify-content:space-between;gap:14px;font-size:14px;color:var(--muted);padding:7px 0}
.calc .row span:last-child{color:#CFC3B2;font-variant-numeric:tabular-nums}
.calc .total{border-top:1px solid var(--line);margin-top:10px;padding-top:14px;display:flex;justify-content:space-between;align-items:baseline;gap:14px}
.calc .total span{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:700}
.calc .total b{font-family:var(--f-display);font-size:1.85rem;color:var(--bronze-2);font-variant-numeric:tabular-nums}
.panel .btn{width:100%;margin-top:20px}
.avail{display:flex;align-items:center;gap:9px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--palm);font-weight:700;margin-top:16px;justify-content:center}
.avail i{width:7px;height:7px;border-radius:50%;background:var(--palm);display:inline-block}
.panel .help{font-size:12.5px;color:var(--muted);text-align:center;margin-top:16px;line-height:1.5}
.panel .help a{color:var(--bronze);border-bottom:1px solid var(--line)}
.more{background:var(--bark-2);padding:88px 0}
.more-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:40px}
.rcard{background:var(--bark);border:1px solid var(--line);overflow:hidden;transition:.5s cubic-bezier(.2,.8,.2,1)}
.rcard:hover{transform:translateY(-6px);border-color:rgba(185,138,80,.5)}
.rcard .ph{aspect-ratio:4/3;overflow:hidden}
.rcard img{width:100%;height:100%;object-fit:cover;transition:1s cubic-bezier(.2,.8,.2,1)}
.rcard:hover img{transform:scale(1.07)}
.rcard div{padding:22px}
.rcard h3{margin-bottom:12px}
.rcard .p{display:flex;justify-content:space-between;align-items:baseline;border-top:1px solid var(--line);padding-top:14px;margin-top:4px}
.rcard .p b{font-family:var(--f-display);font-size:1.5rem;color:var(--bronze);font-variant-numeric:tabular-nums;font-weight:400}
.rcard .p span{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.mobar{display:none;position:fixed;left:0;right:0;bottom:0;z-index:95;background:rgba(30,21,13,.98);backdrop-filter:blur(14px);border-top:1px solid var(--line);padding:12px 18px;align-items:center;justify-content:space-between;gap:14px}
.mobar b{font-family:var(--f-display);font-size:1.35rem;color:var(--bronze);display:block;line-height:1;font-variant-numeric:tabular-nums}
.mobar span{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.mobar .btn{padding:14px 22px}
#lb{position:fixed;inset:0;background:rgba(10,6,3,.98);z-index:200;display:none;place-items:center;padding:40px}
#lb.on{display:grid}
#lb img{max-width:92vw;max-height:84vh;object-fit:contain}
#lbc{position:absolute;bottom:26px;left:0;right:0;text-align:center;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.lb-btn{position:absolute;background:rgba(16,11,6,.75);border:1px solid var(--line);color:var(--cream);width:48px;height:48px;cursor:pointer;font-size:20px;transition:.3s}
.lb-btn:hover{border-color:var(--bronze);color:var(--bronze)}
#lb .prev{left:26px;top:50%}#lb .next{right:26px;top:50%}#lb .close{top:26px;right:26px}
@media(max-width:1080px){
  .body-grid{grid-template-columns:1fr;gap:0}
  .panel{position:static;margin-bottom:56px}
  .mosaic{grid-template-columns:1fr 1fr;grid-auto-rows:180px}
  .mosaic figure:first-child{grid-column:span 2}
  .more-grid{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:720px){
  .head{padding:126px 0 26px}
  .head-price{text-align:left}
  .amen,.more-grid{grid-template-columns:1fr}
  .two{grid-template-columns:1fr}
  .mosaic{grid-template-columns:1fr;grid-auto-rows:210px}
  .mosaic figure:first-child{grid-column:span 1}
  .mobar{display:flex}
  body{padding-bottom:78px}
  #lb .prev{left:8px}#lb .next{right:8px}
}
"""

PHOTOS = [
 ('sa-main',"La Suite Arabe de l'Hôtel Evannath",'cap1','La suite'),
 ('sa-chambre2',"La seconde chambre de la Suite Arabe, textiles wax et accès balcon",'cap2','La seconde chambre'),
 ('sa-bain',"Salle de bain avec miroir soleil",'cap3','La salle de bain'),
 ('sa-salon',"Coin salon et espace de repos",'cap4','Le salon'),
 ('sa-terrasse',"Terrasse ombragée de l'hôtel",'cap5','La terrasse'),
]

AMEN = [
 ('a1','Air conditionné','<path d="M3 12h18M8 8h12M6 16h12"/>'),
 ('a2','Wifi gratuit','<path d="M5 13a10 10 0 0114 0M8.5 16.5a5 5 0 017 0"/><circle cx="12" cy="20" r="1"/>'),
 ('a3','Télévision smart','<rect x="3" y="5" width="18" height="12"/><path d="M9 21h6"/>'),
 ('a4','Deux lits king','<path d="M4 18v-6a8 8 0 0116 0v6M4 18h16M9 22h6"/>'),
 ('a5','Salon privatif','<path d="M6 21V9l6-5 6 5v12M10 21v-6h4v6"/>'),
 ('a6','Deux salles d\'eau','<path d="M4 12h16v5a3 3 0 01-3 3H7a3 3 0 01-3-3zM7 12V6a2 2 0 014 0"/>'),
 ('a7','Sèche-cheveux','<path d="M8 3v6a4 4 0 008 0V3M12 13v8M9 21h6"/>'),
 ('a8','Coffre-fort','<rect x="4" y="4" width="16" height="16"/><path d="M9 9h6v6H9z"/>'),
 ('a9','Accès piscine &amp; jacuzzi','<path d="M3 17c2 1 4-1 6 0s4 1 6 0 4-1 6 0M3 12c2 1 4-1 6 0s4 1 6 0 4-1 6 0"/>'),
 ('a10','Terrasse commune','<path d="M5 20V8h14v12M9 20v-5h6v5M3 8l9-5 9 5"/>'),
]

INCL = [
 ('i1','Petit-déjeuner pour tous les occupants','Servi au restaurant ou en terrasse, fruits frais et produits locaux.'),
 ('i2','Navette aéroport gratuite','Prise en charge et dépose à l\'aéroport Félix-Houphouët-Boigny, sans frais, à la demande.'),
 ('i3','Piscine, jacuzzi et salle de sport','Accès libre du lever du jour à la nuit tombée.'),
 ('i4','Wifi et parking','Gratuits sur tout le domaine.'),
]

MORE = [
 ('r-mezzanine','Mezzanine Supérieure','m1','Coin salon, équipements renforcés et terrasse privative. Jusqu\'à 4 personnes.','142 000'),
 ('r-anglaise','Suite Anglaise','m2','Vue directe sur la lagune Aby et la piscine. Le meilleur couchant du domaine.','107 000'),
 ('r-wax','Deluxe Supérieure','m3','Textiles wax, lits à baldaquin et salle à manger privative. Jusqu\'à 3 personnes.','97 000'),
]

b = [header('#reserver','Réserver'), drawer('index.html#chambres'), '''
<div class="wrap head">
  <nav class="crumb" aria-label="Fil d'Ariane">
    <a href="index.html" data-t="c1">Accueil</a> &nbsp;·&nbsp;
    <a href="index.html#chambres" data-t="c2">Chambres &amp; Suites</a> &nbsp;·&nbsp;
    <span>Suite Arabe</span>
  </nav>
  <div class="head-top">
    <div>
      <span class="eyebrow" data-t="sig">Catégorie signature</span>
      <h1>Suite Arabe</h1>
      <div class="facts">
        <span data-t="f1"><b>2</b> chambres</span>
        <span data-t="f2"><b>6</b> personnes</span>
        <span data-t="f3"><b>Salon</b> privatif</span>
        <span data-t="f4"><b>Décor</b> arabo-andalou</span>
      </div>
    </div>
    <div class="head-price"><b>280 000</b><span data-t="pn">FCFA / nuit</span></div>
  </div>
</div>

<div class="wrap">
  <div class="mosaic" id="gl">''']

for i, (img, alt, ck, clab) in enumerate(PHOTOS):
    ld = 'eager' if i == 0 else 'lazy'
    b.append('''    <figure><picture><source srcset="img/opt/%s-t.webp" type="image/webp">
      <img loading="%s" width="560" height="373" src="img/opt/%s-t.jpg" data-full="img/opt/%s.jpg" alt="%s"></picture>
      <figcaption data-t="%s">%s</figcaption></figure>''' % (img, ld, img, img, alt, ck, clab))

b.append('''  </div>
</div>

<div class="wrap body-grid">
 <div>
  <section class="block reveal">
    <span class="eyebrow" data-t="e1">La suite</span>
    <h2 data-t="h1x">Deux chambres,<br>un patio, un service dédié</h2>
    <p data-t="p1">C'est la plus grande de nos sept catégories, et la seule à proposer deux chambres séparées. Le décor arabo-andalou — bois sculpté, arcades, textiles brodés — a été composé pièce par pièce avec des artisans locaux, dans l'esprit qui guide tout l'établissement.</p>
    <p data-t="p2">Deux couples, une famille avec enfants grands, ou un groupe d'amis : la suite absorbe six personnes sans que personne ne se marche dessus. Le salon privatif sert de pièce de vie commune, et chaque chambre garde sa salle d'eau.</p>
    <p data-t="p3">C'est aussi la catégorie la plus demandée pour les lunes de miel et les anniversaires. Elle part vite en saison sèche — de décembre à mars, prévoyez de réserver plusieurs semaines à l'avance.</p>
  </section>

  <section class="block reveal">
    <span class="eyebrow" data-t="e2">Équipements</span>
    <h2 data-t="h2">Dans la suite</h2>
    <div class="amen">''')

for key, lab, ic in AMEN:
    b.append('      <div><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg><span data-t="%s">%s</span></div>' % (ic, key, lab))

b.append('''    </div>
  </section>

  <section class="block reveal">
    <span class="eyebrow" data-t="e3">Inclus</span>
    <h2 data-t="h3">Compris dans le tarif</h2>
    <ul class="incl">''')

for key, t, d in INCL:
    b.append('      <li><span class="chk">✓</span><div><b data-t="%s">%s</b><p data-t="%sp">%s</p></div></li>' % (key, t, key, d))

b.append('''    </ul>
  </section>

  <section class="block reveal">
    <span class="eyebrow" data-t="e4">Conditions</span>
    <h2 data-t="h4">Bon à savoir</h2>
    <div class="cond">
      <div><span data-t="k1">Arrivée</span><span>à partir de 14 h 00</span></div>
      <div><span data-t="k2">Départ</span><span>avant 12 h 00</span></div>
      <div><span data-t="k3">Annulation</span><span data-t="v3">gratuite jusqu'à 48 h avant</span></div>
      <div><span data-t="k4">Acompte</span><span data-t="v4">30 % à la réservation</span></div>
      <div><span data-t="k5">Animaux</span><span data-t="v5">non admis</span></div>
      <div><span data-t="k6">Paiement</span><span>Wave · Orange Money · MTN · carte</span></div>
    </div>
  </section>
 </div>

 <aside class="panel" id="reserver">
  <span class="from" data-t="from">À partir de</span>
  <div class="rate">280 000 <span style="font-size:1rem">FCFA</span></div>
  <div class="per" data-t="per">par nuit, petit-déjeuner inclus</div>

  <form id="bkf">
    <div class="two">
      <div class="pf"><label for="d1" data-t="in">Arrivée</label><input type="date" id="d1"></div>
      <div class="pf"><label for="d2" data-t="out">Départ</label><input type="date" id="d2"></div>
    </div>
    <div class="pf"><label for="pax" data-t="guests">Voyageurs</label>
      <select id="pax">
        <option value="2">2 personnes</option><option value="3">3 personnes</option>
        <option value="4" selected>4 personnes</option><option value="5">5 personnes</option>
        <option value="6">6 personnes</option>
      </select>
    </div>

    <div class="calc">
      <div class="row"><span id="l1">280 000 FCFA × 2 nuits</span><span id="v1">560 000</span></div>
      <div class="row"><span data-t="tax">Taxe de séjour</span><span id="v2">0</span></div>
      <div class="row"><span data-t="bkf2">Petit-déjeuner</span><span style="color:var(--palm)" data-t="incl">Inclus</span></div>
      <div class="total"><span data-t="tot">Total séjour</span><b id="tt">560 000</b></div>
    </div>

    <button type="submit" class="btn btn-solid" data-t="ctab">Réserver cette suite</button>
    <div class="avail"><i></i><span data-t="av">Disponible à ces dates</span></div>
    <p class="help" data-t="helpt">Une question&nbsp;? Écrivez-nous sur <a href="https://wa.me/2250546017377" target="_blank" rel="noopener">WhatsApp</a> ou appelez le +225 01 51 52 75 75.</p>
  </form>
 </aside>
</div>

<section class="more">
  <div class="wrap">
    <span class="eyebrow" data-t="e5">Autres catégories</span>
    <h2 data-t="h5">Si la Suite Arabe est prise</h2>
    <div class="more-grid">''')

for i, (img, t, key, d, price) in enumerate(MORE, 1):
    b.append('''      <article class="rcard reveal">
        <div class="ph"><picture><source srcset="img/opt/%s.webp" type="image/webp"><img loading="lazy" width="900" height="600" src="img/opt/%s.jpg" alt="%s"></picture></div>
        <div><h3>%s</h3><p style="font-size:14px" data-t="%s">%s</p>
        <div class="p"><b>%s</b><span data-t="pn2">FCFA / nuit</span></div></div>
      </article>''' % (img, img, t, t, key, d, price))

b.append('''    </div>
  </div>
</section>

''' + FOOTER + '''

<div class="mobar">
  <div><b id="mb">560 000</b><span data-t="mbl">FCFA · séjour total</span></div>
  <a href="#reserver" class="btn btn-solid" data-t="mcta">Réserver</a>
</div>

<div id="lb" role="dialog" aria-modal="true" aria-label="Galerie photo">
  <button class="lb-btn close" aria-label="Fermer">×</button>
  <button class="lb-btn prev" aria-label="Photo précédente">‹</button>
  <img id="lbi" alt="">
  <button class="lb-btn next" aria-label="Photo suivante">›</button>
  <div id="lbc"></div>
</div>''')

JS = NAV_JS + '''

var RATE=280000, TAX=1500; // taxe de séjour par personne et par nuit
var d1=document.getElementById('d1'),d2=document.getElementById('d2'),pax=document.getElementById('pax');
function iso(d){return new Date(d.getTime()-d.getTimezoneOffset()*6e4).toISOString().slice(0,10)}
d1.value=iso(new Date(Date.now()+864e5));d2.value=iso(new Date(Date.now()+864e5*3));
d1.min=iso(new Date());d2.min=iso(new Date());
function fmt(n){return n.toLocaleString('fr-FR').replace(/ | |,/g,' ')}
function calc(){
  var a=new Date(d1.value),b=new Date(d2.value);
  var n=Math.round((b-a)/864e5); if(!n||n<1){n=1;d2.value=iso(new Date(a.getTime()+864e5))}
  var p=+pax.value, sejour=RATE*n, taxe=TAX*p*n, total=sejour+taxe;
  document.getElementById('l1').textContent=fmt(RATE)+' FCFA × '+n+(n>1?' nuits':' nuit');
  document.getElementById('v1').textContent=fmt(sejour);
  document.getElementById('v2').textContent=fmt(taxe);
  document.getElementById('tt').textContent=fmt(total);
  document.getElementById('mb').textContent=fmt(total);
}
[d1,d2,pax].forEach(function(e){e.addEventListener('change',calc)});
document.getElementById('bkf').addEventListener('submit',function(e){e.preventDefault();calc();
  alert("Démonstration : cette étape mènerait au paiement de l'acompte (Wave, Orange Money, MTN ou carte).")});
calc();

var figs=[].slice.call(document.querySelectorAll('#gl img')),lb=document.getElementById('lb'),lbi=document.getElementById('lbi'),lbc=document.getElementById('lbc'),gi=0;
function show(i){gi=(i+figs.length)%figs.length;lbi.src=figs[gi].dataset.full||figs[gi].src;lbi.alt=figs[gi].alt;lbc.textContent=figs[gi].alt+'  ·  '+(gi+1)+' / '+figs.length;lb.classList.add('on');document.body.style.overflow='hidden'}
function hideLb(){lb.classList.remove('on');document.body.style.overflow=''}
figs.forEach(function(im,i){im.closest('figure').onclick=function(){show(i)}});
lb.querySelector('.next').onclick=function(e){e.stopPropagation();show(gi+1)};
lb.querySelector('.prev').onclick=function(e){e.stopPropagation();show(gi-1)};
lb.querySelector('.close').onclick=hideLb;
lb.onclick=function(e){if(e.target===lb)hideLb()};
addEventListener('keydown',function(e){if(!lb.classList.contains('on'))return;
 if(e.key==='Escape')hideLb();if(e.key==='ArrowRight')show(gi+1);if(e.key==='ArrowLeft')show(gi-1)});

var EN={''' + EN_NAV + '''cta:"Book",
c1:"Home",c2:"Rooms &amp; Suites",sig:"Signature category",pn:"FCFA / night",pn2:"FCFA / night",
f1:"<b>2</b> bedrooms",f2:"<b>6</b> guests",f3:"<b>Private</b> lounge",f4:"<b>Moorish</b> decor",
cap1:"The suite",cap2:"The second bedroom",cap3:"The bathroom",cap4:"The lounge",cap5:"The terrace",
e1:"The suite",h1x:"Two bedrooms,<br>a patio, a dedicated service",
p1:"It is the largest of our seven categories, and the only one with two separate bedrooms. The Moorish decor — carved wood, arches, embroidered textiles — was put together piece by piece with local craftspeople, in the spirit that guides the whole property.",
p2:"Two couples, a family with older children, or a group of friends: the suite takes six people without anyone getting in anyone's way. The private lounge is the shared living space, and each bedroom keeps its own bathroom.",
p3:"It is also our most requested category for honeymoons and birthdays. It goes fast in the dry season — from December to March, plan to book several weeks ahead.",
e2:"Amenities",h2:"In the suite",a1:"Air conditioning",a2:"Free wifi",a3:"Smart TV",a4:"Two king beds",a5:"Private lounge",
a6:"Two bathrooms",a7:"Hairdryer",a8:"Safe",a9:"Pool &amp; jacuzzi access",a10:"Shared terrace",
e3:"Included",h3:"Included in the rate",
i1:"Breakfast for every guest",i1p:"Served in the restaurant or on the terrace, fresh fruit and local produce.",
i2:"Free airport shuttle",i2p:"Pick-up and drop-off at Félix-Houphouët-Boigny airport, at no extra charge, on request.",
i3:"Pool, jacuzzi and gym",i3p:"Open from first light until late.",
i4:"Wifi and parking",i4p:"Free across the whole property.",
e4:"Conditions",h4:"Good to know",k1:"Check-in",k2:"Check-out",k3:"Cancellation",v3:"free up to 48 h before",
k4:"Deposit",v4:"30 % on booking",k5:"Pets",v5:"not allowed",k6:"Payment",
from:"From",per:"per night, breakfast included",in:"Check-in",out:"Check-out",guests:"Guests",
tax:"Tourist tax",bkf2:"Breakfast",incl:"Included",tot:"Stay total",ctab:"Book this suite",av:"Available on these dates",
helpt:"A question&nbsp;? Message us on <a href=\\"https://wa.me/2250546017377\\" target=\\"_blank\\" rel=\\"noopener\\">WhatsApp</a> or call +225 01 51 52 75 75.",
e5:"Other categories",h5:"If the Arabian Suite is taken",
m1:"Lounge area, upgraded amenities and a private terrace. Up to 4 guests.",
m2:"Direct view over the Aby lagoon and the pool. The best sunset on the estate.",
m3:"Wax textiles, four-poster beds and a private dining room. Up to 3 guests.",
mbl:"FCFA · stay total",mcta:"Book"};

''' + LANG_JS

io.open('suite-arabe.html','w',encoding='utf-8').write(page(
 "Suite Arabe — Hôtel Evannath, Assinie | 280 000 FCFA la nuit",
 "La Suite Arabe de l'Hôtel Evannath à Assinie : deux chambres, décor arabo-andalou, salon privatif. 280 000 FCFA la nuit, petit-déjeuner et navette aéroport inclus.",
 "sa-main", CSS, '\n'.join(b), JS, preload="sa-main"))
print('suite-arabe.html      ok')
