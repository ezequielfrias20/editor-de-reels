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


