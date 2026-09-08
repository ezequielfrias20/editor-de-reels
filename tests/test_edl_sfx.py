"""SFX opt-in, colapso y concurrencia — Tarea 10.

`resolve_sfx` vive en `edl_metrics.py` (donde ya está `q()` y el resto de
cálculos de sonido, `sfx_per_macro` incluido) y `edl_compile.py` lo
re-exporta: es lo que le permite a `measure()` calcular `sfx_dropped` sin que
`edl_metrics` tenga que importar `edl_compile` (que sí importa `edl_metrics`
— un import en la otra dirección sería circular).
"""
import pytest
from edl_compile import PRESET_SFX, PRIORITY, resolve_sfx


# ── opt-in ───────────────────────────────────────────────────────────────────
def test_sin_declarar_nada_no_suena():
    """`do not add SFX to every animation` como comportamiento por defecto,
    no como disciplina: el silencio no hay que recordarlo."""
    assert resolve_sfx([{"t": 1.0, "preset": "float-in", "sfx": None}]) == []


def test_auto_toma_el_efecto_del_preset():
    out = resolve_sfx([{"t": 1.0, "preset": "float-in", "sfx": "auto"}])
    assert out[0][1] == PRESET_SFX["float-in"] == "pop"


def test_auto_sin_preset_reconocido_falla_claro():
    with pytest.raises(KeyError, match="preset-inventado"):
        resolve_sfx([{"t": 1.0, "preset": "preset-inventado", "sfx": "auto"}])


def test_un_nombre_explicito_no_pasa_por_el_preset():
    """`sfx` puede ser el nombre del efecto directamente, sin `preset` — el
    tercer test de concurrencia lo hace así."""
    out = resolve_sfx([{"t": 1.0, "sfx": "chime"}])
    assert out[0][1] == "chime"


# ── colapso de iguales ───────────────────────────────────────────────────────
def test_dos_iguales_dentro_de_250ms_colapsan():
    out = resolve_sfx([{"t": 1.00, "preset": "float-in", "sfx": "auto"},
                       {"t": 1.15, "preset": "float-in", "sfx": "auto"}])
    assert len(out) == 1


def test_dos_iguales_separados_no_colapsan():
    out = resolve_sfx([{"t": 1.00, "preset": "float-in", "sfx": "auto"},
                       {"t": 1.60, "preset": "float-in", "sfx": "auto"}])
    assert len(out) == 2


def test_el_colapso_sobrevive_como_el_primero():
    """La acumulación tiene que sonar a algo que EMPIEZA a crecer, no a un
    eco tardío: el superviviente es el primer instante, no el último."""
    out = resolve_sfx([{"t": 1.00, "sfx": "pop"}, {"t": 1.20, "sfx": "pop"}])
    assert out[0][0] == 1.0


# ── concurrencia entre clases ─────────────────────────────────────────────────
def test_distintos_dentro_de_180ms_gana_la_clase_mas_alta():
    """impact + whoosh + pop casi simultáneos son una metralleta sonora."""
    out = resolve_sfx([{"t": 1.00, "sfx": "pop"},
                       {"t": 1.05, "sfx": "whoosh-short"},
                       {"t": 1.10, "sfx": "impact-bass-1"}])
    assert len(out) == 1 and out[0][1] == "impact-bass-1"
    assert PRIORITY["impact-bass-1"] < PRIORITY["pop"]


def test_distintos_separados_no_compiten():
    out = resolve_sfx([{"t": 1.00, "sfx": "pop"},
                       {"t": 2.00, "sfx": "impact-bass-1"}])
    assert len(out) == 2


def test_tres_clases_distintas_dejan_solo_la_mas_alta_sin_importar_el_orden():
    """El orden de llegada no puede decidir el ganador — solo la prioridad."""
    out = resolve_sfx([{"t": 1.00, "sfx": "impact-bass-1"},
                       {"t": 1.05, "sfx": "pop"},
                       {"t": 1.10, "sfx": "whoosh-short"}])
    assert len(out) == 1 and out[0][1] == "impact-bass-1"


# ── la tupla que espera build_sfx ────────────────────────────────────────────
def test_el_trim_es_relativo_y_por_defecto_1():
    """El EDL nunca fija dB: el nivel absoluto lo calcula la fórmula de
    build_sfx a partir de la medición del archivo."""
    out = resolve_sfx([{"t": 1.0, "sfx": "pop", "trim": 0.85}])
    assert out[0][2] == 0.85
    assert resolve_sfx([{"t": 2.0, "sfx": "pop"}])[0][2] == 1.0


def test_la_tupla_es_la_que_espera_build_sfx():
    t, nombre, trim, por_que = resolve_sfx([{"t": 1.0, "sfx": "pop",
                                             "why": "entra el reloj"}])[0]
    assert (t, nombre, trim, por_que) == (1.0, "pop", 1.0, "entra el reloj")


def test_los_tiempos_salen_cuantizados():
    """`t` no llega alineado a frame desde el EDL (es `remap()` crudo) — el
    único punto de cuantización tiene que tocarlo aquí, no dejarlo para
    `build-composition.py`."""
    out = resolve_sfx([{"t": 1.0021, "sfx": "pop"}])
    assert out[0][0] == 1.0


# ── integración con la pieza 10 ───────────────────────────────────────────────
def test_la_pieza_10_declara_las_cinco_sfx_del_plan(edl10):
    from edl_metrics import sfx_declarations
    decl = sfx_declarations(edl10)
    assert len(decl) == 5


def test_el_plan_de_la_pieza_10_trae_la_capa_de_sfx(plan10):
    assert len(plan10["sfx"]) >= 1
    for row in plan10["sfx"]:
        assert len(row) == 4


def test_sfx_dropped_es_cero_para_la_pieza_10(edl10, style):
    """Los cinco `sfx:"auto"` de la pieza 10 caen lejos entre sí — nada
    debería colapsar. Si algún día empieza a colapsar, este test avisa."""
    from edl_metrics import measure
    m = measure(edl10, style)
    assert m["sfx_dropped"] == 0.0
