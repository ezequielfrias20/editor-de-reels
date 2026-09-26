"""Clips sintéticos de pocos segundos para probar la unión sin metraje real."""
import shutil
import subprocess
from pathlib import Path

import pytest

necesita_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="sin ffmpeg")


def clip(path: Path, dur: float = 1.0, w: int = 320, h: int = 568, fps: int = 30,
         freq: int = 440, audio_dur: float | None = None, ar: int = 44100, ac: int = 1) -> Path:
    """Video testsrc2 + tono puro. h > w = vertical, como un reel.

    `audio_dur` distinto de `dur` imita el footage real, donde el audio y el video casi
    nunca miden lo mismo."""
    path.parent.mkdir(parents=True, exist_ok=True)
    a = dur if audio_dur is None else audio_dur
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y",
         "-f", "lavfi", "-i", f"testsrc2=size={w}x{h}:rate={fps}:duration={dur}",
         "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={a}:sample_rate={ar}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ac", str(ac), "-ar", str(ar),
         *(["-shortest"] if audio_dur is None else []), str(path)],
        check=True)
    return path


def inicio_tono(path: Path, freq: int, sr: int = 16000) -> float:
    """Segundo en que el tono `freq` pasa a dominar el audio (ventanas de 10 ms)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    n = sr // 100
    t = np.arange(n) / sr
    ref = np.exp(-2j * np.pi * freq * t)
    for i in range(0, len(x) - n, n):
        w = x[i:i + n]
        if np.sqrt(np.mean(w ** 2)) > 0.05 and abs(np.dot(w, ref)) / n > 0.25 * np.sqrt(np.mean(w ** 2)):
            return i / sr
    raise AssertionError(f"no encontré el tono de {freq} Hz en {path}")


def duracion(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())
