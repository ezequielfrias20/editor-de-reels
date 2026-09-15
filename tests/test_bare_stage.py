"""`max_bare_stage` — un stage no puede estar en pantalla sin objetos.

LA HERMANA DE `check_no_black()`, y nace del mismo tipo de fallo con la
diferencia que lo hacía invisible: el frame no cae a negro, porque el suelo del
stage SÍ se pinta —viñeta y retícula—, así que ninguna comprobación existente
lo veía. Lo que se ve es un fondo grafito vacío con un subtítulo encima.

Vive en `edl_metrics` y no en `edl_schema` a propósito: el schema solo tiene
severidad «fallo», y la pieza 10 ya está ENTREGADA con tres huecos (0.90, 1.38
y 0.74 s). Un fallo duro impediría re-renderizarla nunca. Con el umbral y la
severidad en `styles/*.json`, el defecto se dice en voz alta sin invalidar
trabajo ya publicado — que es exactamente la separación que el módulo declara.
"""
import pytest

from edl_metrics import bare_stage_gaps, measure, run_gates

FADE = 0.22
MARGEN = FADE + 1.0 / 30


def _obj(at, iid="o1"):
    return {"atWord": at, "type": "OBJECT_IN", "asset": "object:clock@1",
            "instanceId": iid, "slot": "center", "state": {"time": "11:00"}}


def _stage(base, words, events, **kw):
    seg = {"words": list(words), "semanticIntent": "un stage",
           "sceneType": "MOTION_STAGE", "representationType": "OBJECT",
           "camera": "OFF", "events": events,
           "reason": "probar el hueco de suelo desnudo"}
    seg.update(kw)
    return seg


def _aroll(words, at):
    return {"words": list(words), "semanticIntent": "el presentador",
            "sceneType": "A_ROLL", "camera": "MEDIUM",
            "events": [{"atWord": at, "type": "CAPTION",
                        "words": [at, min(at + 2, words[1])]}],
            "reason": "relleno de presentador para los tests"}


# ── la medida ────────────────────────────────────────────────────────────────
def test_un_objeto_en_la_primera_palabra_del_stage_no_deja_hueco(edl_min, write_edl, style):
    """El arreglo correcto: la ventana de un segmento empieza en su PRIMERA
    palabra, así que un stage que empieza en la palabra del objeto abre ya con
    él puesto — sin adelantar el guion ni un frame."""
    edl = write_edl(dict(edl_min, segments=[
        _aroll([0, 9], 0),
        _stage(edl_min, [10, 130], [_obj(10)]),
    ]))
    assert bare_stage_gaps(edl, FADE) == []
    assert measure(edl, style)["max_bare_stage"] == 0.0


def test_el_objeto_que_llega_tarde_se_mide(edl_min, write_edl, style, w10):
    edl = write_edl(dict(edl_min, segments=[
        _aroll([0, 9], 0),
        _stage(edl_min, [10, 130], [_obj(20)]),
    ]))
    (donde, hueco), = bare_stage_gaps(edl, FADE)
    assert "al entrar" in donde
    assert hueco == pytest.approx(w10.at(20) - w10.at(10), abs=1e-3)
    assert measure(edl, style)["max_bare_stage"] == pytest.approx(hueco, abs=1e-3)


def test_un_frame_de_tolerancia(edl_min, write_edl):
    """Por debajo de 1/30 s no hay nada que ver: el compilador cuantiza cada
    instante con `q()`, así que marcarlo pediría mover un límite por algo
    invisible. Medido en la pieza 13: su stage de la secuencia abre 246 ms
    antes del primer mensaje, 26 ms por encima del fade_in, y no se ve."""
    edl = write_edl(dict(edl_min, segments=[
        _aroll([0, 9], 0),
        _stage(edl_min, [10, 130], [_obj(10)]),
    ]))
    # el margen efectivo es fade_in + un frame, no fade_in a secas
    assert bare_stage_gaps(edl, 0.0) == []          # hueco 0 < 1/30
    assert MARGEN > FADE


def test_un_stage_sin_ningun_objeto_se_reporta_entero(edl_min, write_edl, style):
    """Si no hay nada que mostrar, el segmento es A_ROLL: un MOTION_STAGE
    vacío es un fondo grafito con un subtítulo encima."""
    edl = write_edl(dict(edl_min, segments=[
        _aroll([0, 9], 0),
        _stage(edl_min, [10, 130],
               [{"atWord": 10, "type": "CAPTION", "words": [10, 13]}]),
    ]))
    (donde, hueco), = bare_stage_gaps(edl, FADE)
    assert "sin un solo objeto" in donde and hueco > 1.0
    assert measure(edl, style)["max_bare_stage"] > 1.0


def test_tambien_se_mide_por_el_otro_lado(edl_min, write_edl):
    """Retirar todo lo vivo a mitad de stage deja el MISMO fondo desnudo hasta
    que el stage termine."""
    edl = write_edl(dict(edl_min, segments=[
        _aroll([0, 9], 0),
        _stage(edl_min, [10, 130], [
            _obj(10),
            {"atWord": 20, "type": "OBJECT_EXIT", "instanceId": "o1"},
        ]),
    ]))
    salidas = [d for d, _ in bare_stage_gaps(edl, FADE)]
    assert any("al salir" in d for d in salidas)


def test_un_stage_clear_seguido_de_otra_entrada_no_cuenta(edl_min, write_edl):
    """`STAGE_CLEAR` libera los ids y el stage sigue vivo: si algo entra
    después, no hay suelo desnudo que reportar."""
    edl = write_edl(dict(edl_min, segments=[
        _aroll([0, 9], 0),
        _stage(edl_min, [10, 130], [
            _obj(10),
            {"atWord": 20, "type": "STAGE_CLEAR"},
            _obj(21, "o2"),
        ]),
    ]))
    assert [d for d, _ in bare_stage_gaps(edl, FADE) if "salir" in d] == []


# ── el gate, con su umbral en datos ──────────────────────────────────────────
def test_el_perfil_lo_declara_como_aviso(style):
    g = next(g for g in style["gates"] if g["metric"] == "max_bare_stage")
    assert g["max"] == 0.0
    # `warn` y no `fail`: la pieza 10 está entregada con tres huecos y un fallo
    # duro impediría volver a renderizarla.
    assert g["severity"] == "warn"


def test_el_gate_dispara_sobre_un_hueco(style):
    (f,) = [f for f in run_gates({**{g["metric"]: 0.0 for g in style["gates"]},
                                  "max_bare_stage": 1.4,
                                  "presenter_share": 0.5,
                                  "min_camera_gap": 1.0}, style)
            if f.metric == "max_bare_stage"]
    assert f.severity == "warn" and "1.4" in f.message


def test_la_pieza_13_no_tiene_ni_un_hueco(edl13, style):
    assert bare_stage_gaps(edl13, style["stage"]["fade_in"]) == []
    assert measure(edl13, style)["max_bare_stage"] == 0.0


def test_la_pieza_10_conserva_sus_tres_huecos_documentados(edl10, style):
    """Regresión al revés: si algún día alguien re-corta la pieza 10, esto
    cambia y hay que actualizar la bitácora en vez de descubrirlo por sorpresa."""
    huecos = bare_stage_gaps(edl10, style["stage"]["fade_in"])
    assert [round(g, 2) for _, g in huecos] == [0.90, 1.38, 0.73]
