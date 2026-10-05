#!/usr/bin/env python3
"""Mockups de la pieza 4: Instagram, monigotes y Claude.

Todos los componentes respetan el contrato de :mod:`mockups`: devuelven
``(css, html, anims)``, prefijan su CSS con el host y dejan los selectores de
animación relativos.  Las primitivas de este archivo son deliberadamente
compartidas: la miniatura, el avatar y el monigote tienen que rimar a lo largo
de toda la pieza.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import icons
import logos
import tokens as TK
from mockups import BOARD_W, _cursor, _cursor_css, text_px
from tokens import C, FONT, MONO, RADIUS, accent_a, esc, ink_a, mix, rgba, shade_a


_VISTAS = ("2,4 M", "1,8 M", "1,1 M", "640 K", "410 K",
           "320 K", "250 K", "190 K", "120 K")


def _need_at(name: str, at: list, n: int) -> None:
    if not isinstance(at, (list, tuple)) or len(at) != n:
        got = len(at) if isinstance(at, (list, tuple)) else type(at).__name__
        raise ValueError(f"{name}: at debe tener {n} tiempos; recibió {got}")


def _host(cid: str, lienzo: bool) -> tuple[str, int, int]:
    """Selector y caja máxima de las dos geometrías del formato."""
    return f'.viz[data-viz-id="{cid}"]', BOARD_W, 1180 if lienzo else 760


def _tone(n: int) -> str:
    tones = (C["surface2"], C["accent_soft"], mix(C["surface"], C["accent"], .35),
             mix(C["surface2"], C["text"], .08), mix(C["surface"], C["go"], .18))
    return tones[n % len(tones)]


_GLYPHS = {
    "heart": '<path d="M12 20.2 4.2 12.8C-.8 7.7 6.4 1.6 12 7.3c5.6-5.7 12.8.4 7.8 5.5Z"/>',
    "heart-fill": '<path d="M12 20.2 4.2 12.8C-.8 7.7 6.4 1.6 12 7.3c5.6-5.7 12.8.4 7.8 5.5Z" fill="currentColor" stroke="none"/>',
    "comment": '<path d="M20.4 11.4a8.2 8.2 0 0 1-9 8.1 9.6 9.6 0 0 1-3.4-1.1l-4.3 1.1 1.2-4a8.2 8.2 0 1 1 15.5-4.1Z"/>',
    "share": '<path d="m3 10.7 18-7-7 18-3.1-7.6Z"/><path d="m10.9 14.1 4.7-5.4"/>',
    "bookmark": '<path d="M6.1 3.2h11.8v17.6L12 16.9l-5.9 3.9Z"/>',
    "bookmark-fill": '<path d="M6.1 3.2h11.8v17.6L12 16.9l-5.9 3.9Z" fill="currentColor" stroke="none"/>',
    "grid": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
    "reels": '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="m4 9 4-5m3 5 4-5m3 5 3-4"/><path d="m10 12 5 3-5 3Z"/>',
    "play": '<path d="m8.2 5.4 10 6.6-10 6.6Z" fill="currentColor" stroke="none"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.4 15.4 5 5"/>',
    "dm": '<path d="m3 10.7 18-7-7 18-3.1-7.6Z"/><path d="m10.9 14.1 4.7-5.4"/>',
    "pause": '<path d="M8 5v14M16 5v14"/>',
    "sort": '<path d="M4 7h16M7 12h10M10 17h4"/>',
    "pin": '<path d="m8 3 8 2-1.7 5.1 3.2 3.2-5.2 1.4L9 21l.3-6.9-4.8-3.7 4.8-1.2Z"/>',
}


def _glifo(nombre: str, px: int) -> str:
    if nombre == "knot":
        return icons.icon("knot", px)
    if nombre not in _GLYPHS:
        raise ValueError(f"glifo {nombre!r} no existe")
    fill = "none" if "fill=" not in _GLYPHS[nombre] else "none"
    return (f'<svg viewBox="0 0 24 24" width="{px}" height="{px}" '
            f'fill="{fill}" stroke="currentColor" stroke-width="1.9" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'{_GLYPHS[nombre]}</svg>')


def _miniatura(iid: str, n: int, vistas: str | None = None,
               avatar: str | None = None, w: int = 120) -> str:
    h = round(w * 16 / 9)
    bust = (f'<svg class="rm-bust" viewBox="0 0 100 150" aria-hidden="true">'
            f'<circle cx="50" cy="48" r="24" fill="{ink_a(.18)}"/>'
            f'<path d="M10 144c3-43 24-66 40-66s37 23 40 66Z" fill="{ink_a(.18)}"/>'
            f'</svg>')
    views = ""
    if vistas is not None:
        views = (f'<span class="rm-views" id="{iid}-v">{_glifo("play", 18)}'
                 f'<span>{esc(vistas)}</span></span>')
    portrait = _avatar(f"{iid}-avatar", avatar, n, max(34, w // 2)) if avatar else bust
    return (f'<div class="rm-thumb" id="{iid}" style="width:{w}px;height:{h}px;'
            f'background:{_tone(n)}">{portrait}<span class="rm-reels">'
            f'{_glifo("reels", max(18, w // 6))}</span>{views}</div>')


@lru_cache(maxsize=1)
def _avatar_data() -> str:
    root = Path(__file__).resolve().parents[4]
    raw = (root / "assets" / "avatar-propio.jpg").read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")


def _avatar(iid: str, quien: str, n: int = 0, px: int = 84) -> str:
    if quien not in ("propio", "ref"):
        raise ValueError(f"avatar: quien {quien!r} no existe")
    if quien == "propio":
        body = f'<img src="{_avatar_data()}" alt=""/>'
        cls = " own"
    else:
        body = (f'<span class="ra-ref" style="background:{_tone(n)}">'
                f'<svg viewBox="0 0 100 100" aria-hidden="true">'
                f'<circle cx="50" cy="36" r="20" fill="{ink_a(.30)}"/>'
                f'<path d="M12 96c4-31 20-46 38-46s34 15 38 46Z" fill="{ink_a(.30)}"/>'
                f'</svg></span>')
        cls = ""
    return (f'<span class="ra-avatar{cls}" id="{iid}" '
            f'style="width:{px}px;height:{px}px">{body}</span>')


def _monigote(iid: str, pose: str) -> str:
    if pose not in ("tableta", "timeline", "mira", "cuaderno"):
        raise ValueError(f"monigote: pose {pose!r} no existe")
    if pose == "tableta":
        acc = '<rect x="118" y="112" width="98" height="72" rx="8"/><path d="m194 102 24-18"/>'
    elif pose == "timeline":
        acc = '<rect x="94" y="124" width="130" height="62" rx="8"/><path d="M106 146h32m7 0h28m7 0h31M106 164h48m7 0h50"/>'
    elif pose == "mira":
        acc = '<path d="m194 54 34 10-34 10"/>'
    else:
        acc = '<rect x="112" y="155" width="94" height="65" rx="7"/><path d="m178 148 35-20"/>'
    return (f'<div class="stick" id="{iid}"><svg viewBox="0 0 300 330" aria-hidden="true">'
            f'<g fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">'
            f'<circle cx="150" cy="57" r="35"/><path d="M150 92v112M150 128 92 166"/>'
            f'<path id="{iid}-arm" d="m150 128 62 30"/><path d="m150 204-45 98M150 204l48 98"/>{acc}</g>'
            f'</svg></div>')


def _contador(iid: str, desde: int, prefijo: str = "", sufijo: str = "") -> str:
    return f'<span id="{iid}">{esc(prefijo)}{desde}{esc(sufijo)}</span>'


def _shared_css(p: str) -> str:
    return f"""
{p} .rm-thumb{{position:relative;border-radius:{RADIUS['md']}px;overflow:hidden;
  border:1px solid {TK.LINE};flex:0 0 auto}}
{p} .rm-bust{{position:absolute;left:0;bottom:0;width:100%;height:92%}}
{p} .rm-reels{{position:absolute;right:8px;top:8px;color:{C['text']};display:flex}}
{p} .rm-views{{position:absolute;left:7px;bottom:7px;display:flex;align-items:center;
  gap:5px;font-family:{FONT};font-size:14px;font-weight:800;color:{C['text']};
  text-shadow:0 2px 5px {shade_a(.55)};padding:4px 6px;border-radius:{RADIUS['pill']}px}}
{p} .rm-views svg{{flex:0 0 auto}}
{p} .ra-avatar{{position:relative;display:inline-flex;align-items:center;justify-content:center;
  box-sizing:border-box;border-radius:50%;padding:4px;background:linear-gradient(135deg,{C['accent']},{C['accent_hi']});overflow:hidden;flex:0 0 auto}}
{p} .ra-avatar img,{p} .ra-ref{{width:100%;height:100%;border-radius:50%;display:block;overflow:hidden}}
{p} .ra-avatar img{{object-fit:cover;border:3px solid {C['surface']}}}
{p} .ra-ref svg{{width:100%;height:100%;display:block}}
{p} .stick{{width:300px;height:330px;color:{C['text']}}}
{p} .stick svg{{width:100%;height:100%;display:block}}
"""


def _profile_header(cid: str, propio: bool, handle: str, visible: bool = True) -> str:
    who = "propio" if propio else "ref"
    style = "" if visible else ' style="opacity:0"'
    return (f'<div class="ip-head" id="{cid}-head"{style}>'
            f'{_avatar(f"{cid}-av", who, 1, 86)}'
            f'<div class="ip-user"><span class="ip-handle">@{esc(handle)}</span>'
            f'<div class="ip-counts"><span>{_contador(f"{cid}-posts", 0)}<small>publicaciones</small></span>'
            f'<span><b>18 K</b><small>seguidores</small></span><span><b>842</b><small>seguidos</small></span>'
            f'</div></div></div>')


def ig_perfil(cid: str, variant: str, at: list, lienzo: bool = False,
              handle: str = "ezequielfrias.ia") -> tuple[str, str, list]:
    variants = {"llenar": 2, "ordenar": 3, "vistas": 1}
    if variant not in variants:
        raise ValueError(f"ig_perfil: variante {variant!r} no existe")
    _need_at("ig_perfil", at, variants[variant])
    p, _, max_h = _host(cid, lienzo)
    many = variant == "llenar"
    n = 30 if many else 9
    cols = 6 if many else 3
    # La relación 9:16 manda el alto: 30 reels solo caben dentro de los
    # 760 px de la banda a 55 px de ancho. En lienzo hay 1180 px y la grilla
    # de 3×3 puede crecer sin cambiar de proporción.
    tw = 55 if many else (172 if lienzo else 92)
    visible_header = variant != "ordenar"
    profile_handle = handle if variant == "llenar" else "referente_1"
    thumbs = []
    for i in range(n):
        # La cifra espera su beat incluso en el DOM; la fila sí existe como
        # chrome para que la miniatura no cambie de geometría al llenarse.
        views = "" if variant == "vistas" else None
        thumbs.append(_miniatura(f"{cid}-m{i}", i, views, w=tw))
    logo, _ = logos.mark("instagram", 40, uid=f"{cid}-instagram")
    cal = ""
    if variant == "llenar":
        days = "".join(f"<span>{x}</span>" for x in "LMXJVSD")
        cal = (f'<div class="ip-cal" id="{cid}-cal"><div class="ip-calhead">'
               f'<span id="{cid}-month"></span><span class="ip-days">{days}</span></div></div>')
    menu = ""
    cursor = ""
    if variant == "ordenar":
        opts = "".join(f'<span class="ip-opt" id="{cid}-opt{i}">'
                       + (f'<i class="ip-hl" id="{cid}-hl"></i>' if i == 1 else "")
                       + f'<span>{esc(x)}</span></span>'
                       for i, x in enumerate(("Más recientes", "Más vistos", "Más antiguos")))
        menu = (f'<div class="ip-glow" id="{cid}-glow"></div><div class="ip-menu" id="{cid}-menu">'
                f'{opts}</div>')
        cursor = _cursor(cid)
    css = _shared_css(p) + _cursor_css(p) + f"""
{p} .ip-wrap{{position:relative;width:960px;max-height:{max_h}px;display:flex;flex-direction:column;
  align-items:center;gap:14px;color:{C['text']}}}
{p} .ip-head{{width:900px;display:flex;align-items:center;gap:24px;padding:14px 22px;
  background:{C['surface']};border:1px solid {TK.LINE};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW}}}
{p} .ip-user{{flex:1;display:flex;flex-direction:column;gap:14px}}
{p} .ip-handle{{align-self:flex-start;font-family:{MONO};font-size:22px;font-weight:700;color:{C['text']};background:{C['surface2']};border-radius:{RADIUS['pill']}px;padding:8px 16px}}
{p} .ip-counts{{display:flex;gap:34px}} {p} .ip-counts span{{display:flex;align-items:baseline;gap:7px;font-family:{FONT};font-size:24px;font-weight:900}}
{p} .ip-counts small{{font-size:14px;font-weight:600;color:{C['text2']}}}
{p} .ip-tabs{{width:900px;height:48px;display:flex;justify-content:center;gap:90px;align-items:center;border-bottom:1px solid {TK.LINE};color:{C['text2']}}}
{p} .ip-tabs .active{{color:{C['accent_hi']};border-bottom:3px solid {C['accent']};height:48px;display:flex;align-items:center}}
{p} .ip-grid{{position:relative;display:grid;grid-template-columns:repeat({cols},{tw}px);gap:{8 if many else 12}px;padding:14px;border:1px dashed {C['text3']};border-radius:{RADIUS['md']}px;z-index:2}}
{p} .ip-grid .rm-thumb{{{'opacity:0;' if variant in ('llenar','ordenar') else ''}}}
{p} .ip-grid .rm-views{{opacity:0}} {p} .ip-grid .rm-thumb:nth-child(-n+3) .rm-views{{background:{C['accent_pill']}}}
{p} .ip-brand{{position:absolute;right:36px;top:35px;opacity:0}}
{p} .ip-cal{{position:absolute;left:10px;right:10px;bottom:-8px;height:{min(max_h - 145, 590)}px;border:2px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;opacity:0;pointer-events:none;z-index:3}}
{p} .ip-calhead{{height:52px;display:flex;align-items:center;justify-content:space-between;padding:0 22px;font-family:{MONO};font-size:18px;font-weight:700;color:{C['text2']}}}
{p} .ip-days{{display:flex;gap:19px}} {p} .ip-days span{{width:22px;text-align:center}}
{p} .ip-menu{{position:absolute;right:42px;top:190px;width:300px;padding:12px;background:{C['surface']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['md']}px;box-shadow:{TK.SHADOW};display:flex;flex-direction:column;opacity:0;z-index:8}}
{p} .ip-hl{{position:absolute;inset:0;border-radius:{RADIUS['sm']}px;background:{C['accent_pill']};opacity:0;z-index:-1}}
{p} .ip-opt{{position:relative;z-index:0;padding:16px 18px;border-radius:{RADIUS['sm']}px;font-family:{FONT};font-size:21px;font-weight:700}}
{p} .ip-opt+ .ip-opt{{border-top:1px solid {TK.LINE}}} {p} #""" + f"{cid}-opt1" + f"""{{position:relative;z-index:2}}
{p} .ip-glow{{position:absolute;right:50px;top:220px;width:260px;height:180px;border-radius:50%;background:radial-gradient(circle,{accent_a(.18)},transparent 70%);filter:blur(16px);opacity:0;z-index:7}}
"""
    html = (f'<div class="ip-wrap">{_profile_header(cid, variant == "llenar", profile_handle, visible_header)}'
            f'<span class="ip-brand" id="{cid}-brand">{logo}</span>'
            f'<div class="ip-tabs"><span>{_glifo("grid", 30)}</span><span class="active">{_glifo("reels", 30)}</span></div>'
            f'<div class="ip-grid" id="{cid}-grid">{"".join(thumbs)}</div>{cal}{menu}{cursor}</div>')
    anims: list = []
    if variant == "llenar":
        t30, tmes = at
        anims += [("count-roll", f"#{cid}-posts", t30, .70, 0, 30, ""),
                  ("chip-in", f"#{cid}-brand", t30, .25)]
        anims += [("chip-in", f"#{cid}-m{i}", round(t30 + i * .022, 4), .24) for i in range(30)]
        anims += [("box-in", f"#{cid}-cal", tmes, .36),
                  ("caret-off", f"#{cid}-month", tmes, .01, "OCTUBRE")]
    elif variant == "ordenar":
        tcuenta, tordena, treels = at
        anims += [("stamp", f"#{cid}-av", tcuenta, .24),
                  ("slide-in", f"#{cid}-head", tcuenta, .30),
                  ("chip-in", f"#{cid}-brand", tcuenta, .24)]
        anims += [("chip-in", f"#{cid}-m{i}", round(tcuenta + i * .045, 4), .24) for i in range(9)]
        anims += [("rise-in", f"#{cid}-menu", tordena, .30),
                  ("chip-in", f"#{cid}-glow", tordena, .25),
                  ("cursor-enter", f"#{cid}-cursor", tordena, .38, 690, 205),
                  ("cursor-to", f"#{cid}-cursor", round(tordena + .40, 4), .30, 710, 285),
                  ("click", f"#{cid}-cursor", treels, .30, f"#{cid}-ring"),
                  ("chip-in", f"#{cid}-hl", treels, .18),
                  ("badge-out", f"#{cid}-menu", round(treels + .18, 4), .22)]
        perm = (4, 0, 7, 2, 8, 1, 6, 3, 5)
        cell = tw + 12
        for i, dest in enumerate(perm):
            anims.append(("cursor-to", f"#{cid}-m{i}", treels, .45,
                          (dest % 3 - i % 3) * cell, (dest // 3 - i // 3) * round(tw * 16 / 9 + 12)))
    else:
        tv = at[0]
        for i, view in enumerate(_VISTAS):
            t = round(tv + i * .09, 4)
            anims += [("caret-off", f"#{cid}-m{i}-v", t, .01, view),
                      ("slide-in", f"#{cid}-m{i}-v", t, .24)]
    return css, html, anims


def ig_barras(cid: str, at: list, lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("ig_barras", at, 2)
    p, _, max_h = _host(cid, lienzo)
    vals = (2400, 1800, 1100, 640, 410, 320, 250, 190, 120)
    bars = []
    for i, (v, label) in enumerate(zip(vals, _VISTAS)):
        h = 90 + round(v / 2400 * 520)
        bars.append(f'<div class="ib-col"><span class="ib-label">{label}</span>'
                    f'<div class="ib-move" id="{cid}-move{i}"><span class="ib-bar" style="height:{h}px">'
                    f'<span class="ib-accent" id="{cid}-accent{i}"></span></span></div>'
                    f'{_miniatura(f"{cid}-m{i}", i, w=72)}</div>')
    css = _shared_css(p) + f"""
{p} .ib-wrap{{position:relative;width:960px;height:{min(max_h, 900)}px;display:flex;align-items:flex-end;justify-content:center;gap:16px;padding:70px 18px 24px}}
{p} .ib-col{{width:88px;height:100%;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:10px}}
{p} .ib-label{{font-family:{MONO};font-size:15px;font-weight:700;color:{C['text2']}}}
{p} .ib-move{{width:54px;display:flex;align-items:flex-end;flex:1;transform-origin:50% 100%}}
{p} .ib-bar{{position:relative;width:54px;display:block;border-radius:{RADIUS['sm']}px {RADIUS['sm']}px 3px 3px;background:{C['text3']};overflow:hidden;transform-origin:50% 100%}}
{p} .ib-accent{{position:absolute;inset:0;background:{C['accent']};box-shadow:{TK.GLOW};opacity:0}}
{p} .ib-avg{{position:absolute;left:24px;right:24px;bottom:330px;border-top:2px dashed {C['text3']};font-family:{MONO};font-size:16px;font-weight:700;color:{C['text2']}}}
{p} .ib-avg span{{position:absolute;right:0;top:-29px;background:{C['surface']};padding:3px 8px}}
"""
    html = f'<div class="ib-wrap"><div class="ib-avg"><span>PROMEDIO</span></div>{"".join(bars)}</div>'
    t_up, t_out = at
    anims = []
    for i in range(3):
        anims += [("cursor-to", f"#{cid}-move{i}", t_up, .30, 0, -40),
                  ("cam-push", f"#{cid}-move{i}", t_out, .52, 1.55, -120),
                  ("chip-in", f"#{cid}-accent{i}", t_out, .20)]
    return css, html, anims


def ig_busqueda(cid: str, at: list, query: str = "inteligencia artificial",
                lienzo: bool = False) -> tuple[str, str, list]:
    _need_at("ig_busqueda", at, 2)
    p, _, max_h = _host(cid, lienzo)
    finals = _VISTAS[:5]
    nums = (2400, 1900, 1200, 860, 640)
    rows = []
    for i in range(5):
        rows.append(f'<div class="is-row" id="{cid}-r{i}">{_avatar(f"{cid}-av{i}", "ref", i + 1, 62)}'
                    f'<span class="is-name">@referente_{i + 1}</span><span class="is-count">'
                    f'{_contador(f"{cid}-n{i}", 0)}</span></div>')
    logo, _ = logos.mark("instagram", 36, uid=f"{cid}-instagram")
    css = _shared_css(p) + f"""
{p} .is-wrap{{width:900px;max-height:{max_h}px;display:flex;flex-direction:column;gap:12px}}
{p} .is-search{{height:76px;display:flex;align-items:center;gap:18px;padding:0 24px;background:{C['surface2']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['pill']}px;color:{C['text2']}}}
{p} .is-query{{font-family:{FONT};font-size:26px;font-weight:700;color:{C['text']};flex:1}}
{p} .is-brand{{opacity:0;display:flex}}
{p} .is-results{{display:flex;flex-direction:column;gap:9px}}
{p} .is-row{{height:92px;display:flex;align-items:center;gap:18px;padding:0 20px;background:{C['surface']};border:1px solid {TK.LINE};border-radius:{RADIUS['md']}px;box-shadow:{TK.SHADOW};opacity:0}}
{p} .is-name{{font-family:{MONO};font-size:20px;font-weight:700;color:{C['text']};flex:1}}
{p} .is-count{{font-family:{MONO};font-size:22px;font-weight:700;color:{C['accent_hi']}}}
{p} .ccaret{{display:inline-block;width:3px;height:25px;background:{C['accent']};vertical-align:-3px}}
"""
    html = (f'<div class="is-wrap"><div class="is-search">{_glifo("search", 32)}'
            f'<span class="is-query" id="{cid}-query"></span><span class="is-brand" id="{cid}-brand">{logo}</span>'
            f'</div><div class="is-results">{"".join(rows)}</div></div>')
    t5, tnicho = at
    anims: list = [("type-word", f"#{cid}-query", 0, .50, query),
                   ("caret-off", f"#{cid}-query", .52, .01, query),
                   ("chip-in", f"#{cid}-brand", t5, .24)]
    for i, (num, final) in enumerate(zip(nums, finals)):
        anims += [("drop-in", f"#{cid}-r{i}", round(t5 + i * .11, 4), .30),
                  ("count-roll", f"#{cid}-n{i}", tnicho, .50, 0, num, "", " K"),
                  ("caret-off", f"#{cid}-n{i}", round(tnicho + .52, 4), .01, final)]
    return css, html, anims


def ig_guardar(cid: str, at: list, coleccion: str = "Outliers",
               lienzo: bool = False) -> tuple[str, str, list]:
    _need_at("ig_guardar", at, 2)
    p, _, max_h = _host(cid, lienzo)
    actions = []
    for name in ("heart", "comment", "share", "bookmark"):
        fill = (f'<span class="igs-fill" id="{cid}-book">'
                f'{_glifo("bookmark-fill", 38)}</span>') if name == "bookmark" else ""
        actions.append(f'<span class="igs-act {"book" if name == "bookmark" else ""}">'
                       f'{_glifo(name, 38)}{fill}</span>')
    actions = "".join(actions)
    copies = "".join(f'<div class="igs-copy" id="{cid}-c{i}" style="left:{30 + i * 12}px;top:{90 + i * 8}px">'
                     f'{_miniatura(f"{cid}-cm{i}", i + 2, w=100)}</div>' for i in range(5))
    css = _shared_css(p) + f"""
{p} .igs-wrap{{width:940px;max-height:{max_h}px;display:flex;align-items:center;justify-content:center;gap:90px}}
{p} .igs-open{{display:flex;align-items:flex-end;gap:18px}} {p} .igs-actions{{display:flex;flex-direction:column;gap:22px;color:{C['text']}}}
{p} .igs-act{{position:relative;display:flex}} {p} .igs-fill{{position:absolute;inset:0;color:{C['accent_hi']};opacity:0}}
{p} .igs-collection{{position:relative;width:320px;height:470px;background:{C['surface']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};overflow:hidden}}
{p} .igs-title{{height:68px;display:flex;align-items:center;padding:0 24px;border-bottom:1px solid {TK.LINE};font-family:{MONO};font-size:23px;font-weight:700;color:{C['text']}}}
{p} .igs-empty{{position:absolute;inset:94px 28px 28px;border:2px dashed {C['text3']};border-radius:{RADIUS['md']}px}}
{p} .igs-copy{{position:absolute;opacity:0;z-index:3}} {p} .igs-copy .rm-thumb{{box-shadow:{TK.SHADOW}}}
"""
    html = (f'<div class="igs-wrap"><div class="igs-open">{_miniatura(f"{cid}-hero", 0, w=260)}'
            f'<div class="igs-actions">{actions}</div></div><div class="igs-collection"><div class="igs-title">'
            f'{esc(coleccion)}</div><div class="igs-empty"></div>{copies}</div></div>')
    t_save, t_each = at
    anims = [("stamp", f"#{cid}-book", round(t_save + .12, 4), .18),
             ("chip-in", f"#{cid}-c0", round(t_save + .12, 4), .10),
             ("cursor-to", f"#{cid}-c0", round(t_save + .14, 4), .40, 535, -70)]
    anims += [("drop-in", f"#{cid}-c{i}", round(t_each + (i - 1) * .08, 4), .24)
              for i in range(1, 5)]
    return css, html, anims


def _halftone(p: str) -> str:
    return f"""
{p} .comic-dots{{position:absolute;inset:0;background-image:radial-gradient({ink_a(.17)} 2.6px,transparent 2.9px);background-size:14px 14px;pointer-events:none}}
"""


def monigote(cid: str, variant: str, at: list,
             lienzo: bool = False) -> tuple[str, str, list]:
    variants = {"desinflar": 2, "pregunta": 2, "copiar": 1}
    if variant not in variants:
        raise ValueError(f"monigote: variante {variant!r} no existe")
    _need_at("monigote", at, variants[variant])
    p, _, max_h = _host(cid, lienzo)
    css = _shared_css(p) + _halftone(p) + f"""
{p} .mo-wrap{{position:relative;width:980px;height:{max_h}px;display:flex;align-items:center;justify-content:center;color:{C['text']}}}
{p} .mo-row{{position:relative;z-index:2;display:flex;align-items:center;justify-content:center;gap:60px;zoom:{1.42 if lienzo else 1.22}}}
{p} .mo-person{{position:relative;transform-origin:50% 100%}} {p} .mo-slot{{position:relative}}
{p} .mo-cloud{{position:absolute;left:90px;bottom:35px;display:flex;gap:9px;opacity:0}}
{p} .mo-cloud i{{display:block;width:28px;height:28px;border-radius:50%;background:{ink_a(.25)}}}
{p} .mo-box{{position:relative;width:300px;height:533px}} {p} .mo-half{{position:absolute;left:0;width:100%;height:50%;overflow:hidden;transform-origin:0 100%}}
{p} .mo-half.top{{top:0}} {p} .mo-half.bot{{bottom:0}} {p} .mo-half.top .rm-thumb{{position:absolute;left:0;top:0}}
{p} .mo-half.bot .rm-thumb{{position:absolute;left:0;bottom:0}}
{p} .mo-knot{{position:absolute;left:90px;top:180px;width:120px;height:120px;color:{C['accent']};opacity:0;z-index:5}}
{p} .mo-knot svg{{width:100%;height:100%}}
{p} .mo-qs{{position:absolute;inset:-30px;pointer-events:none}} {p} .mo-q{{position:absolute;font-family:{FONT};font-size:80px;font-weight:900;color:{C['text2']}}}
{p} .mo-q:nth-child(1){{left:-65px;top:40px}} {p} .mo-q:nth-child(2){{right:-60px;top:140px}} {p} .mo-q:nth-child(3){{left:-20px;bottom:20px}}
{p} .mo-stack{{position:relative;width:320px;height:590px}} {p} .mo-card{{position:absolute;opacity:0;z-index:4}}
"""
    if variant == "desinflar":
        people = []
        for i, pose in enumerate(("tableta", "timeline")):
            people.append(f'<div class="mo-slot"><div class="mo-person" id="{cid}-p{i}">{_monigote(f"{cid}-s{i}", pose)}</div>'
                          f'<span class="mo-cloud" id="{cid}-cl{i}"><i></i><i></i><i></i></span></div>')
        html = f'<div class="comic-dots"></div><div class="mo-wrap"><div class="mo-row">{"".join(people)}</div></div>'
        anims = []
        for i, t in enumerate(at):
            anims += [("cam-push", f"#{cid}-s{i}", t, .30, .08, 220),
                      ("badge-out", f"#{cid}-p{i}", round(t + .26, 4), .06),
                      ("chip-in", f"#{cid}-cl{i}", round(t + .15, 4), .18),
                      ("badge-out", f"#{cid}-cl{i}", round(t + .38, 4), .18)]
    elif variant == "pregunta":
        thumb = _miniatura(f"{cid}-thumbtop", 4, w=300)
        thumb2 = _miniatura(f"{cid}-thumbbot", 4, w=300)
        qs = "".join(f'<span class="mo-q" id="{cid}-q{i}">?</span>' for i in range(3))
        html = (f'<div class="comic-dots"></div><div class="mo-wrap"><div class="mo-row">'
                f'<div class="mo-person">{_monigote(f"{cid}-person", "mira")}</div>'
                f'<div class="mo-box"><div class="mo-half top" id="{cid}-top">{thumb}</div>'
                f'<div class="mo-half bot">{thumb2}</div><div class="mo-knot" id="{cid}-knot">{_glifo("knot", 120)}</div>'
                f'<div class="mo-qs">{qs}</div></div></div></div>')
        t_problem, t_solve = at
        anims = [("fade-to", f"#{cid}-q0", .05, .45, .55),
                 ("fade-to", f"#{cid}-q1", .12, .45, .70),
                 ("fade-to", f"#{cid}-q2", .20, .45, .62),
                 ("rot-to", f"#{cid}-top", t_problem, .35, -24),
                 ("drop-in", f"#{cid}-knot", round(t_problem + .12, 4), .28),
                 ("cam-push", f"#{cid}-knot", round(t_problem + .34, 4), .18, 1.08, 16),
                 ("rot-to", f"#{cid}-person-arm", t_solve, .30, -38),
                 ("cursor-to", f"#{cid}-knot", t_solve, .45, -280, -90)]
        anims += [("badge-out", f"#{cid}-q{i}", t_solve, .20) for i in range(3)]
    else:
        pos = [(100 + (i % 2) * 18, 210 - i * 26) if i < 4 else (-330 + (i - 4) * 34, 40 + ((i - 4) % 3) * 34) for i in range(10)]
        cards = "".join(f'<div class="mo-card" id="{cid}-c{i}" style="left:{pos[i][0]}px;top:{pos[i][1]}px;opacity:{1 if i < 4 else 0}">'
                        f'{_miniatura(f"{cid}-m{i}", i, w=116)}</div>' for i in range(10))
        html = (f'<div class="comic-dots"></div><div class="mo-wrap"><div class="mo-row">'
                f'<div class="mo-person">{_monigote(f"{cid}-person", "cuaderno")}</div>'
                f'<div class="mo-stack">{cards}</div></div></div>')
        tm = at[0]
        anims = [("jitter", f"#{cid}-person-arm", .10, .36)]
        anims += [("drop-in", f"#{cid}-c{i}", round(tm + (i - 4) * .05, 4), .22)
                  for i in range(4, 10)]
    return css, html, anims


def nudo_viaje(cid: str, at: list, lienzo: bool = False) -> tuple[str, str, list]:
    _need_at("nudo_viaje", at, 2)
    p, _, max_h = _host(cid, lienzo)
    css = _shared_css(p) + f"""
{p} .nv-wrap{{position:relative;width:900px;height:{min(max_h, 560)}px;display:flex;align-items:center;justify-content:space-between;padding:0 80px}}
{p} .nv-arrow{{position:absolute;left:205px;top:130px;width:490px;height:210px;color:{C['text3']}}}
{p} .nv-arrow path{{fill:none;stroke:currentColor;stroke-width:5;stroke-dasharray:12 13;stroke-linecap:round}}
{p} .nv-knot{{position:absolute;left:168px;top:185px;width:110px;height:110px;color:{C['accent']};z-index:4}}
{p} .nv-knot.good{{color:{C['go']};opacity:0}} {p} .nv-knot svg{{width:100%;height:100%}}
"""
    html = (f'<div class="nv-wrap">{_avatar(f"{cid}-left", "ref", 1, 150)}'
            f'<svg class="nv-arrow" viewBox="0 0 490 210" aria-hidden="true"><path d="M15 165C135 15 335 15 470 160"/></svg>'
            f'<span class="nv-knot" id="{cid}-knot">{_glifo("knot", 110)}</span>'
            f'<span class="nv-knot good" id="{cid}-good">{_glifo("knot", 110)}</span>'
            f'{_avatar(f"{cid}-right", "propio", 0, 150)}</div>')
    travel, land = at
    anims = [("cursor-to", f"#{cid}-knot", travel, .30, 155, -100),
             ("cursor-to", f"#{cid}-knot", round(travel + .30, 4), .30, 315, -100),
             ("cursor-to", f"#{cid}-knot", round(travel + .60, 4), .30, 490, 0),
             ("badge-out", f"#{cid}-knot", land, .14),
             ("chip-in", f"#{cid}-good", land, .18),
             ("cursor-to", f"#{cid}-good", land, .01, 490, 0),
             ("stamp", f"#{cid}-good", round(land + .16, 4), .22)]
    return css, html, anims


def ideas_notas(cid: str, at: list, lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("ideas_notas", at, 2)
    p, _, max_h = _host(cid, lienzo)
    minis = []
    notes = []
    for i in range(5):
        if i == 0:
            minis.append(f'<div class="in-split"><div id="{cid}-halfL">{_miniatura(f"{cid}-ml", i, w=150)}</div>'
                         f'<div id="{cid}-halfR">{_miniatura(f"{cid}-mr", i, w=150)}</div></div>')
        else:
            minis.append(_miniatura(f"{cid}-m{i}", i, w=150))
        lines = '<i></i><i></i><i></i>'
        notes.append(f'<span class="in-note" id="{cid}-n{i}" style="top:{90 + i * 18}px">{lines}</span>')
    css = _shared_css(p) + f"""
{p} .in-wrap{{position:relative;width:640px;height:780px;display:flex;align-items:center;padding:30px 40px;zoom:{1.45 if lienzo else 0.95}}}
{p} .in-list{{display:flex;flex-direction:column;gap:13px}} {p} .in-list>.rm-thumb{{height:118px!important}}
{p} .in-split{{position:relative;width:150px;height:118px;overflow:visible}} {p} .in-split>div{{position:absolute;inset:0;overflow:hidden}}
{p} .in-split>div:first-child{{clip-path:inset(0 50% 0 0)}} {p} .in-split>div:last-child{{clip-path:inset(0 0 0 50%)}}
{p} .in-notes{{position:absolute;left:220px;right:20px;top:80px;bottom:80px}}
{p} .in-note{{position:absolute;left:0;width:180px;height:150px;background:{C['accent_soft']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['sm']}px;padding:30px 22px;box-shadow:{TK.SHADOW};opacity:0}}
{p} .in-note i{{display:block;height:9px;margin-bottom:14px;border-radius:{RADIUS['pill']}px;background:{ink_a(.25)}}}
"""
    html = f'<div class="in-wrap"><div class="in-list">{"".join(minis)}</div><div class="in-notes">{"".join(notes)}</div></div>'
    outlier, idea = at
    anims = [("cursor-to", f"#{cid}-halfL", outlier, .28, -30, 0),
             ("cursor-to", f"#{cid}-halfR", outlier, .28, 30, 0)]
    for i in range(5):
        t = round(idea + i * .09, 4)
        anims += [("chip-in", f"#{cid}-n{i}", t, .16),
                  ("cursor-to", f"#{cid}-n{i}", t, .35,
                   170 + i * 8, 120 + i * 40)]
    return css, html, anims


def _claude_shell(cid: str, p: str, max_h: int, attachments: str,
                  placeholder: bool = True) -> tuple[str, str]:
    logo, _ = logos.mark("claude", 44, uid=f"{cid}-claude")
    css = _shared_css(p) + _cursor_css(p) + f"""
{p} .cc-wrap{{position:relative;width:900px;height:{min(max_h, 720)}px;background:{C['surface']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};overflow:hidden}}
{p} .cc-head{{height:82px;display:flex;align-items:center;gap:15px;padding:0 26px;border-bottom:1px solid {TK.LINE};font-family:{FONT};font-size:28px;font-weight:800;color:{C['text']}}}
{p} .cc-field{{position:relative;height:calc(100% - 82px);padding:34px}}
{p} .cc-ph{{font-family:{FONT};font-size:27px;color:{C['text3']}}}
{p} .cc-files{{position:absolute;left:34px;top:90px;display:flex;gap:16px;align-items:flex-end}}
{p} .cc-file{{position:relative;width:128px;height:218px;padding:8px;background:{C['surface2']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['md']}px;box-shadow:{TK.SHADOW}}}
{p} .cc-file .rm-thumb{{width:90px!important;height:160px!important;margin:auto}} {p} .cc-file .rm-views{{opacity:0}}
{p} .cc-ig{{position:absolute;right:5px;top:5px;width:28px;height:28px;background:{C['surface']};border-radius:8px;display:flex;align-items:center;justify-content:center}}
{p} .cc-bar{{position:absolute;left:34px;right:34px;bottom:24px;height:76px;border-top:1px solid {TK.LINE};display:flex;align-items:center;justify-content:flex-end}}
{p} .cc-send{{width:54px;height:54px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:{C['surface2']};color:{C['text']}}}
{p} .cc-spot{{position:absolute;right:12px;bottom:4px;width:150px;height:150px;border-radius:50%;background:radial-gradient(circle,{accent_a(.20)},transparent 70%);opacity:0}}
"""
    ph = f'<span class="cc-ph" id="{cid}-ph">Escribe un mensaje…</span>' if placeholder else ""
    html = (f'<div class="cc-wrap"><div class="cc-head">{logo}<span>Claude</span></div><div class="cc-field">'
            f'{ph}'
            f'<div class="cc-files">{attachments}</div><div class="cc-spot" id="{cid}-spot"></div>'
            f'<div class="cc-bar"><span class="cc-send" id="{cid}-send">{_glifo("share", 27)}</span></div></div></div>')
    return css, html


def claude_chat(cid: str, variant: str, at: list,
                lienzo: bool = False) -> tuple[str, str, list]:
    if variant not in ("arrastrar", "enviar"):
        raise ValueError(f"claude_chat: variante {variant!r} no existe")
    _need_at("claude_chat", at, 2)
    p, _, max_h = _host(cid, lienzo)
    files = []
    for i, view in enumerate(_VISTAS[:3]):
        ig, _ = logos.mark("instagram", 22, uid=f"{cid}-ig{i}")
        opacity = 0 if variant == "arrastrar" and i else (0 if variant == "arrastrar" and i == 0 else 1)
        shown_view = "" if variant == "arrastrar" else view
        files.append(f'<div class="cc-file" id="{cid}-f{i}" style="opacity:{opacity}">'
                     f'{_miniatura(f"{cid}-m{i}", i, shown_view, w=90)}<span class="cc-ig">{ig}</span></div>')
    css, html = _claude_shell(cid, p, max_h, "".join(files), variant == "arrastrar")
    if variant == "enviar":
        css += f"\n{p} .cc-file .rm-views{{opacity:1}}"
    html = html[:-6] + _cursor(cid) + '</div>'
    if variant == "arrastrar":
        tvideo, twinner = at
        anims = [("cursor-enter", f"#{cid}-cursor", 0, .34, 80, 210),
                 ("cursor-to", f"#{cid}-cursor", round(tvideo - .30, 4), .30, 120, 260),
                 ("drop-in", f"#{cid}-f0", tvideo, .25),
                 ("badge-out", f"#{cid}-ph", tvideo, .16)]
        anims += [("drop-in", f"#{cid}-f{i}", round(twinner + (i - 1) * .10, 4), .25)
                  for i in (1, 2)]
        for i, view in enumerate(_VISTAS[:3]):
            t = round(twinner + i * .08, 4)
            anims += [("caret-off", f"#{cid}-m{i}-v", t, .01, view),
                      ("slide-in", f"#{cid}-m{i}-v", t, .22)]
    else:
        tpass, tclaude = at
        anims = [("chip-in", f"#{cid}-spot", tpass, .25),
                 ("cursor-enter", f"#{cid}-cursor", tpass, .34, 720, 520),
                 ("cursor-to", f"#{cid}-cursor", round(tpass + .30, 4), .30, 785, 555),
                 ("click", f"#{cid}-cursor", tclaude, .30, f"#{cid}-ring"),
                 ("send-on", f"#{cid}-send", tclaude, .30)]
    return css, html, anims


def _transcript_panel(cid: str, filled: bool = False) -> str:
    rows = "".join(f'<span class="scan-row"><i id="{cid}-line{i}"></i></span>'
                   for i in range(6))
    return f'<div class="scan-panel" id="{cid}-panel"><div class="scan-head" id="{cid}-head"></div><div class="scan-lines{(" filled" if filled else "")}">{rows}</div></div>'


def escaneo(cid: str, at: list, lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("escaneo", at, 2)
    p, _, max_h = _host(cid, lienzo)
    claude, _ = logos.mark("claude", 38, uid=f"{cid}-claude")
    css = _shared_css(p) + f"""
{p} .scan-wrap{{position:relative;width:850px;height:{min(max_h, 1050)}px;display:flex;flex-direction:column;align-items:center;gap:28px}}
{p} .scan-media{{position:relative}} {p} .scan-laser{{position:absolute;left:0;top:0;width:100%;height:10px;background:{C['accent']};box-shadow:{TK.GLOW};border-radius:{RADIUS['pill']}px;opacity:0;z-index:4}}
{p} .scan-panel{{width:760px;background:{C['surface']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};padding:20px}}
{p} .scan-head{{height:54px;border-bottom:1px solid {TK.LINE};display:flex;align-items:center}}
{p} .scan-lines{{padding:22px;display:flex;flex-direction:column;gap:18px}}
{p} .scan-row{{height:15px;border-radius:{RADIUS['pill']}px;background:{ink_a(.10)};overflow:hidden}}
{p} .scan-row i{{display:block;height:100%;background:{rgba(C['text2'], .30)};width:0}}
"""
    panel = _transcript_panel(cid)
    panel = panel.replace(f'<div class="scan-head" id="{cid}-head"></div>',
                          f'<div class="scan-head" id="{cid}-head">{claude}</div>')
    html = (f'<div class="scan-wrap"><div class="scan-media">{_miniatura(f"{cid}-media", 2, w=310)}'
            f'<span class="scan-laser" id="{cid}-laser"></span></div>{panel}</div>')
    tscan, ttext = at
    anims = [("chip-in", f"#{cid}-laser", tscan, .10),
             ("cam-push", f"#{cid}-laser", tscan, .90, 1, 540),
             ("badge-out", f"#{cid}-laser", round(tscan + .90, 4), .14)]
    anims += [("grow-x", f"#{cid}-line{i}", round(ttext + i * .08, 4), .28,
               480 + (i * 47) % 170) for i in range(6)]
    return css, html, anims


def prompt_encaje(cid: str, at: list, lienzo: bool = False) -> tuple[str, str, list]:
    _need_at("prompt_encaje", at, 2)
    p, _, max_h = _host(cid, lienzo)
    claude, _ = logos.mark("claude", 38, uid=f"{cid}-claude")
    rows = "".join(f'<span class="pe-line" style="width:{72 + i * 4}%"></span>' for i in range(6))
    prompt_lines = '<i></i><i></i><i></i>'
    css = f"""
{p} .pe-wrap{{position:relative;width:860px;height:{min(max_h, 650)}px;display:flex;align-items:center;justify-content:center}}
{p} .pe-inner{{position:relative;width:760px;transform-origin:50% 70%}}
{p} .pe-panel{{background:{C['surface']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};padding:20px}}
{p} .pe-head{{height:54px;display:flex;align-items:center;border-bottom:1px solid {TK.LINE}}}
{p} .pe-lines{{padding:20px;display:flex;flex-direction:column;gap:16px}} {p} .pe-line{{height:14px;border-radius:{RADIUS['pill']}px;background:{rgba(C['text2'], .30)}}}
{p} .pe-prompt{{position:absolute;left:130px;top:45px;width:500px;padding:25px;background:{C['surface']};border:2px solid {C['accent']};border-radius:{RADIUS['md']}px;box-shadow:{TK.SHADOW};opacity:0;z-index:5}}
{p} .pe-symbol{{font-family:{MONO};font-size:30px;font-weight:700;color:{C['accent_hi']}}} {p} .pe-prompt i{{display:block;height:12px;margin-top:15px;border-radius:{RADIUS['pill']}px;background:{ink_a(.20)}}}
"""
    html = (f'<div class="pe-wrap"><div class="pe-inner" id="{cid}-inner"><div class="pe-panel">'
            f'<div class="pe-head">{claude}</div><div class="pe-lines">{rows}</div></div></div>'
            f'<div class="pe-prompt" id="{cid}-prompt"><span class="pe-symbol">&gt;_</span>{prompt_lines}</div></div>')
    shrink, prompt = at
    anims = [("cam-push", f"#{cid}-inner", shrink, .35, .55, 90),
             ("drop-in", f"#{cid}-prompt", prompt, .32),
             ("stamp", f"#{cid}-prompt", round(prompt + .28, 4), .18)]
    return css, html, anims


def _prompt_size(lineas: list[str], lienzo: bool) -> int:
    size = 30 if lienzo else 23
    available = 836 if lienzo else 830
    while size >= 20:
        # JetBrains Mono avanza 0.6 em por carácter; `text_px` mide Inter y
        # subestimaba la línea larga, que salía cortada por el borde.
        if max((len(str(line)) * size * .6 for line in lineas), default=0) <= available:
            return size
        size -= 1
    raise ValueError("prompt_hoja: una línea no cabe ni a 20 px")


def _prompt_card(cid: str, lineas: list[str], written: bool) -> str:
    rows = "".join(f'<div class="ph-row"><span class="ph-mark" id="{cid}-mark{i}"></span>'
                   f'<span class="ph-text" id="{cid}-line{i}">{esc(line) if written else ""}</span></div>'
                   for i, line in enumerate(lineas))
    return (f'<div class="ph-card" id="{cid}-card"><div class="ph-head"><span>&gt;_</span>'
            f'<b>PROMPT</b></div><div class="ph-body">{rows}</div></div>')


def prompt_hoja(cid: str, variant: str, at: list, lineas: list[str],
                lienzo: bool = False) -> tuple[str, str, list]:
    variants = {"desplegar": 2, "copiar": 2, "absorber": 1}
    if variant not in variants:
        raise ValueError(f"prompt_hoja: variante {variant!r} no existe")
    _need_at("prompt_hoja", at, variants[variant])
    p, _, max_h = _host(cid, lienzo)
    size = _prompt_size(lineas, lienzo)
    written = variant != "desplegar"
    card = _prompt_card(cid, lineas, written)
    css = _shared_css(p) + _cursor_css(p) + f"""
{p} .ph-wrap{{position:relative;width:940px;max-height:{max_h}px;display:flex;align-items:center;justify-content:center;color:{C['text']}}}
{p} .ph-card{{position:relative;width:900px;background:{C['surface']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};overflow:hidden}}
{p} .ph-head{{height:66px;display:flex;align-items:center;gap:14px;padding:0 24px;border-bottom:1px solid {TK.LINE};font-family:{MONO};font-size:20px;font-weight:700;color:{C['accent_hi']};letter-spacing:.12em}}
{p} .ph-body{{padding:24px 28px;display:flex;flex-direction:column;gap:{8 if lienzo else 5}px}}
{p} .ph-row{{position:relative;min-height:{round(size * 1.45)}px;display:flex;align-items:center}}
{p} .ph-text{{position:relative;z-index:2;font-family:{MONO};font-size:{size}px;font-weight:700;line-height:1.45;white-space:pre;color:{C['text']}}}
{p} .ph-mark{{position:absolute;left:-5px;right:-5px;height:{round(size * 1.35)}px;background:{accent_a(.28)};border-radius:5px;width:0;z-index:1}}
{p} .ccaret{{display:inline-block;width:3px;height:{size}px;background:{C['accent']};vertical-align:-3px}}
{p} .ph-progress{{position:absolute;left:20px;right:20px;bottom:-76px;height:48px;display:flex;align-items:center;gap:18px;color:{C['text']}}}
{p} .ph-track{{flex:1;height:9px;border-radius:{RADIUS['pill']}px;background:{ink_a(.15)};overflow:hidden}} {p} .ph-fill{{display:block;width:62%;height:100%;background:{C['text']}}}
{p} .ph-small{{width:390px;transform:scale(.43);transform-origin:50% 50%}}
{p} .ph-mosaic{{position:relative;width:300px;height:300px;display:flex;align-items:center;justify-content:center;background:{C['surface']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};opacity:.45}}
{p} .ph-halo{{position:absolute;inset:-55px;border-radius:50%;background:radial-gradient(circle,{accent_a(.28)},transparent 70%);opacity:0;z-index:-1}}
"""
    if variant == "desplegar":
        html = f'<div class="ph-wrap">{card}</div>'
        start, end = at
        if end < start:
            raise ValueError("prompt_hoja: t_pantalla debe ser >= t_prompt")
        slot = max(.12, (end - start) / max(1, len(lineas)))
        anims = []
        for i, line in enumerate(lineas):
            t = round(start + i * slot, 4)
            dur = max(.08, slot * .82)
            anims += [("type-word", f"#{cid}-line{i}", t, dur, str(line)),
                      ("caret-off", f"#{cid}-line{i}", round(min(end, t + dur), 4), .01, str(line))]
    elif variant == "copiar":
        pause, copies = at
        progress = (f'<div class="ph-progress"><span id="{cid}-pause">{_glifo("pause", 34)}</span>'
                    f'<span class="ph-track"><i class="ph-fill" id="{cid}-fill"></i></span></div>')
        html = f'<div class="ph-wrap">{card}{progress}{_cursor(cid)}</div>'
        anims = [("stamp", f"#{cid}-pause", pause, .20),
                 ("jitter", f"#{cid}-fill", pause, .28),
                 ("cursor-enter", f"#{cid}-cursor", copies, .28, 40, 60)]
        anims += [("grow-x", f"#{cid}-mark{i}", round(copies + i * .05, 4), .24, 840)
                  for i in range(len(lineas))]
    else:
        logo, _ = logos.mark("claude", 120, uid=f"{cid}-claude")
        html = (f'<div class="ph-wrap" style="gap:120px"><div class="ph-small" id="{cid}-small">{card}</div>'
                f'<div class="ph-mosaic" id="{cid}-mosaic"><span class="ph-halo" id="{cid}-halo"></span>{logo}</div></div>')
        t = at[0]
        anims = [("cursor-to", f"#{cid}-small", t, .52, 450, 0),
                 ("fade-to", f"#{cid}-small", t, .52, 0),
                 ("fade-to", f"#{cid}-mosaic", t, .35, 1),
                 ("chip-in", f"#{cid}-halo", t, .30)]
    return css, html, anims


def tablero(cid: str, at: list, lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("tablero", at, 2)
    p, _, max_h = _host(cid, lienzo)
    logo, _ = logos.mark("claude", 110, uid=f"{cid}-claude")
    card_parts = []
    for i in range(4):
        ring = f'<span class="tb-ring" id="{cid}-ringcard"></span>' if i == 2 else ""
        card_parts.append(f'<div class="tb-card" id="{cid}-m{i}" '
                          f'style="left:{100 + (i % 2) * 260}px;top:{100 + (i // 2) * 360}px">'
                          f'{_miniatura(f"{cid}-thumb{i}", i, w=180)}'
                          f'<span class="tb-pin">{_glifo("pin", 36)}</span>{ring}</div>')
    cards = "".join(card_parts)
    css = _shared_css(p) + _cursor_css(p) + f"""
{p} .tb-wrap{{position:relative;width:940px;height:{min(max_h, 1020)}px;background:{C['surface2']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};overflow:hidden;background-image:linear-gradient({ink_a(.06)} 1px,transparent 1px),linear-gradient(90deg,{ink_a(.06)} 1px,transparent 1px);background-size:54px 54px}}
{p} .tb-claude{{position:absolute;right:55px;top:80px;width:190px;height:190px;display:flex;align-items:center;justify-content:center;background:{C['surface']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};opacity:0}}
{p} .tb-claude:before{{content:"";position:absolute;inset:-38px;border-radius:50%;background:radial-gradient(circle,{accent_a(.24)},transparent 70%);z-index:-1}}
{p} .tb-card{{position:absolute;opacity:0}} {p} .tb-pin{{position:absolute;left:50%;top:-20px;color:{C['accent']}}}
{p} .tb-ring{{position:absolute;inset:-12px;border:4px solid {C['accent']};border-radius:{RADIUS['lg']}px;opacity:0}}
"""
    html = f'<div class="tb-wrap"><div class="tb-claude" id="{cid}-claudebox">{logo}</div>{cards}{_cursor(cid)}</div>'
    expert, marketing = at
    anims = [("chip-in", f"#{cid}-claudebox", expert, .30),
             ("cursor-enter", f"#{cid}-cursor", expert, .35, 720, 260)]
    anims += [("stamp", f"#{cid}-m{i}", round(marketing + i * .09, 4), .28) for i in range(4)]
    anims += [("cursor-to", f"#{cid}-cursor", marketing, .38, 420, 650),
              ("box-in", f"#{cid}-ringcard", round(marketing + .34, 4), .28)]
    return css, html, anims


def _reel_face(cid: str, own: bool, view: str, n: int = 2,
               defer_view: bool = False) -> str:
    who = "propio" if own else "ref"
    handle = "ezequielfrias.ia" if own else "referente_2"
    return (f'<div class="rt-face"><div class="rt-author">{_avatar(f"{cid}-av-{who}", who, n, 62)}'
            f'<span>@{handle}</span></div>{_miniatura(f"{cid}-thumb-{who}", n, w=330)}'
            f'<span class="rt-view" id="{cid}-view-{who}"'
            f'{" style=\"opacity:0\"" if defer_view else ""}>'
            f'{"" if defer_view else esc(view)}</span></div>')


def reel_tarjeta(cid: str, variant: str, at: list,
                 lienzo: bool = False) -> tuple[str, str, list]:
    variants = {"llega": 3, "girar": 2, "cruce": 3}
    if variant not in variants:
        raise ValueError(f"reel_tarjeta: variante {variant!r} no existe")
    _need_at("reel_tarjeta", at, variants[variant])
    p, _, max_h = _host(cid, lienzo)
    css = _shared_css(p) + f"""
{p} .rt-wrap{{position:relative;width:940px;height:{min(max_h, 930)}px;display:flex;align-items:center;justify-content:center}}
{p} .rt-slot{{position:relative;width:380px;min-height:720px;display:flex;align-items:center;justify-content:center;transform-style:preserve-3d}}
{p} .rt-slot.arrive{{left:-700px}}
{p} .rt-face{{position:relative;padding:20px;background:{C['surface']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW}}}
{p} .rt-author{{height:72px;display:flex;align-items:center;gap:14px;font-family:{MONO};font-size:18px;font-weight:700;color:{C['text']}}}
{p} .rt-view{{position:absolute;left:42px;bottom:40px;background:{C['accent_pill']};border-radius:{RADIUS['pill']}px;padding:8px 14px;font-family:{FONT};font-size:22px;font-weight:900;color:{C['text']}}}
{p} .rt-back{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;opacity:0}}
{p} .rt-prompt{{width:260px;padding:25px;background:{C['surface']};border:2px solid {C['accent']};border-radius:{RADIUS['md']}px;box-shadow:{TK.SHADOW};opacity:0}}
{p} .rt-prompt i{{display:block;height:10px;margin:12px 0;background:{ink_a(.20)};border-radius:{RADIUS['pill']}px}}
{p} .rt-claude{{position:absolute;right:60px;top:40px;width:170px;height:170px;display:flex;align-items:center;justify-content:center;background:{C['surface']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;opacity:.45}}
{p} .rt-cross{{position:absolute;left:10px;opacity:0}} {p} .rt-cross>div{{zoom:.5}}
{p} .rt-prompt b{{font-family:{MONO};font-size:26px;color:{C['accent_hi']}}}
"""
    if variant == "llega":
        face = _reel_face(cid, False, "1,8 M", defer_view=True)
        html = f'<div class="rt-wrap"><div class="rt-slot arrive" id="{cid}-slot"><div id="{cid}-shake">{face}</div></div></div>'
        take, idea, winner = at
        anims = [("cursor-to", f"#{cid}-slot", take, .50, 520, 0),
                 ("cursor-to", f"#{cid}-slot", idea, .35, 700, 0),
                 ("jitter", f"#{cid}-shake", round(idea + .30, 4), .24),
                 ("caret-off", f"#{cid}-view-ref", winner, .01, "1,8 M"),
                 ("stamp", f"#{cid}-view-ref", winner, .25)]
    elif variant == "girar":
        front = _reel_face(cid, False, "1,8 M")
        back = _reel_face(cid, True, "0")
        html = (f'<div class="rt-wrap"><div class="rt-slot" id="{cid}-slot"><div id="{cid}-front">{front}</div>'
                f'<div class="rt-back" id="{cid}-back">{back}</div></div></div>')
        adjust, message = at
        gire = max(.22, round(message - adjust - .03, 4))
        anims = [("flip-out", f"#{cid}-slot", adjust, gire),
                 ("badge-out", f"#{cid}-front", round(adjust + gire - .01, 4), .01),
                 ("chip-in", f"#{cid}-back", round(message - .01, 4), .01),
                 ("flip-in", f"#{cid}-slot", message, .28)]
    else:
        logo, _ = logos.mark("claude", 96, uid=f"{cid}-claude")
        prompt = '<div class="rt-prompt" id="%s-prompt"><b>&gt;_</b><i></i><i></i><i></i></div>' % cid
        cross = (f'<div class="rt-cross" id="{cid}-cross">'
                 f'<div id="{cid}-cross-ref">{_reel_face(cid, False, "1,8 M")}</div>'
                 f'<div class="rt-back" id="{cid}-cross-own">{_reel_face(cid, True, "0")}</div></div>')
        html = f'<div class="rt-wrap">{prompt}<div class="rt-claude" id="{cid}-claude">{logo}</div>{cross}</div>'
        tprompt, toutlier, tclaude = at
        anims = [("drop-in", f"#{cid}-prompt", tprompt, .30),
                 ("chip-in", f"#{cid}-cross", toutlier, .18),
                 ("cursor-to", f"#{cid}-cross", toutlier, .60, 390, 0),
                 ("badge-out", f"#{cid}-cross-ref", tclaude, .01),
                 ("chip-in", f"#{cid}-cross-own", tclaude, .01),
                 ("cursor-to", f"#{cid}-cross", tclaude, .48, 760, 0),
                 ("fade-to", f"#{cid}-claude", tclaude, .32, 1)]
    return css, html, anims


def reel_cascada(cid: str, at: list, lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("reel_cascada", at, 3)
    p, _, max_h = _host(cid, lienzo)
    avatars = "".join(_avatar(f"{cid}-av{i}", "ref", i, 92) for i in range(5))
    columns = []
    for col in range(5):
        thumbs = "".join(f'<span id="{cid}-m{col}-{row}" style="opacity:0">'
                         f'{_miniatura(f"{cid}-t{col}-{row}", col * 5 + row, w=78)}</span>'
                         for row in range(5))
        columns.append(f'<div class="rc-col">{thumbs}</div>')
    css = _shared_css(p) + f"""
{p} .rca-wrap{{width:940px;height:{min(max_h, 1120)}px;display:flex;flex-direction:column;align-items:center;gap:28px}}
{p} .rca-avatars{{width:760px;display:flex;justify-content:space-between}} {p} .rca-grid{{display:flex;gap:74px;height:730px}}
{p} .rc-col{{display:flex;flex-direction:column;gap:9px}} {p} .rc-count{{font-family:{MONO};font-size:82px;font-weight:700;color:{C['accent_hi']}}}
"""
    html = f'<div class="rca-wrap"><div class="rca-avatars">{avatars}</div><div class="rca-grid">{"".join(columns)}</div><div class="rc-count">{_contador(f"{cid}-count", 0)}</div></div>'
    t5, tvideos, trefs = at
    anims = []
    for col in range(4):
        for row in range(5):
            anims.append(("drop-in", f"#{cid}-m{col}-{row}", round(t5 + (col * 5 + row) * .06, 4), .22))
    anims.append(("count-roll", f"#{cid}-count", tvideos, max(.35, trefs - tvideos), 0, 20, ""))
    anims += [("drop-in", f"#{cid}-m4-{row}", round(trefs + row * .06, 4), .22) for row in range(5)]
    return css, html, anims


def ig_grilla(cid: str, variant: str, at: list,
              lienzo: bool = False) -> tuple[str, str, list]:
    variants = {"contar": 2, "respirar": 1, "viral": 2}
    if variant not in variants:
        raise ValueError(f"ig_grilla: variante {variant!r} no existe")
    _need_at("ig_grilla", at, variants[variant])
    p, _, max_h = _host(cid, lienzo)
    # Cinco filas 9:16 + contador: 70 px es el máximo que conserva los
    # 760 px de la banda; el lienzo completo admite 128 px.
    w = 128 if lienzo else 70
    views = [f"{11 + (i * 7) % 4} K" for i in range(25)] if variant in ("respirar", "viral") else [None] * 25
    thumbs = "".join(f'<div class="igr-cell" id="{cid}-cell{i}">{_miniatura(f"{cid}-m{i}", i, views[i], w=w)}</div>'
                     for i in range(25))
    css = _shared_css(p) + f"""
{p} .igr-wrap{{position:relative;width:940px;max-height:{max_h}px;display:flex;flex-direction:column;align-items:center;gap:18px}}
{p} .igr-count{{position:relative;z-index:8;font-family:{MONO};font-size:68px;font-weight:700;color:{C['accent_hi']};transform-origin:50% 50%}}
{p} .igr-grid{{display:grid;grid-template-columns:repeat(5,{w}px);gap:10px;position:relative}}
{p} .igr-cell{{position:relative;transform-origin:50% 50%;{'opacity:.35;' if variant == 'respirar' else ('opacity:0;' if variant == 'contar' else '')}}}
{p} .igr-cell .rm-views{{font-size:11px}} {p} .igr-cell.hero{{z-index:12;filter:drop-shadow(0 20px 60px {shade_a(.70)})}}
{p} .igr-burst{{position:absolute;left:50%;top:50%;width:1px;height:1px;z-index:15}} {p} .igr-icon{{position:absolute;color:{C['alert']};opacity:0;filter:drop-shadow(0 0 18px {C['accent']})}}
"""
    burst = ""
    if variant == "viral":
        names = ("heart-fill", "comment", "share", "heart-fill", "comment", "share", "heart-fill", "comment", "share")
        burst = '<div class="igr-burst">' + "".join(f'<span class="igr-icon" id="{cid}-ic{i}">{_glifo(name, 64)}</span>'
                                                     for i, name in enumerate(names)) + '</div>'
    html = f'<div class="igr-wrap"><div class="igr-count">{_contador(f"{cid}-count", 20 if variant == "contar" else 25)}</div><div class="igr-grid" id="{cid}-grid">{thumbs}{burst}</div></div>'
    if variant == "contar":
        t25, tvideos = at
        anims = [("count-roll", f"#{cid}-count", t25, .45, 20, 25, ""),
                 ("jitter", f"#{cid}-count", round(t25 + .45, 4), .24),
                 ("cam-push", f"#{cid}-count", t25, .35, 1.6, 0)]
        anims += [("chip-in", f"#{cid}-cell{i}", round(tvideos + i * .015, 4), .20) for i in range(25)]
        anims.append(("cursor-to", f"#{cid}-count", tvideos, .35, 0, 18))
    elif variant == "respirar":
        anims = [("fade-to", f"#{cid}-cell{i}", at[0], .50, 1) for i in range(25)]
    else:
        tone, viral = at
        anims = [("cam-push", f"#{cid}-cell12", tone, .50, 3.0, 0)]
        anims += [("fade-to", f"#{cid}-cell{i}", tone, .38, .25) for i in range(25) if i != 12]
        anims += [("count-roll", f"#{cid}-m12-v", viral, .65, 12, 2400, "", " K"),
                  ("caret-off", f"#{cid}-m12-v", round(viral + .67, 4), .01, "2,4 M")]
        coords = ((-250, -220), (0, -300), (230, -210), (-320, 0), (310, 10), (-230, 220), (10, 290), (250, 220), (0, -180))
        for i, (x, y) in enumerate(coords):
            t = round(viral + i * .04, 4)
            anims += [("chip-in", f"#{cid}-ic{i}", t, .18),
                      ("cursor-to", f"#{cid}-ic{i}", t, .35, x, y)]
    return css, html, anims


def _skeleton(cid: str, filled: bool) -> str:
    blocks = []
    for i in range(3):
        lines = "".join(f'<i id="{cid}-line{i}-{j}"></i>' for j in range(3))
        cls = "ge-lines shown" if filled else "ge-lines"
        blocks.append(f'<div class="ge-block"><div class="{cls}">{lines}</div></div>')
    marks = "".join(f'<path id="{cid}-mark{i}" d="M8 {35 + i * 135}h42"/>' for i in range(3))
    return f'<div class="ge-skeleton"><div class="ge-blocks">{"".join(blocks)}</div><svg class="ge-ruler" viewBox="0 0 60 410">{marks}</svg></div>'


def guion_esqueleto(cid: str, variant: str, at: list,
                    lienzo: bool = False) -> tuple[str, str, list]:
    variants = {"voltear": 3, "replicar": 2}
    if variant not in variants:
        raise ValueError(f"guion_esqueleto: variante {variant!r} no existe")
    _need_at("guion_esqueleto", at, variants[variant])
    p, _, max_h = _host(cid, lienzo)
    css = _shared_css(p) + f"""
{p} .ge-wrap{{position:relative;width:940px;height:{min(max_h, 1040)}px;display:flex;align-items:center;justify-content:center;gap:70px}}
{p} .ge-card{{position:relative;width:360px;height:640px;display:flex;align-items:center;justify-content:center;transform-style:preserve-3d}}
{p} .ge-front,{p} .ge-back{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}} {p} .ge-back{{opacity:0}}
{p} .ge-skeleton{{position:relative;width:330px;height:520px;padding:30px;background:{C['surface']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW}}}
{p} .ge-blocks{{display:flex;flex-direction:column;gap:18px}} {p} .ge-block{{height:120px;border:2px dashed {C['text3']};border-radius:{RADIUS['sm']}px;padding:18px}}
{p} .ge-lines{{display:flex;flex-direction:column;gap:12px}} {p} .ge-lines i{{display:block;height:10px;border-radius:{RADIUS['pill']}px;background:{rgba(C['text2'], .30)};width:0}} {p} .ge-lines.shown i{{width:82%}}
{p} .ge-ruler{{position:absolute;right:-62px;top:55px;width:60px;height:410px;fill:none;stroke:{C['accent']};stroke-width:5;stroke-linecap:round}}
{p} .ge-grid{{display:grid;grid-template-columns:repeat(6,62px);gap:9px}} {p} .ge-mini{{width:62px;height:94px;border:2px dashed {C['text3']};border-radius:8px;padding:8px}}
{p} .ge-minilines{{opacity:0}} {p} .ge-minilines i{{display:block;height:6px;margin:9px 0;background:{ink_a(.24)};border-radius:{RADIUS['pill']}px}}
"""
    if variant == "voltear":
        front = _miniatura(f"{cid}-thumb", 8, w=360)
        back = _skeleton(cid, False)
        html = f'<div class="ge-wrap"><div class="ge-card" id="{cid}-card"><div class="ge-front" id="{cid}-front">{front}</div><div class="ge-back" id="{cid}-back">{back}</div></div></div>'
        structure, script, exact = at
        anims = [("flip-out", f"#{cid}-card", structure, .22),
                 ("badge-out", f"#{cid}-front", round(structure + .21, 4), .01),
                 ("chip-in", f"#{cid}-back", round(structure + .22, 4), .01),
                 ("flip-in", f"#{cid}-card", round(structure + .23, 4), .28)]
        for i in range(3):
            for j in range(3):
                anims.append(("grow-x", f"#{cid}-line{i}-{j}", round(script + (i * 3 + j) * .06, 4), .24, 210 - j * 20))
        anims += [("draw", f"#{cid}-mark{i}", round(exact + i * .10, 4), .28) for i in range(3)]
    else:
        minis = "".join(f'<div class="ge-mini"><div class="ge-minilines" id="{cid}-mini{i}"><i></i><i></i><i></i></div></div>' for i in range(24))
        html = f'<div class="ge-wrap"><div id="{cid}-source">{_skeleton(cid, True)}</div><div class="ge-grid">{minis}</div></div>'
        paste, replicas = at
        anims = [("cam-push", f"#{cid}-source", paste, .32, 1.07, -30),
                 ("cursor-to", f"#{cid}-source", replicas, .45, 420, 30)]
        anims += [("chip-in", f"#{cid}-mini{i}", round(replicas + i * .01, 4), .20) for i in range(24)]
    return css, html, anims
