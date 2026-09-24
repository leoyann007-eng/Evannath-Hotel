# -*- coding: utf-8 -*-
"""Genere index.html a partir de index-template.html.

L'accueil etait la derniere page a recopier les jetons de couleur et le JS de
navigation du site. Toute correction centrale la manquait donc en silence.
Elle consomme desormais les memes briques que les autres, et ne garde en
propre que les six valeurs de couleur qui lui sont specifiques.
"""
import io
NL_ = chr(10)
from _chrome import REMISE_JS, REMISE_CSS, DISPO_JS, FOOTER_CSS
from _chrome import (TOKENS, NAV_BASE, LANG_JS, dimensionner, responsive, versionner,
                     liens_nav, EN_NAV, WA, WA_TEXTE, MAIL)
from _evenements import EVENEMENTS, EN as EV_EN
import _schema


# Le bandeau de l'accueil : le premier evenement de la liste, celui que
# l'etablissement veut mettre en avant. Il porte sa date de fin et disparait
# tout seul — le meme mecanisme que sur la page Evenements.
_e = EVENEMENTS[0] if EVENEMENTS else None
if _e:
    _fin = ' data-fin="%s"' % _e['fin'] if _e['fin'] else ''
    # Pas de classe « reveal » : le bandeau annonce ce qui se passe MAINTENANT.
    # L'attendre au defilement le rendrait invisible tant que le script n'a
    # pas tourne, et invisible tout court si le script echoue.
    BANDEAU = ('<div class="bandeau" id="bandeau"%s>'
               '<a href="circuits.html#a-la-une">'
               '<span class="quand" data-t="bq">%s</span>'
               '<b data-t="bt">%s</b>'
               '<span class="t" data-t="bx">%s</span>'
               '<span class="fl" data-t="bf">Voir tout</span>'
               '</a></div>') % (_fin, _e['quand'], _e['titre'],
                                "Et tout ce qui se passe à l'hôtel en ce moment.")
    _en = EV_EN.get(_e['slug'])
    EN_BANDEAU = ('bq:"%s",bt:"%s",bx:"On now at the hotel.",bf:"See all",'
                  % (_en[1], _en[0])) if _en else ''
else:
    BANDEAU, EN_BANDEAU = '', ''

# L'expiration, cote navigateur.
JS_BANDEAU = r"""<script>
(function(){
  var b = document.getElementById('bandeau');

  /* L'evenement fige dans la page expire tout seul. */
  if (b) {
    var f = b.getAttribute('data-fin');
    var a = new Date(); a.setHours(0, 0, 0, 0);
    if (f && new Date(f + 'T23:59:59') < a) b.remove();
  }

  /* Une promotion mise en avant depuis l'administration prend la place : c'est
     ce que promet la case « Mettre en avant sur la page d'accueil ». Le serveur
     ne renvoie que les promotions dont la periode court. Si aucune n'est mise
     en avant, le bandeau garde l'evenement — ou reste absent. */
  fetch('/api/admin?a=public', { cache: 'no-store' })
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(function(j){
      if (!j) return;

      /* Une campagne mise en avant passe devant une promotion : c'est le
         moment commercial le plus large, et elle porte plusieurs offres. */
      var camp = (j.campagnes || []).filter(function(x){ return x.avant; })[0];
      var p = camp || (j.promotions || []).filter(function(x){ return x.avant; })[0];
      if (!p) return;

      var d = document.getElementById('bandeau');
      if (!d) {
        var hero = document.querySelector('.hero');
        if (!hero || !hero.parentNode) return;
        d = document.createElement('div');
        d.className = 'bandeau';
        d.id = 'bandeau';
        hero.parentNode.insertBefore(d, hero.nextSibling);
      }

      d.className = 'bandeau offre';

      var el = function(balise, cl, txt){
        var n = document.createElement(balise);
        if (cl) n.className = cl;
        if (txt != null) n.textContent = txt;
        return n;
      };

      /* Ce qui fait decider tient en trois choses : ce que c'est, a partir de
         combien, et jusqu'a quand. Aucune n'est inventee — si la donnee
         manque, la ligne disparait plutot que de mentir. */
      var UNITES = { personne: 'par personne', enfant: 'par enfant',
                     nuit: 'la nuit' };
      var genre, prix, unite = '', compte = '', lien, appel;

      if (camp) {
        var packs = (p.packs || []).filter(function(x){ return Number(x.prix) > 0; });
        var bas = packs.slice().sort(function(x, y){ return x.prix - y.prix; })[0];
        genre = 'Offre de saison';
        prix = bas ? 'Dès ' + Number(bas.prix).toLocaleString('fr-FR') + ' F' : '';
        /* L'unite compte : « dès 15 000 F » quand c'est un tarif par enfant
           n'est pas la meme promesse qu'un forfait. On la dit. */
        unite = bas ? (UNITES[bas.unite] || '') : '';
        compte = packs.length > 1 ? packs.length + ' packs' : '';
        lien = 'circuits.html#campagnes';
        appel = 'Voir les packs';
      } else {
        var r = p.remise || {};
        genre = 'Promotion';
        prix = !r.valeur ? 'Offre en cours'
          : r.type === 'montant'
            ? '−' + Number(r.valeur).toLocaleString('fr-FR') + ' F'
            : '−' + r.valeur + ' %';
        compte = p.code ? 'Code ' + p.code : '';
        lien = 'circuits.html#forfaits';
        appel = 'Voir l’offre';
      }

      /* L'echeance. Au-dela de deux semaines on donne la date : elle informe.
         En deca on donne les jours restants : c'est la meme information, mais
         elle se lit comme une echeance. Sans date de fin, rien. */
      var delai = '', court = false;
      if (p.fin) {
        var f = new Date(p.fin);
        if (!isNaN(f.getTime())) {
          if (String(p.fin).length <= 10) f.setHours(23, 59, 59, 0);
          var jours = Math.ceil((f - new Date()) / 86400000);
          if (jours > 0 && jours <= 14) {
            court = true;
            delai = jours === 1 ? 'Dernier jour' : 'Plus que ' + jours + ' jours';
          } else if (jours > 14) {
            delai = 'Jusqu’au ' + f.toLocaleDateString('fr-FR',
              { day: 'numeric', month: 'long' });
          }
        }
      }

      var a2 = document.createElement('a');
      a2.href = lien;

      var corps = el('div', 'corps');
      var sur = el('div', 'sur');
      sur.appendChild(el('span', 'genre', genre));
      if (compte) sur.appendChild(el('span', 'compte', '· ' + compte));
      corps.appendChild(sur);

      var titre = el('div', 'titre-offre');
      titre.appendChild(el('b', '', p.titre || ''));
      if (prix) {
        var pr = el('span', 'prix', prix);
        if (unite) pr.appendChild(el('i', '', unite));
        titre.appendChild(pr);
      }
      corps.appendChild(titre);

      /* L'accroche d'une campagne tient sur plusieurs lignes : le bandeau
         n'en prend que la première. */
      var texte = (p.message || p.accroche || '').split('\n')[0];
      if (texte) corps.appendChild(el('span', 'accroche', texte));

      var agir = el('div', 'agir');
      if (delai) agir.appendChild(el('span', 'delai' + (court ? ' court' : ''), delai));
      agir.appendChild(el('span', 'bouton', appel));

      a2.appendChild(corps);
      a2.appendChild(agir);

      d.innerHTML = '';
      d.appendChild(a2);
    })
    .catch(function(){});
})();
</script>"""
html = io.open('index-template.html', encoding='utf-8').read()
html = (html
        .replace('{{BANDEAU}}', BANDEAU)
        .replace('{{NAV_LINKS}}', liens_nav('index.html'))
        .replace('{{EN_NAV}}', EN_NAV + EN_BANDEAU)
        .replace('{{WA}}', WA)
        .replace('{{WA_TEXTE}}', WA_TEXTE)
        .replace('{{TOKENS}}', TOKENS + REMISE_CSS)
        .replace('{{REMISE_JS}}', REMISE_JS)
        .replace('{{DISPO_JS}}', DISPO_JS)
        .replace('{{FOOTER_CSS}}', FOOTER_CSS)
        .replace('{{NAV_BASE}}', NAV_BASE)
        .replace('{{LANG_JS}}', LANG_JS)
        .replace('{{JSONLD}}', _schema.bloc(_schema.hotel(complet=True),
                                            _schema.site_web(),
                                            _schema.restaurant())))
# Largeur reelle des cartes des deux grilles de l'accueil.
#
# .wrap fait min(1240px, 100vw) - 48. Les chambres tiennent sur trois colonnes
# de 24 px de gouttiere au-dela de 1024, les offres sur quatre ; en dessous,
# deux colonnes, puis une seule sous 721 px.
#
# On declare la geometrie des CHAMBRES, la plus large des deux : une image
# partagee par les deux grilles — r-standard, r-mezzanine — doit rester nette
# dans la plus grande case. Sans cette declaration, une carte de 279 px se
# faisait servir l'image pleine, parce que sizes annoncait 700 px.
SIZES_CARTES = ('(max-width:720px) calc(100vw - 48px), '
                '(max-width:1024px) calc((100vw - 72px) / 2), '
                '(max-width:1287px) calc((100vw - 96px) / 3), 381px')
CARTES = ('r-standard', 'ig-baldaquin', 'r-wax', 'r-anglaise', 'r-mezz2',
          'r-mezzanine', 'r-arabe', 'g-aerien', 'g-terrasse')

html = versionner(responsive(dimensionner(html), hero='hero-chambre-wax',
                             sizes={n: SIZES_CARTES for n in CARTES}))
# En dernier : le JSON-LD injecte plus haut porte lui aussi l'adresse.
html = html.replace('{{MAIL}}', MAIL)

assert '{{' not in html, 'un placeholder n a pas ete remplace'
io.open('index.html', 'w', encoding='utf-8').write(html.replace('</body>', JS_BANDEAU + '</body>'))
print('index.html            ok')
