#!/usr/bin/env python3
"""Mockups de la pieza 5: zócalo de plugins y Claude Code.

Todos devuelven ``(css, html, anims)``. El CSS queda encerrado en el host del
visual y los selectores de animación son relativos para que ``build_visuals``
pueda prefijarlos una sola vez.
"""

from __future__ import annotations

import base64
import math
from functools import lru_cache
from numbers import Real
from pathlib import Path

import icons
import logos
import tokens as TK
from mockups import _cursor, _cursor_css
from mockups_reels import (_contador, _glifo, _halftone, _host,
                           _need_at as _need_at_len, _shared_css)
from tokens import C, FONT, INK_ON_FILL, MONO, RADIUS, accent_a, esc, ink_a, rgba, shade_a


_PLUGINS = (
    ("omniroute", "OmniRoute"),
    ("claudemem", "Claude Mem"),
    ("headroom", "Headroom"),
    ("claudecode", "Claude Code Setup"),
    ("github", "Task Observer"),
)
_PROVIDERS = ("cerebras", "cohere", "deepseek", "fireworks", "gemini",
              "groq", "huggingface", "kimi", "mistral", "nvidia",
              "openrouter", "perplexity", "qwen", "sambanova", "xai")
_SLOTS = ((15, 135), (85, 405), (415, 5), (815, 135), (745, 405))


def _need_at(name: str, at: list, n: int) -> None:
    """Longitud, dominio y orden de los offsets de un visual."""
    _need_at_len(name, at, n)
    if any(isinstance(t, bool) or not isinstance(t, Real) or not math.isfinite(t)
           or t < 0 for t in at):
        raise ValueError(f"{name}: cada at debe ser un número finito >= 0")
    if any(b < a for a, b in zip(at, at[1:])):
        raise ValueError(f"{name}: at debe estar en orden no decreciente")


def _mosaico(iid: str, slug: str, px: int = 150, nombre: str | None = None) -> str:
    logo, _ = logos.mark(slug, round(px * .58), uid=iid)
    pill = (f'<span class="pp-name" id="{iid}-name"></span>'
            if nombre is not None else "")
    return (f'<div class="pp-mosaic" id="{iid}" style="width:{px}px;height:{px}px">'
            f'<span class="pp-logo" id="{iid}-logo">{logo}</span>{pill}</div>')


def _named_mosaic(iid: str, slug: str, px: int, nombre: str) -> str:
    empty = f'id="{iid}-name"></span>'
    return _mosaico(iid, slug, px, nombre).replace(
        empty, f'id="{iid}-name">{esc(nombre)}</span>')


def _neon(iid: str, w: int, h: int, r: int) -> str:
    return (f'<svg class="pp-neon" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'aria-hidden="true"><rect id="{iid}" x="3" y="3" width="{w - 6}" '
            f'height="{h - 6}" rx="{r}" fill="none" stroke="{C["accent"]}" '
            f'stroke-width="4" filter="drop-shadow(0 0 10px {accent_a(.8)})"/></svg>')


def _terminal(iid: str, w: int, h: int, lineas: int = 0) -> str:
    logo, _ = logos.mark("claudecode", 30, uid=f"{iid}-brand")
    rows = "".join(
        f'<i class="pp-tline" id="{iid}-line{i}" style="width:{48 + (i * 29) % 43}%"></i>'
        for i in range(lineas))
    return (f'<div class="pp-terminal" id="{iid}" style="width:{w}px;height:{h}px">'
            f'<div class="pp-tbar"><span class="pp-lights"><i></i><i></i><i></i></span>'
            f'<span class="pp-tbrand">{logo}</span></div><div class="pp-tbody">'
            f'<span class="pp-prompt">&gt;</span><span class="pp-block" id="{iid}-cursor"></span>'
            f'<div class="pp-tlines">{rows}</div></div></div>')


@lru_cache(maxsize=3)
def _sprite_data(pose: str) -> str:
    if pose not in ("salto", "espia", "espaldas"):
        raise ValueError(f"sprite: pose {pose!r} no existe")
    root = Path(__file__).resolve().parents[4]
    raw = (root / "assets" / "mascota" / f"mascota-{pose}.png").read_bytes()
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def _sprite(iid: str, pose: str, px: int) -> str:
    return (f'<img class="pp-sprite" id="{iid}" src="{_sprite_data(pose)}" alt="" '
            f'style="width:{px}px;height:{px}px"/>')


@lru_cache(maxsize=32)
def _provider_data(nombre: str) -> str:
    if nombre not in _PROVIDERS:
        raise ValueError(f"proveedor {nombre!r} no existe")
    root = Path(__file__).resolve().parents[4]
    raw = (root / "assets" / "proveedores" / f"{nombre}.svg").read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(raw).decode("ascii")


def _proveedor(iid: str, nombre: str, px: int) -> str:
    return (f'<span class="pp-provider" id="{iid}" style="width:{px}px;height:{px}px">'
            f'<img src="{_provider_data(nombre)}" alt=""/></span>')


def _icon(name: str, px: int) -> str:
    if name in ("search", "grid"):
        return _glifo(name, px)
    aliases = {"file": "doc", "browser": "desktop", "database": "stack",
               "skill": "gear", "chain": "link"}
    return icons.icon(aliases.get(name, name), px)


def _plugin_css(p: str) -> str:
    return _shared_css(p) + f"""
{p} .pp-mosaic{{position:relative;display:flex;align-items:center;justify-content:center;
  box-sizing:border-box;background:{C['surface2']};border:1px solid {TK.LINE_HI};
  border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};color:{C['text']}}}
{p} .pp-logo{{display:flex;align-items:center;justify-content:center}}
{p} .pp-name{{position:absolute;left:50%;top:calc(100% + 10px);transform:translateX(-50%);
  min-width:max-content;padding:7px 13px;background:{C['surface']};border:1px solid {TK.LINE};
  border-radius:{RADIUS['pill']}px;font-family:{FONT};font-size:26px;font-weight:800;
  color:{C['text']};line-height:1;box-shadow:{TK.SHADOW};z-index:8}}
{p} .pp-neon{{position:absolute;inset:0;overflow:visible;pointer-events:none}}
{p} .pp-terminal{{position:relative;box-sizing:border-box;background:{C['surface']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};overflow:hidden}}
{p} .pp-tbar{{height:44px;display:flex;align-items:center;justify-content:center;
  border-bottom:1px solid {TK.LINE};background:{C['surface2']}}}
{p} .pp-lights{{position:absolute;left:16px;display:flex;gap:8px}}
{p} .pp-lights i{{width:12px;height:12px;border-radius:50%;background:#FF5F57}}
{p} .pp-lights i:nth-child(2){{background:#FFBD2E}} {p} .pp-lights i:nth-child(3){{background:#28C840}}
{p} .pp-tbrand{{display:flex}} {p} .pp-tbody{{position:relative;height:calc(100% - 44px);padding:22px;
  box-sizing:border-box;color:{C['accent_hi']};font-family:{MONO};font-size:25px;font-weight:700}}
{p} .pp-block{{display:inline-block;width:13px;height:26px;margin-left:9px;background:{C['accent']};
  vertical-align:-5px;animation:ppblink 1s steps(1,end) infinite}}
{p} .pp-tlines{{position:absolute;left:24px;right:24px;top:68px;display:flex;flex-direction:column;gap:13px}}
{p} .pp-tline{{display:block;height:9px;border-radius:{RADIUS['pill']}px;background:{rgba(C['text2'], .30)}}}
{p} .pp-sprite{{display:block;object-fit:contain;image-rendering:pixelated}}
{p} .pp-provider{{display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box;
  border-radius:50%;background:{C['surface2']};border:1px solid {TK.LINE_HI};box-shadow:{TK.SHADOW}}}
{p} .pp-provider img{{width:68%;height:68%;object-fit:contain}}
{p} .ccaret{{display:inline-block;width:3px;height:24px;background:{C['accent']};vertical-align:-3px}}
{p} .tb-barrier{{position:absolute;left:170px;top:300px;width:600px;height:70px;
  display:flex;align-items:center;opacity:0;z-index:9}}
{p} .tb-barrier.shown{{opacity:1}}
{p} .tb-barrier span{{height:70px;flex:1;border:3px solid {TK.LINE_HI};
  background:repeating-linear-gradient(135deg,{C['accent']} 0 34px,{C['bg']} 34px 68px);box-shadow:{TK.SHADOW}}}
{p} .tb-barrier i{{display:block;width:24px;height:210px;background:{C['text2']};
  border:2px solid {TK.LINE_HI};border-radius:{RADIUS['sm']}px}}
@keyframes ppblink{{0%,48%{{opacity:1}}49%,100%{{opacity:.16}}}}
"""


def _barrier(cid: str, shown: bool = False) -> str:
    cls = "tb-barrier shown" if shown else "tb-barrier"
    return f'<div class="{cls}" id="{cid}-barrier"><i></i><span></span><i></i></div>'


def terminal_barrera(cid: str, at: list, lienzo: bool = False) -> tuple[str, str, list]:
    _need_at("terminal_barrera", at, 2)
    p, _, max_h = _host(cid, lienzo)
    css = _plugin_css(p) + _halftone(p) + f"""
{p} .tb-wrap{{position:relative;width:940px;height:{max_h}px;display:flex;align-items:center;justify-content:center}}
{p} .tb-clip{{position:relative;width:420px;height:300px;zoom:1.5}}
{p} .tb-wrap .tb-barrier{{left:40px;width:860px;top:{round(max_h / 2) - 10}px}}
{p} .tb-static{{position:absolute;inset:0 auto auto 0;width:420px;height:44px;overflow:hidden;
  border-radius:{RADIUS['lg']}px;z-index:3}}
{p} .tb-open{{position:absolute;inset:0;transform-origin:50% 0;opacity:0}}
"""
    html = (f'<div class="comic-dots"></div><div class="tb-wrap"><div class="tb-clip">'
            f'<div class="tb-static" id="{cid}-static">{_terminal(f"{cid}-bar", 420, 300)}</div>'
            f'<div class="tb-open" id="{cid}-open">{_terminal(f"{cid}-term", 420, 300)}</div>'
            f'</div>{_barrier(cid)}</div>')
    abrir, code = at
    anims = [("rise-bar", f"#{cid}-open", abrir, .32),
             ("drop-in", f"#{cid}-barrier", code, .18),
             ("badge-out", f"#{cid}-term-cursor", code, .08),
             ("fade-to", f"#{cid}-term", code, .18, .55),
             ("fade-to", f"#{cid}-static", code, .18, .55)]
    return css, html, anims


def _slot_outline(cid: str, i: int) -> str:
    return (f'<svg class="zp-outline" viewBox="0 0 150 150" aria-hidden="true">'
            f'<rect id="{cid}-holepath{i}" x="3" y="3" width="144" height="144" '
            f'rx="{RADIUS["lg"]}" fill="none" stroke="{TK.LINE_HI}" stroke-width="3" '
            f'stroke-dasharray="14 10"/></svg>')


def _zocalo_board(cid: str, puestos: int, protagonist: int | None = None,
                  blank_tiles: bool = False, complete: bool = False) -> str:
    slots = []
    for i, ((slug, name), (x, y)) in enumerate(zip(_PLUGINS, _SLOTS)):
        content = ""
        if complete or i < puestos:
            content = _mosaico(f"{cid}-m{i}", slug)
        elif protagonist == i:
            content = _mosaico(f"{cid}-m{i}", slug, 150, name)
        elif blank_tiles:
            content = f'<span class="zp-blank" id="{cid}-blank{i}"></span>'
        if content:
            content = f'<span class="zp-move" id="{cid}-move{i}">{content}</span>'
        neon = _neon(f"{cid}-neon{i}", 150, 150, RADIUS["lg"]) if protagonist == i else ""
        halo_style = ' style="opacity:1"' if complete or i < puestos else ""
        slots.append(f'<div class="zp-slot" id="{cid}-slot{i}" style="left:{x}px;top:{y}px">'
                     f'<span class="zp-halo" id="{cid}-halo{i}"{halo_style}></span>'
                     f'<span class="zp-flash" id="{cid}-flash{i}"></span>'
                     f'{_slot_outline(cid, i)}{content}{neon}</div>')
    return (f'<div class="zp-board" id="{cid}-board">{"".join(slots)}'
            f'<div class="zp-center" id="{cid}-center">{_terminal(f"{cid}-term", 420, 300)}</div></div>')


def zocalo(cid: str, variant: str, at: list, lienzo: bool = False,
           puestos: int = 0) -> tuple[str, str, list]:
    variants = {"instala": 3, "enciende": 2, "lista": 2}
    if variant not in variants:
        raise ValueError(f"zocalo: variante {variant!r} no existe")
    _need_at("zocalo", at, variants[variant])
    if variant == "enciende" and (isinstance(puestos, bool) or not isinstance(puestos, int)
                                   or not 0 <= puestos <= 4):
        raise ValueError("zocalo enciende: puestos debe estar entre 0 y 4")
    p, _, max_h = _host(cid, lienzo)
    scale = 1.06 if lienzo else 1
    css = _plugin_css(p) + f"""
{p} .zp-wrap{{position:relative;width:980px;height:{max_h}px;display:flex;align-items:center;justify-content:center}}
{p} .zp-scale{{position:relative;width:980px;height:700px;transform:scale({scale});transform-origin:50% 50%}}
{p} .zp-board{{position:relative;width:980px;height:700px}} {p} .zp-center{{position:absolute;left:280px;top:225px}}
{p} .zp-slot{{position:absolute;width:150px;height:150px}} {p} .zp-outline{{position:absolute;inset:0;width:150px;height:150px}}
{p} .zp-move{{position:absolute;inset:0;display:block;transform-origin:50% 50%}}
{p} .zp-halo{{position:absolute;inset:-22px;border-radius:{RADIUS['xl']}px;
  background:radial-gradient(circle,{accent_a(.25)},transparent 70%);opacity:0}}
{p} .zp-flash{{position:absolute;inset:-34px;border-radius:{RADIUS['xl']}px;
  background:radial-gradient(circle,{accent_a(.35)},transparent 70%);opacity:0}}
{p} .zp-blank{{position:absolute;inset:0;border-radius:{RADIUS['lg']}px;background:{C['surface2']};
  border:1px solid {TK.LINE_HI};box-shadow:{TK.SHADOW};opacity:0}}
{p} .zp-slot .pp-neon{{z-index:5}} {p} .zp-slot .pp-logo{{z-index:2}}
{p} .zp-listname{{position:absolute;left:230px;top:27px;min-width:250px;font-family:{FONT};font-size:27px;
  font-weight:800;color:{C['text']};opacity:0}}
{p} .zp-link{{position:absolute;left:650px;top:21px;display:flex;align-items:center;gap:8px;padding:8px 14px;
  border-radius:{RADIUS['pill']}px;background:{C['surface']};border:1px solid {TK.LINE};
  color:{C['accent_hi']};font-family:{MONO};font-size:18px;font-weight:700;opacity:0}}
"""
    anims: list = []
    if variant == "instala":
        html = (f'<div class="zp-wrap"><div class="zp-scale">{_zocalo_board(cid, 0, blank_tiles=True)}'
                f'{_barrier(cid, shown=True)}</div></div>')
        instala, cinco, plugins = at
        anims += [("draw", f"#{cid}-holepath{i}", round(instala + i * .06, 4), .30) for i in range(5)]
        anims += [("drop-in", f"#{cid}-blank{i}", round(cinco + i * .09, 4), .24) for i in range(5)]
        anims += [("chip-in", f"#{cid}-halo{i}", plugins, .22) for i in range(5)]
        anims += [("cursor-to", f"#{cid}-barrier", plugins, .30, 0, -500),
                  ("badge-out", f"#{cid}-barrier", round(plugins + .22, 4), .12)]
    elif variant == "enciende":
        html = f'<div class="zp-wrap"><div class="zp-scale">{_zocalo_board(cid, puestos, puestos)}</div></div>'
        numero, nombre_at = at
        anims.append(("chip-in", f"#{cid}-halo{puestos}", numero, .22))
        for i in range(5):
            if i != puestos:
                anims.append(("fade-to", f"#{cid}-slot{i}", numero, .22, .45))
        if puestos == 4:
            for i in range(5):
                anims += [("chip-in", f"#{cid}-flash{i}", numero, .18),
                          ("badge-out", f"#{cid}-flash{i}", round(numero + .20, 4), .14)]
        name = _PLUGINS[puestos][1]
        anims += [("draw", f"#{cid}-neon{puestos}", nombre_at, .35),
                  ("chip-in", f"#{cid}-m{puestos}-logo", nombre_at, .24),
                  ("type-word", f"#{cid}-m{puestos}-name", nombre_at, .34, name),
                  ("caret-off", f"#{cid}-m{puestos}-name", round(nombre_at + .35, 4), .01, name)]
    else:
        board = _zocalo_board(cid, 5, complete=True)
        extras = []
        for i, (_, name) in enumerate(_PLUGINS):
            row_y = 25 + i * 130
            extras.append(f'<span class="zp-listname" id="{cid}-listname{i}" style="top:{row_y + 28}px">{esc(name)}</span>'
                          f'<span class="zp-link" id="{cid}-link{i}" style="top:{row_y + 22}px">{_icon("chain", 22)}'
                          f'<span id="{cid}-linktext{i}"></span></span>')
        html = f'<div class="zp-wrap"><div class="zp-scale">{board}{"".join(extras)}</div></div>'
        cinco, link = at
        destinations = ((75, -110), (5, -250), (-325, 280), (-725, 280), (-655, 140))
        for i, (dx, dy) in enumerate(destinations):
            anims += [("cursor-to", f"#{cid}-move{i}", cinco, .45, dx, dy),
                      ("cam-push", f"#{cid}-m{i}", cinco, .45, .64, 0),
                      ("chip-in", f"#{cid}-listname{i}", round(cinco + i * .04, 4), .22)]
        anims += [("badge-out", f"#{cid}-center", cinco, .25)]
        anims += [("badge-out", f"#{cid}-holepath{i}", cinco, .20) for i in range(5)]
        anims += [("badge-out", f"#{cid}-halo{i}", cinco, .20) for i in range(5)]
        for i in range(5):
            t = round(link + i * .08, 4)
            anims += [("caret-off", f"#{cid}-linktext{i}", t, .01, "link"),
                      ("chip-in", f"#{cid}-link{i}", t, .22)]
    return css, html, anims


def anillo_proveedores(cid: str, at: list, lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("anillo_proveedores", at, 2)
    p, _, max_h = _host(cid, lienzo)
    nodes, paths, particles = [], [], []
    for i, name in enumerate(_PROVIDERS):
        ang = -math.pi / 2 + i * 2 * math.pi / len(_PROVIDERS)
        x, y = 440 + round(math.cos(ang) * 365), 470 + round(math.sin(ang) * 365)
        nodes.append(f'<span class="ap-node" style="left:{x}px;top:{y}px">'
                     f'<i class="ap-halo" id="{cid}-ph{i}"></i>{_proveedor(f"{cid}-p{i}", name, 82)}</span>')
        paths.append(f'<path id="{cid}-ray{i}" d="M480 510 L{x + 41} {y + 41}"/>')
        particles.append(f'<i class="ap-particle" id="{cid}-dot{i}" style="left:{x + 36}px;top:{y + 36}px"></i>')
    css = _plugin_css(p) + f"""
{p} .ap-wrap{{position:relative;width:960px;height:{min(max_h, 1120)}px;color:{C['text']}}}
{p} .ap-ring{{position:absolute;left:100px;top:130px;width:760px;height:760px;border:2px dashed {C['text3']};border-radius:50%}}
{p} .ap-center{{position:absolute;left:380px;top:410px}} {p} .ap-omni{{position:absolute;left:565px;top:515px}}
{p} .ap-node{{position:absolute;width:82px;height:82px}} {p} .ap-halo{{position:absolute;inset:-16px;
  border-radius:50%;background:{accent_a(.30)};filter:blur(12px);opacity:0}}
{p} .ap-rays{{position:absolute;inset:0;width:960px;height:1020px;fill:none;stroke:{C['accent']};stroke-width:3}}
{p} .ap-count{{position:absolute;left:0;right:0;top:625px;text-align:center;font-family:{FONT};font-size:110px;
  font-weight:900;color:{C['accent_hi']}}} {p} .ap-particle{{position:absolute;width:10px;height:10px;
  border-radius:50%;background:{C['accent']};box-shadow:{TK.GLOW};opacity:0}}
"""
    html = (f'<div class="ap-wrap"><div class="ap-ring"></div><svg class="ap-rays" viewBox="0 0 960 1020">'
            f'{"".join(paths)}</svg>{"".join(nodes)}{"".join(particles)}'
            f'<div class="ap-center">{_mosaico(f"{cid}-code", "claudecode", 200)}</div>'
            f'<div class="ap-omni">{_mosaico(f"{cid}-omni", "omniroute", 92)}</div>'
            f'<div class="ap-count">{_contador(f"{cid}-count", 0)}</div></div>')
    two_hundred, providers = at
    anims: list = [("count-roll", f"#{cid}-count", two_hundred, .70, 0, 200, "+")]
    for i in range(15):
        t = round(two_hundred + i * .03, 4)
        anims += [("chip-in", f"#{cid}-p{i}", t, .22), ("draw", f"#{cid}-ray{i}", t, .32)]
        tp = round(providers + i * .025, 4)
        anims += [("chip-in", f"#{cid}-ph{i}", tp, .18),
                  ("chip-in", f"#{cid}-dot{i}", tp, .12),
                  ("cursor-to", f"#{cid}-dot{i}", tp, .42,
                   480 - (440 + round(math.cos(-math.pi / 2 + i * 2 * math.pi / 15) * 365)),
                   510 - (470 + round(math.sin(-math.pi / 2 + i * 2 * math.pi / 15) * 365)))]
    return css, html, anims


def costo_llaves(cid: str, at: list, lienzo: bool = False) -> tuple[str, str, list]:
    _need_at("costo_llaves", at, 3)
    p, _, max_h = _host(cid, lienzo)
    cards = []
    for i, name in enumerate(("groq", "gemini", "openrouter")):
        cards.append(f'<div class="cl-card" id="{cid}-card{i}"><div class="cl-front" id="{cid}-front{i}">'
                     f'{_proveedor(f"{cid}-p{i}", name, 150)}<span class="cl-cost">'
                     f'{_contador(f"{cid}-cost{i}", 20, "$ ")}</span></div>'
                     f'<div class="cl-key" id="{cid}-key{i}">{_icon("key", 48)}'
                     f'<span>sk-&bull;&bull;&bull;&bull;&bull;&bull;</span></div>'
                     f'<span class="cl-model" id="{cid}-model{i}"><i></i></span></div>')
    css = _plugin_css(p) + f"""
{p} .cl-wrap{{width:940px;height:{max_h}px;display:flex;align-items:center;justify-content:center;gap:55px;color:{C['text']}}}
{p} .cl-card{{position:relative;width:240px;height:270px;display:flex;align-items:center;justify-content:center;transform-style:preserve-3d}}
{p} .cl-front{{display:flex;flex-direction:column;align-items:center;gap:20px}} {p} .cl-cost{{font-family:{MONO};font-size:34px;font-weight:700;color:{C['accent_hi']}}}
{p} .cl-key{{position:absolute;inset:35px 0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:22px;
  background:{C['surface']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};
  color:{C['text']};font-family:{MONO};font-size:19px;font-weight:700;opacity:0}}
{p} .cl-model{{position:absolute;left:70px;bottom:-25px;width:100px;height:74px;border-radius:{RADIUS['md']}px;
  background:{C['surface2']};border:1px solid {TK.LINE};opacity:0;z-index:-1}}
{p} .cl-model i{{position:absolute;left:38px;top:23px;width:24px;height:24px;background:{C['accent']};transform:rotate(45deg);box-shadow:{TK.GLOW}}}
"""
    html = f'<div class="cl-wrap">{"".join(cards)}</div>'
    free, api, ai = at
    anims: list = []
    for i in range(3):
        anims += [("count-roll", f"#{cid}-cost{i}", free, .42, 20, 0, "$ "),
                  ("fade-to", f"#{cid}-cost{i}", round(free + .30, 4), .20, .4),
                  ("flip-out", f"#{cid}-card{i}", round(api + i * .04, 4), .22),
                  ("badge-out", f"#{cid}-front{i}", round(api + .20 + i * .04, 4), .01),
                  ("chip-in", f"#{cid}-key{i}", round(api + .21 + i * .04, 4), .01),
                  ("flip-in", f"#{cid}-card{i}", round(api + .23 + i * .04, 4), .28),
                  ("chip-in", f"#{cid}-model{i}", round(ai + i * .08, 4), .24)]
    return css, html, anims


def piedras_modelo(cid: str, at: list, lienzo: bool = False) -> tuple[str, str, list]:
    _need_at("piedras_modelo", at, 3)
    p, _, max_h = _host(cid, lienzo)
    names = ("deepseek", "mistral", "qwen", "kimi", "cerebras", "nvidia", "groq", "xai")
    stones = "".join(f'<span class="pm-stone {"extra" if i >= 6 else ""}" id="{cid}-stone{i}">'
                     f'<i class="pm-halo" id="{cid}-halo{i}"></i>'
                     f'{_proveedor(f"{cid}-p{i}", name, 118)}</span>' for i, name in enumerate(names))
    css = _plugin_css(p) + f"""
{p} .pm-wrap{{position:relative;width:940px;height:{max_h}px;display:flex;align-items:center;overflow:hidden}}
{p} .pm-river{{position:absolute;left:15px;top:395px;width:1200px;height:120px;fill:none;stroke:{accent_a(.15)};stroke-width:18}}
{p} .pm-row{{position:absolute;left:10px;top:325px;width:1220px;display:flex;align-items:center;gap:34px}}
{p} .pm-stone{{position:relative;flex:0 0 118px}} {p} .pm-stone.extra{{opacity:0}}
{p} .pm-halo{{position:absolute;inset:-18px;border-radius:50%;background:{accent_a(.30)};filter:blur(12px);opacity:0}}
{p} .pm-mascot-x{{position:absolute;left:2px;top:180px;z-index:8}} {p} .pm-mascot-y{{position:relative}}
"""
    html = (f'<div class="pm-wrap"><svg class="pm-river" viewBox="0 0 1200 120">'
            f'<path d="M0 62 C180 4 310 118 490 62 S810 5 1200 62"/></svg>'
            f'<div class="pm-row" id="{cid}-row">{stones}</div><div class="pm-mascot-x" id="{cid}-mascot-x">'
            f'<div class="pm-mascot-y" id="{cid}-mascot-y">{_sprite(f"{cid}-pet", "salto", 170)}</div></div></div>')
    jump, next_at, model = at
    anims = [("fade-to", f"#{cid}-stone0", jump, .24, .3),
             ("cursor-to", f"#{cid}-mascot-x", jump, .45, 152, 0),
             ("cursor-to", f"#{cid}-mascot-y", jump, .22, 0, -95),
             ("cursor-to", f"#{cid}-mascot-y", round(jump + .22, 4), .23, 0, 0),
             ("chip-in", f"#{cid}-halo1", next_at, .22),
             ("cursor-to", f"#{cid}-row", model, .42, -260, 0),
             ("chip-in", f"#{cid}-stone6", model, .22),
             ("chip-in", f"#{cid}-stone7", round(model + .08, 4), .22)]
    return css, html, anims


def contador_tokens(cid: str, at: list, lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("contador_tokens", at, 3)
    p, _, max_h = _host(cid, lienzo)
    coins = []
    for i in range(40):
        left = 35 + (i * 83) % 860
        bottom = 40 + (i // 10) * 58 + (i * 17) % 34
        coins.append(f'<span class="ct-coin" id="{cid}-coin{i}" style="left:{left}px;bottom:{bottom}px">T</span>')
    css = _plugin_css(p) + f"""
{p} .ct-wrap{{position:relative;width:960px;height:{min(max_h, 1120)}px;display:flex;align-items:flex-start;justify-content:center;padding-top:300px;box-sizing:border-box;overflow:hidden}}
{p} .ct-mountain{{position:absolute;inset:0;z-index:1}} {p} .ct-coin{{position:absolute;width:52px;height:52px;
  display:flex;align-items:center;justify-content:center;border-radius:50%;background:{C['surface2']};border:1px solid {TK.LINE_HI};
  color:{C['text2']};font-family:{MONO};font-size:22px;font-weight:700;opacity:0}}
{p} .ct-number{{position:relative;z-index:4;font-family:{FONT};font-size:90px;font-weight:900;color:{C['text']};
  white-space:nowrap;transform-origin:50% 50%}} {p} .ct-accent{{position:absolute;inset:0;display:flex;align-items:center;
  justify-content:center;color:{C['accent_hi']};text-shadow:{TK.GLOW};opacity:0}}
"""
    html = (f'<div class="ct-wrap"><div class="ct-mountain">{"".join(coins)}</div>'
            f'<div class="ct-number" id="{cid}-number">{_contador(f"{cid}-count", 0)}'
            f'<span class="ct-accent" id="{cid}-accent" data-layout-allow-overlap></span></div></div>')
    sixteen, millions, tokens = at
    final = "1.600.000.000"
    anims: list = [("count-roll", f"#{cid}-count", sixteen, 1.20, 0, 1600000000, ""),
                   ("caret-off", f"#{cid}-count", round(sixteen + 1.20, 4), .01, final),
                   ("cam-push", f"#{cid}-number", millions, .42, 1.28, 0),
                   ("caret-off", f"#{cid}-accent", millions, .01, final),
                   ("chip-in", f"#{cid}-accent", millions, .24),
                   ("fade-to", f"#{cid}-count", round(millions + .20, 4), .06, 0)]
    anims += [("drop-in", f"#{cid}-coin{i}", round(tokens + i * .012, 4), .24)
              for i in range(40)]
    return css, html, anims


def dos_terminales(cid: str, at: list, lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("dos_terminales", at, 3)
    p, _, max_h = _host(cid, lienzo)
    css = _plugin_css(p) + f"""
{p} .dt-wrap{{position:relative;width:960px;height:{min(max_h, 850)}px;display:flex;align-items:center;justify-content:space-between}}
{p} .dt-shell{{position:relative;transform-origin:50% 100%}} {p} .dt-thread{{position:absolute;inset:0;width:960px;height:850px;
  fill:none;stroke:{C['accent']};stroke-width:5;filter:drop-shadow(0 0 10px {accent_a(.8)})}}
{p} .dt-right .pp-tline{{opacity:0}}
"""
    html = (f'<div class="dt-wrap"><div class="dt-shell" id="{cid}-left">'
            f'{_terminal(f"{cid}-tl", 440, 520, 12)}</div><svg class="dt-thread" viewBox="0 0 960 850">'
            f'<path id="{cid}-thread1" d="M418 420 C500 330 510 330 555 410"/>'
            f'<path id="{cid}-thread2" d="M555 410 C610 475 650 450 700 390"/></svg>'
            f'<div class="dt-shell dt-right">{_terminal(f"{cid}-tr", 440, 520, 10)}</div></div>')
    memory, session, next_at = at
    anims = [("draw", f"#{cid}-thread1", memory, .40),
             ("scale-y-to", f"#{cid}-left", session, .28, .04),
             ("badge-out", f"#{cid}-left", round(session + .24, 4), .08),
             ("fade-to", f"#{cid}-thread1", session, .24, .55),
             ("draw", f"#{cid}-thread2", next_at, .40)]
    anims += [("rise-bar", f"#{cid}-tr-line{i}", round(next_at + i * .04, 4), .22)
              for i in range(10)]
    return css, html, anims


def cable_headroom(cid: str, variant: str, at: list,
                   lienzo: bool = False) -> tuple[str, str, list]:
    if variant not in ("clavar", "chat"):
        raise ValueError(f"cable_headroom: variante {variant!r} no existe")
    _need_at("cable_headroom", at, 2)
    p, _, max_h = _host(cid, lienzo)
    css = _plugin_css(p) + f"""
{p} .ch-wrap{{position:relative;width:940px;height:{max_h}px;display:flex;align-items:center;justify-content:center;color:{C['text']}}}
{p} .ch-cable{{position:absolute;left:20px;right:20px;top:50%;height:18px;background:{C['text3']};border:2px solid {TK.LINE_HI};border-radius:{RADIUS['pill']}px}}
{p} .ch-center{{position:relative;z-index:4}} {p} .ch-plug{{position:absolute;top:calc(50% - 17px);width:44px;height:52px;
  border:3px solid {TK.LINE_HI};background:{C['surface2']};border-radius:{RADIUS['sm']}px;opacity:0}}
{p} .ch-plug.left{{left:330px}} {p} .ch-plug.right{{right:330px}} {p} .ch-mid{{position:absolute;left:365px;top:calc(50% - 15px);width:210px;height:48px;background:{C['text3']}}}
{p} .ch-chat{{position:absolute;left:25px;top:245px;width:260px;height:180px;padding:24px;background:{C['surface']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};opacity:0}}
{p} .ch-chat i{{display:block;width:3px;height:32px;background:{C['accent']}}}
{p} .ch-model{{position:absolute;right:25px;top:245px;opacity:0}} {p} .ch-extra{{position:absolute;top:calc(50% - 4px);height:10px;
  width:0;background:{C['accent']}}} {p} .ch-extra.left{{left:280px}} {p} .ch-extra.right{{right:280px}}
{p} .ch-dot{{position:absolute;left:170px;top:calc(50% - 1px);width:16px;height:16px;border-radius:50%;background:{C['accent']};box-shadow:{TK.GLOW};opacity:0}}
{p} .ch-impact{{position:absolute;inset:-24px;border:5px solid {C['accent']};border-radius:{RADIUS['xl']}px;opacity:0}}
"""
    if variant == "clavar":
        html = (f'<div class="ch-wrap"><span class="ch-cable"></span><span class="ch-mid" id="{cid}-mid"></span>'
                f'<span class="ch-plug left" id="{cid}-plugl"></span><span class="ch-plug right" id="{cid}-plugr"></span>'
                f'<div class="ch-center" id="{cid}-head"><i class="ch-impact" id="{cid}-impact"></i>'
                f'{_mosaico(f"{cid}-hm", "headroom", 170)}</div></div>')
        put, middle = at
        anims = [("drop-in", f"#{cid}-head", put, .28),
                 ("stamp", f"#{cid}-impact", middle, .22),
                 ("badge-out", f"#{cid}-impact", round(middle + .22, 4), .14),
                 ("badge-out", f"#{cid}-mid", middle, .16),
                 ("chip-in", f"#{cid}-plugl", middle, .18),
                 ("chip-in", f"#{cid}-plugr", middle, .18)]
    else:
        html = (f'<div class="ch-wrap"><span class="ch-cable"></span><span class="ch-plug left" style="opacity:1"></span>'
                f'<span class="ch-plug right" style="opacity:1"></span><div class="ch-center">'
                f'{_mosaico(f"{cid}-hm", "headroom", 170)}</div><div class="ch-chat" id="{cid}-chat"><i></i></div>'
                f'<div class="ch-model" id="{cid}-model">{_mosaico(f"{cid}-claude", "claude", 150)}</div>'
                f'<span class="ch-extra left" id="{cid}-xl"></span><span class="ch-extra right" id="{cid}-xr"></span>'
                f'<span class="ch-dot" id="{cid}-dot"></span></div>')
        you, model = at
        anims = [("rise-in", f"#{cid}-chat", you, .30),
                 ("chip-in", f"#{cid}-model", model, .24),
                 ("grow-x", f"#{cid}-xl", model, .30, 120),
                 ("grow-x", f"#{cid}-xr", model, .30, 120),
                 ("chip-in", f"#{cid}-dot", model, .12),
                 ("cursor-to", f"#{cid}-dot", model, .55, 590, 0)]
    return css, html, anims


def prensa(cid: str, at: list, lienzo: bool = False) -> tuple[str, str, list]:
    _need_at("prensa", at, 3)
    p, _, max_h = _host(cid, lienzo)
    rows = []
    scraps = []
    for i in range(30):
        edge = i < 8 or i >= 22
        row = f'<i class="pr-line" style="width:{58 + (i * 19) % 37}%"></i>'
        if edge:
            scraps.append(f'<span class="pr-scrap" id="{cid}-scrap{i}">{row}</span>')
        else:
            rows.append(row)
    css = _plugin_css(p) + _halftone(p) + f"""
{p} .pr-wrap{{position:relative;width:940px;height:{max_h}px;display:flex;align-items:flex-end;justify-content:center;overflow:hidden}}
{p} .pr-block{{position:relative;width:320px;height:620px;padding:20px;box-sizing:border-box;background:{C['surface']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['md']}px;box-shadow:{TK.SHADOW};transform-origin:50% 100%;z-index:2}}
{p} .pr-lines{{display:flex;flex-direction:column;gap:10px}} {p} .pr-line{{display:block;height:9px;border-radius:{RADIUS['pill']}px;background:{rgba(C['text2'], .30)}}}
{p} .pr-press{{position:absolute;left:285px;top:4px;width:370px;height:125px;z-index:5}}
{p} .pr-stem{{display:block;width:80px;height:70px;margin:auto;background:{C['text2']};border:2px solid {TK.LINE_HI}}}
{p} .pr-plate{{display:block;height:48px;background:{C['text2']};border:2px solid {TK.LINE_HI};border-radius:{RADIUS['sm']}px}}
{p} .pr-scraps{{position:absolute;left:310px;bottom:30px;width:320px;height:560px;z-index:4;pointer-events:none}}
{p} .pr-scrap{{position:absolute;left:0;right:0;height:16px;padding:4px 12px;background:{C['surface2']};
  border:1px solid {TK.LINE};transform-origin:50% 50%}}
"""
    positioned = "".join(s.replace('class="pr-scrap"',
                                   f'class="pr-scrap" style="top:{i * 33}px"')
                           for i, s in enumerate(scraps))
    html = (f'<div class="comic-dots"></div><div class="pr-wrap"><div class="pr-press" id="{cid}-press">'
            f'<span class="pr-stem"></span><span class="pr-plate"></span></div>'
            f'<div class="pr-block" id="{cid}-block"><div class="pr-lines">{"".join(rows)}</div></div>'
            f'<div class="pr-scraps">{positioned}</div></div>')
    compress, cut, excess = at
    anims: list = [("cursor-to", f"#{cid}-press", compress, .35, 0, 355),
                   ("scale-y-to", f"#{cid}-block", compress, .38, .34)]
    edge_ids = list(range(8)) + list(range(22, 30))
    for j, i in enumerate(edge_ids):
        direction = -220 if j % 2 == 0 else 220
        anims += [("rot-to", f"#{cid}-scrap{i}", round(cut + j * .018, 4), .24,
                   -12 if j % 2 == 0 else 12),
                  ("cursor-to", f"#{cid}-scrap{i}", round(cut + j * .018, 4), .30, direction, -80 + j * 8),
                  ("cursor-to", f"#{cid}-scrap{i}", round(excess + j * .018, 4), .38, direction, 700)]
    return css, html, anims


def dos_salidas(cid: str, at: list, lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("dos_salidas", at, 2)
    p, _, max_h = _host(cid, lienzo)
    panels = []
    for side in ("l", "r"):
        lines = "".join(f'<i style="width:{55 + (i * 23) % 37}%"></i>' for i in range(8))
        coins = "".join(f'<span class="ds-token" id="{cid}-{side}-tok{i}" '
                        f'style="left:{(i % 4) * 48}px;bottom:{(i // 4) * 42}px">T</span>' for i in range(12))
        panels.append(f'<div class="ds-side"><div class="ds-screen"><span class="ds-check" id="{cid}-{side}-check">'
                      f'{_icon("check", 38)}</span><div class="ds-lines">{lines}</div></div>'
                      f'<div class="ds-stack">{coins}</div></div>')
    css = _plugin_css(p) + f"""
{p} .ds-wrap{{width:960px;height:{min(max_h, 900)}px;display:flex;align-items:center;justify-content:center;gap:70px;color:{C['text']}}}
{p} .ds-side{{width:400px;display:flex;flex-direction:column;align-items:center;gap:30px}}
{p} .ds-screen{{position:relative;width:400px;height:300px;padding:70px 35px 30px;box-sizing:border-box;background:{C['surface']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW}}}
{p} .ds-lines{{display:flex;flex-direction:column;gap:13px}} {p} .ds-lines i{{display:block;height:10px;background:{rgba(C['text2'], .30)};border-radius:{RADIUS['pill']}px}}
{p} .ds-check{{position:absolute;right:22px;top:18px;width:58px;height:58px;display:flex;align-items:center;justify-content:center;
  border-radius:50%;background:{C['go']};color:{INK_ON_FILL['success']};opacity:0}}
{p} .ds-stack{{position:relative;width:184px;height:126px}} {p} .ds-token{{position:absolute;width:48px;height:48px;display:flex;
  align-items:center;justify-content:center;border-radius:50%;background:{C['surface2']};border:1px solid {TK.LINE_HI};
  color:{C['text2']};font-family:{MONO};font-size:17px;font-weight:700}}
"""
    html = f'<div class="ds-wrap">{"".join(panels)}</div>'
    same, result = at
    anims: list = [("stamp", f"#{cid}-l-check", same, .22),
                   ("stamp", f"#{cid}-r-check", same, .22)]
    for i in range(4, 12):
        anims += [("cursor-to", f"#{cid}-r-tok{i}", round(result + (i - 4) * .025, 4), .28, 0, 70),
                  ("badge-out", f"#{cid}-r-tok{i}", round(result + .18 + (i - 4) * .025, 4), .18)]
    return css, html, anims


def sello_oficial(cid: str, at: list, lienzo: bool = False) -> tuple[str, str, list]:
    _need_at("sello_oficial", at, 2)
    p, _, max_h = _host(cid, lienzo)
    anthropic, _ = logos.mark("anthropic", 90, uid=f"{cid}-anthropic")
    css = _plugin_css(p) + f"""
{p} .so-wrap{{position:relative;width:940px;height:{max_h}px;display:flex;align-items:center;justify-content:center;color:{C['text']}}}
{p} .so-main{{position:relative}} {p} .so-badge{{position:absolute;right:-26px;top:-28px;width:64px;height:64px;
  display:flex;align-items:center;justify-content:center;border-radius:50%;background:{C['go']};
  color:{INK_ON_FILL['success']};box-shadow:{TK.SHADOW};opacity:0;z-index:7}}
{p} .so-brand{{position:absolute;left:40px;top:245px;display:flex;opacity:0;z-index:5}}
{p} .so-glow{{position:absolute;left:-38px;top:-38px;width:166px;height:166px;border-radius:50%;
  background:radial-gradient(circle,{accent_a(.22)},transparent 70%);filter:blur(14px);opacity:0;z-index:-1}}
"""
    html = (f'<div class="so-wrap"><div class="so-main">'
            f'{_named_mosaic(f"{cid}-setup", "claudecode", 170, "Claude Code Setup")}'
            f'<span class="so-badge" id="{cid}-badge">{_icon("check", 40)}</span>'
            f'<span class="so-brand" id="{cid}-brand"><i class="so-glow" id="{cid}-glow"></i>{anthropic}</span></div></div>')
    official, anth = at
    anims = [("stamp", f"#{cid}-badge", official, .24),
             ("chip-in", f"#{cid}-brand", anth, .25),
             ("fade-to", f"#{cid}-glow", anth, .28, 1)]
    return css, html, anims


_TREE_ROWS = (("src/", 0, "folder"), ("app.ts", 1, "file"), ("api/", 1, "folder"),
              ("routes.ts", 2, "file"), ("db.ts", 2, "file"), ("tests/", 0, "folder"),
              ("app.test.ts", 1, "file"), ("package.json", 0, "file"),
              ("README.md", 0, "file"), (".claude/", 0, "folder"),
              ("settings.json", 1, "file"), ("CLAUDE.md", 0, "file"),
              ("scripts/", 0, "folder"), ("build.ts", 1, "file"))


def _tree(cid: str, count: int = 14) -> str:
    return "".join(f'<div class="ae-row" id="{cid}-row{i}" style="padding-left:{level * 46}px">'
                   f'{_icon("repo" if kind == "folder" else "file", 30)}<span>{esc(name)}</span></div>'
                   for i, (name, level, kind) in enumerate(_TREE_ROWS[:count]))


def arbol_escaneo(cid: str, at: list, lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("arbol_escaneo", at, 2)
    p, _, max_h = _host(cid, lienzo)
    css = _plugin_css(p) + f"""
{p} .ae-wrap{{position:relative;width:900px;height:{min(max_h, 1120)}px;padding:45px 65px;box-sizing:border-box;
  background:{C['surface']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};overflow:hidden}}
{p} .ae-tree{{display:flex;flex-direction:column;gap:13px}} {p} .ae-row{{height:52px;display:flex;align-items:center;gap:15px;
  box-sizing:border-box;color:{C['text3']};font-family:{MONO};font-size:23px;font-weight:700}}
{p} .ae-scan{{position:absolute;left:0;right:0;top:40px;height:5px;background:{C['accent']};box-shadow:{TK.GLOW};z-index:5}}
"""
    html = f'<div class="ae-wrap"><div class="ae-tree">{_tree(cid)}</div><span class="ae-scan" id="{cid}-scan"></span></div>'
    review, code = at
    anims: list = [("cursor-to", f"#{cid}-scan", review, 1.30, 0, 930)]
    anims += [("color-to", f"#{cid}-row{i}", round(code + i * (1.30 / 14), 4), .18, C["text"])
              for i in range(14)]
    return css, html, anims


def _server(iid: str) -> str:
    units = []
    for row in range(3):
        leds = "".join(f'<i id="{iid}-led{row}-{j}"></i>' for j in range(3))
        units.append(f'<span class="sm-unit">{leds}</span>')
    return f'<div class="sm-server" id="{iid}">{"".join(units)}</div>'


def servidor_mcp(cid: str, variant: str, at: list,
                 lienzo: bool = False) -> tuple[str, str, list]:
    variants = {"conectar": 2, "aterrizar": 1}
    if variant not in variants:
        raise ValueError(f"servidor_mcp: variante {variant!r} no existe")
    _need_at("servidor_mcp", at, variants[variant])
    p, _, max_h = _host(cid, lienzo)
    services = "".join(f'<span class="sm-service s{i}" id="{cid}-svc{i}">{_icon(name, 48)}</span>'
                       for i, name in enumerate(("database", "browser", "file")))
    paths = "".join(f'<path id="{cid}-path{i}" d="{d}"/>' for i, d in enumerate(
        ("M470 280 C260 300 210 390 180 455", "M470 280 V470", "M470 280 C680 300 730 390 760 455")))
    finals = ("".join(f'<path id="{cid}-final{i}" d="M{180 + i * 290} 455 C{180 + i * 290} 590 {330 + i * 135} 600 {330 + i * 135} 675"/>'
                      for i in range(3)) if variant == "aterrizar" else "")
    tree_rows = _tree(f"{cid}-tree", 6)
    halos = "".join(f'<i class="sm-rowhalo" id="{cid}-rowhalo{i}" style="top:{i * 52}px"></i>' for i in range(3))
    css = _plugin_css(p) + f"""
{p} .sm-wrap{{position:relative;width:940px;height:{max_h}px;color:{C['text']}}}
{p} .sm-outline{{position:absolute;left:340px;top:55px;width:260px;height:200px;border:3px dashed {TK.LINE_HI};border-radius:{RADIUS['lg']}px}}
{p} .sm-server{{position:absolute;left:340px;top:55px;width:260px;height:200px;padding:13px;box-sizing:border-box;
  display:flex;flex-direction:column;gap:10px;background:{C['surface']};border:1px solid {TK.LINE_HI};
  border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};{'opacity:0;' if variant == 'conectar' else ''}}}
{p} .sm-unit{{height:50px;display:flex;align-items:center;justify-content:flex-end;gap:12px;padding:0 14px;background:{C['surface2']};
  border:1px solid {TK.LINE};border-radius:{RADIUS['sm']}px}} {p} .sm-unit i{{width:12px;height:12px;border-radius:50%;background:{C['go']};{'opacity:0;' if variant == 'conectar' else ''}}}
{p} .sm-service{{position:absolute;width:100px;height:100px;display:flex;align-items:center;justify-content:center;border-radius:50%;
  background:{C['surface2']};border:1px solid {TK.LINE_HI};box-shadow:{TK.SHADOW};{'opacity:0;' if variant == 'conectar' else ''}}}
{p} .sm-service.s0{{left:130px;top:405px}} {p} .sm-service.s1{{left:420px;top:440px}} {p} .sm-service.s2{{left:710px;top:405px}}
{p} .sm-lines{{position:absolute;inset:0;width:940px;height:{max_h}px;fill:none;stroke:{C['accent']};stroke-width:4;filter:drop-shadow(0 0 8px {accent_a(.7)})}}
{p} .sm-tree{{position:absolute;left:220px;bottom:20px;width:500px;padding:20px 30px;background:{C['surface']};border:1px solid {TK.LINE};border-radius:{RADIUS['md']}px;{'opacity:0;' if variant == 'conectar' else ''}}}
{p} .sm-tree .ae-row{{height:52px;display:flex;align-items:center;gap:12px;color:{C['text3']};font-family:{MONO};font-size:18px}}
{p} .sm-rowhalo{{position:absolute;left:20px;right:20px;height:46px;border-radius:{RADIUS['sm']}px;background:{accent_a(.22)};opacity:0}}
"""
    html = (f'<div class="sm-wrap"><span class="sm-outline"></span><svg class="sm-lines" viewBox="0 0 940 {max_h}">'
            f'{paths}{finals}</svg>{_server(f"{cid}-server")}{services}'
            f'<div class="sm-tree" id="{cid}-treepanel">{halos}{tree_rows}</div></div>')
    anims: list = []
    if variant == "conectar":
        servers, mcp = at
        anims += [("rise-in", f"#{cid}-server", servers, .30)]
        anims += [("chip-in", f"#{cid}-server-led{r}-{j}", round(servers + (r * 3 + j) * .08, 4), .16)
                  for r in range(3) for j in range(3)]
        for i in range(3):
            anims += [("draw", f"#{cid}-path{i}", round(mcp + i * .06, 4), .38),
                      ("chip-in", f"#{cid}-svc{i}", round(mcp + i * .06, 4), .22)]
        anims.append(("rise-in", f"#{cid}-treepanel", mcp, .30))
    else:
        project = at[0]
        for i in range(3):
            anims += [("draw", f"#{cid}-final{i}", round(project + i * .06, 4), .36),
                      ("chip-in", f"#{cid}-rowhalo{i}", round(project + .18 + i * .06, 4), .22)]
    return css, html, anims


def mascota_cuaderno(cid: str, at: list, lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("mascota_cuaderno", at, 3)
    p, _, max_h = _host(cid, lienzo)
    scribbles = "".join(f'<svg class="mc-scribble" id="{cid}-scribsvg{i}" viewBox="0 0 100 60" '
                        f'style="left:{430 + i * 25}px;top:{350 + i * 40}px"><path id="{cid}-scrib{i}" '
                        f'd="M5 35 C25 {5 + i * 5} 55 {55 - i * 4} 92 22"/></svg>' for i in range(3))
    css = _plugin_css(p) + _cursor_css(p) + f"""
{p} .mc-wrap{{position:relative;width:960px;height:{min(max_h, 1060)}px;overflow:hidden;color:{C['text']}}}
{p} .mc-terminal{{position:absolute;left:300px;top:280px}} {p} .mc-pet{{position:absolute;left:-300px;top:360px;z-index:7}}
{p} .mc-eyes{{position:absolute;left:82px;top:62px;width:96px;height:54px;border-radius:50%;background:{accent_a(.5)};
  filter:blur(13px);opacity:0}} {p} .mc-scribble{{position:absolute;width:100px;height:60px;overflow:visible;
  fill:none;stroke:{C['accent']};stroke-width:5;stroke-linecap:round}}
{p} .mc-sign{{position:absolute;left:95px;top:600px;width:270px;height:150px;fill:none;stroke:{C['accent_hi']};
  stroke-width:7;stroke-linecap:round;stroke-linejoin:round}}
"""
    html = (f'<div class="mc-wrap"><div class="mc-terminal">{_terminal(f"{cid}-term", 520, 340, 4)}</div>'
            f'<div class="mc-pet" id="{cid}-petmove"><span class="mc-eyes" id="{cid}-eyes"></span>'
            f'{_sprite(f"{cid}-pet", "espia", 260)}</div>{_cursor(cid)}{scribbles}'
            f'<svg class="mc-sign" viewBox="0 0 270 150"><path id="{cid}-sign" '
            f'd="M8 110 C55 15 75 130 118 48 S165 135 205 52 C225 24 244 64 262 30"/></svg></div>')
    look, work, style = at
    anims: list = [("cursor-to", f"#{cid}-petmove", look, .42, 300, 0),
                   ("chip-in", f"#{cid}-eyes", look, .22),
                   ("cursor-enter", f"#{cid}-cursor", work, .30, 520, 390)]
    points = ((620, 360), (460, 430), (670, 500))
    for i, (x, y) in enumerate(points):
        t = round(work + i * .35, 4)
        anims += [("cursor-to", f"#{cid}-cursor", t, .18, x, y),
                  ("click", f"#{cid}-cursor", round(t + .18, 4), .20, f"#{cid}-ring"),
                  ("draw", f"#{cid}-scrib{i}", round(t + .08, 4), .25),
                  ("cursor-to", f"#{cid}-scribsvg{i}", round(t + .18, 4), .30, -390 - i * 15, 230 - i * 30)]
    anims.append(("draw", f"#{cid}-sign", style, .50))
    return css, html, anims


def reloj_fondo(cid: str, at: list, lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("reloj_fondo", at, 2)
    p, _, max_h = _host(cid, lienzo)
    cards = "".join(f'<div class="rf-card">{_icon(name, 50)}<span class="rf-track">'
                    f'<i id="{cid}-bar{i}" style="height:{35 + i * 12}%"></i></span></div>'
                    for i, name in enumerate(("code", "strategy", "build", "inspect")))
    css = _plugin_css(p) + f"""
{p} .rf-wrap{{position:relative;width:960px;height:{min(max_h, 1050)}px;display:flex;align-items:center;justify-content:center;color:{C['text']}}}
{p} .rf-back{{position:relative;width:880px;display:flex;align-items:center;gap:38px;transform-origin:50% 50%}}
{p} .rf-cards{{display:flex;gap:20px}} {p} .rf-card{{width:150px;height:250px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:28px;background:{C['surface']};border:1px solid {TK.LINE_HI};
  border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW}}} {p} .rf-track{{position:relative;width:24px;height:110px;
  border-radius:{RADIUS['pill']}px;background:{C['surface3']};overflow:hidden;display:flex;align-items:flex-end}}
{p} .rf-track i{{display:block;width:100%;background:{C['accent']};transform-origin:50% 100%}}
{p} .rf-clock{{width:190px;height:190px;border:5px solid {TK.LINE_HI};border-radius:50%;position:relative;background:{C['surface']}}}
{p} .rf-hand{{position:absolute;left:92px;bottom:92px;width:5px;border-radius:{RADIUS['pill']}px;background:{C['text']};transform-origin:50% 100%}}
{p} .rf-hand.short{{height:50px;transform:rotate(45deg)}} {p} .rf-hand.long{{height:76px}}
{p} .rf-terminal{{position:absolute;left:220px;top:330px;opacity:0;z-index:8}} {p} .rf-terminal .pp-tline{{opacity:0}}
"""
    html = (f'<div class="rf-wrap"><div class="rf-back" id="{cid}-back"><div class="rf-cards">{cards}</div>'
            f'<div class="rf-clock"><i class="rf-hand short"></i><i class="rf-hand long" id="{cid}-long"></i></div></div>'
            f'<div class="rf-terminal" id="{cid}-terminal">{_terminal(f"{cid}-term", 520, 390, 8)}</div></div>')
    time, plane = at
    anims: list = [("rot-to", f"#{cid}-long", time, 1.20, 360)]
    anims += [("rise-bar", f"#{cid}-bar{i}", round(time + i * .09, 4), .32) for i in range(4)]
    anims += [("cam-push", f"#{cid}-back", plane, .40, .78, 0),
              ("fade-to", f"#{cid}-back", plane, .40, .35),
              ("blur-to", f"#{cid}-back", plane, .40, 6),
              ("rise-in", f"#{cid}-terminal", plane, .32)]
    anims += [("chip-in", f"#{cid}-term-line{i}", round(plane + .18 + i * .06, 4), .22)
              for i in range(8)]
    return css, html, anims
