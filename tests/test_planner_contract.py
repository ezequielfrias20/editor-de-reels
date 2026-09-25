"""El Creative Planner — Tarea 13, el último eslabón y el único no
determinista. El test que importa no es del Planner, es del PIPELINE: que
lo que produce pase por exactamente el mismo CORE que un EDL escrito a
mano. Que sea no determinista es seguro precisamente porque nada de lo
que produce se acepta sin validar.
"""
import json
from pathlib import Path

import pytest
from edl_schema import load_edl


def test_un_draft_del_planner_pasa_por_el_mismo_core(fixtures_root, tmp_path, project_root):
    """El Planner es un CANDIDATO, no una autoridad."""
    from asset_resolve import load_manifest, resolve_edl
    draft = json.loads((fixtures_root / "videos" / "10" / "edl.draft.json").read_text())
    resuelto = resolve_edl(draft, load_manifest(project_root / "assets" / "manifest.json"))
    p = tmp_path / "edl.json"
    p.write_text(json.dumps(resuelto, ensure_ascii=False))
    load_edl(p, fixtures_root)          # no lanza -> el draft era ejecutable


def test_el_draft_no_trae_ningun_asset_ya_resuelto(fixtures_root, project_root):
    """Si trajera `asset` resuelto en vez de `semantic`, no probaría nada:
    el Resolver no habría tenido nada que hacer."""
    draft = json.loads((fixtures_root / "videos" / "10" / "edl.draft.json").read_text())
    semanticos = [ev for seg in draft["segments"] for ev in seg["events"]
                 if ev.get("type") == "OBJECT_IN"]
    assert len(semanticos) == 6
    assert all("semantic" in ev and "asset" not in ev for ev in semanticos)


def test_el_draft_declara_metadata_de_planner_no_vacia(fixtures_root, project_root):
    draft = json.loads((fixtures_root / "videos" / "10" / "edl.draft.json").read_text())
    assert draft["planner"]["generatedAt"]
    assert draft["planner"]["styleProfile"] == "motion-explainer"


# ── creative_hash ────────────────────────────────────────────────────────────
def test_generated_at_no_entra_en_el_hash_creativo(fixtures_root, project_root):
    """Si entrara, dos corridas del mismo EDL darían hashes distintos y la
    prueba de determinismo sería inútil."""
    from edl_compile import creative_hash
    a = json.loads((fixtures_root / "videos" / "10" / "edl.json").read_text())
    b = json.loads(json.dumps(a))
    b.setdefault("planner", {})["generatedAt"] = "2030-01-01T00:00:00Z"
    assert creative_hash(a) == creative_hash(b)


def test_el_hash_creativo_ignora_las_claves_subrayadas(fixtures_root, project_root):
    from edl_compile import creative_hash
    a = json.loads((fixtures_root / "videos" / "10" / "edl.json").read_text())
    b = json.loads(json.dumps(a))
    b["segments"][0]["_spokenText"] = "lo que sea"
    assert creative_hash(a) == creative_hash(b)


def test_el_hash_creativo_SI_cambia_con_una_decision_editorial(fixtures_root, project_root):
    from edl_compile import creative_hash
    a = json.loads((fixtures_root / "videos" / "10" / "edl.json").read_text())
    b = json.loads(json.dumps(a))
    b["segments"][0]["camera"] = "WIDE"
    assert creative_hash(a) != creative_hash(b)


def test_el_hash_creativo_es_determinista_ante_el_orden_de_claves():
    """`sort_keys` en la canonicalización: dos dicts con las mismas claves en
    orden distinto son la MISMA decisión creativa."""
    from edl_compile import creative_hash
    a = {"b": 1, "a": 2}
    b = {"a": 2, "b": 1}
    assert creative_hash(a) == creative_hash(b)


def test_el_hash_creativo_ignora_subrayadas_en_cualquier_profundidad():
    from edl_compile import creative_hash
    a = {"segments": [{"events": [{"type": "CAPTION"}]}]}
    b = {"segments": [{"events": [{"type": "CAPTION", "_note": "comentario"}]}]}
    assert creative_hash(a) == creative_hash(b)


def test_el_hash_creativo_no_muta_el_dict_de_entrada():
    from edl_compile import creative_hash
    a = {"planner": {"generatedAt": "x", "plannerVersion": "0.1.0"}, "_c": 1}
    antes = json.loads(json.dumps(a))
    creative_hash(a)
    assert a == antes


def test_el_hash_creativo_es_un_string_hexadecimal():
    from edl_compile import creative_hash
    h = creative_hash({"a": 1})
    assert isinstance(h, str) and len(h) == 64
    int(h, 16)  # no lanza -> es hex válido


# ── el andamiaje mecánico de edl-plan.py ─────────────────────────────────────
def _load_edl_plan():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "edl_plan", Path(__file__).resolve().parent.parent /
        ".claude" / "skills" / "video-tech-premium" / "scripts" / "edl-plan.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_las_frases_de_la_pieza_10_dan_9_segmentos(w10):
    edl_plan = _load_edl_plan()
    draft = edl_plan.build_draft(w10, 10, "REEL", "motion-explainer", "0.1.0", "draft")
    assert len(draft["segments"]) == 9
    assert draft["segments"][0]["words"] == [0, 13]


def test_el_andamiaje_no_elige_nada_creativo(w10):
    edl_plan = _load_edl_plan()
    draft = edl_plan.build_draft(w10, 10, "REEL", "motion-explainer", "0.1.0", "draft")
    for seg in draft["segments"]:
        assert seg["sceneType"] == "A_ROLL"
        assert "representationType" not in seg
        assert all(e["type"] == "CAPTION" for e in seg["events"])
        assert "revisar" in seg["reason"]


def test_el_andamiaje_pasa_por_core_directamente(fixtures_root, w10, tmp_path, project_root):
    """Sin OBJECT_IN no hace falta ni el Asset Resolver: el andamiaje solo
    A_ROLL/CAPTION tiene que ser ejecutable tal cual sale."""
    edl_plan = _load_edl_plan()
    draft = edl_plan.build_draft(w10, 10, "REEL", "motion-explainer", "0.1.0", "draft")
    p = tmp_path / "edl.json"
    p.write_text(json.dumps(draft, ensure_ascii=False))
    load_edl(p, fixtures_root)


def test_las_frases_cubren_todas_las_palabras_sin_hueco_ni_solape(w10):
    edl_plan = _load_edl_plan()
    segs = edl_plan._sentences(w10.words)
    assert segs[0][0] == 0
    assert segs[-1][1] == len(w10.words) - 1
    for (_, hi), (lo2, _) in zip(segs, segs[1:]):
        assert lo2 == hi + 1
