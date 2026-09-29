"""La doctrina dice lo que el compilador hace: formatos por defecto, mostrar sin escribir."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCTRINA = (ROOT / "CLAUDE.md").read_text()
FORMATOS = (ROOT / ".claude/skills/video-tech-premium/references/formatos.md").read_text()


def test_el_layout_por_defecto_es_formatos():
    assert '"layout": {"mode": "formatos"}' in DOCTRINA
    assert "check_layout_default" in DOCTRINA and "check_triband_default" not in DOCTRINA


def test_mostrar_no_escribir():
    assert "Mostrar, no escribir" in DOCTRINA
    for m in ("keyword_hero", "step_grid", "chip_grid"):
        assert m in DOCTRINA


def test_la_referencia_trae_los_tres_formatos_y_la_palabra_del_cta():
    for clave in ('"kind": "band"', '"kind": "off"', '"kind": "full"', '"cta_palabra"',
                  "ZOOM_MAX_1080", "ZOOM_MAX_4K", "960"):
        assert clave in FORMATOS, clave


def test_la_referencia_dice_que_el_subtitulo_sube_y_que_el_cta_va_en_cara():
    assert "sube hasta quedar justo encima de la cara" in FORMATOS
    assert "El CTA cierra en `cara`" in FORMATOS
    skill = (ROOT / ".claude/skills/editar-pieza/SKILL.md").read_text()
    assert "El CTA va en `cara`" in skill
