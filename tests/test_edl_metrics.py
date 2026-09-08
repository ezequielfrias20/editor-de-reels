from pathlib import Path

import pytest
from edl_metrics import measure, run_gates
from edl_schema import Edl, Segment


@pytest.fixture(scope="module")
def m10(edl10):
    return measure(edl10)


def _synthetic_edl(wt, segments):
    """Un EDL sintético sobre las palabras REALES de la pieza 10 (`w10`,
    inmutable), pero con segmentos inventados. Las dos pruebas de abajo
    verifican una propiedad GENERAL de `measure()`, no algo de la pieza 10
    en sí — anclarlas a `edl10` las rompía cada vez que la pieza avanzaba de
    tarea en tarea (dejó de ser toda A_ROLL en la Tarea 6)."""
    return Edl(src=Path("synthetic"), fmt="REEL", piece=0,
              style_profile="motion-explainer", wt=wt, segments=tuple(segments),
              overrides=(), voice_gain=0.7, music={}, planner={})


# ── presencia del presentador ───────────────────────────────────────────────
def test_una_pieza_toda_a_roll_da_presencia_1(w10):
    n = len(w10.words)
    seg = Segment(words=(0, n - 1), semantic_intent="x", scene_type="A_ROLL",
                  reason="sintético: toda la pieza en un solo A_ROLL")
    assert measure(_synthetic_edl(w10, [seg]))["presenter_share"] == pytest.approx(1.0)


def test_ui_demo_sale_del_denominador(w10):
    """El caso del reel de ChatGPT: 15 s de demo legítima no deben obligar a
    volver al presentador para cuadrar un porcentaje."""
    n = len(w10.words)
    mid = n // 2
    segs = [
        Segment(words=(0, mid), semantic_intent="a", scene_type="A_ROLL",
                reason="sintético: mitad presentador"),
        Segment(words=(mid + 1, n - 1), semantic_intent="b", scene_type="UI_DEMO",
                representation_type="INTERFACE", camera="OFF",
                reason="sintético: mitad demo de producto"),
    ]
    m = measure(_synthetic_edl(w10, segs))
    assert m["presenter_share"] == pytest.approx(1.0)
    assert m["presenter_share_raw"] < 1.0


# ── ritmo ───────────────────────────────────────────────────────────────────
def test_los_captions_solos_no_satisfacen_el_gate_macro(m10):
    """La razón de existir de los dos niveles: si micro y macro fueran lo
    mismo, un plano fijo de 15 s pasaría por cambiar de subtítulo."""
    assert m10["max_macro_gap"] > m10["max_micro_gap"]


def test_el_hueco_macro_de_la_pieza_10_cabe_en_el_gate(m10):
    assert m10["max_macro_gap"] <= 4.5, (
        f"hay {m10['max_macro_gap']:.2f} s sin un cambio macro")


def test_un_segmento_con_hold_no_cuenta_para_el_gate(edl10):
    """El brief pide quietud antes del clímax; una quietud deliberada debe
    estar ESCRITA, no colada en silencio."""
    from edl_schema import Edl, Segment
    segs = list(edl10.segments)
    old = segs[7]
    segs[7] = Segment(**{**old.__dict__, "events": (), "hold": True})
    edl = Edl(**{**edl10.__dict__, "segments": tuple(segs)})
    assert measure(edl)["max_macro_gap"] <= 4.5


# ── el motor genérico ───────────────────────────────────────────────────────
def test_un_gate_max_superado_produce_un_finding():
    style = {"gates": [{"metric": "punch_zoom_count", "max": 2, "severity": "warn"}]}
    fs = run_gates({"punch_zoom_count": 5}, style)
    assert len(fs) == 1 and fs[0].severity == "warn" and "5" in fs[0].message


def test_una_banda_produce_warn_o_fail_segun_lo_lejos_que_este():
    style = {"gates": [{"metric": "presenter_share", "in": [0.45, 0.60],
                        "warn_in": [0.35, 0.70], "fail_in": [0.20, 0.85]}]}
    assert run_gates({"presenter_share": 0.50}, style) == []
    assert run_gates({"presenter_share": 0.32}, style)[0].severity == "warn"
    assert run_gates({"presenter_share": 0.10}, style)[0].severity == "fail"


def test_un_perfil_sin_gates_no_produce_nada():
    assert run_gates({"punch_zoom_count": 99}, {"gates": []}) == []


def test_una_metrica_desconocida_en_el_perfil_falla_claro():
    """Un gate sobre una métrica que nadie calcula es un typo silencioso."""
    with pytest.raises(KeyError, match="metrica_inventada"):
        run_gates({"punch_zoom_count": 1},
                  {"gates": [{"metric": "metrica_inventada", "max": 1}]})


def test_anadir_un_gate_no_toca_el_compilador():
    """El requisito arquitectónico: umbrales y severidad son DATOS."""
    style = {"gates": [{"metric": "theme_change_count", "max": 0, "severity": "fail"}]}
    assert run_gates({"theme_change_count": 1}, style)[0].severity == "fail"
