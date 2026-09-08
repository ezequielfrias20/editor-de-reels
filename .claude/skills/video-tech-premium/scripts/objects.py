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
        anims.extend(r.get("anims", []))
        eid_of[od["id"]] = r["eid"]
        anims.append(("scale-pop", f"#{r['eid']}", od["in"] - visual_start,
                      OBJECT_ENTRANCE_DURATION))

    cuerpo = "".join(cuerpo_partes)
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
    <circle cx="150" cy="150" r="10" fill="{t.C['violet']}"/>
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


# Las CLAVES son el nombre del asset tal como lo escribe el EDL
# (`object:dental-chair@1` -> kind `dental-chair`): `ASSET_RE` en
# `edl_schema.py` solo admite `[a-z0-9-]+`, así que un asset de dos palabras
# es kebab-case, nunca snake_case. Las FUNCIONES de Python siguen su propia
# convención (`dental_chair`, guion bajo) porque un identificador no puede
# llevar guiones — dos namespaces distintos, unidos aquí a propósito.
REGISTRY = {"motion_stage": motion_stage, "clock": clock,
           "dental-chair": dental_chair, "phone": phone,
           "card-payment": card_payment, "instagram": instagram}
