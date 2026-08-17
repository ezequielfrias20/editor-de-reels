#!/usr/bin/env python3
"""Logos oficiales de Simple Icons, entintados para superficie OSCURA.

El logo se dibuja sobre `surface` (#16181F), así que el color de marca hay que
ACLARARLO, no oscurecerlo: el verde de WhatsApp o el de Excel a su valor
nominal se hunden en el fondo. Se mezcla hacia blanco hasta pasar 3:1 y se
devuelve el ratio medido para que el mockup pueda fallar en vez de renderizar
un logo ilegible.
"""
import json
import re
from pathlib import Path

from tokens import C

SURFACE = C["surface"]
WHITE = "#FFFFFF"


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#" + "".join(f"{round(v):02X}" for v in rgb)


def _lum(h):
    def f(v):
        v /= 255
        return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    r, g, b = _rgb(h)
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def contrast(a, b):
    x, y = sorted((_lum(a), _lum(b)), reverse=True)
    return (x + .05) / (y + .05)


def brand_tone(hex_brand, bg=SURFACE, ratio_min=3.0):
    """El color de marca, aclarado lo justo para sobrevivir al fondo oscuro."""
    a, b = _rgb("#" + hex_brand.lstrip("#")), _rgb(WHITE)
    if contrast(_hex(a), bg) >= ratio_min:
        return _hex(a)
    for mix in (.15, .25, .35, .45, .55, .70):
        c = _hex(tuple(x + (y - x) * mix for x, y in zip(a, b)))
        if contrast(c, bg) >= ratio_min:
            return c
    return WHITE


def mark(slug: str, size: int, tone: str = "brand", bg: str = SURFACE) -> tuple[str, float]:
    """(html, ratio). `tone="mono"` lo pinta en texto claro; `"brand"` conserva
    el color de la marca ya aclarado."""
    root = Path.cwd() / "assets" / "logos"
    meta = json.loads((root / "meta.json").read_text())
    raw = (root / f"{slug}.svg").read_text()
    path = re.search(r"<path[^>]*d=\"([^\"]+)\"", raw)
    if not path:
        raise ValueError(f"{slug}: SVG sin path")
    fill = C["text2"] if tone == "mono" else brand_tone(meta[slug]["hex"], bg)
    ratio = contrast(fill, bg)
    html = (f'<span class="brandmark" style="width:{size}px;height:{size}px">'
            f'<svg viewBox="0 0 24 24" aria-label="{meta[slug]["title"]}">'
            f'<path fill="{fill}" d="{path.group(1)}"/></svg></span>')
    return html, ratio
