"""El anclaje horizontal del reencuadre — cambio quirúrgico nº 2.

El punch-in es una caja SOBREDIMENSIONADA con desborde negativo. Hasta ahora el
desborde se repartía a partes iguales (`-(w - W) / 2`), o sea: el crop ocurría
alrededor del centro GEOMÉTRICO del cuadro. Con `anchorX` ocurre alrededor de la
cara, que es lo que mide `cx_frac`.

Lo que estos tests protegen es la retrocompatibilidad: sin `anchorX` el rect
tiene que salir idéntico al de las 4 piezas publicadas.
"""
import pytest


@pytest.fixture(autouse=True)
def lienzo_reel(bc):
    """Los globals del formato REEL. `shot_geometry` los lee, no los recibe."""
    bc.W, bc.H = 1080, 1920
    yield


def test_sin_anchorx_es_el_comportamiento_de_siempre(bc):
    """El default 0.5 tiene que dar `-(w - W) / 2` EXACTO, no aproximado."""
    for zoom in (1.0, 1.05, 1.12, 1.15, 1.2, 1.25):
        g = bc.shot_geometry("full", zoom, 0.42)
        w = round(1080 * zoom)
        assert g["left"] == round(-(w - 1080) / 2), f"zoom {zoom}"


def test_anchorx_explicito_de_0_5_es_el_mismo_rect(bc):
    assert bc.shot_geometry("full", 1.2, 0.42) == \
           bc.shot_geometry("full", 1.2, 0.42, 0.5)


def test_el_crop_se_mueve_hacia_la_cara(bc):
    """`cx_frac` 0.4861 (pieza 10): el sujeto está a la izquierda del centro,
    así que la caja tiene que desplazarse a la DERECHA para encuadrarlo."""
    centro = bc.shot_geometry("full", 1.2, 0.42, 0.5)["left"]
    cara = bc.shot_geometry("full", 1.2, 0.42, 0.4861)["left"]
    assert cara > centro
    assert cara == round(-(round(1080 * 1.2) - 1080) * 0.4861)


def test_los_extremos_no_dejan_franja_negra(bc):
    """anchorX 0 y 1 pegan la caja a un borde, nunca la despegan del otro."""
    w = round(1080 * 1.2)
    assert bc.shot_geometry("full", 1.2, 0.42, 0.0)["left"] == 0
    assert bc.shot_geometry("full", 1.2, 0.42, 1.0)["left"] == -(w - 1080)


def test_anchorx_no_toca_el_eje_vertical(bc):
    """La barbilla es de `anchor`. Si `anchorX` moviera `top`, el subtítulo
    calculado por `chin_at()` dejaría de cuadrar con lo que se ve."""
    a = bc.shot_geometry("full", 1.2, 0.42, 0.5)
    b = bc.shot_geometry("full", 1.2, 0.42, 0.2)
    assert a["top"] == b["top"]
    assert (a["width"], a["height"]) == (b["width"], b["height"])


def test_split_y_pip_ignoran_anchorx(bc):
    """Solo `full` desborda. En `split`/`pip` el panel tiene rect propio y el
    reencuadre horizontal lo hace `object-position`, que ya está centrado."""
    for kind in ("split", "pip"):
        assert bc.shot_geometry(kind, 1.2, 0.40) == \
               bc.shot_geometry(kind, 1.2, 0.40, 0.2)
