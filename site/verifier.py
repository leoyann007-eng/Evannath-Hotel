# -*- coding: utf-8 -*-
"""Controles de coherence sur les pages generees.

A lancer apres les generateurs. Chaque controle correspond a un defaut qui est
reellement survenu sur ce projet — ils sont la pour qu'il ne revienne pas.
"""
import io, os, re, glob, json, sys
sys.path.insert(0, '.')
from _chrome import TOKENS, NAV_BASE, LANG_JS

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

        # 5. fichiers reellement presents
        for src in set(re.findall(r'(?:src|srcset)="(img/[^" ]+)', s)):
            if not os.path.exists(src):
                pb.append((f, 'fichier absent : ' + src))

        # 6. liens internes
        for h in set(re.findall(r'href="([^"]+)"', s)):
            if h.startswith(('http', 'mailto:', 'tel:', '#', '/api')):
                continue
            p = h.split('#')[0].split('?')[0].lstrip('/')
            if p and not os.path.exists(p):
                pb.append((f, 'lien mort : ' + h))

        # 7. navigation complete et repere principal
        if len(re.findall(r'<a href="[^"]+"[^>]*><i>\d+</i><span data-t="n\d+"', s)) != 11:
            pb.append((f, 'navigation incomplete'))
        if s.count('<main id="contenu">') != 1:
            pb.append((f, 'balise <main> absente ou en double'))

        # 8. donnees structurees valides
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
        if m:
            try:
                json.loads(m.group(1))
            except Exception as e:
                pb.append((f, 'JSON-LD invalide : %s' % e))
        elif f not in SANS_JSONLD:
            pb.append((f, 'JSON-LD absent'))

        # 9. une barre collante doit avoir son rideau
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
