"""Deja los scripts de la skill importables desde los tests."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / ".claude" / "skills" / "video-tech-premium" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def skill_root() -> Path:
    return SCRIPTS.parent


@pytest.fixture(scope="session")
def w10(project_root):
    """Las palabras de la pieza 10, remapeadas a la línea del corte."""
    from edl_words import load_words
    return load_words(project_root / "transcripts" / "10.json",
                      project_root / "cuts" / "10.json")


# ── Tarea 2 ──────────────────────────────────────────────────────────────────
@pytest.fixture
def edl_min(w10):
    """El EDL más pequeño que es válido: un A_ROLL sobre las 131 palabras."""
    return {
        "format": "REEL", "piece": 10, "style_profile": "motion-explainer",
        "transcript": {"words": "transcripts/10.json", "cuts": "cuts/10.json",
                       "fingerprint": w10.fingerprint},
        "voice_gain": 0.70,
        "segments": [{
            "words": [0, 130], "semanticIntent": "la pieza entera de una",
            "sceneType": "A_ROLL", "camera": "CLOSE", "transitionIn": "CUT",
            "events": [{"atWord": 0, "type": "CAPTION", "words": [0, 4]}],
            "reason": "andamiaje mínimo para los tests del schema"}],
    }


@pytest.fixture
def write_edl(tmp_path, project_root):
    from edl_schema import load_edl

    def _w(data):
        p = tmp_path / "edl.json"
        p.write_text(json.dumps(data, ensure_ascii=False))
        return load_edl(p, project_root)
    return _w


@pytest.fixture
def problems_of(write_edl):
    from edl_schema import EdlError

    def _p(data):
        with pytest.raises(EdlError) as ei:
            write_edl(data)
        return " | ".join(ei.value.problems)
    return _p


@pytest.fixture
def stage_edl():
    """Un EDL de un solo MOTION_STAGE, para los tests de instancias."""
    def _s(base, events, **kw):
        seg = {"words": [0, 130], "semanticIntent": "un stage",
               "sceneType": "MOTION_STAGE", "representationType": "OBJECT",
               "camera": "OFF", "transitionIn": "CUT", "events": events,
               "reason": "probar el ciclo de vida de las instancias"}
        seg.update(kw)
        return dict(base, segments=[seg])
    return _s


# ── Tarea 3 ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def style(skill_root):
    from edl_compile import load_style
    return load_style("motion-explainer", skill_root)


@pytest.fixture(scope="session")
def edl10(project_root):
    from edl_schema import load_edl
    return load_edl(project_root / "videos" / "10" / "edl.json", project_root)


@pytest.fixture(scope="session")
def plan10(edl10, style):
    from edl_compile import compile_edl
    return compile_edl(edl10, style)


# ── Tarea 8 ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def bc():
    """`build-composition.py` cargado como módulo.

    Lleva guion, así que un `import` normal no lo alcanza. No se extrae la
    geometría a un módulo aparte a propósito: el plan le concede EXACTAMENTE 4
    cambios quirúrgicos y una extracción sería un quinto de otra naturaleza.
    Cargarlo con importlib no tiene efectos secundarios — todo su estado vive
    en `configure()`, que estos tests no llaman.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "build_composition", SCRIPTS / "build-composition.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Tarea 12 ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def manifest(project_root):
    from asset_resolve import load_manifest
    return load_manifest(project_root / "assets" / "manifest.json")


# ── pieza 12 ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def edl12(project_root):
    """El EDL de la pieza 12.

    ⚠ No está: `videos/` se borró sin commitear y estos EDL nunca llegaron a
    HEAD. El golden `tests/golden/12.plan.json` sí sobrevive, pero sin su
    entrada no hay nada que compilar. Se salta con razón en vez de reventar
    —el mismo trato que `audio14`— para que un fallo NUEVO se vea.
    """
    from edl_schema import load_edl
    p = project_root / "videos" / "12" / "edl.json"
    if not p.exists():
        pytest.skip("videos/12/edl.json no está: se perdió al borrar videos/ "
                    "sin commitear. La no-regresión la cubre la pieza 10.")
    return load_edl(p, project_root)


@pytest.fixture(scope="session")
def plan12(edl12, style):
    from edl_compile import compile_edl
    return compile_edl(edl12, style)


@pytest.fixture
def card_edl(edl_min):
    """`edl_min` (un A_ROLL sobre las 131 palabras de la pieza 10) con los
    eventos CARD que se le pasen. Sirve para los tests del rótulo sin
    depender del EDL real de ninguna pieza."""
    def _c(*cards):
        base = dict(edl_min)
        seg = dict(base["segments"][0])
        seg["events"] = list(seg["events"]) + list(cards)
        base["segments"] = [seg]
        return base
    return _c


# ── pieza 13 ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def edl13(project_root):
    """El EDL de la pieza 13.

    ⚠ No está: `videos/` se borró sin commitear y estos EDL nunca llegaron a
    HEAD. El golden `tests/golden/13.plan.json` sí sobrevive, pero sin su
    entrada no hay nada que compilar. Se salta con razón en vez de reventar
    —el mismo trato que `audio14`— para que un fallo NUEVO se vea.
    """
    from edl_schema import load_edl
    p = project_root / "videos" / "13" / "edl.json"
    if not p.exists():
        pytest.skip("videos/13/edl.json no está: se perdió al borrar videos/ "
                    "sin commitear. La no-regresión la cubre la pieza 10.")
    return load_edl(p, project_root)


@pytest.fixture(scope="session")
def plan13(edl13, style):
    from edl_compile import compile_edl
    return compile_edl(edl13, style)


# ── pieza 14 ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def edl14(project_root):
    """El EDL de la pieza 14.

    ⚠ No está: `videos/` se borró sin commitear y estos EDL nunca llegaron a
    HEAD. El golden `tests/golden/14.plan.json` sí sobrevive, pero sin su
    entrada no hay nada que compilar. Se salta con razón en vez de reventar
    —el mismo trato que `audio14`— para que un fallo NUEVO se vea.
    """
    from edl_schema import load_edl
    p = project_root / "videos" / "14" / "edl.json"
    if not p.exists():
        pytest.skip("videos/14/edl.json no está: se perdió al borrar videos/ "
                    "sin commitear. La no-regresión la cubre la pieza 10.")
    return load_edl(p, project_root)


@pytest.fixture(scope="session")
def plan14(edl14, style):
    from edl_compile import compile_edl
    return compile_edl(edl14, style)


@pytest.fixture(scope="session")
def pc():
    """`plan-cuts.py` cargado como módulo — lleva guion en el nombre."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("plan_cuts", SCRIPTS / "plan-cuts.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def audio14(project_root):
    """El FLAC de la pieza 14. `assets/audio/` está en .gitignore, así que los
    tests que lo necesitan se saltan en un clon limpio en vez de fallar."""
    p = project_root / "assets" / "audio" / "14.flac"
    if not p.exists():
        pytest.skip("assets/audio/14.flac no está (gitignored)")
    return p


@pytest.fixture(scope="session")
def ab():
    """`audit-breaths.py` cargado como módulo — lleva guion en el nombre."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "audit_breaths", SCRIPTS / "audit-breaths.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
