#!/usr/bin/env python3
"""Valida, renderiza y entrega una versión de una pieza del dashboard.

    scripts/renderizar-version.py --piece 7 --plataforma instagram --version 1

En videos/7-instagram/: `npx hyperframes check public`, después
`npx hyperframes render public --skill=talking-head-recut -o output.mp4 --fps 30 --sdr`,
y copia el resultado a videos/7/output-instagram-v1.mp4 y a
VIDEOS EDITADOS/7-instagram-v1.mp4. Antes hay que haber compuesto la versión
(build-composition.py --piece 7-instagram). Cierra apps antes: el render usa mucha memoria.
"""
import argparse
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

from versiones import version_id


def entregar(root: Path, n: int, plataforma: str, k: int) -> tuple[Path, Path]:
    v = version_id(n, plataforma)
    render = root / "videos" / v / "output.mp4"
    if not render.exists():
        raise FileNotFoundError(f"no existe {render}")
    a = root / "videos" / str(n) / f"output-{plataforma}-v{k}.mp4"
    b = root / "VIDEOS EDITADOS" / f"{v}-v{k}.mp4"
    for destino in (a, b):
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(render, destino)
    return a, b


def _hf(args: list[str], cwd: Path) -> None:
    cmd = shlex.split(os.environ.get("HYPERFRAMES", "npx hyperframes")) + args
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        raise RuntimeError(f"`hyperframes {args[0]}` falló ({r.returncode}): "
                           f"{(r.stderr or r.stdout).strip()[-500:]}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Renderiza y entrega una versión")
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--piece", required=True, type=int)
    ap.add_argument("--plataforma", required=True)
    ap.add_argument("--version", required=True, type=int)
    a = ap.parse_args(argv)
    root = a.project.resolve()
    work = root / "videos" / version_id(a.piece, a.plataforma)
    try:
        if not (work / "public").exists():
            raise RuntimeError(f"no existe {work}/public: compón antes con "
                               f"build-composition.py --piece {work.name}")
        inicio = time.time()
        _hf(["check", "public"], work)
        _hf(["render", "public", "--skill=talking-head-recut", "-o", "output.mp4",
             "--fps", "30", "--sdr"], work)
        out = work / "output.mp4"
        # un output.mp4 de un render anterior no puede entregarse como si fuera de este
        if not out.exists() or out.stat().st_mtime < inicio:
            raise RuntimeError(f"el render terminó sin escribir {out}")
        a_, b_ = entregar(root, a.piece, a.plataforma, a.version)
    except (RuntimeError, FileNotFoundError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"✓ {a_.relative_to(root)} · {b_.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
