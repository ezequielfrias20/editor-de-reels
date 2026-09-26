"""Pedido del dashboard y unión de tomas (pieza.py, unir-cuerpo.py)."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from clips import clip, duracion, necesita_ffmpeg  # noqa: E402

from pieza import PiezaError, cargar_pedido, probe, unir  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent.parent / ".claude/skills/video-tech-premium/scripts"


def _cli():
    spec = importlib.util.spec_from_file_location("unir_cuerpo", SCRIPTS / "unir-cuerpo.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pedido(root: Path, n: int, clips: list[dict], paleta="claro") -> Path:
    d = root / "VIDEOS ORIGINALES" / str(n)
    d.mkdir(parents=True, exist_ok=True)
    for c in clips:
        f = d / c["archivo"]
        if not f.exists():
            f.write_bytes(b"x")
    (d / "pedido.json").write_text(json.dumps({
        "pieza": n, "titulo": "Prueba", "origen": {"tipo": "libre"}, "prompt": "",
        "paleta": paleta, "clips": clips, "pedido": "2026-09-26T10:00:00"}))
    return d


def test_pedido_ordena_por_orden_y_lista_plataformas(tmp_path):
    pedido(tmp_path, 7, [
        {"archivo": "cuerpo-2.mov", "rol": "cuerpo", "orden": 2},
        {"archivo": "cuerpo-1.mov", "rol": "cuerpo", "orden": 1},
        {"archivo": "cta-tiktok.mov", "rol": "cta", "plataforma": "tiktok", "orden": 1},
        {"archivo": "cta-instagram.mov", "rol": "cta", "plataforma": "instagram", "orden": 2},
    ])
    p = cargar_pedido(tmp_path, 7)
    assert [c.archivo for c in p.de_rol("cuerpo")] == ["cuerpo-1.mov", "cuerpo-2.mov"]
    assert p.plataformas == ["tiktok", "instagram"]
    assert p.paleta == "claro"


def test_sin_cta_la_unica_version_es_general(tmp_path):
    pedido(tmp_path, 3, [{"archivo": "cuerpo-1.mov", "rol": "cuerpo", "orden": 1}])
    assert cargar_pedido(tmp_path, 3).plataformas == ["general"]


def test_pedido_invalido_junta_todos_los_problemas(tmp_path):
    d = pedido(tmp_path, 4, [
        {"archivo": "a.mov", "rol": "pantalla", "orden": 1},
        {"archivo": "b.mov", "rol": "cta", "orden": 1},
        {"archivo": "c.mov", "rol": "cta", "plataforma": "tiktok", "orden": 2},
        {"archivo": "d.mov", "rol": "cta", "plataforma": "tiktok", "orden": 3},
        {"archivo": "e.mov", "rol": "musica", "orden": 1},
    ], paleta="violeta")
    (d / "a.mov").unlink()
    with pytest.raises(PiezaError) as e:
        cargar_pedido(tmp_path, 4)
    msg = str(e.value)
    for trozo in ("no hay ningún clip de cuerpo", "necesita plataforma", "dos CTA para tiktok",
                  "rol 'musica'", "no existe a.mov", "paleta 'violeta'"):
        assert trozo in msg


def test_sin_pedido_lo_dice(tmp_path):
    with pytest.raises(PiezaError, match="pedido.json"):
        cargar_pedido(tmp_path, 9)


@necesita_ffmpeg
def test_probe_ve_la_orientacion(tmp_path):
    assert probe(clip(tmp_path / "v.mp4")).orientacion == "vertical"
    assert probe(clip(tmp_path / "h.mp4", w=568, h=320)).orientacion == "horizontal"


@necesita_ffmpeg
def test_una_sola_toma_no_se_copia(tmp_path):
    a = clip(tmp_path / "a.mp4")
    assert unir([a], tmp_path / "out" / "f.mov") == "enlace"
    assert (tmp_path / "out" / "f.mov").stat().st_size == a.stat().st_size


@necesita_ffmpeg
def test_tomas_compatibles_se_concatenan_sin_recodificar(tmp_path):
    a, b = clip(tmp_path / "a.mp4"), clip(tmp_path / "b.mp4", freq=660)
    salida = tmp_path / "out" / "f.mov"
    assert unir([a, b], salida) == "copia"
    assert duracion(salida) == pytest.approx(2.0, abs=0.1)


@necesita_ffmpeg
def test_tomas_distintas_se_recodifican_al_formato_de_la_primera(tmp_path):
    a = clip(tmp_path / "a.mp4")
    b = clip(tmp_path / "b.mp4", w=360, h=640, fps=25)
    salida = tmp_path / "out" / "f.mov"
    assert unir([a, b], salida) == "recodificado"
    info = probe(salida)
    assert (info.ancho, info.alto) == (320, 568)
    assert info.audio is not None
    assert duracion(salida) == pytest.approx(2.0, abs=0.15)


@necesita_ffmpeg
def test_orientaciones_distintas_no_se_unen(tmp_path):
    a = clip(tmp_path / "a.mp4")
    b = clip(tmp_path / "b.mp4", w=568, h=320)
    with pytest.raises(PiezaError, match="b.mp4 horizontal"):
        unir([a, b], tmp_path / "f.mov")


@necesita_ffmpeg
def test_cli_une_el_cuerpo(tmp_path, capsys):
    d = pedido(tmp_path, 7, [
        {"archivo": "cuerpo-1.mp4", "rol": "cuerpo", "orden": 1},
        {"archivo": "cuerpo-2.mp4", "rol": "cuerpo", "orden": 2},
    ])
    clip(d / "cuerpo-1.mp4"), clip(d / "cuerpo-2.mp4")
    assert _cli().main(["--project", str(tmp_path), "--piece", "7"]) == 0
    assert (tmp_path / "out" / "7-fuente.mov").exists()
    assert "2 toma(s)" in capsys.readouterr().out


@necesita_ffmpeg
def test_cli_frena_un_cta_con_otra_orientacion(tmp_path, capsys):
    d = pedido(tmp_path, 8, [
        {"archivo": "cuerpo-1.mp4", "rol": "cuerpo", "orden": 1},
        {"archivo": "cta-tiktok.mp4", "rol": "cta", "plataforma": "tiktok", "orden": 1},
    ])
    clip(d / "cuerpo-1.mp4"), clip(d / "cta-tiktok.mp4", w=568, h=320)
    assert _cli().main(["--project", str(tmp_path), "--piece", "8"]) == 1
    err = capsys.readouterr().err
    assert err.startswith("ERROR:") and "cta-tiktok.mp4" in err
    assert not (tmp_path / "out" / "8-fuente.mov").exists()
