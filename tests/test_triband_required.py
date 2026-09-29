"""El triband deja de ser opcional en REEL — doctrina de la sesión 2026-09-15.

Hasta ahora `layout` era un bloque que una pieza declaraba SI QUERÍA el
triband; la mayoría de piezas REEL no lo traían y compilaban igual, cayendo
al full/pip/split de siempre sin que nada lo señalara. Desde ahora una pieza
REEL sin `layout` es un olvido, no una opción, y `check_triband_default` la
para en tiempo de compilación — con una escotilla explícita
(`"layout": {"mode": "none"}`) para quien renuncie al triband a sabiendas.

YOUTUBE queda fuera del gate a propósito: el triband es un reparto vertical
y no tiene sentido en 16:9.
"""
import pytest


@pytest.fixture(autouse=True)
def limpio(bc):
    yield
    bc.FMT = "REEL"
    bc.LAYOUT = {}


def test_reel_sin_layout_falla(bc):
    """El caso que esta doctrina existe para cazar: una pieza REEL nueva a la
    que se le olvidó declarar `layout` no debe llegar al MP4 sin bandas."""
    bc.FMT = "REEL"
    bc.LAYOUT = {}
    with pytest.raises(SystemExit) as ei:
        bc.check_layout_default()
    msg = str(ei.value)
    assert "REEL" in msg
    assert "layout" in msg
    assert '"mode": "formatos"' in msg


def test_el_mensaje_de_error_dice_la_escotilla(bc):
    """Un gate sin salida documentada acaba comentado. El mensaje tiene que
    nombrar `"mode": "none"`, no solo pedir el triband."""
    bc.FMT = "REEL"
    bc.LAYOUT = {}
    with pytest.raises(SystemExit) as ei:
        bc.check_layout_default()
    assert '"mode": "none"' in str(ei.value)


def test_reel_con_layout_triband_pasa(bc):
    bc.FMT = "REEL"
    bc.LAYOUT = {"mode": "triband",
                 "bands": {"top": [0, 660], "text": [660, 960], "speaker": [960, 1920]}}
    bc.check_layout_default()  # no debe lanzar


def test_reel_con_la_escotilla_mode_none_pasa(bc):
    """La renuncia explícita y documentada: una pieza que de verdad no
    necesita el triband lo declara a sabiendas, no por omisión."""
    bc.FMT = "REEL"
    bc.LAYOUT = {"mode": "none"}
    bc.check_layout_default()  # no debe lanzar


def test_youtube_sin_layout_no_falla(bc):
    """El gate no aplica a YOUTUBE: el triband es un layout vertical y en
    apaisado no hay banda de arriba que llenar."""
    bc.FMT = "YOUTUBE"
    bc.LAYOUT = {}
    bc.check_layout_default()  # no debe lanzar


def test_youtube_con_layout_tambien_pasa(bc):
    """Regresión trivial: declarar `layout` en YOUTUBE no rompe nada, el
    gate simplemente no tiene nada que exigir ahí."""
    bc.FMT = "YOUTUBE"
    bc.LAYOUT = {"mode": "triband",
                 "bands": {"top": [0, 660], "text": [660, 960], "speaker": [960, 1920]}}
    bc.check_layout_default()  # no debe lanzar


def test_reel_con_layout_formatos_pasa(bc):
    bc.FMT = "REEL"
    bc.LAYOUT = {"mode": "formatos", "bands": {"top": [0, 960], "speaker": [960, 1920]}}
    bc.check_layout_default()  # no debe lanzar
