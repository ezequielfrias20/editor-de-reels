#!/usr/bin/env python3
"""Descarga los woff2 del subset LATINO desde Google Fonts y verifica los glifos.

    scripts/fetch-fonts.py

Google devuelve varios @font-face por familia (cirílico, vietnamita, latin-ext,
latino) y el latino NO es el primero — quedarse con el primer src baja el subset
cirílico, que no tiene ni una tilde. Aquí se elige por unicode-range y luego se
verifica con fontTools que los caracteres del español existan de verdad.

La familia del sistema es **Inter** (400→900) para todo el texto y **JetBrains
Mono** para etiquetas de UI. Dos familias, no tres: es lo que hace que una pieza
se lea como un producto y no como una plantilla.
"""
import re
import sys
import urllib.request
from pathlib import Path

from fontTools.ttLib import TTFont

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

DEST = Path(__file__).resolve().parent.parent / "assets" / "fonts"

FAMILIES = {
    "Inter-400":          "family=Inter:wght@400",
    "Inter-500":          "family=Inter:wght@500",
    "Inter-600":          "family=Inter:wght@600",
    "Inter-700":          "family=Inter:wght@700",
    "Inter-800":          "family=Inter:wght@800",
    "Inter-900":          "family=Inter:wght@900",
    "JetBrainsMono-400":  "family=JetBrains+Mono:wght@400",
    "JetBrainsMono-700":  "family=JetBrains+Mono:wght@700",
    "Fraunces-Italic800": "family=Fraunces:ital,wght@1,800",
}

# lo que el guion necesita de verdad, en minúscula y mayúscula
NEEDED = "áéíóúüñÁÉÍÓÚÜÑ¿¡%3408—·“”"


def get(url: str) -> bytes:
    r = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(r, timeout=60) as resp:
        return resp.read()


def latin_url(css: str) -> str | None:
    """El bloque cuyo unicode-range cubre U+0000-00FF (Latin-1 = tildes y ñ)."""
    blocks = re.findall(r"src:\s*url\((https://[^)]+\.woff2)\)[^}]*?"
                        r"unicode-range:\s*([^;]+);", css, re.S)
    for url, rng in blocks:
        if "U+0000-00FF" in rng.replace(" ", ""):
            return url
    return None


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    failures = []

    for name, query in FAMILIES.items():
        css = get(f"https://fonts.googleapis.com/css2?{query}&display=swap").decode()
        url = latin_url(css)
        if not url:
            print(f"  FALLO  {name}: no hay subset latino")
            failures.append(name)
            continue

        path = DEST / f"{name}.woff2"
        path.write_bytes(get(url))

        # verificación real: ¿están los glifos en el cmap?
        cmap = TTFont(path).getBestCmap()
        missing = [c for c in NEEDED if ord(c) not in cmap]
        if missing:
            print(f"  FALLO  {name}: faltan {''.join(missing)}")
            failures.append(name)
        else:
            print(f"  ok     {name}.woff2  {path.stat().st_size/1024:.0f} KB  "
                  f"· {len(cmap)} glifos · español completo")

    if failures:
        print(f"\n{len(failures)} fuente(s) con problemas: {', '.join(failures)}")
        return 1
    print("\ntodas las fuentes verificadas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
