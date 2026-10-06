#!/usr/bin/env python3
"""Pieza 5: las capturas reales de los plugins, como clips para `tool_recording`.

Cada captura es UN cuadro quieto de la grabación de pantalla (la página scrollea en la
grabación; el cuadro se eligió donde el texto que se dice está entero y quieto), recortado
sobre lo que se nombra y con un empuje de cámara lento (×1.00→×1.03). El clip lleva 84 px
de margen arriba porque la cabecera opaca de `tool_recording` tapa ese alto del rect.

    .venv/bin/python videos/5/capturas.py   → assets/capturas-5/<id>.mp4 + capturas.json
"""
import json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "capturas-5"
HEAD = 84
W = 1040
# id: (cuadro, [(crop x,y,w,h, dur), ...]) — varios tramos = corte duro entre recortes
CAPTURAS = {
    "omni-proveedores": ("omni-proveedores.png", [((270, 190, 540, 350), 2.2)]),
    "omni-tokens":      ("omni-tokens.png",      [((166, 297, 300, 98), 1.5)]),
    "mem-sesiones":     ("mem-sesiones.png",     [((285, 55, 450, 150), 0.9),
                                                  ((130, 443, 750, 250), 2.1)]),
    "head-tokens":      ("head-tokens.png",      [((190, 115, 640, 250), 1.6)]),
    "setup-lista":      ("setup-lista.png",      [((340, 280, 540, 230), 2.8)]),
    "task-titulo":      ("task-titulo.png",      [((332, 388, 754, 120), 2.0)]),
}
FPS = 30


def tramo(png, crop, dur, h, out):
    x, y, w, hh = crop
    n = round(dur * FPS)
    vf = (f"crop={w}:{hh}:{x}:{y},scale={W*2}:{h*2}:flags=lanczos,"
          f"zoompan=z='1+0.03*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{h}:fps={FPS},"
          f"pad={W}:{h+HEAD}:0:{HEAD}:color=0x201D1A,format=yuv420p")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-t", f"{dur}",
                    "-i", str(png), "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-crf", "16",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], check=True)


meta = {}
for cid, (png, tramos) in CAPTURAS.items():
    # todos los tramos de una captura comparten aspecto: el primero manda el alto
    x, y, w, hh = tramos[0][0]
    h = 2 * round(hh * W / w / 2)  # par: yuv420p
    partes = []
    for i, (crop, dur) in enumerate(tramos):
        assert abs(crop[3] / crop[2] - hh / w) < 1e-3, (cid, i, "aspecto distinto")
        out = SRC / f".{cid}-{i}.mp4"
        tramo(SRC / png, crop, dur, h, out)
        partes.append(out)
    final = SRC / f"{cid}.mp4"
    if len(partes) == 1:
        partes[0].replace(final)
    else:
        lista = SRC / f".{cid}.txt"
        lista.write_text("".join(f"file '{p.name}'\n" for p in partes))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
                        "-c", "copy", str(final)], check=True)
        for p in partes + [lista]:
            p.unlink()
    meta[cid] = {"w": W, "h": h + HEAD, "escala": round(W / w, 4), "tramos": tramos}
    print(f"✓ {final.relative_to(ROOT)}  {W}×{h + HEAD}  escala {W / w:.3f}")
(SRC / "capturas.json").write_text(json.dumps(meta, indent=1))
