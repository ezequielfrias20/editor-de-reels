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


def test_editar_va_por_el_plan_y_no_por_el_edl():
    """La pasada escribe el plan a mano (el compilador del EDL no emite bandas) y lo arma
    en tres formatos con el ejemplo de references/formatos.md."""
    txt = SKILL.read_text()
    editar = txt[txt.index("## Pasada `editar`"):txt.index("## Pasada `corregir`")]
    assert "scripts/edl-compile.py" not in txt and "armar-version.py edl" not in txt
    for paso in ("armar-version.py palabras", "armar-version.py anchor", "armar-version.py plan",
                 "plan-cuerpo.json", "plan-cta-<p>.json", "references/formatos.md", "cta_palabra"):
        assert paso in editar, paso
    assert (ROOT / ".claude" / "skills" / "video-tech-premium" / "references" / "formatos.md").exists()


def test_la_skill_trabaja_en_tres_formatos():
    txt = SKILL.read_text()
    assert '"formato"' in txt and '"visual"' in txt and "banda_arriba" not in txt
    assert "triband en REEL" not in txt
    for f in ("cara", "partida", "grafico"):
        assert f in txt

def test_instagram_siempre_y_tiktok_solo_con_su_clip():
    """Decisiones de Ezequiel (2026-09-27 y 2026-10-05): el CTA dicho en el cuerpo es el de
    Instagram; TikTok lo reemplaza por su clip desde «comenta», y sin clip no hay TikTok."""
    txt = SKILL.read_text()
    assert "general" not in txt
    assert "cta-cuerpo.json" in txt and "desde_palabra" in txt
    assert "preparar-version.sh <n> instagram" in txt and "preparar-version.sh <n> tiktok" in txt
    assert "SOLO si el pedido trae el clip `cta` de\n  tiktok" in txt
    assert "El corte va en la palabra «comenta»" in txt
