# -*- coding: utf-8 -*-
"""Genere mentions-legales.html."""
import io
from _chrome import PROSPECTION
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV

CSS = """
.head{padding:150px 0 34px}
.head h1{margin:10px 0 16px;font-size:clamp(2.2rem,4.6vw,3.2rem)}
.head .maj{font-size:13px;color:var(--muted);letter-spacing:.04em}
.head .maj b{color:var(--cream);font-weight:600}
.body{display:grid;grid-template-columns:240px 1fr;gap:64px;align-items:start;padding-bottom:96px}
.side{position:sticky;top:118px}
.side b{display:block;font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:var(--bronze);font-weight:700;margin-bottom:14px}
.side nav{display:flex;flex-direction:column;counter-reset:s}
.side a{font-size:13px;color:var(--muted);padding:9px 0;border-bottom:1px solid var(--line);transition:.3s;counter-increment:s;display:flex;gap:11px}
.side a::before{content:counter(s,decimal-leading-zero);color:var(--bronze);opacity:.55;font-variant-numeric:tabular-nums;flex:0 0 auto}
.side a:hover,.side a.on{color:var(--cream)}
.side a.on::before{opacity:1}
article{max-width:74ch;counter-reset:art}
article section{margin-bottom:52px;scroll-margin-top:120px;counter-increment:art}
article h2{padding-bottom:14px;border-bottom:1px solid var(--line);margin-bottom:20px;display:flex;gap:16px;align-items:baseline;font-size:1.55rem}
article h2::before{content:counter(art,decimal-leading-zero);font-size:.62em;color:var(--bronze);font-family:var(--f-body);font-weight:700;letter-spacing:.08em;flex:0 0 auto}
article h3{margin:26px 0 10px;color:var(--bronze-2);font-size:1.08rem}
article p{font-size:15.5px;margin-bottom:14px}
article ul{margin:0 0 16px}
article li{list-style:none;font-size:15px;color:#CFC3B2;padding:6px 0 6px 20px;position:relative}
article li::before{content:"";position:absolute;left:0;top:15px;width:6px;height:6px;background:var(--bronze);opacity:.65}
article a{color:var(--bronze);border-bottom:1px solid var(--line)}
article a:hover{border-color:var(--bronze)}
.kv{display:flex;justify-content:space-between;gap:20px;padding:13px 0;border-bottom:1px solid rgba(185,138,80,.12);font-size:15px}
.kv:last-of-type{border-bottom:0}
.kv>span:first-child{color:var(--muted);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;font-weight:600;flex:0 0 42%}
.kv>span:last-child{text-align:right}
.todo{display:inline-block;border:1px dashed rgba(185,138,80,.6);color:var(--bronze-2);padding:2px 10px;font-size:13.5px;font-style:italic;background:rgba(185,138,80,.06)}
.warn{border:1px solid var(--bronze);background:rgba(185,138,80,.07);padding:26px 28px;margin-bottom:52px}
.warn b{display:block;font-family:var(--f-display);font-size:1.22rem;color:var(--bronze-2);margin-bottom:8px}
.warn p{font-size:14.5px;margin:0}
.cook{border:1px solid var(--line);margin:8px 0 20px}
.cook div{display:grid;grid-template-columns:1.1fr 2fr 90px;gap:18px;padding:14px 20px;border-bottom:1px solid var(--line);font-size:14px;align-items:center}
.cook div:last-child{border-bottom:0}
.cook div.h{background:var(--bark-2);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:700}
.cook b{font-weight:600;color:var(--cream)}
.cook span:last-child{color:var(--muted);text-align:right;font-variant-numeric:tabular-nums}
@media(max-width:1080px){.body{grid-template-columns:1fr;gap:0}.side{display:none}}
@media(max-width:720px){.head{padding:126px 0 26px}.kv{flex-direction:column;gap:4px}.kv>span:last-child{text-align:left}
 .cook div{grid-template-columns:1fr;gap:6px}.cook span:last-child{text-align:left}.cook div.h{display:none}}
"""

# Les cles du sommaire etaient n1..n9 — exactement celles du menu principal,
# definies par EN_NAV. Le dictionnaire anglais les redefinissait juste apres :
# en anglais, le menu affichait donc « Site publisher », « Hosting »,
# « Cookies » a la place des chambres, du spa et de la galerie.
# Prefixees sm*, plus de collision possible.
NAV_ITEMS = [('editeur','sm1','Éditeur du site'),('hebergeur','sm2','Hébergement'),
 ('propriete','sm3','Propriété intellectuelle'),('donnees','sm4','Données personnelles'),
 ('cookies','sm5','Cookies'),('reservation','sm6','Réservation et paiement'),
 ('responsabilite','sm7','Responsabilité'),('droit','sm8','Droit applicable'),('credits','sm9','Crédits')]

def kv(k, lab, val, todo=False):
    v = '<span class="todo">%s</span>' % val if todo else val
    return '      <div class="kv"><span data-t="%s">%s</span><span>%s</span></div>' % (k, lab, v)

b = [header('index.html#reserver','Réserver'), drawer(''), '''
<div class="wrap head">
  <nav class="crumb" aria-label="Fil d'Ariane">
    <a href="index.html" data-t="c1">Accueil</a> &nbsp;·&nbsp; <span data-t="c2">Mentions légales</span>
  </nav>
  <span class="eyebrow" data-t="eb">Informations juridiques</span>
  <h1 data-t="h1">Mentions légales &amp;<br>protection des données</h1>
  <p class="maj" data-t="maj">Dernière mise à jour : <b>21 août 2026</b> · La version française de ce document fait foi.</p>
</div>

<div class="wrap body">
  <aside class="side">
    <b data-t="sm">Sommaire</b>
    <nav id="toc">''']

for sid, key, lab in NAV_ITEMS:
    b.append('      <a href="#%s" data-t="%s">%s</a>' % (sid, key, lab))

b.append('''    </nav>
  </aside>

  <article>

    <div class="warn">
      <b data-t="wt">Document à compléter et à faire valider</b>
      <p data-t="wp">Les champs encadrés en pointillés doivent être renseignés par la direction de l'établissement à partir des documents officiels (RCCM, statuts, contrat d'hébergement). Ce document est une trame : il doit être relu et validé par un conseil juridique avant mise en ligne.</p>
    </div>

    <section id="editeur">
      <h2 data-t="t1">Éditeur du site</h2>
      <p data-t="p1">Le site <strong>evannathhotel.com</strong> est édité par :</p>''')

b += [
 kv('e1','Raison sociale','Dénomination exacte de la société',True),
 kv('e2','Forme juridique','SA, SARL, SAS…',True),
 kv('e3','Capital social','Montant en francs CFA',True),
 kv('e4','RCCM','Numéro d\'immatriculation',True),
 kv('e5','Compte contribuable','Numéro',True),
 kv('e6','Siège social','Assinie PK 19, Comoé, Côte d\'Ivoire'),
 kv('e7','Téléphone','+225 27 21 73 12 65'),
 kv('e8','E-mail','<a href="mailto:{{MAIL}}">{{MAIL}}</a>'),
 kv('e9','Directeur de la publication','Nom et qualité',True),
 '    </section>',
 '',
 '    <section id="hebergeur">',
 '      <h2 data-t="t2">Hébergement du site</h2>',
 '      <p data-t="p2">Le site est hébergé par :</p>',
 kv('h1l','Hébergeur','Nom de la société',True),
 kv('h2l','Adresse','Adresse complète',True),
 kv('h3l','Contact','Téléphone ou e-mail',True),
 kv('h4l','Localisation des serveurs','Pays',True),
 '    </section>',
]

b.append('''
    <section id="propriete">
      <h2 data-t="t3">Propriété intellectuelle</h2>
      <p data-t="p3a">L'ensemble des éléments composant ce site — textes, photographies, illustrations, logo, charte graphique, arborescence et code source — est la propriété exclusive de l'Hôtel Evannath ou de ses ayants droit, et est protégé par les dispositions relatives au droit d'auteur.</p>
      <p data-t="p3b">Toute reproduction, représentation, adaptation ou exploitation, totale ou partielle, sur quelque support que ce soit, est interdite sans autorisation écrite préalable. Le nom « Evannath », le logo et la signature « Le Rêve Africain » sont des signes distinctifs de l'établissement.</p>
      <p data-t="p3c">Les demandes d'utilisation à des fins de presse ou de partenariat peuvent être adressées à <a href="mailto:{{MAIL}}">{{MAIL}}</a>.</p>
    </section>

    <section id="donnees">
      <h2 data-t="t4">Données personnelles</h2>
      <h3 data-t="d0">Ce que nous collectons, et pourquoi</h3>
      <p data-t="p4a">Nous ne collectons que les données nécessaires au traitement de votre demande. Aucune donnée n'est vendue, louée ou transmise à des tiers à des fins commerciales.</p>''')

b += [
 kv('d1','Formulaire de contact','nom, e-mail, téléphone, message'),
 kv('d2','Réservation','identité, coordonnées, dates et détails du séjour'),
 kv('d3','Paiement','traité par le prestataire, jamais stocké par nos soins'),
 kv('d4','Mesure d\'audience','données de navigation, sous forme agrégée'),
 '      <h3 data-t="d5">Combien de temps nous les conservons</h3>',
 kv('d6','Demandes de contact','à définir — usage : 12 mois',True),
 kv('d7','Dossiers de réservation','à définir — obligation comptable',True),
 kv('d8','Mesure d\'audience','13 mois maximum'),
]

b.append('''      <h3 data-t="d9">Vos droits</h3>
      <p data-t="p4b">Conformément à la loi ivoirienne n° 2013-450 du 19 juin 2013 relative à la protection des données à caractère personnel, vous disposez d'un droit d'accès, de rectification, d'opposition et de suppression des données vous concernant.</p>
      <p data-t="p4c">Pour l'exercer, écrivez à <a href="mailto:{{MAIL}}">{{MAIL}}</a> en précisant votre demande. Une réponse vous sera apportée dans un délai de trente jours.</p>
      <p data-t="p4d">Si vous estimez que vos droits ne sont pas respectés, vous pouvez saisir l'Autorité de Régulation des Télécommunications de Côte d'Ivoire (ARTCI), autorité compétente en matière de protection des données personnelles.</p>''')

b += [
 kv('d10','Déclaration ARTCI','Numéro de déclaration du traitement',True),
 kv('d11','Responsable des données','Nom et contact',True),
]

b.append('''      <p data-t="p4e">Les visiteurs résidant dans l'Union européenne bénéficient en outre des droits prévus par le Règlement général sur la protection des données, dont la portabilité et la limitation du traitement.</p>
    </section>

    <section id="cookies">
      <h2 data-t="t5">Cookies</h2>
      <p data-t="p5a">Un cookie est un petit fichier déposé sur votre appareil lors de la visite d'un site. Nous n'utilisons que les cookies décrits ci-dessous, et les cookies de mesure d'audience ne sont déposés qu'après votre accord.</p>
      <div class="cook">
        <div class="h"><span data-t="ch1">Cookie</span><span data-t="ch2">Finalité</span><span data-t="ch3">Durée</span></div>
        <div><b>evn_session</b><span data-t="ck1">Maintien de votre sélection pendant la réservation</span><span data-t="ck1d">session</span></div>
        <div><b>evn_lang</b><span data-t="ck2">Mémorisation de la langue choisie, français ou anglais</span><span>6 <span data-t="mois">mois</span></span></div>
        <div><b>evn_consent</b><span data-t="ck3">Mémorisation de votre choix concernant les cookies</span><span>6 <span data-t="mois">mois</span></span></div>
        <div><b>_ga</b><span data-t="ck4">Mesure d'audience anonymisée — déposé après consentement</span><span>13 <span data-t="mois">mois</span></span></div>
      </div>
      <p data-t="p5b">Vous pouvez à tout moment modifier votre choix, ou supprimer les cookies déjà déposés depuis les réglages de votre navigateur. Le refus des cookies de mesure d'audience n'empêche en rien la réservation.</p>
    </section>

    <section id="reservation">
      <h2 data-t="t6">Réservation et paiement</h2>
      <p data-t="p6a">Les conditions de réservation, d'acompte et d'annulation sont détaillées sur la page <a href="informations-utiles.html#reserver">Informations utiles</a>. Elles font partie intégrante du contrat conclu au moment de la confirmation.</p>
      <p data-t="p6b">Les tarifs sont indiqués en francs CFA (XOF), toutes taxes comprises sauf mention contraire. Ils s'entendent par nuit et par chambre pour l'hébergement, et par personne ou par forfait pour les circuits, selon ce qui est précisé.</p>
      <p data-t="p6c">Les paiements en ligne sont traités par un prestataire agréé. Les données bancaires transitent de manière chiffrée et ne sont à aucun moment conservées sur nos serveurs.</p>''')

b += [
 kv('r1','Prestataire de paiement','Nom et agrément',True),
 kv('r2','Moyens acceptés','Wave, Orange Money, MTN Money, Visa, Mastercard'),
 '    </section>',
]

b.append('''
    <section id="responsabilite">
      <h2 data-t="t7">Responsabilité et liens externes</h2>
      <p data-t="p7a">L'Hôtel Evannath apporte le plus grand soin à l'exactitude des informations publiées sur ce site. Des erreurs ou omissions peuvent néanmoins subsister ; les informations sont fournies à titre indicatif et peuvent évoluer sans préavis. Seule la confirmation écrite de réservation engage l'établissement.</p>
      <p data-t="p7b">Ce site contient des liens vers des sites tiers — cartographie, réseaux sociaux, messagerie. L'Hôtel Evannath n'exerce aucun contrôle sur leur contenu ni sur leurs pratiques en matière de données, et ne saurait en être tenu responsable.</p>
      <p data-t="p7c">L'établissement met en œuvre les moyens raisonnables pour assurer la disponibilité du site, sans garantir un accès ininterrompu.</p>
    </section>

    <section id="droit">
      <h2 data-t="t8">Droit applicable et litiges</h2>
      <p data-t="p8a">Le présent site et les prestations qui y sont proposées sont régis par le droit ivoirien.</p>
      <p data-t="p8b">En cas de différend, les parties s'engagent à rechercher une solution amiable avant toute action contentieuse. À défaut d'accord, le litige sera porté devant les juridictions compétentes de Côte d'Ivoire.</p>''')

b += [
 kv('j1','Juridiction compétente','Tribunal à préciser',True),
 '    </section>',
 '',
 '    <section id="credits">',
 '      <h2 data-t="t9">Crédits</h2>',
 kv('cr1','Photographies','Nom du ou des photographes',True),
 kv('cr2','Conception et développement','Prestataire',True),
 kv('cr3','Typographies','Marcellus, Karla — SIL Open Font License'),
 '      <p style="margin-top:20px" data-t="p9">Toute remarque sur le contenu de cette page peut être adressée à <a href="mailto:{{MAIL}}">{{MAIL}}</a>.</p>',
 '    </section>',
 '',
 '  </article>',
 '</div>',
 '',
 FOOTER,
]

JS = NAV_JS + '''

var secs=[].slice.call(document.querySelectorAll('article section')),links=[].slice.call(document.querySelectorAll('#toc a'));
if('IntersectionObserver' in window){
  var so=new IntersectionObserver(function(es){
    es.forEach(function(e){
      if(!e.isIntersecting)return;
      links.forEach(function(l){l.classList.toggle('on',l.getAttribute('href')==='#'+e.target.id)});
    });
  },{rootMargin:'-110px 0px -72% 0px'});
  secs.forEach(function(s){so.observe(s)});
}

// La navigation est bilingue ; le corps juridique reste en français, qui fait foi.
// Traduire un document juridique cree un second texte non relu par un conseil,
// et une ambiguite sur celui qui prevaut. Le bandeau « maj » le dit au lecteur.
// Marqueur lu par verifier.py, qui n'exige alors pas de traduction du corps :
// EVN_FR_FAIT_FOI
var EN={''' + EN_NAV + '''cta:"Book now",
c1:"Home",c2:"Legal notice",eb:"Legal information",h1:"Legal notice &amp;<br>data protection",
maj:"Last updated: <b>21 August 2026</b> · The French version of this document is the authoritative one.",
sm:"Contents",sm1:"Site publisher",sm2:"Hosting",sm3:"Intellectual property",sm4:"Personal data",sm5:"Cookies",
sm6:"Booking and payment",sm7:"Liability",sm8:"Applicable law",sm9:"Credits"};

''' + LANG_JS

io.open('mentions-legales.html','w',encoding='utf-8').write(page(
 "Mentions légales — Hôtel Evannath, Assinie",
 "Mentions légales, politique de confidentialité et gestion des cookies du site de l'Hôtel Evannath, Assinie PK 19, Côte d'Ivoire.",
 "g-lobby", CSS, '\n'.join(b), JS, slug="mentions-legales").replace('<meta property="og:image"', (('' if PROSPECTION else '<meta name="robots" content="noindex, follow">\n') + '<meta property="og:image"')))
print('mentions-legales.html ok')
