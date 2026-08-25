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

        # 7 ter. la mosaique des fiches chambres doit se remplir exactement.
        # La grille a trois colonnes place la premiere image sur deux rangees ;
        # a trois photos, la seconde rangee restait vide — 27 % de trou sur six
        # fiches. A deux colonnes, un nombre pair laisse une case vide en fin
        # de grille. Les deux cas se corrigent par une classe, encore faut-il
        # qu'elle soit la.
        mo = re.search(r'<div class="mosaic([^"]*)" id="gl">(.*?)</div>\s*</div>', s, re.S)
        if mo:
            classes, corps = mo.group(1), mo.group(2)
            n = corps.count('<figure')
            if n < 5 and 'court' not in classes:
                pb.append((f, 'mosaique : %d photos sans la classe « court » '
                              '— trou sous la premiere image' % n))
            if n >= 5 and 'court' in classes:
                pb.append((f, 'mosaique : %d photos avec la classe « court »' % n))
            etale = 'class="plein"' in corps
            if n % 2 == 0 and not etale:
                pb.append((f, 'mosaique : %d photos, derniere case vide a deux '
                              'colonnes — classe « plein » manquante' % n))
            if n % 2 and etale:
                pb.append((f, 'mosaique : %d photos, la classe « plein » est de trop' % n))

        # 7 quater. le bouton EN doit tout traduire, pas seulement le menu.
        # Dix pages ne portaient de data-t que sur la navigation : cliquer EN
        # faisait basculer le menu et laissait la page en francais. Pire que
        # pas de bouton du tout. On exige donc qu'aucune cle declaree ne soit
        # absente du dictionnaire — et qu'aucune cle du dictionnaire ne soit
        # redefinie, un sommaire ayant deja ecrase les libelles du menu.
        i = s.find('var EN={')
        if i < 0:
            pb.append((f, 'aucun dictionnaire de traduction'))
        else:
            bloc = s[i + 8:]
            bloc = bloc[:bloc.find('};')]
            declarees = re.findall(r'(?:^|,)\s*([\w-]+)\s*:', bloc)
            traduites = set(declarees)
            doublons = sorted({k for k in declarees if declarees.count(k) > 1})
            if doublons:
                pb.append((f, 'cles de traduction redefinies : ' + ' '.join(doublons)))
            # Une page peut declarer que son corps reste en francais — un
            # document juridique, dont la version francaise fait foi. La
            # decision doit etre ecrite dans le generateur, pas subie ici.
            manque = sorted(set(re.findall(r'data-t="([\w-]+)"', s)) - traduites)
            if 'EVN_FR_FAIT_FOI' in s:
                manque = []
            if manque:
                pb.append((f, '%d segment(s) sans traduction anglaise : %s'
                           % (len(manque), ' '.join(manque[:8])
                              + (' …' if len(manque) > 8 else ''))))

        # 7 quinquies. sur la page des offres, le catalogue declare a Google
        # et le menu de reservation doivent lister exactement les memes
        # offres, aux memes prix et aux memes unites. Deux sources ecrites
        # separement finissent toujours par diverger, et l'ecart ne se voit
        # nulle part : le visiteur ne lit pas le JSON-LD, le moteur ne lit pas
        # le menu.
        if f == 'circuits.html':
            unites = {'forfait': 'le forfait', 'personne': 'par personne',
                      'enfant': 'par enfant'}
            menu = {}
            for prix, u, lib in re.findall(
                    r'<option value="(\d+)\|([a-z]+)">([^<]+)</option>', s):
                menu[lib.split('—')[0].strip()] = (prix, unites.get(u, u))
            cat = {}
            for graphe in re.findall(
                    r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
                for e in json.loads(graphe).get('@graph', []):
                    for o in e.get('hasOfferCatalog', {}).get('itemListElement', []):
                        cat[o['name']] = (
                            o.get('price', ''),
                            o.get('priceSpecification', {}).get('unitText', ''))
            if not cat:
                pb.append((f, 'les offres ne sont declarees dans aucun catalogue'))
            for nom in sorted(set(cat) | set(menu)):
                if nom not in cat:
                    pb.append((f, 'offre « %s » reservable mais absente du catalogue' % nom))
                elif nom not in menu:
                    pb.append((f, 'offre « %s » declaree mais non reservable' % nom))
                elif cat[nom] != menu[nom]:
                    pb.append((f, 'offre « %s » : %s dans le catalogue, %s dans le menu'
                               % (nom, cat[nom], menu[nom])))

        # 7 sexies. les quatre offres mises en avant sur l'accueil affichent
        # un tarif ecrit en dur. Il doit correspondre a celui de la page des
        # circuits, seule source de verite. Une remise saisonniere appliquee
        # d'un cote et pas de l'autre donnerait deux prix pour la meme offre.
        if f == 'index.html' and 'id="offres"' in s:
            bloc = s[s.find('id="offres"'):]
            bloc = bloc[:bloc.find('</section>')]
            accueil = {}
            for m in re.finditer(r'data-t="ot\d+">([^<]+)</h3>.*?'
                                 r'<b>([\d\s ]+)</b>', bloc, re.S):
                accueil[m.group(1).strip()] = m.group(2).replace(' ', '').replace(' ', '')
            ref = {}
            try:
                c = io.open('circuits.html', encoding='utf-8').read()
                for graphe in re.findall(
                        r'<script type="application/ld\+json">(.*?)</script>', c, re.S):
                    for e in json.loads(graphe).get('@graph', []):
                        for o in e.get('hasOfferCatalog', {}).get('itemListElement', []):
                            ref[o['name']] = o.get('price', '')
            except OSError:
                pb.append((f, 'circuits.html introuvable, tarifs non verifiables'))
            if not accueil:
                pb.append((f, 'section offres presente mais aucun tarif lisible'))
            for nom, prix in sorted(accueil.items()):
                if nom not in ref:
                    pb.append((f, 'offre « %s » mise en avant mais absente des circuits' % nom))
                elif prix != ref[nom]:
                    pb.append((f, 'offre « %s » : %s sur l accueil, %s sur les circuits'
                               % (nom, prix, ref[nom])))

        # 7 septies. le contenu ne doit pas dependre du JavaScript pour etre
        # visible. .reveal masque les blocs en attendant qu'un script leur
        # pose .in ; si ce script ne s'execute pas, la page garde sa hauteur
        # et reste vide sous l'en-tete. Le masquage est donc conditionne a la
        # classe « js », et un secours revele tout au bout de 3 s si le script
        # principal n'a jamais signale son passage.
        if '.reveal' in s:
            # On lit les regles une par une : un selecteur qui masque .reveal
            # doit etre porte par la classe « js ». Chercher le motif brut
            # attrapait aussi « .js .reveal », donc ne detectait rien.
            for regle in re.finditer(r'([^{}]+)\{([^}]*)\}', s):
                sel, decl = regle.group(1), regle.group(2)
                if '.reveal' not in sel or 'opacity' not in decl:
                    continue
                if not re.search(r'opacity\s*:\s*0(?![.\d])', decl):
                    continue
                if '.js' not in sel:
                    pb.append((f, 'masquage .reveal non conditionne a la classe js '
                                  '— page vide si le script ne tourne pas : '
                                  + sel.strip()[:50]))
            if '__reveal' not in s:
                pb.append((f, 'secours de revelation absent du <head>'))

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
