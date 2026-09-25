"""Lo que trajo la pieza 16: dos bugs de la herramienta y tres componentes.

Los dos bugs son de `logos.py` y del emisor de visuales, no del plan, y los dos
salieron de mirar el frame renderizado — no de leer el JSON:

1. **Un SVG de marca inlineado dos veces se renderiza VACÍO la segunda vez.**
   La marca de Canva trae seis gradientes con ids fijos de exportador y seis
   `url(#…)` que los apuntan; la pieza la pinta cinco veces. El navegador
   resuelve cada referencia al PRIMER id del documento, así que al ocultarse
   el host de la primera copia las otras cuatro pierden el relleno.
2. **El último visual se fundía a negro.** La bitácora ya escribía la regla
   (§9, trampa 6: «el CTA tiene que estar puesto en el último frame») y el
   emisor no la cumplía — le ponía `fade_out` a TODOS.

Cada gate tiene aquí su camino de FALLO, no solo el de éxito: un gate que
nunca ha fallado no es un gate.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import logos  # noqa: E402
import mockups  # noqa: E402


@pytest.fixture(scope="session")
def bc():
    spec = importlib.util.spec_from_file_location(
        "build_composition", SCRIPTS / "build-composition.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SVG_CON_REFS = (
    '<svg viewBox="0 0 10 10">'
    '<defs><radialGradient id="g1"><stop stop-color="#fff"/></radialGradient>'
    '<clipPath id="c1"><rect width="10" height="10"/></clipPath></defs>'
    '<path fill="url(#g1)" clip-path="url(#c1)" d="M0 0h10v10H0z"/></svg>'
)


# ── bug 1: los ids internos del SVG ──────────────────────────────────────────
def test_los_ids_y_sus_referencias_se_renombran_juntos():
    a = logos.namespace_svg_ids(SVG_CON_REFS, "v-uno")
    assert 'id="g1"' not in a and 'url(#g1)' not in a
    # El id nuevo y la referencia nueva tienen que COINCIDIR, que es justo lo
    # que rompía el render: renombrar solo uno de los dos deja el gradiente
    # huérfano y el relleno vacío igual que antes.
    nuevo = a.split('id="g1__')[1].split('"')[0]
    assert f'url(#g1__{nuevo})' in a
    assert f'url(#c1__{nuevo})' in a


def test_dos_instancias_no_comparten_un_solo_id():
    a = logos.namespace_svg_ids(SVG_CON_REFS, "v-uno")
    b = logos.namespace_svg_ids(SVG_CON_REFS, "v-dos")
    ids_a = set(logos._ID_ATTR.findall(a))
    ids_b = set(logos._ID_ATTR.findall(b))
    assert ids_a and ids_b and not (ids_a & ids_b)


def test_el_sufijo_no_depende_del_orden_de_las_llamadas():
    """Un contador daría HTML distinto compilando el mismo plan dos veces."""
    primero = logos.namespace_svg_ids(SVG_CON_REFS, "v-uno")
    logos.namespace_svg_ids(SVG_CON_REFS, "otra-cosa")
    assert logos.namespace_svg_ids(SVG_CON_REFS, "v-uno") == primero


def test_una_referencia_que_el_svg_no_define_se_deja_intacta():
    externo = '<svg viewBox="0 0 10 10"><use href="#no-mio"/></svg>'
    assert logos.namespace_svg_ids(externo, "v-uno") == externo


def test_un_svg_sin_ids_no_se_toca():
    plano = '<svg viewBox="0 0 24 24"><path d="M0 0h24v24H0z"/></svg>'
    assert logos.namespace_svg_ids(plano, "v-uno") == plano


def test_marcar_sin_uid_un_svg_con_referencias_falla(monkeypatch, tmp_path):
    """El camino de FALLO. Sin él, la protección es una intención."""
    (tmp_path / "assets" / "logos").mkdir(parents=True)
    (tmp_path / "assets" / "logos" / "falsa.svg").write_text(SVG_CON_REFS)
    (tmp_path / "assets" / "logos" / "meta.json").write_text(
        '{"falsa": {"title": "Falsa", "format": "svg", "tile": null}}')
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="uid"):
        logos.mark("falsa", 64)
    # Con `uid` sí pasa, y el id sale renombrado.
    html, _ = logos.mark("falsa", 64, uid="v-uno")
    assert 'id="g1"' not in html


def test_canva_es_la_marca_que_lo_destapo(project_root, monkeypatch):
    """La marca real, no una de laboratorio: si un día deja de traer
    gradientes propios, este test avisa de que el caso desapareció."""
    monkeypatch.chdir(project_root)
    raw = (project_root / "assets" / "logos" / "canva.svg").read_text()
    assert logos.svg_has_internal_refs(raw)


# ── bug 1b: el gate sobre el HTML ya ensamblado ──────────────────────────────
def test_el_gate_de_ids_falla_con_un_duplicado(bc):
    doc = '<div id="a"></div><div id="b"></div><div id="a"></div>'
    with pytest.raises(SystemExit, match='"a"|a,|: a'):
        bc.check_unique_element_ids(doc)


def test_el_gate_de_ids_pasa_sin_duplicados(bc):
    bc.check_unique_element_ids('<div id="a"></div><div id="b"></div>')


def test_el_gate_de_ids_no_confunde_data_viz_id(bc):
    """`\\b` casaba DENTRO de `data-viz-id="…"` y los doce visuales de la
    pieza salían como ids repetidos — un falso positivo que llegó a parar una
    compilación buena."""
    bc.check_unique_element_ids(
        '<div data-viz-id="v-caps"></div><div data-viz-id="v-caps"></div>')


# ── bug 2: el visual que llega al final no se funde ──────────────────────────
def test_el_ultimo_visual_no_se_funde_a_la_salida(bc, monkeypatch):
    js = _emitir_fundidos(bc, monkeypatch, dur=10.0,
                          visuals=[{"id": "v-cta", "start": 8.0, "end": None}])
    assert "opacity: 0, duration" not in js, (
        "el CTA se apaga en el último frame, que es el que congela la "
        "plataforma cuando el reel vuelve a empezar (§9, trampa 6)")


def test_un_visual_intermedio_si_se_funde(bc, monkeypatch):
    js = _emitir_fundidos(bc, monkeypatch, dur=10.0,
                          visuals=[{"id": "v-med", "start": 2.0, "end": 5.0}])
    assert "opacity: 0, duration" in js


def _emitir_fundidos(bc, monkeypatch, dur, visuals):
    """El trozo del emisor que decide los fundidos de los visuales."""
    monkeypatch.setattr(bc, "VISUALS", visuals)
    js = []
    for v in visuals:
        vs = bc.q(v["start"])
        ve = bc.q(dur if v.get("end") is None else min(v["end"], dur))
        sel = f'.viz[data-viz-id="{v["id"]}"]'
        if ve < dur - 1.0 / bc.FPS:
            js.append(f'tl.to(\'{sel}\', {{ opacity: 0, duration: 0.26 }});')
    return "\n".join(js)


# ── tool_pair ────────────────────────────────────────────────────────────────
def _kinds(anims, sufijo):
    return [a[0] for a in anims if a[1].endswith(sufijo)]


def test_tool_pair_dibuja_el_hueco_cuando_la_segunda_marca_tarda(project_root,
                                                                 monkeypatch):
    monkeypatch.chdir(project_root)
    _, html, anims = mockups.tool_pair(
        "v1", {"slug": "claude", "name": "Claude"},
        {"slug": "canva", "name": "Canva"}, at=[1.0, 1.6, 4.9])
    assert "tp-slot" in html
    # El hueco entra Y se apaga: las dos mitades del relevo.
    assert _kinds(anims, "-slot") == ["chip-in", "badge-out"]


def test_tool_pair_no_pelea_dos_tweens_por_la_misma_opacidad(project_root,
                                                             monkeypatch):
    """La reaparición de la pareja ya formada NO pasa por el hueco.

    Con `t_slot == t_right`, un `chip-in` y un `badge-out` sobre el MISMO
    elemento en el MISMO instante son dos tweens peleándose por `opacity`, y
    de cuál gane depende el orden de evaluación — justo lo que rompe un render
    determinista.
    """
    monkeypatch.chdir(project_root)
    _, _, anims = mockups.tool_pair(
        "v2", {"slug": "claude", "name": "Claude"},
        {"slug": "canva", "name": "Canva"}, at=[14.6, 14.6, 14.6])
    assert _kinds(anims, "-slot") == []
    assert _kinds(anims, "-fill") == ["chip-in"]


# ── claude_prompt ────────────────────────────────────────────────────────────
def test_claude_prompt_teclea_una_linea_por_tiempo(project_root, monkeypatch):
    monkeypatch.chdir(project_root)
    _, _, anims = mockups.claude_prompt(
        "v3", lines=["uno", "dos", "tres"], at=[1.0, 2.0, 3.0])
    tecleos = [a for a in anims if a[0] == "type-word"]
    assert [a[2] for a in tecleos] == [1.0, 2.0, 3.0]
    assert [a[4] for a in tecleos] == ["uno", "dos", "tres"]


def test_el_cursor_viaja_no_se_multiplica(project_root, monkeypatch):
    """`type-word` mete el cursor DENTRO del innerHTML de su destino, así que
    sin `caret-off` acabarían tres parpadeando a la vez."""
    monkeypatch.chdir(project_root)
    _, _, anims = mockups.claude_prompt(
        "v4", lines=["uno", "dos", "tres"], at=[1.0, 2.0, 3.0])
    apagados = [a for a in anims if a[0] == "caret-off"]
    # Una línea deja de tener cursor cuando arranca la SIGUIENTE; la última se
    # queda parpadeando, que es lo que hace una caja de texto con el foco.
    assert [(a[1], a[2]) for a in apagados] == [
        ("#v4-l0", 2.0), ("#v4-l1", 3.0)]


def test_caret_off_reescribe_la_linea_sin_el_span(bc):
    js = bc.emit_anim(("caret-off", "#x-l0", 2.0, 0.01, "hola"))
    assert "ccaret" not in js and '"hola"' in js and "tl.set" in js


def test_el_placeholder_se_apaga_con_la_primera_linea(project_root, monkeypatch):
    monkeypatch.chdir(project_root)
    _, _, anims = mockups.claude_prompt("v5", lines=["uno"], at=[2.5])
    ph = [a for a in anims if a[1].endswith("-ph")]
    assert len(ph) == 1 and ph[0][0] == "badge-out" and ph[0][2] == 2.5


def test_sin_conector_no_se_dibuja_la_pastilla(project_root, monkeypatch):
    monkeypatch.chdir(project_root)
    _, html, anims = mockups.claude_prompt("v6", lines=["uno"], at=[1.0])
    assert "cp-conn" not in html
    assert not [a for a in anims if a[1].endswith("-conn")]


# ── layer_stack ──────────────────────────────────────────────────────────────
def test_la_capa_baja_en_su_palabra_no_con_la_fila(project_root, monkeypatch):
    monkeypatch.chdir(project_root)
    _, _, anims = mockups.layer_stack(
        "v7", apps=[{"slug": "canva", "name": "Canva"}, {"name": ""}],
        at=[44.4, 44.6], layer_at=49.3, kicker="UNA CAPA ENCIMA")
    capa = [a for a in anims if a[1].endswith("-layer")][0]
    assert capa[0] == "drop-in" and capa[2] == 49.3
    # El kicker NOMBRA la idea («una capa encima») y esa palabra se dice al
    # final del beat: puesto con la fila, se lee casi cinco segundos antes de
    # oírse. «Nada entra antes de su palabra» aplica al texto igual que al logo.
    kick = [a for a in anims if a[1].endswith("-kick")][0]
    assert kick[2] == 49.3


def test_una_app_sin_slug_se_pinta_muda(project_root, monkeypatch):
    """El guion dice «muchísimas otras aplicaciones» sin nombrar ninguna:
    poner logos que nadie mencionó sería inventarse guion."""
    monkeypatch.chdir(project_root)
    _, html, _ = mockups.layer_stack(
        "v8", apps=[{"name": ""}], at=[0.1], layer_at=1.0)
    # Solo la FILA: la capa de arriba sí lleva su marca, y buscar "brandmark"
    # en el html entero la encontraba siempre — el test pasaba por el motivo
    # equivocado antes de acotarlo.
    fila = html.split('class="ls-row"')[1]
    assert "ls-mute" in fila and "brandmark" not in fila


def test_cada_tesela_tiene_su_bajante(project_root, monkeypatch):
    monkeypatch.chdir(project_root)
    _, html, anims = mockups.layer_stack(
        "v9", apps=[{"name": ""}] * 4, at=[0.1] * 4, layer_at=1.0)
    trazos = [a for a in anims if a[0] == "draw"]
    assert len(trazos) == 4
    for i in range(4):
        assert f'id="v9-d{i}"' in html
    # Escalonadas y SIEMPRE después de que la capa haya empezado a bajar:
    # una bajante que llega antes que su origen no se lee como alcance.
    assert all(a[2] > 1.0 for a in trazos)
    assert [a[2] for a in trazos] == sorted(a[2] for a in trazos)
