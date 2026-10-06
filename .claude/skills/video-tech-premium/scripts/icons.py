#!/usr/bin/env python3
"""Iconos de línea dibujados, para las animaciones que no son solo texto.

NACE DE UNA PETICIÓN DEL USUARIO EN LA PIEZA 19: «me gusta que las animaciones
también lleven iconos y así, no solo textos y recuadros». La librería de
`mockups.py` estaba casi entera hecha de pastillas, tarjetas y titulares — que
es lo correcto para enunciar, y demasiado plano para una enumeración de
ESPECIALIDADES, donde cada una tiene una forma reconocible antes de leerse.

⚠ **NUNCA UN EMOJI.** Es la lección que la pieza 18 pagó entera: el navegador
pinta un emoji con su propia paleta, pero el linter de contraste lee el `color`
HEREDADO del elemento —negro, si nadie lo declara— y midió **1.11:1** contra el
suelo para un 💡 que en el frame se veía perfecto. Un glifo dibujado no tiene
ese problema por construcción: va en `currentColor`, así que lo tiñe quien lo
hospeda y el par que mide el linter es el mismo que se ve.

CÓMO ESTÁN DIBUJADOS

Todos comparten un lienzo de 24×24 y un trazo de 1.8 con extremos y uniones
redondeados, así que a cualquier tamaño se leen como una familia y no como un
collage de sets distintos — el mismo criterio que §3 aplica a las dos familias
tipográficas. `stroke="currentColor"` y `fill="none"` salvo donde el relleno ES
la forma (el punto de un nodo), y ahí también va en `currentColor`.

⚠ **Cada uno se probó SOBRE UN FRAME a su tamaño real, no en el editor.** Cinco
de los dieciséis no sobrevivieron a 40 px en la primera pasada: la multitud
dibujada con arcos finos salía como una mancha, el engranaje de ocho marcas
sueltas se leía como un SOL, el tablero de estrategia como un borrón, el
martillo como un alfiler y la maraña como una rayita. Un icono no es correcto
porque el path lo sea — lo es cuando se reconoce al tamaño en que se va a ver,
y eso solo lo dice el frame (§14).

No llevan `id` propio: `check_unique_element_ids` falla sobre el HTML ensamblado
si un id se repite, y un icono se inlinea muchas veces por pieza (la trampa
7bis de §9, que con los gradientes de Canva dejó cinco marcas vacías). Estos no
tienen gradientes ni clip-paths — solo trazos — así que no hay nada que
renombrar por instancia.
"""

# Lienzo y trazo comunes: lo que los hace leerse como una familia.
VIEWBOX = "0 0 24 24"
STROKE = 1.8

# El cuerpo de cada icono: solo la geometría, sin el `<svg>` que la envuelve.
# El orden es el de la pieza 19, que es donde se estrenaron.
_PATHS: dict[str, str] = {
    # pieza 5: la llave de API (aro + paletón) y la cadena del link.
    "key": ('<circle cx="7.5" cy="12" r="4"/><path d="M11.5 12h9"/>'
            '<path d="M17.5 12v3.2"/><path d="M20.5 12v2.4"/>'),
    "link": ('<path d="M10.2 13.8a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1.1 1.1"/>'
             '<path d="M13.8 10.2a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1.1-1.1"/>'),
    # ── especialidades (los cinco chips del guion) ───────────────────────────
    # frontend: las llaves del código y una barra de cursor.
    "code": ('<path d="M9 7 4.5 12 9 17"/><path d="m15 7 4.5 5-4.5 5"/>'
             '<path d="M13.2 4.6 10.8 19.4"/>'),
    # marketing: el megáfono y sus dos ondas.
    "megaphone": ('<path d="M4 10v4a1 1 0 0 0 1 1h2l6 4V5L7 9H5a1 1 0 0 0-1 1Z"/>'
                  '<path d="M17.5 9.2a4 4 0 0 1 0 5.6"/>'
                  '<path d="M20 6.8a7.5 7.5 0 0 1 0 10.4"/>'),
    # contenido: la hoja con renglones y la esquina doblada.
    "doc": ('<path d="M14 3H7a1.5 1.5 0 0 0-1.5 1.5v15A1.5 1.5 0 0 0 7 21h10a1.5 1.5 0 0 0 1.5-1.5V7.5Z"/>'
            '<path d="M14 3v4.5h4.5"/><path d="M8.5 12.5h7"/><path d="M8.5 16.5h5"/>'),
    # comunidad: tres personas, la del medio delante.
    "people": ('<circle cx="9" cy="8" r="3"/>'
               '<path d="M3.4 19.2a5.6 5.6 0 0 1 11.2 0"/>'
               '<circle cx="17.6" cy="9.6" r="2.4"/>'
               '<path d="M16.1 14.7a4.6 4.6 0 0 1 4.5 4.5"/>'),
    # ingeniería: el engranaje.
    "gear": ('<circle cx="12" cy="12" r="3.1"/>'
             '<path d="M19.5 14.6a1.6 1.6 0 0 0 .32 1.77l.06.06a1.94 1.94 0 1 1-2.75 '
             '2.75l-.06-.06a1.6 1.6 0 0 0-1.77-.32 1.6 1.6 0 0 0-.97 1.47v.17a1.94 '
             '1.94 0 1 1-3.88 0v-.09a1.6 1.6 0 0 0-1.05-1.47 1.6 1.6 0 0 0-1.77.32l-.06'
             '.06a1.94 1.94 0 1 1-2.75-2.75l.06-.06a1.6 1.6 0 0 0 .32-1.77 1.6 1.6 0 0 '
             '0-1.47-.97h-.17a1.94 1.94 0 1 1 0-3.88h.09a1.6 1.6 0 0 0 1.47-1.05 1.6 '
             '1.6 0 0 0-.32-1.77l-.06-.06a1.94 1.94 0 1 1 2.75-2.75l.06.06a1.6 1.6 0 0 '
             '0 1.77.32h.08a1.6 1.6 0 0 0 .97-1.47v-.17a1.94 1.94 0 1 1 3.88 0v.09a1.6 '
             '1.6 0 0 0 .97 1.47 1.6 1.6 0 0 0 1.77-.32l.06-.06a1.94 1.94 0 1 1 2.75 '
             '2.75l-.06.06a1.6 1.6 0 0 0-.32 1.77v.08a1.6 1.6 0 0 0 1.47.97h.17a1.94 '
             '1.94 0 1 1 0 3.88h-.09a1.6 1.6 0 0 0-1.47.97Z"/>'),

    # ── el flujo de tres pasos ───────────────────────────────────────────────
    # estrategia: el tablero con la pieza y su línea de juego.
    "strategy": ('<circle cx="12" cy="12" r="8.6"/><circle cx="12" cy="12" r="4.7"/>'
                 '<circle cx="12" cy="12" r="1.15" fill="currentColor" stroke="none"/>'),
    # construir: el martillo y la viga.
    "build": ('<path d="M14.8 6.4a1 1 0 0 0 0 1.4l1.5 1.5a1 1 0 0 0 1.4 0l3.6-3.6a6 '
              '6 0 0 1-7.9 7.9l-6.8 6.8a2.1 2.1 0 1 1-3-3l6.8-6.8a6 6 0 0 1 '
              '7.9-7.9l-3.5 3.7Z"/>'),
    # QA: la lupa sobre la lista y el fallo que encuentra.
    "inspect": ('<circle cx="10.5" cy="10.5" r="5.5"/><path d="m14.6 14.6 5 5"/>'
                '<path d="m8.6 10.5 1.5 1.6 2.8-3"/>'),

    # ── la app de escritorio ─────────────────────────────────────────────────
    # el monitor con su pie: lo que distingue «escritorio» de «navegador».
    "desktop": ('<rect x="2.8" y="4" width="18.4" height="12.4" rx="1.8"/>'
                '<path d="M9 20.4h6"/><path d="M12 16.4v4"/>'),
    "download": ('<path d="M12 3.6v10.2"/><path d="m8.2 10.2 3.8 3.8 3.8-3.8"/>'
                 '<path d="M4.5 16.6v2.3a1.5 1.5 0 0 0 1.5 1.5h12a1.5 1.5 0 0 0 1.5-1.5v-2.3"/>'),
    "check": '<path d="m4.8 12.6 4.6 4.6L19.2 7.4"/>',

    # ── el agente, y lo que le pasa ──────────────────────────────────────────
    # un agente: el chip con su cara. Es el objeto que la pieza repite más.
    "agent": ('<rect x="4.6" y="6.4" width="14.8" height="12" rx="3"/>'
              '<circle cx="9.4" cy="12" r="1.15" fill="currentColor" stroke="none"/>'
              '<circle cx="14.6" cy="12" r="1.15" fill="currentColor" stroke="none"/>'
              '<path d="M12 3.2v3.2"/><path d="M2.6 11.2v2.4M21.4 11.2v2.4"/>'),
    # el repositorio abierto: la caja con la tapa levantada.
    "repo": ('<path d="M3.4 7.6 12 3.2l8.6 4.4"/>'
             '<path d="M3.4 7.6v8.8L12 20.8l8.6-4.4V7.6"/>'
             '<path d="M3.4 7.6 12 12l8.6-4.4"/><path d="M12 12v8.8"/>'),
    # la carga que aplasta a un agente solo: las tres tareas apiladas.
    "stack": ('<path d="m12 3.4 8.4 4.1-8.4 4.1-8.4-4.1Z"/>'
              '<path d="m3.6 12 8.4 4.1 8.4-4.1"/>'
              '<path d="m3.6 16.4 8.4 4.1 8.4-4.1"/>'),
    # ── la cadena de producción de un vídeo faceless (pieza 20) ─────────────
    # tema: la chispa. Un destello dibujado, nunca el emoji 💡 (§14).
    "spark": ('<path d="M12 2.6v3.4M12 18v3.4M2.6 12H6M18 12h3.4"/>'
              '<path d="m5.4 5.4 2.4 2.4M16.2 16.2l2.4 2.4M18.6 5.4l-2.4 2.4'
              'M7.8 16.2l-2.4 2.4"/>'
              '<circle cx="12" cy="12" r="3.4"/>'),
    # material: la imagen con su horizonte y su sol.
    "image": ('<rect x="3.2" y="4.6" width="17.6" height="14.8" rx="2.2"/>'
              '<circle cx="8.6" cy="9.8" r="1.7"/>'
              '<path d="m3.7 16.6 4.6-4.2 3.4 3 3.1-2.6 5.1 4.4"/>'),
    # narración: el micrófono.
    "mic": ('<rect x="9" y="2.6" width="6" height="11.2" rx="3"/>'
            '<path d="M5.4 11.4a6.6 6.6 0 0 0 13.2 0"/>'
            '<path d="M12 18v3.4"/><path d="M8.6 21.4h6.8"/>'),
    # subtítulos: la caja con sus dos renglones cortos.
    "captions": ('<rect x="2.8" y="5" width="18.4" height="14" rx="2.4"/>'
                 '<path d="M6.6 11.4h5.2M6.6 15h8.8M15.2 11.4h2.2"/>'),
    # música: la corchea.
    "music": ('<path d="M9.4 18.2V5.4l9.2-2v12.4"/>'
              '<circle cx="6.8" cy="18.2" r="2.6"/><circle cx="16" cy="15.8" r="2.6"/>'),
    # render: la claqueta de cine con su play.
    "film": ('<rect x="2.8" y="5" width="18.4" height="14" rx="2.4"/>'
             '<path d="M2.8 9.6h18.4M8.4 5v4.6M15.6 5v4.6"/>'
             '<path d="m10.6 12.6 4.4 2.6-4.4 2.6Z"/>'),
    # las visualizaciones que no llegan.
    "eye": ('<path d="M2.4 12s3.5-6.4 9.6-6.4S21.6 12 21.6 12s-3.5 6.4-9.6 '
            '6.4S2.4 12 2.4 12Z"/><circle cx="12" cy="12" r="2.8"/>'),
    # el tiempo que cuesta hacerlo a mano.
    "clock": ('<circle cx="12" cy="12" r="8.8"/><path d="M12 6.8V12l3.6 2.2"/>'),
    # el puntero que pulsa el botón.
    "pointer": ('<path d="M5.6 3.4 18.2 11l-5.4 1.5-2.6 5.2Z"/>'
                '<path d="m13.4 13.6 4.6 5.2"/>'),
    # el problema complejo, antes de repartirse.
    "knot": ('<circle cx="5.8" cy="6.6" r="2.1"/><circle cx="18.2" cy="7.6" r="2.1"/>'
             '<circle cx="11.6" cy="18" r="2.1"/>'
             '<path d="m7.4 8.2 8.5 8.2M16.6 9.3 7.9 16.2M7.9 6.9l8.2.5"/>'),
}

# Alias, para que un componente pida el concepto y no el dibujo.
_ALIAS = {
    # la cadena de la pieza 20, para que el plan pida el PASO y no el dibujo
    "tema": "spark",
    "guion": "doc",
    "material": "image",
    "narracion": "mic",
    "subtitulos": "captions",
    "musica": "music",
    "render": "film",
    "frontend": "code",
    "marketing": "megaphone",
    "contenido": "doc",
    "comunidad": "people",
    "ingenieria": "gear",
}


def names() -> list[str]:
    """Los iconos disponibles. Lo usa el test que fija el roster."""
    return sorted(_PATHS)


def icon(name: str, size: int = 34, stroke: float = STROKE) -> str:
    """Un icono en `currentColor`, listo para inlinear.

    `size` es el lado del cuadrado; el trazo NO se escala con él a propósito —
    un icono de 64 px con trazo proporcional se convierte en una mancha, y uno
    de 22 px con trazo fino desaparece. Quien lo llama ajusta `stroke` si el
    tamaño se sale del rango de 28–48 px para el que está dibujado.
    """
    key = _ALIAS.get(name, name)
    if key not in _PATHS:
        raise KeyError(f"icono desconocido: {name!r} — hay {', '.join(names())}")
    return (f'<svg class="ic" viewBox="{VIEWBOX}" width="{size}" height="{size}" '
            f'fill="none" stroke="currentColor" stroke-width="{stroke}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'{_PATHS[key]}</svg>')
