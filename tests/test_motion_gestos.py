"""Los dos gestos del triband: horizontal y descendente.

`slide-in` entra desde ABAJO y `chip-in` escala; ninguno sirve para «de
derecha a izquierda». Recorrido pequeño a propósito (§6: el contenedor entra
por opacidad y lo que se mueve es su contenido).
"""
import re

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


# ── regresión: el nonce de `emit_anim` no puede volver a `len(js)` ───────────
#
# Esto no es de glide-x/drop-in — es del refactor de la Tarea 7 que los hizo
# posibles. `hands-sweep` y `count-roll` declaran un `const` con un nombre que
# tiene que ser único DENTRO de un documento (varias llamadas a `emit_anim` se
# concatenan en el mismo <script>). Antes de la extracción, ese nombre salía
# de `len(js)` sobre la lista GLOBAL que iba acumulando build() — creciente y
# por tanto único. Si alguien "simplifica" `emit_anim` de vuelta a un
# `js: list[str] = []` fresco por llamada (que es literalmente lo que sugería
# el brief de la Tarea 7), `len(js)` se reinicia en cada llamada y dos
# animaciones del mismo kind en el mismo documento sacan el MISMO nombre.
#
# No es hipotético: la pieza 12 sube su contador en dos tramos —12→18 y
# 18→27, mismo id "counter"— dentro del MISMO stage (ver
# el golden de la pieza 12, ya retirado), y eso son dos tuplas count-roll
# consecutivas. Con el nonce roto, las dos declararían `const _cv0` y el
# script ENTERO de la pieza rompería con `SyntaxError: Identifier '_cv0' has
# already been declared` — no solo esa animación.
#
# Nota sobre el estado compartido: `_ANIM_NONCE` es un contador de MÓDULO, así
# que estos dos tests lo consumen y lo dejan avanzado para el resto de la
# sesión de pytest (`bc` es session-scoped). Es seguro: ningún otro test del
# repo compara un nombre `_hv`/`_mv`/`_cv` literal (comprobado con
# `grep -rn "_hv\|_mv[0-9]\|_cv[0-9]" tests/`), y las aserciones de aquí abajo
# son sobre la relación ENTRE dos llamadas propias (que no compartan nombre),
# nunca sobre qué número concreto entrega el contador — así que el resultado
# no depende de cuántas veces se haya llamado antes, ni del orden en que
# pytest ejecute los tests.

def _consts(js: str) -> list[str]:
    """Los identificadores `const _xxN` que declara el JS de una animación."""
    return re.findall(r"const (_\w+)\s*=", js)


def test_count_roll_dos_tramos_no_colisiona(bc):
    """El contador de la pieza 12 sube en dos tramos, mismo id, mismo
    documento (12→18 y 18→27 — ver el golden de la pieza 12, ya retirado). Dos
    llamadas a `emit_anim` para ese mismo gesto no pueden declarar el mismo
    `const`, o el script de la pieza entera deja de parsear."""
    js1 = bc.emit_anim(("count-roll", "#counter-num", 3.1333, 0.4333, 12, 18, "#"))
    js2 = bc.emit_anim(("count-roll", "#counter-num", 3.5667, 0.4333, 18, 27, "#"))
    ids1, ids2 = _consts(js1), _consts(js2)
    assert ids1 and ids2, "count-roll debe declarar un const con el valor tuneado"
    assert not (set(ids1) & set(ids2)), (
        f"identificador repetido entre dos count-roll del mismo documento: "
        f"{set(ids1) & set(ids2)} — esto rompería el <script> entero de la pieza")


def test_hands_sweep_dos_instancias_no_colisiona(bc):
    """Mismo mecanismo que count-roll: dos relojes (o el mismo con dos
    barridos) en el mismo documento no pueden compartir `_hv`/`_mv`."""
    a = ("hands-sweep", "#clock-a-h", 1.0, 0.42, 330, 570, "#clock-a-m", 0, 2880)
    b = ("hands-sweep", "#clock-b-h", 5.0, 0.42, 0, 180, "#clock-b-m", 0, 2880)
    ids1, ids2 = _consts(bc.emit_anim(a)), _consts(bc.emit_anim(b))
    assert len(ids1) == 2 and len(ids2) == 2, "hands-sweep declara _hv y _mv"
    assert not (set(ids1) & set(ids2)), (
        f"identificador repetido entre dos hands-sweep del mismo documento: "
        f"{set(ids1) & set(ids2)} — esto rompería el <script> entero de la pieza")
