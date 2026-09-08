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

from edl_metrics import measure, run_gates
from edl_schema import Edl, EdlError, load_edl, segment_windows

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
    """La capa de metraje. Un encuadre por segmento, más los eventos CAMERA."""
    ladder = style["camera"]["ladder"]
    anchor = style["camera"]["default_anchor"]
    out: list[dict] = []

    def push(at: float, camera: str) -> None:
        if camera == "OFF":
            out.append({"at": q(at), "kind": "off"})
        else:
            out.append({"at": q(at), "kind": "full",
                        "zoom": ladder[camera], "anchor": anchor})

    windows = segment_windows(edl.segments, edl.wt)
    for (start, _end), seg in zip(windows, edl.segments):
        # El primer encuadre arranca la PIEZA, no la primera palabra: antes de
        # que él hable ya hay imagen en pantalla. `segment_windows` ya lo
        # resuelve así, y es la MISMA regla que measure() usa para calcular
        # cuánto tiempo está el presentador en pantalla.
        push(start, seg.camera)
        for ev in sorted(seg.events, key=lambda e: (e.at_word,)):
            if ev.type == "CAMERA":
                push(ev.t(edl.wt), ev.state.get("camera") or ev.theme or "MEDIUM")

    out.sort(key=lambda s: s["at"])
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
        "visuals": [],
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
