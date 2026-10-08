# -*- coding: utf-8 -*-
"""Genere recrutement.html : les postes ouverts, tels que l'hotel les publie.

POURQUOI CETTE PAGE EXISTE, ET CE QU'ELLE N'EST PAS.

Elle ne TROUVE pas de candidats. Les visiteurs de ce site cherchent une
chambre, pas un emploi, et le site est en mode prospection — invisible des
moteurs. En Cote d'Ivoire, pour un poste en hotellerie a Assinie, les
candidats viennent de Facebook, de WhatsApp et du bouche-a-oreille ; le pied
de page annonce 21 000 abonnes sur Facebook, et cette page part de zero.

Facebook reste donc le CANAL. Cette page est la DESTINATION : une
publication disparait du fil en trois jours, les details se perdent dans les
commentaires, et six mois plus tard plus personne ne retrouve l'annonce. Ici
l'offre est entiere, le lien est permanent, et un seul endroit dit comment
postuler.

TROIS CONSEQUENCES, ecrites dans le code plus bas :

  1. CHAQUE OFFRE A SON ANCRE. recrutement.html#poste-receptionniste-de-nuit :
     une publication pointe sur UN poste, pas sur la liste.
  2. LE TELEPHONE D'ABORD. Le trafic viendra d'un lien ouvert dans le
     navigateur d'un telephone.
  3. PAS DANS LE MENU PRINCIPAL. Le menu est le parcours d'un client qui
     reserve. Le lien vit dans le pied de page ; les candidats arrivent par
     un lien direct.

LE CONTENU N'EST PAS DANS CETTE PAGE. Les offres vivent dans le magasin et
se lisent a l'ouverture, comme les promotions. Une offre publiee apparait
sans regenerer le site, et une offre dont la date de fin est passee ne sort
meme pas du serveur.

TROIS ETATS, ET LE TROISIEME EST LA RAISON D'ETRE DU RESTE. Aucune offre
n'est pas la meme chose qu'une panne : un reseau coupe qui afficherait
« aucun poste ouvert » ferait croire a un candidat qu'il n'y a rien. On dit
alors qu'on n'arrive pas a afficher, et on donne le contact.

LA PORTE D'ENTREE (maquette 6a, « la case et la conversation »).
La photo d'equipe est une mosaique ; la case du logo et de l'affiche VISA
est recouverte d'un « Vous ? ». A cote, l'hotel ecrit au candidat comme sur
WhatsApp : il choisit un poste parmi les offres du magasin, la case de la
personne qui fait ce metier s'allume, et l'offre arrive en reponse. La
conversation n'est qu'une porte : chaque bulle d'offre renvoie au bloc
complet plus bas, qui reste la reference — ancre, texte entier, date
limite, lien a copier.

La correspondance poste -> case se devine a partir de l'intitule et du
departement (CASES, plus bas). Un poste sans case (chauffeur, bar...) arrive
sans photo, et aucune case ne s'allume : on ne met pas le visage de
quelqu'un sur un metier qu'il ne fait pas.
"""
import io
import json
import _schema
from _chrome import page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV, WA, MAIL, medaillon, PAGNE_CSS

KENTE = "repeating-linear-gradient(90deg,#C9842F 0 22px,#2B1B12 22px 26px,#E7D7B8 26px 40px,#B8402B 40px 48px,#2B1B12 48px 52px,#3F7A4A 52px 60px,#C9842F 60px 74px)"

CSS = """
body{background:var(--bark)}

/* --- La porte d'entree : mosaique + conversation, aux couleurs des tenues
   (beige des polos, brun, liseres kente). --- */
.rc{background:#F3EBDD;color:#2B1B12}
.rc-k{height:10px;background:""" + KENTE + """}
.rc-in{max-width:1200px;margin:0 auto;padding:140px 32px 64px;display:grid;
  grid-template-columns:minmax(0,5fr) minmax(0,6fr);gap:56px;align-items:start}
.rc .eyebrow{color:#8A5524}
.rc h1{color:#3A2416;font-size:clamp(2.3rem,5vw,3.8rem);line-height:1.03;margin:12px 0 18px}
.rc .lede{color:#5A4636;max-width:40ch;font-size:1.05rem;line-height:1.65;margin:0}
.rc-mos{position:relative;aspect-ratio:1/1;overflow:hidden;border-radius:4px;background:#2B1B12;
  margin-top:30px;box-shadow:0 40px 70px -30px rgba(58,36,22,.55)}
.rc-mos img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.rc-t{position:absolute;outline:4px solid rgba(224,164,88,0);outline-offset:-4px;
  transition:box-shadow .6s ease,outline-color .6s ease;pointer-events:none}
.rc-mos.sel .rc-t{box-shadow:inset 0 0 0 2000px rgba(43,27,18,.5)}
.rc-mos.sel .rc-t.on{box-shadow:none;outline-color:#E0A458}
.rc-vous{position:absolute;left:31.2%;top:60.35%;width:37.3%;height:39.65%;background:#F3EBDD;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;text-align:center}
.rc-vous:before{content:"";position:absolute;inset:7%;border:2px dashed #8A5524;border-radius:3px}
.rc-vous b{font-family:var(--f-display);font-weight:400;font-size:clamp(1.3rem,3.2vw,2.3rem);line-height:1;color:#3A2416}
.rc-vous span{font-size:12px;line-height:1.4;color:#6E5643;max-width:14ch}

.rc-tel{background:#E9DDC9;border-radius:28px;height:720px;display:flex;flex-direction:column;
  overflow:hidden;box-shadow:0 40px 80px -30px rgba(58,36,22,.5)}
.rc-tete{display:flex;align-items:center;gap:12px;padding:14px 18px;background:#3A2416;color:#F3EBDD}
.rc-logo{width:40px;height:40px;flex:0 0 auto;border-radius:50%;border:1.5px solid #E0A458;
  background:#2B1B12 url(img/opt/logo-creme.png) center/70% auto no-repeat}
.rc-tete .n{flex:1;display:flex;flex-direction:column;line-height:1.3}
.rc-tete .n b{font-size:15px}
.rc-tete .n span{font-size:12px;color:#E0A458}
.rc-re{background:none;border:1px solid rgba(243,235,221,.3);color:#F3EBDD;height:34px;padding:0 14px;
  border-radius:17px;font:700 11px var(--f-body);letter-spacing:.12em;text-transform:uppercase;cursor:pointer}
.rc-k6{height:6px;flex:0 0 auto;background:""" + KENTE + """}
.rc-fil{flex:1;min-height:0;overflow-y:auto;padding:22px 18px 28px;display:flex;flex-direction:column;gap:10px}
.rc-l{display:flex;align-items:flex-end;gap:10px;animation:rc-bulle .5s cubic-bezier(.2,.9,.3,1.2) both}
.rc-l.moi{justify-content:flex-end}
.rc-l .rc-logo{width:32px;height:32px;border:0;background-color:#3A2416}
.rc-l .rc-logo.cache{visibility:hidden}
.rc-b{max-width:76%;padding:11px 15px;border-radius:18px 18px 18px 6px;background:#FBF7F0;
  color:#2B1B12;font-size:15px;line-height:1.5;box-shadow:0 1px 1px rgba(0,0,0,.06)}
.rc-l.moi .rc-b{background:#E0A458;border-radius:18px 18px 6px 18px}
.rc-pts{display:flex;gap:4px;padding:15px 16px}
.rc-pts i{width:7px;height:7px;border-radius:50%;background:#3A2416;animation:rc-pt 1.2s infinite}
.rc-pts i:nth-child(2){animation-delay:.15s}.rc-pts i:nth-child(3){animation-delay:.3s}
.rc-o{width:82%;background:#3A2416;color:#F3EBDD;border-radius:18px 18px 18px 6px;overflow:hidden;
  box-shadow:0 10px 24px -12px rgba(58,36,22,.6)}
.rc-o .ph{aspect-ratio:3/2;overflow:hidden}
.rc-o .ph img{display:block;max-width:none;height:auto}
.rc-o .k{height:8px;background:""" + KENTE + """}
.rc-o .c{padding:18px 20px 20px;display:flex;flex-direction:column;gap:8px}
.rc-o .m{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#E0A458;font-weight:700}
.rc-o h2{font-size:1.6rem;margin:0;color:#F3EBDD}
.rc-o p{margin:0;font-size:14.5px;line-height:1.55;color:#DCCDB6}
.rc-o .g{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px}
.rc-o .g a{display:inline-flex;align-items:center;min-height:44px;padding:0 20px;border-radius:22px;
  font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;border:1px solid #E0A458;color:#E0A458}
.rc-o .g a.p{background:#E0A458;color:#2B1B12}
.rc-ch{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:8px;margin-top:4px;animation:rc-bulle .5s ease both}
.rc-ch button,.rc-ch a{min-height:44px;padding:0 18px;border-radius:22px;border:1.5px solid #3A2416;background:#FBF7F0;
  color:#3A2416;font:600 14px var(--f-body);cursor:pointer;display:inline-flex;align-items:center}
.rc-ch button:hover,.rc-ch a:hover{background:#3A2416;color:#F3EBDD}
.rc-pied{max-width:1200px;margin:0 auto;padding:0 32px 56px}
.rc-pied p{margin:0;border-top:1px solid rgba(58,36,22,.2);padding-top:26px;font-family:var(--f-display);
  font-size:clamp(1.15rem,2.4vw,1.5rem);color:#3A2416}
.rc-pied a{color:#8A5524}
@keyframes rc-bulle{from{opacity:0;transform:translateY(10px) scale(.96)}to{opacity:1;transform:none}}
@keyframes rc-pt{0%,60%,100%{opacity:.3;transform:none}30%{opacity:1;transform:translateY(-3px)}}

.postes{padding:56px 0 96px}
.postes > .wrap > h2{font-size:clamp(1.6rem,3.4vw,2.2rem);margin:0 0 26px}
/* Une offre par bloc, pleine largeur : une grille de cartes obligerait a
   resumer, et un resume d'offre d'emploi est une offre incomplete. */
.poste{border:1px solid var(--line);background:var(--bark-2);padding:30px 32px;
  margin-bottom:18px;scroll-margin-top:110px}
.poste:target{border-color:var(--bronze);box-shadow:0 0 0 1px rgba(185,138,80,.35)}
.poste h2{font-size:1.5rem;font-weight:400;margin-bottom:8px}
.poste .meta{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px}
/* La date limite : sous l'intitule, discrete. Un candidat la cherche avant
   de lire le reste. */
.poste .fin{font-size:13px;color:var(--muted);margin:-8px 0 18px}
.poste .fin time{color:var(--cream);font-weight:600}
.poste .meta span{font-size:10px;letter-spacing:.16em;text-transform:uppercase;
  font-weight:700;color:var(--bronze-2);border:1px solid var(--line);padding:5px 11px}
/* white-space:pre-line — l'hotel ecrit ses missions une par ligne. Les
   ecraser en un pave rendrait l'offre illisible sur un telephone. */
.poste .corps{white-space:pre-line;font-size:15.5px;color:var(--prose);
  max-width:72ch;margin-bottom:18px}
.poste h3{font-size:10px;letter-spacing:.2em;text-transform:uppercase;
  color:var(--bronze);font-weight:700;margin:22px 0 8px}
.poste .post{border-top:1px solid var(--line);margin-top:24px;padding-top:20px;
  display:flex;flex-wrap:wrap;gap:14px;align-items:center}
.poste .post p{font-size:15px;margin:0}
.poste .post b{color:var(--cream);font-weight:600}
.poste .lien{font-size:12.5px;color:var(--muted);border:0;background:none;
  cursor:pointer;padding:0;letter-spacing:.04em}
.poste .lien:hover{color:var(--bronze-2)}
.poste .lien.fait{color:var(--palm)}

/* Les trois etats de la liste. Le dernier n'est pas une politesse : un
   reseau coupe qui dirait « aucun poste » ferait croire qu'il n'y a rien. */
.etat{border:1px solid var(--line);background:var(--bark-2);padding:44px 32px;
  text-align:center}
/* Signature textile — touche 3 sur 5. Le medaillon coiffe le bloc vide.
   Le padding du bloc l'ecarte deja du bord ; le margin-bottom pose les
   12 px demandes entre lui et la premiere ligne. */
.pagne-vide{width:96px;margin:0 auto 14px;color:#A88560}
.etat p{color:var(--muted);font-size:15.5px;margin:0 auto;max-width:48ch}
.etat .g{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:24px}
.etat.mal{border-color:rgba(166,58,37,.4)}

/* Le telephone d'abord : la mosaique passe au-dessus, la conversation
   dessous, a hauteur d'ecran. */
@media(max-width:900px){
  .rc-in{grid-template-columns:minmax(0,1fr);gap:28px;padding:120px 20px 40px}
  .rc-mos{max-width:520px}
  .rc-tel{height:min(640px,82vh);border-radius:22px}
  .rc-pied{padding:0 20px 44px}
}
@media(max-width:720px){
  .postes{padding:40px 0 70px}
  .poste{padding:24px 20px}
  .poste .post{flex-direction:column;align-items:flex-start;gap:10px}
  .rc-b{max-width:84%}.rc-o{width:92%}
}
@media(prefers-reduced-motion:reduce){.rc-l,.rc-ch{animation:none}.rc-pts i{animation:none;opacity:.6}}
"""
# Les cinq touches textiles : ce morceau ne part que sur les pages qui
# en portent une.
# Les utilitaires D'ABORD, les placements ensuite : a specificite egale
# c'est la derniere regle qui gagne, et ce sont les placements qui
# doivent gagner. Dans l'autre sens, `.pagne-damas{position:absolute}`
# ecrasait le `position:relative` du placement, et le motif sortait du
# flux — largeur zero, invisible, et le test passait au vert.
CSS = PAGNE_CSS + CSS

# Les cases de la mosaique (img/equipe-2.jpg), en % de la photo. L'ordre
# compte : c'est l'index que CASE() renvoie.
# Mesurees sur la photo livree (2000 x 2000) : lignes de separation a
# 43,2 % et 60,35 % en hauteur ; colonnes a 31,5 % / 68,5 % en haut et en
# bas, a 43,15 % au milieu.
TUILES = [('0%', '0%', '31.5%', '43.2%'),         # 0 salle : la serveuse au plateau
          ('0%', '43.2%', '43.15%', '17.15%'),    # 1 cuisine : la brigade
          ('0%', '60.35%', '31.2%', '39.65%'),    # 2 chambres : le lit
          ('68.5%', '60.35%', '31.5%', '39.65%')]  # 3 reception
tuiles = ''.join('<i class="rc-t" style="left:%s;top:%s;width:%s;height:%s"></i>' % t for t in TUILES)

b = [header('index.html#reserver', 'Réserver'), drawer(''), '''
<section class="rc">
  <div class="rc-k"></div>
  <div class="rc-in">
    <div>
      <span class="eyebrow" data-t="eb">Recrutement · Assinie PK19</span>
      <h1 data-t="h1">Il reste une case pour vous.</h1>
      <p class="lede" data-t="lede">Pas de formulaire. Dites-nous ce qui vous plaît, on vous montre le poste.</p>
      <div class="rc-mos" id="mos">
        <img src="img/equipe-2.jpg" width="2000" height="2000" alt="L'équipe de l'Hôtel Evannath au travail">
        ''' + tuiles + '''
        <div class="rc-vous"><b data-t="vous">Vous ?</b><span data-t="place">Votre place est ici.</span></div>
      </div>
    </div>
    <div class="rc-tel" role="log" aria-live="polite" aria-label="Conversation avec l'Hôtel Evannath">
      <div class="rc-tete">
        <span class="rc-logo"></span>
        <span class="n"><b>Hôtel Evannath</b><span data-t="sous">Recrutement · Assinie</span></span>
        <button type="button" class="rc-re" id="re" data-t="re">Recommencer</button>
      </div>
      <div class="rc-k6"></div>
      <div class="rc-fil" id="fil"></div>
    </div>
  </div>
  <div class="rc-pied"><p><span data-t="dir">Vous préférez écrire directement ?</span>
    <a href="mailto:''' + MAIL + '''">''' + MAIL + '''</a></p></div>
  <div class="rc-k"></div>
</section>

<section class="postes">
  <div class="wrap narrow">
    <h2 data-t="tous">Toutes les offres</h2>
    <div id="liste">
      <div class="etat"><p data-t="charge">Chargement des offres…</p></div>
    </div>
  </div>
</section>

''' + FOOTER]

# Le rendu se fait a l'ouverture : les offres vivent dans le magasin, pas
# dans cette page. Aucun cache — une offre retiree doit disparaitre a la
# seconde, et la reponse fait quelques centaines d'octets.
JS = NAV_JS + '''

(function () {
  /* Le medaillon est pose a la GENERATION, pas recopie ici : une seule
     source, le fichier SVG. */
  var MED = ''' + json.dumps(medaillon('carre', 'pagne-vide')) + ''';
  var liste = document.getElementById('liste');
  var fil = document.getElementById('fil');
  var mos = document.getElementById('mos');
  if (!liste) return;
  var REDUIT = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  function ech(t) {
    return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function plat(t) {
    return String(t || '').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
  }

  /* L'ancre d'une offre : son intitule, reduit a ce qui tient dans une URL.
     Elle doit survivre a une modification du texte, d'ou l'identifiant en
     secours si le titre ne donne rien d'utilisable. */
  function ancre(o) {
    var s = plat(o.titre).replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    return 'poste-' + (s || String(o.id || '').slice(0, 8));
  }

  /* Quelle case de la mosaique pour ce poste ? La cuisine d'abord : un
     « commis de cuisine » n'est pas en salle. -1 : pas de case. */
  function CASE(o) {
    var s = plat((o.titre || '') + ' ' + (o.departement || ''));
    if (/cuisi|commis|patiss|plonge/.test(s)) return 1;
    if (/serv|salle|rang|restaurant/.test(s)) return 0;
    if (/chambre|heberg|menage|gouvern|housekeep|lingerie|valet/.test(s)) return 2;
    if (/recep|accueil|concierge|front/.test(s)) return 3;
    return -1;
  }
  /* Le cadrage de chaque case dans une vignette 3:2 (largeur et decalages
     en % de la vignette). Recalcule si la photo change. */
  var CADRE = [['317.46%', '0%', '-35.24%'], ['388.73%', '-33.87%', '-167.93%'],
               ['320.51%', '0%', '-223.64%'], ['317.46%', '-217.46%', '-221.19%']];

  /* « Comment postuler » est ecrit par l'hotel, et affiche tel quel. Si
     une adresse y figure, on en fait un lien ; sinon c'est une consigne,
     et une consigne ne se clique pas. */
  function postuler(o) {
    var p = String(o.postuler || '').trim();
    var mail = p.match(/[\\w.+-]+@[\\w-]+\\.[\\w.-]+/);
    var tel = p.match(/\\+?[0-9][0-9 ().-]{7,}/);
    if (mail) return { href: 'mailto:' + mail[0] + '?subject='
      + encodeURIComponent('Candidature — ' + (o.titre || '')), txt: mail[0], lien: true };
    if (tel) return { href: 'tel:' + tel[0].replace(/[^+0-9]/g, ''), txt: p, lien: true };
    if (p) return { txt: p, lien: false };
    return null;
  }

  function bloc(o) {
    var id = ancre(o);
    var meta = [o.contrat, o.departement].filter(Boolean)
      .map(function (m) { return '<span>' + ech(m) + '</span>'; }).join('');
    var profil = o.profil
      ? '<h3 data-t="pr">Profil recherché</h3><div class="corps">' + ech(o.profil) + '</div>'
      : '';
    var p = postuler(o), comment;
    if (p && p.lien) {
      comment = '<p><b data-t="cp">Pour postuler</b> — <a href="' + ech(p.href) + '">' + ech(p.txt) + '</a></p>';
    } else if (p) {
      comment = '<p><b data-t="cp">Pour postuler</b> — ' + ech(p.txt) + '</p>';
    } else {
      /* Rien n'a ete precise : on renvoie vers le chemin que le site porte
         deja, plutot que d'inventer une adresse de recrutement. */
      comment = '<p><b data-t="cp">Pour postuler</b> — <a href="contact.html"'
        + ' data-t="cc">écrivez-nous par la page Contact</a></p>';
    }
    /* La date limite, si l'hotel en a pose une. Le texte de la date est ecrit
       par EVN_LANG, dans la langue de la page. */
    var fin = /^\\d{4}-\\d{2}-\\d{2}$/.test(o.fin || '')
      ? '<p class="fin"><span data-t="jq">Candidatures jusqu\\'au</span> '
        + '<time datetime="' + o.fin + '"></time></p>'
      : '';
    return '<article class="poste" id="' + id + '">'
      + '<h2>' + ech(o.titre) + '</h2>'
      + (meta ? '<div class="meta">' + meta + '</div>' : '')
      + fin
      + '<div class="corps">' + ech(o.texte) + '</div>'
      + profil
      + '<div class="post">' + comment
      + '<button type="button" class="lien" data-copier="' + id + '"'
      + ' data-t="cl">Copier le lien de cette offre</button>'
      + '</div></article>';
  }

  var VIDE = '<div class="etat">' + MED
    + '<p data-t="vide">Aucun poste n\\'est ouvert en ce moment. '
    + 'Les offres paraissent ici et sur notre page Facebook.</p>'
    + '<div class="g"><a class="btn" href="https://www.facebook.com/evannathhotel"'
    + ' target="_blank" rel="noopener" data-t="fb">Suivre sur Facebook</a></div></div>';

  /* La panne se dit. Elle ne se deguise pas en « aucun poste ». */
  var PANNE = '<div class="etat mal"><p data-t="panne">Nous n\\'arrivons pas à afficher '
    + 'les offres pour le moment. Réessayez dans un instant, ou écrivez-nous.</p>'
    + '<div class="g"><a class="btn" href="https://wa.me/''' + WA + '''"'
    + ' target="_blank" rel="noopener" data-t="wa">Écrire sur WhatsApp</a>'
    + '<a class="btn" href="mailto:''' + MAIL + '''" data-t="ml">''' + MAIL + '''</a></div></div>';

  /* ---------- La conversation ----------
     Ses phrases sont dans les deux langues ici, pas dans data-t : elles
     s'ecrivent au fil du temps, et un changement de langue relance la
     conversation depuis le debut. */
  var DIT = {
    fr: { a: 'Bonjour !', b: "Nous cherchons des collègues pour l'Hôtel Evannath, à Assinie.",
      n1: 'Un poste est ouvert. Il vous intéresse ?', nx: ' postes sont ouverts. Lequel vous intéresse ?',
      autre: 'Un autre poste vous intéresse ?', vu: 'Voici le poste.',
      vide: "Aucun poste n'est ouvert en ce moment. Les offres paraissent ici et sur notre page Facebook.",
      panne: "Nous n'arrivons pas à afficher les offres pour le moment. Écrivez-nous, on vous répond.",
      post: 'Je postule', lire: "Lire l'offre", fb: 'Suivre sur Facebook', wa: 'Écrire sur WhatsApp' },
    en: { a: 'Hello!', b: 'We are looking for colleagues at the Hôtel Evannath, in Assinie.',
      n1: 'One position is open. Interested?', nx: ' positions are open. Which one interests you?',
      autre: 'Interested in another position?', vu: 'Here is the position.',
      vide: 'No position is open at the moment. Listings appear here and on our Facebook page.',
      panne: 'We cannot display the listings right now. Write to us and we will answer.',
      post: 'Apply', lire: 'Read the listing', fb: 'Follow on Facebook', wa: 'Message on WhatsApp' }
  };
  var NB = { fr: ['', 'Un', 'Deux', 'Trois', 'Quatre', 'Cinq', 'Six', 'Sept', 'Huit', 'Neuf', 'Dix'],
             en: ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten'] };
  var OFFRES = null, ETAT = 'charge', minuteurs = [];
  function lg() { return document.documentElement.lang === 'en' ? 'en' : 'fr'; }
  function plus(fn, ms) { minuteurs.push(setTimeout(fn, REDUIT ? 0 : ms)); }
  function bas() { fil.scrollTo({ top: fil.scrollHeight, behavior: REDUIT ? 'auto' : 'smooth' }); }
  function ligne(html, moi) {
    var pts = fil.querySelector('.rc-pts');
    if (pts) pts.parentNode.remove();
    var prec = fil.lastElementChild;
    if (!moi && prec && !prec.classList.contains('moi')) {
      var l = prec.querySelector('.rc-logo'); if (l) l.classList.add('cache');
    }
    var d = document.createElement('div');
    d.className = 'rc-l' + (moi ? ' moi' : '');
    d.innerHTML = (moi ? '' : '<span class="rc-logo"></span>') + html;
    fil.appendChild(d); bas(); return d;
  }
  /* Les bulles de l'hotel arrivent l'une apres l'autre, chacune precedee
     des trois points : on lit au rythme ou l'on ecrirait. */
  function dire(liste_, t0, fin_) {
    var t = t0 || 300;
    liste_.forEach(function (h) {
      plus(function () { if (!fil.querySelector('.rc-pts')) ligne('<div class="rc-b rc-pts"><i></i><i></i><i></i></div>'); }, t);
      t += 850;
      plus(function () { ligne(h); }, t);
      t += 320;
    });
    if (fin_) plus(fin_, t);
  }
  function bulle(t) { return '<div class="rc-b">' + ech(t) + '</div>'; }
  function choix() {
    var d = document.createElement('div');
    d.className = 'rc-ch';
    d.innerHTML = OFFRES.map(function (o, i) {
      return '<button type="button" data-i="' + i + '">' + ech(o.titre) + '</button>';
    }).join('');
    fil.appendChild(d); bas();
  }
  function allume(c) {
    mos.classList.toggle('sel', c >= 0);
    mos.querySelectorAll('.rc-t').forEach(function (t, k) { t.classList.toggle('on', k === c); });
  }
  function carte(o) {
    var D = DIT[lg()], c = CASE(o), p = postuler(o);
    var ph = c >= 0 ? '<div class="ph"><img src="img/equipe-2.jpg" width="2000" height="2000" alt="" style="width:' + CADRE[c][0]
      + ';margin-left:' + CADRE[c][1] + ';margin-top:' + CADRE[c][2] + '"></div>' : '';
    var meta = [o.contrat, o.departement].filter(Boolean).map(ech).join(' · ');
    var acc = String(o.texte || '').split(/\\n/).filter(function (x) { return x.trim(); })[0] || '';
    return '<div class="rc-o">' + ph + '<div class="k"></div><div class="c">'
      + (meta ? '<span class="m">' + meta + '</span>' : '')
      + '<h2>' + ech(o.titre) + '</h2>'
      + (acc ? '<p>' + ech(acc) + '</p>' : '')
      + '<div class="g">'
      + (p && p.lien ? '<a class="p" href="' + ech(p.href) + '">' + D.post + '</a>' : '')
      + '<a href="#' + ancre(o) + '">' + D.lire + '</a></div></div></div>';
  }
  function choisir(i) {
    var o = OFFRES[i];
    var ch = fil.querySelector('.rc-ch'); if (ch) ch.remove();
    ligne(bulle(o.titre), true);
    allume(CASE(o));
    dire([bulle(DIT[lg()].vu), carte(o)], 200, function () {
      if (OFFRES.length > 1) dire([bulle(DIT[lg()].autre)], 400, choix);
    });
  }
  function demarre() {
    minuteurs.forEach(clearTimeout); minuteurs = [];
    fil.innerHTML = ''; allume(-1);
    var D = DIT[lg()];
    if (ETAT === 'charge') return;
    if (ETAT === 'panne') {
      dire([bulle(D.a), bulle(D.panne)], 300, function () {
        var d = document.createElement('div'); d.className = 'rc-ch';
        d.innerHTML = '<a href="https://wa.me/''' + WA + '''" target="_blank" rel="noopener">' + D.wa + '</a>'
          + '<a href="mailto:''' + MAIL + '''">''' + MAIL + '''</a>';
        fil.appendChild(d); bas();
      });
      return;
    }
    if (!OFFRES.length) {
      dire([bulle(D.a), bulle(D.vide)], 300, function () {
        var d = document.createElement('div'); d.className = 'rc-ch';
        d.innerHTML = '<a href="https://www.facebook.com/evannathhotel" target="_blank" rel="noopener">' + D.fb + '</a>';
        fil.appendChild(d); bas();
      });
      return;
    }
    var n = OFFRES.length;
    var q = n === 1 ? D.n1 : (NB[lg()][n] || n) + D.nx;
    dire([bulle(D.a), bulle(D.b), bulle(q)], 300, choix);
  }
  if (fil) {
    fil.addEventListener('click', function (e) {
      var b = e.target.closest('[data-i]');
      if (b) choisir(+b.dataset.i);
    });
    document.getElementById('re').addEventListener('click', demarre);
  }

  fetch('/api/admin?a=public', { cache: 'no-store' })
    .then(function (r) { if (!r.ok) throw new Error('indisponible'); return r.json(); })
    .then(function (j) {
      var offres = (j && j.emplois) || [];
      OFFRES = offres; ETAT = 'ok';
      if (!offres.length) { liste.innerHTML = VIDE; return; }
      liste.innerHTML = offres.map(bloc).join('');
      /* Arrive par un lien vers une offre precise : on l'amene dessus une
         fois la liste posee. L'ancre du document a ete lue avant que le
         bloc n'existe, le navigateur n'a donc rien pu faire. */
      if (location.hash) {
        var cible = document.getElementById(location.hash.slice(1));
        if (cible) cible.scrollIntoView();
      }
    })
    .catch(function () { ETAT = 'panne'; liste.innerHTML = PANNE; })
    .then(function () {
      /* 01 · Le medaillon n'existe qu'APRES la reponse du serveur : il est
         dans le bloc vide, injecte ici. L'observateur doit donc tourner
         maintenant — lance au chargement, il n'aurait rien trouve, et le
         medaillon serait reste invisible, bloque a son etat de depart. */
      if (window.EVN_AU_SCROLL) window.EVN_AU_SCROLL('.pagne-vide', 'vu');
      /* Les offres arrivent APRES la traduction de la page : un visiteur
         venu en anglais voyait « Profil recherche », « Pour postuler » en
         francais. Leurs libelles rejoignent le dictionnaire francais (pour
         revenir au francais), puis la langue courante est reappliquee. */
      liste.querySelectorAll('[data-t]').forEach(function (e) {
        if (!(e.dataset.t in FR)) FR[e.dataset.t] = e.innerHTML;
      });
      if (document.documentElement.lang === 'en') EVN_LANGUE('en', false);
      else EVN_LANG('fr');
    });

  /* Les dates limites, dans la langue de la page. Appelee par le chassis a
     chaque changement de langue. Midi, et non minuit : une date seule lue
     a minuit UTC tomberait la veille selon le fuseau. La conversation
     repart dans la nouvelle langue. */
  var derniere = null;
  window.EVN_LANG = function (lg_) {
    var loc = lg_ === 'en' ? 'en-GB' : 'fr-FR';
    liste.querySelectorAll('time[datetime]').forEach(function (t) {
      t.textContent = new Date(t.getAttribute('datetime') + 'T12:00:00')
        .toLocaleDateString(loc, { day: 'numeric', month: 'long', year: 'numeric' });
    });
    if (fil && ETAT !== 'charge' && derniere !== lg_) { derniere = lg_; demarre(); }
  };

  /* Copier le lien d'une offre : c'est le geste qui sert a la publier sur
     Facebook ou a l'envoyer par WhatsApp. */
  liste.addEventListener('click', function (e) {
    var b = e.target.closest('[data-copier]');
    if (!b) return;
    var url = location.origin + location.pathname + '#' + b.dataset.copier;
    var fait = function () {
      b.textContent = b.dataset.ok || 'Lien copié';
      b.classList.add('fait');
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(fait, function () { location.hash = b.dataset.copier; });
    } else {
      location.hash = b.dataset.copier;
    }
  });
}());

var EN={''' + EN_NAV + '''cta:"Book now",
eb:"Recruitment · Assinie PK19",h1:"There is a place left for you.",
lede:"No form. Tell us what you enjoy, we show you the position.",
vous:"You?",place:"Your place is here.",sous:"Recruitment · Assinie",re:"Restart",
dir:"Prefer to write directly?",tous:"All listings",
charge:"Loading the listings…",
pr:"Who we are looking for",jq:"Applications until",cp:"To apply",cc:"write to us from the Contact page",
cl:"Copy the link to this listing",
vide:"No position is open at the moment. Listings appear here and on our Facebook page.",
fb:"Follow on Facebook",
panne:"We cannot display the listings right now. Try again in a moment, or write to us.",
wa:"Message on WhatsApp",ml:"''' + MAIL + '''"};

''' + LANG_JS

LD = _schema.bloc(
    _schema.hotel(),
    _schema.fil([('Accueil', 'index'), ('Nous rejoindre', None)]))

# PAS de noindex, contrairement a reserver, mentions-legales et 404. C'est la
# page du site qui gagne le PLUS a etre indexee : on cherche un emploi sur
# Google. Tant que le site est en mode prospection, le chassis pose le
# noindex global — le jour ou il tombe, cette page est prete.
html = page(
 "Nous rejoindre — Hôtel Evannath, Assinie",
 "Les postes ouverts à l'Hôtel Evannath, Assinie PK 19. Réception, "
 "restauration, chambres : les offres en cours et comment postuler.",
 "g-entree", CSS, '\n'.join(b), JS, slug="recrutement", jsonld=LD)

io.open('recrutement.html', 'w', encoding='utf-8').write(html)
print('recrutement.html      ok')
