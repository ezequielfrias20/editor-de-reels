"""Qué garantiza `check_band_top_covered` — y qué NO.

Medido en la pieza 18 y confirmado en la 17: en el MP4 renderizado, la banda
`top` cae al suelo grafito (luma ~26) durante **unos 130 ms en cada relevo
entre visuales**. El gate pasa igualmente, y tiene razón en pasar: lo que
comprueba es que en todo instante de un tramo `band` haya un visual DECLARADO,
no que el renderer lo esté pintando encendido en ese frame.

El fundido de relevo lo aplica el runtime de HyperFrames a los elementos
`class="clip"` a partir de `data-start`/`data-duration`; la composición no lo
gobierna. Y no es el problema que la doctrina de 2026-09-15 vino a resolver:
aquella medía **15.0 s de 55.3 en siete huecos** en la pieza 15 —beats enteros
sin nada asignado—, no tres o cuatro frames en un corte. A esa escala se lee
como el CORTE DURO que §6 pide, no como fondo vacío.

Este archivo existe para que nadie lea el nombre del gate y concluya que el
MP4 no puede tener un frame oscuro arriba. Si alguna vez se quiere esa
garantía, hay que medir LUMA sobre el render, que es otro gate y otro coste.
"""
import json

import pytest


@pytest.fixture(scope="module")
def plan18(fixtures_root, project_root):
    p = fixtures_root / "videos" / "18" / "plan.json"
    if not p.exists():
        pytest.skip("la pieza 18 no está")
    return json.loads(p.read_text())


def test_la_18_no_deja_ni_un_hueco_DECLARADO_en_la_banda(plan18):
    """Lo que el gate sí garantiza, y en esta pieza sale exacto: el `end` de
    cada visual ES el `start` del siguiente."""
    vis = sorted(plan18["visuals"], key=lambda v: v["start"])
    assert vis[0]["start"] == 0.0, "el hueco de arranque se cierra empezando en 0"
    for a, b in zip(vis, vis[1:]):
        assert a["end"] == pytest.approx(b["start"], abs=1e-6), (
            f"{a['id']} termina en {a['end']} y {b['id']} empieza en {b['start']}")


def test_la_banda_esta_cubierta_hasta_el_final_del_corte(plan18):
    vis = sorted(plan18["visuals"], key=lambda v: v["start"])
    assert vis[-1]["end"] >= 53.46


def test_el_cta_es_el_ultimo_visual_y_no_se_funde(plan18):
    """Trampa 6c: el último frame tiene que tener el CTA encendido."""
    vis = sorted(plan18["visuals"], key=lambda v: v["start"])
    assert vis[-1]["mock"][0] == "comment_ui"


def test_el_gate_mira_intervalos_declarados_no_luma(project_root):
    """La comprobación de que el gate es lo que este archivo dice que es. Si
    alguien le añade una medición de luma, este test lo obliga a actualizar la
    documentación de arriba en el mismo commit."""
    src = (project_root / "scripts" / "build-composition.py").read_text()
    i = src.find("def check_band_top_covered")
    assert i > 0, "el gate cambió de nombre"
    cuerpo = src[i:i + 3000]
    assert "luma" not in cuerpo.lower(), (
        "el gate ahora mide luma: actualiza la cabecera de este archivo y la "
        "nota de §4 en CLAUDE.md, porque la garantía ha cambiado")
