#!/usr/bin/env python3
"""Interfaz literal de ChatGPT y resultados de imagen para la pieza 6.

Todos los componentes devuelven ``(css, html, anims)`` y dejan sus selectores
de animación relativos. Las imágenes permanecen como archivos: ``assets_de``
declara al compilador cuáles debe copiar a ``public/``.
"""

from __future__ import annotations

import logos
import tokens as TK
from mockups import _cursor, _cursor_css
from mockups_plugins import _need_at
from mockups_reels import _host
from tokens import C, FONT, MONO, RADIUS, esc, rgba


_IMAGES = {
    "original": "imagenes-6/original.jpg",
    "blueprint": "imagenes-6/blueprint.jpg",
    "explodedview": "imagenes-6/explodedview.jpg",
    "xray": "imagenes-6/xray.jpg",
    "handwritten": "imagenes-6/handwritten.jpg",
    "stickynotes": "imagenes-6/stickynotes.jpg",
}
_COMMANDS = ("blueprint", "explodedview", "xray", "handwritten")
_REVEALS = ("barrido", "escaneo", "trazo", "despiece")


def _brand() -> dict:
    return TK.BRANDS["chatgpt"]


def _image(clave: str) -> str:
    if clave not in _IMAGES:
        raise ValueError(f"imagen de ChatGPT {clave!r} no existe")
    return _IMAGES[clave]


def _ordered_unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _icon(nombre: str, px: int) -> str:
    paths = {
        "down": '<path d="m7 10 5 5 5-5"/>',
        "plus": '<path d="M12 5v14M5 12h14"/>',
        "close": '<path d="m7 7 10 10M17 7 7 17"/>',
        "up": '<path d="M12 19V5m0 0-6 6m6-6 6 6"/>',
        "lock": ('<rect x="5" y="10" width="14" height="11" rx="3"/>'
                 '<path d="M8 10V7a4 4 0 0 1 8 0v3"/>'),
    }
    if nombre not in paths:
        raise ValueError(f"glifo ChatGPT {nombre!r} no existe")
    return (f'<svg viewBox="0 0 24 24" width="{px}" height="{px}" fill="none" '
            f'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{paths[nombre]}</svg>')


def _ventana(cid: str, w: int, h: int) -> str:
    logo, _ = logos.mark("openai", 34, uid=f"{cid}-openai")
    return (f'<div class="cg-window" id="{cid}-window" '
            f'style="width:{w}px;height:{h}px">'
            f'<div class="cg-head" id="{cid}-head"><span class="cg-logo">{logo}</span>'
            f'<span>ChatGPT</span><span class="cg-chevron">{_icon("down", 26)}</span></div>')


def _campo(cid: str, adjunto: bool = True, hidden_text: str = "") -> str:
    b = _brand()
    attachment = ""
    if adjunto:
        attachment = (f'<span class="cg-attachment" id="{cid}-attachment">'
                      f'<img id="{cid}-attachment-img" src="{_image("original")}" alt=""/>'
                      f'<span class="cg-close">{_icon("close", 14)}</span></span>')
    text = esc(hidden_text)
    caret = '<span class="ccaret"></span>' if hidden_text else ""
    placeholder = "" if hidden_text else "Pregunta lo que quieras"
    return (f'<div class="cg-field" id="{cid}-field">{attachment}'
            f'<span class="cg-plus" id="{cid}-plus">{_icon("plus", 30)}</span>'
            f'<span class="cg-placeholder" id="{cid}-placeholder">{placeholder}</span>'
            f'<span class="cg-command" id="{cid}-command">{text}{caret}</span>'
            f'<span class="cg-send" id="{cid}-send" '
            f'style="background:{b["send_off"]};color:{b["send_fg"]}">'
            f'<span class="cg-send-ring" id="{cid}-send-ring"></span>{_icon("up", 29)}</span>'
            f'</div>')


def _burbuja_usuario(cid: str, comando: str) -> str:
    del comando  # El texto hablado entra después con caret-off; nunca vive adelantado en DOM.
    return (f'<div class="cg-user" id="{cid}-user">'
            f'<img id="{cid}-user-img" src="{_image("original")}" alt=""/>'
            f'<span class="cg-user-bubble"><span id="{cid}-user-command"></span></span>'
            f'</div>')


def _respuesta(cid: str, clave: str) -> str:
    src = _image(clave)
    landscape = clave == "blueprint"
    w, h = (582, 388) if landscape else (260, 390)
    return (f'<div class="cg-answer" id="{cid}-answer">'
            f'<div class="cg-making" id="{cid}-making"><span>Creando imagen</span>'
            f'<i id="{cid}-shimmer"><b></b></i></div>'
            f'<div class="cg-answer-frame" id="{cid}-answer-frame" '
            f'style="width:{w}px;height:{h}px">'
            f'<img class="cg-answer-blur" id="{cid}-answer-blur" src="{src}" alt=""/>'
            f'<span class="cg-answer-veil"></span>'
            f'<img class="cg-answer-sharp" id="{cid}-answer-sharp" src="{src}" alt=""/>'
            f'</div></div>')


def _chat_css(p: str) -> str:
    b = _brand()
    return _cursor_css(p) + f"""
{p} .cg-window{{position:relative;box-sizing:border-box;overflow:hidden;background:{b['bg']};
  border:1px solid {b['line']};border-radius:{RADIUS['xl']}px;box-shadow:{TK.SHADOW};
  color:{b['text']};font-family:{FONT}}}
{p} .cg-head{{height:76px;display:flex;align-items:center;gap:13px;padding:0 28px;
  border-bottom:1px solid {b['line']};font-size:28px;font-weight:600}}
{p} .cg-logo{{display:flex;color:{b['text']}}}
{p} .cg-logo .brandmark svg path{{fill:{b['text']}}}
{p} .cg-chevron{{display:flex;color:{b['text2']}}}
{p} .cg-conversation{{position:absolute;left:34px;right:34px;top:76px;bottom:206px;overflow:hidden}}
{p} .cg-field{{position:absolute;left:39px;right:39px;bottom:18px;height:174px;
  box-sizing:border-box;background:{b['surface']};border:1px solid {b['line']};
  border-radius:34px;box-shadow:0 10px 32px rgba(0,0,0,.22)}}
{p} .cg-focus{{position:absolute;inset:-2px;border:2px solid {b['text2']};
  border-radius:35px;opacity:0;pointer-events:none}}
{p} .cg-attachment{{position:absolute;left:18px;top:12px;width:88px;height:88px;
  border-radius:14px;overflow:hidden;border:1px solid {b['line']};box-shadow:0 4px 14px rgba(0,0,0,.25)}}
{p} .cg-attachment img{{width:100%;height:100%;display:block;object-fit:cover}}
{p} .cg-close{{position:absolute;right:4px;top:4px;width:22px;height:22px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;background:{rgba(b['bg'], .82)};color:{b['text']}}}
{p} .cg-plus{{position:absolute;left:22px;bottom:15px;display:flex;color:{b['text2']}}}
{p} .cg-placeholder,{p} .cg-command{{position:absolute;left:70px;right:92px;bottom:18px;
  height:50px;display:flex;align-items:center;font-size:42px;font-weight:500;line-height:1.1}}
{p} .cg-placeholder{{color:{b['text2']}}}
{p} .cg-command{{color:{b['text']}}}
{p} .cg-send{{position:absolute;right:14px;bottom:12px;width:52px;height:52px;border-radius:50%;
  display:flex;align-items:center;justify-content:center}}
{p} .cg-send-ring{{position:absolute;inset:-10px;border:3px solid {rgba(b['send_bg'], .45)};
  border-radius:50%;opacity:0}}
{p} .cg-scroll{{position:absolute;inset:0}}
{p} .cg-user{{position:absolute;right:4px;top:18px;width:480px;display:flex;flex-direction:column;
  align-items:flex-end;gap:12px;opacity:0}}
{p} .cg-user>img{{width:120px;height:120px;object-fit:cover;border-radius:18px;
  border:1px solid {b['line']}}}
{p} .cg-user-bubble{{max-width:430px;padding:14px 20px;border-radius:24px 8px 24px 24px;
  background:{b['surface']};font-size:36px;font-weight:500;line-height:1.2}}
{p} .cg-answer{{position:absolute;left:2px;top:214px;width:600px;opacity:0}}
{p} .cg-making{{position:relative;width:max-content;overflow:hidden;margin-bottom:12px;
  color:{b['text2']};font-size:22px;font-weight:600}}
{p} .cg-making i{{position:absolute;left:-220px;top:0;width:180px;height:100%;
  display:block}}
{p} .cg-making i b{{position:absolute;inset:0;display:block;
  background:linear-gradient(90deg,transparent,{rgba(b['text'], .45)},transparent);
  transform:skewX(-18deg)}}
{p} .cg-answer-frame{{position:relative;overflow:hidden;border:1px solid {b['line']};
  border-radius:20px;background:{b['surface']};box-shadow:{TK.SHADOW}}}
{p} .cg-answer-frame img{{position:absolute;inset:0;width:100%;height:100%;display:block;object-fit:cover}}
{p} .cg-answer-blur{{filter:blur(28px);transform:scale(1.12)}}
{p} .cg-answer-veil{{position:absolute;inset:0;background:{rgba(b['bg'], .24)}}}
{p} .cg-answer-sharp{{clip-path:inset(0 0 100% 0);will-change:clip-path}}
{p} .cg-prev{{position:absolute;left:12px;top:-226px;width:420px;height:340px;opacity:.55;
  overflow:hidden;border-radius:20px;border:1px solid {b['line']}}}
{p} .cg-prev img{{width:100%;height:100%;object-fit:cover;filter:saturate(.65)}}
{p} .cg-cover{{position:absolute;left:64px;bottom:14px;width:250px;height:46px;
  border-radius:8px;background:{b['send_fg']};z-index:4}}
{p} .ccaret{{display:inline-block;width:3px;height:1.05em;margin-left:3px;vertical-align:-.12em;
  background:currentColor;animation:cg-caret .8s steps(1,end) infinite}}
@keyframes cg-caret{{50%{{opacity:0}}}}
"""


def chatgpt_chat(cid: str, variant: str, at: list, comando: str = "",
                 resultado: str | None = None, previo: str | None = None,
                 lienzo: bool = False, cursor: bool = False) -> tuple[str, str, list]:
    if variant not in ("oculto", "enviar"):
        raise ValueError(f"chatgpt_chat: variante {variant!r} no existe")
    _need_at("chatgpt_chat", at, 2 if variant == "oculto" else 5)
    if variant == "enviar" and (not comando or resultado is None):
        raise ValueError("chatgpt_chat enviar exige comando y resultado")
    if resultado is not None:
        _image(resultado)
    if previo is not None:
        _image(previo)

    p, _, max_h = _host(cid, lienzo)
    h = min(max_h, 920 if lienzo else 740)
    css = _chat_css(p)

    if variant == "oculto":
        hidden = comando[:max(1, (len(comando) + 1) // 2)]
        field = _campo(cid, True, hidden)
        field = field[:-6] + f'<span class="cg-cover" id="{cid}-cover"></span></div>'
        html = (_ventana(cid, 980, h) + field
                + f'<div class="cg-conversation" id="{cid}-conversation"></div></div>')
        anims = [("cursor-to", f"#{cid}-cover", at[1], .38, 330, 0),
                 ("badge-out", f"#{cid}-cover", round(at[1] + .26, 4), .12)]
        return css, html, anims

    assert resultado is not None
    field = _campo(cid, True)
    field = field[:-6] + f'<span class="cg-focus" id="{cid}-focus"></span></div>'
    # `cg-scroll` es lo que ChatGPT hace al llegar la respuesta: la conversación
    # sube y la imagen que se está generando queda entera a la vista.
    conversation = (f'<div class="cg-conversation" id="{cid}-conversation">'
                    f'<div class="cg-scroll" id="{cid}-scroll">'
                    f'{_burbuja_usuario(cid, comando)}{_respuesta(cid, resultado)}')
    if previo:
        conversation += (f'<div class="cg-prev" id="{cid}-prev">'
                         f'<img id="{cid}-prev-img" src="{_image(previo)}" alt=""/></div>')
    conversation += "</div></div>"
    pointer = _cursor(cid) if cursor else ""
    html = _ventana(cid, 980, h) + field + conversation + pointer + "</div>"

    foco, tecleo, envio, respuesta, revelado_fin = at
    anims: list[tuple] = [("chip-in", f"#{cid}-focus", foco, .18)]
    if cursor:
        anims += [("cursor-enter", f"#{cid}-cursor", foco, .28, 390, h - 105),
                  ("click", f"#{cid}-cursor", min(tecleo, foco + .28), .24,
                   f"#{cid}-ring")]
    if tecleo == envio:
        anims.append(("caret-off", f"#{cid}-command", tecleo, .01, comando))
    else:
        anims.append(("type-word", f"#{cid}-command", tecleo,
                      round(envio - tecleo, 4), comando))
    anims += [("badge-out", f"#{cid}-placeholder", tecleo, .12),
              ("chatgpt-send-on", f"#{cid}-send", tecleo, .16),
              ("click", f"#{cid}-send", envio, .25, f"#{cid}-send-ring"),
              ("chatgpt-send-off", f"#{cid}-send", round(envio + .12, 4), .12),
              ("badge-out", f"#{cid}-attachment", envio, .14),
              ("badge-out", f"#{cid}-command", envio, .12),
              ("caret-off", f"#{cid}-user-command", envio, .01, comando),
              ("rise-in", f"#{cid}-user", envio, .24),
              ("rise-in", f"#{cid}-answer", respuesta, .24),
              ("cursor-to", f"#{cid}-scroll", respuesta, .30, 0, -186),
              ("cursor-to", f"#{cid}-shimmer", respuesta,
               max(.12, round(revelado_fin - respuesta, 4)), 440, 0),
              ("wipe-down", f"#{cid}-answer-sharp", respuesta,
               max(.05, round(revelado_fin - respuesta, 4))),
              ("badge-out", f"#{cid}-making", max(respuesta, revelado_fin - .15), .15)]
    return css, html, anims


def _result_css(p: str) -> str:
    b = _brand()
    return f"""
{p} .cg-result-stage{{position:absolute;inset:0;width:1080px;height:1920px;overflow:hidden;
  background:{b['bg']};font-family:{FONT}}}
{p} .cg-result-camera{{position:absolute;inset:0;transform-origin:50% 50%;will-change:transform}}
{p} .cg-result-main,{p} .cg-result-bg{{position:absolute;display:block;object-fit:cover}}
{p} .cg-result-main{{inset:0;width:100%;height:100%;filter:blur(14px)}}
{p} .cg-result-bg{{inset:-50px;width:1180px;height:2020px;filter:blur(36px);transform:scale(1.08)}}
{p} .cg-result-shade{{position:absolute;inset:0;background:{rgba(b['bg'], .55)}}}
{p} .cg-result-landscape{{position:absolute;left:0;top:540px;width:1080px;height:720px;
  object-fit:contain;background:{b['bg']};border-top:1px solid {b['line']};
  border-bottom:1px solid {b['line']};box-shadow:{TK.SHADOW};filter:blur(14px)}}
{p} .cg-result-label{{position:absolute;left:50%;top:150px;transform:translateX(-50%);
  padding:14px 24px;border-radius:{RADIUS['pill']}px;background:{rgba(b['surface'], .88)};
  border:1px solid {b['line']};color:{b['text']};font-size:30px;font-weight:500;
  box-shadow:{TK.SHADOW};white-space:nowrap}}
{p} .cg-light{{position:absolute;left:-300px;top:-180px;width:260px;height:2300px;
  mix-blend-mode:screen}}
{p} .cg-light i{{position:absolute;inset:0;display:block;transform:rotate(16deg);
  background:linear-gradient(90deg,transparent,{rgba(b['text'], .22)},transparent)}}
{p} .cg-scan{{position:absolute;left:0;right:0;bottom:120px;height:4px;opacity:0;background:{b['text']};
  box-shadow:0 0 12px {b['text']},0 0 34px {rgba(b['text'], .65)}}}
{p} .cg-ink-mask{{position:absolute;inset:0;background:{C['surface']}}}
{p} .cg-strips{{position:absolute;inset:0;filter:blur(14px)}}
{p} .cg-strip{{position:absolute;left:0;width:100%;height:33.4%;overflow:hidden}}
{p} .cg-strip img{{position:absolute;left:0;width:1080px;height:1920px;object-fit:cover}}
"""


def imagen_resultado(cid: str, clave: str, at: list, comando: str = "",
                     revelado: str = "barrido", lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("imagen_resultado", at, 2)
    src = _image(clave)
    if revelado not in _REVEALS:
        raise ValueError(f"imagen_resultado: revelado {revelado!r} no existe")
    p, _, _ = _host(cid, lienzo)
    css = _result_css(p)

    if revelado == "despiece":
        strips = []
        for i in range(3):
            top = round(i * 33.3333, 4)
            strips.append(
                f'<span class="cg-strip" id="{cid}-strip{i}" '
                f'style="top:{top}%">'
                f'<img id="{cid}-strip-img{i}" src="{src}" alt="" '
                f'style="top:-{i * 640}px"/></span>')
        image_html = f'<div class="cg-strips" id="{cid}-strips">{"".join(strips)}</div>'
    elif clave == "blueprint":
        image_html = (f'<img class="cg-result-bg" id="{cid}-bg" src="{src}" alt=""/>'
                      f'<span class="cg-result-shade" id="{cid}-shade"></span>'
                      f'<img class="cg-result-landscape" id="{cid}-image" src="{src}" alt=""/>')
    else:
        image_html = f'<img class="cg-result-main" id="{cid}-image" src="{src}" alt=""/>'

    label = (f'<span class="cg-result-label" id="{cid}-label">{esc(comando)}</span>'
             if comando else "")
    gesture = ""
    if revelado == "barrido":
        gesture = f'<span class="cg-light" id="{cid}-gesture"><i></i></span>'
    elif revelado == "escaneo":
        gesture = f'<span class="cg-scan" id="{cid}-gesture"></span>'
    elif revelado == "trazo":
        gesture = f'<span class="cg-ink-mask" id="{cid}-gesture"></span>'

    html = (f'<div class="cg-result-stage" id="{cid}-stage">'
            f'<div class="cg-result-camera" id="{cid}-camera">{image_html}{gesture}</div>'
            f'{label}</div>')
    entrada, gesto = at
    anims: list[tuple] = [("cam-push", f"#{cid}-camera", entrada, 1.4, 1.05, 0)]
    blur_target = f"#{cid}-image" if revelado != "despiece" else f"#{cid}-strips"
    anims.append(("blur-to", blur_target, entrada, .30, 0))
    if revelado == "barrido":
        anims.append(("cursor-to", f"#{cid}-gesture", gesto, .60, 1380, 0))
    elif revelado == "escaneo":
        anims += [("fade-to", f"#{cid}-gesture", gesto, .06, 1),
                  ("cursor-to", f"#{cid}-gesture", gesto, .70, 0, -1620),
                  ("badge-out", f"#{cid}-gesture", round(gesto + .62, 4), .12)]
    elif revelado == "trazo":
        anims.append(("cursor-to", f"#{cid}-gesture", entrada,
                      max(.05, round(gesto - entrada, 4)), 1120, 0))
    else:
        for i, shift in enumerate((-40, 40, -40)):
            anims.append(("settle-y", f"#{cid}-strip{i}", entrada, .45, shift))
    return css, html, anims


def parpadeo_estados(cid: str, at: list,
                     claves: tuple[str, ...] = ("blueprint", "explodedview", "xray"),
                     lienzo: bool = True) -> tuple[str, str, list]:
    _need_at("parpadeo_estados", at, 2)
    if len(claves) != 3:
        raise ValueError("parpadeo_estados: claves debe traer tres estados")
    for clave in claves:
        _image(clave)
    p, _, _ = _host(cid, lienzo)
    b = _brand()
    css = f"""
{p} .cg-blink{{position:absolute;inset:0;width:1080px;height:1920px;overflow:hidden;background:{b['bg']}}}
{p} .cg-blink img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}}
{p} .cg-blink-state{{opacity:0}}
{p} .cg-blink-light{{position:absolute;left:-300px;top:-180px;width:260px;height:2300px;
  mix-blend-mode:screen}}
{p} .cg-blink-light i{{position:absolute;inset:0;display:block;transform:rotate(16deg);
  background:linear-gradient(90deg,transparent,{rgba(b['text'], .22)},transparent)}}
{p} .cg-flash{{position:absolute;inset:0;background:{rgba(b['text'], .35)};opacity:0}}
"""
    states = "".join(f'<img class="cg-blink-state" id="{cid}-state{i}" '
                     f'src="{_image(clave)}" alt=""/>'
                     for i, clave in enumerate(claves))
    html = (f'<div class="cg-blink" id="{cid}-blink">'
            f'<img id="{cid}-original" src="{_image("original")}" alt=""/>'
            f'{states}<span class="cg-blink-light" id="{cid}-light"><i></i></span>'
            f'<span class="cg-flash" id="{cid}-flash"></span></div>')
    imagen, completo = at
    anims: list[tuple] = [("cursor-to", f"#{cid}-light", imagen, .60, 1380, 0),
                          ("fade-to", f"#{cid}-original", completo, .001, 0)]
    step = .2067  # 0.14 s de estado + dos frames completos de destello.
    for i in range(3):
        t = round(completo + i * step, 4)
        anims += [("fade-to", f"#{cid}-state{i}", t, .001, 1),
                  # El estado sigue debajo del destello: sin él, esos dos
                  # frames serían un velo sobre el suelo vacío.
                  ("fade-to", f"#{cid}-state{i}", round(t + step, 4), .001, 0),
                  ("fade-to", f"#{cid}-flash", round(t + .14, 4), .001, .35),
                  ("fade-to", f"#{cid}-flash", round(t + step, 4), .001, 0)]
    anims.append(("fade-to", f"#{cid}-original",
                  round(completo + 3 * step, 4), .001, 1))
    return css, html, anims


def lista_codigos(cid: str, at: list, lienzo: bool = False) -> tuple[str, str, list]:
    _need_at("lista_codigos", at, 4)
    p, _, max_h = _host(cid, lienzo)
    b = _brand()
    h = min(max_h, 720)
    css = f"""
{p} .cg-list{{position:relative;width:940px;height:{h}px;padding:30px 20px;box-sizing:border-box;
  border-radius:{RADIUS['xl']}px;font-family:{FONT};color:{b['text']}}}
{p} .cg-list-fill{{position:absolute;inset:0;border-radius:{RADIUS['xl']}px;background:{b['surface']};
  border:1px solid {b['line']};box-shadow:{TK.SHADOW};opacity:0}}
{p} .cg-list-border{{position:absolute;inset:0;width:940px;height:{h}px;overflow:visible}}
{p} .cg-row{{position:relative;height:112px;margin-bottom:10px;padding:4px 20px 4px 4px;
  display:flex;align-items:center;gap:24px;border-radius:20px;background:{b['surface']};
  border:1px solid {b['line']};z-index:2}}
{p} .cg-row-thumb{{width:104px;height:104px;object-fit:cover;border-radius:14px;opacity:0}}
{p} .cg-row-code{{flex:1;min-width:0;padding:16px 22px;border-radius:{RADIUS['pill']}px;
  background:{C['surface2']};font-family:{MONO};font-size:34px;font-weight:700;line-height:1.1}}
{p} .cg-secret{{opacity:0}}
{p} .cg-secret-thumb{{position:relative;width:104px;height:104px;overflow:hidden;border-radius:14px}}
{p} .cg-secret-thumb img{{width:100%;height:100%;object-fit:cover;filter:blur(10px);transform:scale(1.08)}}
{p} .cg-secret-veil{{position:absolute;inset:0;background:{rgba(b['bg'], .28)}}}
{p} .cg-bars{{flex:1;padding:22px;border-radius:{RADIUS['pill']}px;background:{C['surface2']};
  display:flex;gap:12px;align-items:center}}
{p} .cg-bars i{{height:13px;border-radius:{RADIUS['pill']}px;background:{rgba(b['text2'], .30)}}}
{p} .cg-bars i:nth-child(1){{width:120px}}{p} .cg-bars i:nth-child(2){{width:82px}}
{p} .cg-bars i:nth-child(3){{width:104px}}{p} .cg-lock{{display:flex;color:{b['text2']}}}
"""
    rows = []
    for i, key in enumerate(_COMMANDS):
        rows.append(f'<div class="cg-row" id="{cid}-row{i}">'
                    f'<img class="cg-row-thumb" id="{cid}-thumb{i}" src="{_image(key)}" alt=""/>'
                    f'<span class="cg-row-code" id="{cid}-code{i}"></span></div>')
    rows.append(f'<div class="cg-row cg-secret" id="{cid}-secret">'
                f'<span class="cg-secret-thumb"><img id="{cid}-secret-img" '
                f'src="{_image("stickynotes")}" alt=""/><i class="cg-secret-veil"></i></span>'
                f'<span class="cg-bars"><i></i><i></i><i></i></span>'
                f'<span class="cg-lock" id="{cid}-lock">{_icon("lock", 40)}</span></div>')
    html = (f'<div class="cg-list" id="{cid}-list"><span class="cg-list-fill" id="{cid}-fill"></span>'
            f'<svg class="cg-list-border" viewBox="0 0 940 {h}" aria-hidden="true">'
            f'<rect id="{cid}-border" x="3" y="3" width="934" height="{h - 6}" rx="{RADIUS["xl"]}" '
            f'fill="none" stroke="{C["accent"]}" stroke-width="4"/></svg>{"".join(rows)}</div>')
    todos, codigos, ocultos, lista = at
    anims: list[tuple] = []
    for i, key in enumerate(_COMMANDS):
        td = round(todos + i * .08, 4)
        tt = round(codigos + i * .10, 4)
        command = f"/{key}"
        anims += [("drop-in", f"#{cid}-thumb{i}", td, .24),
                  ("type-word", f"#{cid}-code{i}", tt, .34, command),
                  # Un frame de aire: `emit_anim` cuantiza el inicio a 30 fps
                  # y el último set de `type-word` cae en t + duración. Si el
                  # caret-off comparte ese borde, el redondeo puede dejar el
                  # último caret como estado final del seek.
                  ("caret-off", f"#{cid}-code{i}", round(tt + .38, 4), .01, command)]
    anims += [("rise-in", f"#{cid}-secret", ocultos, .24),
              ("stamp", f"#{cid}-lock", ocultos, .20),
              ("chip-in", f"#{cid}-fill", lista, .18),
              ("draw", f"#{cid}-border", lista, .44)]
    return css, html, anims


def assets_de(fn_name: str, kw: dict) -> list[str]:
    """Rutas relativas a ``assets/`` que una llamada va a referenciar."""
    if fn_name == "chatgpt_chat":
        variant = kw.get("variant")
        if variant not in ("oculto", "enviar"):
            raise ValueError(f"assets_de: variante {variant!r} no existe")
        out = [_image("original")]
        if variant == "enviar":
            if kw.get("resultado") is None:
                raise ValueError("assets_de: chatgpt_chat enviar exige resultado")
            out.append(_image(kw["resultado"]))
            if kw.get("previo") is not None:
                out.append(_image(kw["previo"]))
        return _ordered_unique(out)
    if fn_name == "imagen_resultado":
        return [_image(kw.get("clave"))]
    if fn_name == "parpadeo_estados":
        claves = kw.get("claves", ("blueprint", "explodedview", "xray"))
        if len(claves) != 3:
            raise ValueError("assets_de: parpadeo_estados exige tres claves")
        return _ordered_unique([_image("original"), *(_image(k) for k in claves)])
    if fn_name == "lista_codigos":
        return [_image(k) for k in (*_COMMANDS, "stickynotes")]
    raise ValueError(f"assets_de: componente {fn_name!r} no existe")
