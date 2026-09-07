"""Deja los scripts de la skill importables desde los tests."""
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
