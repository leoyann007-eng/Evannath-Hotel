# -*- coding: utf-8 -*-
"""Les evenements dates de l'etablissement.

Ce fichier est le seul endroit a modifier pour publier un evenement. Il ne
porte AUCUN tarif deja present ailleurs sur la page : l'evenement renvoie vers
l'offre, il ne la recopie pas.

Cette liste ne contient QUE ce qui a une date ou revient a date fixe. Les
Packs Vacances et le Coffret Anniversaire n'y sont pas : ce sont des offres
permanentes, elles vivent dans « Nos offres & forfaits ». Une chose, un
endroit.

Chaque entree :
  slug      identifiant, sert d'ancre
  categorie le surtitre, en petites capitales
  titre     le debut du titre
  accent    la fin du titre, en italique — c'est elle qui donne le rythme
  badge     la recurrence, dans la pastille du haut
  fond      l'image de fond, plein cadre, dans img/opt/
  quand     la periode en toutes lettres, pour le JSON-LD
  fin       date ISO de fin, ou None si l'evenement revient chaque annee.
            Passee cette date, le navigateur retire la diapositive : une
            affiche perimee sur un site d'hotel fait plus de mal que pas
            d'affiche du tout.
  texte     deux phrases, pas davantage
  infos     trois ou quatre couples (libelle, valeur) — les pastilles
  href      ou mene le bouton
  cta       le libelle du bouton

ATTENTION — les dates et les horaires sont des HYPOTHESES. L'etablissement ne
publie aucun calendrier. A confirmer avant mise en ligne (voir « A valider »
dans le README).
"""

EVENEMENTS = [

 dict(slug='reveillon',
      categorie="Soirée de fin d'année",
      titre='Le Réveillon',
      accent='à Assinie',
      badge='31 décembre',
      fond='gal-lag-nuit',
      quand='31 décembre',
      fin='2027-01-02',
      texte="Dîner de fin d'année au bord de la lagune, puis la nuit au "
            "night-club. Les chambres partent tôt sur cette date.",
      infos=[('Horaire', 'Dès 20 h'),
             ('Lieu', 'La paillote'),
             ('Ambiance', 'DJ résident'),
             ('Au menu', 'Dîner de fête')],
      href='reserver.html',
      cta='Réserver ma chambre'),

 dict(slug='mechoui-party',
      categorie='Rendez-vous hebdomadaire',
      titre='La Méchoui',
      accent='Party',
      badge='Tous les samedis',
      fond='gal-tab-terrasse',
      quand='Chaque samedi, dès 15 h',
      fin=None,
      texte="Méchoui au bord de l'eau, puis la soirée continue au night-club. "
            "Ouvert aux clients de l'hôtel comme aux visiteurs de passage.",
      infos=[('Horaire', 'Dès 15 h'),
             ('Lieu', 'La terrasse'),
             ('Ambiance', 'Happy hour'),
             ('Au menu', 'Méchoui grillé')],
      href='#demande',
      cta='Réserver une table'),

 dict(slug='independance',
      categorie='Fête nationale',
      titre='Jour de',
      accent="l'Indépendance",
      badge='7 août',
      fond='ev-independance',
      quand='7 août',
      fin='2026-08-09',
      texte="L'hôtel salue chaque année la fête nationale. Cette affiche est "
            "celle que vous avez diffusée en août.",
      infos=[('Horaire', 'Toute la journée'),
             ('Lieu', 'Le domaine'),
             ('Ambiance', 'En famille')],
      href='contact.html',
      cta='Nous écrire'),
]

# Traductions. Une cle absente laisse le francais en place.
# (categorie, titre, accent, badge, texte, cta, valeurs des pastilles)
EN = {
 'reveillon': ("Year's end", 'New Year', 'in Assinie', '31 December',
               'A year-end dinner by the lagoon, then the night club. Rooms go early '
               'for this date.', 'Book my room',
               ['From 8 pm', 'The pontoon', 'Resident DJ', 'Festive dinner']),

 'mechoui-party': ('Weekly gathering', 'The Méchoui', 'Party', 'Every Saturday',
                   'Méchoui by the water, then the evening carries on at the night '
                   'club. Open to hotel guests and visitors alike.', 'Book a table',
                   ['From 3 pm', 'The terrace', 'Happy hour', 'Grilled méchoui']),

 'independance': ('National holiday', 'Independence', 'Day', '7 August',
                  'The hotel marks the national holiday each year. This is the '
                  'artwork you published in August.', 'Write to us',
                  ['All day', 'The grounds', 'Family']),
}

# Les libelles des pastilles, communs a tous les evenements.
INFOS_EN = {'Horaire': 'Time', 'Lieu': 'Where',
            'Ambiance': 'Mood', 'Au menu': 'On the menu'}
