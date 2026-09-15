"""El evento CARD — la capa de rótulos, anclada a palabras.

POR QUÉ EXISTE ESTE EVENTO. Hasta la pieza 12 el camino del EDL emitía
`"cards": []` fijo, así que lo único que podía acompañar al presentador era el
subtítulo. Un rótulo no es un stage más pequeño: el stage SUSTITUYE la cara y
el rótulo la ACOMPAÑA, y hay frases —«escalar a un humano», dicha por un
humano— en las que esa diferencia es el argumento.

Lo que se prueba aquí es sobre todo lo que NO se puede escribir: las cuatro
formas de declarar un rótulo que renderizaría algo distinto de lo que el autor
cree que declaró.
"""
import pytest

from edl_compile import compile_edl
from edl_metrics import MACRO_EVENTS, measure


def _card(at, until, **card):
    card.setdefault("kicker", "UN KICKER")
    return {"atWord": at, "type": "CARD", "untilWord": until, "card": card}


# ── compilación ──────────────────────────────────────────────────────────────
def test_los_bordes_salen_de_las_palabras(card_edl, write_edl, style, w10):
    edl = write_edl(card_edl(_card(10, 14, title="Hola")))
    (c,) = compile_edl(edl, style)["cards"]
    assert c["start"] == pytest.approx(w10.at(10), abs=0.034)
    # El borde de salida es el FINAL de su palabra, no el inicio de la
    # siguiente: un rótulo acompaña hasta que la idea acaba de pronunciarse.
    assert c["end"] == pytest.approx(w10.words[14].end, abs=0.034)


def test_until_offset_estira_el_borde(card_edl, write_edl, style, w10):
    ev = _card(10, 14, title="Hola")
    ev["untilOffset"] = 0.4
    (c,) = compile_edl(write_edl(card_edl(ev)), style)["cards"]
    assert c["end"] == pytest.approx(w10.words[14].end + 0.4, abs=0.034)


def test_el_contenido_del_rotulo_llega_intacto(card_edl, write_edl, style):
    (c,) = compile_edl(write_edl(card_edl(
        _card(10, 14, kicker="CUANDO HACE FALTA", title="Escalar a\nun humano",
              key="humano", place="top"))), style)["cards"]
    assert c["kicker"] == "CUANDO HACE FALTA"
    assert c["title"] == "Escalar a\nun humano"
    assert c["key"] == "humano"


def test_cta_at_word_se_resuelve_a_instante_absoluto(card_edl, write_edl, style, w10):
    ev = _card(10, 20, body="cta", cta_text="RESPUESTAS")
    ev["ctaAtWord"] = 12
    (c,) = compile_edl(write_edl(card_edl(ev)), style)["cards"]
    # ABSOLUTO a propósito: `build_cards` lo pasa a relativo restando el
    # `start` del propio rótulo. Emitirlo ya relativo lo restaría dos veces.
    assert c["cta_at"] == pytest.approx(w10.at(12), abs=0.034)


def test_las_tarjetas_salen_ordenadas_por_tiempo(card_edl, write_edl, style):
    plan = compile_edl(write_edl(card_edl(
        _card(60, 64, title="Segunda"), _card(10, 14, title="Primera"))), style)
    assert [c["title"] for c in plan["cards"]] == ["Primera", "Segunda"]


def test_un_rotulo_es_un_cambio_macro(card_edl, write_edl, style):
    """Si no contara, un tramo de A_ROLL sostenido por un rótulo daría un
    hueco macro enorme y el gate pediría añadir movimiento que ya está ahí."""
    assert "CARD" in MACRO_EVENTS
    sin_ = measure(write_edl(card_edl()), style)["max_macro_gap"]
    con = measure(write_edl(card_edl(_card(60, 64, title="Algo"))), style)["max_macro_gap"]
    assert con < sin_


# ── lo que no se puede escribir ──────────────────────────────────────────────
def test_un_rotulo_sobre_un_stage_falla(problems_of, edl_min, stage_edl):
    """Apilado, no gusto: las tarjetas van en la pista 4 y el takeover del
    stage en la 5, así que el rótulo se renderizaría DEBAJO de un fondo opaco.
    Un render que sale mal sin que nada falle es el peor de los dos."""
    p = problems_of(stage_edl(edl_min, [
        {"atWord": 0, "type": "CAPTION", "words": [0, 4]},
        _card(10, 14, title="Invisible")]))
    assert "DEBAJO del takeover" in p


def test_un_rotulo_que_pisa_el_stage_siguiente_falla(problems_of, edl_min, w10):
    """El caso que no basta con mirar el segmento en que se declara: el rótulo
    se extiende hasta `untilWord`, y ese borde puede caer ya dentro del stage."""
    base = dict(edl_min)
    base["segments"] = [
        {"words": [0, 20], "semanticIntent": "presentador",
         "sceneType": "A_ROLL", "camera": "MEDIUM",
         "events": [{"atWord": 0, "type": "CAPTION", "words": [0, 4]},
                    _card(10, 40, title="Se pasa de largo")],
         "reason": "el rótulo muere dentro del stage de al lado"},
        {"words": [21, 130], "semanticIntent": "un stage",
         "sceneType": "MOTION_STAGE", "representationType": "OBJECT",
         "camera": "OFF", "events": [],
         "reason": "el stage que el rótulo pisa"}]
    assert "pisa el stage" in problems_of(base)


def test_una_key_que_no_esta_en_el_titular_falla(problems_of, card_edl):
    p = problems_of(card_edl(_card(10, 14, title="Escalar a un humano",
                                   key="paciente")))
    assert "no aparece en 'title'" in p


def test_una_clave_desconocida_falla(problems_of, card_edl):
    """`build_cards` ignora en silencio lo que no conoce: un `titel` mal
    escrito daría un rótulo sin titular y un render aparentemente correcto."""
    p = problems_of(card_edl(_card(10, 14, titel="typo")))
    assert "desconocidas" in p and "titel" in p


def test_un_rotulo_sin_kicker_ni_titular_falla(problems_of, card_edl):
    p = problems_of(card_edl({"atWord": 10, "type": "CARD", "untilWord": 14,
                              "card": {"place": "top"}}))
    assert "no pinta nada" in p


def test_falta_until_word(problems_of, card_edl):
    p = problems_of(card_edl({"atWord": 10, "type": "CARD",
                              "card": {"kicker": "X"}}))
    assert "falta untilWord" in p


def test_until_word_antes_de_at_word(problems_of, card_edl):
    p = problems_of(card_edl(_card(14, 10, title="Al revés")))
    assert "va antes de atWord" in p


def test_cta_at_word_solo_con_body_cta(problems_of, card_edl):
    ev = _card(10, 20, title="Sin botón")
    ev["ctaAtWord"] = 12
    assert "solo tiene sentido con body 'cta'" in problems_of(card_edl(ev))


def test_cta_at_word_fuera_del_rotulo(problems_of, card_edl):
    ev = _card(10, 20, body="cta")
    ev["ctaAtWord"] = 40
    assert "cae fuera del rótulo" in problems_of(card_edl(ev))


def test_place_y_body_desconocidos(problems_of, card_edl):
    assert "place 'arriba' no existe" in problems_of(
        card_edl(_card(10, 14, title="X", place="arriba")))
    assert "body 'grafico' no existe" in problems_of(
        card_edl(_card(10, 14, title="X", body="grafico")))
