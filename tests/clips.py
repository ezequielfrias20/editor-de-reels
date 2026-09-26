"""Clips sintéticos de pocos segundos para probar la unión sin metraje real."""
import shutil
import subprocess
from pathlib import Path

import pytest

necesita_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="sin ffmpeg")


def clip(path: Path, dur: float = 1.0, w: int = 320, h: int = 568, fps: int = 30,
         freq: int = 440) -> Path:
    """Video testsrc2 + tono puro. h > w = vertical, como un reel."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y",
         "-f", "lavfi", "-i", f"testsrc2=size={w}x{h}:rate={fps}:duration={dur}",
         "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={dur}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path)],
        check=True)
    return path


def duracion(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())
