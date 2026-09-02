# -*- coding: utf-8 -*-
"""Genere index.html a partir de index-template.html.

L'accueil etait la derniere page a recopier les jetons de couleur et le JS de
navigation du site. Toute correction centrale la manquait donc en silence.
Elle consomme desormais les memes briques que les autres, et ne garde en
propre que les six valeurs de couleur qui lui sont specifiques.
"""
import io
from _chrome import (TOKENS, NAV_BASE, LANG_JS, dimensionner, responsive, versionner,
                     liens_nav, EN_NAV, WA, WA_TEXTE, MAIL)
from _evenements import EVENEMENTS, EN as EV_EN
import _schema


# Le bandeau de l'accueil : le premier evenement de la liste, celui que
# l'etablissement veut mettre en avant. Il porte sa date de fin et disparait
# tout seul — le meme mecanisme que sur la page Evenements.
_e = EVENEMENTS[0] if EVENEMENTS else None
if _e:
    _fin = ' data-fin="%s"' % _e['fin'] if _e['fin'] else ''
    # Pas de classe « reveal » : le bandeau annonce ce qui se passe MAINTENANT.
    # L'attendre au defilement le rendrait invisible tant que le script n'a
    # pas tourne, et invisible tout court si le script echoue.
    BANDEAU = ('<div class="bandeau" id="bandeau"%s>'
               '<a href="circuits.html#a-la-une">'
               '<span class="quand" data-t="bq">%s</span>'
               '<b data-t="bt">%s</b>'
               '<span class="t" data-t="bx">%s</span>'
               '<span class="fl" data-t="bf">Voir tout</span>'
               '</a></div>') % (_fin, _e['quand'], _e['titre'],
                                "Et tout ce qui se passe à l'hôtel en ce moment.")
    _en = EV_EN.get(_e['slug'])
    EN_BANDEAU = ('bq:"%s",bt:"%s",bx:"On now at the hotel.",bf:"See all",'
                  % (_en[1], _en[0])) if _en else ''
else:
    BANDEAU, EN_BANDEAU = '', ''

# L'expiration, cote navigateur.
JS_BANDEAU = ("<script>(function(){var b=document.getElementById('bandeau');"
              "if(!b)return;var f=b.getAttribute('data-fin');var a=new Date();"
              "a.setHours(0,0,0,0);"
              "if(f&&new Date(f+'T23:59:59')<a)b.remove();})();</script>")
html = io.open('index-template.html', encoding='utf-8').read()
html = (html
        .replace('{{BANDEAU}}', BANDEAU)
        .replace('{{NAV_LINKS}}', liens_nav('index.html'))
        .replace('{{EN_NAV}}', EN_NAV + EN_BANDEAU)
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
io.open('index.html', 'w', encoding='utf-8').write(html.replace('</body>', JS_BANDEAU + '</body>'))
print('index.html            ok')
