# -*- coding: utf-8 -*-
"""Genere index.html a partir de index-template.html.

L'accueil etait la derniere page a recopier les jetons de couleur et le JS de
navigation du site. Toute correction centrale la manquait donc en silence.
Elle consomme desormais les memes briques que les autres, et ne garde en
propre que les six valeurs de couleur qui lui sont specifiques.
"""
import io
from _chrome import TOKENS, NAV_BASE, LANG_JS, dimensionner, responsive, versionner, WA, WA_TEXTE, MAIL
import _schema

html = io.open('index-template.html', encoding='utf-8').read()
html = (html
        .replace('{{WA}}', WA)
        .replace('{{WA_TEXTE}}', WA_TEXTE)
        .replace('{{TOKENS}}', TOKENS)
        .replace('{{NAV_BASE}}', NAV_BASE)
        .replace('{{LANG_JS}}', LANG_JS)
        .replace('{{JSONLD}}', _schema.bloc(_schema.hotel(complet=True),
                                            _schema.site_web(),
                                            _schema.restaurant())))
# Largeur reelle des cartes des deux grilles de l'accueil.
#
# .wrap fait min(1240px, 100vw) - 48. Les chambres tiennent sur trois colonnes
# de 24 px de gouttiere au-dela de 1024, les offres sur quatre ; en dessous,
# deux colonnes, puis une seule sous 721 px.
#
# On declare la geometrie des CHAMBRES, la plus large des deux : une image
# partagee par les deux grilles — r-standard, r-mezzanine — doit rester nette
# dans la plus grande case. Sans cette declaration, une carte de 279 px se
# faisait servir l'image pleine, parce que sizes annoncait 700 px.
SIZES_CARTES = ('(max-width:720px) calc(100vw - 48px), '
                '(max-width:1024px) calc((100vw - 72px) / 2), '
                '(max-width:1287px) calc((100vw - 96px) / 3), 381px')
CARTES = ('r-standard', 'ig-baldaquin', 'r-wax', 'r-anglaise', 'r-mezz2',
          'r-mezzanine', 'r-arabe', 'g-aerien', 'g-terrasse')

html = versionner(responsive(dimensionner(html), hero='hero-chambre-wax',
                             sizes={n: SIZES_CARTES for n in CARTES}))
# En dernier : le JSON-LD injecte plus haut porte lui aussi l'adresse.
html = html.replace('{{MAIL}}', MAIL)

assert '{{' not in html, 'un placeholder n a pas ete remplace'
io.open('index.html', 'w', encoding='utf-8').write(html)
print('index.html            ok')
