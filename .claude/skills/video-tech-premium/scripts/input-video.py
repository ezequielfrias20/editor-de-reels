#!/usr/bin/env python3
"""Arma videos/<n>-<p>/public/input-video.mp4 desde el corte bruto, con la VOZ LIMPIA.

    .venv/bin/python scripts/input-video.py --piece 9 --plataforma instagram
    .venv/bin/python scripts/input-video.py --piece 9 --plataforma instagram --lut assets/hlg-to-709.cube

La voz del iPhone llega ya comprimida (rango ~4 LU) y tocando 0 dBFS, con la presencia
(3–4 kHz) adelante: a Ezequiel le sonó «muy dura» (pieza 9, 2026-10-10). La cadena es
suave a propósito y no comprime más:

- `highpass` 75 Hz: rumor y golpes de mesa, nada de voz.
- `afftdn` leve: suelo de ruido de la sala, sin el «agua» de una reducción fuerte.
- `deesser`: las eses y las tes.
- EQ: −3 dB en 3,2 kHz (la dureza), +1,5 dB en 190 Hz (cuerpo), −1,5 dB sobre 9 kHz.
- Ganancia MEDIDA para dejar la voz en −17 LUFS integrados (lo que traía), así el balance
  voz / música / efectos de `build-composition.py` no cambia.
- `alimiter` a −1,5 dBFS: los picos dejan de tocar el techo.

El video no cambia (con `--lut`, el camino HDR de §8). Imprime la medición antes y después.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

LUFS_OBJETIVO = -17.0
CADENA = ("highpass=f=75,"
          "afftdn=nr=10:nf=-55:tn=1,"
          "deesser=i=0.5:m=0.5:f=0.5,"
          "equalizer=f=3200:width_type=q:w=1.1:g=-3,"
          "equalizer=f=190:width_type=o:w=1.2:g=1.5,"
          "highshelf=f=9000:g=-1.5")
LIMITE = "alimiter=limit=0.84:attack=5:release=80:level=disabled"


def medir(src: Path, af: str = "") -> dict:
    filtro = (af + "," if af else "") + "ebur128=peak=true"
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-vn", "-af", filtro,
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    resumen = err[err.rfind("Summary:"):]
    out = {}
    for clave, patron in (("I", r"I:\s+(-?[\d.]+) LUFS"), ("LRA", r"LRA:\s+([\d.]+) LU"),
                          ("pico", r"Peak:\s+(-?[\d.]+) dBFS")):
        m = re.search(patron, resumen)
        if not m:
            raise SystemExit(f"ERROR: no se pudo medir {clave} de {src}")
        out[clave] = float(m.group(1))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--piece", required=True)
    ap.add_argument("--plataforma", required=True)
    ap.add_argument("--lut", type=Path, help="LUT HLG→709 si la fuente es HDR (§8)")
    a = ap.parse_args(argv)
    root = a.project.resolve()
    v = f"{a.piece}-{a.plataforma}"
    src = root / "out" / f"{v}-rough.mp4"
    if not src.exists():
        print(f"ERROR: falta {src.relative_to(root)} (scripts/preparar-version.sh)", file=sys.stderr)
        return 1
    dst = root / "videos" / v / "public" / "input-video.mp4"
    dst.parent.mkdir(parents=True, exist_ok=True)

    antes = medir(src)
    eq = medir(src, CADENA)
    ganancia = round(LUFS_OBJETIVO - eq["I"], 2)
    af = f"{CADENA},volume={ganancia}dB,{LIMITE}"
    vf = (["-vf", f"lut3d={a.lut},setparams=color_primaries=bt709:color_trc=bt709:"
                  "colorspace=bt709:range=tv"] if a.lut else [])
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(src), *vf,
                        "-af", af, "-c:v", "libx264", "-crf", "18", "-g", "30", "-keyint_min", "30",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "256k",
                        str(dst)], capture_output=True, text=True)
    if r.returncode:
        print(f"ERROR: ffmpeg falló: {r.stderr.strip()[-400:]}", file=sys.stderr)
        return 1
    despues = medir(dst)
    print(f"voz {v}: {antes['I']:.1f} LUFS · LRA {antes['LRA']:.1f} · pico {antes['pico']:.1f} dBFS"
          f"  →  {despues['I']:.1f} LUFS · LRA {despues['LRA']:.1f} · pico {despues['pico']:.1f} dBFS"
          f"  (ganancia {ganancia:+.2f} dB)")
    print(f"✓ {dst.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
