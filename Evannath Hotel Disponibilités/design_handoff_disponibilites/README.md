# Handoff : Page « Disponibilités » — Evannath Hotel (back-office)

## Instruction principale pour Claude Code
**Respecte le design system déjà présent dans le projet Evannath Hotel.** Réutilise les composants existants (layout, sidebar, header, boutons, inputs, selects, cards, badges, icônes), les tokens (couleurs, polices, rayons, ombres, espacements) et les conventions (routing, state, appels API) du code. Les valeurs ci-dessous sont des références : si un token équivalent existe dans le projet, **utilise le token du projet**, pas la valeur hex.

La sidebar et le header existent probablement déjà : ne les recrée pas, ajoute seulement l'entrée de menu « Disponibilités » (active) et la nouvelle page.

## À propos des fichiers
`Disponibilites.dc.html` est une **maquette HTML de référence** (prototype interactif), pas du code de production. Il faut recréer cette page dans la stack du projet.

## Fidélité
Haute fidélité pour la structure, le contenu, les états et les interactions. Style visuel : aligner sur le design system existant.

---

## Structure de l'écran
```
┌ Sidebar (existante) ┬──────────────────────────────────────────────┐
│                     │ Header (existant) : recherche, notifs, profil │
│                     ├──────────────────────────────────────────────┤
│                     │ Titre + actions                               │
│                     │ ┌ Colonne principale ─────────┐ ┌ Panneau ─┐ │
│                     │ │ 5 cartes KPI                │ │ Détail    │ │
│                     │ │ Carte : filtres + planning  │ │ chambre   │ │
│                     │ └─────────────────────────────┘ └ 244px ────┘ │
└─────────────────────┴──────────────────────────────────────────────┘
```
Grille contenu : `grid-template-columns: minmax(0,1fr) 244px; gap: 14px`. Le panneau droit est fermable (×) → la colonne principale prend toute la largeur. Le panneau est `sticky` en haut.

### 1. En-tête de page
- H1 « Disponibilités » (≈34px, semi-bold) + sous-titre « Gérez l'état et la disponibilité de toutes vos chambres en temps réel. » (14px, gris).
- À droite : sélecteur de période `‹ [icône calendrier] 25 sept. 2026 – 1 oct. 2026 ›` (bouton secondaire), bouton secondaire « Aujourd'hui », bouton primaire doré « + Nouvelle réservation ».

### 2. Cartes KPI (5 colonnes égales)
Chaque carte : icône dans un cercle 44px (fond teinté clair + icône couleur), nombre (22px semi-bold), libellé (12px gris).
| KPI | Couleur icône | Fond cercle |
|---|---|---|
| Total chambres | #1f3a66 | #e6ecf6 |
| Disponibles | #2f9e4f | #dff3e2 |
| Occupées | #e0474c | #fde3e3 |
| Réservées | #e0850f | #fdebd6 |
| Indisponibles (maintenance + nettoyage) | #3b4455 | #eceef2 |
Valeurs calculées à partir des données (statut du jour courant).

### 3. Barre de filtres (dans la carte blanche du planning)
- Champ recherche « Rechercher une chambre… » (numéro ou type).
- 3 selects avec label flottant : **Type de chambre** (Tous, Standard, Deluxe, Suite, Executive), **Étage** (Tous, 1, 2, 3), **Statut** (Tous, Libre, Réservée, Occupée, Maintenance, Nettoyage).
- Checkbox « Afficher uniquement les disponibles ».

### 4. Barre de vue
- Gauche : segmented « Vue calendrier » / « Vue liste » (actif = fond bleu marine #0f1e33, texte blanc).
- Centre : `‹ 25 sept. 2026 – 1 oct. 2026 ›` (15px semi-bold).
- Droite : segmented « Jour / Semaine / Mois » (Semaine actif par défaut).
- Tout le texte des segmented reste sur une ligne (`white-space: nowrap`).

### 5. Planning (Vue calendrier)
Grille : `156px (Chambre/Type) | 52px (Étage) | 7 × 1fr (jours)`.
- En-tête jours : « Ven 25 sept. », « Sam 26 sept. »… Le jour courant a un fond bleu très clair #eef4fd, un texte #2563c9, et une colonne entière encadrée par une bordure bleue #3f86e6 de 1.5px.
- Ligne chambre (≈54px) : icône lit + numéro (12px gras) / type (11px) / literie (9.5px gris) ; étage centré.
- **Cellules de statut** : blocs arrondis (radius 3px, marge 3px, hauteur 44px), icône + libellé (11px) + nom client (9.5px). **Une réservation sur plusieurs nuits = un seul bloc qui s'étend sur plusieurs colonnes** (`grid-column: span N`).
- La cellule sélectionnée a un contour de 2px bleu marine.

| Statut | Fond | Texte | Icône |
|---|---|---|---|
| Libre | #bfe8bb | #1f4f2a | check dans un cercle vert #2f9e4f |
| Réservée | #fcc873 | #6b3f00 | calendrier #d9650a |
| Occupée | #3f86e6 | #fff | personne |
| Occupée – départ en retard / alerte | #e35d5d | #fff | personne |
| Maintenance | #8e8e8e | #fff | clé |
| Nettoyage | #9a6fe0 | #fff | étincelles |

État vide : « Aucune chambre ne correspond à ces filtres. »

### 5b. Vue liste
Tableau : Chambre | Type | Lits | Étage | Statut (jour courant, en badge coloré) | Client. Un clic sur une ligne ouvre le panneau.

### 6. Panneau détail (droite, 244px)
- Titre « Chambre 103 » + bouton fermer ×.
- Photo de la chambre (84×72, radius 4) + type (gras), literie, étage.
- **Détails de la réservation** (carte bordée) : Statut (badge couleur du statut), Du, Au (+ nombre de nuits), Tarif par nuit (ex. « 45 000 FCFA »), Client (ou « — »), Réservation n° (ex. « #RES-2026-078 » ou « — »).
- **Changer le statut** : liste radio (Disponible, Réservée, Occupée, Maintenance, Nettoyage) avec une pastille de couleur du statut.
- **Actions rapides** : « Créer une réservation » (primaire bleu marine), « Bloquer la chambre » (secondaire gris clair), « Modifier la réservation » (outline).
- **Notes** : textarea « Ajouter une note… », max 200 caractères, compteur « 0/200 ».

---

## Interactions
- Clic sur une cellule → sélectionne (chambre, jour) et ouvre le panneau avec les infos du bloc (dates de début et de fin de la réservation entière).
- Changer le statut → met à jour toute la réservation (toutes les nuits du bloc). « Libre » supprime le client et la référence.
- « Créer une réservation » → ouvre le formulaire / la modale de réservation du projet, préremplie avec la chambre et la date.
- « Bloquer la chambre » → statut Maintenance.
- « Modifier la réservation » → ouvre l'édition existante de la réservation.
- « Nouvelle réservation » (en-tête) → même formulaire, sans préremplissage.
- Flèches ‹ › → semaine précédente / suivante ; « Aujourd'hui » → semaine courante ; Jour / Semaine / Mois → nombre de colonnes (1 / 7 / jours du mois, avec scroll horizontal).
- Filtres et recherche → filtrent les lignes en direct ; les KPI restent sur l'ensemble de l'hôtel.
- Notes → enregistrées par chambre.
- Survol d'une cellule : légère baisse de luminosité (`filter: brightness(.96)`, 150ms).

## State / Données
```ts
type Status = 'libre'|'reservee'|'occupee'|'maintenance'|'nettoyage';
Room { id, number, type: 'Standard'|'Deluxe'|'Suite'|'Executive', bedding, floor, ratePerNight }
Booking { id, ref, roomId, guestName, checkIn: Date, checkOut: Date, status, isLate? }
RoomBlock { roomId, from, to, status: 'maintenance'|'nettoyage' }
UI state : period {start, mode}, view 'calendar'|'list', filters {q, type, floor, status, onlyAvailable}, selected {roomId, date}, panelOpen
```
Endpoints à brancher sur l'API existante : liste des chambres, réservations / blocages sur la période, mise à jour du statut, notes de chambre. Les jours sans réservation ni blocage sont « Libre ».

## Tokens de référence (à remplacer par ceux du projet)
- Bleu marine (sidebar, primaire foncé) : #0f1e33 · Or (accent, CTA) : #b8925a (hover #a57f48), or clair #c9a46a
- Fond app #f4f6fa · Cartes #fff, bordure #edf0f4 · Bordures inputs #e1e5ec · Séparateurs #eef1f5
- Texte #0f1e33 · Texte secondaire #5b6576 / #6b7686
- Rayons : cartes 8px, inputs/boutons 6px, cellules 3px
- Police du prototype : Outfit (UI) et Cormorant Garamond (logo) → **utiliser celles du projet**

## Données d'exemple utilisées
11 chambres (101–104 Standard/Deluxe à l'étage 1, 201–204 Suite à l'étage 2, 301–303 Executive à l'étage 3), semaine du 25 sept. au 1 oct. 2026. Tarifs : Standard 35 000, Deluxe 45 000, Suite 75 000, Executive 95 000 FCFA.

## Fichiers
- `Disponibilites.dc.html` : prototype de référence (logique et données dans la classe `Component` en bas du fichier).
- `reference.png` : capture d'origine.
