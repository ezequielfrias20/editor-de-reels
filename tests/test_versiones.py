"""Una versión = cuerpo + CTA de una plataforma (versiones.py, armar-version.py)."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from clips import clip, duracion, necesita_ffmpeg  # noqa: E402

from edl_schema import load_edl  # noqa: E402
from versiones import desplazar_segmento, unir_cortes, unir_edl, unir_transcripts, version_id  # noqa: E402

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


def _proyecto(tmp_path, con_cta=True):
    """Pieza 7 con la pasada 1 ya hecha: fuente unida, transcripts y cortes."""
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
    (tmp_path / "transcripts" / "7.json").write_text(json.dumps(CUERPO))
    (tmp_path / "cuts" / "7.json").write_text(json.dumps(cortes(2.0, [(0.05, 1.0)])))
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
def test_cli_general_sin_cta(tmp_path):
    root = _proyecto(tmp_path, con_cta=False)
    cli = _cli()
    assert cli.main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "general"]) == 0
    assert cli.main(["edl", "--project", str(root), "--piece", "7", "--plataforma", "general"]) == 0
    assert len(load_edl(root / "videos" / "7-general" / "edl.json", root).segments) == 1


def test_cli_plataforma_que_no_esta_en_el_pedido(tmp_path, capsys):
    root = tmp_path
    d = root / "VIDEOS ORIGINALES" / "7"
    d.mkdir(parents=True)
    (d / "cuerpo-1.mp4").write_bytes(b"x")
    (d / "pedido.json").write_text(json.dumps({"pieza": 7, "paleta": "claro",
                                               "clips": [{"archivo": "cuerpo-1.mp4", "rol": "cuerpo", "orden": 1}]}))
    assert _cli().main(["datos", "--project", str(root), "--piece", "7", "--plataforma", "tiktok"]) == 1
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
