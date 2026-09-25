"""Los tres componentes de la pieza 19, y las dos extensiones que no mueven nada.

Casi todo lo que hay aquí sale de un fallo que `hyperframes check` daba por
bueno con 0 errores y que solo se vio extrayendo el frame — que es el patrón de
esta suite desde la pieza 16.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import icons  # noqa: E402
import mockups  # noqa: E402


def sels(anims):
    return [a[1] for a in anims]


# ── la regla que se llevó los cuatro tweens del roster ───────────────────────

TODOS = [
    lambda: mockups.agent_swarm("x", "fanout", [0.1, 0.4, 0.9], slug="claude"),
    lambda: mockups.agent_swarm("x", "solo", [0.1, 0.3, 0.5, 0.7, 0.9],
                                kicker="EN VEZ DE", label="UN SOLO AGENTE",
                                tasks=[["stack", ""]] * 4),
    lambda: mockups.agent_swarm("x", "roster", [0.1, 2.0], label="AGENTES",
                                total=146, lit=3),
    lambda: mockups.agent_swarm("x", "team", [0.1, 0.4, 0.7, 1.2],
                                label="SEGÚN LA TAREA",
                                team=[["code", "FRONTEND"], ["gear", "INGENIERÍA"]]),
    lambda: mockups.desktop_manager("x", "Agency Agents",
                                    [["code", "Frontend"], ["gear", "Ingeniería"]],
                                    [0.1, 0.4, 0.8]),
    lambda: mockups.split_problem("x", "+1 EMPLEADO GRATIS", "PROBLEMA COMPLEJO",
                                  [["code", "FRONTEND"], ["gear", "INGENIERÍA"],
                                   ["megaphone", "MARKETING"]],
                                  [0.1, 0.6, 1.2, 1.8, 2.4]),
]


@pytest.mark.parametrize("make", TODOS, ids=lambda f: "componente")
def test_ningun_selector_trae_el_prefijo_del_host(make):
    """`build_visuals` antepone `.viz[data-viz-id="…"]` a todo lo que devuelve
    un mockup, así que un selector ya prefijado se duplica y GSAP no encuentra
    el destino. `check` lo reporta como `console_warning` con **0 errores** y el
    gesto sencillamente no ocurre — la misma firma que el tachado de
    `rewrite_line` en la pieza 17. Aquí costó los cuatro tweens del roster: ni
    entraban los 146 puntos ni bajaban los 143."""
    _, _, anims = make()
    for s in sels(anims):
        assert "data-viz-id" not in s, f"selector ya prefijado: {s}"


# ── agent_swarm: cuatro estados del mismo tablero ────────────────────────────

def test_las_cuatro_variantes_existen_y_una_quinta_lanza():
    """El camino de FALLO: una variante mal escrita en el plan tiene que parar
    la compilación, no renderizar un tablero vacío."""
    with pytest.raises(ValueError) as e:
        mockups.agent_swarm("x", "enjambre", [0.1])
    assert "enjambre" in str(e.value)


def test_el_roster_apaga_los_que_sobran_pero_NO_los_borra():
    """A opacidad 0 el frame diría que esos agentes dejaron de existir, y la
    frase dice que siguen ahí sin usarse — la distinción que `idea_fate` hace
    entre una salida apagada y una en rojo."""
    _, _, anims = mockups.agent_swarm("x", "roster", [0.1, 2.0],
                                      label="AGENTES", total=146, lit=3)
    fade = [a for a in anims if a[0] == "fade-to"]
    assert len(fade) == 1, "los 143 son UN tween, no 143 decisiones editoriales"
    assert fade[0][1] == ".asdot:not(.pick)"
    assert 0 < fade[0][4] < 1, "bajan de intensidad; no se apagan ni se quedan"


def test_el_roster_emite_los_146_y_marca_exactamente_los_encendidos():
    _, html, _ = mockups.agent_swarm("x", "roster", [0.1, 2.0],
                                     label="AGENTES", total=146, lit=3)
    # ⚠ `class="asdot` casa TAMBIÉN con el contenedor `asdots` y daba 147: una
    # aserción que se pasa por uno es una aserción que no mide lo que dice.
    assert html.count('id="x-d') == 146
    assert html.count('asdot pick') == 3


def test_los_puntos_encendidos_son_deterministas():
    """Un golden no puede depender de un `random` — la regla que `spreadsheet`
    (pieza 14) fijó con sus barras."""
    a = mockups.agent_swarm("x", "roster", [0.1, 2.0], label="A", total=146, lit=3)[1]
    b = mockups.agent_swarm("x", "roster", [0.1, 2.0], label="A", total=146, lit=3)[1]
    assert a == b


def test_la_pila_del_agente_solo_no_nombra_ninguna_especialidad():
    """«Nada entra antes de su palabra» (§7) aplicado a un icono. Este beat cae
    en 7.8-10.5 s y las cinco especialidades no se dicen hasta 13.7-18.4."""
    _, html, _ = mockups.agent_swarm(
        "x", "solo", [0.1, 0.3, 0.5, 0.7, 0.9],
        kicker="EN VEZ DE", label="UN SOLO AGENTE", tasks=[["stack", ""]] * 4)
    for palabra in ("FRONTEND", "MARKETING", "CONTENIDO", "COMUNIDAD", "INGENIERÍA"):
        assert palabra not in html.upper()
    assert html.count("aspilebar") == 4, "sin etiqueta, la fila es una barra"


def test_las_bajantes_del_hook_se_DIBUJAN_no_se_funden():
    """Lo que se afirma es que la marca ALCANZA a cada especialista, y un
    fundido solo diría que las líneas existen (la lección de `layer_stack`)."""
    _, _, anims = mockups.agent_swarm("x", "fanout", [0.1, 0.4, 0.9], slug="claude")
    assert sum(1 for a in anims if a[0] == "draw") == 3


# ── desktop_manager ──────────────────────────────────────────────────────────

def test_la_ventana_nace_con_sus_filas_y_lo_que_espera_es_el_ESTADO():
    """Dibujarla vacía durante los segundos previos la leería como un panel
    roto — la trampa que `knowledge-base` documenta con `reveal` y que
    `agent_editor` volvió a pagar con su lienzo negro."""
    _, html, anims = mockups.desktop_manager(
        "x", "Agency Agents",
        [["code", "Frontend"], ["gear", "Ingeniería"]], [0.1, 0.4, 0.8])
    assert "Frontend" in html and "Ingeniería" in html
    # lo único con `opacity:0` de salida son los botones, que son el estado
    assert [a[1] for a in anims if a[0] == "chip-in"] == ["#x-b0", "#x-b1"]


def test_es_una_app_de_escritorio_y_no_un_navegador():
    """Poner `browser_chrome` alrededor diría «esto es una web», que es la
    frase ANTERIOR del guion, no esta."""
    _, html, _ = mockups.desktop_manager("x", "Agency Agents",
                                         [["code", "Frontend"]], [0.1, 0.4])
    assert "dmdots" in html          # el semáforo
    assert "bframe" not in html      # ninguna barra de direcciones


def test_installed_reparte_los_dos_estados_en_el_orden_de_la_lista():
    _, html, _ = mockups.desktop_manager(
        "x", "A", [["code", "a"], ["gear", "b"], ["doc", "c"]], [0.1], installed=2)
    assert html.count("INSTALADO") == 2
    assert html.count("INSTALAR") == 1   # no es subcadena de INSTALADO


# ── split_problem ────────────────────────────────────────────────────────────

def test_el_tachado_vive_en_el_HTML_desde_t0_con_ancho_0():
    """§9, trampa 7: un trazo se prepara en t=0, no al dibujarlo. Inyectarlo en
    el instante de pintarse dejó a GSAP sin destino en la pieza 17 y la raya no
    se dibujaba nunca."""
    css, html, anims = mockups.split_problem(
        "x", "+1 EMPLEADO GRATIS", "PROBLEMA COMPLEJO",
        [["code", "A"], ["gear", "B"], ["megaphone", "C"]],
        [0.1, 0.6, 1.2, 1.8, 2.4])
    assert 'id="x-st"' in html
    assert re.search(r"\.spstrike\{[^}]*width:0", css.replace("\n", ""))
    grow = [a for a in anims if a[0] == "grow-x"]
    assert len(grow) == 1 and grow[0][1] == "#x-st"


def test_el_tachado_mide_el_TEXTO_y_no_la_tarjeta():
    """`grow-x` anima un `width` en píxeles: `width:100%` cruzaría también el
    vacío de detrás de la última palabra y se leería como una raya suelta
    (pieza 17). Se mide con la MISMA woff2 que renderiza el navegador."""
    corto = mockups.split_problem("x", "GRATIS", "P", [["code", "A"]] * 3,
                                  [0.1, 0.6, 1.2, 1.8, 2.4])[2]
    largo = mockups.split_problem("x", "+1 EMPLEADO GRATIS", "P", [["code", "A"]] * 3,
                                  [0.1, 0.6, 1.2, 1.8, 2.4])[2]
    wc = [a[4] for a in corto if a[0] == "grow-x"][0]
    wl = [a[4] for a in largo if a[0] == "grow-x"][0]
    assert wl > wc > 0
    assert abs(wc - mockups.text_px("GRATIS", 46, 800)) < 1.0


def test_el_hueco_de_la_lectura_facil_se_DIBUJA_y_se_retira_con_su_palabra():
    """El idioma que `calendar` usa para la hora sin paciente y `tool_pair`
    para la marca que todavía no se ha dicho. Resuelve un choque concreto: el
    beat abre 2.3 s antes de que la tarjeta pueda decir «EMPLEADO GRATIS»."""
    _, html, anims = mockups.split_problem(
        "x", "+1 EMPLEADO GRATIS", "P", [["code", "A"]] * 3,
        [0.1, 0.6, 1.2, 1.8, 2.4])
    assert 'id="x-slot"' in html
    entra = [a for a in anims if a[1] == "#x-slot" and a[0] == "chip-in"][0]
    sale = [a for a in anims if a[1] == "#x-slot" and a[0] == "badge-out"][0]
    hire = [a for a in anims if a[1] == "#x-hire"][0]
    assert entra[2] == 0.1
    assert sale[2] == hire[2] == 0.6, "el hueco se retira EN la palabra, no antes"


def test_las_bajantes_del_reparto_se_dibujan():
    _, _, anims = mockups.split_problem(
        "x", "A", "P", [["code", "A"]] * 3, [0.1, 0.6, 1.2, 1.8, 2.4])
    assert sum(1 for a in anims if a[0] == "draw") == 3


def test_el_parametro_se_llama_specialists_y_no_parts():
    """`absolute_times` trata `parts` como la lista de DICTS de `rewrite_line` y
    le resta el inicio a `pt["at"]`: una lista de tuplas con ese nombre revienta
    la compilación con un `TypeError`. Pasó de verdad."""
    import inspect
    firma = inspect.signature(mockups.split_problem).parameters
    assert "specialists" in firma and "parts" not in firma


# ── las dos extensiones: sin iconos, no cambia NADA ──────────────────────────

def test_chip_grid_sin_iconos_emite_el_marcado_de_siempre():
    """Las piezas 3, 11 y 16 lo usan; el golden las fija, pero esto lo dice con
    nombre en vez de con un diff de 400 líneas."""
    sin = mockups.chip_grid("x", ["A", "B"], [0.1, 0.4])
    con = mockups.chip_grid("x", ["A", "B"], [0.1, 0.4],
                            icons_=["code", "gear"])
    assert "cgic" not in sin[1] and "cgic" in con[1]
    assert sin[2] == con[2], "los iconos no tocan la coreografía"


def test_flow_steps_sin_iconos_emite_el_marcado_de_siempre():
    sin = mockups.flow_steps("x", ["A", "B"], [0.1, 0.4])
    con = mockups.flow_steps("x", ["A", "B"], [0.1, 0.4], icons_=["strategy", "build"])
    assert '<span class="fic">' not in sin[1]
    assert con[1].count('<span class="fic">') == 2
    assert sin[2] == con[2]


def test_una_lista_de_iconos_mas_corta_no_revienta_sino_que_deja_el_resto_pelado():
    _, html, _ = mockups.chip_grid("x", ["A", "B", "C"], [0.1, 0.4, 0.7],
                                   icons_=["code"])
    assert html.count("cgic") == 1


@pytest.mark.parametrize("make", TODOS, ids=lambda f: "componente")
def test_ningun_componente_nuevo_mete_un_emoji(make):
    """§14: el navegador lo pinta con su propia paleta pero el linter lee el
    `color` heredado. El 💡 de `idea_fate` daba 1.11:1 y tiraba la pieza
    entera, viéndose perfecto en pantalla."""
    _, html, _ = make()
    assert not re.search(r"[\U0001F300-\U0001FAFF☀-➿]", html)
