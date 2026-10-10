#!/usr/bin/env python3
"""Sistema de diseño — las dos paletas de la marca (claro / oscuro).

Única fuente de verdad del look. Lo importan `mockups.py`, `objects.py`,
`logos.py` y `build-composition.py`, así que un cambio aquí se propaga a toda
la pieza.

La intención: **contenido educativo premium de tecnología e IA** con la marca
del proyecto — crema + terracota, tipografía grotesca pesada (Inter 900) y un
único momento de acento por frame. Cada pieza elige su paleta (`"palette"` en
el plan): `claro` (suelo crema, tinta casi negra) u `oscuro` (suelo casi negro
cálido, texto crema). Los valores BASE salen del dashboard del proyecto
(Marketing/dashboard/web/src/app/theme.css); todo lo demás se DERIVA con una
regla y se MIDE en `tests/test_paletas.py`.

Nada de blanco ni negro puro como fondo.

⚠ Los escalares de color (`LINE`, `LINE_HI`, `SHADOW`, `SHADOW_LIFT`, `GLOW`)
cambian con `use()`: se leen como `tokens.LINE`, nunca con
`from tokens import LINE` (quedarían congelados en la paleta de arranque).
Los diccionarios (`C`, `FILL`, `THEME`, `INK_ON_FILL`) se mutan en su lugar,
así que importarlos por nombre sí es seguro.
"""

# ── color ─────────────────────────────────────────────────────────────────────
# Las dos paletas de la marca. Valores BASE copiados de
# Marketing/dashboard/web/src/app/theme.css; no se inventan aquí.
PALETTES_BASE = {
    "claro": {
        "bg": "#ECE7DE", "surface": "#F7F4EE", "surface2": "#E4DED2",
        "text": "#1C1A16", "text2": "#6F695F", "line": "#D8D1C4",
        "accent": "#C45F38", "accent_soft": "#F1DDD2", "on_accent": "#FFFFFF",
        "go": "#3F7D4E", "warn": "#A66A12", "alert": "#B23A2E",
    },
    "oscuro": {
        "bg": "#161412", "surface": "#201D1A", "surface2": "#2B2723",
        "text": "#EEE8DF", "text2": "#A39C91", "line": "#36312B",
        "accent": "#E27B52", "accent_soft": "#3A2419", "on_accent": "#1A0F0A",
        "go": "#7CC08C", "warn": "#E0A64A", "alert": "#EC7B6E",
    },
}
PALETTES = tuple(sorted(PALETTES_BASE))

# Marcas de terceros (logos), tonos reales: no dependen de la paleta.
BRANDS = {"excel": "#21A366", "whatsapp": "#25D366"}

# ── elevación ─────────────────────────────────────────────────────────────────
# Sombras por paleta. La clara es la del dashboard (--shadow); la oscura, la de
# siempre del editor: sobre fondo oscuro una sombra suave no se ve, así que la
# elevación la dan la sombra (que asienta) y el hairline (que separa).
_ELEVATION = {
    "claro": {"shadow": "0 1px 2px rgba(28,26,22,.06), 0 8px 24px rgba(28,26,22,.08)",
              "shadow_lift": "0 2px 4px rgba(28,26,22,.08), 0 16px 48px rgba(28,26,22,.12)"},
    "oscuro": {"shadow": "0 2px 6px rgba(0,0,0,.45), 0 18px 50px rgba(0,0,0,.55)",
               "shadow_lift": "0 8px 20px rgba(0,0,0,.55), 0 40px 90px rgba(0,0,0,.65)"},
}


def _rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a: str, b: str, t: float) -> str:
    """`a` mezclado hacia `b` en proporción `t` (0 = a, 1 = b)."""
    return "#%02X%02X%02X" % tuple(round(x + (y - x) * t) for x, y in zip(_rgb(a), _rgb(b)))


def rgba(h: str, a: float) -> str:
    r, g, b = _rgb(h)
    return f"rgba({r},{g},{b},{('%g' % a).lstrip('0') or '0'})"


def _until(color: str, toward: str, against: str, ratio: float) -> str:
    """El primer paso de `color` hacia `toward` (de 5 en 5 %) que llega a
    `ratio` contra `against`. Falla si ni el extremo llega: mejor romper aquí
    que renderizar texto ilegible."""
    for i in range(21):
        c = mix(color, toward, i / 20)
        if contrast(c, against) >= ratio:
            return c
    raise ValueError(f"{color}→{toward} no llega a {ratio}:1 contra {against}")


def _dimmest(color: str, toward: str, against: str, ratio: float) -> str:
    """El paso MÁS tenue de `color` hacia `toward` que todavía llega a `ratio`."""
    best = color
    for i in range(21):
        c = mix(color, toward, i / 20)
        if contrast(c, against) < ratio:
            break
        best = c
    return best


def _derive(name: str) -> dict:
    b = PALETTES_BASE[name]
    dark = luminance(b["bg"]) < 0.2
    c = dict(b)
    c.update(BRANDS)
    c["bg2"] = mix(b["bg"], b["surface"], .5)                       # centro del viñeteado
    c["bg_edge"] = mix(b["bg"], "#000000", .30 if dark else .06)    # borde del viñeteado
    c["surface3"] = mix(b["surface2"], b["text"], .06)              # bordes internos de UI
    c["text3"] = _dimmest(b["text2"], b["surface"], b["surface"], 4.5)
    # El acento como TEXTO sobre el suelo, y bajo el foco del stage (que aclara
    # el suelo hasta SPOTLIGHT_MAX): se exige contra el peor de los dos.
    c["accent_hi"] = _until(b["accent"], b["text"], lift(b["bg"], SPOTLIGHT_MAX), 4.5)
    c["accent_lt"] = _until(b["accent"], b["text"], b["bg"], 7.0)   # texto que va a FUNDIR
    # Fondo para una palabra de color `text` encima (pastilla del karaoke,
    # rótulos): el acento empujado hacia el suelo hasta que `text` se lea.
    c["accent_pill"] = _until(b["accent"], b["bg"], b["text"], 4.5)
    return c


C: dict = {}
FILL: dict = {}
THEME: dict = {}
INK_ON_FILL: dict = {}
PALETTE = ""
LINE = LINE_HI = SHADOW = SHADOW_LIFT = GLOW = ""

RADIUS = {"sm": 10, "md": 16, "lg": 24, "xl": 32, "pill": 9999}

# ── tipografía ────────────────────────────────────────────────────────────────
# Dos familias. Inter para todo el texto, JetBrains Mono para etiquetas de UI y
# datos. Una tercera familia es lo que hace que una pieza parezca un collage.
FONT = "'Inter', system-ui, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, monospace"

# Escala en px por formato. El REEL sube ~15 % porque se ve en un teléfono a
# distancia de brazo y compite con la interfaz de la app.
TYPE = {
    "REEL": {
        "chip": 26, "label": 24, "body": 34, "card_title": 52,
        "headline": 96, "display": 132, "hero_num": 200, "caption": 66,
    },
    "YOUTUBE": {
        "chip": 22, "label": 20, "body": 29, "card_title": 44,
        "headline": 80, "display": 112, "hero_num": 168, "caption": 54,
    },
}

# Tracking: cuanto más grande el texto, más se cierra. Es lo que hace que un
# titular pesado se lea como un producto y no como un cartel.
TRACK = {"chip": ".16em", "label": ".12em", "body": "0",
         "card_title": "-.02em", "headline": "-.032em",
         "display": "-.038em", "hero_num": "-.04em", "caption": "-.02em"}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def luminance(h: str) -> float:
    h = h.lstrip("#")
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a: str, b: str) -> float:
    """Ratio WCAG entre dos hex. Para comprobar un mockup nuevo ANTES de
    renderizar, que es cuando cuesta barato."""
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


def vignette(w: str = "120% 90%") -> str:
    """Fondo base. El viñeteado es sutil y su función es empujar la mirada al
    centro, no decorar: sin él un 1080×1920 de color plano se ve muerto."""
    return (f"radial-gradient({w} at 50% 42%, {C['bg2']} 0%, "
            f"{C['bg']} 62%, {C['bg_edge']} 100%)")


def grid(size: int = 72, alpha: float = .022) -> str:
    """Rejilla técnica casi invisible. Le da al fondo una textura de producto
    —de plano, de blueprint— en vez de un degradado liso de plantilla."""
    a = ink_a(alpha)
    return (f"repeating-linear-gradient(0deg,{a} 0 1px,transparent 1px {size}px),"
            f"repeating-linear-gradient(90deg,{a} 0 1px,transparent 1px {size}px)")


# ── el Motion Stage ───────────────────────────────────────────────────────────
def lift(hex_bg: str, alpha: float) -> str:
    """El color que resulta de poner blanco a `alpha` encima de `hex_bg`.

    Sirve para MEDIR el contraste dentro de un stage iluminado antes de
    renderizar, que es cuando cuesta barato.
    """
    b = hex_bg.lstrip("#")
    rgb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(round(c * (1 - alpha) + 255 * alpha) for c in rgb)


# Techo del foco cenital. `accent_hi` se deriva para aguantar 4.5:1 sobre el
# suelo iluminado HASTA este alfa (ver `_derive` y tests/test_paletas.py).
SPOTLIGHT_MAX = 0.05


def spotlight(alpha: float = SPOTLIGHT_MAX) -> str:
    """Foco cenital centrado. Empuja la mirada arriba, donde vive el objeto."""
    if alpha > SPOTLIGHT_MAX:
        raise ValueError(
            f"spotlight alpha {alpha} pasa del techo medido {SPOTLIGHT_MAX}: por "
            f"encima, el acento como texto (accent_hi) cae por debajo de AA sobre el fondo "
            f"iluminado")
    return (f"radial-gradient(120% 62% at 50% 0%, rgba(255,255,255,{alpha}) 0%, "
            f"rgba(255,255,255,0) 58%)")


def grain(seed: int = 7, opacity: float = 0.035) -> str:
    """Grano como data-URI SVG con SEMILLA FIJA y filtro ESTÁTICO.

    Es la única forma determinista: `Math.random` sin semilla está prohibido por
    el contrato de render, y un grano animado desincronizaría en cuanto el
    renderer muestree frames en paralelo.
    """
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'>"
           f"<filter id='g'><feTurbulence type='fractalNoise' baseFrequency='0.82' "
           f"numOctaves='2' seed=\"{seed}\"/></filter>"
           f"<rect width='160' height='160' filter='url(#g)' opacity='{opacity}'/>"
           f"</svg>")
    from urllib.parse import quote
    return f"url(\"data:image/svg+xml,{quote(svg)}\")"


# ── la paleta activa ──────────────────────────────────────────────────────────
def use(name: str) -> None:
    """Activa una paleta. Muta en su lugar C/FILL/THEME/INK_ON_FILL (quien los
    importó por nombre ve el cambio) y reasigna los escalares, que los
    consumidores leen como `tokens.LINE`, nunca con `from tokens import LINE`.

    El tema semántico (`THEME`) cambia ACENTO, relleno y glow; nunca el color
    del texto, que ya está medido contra cada superficie."""
    global PALETTE, LINE, LINE_HI, SHADOW, SHADOW_LIFT, GLOW
    if name not in PALETTES_BASE:
        raise ValueError(f"paleta '{name}' no existe; las que hay son: {', '.join(PALETTES)}")
    c = _derive(name)
    C.clear()
    C.update(c)
    FILL.clear()
    FILL.update({
        "accent": rgba(c["accent"], .16), "accent2": rgba(c["accent"], .28),
        "go": rgba(c["go"], .14), "alert": rgba(c["alert"], .14),
        "warn": rgba(c["warn"], .14), "ink": rgba(c["text"], .05),
    })
    PALETTE = name
    LINE = c["line"]
    LINE_HI = mix(c["line"], c["text"], .15)
    SHADOW = _ELEVATION[name]["shadow"]
    SHADOW_LIFT = _ELEVATION[name]["shadow_lift"]
    GLOW = f"0 0 0 1px {rgba(c['accent'], .35)}, 0 18px 60px {rgba(c['accent'], .22)}"

    def glow(h):
        return f"0 0 0 1px {rgba(h, .32)}, 0 18px 60px {rgba(h, .20)}"
    THEME.clear()
    THEME.update({
        "primary": {"accent": c["accent"], "accent_text": c["accent_hi"],
                    "fill": FILL["accent"], "glow": GLOW},
        "problem": {"accent": c["alert"], "accent_text": c["alert"],
                    "fill": FILL["alert"], "glow": glow(c["alert"])},
        "warning": {"accent": c["warn"], "accent_text": c["warn"],
                    "fill": FILL["warn"], "glow": glow(c["warn"])},
        "success": {"accent": c["go"], "accent_text": c["go"], "fill": FILL["go"],
                    "glow": glow(c["go"])},
        "neutral": {"accent": c["text"], "accent_text": c["text"], "fill": FILL["ink"],
                    "glow": SHADOW},
    })
    # Sobre un relleno de señal va la tinta que más contraste da con él.
    INK_ON_FILL.clear()
    INK_ON_FILL.update({
        sem: max((c["bg"], c["text"]), key=lambda ink: contrast(ink, c[k]))
        for sem, k in (("warning", "warn"), ("success", "go"))
    })


def accent_a(a: float) -> str:
    """El acento de la paleta activa con opacidad `a`."""
    return rgba(C["accent"], a)


def ink_a(a: float) -> str:
    """El texto de la paleta activa con opacidad `a` (hairlines, rejilla)."""
    return rgba(C["text"], a)


def shade_a(a: float) -> str:
    """El suelo de la paleta activa con opacidad `a` (velos, halos de texto)."""
    return rgba(C["bg"], a)


use("oscuro")

# Coordenadas HORNEADAS del lienzo REEL 1080×1920. Se calculan aquí, en Python,
# no con cos/sin en el navegador. El centro va hacia y 820-880 porque un bloque
# centrado en el lienzo deja medio frame vacío bajo el PiP.
def _bake_slots(cx=540, cy=850, rx=330, ry=250):
    import math
    s = {"center": (cx, cy)}
    for i in range(6):
        a = math.radians(-90 + i * 60)
        s[f"orbit-{i+1}"] = (round(cx + rx * math.cos(a)), round(cy + ry * math.sin(a)))
    for i in range(4):
        s[f"stack-{i+1}"] = (cx, round(cy - 240 + i * 160))
    # Los dos extremos del RAIL vertical, para un flujo origen -> operador ->
    # destino en 9:16. Un flujo de tres bloques no cabe en horizontal: a 1080
    # de ancho, tres paneles legibles se quedan en 340 px cada uno y el del
    # medio —que es el que lleva la información— deja de leerse. En vertical
    # el operador se queda en `center` a tamaño de héroe y los dos extremos
    # caben encima y debajo.
    #
    # `foot` en 1250 no es libre: con un objeto de 108 px de alto acaba en
    # y1304, y el subtítulo de un stage empieza en y1352 (min(0.72·H,
    # floor_top) con dos líneas). 48 px de margen, medidos, no estimados.
    s["head"] = (cx, 440)
    s["foot"] = (cx, 1250)
    return s


SLOTS = _bake_slots()

# Escala dedicada de kinetic typography. `hero` cae EXACTAMENTE en TYPE.display
# de cada formato, así que extiende la escala verificada en vez de inventar una.
KINETIC = {
    "REEL":    {"small": 60, "medium": 93, "hero": 132, "mega": 168},
    "YOUTUBE": {"small": 51, "medium": 79, "hero": 112, "mega": 143},
}
