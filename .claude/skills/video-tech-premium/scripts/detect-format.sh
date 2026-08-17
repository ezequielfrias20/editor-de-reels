#!/usr/bin/env bash
# Detecta el formato de salida a partir del video fuente.
#
#   scripts/detect-format.sh assets/footage/mi-video.mov
#
# Imprime: FORMAT / CANVAS / SOURCE / RATIO  (parseable con grep+cut)
# Tiene en cuenta la rotación embebida — los videos de iPhone se almacenan
# apaisados con metadato rotate=-90, así que width/height crudos mienten.

set -euo pipefail

src="${1:?uso: detect-format.sh <video>}"
[ -f "$src" ] || { echo "error: no existe $src" >&2; exit 1; }

probe() {
  # Sin pipes: cerrar el pipe temprano mata a ffprobe con SIGPIPE bajo pipefail.
  # Devuelve la primera línea NO VACÍA — `side_data=rotation` emite una línea en
  # blanco por cada stream sin side data antes del valor real.
  local out line
  out=$(ffprobe -v error -select_streams v:0 -show_entries "$1" -of csv=p=0 "$src" 2>/dev/null || true)
  while IFS= read -r line; do
    # csv=p=0 deja comas de campos vacíos cuando el stream trae side data
    line=${line//,/}
    if [ -n "$line" ]; then printf '%s' "$line"; return; fi
  done <<< "$out"
}

w=$(probe stream=width)
h=$(probe stream=height)

# ffmpeg >=7 expone la rotación en side_data; versiones viejas usan el tag 'rotate'
rot=$(probe side_data=rotation)
[ -z "$rot" ] && rot=$(probe stream_tags=rotate)
rot=${rot:-0}
rot=${rot%.*}          # descartar decimales
rot=${rot#-}           # valor absoluto

if [ "$rot" = "90" ] || [ "$rot" = "270" ]; then
  tmp=$w; w=$h; h=$tmp
fi

ratio=$(awk -v w="$w" -v h="$h" 'BEGIN{printf "%.4f", w/h}')

if awk -v r="$ratio" 'BEGIN{exit !(r > 0.95 && r < 1.05)}'; then
  echo "aviso: fuente casi cuadrada (${w}x${h}) — decidir formato a mano" >&2
fi

if awk -v r="$ratio" 'BEGIN{exit !(r < 1)}'; then
  format="9:16"; canvas="1080x1920"; label="REEL"
else
  format="16:9"; canvas="1920x1080"; label="YOUTUBE"
fi

echo "FORMAT $format"
echo "LABEL  $label"
echo "CANVAS $canvas"
echo "SOURCE ${w}x${h} (rot ${rot}°)"
echo "RATIO  $ratio"
