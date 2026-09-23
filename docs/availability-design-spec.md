# EVANNATH HOTEL — AVAILABILITY DESIGN SPECIFICATION

> ## ⚠️ REMPLACÉE — ne plus s'y référer
>
> **Statut : périmée le 23 septembre 2026.** La direction a validé une
> nouvelle maquette, `docs/availability-reference-v2.webp`, qui remplace
> celle-ci. Ce document est conservé pour l'historique, et pour les règles
> d'UX qui restent valables (sections 3 et suivantes) — mais **sa maquette,
> sa navigation et ses valeurs ne font plus foi.**
>
> Ce qui change : les lignes du calendrier sont des **chambres** et non des
> catégories, le panneau de droite est **permanent** au lieu d'un tiroir, et
> l'écran gagne des filtres et une recherche.
>
> Ce qui ne doit être repris d'**aucune** des deux maquettes : leurs chiffres.
> Elles montrent des catégories, des tarifs et des numéros de chambre
> inventés. Les vraies catégories et les vrais tarifs vivent dans
> `site/donnees/chambres.json` ; **les numéros de chambre, l'hôtel ne nous
> les a pas encore donnés.**
>
> Corriger aussi, dans toute maquette : « au cœur d'Abidjan ». L'hôtel est à
> **Assinie PK 19**, à environ 80 km.

> **Version:** 1.0  
> **Statut:** REMPLACÉE  
> **Page:** Disponibilités des chambres  
> **Application:** Back-office Evannath Hotel  
> **Référence visuelle:** `docs/availability-reference.png` (périmée)

---

# 1. OBJECTIF

Cette spécification définit l'apparence, la structure, l'expérience utilisateur et les règles fonctionnelles de la page :

`Disponibilités des chambres`

Cette page permet au personnel de l'hôtel de visualiser et gérer les disponibilités des chambres par :

- catégorie ;
- chambre individuelle ;
- date ;
- réservation ;
- blocage / maintenance.

L'objectif principal est de permettre à un utilisateur non technique de comprendre l'état de l'hôtel en quelques secondes et de modifier une disponibilité avec un minimum d'actions.

---

# 2. SOURCE DE VÉRITÉ

La référence visuelle principale est :

`docs/availability-reference.png`

La maquette représente la direction visuelle validée de la page.

## Règle fondamentale

**NE PAS REDESIGNER LA PAGE.**

Claude Code doit implémenter la maquette dans le projet existant.

Il ne doit pas :

- inventer une autre disposition ;
- changer la palette ;
- remplacer arbitrairement les composants ;
- transformer le calendrier en tableau générique ;
- ajouter des éléments visuels inutiles ;
- modifier la hiérarchie visuelle ;
- créer une nouvelle direction artistique.

Si une amélioration visuelle semble nécessaire, elle doit être explicitement demandée.

---

# 3. PRINCIPES UX

La page doit respecter les principes suivants :

1. Compréhension immédiate.
2. Peu d'actions pour modifier une disponibilité.
3. Informations importantes visibles sans ouvrir plusieurs pages.
4. Utilisation prioritaire sur desktop.
5. Design premium hôtelier.
6. Interface adaptée à un utilisateur non technique.
7. Les couleurs servent à comprendre l'état des chambres.
8. Les informations doivent être issues des données réelles.
9. Le calendrier est l'élément central.
10. Les réservations et blocages doivent influencer automatiquement les disponibilités.

---

# 4. STRUCTURE GLOBALE

La page est composée de :

```text
┌──────────────────────────────────────────────────────────────┐
│ HEADER                                                       │
├───────────────┬──────────────────────────────────────────────┤
│               │                                              │
│   SIDEBAR     │             MAIN CONTENT                     │
│               │                                              │
│               │  Page header                                 │
│               │  Calendar toolbar                            │
│               │  Availability calendar                       │
│               │  Quick overview                              │
│               │                                              │
│               ├──────────────────────────────┬───────────────┤
│               │                              │               │
│               │                              │ RIGHT PANEL   │
│               │                              │               │
│               │                              │ Summary       │
│               │                              │ Reservations  │
│               │                              │ Edit drawer   │
│               │                              │               │
└───────────────┴──────────────────────────────┴───────────────┘
```

---

# 5. SIDEBAR

La navigation doit reprendre le système de navigation existant du back-office Evannath.

## Navigation

```text
Tableau de bord

Chambres
  ├── Catégories
  ├── Chambres
  └── Disponibilités

Réservations

Clients

Promotions

Événements & Offres

Rapports

Paramètres
```

## État actif

`Disponibilités` doit être visuellement sélectionné.

Le style actif doit reprendre le design existant du back-office.

La couleur d'accent est une tonalité champagne / dorée.

---

# 6. HEADER

Le header doit conserver l'identité Evannath.

Contenu :

### Gauche

Logo :

`EVANNATH HOTEL`

Signature :

`Un séjour d'exception, au cœur d'Abidjan`

### Droite

- date actuelle ;
- utilisateur connecté ;
- avatar ;
- rôle ;
- menu utilisateur.

Exemple :

```text
Mer. 24 Sept. 2026

L. Yann
Administrateur
⌄
```

---

# 7. PAGE HEADER

Titre :

```text
Disponibilités des chambres
```

Icône :

Calendrier.

Sous-titre :

```text
Gérez facilement la disponibilité de vos chambres par catégorie et par date.
```

## Actions principales

À droite :

### Bouton principal

`+ Nouvelle réservation`

Style :
- fond sombre ou accent Evannath ;
- texte clair ;
- hauteur confortable ;
- rayon modéré.

### Bouton secondaire

`Modifier en lot`

Style plus discret.

---

# 8. CALENDRIER

Le calendrier est le composant principal de la page.

## Toolbar

Afficher :

```text
‹    ›    Septembre 2026   ⌄
```

Puis :

```text
Vue mois
Vue semaine
Vue jour
```

La vue par défaut est :

`Vue mois`

---

# 9. GRILLE DU CALENDRIER

Les dates sont affichées horizontalement.

Exemple :

```text
             Mer 23   Jeu 24   Ven 25   Sam 26   Dim 27   Lun 28   Mar 29
```

La date actuelle doit être visuellement mise en évidence.

Les colonnes doivent avoir une largeur suffisante pour conserver la lisibilité.

La grille doit être horizontalement scrollable si nécessaire.

---

# 10. CATÉGORIES DE CHAMBRES

Chaque catégorie constitue une section.

Exemple :

```text
Chambre Standard
À partir de 35 000 FCFA / nuit

6 Total
4 Occupées
2 Disponibles
```

Puis les disponibilités quotidiennes :

```text
2/6
2/6
1/6
0/6
1/6
2/6
3/6
```

---

# 11. CATÉGORIES INITIALES

Les données de démonstration de la maquette utilisent :

## Chambre Standard

- Total : 6
- Tarif : 35 000 FCFA / nuit

## Chambre Deluxe

- Total : 4
- Tarif : 50 000 FCFA / nuit

## Suite

- Total : 2
- Tarif : 80 000 FCFA / nuit

Ces valeurs ne doivent PAS être hardcodées dans l'application finale.

Elles servent uniquement de référence visuelle.

Les données réelles doivent provenir de la base de données.

---

# 12. INFORMATIONS D'UNE CATÉGORIE

Chaque catégorie doit afficher :

- image ;
- nom ;
- prix de base ;
- nombre total ;
- nombre occupé ;
- nombre disponible ;
- disponibilité par date.

Exemple :

```text
┌─────────────────────────────────────────────┐
│ [IMAGE]  Chambre Deluxe                    │
│          À partir de 50 000 FCFA / nuit    │
│                                             │
│          4       2       2                  │
│        Total  Occupées Disponibles          │
└─────────────────────────────────────────────┘
```

---

# 13. CELLULE DE DISPONIBILITÉ

Chaque cellule représente une catégorie pour une date.

Format :

```text
2/4
```

Signification :

```text
2 chambres disponibles
sur 4 chambres au total
```

La cellule doit également afficher un indicateur d'état.

---

# 14. ÉTATS DE DISPONIBILITÉ

## DISPONIBLE

Condition :

Disponibilité normale.

Couleur :

Vert.

Exemple :

```text
2/6
●
```

---

## FAIBLE DISPONIBILITÉ

Condition :

Il reste peu de chambres disponibles.

Couleur :

Orange / ambre.

Exemple :

```text
1/6
●
```

Le seuil doit être configurable.

Par défaut :

```text
available / total <= 30%
```

---

## COMPLET

Condition :

```text
available === 0
```

Couleur :

Rouge.

Exemple :

```text
0/6
●
```

---

## HORS SERVICE

Lorsqu'une ou plusieurs chambres sont temporairement indisponibles pour une raison technique ou opérationnelle.

Couleur :

Gris.

Raison possible :

- maintenance ;
- travaux ;
- problème technique ;
- nettoyage exceptionnel ;
- usage interne.

---

# 15. CHAMBRES INDIVIDUELLES

Sous une catégorie, les chambres individuelles peuvent être affichées.

Exemple :

```text
Chambre 101
Chambre 102
Chambre 103
Chambre 104
Chambre 105
Chambre 106
```

Chaque chambre possède un statut pour chaque date.

Statuts possibles :

```text
Disponible
Occupée
Réservée
Hors service
```

---

# 16. STATUTS DES CHAMBRES

## Disponible

Vert.

## Occupée

Bleu.

## Réservée

Jaune / ambre.

## Hors service

Gris.

Ne jamais utiliser uniquement la couleur pour communiquer une information importante.

Le texte du statut doit également être accessible.

---

# 17. INTERACTION AVEC UNE CELLULE

Lorsqu'un utilisateur clique sur une cellule de disponibilité :

Exemple :

```text
Chambre Deluxe
Vendredi 25 septembre 2026
```

ouvrir un drawer latéral.

---

# 18. DRAWER — MODIFIER LA DISPONIBILITÉ

Titre :

```text
Modifier la disponibilité
```

Contenu :

```text
Chambre Deluxe
Vendredi 25 septembre 2026
```

Puis :

```text
Total des chambres     4

Réservées              3

Hors service           0

Disponibles            1
```

---

# 19. AJUSTEMENT DE DISPONIBILITÉ

Afficher :

```text
Ajuster la disponibilité

[-]     1     [+]
```

Les boutons doivent être facilement cliquables.

Ne jamais permettre une disponibilité négative.

La disponibilité ne peut pas dépasser le nombre de chambres réellement actives dans la catégorie.

---

# 20. STATUT MANUEL

Permettre :

```text
○ Disponible
○ Complet
○ Hors service
```

Le statut manuel ne doit pas écraser silencieusement les réservations existantes.

Si une action entraîne un conflit avec une réservation existante, afficher un avertissement explicite.

---

# 21. COMMENTAIRE

Ajouter un champ facultatif :

```text
Commentaire
```

Placeholder :

```text
Ex. : maintenance, travaux, problème technique...
```

Le commentaire doit être enregistré avec le blocage lorsqu'il s'agit d'une mise hors service.

---

# 22. BOUTON DE SAUVEGARDE

Bouton principal :

```text
Enregistrer les modifications
```

Après sauvegarde :

- fermer le drawer ;
- actualiser la cellule ;
- actualiser les compteurs ;
- afficher une notification de succès.

Exemple :

```text
✓ Disponibilité mise à jour
```

---

# 23. MODIFICATION EN LOT

Le bouton :

```text
Modifier en lot
```

permet de modifier plusieurs dates ou plusieurs chambres.

L'utilisateur doit pouvoir sélectionner :

- catégorie ;
- chambre(s) ;
- date de début ;
- date de fin ;
- action ;
- raison.

Exemples :

```text
Mettre hors service
Rendre disponible
Bloquer
```

Avant validation, afficher un résumé :

```text
Vous êtes sur le point de mettre :

3 chambres Deluxe
du 25 au 28 septembre

hors service.

[Annuler] [Confirmer]
```

---

# 24. COLONNE DROITE

La colonne droite contient des informations complémentaires.

Elle ne doit pas prendre le dessus sur le calendrier.

---

# 25. CARTE « AUJOURD'HUI »

Afficher :

```text
Aujourd'hui — 24 sept. 2026
```

Puis :

```text
🟢 12
Disponibles

🟠 4
Peu de chambres

🔴 4
Complet
```

Les valeurs sont dynamiques.

---

# 26. PROCHAINES RÉSERVATIONS

Afficher les prochaines réservations pertinentes.

Exemple :

```text
Prochaines réservations                Voir tout

M. Koné
Chambre Standard — 2 chambres
Arrivée 24 sept. → Départ 27 sept.
Confirmée

Mme Traoré
Chambre Deluxe — 1 chambre
Arrivée 27 sept. → Départ 28 sept.
Confirmée

M. Diarra
Suite — 1 chambre
Arrivée 26 sept. → Départ 29 sept.
En attente
```

Les informations doivent provenir du système de réservation existant.

---

# 27. VUE D'ENSEMBLE RAPIDE

Sous le calendrier, afficher une synthèse.

Exemple :

```text
Vue d'ensemble rapide

Standard
2 / 6 disponibles
██████░░░░ 33%

Deluxe
2 / 4 disponibles
█████░░░░░ 50%

Suite
1 / 2 disponibles
█████░░░░░ 50%
```

Les pourcentages doivent être calculés dynamiquement.

---

# 28. LÉGENDE

Afficher :

```text
Statut des chambres

● Disponible
● Peu de chambres
● Complet
● Hors service
```

Ajouter :

```text
Total des chambres : 21
```

Le total doit être calculé à partir des chambres actives.

---

# 29. LOGIQUE MÉTIER

La disponibilité doit être calculée dynamiquement.

Formule générale :

```text
Disponibles =
Chambres actives
- Chambres réservées
- Chambres bloquées / hors service
```

Ne jamais utiliser un nombre statique pour représenter une disponibilité réelle.

---

# 30. RÈGLE CHECK-IN / CHECK-OUT

Une réservation occupe une chambre :

```text
checkIn inclus
checkOut exclus
```

Exemple :

```text
Arrivée : 24 septembre
Départ : 27 septembre
```

La chambre est occupée les :

```text
24
25
26
```

Elle redevient disponible pour une nouvelle réservation à partir du :

```text
27
```

Cette règle doit être appliquée partout.

---

# 31. STATUTS DE RÉSERVATION

Les réservations doivent être traitées selon leur statut.

Au minimum :

```text
Confirmée
En attente
Annulée
Terminée
```

Une réservation annulée ne doit plus réduire la disponibilité.

Le comportement des réservations « En attente » doit suivre la règle métier définie par le système existant.

Ne pas inventer une règle différente dans cette page.

---

# 32. CHAMBRES HORS SERVICE

Une chambre hors service doit être retirée du stock disponible pendant sa période de blocage.

Exemple :

```text
4 chambres Deluxe

3 réservées
1 hors service

Disponibles = 0
```

La catégorie est donc :

```text
COMPLET
```

---

# 33. CONFLITS

Le système doit détecter les conflits.

Exemple :

Une chambre possède une réservation confirmée.

L'administrateur tente de la mettre hors service pendant cette période.

Ne pas effectuer silencieusement l'opération.

Afficher :

```text
Attention

Cette chambre possède une réservation confirmée
sur cette période.

Vous ne pouvez pas la mettre hors service
sans traiter d'abord la réservation.

[Annuler]
```

---

# 34. DONNÉES

Utiliser les modèles déjà présents dans le projet.

Les concepts nécessaires sont :

```text
RoomCategory
Room
Reservation
RoomBlock
Customer
```

Ne pas créer de doublons si des modèles équivalents existent déjà.

---

# 35. ROOM CATEGORY

Conceptuellement :

```text
id
name
description
image
basePrice
active
```

---

# 36. ROOM

Conceptuellement :

```text
id
number
categoryId
status
active
```

---

# 37. RESERVATION

Conceptuellement :

```text
id
customerId
roomId / roomCategoryId
checkIn
checkOut
numberOfRooms
status
```

Adapter au modèle réel de l'application.

---

# 38. ROOM BLOCK

Conceptuellement :

```text
id
roomId / categoryId
startDate
endDate
reason
status
```

Utiliser les dates avec la même convention :

```text
startDate inclus
endDate exclus
```

---

# 39. PERFORMANCE

Ne jamais effectuer une requête réseau pour chaque cellule du calendrier.

Mauvais :

```text
cell 1 → API
cell 2 → API
cell 3 → API
...
```

Préférer :

```text
1 requête période
        ↓
données chambres
        +
réservations
        +
blocages
        ↓
calcul des disponibilités
```

Les données nécessaires à la période affichée doivent être récupérées efficacement.

---

# 40. CHANGEMENT DE MOIS

Lorsque l'utilisateur passe au mois suivant :

```text
Septembre → Octobre
```

charger uniquement les données nécessaires.

Afficher un état de chargement élégant pendant la récupération.

Ne pas bloquer toute l'application.

---

# 41. ÉTATS UI

La page doit gérer :

### Loading

Afficher des skeletons correspondant à la structure réelle.

Ne pas afficher un spinner plein écran inutilement.

### Empty state

Si aucune catégorie n'existe :

```text
Aucune catégorie de chambre

Commencez par créer une catégorie
pour gérer ses disponibilités.

[Créer une catégorie]
```

### Aucun résultat

Si aucune réservation n'existe :

```text
Aucune réservation à venir
```

### Erreur

Afficher :

```text
Impossible de charger les disponibilités.

[Réessayer]
```

### Sauvegarde réussie

Afficher une notification discrète :

```text
✓ Modifications enregistrées
```

### Erreur de sauvegarde

```text
Impossible d'enregistrer les modifications.

Vérifiez votre connexion puis réessayez.
```

---

# 42. DESIGN SYSTEM

La page doit utiliser le design system existant d'Evannath.

Si des tokens existent déjà dans le projet, les réutiliser.

Ne pas créer une deuxième palette concurrente.

## Direction visuelle

Identité :

```text
Premium
Hôtel
Élégant
Contemporain
Chaleureux
Professionnel
```

---

# 43. COULEURS

Les couleurs sont indicatives si le projet possède déjà des tokens équivalents.

## Primary dark

Utilisé pour :

- header ;
- boutons principaux ;
- titres importants ;
- navigation.

Direction :

```text
#111820
```

## Champagne / Gold

Utilisé pour :

- accents ;
- navigation active ;
- boutons premium ;
- détails Evannath.

Direction :

```text
#B08A52
```

## Background

```text
#F7F6F3
```

ou équivalent du design system existant.

## Surface

```text
#FFFFFF
```

## Success

Vert discret.

Direction :

```text
#16834A
```

## Warning

Orange / ambre.

Direction :

```text
#D98B16
```

## Danger

Rouge.

Direction :

```text
#D92D3A
```

## Muted

Gris neutre.

---

# 44. TYPOGRAPHIE

La typographie doit reprendre celle déjà utilisée dans le projet.

Hiérarchie :

```text
Page title
→ grand, élégant, fort

Section title
→ moyen, semi-bold

Body
→ lisible et neutre

Metadata
→ plus petite, discrète

Status
→ court, semi-bold
```

Ne pas introduire plusieurs polices sans nécessité.

---

# 45. ESPACEMENTS

Le design doit respirer.

Utiliser les tokens d'espacement du projet.

À défaut :

```text
4px
8px
12px
16px
20px
24px
32px
40px
48px
```

Éviter les espacements arbitraires.

---

# 46. BORDURES ET RAYONS

Les cartes doivent avoir :

- bordures très légères ;
- rayons modérés ;
- ombres discrètes.

Éviter les cartes extrêmement arrondies de type SaaS générique.

Le rendu doit rester hôtelier et premium.

---

# 47. RESPONSIVE

La priorité est :

```text
Desktop
```

La largeur doit être optimisée pour les écrans de back-office.

Sur tablette :

- permettre le scroll horizontal du calendrier ;
- conserver les informations importantes ;
- garder le drawer utilisable.

Sur mobile :

- transformer le drawer en modal/drawer plein écran ;
- rendre le calendrier horizontalement scrollable ;
- conserver les dates lisibles ;
- ne jamais écraser les colonnes pour tout faire tenir artificiellement.

---

# 48. ACCESSIBILITÉ

Respecter :

- navigation clavier ;
- focus visible ;
- labels explicites ;
- boutons accessibles ;
- contraste suffisant ;
- aria-label lorsque nécessaire ;
- ne pas dépendre uniquement des couleurs.

Exemple :

Une cellule complète ne doit pas communiquer uniquement :

```text
🔴
```

Elle doit pouvoir être comprise comme :

```text
0/6 — Complet
```

---

# 49. MICRO-INTERACTIONS

Les animations doivent être discrètes.

Autorisé :

- hover léger ;
- transition de couleur ;
- ouverture fluide du drawer ;
- feedback lors de sauvegarde ;
- changement de mois fluide.

Éviter :

- animations excessives ;
- effets 3D ;
- mouvements permanents ;
- éléments qui attirent inutilement l'attention.

Le back-office doit rester rapide et professionnel.

---

# 50. RÈGLE DE COHÉRENCE

Toutes les interactions doivent utiliser les composants existants du projet lorsqu'ils existent :

- Button
- Modal
- Drawer
- Badge
- Tooltip
- Toast
- Input
- Select
- DatePicker
- Dropdown
- Skeleton

Ne pas créer une deuxième version de ces composants uniquement pour cette page.

---

# 51. ARCHITECTURE FRONT-END RECOMMANDÉE

Si compatible avec l'architecture existante :

```text
AvailabilityPage
│
├── AvailabilityHeader
│
├── AvailabilityToolbar
│
├── AvailabilityCalendar
│   ├── DateHeader
│   ├── RoomCategorySection
│   │   ├── CategorySummary
│   │   ├── AvailabilityCell
│   │   └── RoomRow
│   │
│   └── AvailabilityLegend
│
├── AvailabilityOverview
│
├── AvailabilitySidebar
│   ├── TodaySummary
│   └── UpcomingReservations
│
└── EditAvailabilityDrawer
```

Adapter les noms aux conventions du projet.

---

# 52. SÉPARATION DES RESPONSABILITÉS

Ne pas placer toute la logique dans le composant principal.

Prévoir idéalement :

```text
UI components
        ↓
hooks / state
        ↓
services
        ↓
API / database
```

Les calculs de disponibilité doivent être isolés dans une couche réutilisable.

---

# 53. FONCTION DE CALCUL

Prévoir conceptuellement une fonction :

```text
calculateAvailability(
    rooms,
    reservations,
    blocks,
    dateRange
)
```

Elle doit retourner une structure exploitable par le calendrier.

Exemple conceptuel :

```text
{
  date: "2026-09-25",
  categoryId: "...",
  total: 4,
  reserved: 3,
  blocked: 0,
  available: 1,
  status: "low"
}
```

Ne pas nécessairement utiliser exactement cette structure si l'architecture actuelle en possède une meilleure.

---

# 54. RÈGLE DE VÉRITÉ DES DONNÉES

Le calendrier n'est jamais la source de vérité.

La source de vérité est :

```text
Database
```

Le calendrier est une représentation calculée des données.

Ne pas enregistrer arbitrairement :

```text
available = 1
```

sans conserver les informations permettant d'expliquer pourquoi il reste 1 chambre.

---

# 55. ORDRE DE PRIORITÉ

En cas de conflit entre éléments :

```text
1. Données réelles
2. Règles métier
3. UX
4. Design system Evannath
5. Maquette de référence
6. Préférences esthétiques secondaires
```

Ne jamais sacrifier la cohérence des données pour reproduire visuellement une maquette.

---

# 56. DESIGN LOCK

Cette section est obligatoire.

## DESIGN LOCK

La maquette :

`docs/availability-reference.png`

et cette spécification :

`docs/availability-design-spec.md`

constituent la référence de la page.

Claude Code ne doit pas :

- redesign la page ;
- changer le layout ;
- changer la palette ;
- remplacer le calendrier par un autre modèle ;
- supprimer les panneaux d'information ;
- ajouter des sections non prévues ;
- déplacer arbitrairement les composants ;
- modifier la hiérarchie visuelle.

Si une modification est techniquement nécessaire, conserver au maximum l'apparence et l'expérience de la référence.

Si une amélioration est souhaitée, attendre une instruction explicite.

---

# 57. DONNÉES FICTIVES

Les données visibles dans la maquette :

```text
Standard
6 chambres

Deluxe
4 chambres

Suite
2 chambres
```

ainsi que les noms :

```text
M. Koné
Mme Traoré
M. Diarra
```

sont uniquement des exemples visuels.

Ils ne doivent pas être ajoutés comme données persistantes.

L'application doit utiliser les données réelles.

---

# 58. CRITÈRES D'ACCEPTATION

La page est considérée comme terminée uniquement si :

### Design

- [ ] La page respecte la maquette de référence.
- [ ] La navigation existante est conservée.
- [ ] La palette Evannath est respectée.
- [ ] La hiérarchie visuelle est respectée.
- [ ] Le calendrier est lisible.
- [ ] Les états sont immédiatement compréhensibles.

### Fonctionnel

- [ ] Les catégories viennent de la base.
- [ ] Les chambres viennent de la base.
- [ ] Les réservations viennent de la base.
- [ ] Les disponibilités sont calculées.
- [ ] Les réservations annulées ne bloquent pas les chambres.
- [ ] Les check-in/check-out sont correctement interprétés.
- [ ] Les chambres hors service sont déduites.
- [ ] Les conflits sont détectés.
- [ ] Une cellule peut être modifiée.
- [ ] Les modifications sont sauvegardées.
- [ ] Le calendrier est actualisé après sauvegarde.
- [ ] La modification en lot fonctionne si implémentée.
- [ ] Les prochaines réservations sont réelles.

### Technique

- [ ] Pas de requête API par cellule.
- [ ] Pas de données métier hardcodées.
- [ ] Pas de duplication inutile des composants.
- [ ] TypeScript sans erreur.
- [ ] Lint sans erreur.
- [ ] États loading/error/empty gérés.
- [ ] Responsive fonctionnel.
- [ ] Accessibilité minimale respectée.

---

# 59. RÈGLE FINALE POUR CLAUDE CODE

Avant toute modification importante, analyser l'architecture existante.

Ne pas reconstruire ce qui existe déjà.

Ne pas créer un système parallèle.

Ne pas transformer cette page en prototype isolé.

Cette fonctionnalité doit devenir une partie native du back-office Evannath Hotel.

**La maquette définit l'apparence.**

**Cette spécification définit le comportement attendu.**

**L'architecture existante définit la manière de l'intégrer.**

Le résultat final doit donner l'impression que cette fonctionnalité a toujours fait partie du back-office Evannath.