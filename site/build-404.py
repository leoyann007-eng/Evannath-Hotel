# -*- coding: utf-8 -*-
"""Genere 404.html : une page d'erreur qui rattrape le visiteur au lieu de le perdre."""
import io
from _chrome import PROSPECTION
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV, WA

CSS = """
body{background:var(--bark)}
/* Padding symetrique : l'en-tete fixe ne peut plus recouvrir le contenu,
   et le centre optique reste exactement ou il etait sur un ecran normal. */
.err{position:relative;min-height:100svh;display:flex;align-items:center;overflow:hidden;padding:150px 0}
.err .bg{position:absolute;inset:0;background:url('img/opt/gal-lag-nuit.jpg') center/cover;animation:kb 24s ease-out forwards}
@keyframes kb{from{transform:scale(1.03)}to{transform:scale(1.12)}}
.err::after{content:"";position:absolute;inset:0;background:
  radial-gradient(ellipse at 50% 46%,rgba(16,11,6,.4),rgba(16,11,6,.9) 74%),
  linear-gradient(180deg,rgba(16,11,6,.8),transparent 34%,rgba(16,11,6,.97))}
.err .in{position:relative;z-index:3;width:100%;text-align:center;padding-top:60px}
.code{font-family:var(--f-display);font-size:clamp(5rem,18vw,13rem);line-height:.86;color:var(--bronze);
  opacity:.32;letter-spacing:.02em;font-variant-numeric:tabular-nums}
.err h1{font-size:clamp(2rem,5.4vw,3.6rem);margin:-8px 0 20px}
.err h1 em{font-style:italic;color:var(--bronze-2)}
.err .lede{max-width:46ch;margin:0 auto;font-size:1.06rem;color:var(--prose)}
.err .cta{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:36px}
.rule{width:1px;height:44px;background:linear-gradient(var(--bronze),transparent);margin:34px auto 0}

.ways{background:var(--bark);padding:100px 0;border-top:1px solid var(--line)}
.ways .head{text-align:center;margin-bottom:54px}
.ways .head p{max-width:50ch;margin:16px auto 0;color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}
.card{border:1px solid var(--line);background:var(--bark-2);overflow:hidden;transition:.45s;display:block}
.card:hover{transform:translateY(-6px);border-color:rgba(185,138,80,.55)}
.card .ph{aspect-ratio:4/3;overflow:hidden}
.card .ph img{width:100%;height:100%;object-fit:cover;transition:1s cubic-bezier(.2,.8,.2,1)}
.card:hover .ph img{transform:scale(1.07)}
.card .in{padding:22px}
.card h3{font-size:1.15rem;margin-bottom:8px;font-weight:400}
.card p{font-size:13.5px;color:var(--muted)}

.helpline{border:1px solid var(--bronze);padding:44px;text-align:center;margin:90px 0 100px}
.helpline h2{margin-bottom:12px}
.helpline p{max-width:52ch;margin:0 auto 26px}
.helpline .g{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}

@media(max-width:1080px){.cards{grid-template-columns:repeat(2,1fr)}}
@media(max-width:720px){
  .ways{padding:70px 0}
  .cards{grid-template-columns:1fr}
  .helpline{padding:30px;margin:60px 0 70px}
}
"""

WAYS = [
 ('index.html#chambres', 'gal-ch-wax',      "Chambres & Suites", 'w1',
  "Sept catégories, de 67 000 à 280 000 FCFA la nuit.", 'w1p'),
 ('carte.html',          'gal-tab-dressee', "La table",          'w2',
  "Cuisine ivoirienne, poisson du jour, cocktails maison.", 'w2p'),
 ('circuits.html',       'gal-lag-ponton',  "Offres & Événements", 'w3',
  "Onze formules, du Pack Enfant à la lune de miel.", 'w3p'),
 ('galerie.html',        'gal-dom-aerien',  "Galerie",           'w4',
  "Quarante-sept photographies du domaine.", 'w4p'),
]

b = [header('index.html#reserver', 'Réserver'), drawer(''), '''
<section class="err">
  <div class="bg"></div>
  <div class="in narrow">
    <div class="code">404</div>
    <h1 data-t="h1">Cette page a pris<br><em data-t="h1e">le large</em></h1>
    <p class="lede" data-t="lede">Elle a peut-être changé d'adresse, ou n'a jamais existé. Pendant qu'on la cherche, la lagune est toujours là.</p>
    <div class="cta">
      <a href="index.html" class="btn btn-solid" data-t="c1">Retour à l'accueil</a>
      <a href="contact.html" class="btn" data-t="c2">Nous écrire</a>
    </div>
    <div class="rule"></div>
  </div>
</section>

<section class="ways">
  <div class="wrap">
    <div class="head">
      <span class="eyebrow" data-t="eb">Vous cherchiez sans doute</span>
      <h2 style="margin-top:16px" data-t="h2">L'une de ces quatre pages</h2>
      <p data-t="p2">Ce sont celles que l'on consulte le plus. Si votre réponse n'y est pas, la réception répond 24 h/24.</p>
    </div>
    <div class="cards">''']

for href, img, title, tkey, desc, dkey in WAYS:
    b.append('''      <a class="card" href="%s">
        <div class="ph"><picture><source srcset="img/opt/%s-t.webp" type="image/webp">
          <img loading="lazy" width="620" height="413" src="img/opt/%s-t.jpg" alt="%s"></picture></div>
        <div class="in"><h3 data-t="%s">%s</h3><p data-t="%s">%s</p></div>
      </a>''' % (href, img, img, title, tkey, title, dkey, desc))

b.append('''    </div>

    <div class="helpline">
      <span class="eyebrow" data-t="eb2">Un lien cassé ?</span>
      <h2 data-t="h3">Dites-le-nous, on le répare</h2>
      <p data-t="p3">Si vous êtes arrivé ici depuis un lien, un message ou un moteur de recherche, signalez-le : nous corrigeons dans la journée.</p>
      <div class="g">
        <a href="https://wa.me/''' + WA + '''" target="_blank" rel="noopener" class="btn btn-solid" data-t="g1">Écrire sur WhatsApp</a>
        <a href="mailto:{{MAIL}}" class="btn" data-t="g2">{{MAIL}}</a>
      </div>
    </div>
  </div>
</section>

''' + FOOTER)

JS = NAV_JS + '''

var EN={''' + EN_NAV + '''cta:"Book now",
h1:"This page has<br>drifted off",h1e:"drifted off",
lede:"It may have moved, or never existed at all. While we look for it, the lagoon is still there.",
c1:"Back to the homepage",c2:"Write to us",
eb:"You were probably looking for",h2:"One of these four pages",
p2:"These are the most visited. If your answer is not there, the front desk answers 24/7.",
w1:"Rooms &amp; Suites",w1p:"Seven categories, from 67,000 to 280,000 FCFA a night.",
w2:"The table",w2p:"Ivorian cooking, catch of the day, house cocktails.",
w3:"Packages &amp; Offers",w3p:"Eleven packages, from the Kids Pack to the honeymoon.",
w4:"Gallery",w4p:"Forty-seven photographs of the estate.",
eb2:"A broken link?",h3:"Tell us and we will fix it",
p3:"If you arrived here from a link, a message or a search engine, let us know: we fix it the same day.",
g1:"Message on WhatsApp",g2:"{{MAIL}}"};

''' + LANG_JS

html = page(
 "Page introuvable — Hôtel Evannath, Assinie",
 "Cette page n'existe pas ou a changé d'adresse. Retrouvez les chambres, la table, les circuits et la galerie de l'Hôtel Evannath à Assinie.",
 "gal-lag-nuit", CSS, '\n'.join(b), JS, slug="404")
html = html.replace('<meta property="og:image"', (('' if PROSPECTION else '<meta name="robots" content="noindex, follow">\n') + '<meta property="og:image"'))
io.open('404.html', 'w', encoding='utf-8').write(html)
print('404.html              ok')
