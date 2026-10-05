"""Entrega de cada versión (renderizar-version.py) y su validación (validar-salida.py)."""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from clips import clip, necesita_ffmpeg  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent.parent / ".claude/skills/video-tech-premium/scripts"


def _mod(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, SCRIPTS / archivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def rv():
    return _mod("renderizar_version", "renderizar-version.py")


@pytest.fixture(scope="module")
def vs():
    return _mod("validar_salida", "validar-salida.py")


def proyecto(tmp_path, plataformas=("instagram", "tiktok"), dur=2.0, clip_tiktok=True):
    root = tmp_path
    o = root / "VIDEOS ORIGINALES" / "7"
    o.mkdir(parents=True)
    clips = [{"archivo": "cuerpo-1.mov", "rol": "cuerpo", "orden": 1}]
    if clip_tiktok:
        clips.append({"archivo": "cta-tiktok.mov", "rol": "cta", "plataforma": "tiktok", "orden": 1})
    for c in clips:
        (o / c["archivo"]).write_bytes(b"x")
    (o / "pedido.json").write_text(json.dumps({"pieza": 7, "paleta": "claro", "clips": clips}))
    (root / "videos" / "7").mkdir(parents=True)
    (root / "videos" / "7" / "propuesta.json").write_text(json.dumps(
        {"pieza": 7, "versiones": [{"plataforma": p} for p in plataformas]}))
    (root / "cuts").mkdir()
    for p in plataformas:
        (root / "cuts" / f"7-{p}.json").write_text(json.dumps({"final_duration": dur, "keeps": []}))
        clip(root / "videos" / f"7-{p}" / "output.mp4", dur=dur)
        (root / "videos" / f"7-{p}" / "public").mkdir()
    return root


@necesita_ffmpeg
def test_entregar_copia_a_los_dos_lugares(rv, tmp_path):
    root = proyecto(tmp_path)
    a, b = rv.entregar(root, 7, "tiktok", 2)
    assert a == root / "videos" / "7" / "output-tiktok-v2.mp4" and a.exists()
    assert b == root / "VIDEOS EDITADOS" / "7-tiktok-v2.mp4" and b.stat().st_size == a.stat().st_size


@necesita_ffmpeg
def test_cli_render_con_hyperframes_falso(rv, tmp_path, monkeypatch):
    root = proyecto(tmp_path)
    falso = tmp_path / "hf.sh"
    # el "render" falso solo toca output.mp4 (así queda más nuevo que el arranque del render)
    falso.write_text('#!/usr/bin/env bash\necho "$@" >> llamadas.txt\n[ "$1" = render ] && touch output.mp4\nexit 0\n')
    falso.chmod(0o755)
    monkeypatch.setenv("HYPERFRAMES", str(falso))
    assert rv.main(["--project", str(root), "--piece", "7", "--plataforma", "instagram", "--version", "1"]) == 0
    llamadas = (root / "videos" / "7-instagram" / "llamadas.txt").read_text().splitlines()
    assert llamadas[0] == "check public"
    assert llamadas[1].startswith("render public --skill=talking-head-recut -o output.mp4")
    assert (root / "videos" / "7" / "output-instagram-v1.mp4").exists()


@necesita_ffmpeg
def test_cli_render_que_falla_no_entrega(rv, tmp_path, monkeypatch, capsys):
    root = proyecto(tmp_path)
    falso = tmp_path / "hf.sh"
    falso.write_text("#!/usr/bin/env bash\necho 'check: 2 errores' >&2\nexit 3\n")
    falso.chmod(0o755)
    monkeypatch.setenv("HYPERFRAMES", str(falso))
    assert rv.main(["--project", str(root), "--piece", "7", "--plataforma", "instagram", "--version", "1"]) == 1
    assert "ERROR:" in capsys.readouterr().err
    assert not (root / "videos" / "7" / "output-instagram-v1.mp4").exists()


@necesita_ffmpeg
def test_salida_completa(rv, vs, tmp_path):
    root = proyecto(tmp_path)
    for p in ("instagram", "tiktok"):
        rv.entregar(root, 7, p, 1)
    assert vs.problemas(root, 7, 1) == []


@necesita_ffmpeg
def test_falta_una_plataforma(rv, vs, tmp_path):
    root = proyecto(tmp_path)
    rv.entregar(root, 7, "instagram", 1)
    assert any("output-tiktok-v1.mp4" in p for p in vs.problemas(root, 7, 1))


@necesita_ffmpeg
def test_duracion_fuera_de_tolerancia(rv, vs, tmp_path):
    root = proyecto(tmp_path)
    for p in ("instagram", "tiktok"):
        rv.entregar(root, 7, p, 1)
    (root / "cuts" / "7-tiktok.json").write_text(json.dumps({"final_duration": 5.0, "keeps": []}))
    assert any("dura" in p for p in vs.problemas(root, 7, 1))


@necesita_ffmpeg
def test_falta_la_copia_para_publicar(rv, vs, tmp_path):
    root = proyecto(tmp_path)
    for p in ("instagram", "tiktok"):
        rv.entregar(root, 7, p, 1)
    (root / "VIDEOS EDITADOS" / "7-tiktok-v1.mp4").unlink()
    assert any("VIDEOS EDITADOS" in p for p in vs.problemas(root, 7, 1))


@necesita_ffmpeg
def test_cli_acepta_v2(rv, vs, tmp_path):
    root = proyecto(tmp_path)
    for p in ("instagram", "tiktok"):
        rv.entregar(root, 7, p, 2)
    assert vs.main(["--project", str(root), "--piece", "7", "--version", "v2"]) == 0


@necesita_ffmpeg
def test_siempre_exige_instagram_y_tiktok_aunque_la_propuesta_sea_vieja(rv, vs, tmp_path):
    """Una propuesta de antes de 2026-09-27 declara solo las versiones con clip de CTA."""
    root = proyecto(tmp_path, plataformas=("tiktok",))
    rv.entregar(root, 7, "tiktok", 1)
    assert any("output-instagram-v1.mp4" in p for p in vs.problemas(root, 7, 1))


@necesita_ffmpeg
def test_sin_clip_de_tiktok_solo_exige_instagram(rv, vs, tmp_path):
    """Regla de Ezequiel (2026-10-05): sin clip de CTA de TikTok la pieza entrega solo Instagram."""
    root = proyecto(tmp_path, plataformas=("instagram",), clip_tiktok=False)
    rv.entregar(root, 7, "instagram", 1)
    assert vs.problemas(root, 7, 1) == []
