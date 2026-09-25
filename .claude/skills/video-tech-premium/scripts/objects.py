#!/usr/bin/env python3
"""Objetos con estado y el escenario que los sostiene.

Mismo contrato que `mockups.py`: cada función devuelve `(css, html, anims)`.

EL STAGE ES UNO, NO UNO POR SEGMENTO. La serie entera de segmentos contiguos
sale como una sola entrada de `visuals`, con un `fade_in` al principio y un
`fade_out` al final. Dos takeovers seguidos abrían un hueco de 0.15-0.25 s en el
cruce que se leía como un fallo — la razón de existir de `check_no_black()`.
Con un stage continuo esa clase de bug no puede ocurrir.
"""
from __future__ import annotations

import tokens as t


# Entrada genérica de un objeto: fundido + escala, reutilizando el preset
# `scale-pop` que ya existe y está verificado en 4 piezas. El vocabulario
# dedicado de entradas (float-in con overshoot 65->108->100, drop-in, etc.)
# es trabajo de una tarea de presets propia; esto es lo mínimo para que un
# objeto deje de estar en opacity:0 para siempre.
OBJECT_ENTRANCE_DURATION = 0.35

# 8 vueltas de minutera en 0.42 s se difuminan solas: el motion blur no hay
# que fingirlo (spec §4).
HANDS_SWEEP_DURATION = 0.42

# Un sub-elemento que se enciende: la misma duración que `chip-in` ya usa en
# la librería de mockups, para que una fila de la base de conocimiento y una
# pastilla de `chip_grid` entren con el mismo peso.
REVEAL_DURATION = 0.30

# El contador sube RÁPIDO: es la repetición lo que vende, no la cifra. Por
# encima de ~0.5 s el ojo empieza a leer los números intermedios y el efecto
# pasa de "esto no para" a "esto se calcula".
COUNT_ROLL_DURATION = 0.34


def motion_stage(cid: str, theme: str = "primary", objects=None, at=None,
                 visual_start: float = 0.0,
                 spotlight_alpha: float = t.SPOTLIGHT_MAX, seed: int = 7, **_):
    """`objects` y `at` llegan DECLARATIVOS desde `edl_compile._visuals()`:
    `objects` es `[{"id","kind","slot","state","in"}, ...]` y `at` es
    `[{"t","op","id","hour","minute","preset"}, ...]`, con `in`/`t` en la línea
    ABSOLUTA de la pieza. Aquí se despachan a la función de render de cada
    `kind` (vía REGISTRY) y se traducen los `OBJECT_STATE` a tweens reales —
    el compilador no sabe de GSAP, solo de ángulos y tiempos.

    ⚠ `visual_start` (= `q(v["start"])`, el mismo valor que `_visuals()` puso
    en la entrada de `visuals`) es OBLIGATORIO para que los tiempos salgan
    bien: `build-composition.py` reconstruye el tiempo absoluto de cada anim
    como `s + a[2]` — espera que `a[2]` sea un OFFSET relativo al inicio del
    visual, como hacen todos los mockups de `mockups.py`. Pasar un tiempo
    absoluto ahí lo suma DOS veces (bug real: un `in` en la palabra 18, a
    ~5.03 s, aterrizaba a las 9.17 s — exactamente `visual_start + 5.03`).
    """
    if theme not in t.THEME:
        raise KeyError(f"tema '{theme}' desconocido; hay {sorted(t.THEME)}")
    th = t.THEME[theme]
    objects, at = list(objects or []), list(at or [])

    # ⚠ El scoping es `.viz[data-viz-id="{cid}"]`, NUNCA `#{cid}`: `cid` nunca
    # es el id LITERAL de un elemento del DOM — el host lleva `id="host-{cid}"`
    # y el `data-viz-id` es un ATRIBUTO, no un id. `#{cid}` era un selector
    # de ID que no matcheaba nada: bug latente desde la Tarea 5, invisible
    # porque `clock()` pinta sus colores a mano y nunca dependió de esta hoja
    # de estilos ni de `.accent`/`currentColor`. La Tarea 9 lo expuso al ser
    # el primer objeto que sí depende de ella — sin el scoping correcto,
    # `.obj.accent` no hereda ningún `color` y `stroke="currentColor"` cae al
    # negro por defecto del navegador: los cuatro objetos SE VEÍAN, pero
    # invisibles contra el fondo oscuro.
    scope = f'.viz[data-viz-id="{cid}"]'
    css = f"""
/* Motion Stage — suelo continuo de una serie de segmentos.
   El fondo va en un ELEMENTO del DOM: el `background` de la página se descarta
   en el render (trampa nº1), y el fill de una escena a pantalla completa nunca
   va en la raíz de la composición. */
{scope} .stage-ground{{position:absolute;inset:0;
  background:{t.spotlight(spotlight_alpha)},{t.grid()},{t.vignette()}}}
{scope} .stage-grain{{position:absolute;inset:0;pointer-events:none;
  background-image:{t.grain(seed)};background-repeat:repeat}}
{scope} .stage-plane{{position:absolute;inset:0}}
{scope} .obj{{position:absolute;display:block;opacity:0;
  transform-origin:50% 50%;filter:drop-shadow({t.SHADOW.split(')')[0]}))}}
{scope} .obj.accent{{color:{th['accent_text']}}}
{scope} .obj .fill{{background:{th['fill']}}}
{scope} .obj.hero{{box-shadow:{th['glow']}}}
{scope} .stage-type{{color:{t.C['text']};font-family:{t.FONT};font-weight:900}}
"""
    anims: list = []
    eid_of: dict[str, str] = {}       # instanceId -> el id real en el DOM
    cuerpo_partes: list[str] = []

    for od in objects:
        kind = od["kind"]
        fn = REGISTRY.get(kind)
        if fn is None or kind == "motion_stage":
            disponibles = sorted(k for k in REGISTRY if k != "motion_stage")
            raise KeyError(
                f"objeto '{kind}' no existe en la librería; hay {disponibles}. "
                f"El compilador no diseña objetos nuevos, solo despacha (§9)")
        r = fn(cid, od["id"], od.get("state", {}), od.get("slot", "center"))
        cuerpo_partes.append(r["html"])
        eid_of[od["id"]] = r["eid"]
        t0 = od["in"] - visual_start
        anims.append(("scale-pop", f"#{r['eid']}", t0,
                      OBJECT_ENTRANCE_DURATION))
        # LA COREOGRAFÍA INTERNA ES DEL OBJETO, NO DEL EDL. Los anims que
        # devuelve la función de render llegan relativos a la ENTRADA del
        # objeto y aquí se desplazan a la línea del stage. Sin este
        # desplazamiento aterrizarían en el inicio del stage, que es otro
        # instante en cuanto el objeto no es el primero en entrar.
        #
        # Por qué existe: una lista que se apila fila a fila es UN gesto, no
        # seis decisiones editoriales. Declararlo con seis `OBJECT_STATE` en
        # el EDL metería en el contrato creativo un escalonado de 130 ms que
        # no sale del transcript — justo lo que la frontera del §9 quiere
        # evitar por el otro lado. Cuando cada fila SÍ cae en su palabra (el
        # enunciado de categorías de la pieza 12), el EDL usa `reveal` y el
        # objeto entra con las filas apagadas.
        for a in r.get("anims", []):
            anims.append((a[0], a[1], round(a[2] + t0, 4)) + tuple(a[3:]))

    cuerpo = "".join(cuerpo_partes)
    # El grano va deliberadamente POR ENCIMA de los objetos: es lo que los mete
    # en la misma película que el metraje. Cuesta una excepción en el linter de
    # layout, que no puede ver a través de un `background-image` y cuenta la
    # capa como opaca — ver `OBJ_ATTRS`. El atributo tiene que ir en el elemento
    # OCULTO, no en el que tapa: probado aquí primero, y los seis errores no se
    # movieron.
    html = (f'<div class="stage-ground"></div>'
            f'<div class="stage-plane">{cuerpo}</div>'
            f'<div class="stage-grain"></div>')

    for op in at:
        eid = eid_of.get(op["id"])
        if eid is None:
            continue    # instancia de un stage anterior (Tarea 9); nada que animar aquí
        if op.get("op") == "state" and "hour" in op and "minute" in op:
            # El post-procesado de build-composition.py solo antepone el
            # scoping `.viz[data-viz-id=...]` al SEL de la posición a[1]. La
            # aguja de minutos vive en a[6] y hay que dárselo a mano — si no,
            # el selector sale sin ámbito y puede colisionar con otro stage.
            #
            # `hour_from`/`minute_from` viajan explícitos (no se leen del
            # elemento): el barrido no confía en transform-origin de CSS, que
            # en un <g> SVG demostró no ser fiable bajo GSAP (ver el aviso en
            # `clock()`), así que el compilador da los dos extremos y el
            # tween se hace sobre un número puro, no sobre `rotation`.
            anims.append(("hands-sweep", f"#{eid}-h", op["t"] - visual_start,
                          HANDS_SWEEP_DURATION, op["hour_from"], op["hour"],
                          f'.viz[data-viz-id="{cid}"] #{eid}-m',
                          op["minute_from"], op["minute"]))
        if "reveal" in op:
            # Un sub-elemento del objeto que se enciende en SU palabra. El
            # objeto expone ids `{eid}-{sufijo}`; el EDL nombra el sufijo y
            # el compilador solo pasa el instante. Genérico a propósito: la
            # fila de una categoría, un sello, una insignia — cualquier cosa
            # que el objeto quiera dejar apagada esperando su beat.
            anims.append(("chip-in", f"#{eid}-{op['reveal']}",
                          op["t"] - visual_start, REVEAL_DURATION))
        if "count" in op and "count_from" in op:
            # El contador que sube. Mismo patrón probado que `hands-sweep`:
            # se tuenea un número PURO y en cada `onUpdate` se reescribe el
            # texto. Determinista —GSAP llama al onUpdate con el valor ya
            # interpolado en cada seek, nunca por reloj de pared— y sin
            # animar ninguna propiedad fuera del allowlist.
            anims.append(("count-roll", f"#{eid}-num", op["t"] - visual_start,
                          COUNT_ROLL_DURATION, op["count_from"], op["count"],
                          op.get("count_prefix", "#")))
        if "dx" in op and "dy" in op:
            # `dx`/`dy` ya vienen horneados por `crowd_delta()` — el
            # compilador los calculó desde el slot ORIGINAL de la instancia
            # (§9: aritmética y lookup son suyos). Aquí solo se traduce el
            # dict a la tupla de anim que espera `build-composition.py`.
            anims.append(("crowd-in", f"#{eid}", op["t"] - visual_start,
                          CROWD_IN_DURATION, op["dx"], op["dy"]))

    return css, html, anims


def hand_angles(desde: str, hasta: str) -> dict:
    """Ángulos de las agujas, SIEMPRE hacia delante.

    Que el sentido sea obligatoriamente horario no es un detalle de pulido:
    de 11:00 a 19:00, el camino corto de la aguja horaria es 330° -> 210°, o
    sea -120°, y el reloj iría hacia atrás. Ocho horas PERDIDAS se leerían
    como ocho horas recuperadas — justo lo contrario de lo que dice la frase.

    Se deriva todo de los minutos transcurridos: la minutera gira 6°/min y la
    horaria 0.5°/min, así que ambas salen positivas por construcción.
    """
    def parse(s: str) -> int:
        try:
            h, m = s.split(":")
            h, m = int(h), int(m)
            if not (0 <= h < 24 and 0 <= m < 60):
                raise ValueError
        except Exception:
            raise ValueError(f"hora '{s}' mal formada; se espera HH:MM en 24 h")
        return h * 60 + m

    a, b = parse(desde), parse(hasta)
    transcurridos = (b - a) % (24 * 60)          # cruzar medianoche va hacia delante
    hour_from = (a / 60 % 12) * 30
    return {
        "hour_from": round(hour_from, 3),
        "hour_to": round(hour_from + transcurridos * 0.5, 3),
        "minute_from": round((a % 60) * 6, 3),
        "minute_to": round((a % 60) * 6 + transcurridos * 6, 3),
    }


def clock(cid: str, iid: str, state: dict, slot: str = "center", **_) -> dict:
    """Reloj 2.5D. Las agujas se hornean en su ángulo inicial con el
    atributo SVG NATIVO `rotate(ángulo, cx, cy)` — NO con CSS `transform` —
    y se mueven con un tween sobre un número puro, no sobre `rotation`.

    ⚠ Por qué no CSS. Depurado con un dump del `transform` computado:
    `transform:rotate(...)deg);transform-origin:150px 150px` en un `<g>` SVG
    se renderizaba bien en un HTML aislado, pero en la composición real GSAP
    lo tocaba (para poder tuenear `rotation` más adelante) y el navegador
    reportaba el pivote computado como "0px 0px" pese al inline style —
    probado con `transform-origin` y con `svgOrigin`, ninguno sobrevivía. La
    aguja giraba desde la esquina del viewBox, no desde su centro; y en un
    segundo tween sobre la misma propiedad aparecía además una traslación
    espuria. La sintaxis nativa `rotate(a, cx, cy)` incrusta el pivote en el
    propio valor del atributo: no hay origen que resolver, así que no hay
    nada que GSAP pueda malinterpretar. El barrido (`build-composition.py`,
    kind `hands-sweep`) anima un objeto `{v: ángulo}` y en cada `onUpdate` —
    determinista, GSAP lo llama con el valor ya interpolado en cada seek,
    nunca por reloj de pared — reescribe este mismo atributo.
    """
    x, y = t.SLOTS[slot]
    a = hand_angles(state.get("time", "12:00"), state.get("time", "12:00"))
    eid = f"{cid}-{iid}"
    html = f"""
<div class="obj" id="{eid}" data-layout-allow-overflow style="left:{x - 150}px;
     top:{y - 150}px;width:300px;height:300px">
  <svg viewBox="0 0 300 300" width="300" height="300">
    <circle cx="150" cy="150" r="140" fill="{t.C['surface']}"
            stroke="{t.LINE_HI}" stroke-width="2"/>
    <circle cx="150" cy="150" r="120" fill="none" stroke="{t.LINE}" stroke-width="1"/>
    <g id="{eid}-h" transform="rotate({a['hour_from']} 150 150)">
      <rect x="144" y="78" width="12" height="76" rx="6" fill="{t.C['text']}"/>
    </g>
    <g id="{eid}-m" transform="rotate({a['minute_from']} 150 150)">
      <rect x="146" y="46" width="8" height="108" rx="4" fill="{t.C['text2']}"/>
    </g>
    <circle cx="150" cy="150" r="10" fill="{t.C['accent']}"/>
  </svg>
</div>"""
    return {"html": html, "anims": [], "eid": eid}


# ── acumulación — cuatro tareas a la vez ─────────────────────────────────────
# El 0.42 no es un número libre: es la MISMA fracción de cierre que documenta
# la razón del beat en el EDL. Un valor de reserva evita que el compilador
# tenga que conocerlo — `crowd_delta(slot)` basta.
CROWD_FRACTION = 0.42
CROWD_IN_DURATION = 0.50


def crowd_delta(slot: str, fraction: float = CROWD_FRACTION) -> tuple[int, int]:
    """Cuánto se desplaza una instancia desde su órbita hacia el CENTRO.

    Horneado en Python sobre `tokens.SLOTS`, nunca con cos/sin en el
    navegador — mismo contrato de determinismo que las propias órbitas. El
    resultado es un DELTA, no una posición absoluta: GSAP anima `x`/`y` como
    transform relativo a la posición natural del elemento (la que ya le dio
    su `left`/`top` horneado), así que sumar el delta lo acerca al centro sin
    tocar su layout base.

    `slot == "center"` da `(0, 0)` por construcción — no es un caso especial,
    es la resta de una coordenada consigo misma. Es la comprobación que
    mantiene honesto el efecto: el sillón nunca se mueve, el mundo se le
    cierra encima.
    """
    cx, cy = t.SLOTS["center"]
    ox, oy = t.SLOTS[slot]
    return round((cx - ox) * fraction), round((cy - oy) * fraction)


def _object_html(cid: str, iid: str, slot: str, w: int, h: int,
                 tilt: float, svg: str) -> dict:
    """El wrapper común de un objeto con estado.

    Dos capas, a propósito: el DIV EXTERIOR (`#{eid}`) es lo único que GSAP
    toca —`opacity`/`scale`/`x`/`y`, el allowlist— y lleva el `left`/`top`
    horneado por slot. El `rotateY` de reposo va en un HIJO estático: si
    viviera en el mismo elemento que anima GSAP, un tween posterior de
    `scale` reescribiría el `transform` entero y se llevaría el tilt por
    delante (mismo problema que documenta `clock()` para el pivote del SVG,
    aunque aquí la solución es una capa de más, no un atributo nativo).

    `class="obj accent"` hereda el color del tema por `currentColor`: es el
    mecanismo que ya declara el CSS de `motion_stage()`, no algo nuevo.
    """
    x, y = t.SLOTS[slot]
    eid = f"{cid}-{iid}"
    html = f"""
<div class="obj accent" id="{eid}" data-layout-allow-overflow style="left:{x - w // 2}px;
     top:{y - h // 2}px;width:{w}px;height:{h}px">
  <div style="width:100%;height:100%;transform:perspective(900px) rotateY({tilt}deg);
       transform-style:preserve-3d">
    {svg}
  </div>
</div>"""
    return {"html": html, "anims": [], "eid": eid}


def dental_chair(cid: str, iid: str, state: dict, slot: str = "center", **_) -> dict:
    """El sillón — el protagonista FIJO de la acumulación. Vive en `center` y
    nunca lleva `crowd`: es el punto hacia el que los demás convergen, no uno
    más que converge."""
    svg = f"""<svg viewBox="0 0 320 320" width="320" height="320">
  <rect x="90" y="30" width="60" height="46" rx="16" fill="{t.C['surface']}"
        stroke="currentColor" stroke-width="3"/>
  <rect x="70" y="60" width="100" height="150" rx="20" fill="{t.C['surface']}"
        stroke="currentColor" stroke-width="3"/>
  <rect x="70" y="196" width="140" height="34" rx="12" fill="{t.C['surface']}"
        stroke="{t.LINE_HI}" stroke-width="2"/>
  <rect x="172" y="206" width="66" height="22" rx="10" fill="{t.C['surface']}"
        stroke="{t.LINE_HI}" stroke-width="2"/>
  <rect x="132" y="230" width="14" height="52" fill="{t.LINE_HI}"/>
  <ellipse cx="139" cy="290" rx="72" ry="11" fill="{t.LINE}"/>
</svg>"""
    return _object_html(cid, iid, slot, 320, 320, -6, svg)


def phone(cid: str, iid: str, state: dict, slot: str = "orbit-1", **_) -> dict:
    """El teléfono sonando. Las dos ondas son decoración estática — SOLO el
    div exterior se anima, así que no hace falta que hagan nada."""
    svg = f"""<svg viewBox="0 0 200 200" width="200" height="200">
  <path d="M40 58 Q18 100 40 142" fill="none" stroke="currentColor"
        stroke-width="4" stroke-linecap="round" opacity="0.55"/>
  <path d="M160 58 Q182 100 160 142" fill="none" stroke="currentColor"
        stroke-width="4" stroke-linecap="round" opacity="0.55"/>
  <rect x="55" y="20" width="90" height="160" rx="20" fill="{t.C['surface']}"
        stroke="currentColor" stroke-width="3"/>
  <rect x="68" y="40" width="64" height="112" rx="4" fill="{t.C['bg']}"/>
  <circle cx="100" cy="166" r="6" fill="currentColor"/>
</svg>"""
    return _object_html(cid, iid, slot, 200, 200, 10, svg)


def card_payment(cid: str, iid: str, state: dict, slot: str = "orbit-2", **_) -> dict:
    """La tarjeta de cobro: silueta con banda magnética y chip."""
    svg = f"""<svg viewBox="0 0 220 150" width="220" height="150">
  <rect x="10" y="10" width="200" height="130" rx="16" fill="{t.C['surface']}"
        stroke="currentColor" stroke-width="3"/>
  <rect x="10" y="42" width="200" height="26" fill="currentColor" opacity="0.85"/>
  <rect x="28" y="96" width="42" height="20" rx="4" fill="{t.LINE_HI}"/>
  <rect x="150" y="96" width="42" height="20" rx="6" fill="{t.LINE_HI}"/>
</svg>"""
    return _object_html(cid, iid, slot, 220, 150, -8, svg)


def instagram(cid: str, iid: str, state: dict, slot: str = "orbit-3", **_) -> dict:
    """Notificaciones sociales llegando. Un globo de chat con líneas de
    mensaje y una insignia de alerta — el CONCEPTO (mensajes que se
    acumulan), no el logotipo literal de ninguna app."""
    svg = f"""<svg viewBox="0 0 200 200" width="200" height="200">
  <rect x="20" y="30" width="160" height="110" rx="24" fill="{t.C['surface']}"
        stroke="currentColor" stroke-width="3"/>
  <path d="M60 55 h50 M60 76 h80 M60 97 h60" stroke="{t.LINE_HI}"
        stroke-width="7" stroke-linecap="round"/>
  <path d="M55 140 L75 168 L92 140 Z" fill="{t.C['surface']}"
        stroke="currentColor" stroke-width="3"/>
  <circle cx="152" cy="48" r="15" fill="currentColor"/>
</svg>"""
    return _object_html(cid, iid, slot, 200, 200, 8, svg)


def bottleneck(cid: str, iid: str, state: dict, slot: str = "center", **_) -> dict:
    """El sexto y último objeto de la librería inicial (Global Constraints:
    empieza con 6, no con 15). Un embudo: varios esperan arriba, la boca los
    aprieta, uno solo sale por el cuello — «contratar a alguien más no lo
    arregla, solo MUEVE el cuello de botella» es literal, no una metáfora
    que haya que traducir a otra forma."""
    svg = f"""<svg viewBox="0 0 320 320" width="320" height="320">
  <circle cx="110" cy="42" r="15" fill="{t.C['surface']}" stroke="currentColor" stroke-width="3"/>
  <circle cx="152" cy="30" r="15" fill="{t.C['surface']}" stroke="currentColor" stroke-width="3"/>
  <circle cx="194" cy="42" r="15" fill="{t.C['surface']}" stroke="currentColor" stroke-width="3"/>
  <circle cx="232" cy="60" r="15" fill="{t.C['surface']}" stroke="currentColor" stroke-width="3"/>
  <circle cx="76" cy="62" r="15" fill="{t.C['surface']}" stroke="currentColor" stroke-width="3"/>
  <path d="M40 92 L280 92 L188 232 L132 232 Z" fill="{t.C['surface']}"
        stroke="currentColor" stroke-width="3"/>
  <rect x="132" y="232" width="56" height="46" fill="{t.C['surface']}"
        stroke="{t.LINE_HI}" stroke-width="2"/>
  <circle cx="160" cy="298" r="15" fill="{t.LINE_HI}"/>
</svg>"""
    return _object_html(cid, iid, slot, 320, 320, -6, svg)


# ── pieza 12 — la repetición, la base y la respuesta aprobada ────────────────
# La librería CRECE POR DEMANDA REAL, no por catálogo (spec §3). Estos cuatro
# salen de los cuatro beats del REEL 10 que no se podían decir con los seis de
# la pieza 10: la pregunta que se repite, la cuenta de veces que se repite, el
# documento donde se organiza y la respuesta que sale de él.
TR = t.TYPE["REEL"]

# ⚠ POR QUÉ `data-layout-allow-occlusion`. Estos son los primeros objetos de la
# librería con TEXTO dentro, y el texto de un objeto vive por debajo de
# `.stage-grain`, que es a sangre. El grano está al 3.5 % de opacidad y no
# oculta nada —los 30/30 pares de contraste WCAG se miden igual—, pero el
# linter de layout no puede ver a través de un `background-image` y cuenta la
# capa como opaca: seis errores de golpe en la pieza 12 y ninguno en la 10,
# cuyos seis objetos eran SVG puro.
#
# Va en el CONTENEDOR de cada objeto nuevo, no en el grano (el linter quiere la
# marca en el elemento ocluido) y no en `_object_html` (eso se lo aplicaría
# también a los seis objetos de la pieza 10, que no lo necesitan y que así
# conservan la comprobación por si algún día llevan texto). Las dos
# alternativas se descartaron: bajar el grano por debajo del plano de objetos
# cambiaría en silencio cómo se renderiza una pieza ya entregada, y además un
# grano que no cubre al sujeto no es grano.
OBJ_ATTRS = "data-layout-allow-overflow data-layout-allow-occlusion"

MSG_CARD_H = 100


def msg_card(cid: str, iid: str, state: dict, slot: str = "stack-1", **_) -> dict:
    """La pregunta que llega otra vez. Es deliberadamente ANODINA: cuatro
    instancias iguales apiladas comunican la repetición mejor que cualquier
    dibujo, y para eso tienen que rimar entre sí.

    `dx` desplaza la burbuja del eje: cuatro tarjetas perfectamente centradas
    se leen como una tabla, y alternando el desplazamiento se leen como un
    hilo de chat, que es lo que son.

    `seal` deja preparada una pastilla que NO se ve hasta que un
    `OBJECT_STATE` con `reveal: "seal"` la enciende — el mismo objeto sirve
    para el problema (la pregunta cruda) y para el remate (la misma pregunta,
    ya automatizada) sin dibujar un segundo objeto. El sello va sobre relleno
    verde y por tanto con TINTA `bg`, nunca blanco: text/go se queda en
    1.66:1 y bg/go da 11.74:1.
    """
    x, y = t.SLOTS[slot]
    w = int(state.get("w", 420))
    dx = int(state.get("dx", 0))
    h = MSG_CARD_H
    eid = f"{cid}-{iid}"
    txt = state.get("text", "")
    seal = state.get("seal")
    seal_html = ""
    if seal:
        seal_html = (
            f'<span id="{eid}-seal" style="margin-left:auto;flex:0 0 auto;opacity:0;'
            f"font-family:{t.MONO};font-weight:700;font-size:{TR['chip'] - 4}px;"
            f"letter-spacing:.12em;background:{t.C['go']};color:{t.C['bg']};"
            f'border-radius:{t.RADIUS["pill"]}px;padding:8px 16px">{seal}</span>')
    arrow = ""
    if state.get("arrow") == "down":
        # La flecha del flujo. Estática y fuera de la caja: el contenedor
        # entra por opacidad y lo que se mueve es su contenido, así que un
        # trazo decorativo no necesita animarse para pertenecer al frame.
        arrow = (f'<svg viewBox="0 0 40 46" width="40" height="46" '
                 f'style="position:absolute;left:{w // 2 - 20}px;top:{h + 8}px">'
                 f'<path d="M20 2 V30 M8 22 L20 34 L32 22" fill="none" '
                 f'stroke="currentColor" stroke-width="4" stroke-linecap="round" '
                 f'stroke-linejoin="round" opacity="0.75"/></svg>')
    html = f"""
<div class="obj accent" id="{eid}" {OBJ_ATTRS}
     style="left:{x + dx - w // 2}px;top:{y - h // 2}px;width:{w}px;height:{h}px">
  <div style="width:100%;height:100%;box-sizing:border-box;display:flex;
       align-items:center;gap:18px;padding:0 26px;background:{t.C['surface2']};
       border:1px solid {t.LINE_HI};border-radius:{t.RADIUS['lg']}px;
       box-shadow:{t.SHADOW}">
    <span style="width:14px;height:14px;border-radius:50%;
          background:currentColor;flex:0 0 auto"></span>
    <span style="font-family:{t.FONT};font-weight:700;font-size:{TR['body']}px;
          color:{t.C['text']};white-space:nowrap">{txt}</span>
    {seal_html}
  </div>
  {arrow}
</div>"""
    return {"html": html, "anims": [], "eid": eid}


def answer_counter(cid: str, iid: str, state: dict, slot: str = "head", **_) -> dict:
    """El contador flotante: «RESPUESTA #12» subiendo a #27.

    Es el único de los cuatro que no dibuja una cosa, sino una CANTIDAD. La
    cifra vive en su propio span (`{eid}-num`) porque el tween del contador
    le reescribe el texto y no puede tocar nada más de la tarjeta.

    El prefijo `#` viaja en el propio texto y NO se recalcula en el
    `onUpdate`: si el prefijo estuviera dentro del número interpolado, un
    seek a mitad del tween pintaría un valor sin él.
    """
    x, y = t.SLOTS[slot]
    w, h = 560, 150
    eid = f"{cid}-{iid}"
    n = int(state.get("n", 0))
    label = state.get("label", "RESPUESTA")
    sub = state.get("sub", "IGUAL A LA ANTERIOR")
    html = f"""
<div class="obj accent" id="{eid}" {OBJ_ATTRS}
     style="left:{x - w // 2}px;top:{y - h // 2}px;width:{w}px;height:{h}px">
  <div style="width:100%;height:100%;box-sizing:border-box;display:flex;
       align-items:center;gap:26px;padding:0 34px;background:{t.C['surface']};
       border:1px solid {t.LINE_HI};border-radius:{t.RADIUS['lg']}px;
       box-shadow:{t.SHADOW}">
    <div style="display:flex;flex-direction:column;gap:6px;flex:1 1 auto">
      <span style="font-family:{t.MONO};font-weight:700;font-size:{TR['chip']}px;
            letter-spacing:.16em;color:{t.C['text2']}">{label}</span>
      <span style="font-family:{t.MONO};font-weight:400;font-size:{TR['chip'] - 4}px;
            letter-spacing:.10em;color:{t.C['text3']}">{sub}</span>
    </div>
    <span id="{eid}-num" style="font-family:{t.FONT};font-weight:900;
          font-size:{round(TR['display'] * 0.82)}px;line-height:.9;
          letter-spacing:-.05em;color:currentColor;flex:0 0 auto">#{n}</span>
  </div>
</div>"""
    return {"html": html, "anims": [], "eid": eid}


KB_ROW_H = 62
KB_ROW_GAP = 12
KB_HEAD_H = 92
KB_PAD = 26


def knowledge_base(cid: str, iid: str, state: dict, slot: str = "center", **_) -> dict:
    """El documento: cabecera y una fila por categoría.

    DOS MODOS, y la diferencia es de quién sale el ritmo:

    · `reveal: False` — las filas entran solas, escalonadas 130 ms desde la
      entrada del propio documento. Es UN gesto ("esto se organiza"), y su
      cadencia no sale del transcript porque no la dice nadie.
    · `reveal: True` — las filas entran apagadas y esperan un `OBJECT_STATE`
      con `reveal: "r<i>"`. Es lo que se usa cuando cada categoría CAE EN SU
      PALABRA, que es la regla dura del proyecto: nada entra antes de que se
      nombre.

    Una etiqueta vacía pinta una barra gris en vez de texto. Así el mismo
    documento sirve para «las respuestas que ya existen» —material en bruto,
    sin nombres todavía— y para el enunciado de categorías, sin adelantar el
    guion en el primer paso.
    """
    TR_BODY, TEXT = TR["body"], t.C["text"]
    labels = list(state.get("labels") or [])
    rows = int(state.get("rows", len(labels) or 6))
    labels += [""] * (rows - len(labels))
    reveal = bool(state.get("reveal", False))
    title = state.get("title", "BASE DE CONOCIMIENTO")
    seal = state.get("seal")

    # 980, no 880: MEDIDO. En la cabecera conviven el título y el sello, y a
    # 880 el ancho útil se queda en ~746 px para 370 + 370 — «BASE DE
    # CONOCIMIENTO» se partía en dos líneas justo cuando aparece «APROBADA POR
    # TU EMPRESA». A 980 el útil sube a ~848 y los dos caben en una línea, con
    # 50 px de margen a cada lado del lienzo.
    w = 980
    h = KB_PAD * 2 + KB_HEAD_H + rows * KB_ROW_H + (rows - 1) * KB_ROW_GAP
    x, y = t.SLOTS[slot]
    eid = f"{cid}-{iid}"

    # ⚠ EL ✓ VERDE SOLO VA EN UNA FILA CON NOMBRE. Un check junto a una barra
    # en bruto se lee como «esto ya está resuelto», que es exactamente lo
    # contrario del beat en que el documento aparece sin organizar. Es la misma
    # trampa que `flow_steps` ya documenta con «✓ junto a No hay stock».
    check = (f'<svg viewBox="0 0 24 24" width="24" height="24" '
             f'style="margin-left:auto;flex:0 0 auto">'
             f'<path d="M4 13 L9 18 L20 6" fill="none" stroke="{t.C["go"]}" '
             f'stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>'
             f'</svg>')
    icono = (f'<span style="width:26px;height:26px;border-radius:8px;'
             f'background:currentColor;opacity:.85;flex:0 0 auto"></span>')

    filas, anims = [], []
    for i, lab in enumerate(labels[:rows]):
        if lab:
            cuerpo = (f'<span style="font-family:{t.FONT};font-weight:600;'
                      f'font-size:{TR_BODY}px;color:{TEXT}">{lab}</span>' + check)
        else:
            cuerpo = (f'<span style="height:14px;width:{240 + (i * 53) % 190}px;'
                      f'border-radius:7px;background:{t.LINE_HI};display:block">'
                      f'</span>')
        # ⚠ QUÉ ENTRA EN CADA MODO, y no es un detalle de pulido.
        #
        # Con `reveal`, el HUECO se queda puesto y lo que aparece es su
        # CONTENIDO. Animando la fila entera, el panel conservaba su alto de
        # seis filas con solo cuatro visibles y el tercio de abajo quedaba
        # vacío DENTRO del marco: se lee como un panel roto, no como una lista
        # que se va llenando. Con los huecos puestos se lee como un formulario
        # rellenándose, que es el beat.
        #
        # Sin `reveal` la fila entera sí entra: ahí no hay nada que rellenar
        # —las barras SON el contenido— y un hueco vacío detrás de una barra
        # gris serían dos rectángulos grises sin jerarquía.
        contenido = (
            f'<span id="{eid}-r{i}" style="display:flex;align-items:center;'
            f'gap:20px;flex:1 1 auto;opacity:0">{icono}{cuerpo}</span>'
            if reveal else f"{icono}{cuerpo}")
        rid = "" if reveal else f' id="{eid}-r{i}"'
        filas.append(f"""
  <div{rid} style="height:{KB_ROW_H}px;box-sizing:border-box;
       display:flex;align-items:center;gap:20px;padding:0 22px;
       background:{t.C['surface2']};border:1px solid {t.LINE};
       border-radius:{t.RADIUS['md']}px;opacity:{1 if reveal else 0}">
    {contenido}
  </div>""")
        if not reveal:
            anims.append(("chip-in", f"#{eid}-r{i}", round(0.18 + i * 0.13, 4),
                          REVEAL_DURATION))

    seal_html = ""
    if seal:
        # Sobre relleno verde va tinta `bg`: bg/go = 11.74:1, blanco/go = 1.66:1.
        seal_html = (
            f'<span id="{eid}-seal" style="margin-left:auto;flex:0 0 auto;opacity:0;'
            f"font-family:{t.MONO};font-weight:700;font-size:{TR['chip'] - 4}px;"
            f"letter-spacing:.12em;background:{t.C['go']};color:{t.C['bg']};"
            f'border-radius:{t.RADIUS["pill"]}px;padding:10px 18px">{seal}</span>')

    html = f"""
<div class="obj accent" id="{eid}" {OBJ_ATTRS}
     style="left:{x - w // 2}px;top:{y - h // 2}px;width:{w}px;height:{h}px">
  <div style="width:100%;height:100%;box-sizing:border-box;padding:{KB_PAD}px;
       display:flex;flex-direction:column;gap:{KB_ROW_GAP}px;
       background:{t.C['surface']};border:1px solid {t.LINE_HI};
       border-radius:{t.RADIUS['xl']}px;box-shadow:{t.SHADOW}">
    <div style="height:{KB_HEAD_H}px;box-sizing:border-box;display:flex;
         align-items:center;gap:20px;padding:0 22px 0 4px;
         border-bottom:1px solid {t.LINE}">
      <svg viewBox="0 0 34 40" width="34" height="40" style="flex:0 0 auto">
        <path d="M4 2 H22 L30 10 V38 H4 Z" fill="{t.C['surface2']}"
              stroke="currentColor" stroke-width="2.6" stroke-linejoin="round"/>
        <path d="M22 2 V10 H30" fill="none" stroke="currentColor" stroke-width="2.6"
              stroke-linejoin="round"/>
        <path d="M10 20 h14 M10 28 h10" stroke="{t.LINE_HI}" stroke-width="3.4"
              stroke-linecap="round"/>
      </svg>
      <span style="font-family:{t.MONO};font-weight:700;font-size:{TR['chip']}px;
            letter-spacing:.16em;color:{t.C['text2']};white-space:nowrap">{title}</span>
      {seal_html}
    </div>{"".join(filas)}
  </div>
</div>"""
    return {"html": html, "anims": anims, "eid": eid}


def answer_approved(cid: str, iid: str, state: dict, slot: str = "foot", **_) -> dict:
    """La respuesta que sale del documento — el tercer bloque del flujo.

    Es el ÚNICO objeto de la librería con relleno verde, y por eso lleva el
    check dentro de una pastilla `go` con tinta `bg`. El texto de la
    respuesta se queda en blanco sobre `surface2`: teñir de verde toda la
    burbuja convertiría el mensaje en un banner de éxito de sistema en vez
    de en una respuesta a un cliente.
    """
    x, y = t.SLOTS[slot]
    w, h = int(state.get("w", 700)), 108
    eid = f"{cid}-{iid}"
    txt = state.get("text", "Respuesta enviada")
    html = f"""
<div class="obj accent" id="{eid}" {OBJ_ATTRS}
     style="left:{x - w // 2}px;top:{y - h // 2}px;width:{w}px;height:{h}px">
  <svg viewBox="0 0 40 46" width="40" height="46"
       style="position:absolute;left:{w // 2 - 20}px;top:-52px">
    <path d="M20 2 V30 M8 22 L20 34 L32 22" fill="none" stroke="currentColor"
          stroke-width="4" stroke-linecap="round" stroke-linejoin="round"
          opacity="0.75"/>
  </svg>
  <div style="width:100%;height:100%;box-sizing:border-box;display:flex;
       align-items:center;gap:20px;padding:0 28px;background:{t.C['surface2']};
       border:1px solid rgba(52,227,155,.42);border-radius:{t.RADIUS['lg']}px;
       box-shadow:{t.SHADOW}">
    <span style="width:44px;height:44px;border-radius:50%;background:{t.C['go']};
          display:flex;align-items:center;justify-content:center;flex:0 0 auto">
      <svg viewBox="0 0 24 24" width="26" height="26">
        <path d="M4 13 L9 18 L20 6" fill="none" stroke="{t.C['bg']}"
              stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </span>
    <span style="font-family:{t.FONT};font-weight:700;font-size:{TR['body']}px;
          color:{t.C['text']};white-space:nowrap">{txt}</span>
  </div>
</div>"""
    return {"html": html, "anims": [], "eid": eid}


# ── pieza 13 — la hora vacía, el silencio y la confirmación ──────────────────
# Tres objetos, no cinco: los mensajes de la secuencia se sirven con `msg-card`
# de la pieza 12 (§11, el Resolver prueba la LIBRERÍA antes de crear nada) y su
# `seal` verde carga la ventana de envío — INMEDIATA, DÍA ANTERIOR, 3 H ANTES.

# MEDIDO sobre frames, no elegido: con filas de 68 px el panel ocupaba el 28 %
# del alto y dejaba muerto todo lo de arriba de y620. A 84 px (y 120 la vacía)
# el bloque va de y528 a y1172 y la agenda pesa lo que tiene que pesar.
CAL_ROW_H = 84
CAL_EMPTY_H = 120
CAL_GAP = 10
CAL_HEAD_H = 96
CAL_PAD = 26
# El brief pide «texto grande» para HORA PERDIDA, y a 40 px se leía pero no
# dominaba. 52 px = TYPE.card_title, así que no inventa un tamaño nuevo.
CAL_LABEL_SIZE = 52


def calendar(cid: str, iid: str, state: dict, slot: str = "center", **_) -> dict:
    """La agenda del día con UNA franja vacía.

    Lo que comunica es la AUSENCIA, igual que `chat_unanswered` en la pieza 11:
    las demás franjas tienen nombre y esa no. Por eso la vacía no se dibuja como
    una fila más en rojo, sino como un HUECO — borde discontinuo, sin relleno —
    y encima es la más alta de la columna. Una fila roja con texto se leería
    como «esta cita tiene un problema»; un hueco se lee como «aquí no hay
    nadie», que es la frase.

    El rótulo va DENTRO del hueco y nace apagado: entra con
    `OBJECT_STATE {"reveal": "perdida"}` en la palabra que lo justifica. Tinta
    `alert` sobre el suelo del panel = 5.32:1, y a 40 px es de sobra.
    """
    rows = list(state.get("rows") or [])
    vacia = int(state.get("empty", 2))
    titulo = state.get("title", "AGENDA · MARTES")
    rotulo = state.get("label", "HORA PERDIDA")

    w = 880
    h = (CAL_PAD * 2 + CAL_HEAD_H + (len(rows) - 1) * CAL_ROW_H + CAL_EMPTY_H
         + (len(rows) - 1) * CAL_GAP)
    x, y = t.SLOTS[slot]
    eid = f"{cid}-{iid}"

    filas = []
    for i, (hora, quien) in enumerate(rows):
        if i == vacia:
            filas.append(f"""
  <div style="height:{CAL_EMPTY_H}px;box-sizing:border-box;display:flex;
       align-items:center;gap:22px;padding:0 22px;background:transparent;
       border:2px dashed {t.C['alert']};border-radius:{t.RADIUS['md']}px">
    <span style="font-family:{t.MONO};font-weight:700;font-size:{TR['chip']}px;
          letter-spacing:.10em;color:{t.C['alert']};flex:0 0 auto;
          width:112px">{hora}</span>
    <span id="{eid}-perdida" style="font-family:{t.FONT};font-weight:900;
          font-size:{CAL_LABEL_SIZE}px;letter-spacing:-.02em;
          color:{t.C['alert']};
          opacity:0">{rotulo}</span>
  </div>""")
        else:
            filas.append(f"""
  <div style="height:{CAL_ROW_H}px;box-sizing:border-box;display:flex;
       align-items:center;gap:22px;padding:0 22px;background:{t.C['surface2']};
       border:1px solid {t.LINE};border-radius:{t.RADIUS['md']}px">
    <span style="font-family:{t.MONO};font-weight:700;font-size:{TR['chip']}px;
          letter-spacing:.10em;color:{t.C['text3']};flex:0 0 auto;
          width:112px">{hora}</span>
    <span style="font-family:{t.FONT};font-weight:600;font-size:{TR['body']}px;
          color:{t.C['text']}">{quien}</span>
    <span style="margin-left:auto;width:12px;height:12px;border-radius:50%;
          background:{t.C['go']};flex:0 0 auto"></span>
  </div>""")

    html = f"""
<div class="obj accent" id="{eid}" {OBJ_ATTRS}
     style="left:{x - w // 2}px;top:{y - h // 2}px;width:{w}px;height:{h}px">
  <div style="width:100%;height:100%;box-sizing:border-box;padding:{CAL_PAD}px;
       display:flex;flex-direction:column;gap:{CAL_GAP}px;
       background:{t.C['surface']};border:1px solid {t.LINE_HI};
       border-radius:{t.RADIUS['xl']}px;box-shadow:{t.SHADOW}">
    <div style="height:{CAL_HEAD_H}px;box-sizing:border-box;display:flex;
         align-items:center;gap:18px;padding:0 22px 0 4px;
         border-bottom:1px solid {t.LINE}">
      <svg viewBox="0 0 36 36" width="36" height="36" style="flex:0 0 auto">
        <rect x="3" y="7" width="30" height="26" rx="5" fill="{t.C['surface2']}"
              stroke="currentColor" stroke-width="2.6"/>
        <path d="M3 15 H33" stroke="currentColor" stroke-width="2.6"/>
        <path d="M11 3 V9 M25 3 V9" stroke="currentColor" stroke-width="2.6"
              stroke-linecap="round"/>
      </svg>
      <span style="font-family:{t.MONO};font-weight:700;font-size:{TR['chip']}px;
            letter-spacing:.16em;color:{t.C['text2']};white-space:nowrap">{titulo}</span>
    </div>{"".join(filas)}
  </div>
</div>"""
    return {"html": html, "anims": [], "eid": eid}


def appointment_timeline(cid: str, iid: str, state: dict,
                         slot: str = "center", **_) -> dict:
    """La línea de tiempo entre la reserva y la cita, con el hueco en medio.

    VERTICAL, no horizontal, y por la misma razón que el rail de la pieza 12: en
    1080 de ancho, siete días repartidos en horizontal dejan cada parada en
    ~150 px y las etiquetas dejan de leerse. En vertical el eje del tiempo baja
    y cada parada tiene el ancho entero del panel.

    ⚠ CUATRO PARADAS, NO DOS. La primera versión tenía solo Reserva y Cita con
    un tramo discontinuo de 244 px en medio, y sobre frames eso NO se leía como
    días pasando: se leía como un panel a medio hacer. El hueco solo cuenta el
    tiempo si hay marcas que lo midan, así que los días intermedios entran como
    nodos huecos con su etiqueta y SIN evento — y esa ausencia de evento, junto
    a un día que sí existe, es exactamente la frase «nadie vuelve a escribirle».

    Los dos rótulos del medio nacen apagados (`span`, `silencio`) y el nodo
    final tiene un aro de alerta (`riesgo`) también apagado, así que el mismo
    objeto sirve para «agenda con anticipación» y para «nadie le escribe» sin
    reconstruirse — que es lo que permite que ese límite sea un
    OBJECT_MATCH_CUT y no un corte.
    """
    inicio = state.get("start") or ("DÍA 1", "Reserva")
    fin = state.get("end") or ("DÍA 7", "Cita")
    medios = state.get("middle") or ["DÍA 3", "DÍA 5"]
    span = state.get("span", "7 DÍAS DE ANTICIPACIÓN")
    silencio = state.get("silence", "SIN MENSAJES")
    titulo = state.get("title", "AGENDA DEL PACIENTE")

    ROW_H, HEAD_H, PAD = 118, 52, 28
    filas_n = 2 + len(medios)
    w = 820
    h = PAD * 2 + HEAD_H + filas_n * ROW_H
    x, y = t.SLOTS[slot]
    eid = f"{cid}-{iid}"

    # El raíl: una sola discontinua que atraviesa los centros de todos los
    # nodos. Va a `text3` y 3 px porque a `LINE_HI` (alpha .16) se perdía
    # contra el suelo del panel en el frame renderizado.
    rail_top = PAD + HEAD_H + ROW_H // 2
    rail_h = (filas_n - 1) * ROW_H
    rail = (f'<span style="position:absolute;left:{PAD + 46}px;top:{rail_top}px;'
            f'height:{rail_h}px;width:0;border-left:3px dashed {t.C["text3"]}">'
            f'</span>')

    CHIP = TR["chip"]

    def fila(dia, nodo, cuerpo):
        return f"""
  <div style="height:{ROW_H}px;box-sizing:border-box;display:flex;
       align-items:center;gap:22px">
    <span style="position:relative;width:34px;height:34px;flex:0 0 auto;
          display:flex;align-items:center;justify-content:center;
          background:{t.C['surface']};border-radius:50%">{nodo}</span>
    <span style="font-family:{t.MONO};font-weight:700;font-size:{CHIP}px;
          letter-spacing:.14em;color:{t.C['text3']};flex:0 0 auto;
          width:104px">{dia}</span>
    {cuerpo}
  </div>"""

    def evento(txt):
        return (f'<span style="font-family:{t.FONT};font-weight:700;'
                f'font-size:{TR["card_title"]}px;letter-spacing:-.02em;'
                f'color:{t.C["text"]}">{txt}</span>')

    def chip(sid, txt, alerta):
        color = t.C["alert"] if alerta else t.C["text2"]
        borde = (f'2px dashed {t.C["alert"]}' if alerta
                 else f'1px solid {t.LINE_HI}')
        fondo = "transparent" if alerta else t.C["surface2"]
        return (f'<span id="{eid}-{sid}" style="font-family:{t.MONO};'
                f'font-weight:700;font-size:{CHIP}px;letter-spacing:.12em;'
                f'color:{color};background:{fondo};border:{borde};'
                f'border-radius:{t.RADIUS["pill"]}px;padding:10px 20px;'
                f'opacity:0;white-space:nowrap">{txt}</span>')

    lleno = (f'<span style="width:26px;height:26px;border-radius:50%;'
             f'background:currentColor;border:3px solid currentColor;'
             f'box-sizing:border-box"></span>')
    hueco = (f'<span style="width:16px;height:16px;border-radius:50%;'
             f'background:{t.C["surface"]};border:3px solid {t.C["text3"]};'
             f'box-sizing:border-box"></span>')
    final = (f'<span style="width:26px;height:26px;border-radius:50%;'
             f'background:{t.C["surface2"]};border:3px solid currentColor;'
             f'box-sizing:border-box"></span>'
             f'<span id="{eid}-riesgo" style="position:absolute;left:-9px;'
             f'top:-9px;width:52px;height:52px;border-radius:50%;'
             f'border:3px solid {t.C["alert"]};opacity:0"></span>')

    # Los dos rótulos del medio cuelgan de los dos días intermedios: el que
    # mide el tramo y el que dice qué pasa dentro (nada).
    cuerpos = [chip("span", span, False), chip("silencio", silencio, True)]
    filas = [fila(inicio[0], lleno, evento(inicio[1]))]
    for i, dia in enumerate(medios):
        filas.append(fila(dia, hueco,
                          cuerpos[i] if i < len(cuerpos) else ""))
    filas.append(fila(fin[0], final, evento(fin[1])))

    html = f"""
<div class="obj accent" id="{eid}" {OBJ_ATTRS}
     style="left:{x - w // 2}px;top:{y - h // 2}px;width:{w}px;height:{h}px">
  <div style="position:relative;width:100%;height:100%;box-sizing:border-box;
       padding:{PAD}px 30px;display:flex;flex-direction:column;
       background:{t.C['surface']};border:1px solid {t.LINE_HI};
       border-radius:{t.RADIUS['xl']}px;box-shadow:{t.SHADOW}">
    {rail}
    <span style="height:{HEAD_H}px;font-family:{t.MONO};font-weight:700;
          font-size:{CHIP}px;letter-spacing:.16em;color:{t.C['text2']};
          white-space:nowrap">{titulo}</span>{"".join(filas)}
  </div>
</div>"""
    return {"html": html, "anims": [], "eid": eid}


def confirm_buttons(cid: str, iid: str, state: dict, slot: str = "stack-3",
                    **_) -> dict:
    """Los dos botones de la respuesta del paciente.

    El PRIMARIO lleva relleno verde y tinta `bg` (11.74:1; blanco sobre verde
    da 1.66:1 y es la regla que ya está escrita); el secundario se queda en
    superficie con filete. Dos botones al mismo peso no son una decisión: son
    dos opciones, y el paciente tiene que ver cuál es la que se espera.

    El check nace apagado y entra con `reveal: "check"`, así que el «tap» cae
    en su palabra y no en un tiempo inventado.
    """
    primario = state.get("primary", "CONFIRMAR")
    secundario = state.get("secondary", "REPROGRAMAR")
    w, h = int(state.get("w", 760)), 120
    x, y = t.SLOTS[slot]
    eid = f"{cid}-{iid}"
    html = f"""
<div class="obj accent" id="{eid}" {OBJ_ATTRS}
     style="left:{x - w // 2}px;top:{y - h // 2}px;width:{w}px;height:{h}px">
  <div style="width:100%;height:100%;box-sizing:border-box;display:flex;
       align-items:center;gap:18px">
    <span style="flex:1 1 0;height:100%;box-sizing:border-box;display:flex;
          align-items:center;justify-content:center;gap:14px;
          background:{t.C['go']};border-radius:{t.RADIUS['lg']}px;
          box-shadow:0 14px 40px rgba(52,227,155,.24)">
      <span id="{eid}-check" style="width:34px;height:34px;flex:0 0 auto;
            opacity:0">
        <svg viewBox="0 0 24 24" width="34" height="34">
          <path d="M4 13 L9 18 L20 6" fill="none" stroke="{t.C['bg']}"
                stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </span>
      <span style="font-family:{t.FONT};font-weight:900;
            font-size:{TR['card_title'] - 6}px;letter-spacing:-.01em;
            color:{t.C['bg']}">{primario}</span>
    </span>
    <span style="flex:1 1 0;height:100%;box-sizing:border-box;display:flex;
          align-items:center;justify-content:center;background:{t.C['surface2']};
          border:1px solid {t.LINE_HI};border-radius:{t.RADIUS['lg']}px">
      <span style="font-family:{t.FONT};font-weight:700;
            font-size:{TR['card_title'] - 10}px;letter-spacing:-.01em;
            color:{t.C['text2']}">{secundario}</span>
    </span>
  </div>
</div>"""
    return {"html": html, "anims": [], "eid": eid}


# ── pieza 14 ────────────────────────────────────────────────────────────────
SS_ROW_H = 44
SS_GAP = 8
SS_HEAD_H = 96
SS_COLHEAD_H = 46
SS_PAD = 26
SS_ROWS = 11
SS_COLS = 4
# El interrogante es un TITULAR, no un adorno: sale de la escala (display).
SS_Q_SIZE = TR["display"]


def spreadsheet(cid: str, iid: str, state: dict, slot: str = "center", **_) -> dict:
    """La hoja de cálculo llena de filas — el problema de la pieza 14.

    ES UNA REJILLA, NO UNA LISTA, y esa es toda la diferencia con
    `knowledge-base`. El documento de la pieza 12 apila filas y comunica
    «esto existe suelto»; aquí hacen falta COLUMNAS con separadores, porque
    lo que se dice es «una hoja con cientos de filas» y una columna de barras
    grises se lee como una lista de pendientes, no como un Excel.

    Las barras son deterministas (`(i * 37 + j * 53) % 41`): un golden file no
    puede depender de un `random`, y de todas formas el dato concreto no es el
    argumento — el VOLUMEN lo es.

    Tres cosas nacen apagadas y entran cada una en su palabra:

    · `conteo`  — la pastilla «1.284 FILAS» en la cabecera, en «cientos».
    · `valiosa` — UNA celda que deja de ser barra gris y pasa a ser una cifra
      legible, en «valiosa». Es una entre 44: el beat no es que el dato exista,
      es que está enterrado, y por eso la celda se enciende sola y el resto de
      la rejilla se queda igual.
    · `preguntas` — los tres interrogantes alrededor del panel, en
      «manualmente». Van en `currentColor`, así que los tiñe el tema del stage
      (`problem` -> alert) en vez de traer un color propio que habría que
      volver a justificar.
    """
    titulo = state.get("title", "VENTAS_ENERO.XLSX")
    cols = list(state.get("cols") or ["FECHA", "SUCURSAL", "PRODUCTO", "TOTAL"])
    filas_n = int(state.get("rows", SS_ROWS))
    conteo = state.get("count", "1.284 FILAS")
    celda = state.get("value", "+38%")
    # La celda que se enciende, en coordenadas de la rejilla. Por defecto cae
    # en el medio: una fila de arriba se leería como la primera y una de abajo
    # como la última, y lo que se quiere decir es «una cualquiera».
    vr, vc = state.get("at", (6, 2))

    w = 860
    h = (SS_PAD * 2 + SS_HEAD_H + SS_COLHEAD_H + filas_n * SS_ROW_H
         + (filas_n + 1) * SS_GAP)
    x, y = t.SLOTS[slot]
    eid = f"{cid}-{iid}"

    cab = "".join(
        f'<span style="flex:1 1 0;padding:0 18px;font-family:{t.MONO};'
        f'font-weight:700;font-size:{TR["chip"] - 4}px;letter-spacing:.14em;'
        f'color:{t.C["text3"]};'
        f'{"border-left:1px solid " + t.LINE if j else ""}">{c}</span>'
        for j, c in enumerate(cols))

    filas = []
    for i in range(filas_n):
        celdas = []
        for j in range(len(cols)):
            borde = f"border-left:1px solid {t.LINE};" if j else ""
            if i == vr and j == vc:
                # La barra sigue puesta debajo: lo que entra es la cifra
                # ENCIMA, no una celda nueva. Quitar la barra dejaría un hueco
                # en la rejilla durante los segundos previos a su palabra.
                celdas.append(
                    f'<span style="flex:1 1 0;position:relative;padding:0 18px;'
                    f'display:flex;align-items:center;{borde}">'
                    f'<span style="height:12px;width:{46 + (i * 37 + j * 53) % 41}%;'
                    f'border-radius:6px;background:{t.LINE_HI};display:block">'
                    f'</span>'
                    f'<span id="{eid}-valiosa" style="position:absolute;'
                    f'left:10px;right:10px;top:-5px;bottom:-5px;opacity:0;'
                    f'display:flex;align-items:center;justify-content:center;'
                    f'background:{t.C["accent_pill"]};border:1px solid {t.C["accent_hi"]};'
                    f'border-radius:{t.RADIUS["sm"]}px;font-family:{t.MONO};'
                    f'font-weight:700;font-size:{TR["chip"]}px;'
                    f'color:{t.C["text"]}">{celda}</span></span>')
            else:
                celdas.append(
                    f'<span style="flex:1 1 0;padding:0 18px;display:flex;'
                    f'align-items:center;{borde}">'
                    f'<span style="height:12px;width:{46 + (i * 37 + j * 53) % 41}%;'
                    f'border-radius:6px;background:{t.LINE_HI};display:block">'
                    f'</span></span>')
        filas.append(
            f'<div style="height:{SS_ROW_H}px;box-sizing:border-box;display:flex;'
            f'align-items:center;background:{t.C["surface2"]};'
            f'border:1px solid {t.LINE};border-radius:{t.RADIUS["sm"]}px">'
            f'{"".join(celdas)}</div>')

    # Tres interrogantes ALREDEDOR, no encima: el panel se sigue leyendo y lo
    # que cambia es que ahora nadie sabe qué mirar.
    qs = "".join(
        f'<span style="position:absolute;left:{lx}px;top:{ty}px;'
        f'font-family:{t.FONT};font-weight:900;font-size:{SS_Q_SIZE}px;'
        f'line-height:1;color:currentColor;opacity:.92">?</span>'
        for lx, ty in ((-96, 24), (w - 26, 246), (-68, h - 214)))

    html = f"""
<div class="obj accent" id="{eid}" {OBJ_ATTRS}
     style="left:{x - w // 2}px;top:{y - h // 2}px;width:{w}px;height:{h}px">
  <div style="width:100%;height:100%;box-sizing:border-box;padding:{SS_PAD}px;
       display:flex;flex-direction:column;gap:{SS_GAP}px;
       background:{t.C['surface']};border:1px solid {t.LINE_HI};
       border-radius:{t.RADIUS['xl']}px;box-shadow:{t.SHADOW}">
    <div style="height:{SS_HEAD_H}px;box-sizing:border-box;display:flex;
         align-items:center;gap:18px;padding:0 22px 0 4px;
         border-bottom:1px solid {t.LINE}">
      <svg viewBox="0 0 34 40" width="34" height="40" style="flex:0 0 auto">
        <path d="M4 2 H22 L30 10 V38 H4 Z" fill="{t.C['surface2']}"
              stroke="{t.C['excel']}" stroke-width="2.6" stroke-linejoin="round"/>
        <path d="M22 2 V10 H30" fill="none" stroke="{t.C['excel']}"
              stroke-width="2.6" stroke-linejoin="round"/>
        <path d="M11 19 L23 31 M23 19 L11 31" stroke="{t.C['excel']}"
              stroke-width="3" stroke-linecap="round"/>
      </svg>
      <span style="font-family:{t.MONO};font-weight:700;font-size:{TR['chip']}px;
            letter-spacing:.16em;color:{t.C['text2']};white-space:nowrap">{titulo}</span>
      <span id="{eid}-conteo" style="margin-left:auto;flex:0 0 auto;opacity:0;
            font-family:{t.MONO};font-weight:700;font-size:{TR['chip'] - 4}px;
            letter-spacing:.12em;background:{t.C['surface3']};color:{t.C['text']};
            border-radius:{t.RADIUS['pill']}px;padding:8px 18px">{conteo}</span>
    </div>
    <div style="height:{SS_COLHEAD_H}px;box-sizing:border-box;display:flex;
         align-items:center">{cab}</div>
    {"".join(filas)}
  </div>
  <div id="{eid}-preguntas" style="position:absolute;inset:0;opacity:0">{qs}</div>
</div>"""
    return {"html": html, "anims": [], "eid": eid}


KPI_CARD_H = 146


def kpi_card(cid: str, iid: str, state: dict, slot: str = "stack-1", **_) -> dict:
    """El indicador: una PREGUNTA, su cifra y la decisión que provoca.

    Es el objeto que sostiene la tesis de la pieza, y por eso lleva las tres
    cosas en la misma tarjeta: sin la pregunta arriba es un número suelto —
    justo lo que el reel dice que no sirve—, y sin la pastilla de la derecha
    es un dashboard más.

    LA PASTILLA ES VERDE EN LAS CUATRO, y no es descuido. Teñir «REVISAR» de
    ámbar y «REPONER» de rojo convertiría la serie en un semáforo de estados,
    que es otra frase: lo que se afirma es que CADA indicador produce una
    decisión, y lo que tienen en común esas cuatro palabras es que son
    accionables, no su gravedad. Sobre relleno `go` va tinta `bg` (11.74:1),
    nunca blanco (1.66:1) — la misma regla que `msg-card`.

    La pastilla nace apagada y entra con `OBJECT_STATE {"reveal": "accion"}`:
    el dato se enseña cuando se nombra y la decisión cuando toca, que es lo
    que deja ver que una sale de la otra.
    """
    x, y = t.SLOTS[slot]
    w = int(state.get("w", 920))
    h = KPI_CARD_H
    eid = f"{cid}-{iid}"
    pregunta = state.get("q", "")
    valor = state.get("value", "")
    accion = state.get("action")

    accion_html = ""
    if accion:
        accion_html = (
            f'<span id="{eid}-accion" style="flex:0 0 auto;opacity:0;'
            f"font-family:{t.MONO};font-weight:700;font-size:{TR['chip'] - 4}px;"
            f"letter-spacing:.12em;background:{t.C['go']};color:{t.C['bg']};"
            f'border-radius:{t.RADIUS["pill"]}px;padding:12px 22px">{accion}</span>')

    # La flecha es ESTÁTICA y vive fuera del bloque de texto: el contenedor
    # entra por opacidad y lo que se mueve es su contenido, así que un trazo
    # que solo dice «esto lleva a esto» no necesita animarse para pertenecer
    # al frame. Misma decisión que la flecha de `msg-card`.
    flecha = (f'<svg viewBox="0 0 46 24" width="46" height="24" '
              f'style="flex:0 0 auto;opacity:.75">'
              f'<path d="M2 12 H40 M30 3 L41 12 L30 21" fill="none" '
              f'stroke="currentColor" stroke-width="3.2" stroke-linecap="round" '
              f'stroke-linejoin="round"/></svg>')

    html = f"""
<div class="obj accent" id="{eid}" {OBJ_ATTRS}
     style="left:{x - w // 2}px;top:{y - h // 2}px;width:{w}px;height:{h}px">
  <div style="width:100%;height:100%;box-sizing:border-box;display:flex;
       align-items:center;gap:22px;padding:0 30px;background:{t.C['surface2']};
       border:1px solid {t.LINE_HI};border-radius:{t.RADIUS['lg']}px;
       box-shadow:{t.SHADOW}">
    <div style="display:flex;flex-direction:column;gap:10px;flex:1 1 auto;
         min-width:0">
      <span style="font-family:{t.MONO};font-weight:700;
            font-size:{TR['chip'] - 4}px;letter-spacing:.12em;
            color:{t.C['text2']};white-space:nowrap">{pregunta}</span>
      <span style="font-family:{t.FONT};font-weight:800;font-size:{TR['body']}px;
            letter-spacing:-.01em;color:{t.C['text']};
            white-space:nowrap">{valor}</span>
    </div>
    {flecha}
    {accion_html}
  </div>
</div>"""
    return {"html": html, "anims": [], "eid": eid}


# Las CLAVES son el nombre del asset tal como lo escribe el EDL
# (`object:dental-chair@1` -> kind `dental-chair`): `ASSET_RE` en
# `edl_schema.py` solo admite `[a-z0-9-]+`, así que un asset de dos palabras
# es kebab-case, nunca snake_case. Las FUNCIONES de Python siguen su propia
# convención (`dental_chair`, guion bajo) porque un identificador no puede
# llevar guiones — dos namespaces distintos, unidos aquí a propósito.
REGISTRY = {"motion_stage": motion_stage, "clock": clock,
           "dental-chair": dental_chair, "phone": phone,
           "card-payment": card_payment, "instagram": instagram,
           "bottleneck": bottleneck, "msg-card": msg_card,
           "answer-counter": answer_counter,
           "knowledge-base": knowledge_base,
           "answer-approved": answer_approved,
           "calendar": calendar,
           "appointment-timeline": appointment_timeline,
           "confirm-buttons": confirm_buttons,
           "spreadsheet": spreadsheet,
           "kpi-card": kpi_card}
