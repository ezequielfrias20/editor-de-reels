"""El subtítulo en la banda de texto del triband.

Deja de perseguir la barbilla —no hay metraje entre y820 y y1120— y ancla el
bloque por ABAJO (Mejora 5, a petición del usuario): el SUELO es fijo —la
tinta más baja se apoya en él, pegada a la separación con el hablante— y el
tope sube o baja según cuántas líneas tenga el bloque. Antes era al revés
(tope fijo, crecía hacia abajo) y un bloque corto dejaba un hueco muerto
entre el subtítulo y el metraje del hablante. Lo que se protege aquí es el
gate: cambia de sentido con el ancla —ahora falla si el tope SUBE por encima
del techo de la banda de texto, no si la tinta baja hasta pisar la banda del
hablante— pero sigue siendo el mismo rigor, y eso tiene que fallar la
compilación, no el frame.
"""
import pytest

BASE = 66          # CAPTION_SIZE en REEL
FLOOR = 1104       # y1120 menos 16 px de holgura


def test_floor_px_manda_sobre_el_20_por_ciento(fixtures_root, project_root):
    """Sin `floor_px` el suelo es 0.80*H; con él, el que se pase."""
    import caption_metrics as cm
    libre = cm.measure_block(["hola", "mundo"], BASE, None, "REEL", 1920,
                             cache_dir=fixtures_root / "videos" / "10")
    band = cm.measure_block(["hola", "mundo"], BASE, None, "REEL", 1920,
                            floor_px=FLOOR,
                            cache_dir=fixtures_root / "videos" / "10")
    assert libre["floor_top"] == 1536 - libre["n_lines"] * libre["line_h"]
    assert band["floor_top"] == FLOOR - band["n_lines"] * band["line_h"]


def test_dos_lineas_con_keyword_caben_en_la_banda(fixtures_root, project_root):
    """66 x 1.22 = 81; 81 x 1.14 = 92. Dos líneas son 184 px desde y844 -> y1028."""
    import caption_metrics as cm
    m = cm.measure_block(["la", "primera", "es", "anime.js"], BASE, (3, 3), "REEL",
                         1920, floor_px=FLOOR,
                         cache_dir=fixtures_root / "videos" / "10")
    assert m["max_size"] == 81
    assert m["line_h"] == 92
    assert 844 + 2 * m["line_h"] <= FLOOR


BANDS = {"top": [0, 820], "text": [820, 1120], "speaker": [1120, 1920]}


@pytest.fixture
def banda(fixtures_root, bc, project_root):
    """Fija los globals que `build_captions` lee (`bc` es de ámbito de SESIÓN
    en conftest.py, así que una fuga aquí contaminaría otros archivos de
    test) y los restaura al terminar — mismo patrón que
    `test_triband_geometry.py`."""
    prev = dict(W=bc.W, H=bc.H, FMT=bc.FMT, LAYOUT=bc.LAYOUT,
                CAPTION_SIZE=bc.CAPTION_SIZE, CAPTION_MAXW=bc.CAPTION_MAXW,
                CAPTION_MARGIN=bc.CAPTION_MARGIN, WORK=bc.WORK,
                CAPTIONS=bc.CAPTIONS)
    bc.W, bc.H, bc.FMT = 1080, 1920, "REEL"
    bc.LAYOUT = {"mode": "triband", "bands": BANDS}
    bc.CAPTION_SIZE = BASE
    bc.CAPTION_MAXW = round(bc.W * 0.84)
    bc.CAPTION_MARGIN = round(bc.W * 0.07)
    # El .inter900.ttf cacheado en videos/10 es lo que permite medir la
    # fuente real sin renderizar.
    bc.WORK = fixtures_root / "videos" / "10"
    yield bc
    for k, v in prev.items():
        setattr(bc, k, v)


def _words(*textos, paso=0.3, dur=0.25):
    """Palabras sintéticas con timings crecientes, en el mismo formato que
    devuelve `load()`: `{"text", "start", "end"}`."""
    out, t = [], 0.0
    for txt in textos:
        out.append({"text": txt, "start": t, "end": t + dur})
        t += paso
    return out


def test_un_bloque_que_cabe_atraviesa_build_captions_con_el_suelo_fijo(banda):
    """El gate no es solo aritmética: hay que atravesar `build_captions()` de
    verdad. El bloque se ancla por ABAJO (Mejora 5): una línea (line_h 92)
    deja el tope en suelo(1104) − 92 = y1012, muy por debajo del techo de la
    banda de texto (820), así que la función devuelve normalmente y el `top`
    del subtítulo emitido —no un literal— sale de restar al suelo fijo, no de
    sumar a un tope fijo como antes de esta Mejora."""
    words = _words("la", "primera", "es", "anime.js")
    shots = [{"start": 0.0, "end": 10.0, "kind": "band", "zoom": 1.0, "anchor": 0.5}]
    banda.CAPTIONS = [{"words": [0, 3], "keyword": [3, 3]}]
    spans, anims, key_anims, rows = banda.build_captions(words, 10.0, shots, [])
    assert len(rows) == 1
    assert rows[0][3] == 1012


def test_un_bloque_que_no_cabe_hace_salir_la_compilacion(banda):
    """El `sys.exit(...)` del gate es un fallo REAL, y solo se prueba de
    verdad disparándolo. Con el ancla por ABAJO (Mejora 5) el gate cambió de
    sentido: ya no es la tinta bajando hasta pisar la banda del hablante, es
    el tope subiendo hasta pisar el TECHO de la banda de texto (820) según
    crecen las líneas — 4 líneas (line_h 92) suben el tope a
    1104 − 4×92 = y736, por encima de y820, y `build_captions()` tiene que
    salir con `SystemExit` mencionando la banda de la animación, no devolver
    un plan que la invade."""
    words = _words("PACIENTES", "AUTOMÁTICAMENTE", "POR", "WHATSAPP", "TODOS",
                   "LOS", "DÍAS", "SIN", "EXCEPCIÓN")
    shots = [{"start": 0.0, "end": 10.0, "kind": "band", "zoom": 1.0, "anchor": 0.5}]
    banda.CAPTIONS = [{"words": [0, 8], "keyword": [0, 0]}]
    with pytest.raises(SystemExit) as ei:
        banda.build_captions(words, 10.0, shots, [])
    assert "banda de la animación" in str(ei.value)
