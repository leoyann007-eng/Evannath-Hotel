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

## Les 11 pages

| Fichier | Page |
|---|---|
| `index.html` | Accueil — hero, réservation, 7 catégories, expériences, avis, accès |
| `galerie.html` | Galerie — 47 photographies, 6 filtres, visionneuse |
| `suite-arabe.html` | Fiche chambre — Suite Arabe, calcul de séjour en direct |
| `circuits.html` | Circuits & Offres — 4 Packs Vacances + 6 circuits + Méchoui Party |
| `carte.html` | La table — 94 articles, recherche instantanée, réservation |
| `spa.html` | Le spa — 22 soins, 4 rituels en vedette |
| `a-propos.html` | À propos — « Akwaba », 6 arguments, 5 espaces, 13 équipements |
| `contact.html` | Contact — 4 canaux, formulaire validé, carte d'accès |
| `informations-utiles.html` | 17 questions en accordéon |
| `mentions-legales.html` | Mentions légales — trame à compléter |
| `404.html` | Page introuvable |

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
demo/
├── *.html                  les 11 pages servies
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
cd demo
python build-carte.py      # carte.html + spa.html
python build-galerie.py    # galerie.html (+ optimise les photos manquantes)
python build-404.py        # 404.html
python build-pages.py      # a-propos.html
python build-pages2.py     # contact.html
python build-pages3.py     # informations-utiles.html
python build-pages4.py     # mentions-legales.html
python build-pages5.py     # suite-arabe.html
python build-pages6.py     # circuits.html
```

`index.html` est écrit à la main et n'a pas de générateur.

Dépendance unique : **Pillow** (`pip install Pillow`), pour l'optimisation des
images dans `build-galerie.py`.

## Régénérer les images

Les scripts d'optimisation lisent les originaux dans `demo/img/`. S'ils sont
absents, il faut les retélécharger depuis la médiathèque de l'hôtel
(`https://evannathhotel.com/wp-json/wp/v2/media?per_page=100&page=1..5`) puis
relancer `build-galerie.py`, qui ne régénère que les fichiers manquants.

## Prévisualiser en local

```bash
cd demo
python -m http.server 5599
```

Puis ouvrir <http://localhost:5599>.

---

## Déploiement

Hébergé sur **Vercel**, en site statique — aucune étape de compilation.
`vercel.json` définit `demo/` comme racine servie, active les URL sans `.html`
et met en cache les images un an.

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
5. **Licence de la police** — le site d'origine utilise
   `MADE-TOMMY-Regular_PERSONAL-USE.otf`, dont la licence n'autorise pas
   l'usage commercial. La maquette n'utilise que des polices libres.

---

Conception et développement : **Léonardo Yann Axel HOUANSOU**
