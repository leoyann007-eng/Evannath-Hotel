# -*- coding: utf-8 -*-
"""Les sept categories de chambres : source unique de verite.

Utilise par build-chambres.py (les sept fiches) et build-chambres-index.py
(la page mere). Toute modification de tarif ou de capacite se fait ici, une
seule fois.

Cles : slug, nom, prix (FCFA la nuit), pax (capacite max), tag, meta, facts,
titre, p1/p2/p3 (texte de la fiche), plus (equipements distinctifs),
photos [(fichier, alt, legende)], autres (renvois croises).
"""

# Regroupement pour les filtres de la page mere.
FAMILLE = {
 'chambre-standard': 'chambre',
 'deluxe-baldaquin': 'chambre',
 'deluxe-superieure': 'chambre',
 'suite-anglaise': 'suite',
 'chambre-mezzanine': 'chambre',
 'mezzanine-superieure': 'famille',
 'suite-arabe': 'famille',
}

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
   # Huit photos : la mosaique est une grille de trois colonnes dont la
   # premiere image occupe deux rangees — a huit, elle se remplit exactement.
   photos=[('r-anglaise', "La Suite Anglaise, vue depuis l'entrée", 'La suite'),
           ('r-anglaise3','Le lit et le coin bureau de la Suite Anglaise','Le lit'),
           ('r-anglaise4','Le lit de la Suite Anglaise, côté baie vitrée','Côté baie'),
           ('r-anglaise2','Le salon et la salle à manger de la suite','Le salon'),
           ('r-anglaise5','La salle à manger privative de la Suite Anglaise','La table'),
           ('r-anglaise6','Le coin salon de la Suite Anglaise','Le coin salon'),
           ('r-anglaise7','Le fauteuil coquille de la Suite Anglaise','Le fauteuil'),
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
