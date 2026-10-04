# Notre compréhension de la réservation

**Document interne.** Écrit le 24 septembre 2026, **avant** le cahier des
charges que la direction s'est engagée à nous transmettre.

Il ne s'adresse pas au client. Il sert à trois choses :

1. **Fixer ce que nous croyons avoir compris**, en nos termes, pendant que
   c'est frais. Une compréhension qu'on ne met pas par écrit se déforme.
2. **Servir de point de comparaison** quand le cahier des charges arrivera.
   Chaque écart entre ce document et le sien est une question à poser — et
   les écarts sont plus faciles à voir qu'à deviner.
3. **Tenir la liste des questions** qui découlent de cette compréhension, pour
   ne pas les redécouvrir une par une en cours de route.

---

## Le point qui change tout

> **Normalement, lorsqu'une réservation est faite avec acompte, la réservation
> est confirmée directement et la chambre passe en réservée.**

C'est la règle normale de l'hôtellerie, et c'est ce qui manquait à notre
modèle. Aujourd'hui le site ne sait faire qu'une **demande** : le client
remplit, la chambre est gardée deux heures, et **un humain confirme**. Ce
n'est pas une réservation, c'est une intention.

Avec l'acompte, ce n'est plus vrai. **C'est le paiement qui confirme.** Aucune
intervention humaine n'est requise pour que la chambre soit prise — la
réception l'apprend, elle ne la décide pas.

Ce n'est pas un ajout au mécanisme existant. C'est un **second régime**, et
les deux devront coexister.

---

## Les deux régimes

### Régime A — sans paiement en ligne (ce qui existe aujourd'hui)

| | |
|---|---|
| Le client fait | une **demande** de réservation |
| La chambre passe en | retenue, **2 heures** |
| Qui confirme | la réception, à la main |
| Quand part l'e-mail | à la confirmation |
| Si personne ne répond | la retenue tombe, la chambre repart à la vente |
| L'acompte | réglé hors ligne, par un lien que la réception envoie |

C'est un pis-aller assumé : sans encaissement, on ne peut pas transformer un
formulaire en engagement.

### Régime B — avec acompte payé en ligne (ce qu'elle décrit)

| | |
|---|---|
| Le client fait | une **réservation**, et il paie |
| La chambre passe en | **réservée**, fermement |
| Qui confirme | **personne — le paiement confirme** |
| Quand part l'e-mail | dès que l'encaissement est confirmé |
| Si personne ne répond | sans objet : il n'y a rien à répondre |
| L'acompte | encaissé pendant le parcours |

Notre vocabulaire interne colle déjà : une chambre dont le séjour commence
plus tard est **Réservée**, elle devient **Occupée** le jour de l'arrivée.
Ces deux états existent dans le calendrier.

---

## Ce que le régime B impose, et que nous n'avons pas

### 1. Un verrou, qui devient obligatoire

C'était écrit dans `exigences-reunion.md` : *« le verrou empêchant deux
clients de prendre la même nuit à la seconde près n'a de sens qu'avec une
réservation ferme — donc avec le paiement en ligne. »*

Nous y sommes. **Dès que le paiement confirme tout seul, il n'y a plus de
réception pour rattraper une collision.** Deux clients qui paient au même
instant pour la dernière chambre créent un double engagement — et cette fois
l'argent est encaissé des deux côtés.

Ce n'est plus une amélioration, c'est un préalable.

> **État au 2 octobre 2026 : le verrou est codé.** Avec une base Postgres
> branchée (`DATABASE_URL`), toute modification n'est écrite que si personne
> n'a écrit depuis sa lecture — choisir la chambre et la retenir se font d'un
> seul geste. Sans la base, le code ignore une clé lomi réelle : le paiement
> en ligne ne peut pas s'activer sur un stockage qui ne tient pas ce verrou.
> Voir « Le stockage » dans le README.

### 2. Une retenue courte, pendant le paiement

Deux heures n'ont plus de sens. Le client ne demande plus, il paie : la
chambre doit être bloquée **le temps du parcours de paiement**, pas le temps
d'une prise de poste. Quelques minutes, et la retenue tombe si le paiement
n'aboutit pas.

Les deux durées coexisteront donc : une longue pour le régime A, une courte
pour le régime B.

### 3. Trois chemins de sortie, pas un

Aujourd'hui une demande finit confirmée ou expirée. Un paiement peut finir :

- **payé** — la chambre est réservée, l'e-mail part ;
- **échoué ou abandonné** — la chambre repart immédiatement à la vente ;
- **payé mais la chambre n'est plus disponible** — le cas qu'il faut rendre
  impossible, et à défaut, traiter explicitement. On a encaissé, il faut
  rembourser, et prévenir un client qui croyait avoir réservé.

Le troisième est le seul qui compte vraiment, parce que c'est celui qui
abîme la réputation de l'hôtel.

### 4. L'ordre reste le même

**On n'encaisse pas pour une chambre dont on n'a pas vérifié qu'elle est
libre.** La disponibilité vient avant le paiement. Ce n'est pas un ordre de
confort, c'en est un de risque — et il est renforcé, pas affaibli, par la
confirmation automatique.

---

## Ce qui ne bouge pas

Ces trois choses sont construites, testées, et ne dépendent d'aucun régime :

- **La règle des nuits.** Un séjour du 24 au 26 occupe les nuits du 24 et du
  25. Une seule fonction, 98 vérifications automatiques.
- **Le raisonnement par chambre physique**, pas par catégorie. C'est la
  correction que la direction avait demandée, et elle vaut pour les deux
  régimes.
- **La dégradation vers `inconnu`.** Tout ce qui échoue ne promet rien. Rien
  ne retombe jamais sur « disponible ».

---

## Les questions que ça ouvre

À poser maintenant, sans attendre le cahier des charges — et à confronter
avec lui quand il arrivera.

### Sur le paiement et la confirmation

1. **Acompte de 30 % ou paiement intégral ?** Le site affiche 30 % — un
   chiffre que nous avons écrit, que l'hôtel n'a jamais validé.
2. **L'acompte confirme-t-il seul, ou la réception valide-t-elle quand même ?**
   Elle a dit « confirmée direct ». À confirmer tel quel : c'est la différence
   entre un système autonome et un système surveillé.
3. **Le régime A survit-il ?** Un client qui ne veut pas payer en ligne, un
   groupe, un séminaire — peuvent-ils encore faire une simple demande ?
4. **Combien de temps garde-t-on la chambre pendant que le client paie ?**

### Sur ce qui peut mal tourner

5. **Un paiement encaissé pour une chambre qui n'est plus libre : qui
   rembourse, sous quel délai, et qui prévient le client ?**
6. **Quelles sont les vraies conditions d'annulation ?** Le site annonce
   « gratuite jusqu'à 48 h avant, acompte remboursé ». **Valeur inventée.**
   Dès qu'on encaisse, elle devient un engagement juridique.
7. **Un reçu, une facture ?** À produire automatiquement, ou non.

### Sur la source des disponibilités

8. **Quel est l'outil hôtelier des réceptionnistes ?** Question déjà posée.
   Elle devient plus lourde avec le paiement : si le site confirme tout seul,
   il doit lire une disponibilité **juste**, pas une copie tenue à la main.
9. **Les réservations prises par téléphone, ou venues de Booking, sont-elles
   saisies dans cet outil ?** Si oui, et si nous le lisons, le problème est
   résolu. Si non, le site vendra des chambres déjà prises.

### Sur ce que nous avons écrit sans source

10. **Le délai « sous 24 h ».** Il vient de nous, pas d'eux. Il s'affiche
    38 fois sur 14 pages — et sur les sept fiches chambres dès qu'aucune
    chambre n'est saisie. À valider ou à retirer.
11. **Les conditions générales** — arrivée, départ, taxe de séjour, animaux.
    Toutes inventées. Voir `README.md`, section « À valider ».

---

## Ce qu'on attend du cahier des charges

Elle s'est engagée à en produire un. Ce qu'il doit trancher, par ordre
d'importance pour nous :

| | Sans quoi |
|---|---|
| Le régime de confirmation — acompte seul, ou validation humaine | on construit le mauvais système |
| Le montant de l'acompte et les conditions d'annulation | on encaisse sur des règles inventées |
| La source des disponibilités — leur outil, ou notre calendrier | on construit une double saisie qui mourra |
| Qui répond, et en combien de temps | le délai affiché reste une invention |

Les trois premières sont bloquantes. La quatrième peut attendre la mise en
ligne, mais pas davantage.

---

## Ce que ce document n'est pas

Il n'est **pas** un cahier des charges, et il ne doit pas être présenté comme
tel. C'est notre lecture, écrite avant la leur, précisément pour pouvoir dire
« voici ce que nous avions compris » et mesurer l'écart.

Si le cahier des charges les contredit, **c'est lui qui gagne.** Ce document
sert à voir les écarts, pas à les trancher.
