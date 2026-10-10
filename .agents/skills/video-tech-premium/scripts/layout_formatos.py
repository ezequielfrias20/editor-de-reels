"""Los layouts de un REEL: `formatos` (la doctrina desde 2026-09-29), `triband` (piezas
de antes) y la escotilla `none`.

`formatos` reparte el lienzo en dos bandas a la MITAD exacta: arriba el visual (`top`),
abajo el hablante (`speaker`). Las otras dos formas de la pieza no necesitan banda: la
cara a lienzo completo es un encuadre `full` y el gráfico a lienzo completo es un
encuadre `off` bajo un visual opaco. La geometría no se escribe en el plan: la fija la
doctrina, así que un plan declara solo `{"mode": "formatos"}` y aquí se completa.
"""
MODOS = ("formatos", "triband", "none")


class LayoutError(ValueError):
    pass


def resolver(layout: dict | None, H: int) -> dict:
    """El bloque `layout` del plan, completo. `{}` si el plan no trae ninguno."""
    if not layout:
        return {}
    modo = layout.get("mode")
    if modo not in MODOS:
        raise LayoutError(f"layout.mode {modo!r} no existe; los modos son {', '.join(MODOS)}")
    if modo == "none":
        return {"mode": "none"}
    if modo == "formatos":
        mitad = H // 2
        bandas = {"top": [0, mitad], "speaker": [mitad, H]}
        dadas = layout.get("bands")
        if dadas and dadas != bandas:
            raise LayoutError(f"layout formatos: las bandas las fija la doctrina ({bandas}); "
                              f"quita `bands` del plan")
        return {"mode": "formatos", "bands": bandas}
    bandas = layout.get("bands") or {}
    if set(bandas) != {"top", "text", "speaker"}:
        raise LayoutError("layout triband: necesita sus tres bandas, top, text y speaker")
    return {"mode": "triband", "bands": bandas}


def costura(layout: dict) -> int | None:
    """La línea de división de `formatos`, donde se centra el subtítulo; None en otro modo."""
    return layout["bands"]["top"][1] if layout.get("mode") == "formatos" else None
