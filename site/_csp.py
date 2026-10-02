# -*- coding: utf-8 -*-
"""La politique de securite du contenu (Content-Security-Policy).

Le navigateur n'execute QUE les scripts qu'elle autorise. Un script injecte
— par un champ mal echappe, un lien piege, une extension — est refuse avant
de tourner.

POURQUOI DES EMPREINTES, ET PAS 'unsafe-inline'. Le site est fait de pages
statiques dont les scripts sont ecrits dans la page. 'unsafe-inline' les
autoriserait d'un mot, mais autoriserait AUSSI tout script injecte : la
politique ne protegerait plus de rien. On autorise donc chaque script par son
empreinte SHA-256, calculee ici sur les pages telles qu'elles sont servies.

L'ENTRETIEN : build-sitemap.py, lance en dernier, recalcule les empreintes et
les ecrit dans vercel.json. verifier.py refuse toute page dont un script n'y
figure pas : une page modifiee sans relancer build-sitemap.py ne part pas en
ligne avec des scripts bloques.

Les styles restent en 'unsafe-inline' : les pages en portent partout
(attributs style), et un style injecte ne vole ni session ni donnee.
"""
import base64
import glob
import hashlib
import io
import os
import re

# Les pages servies. Les gabarits et la variante ne partent pas (.vercelignore).
NON_SERVIES = re.compile(r'(-template\.html|index-luxe-variante\.html)$')

SCRIPT = re.compile(r'<script(?![^>]*\bsrc=)([^>]*)>(.*?)</script>', re.S | re.I)


def pages_servies(racine='.'):
    fichiers = glob.glob(os.path.join(racine, '*.html')) + glob.glob(os.path.join(racine, 'admin', '*.html'))
    return sorted(f for f in fichiers if not NON_SERVIES.search(f))


def empreinte(texte):
    # Le navigateur normalise les fins de ligne (CRLF -> LF) avant de hacher :
    # on fait de meme, sinon une copie de travail Windows donnerait d'autres
    # empreintes que la production.
    texte = texte.replace('\r\n', '\n').replace('\r', '\n')
    return "'sha256-" + base64.b64encode(hashlib.sha256(texte.encode('utf-8')).digest()).decode() + "'"


def empreintes_de(html):
    """Les empreintes des scripts EXECUTABLES de la page (pas le JSON-LD)."""
    out = []
    for m in SCRIPT.finditer(html):
        attrs = m.group(1).lower()
        if 'application/ld+json' in attrs or 'application/json' in attrs:
            continue
        out.append(empreinte(m.group(2)))
    return out


def toutes_les_empreintes(racine='.'):
    vues = set()
    for f in pages_servies(racine):
        vues.update(empreintes_de(io.open(f, encoding='utf-8').read()))
    return sorted(vues)


def politique(empreintes):
    return '; '.join([
        "default-src 'self'",
        "script-src 'self' " + ' '.join(empreintes),
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com data:",
        # Les affiches deposees vivent dans notre magasin Blob ; data: et blob:
        # servent a l'apercu d'une image avant son envoi (administration).
        "img-src 'self' data: blob: https://*.public.blob.vercel-storage.com",
        "media-src 'self'",
        "connect-src 'self'",
        # La carte d'acces (contact, accueil).
        "frame-src https://www.google.com https://maps.google.com",
        "frame-ancestors 'self'",
        "form-action 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        'upgrade-insecure-requests',
    ])
