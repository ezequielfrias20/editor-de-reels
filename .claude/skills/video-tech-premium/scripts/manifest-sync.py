#!/usr/bin/env python3
"""Recalcula los hashes de `assets/manifest.json` y FALLA si un `@n` que ya
existía cambió — es la garantía de inmutabilidad, hecha ejecutable.

    scripts/manifest-sync.py [--project .] [--write]

Sin `--write`: solo compara y reporta. Con `--write`: además añade hashes a
entradas nuevas que no traían uno (alta de un asset), pero SIGUE fallando si
una entrada YA HASHEADA no cuadra con su código — eso nunca se autocorrige
solo, porque autocorregirlo sería exactamente el bug que existe para cazar:
un `@n` editado en silencio.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asset_resolve import asset_hash, load_manifest  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verifica/recalcula assets/manifest.json")
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--write", action="store_true",
                    help="escribe los hashes que faltan (altas nuevas); nunca "
                         "sobrescribe uno que ya existía")
    a = ap.parse_args(argv)

    root = a.project.resolve()
    path = root / "assets" / "manifest.json"
    manifest = load_manifest(path)

    problems: list[str] = []
    altas = 0
    for ref, entry in sorted(manifest["assets"].items()):
        real = asset_hash(ref, manifest)
        stored = entry.get("hash")
        if stored is None:
            if a.write:
                entry["hash"] = real
                altas += 1
                print(f"  + {ref}  (hash nuevo)")
            else:
                problems.append(f"'{ref}' no tiene hash — corre con --write")
        elif stored != real:
            problems.append(
                f"'{ref}' CAMBIÓ: el manifest dice {stored}, el código da {real}. "
                f"Un @n es inmutable — si el rediseño es intencionado, sube la "
                f"versión (@{int(ref.rsplit('@', 1)[1]) + 1}) en vez de editar esta")
        else:
            print(f"  ✓ {ref}")

    if problems:
        print(f"\n✗ {len(problems)} problema(s):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    if a.write and altas:
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2,
                                   sort_keys=True) + "\n")
        print(f"\n✓ {altas} hash(es) nuevo(s) escritos en {path}")
    else:
        print(f"\n✓ {len(manifest['assets'])} asset(s), todos en orden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
