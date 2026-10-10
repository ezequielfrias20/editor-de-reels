#!/usr/bin/env python3
"""Hoja estática de las dos paletas: los mockups más usados en su estado final.

No es un render ni una pieza: sirve para MIRAR la paleta antes de editar nada.
Fuerza el estado final (opacidad 1, sin transform) porque aquí no corre GSAP.

    scripts/palette-sheet.py [--out out/palette-sheet]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mockups  # noqa: E402
import tokens as TK  # noqa: E402

MUESTRAS = {
    "tool_card": lambda cid: mockups.tool_card(cid, "claude", "Claude Code", kicker="LA HERRAMIENTA"),
    "keyword_hero": lambda cid: mockups.keyword_hero(cid, "AGENTES", kicker="LA IDEA"),
    "chip_grid": lambda cid: mockups.chip_grid(cid, ["TERMINAL", "AGENTES", "CÓDIGO"], [0.2, 0.4, 0.6]),
    "flow_steps": lambda cid: mockups.flow_steps(cid, ["PIDES", "PLANIFICA", "ENTREGA"], [0.2, 0.5, 0.8]),
    "stat_grid": lambda cid: mockups.stat_grid(cid, [("3", "AGENTES"), ("2 h", "AHORRO"), ("0", "CÓDIGO")],
                                               [0.2, 0.4, 0.6]),
    "comment_ui": lambda cid: mockups.comment_ui(cid, "CLAUDE"),
}


def _frame(palette: str) -> str:
    TK.use(palette)
    c = TK.C
    cells = []
    for i, (nombre, fn) in enumerate(MUESTRAS.items(), 1):
        # Los selectores del mockup cuelgan de `.viz[data-viz-id="<cid>"]`
        # (el host que pone build-composition), y cada paleta lleva sus ids.
        cid = f"{palette}-m{i}"
        css, html, _ = fn(cid)
        cells.append(
            f'<section class="cell" data-muestra="{nombre}" style="background:{c["bg"]};'
            f'background-image:{TK.grid()}"><style>{css}</style>'
            f'<div class="viz" data-viz-id="{cid}">{html}</div>'
            f'<b class="tag" style="color:{c["text2"]}">{nombre}</b></section>')
    cap = (f'<section class="cell cap" style="background:{c["bg"]}">'
           f'<span style="color:{c["text"]}">LE DI UNA TAREA </span>'
           f'<span class="pill" style="background:{c["accent_pill"]};color:{c["text"]}">DE FIN DE SEMANA</span>'
           f'<b class="tag" style="color:{c["text2"]}">subtítulo + karaoke</b></section>')
    return (f'<div class="frame"><h2 style="color:#fff">{palette}</h2>'
            f'{"".join(cells)}{cap}</div>')


def build(out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    body = "".join(_frame(p) for p in TK.PALETTES)
    TK.use("oscuro")
    doc = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
body{{margin:0;background:#777;display:flex;gap:48px;padding:32px;font-family:{TK.FONT}}}
.frame{{display:flex;flex-direction:column;gap:24px;width:1080px}}
.frame h2{{margin:0;font:700 34px {TK.MONO}}}
.cell{{position:relative;width:1080px;height:660px;overflow:hidden;display:flex;
  align-items:center;justify-content:center}}
.viz{{width:100%;height:100%;display:flex;align-items:center;justify-content:center}}
.cell *{{opacity:1!important;transform:none!important}}
.cap{{height:300px;gap:18px;font:900 66px/1 {TK.FONT};text-transform:uppercase;letter-spacing:-.02em}}
.pill{{padding:4px 8px;border-radius:{TK.RADIUS['sm']}px}}
.tag{{position:absolute;left:16px;bottom:10px;font:700 20px {TK.MONO}}}
</style></head><body>{body}</body></html>"""
    out = out_dir / "palette-sheet.html"
    out.write_text(doc, encoding="utf-8")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="out/palette-sheet")
    print(build(Path(ap.parse_args().out)))
