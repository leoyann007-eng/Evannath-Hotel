# -*- coding: utf-8 -*-
"""Genere sitemap.xml, robots.txt et site.webmanifest.

A relancer apres toute creation ou suppression de page, et en DERNIER, apres
les autres generateurs : il lit les pages produites.

    python build-sitemap.py

Le sitemap declare chaque page indexable, sa date de derniere modification
(celle du dernier commit qui l'a touchee) et les photos qu'elle montre — un
hotel se choisit sur Google Images autant que sur les liens bleus.

Mode prospection (_chrome.PROSPECTION) : le sitemap est ecrit sous le nom
sitemap-apercu.xml, que .vercelignore garde hors ligne. On peut le relire, il
ne part pas. Le jour de la mise en ligne, PROSPECTION = False : sitemap.xml
est servi, robots.txt le declare, et la regle X-Robots-Tag de vercel.json est
retiree — ici, automatiquement.
"""
import io, os, re, glob, json, datetime, subprocess, sys
from xml.sax.saxutils import escape
sys.path.insert(0, '.')
from _chrome import SITE, PROSPECTION, CHAMBRES_ANNONCEES

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
IGNORE = {'index-luxe-variante', 'index-template', 'carte-template', 'spa-template'}
# Hors index, quel que soit le mode : le tunnel de reservation, les mentions
# legales et la page d'erreur portent leur propre noindex. La liste est
# ecrite ici plutot que devinee dans le HTML : en prospection, TOUTES les
# pages portent noindex, et la detection videait le sitemap.
HORS_INDEX = {'reserver', 'mentions-legales', '404'}

AUJOURD_HUI = datetime.date.today().isoformat()

def date_de(f):
    """Le dernier commit qui a touche la page — pas l'heure du fichier, que
    chaque regeneration remet a aujourd'hui. Une page modifiee et pas encore
    commitee date d'aujourd'hui."""
    try:
        sale = subprocess.run(['git', 'status', '--porcelain', '--', f],
                              capture_output=True, text=True).stdout.strip()
        if sale:
            return AUJOURD_HUI
        d = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', f],
                           capture_output=True, text=True).stdout.strip()
        return d or AUJOURD_HUI
    except OSError:
        return datetime.date.fromtimestamp(os.path.getmtime(f)).isoformat()

# Les photos d'une page : ses <img> et son og:image. On remonte de la
# vignette ou du palier responsive (-t, -640…) a l'original quand il existe,
# et on laisse de cote ce qui n'est pas une photo (logos, icones, SVG).
_palier = re.compile(r'-(640|1024|1600|t|t360)(\.\w+)$')
def photos_de(html):
    vues = []
    for src in re.findall(r'<img\b[^>]*?\ssrc="([^"]+)"', html) + \
               re.findall(r'<meta property="og:image" content="([^"]+)"', html):
        chemin = src.replace(SITE, '').lstrip('/')
        if not chemin.startswith('img/opt/') or not re.search(r'\.(jpe?g|webp|png)$', chemin):
            continue
        if 'logo' in chemin or 'icon' in chemin:
            continue
        orig = _palier.sub(r'\2', chemin)
        chemin = orig if os.path.exists(orig) else chemin
        if chemin not in vues:
            vues.append(chemin)
    return vues

pages = []
for f in sorted(glob.glob('*.html')):
    slug = f[:-5]
    if slug in IGNORE or slug in HORS_INDEX:
        continue
    contenu = io.open(f, encoding='utf-8').read()
    loc = SITE + ('/' if slug == 'index' else '/' + slug)
    # Le sitemap et la page doivent dire la meme adresse : une canonical qui
    # diverge, et Google ignore l'entree.
    canon = re.search(r'<link rel="canonical" href="([^"]+)"', contenu)
    if not canon or canon.group(1) != loc:
        sys.exit('ERREUR %s : canonical %s, attendu %s'
                 % (f, canon.group(1) if canon else 'absente', loc))
    pages.append((slug, PRIORITE.get(slug, '0.5'), date_de(f), loc, photos_de(contenu)))

# ── Inventaire des photos, pour le selecteur d'images de l'administration ──
# On ne liste que les originaux : ni les paliers responsives (-640, -1024,
# -1600), ni les vignettes, ni les affiches de video.
import json, re
os.makedirs('donnees', exist_ok=True)
_ecart = re.compile(r'-(640|1024|1600|t|t360)$')
_photos = sorted({
    os.path.basename(f)[:-4] for f in glob.glob('img/opt/*.jpg')
    if not _ecart.search(os.path.basename(f)[:-4])
    and not os.path.basename(f).endswith('-affiche.jpg')
})
io.open('donnees/images.json', 'w', encoding='utf-8').write(
    json.dumps(_photos, ensure_ascii=False))
print('donnees/images.json     %d photos' % len(_photos))

# La liste des chambres, pour l'administration : une promotion s'applique a
# des chambres precises, et l'interface doit pouvoir les proposer avec leur
# tarif sans que personne ne les ressaisisse.
#
# `pax` vient avec : la fiche d'une chambre, dans l'administration, dit sa
# capacite. Le type de lit n'y est PAS — une seule des sept categories le
# declare dans ses `facts`, et inventer les six autres serait afficher a la
# reception une information que l'hotel n'a jamais donnee.
import _chambres
# `photo` : la PREMIERE photo declaree pour la categorie, celle que le site
# montre en tete de sa fiche. La carte ecrite a la main dans le calendrier
# se trompait sur six categories sur sept — elle donnait a « Deluxe · lits a
# baldaquin » une photo de textiles wax, qui est celle de la Deluxe
# Superieure, et intervertissait les deux Mezzanines. Une carte recopiee
# diverge ; celle-ci se deduit.
def _vignette(c):
    nom = c['photos'][0][0]
    return nom + '-640' if os.path.exists('img/opt/%s-640.jpg' % nom) else nom

# Le lit, tel que la fiche l'annonce (« Queen », « Baldaquin ») : le
# back-office le propose en EXEMPLE pour une chambre de la categorie, sans
# le lui attribuer. Absent quand la fiche n'en dit rien.
def _lit(c):
    return next((v for v, l in c['facts'] if l in ('lit', 'lits')), '')

_ch = [dict(slug=c['slug'], nom=c['nom'], prix=c['prix'], pax=c['pax'],
            photo=_vignette(c), lit=_lit(c))
       for c in _chambres.CHAMBRES]
io.open('donnees/chambres.json', 'w', encoding='utf-8').write(
    json.dumps(_ch, ensure_ascii=False))
print('donnees/chambres.json   %d chambres' % len(_ch))

# Ce que le site annonce, pour que l'administration puisse le comparer a ce
# que la reception a reellement saisi.
io.open('donnees/hotel.json', 'w', encoding='utf-8').write(
    json.dumps({'chambres_annoncees': CHAMBRES_ANNONCEES}, ensure_ascii=False))
print('donnees/hotel.json      %d chambres annoncees' % CHAMBRES_ANNONCEES)

# changefreq et priority ne sont plus lus par Google ; on garde priority pour
# Bing et pour l'ordre du fichier, qui se relit mieux de l'accueil vers le bas.
lignes = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
          '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
nb_photos = 0
for slug, prio, maj, loc, photos in sorted(pages, key=lambda p: (-float(p[1]), p[0])):
    lignes.append('  <url>')
    lignes.append('    <loc>%s</loc>' % escape(loc))
    lignes.append('    <lastmod>%s</lastmod>' % maj)
    lignes.append('    <priority>%s</priority>' % prio)
    for p in photos[:1000]:                       # plafond du protocole
        lignes.append('    <image:image><image:loc>%s/%s</image:loc></image:image>'
                      % (SITE, escape(p)))
        nb_photos += 1
    lignes.append('  </url>')
lignes.append('</urlset>')
xml = '\n'.join(lignes) + '\n'

# En prospection : sitemap-apercu.xml, relisible en local, jamais servi
# (.vercelignore). En publier un reviendrait a inviter les robots sur une
# maquette qui porte la marque de l'hotel.
NOM = 'sitemap-apercu.xml' if PROSPECTION else 'sitemap.xml'
io.open(NOM, 'w', encoding='utf-8', newline='\n').write(xml)
for vieux in {'sitemap.xml', 'sitemap-apercu.xml'} - {NOM}:
    if os.path.exists(vieux):
        os.remove(vieux)

# La regle X-Robots-Tag de vercel.json suit le mode : posee en prospection,
# retiree a la mise en ligne. Oublier de la retirer a la main laisserait le
# site invisible de Google malgre tout le reste — ce n'est plus a retenir.
REGLE_NOINDEX = {'source': '/(.*)', 'headers': [
    {'key': 'X-Robots-Tag', 'value': 'noindex, nofollow, noarchive, noimageindex'}]}
_vc = json.load(io.open('vercel.json', encoding='utf-8'))
_a = REGLE_NOINDEX in _vc['headers']
if PROSPECTION != _a:
    if PROSPECTION:
        _vc['headers'].append(REGLE_NOINDEX)
    else:
        _vc['headers'].remove(REGLE_NOINDEX)
    io.open('vercel.json', 'w', encoding='utf-8', newline='\n').write(
        json.dumps(_vc, indent=2, ensure_ascii=False) + '\n')
    print('vercel.json           regle X-Robots-Tag ' + ('posee' if PROSPECTION else 'retiree'))

# La politique de securite du contenu : les empreintes des scripts des pages
# telles qu'elles viennent d'etre generees. Voir _csp.py.
import _csp
_vc = json.load(io.open('vercel.json', encoding='utf-8'))
_valeur = _csp.politique(_csp.toutes_les_empreintes())
_regle = next(r for r in _vc['headers'] if r['source'] == '/(.*)'
              and any(h['key'] == 'X-Content-Type-Options' for h in r['headers']))
_h = next((h for h in _regle['headers'] if h['key'] == 'Content-Security-Policy'), None)
if not _h or _h['value'] != _valeur:
    if _h: _h['value'] = _valeur
    else: _regle['headers'].append({'key': 'Content-Security-Policy', 'value': _valeur})
    io.open('vercel.json', 'w', encoding='utf-8', newline='\n').write(
        json.dumps(_vc, indent=2, ensure_ascii=False) + '\n')
print('vercel.json           CSP : %d scripts autorises par empreinte' % len(_csp.toutes_les_empreintes()))

if PROSPECTION:
    # Maquette de prospection : on laisse crawler pour que la directive noindex
    # (balise meta + en-tete X-Robots-Tag) soit effectivement LUE. Un
    # « Disallow: / » empecherait justement les robots de la lire, et l'URL nue
    # pourrait rester indexee. Aucun sitemap n'est declare : on n'invite pas.
    io.open('robots.txt', 'w', encoding='utf-8').write(
"""# Maquette de demonstration. Ce site ne doit apparaitre dans aucun index :
# chaque page sert noindex, en balise meta et en en-tete HTTP.
User-agent: *
Allow: /

Disallow: /api/
""")
else:
    # Reserver, mentions legales et 404 restent CRAWLABLES : elles portent
    # noindex, et un Disallow empecherait Google de le lire — l'URL nue
    # pourrait alors apparaitre dans les resultats, sans titre ni texte.
    io.open('robots.txt', 'w', encoding='utf-8').write(
"""User-agent: *
Allow: /

Disallow: /api/

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

print('%-21s %d pages, %d photos%s' % (NOM, len(pages), nb_photos,
      ' (apercu local, non servi : mode prospection)' if PROSPECTION else ''))
print('robots.txt            ok')
print('site.webmanifest      ok')
