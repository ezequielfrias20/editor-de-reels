#!/usr/bin/env python3
"""EDL → plan.json. Determinista, y sin decidir nada.

FRONTERA (spec §9): este módulo hace aritmética, lookup, derivación y
aplicación de fórmulas. NO elige objetos, ni instantes, ni si un segmento
merece visual. Si una decisión podría ser razonablemente distinta en manos de
otro editor, no es de aquí.

Los bloques de subtítulo se emiten EXPLÍCITOS, por rango de palabras
(`captions`), así que la keyword se enciende en el `start` exacto de su propia
palabra. `keywords` (la lista de strings) se sigue emitiendo porque el troceo
automático de `build-composition.py` la usa como fallback — es lo que mantiene
compilando las piezas 1-9, que no traen `captions` en su plan.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import objects as _objects
from asset_resolve import asset_hash, load_manifest
from edl_metrics import (PRESET_SFX, PRIORITY, measure, resolve_sfx,
                        run_gates, sfx_declarations)
from edl_schema import Edl, EdlError, derive_stages, load_edl, segment_windows

FPS = 30

# El ancho del lienzo por formato. El fuente puede ser cualquier cosa; el lienzo
# no, y es la mitad de la fórmula del reescalado.
CANVAS_W = {"REEL": 1080, "YOUTUBE": 1920}


def q(t: float) -> float:
    """Cuantiza a frame y recorta a 4 decimales.

    Copia literal de build-composition.py. EL ÚNICO punto de cuantización del
    compilador: un segundo sitio que redondee haría que dos rutas dieran
    instantes distintos para la misma palabra.
    """
    return round(round(float(t) * FPS) / FPS, 4)


def cap_ladder(ladder: dict, src_w: int, canvas_w: int,
               max_upscale: float) -> dict:
    """Recorta la escalera de zoom por la RESOLUCIÓN del fuente.

    El factor de reescalado al alza de un encuadre es `zoom · canvas_w / src_w`,
    así que el zoom máximo tolerable sale de despejar:

        techo = (src_w / canvas_w) · max_upscale

    Con fuente 1080 en lienzo 1080 el techo es **1.20**; con 4K vertical (2160)
    es **2.40**, y ahí un `z = 2.00` sigue en nativo (reescalado 1.00×). El 1.25
    del brief queda descartado SOLO para fuente 1080: por encima de ~1.2 el H.264
    a 1080 de ancho ablanda la piel de forma visible. La solución para crops más
    agresivos no es software, es grabar en 4K.

    El perfil pide la escalera que quiera y esto la recorta. Devuelve un dict
    NUEVO: el perfil se carga una vez y lo comparten todas las piezas, así que
    mutarlo haría que compilar dos seguidas diera resultados distintos.
    """
    techo = (src_w / canvas_w) * max_upscale
    return {k: min(v, techo) for k, v in ladder.items()}


def load_style(name: str, skill_root: Path) -> dict:
    p = Path(skill_root) / "styles" / f"{name}.json"
    if not p.exists():
        disponibles = sorted(x.stem for x in (Path(skill_root) / "styles").glob("*.json"))
        raise FileNotFoundError(
            f"no existe el style profile '{name}' en {p.parent}. "
            f"Disponibles: {disponibles or '(ninguno)'}")
    return json.loads(p.read_text())


def _shots(edl: Edl, style: dict, src_w: int | None = None) -> list[dict]:
    """La capa de metraje. Un encuadre por segmento, más los eventos CAMERA.

    Gotcha #6: un `off` que empieza a la vez que el takeover deja el frame
    vacío durante el fundido — el visual no ha terminado de aparecer y no hay
    nada debajo. El encuadre visible se queda hasta `start + fade_in` (el
    takeover ya está del todo puesto), y al salir del stage el siguiente
    encuadre entra en `start − fade_out` (antes de que el fundido de salida
    termine), nunca exactamente en el borde del stage.
    """
    canvas_w = CANVAS_W[edl.fmt]
    ladder = cap_ladder(style["camera"]["ladder"], src_w or canvas_w, canvas_w,
                        style["camera"]["max_upscale"])
    recortados = {k: v for k, v in style["camera"]["ladder"].items()
                  if ladder[k] < v}
    if recortados:
        print(f"  ⚠ escalera recortada por resolución del fuente "
              f"({src_w or canvas_w}px → lienzo {canvas_w}px): " +
              " · ".join(f"{k} {style['camera']['ladder'][k]} → {ladder[k]:.4g}"
                         for k, v in sorted(recortados.items())), file=sys.stderr)
    anchor = style["camera"]["default_anchor"]
    fade_in = style["stage"]["fade_in"]
    fade_out = style["stage"]["fade_out"]
    out: list[dict] = []

    def emit(at: float, camera: str) -> None:
        if camera == "OFF":
            out.append({"at": q(at), "kind": "off"})
        else:
            out.append({"at": q(at), "kind": "full",
                        "zoom": ladder[camera], "anchor": anchor})

    windows = segment_windows(edl.segments, edl.wt)
    prev_camera = None
    for (start, _end), seg in zip(windows, edl.segments):
        # El primer encuadre arranca la PIEZA, no la primera palabra: antes de
        # que él hable ya hay imagen en pantalla. `segment_windows` ya lo
        # resuelve así, y es la MISMA regla que measure() usa para calcular
        # cuánto tiempo está el presentador en pantalla.
        if seg.camera == "OFF" and prev_camera != "OFF":
            emit(start + fade_in, "OFF")
        elif seg.camera != "OFF" and prev_camera == "OFF":
            emit(start - fade_out, seg.camera)
        else:
            emit(start, seg.camera)
        prev_camera = seg.camera

        for ev in sorted(seg.events, key=lambda e: (e.at_word,)):
            if ev.type == "CAMERA":
                cam = ev.state.get("camera") or ev.theme or "MEDIUM"
                emit(ev.t(edl.wt), cam)
                prev_camera = cam

    out.sort(key=lambda s: s["at"])
    return out


def _visuals(edl: Edl, style: dict) -> list[dict]:
    """La capa de Motion Stage. Cada stage sale como UNA sola entrada de
    `visuals`, con un `fade_in` al principio y un `fade_out` al final —
    nunca una entrada por segmento (§3, la razón de existir de
    `check_no_black()`).

    El compilador NO decide qué objeto representa una idea ni cuándo entra:
    eso ya está en el EDL. Aquí solo se traduce `OBJECT_IN`/`OBJECT_STATE` a
    coordenadas, ángulos e instantes — aritmética y lookup, nada más.
    """
    fade_in = style["stage"]["fade_in"]
    fade_out = style["stage"]["fade_out"]
    windows = segment_windows(edl.segments, edl.wt)
    out: list[dict] = []

    for si, stage in enumerate(derive_stages(edl.segments)):
        start = windows[stage.first][0]
        end = windows[stage.last][1]
        theme = "primary"
        obj_defs: list[dict] = []
        ops: list[dict] = []
        last_state: dict[str, dict] = {}

        events = []
        for k in range(stage.first, stage.last + 1):
            events.extend(edl.segments[k].events)
        events.sort(key=lambda e: e.at_word)

        for ev in events:
            if ev.type == "THEME_CHANGE":
                theme = ev.theme or theme
            elif ev.type == "OBJECT_IN":
                # "object:clock@1" -> "clock". La referencia ya llegó resuelta
                # y versionada (§11); el compilador solo lee el nombre.
                kind = ev.asset.split(":", 1)[1].split("@", 1)[0]
                obj_defs.append({"id": ev.instance_id, "kind": kind,
                                 "slot": ev.slot, "state": dict(ev.state),
                                 "in": q(ev.t(edl.wt))})
                last_state[ev.instance_id] = dict(ev.state)
            elif ev.type == "OBJECT_STATE":
                prev = last_state.get(ev.instance_id, {})
                op = {"t": q(ev.t(edl.wt)), "op": "state", "id": ev.instance_id}
                if "time" in ev.state:
                    # Las agujas se derivan del estado ANTERIOR conocido de
                    # esta instancia, no de lo que el EDL escribe: el compilador
                    # rastrea la continuidad, el EDL solo dice el objetivo.
                    angles = _objects.hand_angles(
                        prev.get("time", "12:00"), ev.state["time"])
                    op["hour"] = angles["hour_to"]
                    op["minute"] = angles["minute_to"]
                    # El FROM también viaja: el tween de las agujas no lee el
                    # valor CSS "actual" del elemento (transform-origin en un
                    # <g> SVG demostró no ser fiable bajo GSAP), así que
                    # necesita los dos extremos explícitos.
                    op["hour_from"] = angles["hour_from"]
                    op["minute_from"] = angles["minute_from"]
                if ev.crowd:
                    # El SLOT de origen es el que le dio su `OBJECT_IN`, no
                    # el estado corriente — la instancia no se reposiciona
                    # entre medias, así que `objects.py` (que también
                    # hornea `tokens.SLOTS`) es quien sabe hacer la cuenta.
                    slot = next((o["slot"] for o in obj_defs
                                if o["id"] == ev.instance_id), None)
                    if slot is None:
                        raise ValueError(
                            f"'{ev.instance_id}' no tiene slot: ¿un OBJECT_STATE "
                            f"con crowd antes de su propio OBJECT_IN? El validador "
                            f"de instancias debería haberlo cazado ya")
                    op["dx"], op["dy"] = _objects.crowd_delta(slot)
                if ev.preset:
                    op["preset"] = ev.preset
                ops.append(op)
                last_state[ev.instance_id] = {**prev, **ev.state}

        out.append({
            "id": f"stage-{chr(97 + si)}", "role": "takeover", "kind": "mockup",
            "start": q(start), "end": q(end), "skin": "on-surface",
            "fade_in": fade_in, "fade_out": fade_out,
            # `visual_start` es el MISMO q(start) de arriba: build-composition.py
            # reconstruye el tiempo absoluto de cada anim como s + a[2], así que
            # motion_stage() necesita restar este valor para dar offsets
            # relativos, no tiempos absolutos (ver el aviso en su docstring).
            "mock": ["motion_stage", {"theme": theme, "objects": obj_defs,
                                      "at": ops, "visual_start": q(start)}],
        })
    return out


def _sfx(edl: Edl) -> list[tuple[float, str, float, str]]:
    """La capa de SONIDO. Pura derivación: `sfx_declarations()` (en
    `edl_metrics.py`, compartida con `measure()` para que `sfx_dropped` mida
    exactamente lo que esto emite) reúne los eventos que declaran sonido, y
    `resolve_sfx()` aplica el colapso de iguales y la concurrencia entre
    clases. El compilador no decide qué suena — nunca elige un preset ni un
    nombre de efecto — solo hace el lookup y aplica la fórmula (§9)."""
    return resolve_sfx(sfx_declarations(edl))


def _keywords(edl: Edl) -> list[str]:
    """Las palabras a resaltar, para el FALLBACK del troceo automático.

    Con `captions` explícitas esta lista no decide nada: el rango de la
    keyword viene dado. Se emite igual porque una pieza sin `captions` (las
    1-9) la sigue necesitando.

    Ordenadas y deduplicadas: un set iterado sin ordenar rompe el determinismo.
    """
    ks: set[str] = set()
    for seg in edl.segments:
        for ev in seg.events:
            if ev.type == "KEYWORD" and ev.words:
                for w in edl.wt.words[ev.words[0]:ev.words[1] + 1]:
                    ks.add(w.text.strip().rstrip(",.:;!?").upper())
    return sorted(ks)


def _captions(edl: Edl) -> list[dict]:
    """Los bloques de subtítulo, por RANGO DE PALABRAS.

    El EDL los declara explícitamente, así que la keyword se enciende en el
    `start` exacto de SU palabra en vez de deducirse por coincidencia de
    texto — que es lo que hacía el troceo automático, y lo que obligaba a
    listar `keywords` como strings sueltos (una palabra repetida en la pieza
    se resaltaba en todas sus apariciones).

    NO se emiten `start`/`end`: los deriva `build_captions` de los mismos
    rangos, con la regla de lectura que ya tenía. Duplicar aquí esa cuenta
    sería una segunda fuente de verdad para el ritmo del subtítulo.
    """
    out: list[dict] = []
    for seg in edl.segments:
        caps = [e for e in seg.events if e.type == "CAPTION" and e.words]
        kws = [e for e in seg.events if e.type == "KEYWORD" and e.words]
        for c in sorted(caps, key=lambda e: e.words[0]):
            kw = next((k for k in kws
                       if c.words[0] <= k.words[0] <= k.words[1] <= c.words[1]), None)
            out.append({"words": list(c.words),
                        "keyword": list(kw.words) if kw else None})
    out.sort(key=lambda c: c["words"][0])
    return out


def compile_edl(edl: Edl, style: dict, src_w: int | None = None) -> dict:
    """Función PURA: mismas entradas, mismo dict, siempre.

    `src_w` es el ancho del METRAJE, que sale de `assets/face-<n>.json`. Sin él
    se asume fuente nativa (igual al lienzo), que es la hipótesis conservadora:
    recorta la escalera al máximo en vez de dar por bueno un zoom que el fuente
    no aguanta.
    """
    return {
        "format": edl.fmt,
        "voice_gain": edl.voice_gain,
        "music": edl.music,
        "keywords": _keywords(edl),
        "captions": _captions(edl),
        "shots": _shots(edl, style, src_w),
        "cards": [],
        "visuals": _visuals(edl, style),
        "sfx": _sfx(edl),
        "_": f"generado por edl-compile desde {edl.src.name} — NO editar a mano",
    }


def _sin_ruido_creativo(node):
    """Copia recursiva sin las claves-comentario (`_algo`, la misma
    convención documentada en `references/plan-schema.md`) ni
    `planner.generatedAt`. Devuelve estructura nueva — nunca toca `node`.
    """
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k.startswith("_"):
                continue
            if k == "planner" and isinstance(v, dict):
                v = {pk: pv for pk, pv in v.items() if pk != "generatedAt"}
                if not v:
                    # Un EDL sin "planner" y uno con solo generatedAt (que
                    # queda vacío tras excluirlo) son la MISMA decisión
                    # creativa — la clave no puede sobrevivir vacía, o un
                    # EDL escrito a mano y su equivalente con metadata de
                    # trazabilidad hashearían distinto sin razón creativa.
                    continue
            out[k] = _sin_ruido_creativo(v)
        return out
    if isinstance(node, list):
        return [_sin_ruido_creativo(x) for x in node]
    return node


def creative_hash(edl: dict) -> str:
    """Identifica «esta decisión creativa» — no «estos bytes exactos».

    `sha256` del EDL canonicalizado (claves ordenadas, separadores fijos)
    SIN `planner.generatedAt` y SIN las claves que empiezan por `_`. Sin
    excluir `generatedAt`, dos corridas del MISMO EDL (misma decisión
    creativa, otro instante de generación) darían hashes distintos y la
    prueba de determinismo sería inútil. El hash del manifest (§12,
    `compile_report`) es una pregunta DISTINTA — «¿son los mismos píxeles?»
    — y mezclarla aquí invalidaría el hash creativo de toda pieza vieja
    cada vez que se añade un objeto nuevo a la librería.

    Recibe el EDL como `dict` crudo (JSON), no como `Edl`: el dataclass ya
    descarta las claves subrayadas y `planner` al parsear, así que hashear
    DESPUÉS de `load_edl` no probaría que la exclusión funciona.
    """
    canon = _sin_ruido_creativo(edl)
    blob = json.dumps(canon, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compile_report(edl: Edl, style: dict, manifest: dict) -> dict:
    """El informe de UNA compilación: qué versión de manifest se usó y el
    hash REAL de cada asset que esta pieza referencia — no el que dice el
    manifest, el recalculado ahora. Con esto una pieza vieja es reproducible
    **por referencia**: si algún día `objects.py` cambia de verdad (subiendo
    versión), el informe archivado de esta pieza sigue apuntando al código
    exacto que tenía cuando se renderizó.

    No decide nada — es lookup y aritmética, como todo lo demás de este
    módulo (§9). `style` no se usa todavía; queda en la firma porque el
    informe es el sitio natural donde un futuro dato del perfil (qué preset
    de calidad, qué build) también debería aparecer.
    """
    refs = sorted({ev.asset for seg in edl.segments for ev in seg.events
                  if ev.type == "OBJECT_IN" and ev.asset})
    return {
        "manifest_version": manifest["manifest_version"],
        "assets_used": {ref: asset_hash(ref, manifest) for ref in refs},
    }


def write_plan(plan: dict, out: Path) -> None:
    Path(out).write_text(
        json.dumps(plan, ensure_ascii=False, indent=2,
                   sort_keys=True, separators=(",", ": ")) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Compila un edl.json a plan.json")
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--piece", required=True)
    ap.add_argument("-o", "--out", type=Path, default=None)
    a = ap.parse_args(argv)

    root = a.project.resolve()
    work = root / "videos" / str(a.piece)
    skill = root / ".claude" / "skills" / "video-tech-premium"

    try:
        edl = load_edl(work / "edl.json", root)
    except EdlError as e:
        print(f"✗ {len(e.problems)} problema(s) en el EDL de la pieza {a.piece}:\n",
              file=sys.stderr)
        for p in e.problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    style = load_style(edl.style_profile, skill)

    # Fase 5: el compilador CALCULA métricas; el perfil decide umbrales y
    # severidad. Un gate en fail detiene el compilador antes de escribir nada;
    # un warn se imprime y se sigue.
    metrics = measure(edl, style)
    findings = run_gates(metrics, style)
    for f in findings:
        marca = "✗" if f.severity == "fail" else "⚠"
        print(f"  {marca} {f.message}", file=sys.stderr)
    if any(f.severity == "fail" for f in findings):
        print("\n✗ gates de estilo en fallo; el plan no se escribe", file=sys.stderr)
        return 1

    print("  métricas: " + " · ".join(f"{k} {v}" for k, v in sorted(metrics.items())))

    face_path = root / "assets" / f"face-{a.piece}.json"
    src_w = None
    if face_path.exists():
        src_w = int(json.loads(face_path.read_text())["width"])

    plan = compile_edl(edl, style, src_w)
    out = a.out or (work / "plan.json")
    write_plan(plan, out)

    manifest = load_manifest(root / "assets" / "manifest.json")
    report = compile_report(edl, style, manifest)
    print(f"  manifest {report['manifest_version']} · "
          f"{len(report['assets_used'])} asset(s) usados")

    print(f"✓ {out}  ·  {len(edl.segments)} segmentos  ·  "
          f"{len(plan['shots'])} encuadres  ·  {len(plan['keywords'])} keywords")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
