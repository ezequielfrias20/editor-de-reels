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


FIXTURES = ROOT / "tests" / "fixtures"


@pytest.fixture(scope="session")
def fixtures_root() -> Path:
    """Datos de piezas pasadas que se quedan SOLO como datos de prueba.

    Misma estructura relativa que un proyecto (`transcripts/`, `cuts/`,
    `videos/<n>/`), así que un EDL que declara `transcripts/10.json` se
    resuelve igual pasando esta carpeta como raíz."""
    return FIXTURES


@pytest.fixture(scope="session")
def w10(fixtures_root):
    """Las palabras de la pieza 10, remapeadas a la línea del corte."""
    from edl_words import load_words
    return load_words(fixtures_root / "transcripts" / "10.json",
                      fixtures_root / "cuts" / "10.json")


# ── Tarea 2 ──────────────────────────────────────────────────────────────────
@pytest.fixture
def edl_min(w10):
    """El EDL más pequeño que es válido: un A_ROLL sobre las 131 palabras."""
    return {
        "format": "REEL", "piece": 10, "style_profile": "motion-explainer",
        "palette": "oscuro",
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
def write_edl(tmp_path, fixtures_root):
    from edl_schema import load_edl

    def _w(data):
        p = tmp_path / "edl.json"
        p.write_text(json.dumps(data, ensure_ascii=False))
        return load_edl(p, fixtures_root)
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
def edl10(fixtures_root):
    from edl_schema import load_edl
    return load_edl(fixtures_root / "videos" / "10" / "edl.json", fixtures_root)


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


@pytest.fixture(scope="session")
def pc():
    """`plan-cuts.py` cargado como módulo — lleva guion en el nombre."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("plan_cuts", SCRIPTS / "plan-cuts.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def audio14(fixtures_root):
    """El FLAC de la pieza 14, como dato de prueba en `tests/fixtures/` (el
    `.gitignore` lo exceptúa). Si faltara, los tests se saltan en vez de fallar."""
    p = fixtures_root / "assets" / "audio" / "14.flac"
    if not p.exists():
        pytest.skip("tests/fixtures/assets/audio/14.flac no está")
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
