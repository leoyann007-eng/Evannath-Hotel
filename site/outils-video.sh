#!/bin/sh
# Fabrique la boucle du hero a partir du film de presentation.
# ffmpeg est installe par winget (Gyan.FFmpeg) et n'est pas forcement dans le PATH.
FF="$LOCALAPPDATA/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0-full_build/bin/ffmpeg.exe"
[ -x "$FF" ] || FF=ffmpeg

DEBUT=158      # bornes du plan continu retenu, reperees par detection de coupes
DUREE=11       # une seconde de plus que la boucle : elle sert au fondu
FONDU=1

# 1. extrait de travail, sans son, en haute qualite
"$FF" -v error -ss $DEBUT -i video/presentation-hotel.mp4 -t $DUREE -an \
      -c:v libx264 -crf 16 -preset veryfast -pix_fmt yuv420p /tmp/brut.mp4 -y

# 2. boucle sans raccord : la premiere seconde fondue par-dessus la derniere.
#    Le decalage vaut DUREE-2*FONDU pour que l'image finale coincide avec la
#    premiere image de la sortie — sinon la boucle saute d'une seconde.
DECALAGE=$((DUREE - 2 * FONDU))
FILTRE="[0]split[corps][tete];\
[tete]trim=duration=$FONDU,format=yuva420p,fade=t=in:st=0:d=$FONDU:alpha=1,setpts=PTS+($DECALAGE/TB)[t];\
[corps]trim=start=$FONDU,setpts=PTS-STARTPTS[c];\
[c][t]overlay=eof_action=pass:format=auto[v]"

"$FF" -v error -i /tmp/brut.mp4 -filter_complex "$FILTRE" -map "[v]" -an \
      -c:v libx264 -profile:v high -preset slow -crf 26 -maxrate 1500k -bufsize 3000k \
      -pix_fmt yuv420p -movflags +faststart -r 30 video/hero-nuit.mp4 -y

"$FF" -v error -i /tmp/brut.mp4 -filter_complex "$FILTRE" -map "[v]" -an \
      -c:v libvpx-vp9 -crf 36 -b:v 0 -row-mt 1 -deadline good -cpu-used 2 \
      -pix_fmt yuv420p video/hero-nuit.webm -y

# 3. l'affiche est la premiere image du clip, pas une photo d'a cote
"$FF" -v error -i video/hero-nuit.mp4 -frames:v 1 -vf scale=1280:-1 -q:v 4 img/opt/hero-nuit-affiche.jpg -y

ls -la video/hero-nuit.* img/opt/hero-nuit-affiche.jpg
