# Ce qu'il reste à améliorer

État au 4 septembre 2026. Classé par compartiment, et dans chacun par ordre
de ce que ça coûte de ne pas le faire.

Trois niveaux :

- **Avant la signature** — rien. Le site tient, et toucher à quoi que ce soit
  à trois jours d'un rendez-vous se paie plus cher que le défaut.
- **Les deux semaines qui suivent** — ce qui protège les données et l'accès.
- **Le trimestre** — ce qui rend le travail confortable et défendable.

---

## Sécurité

| | Quand | Pourquoi |
|---|---|---|
| **`ADMIN_SECRET` non défini** | 2 semaines | La clé qui signe les sessions retombe alors sur le mot de passe lui-même. Une longue chaîne aléatoire chez Vercel, deux minutes. |
| **Aucune limite sur les tentatives de connexion** | 2 semaines | On peut essayer des mots de passe aussi vite que le réseau le permet. En serverless la protection ne peut être que partielle — compteur par instance et délai sur chaque échec — mais partielle vaut mieux qu'absente. |
| **Un seul mot de passe partagé** | 2 semaines | Impossible de savoir qui a publié quoi, ni de couper l'accès d'une personne qui part. Un compte par personne. |
| **Aucun journal des publications** | 2 semaines | « Qui a supprimé l'affiche ? » doit avoir une réponse. Trois champs suffisent : qui, quoi, quand. |
| **Pas de politique de sécurité du contenu (CSP)** | Trimestre | Les pages utilisent des scripts en ligne : une CSP stricte demande de les sortir. Le gain est réel mais le travail n'est pas mince. |
| **`/admin` servi en `public, max-age=0`** | Trimestre | La règle `no-store` de `vercel.json` perd contre celle des `.html`, quel que soit leur ordre — précédence que je n'explique pas. Sans conséquence : la page ne contient aucun secret, l'API est bien en `no-store`, et `must-revalidate` force une revalidation à chaque appel. |
| **Le contenu des dépôts n'est pas validé** | Trimestre | On vérifie le type annoncé, pas les octets. Risque faible : seul un administrateur connecté peut déposer. |

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
| **Aucune restriction de remise sur les services** | Trimestre | Le formulaire permet de cibler le spa ou la table ; le site n'applique la remise qu'aux chambres. Le ciblage est donc sans effet. |

## Ce qui n'existe pas encore

| | Quand | Pourquoi |
|---|---|---|
| **Paiement en ligne** | Selon le contrat | CinetPay ou GeniusPay. C'est la seule question qui fait varier le chiffrage. |
| **Disponibilité en temps réel** | Formule Signature | Aujourd'hui toute demande affiche « Disponible à ces dates ». C'est une promesse que rien ne vérifie. |
| **Synchronisation Booking / Airbnb** | Formule Performance | — |
| **Surveillance automatique** | Trimestre | Un test qui tourne chaque nuit et prévient si le site ne répond plus ou si les données ne se lisent pas. `tests/en-ligne.test.mjs` fait déjà le travail : il ne manque que la planification. |

## Le domaine

| | Quand | Pourquoi |
|---|---|---|
| **Les accès LWS** | Avant la mise en ligne | DNS, site et courrier sont chez LWS. Un `whois evannathhotel.com` donne la date d'expiration — c'est le seul point réellement urgent, un domaine expiré se perd. |
| **Ne jamais toucher aux `MX` ni à `mail.`** | À la bascule | La messagerie @evannathhotel.com vit dessus, et Brevo est déclaré dans le SPF. Une bascule trop rapide coupe le courrier de l'hôtel. |
| **Une modification à la fois** | À la bascule | Transfert de domaine, changement de DNS et mise en ligne la même semaine : on ne saurait pas laquelle a cassé quoi. |

---

## Ce qui est déjà réglé

Pour ne pas y revenir : le prix barré sur les cinq surfaces, la remise
appliquée jusqu'au message reçu par la réception, la colonne qui s'additionne,
les sauvegardes, l'écriture qui refuse plutôt que d'abîmer, l'avertissement de
page périmée qui ne se déclenche plus à tort, l'en-tête opaque menu ouvert,
l'adresse de l'hôtel affichée partout, les visuels allégés de 62 %, et
l'absence totale de débordement latéral sur les 17 pages testées.
