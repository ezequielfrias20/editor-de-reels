#!/usr/bin/env python3
"""Arma una versión (cuerpo + CTA de una plataforma) de una pieza del dashboard.

    scripts/armar-version.py datos --piece 7 --plataforma instagram
        out/7-fuente.mov + el clip del CTA      → out/7-instagram-fuente.mov
        transcripts/7.json + 7-cta-instagram    → transcripts/7-instagram.json
        cuts/7.json + 7-cta-instagram           → cuts/7-instagram.json

    scripts/armar-version.py edl --piece 7 --plataforma instagram
        videos/7/edl-cuerpo.json + videos/7/cta-instagram.json → videos/7-instagram/edl.json

    scripts/armar-version.py plan --piece 7 --plataforma instagram
        videos/7/plan-cuerpo.json + videos/7/plan-cta-instagram.json → videos/7-instagram/plan.json
        (el camino del triband: la banda de arriba no la emite el EDL, va a mano en el plan)

    scripts/armar-version.py palabras --piece 7 --plataforma instagram
        cada palabra de la versión con sus tiempos YA remapeados al corte, y dónde arranca el CTA

    scripts/armar-version.py anchor --piece 7 --plataforma instagram
        el rango de `anchor` que deja entera la cara de assets/face-7-instagram.json en la banda

Las versiones son siempre `instagram` y `tiktok`; cada una corta el cuerpo donde empieza el
CTA dicho en él (videos/7/cta-cuerpo.json) y le suma su CTA. Ver versiones.py.
"""
import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from edl_words import load_words
from pieza import PiezaError, cargar_pedido, probe, unir
from versiones import (anchor_recomendado, leer_cta_cuerpo, rango_anchor, recortar_cuerpo, unir_cortes,
                       unir_edl, unir_plan, unir_transcripts, version_id)

SPEAKER = [960, 1920]  # la banda `speaker` de la doctrina, si plan-cuerpo.json aún no la declara


def _leer(p: Path) -> dict:
    if not p.exists():
        raise PiezaError(f"falta {p}: corre antes la pasada propuesta")
    return json.loads(p.read_text())


def _escribir(p: Path, data: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


@dataclass(frozen=True)
class Armado:
    """Lo que es una versión, calculado del pedido, el cuerpo y cta-cuerpo.json."""
    fuentes: list[Path]
    transcript: dict
    cortes: dict
    comun: int          # palabras de la parte común; el CTA (si hay) empieza en esta
    fin_comun: float    # segundos del corte donde termina la parte común
    tiene_cta: bool


def _cta_cuerpo(root: Path, n: int, tr_c: dict) -> int | None:
    f = root / "videos" / str(n) / "cta-cuerpo.json"
    if not f.exists():
        raise PiezaError(f"falta videos/{n}/cta-cuerpo.json: la pasada propuesta anota ahí en qué "
                         f"palabra empieza el CTA de Instagram dicho en el cuerpo "
                         f'({{"desde_palabra": null}} si el cuerpo no lo dice)')
    try:
        return leer_cta_cuerpo(json.loads(f.read_text()), tr_c["words"])
    except ValueError as e:
        raise PiezaError(f"videos/{n}/cta-cuerpo.json: {e}") from e


def _armar(root: Path, n: int, plat: str) -> Armado:
    pedido = cargar_pedido(root, n)
    if plat not in pedido.plataformas:
        raise PiezaError(f"no hay versión {plat}: salen {', '.join(pedido.plataformas)}")
    fuente = root / "out" / f"{n}-fuente.mov"
    if not fuente.exists():
        raise PiezaError(f"falta {fuente}: corre antes scripts/unir-cuerpo.py --piece {n}")
    tr_c, cu_c = _leer(root / "transcripts" / f"{n}.json"), _leer(root / "cuts" / f"{n}.json")
    k = _cta_cuerpo(root, n, tr_c)
    tr_com, cu_com = recortar_cuerpo(tr_c, cu_c, k)
    comun, fin = len(tr_com["words"]), cu_com["final_duration"]
    clip = pedido.cta(plat)
    if clip is None:
        if plat == "instagram" and k is not None:   # el CTA es el que se dijo en el cuerpo
            return Armado([fuente], tr_c, cu_c, comun, fin, True)
        return Armado([fuente], tr_com, cu_com, comun, fin, False)
    tr_x = _leer(root / "transcripts" / f"{n}-cta-{plat}.json")
    cu_x = _leer(root / "cuts" / f"{n}-cta-{plat}.json")
    # El clip empieza donde termina la fuente del cuerpo en la concatenación; el CTA dicho en
    # el cuerpo sigue en la fuente, pero sus `keeps` ya no están.
    offset = probe(fuente).duracion
    return Armado([fuente, pedido.ruta(clip)], unir_transcripts(tr_com, tr_x, offset),
                  unir_cortes(cu_com, cu_x, offset), comun, fin, True)


def datos(root: Path, n: int, plat: str) -> str:
    v = version_id(n, plat)
    a = _armar(root, n, plat)
    unir(a.fuentes, root / "out" / f"{v}-fuente.mov")
    _escribir(root / "transcripts" / f"{v}.json", a.transcript)
    _escribir(root / "cuts" / f"{v}.json", a.cortes)
    cta = f"CTA desde {a.fin_comun:.3f} s del corte" if a.tiene_cta else "sin CTA"
    return f"✓ {v}: fuente, transcript y cortes ({a.cortes['final_duration']:.3f} s, {cta})"


def _vigente(root: Path, n: int, plat: str) -> Armado:
    """La versión se armó con el cuerpo de AHORA. Si después se corrigió el transcript (una
    marca mal oída, palabras fundidas), se recortó de nuevo o se movió el CTA del cuerpo, sus
    archivos quedaron viejos."""
    v = version_id(n, plat)
    a = _armar(root, n, plat)
    tr_v, cu_v = _leer(root / "transcripts" / f"{v}.json"), _leer(root / "cuts" / f"{v}.json")
    if tr_v["words"] != a.transcript["words"] or cu_v["keeps"] != a.cortes["keeps"]:
        raise PiezaError(f"la versión {v} quedó vieja: cambió transcripts/{n}.json, cuts/{n}.json "
                         f"o videos/{n}/cta-cuerpo.json después de prepararla. Corre "
                         f"scripts/preparar-version.sh {n} {plat}")
    return a


def edl(root: Path, n: int, plat: str) -> str:
    v = version_id(n, plat)
    a = _vigente(root, n, plat)
    cuerpo = _leer(root / "videos" / str(n) / "edl-cuerpo.json")
    palabras_cta = len(a.transcript["words"]) - a.comun
    segs = _leer(root / "videos" / str(n) / f"cta-{plat}.json")["segments"] if a.tiene_cta else []
    words_rel, cuts_rel = f"transcripts/{v}.json", f"cuts/{v}.json"
    fp = load_words(root / words_rel, root / cuts_rel).fingerprint
    try:
        out = unir_edl(cuerpo, segs, a.comun, palabras_cta, v, words_rel, cuts_rel, fp)
    except ValueError as e:
        raise PiezaError(str(e)) from e
    _escribir(root / "videos" / v / "edl.json", out)
    return f"✓ videos/{v}/edl.json · {len(out['segments'])} segmentos"


def plan(root: Path, n: int, plat: str) -> str:
    v = version_id(n, plat)
    a = _vigente(root, n, plat)
    cuerpo = _leer(root / "videos" / str(n) / "plan-cuerpo.json")
    paleta = cargar_pedido(root, n).paleta
    if cuerpo.get("palette") != paleta:
        raise PiezaError(f"plan-cuerpo.json declara la paleta {cuerpo.get('palette')!r} y el "
                         f"pedido pide {paleta!r}: la paleta la elige el pedido")
    f_cta = root / "videos" / str(n) / f"plan-cta-{plat}.json"
    if not a.tiene_cta and f_cta.exists():
        raise PiezaError(f"la versión {v} no tiene CTA (ni clip ni CTA dicho que le toque): "
                         f"borra videos/{n}/plan-cta-{plat}.json")
    cta = _leer(f_cta) if a.tiene_cta else None
    try:
        out = unir_plan(cuerpo, cta, a.fin_comun)
    except ValueError as e:
        raise PiezaError(str(e)) from e
    _escribir(root / "videos" / v / "plan.json", out)
    return (f"✓ videos/{v}/plan.json · {len(out.get('shots', []))} encuadres · "
            f"{len(out.get('visuals', []))} visuales · {len(out.get('sfx', []))} efectos")


def palabras(root: Path, n: int, plat: str) -> str:
    v = version_id(n, plat)
    a = _vigente(root, n, plat)
    tabla = load_words(root / "transcripts" / f"{v}.json", root / "cuts" / f"{v}.json")
    cta = "" if a.tiene_cta else " · sin CTA"
    filas = [f"{v} · {tabla.duration:.3f} s en el corte{cta} · índice, inicio, fin, palabra"]
    for i, w in enumerate(tabla.words):
        if i == a.comun:
            filas.append(f"── CTA desde {a.fin_comun:.3f} s (palabra {a.comun}) ──")
        filas.append(f"{i:4d}  {w.start:8.3f}  {w.end:8.3f}  {w.text}")
    return "\n".join(filas)


def anchor(root: Path, n: int, plat: str) -> str:
    v = version_id(n, plat)
    face = _leer(root / "assets" / f"face-{v}.json")
    pc = root / "videos" / str(n) / "plan-cuerpo.json"
    speaker = _leer(pc).get("layout", {}).get("bands", {}).get("speaker", SPEAKER) if pc.exists() else SPEAKER
    lo, hi = rango_anchor(face, speaker)
    a = anchor_recomendado(lo, hi)
    if a is None:
        # La cara es más alta que la banda: se prioriza no cortarla (el gate que para el
        # render) y la barbilla entra en la zona de la interfaz de la plataforma.
        a = round(hi, 4)
        h = speaker[1] - speaker[0]
        sobra = face["height"] * max(1080 / face["width"], h / face["height"]) - h
        baja = (lo - hi) * sobra
        return (f"⚠ {v}: la cara no entra entera sobre y1536 en la banda {speaker} "
                f"(haría falta anchor ≥ {lo:.4f} y ≤ {hi:.4f}). anchor {a} deja la cara sin cortar "
                f"y la barbilla {baja:.0f} px dentro de la zona de la interfaz: la toma está "
                f"demasiado cerca de la cámara")
    return f"✓ {v}: anchor válido en [{lo:.4f}, {hi:.4f}] · usa anchor {a}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Arma una versión cuerpo + CTA")
    ap.add_argument("que", choices=("datos", "edl", "plan", "palabras", "anchor"))
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--piece", required=True, type=int)
    ap.add_argument("--plataforma", required=True)
    a = ap.parse_args(argv)
    try:
        fn = {"datos": datos, "edl": edl, "plan": plan, "palabras": palabras, "anchor": anchor}[a.que]
        print(fn(a.project.resolve(), a.piece, a.plataforma))
    except PiezaError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
