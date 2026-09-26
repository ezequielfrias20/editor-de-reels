#!/usr/bin/env python3
"""Arma una versión (cuerpo + CTA de una plataforma) de una pieza del dashboard.

    scripts/armar-version.py datos --piece 7 --plataforma instagram
        out/7-fuente.mov + el clip del CTA      → out/7-instagram-fuente.mov
        transcripts/7.json + 7-cta-instagram    → transcripts/7-instagram.json
        cuts/7.json + 7-cta-instagram           → cuts/7-instagram.json

    scripts/armar-version.py edl --piece 7 --plataforma instagram
        videos/7/edl-cuerpo.json + videos/7/cta-instagram.json → videos/7-instagram/edl.json

Con `--plataforma general` (pieza sin CTA) la versión es el cuerpo solo.
Ver versiones.py para el porqué de la línea de tiempo.
"""
import argparse
import json
import sys
from pathlib import Path

from edl_words import load_words
from pieza import PiezaError, cargar_pedido, probe, unir
from versiones import unir_cortes, unir_edl, unir_transcripts, version_id


def _leer(p: Path) -> dict:
    if not p.exists():
        raise PiezaError(f"falta {p}: corre antes la pasada propuesta")
    return json.loads(p.read_text())


def _escribir(p: Path, data: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def datos(root: Path, n: int, plat: str) -> str:
    pedido = cargar_pedido(root, n)
    if plat not in pedido.plataformas:
        raise PiezaError(f"la pieza {n} no tiene CTA para {plat} "
                         f"(sus versiones: {', '.join(pedido.plataformas)})")
    v = version_id(n, plat)
    fuente = root / "out" / f"{n}-fuente.mov"
    if not fuente.exists():
        raise PiezaError(f"falta {fuente}: corre antes scripts/unir-cuerpo.py --piece {n}")
    tr_c, cu_c = _leer(root / "transcripts" / f"{n}.json"), _leer(root / "cuts" / f"{n}.json")
    if plat == "general":
        unir([fuente], root / "out" / f"{v}-fuente.mov")
        tr_x = cu_x = None
        offset = 0.0
    else:
        cta = next(c for c in pedido.de_rol("cta") if c.plataforma == plat)
        tr_x = _leer(root / "transcripts" / f"{n}-cta-{plat}.json")
        cu_x = _leer(root / "cuts" / f"{n}-cta-{plat}.json")
        # El CTA empieza donde termina la fuente del cuerpo en la concatenación.
        offset = probe(fuente).duracion
        unir([fuente, pedido.ruta(cta)], root / "out" / f"{v}-fuente.mov")
    _escribir(root / "transcripts" / f"{v}.json", unir_transcripts(tr_c, tr_x, offset))
    _escribir(root / "cuts" / f"{v}.json", unir_cortes(cu_c, cu_x, offset))
    return f"✓ {v}: fuente, transcript y cortes (CTA desde {offset:.3f} s)"


def _vigente(root: Path, n: int, plat: str) -> None:
    """La versión se armó con el cuerpo de AHORA. Si después se corrigió el transcript (una
    marca mal oída, palabras fundidas) o se recortó de nuevo, sus archivos quedaron viejos."""
    v = version_id(n, plat)
    tr_c, cu_c = _leer(root / "transcripts" / f"{n}.json"), _leer(root / "cuts" / f"{n}.json")
    tr_v, cu_v = _leer(root / "transcripts" / f"{v}.json"), _leer(root / "cuts" / f"{v}.json")
    if (tr_v["words"][:len(tr_c["words"])] != tr_c["words"]
            or cu_v["keeps"][:len(cu_c["keeps"])] != cu_c["keeps"]):
        raise PiezaError(f"la versión {v} quedó vieja: cambió transcripts/{n}.json o cuts/{n}.json "
                         f"después de prepararla. Corre scripts/preparar-version.sh {n} {plat}")


def edl(root: Path, n: int, plat: str) -> str:
    v = version_id(n, plat)
    _vigente(root, n, plat)
    cuerpo = _leer(root / "videos" / str(n) / "edl-cuerpo.json")
    palabras_cuerpo = len(_leer(root / "transcripts" / f"{n}.json")["words"])
    if plat == "general":
        segs, palabras_cta = [], 0
    else:
        segs = _leer(root / "videos" / str(n) / f"cta-{plat}.json")["segments"]
        palabras_cta = len(_leer(root / "transcripts" / f"{n}-cta-{plat}.json")["words"])
    words_rel, cuts_rel = f"transcripts/{v}.json", f"cuts/{v}.json"
    fp = load_words(root / words_rel, root / cuts_rel).fingerprint
    try:
        out = unir_edl(cuerpo, segs, palabras_cuerpo, palabras_cta, v, words_rel, cuts_rel, fp)
    except ValueError as e:
        raise PiezaError(str(e)) from e
    _escribir(root / "videos" / v / "edl.json", out)
    return f"✓ videos/{v}/edl.json · {len(out['segments'])} segmentos"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Arma una versión cuerpo + CTA")
    ap.add_argument("que", choices=("datos", "edl"))
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--piece", required=True, type=int)
    ap.add_argument("--plataforma", required=True)
    a = ap.parse_args(argv)
    try:
        fn = datos if a.que == "datos" else edl
        print(fn(a.project.resolve(), a.piece, a.plataforma))
    except PiezaError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
