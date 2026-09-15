"""Fix round 2/5 de la Tarea 6 — HALLAZGO 1.

`logos.mark()` amplió su contrato de retorno de `float` a `float | None`: las
marcas vendorizadas transparentes (animejs, kokonutui) no tienen `tile` propio,
así que no hay contraste que medir y `mark()` devuelve `ratio=None` en vez de
inventar un número.

Ningún llamador existente estaba preparado para eso. `mockups.app_switch` hace
`if ratio < 3: raise ValueError(...)`, y con `ratio=None` eso revienta con un
`TypeError` crudo — el mensaje bien construido de la función nunca llega a
verse. Reproducido con exactamente la llamada que encontró la re-revisión:

    mockups.app_switch("t1", [("animejs", "Anime.js"), ("whatsapp", "WhatsApp")],
                        "whatsapp", [0.5, 1.0])
    → TypeError: '<' not supported between instances of 'NoneType' and 'int'

Cuando `ratio is None` la marca es transparente: no tiene tile propio, así que
la pregunta «¿se distingue el tile del fondo?» no aplica — no hay tile. No se
inventa un número y no se bloquea la marca por algo que no le corresponde
medir.
"""
import mockups


def test_app_switch_con_marca_transparente_no_explota():
    """La llamada exacta que encontró la re-revisión: antes TypeError, ahora
    construye las tres tarjetas sin petar."""
    css, html, anims = mockups.app_switch(
        "t1", [("animejs", "Anime.js"), ("whatsapp", "WhatsApp")],
        "whatsapp", [0.5, 1.0])
    assert "t1-app0" in html
    assert "t1-app1" in html


def test_app_switch_con_dos_marcas_transparentes_tampoco_explota():
    """kokonutui es la otra marca vendorizada sin tile (PNG transparente)."""
    css, html, anims = mockups.app_switch(
        "t1", [("animejs", "Anime.js"), ("kokonutui", "Kokonut UI")],
        "kokonutui", [0.5, 1.0])
    assert "t1-app0" in html
    assert "t1-app1" in html


def test_app_switch_sigue_rechazando_contraste_insuficiente():
    """El gate de contraste sigue vivo para marcas que SÍ tienen tile: no basta
    con que `ratio is None` deje pasar todo sin condición."""
    import pytest
    # motion tiene tile #0B0B0C, casi negro contra la card oscura: por debajo
    # de 3:1 y el gate tiene que seguir disparando.
    with pytest.raises(ValueError, match="contraste de logo insuficiente"):
        mockups.app_switch("t1", [("motion", "Motion"), ("whatsapp", "WhatsApp")],
                            "motion", [0.5, 1.0])


def test_chat_unanswered_ya_descartaba_el_ratio():
    """`chat_unanswered` (mockups.py:623) usa `_ratio` — ya lo descartaba antes
    de este fix. Se confirma que sigue construyendo bien con una marca
    transparente."""
    css, html, anims = mockups.chat_unanswered("t2", "Anime.js", "¿Hola?",
                                                brand="animejs")
    assert "t2-brand" in html
