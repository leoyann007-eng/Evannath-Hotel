# -*- coding: utf-8 -*-
"""Version anglaise des sept fiches chambres.

Tenue a part de _chambres.py pour deux raisons : le francais reste la source
de verite et n'est jamais touche par une correction de traduction, et le
fichier peut etre relu par un anglophone sans avoir a traverser du code.

Les cles reprennent exactement celles de _chambres.py, sauf `nom` et `prix`,
identiques dans les deux langues. `facts` et `plus` gardent leur forme de
paires ; `caps` reprend les legendes de photos dans l'ordre.

Registre : celui d'un hotel, pas d'une brochure. Les tournures francaises qui
ne passent pas telles quelles sont adaptees, pas calquees.
"""

from _chrome import WA

EN = {

 'chambre-standard': dict(
   tag='Best-seller', meta='2 guests · garden view',
   facts=[('2', 'guests'), ('Queen', 'bed'), ('Garden', 'view'), ('Included', 'breakfast')],
   titre="The essentials,<br>done properly",
   p1="This is the room we sell most, and the one guests mention most often afterwards. A queen bed, air conditioning, a private shower room, and a shared terrace opening onto the garden. Nothing superfluous, nothing missing.",
   p2="It suits a couple passing through, a business traveller, anyone who comes to sleep between two days on the lagoon. Breakfast is included, as in every one of our categories.",
   p3="It is also the room of the Week-End Intense package at 155,000 F: two nights, two breakfasts, drinks, dinner, and a jet-ski outing or lagoon cruise.",
   plus=[],
   caps=['The room', 'The desk', 'The shower room']),

 'deluxe-baldaquin': dict(
   tag='', meta='2 guests · four-poster beds · lounge area',
   facts=[('2', 'guests'), ('Four-poster', 'beds'), ('Lounge', 'area'), ('Garden', 'terrace')],
   titre="Dark wood<br>and light drapes",
   p1="The four-poster beds are what guests photograph most. Dark wood, white drapes, light filtered in the morning — the room has a character the standard categories do not.",
   p2="A lounge area completes the room, and the terrace opens onto the garden. This is the first step where you stop sleeping in a room and start living in it.",
   p3="Fifteen thousand francs separate this room from the Standard. It is the best value on our whole rate card.",
   plus=[('Four-poster beds', 'Solid wood and sheer drapes')],
   caps=['The room', 'The lounge area', 'The shower room']),

 'deluxe-superieure': dict(
   tag='Private dining room', meta='3 guests · wax textiles · dining room',
   facts=[('3', 'guests'), ('Four-poster', 'beds'), ('Private', 'dining room'), ('Wax', 'textiles')],
   titre="The Deluxe,<br>more generous",
   p1="The same four-poster beds, but the room gains a private dining room. The wax textiles give it its colour — they are what you notice on the way in.",
   p2="Three guests fit without crowding one another. It is our choice for a family with one child, or for a longer stay where you like to take breakfast in your own room.",
   p3="The dining room makes the difference for anyone staying more than three nights.",
   plus=[('Private dining room', 'Seats three'),
         ('Wax textiles', 'Sourced from local craftspeople')],
   caps=['The room', 'The textiles', 'The lounge']),

 'suite-anglaise': dict(
   tag='Lagoon view', meta='2 guests · lagoon view · the finest sunset',
   facts=[('2', 'guests'), ('Lagoon', 'view'), ('Separate', 'lounge'), ('Sunset', 'aspect')],
   titre="The view,<br>then the sunset",
   p1="This is the first category looking straight onto the Aby lagoon and the pool. The aspect does the rest: from five in the afternoon, the light comes through the bay window and stays.",
   p2="The elegance here is quiet — restrained materials, a separate lounge, nothing shouting. The suite suits those who come for the calm rather than the party.",
   p3="If you remember one thing: this is where the finest sunset on the estate is seen from.",
   plus=[('Direct lagoon view', 'And over the pool'),
         ('Separate lounge', 'Its own sitting area')],
   caps=['The suite', 'The bed', 'Bay side', 'The lounge', 'The table',
         'The sitting area', 'The chair', 'The bathroom']),

 'chambre-mezzanine': dict(
   tag='', meta='2 guests · duplex · under the rafters',
   facts=[('2', 'guests'), ('Duplex', 'volume'), ('Wooden', 'stair'), ('Rafters', 'under')],
   titre="A volume<br>under the rafters",
   p1="The mezzanine is a duplex: you live downstairs and sleep upstairs. A wooden stair climbs to a raised sleeping area, under exposed rafters.",
   p2="It is the room of young couples and of anyone who likes volume. The open ceiling changes the feel entirely compared with a conventional room.",
   p3="Two guests, no more — the mezzanine is lived in as a pair or not at all.",
   plus=[('Raised sleeping area', 'Reached by a wooden stair'),
         ('Exposed rafters', 'Open ceiling')],
   caps=['The room', 'The stair', 'The shower room']),

 'mezzanine-superieure': dict(
   tag='Private terrace', meta='4 guests · private terrace · lounge area',
   facts=[('4', 'guests'), ('Duplex', 'volume'), ('Private', 'terrace'), ('Full', 'lounge')],
   titre="The mezzanine,<br>on a larger scale",
   p1="The same idea, with more room: a full lounge area downstairs, upgraded fittings, and above all a private terrace that exists in no other category at this rate.",
   p2="Four guests stay comfortably — it is our most requested family room after the Arabian Suite.",
   p3="It is also the room of the Honeymoon package at 340,000 F: two nights, the room dressed before you arrive, breakfasts included.",
   plus=[('Private terrace', 'Yours alone'),
         ('Full lounge area', 'Separate from the sleeping space')],
   caps=['The room', 'The mezzanine', 'The lounge']),

 'suite-arabe': dict(
   tag='Signature', meta='6 guests · 2 bedrooms · Moorish decor',
   facts=[('2', 'bedrooms'), ('6', 'guests'), ('Private', 'lounge'), ('Moorish', 'decor')],
   titre="Two bedrooms,<br>a lounge, a dedicated service",
   p1="This is the largest of our seven categories, and the only one with two separate bedrooms. The Moorish decor — carved wood, arches, embroidered textiles — was composed piece by piece with local craftspeople, in the spirit that guides the whole property.",
   p2="Two couples, a family with older children, or a group of friends: the suite absorbs six guests without anyone getting in anyone's way. The private lounge serves as the shared living room, and each bedroom keeps its own shower room.",
   p3="It is the category most requested for honeymoons and birthdays. It goes quickly in the dry season — from December to March, book several weeks ahead.",
   plus=[('Two separate bedrooms', 'Each with its own shower room'),
         ('Private lounge', 'Shared living room'),
         ('Dedicated service', 'On request')],
   caps=['The suite', 'The second bedroom', 'The bathroom', 'The lounge', 'The terrace']),
}


# Le chassis commun aux sept fiches : libelles, equipements, inclus,
# conditions et tunnel de reservation lateral.
CHASSIS = {
 'c1': 'Home', 'c2': 'Rooms &amp; Suites',
 'eb0': 'Room',
 'pnuit': 'FCFA / night',
 'ebr': 'The room',
 'ebe': 'Amenities', 'hae': 'In the room',
 'ebi': 'Included', 'hai': 'Included in the rate',
 'ebc': 'Conditions', 'hac': 'Good to know',
 'cd1': 'Check-in', 'cd1v': 'from 2 pm',
 'cd2': 'Check-out', 'cd2v': 'before noon',
 'cd3': 'Cancellation', 'cd3v': 'free up to 48 h before',
 'cd4': 'Deposit', 'cd4v': '30 % on booking',
 'cd5': 'Pets', 'cd5v': 'not allowed',
 'cd6': 'Payment', 'cd6v': 'Wave · Orange Money · MTN · card',
 'cdn': 'Full details are on the <a href="informations-utiles.html#reserver" style="color:var(--bronze)">Useful information</a> page.',
 'apd': 'From', 'pern': 'per night, breakfast included',
 'la1': 'Check-in', 'la2': 'Check-out', 'lax': 'Guests',
 'rtx': 'Tourist tax', 'rpd': 'Breakfast', 'rin': 'Included', 'rtt': 'Total stay',
 'bkb': 'Book this room',
 'hlp': 'A question? Write to us on <a href="https://wa.me/' + WA + '" target="_blank" rel="noopener">WhatsApp</a> or call +225 01 51 52 75 75.',
 'ebo': 'Other categories', 'hao': 'If this one is taken',
 'mbs': 'FCFA · total stay',
 'cta': 'Book',
}

# Equipements de base, dans l'ordre de AMEN_BASE.
AMEN_EN = ['Air conditioning', 'Free wifi', 'Smart TV', 'Private shower room',
           'Hairdryer', 'Safe', 'Pool &amp; jacuzzi access', 'Breakfast included']

# Prestations incluses, dans l'ordre de INCL.
INCL_EN = [
 ('Breakfast', 'Served in the restaurant or on the terrace, fresh fruit and local produce.'),
 ('Free airport shuttle', 'Pick-up and drop-off at Félix-Houphouët-Boigny airport, free of charge, on request.'),
 ('Pool, jacuzzi and gym', 'Open access from first light until dark.'),
 ('Wifi and parking', 'Free across the estate.'),
]
