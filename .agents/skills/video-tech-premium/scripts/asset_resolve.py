#!/usr/bin/env python3
"""Asset Resolver — reutilizar antes que generar, con rastro de por qué.

FRONTERA: este módulo decide DE DÓNDE sale un asset (biblioteca existente,
parámetro de una plantilla, grabación propia, generación IA, o B-roll), nunca
CUÁL representa mejor una idea — esa sigue siendo decisión creativa (§13, el
Planner). El Resolver es infraestructura de reutilización, no de diseño.

La prioridad es estricta y siempre en el mismo orden: cada nivel se intenta
antes que el siguiente, y solo se baja si el de arriba no puede servir la
petición. Bajar de nivel SIEMPRE se anota (`.reason`) — sin ese rastro, dentro
de tres meses no se sabe si un `gen:` existe porque hacía falta o porque nadie
miró la librería primero.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import objects  # noqa: E402

PRIORIDAD = ("library", "configurable", "recording", "generated", "broll")


def _project_root() -> Path:
    """Copia del helper de `calibrate-hlg.py`: el PROYECTO es el directorio
    de trabajo, no donde vive el script — estos scripts viajan dentro de la
    skill. Se ejecutan siempre desde la raíz del proyecto; si hay un `.env`
    más arriba, se sube a buscarlo. Solo la usa el nivel `generated` para
    encontrar `assets/gen/ledger.json` sin que `resolve()` necesite un
    parámetro de proyecto que el resto de su contrato no pide."""
    cwd = Path.cwd().resolve()
    for d in (cwd, *cwd.parents):
        if (d / ".env").exists() or (d / "VIDEOS ORIGINALES").is_dir():
            return d
    return cwd


@dataclass(frozen=True)
class Resolution:
    ref: str
    resolved_via: str
    reason: str


def load_manifest(path: Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"no existe el manifest en {p} — sin él, CORE no puede validar que "
            f"un asset referenciado por el EDL sea real")
    return json.loads(p.read_text())


def _latest_version(kind_semantic: str, manifest: dict) -> str | None:
    """La versión MÁS ALTA de `object:<semantic>@n` que hay en el manifest, o
    `None` si no existe ninguna. Un semántico nuevo empieza en `@1`; uno que ya
    tiene `@1` y `@2` usa el más reciente — nunca se elige a mano."""
    prefix = f"{kind_semantic}@"
    versions = [int(ref.rsplit("@", 1)[1]) for ref in manifest.get("assets", {})
               if ref.startswith(prefix) and ref.rsplit("@", 1)[1].isdigit()]
    return f"{kind_semantic}@{max(versions)}" if versions else None


def asset_hash(ref: str, manifest: dict) -> str:
    """El hash REAL de un asset — recalculado ahora, no el que dice el
    manifest. `manifest-sync.py` compara los dos: si difieren, alguien editó
    un `@n` que se prometió inmutable, y los renders históricos que lo usan
    dejarían de ser reproducibles en silencio.

    Solo sabe hashear `kind: "object"` — el asset se DEFINE por el código
    fuente de su función en `objects.REGISTRY` (`inspect.getsource`), así que
    cualquier cambio de una coma para adentro cuenta como un asset distinto.
    """
    entry = manifest.get("assets", {}).get(ref)
    if entry is None:
        raise KeyError(f"'{ref}' no está en el manifest")
    kind = entry["kind"]
    if kind != "object":
        raise ValueError(
            f"'{ref}': hashear kind '{kind}' no está implementado — de momento "
            f"solo los objetos de objects.py se definen por su código fuente")
    name = ref.split(":", 1)[1].split("@", 1)[0]
    fn = objects.REGISTRY.get(name)
    if fn is None:
        raise KeyError(
            f"'{ref}' está en el manifest pero '{name}' no existe en "
            f"objects.REGISTRY — el manifest quedó desincronizado del código")
    src = inspect.getsource(fn)
    return "sha256:" + hashlib.sha256(src.encode("utf-8")).hexdigest()


def resolve(semantic: str, ctx: dict, manifest: dict) -> Resolution:
    """`semantic`: qué hace falta representar (`"clock"`, `"recepcion-de-
    clinica"`...), no un asset ya resuelto. `ctx` queda para que un nivel
    futuro (`configurable`, `recording`) decida con más que el nombre —
    de momento ningún nivel lo usa, y por eso no se documenta más."""
    # 1 · library — ¿ya existe un objeto reutilizable con este nombre?
    ref = _latest_version(f"object:{semantic}", manifest)
    if ref is not None:
        return Resolution(ref, "library",
                          f"'{semantic}' ya vive en objects.REGISTRY; reutilizar "
                          f"cuesta cero y no infla la librería (§ Global "
                          f"Constraints: empieza con 6, no con 15)")

    # 2 · configurable — una plantilla paramétrica registrada para este
    # semántico. Ningún asset de este nivel existe todavía en el manifest de
    # la pieza 10; el mecanismo queda listo para cuando lo haya.
    ref = _latest_version(f"configurable:{semantic}", manifest)
    if ref is not None:
        return Resolution(ref, "configurable",
                          f"'{semantic}' tiene una plantilla parametrizable "
                          f"registrada — configurarla es más barato que grabar "
                          f"o generar de cero")

    # 3 · recording — metraje propio ya capturado para este semántico.
    ref = _latest_version(f"recording:{semantic}", manifest)
    if ref is not None:
        return Resolution(ref, "recording",
                          f"'{semantic}' ya se grabó; una grabación real pesa "
                          f"más que cualquier alternativa sintética")

    # 4 · generated — reutilizar del ledger de IA si ya se pagó por algo con
    # este nombre; si no, la recomendación es generar (y el `reason` deja
    # constancia de que los tres niveles de arriba no tenían nada que servir).
    ledger_path = _project_root() / "assets" / "gen" / "ledger.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    existente = next((e for e in ledger.values()
                      if Path(e.get("file", "")).stem == semantic), None)
    if existente is not None:
        return Resolution(f"gen:{semantic}@1", "generated",
                          f"'{semantic}' ya está en assets/gen/ledger.json "
                          f"({existente['file']}) — el pipeline se re-corre sin "
                          f"volver a pagar")

    return Resolution(f"gen:{semantic}@pending", "generated",
                      f"'{semantic}' no está en la librería, no tiene plantilla "
                      f"configurable y no hay grabación propia — generar de cero "
                      f"es la vía más barata que queda. Si sale caro o repetido, "
                      f"BROLL es la alternativa (§11: ya no limitado a metraje "
                      f"propio; puede ser licenciado, buscado o generado)")


def resolve_edl(draft: dict, manifest: dict) -> dict:
    """Recorre un EDL en BORRADOR (eventos con `semantic` en vez de `asset`
    resuelto) y devuelve una copia con `asset`, `resolvedVia` y
    `resolveReason` rellenos en cada `OBJECT_IN`.

    No toca eventos que ya traen `asset` — el Resolver completa lo que falta,
    no reescribe una decisión que el borrador ya tomó a propósito.
    """
    import copy
    out = copy.deepcopy(draft)
    for seg in out.get("segments", []):
        for ev in seg.get("events", []):
            if ev.get("type") != "OBJECT_IN" or ev.get("asset"):
                continue
            semantic = ev.pop("semantic", None)
            if not semantic:
                continue
            r = resolve(semantic, {}, manifest)
            ev["asset"] = r.ref
            ev["resolvedVia"] = r.resolved_via
            ev["resolveReason"] = r.reason
    return out
