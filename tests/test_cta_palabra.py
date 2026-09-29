"""La palabra clave del CTA: grande, en serif itálica y entre comillas, fija debajo del
subtítulo mientras dura el CTA (doctrina 2026-09-29, idea 12 de la referencia)."""
from pathlib import Path

import pytest

BASE = 66
SKILL = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "video-tech-premium"


@pytest.fixture
def cta(fixtures_root, bc, project_root):
    prev = dict(W=bc.W, H=bc.H, FMT=bc.FMT, LAYOUT=bc.LAYOUT, CAPTION_SIZE=bc.CAPTION_SIZE,
                CAPTION_MAXW=bc.CAPTION_MAXW, CAPTION_MARGIN=bc.CAPTION_MARGIN, WORK=bc.WORK,
                CAPTIONS=bc.CAPTIONS, CHIN=bc.CHIN, CTA_PALABRA=getattr(bc, "CTA_PALABRA", None))
    bc.W, bc.H, bc.FMT = 1080, 1920, "REEL"
    bc.LAYOUT = {"mode": "formatos", "bands": {"top": [0, 960], "speaker": [960, 1920]}}
    bc.CAPTION_SIZE = BASE
    bc.CAPTION_MAXW = round(bc.W * 0.84)
    bc.CAPTION_MARGIN = round(bc.W * 0.07)
    bc.WORK = fixtures_root / "videos" / "10"
    bc.CHIN = 0.4324
    yield bc
    for k, v in prev.items():
        setattr(bc, k, v)


def _words(*textos, paso=0.3, dur=0.25):
    out, t = [], 0.0
    for txt in textos:
        out.append({"text": txt, "start": t, "end": t + dur})
        t += paso
    return out


CARA = [{"start": 0.0, "end": 10.0, "kind": "full", "zoom": 1.1, "anchor": 0.44}]


def test_la_palabra_va_debajo_del_subtitulo_y_dura_el_cta(cta):
    cta.CAPTIONS = [{"words": [0, 3]}]
    cta.CTA_PALABRA = {"texto": "MARCA", "desde": 0.0, "hasta": 3.0}
    spans, anims, _, rows = cta.build_captions(_words("comenta", "marca", "y", "listo"), 10.0, CARA, [])
    kw = next(s for s in spans if 'id="cta-kw"' in s)
    assert "“MARCA”" in kw
    top_kw = int(kw.split("top:")[1].split("px")[0])
    import caption_metrics as cm
    m = cm.measure_block(["comenta", "marca", "y", "listo"], BASE, None, "REEL", 1920, cache_dir=cta.WORK)
    assert top_kw == rows[0][3] + m["n_lines"] * m["line_h"] + cta.CTA_KW_GAP
    assert ("#cta-kw", 0.0, 3.0) in anims


def test_el_subtitulo_deja_sitio_para_la_palabra_sobre_el_20_por_ciento(cta):
    cta.CHIN = 0.95                   # la barbilla muy abajo empujaría el bloque al suelo
    cta.CAPTIONS = [{"words": [0, 3]}]
    cta.CTA_PALABRA = {"texto": "MARCA", "desde": 0.0, "hasta": None}
    spans, _, _, rows = cta.build_captions(_words("comenta", "marca", "y", "listo"), 10.0, CARA, [])
    kw = next(s for s in spans if 'id="cta-kw"' in s)
    top_kw = int(kw.split("top:")[1].split("px")[0])
    alto_kw = round(round(BASE * cta.CTA_KW_RATIO) * 1.14)
    assert top_kw + alto_kw <= round(1920 * 0.80)


def test_sin_subtitulo_en_su_ventana_igual_aparece(cta):
    cta.CAPTIONS = [{"words": [0, 1]}]
    cta.CTA_PALABRA = {"texto": "MARCA", "desde": 8.0, "hasta": 9.0}
    spans, anims, _, _ = cta.build_captions(_words("hola", "mundo"), 10.0, CARA, [])
    assert any('id="cta-kw"' in s for s in spans)
    assert ("#cta-kw", 8.0, 9.0) in anims


def test_sin_cta_palabra_no_hay_elemento(cta):
    cta.CAPTIONS = [{"words": [0, 1]}]
    cta.CTA_PALABRA = None
    spans, _, _, _ = cta.build_captions(_words("hola", "mundo"), 10.0, CARA, [])
    assert not any("cta-kw" in s for s in spans)


def test_la_fuente_de_la_palabra_esta_en_la_skill_y_trae_el_espanol():
    from fontTools.ttLib import TTFont
    f = SKILL / "assets" / "fonts" / "Fraunces-Italic800.woff2"
    assert f.exists()
    cmap = TTFont(f).getBestCmap()
    assert all(ord(c) in cmap for c in "áéíóúñÁÉÍÓÚÑ“”")


def test_la_palabra_del_cta_no_va_sobre_un_encuadre_band(cta):
    """En `partida` la palabra caería sobre la cara: el CTA cierra en `cara` (encuadre full)."""
    cta.CAPTIONS = [{"words": [0, 3]}]
    cta.CTA_PALABRA = {"texto": "MARCA", "desde": 0.0, "hasta": 3.0}
    band = [{"start": 0.0, "end": 10.0, "kind": "band", "zoom": 1.0, "anchor": 0.40}]
    with pytest.raises(SystemExit) as ei:
        cta.build_captions(_words("comenta", "marca", "y", "listo"), 10.0, band, [])
    assert "cara" in str(ei.value) and "full" in str(ei.value)
