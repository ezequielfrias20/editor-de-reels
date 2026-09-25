#!/usr/bin/env python3
"""El andamiaje DETERMINISTA del Creative Planner — no el Planner.

    scripts/edl-plan.py --project . --piece 12 [--style motion-explainer] [--format REEL]

Escribe `videos/<piece>/edl.draft.json`: un segmento `A_ROLL` por FRASE del
transcript (partido en los signos de puntuación que ya trae AssemblyAI), con
un único `CAPTION` que cubre todo el rango de palabras y un `reason` honesto
— «borrador sin revisar», nunca una razón creativa inventada.

NO elige `MOTION_STAGE`, no asigna objetos, no resalta keywords, no decide
cámara. Esas son las decisiones NO deterministas de verdad (§ referencia
`planner.md`), y este script no las toma por nadie — las deja explícitamente
pendientes para que un agente o un humano las complete editando el draft.

Ver `references/planner.md` para el contrato completo: qué entra, qué sale,
las cuatro restricciones, y por qué el draft nunca lo acepta `edl-compile.py`
directamente (tiene que pasar por el Asset Resolver y por CORE primero).
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edl_words import load_words  # noqa: E402

ENDERS = (".", "?", "!", "…")


def _sentences(words) -> list[tuple[int, int]]:
    """Rangos `[inicio, fin]` de índice de palabra, uno por frase.

    Una frase termina en la palabra cuyo texto acaba en uno de `ENDERS`,
    sin importar mayúsculas ni signos de apertura (¿, ¡) que AssemblyAI no
    siempre transcribe de todos modos. La última frase se cierra aunque no
    termine en signo — un transcript real casi nunca lo hace.
    """
    out, start = [], 0
    for i, w in enumerate(words):
        if w.text.rstrip().endswith(ENDERS):
            out.append((start, i))
            start = i + 1
    if start < len(words):
        out.append((start, len(words) - 1))
    return out


def build_draft(wt, piece: int, fmt: str, style_profile: str,
                planner_version: str, prompt_version: str, palette: str) -> dict:
    segments = []
    for lo, hi in _sentences(wt.words):
        segments.append({
            "words": [lo, hi],
            "semanticIntent": wt.text_of(lo, hi),
            "sceneType": "A_ROLL",
            "camera": "MEDIUM",
            "transitionIn": "CUT",
            "events": [
                {"atWord": lo, "type": "CAPTION", "words": [lo, hi]},
            ],
            "reason": "borrador sin revisar — decidir sceneType, objetos y cámara",
        })

    return {
        "format": fmt.upper(),
        "palette": palette,
        "piece": piece,
        "style_profile": style_profile,
        "transcript": {
            "words": f"transcripts/{piece}.json",
            "cuts": f"cuts/{piece}.json",
            "fingerprint": wt.fingerprint,
        },
        "voice_gain": 0.70,
        "segments": segments,
        "planner": {
            "plannerVersion": planner_version,
            "styleProfile": style_profile,
            "promptVersion": prompt_version,
            "generatedAt": datetime.datetime.now(datetime.timezone.utc)
                                   .strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Genera el andamiaje determinista de un edl.draft.json")
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--piece", required=True, type=int)
    ap.add_argument("--style", default="motion-explainer")
    ap.add_argument("--format", default="REEL", choices=("REEL", "YOUTUBE"))
    ap.add_argument("--palette", required=True, choices=("claro", "oscuro"),
                    help="paleta de la marca: la elige el brief o el usuario, no el andamiaje")
    ap.add_argument("--planner-version", default="0.1.0")
    ap.add_argument("--prompt-version", default="draft")
    ap.add_argument("-o", "--out", type=Path, default=None)
    a = ap.parse_args(argv)

    root = a.project.resolve()
    tr = root / "transcripts" / f"{a.piece}.json"
    cu = root / "cuts" / f"{a.piece}.json"
    if not tr.exists() or not cu.exists():
        sys.exit(f"faltan {tr} o {cu} — corre el pipeline (§2) hasta el paso 3 primero")

    wt = load_words(tr, cu)
    draft = build_draft(wt, a.piece, a.format, a.style,
                        a.planner_version, a.prompt_version, a.palette)

    out = a.out or (root / "videos" / str(a.piece) / "edl.draft.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n")
    print(f"✓ {out}  ·  {len(draft['segments'])} frases  ·  {len(wt.words)} palabras")
    print("  todo A_ROLL, sin objetos ni keywords — revisar y editar antes del Resolver")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
