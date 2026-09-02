# -*- coding: utf-8 -*-
"""Les evenements et offres datees de l'etablissement.

Ce fichier est le seul endroit a modifier pour publier une affiche. Il ne
porte AUCUN tarif deja present sur circuits.html : l'evenement renvoie vers
l'offre, il ne la recopie pas. Deux prix pour la meme chose finissent
toujours par diverger, et l'ecart ne se voit nulle part.

Chaque entree :
  slug     identifiant, sert d'ancre
  titre    ce qui s'affiche
  affiche  nom du visuel dans img/opt/ — l'affiche fournie par l'hotel,
           ou a defaut une photo du domaine
  format   'carre' (une affiche 1:1) ou 'large' (une banniere)
  quand    la periode, en toutes lettres
  fin      date ISO de fin, ou None si l'evenement revient chaque annee.
           Passee cette date, le navigateur retire l'entree de lui-meme :
           une affiche perimee sur un site d'hotel fait plus de mal que
           pas d'affiche du tout.
  texte    deux ou trois phrases, pas davantage
  href     ou mene le bouton
  cta      le libelle du bouton
"""

# ATTENTION — les dates ci-dessous sont des HYPOTHESES sauf mention contraire.
# L'etablissement ne publie aucun calendrier. A confirmer avant mise en ligne,
# comme les autres valeurs provisoires du projet (voir « A valider » au README).

EVENEMENTS = [

 dict(slug='packs-vacances',
      titre='Packs Vacances',
      affiche='ev-packs',
      format='carre',
      quand='Saison en cours',
      fin=None,
      texte="Quatre formules pensées pour la saison : famille, couple, enfant, "
            "et la journée Chillday sans nuitée. C'est la campagne que vous "
            "diffusez déjà sur vos réseaux — elle a désormais sa page.",
      href='circuits.html#packs',
      cta='Voir les quatre formules'),

 dict(slug='mechoui-party',
      titre='La Méchoui Party',
      affiche='gal-tab-terrasse',
      format='large',
      quand='Chaque samedi, en soirée',
      fin=None,
      texte="Le rendez-vous du week-end : méchoui en terrasse, puis happy hour "
            "et DJ résident au night-club. Ouvert aux clients de l'hôtel comme "
            "aux visiteurs de passage.",
      href='circuits.html#mechoui',
      cta='En savoir plus'),

 dict(slug='reveillon',
      titre='Le Réveillon à Assinie',
      affiche='gal-lag-nuit',
      format='large',
      quand='31 décembre',
      fin='2027-01-02',
      texte="Dîner de fin d'année au bord de la lagune, puis la nuit au "
            "night-club. Les chambres partent tôt sur cette date : la demande "
            "se fait dès l'automne.",
      href='reserver.html',
      cta='Demander une chambre'),

 dict(slug='coffret-anniversaire',
      titre='Coffret Anniversaire',
      affiche='gal-tab-dressee',
      format='large',
      quand='Toute l\'année, sur demande',
      fin=None,
      texte="Table dressée, gâteau et décoration de la chambre. À organiser "
            "avec la réception, quelques jours à l'avance.",
      href='circuits.html#coffret',
      cta='Organiser un anniversaire'),

 dict(slug='independance',
      titre='Fête de l\'Indépendance',
      affiche='ev-independance',
      format='carre',
      quand='7 août',
      fin='2026-08-09',
      texte="L'hôtel salue chaque année la fête nationale. Cette affiche est "
            "celle que vous avez diffusée en août — elle montre comment une "
            "publication de vos réseaux prend place ici.",
      href='contact.html',
      cta='Nous écrire'),
]

# Traductions. Une cle absente laisse le francais en place.
EN = {
 'packs-vacances':      ('Holiday Packages', 'Current season',
                         'Four packages for the season: family, couple, child, and the '
                         'Chillday with no overnight stay. The campaign you already run '
                         'on social media now has a page of its own.',
                         'See all four'),
 'mechoui-party':       ('Méchoui Party', 'Every Saturday evening',
                         'The weekend gathering: méchoui on the terrace, then happy hour '
                         'and our resident DJ at the night club. Open to hotel guests and '
                         'visitors alike.', 'Find out more'),
 'reveillon':           ("New Year's Eve in Assinie", '31 December',
                         'A year-end dinner by the lagoon, then the night club. Rooms go '
                         'early for this date — requests start coming in the autumn.',
                         'Request a room'),
 'coffret-anniversaire':('Birthday Package', 'All year, on request',
                         'A dressed table, cake and a decorated room. Arranged with the '
                         'front desk a few days ahead.', 'Plan a birthday'),
 'independance':        ('Independence Day', '7 August',
                         'The hotel marks the national holiday each year. This is the '
                         'artwork you published in August — it shows how a post from your '
                         'social media finds its place here.', 'Write to us'),
}
