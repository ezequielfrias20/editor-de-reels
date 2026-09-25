"""El gate de resolución de las marcas raster.

Un favicon de 64 px pintado a 110 px en una card se ve blando, y es la clase
de error que no se nota en el JSON y sí en el frame. Se exige 2x.
"""
import importlib.util
import pytest

from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


@pytest.fixture(scope="session")
def fl():
    spec = importlib.util.spec_from_file_location("fetch_logos", SCRIPTS / "fetch-logos.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_64px_no_sirve_para_pintar_a_110(fl, tmp_path):
    from PIL import Image
    p = tmp_path / "chico.png"
    Image.new("RGBA", (64, 64)).save(p)
    alto, pasa = fl.check_raster(p, 110)
    assert alto == 64 and not pasa


def test_1024px_sirve_de_sobra(fl, tmp_path):
    from PIL import Image
    p = tmp_path / "grande.png"
    Image.new("RGBA", (1024, 1024)).save(p)
    alto, pasa = fl.check_raster(p, 110)
    assert alto == 1024 and pasa


def test_el_limite_es_exactamente_el_doble(fl, tmp_path):
    from PIL import Image
    for alto, esperado in ((220, True), (219, False)):
        p = tmp_path / f"m{alto}.png"
        Image.new("RGBA", (alto, alto)).save(p)
        assert fl.check_raster(p, 110)[1] is esperado


def test_las_marcas_vendorizadas_estan_declaradas(fl):
    """Cada marca fuera de Simple Icons, con su fuente oficial escrita.

    Se comprueba el conjunto EXACTO, no una inclusión: lo que este test
    protege es que nadie añada un slug sin pasar por `VENDOR` —y por tanto sin
    dejar escrito de dónde salió el archivo— así que crece a mano cada vez que
    una pieza trae una marca nueva. Las cinco primeras son de la pieza 15; las
    dos siguientes, de la 16; `hyperframes`, de la 18.
    """
    assert set(fl.VENDOR) == {"animejs", "motion", "kokonutui", "bklitui",
                              "manus", "canva", "composio", "hyperframes"}


def test_hyperframes_se_vendoriza_del_subdominio_del_producto(fl):
    """⚠ `hyperframes.dev/favicon.svg` responde 200 y NO es la marca: devuelve
    un icono titulado «EdgeNova App Icon». Un 200 no es una verificación de
    que el archivo sea el logo correcto, y la única forma de saberlo fue
    abrirlo. La fuente buena es el subdominio del producto, que además es el
    que sale en la grabación de la pieza."""
    _titulo, url, fmt = fl.VENDOR["hyperframes"]
    assert url.startswith("https://hyperframes.heygen.com/")
    assert "hyperframes.dev" not in url
    assert fmt == "svg"


# ── Fix round 2/5 — HALLAZGO 2: gate de seguridad del SVG vendorizado ───────
#
# El SVG entra VERBATIM al HTML que Chrome renderiza (logos.py::_fit_svg solo
# toca width/height del <svg> raíz). Hoy los tres SVG vendorizados están
# limpios, pero si mañana se añade una marca nueva o se re-descarga desde una
# URL comprometida, un <script>, un manejador on...= o un foreignObject
# entrarían enteros. El gate falla en la DESCARGA, no en el render.

def test_svg_con_script_se_rechaza(fl):
    malicioso = b'<svg viewBox="0 0 10 10"><script>alert(1)</script></svg>'
    with pytest.raises(SystemExit, match="script"):
        fl._reject_unsafe_svg(malicioso, "test")


def test_svg_con_manejador_de_evento_se_rechaza(fl):
    malicioso = b'<svg viewBox="0 0 10 10"><rect onload="alert(1)" width="10" height="10"/></svg>'
    with pytest.raises(SystemExit, match="on"):
        fl._reject_unsafe_svg(malicioso, "test")


def test_svg_con_foreignobject_se_rechaza(fl):
    malicioso = (b'<svg viewBox="0 0 10 10">'
                 b'<foreignObject><body xmlns="http://www.w3.org/1999/xhtml">'
                 b'hola</body></foreignObject></svg>')
    with pytest.raises(SystemExit, match="foreignObject"):
        fl._reject_unsafe_svg(malicioso, "test")


def test_svg_limpio_no_se_rechaza(fl):
    """Ni un falso positivo: los SVG ya vendorizados tienen que seguir
    pasando el gate sin tocarlos (se leen de assets/logos/, no se escriben)."""
    root = Path.cwd() / "assets" / "logos"
    for slug in ("motion", "manus", "animejs"):
        raw = (root / f"{slug}.svg").read_bytes()
        fl._reject_unsafe_svg(raw, slug)  # no debe lanzar


def test_fetch_vendor_rechaza_un_svg_malicioso_sin_escribir_nada(fl, tmp_path, monkeypatch):
    """Integración: `fetch_vendor()` tiene que invocar el gate ANTES de
    escribir a disco. Se redirige `OUT` a un tmp_path y se monkeypatchea la
    descarga — no se toca `assets/logos/` ni se re-descargan los cinco logos
    reales."""
    import io

    monkeypatch.setattr(fl, "OUT", tmp_path)
    monkeypatch.setitem(
        fl.VENDOR, "malo",
        ("Malo", "https://example.invalid/malo.svg", "svg"))

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'<svg viewBox="0 0 10 10"><script>alert(1)</script></svg>'

    monkeypatch.setattr(fl.urllib.request, "urlopen", lambda *a, **k: FakeResponse())

    meta = {}
    with pytest.raises(SystemExit, match="script"):
        fl.fetch_vendor("malo", meta)
    assert "malo" not in meta
    assert not (tmp_path / "malo.svg").exists()
