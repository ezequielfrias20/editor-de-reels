"""validar-propuesta.py: lo mecánico de la propuesta de la pasada 1."""
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / ".claude/skills/video-tech-premium/scripts"


@pytest.fixture(scope="module")
def vp():
    spec = importlib.util.spec_from_file_location("validar_propuesta", SCRIPTS / "validar-propuesta.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def proyecto(tmp_path, propuesta_extra=None, beats=None, versiones=None):
    root = tmp_path
    d = root / "VIDEOS ORIGINALES" / "7"
    d.mkdir(parents=True)
    for f in ("cuerpo-1.mov", "cta-tiktok.mov", "pantalla-1.mov"):
        (d / f).write_bytes(b"x")
    (d / "pedido.json").write_text(json.dumps({"pieza": 7, "paleta": "claro", "clips": [
        {"archivo": "cuerpo-1.mov", "rol": "cuerpo", "orden": 1},
        {"archivo": "cta-tiktok.mov", "rol": "cta", "plataforma": "tiktok", "orden": 1},
        {"archivo": "pantalla-1.mov", "rol": "pantalla", "orden": 1}]}))
    (root / "transcripts").mkdir()
    palabras = "Hoy te muestro cómo instalar Claude Code en dos minutos".split()
    (root / "transcripts" / "7.json").write_text(json.dumps(
        {"words": [{"text": w, "start": i * 300, "end": i * 300 + 250} for i, w in enumerate(palabras)]}))
    (root / "scripts").mkdir()
    (root / "scripts" / "mockups.py").write_text(
        "def tool_card(x) -> tuple[str, str, list]:\n  pass\n"
        "def _privada() -> tuple[str, str, list]:\n  pass\n"
        "def text_px(t: str) -> float:\n  pass\n")
    (root / "scripts" / "objects.py").write_text(
        "def dental_chair(x):\n  pass\n"
        "REGISTRY = {\"motion_stage\": None, \"document\": None, \"dental-chair\": dental_chair}\n")
    (root / "assets" / "logos").mkdir(parents=True)
    (root / "assets" / "logos" / "meta.json").write_text(json.dumps({"claude": {"title": "Claude"}}))
    prop = {
        "pieza": 7, "generado": "2026-09-26T10:00:00", "formato": "REEL", "duracion_corte": 3.0,
        "paleta": "claro",
        "beats": beats if beats is not None else [{
            "id": "b1", "desde": 0.0, "hasta": 3.0, "texto": "Hoy te muestro…",
            "ancla": "cómo instalar Claude Code", "banda_arriba": "tarjeta de Claude",
            "componente": {"nombre": "tool_card", "existe": True},
            "logos": [{"slug": "claude", "estado": "disponible"}], "material": ["pantalla-1.mov"]}],
        "preguntas": [{"id": "q1", "beat": "b1", "pregunta": "¿?", "opciones": ["a", "b"],
                       "propuesta_por_defecto": "a"}],
        "versiones": versiones if versiones is not None else [{"plataforma": "tiktok", "cta_texto": "link", "duracion": 2.0}],
        "avisos": [],
        **(propuesta_extra or {}),
    }
    (root / "videos" / "7").mkdir(parents=True)
    (root / "videos" / "7" / "propuesta.json").write_text(json.dumps(prop))
    return root


def test_una_propuesta_buena_no_tiene_problemas(vp, tmp_path):
    assert vp.problemas(proyecto(tmp_path), 7) == []


def test_componentes_son_los_mockups_y_el_registro_de_objetos(vp, tmp_path):
    """Los objetos se nombran como en objects.REGISTRY (con guion, como en el EDL); los
    helpers de mockups.py (text_px…) no son componentes, ni motion_stage."""
    assert vp.componentes(proyecto(tmp_path)) == {"tool_card", "document", "dental-chair"}


def test_un_objeto_con_guion_existe(vp, tmp_path):
    beat = _beat(componente={"nombre": "dental-chair", "existe": True})
    assert vp.problemas(proyecto(tmp_path, beats=[beat]), 7) == []


def test_normalizar(vp):
    assert vp.normalizar("¿Cómo  INSTALAR, Claude?") == "como instalar claude"


def _beat(**cambios):
    b = {"id": "b1", "desde": 0.0, "hasta": 3.0, "texto": "t", "ancla": "instalar Claude Code",
         "banda_arriba": "x", "componente": {"nombre": "tool_card", "existe": True},
         "logos": [], "material": []}
    return {**b, **cambios}


@pytest.mark.parametrize("beat,trozo", [
    (_beat(ancla="esto nunca se dijo"), "no aparece en el transcript"),
    (_beat(componente={"nombre": "holograma", "existe": True}), "holograma"),
    (_beat(logos=[{"slug": "notion", "estado": "disponible"}]), "notion"),
    (_beat(material=["grabacion-secreta.mov"]), "grabacion-secreta.mov"),
    (_beat(id=""), "sin id"),
])
def test_propuestas_que_inventan(vp, tmp_path, beat, trozo):
    ps = vp.problemas(proyecto(tmp_path, beats=[beat]), 7)
    assert any(trozo in p for p in ps), ps


def test_un_componente_nuevo_marcado_como_tal_esta_bien(vp, tmp_path):
    beat = _beat(componente={"nombre": "holograma", "existe": False})
    assert vp.problemas(proyecto(tmp_path, beats=[beat]), 7) == []


def test_falta_la_version_de_una_plataforma(vp, tmp_path):
    ps = vp.problemas(proyecto(tmp_path, versiones=[]), 7)
    assert any("tiktok" in p for p in ps)


def test_una_version_que_no_se_pidio(vp, tmp_path):
    vs = [{"plataforma": "tiktok", "cta_texto": "", "duracion": 1}, {"plataforma": "youtube", "cta_texto": "", "duracion": 1}]
    assert any("youtube" in p for p in vp.problemas(proyecto(tmp_path, versiones=vs), 7))


def test_pregunta_sin_opcion_por_defecto(vp, tmp_path):
    prop = {"preguntas": [{"id": "q1", "beat": "b1", "pregunta": "¿?", "opciones": [], "propuesta_por_defecto": ""}]}
    assert any("q1" in p for p in vp.problemas(proyecto(tmp_path, propuesta_extra=prop), 7))


def test_paleta_distinta_del_pedido(vp, tmp_path):
    assert any("paleta" in p for p in vp.problemas(proyecto(tmp_path, propuesta_extra={"paleta": "oscuro"}), 7))


def test_sin_propuesta(vp, tmp_path):
    root = proyecto(tmp_path)
    (root / "videos" / "7" / "propuesta.json").unlink()
    assert any("propuesta.json" in p for p in vp.problemas(root, 7))


def test_cli(vp, tmp_path, capsys):
    root = proyecto(tmp_path, beats=[_beat(ancla="nunca dicho")])
    assert vp.main(["--project", str(root), "--piece", "7"]) == 1
    assert "✗ 1 problema(s)" in capsys.readouterr().out
