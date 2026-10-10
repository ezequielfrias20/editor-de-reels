#!/usr/bin/env python3
"""Vendoriza marcas monocromas desde Simple Icons v16, y marcas fuera de ese
catálogo directamente desde el sitio oficial de cada una (VENDOR)."""
import json
import re
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
    # Pieza 16. `claude` SÍ está en Simple Icons v16 — es el sol de Anthropic,
    # no el wordmark. Se prefiere a `anthropic` (también presente) porque lo
    # que el guion nombra es el producto, no la empresa.
    "claude": ("Claude", "D97757", "16"),
    # Pieza 3. Las cuatro marcas que nombra el guion y que SÍ están en el
    # catálogo. Los hex no se escribieron de memoria: salen de
    # `data/simple-icons.json` de la propia versión que se descarga, que es la
    # única fuente que no envejece con la siguiente marca nueva.
    #
    # Aquí la EMPRESA sí es lo que se nombra («lo anunció Anthropic»), al
    # contrario que en la pieza 16: `anthropic` entra ADEMÁS de `claude`, no en
    # su lugar.
    "anthropic": ("Anthropic", "191919", "16"),
    "claudecode": ("Claude Code", "D97757", "16"),
    # ⚠ `gemini` a secas en Simple Icons es la CASA DE CAMBIO, no el modelo de
    # Google: el slug del modelo es `googlegemini`. Es justo el caso que la
    # regla dura persigue — un slug que responde 200 y es otra marca.
    "googlegemini": ("Google Gemini", "8E75B2", "16"),
    # OpenAI pidió salir del catálogo y v16 ya no la trae (`openai` → 404; el
    # único resto es `openaigym`, el toolkit de RL, que es la marca
    # equivocada). Se pincha la última versión que la tiene verificada —el
    # mismo trato que `microsoftexcel` con 12.4.0— en vez de inventarle una.
    # El título queda «OpenAI» porque la marca ES la de OpenAI: ChatGPT no
    # tiene glifo propio, igual que Cowork. La PASTILLA del nombre, que la pone
    # quien pinta el mockup, es la que dice «ChatGPT».
    "openai": ("OpenAI", "412991", "15"),
    # Pieza 9 (DaVinci Resolve + MCP). Hex de `_data/simple-icons.json` de cada
    # versión. Adobe Premiere Pro salió del catálogo en v14 (404 en 14–16): se
    # pincha 13, la última que la tiene, como `openai` con 15.
    "davinciresolve": ("DaVinci Resolve", "233A51", "16"),
    "modelcontextprotocol": ("Model Context Protocol", "000000", "16"),
    "adobepremierepro": ("Adobe Premiere Pro", "9999FF", "13"),
}

# Marcas SIN logotipo propio, cuya marca honesta es la de otra. No se
# vendorizan: dibujarle una identidad a algo que no la tiene es lo mismo que
# inventarle un logotipo a un repositorio, cuya marca es la de GitHub.
#
# `cowork` → `claude`. Comprobado sobre claude.com/product/cowork: los únicos
# assets con «cowork» en el nombre son capturas de producto (.webp) y todos los
# <link rel="icon"> de la página son el favicon de Claude. Cowork es una
# superficie de Claude; lo que la distingue es la PASTILLA del nombre, no un
# logotipo que no existe.
SIN_MARCA_PROPIA = {"cowork": "claude"}

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
    # Las dos marcas de la pieza 16 que NO están en Simple Icons v16 (canva y
    # composio → 404; `canvas`, que sí existe, es el LMS: la marca equivocada).
    #
    # Canva sirve su wordmark oficial desde su CDN estático. NO hay icono
    # cuadrado vendorizable: `canva.com` responde 403 a todo (favicon, manifest
    # y apple-touch incluidos) y el favicon.ico que sí sale mide 32 px, muy por
    # debajo del gate de resolución. El wordmark es 80x30, así que entra
    # apaisado en un marco cuadrado — `_fit_svg` conserva el viewBox y lo
    # contiene sin deformarlo, el mismo caso que el wordmark 580x118 de
    # Anime.js. Quien lo pinte sube su `logo_px` para que llene el marco.
    "canva":    ("Canva", "https://static.canva.com/web/images/"
                          "8439b51bb7a19f6e65ce1064bc37c197.svg", "svg"),
    # Composio publica dos variantes; se vendoriza la BLANCA a propósito: la
    # negra (`composio-black.svg`) es tinta #000 sobre transparente y el marco
    # de logo de `tool_card` tiene el fondo `bg` de la paleta activa, donde desaparecería.
    "composio": ("Composio", "https://composio.dev/logos/composio-white.svg",
                 "svg"),
    # Pieza 18. HyperFrames no está en Simple Icons v16 (`hyperframes`,
    # `heygen` → 404). La marca buena la sirve el PROPIO subdominio del
    # producto, que es el que sale en la grabación de la pieza:
    # `hyperframes.heygen.com`, las dos alas verde/teal del encabezado. ⚠ NO
    # se vendoriza desde `hyperframes.dev`: ese dominio responde 200 a
    # /favicon.svg pero devuelve un icono titulado «EdgeNova App Icon», que no
    # es la marca — un 200 no es una verificación de que sea el logo correcto.
    # El SVG trae DOS gradientes con id propio (`paint0_linear_2204_3074`,
    # `paint1_...`), así que quien lo pinte tiene que pasar `uid=` a
    # `logos.mark()` o la segunda instancia sale vacía (regla dura de §14).
    "hyperframes": ("HyperFrames",
                    "https://hyperframes.heygen.com/favicon.svg", "svg"),
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


_NAMED_COLOR = {"white": "#FFFFFF", "black": "#000000", "none": None}


def _svg_tile(raw: bytes) -> str | None:
    """Color de fondo dominante de un SVG vendorizado.

    Busca un `<rect>` que cubra el lienzo entero (mismo ancho/alto que el
    `viewBox`) y devuelve su `fill`. Si no hay ninguno, la marca es
    transparente y no tiene tile que medir.
    """
    text = raw.decode("utf-8")
    vb = re.search(r'viewBox="[\d.\-]+\s+[\d.\-]+\s+([\d.]+)\s+([\d.]+)"', text)
    if not vb:
        return None
    view_w, view_h = float(vb.group(1)), float(vb.group(2))
    for m in re.finditer(r"<rect\b[^>]*/?>", text):
        tag = m.group(0)
        wm = re.search(r'width="([\d.]+)"', tag)
        hm = re.search(r'height="([\d.]+)"', tag)
        fm = re.search(r'fill="([^"]+)"', tag)
        if not (wm and hm and fm):
            continue
        w, h = float(wm.group(1)), float(hm.group(1))
        if abs(w - view_w) < 0.5 and abs(h - view_h) < 0.5:
            fill = fm.group(1).strip()
            low = fill.lower()
            if low in _NAMED_COLOR:
                return _NAMED_COLOR[low]
            return fill.upper() if fill.startswith("#") else fill
    return None


def _png_tile(path: Path) -> str | None:
    """Color de fondo dominante de un PNG vendorizado, muestreado en las
    cuatro esquinas. `None` si es transparente (alpha 0) — sin tile que medir.
    """
    from PIL import Image
    with Image.open(path) as im:
        im = im.convert("RGBA")
        w, h = im.size
        corners = [im.getpixel(p) for p in
                   ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
    r, g, b, a = corners[0]
    if a == 0:
        return None
    return "#" + "".join(f"{v:02X}" for v in (r, g, b))


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


_UNSAFE_SVG = (
    (re.compile(rb"<script\b", re.IGNORECASE), "un <script>"),
    (re.compile(rb"<foreignObject\b", re.IGNORECASE), "un <foreignObject>"),
    (re.compile(rb"\son\w+\s*=", re.IGNORECASE), "un manejador de evento on...="),
)


def _reject_unsafe_svg(raw: bytes, slug: str) -> None:
    """Un SVG vendorizado entra VERBATIM al HTML que Chrome renderiza —
    `_fit_svg()` en logos.py solo toca el `width`/`height` del `<svg>` raíz,
    nada de su contenido. Sin este gate, un `<script>`, un manejador
    `on...=` o un `foreignObject` entrarían enteros al render. Falla en la
    DESCARGA, no en el render: la misma disciplina que el gate de resolución
    de abajo, y que `screen-tour.py` fallando antes de renderizar ante barras
    negras."""
    for pattern, label in _UNSAFE_SVG:
        if pattern.search(raw):
            raise SystemExit(f"{slug}: SVG rechazado — contiene {label}")


def fetch_vendor(slug: str, meta: dict) -> None:
    """Descarga una marca fuera de Simple Icons desde su fuente oficial.

    Una marca raster que no pase el gate de resolución NO se vendoriza: el
    script se detiene en vez de guardar algo que entraría estirado en la
    card sin que nadie lo note. Un SVG que no pase el gate de seguridad
    tampoco: ver `_reject_unsafe_svg`.
    """
    if slug not in VENDOR:
        raise SystemExit(f"slug no declarado en VENDOR: {slug}")
    title, url, fmt = VENDOR[slug]
    req = urllib.request.Request(url, headers={"User-Agent": "editor-videos/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    if fmt == "svg":
        _reject_unsafe_svg(raw, slug)
    dest = OUT / f"{slug}.{fmt}"
    dest.write_bytes(raw)
    if fmt == "svg":
        tile = _svg_tile(raw)
    else:
        alto, pasa = check_raster(dest, CARD_RENDER_H)
        if not pasa:
            dest.unlink()
            raise SystemExit(
                f"{slug}: {alto}px no pasa el gate de resolución "
                f"(mínimo {CARD_RENDER_H * RASTER_MIN_SCALE}px) — no se vendoriza"
            )
        tile = _png_tile(dest)
    meta[slug] = {
        "title": title,
        "source": url,
        "downloaded": date.today().isoformat(),
        "format": fmt,
        # Fondo dominante que la marca trae consigo (para medir si se
        # distingue del `surface` de la card), o None si es transparente.
        "tile": tile,
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
