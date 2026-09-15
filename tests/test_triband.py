"""El layout triband: animación arriba, texto en medio, hablante abajo.

Un modo por pieza, no un reemplazo. Lo que estos tests protegen es que un
EDL SIN `layout` compile exactamente igual que antes.
"""
import pytest


def test_band_es_una_camara_valida(edl_min, write_edl):
    """`BAND` entra en el mismo sitio que WIDE/MEDIUM/CLOSE/OFF."""
    from edl_schema import CAMERAS
    assert "BAND" in CAMERAS


def test_una_camara_inventada_sigue_rechazandose(edl_min, problems_of):
    """Añadir BAND no puede abrir la puerta a cualquier cosa."""
    malo = dict(edl_min)
    seg = dict(malo["segments"][0], camera="CINEMATIC")
    malo["segments"] = [seg]
    assert "camera 'CINEMATIC' desconocida" in problems_of(malo)


LAYOUT_OK = {"mode": "triband",
             "bands": {"top": [0, 820], "text": [820, 1120], "speaker": [1120, 1920]}}


def _con_layout(edl_min, layout, camera="BAND"):
    base = dict(edl_min, layout=layout)
    base["segments"] = [dict(base["segments"][0], camera=camera)]
    return base


def test_un_edl_sin_layout_no_declara_ninguno(edl_min, write_edl):
    """La ausencia de `layout` ES la prueba de regresión: camino viejo intacto."""
    assert write_edl(edl_min).layout == {}


def test_el_layout_valido_se_carga_entero(edl_min, write_edl):
    edl = write_edl(_con_layout(edl_min, LAYOUT_OK))
    assert edl.layout["mode"] == "triband"
    assert edl.layout["bands"]["text"] == [820, 1120]


def test_un_modo_desconocido_se_rechaza(edl_min, problems_of):
    malo = _con_layout(edl_min, dict(LAYOUT_OK, mode="cuatribanda"))
    assert "layout.mode 'cuatribanda' desconocido" in problems_of(malo)


def test_las_bandas_tienen_que_cubrir_el_lienzo_entero(edl_min, problems_of):
    """Un hueco entre bandas es suelo grafito que nadie decidió dejar."""
    malo = _con_layout(edl_min, {"mode": "triband", "bands": {
        "top": [0, 820], "text": [820, 1100], "speaker": [1120, 1920]}})
    assert "no son contiguas" in problems_of(malo)


def test_una_banda_invertida_se_rechaza(edl_min, problems_of):
    malo = _con_layout(edl_min, {"mode": "triband", "bands": {
        "top": [0, 820], "text": [1120, 820], "speaker": [1120, 1920]}})
    assert "banda 'text' invertida" in problems_of(malo)


def test_layout_declarado_sin_ningun_segmento_band_es_error(edl_min, problems_of):
    """Declarar geometría que nadie usa casi siempre es un olvido, no un estilo."""
    malo = _con_layout(edl_min, LAYOUT_OK, camera="CLOSE")
    assert "ningún segmento usa camera BAND" in problems_of(malo)


def test_un_segmento_band_sin_layout_es_error(edl_min, problems_of):
    malo = dict(edl_min)
    malo["segments"] = [dict(malo["segments"][0], camera="BAND")]
    assert "camera BAND sin bloque 'layout'" in problems_of(malo)
