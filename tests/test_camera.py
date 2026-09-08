"""La escalera adaptativa y el ritmo de cámara — Tarea 8, Step 6.

Dos reglas que no son de gusto sino de física del reescalado:

1. El factor de reescalado al alza es `zoom · canvas_w / src_w`. Por encima de
   ~1.2 el H.264 a 1080 de ancho ablanda la piel de forma visible, así que el
   perfil pide la escalera que quiera y el compilador la RECORTA por la fórmula.
2. Dos cambios de cámara demasiado seguidos son jitter, no jump cut. El hook
   está exento: ahí el atropello es el efecto que se busca.
"""
from pathlib import Path

import pytest
from edl_compile import cap_ladder
from edl_metrics import measure, run_gates
from edl_schema import Edl, Event, Segment

LADDER = {"WIDE": 1.0, "MEDIUM": 1.12, "CLOSE": 1.2}


# ── el tope por resolución ──────────────────────────────────────────────────
def test_fuente_1080_en_lienzo_1080_deja_la_escalera_aprobada():
    assert cap_ladder(LADDER, 1080, 1080, 1.2) == LADDER


def test_el_125_del_brief_queda_descartado_con_fuente_1080():
    """No es una opinión: a 1.25 el reescalado es 1.25× sobre 1080 de ancho."""
    capped = cap_ladder({**LADDER, "CLOSE": 1.25}, 1080, 1080, 1.2)
    assert capped["CLOSE"] == 1.2
    assert capped["WIDE"] == 1.0 and capped["MEDIUM"] == 1.12


def test_fuente_4k_permite_z_2_en_nativo():
    """techo = (2160 / 1080) · 1.2 = 2.40. A z=2.00 el reescalado es 1.00×."""
    capped = cap_ladder({**LADDER, "CLOSE": 2.0}, 2160, 1080, 1.2)
    assert capped["CLOSE"] == 2.0
    assert cap_ladder({"X": 3.0}, 2160, 1080, 1.2)["X"] == pytest.approx(2.4)


def test_una_fuente_por_debajo_del_lienzo_recorta_mas():
    """Fuente 720 en lienzo 1080 ya viene reescalada 1.5×: el techo cae por
    debajo de 1.0 y ni el WIDE se salva."""
    capped = cap_ladder(LADDER, 720, 1080, 1.2)
    assert capped["WIDE"] == pytest.approx(0.8)
    assert capped["CLOSE"] == pytest.approx(0.8)


def test_cap_ladder_no_muta_la_entrada():
    """El perfil se carga una vez y lo comparten todas las piezas. Mutarlo
    haría que compilar dos piezas seguidas diera resultados distintos."""
    original = dict(LADDER, CLOSE=1.25)
    cap_ladder(original, 1080, 1080, 1.2)
    assert original["CLOSE"] == 1.25


# ── el ritmo ────────────────────────────────────────────────────────────────
def _edl(wt, segments):
    return Edl(src=Path("synthetic"), fmt="REEL", piece=0,
               style_profile="motion-explainer", wt=wt, segments=tuple(segments),
               overrides=(), voice_gain=0.7, music={}, planner={})


def _con_camaras(wt, cambios):
    """Un A_ROLL con eventos CAMERA en los índices de palabra dados."""
    n = len(wt.words)
    evs = [Event(type="CAMERA", at_word=w, state={"camera": cam})
           for w, cam in cambios]
    return _edl(wt, [Segment(words=(0, n - 1), semantic_intent="x",
                             scene_type="A_ROLL", camera="WIDE",
                             reason="sintético: ritmo de cámara",
                             events=tuple(evs))])


def test_sin_segundo_cambio_no_hay_hueco_que_medir(w10, style):
    """Una pieza de un solo plano no puede tener jitter. El valor de reserva
    es la duración: 'todo el rato sin volver a cambiar', no cero — cero
    dispararía el gate al revés."""
    m = measure(_con_camaras(w10, []), style)
    assert m["min_camera_gap"] == pytest.approx(w10.duration)
    assert run_gates(m, style) == [] or all(
        f.metric != "min_camera_gap" for f in run_gates(m, style))


def test_dos_cambios_pegados_fuera_del_hook_son_jitter(w10, style):
    """Palabras 57 · 62 · 64, con `remap()` en 18.417 · 19.799 · 20.360 s.

    El hueco menor es 20.360 - 19.799 = **0.561 s**, por debajo del mínimo de
    0.70. Ojo con la tabla del plan: ahí figuran los tiempos ya pasados por
    `q()` (19.8 y 20.3667), y esta métrica NO cuantiza — el ritmo que percibe
    el espectador no depende de a qué frame caiga el corte, y cuantizar aquí
    metería un segundo redondeo fuera del único punto autorizado.
    """
    m = measure(_con_camaras(w10, [(57, "CLOSE"), (62, "WIDE"), (64, "MEDIUM")]),
                style)
    assert m["min_camera_gap"] == pytest.approx(0.561, abs=1e-3)
    fs = [f for f in run_gates(m, style) if f.metric == "min_camera_gap"]
    assert len(fs) == 1 and fs[0].severity == "warn"


def test_el_hook_esta_exento(w10, style):
    """Mismos dos cambios pegados, pero en las palabras 0 (0.1333 s) y 13
    (3.3667 s)... no: el par que importa es dentro del hook. Palabras 0 y 1,
    que caen en los primeros 3 s, no pueden disparar el gate."""
    m = measure(_con_camaras(w10, [(0, "CLOSE"), (1, "WIDE")]), style)
    fs = [f for f in run_gates(m, style) if f.metric == "min_camera_gap"]
    assert fs == [], f"el hook no debería disparar el gate: {m['min_camera_gap']}"


def test_el_gate_de_ritmo_es_warn_no_fail():
    """`run_gates` exige que TODA métrica citada por el perfil esté calculada,
    así que el motor se prueba con un perfil mínimo, no con el completo."""
    solo = {"gates": [{"metric": "min_camera_gap", "min": 0.70,
                       "severity": "warn"}]}
    fs = run_gates({"min_camera_gap": 0.4}, solo)
    assert len(fs) == 1 and fs[0].severity == "warn"
    assert run_gates({"min_camera_gap": 0.7}, solo) == []


def test_el_perfil_aprobado_lleva_el_gate_de_ritmo(style):
    g = next(g for g in style["gates"] if g["metric"] == "min_camera_gap")
    assert g["min"] == 0.70 and g["severity"] == "warn"
    assert style["camera"]["hook_exempt_until"] == 3.0


def test_measure_sin_style_sigue_funcionando(edl10):
    """La firma vieja no se rompe: `measure(edl)` es lo que llaman los tests
    de la Tarea 4 y lo que documenta el plan."""
    assert "min_camera_gap" in measure(edl10)
