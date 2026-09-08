#!/usr/bin/env python3
"""Métricas de estilo y motor genérico de gates.

LA SEPARACIÓN QUE IMPORTA: aquí se CALCULAN métricas — una lista fija y
cerrada, en código. Los UMBRALES y la SEVERIDAD viven en `styles/*.json`.
Un perfil nuevo es un archivo nuevo y cero líneas de este módulo.
"""
from __future__ import annotations

from dataclasses import dataclass

from edl_schema import Edl, derive_stages, segment_windows

# Un cambio macro es un cambio de MUNDO; uno micro, de lectura.
MACRO_EVENTS = frozenset({"CAMERA", "OBJECT_IN", "OBJECT_EXIT", "OBJECT_STATE",
                          "STAGE_CLEAR", "THEME_CHANGE", "TYPE_BEAT", "UI_ACTION"})
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


def measure(edl: Edl) -> dict[str, float]:
    """La lista FIJA de métricas. Añadir una es tocar código, a propósito."""
    total = edl.wt.duration
    windows = segment_windows(edl.segments, edl.wt)

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
        "stage_count": float(len(derive_stages(edl.segments))),
        "segment_count": float(len(edl.segments)),
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
