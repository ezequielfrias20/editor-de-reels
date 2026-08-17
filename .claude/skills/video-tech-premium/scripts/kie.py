#!/usr/bin/env python3
"""Generación de assets con Kie AI — imágenes y animaciones — con caché y ledger.

    scripts/kie.py credits
    scripts/kie.py image --prompt "..." --ratio 9:16 --out assets/gen/hero.png
    scripts/kie.py video --prompt "..." --ratio 9:16 --dur 8 --out assets/gen/hero.mp4

Dos rutas distintas en la API de Kie, no una sola:

  · IMAGEN  → API unificada de jobs.  POST /api/v1/jobs/createTask con
    `model: google/nano-banana`, y se sondea con GET /api/v1/jobs/recordInfo.
  · VIDEO   → endpoint dedicado.      POST /api/v1/veo/generate
    (`model: veo3_fast|veo3|veo3_lite`), y se sondea con GET /api/v1/veo/record-info.

Los nombres de modelo de video NO existen en la API de jobs: `veo3_fast` allí
devuelve 422 «model not supported». Es el error fácil de cometer.

Caché: la clave es el hash de (ruta, modelo, prompt, parámetros). Si el archivo ya
está y la clave coincide, no se regenera ni se gastan créditos — así el pipeline
se puede volver a correr entero sin pagar dos veces. `--force` lo salta.

Cada generación queda anotada en assets/gen/ledger.json con prompt, modelo,
créditos gastados y taskId, para poder reproducir o auditar cualquier asset.
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

def _project_root() -> Path:
    """El PROYECTO es el directorio de trabajo, no donde vive el script.

    Estos scripts viajan dentro de la skill, así que `Path(__file__).parent.parent`
    apunta a la skill y no al proyecto que se está editando. Se ejecutan siempre
    desde la raíz del proyecto; si hay un .env más arriba, se sube a buscarlo.
    """
    cwd = Path.cwd().resolve()
    for d in (cwd, *cwd.parents):
        if (d / ".env").exists() or (d / "VIDEOS ORIGINALES").is_dir():
            return d
    return cwd


ROOT = _project_root()
GEN = ROOT / "assets" / "gen"
LEDGER = GEN / "ledger.json"
BASE = "https://api.kie.ai"

IMAGE_MODEL = "google/nano-banana"
VIDEO_MODEL_DEFAULT = "veo3_fast"

# nano-banana acepta la relación como cadena; un valor inválido no falla en la
# llamada sino en la tarea, minutos después. Se valida aquí.
IMAGE_RATIOS = {"1:1", "9:16", "16:9", "3:4", "4:3", "2:3", "3:2", "5:4", "4:5", "21:9", "auto"}
VIDEO_RATIOS = {"9:16", "16:9", "Auto"}
VIDEO_DURATIONS = {4, 6, 8}


def key() -> str:
    k = os.environ.get("KIE_API_KEY")
    if not k:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("KIE_API_KEY="):
                    k = line.split("=", 1)[1].strip()
                    break
    if not k:
        sys.exit("falta KIE_API_KEY (ponla en .env)")
    return k


def call(method: str, path: str, body: dict | None = None, timeout: int = 60) -> dict:
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {key()}")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} en {path}: {e.read().decode()[:400]}")
    except urllib.error.URLError as e:
        raise SystemExit(f"red caída al llamar {path}: {e.reason}")


def credits() -> float:
    return float(call("GET", "/api/v1/chat/credit")["data"])


# ── caché y ledger ────────────────────────────────────────────────────────────
def cache_key(out: Path, model: str, prompt: str, params: dict) -> str:
    blob = json.dumps([str(out), model, prompt, params], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def ledger_load() -> dict:
    if LEDGER.exists():
        try:
            return json.loads(LEDGER.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def ledger_put(ck: str, rec: dict) -> None:
    led = ledger_load()
    led[ck] = rec
    GEN.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, indent=2, ensure_ascii=False), encoding="utf-8")


def cached(out: Path, ck: str) -> bool:
    return out.exists() and out.stat().st_size > 0 and ck in ledger_load()


def download(url: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "editor-videos/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r, open(out, "wb") as f:
        while chunk := r.read(1 << 16):
            f.write(chunk)


def result_urls(result_json: str) -> list[str]:
    """El resultado viene como JSON serializado dentro del JSON. Varía de forma
    según el modelo: resultUrls, urls, o una lista suelta."""
    if not result_json:
        return []
    try:
        d = json.loads(result_json)
    except json.JSONDecodeError:
        return []
    if isinstance(d, list):
        return [u for u in d if isinstance(u, str)]
    for f in ("resultUrls", "urls", "resultUrl", "url", "videoUrl", "imageUrls"):
        v = d.get(f)
        if isinstance(v, str):
            return [v]
        if isinstance(v, list) and v:
            return [u for u in v if isinstance(u, str)]
    return []


def veo_urls(d: dict) -> list[str]:
    """Veo devuelve el resultado en `response.resultUrls`, ya deserializado —
    no en el `resultJson` serializado que usa la API de jobs."""
    resp = d.get("response") or {}
    for f in ("resultUrls", "fullResultUrls", "full_result_urls", "originUrls"):
        v = resp.get(f)
        if isinstance(v, list) and v:
            return [u for u in v if isinstance(u, str)]
        if isinstance(v, str):
            return [v]
    return result_urls(d.get("resultJson", ""))


def poll(get_path: str, task_id: str, label: str, budget: int) -> dict:
    """Sondea hasta que la tarea acabe. Devuelve el data crudo.

    Sube el intervalo poco a poco: las imágenes tardan ~10-20 s y los videos
    varios minutos, y no tiene sentido machacar la API para el segundo caso.
    """
    t0, wait = time.time(), 3.0
    while True:
        d = call("GET", f"{get_path}?taskId={urllib.parse.quote(task_id)}")["data"]

        # Las dos rutas de Kie NO informan el estado igual y ese es el error caro:
        #   · jobs/recordInfo → `state`: "waiting" | "success" | "fail"
        #   · veo/record-info → `successFlag`: 0 generando · 1 listo · 2-3 falló,
        #     y NO trae ningún campo `state`. Sondear solo por `state` deja el
        #     video colgado hasta el timeout aunque haya terminado en un minuto
        #     — y los créditos ya se gastaron.
        state = str(d.get("state") or d.get("status") or "").lower()
        flag = d.get("successFlag")
        if flag is not None:
            state = {0: "generando", 1: "success", 2: "fail", 3: "fail"}.get(int(flag), "generando")

        if state in ("success", "succeeded", "completed"):
            return d
        if state in ("fail", "failed", "error"):
            raise SystemExit(
                f"{label}: la tarea falló ({d.get('failCode') or d.get('errorCode')}) "
                f"{d.get('failMsg') or d.get('errorMessage')}")
        el = time.time() - t0
        if el > budget:
            raise SystemExit(f"{label}: sin resultado tras {budget}s (estado «{state}», task {task_id})")
        print(f"   · {label}: {state or 'en cola'} … {el:.0f}s", flush=True)
        time.sleep(wait)
        wait = min(wait * 1.35, 20.0)


# ── generadores ───────────────────────────────────────────────────────────────
def gen_image(prompt: str, ratio: str, out: Path, force: bool) -> Path:
    if ratio not in IMAGE_RATIOS:
        sys.exit(f"ratio de imagen inválido: {ratio} (usa {sorted(IMAGE_RATIOS)})")
    params = {"image_size": ratio, "output_format": "png"}
    ck = cache_key(out, IMAGE_MODEL, prompt, params)
    if cached(out, ck) and not force:
        print(f"⋯ caché  {out.relative_to(ROOT)}")
        return out

    print(f"→ imagen {out.name}  [{ratio}]  {prompt[:64]}…", flush=True)
    r = call("POST", "/api/v1/jobs/createTask",
             {"model": IMAGE_MODEL, "input": {"prompt": prompt, **params}})
    if r.get("code") != 200:
        sys.exit(f"createTask falló: {r.get('msg')}")
    tid = r["data"]["taskId"]
    d = poll("/api/v1/jobs/recordInfo", tid, out.name, budget=420)

    urls = result_urls(d.get("resultJson", ""))
    if not urls:
        sys.exit(f"{out.name}: la tarea acabó sin URL de resultado — {str(d)[:300]}")
    download(urls[0], out)
    cost = float(d.get("creditsConsumed") or 0)
    ledger_put(ck, dict(file=str(out.relative_to(ROOT)), kind="image", model=IMAGE_MODEL,
                        prompt=prompt, params=params, taskId=tid, credits=cost,
                        source=urls[0], at=time.strftime("%Y-%m-%d %H:%M:%S")))
    print(f"✓ {out.relative_to(ROOT)}  ({out.stat().st_size // 1024} KB, {cost:g} créditos)")
    return out


def gen_video(prompt: str, ratio: str, dur: int, out: Path, model: str,
              resolution: str, force: bool) -> Path:
    if ratio not in VIDEO_RATIOS:
        sys.exit(f"ratio de video inválido: {ratio} (usa {sorted(VIDEO_RATIOS)})")
    if dur not in VIDEO_DURATIONS:
        sys.exit(f"duración inválida: {dur} (usa {sorted(VIDEO_DURATIONS)})")
    params = {"aspect_ratio": ratio, "duration": dur, "model": model, "resolution": resolution}
    ck = cache_key(out, model, prompt, params)
    if cached(out, ck) and not force:
        print(f"⋯ caché  {out.relative_to(ROOT)}")
        return out

    print(f"→ video  {out.name}  [{ratio} {dur}s {model}]  {prompt[:56]}…", flush=True)
    body = {"prompt": prompt, "model": model, "aspect_ratio": ratio,
            "duration": dur, "resolution": resolution, "enableTranslation": False}
    r = call("POST", "/api/v1/veo/generate", body)
    if r.get("code") != 200:
        sys.exit(f"veo/generate falló: {r.get('msg')}")
    tid = r["data"]["taskId"]
    # Veo tarda minutos, no segundos.
    d = poll("/api/v1/veo/record-info", tid, out.name, budget=1200)

    urls = veo_urls(d)
    if not urls:
        sys.exit(f"{out.name}: la tarea acabó sin URL de resultado — {str(d)[:300]}")
    download(urls[0], out)
    cost = float(d.get("creditsConsumed") or 0)
    ledger_put(ck, dict(file=str(out.relative_to(ROOT)), kind="video", model=model,
                        prompt=prompt, params=params, taskId=tid, credits=cost,
                        source=urls[0], at=time.strftime("%Y-%m-%d %H:%M:%S")))
    print(f"✓ {out.relative_to(ROOT)}  ({out.stat().st_size // 1024} KB, {cost:g} créditos)")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Generación de assets con Kie AI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("credits", help="créditos disponibles")

    pi = sub.add_parser("image", help="genera una imagen (nano-banana)")
    pi.add_argument("--prompt", required=True)
    pi.add_argument("--ratio", default="9:16")
    pi.add_argument("--out", required=True)
    pi.add_argument("--force", action="store_true")

    pf = sub.add_parser("fetch", help="descarga el resultado de una tarea ya lanzada")
    pf.add_argument("--task", required=True)
    pf.add_argument("--out", required=True)
    pf.add_argument("--kind", default="video", choices=["video", "image"])

    pv = sub.add_parser("video", help="genera una animación (Veo 3)")
    pv.add_argument("--prompt", required=True)
    pv.add_argument("--ratio", default="9:16")
    pv.add_argument("--dur", type=int, default=8)
    pv.add_argument("--out", required=True)
    pv.add_argument("--model", default=VIDEO_MODEL_DEFAULT,
                    choices=["veo3_fast", "veo3", "veo3_lite"])
    pv.add_argument("--resolution", default="720p", choices=["720p", "1080p"])
    pv.add_argument("--force", action="store_true")

    a = ap.parse_args()
    if a.cmd == "credits":
        print(f"{credits():g} créditos")
        return

    out = Path(a.out)
    if not out.is_absolute():
        out = ROOT / out

    if a.cmd == "fetch":
        # Rescate: la generación ya se pagó, solo faltaba bajar el archivo. Evita
        # volver a pagar cuando el sondeo se cae o expira por timeout.
        path = "/api/v1/veo/record-info" if a.kind == "video" else "/api/v1/jobs/recordInfo"
        d = call("GET", f"{path}?taskId={urllib.parse.quote(a.task)}")["data"]
        urls = veo_urls(d) if a.kind == "video" else result_urls(d.get("resultJson", ""))
        if not urls:
            sys.exit(f"la tarea {a.task} no tiene resultado descargable: {str(d)[:300]}")
        download(urls[0], out)
        ck = cache_key(out, "fetch", a.task, {})
        ledger_put(ck, dict(file=str(out.relative_to(ROOT)), kind=a.kind, model="fetch",
                            prompt=f"(rescatada) task {a.task}", params={}, taskId=a.task,
                            credits=0.0, source=urls[0],
                            at=time.strftime("%Y-%m-%d %H:%M:%S")))
        print(f"✓ {out.relative_to(ROOT)}  ({out.stat().st_size // 1024} KB, ya pagada)")
        return

    before = credits()
    if a.cmd == "image":
        gen_image(a.prompt, a.ratio, out, a.force)
    else:
        gen_video(a.prompt, a.ratio, a.dur, out, a.model, a.resolution, a.force)
    after = credits()
    if before != after:
        print(f"  créditos: {before:g} → {after:g}  (−{before - after:g})")


if __name__ == "__main__":
    main()
