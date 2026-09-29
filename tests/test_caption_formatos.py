"""El subtítulo de `partida` (layout formatos): centrado sobre la línea de división,
con filete porque la mitad de abajo cae sobre el metraje, y nunca encima de la cara."""
import pytest

BASE = 66
FORMATOS = {"mode": "formatos", "bands": {"top": [0, 960], "speaker": [960, 1920]}}


@pytest.fixture
def formatos(fixtures_root, bc, project_root):
    prev = dict(W=bc.W, H=bc.H, FMT=bc.FMT, LAYOUT=bc.LAYOUT, CAPTION_SIZE=bc.CAPTION_SIZE,
                CAPTION_MAXW=bc.CAPTION_MAXW, CAPTION_MARGIN=bc.CAPTION_MARGIN, WORK=bc.WORK,
                CAPTIONS=bc.CAPTIONS, TOP_FRAC=bc.TOP_FRAC, SRC_W=bc.SRC_W, SRC_H=bc.SRC_H,
                CTA_PALABRA=getattr(bc, "CTA_PALABRA", None))
    bc.W, bc.H, bc.FMT = 1080, 1920, "REEL"
    bc.LAYOUT = FORMATOS
    bc.CAPTION_SIZE = BASE
    bc.CAPTION_MAXW = round(bc.W * 0.84)
    bc.CAPTION_MARGIN = round(bc.W * 0.07)
    bc.WORK = fixtures_root / "videos" / "10"
    bc.SRC_W, bc.SRC_H = 1080, 1920
    bc.TOP_FRAC = None
    bc.CTA_PALABRA = None
    yield bc
    for k, v in prev.items():
        setattr(bc, k, v)


def _words(*textos, paso=0.3, dur=0.25):
    out, t = [], 0.0
    for txt in textos:
        out.append({"text": txt, "start": t, "end": t + dur})
        t += paso
    return out


SHOT = [{"start": 0.0, "end": 10.0, "kind": "band", "zoom": 1.0, "anchor": 0.40}]


def test_el_bloque_se_centra_sobre_la_costura(formatos):
    import caption_metrics as cm
    formatos.CAPTIONS = [{"words": [0, 3]}]
    spans, anims, _, rows = formatos.build_captions(_words("la", "primera", "es", "anime"), 10.0, SHOT, [])
    m = cm.measure_block(["la", "primera", "es", "anime"], BASE, None, "REEL", 1920,
                         cache_dir=formatos.WORK)
    assert rows[0][3] == 960 - (m["n_lines"] * m["line_h"]) // 2
    assert 'class="cap on-dark"' in spans[0]


def test_si_centrado_pisaria_la_cara_el_bloque_sube_hasta_quedar_encima(formatos):
    # speaker [960,1920], fuente 1080×1920: escala 1, drawn_h 1920, top = 960 − 960·0.40 = 576;
    # con top_frac 0.20 la cara empieza en y960, justo en la costura. Las tomas reales de
    # Ezequiel son así (top_frac 0.18–0.21): el bloque no puede frenar la compilación ni
    # obligar a bajar el anchor (la barbilla caería en el 20 % de la plataforma). Sube.
    import caption_metrics as cm
    formatos.TOP_FRAC = 0.20
    formatos.CAPTIONS = [{"words": [0, 3]}]
    _, _, _, rows = formatos.build_captions(_words("la", "primera", "es", "anime"), 10.0, SHOT, [])
    m = cm.measure_block(["la", "primera", "es", "anime"], BASE, None, "REEL", 1920,
                         cache_dir=formatos.WORK)
    alto = m["n_lines"] * m["line_h"]
    assert rows[0][3] == 960 - formatos.BAND_CAP_MARGIN - alto
    assert rows[0][3] + alto < 960


def test_con_la_cara_mas_abajo_pasa(formatos):
    formatos.TOP_FRAC = 0.30          # la cara empieza en y1152
    formatos.CAPTIONS = [{"words": [0, 3]}]
    _, _, _, rows = formatos.build_captions(_words("la", "primera", "es", "anime"), 10.0, SHOT, [])
    assert len(rows) == 1
    assert rows[0][3] == 923          # centrado: 960 − 75 // 2


def test_face_top_y(formatos):
    formatos.TOP_FRAC = 0.30
    assert formatos.face_top_y(SHOT[0]) == pytest.approx(576 + 0.30 * 1920)
    formatos.TOP_FRAC = None
    assert formatos.face_top_y(SHOT[0]) is None
