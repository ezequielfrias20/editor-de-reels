"""El gate que impide cortar la cara por arriba en un encuadre `band` (Mejora 2).

`check_band_speaker_clear` ya cazaba un mockup opaco tapando al hablante; a
este le falta el caso simétrico: un `anchor` demasiado alto, con
`object-fit: cover`, recorta más del techo de la FUENTE y se lleva la
coronilla por delante — el mismo tipo de error, sin arreglo en post, que
tiene que parar la compilación en vez de colarse hasta el MP4.

La cuenta reutiliza la fórmula de `chin_at` para el kind `band` (rect de la
banda `speaker`, escala de `object-fit: cover`, reparto del desborde por
`anchor`) pero proyecta `TOP_FRAC` en vez de `CHIN`. Con `SRC_W == W` la
escala siempre es 1.0 y `drawn_h == SRC_H`, así que los números salen limpios:
con la banda `speaker` en [960, 1920] (960 px de alto) y `TOP_FRAC = 0.30`,

    face_top = (960 − 960·anchor) + 0.30·1920 = 1536 − 960·anchor

cruza el techo de la banda (y960) exactamente en `anchor = 0.6`.
"""
import pytest

BANDS = {"top": [0, 660], "text": [660, 960], "speaker": [960, 1920]}


@pytest.fixture(autouse=True)
def lienzo(bc):
    bc.W, bc.H = 1080, 1920
    bc.LAYOUT = {"mode": "triband", "bands": BANDS}
    bc.SRC_W, bc.SRC_H = 1080, 1920
    bc.TOP_FRAC = 0.30
    yield
    bc.LAYOUT = {}
    bc.TOP_FRAC = None


def _band_shot(anchor, start=8.0, end=16.0):
    return {"start": start, "end": end, "kind": "band", "anchor": anchor}


def test_anchor_por_debajo_del_umbral_no_corta_la_cara(bc):
    """anchor 0.5 < 0.6: el borde superior de la cara cae en y1056, dentro de
    la banda `speaker` (techo y960) — no debe lanzar."""
    bc.check_face_top_clear([_band_shot(0.5)], 20.0)  # no debe lanzar


def test_anchor_justo_en_el_umbral_pasa(bc):
    """anchor exactamente 0.6: el borde de la cara toca y960 —el propio
    techo—, no lo cruza. La comparación es estricta (`<`), así que el límite
    es válido."""
    bc.check_face_top_clear([_band_shot(0.6)], 20.0)  # no debe lanzar


def test_anchor_por_encima_del_umbral_corta_la_cara(bc):
    """anchor 0.7 > 0.6: el borde superior de la cara sube a y864, POR ENCIMA
    del techo de la banda `speaker` — tiene que fallar con un mensaje claro."""
    with pytest.raises(SystemExit) as ei:
        bc.check_face_top_clear([_band_shot(0.7)], 20.0)
    msg = str(ei.value)
    assert "cortada" in msg
    assert "speaker" in msg
    assert "0.70" in msg


def test_sin_top_frac_el_gate_se_salta_limpio(bc):
    """Una medición vieja sin `top_frac` (piezas de antes de la Mejora 2) no
    puede romper la compilación: el gate se salta en vez de reventar con un
    TypeError, aunque el anchor sea uno que SÍ cortaría la cara."""
    bc.TOP_FRAC = None
    bc.check_face_top_clear([_band_shot(0.9)], 20.0)  # no debe lanzar


def test_sin_encuadres_band_el_gate_no_hace_nada(bc):
    """Regresión: una pieza sin ningún encuadre `band` (full/pip/split) no
    tiene banda `speaker` que proteger."""
    shots = [{"start": 0.0, "end": 20.0, "kind": "full", "anchor": 0.9, "zoom": 1.0}]
    bc.check_face_top_clear(shots, 20.0)  # no debe lanzar


def test_el_anchor_0_38_de_la_pieza_15_deja_margen_real(bc):
    """El anchor elegido en la Mejora 2 no es un valor límite: con
    `TOP_FRAC = 0.30` (sintético, redondo) deja 634 px de margen sobre el
    techo de la banda, muy por encima del umbral (0.6)."""
    bc.check_face_top_clear([_band_shot(0.38)], 20.0)  # no debe lanzar
