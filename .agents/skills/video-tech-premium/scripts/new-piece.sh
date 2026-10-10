#!/usr/bin/env bash
# Prepara una pieza nueva: numera el hueco libre, extrae el audio y deja el
# plan.json en blanco listo para escribir.
#
#     scripts/new-piece.sh "VIDEOS ORIGINALES/2.MOV"        # numera sola
#     scripts/new-piece.sh "VIDEOS ORIGINALES/2.MOV" 7      # fuerza la pieza 7
#
# No transcribe ni corta: eso son los pasos 2-4 del pipeline y cuestan API o
# minutos. Aquí solo se monta el andamio y se imprime qué toca a continuación.
set -euo pipefail

SRC="${1:?uso: new-piece.sh <video> [numero]}"
[ -f "$SRC" ] || { echo "no existe: $SRC" >&2; exit 1; }

SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Siguiente número libre, mirando las tres carpetas por si una quedó a medias.
if [ $# -ge 2 ]; then
  N="$2"
else
  N=1
  while [ -e "transcripts/$N.json" ] || [ -e "cuts/$N.json" ] || [ -d "videos/$N" ]; do
    N=$((N+1))
  done
fi

if [ -d "videos/$N" ]; then
  echo "la pieza $N ya existe (videos/$N). Pasa otro número si quieres otra." >&2
  exit 1
fi

mkdir -p transcripts cuts out assets/audio assets/gen "videos/$N/public"

echo "── pieza $N ─────────────────────────────────────────"
"$SKILL/scripts/detect-format.sh" "$SRC"
FORMAT=$("$SKILL/scripts/detect-format.sh" "$SRC" | awk '/^LABEL/{print $2}')

# Audio mono 16k FLAC: ~1 % del tamaño del original y es lo que quiere AssemblyAI.
if [ ! -f "assets/audio/$N.flac" ]; then
  ffmpeg -v error -i "$SRC" -vn -ac 1 -ar 16000 -c:a flac "assets/audio/$N.flac"
  echo "audio      assets/audio/$N.flac"
fi

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$SRC")

cat > "videos/$N/plan.json" <<JSON
{
  "format": "${FORMAT:-REEL}",
  "_source": "$SRC",
  "_duration_source": $DUR,
  "_pendiente": "TODOS los tiempos van en segundos de la LINEA DEL CORTE, no del fuente. Divide el transcript en unidades semanticas y decide, para cada una, que recurso la explica mejor. Cambio de imagen cada 1-2.5 s.",
  "_capas": "shots = el metraje y sus punch-ins · cards = rotulos flotantes · visuals = lo que ocupa el lienzo",
  "keywords": [],
  "voice_gain": 0.70,
  "music": {"src": "assets/music/bed-tech.mp3", "fade_in": 1.0, "fade_out": 2.6},
  "shots": [
    {"at": 0.0, "kind": "full", "zoom": 1.10, "anchor": 0.44}
  ],
  "cards": [],
  "visuals": [],
  "sfx": []
}
JSON
echo "plan       videos/$N/plan.json (esqueleto)"
echo
echo "siguiente:"
echo "  1. scripts/transcribe.py assets/audio/$N.flac transcripts/$N.json"
echo "  2. scripts/plan-cuts.py transcripts/$N.json cuts/$N.json $DUR"
echo "  3. scripts/rough-cut.sh \"$SRC\" cuts/$N.json out/$N-rough.mp4"
echo "  4. scripts/measure-face.py out/$N-rough.mp4 assets/face-$N.json"
echo "  5. color (§6 de SKILL.md) -> videos/$N/public/input-video.mp4"
echo "  6. grabacion de pantalla, si la hay: scripts/screen-tour.py videos/$N/screen-tour.json --preview"
echo "  7. musica: scripts/make-music-bed.py assets/music/bed-tech.mp3 --dur 70"
echo "  8. escribir videos/$N/plan.json   <- el trabajo creativo"
echo "  9. scripts/build-composition.py --project . --piece $N"
