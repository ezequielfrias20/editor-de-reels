import json
import pytest
from edl_schema import EdlError, derive_stages, load_edl


# ── lo que debe pasar ────────────────────────────────────────────────────────
def test_un_edl_minimo_valido_carga(write_edl, edl_min):
    edl = write_edl(edl_min)
    assert len(edl.segments) == 1
    assert edl.segments[0].t(edl.wt) == pytest.approx((0.150, 43.933), abs=1e-2)


def test_el_instante_de_un_evento_sale_de_su_palabra_remapeada(write_edl, edl_min):
    edl_min["segments"][0]["events"] = [
        {"atWord": 34, "type": "CAPTION", "words": [34, 37]}]
    edl = write_edl(edl_min)
    assert edl.segments[0].events[0].t(edl.wt) == pytest.approx(10.293, abs=1e-3)


def test_el_offset_se_suma_sin_cuantizar(write_edl, edl_min):
    edl_min["segments"][0]["events"] = [
        {"atWord": 34, "type": "CAPTION", "words": [34, 37], "offset": -0.08}]
    edl = write_edl(edl_min)
    assert edl.segments[0].events[0].t(edl.wt) == pytest.approx(10.213, abs=1e-3)


def test_offset_que_adelanta_demasiado_falla(write_edl, edl_min, problems_of):
    edl_min["segments"][0]["events"] = [
        {"atWord": 34, "type": "CAPTION", "words": [34, 37], "offset": -0.4}]
    assert "adelanta el guion" in problems_of(edl_min)


# ── fingerprint ─────────────────────────────────────────────────────────────
def test_fingerprint_que_no_cuadra_falla(write_edl, edl_min, problems_of):
    edl_min["transcript"]["fingerprint"] = "sha256:0000"
    assert "fingerprint" in problems_of(edl_min)


def test_apuntar_al_rough_falla(write_edl, edl_min, problems_of):
    edl_min["transcript"]["words"] = "transcripts/10-rough.json"
    assert "fingerprint" in problems_of(edl_min)


def test_falta_cuts_falla(fixtures_root, edl_min, tmp_path, project_root):
    del edl_min["transcript"]["cuts"]
    p = tmp_path / "edl.json"
    p.write_text(json.dumps(edl_min, ensure_ascii=False))
    with pytest.raises(EdlError, match="cuts"):
        load_edl(p, fixtures_root)


# ── cobertura y contigüidad ─────────────────────────────────────────────────
def test_los_segmentos_deben_cubrir_todas_las_palabras(write_edl, edl_min, problems_of):
    edl_min["segments"][0]["words"] = [0, 100]
    assert "no cubren" in problems_of(edl_min)


def test_hueco_entre_segmentos_falla(write_edl, edl_min, problems_of):
    edl_min["segments"] = [dict(edl_min["segments"][0], words=[0, 13]),
                           dict(edl_min["segments"][0], words=[20, 130])]
    assert "hueco" in problems_of(edl_min)


def test_solape_entre_segmentos_falla(write_edl, edl_min, problems_of):
    edl_min["segments"] = [dict(edl_min["segments"][0], words=[0, 20]),
                           dict(edl_min["segments"][0], words=[13, 130])]
    assert "solap" in problems_of(edl_min)


# ── captions y keywords ─────────────────────────────────────────────────────
def test_caption_fuera_del_segmento_falla(write_edl, edl_min, problems_of):
    edl_min["segments"] = [
        dict(edl_min["segments"][0], words=[0, 13],
             events=[{"atWord": 0, "type": "CAPTION", "words": [0, 40]}]),
        dict(edl_min["segments"][0], words=[14, 130], events=[])]
    assert "fuera del segmento" in problems_of(edl_min)


def test_keyword_fuera_de_todo_caption_falla(write_edl, edl_min, problems_of):
    edl_min["segments"][0]["events"] = [
        {"atWord": 0,  "type": "CAPTION", "words": [0, 4]},
        {"atWord": 12, "type": "KEYWORD", "words": [12, 13]}]
    assert "keyword" in problems_of(edl_min)


def test_keyword_dentro_de_su_caption_pasa(write_edl, edl_min):
    edl_min["segments"][0]["events"] = [
        {"atWord": 11, "type": "CAPTION", "words": [11, 13]},
        {"atWord": 12, "type": "KEYWORD", "words": [12, 13]}]
    assert len(write_edl(edl_min).segments[0].events) == 2


def test_caption_prohibido_en_kinetic_type(write_edl, edl_min, problems_of):
    edl_min["segments"][0].update(sceneType="KINETIC_TYPE",
                                  representationType="OBJECT", camera="OFF")
    assert "KINETIC_TYPE" in problems_of(edl_min)


# ── reason y representationType ─────────────────────────────────────────────
def test_reason_ausente_falla(write_edl, edl_min, problems_of):
    del edl_min["segments"][0]["reason"]
    assert "reason" in problems_of(edl_min)


def test_reason_que_repite_el_intent_falla(write_edl, edl_min, problems_of):
    edl_min["segments"][0]["reason"] = edl_min["segments"][0]["semanticIntent"]
    assert "repite" in problems_of(edl_min)


def test_motion_stage_sin_representation_type_falla(write_edl, edl_min, problems_of):
    edl_min["segments"][0].update(sceneType="MOTION_STAGE", camera="OFF")
    assert "representationType" in problems_of(edl_min)


def test_a_roll_no_necesita_representation_type(write_edl, edl_min):
    assert write_edl(edl_min).segments[0].representation_type is None


# ── instancias ──────────────────────────────────────────────────────────────
def test_object_in_duplicado_en_el_mismo_stage_falla(write_edl, edl_min, problems_of, stage_edl):
    data = stage_edl(edl_min, [
        {"atWord": 0,  "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "center"},
        {"atWord": 10, "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "center"}])
    assert "ya existe" in problems_of(data)


def test_object_state_sobre_instancia_inexistente_falla(write_edl, edl_min, problems_of, stage_edl):
    data = stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_STATE", "instanceId": "fantasma",
         "state": {"time": "19:00"}}])
    assert "no existe" in problems_of(data)


def test_object_state_tras_exit_falla(write_edl, edl_min, problems_of, stage_edl):
    data = stage_edl(edl_min, [
        {"atWord": 0,  "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "center"},
        {"atWord": 5,  "type": "OBJECT_EXIT", "instanceId": "c"},
        {"atWord": 10, "type": "OBJECT_STATE", "instanceId": "c",
         "state": {"time": "19:00"}}])
    assert "retirada" in problems_of(data)


def test_stage_clear_libera_los_instance_id(write_edl, edl_min, stage_edl):
    data = stage_edl(edl_min, [
        {"atWord": 0,  "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "center"},
        {"atWord": 5,  "type": "STAGE_CLEAR"},
        {"atWord": 10, "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "center"}])
    assert len(write_edl(data).segments[0].events) == 3


def test_slot_inexistente_falla(write_edl, edl_min, problems_of, stage_edl):
    """Activado por tokens.SLOTS (Tarea 5): un objeto puede caer dentro de la
    interfaz de la plataforma y hasta ahora nada lo comprobaba."""
    data = stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "orbit-99"}])
    assert "no existe" in problems_of(data)


# ── assets ──────────────────────────────────────────────────────────────────
def test_asset_semantico_sin_resolver_falla(write_edl, edl_min, problems_of, stage_edl):
    data = stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "asset": "clock",
         "instanceId": "c", "slot": "center"}])
    assert "sin resolver" in problems_of(data)


def test_asset_sin_version_falla(write_edl, edl_min, problems_of, stage_edl):
    data = stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "asset": "object:clock",
         "instanceId": "c", "slot": "center"}])
    assert "versión" in problems_of(data)


def test_asset_resuelto_y_versionado_pasa(write_edl, edl_min, stage_edl):
    data = stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "center"}])
    assert write_edl(data).segments[0].events[0].asset == "object:clock@1"


# ── transiciones ────────────────────────────────────────────────────────────
def test_transition_out_en_el_ultimo_segmento_falla(write_edl, edl_min, problems_of):
    edl_min["segments"][0]["transitionOut"] = "BLUR_WIPE"
    assert "último segmento" in problems_of(edl_min)


def test_transiciones_en_conflicto_en_un_limite_fallan(write_edl, edl_min, problems_of):
    edl_min["segments"] = [
        dict(edl_min["segments"][0], words=[0, 13], transitionOut="BLUR_WIPE"),
        dict(edl_min["segments"][0], words=[14, 130], transitionIn="DIAGONAL_WIPE")]
    assert "conflicto" in problems_of(edl_min)


def test_match_cut_sin_instancia_compartida_falla(write_edl, edl_min, problems_of):
    edl_min["segments"] = [
        dict(edl_min["segments"][0], words=[0, 13]),
        dict(edl_min["segments"][0], words=[14, 130],
             transitionIn="OBJECT_MATCH_CUT")]
    assert "OBJECT_MATCH_CUT" in problems_of(edl_min)


def test_match_cut_sin_object_state_falla(write_edl, edl_min, problems_of):
    base = {"semanticIntent": "el reloj", "sceneType": "MOTION_STAGE",
            "representationType": "OBJECT", "camera": "OFF",
            "reason": "un match cut que no muta nada"}
    edl_min["segments"] = [
        dict(base, words=[0, 30], transitionIn="CUT", events=[
            {"atWord": 18, "type": "OBJECT_IN", "asset": "object:clock@1",
             "instanceId": "clock-main", "slot": "center",
             "state": {"time": "11:00"}}]),
        dict(base, words=[31, 130], transitionIn="OBJECT_MATCH_CUT", events=[])]
    assert "no las muta" in problems_of(edl_min)


def test_match_cut_valido_pasa(write_edl, edl_min):
    """El caso del reloj: la instancia vive a ambos lados y el entrante la muta."""
    base = {"semanticIntent": "el reloj", "sceneType": "MOTION_STAGE",
            "representationType": "OBJECT", "camera": "OFF",
            "reason": "probar un match cut legítimo"}
    edl_min["segments"] = [
        dict(base, words=[0, 30], transitionIn="CUT", events=[
            {"atWord": 18, "type": "OBJECT_IN", "asset": "object:clock@1",
             "instanceId": "clock-main", "slot": "center",
             "state": {"time": "11:00"}}]),
        dict(base, words=[31, 130], transitionIn="OBJECT_MATCH_CUT",
             representationType="STATE_CHANGE", events=[
            {"atWord": 34, "type": "OBJECT_STATE", "instanceId": "clock-main",
             "state": {"time": "19:00"}, "preset": "hands-sweep"}])]
    assert write_edl(edl_min).segments[1].transition_in == "OBJECT_MATCH_CUT"


# ── overrides ───────────────────────────────────────────────────────────────
def test_override_fuera_de_whitelist_falla(write_edl, edl_min, problems_of):
    edl_min["plan_overrides"] = [
        {"target": "visuals[stage-a].zoom", "value": 2, "why": "porque"}]
    assert "whitelist" in problems_of(edl_min)


def test_override_sin_why_falla(write_edl, edl_min, problems_of):
    edl_min["plan_overrides"] = [
        {"target": "visuals[stage-a].cap_top", "value": 1180}]
    assert "why" in problems_of(edl_min)


def test_override_valido_pasa(write_edl, edl_min):
    edl_min["plan_overrides"] = [
        {"target": "visuals[stage-a].cap_top", "value": 1180,
         "why": "el bloque de dos líneas se metía 46 px en la zona segura"}]
    assert len(write_edl(edl_min).overrides) == 1


# ── draft ───────────────────────────────────────────────────────────────────
def test_un_draft_es_rechazado(fixtures_root, edl_min, tmp_path, project_root):
    p = tmp_path / "edl.draft.json"
    p.write_text(json.dumps(edl_min, ensure_ascii=False))
    with pytest.raises(EdlError, match="draft"):
        load_edl(p, fixtures_root)


# ── stages ──────────────────────────────────────────────────────────────────
class _S:
    def __init__(self, st):
        self.scene_type = st


def test_los_segmentos_contiguos_de_stage_forman_uno_solo():
    segs = [_S("A_ROLL"), _S("MOTION_STAGE"), _S("KINETIC_TYPE"),
            _S("MOTION_STAGE"), _S("A_ROLL"), _S("MOTION_STAGE")]
    assert [(s.first, s.last) for s in derive_stages(segs)] == [(1, 3), (5, 5)]


def test_una_pieza_sin_stages_no_deriva_ninguno():
    assert derive_stages([_S("A_ROLL"), _S("CTA")]) == ()


# ── el error junta todos los problemas ──────────────────────────────────────
def test_todos_los_problemas_se_reportan_juntos(write_edl, edl_min):
    del edl_min["segments"][0]["reason"]
    edl_min["transcript"]["fingerprint"] = "sha256:0000"
    with pytest.raises(EdlError) as ei:
        write_edl(edl_min)
    assert len(ei.value.problems) >= 2
