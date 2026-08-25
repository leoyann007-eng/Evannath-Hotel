# -*- coding: utf-8 -*-
"""Blocs partages par toutes les pages : nav unique, tiroir plein ecran, pied de page.
Utilise par les generateurs de pages. Aucune expression reguliere destructrice ici :
les pages sont ecrites en entier a partir de ces briques.
"""

# Domaine de production. Une seule ligne a changer le jour ou le site passe
# sur evannathhotel.com : og:image, og:url, canonical et sitemap.xml en decoulent.
SITE = "https://evannathhotel.vercel.app"

# ---------------------------------------------------------------------------
# Mode prospection
# ---------------------------------------------------------------------------
# True  : la maquette porte la marque de l'hotel sur une URL qu'il ne controle
#         pas. Elle ne doit apparaitre dans aucun moteur de recherche, sous
#         peine de concurrencer leur propre site et d'exploiter publiquement
#         leur marque sans accord ecrit. Le visiteur qui a le lien voit tout
#         normalement : seuls les robots sont ecartes.
# False : le jour de la signature. Repasser a False, relancer tous les
#         generateurs et build-sitemap.py, puis retirer la regle
#         X-Robots-Tag de vercel.json (elle est commentee sur place).
PROSPECTION = True

# On laisse volontairement les robots CRAWLER, tout en leur servant `noindex`.
# Un simple « Disallow: / » serait un contresens ici : Google ne lirait alors
# jamais la directive noindex, et pourrait tout de meme indexer l'URL nue en la
# decouvrant par un lien externe. Pour disparaitre vraiment, il faut etre lu.
ROBOTS_META = ('<meta name="robots" content="noindex, nofollow">\n'
               '<meta name="googlebot" content="noindex, nofollow">\n') if PROSPECTION else ''


ICONS = """<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#17100A">"""

HEAD_CSS = """:root{
  --night:#100B06; --bark:#17100A; --bark-2:#1E150D; --bark-3:#2A1E13;
  --bronze:#B98A50; --bronze-2:#DFBB84;
  --cream:#F6EEE2; --muted:#9C8B78; --palm:#8FAE63; --err:#E08A7B;
  --line:rgba(185,138,80,.18); --line-2:rgba(185,138,80,.10);
  --max:1240px;
  /* Hauteur de l'en-tete fixe une fois compacte. Les barres collantes s'y
     adossent : une valeur devinee laissait soit un interstice ou le contenu
     defilait a decouvert, soit un chevauchement qui masquait la barre. */
  --h-nav:83px;
  --f-display:"Marcellus",Georgia,"Times New Roman",serif;
  --f-body:"Karla",system-ui,-apple-system,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--bark);color:var(--cream);font-family:var(--f-body);font-size:16.5px;line-height:1.7;overflow-x:hidden;-webkit-font-smoothing:antialiased}
img{max-width:100%;height:auto;display:block}
a{color:inherit;text-decoration:none}
:focus-visible{outline:2px solid var(--bronze);outline-offset:3px}
.wrap{max-width:var(--max);margin:0 auto;padding:0 24px}
.narrow{max-width:900px;margin:0 auto;padding:0 24px}
.eyebrow{font-size:10.5px;letter-spacing:.36em;text-transform:uppercase;color:var(--bronze);font-weight:700;display:block}
h1,h2,h3{font-family:var(--f-display);font-weight:400;line-height:1.1;text-wrap:balance}
h1{font-size:clamp(2.4rem,5.4vw,4rem)}
h2{font-size:clamp(1.7rem,3.2vw,2.5rem)}
h3{font-size:1.2rem}
p{color:#D6CBBB}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:10px;padding:16px 32px;font-size:11px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;border:1px solid var(--bronze);color:var(--bronze);background:transparent;cursor:pointer;transition:.4s cubic-bezier(.2,.8,.2,1);font-family:var(--f-body)}
.btn:hover{background:var(--bronze);color:var(--night);transform:translateY(-2px)}
.btn-solid{background:var(--bronze);color:var(--night)}
.btn-solid:hover{background:var(--bronze-2);border-color:var(--bronze-2)}

/* NAV : un seul element */
header{position:fixed;top:0;left:0;right:0;z-index:100;transition:.45s;padding:22px 0;background:rgba(23,16,10,.9);backdrop-filter:blur(14px)}
header.scrolled{padding:11px 0;background:rgba(23,16,10,.97);border-bottom:1px solid var(--line)}
.nav{display:flex;align-items:center;justify-content:space-between;gap:20px}
.brand img{width:168px;transition:.45s}
header.scrolled .brand img{width:132px}
.brand small{display:block;font-size:8px;letter-spacing:.42em;color:var(--bronze);margin-top:6px;padding-left:2px;font-weight:700}
.nav-right{display:flex;align-items:center;gap:18px}
.lang{display:flex;border:1px solid var(--line)}
.lang button{background:none;border:0;color:var(--muted);font:700 10.5px/1 var(--f-body);letter-spacing:.12em;padding:9px 11px;cursor:pointer;transition:.3s}
.lang button.on{background:var(--bronze);color:var(--night)}
.burger{display:flex;align-items:center;gap:12px;background:none;border:0;cursor:pointer;padding:10px 4px;position:relative;z-index:101}
.burger .bars{display:block;width:26px}
.burger .bars span{display:block;height:1.5px;background:var(--cream);margin:6px 0;transition:.35s}
.burger .lbl{font-size:10.5px;letter-spacing:.24em;text-transform:uppercase;font-weight:700;color:var(--cream)}
.burger.open .bars span:nth-child(1){transform:translateY(7.5px) rotate(45deg)}
.burger.open .bars span:nth-child(2){opacity:0}
.burger.open .bars span:nth-child(3){transform:translateY(-7.5px) rotate(-45deg)}
.drawer{position:fixed;inset:0;background:var(--night);z-index:99;opacity:0;visibility:hidden;transition:.5s cubic-bezier(.2,.8,.2,1);overflow-y:auto}
.drawer.open{opacity:1;visibility:visible}
.dw-in{min-height:100svh;display:grid;grid-template-columns:1.25fr 1fr;align-items:center;gap:60px;max-width:var(--max);margin:0 auto;padding:130px 24px 60px}
.dw-in nav{display:flex;flex-direction:column}
.dw-in nav a{
  display:flex;align-items:baseline;gap:22px;padding:16px 0;border-bottom:1px solid var(--line-2);
  font-family:var(--f-display);font-size:clamp(1.45rem,3.2vw,2.4rem);color:var(--cream);
  opacity:0;transform:translateY(18px);transition:color .3s,opacity .6s,transform .6s
}
.drawer.open .dw-in nav a{opacity:1;transform:none}
.dw-in nav a:hover,.dw-in nav a.on{color:var(--bronze-2)}
.dw-in nav a i{font-style:normal;font-family:var(--f-body);font-size:10px;letter-spacing:.2em;color:var(--bronze);font-weight:700;flex:0 0 auto;opacity:.7}
.dw-side{display:flex;flex-direction:column;gap:26px}
.dw-side .ph{aspect-ratio:4/3;overflow:hidden;background:var(--bark-2)}
.dw-side .ph img{width:100%;height:100%;object-fit:cover}
.dw-side b{display:block;font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:var(--bronze);font-weight:700;margin-bottom:12px}
.dw-side a{display:block;font-size:15px;color:#CDBFAE;padding:7px 0;transition:.3s}
.dw-side a:hover{color:var(--bronze)}
.dw-side p{font-size:13.5px;color:var(--muted);margin-top:12px}
.dw-side .lang{margin-top:6px;width:max-content}
.dw-side .lang button{padding:15px 20px;font-size:11px}

/* Etats d'envoi des formulaires */
.piege{position:absolute!important;left:-9999px!important;width:1px;height:1px;overflow:hidden}
button[aria-busy="true"]{opacity:.62;cursor:progress}
.secours{display:none;border:1px solid var(--bronze);background:rgba(185,138,80,.07);padding:24px 26px;margin-top:20px}
.secours.on{display:block}
.secours b{display:block;font-family:var(--f-display);font-size:1.2rem;color:var(--bronze-2);margin-bottom:8px}
.secours p{font-size:14px;margin-bottom:16px}
.secours .liens{display:flex;gap:12px;flex-wrap:wrap}
.secours .liens a{display:inline-flex;align-items:center;gap:9px;border:1px solid var(--line);padding:12px 18px;
  font-size:11px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--cream);transition:.3s}
.secours .liens a:hover{border-color:var(--bronze);color:var(--bronze-2)}
.secours .liens a.wa{background:var(--palm);border-color:var(--palm);color:#0F1508}
.secours .liens a.wa:hover{filter:brightness(1.1);color:#0F1508}
.err-envoi{display:none;color:var(--err);font-size:13.5px;margin-top:14px}
.err-envoi.on{display:block}

.skip{position:absolute;left:-9999px;top:0;z-index:200;background:var(--bronze);color:var(--night);
  padding:14px 22px;font-size:11px;font-weight:700;letter-spacing:.2em;text-transform:uppercase}
.skip:focus{left:0}
main{display:block}

.crumb{font-size:11.5px;letter-spacing:.1em;color:var(--muted);margin-bottom:22px}
.crumb a{padding:6px 0;display:inline-block}
.crumb a:hover{color:var(--bronze)}
.crumb span{color:var(--bronze)}

footer{background:#0B0704;border-top:1px solid var(--line);padding:74px 0 28px}
.f-grid{display:grid;grid-template-columns:1.6fr 1fr 1fr 1.2fr;gap:44px}
.f-grid h4{font-size:10.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--bronze);margin-bottom:20px;font-weight:700}
.f-grid p{display:block;font-size:13.5px;color:#9C8B78;margin-bottom:11px}
.f-grid a{display:block;font-size:13.5px;color:#9C8B78;padding:9px 0;transition:.3s}
.f-grid a:hover{color:var(--bronze)}
.f-bot{border-top:1px solid var(--line);margin-top:54px;padding-top:26px;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-size:11.5px;color:#A2907C}
.wa{position:fixed;right:22px;bottom:22px;z-index:90;width:56px;height:56px;border-radius:50%;background:#25D366;display:grid;place-items:center;box-shadow:0 10px 30px rgba(37,211,102,.35);transition:.35s}
.wa:hover{transform:scale(1.09)}
.wa svg{width:28px;height:28px;fill:#fff}

.reveal{opacity:0;transform:translateY(28px);transition:opacity .9s cubic-bezier(.2,.8,.2,1),transform .9s cubic-bezier(.2,.8,.2,1)}
.reveal.in{opacity:1;transform:none}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition-duration:.01ms!important}.reveal,.dw-in nav a{opacity:1;transform:none}}

@media(max-width:1080px){
  .dw-in{grid-template-columns:1fr;gap:40px;align-content:start}
  .dw-side .ph{display:none}
  .f-grid{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:720px){
  .burger .lbl{display:none}
  .nav-right .lang{display:none}
  .dw-in{padding:110px 24px 50px}
  .f-grid{grid-template-columns:1fr}
}
"""

HEAD = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Karla:wght@300;400;500;600;700&display=swap" rel="stylesheet">"""

LINKS = [
 ('01','chambres.html','n1','Chambres &amp; Suites'),
 ('02','experiences.html','n2','Expériences'),
 ('03','carte.html','n3','La table'),
 ('04','spa.html','n4','Le spa'),
 ('05','circuits.html','n5','Circuits &amp; Offres'),
 ('06','seminaires.html','n6','Séminaires &amp; groupes'),
 ('07','galerie.html','n7','Galerie'),
 ('08','a-propos.html','n8','À propos'),
 ('09','informations-utiles.html','n9','Informations utiles'),
 ('10','contact.html','n10','Contact'),
 ('11','reserver.html','n11','Réserver'),
]

def header(cta_href, cta_label, cta_key='cta'):
    return '''<a class="skip" href="#contenu">Aller au contenu</a>
<header id="hd">
  <div class="wrap nav">
    <a href="index.html" class="brand" aria-label="Hôtel Evannath, accueil">
      <img src="img/opt/logo-blanc.png" alt="Hôtel Evannath" width="729" height="176">
      <small>LE RÊVE AFRICAIN</small>
    </a>
    <div class="nav-right">
      <div class="lang"><button class="on" data-lang="fr">FR</button><button data-lang="en">EN</button></div>
      <a href="%s" class="btn btn-solid" data-t="%s">%s</a>
      <button class="burger" id="bg" aria-label="Ouvrir le menu" aria-expanded="false" aria-controls="dw">
        <span class="lbl" data-t="mn">Menu</span>
        <span class="bars"><span></span><span></span><span></span></span>
      </button>
    </div>
  </div>
</header>''' % (cta_href, cta_key, cta_label)

def drawer(current='', photo='t-lampe', alt='Lanterne de rotin de l\'Hôtel Evannath'):
    rows = []
    for num, href, key, label in LINKS:
        cls = ' class="on"' if href == current else ''
        rows.append('      <a href="%s"%s><i>%s</i><span data-t="%s">%s</span></a>' % (href, cls, num, key, label))
    return '''<div class="drawer" id="dw">
  <div class="dw-in">
    <nav aria-label="Navigation principale">
%s
    </nav>
    <aside class="dw-side">
      <div class="ph"><picture><source srcset="img/opt/%s.webp" type="image/webp">
        <img src="img/opt/%s.jpg" width="1100" height="733" alt="%s" loading="lazy"></picture></div>
      <div>
        <b data-t="dr">Réservations</b>
        <a href="tel:+2250151527575">+225 01 51 52 75 75</a>
        <a href="mailto:bonjour@evannathhotel.com">bonjour@evannathhotel.com</a>
        <a href="https://wa.me/2250546017377" target="_blank" rel="noopener">WhatsApp</a>
        <p>Assinie PK 19 · Comoé · Côte d'Ivoire</p>
      </div>
      <div class="lang"><button class="on" data-lang="fr">FR</button><button data-lang="en">EN</button></div>
    </aside>
  </div>
</div>

<main id="contenu">''' % ('\n'.join(rows), photo, photo, alt)

FOOTER = '''</main>

<footer>
  <div class="wrap">
    <div class="f-grid">
      <div>
        <img src="img/opt/logo-blanc.png" alt="Hôtel Evannath" width="729" height="176" style="width:180px;margin-bottom:8px">
        <p style="font-size:8.5px;letter-spacing:.42em;color:var(--bronze);font-weight:700;margin-bottom:18px">LE RÊVE AFRICAIN</p>
        <p style="max-width:300px">46 chambres et suites face à la lagune Aby, à Assinie. Réservation directe, meilleur tarif garanti, réception ouverte 24 h/24.</p>
      </div>
      <div><h4>Navigation</h4><a href="chambres.html">Chambres</a><a href="experiences.html">Expériences</a><a href="carte.html">La table</a><a href="circuits.html">Circuits &amp; Offres</a><a href="spa.html">Spa</a><a href="a-propos.html">À propos</a><a href="contact.html">Contact</a></div>
      <div><h4>Informations</h4><a href="informations-utiles.html">Informations utiles</a><a href="seminaires.html">Séminaires &amp; groupes</a><a href="informations-utiles.html#reserver">Conditions d'annulation</a><a href="mentions-legales.html">Mentions légales</a></div>
      <div><h4>Contact</h4>
        <a href="tel:+2252721731265">+225 27 21 73 12 65</a>
        <a href="tel:+2250151527575">+225 01 51 52 75 75</a>
        <a href="mailto:bonjour@evannathhotel.com">bonjour@evannathhotel.com</a>
        <a href="https://www.facebook.com/evannathhotel" target="_blank" rel="noopener">Facebook — 21 K abonnés</a>
      </div>
    </div>
    <div class="f-bot"><span>© 2026 Hôtel Evannath — Assinie, Côte d'Ivoire</span><span>Assinie · Comoé · Côte d'Ivoire</span></div>
  </div>
</footer>

<a class="wa" href="https://wa.me/2250546017377" target="_blank" rel="noopener" aria-label="Nous écrire sur WhatsApp">
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.5 14.4c-.3-.1-1.7-.9-2-1-.3-.1-.5-.1-.7.1-.2.3-.7 1-.9 1.2-.2.2-.3.2-.6.1-1.7-.9-2.9-1.6-4-3.5-.3-.5.3-.5.9-1.6.1-.2 0-.4 0-.5s-.7-1.6-.9-2.2c-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.5s1.1 2.9 1.2 3.1c.1.2 2.1 3.3 5.2 4.6 1.9.8 2.7.9 3.6.8.6-.1 1.7-.7 2-1.4.2-.7.2-1.2.2-1.4-.1-.1-.3-.2-.6-.3M12 2a10 10 0 00-8.6 15L2 22l5.2-1.4A10 10 0 1012 2z"/></svg>
</a>'''

NAV_JS = """var hd=document.getElementById('hd');
addEventListener('scroll',function(){hd.classList.toggle('scrolled',scrollY>60)},{passive:true});

var bg=document.getElementById('bg'),dw=document.getElementById('dw');
var dwLinks=[].slice.call(dw.querySelectorAll('nav a'));
function toggleMenu(){
  var o=dw.classList.toggle('open');
  bg.classList.toggle('open',o);
  bg.setAttribute('aria-expanded',o);
  bg.setAttribute('aria-label',o?'Fermer le menu':'Ouvrir le menu');
  document.body.style.overflow=o?'hidden':'';
  dwLinks.forEach(function(a,i){a.style.transitionDelay=o?(60+i*55)+'ms':'0ms'});
}
bg.onclick=toggleMenu;
dwLinks.forEach(function(a){a.onclick=function(){if(dw.classList.contains('open'))toggleMenu()}});
addEventListener('keydown',function(e){if(e.key==='Escape'&&dw.classList.contains('open'))toggleMenu()});

var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
if(!('IntersectionObserver' in window)||reduce){document.querySelectorAll('.reveal').forEach(function(e){e.classList.add('in')})}
else{var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.1});
 document.querySelectorAll('.reveal').forEach(function(el){io.observe(el)});
 setTimeout(function(){document.querySelectorAll('.reveal:not(.in)').forEach(function(el){if(el.getBoundingClientRect().top<innerHeight)el.classList.add('in')})},1200)}"""

LANG_JS = """var FR={};document.querySelectorAll('[data-t]').forEach(function(e){FR[e.dataset.t]=e.innerHTML});
document.querySelectorAll('.lang button').forEach(function(b){b.onclick=function(){
  var lg=b.dataset.lang;
  document.querySelectorAll('.lang button').forEach(function(x){x.classList.toggle('on',x.dataset.lang===lg)});
  var dict=lg==='en'?EN:FR;
  document.querySelectorAll('[data-t]').forEach(function(e){if(dict[e.dataset.t])e.innerHTML=dict[e.dataset.t]});
  document.documentElement.lang=lg;
}});"""

ENVOI_JS = """
/* Envoi des formulaires -------------------------------------------------
   Un seul point d'entree cote serveur : /api/envoyer.
   Si l'envoi automatique n'est pas configure ou echoue, on ne perd jamais le
   visiteur : on lui propose WhatsApp avec le message deja redige, plus les
   numeros de la reception. */
var EVN = {
  wa: '2250546017377',
  tel: '+2250151527575',
  mail: 'bonjour@evannathhotel.com',
  ouvert: Date.now(),

  lienWhatsApp: function (texte) {
    return 'https://wa.me/' + this.wa + '?text=' + encodeURIComponent(texte);
  },

  /* o : {bouton, secours, erreur, resume} */
  envoyer: function (type, donnees, o, alors) {
    var b = o.bouton, libelle = b ? b.textContent : '';
    if (b) { b.setAttribute('aria-busy', 'true'); b.disabled = true; b.textContent = 'Envoi en cours…'; }
    if (o.erreur) o.erreur.classList.remove('on');
    if (o.secours) o.secours.classList.remove('on');

    var charge = Object.assign({}, donnees, {
      type: type,
      website: (document.querySelector('[name=website]') || {}).value || '',
      duree: Date.now() - EVN.ouvert,
      page: location.pathname
    });

    var fini = function (etat, reponse) {
      if (b) { b.removeAttribute('aria-busy'); b.disabled = false; b.textContent = libelle; }
      if (etat === 'ok') { alors(reponse); return; }
      if (etat === 'champs') {
        if (o.erreur) { o.erreur.textContent = reponse.message; o.erreur.classList.add('on'); }
        if (o.marquer) o.marquer(reponse.champs || []);
        return;
      }
      /* Ni succes ni faute du visiteur : on bascule sur WhatsApp. */
      if (o.secours) {
        var lien = o.secours.querySelector('a.wa');
        if (lien) lien.href = EVN.lienWhatsApp(o.resume ? o.resume() : 'Bonjour, je souhaite vous contacter.');
        o.secours.classList.add('on');
        o.secours.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    };

    if (!('fetch' in window)) { fini('secours', {}); return; }

    var minuteur = setTimeout(function () { fini('secours', {}); }, 12000);
    var repondu = false;
    fetch('/api/envoyer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(charge)
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) { return { s: r.status, j: j }; });
    }).then(function (x) {
      if (repondu) return; repondu = true; clearTimeout(minuteur);
      if (x.s === 200 && x.j.ok) fini('ok', x.j);
      else if (x.s === 422) fini('champs', x.j);
      else fini('secours', x.j);
    }).catch(function () {
      if (repondu) return; repondu = true; clearTimeout(minuteur);
      fini('secours', {});
    });
  }
};
"""

PIEGE = ('<div class="piege" aria-hidden="true">'
         '<label>Ne pas remplir<input type="text" name="website" tabindex="-1" autocomplete="off"></label>'
         '</div>')


def secours(id_='sec', phrase="Nous n'avons pas pu transmettre votre demande automatiquement."):
    """Panneau de repli : WhatsApp pre-rempli, telephone, e-mail."""
    return '''<div class="secours" id="%s" role="alert">
  <b>Envoyons-la autrement</b>
  <p>%s Votre message est prêt : il part sur WhatsApp en un clic, et la réception répond 24 h/24.</p>
  <div class="liens">
    <a class="wa" href="https://wa.me/2250546017377" target="_blank" rel="noopener">Envoyer sur WhatsApp</a>
    <a href="tel:+2250151527575">Appeler la réception</a>
    <a href="mailto:bonjour@evannathhotel.com">Écrire un e-mail</a>
  </div>
</div>''' % (id_, phrase)

EN_NAV = ('mn:"Menu",n1:"Rooms &amp; Suites",n2:"Experiences",n3:"The table",n4:"The spa",'
          'n5:"Packages &amp; Offers",n6:"Meetings &amp; groups",n7:"Gallery",n8:"About",'
          'n9:"Useful information",n10:"Contact",n11:"Book",dr:"Reservations",')


# ---------------------------------------------------------------------------
# Images responsives
# ---------------------------------------------------------------------------
# build-images.py produit les variantes NOM-640, NOM-1024, NOM-1600 en webp et
# en jpeg. Cette fonction les declare dans les balises deja ecrites.
#
# Les motifs sont volontairement etroits : ils ne remplacent qu'une VALEUR
# d'attribut, ne traversent jamais une balise et ne peuvent donc rien effacer.
# `data-full`, `href`, `content` et les URL absolues du JSON-LD ne matchent pas.
import os as _os
import re as _re

_W = (640, 1024, 1600)
# Un hero occupe toute la largeur ; le reste ne depasse jamais la colonne.
SIZES_HERO = '100vw'
SIZES_DEFAUT = '(max-width:720px) 100vw, (max-width:1100px) 60vw, 700px'


_largeur_cache = {}


def _largeur(chemin):
    """Largeur reelle du fichier, lue une seule fois. Sans elle, le dernier
    candidat du srcset n'aurait pas de descripteur `w` — or on ne peut pas
    melanger descripteurs `w` et candidats nus dans un meme srcset."""
    if chemin not in _largeur_cache:
        try:
            from PIL import Image
            _largeur_cache[chemin] = Image.open(chemin).size[0]
        except Exception:
            _largeur_cache[chemin] = None
    return _largeur_cache[chemin]


def _variantes(nom, ext):
    v = [(w, 'img/opt/%s-%d.%s' % (nom, w, ext)) for w in _W]
    v = [(w, p) for w, p in v if _os.path.exists(p)]
    plein = 'img/opt/%s.%s' % (nom, ext)
    w0 = _largeur(plein)
    if w0:
        v = [(w, p) for w, p in v if w < w0] + [(w0, plein)]
    return v


def responsive(html, hero=None):
    """Ajoute srcset + sizes aux <picture>/<img> qui ont des variantes."""

    def sizes_de(nom):
        return SIZES_HERO if hero and nom == hero else SIZES_DEFAUT

    def source(m):
        nom = m.group(1)
        v = _variantes(nom, 'webp')
        if len(v) < 2:
            return m.group(0)
        jeu = ', '.join('%s %dw' % (p, w) for w, p in v)
        return 'srcset="%s" sizes="%s"' % (jeu, sizes_de(nom))

    def image(m):
        avant, nom, apres = m.group(1), m.group(2), m.group(3)
        v = _variantes(nom, 'jpg')
        if len(v) < 2:
            return m.group(0)
        jeu = ', '.join('%s %dw' % (p, w) for w, p in v)
        return ('<img%ssrc="img/opt/%s.jpg" srcset="%s" sizes="%s"%s'
                % (avant, nom, jeu, sizes_de(nom), apres))

    html = _re.sub(r'srcset="img/opt/([\w-]+)\.webp"', source, html)
    html = _re.sub(r'<img([^<>]*?)src="img/opt/([\w-]+)\.jpg"([^<>]*?>)', image, html)
    return html


def page(title, desc, og, css, body, script, preload=None, slug=None, jsonld=''):
    pre = '\n<link rel="preload" as="image" href="img/opt/%s.webp" type="image/webp">' % preload if preload else ''
    if slug is not None:
        url = SITE + ('/' if slug in ('index', '') else '/' + slug)
        can = '\n<link rel="canonical" href="%s">\n<meta property="og:url" content="%s">' % (url, url)
    else:
        can = ''
    return '''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
%s<title>%s</title>
<meta name="description" content="%s">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="Hôtel Evannath">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:image" content="%s/img/opt/%s.jpg">
<meta name="twitter:card" content="summary_large_image">
%s%s
%s%s
%s
<style>
%s
%s
</style>
</head>
<body>

%s

<script>
%s
</script>
</body>
</html>
''' % (ROBOTS_META, title, desc, title, desc, SITE, og, ICONS, can, HEAD, pre, jsonld, HEAD_CSS, css,
       responsive(body, hero=preload), script)
