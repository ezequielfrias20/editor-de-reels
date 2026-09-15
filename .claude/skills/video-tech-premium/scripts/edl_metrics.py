#!/usr/bin/env python3
"""Métricas de estilo y motor genérico de gates.

LA SEPARACIÓN QUE IMPORTA: aquí se CALCULAN métricas — una lista fija y
cerrada, en código. Los UMBRALES y la SEVERIDAD viven en `styles/*.json`.
Un perfil nuevo es un archivo nuevo y cero líneas de este módulo.
"""
from __future__ import annotations

from dataclasses import dataclass

from edl_schema import Edl, derive_stages, segment_windows

FPS = 30


def q(t: float) -> float:
    """Cuantiza a frame y recorta a 4 decimales.

    Copia literal de `edl_compile.py`/`build-composition.py`. El punto de
    cuantización es por MÓDULO, a propósito (cada uno lo necesita sin crear
    un import cruzado) — lo que no puede pasar es que dos rutas hagan
    aritmética de redondeo DISTINTA para el mismo instante.
    """
    return round(round(float(t) * FPS) / FPS, 4)


# Un cambio macro es un cambio de MUNDO; uno micro, de lectura.
MACRO_EVENTS = frozenset({"CAMERA", "OBJECT_IN", "OBJECT_EXIT", "OBJECT_STATE",
                          "STAGE_CLEAR", "THEME_CHANGE", "TYPE_BEAT", "UI_ACTION",
                          "CARD"})
MICRO_EVENTS = frozenset({"CAPTION", "KEYWORD"})
# SFX no cuenta en ninguno: no es un cambio visual.

PRESENTER_TYPES = frozenset({"A_ROLL", "A_ROLL_ICON", "CTA"})

DECORATIVE = ("mantener la atención", "dar dinamismo", "que no sea aburrido",
              "rellenar", "para que se vea bien", "dinamismo")


@dataclass(frozen=True)
class Finding:
    metric: str
    severity: str          # "fail" | "warn"
    message: str


def _beats(edl: Edl, windows, kinds: frozenset) -> list[float]:
    """Instantes de cambio visual, más los límites de segmento (SCENE).

    Los límites de SCENE son los de `segment_windows` — la MISMA ventana
    activa que usa `_shots()` — para que "cambio de plano" signifique lo mismo
    aquí que en lo que de verdad se emite.
    """
    ts = [0.0]
    for (start, _end), seg in zip(windows, edl.segments):
        ts.append(start)                      # SCENE: el límite es macro y micro
        for ev in seg.events:
            if ev.type in kinds:
                ts.append(ev.t(edl.wt))
    ts.append(edl.wt.duration)
    return sorted(ts)


def _max_gap(edl: Edl, windows, kinds: frozenset) -> float:
    """Hueco mayor, saltando los segmentos con `hold` autorizado.

    El hold se mide sobre la VENTANA del segmento, no sobre el span de sus
    palabras: la ventana es lo que de verdad cubre en pantalla, silencios
    incluidos.
    """
    holds = [w for w, seg in zip(windows, edl.segments) if seg.hold]
    ts = _beats(edl, windows, kinds)
    peor = 0.0
    for a, b in zip(ts, ts[1:]):
        if any(ha <= a and b <= hb for ha, hb in holds):
            continue
        peor = max(peor, b - a)
    return round(peor, 4)


def _camera_changes(edl: Edl, windows) -> list[float]:
    """Instantes en que la cámara CAMBIA de verdad.

    No es lo mismo que los encuadres que emite `_shots()`: ese emite una
    entrada por segmento aunque el plano sea el mismo que el anterior, porque
    le sale más barato que razonar sobre continuidad. Aquí un plano que se
    repite no es un cambio, y `OFF` sí lo es — entrar a un stage y volver son
    los dos cambios de imagen que el espectador lee como corte.

    Se usa el inicio CRUDO de la ventana, no el desplazado por `fade_in` /
    `fade_out` del relevo con el stage: ese ajuste es un ahorro de
    decodificación de ±0.2 s, no un corte que nadie percibe como tal.
    """
    ts: list[float] = []
    prev = None
    for (start, _end), seg in zip(windows, edl.segments):
        if seg.camera != prev:
            ts.append(start)
            prev = seg.camera
        for ev in sorted(seg.events, key=lambda e: e.at_word):
            if ev.type == "CAMERA":
                cam = ev.state.get("camera") or ev.theme or "MEDIUM"
                if cam != prev:
                    ts.append(ev.t(edl.wt))
                    prev = cam
    return ts


def _min_camera_gap(edl: Edl, windows, hook_exempt_until: float) -> float:
    """El hueco MENOR entre dos cambios de cámara. Por debajo de ~0.7 s deja
    de leerse como jump cut multicámara y se lee como jitter.

    El hook está exento: en los primeros segundos el atropello de planos es
    justo el efecto que se busca, y medirlo con la misma regla que el cuerpo
    obligaría a abrir la pieza con calma.

    Sin un segundo cambio no hay hueco que medir, y el valor de reserva es la
    DURACIÓN, no cero: cero dispararía el gate al revés y convertiría «esta
    pieza es de un solo plano» en «esta pieza tiembla».
    """
    ts = _camera_changes(edl, windows)
    peor = edl.wt.duration
    for a, b in zip(ts, ts[1:]):
        if b <= hook_exempt_until:
            continue
        peor = min(peor, b - a)
    return round(peor, 4)


def bare_stage_gaps(edl: Edl, fade_in: float) -> list[tuple[str, float]]:
    """Cuánto tiempo está cada stage EN PANTALLA SIN NINGÚN OBJETO.

    Es la hermana de `check_no_black()` y nace del mismo tipo de fallo, con la
    diferencia que lo hacía invisible: el frame no cae a negro, porque el suelo
    del stage SÍ se pinta —con su viñeta y su retícula—, así que ninguna
    comprobación existente lo veía. Lo que se ve es un fondo grafito vacío con
    un subtítulo encima, y eso se lee como un error de montaje.

    Medido cuando esta función se escribió: **1.63 s** en el stage de la
    secuencia de la pieza 13 y **0.97 s** en el de su línea de tiempo; y, ya
    entregada, **0.90 / 1.38 / 0.74 s** en los tres stages de la pieza 10.

    El arreglo es mover el LÍMITE del segmento, no el evento: la ventana de un
    segmento empieza en su primera palabra, así que hacer que el stage empiece
    en la palabra del objeto cierra el hueco sin adelantar el guion.

    El margen es el `fade_in` del stage —mientras el fondo se funde no hay nada
    que se lea como vacío— MÁS UN FRAME, porque el compilador cuantiza cada
    instante con `q()` y por debajo de 1/30 s no hay nada que ver.
    """
    margen = fade_in + 1.0 / FPS
    windows = segment_windows(edl.segments, edl.wt)
    fuera: list[tuple[str, float]] = []
    for stage in derive_stages(edl.segments):
        eventos = []
        for si in range(stage.first, stage.last + 1):
            eventos.extend(sorted(edl.segments[si].events, key=lambda e: e.at_word))
        donde = f"stage {stage.first}-{stage.last}"
        entradas = [e for e in eventos if e.type == "OBJECT_IN"]
        if not entradas:
            fuera.append((f"{donde} (sin un solo objeto)",
                          windows[stage.last][1] - windows[stage.first][0]))
            continue
        hueco = min(e.t(edl.wt) for e in entradas) - windows[stage.first][0]
        if hueco > margen:
            fuera.append((f"{donde} (al entrar)", round(hueco, 3)))
        # Y por el otro lado: retirar todo lo vivo a mitad de stage deja el
        # mismo fondo desnudo hasta que el stage termine.
        vivas, vaciado = set(), None
        for e in eventos:
            if e.type == "OBJECT_IN":
                vivas.add(e.instance_id); vaciado = None
            elif e.type == "OBJECT_EXIT":
                vivas.discard(e.instance_id)
                if not vivas:
                    vaciado = e.t(edl.wt)
            elif e.type == "STAGE_CLEAR":
                vivas.clear(); vaciado = e.t(edl.wt)
        if vaciado is not None and windows[stage.last][1] - vaciado > margen:
            fuera.append((f"{donde} (al salir)",
                          round(windows[stage.last][1] - vaciado, 3)))
    return fuera


def measure(edl: Edl, style: dict | None = None) -> dict[str, float]:
    """La lista FIJA de métricas. Añadir una es tocar código, a propósito.

    `style` es opcional y NO trae umbrales — esos siguen siendo del perfil y
    los aplica `run_gates()`. Lo único que aporta es la VENTANA del hook, que
    es un dato de encuadre del cálculo, no un límite: sin él, `min_camera_gap`
    se mide sobre la pieza entera.
    """
    total = edl.wt.duration
    windows = segment_windows(edl.segments, edl.wt)
    hook = float((style or {}).get("camera", {}).get("hook_exempt_until", 0.0))

    # POR QUÉ VENTANAS Y NO EL SPAN DE PALABRAS: el span deja fuera las
    # pausas entre frases, pero el presentador sigue en pantalla durante esas
    # pausas — el plano no cambia hasta que empieza el siguiente segmento. Con
    # el span, una pieza toda A_ROLL daba presenter_share ≈ 0.91 en vez de 1.0.
    dur = {}
    for (a, b), seg in zip(windows, edl.segments):
        dur[seg.scene_type] = dur.get(seg.scene_type, 0.0) + (b - a)

    presenter = sum(v for k, v in dur.items() if k in PRESENTER_TYPES)
    ui = dur.get("UI_DEMO", 0.0)
    # `exclude_ui_demo`: la demostración de producto sale del denominador.
    ajustado = total - ui

    macro = sum(1 for s in edl.segments for e in s.events if e.type in MACRO_EVENTS)
    sfx = sum(1 for s in edl.segments for e in s.events if e.type == "SFX")
    especiales = sum(1 for s in edl.segments if s.transition_in != "CUT")
    limites = max(1, len(edl.segments) - 1)

    # `sfx_declarations` es TODO lo que declara `sfx:"auto"` o un nombre
    # explícito — el mecanismo real que usa la pieza, distinto de `sfx` de
    # arriba (que solo cuenta el tipo de evento dedicado `SFX`, la escotilla
    # para un sonido sin evento visual detrás). `sfx_dropped` es cuánto de
    # eso se queda por el camino en `resolve_sfx()`: el colapso de iguales y
    # la concurrencia entre clases.
    desnudos = bare_stage_gaps(
        edl, float((style or {}).get("stage", {}).get("fade_in", 0.22)))

    declarados = sfx_declarations(edl)
    sobreviven = resolve_sfx(declarados)
    sfx_dropped = len(declarados) - len(sobreviven)

    return {
        "presenter_share": round(presenter / ajustado, 4) if ajustado > 0 else 0.0,
        "presenter_share_raw": round(presenter / total, 4) if total > 0 else 0.0,
        "max_micro_gap": _max_gap(edl, windows, MACRO_EVENTS | MICRO_EVENTS),
        "max_macro_gap": _max_gap(edl, windows, MACRO_EVENTS),
        "punch_zoom_count": sum(
            1 for s in edl.segments for e in s.events
            if e.type == "CAMERA" and e.preset == "punch-zoom"),
        "theme_change_count": sum(
            1 for s in edl.segments for e in s.events if e.type == "THEME_CHANGE"),
        "mega_count": sum(
            1 for s in edl.segments for e in s.events
            if e.type == "TYPE_BEAT" and "mega" in (e.roles or {}).values()),
        "special_transition_ratio": round(especiales / limites, 4),
        "sfx_per_macro": round(sfx / macro, 4) if macro else 0.0,
        "decorative_reason_count": sum(
            1 for s in edl.segments
            if any(d in s.reason.lower() for d in DECORATIVE)),
        "min_camera_gap": _min_camera_gap(edl, windows, hook),
        "stage_count": float(len(derive_stages(edl.segments))),
        "segment_count": float(len(edl.segments)),
        "sfx_dropped": float(sfx_dropped),
        # El PEOR hueco de suelo desnudo. 0.0 significa que ningún stage está
        # en pantalla sin objetos — ver `bare_stage_gaps`.
        "max_bare_stage": round(max((g for _, g in desnudos), default=0.0), 4),
    }


def run_gates(metrics: dict, style: dict) -> list[Finding]:
    out: list[Finding] = []
    for g in style.get("gates", []):
        name = g["metric"]
        if name not in metrics:
            raise KeyError(
                f"el perfil declara un gate sobre '{name}', que no es una métrica "
                f"calculada. Disponibles: {sorted(metrics)}")
        v = metrics[name]

        if "max" in g and v > g["max"]:
            out.append(Finding(name, g.get("severity", "warn"),
                               f"{name} = {v} supera el máximo {g['max']}"))
        if "min" in g and v < g["min"]:
            out.append(Finding(name, g.get("severity", "warn"),
                               f"{name} = {v} no llega al mínimo {g['min']}"))
        if "in" in g:
            lo, hi = g["in"]
            if not (lo <= v <= hi):
                fl, fh = g.get("fail_in", (float("-inf"), float("inf")))
                wl, wh = g.get("warn_in", g["in"])
                sev = "fail" if not (fl <= v <= fh) else (
                    "warn" if not (wl <= v <= wh) else "warn")
                out.append(Finding(name, sev,
                                   f"{name} = {v} fuera de la banda objetivo [{lo}, {hi}]"))
    return out


# ── SFX: opt-in, colapso y concurrencia (Tarea 10) ──────────────────────────
# Cada preset trae su efecto, pero SOLO suena si el evento declara sfx:"auto".
# `do not add SFX to every animation` como comportamiento por defecto, no
# como disciplina que hay que recordar en cada EDL.
PRESET_SFX = {"float-in": "pop", "drop-in": "impact-bass-2",
             "slide-blur": "whoosh-short", "hands-sweep": "whoosh-short",
             "crowd-in": "impact-bass-1", "type-beat": "key-press",
             "punch": "impact-bass-1", "box-in": "click"}

# Clase 1 gana a clase 4. El orden sale del peso narrativo, no del volumen:
# un impacto SIGNIFICA algo (el mundo cambió), un adorno solo decora.
PRIORITY = {"impact-bass-1": 1, "impact-bass-2": 1, "error": 1,
           "whoosh": 2, "whoosh-short": 2, "whoosh-cinematic": 2, "riser": 2,
           "click": 3, "click-soft": 3, "key-press": 3, "pop": 3, "typing": 3,
           "chime": 4, "sparkle": 4, "ping": 4, "notification": 4}

COLLAPSE_SAME = 0.25
CONCURRENCY = 0.18


def sfx_declarations(edl: Edl) -> list[dict]:
    """Todo evento que declara sonido — de cualquier tipo (`CAMERA`,
    `OBJECT_IN`, `OBJECT_STATE`, `KEYWORD`, o el tipo dedicado `SFX`), en
    cualquier segmento — traducido a lo que `resolve_sfx()` necesita.

    `preset` sale del evento y, si no trae uno, del `defaultPreset` del
    segmento — el mismo fallback que usa la interpretación visual del stage.
    `why` no es un campo del `Event` (no hay dónde escribirlo aparte): la
    intención del SEGMENTO que lo contiene ya describe con qué beat va ese
    sonido, así que sirve de sobra como comentario en el HTML.
    """
    out = []
    for seg in edl.segments:
        for ev in seg.events:
            if not ev.sfx:
                continue
            out.append({"t": ev.t(edl.wt), "sfx": ev.sfx,
                       "preset": ev.preset or seg.default_preset,
                       "trim": ev.trim, "why": seg.semantic_intent})
    return out


def resolve_sfx(events) -> list[tuple[float, str, float, str]]:
    """`events`: dicts `{t, sfx, preset?, trim?, why?}` — la forma que da
    `sfx_declarations()`, pero la función es pura y no exige un `Edl`: los
    tests del motor de colapso/concurrencia construyen la lista a mano.

    `sfx` en `None` es silencio — la palanca del opt-in. `sfx == "auto"`
    busca el efecto del `preset` en `PRESET_SFX`; cualquier otro string ES
    el nombre del efecto, sin pasar por el preset (el tipo dedicado `SFX`
    y los tests de concurrencia lo usan así).

    Dos reglas, en ORDEN — no son la misma regla con distinto umbral:

    1. Iguales dentro de `COLLAPSE_SAME` (250 ms) colapsan en uno — el
       primero, no el último: cuatro `OBJECT_IN` con `pop` en 2.3 s tienen
       que sonar a algo que EMPIEZA a crecer, no a un eco tardío.
    2. Distintos dentro de `CONCURRENCY` (180 ms) dejan solo el de la clase
       más alta (número de prioridad más bajo) — impact + whoosh + pop casi
       simultáneos son una metralleta sonora, no tres capas.

    Devuelve tuplas `(q(t), nombre, trim, why)` en el mismo orden que
    `build_sfx()` desempaqueta — `for start, name, trim, why in sorted(SFX)`.
    """
    resolved: list[dict] = []
    for e in events:
        sfx = e.get("sfx")
        if not sfx:
            continue
        if sfx == "auto":
            preset = e.get("preset")
            if preset not in PRESET_SFX:
                raise KeyError(
                    f"sfx:\"auto\" sobre un preset sin efecto por defecto "
                    f"({preset!r}); hay {sorted(PRESET_SFX)}")
            name = PRESET_SFX[preset]
        else:
            name = sfx
        resolved.append({"t": q(float(e["t"])), "name": name,
                        "trim": float(e.get("trim", 1.0)),
                        "why": e.get("why", "")})
    # Orden estable por tiempo: a igualdad de instante, la prioridad decide
    # cuál se procesa primero, así que un impacto simultáneo con un pop
    # nunca depende de en qué orden llegaron en la lista de entrada.
    resolved.sort(key=lambda r: (r["t"], PRIORITY.get(r["name"], 99)))

    kept: list[dict] = []
    for r in resolved:
        if any(k["name"] == r["name"] and abs(r["t"] - k["t"]) < COLLAPSE_SAME
              for k in kept):
            continue
        rivals = [i for i, k in enumerate(kept)
                 if abs(r["t"] - k["t"]) < CONCURRENCY]
        if any(PRIORITY.get(kept[i]["name"], 99) <= PRIORITY.get(r["name"], 99)
              for i in rivals):
            continue    # ya hay uno de clase igual o más alta ahí mismo
        kept = [k for i, k in enumerate(kept) if i not in rivals] + [r]

    kept.sort(key=lambda r: r["t"])
    return [(r["t"], r["name"], r["trim"], r["why"]) for r in kept]
