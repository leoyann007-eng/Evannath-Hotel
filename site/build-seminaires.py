# -*- coding: utf-8 -*-
"""Genere seminaires.html.

Le contenu factuel vient de la page Services de l'hotel : salle de conference
baignee de lumiere naturelle, sonorisation et technicien son disponibles,
formules journee d'etude et residentielles, Coffret Anniversaire des
10 personnes a 28 000 FCFA.

⚠️ Les CAPACITES (nombre de participants par configuration) sont des
hypotheses : l'hotel ne les publie nulle part. A confirmer avant mise en
production — voir la section « A valider » du README.
"""
import io
import _schema
from _chrome import (page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV, EN_SECOURS, CONF_TITRE, CONF_TITRE_EN, CONF_GESTE, CONF_GESTE_EN, CONF_VERBE, CONF_VERBE_EN,
                     ENVOI_JS, PIEGE, secours, CONF_SVG, CONF_CSS)

CONFIGS = [
 ('Théâtre',    '60', 'Chaises en rangées face à l\'écran. Pour une présentation, un lancement, une assemblée.'),
 ('Classe',     '35', 'Tables et chaises orientées vers l\'avant. Pour une formation où l\'on prend des notes.'),
 ('En U',       '25', 'Tables disposées en fer à cheval. Pour un comité de direction ou un atelier.'),
 ('Cocktail',   '90', 'Debout, mange-debout et buffet. Pour un lancement produit ou une réception.'),
 ('Banquet',    '70', 'Tables rondes de huit. Pour un dîner de gala ou un anniversaire.'),
]

FORMULES = [
 ('01', "Journée d'étude",
  "La salle pour la journée, la pause du matin, le déjeuner au restaurant et la pause de l'après-midi. "
  "Sonorisation, écran et technicien son compris.",
  "De 9 h à 18 h · sans hébergement"),
 ('02', "Séminaire résidentiel",
  "La journée d'étude, plus les chambres et les dîners. Nos sept catégories accueillent de deux à six "
  "personnes chacune, et la navette aéroport est offerte pour tout le groupe.",
  "Une à trois nuits · hébergement compris"),
 ('03', "Séminaire &amp; lagune",
  "Le travail le matin, la lagune l'après-midi : balade en pirogue, jet ski, ou simplement la piscine. "
  "C'est ce qui distingue Assinie d'une salle de réunion à Abidjan.",
  "Deux jours · activités comprises"),
 ('04', "Réception privée",
  "Cocktail, dîner de gala, lancement de produit, anniversaire d'entreprise. Salle privatisée, buffet "
  "complet, sonorisation et technicien son inclus dès dix personnes.",
  "Soirée · à partir de 10 personnes"),
]

EQUIP = [
 ('Lumière naturelle', "Baies vitrées sur toute la longueur", '<path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/><circle cx="12" cy="12" r="4"/>'),
 ('Sonorisation', "Micros, enceintes, table de mixage", '<path d="M12 3a3 3 0 013 3v6a3 3 0 01-6 0V6a3 3 0 013-3z"/><path d="M5 11a7 7 0 0014 0M12 18v3M9 21h6"/>'),
 ('Technicien son', "Présent toute la durée, compris", '<circle cx="9" cy="8" r="3.4"/><path d="M2 20a7 7 0 0114 0M17 11a3 3 0 100-6"/>'),
 ('Écran &amp; vidéoprojection', "Sur demande, sans supplément", '<rect x="3" y="4" width="18" height="12"/><path d="M12 16v4M8 20h8"/>'),
 ('Wifi sur tout le domaine', "Gratuit, dans la salle comme en chambre", '<path d="M5 13a10 10 0 0114 0M8.5 16.5a5 5 0 017 0"/><circle cx="12" cy="20" r="1"/>'),
 ('Restauration sur place', "Pauses, déjeuner, dîner de gala", '<path d="M12 3v6M8 21h8M6 12h12l-2 9H8z"/>'),
 ('Parking gratuit', "Surveillé, sur le domaine", '<rect x="3" y="3" width="18" height="18"/><path d="M9 17V7h3.5a3 3 0 010 6H9"/>'),
 ('Navette aéroport', "Offerte, aller et retour, pour le groupe", '<path d="M2 16l20-7-8 12-2-5-5-2z"/><path d="M4 20h7"/>'),
]

CSS = CONF_CSS + """
/* L'en-tete est fixe : le hero doit lui reserver sa hauteur, comme le font
   les pages sans hero avec leur padding de 150px. Sans cela, sur un ecran
   court, le contenu aligne en bas remonte et passe sous l'en-tete. */
.hero{position:relative;min-height:74vh;display:flex;align-items:flex-end;overflow:hidden;padding-top:150px}
.hero>picture img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.hero::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(23,16,10,.8),rgba(23,16,10,.4) 44%,rgba(23,16,10,.97))}
.hero .in{position:relative;z-index:3;width:100%;padding-bottom:56px}
.hero h1{margin:12px 0 18px;font-size:clamp(2.5rem,5.6vw,4rem)}
.hero p{max-width:58ch;font-size:1.08rem}

section{padding:104px 0}
.head{margin-bottom:56px}
.head.mid{text-align:center}
.head.mid p{max-width:54ch;margin:18px auto 0;color:var(--muted)}
.head p{color:var(--muted);margin-top:18px;max-width:58ch}

/* argument */
.pitch{display:grid;grid-template-columns:1fr 1.25fr;gap:70px;align-items:start}
.pitch .big{font-family:var(--f-display);font-size:clamp(1.5rem,2.7vw,2.15rem);line-height:1.4;color:var(--cream)}
.pitch p+p{margin-top:18px}

/* configurations */
.cfg-sec{background:var(--bark);border-block:1px solid var(--line)}
.cfg{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:var(--line);border:1px solid var(--line)}
.cfg div{background:var(--bark);padding:32px 22px;text-align:center;transition:.4s}
.cfg div:hover{background:var(--bark-3)}
.cfg b{display:block;font-family:var(--f-display);font-size:2.4rem;color:var(--bronze);line-height:1;font-variant-numeric:tabular-nums;font-weight:400}
.cfg .u{font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);font-weight:700;margin-top:7px;display:block}
.cfg h3{font-size:1.1rem;margin:18px 0 8px;font-weight:400}
.cfg p{font-size:13px;color:var(--muted)}

/* formules */
.plate{display:grid;grid-template-columns:88px 1fr auto;gap:34px;align-items:baseline;padding:36px 0;
  border-top:1px solid var(--line-2);transition:.45s}
.plate:last-of-type{border-bottom:1px solid var(--line-2)}
.plate:hover{background:linear-gradient(90deg,rgba(185,138,80,.055),transparent 70%)}
.plate .n{font-family:var(--f-display);font-size:2.2rem;color:var(--bronze);opacity:.4;line-height:.8;
  font-variant-numeric:tabular-nums;transition:.45s}
.plate:hover .n{opacity:1}
.plate h3{font-size:clamp(1.3rem,2.4vw,1.85rem);margin-bottom:10px;font-weight:400}
.plate p{font-size:14.5px;color:var(--muted);max-width:58ch}
.plate .q{font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);font-weight:700;text-align:right;white-space:nowrap}

/* equipements */
.eq-sec{background:var(--bark)}
.eq{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line)}
.eq div{background:var(--bark);padding:28px 24px}
.eq svg{width:22px;height:22px;stroke:var(--bronze);fill:none;stroke-width:1.3;margin-bottom:16px}
.eq b{display:block;font-size:14.5px;color:var(--cream);font-weight:600;margin-bottom:5px}
.eq span{font-size:13px;color:var(--muted)}

/* anniversaire */
.coffret{display:grid;grid-template-columns:1fr 1fr;border:1px solid var(--bronze);background:var(--bark-2)}
.coffret .ph{overflow:hidden;min-height:340px}
.coffret .ph img{width:100%;height:100%;object-fit:cover}
.coffret .tx{padding:48px}
.coffret h2{margin:12px 0 16px}
.coffret ul{list-style:none;margin:22px 0}
.coffret li{padding:11px 0;border-bottom:1px solid var(--line);font-size:14.5px;color:var(--prose);display:flex;gap:13px}
.coffret li i{color:var(--palm);font-style:normal}
.coffret .pr{display:flex;align-items:flex-end;gap:20px;flex-wrap:wrap;margin-top:26px}
.coffret .pr b{font-family:var(--f-display);font-size:2.5rem;color:var(--bronze);line-height:1;font-variant-numeric:tabular-nums;font-weight:400}
.coffret .pr span{font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:600}

/* devis */
.devis{background:var(--bark);padding:100px 0;border-top:1px solid var(--line)}
.devis-grid{display:grid;grid-template-columns:1fr 380px;gap:56px;align-items:start;margin-top:40px}
.f{display:flex;flex-direction:column;margin-bottom:18px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
label{font-size:9.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--bronze);margin-bottom:8px;font-weight:700}
input,select,textarea{min-height:48px;background:transparent;border:1px solid var(--line);color:var(--cream);
  font:400 15px/1.5 var(--f-body);padding:12px 14px;outline:none;transition:.3s;min-width:0;font-family:var(--f-body)}
textarea{min-height:110px;resize:vertical}
input:focus,select:focus,textarea:focus{border-color:var(--bronze)}
select option{background:var(--bark-2);color:var(--cream)}
/* Un exemple, pas une saisie : plus clair et en italique. A #6E6154, « Aya »
   et « Kouassi » se lisaient comme des champs deja remplis. */
input::placeholder,textarea::placeholder{color:#A39686;font-style:italic;opacity:1}
.f.bad input,.f.bad select{border-color:var(--err)}
.msg{display:none;font-size:12.5px;color:var(--err);margin-top:7px}
.f.bad .msg{display:block}
.sent{display:none;border:1px solid rgba(143,174,99,.5);background:rgba(143,174,99,.08);padding:24px 26px;margin-top:20px}
.sent.on{display:block}
.sent b{display:block;font-family:var(--f-display);font-size:1.3rem;color:var(--palm);margin-bottom:6px}
.sent p{font-size:14px;margin:0}
.aside-box{border:1px solid var(--line);background:var(--bark-2);padding:30px;position:sticky;top:110px}
.aside-box h3{font-size:1.25rem;margin-bottom:18px;font-weight:400}
.aside-box .r{display:flex;justify-content:space-between;gap:16px;padding:12px 0;border-bottom:1px solid var(--line-2);font-size:14px}
.aside-box .r:last-of-type{border-bottom:0}
.aside-box .r span:first-child{color:var(--muted);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;font-weight:600}
.aside-box .r span:last-child{color:var(--prose);text-align:right}
.aside-box .call{margin-top:22px;padding-top:20px;border-top:1px solid var(--line);font-size:13.5px;color:var(--muted)}
.aside-box .call a{color:var(--bronze);display:block;margin-top:6px;font-size:15px}

@media(max-width:1080px){
  .pitch,.coffret,.devis-grid{grid-template-columns:1fr;gap:40px}
  .cfg{grid-template-columns:repeat(2,1fr)}
  .eq{grid-template-columns:repeat(2,1fr)}
  .aside-box{position:static}
  .coffret .ph{min-height:260px}
}
@media(max-width:720px){
  section{padding:72px 0}
  .cfg,.eq,.two{grid-template-columns:1fr}
  .plate{grid-template-columns:minmax(0,1fr);gap:10px;padding:28px 0}
  .plate .n{font-size:1.5rem;opacity:1}
  .plate .q{text-align:left;white-space:normal}
  .coffret .tx{padding:28px}
}
"""

b = [header('#devis', 'Demander un devis', 'cta'), drawer(''), '''
<section class="hero">
  <picture><source srcset="img/opt/g-seminaire.webp" type="image/webp">
  <img src="img/opt/g-seminaire.jpg" width="1200" height="800" alt="La salle de conférence de l'Hôtel Evannath"></picture>
  <div class="in wrap">
    <nav class="crumb" aria-label="Fil d'Ariane">
      <a href="index.html" data-t="c1">Accueil</a> &nbsp;·&nbsp; <span data-t="c2">Séminaires &amp; groupes</span>
    </nav>
    <span class="eyebrow" data-t="eb1">Journées d'étude · résidentiels · réceptions</span>
    <h1 data-t="h1">Travailler ailleurs,<br>et que ça se voie</h1>
    <p data-t="lede">Une salle baignée de lumière naturelle, à une heure quarante-cinq d'Abidjan, avec la lagune Aby derrière. Vos équipes s'en souviendront plus longtemps que d'une salle d'hôtel du Plateau.</p>
  </div>
</section>

<section class="wrap">
  <div class="pitch reveal">
    <div>
      <span class="eyebrow" data-t="eb2">Pourquoi ici</span>
      <p class="big" style="margin-top:20px" data-t="big">Le trajet fait partie du séminaire.</p>
    </div>
    <div>
      <p data-t="pp1">Une heure quarante-cinq de route sépare Abidjan d'Assinie. C'est assez pour que le groupe décroche vraiment, et assez peu pour partir le matin et travailler à dix heures. La navette aéroport est offerte si vos participants arrivent en avion.</p>
      <p data-t="pp2">La salle donne sur l'extérieur par des baies vitrées : on n'y travaille pas en cave. Sonorisation, écran et technicien son sont compris, pas facturés en supplément à la fin.</p>
      <p data-t="pp3">Et à seize heures, quand la session est finie, il y a la piscine, le ponton et la pirogue. C'est ce qui transforme une journée d'étude en quelque chose dont on reparle.</p>
    </div>
  </div>
</section>

<section class="cfg-sec">
  <div class="wrap">
    <div class="head mid reveal">
      <span class="eyebrow" data-t="eb3">La salle</span>
      <h2 style="margin-top:16px" data-t="h3">Cinq configurations</h2>
      <p data-t="p3">Le mobilier se remonte selon vos besoins, la veille ou le matin même.</p>
    </div>
    <div class="cfg reveal">''']

for i, (nom, cap, desc) in enumerate(CONFIGS):
    b.append('      <div><b>%s</b><span class="u" data-t="cu%d">personnes</span>'
             '<h3 data-t="cn%d">%s</h3><p data-t="cd%d">%s</p></div>' % (cap, i, i, nom, i, desc))

b.append('''    </div>
    <p style="margin-top:24px;font-size:13px;color:var(--muted);font-style:italic">
      <span data-t="capn">Capacités indicatives — la réception confirme selon la configuration retenue et le nombre exact de participants.</span>
    </p>
  </div>
</section>

<section class="wrap">
  <div class="head reveal">
    <span class="eyebrow" data-t="eb4">Les formules</span>
    <h2 style="margin-top:16px" data-t="h4">Quatre façons<br>de réunir vos équipes</h2>
    <p data-t="p4">Chaque formule se chiffre selon l'effectif, la durée et la restauration retenue. Devis sous 24 h.</p>
  </div>
  <div class="reveal">''')

for i, (n, titre, desc, quand) in enumerate(FORMULES):
    b.append('''    <article class="plate">
      <span class="n">%s</span>
      <div><h3 data-t="ft%d">%s</h3><p data-t="fd%d">%s</p></div>
      <span class="q" data-t="fq%d">%s</span>
    </article>''' % (n, i, titre, i, desc, i, quand))

b.append('''  </div>
</section>

<section class="eq-sec">
  <div class="wrap">
    <div class="head mid reveal">
      <span class="eyebrow" data-t="eb5">Compris</span>
      <h2 style="margin-top:16px" data-t="h5">Ce que vous ne payerez pas en plus</h2>
    </div>
    <div class="eq reveal">''')

for i, (titre, desc, ic) in enumerate(EQUIP):
    b.append('      <div><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg>'
             '<b data-t="qt%d">%s</b><span data-t="qd%d">%s</span></div>' % (ic, i, titre, i, desc))

b.append('''    </div>
  </div>
</section>

<section class="wrap">
  <div class="coffret reveal">
    <div class="ph"><picture><source srcset="img/opt/gal-tab-salle.webp" type="image/webp">
      <img loading="lazy" src="img/opt/gal-tab-salle.jpg" alt="La salle de restaurant dressée pour un groupe"></picture></div>
    <div class="tx">
      <span class="eyebrow" data-t="eb6">Réception privée</span>
      <h2 data-t="h6">Le Coffret Anniversaire</h2>
      <p data-t="p6">Notre formule la plus simple à organiser : vous donnez une date et un nombre, nous faisons le reste.</p>
      <ul>
        <li><i>✓</i><span data-t="cl0">Salle privatisée, offerte</span></li>
        <li><i>✓</i><span data-t="cl1">Buffet complet — entrées, plats chauds, dessert</span></li>
        <li><i>✓</i><span data-t="cl2">Boissons comprises</span></li>
        <li><i>✓</i><span data-t="cl3">Sonorisation et technicien son inclus</span></li>
      </ul>
      <div class="pr">
        <div><b>28 000</b><span data-t="cpu">FCFA · par personne</span></div>
        <span style="font-size:13px;color:var(--muted)" data-t="cpm">à partir de 10 personnes</span>
      </div>
    </div>
  </div>
</section>

<section class="devis" id="devis">
  <div class="wrap">
    <span class="eyebrow" data-t="eb7">Votre projet</span>
    <h2 style="margin-top:16px" data-t="h7">Demander un devis</h2>
    <div class="devis-grid">
      <form id="df" novalidate>
        <div class="two">
          <div class="f"><label for="soc" data-t="lsoc">Société ou organisation *</label>
            <input type="text" id="soc" placeholder="Nom de votre structure">
            <span class="msg" data-t="msoc">Merci d'indiquer le nom de votre structure.</span></div>
          <div class="f"><label for="nom" data-t="lnom">Votre nom *</label>
            <input type="text" id="nom" placeholder="Aya Kouassi">
            <span class="msg" data-t="mnom">Merci d'indiquer votre nom.</span></div>
        </div>
        <div class="two">
          <div class="f"><label for="em" data-t="lem">E-mail *</label>
            <input type="email" id="em" placeholder="vous@societe.com">
            <span class="msg" data-t="mem">Cette adresse e-mail ne semble pas valide.</span></div>
          <div class="f"><label for="tel" data-t="ltel">Téléphone *</label>
            <input type="tel" id="tel" placeholder="+225 01 02 03 04 05">
            <span class="msg" data-t="mtel">Indiquez un numéro d'au moins 8 chiffres.</span></div>
        </div>
        <div class="two">
          <div class="f"><label for="typ" data-t="ltyp">Type d'événement</label>
            <select id="typ">
              <option value="Séminaire ou journée d&#39;étude" data-t="ty0">Séminaire ou journée d&#39;étude</option>
              <option value="Formation" data-t="ty1">Formation</option>
              <option value="Team building" data-t="ty2">Team building</option>
              <option value="Réception d&#39;entreprise" data-t="ty3">Réception d&#39;entreprise</option>
              <option value="Lancement de produit" data-t="ty4">Lancement de produit</option>
              <option value="Mariage" data-t="ty5">Mariage</option>
              <option value="Anniversaire" data-t="ty6">Anniversaire</option>
              <option value="Baptême" data-t="ty7">Baptême</option>
              <option value="Fête privée" data-t="ty8">Fête privée</option>
              <option value="Autre" data-t="ty9">Autre</option>
            </select></div>
          <div class="f"><label for="nch" data-t="lnch">Chambres souhaitées</label>
            <input type="number" id="nch" min="0" max="46" placeholder="0"></div>
        </div>
        <div class="two">
          <div class="f"><label for="form" data-t="lform">Formule</label>
            <select id="form">
              <option value="Journée d'étude" data-t="fo0">Journée d'étude</option>
              <option value="Séminaire résidentiel" data-t="fo1">Séminaire résidentiel</option>
              <option value="Séminaire &amp; lagune" data-t="fo2">Séminaire &amp; lagune</option>
              <option value="Réception privée" data-t="fo3">Réception privée</option>
              <option value="Coffret Anniversaire" data-t="fo4">Coffret Anniversaire</option>
              <option value="Je ne sais pas encore" data-t="fo5">Je ne sais pas encore</option>
            </select></div>
          <div class="f"><label for="cfg" data-t="lcfg">Configuration de salle</label>
            <select id="cfg">
              <option value="Théâtre" data-t="co0">Théâtre</option><option value="Classe" data-t="co1">Classe</option><option value="En U" data-t="co2">En U</option>
              <option value="Cocktail" data-t="co3">Cocktail</option><option value="Banquet" data-t="co4">Banquet</option><option value="À définir" data-t="co5">À définir</option>
            </select></div>
        </div>
        <div class="two">
          <div class="f"><label for="nb" data-t="lnb">Nombre de participants *</label>
            <input type="number" id="nb" min="1" max="200" value="25">
            <span class="msg" data-t="mnb">Indiquez au moins un participant.</span></div>
          <div class="f"><label for="dt" data-t="ldt">Date souhaitée</label><input type="date" id="dt"></div>
        </div>
        <div class="f"><label for="msg" data-t="lmsg">Votre projet</label>
          <textarea id="msg" placeholder="Durée, hébergement souhaité, activités, contraintes particulières…"></textarea></div>
        ''' + PIEGE + '''
        <button type="submit" class="btn btn-solid" id="envoi" data-t="env">Envoyer la demande</button>
        <p class="err-envoi" id="err" role="alert"></p>''' + secours('sec') + '''
        <div class="sent" id="ok" role="status">''' + CONF_SVG + '''<div class="conf-msg">
          <b data-t="okt">{{CT}}</b>
          <p id="okm">Merci. Le service commercial revient vers vous sous 24 h avec un devis détaillé.</p>
        </div></div>
      </form>

      <aside class="aside-box">
        <h3 data-t="ah3">Votre demande</h3>
        <div class="r"><span data-t="ar1">Formule</span><span id="rf">Journée d'étude</span></div>
        <div class="r"><span data-t="ar2">Salle</span><span id="rc">Théâtre</span></div>
        <div class="r"><span data-t="ar3">Participants</span><span id="rn">25</span></div>
        <div class="r"><span data-t="ar4">Date</span><span id="rd">—</span></div>
        <div class="r"><span data-t="ar5">Capacité</span><span id="rk">—</span></div>
        <div class="call">
          <span data-t="acall">Pour un projet urgent, appelez directement :</span>
          <a href="tel:+2250151527575">+225 01 51 52 75 75</a>
          <a href="mailto:{{MAIL}}">{{MAIL}}</a>
        </div>
      </aside>
    </div>
  </div>
</section>

''' + FOOTER)

JS = NAV_JS + ENVOI_JS + '''
var N='\\n';

var CAP={'Théâtre':60,'Classe':35,'En U':25,'Cocktail':90,'Banquet':70};
/* Le recapitulatif lateral et le message de confirmation sont ecrits par ce
   script, donc hors de portee de [data-t]. LANG_JS appelle EVN_LANG a chaque
   bascule. Les valeurs des <select> restent francaises : c'est ce qui part a
   la reception, et ce qui indexe CAP ci-dessus. */
var LG='fr';
var S={fr:{loc:'fr-FR',adef:'à définir',audela:'au-delà de ',etud:' — à étudier',
           sur:' sur ',places:' places',
           ok1:'{{CG}}Votre demande pour ',ok2:' participants en configuration « ',
           ok3:' » {{CV}} sous la référence ',
           ok4:". Le service commercial revient vers vous sous 24 h avec un devis détaillé."},
     en:{loc:'en-GB',adef:'to be defined',audela:'beyond ',etud:' — to be studied',
           sur:' of ',places:' seats',
           ok1:'{{CG_EN}}Your request for ',ok2:' participants in « ',
           ok3:' » layout {{CV_EN}} under reference ',
           ok4:'. The sales desk will come back to you within 24 h with a detailed quote.'}};
function EVN_LANG(lg){ LG=S[lg]?lg:'fr'; recap(); }
var form=document.getElementById('form'),cfg=document.getElementById('cfg'),
    nb=document.getElementById('nb'),dt=document.getElementById('dt');

function iso(d){return new Date(d.getTime()-d.getTimezoneOffset()*6e4).toISOString().slice(0,10)}
dt.value=iso(new Date(Date.now()+864e5*21)); dt.min=iso(new Date());

function recap(){
  /* On affiche le LIBELLE de l'option, pas sa valeur : la valeur reste
     francaise pour la reception et pour l'index CAP, le libelle suit la
     langue choisie. Sans cela le recapitulatif anglais gardait « Theatre »
     en francais. */
  var lib=function(sel){var o=sel.selectedOptions[0];return o?o.textContent:sel.value};
  document.getElementById('rf').textContent=lib(form);
  document.getElementById('rc').textContent=lib(cfg);
  var n=+nb.value||0;
  document.getElementById('rn').textContent=n;
  document.getElementById('rd').textContent=dt.value
    ? new Date(dt.value).toLocaleDateString(S[LG].loc,{day:'numeric',month:'long',year:'numeric'}) : '—';
  var max=CAP[cfg.value];
  var k=document.getElementById('rk');
  if(!max){ k.textContent=S[LG].adef; k.style.color='var(--prose)'; }
  else if(n>max){ k.textContent=S[LG].audela+max+S[LG].etud; k.style.color='var(--bronze-2)'; }
  else { k.textContent=n+S[LG].sur+max+S[LG].places; k.style.color='var(--palm)'; }
}
[form,cfg,nb,dt].forEach(function(e){e.addEventListener('input',recap);e.addEventListener('change',recap)});
recap();

var champs=[
  {id:'soc',test:function(v){return v.trim().length>=2}},
  {id:'nom',test:function(v){return v.trim().length>=2}},
  {id:'em', test:function(v){return /^[^\\s@]+@[^\\s@]+\\.[a-z]{2,}$/i.test(v.trim())}},
  {id:'tel',test:function(v){return v.replace(/\\D/g,'').length>=8}},
  {id:'nb', test:function(v){return +v>=1}}
];
function verifier(c,montrer){
  var el=document.getElementById(c.id),ok=c.test(el.value);
  if(montrer||el.closest('.f').classList.contains('bad'))el.closest('.f').classList.toggle('bad',!ok);
  el.setAttribute('aria-invalid',ok?'false':'true');
  return ok;
}
champs.forEach(function(c){
  var el=document.getElementById(c.id);
  el.addEventListener('blur',function(){verifier(c,true)});
  el.addEventListener('input',function(){if(el.closest('.f').classList.contains('bad'))verifier(c,true)});
});
document.getElementById('df').addEventListener('submit',function(e){
  e.preventDefault();
  var premier=null;
  champs.forEach(function(c){if(!verifier(c,true)&&!premier)premier=document.getElementById(c.id)});
  if(premier){premier.focus();premier.scrollIntoView({behavior:'smooth',block:'center'});return}

  var d={societe:document.getElementById('soc').value,nom:document.getElementById('nom').value,
         email:document.getElementById('em').value,tel:document.getElementById('tel').value,
         type:document.getElementById('typ').value,chambres:document.getElementById('nch').value,
         formule:form.value,configuration:cfg.value,participants:nb.value,date:dt.value,
         message:document.getElementById('msg').value};

  function resume(){
    return "Bonjour, je souhaite un devis pour un séminaire à l'Hôtel Evannath."+N+N
      +'Société : '+d.societe+N+'Contact : '+d.nom+N+'Téléphone : '+d.tel+N+'E-mail : '+d.email
      +N+N+"Type d'événement : "+d.type+N+'Formule : '+d.formule+N+'Configuration : '+d.configuration
      +N+'Participants : '+d.participants+(d.chambres?N+'Chambres souhaitées : '+d.chambres:'')+N+'Date souhaitée : '+d.date
      +(d.message?N+N+d.message:'');
  }
  var CH={societe:'soc',nom:'nom',email:'em',tel:'tel',participants:'nb'};

  EVN.envoyer('devis',d,{
    bouton:document.getElementById('envoi'),
    secours:document.getElementById('sec'),
    erreur:document.getElementById('err'),
    resume:resume,
    marquer:function(champs){
      champs.forEach(function(c){var el=document.getElementById(CH[c]);
        if(el){el.closest('.f').classList.add('bad');el.setAttribute('aria-invalid','true')}});
      var pr=document.getElementById(CH[champs[0]]);
      if(pr){pr.focus();pr.scrollIntoView({behavior:'smooth',block:'center'})}
    }
  },function(rep){
    document.getElementById('okm').textContent=
      S[LG].ok1+d.participants+S[LG].ok2+d.configuration+S[LG].ok3+rep.reference+S[LG].ok4;
    document.getElementById('ok').classList.add('on');
    document.getElementById('ok').scrollIntoView({behavior:'smooth',block:'center'});
  });
});

var EN={''' + EN_NAV + EN_SECOURS + '''cta:"Request a quote",
c1:"Home",c2:"Meetings &amp; groups",
eb1:"Study days · residential · receptions",
h1:"Working elsewhere,<br>and having it show",
lede:"A room bathed in natural light, an hour and three quarters from Abidjan, with the Aby lagoon behind. Your teams will remember it far longer than a hotel room in the Plateau.",
eb2:"Why here",big:"The journey is part of the seminar.",
pp1:"An hour and three quarters of road separates Abidjan from Assinie. Enough for the group to genuinely switch off, and little enough to leave in the morning and be working by ten. The airport shuttle is free if your participants arrive by air.",
pp2:"The room opens to the outside through full-length windows: nobody works in a basement here. Sound system, screen and sound engineer are included, not billed as extras at the end.",
pp3:"And at four in the afternoon, when the session is over, there is the pool, the pontoon and the pirogue. That is what turns a study day into something people talk about afterwards.",
eb3:"The room",h3:"Five layouts",
p3:"The furniture is reset to suit you, the day before or the same morning.",
cn0:"Theatre",cd0:"Chairs in rows facing the screen. For a presentation, a launch, a general meeting.",cu0:"people",
cn1:"Classroom",cd1:"Tables and chairs facing the front. For training where people take notes.",cu1:"people",
cn2:"U-shape",cd2:"Tables in a horseshoe. For a board meeting or a workshop.",cu2:"people",
cn3:"Cocktail",cd3:"Standing, high tables and buffet. For a product launch or a reception.",cu3:"people",
cn4:"Banquet",cd4:"Round tables of eight. For a gala dinner or a birthday.",cu4:"people",
capn:"Indicative capacities — the front desk confirms according to the layout chosen and the exact number of participants.",
eb4:"The packages",h4:"Four ways<br>to bring your teams together",
p4:"Each package is priced according to numbers, duration and catering. Quote within 24 h.",
ft0:"Study day",fd0:"The room for the day, the morning break, lunch in the restaurant and the afternoon break. Sound system, screen and sound engineer included.",fq0:"9 am to 6 pm · no accommodation",
ft1:"Residential seminar",fd1:"The study day, plus rooms and dinners. Our seven categories take two to six people each, and the airport shuttle is free for the whole group.",fq1:"One to three nights · accommodation included",
ft2:"Seminar &amp; lagoon",fd2:"Work in the morning, the lagoon in the afternoon: pirogue cruise, jet ski, or simply the pool. This is what sets Assinie apart from a meeting room in Abidjan.",fq2:"Two days · activities included",
ft3:"Private reception",fd3:"Cocktail, gala dinner, product launch, company anniversary. Room to yourselves, full buffet, sound system and sound engineer included from ten people.",fq3:"Evening · from 10 people",
eb5:"Included",h5:"What you will not pay extra for",
qt0:"Natural light",qd0:"Full-length windows along the whole side",
qt1:"Sound system",qd1:"Microphones, speakers, mixing desk",
qt2:"Sound engineer",qd2:"Present throughout, included",
qt3:"Screen &amp; projection",qd3:"On request, at no extra cost",
qt4:"Wifi across the estate",qd4:"Free, in the room as in the bedrooms",
qt5:"Catering on site",qd5:"Breaks, lunch, gala dinner",
qt6:"Free parking",qd6:"Guarded, on the estate",
qt7:"Airport shuttle",qd7:"Free, both ways, for the group",
eb6:"Private reception",h6:"The Birthday Package",
p6:"Our simplest package to arrange: you give a date and a number, we do the rest.",
cl0:"Room to yourselves, free of charge",
cl1:"Full buffet — starters, hot dishes, dessert",
cl2:"Drinks included",
cl3:"Sound system and sound engineer included",
cpu:"FCFA · per person",cpm:"from 10 people",
eb7:"Your project",h7:"Request a quote",
lsoc:"Company or organisation *",msoc:"Please give the name of your organisation.",
lnom:"Your name *",mnom:"Please give your name.",
lem:"E-mail *",mem:"This e-mail address does not look valid.",
ltel:"Phone *",mtel:"Please give a number of at least 8 digits.",
ltyp:"Type of event",lnch:"Rooms needed",
ty0:"Seminar or study day",ty1:"Training",ty2:"Team building",ty3:"Corporate reception",ty4:"Product launch",ty5:"Wedding",ty6:"Birthday",ty7:"Christening",ty8:"Private party",ty9:"Other",
lform:"Package",
fo0:"Study day",fo1:"Residential seminar",fo2:"Seminar &amp; lagoon",fo3:"Private reception",
fo4:"Birthday Package",fo5:"I do not know yet",
lcfg:"Room layout",
co0:"Theatre",co1:"Classroom",co2:"U-shape",co3:"Cocktail",co4:"Banquet",co5:"To be defined",
lnb:"Number of participants *",mnb:"Please give at least one participant.",
ldt:"Preferred date",lmsg:"Your project",
env:"Send the request",okt:"{{CT_EN}}",
ah3:"Your request",ar1:"Package",ar2:"Room",ar3:"Participants",ar4:"Date",ar5:"Capacity",
acall:"For an urgent project, call us directly:"};

''' + LANG_JS

LD = _schema.bloc(
    _schema.service("Séminaires, journées d'étude et réceptions",
                    "Salle de conférence en lumière naturelle, cinq configurations jusqu'à 90 personnes, sonorisation et technicien son inclus, à Assinie PK 19.",
                    'seminaires', image='g-seminaire'),
    _schema.hotel(),
    _schema.fil([('Accueil','index'),('Séminaires & groupes',None)]))

HTML = page(
 "Séminaires &amp; groupes — Hôtel Evannath, Assinie",
 "Séminaires, journées d'étude et réceptions à l'Hôtel Evannath, Assinie PK 19 : salle en lumière naturelle, cinq configurations, sonorisation et technicien inclus, navette aéroport offerte.",
 "g-seminaire", CSS, '\n'.join(b), JS, preload="g-seminaire", slug="seminaires", jsonld=LD)

# Les quatre textes de confirmation suivent ENVOI_WHATSAPP : voir _chrome.py.
for _m, _v in (('{{CT}}',    CONF_TITRE    or 'Demande envoyée'),
               ('{{CT_EN}}', CONF_TITRE_EN or 'Request sent'),
               ('{{CG}}',    CONF_GESTE    or 'Merci. '),
               ('{{CG_EN}}', CONF_GESTE_EN or 'Thank you. '),
               ('{{CV}}',    CONF_VERBE),
               ('{{CV_EN}}', CONF_VERBE_EN)):
    HTML = HTML.replace(_m, _v.replace("'", "\'"))   # contexte JS entre apostrophes

io.open('seminaires.html', 'w', encoding='utf-8').write(HTML)
print('seminaires.html       ok')
