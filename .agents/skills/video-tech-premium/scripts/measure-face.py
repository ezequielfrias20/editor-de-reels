#!/usr/bin/env python3
"""Mide dónde acaba la CARA en el metraje, para que el subtítulo nunca la pise.

    scripts/measure-face.py out/1-rough.mp4 assets/face.json [--samples 48]

Escribe `{chin_px, chin_frac, cx_frac, cy_frac, top_frac, width, height,
samples, hits}`. `chin_frac` es lo que usa el generador para la altura del
subtítulo, `cx_frac` / `cy_frac` para el ANCLAJE del reencuadre, y `top_frac`
para el gate que impide cortar la cara en un encuadre `band` (Mejora 2,
`check_face_top_clear` en `build-composition.py`): las tres son fracciones del
fuente, que es lo único que sobrevive al reencuadre de cada modo.

Tres estadísticos distintos porque miden tres cosas distintas:

- La barbilla usa el **percentil 95**, no el máximo: un solo falso positivo del
  detector (un reflejo, una mano) arrastraría el subtítulo hasta el borde
  inferior y arruinaría el encuadre de toda la pieza. El p95 absorbe esos
  atípicos y sigue dejando el 95 % de los frames cubiertos.
- El borde superior usa el **percentil 5**, el espejo del anterior: lo que
  importa aquí es el caso casi-peor en el que la cara sube más —más cerca de
  y0—, así que se toma el extremo BAJO de la distribución del borde superior
  en vez del alto. Igual que con la barbilla, el p5 (en vez del mínimo)
  absorbe el falso positivo aislado que arrastraría el gate a un valor
  imposible de cumplir.
- El centroide usa la **mediana**. Aquí no interesa cubrir un extremo sino dar
  con el sitio donde el sujeto ESTÁ, y un p95 horizontal devolvería el borde
  derecho de su recorrido, no su centro.

Las tres salen de las MISMAS muestras Haar y de la MISMA caja principal por
muestra, así que añadir el borde superior o el centroide no puede mover
`chin_frac`.

Requiere `opencv-python-headless<5` — la 5.x sacó `objdetect`/`CascadeClassifier`
del paquete headless, así que con la 5 esto no importa.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Mide la barbilla p95 del metraje")
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--samples", type=int, default=48)
    a = ap.parse_args()

    try:
        import cv2
    except ImportError:
        sys.exit("falta opencv: pip install 'opencv-python-headless<5'")
    if not hasattr(cv2, "CascadeClassifier"):
        sys.exit("este opencv no trae CascadeClassifier: pip install 'opencv-python-headless<5'")

    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", a.video], capture_output=True, text=True).stdout.strip())

    cap = cv2.VideoCapture(a.video)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    boxes = []
    for i in range(a.samples):
        t = dur * (i + 0.5) / a.samples
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = casc.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5,
                                      minSize=(int(h * 0.08), int(h * 0.08)))
        if len(faces):
            # Una mano o un tatuaje puede producir falsos positivos pequeños y
            # repetidos. Acumular TODAS las cajas hace que incluso el p95 caiga
            # en ese grupo inferior. El talking-head tiene un sujeto principal:
            # conservamos la caja de mayor área de cada muestra y después
            # calculamos el p95 temporal sobre esas detecciones principales.
            boxes.append(max(faces, key=lambda box: box[2] * box[3]))
    cap.release()

    if not boxes:
        sys.exit("no se detectó ninguna cara: revisa el metraje o pasa la medida a mano")

    # El Haar encuadra la cara sin mandíbula; el borde real cae algo más abajo.
    # Un 5 % del alto de la caja cubre esa diferencia sin empujar el subtítulo
    # más de lo necesario: pasarse de margen no es gratis, en `split` deja el
    # texto contra el borde inferior.
    chins = sorted(fy + fh * 1.05 for _, fy, _, fh in boxes)
    p95 = chins[min(len(chins) - 1, int(len(chins) * 0.95))]

    # El borde superior no lleva el ajuste de 1.05x de la barbilla: ese factor
    # cubre la mandíbula que el Haar deja fuera por abajo, y aquí se mide el
    # borde de la caja tal cual la devuelve el detector, sin estimar cuánto
    # pelo hay por encima (no hay forma de medir eso con Haar de cara).
    # `fy` sale de detectMultiScale como numpy.int32 y, a diferencia de la
    # barbilla (que suma `fh * 1.05` y con eso ya sube a float), aquí no hay
    # ninguna operación que lo convierta: sin el `float()`, `json.dumps` revienta
    # con «Object of type int32 is not JSON serializable».
    tops = sorted(float(fy) for _, fy, _, _ in boxes)
    p5 = tops[max(0, int(len(tops) * 0.05))]

    def median(vals):
        v = sorted(vals)
        n = len(v)
        return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2

    cx = median([fx + fw / 2 for fx, _, fw, _ in boxes])
    cy = median([fy + fh / 2 for _, fy, _, fh in boxes])

    out = dict(chin_px=round(p95, 1), chin_frac=round(p95 / h, 4),
               cx_frac=round(cx / w, 4), cy_frac=round(cy / h, 4),
               top_px=round(p5, 1), top_frac=round(p5 / h, 4),
               width=w, height=h, samples=a.samples, hits=len(boxes))

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"barbilla p95 = y{out['chin_px']:.0f} de {h}px  ({out['chin_frac']:.1%} del alto)")
    print(f"borde sup p5 = y{out['top_px']:.0f} de {h}px  ({out['top_frac']:.1%} del alto)")
    print(f"centroide    = ({out['cx_frac']:.1%}, {out['cy_frac']:.1%}) del fuente")
    print(f"{out['hits']} detecciones en {a.samples} muestras -> {a.out}")


if __name__ == "__main__":
    main()
