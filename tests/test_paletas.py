"""Las dos paletas de la marca (claro / oscuro) y lo que se deriva de ellas.

Los valores base son los de dashboard/web/src/app/theme.css. Todo lo demás se
DERIVA con una regla y se MIDE aquí: si un par baja del mínimo, se ajusta la
regla en tokens.py, nunca el componente."""
import pytest

import tokens as T


@pytest.fixture(autouse=True)
def _restaurar():
    yield
    T.use("oscuro")


BASE = {
    "claro": {"bg": "#ECE7DE", "surface": "#F7F4EE", "text": "#1C1A16", "accent": "#C45F38",
              "on_accent": "#FFFFFF", "line": "#D8D1C4"},
    "oscuro": {"bg": "#161412", "surface": "#201D1A", "text": "#EEE8DF", "accent": "#E27B52",
               "on_accent": "#1A0F0A", "line": "#36312B"},
}


def test_hay_exactamente_dos_paletas():
    assert T.PALETTES == ("claro", "oscuro")


@pytest.mark.parametrize("nombre", ["claro", "oscuro"])
def test_valores_base_copiados_del_dashboard(nombre):
    T.use(nombre)
    assert T.PALETTE == nombre
    for k, v in BASE[nombre].items():
        assert T.C[k] == v, k
    assert T.LINE == BASE[nombre]["line"]


@pytest.mark.parametrize("nombre", ["claro", "oscuro"])
def test_contrastes_minimos(nombre):
    T.use(nombre)
    c = T.C
    assert T.contrast(c["text"], c["surface"]) >= 4.5
    assert T.contrast(c["text2"], c["surface"]) >= 4.5
    assert T.contrast(c["text3"], c["surface"]) >= 4.5
    assert T.contrast(c["accent_hi"], c["bg"]) >= 4.5      # acento como TEXTO
    assert T.contrast(c["accent_hi"], T.lift(c["bg"], T.SPOTLIGHT_MAX)) >= 4.5  # bajo el foco del stage
    assert T.contrast(c["accent_lt"], c["bg"]) >= 7.0      # acento como texto que FUNDE
    assert T.contrast(c["text"], c["accent_pill"]) >= 4.5  # palabra del karaoke sobre su pastilla
    assert T.contrast(c["on_accent"], c["accent"]) >= 3.0  # solo texto grande en negrita
    for sem in ("warning", "success"):
        fill = c["warn"] if sem == "warning" else c["go"]
        assert T.contrast(T.INK_ON_FILL[sem], fill) >= 3.0


@pytest.mark.parametrize("nombre", ["claro", "oscuro"])
def test_text3_es_mas_tenue_que_text2(nombre):
    T.use(nombre)
    s = T.C["surface"]
    assert T.contrast(T.C["text3"], s) <= T.contrast(T.C["text2"], s)


@pytest.mark.parametrize("nombre", ["claro", "oscuro"])
def test_sin_negro_ni_blanco_puro_de_fondo(nombre):
    T.use(nombre)
    for k in ("bg", "bg2", "surface", "surface2", "surface3"):
        assert T.C[k].upper() not in ("#000000", "#FFFFFF"), k


def test_use_muta_en_su_lugar():
    c, fill, theme = T.C, T.FILL, T.THEME
    T.use("claro")
    assert T.C is c and T.FILL is fill and T.THEME is theme
    assert T.C["bg"] == "#ECE7DE"
    assert T.THEME["primary"]["accent"] == T.C["accent"]
    assert T.FILL["accent"] == T.rgba(T.C["accent"], .16)


def test_helpers_leen_la_paleta_activa():
    T.use("claro")
    assert T.accent_a(.5) == "rgba(196,95,56,.5)"
    T.use("oscuro")
    assert T.accent_a(.5) == "rgba(226,123,82,.5)"
    assert T.shade_a(.8) == "rgba(22,20,18,.8)"
    assert T.ink_a(.05) == "rgba(238,232,223,.05)"


def test_paleta_inexistente_falla_con_las_opciones():
    with pytest.raises(ValueError) as e:
        T.use("violeta")
    assert "claro" in str(e.value) and "oscuro" in str(e.value)


def test_al_importar_la_activa_es_oscuro():
    # En un proceso aparte: recargar `tokens` aquí crearía dicts nuevos y los
    # módulos que ya importaron `C` por nombre quedarían mirando los viejos.
    import subprocess
    import sys
    from pathlib import Path
    scripts = Path(T.__file__).parent
    out = subprocess.run([sys.executable, "-c", "import tokens; print(tokens.PALETTE)"],
                         cwd=scripts, capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "oscuro"
