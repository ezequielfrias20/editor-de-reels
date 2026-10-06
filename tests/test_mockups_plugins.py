"""Contrato de los 15 mockups de la pieza 5."""

import re

import pytest

import mockups_plugins as M
import tokens as T


CASES = [
    (M.terminal_barrera, {"at": [1, 2]}),
    (M.zocalo, {"variant": "instala", "at": [1, 2, 3], "lienzo": True}),
    (M.zocalo, {"variant": "enciende", "at": [1, 2], "puestos": 0}),
    (M.zocalo, {"variant": "enciende", "at": [1, 2], "puestos": 4}),
    (M.zocalo, {"variant": "lista", "at": [1, 2]}),
    (M.anillo_proveedores, {"at": [1, 2]}),
    (M.costo_llaves, {"at": [1, 2, 3]}),
    (M.piedras_modelo, {"at": [1, 2, 3]}),
    (M.contador_tokens, {"at": [1, 2, 3]}),
    (M.dos_terminales, {"at": [1, 2, 3]}),
    (M.cable_headroom, {"variant": "clavar", "at": [1, 2]}),
    (M.cable_headroom, {"variant": "chat", "at": [1, 2], "lienzo": True}),
    (M.prensa, {"at": [1, 2, 3]}),
    (M.dos_salidas, {"at": [1, 2]}),
    (M.sello_oficial, {"at": [1, 2]}),
    (M.arbol_escaneo, {"at": [1, 2]}),
    (M.servidor_mcp, {"variant": "conectar", "at": [1, 2], "lienzo": True}),
    (M.servidor_mcp, {"variant": "aterrizar", "at": [1]}),
    (M.mascota_cuaderno, {"at": [1, 2, 3]}),
    (M.reloj_fondo, {"at": [1, 2]}),
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
        result = fn("pieza5", **kw)
        assert isinstance(result, tuple) and len(result) == 3
        css, html, anims = result
        renders.append(css + html)
        found = re.findall(r'(?<![-\w])id="([^"]+)"', html)
        ids = set(found)
        assert len(ids) == len(found), "ningun id puede repetirse"
        for anim in anims:
            selector = anim[1]
            assert not selector.startswith(".viz[")
            assert selector.startswith("#"), anim
            assert selector[1:] in ids, anim
    assert renders[0] != renders[1]


@pytest.mark.parametrize("fn,kw", [
    (M.zocalo, {"variant": "inventada", "at": [1, 2]}),
    (M.cable_headroom, {"variant": "inventada", "at": [1, 2]}),
    (M.servidor_mcp, {"variant": "inventada", "at": [1]}),
])
def test_variante_desconocida_lanza(fn, kw):
    with pytest.raises(ValueError):
        fn("x", **kw)


@pytest.mark.parametrize("fn,kw", [
    (M.terminal_barrera, {"at": [1]}),
    (M.zocalo, {"variant": "instala", "at": [1, 2]}),
    (M.anillo_proveedores, {"at": [1]}),
    (M.costo_llaves, {"at": [1, 2]}),
    (M.piedras_modelo, {"at": [1, 2]}),
    (M.contador_tokens, {"at": [1, 2]}),
    (M.dos_terminales, {"at": [1, 2]}),
    (M.cable_headroom, {"variant": "clavar", "at": [1]}),
    (M.prensa, {"at": [1, 2]}),
    (M.dos_salidas, {"at": [1]}),
    (M.sello_oficial, {"at": [1]}),
    (M.arbol_escaneo, {"at": [1]}),
    (M.servidor_mcp, {"variant": "conectar", "at": [1]}),
    (M.mascota_cuaderno, {"at": [1, 2]}),
    (M.reloj_fondo, {"at": [1]}),
])
def test_at_de_longitud_incorrecta_lanza(fn, kw):
    with pytest.raises(ValueError):
        fn("x", **kw)


@pytest.mark.parametrize("bad", [
    [-0.01, 1],
    [2, 1],
    [1, float("inf")],
    [1, "dos"],
])
def test_at_fuera_de_rango_lanza(bad):
    with pytest.raises(ValueError):
        M.terminal_barrera("x", bad)


@pytest.mark.parametrize("puestos", [-1, 5, 1.5, "2"])
def test_zocalo_enciende_rechaza_puestos_fuera_de_rango(puestos):
    with pytest.raises(ValueError):
        M.zocalo("x", "enciende", [1, 2], puestos=puestos)


def test_texto_y_contador_dichos_no_estan_adelantados_en_el_dom():
    _, html, _ = M.zocalo("z", "enciende", [1, 2], puestos=0)
    match = re.search(r'id="z-m0-name"[^>]*>(.*?)</span>', html, flags=re.S)
    assert match and match.group(1) == ""
    assert "OmniRoute" not in html

    _, html, _ = M.anillo_proveedores("a", [1, 2])
    match = re.search(r'id="a-count"[^>]*>(.*?)</span>', html, flags=re.S)
    assert match and match.group(1) == "0"
    assert not re.search(r">[^<]*200[^<]*<", html)
    assert not re.search(r">[^<]*358[^<]*<", html)
