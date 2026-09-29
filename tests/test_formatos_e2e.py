"""Una pieza con los tres formatos compila de punta a punta: partida (band + visual en la
banda de arriba), gráfico (off bajo un visual opaco) y cara (full con zoom), con la
palabra del CTA. Usa las palabras, el corte y la cara de la pieza 10 de los fixtures."""
import json
import shutil

import pytest


@pytest.fixture
def proyecto(tmp_path, fixtures_root):
    for rel in ("transcripts/10.json", "cuts/10.json"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(fixtures_root / rel, tmp_path / rel)
    # La medición de la pieza 10 es de antes de `top_frac`. Las tomas reales de Ezequiel
    # lo traen (0.18–0.21) y con él corren los gates de la cara: se prueba con 0.20.
    face = json.loads((fixtures_root / "assets" / "face-10.json").read_text())
    (tmp_path / "assets").mkdir(exist_ok=True)
    (tmp_path / "assets" / "face-10.json").write_text(json.dumps({**face, "top_frac": 0.20}))
    d = tmp_path / "videos" / "10"
    d.mkdir(parents=True)
    shutil.copy(fixtures_root / "videos" / "10" / ".inter900.ttf", d / ".inter900.ttf")
    plan = {
        "format": "REEL", "palette": "claro", "layout": {"mode": "formatos"},
        "shots": [
            {"at": 0.0, "kind": "band", "anchor": 0.40},
            {"at": 10.0, "kind": "off"},
            {"at": 20.0, "kind": "full", "zoom": 1.12, "anchor": 0.44},
        ],
        "visuals": [
            {"id": "v-partida", "role": "takeover", "kind": "mockup", "band": "top",
             "start": 0.0, "end": 10.0, "mock": ["keyword_hero", {"word": "ARRIBA"}]},
            # gráfico: corte seco (fade 0), porque un visual opaco no puede solaparse con
            # el encuadre band de antes (check_band_speaker_clear) y el off no puede
            # empezar antes de que el visual tape (check_no_black)
            {"id": "v-grafico", "role": "takeover", "kind": "mockup", "fade_in": 0.0, "fade_out": 0.0,
             "start": 10.0, "end": 20.0, "mock": ["keyword_hero", {"word": "TODO"}]},
        ],
        "cta_palabra": {"texto": "MARCA", "desde": 40.0, "hasta": None},
    }
    (d / "plan.json").write_text(json.dumps(plan))
    return tmp_path


@pytest.fixture
def compilado(bc, proyecto):
    nombres = ("ROOT", "WORK", "PUB", "PIECE", "W", "H", "FMT", "T", "SRC_W", "SRC_H", "CHIN",
               "CX", "TOP_FRAC", "SHOTS", "CARDS", "VISUALS", "SFX", "MUSIC", "KEYWORDS",
               "CAPTIONS", "LAYOUT", "CAPTION_SIZE", "CAPTION_MAXW", "CAPTION_MARGIN",
               "CTA_PALABRA")
    import tokens as TK
    prev = {k: getattr(bc, k, None) for k in nombres}
    paleta = TK.PALETTE          # configure() activa la paleta del plan para todo el proceso
    try:
        bc.configure(proyecto, "10")
        bc.build()
        yield (proyecto / "videos" / "10" / "public" / "index.html").read_text()
    finally:
        TK.use(paleta)
        for k, v in prev.items():
            setattr(bc, k, v)


def test_la_pieza_en_tres_formatos_compila(compilado):
    html = compilado
    assert 'class="vid band clip"' in html          # partida
    assert 'class="vid clip"' in html               # cara (full)
    assert 'id="cta-kw"' in html and "“MARCA”" in html
    assert "Fraunces-Italic800.woff2" in html and ".cta-kw{" in html


def test_la_fuente_del_cta_se_copia_a_la_pieza(compilado, proyecto):
    assert (proyecto / "videos" / "10" / "public" / "fonts" / "Fraunces-Italic800.woff2").exists()
