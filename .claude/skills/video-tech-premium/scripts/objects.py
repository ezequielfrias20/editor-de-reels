#!/usr/bin/env python3
"""Objetos con estado y el escenario que los sostiene.

Mismo contrato que `mockups.py`: cada función devuelve `(css, html, anims)`.

EL STAGE ES UNO, NO UNO POR SEGMENTO. La serie entera de segmentos contiguos
sale como una sola entrada de `visuals`, con un `fade_in` al principio y un
`fade_out` al final. Dos takeovers seguidos abrían un hueco de 0.15-0.25 s en el
cruce que se leía como un fallo — la razón de existir de `check_no_black()`.
Con un stage continuo esa clase de bug no puede ocurrir.
"""
from __future__ import annotations

import tokens as t


def motion_stage(cid: str, theme: str = "primary", objects=None, at=None,
                 spotlight_alpha: float = t.SPOTLIGHT_MAX, seed: int = 7, **_):
    if theme not in t.THEME:
        raise KeyError(f"tema '{theme}' desconocido; hay {sorted(t.THEME)}")
    th = t.THEME[theme]
    objects, at = list(objects or []), list(at or [])

    css = f"""
/* Motion Stage — suelo continuo de una serie de segmentos.
   El fondo va en un ELEMENTO del DOM: el `background` de la página se descarta
   en el render (trampa nº1), y el fill de una escena a pantalla completa nunca
   va en la raíz de la composición. */
#{cid} .stage-ground{{position:absolute;inset:0;
  background:{t.spotlight(spotlight_alpha)},{t.grid()},{t.vignette()}}}
#{cid} .stage-grain{{position:absolute;inset:0;pointer-events:none;
  background-image:{t.grain(seed)};background-repeat:repeat}}
#{cid} .stage-plane{{position:absolute;inset:0}}
#{cid} .obj{{position:absolute;display:block;opacity:0;
  transform-origin:50% 50%;filter:drop-shadow({t.SHADOW.split(',')[0]})}}
#{cid} .obj.accent{{color:{th['accent_text']}}}
#{cid} .obj .fill{{background:{th['fill']}}}
#{cid} .obj.hero{{box-shadow:{th['glow']}}}
#{cid} .stage-type{{color:{t.C['text']};font-family:{t.FONT};font-weight:900}}
"""
    cuerpo = "".join(o["html"] for o in objects)
    html = (f'<div class="stage-ground"></div>'
            f'<div class="stage-plane">{cuerpo}</div>'
            f'<div class="stage-grain"></div>')

    anims: list = []
    for o in objects:
        anims.extend(o.get("anims", []))
    for op in at:
        anims.extend(op.get("anims", []))
    return css, html, anims


REGISTRY = {"motion_stage": motion_stage}
