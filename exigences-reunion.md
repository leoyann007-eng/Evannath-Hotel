# Ce que la direction a demandé — réunion du 23 septembre 2026

Trois demandes, notées telles qu'elles ont été formulées :

1. **Un chatbot** qui discute avec le client, puis passe la main à la réception.
2. **Mettre en ligne les chambres disponibles.**
3. **Un système de paiement** pour les réservations en ligne.

Ce document dit, pour chacune, ce qu'elle veut dire techniquement, ce qui est
déjà là, ce qui bloque, et ce que ça change au devis. Il ne décide rien à la
place de l'hôtel.

---

## D'abord : deux de ces trois demandes sont déjà écrites dans la proposition

Ce n'est pas une mauvaise nouvelle, c'est la bonne. La proposition remise
distingue trois formules, et les demandes 2 et 3 sont **exactement** la ligne
de partage entre la première et la deuxième :

| | Essentiel — 1 200 000 F | Signature — socle + devis |
|---|---|---|
| Les 21 pages, l'espace de publication, les 5 formulaires | ✅ | ✅ |
| **Disponibilité en temps réel** | ❌ | ✅ |
| **Acompte réglé en ligne** — Wave, Orange Money, MTN, carte | ❌ | ✅ |

L'Essentiel porte noir sur blanc la mention **« Sans paiement en ligne »**.

**Mme Josiane ne demande donc pas des ajouts : elle demande la formule
Signature.** C'est à écrire clairement dans le devis, sans en faire un
reproche et sans faire semblant que c'était compris d'avance. La proposition
annonçait déjà que « ce qu'il reste à décider tient en une question — le
paiement en ligne ». Elle vient d'y répondre : oui.

**Le chatbot, lui, n'est dans aucune formule.** Il est neuf. Il se chiffre à
part.

---

## 1. Les chambres disponibles

### Ce qu'il y a aujourd'hui, et le seul endroit où le site ment

Le tunnel de réservation est honnête : il annonce que « la réception vérifie
la disponibilité et vous répond sous 24 h », puis que le lien d'acompte suit
une fois la chambre confirmée. C'est une demande de réservation, et elle se
présente comme telle.

**Sauf à un endroit.** Les sept fiches chambres affichent, sous le bouton
« Réserver cette chambre », une pastille verte et la mention :

> ● Disponible à ces dates

Elle s'affiche **quelles que soient les dates choisies**, et rien ne la
vérifie. C'est la seule phrase du site que rien ne soutient. Elle doit
disparaître ou devenir vraie — et la demande de la direction est précisément
de la rendre vraie.

### La vraie question, et elle est pour l'hôtel

Un affichage de disponibilité ne vaut que ce que vaut sa source. **Où vit
aujourd'hui la vérité des chambres libres ?** Un cahier à la réception, un
tableur, un logiciel ? La réponse change tout :

- **Pas de logiciel** — le cas le plus probable. On construit alors un
  calendrier dans l'espace d'administration que l'hôtel possède déjà : la
  réception y ferme les dates prises, catégorie par catégorie. Le site lit ce
  calendrier. Simple, sans abonnement, et vrai **tant que la réception le
  tient à jour** — c'est le prix à dire clairement.
- **Un logiciel de gestion (PMS)** — on se branche dessus, et la question
  devient laquelle, et expose-t-il ses données.

Dans les deux cas le mécanisme côté site est le même ; seule la source change.

### ✅ Construit le 23 septembre

Le mécanisme existe et tourne. Ce qui a été fait :

- les sept fiches chambres, l'accueil et le tunnel lisent désormais un
  verdict du serveur au lieu d'affirmer ;
- un écran **Disponibilités** dans l'administration : la réception coche les
  catégories qu'elle prend en ligne, et ferme les nuits prises ;
- trois états, dont `inconnu`, qui ne promet rien ;
- la règle des nuits, à un seul endroit, avec 39 vérifications automatiques ;
- un quinzième contrôle dans `verifier.py` qui refuse toute disponibilité
  écrite en dur dans une page.

Voir `README.md`, section « Les disponibilités ».

Ce qui **n'est pas** fait, et qui demande un logiciel de gestion : le nombre
de chambres restantes, et le verrou qui empêche deux clients de prendre la
même nuit à la seconde près.

### Ce qui se construit, et ce qui se promet

Ce qu'on peut tenir : **le site ne montre plus comme libre une chambre que la
réception a fermée, et n'annonce « disponible » que là où elle l'a dit.**
Quand elle n'a rien saisi, le site ne prétend rien : il redit qu'on vérifie
sous 24 h.

Ce qu'on ne peut pas tenir sans logiciel de gestion : la disponibilité à la
minute, avec deux clients qui réservent la même chambre en même temps. Ça,
c'est la synchronisation Booking / Airbnb, et c'est la formule Performance.

**À ne pas escamoter :** un calendrier que personne ne remplit est pire que
pas de calendrier. Il transforme un silence honnête en promesse fausse. La
formation de la réception fait partie du travail, pas du service après-vente.

---

## 2. Le paiement en ligne

### Ce qui existe déjà

Le tunnel demande déjà au client **quel moyen de paiement il souhaite** —
Wave, Orange Money, MTN Money, carte bancaire — et calcule l'acompte de 30 %.
Rien n'est encaissé : la demande part par e-mail à la réception, qui envoie le
lien. L'ossature du parcours est donc en place ; il manque l'encaissement.

### Ce qui bloque, et ce n'est pas technique

Encaisser exige un **compte marchand au nom de l'hôtel** chez un agrégateur
ivoirien — CinetPay ou GeniusPay sont les deux candidats sérieux, tous deux
couvrant Wave, Orange Money, MTN, Moov et la carte en un seul branchement.

Ce compte demande, du côté de l'hôtel :

- le registre de commerce et la déclaration fiscale de l'établissement,
- un compte bancaire ou un compte marchand mobile à son nom,
- la signature du contrat de l'agrégateur, qui prélève une commission par
  transaction — **c'est de l'argent de l'hôtel, pas du mien : le contrat se
  signe entre eux et l'agrégateur, jamais par mon intermédiaire.**

**Je ne peux ni ouvrir ce compte, ni le détenir, ni faire transiter leurs
encaissements par un compte à moi.** Je branche la passerelle, je la teste en
mode bac à sable, et le jour où leurs clés arrivent, on bascule.

### Ce qu'il faut décider avec la direction

| Question | Pourquoi elle compte |
|---|---|
| Acompte de 30 %, ou paiement intégral ? | Le site dit 30 % aujourd'hui. |
| Les conditions d'annulation | Le site annonce « gratuite jusqu'à 48 h avant, acompte remboursé ». **C'est une valeur plausible que j'ai écrite, pas une règle de l'hôtel.** Dès qu'on encaisse pour de vrai, elle devient un engagement juridique. |
| Qui rembourse, et sous quel délai ? | Un paiement en ligne crée des remboursements. Il faut savoir qui les fait. |
| Un reçu, une facture ? | À produire automatiquement, ou non. |

### L'ordre compte

**On n'encaisse pas pour une chambre dont on n'a pas vérifié qu'elle est
libre.** Prendre l'argent d'un client puis lui apprendre que la chambre est
prise, c'est le pire des deux mondes : on a encaissé, on doit rembourser, et
on a perdu le client. La disponibilité vient donc avant le paiement — ce n'est
pas un ordre de confort, c'en est un de risque.

---

## 3. Le chatbot

### Ce qu'elle décrit

« Un chatbot qui discutera avec les clients **avant que la réception ne prenne
le relai** ». La formulation est juste : ce n'est pas un robot qui remplace la
réception, c'est un filtre qui absorbe les questions répétitives et passe la
main dès que ça devient une vraie conversation.

### Ce qu'il y a déjà pour le nourrir

Le site contient déjà, écrit et validé, tout ce qu'un client demande vingt
fois par jour : les 7 catégories et leurs prix, les 17 questions de la page
Informations utiles, la carte du restaurant (94 articles), les 22 soins du
spa, l'accès, les horaires, les formules séminaires. **La matière existe.**

### Les deux chemins, et ils ne coûtent pas la même chose

**A. Un assistant guidé, sans intelligence artificielle.** Des questions
proposées, des réponses tirées mot pour mot du site, et un bouton « parler à
la réception » qui bascule sur WhatsApp avec le fil de la conversation. Il ne
se trompe jamais, parce qu'il n'invente rien : il ne sait que ce qui est
écrit. En contrepartie il ne comprend pas une question formulée de travers.
Pas d'abonnement, pas de clé, pas de coût par message.

**B. Un vrai modèle de langue** (Claude ou équivalent), à qui on donne le
contenu du site comme seule source autorisée. Il comprend la question posée
en n'importe quels termes, dans n'importe quelle langue. En contrepartie : un
abonnement au prorata des messages, et surtout **un risque d'invention** qu'on
réduit sans jamais l'annuler. Un robot qui annonce un prix faux ou une chambre
libre engage l'hôtel.

**Ma recommandation : A d'abord, B ensuite si le volume le justifie.** Non par
prudence de principe, mais parce qu'on ne sait pas encore quelles questions
les clients posent vraiment. L'assistant guidé le dira — chaque question
laissée sans réponse est enregistrée. On saura alors si B se justifie, et sur
quoi l'appuyer.

**Dans les deux cas, la règle est la même :** le robot ne confirme jamais une
réservation, n'annonce jamais une disponibilité, ne touche jamais à un
paiement. Il informe, et il passe la main.

### Une question pour la direction

**Qui reprend la conversation, et en combien de temps ?** Un « la réception
vous répond » à 23 h un dimanche ne veut rien dire. Le robot doit annoncer
l'heure à laquelle quelqu'un répondra réellement, sans quoi il fabrique de la
déception au lieu de l'absorber.

---

## L'ordre de construction

1. **Les disponibilités.** Parce que le site affiche aujourd'hui une promesse
   que rien ne vérifie, et parce que le paiement en dépend.
2. **Le chatbot.** Parce qu'il est indépendant des deux autres, qu'il se
   branche sur du contenu déjà écrit, et qu'il soulage la réception tout de
   suite.
3. **Le paiement.** En dernier, parce qu'il dépend du 1 et qu'il est de toute
   façon suspendu au compte marchand de l'hôtel.

---

## Ce que ces trois demandes changent à l'espace d'administration

Aujourd'hui l'administration publie des affiches et des promotions. Un mot de
passe unique, partagé, y suffit : au pire on publie une affiche de travers.

**Demain elle gouvernera les chambres libres et touchera à de l'argent.** Le
même mot de passe ne suffit plus. Ce qui figurait dans `AMELIORATIONS.md`
comme « à faire sous deux semaines » devient **préalable à la mise en ligne** :

- `ADMIN_SECRET` défini pour de bon,
- une limite sur les tentatives de connexion,
- **un compte par personne**, pour savoir qui a fermé quelle chambre,
- un journal des modifications.

Ce n'est pas du zèle. Le jour où une chambre est fermée par erreur un week-end
de pont, la première question sera « qui l'a fait ». Il faut pouvoir y
répondre.

---

## Les questions à lui poser

Courtes, et toutes bloquantes pour le devis :

1. **Où notez-vous aujourd'hui les chambres prises ?** Cahier, tableur,
   logiciel ?
2. **Avez-vous déjà un compte marchand** — CinetPay, GeniusPay, ou un compte
   Wave professionnel ?
3. **Acompte de 30 % ou paiement intégral**, et quelles sont vos vraies
   conditions d'annulation ?
4. **Qui répond aux clients, et à quelles heures ?**
5. **Qui, à l'hôtel, tiendra le calendrier des disponibilités à jour ?**

La cinquième est la plus importante, et c'est celle qu'on oublie de poser.
