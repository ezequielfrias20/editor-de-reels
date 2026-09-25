"""Los logos vendorizados SIN fondo propio (`tile: null`) se leen en las dos paletas.

Composio es todo blanco y Anime.js y HyperFrames son blanco o cian claro: sobre
el suelo crema de `claro` desaparecen (≈1.2:1). `logos.mark()` les pone una
PLACA con la tinta de la paleta (`bg` o `text`) cuando el suelo no los sostiene,
elegida para que se lea la mayoría de los colores de la marca."""
import json
import re
from pathlib import Path

import pytest

import logos
import tokens as T

ROOT = Path(__file__).resolve().parent.parent
META = json.loads((ROOT / "assets" / "logos" / "meta.json").read_text())
SIN_TILE_SVG = sorted(s for s, m in META.items() if "hex" not in m and m.get("format") == "svg"
                      and not m.get("tile"))


@pytest.fixture(autouse=True)
def _restaurar():
    yield
    T.use("oscuro")


def test_hay_logos_sin_tile_que_probar():
    assert {"composio", "animejs", "hyperframes"} <= set(SIN_TILE_SVG)


@pytest.mark.parametrize("paleta", ["claro", "oscuro"])
@pytest.mark.parametrize("slug", SIN_TILE_SVG)
def test_la_mayoria_de_los_colores_de_la_marca_se_leen_sobre_su_placa(slug, paleta):
    T.use(paleta)
    placa, colores = logos.mark_plate(slug)
    assert placa in (T.C["bg"], T.C["text"])
    legibles = [c for c in colores if T.contrast(c, placa) >= 3.0]
    assert colores, f"{slug}: no se encontraron colores en el SVG"
    assert len(legibles) * 2 >= len(colores), (slug, paleta, placa, colores)


@pytest.mark.parametrize("slug", ["composio", "animejs", "hyperframes"])
def test_en_claro_los_logos_claros_llevan_placa_de_tinta(slug):
    T.use("claro")
    placa, _ = logos.mark_plate(slug)
    assert placa == T.C["text"]
    html, _ = logos.mark(slug, 110, uid="t")
    assert re.search(r'class="brandmark[^"]*"[^>]*background:' + re.escape(T.C["text"]), html), html[:200]


def test_en_oscuro_composio_va_sin_placa():
    T.use("oscuro")
    placa, _ = logos.mark_plate("composio")
    assert placa == T.C["bg"]
    html, _ = logos.mark("composio", 110, uid="t")
    assert "background:" not in html.split(">", 1)[0]
