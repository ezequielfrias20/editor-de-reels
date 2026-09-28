"""Una versión = cuerpo + CTA de una plataforma (versiones.py, armar-version.py)."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from clips import clip, duracion, necesita_ffmpeg  # noqa: E402

from edl_schema import load_edl  # noqa: E402
from versiones import (anchor_recomendado, desplazar_segmento, leer_cta_cuerpo, rango_anchor,  # noqa: E402
                       recortar_cuerpo, unir_cortes, unir_edl, unir_plan, unir_transcripts, version_id)

SCRIPTS = Path(__file__).resolve().parent.parent / ".claude/skills/video-tech-premium/scripts"


def _cli():
    spec = importlib.util.spec_from_file_location("armar_version", SCRIPTS / "armar-version.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tr(*palabras):
    """Transcript mínimo de AssemblyAI: (texto, inicio_ms, fin_ms)."""
    return {"text": " ".join(p[0] for p in palabras), "utterances": None, "audio_duration": 5,
            "words": [{"text": t, "start": s, "end": e, "confidence": 1, "speaker": None}
                      for t, s, e in palabras]}


def cortes(dur, keeps):
    k = [{"start": s, "end": e, "dur": round(e - s, 3)} for s, e in keeps]
    kept = sum(x["dur"] for x in k)
    return {"source_duration": dur, "final_duration": round(kept, 3), "removed": round(dur - kept, 3),
            "cuts": [], "keeps": k}


CUERPO = tr(("Hola", 100, 400), ("mundo", 450, 900))
CTA = tr(("Link", 200, 500), ("perfil", 550, 1000))


CON_CTA = tr(("Hola", 100, 400), ("mundo.", 450, 900), ("Comenta", 1300, 1500), ("YA.", 1550, 1800))


def test_recortar_cuerpo_corta_entre_la_ultima_palabra_y_el_cta():
    t, c = recortar_cuerpo(CON_CTA, cortes(2.0, [(0.05, 1.9)]), 2)
    assert [w["text"] for w in t["words"]] == ["Hola", "mundo."]
    assert c["keeps"] == [{"start": 0.05, "end": 1.1, "dur": 1.05}]   # (0.9 + 1.3) / 2
    assert c["final_duration"] == pytest.approx(1.05)
    assert len(CON_CTA["words"]) == 4                                  # no toca el original


def test_recortar_cuerpo_no_deja_mas_de_300_ms_de_silencio_antes_del_corte():
    t = tr(("Hola", 100, 400), ("Comenta", 2000, 2300))
    _, c = recortar_cuerpo(t, cortes(3.0, [(0.0, 3.0)]), 1)
    assert c["keeps"][-1]["end"] == pytest.approx(0.7)


def test_recortar_cuerpo_sin_cta_dicho_no_recorta():
    t, c = recortar_cuerpo(CON_CTA, cortes(2.0, [(0.05, 1.9)]), None)
    assert t == CON_CTA and c["keeps"] == [{"start": 0.05, "end": 1.9, "dur": 1.85}]


def test_leer_cta_cuerpo():
    assert leer_cta_cuerpo({"desde_palabra": 2, "texto": "comenta ya"}, CON_CTA["words"]) == 2
    assert leer_cta_cuerpo({"desde_palabra": None}, CON_CTA["words"]) is None


@pytest.mark.parametrize("dato,esperado", [
    ({"desde_palabra": 2, "texto": "comenta ahora"}, "«Comenta YA.»"),     # no es lo que se dijo
    ({"desde_palabra": 1, "texto": "mundo. comenta ya"}, "«Hola»"),        # a mitad de frase
    ({"desde_palabra": 0, "texto": "hola mundo comenta ya"}, "palabra 0"),
    ({"desde_palabra": 9, "texto": "x"}, "palabra 9"),
    ({"texto": "comenta ya"}, "desde_palabra"),
])
def test_leer_cta_cuerpo_rechaza_lo_que_no_es_la_cola_del_cuerpo(dato, esperado):
    with pytest.raises(ValueError, match=esperado):
        leer_cta_cuerpo(dato, CON_CTA["words"])


def test_leer_cta_cuerpo_no_deja_el_cuerpo_a_mitad_de_frase():
    """Pieza 1: «…que uso para eso, comenta paralelo…» — el CTA empieza en «Si quieres», no en
    «comenta»; si no, TikTok terminaría colgado en «para eso,»."""
    w = tr(("Dalo", 0, 300), ("tú.", 300, 600), ("Si", 700, 800), ("quieres", 800, 900), ("eso,", 900, 1000),
           ("comenta", 1100, 1300), ("YA.", 1300, 1500))["words"]
    with pytest.raises(ValueError, match="«eso,»"):
        leer_cta_cuerpo({"desde_palabra": 5, "texto": "comenta YA."}, w)
    assert leer_cta_cuerpo({"desde_palabra": 2, "texto": "Si quieres eso, comenta YA."}, w) == 2


def test_version_id():
    assert version_id(7, "instagram") == "7-instagram"


def test_el_cta_se_desplaza_la_duracion_del_cuerpo():
    t = unir_transcripts(CUERPO, CTA, offset=2.0)
    assert [w["text"] for w in t["words"]] == ["Hola", "mundo", "Link", "perfil"]
    assert t["words"][2]["start"] == 2200 and t["words"][3]["end"] == 3000
    assert t["words"][0]["start"] == 100
    assert t["text"] == "Hola mundo Link perfil"


def test_sin_cta_el_transcript_es_el_del_cuerpo():
    assert unir_transcripts(CUERPO, None, 2.0)["words"] == CUERPO["words"]


def test_cortes_unidos():
    c = unir_cortes(cortes(2.0, [(0.05, 1.0)]), cortes(1.5, [(0.1, 1.1)]), offset=2.0)
    assert c["keeps"][1] == {"start": 2.1, "end": 3.1, "dur": 1.0}
    assert c["source_duration"] == 3.5
    assert c["final_duration"] == pytest.approx(1.95)


def test_desplazar_segmento_mueve_todos_los_indices():
    seg = {"words": [0, 1], "sceneType": "A_ROLL", "events": [
        {"type": "CARD", "atWord": 0, "untilWord": 1, "ctaAtWord": 1, "card": {"body": "cta"}},
        {"type": "CAPTION", "atWord": 0, "words": [0, 1]}]}
    s = desplazar_segmento(seg, 10)
    assert s["words"] == [10, 11]
    assert s["events"][0] | {} == {"type": "CARD", "atWord": 10, "untilWord": 11, "ctaAtWord": 11, "card": {"body": "cta"}}
    assert s["events"][1]["words"] == [10, 11]
    assert seg["words"] == [0, 1]            # no toca el original


EDL_CUERPO = {"format": "REEL", "piece": 7, "palette": "claro", "style_profile": "motion-explainer",
              "transcript": {"words": "transcripts/7.json", "cuts": "cuts/7.json", "fingerprint": "x"},
              "voice_gain": 0.7, "music": {},
              "segments": [{"words": [0, 1], "semanticIntent": "saludo", "sceneType": "A_ROLL",
                            "camera": "CLOSE", "reason": "arranque a cámara", "events": []}]}
CTA_SEGS = [{"words": [0, 1], "semanticIntent": "cta", "sceneType": "A_ROLL", "camera": "CLOSE",
             "reason": "el cierre va a cámara", "events": []}]


def test_unir_edl():
    e = unir_edl(EDL_CUERPO, CTA_SEGS, palabras_cuerpo=2, palabras_cta=2, pieza="7-tiktok",
                 words_rel="transcripts/7-tiktok.json", cuts_rel="cuts/7-tiktok.json", fingerprint="sha256:abc")
    assert e["piece"] == "7-tiktok"
    assert e["transcript"] == {"words": "transcripts/7-tiktok.json", "cuts": "cuts/7-tiktok.json", "fingerprint": "sha256:abc"}
    assert [s["words"] for s in e["segments"]] == [[0, 1], [2, 3]]
    assert e["palette"] == "claro"


@pytest.mark.parametrize("segs,esperado", [
    ([{**CTA_SEGS[0], "words": [1, 1]}], "empezar en la palabra 0"),
    ([{**CTA_SEGS[0], "words": [0, 4]}], "terminar en la palabra 1"),
])
def test_unir_edl_rechaza_un_cta_mal_indexado(segs, esperado):
    with pytest.raises(ValueError, match=esperado):
        unir_edl(EDL_CUERPO, segs, 2, 2, "7-tiktok", "a", "b", "c")


def test_unir_edl_rechaza_un_cuerpo_que_no_llega_al_final():
    with pytest.raises(ValueError, match="cuerpo"):
        unir_edl(EDL_CUERPO, CTA_SEGS, palabras_cuerpo=5, palabras_cta=2, pieza="7-x",
                 words_rel="a", cuts_rel="b", fingerprint="c")


def test_el_schema_acepta_piezas_con_texto(tmp_path):
    (tmp_path / "transcripts").mkdir(), (tmp_path / "cuts").mkdir()
    (tmp_path / "transcripts" / "7-tiktok.json").write_text(json.dumps(tr(("Hola", 100, 400), ("mundo", 450, 900))))
    (tmp_path / "cuts" / "7-tiktok.json").write_text(json.dumps(cortes(2.0, [(0.0, 2.0)])))
    from edl_words import load_words
    fp = load_words(tmp_path / "transcripts" / "7-tiktok.json", tmp_path / "cuts" / "7-tiktok.json").fingerprint
    edl = {**EDL_CUERPO, "piece": "7-tiktok",
           "transcript": {"words": "transcripts/7-tiktok.json", "cuts": "cuts/7-tiktok.json", "fingerprint": fp}}
    p = tmp_path / "edl.json"
    p.write_text(json.dumps(edl))
    assert load_edl(p, tmp_path).piece == "7-tiktok"


def _proyecto(tmp_path, con_cta=True, dice_cta=False):
    """Pieza 7 con la pasada 1 ya hecha: fuente unida, transcripts y cortes. `con_cta`: se
    subió el clip de CTA de TikTok. `dice_cta`: el cuerpo cierra con «Comenta YA.»."""
    d = tmp_path / "VIDEOS ORIGINALES" / "7"
    clips = [{"archivo": "cuerpo-1.mp4", "rol": "cuerpo", "orden": 1}]
    clip(d / "cuerpo-1.mp4", dur=2.0)
    if con_cta:
        clips.append({"archivo": "cta-tiktok.mp4", "rol": "cta", "plataforma": "tiktok", "orden": 1})
        clip(d / "cta-tiktok.mp4", dur=1.5, freq=660)
    (d / "pedido.json").write_text(json.dumps({"pieza": 7, "titulo": "t", "origen": {"tipo": "libre"},
                                               "prompt": "", "paleta": "claro", "clips": clips}))
    (tmp_path / "out").mkdir()
    import shutil
    shutil.copy(d / "cuerpo-1.mp4", tmp_path / "out" / "7-fuente.mov")
    for sub in ("transcripts", "cuts", "videos/7"):
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)
    if dice_cta:
        (tmp_path / "transcripts" / "7.json").write_text(json.dumps(CON_CTA))
        (tmp_path / "cuts" / "7.json").write_text(json.dumps(cortes(2.0, [(0.05, 1.9)])))
        cc = {"desde_palabra": 2, "texto": "Comenta YA."}
    else:
        (tmp_path / "transcripts" / "7.json").write_text(json.dumps(CUERPO))
        (tmp_path / "cuts" / "7.json").write_text(json.dumps(cortes(2.0, [(0.05, 1.0)])))
        cc = {"desde_palabra": None}
    (tmp_path / "videos" / "7" / "cta-cuerpo.json").write_text(json.dumps(cc))
    (tmp_path / "transcripts" / "7-cta-tiktok.json").write_text(json.dumps(CTA))
    (tmp_path / "cuts" / "7-cta-tiktok.json").write_text(json.dumps(cortes(1.5, [(0.1, 1.1)])))
    (tmp_path / "videos" / "7" / "edl-cuerpo.json").write_text(json.dumps(EDL_CUERPO))
    (tmp_path / "videos" / "7" / "cta-tiktok.json").write_text(json.dumps({"segments": CTA_SEGS}))
    return tmp_path


@necesita_ffmpeg
def test_cli_datos_arma_fuente_transcript_y_cortes(tmp_path):
    root = _proyecto(tmp_path)
    assert _cli().main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    assert duracion(root / "out" / "7-tiktok-fuente.mov") == pytest.approx(3.5, abs=0.1)
    t = json.loads((root / "transcripts" / "7-tiktok.json").read_text())
    # el CTA arranca donde termina el cuerpo EN LA FUENTE UNIDA (≈ 2.0 s)
    assert t["words"][2]["start"] == pytest.approx(2200, abs=60)
    c = json.loads((root / "cuts" / "7-tiktok.json").read_text())
    assert len(c["keeps"]) == 2


@necesita_ffmpeg
def test_cli_edl_escribe_la_version_y_compila_su_schema(tmp_path):
    root = _proyecto(tmp_path)
    cli = _cli()
    assert cli.main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    assert cli.main(["edl", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    edl = load_edl(root / "videos" / "7-tiktok" / "edl.json", root)
    assert edl.piece == "7-tiktok" and len(edl.segments) == 2


@necesita_ffmpeg
def test_cli_tiktok_sin_clip_es_el_cuerpo_solo(tmp_path):
    root = _proyecto(tmp_path, con_cta=False)
    cli = _cli()
    assert cli.main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    assert cli.main(["edl", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    assert len(load_edl(root / "videos" / "7-tiktok" / "edl.json", root).segments) == 1


def _v(root, v, que):
    return json.loads((root / que / f"{v}.json").read_text())


@necesita_ffmpeg
def test_cli_tiktok_reemplaza_el_cta_dicho_en_el_cuerpo(tmp_path):
    root = _proyecto(tmp_path, dice_cta=True)
    assert _cli().main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    assert [w["text"] for w in _v(root, "7-tiktok", "transcripts")["words"]] == ["Hola", "mundo.", "Link", "perfil"]
    assert _v(root, "7-tiktok", "cuts")["keeps"][0]["end"] == 1.1     # antes de «Comenta»


@necesita_ffmpeg
def test_cli_instagram_sin_clip_usa_el_cta_dicho_en_el_cuerpo(tmp_path, capsys):
    root = _proyecto(tmp_path, dice_cta=True)
    cli = _cli()
    assert cli.main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "instagram"]) == 0
    assert [w["text"] for w in _v(root, "7-instagram", "transcripts")["words"]] == ["Hola", "mundo.", "Comenta", "YA."]
    assert _v(root, "7-instagram", "cuts")["keeps"] == [{"start": 0.05, "end": 1.9, "dur": 1.85}]
    capsys.readouterr()
    assert cli.main(["palabras", "--project", str(root), "--piece", "7", "--plataforma", "instagram"]) == 0
    assert "CTA desde 1.050 s (palabra 2)" in capsys.readouterr().out


@necesita_ffmpeg
def test_cli_tiktok_sin_clip_corta_el_cta_de_instagram_y_no_lleva_plan_de_cta(tmp_path, capsys):
    root = _proyecto(tmp_path, con_cta=False, dice_cta=True)
    cli = _cli()
    assert cli.main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    assert [w["text"] for w in _v(root, "7-tiktok", "transcripts")["words"]] == ["Hola", "mundo."]
    cuerpo = {**PLAN_CUERPO, "visuals": [{**PLAN_CUERPO["visuals"][0], "end": 1.05}]}
    (root / "videos" / "7" / "plan-cuerpo.json").write_text(json.dumps(cuerpo))
    assert cli.main(["plan", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    (root / "videos" / "7" / "plan-cta-tiktok.json").write_text(json.dumps(PLAN_CTA))
    assert cli.main(["plan", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 1
    assert "no tiene CTA" in capsys.readouterr().err


def test_cli_sin_cta_cuerpo_lo_pide(tmp_path, capsys):
    root = tmp_path
    d = root / "VIDEOS ORIGINALES" / "7"
    d.mkdir(parents=True)
    (d / "cuerpo-1.mp4").write_bytes(b"x")
    (d / "pedido.json").write_text(json.dumps({"pieza": 7, "paleta": "claro",
                                               "clips": [{"archivo": "cuerpo-1.mp4", "rol": "cuerpo", "orden": 1}]}))
    (root / "out").mkdir()
    (root / "out" / "7-fuente.mov").write_bytes(b"x")
    for sub, data in (("transcripts", CUERPO), ("cuts", cortes(2.0, [(0.05, 1.0)]))):
        (root / sub).mkdir()
        (root / sub / "7.json").write_text(json.dumps(data))
    assert _cli().main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 1
    assert "cta-cuerpo.json" in capsys.readouterr().err


def test_cli_plataforma_que_no_esta_en_el_pedido(tmp_path, capsys):
    root = tmp_path
    d = root / "VIDEOS ORIGINALES" / "7"
    d.mkdir(parents=True)
    (d / "cuerpo-1.mp4").write_bytes(b"x")
    (d / "pedido.json").write_text(json.dumps({"pieza": 7, "paleta": "claro",
                                               "clips": [{"archivo": "cuerpo-1.mp4", "rol": "cuerpo", "orden": 1}]}))
    assert _cli().main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "youtube"]) == 1
    assert "ERROR:" in capsys.readouterr().err


@necesita_ffmpeg
@pytest.mark.parametrize("cambio", ["transcript", "cortes"])
def test_edl_frena_si_el_cuerpo_cambio_despues_de_preparar_la_version(tmp_path, capsys, cambio):
    """Corregir una marca en el transcript (o recortar de nuevo) después de preparar la
    versión la deja vieja: el subtítulo saldría sin corregir y los índices del CTA se correrían."""
    root = _proyecto(tmp_path)
    cli = _cli()
    assert cli.main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    if cambio == "transcript":
        t = json.loads((root / "transcripts" / "7.json").read_text())
        t["words"][1]["text"] = "Mundo"
        (root / "transcripts" / "7.json").write_text(json.dumps(t))
    else:
        (root / "cuts" / "7.json").write_text(json.dumps(cortes(2.0, [(0.05, 0.9)])))
    assert cli.main(["edl", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 1
    err = capsys.readouterr().err
    assert "ERROR:" in err and "preparar-version.sh 7 tiktok" in err


# ── el camino del plan.json: triband a mano (la banda de arriba no la emite el EDL) ──

PLAN_CUERPO = {"format": "REEL", "palette": "claro",
               "layout": {"mode": "triband", "bands": {"top": [0, 660], "text": [660, 960], "speaker": [960, 1920]}},
               "voice_gain": 0.7, "music": {}, "keywords": ["mundo"],
               "shots": [{"at": 0.0, "kind": "band", "anchor": 0.4}],
               "visuals": [{"id": "v-hola", "role": "takeover", "kind": "mockup", "band": "top",
                            "start": 0.0, "end": 0.95, "mock": ["tool_card", {"slug": "claude"}]}],
               "sfx": [[0.0, "pop", 0.8, "arranque"]], "cards": []}
PLAN_CTA = {"_": "el CTA en segundos de la versión",
            "visuals": [{"id": "v-cta", "role": "takeover", "kind": "mockup", "band": "top",
                         "start": 0.95, "end": 1.95, "mock": ["tool_card", {"slug": "tiktok"}]}],
            "sfx": [[0.95, "whoosh-short", 0.8, "entra el CTA"]]}


def test_unir_plan_concatena_el_cta_sin_mover_sus_tiempos():
    """El cuerpo va primero, así que sus segundos son los mismos en todas las versiones, y
    el CTA se escribe YA en segundos de la versión: unir es concatenar, nunca desplazar
    (los mockups guardan tiempos dentro de `mock`, que nadie podría correr a ciegas)."""
    p = unir_plan(PLAN_CUERPO, PLAN_CTA, fin_cuerpo=0.95)
    assert [v["id"] for v in p["visuals"]] == ["v-hola", "v-cta"]
    assert p["visuals"][1]["start"] == 0.95
    assert [s[1] for s in p["sfx"]] == ["pop", "whoosh-short"]
    assert p["palette"] == "claro" and p["layout"] == PLAN_CUERPO["layout"]
    assert "_" not in p or p["_"] == PLAN_CUERPO.get("_")
    assert PLAN_CUERPO["visuals"][0]["id"] == "v-hola" and len(PLAN_CUERPO["visuals"]) == 1


def test_sin_cta_el_plan_es_el_del_cuerpo():
    assert unir_plan(PLAN_CUERPO, None, fin_cuerpo=0.95) == PLAN_CUERPO


@pytest.mark.parametrize("cta,esperado", [
    ({"visuals": [{**PLAN_CTA["visuals"][0], "start": 0.5}]}, "empieza en 0.500"),
    ({"shots": [{"at": 0.2, "kind": "band", "anchor": 0.4}]}, "empieza en 0.200"),
    ({"sfx": [[0.1, "pop", 0.8, "x"]]}, "empieza en 0.100"),
    ({"palette": "oscuro"}, "plan-cuerpo.json"),
    ({"visuals": [{**PLAN_CTA["visuals"][0], "id": "v-hola"}]}, "v-hola"),
])
def test_unir_plan_rechaza_un_cta_mal_armado(cta, esperado):
    with pytest.raises(ValueError, match=esperado):
        unir_plan(PLAN_CUERPO, cta, fin_cuerpo=0.95)


@pytest.mark.parametrize("visual,esperado", [
    ({"end": 1.4}, "termina en 1.400"),
    ({"end": None}, "sin `end`"),
])
def test_unir_plan_rechaza_un_cuerpo_que_se_mete_en_el_cta(visual, esperado):
    cuerpo = {**PLAN_CUERPO, "visuals": [{**PLAN_CUERPO["visuals"][0], **visual}]}
    with pytest.raises(ValueError, match=esperado):
        unir_plan(cuerpo, PLAN_CTA, fin_cuerpo=0.95)


def test_unir_plan_no_acepta_captions_a_mano():
    """`captions` son rangos de palabras que el cuerpo no puede declarar por el CTA; sin
    ellos `build-composition.py` trocea solo, cuerpo y CTA por igual."""
    with pytest.raises(ValueError, match="captions"):
        unir_plan({**PLAN_CUERPO, "captions": [{"words": [0, 1]}]}, PLAN_CTA, fin_cuerpo=0.95)


def test_rango_anchor_del_ejemplo_de_triband_md():
    lo, hi = rango_anchor({"width": 1080, "height": 1920, "chin_frac": 0.4531, "top_frac": 0.2812},
                          speaker=[960, 1920])
    assert lo == pytest.approx(0.306, abs=5e-4) and hi == pytest.approx(0.5624, abs=5e-4)
    assert anchor_recomendado(lo, hi) == 0.4


def test_rango_anchor_de_la_pieza_1_cabe_en_cuatro_diezmilesimas():
    """La toma de la pieza 1 (cara grande en cuadro): el 0.42 fijo del EDL cortaba la coronilla."""
    lo, hi = rango_anchor({"width": 1080, "height": 1920, "chin_frac": 0.5034, "top_frac": 0.2036},
                          speaker=[960, 1920])
    assert lo == pytest.approx(0.4068, abs=1e-4) and hi == pytest.approx(0.4072, abs=1e-4)
    a = anchor_recomendado(lo, hi)
    assert lo <= a <= hi and a == round(a, 4)


def test_sin_rango_valido_no_hay_anchor_recomendado():
    lo, hi = rango_anchor({"width": 1080, "height": 1920, "chin_frac": 0.56, "top_frac": 0.19},
                          speaker=[960, 1920])
    assert lo > hi and anchor_recomendado(lo, hi) is None


def _con_planes(root, con_cta=True):
    (root / "videos" / "7" / "plan-cuerpo.json").write_text(json.dumps(PLAN_CUERPO))
    if con_cta:
        (root / "videos" / "7" / "plan-cta-tiktok.json").write_text(json.dumps(PLAN_CTA))


@necesita_ffmpeg
def test_cli_plan_escribe_la_version(tmp_path):
    root = _proyecto(tmp_path)
    _con_planes(root)
    cli = _cli()
    assert cli.main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    assert cli.main(["plan", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    p = json.loads((root / "videos" / "7-tiktok" / "plan.json").read_text())
    assert [v["id"] for v in p["visuals"]] == ["v-hola", "v-cta"]


@necesita_ffmpeg
def test_cli_plan_rechaza_una_paleta_distinta_de_la_del_pedido(tmp_path, capsys):
    root = _proyecto(tmp_path)
    (root / "videos" / "7" / "plan-cuerpo.json").write_text(json.dumps({**PLAN_CUERPO, "palette": "oscuro"}))
    (root / "videos" / "7" / "plan-cta-tiktok.json").write_text(json.dumps(PLAN_CTA))
    cli = _cli()
    assert cli.main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    assert cli.main(["plan", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 1
    assert "paleta" in capsys.readouterr().err


@necesita_ffmpeg
def test_cli_plan_frena_si_el_cuerpo_cambio_despues_de_preparar_la_version(tmp_path, capsys):
    root = _proyecto(tmp_path)
    _con_planes(root)
    cli = _cli()
    assert cli.main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    (root / "cuts" / "7.json").write_text(json.dumps(cortes(2.0, [(0.05, 0.9)])))
    assert cli.main(["plan", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 1
    assert "preparar-version.sh 7 tiktok" in capsys.readouterr().err


@necesita_ffmpeg
def test_cli_palabras_lista_la_version_remapeada_y_marca_el_cta(tmp_path, capsys):
    root = _proyecto(tmp_path)
    cli = _cli()
    assert cli.main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    capsys.readouterr()
    assert cli.main(["palabras", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 0
    out = capsys.readouterr().out
    assert "Hola" in out and "perfil" in out
    assert "CTA desde 0.950" in out        # final_duration del corte del cuerpo


def test_cli_anchor_lee_la_cara_de_la_version(tmp_path, capsys):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "face-7-tiktok.json").write_text(json.dumps(
        {"width": 1080, "height": 1920, "chin_frac": 0.5034, "top_frac": 0.2036}))
    assert _cli().main(["anchor", "--project", str(tmp_path), "--piece", "7", "--plataforma", "tiktok"]) == 0
    out = capsys.readouterr().out
    assert "0.4068" in out and "0.4072" in out and "anchor 0.407" in out


def test_cli_anchor_sin_rango_prioriza_no_cortar_la_cara(tmp_path, capsys):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "face-7-tiktok.json").write_text(json.dumps(
        {"width": 1080, "height": 1920, "chin_frac": 0.56, "top_frac": 0.19}))
    assert _cli().main(["anchor", "--project", str(tmp_path), "--piece", "7", "--plataforma", "tiktok"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("⚠") and "anchor 0.38" in out and "cerca de la cámara" in out
