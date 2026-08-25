# -*- coding: utf-8 -*-
"""Controles de coherence sur les pages generees.

A lancer apres les generateurs. Chaque controle correspond a un defaut qui est
reellement survenu sur ce projet — ils sont la pour qu'il ne revienne pas.
"""
import io, os, re, glob, json, sys
sys.path.insert(0, '.')
from _chrome import TOKENS, NAV_BASE, LANG_JS, empreinte

_cache = {}


def _taille_de(chemin):
    if chemin not in _cache:
        from PIL import Image
        _cache[chemin] = Image.open(chemin).size
    return _cache[chemin]


def _largeur_de(chemin):
    return _taille_de(chemin)[0]


IGNORE = {'index-luxe-variante.html', 'carte-template.html',
          'spa-template.html', 'index-template.html'}
SANS_JSONLD = {'404.html', 'mentions-legales.html', 'reserver.html'}


def controler():
    pages = [f for f in sorted(glob.glob('*.html')) if f not in IGNORE]
    pb = []
    jetons_ref = set(re.findall(r'(--[\w-]+)\s*:', TOKENS))

    for f in pages:
        s = io.open(f, encoding='utf-8').read()

        # 1. toute variable CSS utilisee doit etre declaree dans la page
        for v in set(re.findall(r'var\((--[\w-]+)\)', s)):
            if not re.search(re.escape(v) + r'\s*:', s):
                pb.append((f, 'variable CSS non declaree : ' + v))

        # 2. les jetons partages doivent tous etre presents
        manquants = jetons_ref - set(re.findall(r'(--[\w-]+)\s*:', s))
        if manquants:
            pb.append((f, 'jetons absents : ' + ', '.join(sorted(manquants))))

        # 3. le JS de navigation doit venir de la source partagee
        if "getElementById('hd')" in s and NAV_BASE not in s:
            pb.append((f, 'JS de navigation divergent de NAV_BASE'))
        if 'var FR={}' in s and LANG_JS not in s:
            pb.append((f, 'JS de langue divergent de LANG_JS'))

        # 4. chaque image doit reserver sa place
        for i in re.findall(r'<img[^>]*>', s):
            if 'src=' in i and not ('width=' in i and 'height=' in i):
                pb.append((f, 'image sans dimensions : ' + i[:60]))

        # 5. les descripteurs w d'un srcset doivent correspondre aux fichiers
        for jeu in re.findall(r'srcset="([^"]+)"', s):
            for c in jeu.split(','):
                bout = c.strip().split()
                if len(bout) != 2 or not bout[1].endswith('w'):
                    continue
                if not os.path.exists(bout[0]):
                    continue
                if _largeur_de(bout[0]) != int(bout[1][:-1]):
                    pb.append((f, 'descripteur faux : %s annonce %s' % (bout[0], bout[1])))

        # 6. les dimensions declarees doivent correspondre au fichier
        for balise in re.findall(r'<img[^>]*>', s):
            w = re.search(r'width="(\d+)"', balise)
            h = re.search(r'height="(\d+)"', balise)
            src = re.search(r'src="(img/opt/[\w-]+\.(?:jpg|png|webp))"', balise)
            if not (w and h and src) or not os.path.exists(src.group(1)):
                continue
            reel = _taille_de(src.group(1))
            if reel != (int(w.group(1)), int(h.group(1))):
                pb.append((f, '%s declare %sx%s, le fichier fait %dx%d'
                           % (src.group(1), w.group(1), h.group(1), reel[0], reel[1])))

        # 7. fichiers reellement presents, quel que soit l'attribut
        # (src, srcset, poster, data-full, href, url(...) : une affiche de video
        # manquante etait passee inapercue parce que seul src etait regarde)
        for src in set(re.findall(r'(img/opt/[\w-]+\.(?:webp|jpg|png))', s)):
            if not os.path.exists(src):
                pb.append((f, 'fichier absent : ' + src))

        # 7 bis. les medias servis en « immutable » portent une empreinte de
        # contenu dans leur URL, et cette empreinte doit correspondre au
        # fichier. Sans ce controle, re-encoder une video sans relancer les
        # generateurs laisse tous les visiteurs precedents sur l'ancienne
        # version pendant un an, sans moyen de la remplacer.
        for chemin, v in re.findall(
                r'(video/[\w-]+\.(?:mp4|webm)|img/opt/[\w-]+-affiche\.(?:jpg|webp))'
                r'\?v=([0-9a-f]+)', s):
            if not os.path.exists(chemin):
                pb.append((f, 'fichier absent : ' + chemin))
            elif empreinte(chemin) != v:
                pb.append((f, '%s : empreinte %s dans l URL, %s dans le fichier '
                              '— relancer les generateurs' % (chemin, v, empreinte(chemin))))
        for chemin in set(re.findall(r"""["'(](video/[\w-]+\.(?:mp4|webm))(?![\w.?])""", s)):
            pb.append((f, 'media sans empreinte : ' + chemin))

        # 8. toute image ouvrable en plein ecran doit exister aussi en WebP
        for base in re.findall(r'data-full="(img/opt/[\w-]+)\.jpg"', s):
            if not os.path.exists(base + '.webp'):
                pb.append((f, 'visionneuse : %s.webp manquant' % base))
        if 'dataset.full||' in s:
            pb.append((f, 'visionneuse : URL construite a la main, utiliser plein()'))

        # 9. liens internes
        for h in set(re.findall(r'href="([^"]+)"', s)):
            if h.startswith(('http', 'mailto:', 'tel:', '#', '/api')):
                continue
            p = h.split('#')[0].split('?')[0].lstrip('/')
            if p and not os.path.exists(p):
                pb.append((f, 'lien mort : ' + h))

        # 10. navigation complete et repere principal
        if len(re.findall(r'<a href="[^"]+"[^>]*><i>\d+</i><span data-t="n\d+"', s)) != 11:
            pb.append((f, 'navigation incomplete'))
        if s.count('<main id="contenu">') != 1:
            pb.append((f, 'balise <main> absente ou en double'))

        # 11. donnees structurees valides
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
        if m:
            try:
                json.loads(m.group(1))
            except Exception as e:
                pb.append((f, 'JSON-LD invalide : %s' % e))
        elif f not in SANS_JSONLD:
            pb.append((f, 'JSON-LD absent'))

        # 12. une barre collante doit avoir son rideau
        if 'collante"' in s:
            if 'collante::before' not in s:
                pb.append((f, 'rideau CSS absent'))
            if 'epinglee' not in s:
                pb.append((f, 'rideau JS absent'))

    print('%d pages controlees' % len(pages))
    if pb:
        print('%d anomalie(s) :' % len(pb))
        for f, m in pb[:40]:
            print('  %-26s %s' % (f, m))
    else:
        print('aucune anomalie')
    return len(pb)


if __name__ == '__main__':
    sys.exit(1 if controler() else 0)
