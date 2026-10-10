#!/usr/bin/env python3
"""Voz frente a sonido. El módulo que decide qué es una respiración.

Existe porque `refine-timings.py` y `plan-cuts.py` necesitan la MISMA
respuesta a la misma pregunta, y dos copias que divergen ya fueron un problema
real en este proyecto (por eso `scripts/` es un enlace y no una copia).

LA LECCIÓN QUE LO CREÓ. En la pieza 14 se entregó un video con una inspiración
de 900 ms a −11.9 dB dentro del hook: más fuerte que media frase. Nadie la
cazó porque las dos herramientas medían ENERGÍA — y una respiración de
proximidad tiene mucha. Lo que la delata es que no tiene TONO:

    vocal        armonicidad 0.35-0.69   energía >400 Hz  0.11-0.93
    fricativa    armonicidad 0.24        energía >400 Hz  0.90     (la «s»)
    respiración  armonicidad 0.06-0.25   energía >400 Hz  0.01-0.11

Hacen falta las dos medidas: la armonicidad sola marcaría la «s» como
respiración, y la energía alta sola marcaría como voz cualquier soplido.
"""
from __future__ import annotations

import io
import subprocess
import wave

import numpy as np

HOP = 0.010
WIN = 0.025
VOICE_WIN = 0.040        # a 70 Hz, 25 ms no llegan a dos ciclos
F0_LO, F0_HI = 70, 350
HARM_MIN = 0.32
HIGH_MIN = 0.40
HIGH_HZ = 400.0
MARGIN_DB = 10.0
FLOOR_DB = -45.0


def load_mono(path, sr=16000):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "wav",
         "-ac", "1", "-ar", str(sr), "-"], capture_output=True).stdout
    w = wave.open(io.BytesIO(raw))
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return a.astype(np.float32) / 32768.0, sr


def _frames(a, sr, win_s):
    hop, win = int(HOP * sr), int(win_s * sr)
    n = max(0, (len(a) - win) // hop + 1)
    return np.lib.stride_tricks.as_strided(
        a, shape=(n, win), strides=(a.strides[0] * hop, a.strides[0])), win


def envelope(a, sr):
    fr, _ = _frames(a, sr, WIN)
    rms = np.sqrt((fr.astype(np.float64) ** 2).mean(axis=1))
    return 20 * np.log10(np.maximum(rms, 1e-9))


def voicing(a, sr):
    """Armonicidad y fracción de energía alta, frame a frame.

    La autocorrelación va por FFT (Wiener-Khinchin): frame a frame con
    `np.correlate` sobre un minuto de audio tarda minutos.
    """
    # ⚠ MISMO NÚMERO DE FRAMES QUE `envelope`. La ventana de voz es más larga
    # (40 ms frente a 25), así que sin rellenar sale un frame menos y cualquier
    # `harm[db > thr]` revienta con un IndexError — o, peor, desalinea en
    # silencio. Se rellena la señal, no se recorta el resultado.
    hop = int(HOP * sr)
    n_env = max(0, (len(a) - int(WIN * sr)) // hop + 1)
    falta = int(VOICE_WIN * sr) - int(WIN * sr)
    a = np.concatenate([a, np.zeros(falta, dtype=a.dtype)]) if falta > 0 else a

    fr, win = _frames(a, sr, VOICE_WIN)
    fr = fr[:n_env]
    if len(fr) == 0:
        return np.zeros(n_env), np.zeros(n_env)
    x = fr.astype(np.float64)
    x = x - x.mean(axis=1, keepdims=True)

    nfft = 1 << int(np.ceil(np.log2(2 * win)))
    pot = np.abs(np.fft.rfft(x * np.hanning(win), n=nfft, axis=1)) ** 2
    ac = np.fft.irfft(pot, n=nfft, axis=1)[:, :win]
    ac = ac / (ac[:, :1] + 1e-12)
    lo, hi = int(sr / F0_HI), min(win - 1, int(sr / F0_LO))
    harm = ac[:, lo:hi].max(axis=1) if hi > lo else np.zeros(len(x))

    frq = np.fft.rfftfreq(nfft, 1 / sr)
    alta = pot[:, frq > HIGH_HZ].sum(axis=1) / (pot.sum(axis=1) + 1e-20)
    return harm, alta


def thresholds(db):
    floor = float(np.percentile(db, 10))
    return floor, max(floor + MARGIN_DB, FLOOR_DB)


def voice_mask(db, harm, alta, thr):
    """True donde hay VOZ: suena Y tiene tono o aire alto."""
    n = min(len(db), len(harm))
    m = np.zeros(len(db), dtype=bool)
    m[:n] = (db[:n] > thr) & ((harm[:n] >= HARM_MIN) | (alta[:n] >= HIGH_MIN))
    return m


def breath_islands(a, sr, thr=None, min_dur=0.08, loud_db=-25.0, skirt_db=6.0):
    """Islas AUDIBLES y SIN VOZ, en segundos: `[(t0, t1, pico_db), ...]`.

    No mira el transcript a propósito — una respiración es una respiración
    caiga donde caiga, y así el mismo detector sirve para cuadrar bordes, para
    colocar la pausa de un corte y para auditar el MP4 entregado.

    ⚠ `thr` SE PASA CUANDO EL AUDIO YA ESTÁ CORTADO. El umbral por defecto sale
    del percentil 10 de la propia envolvente, y un corte ya no contiene los
    silencios de los que ese percentil se estima: medido en la pieza 14, el
    suelo «sube» de −52.0 a −41.9 dB y el umbral con él, de −42.0 a −31.9. Con
    el umbral equivocado, una ráfaga de −11.7 dB se quedaba en 75 ms y caía por
    debajo de `min_dur`. Para auditar un corte se pasa el umbral de la FUENTE.

    ⚠ `loud_db`: una isla CORTA pero FUERTE cuenta igual. Un chasquido de boca
    de 60 ms a −12 dB se oye perfectamente, y filtrar solo por duración lo dejó
    pasar.

    ⚠ `skirt_db`: la isla se extiende por sus dos lados mientras la energía
    siga por encima de `suelo + skirt_db`. Lo AUDIBLE es más ancho que lo que
    cruza el umbral de detección, y cortar en el borde estrecho deja el ataque
    de la respiración dentro del material conservado — que es exactamente lo
    que pasó en la pieza 14 con el corte de «ingresos.».
    """
    db = envelope(a, sr)
    harm, alta = voicing(a, sr)
    floor, auto = thresholds(db)
    thr = auto if thr is None else float(thr)
    aire = (db > thr) & ~voice_mask(db, harm, alta, thr)
    faldon = floor + skirt_db

    out, i, n = [], 0, len(aire)
    while i < n:
        if not aire[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and aire[j + 1]:
            j += 1
        # el faldón: hasta donde deja de OÍRSE, no hasta donde deja de detectarse
        lo, hi = i, j
        while lo > 0 and db[lo - 1] > faldon and not voice_mask(
                db, harm, alta, thr)[lo - 1]:
            lo -= 1
        while hi + 1 < n and db[hi + 1] > faldon and not voice_mask(
                db, harm, alta, thr)[hi + 1]:
            hi += 1
        t0, t1 = lo * HOP, hi * HOP + WIN
        pico = float(db[lo:hi + 1].max())
        if (t1 - t0) >= min_dur or pico >= loud_db:
            out.append((t0, t1, pico))
        i = j + 1

    # el faldón puede solapar islas vecinas: se funden
    fundidas = []
    for t0, t1, pk in out:
        if fundidas and t0 <= fundidas[-1][1]:
            a0, a1, apk = fundidas[-1]
            fundidas[-1] = (a0, max(a1, t1), max(apk, pk))
        else:
            fundidas.append((t0, t1, pk))
    return fundidas


def source_threshold(path):
    """El umbral de una FUENTE sin cortar, para auditar su corte."""
    a, sr = load_mono(path)
    return thresholds(envelope(a, sr))[1]
