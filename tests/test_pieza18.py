"""Pieza 18 — el motion design descrito en lenguaje natural.

Cinco componentes nuevos, y casi cada test de aquí nace de algo que
`hyperframes check` daba por bueno o que solo se vio en el frame. Es la regla
dura del proyecto («no dar por buena una animación sin mirar el frame»)
convertida en red, igual que en la pieza 17.
"""
import re

import pytest

import mockups
from tokens import C, contrast


# ── keyframe_grind: el trabajo se CUENTA, no se enuncia ─────────────────────
def test_los_rombos_caen_de_uno_en_uno_entre_sus_dos_bordes():
    """Un montón de keyframes ya puestos diría «hay muchos»; el ritmo dice
    «esto lo pone alguien uno a uno», que es la frase del hook."""
    _, _, anims = mockups.keyframe_grind("k", [0.06, 0.8, 2.5, 3.5, 3.7])
    caidas = sorted(a[2] for a in anims if re.match(r"#k-k\d+$", a[1]))
    assert len(caidas) == 14
    assert caidas[0] == pytest.approx(2.5) and caidas[-1] == pytest.approx(3.5)
    assert caidas == sorted(caidas), "caen en orden, no a la vez"


def test_el_contador_sube_con_los_rombos_y_no_antes():
    _, _, anims = mockups.keyframe_grind("k", [0.06, 0.8, 2.5, 3.5, 3.7], total=240)
    roll = next(a for a in anims if a[0] == "count-roll")
    assert roll[2] == pytest.approx(2.5), "arranca con el primer rombo"
    assert roll[3] == pytest.approx(1.0), "y dura lo que dura la caída"
    assert (roll[4], roll[5]) == (0, 240)


def test_el_escenario_no_recibe_NI_UN_tween_despues_de_entrar():
    """Es lo único de la pieza que se queda quieto a propósito: cualquier
    gesto ahí contradiría el rótulo SIN MOTION que lleva pegado."""
    _, _, anims = mockups.keyframe_grind("k", [0.06, 0.8, 2.5, 3.5, 3.7])
    sobre_el_stage = [a for a in anims if a[1] == "#k-stage"]
    assert len(sobre_el_stage) == 1 and sobre_el_stage[0][0] == "rise-in"


def test_el_reloj_es_lo_UNICO_que_se_sella():
    """Es la conclusión del beat, no un dato más de la pista."""
    _, _, anims = mockups.keyframe_grind("k", [0.06, 0.8, 2.5, 3.5, 3.7])
    sellos = [a[1] for a in anims if a[0] == "stamp"]
    assert sellos == ["#k-clock"]


# ── agent_editor: el lienzo vacío no puede ser un rectángulo negro ──────────
def test_el_lienzo_nace_con_sus_guias_no_en_negro():
    """El frame de t=12 del primer montaje: 980x244 de negro durante los
    cuatro segundos del tecleo, que se lee como panel roto y no como lienzo."""
    _, html, _ = mockups.agent_editor(
        "e", "prompt", [0, .4, 3, 5], [["pista", 2.0]], ["UNO"])
    for marca in ("aeguide", "aetick", "aecross", "aeres"):
        assert marca in html, f"falta la guía {marca} del área de trabajo"


def test_las_guias_son_CHROME_y_estan_desde_el_primer_frame():
    """Si entraran animadas serían contenido, y el contenido espera su
    palabra. El área de trabajo no espera a nadie: ya estaba."""
    _, _, anims = mockups.agent_editor(
        "e", "prompt", [0, .4, 3, 5], [["pista", 2.0]], ["UNO"])
    sels = {a[1] for a in anims}
    assert not any(s.endswith(("-guide", "-tick", "-cross", "-res")) for s in sels)


def test_las_pistas_reservan_su_alto_aunque_no_hayan_entrado():
    """Si la zona de pistas creciera al llenarse, el panel entero daría un
    salto de layout — la lección de `step_grid` con su `.sgtxt` vacío."""
    _, sin, _ = mockups.agent_editor("e", "p", [0, .4, 3, 5],
                                     [["a", 2.0], ["b", 2.4], ["c", 2.8]], [])
    assert sin.count("aerow") == 3, "las tres filas se emiten siempre"


def test_el_cursor_del_chat_se_apaga_cuando_el_foco_se_va_arriba():
    """`type-word` deja su cursor DENTRO del innerHTML (pieza 16): sin el
    `caret-off` el campo sigue parpadeando cinco segundos después de enviar."""
    _, _, anims = mockups.agent_editor(
        "e", "un prompt", [0, .4, 3, 5], [["pista", 2.0]], ["UNO"])
    tecleo = next(a for a in anims if a[0] == "type-word")
    apagado = next(a for a in anims if a[0] == "caret-off")
    assert tecleo[2] < apagado[2] <= 2.0


def test_el_logo_de_hyperframes_del_chat_va_con_uid():
    """Se inlinea tres veces en la pieza y trae dos gradientes con id propio:
    sin namespacing, la segunda y la tercera salen VACÍAS (§14)."""
    _, a, _ = mockups.agent_editor("e1", "p", [0, .4, 3, 5], [["x", 2.0]], [])
    _, b, _ = mockups.agent_editor("e2", "p", [0, .4, 3, 5], [["x", 2.0]], [])
    ga = set(re.findall(r'id="(paint\d[^"]*)"', a))
    gb = set(re.findall(r'id="(paint\d[^"]*)"', b))
    assert ga and gb and not (ga & gb), "dos instancias comparten id de gradiente"


# ── motion_demo: cuatro ejemplos, no cuatro etiquetas ───────────────────────
def test_cada_palabra_del_ejemplo_de_textos_entra_en_SU_palabra():
    _, _, anims = mockups.motion_demo(
        "d", "text", "", [30.875, 31.276, 31.453],
        words=["TEXTOS", "QUE", "ENTRAN"])
    por_sel = {a[1]: a[2] for a in anims}
    assert por_sel["#d-w0"] == pytest.approx(30.875)
    assert por_sel["#d-w1"] == pytest.approx(31.276)
    assert por_sel["#d-w2"] == pytest.approx(31.453)


def test_las_barras_crecen_desde_su_BASE_no_desde_su_centro():
    """`chip-in` escala desde el centro y una barra que sale de su centro no
    se lee como una barra que crece: se lee como una barra que aparece."""
    css, _, anims = mockups.motion_demo("d", "chart", "", [0.1])
    assert "transform-origin:50% 100%" in css.replace("\n", "")
    assert all(a[0] == "rise-bar" for a in anims if re.match(r"#d-b\d+$", a[1]))


def test_la_onda_tiene_una_base_declarada_antes_del_primer_golpe():
    """Tres `fromTo` sobre la misma propiedad dejan el reposo en manos de cuál
    se autoró el último. Aquí coinciden, pero «inofensivo por casualidad» no
    es una base — `gsap_repeated_fromto_without_baseline` lo caza."""
    _, _, anims = mockups.motion_demo("d", "audio", "", [1.0, 2.0, 3.0])
    bases = [a for a in anims if a[0] == "set-hidden"]
    assert len(bases) == mockups._DEMO_BARS
    assert all(a[2] == 0.0 for a in bases)
    assert all(a[2] == 0.0 or a[0] != "set-hidden" for a in anims)
    primer_golpe = min(a[2] for a in anims if a[0] == "rise-bar")
    assert all(b[2] < primer_golpe for b in bases)


def test_dos_golpes_de_la_onda_no_solapan_tweens_sobre_la_misma_barra():
    """Lo que `hyperframes check` llama `overlapping_gsap_tweens`."""
    _, _, anims = mockups.motion_demo("d", "audio", "", [35.013, 36.0, 36.9])
    de_la_barra_0 = sorted(a[2] for a in anims
                           if a[1] == "#d-a0" and a[0] == "rise-bar")
    dur = 0.26 * 1.30
    assert all(b - a > dur for a, b in zip(de_la_barra_0, de_la_barra_0[1:]))


def test_el_rotulo_entra_EXACTAMENTE_en_su_palabra():
    """60 ms son dos frames, y «nada entra antes de su palabra» se mide en
    frames."""
    _, _, anims = mockups.motion_demo("d", "chart", "GRÁFICOS", [32.401])
    lab = next(a for a in anims if a[1] == "#d-lab")
    assert lab[2] == pytest.approx(32.401)


def test_el_recap_deja_un_hueco_que_ninguna_capacidad_llena():
    _, html, anims = mockups.motion_demo(
        "d", "recap", "", [37.8], slots=["A", "B", "C", "D"],
        fill="CRITERIO", fill_at=40.683)
    assert "mdhole" in html and "CRITERIO" in html
    apaga = next(a for a in anims if a[0] == "badge-out" and a[1] == "#d-hole")
    sella = next(a for a in anims if a[0] == "stamp" and a[1] == "#d-fill")
    assert apaga[2] == sella[2] == pytest.approx(40.683), \
        "el hueco se apaga en el MISMO instante en que entra la palabra"


def test_el_hueco_del_recap_sin_fill_at_se_queda_puesto():
    _, _, anims = mockups.motion_demo("d", "recap", "", [1.0], slots=["A"])
    assert not any(a[1] in ("#d-hole", "#d-fill") and a[0] in ("badge-out", "stamp")
                   for a in anims)


def test_una_variante_desconocida_falla_en_vez_de_dibujar_nada():
    with pytest.raises(ValueError):
        mockups.motion_demo("d", "inventada", "", [0.0])


# ── idea_fate: la misma idea en dos estados ─────────────────────────────────
def test_el_nombre_de_la_idea_espera_su_palabra_y_su_sitio_es_un_hueco():
    _, html, anims = mockups.idea_fate(
        "i", "Una animación", [], [21.086, 22.42, 27.674])
    assert "ifnamehole" in html
    apaga = next(a for a in anims if a[1] == "#i-nhole")
    entra = next(a for a in anims if a[1] == "#i-name")
    assert apaga[2] == entra[2] == pytest.approx(22.42)


def test_las_salidas_existen_como_hueco_desde_que_entra_la_tarjeta():
    """El frame de t=23.5 del primer montaje: tarjeta pequeña y media banda de
    grafito debajo. El usuario pidió que NUNCA hubiera fondo vacío (§4), y un
    hueco discontinuo lo llena diciendo algo."""
    _, html, anims = mockups.idea_fate(
        "i", "Idea", [["a", 24.8], ["b", 26.3]], [21.086, 22.42, 27.674])
    assert html.count("ifxhole") == 2
    for n, t in ((0, 24.8), (1, 26.3)):
        hueco = [a for a in anims if a[1] == f"#i-h{n}"]
        assert any(a[0] == "chip-in" and a[2] < 22.0 for a in hueco), \
            "el hueco está puesto mucho antes de que se diga su texto"
        assert any(a[0] == "badge-out" and a[2] == pytest.approx(t) for a in hueco)


def test_la_pastilla_de_la_idea_descartada_no_es_verde_ni_roja():
    """Verde diría «resuelto» y rojo «esto falla»: lo que pasa es que la idea
    se quedó fuera."""
    _, muerta, _ = mockups.idea_fate("i", "Idea", [], [0, 1, 2], badge="descartada")
    _, viva, _ = mockups.idea_fate("i", "Idea", [], [0, 1, 2], revive=True,
                                   badge="con IA")
    assert 'class="ifbadge off"' in muerta
    assert 'class="ifbadge"' in viva


def test_el_destello_NO_es_un_emoji():
    """Un emoji se pinta con la paleta del navegador pero el checker lee el
    `color` heredado, que sin declarar es negro: 1.11:1 contra el grafito y la
    pieza entera se cae por un glifo que en pantalla se ve perfectamente."""
    _, html, _ = mockups.idea_fate("i", "Idea", [], [0, 1, 2])
    assert "💡" not in html
    assert "currentColor" in html, "el destello se tiñe con el estado, no propio"


@pytest.mark.parametrize("paleta", ["claro", "oscuro"])
def test_el_destello_pasa_AA_en_los_dos_estados(paleta):
    """Lo que el emoji no hacía. Se mide, no se estima."""
    import tokens
    tokens.use(paleta)
    try:
        assert contrast(C["text3"], C["bg"]) >= 3.0
        assert contrast(C["accent_hi"], C["bg"]) >= 3.0
    finally:
        tokens.use("oscuro")


# ── idea_veneer: lo de arriba se va y lo de abajo NO cambia ─────────────────
def test_al_apagarse_el_espectaculo_la_tarjeta_gris_no_recibe_ni_un_tween():
    """Si se encogiera o se tiñera, el frame diría «y entonces pasó algo». Lo
    que la frase dice es que no pasó nada."""
    _, _, anims = mockups.idea_veneer("v", "Otro vídeo más", "ESPECTACULAR",
                                      [41.456, 42.234, 44.884])
    sobre_la_tarjeta = [a for a in anims if a[1] == "#v-slab"]
    assert len(sobre_la_tarjeta) == 1 and sobre_la_tarjeta[0][0] == "rise-in"
    assert sobre_la_tarjeta[0][2] == pytest.approx(41.456)


def test_se_va_TODO_lo_de_encima_capa_y_palabra():
    _, _, anims = mockups.idea_veneer("v", "Idea", "WOW", [0.0, 1.0, 3.0])
    salidas = {a[1] for a in anims if a[0] == "badge-out"}
    assert "#v-word" in salidas and "#v-layer" in salidas


def test_la_capa_va_ENCIMA_no_al_lado():
    """«Encima» es el literal de la frase."""
    css, _, _ = mockups.idea_veneer("v", "Idea", "WOW", [0.0, 1.0, 3.0])
    regla = re.search(r"\.ivelayer\{([^}]*)\}", css.replace("\n", "")).group(1)
    assert "position:absolute" in regla


def test_los_dos_avisos_de_layout_se_responden_por_separado():
    """`data-layout-allow-occlusion` (panel opaco sobre su texto) NO cubre
    `data-layout-allow-overlap` (dos bloques de texto que se pisan). El linter
    cazó el segundo con el primero ya declarado."""
    _, html, _ = mockups.idea_veneer("v", "Idea", "WOW", [0.0, 1.0, 3.0])
    assert "data-layout-allow-occlusion" in html
    assert "data-layout-allow-overlap" in html


@pytest.mark.parametrize("paleta", ["claro", "oscuro"])
def test_la_palabra_espectacular_pasa_AA_sobre_todo_el_degradado(paleta):
    """Sale del muestreo por el `allow-overlap`, así que se mide a mano — 92px
    y peso 900 la ponen en «texto grande», umbral 3:1. Se mide contra CADA
    parada del degradado que el componente emite de verdad."""
    import tokens
    tokens.use(paleta)
    try:
        css, _, _ = mockups.idea_veneer("v", "Idea", "WOW", [0.0, 1.0, 3.0])
        grad = re.search(r"\.ivelayer\{\{?[^}]*?linear-gradient\(([^;]*)\);", css)
        assert grad, "`.ivelayer` ya no declara su degradado"
        paradas = re.findall(r"#[0-9A-Fa-f]{6}", grad.group(1))
        assert len(paradas) >= 3
        for fondo in paradas:
            assert contrast(C["text"], fondo) >= 3.0, (paleta, fondo)
    finally:
        tokens.use("oscuro")


# ── el gesto nuevo ──────────────────────────────────────────────────────────
def test_rise_bar_escala_en_Y_y_no_toca_height(bc):
    """Animar `height` es reflow y el sistema solo mueve opacidad y
    transform (§6)."""
    js = bc.emit_anim(("rise-bar", "#b", 0.1, 0.26)).replace(" ", "")
    assert "scaleY:0.04" in js and "scaleY:1" in js
    assert "height" not in js


def test_rise_bar_no_usa_muelle(bc):
    js = bc.emit_anim(("rise-bar", "#b", 0.1, 0.26))
    assert "back.out" not in js and "power3.out" in js


def test_set_hidden_deja_la_base_en_el_instante_que_se_le_pide(bc):
    js = bc.emit_anim(("set-hidden", "#b", 0.0, 0.0)).replace(" ", "")
    assert "tl.set('#b'" in js and "opacity:0" in js and "scaleY:0.04" in js


# ── el despacho ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("nombre", [
    "keyframe_grind", "agent_editor", "motion_demo", "idea_fate", "idea_veneer"])
def test_los_cinco_componentes_estan_en_el_despacho(bc, nombre):
    """Un componente que existe pero no está registrado compila con un
    KeyError que solo aparece al escribir el plan."""
    fuente = (bc.__file__ and open(bc.__file__).read()) or ""
    assert f'"{nombre}": mockups.{nombre}' in fuente


@pytest.mark.parametrize("clave", ["exits", "layers"])
def test_los_tiempos_dentro_de_tupla_se_remapean(bc, clave):
    """`exits` y `layers` llevan su tiempo DENTRO de cada tupla, como `parts`
    en `rewrite_line`: sin remapeo llegarían en la línea del corte y se
    sumarían dos veces (la trampa de `motion_stage`)."""
    fuente = open(bc.__file__).read()
    assert f'for key in ("exits", "layers")' in fuente or f'"{clave}"' in fuente
