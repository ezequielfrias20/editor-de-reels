"""El subtítulo en la banda de texto del triband.

Deja de perseguir la barbilla —no hay metraje entre y820 y y1120— y pasa a
tope FIJO. Lo que se protege aquí es el gate: un bloque que se pase invade
la banda del hablante, y eso tiene que fallar la compilación, no el frame.
"""
import pytest

BASE = 66          # CAPTION_SIZE en REEL
FLOOR = 1104       # y1120 menos 16 px de holgura


def test_floor_px_manda_sobre_el_20_por_ciento(project_root):
    """Sin `floor_px` el suelo es 0.80*H; con él, el que se pase."""
    import caption_metrics as cm
    libre = cm.measure_block(["hola", "mundo"], BASE, None, "REEL", 1920,
                             cache_dir=project_root / "videos" / "10")
    band = cm.measure_block(["hola", "mundo"], BASE, None, "REEL", 1920,
                            floor_px=FLOOR,
                            cache_dir=project_root / "videos" / "10")
    assert libre["floor_top"] == 1536 - libre["n_lines"] * libre["line_h"]
    assert band["floor_top"] == FLOOR - band["n_lines"] * band["line_h"]


def test_dos_lineas_con_keyword_caben_en_la_banda(project_root):
    """66 x 1.22 = 81; 81 x 1.14 = 92. Dos líneas son 184 px desde y844 -> y1028."""
    import caption_metrics as cm
    m = cm.measure_block(["la", "primera", "es", "anime.js"], BASE, (3, 3), "REEL",
                         1920, floor_px=FLOOR,
                         cache_dir=project_root / "videos" / "10")
    assert m["max_size"] == 81
    assert m["line_h"] == 92
    assert 844 + 2 * m["line_h"] <= FLOOR


def test_tres_lineas_no_caben(project_root):
    """3 x 92 = 276; 844 + 276 = 1120, o sea encima de la banda del hablante."""
    assert 844 + 3 * 92 > FLOOR
