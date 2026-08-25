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
| `circuits.html` | 4 Packs Vacances + 6 circuits + Méchoui Party |
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
- Fond : `#17100A` — `#100B06` sur les pages nocturnes (La table, Le spa)
- Accent : `#B98A50`
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
`{{NAV_BASE}}`, `{{LANG_JS}}`, `{{ENVOI}}`.

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
```

Neuf contrôles sur les 21 pages : variables CSS déclarées, jetons partagés
présents, JS de navigation non divergent, images dimensionnées, fichiers
existants, liens valides, navigation complète, JSON-LD valide, rideau présent.
Chacun correspond à un défaut réellement survenu.

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

**Tant qu'elles ne sont pas définies**, l'endpoint répond 503 et le formulaire
bascule sur un panneau de repli : WhatsApp avec le message déjà rédigé,
téléphone de la réception, e-mail. Le visiteur n'est jamais dans le vide, et
en Côte d'Ivoire WhatsApp est souvent le canal le plus rapide de toute façon.

Le même repli couvre la panne réseau, l'échec du fournisseur et un délai
dépassant douze secondes.

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

### Les barres collantes et leur rideau

Les pages Chambres, Galerie et La table ont une barre de filtres qui se colle
sous l'en-tête. Comme l'en-tête se compacte sur 0,45 s, sa hauteur varie
pendant le défilement : viser une valeur laisse passer du contenu entre les
deux. La barre porte donc un **rideau opaque** qui remonte jusqu'en haut de
la fenêtre, et l'en-tête, en `z-index` supérieur, se peint par-dessus.

**La hauteur de l'en-tête n'est plus devinée.** `--h-nav` valait 83 px en dur,
alors que l'en-tête compacté mesure **75 px sur Chambres et Galerie, 77 px sur
La table** — celle-ci ayant une bordure basse en plus. La barre se collait
donc 6 à 8 px trop bas, et le contenu défilait à découvert dans cet
interstice : c'est la bande de bouts d'images visible entre l'en-tête et la
barre. `NAV_BASE` mesure désormais la hauteur réelle au chargement, la
remesure après le chargement des polices et à chaque redimensionnement, et
l'écrit dans `--h-nav`. Vérifié : écart de 0 px sur les trois pages.

Ce rideau ne doit s'activer **que** lorsque la barre est réellement épinglée
en haut. Deux défauts l'activaient à tort, et il recouvrait alors tout le
contenu situé au-dessus d'elle — un aplat brun sur toute la page :

1. **La sentinelle était au mauvais endroit.** Déclarée en
   `position:absolute; top:0`, sans aucun ancêtre positionné, elle se calait
   sur le bloc conteneur initial — donc en haut du document. Mesuré :
   sentinelle à 0, barre à 540. La barre se croyait épinglée sur toute la
   page. Elle est maintenant dans le flux, juste avant la barre, avec une
   marge négative qui annule son pixel de hauteur.
2. **`isIntersecting` est faux des deux côtés.** Sentinelle sortie par le
   haut, mais aussi passée sous le bas de la fenêtre. En **remontant**, la
   barre restait donc épinglée alors qu'elle redescendait dans la page. On
   n'épingle plus que si la sentinelle est sortie **par le haut**.

La marge du haut de l'observateur est lue dans `--h-nav`, la même variable que
le `top` de la barre : les deux ne peuvent pas diverger.

⚠️ Le volet d'aperçu **ne sait pas faire défiler** une page, ni dans un cadre
ni au premier plan : le geste ne peut pas être rejoué ici. Ce qui a été
vérifié : la sentinelle est à la position exacte de la barre sur les trois
pages (écart de 0 px), et la règle de décision passe les quatre situations,
dont celle qui échouait avant.

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

⚠️ **L'image de partage de l'accueil** (`og:image`) reste cette chambre. Ce
n'est pas faux — elle ne porte aucune légende — mais un lien partagé sur
WhatsApp montre une chambre plutôt que la paillote sur la lagune, qui est la
signature de l'établissement. À trancher avec la direction.

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
7. **Licence de la police** — le site d'origine utilise
   `MADE-TOMMY-Regular_PERSONAL-USE.otf`, dont la licence n'autorise pas
   l'usage commercial. La maquette n'utilise que des polices libres.

---

Conception et développement : **Léonardo Yann Axel HOUANSOU**
