"""`logos.mark()` sabe consumir marcas de Simple Icons y marcas vendorizadas.

Fix round 1/5 de la Tarea 6: `mark()` solo sabía leer `meta[slug]["hex"]` y el
primer `<path>` de un SVG 24x24 — exactamente el contrato de Simple Icons. Las
cinco marcas vendorizadas (motion, manus, bklitui, kokonutui, animejs) no
tienen `hex` (no son monocromas), no todas caben en un viewBox 24x24 con un
solo path, y dos son PNG. `mark()` petaba con las cinco.

La retrocompatibilidad es innegociable: `mark("whatsapp", 110)` y
`mark("microsoftexcel", 110)` tienen que seguir devolviendo EXACTAMENTE el
mismo HTML y el mismo ratio que antes de este fix. Los dos primeros tests lo
congelan con el valor medido ANTES de tocar `logos.py`.
"""
import json
from pathlib import Path

import pytest

import logos
import tokens

ROOT = Path(__file__).resolve().parent.parent
LOGOS_DIR = ROOT / "assets" / "logos"


@pytest.fixture(scope="session")
def meta():
    return json.loads((LOGOS_DIR / "meta.json").read_text())


# ── retrocompatibilidad: Simple Icons, congelada ────────────────────────────

def test_whatsapp_congelado():
    """Valor medido ANTES del fix: ratio=8.938580282905505, len(html)=1248."""
    html, ratio = logos.mark("whatsapp", 110)
    assert ratio == pytest.approx(8.938580282905505)
    assert len(html) == 1248
    assert html == (
        '<span class="brandmark" style="width:110px;height:110px">'
        '<svg viewBox="0 0 24 24" aria-label="WhatsApp">'
        '<path fill="#25D366" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-'
        '.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-'
        '1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-'
        '.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-'
        '.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-'
        '.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 '
        '2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.'
        '227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-'
        '1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l'
        '-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436'
        '-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003'
        ' 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 '
        '5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 '
        '0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.'
        '413Z"/></svg></span>'
    )


def test_microsoftexcel_congelado():
    """Valor medido ANTES del fix: ratio=3.0436767002596676, len(html)=595."""
    html, ratio = logos.mark("microsoftexcel", 110)
    assert ratio == pytest.approx(3.0436767002596676)
    assert len(html) == 595
    assert html == (
        '<span class="brandmark" style="width:110px;height:110px">'
        '<svg viewBox="0 0 24 24" aria-label="Microsoft Excel">'
        '<path fill="#217346" d="M23 1.5q.41 0 .7.3.3.29.3.7v19q0 .41-.3.7-.29.3-.7.3H7q-'
        '.41 0-.7-.3-.3-.29-.3-.7V18H1q-.41 0-.7-.3-.3-.29-.3-.7V7q0-.41.3-.7Q.58 6 1 6h5V'
        '2.5q0-.41.3-.7.29-.3.7-.3zM6 13.28l1.42 2.66h2.14l-2.38-3.87 2.34-3.8H7.46l-1.3 '
        '2.4-.05.08-.04.09-.64-1.28-.66-1.29H2.59l2.27 3.82-2.48 3.85h2.16zM14.25 21v-3H7.'
        '5v3zm0-4.5v-3.75H12v3.75zm0-5.25V7.5H12v3.75zm0-5.25V3H7.5v3zm8.25 15v-3h-6.75v3z'
        'm0-4.5v-3.75h-6.75v3.75zm0-5.25V7.5h-6.75v3.75zm0-5.25V3h-6.75v3Z"/></svg></span>'
    )


# ── marcas vendorizadas ──────────────────────────────────────────────────────

def test_motion_svg_verbatim_y_tile_oscuro(meta):
    """Motion es SVG con su propio tile casi negro (#0B0B0C, contra la card
    #16181F). El SVG entra VERBATIM: ni un fill tocado."""
    raw = (LOGOS_DIR / "motion.svg").read_text()
    body = raw[raw.index(">", raw.index("<svg")) + 1:]
    html, ratio = logos.mark("motion", 110)
    assert html
    assert body in html, "el SVG de Motion no se conserva verbatim"
    assert meta["motion"]["tile"] == "#0B0B0C"
    assert ratio == pytest.approx(logos.contrast("#0B0B0C", logos.SURFACE))


def test_manus_svg_verbatim_y_tile_blanco(meta):
    """Manus trae un `<rect fill="white">` de fondo: tile blanco."""
    raw = (LOGOS_DIR / "manus.svg").read_text()
    body = raw[raw.index(">", raw.index("<svg")) + 1:]
    html, ratio = logos.mark("manus", 110)
    assert html
    assert body in html, "el SVG de Manus no se conserva verbatim"
    assert meta["manus"]["tile"] == "#FFFFFF"
    assert ratio == pytest.approx(logos.contrast("#FFFFFF", logos.SURFACE))


def test_animejs_svg_verbatim_sin_tile(meta):
    """El wordmark de Anime.js no tiene rect de fondo: es transparente, y
    `mark()` no puede calcular un contraste que no existe."""
    raw = (LOGOS_DIR / "animejs.svg").read_text()
    body = raw[raw.index(">", raw.index("<svg")) + 1:]
    html, ratio = logos.mark("animejs", 110)
    assert html
    assert body in html, "el SVG de Anime.js no se conserva verbatim"
    assert meta["animejs"]["tile"] is None
    assert ratio is None


def test_bklitui_png_referencia_el_asset_y_tile_negro(meta):
    """Bklit UI es PNG con tile negro opaco (las cuatro esquinas)."""
    html, ratio = logos.mark("bklitui", 110)
    assert html
    assert 'src="logos/bklitui.png"' in html
    assert (LOGOS_DIR / "bklitui.png").exists()
    assert meta["bklitui"]["tile"] == "#000000"
    assert ratio == pytest.approx(logos.contrast("#000000", logos.SURFACE))


def test_kokonutui_png_referencia_el_asset_sin_tile(meta):
    """Kokonut UI es PNG transparente (alpha 0 en las esquinas): sin tile."""
    html, ratio = logos.mark("kokonutui", 110)
    assert html
    assert 'src="logos/kokonutui.png"' in html
    assert (LOGOS_DIR / "kokonutui.png").exists()
    assert meta["kokonutui"]["tile"] is None
    assert ratio is None
