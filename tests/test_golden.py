"""El hito — Tarea 11. La pieza 10 renderiza de punta a punta desde su
`edl.json`, y el `plan.json` que produce queda congelado en un golden file.

Por qué un golden y no solo los tests unitarios de cada tarea: los tests
unitarios verifican PIEZAS del compilador (`_shots`, `_visuals`, `resolve_sfx`)
por separado. Este test verifica el TODO — que ningún cambio futuro en
`objects.py`, `tokens.py` o `edl_compile.py` mueva un slot, un color o un
tiempo de la pieza 10 sin que alguien lo vea en el diff. Sin él, ese tipo de
regresión se descubre tres piezas después, cuando ya no se recuerda qué la
causó.
"""
import json

from edl_compile import compile_edl


def test_el_plan_de_la_pieza_10_no_ha_cambiado(edl10, style, project_root):
    esperado = json.loads((project_root / "tests" / "golden" / "10.plan.json").read_text())
    # `sfx` sale de `resolve_sfx()` como TUPLAS, a propósito (es lo que prueba
    # su propio test unitario). El golden, leído de JSON, las trae como
    # listas — comparar contra ese mismo redondeo por JSON es lo correcto:
    # es exactamente lo que `write_plan()` escribe a disco.
    obtenido = json.loads(json.dumps(compile_edl(edl10, style), ensure_ascii=False))
    assert obtenido == esperado, (
        "el plan compilado cambió. Si es intencionado, regenera el golden y "
        "MIRA el diff: un slot movido o un token tocado llega hasta aquí")


def test_compilar_dos_veces_da_bytes_identicos(edl10, style, tmp_path):
    from edl_compile import write_plan
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    write_plan(compile_edl(edl10, style), a)
    write_plan(compile_edl(edl10, style), b)
    assert a.read_bytes() == b.read_bytes()


def test_el_golden_es_json_valido_y_no_esta_vacio(project_root):
    """Que el propio fixture no sea un archivo corrupto o truncado — si esto
    falla, el fallo de arriba no dice nada útil."""
    plan = json.loads((project_root / "tests" / "golden" / "10.plan.json").read_text())
    assert plan["shots"] and plan["visuals"] and plan["captions"] and plan["sfx"]


def test_el_plan_de_la_pieza_12_no_ha_cambiado(edl12, style, project_root):
    """La 12 congela lo que la 10 no cubría: el evento CARD, los dos slots
    nuevos y los tres mecanismos de objeto (`reveal`, `count`, coreografía
    interna). Sin este golden, un `card_body` retocado o un slot movido
    tardaría tres piezas en salir a la luz."""
    esperado = json.loads((project_root / "tests" / "golden" / "12.plan.json").read_text())
    obtenido = json.loads(json.dumps(compile_edl(edl12, style), ensure_ascii=False))
    assert obtenido == esperado, (
        "el plan compilado de la pieza 12 cambió. Si es intencionado, "
        "regenera el golden y MIRA el diff")


def test_la_pieza_12_emite_las_cinco_tarjetas(plan12):
    """El camino del EDL emitía `cards: []` fijo hasta la pieza 12; que la
    lista llegue con contenido es la prueba de que la capa existe de punta a
    punta, no solo en el schema."""
    assert len(plan12["cards"]) == 5
    assert all("start" in c and "end" in c for c in plan12["cards"])
    assert [c["start"] for c in plan12["cards"]] == sorted(
        c["start"] for c in plan12["cards"])


def test_el_plan_de_la_pieza_13_no_ha_cambiado(edl13, style, project_root):
    """La 13 congela lo que las anteriores no cubrían: `max_bare_stage` en 0,
    el cuerpo de rótulo `msgteaser` y los tres objetos de agenda."""
    esperado = json.loads((project_root / "tests" / "golden" / "13.plan.json").read_text())
    obtenido = json.loads(json.dumps(compile_edl(edl13, style), ensure_ascii=False))
    assert obtenido == esperado, (
        "el plan compilado de la pieza 13 cambió. Si es intencionado, "
        "regenera el golden y MIRA el diff")


def test_el_plan_de_la_pieza_14_no_ha_cambiado(edl14, style, project_root):
    """La 14 congela los dos objetos nuevos —la rejilla y la tarjeta de
    indicador— y, con ellos, el primer stage que ACUMULA cuatro instancias del
    MISMO objeto en los cuatro slots `stack`. Un `stack-4` movido rompe aquí en
    vez de descubrirse tres piezas después."""
    esperado = json.loads((project_root / "tests" / "golden" / "14.plan.json").read_text())
    obtenido = json.loads(json.dumps(compile_edl(edl14, style), ensure_ascii=False))
    assert obtenido == esperado, (
        "el plan compilado de la pieza 14 cambió. Si es intencionado, "
        "regenera el golden y MIRA el diff")


def test_la_pieza_14_acumula_las_cuatro_tarjetas_de_indicador(plan14):
    """Los cuatro indicadores ENTRAN y ninguno sale: el panel se construye
    delante del espectador. Si alguno se declarara con `OBJECT_EXIT`, el
    argumento («cada indicador trae su decisión») se quedaría en uno a la vez."""
    stage = next(v for v in plan14["visuals"] if v["mock"][0] == "motion_stage"
                 and any(o["kind"] == "kpi-card" for o in v["mock"][1]["objects"]))
    kpis = [o for o in stage["mock"][1]["objects"] if o["kind"] == "kpi-card"]
    assert [o["slot"] for o in kpis] == ["stack-1", "stack-2", "stack-3", "stack-4"]
    assert [o["in"] for o in kpis] == sorted(o["in"] for o in kpis)
    assert all(o["state"]["action"] for o in kpis)
