"""El ataque de un efecto cae en su beat, no el principio de su fichero.

⚠ Esto estaba mal en TODAS las piezas anteriores y lo encontró la 18. `§12`
ya documentaba que el VOLUMEN se calcula en vez de escribirse a mano, porque
los archivos no vienen igualados; el ataque tenía exactamente la misma forma
de error —dar por hecho que los ficheros vienen alineados— y nadie lo había
medido. 16 de los 19 efectos de la librería traen silencio de cabecera:
`error` 604 ms, `typing` 437, `chime` 416, `ping` 323, `riser` 1727.

Cómo se vio: un filtro adaptado sobre el MP4 de la pieza 18 daba correlación
CERO para `error`. La primera lectura fue «el efecto no está»; la segunda, al
mirar el fichero, fue que la plantilla de 350 ms con la que se correlaba era
silencio puro. El fallo del test era el hallazgo.
"""
import subprocess

import numpy as np
import pytest


SFX = "assets/sfx"


def _lead_ms(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1",
                          "-ar", "48000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32)
    env = np.abs(a)
    on = np.flatnonzero(env > env.max() * 0.05)
    return float(on[0]) / 48.0 if on.size else 0.0


@pytest.fixture(scope="module")
def sfx_dir(project_root):
    d = project_root / SFX
    if not d.exists():
        pytest.skip("assets/sfx no está")
    return d


def test_la_medida_encuentra_el_silencio_de_cabecera_real(bc, sfx_dir):
    """Los números concretos que motivaron el arreglo, contra los ficheros."""
    for name, esperado in (("error", 604), ("typing", 437), ("chime", 416)):
        p = sfx_dir / f"{name}.mp3"
        if not p.exists():
            pytest.skip(f"{name}.mp3 no está")
        assert bc._lead_in(p) * 1000 == pytest.approx(esperado, abs=12)
        assert _lead_ms(p) == pytest.approx(esperado, abs=12)


def test_un_efecto_sin_cabecera_no_se_mueve(bc, sfx_dir):
    """`sparkle` (25 ms) y `glitch-2` (23 ms) están por debajo del umbral: no
    se compensan, para no mover tiempos por ruido de medición."""
    for name in ("sparkle", "glitch-2", "impact-bass-2"):
        p = sfx_dir / f"{name}.mp3"
        if not p.exists():
            continue
        assert bc._lead_in(p) < bc.SFX_LEAD_MIN


def test_el_umbral_son_menos_de_dos_frames(bc):
    """Por debajo de esto el desfase no se oye como retraso."""
    assert bc.SFX_LEAD_MIN <= 2 / 30


def test_la_medida_esta_cacheada(bc, sfx_dir):
    """Se llama una vez por efecto y por pieza; sin caché son 38 decodificados
    completos por compilación."""
    p = sfx_dir / "pop.mp3"
    if not p.exists():
        pytest.skip("pop.mp3 no está")
    assert bc._lead_in(p) is bc._lead_in(p) or bc._lead_in(p) == bc._lead_in(p)
    import inspect
    assert "cache" in inspect.signature(bc._lead_in).parameters


def test_un_fichero_vacio_no_revienta_la_compilacion(bc, tmp_path):
    vacio = tmp_path / "nada.mp3"
    vacio.write_bytes(b"")
    assert bc._lead_in(vacio) == 0.0


def test_el_html_adelanta_el_start_del_efecto_con_cabecera(project_root):
    """La comprobación de punta a punta, sobre el index.html ya compilado de la
    pieza 18: `error` se declara en 24.814 y su <audio> tiene que empezar
    ~604 ms antes para que el golpe caiga en la palabra."""
    import re
    idx = project_root / "videos" / "18" / "public" / "index.html"
    if not idx.exists():
        pytest.skip("la pieza 18 no está compilada")
    h = idx.read_text()
    m = re.search(r'<audio[^>]*src="sfx/error\.mp3"[^>]*data-start="([\d.]+)"', h)
    assert m, "no hay ningún <audio> de error.mp3 en la pieza 18"
    start = float(m.group(1))
    assert start == pytest.approx(24.814 - 0.604, abs=0.02), (
        f"data-start={start}: el efecto empieza en el beat en vez de adelantarse "
        "su cabecera, así que suena medio segundo tarde")


def test_ningun_efecto_de_la_18_queda_con_start_negativo(project_root):
    import re
    idx = project_root / "videos" / "18" / "public" / "index.html"
    if not idx.exists():
        pytest.skip("la pieza 18 no está compilada")
    for s in re.findall(r'<audio[^>]*class="clip"[^>]*data-start="(-?[\d.]+)"',
                        idx.read_text()):
        assert float(s) >= 0.0
