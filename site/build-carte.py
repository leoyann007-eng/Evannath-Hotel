# -*- coding: utf-8 -*-
"""Génère carte.html à partir de la carte réelle de l'Hôtel Evannath.
Source : https://evannathhotel.com/cartes/ (relevé le 20/08/2026).
Les fautes de frappe du site d'origine sont corrigées ici ; les deux tarifs
manifestement erronés (Tajine affiché « FREE », Casserole à 95 000) sont
remplacés par « Nous consulter » plutôt qu'inventés.
"""
import io
import _schema
from _chrome import responsive, dimensionner, versionner, secours, liens_nav, EN_NAV, EN_SECOURS, CONF_TITRE, CONF_GESTE, CONF_VERBE, WA, WA_TEXTE, MAIL, ENVOI_JS, NAV_JS, TOKENS, HEAD_CSS, FOOTER_CSS, LANG_JS

CUISINE = [
 ("Nos entrées", [
  ("Salade d'avocat aux fruits de mer, chips de banane","6 000","Laitue, chips de banane, avocat, crevette, oignon, olive noire, sauce aurore"),
  ("Salade César Babi","7 000","Salade, œuf de caille, parmesan, croûton, poulet fumé effiloché"),
  ("Salade croquante d'Assinie, maquereau fumé","5 000","Crudités, œuf dur, maïs, gingembre séché, maquereau fumé, vinaigrette maison"),
  ("Salade de la ferme +","5 000","Laitue, jambon blanc, pomme de terre, concombre, œuf poché, tomate, fromage"),
  ("Salade exotique, poulet fumé et œuf poché","4 500","Œuf poché, carotte, haricot vert, concombre, tomate cerise, poulet fumé"),
  ("Salade Evannath, poisson magnin sec","4 500","Laitue, concombre, magnin sec, tomate, carotte, haricot vert, thon, parmesan"),
  ("Salade de la ferme","4 500","Laitue, jambon blanc, pomme de terre, concombre, œuf poché, tomate, fromage"),
  ("Bouillie de couscous","4 500","Couscous, beurre, lait, sucre, miel, sucre vanillé"),
 ]),
 ("Fruits de mer &amp; poissons", [
  ("Tagliatelles aux fruits de mer","15 000",""),
  ("Filet de capitaine en papillote","14 000","Riz au curcuma"),
  ("Gambas flambées façon tikka","14 000","Gratin de pommes"),
  ("Môgô braisé aux petits légumes","14 000","Alloco ou attiéké"),
  ("Casserole de la pêche bassamoise","—","Attiéké huile rouge · Nous consulter"),
 ]),
 ("Dégustations familiales <em>· 5 personnes</em>", [
  ("Thiéboudiène, poisson à la sénégalaise","50 000",""),
  ("Mafé au bœuf fumé","45 000","Riz étuvé"),
  ("Soupe de queue de bœuf au gnangnan","45 000","Riz étuvé"),
  ("Coulant de palmier au poulet fumé","40 000","Foutou de banane plantain"),
  ("Gibier sauce gouagouassou","40 000","Foutou ou riz étuvé"),
  ("Duo patate-épinard, queue de bœuf fumée","32 000","Riz étuvé"),
  ("Soumara lafri au poulet","30 000","Riz"),
  ("Akpessi de poisson fumé, bâton de banane aux fleurs de piment","30 000",""),
  ("Tajine d'agneau aux prunes","—","Couscous · digestif offert · Nous consulter"),
 ]),
 ("Viandes blanches", [
  ("Cordon bleu Evannath","14 000","Féroce de manioc, sauce tartare"),
  ("Kedjenou de poulet africain à la citronnelle","12 000","Attiéké"),
  ("Crème de curry au poulet, gingembre séché","12 000","Riz persillé"),
  ("Brochette de poulet marinée au soumara, cuite au feu de bois","10 000","Igname frite maison, parmesane"),
  ("Selim de poulet enrobé de kankankan au feu de bois","9 000","Alloco"),
 ]),
 ("Viandes rouges", [
  ("Fondant de souris d'agneau au miel de Tafiré","21 000","Pommes grenaille"),
  ("Filet de bœuf au jus corsé de cacao","15 000","Écrasé de patate douce"),
  ("Dibi d'agneau grillé à la guinéenne","15 000","Moutarde, oignon, grosses frites"),
  ("T-bone grillé aux trois moutardes","15 000","Légumes grillés"),
 ]),
 ("Pizzas", [
  ("Tropicale","10 000",""),("Royale","10 000",""),
  ("Parmentière","10 000",""),("Calabraise","10 000",""),
 ]),
 ("Desserts", [
  ("Crème de baobab","6 000",""),
  ("Panna cotta fruitée parfumée","5 500","Bissap, passion, orange"),
  ("Fondant au chocolat au lait de Daloa","5 000",""),
  ("Crème brûlée à la citronnelle","4 500",""),
  ("Dêguê de couscous au miel","4 500",""),
  ("Mousse au chocolat noir et basilic","3 500",""),
  ("Parfait au chocolat","3 500",""),
  ("Assiette de fruits","3 500",""),
  ("Tarte aux fruits","3 500",""),
  ("Coupes de glaces","3 000",""),
  ("Thé Evannath","2 000",""),
 ]),
]

BOISSONS = [
 ("Cocktails signatures", [
  ("The Fimbu King","12 000","Gingembre, garcinia kola, miel, gin, triple sec, citron"),
  ("Le Sensationnel","12 000","Citron, verveine citronnelle, cannelle, gingembre, kiwi, menthe, rhum, triple sec"),
 ]),
 ("Cocktails avec alcool", [
  ("Le Kréol","8 500","Mangue, citron, gingembre, rhum blanc, rhum ambré"),
  ("Exotic Cosmo","8 500","Cranberry, maracuja, goyave, vanille, vodka"),
  ("Mojito","8 500","Citron, menthe, rhum, sucre de canne, eau gazeuse"),
  ("White Lady","8 500","Gin, triple sec, citron, sirop de canne, blanc d'œuf"),
  ("Diamant Éternel","8 500","Grenadine, banane, lait de coco, goyave, citron"),
  ("Tarzan","8 500","Gin, campari, ananas, citron, soda"),
  ("Manguo Love","8 500","Mangue, goyave, rhum blanc"),
  ("Vanilla Lover","8 500","Vodka, goyave, orange, mangue, vanille"),
  ("Southside","8 500","Gin, basilic frais, citron vert, sirop de canne"),
  ("Epi Sour","8 500","Ananas, orange, passion, kiwi, sirop de fraise, vanille, rhum"),
  ("Evan Tropic","8 500","Pamplemousse, orange, vanille, vodka"),
  ("Blue Hawaii","8 500","Vodka, rhum, curaçao, ananas, limonade"),
 ]),
 ("Cocktails sans alcool", [
  ("Fraîcheur Evannath","6 000","Menthe fraîche, concombre, limonade"),
  ("Exotique","6 000","Mangue, goyave, citron"),
  ("Tropical Breeze","6 000","Goyave, orange, banane"),
  ("The Detox","6 000","Concombre, citron vert, pamplemousse, menthe fraîche, fenouil"),
  ("Virgin Colada","6 000","Jus d'ananas, lait de coco, citron, sucre vanillé"),
  ("Passionné Sour","6 000","Jus de passion, orange, ananas, pêche, curaçao bleu"),
  ("Florida","6 000","Jus d'orange, sirop de grenadine, citron, ananas"),
  ("The Green","6 000","Sirop de kiwi, citron, menthe, limonade"),
  ("Devil's Kiss","6 000","Goyave, framboise, citron, feuilles de coriandre"),
  ("Diamant Éternel","6 000","Grenadine, banane, lait de coco, goyave, citron"),
  ("Sunset Mocktail","6 000","Pastèque, orange ou clémentine, feuilles de menthe, sprite"),
  ("Banana Kiss","6 000","Banane, mangue, maracuja"),
 ]),
 ("Spiritueux", [
  ("Blue Label","30 000",""),
  ("Whisky","10 000","Double Black, Chivas 15 ans, Glenfiddich 12 ans, Gentleman Jack"),
  ("Macallan 12 ans","10 000",""),
  ("Whisky","7 000","Ballantine's 17 ans, Chivas Extra"),
  ("Whisky","5 000","Clan, Red Label, Black Label, Jack Daniel's N°7, Chivas 12 ans, J&amp;B, Jack Honey"),
  ("Gin","4 000","Bombay Sapphire, Citadelle Jardin d'Été, Hendrick's"),
  ("Téquila","1 500","Camino, Olmeca blanco"),
  ("Vodka","1 000","Absolut, Belvedere"),
 ]),
 ("Digestifs", [
  ("Hennessy XXO","30 000",""),
  ("Grand Marnier, Cointreau, Godet N°1, Hennessy VS / VSOP","10 000",""),
  ("Malibu, Get 27, Get 31, Calvados Père Magloire, poire ou mirabelle, limoncello","5 000",""),
  ("Rhum arrangé maison","3 000",""),
 ]),
 ("Apéritifs &amp; bières", [
  ("Apérol, Baileys, Campari","4 000","Martini blanc, rouge ou rosé, porto, Pastis 51, Ricard"),
  ("Bières","2 000","Beaufort, Bock, Castel, Desperados, Heineken, Guinness, Tequila, Racine"),
 ]),
 ("Sans alcool", [
  ("Red Bull","2 500",""),
  ("San Bitter","2 000",""),
  ("Jus nature","2 000",""),
  ("Orangina, Cody's Energy, autres","1 500",""),
  ("Sodas","1 000","Bavaria, Coca-Cola, Sprite, Youki Pomme, Fanta, Moka Café, Coca Zéro"),
 ]),
 ("Boissons chaudes", [
  ("Nespresso","2 000",""),("Café","1 500",""),("Thé","1 000",""),
 ]),
]

SPA = [
 ("Massages du corps", [
  ("Massage thérapeutique aux pierres chauffantes","25 000","50 min"),
  ("Grand rituel corps de l'Orient, argan divin","25 000","1 h 30"),
  ("Massage sublime de Polynésie, lâcher-prise","15 000","50 min"),
  ("Massage relaxant sur mesure aux eucalyptus","15 000","50 min"),
  ("Massage détente et bien-être au jasmin","10 000","20 min"),
  ("Massage relaxant de l'arrière du corps","10 000","20 min"),
  ("Massage délassant des jambes, fraîcheur et légèreté","5 000","20 min"),
 ]),
 ("Soins du visage", [
  ("Soin massage fleurs d'Assinie, pureté et éclat","5 000","20 min"),
  ("Soin massage aux 5 fleurs d'Assinie, hydratant et repulpant","5 000","30 min"),
  ("Soin Ko-Bi-Do, jeunesse et éclat","5 000","20 min"),
 ]),
 ("Gommages &amp; sauna", [
  ("Sauna, fitness et massage","50 000","2 h"),
  ("Soin massage aux 5 fleurs d'Assinie, hydratant et repulpant","15 000","20 min"),
  ("Gommage au savon noir africain, peau douce et satinée","15 000","20 min"),
 ]),
 ("Onglerie", [
  ("Soin fortifiant et embellissement des ongles naturels","5 000",""),
  ("Renfort d'ongles naturels, gainage transparent","5 000",""),
  ("Rallongement, extensions sans capsules","5 000",""),
  ("Pose de vernis","2 500",""),
 ]),
 ("Épilation", [
  ("Création de ligne de sourcil","15 000",""),
  ("Sourcil","2 000",""),
  ("Lèvre ou menton","2 000",""),
  ("Pose de faux cils naturels","2 000",""),
  ("Jambe entière","2 000",""),
 ]),
]

def items(rows):
    out=[]
    for nom,prix,desc in rows:
        d = '<em>%s</em>' % desc if desc else ''
        p = prix if prix != '—' else '<i>Nous consulter</i>'
        out.append('<li><div><b>%s</b>%s</div><span>%s</span></li>' % (nom,d,p))
    return '\n        '.join(out)

def sections(groups, pref):
    out=[]
    for i,(titre,rows) in enumerate(groups):
        out.append(
 '''      <section class="grp" id="%s%d">
        <h3>%s</h3>
        <ul class="menu-list">
        %s
        </ul>
      </section>''' % (pref,i,titre,items(rows)))
    return '\n'.join(out)

def anchors(groups,pref):
    return '\n        '.join(
      '<a href="#%s%d">%s</a>' % (pref,i,t.replace('<em>','').replace('</em>',''))
      for i,(t,_) in enumerate(groups))

total = sum(len(r) for _,r in CUISINE)+sum(len(r) for _,r in BOISSONS)
total_spa = sum(len(r) for _,r in SPA)

HTML = io.open('carte-template.html',encoding='utf-8').read()
HTML = (HTML
  .replace('{{CUISINE}}',sections(CUISINE,'c'))
  .replace('{{BOISSONS}}',sections(BOISSONS,'b'))
  .replace('{{WA}}', WA).replace('{{NAV_LINKS}}', liens_nav('carte.html')).replace('{{EN_NAV}}', EN_NAV).replace('{{WA_TEXTE}}', WA_TEXTE).replace('{{SECOURS}}', secours('sec')).replace('{{EN_SECOURS}}', EN_SECOURS).replace('{{CG}}', (CONF_GESTE or '').replace("'", "\\'")).replace('{{CV}}', CONF_VERBE).replace('{{CT}}', CONF_TITRE or 'Table demand\u00e9e').replace('{{ENVOI}}', ENVOI_JS).replace('{{NAV_JS}}', NAV_JS).replace('{{TOKENS}}', TOKENS).replace('{{LANG_JS}}', LANG_JS).replace('{{HEAD_CSS}}', HEAD_CSS).replace('{{FOOTER_CSS}}', FOOTER_CSS)
  .replace('{{TOTAL}}',str(total))
  .replace('{{LD}}', _schema.bloc(
      _schema.restaurant(nb_plats=total),
      _schema.hotel(),
      _schema.fil([('Accueil','index'),('La table',None)]))))
# En dernier : le JSON-LD injecte plus haut porte lui aussi l'adresse.
io.open('carte.html','w',encoding='utf-8').write(
    versionner(responsive(dimensionner(HTML), hero='gal-lag-nuit')).replace('{{MAIL}}', MAIL))
print('carte.html :', total, 'articles')

SPAH = io.open('spa-template.html',encoding='utf-8').read()
SPAH = (SPAH.replace('{{SPA}}',sections(SPA,'s')).replace('{{WA}}', WA).replace('{{NAV_LINKS}}', liens_nav('spa.html')).replace('{{EN_NAV}}', EN_NAV).replace('{{WA_TEXTE}}', WA_TEXTE).replace('{{SECOURS}}', secours('sec')).replace('{{EN_SECOURS}}', EN_SECOURS).replace('{{CG}}', (CONF_GESTE or '').replace("'", "\\'")).replace('{{CV}}', CONF_VERBE).replace('{{CT}}', CONF_TITRE or 'Cr\u00e9neau demand\u00e9').replace('{{ENVOI}}', ENVOI_JS).replace('{{NAV_JS}}', NAV_JS).replace('{{TOKENS}}', TOKENS).replace('{{LANG_JS}}', LANG_JS).replace('{{HEAD_CSS}}', HEAD_CSS).replace('{{FOOTER_CSS}}', FOOTER_CSS).replace('{{TOTAL}}',str(total_spa))
  .replace('{{LD}}', _schema.bloc(
      _schema.service('Spa et soins du corps',
                      "Massages, gommages, soins du visage, sauna et onglerie au spa de l'Hôtel Evannath, "
                      "Assinie PK 19. %d soins, sur rendez-vous." % total_spa,
                      'spa', image='gal-spa-couchant'),
      _schema.hotel(),
      _schema.fil([('Accueil','index'),('Le spa',None)]))))
io.open('spa.html','w',encoding='utf-8').write(
    versionner(responsive(dimensionner(SPAH), hero='gal-spa-couchant')).replace('{{MAIL}}', MAIL))
print('spa.html   :', total_spa, 'soins')
