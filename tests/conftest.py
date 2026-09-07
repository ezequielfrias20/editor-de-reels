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
