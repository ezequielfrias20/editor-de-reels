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


def test_las_cinco_marcas_estan_declaradas(fl):
    assert set(fl.VENDOR) == {"animejs", "motion", "kokonutui", "bklitui", "manus"}
