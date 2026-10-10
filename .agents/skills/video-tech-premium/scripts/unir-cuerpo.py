#!/usr/bin/env python3
"""Une las tomas de cuerpo de una pieza del dashboard en out/<n>-fuente.mov.

    scripts/unir-cuerpo.py --project . --piece 7

Antes de unir comprueba que TODOS los clips con voz (cuerpo y CTA) tienen la misma
orientación: un CTA horizontal con un cuerpo vertical no se puede empalmar y conviene
saberlo antes de gastar AssemblyAI. Es el primer paso de la pasada `propuesta`.
"""
import argparse
import sys
from pathlib import Path

from pieza import PiezaError, cargar_pedido, probe, unir


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--piece", required=True, type=int)
    a = ap.parse_args(argv)
    root = a.project.resolve()
    try:
        pedido = cargar_pedido(root, a.piece)
        cuerpos = [pedido.ruta(c) for c in pedido.de_rol("cuerpo")]
        con_voz = cuerpos + [pedido.ruta(c) for c in pedido.de_rol("cta")]
        infos = {p.name: probe(p).orientacion for p in con_voz}
        if len(set(infos.values())) > 1:
            detalle = ", ".join(f"{k} {v}" for k, v in infos.items())
            raise PiezaError(f"el cuerpo y los CTA no tienen la misma orientación: {detalle}")
        salida = root / "out" / f"{a.piece}-fuente.mov"
        modo = unir(cuerpos, salida)
    except PiezaError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"✓ {salida.relative_to(root)} · {len(cuerpos)} toma(s) · {modo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
