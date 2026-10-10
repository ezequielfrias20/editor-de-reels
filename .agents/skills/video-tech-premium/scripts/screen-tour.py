#!/usr/bin/env python3
"""Convierte una grabación de pantalla cruda en un recorrido editado.

    scripts/screen-tour.py <spec.json> [--preview]

Una grabación de pantalla cruda es el peor b-roll posible: apaisada, llena de
chrome del navegador y del sistema, y con el punto de interés ocupando el 8 %
del cuadro. Este script la convierte en lo que pide el lenguaje de la pieza:

    · **recorta el chrome** — pestañas, barra de direcciones, marcadores y dock
      quedan fuera. Lo que se ve es el PRODUCTO, no el navegador de quien grabó.
    · **encuadra el punto de interés** — cada tramo es un recorte distinto,
      elegido por lo que se está diciendo en ese segundo.
    · **empuja la cámara** — un zoom lento dentro de cada tramo para que la
      captura no se lea como una imagen fija.
    · **corta en duro** entre tramos, al ritmo del habla.

El spec es JSON:

    {
      "src": "VIDEOS ORIGINALES/2/pantalla.mov",
      "out": "assets/erp-tour.mp4",
      "size": [1960, 1240],          # 2× el tamaño en que se verá, por nitidez
      "segments": [
        {"label": "VENTA", "at": 33.0, "dur": 1.45,
         "crop": [170, 180, 1510, 955], "zoom": [1.00, 1.06]}
      ]
    }

`crop` es [x, y, w, h] en píxeles del ORIGINAL. `zoom` es el empuje de cámara
dentro del tramo (de → a), centrado en el recorte.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def probe_size(src):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(src)],
        capture_output=True, text=True).stdout.strip()
    w, h = out.split("x")
    return int(w), int(h)


def content_bounds(src, at):
    """Los bordes REALES del contenido, saltándose las barras negras.

    Una grabación de pantalla casi nunca llena el archivo: si la ventana no
    cubría todo el monitor, o si la resolución de captura no coincidía con la
    del escritorio, quedan barras negras a los lados. Un recorte que las pise
    mete una franja negra en mitad del mockup — y solo se ve al mirar el
    resultado, porque el recorte «cabe» en el archivo perfectamente.

    `cropdetect` de ffmpeg mide justo esto, así que aquí no se adivina.
    """
    out = subprocess.run(
        ["ffmpeg", "-v", "info", "-ss", str(at), "-i", str(src), "-frames:v", "6",
         "-vf", "cropdetect=limit=24:round=2:reset=0", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    last = None
    for line in out.splitlines():
        if "crop=" in line:
            last = line.split("crop=")[-1].strip()
    if not last:
        return None
    try:
        w, h, x, y = (int(v) for v in last.split(":"))
        return x, y, w, h
    except ValueError:
        return None


def check_exclusions(spec, i, seg, crop):
    """Zonas sucias de la grabación: el recorte no puede pisarlas.

    Una grabación de producto casi nunca está limpia. En estas hay dos cosas
    que no son el producto y que delatan que es una demo a medias:

      · el **indicador de dev** del framework (esa pastilla negra abajo a la
        izquierda que dice «Compiling…» / «Rendering…»);
      · un **toast de error** de validación, que en un video de venta se lee
        como que el producto falla.

    Ninguna se ve en el frame que uno mira al elegir el crop, porque aparecen
    solo unos segundos. Se declaran una vez en el spec y a partir de ahí el
    script falla antes de renderizar en vez de descubrirse en el MP4:

        "exclude": [
          {"t": [22.67, 36.87], "rect": [96, 990, 260, 90],
           "why": "indicador de dev del framework"}
        ]
    """
    x, y, w, h = crop
    t0, t1 = seg["at"], seg["at"] + seg["dur"]
    for ex in spec.get("exclude", []):
        e0, e1 = ex["t"]
        if t1 <= e0 or t0 >= e1:            # no coinciden en el tiempo
            continue
        ex_, ey, ew, eh = ex["rect"]
        if x + w <= ex_ or ex_ + ew <= x or y + h <= ey or ey + eh <= y:
            continue                        # no se solapan en el espacio
        sys.exit(
            f"segmento {i} ({seg.get('label','')}): el recorte "
            f"[{x},{y},{w},{h}] en t {t0:.2f}-{t1:.2f} pisa una zona sucia.\n"
            f"  {ex.get('why','zona excluida')} "
            f"en t {e0:.2f}-{e1:.2f}, rect [{ex_},{ey},{ew},{eh}]\n"
            f"  mueve el `at` fuera de esa ventana o el `crop` fuera del rect.")


def build(spec_path: Path, preview: bool = False) -> int:
    spec = json.loads(spec_path.read_text())
    root = Path.cwd()
    src = root / spec["src"]
    out = root / spec["out"]
    ow, oh = spec.get("size", [1960, 1240])
    fps = spec.get("fps", 30)
    segs = spec["segments"]

    if not src.exists():
        sys.exit(f"no existe la grabación: {src}")
    sw, sh = probe_size(src)
    target_ar = ow / oh

    tmp = out.parent / "_tour_parts"
    tmp.mkdir(parents=True, exist_ok=True)
    parts = []

    for i, s in enumerate(segs):
        x, y, w, h = s["crop"]
        if x < 0 or y < 0 or x + w > sw or y + h > sh:
            sys.exit(f"segmento {i} ({s.get('label','')}): el recorte "
                     f"[{x},{y},{w},{h}] se sale de {sw}×{sh}")
        cb = content_bounds(src, s["at"])
        if cb:
            bx, by, bw, bh = cb
            if x < bx or y < by or x + w > bx + bw or y + h > by + bh:
                sys.exit(
                    f"segmento {i} ({s.get('label','')}): el recorte "
                    f"[{x},{y},{w},{h}] pisa las barras negras del archivo.\n"
                    f"  contenido real en x {bx}..{bx+bw}, y {by}..{by+bh}\n"
                    f"  ajusta el crop para que quede dentro.")
        ar = w / h
        if abs(ar - target_ar) > 0.02:
            print(f"  ⚠ segmento {i} ({s.get('label','')}): recorte {ar:.3f} "
                  f"≠ salida {target_ar:.3f} — se deformaría, ajusta el crop")
        check_exclusions(spec, i, s, (x, y, w, h))
        z0, z1 = s.get("zoom", [1.0, 1.0])
        dur = s["dur"]
        n = max(1, round(dur * fps))

        # Empuje de cámara: zoompan trabaja sobre el recorte ya hecho y a la
        # resolución de salida, así que el zoom no come nitidez.
        part = tmp / f"{i:02d}.mp4"
        zexpr = f"{z0}+({z1}-{z0})*on/{max(1, n - 1)}"
        vf = (f"crop={w}:{h}:{x}:{y},scale={ow*2}:{oh*2}:flags=lanczos,"
              f"zoompan=z='{zexpr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":d=1:s={ow}x{oh}:fps={fps},setsar=1")
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(s["at"]), "-i", str(src),
               "-t", f"{dur:.3f}", "-an", "-vf", vf,
               "-c:v", "libx264", "-crf", "17", "-preset", "medium",
               "-pix_fmt", "yuv420p", "-r", str(fps), str(part)]
        subprocess.run(cmd, check=True)
        parts.append(part)
        print(f"  {i} {s.get('label',''):<10} {dur:.2f}s  crop {w}×{h} @{x},{y}  "
              f"zoom {z0}→{z1}")

        if preview:
            still = tmp / f"{i:02d}-preview.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(part),
                            "-frames:v", "1", str(still)], check=True)

    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(out)], check=True)

    total = sum(s["dur"] for s in segs)
    print(f"\n-> {out}  ({total:.2f}s, {ow}×{oh}, {len(segs)} tramos)")
    if preview:
        print(f"   previews en {tmp}/")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Recorrido editado de una grabación de pantalla")
    ap.add_argument("spec")
    ap.add_argument("--preview", action="store_true",
                    help="deja un PNG del primer frame de cada tramo")
    a = ap.parse_args()
    sys.exit(build(Path(a.spec), a.preview))


if __name__ == "__main__":
    main()
