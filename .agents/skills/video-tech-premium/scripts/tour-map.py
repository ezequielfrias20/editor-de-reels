#!/usr/bin/env python3
"""Traduce coordenadas de la GRABACIÓN a coordenadas del LIENZO.

    scripts/tour-map.py videos/3/screen-tour.json --rect 40,540,1000,820 \
        --at 1325,163,155,42 --at 1455,840,345,90

`clicks` y `boxes` del plan van en píxeles del **lienzo**, pero lo que uno mira
para elegirlos es un frame de la grabación, que está en píxeles del ORIGINAL.
Entre los dos hay tres transformaciones encadenadas —el `crop` del tramo, el
escalado a la resolución del recorrido y el `rect` que lo coloca en el lienzo—
y hacerlas a ojo produce cajas que caen fuera del elemento que quieren señalar.

Además dice **a qué tramo pertenece** cada punto y en qué segundo del recorrido
cae, que es lo que hace falta para que la caja entre cuando ese tramo está en
pantalla y no durante el anterior.

El `zoom` del tramo se tiene en cuenta: el empuje es hacia el centro del
recorte, así que un punto del borde se desplaza más que uno del medio. Sin
`--t` se calcula al principio del tramo (zoom inicial), que es cuando la caja
suele entrar.
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--rect", required=True,
                    help="rect del plan en el lienzo: x,y,w,h")
    ap.add_argument("--at", action="append", default=[], metavar="X,Y[,W,H]",
                    help="punto o caja en píxeles del ORIGINAL; repetible")
    ap.add_argument("--t", type=float, default=None,
                    help="segundo del RECORRIDO para el que calcular el zoom "
                         "(por defecto, el inicio del tramo)")
    a = ap.parse_args()

    spec = json.loads(Path(a.spec).read_text())
    ow, oh = spec.get("size", [1960, 1240])
    px, py, pw, ph = (int(v) for v in a.rect.split(","))
    segs = spec["segments"]

    # cada tramo ocupa un tramo del recorrido concatenado
    starts, acc = [], 0.0
    for s in segs:
        starts.append(acc)
        acc += s["dur"]

    print(f"recorrido {acc:.2f}s · salida {ow}×{oh} · rect del lienzo "
          f"[{px},{py},{pw},{ph}]\n")

    for spec_at in a.at:
        v = [float(x) for x in spec_at.split(",")]
        sx, sy = v[0], v[1]
        sw, sh = (v[2], v[3]) if len(v) >= 4 else (0.0, 0.0)

        hits = []
        for i, s in enumerate(segs):
            cx, cy, cw, ch = s["crop"]
            if not (cx <= sx <= cx + cw and cy <= sy <= cy + ch):
                continue
            z0, z1 = s.get("zoom", [1.0, 1.0])
            if a.t is not None and starts[i] <= a.t <= starts[i] + s["dur"]:
                f = (a.t - starts[i]) / max(1e-6, s["dur"])
                z = z0 + (z1 - z0) * f
            else:
                z = z0
            # el zoompan empuja hacia el CENTRO del recorte
            def conv(ux, uy):
                rx = (ux - cx - cw / 2) * z + cw / 2
                ry = (uy - cy - ch / 2) * z + ch / 2
                return px + rx * pw / cw, py + ry * ph / ch

            x0, y0 = conv(sx, sy)
            x1, y1 = conv(sx + sw, sy + sh)
            fuera = "" if 0 <= x0 and 0 <= y0 else "  ⚠ cae fuera del rect"
            hits.append((i, s.get("label", ""), starts[i],
                         starts[i] + s["dur"], z, x0, y0, x1 - x0, y1 - y0,
                         fuera))

        if not hits:
            print(f"[{sx:.0f},{sy:.0f}] — ningún tramo contiene ese punto\n")
            continue
        for i, label, t0, t1, z, x0, y0, w, h, fuera in hits:
            print(f"[{sx:.0f},{sy:.0f}{f',{sw:.0f},{sh:.0f}' if sw else ''}]"
                  f"  tramo {i} «{label}»  t {t0:.2f}-{t1:.2f} del recorrido "
                  f"(zoom {z:.3f}){fuera}")
            if sw:
                print(f"     box  -> [{x0:.0f}, {y0:.0f}, {w:.0f}, {h:.0f}]")
                print(f"     click-> [{x0 + w/2:.0f}, {y0 + h/2:.0f}]")
            else:
                print(f"     click-> [{x0:.0f}, {y0:.0f}]")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
