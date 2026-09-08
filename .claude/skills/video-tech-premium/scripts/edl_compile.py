#!/usr/bin/env python3
"""EDL → plan.json. Determinista, y sin decidir nada.

FRONTERA (spec §9): este módulo hace aritmética, lookup, derivación y
aplicación de fórmulas. NO elige objetos, ni instantes, ni si un segmento
merece visual. Si una decisión podría ser razonablemente distinta en manos de
otro editor, no es de aquí.

Mínimo a propósito: emite `keywords` como lista de strings, que es lo que el
motor de captions actual ya consume, así que `build-composition.py` no se toca.
Las captions explícitas llegan en la Tarea 7.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import objects as _objects
from edl_metrics import measure, run_gates
from edl_schema import Edl, EdlError, derive_stages, load_edl, segment_windows

FPS = 30


def q(t: float) -> float:
    """Cuantiza a frame y recorta a 4 decimales.

    Copia literal de build-composition.py. EL ÚNICO punto de cuantización del
    compilador: un segundo sitio que redondee haría que dos rutas dieran
    instantes distintos para la misma palabra.
    """
    return round(round(float(t) * FPS) / FPS, 4)


def load_style(name: str, skill_root: Path) -> dict:
    p = Path(skill_root) / "styles" / f"{name}.json"
    if not p.exists():
        disponibles = sorted(x.stem for x in (Path(skill_root) / "styles").glob("*.json"))
        raise FileNotFoundError(
            f"no existe el style profile '{name}' en {p.parent}. "
            f"Disponibles: {disponibles or '(ninguno)'}")
    return json.loads(p.read_text())


def _shots(edl: Edl, style: dict) -> list[dict]:
    """La capa de metraje. Un encuadre por segmento, más los eventos CAMERA.

    Gotcha #6: un `off` que empieza a la vez que el takeover deja el frame
    vacío durante el fundido — el visual no ha terminado de aparecer y no hay
    nada debajo. El encuadre visible se queda hasta `start + fade_in` (el
    takeover ya está del todo puesto), y al salir del stage el siguiente
    encuadre entra en `start − fade_out` (antes de que el fundido de salida
    termine), nunca exactamente en el borde del stage.
    """
    ladder = style["camera"]["ladder"]
    anchor = style["camera"]["default_anchor"]
    fade_in = style["stage"]["fade_in"]
    fade_out = style["stage"]["fade_out"]
    out: list[dict] = []

    def emit(at: float, camera: str) -> None:
        if camera == "OFF":
            out.append({"at": q(at), "kind": "off"})
        else:
            out.append({"at": q(at), "kind": "full",
                        "zoom": ladder[camera], "anchor": anchor})

    windows = segment_windows(edl.segments, edl.wt)
    prev_camera = None
    for (start, _end), seg in zip(windows, edl.segments):
        # El primer encuadre arranca la PIEZA, no la primera palabra: antes de
        # que él hable ya hay imagen en pantalla. `segment_windows` ya lo
        # resuelve así, y es la MISMA regla que measure() usa para calcular
        # cuánto tiempo está el presentador en pantalla.
        if seg.camera == "OFF" and prev_camera != "OFF":
            emit(start + fade_in, "OFF")
        elif seg.camera != "OFF" and prev_camera == "OFF":
            emit(start - fade_out, seg.camera)
        else:
            emit(start, seg.camera)
        prev_camera = seg.camera

        for ev in sorted(seg.events, key=lambda e: (e.at_word,)):
            if ev.type == "CAMERA":
                cam = ev.state.get("camera") or ev.theme or "MEDIUM"
                emit(ev.t(edl.wt), cam)
                prev_camera = cam

    out.sort(key=lambda s: s["at"])
    return out


def _visuals(edl: Edl, style: dict) -> list[dict]:
    """La capa de Motion Stage. Cada stage sale como UNA sola entrada de
    `visuals`, con un `fade_in` al principio y un `fade_out` al final —
    nunca una entrada por segmento (§3, la razón de existir de
    `check_no_black()`).

    El compilador NO decide qué objeto representa una idea ni cuándo entra:
    eso ya está en el EDL. Aquí solo se traduce `OBJECT_IN`/`OBJECT_STATE` a
    coordenadas, ángulos e instantes — aritmética y lookup, nada más.
    """
    fade_in = style["stage"]["fade_in"]
    fade_out = style["stage"]["fade_out"]
    windows = segment_windows(edl.segments, edl.wt)
    out: list[dict] = []

    for si, stage in enumerate(derive_stages(edl.segments)):
        start = windows[stage.first][0]
        end = windows[stage.last][1]
        theme = "primary"
        obj_defs: list[dict] = []
        ops: list[dict] = []
        last_state: dict[str, dict] = {}

        events = []
        for k in range(stage.first, stage.last + 1):
            events.extend(edl.segments[k].events)
        events.sort(key=lambda e: e.at_word)

        for ev in events:
            if ev.type == "THEME_CHANGE":
                theme = ev.theme or theme
            elif ev.type == "OBJECT_IN":
                # "object:clock@1" -> "clock". La referencia ya llegó resuelta
                # y versionada (§11); el compilador solo lee el nombre.
                kind = ev.asset.split(":", 1)[1].split("@", 1)[0]
                obj_defs.append({"id": ev.instance_id, "kind": kind,
                                 "slot": ev.slot, "state": dict(ev.state),
                                 "in": q(ev.t(edl.wt))})
                last_state[ev.instance_id] = dict(ev.state)
            elif ev.type == "OBJECT_STATE":
                prev = last_state.get(ev.instance_id, {})
                op = {"t": q(ev.t(edl.wt)), "op": "state", "id": ev.instance_id}
                if "time" in ev.state:
                    # Las agujas se derivan del estado ANTERIOR conocido de
                    # esta instancia, no de lo que el EDL escribe: el compilador
                    # rastrea la continuidad, el EDL solo dice el objetivo.
                    angles = _objects.hand_angles(
                        prev.get("time", "12:00"), ev.state["time"])
                    op["hour"] = angles["hour_to"]
                    op["minute"] = angles["minute_to"]
                    # El FROM también viaja: el tween de las agujas no lee el
                    # valor CSS "actual" del elemento (transform-origin en un
                    # <g> SVG demostró no ser fiable bajo GSAP), así que
                    # necesita los dos extremos explícitos.
                    op["hour_from"] = angles["hour_from"]
                    op["minute_from"] = angles["minute_from"]
                if ev.preset:
                    op["preset"] = ev.preset
                ops.append(op)
                last_state[ev.instance_id] = {**prev, **ev.state}

        out.append({
            "id": f"stage-{chr(97 + si)}", "role": "takeover", "kind": "mockup",
            "start": q(start), "end": q(end), "skin": "on-surface",
            "fade_in": fade_in, "fade_out": fade_out,
            # `visual_start` es el MISMO q(start) de arriba: build-composition.py
            # reconstruye el tiempo absoluto de cada anim como s + a[2], así que
            # motion_stage() necesita restar este valor para dar offsets
            # relativos, no tiempos absolutos (ver el aviso en su docstring).
            "mock": ["motion_stage", {"theme": theme, "objects": obj_defs,
                                      "at": ops, "visual_start": q(start)}],
        })
    return out


def _keywords(edl: Edl) -> list[str]:
    """Las palabras que el motor de captions actual debe resaltar.

    Ordenadas y deduplicadas: un set iterado sin ordenar rompe el determinismo.
    """
    ks: set[str] = set()
    for seg in edl.segments:
        for ev in seg.events:
            if ev.type == "KEYWORD" and ev.words:
                for w in edl.wt.words[ev.words[0]:ev.words[1] + 1]:
                    ks.add(w.text.strip().rstrip(",.:;!?").upper())
    return sorted(ks)


def compile_edl(edl: Edl, style: dict) -> dict:
    """Función PURA: mismas entradas, mismo dict, siempre."""
    return {
        "format": edl.fmt,
        "voice_gain": edl.voice_gain,
        "music": edl.music,
        "keywords": _keywords(edl),
        "shots": _shots(edl, style),
        "cards": [],
        "visuals": _visuals(edl, style),
        "sfx": [],
        "_": f"generado por edl-compile desde {edl.src.name} — NO editar a mano",
    }


def write_plan(plan: dict, out: Path) -> None:
    Path(out).write_text(
        json.dumps(plan, ensure_ascii=False, indent=2,
                   sort_keys=True, separators=(",", ": ")) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Compila un edl.json a plan.json")
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--piece", required=True)
    ap.add_argument("-o", "--out", type=Path, default=None)
    a = ap.parse_args(argv)

    root = a.project.resolve()
    work = root / "videos" / str(a.piece)
    skill = root / ".claude" / "skills" / "video-tech-premium"

    try:
        edl = load_edl(work / "edl.json", root)
    except EdlError as e:
        print(f"✗ {len(e.problems)} problema(s) en el EDL de la pieza {a.piece}:\n",
              file=sys.stderr)
        for p in e.problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    style = load_style(edl.style_profile, skill)

    # Fase 5: el compilador CALCULA métricas; el perfil decide umbrales y
    # severidad. Un gate en fail detiene el compilador antes de escribir nada;
    # un warn se imprime y se sigue.
    metrics = measure(edl)
    findings = run_gates(metrics, style)
    for f in findings:
        marca = "✗" if f.severity == "fail" else "⚠"
        print(f"  {marca} {f.message}", file=sys.stderr)
    if any(f.severity == "fail" for f in findings):
        print("\n✗ gates de estilo en fallo; el plan no se escribe", file=sys.stderr)
        return 1

    print("  métricas: " + " · ".join(f"{k} {v}" for k, v in sorted(metrics.items())))

    plan = compile_edl(edl, style)
    out = a.out or (work / "plan.json")
    write_plan(plan, out)
    print(f"✓ {out}  ·  {len(edl.segments)} segmentos  ·  "
          f"{len(plan['shots'])} encuadres  ·  {len(plan['keywords'])} keywords")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
