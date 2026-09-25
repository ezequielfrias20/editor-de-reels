import importlib.util
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "video-tech-premium" / "scripts"


def _mod():
    spec = importlib.util.spec_from_file_location("palette_sheet", SCRIPTS / "palette-sheet.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_la_hoja_trae_las_dos_paletas_y_todas_las_muestras(tmp_path):
    m = _mod()
    out = m.build(tmp_path)
    html = out.read_text()
    assert out.name == "palette-sheet.html"
    assert "#ECE7DE" in html.upper() and "#161412" in html.upper()
    for nombre in m.MUESTRAS:
        assert f'data-muestra="{nombre}"' in html
    assert html.count('class="frame"') == 2
    # Los selectores de un mockup cuelgan de `.viz[data-viz-id="<cid>"]`, y
    # cada paleta necesita sus propios ids o su CSS pisa al de la otra.
    for paleta in ("claro", "oscuro"):
        for i in range(1, len(m.MUESTRAS) + 1):
            assert f'class="viz" data-viz-id="{paleta}-m{i}"' in html
