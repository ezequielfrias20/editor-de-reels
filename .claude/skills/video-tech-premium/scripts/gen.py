#!/usr/bin/env python3
"""Registro unificado de assets generados fuera del shell.

Higgsfield vive como conector, por lo que el agente genera allí y este script
descarga el resultado y lo incorpora al ledger compartido con ``kie.py``.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

import kie


def import_asset(a: argparse.Namespace) -> None:
    out = Path(a.out)
    if not out.is_absolute():
        out = kie.ROOT / out
    params = json.loads(a.params)
    ck = kie.cache_key(out, a.model, a.prompt, params)
    if not kie.cached(out, ck):
        kie.download(a.url, out)
        kie.ledger_put(ck, {
            "file": str(out.relative_to(kie.ROOT)),
            "provider": a.provider,
            "kind": a.kind,
            "model": a.model,
            "prompt": a.prompt,
            "params": params,
            "taskId": a.task,
            "credits": a.credits,
            "source": a.url,
            "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    print(f"importado {out.relative_to(kie.ROOT)} [{a.provider} · {a.model} · {a.credits:g} cr]")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    imp = sub.add_parser("import")
    imp.add_argument("--url", required=True)
    imp.add_argument("--out", required=True)
    imp.add_argument("--provider", required=True)
    imp.add_argument("--model", required=True)
    imp.add_argument("--task", required=True)
    imp.add_argument("--prompt", required=True)
    imp.add_argument("--params", default="{}")
    imp.add_argument("--credits", type=float, required=True)
    imp.add_argument("--kind", choices=("image", "video"), default="image")
    a = ap.parse_args()
    if a.cmd == "import":
        import_asset(a)


if __name__ == "__main__":
    main()
