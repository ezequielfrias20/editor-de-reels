"""`band` confina el host de un visual a una banda del triband (Tarea 9c).

El bug que esto arregla: un `tool_card` (`kind: "mockup"`) recibía un host a
LIENZO COMPLETO con fondo opaco (grid+vignette), así que durante las cinco
cards de logo de la pieza 15 el hablante desaparecía por debajo — medido en
el MP4, luma máxima 28 en la banda [1120,1920] donde debía verse su
camiseta blanca. `band` deja vivir al visual DENTRO de una banda: el host
toma el rect de esa banda (no el lienzo) y su fondo pasa a transparente,
para que el metraje de las demás bandas — en particular la del hablante —
se siga viendo por debajo.
"""
import pytest

BANDS = {"top": [0, 820], "text": [820, 1120], "speaker": [1120, 1920]}


@pytest.fixture(autouse=True)
def lienzo(bc):
    bc.W, bc.H = 1080, 1920
    bc.LAYOUT = {"mode": "triband", "bands": BANDS}
    yield
    bc.LAYOUT = {}
    bc.VISUALS = None


def _tool_card(band=None):
    v = {
        "id": "v-t", "role": "takeover", "kind": "mockup",
        "start": 1.0, "end": 2.0,
        "mock": ["tool_card", {"slug": "motion", "name": "Motion", "kicker": "X"}],
    }
    if band:
        v["band"] = band
    return v


def test_band_confina_el_host_al_rect_de_la_banda(bc):
    """El host ya no es `left:0;top:0;width:W;height:H`: es el rect de la
    banda declarada, sacado de `LAYOUT["bands"]` — no inventado aquí."""
    bc.VISUALS = [_tool_card("top")]
    _, _, hosts_back, hosts_over, *_ = bc.build_visuals(10.0)
    assert hosts_back == []
    assert len(hosts_over) == 1
    assert "left:0px;top:0px;width:1080px;height:820px;" in hosts_over[0]


def test_sin_band_el_host_sigue_a_lienzo_completo(bc):
    """Regresión: un visual SIN `band` compila exactamente igual que antes."""
    bc.VISUALS = [_tool_card(None)]
    _, _, _, hosts_over, *_ = bc.build_visuals(10.0)
    assert "left:0px;top:0px;width:1080px;height:1920px;" in hosts_over[0]


def test_band_deja_el_fondo_transparente(bc):
    """Es la parte que arregla el bug: con `band`, el `.vizbg` de un mockup
    ya NO pinta grid+vignette encima de la banda del hablante."""
    bc.VISUALS = [_tool_card("top")]
    css, *_ = bc.build_visuals(10.0)
    assert '.viz[data-viz-id="v-t"] .vizbg{position:absolute;inset:0;background:transparent}' in css


def test_sin_band_el_mockup_sigue_siendo_opaco(bc):
    """Regresión: el fondo opaco de un mockup a lienzo completo no se toca —
    la regla vieja sigue viva para el caso que la necesita."""
    bc.VISUALS = [_tool_card(None)]
    css, *_ = bc.build_visuals(10.0)
    assert '.viz[data-viz-id="v-t"] .vizbg{position:absolute;inset:0;background:transparent}' not in css


def test_band_no_resta_el_16pc_de_vizcam_mock(bc):
    """`.vizcam.mock` resta un 16% de alto para la zona segura de la
    PLATAFORMA sobre el LIENZO ENTERO. Con el host ya confinado a una banda
    ese descuento no aplica: el visual centra a secas."""
    bc.VISUALS = [_tool_card("top")]
    _, _, _, hosts_over, *_ = bc.build_visuals(10.0)
    assert 'class="vizcam"' in hosts_over[0]
    assert 'class="vizcam mock"' not in hosts_over[0]


def test_sin_band_vizcam_mock_sigue_aplicando(bc):
    bc.VISUALS = [_tool_card(None)]
    _, _, _, hosts_over, *_ = bc.build_visuals(10.0)
    assert 'class="vizcam mock"' in hosts_over[0]


def test_band_sin_bloque_layout_falla_claro(bc):
    """No hay default silencioso: declarar `band` sin `layout` en el plan
    tiene que fallar con un mensaje que diga por qué, no reventar con un
    KeyError o —peor— dibujar el visual a lienzo completo como si nada."""
    bc.LAYOUT = {}
    bc.VISUALS = [_tool_card("top")]
    with pytest.raises(SystemExit) as ei:
        bc.build_visuals(10.0)
    msg = str(ei.value)
    assert "band" in msg and "layout" in msg
