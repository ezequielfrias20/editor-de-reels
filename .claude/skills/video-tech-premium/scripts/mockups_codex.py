#!/usr/bin/env python3
"""Claude Code + Codex para la pieza 8.

Las interfaces se recrean en HTML, los personajes permanecen como archivos
PNG referenciados y todos los tiempos son offsets del visual en ``at``.
"""

from __future__ import annotations

import re

import icons
import logos
import tokens as TK
from mockups import text_px
from mockups_plugins import _need_at
from mockups_reels import _host
from tokens import C, FONT, MONO, RADIUS, esc, mix, rgba


_FONDOS = ("claro", "oscuro", "comic")
_POSES = {
    "cangrejo": ("piensa", "sello", "lupa", "caja", "encogido", "saluda",
                 "arrastra", "rueda", "asoma", "pinta"),
    "obrero": ("caja-herramientas", "martillo", "linterna", "carga", "camina", "tira"),
}
_POSES_9 = {"arrastra", "rueda", "asoma", "pinta"}
_COMANDOS = (
    "/plugin marketplace add openai/codex-plugin-cc",
    "/plugin install codex@openai-codex",
    "/reload-plugins",
    "/codex:setup",
)
_TAREAS = ("/codex:rescue", "/codex:review", "/codex:adversarial-review")


def _P(fondo: str) -> dict:
    if fondo not in _FONDOS:
        raise ValueError(f"fondo {fondo!r} no existe")
    return TK.paleta("oscuro") if fondo == "oscuro" else C


def _svg(paths: str, px: int = 24, view: str = "0 0 24 24") -> str:
    return (f'<svg viewBox="{view}" width="{px}" height="{px}" fill="none" '
            f'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{paths}</svg>')


def _check(px: int = 24) -> str:
    return _svg('<path d="m5 12 4 4 10-10"/>', px)


def _cross(px: int = 24) -> str:
    return _svg('<path d="m6 6 12 12M18 6 6 18"/>', px)


def _question(px: int = 54) -> str:
    return _svg('<path d="M8 8a4.5 4.5 0 0 1 8 2.8c0 3.2-4 3.1-4 6.2M12 21h.01"/>', px)


def _logo(iid: str, slug: str, px: int) -> str:
    mapped = "openai" if slug in ("codex", "chatgpt") else slug
    mark, _ = logos.mark(mapped, px, uid=iid)
    return mark


def _suelo(cid: str, fondo: str) -> str:
    """Suelo de escena. Se estira 2400 px por lado: lo recorta el `.viz` del host
    (overflow:hidden), así cubre la banda entera en partida y el lienzo en grafico."""
    P = _P(fondo)
    if fondo == "claro":
        return ""
    if fondo == "oscuro":
        bg = (f"radial-gradient(120% 90% at 50% 28%,{P['bg2']} 0%,"
              f"{P['bg']} 62%,{P['bg_edge']} 100%),"
              f"linear-gradient({rgba(P['text'], .022)} 1px,transparent 1px),"
              f"linear-gradient(90deg,{rgba(P['text'], .022)} 1px,transparent 1px)")
        return (f'<span class="cx-ground" id="{cid}-ground" '
                f'style="background:{bg};background-size:auto,72px 72px,72px 72px"></span>')
    bg = (f"radial-gradient({rgba(P['text'], .16)} 22%,transparent 24%),"
          f"linear-gradient({P['accent']},{P['accent']})")
    return (f'<span class="cx-ground" id="{cid}-ground" '
            f'style="background:{bg};background-size:16px 16px,auto"></span>')


def _terminal(cid: str, w: int, h: int, P: dict, logo_at=None, body: str = "") -> str:
    del P, logo_at
    cc = TK.BRANDS["claudecode"]
    star = _svg('<path d="M12 3v18M3 12h18M5.6 5.6l12.8 12.8M18.4 5.6 5.6 18.4"/>', 25)
    return (f'<div class="cx-terminal" id="{cid}-terminal" style="width:{w}px;height:{h}px">'
            f'<div class="cx-tbar"><span class="cx-lights"><i></i><i></i><i></i></span>'
            f'<span class="cx-ttitle">claude</span></div>'
            f'<div class="cx-chead"><span class="cx-head-logo" id="{cid}-head-logo"></span>'
            f'<span class="cx-star" style="color:{cc["accent"]}">{star}</span>'
            f'<span>Claude Code</span></div>'
            f'<div class="cx-body" id="{cid}-body">{body}</div>'
            f'<div class="cx-input"><span>&gt;</span><i class="cx-caret"></i></div>'
            f'<div class="cx-plugins"><span class="cx-slot" id="{cid}-plugin-slot"></span></div>'
            f'</div>')


def _personaje(iid: str, quien: str, poses, px: int) -> str:
    if quien not in _POSES:
        raise ValueError(f"personaje {quien!r} no existe")
    if isinstance(poses, str):
        poses = (poses,)
    if not poses or any(p not in _POSES[quien] for p in poses):
        raise ValueError(f"pose de {quien!r} no existe: {poses!r}")
    imgs = []
    for i, pose in enumerate(poses):
        path = _personaje_path(quien, pose)
        imgs.append(f'<img id="{iid}-{pose}" src="{path}" alt="" '
                    f'style="opacity:{1 if i == 0 else 0}"/>')
    return (f'<span class="cx-person" id="{iid}" style="height:{px}px;width:{px}px">'
            f'{"".join(imgs)}</span>')


def _personaje_path(quien: str, pose: str) -> str:
    if quien not in _POSES or pose not in _POSES[quien]:
        raise ValueError(f"pose {quien!r}-{pose!r} no existe")
    carpeta = "personajes-9" if quien == "cangrejo" and pose in _POSES_9 else "personajes-8"
    return f"{carpeta}/{quien}-{pose}.png"


def _tablero(iid: str, P: dict) -> str:
    rows = "".join(
        f'<span class="cx-plan-row"><i></i><b id="{iid}-bar{i}"></b></span>'
        for i in range(3))
    return (f'<span class="cx-plan" id="{iid}" style="background:{P["surface"]};'
            f'border-color:{P["line"]}">{rows}</span>')


def _bloque(iid: str, P: dict) -> str:
    top = mix(P["accent"], P["surface"], .35)
    side = mix(P["accent"], P["text"], .25)
    return (f'<span class="cx-block" id="{iid}">'
            f'<i class="cx-block-top" id="{iid}-top" style="background:{top}"></i>'
            f'<i class="cx-block-side" id="{iid}-side" style="background:{side}"></i>'
            f'<i class="cx-block-half cx-block-left" id="{iid}-izq" style="background:{P["accent"]}"></i>'
            f'<i class="cx-block-half cx-block-right" id="{iid}-der" style="background:{P["accent"]}"></i>'
            f'<i class="cx-joint" id="{iid}-junta" style="background:{P["text"]}"></i>'
            f'</span>')


def _mosaico(iid: str, slug: str, P: dict, px: int = 150) -> str:
    if slug not in ("claude", "openai", "codex", "chatgpt", "fusionado",
                    "davinciresolve", "modelcontextprotocol",
                    "adobepremierepro", "higgsfield"):
        raise ValueError(f"mosaico {slug!r} no existe")
    if slug == "fusionado":
        return (f'<span class="cx-mosaic cx-fused" id="{iid}" style="width:{px}px;height:{px}px">'
                f'<i id="{iid}-a" style="background:{P["surface"]}">{_logo(f"{iid}-claude", "claude", round(px*.42))}</i>'
                f'<i id="{iid}-b" style="background:{P["text"]};color:{P["bg"]}">{_logo(f"{iid}-openai", "openai", round(px*.42))}</i></span>')
    return (f'<span class="cx-mosaic" id="{iid}" style="width:{px}px;height:{px}px;'
            f'background:{P["surface2"]};border-color:{P["line"]}">'
            f'{_logo(f"{iid}-logo", slug, round(px*.54))}</span>')


def _comando(iid: str, texto: str, legible: bool = False, empty: bool = False) -> str:
    # Inter 700 ya está materializada por el proyecto y es una medición
    # conservadora para el peso 500 que se pinta en la terminal.
    size = 24 if not legible or text_px(texto, 24, 700) <= 840 else 22
    blurred = "" if empty else esc(texto)
    sharp = (f'<span class="cx-command-n" id="{iid}-n" '
             f'style="font-size:{size}px"></span>') if legible else ""
    return (f'<span class="cx-command" id="{iid}"><b>&gt;</b>'
            f'<span class="cx-command-b" id="{iid}-b">{blurred}</span>{sharp}</span>')


def _medidor(iid: str, P: dict, valor: int = 100) -> str:
    return (f'<span class="cx-meter" id="{iid}"><em style="color:{P["text2"]}">Uso</em>'
            f'<span class="cx-meter-track" style="background:{P["surface3"]}">'
            f'<i id="{iid}-fill" style="background:{P["accent"]};width:{valor}%"></i>'
            f'<b id="{iid}-n" style="color:{P["text"]}">{valor}%</b></span></span>')


def _barra_trabada(iid: str, P: dict, error: bool = True) -> str:
    err = ""
    if error:
        err = (f'<span class="cx-error" id="{iid}-err" style="background:currentColor;color:{P["alert"]}">'
               f'{_cross(42)}<i></i><i></i></span>')
    return (f'<span class="cx-stuck" id="{iid}" style="background:{P["surface3"]}">'
            f'<i id="{iid}-fill" style="background:currentColor;color:{P["accent"]};width:52%"></i>{err}</span>')


def _marcador(iid: str, P: dict, n: int = 2) -> str:
    cells = "".join(f'<span id="{iid}-cell{i}" style="border-color:currentColor">'
                    f'<svg viewBox="0 0 96 96"><path id="{iid}-x{i}a" d="M24 24 72 72"/>'
                    f'<path id="{iid}-x{i}b" d="M72 24 24 72"/></svg></span>' for i in range(n))
    return f'<span class="cx-score" id="{iid}" style="color:{P["text"]}">{cells}</span>'


def _css(p: str, P: dict) -> str:
    cc, mac = TK.BRANDS["claudecode"], TK.BRANDS["macos"]
    return f"""
{p} .cx-scene{{position:relative;width:980px;height:100%;max-height:1180px;display:flex;
  align-items:center;justify-content:center;font-family:{FONT};color:{P['text']}}}
{p} .cx-ground{{position:absolute;inset:-2400px;z-index:0}}
{p} .cx-layer{{position:relative;width:100%;height:100%;z-index:1;display:flex;align-items:center;justify-content:center}}
{p} .cx-terminal{{position:relative;box-sizing:border-box;overflow:hidden;background:{cc['bg']};
  border:1px solid {cc['line']};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};color:{cc['text']}}}
{p} .cx-tbar{{height:48px;display:flex;align-items:center;justify-content:center;background:{cc['surface']};border-bottom:1px solid {cc['line']}}}
{p} .cx-lights{{position:absolute;left:18px;display:flex;gap:9px}}{p} .cx-lights i{{width:13px;height:13px;border-radius:999px;background:{mac['close']}}}
{p} .cx-lights i:nth-child(2){{background:{mac['minimize']}}}{p} .cx-lights i:nth-child(3){{background:{mac['maximize']}}}
{p} .cx-ttitle{{font-family:{MONO};font-size:18px;color:{cc['text2']}}}
{p} .cx-chead{{height:70px;margin:18px 24px 0;border:2px solid {cc['accent']};border-radius:{RADIUS['md']}px;display:flex;align-items:center;justify-content:center;gap:12px;font-size:26px;font-weight:700}}
{p} .cx-head-logo{{width:32px;display:flex;align-items:center;justify-content:center}}{p} .cx-star{{display:flex}}
{p} .cx-body{{position:absolute;left:24px;right:24px;top:154px;bottom:150px;overflow:hidden}}
{p} .cx-input{{position:absolute;left:24px;right:24px;bottom:74px;height:56px;border:1px solid {cc['line']};border-radius:{RADIUS['md']}px;background:{cc['surface']};display:flex;align-items:center;padding:0 18px;gap:12px;font-family:{MONO};color:{cc['accent']}}}
{p} .cx-caret{{width:10px;height:25px;background:{cc['text']};animation:cxblink .8s steps(1,end) infinite}}@keyframes cxblink{{50%{{opacity:0}}}}
{p} .cx-plugins{{position:absolute;left:0;right:0;bottom:0;height:56px;background:{cc['surface']};border-top:1px solid {cc['line']};display:flex;align-items:center;padding:0 22px}}
{p} .cx-slot{{width:62px;height:38px;border:1px dashed {cc['line']};border-radius:{RADIUS['sm']}px;display:flex;align-items:center;justify-content:center}}
{p} .cx-person{{position:absolute;display:block;transform-origin:50% 100%}}{p} .cx-person img{{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;object-position:50% 100%}}
{p} .cx-plan{{width:220px;height:150px;border:1px solid;box-sizing:border-box;border-radius:{RADIUS['md']}px;box-shadow:{TK.SHADOW};display:flex;flex-direction:column;justify-content:center;gap:17px;padding:22px}}
{p} .cx-plan-row{{display:flex;align-items:center;gap:12px}}{p} .cx-plan-row i{{width:19px;height:19px;border:2px solid {P['text2']};border-radius:4px}}{p} .cx-plan-row b{{display:block;height:9px;border-radius:{RADIUS['pill']}px;background:{rgba(P['text2'], .30)};width:130px}}
{p} .cx-block{{position:relative;width:200px;height:170px;display:block;transform-origin:50% 100%}}{p} .cx-block-top{{position:absolute;left:0;top:0;width:160px;height:42px;transform:skewX(-38deg);transform-origin:0 100%}}
{p} .cx-block-side{{position:absolute;right:0;top:41px;width:40px;height:128px;clip-path:polygon(0 0,100% 0,100% 76%,0 100%)}}
{p} .cx-block-half{{position:absolute;top:41px;width:80px;height:128px}}{p} .cx-block-left{{left:0;transform-origin:100% 50%}}{p} .cx-block-right{{left:80px;transform-origin:0 50%}}
{p} .cx-joint{{position:absolute;left:78px;top:44px;width:4px;height:122px;opacity:0;z-index:4}}
{p} .cx-mosaic{{box-sizing:border-box;border:1px solid;border-radius:36px;box-shadow:{TK.SHADOW};display:flex;align-items:center;justify-content:center;overflow:hidden}}
{p} .cx-fused{{border:1px solid {P['line']}}}{p} .cx-fused>i{{width:50%;height:100%;display:flex;align-items:center;justify-content:center}}
{p} .cx-command{{position:relative;height:56px;display:flex;align-items:center;gap:12px;font-family:{MONO};font-size:24px;color:{cc['text']};overflow:hidden}}
{p} .cx-command>b{{color:{cc['accent']}}}{p} .cx-command-b,{p} .cx-command-n{{position:absolute;left:30px;right:0;white-space:nowrap}}
{p} .cx-command-b{{filter:blur(7px);opacity:.85}}{p} .cx-command-n{{opacity:0}}
{p} .cx-meter{{position:relative;width:600px;height:92px;display:block}}{p} .cx-meter em{{position:absolute;top:0;left:0;font-family:{MONO};font-style:normal;font-size:19px}}
{p} .cx-meter-track{{position:absolute;left:0;right:0;bottom:0;height:44px;border-radius:{RADIUS['pill']}px;overflow:hidden}}{p} .cx-meter-track i{{position:absolute;inset:0 auto 0 0;transform-origin:0 50%}}
{p} .cx-meter-track b{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:800}}
{p} .cx-stuck{{position:relative;width:640px;height:36px;border-radius:{RADIUS['pill']}px;display:block}}{p} .cx-stuck>i{{position:absolute;left:0;top:0;height:100%;border-radius:{RADIUS['pill']}px}}
{p} .cx-error{{position:absolute;left:46%;top:-38px;width:180px;height:110px;border-radius:{RADIUS['md']}px;box-shadow:{TK.SHADOW};display:flex;align-items:center;justify-content:center;gap:10px}}
{p} .cx-error svg{{color:{P['bg']}}}{p} .cx-error i{{width:34px;height:8px;border-radius:{RADIUS['pill']}px;background:{P['bg']}}}
{p} .cx-score{{display:flex;gap:24px}}{p} .cx-score>span{{width:96px;height:96px;border:4px solid;border-radius:{RADIUS['md']}px;display:block}}{p} .cx-score svg{{width:100%;height:100%;fill:none;stroke:{P['alert']};stroke-width:9;stroke-linecap:round}}
{p} .cx-card{{box-sizing:border-box;border:1px solid {P['line']};border-radius:{RADIUS['md']}px;background:{P['surface']};box-shadow:{TK.SHADOW}}}
{p} .cx-row{{display:flex;align-items:center}}{p} .cx-hidden{{opacity:0}}
"""


def _wrap(cid: str, lienzo: bool, fondo: str, inner: str) -> tuple[str, str]:
    P = _P(fondo)
    p, _, max_h = _host(cid, lienzo)
    h = min(max_h, 1180 if lienzo else 760)
    css = _css(p, P) + f"\n{p} .cx-scene{{height:{h}px}}"
    html_ = (f'<div class="cx-scene" id="{cid}-scene">{_suelo(cid, fondo)}'
             f'<div class="cx-layer" id="{cid}-layer">{inner}</div></div>')
    return css, html_


def _encender(fn):
    """`html-on` sin interpolar: GSAP trata el innerHTML como cadena compleja y, con
    números dentro (los `d` de un SVG), escribía el marcado con todos los números en 0
    antes de su instante (`<path> attribute d: Expected number` en `check`). El marcado
    va al HTML dentro de su hueco, envuelto en un span a opacidad 0, y se enciende con
    `fade-to` en su palabra: seek-safe y sin interpolar cadenas."""
    import functools

    @functools.wraps(fn)
    def envuelta(*args, **kw):
        css, html_, anims = fn(*args, **kw)
        out = []
        for a in anims:
            if a[0] != "html-on":
                out.append(a)
                continue
            sel, t, markup = a[1], a[2], a[4]
            iid = sel.lstrip("#")
            hon = f"{iid}-hon"
            pat = re.compile(r'(id="' + re.escape(iid) + r'"[^>]*>)')
            if len(pat.findall(html_)) != 1:
                raise ValueError(f"html-on: el hueco #{iid} no está una sola vez en el html")
            html_ = pat.sub(lambda m: m.group(1) + f'<span class="cx-hon" id="{hon}" '
                            f'style="opacity:0">{markup}</span>', html_, count=1)
            out.append(("fade-to", f"#{hon}", t, .01, 1))
        if any(a[0] == "fade-to" and str(a[1]).endswith("-hon") for a in out):
            css += "\n.cx-hon{display:inline-flex;align-items:center;justify-content:center}"
        return css, html_, out
    return envuelta


def _logo_on(cid: str, target: str, slug: str, px: int, at: float) -> tuple:
    return ("html-on", f"#{target}", at, .01, _logo(f"{cid}-{slug}-{target}", slug, px))


def _pose(anims: list, iid: str, old: str, new: str, at: float) -> None:
    anims.extend([("fade-to", f"#{iid}-{old}", at, .01, 0),
                  ("fade-to", f"#{iid}-{new}", at, .01, 1)])


@_encender
def cc_gancho(cid: str, variant: str, at: list, lienzo: bool = False,
              fondo: str = "oscuro") -> tuple[str, str, list]:
    variants = {"piensa": 2, "ejecuta": 3, "fusion": 3, "casa": 2}
    if variant not in variants:
        raise ValueError(f"cc_gancho: variante {variant!r} no existe")
    _need_at("cc_gancho", at, variants[variant])
    P = _P(fondo)
    anims: list[tuple] = []
    if variant == "piensa":
        crab = _personaje(f"{cid}-crab", "cangrejo", "piensa", 190)
        plan = _tablero(f"{cid}-plan", P)
        thought = (f'<span class="cx-thought" id="{cid}-thought"><i></i><i></i>'
                   f'<b id="{cid}-cloud">{plan}</b></span>')
        body = f'<span class="cx-peek" id="{cid}-peek">{crab}</span>{thought}'
        term = _terminal(cid, 960, 700, P, logo_at=at[0], body=body)
        css, html_ = _wrap(cid, lienzo, fondo, term)
        css += f"""
.viz[data-viz-id="{cid}"] .cx-peek{{position:absolute;left:385px;bottom:-8px;width:190px;height:190px;overflow:hidden;opacity:0}}
.viz[data-viz-id="{cid}"] .cx-peek .cx-person{{inset:auto 0 0 0}}
.viz[data-viz-id="{cid}"] .cx-thought{{position:absolute;left:350px;top:10px;width:300px;height:250px;opacity:0}}
.viz[data-viz-id="{cid}"] .cx-thought>i{{position:absolute;border-radius:50%;background:{P['surface']};border:1px solid {P['line']}}}
.viz[data-viz-id="{cid}"] .cx-thought>i:nth-child(1){{left:58px;bottom:18px;width:24px;height:24px}}.viz[data-viz-id="{cid}"] .cx-thought>i:nth-child(2){{left:76px;bottom:43px;width:38px;height:38px}}
.viz[data-viz-id="{cid}"] .cx-thought>b{{position:absolute;inset:0 0 55px;border-radius:48%;background:{P['surface']};display:flex;align-items:center;justify-content:center;transform:scale(.82)}}
"""
        anims += [_logo_on(cid, f"{cid}-head-logo", "claude", 30, at[0]),
                  ("rise-in", f"#{cid}-peek", at[0], .28),
                  ("scale-pop", f"#{cid}-thought", at[1], .30)]
        anims += [("grow-x", f"#{cid}-plan-bar{i}", round(at[1]+i*.12, 4), .26, 130)
                  for i in range(3)]
        return css, html_, anims

    if variant == "ejecuta":
        plan = _tablero(f"{cid}-plan", P)
        block = _bloque(f"{cid}-block", P)
        crab = _personaje(f"{cid}-crab", "cangrejo", "piensa", 145)
        worker = _personaje(f"{cid}-worker", "obrero", ("caja-herramientas", "martillo"), 320)
        body = (f'<span class="cx-hook-plan" id="{cid}-plan-wrap">{plan}</span>'
                f'<span class="cx-hook-block" id="{cid}-block-wrap">{block}<i id="{cid}-block-glow"></i></span>'
                f'{crab}{worker}')
        term = _terminal(cid, 980, 1100, P, body=body)
        css, html_ = _wrap(cid, True, fondo, term)
        css += f"""
.viz[data-viz-id="{cid}"] .cx-hook-plan,.viz[data-viz-id="{cid}"] .cx-hook-block{{position:absolute;left:390px;bottom:150px}}
.viz[data-viz-id="{cid}"] .cx-hook-block{{opacity:0}}.viz[data-viz-id="{cid}"] #{cid}-block-glow{{position:absolute;inset:-18px;box-shadow:{TK.GLOW};opacity:0}}
.viz[data-viz-id="{cid}"] #{cid}-crab{{left:40px;top:20px}}.viz[data-viz-id="{cid}"] #{cid}-worker{{left:45px;bottom:70px;opacity:0}}
""".replace("#{cid}", f"#{cid}")
        anims += [("drop-in", f"#{cid}-plan-wrap", 0, .28),
                  ("glide-x", f"#{cid}-worker", at[0], .32)]
        _pose(anims, f"{cid}-worker", "caja-herramientas", "martillo", at[1])
        anims += [("punch", f"#{cid}-plan-wrap", at[1], .18),
                  ("fade-to", f"#{cid}-plan-wrap", at[1], .12, 0),
                  ("fade-to", f"#{cid}-block-wrap", at[1], .12, .55),
                  ("stamp", f"#{cid}-block-wrap", at[2], .22),
                  ("fade-to", f"#{cid}-block-glow", at[2], .18, 1)]
        return css, html_, anims

    if variant == "fusion":
        a = f'<span id="{cid}-ma-slot"></span>'
        b = f'<span id="{cid}-mb-slot"></span>'
        fused = (f'<span class="cx-mosaic cx-fused" id="{cid}-fused" '
                 f'style="width:150px;height:150px"><i id="{cid}-fused-a" '
                 f'style="background:{P["surface"]}"></i><i id="{cid}-fused-b" '
                 f'style="background:{P["text"]};color:{P["bg"]}"></i></span>')
        plug = _svg('<path d="M8 3v6m8-6v6M6 9h12v3a6 6 0 0 1-12 0Zm6 9v3"/>', 30)
        strip = (f'<span class="cx-terminal-strip" id="{cid}-strip"><span class="cx-slot" '
                 f'id="{cid}-strip-slot"></span></span>')
        inner = (f'<span class="cx-pair"><span class="cx-logo-slot" id="{cid}-ma">{a}</span>'
                 f'<span class="cx-logo-slot" id="{cid}-mb">{b}</span>'
                 f'<span class="cx-fusion" id="{cid}-fusion">{fused}<i>{plug}</i></span></span>{strip}')
        css, html_ = _wrap(cid, lienzo, fondo, inner)
        css += f"""
.viz[data-viz-id="{cid}"] .cx-pair{{position:absolute;left:190px;top:120px;width:600px;height:270px;display:flex;justify-content:space-between;align-items:center}}
.viz[data-viz-id="{cid}"] .cx-logo-slot{{width:150px;height:150px;display:flex;align-items:center;justify-content:center;opacity:0;background:{P['surface2']};border:1px solid {P['line']};border-radius:24%;box-shadow:{TK.SHADOW}}}
.viz[data-viz-id="{cid}"] .cx-fusion{{position:absolute;left:225px;top:35px;opacity:0;display:flex;flex-direction:column;align-items:center;gap:14px}}
.viz[data-viz-id="{cid}"] .cx-fusion>i{{width:58px;height:40px;border-radius:{RADIUS['pill']}px;background:{P['accent_soft']};color:{P['accent_hi']};display:flex;align-items:center;justify-content:center}}
.viz[data-viz-id="{cid}"] .cx-terminal-strip{{position:absolute;left:0;right:0;bottom:0;height:110px;background:{TK.BRANDS['claudecode']['bg']};border-top:1px solid {TK.BRANDS['claudecode']['line']};display:flex;align-items:flex-end;padding:0 30px 16px}}
"""
        anims += [_logo_on(cid, f"{cid}-ma-slot", "claude", 82, at[0]),
                  _logo_on(cid, f"{cid}-mb-slot", "codex", 82, at[0]),
                  ("glide-x", f"#{cid}-ma", at[0], .35),
                  ("glide-x", f"#{cid}-mb", at[0], .35),
                  ("fade-to", f"#{cid}-ma", at[1], .08, 0),
                  ("fade-to", f"#{cid}-mb", at[1], .08, 0),
                  _logo_on(cid, f"{cid}-fused-a", "claude", 64, at[1]),
                  _logo_on(cid, f"{cid}-fused-b", "codex", 64, at[1]),
                  ("stamp", f"#{cid}-fusion", at[1], .24),
                  ("cursor-to", f"#{cid}-fusion", at[2], .48, 0, 220)]
        return css, html_, anims

    fused = _mosaico(f"{cid}-home-plugin", "fusionado", P, 72)
    crab = _personaje(f"{cid}-crab", "cangrejo", "saluda", 260)
    worker = _personaje(f"{cid}-worker", "obrero", "caja-herramientas", 280)
    body = (f'<span class="cx-home-row cx-home-top" id="{cid}-home-top">{crab}</span>'
            f'<span class="cx-home-row cx-home-bottom" id="{cid}-home-bottom">{worker}</span>')
    term = _terminal(cid, 980, 1100, P, logo_at=at[1], body=body)
    term = term.replace(
        f'<span class="cx-slot" id="{cid}-plugin-slot"></span>',
        f'<span class="cx-slot cx-lit-slot" id="{cid}-plugin-slot">'
        f'{fused}<i class="cx-slot-glow" id="{cid}-home-glow"></i></span>')
    css, html_ = _wrap(cid, True, fondo, term)
    css += f"""
.viz[data-viz-id="{cid}"] .cx-terminal{{opacity:0}}.viz[data-viz-id="{cid}"] .cx-lit-slot{{position:relative;width:76px;height:48px;overflow:visible}}
.viz[data-viz-id="{cid}"] .cx-lit-slot>.cx-mosaic{{position:absolute;left:1px;bottom:0;opacity:0;z-index:2}}
.viz[data-viz-id="{cid}"] .cx-slot-glow{{position:absolute;left:-7px;bottom:-8px;width:88px;height:88px;box-shadow:{TK.GLOW};opacity:0;z-index:1}}
.viz[data-viz-id="{cid}"] .cx-home-row{{position:absolute;left:170px;right:170px;height:340px;display:flex;align-items:center;justify-content:center;opacity:0}}
.viz[data-viz-id="{cid}"] .cx-home-top{{top:0;border-bottom:1px solid {P['line']}}}.viz[data-viz-id="{cid}"] .cx-home-bottom{{bottom:0}}
"""
    anims += [("rise-in", f"#{cid}-terminal", at[0], .32),
              ("stamp", f"#{cid}-home-plugin", at[0], .20),
              _logo_on(cid, f"{cid}-head-logo", "claude", 30, at[1]),
              ("fade-to", f"#{cid}-home-glow", at[1], .18, 1),
              ("chip-in", f"#{cid}-home-top", at[1], .24),
              ("chip-in", f"#{cid}-home-bottom", round(at[1]+.15, 4), .24)]
    return css, html_, anims


@_encender
def plan_medidor(cid: str, variant: str, at: list, lienzo: bool = False,
                 fondo: str = "comic") -> tuple[str, str, list]:
    variants = {"vacia": 3, "calendario": 2}
    if variant not in variants:
        raise ValueError(f"plan_medidor: variante {variant!r} no existe")
    _need_at("plan_medidor", at, variants[variant])
    P = _P(fondo)
    anims: list[tuple] = []
    if variant == "vacia":
        meter = _medidor(f"{cid}-meter", P, 100)
        crab = _personaje(f"{cid}-crab", "cangrejo", "encogido", 170)
        card = (f'<span class="cx-card cx-plan-card" id="{cid}-card"><span id="{cid}-plan-name"></span>'
                f'<small id="{cid}-plan-price"></small><i id="{cid}-plan-logo"></i></span>')
        inner = f'<span class="cx-meter-wrap">{meter}{crab}</span>{card}'
        css, html_ = _wrap(cid, lienzo, fondo, inner)
        css += f"""
.viz[data-viz-id="{cid}"] .cx-meter-wrap{{position:absolute;top:150px;left:140px;width:700px;height:210px}}.viz[data-viz-id="{cid}"] #{cid}-crab{{right:-30px;bottom:-35px;opacity:0}}
.viz[data-viz-id="{cid}"] .cx-plan-card{{position:absolute;left:285px;top:410px;width:410px;height:170px;padding:28px 34px;opacity:0;display:flex;flex-direction:column;justify-content:center}}
.viz[data-viz-id="{cid}"] .cx-plan-card>span{{font-size:34px;font-weight:800}}.viz[data-viz-id="{cid}"] .cx-plan-card small{{font-size:26px;color:{P['text2']}}}.viz[data-viz-id="{cid}"] .cx-plan-card>i{{position:absolute;right:28px;top:60px}}
"""
        anims += [("grow-x", f"#{cid}-meter-fill", at[0], 1.0, 108),
                  ("count-roll", f"#{cid}-meter-n", at[0], 1.0, 100, 18, "", "%"),
                  ("rise-in", f"#{cid}-card", at[1], .24),
                  ("type-word", f"#{cid}-plan-name", at[1], .34, "Plan Pro"),
                  ("type-word", f"#{cid}-plan-price", at[1], .40, "20 US$/mes"),
                  _logo_on(cid, f"{cid}-plan-logo", "claude", 40, at[2]),
                  ("chip-in", f"#{cid}-crab", at[2], .22),
                  ("punch", f"#{cid}-crab-encogido", at[2], .20)]
        return css, html_, anims

    meter = _medidor(f"{cid}-meter", P, 18)
    leaves = "".join(f'<i id="{cid}-leaf{i}"></i>' for i in range(3))
    dust = "".join(f'<i id="{cid}-dust{i}" style="left:{255+i*18}px"></i>' for i in range(8))
    inner = (f'<span class="cx-calendar cx-card"><span class="cx-rings"></span>'
             f'<b id="{cid}-day">1</b><i class="cx-day-ring" id="{cid}-day-ring"></i>{leaves}</span>'
             f'<span class="cx-cal-meter">{meter}{dust}</span>')
    css, html_ = _wrap(cid, True, fondo, inner)
    css += f"""
.viz[data-viz-id="{cid}"] .cx-calendar{{position:absolute;top:90px;width:420px;height:480px;display:flex;align-items:center;justify-content:center;border-top:78px solid {P['accent']}}}.viz[data-viz-id="{cid}"] .cx-calendar>b{{font-size:220px;font-weight:900}}
.viz[data-viz-id="{cid}"] .cx-calendar>i:not(.cx-day-ring){{position:absolute;inset:0;background:{P['surface']};border:1px solid {P['line']};opacity:.9}}
.viz[data-viz-id="{cid}"] .cx-day-ring{{position:absolute;width:260px;height:260px;border:8px solid {P['alert']};border-radius:50%;opacity:0}}
.viz[data-viz-id="{cid}"] .cx-cal-meter{{position:absolute;top:650px;width:600px;height:150px}}.viz[data-viz-id="{cid}"] .cx-cal-meter>.cx-meter{{position:absolute;inset:0}}
.viz[data-viz-id="{cid}"] .cx-cal-meter>i{{position:absolute;bottom:35px;width:12px;height:12px;border-radius:3px;background:{P['text2']};opacity:0}}
"""
    anims += [("count-roll", f"#{cid}-day", at[0], .85, 1, 15, "")]
    for i in range(3):
        t = round(at[0] + i*.18, 4)
        anims += [("rot-to", f"#{cid}-leaf{i}", t, .34, 18+i*17),
                  ("cursor-to", f"#{cid}-leaf{i}", t, .34, 110+i*70, -80-i*25),
                  ("badge-out", f"#{cid}-leaf{i}", round(t+.2, 4), .12)]
    anims += [("stamp", f"#{cid}-day-ring", at[1], .22),
              ("grow-x", f"#{cid}-meter-fill", at[1], .26, 0),
              ("count-roll", f"#{cid}-meter-n", at[1], .26, 18, 0, "", "%")]
    for i in range(8):
        anims += [("chip-in", f"#{cid}-dust{i}", round(at[1]+i*.025, 4), .12),
                  ("cursor-to", f"#{cid}-dust{i}", round(at[1]+i*.025, 4), .28,
                   (i-3)*24, -35-abs(i-3)*9)]
    return css, html_, anims


def _cuenta(cid: str, named: bool = False) -> str:
    b = TK.BRANDS["chatgpt"]
    logo = _logo(f"{cid}-account-openai", "chatgpt", 48) if named else ""
    name = "ChatGPT" if named else ""
    return (f'<span class="cx-account" id="{cid}-account" style="background:{b["bg"]};border-color:{b["line"]};color:{b["text"]}">'
            f'<i class="cx-port" id="{cid}-port" style="border-color:{b["line"]}">'
            f'<b id="{cid}-port-ring"></b></i>'
            f'<i class="cx-avatar" style="background:{b["surface"]}"></i>'
            f'<span class="cx-account-logo" id="{cid}-account-logo">{logo}</span>'
            f'<b id="{cid}-account-name">{name}</b></span>')


def _checklist(cid: str, P: dict, checked: int = 0) -> str:
    labels = ("Plugin", "Comandos", "Codex", "Cuenta")
    return "".join(f'<span class="cx-check-row" id="{cid}-check{i}"><i id="{cid}-checkmark{i}">'
                   f'{_check(22) if i < checked else ""}</i><b>{lab}</b></span>'
                   for i, lab in enumerate(labels))


@_encender
def cuenta_chatgpt(cid: str, variant: str, at: list, lienzo: bool = True,
                   fondo: str = "claro") -> tuple[str, str, list]:
    variants = {"enchufe": 4, "conectada": 2}
    if variant not in variants:
        raise ValueError(f"cuenta_chatgpt: variante {variant!r} no existe")
    _need_at("cuenta_chatgpt", at, variants[variant])
    P = _P(fondo)
    worker_poses = ("camina", "caja-herramientas") if variant == "enchufe" else ("caja-herramientas",)
    worker = _personaje(f"{cid}-worker", "obrero", worker_poses, 290)
    anims: list[tuple] = []
    if variant == "enchufe":
        account = _cuenta(cid, False)
        block = _bloque(f"{cid}-block", P)
        inner = (f'{worker}<svg class="cx-cable" viewBox="0 0 980 1180"><path id="{cid}-cable-loose" d="M190 985 C250 1080 330 1090 390 1045"/>'
                 f'<path id="{cid}-cable" d="M190 985 C275 825 345 500 500 330"/>'
                 f'<path class="cx-cable-light" id="{cid}-cable-light" d="M190 985 C275 825 345 500 500 330"/></svg>'
                 f'{account}<span class="cx-power">{_medidor(f"{cid}-power", P, 0)}</span>'
                 f'<span class="cx-account-block">{block}<i id="{cid}-block-row"></i></span>')
        css, html_ = _wrap(cid, True, fondo, inner)
        css += _account_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] #{cid}-worker{{left:40px;bottom:70px;opacity:0}}.viz[data-viz-id="{cid}"] .cx-account{{right:40px;top:230px;opacity:0}}
.viz[data-viz-id="{cid}"] .cx-account-block{{position:absolute;right:80px;bottom:95px}}.viz[data-viz-id="{cid}"] #{cid}-block-row{{position:absolute;left:28px;bottom:45px;width:110px;height:10px;background:{P['text']};opacity:0}}
.viz[data-viz-id="{cid}"] .cx-power{{position:absolute;left:230px;bottom:95px;transform:scale(.55);transform-origin:0 100%}}
""".replace("#{cid}", f"#{cid}")
        anims += [("glide-x", f"#{cid}-worker", at[0], .32)]
        _pose(anims, f"{cid}-worker", "camina", "caja-herramientas", round(at[0]+.25, 4))
        anims += [("fade-to", f"#{cid}-cable-loose", at[1], .12, 0),
                  ("draw", f"#{cid}-cable", at[1], .48),
                  ("rise-in", f"#{cid}-account", at[2], .28),
                  ("click", f"#{cid}-port", at[2], .18, f"#{cid}-port-ring"),
                  _logo_on(cid, f"{cid}-account-logo", "chatgpt", 48, at[3]),
                  ("type-word", f"#{cid}-account-name", at[3], .36, "ChatGPT"),
                  ("draw", f"#{cid}-cable-light", at[3], .62),
                  ("grow-x", f"#{cid}-block-row", at[3], .35, 110)]
        return css, html_, anims

    account = _cuenta(cid, True)
    checklist = _checklist(cid, P, checked=3)
    badge = (f'<span class="cx-connected" id="{cid}-connected"><i style="background:{P["go"]}"></i><b>Conectado</b></span>')
    inner = (f'<span class="cx-small-checks">{checklist}<b id="{cid}-counter">3/4</b></span>'
             f'<span class="cx-account-wrap" id="{cid}-account-wrap">{account}{badge}<i id="{cid}-account-glow"></i></span>'
             f'{worker}<svg class="cx-cable" viewBox="0 0 980 720"><path class="cx-cable-light" id="{cid}-cable-light" d="M180 650 C350 590 480 520 590 430"/></svg>')
    css, html_ = _wrap(cid, True, fondo, inner)
    css += _account_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-small-checks{{position:absolute;left:42px;top:70px;width:380px}}.viz[data-viz-id="{cid}"] .cx-small-checks>#{cid}-counter{{position:absolute;left:300px;top:0;font:700 30px {MONO}}}
.viz[data-viz-id="{cid}"] .cx-account-wrap{{position:absolute;left:300px;top:360px;width:440px;height:260px}}.viz[data-viz-id="{cid}"] .cx-account-wrap>.cx-account{{left:0;top:0}}
.viz[data-viz-id="{cid}"] .cx-connected{{position:absolute;right:18px;bottom:6px;padding:9px 14px;border-radius:{RADIUS['pill']}px;background:{P['surface']};display:flex;gap:8px;align-items:center}}.viz[data-viz-id="{cid}"] .cx-connected i{{width:12px;height:12px;border-radius:50%}}
.viz[data-viz-id="{cid}"] #{cid}-account-glow{{position:absolute;inset:-18px;box-shadow:{TK.GLOW};opacity:0;z-index:-1}}.viz[data-viz-id="{cid}"] #{cid}-worker{{left:30px;bottom:30px}}
""".replace("#{cid}", f"#{cid}")
    anims += [("rot-to", f"#{cid}-checkmark3", 0, max(.2, at[0]), 720),
              ("html-on", f"#{cid}-checkmark3", at[0], .01, _check(22)),
              ("rise-in", f"#{cid}-account-wrap", at[1], .28),
              ("cursor-to", f"#{cid}-account-wrap", at[1], .28, 0, -40),
              ("fade-to", f"#{cid}-account-glow", at[1], .18, 1),
              ("draw", f"#{cid}-cable-light", at[1], .60),
              ("count-roll", f"#{cid}-counter", at[1], .34, 3, 4, "", "/4")]
    return css, html_, anims


def _account_css(cid: str, P: dict) -> str:
    b = TK.BRANDS["chatgpt"]
    p = f'.viz[data-viz-id="{cid}"]'
    return f"""
{p} .cx-account{{position:absolute;width:440px;height:200px;box-sizing:border-box;border:1px solid;border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};display:flex;align-items:center;padding:28px 32px;gap:16px}}
{p} .cx-avatar{{width:70px;height:70px;border-radius:50%}}{p} .cx-account-logo{{width:52px;height:52px;display:flex;align-items:center;justify-content:center}}{p} .cx-account>b{{font-size:31px}}
{p} .cx-port{{position:absolute;left:-14px;top:82px;width:26px;height:36px;border:4px solid;border-radius:8px}}{p} .cx-port>b{{position:absolute;inset:-14px;border:2px solid {b['text2']};border-radius:50%;opacity:0}}
{p} .cx-cable{{position:absolute;inset:0;width:980px;height:100%;fill:none;stroke:{P['text']};stroke-width:10;stroke-linecap:round;pointer-events:none}}{p} .cx-cable-light{{stroke:{P['accent_hi']};stroke-width:5}}
{p} .cx-check-row{{height:54px;display:flex;align-items:center;gap:14px;color:{P['text']}}}{p} .cx-check-row>i{{width:27px;height:27px;border:2px solid {P['line']};border-radius:50%;display:flex;align-items:center;justify-content:center}}{p} .cx-check-row>b{{font-size:25px;font-weight:600}}
"""


def _command_rows(cid: str, hechos: int, sharp: bool = False) -> str:
    rows = []
    for i, command in enumerate(_COMANDOS):
        filled = i < hechos
        cmd = _comando(f"{cid}-cmd{i}", command, legible=sharp, empty=not filled)
        check = _check(28) if filled else ""
        rows.append(f'<span class="cx-command-row" id="{cid}-row{i}" '
                    f'style="opacity:{1 if filled else 0}">{cmd}'
                    f'<i class="cx-row-check" id="{cid}-row-check{i}">{check}</i></span>')
    return "".join(rows)


def _terminal_commands(cid: str, P: dict, hechos: int, w: int, h: int,
                       sharp: bool = False, counter: bool = True) -> str:
    if isinstance(hechos, bool) or not isinstance(hechos, int) or not 0 <= hechos <= 4:
        raise ValueError("instalacion: hechos debe ser un entero entre 0 y 4")
    count = f'<b class="cx-command-count" id="{cid}-count">{hechos}/4</b>' if counter else ""
    body = f'{count}<span class="cx-command-list">{_command_rows(cid, hechos, sharp)}</span>'
    return _terminal(cid, w, h, P, body=body)


@_encender
def instalacion(cid: str, variant: str, at: list, lienzo: bool = False,
                fondo: str = "claro", hechos: int = 0) -> tuple[str, str, list]:
    variants = {"comandos": 3, "catalogo": 3, "plugin": 2,
                "recarga": 3, "chequeo": 3, "enfoque": 3}
    if variant not in variants:
        raise ValueError(f"instalacion: variante {variant!r} no existe")
    _need_at("instalacion", at, variants[variant])
    P = _P(fondo)
    if isinstance(hechos, bool) or not isinstance(hechos, int) or not 0 <= hechos <= 4:
        raise ValueError("instalacion: hechos debe ser un entero entre 0 y 4")
    anims: list[tuple] = []
    sharp = variant == "enfoque"
    counter = variant != "enfoque"
    tw, th = (980, 560) if variant in ("catalogo", "recarga") else (960, 700)
    term = _terminal_commands(cid, P, hechos, tw, th, sharp=sharp, counter=counter)

    if variant == "comandos":
        css, html_ = _wrap(cid, lienzo, fondo, term)
        css += _install_css(cid, P)
        anims.append(_logo_on(cid, f"{cid}-head-logo", "claude", 30, at[0]))
        for i in range(4):
            anims.append(("chip-in", f"#{cid}-row{i}", round(at[1]+i*.1, 4), .22))
        anims += [("caret-off", f"#{cid}-cmd0-b", at[2], .01, _COMANDOS[0]),
                  ("glide-x", f"#{cid}-cmd0-b", at[2], .28)]
        return css, html_, anims

    if variant == "catalogo":
        cells = []
        icon_names = ("desktop", "stack", "link", "gear", "doc", "repo", "code", "inspect")
        for i, name in enumerate(icon_names):
            content = _mosaico(f"{cid}-plugin", "fusionado", P, 92) if i == 2 else icons.icon(name, 48)
            cells.append(f'<span class="cx-shelf-cell" id="{cid}-cell{i}">{content}</span>')
        shelf = (f'<span class="cx-shelf cx-card" id="{cid}-shelf"><span class="cx-shelf-head">'
                 f'<i id="{cid}-shelf-logo"></i></span><span class="cx-shelf-grid">{"".join(cells)}</span></span>')
        inner = f'{shelf}<span class="cx-install-term">{term}</span>'
        css, html_ = _wrap(cid, True, fondo, inner)
        css += _install_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-shelf{{position:absolute;top:55px;width:940px;height:460px;opacity:0;padding:62px 28px 24px}}.viz[data-viz-id="{cid}"] .cx-shelf-head{{position:absolute;left:30px;right:30px;top:15px;height:42px;display:flex;align-items:center}}
.viz[data-viz-id="{cid}"] .cx-shelf-grid{{display:grid;grid-template-columns:repeat(4,1fr);grid-template-rows:repeat(2,1fr);gap:16px;height:100%}}
.viz[data-viz-id="{cid}"] .cx-shelf-cell{{border:1px solid {P['line']};border-radius:{RADIUS['md']}px;background:{P['surface2']};display:flex;align-items:center;justify-content:center;opacity:0;color:{P['text2']}}}
.viz[data-viz-id="{cid}"] .cx-shelf-cell .cx-mosaic{{border:0;box-shadow:none}}.viz[data-viz-id="{cid}"] .cx-install-term{{position:absolute;bottom:20px}}
"""
        anims += [("caret-off", f"#{cid}-cmd0-b", 0, .01, _COMANDOS[0]),
                  ("fade-to", f"#{cid}-row0", 0, .01, 1),
                  ("rise-bar", f"#{cid}-shelf", at[0], .34)]
        for i in range(8):
            anims.append(("chip-in", f"#{cid}-cell{i}", round(at[1]+i*.07, 4), .20))
        anims += [_logo_on(cid, f"{cid}-shelf-logo", "openai", 56, at[2]),
                  ("count-roll", f"#{cid}-count", at[2], .30, 0, 1, "", "/4"),
                  ("html-on", f"#{cid}-row-check0", at[2], .01, _check(28))]
        return css, html_, anims

    if variant == "plugin":
        landed = _mosaico(f"{cid}-landed", "fusionado", P, 72)
        shelf_cells = "".join(
            f'<span class="cx-mini-cell">{_mosaico(f"{cid}-fly", "fusionado", P, 72) if i == 2 else icons.icon(("desktop","stack","gear","doc")[i], 36)}</span>'
            for i in range(4))
        shelf = f'<span class="cx-mini-shelf cx-card" id="{cid}-shelf">{shelf_cells}</span>'
        term = term.replace(
            f'<span class="cx-slot" id="{cid}-plugin-slot"></span>',
            f'<span class="cx-slot cx-lit-slot" id="{cid}-plugin-slot">{landed}'
            f'<i class="cx-slot-glow" id="{cid}-landed-glow"></i></span>')
        inner = f'{shelf}<span class="cx-plugin-term">{term}</span>'
        css, html_ = _wrap(cid, lienzo, fondo, inner)
        css += _install_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-mini-shelf{{position:absolute;top:22px;width:720px;height:120px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:12px}}
.viz[data-viz-id="{cid}"] .cx-mini-cell{{display:flex;align-items:center;justify-content:center;border:1px solid {P['line']};border-radius:{RADIUS['sm']}px;color:{P['text2']}}}.viz[data-viz-id="{cid}"] .cx-plugin-term{{position:absolute;bottom:0}}
.viz[data-viz-id="{cid}"] #{cid}-fly{{position:relative}}.viz[data-viz-id="{cid}"] .cx-terminal #{cid}-plugin-slot{{box-shadow:none}}
.viz[data-viz-id="{cid}"] .cx-lit-slot{{position:relative;width:76px;height:48px;overflow:visible}}.viz[data-viz-id="{cid}"] .cx-lit-slot>.cx-mosaic{{position:absolute;left:1px;bottom:0;opacity:0;z-index:2}}
.viz[data-viz-id="{cid}"] .cx-slot-glow{{position:absolute;left:-7px;bottom:-8px;width:88px;height:88px;box-shadow:{TK.GLOW};opacity:0;z-index:1}}
""".replace("#{cid}", f"#{cid}")
        anims += [("caret-off", f"#{cid}-cmd1-b", at[0], .01, _COMANDOS[1]),
                  ("fade-to", f"#{cid}-row1", at[0], .01, 1),
                  ("cursor-to", f"#{cid}-fly", at[0], .30, 120, 170),
                  ("cursor-to", f"#{cid}-fly", round(at[0]+.30, 4), .30, 265, 390),
                  ("fade-to", f"#{cid}-fly", at[1], .01, 0),
                  ("stamp", f"#{cid}-landed", at[1], .20),
                  ("fade-to", f"#{cid}-landed-glow", at[1], .18, 1),
                  ("fade-to", f"#{cid}-shelf", at[1], .18, 0),
                  ("count-roll", f"#{cid}-count", at[1], .30, 1, 2, "", "/4"),
                  ("html-on", f"#{cid}-row-check1", at[1], .01, _check(28))]
        return css, html_, anims

    if variant == "recarga":
        menu_rows = "".join(
            f'<span class="cx-menu-row" id="{cid}-menu{i}"><i id="{cid}-menu-logo{i}"></i>'
            f'<b id="{cid}-menu-text{i}"></b><em></em></span>' for i in range(6))
        menu = f'<span class="cx-command-menu" id="{cid}-menu"><span id="{cid}-menu-roll">{menu_rows}</span></span>'
        inner = f'{menu}<span class="cx-reload-term">{term}</span>'
        css, html_ = _wrap(cid, True, fondo, inner)
        css += _install_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-command-menu{{position:absolute;top:70px;width:760px;height:390px;padding:18px;box-sizing:border-box;background:{TK.BRANDS['claudecode']['surface']};border:1px solid {TK.BRANDS['claudecode']['line']};border-radius:{RADIUS['lg']}px;overflow:hidden;color:{TK.BRANDS['claudecode']['text']}}}
.viz[data-viz-id="{cid}"] .cx-command-menu>span{{position:absolute;inset:18px}}.viz[data-viz-id="{cid}"] .cx-menu-row{{height:52px;display:flex;align-items:center;gap:13px;border-radius:{RADIUS['sm']}px;padding:0 14px}}
.viz[data-viz-id="{cid}"] .cx-menu-row>i{{width:28px}}.viz[data-viz-id="{cid}"] .cx-menu-row>b{{width:310px;filter:blur(7px);font:500 21px {MONO}}}.viz[data-viz-id="{cid}"] .cx-menu-row>em{{width:180px;height:8px;border-radius:{RADIUS['pill']}px;background:{rgba(TK.BRANDS['claudecode']['text2'], .30)}}}
.viz[data-viz-id="{cid}"] .cx-reload-term{{position:absolute;bottom:10px}}
"""
        anims += [("cursor-to", f"#{cid}-menu-roll", at[0], .30, 0, -250),
                  ("cursor-to", f"#{cid}-menu-roll", round(at[0]+.3, 4), .30, 0, 0),
                  ("caret-off", f"#{cid}-cmd2-b", at[0], .01, _COMANDOS[2]),
                  ("fade-to", f"#{cid}-row2", at[0], .01, 1)]
        for i, task in enumerate(_TAREAS):
            t = round(at[1]+i*.12, 4)
            anims += [_logo_on(cid, f"{cid}-menu-logo{i}", "openai", 24, t),
                      ("caret-off", f"#{cid}-menu-text{i}", t, .01, task),
                      ("chip-in", f"#{cid}-menu{i}", t, .20),
                      ("fade-to", f"#{cid}-menu{i}", at[2], .16, .78)]
        anims += [("count-roll", f"#{cid}-count", at[2], .30, 2, 3, "", "/4"),
                  ("html-on", f"#{cid}-row-check2", at[2], .01, _check(28))]
        return css, html_, anims

    if variant == "chequeo":
        checks = _checklist(f"{cid}-verify", P)
        panel = f'<span class="cx-verify cx-card" id="{cid}-verify">{checks}</span>'
        inner = f'<span class="cx-check-term">{term}</span>{panel}'
        css, html_ = _wrap(cid, lienzo, fondo, inner)
        css += _install_css(cid, P) + _account_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-check-term{{position:absolute;top:0}}.viz[data-viz-id="{cid}"] .cx-verify{{position:absolute;right:30px;bottom:15px;width:360px;height:245px;padding:18px 28px;opacity:0}}
.viz[data-viz-id="{cid}"] .cx-verify .cx-check-row>i{{color:{TK.BRANDS['claudecode']['ok']}}}
"""
        anims += [("caret-off", f"#{cid}-cmd3-b", at[0], .01, _COMANDOS[3]),
                  ("fade-to", f"#{cid}-row3", at[0], .01, 1),
                  ("drop-in", f"#{cid}-verify", at[0], .24),
                  ("html-on", f"#{cid}-verify-checkmark0", at[0], .01, _check(22)),
                  ("html-on", f"#{cid}-verify-checkmark1", at[1], .01, _check(22)),
                  ("html-on", f"#{cid}-verify-checkmark2", round(at[1]+.25, 4), .01, _check(22)),
                  ("rot-to", f"#{cid}-verify-checkmark3", at[2], max(.2, at[2]+.8), 720)]
        return css, html_, anims

    # enfoque
    css, html_ = _wrap(cid, lienzo, fondo, term)
    css += _install_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-focus-wave{{position:absolute;left:0;right:0;top:180px;height:90px;background:linear-gradient(180deg,transparent,{rgba(TK.BRANDS['claudecode']['accent'], .42)},transparent);pointer-events:none}}
"""
    wave = f'<span class="cx-focus-wave" id="{cid}-wave"></span>'
    html_ = html_.replace(f'</div></div>', f'{wave}</div></div>', 1)
    for i, command in enumerate(_COMANDOS):
        t0 = round(at[0]+i*.1, 4)
        tf = round(at[2]+i*.22, 4)
        anims += [("caret-off", f"#{cid}-cmd{i}-b", t0, .01, command),
                  ("chip-in", f"#{cid}-row{i}", t0, .20),
                  ("caret-off", f"#{cid}-cmd{i}-n", tf, .01, command),
                  ("fade-to", f"#{cid}-cmd{i}-b", tf, .12, 0),
                  ("fade-to", f"#{cid}-cmd{i}-n", tf, .12, 1)]
    anims.append(("cursor-to", f"#{cid}-wave", at[1], max(.25, at[2]-at[1]), 0, 310))
    return css, html_, anims


def _install_css(cid: str, P: dict) -> str:
    p = f'.viz[data-viz-id="{cid}"]'
    cc = TK.BRANDS["claudecode"]
    return f"""
{p} .cx-command-count{{position:absolute;right:10px;top:0;font:700 30px {MONO};z-index:3}}
{p} .cx-command-list{{position:absolute;left:0;right:0;top:44px;display:flex;flex-direction:column;gap:8px}}
{p} .cx-command-row{{position:relative;height:64px;border:1px dashed {cc['line']};border-radius:{RADIUS['sm']}px;padding:4px 48px 4px 14px;box-sizing:border-box;opacity:0}}
{p} .cx-row-check{{position:absolute;right:12px;top:17px;color:{cc['ok']};display:flex}}
"""


@_encender
def error_trabado(cid: str, variant: str, at: list, lienzo: bool = False,
                  fondo: str = "comic") -> tuple[str, str, list]:
    variants = {"traba": 3, "lampara": 3, "destraba": 2}
    if variant not in variants:
        raise ValueError(f"error_trabado: variante {variant!r} no existe")
    _need_at("error_trabado", at, variants[variant])
    P = _P(fondo)
    anims: list[tuple] = []
    if variant == "traba":
        bar = _barra_trabada(f"{cid}-bar", P, error=True)
        command = _comando(f"{cid}-rescue", _TAREAS[0], empty=True)
        term = _terminal(cid, 960, 280, P, body=command)
        inner = f'<span class="cx-traba-bar">{bar}</span><span class="cx-low-term">{term}</span>'
        css, html_ = _wrap(cid, lienzo, fondo, inner)
        css += _error_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-traba-bar{{position:absolute;top:130px}}.viz[data-viz-id="{cid}"] .cx-low-term{{position:absolute;bottom:10px}}
.viz[data-viz-id="{cid}"] .cx-low-term .cx-chead{{display:none}}.viz[data-viz-id="{cid}"] .cx-low-term .cx-body{{top:62px;bottom:94px}}
.viz[data-viz-id="{cid}"] #{cid}-bar-err{{opacity:0;top:-210px;left:46%}}
"""
        anims += [("caret-off", f"#{cid}-rescue-b", at[0], .01, _TAREAS[0]),
                  ("glide-x", f"#{cid}-rescue-b", at[0], .24),
                  ("drop-in", f"#{cid}-bar-err", at[1], .28),
                  ("cursor-to", f"#{cid}-bar-err", at[2], .34, 0, 172),
                  ("rot-to", f"#{cid}-bar-err", at[2], .34, -8),
                  ("jitter", f"#{cid}-bar", at[2], .40)]
        return css, html_, anims

    if variant == "lampara":
        worker = _personaje(f"{cid}-worker", "obrero", ("linterna", "martillo"), 330)
        rows = []
        for i in range(14):
            token = "at login()" if i == 8 else ""
            rows.append(f'<span class="cx-code-line" id="{cid}-code{i}"><b>{i+1:02d}</b>'
                        f'<i style="width:{260+(i*37)%250}px"></i><em>{token}</em></span>')
        trace = f'<span class="cx-trace cx-card" id="{cid}-trace"><span id="{cid}-trace-roll">{"".join(rows)}</span></span>'
        error = _barra_trabada(f"{cid}-mini", P, error=True)
        inner = (f'{worker}<span class="cx-beam" id="{cid}-beam"></span>{trace}'
                 f'<span class="cx-mini-progress" id="{cid}-mini-progress">{error}</span>')
        css, html_ = _wrap(cid, True, fondo, inner)
        css += _error_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] #{cid}-worker{{left:25px;bottom:115px}}.viz[data-viz-id="{cid}"] .cx-trace{{position:absolute;right:20px;top:55px;width:610px;height:820px;overflow:hidden;padding:20px}}
.viz[data-viz-id="{cid}"] .cx-trace>span{{position:absolute;inset:20px}}.viz[data-viz-id="{cid}"] .cx-code-line{{height:54px;display:flex;align-items:center;gap:14px;font-family:{MONO};opacity:.4}}
.viz[data-viz-id="{cid}"] .cx-code-line>b{{width:36px;color:{P['text2']}}}.viz[data-viz-id="{cid}"] .cx-code-line>i{{height:9px;border-radius:{RADIUS['pill']}px;background:{rgba(P['text2'], .30)}}}.viz[data-viz-id="{cid}"] .cx-code-line>em{{font-style:normal;color:{P['text2']};white-space:nowrap}}
.viz[data-viz-id="{cid}"] .cx-beam{{position:absolute;left:215px;top:250px;width:620px;height:290px;background:radial-gradient(ellipse at 0 50%,{rgba(P['accent_hi'], .35)},transparent 68%);clip-path:polygon(0 44%,100% 0,100% 100%,0 56%);opacity:0;z-index:4}}
.viz[data-viz-id="{cid}"] .cx-mini-progress{{position:absolute;right:35px;bottom:60px;transform:scale(.55);transform-origin:100% 100%}}.viz[data-viz-id="{cid}"] .cx-mini-progress .cx-error{{transform-origin:50% 50%}}
"""
        anims += [("cursor-to", f"#{cid}-trace-roll", 0, max(.8, at[2]+1), 0, -120),
                  ("fade-to", f"#{cid}-beam", at[0], .16, 1),
                  ("cursor-to", f"#{cid}-beam", at[0], max(.3, at[1]-at[0]), 0, 430)]
        for i in range(14):
            anims.append(("fade-to", f"#{cid}-code{i}", round(at[0]+i*.07, 4), .18, 1))
            if i != 8:
                anims.append(("fade-to", f"#{cid}-code{i}", at[1], .20, .25))
        anims += [("color-to", f"#{cid}-code8", at[1], .18, P["alert"])]
        _pose(anims, f"{cid}-worker", "linterna", "martillo", at[2])
        anims += [("flip-out", f"#{cid}-mini-err", at[2], .14),
                  ("flip-in", f"#{cid}-mini-err", round(at[2]+.14, 4), .18),
                  ("color-to", f"#{cid}-mini-err", round(at[2]+.14, 4), .12, P["go"]),
                  ("grow-x", f"#{cid}-mini-fill", at[2], .44, 640)]
        return css, html_, anims

    bar = _barra_trabada(f"{cid}-bar", P, error=True)
    worker = _personaje(f"{cid}-worker", "obrero", ("tira", "caja-herramientas"), 300)
    rope = f'<svg class="cx-rope" viewBox="0 0 980 500"><path d="M610 310 C720 280 760 230 800 210"/></svg>'
    inner = f'<span class="cx-destraba-bar">{bar}</span>{worker}{rope}'
    css, html_ = _wrap(cid, lienzo, fondo, inner)
    css += _error_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-destraba-bar{{position:absolute;left:55px;top:250px}}.viz[data-viz-id="{cid}"] #{cid}-worker{{right:10px;bottom:25px}}
.viz[data-viz-id="{cid}"] .cx-rope{{position:absolute;inset:0;width:980px;height:500px;fill:none;stroke:{P['text']};stroke-width:8;stroke-linecap:round}}
"""
    anims += [("jitter", f"#{cid}-bar", 0, max(.25, at[0])),
              ("cursor-to", f"#{cid}-bar-err", at[0], .48, 380, -50),
              ("rot-to", f"#{cid}-bar-err", at[0], .48, 160),
              ("grow-x", f"#{cid}-bar-fill", at[0], .48, 640),
              ("color-to", f"#{cid}-bar-fill", at[0], .24, P["go"]),
              ("cursor-to", f"#{cid}-bar-err", at[1], .26, 600, -120)]
    _pose(anims, f"{cid}-worker", "tira", "caja-herramientas", at[1])
    return css, html_, anims


def _error_css(cid: str, P: dict) -> str:
    return f"""
.viz[data-viz-id="{cid}"] .cx-error svg{{flex:none}}.viz[data-viz-id="{cid}"] .cx-mini-progress .cx-stuck{{width:640px}}
"""


def _diff_panel(cid: str, P: dict, rows: int, *, footer: bool = True) -> str:
    lines = []
    for i in range(rows):
        kind = "plus" if i % 5 in (1, 2) else "minus" if i % 7 == 0 else "plain"
        lines.append(f'<span class="cx-diff-line cx-{kind}" id="{cid}-diff{i}"><b>{i+1}</b>'
                     f'<i style="width:{250+(i*53)%430}px"></i></span>')
    foot = (f'<span class="cx-diff-foot"><b id="{cid}-modified">Modificados: 0</b>'
            f'<button id="{cid}-save">Guardar</button><i id="{cid}-lock"></i></span>') if footer else ""
    return (f'<span class="cx-diff cx-card" id="{cid}-diff"><span class="cx-file-tab">src/main.py</span>'
            f'<span class="cx-diff-roll" id="{cid}-diff-roll">{"".join(lines)}</span>'
            f'{foot}</span>')


@_encender
def revision_diff(cid: str, variant: str, at: list, lienzo: bool = False,
                  fondo: str = "claro") -> tuple[str, str, list]:
    variants = {"revisa": 4, "grandes": 2}
    if variant not in variants:
        raise ValueError(f"revision_diff: variante {variant!r} no existe")
    _need_at("revision_diff", at, variants[variant])
    P = _P(fondo)
    rows = 16 if variant == "revisa" else 40
    panel = _diff_panel(cid, P, rows, footer=variant == "revisa")
    anims: list[tuple] = []
    if variant == "revisa":
        glass = _svg('<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>', 120)
        notes = "".join(f'<span class="cx-note" id="{cid}-note{i}"><i></i><i></i></span>' for i in range(3))
        inner = f'{panel}<span class="cx-glass" id="{cid}-glass">{glass}</span>{notes}'
        css, html_ = _wrap(cid, lienzo, fondo, inner)
        css += _diff_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-diff{{width:900px;height:690px}}.viz[data-viz-id="{cid}"] .cx-glass{{position:absolute;left:70px;top:120px;color:{P['text']};opacity:0;z-index:4}}
.viz[data-viz-id="{cid}"] .cx-note{{position:absolute;right:20px;width:150px;height:70px;border-radius:{RADIUS['md']}px;background:{P['accent_soft']};opacity:0;z-index:5;padding:14px;box-sizing:border-box}}.viz[data-viz-id="{cid}"] .cx-note:nth-last-child(3){{top:210px}}.viz[data-viz-id="{cid}"] .cx-note:nth-last-child(2){{top:340px}}.viz[data-viz-id="{cid}"] .cx-note:nth-last-child(1){{top:470px}}
.viz[data-viz-id="{cid}"] .cx-note i{{display:block;width:100px;height:8px;margin:8px 0;border-radius:{RADIUS['pill']}px;background:{rgba(P['text2'], .30)}}}
"""
        anims += [("chip-in", f"#{cid}-glass", at[0], .24),
                  ("cursor-to", f"#{cid}-glass", at[0], max(.5, at[3]-at[0]), 0, 430)]
        for i in range(rows):
            anims.append(("fade-to", f"#{cid}-diff{i}", round(at[1]+i*.05, 4), .16, 1))
        for i in range(3):
            anims.append(("chip-in", f"#{cid}-note{i}", round(at[1]+i*.12, 4), .20))
        lock = _svg('<rect x="5" y="10" width="14" height="11" rx="3"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>', 34)
        anims += [("html-on", f"#{cid}-lock", at[2], .01, lock),
                  ("stamp", f"#{cid}-lock", at[2], .18),
                  ("fade-to", f"#{cid}-save", at[2], .16, .45),
                  ("jitter", f"#{cid}-modified", at[3], .40)]
        return css, html_, anims

    worker = _personaje(f"{cid}-worker", "obrero", "carga", 330)
    inner = (f'<span class="cx-big-count">archivos tocados <b id="{cid}-files">3</b></span>'
             f'{panel}{worker}')
    css, html_ = _wrap(cid, True, fondo, inner)
    css += _diff_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-diff{{position:absolute;left:0;top:120px;width:980px;height:1000px;overflow:hidden;padding:64px 20px 20px}}.viz[data-viz-id="{cid}"] .cx-diff-roll{{height:2320px}}
.viz[data-viz-id="{cid}"] .cx-diff-line{{height:58px}}.viz[data-viz-id="{cid}"] #{cid}-worker{{left:0;bottom:45px;opacity:0;z-index:5}}.viz[data-viz-id="{cid}"] .cx-big-count{{position:absolute;top:20px;right:20px;font-size:36px;font-weight:700;z-index:6}}.viz[data-viz-id="{cid}"] .cx-big-count b{{font-size:64px;font-weight:900}}
"""
    anims += [("cursor-to", f"#{cid}-diff-roll", at[0], max(.8, at[1]+1), 0, -1600),
              ("rise-in", f"#{cid}-worker", at[0], .28),
              ("count-roll", f"#{cid}-files", at[1], .65, 3, 148, "")]
    return css, html_, anims


def _diff_css(cid: str, P: dict) -> str:
    p = f'.viz[data-viz-id="{cid}"]'
    return f"""
{p} .cx-diff{{position:relative;overflow:hidden;padding:64px 20px 76px}}
{p} .cx-file-tab{{position:absolute;left:20px;top:16px;font:600 23px {MONO}}}
{p} .cx-diff-roll{{display:flex;flex-direction:column}}
{p} .cx-diff-line{{height:34px;display:flex;align-items:center;gap:14px;opacity:.72;font-family:{MONO}}}
{p} .cx-diff-line>b{{width:42px;text-align:right;color:{P['text2']}}}
{p} .cx-diff-line>i{{height:8px;border-radius:{RADIUS['pill']}px;background:{rgba(P['text2'], .32)}}}
{p} .cx-plus{{background:{rgba(P['go'], .16)}}}
{p} .cx-minus{{background:{rgba(P['alert'], .14)}}}
{p} .cx-diff-foot{{position:absolute;left:20px;right:20px;bottom:18px;height:46px;display:flex;align-items:center;justify-content:space-between}}
{p} .cx-diff-foot>b{{font-size:26px}}
{p} .cx-diff-foot button{{border:0;border-radius:{RADIUS['sm']}px;background:{P['accent']};color:{P['on_accent']};font:700 24px {FONT};padding:10px 22px}}
{p} .cx-diff-foot>i{{position:absolute;right:52px;display:flex;color:{P['text']}}}
"""


@_encender
def bloque_cuestiona(cid: str, at: list, lienzo: bool = True,
                     fondo: str = "claro") -> tuple[str, str, list]:
    _need_at("bloque_cuestiona", at, 2)
    P = _P(fondo)
    block = _bloque(f"{cid}-block", P)
    worker = _personaje(f"{cid}-worker", "obrero", ("camina", "martillo"), 320)
    qs = "".join(f'<span class="cx-q" id="{cid}-q{i}">{_question(62)}</span>' for i in range(3))
    inner = f'<span class="cx-question-block">{block}</span>{worker}{qs}'
    css, html_ = _wrap(cid, lienzo, fondo, inner)
    css += f"""
.viz[data-viz-id="{cid}"] .cx-question-block{{position:absolute;left:340px;top:390px;transform:scale(1.6)}}.viz[data-viz-id="{cid}"] #{cid}-worker{{left:650px;top:420px;z-index:1}}
.viz[data-viz-id="{cid}"] .cx-q{{position:absolute;color:{P['accent_hi']};opacity:0}}.viz[data-viz-id="{cid}"] #{cid}-q0{{left:245px;top:280px}}.viz[data-viz-id="{cid}"] #{cid}-q1{{right:210px;top:335px}}.viz[data-viz-id="{cid}"] #{cid}-q2{{left:470px;top:240px}}
"""
    anims: list[tuple] = [("cursor-to", f"#{cid}-worker", at[0], .45, -430, 30),
                          ("fade-to", f"#{cid}-worker", at[0], .01, .86),
                          ("cursor-to", f"#{cid}-worker", round(at[0]+.45, 4), .45, -90, 20),
                          ("fade-to", f"#{cid}-worker", round(at[0]+.45, 4), .01, 1)]
    for i in range(3):
        anims.append(("chip-in", f"#{cid}-q{i}", round(at[0]+.2+i*.26, 4), .18))
    _pose(anims, f"{cid}-worker", "camina", "martillo", at[1])
    anims += [("fade-to", f"#{cid}-block-junta", at[1], .12, 1),
              ("rot-to", f"#{cid}-block-izq", at[1], .24, -6),
              ("rot-to", f"#{cid}-block-der", at[1], .24, 6),
              ("cursor-to", f"#{cid}-block-izq", at[1], .24, -14, 0),
              ("cursor-to", f"#{cid}-block-der", at[1], .24, 14, 0)]
    return css, html_, anims


def _file(cid: str, P: dict, tab: str = "CLAUDE.md", tab_empty: bool = False) -> str:
    title = "" if tab_empty else esc(tab)
    return (f'<span class="cx-file cx-card" id="{cid}-file"><span class="cx-file-name" '
            f'id="{cid}-file-name">{title}</span><span class="cx-file-row" id="{cid}-file-row0">'
            f'<i id="{cid}-file-logo0"></i><span id="{cid}-file-content0"></span></span>'
            f'<span class="cx-file-row" id="{cid}-file-row1"><i id="{cid}-file-logo1"></i>'
            f'<span id="{cid}-file-content1"></span></span></span>')


@_encender
def claude_md(cid: str, variant: str, at: list, lienzo: bool = False,
              fondo: str = "claro") -> tuple[str, str, list]:
    variants = {"claude": 5, "codex": 2, "vuelve": 3, "reparto": 3}
    if variant not in variants:
        raise ValueError(f"claude_md: variante {variant!r} no existe")
    _need_at("claude_md", at, variants[variant])
    P = _P(fondo)
    file_html = _file(cid, P)
    anims: list[tuple] = []
    if variant == "claude":
        crab = _personaje(f"{cid}-crab", "cangrejo", ("saluda", "piensa", "sello", "lupa"), 260)
        plan = _tablero(f"{cid}-plan", P)
        opts = "".join(f'<span class="cx-option cx-card" id="{cid}-option{i}"><i></i><i></i></span>' for i in range(2))
        seal = f'<span class="cx-seal" id="{cid}-seal" style="background:{P["go"]};color:{P["bg"]}">{_check(46)}</span>'
        box = (f'<span class="cx-box" id="{cid}-box" style="background:{mix(P["accent"], P["warn"], .5)};border-color:{P["line"]}">'
               f'<i class="cx-box-flap" id="{cid}-box-lid"></i><b class="cx-box-tape"></b></span>')
        content = f'{crab}<span class="cx-md-plan" id="{cid}-plan-wrap">{plan}</span>{opts}{seal}{box}'
        file_html = file_html.replace(f'<span id="{cid}-file-content0"></span>',
                                      f'<span id="{cid}-file-content0">{content}</span>')
        css, html_ = _wrap(cid, True, fondo, file_html)
        css += _file_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-file{{width:940px;height:1030px}}.viz[data-viz-id="{cid}"] .cx-file-row:nth-child(3){{opacity:.35}}
.viz[data-viz-id="{cid}"] #{cid}-crab{{left:80px;bottom:15px;opacity:0}}.viz[data-viz-id="{cid}"] .cx-md-plan{{position:absolute;left:390px;top:110px;opacity:0}}
.viz[data-viz-id="{cid}"] .cx-option{{position:absolute;top:110px;width:175px;height:115px;opacity:0;padding:22px}}.viz[data-viz-id="{cid}"] #{cid}-option0{{left:375px}}.viz[data-viz-id="{cid}"] #{cid}-option1{{left:580px}}.viz[data-viz-id="{cid}"] .cx-option i{{display:block;height:9px;margin:10px;border-radius:{RADIUS['pill']}px;background:{rgba(P['text2'], .30)}}}
.viz[data-viz-id="{cid}"] .cx-seal{{position:absolute;left:630px;top:135px;width:72px;height:72px;border-radius:50%;display:flex;align-items:center;justify-content:center;opacity:0}}
.viz[data-viz-id="{cid}"] .cx-box{{position:absolute;left:440px;bottom:24px;width:230px;height:170px;border:2px solid;border-radius:{RADIUS['sm']}px;box-sizing:border-box;opacity:0;box-shadow:{TK.SHADOW}}}.viz[data-viz-id="{cid}"] .cx-box>i{{position:absolute;left:8px;top:-42px;width:210px;height:54px;background:{mix(P['accent'], P['warn'], .35)};border:2px solid {P['line']};border-radius:{RADIUS['sm']}px;box-sizing:border-box;transform-origin:0 100%}}.viz[data-viz-id="{cid}"] .cx-box>b{{position:absolute;left:98px;top:0;width:30px;height:166px;background:{rgba(P['surface'], .55)}}}
"""
        anims += [("chip-in", f"#{cid}-crab", at[0], .24),
                  _logo_on(cid, f"{cid}-file-logo0", "claude", 40, at[0])]
        _pose(anims, f"{cid}-crab", "saluda", "piensa", at[1])
        anims.append(("chip-in", f"#{cid}-plan-wrap", at[1], .22))
        anims += [("grow-x", f"#{cid}-plan-bar{i}", round(at[1]+i*.12, 4), .24, 130)
                  for i in range(3)]
        _pose(anims, f"{cid}-crab", "piensa", "sello", at[2])
        anims += [("chip-in", f"#{cid}-option0", at[2], .20),
                  ("chip-in", f"#{cid}-option1", round(at[2]+.1, 4), .20),
                  ("stamp", f"#{cid}-seal", at[2], .20),
                  ("fade-to", f"#{cid}-option0", at[2], .14, .4)]
        _pose(anims, f"{cid}-crab", "sello", "lupa", at[3])
        anims += [("glide-x", f"#{cid}-crab", at[3], .30),
                  ("rise-in", f"#{cid}-box", at[4], .28),
                  ("rot-to", f"#{cid}-box-lid", at[4], .24, -24)]
        return css, html_, anims

    if variant == "codex":
        crab = _personaje(f"{cid}-crab", "cangrejo", "saluda", 160)
        worker = _personaje(f"{cid}-worker", "obrero", "martillo", 230)
        bits = "".join(f'<i class="cx-bit" id="{cid}-bit{i}" style="background:{P["accent"]}"></i>' for i in range(4))
        file_html = file_html.replace(f'<span id="{cid}-file-content0"></span>', f'<span id="{cid}-file-content0">{crab}</span>')
        file_html = file_html.replace(f'<span id="{cid}-file-content1"></span>', f'<span id="{cid}-file-content1">{worker}{bits}</span>')
        css, html_ = _wrap(cid, lienzo, fondo, file_html)
        css += _file_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-file{{width:920px;height:650px}}.viz[data-viz-id="{cid}"] .cx-file-row:nth-child(2){{opacity:.35}}.viz[data-viz-id="{cid}"] #{cid}-crab{{left:95px;bottom:0}}
.viz[data-viz-id="{cid}"] #{cid}-worker{{left:430px;bottom:0;opacity:0}}.viz[data-viz-id="{cid}"] .cx-bit{{position:absolute;left:690px;width:90px;height:42px;border-radius:5px;opacity:0}}.viz[data-viz-id="{cid}"] #{cid}-bit0{{bottom:20px}}.viz[data-viz-id="{cid}"] #{cid}-bit1{{bottom:64px}}.viz[data-viz-id="{cid}"] #{cid}-bit2{{bottom:108px}}.viz[data-viz-id="{cid}"] #{cid}-bit3{{bottom:152px}}
"""
        anims += [("fade-to", f"#{cid}-file-row1", at[0], .18, 1),
                  _logo_on(cid, f"{cid}-file-logo1", "codex", 40, at[0]),
                  ("chip-in", f"#{cid}-worker", at[1], .22)]
        anims += [("drop-in", f"#{cid}-bit{i}", round(at[1]+i*.18, 4), .20) for i in range(4)]
        return css, html_, anims

    if variant == "vuelve":
        crab = _personaje(f"{cid}-crab", "cangrejo", ("lupa", "caja"), 220)
        worker = _personaje(f"{cid}-worker", "obrero", "caja-herramientas", 210)
        task = f'<span class="cx-task cx-card" id="{cid}-task"><i></i><i></i></span>'
        file_html = file_html.replace(f'<span id="{cid}-file-content0"></span>', f'<span id="{cid}-file-content0">{crab}</span>')
        file_html = file_html.replace(f'<span id="{cid}-file-content1"></span>', f'<span id="{cid}-file-content1">{worker}{task}</span>')
        css, html_ = _wrap(cid, lienzo, fondo, file_html)
        css += _file_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-file{{width:920px;height:670px}}.viz[data-viz-id="{cid}"] #{cid}-crab{{left:90px;bottom:0}}.viz[data-viz-id="{cid}"] #{cid}-worker{{left:520px;bottom:0}}
.viz[data-viz-id="{cid}"] .cx-task{{position:absolute;left:690px;bottom:75px;width:180px;height:100px;padding:22px}}.viz[data-viz-id="{cid}"] .cx-task i{{display:block;height:9px;margin:10px 0;border-radius:{RADIUS['pill']}px;background:{rgba(P['text2'], .30)}}}
"""
        anims += [("punch", f"#{cid}-task", at[0], .20),
                  ("cursor-to", f"#{cid}-task", at[1], .32, -120, -130),
                  ("cursor-to", f"#{cid}-task", round(at[1]+.32, 4), .32, -500, -270)]
        _pose(anims, f"{cid}-crab", "lupa", "caja", at[2])
        anims += [_logo_on(cid, f"{cid}-file-logo0", "claude", 40, at[2]),
                  ("punch", f"#{cid}-file-logo0", at[2], .18)]
        return css, html_, anims

    # reparto
    text1 = "Claude: planea, decide y revisa lo que vuelve."
    text2 = "Codex: construye, cambios grandes, destraba errores. 2 fallas → vuelve a Claude."
    block = (f'<span class="cx-share-block cx-card" id="{cid}-share"><span id="{cid}-share0"></span>'
             f'<span id="{cid}-share1"></span><button id="{cid}-copy">'
             f'<i id="{cid}-copy-ring"></i>{_svg("<rect x=\"7\" y=\"7\" width=\"12\" height=\"12\" rx=\"2\"/><path d=\"M5 16H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v1\"/>", 28)} Copiar</button></span>')
    empty = _file(f"{cid}-dest", P, tab_empty=True)
    empty = empty.replace(
        f'<span class="cx-file-name" id="{cid}-dest-file-name"></span>',
        f'<span class="cx-file-name" id="{cid}-dest-file-name"></span>'
        f'<i class="cx-file-ok" id="{cid}-dest-file-ok"></i>')
    copy = (f'<span class="cx-share-copy-travel" id="{cid}-share-copy-travel">'
            f'<span class="cx-share-copy cx-card" id="{cid}-share-copy">'
            f'<span id="{cid}-copy0"></span><span id="{cid}-copy1"></span></span></span>')
    inner = (f'<span class="cx-source-file">{file_html}</span>{block}{copy}'
             f'<span class="cx-dest-file" id="{cid}-dest-wrap">{empty}</span>')
    css, html_ = _wrap(cid, True, fondo, inner)
    css += _file_css(cid, P) + f"""
.viz[data-viz-id="{cid}"] .cx-source-file{{position:absolute;top:10px;width:940px;height:500px;display:block}}.viz[data-viz-id="{cid}"] .cx-source-file>.cx-file{{width:940px;height:500px;display:block}}
.viz[data-viz-id="{cid}"] .cx-share-block{{position:absolute;top:130px;width:880px;height:260px;padding:44px 150px 32px 34px;opacity:0;display:flex;flex-direction:column;gap:24px;font:500 22px {MONO};z-index:3}}.viz[data-viz-id="{cid}"] .cx-share-block button{{position:absolute;right:24px;top:100px;border:1px solid {P['line']};border-radius:{RADIUS['sm']}px;background:{P['surface2']};color:{P['text']};font:600 22px {FONT};padding:12px;display:flex;align-items:center;gap:8px}}
.viz[data-viz-id="{cid}"] .cx-share-block button>i{{position:absolute;inset:-10px;border:2px solid {P['accent']};border-radius:{RADIUS['md']}px;opacity:0}}
.viz[data-viz-id="{cid}"] .cx-share-copy-travel{{position:absolute;left:50px;top:300px;width:880px;height:230px;z-index:5}}.viz[data-viz-id="{cid}"] .cx-share-copy{{position:absolute;inset:0;padding:42px 34px;box-sizing:border-box;display:flex;flex-direction:column;gap:24px;font:500 22px {MONO};opacity:0}}
.viz[data-viz-id="{cid}"] .cx-dest-file{{position:absolute;top:590px;width:940px;height:560px;display:block;opacity:0}}.viz[data-viz-id="{cid}"] .cx-dest-file>.cx-file{{width:940px;height:560px;display:block}}.viz[data-viz-id="{cid}"] .cx-file-ok{{position:absolute;left:170px;top:14px;width:36px;height:36px;color:{P['go']};display:flex;align-items:center;justify-content:center}}
"""
    anims += [("chip-in", f"#{cid}-share", at[0], .24),
              ("type-word", f"#{cid}-share0", at[0], .52, text1),
              ("type-word", f"#{cid}-share1", at[0], .70, text2),
              ("click", f"#{cid}-copy", at[1], .20, f"#{cid}-copy-ring"),
              ("fade-to", f"#{cid}-dest-wrap", at[1], .18, 1),
              ("caret-off", f"#{cid}-copy0", at[1], .01, text1),
              ("caret-off", f"#{cid}-copy1", at[1], .01, text2),
              ("chip-in", f"#{cid}-share-copy", at[1], .18),
              ("cursor-to", f"#{cid}-share-copy-travel", at[1], .42, 0, 360),
              ("type-word", f"#{cid}-dest-file-name", at[2], .36, "CLAUDE.md"),
              ("html-on", f"#{cid}-dest-file-ok", at[2], .01, _check(32))]
    return css, html_, anims


def _file_css(cid: str, P: dict) -> str:
    p = f'.viz[data-viz-id="{cid}"]'
    return f"""
{p} .cx-file{{position:relative;overflow:hidden;padding-top:58px}}{p} .cx-file-name{{position:absolute;left:24px;top:16px;font:600 24px {FONT}}}
{p} .cx-file-row{{position:relative;height:50%;box-sizing:border-box;border-top:1px solid {P['line']};display:block;overflow:hidden}}{p} .cx-file-row>i{{position:absolute;left:26px;top:26px;width:44px;height:44px;display:flex;align-items:center;justify-content:center}}{p} .cx-file-row>span{{position:absolute;inset:0}}
"""


@_encender
def marcador_fallas(cid: str, at: list, lienzo: bool = True,
                    fondo: str = "comic") -> tuple[str, str, list]:
    _need_at("marcador_fallas", at, 3)
    P = _P(fondo)
    block = _bloque(f"{cid}-block", P)
    worker = _personaje(f"{cid}-worker", "obrero", "martillo", 310)
    score = _marcador(f"{cid}-score", P, 2)
    inner = (f'<span class="cx-collapse" id="{cid}-collapse">{block}'
             f'<i class="cx-piece" id="{cid}-piece0"></i><i class="cx-piece" id="{cid}-piece1"></i>'
             f'<i class="cx-piece" id="{cid}-piece2"></i><i class="cx-piece" id="{cid}-piece3"></i></span>'
             f'{worker}{score}')
    css, html_ = _wrap(cid, lienzo, fondo, inner)
    css += f"""
.viz[data-viz-id="{cid}"] .cx-collapse{{position:absolute;left:120px;top:440px}}.viz[data-viz-id="{cid}"] #{cid}-worker{{left:350px;top:380px}}.viz[data-viz-id="{cid}"] .cx-score{{position:absolute;right:80px;top:490px}}
.viz[data-viz-id="{cid}"] .cx-piece{{position:absolute;width:82px;height:62px;background:{P['accent']};opacity:0}}.viz[data-viz-id="{cid}"] #{cid}-piece0{{left:0;top:42px}}.viz[data-viz-id="{cid}"] #{cid}-piece1{{left:82px;top:42px}}.viz[data-viz-id="{cid}"] #{cid}-piece2{{left:0;top:105px}}.viz[data-viz-id="{cid}"] #{cid}-piece3{{left:82px;top:105px}}
"""
    anims: list[tuple] = []
    for fall_i, t in enumerate((at[0], at[1])):
        for i in range(4):
            tt = round(t+i*.035, 4)
            anims += [("fade-to", f"#{cid}-piece{i}", tt, .01, 1),
                      ("cursor-to", f"#{cid}-piece{i}", tt, .30, (i%2)*16-8, 120+(i//2)*24),
                      ("rot-to", f"#{cid}-piece{i}", tt, .30, (-24, 18, -37, 31)[i]),
                      ("cursor-to", f"#{cid}-piece{i}", round(t+.45, 4), .28, 0, 0),
                      ("rot-to", f"#{cid}-piece{i}", round(t+.45, 4), .28, 0)]
        anims += [("fade-to", f"#{cid}-block", t, .01, 0),
                  ("fade-to", f"#{cid}-block", round(t+.45, 4), .12, 1),
                  ("draw", f"#{cid}-score-x{fall_i}a", t, .24),
                  ("draw", f"#{cid}-score-x{fall_i}b", round(t+.08, 4), .24)]
    anims += [("punch", f"#{cid}-score-cell0", at[2], .18),
              ("punch", f"#{cid}-score-cell1", at[2], .18),
              ("color-to", f"#{cid}-score", at[2], .16, P["alert"])]
    return css, html_, anims


def assets_de(fn_name: str, kw: dict) -> list[str]:
    """Rutas relativas a ``assets/`` que la llamada va a referenciar."""
    variant = kw.get("variant")
    table = {
        "cc_gancho": {
            "piensa": (("cangrejo", "piensa"),),
            "ejecuta": (("cangrejo", "piensa"), ("obrero", "caja-herramientas"), ("obrero", "martillo")),
            "fusion": (),
            "casa": (("cangrejo", "saluda"), ("obrero", "caja-herramientas")),
        },
        "plan_medidor": {
            "vacia": (("cangrejo", "encogido"),), "calendario": (),
        },
        "cuenta_chatgpt": {
            "enchufe": (("obrero", "camina"), ("obrero", "caja-herramientas")),
            "conectada": (("obrero", "caja-herramientas"),),
        },
        "instalacion": {v: () for v in ("comandos", "catalogo", "plugin", "recarga", "chequeo", "enfoque")},
        "error_trabado": {
            "traba": (), "lampara": (("obrero", "linterna"), ("obrero", "martillo")),
            "destraba": (("obrero", "tira"), ("obrero", "caja-herramientas")),
        },
        "revision_diff": {"revisa": (), "grandes": (("obrero", "carga"),)},
        "claude_md": {
            "claude": (("cangrejo", "saluda"), ("cangrejo", "piensa"),
                       ("cangrejo", "sello"), ("cangrejo", "lupa")),
            "codex": (("cangrejo", "saluda"), ("obrero", "martillo")),
            "vuelve": (("cangrejo", "lupa"), ("cangrejo", "caja"),
                       ("obrero", "caja-herramientas")),
            "reparto": (),
        },
    }
    no_variant = {
        "bloque_cuestiona": (("obrero", "camina"), ("obrero", "martillo")),
        "marcador_fallas": (("obrero", "martillo"),),
    }
    if fn_name in no_variant:
        pairs = no_variant[fn_name]
    elif fn_name in table:
        if variant not in table[fn_name]:
            raise ValueError(f"assets_de: variante {variant!r} no existe para {fn_name}")
        pairs = table[fn_name][variant]
    else:
        raise ValueError(f"assets_de: componente {fn_name!r} no existe")
    out = []
    for quien, pose in pairs:
        if quien not in _POSES or pose not in _POSES[quien]:
            raise ValueError(f"assets_de: pose {quien}-{pose} no existe")
        out.append(_personaje_path(quien, pose))
    return list(dict.fromkeys(out))
