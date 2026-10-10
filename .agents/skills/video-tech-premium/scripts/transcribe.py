#!/usr/bin/env python3
"""Transcribe audio con AssemblyAI y guarda el JSON completo (con timings por palabra).

    scripts/transcribe.py assets/audio/1.flac transcripts/1.json

La clave se lee de .env (ASSEMBLYAI_API_KEY) — nunca se pasa por argumento.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://api.assemblyai.com/v2"


def load_key() -> str:
    env = next((d / ".env" for d in (Path.cwd().resolve(), *Path.cwd().resolve().parents)
                if (d / ".env").exists()), Path(".env"))
    for line in env.read_text().splitlines():
        if line.startswith("ASSEMBLYAI_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("error: falta ASSEMBLYAI_API_KEY en .env")


def req(url, key, data=None, method="GET", raw=False):
    headers = {"authorization": key}
    if data is not None and not raw:
        headers["content-type"] = "application/json"
        data = json.dumps(data).encode()
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=300) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"error HTTP {e.code} en {url}\n{e.read().decode()[:600]}")


def main():
    src, dest = Path(sys.argv[1]), Path(sys.argv[2])
    key = load_key()

    print(f"subiendo {src.name} ({src.stat().st_size/1e6:.1f} MB)…", flush=True)
    upload_url = req(f"{BASE}/upload", key, src.read_bytes(), "POST", raw=True)["upload_url"]

    print("encolando transcripción (es, word-level timings)…", flush=True)
    job = req(f"{BASE}/transcript", key, {
        "audio_url": upload_url,
        "language_code": "es",
        "punctuate": True,
        "format_text": True,
        "disfluencies": True,   # conserva muletillas -> sirven para detectar trabas
    }, "POST")

    tid = job["id"]
    while True:
        t = req(f"{BASE}/transcript/{tid}", key)
        status = t["status"]
        if status == "completed":
            break
        if status == "error":
            sys.exit(f"error de AssemblyAI: {t.get('error')}")
        print(f"  … {status}", flush=True)
        time.sleep(3)

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(t, ensure_ascii=False, indent=2))
    words = t.get("words") or []
    print(f"\nlisto -> {dest}")
    print(f"palabras: {len(words)} · confianza: {t.get('confidence')}")
    print(f"duración audio: {t.get('audio_duration')} s")


if __name__ == "__main__":
    main()
