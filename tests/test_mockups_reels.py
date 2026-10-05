"""Contrato de los 16 mockups de la pieza 4."""

import re

import pytest

import mockups_reels as M
import tokens as T


LINEAS = [
    "Te paso la transcripción de un reel viral:",
    "[PEGA AQUÍ LA TRANSCRIPCIÓN]",
    "Mi nicho: [TU NICHO]. Mi audiencia: [A QUIÉN LE HABLAS].",
    "1. Marca el gancho, la estructura y el remate.",
    "2. Dime qué problema concreto resuelve.",
    "3. Reescríbelo para mi nicho con mis palabras:",
    "   misma estructura y duración, sin copiar frases.",
    "4. Dame 3 ganchos alternativos.",
]


CASES = [
    (M.ig_perfil, {"variant": "llenar", "at": [1, 2]}),
    (M.ig_perfil, {"variant": "ordenar", "at": [1, 2, 3], "lienzo": True}),
    (M.ig_perfil, {"variant": "vistas", "at": [1]}),
    (M.ig_barras, {"at": [1, 2]}),
    (M.ig_busqueda, {"at": [1, 2]}),
    (M.ig_guardar, {"at": [1, 2]}),
    (M.monigote, {"variant": "desinflar", "at": [1, 2], "lienzo": True}),
    (M.monigote, {"variant": "pregunta", "at": [1, 2], "lienzo": True}),
    (M.monigote, {"variant": "copiar", "at": [1]}),
    (M.nudo_viaje, {"at": [1, 2]}),
    (M.ideas_notas, {"at": [1, 2]}),
    (M.claude_chat, {"variant": "arrastrar", "at": [1, 2], "lienzo": True}),
    (M.claude_chat, {"variant": "enviar", "at": [1, 2]}),
    (M.escaneo, {"at": [1, 2]}),
    (M.prompt_encaje, {"at": [1, 2]}),
    (M.prompt_hoja, {"variant": "desplegar", "at": [1, 2], "lineas": LINEAS, "lienzo": True}),
    (M.prompt_hoja, {"variant": "copiar", "at": [1, 2], "lineas": LINEAS}),
    (M.prompt_hoja, {"variant": "absorber", "at": [1], "lineas": LINEAS}),
    (M.tablero, {"at": [1, 2]}),
    (M.reel_tarjeta, {"variant": "llega", "at": [1, 2, 3]}),
    (M.reel_tarjeta, {"variant": "girar", "at": [1, 2], "lienzo": True}),
    (M.reel_tarjeta, {"variant": "cruce", "at": [1, 2, 3]}),
    (M.reel_cascada, {"at": [1, 2, 3]}),
    (M.ig_grilla, {"variant": "contar", "at": [1, 2]}),
    (M.ig_grilla, {"variant": "respirar", "at": [1], "lienzo": True}),
    (M.ig_grilla, {"variant": "viral", "at": [1, 2]}),
    (M.guion_esqueleto, {"variant": "voltear", "at": [1, 2, 3], "lienzo": True}),
    (M.guion_esqueleto, {"variant": "replicar", "at": [1, 2]}),
]


@pytest.fixture(autouse=True)
def _restore_palette():
    yield
    T.use("oscuro")


@pytest.mark.parametrize("fn,kw", CASES, ids=lambda x: getattr(x, "__name__", str(x)))
def test_cada_variante_renderiza_en_las_dos_paletas_y_sus_selectores_existen(fn, kw):
    renders = []
    for palette in ("claro", "oscuro"):
        T.use(palette)
        css, html, anims = fn("pieza4", **kw)
        renders.append(css + html)
        ids = set(re.findall(r'(?<![-\w])id="([^"]+)"', html))
        assert len(ids) == len(re.findall(r'(?<![-\w])id="([^"]+)"', html))
        for anim in anims:
            selector = anim[1]
            assert not selector.startswith(".viz[")
            assert selector.startswith("#"), anim
            assert selector[1:] in ids, anim
    assert renders[0] != renders[1]


@pytest.mark.parametrize("fn,kw", [
    (M.ig_perfil, {"variant": "inventada", "at": [1]}),
    (M.monigote, {"variant": "inventada", "at": [1]}),
    (M.claude_chat, {"variant": "inventada", "at": [1]}),
    (M.prompt_hoja, {"variant": "inventada", "at": [1], "lineas": LINEAS}),
    (M.reel_tarjeta, {"variant": "inventada", "at": [1]}),
    (M.ig_grilla, {"variant": "inventada", "at": [1]}),
    (M.guion_esqueleto, {"variant": "inventada", "at": [1]}),
])
def test_variante_desconocida_lanza(fn, kw):
    with pytest.raises(ValueError):
        fn("x", **kw)


@pytest.mark.parametrize("fn,kw", [
    (M.ig_perfil, {"variant": "llenar", "at": [1]}),
    (M.ig_barras, {"at": [1]}),
    (M.ig_busqueda, {"at": [1]}),
    (M.ig_guardar, {"at": [1]}),
    (M.monigote, {"variant": "pregunta", "at": [1]}),
    (M.nudo_viaje, {"at": [1]}),
    (M.ideas_notas, {"at": [1]}),
    (M.claude_chat, {"variant": "enviar", "at": [1]}),
    (M.escaneo, {"at": [1]}),
    (M.prompt_encaje, {"at": [1]}),
    (M.prompt_hoja, {"variant": "desplegar", "at": [1], "lineas": LINEAS}),
    (M.tablero, {"at": [1]}),
    (M.reel_tarjeta, {"variant": "llega", "at": [1]}),
    (M.reel_cascada, {"at": [1]}),
    (M.ig_grilla, {"variant": "contar", "at": [1]}),
    (M.guion_esqueleto, {"variant": "voltear", "at": [1]}),
])
def test_at_de_longitud_incorrecta_lanza(fn, kw):
    with pytest.raises(ValueError):
        fn("x", **kw)


def test_texto_dicho_no_esta_en_el_dom_antes_del_tiempo():
    _, html, _ = M.ig_busqueda("q", [1, 2], query="inteligencia artificial")
    assert "inteligencia artificial" not in html
    _, html, _ = M.prompt_hoja("p", "desplegar", [1, 4], LINEAS, lienzo=True)
    for line in LINEAS:
        assert line not in html


def test_avatar_derivado_es_jpeg_200(project_root):
    from PIL import Image
    p = project_root / "assets" / "avatar-propio.jpg"
    with Image.open(p) as im:
        assert im.format == "JPEG"
        assert im.size == (200, 200)

