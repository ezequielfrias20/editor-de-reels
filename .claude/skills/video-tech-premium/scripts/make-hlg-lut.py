#!/usr/bin/env python3
"""Genera el LUT que lleva el metraje HLG del iPhone al aspecto ORIGINAL en SDR.

    scripts/make-hlg-lut.py assets/hlg-to-709.cube

Objetivo: NO estilizar. Reproducir en BT.709 exactamente lo que macOS muestra al
reproducir el .MOV original — ni el lavado de reetiquetar sin convertir, ni el
turquesa saturado de una conversión física ingenua.

Los parámetros salen de calibrar contra un frame de referencia generado con el
gestor de color de macOS (`qlmanage`), buscando el mínimo error en saturación,
negros, luminancia media y altas luces. Resultado del ajuste: error 6.6 sobre
las cuatro métricas (la conversión física pura daba 53).

Se usa un modelo de curva tonal, no la cadena física: HLG está diseñado para ser
retrocompatible con SDR, así que su señal ya está cerca de una gamma. Forzar la
matriz BT.2020->BT.709 sobresaturaba (el ajuste eligió gamut 0.00 por su cuenta).
"""
import json
import sys
from pathlib import Path

import numpy as np

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
SIZE = 33

# Los parámetros salen de scripts/calibrate-hlg.py. Los de aquí son el respaldo
# calibrado para VIDEOS ORIGINALES/1.MOV (error 6.6 sobre las cuatro métricas).
_p = ROOT / "assets" / "hlg-params.json"
if _p.exists():
    _d = json.loads(_p.read_text())
    GAMMA, GAIN, LIFT, SAT = _d["gamma"], _d["gain"], _d["lift"], _d["sat"]
else:
    GAMMA, GAIN, LIFT, SAT = 1.65, 0.85, 0.06, 1.20


def convert(rgb):
    y = np.clip(GAIN * np.power(np.clip(rgb, 0, 1), GAMMA) + LIFT, 0, 1)
    lum = (0.299 * y[..., 0] + 0.587 * y[..., 1] + 0.114 * y[..., 2])[..., None]
    return np.clip(lum + SAT * (y - lum), 0, 1)


def main():
    dest = Path(sys.argv[1] if len(sys.argv) > 1 else "assets/hlg-to-709.cube")
    g = np.linspace(0.0, 1.0, SIZE)
    b, gr, r = np.meshgrid(g, g, g, indexing="ij")   # .cube recorre R más rápido
    out = convert(np.stack([r, gr, b], axis=-1).reshape(-1, 3))

    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w") as f:
        f.write("# HLG (iPhone) -> BT.709 conservando el aspecto original\n")
        f.write(f"# gamma {GAMMA} gain {GAIN} lift {LIFT} sat {SAT}\n")
        f.write(f"LUT_3D_SIZE {SIZE}\n\n")
        for v in out:
            f.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
    print(f"-> {dest}  ({SIZE}^3, gamma {GAMMA} gain {GAIN} lift {LIFT} sat {SAT})")


if __name__ == "__main__":
    main()
