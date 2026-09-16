"""`check_band_top_covered` — la banda `top` nunca puede quedarse vacía
durante un tramo `band` (doctrina de 2026-09-15, a petición del usuario: «en
la parte de animaciones siempre se debe mostrar algo, en cualquier segundo,
nunca debe estar el fondo vacío»).

Medido en la pieza 15 antes de este gate: la banda de arriba se quedaba en
suelo grafito liso 15.0 s de 55.3 s (27%) de sus tramos `band`, en siete
huecos. La resolución de la tensión con «nada entra antes de su palabra»
(§7): se SOSTIENE el visual anterior (se extiende su `end`), nunca se
adelanta el siguiente. El hueco de arranque —nada delante que sostener— se
cierra moviendo el `at` del propio encuadre `band`, no aquí.
"""
import pytest

BANDS = {"top": [0, 660], "text": [660, 960], "speaker": [960, 1920]}


@pytest.fixture(autouse=True)
def lienzo(bc):
    bc.W, bc.H = 1080, 1920
    bc.LAYOUT = {"mode": "triband", "bands": BANDS}
    yield
    bc.LAYOUT = {}
    bc.VISUALS = None


def _band_shot(start, end):
    return {"start": start, "end": end, "kind": "band", "anchor": 0.38}


def _card(vid, start, end):
    """Una card de logo: `kind: mockup` + `band: "top"` — cobertura por
    confinamiento de host (mecanismo 1)."""
    return {
        "id": vid, "role": "takeover", "kind": "mockup",
        "start": start, "end": end, "band": "top",
        "mock": ["tool_card", {"slug": "motion", "name": "Motion"}],
    }


def _recording(vid, start, end):
    """Una grabación: `kind: screen-video`, SIN `band` — cobertura por
    solape vertical de su `rect` con la banda `top` (mecanismo 2)."""
    return {
        "id": vid, "role": "takeover", "kind": "screen-video",
        "start": start, "end": end, "src": f"{vid}.mp4",
        "rect": [60, 100, 960, 540],
        "tool_recording": {"slug": "motion", "name": "Motion"},
    }


def test_sin_encuadres_band_el_gate_no_hace_nada(bc):
    """Regresión: full/pip/split no tienen banda `top` que llenar."""
    bc.VISUALS = []
    shots = [{"start": 0.0, "end": 20.0, "kind": "full"}]
    bc.check_band_top_covered(shots, 20.0)  # no debe lanzar


def test_hueco_de_arranque_sin_ningun_visual_falla(bc):
    """Un tramo `band` completo sin ningún visual en la banda `top`."""
    bc.VISUALS = []
    with pytest.raises(SystemExit) as ei:
        bc.check_band_top_covered([_band_shot(8.0, 16.0)], 20.0)
    msg = str(ei.value)
    assert "8.00" in msg and "16.00" in msg


def test_card_con_band_top_cubre_el_tramo_entero(bc):
    """Mecanismo 1: `band: \"top\"` cubre — no debe lanzar."""
    bc.VISUALS = [_card("v-1", 8.0, 16.0)]
    bc.check_band_top_covered([_band_shot(8.0, 16.0)], 20.0)  # no debe lanzar


def test_grabacion_por_rect_cuenta_como_cobertura(bc):
    """Mecanismo 2, el que se comprobó primero contra la pieza 15 real y
    daba falso positivo: una grabación `screen-video` nunca declara `band`
    (coloca su `<video>` con `rect` en coordenadas de lienzo), pero su rect
    [60,100,960,540] cae dentro de la banda `top` [0,660] y tiene que contar
    como cobertura igual que una card."""
    bc.VISUALS = [_recording("v-rec", 8.0, 16.0)]
    bc.check_band_top_covered([_band_shot(8.0, 16.0)], 20.0)  # no debe lanzar


def test_grabacion_con_rect_fuera_de_la_banda_top_no_cuenta(bc):
    """Un `rect` que vive en la banda `speaker` (p.ej. y1000) no tapa el
    hueco de la banda `top` — sigue siendo un hueco real."""
    v = _recording("v-rec", 8.0, 16.0)
    v["rect"] = [60, 1000, 960, 540]
    bc.VISUALS = [v]
    with pytest.raises(SystemExit):
        bc.check_band_top_covered([_band_shot(8.0, 16.0)], 20.0)


def test_hueco_entre_dos_visuales_de_banda_falla_con_los_tiempos(bc):
    """El caso central de la pieza 15: sostener el anterior hasta que entra
    el siguiente. Sin sostenerlo, el hueco intermedio tiene que fallar
    listando sus tiempos exactos — un gate que solo dice «hay un hueco»
    obliga a buscarlo a mano."""
    bc.VISUALS = [
        _card("v-tool-1", 9.0, 10.7),
        _recording("v-rec-1", 10.7, 15.6),
        _card("v-tool-2", 17.0, 18.3),
    ]
    with pytest.raises(SystemExit) as ei:
        bc.check_band_top_covered([_band_shot(9.0, 25.0)], 30.0)
    msg = str(ei.value)
    assert "15.60" in msg and "17.00" in msg


def test_sostener_el_anterior_cierra_el_hueco(bc):
    """El arreglo real de la pieza 15: se extiende el `end` de la grabación
    ANTERIOR hasta el `start` de la card SIGUIENTE — nunca se adelanta la
    siguiente. Con el mismo material de arriba, solo estirado, no debe
    lanzar."""
    bc.VISUALS = [
        _card("v-tool-1", 9.0, 10.7),
        _recording("v-rec-1", 10.7, 17.0),   # end estirado hasta v-tool-2.start
        _card("v-tool-2", 17.0, 18.3),
    ]
    bc.check_band_top_covered([_band_shot(9.0, 18.3)], 30.0)  # no debe lanzar


def test_transicion_contigua_no_cuenta_como_hueco_por_margen_de_fundido(bc):
    """Dos visuales de banda que se TOCAN exactamente (la card y su propia
    grabación, como en las cinco herramientas de la pieza 15) no pueden
    marcarse en falso: la cuenta usa ventanas CRUDAS, no el margen de
    `fade_in`/`fade_out` que sí aplica `check_no_black` — con margen, este
    cruce de opacidades legítimo se leería como un hueco de ~0.5s."""
    bc.VISUALS = [_card("v-tool-1", 9.0, 10.747), _recording("v-rec-1", 10.747, 15.648)]
    bc.check_band_top_covered([_band_shot(9.0, 15.648)], 30.0)  # no debe lanzar


def test_tolerancia_de_un_frame_no_falla_por_redondeo(bc):
    """Un hueco de menos de 1/FPS (redondeo de cuantización) no debe hacer
    fallar la compilación — la misma tolerancia que `check_band_speaker_clear`."""
    bc.VISUALS = [_card("v-1", 8.0, 11.999), _recording("v-rec", 12.001, 16.0)]
    bc.check_band_top_covered([_band_shot(8.0, 16.0)], 20.0)  # no debe lanzar


def test_varios_encuadres_band_seguidos_cuentan_como_un_solo_tramo(bc):
    """Las cinco herramientas de la pieza 15 son CINCO encuadres `band`
    contiguos (uno por herramienta, cada uno con su propio anchor) — deben
    tratarse como un tramo `band` continuo, no cinco tramos sueltos que cada
    uno exija su propia cobertura desde 0."""
    bc.VISUALS = [_card("v-1", 8.0, 20.0)]
    shots = [_band_shot(8.0, 12.0), _band_shot(12.0, 16.0), _band_shot(16.0, 20.0)]
    bc.check_band_top_covered(shots, 20.0)  # no debe lanzar


def test_cola_del_ultimo_visual_antes_del_fin_del_tramo_band_falla(bc):
    """El hueco de cola de la pieza 15 (0.40s antes de la tesis): el último
    visual de la banda `top` termina antes de que el tramo `band` termine."""
    bc.VISUALS = [_recording("v-rec-5", 8.0, 15.0)]
    with pytest.raises(SystemExit) as ei:
        bc.check_band_top_covered([_band_shot(8.0, 15.4)], 20.0)
    msg = str(ei.value)
    assert "15.00" in msg and "15.40" in msg
