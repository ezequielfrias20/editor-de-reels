#!/usr/bin/env python3
"""Logos oficiales de Simple Icons, entintados para la superficie de la paleta activa.

El logo se dibuja sobre `surface`, así que el color de marca se mueve hacia el
TEXTO de la paleta hasta pasar 3:1: en la oscura se aclara (el verde de WhatsApp
o el de Excel a su valor nominal se hunden en el fondo) y en la clara se
oscurece, con la misma regla. Se devuelve el ratio medido para que el mockup
pueda fallar en vez de renderizar un logo ilegible.
"""
import hashlib
import json
import re
from pathlib import Path

from tokens import C



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


def brand_tone(hex_brand, bg=None, ratio_min=3.0):
    """El color de marca, movido hacia el TEXTO de la paleta activa lo justo
    para leerse sobre `surface`: se aclara en la oscura y se oscurece en la
    clara, con la misma regla."""
    bg = bg or C["surface"]
    toward = C["text"]
    a, b = _rgb("#" + hex_brand.lstrip("#")), _rgb(toward)
    if contrast(_hex(a), bg) >= ratio_min:
        return _hex(a)
    for mix in (.15, .25, .35, .45, .55, .70):
        c = _hex(tuple(x + (y - x) * mix for x, y in zip(a, b)))
        if contrast(c, bg) >= ratio_min:
            return c
    return toward


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


_ID_ATTR = re.compile(r'\bid="([^"]+)"')
_ID_REF = re.compile(r'url\(#([^)]+)\)|(?:xlink:)?href="#([^"]+)"')


def svg_has_internal_refs(raw: str) -> bool:
    """¿Este SVG apunta a sus propios ids? (gradientes, clip-paths, máscaras)"""
    return _ID_REF.search(raw) is not None


def namespace_svg_ids(raw: str, uid: str) -> str:
    """Los ids internos del SVG, renombrados para ESTA instancia.

    ⚠ **Un SVG vendorizado inlineado dos veces rompe el documento, y no se ve
    venir.** La marca de Canva trae seis `<radialGradient>` con ids fijos que
    exporta su herramienta (`_2002046508__a`…) y seis `fill="url(#…)"` que los
    apuntan. La pieza 16 la pinta CINCO veces —la card de la pareja, su
    reaparición, la pastilla del conector, la fila de teselas y el lineup— y el
    navegador resuelve cada `url(#id)` al PRIMER elemento con ese id del
    documento, que vive dentro del host de la primera card. En cuanto el
    renderer oculta ese host, las otras cuatro se quedan sin relleno: **el
    marco se sigue viendo y la marca desaparece**. Medido sobre snapshots en
    t=15.5 y t=17.5 — el hueco del logo estaba a fondo `bg` liso.

    El sufijo sale de un sha1 del `uid`, no de un contador: un contador
    dependería del ORDEN de las llamadas y el mismo plan compilado dos veces
    daría HTML distinto — los golden files no lo perdonarían. Con el hash, el
    id de un visual depende solo de qué visual es.

    Se renombran TODOS los ids, no solo los referenciados: dos ids iguales en
    un documento son HTML inválido aunque nadie los apunte (el wordmark de
    Anime.js trae nueve sin una sola referencia), y dejar la mitad limpia es
    dejar el gate a medias.
    """
    token = hashlib.sha1(uid.encode()).hexdigest()[:8]
    ids = set(_ID_ATTR.findall(raw))
    if not ids:
        return raw
    out = _ID_ATTR.sub(lambda m: f'id="{m.group(1)}__{token}"', raw)

    def ref(m):
        old = m.group(1) or m.group(2)
        if old not in ids:
            # Una referencia a algo que este SVG no define se deja intacta:
            # renombrarla la rompería en vez de arreglarla.
            return m.group(0)
        return (f'url(#{old}__{token})' if m.group(1)
                else m.group(0).replace(f'#{old}', f'#{old}__{token}'))
    return _ID_REF.sub(ref, out)


def mark(slug: str, size: int, tone: str = "brand", bg: str | None = None,
         uid: str = "") -> tuple[str, float | None]:
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
    bg = bg or C["surface"]
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
        if uid:
            raw = namespace_svg_ids(raw, uid)
        elif svg_has_internal_refs(raw):
            raise ValueError(
                f"{slug}: este SVG apunta a sus propios ids (gradiente, "
                f"clip-path o máscara) y `mark()` se ha llamado sin `uid`. "
                f"Inlineado dos veces en la misma composición, el navegador "
                f"resuelve las dos referencias al PRIMER id del documento y "
                f"la segunda marca se renderiza vacía. Pasa `uid=` con algo "
                f"único por instancia — los mockups pasan su `cid`.")
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
