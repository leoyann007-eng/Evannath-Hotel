# Cahier des exigences — ce que le site fait déjà, ce qui manque

Analyse du *Cahier des exigences — Refonte du site internet d'Evannath Hotel*
(reçu le 7 octobre 2026), point par point, contre le site tel qu'il est sur
`main` à cette date.

Légende : ✅ fait · 🟡 en partie · ❌ absent · 🏨 dépend de l'hôtel (contenu,
compte, décision), pas du code.

---

## En une page

Le cahier pose dix exigences non négociables (§ 31). Voici où en est le site :

| # | Exigence | État | Ce qui manque |
|---|---|---|---|
| 1 | Réservation directe | 🟡 | Le parcours existe : dates, disponibilité, chambre, prix, acompte en ligne. Il manque l'inventaire réel des chambres 🏨 et la clé de paiement réelle 🏨. |
| 2 | WhatsApp commercial | 🟡 | Le bouton flottant existe, mais sans message prérempli. Il n'y a pas de boutons dédiés : « Réserver sur WhatsApp », « Organiser mon séminaire »… |
| 3 | Mobile first | ✅ | Audité sur iPhone ; barre « Réserver » collée en bas des fiches chambres. |
| 4 | SEO | 🟡 | Les bases techniques sont là. Il manque les pages qui visent les recherches (« que faire à Assinie », « mariage Assinie »…), le blog et la Search Console. |
| 5 | Pages commerciales | 🟡 | Week-ends, séminaires, restaurant et expériences sont faits. **Il n'y a pas de page Événements privés** : mariages, baptêmes, anniversaires… |
| 6 | Tracking | ❌ | Aucune mesure d'audience ni des clics. |
| 7 | Un appel à l'action par page | ✅ | Chaque page a son bouton : réserver, devis, table, rendez-vous ou WhatsApp. |
| 8 | CRM | ❌ | Les demandes partent par e-mail et ne sont gardées nulle part. Il n'y a ni suivi ni relance. |
| 9 | Propriété Evannath | 🟡 🏨 | Le domaine est à l'hôtel (LWS). **Vercel, GitHub et la base sont encore sur des comptes personnels**, à transférer. |
| 10 | Mesurer demandes, réservations et CA | ❌ | Il faut d'abord le tracking (6) et le CRM (8). |

**En résumé** : la vitrine et le tunnel de vente sont solides. Ce qui manque
tient en trois blocs :

1. **Mesurer** : analytics et suivi des conversions.
2. **Garder et relancer les prospects** : demandes enregistrées, suivi
   commercial, relances, capture de contacts.
3. **Quelques pages de contenu** : événements privés, guide Assinie, avis
   clients, carnet.

---

## Point par point

### 1–2. Objectifs et positionnement

- **Attirer** 🟡 : voir SEO (§ 19) et tracking (§ 23).
- **Convertir** ✅ : il y a cinq formulaires (réservation, devis séminaire,
  contact, table, spa), le WhatsApp, le chatbot qui passe la main à la
  réception, et l'acompte en ligne.
- **Fidéliser** ❌ : le site ne recueille aucun contact hors demande, et ne
  sollicite aucun avis après le séjour.

### 3. Page d'accueil — premier écran 🟡

Ce qui est fait :

- photo immersive ;
- lieu affiché (« Assinie · PK 19 · Lagune Aby ») ;
- boutons « Réserver en direct » et « Voir les chambres » ;
- barre de réservation avec dates, voyageurs, catégorie et **prix estimé**.

À faire :

- Un sous-titre qui dise tout de suite l'étendue de l'offre : *Séjours ·
  Week-ends · Séminaires · Événements*. Aujourd'hui le premier écran ne parle
  que de chambres.
- Deux boutons de plus, **WhatsApp** et **Demander un devis**. Il faut les
  ajouter sans surcharger : sur mobile, deux gros boutons et deux liens
  discrets.
- Le titre « Le rêve africain, en vrai » peut rester : c'est la signature de
  l'hôtel. Le cahier propose « Votre évasion commence à Assinie ». C'est à
  trancher avec la direction 🏨.

### 4. Ce que l'accueil doit montrer 🟡

Déjà sur l'accueil : chambres, spa et sauna, séminaires, restaurant, offres
du moment (bandeau), expériences.

Manquent :

- **les avis clients** (§ 15) ;
- **un bloc Assinie** qui renvoie au futur guide (§ 13) ;
- **un bloc Événements privés** qui renvoie à la future page (§ 11).

### 5. Réservation directe 🟡

Le parcours demandé existe tel quel :

1. dates ;
2. disponibilité, interrogée en direct (`/api/admin?a=dispo`, tenue depuis
   l'onglet **Disponibilités** de l'administration) ;
3. catégorie ;
4. prix ;
5. coordonnées ;
6. acompte de 30 % par Wave, MTN ou carte (lomi).

La barre « Réserver » est collée en bas d'écran sur les fiches chambres.

Ce qui bloque la mise en service réelle, et ne se règle pas dans le code :

- 🏨 **La liste réelle des chambres physiques** par catégorie, toujours
  attendue de la direction. Sans elle, la disponibilité reste « à confirmer ».
- 🏨 **La clé lomi de production**. Le paiement tourne aujourd'hui en mode
  test.

### 6. WhatsApp commercial 🟡

Le bouton flottant est là, sur toutes les pages. Mais :

- il ouvre une conversation **vide** ;
- le message n'est prérempli que dans le chatbot et dans le secours des
  formulaires.

À faire, c'est rapide :

- **Préremplir selon la page et ce que le visiteur a choisi**. Sur une fiche
  chambre : *« Bonjour Evannath, je souhaite connaître les disponibilités de
  la Suite Arabe du 12 au 14 décembre pour 2 personnes. »* Sur Séminaires :
  *« … organiser un séminaire pour … participants. »*
- **Des boutons dédiés** aux bons endroits :
  - « Réserver sur WhatsApp » sur les fiches et les offres ;
  - « Organiser mon séminaire » ;
  - « Organiser mon événement ».
- **Compter les clics** (voir § 23).

### 7. Page « Nos chambres » 🟡

Les sept fiches ont déjà : photos, capacité, literie, vue, équipements,
conditions, tarif, bouton réserver, et un texte qui vend l'expérience
(« L'essentiel, fait comme il faut… »).

Manquent :

- 🏨 **la superficie** en m², à mesurer par l'hôtel ;
- 🏨 **une vidéo courte** par catégorie, verticale, 15–30 s. La place est
  prévue, il faut les tournages ;
- **la salle de bain** : aujourd'hui une seule ligne (« salle d'eau
  privative »). Une ligne de plus par fiche suffit : douche ou baignoire,
  produits.

### 8. Page « Nos offres » 🟡

`circuits.html` (« Offres & Événements ») présente onze offres avec prix.
Plusieurs correspondent à la liste du cahier :

| Demandé par le cahier | Offre existante |
|---|---|
| Week-end couple | Pack Couple |
| Week-end famille | Pack Famille |
| Romantic escape | Évasion Romantique |
| 48 h à Assinie | Week-End Intense |
| Offre anniversaire | Coffret Anniversaire |

Manquent :

- **Offre séminaire** et **Offre team building**, en forfaits avec prix, à
  composer avec l'hôtel 🏨 ;
- **une période de validité** sur chaque offre ;
- **des conditions écrites** sur chaque offre.

Les campagnes saisonnières existent déjà dans l'administration. Il suffit
d'en afficher les dates.

### 9. Page « Expériences » ✅

La page existe : sur le domaine, sur l'eau, autour d'Assinie.

Manquent seulement **brunch** et **sunset**, s'ils existent vraiment 🏨. Le
mot « brunch » n'apparaît nulle part sur le site. On ne l'invente pas.

### 10. Séminaires & entreprises 🟡

Déjà sur la page : salle, capacités, cinq configurations, équipements
compris, formules, hébergement, piscine et activités, formulaire de devis.

À ajouter :

- **au formulaire** : *nombre de chambres* et *type d'événement*, deux champs
  à ajouter dans `api/envoyer.js` et dans la page ;
- **une section team building**, contenu 🏨 ;
- **des témoignages d'entreprises**, de vrais clients seulement, avec leur
  accord 🏨 ;
- **la restauration et les pauses** : à détailler davantage, contenu 🏨.

### 11. Page « Événements » ❌ — le plus gros manque de contenu

`circuits.html` montre les événements **organisés par l'hôtel** : Réveillon,
Méchoui Party. Rien ne s'adresse à qui veut **organiser le sien** : mariage,
baptême, anniversaire, fête privée, lancement de produit.

Il faut une page dédiée, construite comme la page Séminaires :

- les espaces et leur capacité (paillote, terrasse, piscine, salle) ;
- restauration ;
- décoration ;
- hébergement des invités ;
- photos ;
- un formulaire **« Demander un devis événement »** : type d'événement,
  date, nombre d'invités, chambres, budget indicatif, besoins.

🏨 Il faut à l'hôtel : les capacités par espace, les prestations réellement
proposées, et des photos d'événements passés.

### 12. Restaurant ✅

`carte.html` présente le concept, l'ambiance, la carte complète avec prix,
des photos, et un formulaire de réservation de table **ouvert à tous**, pas
seulement aux clients de l'hôtel. L'idée commerciale du cahier est donc déjà
en place. La Méchoui Party du samedi est d'ailleurs annoncée « ouverte aux
visiteurs de passage ».

À compléter :

- horaires bien visibles en tête de page ;
- plats signatures mis en avant ;
- brunch 🏨 (voir § 9).

### 13. Page « Assinie » ❌

Il y a des morceaux, mais dispersés :

- « Autour d'Assinie » sur la page Expériences ;
- l'accès et les conseils dans Informations utiles.

Il manque une vraie page **« Que faire à Assinie ? »** : plages, lagune,
activités nautiques, sorties, restaurants, idées de week-end. C'est la page
la plus utile pour le référencement : elle répond aux recherches de gens qui
ne connaissent pas encore l'hôtel. Une page statique de plus, construite comme
les autres, avec ses paragraphes en anglais.

### 14. Blog « Le Carnet d'Assinie » ❌

Le site est généré par des scripts Python. Un carnet s'y ajoute bien :

- un dossier d'articles en Markdown ;
- un générateur qui produit la page de liste et une page par article ;
- le sitemap mis à jour.

Il faut décider **qui écrit** 🏨. Un carnet qui reste avec trois articles de
2026 fait plus de tort que pas de carnet du tout. Il faut au moins un article
par mois, sinon mieux vaut ne pas l'ouvrir.

Variante plus légère : publier les articles depuis l'administration, comme
les offres d'emploi. Plus de développement, mais l'hôtel devient autonome.

### 15. Avis clients ❌

Le site ne montre **aucun avis**. Le cahier insiste, à juste titre : *ne pas
inventer*. Deux façons honnêtes :

1. **La note Google et quelques avis Google réels**, recopiés avec le nom tel
   qu'affiché publiquement et un lien vers la fiche Google. C'est simple et
   ça se met à jour à la main.
2. **L'API Google Places**, pour afficher la note et les avis en direct.
   C'est plus fiable dans la durée, mais il faut un compte Google Cloud
   **au nom de l'hôtel** 🏨 et c'est payant au-delà du quota gratuit.

Dans les deux cas, il faut faire **demander l'avis après le séjour** (§ 26) :
c'est ce qui alimente la section.

### 16. Galerie photo & vidéo 🟡

La galerie existe, avec six catégories : domaine, table, lagune, art,
chambres, bien-être.

Manquent :

- des catégories **Séminaires**, **Événements** et **Assinie**, avec leurs
  photos 🏨 ;
- les **vidéos verticales**, tournages 🏨.

### 17–18. Mobile et vitesse ✅

- Images en WebP et AVIF, déclinées en plusieurs tailles.
- Chargement différé.
- Hébergement Vercel avec CDN.
- Audit iPhone effectué.

### 19. SEO 🟡

Déjà en place :

- titre et méta-description par page ;
- adresses propres ;
- un seul H1 ;
- données structurées (Hotel, chambres, restaurant…) ;
- sitemap ;
- images optimisées ;
- liens internes.

Manquent :

- Les **pages qui portent les recherches** du cahier :
  - « hôtel séminaire Assinie » : la page existe, son titre est à travailler ;
  - « mariage Assinie » : il faut la page Événements ;
  - « que faire à Assinie » : il faut la page guide ;
  - « restaurant Assinie » : la page existe.
- **La Search Console**, au nom de l'hôtel 🏨.
- **Rien n'est indexé tant que le site est en démonstration**. Il passera en
  production avec les trois réglages déjà prévus (voir le README, « Mise en
  ligne »). C'est volontaire, pas un oubli.

### 20. Français + anglais ✅

La version anglaise est écrite à la main, avec un dictionnaire par page. Ce
n'est pas une traduction automatique.

Conseil : faire relire l'anglais par une personne anglophone avant la mise
en ligne 🏨. Chaque nouvelle page devra avoir sa traduction.

### 21–22. Capture de prospects et pop-up ❌

- **Inscription aux offres privées** : prénom + WhatsApp ou e-mail, avec une
  case de consentement explicite. La loi ivoirienne 2013-450 sur les données
  personnelles l'impose, et les mentions légales doivent le dire. Les
  contacts sont enregistrés dans la base et exportables depuis
  l'administration. Elle s'affiche dans le pied de page de toutes les pages
  et au bas des pages Offres.
- **Le pop-up** : un seul, avec le texte du cahier (« Votre prochain
  week-end à Assinie commence ici ») et deux boutons. Il apparaît après
  30 secondes ou au deuxième écran parcouru, **une fois par visiteur**. Il
  n'apparaît jamais sur Réserver ni dans un formulaire, et jamais sur
  mobile avant que le visiteur ait fait défiler la page.

### 23–24. Tracking et indicateurs ❌

Rien n'est mesuré aujourd'hui. À installer :

- **Google Analytics 4** et **Google Search Console**, sur des comptes
  **créés au nom de l'hôtel** 🏨.
- **Des événements nommés** sur chaque conversion :
  - clic WhatsApp ;
  - clic téléphone ;
  - début de réservation ;
  - réservation envoyée ;
  - acompte payé ;
  - devis séminaire envoyé ;
  - devis événement envoyé ;
  - table demandée ;
  - spa demandé ;
  - inscription aux offres.
- **Les UTM** sur les liens publicitaires (Instagram, Facebook). Le site les
  garde dans la session et les joint à chaque demande. On sait alors quelle
  campagne a produit quel devis.
- **Un bandeau de consentement aux cookies**, puisque GA4 dépose des
  cookies. Alternative sans cookie et sans bandeau : Vercel Web Analytics
  ou Plausible. C'est moins détaillé sur les campagnes, mais conforme d'office.
- **La CSP** (en-têtes de sécurité) doit autoriser les domaines de
  Google. C'est un réglage dans `vercel.json` et `_csp.py`.

Les indicateurs du § 24 viennent ensuite **du CRM** (§ 25) plus que
d'Analytics :

- demandes reçues ;
- réservations confirmées ;
- CA des acomptes encaissés, déjà connu grâce à lomi ;
- CA des séminaires et des événements, saisi quand le commercial passe une
  demande à « gagnée ».

Un tableau de bord mensuel dans l'administration suffit.

### 25–26. CRM et relances ❌ — le plus gros manque fonctionnel

Aujourd'hui, une demande produit **un e-mail à la réception, et c'est
tout** :

- rien n'est enregistré ;
- le client ne reçoit **même pas d'accusé de réception** ;
- personne ne peut savoir qu'« une personne a demandé un devis il y a 2
  jours et n'a pas eu de réponse ».

Deux voies :

**A. Un module « Demandes » dans l'administration existante**, recommandé.

- Chaque formulaire enregistre la demande dans la base Postgres déjà en
  place, en plus de l'e-mail.
- Un onglet **Demandes** liste les demandes avec :
  - type ;
  - date ;
  - source (UTM) ;
  - statut : nouvelle → répondue → devis envoyé → gagnée / perdue ;
  - commercial en charge ;
  - notes ;
  - montant si gagnée.
- **J0** : un accusé de réception automatique part vers le client, par
  e-mail via Resend, qui est déjà branché.
- **J1, J3, J7** : une tâche planifiée (cron Vercel, une fois par jour)
  envoie les relances par e-mail tant que la demande n'a pas changé de
  statut. La J7 porte une nouvelle proposition.
- L'onglet affiche aussi ce qui **attend une réponse** depuis plus de 24 h.
- Avantages : tout reste chez l'hôtel, sans abonnement, dans un outil que
  l'équipe connaît déjà.

**B. Brancher un CRM du marché** (Brevo, HubSpot gratuit…).

- Les formulaires y poussent les contacts, et les relances se programment
  dans l'outil.
- C'est plus riche pour le marketing.
- Mais il y a un abonnement, une formation à un outil de plus, et les données
  sont chez un tiers. Le compte doit être au nom de l'hôtel 🏨.

**Relances par WhatsApp** : l'automatisation impose l'API WhatsApp Business
de Meta, payante par conversation, et des modèles de messages validés par
Meta. C'est faisable plus tard. Au départ, les relances partent par e-mail,
et le module affiche au commercial un bouton « Relancer sur WhatsApp » avec
le message déjà rédigé.

### 27. Propriété du site 🟡 🏨 — à régler avant la mise en ligne

| Actif | Aujourd'hui | À faire |
|---|---|---|
| Nom de domaine evannathhotel.com | Compte LWS de l'hôtel | ✅ Rien. **Ne jamais toucher aux enregistrements MX / mail.** |
| Hébergement Vercel | **Compte personnel** du développeur | Créer une équipe Vercel au nom de l'hôtel, transférer le projet, garder un accès développeur |
| Code (GitHub) | **Compte personnel** | Créer une organisation GitHub de l'hôtel, transférer le dépôt (le miroir GitLab suit) |
| Base Postgres (Neon) et stockage Blob | Rattachés au compte Vercel | Suivent le transfert du projet ; à vérifier |
| Paiement (lomi), e-mails (Resend) | À ouvrir | Comptes **au nom de l'hôtel** dès le départ |
| Analytics, Search Console | Inexistants | À créer **au nom de l'hôtel** |
| Administration du site | Comptes créés par le développeur | La direction détient le compte propriétaire |
| Photos, vidéos, textes | Fournis par l'hôtel | Livrer une archive complète à la mise en ligne |

### 28. Formation 🟡

L'administration couvre déjà presque toute la liste du cahier :

| Tâche demandée | Où c'est dans l'administration |
|---|---|
| Ajouter une offre | Promotions, Campagnes |
| Modifier les tarifs | Chambres |
| Publier une actualité | Événements |
| Gérer les disponibilités | Disponibilités |
| Publier une offre d'emploi | Offres d'emploi |
| Changer les photos | Galerie |
| Gérer les comptes | Utilisateurs |

Manquent :

- **consulter les statistiques**, qui attend le § 23 ;
- **gérer les demandes**, qui attend le § 25.

À prévoir :

- un **guide illustré** de quelques pages ;
- **une séance de 2 h** avec une ou deux personnes de l'hôtel.

### 29. Maintenance 🟡

Déjà en place côté technique :

- tests automatiques à chaque modification ;
- surveillance du site en ligne chaque nuit, avec alerte ;
- sauvegardes des données : versions conservées dans la base et le
  stockage.

Le reste est **contractuel** 🏨 : qui, combien de temps, délai
d'intervention, coût annuel. À écrire dans le devis.

### 32. Le parcours client idéal

| Étape | État |
|---|---|
| 1–2. Publicité Instagram → page de l'offre | ❌ Les forfaits n'ont pas d'adresse à eux : une publicité « Pack Couple » arrive en haut de la page Offres. Il faut au minimum une ancre par forfait (`/circuits#pack-couple`), les UTM (§ 23) et, à terme, une page d'atterrissage par offre phare. |
| 3–5. Expérience, photos, avis, prix | 🟡 Il manque les avis (§ 15). |
| 6. Réserver ou WhatsApp | ✅ (WhatsApp prérempli à faire, § 6) |
| 7. Réponse rapide du commercial | ❌ Il faut le module Demandes (§ 25). |
| 8. Réservation confirmée | ✅ Acompte en ligne, en mode test. |
| 10. Demande d'avis après le séjour | ❌ E-mail automatique le lendemain du départ, avec lien vers la fiche Google. Se greffe sur le § 25. |
| 11–12. Fidélité, nouvelle expérience | ❌ Il faut la base de contacts (§ 21) et des envois d'offres. Un vrai programme de fidélité est un projet à part. |

---

## Ordre proposé

Du plus rentable au plus long. Chaque lot fait l'objet d'une PR séparée.

| Lot | Contenu | Dépend de l'hôtel ? |
|---|---|---|
| **1. Vendre mieux, tout de suite** | WhatsApp prérempli et boutons dédiés · boutons WhatsApp et Devis sur l'accueil · une adresse par forfait · champs *chambres* et *type d'événement* au devis · accusé de réception automatique au client | Non |
| **2. Mesurer** | GA4 ou Vercel Analytics · événements de conversion · UTM conservés et joints aux demandes · bandeau cookies si GA4 | Comptes Google au nom de l'hôtel |
| **3. Garder les prospects** | Onglet **Demandes** (statuts, notes, montants) · relances J1, J3, J7 · demande d'avis après le séjour · inscription aux offres privées · tableau de bord mensuel | Non (textes des relances à valider) |
| **4. Pages manquantes** | Événements privés · Que faire à Assinie · avis clients · catégories de galerie · offres séminaire et team building | **Oui** : capacités, prestations, photos, avis |
| **5. Contenus longs** | Le Carnet d'Assinie · vidéos courtes · superficies · pop-up | **Oui** : rédaction et tournages |
| **Avant la mise en ligne** | Transfert Vercel, GitHub et base au nom de l'hôtel · clé lomi réelle · liste des chambres · mentions légales · Search Console | **Oui** |

Ce qu'il faut demander à la direction dès maintenant, pour ne pas bloquer
les lots 4 et 5 :

1. **La liste des chambres physiques**, déjà demandée.
2. **Les espaces pour les événements** et leurs capacités, avec les
   prestations proposées (traiteur, décoration, sonorisation…).
3. **Les superficies des sept catégories.**
4. **Brunch, sunset** : existent-ils, à quel prix, quel jour ?
5. **Des photos de séminaires et d'événements passés.**
6. **L'accès à la fiche Google** de l'hôtel, pour les avis.
7. **Qui écrira le carnet**, et à quel rythme.
8. **Les adresses e-mail** au nom de l'hôtel pour créer les comptes Google,
   Vercel et GitHub.
