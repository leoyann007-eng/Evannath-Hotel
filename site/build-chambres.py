# -*- coding: utf-8 -*-
"""Genere les 7 fiches chambres a partir d'un seul gabarit.

Tarifs, capacites et intitules proviennent du catalogue reel de l'hotel
(API WooCommerce de evannathhotel.com). Les conditions de sejour sont
des hypotheses a faire confirmer — voir README.
"""
import io
import _schema
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV

# slug, nom, prix, capacite, resume, accroche, 3 paragraphes, equipements+, photos
from _chambres import CHAMBRES
import _chambres_en
import json

PAR_SLUG = {c['slug']: c for c in CHAMBRES}

AMEN_BASE = [
 ('Air conditionné', '<path d="M3 12h18M8 8h12M6 16h12"/>'),
 ('Wifi gratuit',    '<path d="M5 13a10 10 0 0114 0M8.5 16.5a5 5 0 017 0"/><circle cx="12" cy="20" r="1"/>'),
 ('Télévision smart','<rect x="3" y="5" width="18" height="12"/><path d="M9 21h6"/>'),
 ('Salle d\'eau privative','<path d="M4 12h16v5a3 3 0 01-3 3H7a3 3 0 01-3-3zM7 12V6a2 2 0 014 0"/>'),
 ('Sèche-cheveux',   '<path d="M8 3v6a4 4 0 008 0V3M12 13v8M9 21h6"/>'),
 ('Coffre-fort',     '<rect x="4" y="4" width="16" height="16"/><path d="M9 9h6v6H9z"/>'),
 ('Accès piscine &amp; jacuzzi', '<path d="M3 17c2 1 4-1 6 0s4 1 6 0 4-1 6 0M3 12c2 1 4-1 6 0s4 1 6 0 4-1 6 0"/>'),
 ('Petit-déjeuner inclus', '<path d="M12 3v6M8 21h8M6 12h12l-2 9H8z"/>'),
]
ICONE_PLUS = '<path d="M12 3l2.4 5.6L20 9.7l-4 4 1 6-5-2.9L7 19.7l1-6-4-4 5.6-1.1z"/>'

INCL = [
 ('Petit-déjeuner','Servi au restaurant ou en terrasse, fruits frais et produits locaux.'),
 ('Navette aéroport gratuite','Prise en charge et dépose à l\'aéroport Félix-Houphouët-Boigny, sans frais, à la demande.'),
 ('Piscine, jacuzzi et salle de sport','Accès libre du lever du jour à la nuit tombée.'),
 ('Wifi et parking','Gratuits sur tout le domaine.'),
]

CSS = open('chambre-style.css', encoding='utf-8').read() if False else """
.head{padding:150px 0 34px}
.head-top{display:flex;justify-content:space-between;align-items:flex-end;gap:30px;flex-wrap:wrap}
.head h1{margin:10px 0 0}
.facts{display:flex;gap:26px;flex-wrap:wrap;margin-top:22px;font-size:13.5px;color:var(--muted)}
.facts b{color:var(--cream);font-weight:500}
.head-price{text-align:right}
.head-price b{font-family:var(--f-display);font-size:2.6rem;color:var(--bronze);display:block;line-height:1;font-variant-numeric:tabular-nums;font-weight:400}
.head-price span{font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:600}
.mosaic{display:grid;grid-template-columns:2fr 1fr 1fr;grid-auto-rows:172px;gap:10px;margin-bottom:76px}
.mosaic figure{overflow:hidden;position:relative;cursor:pointer;background:var(--bark-2)}
.mosaic figure:first-child{grid-column:span 1;grid-row:span 2}
/* La mosaique doit tomber juste, sinon la grille laisse un trou visible.
   A trois photos, la premiere prenait deux rangees sans que rien ne remplisse
   la seconde : 27 % de vide sous les deux vignettes, sur six fiches.
   A huit photos, c'est la grille a deux colonnes qui finissait sur une rangee
   incomplete ; la derniere image s'y etale alors sur toute la largeur.
   Les deux classes sont posees par le generateur, qui seul connait le nombre. */
.mosaic.court figure:first-child{grid-row:span 1}
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
.amen div.hi{background:var(--bark-2)}
.amen div.hi svg{stroke:var(--bronze-2)}
.amen div.hi b{color:var(--cream);font-weight:600;display:block}
.amen div.hi em{font-style:normal;font-size:12px;color:var(--muted);display:block;margin-top:2px}
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
.calc .total b{font-family:var(--f-display);font-size:1.85rem;color:var(--bronze-2);font-variant-numeric:tabular-nums;font-weight:400}
.panel .btn{width:100%;margin-top:20px}
.avail{display:flex;align-items:center;gap:9px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--palm);font-weight:700;margin-top:16px;justify-content:center}
.avail i{width:7px;height:7px;border-radius:50%;background:var(--palm);display:inline-block}
.panel .helpt{font-size:12.5px;color:var(--muted);text-align:center;margin-top:16px;line-height:1.5}
.panel .helpt a{color:var(--bronze);border-bottom:1px solid var(--line)}
.more{background:var(--bark-2);padding:88px 0}
.more-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:40px}
.rcard{background:var(--bark);border:1px solid var(--line);overflow:hidden;transition:.5s cubic-bezier(.2,.8,.2,1);display:block}
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
.mobar b{font-family:var(--f-display);font-size:1.35rem;color:var(--bronze);display:block;line-height:1;font-variant-numeric:tabular-nums;font-weight:400}
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
  .mosaic.court figure:first-child{grid-row:span 2}
  .mosaic figure.plein{grid-column:span 2}
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

# Largeurs reelles des vignettes de la mosaique -------------------------------
#
# .wrap fait min(1240px, 100vw) - 48. La grille est en 2fr 1fr 1fr avec 10 px
# de gouttiere au-dela de 1100 px, en deux colonnes entre 721 et 1100, et en
# une seule colonne en dessous. La premiere figure occupe deux rangees, donc
# la moitie de la largeur en grand, et toute la largeur en dessous de 1100.
#
# Sans ces declarations, une vignette de 293 px se faisait servir le palier
# 1024 : le navigateur ne voit pas la grille, il croit ce qu'on lui declare.
#
# Placement en trois colonnes : la premiere figure prend la colonne large sur
# deux rangees, donc les quatre suivantes remplissent les deux colonnes
# etroites. A partir de la sixieme, les rangees repartent sur les trois
# colonnes — l'image d'indice 5, puis 8, puis 11, retombe dans la colonne
# large. En dessous de cinq photos la premiere ne prend qu'une rangee.
_LARGE_3COL = '(max-width:1287px) calc((100vw - 68px) / 2), 586px'
_ETROIT_3COL = '(max-width:1287px) calc((100vw - 68px) / 4), 293px'
# Deux colonnes : pleine largeur pour la premiere et pour une derniere etalee,
# demi-largeur sinon. Une seule colonne en dessous de 721 px.
_PLEIN = 'calc(100vw - 48px)'
_DEMI = 'calc((100vw - 58px) / 2)'


def _sizes_mosaique(i, n):
    """Declaration de largeur pour la i-eme photo d'une mosaique de n.

    Composee a partir du placement reel, pas approximee : une vignette de
    293 px se faisait servir le palier 1024 parce qu'on lui declarait 700 px.
    """
    grand = (i == 0) or (n >= 5 and i >= 5 and (i - 5) % 3 == 0)
    etale = (i == 0) or (i == n - 1 and n % 2 == 0)   # pleine largeur a 2 colonnes
    trois = _LARGE_3COL if grand else _ETROIT_3COL
    deux = _PLEIN if etale else _DEMI
    if i == 0:
        return '(max-width:1100px) %s, %s' % (_PLEIN, trois)
    return '(max-width:720px) %s, (max-width:1100px) %s, %s' % (_PLEIN, deux, trois)


def fmt(n):
    return format(n, ',').replace(',', ' ')


def _en_dict(c):
    """Assemble le dictionnaire anglais de la fiche, cle par cle.

    Les cles sont celles des data-t poses dans le balisage. Si une traduction
    manque, LANG_JS laisse le francais en place plutot que d'afficher un trou
    — et verifier.py signale le manque.
    """
    e = _chambres_en.EN[c['slug']]
    d = dict(_chambres_en.CHASSIS)
    d['mbb'] = d['cta']
    d['eb0'] = e['tag'] or _chambres_en.CHASSIS['eb0']
    d['ttl'] = e['titre']
    d['pa1'], d['pa2'], d['pa3'] = e['p1'], e['p2'], e['p3']
    for i, (val, lab) in enumerate(e['facts']):
        d['fv%d' % i], d['fl%d' % i] = val, lab
    for i, cap in enumerate(e['caps']):
        d['cap%d' % i] = cap
    for i, (t, dd) in enumerate(e['plus']):
        d['pt%d' % i], d['pd%d' % i] = t, dd
    for i, t in enumerate(_chambres_en.AMEN_EN):
        d['am%d' % i] = t
    for i, (t, dd) in enumerate(_chambres_en.INCL_EN):
        d['it%d' % i], d['id%d' % i] = t, dd
    for i, slug in enumerate(c['autres']):
        d['om%d' % i] = _chambres_en.EN[slug]['meta']
        d['on%d' % i] = _chambres_en.CHASSIS['pnuit']
    return ','.join('%s:%s' % (k, json.dumps(v, ensure_ascii=False))
                    for k, v in sorted(d.items()))

for c in CHAMBRES:
    pax_opts = ''.join(
        '<option value="%d"%s>%d personne%s</option>' % (i, ' selected' if i == min(2, c['pax']) else '', i, 's' if i > 1 else '')
        for i in range(1, c['pax'] + 1))

    b = [header('#reserver', 'Réserver'), drawer('index.html#chambres'), '''
<div class="wrap head">
  <nav class="crumb" aria-label="Fil d'Ariane">
    <a href="index.html" data-t="c1">Accueil</a> &nbsp;·&nbsp;
    <a href="index.html#chambres" data-t="c2">Chambres &amp; Suites</a> &nbsp;·&nbsp;
    <span>%s</span>
  </nav>
  <div class="head-top">
    <div>
      <span class="eyebrow" data-t="eb0">%s</span>
      <h1>%s</h1>
      <div class="facts">''' % (c['nom'], c['tag'] or 'Chambre', c['nom'])]

    for i, (val, lab) in enumerate(c['facts']):
        b.append('        <span><b data-t="fv%d">%s</b> <span data-t="fl%d">%s</span></span>'
                 % (i, val, i, lab))

    b.append('''      </div>
    </div>
    <div class="head-price"><b>%s</b><span data-t="pnuit">FCFA / nuit</span></div>
  </div>
</div>

<div class="wrap">
  <div class="mosaic%s" id="gl">''' % (fmt(c['prix']), ' court' if len(c['photos']) < 5 else ''))

    for i, (img, alt, cap) in enumerate(c['photos']):
        ld = 'eager' if i == 0 else 'lazy'
        # Rangee incomplete a deux colonnes quand le nombre est pair : la
        # derniere image s'etale plutot que de laisser une case vide.
        cl = ' class="plein"' if (i == len(c['photos']) - 1 and len(c['photos']) % 2 == 0) else ''
        b.append('''    <figure%s><picture><source srcset="img/opt/%s.webp" type="image/webp">
      <img loading="%s" src="img/opt/%s.jpg" data-full="img/opt/%s.jpg" alt="%s"></picture>
      <figcaption data-t="cap%d">%s</figcaption></figure>''' % (cl, img, ld, img, img, alt, i, cap))

    b.append('''  </div>
</div>

<div class="wrap body-grid">
 <div>
  <section class="block reveal">
    <span class="eyebrow" data-t="ebr">La chambre</span>
    <h2 data-t="ttl">%s</h2>
    <p data-t="pa1">%s</p>
    <p data-t="pa2">%s</p>
    <p data-t="pa3">%s</p>
  </section>

  <section class="block reveal">
    <span class="eyebrow" data-t="ebe">Équipements</span>
    <h2 data-t="hae">Dans la chambre</h2>
    <div class="amen">''' % (c['titre'], c['p1'], c['p2'], c['p3']))

    for i, (t, d) in enumerate(c['plus']):
        b.append('      <div class="hi"><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg>'
                 '<span><b data-t="pt%d">%s</b><em data-t="pd%d">%s</em></span></div>'
                 % (ICONE_PLUS, i, t, i, d))
    for i, (t, d) in enumerate(AMEN_BASE):
        b.append('      <div><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg>'
                 '<span data-t="am%d">%s</span></div>' % (d, i, t))

    b.append('''    </div>
  </section>

  <section class="block reveal">
    <span class="eyebrow" data-t="ebi">Inclus</span>
    <h2 data-t="hai">Compris dans le tarif</h2>
    <ul class="incl">''')
    for i, (t, d) in enumerate(INCL):
        b.append('      <li><span class="chk">✓</span><div><b data-t="it%d">%s</b>'
                 '<p data-t="id%d">%s</p></div></li>' % (i, t, i, d))

    b.append('''    </ul>
  </section>

  <section class="block reveal">
    <span class="eyebrow" data-t="ebc">Conditions</span>
    <h2 data-t="hac">Bon à savoir</h2>
    <div class="cond">
      <div><span data-t="cd1">Arrivée</span><span data-t="cd1v">à partir de 14 h 00</span></div>
      <div><span data-t="cd2">Départ</span><span data-t="cd2v">avant 12 h 00</span></div>
      <div><span data-t="cd3">Annulation</span><span data-t="cd3v">gratuite jusqu'à 48 h avant</span></div>
      <div><span data-t="cd4">Acompte</span><span data-t="cd4v">30 %% à la réservation</span></div>
      <div><span data-t="cd5">Animaux</span><span data-t="cd5v">non admis</span></div>
      <div><span data-t="cd6">Paiement</span><span data-t="cd6v">Wave · Orange Money · MTN · carte</span></div>
    </div>
    <p style="margin-top:16px;font-size:13px;color:var(--muted)" data-t="cdn">
      Le détail complet figure sur la page <a href="informations-utiles.html#reserver" style="color:var(--bronze)">Informations utiles</a>.
    </p>
  </section>
 </div>

 <aside class="panel" id="reserver">
  <span class="from" data-t="apd">À partir de</span>
  <div class="rate">%s <span style="font-size:1rem">FCFA</span></div>
  <div class="per" data-t="pern">par nuit, petit-déjeuner inclus</div>

  <form id="bkf">
    <div class="two">
      <div class="pf"><label for="d1" data-t="la1">Arrivée</label><input type="date" id="d1"></div>
      <div class="pf"><label for="d2" data-t="la2">Départ</label><input type="date" id="d2"></div>
    </div>
    <div class="pf"><label for="pax" data-t="lax">Voyageurs</label><select id="pax">%s</select></div>

    <div class="calc">
      <div class="row"><span id="l1">%s FCFA × 2 nuits</span><span id="v1"></span></div>
      <div class="row"><span data-t="rtx">Taxe de séjour</span><span id="v2"></span></div>
      <div class="row"><span data-t="rpd">Petit-déjeuner</span><span style="color:var(--palm)" data-t="rin">Inclus</span></div>
      <div class="total"><span data-t="rtt">Total séjour</span><b id="tt"></b></div>
    </div>

    <button type="submit" class="btn btn-solid" data-t="bkb">Réserver cette chambre</button>
    <div class="avail"><i></i><span data-t="avl">Disponible à ces dates</span></div>
    <p class="helpt" data-t="hlp">Une question&nbsp;? Écrivez-nous sur <a href="https://wa.me/2250546017377" target="_blank" rel="noopener">WhatsApp</a> ou appelez le +225 01 51 52 75 75.</p>
  </form>
 </aside>
</div>

<section class="more">
  <div class="wrap">
    <span class="eyebrow" data-t="ebo">Autres catégories</span>
    <h2 data-t="hao">Si celle-ci est prise</h2>
    <div class="more-grid">''' % (fmt(c['prix']), pax_opts, fmt(c['prix'])))

    for i, slug in enumerate(c['autres']):
        o = PAR_SLUG[slug]
        img = o['photos'][0][0]
        b.append('''      <a class="rcard reveal" href="%s.html">
        <div class="ph"><picture><source srcset="img/opt/%s.webp" type="image/webp">
          <img loading="lazy" src="img/opt/%s.jpg" alt="%s"></picture></div>
        <div><h3>%s</h3><p style="font-size:14px" data-t="om%d">%s</p>
        <div class="p"><b>%s</b><span data-t="on%d">FCFA / nuit</span></div></div>
      </a>''' % (slug, img, img, o['nom'], o['nom'], i, o['meta'], fmt(o['prix']), i))

    b.append('''    </div>
  </div>
</section>

''' + FOOTER + '''

<div class="mobar">
  <div><b id="mb"></b><span data-t="mbs">FCFA · séjour total</span></div>
  <a href="#reserver" class="btn btn-solid" data-t="mbb">Réserver</a>
</div>

<div id="lb" role="dialog" aria-modal="true" aria-label="Photos de la chambre">
  <button class="lb-btn close" aria-label="Fermer">×</button>
  <button class="lb-btn prev" aria-label="Photo précédente">‹</button>
  <img id="lbi" alt="">
  <button class="lb-btn next" aria-label="Photo suivante">›</button>
  <div id="lbc"></div>
</div>''')

    JS = NAV_JS + '''

var RATE=%d, TAX=1500; // taxe de séjour par personne et par nuit
var d1=document.getElementById('d1'),d2=document.getElementById('d2'),pax=document.getElementById('pax');
function iso(d){return new Date(d.getTime()-d.getTimezoneOffset()*6e4).toISOString().slice(0,10)}
d1.value=iso(new Date(Date.now()+864e5));d2.value=iso(new Date(Date.now()+864e5*3));
d1.min=iso(new Date());d2.min=iso(new Date());
function fmt(n){return n.toLocaleString('fr-FR').replace(/ | |,/g,' ')}
/* Le recapitulatif et le selecteur de voyageurs sont ecrits par ce script,
   donc hors de portee de [data-t]. LANG_JS appelle EVN_LANG a chaque
   bascule : c'est le point d'extension prevu pour ce cas. */
var MOTS={fr:{n1:' nuit',nn:' nuits',p1:' personne',pp:' personnes'},
          en:{n1:' night',nn:' nights',p1:' guest',pp:' guests'}};
var LG='fr';
function EVN_LANG(lg){
  LG=MOTS[lg]?lg:'fr';
  [].forEach.call(pax.options,function(o){
    var n=+o.value; o.textContent=n+(n>1?MOTS[LG].pp:MOTS[LG].p1);
  });
  calc();
}
function calc(){
  var a=new Date(d1.value),b=new Date(d2.value);
  var n=Math.round((b-a)/864e5); if(!n||n<1){n=1;d2.value=iso(new Date(a.getTime()+864e5))}
  var p=+pax.value, sejour=RATE*n, taxe=TAX*p*n, total=sejour+taxe;
  document.getElementById('l1').textContent=fmt(RATE)+' FCFA × '+n+(n>1?MOTS[LG].nn:MOTS[LG].n1);
  document.getElementById('v1').textContent=fmt(sejour);
  document.getElementById('v2').textContent=fmt(taxe);
  document.getElementById('tt').textContent=fmt(total);
  document.getElementById('mb').textContent=fmt(total);
}
[d1,d2,pax].forEach(function(e){e.addEventListener('change',calc)});
document.getElementById('bkf').addEventListener('submit',function(e){e.preventDefault();calc();
  var q='?chambre=%s&du='+d1.value+'&au='+d2.value+'&pax='+pax.value;
  location.href='reserver.html'+q;
});
calc();

var figs=[].slice.call(document.querySelectorAll('#gl img')),lb=document.getElementById('lb'),lbi=document.getElementById('lbi'),lbc=document.getElementById('lbc'),gi=0;
function show(i){gi=(i+figs.length)%%figs.length;lbi.src=plein(figs[gi]);lbi.alt=figs[gi].alt;lbc.textContent=figs[gi].alt+'  ·  '+(gi+1)+' / '+figs.length;lb.classList.add('on');document.body.style.overflow='hidden'}
function hideLb(){lb.classList.remove('on');document.body.style.overflow=''}
figs.forEach(function(im,i){im.closest('figure').onclick=function(){show(i)}});
lb.querySelector('.next').onclick=function(e){e.stopPropagation();show(gi+1)};
lb.querySelector('.prev').onclick=function(e){e.stopPropagation();show(gi-1)};
lb.querySelector('.close').onclick=hideLb;
lb.onclick=function(e){if(e.target===lb)hideLb()};
addEventListener('keydown',function(e){if(!lb.classList.contains('on'))return;
 if(e.key==='Escape')hideLb();if(e.key==='ArrowRight')show(gi+1);if(e.key==='ArrowLeft')show(gi-1)});

var EN={''' % (c['prix'], c['slug']) + EN_NAV + _en_dict(c) + '};\n\n' + LANG_JS

    LD = _schema.bloc(
        _schema.chambre(
            c['nom'].replace('&amp;', '&'), c['slug'], c['prix'], c['pax'],
            "%s %s FCFA la nuit, petit-dejeuner et navette aeroport inclus."
            % (c['meta'].replace('&nbsp;', ' '), fmt(c['prix'])),
            [ph[0] for ph in c['photos']],
            equipements=['Climatisation', 'Salle de bain privative', 'Wifi gratuit',
                         'Petit-déjeuner inclus']
                        + [p[0] for p in c['plus']],
            lits={v: k for k, v in c['facts']}.get('lit')),
        _schema.hotel(),
        _schema.fil([('Accueil', 'index'), ('Chambres &amp; Suites', 'chambres'),
                     (c['nom'].replace('&amp;', '&'), None)]))

    mosa = {ph[0]: _sizes_mosaique(i, len(c['photos'])) for i, ph in enumerate(c['photos'])}

    io.open(c['slug'] + '.html', 'w', encoding='utf-8').write(page(
        "%s — Hôtel Evannath, Assinie | %s FCFA la nuit" % (c['nom'], fmt(c['prix'])),
        "%s à l'Hôtel Evannath, Assinie PK 19 : %s. %s FCFA la nuit, petit-déjeuner et navette aéroport inclus."
        % (c['nom'], c['meta'], fmt(c['prix'])),
        c['photos'][0][0], CSS, '\n'.join(b), JS, preload=c['photos'][0][0], slug=c['slug'], jsonld=LD, sizes=mosa))
    print('  %-26s %s FCFA' % (c['slug'] + '.html', fmt(c['prix'])))

print('%d fiches chambres generees' % len(CHAMBRES))
