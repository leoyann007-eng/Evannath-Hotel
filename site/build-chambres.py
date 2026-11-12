# -*- coding: utf-8 -*-
"""Genere les 7 fiches chambres a partir d'un seul gabarit.

Tarifs, capacites et intitules proviennent du catalogue reel de l'hotel
(API WooCommerce de evannathhotel.com). Les conditions de sejour sont
des hypotheses a faire confirmer — voir README.
"""
import io
import _schema
from _chrome import NOTE_GOOGLE, FICHE_GOOGLE
from _chrome import (page, header, drawer, FOOTER, NAV_JS, LANG_JS, EN_NAV, WA,
                     REMISE_JS, REMISE_CSS, DISPO_JS, PAGNE_CSS, PAGNE_JS)

# slug, nom, prix, capacite, resume, accroche, 3 paragraphes, equipements+, photos
from _chambres import CHAMBRES
import _chambres_en
import json

PAR_SLUG = {c['slug']: c for c in CHAMBRES}

# Le pictogramme de chacun des quatre points forts, d'apres son libelle.
_P = {
 'pers': '<circle cx="9" cy="8" r="3.4"/><path d="M2.5 20a6.5 6.5 0 0113 0M16 5.2a3.4 3.4 0 010 5.6M18 14.4a6.5 6.5 0 013.5 5.6"/>',
 'lit': '<path d="M2 5v14M2 9h17a3 3 0 013 3v7M2 16h20M6 9v7"/>',
 'eau': '<path d="M2 17c2 1 4-1 6 0s4 1 6 0 4-1 6 0M2 12c2 1 4-1 6 0s4 1 6 0 4-1 6 0"/><circle cx="17" cy="6" r="2.5"/>',
 'jardin': '<path d="M12 21v-9M12 12c0-4 3-7 7-7 0 4-3 7-7 7zM12 15c0-3-2-5-6-5 0 3 2 5 6 5z"/>',
 'salon': '<path d="M4 12V8a2 2 0 012-2h12a2 2 0 012 2v4M2 13a2 2 0 014 0v3h12v-3a2 2 0 014 0v5H2zM6 18v2M18 18v2"/>',
 'soleil': '<circle cx="12" cy="13" r="4"/><path d="M12 3v3M4.2 6.2l2.1 2.1M19.8 6.2l-2.1 2.1M2 13h3M19 13h3M3 20h18"/>',
 'tasse': '<path d="M4 9h13v5a5 5 0 01-5 5H9a5 5 0 01-5-5zM17 10h1.5a2.5 2.5 0 010 5H17M8 3v3M12 3v3"/>',
 'table': '<path d="M3 8h18M5 8v11M19 8v11M8 8V5h8v3"/>',
 'motif': '<path d="M12 2l10 10-10 10L2 12z"/><path d="M12 7l5 5-5 5-5-5z"/>',
 'duplex': '<path d="M3 20h18M3 20V5h8v6h10v9M11 11H3"/>',
 'escalier': '<path d="M3 20h4v-4h4v-4h4V8h4V4"/>',
 'toit': '<path d="M3 12l9-8 9 8M5 10.5V20h14v-9.5"/>',
}
_PICTO = {'personnes': 'pers', 'lit': 'lit', 'lits': 'lit', 'chambres': 'lit',
          'coin': 'salon', 'séparé': 'salon', 'complet': 'salon', 'privatif': 'salon',
          'exposition': 'soleil', 'petit-déjeuner': 'tasse', 'salle à manger': 'table',
          'textiles': 'motif', 'décor': 'motif', 'volume': 'duplex', 'escalier': 'escalier',
          'sous': 'toit', 'terrasse': 'jardin'}


def picto(val, lab):
    """« Lagune vue » montre l'eau, « Jardin vue » le jardin."""
    if lab == 'vue':
        return _P['eau' if val == 'Lagune' else 'jardin']
    return _P[_PICTO.get(lab, 'motif')]


def nom_accentue(nom):
    """Le dernier mot du nom en italique, comme le titre de l'accueil.
    « Deluxe · lits à baldaquin » : ce qui suit le point median."""
    if ' · ' in nom:
        a, b = nom.split(' · ', 1)
        return '%s · <em>%s</em>' % (a, b)
    a, _, b = nom.rpartition(' ')
    return '%s <em>%s</em>' % (a, b) if a else nom


# Le mot d'un client, avant la reservation. Ce sont les avis de l'accueil ;
# ils tournent d'une fiche a l'autre pour ne pas dire sept fois la meme chose.
AVIS = [
 ("Depuis la réservation jusqu'à mon départ, tout s'est très bien passé. Chambre propre, personnel accueillant et bienveillant. Rien à dire.", 'Mme Diakité'),
 ("La balade lagunaire est magnifique, le cadre très cosy et le personnel très accueillant. Franchement, j'ai adoré.", 'M. Jean-Michel'),
 ("J'avais lu que vous étiez accueillants et que votre service client était de qualité. Je peux l'affirmer de vive voix. Nous reviendrons pour un long séjour.", 'M. Koné'),
 ("C'était juste parfait. Avec les images partagées sur mes réseaux, beaucoup me demandent l'adresse — et je sais qu'ils viendront découvrir.", 'Mme Kane'),
]

# Les equipements communs, chacun avec un pictogramme qu'on reconnait sans
# lire : un climatiseur, un televiseur, un pommeau de douche — et non trois
# traits ou une etoile.
AMEN_BASE = [
 ('Air conditionné', '<rect x="3" y="4" width="18" height="8" rx="2"/><path d="M7 9h10M8 15.5c0 2-2 2-2 4M12 15v5M16 15.5c0 2 2 2 2 4"/>'),
 ('Wifi gratuit', '<path d="M2.5 9.5a14 14 0 0119 0M6 13a9 9 0 0112 0M9.3 16.3a4.2 4.2 0 015.4 0"/><circle cx="12" cy="19.6" r=".9"/>'),
 ('Téléphone', '<path d="M3 10.3V8.5c0-1.5 4-3 9-3s9 1.5 9 3v1.8h-4.5V8.6c-1.2-.5-2.8-.7-4.5-.7s-3.3.2-4.5.7v1.7z"/><path d="M6.5 12.5h11l2 8h-15z"/><circle cx="12" cy="16.5" r="1.8"/>'),
 ('Télévision smart', '<rect x="2.5" y="4" width="19" height="13" rx="1.5"/><rect x="5" y="6.5" width="14" height="8" rx=".5"/><path d="M8 20.5h8"/>'),
 ('Coffre-fort', '<rect x="3" y="4" width="18" height="15" rx="2"/><circle cx="10.5" cy="11.5" r="3.5"/><circle cx="10.5" cy="11.5" r="1"/><path d="M17 9v5M6.5 19v2M17.5 19v2"/>'),
 ('Service en chambre', '<path d="M4.5 17.5a7.5 7.5 0 0115 0zM12 10V7.5M10.5 7.5h3M2.5 20.5h19"/>'),
 ('Minibar', '<rect x="6" y="2.5" width="12" height="19" rx="1.5"/><path d="M6 9.5h12M9 5v2M9 12v3.5"/>'),
 ('Plateau thé &amp; café', '<path d="M4 10h13v4.5a5.5 5.5 0 01-5.5 5.5h-2A5.5 5.5 0 014 14.5zM17 11.5h1.5a2.5 2.5 0 010 5h-1.9M8 3c0 1.5 1.5 1.5 1.5 3M12 3c0 1.5 1.5 1.5 1.5 3"/>'),
 ('Salle d\'eau privative', '<path d="M5 21V8a4 4 0 018 0M9.5 8.5h7"/><circle cx="11" cy="12" r=".5"/><circle cx="14" cy="12" r=".5"/><circle cx="17" cy="12" r=".5"/><circle cx="12.5" cy="15" r=".5"/><circle cx="15.5" cy="15" r=".5"/><circle cx="18.5" cy="15" r=".5"/><circle cx="14" cy="18" r=".5"/><circle cx="17" cy="18" r=".5"/>'),
 ('Sèche-cheveux', '<circle cx="9" cy="8" r="5"/><circle cx="9" cy="8" r="1.6"/><path d="M13.6 5.8l6.9-1.6v7.6l-6.9-1.6M7.4 12.8l1 8.2h3l1-8.6"/>'),
 ('Peignoirs', '<path d="M9 3L5 5.5 3 12l3 1 .5-2.5V21h11V10.5L18 13l3-1-2-6.5L15 3l-3 6z"/><path d="M12 9v12M7.5 14.5h9"/>'),
 ('Produits d\'accueil', '<path d="M5.5 10h6v10.5h-6zM8.5 10V6.5M6.5 6.5h4.5v1.5"/><rect x="14.5" y="13" width="4.5" height="7.5" rx=".8"/><path d="M15.5 13v-2h2.5v2"/>'),
 ('Accès piscine &amp; jacuzzi', '<path d="M8 15V6a2 2 0 014 0M14 15V6a2 2 0 014 0M8 9h6M8 12.5h6M2 19c2 1.4 3.5-1.4 5.5 0s3.5 1.4 5.5 0 3.5-1.4 5.5 0 2 .6 3.5 0"/>'),
 ('Petit-déjeuner inclus', '<path d="M6 3v5a2.5 2.5 0 005 0V3M8.5 3v18M16.5 21V3c-2 1.5-3 4.5-3 9h3"/>'),
]

# Les atouts propres a une chambre : le pictogramme suit le premier mot-cle
# reconnu dans le titre. Rien de reconnu : le losange de la maison.
_ATOUTS = [
 ('baldaquin', '<path d="M4 3v18M20 3v18M4 4h16M4 13h16v4H4M4 12c2-1 3-3 3-6M20 12c-2-1-3-3-3-6"/>'),
 ('salle à manger', '<path d="M3 8h18M5 8v11M19 8v11M8 8V5h8v3"/>'),
 ('lagune', '<path d="M2 17c2 1 4-1 6 0s4 1 6 0 4-1 6 0M2 12c2 1 4-1 6 0s4 1 6 0 4-1 6 0"/><circle cx="17" cy="6" r="2.5"/>'),
 ('salon', '<path d="M4 12V8a2 2 0 012-2h12a2 2 0 012 2v4M2 13a2 2 0 014 0v3h12v-3a2 2 0 014 0v5H2zM6 18v2M18 18v2"/>'),
 ('coin nuit', '<path d="M3 20h4v-4h4v-4h4V8h4V4"/>'),
 ('charpente', '<path d="M3 12l9-8 9 8M5 10.5V20h14v-9.5M12 4v16M5 14l7-6 7 6"/>'),
 ('terrasse', '<path d="M12 21v-9M12 12c0-4 3-7 7-7 0 4-3 7-7 7zM12 15c0-3-2-5-6-5 0 3 2 5 6 5z"/>'),
 ('chambres', '<path d="M2 5v14M2 9h17a3 3 0 013 3v7M2 16h20M6 9v7"/>'),
 ('service', '<path d="M3 18h18M5 18a7 7 0 0114 0M12 8v3M10 8h4"/>'),
]


def picto_atout(titre):
    t = titre.lower()
    for cle, dessin in _ATOUTS:
        if cle in t:
            return dessin
    return '<path d="M12 2l10 10-10 10L2 12z"/><path d="M12 7l5 5-5 5-5-5z"/>'

INCL = [
 ('Petit-déjeuner','Servi au restaurant ou en terrasse, fruits frais et produits locaux.'),
 ('Navette aéroport gratuite','Prise en charge et dépose à l\'aéroport Félix-Houphouët-Boigny, sans frais, à la demande.'),
 ('Piscine, jacuzzi et salle de sport','Accès libre du lever du jour à la nuit tombée.'),
 ('Wifi et parking','Gratuits sur tout le domaine.'),
]

CSS = REMISE_CSS + """
.head{padding-top:150px;padding-bottom:34px}
/* L'en-tete est transparent tant qu'on est sur la photo, comme a l'accueil :
   logo et menu en clair, puis la barre creme au defilement. */
header:not(.scrolled):not(.menu) .hd-fond{background:transparent;backdrop-filter:none}
header:not(.scrolled):not(.menu) .burger .lbl{color:#F6EEE2}
header:not(.scrolled):not(.menu) .burger .bars span{background:#F6EEE2}
header:not(.scrolled):not(.menu) .lang{border-color:rgba(246,238,226,.35)}
header:not(.scrolled):not(.menu) .lang button:not(.on){color:#E3D9C9}
header:not(.scrolled):not(.menu) .brand img{filter:brightness(0) invert(1)}
header:not(.scrolled):not(.menu) .brand small{color:#E2BE8C}
.brand img{transition:clip-path 1.1s var(--ease-inout),filter .6s ease}
/* L'EN-TETE DES FICHES : le logo au centre, le menu et la langue a gauche,
   « Reserver » a droite. La photo prend tout l'ecran derriere. Le balisage
   est celui de tout le site (_chrome.header) : seul l'ordre change, en CSS. */
.nav .brand{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);text-align:center;
  transition:transform 1.1s var(--ease-inout)}
.nav .brand img{width:196px}
.nav .brand small{padding-left:0}
/* Au defilement le logo se recadre sur son embleme, a gauche de sa boite :
   on le ramene au centre. */
header.scrolled .nav .brand{transform:translate(calc(-50% + 61px),-50%)}
.nav-right{flex:1}
.nav-right .burger{order:1;flex-direction:row-reverse}
.nav-right .lang{order:2}
.nav-right .btn{order:3;margin-left:auto}
.fhero{position:relative;height:100vh;height:100svh;min-height:480px;overflow:hidden;background:var(--bark-3)}
.fhero>picture img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center 58%}
/* Deux voiles legers : en haut pour le logo et le menu, en bas pour
   « Decouvrir ». Le milieu reste nu. */
.fhero::after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(180deg,rgba(16,11,6,.58) 0,rgba(16,11,6,.18) 150px,rgba(16,11,6,0) 260px,rgba(16,11,6,0) calc(100% - 130px),rgba(16,11,6,.38) 100%)}
.fhero-tout{position:absolute;left:max(24px,calc((100% - var(--max)) / 2 + 24px));bottom:28px;z-index:3;display:flex;align-items:center;gap:9px;
  background:rgba(16,11,6,.42);color:#F6EEE2;border:1px solid rgba(246,238,226,.45);backdrop-filter:blur(6px);padding:12px 17px;font:700 11px var(--f-body);letter-spacing:.14em;text-transform:uppercase;cursor:pointer;transition:.3s}
.fhero-tout:hover{background:rgba(16,11,6,.62);border-color:#F6EEE2}
.fhero-tout svg{width:16px;height:16px;stroke:#F6EEE2;fill:none;stroke-width:1.6}
.fhero-bas{position:absolute;left:50%;bottom:22px;transform:translateX(-50%);z-index:3;width:54px;height:54px;display:grid;place-items:center;
  animation:fhero-bas 2.4s ease-in-out infinite}
.fhero-bas svg{width:38px;height:38px;stroke:#F6EEE2;fill:none;stroke-width:1.4}
@keyframes fhero-bas{0%,100%{transform:translate(-50%,0)}50%{transform:translate(-50%,7px)}}
@media(prefers-reduced-motion:reduce){.fhero-bas{animation:none}}
.fintro{text-align:center;padding-top:54px;padding-bottom:46px;scroll-margin-top:60px}
.fintro .crumb{margin-bottom:34px}
.fintro h1{font-size:clamp(2.6rem,6.6vw,5rem);color:var(--cream);margin:14px 0 6px;line-height:1.05}
.fintro h1 em{font-style:italic;color:var(--bronze)}
.forn{display:flex;align-items:center;justify-content:center;gap:16px;margin:22px auto 24px}
.forn::before,.forn::after{content:"";width:min(120px,22vw);height:1px;background:var(--line)}
.forn svg{width:22px;height:22px;stroke:var(--bronze);fill:none;stroke-width:1}
.head-price{display:flex;align-items:baseline;justify-content:center;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.head-price small,.head-price span{font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);font-weight:600}
.head-price b{font-family:var(--f-display);font-size:2.1rem;color:var(--cream);line-height:1;font-variant-numeric:tabular-nums;font-weight:400}
.fnote{display:inline-flex;align-items:center;gap:10px;font-size:13px;color:var(--muted)}
.fnote .et{color:#C8922F;letter-spacing:.1em}
.fnote b{color:var(--cream)}
.fnote:hover{color:var(--bronze)}
.faits{display:grid;grid-template-columns:repeat(4,1fr);border-block:1px solid var(--line);margin-bottom:96px}
.faits div{padding:30px 20px;text-align:center}
.faits div+div{border-left:1px solid var(--line)}
.faits svg{width:30px;height:30px;stroke:var(--bronze);fill:none;stroke-width:1.1;margin-bottom:12px}
.faits b{display:block;font-family:var(--f-display);font-weight:400;font-size:1.3rem;color:var(--cream)}
.faits span{font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);font-weight:600}
.frecit{display:grid;grid-template-columns:1fr 1.08fr;gap:84px;align-items:center;margin-bottom:120px}
.frecit h2{font-size:clamp(2rem,3.6vw,3rem);margin:14px 0 24px;line-height:1.12}
.frecit p{font-size:1.04rem;line-height:1.8;color:var(--prose)}
.frecit p+p{margin-top:16px}
.frecit .btn{margin-top:32px}
.fduo{position:relative;z-index:0;padding-bottom:70px;padding-left:60px}
.fduo img{display:block;object-fit:cover;cursor:pointer}
.fduo .g{width:100%;aspect-ratio:4/5}
.fduo .p{position:absolute;left:0;bottom:0;width:46%;aspect-ratio:4/3;border:8px solid var(--bark);box-shadow:0 26px 50px -26px rgba(42,35,30,.5)}
.fduo::before{content:"";position:absolute;right:-22px;top:-22px;width:46%;height:46%;border:1px solid var(--line);z-index:-1}
.fequip{margin-bottom:110px}
.fequip-tete{text-align:center;margin-bottom:26px}
.fequip-tete h2{margin-top:10px}
.fgal-tete{text-align:center;margin-bottom:34px}
.fgal-tete h2{margin-top:10px}
.fgal{display:grid;gap:12px}
.fgal.rang{grid-template-columns:repeat(var(--n),1fr)}
.fgal.mosa{grid-template-columns:repeat(4,1fr);grid-template-rows:repeat(2,250px)}
.fgal figure{position:relative;aspect-ratio:4/3;overflow:hidden;cursor:pointer;background:var(--bark-2)}
.fgal.rang[style*="--n:2"] figure{aspect-ratio:16/10}
.fgal.mosa figure{aspect-ratio:auto}
.fgal.mosa figure.grand{grid-column:span 2;grid-row:span 2}
.fgal figure.hors{display:none}
.fgal img{width:100%;height:100%;object-fit:cover;transition:1s cubic-bezier(.2,.8,.2,1)}
.fgal figure:hover img{transform:scale(1.06)}
.fgal-bas{text-align:center;margin-top:30px}
.fmot{position:relative;padding:120px 24px;text-align:center;color:#F6EEE2;margin:110px 0;
  background:#17100A url(img/opt/gal-dom-couchant-1024.jpg) center/cover}
.fmot::before{content:"";position:absolute;inset:0;background:rgba(16,11,6,.55)}
.fmot>*{position:relative}
.fmot .et{color:#F2C879;letter-spacing:.2em;font-size:15px}
.fmot blockquote{font-family:var(--f-display);font-size:clamp(1.35rem,2.9vw,2.2rem);line-height:1.5;max-width:900px;margin:22px auto 24px;color:#F6EEE2}
.fmot cite{font-style:normal;font-size:10.5px;letter-spacing:.26em;text-transform:uppercase;color:#E2BE8C;font-weight:700}
.surs{list-style:none;margin:18px 0 0;padding:16px 0 0;border-top:1px solid var(--line);display:grid;gap:9px;font-size:13px;color:var(--prose)}
.surs li{display:flex;gap:10px;align-items:flex-start;text-align:left}
.surs svg{width:16px;height:16px;stroke:var(--palm);fill:none;stroke-width:2;flex:none;margin-top:3px}
.body-grid{display:grid;grid-template-columns:1fr 372px;gap:56px;align-items:start;padding-bottom:100px}
.block{margin-bottom:56px}
.block .eyebrow{margin-bottom:14px}
.block h2{margin-bottom:18px}
.block p+p{margin-top:16px}
/* Les equipements : une carte blanche posee sur le fond creme, quatre par
   rangee, de l'air entre les lignes. Les atouts de la chambre et les
   equipements communs ont le meme poids : c'est une liste, pas un classement. */
.amen{display:grid;grid-template-columns:repeat(4,1fr);background:#fff;box-shadow:0 18px 48px -22px rgba(42,35,30,.28),0 2px 8px rgba(42,35,30,.05);padding:26px 12px}
.amen div{padding:34px 20px;font-size:16px;line-height:1.5;display:flex;flex-direction:column;align-items:center;text-align:center;gap:18px;color:var(--cream)}
.amen svg{width:44px;height:44px;stroke:var(--bronze);fill:none;stroke-width:1;stroke-linecap:round;stroke-linejoin:round;flex:0 0 auto}
.amen div.hi b{color:var(--cream);font-weight:400;display:block}
.amen div.hi em{font-style:normal;font-size:12.5px;color:var(--muted);display:block;margin-top:3px}
.incl{list-style:none;margin-top:22px}
.incl li{padding:15px 0;border-bottom:1px solid var(--line);display:flex;gap:16px;align-items:flex-start}
.incl b{display:block;color:var(--cream);font-weight:600;font-size:14.5px;margin-bottom:3px}
.incl p{font-size:13.5px;margin:0;color:var(--muted)}
.incl .chk{color:var(--palm);font-size:15px;line-height:1.5}
.cond{border:1px solid var(--line);margin-top:22px}
.cond div{padding:15px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:18px;font-size:14px}
.cond div:last-child{border-bottom:0}
.cond span:first-child{color:var(--muted);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;font-weight:600}
/* 48 px en haut : le galon occupe les 20 premiers, le contenu commence dessous. */
.panel{position:sticky;top:110px;background:var(--bark-2);border:1px solid var(--line);padding:48px 28px 28px}
.panel .from{font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);font-weight:600}
.panel .rate{font-family:var(--f-display);font-size:2.3rem;color:var(--bronze);line-height:1;margin:6px 0 2px;font-variant-numeric:tabular-nums}
.panel .per{font-size:12px;color:var(--muted);margin-bottom:24px}
.pf{margin-bottom:16px}
.pf label{display:block;font-size:9.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--bronze);margin-bottom:7px;font-weight:700}
.pf input,.pf select{width:100%;min-width:0;min-height:46px;background:transparent;border:1px solid var(--line);color:var(--cream);font:400 15px/1.4 var(--f-body);padding:10px 12px;outline:none;transition:.3s}
.pf input:focus,.pf select:focus{border-color:var(--bronze)}
.pf select option{background:var(--bark-2);color:var(--cream)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.calc{border-top:1px solid var(--line);margin-top:22px;padding-top:18px}
.calc .row{display:flex;justify-content:space-between;gap:14px;font-size:14px;color:var(--muted);padding:7px 0}
.calc .row span:last-child{color:var(--prose);font-variant-numeric:tabular-nums}
.calc .total{border-top:1px solid var(--line);margin-top:10px;padding-top:14px;display:flex;justify-content:space-between;align-items:baseline;gap:14px}
.calc .total span{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:700}
.calc .total b{font-family:var(--f-display);font-size:1.85rem;color:var(--bronze-2);font-variant-numeric:tabular-nums;font-weight:400}
.panel .btn{width:100%;margin-top:20px}
.avail{display:flex;align-items:center;gap:9px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:700;margin-top:16px;justify-content:center}
.avail i{width:7px;height:7px;border-radius:50%;background:var(--muted);display:inline-block}
.panel .helpt{font-size:12.5px;color:var(--muted);text-align:center;margin-top:16px;line-height:1.5}
.panel .helpt a{color:var(--bronze);border-bottom:1px solid var(--line)}
.more{background:var(--bark-2);padding:88px 0}
.more-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:40px}
.rcard{background:var(--bark);border:1px solid var(--line);overflow:hidden;transition:.5s cubic-bezier(.2,.8,.2,1);display:block}
.rcard:hover{transform:translateY(-6px);border-color:rgba(185,138,80,.5)}
.rcard .ph{aspect-ratio:4/3;overflow:hidden}
.rcard img{width:100%;height:100%;object-fit:cover;transition:1s cubic-bezier(.2,.8,.2,1)}
.rcard:hover img{transform:scale(1.07)}
.rcard div{padding:22px}
.rcard h3{margin-bottom:12px}
.rcard .p{display:flex;justify-content:space-between;align-items:baseline;border-top:1px solid var(--line);padding-top:14px;margin-top:4px}
.rcard .p b{font-family:var(--f-display);font-size:1.5rem;color:var(--bronze);font-variant-numeric:tabular-nums;font-weight:400}
.rcard .p span{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.mobar{display:none;position:fixed;left:0;right:0;bottom:0;z-index:95;background:rgba(30,21,13,.98);backdrop-filter:blur(14px);border-top:1px solid var(--line);padding:12px 18px;align-items:center;justify-content:space-between;gap:14px}
.mobar b{font-family:var(--f-display);font-size:1.35rem;color:var(--bronze);display:block;line-height:1;font-variant-numeric:tabular-nums;font-weight:400}
.mobar span{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.mobar .btn{padding:14px 22px}
#lb{position:fixed;inset:0;background:rgba(10,6,3,.98);z-index:200;display:none;place-items:center;padding:40px}
#lb.on{display:grid}
#lb img{max-width:92vw;max-height:84vh;object-fit:contain}
#lbc{position:absolute;bottom:26px;left:0;right:0;text-align:center;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.lb-btn{position:absolute;background:rgba(16,11,6,.75);border:1px solid var(--line);color:var(--cream);width:48px;height:48px;cursor:pointer;font-size:20px;transition:.3s}
.lb-btn:hover{border-color:var(--bronze);color:var(--bronze)}
#lb .prev{left:26px;top:50%}#lb .next{right:26px;top:50%}#lb .close{top:26px;right:26px}
@media(max-width:1080px){
  .body-grid{grid-template-columns:1fr;gap:0}
  /* relative, et non static : le galon de la carte est en position absolue.
     En static il s'echappait tout en haut de la page — cache par l'en-tete
     tant qu'il etait opaque, visible depuis qu'il est transparent. */
  .panel{position:relative;top:auto;margin-bottom:56px}
  .amen{grid-template-columns:repeat(2,1fr)}
  .frecit{grid-template-columns:1fr;gap:54px}
  .faits{grid-template-columns:repeat(2,1fr)}
  .faits div:nth-child(3){border-left:0}
  .faits div:nth-child(n+3){border-top:1px solid var(--line)}
  /* Sur telephone et tablette, reserver vient avant le detail. */
  .body-grid{display:flex;flex-direction:column}
  .body-grid>aside{order:-1}
  .more-grid{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:720px){
  .nav .brand img{width:132px}
  .nav .brand small{display:none}
  header.scrolled .nav .brand{transform:translate(calc(-50% + 41px),-50%)}
  /* Sur telephone, « Reserver » est deja dans la barre du bas : l'en-tete
     garde le menu et le logo. La photo s'arrete au-dessus de cette barre. */
  .nav-right .btn{display:none}
  .fhero{height:calc(100vh - 78px);height:calc(100svh - 78px)}
  .fhero-tout{bottom:18px;left:16px;padding:10px 13px}
  .fhero-bas{display:none}
  .fintro{padding-top:30px;padding-bottom:36px}
  .fintro .crumb{margin-bottom:24px}
  .head-price b{font-size:1.8rem}
  .faits{margin-bottom:60px}.faits div{padding:20px 10px}.faits b{font-size:1.1rem}
  .frecit{margin-bottom:70px}
  .fduo{padding-left:28px;padding-bottom:48px}
  .fequip{margin-bottom:64px}
  .amen{padding:12px 4px}
  .amen div{padding:22px 8px;font-size:13.5px;gap:12px}
  .amen svg{width:36px;height:36px}
  .fgal.rang,.fgal.mosa{grid-template-columns:1fr 1fr;grid-template-rows:none;grid-auto-rows:150px;gap:8px}
  .fgal figure,.fgal.rang[style*="--n:2"] figure{aspect-ratio:auto}
  .fgal.rang[style*="--n:3"] figure:nth-child(4),.fgal.mosa figure.grand{grid-column:span 2;grid-row:span 2}
  .fmot{padding:74px 24px;margin:64px 0}
  .more-grid{grid-template-columns:1fr}
  .two{grid-template-columns:1fr}
  .mobar{display:flex}
  body{padding-bottom:78px}
  /* Les bulles flottantes passent au-dessus de la barre de reservation. */
  .wa{bottom:92px}.chat-bulle{bottom:162px}
  #lb .prev{left:8px}#lb .next{right:8px}
}
"""
# Les cinq touches textiles : ce morceau ne part que sur les pages qui
# en portent une.
# Les utilitaires D'ABORD, les placements ensuite : a specificite egale
# c'est la derniere regle qui gagne, et ce sont les placements qui
# doivent gagner. Dans l'autre sens, `.pagne-damas{position:absolute}`
# ecrasait le `position:relative` du placement, et le motif sortait du
# flux — largeur zero, invisible, et le test passait au vert.
CSS = PAGNE_CSS + CSS


# Largeurs reelles des vignettes de la mosaique -------------------------------
#
# .wrap fait min(--max, 100vw) - 48 ; --max vaut 1240, 1440 des 1600 px, 1580 des 1840. La grille est en 2fr 1fr 1fr avec 10 px
# de gouttiere au-dela de 1100 px, en deux colonnes entre 721 et 1100, et en
# une seule colonne en dessous. La premiere figure occupe deux rangees, donc
# la moitie de la largeur en grand, et toute la largeur en dessous de 1100.
#
# Sans ces declarations, une vignette de 293 px se faisait servir le palier
# 1024 : le navigateur ne voit pas la grille, il croit ce qu'on lui declare.
#
# Placement en trois colonnes : la premiere figure prend la colonne large sur
# deux rangees, donc les quatre suivantes remplissent les deux colonnes
# etroites. A partir de la sixieme, les rangees repartent sur les trois
# colonnes — l'image d'indice 5, puis 8, puis 11, retombe dans la colonne
# large. En dessous de cinq photos la premiere ne prend qu'une rangee.
_LARGE_3COL = '(max-width:1287px) calc((100vw - 68px) / 2), (max-width:1439px) 586px, (max-width:1599px) 646px, (max-width:1839px) 686px, 756px'
_ETROIT_3COL = '(max-width:1287px) calc((100vw - 68px) / 4), (max-width:1439px) 293px, (max-width:1599px) 323px, (max-width:1839px) 343px, 378px'
# Deux colonnes : pleine largeur pour la premiere et pour une derniere etalee,
# demi-largeur sinon. Une seule colonne en dessous de 721 px.
_PLEIN = 'calc(100vw - 48px)'
_DEMI = 'calc((100vw - 58px) / 2)'


def _sizes_mosaique(i, n):
    """Declaration de largeur pour la i-eme photo d'une mosaique de n.

    Composee a partir du placement reel, pas approximee : une vignette de
    293 px se faisait servir le palier 1024 parce qu'on lui declarait 700 px.
    """
    grand = (i == 0) or (n >= 5 and i >= 5 and (i - 5) % 3 == 0)
    etale = (i == 0) or (i == n - 1 and n % 2 == 0)   # pleine largeur a 2 colonnes
    trois = _LARGE_3COL if grand else _ETROIT_3COL
    deux = _PLEIN if etale else _DEMI
    if i == 0:
        return '(max-width:1100px) %s, %s' % (_PLEIN, trois)
    return '(max-width:720px) %s, (max-width:1100px) %s, %s' % (_PLEIN, deux, trois)


def fmt(n):
    return format(n, ',').replace(',', ' ')


def _en_dict(c):
    """Assemble le dictionnaire anglais de la fiche, cle par cle.

    Les cles sont celles des data-t poses dans le balisage. Si une traduction
    manque, LANG_JS laisse le francais en place plutot que d'afficher un trou
    — et verifier.py signale le manque.
    """
    e = _chambres_en.EN[c['slug']]
    d = dict(_chambres_en.CHASSIS)
    d['mbb'] = d['cta']
    d['vph'] = 'See all %d photos' % len(c['photos'])
    d['him'] = 'A tour of the suite' if c['slug'].startswith('suite') else 'A tour of the room'
    if NOTE_GOOGLE:
        d['nt1'] = '<b>%.1f/5</b> · %d Google reviews' % NOTE_GOOGLE
    d['eb0'] = e['tag'] or _chambres_en.CHASSIS['eb0']
    d['ttl'] = e['titre'].replace('<br>', ' ')   # une seule ligne sous le nom
    d['pa1'], d['pa2'], d['pa3'] = e['p1'], e['p2'], e['p3']
    for i, (val, lab) in enumerate(e['facts']):
        d['fv%d' % i], d['fl%d' % i] = val, lab
    for i, (t, dd) in enumerate(e['plus']):
        d['pt%d' % i], d['pd%d' % i] = t, dd
    for i, t in enumerate(_chambres_en.AMEN_EN):
        d['am%d' % i] = t
    for i, (t, dd) in enumerate(_chambres_en.INCL_EN):
        d['it%d' % i], d['id%d' % i] = t, dd
    for i, slug in enumerate(c['autres']):
        d['om%d' % i] = _chambres_en.EN[slug]['meta']
        d['on%d' % i] = _chambres_en.CHASSIS['pnuit']
    return ','.join('%s:%s' % (k, json.dumps(v, ensure_ascii=False))
                    for k, v in sorted(d.items()))

for c in CHAMBRES:
    pax_opts = ''.join(
        '<option value="%d"%s>%d personne%s</option>' % (i, ' selected' if i == min(2, c['pax']) else '', i, 's' if i > 1 else '')
        for i in range(1, c['pax'] + 1))

    # LA FICHE « SIGNATURE » (novembre 2026), en huit temps : la chambre en
    # grand, SANS texte dessus ; son nom, son prix et la note Google ; ses
    # quatre points forts ; son recit a cote de deux photos ; ses
    # equipements ; sa galerie ; le mot d'un client ; la reservation.
    #
    # Les photos : la premiere fait l'ouverture, les deux suivantes
    # accompagnent le recit, le reste compose la galerie. Toutes restent
    # dans #gl, dans l'ordre : c'est la liste du diaporama.
    ph = c['photos']
    tete = ph[0]
    reste = len(ph) - 3
    if reste >= 5:
        forme, n_gal = 'mosa', 5          # une grande et quatre petites
    elif reste >= 2:
        forme, n_gal = 'rang', reste      # une rangee
    else:
        forme, n_gal = 'vide', 0          # trois photos : tout est deja montre
    suite = c['slug'].startswith('suite')
    if NOTE_GOOGLE:
        note = ('<a class="fnote" href="%s" target="_blank" rel="noopener"><span class="et" aria-hidden="true">★★★★★</span>'
                '<span data-t="nt1"><b>%s/5</b> · %d avis Google</span></a>'
                % (FICHE_GOOGLE, ('%.1f' % NOTE_GOOGLE[0]).replace('.', ','), NOTE_GOOGLE[1]))
    else:
        note = ''

    b = [header('#reserver', 'Réserver'), drawer('index.html#chambres'), """
<section class="fhero">
  <picture><source srcset="img/opt/%s.webp" type="image/webp">
    <img loading="eager" fetchpriority="high" src="img/opt/%s.jpg" alt="%s"></picture>
  <button type="button" class="fhero-tout voir-photos"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.1-3.1a2 2 0 00-2.8 0L6 21"/></svg><span data-t="vph">Voir les %d photos</span></button>
  <a class="fhero-bas" href="#fiche" aria-label="Découvrir la chambre"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8l8 8 8-8"/></svg></a>
</section>

<section class="wrap fintro" id="fiche">
  <nav class="crumb" aria-label="Fil d'Ariane">
    <a href="index.html" data-t="c1">Accueil</a> &nbsp;·&nbsp;
    <a href="chambres.html" data-t="c2">Chambres &amp; Suites</a> &nbsp;·&nbsp;
    <span>%s</span>
  </nav>
  <span class="eyebrow" data-t="eb0">%s</span>
  <h1>%s</h1>
  <div class="forn" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 2l10 10-10 10L2 12z"/><path d="M12 7l5 5-5 5-5-5z"/></svg></div>
  <div class="head-price" id="prix-tete"><small data-t="frm">À partir de</small><b data-prix-de="%s">%s</b><span data-t="pnuit">FCFA / nuit</span></div>
  %s
</section>

<section class="wrap">
  <div class="faits reveal">""" % (tete[0], tete[0], tete[1], len(ph), c['nom'], c['tag'] or 'Chambre',
                              nom_accentue(c['nom']), c['slug'], fmt(c['prix']), note)]

    for i, (val, lab) in enumerate(c['facts']):
        b.append('    <div><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg>'
                 '<b data-t="fv%d">%s</b><span data-t="fl%d">%s</span></div>'
                 % (picto(val, lab), i, val, i, lab))

    b.append("""  </div>
</section>

<section class="wrap frecit">
  <div class="reveal">
    <span class="eyebrow" data-t="ebr">La chambre</span>
    <h2 data-t="ttl">%s</h2>
    <p data-t="pa1">%s</p>
    <p data-t="pa2">%s</p>
    <p data-t="pa3">%s</p>
    <a class="btn btn-solid" href="#reserver" data-t="vdi">Vérifier les disponibilités</a>
  </div>
  <div class="fduo reveal">
    <picture><source srcset="img/opt/%s.webp" type="image/webp">
      <img class="g" loading="lazy" src="img/opt/%s.jpg" alt="%s" data-lb="1"></picture>
    <picture><source srcset="img/opt/%s.webp" type="image/webp">
      <img class="p" loading="lazy" src="img/opt/%s.jpg" alt="%s" data-lb="2"></picture>
  </div>
</section>

<section class="wrap fequip reveal">
  <div class="fequip-tete">
    <span class="eyebrow" data-t="ebe">Équipements</span>
    <h2 data-t="hae">Dans la chambre</h2>
  </div>
  <div class="amen">""" % (c['titre'].replace('<br>', ' '), c['p1'], c['p2'], c['p3'],
                           ph[1][0], ph[1][0], ph[1][1], ph[2][0], ph[2][0], ph[2][1]))

    for i, (t, d) in enumerate(c['plus']):
        b.append('      <div class="hi"><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg>'
                 '<span><b data-t="pt%d">%s</b><em data-t="pd%d">%s</em></span></div>'
                 % (picto_atout(t), i, t, i, d))
    for i, (t, d) in enumerate(AMEN_BASE):
        b.append('      <div><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg>'
                 '<span data-t="am%d">%s</span></div>' % (d, i, t))

    b.append("""  </div>
</section>
""")
    if forme != 'vide':
        b.append("""
<section class="wrap fgal-tete reveal">
  <span class="eyebrow" data-t="eim">En images</span>
  <h2 data-t="him">%s</h2>
</section>""" % ('Un tour de la suite' if suite else 'Un tour de la chambre'))

    b.append("""
<div class="wrap">
  <div class="fgal %s" id="gl" style="--n:%d">""" % (forme, n_gal))

    # Pas de legende sur les photos : l'image parle seule, le texte
    # alternatif reste pour les lecteurs d'ecran.
    for i, (img, alt, cap) in enumerate(ph):
        # « hors » : dans le diaporama seulement — l'ouverture, les deux
        # photos du recit, et ce qui depasse de la galerie.
        hors = i < 3 or i >= 3 + n_gal
        cl = ' class="hors"' if hors else (' class="grand"' if forme == 'mosa' and i == 3 else '')
        b.append("""    <figure%s><picture><source srcset="img/opt/%s.webp" type="image/webp">
      <img loading="lazy" src="img/opt/%s.jpg" data-full="img/opt/%s.jpg" alt="%s"></picture></figure>""" % (cl, img, img, img, alt))

    b.append("""  </div>
</div>
""")
    if forme != 'vide':
        b.append("""<div class="wrap fgal-bas"><button type="button" class="btn voir-photos" data-t="vph">Voir les %d photos</button></div>
""" % len(ph))

    avis = AVIS[CHAMBRES.index(c) % len(AVIS)]
    b.append("""
<section class="fmot">
  <div class="et" aria-label="5 étoiles sur 5">★★★★★</div>
  <blockquote>« %s »</blockquote>
  <cite>%s</cite>
</section>

<div class="wrap body-grid">
 <div>
""" % avis)

    b.append('''
  <section class="block reveal">
    <span class="eyebrow" data-t="ebi">Inclus</span>
    <h2 data-t="hai">Compris dans le tarif</h2>
    <ul class="incl">''')
    for i, (t, d) in enumerate(INCL):
        b.append('      <li><span class="chk">✓</span><div><b data-t="it%d">%s</b>'
                 '<p data-t="id%d">%s</p></div></li>' % (i, t, i, d))

    b.append('''    </ul>
  </section>

  <section class="block reveal">
    <span class="eyebrow" data-t="ebc">Conditions</span>
    <h2 data-t="hac">Bon à savoir</h2>
    <div class="cond">
      <div><span data-t="cd1">Arrivée</span><span data-t="cd1v">à partir de 14 h 00</span></div>
      <div><span data-t="cd2">Départ</span><span data-t="cd2v">avant 12 h 00</span></div>
      <div><span data-t="cd3">Annulation</span><span data-t="cd3v">gratuite jusqu'à 48 h avant</span></div>
      <div><span data-t="cd4">Acompte</span><span data-t="cd4v">30 %% à la réservation</span></div>
      <div><span data-t="cd5">Animaux</span><span data-t="cd5v">non admis</span></div>
      <div><span data-t="cd6">Paiement</span><span data-t="cd6v">Wave · Orange Money · MTN · carte</span></div>
    </div>
    <p style="margin-top:16px;font-size:13px;color:var(--muted)" data-t="cdn">
      Le détail complet figure sur la page <a href="informations-utiles.html#reserver" style="color:var(--bronze)">Informations utiles</a>.
    </p>
  </section>
 </div>

 <aside class="panel" id="reserver">
  <div class="pagne pagne-galon" aria-hidden="true"></div>
  <span class="from" data-t="apd">À partir de</span>
  <div class="rate" id="prix-panneau"><span data-prix-de="%s">%s</span> <span style="font-size:1rem">FCFA</span></div>
  <div class="per" data-t="pern">par nuit, petit-déjeuner inclus</div>

  <form id="bkf">
    <div class="two">
      <div class="pf"><label for="d1" data-t="la1">Arrivée</label><input type="date" id="d1"></div>
      <div class="pf"><label for="d2" data-t="la2">Départ</label><input type="date" id="d2"></div>
    </div>
    <div class="pf"><label for="pax" data-t="lax">Voyageurs</label><select id="pax">%s</select></div>

    <div class="calc">
      <div class="row"><span id="l1">%s FCFA × 2 nuits</span><span id="v1"></span></div>
      <div class="row"><span data-t="rtx">Taxe de séjour</span><span id="v2"></span></div>
      <div class="row"><span data-t="rpd">Petit-déjeuner</span><span style="color:var(--palm)" data-t="rin">Inclus</span></div>
      <div class="total"><span data-t="rtt">Total séjour</span><b id="tt"></b></div>
    </div>

    <button type="submit" class="btn btn-solid" data-t="bkb">Réserver cette chambre</button>
    <div class="avail" id="avl"><i></i><span>Disponibilité confirmée sous 24 h</span></div>
    <ul class="surs"><li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg><span data-t="as0">Meilleur tarif en réservant ici</span></li><li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg><span data-t="as1">Annulation gratuite jusqu'à 48 h avant</span></li><li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg><span data-t="as2">Acompte de 30 %% seulement</span></li><li><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg><span data-t="as3">Petit-déjeuner et navette aéroport compris</span></li></ul>
    <p class="helpt" data-t="hlp">Une question&nbsp;? Écrivez-nous sur <a href="https://wa.me/{{WA}}" target="_blank" rel="noopener">WhatsApp</a> ou appelez le +225 01 51 52 75 75.</p>
  </form>
 </aside>
</div>

<section class="more">
  <div class="wrap">
    <span class="eyebrow" data-t="ebo">Autres catégories</span>
    <h2 data-t="hao">Si celle-ci est prise</h2>
    <div class="more-grid">''' % (c['slug'], fmt(c['prix']), pax_opts, fmt(c['prix'])))

    for i, slug in enumerate(c['autres']):
        o = PAR_SLUG[slug]
        img = o['photos'][0][0]
        b.append('''      <a class="rcard reveal" href="%s.html">
        <div class="ph"><picture><source srcset="img/opt/%s.webp" type="image/webp">
          <img loading="lazy" src="img/opt/%s.jpg" alt="%s"></picture></div>
        <div><h3>%s</h3><p style="font-size:14px" data-t="om%d">%s</p>
        <div class="p"><b data-prix-de="%s">%s</b><span data-t="on%d">FCFA / nuit</span></div></div>
      </a>''' % (slug, img, img, o['nom'], o['nom'], i, o['meta'], slug, fmt(o['prix']), i))

    b.append('''    </div>
  </div>
</section>

''' + FOOTER + '''

<div class="mobar sombre">
  <div><b id="mb"></b><span data-t="mbs">FCFA · séjour total</span></div>
  <a href="#reserver" class="btn btn-solid" data-t="mbb">Réserver</a>
</div>

<div id="lb" role="dialog" aria-modal="true" aria-label="Photos de la chambre">
  <button class="lb-btn close" aria-label="Fermer">×</button>
  <button class="lb-btn prev" aria-label="Photo précédente">‹</button>
  <img id="lbi" alt="">
  <button class="lb-btn next" aria-label="Photo suivante">›</button>
  <div id="lbc"></div>
</div>''')

    JS = NAV_JS + REMISE_JS + DISPO_JS + '''

var RATE=%d, TAX=1500; // taxe de séjour par personne et par nuit
/* PLEIN ne bouge jamais : c'est le tarif de la grille. RATE est ce qu'on
   facture, et une promotion en cours le baisse. Les deux restent distincts
   parce que le recapitulatif doit montrer l'un barre et l'autre applique.
   Le slug se lit dans l'adresse — la fiche s'appelle du nom de sa chambre,
   avec ou sans .html selon la reecriture d'URL. */
var PLEIN=RATE;
var SLUG=location.pathname.split('/').pop().split('.')[0];
var d1=document.getElementById('d1'),d2=document.getElementById('d2'),pax=document.getElementById('pax');
function iso(d){return new Date(d.getTime()-d.getTimezoneOffset()*6e4).toISOString().slice(0,10)}
d1.value=iso(new Date(Date.now()+864e5));d2.value=iso(new Date(Date.now()+864e5*3));
d1.min=iso(new Date());d2.min=iso(new Date());
function fmt(n){return n.toLocaleString('fr-FR').replace(/ | |,/g,' ')}
/* Le recapitulatif et le selecteur de voyageurs sont ecrits par ce script,
   donc hors de portee de [data-t]. LANG_JS appelle EVN_LANG a chaque
   bascule : c'est le point d'extension prevu pour ce cas. */
var MOTS={fr:{n1:' nuit',nn:' nuits',p1:' personne',pp:' personnes'},
          en:{n1:' night',nn:' nights',p1:' guest',pp:' guests'}};
var LG='fr';
function EVN_LANG(lg){
  LG=MOTS[lg]?lg:'fr';
  [].forEach.call(pax.options,function(o){
    var n=+o.value; o.textContent=n+(n>1?MOTS[LG].pp:MOTS[LG].p1);
  });
  calc();
  peindre();
}

/* La disponibilite -----------------------------------------------------
   ETAT vaut 'inconnu' tant que rien n'a repondu, et c'est l'etat juste :
   la pastille dit alors « confirmee sous 24 h », ce que la reception fait
   deja. Elle ne passe au vert que sur un 'libre' venu du serveur. */
var ETAT='inconnu';
var avl=document.getElementById('avl');
function peindre(){
  if(!avl)return;
  var c=EVN_DISPO.couleur(ETAT);
  avl.querySelector('span').textContent=EVN_DISPO.libelle(ETAT,LG);
  avl.style.color=c;
  avl.querySelector('i').style.background=c;
}
function interroger(){
  EVN_DISPO.pour(SLUG,d1.value,d2.value,function(e){ETAT=e;peindre()});
}
function calc(){
  var a=new Date(d1.value),b=new Date(d2.value);
  var n=Math.round((b-a)/864e5); if(!n||n<1){n=1;d2.value=iso(new Date(a.getTime()+864e5))}
  var p=+pax.value, sejour=RATE*n, taxe=TAX*p*n, total=sejour+taxe;
  document.getElementById('l1').textContent=fmt(RATE)+' FCFA × '+n+(n>1?MOTS[LG].nn:MOTS[LG].n1)
    +(RATE<PLEIN?' · '+EVN_REMISE.etiquette():'');
  document.getElementById('v1').textContent=fmt(sejour);
  document.getElementById('v2').textContent=fmt(taxe);
  document.getElementById('tt').textContent=fmt(total);
  document.getElementById('mb').textContent=fmt(total);
  interroger();
}
/* La remise arrive apres le premier calcul : on recalcule des qu'elle est la.
   Si l'API se tait, la fiche garde le tarif plein — le repli sur.
   Une remise affichee sur la carte et absente ici enverrait le client
   decouvrir le prix reel au moment de payer. */
EVN_REMISE.quand(function(R){
  peindre();   /* le paiement en ligne se sait maintenant : voir EVN_DISPO.libelle */
  /* Le prix saisi dans l'administration remplace celui de la grille. Les
     prix affiches sont deja repeints (REMISE_JS) ; reste le calcul. */
  PLEIN=R.base(SLUG,PLEIN); RATE=PLEIN;
  var applique=R.prix(PLEIN,SLUG);
  if(applique>=PLEIN){calc();return;}
  RATE=applique;

  var tete=document.getElementById('prix-tete');
  var b=tete&&tete.querySelector('b');
  if(b){
    var barre=document.createElement('s');
    barre.className='avant';
    barre.textContent=fmt(PLEIN);
    tete.insertBefore(barre,b);
    b.textContent=fmt(RATE);
    b.className='apres';
  }

  var pan=document.getElementById('prix-panneau');
  if(pan){
    pan.innerHTML='<s class="avant">'+fmt(PLEIN)+'</s>'
      +'<span class="apres">'+fmt(RATE)+'</span>'
      +' <span style="font-size:1rem">FCFA</span>';
  }

  calc();
});

[d1,d2,pax].forEach(function(e){e.addEventListener('change',calc)});
document.getElementById('bkf').addEventListener('submit',function(e){e.preventDefault();calc();
  var q='?chambre=%s&du='+d1.value+'&au='+d2.value+'&pax='+pax.value;
  location.href='reserver.html'+q;
});
calc();

var figs=[].slice.call(document.querySelectorAll('#gl img')),lb=document.getElementById('lb'),lbi=document.getElementById('lbi'),lbc=document.getElementById('lbc'),gi=0;
function show(i){gi=(i+figs.length)%%figs.length;lbi.src=plein(figs[gi]);lbi.alt=figs[gi].alt;lbc.textContent=figs[gi].alt+'  ·  '+(gi+1)+' / '+figs.length;lb.classList.add('on');document.body.style.overflow='hidden'}
function hideLb(){lb.classList.remove('on');document.body.style.overflow=''}
figs.forEach(function(im,i){im.closest('figure').onclick=function(){show(i)}});
[].forEach.call(document.querySelectorAll('.voir-photos'),function(x){x.onclick=function(){show(0)}});
[].forEach.call(document.querySelectorAll('[data-lb]'),function(x){x.onclick=function(){show(+x.getAttribute('data-lb'))}});
lb.querySelector('.next').onclick=function(e){e.stopPropagation();show(gi+1)};
lb.querySelector('.prev').onclick=function(e){e.stopPropagation();show(gi-1)};
lb.querySelector('.close').onclick=hideLb;
lb.onclick=function(e){if(e.target===lb)hideLb()};
addEventListener('keydown',function(e){if(!lb.classList.contains('on'))return;
 if(e.key==='Escape')hideLb();if(e.key==='ArrowRight')show(gi+1);if(e.key==='ArrowLeft')show(gi-1)});

var EN={''' % (c['prix'], c['slug']) + EN_NAV + _en_dict(c) + '};\n\n' + LANG_JS

    LD = _schema.bloc(
        _schema.chambre(
            c['nom'].replace('&amp;', '&'), c['slug'], c['prix'], c['pax'],
            "%s %s FCFA la nuit, petit-dejeuner et navette aeroport inclus."
            % (c['meta'].replace('&nbsp;', ' '), fmt(c['prix'])),
            [ph[0] for ph in c['photos']],
            equipements=['Climatisation', 'Salle de bain privative', 'Wifi gratuit',
                         'Petit-déjeuner inclus']
                        + [p[0] for p in c['plus']],
            lits={v: k for k, v in c['facts']}.get('lit')),
        _schema.hotel(),
        _schema.fil([('Accueil', 'index'), ('Chambres &amp; Suites', 'chambres'),
                     (c['nom'].replace('&amp;', '&'), None)]))

    # L'ouverture est en pleine largeur (hero=preload la declare en 100vw).
    # Les deux photos du recit : la grande tient la moitie de .wrap, la
    # petite un peu moins du quart. La galerie : des quarts, sauf la grande
    # de la mosaique. Sur telephone, tout passe en pleine ou demi-largeur.
    mosa = {p[0]: '(max-width:720px) 50vw, (max-width:1287px) calc((100vw - 48px) / 4), 395px' for p in ph[3:]}
    if forme == 'mosa':
        mosa[ph[3][0]] = '(max-width:1287px) calc((100vw - 48px) / 2), 790px'
    mosa[ph[1][0]] = '(max-width:1080px) calc(100vw - 76px), 700px'
    mosa[ph[2][0]] = '(max-width:1080px) 46vw, 340px'

    HTML = page(
        "%s — Hôtel Evannath, Assinie | %s FCFA la nuit" % (c['nom'], fmt(c['prix'])),
        "%s à l'Hôtel Evannath, Assinie PK 19 : %s. %s FCFA la nuit, petit-déjeuner et navette aéroport inclus."
        % (c['nom'], c['meta'], fmt(c['prix'])),
        c['photos'][0][0], CSS, '\n'.join(b), JS + PAGNE_JS, preload=c['photos'][0][0], slug=c['slug'], jsonld=LD, sizes=mosa)
    # Le numero WhatsApp du moment : voir WA_EN_TEST dans _chrome.py.
    io.open(c['slug'] + '.html', 'w', encoding='utf-8').write(HTML.replace('{{WA}}', WA))
    print('  %-26s %s FCFA' % (c['slug'] + '.html', fmt(c['prix'])))

print('%d fiches chambres generees' % len(CHAMBRES))
