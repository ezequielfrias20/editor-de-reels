#!/usr/bin/env python3
"""Calibra la conversión HLG->BT.709 contra el gestor de color de macOS.

    scripts/calibrate-hlg.py out/1-rough.mp4 5.5

Cada metraje puede necesitar parámetros distintos (luz, exposición, cámara), así que
esto vuelve a correrse por pieza. Escribe assets/hlg-params.json, que es lo que lee
`make-hlg-lut.py`.

El objetivo NO es estilizar: es reproducir en SDR lo que macOS muestra al reproducir el
original. La referencia se saca con `qlmanage`, que usa el mismo pipeline de color que
QuickTime.

Modelo: curva tonal (gamma, ganancia, lift, saturación). Se eligió frente a la cadena
física HLG porque HLG ya está diseñado para ser retrocompatible con SDR — la conversión
física pura sobresatura y aplasta los negros, y un ajuste con curvas 1D por canal produce
manchas de color en la piel.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

def _project_root() -> Path:
    """El PROYECTO es el directorio de trabajo, no donde vive el script.

    Estos scripts viajan dentro de la skill, así que `Path(__file__).parent.parent`
    apunta a la skill y no al proyecto que se está editando. Se ejecutan siempre
    desde la raíz del proyecto; si hay un .env más arriba, se sube a buscarlo.
    """
    cwd = Path.cwd().resolve()
    for d in (cwd, *cwd.parents):
        if (d / ".env").exists() or (d / "VIDEOS ORIGINALES").is_dir():
            return d
    return cwd


ROOT = _project_root()


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def reference_frame(src, t, tmp):
    """Frame gestionado por macOS: recorta un fragmento con las etiquetas HLG intactas."""
    snip = tmp / "snip.mov"
    run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-ss", str(t), "-t", "0.5",
         "-i", str(src), "-an", "-c:v", "libx264", "-crf", "12",
         "-pix_fmt", "yuv420p", str(snip)])
    run(["qlmanage", "-t", "-s", "1080", "-o", str(tmp), str(snip)])
    pngs = list(tmp.glob("*.png"))
    if not pngs:
        sys.exit("error: qlmanage no generó referencia")
    return Image.open(pngs[0]).convert("RGB")


def raw_frame(src, t, tmp):
    out = tmp / "raw.png"
    run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-ss", str(t),
         "-i", str(src), "-frames:v", "1", str(out)])
    return Image.open(out).convert("RGB")


def stats(a):
    mx, mn = a.max(-1), a.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0).mean() * 100
    lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    return np.array([sat, np.percentile(lum, 5) * 255,
                     lum.mean() * 255, np.percentile(lum, 95) * 255])


def apply(x, gamma, gain, lift, sat):
    y = np.clip(gain * np.power(np.clip(x, 0, 1), gamma) + lift, 0, 1)
    lum = (0.299 * y[..., 0] + 0.587 * y[..., 1] + 0.114 * y[..., 2])[..., None]
    return np.clip(lum + sat * (y - lum), 0, 1)


def main():
    src = Path(sys.argv[1])
    t = float(sys.argv[2]) if len(sys.argv) > 2 else 5.5

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        ref_img = reference_frame(src, t, tmp)
        raw_img = raw_frame(src, t, tmp).resize(ref_img.size, Image.LANCZOS)

    w, h = ref_img.size
    box = (int(w * .12), int(h * .18), int(w * .88), int(h * .82))
    R = np.asarray(ref_img.crop(box), float) / 255.0
    X = np.asarray(raw_img.crop(box), float) / 255.0

    target = stats(R)
    print(f"referencia macOS   satur {target[0]:.1f}%  negros {target[1]:.1f}  "
          f"media {target[2]:.1f}  altas {target[3]:.1f}")
    s0 = stats(X)
    print(f"crudo sin convertir satur {s0[0]:.1f}%  negros {s0[1]:.1f}  "
          f"media {s0[2]:.1f}  altas {s0[3]:.1f}\n")

    best = None
    for gamma in np.arange(0.9, 2.01, 0.05):
        for gain in np.arange(0.75, 1.31, 0.05):
            for lift in np.arange(-0.04, 0.061, 0.02):
                for sat in np.arange(1.0, 1.61, 0.05):
                    s = stats(apply(X, gamma, gain, lift, sat))
                    err = (2.0 * abs(s[2] - target[2]) + 1.5 * abs(s[1] - target[1])
                           + 1.5 * abs(s[3] - target[3]) + 3.0 * abs(s[0] - target[0]))
                    if best is None or err < best[0]:
                        best = (err, gamma, gain, lift, sat, s)

    err, gamma, gain, lift, sat, s = best
    print(f"ajuste  gamma {gamma:.2f}  gain {gain:.2f}  lift {lift:+.2f}  sat {sat:.2f}")
    print(f"result  satur {s[0]:.1f}%  negros {s[1]:.1f}  media {s[2]:.1f}  "
          f"altas {s[3]:.1f}   (error {err:.1f})")
    if err > 20:
        print("\n⚠ error alto: revisar que el frame de referencia y el crudo "
              "sean del mismo instante")

    dest = ROOT / "assets" / "hlg-params.json"
    dest.write_text(json.dumps({
        "gamma": round(float(gamma), 3), "gain": round(float(gain), 3),
        "lift": round(float(lift), 3), "sat": round(float(sat), 3),
        "error": round(float(err), 2), "source": str(src), "at": t,
    }, indent=2))
    print(f"\n-> {dest}   (ahora: scripts/make-hlg-lut.py)")


if __name__ == "__main__":
    main()
