# Hôtel Evannath — maquette de refonte

Maquette complète proposée à l'**Hôtel Evannath** (Assinie PK 19, Côte d'Ivoire)
en remplacement de [evannathhotel.com](https://evannathhotel.com).

Site statique, sans dépendance ni framework : du HTML, du CSS et du JavaScript
sans bibliothèque. Les pages riches en données sont générées par des scripts
Python à partir de gabarits, pour éviter la saisie manuelle.

> ⚠️ **Ceci est une démonstration.** Certaines informations (horaires, conditions
> d'annulation, acompte, taxe de séjour) sont plausibles mais **inventées** :
> elles n'existent nulle part sur le site d'origine et doivent être confirmées
> par l'établissement avant toute mise en production. Voir « À valider » plus bas.

---

## Les 19 pages

**Le parcours de réservation**

| Fichier | Page |
|---|---|
| `index.html` | Accueil — hero, recherche, 7 catégories, expériences, avis, accès |
| `chambre-standard.html` | Chambre Standard — 67 000 FCFA |
| `deluxe-baldaquin.html` | Deluxe · lits à baldaquin — 82 000 FCFA |
| `deluxe-superieure.html` | Deluxe Supérieure — 97 000 FCFA |
| `suite-anglaise.html` | Suite Anglaise — 107 000 FCFA |
| `chambre-mezzanine.html` | Chambre en Mezzanine — 127 000 FCFA |
| `mezzanine-superieure.html` | Mezzanine Supérieure — 142 000 FCFA |
| `suite-arabe.html` | Suite Arabe — 280 000 FCFA |
| `reserver.html` | Tunnel de réservation en trois étapes |

**Les autres pages**

| Fichier | Page |
|---|---|
| `chambres.html` | Page mère des 7 catégories : filtres, tri, comparateur |
| `galerie.html` | 47 photographies, 6 filtres, visionneuse |
| `circuits.html` | Offres &amp; Événements — à la une, événements datés, forfaits, découvertes |
| `carte.html` | La table — 94 articles, recherche instantanée |
| `spa.html` | Le spa — 22 soins, 4 rituels en vedette |
| `a-propos.html` | « Akwaba », 6 arguments, 5 espaces, 13 équipements |
| `contact.html` | 4 canaux, formulaire validé, carte d'accès |
| `experiences.html` | 6 lieux du domaine, 4 activités nautiques, 4 excursions |
| `seminaires.html` | 5 configurations de salle, 4 formules, demande de devis |
| `informations-utiles.html` | 17 questions en accordéon |
| `mentions-legales.html` | Trame juridique à compléter |
| `404.html` | Page introuvable |

## Le parcours

Chaque catégorie a sa fiche, avec calcul du séjour en direct. Le bouton
« Réserver » passe la sélection à `reserver.html` par l'URL
(`?chambre=&du=&au=&pax=`), qui déroule trois étapes : dates, coordonnées
validées, acompte de 30 % — puis une confirmation avec numéro de dossier.

Aucun formulaire ne se termine par une impasse.

## Identité

La palette est **extraite du logo** de l'établissement (dominante `#84603C`) :
bronze, bois, écorce. La signature **« Le Rêve Africain »**, présente dans le
logo mais absente du site d'origine, structure le discours.

- Typographies : **Marcellus** (titres) et **Karla** (texte), via Google Fonts
- Fond : **`#FBF7F0`**, un crème chaud — `#100B06` sur les pages nocturnes
  (La table, Le spa), qui gardent leur nuit
- Accent : `#7F5524`

> **Le site est passé du noir au crème le 24 septembre 2026**, à la demande de
> la direction. Ce qui n'a pas changé : le bronze, le bois, les typographies
> et « Le Rêve Africain ». La palette vient toujours du logo — c'est le
> **fond** qui a changé, pas l'identité.
>
> Trois pièges, tous rencontrés :
>
> 1. **`--night` n'est pas « le fond le plus noir »**, c'est *ce qui contraste
>    avec le bronze*. Il sert au texte posé sur un aplat bronze et aux voiles
>    posés sur les photos : il reste sombre.
> 2. **`--bronze` sert de texte ET de fond.** Il lui faut être assez sombre
>    pour se lire sur le crème, et assez sombre pour porter du texte clair.
> 3. **Redéclarer un jeton ne suffit pas.** `body{color:var(--cream)}` se
>    résout au `body` : les descendants héritent d'une couleur déjà calculée.
>    Tout voile qui redéclare ses jetons doit réaffirmer `color`.
- Navigation : un seul élément, menu plein écran

Bilingue français / anglais sur toutes les pages, sans rechargement.

---

## Structure

```
site/
├── *.html                  les 23 pages servies
├── _chrome.py              briques partagées : nav, tiroir, pied de page
├── build-*.py              générateurs de pages
├── carte-template.html     gabarit de la carte du restaurant
├── spa-template.html       gabarit de la carte des soins
└── img/opt/                images optimisées (WebP + JPEG de secours)
```

Les dossiers `img/gallery/`, `img/rest/`, `img/rooms/`, `img/brand/`,
`img/insta/` et `img/manquant/` contiennent les **originaux téléchargés** et ne
sont pas versionnés (~60 Mo). Seul `img/opt/` est nécessaire pour servir le site.

## Régénérer les pages

Les pages générées ne se modifient pas à la main : on édite le script ou le
gabarit, puis on relance.

```bash
cd site
python build-chambres.py   # les 7 fiches chambres
python build-reserver.py   # reserver.html
python build-carte.py      # carte.html + spa.html
python build-galerie.py    # galerie.html (+ optimise les photos manquantes)
python build-404.py        # 404.html
python build-pages.py      # a-propos.html
python build-pages2.py     # contact.html
python build-pages3.py     # informations-utiles.html
python build-pages4.py     # mentions-legales.html
python build-pages5.py     # suite-arabe.html (remplacé par build-chambres.py)
python build-pages6.py     # circuits.html
```

`index.html` est écrit à la main et n'a pas de générateur.

Dépendance unique : **Pillow** (`pip install Pillow`), pour l'optimisation des
images dans `build-galerie.py`.

## Régénérer les images

Les scripts d'optimisation lisent les originaux dans `site/img/`. S'ils sont
absents, il faut les retélécharger depuis la médiathèque de l'hôtel
(`https://evannathhotel.com/wp-json/wp/v2/media?per_page=100&page=1..5`) puis
relancer `build-galerie.py`, qui ne régénère que les fichiers manquants.

## Prévisualiser en local

```bash
cd site
python -m http.server 5599
```

Puis ouvrir <http://localhost:5599>.

---

## Déploiement

Hébergé sur **Vercel**, en site statique — aucune étape de compilation.

À l'import du dépôt, régler **Root Directory** sur `site`. Le fichier
`site/vercel.json` fait le reste : URL sans `.html`, images en cache un an,
en-têtes de sécurité. Chaque `git push` sur `main` redéploie automatiquement.

## Mode prospection — le site est volontairement invisible des moteurs

La maquette porte la marque, le logo et les photos de l'hôtel sur une URL qu'il
ne contrôle pas. Tant qu'il n'a rien signé, elle **ne doit apparaître dans aucun
moteur de recherche** : sans quoi elle concurrencerait son propre site sur son
propre nom, et exploiterait publiquement sa marque sans accord écrit.

Trois couches, parce qu'aucune ne suffit seule :

| Couche | Où | Portée |
|---|---|---|
| `<meta name="robots">` + `googlebot` | les 21 pages | HTML |
| En-tête `X-Robots-Tag` | `vercel.json`, toutes les routes | images, PDF, manifest — tout |
| Aucun `sitemap.xml` | supprimé automatiquement | on n'invite pas |

**Le crawl reste autorisé, et c'est volontaire.** Un `Disallow: /` serait ici un
contresens : Google ne lirait alors jamais la directive `noindex`, et pourrait
tout de même indexer l'URL nue s'il la découvre par un lien externe. Pour
disparaître vraiment, il faut d'abord être lu.

Le visiteur qui a le lien voit le site normalement. Seuls les robots sont
écartés.

### Repasser en production le jour de la signature

1. `PROSPECTION = False` en tête de `site/_chrome.py`
2. Relancer tous les générateurs, puis `build-sitemap.py`
3. Dans `site/vercel.json` : supprimer la règle `X-Robots-Tag` (la dernière
   entrée de `headers`). Attention, `vercel.json` **refuse toute propriété
   inconnue** — ne pas y ajouter de note ou de commentaire, le déploiement
   échouerait silencieusement.
4. Redéployer, puis soumettre `sitemap.xml` à la Search Console

## Une seule source pour le châssis

`site/_chrome.py` porte les briques partagées par toutes les pages :

| Brique | Contenu |
|---|---|
| `TOKENS` | les jetons de couleur, de typographie et `--h-nav` |
| `HEAD_CSS` | `TOKENS` + la feuille de base (reset, en-tête, tiroir, pied) |
| `NAV_BASE` | en-tête qui se compacte, tiroir plein écran, touche Échap |
| `COLLANTE_JS` | rideau des barres collantes |
| `REVEAL_JS` | apparition au défilement |
| `NAV_JS` | la somme des trois précédents |
| `LANG_JS` | bascule français / anglais |

**Les trois pages écrites à la main les consomment aussi.** L'accueil, La table
et Le spa recopiaient auparavant le bloc `:root` et le JS de navigation : toute
correction centrale les manquait en silence — c'est arrivé trois fois de suite
avec `--h-nav`, puis le rideau CSS, puis le rideau JS.

Elles passent désormais par des gabarits à substitution :

```
index-template.html   -> build-index.py  -> index.html
carte-template.html   -> build-carte.py  -> carte.html
spa-template.html     -> build-carte.py  -> spa.html
```

Marqueurs disponibles : `{{TOKENS}}`, `{{HEAD_CSS}}`, `{{NAV_JS}}`,
`{{NAV_BASE}}`, `{{LANG_JS}}`, `{{ENVOI}}`, `{{SECOURS}}`, `{{EN_SECOURS}}`.

⚠️ **Ne pas modifier `index.html`, `carte.html` ni `spa.html` directement** :
ils sont regénérés depuis leur gabarit.

Ce qui reste propre à chaque page est conservé tel quel : l'accueil redéclare
six couleurs plus chaudes, La table garde son en-tête transparent au repos et
son `.btn` à elle. **Le reste de leur CSS n'a délibérément pas été fusionné** —
ces pages surchargent des règles de base, et l'ordre de cascade doit être
préservé. Une tentative de fusion complète a été mesurée puis abandonnée : elle
neutralisait `.btn-solid` et rendait l'en-tête de La table opaque.

Quand une page a du texte hors `[data-t]` — un `placeholder` de champ, par
exemple — elle déclare `EVN_LANG(lg)`, que `LANG_JS` appelle à chaque bascule.

### Contrôler

```bash
cd site && python verifier.py
node .outils/contraste.js          # le contraste de chaque texte, chaque page
```

`contraste.js` ouvre les 21 pages dans un vrai navigateur et mesure chaque
texte contre le fond qu'il a réellement — les couches translucides sont
**composées**, sans quoi un fond à 6 % d'opacité passe pour opaque et invente
dix-huit défauts.

⚠️ **Il ne voit pas le texte posé sur une photographie** : il compare à une
*couleur* de fond, et une image n'en est pas une. Ces textes-là sont comptés
et écartés du verdict — ils se jugent sur capture. Lors du passage au crème,
l'outil annonçait zéro défaut sur 2 806 textes pendant que « Où vous allez
dormir » disparaissait dans un canapé.

Quinze contrôles sur les 21 pages : variables CSS déclarées, jetons partagés
présents, JS de navigation non divergent, images dimensionnées, fichiers
existants, liens valides, navigation complète, JSON-LD valide, JavaScript qui
se parse, `srcset` effacé sur les images reconstruites, et aucune
disponibilité affirmée dans le balisage. Chacun correspond à un défaut
réellement survenu.

Les autres suites :

```bash
node tests/dispo.test.mjs     # la regle des nuits, hors reseau
node tests/remise.test.mjs    # la logique de remise
node tests/envoyer.test.mjs   # l'envoi des formulaires
```

## Vidéo

`site/video/presentation-hotel.mp4` — 3 minutes, 1280×720, 28 Mo, avec son.
Elle est intégrée à la page **À propos**, en lecture à la demande :
`preload="none"`, donc **rien ne part tant que le visiteur n'a pas cliqué**.
Le fichier est en *fast-start* (index en tête), la lecture démarre donc sans
attendre les 28 Mo.

L'affiche est une photo du domaine et non une image du film : **ffmpeg n'est
pas installé sur ce poste**, il est donc impossible d'extraire une image, de
découper, de couper le son ou de ré-encoder.

Trois autres vidéos dorment dans `site/img/gallery/` (dossier non versionné) :
Réveillon (3 min 21, 1280×720), Massage (13 s, vertical 720×1280) et Suite
mezzanine (45 s, 360×640 — trop basse définition pour être utilisable).

### Le hero animé de l'accueil

`video/hero-presentation.mp4` — le film de présentation, **2 min 47**,
1280×720, sans son. Ré-encodé pour un usage de fond : **12,9 Mo au lieu de
28**, soit 647 kb/s. Qualité vérifiée à 100 % sur un plan détaillé,
indiscernable de la source derrière le dégradé.

Le son est coupé par obligation : aucun navigateur ne lance une lecture
automatique avec du son. Pour l'entendre, la page **À propos** sert le film
complet en lecture à la demande.

**Le film source est coupé à 5,0 s et 172,3 s.** Il ouvrait et fermait sur un
carton « Hôtel Evannath » qui venait s'écrire par-dessus le titre de la page —
deux logos superposés — et sur du noir. Mesure image par image :

| moment | ce qu'on voit |
|---|---|
| 0,0 – 0,5 s | noir |
| 0,0 – 4,9 s | carton « Hôtel Evannath » en surimpression |
| **5,0 s** | le carton disparaît, une nouvelle scène commence |
| **172,3 s** | début du fondu au noir |
| 173 – 175,4 s | noir |
| 175,5 – 180 s | le même carton, sur fond noir |

Un **fondu d'enchaînement de 1,2 s** relie la fin au début : sans lui la
boucle sautait de la nuit au petit matin. Contrôlé après encodage : plus une
seule image sous 9,4 de luminance sur les 167 s, et aucun carton ailleurs
dans le film.

Le titre reste lisible sur toutes les images : contraste mesuré sous le `<h1>`
image par image, **9,22:1** au pire pour le titre et **5,41:1** pour l'accent
doré, contre 3:1 exigés pour du grand texte.

### La mosaïque des fiches chambres

La grille fait trois colonnes `2fr 1fr 1fr`, et la première image occupe deux
rangées. Elle ne tombe juste que pour certains nombres de photos — sinon elle
laisse un trou, et le trou se voit :

- **moins de 5 photos** : la seconde rangée reste vide sous la grande image.
  Mesuré à 3 photos : **27 % de la grille**, sur six fiches. La classe `court`
  retire l'étalement sur deux rangées.
- **nombre pair** : la grille à deux colonnes finit sur une rangée incomplète.
  La classe `plein` étale la dernière image sur toute la largeur.

Les deux classes sont posées par `build-chambres.py`, qui seul connaît le
nombre. `verifier.py` (contrôle 7 ter) refuse une classe manquante ou de trop —
les quatre cas ont été testés en les provoquant.

Remplissage mesuré après correction, à 1280 / 900 / 375 px :

| fiche | photos | 1280 px | 900 px | 375 px |
|---|---|---|---|---|
| chambre-standard | 3 | 98,3 % | 97,8 % | 97,7 % |
| suite-arabe | 5 | 96,9 % | 96,8 % | 96,9 % |
| suite-anglaise | 8 | 95,6 % | 95,9 % | 93,9 % |

Le reste, ce sont les gouttières de 10 px.

**Les largeurs déclarées suivent le placement réel.** Une vignette de 293 px se
faisait servir le palier 1024 parce que `sizes` annonçait 700 px — le
navigateur ne voit pas la grille, il croit ce qu'on lui déclare.
`_sizes_mosaique()` compose la déclaration à partir de la position de l'image :
colonne large ou étroite, pleine largeur ou moitié selon le nombre de colonnes.

### Le cache, et pourquoi les URL des médias portent `?v=`

`vercel.json` sert `/video/` en `immutable, max-age=31536000` : le navigateur
reçoit l'ordre de garder le fichier **un an** et de ne plus jamais redemander
cette URL. Cette promesse n'est tenable que si **l'URL change quand le contenu
change**.

Elle ne l'était pas. Le film du hero a été ré-encodé trois fois sous le même
nom : tout visiteur ayant vu une version précédente y restait bloqué, sans
aucun moyen de recevoir la correction — un rechargement ne suffit pas, la
requête n'est même pas émise.

Les URL des vidéos et de leurs affiches portent donc une **empreinte de leur
propre contenu**, ajoutée automatiquement par `versionner()` dans `_chrome.py`
au moment de la génération :

```
video/hero-presentation.mp4?v=91f5865b
img/opt/hero-presentation-affiche.jpg?v=896b64f2
```

Ré-encoder un fichier change son empreinte, donc son URL, donc le navigateur
le retélécharge. Rien à purger.

`verifier.py` (contrôle 7 bis) refuse une empreinte périmée **et** une vidéo
citée sans empreinte. Les deux cas ont été testés en les provoquant.

`/img/opt/` n'est pas versionné — les photos y sont trop nombreuses. Sa règle
est donc passée de `immutable` à
`max-age=86400, stale-while-revalidate=2592000` : une photo régénérée se
propage en un jour au lieu d'un an, sans coûter de requête au visiteur.

### Sur téléphone, pas de film

Aucune des deux vidéos ne se charge en dessous de 900 px de large, ni en
connexion économe, ni en mouvement réduit — décision prise une seule fois,
dans `filmAmbiance()`.

Sur l'accueil, le **carrousel de photos reste le hero du téléphone**. Le
`<video>` n'y déclare donc **pas** d'attribut `poster` mais un `data-affiche` :
l'affiche est posée par `filmAmbiance()` au moment seulement où elle décide de
charger. Déclarée en HTML, elle partait sur tous les téléphones — 46 Ko — pour
une image que personne ne voit jamais, le `<video>` restant à `opacity:0`
tant que la lecture n'a pas commencé.

Sur le spa, c'est l'inverse : l'affiche **doit** rester à l'écran quand le film
ne se charge pas, puisqu'il n'y a rien derrière elle. Elle garde donc son
attribut `poster`, et la vidéo n'y est plus masquée par une opacité à 0.

### Le geste, sur la page Spa

`video/spa-massage.mp4` (840 Ko) — 10 s, muet, vertical 640×896, tiré de la
vidéo Massage. Placé dans la section « Le sel, l'huile et la main », qu'il
illustre littéralement.

La source était une **publicité pour les réseaux sociaux** : logo incrusté en
haut, numéro de téléphone et icônes réseaux en bas, et un carton d'appel à
l'action sur les 2,3 dernières secondes. Le clip est recadré pour retirer les
deux bandeaux — sur son propre site, l'adresse du site n'a rien à faire dans
l'image — et coupé avant le carton.

Pas de WebM ici : mesuré à la même taille que le MP4, il n'apportait rien.
Sur le hero il fait 23 % de moins, d'où la différence de traitement.

### La règle commune

`filmAmbiance()` dans `NAV_BASE` porte la décision pour les deux films :
écran d'au moins 900 px, connexion ni 2G ni économie de données, pas de
mouvement réduit. Sinon l'affiche reste et **pas un octet ne part**.

L'appel se fait après le chargement de la page, jamais au moment où le script
est lu — un appel prématuré verrouille la décision alors que la largeur de la
fenêtre n'est pas encore connue.

Pour refaire les extraits avec d'autres bornes, tout est dans `outils-video.sh`.

## Offres & Événements

L'établissement produit des affiches — Packs Vacances, Réveillon, fête de
l'Indépendance — et les publie sur ses réseaux. Son site n'avait aucun endroit
pour les recevoir : c'est l'un des constats de l'audit.

**Une page séparée a d'abord été construite, puis retirée.** Trois de ses cinq
entrées existaient déjà sur `circuits.html`, et deux libellés de menu disaient
« offres ». C'était un doublon, pas un complément.

`circuits.html` s'appelle désormais **Offres & Événements** et se lit du plus
urgent au plus permanent :

| Section | Contenu |
|---|---|
| **À la une** | ce qui a une date proche — aujourd'hui le Réveillon |
| **Événements** | les rendez-vous datés, affiche à l'appui |
| **Nos offres & forfaits** | Packs Vacances, lune de miel, séjours composés |
| **Circuits & découvertes** | ce qui emmène hors du domaine |

Les événements vivent dans `_evenements.py`, **le seul fichier à modifier pour
publier une affiche**. Il ne contient que ce qui a une date : les Packs Vacances
et le Coffret Anniversaire n'y sont pas, ce sont des offres permanentes de la
section du dessous. Une chose, un endroit.

Le bloc Méchoui Party qui vivait à part a été retiré pour la même raison :
l'événement a maintenant son entrée, il n'a plus besoin de sa section.

### L'agenda : un événement à la fois

La section **Événements du moment** est un carrousel plein cadre, inspiré de
ce que fait le Platinum Hotel Spa à Cocody — un concurrent direct sur le
séminaire d'entreprise.

Chaque événement occupe toute la largeur : photo de fond, pastille de
récurrence, surtitre, titre dont la fin passe en italique bronze, deux phrases,
puis **trois ou quatre pastilles d'information** — horaire, lieu, ambiance, au
menu. C'est ce qu'on veut savoir avant de se déplacer, et c'est ce qui manquait
à une simple carte.

Le compteur `01 / 02` et les deux flèches se tiennent en bas à droite. Les
flèches du clavier fonctionnent aussi.

**Il défile tout seul, toutes les sept secondes** — mais il s'arrête dès qu'on
le survole, qu'on y met le clavier, ou que l'onglet passe en arrière-plan : un
carrousel qui tourne pendant qu'on lit une pastille est plus agaçant qu'utile.
Toute action manuelle relance le compte à zéro, pour ne pas enchaîner juste
après un clic. Et rien ne bouge si le visiteur a demandé moins de mouvement
(`prefers-reduced-motion`).


**Le carrousel reste dans la largeur du contenu.** Un débordement plein écran
demanderait `100vw`, qui inclut la barre de défilement et décale la page de
8 px — le défaut est déjà documenté ailleurs dans ce projet.

S'il ne reste qu'un événement, les flèches disparaissent : elles n'ont plus
d'objet.

### Une affiche périmée disparaît toute seule

Chaque entrée porte une `fin`. Passée cette date, **le navigateur retire
l'entrée** au chargement — et la section entière si elle se vide. Le site est
statique, et personne ne le reconstruit le 2 janvier au matin pour décrocher
l'affiche du réveillon. Vérifié : l'affiche du 7 août ne s'affiche plus.

Le bandeau de l'accueil suit le même mécanisme et pointe vers `#a-la-une`. Il
ne porte pas la classe `reveal` — il annonce ce qui se passe maintenant, il n'a
pas à attendre le défilement. Il est placé **sous** la carte de réservation :
`.booking` remonte de 58 px avec un `z-index` supérieur, et le recouvrait.

### Ce que Google en voit

`_schema.evenements()` ne déclare en `Event` que les entrées **qui portent une
date de fin**. Un Event sans date n'en est pas un pour Google, qui exige
`startDate` ; déclarer la Méchoui Party du samedi avec une date inventée
reviendrait à mentir au moteur, qui affiche ces dates telles quelles.

### La navigation ne se recopie plus

Ajouter une entrée a révélé que **les trois pages à gabarit portaient leur
navigation en dur**, ainsi que le dictionnaire anglais du menu. `liens_nav()`
rend désormais le bloc depuis `LINKS`, et les gabarits le consomment par
`{{NAV_LINKS}}` et `{{EN_NAV}}`.

### Deux contrôles de plus

**Contrôle 13 — le JavaScript doit se parser.** Une clé de traduction portant un
tiret, `q-packs-vacances:`, a suffi à casser tout le script d'une page :
JavaScript refuse un tiret dans une clé non quotée. La page s'affichait
normalement ; seuls la bascule de langue, le tiroir et l'expiration avaient
disparu. Chaque script passe maintenant à `node --check`.

**Une clé posée sur deux textes différents** est refusée à son tour. Le contrôle
7 quater ne voyait que les doublons du *dictionnaire*, pas ceux du HTML. Il a
immédiatement trouvé deux défauts qui dormaient : sur `circuits`, le bouton de
l'en-tête et celui du circuit partageaient `cta` — en anglais l'en-tête affichait
« Book this package » ; sur `spa`, « Accueil » et « La case » partageaient `c1`,
et le fil d'Ariane devenait « La case » après un aller-retour de langue.
## Les disponibilités

Demandé par la direction le 23 septembre 2026. Le site affichait jusque-là,
sur les sept fiches chambres, une pastille verte et « Disponible à ces
dates » — quelles que soient les dates, sans que rien ne le vérifie.

### On raisonne par chambre physique

La première version raisonnait par catégorie : « les Standards sont-elles
ouvertes ? ». La direction l'a repris, et elle avait raison : **une réception
tient un cahier de numéros.** C'est la chambre 25 qui est prise, pas « les
Standards ».

Le gain n'est pas cosmétique. En comptant des chambres, on obtient **le
stock** — ce que la première version déclarait hors de portée sans logiciel
de gestion.

| Ce que la réception saisit | Ce que le site demande |
|---|---|
| ses chambres, une à une, avec leur numéro et leur catégorie | « reste-t-il au moins une chambre de cette catégorie ces nuits-là ? » |

L'écran s'ouvre donc sur **un récapitulatif : une ligne par catégorie, ses
numéros à la suite.** Avec trente chambres, la liste détaillée ne tient plus
à l'écran et on ne sait plus quelle 25 appartient à quoi ; ce tableau tient
en dix lignes quel que soit le nombre de chambres. Les numéros s'y trient
comme on les lit — 2 avant 10, B2 avant B10 — et les numéros barrés sont
hors service, ce que la légende dit en toutes lettres plutôt que de laisser
un trait s'expliquer tout seul.

### Quatre états

| État | Quand | Ce que le site écrit |
|---|---|---|
| **libre** | au moins deux chambres restent | « Disponible à ces dates », en vert |
| **derniere** | exactement une | « Dernière chambre à ces dates », en bronze |
| **complet** | aucune | « Complet à ces dates », en rouge |
| **inconnu** | aucune chambre saisie dans cette catégorie | « Disponibilité confirmée sous 24 h », en gris |

`inconnu` n'est pas une panne : c'est l'état de départ. Un calendrier vide ne
promet rien, et le site redit simplement ce qu'il disait déjà.

**« Dernière chambre » est le seul chiffre qui sort du serveur.** « Il en
reste sept » publierait le taux d'occupation de l'hôtel à qui sait lire du
JSON ; « il en reste une » est utile au visiteur et ne lui apprend rien qu'il
ne découvrirait en réservant.

**Rien ne retombe jamais sur `libre`.** Réseau coupé, API absente, réponse
illisible, réponse vide, état inconnu renvoyé par le serveur : les cinq cas
ont été provoqués dans le navigateur, les cinq donnent `inconnu`. Annoncer
libre à tort, c'est vendre une chambre qui n'existe pas.

### Deux façons de retirer une chambre, et elles ne disent pas la même chose

| | Ce que ça veut dire |
|---|---|
| **Hors service** | indisponible **sans dates**, jusqu'à nouvel ordre. Une climatisation en panne n'a pas de date de fin connue, et obliger à en inventer une rouvrirait la chambre toute seule ce jour-là. |
| **Une fermeture** | des nuits précises. C'est la chambre prise par un client, ou par un groupe. |
| **Retirer** | la chambre n'existe plus. L'écran le dit au moment de confirmer, et renvoie vers « hors service » pour une panne. |

Une fermeture peut viser **une chambre**, **une catégorie entière** (peinture
dans toute une aile) ou **tout l'hôtel** (fermeture annuelle). Elle peut aussi
être **sans date de fin** — cochée explicitement, jamais par l'oubli du champ :
une fin laissée vide ferme **une seule nuit**.

### Les dates sont des nuits

Une fermeture **du 24 au 26** ferme les nuits du 24, du 25 et du 26. Un séjour
**du 24 au 26** occupe les nuits du 24 et du 25 — pas celle du 26, le client
part ce matin-là.

La règle vit à un seul endroit, `api/admin.js` :

```js
function chevauche(du, au, debut, fin) {
  if (debut >= au) return false;
  return fin === null || fin === undefined || fin >= du;
}
```

Les bornes sont des chaînes `AAAA-MM-JJ` : leur ordre lexicographique **est**
leur ordre chronologique, aucune conversion en `Date` n'est nécessaire — et
aucun fuseau horaire ne vient s'en mêler. `fin` à `null` vaut « sans date de
fin ».

`tests/dispo.test.mjs` — 62 vérifications. Elles ont été prouvées en cassant
la logique **huit fois** : nuit du départ comptée, première nuit oubliée,
fermeture sans fin qui s'arrête, catégorie vide devenue libre, zéro chambre
qui ne fait plus « complet », dernière chambre qui ne se dit plus, hors
service ignoré, fermeture par catégorie qui n'atteint pas ses chambres. Les
huit sont vues.

### Où ça vit

| | |
|---|---|
| La règle et le décompte | `api/admin.js` — `chevauche()`, `vise()`, `etatDe()` |
| La route publique | `/api/admin?a=dispo&chambre=<catégorie>&du=&au=` |
| Le module client | `DISPO_JS` dans `_chrome.py` |
| La saisie | `/admin`, écran **Disponibilités** |
| Ce qui l'affiche | les 7 fiches chambres, l'accueil, le tunnel |

La route publique rend **un verdict, pas le calendrier**. N'en sortent jamais :
les numéros de chambre, le nombre de chambres restantes, et le motif d'une
fermeture — « groupe séminaire », « travaux » regarde l'hôtel, pas ses
visiteurs.

⚠️ **Le paramètre s'appelle `chambre` et porte un slug de CATÉGORIE**, parce
que c'est ce que le visiteur choisit. Dans le magasin de données, `chambres`
désigne au contraire les chambres physiques. Dans `/admin`, `ETAT.categories`
porte les catégories et `ETAT.chambres` les chambres.

### Du site au calendrier : la retenue

Jusqu'au 23 septembre, une demande faite sur le site **n'atteignait jamais le
serveur**. Elle partait sur le téléphone de la réception, et si celle-ci ne la
recopiait pas dans le calendrier, le site continuait d'annoncer la chambre
libre : deux clients pouvaient demander la dernière.

Le tunnel prévient désormais le serveur, qui **retient une chambre**.

| | |
|---|---|
| Quelle chambre | la première libre de la catégorie, dans l'ordre où un humain lit les numéros — 2 avant 10. Le client choisit une catégorie, jamais un numéro. |
| Combien de temps | **deux heures**, puis la retenue cesse de peser |
| Ce qu'en voit le visiteur | rien de l'inventaire : ni le numéro, ni combien il en reste |
| Si rien n'est libre | aucune retenue, et **le formulaire n'échoue pas** — la demande part quand même |
| Si le serveur ne répond pas | idem. L'envoi ne l'attend pas, et le message part de toute façon |

**La péremption est vérifiée à la lecture**, pas par un ménage nocturne — il
n'y en a pas. Une chambre bloquée jusqu'au prochain déploiement serait une
chambre invendable sans que personne ne sache pourquoi.

Une retenue périmée **reste dans le magasin** : la demande a eu lieu, et
l'effacer perdrait le nom du client et ses dates. Elle cesse simplement de
peser, et l'écran le dit — « Retenue expirée : la chambre est redevenue
disponible. »

**La référence est la même des deux côtés.** La réception lit
« EVN-EIMWJG » dans son WhatsApp et retrouve la même à côté du nom, dans le
calendrier. Un clic sur **Confirmer** transforme la retenue en réservation :
elle perd sa péremption et ne se rouvrira plus toute seule.

⚠️ C'est la **seule route publique qui écrive**. Elle est donc bornée : douze
demandes par minute et par adresse — seuil volontairement haut, le trafic
mobile ivoirien partageant des IP par NAT opérateur. La péremption fait le
reste : même un flot de fausses demandes se vide en deux heures.

### Le client est prévenu quand la réception confirme

Jusqu'au 23 septembre, un client qui demandait une chambre n'avait que sa
référence. Rien ne lui disait que sa demande était acceptée : c'était à la
réception de le rappeler, à la main, et si elle oubliait il restait sans
nouvelles.

Le passage d'une retenue de **« en attente » à « confirmée »** déclenche
désormais un e-mail au client. Il est envoyé **après l'écriture** — une
confirmation enregistrée vaut mieux qu'un e-mail parti pour une réservation
qu'on n'a pas su écrire.

**Son résultat remonte toujours**, et l'écran le dit :

| | Ce que la réception lit |
|---|---|
| `envoye` | « le client est prévenu par e-mail » |
| `sans-adresse` | « aucune adresse : prévenez-le vous-même » |
| `non-configure` | « l'envoi d'e-mails n'est pas encore branché » |
| `refuse` · `echec` | « l'e-mail n'est pas parti : prévenez-le vous-même » |

Un e-mail qui échoue en silence, c'est un client que personne ne prévient
pendant que la réception croit le contraire. Les quatre cas sortent donc en
**alerte**, pas en message vert.

**Ce que l'e-mail ne dit pas, et pourquoi :**

- **ni montant, ni acompte, ni conditions d'annulation.** Le site affiche
  « acompte de 30 % » et « annulation gratuite jusqu'à 48 h » — deux valeurs
  plausibles **que j'ai écrites**, que l'hôtel n'a jamais validées. Les
  répéter dans un e-mail de confirmation en ferait un engagement écrit.
- **ni numéro de chambre.** Le client a demandé une catégorie ; la chambre
  retenue peut changer d'ici son arrivée.

Il dit donc : c'est confirmé, la catégorie, les dates, la référence, et que
la réception recontacte pour le règlement.

**Pour l'activer**, deux variables chez Vercel :

| | |
|---|---|
| `RESEND_API_KEY` | la clé Resend |
| `MAIL_EXP` | l'expéditeur, **vérifié chez Resend** — donc une adresse du domaine de l'hôtel |
| `MAIL_DEST` | facultatif : l'adresse en réponse |

Tant qu'elles manquent, tout le reste fonctionne et l'écran annonce
`non-configure`. **Ce qui bloque n'est pas le code, c'est le domaine** :
Resend exige un expéditeur vérifié, donc `evannathhotel.com`, donc la
signature.

### Ce que ça ne fait pas

Deux clients peuvent réserver la même nuit à la seconde près sans que rien ne
les en empêche : il n'y a pas de verrou, parce qu'il n'y a pas de réservation
ferme — le site produit une demande, la réception confirme. Le verrou viendra
avec la synchronisation Booking / Airbnb, formule Performance.

**Un calendrier que personne ne remplit est pire que pas de calendrier** : il
transforme un silence honnête en promesse fausse. C'est pourquoi l'écran de
saisie dit en toutes lettres ce que chaque état produit à l'écran du client,
et pourquoi la formation de la réception fait partie du travail.

## L'administration

`/admin` — un espace pour que l'établissement publie ses événements et ses
promotions **sans intervention**. C'était la condition pour que la page vive :
une section qu'il faut demander à son prestataire de mettre à jour meurt en
trois mois.

| Écran | Ce qu'il fait |
|---|---|
| Tableau de bord | les compteurs, l'état du stockage, un raccourci pour publier |
| Disponibilités | les catégories prises en ligne, et les nuits fermées |
| Événements | créer, modifier, dépublier, supprimer |
| Promotions | les mêmes champs, plus une remise et un code |
| Galerie | les 90 photos du site, pour choisir un fond |
| Paramètres | l'état de l'installation |
| Utilisateurs | qui peut publier |

### Le formulaire tient en cinq champs

L'établissement communique par des **affiches carrées** — celles qu'il publie
sur ses réseaux portent déjà les dates, le tarif, ce qui est compris et le
téléphone. Lui demander de ressaisir tout cela serait lui faire faire le
travail deux fois.

Le formulaire demande donc : **l'affiche, un titre, quand, jusqu'à quand, et
le bouton.** Le reste — surtitre, pastille, texte, informations détaillées —
est replié sous « Plus de détails », et vide par défaut.

Seul le titre est exigé. Le texte ne l'est pas : quand l'affiche dit tout, le
redemander n'a pas de sens.

### Une affiche se montre entière, une photo sert de fond

Deux mises en page, choisies **sans rien demander** : au dépôt, les
proportions du fichier décident.

| Proportions | Format | Rendu |
|---|---|---|
| carré (0,8 à 1,25) | `affiche` | montrée **entière**, à côté du texte |
| large | `fond` | recadrée derrière le texte |

C'était le défaut de la première version : une affiche carrée passée en fond
était recadrée, et mon texte s'écrivait par-dessus le sien.

Les champs laissés vides ne sont pas rendus — un paragraphe vide occupe une
marge et creuse un trou. Et si la pastille n'est pas renseignée, elle reprend
le « quand » : la date saisie doit se voir quelque part.

### Ce qui ne casse pas le site

Le contenu généré depuis `_evenements.py` **reste en place**. La page le rend
comme avant, puis demande à l'API s'il existe des événements publiés ; s'il y
en a, elle refait les diapositives. Trois conséquences :

- la page fonctionne **sans JavaScript**, avec le contenu construit ;
- si l'API se tait, elle affiche le contenu construit ;
- publier une affiche ne demande **aucune reconstruction** : elle est en ligne
  à la seconde.

### Le stockage, et ce qu'il reste à brancher

Deux modes, décidés par la présence de `BLOB_READ_WRITE_TOKEN` :

| Mode | Quand | Ce qui se passe |
|---|---|---|
| **Démonstration** | pas de jeton | les données vivent en mémoire et se perdent au redéploiement |
| **Durable** | jeton présent | Vercel Blob — les données sont conservées |

**Le mode est affiché en clair dans l'interface**, en rouge, sur chaque écran.
Laisser croire qu'une affiche est enregistrée alors qu'elle disparaîtra au
prochain déploiement serait le pire défaut possible pour cet outil.

**Trois objets, pas un.** Un **événement** a une date et se retire. Une
**promotion** a une remise, un périmètre et une période qui commence. Une
**campagne saisonnière** — Vacances, Saint-Valentin, Noël — n'a rien à
remiser : elle annonce des packs à prix ferme, chacun avec sa photo. Les
confondre menait à greffer des champs les uns sur les autres ; chacun a
désormais son entrée, son formulaire et sa forme sur le site.

Les quatre Packs Vacances écrits en dur restent comme secours : dès qu'une
campagne est publiée, elle prend leur place, au même gabarit.

**L'ordre de la liste est l'ordre du carrousel.** Les flèches ▲ ▼ de chaque
ligne le changent : la première ligne est la première diapositive. Le serveur
réordonne sur la liste complète d'identifiants envoyée par l'interface — aucune
position n'est stockée, donc ni trou ni doublon possibles dans la numérotation.

**Le nom de la variable n'a pas d'importance.** Connecter un magasin permet de
choisir un préfixe : le jeton s'appelle alors `MONPRÉFIXE_READ_WRITE_TOKEN`.
Le code reconnaît le jeton à sa forme — `vercel_blob_rw_…` — dans n'importe
quelle variable finissant par `READ_WRITE_TOKEN`. *Paramètres* affiche le nom
de celle qui a été lue, ce que la liste de Vercel ne montre pas toujours pour
les magasins connectés.

**Ne saisissez pas `BLOB_READ_WRITE_TOKEN` à la main.** Connecter le magasin
au projet crée la variable tout seul. Une variable saisie manuellement, elle,
survit à la suppression du magasin qu'elle désignait et l'emporte sur celle de
la connexion : le code parle alors à un magasin disparu — « This store does
not exist ». *Paramètres* affiche l'identifiant du magasin réellement visé,
à comparer avec celui de Vercel.

**Le magasin doit être en accès public.** C'est un choix fait à la création et
qui ne se change pas ensuite. Un magasin privé refuse l'écriture avec
« Cannot use public access on a private store » — et il ne conviendrait de
toute façon pas : les affiches s'affichent aux visiteurs du site, elles
doivent être lisibles sans jeton.

**Le fichier de données, lui, porte un suffixe aléatoire.** Écrit à une adresse
fixe dans un magasin public, son URL serait devinable : n'importe qui lirait
tous les événements, **brouillons non publiés compris**. Il se retrouve par
préfixe, côté serveur, jeton en main. Les versions précédentes sont effacées
après chaque écriture réussie — jamais avant, pour qu'un échec ne fasse pas
tout perdre.

Pour passer en durable : créer un magasin Vercel Blob dans l'onglet *Storage*
et le connecter au projet, en cochant **Production et Preview**. Vercel injecte
alors `BLOB_READ_WRITE_TOKEN` de lui-même — ne le saisissez pas à la main, vous
auriez un doublon.

**Créez un magasin dédié plutôt que d'en partager un** avec un autre projet :
le jour où le site est remis à l'établissement, un magasin partagé ne se remet
pas.

`site/package.json` déclare `@vercel/blob` — c'est là que Vercel lit les
dépendances des fonctions, la racine du projet étant `site/`. Le site lui-même
n'a toujours aucune dépendance : il est généré en Python et servi en statique.

Si le jeton est absent ou refusé, **l'enregistrement échoue visiblement** :
l'interface affiche la cause. Un échec silencieux ici, c'est une affiche qu'on
croit publiée et qui ne l'est pas.

### Mettre l'administration en service

**1. Choisir un mot de passe.** Générez-le, ne l'inventez pas :

```
node -e "console.log(require('crypto').randomBytes(18).toString('base64url'))"
```

**2. Dans Vercel** — *Settings → Environment Variables* :

| Variable | Valeur |
|---|---|
| `ADMIN_MDP` | le mot de passe généré |
| `ADMIN_SECRET` | une seconde chaîne au hasard, qui signe les sessions |
| `BLOB_READ_WRITE_TOKEN` | le jeton du magasin Vercel Blob, pour le stockage durable |

Redéployer après les avoir définies. Sans `ADMIN_MDP`, la connexion répond 503
avec la marche à suivre.

**3. Essayer avant de déployer.** Un serveur local exécute les fonctions, ce
que `python -m http.server` ne sait pas faire :

```
node serveur-local.js
```

Il lit `.env.local` à la racine — une ligne par variable, `NOM=valeur`. **Ce
fichier est écarté du dépôt** : un mot de passe poussé sur un dépôt distant est
à considérer comme divulgué, même effacé ensuite.

Le site répond alors sur <http://localhost:5599>, l'administration sur
<http://localhost:5599/admin/>. Le serveur annonce au démarrage si `ADMIN_MDP`
est défini et quel stockage est actif.

*Une modification d'une fonction demande un redémarrage : les modules sont
chargés une fois et gardés. Les recharger à chaque appel remettrait à zéro le
stockage de démonstration — chaque événement créé se perdait dans la seconde.*

### L'accès

Un mot de passe, défini par `ADMIN_MDP`, échangé contre un cookie signé de
12 heures. La comparaison est à durée constante : une comparaison naïve laisse
deviner le mot de passe caractère par caractère.

Ce n'est pas un système multi-comptes. Des comptes nominatifs, avec un journal
de qui a publié quoi, demandent le stockage durable — c'est la suite logique.

Sans `ADMIN_MDP`, la connexion répond 503 avec la marche à suivre plutôt que
d'échouer sans explication.

## Version anglaise

Le bouton FR/EN capture le français depuis le DOM au chargement, puis
remplace chaque `[data-t]` par la valeur du dictionnaire `EN` de la page.
Une clé absente laisse le français en place — jamais un trou.

**Dix pages ne portaient de `data-t` que sur la navigation** : les sept fiches
chambres, `reserver`, `seminaires` et `experiences`. Cliquer EN faisait
basculer le menu et laissait toute la page en français. Elles sont
maintenant traduites intégralement.

Le français reste la source de vérité. Les traductions des chambres vivent
dans `_chambres_en.py`, à part de `_chambres.py`, pour qu'une correction de
traduction ne touche jamais le texte français et qu'un anglophone puisse
relire le fichier sans traverser du code.

### Ce que le script écrit lui-même

Le compteur de nuits, le sélecteur de voyageurs, le récapitulatif du tunnel,
la date en toutes lettres et les messages de confirmation sont écrits en
JavaScript, donc hors de portée de `[data-t]`. `LANG_JS` appelle `EVN_LANG(lg)`
à chaque bascule : c'est le point d'extension prévu pour ces cas, utilisé par
les fiches chambres, `reserver` et `seminaires`.

**Les valeurs restent françaises.** Les `<select>` du devis portent désormais
un `value` explicite : l'affichage bascule, mais ce qui part à la réception —
et ce qui indexe la table des capacités — reste `Théâtre`, `En U`,
`Journée d'étude`. Le récapitulatif affiche le libellé, pas la valeur.

### Collisions de clés

Une clé réutilisée par deux textes de la même page fait que le dernier gagne.
Quand la clé appartient au menu (`n1`…`n11`, définies par `EN_NAV`), c'est le
menu qui est écrasé. Quatre pages étaient touchées :

| page | clés | effet en anglais |
|---|---|---|
| `a-propos` | `n1`–`n5`, `d1`–`d3` | le menu affichait « 01 · Accommodation » |
| `mentions-legales` | `n1`–`n9` | le menu affichait « Site publisher » |
| `contact` | `h3` | « Check-in » à la place du titre de section |
| `spa` | `c2` | « The oils » dans le fil d'Ariane |

`verifier.py` (contrôle 7 quater) refuse désormais une clé redéfinie **et** un
segment sans traduction. Les deux cas ont été testés en les provoquant.

### La page mentions légales

Son corps juridique reste **volontairement en français**, qui fait foi —
traduire un document juridique crée un second texte non relu par un conseil,
et une ambiguïté sur celui qui prévaut. Le bandeau de mise à jour le dit au
lecteur. La décision est écrite dans `build-pages4.py` sous la forme du
marqueur `EVN_FR_FAIT_FOI`, que `verifier.py` lit : elle est donc explicite,
pas subie.

## Formulaires

Les cinq formulaires du site — réservation, devis séminaire, contact, table,
spa — postent sur `/api/envoyer`, une fonction serverless Vercel sans aucune
dépendance (`site/api/envoyer.js`).

Elle valide côté serveur, échappe le HTML, tronque les champs, limite le débit
à vingt envois par minute et par IP — seuil volontairement haut, une grande
part du trafic mobile ivoirien partageant une même IP publique derrière du
NAT opérateur, et piège les robots par un champ invisible
doublé d'un délai minimum de remplissage.

**Activer l'envoi par e-mail** — dans Vercel, *Settings → Environment Variables* :

| Variable | Valeur |
|---|---|
| `RESEND_API_KEY` | la clé API Resend, commence par `re_` |
| `MAIL_DEST` | destinataire, ex. `bonjour@evannathhotel.com` (plusieurs adresses séparées par des virgules) |
| `MAIL_EXP` | expéditeur **vérifié chez Resend**, ex. `site@evannathhotel.com` |

Le domaine doit être vérifié chez Resend (enregistrements SPF et DKIM) sans
quoi les envois sont refusés. Redéployer après avoir défini les variables.

### Pendant la prospection, la demande part sur WhatsApp

`ENVOI_WHATSAPP = True` en tête de `_chrome.py`. Le formulaire n'appelle plus
`/api/envoyer` du tout : il présente WhatsApp avec le récapitulatif déjà
rédigé et une référence. Aucune clé, aucun domaine, rien à configurer.

**Le visiteur touche lui-même le lien — on n'ouvre rien à sa place.** La
première version appelait `window.open`. Les navigateurs le bloquent
largement : au clic, il ne se passait plus rien du tout. On ne peut pas parier
la seule voie d'envoi sur une API que le visiteur peut refuser.

Le panneau s'ouvre donc avec le lien déjà rempli, et c'est un vrai clic sur un
vrai lien qui part — ce qu'aucun bloqueur n'arrête, sur téléphone comme sur
ordinateur. La confirmation s'affiche **juste après ce clic**, pas avant :
elle est donc derrière lui, avec sa référence, quand il revient de WhatsApp.

C'est ce qui lève le blocage réel : `MAIL_EXP` doit être un expéditeur vérifié
chez Resend, donc un domaine que l'on ne possède pas tant que rien n'est signé.
Et en Côte d'Ivoire, WhatsApp est de toute façon le canal le plus rapide vers
une réception.

#### Pendant les tests, un seul numéro : le vôtre

`WA_EN_TEST = True` en tête de `_chrome.py`. **Tous** les liens WhatsApp du
site pointent alors sur `WA_TEST` : la destination des cinq formulaires, mais
aussi le bouton flottant, le tiroir de navigation, le pied de page, la page
Contact, les fiches chambres et les informations utiles. Le numéro affiché en
clair suit également.

| Constante | Valeur |
|---|---|
| `WA_HOTEL` / `WA_HOTEL_TEXTE` | `2250546017377` · `+225 05 46 01 73 77` |
| `WA_TEST` / `WA_TEST_TEXTE` | `2250758408079` · `+225 07 58 40 80 79` |
| `WA` / `WA_TEXTE` | **les deux seules valeurs que le reste du code emploie** |

Rien ne doit atteindre la réception d'un établissement qui n'a rien signé —
ni une demande de réservation, ni un visiteur curieux qui clique sur le bouton
flottant.

Le jour de la signature : `WA_EN_TEST = False`, relancer les générateurs. Le
numéro de l'hôtel revient partout, il n'a jamais quitté le fichier.

`verifier.py` (contrôle 11 ter) refuse, tant que `WA_EN_TEST` vaut `True`,
**toute** trace du numéro de l'hôtel — lien comme libellé affiché — et tout
lien `wa.me` vers un autre numéro que celui du moment. Personne ne relit
21 pages à la main, et une demande qui part au mauvais endroit ne se rattrape
pas. Les deux cas ont été testés en les provoquant.

Le drapeau est **indépendant de `PROSPECTION`** : on peut signer et rester sur
WhatsApp le temps que le domaine soit vérifié.

**Les écrans de confirmation suivent le drapeau.** Ils disaient « Demande
envoyée », « est transmise au restaurant », « est partie à la réception ». En
mode WhatsApp c'est faux : rien ne part tant que le visiteur n'a pas appuyé sur
envoyer dans l'application, et celui qui referme sans le faire repartirait en
croyant avoir réservé.

Les cinq écrans annoncent donc **« Votre demande vous attend dans WhatsApp »**,
suivi de « Appuyez sur envoyer dans WhatsApp : ce geste transmet votre demande
à la réception », et les récapitulatifs passent au futur. L'écran final du
tunnel de réservation reste affiché, avec sa référence : c'est lui qu'on montre
en démonstration.

Les textes vivent dans `_chrome.py` (`CONF_TITRE`, `CONF_GESTE`, `CONF_VERBE`
et leurs variantes anglaises), pas dans les pages : repasser le drapeau à
`False` restaure seul les formulations d'origine.

La référence est calculée côté client au même format que le serveur
(`EVN-XXXXXX`), et **figure dans le message WhatsApp** : celle que lit la
réception est celle affichée à l'écran.

#### La classe `.wa` appartient au bouton flottant, et à lui seul

Le lien « Envoyer sur WhatsApp » du panneau de repli portait `class="wa"` —
la même que le bouton flottant du coin de l'écran, dont la règle impose
`position:fixed`, 56 × 56 et un rond. Le lien était donc **arraché du panneau**
et rendu en pastille par-dessus le bouton existant : le repli n'affichait plus
que « Appeler la réception » et « Écrire un e-mail », et son bouton le plus
utile était invisible.

Mesuré avant correction : 56 × 56 px au lieu de 205 × 44, `min-width` à 0 au
lieu de `auto`. Il porte maintenant `.wa-envoi`.

`verifier.py` (contrôle 11 bis) refuse un `class="wa"` en double **et** un
panneau de repli sans son lien. Les deux cas ont été testés en les provoquant.

Si un bloqueur de fenêtres empêche l'ouverture, le panneau de repli s'affiche
avec le lien cliquable à la main — le visiteur n'est jamais dans le vide.

### Activer l'envoi par e-mail à la place

**Le domaine de l'hôtel n'est pas encore le vôtre.**
`MAIL_EXP` doit être un expéditeur vérifié chez Resend : `site@evannathhotel.com`
est donc hors de portée tant que rien n'est signé. Resend fournit pour cela
l'expéditeur de test `onboarding@resend.dev`, qui ne demande aucune
vérification de domaine et ne délivre qu'à l'adresse du titulaire du compte —
ce qui tombe bien, les demandes de test devant arriver chez le prestataire et
non dans la boîte de l'hôtel. On pose donc `MAIL_EXP=onboarding@resend.dev` et
`MAIL_DEST` sur sa propre adresse ; le jour de la signature, ces deux lignes
seules changent.

**Tant qu'elles ne sont pas définies**, l'endpoint répond 503 et le formulaire
bascule sur un panneau de repli : WhatsApp avec le message déjà rédigé,
téléphone de la réception, e-mail. Le visiteur n'est jamais dans le vide, et
en Côte d'Ivoire WhatsApp est souvent le canal le plus rapide de toute façon.

Le même repli couvre la panne réseau, l'échec du fournisseur et un délai
dépassant douze secondes.

### Le panneau de repli ne s'excuse pas

Il ouvrait sur l'aveu de la panne — « Nous n'avons pas pu transmettre votre
demande automatiquement » — avant de proposer la suite. Lu froidement, sans
personne pour l'accompagner, ce n'est plus un filet de sécurité : c'est un
formulaire qui ne marche pas. Or le visiteur a sous les yeux le canal le plus
rapide du pays.

Il mène donc par l'action : **« Terminons sur WhatsApp »**, puis « Votre
demande est prête — il ne reste qu'à l'envoyer ».

**Un point reste explicite, et doit le rester** : la demande n'est pas partie.
« Il ne reste qu'à l'envoyer » le dit sans détour. Les formulations plus
lisses ont été écartées — un visiteur qui ferme la page en croyant avoir
réservé coûte plus cher que le message d'excuse qu'on remplace.

Le texte vit dans `secours()` (`_chrome.py`), **une seule fois**. Les gabarits
de La table et du Spa en portaient une copie figée : cette reformulation les
aurait manqués en silence, comme `--h-nav` et le rideau CSS avant elle. Ils
passent désormais par le marqueur `{{SECOURS}}`, et leur dictionnaire anglais
par `{{EN_SECOURS}}`.

Le panneau est traduit sur les cinq formulaires (clés `sc1`–`sc5`, vérifiées
libres pour ne rien écraser, cf. « Collisions de clés »). Vérifié dans le
navigateur : bascule FR → EN → FR sans perte, `href` du lien WhatsApp intact,
et le message pré-rempli s'y accroche toujours après traduction.

**Ce message pré-rempli reste en français**, y compris en anglais : il part
vers une réception ivoirienne qui travaille en français. Le libellé du bouton
bascule, pas le contenu du message.

Tests : `node tests/envoyer.test.mjs` depuis la racine (12 vérifications).

### Ce que le tunnel de réservation promet

Il envoie une **demande**, pas une réservation confirmée : aucune
disponibilité n'est vérifiée en temps réel et aucun paiement n'est encaissé.
Les libellés le disent — « Envoyer ma demande », « Demande envoyée », et la
réception envoie le lien de paiement après avoir confirmé la chambre.

Passer à la réservation ferme et à l'encaissement demande un channel manager
et un prestataire de paiement : c'est une décision de l'établissement.

## Données structurées

Chaque page indexable porte un graphe JSON-LD (`_schema.py`) : `Hotel` avec les
46 chambres, les 13 équipements, la fourchette 67 000 – 280 000 XOF et les
horaires ; `HotelRoom` avec tarif et capacité sur les 7 fiches ; `Restaurant`
sur la carte ; `FAQPage` sur les 17 questions ; `BreadcrumbList` partout.

Toutes les entités pointent vers des `@id` stables, pour que Google comprenne
qu'il s'agit du même établissement d'une page à l'autre.

**Les coordonnées GPS sont volontairement absentes** : l'établissement ne les
publie nulle part, et un point mal placé vaut moins que pas de point.

### Les barres de filtres ne sont plus collantes

Les pages Chambres, Galerie et La table avaient une barre de filtres qui se
collait sous l'en-tête, avec un « rideau » opaque censé masquer l'intervalle.

**Le mécanisme a résisté à trois corrections.** Une bande de bouts d'images
restait visible entre l'en-tête et la barre. La cause est structurelle : la
barre s'adosse à `--h-nav`, mesurée au chargement, alors que la hauteur de
l'en-tête **varie pendant sa transition de 0,45 s**. Toute valeur fixe est
fausse pendant ce laps de temps.

Le dispositif est retiré plutôt que réparé une quatrième fois : sentinelle,
classe `epinglee`, rideau de 100 vh, et le contrôle 12 du vérificateur qui les
surveillait. **Une barre qui défile avec la page ne peut pas laisser
d'intervalle.**

Ce qu'on perd : les filtres ne suivent plus le défilement sur la galerie. Ils
restent en tête de page, à un retour en haut. Ce qu'on gagne : un défaut visible
sur les trois pages les plus montrées disparaît, et environ soixante lignes de
CSS et de JavaScript avec lui.

`carte-template.html` portait **sa propre copie** du rideau — une recopie de
plus, découverte au nettoyage.
### Le contenu ne dépend pas du JavaScript pour être visible

`.reveal` masque les blocs et attend qu'un script leur pose la classe `in` :
c'est l'apparition au défilement. **Vingt-deux blocs sur l'accueil.** Si ce
script ne s'exécute pas — JavaScript désactivé, extension qui le bloque, ou
erreur survenue plus haut dans le même `<script>` — la page gardait ses
8 121 px de hauteur et restait **vide sous l'en-tête**.

Deux garde-fous, indépendants l'un de l'autre :

1. Le masquage n'est appliqué que si `<html>` porte la classe `js`, posée par
   un script minuscule placé dans le `<head>`. Sans JavaScript, la règle ne
   s'applique pas du tout et tout est visible immédiatement.
2. Ce même script révèle tout au bout de **3 secondes** si le script principal
   n'a jamais posé `window.__reveal`. Comme il s'agit d'un `<script>` séparé,
   une erreur dans l'autre ne l'empêche pas de tourner.

Les trois cas ont été vérifiés, en comptant la **classe** et non l'opacité —
le volet d'aperçu n'exécute pas les transitions CSS, donc une opacité mesurée
y reste figée à 0 :

| situation | classe `js` | blocs révélés |
|---|---|---|
| aucun script | absente | 22/22 visibles d'emblée |
| script principal en panne | posée | 22/22 après 3 s |
| fonctionnement normal | posée | 22/22 |

`verifier.py` (contrôle 7 septies) refuse un masquage `.reveal` non
conditionné et un secours manquant.

### L'image de partage

C'est la vignette que WhatsApp, Facebook ou un client mail affichent quand on
colle le lien. Le prospect la voit **avant** d'ouvrir la page.

L'accueil déclarait la chambre au jeté wax — celle qui s'appelait « paillote »
avant d'être renommée. Il déclare maintenant **la paillote sur pilotis**, la
signature de l'établissement.

**`img/opt/og-accueil.jpg` est une image dédiée, en 1200×628.** Les cartes de
partage recadrent en 1,91:1 ; nos photos sont en 1,41:1, donc laisser faire
coupait un quart de la hauteur sans qu'on choisisse ce qui saute. Le
recadrage est fait au centre : il garde le toit de paille, tout le ponton et
le reflet dans l'eau.

Les balises `og:image:width`, `og:image:height` et `og:image:alt` sont
déclarées — sans les dimensions, certains clients affichent une vignette
carrée le temps de télécharger l'image.

Les autres pages gardent chacune leur image de partage, en 1,41:1 : elles
seront recadrées par les messageries. Seul l'accueil, le plus partagé, a son
image dédiée.

### La fiche JSON-LD de l'accueil

Elle était **collée en dur** dans `index-template.html` : une copie figée de
ce que `_schema.py` produit. Toute correction faite dans le module la manquait
en silence — exactement le défaut que cette page avait déjà pour les jetons de
couleur et le JS de navigation.

Elle est désormais générée par `build-index.py` via `{{JSONLD}}`. Comparaison
avant/après sur les 110 valeurs de la fiche : trois écarts, tous voulus.

### Photos mal nommées

Quatre emplacements montraient autre chose que ce que leur légende annonçait.
Vérifié par signature d'image, pas à l'œil :

| fichier | ce qu'il montre | ce qu'on en disait |
|---|---|---|
| `gal-lag-paillote` | une chambre | « La paillote sur pilotis » |
| `hero-paillote` | la même chambre | hero de l'accueil, nommé « paillote » |
| `c-ponton` | des fauteuils de rotin | « Le ponton de bois sur la lagune » |
| `g-ponton` | les mêmes fauteuils | « La paillote sur pilotis » |

Trois de ces fichiers sont **la même photo sous trois noms** (`gal-lag-rotin`,
`c-ponton`, `g-ponton`), et deux autres également (`gal-lag-paillote`,
`hero-paillote`). La vraie paillote sur pilotis est **`gal-lag-ponton`**, qui
ne servait qu'à la galerie.

L'erreur vient de l'import : `gallery/8.png` a été étiquetée « La paillote sur
pilotis » alors que c'est une chambre. Elle est reclassée en `gal-ch-wax2`,
catégorie Chambres.

`hero-paillote` est **renommé `hero-chambre-wax`**. L'image reste le hero de
l'accueil — elle est bonne — mais son nom dit désormais ce qu'elle est. C'est
ce nom qui avait produit l'erreur : on cherche « la paillote » dans la
photothèque, on tombe sur une chambre.

Les fichiers devenus orphelins sont dans `site/.quarantaine/`, **non
supprimés** : une fois déjà, des variantes `hero-*` dont le chemin était
construit en JavaScript ont failli être effacées.

### Les offres sur l'accueil

Quatre des onze forfaits sont mis en avant, juste **après les chambres** :
c'est le moment où le visiteur vient de voir un tarif à la nuit et se demande
s'il existe mieux. Les quatre couvrent quatre intentions distinctes — un
couple, un week-end, une famille, une journée sans nuitée — et le lien mène
aux onze.

La section reste sur le fond de base, séparée des chambres par un filet ; la
bande sombre des expériences suit, donc le rythme des fonds n'est pas cassé.

**Les tarifs y sont écrits en dur.** `verifier.py` (contrôle 7 sexies) les
compare à ceux du catalogue de `circuits.html`, seule source de vérité : une
remise saisonnière appliquée d'un côté et pas de l'autre donnerait deux prix
pour la même offre. Les deux cas — tarif qui dérive, offre inexistante — ont
été testés en les provoquant.

**Largeurs déclarées.** Les cartes des deux grilles de l'accueil font 279 à
405 px selon la largeur d'écran, mais `sizes` annonçait 700 px : le navigateur
téléchargeait l'image pleine. `build-index.py` déclare maintenant la géométrie
réelle — trois colonnes pour les chambres, quatre pour les offres, deux puis
une en dessous. On déclare la plus large des deux, les grilles partageant des
images. **779 Ko d'images de cartes ramenés à 342 Ko, soit 56 % de moins.**

### Les onze offres de la page Circuits

Elles étaient affichées mais **invisibles des moteurs** : le `Service` de
`circuits.html` n'avait pas de `hasOfferCatalog`, donc aucun forfait
n'existait pour une recherche du type « forfait lune de miel Assinie ».

Le catalogue se construit maintenant dans `build-pages6.py` à partir des mêmes
listes que la page — `PACKS` et `CARDS` — pour qu'il ne puisse pas dériver du
contenu affiché. Chaque offre porte son prix, sa disponibilité et son **unité**
(`le forfait`, `par personne`, `par enfant`) via `UnitPriceSpecification` :
sans elle, un forfait à 25 000 F par enfant et un forfait à 25 000 F tout
compris se ressemblent dans un résultat de recherche.

`verifier.py` (contrôle 7 quinquies) exige que le catalogue déclaré et le menu
de réservation listent **exactement** les mêmes offres, aux mêmes prix et aux
mêmes unités — deux sources écrites séparément finissent toujours par
diverger, et l'écart ne se voit nulle part : le visiteur ne lit pas le
JSON-LD, le moteur ne lit pas le menu. Les trois cas — offre non réservable,
offre non déclarée, prix qui dérive — ont été testés en les provoquant.

## Images responsives

`build-galerie.py` sort les 47 photos à **1748 px**, la définition réelle des
originaux de `img/gallery/`, et deux tailles de vignette — **360 et 620 px**.
La grille passe de 4 colonnes à 3 puis 2 : sur un téléphone une vignette ne
fait que 151 px de large, servir du 620 revenait à envoyer trois fois les
pixels utiles. Le rapport des vignettes est figé en CSS (`aspect-ratio`), sinon
la hauteur rendue changerait selon le palier chargé et la grille bougerait. Il se régénère de lui-même si `LARGEUR` change :
inutile de supprimer quoi que ce soit à la main.

Les images de **La table** ne sont plus des fichiers à part : c'étaient des
copies bit à bit de photos de la galerie, sous d'autres noms. La page pointe
désormais sur les originaux en 1748 px.

`build-images.py` ne fabrique de paliers que pour les images réellement
affichées — pas pour celles que seule la visionneuse charge en plein écran.
Il garantit en revanche qu'un WebP existe pour chacune d'elles : la
visionneuse le sert quand le navigateur le gère, soit **24 % de moins**, environ
61 Ko par photo ouverte. Le JPEG reste en secours pour les rares navigateurs
sans WebP, d'où les deux formats sur le disque.

La construction de l'URL est centralisée dans `plein()` (`NAV_BASE`) : les
quatre visionneuses du site l'utilisent au lieu de recomposer le chemin
chacune de leur côté.

`build-images.py` produit ensuite les largeurs intermédiaires (640 / 1024 /
1600), en WebP et en JPEG progressif, sans jamais agrandir au-delà de
l'original — **ni générer un palier à moins de 10 % de la source** : un
1600 tiré d'un 1748 pèse presque autant pour une différence invisible, et
double le nombre de fichiers pour rien. `responsive()`
dans `_chrome.py` les déclare en `srcset` + `sizes` — par des motifs qui ne
remplacent qu'une valeur d'attribut, jamais du balisage.

Gain mesuré sur l'ensemble du site :

| Profil | Avant | Après | Gain |
|---|---|---|---|
| Téléphone 375 px, écran standard | 11,1 Mo | 6,7 Mo | **40 %** |
| Téléphone 375 px, écran retina | 11,1 Mo | 10,1 Mo | 9 % |
| Bureau 1440 px | 11,1 Mo | 10,3 Mo | 8 % |

Le gain faible sur écran retina n'est pas un défaut du dispositif : **les photos
sources plafonnent à 900 px** pour les chambres. Un écran retina de téléphone en
réclame 750, donc la variante 640 est écartée. Des photos haute définition
débloqueraient ce gain-là aussi — c'est le premier point de la liste ci-dessous.

## Référencement et partage

`sitemap.xml`, `robots.txt` et `site.webmanifest` sont générés par
`build-sitemap.py`. Le favicon est découpé dans le sigle du logo
(`img/brand/logo.png`) — le « H » stylisé, seul élément du logo lisible à
32 px.

Les 17 pages indexables portent une `canonical` absolue et une `og:image`
absolue : sans quoi Facebook et WhatsApp n'affichent aucune vignette au
partage — ce qui compte pour un établissement dont le premier canal compte
21 000 abonnés. `reserver`, `mentions-legales` et `404` sont en `noindex`.

**Au passage en production sur evannathhotel.com**, une seule ligne change :
la constante `SITE` en tête de `site/_chrome.py`. Relancer ensuite tous les
générateurs puis `build-sitemap.py`.

## À valider avec l'établissement

Avant toute mise en production :

1. **Conditions réelles** — arrivée, départ, annulation, acompte, taxe de
   séjour, animaux. Toutes les valeurs actuelles sont des hypothèses.
2. **Quatre erreurs relevées sur la carte d'origine** — un plat affiché
   « FREE », une casserole à 95 000 F dans une section à 14 000 F, un sourcil à
   20 000 F quand la jambe entière est à 2 000 F, et un onglet « Vins » qui ne
   contient aucun vin.
3. **Les 18 champs des mentions légales** — RCCM, capital, hébergeur,
   déclaration ARTCI, prestataire de paiement.
4. **Photographies haute définition** — huit visuels proviennent d'Instagram et
   plafonnent à 640 px. Suffisant pour des vignettes, pas pour un plein écran.
5. **Coordonnées GPS de l'établissement** — absentes du JSON-LD faute de source
   fiable. Une fois relevées, les renseigner dans `ADRESSE` / `geo` de
   `site/_schema.py` : c'est ce qui alimente le point sur Google Maps.
6. **Capacités de la salle de séminaire** — les cinq configurations de
   `seminaires.html` (théâtre 60, classe 35, en U 25, cocktail 90, banquet 70)
   sont des hypothèses : l'établissement ne publie aucun chiffre. À remplacer
   par les capacités réelles avant mise en production.
7. **Les dates des événements** — `_evenements.py` porte des périodes
   plausibles (Réveillon au 31 décembre, Méchoui Party le samedi) mais
   l'établissement ne publie aucun calendrier. À confirmer, et à compléter
   avec leurs vraies affiches.
8. **Licence de la police** — le site d'origine utilise
   `MADE-TOMMY-Regular_PERSONAL-USE.otf`, dont la licence n'autorise pas
   l'usage commercial. La maquette n'utilise que des polices libres.
8. **Quelle adresse e-mail afficher** — deux existent :
   `bonjour@evannathhotel.com`, publiée sur leur Facebook et alignée sur la
   marque, et `receptionhotelevannath@gmail.com`, celle que la réception
   relève réellement. La première fait plus professionnelle sur un site
   d'hôtel ; la seconde a le mérite d'être lue. `MAIL_HOTEL` porte la
   seconde en attendant leur réponse.

   Le numéro WhatsApp, lui, est tranché : **+225 01 51 52 75 75**, confirmé
   par la direction. Ni l'un ni l'autre ne se déduisent du site d'origine,
   qui n'affiche ni lien WhatsApp ni adresse e-mail — points 15 et 17 de
   l'audit.

   **Pendant la démonstration, les deux pointent sur le prestataire** :
   `WA_EN_TEST = True`. Rien n'atteint la réception d'un établissement qui
   n'a rien signé, et l'adresse personnelle affichée sur la page Contact est
   assumée le temps des tests.

---

Conception et développement : **Léonardo Yann Axel HOUANSOU**
