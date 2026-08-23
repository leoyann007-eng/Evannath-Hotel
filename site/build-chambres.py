# -*- coding: utf-8 -*-
"""Genere les 7 fiches chambres a partir d'un seul gabarit.

Tarifs, capacites et intitules proviennent du catalogue reel de l'hotel
(API WooCommerce de evannathhotel.com). Les conditions de sejour sont
des hypotheses a faire confirmer — voir README.
"""
import io
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV

# slug, nom, prix, capacite, resume, accroche, 3 paragraphes, equipements+, photos
CHAMBRES = [
 dict(slug='chambre-standard', nom='Chambre Standard', prix=67000, pax=2,
   tag='Best-seller', meta='2 personnes · vue jardin',
   facts=[('2','personnes'),('Queen','lit'),('Jardin','vue'),('Inclus','petit-déjeuner')],
   titre="L'essentiel,<br>fait comme il faut",
   p1="C'est la chambre que nous vendons le plus, et celle dont on nous reparle le plus souvent. Un lit queen, la climatisation, une salle d'eau privative, une terrasse partagée qui donne sur le jardin. Rien de superflu, rien qui manque.",
   p2="Elle convient à un couple de passage, à un voyageur d'affaires, à qui vient dormir entre deux journées de lagune. Le petit-déjeuner est compris, comme dans toutes nos catégories.",
   p3="C'est aussi la chambre du Week-End Intense, notre forfait à 155 000 F : deux nuits, deux petits-déjeuners, un apéro, un dîner et une sortie jet ski ou balade lagunaire.",
   plus=[], photos=[('r-standard','La Chambre Standard','La chambre'),
                    ('gal-ch-bureau','Coin bureau et miroir soleil','Le coin bureau'),
                    ('gal-ch-bain','Salle de bain','La salle d\'eau')],
   autres=['deluxe-baldaquin','chambre-mezzanine','suite-anglaise']),

 dict(slug='deluxe-baldaquin', nom='Deluxe · lits à baldaquin', prix=82000, pax=2,
   tag='', meta='2 personnes · baldaquin · coin salon',
   facts=[('2','personnes'),('Baldaquin','lits'),('Salon','coin'),('Jardin','terrasse')],
   titre="Bois sombre<br>et voilages clairs",
   p1="Les lits à baldaquin sont ce que les clients photographient le plus. Bois sombre, voilages blancs, lumière filtrée le matin — la chambre a un caractère que les catégories standard n'ont pas.",
   p2="Un coin salon complète la pièce, et la terrasse ouvre sur le jardin. C'est le premier palier où l'on cesse de dormir dans une chambre pour commencer à y vivre.",
   p3="Quinze mille francs séparent cette chambre de la Standard. C'est le meilleur rapport de toute notre grille.",
   plus=[('Lits à baldaquin','Bois massif et voilages')],
   photos=[('ig-baldaquin','Chambre Deluxe à lits à baldaquin','La chambre'),
           ('gal-ch-salon','Coin salon et plantes','Le coin salon'),
           ('gal-ch-bain','Salle de bain','La salle d\'eau')],
   autres=['chambre-standard','deluxe-superieure','suite-anglaise']),

 dict(slug='deluxe-superieure', nom='Deluxe Supérieure', prix=97000, pax=3,
   tag='Salle à manger privée', meta='3 personnes · textiles wax · salle à manger',
   facts=[('3','personnes'),('Baldaquin','lits'),('Privée','salle à manger'),('Wax','textiles')],
   titre="La Deluxe,<br>en plus généreux",
   p1="Mêmes lits à baldaquin, mais la pièce s'agrandit d'une salle à manger privative. Les textiles wax donnent à la chambre sa couleur — ce sont eux qu'on remarque en entrant.",
   p2="Trois personnes y tiennent sans se gêner. C'est notre choix pour une famille avec un enfant, ou pour un séjour long où l'on aime prendre le petit-déjeuner chez soi.",
   p3="La salle à manger fait la différence pour qui reste plus de trois nuits.",
   plus=[('Salle à manger privative','Pour trois couverts'),('Textiles wax','Choisis chez des artisans locaux')],
   photos=[('r-wax','Deluxe Supérieure, textiles wax','La chambre'),
           ('gal-ch-wax','Détail des textiles wax','Les textiles'),
           ('gal-ch-salon','Coin salon','Le salon')],
   autres=['deluxe-baldaquin','mezzanine-superieure','suite-arabe']),

 dict(slug='suite-anglaise', nom='Suite Anglaise', prix=107000, pax=2,
   tag='Vue lagune', meta='2 personnes · vue lagune · le meilleur couchant',
   facts=[('2','personnes'),('Lagune','vue'),('Salon','séparé'),('Couchant','exposition')],
   titre="La vue,<br>puis le couchant",
   p1="C'est la première catégorie qui donne directement sur la lagune Aby et sur la piscine. L'exposition fait le reste : à partir de dix-sept heures, la lumière entre par la baie et ne repart plus.",
   p2="L'élégance y est feutrée — matériaux sobres, salon séparé, rien qui crie. La suite plaît à ceux qui viennent pour le calme plutôt que pour la fête.",
   p3="Si vous ne deviez retenir qu'une chose : c'est d'ici qu'on voit le meilleur coucher de soleil du domaine.",
   plus=[('Vue directe sur la lagune','Et sur la piscine'),('Salon séparé','Coin salon indépendant')],
   photos=[('r-anglaise','La Suite Anglaise','La suite'),
           ('r-anglaise2','Le salon et la salle à manger de la suite','Le salon'),
           ('gal-ch-bain','Salle de bain','La salle de bain')],
   autres=['deluxe-superieure','mezzanine-superieure','suite-arabe']),

 dict(slug='chambre-mezzanine', nom='Chambre en Mezzanine', prix=127000, pax=2,
   tag='', meta='2 personnes · duplex · sous charpente',
   facts=[('2','personnes'),('Duplex','volume'),('Bois','escalier'),('Charpente','sous')],
   titre="Un volume<br>sous charpente",
   p1="La mezzanine est un duplex : on vit en bas, on dort en haut. L'escalier de bois monte vers un coin nuit surélevé, sous la charpente apparente.",
   p2="C'est la chambre des jeunes couples et de ceux qui aiment les volumes. Le plafond ouvert change complètement la sensation par rapport à une chambre classique.",
   p3="Deux personnes, pas plus — la mezzanine se vit à deux ou pas du tout.",
   plus=[('Coin nuit surélevé','Accessible par escalier de bois'),('Charpente apparente','Plafond ouvert')],
   photos=[('r-mezz2','Chambre en Mezzanine','La chambre'),
           ('gal-ch-mezz','L\'escalier de la mezzanine','L\'escalier'),
           ('gal-ch-bain','Salle de bain','La salle d\'eau')],
   autres=['mezzanine-superieure','suite-anglaise','deluxe-superieure']),

 dict(slug='mezzanine-superieure', nom='Mezzanine Supérieure', prix=142000, pax=4,
   tag='Terrasse privative', meta='4 personnes · terrasse privative · coin salon',
   facts=[('4','personnes'),('Duplex','volume'),('Privative','terrasse'),('Salon','complet')],
   titre="La mezzanine,<br>en plus grand",
   p1="Même principe, plus d'espace : un coin salon complet en bas, des équipements renforcés, et surtout une terrasse privative qui n'existe dans aucune autre catégorie à ce tarif.",
   p2="Quatre personnes y logent confortablement — c'est notre chambre familiale la plus demandée après la Suite Arabe.",
   p3="C'est aussi la chambre du forfait Lune de Miel à 340 000 F : deux nuits, la chambre décorée avant votre arrivée, les petits-déjeuners compris.",
   plus=[('Terrasse privative','À vous seuls'),('Coin salon complet','Séparé de l\'espace nuit')],
   photos=[('r-mezzanine','Mezzanine Supérieure','La chambre'),
           ('gal-ch-mezz','L\'escalier et le coin nuit','La mezzanine'),
           ('gal-ch-salon','Le coin salon','Le salon')],
   autres=['chambre-mezzanine','suite-arabe','suite-anglaise']),

 dict(slug='suite-arabe', nom='Suite Arabe', prix=280000, pax=6,
   tag='Signature', meta='6 personnes · 2 chambres · décor arabo-andalou',
   facts=[('2','chambres'),('6','personnes'),('Salon','privatif'),('Arabo-andalou','décor')],
   titre="Deux chambres,<br>un salon, un service dédié",
   p1="C'est la plus grande de nos sept catégories, et la seule à proposer deux chambres séparées. Le décor arabo-andalou — bois sculpté, arcades, textiles brodés — a été composé pièce par pièce avec des artisans locaux, dans l'esprit qui guide tout l'établissement.",
   p2="Deux couples, une famille avec enfants grands, ou un groupe d'amis : la suite absorbe six personnes sans que personne ne se marche dessus. Le salon privatif sert de pièce de vie commune, et chaque chambre garde sa salle d'eau.",
   p3="C'est la catégorie la plus demandée pour les lunes de miel et les anniversaires. Elle part vite en saison sèche — de décembre à mars, prévoyez plusieurs semaines à l'avance.",
   plus=[('Deux chambres séparées','Chacune avec sa salle d\'eau'),('Salon privatif','Pièce de vie commune'),('Service dédié','Sur demande')],
   photos=[('sa-main','La Suite Arabe','La suite'),
           ('sa-chambre2','La seconde chambre, textiles wax et accès balcon','La seconde chambre'),
           ('sa-bain','Salle de bain et miroir soleil','La salle de bain'),
           ('sa-salon','Coin salon et espace de repos','Le salon'),
           ('sa-terrasse','Terrasse ombragée','La terrasse')],
   autres=['mezzanine-superieure','suite-anglaise','deluxe-superieure']),
]

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

def fmt(n):
    return format(n, ',').replace(',', ' ')

for c in CHAMBRES:
    pax_opts = ''.join(
        '<option value="%d"%s>%d personne%s</option>' % (i, ' selected' if i == min(2, c['pax']) else '', i, 's' if i > 1 else '')
        for i in range(1, c['pax'] + 1))

    b = [header('#reserver', 'Réserver'), drawer('index.html#chambres'), '''
<div class="wrap head">
  <nav class="crumb" aria-label="Fil d'Ariane">
    <a href="index.html">Accueil</a> &nbsp;·&nbsp;
    <a href="index.html#chambres">Chambres &amp; Suites</a> &nbsp;·&nbsp;
    <span>%s</span>
  </nav>
  <div class="head-top">
    <div>
      <span class="eyebrow">%s</span>
      <h1>%s</h1>
      <div class="facts">''' % (c['nom'], c['tag'] or 'Chambre', c['nom'])]

    for val, lab in c['facts']:
        b.append('        <span><b>%s</b> %s</span>' % (val, lab))

    b.append('''      </div>
    </div>
    <div class="head-price"><b>%s</b><span>FCFA / nuit</span></div>
  </div>
</div>

<div class="wrap">
  <div class="mosaic" id="gl">''' % fmt(c['prix']))

    for i, (img, alt, cap) in enumerate(c['photos']):
        ld = 'eager' if i == 0 else 'lazy'
        b.append('''    <figure><picture><source srcset="img/opt/%s.webp" type="image/webp">
      <img loading="%s" src="img/opt/%s.jpg" data-full="img/opt/%s.jpg" alt="%s"></picture>
      <figcaption>%s</figcaption></figure>''' % (img, ld, img, img, alt, cap))

    b.append('''  </div>
</div>

<div class="wrap body-grid">
 <div>
  <section class="block reveal">
    <span class="eyebrow">La chambre</span>
    <h2>%s</h2>
    <p>%s</p>
    <p>%s</p>
    <p>%s</p>
  </section>

  <section class="block reveal">
    <span class="eyebrow">Équipements</span>
    <h2>Dans la chambre</h2>
    <div class="amen">''' % (c['titre'], c['p1'], c['p2'], c['p3']))

    for t, d in c['plus']:
        b.append('      <div class="hi"><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg><span><b>%s</b><em>%s</em></span></div>' % (ICONE_PLUS, t, d))
    for t, d in AMEN_BASE:
        b.append('      <div><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg><span>%s</span></div>' % (d, t))

    b.append('''    </div>
  </section>

  <section class="block reveal">
    <span class="eyebrow">Inclus</span>
    <h2>Compris dans le tarif</h2>
    <ul class="incl">''')
    for t, d in INCL:
        b.append('      <li><span class="chk">✓</span><div><b>%s</b><p>%s</p></div></li>' % (t, d))

    b.append('''    </ul>
  </section>

  <section class="block reveal">
    <span class="eyebrow">Conditions</span>
    <h2>Bon à savoir</h2>
    <div class="cond">
      <div><span>Arrivée</span><span>à partir de 14 h 00</span></div>
      <div><span>Départ</span><span>avant 12 h 00</span></div>
      <div><span>Annulation</span><span>gratuite jusqu'à 48 h avant</span></div>
      <div><span>Acompte</span><span>30 %% à la réservation</span></div>
      <div><span>Animaux</span><span>non admis</span></div>
      <div><span>Paiement</span><span>Wave · Orange Money · MTN · carte</span></div>
    </div>
    <p style="margin-top:16px;font-size:13px;color:var(--muted)">
      Le détail complet figure sur la page <a href="informations-utiles.html#reserver" style="color:var(--bronze)">Informations utiles</a>.
    </p>
  </section>
 </div>

 <aside class="panel" id="reserver">
  <span class="from">À partir de</span>
  <div class="rate">%s <span style="font-size:1rem">FCFA</span></div>
  <div class="per">par nuit, petit-déjeuner inclus</div>

  <form id="bkf">
    <div class="two">
      <div class="pf"><label for="d1">Arrivée</label><input type="date" id="d1"></div>
      <div class="pf"><label for="d2">Départ</label><input type="date" id="d2"></div>
    </div>
    <div class="pf"><label for="pax">Voyageurs</label><select id="pax">%s</select></div>

    <div class="calc">
      <div class="row"><span id="l1">%s FCFA × 2 nuits</span><span id="v1"></span></div>
      <div class="row"><span>Taxe de séjour</span><span id="v2"></span></div>
      <div class="row"><span>Petit-déjeuner</span><span style="color:var(--palm)">Inclus</span></div>
      <div class="total"><span>Total séjour</span><b id="tt"></b></div>
    </div>

    <button type="submit" class="btn btn-solid">Réserver cette chambre</button>
    <div class="avail"><i></i><span>Disponible à ces dates</span></div>
    <p class="helpt">Une question&nbsp;? Écrivez-nous sur <a href="https://wa.me/2250546017377" target="_blank" rel="noopener">WhatsApp</a> ou appelez le +225 01 51 52 75 75.</p>
  </form>
 </aside>
</div>

<section class="more">
  <div class="wrap">
    <span class="eyebrow">Autres catégories</span>
    <h2>Si celle-ci est prise</h2>
    <div class="more-grid">''' % (fmt(c['prix']), pax_opts, fmt(c['prix'])))

    for slug in c['autres']:
        o = PAR_SLUG[slug]
        img = o['photos'][0][0]
        b.append('''      <a class="rcard reveal" href="%s.html">
        <div class="ph"><picture><source srcset="img/opt/%s.webp" type="image/webp">
          <img loading="lazy" src="img/opt/%s.jpg" alt="%s"></picture></div>
        <div><h3>%s</h3><p style="font-size:14px">%s</p>
        <div class="p"><b>%s</b><span>FCFA / nuit</span></div></div>
      </a>''' % (slug, img, img, o['nom'], o['nom'], o['meta'], fmt(o['prix'])))

    b.append('''    </div>
  </div>
</section>

''' + FOOTER + '''

<div class="mobar">
  <div><b id="mb"></b><span>FCFA · séjour total</span></div>
  <a href="#reserver" class="btn btn-solid">Réserver</a>
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
  var q='?chambre=%s&du='+d1.value+'&au='+d2.value+'&pax='+pax.value;
  location.href='reserver.html'+q;
});
calc();

var figs=[].slice.call(document.querySelectorAll('#gl img')),lb=document.getElementById('lb'),lbi=document.getElementById('lbi'),lbc=document.getElementById('lbc'),gi=0;
function show(i){gi=(i+figs.length)%%figs.length;lbi.src=figs[gi].dataset.full||figs[gi].src;lbi.alt=figs[gi].alt;lbc.textContent=figs[gi].alt+'  ·  '+(gi+1)+' / '+figs.length;lb.classList.add('on');document.body.style.overflow='hidden'}
function hideLb(){lb.classList.remove('on');document.body.style.overflow=''}
figs.forEach(function(im,i){im.closest('figure').onclick=function(){show(i)}});
lb.querySelector('.next').onclick=function(e){e.stopPropagation();show(gi+1)};
lb.querySelector('.prev').onclick=function(e){e.stopPropagation();show(gi-1)};
lb.querySelector('.close').onclick=hideLb;
lb.onclick=function(e){if(e.target===lb)hideLb()};
addEventListener('keydown',function(e){if(!lb.classList.contains('on'))return;
 if(e.key==='Escape')hideLb();if(e.key==='ArrowRight')show(gi+1);if(e.key==='ArrowLeft')show(gi-1)});

var EN={''' % (c['prix'], c['slug']) + EN_NAV + 'cta:"Book"};\n\n' + LANG_JS

    io.open(c['slug'] + '.html', 'w', encoding='utf-8').write(page(
        "%s — Hôtel Evannath, Assinie | %s FCFA la nuit" % (c['nom'], fmt(c['prix'])),
        "%s à l'Hôtel Evannath, Assinie PK 19 : %s. %s FCFA la nuit, petit-déjeuner et navette aéroport inclus."
        % (c['nom'], c['meta'], fmt(c['prix'])),
        c['photos'][0][0], CSS, '\n'.join(b), JS, preload=c['photos'][0][0]))
    print('  %-26s %s FCFA' % (c['slug'] + '.html', fmt(c['prix'])))

print('%d fiches chambres generees' % len(CHAMBRES))
