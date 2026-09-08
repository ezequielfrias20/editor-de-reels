#!/usr/bin/env python3
"""Métricas de un bloque de subtítulo. Extraídas de build-composition.py.

POR QUÉ EXISTE ESTE MÓDULO. La keyword pasa a ser 1.22x más grande que el
resto del bloque, y eso cambia dos cuentas que antes eran triviales:

  1. `floor_top` usaba `CAPTION_SIZE` para TODAS las líneas. Con una keyword
     grande la caja de línea crece y un bloque de dos líneas se mete en el 20%
     inferior que pinta la plataforma. Ese bug ya ocurrió una vez: 46 px
     dentro de la interfaz.
  2. El ancho que decide si el bloque es de una o dos líneas tiene que pesar
     los caracteres de la keyword a SU tamaño, o un bloque medido como una
     línea se renderiza como dos y la cuenta de arriba falla igual.

Encapsularlo aquí lo hace testeable SIN renderizar, que es el ciclo caro: la
zona segura solo se verificaba extrayendo frames del MP4.
"""
from __future__ import annotations

from caption_fonts import words_width

# Tope MEDIDO: a 66 px de base, 1.30 son 86 px y un bloque de dos líneas se
# queda sin presupuesto de zona segura. El brief pedía hasta 1.30.
KEYWORD_SCALE_MAX = 1.22

LINE_RATIO = 1.14          # el line-height del `.cap` actual
SAFE_BOTTOM = 0.80         # el 20% inferior lo pinta la plataforma
MAXW_RATIO = 0.84          # el ancho útil, igual que CAPTION_MAXW

FORMATS = ("REEL", "YOUTUBE")


def measure_block(words, base_size: int, keyword_range, fmt: str, canvas_h: int,
                  canvas_w: int = 1080, keyword_scale: float = KEYWORD_SCALE_MAX,
                  cache_dir=None) -> dict:
    """→ {n_lines, max_size, line_h, floor_top, width}

    `keyword_range` es `(lo, hi)` inclusive sobre los índices de `words`, o
    `None` si el bloque no resalta nada.
    """
    if fmt not in FORMATS:
        raise ValueError(f"formato '{fmt}' desconocido; hay {FORMATS}")
    if keyword_scale > KEYWORD_SCALE_MAX:
        raise ValueError(
            f"keyword_scale {keyword_scale} pasa del tope {KEYWORD_SCALE_MAX}: por "
            f"encima, un bloque de dos líneas se queda sin zona segura")

    kw_size = round(base_size * keyword_scale)
    lo, hi = keyword_range if keyword_range else (-1, -2)
    sizes = [kw_size if lo <= i <= hi else base_size for i in range(len(words))]

    max_size = max(sizes) if sizes else base_size
    line_h = round(max_size * LINE_RATIO)
    width = words_width(words, sizes, cache_dir)
    n_lines = 1 if width <= round(canvas_w * MAXW_RATIO) else 2

    # LA CUENTA QUE IMPORTA: con `max_size`, no con `base_size`.
    floor_top = round(canvas_h * SAFE_BOTTOM) - n_lines * line_h

    return {"n_lines": n_lines, "max_size": max_size, "line_h": line_h,
            "floor_top": floor_top, "width": round(width, 2)}
