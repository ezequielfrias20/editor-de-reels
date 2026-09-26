#!/usr/bin/env python3
"""Chequeos mecánicos de videos/<n>/propuesta.json (pasada `propuesta` de editar-pieza).

    scripts/validar-propuesta.py --project . --piece 7

Lo que se comprueba es lo que no se puede inventar: que cada ancla se dijo, que un
componente o un logo marcado como existente existe, que hay una versión por CTA del
pedido y que el material nombrado es un clip del pedido. El criterio de edición vive en
la skill, no aquí. El dashboard lo corre al terminar la pasada.
"""
import argparse
import ast
import json
import re
import sys
import unicodedata
from pathlib import Path

from pieza import PiezaError, cargar_pedido


def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def componentes(root: Path) -> set[str]:
    """Lo que la banda de arriba puede mostrar, con el mismo criterio que el inventario de
    plan-edicion: los mockups públicos que devuelven un componente (`tuple[str, str, list]`)
    y los objetos de `objects.REGISTRY`, con su nombre de registro (`dental-chair`)."""
    nombres: set[str] = set()
    m = root / "scripts" / "mockups.py"
    if m.exists():
        for n in ast.parse(m.read_text()).body:
            if (isinstance(n, ast.FunctionDef) and not n.name.startswith("_") and n.returns is not None
                    and ast.unparse(n.returns).replace(" ", "") == "tuple[str,str,list]"):
                nombres.add(n.name)
    o = root / "scripts" / "objects.py"
    if o.exists():
        for n in ast.parse(o.read_text()).body:
            if (isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "REGISTRY" for t in n.targets)
                    and isinstance(n.value, ast.Dict)):
                nombres |= {k.value for k in n.value.keys
                            if isinstance(k, ast.Constant) and k.value != "motion_stage"}
    return nombres


def problemas(root: Path, n: int) -> list[str]:
    root = Path(root)
    f = root / "videos" / str(n) / "propuesta.json"
    if not f.exists():
        return [f"no existe videos/{n}/propuesta.json"]
    try:
        prop = json.loads(f.read_text())
    except json.JSONDecodeError as e:
        return [f"propuesta.json no es JSON válido: {e}"]
    try:
        pedido = cargar_pedido(root, n)
    except PiezaError as e:
        return [f"pedido: {e}"]

    out: list[str] = []
    tr = root / "transcripts" / f"{n}.json"
    dicho = normalizar(" ".join(w["text"] for w in json.loads(tr.read_text())["words"])) \
        if tr.exists() else ""
    if not dicho:
        out.append(f"no existe transcripts/{n}.json (o está vacío)")
    comps = componentes(root)
    meta = root / "assets" / "logos" / "meta.json"
    logos = set(json.loads(meta.read_text())) if meta.exists() else set()
    archivos = {c.archivo for c in pedido.clips}

    if prop.get("pieza") != n:
        out.append(f"pieza {prop.get('pieza')!r} no es {n}")
    if prop.get("paleta") != pedido.paleta:
        out.append(f"paleta {prop.get('paleta')!r} distinta de la del pedido ({pedido.paleta})")
    beats = prop.get("beats") or []
    if not beats:
        out.append("la propuesta no tiene beats")
    ids = set()
    for i, b in enumerate(beats):
        bid = b.get("id") or ""
        donde = f"beat {bid or i}"
        if not bid:
            out.append(f"beat {i} sin id")
        elif bid in ids:
            out.append(f"{donde}: id repetido")
        ids.add(bid)
        ancla = b.get("ancla", "")
        if not ancla or normalizar(ancla) not in dicho:
            out.append(f"{donde}: el ancla «{ancla}» no aparece en el transcript")
        comp = b.get("componente") or {}
        if comp.get("existe") and comp.get("nombre") not in comps:
            out.append(f"{donde}: el componente {comp.get('nombre')!r} no existe "
                       f"(márcalo con existe: false si hay que crearlo)")
        for lg in b.get("logos", []):
            if lg.get("estado") == "disponible" and lg.get("slug") not in logos:
                out.append(f"{donde}: el logo {lg.get('slug')!r} no está en assets/logos "
                           f"(márcalo descargar o bájalo con fetch-logos.py)")
        for m in b.get("material", []):
            if m not in archivos:
                out.append(f"{donde}: el material {m!r} no es un clip del pedido")
    for q in prop.get("preguntas", []):
        if not q.get("id") or not (q.get("propuesta_por_defecto") or "").strip():
            out.append(f"pregunta {q.get('id') or '?'}: falta id o propuesta_por_defecto")
        if q.get("beat") and q["beat"] not in ids:
            out.append(f"pregunta {q.get('id')}: el beat {q['beat']!r} no existe")
    pedidas = pedido.plataformas
    dadas = [v.get("plataforma") for v in prop.get("versiones", [])]
    for p in pedidas:
        if p not in dadas:
            out.append(f"falta la versión {p}")
    for p in dadas:
        if p not in pedidas:
            out.append(f"la versión {p} no está en el pedido")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Valida videos/<n>/propuesta.json")
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--piece", required=True, type=int)
    a = ap.parse_args(argv)
    ps = problemas(a.project.resolve(), a.piece)
    if ps:
        print(f"✗ {len(ps)} problema(s):")
        for p in ps:
            print(f"  - {p}")
        return 1
    print(f"✓ propuesta {a.piece} válida")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
