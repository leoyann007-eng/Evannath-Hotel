# Les tests qu'aucun script ne fait à votre place

Deux suites tournent toutes seules :

```bash
node tests/dispo.test.mjs         # le décompte et la règle des nuits
node tests/remise.test.mjs        # la logique de remise, hors réseau
node tests/en-ligne.test.mjs      # le site déployé, sans navigateur
node tests/envoyer.test.mjs       # l'envoi des formulaires
node tests/comptes.test.mjs       # comptes, profils et sessions, hors réseau
python site/verifier.py           # les 15 contrôles sur les pages générées
```

Ce fichier liste ce qui reste, et que seul un humain peut faire : ce qui passe
par le **formulaire du back-office**, par un **vrai navigateur**, ou par un
**vrai téléphone**.

Cochez au fur et à mesure. Ce qui échoue se note avec la capture d'écran.

---

## 0. Les disponibilités

Le mécanisme est testé de bout en bout par `tests/dispo.test.mjs`. Ce qui
reste ici, c'est **ce qu'une personne comprend** en ouvrant l'écran.

- [ ] **Saisir deux chambres** d'une même catégorie, puis ouvrir sa fiche :
      la pastille passe au vert et dit « Disponible à ces dates ».
- [ ] **Fermer une des deux** sur ces nuits : la pastille passe au bronze et
      dit « Dernière chambre à ces dates ».
- [ ] **Fermer la seconde** : elle passe au rouge, « Complet à ces dates ».
- [ ] **La veille de ces nuits reste verte.** C'est le cas limite qui se
      trompe le plus souvent.
- [ ] **Retirer les deux chambres** : la pastille redevient grise et dit
      « Disponibilité confirmée sous 24 h ». Rien n'est cassé — c'est l'état
      de départ.
- [ ] **Hors service** : décocher « En service » retire la chambre du
      décompte à **toutes** les dates, pas seulement aux prochaines.
- [ ] **Ni le motif, ni les numéros de chambre, ni le nombre restant** ne
      s'affichent sur le site public. Écrivez un mot reconnaissable dans un
      motif et cherchez-le dans la page.
- [ ] **Le récapitulatif en haut** donne, pour chaque catégorie, la liste de
      ses numéros. Saisissez une chambre « 2 » et une « 10 » : elles doivent
      sortir dans cet ordre, pas 10 avant 2.
- [ ] **Sur un vrai téléphone** : la case « En service » passe sous le nom de
      la chambre, le récapitulatif passe les numéros sous le nom de la
      catégorie, et rien ne déborde.
- [ ] **Faire saisir dix chambres par quelqu'un de la réception, sans
      l'aider.** S'il ne sait pas dire ce que le client verra, l'écran est
      raté — c'est ce qu'il explique en premier. Et si saisir dix chambres
      est pénible, la liste ne sera jamais tenue à jour.
- [ ] **Un « complet » n'empêche pas d'envoyer la demande** : le tunnel le
      dit et laisse continuer. La réception a des annulations.

## 1. Le back-office produit-il les bonnes données ?

C'est le trou que les scripts ne comblent pas : ils vérifient ce que le site
fait d'une donnée, jamais que le formulaire sache la fabriquer.

- [ ] **Créer un événement** avec une affiche déposée depuis l'ordinateur.
      L'affiche apparaît entière sur `/circuits`, sans recadrage.
- [ ] **Un événement daté d'hier** disparaît du site sans qu'on y touche.
- [ ] **Un brouillon** (« Visible » décoché) n'apparaît nulle part, même en
      connaissant l'adresse de la page.
- [ ] **Une promotion en pourcentage** sur toutes les chambres.
- [ ] **Une promotion en montant fixe** — le badge doit dire `−15 000 F`,
      jamais `−15 %`.
- [ ] **Une promotion ciblée sur une seule chambre** — les six autres restent
      au tarif plein sur les cinq surfaces.
- [ ] **Une promotion programmée** (début dans le futur) reste invisible, et
      son contenu n'est lisible par personne d'ici là.
- [ ] **Une campagne** avec quatre packs, photos déposées depuis l'ordinateur.
- [ ] **Retirer un pack** d'une campagne, puis republier : il disparaît du
      site et les trois autres restent.
- [ ] **Les flèches d'ordre** changent l'ordre d'affichage sur le site.

## 2. L'argent

Une erreur ici ne se rattrape pas par un correctif : elle se rattrape par un
appel au client.

- [ ] Réserver de bout en bout, **lire le message dans WhatsApp** — pas sur le
      site. Les retours à la ligne tiennent, la colonne reste lisible.
- [ ] Vérifier à la main les trois égalités :
      - Tarif − Remise + Taxe = **Total**
      - Acompte = **30 % du total**
      - Acompte + Solde = **Total**
- [ ] **Une seule nuit** (arrivée et départ consécutifs) : le calcul tient.
- [ ] Le **prix de la fiche** et celui du **tunnel** sont identiques pour la
      même chambre.
- [ ] Changer de chambre dans le menu déroulant : le récapitulatif suit.

## 3. Le stockage

- [ ] Après une publication, **Paramètres → Sauvegardes** a augmenté d'un.
- [ ] Le compteur plafonne à **10** et n'augmente plus au-delà.
- [ ] Aucun **bandeau rouge** dans l'administration.

## 4. Le navigateur

- [ ] **Menu ouvert puis défilé** : le logo ne se mélange à aucun lien.
      À faire sur l'accueil, la carte et le spa — ces trois pages ont leur
      propre en-tête.
- [ ] **Bascule FR → EN** avec une promotion active : le menu des catégories
      passe à « instead of ».
- [ ] **Rechargement forcé** (`Ctrl+Shift+R`) : aucune ancienne version ne
      s'affiche même brièvement.
- [ ] La **visionneuse de la galerie** ouvre, défile, se ferme.

## 5. Le téléphone

Sur un vrai appareil, en 4G, **hors wifi**.

- [ ] La page **Offres & Événements** — les packs, leurs photos, leurs prix.
- [ ] La page **Chambres** — les cartes, le comparateur qui défile latéralement.
- [ ] Une **réservation complète** au pouce.
- [ ] **Aucune page ne glisse latéralement** quand on fait défiler.
- [ ] Le bouton WhatsApp flottant ne recouvre rien d'important.

## 6. Avant un rendez-vous

- [ ] `node tests/en-ligne.test.mjs` — tout au vert.
- [ ] La case **« Mettre en avant »** est dans l'état voulu.
- [ ] Le site ne montre **que ce qui est d'actualité**.
- [ ] Connexion à `/admin` faite **avant** le partage d'écran.
