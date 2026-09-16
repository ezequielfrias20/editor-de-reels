#!/usr/bin/env python3
"""Librería de componentes visuales — la técnica «interfaz» del sistema.

Cada componente devuelve la misma terna:

    (css, html, anims)

    · css   — reglas ya prefijadas con el selector del host, para que dos
              componentes en la misma composición no se pisen.
    · html  — el marcado.
    · anims — [(kind, selector_relativo, offset_s, dur_s, *extra)], donde el
              offset es RELATIVO al inicio del visual; el generador le suma el
              tiempo absoluto.

Todo está dibujado con `tokens.py`: grafito profundo, superficies flotando con
hairline claro y sombra ancha, tipografía Inter/JetBrains Mono y un único
acento violeta por frame.

DOCTRINA DE ESTOS MOCKUPS
- **Nunca una captura de pantalla real dibujada a mano.** O es el producto de
  verdad (`screen_overlay` sobre la grabación) o es un mockup declarado.
- **Border radius generoso + sombra suave + hairline.** Es lo que separa una
  UI premium de una caja.
- **Perspectiva 2.5D con moderación**: solo el objeto protagonista, y siempre
  aterrizando en plano (`perspective-to-flat`). Un mockup que se queda torcido
  se lee como plantilla de plantilla.
- Nada se centra con `transform: translate(-50%,-50%)` si GSAP lo va a animar:
  en cuanto recibe un `y` o un `scale`, GSAP toma el transform y descarta el
  centrado. Se centra con **flex** o con left/top absolutos.

Se diseñan sobre un lienzo de 1080×1920 (REEL). Las medidas son absolutas en px
porque el visual ocupa el lienzo entero; para 16:9 se escalan desde el host.
"""

import logos
from tokens import (C, FILL, FONT, GLOW, LINE, LINE_HI, MONO, RADIUS, SHADOW,
                    SHADOW_LIFT, esc)

# Ancho de trabajo de un mockup a pantalla completa en REEL.
BOARD_W = 980


def _cursor(cid: str, ring_color: str | None = None) -> str:
    """Cursor macOS sobredimensionado. Sobre fondo oscuro va en blanco con
    filete grafito: al revés desaparece encima de cualquier UI clara."""
    ring = ring_color or C["violet"]
    return (f'<div class="bigcursor" id="{cid}-cursor">'
            f'<span class="tap-ring" id="{cid}-ring" style="border-color:{ring}"></span>'
            '<svg viewBox="0 0 80 96" aria-hidden="true"><path '
            f'fill="#FFFFFF" stroke="{C["bg"]}" stroke-width="6" '
            'stroke-linejoin="round" d="M8 7v70l18-17 14 29 17-8-14-28h27z"/></svg></div>')


def _cursor_css(p: str) -> str:
    return f"""
{p} .bigcursor{{position:absolute;left:0;top:0;width:76px;height:92px;z-index:20;opacity:0}}
{p} .bigcursor svg{{width:76px;height:92px;filter:drop-shadow(0 10px 14px rgba(0,0,0,.6))}}
{p} .tap-ring{{position:absolute;left:-22px;top:-22px;width:74px;height:74px;
  border-radius:50%;border:6px solid {C['violet']};opacity:0}}"""


# ── chrome de navegador ───────────────────────────────────────────────────────
def browser_chrome(url: str, brand: str = "") -> str:
    """La barra superior de un navegador. Se usa como cabecera de cualquier
    mockup que represente una app web — que es lo que el espectador reconoce
    al instante como «esto es un producto real»."""
    dots = "".join(f'<i style="background:{c}"></i>'
                   for c in ("#FF5F57", "#FEBC2E", "#28C840"))
    tag = f'<span class="bchip">{esc(brand)}</span>' if brand else ""
    return (f'<div class="bchrome"><div class="bdots">{dots}</div>'
            f'<div class="burl">{esc(url)}</div>{tag}</div>')


def browser_frame(cid: str, rect: tuple[int, int, int, int], url: str,
                  brand: str = "") -> tuple[str, str, list]:
    """Chrome de navegador alrededor de un <video> colocado en `rect`.

    El <video> va suelto en el stage (media anidada en un elemento temporizado
    se congela), así que el marco no puede CONTENERLO: se dibuja alrededor.
    La barra va justo encima del rect y el aro lo rodea; el borde pisa el filo
    del video, que es exactamente lo que hace que se lea como una sola tarjeta.
    """
    x, y, w, h = rect
    CH = 74                       # alto de la barra
    p = f'.viz[data-viz-id="{cid}"]'
    css = browser_css(p) + f"""
{p} .bframe{{position:absolute;left:{x}px;top:{y - CH}px;width:{w}px;height:{CH}px;
  border-radius:{RADIUS['lg']}px {RADIUS['lg']}px 0 0;overflow:hidden;
  border:1px solid {LINE};border-bottom:0;z-index:10;opacity:0}}
{p} .bring{{position:absolute;left:{x}px;top:{y - CH}px;width:{w}px;height:{h + CH}px;
  border:1px solid {LINE};border-radius:{RADIUS['lg']}px;pointer-events:none;
  box-shadow:{SHADOW_LIFT};z-index:11;opacity:0}}"""
    html = (f'<div class="bframe" id="{cid}-chrome">{browser_chrome(url, brand)}</div>'
            f'<div class="bring" id="{cid}-ring2"></div>')
    anims = [("chip-in", f"#{cid}-chrome", .02, .30),
             ("chip-in", f"#{cid}-ring2", .02, .30)]
    return css, html, anims


def screen_panel(cid: str, rect: tuple[int, int, int, int],
                 label: str = "") -> tuple[str, str, list]:
    """Panel elevado alrededor del producto real — SIN chrome de navegador.

    El tratamiento por defecto de una grabación de producto. La barra de
    navegador de `browser_frame` declara «esto es real», pero cuesta 74 px de
    alto y llena el frame de pestañas y de una URL que nadie lee; en 9:16 ese
    alto sale directamente del tamaño de la interfaz, que es lo único que el
    espectador necesita ver. Aquí la tarjeta se sostiene con lo mismo que el
    resto del sistema: hairline claro y sombra ancha (§3), sin nada que leer.

    `label` es un chip mono opcional, para nombrar la vista del producto
    cuando el HUD ya está ocupado. Vacío por defecto: el HUD basta.
    """
    x, y, w, h = rect
    p = f'.viz[data-viz-id="{cid}"]'
    chip = ""
    css = f"""
{p} .spring{{position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;
  border:1px solid {LINE_HI};border-radius:{RADIUS['lg']}px;pointer-events:none;
  box-shadow:{SHADOW_LIFT};z-index:11;opacity:0}}"""
    if label:
        css += f"""
{p} .splabel{{position:absolute;left:{x + 22}px;top:{y - 58}px;
  font-family:{MONO};font-weight:700;font-size:24px;letter-spacing:.14em;
  color:{C['text3']};text-transform:uppercase;z-index:12;opacity:0}}"""
        chip = f'<div class="splabel" id="{cid}-splabel">{esc(label)}</div>'
    html = f'<div class="spring" id="{cid}-spring"></div>{chip}'
    anims = [("chip-in", f"#{cid}-spring", .02, .30)]
    if label:
        anims.append(("slide-in", f"#{cid}-splabel", .06, .30))
    return css, html, anims


def browser_css(p: str) -> str:
    return f"""
{p} .bchrome{{display:flex;align-items:center;gap:18px;height:74px;padding:0 24px;
  background:{C['surface2']};border-bottom:1px solid {LINE}}}
{p} .bdots{{display:flex;gap:11px}}
{p} .bdots i{{width:17px;height:17px;border-radius:50%;display:block}}
{p} .burl{{flex:1;height:44px;border-radius:{RADIUS['pill']}px;background:{C['bg']};
  border:1px solid {LINE};display:flex;align-items:center;padding:0 22px;
  font-family:{MONO};font-size:22px;color:{C['text3']};overflow:hidden;white-space:nowrap}}
{p} .bchip{{font-family:{MONO};font-weight:700;font-size:19px;letter-spacing:.14em;
  color:{C['violet_hi']};background:{FILL['violet']};border-radius:{RADIUS['pill']}px;
  padding:8px 16px;white-space:nowrap}}"""


# ── HUD ───────────────────────────────────────────────────────────────────────
def hud(cid: str, label: str, corner: str = "01") -> tuple[str, str, list]:
    """Etiqueta de contexto del visual. Minimal: una pastilla mono a la
    izquierda con punto violeta y un índice a la derecha.

    Los corchetes de encuadre del sistema anterior se han quitado a propósito:
    son lenguaje de cámara retro y aquí compiten con la UI del producto.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    # el ancho de la pastilla de la izquierda, para colocar el tick a su lado
    left_tick = 44 + 40 + round(len(label) * 15.5) + 32
    css = f"""
{p} .hud{{position:absolute;inset:0;pointer-events:none;z-index:30}}
{p} .hlabel{{position:absolute;left:44px;top:96px;display:flex;align-items:center;gap:12px;
  font-family:{MONO};font-weight:700;font-size:23px;letter-spacing:.16em;
  color:{C['text2']};background:rgba(22,24,31,.92);border:1px solid {LINE};
  border-radius:{RADIUS['pill']}px;padding:11px 20px;white-space:nowrap;opacity:0}}
{p} .hlabel s{{width:11px;height:11px;border-radius:50%;background:{C['violet']};
  display:block;text-decoration:none;flex:0 0 11px}}
{p} .htick{{position:absolute;left:{left_tick}px;top:96px;
  font-family:{MONO};font-weight:700;font-size:21px;letter-spacing:.18em;
  color:{C['text3']};background:rgba(22,24,31,.92);border:1px solid {LINE};
  border-radius:{RADIUS['pill']}px;padding:11px 18px;white-space:nowrap;opacity:0}}"""
    html = (f'<div class="hud">'
            f'<div class="hlabel" id="{cid}-hl"><s></s>{esc(label)}</div>'
            f'<div class="htick" id="{cid}-ht">{esc(corner)}</div></div>')
    anims = [("slide-in", f"#{cid}-hl", 0.16, 0.32),
             ("slide-in", f"#{cid}-ht", 0.24, 0.30)]
    return css, html, anims


# ── tres sistemas desconectados ───────────────────────────────────────────────
def app_switch(cid: str, apps: list[tuple[str, str]], brand: str,
               switch_at: list[float],
               alert_at: float | None = None) -> tuple[str, str, list]:
    """Tres herramientas AISLADAS. La desconexión se dibuja: entre tarjeta y
    tarjeta hay un conector roto (dos muñones y un hueco), no solo un gap.
    Eso es lo que convierte «tres apps» en «tres problemas» sin decirlo.

    Cada tarjeta ENTRA en la palabra que la nombra (`switch_at`), no antes.
    Tenerlas las tres desde el primer frame parece más limpio, pero adelanta el
    guion: el espectador lee «Excel» dos segundos antes de que él lo diga, y
    cuando llega la palabra ya no pasa nada en pantalla. El conector roto de
    cada hueco aparece con la tarjeta que lo cierra.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    tiles = []
    for i, (slug, label) in enumerate(apps):
        if slug == "erp":
            mk = f'<span class="erpmark">POS</span>'
            ratio = 99.0
        else:
            mk, ratio = logos.mark(slug, 104, "brand" if slug == brand else "mono")
        # `ratio` es None cuando la marca es vendorizada y transparente (sin
        # tile propio, p.ej. animejs, kokonutui): no hay tile que se pueda
        # perder contra el fondo de la tarjeta, así que la pregunta de este
        # gate no aplica. No se bloquea la marca por algo que no le
        # corresponde medir, y tampoco se inventa un ratio.
        if ratio is not None and ratio < 3:
            raise ValueError(f"{slug}: contraste de logo insuficiente ({ratio:.2f}:1)")
        tiles.append(
            f'<div class="apptile" id="{cid}-app{i}">'
            f'<div class="appicon">{mk}</div>'
            f'<div class="appname">{esc(label)}</div>'
            f'<div class="appstate"><s></s>AISLADO</div></div>')
    # conectores rotos entre las tres tarjetas
    breaks = "".join(
        f'<div class="brk" id="{cid}-brk{i}" style="left:{300 + i * 312}px"></div>'
        for i in range(2))
    css = f"""
{p} .appboard{{position:relative;width:{BOARD_W}px;padding:38px 30px 34px;
  background:{C['surface']};border:1px solid {LINE};border-radius:{RADIUS['xl']}px;
  box-shadow:{SHADOW_LIFT}}}
{p} .apphead{{display:flex;align-items:center;justify-content:space-between;
  margin-bottom:30px;font-family:{MONO};font-weight:700;font-size:22px;
  letter-spacing:.16em;color:{C['text3']}}}
{p} .apphead b{{color:{C['alert']};font-weight:700}}
{p} .appline{{display:flex;gap:22px;align-items:stretch;position:relative}}
{p} .apptile{{flex:1;height:400px;background:{C['surface2']};border:1px solid {LINE};
  border-radius:{RADIUS['lg']}px;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:26px;box-shadow:{SHADOW};position:relative;opacity:0}}
{p} .appicon{{width:132px;height:132px;border-radius:{RADIUS['lg']}px;background:{C['bg']};
  border:1px solid {LINE};display:flex;align-items:center;justify-content:center}}
{p} .brandmark{{display:block}}{p} .brandmark svg{{width:100%;height:100%;display:block}}
{p} .erpmark{{font-family:{MONO};font-weight:700;font-size:34px;letter-spacing:.06em;
  color:{C['violet_hi']}}}
{p} .appname{{font-family:{FONT};font-weight:800;font-size:38px;letter-spacing:-.02em;
  color:{C['text']};text-align:center}}
{p} .appstate{{display:flex;align-items:center;gap:10px;font-family:{MONO};
  font-weight:700;font-size:19px;letter-spacing:.14em;color:{C['text3']}}}
{p} .appstate s{{width:9px;height:9px;border-radius:50%;background:{C['alert']};
  display:block;text-decoration:none}}
/* conector ROTO: dos muñones y un hueco. La desconexión se ve, no se explica. */
{p} .brk{{position:absolute;top:198px;width:22px;height:5px;border-radius:3px;
  background:rgba(255,90,90,.65);opacity:0}}
{p} .brk:before,{p} .brk:after{{content:'';position:absolute;top:0;width:22px;height:5px;
  border-radius:3px;background:rgba(255,90,90,.65)}}
{p} .brk:before{{left:-42px}}{p} .brk:after{{left:42px}}
{p} .alertbar{{margin-top:30px;background:{FILL['alert']};border:1px solid rgba(255,90,90,.45);
  color:{C['alert']};font-family:{FONT};font-weight:900;font-size:40px;letter-spacing:-.02em;
  text-align:center;padding:24px;border-radius:{RADIUS['md']}px;opacity:0}}"""
    html = (f'<div class="appboard" id="{cid}-board">'
            f'<div class="apphead"><span>3 HERRAMIENTAS</span><b>0 CONEXIONES</b></div>'
            f'<div class="appline">{"".join(tiles)}{breaks}</div>'
            + (f'<div class="alertbar" id="{cid}-alert">= 3 problemas</div>'
               if alert_at is not None else "")
            + '</div>')
    anims = [("rise-in", f"#{cid}-board", .02, .46)]
    # cada herramienta se SELLA en su palabra; el conector roto llega detrás
    for i, at in enumerate(switch_at):
        if i >= len(apps):
            break
        anims.append(("stamp", f"#{cid}-app{i}", at, .38))
        if i:
            anims.append(("chip-in", f"#{cid}-brk{i-1}", at + .22, .26))
    if alert_at is not None:
        anims.append(("alert-hit", f"#{cid}-alert", alert_at, .44))
    return css, html, anims


# ── mapa de conexiones del ERP ────────────────────────────────────────────────
def connection_map(cid: str, nodes: list[str], draw_at: list[float],
                   hub: str = "ERP") -> tuple[str, str, list]:
    """Núcleo + módulos. Cada línea se DIBUJA al nombrarse el módulo, así que
    el gráfico se construye al ritmo del habla en vez de aparecer entero."""
    p = f'.viz[data-viz-id="{cid}"]'
    pts = [(168, 148), (490, 92), (812, 148), (120, 430),
           (860, 430), (250, 712), (730, 712)]
    cx, cy = 490, 430
    paths, cards = [], []
    for i, (label, (x, y)) in enumerate(zip(nodes, pts)):
        paths.append(f'<path id="{cid}-line{i}" d="M {cx} {cy} L {x} {y}"/>')
        cards.append(
            f'<div class="mapnode" id="{cid}-node{i}" style="left:{x-118}px;top:{y-52}px">'
            f'<s></s>{esc(label)}</div>')
    css = f"""
{p} .mapboard{{position:relative;width:{BOARD_W}px;height:860px;background:{C['surface']};
  border:1px solid {LINE};border-radius:{RADIUS['xl']}px;box-shadow:{SHADOW_LIFT};
  background-image:radial-gradient(circle at 50% 50%,{FILL['violet']} 0%,transparent 58%)}}
{p} .maplines{{position:absolute;inset:0;width:100%;height:100%}}
{p} .maplines path{{fill:none;stroke:{C['violet']};stroke-width:5;stroke-linecap:round}}
{p} .maphub{{position:absolute;left:{cx-115}px;top:{cy-115}px;width:230px;height:230px;
  border-radius:{RADIUS['xl']}px;background:{C['violet']};color:#FFFFFF;
  display:flex;align-items:center;justify-content:center;
  font-family:{FONT};font-weight:900;font-size:66px;letter-spacing:-.03em;
  box-shadow:{GLOW},{SHADOW_LIFT};z-index:4}}
{p} .mapnode{{position:absolute;width:236px;height:104px;background:{C['surface2']};
  border:1px solid {LINE_HI};border-radius:{RADIUS['md']}px;display:flex;align-items:center;
  justify-content:center;gap:13px;text-align:center;padding:0 14px;
  font-family:{FONT};font-weight:700;font-size:26px;letter-spacing:-.01em;
  color:{C['text']};z-index:5;opacity:0;box-shadow:{SHADOW}}}
{p} .mapnode s{{width:11px;height:11px;border-radius:50%;background:{C['go']};
  display:block;text-decoration:none;flex:0 0 11px}}"""
    html = (f'<div class="mapboard" id="{cid}-map">'
            f'<svg class="maplines" viewBox="0 0 {BOARD_W} 860">{"".join(paths)}</svg>'
            f'<div class="maphub" id="{cid}-hub">{esc(hub)}</div>'
            f'{"".join(cards)}</div>')
    anims = [("rise-in", f"#{cid}-map", .02, .46),
             ("punch", f"#{cid}-hub", .16, .44)]
    for i, at in enumerate(draw_at):
        if i >= len(nodes):
            break
        anims += [("draw", f"#{cid}-line{i}", at, .30),
                  ("chip-in", f"#{cid}-node{i}", at + .16, .30)]
    return css, html, anims


# ── overlay sobre la grabación real del producto ──────────────────────────────
def screen_overlay(cid: str, clicks: list[tuple[float, int, int, str]],
                   boxes: list[tuple[float, float, int, int, int, int]] | None = None,
                   ) -> tuple[str, str, list]:
    """Cursor, clic, etiqueta y caja delimitadora sobre el producto real.

    `clicks` = [(t, x, y, etiqueta)] · `boxes` = [(t_in, t_out, x, y, w, h)].
    La caja delimitadora es lo que dirige la mirada al punto exacto que se
    está nombrando: sin ella el espectador barre la pantalla entera y se pierde
    la frase.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    boxes = boxes or []
    badges = "".join(
        f'<div class="scbadge" id="{cid}-badge{i}" '
        f'style="left:{max(44, min(x - 100, 720))}px;top:{max(150, y - 118)}px">'
        f'{esc(label)}</div>'
        for i, (_, x, y, label) in enumerate(clicks))
    bxs = "".join(
        f'<div class="scbox" id="{cid}-box{i}" '
        f'style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>'
        for i, (_, _, x, y, w, h) in enumerate(boxes))
    css = f"""
{p} .screenfx{{position:absolute;inset:0;z-index:12}}
{p} .scbadge{{position:absolute;background:{C['violet']};color:#FFFFFF;
  border-radius:{RADIUS['pill']}px;padding:13px 24px;font-family:{MONO};font-weight:700;
  font-size:24px;letter-spacing:.10em;opacity:0;white-space:nowrap;
  box-shadow:0 10px 30px rgba(0,0,0,.55);z-index:16}}
{p} .scbox{{position:absolute;border:5px solid {C['violet']};border-radius:{RADIUS['md']}px;
  box-shadow:0 0 0 9999px rgba(11,12,16,.55);opacity:0;z-index:14}}
{_cursor_css(p)}"""
    html = f'<div class="screenfx">{bxs}{badges}{_cursor(cid)}</div>'
    anims = []
    for i, (t_in, t_out, *_rest) in enumerate(boxes):
        anims.append(("box-in", f"#{cid}-box{i}", t_in, .38))
        anims.append(("badge-out", f"#{cid}-box{i}", t_out, .26))
    for i, (at, x, y, _) in enumerate(clicks):
        anims.append(("cursor-enter" if i == 0 else "cursor-to",
                      f"#{cid}-cursor", max(.06, at - .32), .32, x, y))
        anims.append(("click", f"#{cid}-cursor", at, .26, f"#{cid}-ring"))
        anims.append(("chip-in", f"#{cid}-badge{i}", at, .30))
        hold = .40 if i == len(clicks) - 1 else .95
        anims.append(("badge-out", f"#{cid}-badge{i}", at + hold, .24))
    if clicks:
        # El cursor SE VA después del último clic. Si se queda aparcado sobre la
        # interfaz hasta que acaba el tramo, son varios segundos de un objeto
        # enorme que ya no hace nada: es wobble ocioso con otra forma, y encima
        # compite con la caja delimitadora que entra después.
        anims.append(("badge-out", f"#{cid}-cursor", clicks[-1][0] + 1.0, .28))
    return css, html, anims


# ── métricas protagonistas ────────────────────────────────────────────────────
def stat_grid(cid: str, items: list[tuple[str, str]], at: list[float],
              accent: int = -1) -> tuple[str, str, list]:
    """Tres cifras como elemento gráfico protagonista, una por beat del habla.

    `items` = [(valor, etiqueta)]. `accent` marca cuál lleva el violeta: solo
    una, porque el sistema pide un único momento de alto voltaje por frame.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    cells = "".join(
        f'<div class="scell{" hot" if i == accent else ""}" id="{cid}-s{i}">'
        f'<div class="sval">{esc(v)}</div><div class="slab">{esc(l)}</div></div>'
        for i, (v, l) in enumerate(items))
    css = f"""
{p} .sgrid{{display:flex;gap:20px;width:{BOARD_W}px}}
{p} .scell{{flex:1;background:{C['surface']};border:1px solid {LINE};
  border-radius:{RADIUS['lg']}px;padding:44px 18px 38px;text-align:center;
  box-shadow:{SHADOW};opacity:0}}
{p} .scell.hot{{border-color:rgba(124,92,255,.5);background:
  linear-gradient(180deg,{FILL['violet']} 0%,{C['surface']} 70%)}}
{p} .sval{{font-family:{FONT};font-weight:900;font-size:88px;line-height:.96;
  letter-spacing:-.04em;color:{C['text']}}}
{p} .scell.hot .sval{{color:{C['violet_hi']}}}
{p} .slab{{font-family:{MONO};font-weight:700;font-size:21px;letter-spacing:.14em;
  color:{C['text3']};margin-top:20px}}"""
    anims = [("stamp", f"#{cid}-s{i}", at[i] if i < len(at) else .3 + i * .16, .40)
             for i in range(len(items))]
    return css, f'<div class="sgrid">{cells}</div>', anims


# ── el mismo dato, dos resultados ─────────────────────────────────────────────
def rate_mismatch(cid: str, subject: str, left: tuple[str, str],
                  right: tuple[str, str], at: list[float],
                  verdict: str = "", verdict_at: float | None = None,
                  ) -> tuple[str, str, list]:
    """Una misma operación calculada dos veces, con dos resultados distintos.

    `left` y `right` = (cifra, etiqueta). Las dos columnas entran una por beat
    y **la segunda llega en rojo**: el error no se explica con un icono, se ve
    en que el número de al lado no cuadra. El veredicto (la diferencia) aterriza
    al final, que es cuando el guion nombra la pérdida.

    Las dos columnas son idénticas en tipo y tamaño a propósito: si la mala se
    dibuja más pequeña o más apagada, el espectador la descarta antes de haber
    comparado, y la comparación ERA el gráfico.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    (lv, ll), (rv, rl) = left, right
    css = f"""
{p} .rmwrap{{width:{BOARD_W}px;display:flex;flex-direction:column;gap:22px}}
{p} .rmsub{{font-family:{MONO};font-weight:700;font-size:24px;letter-spacing:.16em;
  color:{C['text3']};text-align:center;opacity:0}}
{p} .rmrow{{display:flex;gap:20px;align-items:stretch;position:relative}}
{p} .rmcol{{flex:1;background:{C['surface']};border:1px solid {LINE};
  border-radius:{RADIUS['lg']}px;padding:40px 22px 34px;text-align:center;
  box-shadow:{SHADOW};opacity:0}}
{p} .rmcol.bad{{border-color:rgba(255,90,90,.45);
  background:linear-gradient(180deg,{FILL['alert']} 0%,{C['surface']} 72%)}}
{p} .rmval{{font-family:{FONT};font-weight:900;font-size:74px;line-height:.96;
  letter-spacing:-.04em;color:{C['text']};white-space:nowrap}}
{p} .rmcol.bad .rmval{{color:{C['alert']}}}
{p} .rmlab{{font-family:{MONO};font-weight:700;font-size:20px;letter-spacing:.14em;
  color:{C['text3']};margin-top:18px}}
{p} .rmneq{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
  width:78px;height:78px;border-radius:50%;background:{C['bg']};
  border:1px solid {LINE_HI};display:flex;align-items:center;justify-content:center;
  font-family:{FONT};font-weight:900;font-size:40px;color:{C['alert']};
  z-index:4;opacity:0}}
{p} .rmverd{{display:flex;align-items:center;justify-content:center;gap:16px;
  background:{FILL['alert']};border:1px solid rgba(255,90,90,.42);
  border-radius:{RADIUS['md']}px;padding:24px 30px;font-family:{FONT};
  font-weight:800;font-size:40px;letter-spacing:-.02em;color:{C['alert']};
  opacity:0}}"""
    html = (f'<div class="rmwrap">'
            f'<div class="rmsub" id="{cid}-rmsub">{esc(subject)}</div>'
            f'<div class="rmrow">'
            f'<div class="rmcol" id="{cid}-rm0">'
            f'<div class="rmval">{esc(lv)}</div>'
            f'<div class="rmlab">{esc(ll)}</div></div>'
            f'<div class="rmcol bad" id="{cid}-rm1">'
            f'<div class="rmval">{esc(rv)}</div>'
            f'<div class="rmlab">{esc(rl)}</div></div>'
            f'<div class="rmneq" id="{cid}-rmneq">≠</div>'
            f'</div>'
            + (f'<div class="rmverd" id="{cid}-rmv">{esc(verdict)}</div>'
               if verdict else "")
            + '</div>')
    anims = [("slide-in", f"#{cid}-rmsub", .04, .28),
             ("stamp", f"#{cid}-rm0", at[0] if at else .22, .38),
             ("stamp", f"#{cid}-rm1", at[1] if len(at) > 1 else .70, .38),
             ("chip-in", f"#{cid}-rmneq",
              (at[1] if len(at) > 1 else .70) + .16, .26)]
    if verdict:
        anims.append(("stamp", f"#{cid}-rmv",
                      verdict_at if verdict_at is not None else 1.30, .40))
    return css, html, anims


# ── una lista que se acumula hasta abrumar ────────────────────────────────────
def chip_grid(cid: str, chips: list[str], at: list[float], kicker: str = "",
              alert: str = "", alert_at: float | None = None,
              ) -> tuple[str, str, list]:
    """Etiquetas que se van amontonando, una por palabra del guion.

    Para una enumeración: cada chip aterriza EN su palabra y se queda. Lo que
    comunica no es cada chip suelto sino el montón que queda al final — por eso
    ninguno se va, y por eso el remate (`alert`) solo tiene sentido cuando ya
    están todos en pantalla.

    Un `stat_grid` respondería «cuánto» con tres cifras; esto responde «cuántas
    cosas a la vez», que es otra pregunta y pide otra forma.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    cells = "".join(
        f'<div class="cgchip" id="{cid}-c{i}">{esc(c)}</div>'
        for i, c in enumerate(chips))
    css = f"""
{p} .cgwrap{{width:{BOARD_W}px;display:flex;flex-direction:column;
  align-items:center;gap:30px}}
{p} .cgkick{{font-family:{MONO};font-weight:700;font-size:24px;letter-spacing:.18em;
  color:{C['text3']};opacity:0}}
{p} .cggrid{{display:flex;flex-wrap:wrap;gap:18px;justify-content:center}}
{p} .cgchip{{background:{C['surface2']};border:1px solid {LINE};
  border-radius:{RADIUS['pill']}px;padding:24px 36px;font-family:{FONT};
  font-weight:800;font-size:44px;letter-spacing:-.02em;color:{C['text']};
  box-shadow:{SHADOW};opacity:0;white-space:nowrap}}
{p} .cgalert{{display:flex;align-items:center;gap:16px;background:{FILL['alert']};
  border:1px solid rgba(255,90,90,.42);border-radius:{RADIUS['md']}px;
  padding:22px 32px;font-family:{FONT};font-weight:800;font-size:40px;
  letter-spacing:-.02em;color:{C['alert']};opacity:0}}
{p} .cgalert s{{width:12px;height:12px;border-radius:50%;background:{C['alert']};
  display:block;text-decoration:none;flex:0 0 12px}}"""
    html = (f'<div class="cgwrap">'
            + (f'<div class="cgkick" id="{cid}-cgk">{esc(kicker)}</div>'
               if kicker else "")
            + f'<div class="cggrid">{cells}</div>'
            + (f'<div class="cgalert" id="{cid}-cga"><s></s>{esc(alert)}</div>'
               if alert else "")
            + "</div>")
    anims = []
    if kicker:
        anims.append(("slide-in", f"#{cid}-cgk", .04, .28))
    for i in range(len(chips)):
        anims.append(("chip-in", f"#{cid}-c{i}",
                      at[i] if i < len(at) else .30 + i * .40, .30))
    if alert:
        anims.append(("stamp", f"#{cid}-cga",
                      alert_at if alert_at is not None else
                      (at[-1] if at else 1.0) + .60, .40))
    return css, html, anims


# ── una palabra convertida en gráfico ─────────────────────────────────────────
def keyword_hero(cid: str, word: str, kicker: str = "",
                 sub: str = "", size: int = 158) -> tuple[str, str, list]:
    """Cuando una idea cabe en una palabra, la palabra ES el gráfico."""
    p = f'.viz[data-viz-id="{cid}"]'
    css = f"""
{p} .khero{{display:flex;flex-direction:column;align-items:center;gap:26px;
  width:{BOARD_W}px;text-align:center}}
{p} .kkick{{font-family:{MONO};font-weight:700;font-size:26px;letter-spacing:.20em;
  color:{C['violet_hi']};background:{FILL['violet']};border-radius:{RADIUS['pill']}px;
  padding:12px 26px;opacity:0}}
{p} .kword{{font-family:{FONT};font-weight:900;font-size:{size}px;line-height:.94;
  letter-spacing:-.045em;color:{C['text']};opacity:0}}
{p} .kbar{{width:0;height:12px;border-radius:6px;background:{C['violet']}}}
{p} .ksub{{font-family:{FONT};font-weight:500;font-size:36px;line-height:1.3;
  color:{C['text2']};max-width:820px;opacity:0}}"""
    html = (f'<div class="khero">'
            + (f'<div class="kkick" id="{cid}-kk">{esc(kicker)}</div>' if kicker else "")
            + f'<div class="kword" id="{cid}-kw">{esc(word)}</div>'
            + f'<div class="kbar" id="{cid}-kb"></div>'
            + (f'<div class="ksub" id="{cid}-ks">{esc(sub)}</div>' if sub else "")
            + "</div>")
    anims = []
    if kicker:
        anims.append(("chip-in", f"#{cid}-kk", .06, .30))
    anims.append(("punch", f"#{cid}-kw", .20, .46))
    anims.append(("grow-x", f"#{cid}-kb", .48, .40, 300))
    if sub:
        anims.append(("slide-in", f"#{cid}-ks", .58, .34))
    return css, html, anims


# ── banda de arriba del triband: card de logo y card de grabación ────────────
def tool_card(cid: str, slug: str, name: str, kicker: str = "") -> tuple[str, str, list]:
    """La card de marca, clavada a la palabra que nombra la herramienta.

    La CARD entra por OPACIDAD (la resuelve quien la hospeda, igual que el
    resto de las cards del sistema — §6): este componente no le pone ningún
    `anim`, solo a lo de DENTRO. El logo viaja en horizontal (`glide-x`) y el
    nombre cae en vertical (`drop-in`) con un pequeño retraso — dos caminos
    distintos a propósito, para que el ojo lea DOS elementos y no un bloque.

    El logo se monta en un marco propio (`.tc-logoframe`: hairline + fondo
    `bg`, el mismo tratamiento que ya usa `.appicon` en `app_switch`) en vez
    de fiarse del tile que trae la marca. Medido contra `surface`: Motion
    (`#0B0B0C`, 1.11:1) y Bklit UI (`#000000`, 1.18:1) se hunden sin él; Manus
    (17.73:1), Anime.js y Kokonut UI (transparentes) no lo necesitan pero
    tampoco lo penaliza — es una regla del componente, no un caso especial
    escrito para dos slugs. El hairline es `LINE_HI` (no el `LINE` de
    costumbre): compuesto sobre `surface` da 1.63:1 (`tokens.lift`), un
    margen real sobre el 1.11–1.18:1 de los dos tiles que motivaron el
    arreglo — con `LINE` a secas quedaba en 1.29:1, apenas por encima del
    peor tile, y el marco tiene que separar más de lo que ya fallaba.

    `tc-tilt` es el wrapper HIJO estático de `perspective()+rotateY()`: GSAP
    no lo toca — solo anima `#{cid}-logo` y `#{cid}-name`, opacity/x/y — así
    que el tilt no se puede descuadrar por un tween posterior de scale (mismo
    mecanismo que `objects._object_html`). -6° es el valor que ya usan
    `dental_chair`/`bottleneck`: una card no necesita su propio ángulo, y
    reutilizar el de la librería de objetos es lo que hace que las tres
    bandas del triband lean del mismo mundo 3D.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    # `ratio` mide el tile de la marca contra `surface` y puede ser None (marca
    # transparente) — aquí no se usa: el marco propio da el contraste que haga
    # falta sin depender de lo que traiga cada logo.
    logo_html, _ratio = logos.mark(slug, 72)
    css = f"""
{p} .tc-card{{display:flex;align-items:center;justify-content:center}}
{p} .tc-tilt{{transform:perspective(1400px) rotateY(-6deg);transform-style:preserve-3d}}
{p} .tc-root{{display:flex;align-items:center;gap:30px;background:{C['surface']};
  border:1px solid {LINE};border-radius:{RADIUS['lg']}px;box-shadow:{SHADOW};
  padding:30px 46px}}
{p} .tc-logoframe{{flex:0 0 auto;width:112px;height:112px;
  border-radius:{RADIUS['md']}px;background:{C['bg']};border:1px solid {LINE_HI};
  display:flex;align-items:center;justify-content:center;overflow:hidden}}
{p} .tc-logo{{opacity:0;display:flex;align-items:center;justify-content:center}}
{p} .tc-name{{display:flex;flex-direction:column;gap:8px;opacity:0}}
{p} .tc-kick{{font-family:{MONO};font-weight:700;font-size:22px;
  letter-spacing:.16em;color:{C['violet_hi']};text-transform:uppercase}}
{p} .tc-word{{font-family:{FONT};font-weight:900;font-size:58px;line-height:1;
  letter-spacing:-.03em;color:{C['text']}}}"""
    html = (f'<div class="tc-card" id="{cid}-card"><div class="tc-tilt">'
            f'<div class="tc-root">'
            f'<div class="tc-logoframe"><span class="tc-logo" id="{cid}-logo">'
            f'{logo_html}</span></div>'
            f'<div class="tc-name" id="{cid}-name">'
            + (f'<span class="tc-kick">{esc(kicker)}</span>' if kicker else "")
            + f'<span class="tc-word">{esc(name)}</span>'
            + "</div></div></div></div>")
    anims = [
        ("glide-x", f'#{cid}-logo', .10, .45),
        ("drop-in", f'#{cid}-name', .18, .42),
    ]
    return css, html, anims


def tool_recording(cid: str, slug: str, name: str,
                    rect: tuple[float, float, float, float],
                    hairline: int = 1) -> tuple[str, str, list]:
    """La card de grabación: el logo persiste de CHIP en la cabecera.

    Corte duro desde `tool_card` — la grabación es un `<video>` nuevo, no una
    transición. Este componente, igual que `browser_frame`/`screen_panel`, no
    dibuja el video: se dibuja ALREDEDOR. El `<video>` real va suelto en el
    stage (media anidada en un elemento temporizado se congela) y ocupa el
    mismo `rect` a sangre — 16:9, igual que la card — así que `.tr-panel` no
    lleva fondo propio: pintarlo taparía la grabación que vive por debajo.

    El chip de marca en la cabecera es lo que ata la grabación a su nombre
    durante los 6–8 s que dura, sin él se desatan (§3).

    `hairline` es el grosor del marco en px, PARAMETRIZADO: la grabación de
    Manus es la única CLARA de las cinco y necesita un marco más marcado para
    no perderse contra un fondo también claro. El llamador decide el grosor
    por grabación — este componente no conoce ningún slug especial.

    **El tilt 3D va SOLO en el chip (`.tr-chip`, 40×40), nunca en el marco
    (`.tr-panel`) ni en la cabecera entera (`.tr-head`).** Dos motivos, los
    dos verificados en Chrome headless, no supuestos:

    1. El `<video>` de la grabación es un elemento aparte que este componente
       no controla y que se coloca sin transform, plano, en el mismo `rect`.
       Si el marco llevara `rotateY`, su borde dejaría de coincidir con el
       borde del video real que enmarca.
    2. **Probé el tilt en `.tr-head` entera (la barra ancha, 960×84) y se ve
       ROTA, no elegante**: al ser una franja pegada al borde superior,
       `rotateY` alrededor de su propio centro le abre un hueco visible en la
       esquina superior donde el fondo se asoma por debajo — no es «sutil»,
       es un defecto. Un elemento CUADRADO y pequeño como `.tr-chip` no tiene
       ese problema: rota sobre sí mismo sin desprenderse de ningún borde
       compartido. Por eso el tilt vive solo ahí, con un ángulo más marcado
       (-8°, contra -6° en `tool_card`) para que se note en un elemento tan
       chico — la cabecera sigue plana y pegada a su rect.
    """
    x, y, w, h = rect
    p = f'.viz[data-viz-id="{cid}"]'
    chip_html, _ratio = logos.mark(slug, 40)
    head_h = 84
    css = f"""
{p} .tr-panel{{position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;
  border-radius:{RADIUS['lg']}px;overflow:hidden;pointer-events:none;
  border:{hairline}px solid {LINE_HI};box-shadow:{SHADOW};z-index:11}}
{p} .tr-head{{position:absolute;left:0;top:0;width:100%;height:{head_h}px;
  display:flex;align-items:center;gap:16px;padding:0 26px;
  background:rgba(11,12,16,.72);border-bottom:1px solid {LINE_HI};opacity:0}}
{p} .tr-chip{{flex:0 0 auto;width:40px;height:40px;border-radius:{RADIUS['sm']}px;
  background:{C['bg']};border:1px solid {LINE_HI};display:flex;align-items:center;
  justify-content:center;overflow:hidden;
  transform:perspective(800px) rotateY(-8deg);transform-style:preserve-3d}}
{p} .tr-name{{font-family:{FONT};font-weight:800;font-size:28px;
  letter-spacing:-.02em;color:{C['text']}}}"""
    html = (f'<div class="tr-panel" id="{cid}-panel">'
            f'<div class="tr-head" id="{cid}-head">'
            f'<span class="tr-chip">{chip_html}</span>'
            f'<span class="tr-name">{esc(name)}</span>'
            f'</div></div>')
    anims = [("slide-in", f'#{cid}-head', .04, .26)]
    return css, html, anims


def tool_lineup(cid: str, tools: list[tuple[str, str]], at: list[float],
                kicker: str = "", kicker_at: float = 0.0) -> tuple[str, str, list]:
    """El beat de «la guía»: las herramientas ya nombradas, juntas en fila.

    Distinto de `tool_card`: aquella clava UNA marca a SU palabra, una a la
    vez; esta reúne TODAS a la vez, porque el beat que la pide no vuelve a
    nombrarlas («he juntado ESTAS y varias más») — para cuando suena, las
    cinco ya se dijeron, así que no hay guion que adelantar poniéndolas
    juntas. `nada entra antes de su palabra` se cumple igual: la fila entra
    cuando él dice «estas», no antes de que la primera se nombrara.

    Construido sobre el mismo marco de logo que `tool_card` (`.tc-logoframe`:
    hairline `LINE_HI` + fondo `bg`) en vez de inventar uno nuevo — la CSS de
    cada componente vive con el prefijo de su propio `data-viz-id`, así que
    reutilizar la clase por nombre no basta entre dos visuales distintos; se
    copia aquí la misma receta, no solo el nombre. Se descartó `app_switch`
    (dibuja logos, pero con un conector ROTO y la etiqueta «AISLADO» — la
    frase de este beat es la contraria, «las he juntado») y `chip_grid`
    (pinta texto en pastillas, no marcas).
    """
    p = f'.viz[data-viz-id="{cid}"]'
    tiles = []
    for i, (slug, name) in enumerate(tools):
        # `logos.mark()` devuelve (html, ratio) y `ratio` puede ser `None`
        # para una marca transparente (animejs, kokonutui aquí) — no hay tile
        # que perderse contra el fondo. Igual que `tool_card` (mismo marco,
        # mismo fondo `bg`), el ratio se DESCARTA aquí a propósito: mide el
        # tile contra `surface` (el default de `mark()`), no contra `bg` —
        # el fondo real de `.tlframe` — así que un número bajo (Motion,
        # 1.11:1; Bklit UI, 1.18:1) no describe lo que de verdad se renderiza
        # y no hay que gatear sobre él, exactamente el mismo razonamiento
        # documentado en `tool_card`.
        logo_html, _ratio = logos.mark(slug, 56)
        tiles.append(
            f'<div class="tlcell" id="{cid}-t{i}">'
            f'<div class="tlframe">{logo_html}</div>'
            f'<div class="tlname">{esc(name)}</div></div>')
    css = f"""
{p} .tlwrap{{display:flex;flex-direction:column;align-items:center;gap:22px}}
{p} .tlkick{{font-family:{MONO};font-weight:700;font-size:24px;letter-spacing:.18em;
  color:{C['violet_hi']};background:{FILL['violet']};border-radius:{RADIUS['pill']}px;
  padding:10px 24px;opacity:0}}
{p} .tlrow{{display:flex;gap:22px;align-items:flex-start}}
{p} .tlcell{{display:flex;flex-direction:column;align-items:center;gap:12px;opacity:0}}
{p} .tlframe{{width:104px;height:104px;border-radius:{RADIUS['md']}px;
  background:{C['bg']};border:1px solid {LINE_HI};display:flex;
  align-items:center;justify-content:center;overflow:hidden}}
{p} .tlname{{font-family:{MONO};font-weight:700;font-size:17px;letter-spacing:.05em;
  color:{C['text2']};text-transform:uppercase;white-space:nowrap}}"""
    html = (f'<div class="tlwrap">'
            + (f'<div class="tlkick" id="{cid}-tk">{esc(kicker)}</div>' if kicker else "")
            + f'<div class="tlrow">{"".join(tiles)}</div></div>')
    anims = []
    if kicker:
        anims.append(("chip-in", f"#{cid}-tk", kicker_at, .30))
    for i in range(len(tools)):
        anims.append(("chip-in", f"#{cid}-t{i}",
                      at[i] if i < len(at) else .20 + i * .22, .30))
    return css, html, anims


# ── cadena de consecuencias ───────────────────────────────────────────────────
def flow_steps(cid: str, steps: list[str], at: list[float],
               tone: str = "ok") -> tuple[str, str, list]:
    """Una acción y lo que dispara. Cada paso entra al nombrarse y la flecha
    que lo precede se dibuja antes: la causalidad se ve en el orden.

    `tone` decide cómo termina la cadena. `ok` es una consecuencia que
    funciona (✓ verde); `fail` es una que se rompe, y entonces **solo el último
    paso** se marca en rojo: si se tiñen todos, la cadena se lee como un error
    de sistema en vez de como el precio de haber llegado hasta ahí.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    fail = tone == "fail"
    rows = []
    for i, s in enumerate(steps):
        if i:
            rows.append(f'<div class="farrow" id="{cid}-a{i}">↓</div>')
        last = i == len(steps) - 1
        cls = " bad" if (fail and last) else (" hot" if (not fail and i == 0) else "")
        # En una cadena de fallo el ✓ verde no vale ni para los pasos de en
        # medio: «No hay stock ✓» se lee al revés de lo que significa. El paso
        # intermedio se queda sin marca —solo ocurrió— y el remate es el ✕.
        glyph = ("✕" if last else "") if fail else "✓"
        rows.append(
            f'<div class="fstep{cls}" id="{cid}-f{i}">'
            f'<span class="fnum">{i+1:02d}</span>{esc(s)}'
            f'<span class="fok">{glyph}</span></div>')
    css = f"""
{p} .fflow{{display:flex;flex-direction:column;align-items:center;gap:8px;width:{BOARD_W}px}}
{p} .fstep{{width:100%;display:flex;align-items:center;gap:22px;
  background:{C['surface']};border:1px solid {LINE};border-radius:{RADIUS['md']}px;
  padding:28px 30px;font-family:{FONT};font-weight:700;font-size:40px;
  letter-spacing:-.02em;color:{C['text']};box-shadow:{SHADOW};opacity:0}}
{p} .fstep.hot{{border-color:rgba(124,92,255,.5);
  background:linear-gradient(90deg,{FILL['violet']} 0%,{C['surface']} 62%)}}
{p} .fstep.bad{{border-color:rgba(255,90,90,.45);
  background:linear-gradient(90deg,{FILL['alert']} 0%,{C['surface']} 62%);
  color:{C['alert']}}}
{p} .fnum{{font-family:{MONO};font-weight:700;font-size:22px;letter-spacing:.12em;
  color:{C['violet_hi']};flex:0 0 auto}}
{p} .fstep.bad .fnum{{color:{C['alert']}}}
{p} .fok{{margin-left:auto;color:{C['go']};font-size:36px;font-weight:900}}
{p} .fstep.hot .fok{{color:{C['violet_hi']}}}
{p} .fstep.bad .fok{{color:{C['alert']}}}
{p} .farrow{{font-family:{FONT};font-size:34px;font-weight:700;color:{C['violet']};
  opacity:0;line-height:1}}"""
    anims = []
    for i in range(len(steps)):
        t = at[i] if i < len(at) else .28 + i * .5
        if i:
            anims.append(("chip-in", f"#{cid}-a{i}", max(.02, t - .16), .18))
        anims.append(("stamp", f"#{cid}-f{i}", t, .38))
    return css, f'<div class="fflow">{"".join(rows)}</div>', anims


# ── el chat: un mensaje y lo que NO vuelve ────────────────────────────────────
def chat_unanswered(cid: str, contact: str, message: str, kicker: str = "",
                    brand: str = "", bubble_at: float = .62,
                    tick_at: float = 1.70, tick_label: str = "ENVIADO",
                    wait: str = "", wait_at: float | None = None,
                    reply: str = "", reply_at: float | None = None,
                    ) -> tuple[str, str, list]:
    """Un mensaje enviado y el hueco debajo. Lo que comunica es la AUSENCIA:
    la burbuja llega, el tilde se queda gris y no baja nada más.

    La marca en la cabecera declara de qué app es **sin clonar su interfaz**:
    dibujar el chat real de WhatsApp sería una captura falsa, y la doctrina de
    este módulo lo prohíbe.

    `wait` es el remate ámbar del silencio («20 MIN SIN RESPUESTA») y solo
    tiene sentido cuando la burbuja ya está puesta. `reply` abre una burbuja
    ENTRANTE: convierte el mismo componente en el caso contrario, que es como
    se lee un contraste — el mismo chat, el otro resultado.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    mk = ""
    if brand:
        svg, _ratio = logos.mark(brand, 44, "brand")
        mk = f'<div class="chbrand" id="{cid}-brand">{svg}</div>'
    css = f"""
{p} .chwrap{{display:flex;flex-direction:column;align-items:center;gap:26px;width:{BOARD_W}px}}
{p} .chkick{{font-family:{MONO};font-weight:700;font-size:26px;letter-spacing:.20em;
  color:{C['text3']};opacity:0}}
{p} .chpane{{width:100%;height:880px;background:{C['surface']};border:1px solid {LINE};
  border-radius:{RADIUS['xl']}px;box-shadow:{SHADOW_LIFT};padding:0 0 34px;
  display:flex;flex-direction:column;overflow:hidden;opacity:0}}
{p} .chtop{{display:flex;align-items:center;gap:20px;padding:26px 30px;
  border-bottom:1px solid {LINE};background:{C['surface2']}}}
{p} .chav{{width:58px;height:58px;border-radius:50%;flex:0 0 58px;
  background:linear-gradient(135deg,{C['surface3']} 0%,{C['bg2']} 100%);
  border:1px solid {LINE_HI}}}
{p} .chname{{font-family:{FONT};font-weight:700;font-size:38px;letter-spacing:-.01em;
  color:{C['text']};flex:1}}
/* La marca va a la IZQUIERDA, pegada al avatar: el borde derecho de la
   cabecera es justo donde se posa la ventana del creador en PiP.
   `display:block` en el span no es decorativo — `logos.mark` le pone el tamaño
   en línea, y un span inline se lo ignora: el SVG crecía hasta comerse la
   cabecera entera. */
{p} .chbrand{{line-height:0;flex:0 0 auto;width:44px;height:44px}}
{p} .chbrand .brandmark{{display:block;width:44px;height:44px}}
{p} .chbrand svg{{width:100%;height:100%;display:block}}
{p} .chbody{{flex:1;display:flex;flex-direction:column;justify-content:flex-start;
  align-items:flex-end;padding:34px 30px 0;gap:10px}}
{p} .chbub{{max-width:78%;background:{FILL['violet2']};border:1px solid rgba(124,92,255,.34);
  border-radius:24px 10px 24px 24px;
  padding:24px 28px;font-family:{FONT};font-weight:500;font-size:36px;line-height:1.34;
  color:{C['text']};opacity:0}}
{p} .chmeta{{display:flex;align-items:center;gap:12px;font-family:{MONO};font-weight:700;
  font-size:24px;letter-spacing:.10em;color:{C['text3']};padding-right:6px;opacity:0}}
{p} .chtick{{font-size:30px;line-height:1;color:{C['text3']}}}
{p} .chwait{{align-self:center;margin-top:26px;font-family:{MONO};font-weight:700;
  font-size:28px;letter-spacing:.14em;color:{C['warn']};background:{FILL['warn']};
  border:1px solid rgba(255,184,77,.34);border-radius:{RADIUS['pill']}px;
  padding:14px 30px;opacity:0}}
/* La entrante va pegada al otro lado y con la esquina espejada: el bando se
   lee en la geometría, no hace falta rotularlo. */
{p} .chin{{align-self:flex-start;max-width:78%;margin-top:26px;background:{C['surface3']};
  border:1px solid {LINE_HI};border-radius:10px 24px 24px 24px;
  padding:24px 28px;font-family:{FONT};font-weight:500;font-size:36px;line-height:1.34;
  color:{C['text']};opacity:0}}"""
    html = (f'<div class="chwrap">'
            + (f'<div class="chkick" id="{cid}-kick">{esc(kicker)}</div>' if kicker else "")
            + f'<div class="chpane" id="{cid}-pane">'
            + f'<div class="chtop"><div class="chav"></div>{mk}'
            + f'<div class="chname">{esc(contact)}</div></div>'
            + f'<div class="chbody">'
            + f'<div class="chbub" id="{cid}-bub">{esc(message)}</div>'
            + f'<div class="chmeta" id="{cid}-meta">'
            + f'<span>{esc(tick_label)}</span><span class="chtick">✓</span></div>'
            + (f'<div class="chwait" id="{cid}-wait">{esc(wait)}</div>' if wait else "")
            + (f'<div class="chin" id="{cid}-in">{esc(reply)}</div>' if reply else "")
            + "</div></div></div>")
    anims = []
    if kicker:
        anims.append(("chip-in", f"#{cid}-kick", .10, .30))
    anims.append(("chip-in", f"#{cid}-pane", .1667, .40))
    anims.append(("rise-in", f"#{cid}-bub", bubble_at, .459))
    anims.append(("chip-in", f"#{cid}-meta", tick_at, .35))
    if wait:
        anims.append(("stamp", f"#{cid}-wait",
                      tick_at + .5 if wait_at is None else wait_at, .38))
    if reply:
        anims.append(("rise-in", f"#{cid}-in",
                      tick_at + .5 if reply_at is None else reply_at, .44))
    return css, html, anims
# ── CTA: la interacción que se pide, simulada ─────────────────────────────────
def comment_ui(cid: str, word: str, type_at: float = 0.6,
               send_at: float = 1.5, headline: str = "") -> tuple[str, str, list]:
    """Simula el comentario que el CTA pide: la palabra en grande, la caja, el
    tecleo y el envío. Pedir «comenta ERP» y ENSEÑARLO convierte la instrucción
    en un gesto que el espectador ya ha visto hacer una vez.

    `headline` es la palabra a tamaño protagonista. Sin ella el cierre se queda
    en una barra fina en mitad de un lienzo vacío: correcto pero sin peso, y el
    CTA es justo el momento que no puede pesar poco.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    css = f"""
{p} .cwrap{{display:flex;flex-direction:column;align-items:center;gap:34px;width:{BOARD_W}px}}
{p} .chead{{font-family:{FONT};font-weight:900;font-size:190px;line-height:.92;
  letter-spacing:-.05em;color:{C['text']};opacity:0}}
{p} .csay{{font-family:{MONO};font-weight:700;font-size:26px;letter-spacing:.20em;
  color:{C['violet_lt']};background:{FILL['violet']};border-radius:{RADIUS['pill']}px;
  padding:12px 26px;opacity:0;margin-bottom:-14px}}
{p} .cbox{{width:100%;display:flex;align-items:center;gap:20px;background:{C['surface']};
  border:1px solid {LINE_HI};border-radius:{RADIUS['pill']}px;padding:22px 26px;
  box-shadow:{SHADOW_LIFT};opacity:0}}
{p} .cav{{width:66px;height:66px;border-radius:50%;flex:0 0 66px;
  background:linear-gradient(135deg,{C['violet']} 0%,{C['violet_dk']} 100%)}}
{p} .cfield{{flex:1;min-width:0;font-family:{FONT};font-weight:700;font-size:42px;
  letter-spacing:-.01em;color:{C['text']};white-space:nowrap;overflow:hidden}}
{p} .cfield i{{color:{C['text3']};font-style:normal;font-weight:500}}
{p} .ccaret{{display:inline-block;width:4px;height:44px;background:{C['violet']};
  vertical-align:-8px;margin-left:6px}}
{p} .csend{{font-family:{MONO};font-weight:700;font-size:24px;letter-spacing:.12em;
  color:{C['text3']};flex:0 0 auto}}
{p} .csend.on{{color:{C['go']}}}
{p} .cposted{{display:flex;align-items:center;gap:16px;font-family:{MONO};font-weight:700;
  font-size:26px;letter-spacing:.14em;color:{C['go']};background:{FILL['go']};
  border:1px solid rgba(52,227,155,.4);border-radius:{RADIUS['pill']}px;
  padding:14px 28px;opacity:0}}"""
    html = (f'<div class="cwrap">'
            + (f'<div class="csay" id="{cid}-say">COMENTA LA PALABRA</div>'
               f'<div class="chead" id="{cid}-head">{esc(headline)}</div>'
               if headline else "")
            + f'<div class="cbox" id="{cid}-box"><div class="cav"></div>'
              f'<div class="cfield" id="{cid}-field"><i>Añade un comentario…</i></div>'
              f'<div class="csend" id="{cid}-send">ENVIAR</div></div>'
              f'<div class="cposted" id="{cid}-posted">✓ COMENTARIO PUBLICADO</div></div>')
    # Nada de dentro empieza a entrar hasta que el contenedor ya es opaco. Si la
    # entrada del chip solapa con el fundido del host, se multiplican las dos
    # opacidades y durante unas décimas el texto queda a 2.15:1 — pasa el ojo,
    # no pasa el linter, y de hecho se ve pastoso. Además, dos fundidos
    # encadenados leen peor que uno.
    anims = []
    if headline:
        anims += [("chip-in", f"#{cid}-say", .16, .22),
                  ("punch", f"#{cid}-head", .26, .44)]
    anims += [
        ("chip-in", f"#{cid}-box", .40, .30),
        ("type-word", f"#{cid}-field", type_at, .70, esc(word)),
        ("send-on", f"#{cid}-send", send_at, .26),
        ("stamp", f"#{cid}-posted", send_at + .22, .38),
    ]
    return css, html, anims
