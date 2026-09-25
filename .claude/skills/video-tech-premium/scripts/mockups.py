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

Todo está dibujado con `tokens.py` y la paleta activa (claro u oscuro):
superficies flotando con hairline y sombra, tipografía Inter/JetBrains Mono y
un único momento de acento por frame.

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

import icons
import logos
import tokens as TK
from tokens import C, FILL, FONT, MONO, RADIUS, accent_a, esc, ink_a, mix, shade_a

# Ancho de trabajo de un mockup a pantalla completa en REEL.
BOARD_W = 980


# Ancho real de un texto, para lo que no se puede resolver con CSS.
_TTF_CACHE: dict = {}


def text_px(text: str, size: int, weight: int = 700) -> float:
    """Los píxeles que ocupa `text` en Inter `weight` a `size`.

    Existe por el tachado de `rewrite_line`: la barra que cruza la línea tiene
    que medir lo que mide el TEXTO, y `grow-x` anima un `width` en píxeles, no
    un porcentaje. Estimarlo contando letras es justo lo que §7 prohíbe con las
    coordenadas de `clicks` y `boxes`, y el fallo tiene la misma firma —el
    navegador se ve bien y el MP4 sale con la raya corta o pasada de largo.

    Se mide con la MISMA woff2 vendorizada que renderiza el navegador, así que
    el número no depende de qué fuentes tenga instaladas la máquina.
    """
    from pathlib import Path
    from PIL import ImageFont
    key = (size, weight)
    if key not in _TTF_CACHE:
        skill = Path(__file__).resolve().parent.parent
        ttf = skill / "assets" / f".inter{weight}.ttf"
        if not ttf.exists():
            from fontTools.ttLib import TTFont
            f = TTFont(skill / "assets" / "fonts" / f"Inter-{weight}.woff2")
            f.flavor = None
            ttf.parent.mkdir(parents=True, exist_ok=True)
            f.save(str(ttf))
        _TTF_CACHE[key] = ImageFont.truetype(str(ttf), size)
    return _TTF_CACHE[key].getlength(text)


def _cursor(cid: str, ring_color: str | None = None) -> str:
    """Cursor macOS sobredimensionado. Sobre fondo oscuro va en blanco con
    filete del suelo: al revés desaparece encima de cualquier UI clara."""
    ring = ring_color or C["accent"]
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
  border-radius:50%;border:6px solid {C['accent']};opacity:0}}"""


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
  border:1px solid {TK.LINE};border-bottom:0;z-index:10;opacity:0}}
{p} .bring{{position:absolute;left:{x}px;top:{y - CH}px;width:{w}px;height:{h + CH}px;
  border:1px solid {TK.LINE};border-radius:{RADIUS['lg']}px;pointer-events:none;
  box-shadow:{TK.SHADOW_LIFT};z-index:11;opacity:0}}"""
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
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;pointer-events:none;
  box-shadow:{TK.SHADOW_LIFT};z-index:11;opacity:0}}"""
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
  background:{C['surface2']};border-bottom:1px solid {TK.LINE}}}
{p} .bdots{{display:flex;gap:11px}}
{p} .bdots i{{width:17px;height:17px;border-radius:50%;display:block}}
{p} .burl{{flex:1;height:44px;border-radius:{RADIUS['pill']}px;background:{C['bg']};
  border:1px solid {TK.LINE};display:flex;align-items:center;padding:0 22px;
  font-family:{MONO};font-size:22px;color:{C['text3']};overflow:hidden;white-space:nowrap}}
{p} .bchip{{font-family:{MONO};font-weight:700;font-size:19px;letter-spacing:.14em;
  color:{C['accent_hi']};background:{FILL['accent']};border-radius:{RADIUS['pill']}px;
  padding:8px 16px;white-space:nowrap}}"""


# ── HUD ───────────────────────────────────────────────────────────────────────
def hud(cid: str, label: str, corner: str = "01") -> tuple[str, str, list]:
    """Etiqueta de contexto del visual. Minimal: una pastilla mono a la
    izquierda con punto de acento y un índice a la derecha.

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
  color:{C['text2']};background:{TK.rgba(C["surface"], .92)};border:1px solid {TK.LINE};
  border-radius:{RADIUS['pill']}px;padding:11px 20px;white-space:nowrap;opacity:0}}
{p} .hlabel s{{width:11px;height:11px;border-radius:50%;background:{C['accent']};
  display:block;text-decoration:none;flex:0 0 11px}}
{p} .htick{{position:absolute;left:{left_tick}px;top:96px;
  font-family:{MONO};font-weight:700;font-size:21px;letter-spacing:.18em;
  color:{C['text3']};background:{TK.rgba(C["surface"], .92)};border:1px solid {TK.LINE};
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
            mk, ratio = logos.mark(slug, 104, "brand" if slug == brand else "mono",
                                   uid=f"{cid}-app{i}")
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
  background:{C['surface']};border:1px solid {TK.LINE};border-radius:{RADIUS['xl']}px;
  box-shadow:{TK.SHADOW_LIFT}}}
{p} .apphead{{display:flex;align-items:center;justify-content:space-between;
  margin-bottom:30px;font-family:{MONO};font-weight:700;font-size:22px;
  letter-spacing:.16em;color:{C['text3']}}}
{p} .apphead b{{color:{C['alert']};font-weight:700}}
{p} .appline{{display:flex;gap:22px;align-items:stretch;position:relative}}
{p} .apptile{{flex:1;height:400px;background:{C['surface2']};border:1px solid {TK.LINE};
  border-radius:{RADIUS['lg']}px;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:26px;box-shadow:{TK.SHADOW};position:relative;opacity:0}}
{p} .appicon{{width:132px;height:132px;border-radius:{RADIUS['lg']}px;background:{C['bg']};
  border:1px solid {TK.LINE};display:flex;align-items:center;justify-content:center}}
{p} .brandmark{{display:block}}{p} .brandmark svg{{width:100%;height:100%;display:block}}
{p} .erpmark{{font-family:{MONO};font-weight:700;font-size:34px;letter-spacing:.06em;
  color:{C['accent_hi']}}}
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
  border:1px solid {TK.LINE};border-radius:{RADIUS['xl']}px;box-shadow:{TK.SHADOW_LIFT};
  background-image:radial-gradient(circle at 50% 50%,{FILL['accent']} 0%,transparent 58%)}}
{p} .maplines{{position:absolute;inset:0;width:100%;height:100%}}
{p} .maplines path{{fill:none;stroke:{C['accent']};stroke-width:5;stroke-linecap:round}}
{p} .maphub{{position:absolute;left:{cx-115}px;top:{cy-115}px;width:230px;height:230px;
  border-radius:{RADIUS['xl']}px;background:{C['accent']};color:{C['on_accent']};
  display:flex;align-items:center;justify-content:center;
  font-family:{FONT};font-weight:900;font-size:66px;letter-spacing:-.03em;
  box-shadow:{TK.GLOW},{TK.SHADOW_LIFT};z-index:4}}
{p} .mapnode{{position:absolute;width:236px;height:104px;background:{C['surface2']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['md']}px;display:flex;align-items:center;
  justify-content:center;gap:13px;text-align:center;padding:0 14px;
  font-family:{FONT};font-weight:700;font-size:26px;letter-spacing:-.01em;
  color:{C['text']};z-index:5;opacity:0;box-shadow:{TK.SHADOW}}}
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
{p} .scbadge{{position:absolute;background:{C['accent']};color:{C['on_accent']};
  border-radius:{RADIUS['pill']}px;padding:13px 24px;font-family:{MONO};font-weight:700;
  font-size:24px;letter-spacing:.10em;opacity:0;white-space:nowrap;
  box-shadow:0 10px 30px rgba(0,0,0,.55);z-index:16}}
{p} .scbox{{position:absolute;border:5px solid {C['accent']};border-radius:{RADIUS['md']}px;
  box-shadow:0 0 0 9999px {shade_a(.55)};opacity:0;z-index:14}}
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

    `items` = [(valor, etiqueta)]. `accent` marca cuál lleva el acento: solo
    una, porque el sistema pide un único momento de alto voltaje por frame.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    cells = "".join(
        f'<div class="scell{" hot" if i == accent else ""}" id="{cid}-s{i}">'
        f'<div class="sval">{esc(v)}</div><div class="slab">{esc(l)}</div></div>'
        for i, (v, l) in enumerate(items))
    css = f"""
{p} .sgrid{{display:flex;gap:20px;width:{BOARD_W}px}}
{p} .scell{{flex:1;background:{C['surface']};border:1px solid {TK.LINE};
  border-radius:{RADIUS['lg']}px;padding:44px 18px 38px;text-align:center;
  box-shadow:{TK.SHADOW};opacity:0}}
{p} .scell.hot{{border-color:{accent_a(.5)};background:
  linear-gradient(180deg,{FILL['accent']} 0%,{C['surface']} 70%)}}
{p} .sval{{font-family:{FONT};font-weight:900;font-size:88px;line-height:.96;
  letter-spacing:-.04em;color:{C['text']}}}
{p} .scell.hot .sval{{color:{C['accent_hi']}}}
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
{p} .rmcol{{flex:1;background:{C['surface']};border:1px solid {TK.LINE};
  border-radius:{RADIUS['lg']}px;padding:40px 22px 34px;text-align:center;
  box-shadow:{TK.SHADOW};opacity:0}}
{p} .rmcol.bad{{border-color:rgba(255,90,90,.45);
  background:linear-gradient(180deg,{FILL['alert']} 0%,{C['surface']} 72%)}}
{p} .rmval{{font-family:{FONT};font-weight:900;font-size:74px;line-height:.96;
  letter-spacing:-.04em;color:{C['text']};white-space:nowrap}}
{p} .rmcol.bad .rmval{{color:{C['alert']}}}
{p} .rmlab{{font-family:{MONO};font-weight:700;font-size:20px;letter-spacing:.14em;
  color:{C['text3']};margin-top:18px}}
{p} .rmneq{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
  width:78px;height:78px;border-radius:50%;background:{C['bg']};
  border:1px solid {TK.LINE_HI};display:flex;align-items:center;justify-content:center;
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
              icons_: list[str] | None = None,
              ) -> tuple[str, str, list]:
    """Etiquetas que se van amontonando, una por palabra del guion.

    Para una enumeración: cada chip aterriza EN su palabra y se queda. Lo que
    comunica no es cada chip suelto sino el montón que queda al final — por eso
    ninguno se va, y por eso el remate (`alert`) solo tiene sentido cuando ya
    están todos en pantalla.

    Un `stat_grid` respondería «cuánto» con tres cifras; esto responde «cuántas
    cosas a la vez», que es otra pregunta y pide otra forma.

    `icons_` (pieza 19, a petición del usuario: «que las animaciones lleven
    iconos, no solo textos y recuadros») pone un glifo DIBUJADO delante de cada
    etiqueta. Es opcional y por defecto no cambia nada, así que las piezas 3,
    11 y 16 siguen compilando idénticas — el golden lo fija. El icono hereda el
    `color` del chip vía `currentColor`, que es lo que lo hace medible por el
    linter en vez de opaco como un emoji (§14).
    """
    p = f'.viz[data-viz-id="{cid}"]'
    cells = "".join(
        f'<div class="cgchip" id="{cid}-c{i}">'
        + (f'<span class="cgic">{icons.icon(icons_[i], 40)}</span>'
           if icons_ and i < len(icons_) else "")
        + f'{esc(c)}</div>'
        for i, c in enumerate(chips))
    css = f"""
{p} .cgwrap{{width:{BOARD_W}px;display:flex;flex-direction:column;
  align-items:center;gap:30px}}
{p} .cgkick{{font-family:{MONO};font-weight:700;font-size:24px;letter-spacing:.18em;
  color:{C['text3']};opacity:0}}
{p} .cggrid{{display:flex;flex-wrap:wrap;gap:18px;justify-content:center}}
{p} .cgchip{{background:{C['surface2']};border:1px solid {TK.LINE};
  border-radius:{RADIUS['pill']}px;padding:24px 36px;font-family:{FONT};
  font-weight:800;font-size:44px;letter-spacing:-.02em;color:{C['text']};
  box-shadow:{TK.SHADOW};opacity:0;white-space:nowrap;
  display:flex;align-items:center;gap:18px}}
{p} .cgic{{display:flex;color:{C['accent_hi']};flex:0 0 auto}}
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
  color:{C['accent_hi']};background:{FILL['accent']};border-radius:{RADIUS['pill']}px;
  padding:12px 26px;opacity:0}}
{p} .kword{{font-family:{FONT};font-weight:900;font-size:{size}px;line-height:.94;
  letter-spacing:-.045em;color:{C['text']};opacity:0}}
{p} .kbar{{width:0;height:12px;border-radius:6px;background:{C['accent']}}}
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
    escrito para dos slugs. El hairline es `TK.LINE_HI` (no el `TK.LINE` de
    costumbre): compuesto sobre `surface` da 1.63:1 (`tokens.lift`), un
    margen real sobre el 1.11–1.18:1 de los dos tiles que motivaron el
    arreglo — con `TK.LINE` a secas quedaba en 1.29:1, apenas por encima del
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
    logo_html, _ratio = logos.mark(slug, 72, uid=cid)
    css = f"""
{p} .tc-card{{display:flex;align-items:center;justify-content:center}}
{p} .tc-tilt{{transform:perspective(1400px) rotateY(-6deg);transform-style:preserve-3d}}
{p} .tc-root{{display:flex;align-items:center;gap:30px;background:{C['surface']};
  border:1px solid {TK.LINE};border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW};
  padding:30px 46px}}
{p} .tc-logoframe{{flex:0 0 auto;width:112px;height:112px;
  border-radius:{RADIUS['md']}px;background:{C['bg']};border:1px solid {TK.LINE_HI};
  display:flex;align-items:center;justify-content:center;overflow:hidden}}
{p} .tc-logo{{opacity:0;display:flex;align-items:center;justify-content:center}}
{p} .tc-name{{display:flex;flex-direction:column;gap:8px;opacity:0}}
{p} .tc-kick{{font-family:{MONO};font-weight:700;font-size:22px;
  letter-spacing:.16em;color:{C['accent_hi']};text-transform:uppercase}}
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


def tool_pair(cid: str, left: dict, right: dict, at: list[float],
              kicker: str = "") -> tuple[str, str, list]:
    """Dos marcas y el `+` que las une, cada pieza clavada a su palabra.

    Nace de la pieza 16, cuyo guion nombra las dos marcas con casi cuatro
    segundos de separación: «una integración de **Claude**…» y, cuatro
    frases después, «**Canva**.». `tool_card` no sirve para eso —clava UNA
    marca a UNA palabra— y `tool_lineup` tampoco: aquella reúne marcas que
    YA se dijeron todas, aquí la segunda todavía no se ha dicho.

    **El hueco de la segunda marca se dibuja, no se deja en blanco.** La
    alternativa —montar la card ya ancha con la mitad derecha vacía— se
    descartó porque medio panel liso durante 3.6 s se lee como un panel roto,
    exactamente la trampa que `knowledge_base` documenta con `reveal` y
    `calendar` con su franja sin paciente. Y la otra alternativa —que la card
    crezca al llegar la segunda marca— anima `width`, que es reflow: el
    sistema solo mueve opacidad y transform (§6).

    Así que el slot vacío va con **borde discontinuo y sin relleno**, el mismo
    idioma que `calendar` ya usa para la hora sin paciente y `chat_unanswered`
    para la respuesta que no llega: lo que comunica es la AUSENCIA. Durante
    esos 3.6 s el frame plantea la pregunta que la palabra siguiente contesta.
    Al llegar su momento el slot se apaga (`badge-out`) y debajo aparece el
    marco real con la marca — dos elementos apilados, no un borde que muta,
    para que cada estado sea un `set` propio y el seek no dependa del anterior.

    `at` son TRES tiempos, en este orden: la marca izquierda, el `+` con el
    slot vacío, y la marca derecha.

    `logo_px` es opcional en cada lado y lo decide el llamador, como el
    `hairline` de `tool_recording`: este componente no conoce ningún slug
    especial. Existe porque no todas las marcas son cuadradas — la de Canva
    es un wordmark 80x30 (su CDN no publica icono, y el favicon que sí sale
    mide 32 px, por debajo del gate de resolución), y `_fit_svg` la contiene
    sin deformarla dentro de un cuadrado, lo que la deja a 56x21 en un marco
    de 140. Subiéndole el `logo_px` llena el marco a lo ancho y pesa lo mismo
    que un icono cuadrado al lado.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    frame = 140
    l_px = int(left.get("logo_px", 84))
    r_px = int(right.get("logo_px", 84))
    l_logo, _ = logos.mark(left["slug"], l_px, uid=f"{cid}-l")
    r_logo, _ = logos.mark(right["slug"], r_px, uid=f"{cid}-r")
    css = f"""
{p} .tp-card{{display:flex;align-items:center;justify-content:center}}
{p} .tp-tilt{{transform:perspective(1400px) rotateY(-6deg);transform-style:preserve-3d}}
{p} .tp-root{{display:flex;flex-direction:column;align-items:center;gap:26px;
  background:{C['surface']};border:1px solid {TK.LINE};border-radius:{RADIUS['lg']}px;
  box-shadow:{TK.SHADOW};padding:34px 54px}}
{p} .tp-kick{{font-family:{MONO};font-weight:700;font-size:22px;
  letter-spacing:.16em;color:{C['accent_hi']};text-transform:uppercase;opacity:0}}
{p} .tp-row{{display:flex;align-items:center;gap:30px}}
{p} .tp-cell{{display:flex;flex-direction:column;align-items:center;gap:14px;
  width:{frame}px}}
{p} .tp-frame{{width:{frame}px;height:{frame}px;border-radius:{RADIUS['md']}px;
  background:{C['bg']};border:1px solid {TK.LINE_HI};display:flex;
  align-items:center;justify-content:center;overflow:hidden}}
{p} .tp-name{{font-family:{MONO};font-weight:700;font-size:20px;letter-spacing:.05em;
  color:{C['text2']};text-transform:uppercase;white-space:nowrap}}
{p} .tp-plus{{font-family:{FONT};font-weight:900;font-size:64px;line-height:1;
  color:{C['accent_hi']};opacity:0;margin-bottom:34px}}
{p} .tp-slotwrap{{position:relative;width:{frame}px;height:{frame}px}}
{p} .tp-slot{{position:absolute;inset:0;border-radius:{RADIUS['md']}px;
  border:2px dashed {TK.LINE_HI};background:none;opacity:0}}
{p} .tp-fill{{position:absolute;inset:0;opacity:0}}
{p} .tp-right{{opacity:0}}
{p} .tp-leftcell{{opacity:0}}"""
    html = (f'<div class="tp-card"><div class="tp-tilt"><div class="tp-root">'
            + (f'<div class="tp-kick" id="{cid}-kick">{esc(kicker)}</div>'
               if kicker else "")
            + f'<div class="tp-row">'
              f'<div class="tp-cell tp-leftcell" id="{cid}-l">'
              f'<div class="tp-frame">{l_logo}</div>'
              f'<div class="tp-name">{esc(left["name"])}</div></div>'
              f'<div class="tp-plus" id="{cid}-plus">+</div>'
              f'<div class="tp-cell">'
              f'<div class="tp-slotwrap">'
              f'<div class="tp-slot" id="{cid}-slot"></div>'
              f'<div class="tp-fill" id="{cid}-fill">'
              f'<div class="tp-frame">{r_logo}</div></div>'
              f'</div>'
              f'<div class="tp-name tp-right" id="{cid}-rname">'
              f'{esc(right["name"])}</div></div>'
              f'</div></div></div></div>')
    t_left, t_slot, t_right = at[0], at[1], at[2]
    anims = []
    if kicker:
        anims.append(("chip-in", f"#{cid}-kick", max(0.0, t_left - .04), .28))
    anims.append(
        # La marca que ya se dijo entra como en `tool_card`: viaje corto en
        # horizontal, no un fundido plano.
        ("glide-x", f"#{cid}-l", t_left, .45))
    if t_slot < t_right:
        anims += [
            # El `+` y el hueco entran JUNTOS: son la misma frase visual
            # («falta algo aquí»). Separarlos deja un `+` colgando de la nada.
            ("punch", f"#{cid}-plus", t_slot, .34),
            ("chip-in", f"#{cid}-slot", t_slot, .30),
            # Y el relevo: el hueco se apaga y la marca real ocupa su sitio.
            ("badge-out", f"#{cid}-slot", t_right, .18),
        ]
    else:
        # **La reaparición de la pareja YA FORMADA no pasa por el hueco.** La
        # pieza 16 la usa dos veces: la primera plantea la ausencia, y la
        # segunda —«sin estar saltando entre aplicaciones», con las dos marcas
        # dichas hace rato— solo tiene que enseñarlas juntas. Con `t_slot`
        # igual o posterior a `t_right`, el hueco no se emite en absoluto: un
        # `chip-in` y un `badge-out` sobre el MISMO elemento en el mismo
        # instante son dos tweens peleándose por la propiedad `opacity`, y de
        # cuál gane depende el orden de evaluación — justo lo que rompe un
        # render determinista (la razón del `overwrite: "auto"` de `click`).
        # El slot se queda en su `opacity:0` de origen, sin tween ninguno.
        anims.append(("punch", f"#{cid}-plus", t_right, .34))
    anims += [
        ("chip-in", f"#{cid}-fill", t_right, .34),
        ("drop-in", f"#{cid}-rname", t_right + .08, .34),
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

    ⚠ **La cabecera es OPACA, y antes no lo era.** Nació con
    el suelo al 72 % de opacidad, que sobre las cuatro grabaciones OSCURAS de la
    pieza 15 se leía como un cristal elegante. Sobre la grabación de Composio
    —documentación con fondo BLANCO— el texto de la página se transparentaba
    por detrás del chip y del nombre: dos textos superpuestos, cazado sobre un
    snapshot en t=42 de la pieza 16. La legibilidad de esta barra no puede
    depender de lo que haya debajo, que es material que el componente no
    controla; el alto de 84 px se paga igual sea opaca o translúcida. Blanco
    sobre `surface` da 17.73:1, medido en los tokens.

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
    chip_html, _ratio = logos.mark(slug, 40, uid=cid)
    head_h = 84
    css = f"""
{p} .tr-panel{{position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;
  border-radius:{RADIUS['lg']}px;overflow:hidden;pointer-events:none;
  border:{hairline}px solid {TK.LINE_HI};box-shadow:{TK.SHADOW};z-index:11}}
{p} .tr-head{{position:absolute;left:0;top:0;width:100%;height:{head_h}px;
  display:flex;align-items:center;gap:16px;padding:0 26px;
  background:{C['surface']};border-bottom:1px solid {TK.LINE_HI};opacity:0}}
{p} .tr-chip{{flex:0 0 auto;width:40px;height:40px;border-radius:{RADIUS['sm']}px;
  background:{C['bg']};border:1px solid {TK.LINE_HI};display:flex;align-items:center;
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


def claude_prompt(cid: str, lines: list[str], at: list[float],
                  rect: tuple[int, int, int, int] = (60, 100, 960, 540),
                  slug: str = "claude", name: str = "Claude",
                  model: str = "Opus 5",
                  placeholder: str = "Escribe / para ver habilidades",
                  chips: tuple[str, ...] = ("Chat", "Cowork"),
                  active_chip: str = "Cowork",
                  connector: dict | None = None,
                  connector_at: float | None = None,
                  attachment: dict | None = None,
                  attach_at: float | None = None) -> tuple[str, str, list]:
    """El compositor de un asistente, escribiéndose línea a línea.

    Es un MOCKUP declarado, no la captura redibujada (§7): lleva la
    tipografía y la paleta del sistema, y lo que lo ata a la
    marca es el logo de la cabecera, igual que el chip de `tool_recording`.
    La estructura sí sale de la captura real que trajo la pieza 16
    (`VIDEOS ORIGINALES/2/chat_claude.png`): campo grande, fila de `+`,
    conmutador Chat/Cowork y el modelo a la derecha.

    **Cada línea se teclea en SU palabra.** `at` trae un tiempo por línea, en
    offsets del visual, y el beat que lo pide («le das contexto… el formato…
    la idea… las referencias») no es que exista un prompt largo, es que se
    construye por partes — un fundido del bloque entero contaría otra cosa.

    ⚠ **Una línea terminada se queda sin cursor, y hace falta decirlo.**
    `type-word` mete el `<span class="ccaret">` DENTRO del innerHTML de su
    destino, así que con cuatro líneas seguidas acabarían cuatro cursores
    parpadeando a la vez. Por eso cada línea recibe además un `caret-off` en
    el instante en que arranca la siguiente (la última, al final del visual):
    el cursor viaja, no se multiplica. `caret-off` se añadió a
    `build-composition.py` para esto.

    El `placeholder` se apaga cuando entra la primera línea, no antes: si
    desapareciera con el panel, el campo pasaría por un estado vacío que la
    UI real nunca tiene.

    `attachment` es el ARCHIVO adjunto (pieza 17): la ficha que aparece en el
    campo cuando se sube un currículum antes de escribir el prompt. Entra
    ANTES que la primera línea y por eso tiene su propio `attach_at` — el beat
    del guion es «lo subes a una IA **y** escribes», dos acciones en ese orden,
    y un adjunto que apareciera con el texto las fundiría en una. Va dentro del
    campo y no en la barra de abajo porque ahí es donde lo pone la UI real: la
    barra es para lo que MODIFICA el envío (el conector), no para su contenido.

    ⚠ **El adjunto apaga el placeholder igual que lo haría una línea de texto.**
    Si solo lo apagara la primera línea, el campo pasaría unos frames con la
    ficha del archivo puesta y «Escribe / para ver habilidades» debajo, un
    estado que la UI real nunca tiene.

    `connector` es la pastilla de app conectada («Canva») que se enciende en
    la barra al decirse su nombre — el beat de «haces que Claude trabaje con
    Canva dentro del mismo proceso». Es opcional porque la primera instancia
    de esta card, la del prompt pobre, no lleva ninguna: el contraste entre
    las dos es justo el argumento, y se lee con un CORTE DURO entre ellas,
    como `chat_unanswered` documenta.
    """
    x, y, w, h = rect
    p = f'.viz[data-viz-id="{cid}"]'
    head_h, bar_h = 92, 104
    logo_html, _ratio = logos.mark(slug, 44, uid=f"{cid}-head")
    chips_html = "".join(
        f'<span class="cp-chip{" on" if c == active_chip else ""}">{esc(c)}</span>'
        for c in chips)
    conn_html = ""
    if connector:
        conn_logo, _ = logos.mark(connector["slug"], 26, uid=f"{cid}-conn")
        conn_html = (f'<span class="cp-conn" id="{cid}-conn">'
                     f'<span class="cp-connmark">{conn_logo}</span>'
                     f'{esc(connector["name"])}</span>')
    att_html = ""
    if attachment:
        att_html = (
            f'<div class="cp-att" id="{cid}-att">'
            f'<span class="cp-attico">'
            f'<svg viewBox="0 0 24 24" width="26" height="26" fill="none" '
            f'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round">'
            f'<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>'
            f'<path d="M14 3v5h5"/></svg></span>'
            f'<span class="cp-attxt">'
            f'<span class="cp-attname">{esc(attachment["name"])}</span>'
            f'<span class="cp-attmeta">{esc(attachment.get("meta", ""))}</span>'
            f'</span></div>')
    rows = "".join(
        f'<div class="cp-line" id="{cid}-l{i}"></div>' for i in range(len(lines)))
    css = f"""
{p} .cp-panel{{position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;
  background:{C['surface']};border:1px solid {TK.LINE_HI};
  border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW_LIFT};overflow:hidden;
  display:flex;flex-direction:column;opacity:0}}
{p} .cp-head{{flex:0 0 {head_h}px;display:flex;align-items:center;gap:18px;
  padding:0 30px;border-bottom:1px solid {TK.LINE};opacity:0}}
{p} .cp-mark{{width:52px;height:52px;border-radius:{RADIUS['sm']}px;
  background:{C['bg']};border:1px solid {TK.LINE_HI};display:flex;
  align-items:center;justify-content:center;overflow:hidden;flex:0 0 auto;
  transform:perspective(800px) rotateY(-8deg);transform-style:preserve-3d}}
{p} .cp-title{{font-family:{FONT};font-weight:800;font-size:30px;
  letter-spacing:-.02em;color:{C['text']}}}
{p} .cp-model{{margin-left:auto;font-family:{MONO};font-weight:700;font-size:20px;
  letter-spacing:.10em;color:{C['text3']};text-transform:uppercase}}
{p} .cp-body{{flex:1 1 auto;padding:30px 34px;display:flex;flex-direction:column;
  gap:14px;min-height:0}}
{p} .cp-ph{{font-family:{FONT};font-weight:500;font-size:34px;
  letter-spacing:-.01em;color:{C['text3']}}}
{p} .cp-line{{font-family:{FONT};font-weight:700;font-size:34px;line-height:1.28;
  letter-spacing:-.01em;color:{C['text']};white-space:nowrap;overflow:hidden}}
{p} .ccaret{{display:inline-block;width:4px;height:34px;background:{C['accent']};
  vertical-align:-6px;margin-left:6px}}
{p} .cp-att{{display:flex;align-items:center;gap:16px;align-self:flex-start;
  background:{C['surface2']};border:1px solid {TK.LINE_HI};
  border-radius:{RADIUS['md']}px;padding:16px 22px;margin-bottom:6px;opacity:0}}
{p} .cp-attico{{width:48px;height:48px;border-radius:{RADIUS['sm']}px;
  background:{FILL['accent']};border:1px solid {accent_a(.42)};
  color:{C['accent_hi']};display:flex;align-items:center;justify-content:center;
  flex:0 0 auto}}
{p} .cp-attxt{{display:flex;flex-direction:column;gap:5px}}
{p} .cp-attname{{font-family:{FONT};font-weight:800;font-size:27px;
  letter-spacing:-.015em;color:{C['text']};line-height:1.1}}
{p} .cp-attmeta{{font-family:{MONO};font-weight:700;font-size:17px;
  letter-spacing:.11em;text-transform:uppercase;color:{C['text3']}}}
{p} .cp-bar{{flex:0 0 {bar_h}px;display:flex;align-items:center;gap:16px;
  padding:0 30px;border-top:1px solid {TK.LINE};opacity:0}}
{p} .cp-plus{{font-family:{FONT};font-weight:400;font-size:40px;line-height:1;
  color:{C['text3']};flex:0 0 auto}}
{p} .cp-chip{{font-family:{FONT};font-weight:700;font-size:24px;
  letter-spacing:-.01em;color:{C['text3']};border-radius:{RADIUS['sm']}px;
  padding:10px 20px}}
{p} .cp-chip.on{{color:{C['text']};background:{C['surface2']};
  border:1px solid {TK.LINE_HI}}}
{p} .cp-conn{{margin-left:auto;display:flex;align-items:center;gap:12px;
  font-family:{MONO};font-weight:700;font-size:21px;letter-spacing:.08em;
  text-transform:uppercase;color:{C['accent_lt']};background:{FILL['accent']};
  border:1px solid {accent_a(.42)};border-radius:{RADIUS['pill']}px;
  padding:11px 22px;opacity:0}}
{p} .cp-connmark{{width:26px;height:26px;display:flex;align-items:center;
  justify-content:center;overflow:hidden;flex:0 0 auto}}"""
    html = (f'<div class="cp-panel" id="{cid}-panel">'
            f'<div class="cp-head" id="{cid}-head">'
            f'<span class="cp-mark">{logo_html}</span>'
            f'<span class="cp-title">{esc(name)}</span>'
            f'<span class="cp-model">{esc(model)}</span></div>'
            f'<div class="cp-body">'
            f'<div class="cp-ph" id="{cid}-ph">{esc(placeholder)}</div>'
            f'{att_html}{rows}</div>'
            f'<div class="cp-bar" id="{cid}-bar">'
            f'<span class="cp-plus">+</span>{chips_html}{conn_html}</div>'
            f'</div>')
    # Nada de dentro entra antes de que el panel sea opaco: dos fundidos
    # encadenados multiplican opacidades y el texto pasa unas décimas por
    # debajo del contraste declarado. Misma regla que `comment_ui`.
    anims = [
        ("rise-in", f"#{cid}-panel", .04, .42),
        ("slide-in", f"#{cid}-head", .14, .30),
        ("chip-in", f"#{cid}-bar", .22, .30),
    ]
    # El placeholder se apaga con lo PRIMERO que entre al campo, sea el
    # adjunto o la primera línea (ver el aviso del docstring).
    first_in = [t for t in (attach_at, at[0] if lines else None) if t is not None]
    if first_in:
        anims.append(("badge-out", f"#{cid}-ph", min(first_in), .16))
    if attachment and attach_at is not None:
        anims.append(("rise-in", f"#{cid}-att", attach_at, .34))
    for i, line in enumerate(lines):
        anims.append(("type-word", f"#{cid}-l{i}", at[i], .62, line))
        # El cursor se apaga cuando arranca la línea siguiente. La última no
        # tiene siguiente: se queda parpadeando hasta el corte, que es lo que
        # hace una caja de texto con el foco puesto.
        if i + 1 < len(lines):
            anims.append(("caret-off", f"#{cid}-l{i}", at[i + 1], .01, line))
    if connector and connector_at is not None:
        anims.append(("chip-in", f"#{cid}-conn", connector_at, .34))
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
    hairline `TK.LINE_HI` + fondo `bg`) en vez de inventar uno nuevo — la CSS de
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
        logo_html, _ratio = logos.mark(slug, 56, uid=f"{cid}-t{i}")
        tiles.append(
            f'<div class="tlcell" id="{cid}-t{i}">'
            f'<div class="tlframe">{logo_html}</div>'
            f'<div class="tlname">{esc(name)}</div></div>')
    css = f"""
{p} .tlwrap{{display:flex;flex-direction:column;align-items:center;gap:22px}}
{p} .tlkick{{font-family:{MONO};font-weight:700;font-size:24px;letter-spacing:.18em;
  color:{C['accent_hi']};background:{FILL['accent']};border-radius:{RADIUS['pill']}px;
  padding:10px 24px;opacity:0}}
{p} .tlrow{{display:flex;gap:22px;align-items:flex-start}}
{p} .tlcell{{display:flex;flex-direction:column;align-items:center;gap:12px;opacity:0}}
{p} .tlframe{{width:104px;height:104px;border-radius:{RADIUS['md']}px;
  background:{C['bg']};border:1px solid {TK.LINE_HI};display:flex;
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


def layer_stack(cid: str, apps: list[dict], at: list[float],
                layer_slug: str = "claude", layer_name: str = "CLAUDE",
                layer_at: float = 1.2,
                kicker: str = "") -> tuple[str, str, list]:
    """Una capa por encima de una fila de herramientas.

    La tesis de la pieza 16 —«no es automatizar Canva, es usar Claude como una
    CAPA encima de tus herramientas»— es una frase espacial, y por eso no la
    sirve ninguno de los mockups que ya había: `connection_map` dibuja un hub
    con radios (está al lado de sus módulos, no encima) y `flow_steps` dibuja
    una secuencia (primero uno, después otro). Encima es otra cosa.

    **Entra en dos tiempos y ese reparto ES el argumento.** Primero la fila de
    apps sola, en «la oportunidad no es automatizar Canva» — las herramientas
    sueltas, que es justo lo que la frase descarta. Y solo al decirse «capa»
    baja el panel de arriba con sus bajantes. Adelantarlo rompería «nada entra
    antes de su palabra» (§7) y, peor, contaría la conclusión mientras se
    enuncia la premisa contraria.

    Las bajantes se dibujan con `draw` (stroke-dashoffset), no con un fundido:
    lo que se afirma es que la capa ALCANZA cada herramienta, y un trazo que
    se dibuja de arriba abajo lo dice; una línea que aparece entera, no.

    Una app sin `slug` se pinta como TESELA MUDA (un cuadrado con el hairline
    del sistema y sin marca). No es decoración: el guion dice «muchísimas
    otras aplicaciones» sin nombrar ninguna, y poner logos que nadie mencionó
    sería adelantar guion que no existe. La ausencia de marca es el dato.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    tile = 118
    gap = 26
    n = len(apps)
    row_w = n * tile + (n - 1) * gap
    cells, drops = [], []
    for i, app in enumerate(apps):
        if app.get("slug"):
            inner, _ = logos.mark(app["slug"], int(app.get("logo_px", 66)),
                                  uid=f"{cid}-a{i}")
        else:
            inner = '<span class="ls-mute"></span>'
        label = esc(app.get("name", ""))
        cells.append(f'<div class="ls-cell" id="{cid}-a{i}">'
                     f'<div class="ls-tile">{inner}</div>'
                     + (f'<div class="ls-name">{label}</div>' if label else "")
                     + "</div>")
        # La bajante cae desde el borde inferior del panel hasta el techo de
        # su tesela, centrada en ella. Coordenadas del propio SVG, no del
        # lienzo: el bloque se centra con flex y el SVG viaja con él.
        cx = i * (tile + gap) + tile / 2
        drops.append(f'<path class="ls-drop" id="{cid}-d{i}" d="M{cx:.1f} 0 '
                     f'L{cx:.1f} 46" stroke="{C["accent"]}" stroke-width="3" '
                     f'stroke-linecap="round" fill="none"/>')
    css = f"""
{p} .ls-wrap{{display:flex;flex-direction:column;align-items:center;gap:0}}
{p} .ls-kick{{font-family:{MONO};font-weight:700;font-size:22px;letter-spacing:.18em;
  color:{C['accent_hi']};text-transform:uppercase;margin-bottom:22px;opacity:0}}
{p} .ls-layer{{display:flex;align-items:center;justify-content:center;gap:22px;
  width:{row_w}px;background:{C['surface']};border:1px solid {TK.LINE_HI};
  border-radius:{RADIUS['lg']}px;box-shadow:{TK.GLOW};padding:26px 0;opacity:0}}
{p} .ls-lmark{{width:62px;height:62px;border-radius:{RADIUS['sm']}px;
  background:{C['bg']};border:1px solid {TK.LINE_HI};display:flex;
  align-items:center;justify-content:center;overflow:hidden;flex:0 0 auto}}
{p} .ls-lname{{font-family:{FONT};font-weight:900;font-size:46px;line-height:1;
  letter-spacing:-.03em;color:{C['text']}}}
{p} .ls-drops{{width:{row_w}px;height:46px;display:block}}
{p} .ls-row{{display:flex;gap:{gap}px;align-items:flex-start}}
{p} .ls-cell{{display:flex;flex-direction:column;align-items:center;gap:12px;
  width:{tile}px;opacity:0}}
{p} .ls-tile{{width:{tile}px;height:{tile}px;border-radius:{RADIUS['md']}px;
  background:{C['bg']};border:1px solid {TK.LINE_HI};display:flex;
  align-items:center;justify-content:center;overflow:hidden}}
{p} .ls-mute{{width:46px;height:46px;border-radius:{RADIUS['sm']}px;
  border:2px solid {TK.LINE_HI};background:{FILL['ink']}}}
{p} .ls-name{{font-family:{MONO};font-weight:700;font-size:17px;letter-spacing:.05em;
  color:{C['text2']};text-transform:uppercase;white-space:nowrap}}"""
    layer_logo, _ = logos.mark(layer_slug, 40, uid=f"{cid}-layer")
    html = (f'<div class="ls-wrap">'
            + (f'<div class="ls-kick" id="{cid}-kick">{esc(kicker)}</div>'
               if kicker else "")
            + f'<div class="ls-layer" id="{cid}-layer">'
              f'<span class="ls-lmark">{layer_logo}</span>'
              f'<span class="ls-lname">{esc(layer_name)}</span></div>'
              f'<svg class="ls-drops" viewBox="0 0 {row_w} 46" '
              f'xmlns="http://www.w3.org/2000/svg">{"".join(drops)}</svg>'
              f'<div class="ls-row">{"".join(cells)}</div></div>')
    anims = []
    if kicker:
        # El kicker entra CON LA CAPA, no con la fila. Nombra la idea («una
        # capa encima») y esa palabra se dice al final del beat: puesto con la
        # fila, el espectador la lee casi cinco segundos antes de oírla —
        # «nada entra antes de su palabra» (§7) aplica al texto igual que a un
        # logo. Cazado sobre un snapshot en t=45.5 de la pieza 16.
        anims.append(("chip-in", f"#{cid}-kick", layer_at, .28))
    for i in range(n):
        anims.append(("chip-in", f"#{cid}-a{i}",
                      at[i] if i < len(at) else .20 + i * .18, .30))
    # La capa baja (`drop-in`, de arriba abajo — el único recorrido que dice
    # «encima»), y las bajantes se dibujan detrás de ella, escalonadas para
    # que se lean como un alcance progresivo y no como una reja que aparece.
    anims.append(("drop-in", f"#{cid}-layer", layer_at, .46))
    for i in range(n):
        anims.append(("draw", f"#{cid}-d{i}", layer_at + .22 + i * .07, .30))
    return css, html, anims


# ── cadena de consecuencias ───────────────────────────────────────────────────
def flow_steps(cid: str, steps: list[str], at: list[float],
               tone: str = "ok",
               icons_: list[str] | None = None) -> tuple[str, str, list]:
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
        # `icons_` es de la pieza 19 y es opcional: sin él el marcado no
        # cambia ni un byte, que es lo que deja intactas a las piezas 4 y 11.
        ic = (f'<span class="fic">{icons.icon(icons_[i], 40)}</span>'
              if icons_ and i < len(icons_) else "")
        rows.append(
            f'<div class="fstep{cls}" id="{cid}-f{i}">'
            f'<span class="fnum">{i+1:02d}</span>{ic}{esc(s)}'
            f'<span class="fok">{glyph}</span></div>')
    css = f"""
{p} .fflow{{display:flex;flex-direction:column;align-items:center;gap:8px;width:{BOARD_W}px}}
{p} .fstep{{width:100%;display:flex;align-items:center;gap:22px;
  background:{C['surface']};border:1px solid {TK.LINE};border-radius:{RADIUS['md']}px;
  padding:28px 30px;font-family:{FONT};font-weight:700;font-size:40px;
  letter-spacing:-.02em;color:{C['text']};box-shadow:{TK.SHADOW};opacity:0}}
{p} .fstep.hot{{border-color:{accent_a(.5)};
  background:linear-gradient(90deg,{FILL['accent']} 0%,{C['surface']} 62%)}}
{p} .fstep.bad{{border-color:rgba(255,90,90,.45);
  background:linear-gradient(90deg,{FILL['alert']} 0%,{C['surface']} 62%);
  color:{C['alert']}}}
{p} .fnum{{font-family:{MONO};font-weight:700;font-size:22px;letter-spacing:.12em;
  color:{C['accent_hi']};flex:0 0 auto}}
{p} .fic{{display:flex;flex:0 0 auto;color:{C['accent_hi']};margin-right:-6px}}
{p} .fstep.bad .fic{{color:{C['alert']}}}
{p} .fstep.bad .fnum{{color:{C['alert']}}}
{p} .fok{{margin-left:auto;color:{C['go']};font-size:36px;font-weight:900}}
{p} .fstep.hot .fok{{color:{C['accent_hi']}}}
{p} .fstep.bad .fok{{color:{C['alert']}}}
{p} .farrow{{font-family:{FONT};font-size:34px;font-weight:700;color:{C['accent']};
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
        svg, _ratio = logos.mark(brand, 44, "brand", uid=f"{cid}-brand")
        mk = f'<div class="chbrand" id="{cid}-brand">{svg}</div>'
    css = f"""
{p} .chwrap{{display:flex;flex-direction:column;align-items:center;gap:26px;width:{BOARD_W}px}}
{p} .chkick{{font-family:{MONO};font-weight:700;font-size:26px;letter-spacing:.20em;
  color:{C['text3']};opacity:0}}
{p} .chpane{{width:100%;height:880px;background:{C['surface']};border:1px solid {TK.LINE};
  border-radius:{RADIUS['xl']}px;box-shadow:{TK.SHADOW_LIFT};padding:0 0 34px;
  display:flex;flex-direction:column;overflow:hidden;opacity:0}}
{p} .chtop{{display:flex;align-items:center;gap:20px;padding:26px 30px;
  border-bottom:1px solid {TK.LINE};background:{C['surface2']}}}
{p} .chav{{width:58px;height:58px;border-radius:50%;flex:0 0 58px;
  background:linear-gradient(135deg,{C['surface3']} 0%,{C['bg2']} 100%);
  border:1px solid {TK.LINE_HI}}}
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
{p} .chbub{{max-width:78%;background:{FILL['accent2']};border:1px solid {accent_a(.34)};
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
  border:1px solid {TK.LINE_HI};border-radius:10px 24px 24px 24px;
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
  color:{C['accent_lt']};background:{FILL['accent']};border-radius:{RADIUS['pill']}px;
  padding:12px 26px;opacity:0;margin-bottom:-14px}}
{p} .cbox{{width:100%;display:flex;align-items:center;gap:20px;background:{C['surface']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['pill']}px;padding:22px 26px;
  box-shadow:{TK.SHADOW_LIFT};opacity:0}}
{p} .cav{{width:66px;height:66px;border-radius:50%;flex:0 0 66px;
  background:linear-gradient(135deg,{C['accent']} 0%,{C['accent_pill']} 100%)}}
{p} .cfield{{flex:1;min-width:0;font-family:{FONT};font-weight:700;font-size:42px;
  letter-spacing:-.01em;color:{C['text']};white-space:nowrap;overflow:hidden}}
{p} .cfield i{{color:{C['text3']};font-style:normal;font-weight:500}}
{p} .ccaret{{display:inline-block;width:4px;height:44px;background:{C['accent']};
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
    # ⚠ El primer gesto va en .03, no en .16. Medido sobre el MP4 de la pieza
    # 19: el relevo entre dos visuales ya cuesta ~130 ms de suelo
    # (§4, cobertura declarada ≠ luma renderizada) y cualquier retraso del
    # elemento ENTRANTE se suma a ese hueco en vez de esconderse dentro de él.
    # Con .16 el CTA abría con 203 ms de banda vacía; con .03, con los 133 del
    # relevo, que es el suelo del sistema y se lee como el CORTE DURO de §6.
    anims = []
    if headline:
        anims += [("chip-in", f"#{cid}-say", .03, .22),
                  ("punch", f"#{cid}-head", .14, .44)]
    anims += [
        ("chip-in", f"#{cid}-box", .32, .30),
        ("type-word", f"#{cid}-field", type_at, .70, esc(word)),
        ("send-on", f"#{cid}-send", send_at, .26),
        ("stamp", f"#{cid}-posted", send_at + .22, .38),
    ]
    return css, html, anims


# ── pieza 17 · el CV y sus cuatro pasos ───────────────────────────────────────
#
# Los seis componentes de abajo salen de un guion que enumera un PROCESO —
# cuatro pasos para trabajar un currículum con una IA— y de una instrucción del
# usuario que pedía dos cosas a la vez: enseñar los cuatro pasos de golpe y
# luego enseñarlos uno a uno. La librería no sabía contestar ninguna de las dos.
#
# `flow_steps`, que es la que más se le parece, encadena pasos con flechas y los
# marca ✓/✕: contesta «qué dispara qué», y aquí la pregunta es otra — los cuatro
# pasos no se disparan entre sí, son cuatro casillas de un método. Y sobre todo,
# `flow_steps` no tiene estado intermedio: sus pasos existen o no existen, y el
# beat de esta pieza necesita que EXISTAN VACÍOS y se llenen 30 s después.


def step_grid(cid: str, slots: list[str], at: list[float],
              kicker: str = "", numbers: bool = True,
              hot: int | None = None) -> tuple[str, str, list]:
    """Cuatro casillas numeradas que nacen VACÍAS y se llenan en su palabra.

    El hueco discontinuo es el mismo idioma que `calendar` usa para la hora sin
    paciente y `tool_pair` para la marca todavía sin nombrar: **lo que comunica
    es la ausencia**. Aquí resuelve de frente el choque entre lo que pidió el
    usuario —«muestra primero los 4 pasos»— y «nada entra antes de su palabra»
    (§7): la ESTRUCTURA entra entera al anunciarse («lo dividiría en 4 pasos»),
    y cada NOMBRE espera a que se diga. El espectador ve que faltan tres cosas
    sin leer cuáles, que es exactamente lo que el guion está diciendo.

    `slots` trae los cuatro textos y `at` un tiempo por slot; un slot con `at`
    en `None` se queda como hueco. Montar la rejilla ya llena y limitarse a
    resaltar la casilla de turno sería la otra lectura posible, y es la que el
    usuario descartó: adelanta «entrevista» 29 segundos.

    `hot` resalta una casilla YA llena (la del paso que se está explicando) sin
    volver a animarla — se usa en las instancias intermedias, que entran con las
    anteriores ya puestas.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    cells = []
    for i, s in enumerate(slots):
        on = i < len(at) and at[i] is not None
        cls = " hot" if (hot is not None and i == hot) else ""
        num = f'<span class="sgnum">{i+1:02d}</span>' if numbers else ""
        # ⚠ La casilla PENDIENTE sigue siendo un hueco hasta que le toca, y eso
        # no se arregla con una clase estática. Nació dándole `.on` —el relleno
        # sólido— a todo slot con `at`, y el snapshot en t=11 enseñó el
        # resultado: una caja sólida y VACÍA entre tres huecos discontinuos, o
        # sea la lectura de «panel roto» que `knowledge-base` ya documenta con
        # `reveal`. El relleno es una capa aparte (`.sgfill`) que se enciende en
        # la misma palabra que el texto, y la raya se apaga en ese instante.
        fill = f'<span class="sgfill" id="{cid}-f{i}"></span>' if on else ""
        # El `.sgtxt` se emite SIEMPRE, vacío en la casilla pendiente: así la
        # caja mide lo mismo llena que vacía y la rejilla no da un salto de
        # layout al llenarse. Lo que va fuera del flujo es la RAYA, que es la
        # decoración que desaparece; sacar el texto en su lugar lo montaba
        # encima del número (14 errores de `content_overlap`).
        dash = (f'<span class="sgdash" id="{cid}-d{i}"></span>' if on
                else '<span class="sgdash"></span>')
        # ⚠ El nombre de una casilla PENDIENTE no se emite, ni siquiera a
        # opacidad 0: «nada entra antes de su palabra» es sobre el DOM, no
        # sobre lo que se ve. El span va vacío para conservar el alto —que es
        # lo único que hacía falta— y el texto llega con su `at`.
        cells.append(
            f'<div class="sgcell{cls}" id="{cid}-c{i}">{fill}{num}'
            f'<span class="sgtxt" id="{cid}-t{i}">{esc(s) if on else ""}</span>'
            f'{dash}</div>')
    kick = f'<div class="sgkick" id="{cid}-kick">{esc(kicker)}</div>' if kicker else ""
    css = f"""
{p} .sgwrap{{display:flex;flex-direction:column;align-items:center;gap:20px;
  width:{BOARD_W}px}}
{p} .sgkick{{font-family:{MONO};font-weight:700;font-size:23px;letter-spacing:.16em;
  text-transform:uppercase;color:{C['accent_hi']};opacity:0}}
{p} .sggrid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;width:100%}}
{p} .sgcell{{position:relative;height:196px;border-radius:{RADIUS['md']}px;
  padding:24px 28px;display:flex;flex-direction:column;gap:14px;
  justify-content:flex-start;background:transparent;
  border:2px dashed {C['text3']};opacity:0}}
{p} .sgfill{{position:absolute;inset:-2px;border-radius:{RADIUS['md']}px;
  background:{C['surface']};border:1px solid {TK.LINE_HI};box-shadow:{TK.SHADOW};
  opacity:0;z-index:0}}
{p} .sgcell.hot .sgfill{{border-color:{accent_a(.55)};
  background:linear-gradient(135deg,{C['accent_pill']} 0%,{C['surface']} 64%)}}
{p} .sgnum{{position:relative;z-index:1;font-family:{MONO};font-weight:700;
  font-size:24px;letter-spacing:.14em;color:{C['text3']}}}
{p} .sgtxt{{position:relative;z-index:1;min-height:90px;
  font-family:{FONT};font-weight:900;font-size:42px;line-height:1.06;
  letter-spacing:-.025em;color:{C['text']};opacity:0}}
{p} .sgdash{{position:absolute;z-index:1;left:28px;top:102px;height:14px;
  width:52%;border-radius:{RADIUS['pill']}px;border:2px dashed {C['text3']}}}"""
    anims = [("chip-in", f"#{cid}-kick", .10, .26)] if kicker else []
    # La rejilla entra como una sola cosa: cuatro entradas escalonadas de 90 ms
    # son un gesto, no cuatro decisiones editoriales (la lección de la
    # coreografía interna de la pieza 12).
    for i in range(len(slots)):
        anims.append(("chip-in", f"#{cid}-c{i}", .06 + i * .09, .30))
    for i, t in enumerate(at):
        if t is not None:
            anims.append(("chip-in", f"#{cid}-f{i}", t, .30))
            anims.append(("badge-out", f"#{cid}-d{i}", t, .16))
            anims.append(("punch", f"#{cid}-t{i}", t, .40))
    return css, f'<div class="sgwrap">{kick}<div class="sggrid">{"".join(cells)}</div></div>', anims


def _cv_card(cid: str, iid: str, title: str, sub: str, rows: list[dict],
             width: int, tag: str = "", tag_tone: str = "",
             marks: str = "") -> tuple[str, str]:
    """Un documento que se lee como un CV sin ser una captura redibujada (§7).

    La estructura la hace legible de un vistazo: cabecera con nombre y rol, y
    debajo filas de secciones donde el TEXTO es la etiqueta y la BARRA es el
    cuerpo. Las barras son deterministas —se declaran en `rows`, no salen de un
    `random`— por la misma razón que las de `spreadsheet`: un golden file no
    puede depender del azar, y el contenido concreto de la línea no es el
    argumento.

    `tone` por fila: `plain` (gris, existe), `hot` (acento, es lo que se está
    señalando) y `bad` (alert, es un desajuste). Un `bad` no tiñe la tarjeta
    entera: teñirla convertiría «a este CV le faltan cosas» en «este CV está
    roto», que es otra frase — la misma lección que `flow_steps` con `fail`.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    rs = []
    for i, r in enumerate(rows):
        tone = r.get("tone", "plain")
        bar = (f'<span class="cvbar {tone}" style="width:{r["w"]}%"></span>'
               if r.get("w") else "")
        lab = f'<span class="cvlab {tone}">{esc(r["label"])}</span>' if r.get("label") else ""
        rs.append(f'<div class="cvrow" id="{iid}-r{i}">{lab}{bar}</div>')
    tg = (f'<span class="cvtag {tag_tone}">{esc(tag)}</span>') if tag else ""
    css = f"""
{p} #{iid}{{width:{width}px;background:{C['surface']};border:1px solid {TK.LINE_HI};
  border-radius:{RADIUS['md']}px;box-shadow:{TK.SHADOW};padding:26px 26px 28px;
  display:flex;flex-direction:column;gap:18px;opacity:0}}
{p} #{iid} .cvhead{{display:flex;align-items:flex-start;gap:14px}}
{p} #{iid} .cvname{{min-height:70px}}
{p} #{iid} .cvname{{font-family:{FONT};font-weight:900;font-size:34px;
  letter-spacing:-.025em;color:{C['text']};line-height:1.04}}
{p} #{iid} .cvsub{{font-family:{MONO};font-weight:700;font-size:19px;
  letter-spacing:.10em;text-transform:uppercase;color:{C['text3']};
  margin-top:8px;display:block}}"""
    # La etiqueta va en su PROPIA fila, encima del nombre. Puesta al lado, un
    # nombre corto («Laura Méndez») convive con ella y uno largo («Growth
    # Marketing Manager») se parte en dos líneas: las dos tarjetas del par
    # dejan de tener la misma altura de cabecera y se leen como desalineadas.
    # Cazado sobre un snapshot en t=8.2, nunca en el JSON.
    html = (f'<div id="{iid}">{tg}<div class="cvhead"><div>'
            f'<div class="cvname">{esc(title)}</div>'
            f'<span class="cvsub">{esc(sub)}</span></div></div>'
            f'<div class="cvrows">{"".join(rs)}{marks}</div></div>')
    return css, html


def _cv_css(p: str) -> str:
    """Las reglas COMPARTIDAS por todas las tarjetas de CV de una composición.

    Van aparte de `_cv_card` porque dos tarjetas en el mismo visual las
    repetirían idénticas, y una tercera regla con el mismo selector es peso
    muerto en un archivo que ya avisa `composition_file_too_large`.
    """
    return f"""
{p} .cvrows{{position:relative;display:flex;flex-direction:column;gap:13px}}
{p} .cvrow{{display:flex;flex-direction:column;gap:7px}}
{p} .cvlab{{font-family:{FONT};font-weight:700;font-size:23px;
  letter-spacing:-.01em;color:{C['text2']};line-height:1.2}}
{p} .cvlab.hot{{color:{C['accent_hi']}}}
{p} .cvlab.bad{{color:{C['alert']}}}
{p} .cvbar{{height:12px;border-radius:{RADIUS['pill']}px;
  background:rgba(167,173,187,.30);display:block}}
{p} .cvbar.hot{{background:{C['accent']}}}
{p} .cvbar.bad{{background:{C['alert']};opacity:.55}}
{p} .cvtag{{align-self:flex-start;font-family:{MONO};font-weight:700;font-size:17px;
  letter-spacing:.12em;text-transform:uppercase;color:{C['text3']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['pill']}px;padding:7px 14px;
  flex:0 0 auto}}
{p} .cvtag.hot{{color:{C['accent_hi']};border-color:{accent_a(.45)};
  background:{FILL['accent']}}}
{p} .cvtag.go{{color:{C['go']};border-color:rgba(52,227,155,.40)}}"""


def cv_echo(cid: str, left: dict, right: dict, seal: str,
            at: list[float], kicker: str = "") -> tuple[str, str, list]:
    """El mismo CV dos veces, y el `=` que lo dice.

    El beat es «estás desaprovechando casi todo lo que puede hacer»: lo que la
    IA devuelve con un prompt pobre no es un CV mejor, es el mismo CV con
    palabras más elegantes. Dibujar DOS documentos con **las mismas barras** y
    solo las etiquetas cambiadas deja ver eso sin una línea de texto que lo
    explique — la rima visual hace el argumento, igual que las dos instancias
    de `chat_unanswered` en la pieza 11.

    El `=` entra el ÚLTIMO, no a la vez que las tarjetas. Puesto desde el primer
    frame contaría el final antes del principio: primero se ve un antes y un
    después —que es lo que el espectador espera— y solo entonces el signo dice
    que son lo mismo. `at` trae [izquierda, derecha, signo].
    """
    p = f'.viz[data-viz-id="{cid}"]'
    cw = 442
    css_l, html_l = _cv_card(cid, f"{cid}-L", left["title"], left["sub"],
                             left["rows"], cw, left.get("tag", ""),
                             left.get("tag_tone", ""))
    css_r, html_r = _cv_card(cid, f"{cid}-R", right["title"], right["sub"],
                             right["rows"], cw, right.get("tag", ""),
                             right.get("tag_tone", "hot"))
    kick = f'<div class="cekick" id="{cid}-kick">{esc(kicker)}</div>' if kicker else ""
    css = _cv_css(p) + css_l + css_r + f"""
{p} .cewrap{{display:flex;flex-direction:column;align-items:center;gap:22px;
  width:{BOARD_W}px}}
{p} .cekick{{font-family:{MONO};font-weight:700;font-size:23px;letter-spacing:.16em;
  text-transform:uppercase;color:{C['text3']};opacity:0}}
{p} .cepair{{display:flex;align-items:flex-start;gap:96px;width:100%;
  position:relative}}
{p} .ceeq{{position:absolute;left:50%;top:50%;margin-left:-38px;margin-top:-38px;
  width:76px;height:76px;border-radius:{RADIUS['pill']}px;background:{C['bg']};
  border:1px solid {accent_a(.45)};box-shadow:{TK.GLOW};display:flex;
  align-items:center;justify-content:center;font-family:{FONT};font-weight:900;
  font-size:42px;color:{C['accent_hi']};opacity:0;z-index:3}}
{p} .ceseal{{font-family:{MONO};font-weight:700;font-size:22px;letter-spacing:.13em;
  text-transform:uppercase;color:{C['warn']};border:1px solid rgba(255,184,77,.42);
  background:rgba(255,184,77,.10);border-radius:{RADIUS['pill']}px;
  padding:12px 26px;opacity:0}}"""
    html = (f'<div class="cewrap">{kick}'
            f'<div class="cepair">{html_l}{html_r}'
            f'<div class="ceeq" id="{cid}-eq">=</div></div>'
            f'<div class="ceseal" id="{cid}-seal">{esc(seal)}</div></div>')
    anims = []
    if kicker:
        anims.append(("chip-in", f"#{cid}-kick", .08, .24))
    anims += [("rise-in", f"#{cid}-L", at[0], .34),
              ("rise-in", f"#{cid}-R", at[1], .34),
              ("stamp", f"#{cid}-eq", at[2], .36),
              ("chip-in", f"#{cid}-seal", at[2] + .22, .30)]
    return css, html, anims


def cv_vs_offer(cid: str, cv: dict, offer: dict, at: list[float],
                gaps: list[int], gap_at: float,
                kicker: str = "") -> tuple[str, str, list]:
    """El CV contra la vacante concreta, y los desajustes que salen.

    Es el paso 1 del guion («pídele que analice el currículum contra la vacante
    concreta y encuentre desajustes») y lo que tiene que verse es la
    CONFRONTACIÓN, no dos documentos que casualmente están al lado. Por eso las
    dos tarjetas comparten una línea de eje y los desajustes se marcan **en el
    lado del CV**: el que tiene el hueco es el candidato, no la oferta.

    `gaps` son los índices de fila del CV que se marcan, y entran TODOS en
    `gap_at` —la palabra «desajustes»— porque el guion los enuncia como un
    resultado único, no uno a uno. Marcarlos escalonados metería en el contrato
    creativo un ritmo que el transcript no dice.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    cw = 442
    cv_rows = [dict(r) for r in cv["rows"]]
    # El aro va DENTRO del contenedor de filas del CV, así que su origen NO
    # depende de lo alta que sea la cabecera de la tarjeta. La primera versión
    # lo colgaba de la tarjeta con un `top` calculado a mano y, al subir la
    # etiqueta a su propia fila, las tres marcas quedaron una fila por encima
    # de la suya — cazado sobre el snapshot de t=18.5, no por ningún gate.
    # Ahora solo depende del PITCH de fila: etiqueta 28 + hueco 7 + barra 12 +
    # gap 13 = 60.
    marks = "".join(
        f'<div class="cvx" id="{cid}-x{n}" style="top:{g * 60 + 1}px"></div>'
        for n, g in enumerate(gaps))
    css_l, html_l = _cv_card(cid, f"{cid}-CV", cv["title"], cv["sub"], cv_rows,
                             cw, cv.get("tag", "TU CV"), "", marks)
    css_r, html_r = _cv_card(cid, f"{cid}-OF", offer["title"], offer["sub"],
                             offer["rows"], cw, offer.get("tag", "LA VACANTE"),
                             "hot")
    kick = f'<div class="cokick" id="{cid}-kick">{esc(kicker)}</div>' if kicker else ""
    css = _cv_css(p) + css_l + css_r + f"""
{p} .cowrap{{display:flex;flex-direction:column;align-items:center;gap:20px;
  width:{BOARD_W}px}}
{p} .cokick{{font-family:{MONO};font-weight:700;font-size:23px;letter-spacing:.16em;
  text-transform:uppercase;color:{C['accent_hi']};opacity:0}}
{p} .copair{{display:flex;align-items:flex-start;gap:96px;width:100%;
  position:relative}}
{p} .covs{{position:absolute;left:50%;top:50%;margin-left:-32px;margin-top:-32px;
  width:64px;height:64px;border-radius:{RADIUS['pill']}px;background:{C['bg']};
  border:1px solid {TK.LINE_HI};display:flex;align-items:center;
  justify-content:center;font-family:{MONO};font-weight:700;font-size:20px;
  letter-spacing:.06em;color:{C['text3']};opacity:0;z-index:3}}
{p} .cvx{{position:absolute;left:-8px;right:-8px;height:44px;
  border:2px solid rgba(255,90,90,.55);border-radius:{RADIUS['sm']}px;
  background:{FILL['alert']};opacity:0;z-index:2;pointer-events:none}}"""
    html = (f'<div class="cowrap">{kick}'
            f'<div class="copair">{html_l}{html_r}'
            f'<div class="covs" id="{cid}-vs">VS</div></div></div>')
    anims = []
    if kicker:
        anims.append(("chip-in", f"#{cid}-kick", .08, .24))
    anims += [("rise-in", f"#{cid}-CV", at[0], .34),
              ("rise-in", f"#{cid}-OF", at[1], .34),
              ("chip-in", f"#{cid}-vs", at[1] + .18, .26)]
    for n in range(len(gaps)):
        anims.append(("box-in", f"#{cid}-x{n}", gap_at + n * .07, .32))
    return css, html, anims


def offer_stack(cid: str, offers: list[str], offer_at: list[float],
                common: list[str], common_at: list[float],
                missing: list[str], missing_at: float,
                kicker: str = "", common_label: str = "SE REPITEN",
                missing_label: str = "NO ESTÁN EN TU CV") -> tuple[str, str, list]:
    """Varias ofertas del mismo perfil, y lo que se repite en todas.

    Tres cosas pasan en este beat y el componente las separa en tres alturas:
    las OFERTAS entran («que compare varias ofertas del mismo perfil»), de ellas
    suben las competencias que aparecen SIEMPRE («detecte qué habilidades
    aparecen constantemente») y al final se dibuja lo que FALTA («y cuáles
    faltan en tu currículum»).

    Los que faltan van con borde discontinuo y sin relleno, no en rojo: es el
    idioma del hueco que ya usan `calendar` para la hora sin paciente y
    `tool_pair` para la marca sin nombrar. Un chip rojo diría «esta competencia
    tiene un problema»; un hueco dice «aquí no hay nada», que es la frase.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    cards = "".join(
        f'<div class="ofcard" id="{cid}-o{i}">'
        f'<span class="ofn">OFERTA {i+1:02d}</span>'
        f'<span class="oft">{esc(o)}</span>'
        f'<span class="ofbar"></span><span class="ofbar s"></span></div>'
        for i, o in enumerate(offers))
    chips_c = "".join(f'<span class="ofchip" id="{cid}-c{i}">{esc(c)}</span>'
                      for i, c in enumerate(common))
    chips_m = "".join(f'<span class="ofchip gap" id="{cid}-m{i}">{esc(c)}</span>'
                      for i, c in enumerate(missing))
    kick = f'<div class="ofkick" id="{cid}-kick">{esc(kicker)}</div>' if kicker else ""
    css = f"""
{p} .ofwrap{{display:flex;flex-direction:column;align-items:center;gap:18px;
  width:{BOARD_W}px}}
{p} .ofkick{{font-family:{MONO};font-weight:700;font-size:23px;letter-spacing:.16em;
  text-transform:uppercase;color:{C['accent_hi']};opacity:0}}
{p} .ofrow{{display:flex;gap:16px;width:100%}}
{p} .ofcard{{flex:1 1 0;background:{C['surface']};border:1px solid {TK.LINE};
  border-radius:{RADIUS['md']}px;padding:20px 20px 22px;display:flex;
  flex-direction:column;gap:11px;box-shadow:{TK.SHADOW};opacity:0}}
{p} .ofn{{font-family:{MONO};font-weight:700;font-size:17px;letter-spacing:.13em;
  color:{C['text3']}}}
{p} .oft{{font-family:{FONT};font-weight:800;font-size:25px;letter-spacing:-.015em;
  color:{C['text']};line-height:1.14;min-height:58px}}
{p} .ofbar{{height:9px;border-radius:{RADIUS['pill']}px;
  background:rgba(167,173,187,.30);width:100%;display:block}}
{p} .ofbar.s{{width:62%}}
{p} .ofblock{{width:100%;display:flex;flex-direction:column;gap:11px}}
{p} .oflab{{font-family:{MONO};font-weight:700;font-size:19px;letter-spacing:.13em;
  text-transform:uppercase;color:{C['text3']};opacity:0}}
{p} .oflab.go{{color:{C['accent_hi']}}}
{p} .ofchips{{display:flex;flex-wrap:wrap;gap:11px}}
{p} .ofchip{{font-family:{MONO};font-weight:700;font-size:24px;letter-spacing:.08em;
  text-transform:uppercase;color:{C['text']};background:{C['accent_pill']};
  border:1px solid {accent_a(.5)};border-radius:{RADIUS['pill']}px;
  padding:13px 24px;opacity:0}}
{p} .ofchip.gap{{background:transparent;border:2px dashed {C['text3']};
  color:{C['text3']}}}"""
    html = (f'<div class="ofwrap">{kick}'
            f'<div class="ofrow">{cards}</div>'
            f'<div class="ofblock">'
            f'<div class="oflab go" id="{cid}-lc">{esc(common_label)}</div>'
            f'<div class="ofchips">{chips_c}</div></div>'
            f'<div class="ofblock">'
            f'<div class="oflab" id="{cid}-lm">{esc(missing_label)}</div>'
            f'<div class="ofchips">{chips_m}</div></div></div>')
    anims = []
    if kicker:
        anims.append(("chip-in", f"#{cid}-kick", .06, .24))
    for i in range(len(offers)):
        anims.append(("rise-in", f"#{cid}-o{i}", offer_at[i], .30))
    anims.append(("slide-in", f"#{cid}-lc", common_at[0] - .12, .22))
    for i in range(len(common)):
        anims.append(("chip-in", f"#{cid}-c{i}", common_at[i], .28))
    anims.append(("slide-in", f"#{cid}-lm", missing_at - .12, .22))
    for i in range(len(missing)):
        # Los huecos entran juntos: el guion los enuncia como un resultado
        # único («y cuáles faltan»), no uno a uno.
        anims.append(("chip-in", f"#{cid}-m{i}", missing_at + i * .08, .28))
    return css, html, anims


def rewrite_line(cid: str, before: str, after: str, parts: list[dict],
                 type_at: float, strike_at: float, after_at: float,
                 kicker: str = "") -> tuple[str, str, list]:
    """La misma experiencia, escrita de las dos maneras.

    El paso 3 del guion no pide dos ejemplos: pide una TRANSFORMACIÓN («en
    lugar de "era responsable de", transforma cada experiencia en resultado,
    métrica e impacto»). Por eso la línea pobre se teclea primero, se TACHA en
    su sitio y la buena baja debajo — dos tarjetas sueltas lado a lado dirían
    «hay dos estilos», y la frase es que uno sustituye al otro.

    `parts` son los tres fragmentos que el guion nombra, cada uno con su
    etiqueta y su palabra. El realce va en un `inset` ABSOLUTO detrás del
    texto, el mismo mecanismo del karaoke (§5): así no le añade ancho a la
    línea y el texto no salta cuando se enciende.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    # La frase buena se parte en trozos: los que `parts` nombra llevan realce
    # propio, el resto es texto llano. Se busca por orden para que dos
    # fragmentos con el mismo texto no se pisen.
    html_after, cursor = "", 0
    for i, pt in enumerate(parts):
        j = after.find(pt["text"], cursor)
        if j < 0:
            raise ValueError(f"rewrite_line: «{pt['text']}» no está en «{after}»")
        html_after += esc(after[cursor:j])
        html_after += (f'<span class="rwf">{esc(pt["text"])}'
                       f'<span class="rwbg" id="{cid}-f{i}"></span></span>')
        cursor = j + len(pt["text"])
    html_after += esc(after[cursor:])
    tags = "".join(
        f'<span class="rwtag" id="{cid}-g{i}">{esc(pt["label"])}</span>'
        for i, pt in enumerate(parts))
    kick = f'<div class="rwkick" id="{cid}-kick">{esc(kicker)}</div>' if kicker else ""
    css = f"""
{p} .rwwrap{{display:flex;flex-direction:column;align-items:flex-start;gap:18px;
  width:{BOARD_W}px}}
{p} .rwkick{{font-family:{MONO};font-weight:700;font-size:23px;letter-spacing:.16em;
  text-transform:uppercase;color:{C['accent_hi']};opacity:0}}
{p} .rwcard{{width:100%;background:{C['surface']};border:1px solid {TK.LINE_HI};
  border-radius:{RADIUS['md']}px;box-shadow:{TK.SHADOW};padding:26px 28px;
  display:flex;flex-direction:column;gap:10px}}
{p} .rwlab{{font-family:{MONO};font-weight:700;font-size:18px;letter-spacing:.14em;
  text-transform:uppercase;color:{C['text3']}}}
{p} .rwbeforebox{{position:relative}}
{p} .rwbefore{{font-family:{FONT};font-weight:700;font-size:34px;
  line-height:1.2;letter-spacing:-.015em;color:{C['text3']}}}
{p} .rwstrike{{position:absolute;left:0;top:calc(50% - 2px);height:4px;width:0;
  background:{C['alert']};border-radius:2px;pointer-events:none}}
{p} .rwarrow{{align-self:center;font-family:{FONT};font-weight:700;font-size:34px;
  color:{C['accent']};line-height:1;opacity:0}}
{p} .rwafter{{font-family:{FONT};font-weight:900;font-size:36px;line-height:1.24;
  letter-spacing:-.02em;color:{C['text']};opacity:0}}
{p} .rwcard.good{{border-color:{accent_a(.42)}}}
{p} .rwf{{position:relative;display:inline-block;z-index:0}}
{p} .rwbg{{position:absolute;left:-8px;right:-8px;top:-3px;bottom:-3px;
  background:{C['accent_pill']};border-radius:{RADIUS['sm']}px;z-index:-1;opacity:0}}
{p} .rwtags{{display:flex;gap:12px;flex-wrap:wrap}}
{p} .rwtag{{font-family:{MONO};font-weight:700;font-size:21px;letter-spacing:.12em;
  text-transform:uppercase;color:{C['accent_hi']};border:1px solid {accent_a(.42)};
  background:{FILL['accent']};border-radius:{RADIUS['pill']}px;padding:11px 20px;
  opacity:0}}"""
    html = (f'<div class="rwwrap">{kick}'
            f'<div class="rwcard"><span class="rwlab">ANTES</span>'
            f'<div class="rwbeforebox">'
            f'<div class="rwbefore" id="{cid}-before" '
            f'data-layout-allow-occlusion></div>'
            f'<span class="rwstrike" id="{cid}-st"></span></div></div>'
            f'<div class="rwarrow" id="{cid}-arrow">↓</div>'
            f'<div class="rwcard good"><span class="rwlab">DESPUÉS</span>'
            f'<div class="rwafter" id="{cid}-after">{html_after}</div></div>'
            f'<div class="rwtags">{tags}</div></div>')
    # El tachado mide LO QUE MIDE EL TEXTO. `.rwbefore` es un bloque del ancho
    # de la tarjeta, así que un `width:100%` cruzaría también el vacío que
    # queda detrás de la última palabra y se leería como una raya suelta.
    strike_w = round(text_px(before, 34, 700))
    anims = [("type-word", f"#{cid}-before", type_at, .58, before),
             # El cursor se apaga cuando la línea queda terminada, o seguiría
             # parpateando debajo del tachado (la lección de `claude_prompt`).
             ("caret-off", f"#{cid}-before", strike_at - .05, .01, before),
             # El tachado NO borra la línea: la deja legible y marcada. Por eso
             # es una barra que crece sobre el texto y no un `badge-out`.
             ("grow-x", f"#{cid}-st", strike_at, .30, strike_w),
             ("chip-in", f"#{cid}-arrow", after_at - .14, .20),
             ("punch", f"#{cid}-after", after_at, .40)]
    if kicker:
        anims.insert(0, ("chip-in", f"#{cid}-kick", .06, .24))
    for i, pt in enumerate(parts):
        anims.append(("chip-in", f"#{cid}-f{i}", pt["at"], .26))
        anims.append(("chip-in", f"#{cid}-g{i}", pt["at"], .28))
    return css, html, anims


def interview_chat(cid: str, answer: str, followup: str, at: list[float],
                   badge: str = "RESPUESTA DÉBIL", role: str = "Hiring manager",
                   slug: str = "claude", kicker: str = "") -> tuple[str, str, list]:
    """La entrevista simulada: una respuesta floja y la repregunta.

    El paso 4 no es «haz que te pregunte», es «haz que REPREGUNTE cuando una
    respuesta sea débil» — y eso solo se ve si en el frame están las dos cosas:
    la respuesta y lo que viene después de ella. Una sola burbuja de pregunta
    no lo contaría.

    El orden de entrada es el del GUION, no el de la lógica: la repregunta entra
    en «repreguntando» y el sello de débil dos segundos después, en «débil».
    Visto así el frame plantea primero que la IA insiste, y solo al final dice
    por qué — que es como está escrita la frase.

    La marca va en la cabecera, igual que en `chat_unanswered`: es lo que ata el
    visual a su palabra y evita que parezca un chat genérico.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    logo_html, _ = logos.mark(slug, 30, uid=f"{cid}-head")
    kick = f'<div class="ivkick" id="{cid}-kick">{esc(kicker)}</div>' if kicker else ""
    css = f"""
{p} .ivwrap{{display:flex;flex-direction:column;align-items:center;gap:16px;
  width:{BOARD_W}px}}
{p} .ivkick{{font-family:{MONO};font-weight:700;font-size:23px;letter-spacing:.16em;
  text-transform:uppercase;color:{C['accent_hi']};opacity:0}}
{p} .ivpanel{{width:100%;background:{C['surface']};border:1px solid {TK.LINE_HI};
  border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW_LIFT};overflow:hidden;
  display:flex;flex-direction:column;opacity:0}}
{p} .ivhead{{display:flex;align-items:center;gap:14px;padding:20px 26px;
  border-bottom:1px solid {TK.LINE};background:{C['surface']}}}
{p} .ivmark{{width:40px;height:40px;border-radius:{RADIUS['sm']}px;
  background:{C['bg']};border:1px solid {TK.LINE_HI};display:flex;
  align-items:center;justify-content:center;overflow:hidden;flex:0 0 auto}}
{p} .ivrole{{font-family:{MONO};font-weight:700;font-size:20px;letter-spacing:.12em;
  text-transform:uppercase;color:{C['text2']}}}
{p} .ivbody{{padding:24px 26px 26px;display:flex;flex-direction:column;gap:16px}}
{p} .ivbub{{max-width:78%;border-radius:{RADIUS['md']}px;padding:20px 24px;
  font-family:{FONT};font-weight:700;font-size:31px;line-height:1.26;
  letter-spacing:-.015em;position:relative;opacity:0}}
{p} .ivbub.them{{align-self:flex-end;background:{C['surface2']};
  border:1px solid {TK.LINE_HI};color:{C['text2']}}}
{p} .ivbub.ia{{align-self:flex-start;background:{FILL['accent']};
  border:1px solid {accent_a(.48)};color:{C['text']}}}
{p} .ivbadge{{position:absolute;right:16px;bottom:-17px;font-family:{MONO};
  font-weight:700;font-size:18px;letter-spacing:.11em;text-transform:uppercase;
  color:{C['warn']};background:{C['bg']};border:1px solid rgba(255,184,77,.48);
  border-radius:{RADIUS['pill']}px;padding:8px 16px;opacity:0;white-space:nowrap}}"""
    html = (f'<div class="ivwrap">{kick}'
            f'<div class="ivpanel" id="{cid}-panel">'
            f'<div class="ivhead"><span class="ivmark">{logo_html}</span>'
            f'<span class="ivrole">{esc(role)}</span></div>'
            f'<div class="ivbody">'
            f'<div class="ivbub them" id="{cid}-ans">{esc(answer)}'
            f'<span class="ivbadge" id="{cid}-badge">{esc(badge)}</span></div>'
            f'<div class="ivbub ia" id="{cid}-fu">{esc(followup)}</div>'
            f'</div></div></div>')
    anims = [("rise-in", f"#{cid}-panel", .04, .34),
             ("chip-in", f"#{cid}-ans", at[0], .30),
             ("chip-in", f"#{cid}-fu", at[1], .32),
             ("stamp", f"#{cid}-badge", at[2], .34)]
    if kicker:
        anims.insert(0, ("chip-in", f"#{cid}-kick", .06, .24))
    return css, html, anims


# ── pieza 18 · el motion design descrito en lenguaje natural ─────────────────
def keyframe_grind(cid: str, at: list[float], total: int = 240,
                   tag: str = "SIN MOTION", clock: str = "6 H A MANO",
                   kicker: str = "") -> tuple[str, str, list]:
    """Un vídeo que no hace NADA y, debajo, el precio de que hiciera algo.

    El hook de la pieza dice «si no metías motion design porque animar todo a
    mano era demasiado trabajo». Son dos afirmaciones y el usuario eligió que
    se dibujaran las dos (P1): arriba el resultado —un plano plano, con los
    bloques de un vídeo sin una sola animación— y abajo el TRABAJO, que es lo
    que de verdad explica por qué el de arriba está muerto.

    El trabajo no se enuncia, se cuenta: los rombos caen **de uno en uno**
    sobre la pista y el contador sube con ellos. Un montón de keyframes ya
    puestos diría «hay muchos»; que aparezcan a este ritmo dice «esto lo pone
    alguien uno a uno», que es la frase. El reloj llega el último, en
    «demasiado trabajo», y es el único elemento que se SELLA (`stamp`): es la
    conclusión, no un dato más de la pista.

    ⚠ El escenario de arriba tiene que quedarse QUIETO. Es lo único de la
    pieza que no se anima por dentro a propósito, y por eso entra con un
    `rise-in` y ya no vuelve a recibir ningún tween: cualquier gesto ahí
    contradiría el rótulo que lleva pegado.

    `at` son cinco tiempos: el panel, el rótulo `tag`, el primer rombo, el
    último y el reloj.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    N = 14
    dias = "".join(f'<span class="kgdia" id="{cid}-k{i}" '
                   f'style="left:{round(4 + i * (92 / (N - 1)), 3)}%"></span>'
                   for i in range(N))
    kick = f'<div class="kgkick" id="{cid}-kick">{esc(kicker)}</div>' if kicker else ""
    css = f"""
{p} .kgwrap{{display:flex;flex-direction:column;align-items:center;gap:18px;
  width:{BOARD_W}px}}
{p} .kgkick{{font-family:{MONO};font-weight:700;font-size:23px;letter-spacing:.16em;
  text-transform:uppercase;color:{C['accent_hi']};opacity:0}}
{p} .kgstage{{position:relative;width:100%;height:296px;border-radius:{RADIUS['lg']}px;
  background:{C['surface']};border:1px solid {TK.LINE};box-shadow:{TK.SHADOW};
  overflow:hidden;opacity:0}}
{p} .kgscene{{position:absolute;inset:0;display:flex;flex-direction:column;
  align-items:flex-start;justify-content:center;gap:20px;padding:0 54px}}
{p} .kgbar{{height:26px;border-radius:{RADIUS['sm']}px;background:{C['surface3']}}}
{p} .kgbar.b1{{width:62%;height:44px}}
{p} .kgbar.b2{{width:44%}}
{p} .kgbar.b3{{width:30%;background:{C['surface2']}}}
{p} .kgtag{{position:absolute;left:34px;top:28px;font-family:{MONO};font-weight:700;
  font-size:21px;letter-spacing:.16em;color:{C['text3']};background:{C['bg']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['pill']}px;padding:9px 18px;
  opacity:0}}
{p} .kgtl{{position:relative;width:100%;height:150px;border-radius:{RADIUS['md']}px;
  background:{C['surface']};border:1px solid {TK.LINE};box-shadow:{TK.SHADOW};
  padding:20px 26px;display:flex;flex-direction:column;gap:18px;opacity:0}}
{p} .kghead{{display:flex;align-items:baseline;justify-content:space-between;
  font-family:{MONO};font-weight:700;font-size:22px;letter-spacing:.14em;
  text-transform:uppercase;color:{C['text3']}}}
{p} .kgnum{{font-family:{MONO};font-weight:700;font-size:30px;letter-spacing:.04em;
  color:{C['text']}}}
{p} .kgnum b{{color:{C['text3']};font-weight:700}}
{p} .kgtrack{{position:relative;height:42px;border-radius:{RADIUS['sm']}px;
  background:{C['bg']};border:1px solid {TK.LINE}}}
{p} .kgdia{{position:absolute;top:11px;width:18px;height:18px;
  background:{C['accent']};transform:rotate(45deg);border-radius:3px;opacity:0}}
{p} .kgclock{{font-family:{MONO};font-weight:700;font-size:26px;letter-spacing:.16em;
  color:{C['warn']};background:{FILL['warn']};border:1px solid rgba(255,184,77,.48);
  border-radius:{RADIUS['pill']}px;padding:12px 26px;opacity:0}}"""
    html = (f'<div class="kgwrap">{kick}'
            f'<div class="kgstage" id="{cid}-stage">'
            f'<div class="kgscene"><i class="kgbar b1"></i>'
            f'<i class="kgbar b2"></i><i class="kgbar b3"></i></div>'
            f'<span class="kgtag" id="{cid}-tag">{esc(tag)}</span></div>'
            f'<div class="kgtl" id="{cid}-tl">'
            f'<div class="kghead"><span>keyframes a mano</span>'
            f'<span class="kgnum"><i id="{cid}-count" style="font-style:normal">0</i>'
            f' <b>/ {total}</b></span></div>'
            f'<div class="kgtrack">{dias}</div></div>'
            f'<div class="kgclock" id="{cid}-clock">{esc(clock)}</div></div>')
    a_panel, a_tag, a_first, a_last, a_clock = at
    anims = [("rise-in", f"#{cid}-stage", a_panel, .38),
             ("chip-in", f"#{cid}-tl", a_panel + .14, .30),
             ("chip-in", f"#{cid}-tag", a_tag, .28)]
    if kicker:
        anims.append(("chip-in", f"#{cid}-kick", a_panel + .02, .24))
    span = max(.05, a_last - a_first)
    for i in range(N):
        anims.append(("chip-in", f"#{cid}-k{i}", a_first + span * i / (N - 1), .16))
    anims.append(("count-roll", f"#{cid}-count", a_first, span, 0, total, ""))
    anims.append(("stamp", f"#{cid}-clock", a_clock, .40))
    return css, html, anims


def agent_editor(cid: str, prompt: str, at: list[float],
                 layers: list[tuple[str, float]], elements: list[str],
                 out_label: str = "A TU VÍDEO",
                 kicker: str = "") -> tuple[str, str, list]:
    """Un editor de vídeo con un CHAT debajo, y lo que se escribe abajo
    aparece arriba.

    Lo pidió el usuario con esas palabras —«que se vea como un editor de vídeo
    y escribiendo bajo un chat, que todo sea animado»— y no había grabación
    que lo enseñara: la captura de la pieza es la WEB de HyperFrames, no su
    Studio. Así que es un MOCKUP declarado, con la tipografía y la paleta del
    sistema, igual que `claude_prompt` en la 16: lo que lo ata al producto es
    el orden de los gestos, no un redibujo de su interfaz.

    **El orden importa y sale del guion, no de la lógica de una app.** El
    guion enumera tres cosas —describir, trabajar con composiciones, generar
    elementos— y cada una tiene su gesto: el texto se teclea en «describir»,
    las pistas caen en «composiciones», y las piezas aparecen en el lienzo en
    «generar». Montar el editor ya lleno y limitarse a teclear debajo diría
    que el chat es un adorno.

    ⚠ El lienzo nace vacío pero **no en negro**. El primer montaje dejaba un
    rectángulo negro de 980x244 durante los cuatro segundos del tecleo, y en
    el frame de t=12 eso no se leía como «un lienzo esperando»: se leía como
    el panel roto que `knowledge-base` documenta con `reveal`. Lo que lo
    arregla es lo mismo que enseña un editor de verdad cuando no hay nada
    puesto — el ÁREA de trabajo dibujada: marco discontinuo, marcas de
    esquina, cruz de centro y la pastilla de resolución. Son CHROME, no
    contenido, así que están desde el primer frame sin adelantar nada del
    guion, y cuando las piezas entran encima queda claro sobre qué entran.

    ⚠ `type-word` deja su cursor DENTRO del innerHTML del destino (pieza 16),
    así que la línea termina con un `caret-off` en cuanto el beat pasa — si no,
    el campo sigue parpadeando durante los cinco segundos siguientes, que en
    una caja que ya envió su mensaje es un estado que la UI real no tiene.

    `at` son cuatro tiempos: el panel, el tecleo, la aparición de las piezas
    en el lienzo, y la entrega al vídeo.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    a_panel, a_type, a_el, a_out = at
    rows = "".join(
        f'<div class="aerow" id="{cid}-l{i}">'
        f'<span class="aelab">{esc(lab)}</span>'
        f'<span class="aeclip" style="width:{[68, 84, 52][i % 3]}%"></span></div>'
        for i, (lab, _t) in enumerate(layers))
    els = "".join(
        f'<span class="aeel e{i}" id="{cid}-e{i}">{esc(e)}</span>'
        for i, e in enumerate(elements))
    kick = f'<div class="aekick" id="{cid}-kick">{esc(kicker)}</div>' if kicker else ""
    css = f"""
{p} .aewrap{{display:flex;flex-direction:column;align-items:center;gap:16px;
  width:{BOARD_W}px}}
{p} .aekick{{font-family:{MONO};font-weight:700;font-size:23px;letter-spacing:.16em;
  text-transform:uppercase;color:{C['accent_hi']};opacity:0}}
{p} .aepanel{{width:100%;border-radius:{RADIUS['lg']}px;background:{C['surface']};
  border:1px solid {TK.LINE};box-shadow:{TK.SHADOW};padding:18px;
  display:flex;flex-direction:column;gap:16px;opacity:0}}
{p} .aecanvas{{position:relative;height:244px;border-radius:{RADIUS['md']}px;
  background:{C['bg']};border:1px solid {TK.LINE};overflow:hidden}}
{p} .aeguide{{position:absolute;left:28px;right:28px;top:20px;bottom:20px;
  border:2px dashed {ink_a(.13)};border-radius:{RADIUS['sm']}px}}
{p} .aetick{{position:absolute;width:26px;height:26px;border:2px solid {C['surface3']}}}
{p} .aetick.t0{{left:16px;top:12px;border-right:0;border-bottom:0}}
{p} .aetick.t1{{right:16px;top:12px;border-left:0;border-bottom:0}}
{p} .aetick.t2{{left:16px;bottom:12px;border-right:0;border-top:0}}
{p} .aetick.t3{{right:16px;bottom:12px;border-left:0;border-top:0}}
{p} .aecross{{position:absolute;left:50%;top:50%;width:34px;height:34px;
  margin:-17px 0 0 -17px}}
{p} .aecross:before,{p} .aecross:after{{content:"";position:absolute;
  background:{C['surface3']}}}
{p} .aecross:before{{left:0;top:16px;width:34px;height:2px}}
{p} .aecross:after{{left:16px;top:0;width:2px;height:34px}}
{p} .aeres{{position:absolute;left:22px;bottom:14px;font-family:{MONO};
  font-weight:700;font-size:17px;letter-spacing:.14em;color:{C['text3']}}}
{p} .aeel{{position:absolute;font-family:{FONT};font-weight:900;
  letter-spacing:-.03em;color:{C['text']};opacity:0;white-space:nowrap}}
{p} .aeel.e0{{left:44px;top:52px;font-size:62px}}
{p} .aeel.e1{{left:44px;top:132px;font-size:62px;color:{C['accent_hi']}}}
{p} .aeel.e2{{right:40px;top:44px;font-family:{MONO};font-weight:700;font-size:22px;
  letter-spacing:.14em;color:{C['text3']};background:{C['surface']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['pill']}px;padding:9px 18px}}
{p} .aetracks{{display:flex;flex-direction:column;gap:10px}}
{p} .aerow{{display:flex;align-items:center;gap:14px;opacity:0}}
{p} .aelab{{flex:0 0 150px;font-family:{MONO};font-weight:700;font-size:19px;
  letter-spacing:.12em;text-transform:uppercase;color:{C['text3']}}}
{p} .aeclip{{height:26px;border-radius:{RADIUS['sm']}px;
  background:linear-gradient(90deg,{C['accent']} 0%,{C['accent_pill']} 100%)}}
{p} .aechat{{width:100%;display:flex;align-items:center;gap:18px;
  background:{C['surface']};border:1px solid {TK.LINE_HI};
  border-radius:{RADIUS['pill']}px;padding:20px 26px;box-shadow:{TK.SHADOW_LIFT};
  opacity:0}}
{p} .aemark{{flex:0 0 auto;display:flex;align-items:center}}
{p} .aefield{{flex:1;min-width:0;font-family:{FONT};font-weight:700;font-size:34px;
  letter-spacing:-.01em;color:{C['text']};white-space:nowrap;overflow:hidden}}
{p} .aesend{{flex:0 0 auto;font-family:{MONO};font-weight:700;font-size:23px;
  letter-spacing:.12em;color:{C['text3']}}}
{p} .aeout{{font-family:{MONO};font-weight:700;font-size:24px;letter-spacing:.16em;
  color:{C['go']};background:{FILL['go']};border:1px solid rgba(52,227,155,.46);
  border-radius:{RADIUS['pill']}px;padding:11px 24px;opacity:0}}"""
    logo_html, _ = logos.mark("hyperframes", 40, uid=f"{cid}-ae")
    html = (f'<div class="aewrap">{kick}'
            f'<div class="aepanel" id="{cid}-panel">'
            f'<div class="aecanvas">'
            f'<span class="aeguide"></span>'
            f'<span class="aetick t0"></span><span class="aetick t1"></span>'
            f'<span class="aetick t2"></span><span class="aetick t3"></span>'
            f'<span class="aecross"></span>'
            f'<span class="aeres">1080 × 1920 · 30 FPS</span>'
            f'{els}</div>'
            f'<div class="aetracks">{rows}</div></div>'
            f'<div class="aechat" id="{cid}-chat">'
            f'<span class="aemark">{logo_html}</span>'
            f'<span class="aefield" id="{cid}-text"></span>'
            f'<span class="aesend" id="{cid}-send">↑</span></div>'
            f'<div class="aeout" id="{cid}-out">{esc(out_label)}</div></div>')
    anims = [("rise-in", f"#{cid}-panel", a_panel, .38),
             ("chip-in", f"#{cid}-chat", a_panel + .10, .30)]
    if kicker:
        anims.append(("chip-in", f"#{cid}-kick", a_panel + .02, .24))
    # El tecleo ocupa el beat de «describir la animación que quieres» entero y
    # se apaga en el instante en que entra la primera pista: a partir de ahí
    # el foco está arriba, y dos cosas parpadeando a la vez reparten la mirada.
    first_layer = min(t for _l, t in layers) if layers else a_el
    anims.append(("type-word", f"#{cid}-text", a_type,
                  max(.30, first_layer - a_type - .18), prompt))
    anims.append(("caret-off", f"#{cid}-text", first_layer - .12, .01, prompt))
    anims.append(("send-on", f"#{cid}-send", first_layer - .12, .26))
    for i, (_lab, t) in enumerate(layers):
        anims.append(("chip-in", f"#{cid}-l{i}", t, .28))
    for i in range(len(elements)):
        anims.append(("punch", f"#{cid}-e{i}", a_el + i * .16, .36))
    anims.append(("chip-in", f"#{cid}-out", a_out, .30))
    return css, html, anims


_DEMO_BARS = 26

_SPARK_SVG = (
    '<svg viewBox="0 0 48 48" aria-hidden="true" fill="none">'
    '<path d="M24 3 L28.4 18.2 L43.6 22.6 L28.4 27 L24 42.2 L19.6 27 '
    'L4.4 22.6 L19.6 18.2 Z" fill="currentColor"/>'
    '<circle cx="39.5" cy="8.5" r="3.4" fill="currentColor" opacity=".7"/>'
    '<circle cx="9" cy="36" r="2.4" fill="currentColor" opacity=".55"/>'
    '</svg>')


def motion_demo(cid: str, variant: str, label: str, at: list[float],
                words: list[str] | None = None, slots: list[str] | None = None,
                fill: str = "", fill_at: float | None = None
                ) -> tuple[str, str, list]:
    """Un ejemplo REAL de cada cosa que el guion enumera, no su etiqueta.

    El guion recita cuatro capacidades en seis segundos —«textos que entran,
    gráficos animados, captions, elementos que reaccionan al audio»— y el
    usuario pidió que cada una se viera hecha, no escrita (P3: se suceden con
    corte duro, cada una ocupando la banda entera). De ahí el reparto: son
    CUATRO visuales distintos del mismo componente, con su `start`/`end`
    pegados a la palabra, y no un panel que va cambiando por dentro.

    Cada variante tiene **1.0–2.8 s**, así que ninguna puede permitirse una
    entrada larga: todas arrancan su gesto en los primeros 120 ms y lo que se
    ve durante el resto del beat es el gesto, no el aterrizaje.

    · `text`     las palabras entran una a una — es la capacidad, literal.
    · `chart`    barras que crecen desde su base y una línea que se dibuja.
    · `captions` un bloque de subtítulo con el fondo de acento corriendo palabra
                 a palabra: el MISMO mecanismo del karaoke del triband (§5),
                 que es lo honesto — el ejemplo de captions de esta pieza son
                 sus propios captions.
    · `audio`    la onda, con las barras saltando en cascada rápida.
    · `recap`    las cuatro, quietas y pequeñas, más un hueco discontinuo que
                 NADA de lo anterior llena. El hueco es el idioma de la
                 ausencia que ya usan `calendar`, `tool_pair` y `step_grid`, y
                 aquí sostiene la frase «hay una parte que ninguna herramienta
                 arregla» hasta que la palabra «criterio» lo rellena.

    ⚠ Las barras NO animan `height`. Eso es reflow y el sistema solo mueve
    opacidad y transform (§6); crecen con `rise-bar`, que escala en Y desde el
    borde de abajo — un kind nuevo, porque `chip-in` escala desde el centro y
    una barra que crece desde su centro no se lee como una barra que crece.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    words = words or []
    slots = slots or []
    anims: list = []
    lab = (f'<div class="mdlab" id="{cid}-lab">{esc(label)}</div>'
           if label else "")
    body = ""

    if variant == "text":
        body = ('<div class="mdtext">'
                + "".join(f'<span class="mdw" id="{cid}-w{i}">{esc(w)}</span>'
                          for i, w in enumerate(words))
                + "</div>")
        # Cada palabra en la suya cuando el llamador las trae clavadas; si
        # solo pasa una, el escalonado de 200 ms hace de reparto.
        for i in range(len(words)):
            anims.append(("punch", f"#{cid}-w{i}",
                          at[i] if i < len(at) else at[0] + i * .20, .38))

    elif variant == "chart":
        n = 6
        vals = (38, 62, 47, 78, 91, 70)
        body = ('<div class="mdchart">'
                + "".join(f'<span class="mdbar" id="{cid}-b{i}" '
                          f'style="height:{vals[i]}%"></span>' for i in range(n))
                + f'<svg class="mdline" viewBox="0 0 600 240" '
                  f'preserveAspectRatio="none" aria-hidden="true">'
                  f'<path id="{cid}-path" d="M26 176 L142 118 L258 148 L374 78 '
                  f'L490 34 L574 72" fill="none" stroke="{C["go"]}" '
                  f'stroke-width="7" stroke-linecap="round" '
                  f'stroke-linejoin="round"/></svg></div>')
        for i in range(n):
            anims.append(("rise-bar", f"#{cid}-b{i}", at[0] + i * .07, .34))
        anims.append(("draw", f"#{cid}-path", at[0] + .30, .72))

    elif variant == "captions":
        body = ('<div class="mdcap">'
                + "".join(f'<span class="mdcw" id="{cid}-c{i}">'
                          f'<span class="mdcbg" id="{cid}-cb{i}"></span>'
                          f'{esc(w)}</span>' for i, w in enumerate(words))
                + "</div>")
        # El fondo de una palabra se apaga cuando arranca el de la siguiente,
        # así que nunca hay dos encendidos — la regla del karaoke del triband.
        step = .17
        for i in range(len(words)):
            t0 = at[0] + i * step
            anims.append(("chip-in", f"#{cid}-cb{i}", t0, .10))
            anims.append(("badge-out", f"#{cid}-cb{i}", t0 + step - .02, .07))

    elif variant == "audio":
        body = ('<div class="mdwave">'
                + "".join(f'<span class="mdwb" id="{cid}-a{i}" '
                          f'style="height:{18 + (i * 37 % 61) + (0 if i % 3 else 22)}%">'
                          f'</span>' for i in range(_DEMO_BARS))
                + "</div>")
        # Una cascada por cada tiempo que traiga `at`: la onda vuelve a
        # saltar en cada golpe, que es lo que significa «reacciona al audio».
        # Los .022 de paso por barra y los .34 de tween caben de sobra entre
        # dos golpes, así que dos tweens nunca se solapan sobre la misma
        # propiedad (lo que `hyperframes check` caza como
        # `overlapping_gsap_tweens`).
        # ⚠ Tres `fromTo` sobre la MISMA propiedad del mismo elemento dejan el
        # estado de reposo en manos de cuál se declaró el último (GSAP aplica
        # los valores `from` al AUTORARLOS, no en la posición del tween), y
        # eso lo caza `gsap_repeated_fromto_without_baseline`. Aquí los tres
        # arrancan del mismo sitio, así que el efecto sería inofensivo — pero
        # «inofensivo por casualidad» no es una base: se declara explícita en
        # t=0 y el reposo deja de depender del orden de autoría.
        for i in range(_DEMO_BARS):
            anims.append(("set-hidden", f"#{cid}-a{i}", 0.0, 0.0))
        for t0 in at:
            for i in range(_DEMO_BARS):
                anims.append(("rise-bar", f"#{cid}-a{i}", t0 + i * .022, .26))

    elif variant == "recap":
        cells = "".join(
            f'<span class="mdslot" id="{cid}-s{i}">{esc(s)}</span>'
            for i, s in enumerate(slots))
        hole = (f'<span class="mdhole" id="{cid}-hole"></span>'
                f'<span class="mdfill" id="{cid}-fill">{esc(fill)}</span>')
        body = f'<div class="mdrecap">{cells}<span class="mdgap">{hole}</span></div>'
        for i in range(len(slots)):
            anims.append(("chip-in", f"#{cid}-s{i}", at[0] + i * .10, .28))
        anims.append(("chip-in", f"#{cid}-hole", at[0] + len(slots) * .10, .28))
        if fill_at is not None:
            anims.append(("badge-out", f"#{cid}-hole", fill_at, .16))
            anims.append(("stamp", f"#{cid}-fill", fill_at, .42))
    else:
        raise ValueError(f"motion_demo: variante desconocida {variant!r}")

    # El rótulo entra EXACTAMENTE en at[0], no 60 ms antes: «nada entra antes
    # de su palabra» se mide en frames, y 60 ms son dos.
    if label:
        anims.insert(0, ("chip-in", f"#{cid}-lab", at[0], .22))

    css = f"""
{p} .mdwrap{{display:flex;flex-direction:column;align-items:center;gap:26px;
  width:{BOARD_W}px}}
{p} .mdlab{{font-family:{MONO};font-weight:700;font-size:23px;letter-spacing:.18em;
  text-transform:uppercase;color:{C['accent_hi']};opacity:0}}
{p} .mdtext{{display:flex;flex-direction:column;align-items:center;gap:6px}}
{p} .mdw{{font-family:{FONT};font-weight:900;font-size:104px;line-height:1.02;
  letter-spacing:-.04em;color:{C['text']};opacity:0}}
{p} .mdw:nth-child(2){{color:{C['accent_hi']}}}
{p} .mdchart{{position:relative;width:100%;height:300px;display:flex;
  align-items:flex-end;justify-content:space-between;gap:26px;
  padding:26px 30px;border-radius:{RADIUS['lg']}px;background:{C['surface']};
  border:1px solid {TK.LINE};box-shadow:{TK.SHADOW}}}
{p} .mdbar{{flex:1;border-radius:{RADIUS['sm']}px {RADIUS['sm']}px 0 0;
  background:linear-gradient(180deg,{C['accent']} 0%,{C['accent_pill']} 100%);
  transform-origin:50% 100%;opacity:0}}
{p} .mdline{{position:absolute;left:30px;right:30px;top:26px;bottom:26px;
  width:calc(100% - 60px);height:calc(100% - 52px)}}
{p} .mdcap{{display:flex;flex-wrap:wrap;justify-content:center;gap:12px 16px;
  max-width:920px}}
{p} .mdcw{{position:relative;font-family:{FONT};font-weight:900;font-size:74px;
  line-height:1.1;letter-spacing:-.03em;color:{C['text']}}}
{p} .mdcbg{{position:absolute;left:-8px;right:-8px;top:2px;bottom:6px;
  border-radius:{RADIUS['sm']}px;background:{C['accent_pill']};z-index:-1;opacity:0}}
{p} .mdwave{{width:100%;height:290px;display:flex;align-items:center;
  justify-content:space-between;gap:9px;padding:24px 30px;
  border-radius:{RADIUS['lg']}px;background:{C['surface']};border:1px solid {TK.LINE};
  box-shadow:{TK.SHADOW}}}
{p} .mdwb{{flex:1;border-radius:{RADIUS['pill']}px;transform-origin:50% 50%;
  background:linear-gradient(180deg,{C['accent_hi']} 0%,{C['accent_pill']} 100%);
  opacity:0}}
{p} .mdrecap{{display:flex;flex-wrap:wrap;justify-content:center;gap:16px;
  max-width:{BOARD_W}px}}
{p} .mdslot{{font-family:{MONO};font-weight:700;font-size:27px;letter-spacing:.12em;
  text-transform:uppercase;color:{C['text2']};background:{C['surface']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['pill']}px;padding:16px 28px;
  opacity:0}}
{p} .mdgap{{position:relative;display:inline-flex}}
{p} .mdhole{{display:inline-block;width:286px;height:66px;border-radius:{RADIUS['pill']}px;
  border:2px dashed {C['text3']};opacity:0}}
{p} .mdfill{{position:absolute;left:0;top:0;display:inline-flex;align-items:center;
  justify-content:center;width:286px;height:66px;border-radius:{RADIUS['pill']}px;
  background:{FILL['accent']};border:1px solid {accent_a(.55)};
  font-family:{MONO};font-weight:700;font-size:27px;letter-spacing:.12em;
  text-transform:uppercase;color:{C['accent_lt']};opacity:0}}"""
    return css, f'<div class="mdwrap">{lab}{body}</div>', anims


def idea_fate(cid: str, idea: str, exits: list[tuple[str, float]],
              at: list[float], revive: bool = False,
              badge: str = "") -> tuple[str, str, list]:
    """La idea que se descarta, y la MISMA idea cuando ya no hace falta.

    El guion cuenta un antes y un después con el mismo sujeto: «antes podías
    tener una buena idea y descartarla porque no sabías hacerla o porque
    externalizarla no compensaba… ahora puedes prototiparla». Dos tarjetas
    distintas dirían «hay dos ideas»; la misma tarjeta en dos estados dice lo
    que dice la frase, que es la rima visual de la pieza 12 aplicada a un
    estado en vez de a un componente.

    Las dos salidas cerradas **no van en rojo**: van apagadas y tachadas. Un
    chip rojo diría «esto tiene un problema» y lo que pasa es que esa puerta
    no estaba — es la misma distinción que `offer_stack` documenta entre el
    hueco discontinuo y la alerta.

    ⚠ Y las dos existen como HUECO desde que entra la tarjeta, aunque su texto
    llegue tres y cinco segundos después. Con las filas naciendo de la nada, el
    frame de t=23.5 era una tarjeta pequeña con media banda de suelo debajo —
    el usuario pidió explícitamente que nunca hubiera fondo vacío (§4), y un
    hueco discontinuo llena el sitio diciendo algo («aquí faltan dos cosas»)
    en vez de llenarlo por llenarlo. Es el mismo reparto que `step_grid`: la
    estructura entra entera, cada nombre espera su palabra.

    Con `revive` la tarjeta entra ya viva: en acento, con su glow y con la
    pastilla de estado. No se anima la transición de una a otra porque entre
    las dos hay un CORTE DURO — son dos visuales, y el corte es lo que deja
    ver que cambió, exactamente como `chat_unanswered` hace su contraste.

    ⚠ La tarjeta entra en DOS tiempos, como `tool_pair` y `step_grid`: el
    marco y el kicker en «antes podías tener», y el NOMBRE de la idea en
    «buena idea», 1.3 s después. Montarla entera al principio metería «una
    buena idea» en pantalla antes de que se diga, y dejar el hueco sin marco
    la leería como un panel roto — la estructura entra, el nombre espera.

    `at` son tres tiempos: el marco, el nombre y la pastilla de estado.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    # El hueco y su contenido son DOS capas apiladas, no un borde que muta: así
    # cada estado es un `set` propio y un seek no depende del anterior (la
    # lección de `tool_pair`).
    rows = "".join(
        f'<div class="ifxrow">'
        f'<span class="ifxhole" id="{cid}-h{i}"></span>'
        f'<div class="ifx" id="{cid}-x{i}"><span class="ifxmark">✕</span>'
        f'<span class="ifxlab">{esc(lab)}</span></div></div>'
        for i, (lab, _t) in enumerate(exits))
    tone = "alive" if revive else "dead"
    # ⚠ La pastilla de la instancia MUERTA no va en verde ni en rojo: va
    # apagada. Verde diría «resuelto» y rojo «esto falla»; lo que pasa es que
    # la idea se quedó fuera, que es el mismo matiz que `offer_stack` separa
    # entre el hueco discontinuo y la alerta.
    bad = (f'<span class="ifbadge{"" if revive else " off"}" '
           f'id="{cid}-badge">{esc(badge)}</span>' if badge else "")
    css = f"""
{p} .ifwrap{{display:flex;flex-direction:column;align-items:center;gap:24px;
  width:{BOARD_W}px}}
{p} .ifcard{{position:relative;width:100%;border-radius:{RADIUS['lg']}px;
  padding:38px 44px;display:flex;align-items:center;gap:30px;
  background:{C['surface']};border:1px solid {TK.LINE};box-shadow:{TK.SHADOW};opacity:0}}
{p} .ifcard.alive{{border-color:{accent_a(.55)};box-shadow:{TK.GLOW};
  background:linear-gradient(135deg,{C['accent_pill']} 0%,{C['surface']} 62%)}}
{p} .ifspark{{flex:0 0 auto;width:96px;height:96px;border-radius:{RADIUS['md']}px;
  display:flex;align-items:center;justify-content:center;
  background:{C['bg']};border:1px solid {TK.LINE_HI};color:{C['text3']}}}
{p} .ifcard.alive .ifspark{{color:{C['accent_hi']};
  border-color:{accent_a(.45)}}}
{p} .ifspark svg{{width:48px;height:48px;display:block}}
{p} .iftext{{display:flex;flex-direction:column;gap:10px;min-width:0}}
{p} .ifnamewrap{{position:relative;display:flex;align-items:center;min-height:62px}}
{p} .ifnamehole{{position:absolute;left:0;top:23px}}
{p} .ifkick{{font-family:{MONO};font-weight:700;font-size:21px;letter-spacing:.16em;
  text-transform:uppercase;color:{C['text3']}}}
{p} .ifcard.alive .ifkick{{color:{C['accent_lt']}}}
{p} .ifname{{font-family:{FONT};font-weight:900;font-size:60px;line-height:1.02;
  letter-spacing:-.03em;color:{C['text2']};opacity:0}}
{p} .ifnamehole{{display:block;height:16px;width:58%;border-radius:{RADIUS['pill']}px;
  border:2px dashed {C['text3']}}}
{p} .ifcard.alive .ifname{{color:{C['text']}}}
{p} .ifbadge{{position:absolute;right:34px;top:-18px;font-family:{MONO};
  font-weight:700;font-size:22px;letter-spacing:.14em;text-transform:uppercase;
  color:{C['go']};background:{C['bg']};border:1px solid rgba(52,227,155,.5);
  border-radius:{RADIUS['pill']}px;padding:10px 22px;opacity:0;white-space:nowrap}}
{p} .ifbadge.off{{color:{C['text3']};border-color:{TK.LINE_HI}}}
{p} .ifexits{{display:flex;flex-direction:column;gap:14px;width:100%}}
{p} .ifxrow{{position:relative;height:78px}}
{p} .ifxhole{{position:absolute;inset:0;border-radius:{RADIUS['md']}px;
  border:2px dashed {C['text3']};opacity:0}}
{p} .ifx{{position:absolute;inset:0;display:flex;align-items:center;gap:18px;
  padding:20px 26px;border-radius:{RADIUS['md']}px;background:{C['surface']};
  border:1px solid {TK.LINE};opacity:0}}
{p} .ifxmark{{flex:0 0 auto;font-family:{MONO};font-weight:700;font-size:28px;
  color:{C['text3']}}}
{p} .ifxlab{{font-family:{FONT};font-weight:700;font-size:36px;
  letter-spacing:-.01em;color:{C['text3']};text-decoration:line-through;
  text-decoration-thickness:3px}}"""
    html = (f'<div class="ifwrap">'
            f'<div class="ifcard {tone}" id="{cid}-card">{bad}'
            f'<span class="ifspark">{_SPARK_SVG}</span>'
            f'<span class="iftext"><span class="ifkick">'
            f'{"prototipo en marcha" if revive else "una buena idea"}</span>'
            f'<span class="ifnamewrap"><span class="ifnamehole" '
            f'id="{cid}-nhole"></span>'
            f'<span class="ifname" id="{cid}-name">{esc(idea)}</span>'
            f'</span></span></div>'
            + (f'<div class="ifexits">{rows}</div>' if exits else "")
            + "</div>")
    anims = [("rise-in", f"#{cid}-card", at[0], .38),
             ("badge-out", f"#{cid}-nhole", at[1], .14),
             ("punch", f"#{cid}-name", at[1], .40)]
    for i, (_lab, t) in enumerate(exits):
        anims.append(("chip-in", f"#{cid}-h{i}", at[0] + .10 + i * .09, .28))
        anims.append(("badge-out", f"#{cid}-h{i}", t, .16))
        anims.append(("chip-in", f"#{cid}-x{i}", t, .30))
    if badge:
        anims.append(("stamp", f"#{cid}-badge", at[2], .40))
    return css, html, anims


def idea_veneer(cid: str, idea: str, spectacle: str, at: list[float],
                kicker: str = "") -> tuple[str, str, list]:
    """La animación espectacular ENCIMA de la idea aburrida, y lo que queda
    cuando se apaga.

    Es la tesis de la pieza dibujada literal, y el usuario la eligió sabiendo
    que choca con la doctrina de «quietud antes del clímax» (P4): pidió que
    siempre hubiera algo en pantalla y esto lo cumple sin regalar el
    argumento, porque el argumento ES que lo de arriba se va.

    La mecánica tiene una sola regla y de ella depende todo: **la capa
    espectacular se apaga y la tarjeta gris NO cambia**. Si al apagarse la
    tarjeta hiciera cualquier cosa —encogerse, teñirse, sellar un rótulo— el
    frame diría «y entonces pasó algo»; lo que la frase dice es que no pasó
    nada, que sigue siendo la misma idea aburrida que había debajo. Así que la
    tarjeta entra una vez, se queda, y sobrevive al fundido de lo de encima.

    ⚠ La capa de encima va con `position:absolute` sobre la tarjeta, no al
    lado: «encima» es el literal de la frase. Eso son DOS avisos del linter y
    hay que responder a los dos por separado, porque miden cosas distintas:
    la tarjeta lleva `data-layout-allow-occlusion` (un panel opaco tapando su
    texto, la trampa que la pieza 12 documenta con `.stage-grain`) y la
    PALABRA lleva `data-layout-allow-overlap` (dos bloques de texto que se
    pisan, «ESPECTACULAR» sobre «Otro vídeo más»). El primero no cubre al
    segundo — el linter cazó el solape de texto con la oclusión ya declarada.
    Los pares de contraste que dejan de muestrearse se miden a mano con
    `tokens.contrast()` y se anotan en el plan.

    `at` son tres tiempos: la tarjeta gris, la entrada del espectáculo y su
    apagado.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    kick = f'<div class="ivekick" id="{cid}-kick">{esc(kicker)}</div>' if kicker else ""
    sparks = "".join(
        f'<span class="ivespark s{i}" id="{cid}-sp{i}"></span>' for i in range(7))
    css = f"""
{p} .ivewrap{{position:relative;display:flex;flex-direction:column;
  align-items:center;gap:22px;width:{BOARD_W}px}}
{p} .ivekick{{font-family:{MONO};font-weight:700;font-size:23px;letter-spacing:.16em;
  text-transform:uppercase;color:{C['text3']};opacity:0}}
{p} .iveslab{{position:relative;width:100%;height:352px;border-radius:{RADIUS['lg']}px;
  background:{C['surface']};border:1px solid {TK.LINE};box-shadow:{TK.SHADOW};
  padding:40px 46px;display:flex;flex-direction:column;justify-content:center;
  gap:20px;opacity:0;overflow:hidden}}
{p} .ivetag{{font-family:{MONO};font-weight:700;font-size:21px;letter-spacing:.16em;
  text-transform:uppercase;color:{C['text3']}}}
{p} .ivename{{font-family:{FONT};font-weight:900;font-size:64px;line-height:1.04;
  letter-spacing:-.03em;color:{C['text3']}}}
{p} .ivebar{{height:22px;border-radius:{RADIUS['sm']}px;background:{C['surface3']}}}
{p} .ivebar.w1{{width:54%}}
{p} .ivebar.w2{{width:36%}}
{p} .ivelayer{{position:absolute;left:0;top:0;right:0;bottom:0;
  border-radius:{RADIUS['lg']}px;display:flex;align-items:center;
  justify-content:center;overflow:hidden;opacity:0;
  background:linear-gradient(118deg,{C['accent_pill']} 0%,{mix(C['accent_pill'], C['bg'], .25)} 42%,
    {mix(C["accent"], C["bg"], .6)} 78%,{C['accent_pill']} 100%);
  box-shadow:{TK.GLOW}}}
{p} .iveword{{font-family:{FONT};font-weight:900;font-size:92px;line-height:1;
  letter-spacing:-.045em;color:{C['text']};text-align:center;
  text-shadow:0 10px 40px rgba(0,0,0,.45);opacity:0}}
{p} .ivespark{{position:absolute;width:14px;height:14px;border-radius:50%;
  background:{C['text']};opacity:0;box-shadow:0 0 22px {ink_a(.85)}}}
{p} .ivespark.s0{{left:9%;top:22%}}  {p} .ivespark.s1{{left:23%;top:74%}}
{p} .ivespark.s2{{left:41%;top:14%}} {p} .ivespark.s3{{left:58%;top:81%}}
{p} .ivespark.s4{{left:72%;top:28%}} {p} .ivespark.s5{{left:86%;top:64%}}
{p} .ivespark.s6{{left:50%;top:50%}}"""
    html = (f'<div class="ivewrap">{kick}'
            f'<div class="iveslab" id="{cid}-slab" data-layout-allow-occlusion>'
            f'<span class="ivetag">la idea</span>'
            f'<span class="ivename">{esc(idea)}</span>'
            f'<i class="ivebar w1"></i><i class="ivebar w2"></i>'
            f'<div class="ivelayer" id="{cid}-layer">{sparks}'
            f'<span class="iveword" id="{cid}-word" data-layout-allow-overlap>'
            f'{esc(spectacle)}</span>'
            f'</div></div></div>')
    a_slab, a_show, a_off = at
    anims = [("rise-in", f"#{cid}-slab", a_slab, .38),
             ("scale-pop", f"#{cid}-layer", a_show, .34),
             ("punch", f"#{cid}-word", a_show + .12, .42)]
    if kicker:
        anims.append(("chip-in", f"#{cid}-kick", a_slab + .04, .24))
    for i in range(7):
        anims.append(("stamp", f"#{cid}-sp{i}", a_show + .22 + i * .13, .22))
        anims.append(("badge-out", f"#{cid}-sp{i}", a_show + .52 + i * .13, .20))
    # El apagado: se va TODO lo de encima —capa, palabra y lo que quede de los
    # destellos— y la tarjeta gris no recibe ni un tween. Ese es el argumento.
    anims.append(("badge-out", f"#{cid}-word", a_off, .28))
    anims.append(("badge-out", f"#{cid}-layer", a_off + .06, .40))
    return css, html, anims


# ── pieza 19: la agencia de agentes ──────────────────────────────────────────
def agent_swarm(cid: str, variant: str, at: list[float],
                kicker: str = "", label: str = "",
                slug: str = "", tasks: list[tuple[str, str]] | None = None,
                team: list[tuple[str, str]] | None = None,
                total: int = 146, lit: int = 3) -> tuple[str, str, list]:
    """El mismo tablero de agentes en cuatro estados, a lo largo de la pieza.

    Es `idea_fate` de la pieza 18 llevado a una enumeración: **no son cuatro
    gráficos, es uno en cuatro momentos**, y el contraste se lee porque el
    corte duro entre dos instancias deja ver qué cambió. El guion de la pieza
    19 hace exactamente ese recorrido —muchos, uno solo, todos, tres— y
    dibujarlo con cuatro componentes distintos rompería la rima.

    · `fanout` — el repositorio, la marca que lo hospeda y la rejilla de
      especialistas llenándose. Es el hook: el titular del guion, hecho.
    · `solo`   — UN agente y todo lo que se le echa encima. El contraste que
      plantea «en vez de tener un único asistente haciendo de todo».
    · `roster` — los 146 encendidos, y la mayoría BAJANDO de intensidad en
      «no necesitas utilizar todos».
    · `team`   — tres, con su icono y la tarea que los convoca.

    ⚠ **Los 143 que se apagan son UN tween, no 143.** El selector de
    `fade-to` casa con todos los puntos a la vez; declararlos uno a uno metería
    en el contrato creativo un escalonado que no sale del transcript (la
    lección de «coreografía interna» de la pieza 12). Y **bajan de intensidad,
    no se apagan**: a opacidad 0 el frame diría que esos agentes dejaron de
    existir, y la frase dice que siguen ahí sin usarse — la misma distinción
    que `idea_fate` hace entre una salida apagada y una en rojo.

    ⚠ **Ningún icono es un emoji.** Todos salen de `icons.py` en
    `currentColor`, por lo que la pieza 18 pagó con su 💡 a 1.11:1 (§14).

    ⚠ **Las medidas del `roster` salen de que la banda `top` mide 660 px.** Con
    puntos de 52 y hueco de 12, los 146 ocupan 11 filas de 64 = 704 px y el
    CONTADOR quedaba empujado por encima de y0: sobre el frame se veía una
    rejilla sin cifra, o sea el dato que el beat necesita, fuera de cuadro. A
    40 px con hueco de 10 caben 18 por fila, 9 filas de 50 = 450, y con el
    contador (110) y su separación (26) el bloque suma 586 — dentro de los 640
    útiles. Y los 143 bajan a **0.26**, no a 0.18: por debajo de ahí el punto
    se confunde con la retícula del suelo y la frase pasa de «no los necesitas
    todos» a «solo hay tres».

    ⚠ **Los selectores que devuelve un mockup son RELATIVOS.** `build_visuals`
    les antepone `.viz[data-viz-id="…"]`, así que escribirlos ya prefijados los
    duplica y GSAP no encuentra el destino: `check` los reporta como
    `console_warning` con **0 errores**, y el gesto sencillamente no ocurre. Es
    la misma firma que el tachado de `rewrite_line` en la pieza 17 —«target
    #…-st not found» y la raya no se dibujaba nunca— y aquí costó los cuatro
    tweens del roster: los 146 puntos no entraban y los 143 no bajaban.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    css = f"""
{p} .aswrap{{width:{BOARD_W}px;display:flex;flex-direction:column;
  align-items:center;gap:26px}}
{p} .askick{{font-family:{MONO};font-weight:700;font-size:24px;letter-spacing:.20em;
  color:{C['accent_hi']};background:{FILL['accent']};border-radius:{RADIUS['pill']}px;
  padding:12px 26px;opacity:0}}
{p} .ashub{{width:132px;height:132px;border-radius:{RADIUS['lg']}px;
  background:{C['bg']};border:1px solid {TK.LINE_HI};display:flex;
  align-items:center;justify-content:center;box-shadow:{TK.SHADOW};opacity:0}}
{p} .ashublogo{{opacity:0;display:flex}}
{p} .asgridstack{{display:grid;width:704px}}
{p} .asgridstack > *{{grid-area:1/1}}
{p} .asslots{{display:flex;flex-wrap:wrap;gap:16px;justify-content:center;
  width:704px;opacity:0}}
{p} .asslot{{width:104px;height:104px;border-radius:{RADIUS['md']}px;
  border:2px dashed {C['text3']};display:block}}
{p} .asstem{{height:54px;width:100%;opacity:1}}
{p} .asstem svg{{width:100%;height:54px;overflow:visible}}
{p} .asgrid{{display:flex;flex-wrap:wrap;gap:16px;justify-content:center;
  width:704px}}
{p} .astile{{width:104px;height:104px;border-radius:{RADIUS['md']}px;
  background:{C['surface']};border:1px solid {TK.LINE};display:flex;
  align-items:center;justify-content:center;color:{C['text2']};
  box-shadow:{TK.SHADOW};opacity:0}}
{p} .astile.on{{border-color:{accent_a(.55)};background:{FILL['accent']};
  color:{C['accent_hi']}}}

{p} .assolo{{display:flex;flex-direction:column;align-items:center;gap:20px;
  width:100%}}
{p} .assolocard{{display:flex;align-items:center;gap:26px;background:{C['surface']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;padding:26px 40px;
  box-shadow:{TK.SHADOW};opacity:0;color:{C['text']}}}
{p} .assololbl{{font-family:{MONO};font-weight:700;font-size:24px;
  letter-spacing:.16em;color:{C['text3']}}}
{p} .assoloname{{font-family:{FONT};font-weight:900;font-size:50px;
  letter-spacing:-.03em;color:{C['text']};line-height:1.05}}
{p} .aspile{{display:flex;flex-direction:column;gap:12px;width:760px}}
{p} .aspilerow{{display:flex;align-items:center;gap:22px;background:{C['surface2']};
  border:1px solid {TK.LINE};border-radius:{RADIUS['md']}px;padding:18px 28px;
  font-family:{FONT};font-weight:700;font-size:34px;letter-spacing:-.02em;
  color:{C['text2']};opacity:0}}
{p} .aspilerow .ic{{color:{C['text3']};flex:0 0 auto}}
{p} .aspilebar{{flex:1 1 auto;height:16px;border-radius:8px;
  background:rgba(167,173,187,.30)}}

{p} .ascount{{display:flex;align-items:baseline;gap:16px;opacity:0}}
{p} .ascountn{{font-family:{FONT};font-weight:900;font-size:96px;line-height:.92;
  letter-spacing:-.045em;color:{C['text']}}}
{p} .ascountl{{font-family:{MONO};font-weight:700;font-size:24px;
  letter-spacing:.20em;color:{C['text3']}}}
{p} .asdots{{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;
  width:890px}}
{p} .asdot{{width:40px;height:40px;border-radius:8px;
  background:{C['surface2']};border:1px solid {TK.LINE};opacity:0}}
{p} .asdot.pick{{background:{FILL['accent2']};border-color:{accent_a(.6)}}}

{p} .asteam{{display:flex;gap:22px;justify-content:center;width:100%}}
{p} .asmember{{flex:1 1 0;display:flex;flex-direction:column;align-items:center;
  gap:16px;background:{C['surface']};border:1px solid {accent_a(.42)};
  border-radius:{RADIUS['lg']}px;padding:34px 18px;box-shadow:{TK.SHADOW};opacity:0}}
{p} .asmemberic{{width:96px;height:96px;border-radius:{RADIUS['md']}px;
  background:{FILL['accent']};display:flex;align-items:center;
  justify-content:center;color:{C['accent_hi']}}}
{p} .asmembern{{font-family:{FONT};font-weight:800;font-size:34px;
  letter-spacing:-.02em;color:{C['text']};text-align:center;line-height:1.1}}
{p} .aspill{{display:flex;align-items:center;gap:14px;background:{FILL['accent']};
  border:1px solid {accent_a(.42)};border-radius:{RADIUS['pill']}px;
  padding:14px 30px;font-family:{MONO};font-weight:700;font-size:24px;
  letter-spacing:.16em;color:{C['accent_hi']};opacity:0}}"""

    anims: list = []
    t = list(at) + [at[-1] if at else 0.4] * 8

    if variant == "fanout":
        logo_html, _r = logos.mark(slug, 76, uid=cid) if slug else ("", None)
        # Las bajantes se DIBUJAN (`draw`), no se funden: lo que se afirma es
        # que la marca alcanza a cada especialista, y un fundido solo diría
        # que las líneas existen (la lección de `layer_stack`, pieza 16).
        stem = ('<svg viewBox="0 0 980 54" preserveAspectRatio="none" '
                'fill="none" aria-hidden="true">'
                f'<path id="{cid}-s0" d="M490 0v22H150v32" stroke="{C["accent"]}" '
                'stroke-width="2.5" stroke-linecap="round"/>'
                f'<path id="{cid}-s1" d="M490 0v54" stroke="{C["accent"]}" '
                'stroke-width="2.5" stroke-linecap="round"/>'
                f'<path id="{cid}-s2" d="M490 0v22h340v32" stroke="{C["accent"]}" '
                'stroke-width="2.5" stroke-linecap="round"/></svg>')
        tiles = "".join(f'<div class="astile" id="{cid}-t{i}">'
                        f'{icons.icon("agent", 52)}</div>' for i in range(12))
        slots = "".join('<i class="asslot"></i>' for _ in range(12))
        html = (f'<div class="aswrap">'
                + (f'<div class="askick" id="{cid}-k">{esc(kicker)}</div>'
                   if kicker else "")
                + f'<div class="ashub" id="{cid}-hub">'
                f'<span class="ashublogo" id="{cid}-logo">{logo_html}</span></div>'
                + f'<div class="asstem">{stem}</div>'
                + f'<div class="asgridstack">'
                f'<div class="asslots" id="{cid}-slots">{slots}</div>'
                f'<div class="asgrid">{tiles}</div></div></div>')
        # ⚠ LA ESTRUCTURA ENTRA CON LA PRIMERA PALABRA, no con el primer dato.
        # Medido sobre el MP4 de la pieza 19 antes de esto: en t=0.5 la banda
        # `top` daba luma 27 —suelo liso— porque el visual estaba
        # declarado desde 0.000 pero su primer elemento no entraba hasta 0.955.
        # `check_band_top_covered` lo daba por bueno, y con razón: garantiza
        # COBERTURA DECLARADA, no luma renderizada (§4). Lo que el usuario pidió
        # es lo segundo.
        #
        # El marco del hub y los doce huecos discontinuos son CHROME —no nombran
        # nada que el guion no haya dicho— así que pueden estar desde el primer
        # frame sin adelantar el guion, igual que el área de trabajo dibujada de
        # `agent_editor` (pieza 18). Lo que espera su palabra es el CONTENIDO:
        # la marca dentro del marco y el agente dentro de cada hueco.
        #
        # Los huecos NO se funden al llenarse: la tarjeta es opaca y del mismo
        # tamaño, así que taparlos basta. Un `badge-out` sobre el grupo mientras
        # los doce entran escalonados dejaría los últimos aterrizando sobre nada.
        anims.append(("rise-in", f"#{cid}-hub", t[0], .40))
        anims.append(("chip-in", f"#{cid}-slots", t[0], .34))
        if kicker:
            anims.append(("chip-in", f"#{cid}-k", t[1], .30))
        anims.append(("stamp", f"#{cid}-logo", t[2], .40))
        for i in range(3):
            anims.append(("draw", f"#{cid}-s{i}", t[3] + i * .06, .34))
        # Los doce entran escalonados 62 ms DENTRO de la ventana de su frase
        # («una agencia llena de especialistas»), no uno por palabra: el guion
        # no nombra doce cosas, nombra una que está llena.
        for i in range(12):
            anims.append(("chip-in", f"#{cid}-t{i}", t[3] + .18 + i * .062, .26))

    elif variant == "solo":
        # ⚠ Las filas van SIN etiqueta, y eso es «nada entra antes de su
        # palabra» (§7) aplicado a un icono. Este beat cae en 7.8-10.5 s y las
        # cinco especialidades no se nombran hasta 13.7-18.4: rotular las filas
        # —o darle a cada una el icono de su especialidad— dejaría leer
        # «marketing» seis segundos antes de oírlo. Lo que el frame tiene que
        # decir aquí no es QUÉ trabajos son, es CUÁNTOS caen sobre uno solo, y
        # eso es volumen, no contenido — la misma respuesta que `spreadsheet`
        # (pieza 14) da con sus barras deterministas. `tx` vacío emite una
        # barra; con texto, la etiqueta. El ancho de cada barra viene dado y no
        # de un `random`, que rompería el golden.
        # La barra va a `text2` al 30 %: en `surface3` sobre `surface` se leía
        # como un hueco en el panel en vez de como contenido (pieza 17).
        rows = "".join(
            f'<div class="aspilerow" id="{cid}-p{i}">'
            f'{icons.icon(ic, 34)}'
            + (esc(tx) if tx else
               f'<span class="aspilebar" style="max-width:{62 + (i * 37) % 33}%">'
               '</span>')
            + '</div>'
            for i, (ic, tx) in enumerate(tasks or []))
        html = (f'<div class="aswrap"><div class="assolo">'
                f'<div class="assolocard" id="{cid}-solo">'
                f'{icons.icon("agent", 76)}'
                f'<div><div class="assololbl">{esc(kicker)}</div>'
                f'<div class="assoloname">{esc(label)}</div></div></div>'
                f'<div class="aspile">{rows}</div></div></div>')
        anims.append(("stamp", f"#{cid}-solo", t[0], .40))
        for i in range(len(tasks or [])):
            anims.append(("slide-in", f"#{cid}-p{i}", t[1 + i], .28))

    elif variant == "roster":
        # `pick` marca de antemano los tres que se quedarán encendidos: no
        # cambian de clase a media pieza, lo único que pasa es que el resto
        # baja. Repartidos por la rejilla con un paso primo para que no salgan
        # los tres seguidos ni dependan de un `random` (la regla del golden de
        # `spreadsheet`, pieza 14).
        picks = {(i * 37) % total for i in range(1, lit + 1)}
        dots = "".join(
            f'<div class="asdot{" pick" if i in picks else ""}" '
            f'id="{cid}-d{i}"></div>' for i in range(total))
        html = (f'<div class="aswrap">'
                f'<div class="ascount" id="{cid}-cnt">'
                f'<span class="ascountn" id="{cid}-cntn">0</span>'
                f'<span class="ascountl">{esc(label)}</span></div>'
                f'<div class="asdots">{dots}</div></div>')
        anims.append(("chip-in", f"#{cid}-cnt", t[0], .30))
        anims.append(("count-roll", f"#{cid}-cntn", t[0] + .06, .70,
                      0, total, ""))
        # Un solo tween para los 146: el selector casa con todos.
        anims.append(("chip-in", ".asdot", t[0] + .12, .34))
        anims.append(("fade-to", ".asdot:not(.pick)", t[1], .55, 0.26))

    elif variant == "team":
        cards = "".join(
            f'<div class="asmember" id="{cid}-m{i}">'
            f'<div class="asmemberic">{icons.icon(ic, 56)}</div>'
            f'<div class="asmembern">{esc(nm)}</div></div>'
            for i, (ic, nm) in enumerate(team or []))
        html = (f'<div class="aswrap"><div class="asteam">{cards}</div>'
                + (f'<div class="aspill" id="{cid}-pill">'
                   f'{icons.icon("strategy", 30)}{esc(label)}</div>'
                   if label else "")
                + "</div>")
        for i in range(len(team or [])):
            anims.append(("chip-in", f"#{cid}-m{i}", t[i], .32))
        if label:
            anims.append(("chip-in", f"#{cid}-pill", t[len(team or [])], .30))
    else:
        raise ValueError(f"agent_swarm: variante desconocida {variant!r}")

    return css, html, anims


def desktop_manager(cid: str, title: str, rows: list[tuple[str, str]],
                    at: list[float], installed: int = 1,
                    kicker: str = "") -> tuple[str, str, list]:
    """Una ventana de escritorio con su lista de agentes y su botón de instalar.

    Existe porque **la grabación no la tiene**: `2026-09-22 08-39-25.mov` es la
    WEB de Agency Agents y su sección de instalación es una línea de terminal
    (`cp -r agency-agents/* ~/.claude/agents/`), o sea justo lo contrario de lo
    que dice el beat. La regla de oro de §7 manda usar la grabación real
    *cuando existe*; para «una aplicación de escritorio» no existe. Mismo caso
    que `agent_editor` en la pieza 18.

    **Lo que la hace de ESCRITORIO y no un navegador es el semáforo y la
    ausencia de barra de direcciones.** Poner `browser_chrome` alrededor diría
    «esto es una web», que es la frase anterior del guion, no esta.

    ⚠ **La lista nace CON sus filas, y lo que entra es el botón.** Dibujar la
    ventana vacía durante los tres segundos previos la leería como un panel
    roto — la trampa que `knowledge-base` documenta con `reveal` y que
    `agent_editor` volvió a pagar con su lienzo negro. Las filas son CHROME (no
    nombran nada que el guion no haya dicho: son las especialidades ya
    enumeradas en 13.7–18.4 s); el estado —instalar, instalado— es lo que
    espera su palabra.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    dots = "".join(f'<i style="background:{c}"></i>'
                   for c in ("#FF5F57", "#FEBC2E", "#28C840"))
    body = []
    for i, (ic, name) in enumerate(rows):
        done = i < installed
        body.append(
            f'<div class="dmrow">'
            f'<span class="dmic">{icons.icon(ic, 40)}</span>'
            f'<span class="dmname">{esc(name)}</span>'
            f'<span class="dmbtn{" done" if done else ""}" id="{cid}-b{i}">'
            + (f'{icons.icon("check", 26)}INSTALADO' if done
               else f'{icons.icon("download", 26)}INSTALAR')
            + '</span></div>')
    css = f"""
{p} .dmwin{{width:{BOARD_W}px;background:{C['surface']};border:1px solid {TK.LINE_HI};
  border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW_LIFT};overflow:hidden}}
{p} .dmbar{{display:flex;align-items:center;gap:16px;padding:20px 26px;
  background:{C['surface2']};border-bottom:1px solid {TK.LINE}}}
{p} .dmdots{{display:flex;gap:10px}}
{p} .dmdots i{{width:16px;height:16px;border-radius:50%;display:block}}
{p} .dmtitle{{font-family:{FONT};font-weight:800;font-size:30px;
  letter-spacing:-.02em;color:{C['text']};margin-left:8px}}
{p} .dmkick{{margin-left:auto;font-family:{MONO};font-weight:700;font-size:20px;
  letter-spacing:.16em;color:{C['text3']}}}
{p} .dmlist{{display:flex;flex-direction:column}}
{p} .dmrow{{display:flex;align-items:center;gap:24px;padding:22px 30px;
  border-bottom:1px solid {TK.LINE}}}
{p} .dmrow:last-child{{border-bottom:none}}
{p} .dmic{{display:flex;color:{C['accent_hi']};flex:0 0 auto}}
{p} .dmname{{font-family:{FONT};font-weight:700;font-size:38px;
  letter-spacing:-.02em;color:{C['text']}}}
{p} .dmbtn{{margin-left:auto;display:flex;align-items:center;gap:12px;
  background:{FILL['accent']};border:1px solid {accent_a(.45)};
  border-radius:{RADIUS['pill']}px;padding:12px 26px;font-family:{MONO};
  font-weight:700;font-size:22px;letter-spacing:.14em;color:{C['accent_hi']};
  opacity:0;white-space:nowrap}}
{p} .dmbtn.done{{background:{FILL['go']};border-color:rgba(52,227,155,.42);
  color:{C['go']}}}"""
    html = (f'<div class="dmwin" id="{cid}-win">'
            f'<div class="dmbar"><span class="dmdots">{dots}</span>'
            f'<span class="dmtitle">{esc(title)}</span>'
            + (f'<span class="dmkick">{esc(kicker)}</span>' if kicker else "")
            + f'</div><div class="dmlist">{"".join(body)}</div></div>')
    # `rise-in` de .30 y no de .42: su rampa de opacidad dura duración×1.35, y
    # con .42 el panel tardaba medio segundo en ser visible — sumándose a los
    # 130 ms del relevo, el frame de entrada del beat se leía vacío.
    anims = [("rise-in", f"#{cid}-win", at[0] if at else .06, .30)]
    for i in range(len(rows)):
        anims.append(("chip-in", f"#{cid}-b{i}",
                      at[i + 1] if i + 1 < len(at) else .6 + i * .3, .28))
    return css, html, anims


def split_problem(cid: str, hire: str, problem: str,
                  specialists: list[tuple[str, str]], at: list[float],
                  kicker: str = "") -> tuple[str, str, list]:
    """La lectura fácil, tachada, y debajo el problema repartido entre tres.

    Es la tesis de la pieza 19 y son DOS afirmaciones encadenadas, no dos
    gráficos: «no es conseguir un empleado gratis» / «es dividir problemas
    complejos entre especialistas». Ponerlas como dos tarjetas sueltas diría
    «hay dos lecturas»; la frase dice que una SUSTITUYE a la otra, y eso se
    dibuja tachando la primera en su sitio — el mecanismo de `rewrite_line`
    (pieza 17), aquí sobre una idea en vez de sobre una línea de CV.

    ⚠ **El tachado es un trazo y se prepara en t=0** (§9, trampa 7): vive en el
    HTML desde el primer frame con ancho 0 y FUERA del texto, no se inyecta en
    el instante de dibujarse. El ancho es el del TEXTO medido con `text_px()`,
    no el de la tarjeta: `width:100%` cruzaría el vacío de detrás de la última
    palabra y se leería como una raya suelta.

    ⚠ **Las bajantes se dibujan con `draw`, no se funden.** Lo que se afirma es
    que el problema ALCANZA a cada especialista (la lección de `layer_stack`).

    ⚠ **El parámetro se llama `specialists` y no `parts` a propósito.** El
    remapeo de `absolute_times` en `build_visuals` trata `parts` como la lista
    de DICTS de `rewrite_line` (le resta el inicio a `pt["at"]`), así que una
    lista de tuplas con ese nombre revienta con un `TypeError` en la
    compilación. Dos componentes distintos no pueden compartir el nombre de un
    campo que el compilador interpreta.

    ⚠ **El nudo no se tiñe de rojo ni se apaga al repartirse.** Rojo diría «el
    problema falla»; apagarlo diría que desaparece. Lo que dice la frase es que
    se divide, y eso ya lo cuentan las tres bajantes.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    hire_w = round(text_px(hire, 46, 800))
    css = f"""
{p} .spwrap{{width:{BOARD_W}px;display:flex;flex-direction:column;
  align-items:center;gap:18px}}
{p} .sphireslot{{display:flex;align-items:center;justify-content:center;
  gap:18px;border:2px dashed {C['text3']};border-radius:{RADIUS['lg']}px;
  padding:24px 38px;color:{C['text3']};opacity:0}}
{p} .sphireslot span{{display:block;width:16px;height:16px;border-radius:50%;
  border:2px solid {C['text3']}}}
{p} .sphire{{position:relative;display:flex;align-items:center;gap:22px;
  background:{C['surface']};border:1px solid {TK.LINE};border-radius:{RADIUS['lg']}px;
  padding:22px 36px;box-shadow:{TK.SHADOW};opacity:0}}
{p} .sphirestack{{display:grid}}
{p} .sphirestack > *{{grid-area:1/1}}
{p} .sphireic{{display:flex;color:{C['text3']};flex:0 0 auto}}
{p} .sphiretx{{font-family:{FONT};font-weight:800;font-size:46px;
  letter-spacing:-.03em;color:{C['text2']};position:relative}}
{p} .spstrike{{position:absolute;left:0;top:52%;height:5px;width:0;
  border-radius:3px;background:{C['alert']};pointer-events:none}}
{p} .spknot{{display:flex;align-items:center;gap:24px;background:{C['surface2']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;padding:24px 40px;
  box-shadow:{TK.SHADOW};opacity:0}}
{p} .spknotic{{display:flex;color:{C['accent_hi']};flex:0 0 auto}}
{p} .spknottx{{font-family:{FONT};font-weight:900;font-size:46px;
  letter-spacing:-.03em;color:{C['text']}}}
{p} .spstem{{height:58px;width:100%}}
{p} .spstem svg{{width:100%;height:58px;overflow:visible}}
{p} .spparts{{display:flex;gap:20px;justify-content:center;width:100%}}
{p} .sppart{{flex:1 1 0;display:flex;flex-direction:column;align-items:center;
  gap:14px;background:{C['surface']};border:1px solid {accent_a(.42)};
  border-radius:{RADIUS['md']}px;padding:26px 14px;box-shadow:{TK.SHADOW};opacity:0}}
{p} .sppartic{{display:flex;color:{C['accent_hi']}}}
{p} .sppartn{{font-family:{MONO};font-weight:700;font-size:22px;
  letter-spacing:.14em;color:{C['text2']};text-align:center}}"""
    stem = ('<svg viewBox="0 0 980 58" preserveAspectRatio="none" fill="none" '
            'aria-hidden="true">'
            f'<path id="{cid}-e0" d="M490 0v24H163v34" stroke="{C["accent"]}" '
            'stroke-width="2.5" stroke-linecap="round"/>'
            f'<path id="{cid}-e1" d="M490 0v58" stroke="{C["accent"]}" '
            'stroke-width="2.5" stroke-linecap="round"/>'
            f'<path id="{cid}-e2" d="M490 0v24h327v34" stroke="{C["accent"]}" '
            'stroke-width="2.5" stroke-linecap="round"/></svg>')
    cards = "".join(
        f'<div class="sppart" id="{cid}-p{i}">'
        f'<span class="sppartic">{icons.icon(ic, 52)}</span>'
        f'<span class="sppartn">{esc(nm)}</span></div>'
        for i, (ic, nm) in enumerate(specialists))
    html = (f'<div class="spwrap">'
            + (f'<div class="askick" id="{cid}-k">{esc(kicker)}</div>'
               if kicker else "")
            + f'<div class="sphirestack">'
            f'<div class="sphireslot" id="{cid}-slot" data-layout-allow-overlap>'
            f'<span></span><span></span><span></span></div>'
            f'<div class="sphire" id="{cid}-hire" data-layout-allow-overlap>'
            f'<span class="sphireic">{icons.icon("people", 44)}</span>'
            f'<span class="sphiretx">{esc(hire)}'
            f'<span class="spstrike" id="{cid}-st"></span></span></div></div>'
            f'<div class="spknot" id="{cid}-knot">'
            f'<span class="spknotic">{icons.icon("knot", 52)}</span>'
            f'<span class="spknottx">{esc(problem)}</span></div>'
            f'<div class="spstem">{stem}</div>'
            f'<div class="spparts">{cards}</div></div>')
    anims = []
    if kicker:
        anims.append(("chip-in", f"#{cid}-k", at[0], .28))
    # El hueco de la lectura fácil se DIBUJA mientras espera su palabra, en vez
    # de dejar la banda con solo un kicker: es el mismo idioma que `calendar`
    # usa para la hora sin paciente y `tool_pair` para la marca que todavía no
    # se ha dicho. Aquí resuelve un choque concreto: el beat abre en 45.623
    # («Yo no lo vería») pero la tarjeta no puede decir «EMPLEADO GRATIS»
    # hasta 47.889, y las dos salidas malas eran dejar 2.3 s de banda casi
    # vacía o sostener el gestor de escritorio encima de la tesis.
    anims.append(("chip-in", f"#{cid}-slot", at[0], .30))
    anims.append(("badge-out", f"#{cid}-slot", at[1], .22))
    anims.append(("rise-in", f"#{cid}-hire", at[1], .40))
    anims.append(("grow-x", f"#{cid}-st", at[2], .34, hire_w))
    anims.append(("stamp", f"#{cid}-knot", at[3], .40))
    for i in range(3):
        anims.append(("draw", f"#{cid}-e{i}", at[4] + i * .05, .32))
    for i in range(len(specialists)):
        anims.append(("chip-in", f"#{cid}-p{i}", at[4] + .16 + i * .10, .30))
    return css, html, anims


# ── pieza 20: la cadena de producción de un vídeo faceless ───────────────────
def video_pipeline(cid: str, variant: str, at: list[float],
                   steps: list[tuple[str, str]] | None = None,
                   n: int = 7, tag: str = "", out_label: str = "",
                   gap_label: str = "", kicker: str = "") -> tuple[str, str, list]:
    """La misma cadena de producción en tres estados, a lo largo de la pieza.

    El guion de la 20 ES una cadena —tema → guion → material → narración →
    subtítulos → música → render— y la usa tres veces: para decir que hacerla a
    mano cuesta, para enseñar que la herramienta la automatiza entera, y para
    señalar la pieza que la herramienta NO pone. Dibujar eso con tres
    componentes distintos rompería la rima; es `agent_swarm` de la pieza 19
    aplicado a un flujo en vez de a un reparto.

    · `manual` — las siete etapas SIN NOMBRE, en gris, con un reloj pegado. Es
      el hook, y las siete palabras no se dicen hasta 11.2–21.0 s: rotularlas
      aquí sería leer «subtítulos» nueve segundos antes de oírlo (§7). Lo que
      el frame afirma no es QUÉ etapas son, es que son muchas y las pone
      alguien — volumen, no contenido, la respuesta de `spreadsheet`.
    · `auto`   — las MISMAS siete casillas, cada una llenándose con su icono y
      su nombre en su palabra.
    · `gap`    — la cadena entera encendida y, DELANTE, un hueco discontinuo
      que solo se rotula cuando el guion lo nombra.

    ⚠ **El nombre va a 15px y tracking .03em, medido, no elegido.** A 17px y
    .08em «SUBTÍTULOS» ocupa 116 px y la casilla de la variante `gap` mide 107
    —el hueco de delante le quita ancho a la fila—, así que desbordaba 4.5 px
    por cada lado. Lo cazó el linter de layout como `text_box_overflow`, con
    **0 errores y 0 avisos**: un `info` que es fácil pasar por alto y que en el
    frame se ve como una palabra saliéndose de su caja.

    ⚠ **La geometría no cambia entre variantes.** Es lo único que hace que el
    espectador lea «la misma cadena» y no «otro gráfico»: siete celdas de 130
    px con 12 de hueco suman los 980 de `BOARD_W` exactos, y el hueco de `gap`
    entra por delante encogiendo la fila, no desplazándola.

    ⚠ **La salida se DIBUJA desde el primer frame en las tres.** Es el vídeo
    que la cadena produce; sin él las etapas no van a ninguna parte y el frame
    se lee como una fila de botones. Lo que espera su palabra no es el marco
    sino su ETIQUETA, que es donde vive el contenido («VÍDEO FACELESS» no se
    dice hasta 4.2 s).

    CONTRATO DE TIEMPOS — `at` es, en este orden:

        [estructura, etiqueta_de_salida, celda_0, celda_1, …, extra]

    `estructura` monta los huecos, la bajante y el marco de salida; `extra` es
    el último y solo lo usan las variantes que lo necesitan (el NOMBRE del
    hueco en `gap`, el kicker en `manual`). Se eligió posicional y no por
    claves porque `absolute_times`, en `build_visuals`, solo sabe remapear
    listas con nombres conocidos — `at` es uno de ellos.
    """
    # ⚠ Sin esto, una variante mal escrita en el plan NO falla: cae al `else`
    # de más abajo y renderiza una cadena vacía, que es exactamente el modo de
    # fallo silencioso que este proyecto paga sobre el MP4. Lo encontró el test
    # del camino de FALLO, no la compilación.
    if variant not in ("manual", "auto", "gap"):
        raise ValueError(
            f"video_pipeline: variante desconocida {variant!r} — "
            "hay manual, auto y gap")
    p = f'.viz[data-viz-id="{cid}"]'
    steps = steps or []
    css = f"""
{p} .vpwrap{{width:{BOARD_W}px;display:flex;flex-direction:column;
  align-items:center;gap:22px}}
{p} .vpkick{{display:flex;align-items:center;gap:14px;font-family:{MONO};
  font-weight:700;font-size:23px;letter-spacing:.18em;color:{C['text3']};
  background:{C['bg']};border:1px solid {TK.LINE_HI};border-radius:{RADIUS['pill']}px;
  padding:10px 22px;opacity:0}}
{p} .vprow{{display:flex;align-items:stretch;gap:12px;width:100%}}
{p} .vpcell{{flex:1 1 0;min-width:0;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:10px;height:132px;
  border-radius:{RADIUS['md']}px;position:relative}}
{p} .vpslot{{border:2px dashed {C['text3']};opacity:0}}
{p} .vpstep{{background:{C['surface']};border:1px solid {accent_a(.42)};
  box-shadow:{TK.SHADOW};opacity:0}}
{p} .vpwork{{background:{C['surface2']};border:1px solid {TK.LINE};
  box-shadow:{TK.SHADOW};opacity:0}}
{p} .vpic{{display:flex;color:{C['accent_hi']}}}
{p} .vpwork .vpic{{color:{C['text3']}}}
{p} .vpname{{font-family:{MONO};font-weight:700;font-size:15px;letter-spacing:.03em;
  color:{C['text2']};text-align:center;line-height:1.1;padding:0 3px}}
{p} .vpstack{{display:grid;width:100%}}
{p} .vpstack > *{{grid-area:1/1}}
{p} .vpgap{{flex:0 0 132px;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:10px;height:132px;border-radius:{RADIUS['md']}px;
  border:2px dashed {C['text3']};color:{C['text3']};opacity:0}}
{p} .vpgapn{{font-family:{MONO};font-weight:700;font-size:15px;letter-spacing:.03em;
  opacity:0}}
{p} .vparrow{{width:2px;height:34px;background:{C['accent']};opacity:0}}
{p} .vpout{{display:flex;align-items:center;gap:22px;background:{C['surface']};
  border:1px solid {TK.LINE};border-radius:{RADIUS['lg']}px;padding:20px 34px;
  box-shadow:{TK.SHADOW};opacity:0}}
{p} .vpoutfr{{width:76px;height:132px;border-radius:{RADIUS['sm']}px;
  background:{C['bg']};border:1px solid {TK.LINE_HI};display:flex;
  align-items:center;justify-content:center;color:{C['accent_hi']}}}
{p} .vpoutstack{{display:grid;min-width:250px}}
{p} .vpoutstack > *{{grid-area:1/1;align-self:center}}
{p} .vpoutslot{{display:flex;flex-direction:column;gap:14px}}
{p} .vpoutslot i{{display:block;height:14px;border-radius:7px;
  border:2px dashed {C['text3']}}}
{p} .vpoutslot i:last-child{{width:58%}}
{p} .vpoutx{{display:flex;flex-direction:column;gap:8px;opacity:0}}
{p} .vpoutt{{font-family:{FONT};font-weight:900;font-size:40px;letter-spacing:-.03em;
  color:{C['text']};line-height:1}}
{p} .vpouts{{font-family:{MONO};font-weight:700;font-size:20px;letter-spacing:.14em;
  color:{C['text3']}}}"""

    anims: list = []
    t = list(at) + [at[-1] if at else .4] * 10

    # Las siete casillas: el hueco discontinuo va SIEMPRE puesto y lo que entra
    # encima es la casilla llena, opaca y del mismo tamaño. Taparlo basta — un
    # fundido del grupo mientras las siete entran escalonadas dejaría a las
    # últimas aterrizando sobre nada (la lección del hook de la pieza 19).
    slots = "".join(f'<div class="vpcell vpslot"></div>' for _ in range(n))
    if variant == "manual":
        cells = "".join(
            f'<div class="vpcell vpwork" id="{cid}-c{i}">'
            f'<span class="vpic">{icons.icon("stack", 40)}</span></div>'
            for i in range(n))
    else:
        cells = "".join(
            f'<div class="vpcell vpstep" id="{cid}-c{i}">'
            f'<span class="vpic">{icons.icon(ic, 40)}</span>'
            f'<span class="vpname">{esc(nm)}</span></div>'
            for i, (ic, nm) in enumerate(steps[:n]))

    gap_html = ""
    if variant == "gap":
        gap_html = (f'<div class="vpgap" id="{cid}-gap">'
                    f'{icons.icon("strategy", 40)}'
                    f'<span class="vpgapn" id="{cid}-gapn">{esc(gap_label)}</span>'
                    "</div>")

    html = (f'<div class="vpwrap">'
            + (f'<div class="vpkick" id="{cid}-k">'
               f'{icons.icon("clock", 28)}{esc(kicker)}</div>' if kicker else "")
            + f'<div class="vprow">{gap_html}'
            f'<div class="vpstack" style="flex:1 1 0">'
            f'<div class="vprow" id="{cid}-slots">{slots}</div>'
            f'<div class="vprow">{cells}</div></div></div>'
            f'<div class="vparrow" id="{cid}-arrow"></div>'
            f'<div class="vpout" id="{cid}-out">'
            f'<div class="vpoutfr">{icons.icon("film", 44)}</div>'
            f'<div class="vpoutstack">'
            f'<div class="vpoutslot" id="{cid}-outslot"><i></i><i></i></div>'
            f'<div class="vpoutx" id="{cid}-outx">'
            f'<span class="vpoutt">{esc(out_label or "VÍDEO")}</span>'
            f'<span class="vpouts">{esc(tag)}</span></div>'
            f'</div></div></div>')

    n_cells = n if variant == "manual" else min(n, len(steps))
    anims.append(("chip-in", f"#{cid}-slots", t[0], .32))
    anims.append(("chip-in", f"#{cid}-arrow", t[0] + .08, .24))
    anims.append(("chip-in", f"#{cid}-out", t[0] + .04, .30))
    # ⚠ La mitad derecha de la tarjeta de salida NO puede quedarse lisa mientras
    # el rótulo espera su palabra: medido sobre el frame de t=3.6, se leía como
    # un panel a medio hacer — la misma trampa que `knowledge-base` documenta
    # con `reveal` y que `agent_editor` pagó con su lienzo negro. El hueco se
    # DIBUJA (dos renglones discontinuos) y el texto lo tapa en su instante.
    anims.append(("badge-out", f"#{cid}-outslot", t[1], .20))
    anims.append(("slide-in", f"#{cid}-outx", t[1], .30))
    if variant == "gap":
        anims.append(("chip-in", f"#{cid}-gap", t[0], .30))
    for i in range(n_cells):
        anims.append(("chip-in", f"#{cid}-c{i}", t[2 + i], .28))
    extra = t[2 + n_cells] if len(at) > 2 + n_cells else t[-1]
    if variant == "gap":
        anims.append(("chip-in", f"#{cid}-gapn", extra, .30))
    if kicker:
        anims.append(("chip-in", f"#{cid}-k", extra, .30))
    return css, html, anims


def money_button(cid: str, label: str, at: list[float],
                 question: str = "", empty_label: str = "") -> tuple[str, str, list]:
    """El botón que se pulsa y no sale nada.

    El guion pregunta «¿significa esto que acabas de encontrar un botón para
    ganar dinero?» y contesta «No». El usuario eligió que la respuesta se
    diera en MECÁNICA y no en texto: el cursor pulsa, y en «No.» un corte duro
    deja la bandeja de salida vacía con su hueco discontinuo.

    ⚠ **La bandeja de salida está DIBUJADA desde el primer frame**, vacía y
    discontinua. Si apareciera con el «No», el frame diría «y entonces salió
    una bandeja»; lo que dice la frase es que la bandeja SIEMPRE estuvo vacía
    y pulsar no la llena. Es el idioma que `calendar` usa para la hora sin
    paciente, aquí sobre una expectativa.

    ⚠ **Nada se tiñe de rojo.** Rojo diría «el botón falla». El botón funciona
    perfectamente; lo que no existe es lo que se esperaba que saliera.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    css = f"""
{p} .mbwrap{{width:{BOARD_W}px;display:flex;flex-direction:column;
  align-items:center;gap:20px}}
{p} .mbq{{font-family:{FONT};font-weight:800;font-size:38px;letter-spacing:-.02em;
  color:{C['text2']};text-align:center;opacity:0}}
{p} .mbbtn{{position:relative;display:flex;align-items:center;justify-content:center;
  gap:20px;background:linear-gradient(180deg,{C['accent']} 0%,{C['accent_pill']} 100%);
  border:1px solid {accent_a(.55)};border-radius:{RADIUS['lg']}px;
  padding:30px 64px;box-shadow:{TK.GLOW};opacity:0}}
{p} .mbbtnt{{font-family:{FONT};font-weight:900;font-size:52px;letter-spacing:-.03em;
  color:{C['on_accent']};line-height:1}}
{p} .mbcur{{position:absolute;right:-26px;bottom:-34px;color:#FFFFFF;
  filter:drop-shadow(0 8px 12px rgba(0,0,0,.6));opacity:0}}
{p} .mbring{{position:absolute;right:-6px;bottom:-14px;width:64px;height:64px;
  border-radius:50%;border:5px solid {C['accent_hi']};opacity:0}}
{p} .mbarrow{{width:2px;height:30px;background:{C['text3']};opacity:0}}
{p} .mbtray{{width:520px;height:150px;border-radius:{RADIUS['lg']}px;
  border:2px dashed {C['text3']};display:flex;align-items:center;
  justify-content:center;opacity:0}}
{p} .mbempty{{font-family:{MONO};font-weight:700;font-size:24px;letter-spacing:.18em;
  color:{C['text3']};opacity:0}}"""
    html = (f'<div class="mbwrap">'
            + (f'<div class="mbq" id="{cid}-q">{esc(question)}</div>'
               if question else "")
            + f'<div class="mbbtn" id="{cid}-btn">'
            f'<span class="mbbtnt">{esc(label)}</span>'
            f'<span class="mbring" id="{cid}-ring"></span>'
            f'<span class="mbcur" id="{cid}-cur">{icons.icon("pointer", 58)}</span>'
            f'</div>'
            f'<div class="mbarrow" id="{cid}-arr"></div>'
            f'<div class="mbtray" id="{cid}-tray">'
            f'<span class="mbempty" id="{cid}-empty">{esc(empty_label)}</span>'
            f'</div></div>')
    anims = []
    if question:
        anims.append(("slide-in", f"#{cid}-q", at[0], .30))
    anims.append(("stamp", f"#{cid}-btn", at[1], .40))
    anims.append(("chip-in", f"#{cid}-arr", at[1] + .14, .22))
    anims.append(("chip-in", f"#{cid}-tray", at[1] + .20, .30))
    # El clic: el cursor llega, pulsa, y el anillo se abre. `overwrite:"auto"`
    # lo resuelve `emit_anim` para el kind `click`, que anima la MISMA escala.
    anims.append(("cursor-enter", f"#{cid}-cur", at[2], .34, 0, 0))
    anims.append(("click", f"#{cid}-btn", at[3], .42, f"#{cid}-ring"))
    if empty_label:
        anims.append(("chip-in", f"#{cid}-empty", at[4], .30))
    return css, html, anims


def video_output(cid: str, at: list[float], count: int = 4,
                 views: str = "0", kicker: str = "", seal: str = "",
                 inputs: list[tuple[str, str]] | None = None
                 ) -> tuple[str, str, list]:
    """La máquina ya montada, escupiendo vídeos que nadie ve.

    El beat es «solo has encontrado una forma más rápida de crear un vídeo que
    nadie quiere ver», y lo que lo vuelve incómodo no es que un vídeo fracase:
    es el RITMO. Los vídeos caen uno tras otro y cada uno aterriza con su
    contador de visualizaciones en cero — el mismo mecanismo que `keyframe_grind`
    usa para que el precio se cuente en vez de enunciarse.

    ⚠ **El cero no es un error, así que no va en rojo ni lleva ✕.** Va en
    `text3`, apagado, como una cifra cualquiera que resulta ser cero. Teñirlo
    diría «algo ha fallado» y lo que dice la frase es que funcionó
    perfectamente y no le importó a nadie. Misma lógica que las salidas
    apagadas de `idea_fate` (pieza 18).

    `inputs` son las dos fichas que ENTRAN a la máquina —el tema y el guion—,
    y existen porque el beat empieza cuatro segundos antes de que caiga el
    primer vídeo: sin ellas la banda pasaba ese tramo con una máquina sola en
    pantalla mientras la voz habla de lo que se le mete dentro. Su contenido va
    como una barra DISCONTINUA, no como texto: lo que las descalifica no es lo
    que dicen sino que da igual lo que digan.

    CONTRATO DE TIEMPOS — `at` es, en este orden:

        [entrada_0, entrada_1, …, máquina, tarjeta_0, …, sello]
    """
    p = f'.viz[data-viz-id="{cid}"]'
    css = f"""
{p} .vowrap{{width:{BOARD_W}px;display:flex;flex-direction:column;
  align-items:center;gap:20px}}
{p} .vokick{{display:flex;align-items:center;gap:14px;font-family:{MONO};
  font-weight:700;font-size:23px;letter-spacing:.16em;color:{C['accent_hi']};
  background:{FILL['accent']};border-radius:{RADIUS['pill']}px;padding:10px 24px;
  opacity:0}}
{p} .vomach{{width:100%;display:flex;align-items:center;justify-content:center;
  gap:16px;background:{C['surface']};border:1px solid {accent_a(.42)};
  border-radius:{RADIUS['md']}px;padding:18px 26px;box-shadow:{TK.SHADOW};opacity:0}}
{p} .vomachic{{display:flex;color:{C['accent_hi']}}}
{p} .vomacht{{font-family:{MONO};font-weight:700;font-size:22px;letter-spacing:.14em;
  color:{C['text2']}}}
{p} .vodot{{width:9px;height:9px;border-radius:50%;background:{C['accent']}}}
{p} .vorow{{display:flex;gap:18px;justify-content:center;width:100%}}
{p} .vocard{{flex:1 1 0;display:flex;flex-direction:column;align-items:center;
  gap:12px;opacity:0}}
{p} .vofr{{width:100%;height:188px;border-radius:{RADIUS['md']}px;
  background:{C['surface2']};border:1px solid {TK.LINE};display:flex;
  align-items:center;justify-content:center;color:{C['text3']};
  box-shadow:{TK.SHADOW}}}
{p} .voviews{{display:flex;align-items:center;gap:10px;font-family:{MONO};
  font-weight:700;font-size:26px;letter-spacing:.08em;color:{C['text3']}}}
{p} .voin{{display:flex;gap:18px;justify-content:center;width:640px}}
{p} .voincard{{flex:1 1 0;display:flex;align-items:center;gap:14px;
  background:{C['surface2']};border:1px solid {TK.LINE};border-radius:{RADIUS['md']}px;
  padding:16px 22px;opacity:0}}
{p} .voinic{{display:flex;color:{C['text3']};flex:0 0 auto}}
{p} .voinx{{display:flex;flex-direction:column;gap:8px;flex:1 1 auto;min-width:0}}
{p} .voinn{{font-family:{MONO};font-weight:700;font-size:19px;letter-spacing:.12em;
  color:{C['text2']}}}
{p} .voinbar{{height:12px;border-radius:6px;border:2px dashed {C['text3']}}}
{p} .voseal{{display:flex;align-items:center;gap:14px;background:{C['bg']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['pill']}px;padding:12px 26px;
  font-family:{MONO};font-weight:700;font-size:24px;letter-spacing:.16em;
  color:{C['text3']};opacity:0}}"""
    cards = "".join(
        f'<div class="vocard" id="{cid}-v{i}">'
        f'<div class="vofr">{icons.icon("film", 52)}</div>'
        f'<div class="voviews">{icons.icon("eye", 26)}{esc(views)}</div>'
        "</div>" for i in range(count))
    ins = "".join(
        f'<div class="voincard" id="{cid}-i{i}">'
        f'<span class="voinic">{icons.icon(ic, 30)}</span>'
        f'<span class="voinx"><span class="voinn">{esc(nm)}</span>'
        '<span class="voinbar"></span></span></div>'
        for i, (ic, nm) in enumerate(inputs or []))
    html = (f'<div class="vowrap">'
            + (f'<div class="vokick" id="{cid}-k">{esc(kicker)}</div>'
               if kicker else "")
            + (f'<div class="voin">{ins}</div>' if ins else "")
            + f'<div class="vomach" id="{cid}-m">'
            f'<span class="vomachic">{icons.icon("gear", 34)}</span>'
            f'<span class="vomacht">{esc("PRODUCCIÓN AUTOMÁTICA")}</span>'
            '<span class="vodot"></span><span class="vodot"></span>'
            '<span class="vodot"></span></div>'
            f'<div class="vorow">{cards}</div>'
            + (f'<div class="voseal" id="{cid}-s">'
               f'{icons.icon("eye", 28)}{esc(seal)}</div>' if seal else "")
            + "</div>")
    anims = []
    ni = len(inputs or [])
    for i in range(ni):
        anims.append(("slide-in", f"#{cid}-i{i}", at[i], .30))
    anims.append(("rise-in", f"#{cid}-m", at[ni], .34))
    if kicker:
        anims.append(("chip-in", f"#{cid}-k", at[ni], .28))
    for i in range(count):
        j = ni + 1 + i
        anims.append(("drop-in", f"#{cid}-v{i}",
                      at[j] if j < len(at) else at[-1] + i * .28, .30))
    if seal:
        anims.append(("stamp", f"#{cid}-s", at[-1], .40))
    return css, html, anims


def tradeoff_bars(cid: str, rows: list[dict], at: list[float],
                  kicker: str = "") -> tuple[str, str, list]:
    """Dos magnitudes y lo que le pasa a cada una: una se comprime, la otra no.

    «La ventaja está en comprimir la ejecución, no en saltarte la estrategia.»
    Son dos afirmaciones sobre dos cosas distintas, y un par de barras las dice
    sin una palabra de más: la de arriba se encoge, la de abajo se queda
    exactamente donde estaba.

    ⚠ **La barra que no cambia NO recibe ningún tween.** Es la lección de
    `idea_veneer` (pieza 18): si se encogiera un poco, o se tiñera, el frame
    diría «y a esta también le pasó algo». Lo que la frase afirma es que no le
    pasa nada, y eso se dibuja no animándola.

    ⚠ **La compresión anima un `width` en píxeles con `grow-x`**, no un
    porcentaje: el `to` es el ancho final medido, y el CSS declara el inicial.
    """
    p = f'.viz[data-viz-id="{cid}"]'
    css = f"""
{p} .tbwrap{{width:{BOARD_W}px;display:flex;flex-direction:column;gap:26px}}
{p} .tbstack{{display:grid}}
{p} .tbstack > *{{grid-area:1/1}}
{p} .tbrails,{p} .tbrows{{display:flex;flex-direction:column;gap:26px}}
{p} .tbrails{{opacity:0;justify-content:flex-end}}
{p} .tbrails .tbtrack{{border-style:dashed;border-color:{C['text3']};
  background:transparent}}
{p} .tbkick{{font-family:{MONO};font-weight:700;font-size:23px;letter-spacing:.18em;
  color:{C['text3']};align-self:center;opacity:0}}
{p} .tbrow{{display:flex;flex-direction:column;gap:12px;opacity:0}}
{p} .tbhead{{display:flex;align-items:center;gap:14px;font-family:{MONO};
  font-weight:700;font-size:24px;letter-spacing:.14em;color:{C['text2']}}}
{p} .tbhead .ic{{color:{C['accent_hi']}}}
{p} .tbtag{{margin-left:auto;font-family:{MONO};font-weight:700;font-size:21px;
  letter-spacing:.14em;opacity:0}}
{p} .tbtrack{{height:64px;border-radius:{RADIUS['md']}px;background:{C['surface']};
  border:1px solid {TK.LINE};position:relative;overflow:hidden}}
{p} .tbfill{{height:100%;border-radius:{RADIUS['md']}px}}
{p} .tbfill.hot{{background:linear-gradient(90deg,{C['accent_pill']},{C['accent']})}}
{p} .tbfill.keep{{background:{FILL['accent2']};
  border-right:3px solid {C['accent_hi']}}}"""
    # CONTRATO DE TIEMPOS: at = [estructura, fila_0, fila_1, …, encoger, tag_0, …]
    # La estructura —los dos raíles vacíos— entra la primera y sin nombre: el
    # beat abre 1.7 s antes de que se diga «ejecución» y cinco antes de
    # «estrategia», y rotular los raíles ahí sería leer la tesis antes de
    # oírla. Es el mecanismo de `step_grid` (pieza 17).
    filas = []
    anims = [("chip-in", f"#{cid}-rails", at[0], .32)]
    base = 1
    for i, r in enumerate(rows):
        tag = (f'<span class="tbtag" id="{cid}-t{i}" '
               f'style="color:{C["go"] if r.get("shrink") else C["accent_hi"]}">'
               f'{esc(r.get("tag", ""))}</span>') if r.get("tag") else ""
        cls = "hot" if r.get("shrink") else "keep"
        filas.append(
            f'<div class="tbrow" id="{cid}-r{i}">'
            f'<div class="tbhead"><span class="ic">{icons.icon(r["icon"], 32)}</span>'
            f'{esc(r["name"])}{tag}</div>'
            f'<div class="tbtrack"><div class="tbfill {cls}" id="{cid}-f{i}" '
            f'style="width:{r["from"]}px"></div></div></div>')
        anims.append(("chip-in", f"#{cid}-r{i}", at[base + i], .32))
        if r.get("shrink"):
            # La única que se mueve. `grow-x` anima el `width` en px: el CSS
            # declara el inicial y el tween lleva al medido.
            anims.append(("grow-x", f"#{cid}-f{i}",
                          at[base + len(rows)], .60, r["to"]))
        if r.get("tag"):
            j = base + len(rows) + 1 + i
            anims.append(("chip-in", f"#{cid}-t{i}",
                          at[j] if len(at) > j else at[-1], .28))
    railes = "".join('<div class="tbtrack"></div>' for _ in rows)
    html = (f'<div class="tbwrap">'
            + (f'<div class="tbkick" id="{cid}-k">{esc(kicker)}</div>'
               if kicker else "")
            + f'<div class="tbstack">'
            f'<div class="tbrails" id="{cid}-rails">{railes}</div>'
            f'<div class="tbrows">{"".join(filas)}</div></div></div>')
    if kicker:
        anims.append(("chip-in", f"#{cid}-k", at[0], .28))
    return css, html, anims
