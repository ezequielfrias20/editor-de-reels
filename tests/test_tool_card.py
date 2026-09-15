"""Las cards de la banda de arriba.

Lo que protegen: que la card entre por OPACIDAD y lo que viaje sea su
contenido (§6), que el logo siga presente en la card de grabación, y que los
radios y la elevación salgan de los tokens y no a mano.
"""
import pytest


@pytest.fixture(scope="session")
def mk():
    import mockups
    return mockups


def test_la_card_no_viaja_su_contenido_si(mk):
    """§6: todo contenedor entra por opacidad; lo que se mueve es lo de dentro."""
    _, _, anims = mk.tool_card("tc", "motion", "Motion")
    kinds = {a[0] for a in anims}
    assert "glide-x" in kinds and "drop-in" in kinds
    sels = {a[1] for a in anims}
    assert not any(s.endswith("-card") for s in sels), "la card no se anima, entra fundiendo"


def test_el_logo_entra_en_horizontal_y_el_nombre_cae(mk):
    _, _, anims = mk.tool_card("tc", "motion", "Motion")
    por_kind = {a[0]: a[1] for a in anims}
    assert por_kind["glide-x"].endswith("-logo")
    assert por_kind["drop-in"].endswith("-name")


def test_el_nombre_entra_despues_del_logo(mk):
    """El retraso es lo que hace que se lean como dos elementos."""
    _, _, anims = mk.tool_card("tc", "motion", "Motion")
    d = {a[0]: a[2] for a in anims}
    assert d["drop-in"] > d["glide-x"]


def test_la_card_de_grabacion_conserva_la_marca(mk):
    """Sin el chip, 8 s de grabación se desatan de su nombre."""
    _, html, _ = mk.tool_recording("tr", "motion", "Motion", (60, 140, 960, 540))
    assert "Motion" in html


def test_ninguna_card_usa_negro_puro(mk):
    for css, _, _ in (mk.tool_card("a", "motion", "Motion"),
                      mk.tool_recording("b", "motion", "Motion", (60, 140, 960, 540))):
        low = css.lower().replace(" ", "")
        assert "#000000" not in low and "#000;" not in low


def test_el_radio_sale_de_los_tokens(mk):
    import tokens
    css, _, _ = mk.tool_card("tc", "motion", "Motion")
    assert f"{tokens.RADIUS['lg']}px" in css
