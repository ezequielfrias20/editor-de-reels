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
