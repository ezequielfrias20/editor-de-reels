"""Los cuatro componentes de la pieza 20 y los iconos de su cadena.

Como en la 19, casi todo lo que hay aquí sale de un fallo que `check` daba por
bueno —o por un simple `info`— y que solo se vio extrayendo el frame.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import icons  # noqa: E402
import mockups  # noqa: E402


PASOS = [["tema", "TEMA"], ["guion", "GUIÓN"], ["material", "MATERIAL"],
         ["narracion", "NARRACIÓN"], ["subtitulos", "SUBTÍTULOS"],
         ["musica", "MÚSICA"], ["render", "RENDER"]]

TODOS = [
    lambda: mockups.video_pipeline(
        "x", "manual", [0.03, 4.18] + [1.9 + i * .25 for i in range(7)],
        n=7, out_label="VÍDEO", tag="FACELESS"),
    lambda: mockups.video_pipeline(
        "x", "auto", [9.2, 21.0] + [11.7 + i * 1.4 for i in range(7)],
        n=7, steps=PASOS, out_label="VÍDEO", tag="LISTO"),
    lambda: mockups.video_pipeline(
        "x", "gap", [30.0, 30.4] + [30.5 + i * .08 for i in range(7)] + [36.2],
        n=7, steps=PASOS, gap_label="CRITERIO", out_label="VÍDEO", tag="LISTO"),
    lambda: mockups.money_button(
        "x", "GANAR DINERO", [25.7, 27.6, 28.0, 28.5, 29.2],
        question="¿Un botón para ganar dinero?", empty_label="VACÍO"),
    lambda: mockups.video_output(
        "x", [37.7, 39.5, 40.7, 41.2, 42.0, 42.9, 43.5, 44.6],
        inputs=[["tema", "TEMA"], ["guion", "GUIÓN"]], seal="NADIE LO VE"),
    lambda: mockups.tradeoff_bars(
        "x", [{"icon": "gear", "name": "EJECUCIÓN", "from": 880, "to": 300,
               "shrink": True, "tag": "SE COMPRIME"},
              {"icon": "strategy", "name": "ESTRATEGIA", "from": 880,
               "to": 880, "tag": "NO SE SALTA"}],
        [45.4, 47.1, 49.0, 47.5, 47.9, 49.4]),
]


@pytest.mark.parametrize("make", TODOS, ids=lambda f: "componente")
def test_ningun_selector_trae_el_prefijo_del_host(make):
    """`build_visuals` antepone `.viz[data-viz-id="…"]`. Prefijarlo aquí lo
    duplica y GSAP no encuentra el destino: `check` lo cuenta como aviso de
    runtime con 0 errores y el gesto no ocurre (la lección de la pieza 19)."""
    _, _, anims = make()
    for a in anims:
        assert "data-viz-id" not in a[1], f"selector ya prefijado: {a[1]}"


@pytest.mark.parametrize("make", TODOS, ids=lambda f: "componente")
def test_ningun_componente_mete_un_emoji(make):
    """§14: el navegador lo pinta con su paleta y el linter lee el `color`
    heredado — el 💡 de la pieza 18 daba 1.11:1 viéndose perfecto."""
    _, html, _ = make()
    assert not re.search(r"[\U0001F300-\U0001FAFF☀-➿]", html)


# ── video_pipeline: la espina de la pieza ────────────────────────────────────

def test_las_tres_variantes_comparten_la_geometria():
    """Es lo ÚNICO que hace que el espectador lea «la misma cadena» tres veces
    y no tres gráficos distintos. Si esto se rompe, la rima se pierde sin que
    nada falle."""
    hs = []
    for v, kw in (("manual", {}), ("auto", {"steps": PASOS}),
                  ("gap", {"steps": PASOS, "gap_label": "CRITERIO"})):
        css, html, _ = mockups.video_pipeline(
            "x", v, [0.1, 0.5] + [1.0 + i * .2 for i in range(7)] + [9.0],
            n=7, **kw)
        hs.append(html)
        assert html.count('class="vpcell vpslot"') == 7
    assert "vpgap" in hs[2] and "vpgap" not in hs[0] and "vpgap" not in hs[1]


def test_el_hook_no_nombra_ninguna_de_las_siete_etapas():
    """«Nada entra antes de su palabra» (§7): el hook cae en 0-6 s y las siete
    palabras no se dicen hasta 11.2-21.0. Lo que el frame afirma es CUÁNTAS
    son, no cuáles."""
    _, html, _ = mockups.video_pipeline(
        "x", "manual", [0.03, 4.18] + [1.9 + i * .25 for i in range(7)], n=7)
    for palabra in ("TEMA", "GUIÓN", "MATERIAL", "NARRACIÓN",
                    "SUBTÍTULOS", "MÚSICA", "RENDER"):
        assert palabra not in html.upper()


def test_la_etiqueta_de_salida_espera_su_palabra_y_su_hueco_se_DIBUJA():
    """Medido sobre el frame de t=3.6: con la mitad derecha de la tarjeta lisa
    se leía como un panel a medio hacer — la trampa que `knowledge-base`
    documenta con `reveal`. El hueco discontinuo lo cubre y el texto lo tapa."""
    _, html, anims = mockups.video_pipeline(
        "x", "manual", [0.03, 4.18] + [1.9 + i * .25 for i in range(7)],
        n=7, out_label="VÍDEO", tag="FACELESS")
    assert 'id="x-outslot"' in html
    slot_out = [a for a in anims if a[1] == "#x-outslot"][0]
    texto = [a for a in anims if a[1] == "#x-outx"][0]
    assert slot_out[0] == "badge-out" and texto[0] == "slide-in"
    assert slot_out[2] == texto[2] == 4.18, "el hueco se retira EN la palabra"


def test_el_nombre_de_una_etapa_cabe_en_la_casilla_mas_estrecha():
    """La casilla de la variante `gap` mide 107 px porque el hueco de delante
    le quita ancho a la fila. A 17px y tracking .08em «SUBTÍTULOS» ocupaba 123
    y desbordaba 4.5 px por lado — el linter lo dio como `info`, con 0 errores
    y 0 avisos, que es justo lo que se pasa por alto."""
    ancho = mockups.text_px("SUBTÍTULOS", 15, 700) + .03 * 15 * len("SUBTÍTULOS")
    assert ancho < 107, f"{ancho:.0f} px no cabe en 107"


def test_el_hueco_del_criterio_espera_su_palabra():
    _, html, anims = mockups.video_pipeline(
        "x", "gap", [30.0, 30.4] + [30.5 + i * .08 for i in range(7)] + [36.2],
        n=7, steps=PASOS, gap_label="CRITERIO")
    caja = [a for a in anims if a[1] == "#x-gap"][0]
    nombre = [a for a in anims if a[1] == "#x-gapn"][0]
    assert caja[2] == 30.0 and nombre[2] == 36.2


def test_una_variante_desconocida_LANZA():
    """El camino de FALLO. Un gate que nunca ha fallado no es un gate."""
    with pytest.raises(ValueError) as e:
        mockups.video_pipeline("x", "cadena", [0.1, 0.2])
    assert "cadena" in str(e.value)


# ── money_button ─────────────────────────────────────────────────────────────

def test_la_bandeja_esta_dibujada_ANTES_de_que_se_pulse():
    """Si apareciera con el «No», el frame diría «y entonces salió una
    bandeja». Lo que dice la frase es que siempre estuvo vacía."""
    _, html, anims = mockups.money_button(
        "x", "GANAR DINERO", [25.7, 27.6, 28.0, 28.5, 29.2],
        question="¿Un botón?", empty_label="VACÍO")
    tray = [a for a in anims if a[1] == "#x-tray"][0]
    clic = [a for a in anims if a[0] == "click"][0]
    vacio = [a for a in anims if a[1] == "#x-empty"][0]
    assert tray[2] < clic[2] < vacio[2]
    assert 'id="x-tray"' in html


def test_nada_se_tine_de_rojo_en_el_boton():
    """Rojo diría «el botón falla». El botón funciona; lo que no existe es lo
    que se esperaba que saliera. Misma lógica que las salidas apagadas de
    `idea_fate` y que el hueco de `calendar`."""
    from tokens import C
    css, _, _ = mockups.money_button("x", "GANAR DINERO",
                                     [25.7, 27.6, 28.0, 28.5, 29.2],
                                     empty_label="VACÍO")
    assert C["alert"] not in css


# ── video_output ─────────────────────────────────────────────────────────────

def test_el_cero_no_es_un_error_y_no_va_en_rojo():
    from tokens import C
    css, html, _ = mockups.video_output(
        "x", [37.7, 39.5, 40.7, 41.2, 42.0, 42.9, 43.5, 44.6],
        inputs=[["tema", "TEMA"], ["guion", "GUIÓN"]], seal="NADIE LO VE")
    assert C["alert"] not in css
    assert "✕" not in html and "✗" not in html
    assert html.count('class="voviews"') == 4


def test_las_entradas_llevan_barra_discontinua_y_no_texto():
    """Lo que las descalifica no es lo que dicen, es que da igual lo que
    digan."""
    _, html, _ = mockups.video_output(
        "x", [37.7, 39.5, 40.7, 41.2, 42.0, 42.9, 43.5, 44.6],
        inputs=[["tema", "TEMA"], ["guion", "GUIÓN"]])
    assert html.count("voinbar") == 2


def test_las_entradas_se_animan_antes_que_la_maquina():
    """Existen porque el beat empieza cuatro segundos antes de que caiga el
    primer vídeo: sin ellas la banda pasaba ese tramo con una máquina sola."""
    _, _, anims = mockups.video_output(
        "x", [37.7, 39.5, 40.7, 41.2, 42.0, 42.9, 43.5, 44.6],
        inputs=[["tema", "TEMA"], ["guion", "GUIÓN"]])
    i0 = [a for a in anims if a[1] == "#x-i0"][0][2]
    i1 = [a for a in anims if a[1] == "#x-i1"][0][2]
    maq = [a for a in anims if a[1] == "#x-m"][0][2]
    assert i0 == 37.7 and i1 == 39.5 and maq == 40.7


def test_sin_entradas_la_maquina_sigue_siendo_el_primer_tiempo():
    """Retrocompatibilidad del contrato: `inputs` es opcional."""
    _, _, anims = mockups.video_output("x", [1.0, 1.4, 1.8, 2.2, 2.6, 3.0])
    assert [a for a in anims if a[1] == "#x-m"][0][2] == 1.0


# ── tradeoff_bars ────────────────────────────────────────────────────────────

def test_la_barra_que_no_cambia_no_recibe_NINGUN_tween():
    """La lección de `idea_veneer` (pieza 18): si se encogiera un poco o se
    tiñera, el frame diría «y a esta también le pasó algo», y lo que la frase
    afirma es que no le pasa nada."""
    _, _, anims = mockups.tradeoff_bars(
        "x", [{"icon": "gear", "name": "EJECUCIÓN", "from": 880, "to": 300,
               "shrink": True, "tag": "A"},
              {"icon": "strategy", "name": "ESTRATEGIA", "from": 880,
               "to": 880, "tag": "B"}],
        [45.4, 47.1, 49.0, 47.5, 47.9, 49.4])
    sobre_f1 = [a for a in anims if a[1] == "#x-f1"]
    assert sobre_f1 == [], "la barra intacta no se anima"
    grow = [a for a in anims if a[0] == "grow-x"]
    assert len(grow) == 1 and grow[0][1] == "#x-f0" and grow[0][4] == 300


def test_los_railes_entran_antes_que_los_nombres():
    """El beat abre 1.7 s antes de «ejecución» y 3.6 antes de «estrategia»:
    rotular los raíles ahí sería leer la tesis antes de oírla. Es el mecanismo
    de `step_grid` (pieza 17)."""
    _, html, anims = mockups.tradeoff_bars(
        "x", [{"icon": "gear", "name": "EJECUCIÓN", "from": 880, "to": 300,
               "shrink": True},
              {"icon": "strategy", "name": "ESTRATEGIA", "from": 880, "to": 880}],
        [45.4, 47.1, 49.0, 47.5])
    assert 'id="x-rails"' in html
    rails = [a for a in anims if a[1] == "#x-rails"][0][2]
    r0 = [a for a in anims if a[1] == "#x-r0"][0][2]
    r1 = [a for a in anims if a[1] == "#x-r1"][0][2]
    assert rails == 45.4 < r0 == 47.1 < r1 == 49.0


# ── los iconos de la cadena ──────────────────────────────────────────────────

NUEVOS = ["spark", "image", "mic", "captions", "music", "film",
          "eye", "clock", "pointer"]


@pytest.mark.parametrize("name", NUEVOS)
def test_los_iconos_nuevos_cumplen_el_contrato(name):
    svg = icons.icon(name, 40)
    assert 'stroke="currentColor"' in svg
    assert not re.search(r'(fill|stroke)="#', svg)
    assert not re.search(r'(?<![-\w])id="', svg)
    assert f'viewBox="{icons.VIEWBOX}"' in svg


def test_los_alias_de_la_cadena_apuntan_a_su_dibujo():
    for alias, real in (("tema", "spark"), ("guion", "doc"),
                        ("material", "image"), ("narracion", "mic"),
                        ("subtitulos", "captions"), ("musica", "music"),
                        ("render", "film")):
        assert icons.icon(alias, 40) == icons.icon(real, 40)
