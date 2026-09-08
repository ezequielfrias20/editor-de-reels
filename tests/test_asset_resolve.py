"""Asset Resolver — Tarea 12. Reutilizar antes que generar, en orden estricto,
y anotando por qué cuando baja de nivel.
"""
import pytest
from asset_resolve import PRIORIDAD, Resolution, asset_hash, resolve, resolve_edl


# ── prioridad ────────────────────────────────────────────────────────────────
def test_la_prioridad_es_reutilizar_antes_que_generar(manifest):
    r = resolve("clock", {}, manifest)
    assert r.ref == "object:clock@1" and r.resolved_via == "library"


def test_solo_baja_de_nivel_si_el_de_arriba_no_sirve(manifest):
    r = resolve("recepcion-de-clinica", {}, manifest)
    assert r.resolved_via in ("generated", "broll")
    assert r.reason, "bajar de nivel sin anotar por qué es lo que hace la librería inauditable"


def test_una_referencia_resuelta_siempre_lleva_version(manifest):
    for s in ("clock", "phone", "bottleneck"):
        assert "@" in resolve(s, {}, manifest).ref


def test_los_seis_objetos_de_la_pieza_10_resuelven_a_library(manifest):
    for s in ("clock", "dental-chair", "phone", "card-payment", "instagram", "bottleneck"):
        r = resolve(s, {}, manifest)
        assert r.resolved_via == "library", s
        assert r.ref == f"object:{s}@1"


def test_el_orden_de_prioridad_es_el_documentado():
    assert PRIORIDAD == ("library", "configurable", "recording", "generated", "broll")


# ── hash e inmutabilidad ───────────────────────────────────────────────────
def test_el_hash_detecta_que_alguien_edito_una_version_inmutable(manifest):
    """@1 es inmutable: rediseñar el reloj crea @2. Si alguien edita @1, los
    renders históricos cambian en silencio."""
    real = asset_hash("object:clock@1", manifest)
    assert real == manifest["assets"]["object:clock@1"]["hash"]


def test_los_seis_hashes_del_manifest_estan_al_dia(manifest):
    """Lo que corre `manifest-sync.py`: si esto falla, alguien tocó
    `objects.py` sin subir de versión."""
    for ref, entry in manifest["assets"].items():
        assert asset_hash(ref, manifest) == entry["hash"], ref


def test_un_hash_distinto_no_engana_a_asset_hash(manifest):
    """El hash se RECALCULA del código, nunca se copia del manifest — si un
    manifest viniera con un hash falso, `asset_hash` lo ignoraría igual."""
    manipulado = {"assets": {**manifest["assets"],
                            "object:clock@1": {**manifest["assets"]["object:clock@1"],
                                              "hash": "sha256:no-es-el-real"}}}
    assert asset_hash("object:clock@1", manipulado) != "sha256:no-es-el-real"
    assert asset_hash("object:clock@1", manipulado) == manifest["assets"]["object:clock@1"]["hash"]


def test_un_ref_fuera_del_manifest_falla_claro(manifest):
    with pytest.raises(KeyError, match="inventado"):
        asset_hash("object:inventado@1", manifest)


def test_hashear_un_kind_sin_implementar_falla_claro():
    m = {"assets": {"recording:algo@1": {"hash": "sha256:x", "kind": "recording"}}}
    with pytest.raises(ValueError, match="recording"):
        asset_hash("recording:algo@1", m)


# ── validación CORE (§ edl_schema) ───────────────────────────────────────────
def test_un_asset_que_no_esta_en_el_manifest_falla_en_core(write_edl, edl_min, stage_edl,
                                                            problems_of):
    data = stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "asset": "object:inventado@1",
         "instanceId": "c", "slot": "center"}])
    assert "manifest" in problems_of(data)


def test_un_asset_con_hash_manipulado_falla_en_core(write_edl, edl_min, stage_edl,
                                                     problems_of, project_root):
    """Editar `objects.py` sin subir la versión del `@n` tiene que fallar en
    CORE, no solo en `manifest-sync.py` — si alguien commitea el código
    tocado y el manifest viejo, el EDL no debe compilar."""
    import json
    manifest_path = project_root / "assets" / "manifest.json"
    real = json.loads(manifest_path.read_text())
    falso = {**real, "assets": {**real["assets"],
                                "object:clock@1": {**real["assets"]["object:clock@1"],
                                                   "hash": "sha256:manipulado"}}}
    manifest_path.write_text(json.dumps(falso))
    try:
        data = stage_edl(edl_min, [
            {"atWord": 0, "type": "OBJECT_IN", "asset": "object:clock@1",
             "instanceId": "c", "slot": "center", "state": {"time": "12:00"}}])
        assert "hash" in problems_of(data) or "cambió" in problems_of(data).lower()
    finally:
        manifest_path.write_text(json.dumps(real, ensure_ascii=False, indent=2,
                                            sort_keys=True) + "\n")


def test_un_asset_bien_resuelto_no_produce_problemas(write_edl, edl_min, stage_edl):
    data = stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "center", "state": {"time": "12:00"}}])
    write_edl(data)  # no debe lanzar EdlError


# ── resolve_edl ────────────────────────────────────────────────────────────
def test_resolve_edl_rellena_asset_resolvedvia_y_reason(manifest, edl_min, stage_edl):
    draft = stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "semantic": "clock",
         "instanceId": "c", "slot": "center"}])
    out = resolve_edl(draft, manifest)
    ev = out["segments"][0]["events"][0]
    assert ev["asset"] == "object:clock@1"
    assert ev["resolvedVia"] == "library"
    assert ev["resolveReason"]
    assert "semantic" not in ev


def test_resolve_edl_no_toca_un_asset_ya_resuelto(manifest, edl_min, stage_edl):
    draft = stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "asset": "object:phone@1",
         "instanceId": "c", "slot": "orbit-1"}])
    out = resolve_edl(draft, manifest)
    ev = out["segments"][0]["events"][0]
    assert ev["asset"] == "object:phone@1"
    assert "resolvedVia" not in ev


def test_resolve_edl_no_muta_el_borrador_original(manifest, edl_min, stage_edl):
    draft = stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "semantic": "clock",
         "instanceId": "c", "slot": "center"}])
    resolve_edl(draft, manifest)
    assert draft["segments"][0]["events"][0].get("asset") is None
    assert draft["segments"][0]["events"][0]["semantic"] == "clock"


# ── el informe de compilación ────────────────────────────────────────────────
def test_el_informe_registra_manifest_version_y_hashes(edl10, style, manifest):
    from edl_compile import compile_report
    r = compile_report(edl10, style, manifest)
    assert r["manifest_version"] == manifest["manifest_version"]
    assert all(h.startswith("sha256:") for h in r["assets_used"].values())


def test_el_informe_de_la_pieza_10_lista_los_seis_objetos(edl10, style, manifest):
    from edl_compile import compile_report
    r = compile_report(edl10, style, manifest)
    assert set(r["assets_used"]) == {
        "object:clock@1", "object:dental-chair@1", "object:phone@1",
        "object:card-payment@1", "object:instagram@1", "object:bottleneck@1"}
