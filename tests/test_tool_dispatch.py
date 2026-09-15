"""Cableado de `tool_card` / `tool_recording` en `build_visuals` — Tarea 8b.

Los dos componentes ya viven en `mockups.py`, con sus propios tests de
componente en `test_tool_card.py`. Pero `build_visuals` los ignoraba por
completo: el diccionario literal de la rama "mockup" no traía `"tool_card"` —
un `mock: ["tool_card", …]` reventaba con `KeyError` — y la rama
"video"/"screen-video" no sabía leer ningún tratamiento para `tool_recording`,
así que su `rect` se perdía.

Estos tests pasan por el camino REAL de una pieza: `plan.json` → `VISUALS` →
`build_visuals()`. Nunca llaman a `mockups.tool_card`/`tool_recording`
directo — eso ya está cubierto.
"""
import re

import pytest
import tokens


@pytest.fixture(autouse=True)
def lienzo_reel(bc):
    """`build_visuals` lee `W`/`H` como globals, igual que `shot_geometry`
    (ver `test_shot_geometry.py`) — no se le pasan por parámetro."""
    bc.W, bc.H = 1080, 1920
    yield


def _visual_tool_card(**over):
    """Mismo molde que usa cualquier otro mockup en un `plan.json` real
    (p. ej. `comment_ui` en `videos/2/plan.json`): `kind: "mockup"` y
    `mock: [which, kw]`."""
    v = {
        "id": "v-tool",
        "role": "takeover",
        "kind": "mockup",
        "start": 0.0,
        "end": 2.0,
        "mock": ["tool_card", {"slug": "motion", "name": "Motion",
                                "kicker": "HERRAMIENTA"}],
    }
    v.update(over)
    return v


def _visual_tool_recording(**over):
    """`tool_recording` no es un mockup suelto: envuelve un `<video>` real,
    igual que `chrome`/`panel` envuelven el de `browser_frame`/
    `screen_panel` — por eso su `rect` vive en el visual, no dentro de un
    `kw` de mockup."""
    v = {
        "id": "v-rec",
        "role": "takeover",
        "kind": "screen-video",
        "start": 0.0,
        "end": 8.0,
        "src": "motion-tour.mp4",
        "rect": [60, 140, 960, 540],
        "tool_recording": {"slug": "motion", "name": "Motion"},
    }
    v.update(over)
    return v


def test_tool_card_se_despacha_desde_un_plan_json(bc):
    """Antes de cablearlo esto reventaba con `KeyError: 'tool_card'`."""
    bc.VISUALS = [_visual_tool_card()]
    css, media, hosts_back, hosts_over, anims, skins, assets = bc.build_visuals(2.0)
    assert css.strip(), "sin CSS no hay card que ver"
    html = "\n".join(hosts_over)
    assert html.strip(), "sin HTML no hay card que ver"
    assert "tc-card" in html and "Motion" in html


def test_tool_recording_se_despacha_con_su_rect(bc):
    """El trato tiene que ser el mismo que ya reciben `chrome`/`panel`: se
    lee `v["rect"]` y se dibuja ALREDEDOR del `<video>`, que sigue suelto en
    `media` (media anidada en un elemento temporizado se congela)."""
    bc.VISUALS = [_visual_tool_recording()]
    css, media, hosts_back, hosts_over, anims, skins, assets = bc.build_visuals(8.0)
    assert css.strip()
    html = "\n".join(hosts_over)
    assert html.strip()
    assert "tr-panel" in html and "Motion" in html
    assert any("motion-tour.mp4" in m for m in media), \
        "el <video> real tiene que seguir suelto en el stage, no dentro del host"


def test_tool_recording_propaga_el_hairline(bc):
    """`hairline` es un parámetro real de `tool_recording` (grabaciones
    claras como Manus necesitan un marco más marcado); el cableado tiene que
    dejarlo pasar del `plan.json` a la función."""
    bc.VISUALS = [_visual_tool_recording(
        tool_recording={"slug": "manus", "name": "Manus", "hairline": 3})]
    css, *_ = bc.build_visuals(8.0)
    assert "border:3px solid" in css


def _video_radius(media, src):
    """El `border-radius` que `build_visuals` le puso al `<video>` suelto
    que apunta a `src`, leído del `style=` real que emite — no supuesto."""
    entry = next(m for m in media if src in m)
    m = re.search(r'border-radius:([^"]+)"', entry)
    assert m, "el <video> no declara border-radius"
    return m.group(1)


def test_tool_recording_gana_sobre_chrome_en_el_mismo_rect(bc):
    """`chrome`, `panel` y `tool_recording` son tratamientos EXCLUYENTES del
    mismo `rect` — declarar los dos a la vez no debe mezclar los dos marcos,
    solo uno gana, igual que hoy `chrome` ya gana sobre `panel`.

    Ganar el HTML no basta: `.tr-panel` redondea las CUATRO esquinas, así que
    el `<video>` que enmarca tiene que llevar el mismo radio parejo — no el
    recorte `0 0 lg lg` que solo tiene sentido bajo la barra de 74 px de
    `chrome`. Con las esquinas de `chrome` puestas, la esquina superior
    cuadrada del video asoma por debajo del marco redondeado del panel: una
    costura real, no solo una etiqueta CSS de más.
    """
    bc.VISUALS = [_visual_tool_recording(chrome={"url": "x.com", "brand": "X"})]
    css, media, hosts_back, hosts_over, anims, skins, assets = bc.build_visuals(8.0)
    assert "tr-panel" in "\n".join(hosts_over)
    assert "bframe" not in css, "el chrome de navegador no debería dibujarse a la vez"
    radius = _video_radius(media, "motion-tour.mp4")
    assert radius == f"{tokens.RADIUS['lg']}px", (
        f"el <video> quedó con esquinas de chrome ({radius!r}) bajo un panel "
        "de tool_recording que las redondea las cuatro"
    )
