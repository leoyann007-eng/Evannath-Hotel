# -*- coding: utf-8 -*-
"""Genere index.html a partir de index-template.html.

L'accueil etait la derniere page a recopier les jetons de couleur et le JS de
navigation du site. Toute correction centrale la manquait donc en silence.
Elle consomme desormais les memes briques que les autres, et ne garde en
propre que les six valeurs de couleur qui lui sont specifiques.
"""
import io
from _chrome import TOKENS, NAV_BASE, LANG_JS

html = io.open('index-template.html', encoding='utf-8').read()
html = (html
        .replace('{{TOKENS}}', TOKENS)
        .replace('{{NAV_BASE}}', NAV_BASE)
        .replace('{{LANG_JS}}', LANG_JS))
assert '{{' not in html, 'un placeholder n a pas ete remplace'
io.open('index.html', 'w', encoding='utf-8').write(html)
print('index.html            ok')
