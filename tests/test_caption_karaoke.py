"""El karaoke (Mejora 3, y su generalización en la Mejora 4, a petición del
usuario).

Sustituye la keyword violeta+agrandada por un fondo violeta con esquinas
redondeadas que aparece detrás de la palabra que suena en el instante exacto
en que se pronuncia y se apaga cuando arranca la siguiente: el resaltado
viaja, no se acumula, y todas las palabras comparten tamaño y color. Nació
limitado a `band` (Mejora 3); la Mejora 4 quita esa frontera — ya no hay
keyword agrandada en ninguna parte, `full`/`pip` incluidos. Lo único que
`full`/`pip` conservan de antes es la PIEL (`on-dark`, con filete de
grafito): el subtítulo sigue encima del metraje ahí, así que la letra sigue
necesitando separarse del fondo.
"""
import pytest

BANDS = {"top": [0, 660], "text": [660, 960], "speaker": [960, 1920]}


@pytest.fixture
def banda(bc, project_root):
    """Mismo patrón que `test_caption_band.py`: `bc` es de ámbito de SESIÓN,
    así que una fuga aquí contaminaría otros archivos de test."""
    prev = dict(W=bc.W, H=bc.H, FMT=bc.FMT, LAYOUT=bc.LAYOUT, CHIN=bc.CHIN,
                CAPTION_SIZE=bc.CAPTION_SIZE, CAPTION_MAXW=bc.CAPTION_MAXW,
                CAPTION_MARGIN=bc.CAPTION_MARGIN, WORK=bc.WORK,
                CAPTIONS=bc.CAPTIONS)
    bc.W, bc.H, bc.FMT = 1080, 1920, "REEL"
    bc.LAYOUT = {"mode": "triband", "bands": BANDS}
    bc.CHIN = 0.45   # lo necesita `chin_at` para el shot `full` de regresión
    bc.CAPTION_SIZE = 66
    bc.CAPTION_MAXW = round(bc.W * 0.84)
    bc.CAPTION_MARGIN = round(bc.W * 0.07)
    bc.WORK = project_root / "videos" / "10"
    yield bc
    for k, v in prev.items():
        setattr(bc, k, v)


def _words(*textos, paso=0.3, dur=0.25, arranque=0.0):
    """Palabras sintéticas con timings CRECIENTES — el mismo formato que
    devuelve `load()`: `{"text", "start", "end"}`. `dur < paso` deja un hueco
    entre palabras, como el habla real."""
    out, t = [], arranque
    for txt in textos:
        out.append({"text": txt, "start": t, "end": t + dur})
        t += paso
    return out


BAND_SHOT = {"start": 0.0, "end": 10.0, "kind": "band", "zoom": 1.0, "anchor": 0.38}
FULL_SHOT = {"start": 0.0, "end": 10.0, "kind": "full", "zoom": 1.09, "anchor": 0.44}


def test_todas_las_palabras_llevan_el_marcado_del_karaoke_en_band(banda):
    """Ninguna palabra es "la keyword": todas son `w kw` con su propio fondo
    `wbg`, y ninguna lleva la clase `key` (agrandado + violeta fijo) del
    esquema de `full`."""
    words = _words("la", "primera", "es", "anime.js")
    banda.CAPTIONS = [{"words": [0, 3], "keyword": [3, 3]}]
    spans, anims, key_anims, rows = banda.build_captions(words, 10.0, [BAND_SHOT], [])
    block = spans[0]
    assert block.count('class="w kw"') == 4
    assert 'class="w key"' not in block
    for i in range(4):
        assert f'id="c0w{i}-bg"' in block


def test_cada_palabra_trae_su_propia_ventana_en_key_anims(banda):
    """Karaoke: una entrada de 5 elementos por PALABRA, no una sola por
    bloque — `(wid, start, end, d_in, d_out)`, con `d_in`/`d_out` el fade YA
    escalado a lo que dura la palabra. El primer elemento entra en su propio
    `start` (o en el arranque del bloque, lo que sea más tarde)."""
    words = _words("uno", "dos", "tres")
    banda.CAPTIONS = [{"words": [0, 2], "keyword": None}]
    _, _, key_anims, _ = banda.build_captions(words, 10.0, [BAND_SHOT], [])
    assert len(key_anims) == 3
    for wid, start, end, d_in, d_out in key_anims:
        assert end > start
        assert d_in + d_out <= end - start + 1e-6
    starts = [s for _, s, _, _, _ in key_anims]
    assert starts == sorted(starts)


def test_el_resaltado_se_mueve_y_no_se_acumula(banda):
    """La ventana de una palabra TERMINA justo cuando arranca la siguiente:
    nunca hay dos fondos encendidos a la vez, y al terminar el bloque no
    queda ninguno pintado — el propio último `end` no se extiende al
    infinito, se recorta al final de la palabra (o del bloque)."""
    words = _words("uno", "dos", "tres", paso=0.4, dur=0.2)
    banda.CAPTIONS = [{"words": [0, 2], "keyword": None}]
    _, _, key_anims, _ = banda.build_captions(words, 10.0, [BAND_SHOT], [])
    (_, s0, e0, *_), (_, s1, e1, *_), (_, s2, e2, *_) = key_anims
    assert e0 == pytest.approx(s1, abs=1e-6)
    assert e1 == pytest.approx(s2, abs=1e-6)
    assert e2 <= words[2]["end"] + 1e-6


def test_una_palabra_muy_corta_no_pisa_su_propio_fade(banda):
    """Con habla rápida una palabra puede durar menos que 0.05+0.08s (el fade
    fijo de antes): `hyperframes check` lo caza como
    `overlapping_gsap_tweens` porque la entrada de la SIGUIENTE animación
    empieza antes de que la anterior termine. `d_in`/`d_out` se escalan a la
    ventana real de la palabra para que eso no pueda pasar nunca, por corta
    que sea."""
    words = _words("ra", "ra", "ra", paso=0.03, dur=0.02)  # ventana de 0.03s
    banda.CAPTIONS = [{"words": [0, 2], "keyword": None}]
    _, _, key_anims, _ = banda.build_captions(words, 10.0, [BAND_SHOT], [])
    for wid, start, end, d_in, d_out in key_anims:
        assert d_in + d_out <= end - start + 1e-9, wid


def test_en_full_tambien_hay_karaoke_pero_con_piel_on_dark(banda):
    """Mejora 4 (a petición del usuario): el karaoke deja la frontera de
    `band` — en `full`/`pip` ya no hay keyword agrandada y violeta, hay el
    MISMO marcado `w kw` + `wbg` que en `band`, con una entrada de 5
    elementos en `key_anims` por palabra. Lo que NO cambia es la PIEL: el
    subtítulo sigue ENCIMA del metraje, así que sigue siendo `on-dark` (con
    su filete de grafito) y no `on-surface` — ese filete lo pone
    `.cap.on-dark .w`, que `.w.kw` no pisa (no le toca ni `color` ni
    `-webkit-text-stroke`)."""
    words = _words("la", "primera", "es", "anime.js")
    banda.CAPTIONS = [{"words": [0, 3], "keyword": [3, 3]}]
    spans, anims, key_anims, rows = banda.build_captions(words, 10.0, [FULL_SHOT], [])
    block = spans[0]
    assert 'class="cap on-dark"' in block
    assert block.count('class="w kw"') == 4
    assert 'class="w key"' not in block
    for i in range(4):
        assert f'id="c0w{i}-bg"' in block
    assert len(key_anims) == 4
    for entry in key_anims:
        assert len(entry) == 5


def test_el_contraste_del_texto_sobre_el_fondo_del_karaoke_cumple_4_5(project_root):
    """La doctrina exige ≥4.5:1 para texto pequeño y blanco sobre `violet` (el
    de siempre) da 4.35:1 — no llega. El fondo del karaoke usa `violet_dk`,
    más oscuro, que sí cumple."""
    import sys
    sys.path.insert(0, str(project_root / ".claude" / "skills" /
                          "video-tech-premium" / "scripts"))
    from tokens import C, contrast
    assert contrast(C["violet"], C["text"]) < 4.5   # el motivo del cambio
    assert contrast(C["violet_dk"], C["text"]) >= 4.5
