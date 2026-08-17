#!/usr/bin/env python3
"""Cuadra los bordes del transcript con la energía real del audio.

    scripts/refine-timings.py assets/audio/3.flac transcripts/3.json [--write]

AssemblyAI clava bien el centro de cada palabra pero **recorta los bordes que
dan a un silencio**: la primera palabra tras una pausa aparece 150 ms tarde y
la última antes de la pausa termina 300 ms pronto. Da igual para leer el texto
y es grave aquí, porque `plan-cuts.py` corta justo en esos huecos: un borde
optimista se lleva por delante el ataque de la palabra siguiente.

Este paso NO reescribe la transcripción — solo mueve los bordes que dan a un
hueco hasta donde el audio deja de sonar de verdad, y avisa de dos cosas que
solo se ven midiendo:

  · **contenido audible sin transcribir** dentro de un hueco (una duda, un
    «mmm», una palabra que se comió el modelo). Cortar ahí parte un sonido por
    la mitad. Se clasifica por espectro: más grave que agudo → vocalización,
    más agudo → respiración.
  · **tramos con la alineación rota** — palabras cuyo ritmo silábico es
    imposible (más de 12 síl/s sostenidas). Ahí el remedio no es este script:
    hay que re-transcribir el tramo suelto, que sale bien porque el modelo
    deja de arrastrar el contexto largo.

Sin `--write` solo informa. Con `--write` guarda el transcript corregido.
"""
import argparse
import io
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

HOP = 0.010          # 10 ms de salto en la envolvente
WIN = 0.025          # 25 ms de ventana
GAP_MIN = 0.45       # solo se refinan los bordes que dan a un hueco así de grande
MARGIN_DB = 10.0     # cuánto sobre el suelo de ruido cuenta como voz
FLOOR_DB = -45.0     # por debajo de esto nunca es voz, aunque el suelo esté bajo
MAX_SHIFT = 0.50     # un borde no se mueve más que esto: si hace falta, es otro problema
VOWELS = "aeiouáéíóúü"


def load_mono(path, sr=16000):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "wav",
         "-ac", "1", "-ar", str(sr), "-"],
        capture_output=True).stdout
    w = wave.open(io.BytesIO(raw))
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return a.astype(np.float32) / 32768.0, sr


def envelope(a, sr):
    hop, win = int(HOP * sr), int(WIN * sr)
    n = max(0, (len(a) - win) // hop + 1)
    frames = np.lib.stride_tricks.as_strided(
        a, shape=(n, win), strides=(a.strides[0] * hop, a.strides[0]))
    rms = np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1))
    return 20 * np.log10(np.maximum(rms, 1e-9))


def classify(a, sr, t0, t1):
    """Vocalización o aire, por reparto espectral. Igual que en la bitácora."""
    seg = a[int(t0 * sr):int(t1 * sr)]
    if len(seg) < 256:
        return "?"
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    fr = np.fft.rfftfreq(len(seg), 1 / sr)
    lo = spec[(fr > 80) & (fr < 500)].sum()
    hi = spec[fr > 2000].sum()
    return "vocalización" if lo > hi else "respiración"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("transcript")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    a, sr = load_mono(args.audio)
    db = envelope(a, sr)
    dur = len(a) / sr

    floor = float(np.percentile(db, 10))
    thr = max(floor + MARGIN_DB, FLOOR_DB)
    print(f"suelo de ruido {floor:6.1f} dB · umbral de voz {thr:6.1f} dB "
          f"· {dur:.2f} s\n")

    def loud(t):
        i = int(t / HOP)
        return 0 <= i < len(db) and db[i] > thr

    tp = Path(args.transcript)
    doc = json.loads(tp.read_text())
    words = doc["words"]

    moved = []
    warn_audible = []

    for i, w in enumerate(words):
        prev_end = words[i - 1]["end"] / 1000 if i else 0.0
        next_start = words[i + 1]["start"] / 1000 if i + 1 < len(words) else dur
        s, e = w["start"] / 1000, w["end"] / 1000

        # ── borde de entrada: solo si delante hay un hueco de verdad
        if s - prev_end > GAP_MIN:
            t, limit = s, max(prev_end, s - MAX_SHIFT)
            while t - HOP > limit and loud(t - HOP):
                t -= HOP
            if s - t > 0.02:
                moved.append((i, w["text"], "inicio", s, t))
                w["start"] = round(t * 1000)

        # ── borde de salida
        if next_start - e > GAP_MIN:
            t, limit = e, min(next_start, e + MAX_SHIFT)
            while t + HOP < limit and loud(t + HOP):
                t += HOP
            if t - e > 0.02:
                moved.append((i, w["text"], "final", e, t))
                w["end"] = round(t * 1000)

    # ── contenido audible dentro de los huecos ya refinados
    for a_, b_ in zip(words, words[1:]):
        g0, g1 = a_["end"] / 1000, b_["start"] / 1000
        if g1 - g0 <= GAP_MIN:
            continue
        i0, i1 = int(g0 / HOP), int(g1 / HOP)
        seg = db[i0:i1]
        if len(seg) == 0:
            continue
        hits = np.flatnonzero(seg > thr)
        if len(hits) < 5:                      # menos de 50 ms: es un chasquido
            continue
        # Islas contiguas: un hueco con dos soplidos sueltos no es lo mismo que
        # un hueco lleno de una duda de dos segundos, y el primero se corta sin
        # pensarlo. Solo interesa la isla más larga.
        islands, run = [], [hits[0]]
        for p, q in zip(hits, hits[1:]):
            if q - p <= 3:                     # hasta 30 ms de bache = misma isla
                run.append(q)
            else:
                islands.append(run)
                run = [q]
        islands.append(run)
        best = max(islands, key=len)
        span = len(best) * HOP
        if span < 0.12:                        # islas cortas: soplidos, se cortan
            continue
        t0 = g0 + best[0] * HOP
        t1 = g0 + best[-1] * HOP
        warn_audible.append((t0, t1, float(seg[best].max()),
                             classify(a, sr, t0, t1),
                             a_["text"], b_["text"]))

    # ── alineación imposible: ritmo silábico fuera de lo humano
    suspect = []
    for i, w in enumerate(words):
        d = (w["end"] - w["start"]) / 1000
        txt = w["text"].strip(".,;:¿?¡!").lower()
        syl = max(1, sum(c in VOWELS for c in txt))
        if len(txt) > 3 and d > 0 and syl / d > 12:
            suspect.append((i, w["text"], w["start"] / 1000, d, syl / d))

    if moved:
        print(f"{len(moved)} bordes cuadrados con el audio:")
        for i, txt, which, was, now in moved:
            print(f"  {i:3d} {txt:<16} {which:<6} {was:7.3f} -> {now:7.3f} "
                  f"({(now-was)*1000:+5.0f} ms)")
    else:
        print("ningún borde necesitaba moverse")

    if warn_audible:
        print(f"\n⚠ {len(warn_audible)} huecos con sonido audible sin transcribir "
              f"— cortar ahí parte el sonido:")
        for t0, t1, pk, kind, before, after in warn_audible:
            print(f"  {t0:7.3f}-{t1:7.3f}  pico {pk:6.1f} dB  {kind:<13} "
                  f"…{before} ⟨hueco⟩ {after}…")

    if suspect:
        print(f"\n⚠ {len(suspect)} palabras con alineación imposible "
              f"— re-transcribe ese tramo suelto:")
        for i, txt, at, d, rate in suspect:
            print(f"  {i:3d} {at:7.3f}  {txt:<16} {d:5.3f} s  {rate:5.1f} síl/s")

    if args.write:
        tp.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
        print(f"\nescrito -> {tp}")
    else:
        print("\n(en seco: pasa --write para guardar)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
