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


def _fit_svg(raw: str, size: int) -> str:
    """Fuerza el `<svg>` raíz a `size`x`size` sin tocar nada más — ni un
    `fill`, ni un `path`. El `viewBox` se deja intacto: el
    `preserveAspectRatio` por defecto (`xMidYMid meet`) contiene la marca sin
    deformarla aunque no sea cuadrada (el wordmark de Anime.js es 580x118).

    El `<?xml ...?>` de cabecera (animejs.svg lo trae) se descarta: no es
    parte de la marca, es ruido de exportador que no pinta nada — un parser
    HTML lo trata como un comentario bogus, pero mejor no dejarlo."""
    raw = re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", raw)

    def repl(m):
        tag = re.sub(r'\swidth="[^"]*"', "", m.group(0))
        tag = re.sub(r'\sheight="[^"]*"', "", tag)
        return tag[:-1] + f' width="{size}" height="{size}">'
    return re.sub(r"<svg\b[^>]*>", repl, raw, count=1)


def mark(slug: str, size: int, tone: str = "brand", bg: str = SURFACE) -> tuple[str, float | None]:
    """(html, ratio).

    Dos familias de marca, con contratos distintos:

    - **Simple Icons** (`meta[slug]` trae `hex`): monocroma, un solo `path` en
      un viewBox 24x24. `tone="mono"` la pinta en texto claro; `"brand"`
      conserva el color de marca ya aclarado contra `bg` (comportamiento sin
      cambios — retrocompatibilidad congelada en `test_logos_mark.py`).
    - **Vendorizada** (`meta[slug]` trae `format`): motion, manus, bklitui,
      kokonutui, animejs. Ninguna es monocroma — llevan su propio color de
      marca — así que NO se re-entintan, y `tone` no aplica. Un SVG se emite
      VERBATIM (todos sus paths y fills); un PNG se referencia con `<img>`.
      El ratio deja de medir un `fill` contra `bg` (no hay uno solo) y pasa a
      medir el `tile` — el fondo dominante que la marca trae consigo — contra
      `bg`. Si la marca es transparente (`tile` es `None`), no hay nada que
      medir y el ratio devuelto es `None`: el llamador tiene que tratar ese
      caso aparte, no asumir que siempre hay un número.
    """
    root = Path.cwd() / "assets" / "logos"
    meta = json.loads((root / "meta.json").read_text())
    info = meta[slug]

    if "hex" in info:
        raw = (root / f"{slug}.svg").read_text()
        path = re.search(r"<path[^>]*d=\"([^\"]+)\"", raw)
        if not path:
            raise ValueError(f"{slug}: SVG sin path")
        fill = C["text2"] if tone == "mono" else brand_tone(info["hex"], bg)
        ratio = contrast(fill, bg)
        html = (f'<span class="brandmark" style="width:{size}px;height:{size}px">'
                f'<svg viewBox="0 0 24 24" aria-label="{info["title"]}">'
                f'<path fill="{fill}" d="{path.group(1)}"/></svg></span>')
        return html, ratio

    fmt = info["format"]
    if fmt == "svg":
        raw = (root / f"{slug}.svg").read_text()
        inner = _fit_svg(raw, size)
    elif fmt == "png":
        inner = (f'<img src="logos/{slug}.png" alt="{info["title"]}" '
                  f'width="{size}" height="{size}" '
                  f'style="width:100%;height:100%;object-fit:contain;display:block" />')
    else:
        raise ValueError(f"{slug}: formato de marca desconocido {fmt!r}")

    tile = info.get("tile")
    ratio = contrast(tile, bg) if tile else None
    html = f'<span class="brandmark" style="width:{size}px;height:{size}px">{inner}</span>'
    return html, ratio
