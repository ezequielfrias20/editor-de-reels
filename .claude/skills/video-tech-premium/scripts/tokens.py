#!/usr/bin/env python3
"""Sistema de diseño — grafito profundo + violeta eléctrico.

Única fuente de verdad del look. Lo importan `mockups.py` y
`build-composition.py`, así que un cambio aquí se propaga a toda la pieza.

La intención: **contenido educativo premium de tecnología, IA y negocios**.
Fondo casi negro, superficies flotando encima con hairline y sombra ancha,
tipografía grotesca pesada, y un único acento violeta de alto voltaje. El
violeta no es decorativo: sale del producto real que se muestra en pantalla
(el ERP), así que el gráfico y el screenshot pertenecen al mismo mundo.

Nada de blanco puro como fondo, nada de negro puro (#000): el fondo es
#0B0C10, un grafito con una pizca de azul que deja respirar los oscuros del
metraje en vez de aplastarlos.

CONTRASTES YA MEDIDOS (no repetir el error):
    blanco   / bg        19.55:1
    blanco   / surface   17.73:1
    text2    / surface    7.88:1
    text3    / surface    5.76:1   ← ya aguanta texto pequeño
    violet   / bg         4.50:1   AA-grande
    violet_hi/ bg         6.70:1   AA-normal ← el violeta para TEXTO
    blanco   / violet     4.35:1   AA-grande → solo ≥24px y en negrita
    bg       / go        11.74:1   → sobre verde va tinta, no blanco
    blanco   / alert      3.06:1   AA-grande
"""

# ── color ─────────────────────────────────────────────────────────────────────
C = {
    # suelo
    "bg":        "#0B0C10",   # grafito profundo — el fondo de todo
    "bg2":       "#101218",   # borde del viñeteado
    "surface":   "#16181F",   # tarjeta / panel
    "surface2":  "#1D2029",   # elevado (fila activa, celda destacada)
    "surface3":  "#252935",   # bordes internos de UI, tracks de barra

    # texto
    "text":      "#FFFFFF",
    "text2":     "#A7ADBB",   # secundario
    "text3":     "#8C93A3",   # metadatos — verificado a 5.76:1, ya no es trampa

    # acento (el voltaje)
    "violet":    "#7C5CFF",   # PRIMARIO: fills, barras, pastillas, keyword
    "violet_hi": "#9B85FF",   # el violeta cuando es TEXTO sobre oscuro
    "violet_lt": "#B8AAFF",   # texto violeta que además va a FUNDIR: 8.22:1 en
                              # reposo, así el transitorio de la entrada no cae
                              # tan abajo. Ningún color sobrevive un fundido
                              # entero, pero este llega mucho más lejos.
    "violet_dk": "#5B3FD6",   # sombra/profundidad del violeta

    # señal
    "go":        "#34E39B",   # resuelto · conectado · CTA
    "alert":     "#FF5A5A",   # problema · desconectado
    "warn":      "#FFB84D",   # atención

    # marcas de terceros (logos), tonos reales
    "excel":     "#21A366",
    "whatsapp":  "#25D366",
}

# Rellenos translúcidos. Se escriben aquí para que ningún mockup invente su
# propia opacidad y el sistema se desalinee.
FILL = {
    "violet":  "rgba(124,92,255,.16)",
    "violet2": "rgba(124,92,255,.28)",
    "go":      "rgba(52,227,155,.14)",
    "alert":   "rgba(255,90,90,.14)",
    "warn":    "rgba(255,184,77,.14)",
    "white":   "rgba(255,255,255,.05)",
}

# El ÚNICO borde. Un hairline claro sobre fondo oscuro es lo que separa una
# superficie premium de una caja plana.
LINE = "rgba(255,255,255,.09)"
LINE_HI = "rgba(255,255,255,.16)"

# ── elevación ─────────────────────────────────────────────────────────────────
# Sombra ancha y suave, nunca dura. Sobre fondo oscuro una sombra negra no se
# ve, así que la elevación la dan DOS cosas: la sombra (que asienta el objeto)
# y el hairline claro del borde superior (que lo separa del fondo).
SHADOW = "0 2px 6px rgba(0,0,0,.45), 0 18px 50px rgba(0,0,0,.55)"
SHADOW_LIFT = "0 8px 20px rgba(0,0,0,.55), 0 40px 90px rgba(0,0,0,.65)"
# El glow violeta es ESCASO: solo el objeto protagonista de un frame lo lleva.
GLOW = "0 0 0 1px rgba(124,92,255,.35), 0 18px 60px rgba(124,92,255,.22)"

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
            f"{C['bg']} 62%, #07080B 100%)")


def grid(size: int = 72, alpha: float = .022) -> str:
    """Rejilla técnica casi invisible. Le da al fondo una textura de producto
    —de plano, de blueprint— en vez de un degradado liso de plantilla."""
    a = f"rgba(255,255,255,{alpha})"
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


# Medido: a alpha 0.05 el violet_hi sobre el fondo iluminado da 6.08:1; a 0.07
# cae a 5.77 y deja de aguantar texto normal. El techo no es una opinión.
SPOTLIGHT_MAX = 0.05


def spotlight(alpha: float = SPOTLIGHT_MAX) -> str:
    """Foco cenital centrado. Empuja la mirada arriba, donde vive el objeto."""
    if alpha > SPOTLIGHT_MAX:
        raise ValueError(
            f"spotlight alpha {alpha} pasa del techo medido {SPOTLIGHT_MAX}: por "
            f"encima, el violeta como texto cae por debajo de AA sobre el fondo "
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


# El tema cambia ACENTO, relleno y glow. Nunca el color del texto: si lo
# cambiara, todo el trabajo de legibilidad habría que re-litigarlo cinco veces.
THEME = {
    "primary": {"accent": C["violet"], "accent_text": C["violet_hi"],
                "fill": FILL["violet"], "glow": GLOW},
    "problem": {"accent": C["alert"], "accent_text": C["alert"],
                "fill": FILL["alert"],
                "glow": "0 0 0 1px rgba(255,90,90,.32), 0 18px 60px rgba(255,90,90,.20)"},
    "warning": {"accent": C["warn"], "accent_text": C["warn"],
                "fill": FILL["warn"],
                "glow": "0 0 0 1px rgba(255,184,77,.30), 0 18px 60px rgba(255,184,77,.18)"},
    "success": {"accent": C["go"], "accent_text": C["go"], "fill": FILL["go"],
                "glow": "0 0 0 1px rgba(52,227,155,.30), 0 18px 60px rgba(52,227,155,.18)"},
    "neutral": {"accent": C["text"], "accent_text": C["text"], "fill": FILL["white"],
                "glow": SHADOW},
}

# ⚠ Sobre un relleno `warn` va TINTA, nunca blanco: text/warn = 1.72:1. Misma
# regla que ya está escrita para el verde (bg/go = 11.74:1).
INK_ON_FILL = {"warning": C["bg"], "success": C["bg"]}

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
