#!/usr/bin/env python3
"""Comprueba que una pasada `editar` o `corregir` dejó todas sus versiones.

    scripts/validar-salida.py --piece 7 --version v2

Por cada versión del pedido (instagram siempre; tiktok si se subió su clip de CTA,
`Pedido.plataformas`): existe videos/<n>/output-<p>-v<k>.mp4,
dura lo que dice cuts/<n>-<p>.json (final_duration, ±0,5 s) y su copia está en
VIDEOS EDITADOS/. El dashboard lo corre al terminar la pasada.
"""
import argparse
import json
import sys
from pathlib import Path

from pieza import PiezaError, cargar_pedido, probe

TOLERANCIA = 0.5


def problemas(root: Path, n: int, k: int) -> list[str]:
    root = Path(root)
    out: list[str] = []
    try:
        plataformas = cargar_pedido(root, n).plataformas
    except PiezaError as e:
        return [str(e)]
    for p in plataformas:
        mp4 = root / "videos" / str(n) / f"output-{p}-v{k}.mp4"
        copia = root / "VIDEOS EDITADOS" / f"{n}-{p}-v{k}.mp4"
        if not mp4.exists():
            out.append(f"falta videos/{n}/output-{p}-v{k}.mp4")
            continue
        if not copia.exists() or copia.stat().st_size != mp4.stat().st_size:
            out.append(f"falta la copia en VIDEOS EDITADOS/{copia.name}")
        cortes = root / "cuts" / f"{n}-{p}.json"
        if cortes.exists():
            esperado = float(json.loads(cortes.read_text())["final_duration"])
            try:
                real = probe(mp4).duracion
            except PiezaError as e:
                out.append(str(e))
                continue
            if abs(real - esperado) > TOLERANCIA:
                out.append(f"output-{p}-v{k}.mp4 dura {real:.2f} s y el corte {esperado:.2f} s")
        else:
            out.append(f"falta cuts/{n}-{p}.json para medir la duración")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Valida los MP4 de una pasada")
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--piece", required=True, type=int)
    ap.add_argument("--version", required=True, help="v2 o 2")
    a = ap.parse_args(argv)
    k = int(a.version.lstrip("v"))
    ps = problemas(a.project.resolve(), a.piece, k)
    if ps:
        print(f"✗ {len(ps)} problema(s):")
        for p in ps:
            print(f"  - {p}")
        return 1
    print(f"✓ pieza {a.piece} v{k}: todas las versiones entregadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
