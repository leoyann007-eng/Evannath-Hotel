# Ce qu'il reste à améliorer

État au 2 octobre 2026, après les corrections du jour (première version le 4 septembre). Classé par compartiment, et dans chacun par ordre
de ce que ça coûte de ne pas le faire.

Trois niveaux :

- **Avant la signature** — rien. Le site tient, et toucher à quoi que ce soit
  à trois jours d'un rendez-vous se paie plus cher que le défaut.
- **Les deux semaines qui suivent** — ce qui protège les données et l'accès.
- **Le trimestre** — ce qui rend le travail confortable et défendable.

---

## Sécurité

> **Le 23 septembre 2026, ce compartiment a changé de statut.** Tant que
> l'administration ne publiait que des affiches, un mot de passe partagé
> suffisait. Elle gouverne maintenant **les chambres qu'on annonce libres**,
> et le paiement en ligne est codé. Les quatre premières lignes de la version
> du 4 septembre sont faites. Le stockage transactionnel et privé est codé le
> 2 octobre : **il ne reste qu'à brancher la base** dans Vercel.

| | Quand | Pourquoi |
|---|---|---|
| **Brancher la base Postgres** | Avant une clé lomi réelle | Le code est prêt (écriture conditionnelle, base privée, passage automatique depuis Blob) ; tant que `DATABASE_URL` manque, le site reste sur Blob — public, et deux enregistrements simultanés peuvent encore s'écraser. Une clé lomi réelle est ignorée d'ici là. Voir « Le stockage » dans le README. |
| **L'offre Vercel et `ADMIN_SECRET`** | Avant la mise en ligne | Hobby est réservé à un usage non commercial ; `ADMIN_SECRET` signe les sessions. Voir « Avant la mise en ligne » dans le README. |
| **La limite de dépense Anthropic** | Avant la mise en ligne | Le site plafonne le concierge (`CHAT_MAX_JOUR`, 200 messages par jour) ; la limite de la console reste le dernier rempart. Le choix du modèle (Opus 5.5 aujourd'hui) se mesure sur de vraies questions. |
| **`@vercel/blob` en 1.x et au-delà** | À la mise à jour | La valeur par défaut d'`addRandomSuffix` change : passer `addRandomSuffix: true` explicitement avant toute montée de version. |
| **Les images acceptées viennent de n'importe quel magasin Blob** | Trimestre | `imageSure()` et la CSP acceptent `*.public.blob.vercel-storage.com`, pas seulement le nôtre. Seul un compte connecté peut en poser une. |
| **`/admin` servi en `public, max-age=0`** | Trimestre | La règle `no-store` de `vercel.json` perd contre celle des `.html`. Sans conséquence : la page ne contient aucun secret, l'API est en `no-store`, et `must-revalidate` force une revalidation. |
| **Le contenu des dépôts n'est pas validé** | Trimestre | On vérifie le type annoncé, pas les octets. Seul un compte connecté peut déposer. |

## Données

| | Quand | Pourquoi |
|---|---|---|
| **Sauvegardes** | ✅ fait | Les dix dernières versions sont conservées. |
| **Pas de bouton de restauration** | 2 semaines | Les dix versions existent, mais y revenir demande une intervention manuelle. La proposition promet « restauration sous 24 h » : c'est tenable, mais ça doit devenir un clic. |
| **Aucune sauvegarde hors du magasin** | Trimestre | Les dix versions vivent au même endroit. Si le magasin Vercel disparaît, tout part avec. Une copie quotidienne ailleurs coûterait quelques lignes. |
| **Les images orphelines s'accumulent** | Trimestre | Supprimer un événement laisse son affiche dans le magasin. Sans conséquence aujourd'hui — 778 Ko — mais ça grossit. |

## Le back-office

| | Quand | Pourquoi |
|---|---|---|
| **Aucun avertissement sur une remise inapplicable** | Trimestre | Une remise de 300 000 F ne s'applique nulle part, et rien ne le dit à la saisie : on voit seulement que rien ne bouge sur le site. |
| **Deux promotions actives : la première gagne, sans le dire** | Trimestre | Comportement jamais décidé, jamais expliqué. À trancher : interdire, ou afficher laquelle s'applique. |
| **La restriction par jour de semaine n'existe pas** | Trimestre | Une promotion « du vendredi au dimanche » s'applique tous les jours de sa période. Aujourd'hui le texte peut donc promettre ce que le mécanisme ne fait pas. |
| **Le bouton de fermeture du menu fait 34 × 49 px** | Trimestre | La recommandation est 44 × 44. Étroit pour un pouce, sans plus. |

## Le site public

| | Quand | Pourquoi |
|---|---|---|
| **Débordement de 32 px sous 320 px de large** | Trimestre | Vient du carrousel de l'accueil, pas du contenu. Masqué par `overflow-x:hidden`, donc invisible. 320 px, c'est un iPhone 5. |
| **L'animation d'apparition est morte sur la carte et le spa** | Trimestre | Ces deux pages ont tout le nécessaire sauf la ligne qui l'active. Rien n'est invisible — la panne va dans le bon sens. Activer sans vérifier chaque bloc risquerait une page blanche. |
| **Le châssis est recopié dans chaque page** | Trimestre | Environ 80 Ko de CSS et de JS en ligne par page, jamais mis en cache d'une page à l'autre. Les sortir en fichiers versionnés (`versionner()` existe) allège chaque navigation et simplifie la CSP. |
| **L'accueil appelle `a=public` deux fois** | Trimestre | `build-index.py` et `REMISE_JS` font chacun leur appel ; chaque appel relit tout le magasin. Une seule promesse partagée suffit. |
| **Aucune restriction de remise sur les services** | Trimestre | Le formulaire permet de cibler le spa ou la table ; le site n'applique la remise qu'aux chambres. Le ciblage est donc sans effet. |

## Ce qui n'existe pas encore

| | Quand | Pourquoi |
|---|---|---|
| **Paiement en ligne** | Selon le contrat | CinetPay ou GeniusPay. C'est la seule question qui fait varier le chiffrage. |
| **Disponibilité** | Formule Signature | ✅ Fait le 23 septembre. La réception saisit ses chambres une à une, les met hors service ou ferme des nuits ; le site compte ce qui reste et va jusqu'à « dernière chambre ». Ce qui manque : le **verrou** empêchant deux clients de prendre la même nuit à la seconde près — il n'a de sens qu'avec une réservation ferme, donc avec le paiement en ligne et un logiciel de gestion. |
| **Synchronisation Booking / Airbnb** | Formule Performance | C'est ce qui apporterait la disponibilité à la seconde, et la seule chose qui l'apporte vraiment. |
| **Surveillance automatique** | Trimestre | Un test qui tourne chaque nuit et prévient si le site ne répond plus ou si les données ne se lisent pas. `tests/en-ligne.test.mjs` fait déjà le travail : il ne manque que la planification. |

## Le domaine

| | Quand | Pourquoi |
|---|---|---|
| **Les accès LWS** | Avant la mise en ligne | DNS, site, courrier et enregistrement du domaine sont tous chez LWS : un seul compte à récupérer. Vérifié au registre le 8 septembre 2026 — le domaine est `active` et court jusqu'au **21 avril 2027**. Rien d'urgent, donc : perdre un mot de passe n'est pas perdre le domaine. |
| **Le renouvellement tombe le 21 avril** | Chaque année | À porter au calendrier. C'est une des choses dont un prestataire se souvient à la place de son client. |
| **Ne jamais toucher aux `MX` ni à `mail.`** | À la bascule | La messagerie @evannathhotel.com vit dessus, et Brevo est déclaré dans le SPF. Une bascule trop rapide coupe le courrier de l'hôtel. |
| **Une modification à la fois** | À la bascule | Transfert de domaine, changement de DNS et mise en ligne la même semaine : on ne saurait pas laquelle a cassé quoi. |

## L'outillage

| | Quand | Pourquoi |
|---|---|---|
| **Aucune intégration continue** | 2 semaines | Les tests et `verifier.py` ne tournent qu'à la main. Une action GitHub à chaque push, et `en-ligne.test.mjs` chaque nuit — c'est aussi la « surveillance automatique » plus haut. |
| **La mise en ligne tient à six interrupteurs dispersés** | Avant la mise en ligne | `PROSPECTION`, `SITE`, `WA_EN_TEST`, `ENVOI_WHATSAPP` dans `_chrome.py`, `SITE_URL` et les clés chez Vercel. Un `verifier.py --production` qui refuse s'il en reste un en position de test. |
| **Le dépôt pèse 106 Mo** | Trimestre | Dont 43 Mo de vidéos ; chaque ré-encodage s'ajoute à l'historique pour toujours. Git LFS, ou les vidéos hors du dépôt. |
| **Trois fichiers trop gros pour être relus** | Trimestre | `api/admin.js` (2 000 lignes, une seule fonction), `admin/index.html` (130 Ko), `_chrome.py` (2 100 lignes de CSS et JS dans des chaînes Python). |

---

## Ce qui est déjà réglé

Pour ne pas y revenir : le stockage transactionnel et privé (2 octobre,
`tests/magasin.test.mjs`, `tests/migration.test.mjs` — à brancher), un acompte
payé qui fait foi face à un formulaire périmé, le plafond quotidien du
concierge (`tests/quota.test.mjs`), la langue qui suit le visiteur d'une page à
l'autre, la traduction anglaise complétée (page Chambres, cartes de La table et
du Spa, légendes de la galerie), les mentions légales remises au réel (cookies et prestataires), le
générateur de la galerie qui ne la vide plus sans les originaux, les comptes nominatifs à quatre profils, la limite
des tentatives de connexion, la clé de session dédiée (`ADMIN_SECRET`), le
journal d'activité, la politique de sécurité du contenu (CSP par empreintes),
le plafond des retenues sans paiement, le réordonnancement qui ne supprime
plus les entrées absentes de la liste (2 octobre, `tests/ordonner.test.mjs`),
le prix barré sur les cinq surfaces, la remise
appliquée jusqu'au message reçu par la réception, la colonne qui s'additionne,
les sauvegardes, l'écriture qui refuse plutôt que d'abîmer, l'avertissement de
page périmée qui ne se déclenche plus à tort, l'en-tête opaque menu ouvert,
l'adresse de l'hôtel affichée partout, les visuels allégés de 62 %, et
l'absence totale de débordement latéral sur les 17 pages testées.
