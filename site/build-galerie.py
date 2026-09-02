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
 # gallery/8.png etait etiquetee « La paillote sur pilotis » a l'import :
 # c'est une chambre. Verifie par signature — meme photo que hero-chambre-wax.
 ('gallery/8.png',  'ch-wax2',      'chambres',"Lit et jeté aux motifs wax"),
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
refaites = []
# Largeur de la version pleine. Les originaux de img/gallery/ font 1748 px :
# les plafonner plus bas revenait a jeter de la definition deja payee, visible
# des qu'une de ces photos sert de hero sur un ecran dense.
LARGEUR = 1748
# Deux tailles de vignette. La grille passe de 4 colonnes a 3 puis 2 : sur un
# telephone, une vignette ne fait que ~176 px de large, soit 352 px reels en
# densite 2. Servir du 620 revenait a envoyer trois fois les pixels utiles.
VIGNETTES = (360, 620)

for src, name, cat, cap in PHOTOS:
    full = 'img/opt/gal-%s.jpg' % name
    chemin = 'img/' + src
    if not os.path.exists(chemin):
        print('  ABSENT :', src); continue

    # On regenere si le fichier manque, mais aussi s'il n'est pas a la largeur
    # voulue : le script se remet ainsi de lui-meme a jour quand LARGEUR change,
    # sans qu'il faille supprimer quoi que ce soit a la main.
    vise = min(LARGEUR, Image.open(chemin).width)
    refaire = (not os.path.exists(full)
               or Image.open(full).width != vise
               or not os.path.exists('img/opt/gal-%s-t360.webp' % name))

    if refaire:
        im = Image.open(chemin).convert('RGB')
        r = LARGEUR / im.width if im.width > LARGEUR else 1
        big = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        big.save(full, 'JPEG', quality=78, optimize=True, progressive=True)
        big.save('img/opt/gal-%s.webp' % name, 'WEBP', quality=76, method=6)
        for v in VIGNETTES:
            th = big.resize((v, round(big.height * v / big.width)), Image.LANCZOS)
            suf = '-t' if v == 620 else '-t%d' % v
            th.save('img/opt/gal-%s%s.jpg' % (name, suf), 'JPEG', quality=74, optimize=True)
            th.save('img/opt/gal-%s%s.webp' % (name, suf), 'WEBP', quality=72, method=6)
        refaites.append(name)
    made.append((name, cat, cap))
if refaites:
    print('  %d photos regenerees en %d px' % (len(refaites), LARGEUR))
print('%d photos pretes pour la galerie' % len(made))

# ── galerie.html ──────────────────────────────────────────────
CSS_GAL = """
.head{padding:150px 0 34px}
.head h1{margin:10px 0 18px}
.head p{max-width:58ch;font-size:1.06rem}
.tools{background:var(--bark);
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
/* Les deux paliers de vignette n'ont pas exactement le meme rapport une
   fois arrondis (620x440 contre 360x255). Sans cette regle, la hauteur
   rendue change selon le palier charge et la grille bouge de quelques
   pixels. On fige le rapport : la place reservee est alors exacte quel
   que soit le fichier retenu. */
.grid img{width:100%;display:block;aspect-ratio:620/440;transition:1s cubic-bezier(.2,.8,.2,1)}
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

# Largeur reellement occupee par une vignette, seuil par seuil :
#   <=720 px  2 colonnes, gouttiere 10  -> (100vw-58)/2  ~ 47vw
#   <=1080    3 colonnes, gouttiere 14  -> (100vw-76)/3  ~ 31vw
#   <=1240    4 colonnes                -> (100vw-90)/4  ~ 23vw
#   au-dela   la colonne est figee a 1192 px            -> 288 px
SIZES = '(max-width:720px) 47vw, (max-width:1080px) 31vw, (max-width:1240px) 23vw, 288px'

FIGURE = """    <figure data-cat="%(cat)s"><picture>
      <source srcset="img/opt/gal-%(n)s-t360.webp 360w, img/opt/gal-%(n)s-t.webp 620w"
        sizes="%(sizes)s" type="image/webp">
      <img loading="lazy" src="img/opt/gal-%(n)s-t.jpg"
        srcset="img/opt/gal-%(n)s-t360.jpg 360w, img/opt/gal-%(n)s-t.jpg 620w"
        sizes="%(sizes)s" data-full="img/opt/gal-%(n)s.jpg" alt="%(cap)s"></picture>
      <figcaption>%(cap)s</figcaption></figure>"""

for name, cat, cap in made:
    b.append(FIGURE % dict(cat=cat, n=name, sizes=SIZES, cap=cap))

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
  lbi.src=plein(im); lbi.alt=im.alt;
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
 "gal-lag-ponton", CSS_GAL, '\n'.join(b), JS_GAL, slug="galerie", jsonld=LD))
print('galerie.html          ok')
