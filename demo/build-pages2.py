# -*- coding: utf-8 -*-
"""Genere contact.html et informations-utiles.html."""
import io
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV

# ═══════════════════════════════ CONTACT ═══════════════════════════════
CSS_CONTACT = """
.head{padding:150px 0 40px}
.head h1{margin:10px 0 18px}
.head p{max-width:58ch;font-size:1.08rem}
.chan{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin-bottom:76px}
.chan a{background:var(--bark);padding:30px 24px;display:block;transition:.35s}
.chan a:hover{background:var(--bark-2)}
.chan svg{width:22px;height:22px;stroke:var(--bronze);fill:none;stroke-width:1.4;margin-bottom:16px}
.chan b{display:block;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);font-weight:700;margin-bottom:8px}
.chan span{display:block;font-family:var(--f-display);font-size:1.22rem;color:var(--cream);line-height:1.25;word-break:break-word}
.chan em{display:block;font-style:normal;font-size:12.5px;color:var(--muted);margin-top:8px}
.grid{display:grid;grid-template-columns:1fr 400px;gap:56px;align-items:start;padding-bottom:88px}
.form{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.form .f{display:flex;flex-direction:column}
.form .f.full{grid-column:1/-1}
.form label{font-size:9.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--bronze);margin-bottom:7px;font-weight:700}
.form label .req{color:var(--muted)}
.form input,.form select,.form textarea{min-height:48px;background:transparent;border:1px solid var(--line);color:var(--cream);font:400 15px/1.5 var(--f-body);padding:12px 14px;outline:none;transition:.3s;font-family:var(--f-body)}
.form textarea{min-height:130px;resize:vertical}
.form input:focus,.form select:focus,.form textarea:focus{border-color:var(--bronze)}
.form select option{background:var(--bark-2);color:var(--cream)}
.form input::placeholder,.form textarea::placeholder{color:#6E6154}
.form .f.bad input,.form .f.bad select,.form .f.bad textarea{border-color:var(--err)}
.msg{display:none;font-size:12.5px;color:var(--err);margin-top:7px}
.f.bad .msg{display:block}
.consent{grid-column:1/-1;display:flex;gap:13px;align-items:flex-start;font-size:13.5px;color:var(--muted);cursor:pointer;padding:6px 0}
.consent input{min-height:0;width:19px;height:19px;flex:0 0 auto;margin-top:3px;accent-color:var(--bronze)}
.consent.bad{color:var(--err)}
.form .btn{grid-column:1/-1;margin-top:6px}
.sent{grid-column:1/-1;display:none;border:1px solid rgba(143,174,99,.5);background:rgba(143,174,99,.08);padding:22px 24px}
.sent.on{display:block;animation:fade .5s}
@keyframes fade{from{opacity:0;transform:translateY(-8px)}}
.sent b{display:block;font-family:var(--f-display);font-size:1.3rem;color:var(--palm);margin-bottom:6px}
.sent p{font-size:14px;margin:0}
.aside .box{border:1px solid var(--line);margin-bottom:24px}
.aside .box h3{padding:20px 24px 0}
.aside .box .r{padding:14px 24px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:16px;font-size:14px}
.aside .box .r:last-child{border-bottom:0}
.aside .box .r span:first-child{color:var(--muted);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;font-weight:600}
.aside .box .r .hi{color:var(--palm)}
.social{display:flex;gap:10px;flex-wrap:wrap}
.social a{width:46px;height:46px;border:1px solid var(--line);display:grid;place-items:center;transition:.3s}
.social a:hover{border-color:var(--bronze);background:var(--bark-2)}
.social svg{width:18px;height:18px;fill:var(--muted);transition:.3s}
.social a:hover svg{fill:var(--bronze)}
.map{position:relative;border-top:1px solid var(--line)}
.map iframe{width:100%;height:480px;border:0;display:block;filter:grayscale(.35) sepia(.25) contrast(.95)}
.map .over{position:absolute;top:34px;left:0;right:0;pointer-events:none}
.map .card{pointer-events:auto;background:rgba(23,16,10,.95);backdrop-filter:blur(12px);border:1px solid var(--line);padding:26px 28px;max-width:340px}
.map .card h3{margin-bottom:10px}
.map .card p{font-size:14px;margin-bottom:16px}
.route{background:var(--bark-2);padding:80px 0;border-top:1px solid var(--line)}
.route-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:36px}
.route-grid article{border:1px solid var(--line);padding:28px}
.route-grid .n{font-family:var(--f-display);font-size:1.9rem;color:var(--bronze);line-height:1;margin-bottom:14px;display:block}
.route-grid h3{margin-bottom:8px;font-size:1.1rem}
.route-grid p{font-size:14px;color:var(--muted)}
@media(max-width:1080px){
  .chan{grid-template-columns:repeat(2,1fr)}
  .grid{grid-template-columns:1fr;gap:44px}
  .route-grid{grid-template-columns:1fr}
}
@media(max-width:720px){
  .head{padding:126px 0 30px}
  .chan,.form{grid-template-columns:1fr}
  .map iframe{height:380px}
  .map .over{position:relative;top:0;padding:0 24px;margin-top:-40px}
  .map .card{max-width:none}
}
"""

CHAN = [
 ('tel:+2252721731265','k1','Réception · 24 h/24','+225 27 21 73 12 65','v1','Pour toute question sur place',
  '<path d="M5 3h4l2 5-3 2a12 12 0 006 6l2-3 5 2v4a2 2 0 01-2 2A17 17 0 013 5a2 2 0 012-2z"/>'),
 ('tel:+2250151527575','k2','Réservations','+225 01 51 52 75 75','v2','Chambres, circuits et groupes',
  '<path d="M4 7h16v13H4zM4 7l8 6 8-6M8 3v4M16 3v4"/>'),
 ('https://wa.me/2250546017377','k3','WhatsApp','+225 05 46 01 73 77','v3','Réponse la plus rapide',
  '<path d="M12 3a9 9 0 00-7.7 13.6L3 21l4.6-1.2A9 9 0 1012 3z"/><path d="M9 9.5c0 3 2.5 5.5 5.5 5.5"/>'),
 ('mailto:bonjour@evannathhotel.com','k4','E-mail','bonjour@<br>evannathhotel.com','v4','Devis, séminaires, presse',
  '<rect x="3" y="5" width="18" height="14"/><path d="M3 7l9 6 9-6"/>'),
]

SOCIAL = [
 ('https://www.facebook.com/evannathhotel','Facebook','<path d="M13 22v-9h3l.5-4H13V7c0-1 .3-1.7 1.8-1.7H17V1.8C16.6 1.7 15.3 1.6 13.8 1.6 10.7 1.6 8.6 3.5 8.6 7v2H5.5v4h3.1v9z"/>'),
 ('https://www.instagram.com/evannathhotel/','Instagram','<path d="M12 2.2c3.2 0 3.6 0 4.9.1 3.3.1 4.8 1.7 4.9 4.9.1 1.3.1 1.6.1 4.8s0 3.6-.1 4.9c-.1 3.2-1.6 4.8-4.9 4.9-1.3.1-1.6.1-4.9.1s-3.6 0-4.9-.1c-3.3-.1-4.8-1.7-4.9-4.9C2.1 15.6 2.1 15.2 2.1 12s0-3.6.1-4.9c.1-3.2 1.6-4.8 4.9-4.9C8.4 2.2 8.8 2.2 12 2.2zm0 3.2A6.6 6.6 0 1018.6 12 6.6 6.6 0 0012 5.4zm0 10.9A4.3 4.3 0 1116.3 12 4.3 4.3 0 0112 16.3zm6.8-11.1a1.5 1.5 0 101.5 1.5 1.5 1.5 0 00-1.5-1.5z"/>'),
 ('https://www.tiktok.com/@evannath.hotel','TikTok','<path d="M16.6 5.8a4.8 4.8 0 01-1.1-3.1h-3.2v12.9a2.6 2.6 0 11-2.6-2.6c.3 0 .5 0 .8.1V9.7a5.9 5.9 0 00-.8-.1 5.9 5.9 0 105.9 5.9V9.1a7.9 7.9 0 004.6 1.5V7.4a4.7 4.7 0 01-3.6-1.6z"/>'),
 ('https://www.youtube.com/@evannathhotel','YouTube','<path d="M23 7.5a3 3 0 00-2.1-2.1C19 4.8 12 4.8 12 4.8s-7 0-8.9.6A3 3 0 001 7.5 31 31 0 00.4 12 31 31 0 001 16.5a3 3 0 002.1 2.1c1.9.6 8.9.6 8.9.6s7 0 8.9-.6a3 3 0 002.1-2.1A31 31 0 0023.6 12 31 31 0 0023 7.5zM9.8 15.3V8.7l5.7 3.3z"/>'),
 ('https://www.linkedin.com/company/evannathhotel','LinkedIn','<path d="M4.9 3.5a2.4 2.4 0 11-2.4 2.4 2.4 2.4 0 012.4-2.4zM2.9 8.9h4V21h-4zM9.4 8.9h3.8v1.7h.1a4.2 4.2 0 013.8-2.1c4 0 4.8 2.7 4.8 6.1V21h-4v-5.6c0-1.3 0-3-1.9-3s-2.1 1.4-2.1 2.9V21h-4z"/>'),
]

b = [header('#ecrire','Nous écrire','wr'), drawer('contact.html'), '''
<div class="wrap head">
  <nav class="crumb" aria-label="Fil d'Ariane">
    <a href="index.html" data-t="c1">Accueil</a> &nbsp;·&nbsp; <span data-t="c2">Contact</span>
  </nav>
  <span class="eyebrow" data-t="eb">Réception ouverte 24 h/24</span>
  <h1 data-t="h1">Nous joindre</h1>
  <p data-t="lede">Par téléphone, par WhatsApp, par e-mail ou par le formulaire — choisissez ce qui vous arrange. Nous répondons sous 24 h, et le plus souvent bien avant.</p>
</div>

<div class="wrap">
  <div class="chan reveal">''']

for href, k, klab, val, v, vlab, ic in CHAN:
    ext = ' target="_blank" rel="noopener"' if href.startswith('http') else ''
    b.append('''    <a href="%s"%s>
      <svg viewBox="0 0 24 24" aria-hidden="true">%s</svg>
      <b data-t="%s">%s</b><span>%s</span><em data-t="%s">%s</em>
    </a>''' % (href, ext, ic, k, klab, val, v, vlab))

b.append('''  </div>
</div>

<div class="wrap grid" id="ecrire">
  <form class="form reveal" id="cf" novalidate>
    <div class="f"><label for="fn" data-t="l1">Prénom <span class="req">*</span></label>
      <input type="text" id="fn" autocomplete="given-name" placeholder="Aya">
      <span class="msg" data-t="m1">Merci d'indiquer votre prénom.</span></div>
    <div class="f"><label for="ln" data-t="l2">Nom <span class="req">*</span></label>
      <input type="text" id="ln" autocomplete="family-name" placeholder="Kouassi">
      <span class="msg" data-t="m2">Merci d'indiquer votre nom.</span></div>
    <div class="f"><label for="em" data-t="l3">E-mail <span class="req">*</span></label>
      <input type="email" id="em" autocomplete="email" placeholder="vous@exemple.com">
      <span class="msg" data-t="m3">Cette adresse e-mail ne semble pas valide.</span></div>
    <div class="f"><label for="tl" data-t="l4">Téléphone <span class="req">*</span></label>
      <input type="tel" id="tl" autocomplete="tel" placeholder="+225 01 02 03 04 05">
      <span class="msg" data-t="m4">Indiquez un numéro d'au moins 8 chiffres.</span></div>
    <div class="f full"><label for="ob" data-t="l5">Objet <span class="req">*</span></label>
      <select id="ob">
        <option value="" data-t="o0">— Choisissez un objet —</option>
        <option data-t="o1">Réserver une chambre</option>
        <option data-t="o2">Réserver un circuit ou une offre</option>
        <option data-t="o3">Réserver une table au restaurant</option>
        <option data-t="o4">Séminaire, groupe ou événement</option>
        <option data-t="o5">Spa et bien-être</option>
        <option data-t="o6">Navette aéroport</option>
        <option data-t="o7">Autre demande</option>
      </select>
      <span class="msg" data-t="m5">Merci de choisir un objet.</span></div>
    <div class="f full"><label for="ms" data-t="l6">Message <span class="req">*</span></label>
      <textarea id="ms" placeholder="Vos dates, le nombre de personnes, vos questions…"></textarea>
      <span class="msg" data-t="m6">Votre message doit faire au moins 10 caractères.</span></div>
    <label class="consent" id="cs"><input type="checkbox" id="ck">
      <span data-t="l7">J'accepte que ces informations soient utilisées pour répondre à ma demande. Elles ne seront ni revendues ni transmises à des tiers.</span></label>
    <span class="msg" id="ckmsg" style="grid-column:1/-1;margin-top:-8px" data-t="m7">Merci de cocher cette case pour continuer.</span>
    <button type="submit" class="btn btn-solid" data-t="l8">Envoyer le message</button>
    <div class="sent" id="ok" role="status">
      <b data-t="s1">Message envoyé</b>
      <p data-t="s2">Merci. La réception vous répond sous 24 h. Pour une demande urgente, WhatsApp reste le plus rapide.</p>
    </div>
  </form>

  <aside class="aside reveal">
    <div class="box">
      <h3 data-t="b1">Horaires</h3>
      <div class="r"><span data-t="h2">Réception</span><span class="hi" data-t="hv">24 h/24</span></div>
      <div class="r"><span data-t="h3">Arrivée</span><span>14 h 00</span></div>
      <div class="r"><span data-t="h4">Départ</span><span>12 h 00</span></div>
      <div class="r"><span data-t="h5">Déjeuner</span><span>12 h — 15 h</span></div>
      <div class="r"><span data-t="h6">Dîner</span><span>19 h — 22 h 30</span></div>
      <div class="r"><span data-t="h7">Spa</span><span data-t="h7v">sur rendez-vous</span></div>
    </div>
    <div class="box">
      <h3 data-t="b2">Adresse</h3>
      <p style="padding:12px 24px 8px;color:#D6CBBB;font-size:15px">Hôtel Evannath<br>Assinie PK 19<br>Comoé, Côte d'Ivoire</p>
      <div style="padding:0 24px 24px"><a href="https://www.google.com/maps/search/Assinie+PK+19" target="_blank" rel="noopener" class="btn" style="width:100%" data-t="b2c">Ouvrir dans Maps</a></div>
    </div>
    <div class="box" style="padding:22px 24px">
      <h3 style="padding:0 0 16px" data-t="b3">Nous suivre</h3>
      <div class="social">''')

for href, lab, ic in SOCIAL:
    b.append('        <a href="%s" target="_blank" rel="noopener" aria-label="%s"><svg viewBox="0 0 24 24">%s</svg></a>' % (href, lab, ic))

b.append('''      </div>
      <p style="padding:16px 0 0;font-size:13px;color:var(--muted)" data-t="b3p">21 000 abonnés nous suivent sur Facebook.</p>
    </div>
  </aside>
</div>

<div class="map">
  <iframe title="Carte d'accès — Hôtel Evannath, Assinie" loading="lazy"
    src="https://www.google.com/maps?q=Assinie-Mafia,%20C%C3%B4te%20d'Ivoire&output=embed"></iframe>
  <div class="over"><div class="wrap"><div class="card">
    <h3 data-t="mp1">Assinie, PK 19</h3>
    <p data-t="mp2">Sur la route d'Assinie-Mafia, entre l'océan Atlantique et la lagune Aby.</p>
    <a href="https://www.google.com/maps/dir/?api=1&destination=Assinie-Mafia" target="_blank" rel="noopener" class="btn btn-solid" data-t="mp3">Lancer l'itinéraire</a>
  </div></div></div>
</div>

<section class="route">
 <div class="wrap">
  <span class="eyebrow" data-t="e3">Venir jusqu'à nous</span>
  <h2 data-t="h3">Trois façons d'arriver</h2>
  <div class="route-grid">
    <article class="reveal"><span class="n">1 h 45</span><h3 data-t="r1">Depuis Abidjan, en voiture</h3><p data-t="r1p">Par l'autoroute puis la route côtière d'Assinie. Parking gratuit et surveillé sur le domaine.</p></article>
    <article class="reveal"><span class="n">80 km</span><h3 data-t="r2">Depuis l'aéroport FHB</h3><p data-t="r2p">Navette gratuite à l'aller comme au retour, sur simple demande à la réservation. Sans supplément.</p></article>
    <article class="reveal"><span class="n">15 min</span><h3 data-t="r3">Par la lagune</h3><p data-t="r3p">Arrivée en pirogue jusqu'au ponton de l'hôtel. À organiser avec la réception à l'avance.</p></article>
  </div>
 </div>
</section>

''' + FOOTER)

JS_CONTACT = NAV_JS + '''

// Validation : le formulaire actuel de l'hôtel n'en a aucune.
// Ici chaque champ se vérifie à la sortie, et le premier champ fautif reçoit le focus.
var champs=[
  {id:'fn',test:function(v){return v.trim().length>=2}},
  {id:'ln',test:function(v){return v.trim().length>=2}},
  {id:'em',test:function(v){return /^[^\\s@]+@[^\\s@]+\\.[a-z]{2,}$/i.test(v.trim())}},
  {id:'tl',test:function(v){return (v.replace(/\\D/g,'').length>=8)}},
  {id:'ob',test:function(v){return v!==''}},
  {id:'ms',test:function(v){return v.trim().length>=10}}
];
function box(el){return el.closest('.f')}
function check(c,montrer){
  var el=document.getElementById(c.id),ok=c.test(el.value);
  if(montrer||box(el).classList.contains('bad'))box(el).classList.toggle('bad',!ok);
  el.setAttribute('aria-invalid',ok?'false':'true');
  return ok;
}
champs.forEach(function(c){
  var el=document.getElementById(c.id);
  el.addEventListener('blur',function(){check(c,true)});
  el.addEventListener('input',function(){if(box(el).classList.contains('bad'))check(c,true)});
  el.addEventListener('change',function(){if(box(el).classList.contains('bad'))check(c,true)});
});
var ck=document.getElementById('ck'),cs=document.getElementById('cs'),ckmsg=document.getElementById('ckmsg');
ckmsg.style.display='none';
ck.addEventListener('change',function(){if(ck.checked){cs.classList.remove('bad');ckmsg.style.display='none'}});

document.getElementById('cf').addEventListener('submit',function(e){
  e.preventDefault();
  var premier=null;
  champs.forEach(function(c){ if(!check(c,true)&&!premier)premier=document.getElementById(c.id) });
  if(!ck.checked){cs.classList.add('bad');ckmsg.style.display='block';if(!premier)premier=ck}
  if(premier){premier.focus();premier.scrollIntoView({behavior:'smooth',block:'center'});return}
  document.getElementById('ok').classList.add('on');
  document.getElementById('ok').scrollIntoView({behavior:'smooth',block:'center'});
});

var EN={''' + EN_NAV + '''wr:"Write to us",
c1:"Home",c2:"Contact",eb:"Front desk open 24/7",h1:"Get in touch",
lede:"By phone, WhatsApp, email or the form — whichever suits you. We reply within 24 h, and usually well before.",
k1:"Front desk · 24/7",v1:"For anything on site",k2:"Reservations",v2:"Rooms, packages and groups",
k3:"WhatsApp",v3:"Fastest reply",k4:"Email",v4:"Quotes, seminars, press",
l1:"First name <span class=\\"req\\">*</span>",l2:"Last name <span class=\\"req\\">*</span>",l3:"Email <span class=\\"req\\">*</span>",
l4:"Phone <span class=\\"req\\">*</span>",l5:"Subject <span class=\\"req\\">*</span>",l6:"Message <span class=\\"req\\">*</span>",
l7:"I agree that this information may be used to answer my request. It will never be sold or passed on to third parties.",
l8:"Send message",
m1:"Please give your first name.",m2:"Please give your last name.",m3:"This email address does not look valid.",
m4:"Enter a number with at least 8 digits.",m5:"Please choose a subject.",m6:"Your message needs at least 10 characters.",
m7:"Please tick this box to continue.",
o0:"— Choose a subject —",o1:"Book a room",o2:"Book a package or offer",o3:"Book a table at the restaurant",
o4:"Seminar, group or event",o5:"Spa and wellbeing",o6:"Airport shuttle",o7:"Something else",
s1:"Message sent",s2:"Thank you. The front desk replies within 24 h. For anything urgent, WhatsApp is fastest.",
b1:"Opening hours",h2:"Front desk",hv:"24/7",h3:"Check-in",h4:"Check-out",h5:"Lunch",h6:"Dinner",h7:"Spa",h7v:"by appointment",
b2:"Address",b2c:"Open in Maps",b3:"Follow us",b3p:"21,000 people follow us on Facebook.",
mp1:"Assinie, PK 19",mp2:"On the Assinie-Mafia road, between the Atlantic Ocean and the Aby lagoon.",mp3:"Get directions",
e3:"Getting here",h3:"Three ways to arrive",
r1:"From Abidjan, by car",r1p:"Motorway then the Assinie coast road. Free, guarded parking on site.",
r2:"From FHB airport",r2p:"Free shuttle both ways, simply ask when booking. No surcharge.",
r3:"By the lagoon",r3p:"Arrive by pirogue at the hotel's pontoon. Arrange with the front desk in advance."};

''' + LANG_JS

io.open('contact.html','w',encoding='utf-8').write(page(
 "Contact — Hôtel Evannath, Assinie PK 19",
 "Contacter l'Hôtel Evannath à Assinie PK 19 : réception 24 h/24, réservations, WhatsApp, e-mail bonjour@evannathhotel.com. Itinéraire depuis Abidjan et navette aéroport gratuite.",
 "g-entree", CSS_CONTACT, '\n'.join(b), JS_CONTACT))
print('contact.html          ok')
