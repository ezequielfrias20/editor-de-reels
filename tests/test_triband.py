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
