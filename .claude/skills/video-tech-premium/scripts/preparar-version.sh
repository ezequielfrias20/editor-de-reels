#!/usr/bin/env bash
# Deja lista una versión (cuerpo + CTA de una plataforma) hasta el paso 5 del pipeline:
# fuente unida, audio, corte bruto, auditoría de respiraciones y medición de cara.
#
#     scripts/preparar-version.sh 7 instagram      # desde la raíz del proyecto
#
# Requiere la pasada 1 del cuerpo y del CTA: transcripts/ y cuts/ de los dos.
# Si la auditoría de respiraciones falla, el script para (paso 4b: no se sigue).
set -euo pipefail

N="${1:?uso: preparar-version.sh <pieza> <plataforma>}"
P="${2:?uso: preparar-version.sh <pieza> <plataforma>}"
V="$N-$P"
S="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$S/armar-version.py" datos --project . --piece "$N" --plataforma "$P"
mkdir -p assets/audio out
ffmpeg -hide_banner -v error -y -i "out/$V-fuente.mov" -vn -ac 1 -ar 16000 -c:a flac "assets/audio/$V.flac"
"$S/rough-cut.sh" "out/$V-fuente.mov" "cuts/$V.json" "out/$V-rough.mp4"
python3 "$S/audit-breaths.py" --project . --piece "$V"
python3 "$S/measure-face.py" "out/$V-rough.mp4" "assets/face-$V.json"
echo "✓ versión $V lista para el EDL"
