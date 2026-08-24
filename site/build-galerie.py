# -*- coding: utf-8 -*-
"""Optimise les 49 photos du domaine et genere galerie.html + 404.html."""
import io, os
from PIL import Image
import _schema
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV

# (fichier source, identifiant, categorie, legende)
PHOTOS = [
 # ── Le domaine ────────────────────────────────────────────────
 ('gallery/1.png',  'dom-facade',   'domaine', "Le corps principal et la piscine"),
 ('rest/2.png',     'dom-piscine',  'domaine', "La piscine et ses parasols"),
 ('gallery/13.png', 'dom-batiment', 'domaine', "La façade depuis la cour"),
 ('gallery/20.png', 'dom-aerien',   'domaine', "Le domaine vu du ciel"),
 ('rest/19.png',    'dom-mangrove', 'domaine', "La lagune et la mangrove, vue aérienne"),
 ('rest/18.png',    'dom-enseigne', 'domaine', "L'enseigne murale à l'entrée"),
 ('gallery/47.png', 'dom-jardin',   'domaine', "L'enseigne du jardin"),
 ('rest/46.png',    'dom-reve',     'domaine', "Le panneau peint « Rêve Africain »"),
 ('gallery/45.png', 'dom-fontaine', 'domaine', "La fontaine et l'éléphant de bois"),
 ('rest/31.png',    'dom-pirogue',  'domaine', "Pirogue décorative dans le jardin"),
 ('rest/44.png',    'dom-couchant', 'domaine', "Le couchant sur Assinie"),

 # ── Lagune & paillote ─────────────────────────────────────────
 ('gallery/8.png',  'lag-paillote', 'lagune',  "La paillote sur pilotis"),
 ('gallery/6.png',  'lag-ponton',   'lagune',  "Le ponton de bois au-dessus de l'eau"),
 ('gallery/21.png', 'lag-bateau',   'lagune',  "Le ponton et le bateau de balade"),
 ('rest/16.png',    'lag-nuit',     'lagune',  "La paillote à la tombée du jour"),
 ('gallery/4.png',  'lag-cocotiers','lagune',  "La lagune Aby et ses cocotiers"),
 ('gallery/5.png',  'lag-large',    'lagune',  "La lagune, vue large"),
 ('gallery/12.png', 'lag-rotin',    'lagune',  "Mobilier de rotin en terrasse"),
 ('gallery/24.png', 'lag-transat',  'lagune',  "Transat et parasol"),

 # ── Chambres & suites ─────────────────────────────────────────
 ('gallery/7.png',  'ch-wax',       'chambres',"Chambre aux textiles wax"),
 ('gallery/9.png',  'ch-salon',     'chambres',"Coin salon et plantes"),
 ('gallery/10.png', 'ch-bureau',    'chambres',"Coin bureau et miroir soleil"),
 ('gallery/11.png', 'ch-mezz',      'chambres',"L'escalier de la mezzanine"),
 ('gallery/23.png', 'ch-bain',      'chambres',"Salle de bain et baignoire"),

 # ── La table ──────────────────────────────────────────────────
 ('gallery/30.png', 'tab-salle',    'table',   "La salle du restaurant"),
 ('gallery/39.png', 'tab-rotin',    'table',   "Le bar et ses fauteuils de rotin"),
 ('rest/43.png',    'tab-dressee',  'table',   "Table dressée face au jardin"),
 ('rest/36.png',    'tab-comptoir', 'table',   "Le comptoir du bar"),
 ('rest/38.png',    'tab-vin',      'table',   "Une bouteille de la cave"),
 ('rest/37.png',    'tab-cave',     'table',   "Porte-bouteille de la cave"),
 ('rest/34.png',    'tab-cocktails','table',   "Cocktails en préparation"),
 ('rest/32.png',    'tab-cocktail', 'table',   "Cocktail au bord de la piscine"),
 ('rest/40.png',    'tab-dejeuner', 'table',   "Le petit-déjeuner, fruits et jus"),
 ('rest/41.png',    'tab-fruits',   'table',   "Ananas et jus pressés"),
 ('gallery/42.png', 'tab-corbeille','table',   "Corbeille de fruits frais"),
 ('gallery/33.png', 'tab-terrasse', 'table',   "Rafraîchissement en terrasse"),

 # ── Piscine & spa ─────────────────────────────────────────────
 ('rest/3.png',     'spa-bassin',   'bienetre',"Le grand bassin"),
 ('gallery/28.png', 'spa-couchant', 'bienetre',"La piscine en fin de journée"),
 ('rest/25.png',    'spa-case',     'bienetre',"La case ronde du spa"),
 ('rest/15.png',    'spa-huiles',   'bienetre',"Serviettes et huiles de soin"),

 # ── Art & détails ─────────────────────────────────────────────
 ('gallery/26.png', 'art-hall',     'art',     "Le hall et ses sculptures"),
 ('gallery/17.png', 'art-salon',    'art',     "Salon d'accueil et artisanat"),
 ('rest/49.png',    'art-masques',  'art',     "Masques et sculptures"),
 ('rest/48.png',    'art-statue',   'art',     "Statue et arbre en fleurs"),
 ('rest/29.png',    'art-lanterne', 'art',     "Lanterne de rotin allumée"),
 ('rest/27.png',    'art-lumineuse','art',     "L'enseigne lumineuse"),
 ('gallery/14.png', 'art-bois',     'art',     "Signalétique sculptée à la main"),
]

CATS = [('all','Tout voir'),('domaine','Le domaine'),('lagune','Lagune & paillote'),
        ('chambres','Chambres'),('table','La table'),('bienetre','Piscine & spa'),('art','Art & détails')]

# ── optimisation ──────────────────────────────────────────────
os.makedirs('img/opt', exist_ok=True)
made = []
for src, name, cat, cap in PHOTOS:
    full = 'img/opt/gal-%s.jpg' % name
    if not os.path.exists('img/' + src):
        print('  ABSENT :', src); continue
    if not os.path.exists(full):
        im = Image.open('img/' + src).convert('RGB')
        r = 1400 / im.width if im.width > 1400 else 1
        big = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
        big.save(full, 'JPEG', quality=78, optimize=True, progressive=True)
        big.save('img/opt/gal-%s.webp' % name, 'WEBP', quality=76, method=6)
        r2 = 620 / big.width
        th = big.resize((620, int(big.height * r2)), Image.LANCZOS)
        th.save('img/opt/gal-%s-t.jpg' % name, 'JPEG', quality=74, optimize=True)
        th.save('img/opt/gal-%s-t.webp' % name, 'WEBP', quality=72, method=6)
    made.append((name, cat, cap))
print('%d photos pretes pour la galerie' % len(made))

# ── galerie.html ──────────────────────────────────────────────
CSS_GAL = """
.head{padding:150px 0 34px}
.head h1{margin:10px 0 18px}
.head p{max-width:58ch;font-size:1.06rem}
.tools{position:sticky;top:74px;z-index:60;background:rgba(23,16,10,.97);backdrop-filter:blur(16px);
  border-block:1px solid var(--line);margin-bottom:44px}
.tools .in{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;padding:13px 0}
.filters{display:flex;gap:6px;flex-wrap:wrap}
.filters button{background:none;border:1px solid transparent;color:var(--muted);font:700 10.5px/1 var(--f-body);
  letter-spacing:.18em;text-transform:uppercase;padding:14px 18px;cursor:pointer;transition:.3s}
.filters button:hover{color:var(--bronze)}
.filters button.on{border-color:var(--bronze);color:var(--bronze)}
.count{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:700}
.grid{columns:4;column-gap:14px;padding-bottom:100px}
.grid figure{break-inside:avoid;margin:0 0 14px;position:relative;overflow:hidden;cursor:pointer;background:var(--bark-2)}
.grid figure.hide{display:none}
.grid img{width:100%;display:block;transition:1s cubic-bezier(.2,.8,.2,1)}
.grid figure:hover img{transform:scale(1.05)}
.grid figcaption{position:absolute;left:0;right:0;bottom:0;padding:30px 14px 12px;
  background:linear-gradient(transparent,rgba(16,11,6,.94));
  font-size:11px;letter-spacing:.06em;color:var(--cream);opacity:0;transition:.4s;
  text-shadow:0 2px 10px rgba(10,6,3,.9)}
.grid figure:hover figcaption{opacity:1}
.empty{display:none;padding:60px 0;text-align:center;color:var(--muted)}
.empty.on{display:block}
#lb{position:fixed;inset:0;background:rgba(10,6,3,.98);z-index:200;display:none;place-items:center;padding:40px}
#lb.on{display:grid}
#lb img{max-width:92vw;max-height:84vh;object-fit:contain}
#lbc{position:absolute;bottom:26px;left:0;right:0;text-align:center;font-size:12px;letter-spacing:.1em;color:var(--muted);padding:0 24px}
.lb-btn{position:absolute;background:rgba(16,11,6,.75);border:1px solid var(--line);color:var(--cream);
  width:48px;height:48px;cursor:pointer;font-size:20px;transition:.3s}
.lb-btn:hover{border-color:var(--bronze);color:var(--bronze)}
#lb .prev{left:26px;top:50%}#lb .next{right:26px;top:50%}#lb .close{top:26px;right:26px}
@media(max-width:1080px){.grid{columns:3}}
@media(max-width:720px){
  .head{padding:126px 0 26px}
  .grid{columns:2;column-gap:10px}
  .grid figure{margin-bottom:10px}
  .grid figcaption{opacity:1;font-size:10px;padding:24px 10px 8px}
  .tools{top:70px}
  .filters button{padding:13px 13px;font-size:10px;letter-spacing:.12em}
  #lb .prev{left:8px}#lb .next{right:8px}
}
@media(max-width:340px){.grid{columns:1}}
"""

b = [header('index.html#reserver', 'Réserver'), drawer('index.html#galerie'), '''
<div class="wrap head">
  <nav class="crumb" aria-label="Fil d'Ariane">
    <a href="index.html" data-t="c1">Accueil</a> &nbsp;·&nbsp; <span data-t="c2">Galerie</span>
  </nav>
  <span class="eyebrow" data-t="eb">%d photographies · aucune image de synthèse</span>
  <h1 data-t="h1">Le domaine, sans filtre</h1>
  <p data-t="lede">Tout ce que vous voyez ici a été photographié sur place. Pas de banque d'images, pas d'illustration générée — le lieu tel qu'il est.</p>
</div>

<div class="tools">
  <div class="wrap in">
    <div class="filters" role="group" aria-label="Filtrer les photos">''' % len(made)]

for i, (key, lab) in enumerate(CATS):
    on = ' class="on"' if key == 'all' else ''
    b.append('      <button%s data-f="%s" data-t="f%d">%s</button>' % (on, key, i, lab))

b.append('''    </div>
    <span class="count"><b id="n">%d</b> <span data-t="ph">photos</span></span>
  </div>
</div>

<div class="wrap">
  <div class="grid" id="gl">''' % len(made))

for name, cat, cap in made:
    b.append('''    <figure data-cat="%s"><picture><source srcset="img/opt/gal-%s-t.webp" type="image/webp">
      <img loading="lazy" src="img/opt/gal-%s-t.jpg" data-full="img/opt/gal-%s.jpg" alt="%s"></picture>
      <figcaption>%s</figcaption></figure>''' % (cat, name, name, name, cap, cap))

b.append('''  </div>
  <p class="empty" id="empty" data-t="emp">Aucune photo dans cette catégorie.</p>
</div>

''' + FOOTER + '''

<div id="lb" role="dialog" aria-modal="true" aria-label="Photo en grand">
  <button class="lb-btn close" aria-label="Fermer">×</button>
  <button class="lb-btn prev" aria-label="Photo précédente">‹</button>
  <img id="lbi" alt="">
  <button class="lb-btn next" aria-label="Photo suivante">›</button>
  <div id="lbc"></div>
</div>''')

JS_GAL = NAV_JS + '''

var figs=[].slice.call(document.querySelectorAll('#gl figure'));
var n=document.getElementById('n'),empty=document.getElementById('empty');

document.querySelectorAll('.filters button').forEach(function(b){b.onclick=function(){
  document.querySelectorAll('.filters button').forEach(function(x){x.classList.remove('on')});
  b.classList.add('on');
  var f=b.dataset.f,c=0;
  figs.forEach(function(fig){
    var ok=(f==='all'||fig.dataset.cat===f);
    fig.classList.toggle('hide',!ok);
    if(ok)c++;
  });
  n.textContent=c;
  empty.classList.toggle('on',c===0);
}});

// la visionneuse ne parcourt que les photos actuellement affichées
function visibles(){return figs.filter(function(f){return !f.classList.contains('hide')})}
var lb=document.getElementById('lb'),lbi=document.getElementById('lbi'),lbc=document.getElementById('lbc'),gi=0;
function show(i){
  var v=visibles(); if(!v.length)return;
  gi=(i+v.length)%v.length;
  var im=v[gi].querySelector('img');
  lbi.src=im.dataset.full||im.src; lbi.alt=im.alt;
  lbc.textContent=im.alt+'  ·  '+(gi+1)+' / '+v.length;
  lb.classList.add('on'); document.body.style.overflow='hidden';
}
function hideLb(){lb.classList.remove('on');document.body.style.overflow=''}
figs.forEach(function(f){f.onclick=function(){show(visibles().indexOf(f))}});
lb.querySelector('.next').onclick=function(e){e.stopPropagation();show(gi+1)};
lb.querySelector('.prev').onclick=function(e){e.stopPropagation();show(gi-1)};
lb.querySelector('.close').onclick=hideLb;
lb.onclick=function(e){if(e.target===lb)hideLb()};
addEventListener('keydown',function(e){
  if(!lb.classList.contains('on'))return;
  if(e.key==='Escape')hideLb();
  if(e.key==='ArrowRight')show(gi+1);
  if(e.key==='ArrowLeft')show(gi-1);
});

var EN={''' + EN_NAV + '''cta:"Book now",
c1:"Home",c2:"Gallery",eb:"%d photographs · no AI imagery",h1:"The estate, unfiltered",
lede:"Everything you see here was photographed on site. No stock library, no generated illustration — the place as it is.",
f0:"View all",f1:"The estate",f2:"Lagoon &amp; deck",f3:"Rooms",f4:"The table",f5:"Pool &amp; spa",f6:"Art &amp; details",
ph:"photos",emp:"No photo in this category."};

''' % len(made) + LANG_JS

LD = _schema.bloc(
    _schema.galerie(['gal-' + m[0] for m in made[:20]]),
    _schema.hotel(),
    _schema.fil([('Accueil','index'),('Galerie',None)]))

io.open('galerie.html', 'w', encoding='utf-8').write(page(
 "Galerie — Hôtel Evannath, Assinie",
 "%d photographies réelles de l'Hôtel Evannath à Assinie : le domaine, la paillote sur la lagune Aby, les chambres, le restaurant, la piscine et le spa." % len(made),
 "gal-lag-paillote", CSS_GAL, '\n'.join(b), JS_GAL, slug="galerie", jsonld=LD))
print('galerie.html          ok')
