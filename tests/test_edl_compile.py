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
    # 10 segmentos (la Tarea 11 partió [73, 87] en un A_ROLL de rebote y un
    # MOTION_STAGE) + 2 eventos CAMERA que sobreviven (palabras 98 y 121).
    # El CAMERA de la palabra 65 lo quitó la Tarea 9 al convertir [57, 72]
    # en MOTION_STAGE; el de la palabra 80 lo quitó la Tarea 11 al pasar a
    # ser el ARRANQUE del nuevo segmento MOTION_STAGE [80, 87] — un corte de
    # cámara mid-stage no tiene sentido, la misma razón las dos veces.
    assert len(plan10["shots"]) == 12


def test_los_encuadres_van_ordenados_y_empiezan_en_cero(plan10):
    ats = [s["at"] for s in plan10["shots"]]
    assert ats == sorted(ats)
    assert ats[0] == 0.0, "el primer encuadre arranca la pieza, no su primera palabra"


def test_la_camara_se_traduce_por_la_escalera_del_perfil(plan10):
    # Segmento 0: CLOSE -> 1.20
    assert plan10["shots"][0]["zoom"] == 1.20
    assert plan10["shots"][0]["kind"] == "full"


def test_el_evento_camera_emite_su_propio_encuadre(plan10, edl10):
    # El CAMERA de la palabra 98 ("es", inicio de la segunda cláusula) baja
    # a MEDIUM a mitad del segmento 7.
    t = q(edl10.wt.at(98))
    sh = next(s for s in plan10["shots"] if s["at"] == t)
    assert sh["zoom"] == 1.12


def test_las_keywords_salen_de_los_eventos_keyword(plan10):
    ks = plan10["keywords"]
    assert ks == sorted(set(ks)), "ordenadas y sin repetir, para que el plan sea estable"
    assert "CONTESTÓ" in ks and "PRIMERO" in ks


def test_cards_sigue_vacio_la_pieza_10_no_usa_tarjetas(plan10):
    assert plan10["cards"] == []


def test_sfx_ya_no_esta_vacio_desde_la_tarea_10(plan10):
    # cards nunca se llena en la pieza 10; visuals ya NO está vacío desde la
    # Tarea 6 — ver test_un_stage_sale_como_UNA_... — y sfx desde la Tarea 10.
    # Eran 5 en la Tarea 10; la Tarea 11 añade el sexto, la entrada del embudo.
    assert len(plan10["sfx"]) == 6
    for start, name, trim, why in plan10["sfx"]:
        assert isinstance(start, float) and isinstance(name, str)
        assert isinstance(trim, float) and isinstance(why, str)


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


# ── Tarea 6: el reloj y el stage como una sola entrada ──────────────────────
def test_un_stage_sale_como_UNA_entrada_de_visuals(plan10):
    """La serie contigua entera, no una entrada por segmento. El `end` es el
    borde de la VENTANA (inicio del siguiente segmento, 11.3333), no el fin
    del span de palabras (11.2): usar el span dejaría un hueco de 0.11 s entre
    el fin del stage y el próximo encuadre — el mismo bug que gotcha #6
    documenta."""
    stages = [v for v in plan10["visuals"] if v["mock"][0] == "motion_stage"]
    v = stages[0]
    assert v["start"] == 4.1333 and v["end"] == 11.3333


def test_stages_no_contiguos_son_entradas_de_visuals_separadas(plan10):
    """La Tarea 9 añade el stage de acumulación (palabras 57-72), separado
    del reloj (14-37) por dos segmentos A_ROLL de por medio — `derive_stages`
    tiene que verlos como series MAXIMALES distintas, no fundirlos en una."""
    stages = [v for v in plan10["visuals"] if v["mock"][0] == "motion_stage"]
    assert len(stages) == 3
    assert stages[1]["id"] == "stage-b"
    assert stages[1]["start"] == 18.4333 and stages[1]["end"] == 23.8667


def test_el_cuello_de_botella_es_un_tercer_stage_separado(plan10):
    """La Tarea 11 añade el embudo (palabras 80-87). Un rebote A_ROLL de
    73-79 lo separa del stage de acumulación — sin él, `derive_stages` los
    fundiría en uno y el sillón seguiría vivo cuando el embudo entra."""
    stages = [v for v in plan10["visuals"] if v["mock"][0] == "motion_stage"]
    assert stages[2]["id"] == "stage-c"
    assert stages[2]["start"] == 26.4667


def test_el_off_se_retrasa_por_el_fade_in(plan10):
    """Gotcha #6: un `off` que empieza a la vez que el takeover deja el frame
    vacío durante el fundido. fade_in se suma al start SIN cuantizar
    (4.124 + 0.22 = 4.344) y se cuantiza una sola vez -> 4.3333, no
    4.1333 + 0.22 cuantizado por separado."""
    off = next(s for s in plan10["shots"] if s["kind"] == "off")
    assert off["at"] == 4.3333


def test_el_estado_del_reloj_se_emite_como_angulos(plan10):
    v = next(v for v in plan10["visuals"] if v["mock"][0] == "motion_stage")
    op = next(o for o in v["mock"][1]["at"] if o["id"] == "clock-main")
    assert op["t"] == 10.3 and op["hour"] == 570 and op["minute"] == 2880
