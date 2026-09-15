#!/usr/bin/env python3
"""Vendoriza marcas monocromas desde Simple Icons v16, y marcas fuera de ese
catálogo directamente desde el sitio oficial de cada una (VENDOR)."""
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path.cwd().resolve()
OUT = ROOT / "assets" / "logos"
KNOWN = {
    "whatsapp": ("WhatsApp", "25D366", "16"),
    # Microsoft retired this glyph from later Simple Icons catalogs. Pin the
    # last verified package family instead of substituting an invented mark.
    "microsoftexcel": ("Microsoft Excel", "217346", "12.4.0"),
}

# Las cinco marcas de la pieza 15. NINGUNA está en Simple Icons v16
# (animejs, anime, motion, manus, kokonut, bklit → 404), así que se vendorizan
# desde su sitio oficial. `framer` sí existe pero Motion ya no es Framer
# Motion: sería la marca equivocada.
VENDOR = {
    "motion":    ("Motion",     "https://motion.dev/favicon.svg",   "svg"),
    "manus":     ("Manus",      "https://manus.im/icon.svg",        "svg"),
    "bklitui":   ("Bklit UI",   "https://bklit.com/apple-icon.png", "png"),
    "kokonutui": ("Kokonut UI", "https://kokonutui.com/icon.png",   "png"),
    # El favicon de Anime.js (assets/images/favicon.png) es 64x64 y NO pasa
    # el gate. El og-image (1200x600) lleva el wordmark pero solo ocupa una
    # esquina diminuta: recortarlo tampoco pasaría el gate. La fuente buena es
    # el logo vectorial que el propio sitio sirve en su cabecera
    # (<img src="anime-js-logo-v4.svg"> en animejs.com) — SVG, así que no
    # tiene un "alto real" que estirar.
    "animejs":   ("Anime.js", "https://animejs.com/assets/images/"
                              "anime-js-logo-v4.svg", "svg"),
}

# La marca se pinta a ~110 px en la card. Por debajo de 2x se ve blanda.
RASTER_MIN_SCALE = 2
CARD_RENDER_H = 110


def check_raster(path, render_h: int) -> tuple[int, bool]:
    """(alto_real, pasa_el_gate). Una marca raster necesita 2x su tamaño de render."""
    from PIL import Image
    with Image.open(path) as im:
        alto = im.height
    return alto, alto >= render_h * RASTER_MIN_SCALE


def fetch_known(slug: str, meta: dict) -> None:
    """Descarga una marca del catálogo de Simple Icons."""
    if slug not in KNOWN:
        raise SystemExit(f"slug no verificado en Simple Icons v16: {slug}")
    title, hx, version = KNOWN[slug]
    url = f"https://cdn.jsdelivr.net/npm/simple-icons@{version}/icons/{slug}.svg"
    req = urllib.request.Request(url, headers={"User-Agent": "editor-videos/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    root = ET.fromstring(raw)
    paths = [n for n in root.iter() if n.tag.rsplit("}", 1)[-1] == "path"]
    if root.attrib.get("viewBox") != "0 0 24 24" or len(paths) != 1:
        raise SystemExit(f"{slug}: contrato SVG inesperado")
    (OUT / f"{slug}.svg").write_bytes(raw)
    meta[slug] = {"title": title, "hex": hx, "source": url,
                  "simple_icons_version": version}
    print(f"{slug} → assets/logos/{slug}.svg")


def fetch_vendor(slug: str, meta: dict) -> None:
    """Descarga una marca fuera de Simple Icons desde su fuente oficial.

    Una marca raster que no pase el gate de resolución NO se vendoriza: el
    script se detiene en vez de guardar algo que entraría estirado en la
    card sin que nadie lo note.
    """
    if slug not in VENDOR:
        raise SystemExit(f"slug no declarado en VENDOR: {slug}")
    title, url, fmt = VENDOR[slug]
    req = urllib.request.Request(url, headers={"User-Agent": "editor-videos/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    dest = OUT / f"{slug}.{fmt}"
    dest.write_bytes(raw)
    if fmt != "svg":
        alto, pasa = check_raster(dest, CARD_RENDER_H)
        if not pasa:
            dest.unlink()
            raise SystemExit(
                f"{slug}: {alto}px no pasa el gate de resolución "
                f"(mínimo {CARD_RENDER_H * RASTER_MIN_SCALE}px) — no se vendoriza"
            )
    meta[slug] = {
        "title": title,
        "source": url,
        "downloaded": date.today().isoformat(),
        "format": fmt,
    }
    print(f"{slug} → assets/logos/{slug}.{fmt}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta_path = OUT / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    args = sys.argv[1:]
    if args and args[0] == "--vendor":
        for slug in args[1:]:
            fetch_vendor(slug, meta)
    else:
        for slug in args:
            fetch_known(slug, meta)

    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
