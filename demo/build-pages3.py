# -*- coding: utf-8 -*-
"""Genere informations-utiles.html (accordeons) et mentions-legales.html."""
import io
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV

# ════════════════════════ INFORMATIONS UTILES ════════════════════════
CSS_INFO = """
.head{padding:150px 0 40px}
.head h1{margin:10px 0 18px}
.head p{max-width:60ch;font-size:1.06rem}
.quick{display:grid;grid-template-columns:repeat(6,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin-bottom:72px}
.quick div{background:var(--bark);padding:24px 18px}
.quick b{display:block;font-family:var(--f-display);font-size:1.5rem;color:var(--bronze);line-height:1;font-variant-numeric:tabular-nums}
.quick span{display:block;font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);margin-top:9px;font-weight:600;line-height:1.4}
.body{display:grid;grid-template-columns:220px 1fr;gap:56px;align-items:start;padding-bottom:100px}
.side{position:sticky;top:118px}
.side b{display:block;font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:var(--bronze);font-weight:700;margin-bottom:14px}
.side nav{display:flex;flex-direction:column}
.side a{font-size:13.5px;color:var(--muted);padding:10px 0;border-bottom:1px solid var(--line);transition:.3s}
.side a:hover,.side a.on{color:var(--cream)}
.side .tools{margin-top:26px;display:flex;flex-direction:column;gap:10px}
.side .tools button{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);background:none;border:1px solid var(--line);padding:14px;cursor:pointer;font-family:var(--f-body);font-weight:700;transition:.3s}
.side .tools button:hover{border-color:var(--bronze);color:var(--bronze)}
.sec{margin-bottom:56px;scroll-margin-top:130px}
.sec>h2{padding-bottom:16px;border-bottom:1px solid var(--line);margin-bottom:4px}
.acc{border-bottom:1px solid var(--line)}
.acc h3{margin:0}
.acc button{width:100%;text-align:left;background:none;border:0;cursor:pointer;color:var(--cream);
  font:400 1.08rem/1.4 var(--f-display);padding:22px 44px 22px 0;position:relative;transition:.3s}
.acc button:hover{color:var(--bronze-2)}
.acc button::after{content:"";position:absolute;right:6px;top:50%;width:11px;height:11px;
  border-right:1.5px solid var(--bronze);border-bottom:1.5px solid var(--bronze);
  transform:translateY(-70%) rotate(45deg);transition:.35s}
.acc.open button::after{transform:translateY(-20%) rotate(-135deg)}
.acc .in{display:grid;grid-template-rows:0fr;transition:grid-template-rows .4s cubic-bezier(.2,.8,.2,1)}
.acc.open .in{grid-template-rows:1fr}
.acc .in>div{overflow:hidden}
.acc .in p{font-size:14.5px;padding-bottom:8px}
.acc .in p:last-child{padding-bottom:24px}
.acc .in ul{list-style:none;padding-bottom:24px}
.acc .in li{font-size:14.5px;color:#CFC3B2;padding:7px 0 7px 20px;position:relative}
.acc .in li::before{content:"";position:absolute;left:0;top:15px;width:6px;height:6px;background:var(--bronze);opacity:.7}
.acc .in .kv{display:flex;justify-content:space-between;gap:18px;padding:11px 0;border-bottom:1px solid rgba(185,138,80,.1);font-size:14.5px}
.acc .in .kv:last-of-type{border-bottom:0;margin-bottom:18px}
.acc .in .kv span:first-child{color:var(--muted);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;font-weight:600}
.acc .in .hi{color:var(--palm)}
.acc .in a{color:var(--bronze);border-bottom:1px solid var(--line)}
.help{border:1px solid var(--bronze);padding:44px;text-align:center;margin-bottom:100px}
.help h2{margin-bottom:12px}
.help p{max-width:50ch;margin:0 auto 26px}
.help .g{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
@media(max-width:1080px){.quick{grid-template-columns:repeat(3,1fr)}.body{grid-template-columns:1fr;gap:0}.side{display:none}.route-grid{grid-template-columns:1fr}}
@media(max-width:720px){.head{padding:126px 0 30px}.quick{grid-template-columns:repeat(2,1fr)}.help{padding:30px}.acc .in .kv{flex-direction:column;gap:4px}}
"""

def kv(k, klab, v, vlab='', hi=False):
    cls = ' class="hi"' if hi else ''
    vv = '<span%s data-t="%s">%s</span>' % (cls, v, vlab) if vlab else '<span%s>%s</span>' % (cls, v)
    return '          <div class="kv"><span data-t="%s">%s</span>%s</div>' % (k, klab, vv)

SECS = [
 ('reserver','s1','Réserver &amp; payer', [
  ('a11','Comment réserver ?', True, [
   ('p','b11','Trois moyens, tous équivalents : directement sur ce site, par WhatsApp au +225 05 46 01 73 77, ou par téléphone au +225 01 51 52 75 75. Le tarif affiché ici est notre meilleur tarif — vous ne le trouverez pas moins cher ailleurs.'),
   ('p','b11b','Pour les circuits, les groupes et les séminaires, passez par le <a href="contact.html">formulaire de contact</a> : nous revenons vers vous avec un devis sous 24 h.')]),
  ('a12','Quels moyens de paiement acceptez-vous ?', False, [
   ('p','b12','Nous sommes flexibles, et c\'est volontaire.'),
   ('ul',[('b12a','Wave'),('b12b','Orange Money et MTN Money'),('b12c','Carte bancaire Visa et Mastercard'),
          ('b12d','Espèces, en francs CFA, à la réception'),('b12e','Virement bancaire, pour les groupes et les entreprises')])]),
  ('a13','Faut-il verser un acompte ?', False, [
   ('kv','k1','Acompte à la réservation','30 %',''),
   ('kv','k2','Solde','','k2v','à l\'arrivée'),
   ('kv','k3','Groupes dès 10 personnes','','k3v','50 % à la confirmation'),
   ('p','b13','L\'acompte confirme définitivement la chambre. Sans acompte, la réservation reste une option, et la chambre peut être attribuée à un autre client.')]),
  ('a14','Puis-je annuler ou modifier ?', False, [
   ('kvh','k4','Plus de 48 h avant','','k4v','gratuit, remboursement intégral'),
   ('kv','k5','Moins de 48 h avant','','k5v','acompte conservé'),
   ('kv','k6','Non-présentation','','k6v','première nuit facturée'),
   ('p','b14','Un décalage de dates est toujours possible sans frais, sous réserve de disponibilité. Appelez-nous, nous trouverons une solution.')]),
 ]),
 ('venir','s2','Venir jusqu\'à nous', [
  ('a21','La navette aéroport est-elle vraiment gratuite ?', False, [
   ('p','b21','Oui, à l\'aller comme au retour, et sans supplément. Il suffit de nous donner votre numéro de vol et votre heure d\'arrivée au moment de la réservation, ou au plus tard 24 h avant.'),
   ('p','b21b','L\'aéroport Félix-Houphouët-Boigny est à environ 80 km. Comptez un peu moins de deux heures de route.')]),
  ('a22','Comment venir en voiture depuis Abidjan ?', False, [
   ('kv','k7','Distance','≈ 85 km',''),
   ('kv','k8','Durée','','k8v','1 h 45 environ'),
   ('kv','k9','Adresse','Assinie, PK 19',''),
   ('p','b22','Prenez la route côtière en direction d\'Assinie-Mafia. Nous sommes au point kilométrique 19. Le parking est gratuit, sur le domaine, et surveillé.'),
   ('p','b22b','<a href="https://www.google.com/maps/dir/?api=1&destination=Assinie-Mafia" target="_blank" rel="noopener">Lancer l\'itinéraire dans Maps</a>')]),
  ('a23','Peut-on arriver par la lagune ?', False, [
   ('p','b23','Oui. L\'hôtel a son propre ponton sur la lagune Aby, et une arrivée en pirogue prend une quinzaine de minutes depuis l\'embarcadère. C\'est la plus belle façon d\'arriver, surtout en fin de journée — mais elle se prépare : prévenez la réception au moins la veille.')]),
 ]),
 ('sejour','s3','Pendant le séjour', [
  ('a31','Arrivée, départ, et si mon vol est décalé ?', False, [
   ('kv','k10','Arrivée','','k10v','à partir de 14 h 00'),
   ('kv','k11','Départ','','k11v','avant 12 h 00'),
   ('kvh','k12','Réception','','k12v','ouverte 24 h/24'),
   ('p','b31','Arrivée tardive, départ matinal, vol décalé : la réception ne ferme jamais, quelqu\'un vous attendra. Prévenez-nous simplement, et nous gardons vos bagages sans frais avant l\'arrivée comme après le départ.')]),
  ('a32','Quels sont les horaires sur le domaine ?', False, [
   ('kv','k13','Petit-déjeuner','6 h 30 — 10 h 30',''),
   ('kv','k14','Déjeuner','12 h 00 — 15 h 00',''),
   ('kv','k15','Dîner','19 h 00 — 22 h 30',''),
   ('kv','k16','Piscine &amp; jacuzzi','','k16v','du lever du jour à la nuit'),
   ('kv','k17','Spa &amp; sauna','','k17v','sur rendez-vous'),
   ('kv','k18','Night-club','','k18v','week-ends'),
   ('kvh','k19','Méchoui Party','','k19v','samedi, dès 15 h')]),
  ('a33','Wifi, parking, blanchisserie ?', False, [
   ('ul',[('b33a','Wifi gratuit dans les chambres et les espaces communs'),
          ('b33b','Parking gratuit et surveillé sur le domaine'),
          ('b33c','Pressing et blanchisserie, service payant à la réception'),
          ('b33d','Boutique souvenir, artisanat local'),
          ('b33e','Salle de sport en accès libre'),
          ('b33f','Ascenseurs desservant tous les étages')])]),
 ]),
 ('familles','s4','Familles &amp; enfants', [
  ('a41','Que faire avec des enfants ?', False, [
   ('p','b41','Le Pack Enfant et le circuit Découvertes Junior sont pensés pour eux : maquillage, accès aux jeux, atelier cuisine, atelier peinture, conte en bordure d\'eau le soir, et les soins « princes &amp; princesses ».'),
   ('p','b41b','<a href="circuits.html">Voir les offres familles</a>')]),
  ('a42','Quelles chambres pour une famille ?', False, [
   ('kv','k20','Deluxe Supérieure','','k20v','jusqu\'à 3 personnes'),
   ('kv','k21','Mezzanine Supérieure','','k21v','jusqu\'à 4 personnes'),
   ('kv','k22','Suite Arabe','','k22v','2 chambres, jusqu\'à 6 personnes'),
   ('p','b42','Lit d\'appoint et lit bébé disponibles sur demande, à préciser à la réservation.')]),
 ]),
 ('groupes','s5','Groupes &amp; séminaires', [
  ('a51','Organiser un séminaire ou un événement', False, [
   ('p','b51','Notre salle de conférence, baignée de lumière naturelle, accueille séminaires, cocktails, dîners de gala et lancements de produits. Sonorisation et technicien son sont disponibles.'),
   ('p','b51b','Formules journée d\'étude ou résidentielles, avec hébergement et restauration. Devis sous 24 h.'),
   ('p','b51c','<a href="contact.html">Demander un devis</a>')]),
  ('a52','Anniversaires et réceptions privées', False, [
   ('p','b52','Le Coffret Anniversaire s\'applique à partir de 10 personnes : salle offerte, buffet complet — entrées, plats chauds, dessert — boissons comprises, sonorisation et technicien son inclus.'),
   ('p','b52b','<a href="circuits.html">Voir le coffret</a>')]),
 ]),
 ('savoir','s6','Bon à savoir', [
  ('a61','Quand venir à Assinie ?', False, [
   ('kv','k23','Décembre — mars','','k23v','saison sèche, la plus demandée'),
   ('kv','k24','Avril — juin','','k24v','saison des pluies, tarifs plus doux'),
   ('kv','k25','Juillet — novembre','','k25v','alternance, très agréable'),
   ('p','b61','De décembre à mars, les suites partent plusieurs semaines à l\'avance. Réservez tôt, surtout pour les week-ends et les fêtes.')]),
  ('a62','Que mettre dans sa valise ?', False, [
   ('ul',[('b62a','Maillot de bain — piscine, lagune et plage'),('b62b','Crème solaire et chapeau'),
          ('b62c','Anti-moustiques, surtout en soirée'),('b62d','Une tenue légère pour les dîners'),
          ('b62e','Des espèces en francs CFA pour les excursions')]),
   ('p','b62','Serviettes de piscine, sèche-cheveux et produits d\'accueil sont fournis dans toutes les chambres.')]),
  ('a63','Langues, animaux, fumeurs', False, [
   ('kv','k26','Langues parlées','','k26v','français, anglais'),
   ('kv','k27','Animaux','','k27v','non admis'),
   ('kv','k28','Chambres','','k28v','non-fumeur'),
   ('kv','k29','Terrasses et extérieurs','','k29v','fumeurs autorisés'),
   ('kv','k30','Monnaie','','k30v','franc CFA (XOF)')]),
 ]),
]

b = [header('index.html#reserver','Réserver'), drawer('informations-utiles.html'), '''
<div class="wrap head">
  <nav class="crumb" aria-label="Fil d'Ariane">
    <a href="index.html" data-t="c1">Accueil</a> &nbsp;·&nbsp; <span data-t="c2">Informations utiles</span>
  </nav>
  <span class="eyebrow" data-t="eb">Avant, pendant et après votre séjour</span>
  <h1 data-t="h1">Informations utiles</h1>
  <p data-t="lede">Les réponses aux questions qu'on nous pose le plus souvent. Si la vôtre n'y est pas, la réception répond 24 h/24 — et WhatsApp reste le plus rapide.</p>
</div>

<div class="wrap">
  <div class="quick">
    <div><b>14 h</b><span data-t="q1">Arrivée</span></div>
    <div><b>12 h</b><span data-t="q2">Départ</span></div>
    <div><b>48 h</b><span data-t="q3">Annulation gratuite</span></div>
    <div><b>30 %</b><span data-t="q4">Acompte</span></div>
    <div><b data-t="q5v">Offerte</b><span data-t="q5">Navette aéroport</span></div>
    <div><b>24 h/24</b><span data-t="q6">Réception</span></div>
  </div>
</div>

<div class="wrap body">
  <aside class="side">
    <b data-t="sm">Sur cette page</b>
    <nav id="toc">''']

for i, (sid, skey, slab, _) in enumerate(SECS, 1):
    b.append('      <a href="#%s" data-t="i%d">%s</a>' % (sid, i, slab))

b.append('''    </nav>
    <div class="tools">
      <button id="all" data-t="ta">Tout déplier</button>
      <button onclick="window.print()" data-t="tp">Imprimer la page</button>
    </div>
  </aside>

  <div id="content">''')

for sid, skey, slab, accs in SECS:
    b.append('    <section class="sec" id="%s">\n      <h2 data-t="%s">%s</h2>' % (sid, skey, slab))
    for akey, alab, opened, rows in accs:
        oc = ' open' if opened else ''
        ae = 'true' if opened else 'false'
        b.append('      <div class="acc%s"><h3><button type="button" aria-expanded="%s" data-t="%s">%s</button></h3>\n        <div class="in"><div>' % (oc, ae, akey, alab))
        for r in rows:
            if r[0] == 'p':
                b.append('          <p data-t="%s">%s</p>' % (r[1], r[2]))
            elif r[0] == 'ul':
                b.append('          <ul>')
                for k, t in r[1]:
                    b.append('            <li data-t="%s">%s</li>' % (k, t))
                b.append('          </ul>')
            elif r[0] in ('kv', 'kvh'):
                hi = (r[0] == 'kvh')
                if len(r) == 6:
                    b.append(kv(r[1], r[2], r[4], r[5], hi))
                else:
                    b.append(kv(r[1], r[2], r[3], '', hi))
        b.append('        </div></div>\n      </div>')
    b.append('    </section>')

b.append('''  </div>
</div>

<div class="wrap">
  <div class="help">
    <span class="eyebrow" data-t="e9">Une question sans réponse ici ?</span>
    <h2 data-t="h9">Écrivez-nous, on répond vite</h2>
    <p data-t="p9">La réception est ouverte 24 h/24. Pour une réponse immédiate, WhatsApp reste le canal le plus rapide.</p>
    <div class="g">
      <a href="https://wa.me/2250546017377" target="_blank" rel="noopener" class="btn btn-solid" data-t="g1">Écrire sur WhatsApp</a>
      <a href="contact.html" class="btn" data-t="g2">Formulaire de contact</a>
    </div>
  </div>
</div>

''' + FOOTER)

JS_INFO = NAV_JS + '''

// accordéons
var accs=[].slice.call(document.querySelectorAll('.acc'));
accs.forEach(function(a,i){
  var btn=a.querySelector('button'), pane=a.querySelector('.in'), id='q'+(i+1);
  pane.id=id; btn.setAttribute('aria-controls',id); pane.setAttribute('role','region');
  btn.addEventListener('click',function(){
    var open=a.classList.toggle('open');
    btn.setAttribute('aria-expanded',open);
  });
});
function openAll(v){accs.forEach(function(a){a.classList.toggle('open',v);a.querySelector('button').setAttribute('aria-expanded',v)})}
var allBtn=document.getElementById('all'),allOpen=false;
allBtn.onclick=function(){allOpen=!allOpen;openAll(allOpen);
  allBtn.textContent=allOpen?(document.documentElement.lang==='en'?'Collapse all':'Tout replier')
                            :(document.documentElement.lang==='en'?'Expand all':'Tout déplier')};
addEventListener('beforeprint',function(){openAll(true)});

// sommaire : la rubrique en cours de lecture est mise en avant
var secs=[].slice.call(document.querySelectorAll('.sec')),links=[].slice.call(document.querySelectorAll('#toc a'));
if('IntersectionObserver' in window){
  var so=new IntersectionObserver(function(es){
    es.forEach(function(e){
      if(!e.isIntersecting)return;
      links.forEach(function(l){l.classList.toggle('on',l.getAttribute('href')==='#'+e.target.id)});
    });
  },{rootMargin:'-120px 0px -70% 0px'});
  secs.forEach(function(s){so.observe(s)});
}

var EN={''' + EN_NAV + '''cta:"Book now",
c1:"Home",c2:"Useful information",eb:"Before, during and after your stay",h1:"Useful information",
lede:"Answers to the questions we are asked most. If yours is not here, the front desk answers 24/7 — and WhatsApp is fastest.",
q1:"Check-in",q2:"Check-out",q3:"Free cancellation",q4:"Deposit",q5:"Airport shuttle",q5v:"Free",q6:"Front desk",
sm:"On this page",i1:"Booking &amp; payment",i2:"Getting here",i3:"During your stay",i4:"Families &amp; children",
i5:"Groups &amp; seminars",i6:"Good to know",ta:"Expand all",tp:"Print this page",
s1:"Booking &amp; payment",a11:"How do I book?",
b11:"Three ways, all equivalent: directly on this site, on WhatsApp at +225 05 46 01 73 77, or by phone at +225 01 51 52 75 75. The rate shown here is our best rate — you will not find it cheaper elsewhere.",
b11b:"For packages, groups and seminars, use the <a href=\\"contact.html\\">contact form</a>: we come back to you with a quote within 24 h.",
a12:"Which payment methods do you accept?",b12:"We are flexible, and that is deliberate.",
b12a:"Wave",b12b:"Orange Money and MTN Money",b12c:"Visa and Mastercard",b12d:"Cash, in CFA francs, at the front desk",b12e:"Bank transfer, for groups and companies",
a13:"Is a deposit required?",k1:"Deposit on booking",k2:"Balance",k2v:"on arrival",k3:"Groups from 10 guests",k3v:"50 % on confirmation",
b13:"The deposit confirms the room for good. Without it, the booking stays an option and the room may go to another guest.",
a14:"Can I cancel or change my booking?",
k4:"More than 48 h before",k4v:"free, full refund",k5:"Less than 48 h before",k5v:"deposit retained",k6:"No-show",k6v:"first night charged",
b14:"Moving your dates is always possible at no charge, subject to availability. Call us and we will find a solution.",
s2:"Getting here",a21:"Is the airport shuttle really free?",
b21:"Yes, both ways, with no surcharge. Just give us your flight number and arrival time when booking, or at the latest 24 h before.",
b21b:"Félix-Houphouët-Boigny airport is around 80 km away. Allow a little under two hours by road.",
a22:"How do I drive from Abidjan?",k7:"Distance",k8:"Journey",k8v:"about 1 h 45",k9:"Address",
b22:"Take the coast road towards Assinie-Mafia. We are at kilometre point 19. Parking is free, on site, and guarded.",
b22b:"<a href=\\"https://www.google.com/maps/dir/?api=1&destination=Assinie-Mafia\\" target=\\"_blank\\" rel=\\"noopener\\">Open directions in Maps</a>",
a23:"Can I arrive by the lagoon?",
b23:"Yes. The hotel has its own pontoon on the Aby lagoon, and arriving by pirogue takes about fifteen minutes from the landing. It is the finest way to arrive, especially late in the day — but it needs preparation: tell the front desk at least a day ahead.",
s3:"During your stay",a31:"Check-in, check-out, and if my flight shifts?",
k10:"Check-in",k10v:"from 2 pm",k11:"Check-out",k11v:"before noon",k12:"Front desk",k12v:"open 24/7",
b31:"Late arrival, early departure, delayed flight: the front desk never closes, someone will be waiting. Just let us know, and we store your luggage free of charge before check-in and after check-out.",
a32:"What are the opening hours on site?",
k13:"Breakfast",k14:"Lunch",k15:"Dinner",k16:"Pool &amp; jacuzzi",k16v:"first light until dark",
k17:"Spa &amp; sauna",k17v:"by appointment",k18:"Night club",k18v:"weekends",k19:"Méchoui Party",k19v:"Saturday, from 3 pm",
a33:"Wifi, parking, laundry?",
b33a:"Free wifi in the rooms and common areas",b33b:"Free guarded parking on site",b33c:"Dry cleaning and laundry, paid service at the front desk",
b33d:"Gift shop, local craftwork",b33e:"Gym, open access",b33f:"Lifts to every floor",
s4:"Families &amp; children",a41:"What is there for children?",
b41:"The Kids Pack and the Junior Discovery tour are built for them: face painting, play area, cooking workshop, painting workshop, waterside storytelling at dusk, and the little prince &amp; princess treatments.",
b41b:"<a href=\\"circuits.html\\">See the family offers</a>",
a42:"Which rooms suit a family?",k20:"Deluxe Superior",k20v:"up to 3 guests",k21:"Superior Mezzanine",k21v:"up to 4 guests",
k22:"Arabian Suite",k22v:"2 bedrooms, up to 6 guests",b42:"Extra bed and cot available on request — mention it when booking.",
s5:"Groups &amp; seminars",a51:"Organising a seminar or an event",
b51:"Our conference room, bathed in natural light, hosts seminars, cocktails, gala dinners and product launches. PA system and sound engineer available.",
b51b:"Day-study or residential packages, with accommodation and catering. Quote within 24 h.",
b51c:"<a href=\\"contact.html\\">Request a quote</a>",
a52:"Birthdays and private receptions",
b52:"The Birthday Box applies from 10 guests: room free of charge, full buffet — starters, mains, dessert — drinks included, PA system and sound engineer included.",
b52b:"<a href=\\"circuits.html\\">See the box</a>",
s6:"Good to know",a61:"When should I come to Assinie?",
k23:"December — March",k23v:"dry season, most in demand",k24:"April — June",k24v:"rainy season, softer rates",
k25:"July — November",k25v:"mixed, very pleasant",
b61:"From December to March the suites go weeks ahead. Book early, especially for weekends and holidays.",
a62:"What should I pack?",
b62a:"Swimwear — pool, lagoon and beach",b62b:"Sun cream and a hat",b62c:"Insect repellent, especially in the evening",
b62d:"Something light for dinner",b62e:"Some cash in CFA francs for excursions",
b62:"Pool towels, hairdryer and toiletries are provided in every room.",
a63:"Languages, pets, smoking",k26:"Languages spoken",k26v:"French, English",k27:"Pets",k27v:"not allowed",
k28:"Rooms",k28v:"non-smoking",k29:"Terraces and outdoors",k29v:"smoking allowed",k30:"Currency",k30v:"CFA franc (XOF)",
e9:"A question we have not answered?",h9:"Write to us, we reply fast",
p9:"The front desk is open 24/7. For an immediate answer, WhatsApp is the quickest channel.",
g1:"Message on WhatsApp",g2:"Contact form"};

''' + LANG_JS + '''
document.querySelectorAll('.lang button').forEach(function(b){var prev=b.onclick;b.onclick=function(){
  prev.call(b);
  allBtn.textContent=allOpen?(document.documentElement.lang==='en'?'Collapse all':'Tout replier')
                            :(document.documentElement.lang==='en'?'Expand all':'Tout déplier');
}});'''

io.open('informations-utiles.html','w',encoding='utf-8').write(page(
 "Informations utiles — Hôtel Evannath, Assinie",
 "Tout ce qu'il faut savoir avant de venir à l'Hôtel Evannath, Assinie PK 19 : arrivée et départ, paiement, annulation, navette aéroport gratuite, accès depuis Abidjan, familles et groupes.",
 "g-lobby", CSS_INFO, '\n'.join(b), JS_INFO))
print('informations-utiles.html  ok')
