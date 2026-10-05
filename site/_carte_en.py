# -*- coding: utf-8 -*-
"""Version anglaise de La table et du spa.

Tenue a part de build-carte.py, comme _chambres_en.py pour les chambres : le
francais reste la source, et ce fichier se relit sans traverser du code.

Une seule table, du francais vers l'anglais. Les noms propres et les noms de
plats ivoiriens (attieke, alloco, kedjenou, foutou...) restent tels quels :
c'est ce qu'un voyageur lira sur place, et ce qu'il commandera. Un texte
absent d'ici reste en francais — un nom de cocktail, une marque.

Registre : celui d'une carte de restaurant, pas d'une traduction mot a mot.
"""

TRAD = {
 # ── Les rubriques ───────────────────────────────────────────────────────
 "Nos entrées": "Starters",
 "Fruits de mer &amp; poissons": "Seafood &amp; fish",
 "Dégustations familiales <em>· 5 personnes</em>": "Family sharing dishes <em>· 5 people</em>",
 "Dégustations familiales": "Family sharing dishes",
 "Viandes blanches": "Poultry",
 "Viandes rouges": "Red meat",
 "Cocktails signatures": "Signature cocktails",
 "Cocktails avec alcool": "Cocktails",
 "Cocktails sans alcool": "Alcohol-free cocktails",
 "Spiritueux": "Spirits",
 "Apéritifs &amp; bières": "Aperitifs &amp; beers",
 "Sans alcool": "Soft drinks",
 "Boissons chaudes": "Hot drinks",
 "Massages du corps": "Body massages",
 "Soins du visage": "Facials",
 "Gommages &amp; sauna": "Scrubs &amp; sauna",
 "Onglerie": "Nails",
 "Épilation": "Waxing",
 "Nous consulter": "Please ask",
 "Offert": "Complimentary",

 # ── Les entrees ─────────────────────────────────────────────────────────
 "Salade d'avocat aux fruits de mer, chips de banane": "Avocado and seafood salad, plantain chips",
 "Laitue, chips de banane, avocat, crevette, oignon, olive noire, sauce aurore":
   "Lettuce, plantain chips, avocado, prawns, onion, black olives, aurore sauce",
 "Salade César Babi": "Babi Caesar salad",
 "Salade, œuf de caille, parmesan, croûton, poulet fumé effiloché":
   "Lettuce, quail egg, parmesan, croutons, pulled smoked chicken",
 "Salade croquante d'Assinie, maquereau fumé": "Assinie crunchy salad, smoked mackerel",
 "Crudités, œuf dur, maïs, gingembre séché, maquereau fumé, vinaigrette maison":
   "Raw vegetables, hard-boiled egg, sweetcorn, dried ginger, smoked mackerel, house dressing",
 "Salade de la ferme +": "Farmhouse salad +",
 "Salade de la ferme": "Farmhouse salad",
 "Laitue, jambon blanc, pomme de terre, concombre, œuf poché, tomate, fromage":
   "Lettuce, ham, potato, cucumber, poached egg, tomato, cheese",
 "Salade exotique, poulet fumé et œuf poché": "Exotic salad, smoked chicken and poached egg",
 "Œuf poché, carotte, haricot vert, concombre, tomate cerise, poulet fumé":
   "Poached egg, carrot, green beans, cucumber, cherry tomatoes, smoked chicken",
 "Salade Evannath, poisson magnin sec": "Evannath salad, dried magnin fish",
 "Laitue, concombre, magnin sec, tomate, carotte, haricot vert, thon, parmesan":
   "Lettuce, cucumber, dried magnin, tomato, carrot, green beans, tuna, parmesan",
 "Bouillie de couscous": "Couscous porridge",
 "Couscous, beurre, lait, sucre, miel, sucre vanillé": "Couscous, butter, milk, sugar, honey, vanilla sugar",

 # ── Fruits de mer et poissons ───────────────────────────────────────────
 "Tagliatelles aux fruits de mer": "Seafood tagliatelle",
 "Filet de capitaine en papillote": "Capitaine fillet en papillote",
 "Riz au curcuma": "Turmeric rice",
 "Gambas flambées façon tikka": "Flambéed king prawns, tikka style",
 "Gratin de pommes": "Potato gratin",
 "Môgô braisé aux petits légumes": "Braised môgô with vegetables",
 "Alloco ou attiéké": "Alloco or attiéké",
 "Casserole de la pêche bassamoise": "Grand-Bassam fisherman's casserole",
 "Attiéké huile rouge": "Attiéké with red palm oil",

 # ── Degustations familiales ─────────────────────────────────────────────
 "Thiéboudiène, poisson à la sénégalaise": "Thiéboudiène, Senegalese-style fish",
 "Mafé au bœuf fumé": "Smoked beef mafé",
 "Riz étuvé": "Steamed rice",
 "Soupe de queue de bœuf au gnangnan": "Oxtail soup with gnangnan",
 "Coulant de palmier au poulet fumé": "Palm nut sauce with smoked chicken",
 "Foutou de banane plantain": "Plantain foutou",
 "Gibier sauce gouagouassou": "Game in gouagouassou sauce",
 "Foutou ou riz étuvé": "Foutou or steamed rice",
 "Duo patate-épinard, queue de bœuf fumée": "Sweet potato and spinach duo, smoked oxtail",
 "Soumara lafri au poulet": "Soumara lafri with chicken",
 "Riz": "Rice",
 "Akpessi de poisson fumé, bâton de banane aux fleurs de piment":
   "Smoked fish akpessi, plantain sticks with chilli flowers",
 "Tajine d'agneau aux prunes": "Lamb tagine with prunes",
 "Couscous · digestif offert": "Couscous · complimentary digestif",

 # ── Viandes ─────────────────────────────────────────────────────────────
 "Cordon bleu Evannath": "Evannath cordon bleu",
 "Féroce de manioc, sauce tartare": "Cassava féroce, tartare sauce",
 "Kedjenou de poulet africain à la citronnelle": "African chicken kedjenou with lemongrass",
 "Crème de curry au poulet, gingembre séché": "Creamy chicken curry, dried ginger",
 "Riz persillé": "Parsley rice",
 "Brochette de poulet marinée au soumara, cuite au feu de bois": "Soumara-marinated chicken skewer, wood-fired",
 "Igname frite maison, parmesane": "Homemade yam fries, parmesan",
 "Selim de poulet enrobé de kankankan au feu de bois": "Wood-fired chicken selim in kankankan spices",
 "Fondant de souris d'agneau au miel de Tafiré": "Slow-cooked lamb shank with Tafiré honey",
 "Pommes grenaille": "Baby potatoes",
 "Filet de bœuf au jus corsé de cacao": "Beef fillet, rich cocoa jus",
 "Écrasé de patate douce": "Crushed sweet potato",
 "Dibi d'agneau grillé à la guinéenne": "Guinean-style grilled lamb dibi",
 "Moutarde, oignon, grosses frites": "Mustard, onion, thick-cut chips",
 "T-bone grillé aux trois moutardes": "Grilled T-bone, three mustards",
 "Légumes grillés": "Grilled vegetables",

 # ── Pizzas et desserts ──────────────────────────────────────────────────
 "Tropicale": "Tropical",
 "Calabraise": "Calabrese",
 "Crème de baobab": "Baobab cream",
 "Panna cotta fruitée parfumée": "Fragrant fruit panna cotta",
 "Bissap, passion, orange": "Bissap, passion fruit, orange",
 "Fondant au chocolat au lait de Daloa": "Daloa milk chocolate fondant",
 "Crème brûlée à la citronnelle": "Lemongrass crème brûlée",
 "Dêguê de couscous au miel": "Couscous dêguê with honey",
 "Mousse au chocolat noir et basilic": "Dark chocolate and basil mousse",
 "Parfait au chocolat": "Chocolate parfait",
 "Assiette de fruits": "Fruit plate",
 "Tarte aux fruits": "Fruit tart",
 "Coupes de glaces": "Ice cream sundaes",
 "Thé Evannath": "Evannath tea",

 # ── Cocktails ───────────────────────────────────────────────────────────
 "Gingembre, garcinia kola, miel, gin, triple sec, citron": "Ginger, bitter kola, honey, gin, triple sec, lemon",
 "Citron, verveine citronnelle, cannelle, gingembre, kiwi, menthe, rhum, triple sec":
   "Lemon, lemon verbena, cinnamon, ginger, kiwi, mint, rum, triple sec",
 "Mangue, citron, gingembre, rhum blanc, rhum ambré": "Mango, lemon, ginger, white rum, amber rum",
 "Cranberry, maracuja, goyave, vanille, vodka": "Cranberry, passion fruit, guava, vanilla, vodka",
 "Citron, menthe, rhum, sucre de canne, eau gazeuse": "Lime, mint, rum, cane sugar, soda water",
 "Gin, triple sec, citron, sirop de canne, blanc d'œuf": "Gin, triple sec, lemon, cane syrup, egg white",
 "Grenadine, banane, lait de coco, goyave, citron": "Grenadine, banana, coconut milk, guava, lemon",
 "Gin, campari, ananas, citron, soda": "Gin, Campari, pineapple, lemon, soda",
 "Mangue, goyave, rhum blanc": "Mango, guava, white rum",
 "Vodka, goyave, orange, mangue, vanille": "Vodka, guava, orange, mango, vanilla",
 "Gin, basilic frais, citron vert, sirop de canne": "Gin, fresh basil, lime, cane syrup",
 "Ananas, orange, passion, kiwi, sirop de fraise, vanille, rhum":
   "Pineapple, orange, passion fruit, kiwi, strawberry syrup, vanilla, rum",
 "Pamplemousse, orange, vanille, vodka": "Grapefruit, orange, vanilla, vodka",
 "Vodka, rhum, curaçao, ananas, limonade": "Vodka, rum, curaçao, pineapple, lemonade",
 "Fraîcheur Evannath": "Evannath Fresh",
 "Menthe fraîche, concombre, limonade": "Fresh mint, cucumber, lemonade",
 "Exotique": "Exotic",
 "Mangue, goyave, citron": "Mango, guava, lemon",
 "Goyave, orange, banane": "Guava, orange, banana",
 "Concombre, citron vert, pamplemousse, menthe fraîche, fenouil": "Cucumber, lime, grapefruit, fresh mint, fennel",
 "Jus d'ananas, lait de coco, citron, sucre vanillé": "Pineapple juice, coconut milk, lemon, vanilla sugar",
 "Jus de passion, orange, ananas, pêche, curaçao bleu": "Passion fruit juice, orange, pineapple, peach, blue curaçao",
 "Jus d'orange, sirop de grenadine, citron, ananas": "Orange juice, grenadine syrup, lemon, pineapple",
 "Sirop de kiwi, citron, menthe, limonade": "Kiwi syrup, lemon, mint, lemonade",
 "Goyave, framboise, citron, feuilles de coriandre": "Guava, raspberry, lemon, coriander leaves",
 "Pastèque, orange ou clémentine, feuilles de menthe, sprite": "Watermelon, orange or clementine, mint leaves, Sprite",
 "Banane, mangue, maracuja": "Banana, mango, passion fruit",

 # ── Spiritueux, aperitifs, sans alcool ──────────────────────────────────
 "Double Black, Chivas 15 ans, Glenfiddich 12 ans, Gentleman Jack":
   "Double Black, Chivas 15 years, Glenfiddich 12 years, Gentleman Jack",
 "Macallan 12 ans": "Macallan 12 years",
 "Ballantine's 17 ans, Chivas Extra": "Ballantine's 17 years, Chivas Extra",
 "Clan, Red Label, Black Label, Jack Daniel's N°7, Chivas 12 ans, J&amp;B, Jack Honey":
   "Clan, Red Label, Black Label, Jack Daniel's No. 7, Chivas 12 years, J&amp;B, Jack Honey",
 "Téquila": "Tequila",
 "Malibu, Get 27, Get 31, Calvados Père Magloire, poire ou mirabelle, limoncello":
   "Malibu, Get 27, Get 31, Calvados Père Magloire, pear or mirabelle brandy, limoncello",
 "Rhum arrangé maison": "House-infused rum",
 "Martini blanc, rouge ou rosé, porto, Pastis 51, Ricard": "Martini bianco, rosso or rosato, port, Pastis 51, Ricard",
 "Bières": "Beers",
 "Jus nature": "Fresh juice",
 "Orangina, Cody's Energy, autres": "Orangina, Cody's Energy, others",
 "Café": "Coffee",
 "Thé": "Tea",

 # ── Le spa ──────────────────────────────────────────────────────────────
 "Massage thérapeutique aux pierres chauffantes": "Therapeutic hot stone massage",
 "Grand rituel corps de l'Orient, argan divin": "Grand Oriental body ritual, divine argan",
 "Massage sublime de Polynésie, lâcher-prise": "Sublime Polynesian massage, letting go",
 "Massage relaxant sur mesure aux eucalyptus": "Tailored relaxing eucalyptus massage",
 "Massage détente et bien-être au jasmin": "Jasmine relaxation and well-being massage",
 "Massage relaxant de l'arrière du corps": "Relaxing back-of-body massage",
 "Massage délassant des jambes, fraîcheur et légèreté": "Soothing leg massage, freshness and lightness",
 "Soin massage fleurs d'Assinie, pureté et éclat": "Assinie flowers facial massage, purity and radiance",
 "Soin massage aux 5 fleurs d'Assinie, hydratant et repulpant":
   "Five Assinie flowers facial massage, hydrating and plumping",
 "Soin Ko-Bi-Do, jeunesse et éclat": "Ko-Bi-Do facial, youth and radiance",
 "Sauna, fitness et massage": "Sauna, fitness and massage",
 "Gommage au savon noir africain, peau douce et satinée": "African black soap scrub, soft and silky skin",
 "Soin fortifiant et embellissement des ongles naturels": "Strengthening and beautifying care for natural nails",
 "Renfort d'ongles naturels, gainage transparent": "Natural nail reinforcement, clear coating",
 "Rallongement, extensions sans capsules": "Lengthening, tip-free extensions",
 "Pose de vernis": "Polish application",
 "Création de ligne de sourcil": "Eyebrow shaping",
 "Sourcil": "Eyebrows",
 "Lèvre ou menton": "Lip or chin",
 "Pose de faux cils naturels": "Natural false lashes",
 "Jambe entière": "Full leg",
}


class Cles:
    """Distribue les cles data-t d'une page et tient son dictionnaire anglais.

    Un meme texte francais garde la meme cle partout (« Riz étuvé » revient
    trois fois) : le verificateur refuse une cle posee sur deux textes
    differents, pas un texte pose sous la meme cle. Un texte sans traduction
    ne recoit pas de cle — il reste en francais, et rien ne manque au
    dictionnaire.
    """

    def __init__(self, prefixe):
        self.prefixe = prefixe
        self.cles = {}

    def attr(self, fr):
        """L'attribut data-t a poser sur l'element qui porte `fr`, ou ''."""
        if fr not in TRAD:
            return ''
        if fr not in self.cles:
            self.cles[fr] = '%s%d' % (self.prefixe, len(self.cles))
        return ' data-t="%s"' % self.cles[fr]

    def dictionnaire(self):
        """Les entrees a glisser dans `var EN={...}`, virgule finale comprise."""
        return ''.join('%s:%s,' % (k, _js(TRAD[fr])) for fr, k in self.cles.items())


def _js(texte):
    return '"' + texte.replace('\\', '\\\\').replace('"', '\\"') + '"'
