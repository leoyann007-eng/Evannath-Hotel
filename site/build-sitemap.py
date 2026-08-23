# -*- coding: utf-8 -*-
"""Genere sitemap.xml, robots.txt et site.webmanifest.

A relancer apres toute creation ou suppression de page. Les pages portant
<meta name="robots" content="noindex"> (reserver, mentions-legales, 404) sont
exclues du sitemap : elles n'ont rien a faire dans l'index de Google.
"""
import io, os, glob, datetime, sys
sys.path.insert(0, '.')
from _chrome import SITE

# Priorite editoriale : ce que l'hotel veut voir remonter en premier.
PRIORITE = {
 'index': '1.0',
 'seminaires': '0.9', 'circuits': '0.9', 'carte': '0.9',
 'experiences': '0.8', 'spa': '0.8', 'galerie': '0.8', 'contact': '0.8',
 'suite-arabe': '0.7', 'mezzanine-superieure': '0.7', 'chambre-mezzanine': '0.7',
 'suite-anglaise': '0.7', 'deluxe-superieure': '0.7', 'deluxe-baldaquin': '0.7',
 'chambre-standard': '0.7',
 'a-propos': '0.6', 'informations-utiles': '0.6',
}
IGNORE = {'index-luxe-variante', 'carte-template', 'spa-template'}

pages = []
for f in sorted(glob.glob('*.html')):
    slug = f[:-5]
    if slug in IGNORE:
        continue
    contenu = io.open(f, encoding='utf-8').read()
    if 'name="robots" content="noindex' in contenu:
        continue
    pages.append((slug, PRIORITE.get(slug, '0.5'),
                  datetime.date.fromtimestamp(os.path.getmtime(f)).isoformat()))

lignes = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for slug, prio, maj in sorted(pages, key=lambda p: (-float(p[1]), p[0])):
    loc = SITE + ('/' if slug == 'index' else '/' + slug)
    lignes.append('  <url>')
    lignes.append('    <loc>%s</loc>' % loc)
    lignes.append('    <lastmod>%s</lastmod>' % maj)
    lignes.append('    <changefreq>%s</changefreq>' % ('weekly' if float(prio) >= 0.9 else 'monthly'))
    lignes.append('    <priority>%s</priority>' % prio)
    lignes.append('  </url>')
lignes.append('</urlset>')
io.open('sitemap.xml', 'w', encoding='utf-8').write('\n'.join(lignes) + '\n')

io.open('robots.txt', 'w', encoding='utf-8').write(
"""User-agent: *
Allow: /

# Pages sans interet pour l'index : formulaire de reservation et pages legales.
Disallow: /reserver
Disallow: /mentions-legales

Sitemap: %s/sitemap.xml
""" % SITE)

io.open('site.webmanifest', 'w', encoding='utf-8').write(
"""{
  "name": "Hôtel Evannath — Le Rêve Africain",
  "short_name": "Evannath",
  "description": "46 chambres et suites face à la lagune Aby, à Assinie PK 19.",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#17100A",
  "theme_color": "#17100A",
  "lang": "fr",
  "icons": [
    { "src": "/favicon-32.png", "sizes": "32x32", "type": "image/png" },
    { "src": "/apple-touch-icon.png", "sizes": "180x180", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icon-512-transparent.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
""")

print('sitemap.xml           %d pages indexables' % len(pages))
print('robots.txt            ok')
print('site.webmanifest      ok')
