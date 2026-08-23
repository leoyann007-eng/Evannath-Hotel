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
5. **Capacités de la salle de séminaire** — les cinq configurations de
   `seminaires.html` (théâtre 60, classe 35, en U 25, cocktail 90, banquet 70)
   sont des hypothèses : l'établissement ne publie aucun chiffre. À remplacer
   par les capacités réelles avant mise en production.
6. **Licence de la police** — le site d'origine utilise
   `MADE-TOMMY-Regular_PERSONAL-USE.otf`, dont la licence n'autorise pas
   l'usage commercial. La maquette n'utilise que des polices libres.

---

Conception et développement : **Léonardo Yann Axel HOUANSOU**
