# -*- coding: utf-8 -*-
"""Donnees structurees JSON-LD (schema.org).

Ce que Google attend d'un site hotelier : la fiche etablissement, les chambres
avec leur tarif, le restaurant, les questions frequentes et le fil d'Ariane.
Sans ces balises, pas de panneau lateral, pas de fourchette de prix dans les
resultats, pas de fiche enrichie.

Un seul point n'est PAS renseigne : les coordonnees GPS. L'etablissement ne les
publie nulle part et un point mal place vaut moins que pas de point du tout.
Voir « A valider » dans le README.

Toutes les entites pointent vers @id stables, pour que Google comprenne qu'il
s'agit du meme etablissement d'une page a l'autre.
"""
import json
from _chrome import SITE

DEVISE = 'XOF'          # franc CFA (UEMOA)
ID_HOTEL = SITE + '/#hotel'
ID_SITE = SITE + '/#website'
ID_RESTO = SITE + '/#restaurant'

TEL = ['+225 27 21 73 12 65', '+225 01 51 52 75 75']
RESEAUX = ['https://www.facebook.com/evannathhotel',
           'https://www.instagram.com/evannathhotel']

# Equipements de l'etablissement, tels qu'annonces par l'hotel.
EQUIPEMENTS = [
    ('Piscine exterieure', True), ('Spa', True), ('Sauna', True),
    ('Restaurant', True), ('Bar', True), ('Wifi gratuit', True),
    ('Parking gratuit', True), ('Navette aeroport gratuite', True),
    ('Salle de conference', True), ('Climatisation', True),
    ('Reception 24h/24', True), ('Petit-dejeuner inclus', True),
    ('Acces lagune', True),
]

ADRESSE = {
    '@type': 'PostalAddress',
    'streetAddress': 'Assinie PK 19',
    'addressLocality': 'Assinie-Mafia',
    'addressRegion': 'Comoé',
    'addressCountry': 'CI',
}


def _amenities():
    return [{'@type': 'LocationFeatureSpecification', 'name': n, 'value': v}
            for n, v in EQUIPEMENTS]


def hotel(complet=False):
    """Fiche etablissement. `complet=True` sur l'accueil uniquement :
    ailleurs on renvoie une reference legere vers le meme @id."""
    if not complet:
        return {'@type': 'Hotel', '@id': ID_HOTEL, 'name': 'Hôtel Evannath'}
    return {
        '@type': ['Hotel', 'LodgingBusiness'],
        '@id': ID_HOTEL,
        'name': 'Hôtel Evannath',
        'alternateName': 'Evannath — Le Rêve Africain',
        'slogan': 'Le Rêve Africain',
        'description': ("Hôtel de 46 chambres et suites à Assinie PK 19, en Côte d'Ivoire, "
                        "face à la lagune Aby : paillote sur pilotis, piscine, spa, restaurant "
                        "et salle de séminaire. Navette aéroport offerte."),
        'url': SITE + '/',
        'logo': SITE + '/img/opt/logo-blanc.png',
        'image': [SITE + '/img/opt/' + n + '.jpg'
                  for n in ('hero-chambre-wax', 'hero-aerien', 'g-lobby', 'g-resto')],
        'address': ADRESSE,
        'telephone': TEL[0],
        'email': 'bonjour@evannathhotel.com',
        'sameAs': RESEAUX,
        'priceRange': '67 000 – 280 000 XOF',
        'currenciesAccepted': DEVISE,
        'paymentAccepted': 'Espèces, Wave, Orange Money, MTN Mobile Money, carte bancaire',
        'numberOfRooms': {'@type': 'QuantitativeValue', 'value': 46},
        'petsAllowed': False,
        'amenityFeature': _amenities(),
        'checkinTime': '14:00',
        'checkoutTime': '12:00',
        'contactPoint': [{
            '@type': 'ContactPoint',
            'contactType': 'reservations',
            'telephone': t,
            'email': 'bonjour@evannathhotel.com',
            'availableLanguage': ['fr', 'en'],
        } for t in TEL],
        'hasMap': 'https://www.google.com/maps/search/Assinie+PK+19',
        'containsPlace': {'@id': ID_RESTO},
    }


def site_web():
    return {
        '@type': 'WebSite',
        '@id': ID_SITE,
        'url': SITE + '/',
        'name': 'Hôtel Evannath',
        'inLanguage': 'fr-CI',
        'publisher': {'@id': ID_HOTEL},
    }


def fil(items):
    """items : liste de (libelle, slug ou None pour la page courante)."""
    el = []
    for i, (nom, slug) in enumerate(items, 1):
        e = {'@type': 'ListItem', 'position': i, 'name': nom}
        if slug is not None:
            e['item'] = SITE + ('/' if slug in ('index', '') else '/' + slug)
        el.append(e)
    return {'@type': 'BreadcrumbList', 'itemListElement': el}


def chambre(nom, slug, prix, pax, description, photos, equipements=(), lits=None):
    d = {
        '@type': 'HotelRoom',
        '@id': SITE + '/' + slug + '#room',
        'name': nom,
        'description': description,
        'url': SITE + '/' + slug,
        'image': [SITE + '/img/opt/' + p + '.jpg' for p in photos],
        'containedInPlace': {'@id': ID_HOTEL},
        'occupancy': {'@type': 'QuantitativeValue', 'maxValue': pax, 'unitCode': 'C62'},
        'offers': {
            '@type': 'Offer',
            'price': prix,
            'priceCurrency': DEVISE,
            'availability': 'https://schema.org/InStock',
            'url': SITE + '/reserver?chambre=' + slug,
            'priceSpecification': {
                '@type': 'UnitPriceSpecification',
                'price': prix,
                'priceCurrency': DEVISE,
                'unitText': 'nuit',
            },
        },
    }
    if equipements:
        d['amenityFeature'] = [{'@type': 'LocationFeatureSpecification',
                                'name': e, 'value': True} for e in equipements]
    if lits:
        d['bed'] = {'@type': 'BedDetails', 'typeOfBed': lits}
    return d


def restaurant(nb_plats=None):
    d = {
        '@type': 'Restaurant',
        '@id': ID_RESTO,
        'name': "La table de l'Hôtel Evannath",
        'description': ("Cuisine ivoirienne et continentale à Assinie PK 19 : poisson du jour, "
                        "kedjenou, grillades et cocktails, en terrasse face à la piscine."),
        'url': SITE + '/carte',
        'servesCuisine': ['Ivoirienne', 'Africaine', 'Française', 'Fruits de mer'],
        'priceRange': 'XOF',
        'currenciesAccepted': DEVISE,
        'address': ADRESSE,
        'telephone': TEL[0],
        'image': SITE + '/img/opt/gal-lag-nuit.jpg',
        'hasMenu': SITE + '/carte',
        'containedInPlace': {'@id': ID_HOTEL},
    }
    if nb_plats:
        d['description'] += ' %d propositions à la carte.' % nb_plats
    return d


def faq(qr):
    """qr : liste de (question, reponse en texte brut)."""
    return {
        '@type': 'FAQPage',
        'mainEntity': [{
            '@type': 'Question',
            'name': q,
            'acceptedAnswer': {'@type': 'Answer', 'text': r},
        } for q, r in qr],
    }


def service(nom, description, url_slug, image=None, catalogue=None):
    d = {
        '@type': 'Service',
        'name': nom,
        'description': description,
        'url': SITE + '/' + url_slug,
        'provider': {'@id': ID_HOTEL},
        'areaServed': {'@type': 'Place', 'name': "Assinie, Côte d'Ivoire"},
    }
    if image:
        d['image'] = SITE + '/img/opt/' + image + '.jpg'
    if catalogue:
        # Une entree vaut (nom, prix, description) ou, pour une offre dont le
        # prix se compte autrement qu'au forfait, (nom, prix, description,
        # unite) : « par personne », « par enfant ». Sans cette unite, un
        # forfait a 25 000 F par enfant et un forfait a 25 000 F tout compris
        # se ressemblent dans un resultat de recherche.
        elements = []
        for entree in catalogue:
            n, px, desc = entree[0], entree[1], entree[2]
            unite = entree[3] if len(entree) > 3 else None
            offre = {'@type': 'Offer', 'name': n}
            if px:
                offre['price'] = px
                offre['priceCurrency'] = DEVISE
                offre['availability'] = 'https://schema.org/InStock'
                if unite:
                    offre['priceSpecification'] = {
                        '@type': 'UnitPriceSpecification',
                        'price': px, 'priceCurrency': DEVISE, 'unitText': unite,
                    }
            if desc:
                offre['description'] = desc
            elements.append(offre)
        d['hasOfferCatalog'] = {
            '@type': 'OfferCatalog', 'name': nom, 'itemListElement': elements,
        }
    return d


def galerie(photos):
    return {
        '@type': 'ImageGallery',
        'name': "Galerie de l'Hôtel Evannath",
        'url': SITE + '/galerie',
        'about': {'@id': ID_HOTEL},
        'image': [SITE + '/img/opt/' + p + '.jpg' for p in photos],
    }


def bloc(*entites):
    """Assemble les entites en un seul <script type=application/ld+json>.

    Un unique graphe plutot que plusieurs balises : Google lit mieux, et les
    references par @id restent resolvables entre entites.
    """
    graphe = [e for e in entites if e]
    doc = {'@context': 'https://schema.org', '@graph': graphe}
    return ('<script type="application/ld+json">'
            + json.dumps(doc, ensure_ascii=False, separators=(',', ':'))
            + '</script>')
