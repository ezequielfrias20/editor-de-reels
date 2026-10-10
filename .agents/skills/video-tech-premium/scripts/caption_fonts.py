#!/usr/bin/env python3
"""Carga de la fuente real para medir texto. Extraído de build-composition.py.

Existe para que `caption_metrics.py` pueda medir un bloque de subtítulo SIN
importar `build-composition.py` (que no es importable: lleva un guion en el
nombre) y sin duplicar la conversión woff2 -> ttf.

Es un movimiento SIN cambio de comportamiento: `build-composition.py` sigue
cacheando el .ttf en el directorio de la pieza (`cache_dir=WORK`), igual que
antes; `caption_metrics` usa por defecto el de la skill, compartido.
"""
from __future__ import annotations

from pathlib import Path

from PIL import ImageFont

SKILL = Path(__file__).resolve().parent.parent
FONT_WOFF2 = SKILL / "assets" / "fonts" / "Inter-900.woff2"

# El ancho que cada palabra ocupa DE MÁS por su margen CSS. En el DOM cada
# palabra es un `.cap .w{display:inline-block;margin:0 9px}`, así que no hay
# glifo de espacio entre ellas: el hueco lo pone el margen.
WORD_MARGIN = 22

_cache: dict[tuple[int, str], ImageFont.FreeTypeFont] = {}


def measure_font(size: int, cache_dir: Path | None = None):
    """Inter 900 real, para cortar los bloques con métricas y no contando letras."""
    base = Path(cache_dir) if cache_dir else (SKILL / "assets")
    key = (size, str(base))
    if key in _cache:
        return _cache[key]

    ttf = base / ".inter900.ttf"
    if not ttf.exists():
        from fontTools.ttLib import TTFont
        ttf.parent.mkdir(parents=True, exist_ok=True)
        f = TTFont(FONT_WOFF2)
        f.flavor = None
        f.save(str(ttf))
    fnt = ImageFont.truetype(str(ttf), size)
    _cache[key] = fnt
    return fnt


def word_widths(words, sizes, cache_dir: Path | None = None) -> list[float]:
    """El ancho de CADA palabra, con su margen incluido.

    Lo necesita el reparto en líneas: el total no dice cuántas líneas salen
    —una sola palabra muy larga rompe la línea antes de agotar el ancho— así
    que hay que repartir palabra a palabra.
    """
    return [measure_font(int(s), cache_dir).getlength(w) + WORD_MARGIN
            for w, s in zip(words, sizes)]


def words_width(words, sizes, cache_dir: Path | None = None) -> float:
    """Ancho de una lista de palabras, cada una a SU tamaño.

    Medir palabra a palabra (en vez de unir con espacios y medir de una) es lo
    que permite que la keyword pese lo que de verdad ocupa a 1.22x. Y modela
    mejor el render real: en el DOM no hay glifos de espacio, hay márgenes.
    """
    total = 0.0
    for w, s in zip(words, sizes):
        total += measure_font(int(s), cache_dir).getlength(w) + WORD_MARGIN
    return total
