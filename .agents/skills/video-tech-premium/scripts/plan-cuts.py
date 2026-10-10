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
  - Con `--audio`, la pausa que queda se coloca sobre SILENCIO, nunca sobre una
    respiración. Ver abajo.

⚠ LA PAUSA QUE QUEDA TIENE QUE SER SILENCIO. Repartir la pausa objetivo a
partes iguales a los dos lados del hueco es lo natural... salvo que justo
detrás de la palabra haya una inspiración, que es exactamente donde suelen
estar. En la pieza 14 eso dejó 200 ms de una respiración de −11.9 dB pegados
al final de «decisión.» —dentro del hook, y se oye.

Con `--audio` se miden las islas sin voz (`voicing.breath_islands`) y cada
lado de la pausa se recorta hasta donde empieza la respiración: se conserva la
MISMA pausa total, pero hecha de silencio. Sin `--audio` el comportamiento es
el de siempre, para que las piezas anteriores se vuelvan a cortar igual.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

GAP_MIN      = 0.45   # por debajo de esto el hueco se respeta tal cual
PAUSE_SENT   = 0.40   # pausa que queda tras fin de oración
PAUSE_MID    = 0.25   # pausa que queda a mitad de frase
HEAD_PAD     = 0.15   # aire antes de la primera palabra
TAIL_PAD     = 0.40   # aire tras la última palabra
MIN_CUT      = 0.25   # por debajo de esto el corte no compensa el salto visual
GUARD        = 0.030  # no se corta pegado al ataque de una respiración
MIN_PAD      = 0.120  # aire mínimo en cabeza y cola: por debajo suena cortado

SENT_END = tuple(".!?:")


def clean_span(t0, t1, islands, hacia_delante):
    """Cuánto se puede conservar desde un borde sin tocar una respiración.

    `hacia_delante`: se conserva desde `t0` hacia `t1` (la cola de la palabra
    anterior). Si no, se conserva desde `t1` hacia atrás (la entrada de la
    siguiente). Devuelve segundos, nunca negativos.
    """
    if hacia_delante:
        lim = min((b0 for b0, b1, _ in islands if b1 > t0 and b0 < t1),
                  default=None)
        if lim is None:           # sin respiración, el hueco entero está limpio
            return t1 - t0
        return max(0.0, min(t1, lim - GUARD) - t0)
    lim = max((b1 for b0, b1, _ in islands if b0 < t1 and b1 > t0), default=None)
    if lim is None:
        return t1 - t0
    return max(0.0, t1 - max(t0, lim + GUARD))


def main():
    ap = argparse.ArgumentParser(description="Plan de cortes desde el transcript")
    ap.add_argument("transcript")
    ap.add_argument("cuts")
    ap.add_argument("duration", nargs="?", type=float,
                    help="duración REAL de ffprobe (AssemblyAI la redondea)")
    ap.add_argument("--audio", help="coloca la pausa sobre silencio, no sobre "
                                    "una respiración (ver la cabecera)")
    args = ap.parse_args()

    src, dest = Path(args.transcript), Path(args.cuts)
    t = json.loads(src.read_text())
    words = t["words"]
    dur = args.duration if args.duration else float(t["audio_duration"])

    islands = []
    if args.audio:
        # ⚠ El detector es CIEGO AL TRANSCRIPT a propósito, así que también caza
        # las plosivas y las nasales apagándose DENTRO de una palabra. Aquí
        # estorban: una ráfaga de 25 ms sobre el ataque de «Una» dejaría la
        # pausa de ese lado en cero. Solo interesan las islas que no pisan
        # ninguna palabra.
        from voicing import breath_islands, load_mono
        a, sr = load_mono(args.audio)
        M = 0.060
        spans = [(w["start"] / 1000, w["end"] / 1000) for w in words]
        crudas = breath_islands(a, sr)
        islands = [x for x in crudas
                   if not any(x[1] > s0 - M and x[0] < s1 + M for s0, s1 in spans)]
        print(f"{len(crudas)} islas sin voz en {args.audio}; "
              f"{len(islands)} fuera de toda palabra\n")

    cuts = []   # (inicio, fin, motivo)

    # cabeza — el aire de entrada también tiene que ser silencio
    w0 = words[0]["start"] / 1000
    pad = HEAD_PAD
    if islands:
        pad = min(pad, max(MIN_PAD, clean_span(w0 - HEAD_PAD, w0, islands, False)))
    head_keep = max(0.0, w0 - pad)
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
        if islands:
            # La pausa total no cambia; cambia DE QUÉ está hecha. Se conserva
            # todo lo que se pueda por cada lado sin tocar una respiración y,
            # si un lado se queda corto, el otro lo compensa.
            head = min(keep_each, clean_span(end, start, islands, True))
            tail = min(target - head, clean_span(end, start, islands, False))
            if head < keep_each:                 # el lado corto es la cabeza
                head = min(head, clean_span(end, start, islands, True))
            cut_a, cut_b = end + head, start - tail
            if cut_b <= cut_a:                   # el hueco es respiración entera
                cut_a, cut_b = end + head, start - min(tail, max(0.0, start - end - head))
        if cut_b - cut_a < MIN_CUT:      # micro-corte: no compensa el salto
            continue
        kind = "pausa fin de oración" if a["text"].endswith(SENT_END) else "pausa interna"
        cuts.append((cut_a, cut_b, kind))

    # cola — idem: la última respiración de la toma no entra en el reel
    wn = words[-1]["end"] / 1000
    pad = TAIL_PAD
    if islands:
        pad = min(pad, max(MIN_PAD, clean_span(wn, wn + TAIL_PAD, islands, True)))
    tail_keep = min(dur, wn + pad)
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
