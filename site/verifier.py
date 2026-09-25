# -*- coding: utf-8 -*-
"""Controles de coherence sur les pages generees.

A lancer apres les generateurs. Chaque controle correspond a un defaut qui est
reellement survenu sur ce projet — ils sont la pour qu'il ne revienne pas.
"""
import io, os, re, glob, json, sys, subprocess, tempfile
sys.path.insert(0, '.')
from _chrome import TOKENS, NAV_BASE, LANG_JS, FOOTER_CSS, empreinte, WA, MAIL

_cache = {}


def _taille_de(chemin):
    if chemin not in _cache:
        from PIL import Image
        _cache[chemin] = Image.open(chemin).size
    return _cache[chemin]


def _largeur_de(chemin):
    return _taille_de(chemin)[0]


# node sert au controle 13. Absent, le controle est saute — mieux vaut un
# verificateur qui tourne partout qu'un verificateur qui refuse de demarrer.
import shutil
_node = shutil.which('node')

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
            # Une cle portant un tiret DOIT etre quotee — JavaScript refuse
            # « q-packs-vacances: » sans guillemets. Les deux formes sont donc
            # legitimes, et le controle doit lire les deux.
            declarees = re.findall(r'(?:^|,)\s*"?([\w-]+)"?\s*:', bloc)
            traduites = set(declarees)
            doublons = sorted({k for k in declarees if declarees.count(k) > 1})
            if doublons:
                pb.append((f, 'cles de traduction redefinies : ' + ' '.join(doublons)))
            # Deux elements qui partagent une cle mais portent des textes
            # francais differents : en anglais, le second ecrase le premier.
            # Le controle 7 quater ne voyait que les doublons du DICTIONNAIRE,
            # pas ceux du HTML. C'est arrive en renommant une cle de section
            # qui servait deja a la description de la lune de miel.
            textes = {}
            for cle, txt in re.findall(r'data-t="([\w-]+)"[^>]*>([^<]{3,})', s):
                t = ' '.join(txt.split())
                if cle in textes and textes[cle] != t:
                    pb.append((f, 'cle « %s » posee sur deux textes differents' % cle))
                textes[cle] = t

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

        # 11 bis. la classe .wa est celle du bouton flottant, et rien d'autre.
        # Elle impose position:fixed et 56x56 en rond : le lien du panneau de
        # repli la portait, se retrouvait arrache du panneau en pastille au
        # coin de l'ecran, et le bouton le plus utile du repli etait invisible.
        if s.count('class="wa"') != 1:
            pb.append((f, 'class="wa" doit servir au seul bouton flottant'))
        if 'class="secours"' in s and s.count('class="wa-envoi"') != 1:
            pb.append((f, 'lien WhatsApp du panneau de repli absent ou en double'))

        # 11 ter. tous les liens WhatsApp du site vont au meme numero,
        # celui du moment. Pendant les tests c'est le prestataire ; a la mise
        # en ligne, l'etablissement. Une demande partie au mauvais endroit ne
        # se rattrape pas, et personne ne relit 21 pages a la main.
        #
        # On ne controle QUE les liens wa.me. Le numero de la reception
        # apparait aussi en tel: sur chaque page — c'est « Appeler la
        # reception », et c'est normal. Une version anterieure de ce controle
        # confondait les deux et signalait les 21 pages.
        autres = set(re.findall(r'wa\.me/(\d+)', s)) - {WA}
        if autres:
            pb.append((f, 'lien WhatsApp vers %s' % ', '.join(sorted(autres))))
        # 11 quater. meme regle pour l'adresse e-mail : une seule sur tout
        # le site, celle du moment. Elle etait ecrite en dur a 139 endroits
        # dans douze fichiers ; il en suffit d'un oublie pour qu'une demande
        # parte au mauvais endroit, et cela ne se voit sur aucune page.
        adresses = set(re.findall(r'mailto:([\w.+-]+@[\w.-]+\.\w+)', s)) - {MAIL}
        if adresses:
            pb.append((f, 'mailto vers %s' % ', '.join(sorted(adresses))))

        # 13. le JavaScript de la page doit se parser.
        # Une erreur de syntaxe ne se VOIT pas : la page s'affiche, mais tout
        # son comportement disparait d'un coup — bascule de langue, tiroir,
        # apparition au defilement, expiration des affiches. C'est arrive avec
        # une cle de dictionnaire portant un tiret, « q-packs-vacances », que
        # JavaScript refuse sans guillemets.
        if _node:
            for i, js in enumerate(re.findall(
                    r'<script(?![^>]*(?:src=|type="application))[^>]*>(.*?)</script>',
                    s, re.S)):
                if not js.strip():
                    continue
                tmp = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False,
                                                  encoding='utf-8')
                tmp.write(js); tmp.close()
                r = subprocess.run([_node, '--check', tmp.name],
                                   capture_output=True, text=True)
                os.unlink(tmp.name)
                if r.returncode:
                    detail = [l for l in r.stderr.split(chr(10)) if 'Error' in l]
                    pb.append((f, 'script %d invalide : %s'
                               % (i + 1, (detail or ['?'])[0].strip()[:70])))

        # 14. une image reconstruite en JavaScript efface le srcset du modele.
        # Le carrousel clone une diapositive generee pour y poser l'evenement
        # publie depuis l'administration. Le clone porte le srcset d'une photo
        # du site, et srcset l'emporte sur src : l'affiche deposee par l'hotel
        # ne s'affichait jamais, on voyait la photo du modele a sa place. Le
        # defaut est invisible — une image s'affiche, simplement pas la bonne.
        # On ne vise que les <img> reprises d'un modele existant. Une image
        # construite de zero — la visionneuse, une source video — n'herite
        # d'aucun srcset et n'a rien a effacer.
        for js in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', s, re.S):
            if 'cloneNode' not in js:
                continue
            reprises = set(re.findall(
                r"""(\w+)\s*=\s*[^;
]*\.querySelector\(['\"]img""", js))
            for pose in reprises:
                if re.search(r'\b%s\.src\s*=' % pose, js) \
                        and ("%s.removeAttribute('srcset')" % pose) not in js:
                    pb.append((f, "%s.src posé sur une image reprise d'un"
                               " modèle sans effacer son srcset" % pose))

        # Le controle 12 — rideau des barres collantes — a disparu avec le
        # mecanisme lui-meme : les barres de filtres ne sont plus collantes.

        # 16. le pied de page doit venir de la source partagee.
        # La table et Le spa ne consomment pas HEAD_CSS — leur CSS surcharge
        # des regles de base, et une fusion complete avait ete tentee puis
        # abandonnee. Elles portaient donc une COPIE du pied, qui a diverge :
        # le copyright y etait a 3,1:1 DEJA sur le site noir, et le passage au
        # creme l'a laisse derriere. Une correction au chassis manquait ces
        # deux pages, en silence. Le bloc doit donc se retrouver AU MOT dans
        # chaque page : le recopier en le modifiant casse ce controle.
        if FOOTER_CSS.strip() not in s:
            pb.append((f, 'pied de page divergent de FOOTER_CSS'))

        # 15. aucune page ne peut affirmer une disponibilite dans son balisage.
        # Les sept fiches chambres ont porte pendant des mois une pastille
        # verte et « Disponible a ces dates », ecrite en dur, affichee quelles
        # que soient les dates choisies. C'etait la seule phrase du site que
        # rien ne soutenait. Elle ne peut desormais venir que de DISPO_JS,
        # a partir du verdict du serveur — donc d'un <script>, jamais du
        # balisage. On retire les scripts avant de chercher : le module et le
        # dictionnaire anglais ont parfaitement le droit de contenir ces mots.
        sans_js = re.sub(r'<script[^>]*>.*?</script>', ' ', s, flags=re.S)
        for phrase in ('Disponible à ces dates', 'Available on these dates',
                       'Dernière chambre à ces dates', 'Last room at these dates',
                       'Complet à ces dates', 'Fully booked on these dates'):
            if phrase in sans_js:
                pb.append((f, 'disponibilite affirmee dans le balisage : « %s »'
                           ' — elle doit venir de DISPO_JS' % phrase))

    # 20. tout ce qui est sous /admin doit etre en no-store, /admin COMPRIS.
    # La regle « /admin/(.*) » exige quelque chose APRES la barre : elle
    # couvrait disponibilites.css et .js, mais pas /admin lui-meme. La page
    # qui porte toute l'interface, derriere mot de passe, etait donc marquee
    # « public, must-revalidate » et stockable, pendant que ses fichiers
    # etaient proteges. Un motif qui a l'air complet et qui laisse passer sa
    # propre racine : la prochaine regle de ce genre fera pareil.
    if os.path.exists('vercel.json'):
        conf = json.loads(io.open('vercel.json', encoding='utf-8').read())
        sans_cache = set()
        for regle in conf.get('headers', []):
            for h in regle.get('headers', []):
                if h.get('key', '').lower() == 'cache-control'                         and 'no-store' in h.get('value', ''):
                    sans_cache.add(regle.get('source'))
        for attendu in ('/admin', '/admin/(.*)'):
            if attendu not in sans_cache:
                pb.append(('vercel.json', 'aucune regle no-store pour « %s » : '
                           "une page derriere mot de passe ne doit pas etre stockee"
                           % attendu))

    # 19. le back-office a DEUX fonds, donc deux logos.
    # Le controle 18 verifie les 21 pages du site. Le back-office y echappait,
    # et le defaut s'y est reproduit tel quel : sa barre laterale est passee au
    # marine, et le logo bronze y est tombe a 2,57:1 — invisible. La regle est
    # la meme, la mesure aussi : un logo est une image, et le balayage de
    # contraste ne voit que du texte.
    #
    # L'ecran de connexion est clair (--bark), la barre laterale est sombre
    # (--night). Chacun son logo, et c'est verifiable sans regarder un pixel.
    admin = 'admin/index.html'
    if os.path.exists(admin):
        a = io.open(admin, encoding='utf-8').read()
        porte = re.search(r'<div id="porte">(.*?)</div>\s*<!--', a, re.S)             or re.search(r'<div id="porte">(.*?)</form>', a, re.S)
        barre = re.search(r'<div class="marque">(.*?)</div>', a, re.S)
        if porte and 'logo-bronze.png' not in porte.group(1):
            pb.append((admin, 'ecran de connexion : fond clair, le logo bronze '
                       'est attendu'))
        if barre and 'logo-blanc.png' not in barre.group(1):
            pb.append((admin, 'barre laterale : fond marine, le logo blanc '
                       'est attendu'))

    # 17. chaque entree du menu du back-office doit peindre quelque chose.
    # Un decoupage du tableau de bord, ancre sur la branche suivante, a emporte
    # les trois branches qui vivaient entre les deux : evenements, promotions,
    # campagnes et galerie. Le fichier se parsait, aucune erreur en console,
    # et le menu s'allumait bien. Mais rendre() n'ecrivait plus rien : on
    # cliquait « Evenements » et la vue precedente restait a l'ecran. Un
    # defaut muet, que seul un clic sur les huit entrees pouvait trouver.
    admin = 'admin/index.html'
    if os.path.exists(admin):
        a = io.open(admin, encoding='utf-8').read()
        # Le corps de rendre(), du mot-cle jusqu'a l'accolade de la marge.
        m = re.search(r'function rendre\(\) \{(.*?)\n\}', a, re.S)
        if not m:
            pb.append((admin, 'rendre() est introuvable'))
        else:
            corps = m.group(1)
            for v in sorted(set(re.findall(r'data-v="([\w-]+)"', a))):
                if ("VUE === '%s'" % v) not in corps:
                    pb.append((admin, 'le menu mene a « %s », mais rendre() '
                               "n'a pas de branche pour cette vue" % v))

    # 18. le logo doit contraster avec le fond sur lequel il est pose.
    # Le site est passe au creme, l'en-tete est devenu creme a 90 % et le
    # pied --bark-2 ; le logo, lui, est reste blanc. Sur l'accueil on en
    # devinait un fantome a travers la transparence, sur les dix-huit autres
    # pages claires il n'y avait plus rien. Aucun outil ne l'a vu : le
    # balayage de contraste ne mesure que du TEXTE, et un logo est une image.
    #
    # La regle se verifie pourtant sans regarder un pixel : une page claire
    # reference le logo bronze, une page nocturne le logo blanc. La table et
    # Le spa sont les deux seules nocturnes, et elles se reconnaissent a leur
    # fond de pied ecrit en clair.
    for f in pages:
        s = io.open(f, encoding='utf-8').read()
        nocturne = 'footer{background:#0B0704}' in s
        attendu = 'logo-blanc.png' if nocturne else 'logo-bronze.png'
        refuse = 'logo-bronze.png' if nocturne else 'logo-blanc.png'
        if refuse in s:
            pb.append((f, 'page %s : le logo %s y est pose sur son propre fond'
                       % ('nocturne' if nocturne else 'claire', refuse)))
        elif attendu not in s:
            pb.append((f, 'aucun logo : %s est attendu' % attendu))

    # 21. le seuil de repli de la barre doit suivre la feuille de style.
    # La barre laterale se replie d'elle-meme quand la vue courante ne tient
    # plus. Pour le mois, « ne tient plus » a un sens precis : une case perd
    # sa seconde colonne de compteurs. Ce chiffre vient de .m-g et de .m-c,
    # pas du JavaScript — deux fois 64 px de piste, la gouttiere, les deux
    # marges interieures et le filet.
    #
    # Le calcul precedent valait 140 + 31 x 34 px : la largeur du PLANNING
    # mensuel, qui n'existe plus depuis que le mois est devenu un calendrier.
    # Il tombait juste a 60 px pres, par accident, et personne ne pouvait le
    # voir — la barre se repliait a peu pres au bon moment. Le prochain
    # accident ne tombera pas juste : on relie donc les deux bouts.
    css, adm = 'admin/disponibilites.css', 'admin/index.html'
    if os.path.exists(css) and os.path.exists(adm):
        c = io.open(css, encoding='utf-8').read()
        a = io.open(adm, encoding='utf-8').read()
        mg = re.search(r'\.m-g\{[^}]*?minmax\((\d+)px[^}]*?gap:\s*\d+px\s+(\d+)px', c, re.S)
        mc = re.search(r'\.m-c\{[^}]*?padding:\s*\d+px\s+(\d+)px', c, re.S)
        js = re.search(r'MENU_CASE_MOIS\s*=\s*(\d+)', a)
        if not (mg and mc):
            pb.append((css, 'le gabarit d une case du mois est introuvable : '
                       'le controle 21 ne peut plus rien affirmer'))
        elif not js:
            pb.append((adm, 'MENU_CASE_MOIS est introuvable : la barre ne sait '
                       'plus a quelle largeur le mois cesse de tenir'))
        else:
            attendu = 2 * int(mg.group(1)) + int(mg.group(2)) + 2 * int(mc.group(1)) + 1
            if int(js.group(1)) != attendu:
                pb.append((adm, 'MENU_CASE_MOIS vaut %s, la feuille de style en '
                           'demande %d : la barre se replie au mauvais moment'
                           % (js.group(1), attendu)))
        # Et le mois ne peut pas se mesurer en colonnes de planning : ce
        # gabarit-la appartient a la semaine.
        besoin = re.search(r'function besoinContenu\(\)\s*\{(.*?)\n\}', a, re.S)
        if besoin and 'DSP_COL' in besoin.group(1):
            pb.append((adm, 'besoinContenu() se sert de DSP_COL : c est la '
                       'colonne du PLANNING, le mois est un calendrier'))

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
