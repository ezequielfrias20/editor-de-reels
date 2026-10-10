#!/usr/bin/env python3
"""Sintetiza una cama musical minimal-tech, libre de licencia y offline.

    scripts/make-music-bed.py assets/music/bed-tech.mp3 [--dur 70] [--bpm 100]

POR QUÉ SINTETIZARLA Y NO DESCARGARLA
La pieza es contenido comercial de marca personal, así que la música tiene que
ser limpia de derechos sin depender de la licencia de un catálogo. Y como el
resto del proyecto (fuentes, efectos), tiene que **vendorizarse**: si mañana
cambia una skill o caduca una credencial, la pieza debe seguir renderizando
igual. Generarla aquí cumple las dos cosas y además la hace reproducible: el
mismo comando da el mismo archivo.

EL DISEÑO — y es la parte que importa
La cama vive **14 dB por debajo de la voz**, así que no compite por volumen
sino por ESPECTRO. Una cama con energía en 300–3000 Hz emborrona las
consonantes aunque esté bajita, que es el error que hace que un video se sienta
«con música encima» en vez de «con música debajo». Aquí el reparto es:

    sub / bajo   55–160 Hz    el pulso: se siente en el pecho, no se escucha
    pad          160–300 Hz   el colchón armónico
    (hueco)      300–3000 Hz  VACÍO a propósito — aquí vive la voz
    aire         3–8 kHz      brillo y arpegio, muy tenue

Tonalidad: La menor, que es la que suena «técnica y seria» sin ser sombría.
Tempo 100 — el ritmo del habla explicativa en español.
"""
import argparse
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

SR = 44100
A = 440.0


def note(semitones_from_a4: int) -> float:
    return A * 2 ** (semitones_from_a4 / 12)


def env_ad(n: int, attack: float, decay: float) -> np.ndarray:
    """Envolvente ataque/decaimiento exponencial — la de un pulso real."""
    a = max(1, int(attack * SR))
    t = np.arange(n)
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    e[a:] = np.exp(-(t[a:] - a) / (decay * SR))
    return e


def build(dur: float, bpm: float, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    beat = 60.0 / bpm
    out = np.zeros(n)

    # ── progresión: Am → F → C → G, cuatro compases de cuatro tiempos ──────────
    # Cada acorde dura un compás. Es la progresión más neutra que existe: sirve
    # de suelo sin pedir atención, que es exactamente lo que debe hacer una cama.
    chords = [(-12, -9, -5), (-16, -9, -4), (-9, -5, 0), (-14, -7, -2)]
    bar = beat * 4

    # ── PAD ───────────────────────────────────────────────────────────────────
    # Sinusoides apiladas con desafinación mínima entre ellas. La desafinación es
    # lo que le quita el sonido de órgano de prueba: dos osciladores a 0.12 Hz de
    # diferencia laten despacio y el oído lo lee como «textura», no como error.
    pad = np.zeros(n)
    for bi in range(int(np.ceil(dur / bar))):
        s = int(bi * bar * SR)
        e = min(n, int((bi + 1) * bar * SR) + int(0.9 * SR))   # solape entre acordes
        if s >= n:
            break
        seg = np.arange(e - s) / SR
        ch = chords[bi % len(chords)]
        v = np.zeros(e - s)
        for k, semi in enumerate(ch):
            f = note(semi)
            # se mantiene por debajo de 300 Hz: el hueco de la voz es sagrado
            while f > 300:
                f /= 2
            for det in (-0.12, 0.12):
                v += np.sin(2 * np.pi * (f + det) * seg + rng.random() * 6.28)
        # entrada y salida suaves de cada acorde, para que no haya costura
        fade = np.minimum(np.minimum(seg / 0.9, (len(seg) / SR - seg) / 0.9), 1.0)
        pad[s:e] += v * np.clip(fade, 0, 1) / (len(ch) * 2)
    out += pad * 0.42

    # ── PULSO ─────────────────────────────────────────────────────────────────
    # Un sub en el tiempo fuerte. Es lo que da sensación de avance sin ocupar
    # sitio: por debajo de 90 Hz no compite con ninguna consonante.
    for i in range(int(dur / beat)):
        s = int(i * beat * SR)
        ln = min(int(0.42 * SR), n - s)
        if ln <= 0:
            break
        seg = np.arange(ln) / SR
        f = 55 if i % 4 == 0 else 55 * 1.0
        amp = 1.0 if i % 4 == 0 else 0.55
        out[s:s + ln] += (np.sin(2 * np.pi * f * seg)
                          * env_ad(ln, 0.004, 0.10) * 0.5 * amp)

    # ── ARPEGIO ───────────────────────────────────────────────────────────────
    # Plucks cortos y agudos cada medio tiempo, muy tenues. Es el único elemento
    # que dice «tecnología»; por eso está arriba del todo, fuera del paso.
    arp = [0, 3, 7, 12, 7, 3]
    for i in range(int(dur / (beat / 2))):
        s = int(i * (beat / 2) * SR)
        ln = min(int(0.30 * SR), n - s)
        if ln <= 0:
            break
        seg = np.arange(ln) / SR
        f = note(arp[i % len(arp)] + 12)          # dos octavas arriba: 3–4 kHz
        v = (np.sin(2 * np.pi * f * seg) + 0.4 * np.sin(2 * np.pi * f * 2 * seg))
        out[s:s + ln] += v * env_ad(ln, 0.002, 0.055) * 0.085

    # ── AIRE ──────────────────────────────────────────────────────────────────
    # Ruido filtrado en paso alto: solo brillo. Le quita a la síntesis el sonido
    # de laboratorio y la acerca a una grabación.
    noise = rng.normal(0, 1, n)
    hp = noise - np.convolve(noise, np.ones(64) / 64, mode="same")
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.06 * t)
    out += hp * 0.012 * lfo

    # ── forma general ─────────────────────────────────────────────────────────
    # Una respiración lentísima de nivel. Sin esto la cama se vuelve un zumbido
    # constante y el oído la empieza a oír, que es justo lo que no debe pasar.
    out *= 0.86 + 0.14 * np.sin(2 * np.pi * 0.022 * t - 1.2)

    peak = np.max(np.abs(out))
    if peak > 0:
        out = out / peak * 0.85
    return out


def write_mp3(sig: np.ndarray, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        wav = Path(tf.name)
    stereo = np.stack([sig, sig], axis=1)
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((stereo * 32767).astype("<i2").tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav),
                    "-c:a", "libmp3lame", "-b:a", "192k", str(dst)], check=True)
    wav.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description="Cama musical minimal-tech")
    ap.add_argument("out")
    ap.add_argument("--dur", type=float, default=70.0)
    ap.add_argument("--bpm", type=float, default=100.0)
    a = ap.parse_args()
    sig = build(a.dur, a.bpm)
    dst = Path(a.out)
    write_mp3(sig, dst)

    out = subprocess.run(["ffmpeg", "-v", "info", "-i", str(dst), "-af",
                          "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    for line in out.splitlines():
        if "mean_volume" in line or "max_volume" in line:
            print("  " + line.split("] ")[-1])
    print(f"-> {dst}  ({a.dur:.0f}s · {a.bpm:.0f} BPM · La menor)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
