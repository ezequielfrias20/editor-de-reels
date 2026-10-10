#!/usr/bin/env python3
"""Respiraciones que sobreviven al corte. Falla si queda alguna.

    scripts/audit-breaths.py --project . --piece 14
    scripts/audit-breaths.py --cut out/14-rough.mp4 --source assets/audio/14.flac \
                             --transcript transcripts/14.json --cuts cuts/14.json

Es un PASO DEL FLUJO (§2, paso 4b), no una utilidad suelta: `plan-cuts --audio`
quita las respiraciones y esto comprueba que de verdad no quedó ninguna. Sale
con código 1 si sobrevive alguna, así que un video con una inspiración dentro
no llega a renderizarse por descuido.

Nació de una entrega real: la pieza 14 salió con 900 ms de inspiración a
−10.4 dB dentro del hook y la cazó el usuario, no el flujo. La causa raíz y las
trampas están en §2 («Voz no es sonido»); esto es la red que faltaba.

⚠ TRES COSAS QUE PARECEN DETALLES Y NO LO SON

1. Se audita el CORTE (`out/<n>-rough.mp4`), que es voz sola. Sobre el MP4 ya
   mezclado la cama musical da falsos positivos: no tiene tono y el detector
   la marcaría como aire.
2. El umbral viene de la FUENTE sin cortar. El corte ya no contiene los
   silencios de los que se estima el suelo — medido, «sube» de −52.0 a
   −41.9 dB — y con el umbral equivocado una ráfaga de −11.7 dB se escondía.
3. Solo cuentan las islas FUERA de todo span de palabra. Dentro de una
   palabra, un frame sin tono es una plosiva o una nasal apagándose, y tratarla
   como respiración estropearía el habla.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from edl_words import load_words          # noqa: E402
from voicing import breath_islands, load_mono, source_threshold  # noqa: E402

MARGEN = 0.060      # aire alrededor de cada palabra: su ataque y su cola


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--piece", help="número de pieza o id de versión (7, 7-instagram)")
    ap.add_argument("--cut", type=Path)
    ap.add_argument("--source", type=Path)
    ap.add_argument("--transcript", type=Path)
    ap.add_argument("--cuts", type=Path)
    ap.add_argument("--margin", type=float, default=MARGEN)
    a = ap.parse_args(argv)

    root = a.project.resolve()
    if a.piece is not None:
        n = a.piece
        cut = a.cut or root / "out" / f"{n}-rough.mp4"
        src = a.source or root / "assets" / "audio" / f"{n}.flac"
        tr = a.transcript or root / "transcripts" / f"{n}.json"
        cu = a.cuts or root / "cuts" / f"{n}.json"
    else:
        if not all((a.cut, a.source, a.transcript, a.cuts)):
            ap.error("pasa --piece, o los cuatro caminos a mano")
        cut, src, tr, cu = a.cut, a.source, a.transcript, a.cuts

    faltan = [p for p in (cut, src, tr, cu) if not Path(p).exists()]
    if faltan:
        print("no existe: " + ", ".join(str(p) for p in faltan), file=sys.stderr)
        return 2

    thr = source_threshold(src)
    audio, sr = load_mono(cut)
    wt = load_words(Path(tr), Path(cu))
    spans = [(w.start, w.end, w.text) for w in wt.words]

    islas = breath_islands(audio, sr, thr=thr)
    fuera = [x for x in islas
             if not any(x[1] > s0 - a.margin and x[0] < s1 + a.margin
                        for s0, s1, _ in spans)]

    print(f"{cut}  ·  {len(audio) / sr:.2f} s  ·  {len(wt.words)} palabras")
    print(f"umbral de la fuente {thr:.1f} dB  ·  {len(islas)} islas sin voz  ·  "
          f"{len(fuera)} fuera de toda palabra\n")

    if not fuera:
        print("✓ ninguna respiración audible sobrevive al corte")
        return 0

    for t0, t1, pico in fuera:
        prev = max((w for w in spans if w[1] <= t0 + 0.01),
                   key=lambda w: w[1], default=None)
        nxt = min((w for w in spans if w[0] >= t1 - 0.01),
                  key=lambda w: w[0], default=None)
        print(f"  ⚠ {t0:7.3f}-{t1:7.3f}  {t1 - t0:5.3f} s  pico {pico:6.1f} dB   "
              f"…{prev[2] if prev else '—'} ⟨aquí⟩ {nxt[2] if nxt else '—'}…")
    print(f"\n{len(fuera)} respiración(es) en el corte. Vuelve a correr el paso 3 con "
          f"`--audio {src}`;\nsi el hueco es demasiado corto para cortarlo, decide a "
          f"mano — pero no se entrega así.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
