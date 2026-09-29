"""El primer plano de `cara` se acerca hasta donde la fuente lo aguanta sin pixelarse:
×1,20 con 1080×1920 y ×1,40 con una fuente 4K."""
import pytest


@pytest.fixture
def fuente(bc):
    prev = (bc.SRC_W, bc.SRC_H)
    yield bc
    bc.SRC_W, bc.SRC_H = prev


def _full(zoom):
    return [{"start": 2.0, "end": 5.0, "kind": "full", "zoom": zoom, "anchor": 0.44}]


def test_1080_hasta_1_20(fuente):
    fuente.SRC_W, fuente.SRC_H = 1080, 1920
    assert fuente.zoom_max() == 1.20
    fuente.check_cara_zoom(_full(1.20))
    with pytest.raises(SystemExit) as ei:
        fuente.check_cara_zoom(_full(1.25))
    assert "1.25" in str(ei.value) and "4K" in str(ei.value)


def test_4k_hasta_1_40(fuente):
    fuente.SRC_W, fuente.SRC_H = 2160, 3840
    assert fuente.zoom_max() == 1.40
    fuente.check_cara_zoom(_full(1.35))
    with pytest.raises(SystemExit):
        fuente.check_cara_zoom(_full(1.45))


def test_solo_mira_los_encuadres_full(fuente):
    fuente.SRC_W, fuente.SRC_H = 1080, 1920
    fuente.check_cara_zoom([{"start": 0.0, "end": 1.0, "kind": "band", "zoom": 1.5, "anchor": 0.4}])
