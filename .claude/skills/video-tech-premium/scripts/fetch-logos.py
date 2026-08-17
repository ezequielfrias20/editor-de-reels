#!/usr/bin/env python3
"""Vendoriza marcas monocromas desde Simple Icons v16."""
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path.cwd().resolve()
OUT = ROOT / "assets" / "logos"
KNOWN = {
    "whatsapp": ("WhatsApp", "25D366", "16"),
    # Microsoft retired this glyph from later Simple Icons catalogs. Pin the
    # last verified package family instead of substituting an invented mark.
    "microsoftexcel": ("Microsoft Excel", "217346", "12.4.0"),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta_path = OUT / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    for slug in sys.argv[1:]:
        if slug not in KNOWN:
            raise SystemExit(f"slug no verificado en Simple Icons v16: {slug}")
        title, hx, version = KNOWN[slug]
        url = f"https://cdn.jsdelivr.net/npm/simple-icons@{version}/icons/{slug}.svg"
        req = urllib.request.Request(url, headers={"User-Agent": "editor-videos/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
        root = ET.fromstring(raw)
        paths = [n for n in root.iter() if n.tag.rsplit("}", 1)[-1] == "path"]
        if root.attrib.get("viewBox") != "0 0 24 24" or len(paths) != 1:
            raise SystemExit(f"{slug}: contrato SVG inesperado")
        (OUT / f"{slug}.svg").write_bytes(raw)
        meta[slug] = {"title": title, "hex": hx, "source": url,
                      "simple_icons_version": version}
        print(f"{slug} → assets/logos/{slug}.svg")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
