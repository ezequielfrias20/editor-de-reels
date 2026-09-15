"""Los dos gestos del triband: horizontal y descendente.

`slide-in` entra desde ABAJO y `chip-in` escala; ninguno sirve para «de
derecha a izquierda». Recorrido pequeño a propósito (§6: el contenedor entra
por opacidad y lo que se mueve es su contenido).
"""
import pytest

GLIDE_X = 72
DROP_Y = -22


def test_glide_x_viaja_en_horizontal_y_acaba_en_cero(bc):
    js = bc.emit_anim(("glide-x", "#logo", 0.10, 0.45))
    assert f"x:{GLIDE_X}" in js.replace(" ", "")
    assert "x:0" in js.replace(" ", "")


def test_glide_x_no_usa_muelle(bc):
    """back.out() es lenguaje de dibujo animado y choca con una pieza de producto."""
    assert "back.out" not in bc.emit_anim(("glide-x", "#logo", 0.10, 0.45))
    assert "power2.out" in bc.emit_anim(("glide-x", "#logo", 0.10, 0.45))


def test_drop_in_cae_desde_arriba(bc):
    js = bc.emit_anim(("drop-in", "#nombre", 0.18, 0.40)).replace(" ", "")
    assert f"y:{DROP_Y}" in js
    assert "power3.out" in js


def test_los_dos_entran_por_opacidad(bc):
    for kind in ("glide-x", "drop-in"):
        assert "opacity:0" in bc.emit_anim((kind, "#x", 0.1, 0.4)).replace(" ", "")


def test_el_recorrido_es_pequeno(bc):
    """§6: «el recorrido y la escala de entrada son pequeños»."""
    assert GLIDE_X <= 80 and abs(DROP_Y) <= 30
