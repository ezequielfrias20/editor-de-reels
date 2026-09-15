"""Los cuatro objetos de la pieza 12 y los tres mecanismos que trajeron.

La librería crece POR DEMANDA REAL. Estos cuatro salen de los beats del REEL 10
que no se podían decir con los seis de la pieza 10: la pregunta que se repite,
la cuenta de veces que se repite, el documento donde se organiza y la respuesta
que sale de él.

Los mecanismos son el valor duradero, más que los dibujos:
  · los anims INTERNOS de un objeto, relativos a su propia entrada;
  · `reveal`, que enciende un sub-elemento en su palabra;
  · `count`, el contador que sube rastreando su estado anterior.
"""
import pytest

import objects as o
import tokens as t
from asset_resolve import asset_hash


NUEVOS = ("msg-card", "answer-counter", "knowledge-base", "answer-approved")


# ── alta en la librería ──────────────────────────────────────────────────────
@pytest.mark.parametrize("nombre", NUEVOS)
def test_estan_en_el_registry(nombre):
    assert nombre in o.REGISTRY


@pytest.mark.parametrize("nombre", NUEVOS)
def test_el_manifest_cuadra_con_el_codigo(nombre, manifest):
    """Un `@n` es inmutable: si el hash del manifest y el del código divergen,
    los renders históricos dejarían de ser reproducibles en silencio."""
    ref = f"object:{nombre}@1"
    assert manifest["assets"][ref]["hash"] == asset_hash(ref, manifest)


@pytest.mark.parametrize("nombre", NUEVOS)
def test_cada_objeto_devuelve_el_contrato(nombre):
    r = o.REGISTRY[nombre]("viz-x", "inst", {}, "center")
    assert set(r) >= {"html", "anims", "eid"}
    assert r["eid"] == "viz-x-inst"
    assert 'class="obj accent"' in r["html"]


# ── los dos slots nuevos ─────────────────────────────────────────────────────
def test_head_y_foot_existen_y_estan_centrados():
    assert t.SLOTS["head"] == (540, 440)
    assert t.SLOTS["foot"] == (540, 1250)


def test_foot_deja_libre_la_zona_del_subtitulo():
    """El subtítulo de un stage empieza en y1352 (dos líneas). Un objeto en
    `foot` mide 108 px de alto, así que acaba en y1304: 48 px de margen."""
    _, y = t.SLOTS["foot"]
    assert y + 108 // 2 < 1352


def test_ningun_slot_baja_de_la_zona_segura():
    """Regla del §3 de la spec, que hasta ahora solo cumplían las captions."""
    for nombre, (_, y) in t.SLOTS.items():
        assert y < round(1920 * 0.80), f"{nombre} cae en la interfaz de la plataforma"


# ── knowledge_base: los dos modos ────────────────────────────────────────────
def test_sin_etiqueta_no_hay_check_verde():
    """Un ✓ junto a una barra en bruto se lee como «ya resuelto», que es lo
    contrario del beat en que el documento aparece sin organizar. Misma trampa
    que `flow_steps` ya documenta con «✓ junto a No hay stock»."""
    bruto = o.knowledge_base("v", "kb", {"labels": [], "rows": 6}, "center")
    assert t.C["go"] not in bruto["html"]
    con = o.knowledge_base("v", "kb", {"labels": ["Horarios"] * 6}, "center")
    assert con["html"].count(t.C["go"]) == 6


def test_modo_cascada_emite_un_anim_por_fila():
    """`reveal: False` es UN gesto —una lista que se organiza—, así que su
    escalonado lo pone el objeto y no seis eventos del EDL."""
    r = o.knowledge_base("v", "kb", {"labels": [], "rows": 6}, "center")
    assert [a[0] for a in r["anims"]] == ["chip-in"] * 6
    ts = [a[2] for a in r["anims"]]
    assert ts == sorted(ts) and ts[0] > 0
    # RELATIVOS a la entrada del objeto, no a la del stage: `motion_stage` los
    # desplaza. Un tiempo absoluto aquí se sumaría dos veces.
    assert max(ts) < 1.0


def test_modo_reveal_deja_el_hueco_puesto_y_apaga_el_contenido():
    """Animando la fila entera, el panel conservaba su alto de seis filas con
    solo cuatro visibles: el tercio de abajo quedaba vacío DENTRO del marco y
    se leía como un panel roto, no como una lista llenándose."""
    r = o.knowledge_base("v", "kb", {"labels": ["Horarios"] * 6,
                                     "reveal": True}, "center")
    assert r["anims"] == []                      # los beats los pone el EDL
    assert r["html"].count("opacity:1") >= 6     # los seis huecos, puestos
    for i in range(6):
        assert f'id="v-kb-r{i}"' in r["html"]    # y su contenido, direccionable


def test_el_titulo_no_se_parte_junto_al_sello():
    r = o.knowledge_base("v", "kb", {"labels": ["x"] * 6,
                                     "seal": "APROBADA POR TU EMPRESA"}, "center")
    assert "white-space:nowrap" in r["html"]
    assert 'id="v-kb-seal"' in r["html"]


# ── msg_card y answer_counter ────────────────────────────────────────────────
def test_msg_card_desplaza_del_eje_para_leerse_como_un_hilo():
    a = o.msg_card("v", "q1", {"text": "¿Y?", "w": 500, "dx": -40}, "stack-1")
    b = o.msg_card("v", "q2", {"text": "¿Y?", "w": 500, "dx": 50}, "stack-1")
    assert "left:250px" in a["html"] and "left:340px" in b["html"]


def test_el_sello_del_msg_card_nace_apagado():
    r = o.msg_card("v", "a1", {"text": "¿Y?", "seal": "AUTOMATIZADO"}, "stack-1")
    assert 'id="v-a1-seal"' in r["html"] and "opacity:0" in r["html"]
    # Sobre relleno verde va TINTA, nunca blanco: text/go = 1.66:1.
    assert f"color:{t.C['bg']}" in r["html"]


def test_el_contador_pinta_su_cifra_en_un_span_propio():
    """El tween le reescribe el texto, así que no puede compartir nodo con la
    etiqueta."""
    r = o.answer_counter("v", "c", {"n": 12}, "head")
    assert 'id="v-c-num"' in r["html"] and "#12" in r["html"]


# ── los mecanismos, vistos desde motion_stage ────────────────────────────────
def _stage(objetos, ops, visual_start=0.0):
    return o.motion_stage("viz-1", "primary", objetos, ops, visual_start)


def test_los_anims_internos_se_desplazan_por_la_entrada_del_objeto():
    objetos = [{"id": "kb", "kind": "knowledge-base", "slot": "center",
                "state": {"labels": [], "rows": 6}, "in": 10.0}]
    _, _, anims = _stage(objetos, [], visual_start=8.0)
    internos = [a for a in anims if a[1].startswith("#viz-1-kb-r")]
    assert len(internos) == 6
    # entrada relativa al stage = 10.0 - 8.0 = 2.0, más el escalonado propio
    assert min(a[2] for a in internos) == pytest.approx(2.18, abs=1e-6)


def test_reveal_enciende_el_sufijo_que_nombra_el_edl():
    objetos = [{"id": "kb", "kind": "knowledge-base", "slot": "center",
                "state": {"labels": ["x"] * 6, "reveal": True}, "in": 1.0}]
    _, _, anims = _stage(objetos, [{"t": 5.0, "op": "state", "id": "kb",
                                    "reveal": "r3"}])
    assert ("chip-in", "#viz-1-kb-r3", 5.0, o.REVEAL_DURATION) in anims


def test_count_emite_el_tween_con_los_dos_extremos():
    objetos = [{"id": "c", "kind": "answer-counter", "slot": "head",
                "state": {"n": 12}, "in": 1.0}]
    _, _, anims = _stage(objetos, [{"t": 3.0, "op": "state", "id": "c",
                                    "count_from": 12, "count": 27}])
    roll = [a for a in anims if a[0] == "count-roll"]
    assert roll == [("count-roll", "#viz-1-c-num", 3.0,
                     o.COUNT_ROLL_DURATION, 12, 27, "#")]


def test_una_instancia_de_otro_stage_no_rompe_nada():
    """`motion_stage` recibe los ops de su propio stage; un id que no conoce
    se ignora en silencio, como ya hacía la pieza 10."""
    _, _, anims = _stage([], [{"t": 1.0, "op": "state", "id": "fantasma",
                               "reveal": "r0"}])
    assert anims == []
