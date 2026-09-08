import json
import pytest
from edl_compile import compile_edl, load_style, q, write_plan
from edl_schema import load_edl


# ── cuantización ────────────────────────────────────────────────────────────
def test_q_cuantiza_a_la_rejilla_de_30fps():
    assert q(10.293) == 10.3          # 308.79 -> 309 -> 309/30
    assert q(4.124) == 4.1333
    assert q(0.150) == 0.1333


# ── forma del plan ──────────────────────────────────────────────────────────
def test_el_plan_tiene_las_claves_que_build_composition_espera(plan10):
    for k in ("format", "keywords", "music", "voice_gain",
              "shots", "cards", "visuals", "sfx"):
        assert k in plan10, f"falta '{k}'"
    assert plan10["format"] == "REEL"
    assert plan10["voice_gain"] == 0.70


def test_hay_un_encuadre_por_segmento_mas_los_eventos_camera(plan10):
    # 9 segmentos + 2 eventos CAMERA
    assert len(plan10["shots"]) == 11


def test_los_encuadres_van_ordenados_y_empiezan_en_cero(plan10):
    ats = [s["at"] for s in plan10["shots"]]
    assert ats == sorted(ats)
    assert ats[0] == 0.0, "el primer encuadre arranca la pieza, no su primera palabra"


def test_la_camara_se_traduce_por_la_escalera_del_perfil(plan10):
    # Segmento 0: CLOSE -> 1.20
    assert plan10["shots"][0]["zoom"] == 1.20
    assert plan10["shots"][0]["kind"] == "full"


def test_el_evento_camera_emite_su_propio_encuadre(plan10, edl10):
    # El CAMERA de la palabra 97 baja a MEDIUM a mitad del segmento 7.
    t = q(edl10.wt.at(97))
    sh = next(s for s in plan10["shots"] if s["at"] == t)
    assert sh["zoom"] == 1.12


def test_las_keywords_salen_de_los_eventos_keyword(plan10):
    ks = plan10["keywords"]
    assert ks == sorted(set(ks)), "ordenadas y sin repetir, para que el plan sea estable"
    assert "CONTESTÓ" in ks and "PRIMERO" in ks


def test_el_minimo_no_emite_visuales_ni_efectos(plan10):
    assert plan10["visuals"] == [] and plan10["sfx"] == [] and plan10["cards"] == []


# ── determinismo ────────────────────────────────────────────────────────────
def test_compilar_dos_veces_da_el_mismo_dict(edl10, style):
    assert compile_edl(edl10, style) == compile_edl(edl10, style)


def test_el_json_escrito_es_byte_identico(plan10, tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    write_plan(plan10, a)
    write_plan(plan10, b)
    assert a.read_bytes() == b.read_bytes()


def test_el_json_va_con_claves_ordenadas(plan10, tmp_path):
    p = tmp_path / "p.json"
    write_plan(plan10, p)
    raw = p.read_text()
    assert raw.index('"cards"') < raw.index('"format"') < raw.index('"shots"')
    assert raw.endswith("\n")


def test_ningun_tiempo_del_plan_esta_sin_cuantizar(plan10):
    for sh in plan10["shots"]:
        assert sh["at"] == q(sh["at"]), f"{sh} sin cuantizar"


# ── el compilador no improvisa ──────────────────────────────────────────────
def test_un_perfil_inexistente_falla_claro(skill_root):
    with pytest.raises(FileNotFoundError, match="motion-explainer|no-existe"):
        load_style("no-existe", skill_root)
