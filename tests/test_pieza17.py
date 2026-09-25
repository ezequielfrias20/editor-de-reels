"""Pieza 17 — el CV y sus cuatro pasos.

Casi todos estos tests nacen de un fallo que **`hyperframes check` daba por
bueno** y que solo se vio extrayendo el frame. Es la regla dura del proyecto
(«no dar por buena una animación sin mirar el frame») convertida en red: lo que
se mira una vez a mano, aquí se mira en cada corrida.
"""
import re

import pytest

import mockups


CV_ROWS = [
    {"label": "Campañas de performance", "w": 86},
    {"label": "Analítica y reporting", "w": 52},
    {"label": "SQL", "w": 22},
    {"label": "Automatización", "w": 16},
]


# ── step_grid: la casilla pendiente es un HUECO ──────────────────────────────
def test_la_casilla_pendiente_se_dibuja_como_hueco_no_como_caja_vacia():
    """El fallo del snapshot en t=11: la casilla con `at` puesto nacía con el
    relleno sólido y sin texto, o sea una caja vacía entre tres huecos — la
    lectura de «panel roto» que `knowledge-base` ya documenta."""
    _, html, _ = mockups.step_grid(
        "g", ["DIAGNÓSTICO", "", "", ""], [2.0, None, None, None])
    # El relleno es una capa aparte que entra en su palabra, no una clase fija.
    assert 'class="sgfill" id="g-f0"' in html
    assert "g-f1" not in html, "una casilla sin `at` no puede traer relleno"
    # Y las cuatro casillas nacen con el borde discontinuo.
    assert html.count("sgdash") == 4


def test_el_relleno_y_el_texto_entran_en_LA_MISMA_palabra():
    _, _, anims = mockups.step_grid("g", ["DIAGNÓSTICO", "", "", ""],
                                    [2.0, None, None, None])
    por_sel = {a[1]: a for a in anims}
    assert por_sel["#g-f0"][2] == 2.0, "el relleno entra en la palabra"
    assert por_sel["#g-t0"][2] == 2.0, "el texto entra en la palabra"
    assert por_sel["#g-d0"][2] == 2.0, "y la raya se apaga en ese mismo instante"


def test_el_texto_se_emite_siempre_para_que_la_rejilla_no_salte():
    """Pendiente y llena tienen que MEDIR lo mismo, o la rejilla da un salto de
    layout al llenarse una casilla."""
    _, vacia, _ = mockups.step_grid("g", ["", "", "", ""], [None] * 4)
    _, llena, _ = mockups.step_grid("g", ["A", "B", "C", "D"], [1, 2, 3, 4])
    assert vacia.count("sgtxt") == llena.count("sgtxt") == 4


def test_el_texto_no_se_saca_del_flujo_encima_del_numero():
    """Sacarlo con `position:absolute` dio 14 errores de `content_overlap`."""
    css, _, _ = mockups.step_grid("g", ["A", "", "", ""], [1.0, None, None, None])
    regla = re.search(r"\.sgtxt\{([^}]*)\}", css).group(1)
    assert "position:relative" in regla
    assert "min-height" in regla, "sin alto mínimo, la casilla vacía encoge"


def test_un_hueco_nunca_lleva_su_nombre_puesto():
    """El choque que resolvió el usuario: la estructura entra entera, los
    nombres esperan su palabra."""
    _, html, _ = mockups.step_grid(
        "g", ["DIAGNÓSTICO", "KEYWORDS", "REESCRITURA", "ENTREVISTA"],
        [2.0, None, None, None])
    assert "DIAGNÓSTICO" in html
    for futuro in ("KEYWORDS", "REESCRITURA", "ENTREVISTA"):
        assert futuro not in html, f"«{futuro}» entra antes de su palabra"


# ── el adjunto de claude_prompt ─────────────────────────────────────────────
def test_el_adjunto_apaga_el_placeholder_aunque_llegue_antes_que_el_texto():
    """Si solo lo apagara la primera línea, el campo pasaría unos frames con la
    ficha del archivo puesta y el placeholder debajo."""
    _, _, anims = mockups.claude_prompt(
        "c", ["Mejora mi currículum"], [4.3],
        attachment={"name": "CV.pdf", "meta": "PDF"}, attach_at=2.7)
    ph = [a for a in anims if a[1].endswith("-ph")]
    assert len(ph) == 1 and ph[0][2] == 2.7


def test_sin_adjunto_el_placeholder_sigue_apagandose_con_la_primera_linea():
    """La pieza 16 no lleva adjunto y no puede cambiar de comportamiento."""
    _, _, anims = mockups.claude_prompt("c", ["Hola"], [1.5])
    ph = [a for a in anims if a[1].endswith("-ph")]
    assert len(ph) == 1 and ph[0][2] == 1.5


def test_el_adjunto_vive_en_el_campo_no_en_la_barra():
    _, html, _ = mockups.claude_prompt(
        "c", [], [], attachment={"name": "CV.pdf", "meta": "PDF"}, attach_at=1.0)
    cuerpo = html[html.index('class="cp-body"'):html.index('class="cp-bar"')]
    assert 'class="cp-att"' in cuerpo


# ── rewrite_line: el trazo se PREPARA en t=0 ────────────────────────────────
def test_el_tachado_existe_en_el_html_desde_el_primer_frame():
    """Inyectarlo con `caret-off` a mitad del timeline dejaba a GSAP sin
    destino: `target #…-st not found`, y la raya no se dibujaba nunca. Es la
    trampa 7 de §9 con otra cara."""
    _, html, _ = mockups.rewrite_line(
        "r", "Era responsable de las campañas", "Bajé el CAC un 32 %",
        [{"text": "32 %", "label": "MÉTRICA", "at": 3.0}], 0.5, 1.5, 2.0)
    assert 'class="rwstrike" id="r-st"' in html


def test_el_tachado_no_vive_dentro_del_elemento_que_se_teclea():
    """`type-word` reescribe el innerHTML de su destino: cualquier cosa que
    viva dentro se pierde al teclear."""
    _, html, _ = mockups.rewrite_line(
        "r", "Era responsable", "Bajé el CAC", [], 0.5, 1.5, 2.0)
    antes = html[html.index('id="r-before"'):]
    assert antes.startswith('id="r-before" data-layout-allow-occlusion></div>')


def test_el_tachado_mide_el_texto_y_no_el_ancho_de_la_tarjeta():
    _, _, anims = mockups.rewrite_line(
        "r", "Era responsable de las campañas", "Bajé el CAC", [], 0.5, 1.5, 2.0)
    grow = [a for a in anims if a[0] == "grow-x"][0]
    medido = mockups.text_px("Era responsable de las campañas", 34, 700)
    assert grow[4] == round(medido)
    assert grow[4] < mockups.BOARD_W, "una raya al ancho de la tarjeta cruza el vacío"


def test_un_fragmento_que_no_esta_en_la_frase_falla_en_vez_de_perderse():
    with pytest.raises(ValueError):
        mockups.rewrite_line("r", "antes", "después",
                             [{"text": "NO ESTÁ", "label": "X", "at": 1.0}],
                             0.5, 1.5, 2.0)


def test_text_px_mide_con_la_woff2_vendorizada():
    """Si midiera con una fuente del sistema, el número dependería de la
    máquina y la raya saldría corta o pasada en otro ordenador."""
    a = mockups.text_px("Era responsable de las campañas", 34, 700)
    assert 500 < a < 600
    assert mockups.text_px("AA", 34, 700) < mockups.text_px("AAAA", 34, 700)


# ── cv_vs_offer: las marcas se anclan a las FILAS ───────────────────────────
def test_las_marcas_de_desajuste_viven_dentro_del_contenedor_de_filas():
    """Colgadas de la tarjeta con un `top` calculado a mano, subir la etiqueta
    a su propia fila las dejó una fila por encima de la suya. Ancladas a las
    filas, el alto de la cabecera deja de importar."""
    _, html, _ = mockups.cv_vs_offer(
        "d", {"title": "A", "sub": "b", "rows": CV_ROWS},
        {"title": "B", "sub": "c", "rows": CV_ROWS}, [0.0, 0.5], [1, 2, 3], 3.0)
    filas = html[html.index('class="cvrows"'):]
    filas = filas[:filas.index("</div></div>")]
    assert filas.count('class="cvx"') == 3


def test_el_top_de_una_marca_solo_depende_del_pitch_de_fila():
    _, html, _ = mockups.cv_vs_offer(
        "d", {"title": "A", "sub": "b", "rows": CV_ROWS},
        {"title": "B", "sub": "c", "rows": CV_ROWS}, [0.0, 0.5], [0, 2], 3.0)
    tops = [int(m) for m in re.findall(r'class="cvx"[^>]*top:(\d+)px', html)]
    assert tops == [1, 121], "pitch 60: fila 0 -> 1, fila 2 -> 121"


def test_los_desajustes_se_marcan_en_el_lado_del_CV():
    """El que tiene el hueco es el candidato, no la oferta."""
    _, html, _ = mockups.cv_vs_offer(
        "d", {"title": "A", "sub": "b", "rows": CV_ROWS},
        {"title": "B", "sub": "c", "rows": CV_ROWS}, [0.0, 0.5], [1], 3.0)
    cv = html[html.index('id="d-CV"'):html.index('id="d-OF"')]
    assert 'class="cvx"' in cv
    assert 'class="cvx"' not in html[html.index('id="d-OF"'):]


def test_los_desajustes_entran_todos_en_la_palabra_desajustes():
    _, _, anims = mockups.cv_vs_offer(
        "d", {"title": "A", "sub": "b", "rows": CV_ROWS},
        {"title": "B", "sub": "c", "rows": CV_ROWS}, [0.0, 0.5], [1, 2, 3], 3.0)
    marcas = sorted(a[2] for a in anims if "-x" in a[1])
    assert max(marcas) - min(marcas) < 0.25, "el guion los enuncia como uno solo"


# ── la pastilla central necesita hueco ──────────────────────────────────────
@pytest.mark.parametrize("fn,args", [
    ("cv_echo", None),
    ("cv_vs_offer", None),
])
def test_el_par_de_tarjetas_deja_sitio_para_la_pastilla_del_medio(fn, args):
    """452+24+452 montaba el `=` y el `VS` encima de la tarjeta derecha:
    «Growth» se leía «3rowth». Cazado sobre frames, nunca en el JSON."""
    doc = {"title": "A", "sub": "b", "rows": CV_ROWS}
    if fn == "cv_echo":
        css, _, _ = mockups.cv_echo("x", doc, doc, "S", [0.0, 0.3, 1.0])
        gap = re.search(r"\.cepair\{[^}]*gap:(\d+)px", css)
        ancho = re.search(r"\.ceeq\{[^}]*width:(\d+)px", css)
    else:
        css, _, _ = mockups.cv_vs_offer("x", doc, doc, [0.0, 0.3], [1], 2.0)
        gap = re.search(r"\.covs\{[^}]*width:(\d+)px", css)
        ancho = gap
        gap = re.search(r"\.copair\{[^}]*gap:(\d+)px", css)
    assert int(gap.group(1)) >= int(ancho.group(1)), (
        "la pastilla no cabe en el hueco y se monta sobre la tarjeta")


def test_las_dos_tarjetas_suman_el_ancho_del_tablero():
    doc = {"title": "A", "sub": "b", "rows": CV_ROWS}
    css, _, _ = mockups.cv_vs_offer("x", doc, doc, [0.0, 0.3], [1], 2.0)
    w = int(re.search(r"#x-CV\{width:(\d+)px", css).group(1))
    gap = int(re.search(r"\.copair\{[^}]*gap:(\d+)px", css).group(1))
    assert w * 2 + gap == mockups.BOARD_W


# ── offer_stack ─────────────────────────────────────────────────────────────
def test_lo_que_falta_se_dibuja_como_hueco_no_en_rojo():
    """Un chip rojo diría «esta competencia tiene un problema»; un hueco dice
    «aquí no hay nada», que es la frase. Mismo idioma que `calendar`."""
    css, html, _ = mockups.offer_stack(
        "o", ["A"], [0.0], ["SQL"], [1.0], ["SQL"], 2.0)
    regla = re.search(r"\.ofchip\.gap\{([^}]*)\}", css).group(1)
    assert "dashed" in regla and "transparent" in regla
    assert "alert" not in regla


def test_las_barras_del_documento_se_ven_sobre_la_superficie():
    """`surface3` sobre `surface` es casi invisible: las barras del CV no se
    leían como contenido en el frame."""
    import tokens
    css, _ = mockups._cv_card("c", "c-a", "A", "b", CV_ROWS, 440)
    css += mockups._cv_css(".viz")
    assert tokens.C["surface3"] not in re.search(
        r"\.cvbar\{([^}]*)\}", css).group(1)
