"""El layout `formatos` (doctrina 2026-09-29): dos bandas a la mitad del lienzo, el
visual arriba y el hablante abajo. La geometría la fija la doctrina, no el plan."""
import pytest

import layout_formatos as lf

TRIBAND = {"top": [0, 660], "text": [660, 960], "speaker": [960, 1920]}


def test_formatos_parte_el_lienzo_a_la_mitad():
    assert lf.resolver({"mode": "formatos"}, 1920) == {
        "mode": "formatos", "bands": {"top": [0, 960], "speaker": [960, 1920]}}


def test_formatos_con_las_bandas_de_la_doctrina_pasa():
    b = {"top": [0, 960], "speaker": [960, 1920]}
    assert lf.resolver({"mode": "formatos", "bands": b}, 1920)["bands"] == b


def test_formatos_con_otras_bandas_falla():
    with pytest.raises(lf.LayoutError, match="doctrina"):
        lf.resolver({"mode": "formatos", "bands": {"top": [0, 700], "speaker": [700, 1920]}}, 1920)


def test_triband_se_respeta_tal_cual():
    assert lf.resolver({"mode": "triband", "bands": TRIBAND}, 1920) == {"mode": "triband", "bands": TRIBAND}


def test_triband_sin_sus_tres_bandas_falla():
    with pytest.raises(lf.LayoutError, match="top, text y speaker"):
        lf.resolver({"mode": "triband", "bands": {"top": [0, 960], "speaker": [960, 1920]}}, 1920)


def test_none_y_sin_layout():
    assert lf.resolver({"mode": "none"}, 1920) == {"mode": "none"}
    assert lf.resolver(None, 1920) == {}
    assert lf.resolver({}, 1920) == {}


def test_modo_desconocido_falla_nombrando_los_modos():
    with pytest.raises(lf.LayoutError, match="formatos, triband, none"):
        lf.resolver({"mode": "cuadros"}, 1920)


def test_costura():
    assert lf.costura(lf.resolver({"mode": "formatos"}, 1920)) == 960
    assert lf.costura({"mode": "triband", "bands": TRIBAND}) is None
    assert lf.costura({}) is None
