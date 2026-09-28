"""La geometría de las tres bandas.

`shot_geometry` lee globals (W, H, LAYOUT), no recibe parámetros de lienzo:
los tests los fijan igual que hace `configure()`.
"""
import pytest

BANDS = {"top": [0, 820], "text": [820, 1120], "speaker": [1120, 1920]}


@pytest.fixture(autouse=True)
def lienzo(bc):
    bc.W, bc.H = 1080, 1920
    bc.LAYOUT = {"mode": "triband", "bands": BANDS}
    yield
    bc.LAYOUT = {}


def test_las_tres_bandas_salen_a_ancho_completo(bc):
    p = bc.triband_panels()
    for k in ("top", "text", "speaker"):
        assert (p[k]["left"], p[k]["width"]) == (0, 1080), k


def test_la_banda_del_hablante_mide_800(bc):
    p = bc.triband_panels()
    assert (p["speaker"]["top"], p["speaker"]["height"]) == (1120, 800)


def test_band_usa_el_rect_del_hablante(bc):
    g = bc.shot_geometry("band", 1.0, 0.45)
    assert (g["left"], g["top"], g["width"], g["height"]) == (0, 1120, 1080, 800)


def test_band_ignora_el_zoom(bc):
    """El zoom no aplica: el rect es el de la banda, venga el zoom que venga."""
    a = bc.shot_geometry("band", 1.0, 0.45)
    b = bc.shot_geometry("band", 1.15, 0.45)
    assert a == b


def test_band_ignora_anchorx(bc):
    """Como split y pip: el reencuadre horizontal lo hace object-position."""
    assert bc.shot_geometry("band", 1.0, 0.45) == bc.shot_geometry("band", 1.0, 0.45, 0.2)


def test_el_anchor_va_a_object_position(bc):
    assert bc.shot_geometry("band", 1.0, 0.45)["objpos"] == "50% 45%"


def test_el_anchor_no_se_redondea_a_un_porcentaje_entero(bc):
    """`check_face_top_clear` verifica el anchor exacto. Si el CSS lo redondea (0.407 → 41%),
    se renderiza un encuadre que nadie verificó: con una ventana válida de 0.0004 (pieza 1),
    ese redondeo es la coronilla cortada."""
    assert bc.shot_geometry("band", 1.0, 0.407)["objpos"] == "50% 40.7%"
    assert bc.shot_geometry("band", 1.0, 0.4068)["objpos"] == "50% 40.68%"


def test_la_barbilla_cae_sobre_la_banda_del_hablante(bc):
    """Con el metraje 1080x1920 en una ventana de 1080x800 la escala es 1.0.

    NOTA: el brief original proponía `anchor=0.45`, pero con `CHIN=0.55` y el
    desborde vertical de este encuadre (1920 de metraje contra 800 de banda)
    esa combinación da y=1672 — DENTRO de la zona de la plataforma, violando
    la propia aserción del test. Verificado a mano y con la fórmula exacta de
    `chin_at`: el punto de cruce está en anchor≈0.5714 (`(1536-1120)/1120 +
    CHIN·… ver texto`); por debajo, la barbilla cae en la franja de la
    interfaz. Se sube el anchor a 0.65 —dentro del mismo rango [0,1] que usa
    `shot_geometry`— para que el test demuestre la invariante que dice
    comprobar en vez de contradecirla."""
    bc.SRC_W, bc.SRC_H, bc.CHIN = 1080, 1920, 0.55
    y = bc.chin_at({"kind": "band", "zoom": 1.0, "anchor": 0.65})
    assert 1120 <= y <= 1920
    assert y < 1536, "la barbilla no puede caer en la zona de la plataforma"


def test_sin_layout_band_falla_claro(bc):
    """Un `band` sin layout es un bug del compilador, no un default silencioso."""
    bc.LAYOUT = {}
    with pytest.raises(Exception):
        bc.shot_geometry("band", 1.0, 0.45)
