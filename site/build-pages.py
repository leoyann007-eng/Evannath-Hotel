# -*- coding: utf-8 -*-
"""Genere les pages secondaires du site : a-propos, contact, informations-utiles,
mentions-legales. Chaque page est ecrite en entier a partir des briques de _chrome.py.
"""
import io
import _schema
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV

# ═══════════════════════════════ À PROPOS ═══════════════════════════════
CSS_ABOUT = """
/* L'en-tete est fixe : le hero doit lui reserver sa hauteur, comme le font
   les pages sans hero avec leur padding de 150px. Sans cela, sur un ecran
   court, le contenu aligne en bas remonte et passe sous l'en-tete. */
.hero{position:relative;min-height:82vh;display:flex;align-items:flex-end;overflow:hidden;padding-top:150px}
.hero>picture img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.hero::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(23,16,10,.8),rgba(23,16,10,.4) 45%,rgba(23,16,10,.97))}
.hero .in{position:relative;z-index:3;width:100%;padding-bottom:60px}
.hero h1{margin:12px 0 6px;font-size:clamp(2.6rem,6vw,4.4rem)}
.hero h1 em{display:block;font-style:italic;font-size:.44em;color:var(--bronze-2);margin-top:14px}
.hero p{max-width:56ch;font-size:1.1rem;margin-top:20px}
section{padding:100px 0}
.lead{display:grid;grid-template-columns:1fr 1fr;gap:64px;align-items:start}
.lead .big{font-family:var(--f-display);font-size:clamp(1.35rem,2.3vw,1.85rem);line-height:1.45;color:var(--cream)}
.lead p+p{margin-top:16px}
.pos{border-left:2px solid var(--bronze);padding:4px 0 4px 22px;margin-top:28px;font-size:14.5px;color:var(--muted)}
.pos b{color:var(--bronze-2);font-weight:600}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line)}
.stat{background:var(--bark);padding:34px 22px;text-align:center}
.stat b{display:block;font-family:var(--f-display);font-size:2.8rem;color:var(--bronze);line-height:1;font-variant-numeric:tabular-nums}
.stat span{font-size:9.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted);margin-top:11px;display:block;font-weight:600}
.why-sec{background:var(--bark-2)}
.why{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin-top:44px}
.why div{background:var(--bark-2);padding:34px 28px;transition:.4s}
.why div:hover{background:var(--bark-3)}
.why svg{width:24px;height:24px;stroke:var(--bronze);fill:none;stroke-width:1.3;margin-bottom:18px}
.why h3{margin-bottom:9px;font-size:1.12rem}
.why p{font-size:13.5px;color:var(--muted)}
.space{display:grid;grid-template-columns:1fr 1fr;align-items:center;border:1px solid var(--line);margin-bottom:24px;background:var(--bark-2)}
.space:nth-child(even) .ph{order:2}
.space .ph{overflow:hidden;min-height:340px}
.space .ph img{width:100%;height:100%;object-fit:cover;transition:1.1s cubic-bezier(.2,.8,.2,1)}
.space:hover .ph img{transform:scale(1.05)}
.space .tx{padding:48px}
.space .tx h3{font-size:1.6rem;margin:12px 0 14px}
/* 24 · Le numero de section tourne — maquette « Motion design II ».
   Chaque colonne roule d'un cran (translateY -50 %) derriere une fenetre
   d'une ligne ; 1,3 s --ease-inout, delai .3 s, le libelle .15 s apres.
   La fenetre est aussi large que le plus long des deux libelles : le
   surtitre est seul sur sa ligne, cet espace ne pousse rien. */
.sec-no .rl{display:inline-block;height:1.3em;overflow:hidden;vertical-align:top}
.sec-no .col{display:flex;flex-direction:column;transition:transform 1.3s var(--ease-inout) .3s}
.sec-no .col-l{transition-delay:.45s}
.sec-no .col>span{display:block;height:1.3em;line-height:1.3em}
/* .pas : seules les colonnes a DEUX lignes roulent. La premiere
   section n'en a qu'une ; la decaler de moitie la couperait en deux. */
.space.vu .sec-no .pas{transform:translateY(-50%)}
.space .tx p{font-size:14.5px}
.space .tx a{display:inline-block;margin-top:16px;font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--bronze);border:1px solid var(--bronze);padding:14px 20px;font-weight:700;transition:.3s}
.space .tx a:hover{background:var(--bronze);color:var(--bark)}
/* Video de presentation ---------------------------------------------------
   preload="none" : rien ne part tant que le visiteur n'a pas clique. Le
   fichier est en fast-start (index en tete), donc la lecture demarre sans
   attendre les 28 Mo. L'affiche est une photo du domaine : sans ffmpeg on
   ne peut pas extraire une image du film lui-meme. */
.film-sec{background:var(--bark);border-block:1px solid var(--line);padding:88px 0}
.film{position:relative;margin-top:34px;border:1px solid var(--line);background:#000;
  aspect-ratio:16/9;overflow:hidden}
.film video{width:100%;height:100%;object-fit:cover;display:block;background:#000}
.film-note{display:flex;gap:22px;flex-wrap:wrap;margin-top:16px;font-size:12.5px;color:var(--muted)}
.film-note span{display:inline-flex;align-items:center;gap:7px}
.film-note svg{width:14px;height:14px;stroke:var(--bronze);fill:none;stroke-width:1.5}

.eq-sec{background:var(--bark-2)}
.eq{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin-top:40px}
.eq div{background:var(--bark-2);padding:22px 20px;display:flex;align-items:center;gap:13px;font-size:14px;color:var(--prose)}
.eq svg{width:18px;height:18px;stroke:var(--bronze);fill:none;stroke-width:1.4;flex:0 0 auto}
.cta{border:1px solid var(--bronze);padding:56px;text-align:center;margin:0 0 100px}
.cta h2{margin-bottom:14px}
.cta p{max-width:52ch;margin:0 auto 28px}
.cta .g{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
@media(max-width:1080px){
  .lead{grid-template-columns:1fr;gap:34px}
  .why,.eq{grid-template-columns:repeat(2,1fr)}
  .space{grid-template-columns:1fr}
  .space:nth-child(even) .ph{order:0}
  .space .ph{min-height:250px}
}
@media(max-width:720px){
  section{padding:70px 0}
  .why,.eq,.stats{grid-template-columns:1fr}
  .space .tx,.cta{padding:30px}
}
"""

def icon(d):
    return '<svg viewBox="0 0 24 24" aria-hidden="true">%s</svg>' % d

WHY = [
 ('w1','Aménagements locaux','Des équipements précieux, choisis chez des marques et des artisans de Côte d\'Ivoire.',
  '<path d="M12 21s-7-4.5-7-10a7 7 0 0114 0c0 5.5-7 10-7 10z"/><circle cx="12" cy="11" r="2.4"/>'),
 ('w2','Paiements variés','Wave, Orange Money, MTN, carte bancaire ou espèces. Nous nous adaptons.',
  '<rect x="2" y="6" width="20" height="13"/><path d="M2 10h20M6 15h4"/>'),
 ('w3','Navette aéroport gratuite','Prise en charge et dépose à l\'aéroport Félix-Houphouët-Boigny, sans frais, chaque fois que vous en avez besoin.',
  '<path d="M2 16l20-7-8 12-2-5-5-2z"/><path d="M4 20h7"/>'),
 ('w4','Le meilleur emplacement','Au PK 19, entre l\'océan Atlantique et la lagune Aby. Accessible, et sans tracas à l\'arrivée.',
  '<path d="M3 18c2 1 4-1 6 0s4 1 6 0 4-1 6 0M4 13l8-9 8 9"/>'),
 ('w5','Offres spéciales','Packs Vacances, circuits, coffrets anniversaire : des formules conçues pour profiter d\'Assinie autrement.',
  '<path d="M12 3l2.4 5.6L20 9.7l-4 4 1 6-5-2.9L7 19.7l1-6-4-4 5.6-1.1z"/>'),
 ('w6','Un personnel qui répond','Serviable, présent, et heureux de répondre à toutes vos questions. C\'est ce que nos clients citent en premier.',
  '<circle cx="9" cy="8" r="3.4"/><path d="M2 20a7 7 0 0114 0M17 11a3 3 0 100-6M18 20a6 6 0 00-2-4.5"/>'),
]

SPACES = [
 ('01 · Hébergement','Chambres &amp; Suites','r-anglaise','Suite de l\'Hôtel Evannath',
  'Des matériaux nobles, des couleurs harmonieuses et une décoration soignée créent un espace où détente et bien-être sont les maîtres mots. Sept catégories, de la chambre standard à la Suite Arabe deux chambres.',
  'index.html#chambres','Voir les catégories'),
 ('02 · Table','Restaurant','g-resto','La salle du restaurant',
  'Les saveurs authentiques de la Côte d\'Ivoire, dans un cadre chaleureux et lumineux ouvert sur la piscine. Kedjenou, thiéboudiène, capitaine en papillote — et une carte de cocktails maison.',
  'carte.html','Consulter la carte'),
 ('03 · Professionnels','Rencontres &amp; Événements','g-seminaire','Salle de conférence équipée',
  'Un espace baigné de lumière naturelle, au design contemporain, qui se prête à tout : séminaires, cocktails, dîners de gala, lancements de produits. Sonorisation et technicien disponibles.',
  'contact.html','Demander un devis'),
 ('04 · Bien-être','Spa &amp; Sauna','gal-spa-case','La case ronde qui abrite le spa',
  'Massages aux pierres chauffantes, rituel de l\'Orient à l\'argan, gommage au savon noir africain, soins du visage aux cinq fleurs d\'Assinie. Et un sauna pour finir la journée.',
  'spa.html','Voir les soins'),
 ('05 · Loisirs','Piscine &amp; Jacuzzi','c-piscine','La piscine de l\'hôtel en fin de journée',
  'Un grand bassin avec jacuzzi intégré, des transats et des parasols, ouverts du lever du jour à la nuit tombée. Aire de jeux pour les enfants et salle de sport à deux pas.',
  'circuits.html','Découvrir les offres'),
]

EQ = [
 ('q1','Air conditionné','<path d="M3 12h18M6 8h12M6 16h12"/>'),
 ('q2','Wifi gratuit','<path d="M5 13a10 10 0 0114 0M8.5 16.5a5 5 0 017 0"/><circle cx="12" cy="20" r="1"/>'),
 ('q3','Piscine &amp; jacuzzi','<path d="M3 17c2 1 4-1 6 0s4 1 6 0 4-1 6 0M3 12c2 1 4-1 6 0s4 1 6 0 4-1 6 0"/>'),
 ('q4','Spa &amp; sauna','<path d="M4 20c2-6 6-9 8-9s6 3 8 9M12 11V4"/>'),
 ('q5','Salle de sport','<path d="M4 9v6M20 9v6M7 7v10M17 7v10M7 12h10"/>'),
 ('q6','Télévision smart','<rect x="3" y="5" width="18" height="12"/><path d="M9 21h6"/>'),
 ('q7','Aire de jeux','<path d="M12 3v6M8 21h8M6 12h12l-2 9H8z"/>'),
 ('q8','Ascenseurs','<rect x="4" y="3" width="16" height="18"/><path d="M9 3v18M4 9h5M4 15h5"/>'),
 ('q9','Navettes','<path d="M2 16l20-7-8 12-2-5-5-2z"/>'),
 ('q10','Parking gratuit','<rect x="3" y="3" width="18" height="18"/><path d="M9 17V7h3.5a3 3 0 010 6H9"/>'),
 ('q11','Boutique souvenir','<path d="M6 3h12l2 6H4zM5 9v12h14V9M9 13h6"/>'),
 ('q12','Pressing','<path d="M5 8h14l-1 12H6zM9 8V5a3 3 0 016 0v3"/>'),
 ('q13','Sèche-cheveux','<path d="M8 3v6a4 4 0 008 0V3M12 13v8M9 21h6"/>'),
]

body = ['''%s

%s

<section class="hero">
  <picture><source srcset="img/opt/g-entree.webp" type="image/webp">
  <img src="img/opt/g-entree.jpg" width="1200" height="800" alt="L'entrée et l'enseigne de l'Hôtel Evannath à Assinie"></picture>
  <div class="in wrap">
    <nav class="crumb" aria-label="Fil d'Ariane">
      <a href="index.html" data-t="c1">Accueil</a> &nbsp;·&nbsp; <span data-t="c2">À propos</span>
    </nav>
    <span class="eyebrow" data-t="eb">Assinie · PK 19 · Depuis toujours</span>
    <h1>Akwaba<em data-t="sub">Bienvenue dans le rêve africain</em></h1>
    <p data-t="lede">Akwaba, c'est « bienvenue » en akan. C'est le premier mot que vous entendez en passant le portail, et le seul qui résume vraiment ce que nous faisons ici.</p>
  </div>
</section>

<section class="wrap">
  <div class="lead reveal">
    <div>
      <span class="eyebrow" data-t="e1">Notre maison</span>
      <p class="big" style="margin-top:18px" data-t="big">Un havre de paix qui allie l'excellence et le confort, pensé pour devenir une référence de l'hospitalité ivoirienne.</p>
    </div>
    <div>
      <p data-t="p1">L'Evannath Hôtel est né d'une idée simple : offrir à Assinie un lieu où le luxe ne serait pas importé, mais africain. Les équipements viennent de marques et d'artisans locaux. Les sculptures du hall ont été choisies une par une. La cuisine célèbre les produits du pays.</p>
      <p data-t="p2">Chaque détail est élaboré pour le bien-être de nos visiteurs — de la navette qui vous attend à l'aéroport jusqu'au dernier cocktail sur le ponton. Notre gamme de services évolue avec les besoins de nos clients, et notre réception ne ferme jamais.</p>
      <div class="pos"><b data-t="pos1">Luxe africain.</b><span data-t="pos2"> Hébergement, salles de conférence, restauration raffinée avec vue sur piscine, bien-être et loisirs.</span></div>
    </div>
  </div>
</section>

<section class="wrap" style="padding-top:0">
  <div class="stats reveal">
    <div class="stat"><b class="cnt" data-to="46">0</b><span data-t="s1">Chambres</span></div>
    <div class="stat"><b class="cnt" data-to="7">0</b><span data-t="s2">Catégories</span></div>
    <div class="stat"><b class="cnt" data-to="13">0</b><span data-t="s3">Équipements</span></div>
    <div class="stat"><b class="cnt" data-to="24" data-suffix="h">0</b><span data-t="s4">Réception</span></div>
  </div>
</section>

<section class="why-sec">
 <div class="wrap">
  <span class="eyebrow" data-t="e2">Pourquoi nous choisir</span>
  <h2 data-t="h2">Six raisons, et une navette<br>qui vous attend à l'aéroport</h2>
  <div class="why reveal">''' % (header('index.html#reserver','Réserver'), drawer('a-propos.html'))]

for key, t, p, d in WHY:
    body.append('    <div>%s<h3 data-t="%s">%s</h3><p data-t="%sp">%s</p></div>' % (icon(d), key, t, key, p))

body.append('''  </div>
 </div>
</section>

<section class="wrap">
  <span class="eyebrow" data-t="e3">Nos espaces</span>
  <h2 style="margin-bottom:44px" data-t="h3">Cinq lieux, un même soin</h2>''')

def _numero(i):
    """24 · Le surtitre « 02 · Table » roule depuis celui de la section
    precedente, « 01 · Hebergement ». Deux colonnes : le numero, puis le
    libelle, qui part .15 s plus tard.

    La ligne precedente est aria-hidden : un lecteur d'ecran lirait sinon
    « 01 02 · Hebergement Table ». Et elle porte la MEME cle de traduction
    que la section d'avant — le meme texte, la meme cle, donc la meme
    traduction, sans rien ecrire deux fois. La premiere section n'a rien
    avant elle : elle ne roule pas."""
    no, lab = SPACES[i - 1][0].split(' · ')
    if i == 1:
        return ('<span class="eyebrow sec-no"><span class="rl"><span class="col">'
                '<span>%s</span></span></span> · <span class="rl"><span class="col">'
                '<span data-t="es1">%s</span></span></span></span>' % (no, lab))
    pno, plab = SPACES[i - 2][0].split(' · ')
    return ('<span class="eyebrow sec-no"><span class="rl"><span class="col pas">'
            '<span aria-hidden="true">%s</span><span>%s</span></span></span> · '
            '<span class="rl"><span class="col col-l pas">'
            '<span aria-hidden="true" data-t="es%d">%s</span><span data-t="es%d">%s</span>'
            '</span></span></span>' % (pno, no, i - 1, plab, i, lab))


for i, (nm, t, img, alt, d, href, cta) in enumerate(SPACES, 1):
    body.append('''  <article class="space reveal">
    <div class="ph"><picture><source srcset="img/opt/%s.webp" type="image/webp"><img loading="lazy" src="img/opt/%s.jpg" width="1200" height="800" alt="%s"></picture></div>
    <div class="tx">%s<h3 data-t="t%d">%s</h3>
      <p data-t="ed%d">%s</p>
      <a href="%s" data-t="a%d">%s</a></div>
  </article>''' % (img, img, alt, _numero(i), i, t, i, d, href, i, cta))

body.append('''</section>

<section class="film-sec">
  <div class="wrap">
    <span class="eyebrow" data-t="ef">En trois minutes</span>
    <h2 style="margin-top:14px" data-t="hf">Le film de la maison</h2>
    <p style="max-width:56ch;margin-top:16px;color:var(--muted)" data-t="pf">Le domaine, la lagune, les chambres et la table, filmés sur place. La lecture ne démarre qu'à votre demande.</p>
    <div class="film">
      <video controls preload="none" playsinline
             poster="img/opt/gal-dom-aerien-1024.jpg"
             width="1280" height="720">
        <source src="video/presentation-hotel.mp4" type="video/mp4">
        <p data-t="vf">Votre navigateur ne peut pas lire cette vidéo.
          <a href="video/presentation-hotel.mp4">La télécharger</a> (28 Mo).</p>
      </video>
    </div>
    <div class="film-note">
      <span><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg><span data-t="d1">3 minutes</span></span>
      <span><svg viewBox="0 0 24 24"><path d="M12 3a3 3 0 013 3v6a3 3 0 01-6 0V6a3 3 0 013-3z"/><path d="M5 11a7 7 0 0014 0M12 18v3"/></svg><span data-t="d2">Avec son</span></span>
      <span><svg viewBox="0 0 24 24"><path d="M3 17c2 1 4-1 6 0s4 1 6 0 4-1 6 0M5 13l7-8 7 8"/></svg><span data-t="d3">28 Mo, lecture progressive</span></span>
    </div>
  </div>
</section>

<section class="eq-sec">
 <div class="wrap">
  <span class="eyebrow" data-t="e4">Sur le domaine</span>
  <h2 data-t="h4">Treize équipements,<br>tous compris</h2>
  <div class="eq reveal">''')

for key, t, d in EQ:
    body.append('    <div>%s<span data-t="%s">%s</span></div>' % (icon(d), key, t))

body.append('''  </div>
 </div>
</section>

<div class="wrap">
  <div class="cta reveal">
    <span class="eyebrow" data-t="e5">Akwaba</span>
    <h2 data-t="h5">Venez voir par vous-même</h2>
    <p data-t="p5">Réservez en direct — c'est ici que le tarif est le meilleur, et la navette vous attend à l'aéroport.</p>
    <div class="g">
      <a href="index.html#reserver" class="btn btn-solid" data-t="b1">Réserver une chambre</a>
      <a href="contact.html" class="btn" data-t="b2">Nous écrire</a>
    </div>
  </div>
</div>

''' + FOOTER)

JS_ABOUT = NAV_JS + '''
/* 24 · chaque surtitre roule quand sa section arrive, une fois. */
EVN_AU_SCROLL('.space','vu');


if(!('IntersectionObserver' in window)||reduce){
  document.querySelectorAll('.cnt').forEach(function(e){e.textContent=e.dataset.to+(e.dataset.suffix||'')});
}else{
  var co=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;
    var el=e.target,to=+el.dataset.to,sfx=el.dataset.suffix||'',n=0;
    var t=setInterval(function(){n+=Math.ceil(to/34);if(n>=to){n=to;clearInterval(t)}el.textContent=n+sfx},34);
    co.unobserve(el)})},{threshold:.5});
  document.querySelectorAll('.cnt').forEach(function(el){co.observe(el)});
}

var EN={''' + EN_NAV + '''cta:"Book now",
c1:"Home",c2:"About",eb:"Assinie · PK 19 · Always",sub:"Welcome to the African dream",
lede:"Akwaba means “welcome” in Akan. It is the first word you hear as you come through the gate, and the only one that really sums up what we do here.",
ef:"Three minutes",hf:"The film of the house",pf:"The grounds, the lagoon, the rooms and the table, filmed on site. Playback starts only when you ask for it.",vf:"Your browser cannot play this video.",d1:"3 minutes",d2:"With sound",d3:"28 MB, progressive playback",e1:"Our house",big:"A haven of peace combining excellence and comfort, built to become a benchmark for Ivorian hospitality.",
p1:"The Evannath Hôtel grew from a simple idea: to give Assinie a place where luxury would not be imported, but African. The fittings come from local brands and craftspeople. The sculptures in the hall were chosen one by one. The kitchen celebrates the country's produce.",
p2:"Every detail is worked out for our visitors' wellbeing — from the shuttle waiting at the airport to the last cocktail on the pontoon. Our range of services grows with what our guests need, and our front desk never closes.",
pos1:"African luxury.",pos2:" Accommodation, conference rooms, refined dining overlooking the pool, wellbeing and leisure.",
s1:"Rooms",s2:"Categories",s3:"Amenities",s4:"Front desk",
e2:"Why choose us",h2:"Six reasons — and a shuttle<br>waiting at the airport",
w1:"Local fittings",w1p:"Fine equipment, sourced from Ivorian brands and craftspeople.",
w2:"Flexible payment",w2p:"Wave, Orange Money, MTN, card or cash. We adapt.",
w3:"Free airport shuttle",w3p:"Pick-up and drop-off at Félix-Houphouët-Boigny airport, free of charge, whenever you need it.",
w4:"The best location",w4p:"At PK 19, between the Atlantic Ocean and the Aby lagoon. Easy to reach, no fuss on arrival.",
w5:"Special offers",w5p:"Holiday Packs, tours, birthday boxes: packages built to enjoy Assinie differently.",
w6:"Staff who answer",w6p:"Helpful, present, and glad to answer every question. It is the first thing our guests mention.",
e3:"Our spaces",h3:"Five places, one same care",
es1:"Accommodation",t1:"Rooms &amp; Suites",
ed1:"Fine materials, harmonious colours and careful decoration create a space where relaxation and wellbeing come first. Seven categories, from the standard room to the two-bedroom Arabian Suite.",a1:"See the categories",
es2:"Table",t2:"Restaurant",
ed2:"The authentic flavours of Côte d'Ivoire, in a warm, bright room opening onto the pool. Kedjenou, thiéboudiène, capitaine en papillote — and a list of house cocktails.",a2:"See the menu",
es3:"Business",t3:"Meetings &amp; Events",
ed3:"A space bathed in natural light, contemporary in design, that suits anything: seminars, cocktails, gala dinners, product launches. PA system and sound engineer available.",a3:"Request a quote",
es4:"Wellbeing",t4:"Spa &amp; Sauna",
ed4:"Hot stone massages, an Oriental argan ritual, African black soap scrub, facials with the five flowers of Assinie. And a sauna to close the day.",a4:"See the treatments",
es5:"Leisure",t5:"Pool &amp; Jacuzzi",
ed5:"A large pool with built-in jacuzzi, sun loungers and parasols, open from first light until dark. Children's play area and gym a few steps away.",a5:"See the offers",
e4:"On the estate",h4:"Thirteen amenities,<br>all included",
q1:"Air conditioning",q2:"Free wifi",q3:"Pool &amp; jacuzzi",q4:"Spa &amp; sauna",q5:"Gym",q6:"Smart TV",q7:"Play area",
q8:"Lifts",q9:"Shuttles",q10:"Free parking",q11:"Gift shop",q12:"Laundry",q13:"Hairdryer",
e5:"Akwaba",h5:"Come and see for yourself",
p5:"Book direct — the rate is always best here, and the shuttle is waiting at the airport.",
b1:"Book a room",b2:"Write to us"};

''' + LANG_JS

LD = _schema.bloc(
    _schema.hotel(complet=True),
    _schema.site_web(),
    _schema.fil([('Accueil','index'),('À propos',None)]))

io.open('a-propos.html','w',encoding='utf-8').write(page(
 "À propos — Hôtel Evannath, le rêve africain à Assinie",
 "Akwaba. L'Hôtel Evannath à Assinie PK 19 : 46 chambres, luxe africain, salles de conférence, restauration avec vue sur piscine, spa et loisirs. Navette aéroport gratuite.",
 "g-entree", CSS_ABOUT, '\n'.join(body), JS_ABOUT, preload="g-entree", slug="a-propos", jsonld=LD))
print('a-propos.html         ok')
