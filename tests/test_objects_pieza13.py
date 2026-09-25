"""Los tres objetos de la pieza 13.

Tres, no cinco: los mensajes de la secuencia se sirven con `msg-card` de la
pieza 12 y su `seal` verde carga la VENTANA DE ENVÍO (INMEDIATA · DÍA ANTERIOR
· 3 H ANTES) en vez de un estado. Es el nivel `library` del Resolver haciendo
su trabajo — reutilizar cuesta cero y no infla la librería.
"""
import pytest

import objects as o
import tokens as t
from asset_resolve import asset_hash

NUEVOS = ("calendar", "appointment-timeline", "confirm-buttons")


@pytest.mark.parametrize("nombre", NUEVOS)
def test_estan_en_el_registry_y_el_manifest_cuadra(nombre, manifest):
    assert nombre in o.REGISTRY
    ref = f"object:{nombre}@1"
    assert manifest["assets"][ref]["hash"] == asset_hash(ref, manifest)


# ── calendar: lo que comunica es la AUSENCIA ─────────────────────────────────
FILAS = [("09:00", "María R."), ("10:00", "Carlos M."), ("11:00", ""),
         ("12:00", "Ana T."), ("13:00", "Luis P.")]


def test_la_franja_vacia_es_un_hueco_no_una_fila_en_rojo():
    """Una fila roja CON texto se leería como «esta cita tiene un problema».
    Un hueco —borde discontinuo, sin relleno— se lee como «aquí no hay
    nadie», que es la frase. Y es más alta que las demás a propósito."""
    r = o.calendar("v", "cal", {"rows": FILAS, "empty": 2}, "center")
    assert f"2px dashed {t.C['alert']}" in r["html"]
    assert "background:transparent" in r["html"]
    assert f"height:{o.CAL_EMPTY_H}px" in r["html"]
    assert o.CAL_EMPTY_H > o.CAL_ROW_H


def test_solo_las_franjas_ocupadas_llevan_punto_verde():
    r = o.calendar("v", "cal", {"rows": FILAS, "empty": 2}, "center")
    assert r["html"].count(f"background:{t.C['go']}") == len(FILAS) - 1


def test_el_rotulo_de_la_hora_perdida_nace_apagado():
    r = o.calendar("v", "cal", {"rows": FILAS, "empty": 2,
                                "label": "HORA PERDIDA"}, "center")
    assert 'id="v-cal-perdida"' in r["html"]
    assert "HORA PERDIDA" in r["html"] and "opacity:0" in r["html"]


def test_el_rotulo_usa_un_tamano_de_la_escala():
    """52 px = TYPE.card_title en REEL: la escala no se extiende con un número
    inventado. A 40 px se leía pero no dominaba, y el brief pide texto grande."""
    assert o.CAL_LABEL_SIZE == t.TYPE["REEL"]["card_title"]


# ── appointment_timeline: el hueco solo cuenta si algo lo mide ───────────────
def test_cuatro_paradas_no_dos():
    """Con solo Reserva y Cita, el tramo del medio NO se leía como días
    pasando: se leía como un panel a medio hacer. Los días intermedios entran
    como nodos huecos SIN evento, y esa ausencia junto a un día que sí existe
    es la frase «nadie vuelve a escribirle»."""
    r = o.appointment_timeline("v", "tl", {}, "center")
    # Se cuenta la COLUMNA de día (width:104px), no la cadena «DÍA»: el rótulo
    # del tramo dice «7 DÍAS DE ANTICIPACIÓN» y la contiene.
    assert r["html"].count("width:104px") == 4
    for dia in ("DÍA 1", "DÍA 3", "DÍA 5", "DÍA 7"):
        assert f">{dia}<" in r["html"]


def test_los_tres_sub_elementos_nacen_apagados():
    r = o.appointment_timeline("v", "tl", {}, "center")
    for sid in ("span", "silencio", "riesgo"):
        assert f'id="v-tl-{sid}"' in r["html"]
    assert r["html"].count("opacity:0") >= 3


def test_el_rail_no_se_pinta_con_el_hairline():
    """A `LINE_HI` (alpha .16) la discontinua se perdía contra el suelo del
    panel en el frame renderizado. Va a `text3`, que es 5.28:1 sobre él."""
    r = o.appointment_timeline("v", "tl", {}, "center")
    assert f"border-left:3px dashed {t.C['text3']}" in r["html"]
    assert t.contrast(t.C["text3"], t.C["surface"]) > 4.5


def test_el_silencio_va_en_alerta_y_el_span_en_neutro():
    """El tramo se MIDE en neutro y lo que falta dentro se marca en rojo: dos
    rótulos del mismo color leerían las dos cosas como el mismo problema."""
    r = o.appointment_timeline("v", "tl", {}, "center")
    span = r["html"][r["html"].index('id="v-tl-span"'):]
    span = span[:span.index("</span>")]
    sil = r["html"][r["html"].index('id="v-tl-silencio"'):]
    sil = sil[:sil.index("</span>")]
    assert t.C["alert"] not in span and t.C["alert"] in sil


# ── confirm_buttons: dos opciones, no dos iguales ───────────────────────────
def test_el_primario_lleva_verde_con_tinta_y_el_otro_no():
    """Sobre relleno verde va TINTA `bg` (11.74:1); blanco daría 1.66:1. Y dos
    botones al mismo peso no son una decisión: el paciente tiene que ver cuál
    es la que se espera."""
    r = o.confirm_buttons("v", "b", {}, "stack-3")
    assert f"background:{t.C['go']}" in r["html"]
    assert f"color:{t.C['bg']}" in r["html"]
    assert t.contrast(t.C["bg"], t.C["go"]) > 4.5
    assert f"background:{t.C['surface2']}" in r["html"]


def test_el_check_nace_apagado():
    r = o.confirm_buttons("v", "b", {}, "stack-3")
    assert 'id="v-b-check"' in r["html"] and "opacity:0" in r["html"]


# ── el reuso, que es el punto ────────────────────────────────────────────────
