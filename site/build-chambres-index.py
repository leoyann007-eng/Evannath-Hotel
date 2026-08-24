# -*- coding: utf-8 -*-
"""Genere chambres.html : la page mere des sept categories.

Elle manquait. « Chambres & Suites » pointait vers une ancre de l'accueil, donc
rien ne pouvait se positionner sur « hotel Assinie chambres » — la requete la
plus evidente du metier. Les sept fiches existaient sans page parente.

Contient un comparateur : filtres par famille, tri par tarif ou par capacite,
et un tableau recapitulatif des sept categories cote a cote.
"""
import io
import _schema
from _chambres import CHAMBRES, FAMILLE
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV, SITE


def fmt(n):
    return '{:,}'.format(n).replace(',', ' ')


FAM_NOM = {'chambre': 'Chambre', 'suite': 'Suite', 'famille': 'Famille'}

CSS = """
/* L'en-tete est fixe : le hero doit lui reserver sa hauteur, comme le font
   les pages sans hero avec leur padding de 150px. Sans cela, sur un ecran
   court, le contenu aligne en bas remonte et passe sous l'en-tete. */
.hero{position:relative;min-height:56vh;display:flex;align-items:flex-end;overflow:hidden;padding-top:150px}
.hero>picture img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.hero::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(23,16,10,.78),rgba(23,16,10,.42) 46%,rgba(23,16,10,.97))}
.hero .in{position:relative;z-index:3;width:100%;padding-bottom:48px}
.hero h1{margin:12px 0 16px}
.hero p{max-width:56ch}

section{padding:88px 0}

/* barre de tri */
.bar{display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap;
  padding:20px 0;border-block:1px solid var(--line);position:sticky;top:110px;z-index:20;
  background:rgba(23,16,10,.96);backdrop-filter:blur(12px)}
.grp{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.grp b{font-size:9.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted);font-weight:700;margin-right:6px}
.chip{background:none;border:1px solid var(--line);color:#B4A794;font:600 11px/1 var(--f-body);
  letter-spacing:.14em;text-transform:uppercase;padding:11px 16px;cursor:pointer;transition:.3s;font-family:var(--f-body)}
.chip:hover{border-color:var(--bronze);color:var(--bronze-2)}
.chip.on{background:var(--bronze);border-color:var(--bronze);color:var(--night)}
.compte{font-size:12.5px;color:var(--muted)}

/* cartes */
.rooms{display:grid;grid-template-columns:repeat(3,1fr);gap:30px;margin-top:48px}
.card{background:var(--bark-2);border:1px solid transparent;display:flex;flex-direction:column;
  transition:.5s cubic-bezier(.2,.8,.2,1)}
.card:hover{border-color:var(--line);transform:translateY(-4px)}
.card .ph{position:relative;aspect-ratio:4/3;overflow:hidden;background:var(--bark-3)}
.card .ph img{width:100%;height:100%;object-fit:cover;transition:1.1s cubic-bezier(.2,.8,.2,1)}
.card:hover .ph img{transform:scale(1.05)}
.card .tag{position:absolute;top:14px;left:14px;background:var(--bronze);color:var(--night);
  font-size:9px;letter-spacing:.18em;text-transform:uppercase;font-weight:700;padding:7px 11px}
.card .tx{padding:26px 24px 28px;display:flex;flex-direction:column;flex:1}
.card h2{font-size:1.32rem;margin-bottom:7px;font-weight:400}
.card .meta{font-size:12.5px;color:var(--muted);margin-bottom:14px}
.card p{font-size:13.5px;color:#AA9B87;flex:1}
.card .bas{display:flex;justify-content:space-between;align-items:flex-end;gap:14px;
  margin-top:22px;padding-top:18px;border-top:1px solid var(--line-2)}
.card .pr b{display:block;font-family:var(--f-display);font-size:1.6rem;color:var(--bronze);
  line-height:1;font-variant-numeric:tabular-nums;font-weight:400}
.card .pr span{font-size:9.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:600}
.card .go{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--bronze);font-weight:700;white-space:nowrap}
.card:hover .go{color:var(--bronze-2)}
.vide{display:none;text-align:center;color:var(--muted);padding:60px 0;font-style:italic}
.vide.on{display:block}

/* comparateur */
.cmp-sec{background:var(--bark);border-block:1px solid var(--line)}
.cmp-wrap{overflow-x:auto;margin-top:40px;border:1px solid var(--line)}
table{border-collapse:collapse;width:100%;min-width:760px;font-size:14px}
th,td{padding:15px 18px;text-align:left;border-bottom:1px solid var(--line-2)}
thead th{background:var(--bark-3);font-family:var(--f-body);font-size:9.5px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--bronze);font-weight:700;white-space:nowrap}
tbody tr{transition:.3s}
tbody tr:hover{background:rgba(185,138,80,.05)}
tbody th{font-family:var(--f-display);font-size:1.02rem;font-weight:400;color:var(--cream);white-space:nowrap}
tbody th a:hover{color:var(--bronze-2)}
td{color:#B4A794}
td.num{font-variant-numeric:tabular-nums;color:var(--bronze);white-space:nowrap}
caption{caption-side:bottom;padding:16px 4px 0;font-size:12.5px;color:var(--muted);text-align:left;font-style:italic}

/* inclus */
.inc-sec{padding:88px 0}
.inc{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);
  border:1px solid var(--line);margin-top:40px}
.inc div{background:var(--bark);padding:26px 22px}
.inc svg{width:21px;height:21px;stroke:var(--bronze);fill:none;stroke-width:1.3;margin-bottom:14px}
.inc b{display:block;font-size:14px;color:var(--cream);font-weight:600;margin-bottom:4px}
.inc span{font-size:12.5px;color:#A9997F}

.fin{text-align:center;padding:88px 0 100px;border-top:1px solid var(--line)}
.fin p{max-width:52ch;margin:16px auto 28px;color:#B4A794}

@media(max-width:1080px){.rooms{grid-template-columns:repeat(2,1fr)}.inc{grid-template-columns:repeat(2,1fr)}}
@media(max-width:720px){
  section{padding:64px 0}
  .rooms{grid-template-columns:1fr;gap:24px}
  .bar{position:static;flex-direction:column;align-items:flex-start;gap:14px}
  .inc{grid-template-columns:1fr}
}
"""

INCLUS = [
 ('Petit-déjeuner', "Compris dans toutes les catégories",
  '<path d="M12 3v6M8 21h8M6 12h12l-2 9H8z"/>'),
 ('Navette aéroport', "Offerte, aller et retour",
  '<path d="M2 16l20-7-8 12-2-5-5-2z"/><path d="M4 20h7"/>'),
 ('Wifi', "Gratuit, chambre et espaces communs",
  '<path d="M5 13a10 10 0 0114 0M8.5 16.5a5 5 0 017 0"/><circle cx="12" cy="20" r="1"/>'),
 ('Climatisation', "Dans chaque chambre",
  '<path d="M12 3v18M3 12h18M6 6l12 12M18 6L6 18"/>'),
 ('Piscine &amp; lagune', "Accès libre du lever au coucher",
  '<path d="M3 17c2 1 4-1 6 0s4 1 6 0 4-1 6 0M3 12c2 1 4-1 6 0s4 1 6 0 4-1 6 0"/>'),
 ('Parking', "Gratuit et surveillé",
  '<rect x="3" y="3" width="18" height="18"/><path d="M9 17V7h3.5a3 3 0 010 6H9"/>'),
 ('Réception 24 h/24', "Quelle que soit votre heure d\'arrivée",
  '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
 ('Meilleur tarif garanti', "En réservant en direct ici",
  '<path d="M12 3l2.6 5.6 6.4.9-4.6 4.4 1.1 6.1-5.5-3-5.5 3 1.1-6.1L3 9.5l6.4-.9z"/>'),
]

# ---------------------------------------------------------------------------

b = [header('reserver.html', 'Réserver', 'cta'), drawer('index.html#chambres'), '''
<section class="hero">
  <picture><source srcset="img/opt/r-mezzanine.webp" type="image/webp">
  <img src="img/opt/r-mezzanine.jpg" width="1400" height="933" alt="Chambre en mezzanine de l'Hôtel Evannath"></picture>
  <div class="in wrap">
    <nav class="crumb" aria-label="Fil d'Ariane">
      <a href="index.html">Accueil</a> &nbsp;·&nbsp; <span>Chambres &amp; Suites</span>
    </nav>
    <span class="eyebrow">Sept catégories · 46 chambres</span>
    <h1>Où vous allez dormir</h1>
    <p>De la Chambre Standard à la Suite Arabe et ses deux chambres. Chaque catégorie a son décor, sa vue et son tarif affiché en clair — rien ne s'ajoute à l'arrivée.</p>
  </div>
</section>

<section class="wrap" id="liste">
  <div class="bar">
    <div class="grp" role="group" aria-label="Filtrer par type">
      <b data-t="ft">Type</b>
      <button class="chip on" data-f="tout" data-t="f0">Tout voir</button>
      <button class="chip" data-f="chambre" data-t="f1">Chambres</button>
      <button class="chip" data-f="suite" data-t="f2">Suites</button>
      <button class="chip" data-f="famille" data-t="f3">Familles</button>
    </div>
    <div class="grp" role="group" aria-label="Trier">
      <b data-t="tr">Trier</b>
      <button class="chip on" data-s="prix" data-t="t1">Tarif croissant</button>
      <button class="chip" data-s="-prix" data-t="t2">Tarif décroissant</button>
      <button class="chip" data-s="-pax" data-t="t3">Capacité</button>
    </div>
    <span class="compte" id="compte"></span>
  </div>

  <div class="rooms" id="grille">''']

for c in CHAMBRES:
    ph, alt, _ = c['photos'][0]
    tag = '<span class="tag">%s</span>' % c['tag'] if c['tag'] else ''
    resume = c['p1'].split('. ')[0] + '.'
    b.append('''    <article class="card" data-fam="%s" data-prix="%d" data-pax="%d">
      <a href="%s.html" aria-label="%s — %s FCFA la nuit">
        <div class="ph">%s<picture><source srcset="img/opt/%s.webp" type="image/webp">
          <img loading="lazy" src="img/opt/%s.jpg" width="1400" height="933" alt="%s"></picture></div>
      </a>
      <div class="tx">
        <h2><a href="%s.html">%s</a></h2>
        <p class="meta">%s</p>
        <p>%s</p>
        <div class="bas">
          <span class="pr"><b>%s</b><span>FCFA · la nuit</span></span>
          <a href="%s.html" class="go">Voir la chambre &nbsp;&rarr;</a>
        </div>
      </div>
    </article>''' % (FAMILLE[c['slug']], c['prix'], c['pax'],
                     c['slug'], c['nom'], fmt(c['prix']),
                     tag, ph, ph, alt,
                     c['slug'], c['nom'], c['meta'], resume,
                     fmt(c['prix']), c['slug']))

b.append('''  </div>
  <p class="vide" id="vide" data-t="vd">Aucune catégorie ne correspond à ce filtre.</p>
</section>

<section class="cmp-sec">
  <div class="wrap">
    <span class="eyebrow">Comparer</span>
    <h2 style="margin-top:14px">Les sept, côte à côte</h2>
    <div class="cmp-wrap">
      <table>
        <caption>Tarifs par nuit, petit-déjeuner et navette aéroport compris. La taxe de séjour de 1 500 FCFA par personne et par nuit s'ajoute au moment du règlement.</caption>
        <thead><tr>
          <th scope="col" data-t="h1">Catégorie</th><th scope="col" data-t="h2">Type</th>
          <th scope="col" data-t="h3">Personnes</th><th scope="col" data-t="h4">Ce qui la distingue</th>
          <th scope="col" data-t="h5">Tarif / nuit</th>
        </tr></thead>
        <tbody>''')

for c in sorted(CHAMBRES, key=lambda x: x['prix']):
    b.append('          <tr><th scope="row"><a href="%s.html">%s</a></th>'
             '<td>%s</td><td>%d</td><td>%s</td><td class="num">%s F</td></tr>'
             % (c['slug'], c['nom'], FAM_NOM[FAMILLE[c['slug']]], c['pax'],
                c['meta'].split('·')[-1].strip(), fmt(c['prix'])))

b.append('''        </tbody>
      </table>
    </div>
  </div>
</section>

<section class="inc-sec wrap">
  <span class="eyebrow">Dans toutes les catégories</span>
  <h2 style="margin-top:14px">Compris, sans supplément</h2>
  <div class="inc">''')

for titre, desc, ic in INCLUS:
    b.append('    <div><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg><b>%s</b><span>%s</span></div>'
             % (ic, titre, desc))

b.append('''  </div>
</section>

<section class="fin wrap">
  <span class="eyebrow">Prêt ?</span>
  <h2 style="margin-top:14px">Réservez en direct</h2>
  <p>Le tarif affiché ici est notre meilleur tarif. Vous ne le trouverez pas moins cher ailleurs, et l'acompte se règle par Wave, Orange Money, MTN ou carte bancaire.</p>
  <a href="reserver.html" class="btn btn-solid" data-t="cta2">Vérifier les disponibilités</a>
</section>

''' + FOOTER)

JS = NAV_JS + '''

var grille=document.getElementById('grille'),
    cartes=[].slice.call(grille.children),
    compte=document.getElementById('compte'),
    vide=document.getElementById('vide');
var filtre='tout', tri='prix';

function appliquer(){
  var visibles=cartes.filter(function(c){
    var ok = filtre==='tout' || c.dataset.fam===filtre;
    c.style.display = ok ? '' : 'none';
    return ok;
  });
  var signe = tri.charAt(0)==='-' ? -1 : 1, cle = tri.replace('-','');
  visibles.sort(function(a,b){ return signe * (+a.dataset[cle] - +b.dataset[cle]); });
  visibles.forEach(function(c){ grille.appendChild(c); });
  compte.textContent = visibles.length + (visibles.length>1 ? ' catégories' : ' catégorie');
  vide.classList.toggle('on', visibles.length===0);
}

document.querySelectorAll('[data-f]').forEach(function(b){
  b.onclick=function(){
    document.querySelectorAll('[data-f]').forEach(function(x){x.classList.toggle('on',x===b)});
    filtre=b.dataset.f; appliquer();
  };
});
document.querySelectorAll('[data-s]').forEach(function(b){
  b.onclick=function(){
    document.querySelectorAll('[data-s]').forEach(function(x){x.classList.toggle('on',x===b)});
    tri=b.dataset.s; appliquer();
  };
});
appliquer();

var EN={''' + EN_NAV + '''cta:"Book",cta2:"Check availability",
ft:"Type",tr:"Sort",f0:"All",f1:"Rooms",f2:"Suites",f3:"Families",
t1:"Price, low to high",t2:"Price, high to low",t3:"Capacity",
h1:"Category",h2:"Type",h3:"Guests",h4:"What sets it apart",h5:"Rate / night",
vd:"No category matches this filter."};

''' + LANG_JS

LD = _schema.bloc(
    {'@type': 'ItemList',
     'name': "Chambres et suites de l'Hôtel Evannath",
     'numberOfItems': len(CHAMBRES),
     'itemListElement': [
         {'@type': 'ListItem', 'position': i,
          'item': _schema.chambre(c['nom'].replace('&amp;', '&'), c['slug'], c['prix'],
                                  c['pax'], c['meta'], [p[0] for p in c['photos']])}
         for i, c in enumerate(sorted(CHAMBRES, key=lambda x: x['prix']), 1)]},
    _schema.hotel(),
    _schema.fil([('Accueil', 'index'), ('Chambres &amp; Suites', None)]))

io.open('chambres.html', 'w', encoding='utf-8').write(page(
    "Chambres &amp; Suites — Hôtel Evannath, Assinie | de 67 000 à 280 000 FCFA",
    "Les sept catégories de l'Hôtel Evannath à Assinie PK 19 : de la Chambre Standard "
    "à 67 000 FCFA à la Suite Arabe à 280 000 FCFA. Petit-déjeuner et navette aéroport "
    "compris dans toutes les catégories.",
    "r-mezzanine", CSS, '\n'.join(b), JS, preload="r-mezzanine",
    slug="chambres", jsonld=LD))
print('chambres.html         %d categories' % len(CHAMBRES))
