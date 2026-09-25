"""La medición de la cara — el anclaje del reencuadre.

`measure-face.py` no es importable (lleva guion, igual que
`build-composition.py`), así que lo que se verifica aquí es su SALIDA: el
`assets/face-<n>.json` que consume `build-composition.py`.

Por qué merece test: regenerar la medición para ganar `cx_frac` no puede mover
la barbilla. Si `chin_frac` cambia, la altura del subtítulo cambia en las 4
piezas que ya están publicadas — y eso es justo lo que las congela.
"""
import json


def test_chin_frac_de_la_pieza_10_no_se_mueve(fixtures_root):
    """El valor verificado del plan. Regenerar no lo negocia."""
    face = json.loads((fixtures_root / "assets" / "face-10.json").read_text())
    assert face["chin_frac"] == 0.4324
    assert face["samples"] == 48 and face["hits"] == 48


def test_el_centroide_de_la_cara_esta_en_el_lienzo(fixtures_root):
    face = json.loads((fixtures_root / "assets" / "face-10.json").read_text())
    assert 0.0 <= face["cx_frac"] <= 1.0
    assert 0.0 <= face["cy_frac"] <= 1.0


def test_el_sujeto_esta_cerca_del_centro_horizontal(fixtures_root):
    """Un talking-head encuadrado a mano no se va a un tercio del cuadro.

    Es la comprobación de cordura del detector: un `cx_frac` de 0.1 querría
    decir que el p95 cayó sobre un falso positivo del borde, no sobre la cara.
    """
    face = json.loads((fixtures_root / "assets" / "face-10.json").read_text())
    assert 0.30 <= face["cx_frac"] <= 0.70
