#!/usr/bin/env bash
# Aplica el plan de cortes a un corte bruto de revisión. NO toca el original.
#
#   scripts/rough-cut.sh "VIDEOS ORIGINALES/1.MOV" cuts/1.json out/1-rough.mp4
#
# Usa select/aselect en una sola pasada (exacto al frame).
#
# NO usar una cadena de `afade` para suavizar junturas: afade=t=in:st=X pone a CERO
# todo lo anterior a X, así que encadenar un fade-in por segmento deja el audio mudo
# (-91 dB). No hace falta de todos modos — cada corte cae dentro de un silencio.

set -euo pipefail

src="${1:?falta el video fuente}"
plan="${2:?falta el plan de cortes}"
out="${3:?falta la salida}"

mkdir -p "$(dirname "$out")"

expr=$(python3 -c "
import json,sys
k=json.load(open('$plan'))['keeps']
print('+'.join(f\"between(t,{s['start']:.3f},{s['end']:.3f})\" for s in k))
")

echo "segmentos conservados: $(python3 -c "import json;print(len(json.load(open('$plan'))['keeps']))")"
echo "codificando…"

ffmpeg -hide_banner -v warning -stats -y -i "$src" \
  -vf "select='${expr}',setpts=N/FRAME_RATE/TB" \
  -af "aselect='${expr}',asetpts=N/SR/TB" \
  -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 160k -movflags +faststart \
  "$out"

echo
echo "-> $out"
ffprobe -v error -show_entries format=duration -show_entries stream=width,height \
  -of default=nw=1 "$out" | grep -v '^$'
