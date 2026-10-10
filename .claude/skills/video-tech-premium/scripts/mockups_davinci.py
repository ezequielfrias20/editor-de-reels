#!/usr/bin/env python3
"""DaVinci Resolve + MCP para la pieza 9.

La ventana, la línea de tiempo y el conector son primitivas compartidas. Las
imágenes se referencian por ruta relativa y todos los tiempos entran por
``at`` como offsets del visual.
"""

from __future__ import annotations


import math

import logos
import tokens as TK
from mockups import text_px
from mockups_codex import (
    _P,
    _check,
    _encender,
    _logo,
    _mosaico as _mosaico_base,
    _personaje,
    _pose,
    _suelo,
    _svg,
    _wrap as _wrap_base,
)
from mockups_plugins import _need_at
from tokens import C, FONT, MONO, RADIUS, esc, mix, rgba


PEDIDOS = (
    "Corrige el color de todos los clips: más contraste y la piel natural.",
    "Arma un título animado con mi nombre al entrar cada sección.",
    "Corta en multicámara siguiendo a quien habla.",
    "Pon un whoosh en cada corte y un pop cuando aparezca un texto.",
    "Ajusta la música para que los golpes caigan sobre los cortes.",
    "Si falta un plano entre dos escenas, genéralo con Higgsfield y ponlo en el hueco.",
)

_FONDOS = ("claro", "oscuro", "comic")
_PAGES = ("Media", "Cut", "Edit", "Fusion", "Color", "Fairlight", "Deliver")


def _validate_fondo(fondo: str) -> dict:
    if fondo not in _FONDOS:
        raise ValueError(f"fondo {fondo!r} no existe")
    return _P(fondo)


def _clip_color(tipo: str) -> str:
    dv = TK.BRANDS["davinci"]
    table = {"video": dv["video"], "video2": dv["video2"],
             "audio": dv["audio"], "music": dv["music"]}
    if tipo not in table:
        raise ValueError(f"tipo de clip {tipo!r} no existe")
    return table[tipo]


def _wave(iid: str, color: str, bars: int = 18, ids: bool = False) -> str:
    rects = []
    for i in range(bars):
        height = 8 + ((i * 17 + 11) % 25)
        rid = f' id="{iid}-w{i}"' if ids else ""
        rects.append(
            f'<rect{rid} x="{i * 6 + 2}" y="{22 - height / 2:.1f}" '
            f'width="3" height="{height}" rx="1.5"/>'
        )
    return (f'<svg viewBox="0 0 {bars * 6 + 4} 44" preserveAspectRatio="none" '
            f'aria-hidden="true" style="color:{color}">{"".join(rects)}</svg>')


def _timeline(iid: str, w: int, h: int, pistas, medidores: bool = False,
              row_height: int | None = None) -> str:
    """Regla, pistas, clips, cabezal y VU de la interfaz literal."""
    dv = TK.BRANDS["davinci"]
    if not isinstance(pistas, (list, tuple)) or not pistas:
        raise ValueError("pistas debe ser una lista no vacía")
    natural_row_h = max(38, math.floor((h - 42) / len(pistas)))
    row_h = row_height if row_height is not None else natural_row_h
    if row_height is not None and (row_h < 38 or 30 + row_h * len(pistas) > h):
        raise ValueError("row_height no cabe en la línea de tiempo")
    rule_marks = "".join(
        f'<i style="left:{56 + i * 40}px"></i>' for i in range(max(1, (w - 80) // 40))
    )
    rule_labels = "".join(
        f'<b style="left:{56 + i * (w - 100) / 3}px">00:00:{i * 4:02d}:00</b>'
        for i in range(3)
    )
    rows = []
    for pi, track in enumerate(pistas):
        label = ("V" if pi < 3 else "A") + str(pi + 1 if pi < 3 else pi - 2)
        if track and len(track[0]) == 5:
            label = str(track[0][4])
        clips = []
        for ci, clip in enumerate(track):
            if len(clip) not in (4, 5):
                raise ValueError(f"clip inválido en pista {pi}: {clip!r}")
            x, cw, tipo, toma = clip[:4]
            color = _clip_color(tipo)
            media = ""
            if tipo in ("video", "video2") and toma:
                media = f'<img src="{toma}" alt=""/>'
            elif tipo in ("audio", "music"):
                media = _wave(f"{iid}-c{pi}-{ci}", dv["text"], 18)
            clips.append(
                f'<span class="dv-clip dv-{tipo}" id="{iid}-c{pi}-{ci}" '
                f'style="left:{x}px;width:{cw}px;background:{color}">'
                f'<i style="background:{rgba(dv["text"], .35)}"></i>{media}</span>'
            )
        rows.append(
            f'<div class="dv-track" id="{iid}-track{pi}" style="height:{row_h}px">'
            f'<b class="dv-track-head">{esc(label)}</b><span class="dv-track-body">'
            f'{"".join(clips)}</span></div>'
        )
    vu = ""
    if medidores:
        vu = (f'<span class="dv-vu" id="{iid}-vu"><i id="{iid}-vu0"></i>'
              f'<i id="{iid}-vu1"></i></span>')
    return (
        f'<div class="dv-timeline" id="{iid}" style="width:{w}px;height:{h}px">'
        f'<div class="dv-rule">{rule_marks}{rule_labels}</div>'
        f'<div class="dv-tracks">{"".join(rows)}</div>'
        f'<span class="dv-playhead" id="{iid}-ph"><span id="{iid}-ph-move">'
        f'<span id="{iid}-ph-jitter"><i></i><b></b></span></span></span>{vu}</div>'
    )


def _transport() -> str:
    return (f'<span class="dv-transport">{_svg("<path d=\"m9 7 8 5-8 5z\"/>", 22)}'
            f'{_svg("<path d=\"M7 6v12M17 6v12\"/>", 22)}'
            f'{_svg("<path d=\"m15 7-8 5 8 5z\"/>", 22)}</span>')


def _davinci(cid: str, w: int, h: int, *, visor: str | None = None,
             pistas=None, pagina: str = "edit", body_extra: str = "",
             nombre: bool = False, medidores: bool = False,
             timeline: bool = True, timeline_h: int | None = None,
             viewer_h: int | None = None,
             track_h: int | None = None) -> str:
    """La única ventana de DaVinci usada por todos los componentes."""
    dv = TK.BRANDS["davinci"]
    mac = TK.BRANDS["macos"]
    if pagina not in tuple(p.lower() for p in _PAGES):
        raise ValueError(f"página DaVinci {pagina!r} no existe")
    if pistas is None:
        pistas = _tracks_basic()
    title = f'<span id="{cid}-title-name"></span>' if nombre else ""
    viewer = ""
    if visor:
        vh = viewer_h if viewer_h is not None else max(150, round(h * .42))
        viewer = (
            f'<div class="dv-viewer" style="height:{vh}px"><img src="{visor}" alt=""/>'
            f'<span class="dv-tc">00:00:12:04</span>{_transport()}</div>'
        )
    pages = "".join(
        f'<span class="dv-page {"is-active" if label.lower() == pagina else ""}">'
        f'{_svg("<path d=\"M5 17h14M7 13h10M9 9h6\"/>", 19)}<b>{label}</b></span>'
        for label in _PAGES
    )
    natural_viewer_h = (viewer_h if viewer_h is not None
                        else max(150, round(h * .42))) if visor else 0
    actual_timeline_h = (timeline_h if timeline_h is not None
                         else max(130, h - (36 + 54 + natural_viewer_h)))
    timeline_html = (_timeline(f"{cid}-tl", w - 24, actual_timeline_h,
                               pistas, medidores, track_h) if timeline else "")
    return (
        f'<div class="dv-window" id="{cid}-window" style="width:{w}px;height:{h}px;'
        f'background:{dv["bg"]};border-color:{dv["line"]}">'
        f'<div class="dv-title" style="background:{dv["panel"]}">'
        f'<span class="dv-lights"><i style="background:{mac["close"]}"></i>'
        f'<i style="background:{mac["minimize"]}"></i>'
        f'<i style="background:{mac["maximize"]}"></i></span>{title}</div>'
        f'<div class="dv-main">{viewer}{timeline_html}{body_extra}</div>'
        f'<div class="dv-pages" style="background:{dv["panel"]}">{pages}</div></div>'
    )


def _conector(iid: str, P: dict, px: int = 120, neon: bool = False,
              logo: bool = False) -> str:
    del P
    dv = TK.BRANDS["davinci"]
    path = '<path d="M18 16h68a18 18 0 0 1 18 18v38a18 18 0 0 1-18 18H18z"/>'
    outline = (f'<svg class="dv-plug-neon" viewBox="0 0 120 110" aria-hidden="true">'
               f'<path id="{iid}-outline" d="M18 16h68a18 18 0 0 1 18 18v38a18 18 0 0 1-18 18H18"/></svg>') if neon else ""
    logo_html = (_logo(f"{iid}-mcp", "modelcontextprotocol", round(px * .46))
                 if logo else "")
    return (
        f'<span class="dv-plug" id="{iid}" style="width:{px}px;height:{round(px * .92)}px;'
        f'color:{dv["text"]}">{outline}<svg viewBox="0 0 120 110" aria-hidden="true">'
        f'{path}<path d="M104 42h13M104 64h13"/></svg>'
        f'<span class="dv-plug-logo" id="{iid}-logo">{logo_html}</span></span>'
    )


def _zocalo(iid: str, P: dict) -> str:
    return (
        f'<span class="dv-socket" id="{iid}" style="background:{P["surface2"]};'
        f'border-color:{P["line"]}"><i></i><i></i>'
        f'<b id="{iid}-luz" style="background:{P["accent_hi"]}"></b></span>'
    )


def _mosaico(iid: str, slug: str, P: dict, px: int = 150,
             nombre: str | None = None, *, logo: bool = True) -> str:
    """Mosaico compartido con una pastilla vacía para el nombre diferido."""
    valid = {"claude", "openai", "davinciresolve", "modelcontextprotocol",
             "adobepremierepro", "higgsfield"}
    if slug not in valid:
        raise ValueError(f"mosaico {slug!r} no existe")
    if logo:
        tile = _mosaico_base(iid, slug, P, px)
    else:
        tile = (f'<span class="cx-mosaic dv-empty-app" id="{iid}" '
                f'style="width:{px}px;height:{px}px;background:{P["surface2"]};'
                f'border-color:{P["line"]}"><span id="{iid}-logo"></span></span>')
    name = f'<span class="dv-app-name" id="{iid}-name"></span>' if nombre is not None else ""
    return f'<span class="dv-app-wrap" id="{iid}-wrap">{tile}{name}</span>'


def _burbuja(iid: str, texto: str, P: dict, legible: bool = False,
             vacia: bool = False) -> str:
    # La copia borrosa lleva el texto REAL del pedido (desenfocado, ilegible): así la burbuja
    # se lee como texto y en el clímax enfoca lo mismo que estaba borroso. La nítida se
    # llena en su instante (caret-off) y solo existe en el clímax.
    sharp = f'<span class="dv-bubble-n" id="{iid}-n"></span>' if legible else ""
    blurred = "" if vacia else f'<span id="{iid}-b-text">{esc(texto)}</span>'
    return (
        f'<span class="dv-bubble" id="{iid}" style="background:{P["surface"]};'
        f'border-color:{P["line"]}"><span class="dv-bubble-b" id="{iid}-b">'
        f'{blurred}</span>{sharp}</span>'
    )


def _tracks_basic(toma: str = "imagenes-9/toma-2.jpg"):
    return [
        [(20, 170, "video2", toma, "V2")],
        [(20, 230, "video", toma, "V1"), (260, 180, "video", toma), (450, 210, "video", toma)],
        [(20, 300, "audio", None, "A1"), (330, 330, "audio", None)],
        [(20, 640, "music", None, "A2")],
    ]


def _wheels(iid: str) -> str:
    labels = ("Lift", "Gamma", "Gain")
    return '<span class="dv-wheels">' + "".join(
        f'<span class="dv-wheel" id="{iid}-wheel{i}"><i></i><b id="{iid}-dot{i}"></b>'
        f'<em>{label}</em></span>' for i, label in enumerate(labels)
    ) + '</span>'


def _scope(iid: str, filled: bool = False) -> str:
    dots = "".join(
        f'<i id="{iid}-bar{i}" style="left:{i * 8 + 8}px;height:{12 + (i * 19) % 75}px;'
        f'opacity:{1 if filled else 0}"></i>' for i in range(18)
    )
    return f'<span class="dv-scope" id="{iid}">{dots}</span>'


def _nodes(iid: str) -> str:
    return (f'<span class="dv-nodes" id="{iid}"><svg viewBox="0 0 280 150">'
            f'<path id="{iid}-path" d="M72 70 C110 20 150 120 204 68"/></svg>'
            f'<i></i><i></i><i></i></span>')


def _css(cid: str, P: dict) -> str:
    p = f'.viz[data-viz-id="{cid}"]'
    dv = TK.BRANDS["davinci"]
    light = mix(dv["line"], dv["text"], .25)
    return f"""
{p} .dv-stage{{position:relative;width:980px;height:100%;display:flex;align-items:center;justify-content:center;font-family:{FONT};color:{P['text']}}}
{p} .dv-dark-glow{{position:absolute;width:720px;height:720px;border-radius:999px;background:{rgba(P['accent'], .10)};filter:blur(90px)}}
{p} .dv-window{{position:relative;box-sizing:border-box;overflow:hidden;border:1px solid;border-radius:{RADIUS['md']}px;box-shadow:{TK.SHADOW};color:{dv['text']}}}
{p} .dv-title{{height:36px;display:flex;align-items:center;justify-content:center;border-bottom:1px solid {dv['line']};font:600 15px {FONT};color:{dv['text2']}}}
{p} .dv-lights{{position:absolute;left:13px;display:flex;gap:7px}}{p} .dv-lights i{{width:10px;height:10px;border-radius:999px;display:block}}
{p} .dv-main{{position:absolute;left:0;right:0;top:36px;bottom:54px;padding:6px 12px;box-sizing:border-box;display:flex;flex-direction:column;gap:6px}}
{p} .dv-viewer{{position:relative;flex:none;background:{dv['panel']};display:flex;align-items:center;justify-content:center;overflow:hidden}}
{p} .dv-viewer>img{{height:calc(100% - 42px);aspect-ratio:9/16;object-fit:cover}}
{p} .dv-tc{{position:absolute;left:18px;bottom:10px;font:700 18px {MONO};color:{dv['tc']}}}
{p} .dv-transport{{position:absolute;right:20px;bottom:7px;display:flex;gap:12px;color:{dv['text2']}}}
{p} .dv-timeline{{position:relative;flex:none;box-sizing:border-box;background:{dv['bg']};border:1px solid {dv['line']};overflow:hidden}}
{p} .dv-rule{{height:30px;position:relative;margin-left:0;background:{dv['panel']};border-bottom:1px solid {dv['line']}}}
{p} .dv-rule i{{position:absolute;bottom:0;width:1px;height:8px;background:{dv['text2']}}}{p} .dv-rule b{{position:absolute;top:3px;font:500 10px {MONO};color:{dv['text2']}}}
{p} .dv-tracks{{position:absolute;left:0;right:0;top:30px;bottom:0}}{p} .dv-track{{position:relative;box-sizing:border-box;border-bottom:1px solid {dv['line']}}}
{p} .dv-track-head{{position:absolute;left:0;top:0;bottom:0;width:56px;display:flex;align-items:center;justify-content:center;background:{dv['panel']};font:700 14px {MONO};color:{dv['text2']}}}
{p} .dv-track-body{{position:absolute;left:56px;right:24px;top:0;bottom:0;background:{dv['panel2']}}}
{p} .dv-clip{{position:absolute;top:4px;bottom:4px;overflow:hidden;border-radius:3px;border-top:2px solid {light};box-sizing:border-box}}
{p} .dv-clip>i{{position:absolute;left:5px;right:5px;top:4px;height:4px;border-radius:2px;z-index:2}}
{p} .dv-clip img{{width:100%;height:100%;object-fit:cover;opacity:.85}}{p} .dv-clip svg{{position:absolute;inset:4px;width:calc(100% - 8px);height:calc(100% - 8px);fill:currentColor;opacity:.72}}
{p} .dv-playhead{{position:absolute;left:56px;top:27px;bottom:0;width:calc(100% - 80px);pointer-events:none}}{p} .dv-playhead>span{{position:absolute;left:0;top:0;bottom:0;width:2px;background:{dv['playhead']}}}{p} .dv-playhead>span>span{{position:absolute;inset:0;background:{dv['playhead']}}}
{p} .dv-playhead i{{position:absolute;left:-6px;top:-1px;width:14px;height:10px;background:{dv['playhead']};clip-path:polygon(0 0,100% 0,70% 100%,30% 100%)}}
{p} .dv-vu{{position:absolute;right:3px;top:38px;bottom:5px;width:18px;display:flex;align-items:flex-end;gap:3px}}{p} .dv-vu i{{width:6px;height:22%;background:{dv['ok']};transform-origin:50% 100%}}
{p} .dv-pages{{position:absolute;left:0;right:0;bottom:0;height:54px;display:flex;align-items:center;justify-content:center;gap:18px;border-top:1px solid {dv['line']}}}
{p} .dv-page{{display:flex;flex-direction:column;align-items:center;gap:2px;color:{dv['text2']}}}{p} .dv-page b{{font:500 10px {FONT}}}{p} .dv-page.is-active{{color:{dv['tc']}}}
{p} .dv-plug{{position:relative;display:flex;align-items:center;justify-content:center}}{p} .dv-plug>svg:not(.dv-plug-neon){{position:absolute;inset:0;width:100%;height:100%;fill:currentColor;stroke:{P['accent_hi']};stroke-width:3}}
{p} .dv-plug-neon{{position:absolute;inset:0;width:100%;height:100%;fill:none;stroke:{P['accent_hi']};stroke-width:3;filter:drop-shadow(0 0 10px {rgba(P['accent'], .45)})}}
{p} .dv-plug-logo{{position:relative;z-index:2;width:54%;height:54%;display:flex;align-items:center;justify-content:center;color:{P['bg']}}}
{p} .dv-socket{{position:relative;width:126px;height:92px;border:3px solid;border-radius:{RADIUS['md']}px;box-shadow:inset 0 5px 18px {rgba(P['text'], .16)}}}{p} .dv-socket>i{{position:absolute;right:15px;width:18px;height:7px;border-radius:3px;background:{P['text2']}}}{p} .dv-socket>i:first-child{{top:25px}}{p} .dv-socket>i:nth-child(2){{top:55px}}
{p} .dv-socket>b{{position:absolute;left:12px;top:38px;width:14px;height:14px;border-radius:999px;opacity:0;box-shadow:{TK.GLOW}}}
{p} .dv-app-wrap{{position:relative;display:flex;flex-direction:column;align-items:center;gap:10px}}{p} .dv-empty-app{{display:flex;align-items:center;justify-content:center;box-sizing:border-box;border:1px solid;border-radius:36px;box-shadow:{TK.SHADOW}}}
{p} .dv-app-name{{min-width:110px;height:28px;padding:0 12px;border-radius:{RADIUS['pill']}px;background:{P['surface2']};display:flex;align-items:center;justify-content:center;font:700 16px {FONT};white-space:nowrap}}
{p} .dv-bubble{{position:relative;display:block;width:600px;min-height:96px;padding:22px 28px;box-sizing:border-box;border:1px solid;border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW}}}{p} .dv-bubble:after{{content:"";position:absolute;left:42px;bottom:-16px;border:9px solid transparent;border-top-color:{P['surface']};transform:rotate(18deg)}}
{p} .dv-bubble-b,{p} .dv-bubble-n{{position:absolute;inset:20px 28px;display:flex;flex-direction:column;justify-content:center;gap:9px;font:600 24px/1.25 {FONT};color:{P['text']}}}{p} .dv-bubble-b{{filter:blur(9px);opacity:.85}}{p} .dv-bubble-n{{opacity:0}}
{p} .dv-wheels{{display:flex;gap:22px;align-items:center;justify-content:center}}{p} .dv-wheel{{position:relative;width:132px;height:154px;display:block}}{p} .dv-wheel>i{{position:absolute;left:7px;top:7px;width:116px;height:116px;border-radius:999px;background:conic-gradient({dv['video']},{dv['tc']},{dv['ok']},{dv['video2']},{dv['video']});box-shadow:inset 0 0 0 26px {dv['panel']}}}
{p} .dv-wheel>b{{position:absolute;left:61px;top:23px;width:10px;height:45px;border-radius:5px;background:{dv['text']};transform-origin:50% 43px}}{p} .dv-wheel>em{{position:absolute;bottom:0;left:0;right:0;text-align:center;font:500 13px {MONO};color:{dv['text2']}}}
{p} .dv-scope{{position:relative;display:block;background:{dv['bg']};border:1px solid {dv['line']};overflow:hidden}}{p} .dv-scope i{{position:absolute;bottom:8px;width:4px;background:{dv['ok']};transform-origin:50% 100%}}
{p} .dv-nodes{{position:relative;display:block;background:{dv['bg']};border:1px solid {dv['line']}}}{p} .dv-nodes svg{{position:absolute;inset:0;width:100%;height:100%;fill:none;stroke:{dv['text2']};stroke-width:3}}{p} .dv-nodes>i{{position:absolute;width:60px;height:40px;border:2px solid {dv['video2']};border-radius:5px;background:{dv['panel']}}}{p} .dv-nodes>i:nth-of-type(1){{left:15px;top:50px}}{p} .dv-nodes>i:nth-of-type(2){{left:110px;top:20px}}{p} .dv-nodes>i:nth-of-type(3){{right:15px;top:55px}}
{p} .cx-person img{{image-rendering:pixelated}}
"""


def _wrap(cid: str, lienzo: bool, fondo: str, inner: str) -> tuple[str, str]:
    P = _validate_fondo(fondo)
    glow = f'<span class="dv-dark-glow" id="{cid}-dark-glow"></span>' if fondo == "oscuro" else ""
    base_css, base_html = _wrap_base(
        cid, lienzo, fondo, f'<div class="dv-stage" id="{cid}-stage">{glow}{inner}</div>'
    )
    return base_css + _css(cid, P), base_html


def _logo_on(cid: str, target: str, slug: str, px: int, at: float) -> tuple:
    return ("html-on", f"#{target}", at, .01,
            _logo(f"{cid}-{slug}-{target}", slug, px))


def _cursor(anims: list, iid: str, x: int, duration: float = 3.0,
            start: float = 0.0) -> None:
    anims.append(("cursor-to", f"#{iid}-ph-move", start, duration, x, 0))


def _meters(anims: list, iid: str, start: float = 0.0) -> None:
    for n, scale in enumerate((.82, .58)):
        anims.append(("rise-bar", f"#{iid}-vu{n}", start + n * .08, .34))
        anims.append(("scale-y-to", f"#{iid}-vu{n}", start + .52 + n * .08, .28, scale))


@_encender
def dv_gancho(cid: str, variant: str, at: list, lienzo: bool = False,
              fondo: str = "oscuro") -> tuple[str, str, list]:
    variants = {"abre": 2, "mcp": 3}
    if variant not in variants:
        raise ValueError(f"dv_gancho: variante {variant!r} no existe")
    _need_at("dv_gancho", at, variants[variant])
    P = _validate_fondo(fondo)
    anims: list[tuple] = []
    if variant == "abre":
        win = _davinci(cid, 940, 700, visor="imagenes-9/toma-2.jpg",
                       nombre=True, medidores=True)
        app = _mosaico(f"{cid}-dv", "davinciresolve", P, 110,
                       nombre="DaVinci Resolve", logo=False)
        inner = f'{win}<span class="dv-hook-app" id="{cid}-hook-app">{app}</span>'
        css, html = _wrap(cid, lienzo, fondo, inner)
        p = f'.viz[data-viz-id="{cid}"]'
        css += f"""
{p} .dv-hook-app{{position:absolute;right:8px;top:22px}}
"""
        _cursor(anims, f"{cid}-tl", 760, 3.4)
        _meters(anims, f"{cid}-tl")
        anims += [("type-word", f"#{cid}-title-name", at[0], .36, "DaVinci Resolve"),
                  ("drop-in", f"#{cid}-hook-app", at[1], .26),
                  _logo_on(cid, f"{cid}-dv-logo", "davinciresolve", 64, at[1]),
                  ("type-word", f"#{cid}-dv-name", at[1], .36, "DaVinci Resolve")]
        return css, html, anims

    win = _davinci(cid, 980, 1040, visor="imagenes-9/toma-2.jpg",
                   timeline_h=430)
    socket = _zocalo(f"{cid}-socket", P)
    plug = _conector(f"{cid}-plug", P, 260, neon=True)
    check = _check(70)
    inner = (f'<span class="dv-hook-window">{win}</span>'
             f'<span class="dv-hook-socket" id="{cid}-socket-wrap">{socket}</span>'
             f'<span class="dv-hook-plug" id="{cid}-plug-travel">{plug}</span>'
             f'<span class="dv-verified" id="{cid}-verified" '
             f'style="background:{TK.BRANDS["davinci"]["ok"]}">{check}</span>')
    css, html = _wrap(cid, True, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-hook-window{{position:absolute;left:0;top:70px}}{p} .dv-hook-socket{{position:absolute;left:748px;top:520px}}
{p} .dv-hook-socket .dv-socket{{width:220px;height:160px;border-width:5px}}{p} .dv-hook-socket .dv-socket>i{{right:24px;width:30px;height:11px}}{p} .dv-hook-socket .dv-socket>i:first-child{{top:42px}}{p} .dv-hook-socket .dv-socket>i:nth-child(2){{top:96px}}{p} .dv-hook-socket .dv-socket>b{{left:22px;top:67px;width:24px;height:24px}}
{p} .dv-hook-plug{{position:absolute;right:-24px;top:476px}}{p} .dv-verified{{position:absolute;right:20px;top:334px;width:140px;height:140px;border-radius:999px;display:flex;align-items:center;justify-content:center;color:{P['bg']};box-shadow:{TK.GLOW}}}{p} .dv-verified svg{{stroke-width:3}}
"""
    _cursor(anims, f"{cid}-tl", 590, 3.3)
    anims += [("glide-x", f"#{cid}-socket-wrap", at[0], .30),
              ("draw", f"#{cid}-plug-outline", at[1], .34),
              ("cursor-to", f"#{cid}-plug-travel", at[1], .48, -125, 0),
              _logo_on(cid, f"{cid}-plug-logo", "modelcontextprotocol", 68, at[1]),
              ("fade-to", f"#{cid}-socket-luz", at[1] + .38, .14, 1),
              ("stamp", f"#{cid}-verified", at[2], .24)]
    return css, html, anims


@_encender
def dv_precio(cid: str, at: list, lienzo: bool = False,
              fondo: str = "claro") -> tuple[str, str, list]:
    _need_at("dv_precio", at, 2)
    P = _validate_fondo(fondo)
    win = _davinci(cid, 620, 420, visor="imagenes-9/toma-2.jpg")
    app = _mosaico(f"{cid}-dv", "davinciresolve", P, 180,
                   nombre="DaVinci Resolve")
    tag = (f'<span class="dv-price" id="{cid}-price" style="background:{P["surface"]};'
           f'border-color:{P["line"]}"><i></i><svg viewBox="0 0 250 100">'
           f'<path id="{cid}-cord" d="M42 0 C55 34 86 18 105 42"/></svg>'
           f'<b>US$ <span id="{cid}-price-n">295</span></b>'
           f'<em id="{cid}-price-glow"></em></span>')
    inner = (f'<span class="dv-price-window" id="{cid}-win-wrap">{win}</span>'
             f'<span class="dv-price-app" id="{cid}-app">{app}</span>{tag}')
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-price-window{{position:absolute;top:40px}}{p} .dv-price-app{{position:absolute;top:120px;opacity:0}}{p} .dv-price-app .dv-app-name:after{{content:"DaVinci Resolve"}}
{p} .dv-price{{position:absolute;top:330px;width:330px;height:190px;border:1px solid;border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};transform-origin:40px 0}}
{p} .dv-price>i{{position:absolute;left:28px;top:24px;width:20px;height:20px;border-radius:999px;background:{P['bg']};border:1px solid {P['line']}}}{p} .dv-price svg{{position:absolute;left:20px;top:-90px;width:250px;height:100px;fill:none;stroke:{P['text']};stroke-width:4}}
{p} .dv-price b{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font:900 72px {FONT}}}
{p} .dv-price em{{position:absolute;left:185px;top:70px;width:74px;height:50px;opacity:0;box-shadow:{TK.GLOW}}}
"""
    anims = [("cursor-to", f"#{cid}-win-wrap", at[0], .42, 0, 65),
             ("cam-push", f"#{cid}-win-wrap", at[0], .42, .35, 65),
             ("fade-to", f"#{cid}-win-wrap", at[0] + .32, .12, 0),
             ("fade-to", f"#{cid}-app", at[0] + .32, .12, 1),
             ("drop-in", f"#{cid}-price", at[1], .26),
             ("rot-to", f"#{cid}-price", at[1], .28, 0),
             ("count-roll", f"#{cid}-price-n", at[1], .70, 295, 0, ""),
             ("color-to", f"#{cid}-price-n", at[1] + .62, .12, P["accent_hi"]),
             ("fade-to", f"#{cid}-price-glow", at[1] + .62, .12, 1)]
    _cursor(anims, f"{cid}-tl", 430, 2.6)
    return css, html, anims


@_encender
def dv_balanza(cid: str, at: list, lienzo: bool = True,
               fondo: str = "claro") -> tuple[str, str, list]:
    _need_at("dv_balanza", at, 4)
    P = _validate_fondo(fondo)
    left = _mosaico(f"{cid}-left-app", "davinciresolve", P, 200)
    right = _mosaico(f"{cid}-right-app", "adobepremierepro", P, 200, logo=False)
    inner = (f'<div class="dv-scale"><span class="dv-scale-post"></span>'
             f'<span class="dv-scale-beam" id="{cid}-beam">'
             f'<span class="dv-pan dv-pan-left" id="{cid}-pan-left">'
             f'<i class="dv-pan-string dv-pan-string-left"></i>'
             f'<i class="dv-pan-string dv-pan-string-right"></i>{left}'
             f'<i class="dv-pan-dish"></i>'
             f'<b class="dv-pan-glow" id="{cid}-pan-left-glow"></b></span>'
             f'<span class="dv-pan dv-pan-right" id="{cid}-pan-right">'
             f'<i class="dv-pan-string dv-pan-string-left"></i>'
             f'<i class="dv-pan-string dv-pan-string-right"></i>{right}'
             f'<i class="dv-pan-dish"></i>'
             f'<b class="dv-pan-glow" id="{cid}-pan-right-glow"></b></span>'
             f'</span></div>')
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-scale{{position:relative;width:980px;height:1000px}}{p} .dv-scale-post{{position:absolute;left:478px;top:250px;width:24px;height:650px;background:{P['text']};border-radius:12px}}{p} .dv-scale-post:after{{content:"";position:absolute;left:-128px;bottom:0;width:280px;height:34px;border-radius:17px;background:{P['text']}}}
{p} .dv-scale-beam{{position:absolute;left:150px;top:230px;width:680px;height:22px;border-radius:11px;background:{P['text']};transform-origin:50% 50%}}
{p} .dv-pan{{position:absolute;top:11px;width:260px;height:470px;display:flex;align-items:flex-end;justify-content:center;transform-origin:50% 0}}{p} .dv-pan-left{{left:-130px}}{p} .dv-pan-right{{right:-130px}}{p} .dv-pan-string{{position:absolute;top:0;width:4px;height:310px;background:{P['text2']};transform-origin:50% 0}}{p} .dv-pan-string-left{{left:130px;transform:rotate(20deg)}}{p} .dv-pan-string-right{{right:130px;transform:rotate(-20deg)}}
{p} .dv-pan .dv-app-wrap{{position:absolute;left:30px;bottom:42px;z-index:2}}{p} .dv-pan-dish{{position:absolute;left:20px;bottom:0;width:220px;height:54px;box-sizing:border-box;border-bottom:6px solid {P['line']};border-left:2px solid {P['line']};border-right:2px solid {P['line']};border-radius:0px 0px 110px 110px;background:{P['surface2']}}}
{p} .dv-pan-glow{{position:absolute;left:20px;right:20px;bottom:-8px;height:24px;opacity:0;box-shadow:{TK.GLOW}}}
"""
    anims = [("drop-in", f"#{cid}-left-app-wrap", at[0], .28),
             ("rot-to", f"#{cid}-beam", at[0], .32, -14),
             ("rot-to", f"#{cid}-pan-left", at[0], .32, 14),
             ("rot-to", f"#{cid}-pan-right", at[0], .32, 14),
             ("rot-to", f"#{cid}-beam", at[1], .42, -6),
             ("rot-to", f"#{cid}-pan-left", at[1], .42, 6),
             ("rot-to", f"#{cid}-pan-right", at[1], .42, 6),
             ("drop-in", f"#{cid}-right-app-wrap", at[2], .28),
             _logo_on(cid, f"{cid}-right-app-logo", "adobepremierepro", 82, at[2]),
             ("rot-to", f"#{cid}-beam", at[3], .12, 0),
             ("rot-to", f"#{cid}-pan-left", at[3], .12, 0),
             ("rot-to", f"#{cid}-pan-right", at[3], .12, 0),
             ("fade-to", f"#{cid}-pan-left-glow", at[3], .14, 1),
             ("fade-to", f"#{cid}-pan-right-glow", at[3], .14, 1)]
    return css, html, anims


@_encender
def dv_linea(cid: str, variant: str, at: list, lienzo: bool = False,
             fondo: str = "claro") -> tuple[str, str, list]:
    variants = {"subtitulos": 2, "tijeras": 3, "produccion": 3}
    if variant not in variants:
        raise ValueError(f"dv_linea: variante {variant!r} no existe")
    _need_at("dv_linea", at, variants[variant])
    P = _validate_fondo(fondo)
    dv = TK.BRANDS["davinci"]
    anims: list[tuple] = []
    if variant == "subtitulos":
        tl = _timeline(f"{cid}-tl", 960, 560, _tracks_basic())
        words = "".join(f'<i id="{cid}-word{i}"></i>' for i in range(6))
        st = (f'<span class="dv-sub-track" id="{cid}-st" '
              f'style="background:{mix(dv["tc"], dv["panel"], .5)}">{words}</span>')
        css, html = _wrap(cid, lienzo, fondo, f'{tl}{st}')
        p = f'.viz[data-viz-id="{cid}"]'
        css += f"""
{p} .dv-sub-track{{position:absolute;left:120px;right:55px;top:170px;height:54px;border-radius:3px;display:flex;align-items:center;gap:12px;padding:0 16px;box-sizing:border-box}}
{p} .dv-sub-track i{{height:12px;flex:1;border-radius:4px;background:{dv['text']};opacity:0}}
"""
        _cursor(anims, f"{cid}-tl", 780, 3.2)
        for pi in (0, 2, 3):
            anims.append(("fade-to", f"#{cid}-tl-track{pi}", at[0] + pi * .06, .08, .16))
        anims += [("scale-y-to", f"#{cid}-tl-track1", at[0], .18, .55),
                  ("drop-in", f"#{cid}-st", at[0], .22)]
        anims += [("fade-to", f"#{cid}-word{i}", at[1] + i * .1, .12, 1) for i in range(6)]
        return css, html, anims

    if variant == "tijeras":
        tracks = [[(20, 850, "video", "imagenes-9/toma-2.jpg", "V1")]]
        tl = _timeline(f"{cid}-tl", 960, 260, tracks)
        scissors = _svg('<circle cx="7" cy="7" r="4"/><circle cx="7" cy="17" r="4"/><path d="m10 9 11 7M10 15 21 8"/>', 220)
        cuts = "".join(f'<i id="{cid}-cut{i}"></i>' for i in range(4))
        inner = (f'{tl}<span class="dv-scissors" id="{cid}-scissors">{scissors}</span>'
                 f'<span class="dv-cut-lines">{cuts}</span><span class="dv-cut-count">'
                 f'<em>Cortes</em><b id="{cid}-cuts-n">0</b></span>')
        css, html = _wrap(cid, True, fondo, inner)
        p = f'.viz[data-viz-id="{cid}"]'
        css += f"""
{p} .dv-timeline{{position:absolute;top:650px}}{p} .dv-scissors{{position:absolute;left:60px;top:390px;color:{P['text']}}}{p} .dv-cut-count{{position:absolute;right:30px;top:160px;display:flex;flex-direction:column;align-items:center}}{p} .dv-cut-count em{{font:700 28px {MONO}}}{p} .dv-cut-count b{{font:900 132px {FONT}}}
{p} .dv-cut-lines{{position:absolute;left:76px;top:680px;width:850px;height:100px}}{p} .dv-cut-lines i{{position:absolute;top:0;width:3px;height:100%;background:{P['text']};opacity:0}}{p} .dv-cut-lines i:nth-child(1){{left:170px}}{p} .dv-cut-lines i:nth-child(2){{left:340px}}{p} .dv-cut-lines i:nth-child(3){{left:510px}}{p} .dv-cut-lines i:nth-child(4){{left:680px}}
"""
        anims += [("glide-x", f"#{cid}-scissors", at[0], .24),
                  ("fade-to", f"#{cid}-cut0", at[0], .08, 1),
                  ("count-roll", f"#{cid}-cuts-n", at[0], .18, 0, 1, "")]
        for i in range(1, 4):
            tt = at[1] + (i - 1) * .18
            anims += [("cursor-to", f"#{cid}-scissors", tt, .16, i * 170, 0),
                      ("fade-to", f"#{cid}-cut{i}", tt, .08, 1),
                      ("count-roll", f"#{cid}-cuts-n", tt, .14, i, i + 1, "")]
        anims += [("cursor-to", f"#{cid}-scissors", at[2], .30, 680, 0),
                  ("fade-to", f"#{cid}-tl-c0-0", at[2], .22, .22)]
        return css, html, anims

    v1 = [
        (20, 205, "video", "imagenes-9/toma-2.jpg", "V1"),
        (235, 205, "video", "imagenes-9/toma-12.jpg"),
        (450, 205, "video", "imagenes-9/toma-22.jpg"),
        (665, 205, "video", "imagenes-9/toma-38.jpg"),
    ]
    tracks = [
        v1,
        [(20, 250, "video2", None, "V2"), (430, 300, "video2", None)],
        [(20, 850, "audio", None, "A1")],
        [(20, 850, "audio", None, "A2")],
        [(20, 850, "music", None, "M1")],
    ]
    tl = _timeline(f"{cid}-tl", 960, 530, tracks, row_height=100)
    panels = (f'<span class="dv-prod-panels"><span id="{cid}-color-panel">{_wheels(f"{cid}-prod")}</span>'
              f'<span id="{cid}-scope-panel">{_scope(f"{cid}-prod-scope")}</span>'
              f'<span id="{cid}-nodes-panel">{_nodes(f"{cid}-prod-nodes")}</span></span>')
    stub = (f'<span class="dv-prod-stub" id="{cid}-prod-stub"><img '
            f'src="imagenes-9/toma-2.jpg" alt=""/></span>')
    css, html = _wrap(cid, lienzo, fondo, f'{panels}{tl}{stub}')
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-timeline{{position:absolute;bottom:0}}{p} .dv-prod-stub{{position:absolute;left:76px;bottom:390px;width:150px;height:92px;border-radius:3px;overflow:hidden;z-index:4;transform-origin:0 50%;background:{dv['video']}}}{p} .dv-prod-stub img{{width:850px;height:92px;object-fit:cover;object-position:left center;opacity:.85}}
{p} #{cid}-tl-track0,{p} #{cid}-tl-track1,{p} #{cid}-tl-track2,{p} #{cid}-tl-track3,{p} #{cid}-tl-track4{{opacity:0}}
{p} .dv-prod-panels{{position:absolute;left:20px;right:20px;top:0;height:190px;display:flex;gap:12px}}{p} .dv-prod-panels>span{{flex:1;background:{dv['panel']};border:1px solid {dv['line']};border-radius:{RADIUS['sm']}px;display:flex;align-items:center;justify-content:center;box-shadow:{TK.GLOW}}}{p} .dv-prod-panels .dv-wheel{{transform:scale(.48);margin:-32px}}{p} .dv-prod-panels .dv-scope,{p} .dv-prod-panels .dv-nodes{{width:250px;height:150px}}
"""
    anims += [("grow-x", f"#{cid}-prod-stub", at[0], .36, 850),
              ("fade-to", f"#{cid}-prod-stub", at[0] + .30, .12, 0),
              ("fade-to", f"#{cid}-tl-track0", at[0] + .30, .12, 1)]
    anims += [("rise-in", f"#{cid}-tl-track{i}", at[1] + (i - 1) * .08, .22)
              for i in range(1, 5)]
    for i, name in enumerate(("color-panel", "scope-panel", "nodes-panel")):
        anims.append(("chip-in", f"#{cid}-{name}", at[2] + i * .10, .22))
    _cursor(anims, f"{cid}-tl", 790, 2.8, at[2])
    return css, html, anims


@_encender
def dv_enchufe(cid: str, at: list, lienzo: bool = True,
               fondo: str = "claro") -> tuple[str, str, list]:
    _need_at("dv_enchufe", at, 3)
    P = _validate_fondo(fondo)
    win = _davinci(cid, 900, 520, visor="imagenes-9/toma-2.jpg",
                   timeline_h=190)
    plug = _conector(f"{cid}-plug", P, 126, logo=True)
    left = _mosaico(f"{cid}-claude", "claude", P, 200,
                    nombre="Claude Code", logo=False)
    right = _mosaico(f"{cid}-codex", "openai", P, 200,
                     nombre="Codex", logo=False)
    cables = (f'<svg class="dv-cables" viewBox="0 0 980 1180"><path id="{cid}-cable0" d="M930 260 C720 430 390 590 245 904"/>'
              f'<path id="{cid}-cable1" d="M930 260 C820 490 790 660 735 904"/>'
              f'<path class="dv-cable-light" id="{cid}-light0" d="M930 260 C720 430 390 590 245 904"/>'
              f'<path class="dv-cable-light" id="{cid}-light1" d="M930 260 C820 490 790 660 735 904"/></svg>')
    rings = '<i id="{cid}-ring0"></i><i id="{cid}-ring1"></i>'.format(cid=cid)
    inner = (f'<span class="dv-plug-window">{win}<span class="dv-fitted-plug">{plug}</span></span>'
             f'{cables}<span class="dv-end-app dv-end-left" id="{cid}-left">'
             f'<i class="dv-app-port"></i>{left}</span>'
             f'<span class="dv-end-app dv-end-right" id="{cid}-right">'
             f'<i class="dv-app-port"></i>{right}</span>{rings}')
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-plug-window{{position:absolute;left:40px;top:20px}}{p} .dv-fitted-plug{{position:absolute;right:-52px;top:170px;transform:scale(.78)}}
{p} .dv-cables{{position:absolute;inset:0;width:100%;height:100%;fill:none;stroke:{P['text']};stroke-width:10;stroke-linecap:round}}{p} .dv-cable-light{{stroke:{P['accent_hi']};stroke-width:4;stroke-dasharray:12 18;opacity:0}}
{p} .dv-end-app{{position:absolute;bottom:30px;opacity:.35}}{p} .dv-end-left{{left:145px}}{p} .dv-end-right{{right:145px}}{p} .dv-end-app .dv-app-name{{background:{P['surface']};font-size:18px;height:34px}}{p} .dv-app-port{{position:absolute;left:82px;top:-18px;width:36px;height:28px;border:4px solid {P['text']};border-radius:8px 8px 3px 3px;background:{P['surface2']};z-index:4}}
{p} #{cid}-ring0,{p} #{cid}-ring1{{position:absolute;bottom:262px;width:42px;height:42px;border:3px solid {P['accent_hi']};border-radius:999px;opacity:0}}{p} #{cid}-ring0{{left:224px}}{p} #{cid}-ring1{{right:224px}}
"""
    anims = [("draw", f"#{cid}-cable0", at[0], .50),
             ("draw", f"#{cid}-cable1", at[0], .50),
             ("click", f"#{cid}-left", at[1], .24, f"#{cid}-ring0"),
             ("fade-to", f"#{cid}-left", at[1], .18, 1),
             _logo_on(cid, f"{cid}-claude-logo", "claude", 92, at[1]),
             ("type-word", f"#{cid}-claude-name", at[1], .30, "Claude Code"),
             ("fade-to", f"#{cid}-light0", at[1], .18, 1),
             ("click", f"#{cid}-right", at[2], .24, f"#{cid}-ring1"),
             ("fade-to", f"#{cid}-right", at[2], .18, 1),
             _logo_on(cid, f"{cid}-codex-logo", "openai", 92, at[2]),
             ("type-word", f"#{cid}-codex-name", at[2], .24, "Codex"),
             ("fade-to", f"#{cid}-light1", at[2], .18, 1)]
    return css, html, anims


@_encender
def dv_pedido(cid: str, at: list, lienzo: bool = False,
              fondo: str = "claro") -> tuple[str, str, list]:
    _need_at("dv_pedido", at, 2)
    P = _validate_fondo(fondo)
    tl = _timeline(f"{cid}-tl", 960, 300, _tracks_basic())
    bubble = _burbuja(f"{cid}-order0", PEDIDOS[0], P)
    stack = "".join(
        f'<span class="dv-order-back" id="{cid}-order{i}">'
        f'{_burbuja(f"{cid}-order-b{i}", "", P, vacia=True)}</span>' for i in range(1, 5)
    )
    voice = (f'<span class="dv-voice">'
             f'<i id="{cid}-voice0"></i><i id="{cid}-voice1"></i>'
             f'<i id="{cid}-voice2"></i></span>')
    inner = f'{tl}<span class="dv-order-main" id="{cid}-order-main">{bubble}</span>{stack}{voice}'
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-timeline{{position:absolute;left:10px;bottom:0}}{p} .dv-order-main,{p} .dv-order-back{{position:absolute;left:80px;top:20px}}{p} .dv-order-main .dv-bubble{{width:820px;min-height:130px;background:{P['surface']};border-color:{P['line']};box-shadow:{TK.SHADOW}}}{p} .dv-order-back .dv-bubble{{width:820px;min-height:130px;background:{P['surface2']};box-shadow:{TK.SHADOW}}}{p} .dv-order-back{{opacity:0}}{''.join(f'{p} #{cid}-order{i}{{transform:translate({i*14}px,{i*12}px) scale({1-i*.025});z-index:{5-i}}}' for i in range(1,5))}{p} .dv-order-main{{z-index:6}}
{p} .dv-voice{{position:absolute;left:0;top:52px;width:160px;height:160px;z-index:8}}{p} .dv-voice i{{position:absolute;border:5px solid {P['accent_hi']};border-left-color:transparent;border-bottom-color:transparent;border-radius:999px;transform:rotate(45deg)}}{p} .dv-voice i:nth-child(1){{inset:58px}}{p} .dv-voice i:nth-child(2){{inset:38px}}{p} .dv-voice i:nth-child(3){{inset:18px}}
"""
    anims: list[tuple] = []
    for i in range(3):
        anims += [("scale-pop", f"#{cid}-voice{i}", at[0] + i * .09, .18),
                  ("fade-to", f"#{cid}-voice{i}", at[0] + .16 + i * .09, .10, 0)]
    anims += [("chip-in", f"#{cid}-order-main", at[0], .24)]
    anims += [("chip-in", f"#{cid}-order{i}", at[1] + (i - 1) * .10, .20)
              for i in range(1, 5)]
    _cursor(anims, f"{cid}-tl", 790, 3.0)
    return css, html, anims


@_encender
def dv_color(cid: str, at: list, lienzo: bool = True,
             fondo: str = "claro") -> tuple[str, str, list]:
    _need_at("dv_color", at, 2)
    P = _validate_fondo(fondo)
    dv = TK.BRANDS["davinci"]
    crab = _personaje(f"{cid}-crab", "cangrejo", "rueda", 240)
    overlay = (f'<span class="dv-grade-overlay" id="{cid}-grade">'
               f'<img src="imagenes-9/toma-12.jpg" alt=""/></span>'
               f'<span class="dv-grade-line" id="{cid}-grade-line"></span>'
               f'<span class="dv-color-tools"><span class="dv-color-wheels">'
               f'{_wheels(cid)}</span><span class="dv-color-scope">'
               f'{_scope(f"{cid}-scope")}</span></span>')
    win = _davinci(cid, 980, 1120, visor="imagenes-9/toma-12.jpg",
                   pagina="color", body_extra=overlay, timeline=False,
                   viewer_h=790)
    inner = f'<span class="dv-color-window">{win}</span>{crab}'
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-color-window{{position:absolute;left:0;top:30px}}{p} .dv-color-window .dv-viewer{{height:790px}}{p} .dv-color-window .dv-viewer>img{{width:422px;height:750px;aspect-ratio:auto;object-fit:cover;filter:grayscale(1) contrast(.7) brightness(1.05)}}
{p} .dv-grade-overlay{{position:absolute;left:279px;top:26px;width:0;height:750px;overflow:hidden}}{p} .dv-grade-overlay img{{width:422px;height:750px;object-fit:cover;filter:saturate(1.25) contrast(1.12)}}
{p} .dv-grade-line{{position:absolute;left:279px;top:26px;width:4px;height:750px;background:{P['text']};box-shadow:{TK.GLOW}}}
{p} .dv-color-tools{{position:absolute;left:12px;right:12px;bottom:0;height:220px;box-sizing:border-box;padding:14px 18px;background:{dv['panel']};border:1px solid {dv['line']};display:flex;align-items:center;justify-content:space-between;gap:18px}}
{p} .dv-color-wheels{{display:flex;align-items:center}}{p} .dv-color-tools .dv-wheels{{gap:12px}}{p} .dv-color-tools .dv-wheel{{width:170px;height:190px}}{p} .dv-color-tools .dv-wheel>i{{left:8px;top:8px;width:154px;height:154px;box-shadow:inset 0 0 0 34px {dv['panel']}}}{p} .dv-color-tools .dv-wheel>b{{left:80px;top:30px;height:55px;transform-origin:50% 52px}}{p} .dv-color-tools .dv-wheel>em{{font-size:18px;color:{dv['text']}}}
{p} .dv-color-tools .dv-scope{{width:330px;height:180px}}{p} #{cid}-crab{{right:0;bottom:0;z-index:8}}
"""
    anims: list[tuple] = []
    for i, deg in enumerate((140, -90, 60)):
        anims.append(("rot-to", f"#{cid}-dot{i}", at[0], .60, deg))
    anims.append(("punch", f"#{cid}-crab", at[0], .20))
    anims += [("grow-x", f"#{cid}-grade", at[1], .70, 422),
              ("cursor-to", f"#{cid}-grade-line", at[1], .70, 422, 0)]
    for i in range(18):
        anims.append(("rise-bar", f"#{cid}-scope-bar{i}", at[1] + i * .025, .26))
    return css, html, anims


@_encender
def dv_graficos(cid: str, at: list, lienzo: bool = False,
                fondo: str = "claro") -> tuple[str, str, list]:
    _need_at("dv_graficos", at, 3)
    P = _validate_fondo(fondo)
    dv = TK.BRANDS["davinci"]
    tracks = [[(20, 820, "video", "imagenes-9/toma-22.jpg", "V1")],
              [(20, 0, "video2", None, "V2")],
              [(20, 820, "audio", None, "A1")]]
    win = _davinci(cid, 960, 720, visor="imagenes-9/toma-22.jpg", pistas=tracks)
    bubble = _burbuja(f"{cid}-order", PEDIDOS[1], P)
    shape = (f'<span class="dv-lower" id="{cid}-lower"><i id="{cid}-lower-box"></i>'
             f'<b id="{cid}-lower-dot"></b><em id="{cid}-lower-bar"></em></span>')
    keys = "".join(f'<i id="{cid}-key{i}"></i>' for i in range(4))
    curve = (f'<svg class="dv-key-curve" viewBox="0 0 360 90"><path id="{cid}-curve" '
             f'd="M20 70 C90 12 150 82 220 32 S310 18 340 50"/></svg>')
    inner = (f'{win}<span class="dv-graphics-order">{bubble}</span>{shape}'
             f'<span class="dv-keys">{keys}{curve}</span>')
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-graphics-order{{position:absolute;left:0;top:0;transform:scale(.58);transform-origin:0 0}}{p} .dv-lower{{position:absolute;left:310px;top:150px;width:320px;height:110px}}
{p} .dv-lower i{{position:absolute;left:0;bottom:0;width:250px;height:65px;border-radius:{RADIUS['sm']}px;background:{P['accent']}}}{p} .dv-lower b{{position:absolute;left:235px;bottom:0;width:80px;height:80px;border-radius:999px;background:{P['surface']}}}{p} .dv-lower em{{position:absolute;left:24px;bottom:24px;width:150px;height:12px;border-radius:6px;background:{P['on_accent']}}}
{p} .dv-keys{{position:absolute;left:330px;bottom:48px;width:360px;height:90px}}{p} .dv-keys>i{{position:absolute;bottom:12px;width:18px;height:18px;background:{dv['tc']};transform:rotate(45deg);opacity:0}}{''.join(f'{p} .dv-keys>i:nth-child({i+1}){{left:{i*100+14}px}}' for i in range(4))}
{p} .dv-key-curve{{position:absolute;inset:0;width:100%;height:100%;fill:none;stroke:{dv['tc']};stroke-width:3}}
"""
    anims = [("grow-x", f"#{cid}-tl-c1-0", at[0], .34, 820)]
    for i, part in enumerate(("lower-box", "lower-dot", "lower-bar")):
        anims.append(("chip-in", f"#{cid}-{part}", at[1] + i * .10, .22))
    anims.append(("fade-to", f"#{cid}-tl-c1-0", at[1], .12, 1))
    for i in range(4):
        anims.append(("drop-in", f"#{cid}-key{i}", at[2] + i * .12, .18))
    anims += [("draw", f"#{cid}-curve", at[2], .52),
              ("cursor-to", f"#{cid}-lower", at[2], .60, 120, 0),
              ("cursor-to", f"#{cid}-lower", at[2] + .60, .60, 0, 0)]
    _cursor(anims, f"{cid}-tl", 760, 3.0)
    return css, html, anims


@_encender
def dv_multicam(cid: str, at: list, lienzo: bool = True,
                fondo: str = "claro") -> tuple[str, str, list]:
    _need_at("dv_multicam", at, 2)
    P = _validate_fondo(fondo)
    dv = TK.BRANDS["davinci"]
    imgs = ("toma-2.jpg", "toma-12.jpg", "toma-22.jpg", "toma-38.jpg")
    v1 = [(20 + i * 205, 195, "video", f"imagenes-9/{name}", "V1")
          if i == 0 else (20 + i * 205, 195, "video", f"imagenes-9/{name}")
          for i, name in enumerate(imgs)]
    tracks = [v1, [(20, 820, "audio", None, "A1")]]
    win = _davinci(cid, 940, 1030, visor="imagenes-9/toma-2.jpg", pistas=tracks,
                   timeline_h=230, viewer_h=500, track_h=100)
    bubble = _burbuja(f"{cid}-order", PEDIDOS[2], P)
    grid = "".join(
        f'<span class="dv-angle" id="{cid}-angle{i}"><img src="imagenes-9/{name}" alt=""/>'
        f'<b>{i + 1}</b></span>' for i, name in enumerate(imgs)
    )
    cuts = "".join(f'<i id="{cid}-cut{i}"></i>' for i in range(4))
    frame = f'<span class="dv-angle-frame" id="{cid}-angle-frame"></span>'
    inner = (f'<span class="dv-multi-window">{win}<span class="dv-angle-grid" '
             f'id="{cid}-grid">{grid}{frame}</span><span class="dv-multi-cuts">{cuts}</span></span>'
             f'<span class="dv-multi-order">{bubble}</span>')
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-multi-window{{position:absolute;top:0}}{p} .dv-angle-grid{{position:absolute;left:214px;top:42px;width:490px;height:430px;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:4px;opacity:0;background:{dv['bg']}}}{p} .dv-angle{{position:relative;overflow:hidden}}{p} .dv-angle img{{width:100%;height:100%;object-fit:cover}}{p} .dv-angle:nth-child(2) img{{transform:scale(1.22)}}{p} .dv-angle:nth-child(3) img{{object-position:30% 50%}}{p} .dv-angle:nth-child(4) img{{object-position:70% 50%}}
{p} .dv-angle b{{position:absolute;left:8px;top:6px;font:700 18px {MONO};color:{dv['text']};text-shadow:{TK.SHADOW}}}{p} .dv-angle-frame{{position:absolute;left:0;top:0;width:239px;height:208px;border:5px solid {dv['playhead']};box-sizing:border-box}}
{p} .dv-multi-cuts{{position:absolute;left:68px;top:578px;width:836px;height:100px}}{p} .dv-multi-cuts i{{position:absolute;top:0;width:3px;height:100%;background:{P['text']};opacity:0}}{''.join(f'{p} .dv-multi-cuts i:nth-child({i+1}){{left:{205+i*205}px}}' for i in range(4))}
{p} .dv-multi-order{{position:absolute;left:0;top:0;transform:scale(.58);transform-origin:0 0}}
"""
    anims = [("fade-to", f"#{cid}-grid", at[0], .18, 1)]
    positions = ((0, 0), (0, 212), (245, 0), (245, 212))
    order = (0, 2, 1, 3)
    for n, angle in enumerate(order):
        x, y = positions[angle]
        tt = at[1] + n * .22
        anims += [("cursor-to", f"#{cid}-angle-frame", tt, .16, x, y),
                  ("fade-to", f"#{cid}-cut{n}", tt, .08, 1)]
    _cursor(anims, f"{cid}-tl", 760, 3.0)
    return css, html, anims


@_encender
def dv_sonido(cid: str, at: list, lienzo: bool = False,
              fondo: str = "claro") -> tuple[str, str, list]:
    _need_at("dv_sonido", at, 3)
    P = _validate_fondo(fondo)
    dv = TK.BRANDS["davinci"]
    imgs = ("toma-2.jpg", "toma-12.jpg", "toma-22.jpg", "toma-38.jpg")
    vclips = [(20 + i * 205, 195, "video", f"imagenes-9/{name}", "V1")
              if i == 0 else (20 + i * 205, 195, "video", f"imagenes-9/{name}")
              for i, name in enumerate(imgs)]
    tracks = [vclips, [(20, 820, "audio", None, "A1")],
              [(20, 0, "audio", None, "A3")]]
    tl = _timeline(f"{cid}-tl", 960, 560, tracks, medidores=True)
    bubble = _burbuja(f"{cid}-order", PEDIDOS[3], P)
    effects = "".join(
        f'<span class="dv-sfx" id="{cid}-sfx{i}" style="left:{245+i*205}px;'
        f'background:{dv["audio"]}">{_wave(f"{cid}-sfx{i}", dv["text"], 8, True)}</span>'
        for i in range(3)
    )
    inner = f'{tl}<span class="dv-sound-order">{bubble}</span><span class="dv-sfx-row">{effects}</span>'
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-timeline{{position:absolute;bottom:0}}{p} .dv-sound-order{{position:absolute;left:0;top:0;transform:scale(.58);transform-origin:0 0}}{p} .dv-sfx-row{{position:absolute;left:56px;bottom:15px;width:880px;height:150px}}{p} .dv-sfx{{position:absolute;bottom:8px;width:90px;height:72px;border-radius:3px;overflow:hidden}}{p} .dv-sfx svg{{width:100%;height:100%;fill:currentColor;color:{dv['text']}}}
"""
    anims = [("grow-x", f"#{cid}-tl-c2-0", at[0], .34, 820)]
    for i in range(3):
        tt = at[1] + i * .16
        anims.append(("drop-in", f"#{cid}-sfx{i}", tt, .18))
    for i in range(3):
        for j in range(8):
            anims.append(("rise-bar", f"#{cid}-sfx{i}-w{j}", at[2] + i * .16 + j * .015, .16))
        if i == 0:
            _meters(anims, f"{cid}-tl", at[2])
        else:
            anims += [("scale-y-to", f"#{cid}-tl-vu0", at[2] + i * .16, .12,
                       (.55, .92)[i - 1]),
                      ("scale-y-to", f"#{cid}-tl-vu1", at[2] + i * .16, .12,
                       (.88, .62)[i - 1])]
    _cursor(anims, f"{cid}-tl", 780, 3.0)
    return css, html, anims


@_encender
def dv_musica(cid: str, at: list, lienzo: bool = True,
              fondo: str = "oscuro") -> tuple[str, str, list]:
    _need_at("dv_musica", at, 3)
    P = _validate_fondo(fondo)
    dv = TK.BRANDS["davinci"]
    tracks = [
        [(20 + i * 164, 154, "video", "imagenes-9/toma-2.jpg") for i in range(5)],
        [(20, 820, "music", None, "A2")],
    ]
    tl = _timeline(f"{cid}-tl", 960, 620, tracks)
    bubble = _burbuja(f"{cid}-order", PEDIDOS[4], P)
    cuts = "".join(f'<i id="{cid}-cut{i}" style="left:{145+i*160}px"></i>' for i in range(5))
    peaks = "".join(f'<i id="{cid}-peak{i}" style="left:{90+i*135}px;height:{38+(i%3)*24}px"></i>' for i in range(6))
    beats = "".join(f'<b id="{cid}-beat{i}" style="left:{130+i*160}px"></b>' for i in range(5))
    inner = (f'{tl}<span class="dv-music-order">{bubble}</span>'
             f'<span class="dv-music-cuts">{cuts}</span><span class="dv-music-wave" '
             f'id="{cid}-music-wave">{peaks}</span><span class="dv-beats">{beats}</span>'
             f'<span class="dv-music-glow" id="{cid}-music-glow"></span>')
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-timeline{{position:absolute;bottom:70px}}{p} .dv-music-order{{position:absolute;left:0;top:0;transform:scale(.58);transform-origin:0 0}}
{p} .dv-music-cuts{{position:absolute;left:56px;bottom:370px;width:850px;height:180px}}{p} .dv-music-cuts i{{position:absolute;top:0;width:2px;height:100%;background:{rgba(P['text'], .5)}}}
{p} .dv-music-wave{{position:absolute;left:78px;bottom:104px;width:800px;height:220px;transform-origin:0 50%}}{p} .dv-music-wave i{{position:absolute;bottom:12px;width:14px;border-radius:7px;background:{dv['text']}}}
{p} .dv-beats{{position:absolute;left:56px;bottom:320px;width:850px;height:45px}}{p} .dv-beats b{{position:absolute;width:18px;height:18px;background:{dv['tc']};transform:rotate(45deg);opacity:0}}
{p} .dv-music-glow{{position:absolute;left:90px;right:90px;bottom:90px;height:240px;opacity:0;box-shadow:{TK.GLOW}}}
"""
    anims = [("cam-push", f"#{cid}-music-wave", at[0], .28, 1.12, 0),
             ("cam-push", f"#{cid}-music-wave", at[0] + .28, .28, .96, 0)]
    anims += [("fade-to", f"#{cid}-beat{i}", at[1] + i * .10, .12, 1) for i in range(5)]
    anims += [("cursor-to", f"#{cid}-music-wave", at[2], .46, 38, 0),
              ("fade-to", f"#{cid}-music-glow", at[2], .16, 1),
              ("cam-push", f"#{cid}-tl", at[2], .14, 1.025, 0),
              ("cam-push", f"#{cid}-tl", at[2] + .14, .18, 1, 0)]
    _cursor(anims, f"{cid}-tl", 780, 3.0)
    return css, html, anims


@_encender
def dv_pozo(cid: str, at: list, lienzo: bool = True,
            fondo: str = "comic") -> tuple[str, str, list]:
    _need_at("dv_pozo", at, 4)
    P = _validate_fondo(fondo)
    tracks = [[
        (20, 250, "video", "imagenes-9/toma-2.jpg", "V1"),
        (280, 250, "video", "imagenes-9/toma-12.jpg", "V1"),
        (540, 250, "video", "imagenes-9/toma-38.jpg", "V1"),
    ], [(20, 770, "audio", None, "A1")]]
    tl = _timeline(f"{cid}-tl", 960, 520, tracks)
    hole = f'<span class="dv-hole" id="{cid}-hole"></span>'
    empty = f'<span class="dv-hole-frame" id="{cid}-hole-frame"></span>'
    inner = f'<span class="dv-pozo-layout">{tl}{hole}{empty}</span>'
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-pozo-layout{{position:relative;width:960px;height:520px}}{p} .dv-pozo-layout .dv-timeline{{position:absolute;inset:0}}{p} .dv-hole{{position:absolute;left:356px;top:114px;width:250px;height:160px;border-radius:{RADIUS['sm']}px;background:{TK.BRANDS['davinci']['bg']};opacity:0;box-shadow:inset 0 0 32px {rgba(P['text'], .28)}}}
{p} .dv-hole-frame{{position:absolute;left:376px;top:125px;width:210px;height:138px;border:4px dashed {P['text2']};border-radius:{RADIUS['sm']}px;opacity:0}}
"""
    anims = [("cursor-to", f"#{cid}-tl-c0-1", at[0], .40, 0, -500),
             ("rot-to", f"#{cid}-tl-c0-1", at[0], .40, 200),
             ("fade-to", f"#{cid}-hole", at[0] + .18, .12, 1),
             ("fade-to", f"#{cid}-hole-frame", at[1], .10, 1),
             ("fade-to", f"#{cid}-hole-frame", at[1] + .16, .10, .3),
             ("fade-to", f"#{cid}-hole-frame", at[1] + .32, .10, 1),
             ("cursor-to", f"#{cid}-tl-c0-0", at[2], .34, -60, 0),
             ("cursor-to", f"#{cid}-tl-c0-2", at[2], .34, 60, 0),
             ("cam-push", f"#{cid}-hole", at[2], .34, 1.35, 0),
             ("cursor-to", f"#{cid}-tl-ph-move", at[3], .48, 330, 0),
             ("jitter", f"#{cid}-tl-ph-jitter", at[3] + .48, .72)]
    return css, html, anims


@_encender
def dv_genera(cid: str, at: list, lienzo: bool = True,
              fondo: str = "oscuro") -> tuple[str, str, list]:
    _need_at("dv_genera", at, 2)
    P = _validate_fondo(fondo)
    frame = (f'<span class="dv-gen-frame" id="{cid}-frame">'
             f'<span class="dv-gen-glow" id="{cid}-glow"></span>'
             f'<img class="dv-gen-blur" id="{cid}-blur" src="imagenes-9/plano.jpg" alt=""/>'
             f'<img class="dv-gen-sharp" id="{cid}-sharp" src="imagenes-9/plano.jpg" alt=""/>'
             f'<svg class="dv-noise" id="{cid}-noise"><filter id="{cid}-noise-filter">'
             f'<feTurbulence baseFrequency=".8" numOctaves="2" seed="9"/></filter>'
             f'<rect width="100%" height="100%" filter="url(#{cid}-noise-filter)"/></svg></span>')
    strip = _timeline(f"{cid}-tl", 800, 150, [[(20, 260, "video", None, "V1"),
                                                (540, 220, "video", None, "V1")]])
    crab = _personaje(f"{cid}-crab", "cangrejo", ("asoma", "pinta"), 220)
    inner = (f'<span class="dv-gen-logo" id="{cid}-claude-logo"></span>{frame}'
             f'<span class="dv-gen-crab">{crab}</span>{strip}')
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-gen-frame{{position:absolute;top:15px;width:520px;height:924px;border:4px dashed {P['text2']};border-radius:{RADIUS['sm']}px;overflow:hidden;background:{TK.BRANDS['davinci']['bg']}}}
{p} .dv-gen-frame img,{p} .dv-noise{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0}}{p} .dv-gen-blur{{filter:blur(28px) brightness(.5);transform:scale(1.08)}}{p} .dv-gen-sharp{{filter:saturate(1.05)}}{p} .dv-noise{{opacity:0;mix-blend-mode:screen}}{p} .dv-noise rect{{fill:{P['text']}}}
{p} .dv-gen-glow{{position:absolute;inset:80px;background:{rgba(P['accent'], .30)};filter:blur(50px);opacity:0}}{p} .dv-gen-logo{{position:absolute;top:0;left:185px;width:64px;height:64px;display:flex;z-index:5}}
{p} .dv-gen-crab{{position:absolute;left:570px;top:730px;z-index:6}}{p} .dv-timeline{{position:absolute;bottom:0}}
"""
    anims = [_logo_on(cid, f"{cid}-claude-logo", "claude", 56, at[0]),
             ("rise-in", f"#{cid}-crab", at[0], .26)]
    _pose(anims, f"{cid}-crab", "asoma", "pinta", at[1])
    anims += [("cursor-to", f"#{cid}-crab", at[1], .36, -80, -80),
              ("fade-to", f"#{cid}-blur", at[1], .01, 1),
              ("fade-to", f"#{cid}-noise", at[1], .01, .60),
              ("fade-to", f"#{cid}-glow", at[1], .18, 1),
              ("fade-to", f"#{cid}-blur", at[1] + .08, 1.10, 0),
              ("fade-to", f"#{cid}-sharp", at[1] + .08, 1.10, 1),
              ("fade-to", f"#{cid}-noise", at[1] + .08, 1.10, 0)]
    return css, html, anims


@_encender
def dv_encastra(cid: str, at: list, lienzo: bool = False,
                fondo: str = "claro") -> tuple[str, str, list]:
    _need_at("dv_encastra", at, 3)
    P = _validate_fondo(fondo)
    # V1 como lo dejó dv_pozo: dos vecinos separados y el hueco entre ellos (340–620).
    # El plano es el clip c0-1 de la MISMA pista: baja desde arriba a su hueco, y los
    # vecinos se cierran contra él (±40 px) sin dejar junta.
    tracks = [[(20, 280, "video", "imagenes-9/toma-2.jpg", "V1"),
               (340, 280, "video", "imagenes-9/plano.jpg", "V1"),
               (660, 240, "video", "imagenes-9/toma-38.jpg", "V1")],
              [(20, 880, "audio", None, "A1")]]
    tl = _timeline(f"{cid}-tl", 960, 520, tracks, medidores=True)
    hole = (f'<span class="dv-insert-hole" id="{cid}-hole" '
            f'style="left:340px;width:280px"></span>')
    tl = tl.replace(f'<span class="dv-clip dv-video" id="{cid}-tl-c0-1"',
                    f'{hole}<span class="dv-clip dv-video" id="{cid}-tl-c0-1"', 1)
    css, html = _wrap(cid, lienzo, fondo, tl)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-insert-hole{{position:absolute;top:4px;bottom:4px;background:{TK.BRANDS['davinci']['bg']};border:3px dashed {P['text2']};border-radius:3px;box-sizing:border-box}}
{p} #{cid}-tl-c0-1{{opacity:0;z-index:4;box-shadow:{TK.SHADOW}}}
"""
    anims = [("jitter", f"#{cid}-tl-ph-jitter", 0, max(.2, at[1])),
             ("cursor-to", f"#{cid}-tl-c0-1", at[0], .01, 0, -330),
             ("fade-to", f"#{cid}-tl-c0-1", at[0] + .01, .12, 1),
             ("cursor-to", f"#{cid}-tl-c0-1", at[0] + .01, .38, 0, 0),
             ("cursor-to", f"#{cid}-tl-c0-0", at[1], .24, 40, 0),
             ("cursor-to", f"#{cid}-tl-c0-2", at[1], .24, -40, 0),
             ("fade-to", f"#{cid}-hole", at[1], .10, 0),
             ("cursor-to", f"#{cid}-tl-ph-move", at[2], .80, 820, 0)]
    _meters(anims, f"{cid}-tl", at[2])
    return css, html, anims


@_encender
def dv_higgsfield(cid: str, at: list, lienzo: bool = False,
                  fondo: str = "oscuro") -> tuple[str, str, list]:
    _need_at("dv_higgsfield", at, 4)
    P = _validate_fondo(fondo)
    win = _davinci(cid, 600, 520, visor="imagenes-9/toma-2.jpg")
    plug = _conector(f"{cid}-plug", P, 88, logo=True)
    app = _mosaico(f"{cid}-higgs", "higgsfield", P, 190,
                   nombre="Higgsfield", logo=False)
    socket = _zocalo(f"{cid}-socket", P)
    thumbs = "".join(
        f'<span class="dv-higgs-thumb" id="{cid}-thumb{i}"><img '
        f'src="imagenes-9/plano.jpg" alt=""/></span>' for i in range(4)
    )
    cable = (f'<svg class="dv-higgs-cable" viewBox="0 0 980 650"><path id="{cid}-cable-loose" '
             f'd="M405 280 C520 360 580 520 700 500"/><path id="{cid}-cable-tight" '
             f'd="M405 280 C530 330 650 360 765 420"/></svg>')
    inner = (f'<span class="dv-higgs-window">{win}<span class="dv-higgs-plug">{plug}</span></span>'
             f'{cable}<span class="dv-higgs-app" id="{cid}-higgs-group">{app}{socket}'
             f'<b id="{cid}-higgs-glow"></b></span>'
             f'<span class="dv-higgs-thumbs">{thumbs}</span><i id="{cid}-click-ring"></i>')
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-higgs-window{{position:absolute;left:0;top:100px}}{p} .dv-higgs-plug{{position:absolute;right:-34px;top:220px;transform:scale(.72)}}{p} .dv-higgs-app{{position:absolute;right:20px;top:240px;opacity:.35}}{p} .dv-higgs-app .dv-socket{{position:absolute;left:-80px;top:55px;transform:scale(.65)}}
{p} .dv-higgs-app>b{{position:absolute;inset:25px;opacity:0;box-shadow:{TK.GLOW}}}
{p} .dv-higgs-cable{{position:absolute;inset:0;width:100%;height:100%;fill:none;stroke:{P['text']};stroke-width:10;stroke-linecap:round}}{p} #{cid}-cable-tight{{opacity:0}}{p} .dv-higgs-thumbs{{position:absolute;right:210px;top:330px}}{p} .dv-higgs-thumb{{position:absolute;width:48px;height:85px;border-radius:3px;overflow:hidden;opacity:0}}{p} .dv-higgs-thumb img{{width:100%;height:100%;object-fit:cover}}
{p} #{cid}-click-ring{{position:absolute;right:148px;top:385px;width:38px;height:38px;border:3px solid {P['accent_hi']};border-radius:999px;opacity:0}}
"""
    anims = [("rot-to", f"#{cid}-cable-loose", 0, .40, 8),
             ("rot-to", f"#{cid}-cable-loose", .40, .40, -8),
             ("fade-to", f"#{cid}-cable-loose", at[0], .10, 0),
             ("draw", f"#{cid}-cable-tight", at[0], .42),
             ("fade-to", f"#{cid}-cable-tight", at[0], .01, 1),
             ("click", f"#{cid}-socket", at[0], .22, f"#{cid}-click-ring"),
             ("fade-to", f"#{cid}-higgs-group", at[1], .18, 1)]
    for i in range(4):
        tt = at[2] + i * .15
        anims += [("fade-to", f"#{cid}-thumb{i}", tt, .08, 1),
                  ("cursor-to", f"#{cid}-thumb{i}", tt, .32, -430 - i * 34, -100 + i * 24)]
    anims += [_logo_on(cid, f"{cid}-higgs-logo", "higgsfield", 104, at[3]),
              ("type-word", f"#{cid}-higgs-name", at[3], .30, "Higgsfield"),
              ("fade-to", f"#{cid}-higgs-glow", at[3], .16, 1),
              ("fade-to", f"#{cid}-socket-luz", at[3], .16, 1)]
    return css, html, anims


@_encender
def dv_editor(cid: str, at: list, lienzo: bool = True,
              fondo: str = "claro") -> tuple[str, str, list]:
    _need_at("dv_editor", at, 3)
    P = _validate_fondo(fondo)
    dv = TK.BRANDS["davinci"]
    media = "".join(
        f'<img src="imagenes-9/toma-{n}.jpg" alt=""/>' for n in (2, 12, 22, 38)
    )
    tracks = [
        [(20, 210, "video2", "imagenes-9/toma-22.jpg", "V2")],
        [(20, 150, "video", "imagenes-9/toma-2.jpg", "V1"),
         (180, 150, "video", "imagenes-9/toma-12.jpg", "V1"),
         (340, 150, "video", "imagenes-9/plano.jpg", "V1"),
         (500, 150, "video", "imagenes-9/toma-38.jpg", "V1")],
        [(20, 120, "audio", None, "A3"), (180, 120, "audio", None, "A3")],
        [(20, 700, "music", None, "A4")],
    ]
    extra = (f'<span class="dv-editor-viewer">'
             f'<img src="imagenes-9/toma-12.jpg" alt=""/></span>')
    win = _davinci(cid, 980, 1120, pistas=tracks, body_extra=extra,
                   medidores=True, timeline_h=430, track_h=97)
    crab = _personaje(f"{cid}-crab", "cangrejo", "arrastra", 240)
    shines = "".join(f'<i id="{cid}-shine{i}"></i>' for i in range(4))
    app = _mosaico(f"{cid}-dv", "davinciresolve", P, 90)
    inner = (f'<span class="dv-editor-wrap" id="{cid}-editor-wrap">'
             f'<span class="dv-media-bin">{media}</span>{win}'
             f'<span class="dv-editor-crab">{crab}</span><span class="dv-track-shines">{shines}</span>'
             f'<span class="dv-editor-app" id="{cid}-editor-app">{app}</span></span>')
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-editor-wrap{{position:absolute;width:980px;height:1120px}}{p} .dv-editor-wrap .dv-timeline{{position:absolute;left:12px;right:12px;bottom:0}}{p} .dv-editor-crab{{position:absolute;left:70px;bottom:80px;width:240px;height:240px;z-index:8}}{p} .dv-media-bin{{position:absolute;left:16px;top:44px;width:230px;height:180px;display:grid;grid-template-columns:1fr 1fr;gap:5px;z-index:4}}{p} .dv-media-bin img{{width:100%;height:86px;object-fit:cover}}
{p} .dv-editor-viewer{{position:absolute;left:300px;top:8px;width:340px;height:300px;background:{dv['panel']};display:flex;align-items:center;justify-content:center}}{p} .dv-editor-viewer img{{height:100%;aspect-ratio:9/16;object-fit:cover}}
{p} .dv-track-shines{{position:absolute;left:70px;right:40px;bottom:64px;height:330px}}{p} .dv-track-shines i{{display:block;height:68px;margin:5px 0;background:linear-gradient(90deg,transparent,{rgba(P['accent'], .25)},transparent);opacity:0}}
{p} .dv-editor-app{{position:absolute;right:20px;top:50px;box-shadow:{TK.GLOW}}}
"""
    anims = [("rise-in", f"#{cid}-crab", at[0], .22),
             ("cursor-to", f"#{cid}-crab", at[0], .72, 600, 0),
             ("cursor-to", f"#{cid}-tl-ph-move", at[0], .72, 650, 0)]
    anims += [("fade-to", f"#{cid}-shine{i}", at[0] + i * .08, .18, 1) for i in range(4)]
    anims += [("cam-push", f"#{cid}-editor-wrap", at[1], .50, 1, 0),
              ("stamp", f"#{cid}-editor-app", at[2], .20)]
    _meters(anims, f"{cid}-tl", at[0])
    return css, html, anims


@_encender
def dv_guia(cid: str, variant: str, at: list, lienzo: bool = False,
            fondo: str = "claro") -> tuple[str, str, list]:
    variants = {"despliega": 2, "pedidos": 3}
    if variant not in variants:
        raise ValueError(f"dv_guia: variante {variant!r} no existe")
    _need_at("dv_guia", at, variants[variant])
    P = _validate_fondo(fondo)
    plug = _conector(f"{cid}-plug", P, 74, logo=True)
    if variant == "despliega":
        tl = _timeline(f"{cid}-tl", 960, 240, _tracks_basic())
        rows = "".join(
            f'<span class="dv-guide-row" id="{cid}-row{i}"><b>{i + 1}</b><i></i>'
            f'<em id="{cid}-row{i}-glow"></em></span>'
            for i in range(5)
        )
        sheet = (f'<span class="dv-guide" id="{cid}-guide" style="background:{P["surface"]};'
                 f'border-color:{P["line"]}"><span class="dv-guide-head"></span>{rows}</span>')
        inner = f'{sheet}<span class="dv-guide-plug" id="{cid}-plug-wrap">{plug}</span>{tl}'
        css, html = _wrap(cid, lienzo, fondo, inner)
        p = f'.viz[data-viz-id="{cid}"]'
        css += f"""
{p} .dv-guide{{position:absolute;left:0;top:0;width:960px;height:480px;border:1px solid;border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};overflow:hidden}}{p} .dv-guide-head{{display:block;height:62px;border-bottom:1px solid {P['line']}}}
{p} .dv-guide-row{{height:80px;display:flex;align-items:center;gap:24px;padding:0 36px;box-sizing:border-box;border-bottom:1px solid {P['line']};transform-origin:50% 0}}{p} .dv-guide-row b{{font:800 26px {FONT};color:{P['accent_hi']}}}{p} .dv-guide-row i{{height:13px;flex:1;border-radius:7px;background:{rgba(P['text'], .35)};filter:blur(4px)}}
{p} .dv-guide-row em{{position:absolute;inset:10px;opacity:0;box-shadow:{TK.GLOW}}}
{p} .dv-guide-plug{{position:absolute;left:30px;top:-20px}}{p} .dv-timeline{{position:absolute;bottom:0}}
"""
        anims = [("rise-bar", f"#{cid}-row{i}", at[0] + i * .08, .24) for i in range(5)]
        anims += [("drop-in", f"#{cid}-plug-wrap", at[1], .24),
                  ("cam-push", f"#{cid}-row0", at[1] + .12, .18, 1.02, 0),
                  ("fade-to", f"#{cid}-row0-glow", at[1] + .12, .18, 1)]
        _cursor(anims, f"{cid}-tl", 790, 3.0)
        return css, html, anims

    header = (f'<span class="dv-guide-head-compact" style="background:{P["surface"]};'
              f'border-color:{P["line"]}">{plug}</span>')
    font_size = 30
    if any(text_px(pedido, font_size, 600) > 932 * 2 for pedido in PEDIDOS):
        font_size = 28
    if any(text_px(pedido, font_size, 600) > 932 * 2 for pedido in PEDIDOS):
        raise ValueError("un pedido no cabe en dos renglones a 28px")
    bubbles = "".join(
        f'<span class="dv-guide-bubble" id="{cid}-order{i}">'
        f'{_burbuja(f"{cid}-pedido{i}", pedido, P, legible=True)}</span>'
        for i, pedido in enumerate(PEDIDOS)
    )
    light = f'<span class="dv-guide-light" id="{cid}-light"></span>'
    frame = f'<span class="dv-guide-frame" id="{cid}-frame"></span>'
    inner = f'<span class="dv-guide-climax">{header}{bubbles}{light}{frame}</span>'
    css, html = _wrap(cid, lienzo, fondo, inner)
    p = f'.viz[data-viz-id="{cid}"]'
    css += f"""
{p} .dv-guide-climax{{position:relative;width:980px;height:760px}}{p} .dv-guide-head-compact{{position:absolute;left:0;top:0;width:980px;height:60px;border:1px solid;border-radius:{RADIUS['lg']}px;display:flex;align-items:center;padding-left:28px;box-sizing:border-box;box-shadow:{TK.SHADOW}}}
{p} .dv-guide-bubble{{position:absolute;left:0;width:980px;height:106px}}{''.join(f'{p} .dv-guide-bubble:nth-of-type({i+2}){{top:{68+i*114}px}}' for i in range(6))}
{p} .dv-guide-bubble .dv-bubble{{width:980px;height:106px;min-height:106px;padding:12px 24px}}{p} .dv-guide-bubble .dv-bubble-b{{inset:10px 24px;font-size:{font_size}px;line-height:1.18;filter:blur(9px);opacity:.85}}{p} .dv-guide-bubble .dv-bubble-n{{inset:10px 24px;font-size:{font_size}px;line-height:1.18;font-weight:600}}
{p} .dv-guide-light{{position:absolute;left:0;top:60px;width:980px;height:80px;background:linear-gradient(180deg,transparent,{rgba(P['accent'], .45)},transparent);opacity:.9}}{p} .dv-guide-frame{{position:absolute;inset:0;border:4px solid {P['accent_hi']};border-radius:{RADIUS['lg']}px;opacity:0;box-shadow:{TK.GLOW}}}
"""
    anims: list[tuple] = []
    for i, pedido in enumerate(PEDIDOS):
        enter = at[0] + i * .07
        anims += [("chip-in", f"#{cid}-order{i}", enter, .18)]
        focus = at[1] + .15 + i * .16
        anims += [("caret-off", f"#{cid}-pedido{i}-n", focus, .01, pedido),
                  ("fade-to", f"#{cid}-pedido{i}-b", focus, .12, 0),
                  ("fade-to", f"#{cid}-pedido{i}-n", focus, .12, 1)]
    anims += [("cursor-to", f"#{cid}-light", at[1], .60, 0, 570),
              ("fade-to", f"#{cid}-frame", at[2], .18, 1),
              ("cam-push", f"#{cid}-frame", at[2], .18, 1.02, 0)]
    return css, html, anims


def assets_de(fn_name: str, kw: dict) -> list[str]:
    """Rutas relativas a ``assets/`` que la llamada va a referenciar."""
    variant = kw.get("variant")
    variants = {
        "dv_gancho": {
            "abre": ("imagenes-9/toma-2.jpg",),
            "mcp": ("imagenes-9/toma-2.jpg",),
        },
        "dv_linea": {
            "subtitulos": ("imagenes-9/toma-2.jpg",),
            "tijeras": ("imagenes-9/toma-2.jpg",),
            "produccion": ("imagenes-9/toma-2.jpg", "imagenes-9/toma-12.jpg",
                            "imagenes-9/toma-22.jpg", "imagenes-9/toma-38.jpg"),
        },
        "dv_guia": {
            "despliega": ("imagenes-9/toma-2.jpg",),
            "pedidos": (),
        },
    }
    plain = {
        "dv_precio": ("imagenes-9/toma-2.jpg",),
        "dv_balanza": (),
        "dv_enchufe": ("imagenes-9/toma-2.jpg",),
        "dv_pedido": ("imagenes-9/toma-2.jpg",),
        "dv_color": ("imagenes-9/toma-12.jpg", "personajes-9/cangrejo-rueda.png"),
        "dv_graficos": ("imagenes-9/toma-22.jpg",),
        "dv_multicam": ("imagenes-9/toma-2.jpg", "imagenes-9/toma-12.jpg",
                         "imagenes-9/toma-22.jpg", "imagenes-9/toma-38.jpg"),
        "dv_sonido": ("imagenes-9/toma-2.jpg", "imagenes-9/toma-12.jpg",
                       "imagenes-9/toma-22.jpg", "imagenes-9/toma-38.jpg"),
        "dv_musica": ("imagenes-9/toma-2.jpg",),
        "dv_pozo": ("imagenes-9/toma-2.jpg", "imagenes-9/toma-12.jpg",
                     "imagenes-9/toma-38.jpg"),
        "dv_genera": ("imagenes-9/plano.jpg", "personajes-9/cangrejo-asoma.png",
                       "personajes-9/cangrejo-pinta.png"),
        "dv_encastra": ("imagenes-9/toma-2.jpg", "imagenes-9/plano.jpg",
                         "imagenes-9/toma-38.jpg"),
        "dv_higgsfield": ("imagenes-9/toma-2.jpg", "imagenes-9/plano.jpg"),
        "dv_editor": ("imagenes-9/toma-2.jpg", "imagenes-9/toma-12.jpg",
                       "imagenes-9/toma-22.jpg", "imagenes-9/toma-38.jpg",
                       "imagenes-9/plano.jpg", "personajes-9/cangrejo-arrastra.png"),
    }
    if fn_name in variants:
        if variant not in variants[fn_name]:
            raise ValueError(f"assets_de: variante {variant!r} no existe para {fn_name}")
        paths = variants[fn_name][variant]
    elif fn_name in plain:
        paths = plain[fn_name]
    else:
        raise ValueError(f"assets_de: componente {fn_name!r} no existe")
    return list(paths)
