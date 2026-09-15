"""Los dos objetos de la pieza 14.

Dos, no cinco: la regla («DATO SIN ACCIÓN = RUIDO») es un RÓTULO sobre su cara
y no un objeto, y el teaser del CTA se sirve con el `msgteaser` de la 13. Lo
que de verdad hacía falta dibujar era el problema —una rejilla llena— y la
unidad que lo resuelve —un indicador con su decisión al lado.
"""
import pytest

import objects as o
import tokens as t
from asset_resolve import asset_hash

NUEVOS = ("spreadsheet", "kpi-card")


@pytest.mark.parametrize("nombre", NUEVOS)
def test_estan_en_el_registry_y_el_manifest_cuadra(nombre, manifest):
    assert nombre in o.REGISTRY
    ref = f"object:{nombre}@1"
    assert manifest["assets"][ref]["hash"] == asset_hash(ref, manifest)


# ── spreadsheet: es una REJILLA, no una lista ────────────────────────────────
COLS = ["FECHA", "SUCURSAL", "PRODUCTO", "TOTAL"]


def test_tiene_separadores_de_columna_y_por_eso_no_es_knowledge_base():
    """La diferencia con `knowledge-base` no es cosmética: «cientos de filas»
    es una TABLA. Sin separadores verticales, una columna de barras grises se
    lee como una lista de pendientes y el beat se pierde. Un separador por
    cada columna menos la primera, en la cabecera y en cada fila."""
    r = o.spreadsheet("v", "ss", {"cols": COLS, "rows": 11}, "center")
    esperados = (len(COLS) - 1) * (11 + 1)      # 11 filas + la cabecera
    assert r["html"].count(f"border-left:1px solid {t.LINE}") == esperados


def test_las_tres_revelaciones_nacen_apagadas():
    """Nada entra antes de su palabra: el conteo en «cientos», la cifra en
    «valiosa» y los interrogantes en «manualmente»."""
    r = o.spreadsheet("v", "ss", {"cols": COLS}, "center")
    for sufijo in ("conteo", "valiosa", "preguntas"):
        assert f'id="v-ss-{sufijo}"' in r["html"]
    assert r["html"].count("opacity:0") == 3


def test_la_cifra_se_pone_ENCIMA_de_la_barra_y_no_en_su_lugar():
    """Si la celda naciera vacía esperando su cifra, la rejilla tendría un
    hueco durante los segundos previos a su palabra y se leería como un panel
    roto — la misma trampa que `knowledge-base` documenta con `reveal`. La
    barra sigue puesta: hay tantas barras como celdas."""
    r = o.spreadsheet("v", "ss", {"cols": COLS, "rows": 11}, "center")
    assert r["html"].count(f"background:{t.LINE_HI};display:block") == 11 * len(COLS)


def test_los_interrogantes_van_en_currentColor():
    """Así los tiñe el tema del stage (`problem` -> alert) en vez de traer un
    color propio que habría que volver a justificar en cada uso."""
    r = o.spreadsheet("v", "ss", {"cols": COLS}, "center")
    assert r["html"].count("color:currentColor;opacity:.92") == 3
    assert t.C["alert"] not in r["html"]


def test_el_interrogante_sale_de_la_escala_de_tipografia():
    """132 px = TYPE.display en REEL. Es un titular, no un adorno, y no
    inventa un tamaño fuera de la escala."""
    assert o.SS_Q_SIZE == t.TYPE["REEL"]["display"]


def test_las_barras_son_deterministas():
    """Un golden file no puede depender de un `random`, y el dato concreto de
    cada celda no es el argumento: el VOLUMEN lo es."""
    a = o.spreadsheet("v", "ss", {"cols": COLS}, "center")["html"]
    b = o.spreadsheet("v", "ss", {"cols": COLS}, "center")["html"]
    assert a == b


# ── kpi-card: pregunta, cifra y la decisión que provoca ──────────────────────
UNO = {"q": "QUÉ PRODUCTO NECESITA REPOSICIÓN", "value": "Filtro A-20 · 6 u.",
       "action": "REPONER"}


def test_la_pastilla_de_accion_nace_apagada():
    r = o.kpi_card("v", "k3", UNO, "stack-3")
    assert 'id="v-k3-accion"' in r["html"]
    assert "opacity:0" in r["html"]
    assert "REPONER" in r["html"]


def test_sobre_verde_va_tinta_bg_y_nunca_blanco():
    """bg/go = 11.74:1; blanco/go = 1.66:1. La misma regla que `msg-card`."""
    r = o.kpi_card("v", "k3", UNO, "stack-3")
    assert f"background:{t.C['go']};color:{t.C['bg']}" in r["html"]
    assert t.contrast(t.C["bg"], t.C["go"]) > 7
    assert t.contrast(t.C["text"], t.C["go"]) < 3


def test_sin_accion_no_hay_pastilla():
    """Un indicador sin decisión asociada es exactamente lo que el reel llama
    ruido; el objeto no la inventa."""
    r = o.kpi_card("v", "k1", {"q": "Q", "value": "V"}, "stack-1")
    assert "-accion" not in r["html"]


def test_la_pregunta_y_la_cifra_conviven_en_la_misma_tarjeta():
    """Sin la pregunta arriba es un número suelto — justo lo que la pieza dice
    que no sirve — y sin la cifra es un enunciado sin dato."""
    r = o.kpi_card("v", "k3", UNO, "stack-3")
    assert UNO["q"] in r["html"] and UNO["value"] in r["html"]


def test_cuatro_tarjetas_caben_en_los_cuatro_slots_stack():
    """Los `stack` van cada 160 px: una tarjeta más alta que eso haría que la
    segunda se montara sobre la primera, y el linter de layout no lo ve porque
    los objetos llevan `data-layout-allow-overflow`."""
    sep = t.SLOTS["stack-2"][1] - t.SLOTS["stack-1"][1]
    assert o.KPI_CARD_H < sep
    ultima = t.SLOTS["stack-4"][1] + o.KPI_CARD_H // 2
    assert ultima < 1536, "la cuarta tarjeta entra en la interfaz de la plataforma"
