"""Las cards de la banda de arriba.

Lo que protegen: que la card entre por OPACIDAD y lo que viaje sea su
contenido (§6), que el logo siga presente en la card de grabación, y que los
radios y la elevación salgan de los tokens y no a mano.

Añadido en la ronda de corrección de la Tarea 8: el marco del logo mide
contraste DE VERDAD contra las dos marcas casi invisibles que lo motivaron, el
parámetro `hairline` (sin ejercer hasta ahora), la copia de los PNG de marca a
`public/logos/` (sin la que Bklit UI y Kokonut UI salen con la imagen rota) y
el tilt 3D — estático en un wrapper hijo, nunca animado por GSAP.
"""
import re
import textwrap

import pytest


@pytest.fixture(scope="session")
def mk():
    import mockups
    return mockups


def test_la_card_no_viaja_su_contenido_si(mk):
    """§6: todo contenedor entra por opacidad; lo que se mueve es lo de dentro."""
    _, _, anims = mk.tool_card("tc", "motion", "Motion")
    kinds = {a[0] for a in anims}
    assert "glide-x" in kinds and "drop-in" in kinds
    sels = {a[1] for a in anims}
    assert not any(s.endswith("-card") for s in sels), "la card no se anima, entra fundiendo"


def test_el_logo_entra_en_horizontal_y_el_nombre_cae(mk):
    _, _, anims = mk.tool_card("tc", "motion", "Motion")
    por_kind = {a[0]: a[1] for a in anims}
    assert por_kind["glide-x"].endswith("-logo")
    assert por_kind["drop-in"].endswith("-name")


def test_el_nombre_entra_despues_del_logo(mk):
    """El retraso es lo que hace que se lean como dos elementos."""
    _, _, anims = mk.tool_card("tc", "motion", "Motion")
    d = {a[0]: a[2] for a in anims}
    assert d["drop-in"] > d["glide-x"]


def test_la_card_de_grabacion_conserva_la_marca(mk):
    """Sin el chip, 8 s de grabación se desatan de su nombre."""
    _, html, _ = mk.tool_recording("tr", "motion", "Motion", (60, 140, 960, 540))
    assert "Motion" in html


def test_ninguna_card_usa_negro_puro(mk):
    for css, _, _ in (mk.tool_card("a", "motion", "Motion"),
                      mk.tool_recording("b", "motion", "Motion", (60, 140, 960, 540))):
        low = css.lower().replace(" ", "")
        assert "#000000" not in low and "#000;" not in low


def test_el_radio_sale_de_los_tokens(mk):
    import tokens
    css, _, _ = mk.tool_card("tc", "motion", "Motion")
    assert f"{tokens.RADIUS['lg']}px" in css


def test_el_marco_del_logo_se_distingue_del_surface(mk):
    """Motion (`#0B0B0C`, 1.11:1) y Bklit UI (`#000000`, 1.18:1) son casi
    invisibles contra `surface` (#16181F): la solución fue `.tc-logoframe`,
    que le da al logo un borde propio.

    Se mide DE VERDAD con `tokens.contrast()`, no buscando la subcadena en
    el CSS: se extrae el color de borde que `.tc-logoframe` declara de
    verdad (sea cual sea, hoy `LINE_HI`) y se compone sobre `surface` con
    `tokens.lift()` — igual que documenta el docstring de `tool_card` — para
    obtener el ratio real del marco, y ese ratio se compara contra los
    ratios reales de los dos tiles que casi desaparecían.
    """
    import tokens

    css, _, _ = mk.tool_card("tc", "motion", "Motion")
    m = re.search(r"\.tc-logoframe\{[^}]*border:1px solid (rgba\([^)]*\))", css)
    assert m, "`.tc-logoframe` ya no declara un borde propio"
    r, g, b, alpha = re.match(
        r"rgba\((\d+),(\d+),(\d+),\s*(\.?\d+(?:\.\d+)?)\)", m.group(1)
    ).groups()
    assert (r, g, b) == ("255", "255", "255"), "el marco dejó de ser un blanco translúcido"

    surface = tokens.C["surface"]
    ratio_marco = tokens.contrast(tokens.lift(surface, float(alpha)), surface)
    ratio_motion = tokens.contrast("#0B0B0C", surface)
    ratio_bklit = tokens.contrast("#000000", surface)

    assert ratio_motion < 1.2 and ratio_bklit < 1.3, "los tiles de referencia cambiaron"
    assert ratio_marco > ratio_motion + 0.3
    assert ratio_marco > ratio_bklit + 0.3


def test_el_hairline_parametriza_el_grosor_del_marco(mk):
    """Ningún test ejercía `hairline` todavía. Manus es la única grabación
    CLARA de las cinco y necesita el marco grueso; el llamador lo decide con
    este parámetro, sin que `tool_recording` conozca ningún slug."""
    css_default, _, _ = mk.tool_recording("tr", "manus", "Manus", (60, 140, 960, 540))
    assert "border:1px solid" in css_default

    css_grueso, _, _ = mk.tool_recording(
        "tr2", "manus", "Manus", (60, 140, 960, 540), hairline=3)
    assert "border:3px solid" in css_grueso


def test_build_composition_copia_los_logos_png_a_public(bc, tmp_path):
    """`build-composition.py` gana un paso que copia `assets/logos/*.png` a
    `public/logos/`. Sin él, `logos.mark()` emite
    `<img src="logos/<slug>.png">` para Bklit UI y Kokonut UI y esa ruta no
    resuelve en el render: la card sale con la imagen rota.

    El fixture `bc` (conftest, Tarea 8) carga `build-composition.py` sin
    efectos secundarios (todo su estado vive en `configure()`, que aquí no
    se llama), así que montar `build()` entero — que exige plan.json,
    face-<n>.json y el resto de la pieza — sería desproporcionado para
    probar solo la copia. En su lugar se extrae el bucle REAL de la fuente
    de `build()` por el propio marcador que lo abre y lo cierra (nada
    reimplementado a mano) y se ejecuta contra un `ROOT`/`PUB` de prueba.
    """
    import inspect

    src = inspect.getsource(bc.build)
    m = re.search(
        r'    logos_src = ROOT.*?dst\.write_bytes\(src\.read_bytes\(\)\)\n',
        src, re.S)
    assert m, "el bucle de copia de logos cambió de forma; localízalo de nuevo"
    snippet = textwrap.dedent(m.group(0))

    root = tmp_path / "root"
    pub = tmp_path / "pub"
    (root / "assets" / "logos").mkdir(parents=True)
    (pub / "logos").mkdir(parents=True)
    (root / "assets" / "logos" / "bklitui.png").write_bytes(b"PNGDATA-BKLIT")
    (root / "assets" / "logos" / "kokonutui.png").write_bytes(b"PNGDATA-KOKONUT")
    (root / "assets" / "logos" / "motion.svg").write_text("<svg/>")  # no es PNG

    ns = {"ROOT": root, "PUB": pub}
    exec(compile(snippet, "<logos-copy>", "exec"), ns)

    assert (pub / "logos" / "bklitui.png").read_bytes() == b"PNGDATA-BKLIT"
    assert (pub / "logos" / "kokonutui.png").read_bytes() == b"PNGDATA-KOKONUT"
    assert not (pub / "logos" / "motion.svg").exists()


def test_el_tilt_3d_existe_y_gsap_no_lo_anima(mk, bc):
    """El aspecto 3D (`perspective()+rotateY()`) tiene que existir en el CSS
    de las dos cards, y ninguna tupla de `anims` puede tocar una
    transformación de rotación: la doctrina (`objects._object_html`, y ahora
    aquí) es que el tilt vive ESTÁTICO en un wrapper hijo y GSAP solo anima
    opacity/scale/x/y del div exterior — si GSAP tocara la rotación, un seek
    a mitad de tween podría descuadrar el render.
    """
    css_card, _, anims_card = mk.tool_card("tc", "motion", "Motion")
    css_rec, _, anims_rec = mk.tool_recording(
        "tr", "motion", "Motion", (60, 140, 960, 540))

    for css in (css_card, css_rec):
        assert "perspective(" in css
        assert "rotateY(" in css

    for anims in (anims_card, anims_rec):
        assert anims, "sin animaciones no hay nada que comprobar"
        for a in anims:
            js = bc.emit_anim(a).lower()
            assert "rotate" not in js
            assert "perspective" not in js
