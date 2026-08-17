#!/usr/bin/env python3
"""Plan de cortes a partir del transcript de AssemblyAI.

    scripts/plan-cuts.py transcripts/1.json cuts/1.json

Reglas:
  - Nunca corta dentro de una palabra: los cortes viven en los huecos entre palabras.
  - Deja aire antes de la primera y después de la última palabra (no se pisa el arranque
    ni el cierre).
  - Los huecos largos se COLAPSAN a una pausa natural, no se eliminan del todo:
    un video sin respiración suena atropellado.
  - Pausa objetivo mayor en fin de oración que a mitad de frase.
"""
import json
import sys
from pathlib import Path

GAP_MIN      = 0.45   # por debajo de esto el hueco se respeta tal cual
PAUSE_SENT   = 0.40   # pausa que queda tras fin de oración
PAUSE_MID    = 0.25   # pausa que queda a mitad de frase
HEAD_PAD     = 0.15   # aire antes de la primera palabra
TAIL_PAD     = 0.40   # aire tras la última palabra
MIN_CUT      = 0.25   # por debajo de esto el corte no compensa el salto visual

SENT_END = tuple(".!?:")


def main():
    src, dest = Path(sys.argv[1]), Path(sys.argv[2])
    t = json.loads(src.read_text())
    words = t["words"]
    # AssemblyAI redondea audio_duration al segundo; para la cola hace falta la real
    if len(sys.argv) > 3:
        dur = float(sys.argv[3])
    else:
        dur = float(t["audio_duration"])

    cuts = []   # (inicio, fin, motivo)

    # cabeza
    head_keep = max(0.0, words[0]["start"] / 1000 - HEAD_PAD)
    if head_keep > 0.05:
        cuts.append((0.0, head_keep, "cabeza muerta"))

    # huecos internos
    for a, b in zip(words, words[1:]):
        end, start = a["end"] / 1000, b["start"] / 1000
        gap = start - end
        if gap <= GAP_MIN:
            continue
        target = PAUSE_SENT if a["text"].endswith(SENT_END) else PAUSE_MID
        if gap <= target:
            continue
        keep_each = target / 2
        cut_a, cut_b = end + keep_each, start - keep_each
        if cut_b - cut_a < MIN_CUT:      # micro-corte: no compensa el salto
            continue
        kind = "pausa fin de oración" if a["text"].endswith(SENT_END) else "pausa interna"
        cuts.append((cut_a, cut_b, kind))

    # cola
    tail_keep = min(dur, words[-1]["end"] / 1000 + TAIL_PAD)
    if dur - tail_keep > 0.05:
        cuts.append((tail_keep, dur, "cola muerta"))

    removed = sum(b - a for a, b, _ in cuts)

    # segmentos que se conservan
    keeps, cursor = [], 0.0
    for a, b, _ in cuts:
        if a > cursor:
            keeps.append((cursor, a))
        cursor = b
    if cursor < dur:
        keeps.append((cursor, dur))

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({
        "source_duration": dur,
        "final_duration": dur - removed,
        "removed": removed,
        "cuts": [{"start": round(a, 3), "end": round(b, 3),
                  "dur": round(b - a, 3), "reason": r} for a, b, r in cuts],
        "keeps": [{"start": round(a, 3), "end": round(b, 3),
                   "dur": round(b - a, 3)} for a, b in keeps],
    }, ensure_ascii=False, indent=2))

    # ---- reporte legible ----
    def ctx(ts, before):
        """Palabra anterior / siguiente al punto de corte."""
        if before:
            c = [w for w in words if w["end"] / 1000 <= ts + 0.01]
            return c[-1]["text"] if c else "—"
        c = [w for w in words if w["start"] / 1000 >= ts - 0.01]
        return c[0]["text"] if c else "—"

    print(f"FUENTE {dur:.2f}s  ->  FINAL {dur-removed:.2f}s   "
          f"(se quitan {removed:.2f}s, {removed/dur*100:.0f}%)\n")
    print(f"{'#':>2}  {'desde':>7} {'hasta':>7} {'dura':>6}  {'motivo':<22} contexto")
    print("-" * 92)
    for i, (a, b, r) in enumerate(cuts, 1):
        print(f"{i:2d}  {a:7.2f} {b:7.2f} {b-a:6.2f}  {r:<22} "
              f"…{ctx(a, True)} ⟨corte⟩ {ctx(b, False)}…")
    print(f"\n{len(keeps)} segmentos conservados")


if __name__ == "__main__":
    main()
