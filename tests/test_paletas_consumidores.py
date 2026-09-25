"""Que la paleta de la pieza llegue a TODO lo que se dibuja, y que nada quede
congelado en el violeta o el grafito de antes."""
import ast
import json
import re
from pathlib import Path

import pytest

import tokens as T

SCRIPTS = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "video-tech-premium" / "scripts"

# Colores del sistema viejo (grafito + violeta) y de su suelo, escritos a mano.
VIEJOS = re.compile(
    r"rgba\((124, ?92, ?255|155, ?133, ?255|91, ?63, ?214|184, ?170, ?255|43, ?29, ?122|11, ?12, ?16|22, ?24, ?31"
    r"|52, ?227, ?155|255, ?90, ?90|255, ?184, ?77|167, ?173, ?187)"
    r"|#7C5CFF|#9B85FF|#5B3FD6|#B8AAFF|#2B1D7A|#0B0C10|#07080B|#16181F|#1D2029|#252935|#A7ADBB|#8C93A3"
    r"|#34E39B|#FF5A5A|#FFB84D",
    re.I)
CLAVES_VIEJAS = re.compile(r"""C\[['"]violet|FILL\[['"](violet|white)['"]\]""")
ESCALARES = {"LINE", "LINE_HI", "SHADOW", "SHADOW_LIFT", "GLOW"}


def _escalares_importados(src: str) -> set:
    """Nombres de color escalar traídos con `from tokens import …` (también
    en imports entre paréntesis de varias líneas): quedarían congelados."""
    out = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom) and node.module == "tokens":
            out |= {a.name for a in node.names} & ESCALARES
    return out


@pytest.fixture(autouse=True)
def _restaurar():
    yield
    T.use("oscuro")


@pytest.mark.parametrize("f", sorted(p.name for p in SCRIPTS.glob("*.py") if p.name != "tokens.py"))
def test_ningun_script_escribe_colores_del_sistema_viejo(f):
    src = (SCRIPTS / f).read_text()
    assert not VIEJOS.findall(src), f"{f}: {sorted(set(VIEJOS.findall(src)))}"
    assert not CLAVES_VIEJAS.findall(src), f"{f} usa claves violeta/white"
    assert not _escalares_importados(src), f"{f} importa por nombre {_escalares_importados(src)}"


def test_todos_los_logos_se_leen_en_las_dos_paletas(project_root):
    """Construir `tool_card` con cada logo vendorizado en cada paleta no
    revienta. (Que el logo SE LEA lo fija `tests/test_logos_paletas.py`:
    `tool_card` no mira el ratio que devuelve `logos.mark()`.)"""
    import mockups
    meta = json.loads((project_root / "assets" / "logos" / "meta.json").read_text())
    for nombre in T.PALETTES:
        T.use(nombre)
        for slug, m in meta.items():
            mockups.tool_card("tl", slug, m.get("title", slug))


def _render(fn, *a, **kw):
    css, html, _ = fn(*a, **kw)
    return css + html


MUESTRAS = [
    ("tool_card", ("t1", "claude", "Claude Code"), {}),
    ("keyword_hero", ("t2", "AGENTES"), {"kicker": "LA IDEA"}),
    ("chip_grid", ("t3", ["TERMINAL", "AGENTES", "CÓDIGO"], [0.2, 0.4, 0.6]), {}),
    ("flow_steps", ("t4", ["PIDES", "PLANIFICA", "ENTREGA"], [0.2, 0.5, 0.8]), {}),
    ("stat_grid", ("t5", [("3", "AGENTES"), ("2 h", "AHORRO"), ("0", "CÓDIGO")], [0.2, 0.4, 0.6]), {}),
    ("comment_ui", ("t6", "CLAUDE"), {}),
]


@pytest.mark.parametrize("nombre,args,kw", MUESTRAS, ids=[m[0] for m in MUESTRAS])
def test_mockups_pintan_con_la_paleta_activa(nombre, args, kw):
    import mockups
    fn = getattr(mockups, nombre)
    T.use("claro")
    claro = _render(fn, *args, **kw)
    T.use("oscuro")
    oscuro = _render(fn, *args, **kw)
    assert claro != oscuro
    assert "#E27B52" not in claro.upper() and "226,123,82" not in claro   # acento oscuro
    assert "#C45F38" not in oscuro.upper() and "196,95,56" not in oscuro  # acento claro


def _plan(tmp_path, **extra):
    d = tmp_path / "videos" / "1"
    d.mkdir(parents=True)
    (d / "plan.json").write_text(json.dumps({"format": "REEL", **extra}))
    return tmp_path


def test_configure_sin_palette_falla_nombrando_el_campo(bc, tmp_path):
    with pytest.raises(SystemExit) as e:
        bc.configure(_plan(tmp_path), "1")
    assert "palette" in str(e.value) and "claro" in str(e.value) and "oscuro" in str(e.value)


def test_configure_con_palette_inexistente_falla(bc, tmp_path):
    with pytest.raises(SystemExit) as e:
        bc.configure(_plan(tmp_path, palette="violeta"), "1")
    assert "violeta" in str(e.value)


def test_configure_activa_la_paleta_antes_de_seguir(bc, tmp_path):
    # Sin face-1.json configure() sale DESPUÉS de activar la paleta.
    with pytest.raises(SystemExit) as e:
        bc.configure(_plan(tmp_path, palette="claro"), "1")
    assert "cara" in str(e.value)
    assert T.PALETTE == "claro" and T.C["bg"] == "#ECE7DE"


def test_load_edl_sin_palette_falla(problems_of, edl_min):
    edl = dict(edl_min)
    edl.pop("palette")
    assert "palette" in problems_of(edl)


def test_compile_edl_escribe_la_palette(write_edl, edl_min, style):
    from edl_compile import compile_edl
    plan = compile_edl(write_edl(dict(edl_min, palette="claro")), style)
    assert plan["palette"] == "claro"


def test_brand_tone_se_adapta_a_la_paleta():
    import logos
    for nombre in T.PALETTES:
        T.use(nombre)
        tono = logos.brand_tone("25D366")   # verde WhatsApp
        assert T.contrast(tono, T.C["surface"]) >= 3.0, nombre


@pytest.mark.parametrize("paleta", ["claro", "oscuro"])
def test_el_cursor_blanco_conserva_su_filete_oscuro(paleta):
    """El cursor es interfaz literal (blanco con filete), igual en las dos
    paletas: el filete es la tinta MÁS OSCURA de la paleta, no el suelo — en
    `claro` el suelo es crema y el cursor blanco se perdía (1.1:1)."""
    import mockups
    T.use(paleta)
    html = mockups._cursor("c1")
    trazo = re.search(r'stroke="(#[0-9A-Fa-f]{6})"', html).group(1)
    assert T.contrast("#FFFFFF", trazo) >= 3.0, (paleta, trazo)


@pytest.mark.parametrize("paleta", ["claro", "oscuro"])
def test_el_cursor_de_money_button_lleva_contorno(paleta):
    import mockups
    T.use(paleta)
    css, _, _ = mockups.money_button("mb", "GANAR DINERO", [0.2, 0.6, 1.0, 1.4, 1.8], question="¿Un botón?", empty_label="VACÍO")
    regla = re.search(r"\.mbcur\{[^}]*\}", css).group(0)
    oscura = min(T.C["bg"], T.C["text"], key=T.luminance)
    assert f"drop-shadow(0 0 2px {oscura})" in regla, regla
