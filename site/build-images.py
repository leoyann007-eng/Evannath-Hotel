# -*- coding: utf-8 -*-
"""Genere les variantes responsives des photos.

Avant : une seule taille servie a tout le monde. Un telephone en 4G a Abidjan
telechargeait la meme image 1400 px qu'un ecran de bureau.

Apres : trois largeurs par photo (640 / 1024 / 1600), en WebP et en JPEG
progressif. Le navigateur choisit selon la largeur d'affichage ET la densite
d'ecran, via srcset. Les variantes plus larges que l'original ne sont jamais
creees : on ne fabrique pas de pixels qui n'existent pas.

Le script est idempotent — il saute ce qui est deja a jour. Relancer apres
tout ajout de photo, puis relancer les generateurs de pages.
"""
import io, os, re, glob, sys
from PIL import Image

LARGEURS = (640, 1024, 1600)
QUAL_WEBP = 80
QUAL_JPEG = 82
DOSSIER = 'img/opt'

# On ne touche pas aux vignettes -t : elles sont deja dimensionnees pour la
# galerie et servies telles quelles.
def pleines_referencees():
    """Images qui peuvent reellement tirer parti de plusieurs largeurs.

    On ne retient que celles affichees par un <img>, un srcset ou un fond CSS.
    Une image citee uniquement par `data-full` sert a la visionneuse, qui la
    charge en pleine definition : lui fabriquer des paliers ne produit que des
    fichiers que personne ne demande — 160 d'entre eux dormaient dans le depot.
    """
    noms = set()
    for f in glob.glob('*.html'):
        if f == 'index-luxe-variante.html':
            continue
        s = io.open(f, encoding='utf-8').read()
        noms |= set(re.findall(r'(?:src|srcset)="img/opt/([\w-]+)\.(?:webp|jpg)', s))
        noms |= set(re.findall(r'[\s,]img/opt/([\w-]+)\.(?:webp|jpg) \d+w', s))
        noms |= set(re.findall(r"url\('img/opt/([\w-]+)\.(?:webp|jpg)'\)", s))
        noms |= set(re.findall(r'data-bg="([\w-]+)"', s))
    return sorted(n for n in noms
                  if not n.endswith('-t')
                  and not re.search(r'-(?:%s)$' % '|'.join(map(str, LARGEURS)), n))


def a_jour(src, dst):
    return os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src)


def main():
    noms = pleines_referencees()
    faits = sautes = 0
    octets = 0
    for n in noms:
        src = os.path.join(DOSSIER, n + '.jpg')
        if not os.path.exists(src):
            print('  source absente :', src)
            continue
        im = Image.open(src)
        if im.mode not in ('RGB', 'L'):
            im = im.convert('RGB')
        w0, h0 = im.size
        for w in LARGEURS:
            # Un palier trop proche de l'original ne sert a rien : il pese
            # presque autant pour une difference que l'oeil ne voit pas, et
            # double le nombre de fichiers. Au-dela de 90 % de la largeur
            # source, on laisse le navigateur prendre l'original.
            if w >= w0 * 0.9:
                continue
            h = round(h0 * w / w0)
            petite = None
            for ext, kw in (('webp', dict(quality=QUAL_WEBP, method=6)),
                            ('jpg', dict(quality=QUAL_JPEG, optimize=True, progressive=True))):
                dst = os.path.join(DOSSIER, '%s-%d.%s' % (n, w, ext))
                if a_jour(src, dst):
                    sautes += 1
                    octets += os.path.getsize(dst)
                    continue
                if petite is None:
                    petite = im.resize((w, h), Image.LANCZOS)
                petite.save(dst, **kw)
                faits += 1
                octets += os.path.getsize(dst)
    print('%d photos sources' % len(noms))
    print('%d variantes creees, %d deja a jour' % (faits, sautes))
    print('%.1f Mo de variantes au total' % (octets / 1048576))


if __name__ == '__main__':
    main()
