# -*- coding: utf-8 -*-
"""Genere circuits.html : Packs Vacances (campagne Facebook) + circuits + Mechoui Party."""
import io
import json as _json
import _chambres
import _schema
from _evenements import EVENEMENTS, EN as EV_EN
NL_ = chr(10)
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV

CSS = """
/* Les intertitres qui separent les quatre parties de la page. */
.sect{margin:86px 0 34px;max-width:70ch}
.sect h2{font-size:clamp(1.9rem,3.4vw,2.6rem);margin:10px 0 12px}
.sect p{color:var(--muted)}

/* L'agenda : un evenement a la fois, photo plein cadre.
   Le carrousel reste dans la largeur du contenu. Un debordement plein ecran
   demanderait 100vw, qui inclut la barre de defilement et decale la page de
   8 px — le defaut est deja documente ailleurs dans ce projet. */
.agenda{position:relative;margin-top:26px;border:1px solid var(--line);overflow:hidden;transition:opacity .25s ease}
.diapos{position:relative}
.diapo{position:absolute;inset:0;opacity:0;visibility:hidden;transition:opacity .7s ease}
.diapo.on{opacity:1;visibility:visible;position:relative}
.diapo>picture img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.diapo .voile{position:absolute;inset:0;background:linear-gradient(100deg,
  rgba(23,16,10,.94) 0%,rgba(23,16,10,.86) 42%,rgba(23,16,10,.42) 100%)}
.diapo .dedans{position:relative;z-index:2;padding:56px 60px;max-width:70ch}

.pastille{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--bronze);
  color:var(--bronze-2);padding:7px 16px;font-size:10.5px;font-weight:700;
  letter-spacing:.2em;text-transform:uppercase}
.diapo .cat{display:block;margin-top:22px;font-size:10.5px;letter-spacing:.3em;
  text-transform:uppercase;color:var(--muted);font-weight:700}
.diapo h3{font-size:clamp(2.1rem,4.4vw,3.2rem);line-height:1.06;margin:10px 0 16px;
  font-weight:400}
.diapo h3 em{font-style:italic;color:var(--bronze-2)}
.diapo p{max-width:52ch;margin-bottom:26px}

/* Les pastilles d'information : ce qu'on veut savoir avant de venir. */
.infos{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:30px}
.infos span{display:flex;flex-direction:column;gap:3px;background:rgba(23,16,10,.72);
  border:1px solid var(--line);padding:11px 16px;min-width:100px}
/* Ce voile est pose sur une PHOTO : il garde sa nuit, quelle que soit la
   couleur de la page. Mais tout ce qu'il contient heritait des jetons
   devenus sombres — « Dès 20 h » tombait a 1,22:1 sur son propre
   fond. Il redeclare donc des jetons clairs pour son interieur :
   une regle, plutot que la chasse a chaque couleur. */
.infos span,.pilote button,.diapo .voile,.c .tag{--cream:#F6EEE2;--prose:#D7CBBA;--muted:#E0D6C8;
  --bronze:#DFBB84;--bronze-2:#E8CDA3;--bark:#17100A;
  color:var(--cream)}

.infos b{font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted);
  font-weight:700}
.infos i{font-style:normal;font-family:var(--f-display);font-size:1.02rem;color:var(--cream)}

/* Une affiche des reseaux se montre ENTIERE. Elle porte deja ses dates, son
   tarif et son telephone : la recadrer en fond reviendrait a couper
   l'information et a ecrire par-dessus. */
.diapo.affiche{display:grid;grid-template-columns:minmax(0,440px) 1fr;align-items:center;
  background:var(--bark-2)}
.diapo.affiche>picture{position:relative;display:block;padding:24px;background:var(--night)}
.diapo.affiche>picture img{position:static;inset:auto;width:100%;height:auto;object-fit:contain}
.diapo.affiche .voile{display:none}
.diapo.affiche .dedans{padding:40px 44px;max-width:none}
@media(max-width:900px){.diapo.affiche{grid-template-columns:1fr}
  .diapo.affiche>picture{padding:16px}}

.pilote{position:absolute;right:26px;bottom:26px;z-index:3;display:flex;align-items:center;
  gap:14px}
.pilote button{width:42px;height:42px;border:1px solid var(--line);background:rgba(23,16,10,.7);
  color:var(--bronze-2);font-size:20px;line-height:1;cursor:pointer;transition:.3s;
  font-family:var(--f-body)}
.pilote button:hover{border-color:var(--bronze);background:var(--bronze);color:var(--bark)}
.cpt{font-size:12px;letter-spacing:.16em;color:var(--muted);display:flex;gap:5px}
.cpt b{color:var(--cream);font-weight:700}
.cpt i{font-style:normal}

@media(max-width:900px){
  .diapos{min-height:0}
  .diapo .dedans{padding:34px 24px 92px}
  .diapo .voile{background:linear-gradient(180deg,rgba(23,16,10,.80),rgba(23,16,10,.95))}
  .infos span{min-width:0;flex:1 1 46%}
  .pilote{right:20px;bottom:20px}
}

.head{padding:150px 0 46px}
.head h1{margin:10px 0 20px}
.head .lede{font-size:1.1rem;max-width:60ch}
.camp{border:1px solid var(--bronze);background:var(--bark-2);padding:34px;margin-bottom:56px}
.camp .top{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;flex-wrap:wrap;margin-bottom:26px}
.camp .live{display:inline-flex;align-items:center;gap:9px;font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--palm);font-weight:700}
.camp .live i{width:7px;height:7px;border-radius:50%;background:var(--palm);display:inline-block;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
.camp h2{margin:12px 0 0}
.camp>p{max-width:62ch}
.packs{align-items:start;display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:26px}
.pack{border:1px solid var(--line);overflow:hidden;background:var(--bark);transition:.45s}

/* Une remise se lit en trois secondes : le montant, sur quoi, jusqu à quand. */
.remises{display:grid;gap:18px;margin-top:26px}
.remises:empty{display:none}
.remise{display:grid;grid-template-columns:minmax(0,260px) 1fr;
  border:1px solid var(--bronze-2);background:var(--bark-2)}
.remise.sans-image{grid-template-columns:1fr}
.remise>picture{display:block;background:var(--night)}
.remise img{width:100%;height:100%;object-fit:cover;display:block}

/* Une affiche est le message, pas l illustration : c est elle qu on lit.
   Elle prend donc la moitie de la carte et se montre entiere, a sa taille.
   Reduite a une vignette de 180 px, elle ne servait a rien. */
.remise.affiche{grid-template-columns:minmax(0,46%) 1fr;align-items:stretch}
.remise.affiche>picture{padding:22px;background:var(--night);
  display:flex;align-items:center;justify-content:center}
.remise.affiche img{width:100%;height:auto;max-height:520px;
  object-fit:contain}
/* Une hauteur minimale avant chargement : sans elle la carte sursaute
   quand l affiche arrive. */
.remise.affiche>picture{min-height:240px}
.remise .dedans{padding:26px 28px}
.remise .haut{display:flex;align-items:center;gap:12px;flex-wrap:wrap;
  margin-bottom:10px}
.remise .taux{display:inline-block;padding:5px 12px;font-size:15px;
  font-weight:700;background:var(--bronze-2);color:var(--bark);
  letter-spacing:.02em}
.remise .jusqua{font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted);font-weight:700}
.remise h3{font-family:var(--f-display);font-size:26px;font-weight:400;
  line-height:1.15;margin:0 0 8px}
.remise p{color:var(--cream);margin:0 0 14px;max-width:62ch}
.remise .sur{font-size:12.5px;color:var(--muted);margin-bottom:16px}


@media (max-width:820px){
  .remise,.remise.affiche{grid-template-columns:1fr}
  .remise>picture{max-height:260px}
  .remise.affiche>picture{max-height:none}
}
.pack:hover{border-color:rgba(185,138,80,.55);transform:translateY(-4px)}
.pack .ph{aspect-ratio:3/2;overflow:hidden}
/* Rien n est rogne : le visuel impose sa hauteur. */
.pack .ph.libre{aspect-ratio:auto;background:var(--night)}
.pack .ph.libre img{height:auto;object-fit:contain}
.pack .ph img{width:100%;height:100%;object-fit:cover;transition:1s cubic-bezier(.2,.8,.2,1)}
.pack:hover .ph img{transform:scale(1.07)}
.pack .in{padding:20px}
.pack h3{font-size:1.12rem;margin-bottom:10px}
.pack b{font-family:var(--f-display);font-size:1.55rem;color:var(--bronze);display:block;line-height:1;font-variant-numeric:tabular-nums;font-weight:400}
.pack span{font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600;display:block;margin-top:5px}
.pack .pick{width:100%;margin-top:16px;text-align:center}
/* L affiche d une campagne : montree entiere, elle porte deja son message. */
.camp-duo{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);
  gap:26px;align-items:center;margin:20px 0 6px}
.camp-duo.seul{grid-template-columns:1fr}
.camp-visuel{border:1px solid var(--line);background:var(--night)}
/* Plafonnee : une affiche carree ou verticale rendait la colonne enorme et
   repoussait les cartes hors de l ecran. */
.camp-visuel{display:flex;align-items:center;justify-content:center}
.camp-visuel img{width:100%;height:auto;max-height:440px;object-fit:contain;
  display:block}
/* Le decoupage en lignes vient de l hotel : on le respecte. */
.camp-texte{white-space:pre-line;margin:0;max-width:52ch}
@media (max-width:860px){ .camp-duo{grid-template-columns:1fr;gap:18px} }
.star{display:grid;grid-template-columns:1.15fr 1fr;border:1px solid var(--line);margin-bottom:64px;background:var(--bark-2)}
.star .ph{position:relative;overflow:hidden;min-height:420px}
.star .ph img{width:100%;height:100%;object-fit:cover}
.star .badge{position:absolute;top:20px;left:20px;background:var(--bronze);color:var(--bark);font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;padding:8px 14px}
.star .txt{padding:48px}
.star h2{margin:12px 0 16px}
.star .incl{list-style:none;margin:24px 0}
.star .incl li{padding:11px 0;border-bottom:1px solid var(--line);font-size:14.5px;color:var(--prose);display:flex;gap:13px}
.star .incl i{color:var(--palm);font-style:normal}
.star .foot{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;flex-wrap:wrap;margin-top:28px}
.star .pr b{font-family:var(--f-display);font-size:2.7rem;color:var(--bronze);display:block;line-height:1;font-variant-numeric:tabular-nums;font-weight:400}
.star .pr span{font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:600}
.filters{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:34px}
.filters button{background:none;border:1px solid var(--line);color:var(--muted);font:700 10.5px/1 var(--f-body);letter-spacing:.16em;text-transform:uppercase;padding:14px 20px;cursor:pointer;transition:.3s}
.filters button.on,.filters button:hover{border-color:var(--bronze);color:var(--bronze)}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.c{background:var(--bark-2);border:1px solid var(--line);display:flex;flex-direction:column;overflow:hidden;transition:.5s cubic-bezier(.2,.8,.2,1)}
.c.hide{display:none}
.c:hover{transform:translateY(-6px);border-color:rgba(185,138,80,.5)}
.c .ph{aspect-ratio:16/10;overflow:hidden;position:relative}
.c .ph img{width:100%;height:100%;object-fit:cover;transition:1s cubic-bezier(.2,.8,.2,1)}
.c:hover .ph img{transform:scale(1.07)}
.c .tag{position:absolute;top:13px;left:13px;background:rgba(23,16,10,.88);backdrop-filter:blur(6px);color:var(--bronze);font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;padding:7px 12px;font-weight:700}
.c .in{padding:24px;display:flex;flex-direction:column;flex:1}
.c h3{margin-bottom:12px}
.c ul{list-style:none;margin:0 0 20px;flex:1}
.c li{font-size:13.5px;color:var(--muted);padding:6px 0 6px 18px;position:relative}
.c li::before{content:"";position:absolute;left:0;top:14px;width:6px;height:6px;background:var(--bronze);opacity:.65}
.c .foot{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;border-top:1px solid var(--line);padding-top:16px}
.c .pr b{font-family:var(--f-display);font-size:1.7rem;color:var(--bronze);display:block;line-height:1;font-variant-numeric:tabular-nums;font-weight:400}
.c .pr span{font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.pick{font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--bronze);border:1px solid var(--bronze);padding:13px 16px;cursor:pointer;background:none;font-family:var(--f-body);font-weight:700;white-space:nowrap;transition:.3s}
.pick:hover{background:var(--bronze);color:var(--bark)}
.weekly{margin:78px 0;border:1px solid var(--line);display:grid;grid-template-columns:1fr 1.3fr;background:var(--bark-2)}
.weekly .ph{overflow:hidden;min-height:280px}
.weekly .ph img{width:100%;height:100%;object-fit:cover}
.weekly .txt{padding:44px}
.weekly .when{display:inline-flex;align-items:center;gap:10px;border:1px solid var(--line);padding:9px 15px;font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--bronze);font-weight:700;margin-bottom:20px}
.weekly .when i{width:7px;height:7px;border-radius:50%;background:var(--palm);display:inline-block}
.weekly h2{margin-bottom:14px}
.weekly .perks{display:flex;gap:26px;flex-wrap:wrap;margin-top:24px;font-size:14px;color:var(--prose)}
.weekly .perks span{display:flex;gap:9px;align-items:center}
.weekly .perks em{color:var(--palm);font-style:normal}
.req{background:var(--bark-2);padding:88px 0;border-top:1px solid var(--line)}
.req-grid{display:grid;grid-template-columns:1fr 400px;gap:56px;align-items:start;margin-top:40px}
.form .f{margin-bottom:18px}
.form label{display:block;font-size:9.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--bronze);margin-bottom:7px;font-weight:700}
.form input,.form select,.form textarea{width:100%;min-height:46px;background:transparent;border:1px solid var(--line);color:var(--cream);font:400 15px/1.5 var(--f-body);padding:11px 13px;outline:none;transition:.3s}
.form textarea{min-height:96px;resize:vertical}
.form input:focus,.form select:focus,.form textarea:focus{border-color:var(--bronze)}
.form select option{background:var(--bark-2);color:var(--cream)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.recap{background:var(--bark);border:1px solid var(--line);padding:28px;position:sticky;top:110px}
.recap h3{margin-bottom:18px}
.recap .row{display:flex;justify-content:space-between;gap:14px;font-size:14px;color:var(--muted);padding:9px 0;border-bottom:1px solid var(--line)}
.recap .row span:last-child{color:var(--prose);text-align:right;font-variant-numeric:tabular-nums}
.recap .tot{display:flex;justify-content:space-between;align-items:baseline;gap:14px;margin-top:18px;padding-top:16px;border-top:1px solid var(--line)}
.recap .tot span{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:700}
.recap .tot b{font-family:var(--f-display);font-size:1.9rem;color:var(--bronze-2);font-variant-numeric:tabular-nums;font-weight:400}
.recap .btn{width:100%;margin-top:20px}
.recap .note{font-size:12.5px;color:var(--muted);text-align:center;margin-top:14px;line-height:1.5}
@media(max-width:1080px){
  .grid,.packs{grid-template-columns:repeat(2,1fr)}
  .star,.weekly{grid-template-columns:1fr}
  .star .ph,.weekly .ph{min-height:280px}
  .req-grid{grid-template-columns:1fr;gap:34px}
  .recap{position:static}
}
@media(max-width:720px){
  .head{padding:126px 0 34px}
  .grid,.packs,.two{grid-template-columns:1fr}
  .star .txt,.weekly .txt,.camp{padding:24px}
  .c .foot{flex-direction:column;align-items:stretch;gap:14px}
  .pick{text-align:center}
}
"""

PACKS = [
 ('Pack Famille','250000','forfait','g-aerien-t','Vue aérienne du domaine Evannath','p1','uf','FCFA · le forfait','250 000'),
 ('Pack Couple','150000','forfait','gal-lag-nuit','La paillote éclairée à la tombée du jour','p2','uf','FCFA · le forfait','150 000'),
 ('Pack Chillday','50000','personne','g-terrasse-t','Terrasse et transats de l\'hôtel','p3','up','FCFA · par personne','50 000'),
 ('Pack Enfant','15000','enfant','ig-enfants',"Des enfants dans la piscine de l'hôtel",'p4','ue','FCFA · par enfant','15 000'),
]

# Les decouvertes se distinguent des forfaits de sejour : elles emmenent
# ailleurs qu'a l'hotel. La page les presente separement.
DECOUVERTES = {'Découvertes Touristiques', 'Découvertes Junior'}

CARDS = [
 ('duo','gal-lag-bateau','Le ponton et le bateau de balade sur la lagune Aby','g1','Romantique','t1','Évasion Romantique',
  [('s11','Cocktails de charme'),('s12','Balade dînatoire aux chandelles'),('s13','Petit-déjeuner au lit'),('s14','Duo de massages')],
  '100 000','100000','forfait','pf','FCFA · le forfait'),
 ('duo','r-standard','Chambre Standard de l\'Hôtel Evannath','g2','Week-end','t2','Week-End Intense',
  [('s21','Chambre Standard + 2 petits-déjeuners'),('s22','Apéro, puis dîner ou déjeuner'),('s23','Balade lagunaire ou jet ski'),('s24','Baignade, fitness et massage')],
  '155 000','155000','forfait','pf','FCFA · le forfait'),
 ('fam grp','g-lagune','La lagune Aby et les îles environnantes','g3','Découverte','t3','Découvertes Touristiques',
  [('s31','Découverte des îles environnantes'),('s32','Balade touristique guidée'),('s33','Histoire de la commune d\'Assinie'),('s34','En-cas à emporter')],
  '35 000','35000','personne','pp','FCFA · par personne'),
 ('fam','c-piscine','La piscine de l\'hôtel en fin de journée','g4','Enfants','t4','Découvertes Junior',
  [('s41','Maquillage enfant et accès aux jeux'),('s42','Atelier cuisine et atelier peinture'),('s43','Conte en bordure d\'eau, le soir'),('s44','Soins princes &amp; princesses')],
  '25 000','25000','enfant','pe','FCFA · par enfant'),
 ('long fam','g-vue','Vue sur la lagune et les cocotiers d\'Assinie','g5','Long séjour','t5','Long Holidays',
  [('s51','−10 % sur chaque nuitée supplémentaire'),('s52','Balade lagunaire offerte dès 3 jours'),('s53','Applicable à toutes les catégories'),('s54','Cumulable avec la navette aéroport')],
  '25 000','25000','forfait','pf','FCFA · le forfait'),
 ('grp fam','g-resto','Salle de restaurant dressée pour un groupe','g6','Dès 10 personnes','t6','Coffret Anniversaire',
  [('s61','Salle privatisée, offerte'),('s62','Buffet : entrées, plats chauds, dessert'),('s63','Boissons comprises'),('s64','Sonorisation et technicien son offerts')],
  '28 000','28000','personne','pp','FCFA · par personne'),
]

def rendre_cartes(liste):
    """Rend un groupe de cartes.

    Les cartes se rendent en deux groupes — les forfaits, puis les
    decouvertes. Le catalogue JSON-LD, lui, continue de se batir sur CARDS
    entier : il ne doit rien perdre au decoupage.
    """
    for cat, img, alt, gkey, glab, tkey, tlab, items, disp, price, unit, ukey, ulab in liste:
        b.append('''    <article class="c reveal" data-cat="%s">
          <div class="ph"><picture><source srcset="img/opt/%s.webp" type="image/webp">
            <img loading="lazy" src="img/opt/%s.jpg" width="900" height="562" alt="%s"></picture>
            <span class="tag" data-t="%s">%s</span></div>
          <div class="in">
            <h3 data-t="%s">%s</h3>
            <ul>''' % (cat, img, img, alt, gkey, glab, tkey, tlab))
        for k, t in items:
            b.append('          <li data-t="%s">%s</li>' % (k, t))
        b.append('''        </ul>
            <div class="foot"><div class="pr"><b>%s</b><span data-t="%s">%s</span></div>
            <button class="pick pickbtn" data-c="%s" data-p="%s" data-u="%s" data-t="ch">Choisir</button></div>
          </div>
        </article>''' % (disp, ukey, ulab, tlab, price, unit))


b = [header('#demande','Réserver'), drawer('circuits.html'), '''
<div class="wrap head">
  <nav class="crumb" aria-label="Fil d'Ariane">
    <a href="index.html" data-t="c1">Accueil</a> &nbsp;·&nbsp; <span data-t="c2">Offres &amp; Événements</span>
  </nav>
  <span class="eyebrow" data-t="eb">Onze offres &amp; un rendez-vous hebdomadaire</span>
  <h1 data-t="h1">Offres &amp; Événements</h1>
  <p class="lede" data-t="lede">Ce qui se passe en ce moment, et les séjours déjà composés — chambre, repas, activités et attentions comprises. Choisissez, indiquez vos dates, et la réception s'occupe du reste.</p>
</div>

<div class="wrap">
{{AGENDA}}
  <div class="sect reveal" id="forfaits">
    <span class="eyebrow" data-t="f0">Séjours composés</span>
    <h2 data-t="f1">Nos offres &amp; forfaits</h2>
    <p data-t="f2">Tout est compris et le tarif est ferme : vous savez ce que
    vous payez avant d'arriver.</p>
  </div>

  <!-- Les remises publiees depuis l'administration. Le bloc reste vide
       — donc invisible — tant qu'il n'y en a aucune : mieux vaut rien
       qu'un cadre annoncant des offres absentes. -->
  <div class="remises" id="remises"></div>

  <!-- Les campagnes publiees depuis l'administration prennent la place de
       celle qui suit, figee dans le code. Celle-ci reste comme secours :
       la page garde du contenu si l'API se tait. -->
  <div id="campagnes"></div>

  <!-- Campagne relevée sur la page Facebook (21 000 abonnés) : absente du site actuel -->
  <section class="camp reveal" id="camp-figee">
    <div class="top">
      <div>
        <span class="live"><i></i><span data-t="cl">Campagne en cours</span></span>
        <h2 data-t="ct">Packs Vacances</h2>
      </div>
      <p style="font-size:13px;color:var(--muted);max-width:30ch;text-align:right" data-t="cs">Annoncés sur notre page Facebook · +225 01 51 52 75 75</p>
    </div>
    <p data-t="cp">« Les vacances qui vous ressemblent. » Quatre formules pensées pour la saison, réservables directement ici.</p>
    <div class="packs">''']

for name, price, unit, img, alt, key, ukey, ulab, disp in PACKS:
    b.append('''      <article class="pack">
        <div class="ph"><picture><source srcset="img/opt/%s.webp" type="image/webp"><img loading="lazy" src="img/opt/%s.jpg" width="700" height="467" alt="%s"></picture></div>
        <div class="in"><h3 data-t="%s">%s</h3><b>%s</b><span data-t="%s">%s</span>
        <button class="pick pickbtn" data-c="%s" data-p="%s" data-u="%s" data-t="ch">Choisir</button></div>
      </article>''' % (img, img, alt, key, name, disp, ukey, ulab, name, price, unit))

b.append('''    </div>
  </section>

  <article class="star reveal">
    <div class="ph">
      <picture><source srcset="img/opt/r-mezzanine.webp" type="image/webp">
      <img src="img/opt/r-mezzanine.jpg" width="900" height="600" alt="Mezzanine Supérieure décorée pour une lune de miel"></picture>
      <span class="badge" data-t="bd">Le plus demandé</span>
    </div>
    <div class="txt">
      <span class="eyebrow" data-t="e0">Pour deux</span>
      <h2 data-t="t0">Lune de miel<br>inoubliable</h2>
      <p data-t="d0">Deux nuits en Mezzanine Supérieure, décorée pour l'occasion avant votre arrivée. La catégorie duplex, avec terrasse privative et vue sur le domaine.</p>
      <ul class="incl">
        <li><i>✓</i><span data-t="s01">2 nuits en Mezzanine Supérieure</span></li>
        <li><i>✓</i><span data-t="s02">Décoration de la chambre à votre arrivée</span></li>
        <li><i>✓</i><span data-t="s03">Petits-déjeuners inclus</span></li>
        <li><i>✓</i><span data-t="s04">Navette aéroport gratuite</span></li>
      </ul>
      <div class="foot">
        <div class="pr"><b>340 000</b><span data-t="pf">FCFA · le forfait</span></div>
        <button class="btn btn-solid pickbtn" data-c="Lune de miel inoubliable" data-p="340000" data-u="forfait" data-t="ctc">Réserver ce circuit</button>
      </div>
    </div>
  </article>

  <div class="filters reveal">
    <button class="on" data-f="all" data-t="fa">Tout voir</button>
    <button data-f="duo" data-t="fb">Pour deux</button>
    <button data-f="fam" data-t="fc">En famille</button>
    <button data-f="grp" data-t="fd">Groupes</button>
    <button data-f="long" data-t="fe">Séjours longs</button>
  </div>

  <div class="grid" id="gr">''')

rendre_cartes([c for c in CARDS if c[6] not in DECOUVERTES])

b.append('''  </div>

  <div class="sect reveal" id="decouvertes">
    <span class="eyebrow" data-t="dc0">Autour d'Assinie</span>
    <h2 data-t="dc1">Circuits &amp; découvertes</h2>
    <p data-t="dc2">Sortir du domaine : les îles de la lagune, l'embouchure, et
    ce que les enfants retiennent d'un séjour ici.</p>
  </div>

  <div class="grid">''')

rendre_cartes([c for c in CARDS if c[6] in DECOUVERTES])

b.append('''  </div>

  <div class="sect reveal">
    <p style="color:var(--muted)"><a href="experiences.html" style="color:var(--bronze)"
    data-t="dc3">Voir aussi toutes les activités du domaine et de la lagune →</a></p>
  </div>



</div>

<section class="req" id="demande">
 <div class="wrap">
  <span class="eyebrow" data-t="e9">Votre demande</span>
  <h2 data-t="h9">Réserver un circuit</h2>
  <div class="req-grid">
    <form class="form" id="rf">
      <div class="f"><label for="circ" data-t="l1">Circuit choisi</label>
        <select id="circ">
          <option value="340000|forfait">Lune de miel inoubliable — 340 000 FCFA</option>
          <option value="250000|forfait">Pack Famille — 250 000 FCFA</option>
          <option value="155000|forfait">Week-End Intense — 155 000 FCFA</option>
          <option value="150000|forfait">Pack Couple — 150 000 FCFA</option>
          <option value="100000|forfait">Évasion Romantique — 100 000 FCFA</option>
          <option value="50000|personne">Pack Chillday — 50 000 FCFA / pers.</option>
          <option value="35000|personne">Découvertes Touristiques — 35 000 FCFA / pers.</option>
          <option value="28000|personne">Coffret Anniversaire — 28 000 FCFA / pers.</option>
          <option value="25000|enfant">Découvertes Junior — 25 000 FCFA / enfant</option>
          <option value="25000|forfait">Long Holidays — 25 000 FCFA</option>
          <option value="15000|enfant">Pack Enfant — 15 000 FCFA / enfant</option>
        </select>
      </div>
      <div class="two">
        <div class="f"><label for="dt" data-t="l2">Date souhaitée</label><input type="date" id="dt"></div>
        <div class="f"><label for="qt" data-t="l3">Nombre</label><input type="number" id="qt" min="1" max="40" value="2"></div>
      </div>
      <div class="two">
        <div class="f"><label for="nm" data-t="l4">Nom complet</label><input type="text" id="nm" placeholder="Aya Kouassi" required></div>
        <div class="f"><label for="tel" data-t="l5">Téléphone / WhatsApp</label><input type="tel" id="tel" placeholder="+225 01 02 03 04 05" required></div>
      </div>
      <div class="f"><label for="em" data-t="l6">E-mail</label><input type="email" id="em" placeholder="vous@exemple.com" required></div>
      <div class="f"><label for="msg" data-t="l7">Précisions (facultatif)</label><textarea id="msg" placeholder="Occasion particulière, allergies, heure d'arrivée…"></textarea></div>
    </form>

    <aside class="recap">
      <h3 data-t="r0">Votre récapitulatif</h3>
      <div class="row"><span data-t="r1">Circuit</span><span id="rc">Lune de miel inoubliable</span></div>
      <div class="row"><span data-t="r2">Date</span><span id="rd">—</span></div>
      <div class="row"><span id="rql">Quantité</span><span id="rq">1 forfait</span></div>
      <div class="row"><span data-t="r4">Tarif unitaire</span><span id="ru">340 000</span></div>
      <div class="tot"><span data-t="r5">Total</span><b id="rt">340 000</b></div>
      <button type="submit" form="rf" class="btn btn-solid" data-t="r6">Envoyer la demande</button>
      <p class="note" data-t="r7">Réponse de la réception sous 24 h. Aucun paiement à cette étape.</p>
    </aside>
  </div>
 </div>
</section>

''' + FOOTER)

# Les titres des quatre sections, et les evenements. Les cles des evenements
# portent un tiret : elles DOIVENT etre quotees, sinon le dictionnaire n'est
# pas un objet JavaScript valide et tout le script de la page meurt.
EN_SECTIONS = ('u0:"Agenda",u1:"Events",u1b:"on now",''u2:"What happens at the hotel beyond your stay: evenings, the Saturday ''gathering, year-end celebrations.",'
               
               'f0:"Composed stays",f1:"Our offers &amp; packages",'
               'f2:"Everything is included and the rate is firm: you know what you '
               'pay before you arrive.",'
               'dc0:"Around Assinie",dc1:"Tours &amp; discoveries",'
               'dc2:"Beyond the grounds: the lagoon islands, the river mouth, and '
               'what children remember from a stay here.",'
               'dc3:"See also every activity on the grounds and the lagoon &rarr;",')
# Les cles des evenements portent un tiret : elles DOIVENT etre quotees,
# sinon le dictionnaire n'est pas un objet JavaScript valide et tout le
# script de la page meurt (voir controle 13 du verificateur).
from _evenements import INFOS_EN
for _e in EVENEMENTS:
    _tr = EV_EN.get(_e['slug'])
    if not _tr:
        continue
    _cat, _tit, _acc, _bad, _tex, _cta, _vals = _tr
    EN_SECTIONS += ('"g-%s":"%s","t-%s":"%s","a-%s":"%s","b-%s":"%s",'
                    '"x-%s":"%s","c-%s":"%s",' % (
        _e['slug'], _cat, _e['slug'], _tit, _e['slug'], _acc,
        _e['slug'], _bad, _e['slug'], _tex, _e['slug'], _cta))
    for _i, (_lib, _val) in enumerate(_e['infos']):
        _k = _lib[:3].lower()
        EN_SECTIONS += '"il-%s-%s":"%s",' % (_e['slug'], _k, INFOS_EN.get(_lib, _lib))
        if _i < len(_vals):
            EN_SECTIONS += '"iv-%s-%s":"%s",' % (_e['slug'], _k, _vals[_i])

JS = NAV_JS + '''

document.querySelectorAll('.filters button').forEach(function(b){b.onclick=function(){
  document.querySelectorAll('.filters button').forEach(function(x){x.classList.remove('on')});b.classList.add('on');
  var f=b.dataset.f;
  document.querySelectorAll('.c').forEach(function(c){c.classList.toggle('hide',f!=='all'&&c.dataset.cat.split(' ').indexOf(f)<0)});
}});

var circ=document.getElementById('circ'),dt=document.getElementById('dt'),qt=document.getElementById('qt');
function iso(d){return new Date(d.getTime()-d.getTimezoneOffset()*6e4).toISOString().slice(0,10)}
dt.value=iso(new Date(Date.now()+864e5*7)); dt.min=iso(new Date());
function fmt(n){return n.toLocaleString('fr-FR').replace(/ | |,/g,' ')}
var UNITS={forfait:['forfait','forfaits'],personne:['personne','personnes'],
  enfant:['enfant','enfants'],nuit:['nuit','nuits']};
function recap(){
  var parts=circ.value.split('|'),prix=+parts[0],unite=parts[1];
  var label=circ.options[circ.selectedIndex].text.split('—')[0].trim();
  var n=Math.max(1,Math.min(40,+qt.value||1));
  // un forfait couple ne se multiplie pas : on ne compte que les unités facturables
  var facturable=(unite==='forfait')?1:n;
  // Une unite inconnue — une formule publiee avec une unite ajoutee plus
  // tard — ne doit pas casser le calcul et emporter toute la page.
  var mots=UNITS[unite]||UNITS.forfait;
  document.getElementById('rc').textContent=label;
  document.getElementById('rd').textContent=dt.value?new Date(dt.value).toLocaleDateString('fr-FR',{day:'numeric',month:'long',year:'numeric'}):'—';
  document.getElementById('rql').textContent=(unite==='forfait')?'Forfait':'Quantité';
  document.getElementById('rq').textContent=facturable+' '+(facturable>1?mots[1]:mots[0]);
  document.getElementById('ru').textContent=fmt(prix);
  document.getElementById('rt').textContent=fmt(prix*facturable);
  qt.disabled=(unite==='forfait');
  qt.style.opacity=(unite==='forfait')?.45:1;
}
[circ,dt,qt].forEach(function(e){e.addEventListener('input',recap);e.addEventListener('change',recap)});
recap();

/* Delegation : les formules publiees depuis l administration arrivent APRES
   le chargement. Attacher le clic a chaque bouton existant les laissait
   inertes — on cliquait, rien ne se passait, sans erreur. */
document.addEventListener('click', function(ev){
  var b = ev.target.closest && ev.target.closest('.pickbtn');
  if (!b) return;
  var want = b.dataset.p + '|' + b.dataset.u;
  for (var i = 0; i < circ.options.length; i++) {
    if (circ.options[i].value === want) { circ.selectedIndex = i; break; }
  }
  recap();
  document.getElementById('demande').scrollIntoView({behavior:'smooth',block:'start'});
});

document.getElementById('rf').addEventListener('submit',function(e){e.preventDefault();
  alert("Démonstration : la demande partirait à la réception et à {{MAIL}}, avec une confirmation automatique au client.")});

var EN={''' + EN_NAV + EN_SECTIONS + '''cta:"Book",ctc:"Book this package",
c1:"Home",c2:"Offers &amp; Events",eb:"Eleven offers &amp; one weekly gathering",h1:"Offers &amp; Events",
lede:"Stays already put together — room, meals, activities and small touches included. Pick one, give us your dates, and the front desk handles the rest.",
cl:"Live campaign",ct:"Holiday Packs",cs:"Announced on our Facebook page · +225 01 51 52 75 75",
cp:"“Holidays that look like you.” Four seasonal packages, bookable right here.",
p1:"Family Pack",p2:"Couples Pack",p3:"Chillday Pack",p4:"Kids Pack",
uf:"FCFA · package",up:"FCFA · per person",ue:"FCFA · per child",
bd:"Most requested",e0:"For two",t0:"An unforgettable<br>honeymoon",
d0:"Two nights in a Superior Mezzanine, decorated before you arrive. The duplex category, with a private terrace overlooking the estate.",
s01:"2 nights in a Superior Mezzanine",s02:"Room decorated on arrival",s03:"Breakfasts included",s04:"Free airport shuttle",
pf:"FCFA · package",pp:"FCFA · per person",pe:"FCFA · per child",ch:"Select",
fa:"View all",fb:"For two",fc:"Family",fd:"Groups",fe:"Long stays",
g1:"Romantic",t1:"Romantic Escape",s11:"Signature cocktails",s12:"Candlelit dinner cruise",s13:"Breakfast in bed",s14:"Couples massage",
g2:"Weekend",t2:"Intense Weekend",s21:"Standard room + 2 breakfasts",s22:"Aperitif, then dinner or lunch",s23:"Lagoon cruise or jet ski",s24:"Swimming, gym and massage",
g3:"Discovery",t3:"Sightseeing Tours",s31:"The surrounding islands",s32:"Guided walking tour",s33:"The history of Assinie",s34:"Snack to take along",
g4:"Children",t4:"Junior Discovery",s41:"Face painting and play area",s42:"Cooking and painting workshops",s43:"Waterside storytelling at dusk",s44:"Little prince &amp; princess treatments",
g5:"Long stay",t5:"Long Holidays",s51:"−10 % on every extra night",s52:"Free lagoon cruise from 3 days",s53:"Valid on every category",s54:"Combines with the airport shuttle",
g6:"From 10 guests",t6:"Birthday Box",s61:"Private room, free of charge",s62:"Buffet: starters, mains, dessert",s63:"Drinks included",s64:"PA system and sound engineer included",
w0:"Every Saturday, from 3 pm",w1:"Méchoui Party",
w2:"This one is not a package: it is the Saturday afternoon gathering, open to everyone — hotel guests and visitors alike. Méchoui by the water, then the evening carries on at the night club.",
w3:"A complimentary cocktail",w4:"Happy hour at the night club",w5:"−10 % on all drinks",w6:"Book a table",
e9:"Your request",h9:"Book a package",l1:"Chosen package",l2:"Preferred date",l3:"Number",l4:"Full name",l5:"Phone / WhatsApp",l6:"Email",l7:"Notes (optional)",
r0:"Your summary",r1:"Package",r2:"Date",r4:"Unit price",r5:"Total",r6:"Send request",
r7:"The front desk replies within 24 h. No payment at this stage."};

''' + LANG_JS

# Les onze offres, declarees a Google avec leur prix et leur unite.
#
# Elles etaient affichees mais invisibles des moteurs : le Service n'avait pas
# de catalogue, donc aucun des onze forfaits n'existait pour une recherche du
# type « forfait lune de miel Assinie ». Le catalogue se construit ici a
# partir des memes listes que la page — PACKS et CARDS — pour qu'il ne puisse
# pas deriver du contenu affiche.
UNITE = {'forfait': 'le forfait', 'personne': 'par personne', 'enfant': 'par enfant'}

CATALOGUE = [
    ('Lune de miel inoubliable', '340000',
     "Deux nuits en Mezzanine Supérieure, décorée pour l'occasion avant votre "
     "arrivée. Petits-déjeuners inclus, navette aéroport gratuite.",
     UNITE['forfait']),
]
CATALOGUE += [(nom, prix, None, UNITE[unite])
              for nom, prix, unite, _i, _a, _k, _u, _l, _d in PACKS]
CATALOGUE += [(titre, prix, ' · '.join(t for _c, t in items), UNITE[unite])
              for _f, _i, _a, _g, _b, _t, titre, items, _d, prix, unite, _pk, _ul in CARDS]

# ── L'agenda : un evenement a la fois, plein cadre ───────────
# Une diapositive perimee est retiree par le navigateur au chargement, avant
# meme que le carrousel demarre : le site est statique et personne ne le
# reconstruit le 2 janvier au matin pour decrocher l'affiche du reveillon.
def _pastilles(e):
    out = []
    for lib, val in e['infos']:
        out.append('<span><b data-t="il-%s-%s">%s</b>'
                   '<i data-t="iv-%s-%s">%s</i></span>'
                   % (e['slug'], lib[:3].lower(), lib,
                      e['slug'], lib[:3].lower(), val))
    return ''.join(out)

DIAPOS = ''
for _n, e in enumerate(EVENEMENTS):
    DIAPOS += '''
    <article class="diapo%s" id="%s"%s>
      <picture><source srcset="img/opt/%s.webp" type="image/webp">
        <img src="img/opt/%s.jpg" alt="" loading="lazy"></picture>
      <div class="voile"></div>
      <div class="dedans">
        <span class="pastille" data-t="b-%s">%s</span>
        <span class="cat" data-t="g-%s">%s</span>
        <h3><span data-t="t-%s">%s</span> <em data-t="a-%s">%s</em></h3>
        <p data-t="x-%s">%s</p>
        <div class="infos">%s</div>
        <a class="btn btn-solid" href="%s" data-t="c-%s">%s</a>
      </div>
    </article>''' % (
      ' on' if _n == 0 else '', e['slug'],
      (' data-fin="%s"' % e['fin']) if e['fin'] else '',
      e['fond'], e['fond'],
      e['slug'], e['badge'], e['slug'], e['categorie'],
      e['slug'], e['titre'], e['slug'], e['accent'],
      e['slug'], e['texte'], _pastilles(e),
      e['href'], e['slug'], e['cta'])

AGENDA = ('''
  <div class="sect reveal" id="a-la-une">
    <span class="eyebrow" data-t="u0">Agenda</span>
    <h2><span data-t="u1">Événements</span> <em data-t="u1b">du moment</em></h2>
    <p data-t="u2">Ce qui se passe à l'hôtel au-delà de votre séjour :
    soirées, rendez-vous du samedi, fêtes de fin d'année.</p>
  </div>

  <div class="agenda reveal" id="agenda">
    <div class="diapos">''' + DIAPOS + '''
    </div>
    <div class="pilote">
      <button type="button" class="prec" aria-label="Événement précédent">&lsaquo;</button>
      <span class="cpt"><b>01</b><span>/</span><i>01</i></span>
      <button type="button" class="suiv" aria-label="Événement suivant">&rsaquo;</button>
    </div>
  </div>''') if EVENEMENTS else ''


# ── Le carrousel de l'agenda ─────────────────────────────────
# Trois choses, dans cet ordre : on ecarte les diapositives perimees, on
# demande a l'administration s'il y a des evenements publies, et on demarre.
# Le contenu genere sert de secours : la page fonctionne sans JavaScript, et
# si l'API se tait, elle affiche ce qui a ete construit.
# Les noms des chambres, pour que les remises disent « Suite Anglaise » et
# non « suite-anglaise ». Ils viennent du catalogue, pas d une liste recopiee.
# Les cartes de pack sont petites : servir l image pleine y serait trois a
# six fois plus lourd pour rien. On dit au navigateur lesquelles ont une
# vignette -t, la version figee les utilise deja.
import glob as _glob, os as _os
_vign = sorted(_os.path.basename(f)[:-6] for f in _glob.glob('img/opt/*-t.jpg'))
JS += (chr(10) + 'window.VIGNETTES = '
       + _json.dumps(_vign, ensure_ascii=False) + ';' + chr(10))

JS += (chr(10) + 'window.NOMS_CHAMBRES = '
       + _json.dumps({c['slug']: c['nom'] for c in _chambres.CHAMBRES},
                     ensure_ascii=False) + ';' + chr(10))

JS += """
(function(){
  var ag = document.getElementById('agenda');
  if (!ag) return;
  var hote = ag.querySelector('.diapos');
  var pilote = ag.querySelector('.pilote');
  var cpt = ag.querySelector('.cpt');
  var modele = ag.querySelector('.diapo').cloneNode(true);
  var diapos = [], n = 0, minuteur = null;
  var calme = matchMedia('(prefers-reduced-motion: reduce)');
  var DELAI = 7000;

  var perime = function(el){
    var f = el.getAttribute('data-fin');
    if (!f) return false;
    var auj = new Date(); auj.setHours(0,0,0,0);
    return new Date(f + 'T23:59:59') < auj;
  };
  var deux = function(v){ return (v < 10 ? '0' : '') + v; };

  function montrer(i){
    n = (i + diapos.length) % diapos.length;
    diapos.forEach(function(d, k){ d.classList.toggle('on', k === n); });
    if (cpt) {
      cpt.querySelector('b').textContent = deux(n + 1);
      cpt.querySelector('i').textContent = deux(diapos.length);
    }
  }

  /* Le defilement s'arrete des qu'on survole, qu'on met le clavier dedans, ou
     que l'onglet passe en arriere-plan : un carrousel qui tourne pendant qu'on
     lit une pastille est plus agacant qu'utile. */
  function relancer(){
    clearInterval(minuteur);
    if (calme.matches || diapos.length < 2) return;
    minuteur = setInterval(function(){ montrer(n + 1); }, DELAI);
  }
  function suspendre(){ clearInterval(minuteur); }

  /* definitif : la reponse du back-office est connue (arrivee ou echouee).
     Avant elle, une section vide est seulement masquee, jamais retiree — les
     evenements figes dans le code finissent tous par perimer, et les retirer
     tout de suite detachait le conteneur du document : ce que l'hotel venait
     de publier s'ecrivait ensuite dans un element absent de la page. */
  function demarrer(definitif){
    diapos = [].slice.call(hote.querySelectorAll('.diapo')).filter(function(d){
      if (perime(d)) { d.remove(); return false; }
      return true;
    });
    var titre = document.getElementById('a-la-une');
    if (!diapos.length) {
      /* Plus rien a l'affiche : on retire la section plutot que d'exposer un
         cadre vide. */
      if (definitif) { ag.remove(); if (titre) titre.remove(); return; }
      ag.style.display = 'none';
      if (titre) titre.style.display = 'none';
      return;
    }
    ag.style.display = '';
    if (titre) titre.style.display = '';
    montrer(0);
    if (pilote) pilote.style.display = diapos.length < 2 ? 'none' : '';
    relancer();
  }

  /* Les evenements publies depuis l'administration remplacent les generes. */
  function refaire(liste){
    hote.innerHTML = '';
    liste.forEach(function(e){
      var d = modele.cloneNode(true);
      d.id = e.id || ''; d.className = 'diapo' + (e.format === 'affiche' ? ' affiche' : '');
      if (e.fin) d.setAttribute('data-fin', e.fin); else d.removeAttribute('data-fin');
      var im = d.querySelector('img'), so = d.querySelector('source');
      /* Le champ porte soit l'URL d'une affiche deposee, soit le nom d'une
         photo du site. */
      if (e.fond) {
        var url = /^https?:/.test(e.fond) ? e.fond : 'img/opt/' + e.fond + '.jpg';
        if (im) {
          im.src = url;
          /* Le modele est clone d'une diapositive generee : son img porte le
             srcset d'une photo du site. Or srcset l'emporte sur src — sans cet
             effacement, l'affiche deposee par l'hotel ne s'affiche jamais, et
             c'est la photo du modele qu'on voit a sa place. */
          im.removeAttribute('srcset'); im.removeAttribute('sizes');
          im.removeAttribute('width'); im.removeAttribute('height');
          im.alt = e.titre || '';
        }
        if (so) {
          if (/^https?:/.test(e.fond)) so.remove();
          else so.srcset = 'img/opt/' + e.fond + '.webp';
        }
      }
      /* Un champ vide se retire : laisse en place, il occupe une marge et
         creuse un trou dans la diapositive. */
      var poser = function(sel, val){
        var el = d.querySelector(sel);
        if (!el) return;
        if (val) el.textContent = val; else el.remove();
      };
      poser('.pastille', e.badge || e.quand);
      poser('.cat', e.categorie);
      d.querySelector('h3 span').textContent = e.titre || '';
      poser('h3 em', e.accent);
      poser('p', e.texte);
      var inf = d.querySelector('.infos');
      inf.innerHTML = '';
      (e.infos || []).forEach(function(pv){
        var c = document.createElement('span');
        var b = document.createElement('b'); b.textContent = pv[0];
        var it = document.createElement('i'); it.textContent = pv[1];
        c.appendChild(b); c.appendChild(it); inf.appendChild(c);
      });
      var a = d.querySelector('.btn');
      a.textContent = e.cta || 'En savoir plus';
      a.setAttribute('href', e.href || '#demande');
      /* Ces textes viennent de l'administration : ils n'ont pas de traduction,
         et doivent echapper au dictionnaire de la bascule de langue. */
      d.querySelectorAll('[data-t]').forEach(function(x){ x.removeAttribute('data-t'); });
      hote.appendChild(d);
    });
  }

  ag.addEventListener('mouseenter', suspendre);
  ag.addEventListener('mouseleave', relancer);
  ag.addEventListener('focusin', suspendre);
  ag.addEventListener('focusout', relancer);
  document.addEventListener('visibilitychange', function(){
    document.hidden ? suspendre() : relancer();
  });
  calme.addEventListener('change', relancer);

  ag.querySelector('.prec').addEventListener('click', function(){ montrer(n - 1); relancer(); });
  ag.querySelector('.suiv').addEventListener('click', function(){ montrer(n + 1); relancer(); });
  addEventListener('keydown', function(ev){
    if (!ag.getBoundingClientRect().height) return;
    if (ev.key === 'ArrowLeft')  { montrer(n - 1); relancer(); }
    if (ev.key === 'ArrowRight') { montrer(n + 1); relancer(); }
  });

  /* La page est livree avec les evenements figes dans le code. Les montrer
     tout de suite, puis les remplacer par ceux du back-office, donnait un
     clignotement : on voyait l'ancienne affiche avant la bonne. Le carrousel
     reste donc invisible jusqu'a ce qu'on sache quoi montrer.
     Le delai de garde evite l'inverse — une page vide si l'API tarde ou ne
     repond pas : passe ce delai, on montre ce qu'on a. */
  var devoile = false;
  function devoiler(){
    if (devoile) return;
    devoile = true;
    ag.style.opacity = '';
  }
  ag.style.opacity = '0';
  setTimeout(devoiler, 1200);

  demarrer(false);

  /* Le verdict tombe dans tous les cas — reponse vide, page hors ligne,
     fonction en panne — sinon une section masquee le resterait. */
  function conclure(j){
    if (j && j.evenements && j.evenements.length) refaire(j.evenements);
    demarrer(true);
    devoiler();
    poserRemises(j && j.promotions);
    poserCampagnes(j && j.campagnes);
  }

  /* Les remises publiees depuis l'administration. Le serveur ne renvoie
     que celles dont la periode court : rien a filtrer ici. */
  /* Une campagne publiee reprend exactement le gabarit des packs figes :
     meme section, memes cartes, meme bouton. Ce n est pas un autre
     affichage, c est le meme, rempli autrement. */
  function poserCampagnes(liste){
    var hote = document.getElementById('campagnes');
    if (!hote || !liste || !liste.length) return;

    // Du contenu publie remplace le contenu fige, comme pour l agenda.
    var figee = document.getElementById('camp-figee');
    if (figee) figee.remove();

    var choix = document.getElementById('circ');
    liste.forEach(function(c){
      var sec = document.createElement('section');
      sec.className = 'camp';

      var top = document.createElement('div');
      top.className = 'top';
      var g = document.createElement('div');
      g.innerHTML = '<span class="live"><i></i><span>Campagne en cours</span>'
        + '</span>';
      var h = document.createElement('h2');
      h.textContent = c.titre || '';
      g.appendChild(h);
      top.appendChild(g);
      if (c.note) {
        var n = document.createElement('p');
        n.style.cssText = 'font-size:13px;color:var(--muted);'
          + 'max-width:30ch;text-align:right';
        n.textContent = c.note;
        top.appendChild(n);
      }
      sec.appendChild(top);

      /* L affiche et l accroche cote a cote. L affiche porte deja les
         formules et les contacts ; le texte l accompagne au lieu de la
         precéder en un bloc qu on ne lit pas. */
      var duo = document.createElement('div');
      duo.className = 'camp-duo';

      if (c.visuel) {
        var fig = document.createElement('div');
        fig.className = 'camp-visuel';
        var vi = document.createElement('img');
        vi.src = /^https?:/.test(c.visuel) ? c.visuel
          : 'img/opt/' + c.visuel + '.jpg';
        vi.alt = c.titre || '';
        vi.loading = 'eager';
        vi.onerror = function(){ fig.remove(); duo.classList.add('seul'); };
        fig.appendChild(vi);
        duo.appendChild(fig);
      } else {
        duo.classList.add('seul');
      }

      if (c.accroche) {
        var a = document.createElement('p');
        a.className = 'camp-texte';
        // Les retours a la ligne de l hotel sont son decoupage : on les garde.
        a.textContent = c.accroche;
        duo.appendChild(a);
      }
      if (duo.children.length) sec.appendChild(duo);

      var grille = document.createElement('div');
      grille.className = 'packs';
      (c.packs || []).forEach(function(p){
        var art = document.createElement('article');
        art.className = 'pack';

        var ph = document.createElement('div');
        /* Les packs figes portent des photos, que le cadre 3/2 recadre
           sans dommage. Un pack publie porte une AFFICHE, souvent carree :
           la recadrer coupe son texte. La carte suit donc les proportions
           du visuel deposé. */
        ph.className = 'ph libre';
        if (p.image) {
          var im = document.createElement('img');
          /* La vignette quand elle existe : la carte est petite, l image
             pleine y pese trois a six fois plus pour rien. */
          var vg = (window.VIGNETTES || []).indexOf(p.image) >= 0 ? '-t' : '';
          im.src = /^https?:/.test(p.image) ? p.image
            : 'img/opt/' + p.image + vg + '.jpg';
          im.alt = p.nom || '';
          /* Pas de chargement paresseux : une image inseree APRES le
             chargement de la page n est pas prise en charge — verifie, la
             ressource repond 200 et la meme image en chargement immediat
             s affiche. Quatre vignettes ne justifient pas ce risque. */
          im.loading = 'eager';
          im.onerror = function(){ ph.remove(); };
          ph.appendChild(im);
        }
        art.appendChild(ph);

        var dedans = document.createElement('div');
        dedans.className = 'in';
        var t = document.createElement('h3'); t.textContent = p.nom || '';
        var pr = document.createElement('b');
        pr.textContent = Number(p.prix).toLocaleString('fr-FR');
        var u = document.createElement('span');
        u.textContent = 'FCFA · ' + (UNITES_NOM[p.unite] || 'le forfait');
        var bt = document.createElement('button');
        bt.type = 'button';
        bt.className = 'pick pickbtn';
        bt.dataset.c = p.nom;
        bt.dataset.p = String(p.prix);
        bt.dataset.u = p.unite || 'forfait';
        bt.textContent = 'Choisir';

        /* Le bouton selectionne une option de la liste de demande. Un pack
           publie depuis l administration n y figure pas : sans cet ajout,
           le clic serait sans effet, sans erreur et sans trace. */
        var val = p.prix + '|' + (p.unite || 'forfait');
        if (choix && !choix.querySelector('option[value="' + val + '"]')) {
          var o = document.createElement('option');
          o.value = val;
          o.textContent = p.nom + ' — '
            + Number(p.prix).toLocaleString('fr-FR') + ' FCFA';
          choix.appendChild(o);
        }

        dedans.appendChild(t); dedans.appendChild(pr);
        dedans.appendChild(u); dedans.appendChild(bt);
        art.appendChild(dedans);
        grille.appendChild(art);
      });
      sec.appendChild(grille);
      hote.appendChild(sec);
    });
  }

  var UNITES_NOM = { forfait: 'le forfait', personne: 'par personne',
                     enfant: 'par enfant', nuit: 'par nuit' };

  function poserRemises(liste){
    var hote = document.getElementById('remises');
    if (!hote || !liste || !liste.length) return;
    var noms = window.NOMS_CHAMBRES || {};
    liste.forEach(function(p){
      var img = p.fond
        ? (/^https?:/.test(p.fond) ? p.fond : 'img/opt/' + p.fond + '.jpg')
        : '';
      var art = document.createElement('article');
      /* Une affiche verticale — celles que l hotel publie sur Facebook —
         se montre ENTIERE : elle porte deja les dates, le tarif et le
         telephone. La rogner rend illisible ce qu elle dit. Une photo
         large, elle, se recadre sans dommage. */
      art.className = 'remise' + (img ? '' : ' sans-image')
        + (p.format === 'affiche' ? ' affiche' : '');

      if (img) {
        var pic = document.createElement('picture');
        var im = document.createElement('img');
        im.src = img; im.alt = p.titre || '';
        /* Pas de chargement paresseux ici. Une affiche s affiche en
           hauteur libre : tant qu elle n est pas chargee elle mesure zero
           pixel, donc elle n entre jamais dans l ecran, donc elle ne se
           charge jamais. Le blocage est circulaire, et il n y a de toute
           facon qu une poignee de promotions. */
        im.loading = 'eager';
        /* Une image supprimee ou mal nommee laisserait un cadre vide avec
           une icone cassee. On retire la colonne : la carte se lit tres
           bien sans visuel, mal avec un trou. */
        im.onerror = function(){
          pic.remove();
          art.className = 'remise sans-image';
        };
        pic.appendChild(im); art.appendChild(pic);
      }

      var d = document.createElement('div');
      d.className = 'dedans';

      var haut = document.createElement('div');
      haut.className = 'haut';
      var r = p.remise || {};
      if (r.valeur) {
        var t = document.createElement('span');
        t.className = 'taux';
        t.textContent = r.type === 'montant'
          ? '−' + Number(r.valeur).toLocaleString('fr-FR') + ' F'
          : '−' + r.valeur + ' %';
        haut.appendChild(t);
      }
      if (p.fin) {
        var j2 = document.createElement('span');
        j2.className = 'jusqua';
        j2.textContent = 'Jusqu’au ' + p.fin.slice(0, 10).split('-')
          .reverse().join('/');
        haut.appendChild(j2);
      }
      if (haut.children.length) d.appendChild(haut);

      var h = document.createElement('h3');
      h.textContent = p.titre || '';
      d.appendChild(h);

      if (p.message) {
        var m = document.createElement('p');
        m.textContent = p.message;
        d.appendChild(m);
      }

      var c = p.cible || {};
      var sur = document.createElement('div');
      sur.className = 'sur';
      if (c.toutes === false && (c.chambres || []).length) {
        sur.textContent = 'Sur : ' + c.chambres.map(function(s){
          return noms[s] || s; }).join(', ');
      } else {
        sur.textContent = 'Sur toutes nos chambres.';
      }
      d.appendChild(sur);

      var a = document.createElement('a');
      a.className = 'btn btn-solid';
      a.href = 'reserver.html';
      a.textContent = 'Réserver maintenant';
      d.appendChild(a);

      art.appendChild(d);
      hote.appendChild(art);
    });
  }
  fetch('/api/admin?a=public', { cache: 'no-store' })
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(conclure)
    .catch(function(){ demarrer(true); devoiler(); });
})();
"""
LD = _schema.bloc(
    _schema.service('Circuits et forfaits', "Packs Vacances, lune de miel, week-end intense, circuits touristiques et coffret anniversaire à l'Hôtel Evannath, Assinie.", 'circuits', image='r-mezzanine', catalogue=CATALOGUE),
    _schema.hotel(),
    _schema.fil([('Accueil','index'),('Offres & Événements',None)]))

CORPS = NL_.join(b).replace('{{AGENDA}}', AGENDA)

io.open('circuits.html','w',encoding='utf-8').write(page(
 "Offres &amp; Événements — Hôtel Evannath, Assinie",
 "Les offres et événements de l'Hôtel Evannath à Assinie : Packs Vacances, réveillon, Méchoui Party du samedi, lune de miel, week-end intense, découvertes touristiques et coffret anniversaire.",
 "r-mezzanine", CSS, CORPS, JS, slug="circuits", jsonld=LD))
print('circuits.html         ok')
