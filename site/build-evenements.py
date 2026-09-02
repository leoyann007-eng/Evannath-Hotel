# -*- coding: utf-8 -*-
"""Genere evenements.html a partir de _evenements.py.

La page que l'etablissement n'avait pas : un endroit pour ce qui a une date.
Les offres permanentes restent sur circuits.html — cette page y renvoie et
ne recopie aucun tarif.

Une affiche perimee reste dans le fichier mais disparait de la page : le
navigateur compare la date de fin a la date du jour au chargement. Sans cela,
un site d'hotel finit toujours par annoncer le reveillon au mois de mars.
"""
import io
import _schema
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV, SITE
from _evenements import EVENEMENTS, EN

CSS = """
.hero{position:relative;min-height:52vh;display:flex;align-items:flex-end;overflow:hidden;padding-top:150px}
.hero>picture img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.hero::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(23,16,10,.80),rgba(23,16,10,.40) 46%,rgba(23,16,10,.97))}
.hero .in{position:relative;z-index:3;width:100%;padding-bottom:52px}
.hero h1{margin:12px 0 16px;font-size:clamp(2.4rem,5.4vw,3.8rem)}
.hero p{max-width:56ch;font-size:1.06rem}

section{padding:96px 0}
.head{text-align:center;margin-bottom:56px}
.head p{max-width:56ch;margin:18px auto 0;color:#B4A794}

.evs{display:flex;flex-direction:column;gap:34px}

/* Une affiche carree se pose a cote du texte ; une banniere le surmonte. */
.ev{background:var(--bark-2);border:1px solid var(--line);overflow:hidden;
    display:grid;transition:.5s cubic-bezier(.2,.8,.2,1)}
.ev:hover{border-color:rgba(185,138,80,.5)}
.ev.carre{grid-template-columns:340px 1fr}
.ev.large{grid-template-columns:1fr}
/* min-width:0 — sans lui, l'element de grille prend la largeur INTRINSEQUE
   de l'affiche (1100 px) et fait deborder toute la page sur telephone. */
.ev{min-width:0}
.ev .ph{position:relative;overflow:hidden;background:var(--bark-3);min-width:0}
.ev.carre .ph{aspect-ratio:1/1}
.ev.large .ph{aspect-ratio:21/7}
.ev .ph img{width:100%;height:100%;object-fit:cover}
.ev .tx{padding:34px 38px;display:flex;flex-direction:column;justify-content:center}
.ev .quand{font-size:10.5px;letter-spacing:.28em;text-transform:uppercase;color:var(--bronze);font-weight:700}
.ev h2{font-size:1.72rem;margin:10px 0 12px}
.ev p{max-width:60ch;margin-bottom:20px}
.ev .btn{align-self:flex-start}

.vide{text-align:center;padding:60px 0;color:var(--muted)}

@media(max-width:900px){
  .ev.carre{grid-template-columns:1fr}
  .ev.carre .ph{aspect-ratio:16/10}
  .ev.large .ph{aspect-ratio:16/9}
  .ev .tx{padding:28px 24px}
}
"""

# ── le corps ──────────────────────────────────────────────────
b = [header('reserver.html', 'Réserver'), drawer('evenements.html', 'gal-lag-nuit',
     "La paillote de l'Hôtel Evannath éclairée à la tombée du jour")]

b.append('''
<div class="hero">
  <picture><source srcset="img/opt/gal-dom-couchant.webp" type="image/webp">
    <img src="img/opt/gal-dom-couchant.jpg" width="1748" height="1240" alt="Le domaine de l'Hôtel Evannath au couchant"></picture>
  <div class="in"><div class="wrap">
    <span class="eyebrow" data-t="e0">À l'affiche</span>
    <h1 data-t="e1">Événements &amp; offres du moment</h1>
    <p data-t="e2">Ce qui se passe à l'hôtel, et ce qui ne dure qu'un temps. Les
    formules permanentes, elles, sont sur la page Circuits &amp; Offres.</p>
  </div></div>
</div>

<section><div class="wrap">
  <div class="evs" id="evs">''')

for e in EVENEMENTS:
    fin = ' data-fin="%s"' % e['fin'] if e['fin'] else ''
    b.append('''    <article class="ev %s" id="%s"%s>
      <div class="ph"><picture><source srcset="img/opt/%s.webp" type="image/webp">
        <img src="img/opt/%s.jpg" alt="%s" loading="lazy"></picture></div>
      <div class="tx">
        <span class="quand" data-t="q-%s">%s</span>
        <h2 data-t="t-%s">%s</h2>
        <p data-t="x-%s">%s</p>
        <a class="btn" href="%s" data-t="c-%s">%s</a>
      </div>
    </article>''' % (e['format'], e['slug'], fin,
                     e['affiche'], e['affiche'], e['titre'],
                     e['slug'], e['quand'], e['slug'], e['titre'],
                     e['slug'], e['texte'], e['href'], e['slug'], e['cta']))

b.append('''  </div>
  <p class="vide" id="vide" hidden data-t="e3">Aucun événement annoncé pour le moment.
  Écrivez-nous, la réception vous dira ce qui se prépare.</p>
</div></section>''')

b.append(FOOTER)

# ── le script ─────────────────────────────────────────────────
# L'expiration se decide dans le navigateur, pas a la generation : le site est
# statique et personne ne le reconstruit le 2 janvier au matin.
JS_PAGE = """
(function(){
  var auj = new Date(); auj.setHours(0,0,0,0);
  var restants = 0;
  document.querySelectorAll('.ev').forEach(function(el){
    var fin = el.getAttribute('data-fin');
    if (fin && new Date(fin + 'T23:59:59') < auj) { el.remove(); return; }
    restants++;
  });
  if (!restants) document.getElementById('vide').hidden = false;
})();
"""

EN_PAGE = ('cta:"Book",e0:"On now",e1:"Events &amp; current offers",'
           'e2:"What is happening at the hotel, and what will not last. '
           'Our permanent packages are on the Packages &amp; Offers page.",'
           'e3:"Nothing announced right now. Write to us and the front desk will '
           'tell you what is coming.",')
for slug, (titre, quand, texte, cta) in EN.items():
    # Les cles portent un tiret — il faut les quoter. Sans cela le
    # dictionnaire n'est pas un objet JavaScript valide, et c'est TOUT le
    # script de la page qui ne s'execute plus : bascule de langue, navigation
    # et expiration des affiches comprises.
    EN_PAGE += '"q-%s":"%s","t-%s":"%s","x-%s":"%s","c-%s":"%s",' % (
        slug, quand, slug, titre, slug, texte, slug, cta)

JS = NAV_JS + '\n\nvar EN={' + EN_NAV + EN_PAGE + '};\n\n' + LANG_JS + '\n' + JS_PAGE

LD = _schema.bloc(
    _schema.evenements([(e['slug'], e['titre'], e['texte'], e['affiche'], e['fin'])
                        for e in EVENEMENTS]),
    _schema.hotel(),
    _schema.fil([('Accueil', 'index'), ('Événements', None)]))

io.open('evenements.html', 'w', encoding='utf-8').write(page(
 "Événements &amp; offres du moment — Hôtel Evannath, Assinie",
 "Les événements et offres datées de l'Hôtel Evannath, Assinie PK 19 : Packs Vacances, "
 "Méchoui Party du samedi, réveillon du 31 décembre et coffret anniversaire.",
 "gal-dom-couchant", CSS, '\n'.join(b), JS,
 preload="gal-dom-couchant", slug="evenements", jsonld=LD))
print('evenements.html       %d événements' % len(EVENEMENTS))
