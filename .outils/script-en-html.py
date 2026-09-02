# -*- coding: utf-8 -*-
"""Transforme script-oral.md en une page imprimable.

Le script se lit en reunion, un doigt sur la page. La mise en forme sert donc
une seule chose : distinguer d'un coup d'oeil CE QUI SE DIT de CE QUI SE FAIT.
Les repliques sont en serif, filet bronze. Les indications scéniques sont en
gris, en retrait. On ne confond pas les deux, meme en diagonale.

Une diapositive par page : on tourne la feuille au rythme du support.
"""
import io
import re

SRC = 'script-oral.md'
OUT = 'script-oral.html'

# ── Formatage en ligne ─────────────────────────────────────────────────────


def ech(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def enligne(t):
    t = ech(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'`([^`]+?)`', r'<code>\1</code>', t)
    # Typographie francaise : espace insecable a l interieur des
    # guillemets et devant les ponctuations doubles. Sans elle, un
    # guillemet fermant se retrouve seul en debut de ligne.
    t = t.replace('« ', '« ').replace(' »', ' »')
    t = re.sub(' ([?!;:])', ' ' + chr(92) + '1', t)
    return t


def rendre(md):
    lignes = md.split(chr(10))
    out = []
    i = [0]                       # compteur partage avec les fonctions internes
    titre_pose = [False]
    section_ouverte = [False]

    def fermer():
        if section_ouverte[0]:
            out.append('</section>')

    def suite(depart, prefixes):
        """Texte d'un point de liste, lignes de continuation comprises.

        Un point qui deborde sur la ligne suivante appartient encore au point :
        sans cela sa fin sortait de la liste et devenait un paragraphe
        orphelin, en pleine page.
        """
        bloc = [depart]
        while i[0] < len(lignes):
            c = lignes[i[0]]
            nue = c.strip()
            if (not nue or not c[:1].isspace()
                    or nue.startswith(prefixes)
                    or re.match(r'^\d+\. ', nue)):
                break
            bloc.append(nue)
            i[0] += 1
        return ' '.join(bloc)

    while i[0] < len(lignes):
        nu = lignes[i[0]].strip()

        if not nu or nu == '---':
            i[0] += 1
            continue

        if nu.startswith('# ') and not titre_pose[0]:
            titre_pose[0] = True
            out.append('<h1>%s</h1>' % enligne(nu[2:]))
            i[0] += 1
            continue

        # Une section par page : on tourne la feuille au rythme du support.
        if nu.startswith('## '):
            fermer()
            section_ouverte[0] = True
            t = nu[3:]
            m = re.match(r'^(.*?) — (\d+ à \d+ min)$', t)
            out.append('<section>')
            if m:
                out.append('<h2>%s<span class="min">%s</span></h2>'
                           % (enligne(m.group(1)), ech(m.group(2))))
            else:
                out.append('<h2>%s</h2>' % enligne(t))
            i[0] += 1
            continue

        if nu.startswith('### '):
            out.append('<h3>%s</h3>' % enligne(nu[4:]))
            i[0] += 1
            continue

        # Ce qui se dit : lignes « > » consecutives = une replique
        if nu.startswith('>'):
            bloc = []
            while i[0] < len(lignes) and lignes[i[0]].strip().startswith('>'):
                bloc.append(lignes[i[0]].strip().lstrip('>').strip())
                i[0] += 1
            texte = ' '.join(x for x in bloc if x)
            fort = texte.startswith('**') and texte.rstrip().endswith('**')
            out.append('<p class="dire%s">%s</p>'
                       % (' fort' if fort else '', enligne(texte)))
            continue

        # Ce qui se fait : *[ ... ]*, parfois sur plusieurs lignes
        if nu.startswith('*['):
            bloc = []
            while i[0] < len(lignes):
                bloc.append(lignes[i[0]].strip())
                fini = lignes[i[0]].strip().endswith(']*')
                i[0] += 1
                if fini:
                    break
            texte = ' '.join(bloc)[2:-2].strip()
            out.append('<p class="faire">%s</p>' % enligne(texte))
            continue

        if nu.startswith('|'):
            rangs = []
            while i[0] < len(lignes) and lignes[i[0]].strip().startswith('|'):
                rangs.append([c.strip() for c in
                              lignes[i[0]].strip().strip('|').split('|')])
                i[0] += 1
            rangs = [r for r in rangs
                     if not all(set(c) <= set('-: ') for c in r)]
            if rangs:
                out.append('<table><thead><tr>%s</tr></thead><tbody>'
                           % ''.join('<th>%s</th>' % enligne(c)
                                     for c in rangs[0]))
                for r in rangs[1:]:
                    out.append('<tr>%s</tr>'
                               % ''.join('<td>%s</td>' % enligne(c) for c in r))
                out.append('</tbody></table>')
            continue

        if re.match(r'^- \[ \] ', nu):
            out.append('<ul class="cocher">')
            while (i[0] < len(lignes)
                   and re.match(r'^- \[ \] ', lignes[i[0]].strip())):
                d = lignes[i[0]].strip()[6:]
                i[0] += 1
                out.append('<li>%s</li>' % enligne(suite(d, ('- ', '#', '>', '|', '*['))))
            out.append('</ul>')
            continue

        if nu.startswith('- '):
            out.append('<ul>')
            while i[0] < len(lignes) and lignes[i[0]].strip().startswith('- '):
                d = lignes[i[0]].strip()[2:]
                i[0] += 1
                out.append('<li>%s</li>' % enligne(suite(d, ('- ', '#', '>', '|', '*['))))
            out.append('</ul>')
            continue

        if re.match(r'^\d+\. ', nu):
            out.append('<ol>')
            while (i[0] < len(lignes)
                   and re.match(r'^\d+\. ', lignes[i[0]].strip())):
                d = re.sub(r'^\d+\. ', '', lignes[i[0]].strip())
                i[0] += 1
                out.append('<li>%s</li>' % enligne(suite(d, ('- ', '#', '>', '|', '*['))))
            out.append('</ol>')
            continue

        # Paragraphe : lignes consecutives recollees
        bloc = []
        while i[0] < len(lignes):
            c = lignes[i[0]].strip()
            if (not c or c.startswith(('#', '>', '- ', '|', '*[', '---'))
                    or re.match(r'^\d+\. ', c)):
                break
            bloc.append(c)
            i[0] += 1
        texte = ' '.join(bloc)
        cl = ' class="chapeau"' if texte.startswith('**Si elle') else ''
        out.append('<p%s>%s</p>' % (cl, enligne(texte)))

    fermer()
    return chr(10).join(out)


CSS = """
:root{
  --ink:#2A1E13; --muted:#7A6A58; --line:#E6DED2;
  --bronze:#8A6534; --bronze-2:#B98A50; --sable:#F7F3EC;
  --rouge:#A6412F;
  --f-t:"Marcellus",Georgia,serif; --f-b:"Karla",Calibri,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--f-b);font-size:13.5px;line-height:1.6;color:var(--ink);
     background:#fff;-webkit-font-smoothing:antialiased}
.page{max-width:760px;margin:0 auto;padding:30px 38px 44px}

h1{font-family:var(--f-t);font-size:31px;line-height:1.15;font-weight:400;
   margin-bottom:8px}
h2{font-family:var(--f-t);font-size:21px;font-weight:400;margin:0 0 12px;
   padding-bottom:8px;border-bottom:1px solid var(--line);
   display:flex;justify-content:space-between;align-items:baseline;gap:16px}
h2 .min{font-family:var(--f-b);font-size:10.5px;letter-spacing:.16em;
        text-transform:uppercase;color:var(--bronze);font-weight:700;
        white-space:nowrap}
h3{font-family:var(--f-t);font-size:16.5px;font-weight:400;margin:20px 0 2px}
p{margin:8px 0}
strong{font-weight:700}
code{font-family:Consolas,monospace;font-size:12px;background:var(--sable);
     padding:1px 5px}

/* Ce qui se dit */
.dire{border-left:3px solid var(--bronze);padding:3px 0 3px 16px;margin:11px 0;
      text-wrap:pretty;
      font-family:var(--f-t);font-size:15.5px;line-height:1.55}
.dire.fort{border-left-color:var(--rouge);font-weight:400}
.dire.fort strong{font-weight:400;color:var(--rouge)}

/* Ce qui se fait */
.faire{color:var(--muted);font-style:italic;font-size:12.5px;
       padding-left:16px;border-left:1px dotted var(--line);margin:10px 0}

.chapeau{margin-top:14px}

table{width:100%;border-collapse:collapse;margin:12px 0 4px;font-size:12.5px}
th{text-align:left;font-size:10px;letter-spacing:.13em;text-transform:uppercase;
   color:var(--muted);font-weight:700;padding:0 12px 6px 0;
   border-bottom:1px solid var(--line)}
td{padding:8px 12px 8px 0;border-bottom:1px solid var(--line);
   vertical-align:top}
tr:last-child td{border-bottom:0}

/* Retrait suspendu : une ligne qui passe a la ligne doit s'aligner sous le
   texte, pas sous le numero. */
ul,ol{margin:8px 0;padding-left:24px}
li{margin:4px 0}
ul.cocher{list-style:none;margin-left:0}
ul.cocher li{padding-left:24px;position:relative}
ul.cocher li:before{content:"";position:absolute;left:0;top:3px;
  width:12px;height:12px;border:1.5px solid var(--bronze-2)}

section{margin-bottom:26px}

@media print{
  @page{margin:14mm 12mm}
  .page{max-width:none;padding:0}
  /* Une diapositive par page : on tourne la feuille au rythme du support. */
  section{break-before:page;margin-bottom:0}
  section:first-of-type{break-before:auto}
  h1,h2,h3{break-after:avoid}
  /* Une replique coupee en deux se lit mal a voix haute. */
  .dire,.faire,tr,li{break-inside:avoid}
  table{break-inside:auto}
}
"""


def main():
    md = io.open(SRC, encoding='utf-8').read()
    corps = rendre(md)
    html = (
        '<meta charset="utf-8">\n'
        '<title>Script oral — 7 septembre 2026</title>\n'
        '<link href="https://fonts.googleapis.com/css2?'
        'family=Marcellus&family=Karla:wght@300;400;500;600;700&display=swap"'
        ' rel="stylesheet">\n'
        '<style>' + CSS + '</style>\n'
        '<div class="page">\n' + corps + '\n</div>\n')
    io.open(OUT, 'w', encoding='utf-8', newline='').write(html)
    print('ecrit : %s (%d octets)' % (OUT, len(html.encode('utf-8'))))
    print('sections : %d' % corps.count('<section>'))
    print('repliques : %d' % corps.count('class="dire'))
    print('indications : %d' % corps.count('class="faire"'))


if __name__ == '__main__':
    main()
