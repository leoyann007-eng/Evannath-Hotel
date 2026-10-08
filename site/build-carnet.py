# -*- coding: utf-8 -*-
"""Genere le Carnet d'Assinie : carnet.html, carnet-article.html, api/_carnet_gabarit.js.

Les articles s'ecrivent dans l'administration (onglet Carnet) : rien ici ne
change quand l'hotel publie. Ce script ne fait que les deux cadres.

  carnet.html          la liste des recits, lue a l'ouverture (a=carnet).
  carnet-article.html  le cadre d'un article. Servi tel quel, il lit
                       l'article par son adresse (repli) ; mais en ligne,
                       /carnet-<adresse> passe par api/admin?a=page-article,
                       qui rend CE MEME cadre deja rempli (voir api/_carnet.js).
  api/_carnet_gabarit.js  la copie exacte de carnet-article.html, pour la
                       fonction serveur. Meme texte, donc memes scripts, donc
                       les empreintes CSP de vercel.json valent pour les deux.
"""
import io
import json
import _schema
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV

CSS = """
.head{padding-top:150px;padding-bottom:30px}
.head h1{margin:10px 0 16px;font-size:clamp(2.2rem,4.6vw,3.4rem)}
.head .lede{max-width:62ch;color:var(--muted)}
.liste{display:grid;grid-template-columns:repeat(3,1fr);gap:26px;padding-bottom:96px}
.carte{display:flex;flex-direction:column;background:var(--bark-2);border:1px solid var(--line);overflow:hidden;transition:.5s cubic-bezier(.2,.8,.2,1)}
.carte:hover{border-color:var(--bronze)}
.carte .ph{aspect-ratio:3/2;overflow:hidden}
.carte .ph img{width:100%;height:100%;object-fit:cover;transition:1s cubic-bezier(.2,.8,.2,1)}
.carte:hover .ph img{transform:scale(1.04)}
.carte .in{padding:24px;display:flex;flex-direction:column;flex:1}
.carte .date{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--bronze);font-weight:700}
.carte h2{font-size:1.4rem;margin:10px 0 10px;line-height:1.25}
.carte p{font-size:14.5px;color:var(--muted);flex:1;margin:0 0 18px}
.carte .lire{font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--bronze);font-weight:700}
.vide{border:1px solid var(--line);padding:46px 30px;text-align:center;margin-bottom:96px}
.vide p{color:var(--muted);margin:0 auto 20px;max-width:52ch}
/* L'article */
.art{max-width:74ch;margin:0 auto;padding:150px 0 40px}
.art-retour{font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--bronze);font-weight:700}
.art-date{font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--bronze);font-weight:700;margin:26px 0 0}
.art h1{font-size:clamp(2.1rem,4.4vw,3.2rem);margin:12px 0 18px;line-height:1.1}
.art-chapo{font-size:1.15rem;color:var(--prose);line-height:1.65;margin-bottom:30px}
.art-img{margin:0 0 36px}
.art-img img{width:100%;height:auto;display:block}
.art-texte h2{font-size:1.65rem;margin:40px 0 14px}
.art-texte h3{font-size:1.2rem;margin:30px 0 10px;color:var(--bronze-2)}
.art-texte p{font-size:16.5px;line-height:1.8;margin:0 0 18px}
.art-texte ul{margin:0 0 20px;padding:0}
.art-texte li{list-style:none;font-size:16px;line-height:1.7;padding:5px 0 5px 22px;position:relative}
.art-texte li::before{content:"";position:absolute;left:0;top:16px;width:6px;height:6px;background:var(--bronze);opacity:.7}
.art-texte a{color:var(--bronze);border-bottom:1px solid var(--line)}
.art-texte a:hover{border-color:var(--bronze)}
.art-fr{font-size:13.5px;color:var(--muted);font-style:italic;margin:-14px 0 26px}
.art-fin{max-width:74ch;margin:0 auto;padding:30px 0 96px;border-top:1px solid var(--line);display:flex;flex-wrap:wrap;gap:14px;justify-content:space-between;align-items:center}
.art-fin p{margin:0;color:var(--muted)}
@media(max-width:1080px){.liste{grid-template-columns:repeat(2,1fr)}}
@media(max-width:720px){.liste{grid-template-columns:1fr}.art{padding-top:120px}.head{padding-top:120px}}
"""

EN_COMMUN = (EN_NAV + 'cta:"Book",c1:"Home",c2:"The Assinie Journal",')

# ── La liste ────────────────────────────────────────────────────────────
LISTE = [header('index.html#reserver', 'Réserver'), drawer(''), '''
<div class="wrap head">
  <nav class="crumb" aria-label="Fil d'Ariane">
    <a href="index.html" data-t="c1">Accueil</a> &nbsp;·&nbsp; <span data-t="c2">Le Carnet d'Assinie</span>
  </nav>
  <span class="eyebrow" data-t="k0">Récits, adresses et saisons</span>
  <h1 data-t="k1">Le Carnet d'Assinie</h1>
  <p class="lede" data-t="k2">La lagune, les plages, les tables et les fêtes d'Assinie, racontées par ceux qui y vivent. Pour préparer un séjour, ou simplement pour y être un peu.</p>
</div>

<div class="wrap">
  <div class="liste" id="liste"></div>
  <div class="vide" id="vide" hidden>
    <p data-t="k3">Les premiers récits arrivent bientôt. En attendant, voici ce que l'on peut faire au domaine et autour d'Assinie.</p>
    <a class="btn" href="experiences.html" data-t="k4">Voir les expériences</a>
  </div>
</div>

''' + FOOTER]

JS_LISTE = NAV_JS + r'''
/* La liste du Carnet. Ecrite avec createElement et textContent : un titre
   saisi dans l'administration n'est jamais lu comme du HTML. */
(function(){
  var L=document.getElementById('liste'),V=document.getElementById('vide'),D=null;
  function en(){return document.documentElement.lang==='en'}
  function jour(iso){var j=new Date(iso+'T12:00:00Z');
    return isNaN(j)?iso:j.toLocaleDateString(en()?'en-GB':'fr-FR',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'})}
  function src(img){return /^https:/.test(img)?img:'img/opt/'+img+'.jpg'}
  function dessiner(){
    if(!D)return;
    L.textContent='';
    D.forEach(function(a){
      var E=en()&&a.titre_en;
      var c=document.createElement('a');c.className='carte';c.href='carnet-'+a.slug;
      if(a.image){var f=document.createElement('div');f.className='ph';
        var i=document.createElement('img');i.src=src(a.image);i.alt=a.alt||'';i.loading='lazy';i.width=1200;i.height=800;
        f.appendChild(i);c.appendChild(f)}
      var b=document.createElement('div');b.className='in';
      var d=document.createElement('span');d.className='date';d.textContent=jour(a.date);
      var h=document.createElement('h2');h.textContent=E?a.titre_en:a.titre;
      var p=document.createElement('p');p.textContent=E?(a.chapo_en||a.chapo):a.chapo;
      var m=document.createElement('span');m.className='lire';m.textContent=en()?'Read the story':'Lire le récit';
      b.appendChild(d);b.appendChild(h);b.appendChild(p);b.appendChild(m);c.appendChild(b);L.appendChild(c);
    });
    V.hidden=D.length>0;
  }
  fetch('/api/admin?a=carnet',{cache:'no-store'})
    .then(function(r){return r.ok?r.json():null})
    .then(function(j){D=(j&&j.articles)||[];dessiner()})
    .catch(function(){D=[];dessiner()});
  var avant=window.EVN_LANG;window.EVN_LANG=function(){if(avant)avant();dessiner()};
})();

var EN={''' + EN_COMMUN + '''k0:"Stories, places and seasons",k1:"The Assinie Journal",
k2:"The lagoon, the beaches, the tables and the celebrations of Assinie, told by those who live there. To plan a stay, or simply to be there for a while.",
k3:"The first stories are on their way. In the meantime, here is what you can do on the estate and around Assinie.",
k4:"See the experiences"};

''' + LANG_JS

LD_LISTE = _schema.bloc(_schema.fil([('Accueil', 'index'), ('Le Carnet d’Assinie', None)]))

io.open('carnet.html', 'w', encoding='utf-8').write(page(
    "Le Carnet d'Assinie — Hôtel Evannath",
    "Que faire à Assinie ? Plages, lagune Aby, tables, fêtes et idées de week-end : le carnet de l'Hôtel Evannath, Assinie PK 19.",
    "gal-lag-ponton", CSS, '\n'.join(LISTE), JS_LISTE, slug="carnet", jsonld=LD_LISTE))
print('carnet.html           ok')

# ── L'article ───────────────────────────────────────────────────────────
# <!--ART--> ... <!--/ART--> : la zone que la fonction serveur remplace.
# <!--ART-LD-->            : ou elle pose le JSON-LD et les donnees.
ARTICLE = [header('index.html#reserver', 'Réserver'), drawer(''), '''
<div class="wrap">
  <!--ART--><article class="art" id="art">
    <p class="art-date" id="art-date"></p>
    <h1 id="art-titre">Le Carnet d'Assinie</h1>
    <p class="art-chapo" id="art-chapo"></p>
    <div class="art-texte" id="art-texte"></div>
  </article><!--/ART-->
  <p class="art-fr" id="art-fr" hidden data-t="a3">Ce récit n'existe pour l'instant qu'en français.</p>
  <div class="art-fin">
    <a class="art-retour" href="carnet.html" data-t="a1">← Tous les récits du Carnet</a>
    <a class="btn btn-solid" href="reserver.html" data-t="a2">Réserver votre séjour</a>
  </div>
</div>

''' + FOOTER]

JS_ARTICLE = NAV_JS + r'''
/* L'article. En ligne, le serveur l'a deja ecrit dans la page, et pose ses
   deux langues dans #art-data : on ne fait que changer de langue. Servie
   telle quelle (en local, ou si la fonction se tait), la page le lit par
   son adresse. Le texte arrive deja mis en forme ET echappe par le serveur
   (api/_carnet.js, rendre) : c'est lui, et lui seul, qui fabrique ce HTML. */
(function(){
  function el(i){return document.getElementById(i)}
  function en(){return document.documentElement.lang==='en'}
  function jour(iso){var j=new Date(iso+'T12:00:00Z');
    return isNaN(j)?iso:j.toLocaleDateString(en()?'en-GB':'fr-FR',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'})}
  var D=null,s=el('art-data');
  if(s){try{D=JSON.parse(s.textContent)}catch(e){D=null}}
  function poser(){
    if(!D)return;
    var E=en()&&!!D.titre_en;
    el('art-titre').textContent=E?D.titre_en:D.titre;
    el('art-chapo').textContent=E?(D.chapo_en||D.chapo):D.chapo;
    el('art-texte').innerHTML=(E&&D.html_en)?D.html_en:D.html;
    el('art-date').textContent=jour(D.date);
    el('art-fr').hidden=!(en()&&!D.titre_en);
  }
  function image(){
    if(!D||!D.image||document.querySelector('.art-img'))return;
    var f=document.createElement('figure');f.className='art-img';
    var i=document.createElement('img');i.alt=D.alt||'';i.width=1200;i.height=800;
    i.src=/^https:/.test(D.image)?D.image:'img/opt/'+D.image+'.jpg';
    f.appendChild(i);el('art-chapo').insertAdjacentElement('afterend',f);
  }
  if(!s){
    var m=location.pathname.match(/carnet-([a-z0-9-]+?)(?:\.html)?$/);
    var slug=(m&&m[1]!=='article')?m[1]:new URLSearchParams(location.search).get('s');
    if(!slug){location.replace('carnet.html');return}
    fetch('/api/admin?a=article&s='+encodeURIComponent(slug),{cache:'no-store'})
      .then(function(r){return r.ok?r.json():null})
      .then(function(j){
        if(j&&j.article){D=j.article;document.title=D.titre+' — Le Carnet d’Assinie · Hôtel Evannath';image();poser()}
        else{el('art-titre').textContent=en()?'Story not found':'Article introuvable';
          el('art-chapo').textContent=en()?'This story does not exist, or is no longer online.':'Cet article n’existe pas, ou n’est plus en ligne.'}
      })
      .catch(function(){});
  }
  var avant=window.EVN_LANG;window.EVN_LANG=function(){if(avant)avant();poser()};
})();

var EN={''' + EN_COMMUN + '''a1:"&larr; All the stories in the Journal",a2:"Book your stay",
a3:"For now, this story is only available in French."};

''' + LANG_JS

LD_ARTICLE = _schema.bloc(_schema.fil([('Accueil', 'index'), ('Le Carnet d’Assinie', 'carnet'), ('Récit', None)])) + '\n<!--ART-LD-->'

GABARIT = page(
    "Le Carnet d'Assinie — Hôtel Evannath",
    "Un récit du Carnet d'Assinie, par l'Hôtel Evannath, Assinie PK 19.",
    "gal-lag-ponton", CSS, '\n'.join(ARTICLE), JS_ARTICLE, slug="carnet-article", jsonld=LD_ARTICLE)
assert GABARIT.count('<!--ART-->') == 1 and GABARIT.count('<!--/ART-->') == 1 and GABARIT.count('<!--ART-LD-->') == 1

io.open('carnet-article.html', 'w', encoding='utf-8').write(GABARIT)
io.open('api/_carnet_gabarit.js', 'w', encoding='utf-8').write(
    '// ECRIT PAR build-carnet.py — ne pas modifier a la main.\n'
    '// La copie exacte de carnet-article.html, pour la fonction serveur (api/_carnet.js).\n'
    'module.exports = ' + json.dumps(GABARIT, ensure_ascii=False) + ';\n')
print('carnet-article.html   ok')
