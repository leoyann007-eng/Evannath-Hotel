# -*- coding: utf-8 -*-
"""Ce que le chatbot sait de l'hotel : le texte des pages publiques du site.

    python build-chatbot.py      ->  api/_chatbot.json

LA REGLE : le chatbot ne dit que ce que le site dit. Il ne recoit donc pas
un texte ecrit pour lui — qui divergerait du site au premier changement de
tarif ou d'horaire — mais le texte meme des pages, relu a chaque generation.
Ce qui change pendant la journee (disponibilites, prix saisis dans
l'administration, promotions, evenements) ne passe pas par ici : il le
demande au serveur, en direct (api/chat.js, ses outils).

On retire de chaque page ce qui n'est pas du contenu : en-tete, menus, pied
de page, tiroir de navigation, scripts, decors marques aria-hidden. Sans
cela, le meme menu reviendrait dix-huit fois.

Ce fichier doit sortir IDENTIQUE tant que le site ne change pas : il forme
le debut de chaque question envoyee a l'IA, et c'est ce debut que l'API met
en cache. Pas de date, pas d'ordre aleatoire.
"""
import io, json, re
from html.parser import HTMLParser
from _chrome import WA, WA_TEXTE

# Les pages publiques, dans l'ordre ou un client les lirait. Absentes : les
# mentions legales, la page 404, le recrutement et les variantes de travail.
PAGES = [
    ('index.html', 'Accueil'),
    ('chambres.html', 'Chambres & Suites'),
    ('chambre-standard.html', 'Chambre Standard'),
    ('deluxe-baldaquin.html', 'Deluxe · lits à baldaquin'),
    ('deluxe-superieure.html', 'Deluxe Supérieure'),
    ('suite-anglaise.html', 'Suite Anglaise'),
    ('chambre-mezzanine.html', 'Chambre en Mezzanine'),
    ('mezzanine-superieure.html', 'Mezzanine Supérieure'),
    ('suite-arabe.html', 'Suite Arabe'),
    ('carte.html', 'La table (restaurant, carte)'),
    ('spa.html', 'Le spa'),
    ('experiences.html', 'Expériences'),
    ('circuits.html', 'Offres & Événements'),
    ('seminaires.html', 'Séminaires & groupes'),
    ('galerie.html', 'Galerie'),
    ('a-propos.html', 'À propos'),
    ('informations-utiles.html', 'Informations utiles'),
    ('contact.html', 'Contact'),
]

# Les formulaires aussi : leurs options (« 1 adulte », « 2 adultes »…) et
# leurs boutons ne disent rien de l'hotel.
SAUTE = {'header', 'nav', 'footer', 'script', 'style', 'noscript', 'svg', 'template', 'head',
         'form', 'select', 'button', 'textarea'}
BLOCS = {'p', 'div', 'section', 'article', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'tr', 'br',
         'dt', 'dd', 'figcaption', 'blockquote', 'label', 'option'}
VIDES = {'br', 'img', 'input', 'meta', 'link', 'source', 'hr', 'area', 'col', 'wbr'}


class Texte(HTMLParser):
    """Le texte lisible d'une page, sans ce qui l'entoure."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pile = []        # pour chaque balise ouverte : est-elle a sauter ?
        self.morceaux = []
        self.compteur = None  # la valeur d'un compteur anime, a la place de son « 0 »

    def _saute(self):
        return any(self.pile)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        saute = (tag in SAUTE or a.get('aria-hidden') == 'true' or a.get('id') in ('dw', 'chat')
                 or 'wa' == (a.get('class') or '').split(' ')[0]
                 or 'intro-ecran' in (a.get('class') or ''))
        if tag in BLOCS and not self._saute():
            self.morceaux.append('\n')
        if tag in VIDES:
            return
        # Un compteur anime est ecrit « 0 » dans la page, puis monte jusqu'a
        # data-to : c'est data-to qui est vrai.
        if 'data-to' in a:
            self.compteur = a['data-to'] + (a.get('data-suffix') or '') + ' '
        self.pile.append(saute)

    def handle_endtag(self, tag):
        if tag in VIDES:
            return
        if self.pile:
            self.pile.pop()
        if tag in BLOCS and not self._saute():
            self.morceaux.append('\n')

    def handle_data(self, data):
        if self._saute():
            return
        if self.compteur is not None:
            data, self.compteur = self.compteur, None
        self.morceaux.append(data)

    def texte(self):
        t = ''.join(self.morceaux).replace('\xa0', ' ').replace(' ', ' ')
        lignes = [re.sub(r'[ \t]+', ' ', l).strip() for l in t.split('\n')]
        propres, prec = [], None
        for l in lignes:
            if l and l != prec:
                propres.append(l)
            prec = l
        return '\n'.join(propres)


morceaux = []
for fichier, titre in PAGES:
    p = Texte()
    p.feed(io.open(fichier, encoding='utf-8').read())
    url = '/' + (fichier[:-5] if fichier != 'index.html' else '')
    morceaux.append('=== %s — %s ===\n%s' % (titre, url, p.texte()))

savoir = '\n\n'.join(morceaux)
io.open('api/_chatbot.json', 'w', encoding='utf-8', newline='\n').write(json.dumps({
    'savoir': savoir,
    # Le numero vers lequel le chatbot passe la main. C'est WA : celui des
    # tests tant que WA_EN_TEST vaut True (_chrome.py), celui de l'hotel
    # ensuite — le meme que le bouton flottant.
    'whatsapp': WA,
    'whatsapp_texte': WA_TEXTE,
}, ensure_ascii=False, indent=1))
print('api/_chatbot.json      %d pages, %d caracteres' % (len(PAGES), len(savoir)))
