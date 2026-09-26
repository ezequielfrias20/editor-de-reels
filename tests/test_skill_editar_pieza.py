"""La skill editar-pieza solo nombra scripts que existen y tiene permisos para correrlos."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / ".claude" / "skills" / "editar-pieza" / "SKILL.md"


def test_la_skill_existe_con_su_frontmatter():
    txt = SKILL.read_text()
    assert txt.startswith("---\nname: editar-pieza\n")
    assert "ERROR:" in txt


def test_cada_script_que_nombra_existe():
    nombrados = set(re.findall(r"scripts/([\w.-]+\.(?:py|sh))", SKILL.read_text()))
    assert nombrados, "la skill no nombra ningún script"
    faltan = [s for s in nombrados if not (ROOT / "scripts" / s).exists()]
    assert faltan == []


def test_los_permisos_cubren_los_scripts_y_las_carpetas_de_salida():
    allow = json.loads((ROOT / ".claude" / "settings.json").read_text())["permissions"]["allow"]
    for regla in ("Bash(python3 scripts/*)", "Bash(scripts/*)", "Bash(ffmpeg *)", "Bash(ffprobe *)",
                  "Write(videos/**)", "Write(out/**)", "Write(transcripts/**)", "Write(cuts/**)"):
        assert regla in allow


def test_los_scripts_corren_con_el_python_del_proyecto():
    """El python3 del sistema no trae cv2 ni numpy: measure-face.py y compañía fallarían
    sin nadie mirando. La skill y preparar-version.sh usan el .venv del proyecto."""
    assert "python3 scripts/" not in SKILL.read_text()
    assert ".venv/bin/python scripts/" in SKILL.read_text()
    prep = (ROOT / "scripts" / "preparar-version.sh").read_text()
    assert ".venv/bin/python" in prep
    allow = json.loads((ROOT / ".claude" / "settings.json").read_text())["permissions"]["allow"]
    assert "Bash(.venv/bin/python scripts/*)" in allow


def test_los_pasos_largos_piden_el_timeout_maximo():
    """El timeout por defecto del Bash tool (2 min) corta un render o una recodificación 4K."""
    txt = SKILL.read_text()
    assert "600000" in txt
    for script in ("unir-cuerpo.py", "preparar-version.sh", "renderizar-version.py"):
        assert script in txt


def test_sin_nadie_mirando_no_se_genera_con_servicios_pagos():
    """El spec (§2) solo deja salir a la red a transcribe.py y fetch-logos.py."""
    txt = SKILL.read_text()
    assert "kie.py" in txt and "gen.py" in txt and "No generes" in txt
