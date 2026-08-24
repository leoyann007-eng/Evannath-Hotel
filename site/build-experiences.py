# -*- coding: utf-8 -*-
"""Genere experiences.html.

Contenu tire de la page Services et des circuits reellement publies par
l'hotel. Les quatre excursions des environs n'ont volontairement aucune
photo : les seuls visuels existants sont des images de synthese.
"""
import io
import _schema
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV

# ── sur le domaine ────────────────────────────────────────────
DOMAINE = [
 ('gal-lag-paillote', "La paillote", 'Le ponton de bois posé sur la lagune Aby. Le cœur du domaine — on y prend un verre au couchant, on y dîne aux lanternes de rotin.', 'Toute la journée', 'carte.html', 'Voir la carte'),
 ('gal-spa-couchant', "Piscine &amp; jacuzzi", 'Un grand bassin avec jacuzzi intégré, transats et parasols. Ouvert du lever du jour à la nuit tombée.', 'Accès libre', 'spa.html', 'Le spa'),
 ('gal-spa-case', "Spa &amp; sauna", 'Massages aux pierres chauffantes, rituel de l\'Orient à l\'argan, gommage au savon noir africain. Vingt-deux soins, sur rendez-vous.', 'Sur rendez-vous', 'spa.html', 'Les soins'),
 ('gal-tab-rotin', "Restaurant &amp; bar", 'Cuisine ivoirienne et continentale, poisson du jour, quatorze cocktails maison dont deux signatures.', 'Midi et soir', 'carte.html', 'La table'),
 ('gal-tab-comptoir', "Night-club", 'DJ résident les week-ends, terrasse ouverte tard. Happy hour le samedi après la Méchoui Party.', 'Week-ends', 'circuits.html', 'Méchoui Party'),
 ('ig-enfants', "Aire de jeux", 'Pour les enfants : jeux, ateliers cuisine et peinture, maquillage, conte en bordure d\'eau le soir.', 'Toute la journée', 'circuits.html', 'Découvertes Junior'),
]

# ── sur l'eau ─────────────────────────────────────────────────
EAU = [
 ('01', "Balade lagunaire en pirogue", 'Guide local, escale sur l\'île, retour au couchant. C\'est l\'activité dont nos clients reparlent le plus.', 'Matin ou fin d\'après-midi'),
 ('02', "Jet ski", 'Sessions encadrées, matériel fourni. Deux créneaux par jour, au lever du soleil et en fin d\'après-midi.', 'Sur réservation'),
 ('03', "L\'Embouchure", 'Là où l\'océan Atlantique rencontre la lagune Aby. Quinze minutes de bateau depuis notre ponton.', 'Demi-journée'),
 ('04', "Arrivée par la lagune", 'Rejoindre l\'hôtel en pirogue plutôt qu\'en voiture. À organiser avec la réception la veille.', 'À la demande'),
]

# ── autour d'Assinie ──────────────────────────────────────────
AUTOUR = [
 ("L'Île Abandonnée", "Une presqu'île entre l'océan et la lagune Aby, plages désertes et eaux claires. Peu fréquentée, et c'est ce qui fait sa valeur."),
 ("Le Parc Dipi", "La première réserve naturelle de la région. Excursion d'une demi-journée, organisée par la conciergerie."),
 ("Le musée Aniaba", "Collections liées à l'histoire du royaume et de la côte. À combiner avec la visite de la commune."),
 ("La commune d'Assinie", "Balade guidée, histoire du lieu, marché local. Comprise dans le circuit Découvertes Touristiques."),
]

CSS = """
.hero{position:relative;min-height:76vh;display:flex;align-items:flex-end;overflow:hidden}
.hero>picture img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.hero::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(23,16,10,.78),rgba(23,16,10,.36) 44%,rgba(23,16,10,.97))}
.hero .in{position:relative;z-index:3;width:100%;padding-bottom:56px}
.hero h1{margin:12px 0 18px;font-size:clamp(2.6rem,6vw,4.2rem)}
.hero p{max-width:56ch;font-size:1.08rem}

section{padding:104px 0}
.head{text-align:center;margin-bottom:60px}
.head p{max-width:54ch;margin:18px auto 0;color:#B4A794}

/* sur le domaine */
.dom{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.card{background:var(--bark-2);border:1px solid var(--line);overflow:hidden;display:flex;flex-direction:column;transition:.5s cubic-bezier(.2,.8,.2,1)}
.card:hover{transform:translateY(-6px);border-color:rgba(185,138,80,.5)}
.card .ph{aspect-ratio:16/10;overflow:hidden;position:relative}
.card .ph img{width:100%;height:100%;object-fit:cover;transition:1s cubic-bezier(.2,.8,.2,1)}
.card:hover .ph img{transform:scale(1.07)}
.card .when{position:absolute;top:13px;left:13px;background:rgba(23,16,10,.88);backdrop-filter:blur(6px);
  color:var(--bronze);font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;padding:7px 12px;font-weight:700}
.card .in{padding:24px;display:flex;flex-direction:column;flex:1}
.card h3{margin-bottom:10px;font-weight:400}
.card p{font-size:14px;flex:1}
.card a{display:inline-block;margin-top:18px;font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--bronze);border:1px solid var(--bronze);padding:13px 18px;font-weight:700;transition:.3s;width:max-content}
.card a:hover{background:var(--bronze);color:var(--night)}

/* sur l'eau */
.eau-sec{background:var(--bark);border-block:1px solid var(--line)}
.plate{display:grid;grid-template-columns:88px 1fr auto;gap:34px;align-items:baseline;padding:34px 0;
  border-top:1px solid var(--line-2);transition:.45s}
.plate:last-of-type{border-bottom:1px solid var(--line-2)}
.plate:hover{background:linear-gradient(90deg,rgba(185,138,80,.055),transparent 70%)}
.plate .n{font-family:var(--f-display);font-size:2.2rem;color:var(--bronze);opacity:.4;line-height:.8;
  font-variant-numeric:tabular-nums;transition:.45s}
.plate:hover .n{opacity:1}
.plate h3{font-size:clamp(1.3rem,2.3vw,1.8rem);margin-bottom:10px;font-weight:400}
.plate p{font-size:14.5px;color:#B4A794;max-width:56ch}
.plate .q{font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);font-weight:700;white-space:nowrap}

/* autour */
.autour{display:grid;grid-template-columns:repeat(2,1fr);gap:1px;background:var(--line);border:1px solid var(--line)}
.autour div{background:var(--bark-2);padding:34px 30px;transition:.4s}
.autour div:hover{background:var(--bark-3)}
.autour h3{font-size:1.3rem;margin-bottom:10px;font-weight:400}
.autour p{font-size:14px;color:#A9997F}
.note{border-left:2px solid var(--bronze);padding:8px 0 8px 22px;margin-top:34px;font-size:14px;
  color:var(--muted);font-style:italic;max-width:62ch}

.band{position:relative;height:56vh;min-height:340px;overflow:hidden}
.band img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.band::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(16,11,6,.5) 0%,rgba(16,11,6,.22) 30%,rgba(16,11,6,.72) 62%,rgba(16,11,6,.95) 100%)}
.band .cap{position:absolute;left:0;right:0;bottom:38px;z-index:3;text-align:center;padding:0 24px}
.band .cap span{font-size:10px;letter-spacing:.34em;text-transform:uppercase;color:var(--bronze-2);font-weight:700;
  text-shadow:0 2px 14px rgba(10,6,3,.95)}
.band .cap p{text-shadow:0 2px 18px rgba(10,6,3,.9);font-family:var(--f-display);
  font-size:clamp(1.3rem,2.6vw,2rem);color:var(--cream);margin-top:12px;max-width:24ch;margin-inline:auto;line-height:1.25}

.cta{border:1px solid var(--bronze);padding:52px;text-align:center;margin-bottom:100px}
.cta h2{margin-bottom:14px}
.cta p{max-width:52ch;margin:0 auto 28px}
.cta .g{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}

@media(max-width:1080px){.dom{grid-template-columns:repeat(2,1fr)}.autour{grid-template-columns:1fr}}
@media(max-width:720px){
  section{padding:72px 0}
  .dom{grid-template-columns:1fr}
  .plate{grid-template-columns:1fr;gap:10px;padding:28px 0}
  .plate .n{font-size:1.5rem;opacity:1}
  .autour div,.cta{padding:26px}
  .band{height:44vh}
}
"""

b = [header('reserver.html', 'Réserver'), drawer(''), '''
<section class="hero">
  <picture><source srcset="img/opt/gal-lag-bateau.webp" type="image/webp">
  <img src="img/opt/gal-lag-bateau.jpg" width="1400" height="933" alt="Le ponton de l'hôtel et le bateau de balade sur la lagune Aby"></picture>
  <div class="in wrap">
    <nav class="crumb" aria-label="Fil d'Ariane">
      <a href="index.html">Accueil</a> &nbsp;·&nbsp; <span>Expériences</span>
    </nav>
    <span class="eyebrow">Sur le domaine, sur l'eau, autour d'Assinie</span>
    <h1>De quoi remplir<br>une journée entière</h1>
    <p>Vous pouvez ne rien faire — beaucoup viennent pour ça. Mais si vous voulez sortir de votre chambre, voici tout ce qui vous attend.</p>
  </div>
</section>

<section class="wrap" id="domaine">
  <div class="head reveal">
    <span class="eyebrow">Sur le domaine</span>
    <h2 style="margin-top:16px">Sans passer le portail</h2>
    <p>Six lieux, tous à moins de deux minutes de marche de votre chambre.</p>
  </div>
  <div class="dom reveal">''']

for img, titre, desc, quand, href, lien in DOMAINE:
    b.append('''    <article class="card">
      <div class="ph"><picture><source srcset="img/opt/%s.webp" type="image/webp">
        <img loading="lazy" src="img/opt/%s.jpg" alt="%s"></picture>
        <span class="when">%s</span></div>
      <div class="in"><h3>%s</h3><p>%s</p>
        <a href="%s">%s</a></div>
    </article>''' % (img, img, titre.replace('&amp;', 'et'), quand, titre, desc, href, lien))

b.append('''  </div>
</section>

<div class="band reveal">
  <picture><source srcset="img/opt/gal-lag-nuit.webp" type="image/webp">
  <img src="img/opt/gal-lag-nuit.jpg" width="1400" height="933" alt="La paillote à la tombée du jour" loading="lazy"></picture>
  <div class="cap"><span>Le service du soir</span><p>Les lanternes s'allument quand la lumière part.</p></div>
</div>

<section class="eau-sec" id="eau">
  <div class="wrap">
    <div class="head reveal">
      <span class="eyebrow">Sur l'eau</span>
      <h2 style="margin-top:16px">La lagune commence<br>au bout du ponton</h2>
      <p>Toutes ces sorties partent de notre propre embarcadère. Réservation à la réception, la veille suffit.</p>
    </div>
    <div class="reveal">''')

for n, titre, desc, quand in EAU:
    b.append('''      <article class="plate">
        <span class="n">%s</span>
        <div><h3>%s</h3><p>%s</p></div>
        <span class="q">%s</span>
      </article>''' % (n, titre, desc, quand))

b.append('''    </div>
  </div>
</section>

<section class="wrap" id="autour">
  <div class="head reveal">
    <span class="eyebrow">Autour d'Assinie</span>
    <h2 style="margin-top:16px">Quatre sorties<br>que la réception organise</h2>
    <p>Elles figurent dans le circuit Découvertes Touristiques, à 35 000 FCFA par personne.</p>
  </div>
  <div class="autour reveal">''')

for titre, desc in AUTOUR:
    b.append('    <div><h3>%s</h3><p>%s</p></div>' % (titre, desc))

b.append('''  </div>
  <p class="note reveal">Ces quatre lieux n'ont pas de photographie sur cette page : nous préférons
  ne rien montrer plutôt que de montrer une image qui ne serait pas la nôtre.</p>
</section>

<div class="wrap">
  <div class="cta reveal">
    <span class="eyebrow">Tout est réservable</span>
    <h2>Composez votre séjour</h2>
    <p>Onze forfaits réunissent chambre, repas et activités — de la journée Chillday à la lune de miel.</p>
    <div class="g">
      <a href="circuits.html" class="btn btn-solid">Voir les circuits</a>
      <a href="reserver.html" class="btn">Réserver une chambre</a>
    </div>
  </div>
</div>

''' + FOOTER)

JS = NAV_JS + '\n\nvar EN={' + EN_NAV + 'cta:"Book"};\n\n' + LANG_JS

LD = _schema.bloc(
    _schema.service('Expériences et activités', "Balade lagunaire en pirogue, jet ski, spa, piscine et excursions autour d'Assinie depuis l'Hôtel Evannath.", 'experiences', image='gal-lag-bateau'),
    _schema.hotel(),
    _schema.fil([('Accueil','index'),('Expériences',None)]))

io.open('experiences.html', 'w', encoding='utf-8').write(page(
 "Expériences — Hôtel Evannath, Assinie",
 "Balade lagunaire en pirogue, jet ski, l'Embouchure, spa et sauna, piscine et jacuzzi, night-club : tout ce que l'on peut faire à l'Hôtel Evannath, Assinie PK 19.",
 "gal-lag-bateau", CSS, '\n'.join(b), JS, preload="gal-lag-bateau", slug="experiences", jsonld=LD))
print('experiences.html      ok')
