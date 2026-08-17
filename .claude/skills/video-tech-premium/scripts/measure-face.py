#!/usr/bin/env python3
"""Mide dónde acaba la CARA en el metraje, para que el subtítulo nunca la pise.

    scripts/measure-face.py out/1-rough.mp4 assets/face.json [--samples 48]

Escribe `{chin_px, chin_frac, height, samples, hits}`. `chin_frac` es lo que usa
el generador: la barbilla como fracción de la altura del fuente, que es lo único
que sobrevive al reencuadre de cada modo.

Se usa el **percentil 95**, no el máximo: un solo falso positivo del detector
(un reflejo, una mano) arrastraría el subtítulo hasta el borde inferior y
arruinaría el encuadre de toda la pieza. El p95 absorbe esos atípicos y sigue
dejando el 95 % de los frames cubiertos.

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

    chins = []
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
            _, fy, _, fh = max(faces, key=lambda box: box[2] * box[3])
            # El Haar encuadra la cara sin mandíbula; el borde real cae algo más
            # abajo. Un 5 % del alto de la caja cubre esa diferencia sin
            # empujar el subtítulo más de lo necesario: pasarse de margen no
            # es gratis, en `split` deja el texto contra el borde inferior.
            chins.append(fy + fh * 1.05)
    cap.release()

    if not chins:
        sys.exit("no se detectó ninguna cara: revisa el metraje o pasa la medida a mano")

    chins.sort()
    p95 = chins[min(len(chins) - 1, int(len(chins) * 0.95))]
    out = dict(chin_px=round(p95, 1), chin_frac=round(p95 / h, 4),
               width=w, height=h, samples=a.samples, hits=len(chins))

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"barbilla p95 = y{out['chin_px']:.0f} de {h}px  ({out['chin_frac']:.1%} del alto)")
    print(f"{out['hits']} detecciones en {a.samples} muestras -> {a.out}")


if __name__ == "__main__":
    main()
