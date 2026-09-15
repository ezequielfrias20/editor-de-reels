#!/usr/bin/env python3
"""El contrato congelado del EDL: forma, derivación de stages y validación CORE.

Un EDL que pasa `load_edl` es ESTRUCTURALMENTE EJECUTABLE. Lo que quede mal a
partir de aquí es gusto, y eso lo miden los gates del style profile, que viven
en datos (`styles/*.json`) y no aquí.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from asset_resolve import asset_hash, load_manifest
from edl_words import WordTable, load_words

SCENE_TYPES = frozenset({"A_ROLL", "A_ROLL_ICON", "MOTION_STAGE",
                         "KINETIC_TYPE", "UI_DEMO", "BROLL", "CTA"})
REPRESENTATION_TYPES = frozenset({"OBJECT", "STATE_CHANGE", "QUANTITY", "RELATION",
                                  "SEQUENCE", "CONTRAST", "INTERFACE"})
EVENT_TYPES = frozenset({"OBJECT_IN", "OBJECT_STATE", "OBJECT_EXIT", "STAGE_CLEAR",
                         "THEME_CHANGE", "CAPTION", "KEYWORD", "CAMERA",
                         "TYPE_BEAT", "UI_ACTION", "SFX", "CARD"})

# Las claves que un rótulo puede declarar. Cerrada por la misma razón que la
# whitelist de overrides: `build_cards` ignora en silencio una clave que no
# conoce, así que un `titel` mal escrito daría un rótulo sin titular y un
# render aparentemente correcto.
CARD_KEYS = frozenset({"kicker", "title", "sub", "key", "place", "body",
                       "items", "accent", "cta_text", "_"})
CARD_PLACES = frozenset({"top", "center", "bottom"})
CARD_BODIES = frozenset({"none", "chips", "stat", "cta", "teaser",
                         "msgteaser"})
TRANSITIONS = frozenset({"CUT", "DIAGONAL_WIPE", "BLUR_WIPE",
                         "OBJECT_MATCH_CUT", "SCALE_BLUR"})
# `BAND` es el layout triband: el metraje ocupa solo la banda de abajo y no
# lleva escalera de zoom — el encuadre de la banda ya es un recorte fuerte y
# una escalera encima lo haría irreconocible.
CAMERAS = frozenset({"WIDE", "MEDIUM", "CLOSE", "BAND", "OFF"})

LAYOUT_MODES = frozenset({"triband"})
# El orden IMPORTA: es el de arriba abajo, y con él se comprueba la contigüidad.
BAND_ORDER = ("top", "text", "speaker")
CANVAS_H = {"REEL": 1920, "YOUTUBE": 1080}

# Los sceneType que abren stage. Es lo que da ámbito a un instanceId.
STAGE_TYPES = frozenset({"MOTION_STAGE", "KINETIC_TYPE"})

# Los que exigen representationType: el filtro anti-decoración de §1.
NEEDS_REPRESENTATION = STAGE_TYPES | {"UI_DEMO", "A_ROLL_ICON", "BROLL"}

# Escotilla acotada a propósito, para que no degenere en bypass del compilador.
OVERRIDE_WHITELIST = frozenset({"cap_top", "anchor", "anchorX", "mock_pad_top",
                                "mock_pad_bottom", "fade_in", "fade_out",
                                "rect", "trim"})

ASSET_KINDS = ("object", "recording", "gen", "broll", "mock")
ASSET_RE = re.compile(r"^(object|recording|gen|broll|mock):[a-z0-9-]+@\d+(\?.*)?$")

# Un offset negativo grande adelanta el guion, que es regla dura del proyecto.
OFFSET_FLOOR = -0.12


class EdlError(Exception):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("EDL inválido:\n  - " + "\n  - ".join(problems))


@dataclass(frozen=True)
class Event:
    type: str
    at_word: int
    offset: float = 0.0
    words: tuple[int, int] | None = None
    instance_id: str | None = None
    asset: str | None = None
    state: dict = field(default_factory=dict)
    preset: str | None = None
    sfx: str | None = None
    slot: str | None = None
    crowd: bool = False
    theme: str | None = None
    roles: dict = field(default_factory=dict)
    trim: float = 1.0
    card: dict = field(default_factory=dict)
    until_word: int | None = None
    until_offset: float = 0.0
    cta_at_word: int | None = None

    def t(self, wt: WordTable) -> float:
        """Instante SIN cuantizar. La cuantización es del compilador."""
        return wt.at(self.at_word) + self.offset


@dataclass(frozen=True)
class Segment:
    words: tuple[int, int]
    semantic_intent: str
    scene_type: str
    reason: str
    camera: str = "MEDIUM"
    representation_type: str | None = None
    default_preset: str | None = None
    transition_in: str = "CUT"
    transition_out: str | None = None
    hold: bool = False
    events: tuple[Event, ...] = ()

    def t(self, wt: WordTable) -> tuple[float, float]:
        return wt.span(*self.words)


@dataclass(frozen=True)
class Stage:
    first: int
    last: int


@dataclass(frozen=True)
class Override:
    target: str
    value: object
    why: str

    @property
    def prop(self) -> str:
        return self.target.rsplit(".", 1)[-1]


@dataclass(frozen=True)
class Edl:
    src: Path
    fmt: str
    piece: int
    style_profile: str
    wt: WordTable
    segments: tuple[Segment, ...]
    overrides: tuple[Override, ...]
    voice_gain: float
    music: dict
    planner: dict
    layout: dict = field(default_factory=dict)


def segment_windows(segments, wt: WordTable) -> tuple[tuple[float, float], ...]:
    """Ventana temporal ACTIVA de cada segmento: desde su inicio (o 0.0 para
    el primero) hasta el inicio del siguiente (o la duración total para el
    último).

    NO es el span de sus palabras. El span deja fuera las pausas entre
    frases, pero el presentador sigue en pantalla durante esas pausas — el
    plano no cambia hasta que empieza el siguiente segmento. Es la misma regla
    que usa `_shots()` para decidir cuándo emitir cada encuadre, y `measure()`
    la necesita para que `presenter_share` dé 1.0 en una pieza toda A_ROLL.
    """
    starts = [0.0 if i == 0 else seg.t(wt)[0] for i, seg in enumerate(segments)]
    ends = starts[1:] + [wt.duration]
    return tuple(zip(starts, ends))


def derive_stages(segments) -> tuple[Stage, ...]:
    """Un stage es una serie MAXIMAL de segmentos contiguos de tipo stage.

    No se escribe en el EDL: se deduce. Es lo que permite que una instancia
    sobreviva varios segmentos y que el stage salga como UNA sola entrada de
    `visuals` — que es lo que cierra la clase de bug de `check_no_black()`.
    """
    stages, run = [], None
    for i, seg in enumerate(segments):
        if seg.scene_type in STAGE_TYPES:
            if run is None:
                run = i
        elif run is not None:
            stages.append(Stage(first=run, last=i - 1))
            run = None
    if run is not None:
        stages.append(Stage(first=run, last=len(segments) - 1))
    return tuple(stages)


def _ordered(events) -> list[Event]:
    """Orden estable: por palabra, y a igualdad por posición en el archivo."""
    return [e for _, e in sorted(enumerate(events), key=lambda p: (p[1].at_word, p[0]))]


def _parse_event(raw: dict, si: int, ei: int, problems: list[str]) -> Event | None:
    et = raw.get("type")
    if et not in EVENT_TYPES:
        problems.append(f"segmento {si}, evento {ei}: type '{et}' desconocido")
        return None
    if "atWord" not in raw:
        problems.append(f"segmento {si}, evento {ei} ({et}): falta atWord")
        return None
    off = float(raw.get("offset", 0.0))
    if off < OFFSET_FLOOR:
        problems.append(
            f"segmento {si}, evento {ei} ({et}): offset {off} adelanta el guion más "
            f"de {abs(OFFSET_FLOOR)} s — nada entra antes de su palabra")
    w = raw.get("words")
    return Event(
        type=et, at_word=int(raw["atWord"]), offset=off,
        words=(int(w[0]), int(w[1])) if w else None,
        instance_id=raw.get("instanceId"), asset=raw.get("asset"),
        state=raw.get("state") or {}, preset=raw.get("preset"), sfx=raw.get("sfx"),
        slot=raw.get("slot"), crowd=bool(raw.get("crowd", False)),
        theme=raw.get("theme"), roles=raw.get("roles") or {},
        trim=float(raw.get("trim", 1.0)),
        card=raw.get("card") or {},
        until_word=(int(raw["untilWord"]) if "untilWord" in raw else None),
        until_offset=float(raw.get("untilOffset", 0.0)),
        cta_at_word=(int(raw["ctaAtWord"]) if "ctaAtWord" in raw else None),
    )


def _check_assets(segments, manifest: dict | None, problems: list[str]) -> None:
    for si, seg in enumerate(segments):
        for ei, ev in enumerate(seg.events):
            if ev.type != "OBJECT_IN":
                continue
            a = ev.asset
            if not a:
                problems.append(f"segmento {si}, evento {ei}: OBJECT_IN sin asset")
            elif ":" not in a:
                problems.append(
                    f"segmento {si}, evento {ei}: asset '{a}' sin resolver — el "
                    f"compilador no elige assets. Pásalo por el Asset Resolver (§11)")
            elif not ASSET_RE.match(a):
                kind = a.split(":", 1)[0]
                if kind not in ASSET_KINDS:
                    problems.append(
                        f"segmento {si}, evento {ei}: asset '{a}' con tipo desconocido; "
                        f"esperado uno de {ASSET_KINDS}")
                else:
                    problems.append(
                        f"segmento {si}, evento {ei}: asset '{a}' sin versión — se "
                        f"espera '{kind}:nombre@n'. Una @n es inmutable, y es lo que "
                        f"permite re-renderizar una pieza vieja idéntica")
            else:
                # Formato correcto (§11, resuelto y versionado): que EXISTA y
                # que su hash CUADRE con el código que dice representar — un
                # asset editado en silencio cambiaría renders históricos.
                if manifest is None:
                    problems.append(
                        f"segmento {si}, evento {ei}: no se pudo cargar "
                        f"assets/manifest.json para validar '{a}'")
                    continue
                entry = manifest.get("assets", {}).get(a)
                if entry is None:
                    problems.append(
                        f"segmento {si}, evento {ei}: asset '{a}' no está en el "
                        f"manifest ({len(manifest.get('assets', {}))} registrados) — "
                        f"el Asset Resolver no lo produjo, o alguien lo escribió a mano")
                    continue
                try:
                    real = asset_hash(a, manifest)
                except Exception as e:
                    problems.append(
                        f"segmento {si}, evento {ei}: no se pudo verificar el hash "
                        f"de '{a}': {e}")
                    continue
                if real != entry.get("hash"):
                    problems.append(
                        f"segmento {si}, evento {ei}: asset '{a}' CAMBIÓ — el "
                        f"manifest dice {entry.get('hash')}, el código da {real}. "
                        f"Un @n es inmutable; si el rediseño es intencionado, sube "
                        f"la versión en vez de editar esta")


def _card_span(ev: Event, wt: WordTable) -> tuple[float, float]:
    return ev.t(wt), wt.words[ev.until_word].end + ev.until_offset


def _check_cards(segments, wt: WordTable, problems: list[str]) -> None:
    """Un rótulo ACOMPAÑA al presentador; no puede vivir sobre un stage.

    No es gusto, es apilado (gotcha #5): las tarjetas van en la pista 4 y el
    takeover del stage en la 5, así que un rótulo declarado dentro de un
    segmento de stage se renderiza DEBAJO de un fondo opaco y no se ve. Un
    render que sale mal sin que nada falle es exactamente lo que este
    validador existe para impedir.
    """
    n = len(wt.words)
    for si, seg in enumerate(segments):
        for ei, ev in enumerate(seg.events):
            if ev.type != "CARD":
                continue
            where = f"segmento {si}, evento {ei} (CARD)"
            if seg.scene_type in STAGE_TYPES:
                problems.append(
                    f"{where}: un rótulo dentro de {seg.scene_type} queda DEBAJO "
                    f"del takeover del stage (pista 4 vs 5) y no se vería. Sobre "
                    f"un stage, el texto lo pone el propio objeto")
            if not ev.card:
                problems.append(f"{where}: falta 'card'")
                continue
            desconocidas = set(ev.card) - CARD_KEYS
            if desconocidas:
                problems.append(
                    f"{where}: claves de rótulo desconocidas {sorted(desconocidas)}; "
                    f"se aceptan {sorted(CARD_KEYS - {'_'})}. `build_cards` ignora "
                    f"en silencio lo que no conoce")
            if not (ev.card.get("kicker") or ev.card.get("title")):
                problems.append(
                    f"{where}: un rótulo sin 'kicker' ni 'title' no pinta nada")
            place = ev.card.get("place", "top")
            if place not in CARD_PLACES:
                problems.append(f"{where}: place '{place}' no existe; hay "
                                f"{sorted(CARD_PLACES)}")
            body = ev.card.get("body", "none")
            if body not in CARD_BODIES:
                problems.append(f"{where}: body '{body}' no existe; hay "
                                f"{sorted(CARD_BODIES)}")
            key = ev.card.get("key")
            title = ev.card.get("title") or ""
            if key and key not in title:
                problems.append(
                    f"{where}: 'key' ({key!r}) no aparece en 'title' ({title!r}), "
                    f"así que ninguna palabra del titular llevaría el acento")
            if ev.until_word is None:
                problems.append(
                    f"{where}: falta untilWord — los dos bordes del rótulo salen "
                    f"de una palabra, no de un float")
            elif not (0 <= ev.until_word < n):
                problems.append(
                    f"{where}: untilWord {ev.until_word} fuera de las {n} palabras")
            elif ev.until_word < ev.at_word:
                problems.append(
                    f"{where}: untilWord {ev.until_word} va antes de atWord "
                    f"{ev.at_word}")
            # Y NO BASTA CON EL SEGMENTO EN QUE SE DECLARA. Un rótulo se
            # extiende hasta `untilWord`, que puede caer YA DENTRO del stage
            # siguiente — y ahí vuelve a quedar debajo del takeover. El borde
            # tiene que morir antes de que el stage empiece.
            if ev.until_word is not None and 0 <= ev.until_word < n:
                cs, ce = _card_span(ev, wt)
                for (ws, we), s2 in zip(segment_windows(segments, wt), segments):
                    if s2.scene_type in STAGE_TYPES and cs < we and ws < ce:
                        problems.append(
                            f"{where}: el rótulo vive {cs:.3f}-{ce:.3f} y pisa el "
                            f"stage de {ws:.3f}-{we:.3f}; ahí queda debajo del "
                            f"takeover. Acorta untilWord")
                        break
            if ev.cta_at_word is not None:
                if body != "cta":
                    problems.append(
                        f"{where}: ctaAtWord solo tiene sentido con body 'cta'")
                elif not (ev.at_word <= ev.cta_at_word <= (ev.until_word or n - 1)):
                    problems.append(
                        f"{where}: ctaAtWord {ev.cta_at_word} cae fuera del rótulo "
                        f"[{ev.at_word}, {ev.until_word}]")


def _check_slots(segments, problems: list[str]) -> None:
    """Zona segura de slots. `tokens.SLOTS` llega en la Tarea 5 (objects.py) —
    hasta entonces no se puede validar contra nada y se omite en silencio."""
    try:
        import tokens as _t
    except ImportError:
        return
    slots = getattr(_t, "SLOTS", None)
    if slots is None:
        return
    for si, seg in enumerate(segments):
        for ev in seg.events:
            if ev.type == "OBJECT_IN" and ev.slot:
                if ev.slot not in slots:
                    problems.append(
                        f"segmento {si}: slot '{ev.slot}' no existe; hay "
                        f"{sorted(slots)}")


def _check_instances(segments, problems: list[str]) -> None:
    for stage in derive_stages(segments):
        live: set[str] = set()
        retired: set[str] = set()
        for si in range(stage.first, stage.last + 1):
            where = f"segmento {si} (stage {stage.first}-{stage.last})"
            for ev in _ordered(segments[si].events):
                if ev.type == "OBJECT_IN":
                    if ev.instance_id in live:
                        problems.append(
                            f"{where}: la instancia '{ev.instance_id}' ya existe en "
                            f"este stage; para mutarla usa OBJECT_STATE")
                    else:
                        live.add(ev.instance_id)
                        retired.discard(ev.instance_id)
                elif ev.type == "OBJECT_EXIT":
                    if ev.instance_id not in live:
                        problems.append(
                            f"{where}: OBJECT_EXIT sobre '{ev.instance_id}', que no "
                            f"existe en este stage")
                    else:
                        live.discard(ev.instance_id)
                        retired.add(ev.instance_id)
                elif ev.type == "OBJECT_STATE":
                    if ev.instance_id in retired:
                        problems.append(
                            f"{where}: OBJECT_STATE sobre '{ev.instance_id}', que ya "
                            f"fue retirada. Un STAGE_CLEAR libera el id para reusarlo")
                    elif ev.instance_id not in live:
                        problems.append(
                            f"{where}: OBJECT_STATE sobre '{ev.instance_id}', que no "
                            f"existe en este stage")
                elif ev.type == "STAGE_CLEAR":
                    live.clear()
                    retired.clear()


def _live_at(segments, si: int) -> set[str]:
    """Instancias vivas al terminar el segmento `si`, dentro de su stage."""
    stage = next((s for s in derive_stages(segments) if s.first <= si <= s.last), None)
    if stage is None:
        return set()
    live: set[str] = set()
    for k in range(stage.first, si + 1):
        for ev in _ordered(segments[k].events):
            if ev.type == "OBJECT_IN":
                live.add(ev.instance_id)
            elif ev.type == "OBJECT_EXIT":
                live.discard(ev.instance_id)
            elif ev.type == "STAGE_CLEAR":
                live.clear()
    return live


def _check_transitions(segments, problems: list[str]) -> None:
    last = len(segments) - 1
    if segments[last].transition_out:
        problems.append(
            f"segmento {last}: transitionOut prohibido en el último segmento — ese "
            f"frame es el que se congela al reiniciar el reel (gotcha #6)")

    for i in range(last):
        out_, in_ = segments[i].transition_out, segments[i + 1].transition_in
        if out_ and out_ != "CUT" and in_ and in_ != "CUT":
            problems.append(
                f"conflicto en el límite {i}→{i+1}: el saliente declara '{out_}' y el "
                f"entrante '{in_}'. Solo uno manda en un límite; decide cuál")

    for i, seg in enumerate(segments):
        if seg.transition_in != "OBJECT_MATCH_CUT":
            continue
        if i == 0:
            problems.append("segmento 0: OBJECT_MATCH_CUT no tiene límite anterior")
            continue
        compartidas = _live_at(segments, i - 1) & _live_at(segments, i)
        mutadas = {e.instance_id for e in seg.events if e.type == "OBJECT_STATE"}
        if not compartidas:
            problems.append(
                f"segmento {i}: OBJECT_MATCH_CUT sin ninguna instancia viva a ambos "
                f"lados del límite. Sin objeto compartido es un corte normal con un "
                f"nombre bonito")
        elif not (compartidas & mutadas):
            problems.append(
                f"segmento {i}: OBJECT_MATCH_CUT sobre {sorted(compartidas)} pero el "
                f"segmento no las muta con OBJECT_STATE. El match cut ES la mutación")


def validate_layout(layout: dict, segments, canvas_h: int) -> list[str]:
    """Las bandas tienen que cubrir el lienzo entero, en orden y sin huecos.

    Un hueco entre dos bandas es suelo grafito que nadie decidió dejar, y en un
    lienzo de 1920 px pasa desapercibido en el JSON y no en el frame.
    """
    problems: list[str] = []
    usa_band = any(s.camera == "BAND" for s in segments)

    if not layout:
        if usa_band:
            problems.append(
                "hay un segmento con camera BAND sin bloque 'layout' en la cabecera: "
                "la geometría de las tres bandas se declara una sola vez y se comparte")
        return problems

    mode = layout.get("mode")
    if mode not in LAYOUT_MODES:
        problems.append(f"layout.mode '{mode}' desconocido; hay {sorted(LAYOUT_MODES)}")
        return problems

    bands = layout.get("bands") or {}
    faltan = [k for k in BAND_ORDER if k not in bands]
    if faltan:
        problems.append(f"layout.bands: faltan {faltan}; el triband pide {list(BAND_ORDER)}")
        return problems

    for k in BAND_ORDER:
        v = bands[k]
        if not isinstance(v, list) or len(v) != 2:
            problems.append(f"layout.bands.{k} tiene que ser [y0, y1]")
            return problems
        if v[1] <= v[0]:
            problems.append(f"layout: banda '{k}' invertida o vacía {v}")

    ys = [bands[k] for k in BAND_ORDER]
    if ys[0][0] != 0 or ys[-1][1] != canvas_h:
        problems.append(
            f"layout: las bandas tienen que cubrir 0..{canvas_h}, y van de "
            f"{ys[0][0]} a {ys[-1][1]}")
    for a, b, ka, kb in zip(ys, ys[1:], BAND_ORDER, BAND_ORDER[1:]):
        if a[1] != b[0]:
            problems.append(
                f"layout: las bandas '{ka}' y '{kb}' no son contiguas "
                f"({a[1]} → {b[0]}): un hueco entre bandas es suelo que nadie decidió")

    if not usa_band:
        problems.append(
            "layout declarado pero ningún segmento usa camera BAND: declarar geometría "
            "que nadie usa casi siempre significa que faltó marcar los segmentos")
    return problems


def load_edl(path: Path, project_root: Path) -> Edl:
    path, project_root = Path(path), Path(project_root)
    if path.name.endswith(".draft.json"):
        raise EdlError([
            f"{path.name} es un draft: el compilador solo acepta el contrato congelado "
            f"edl.json. Pásalo por el Asset Resolver y la validación CORE (§11)"])

    raw = json.loads(path.read_text())
    problems: list[str] = []

    decl = raw.get("transcript") or {}
    for key in ("words", "cuts"):
        if key not in decl:
            raise EdlError([
                f"falta transcript.{key} — el EDL declara los DOS archivos que fijan "
                f"sus tiempos: las palabras del fuente y los cortes que las remapean"])
    wt = load_words(project_root / decl["words"], project_root / decl["cuts"])
    if decl.get("fingerprint") != wt.fingerprint:
        problems.append(
            f"el fingerprint no cuadra con {decl['words']} + {decl['cuts']}\n"
            f"      declarado: {decl.get('fingerprint')}\n"
            f"      real:      {wt.fingerprint}\n"
            f"      Cambió el transcript, cambiaron los cortes, o el EDL apunta a los "
            f"archivos equivocados. Revisa TODOS los segmentos antes de re-fijarlo")

    segments: list[Segment] = []
    for si, rs in enumerate(raw.get("segments", [])):
        w = rs.get("words")
        if not w or len(w) != 2:
            problems.append(f"segmento {si}: falta 'words' como [i, j]")
            continue
        st = rs.get("sceneType")
        if st not in SCENE_TYPES:
            problems.append(f"segmento {si}: sceneType '{st}' desconocido")
        cam = rs.get("camera", "MEDIUM")
        if cam not in CAMERAS:
            problems.append(f"segmento {si}: camera '{cam}' desconocida")
        rt = rs.get("representationType")
        if rt is not None and rt not in REPRESENTATION_TYPES:
            problems.append(f"segmento {si}: representationType '{rt}' desconocido")
        if st in NEEDS_REPRESENTATION and rt is None:
            problems.append(
                f"segmento {si}: {st} necesita representationType — es el filtro "
                f"anti-decoración (§1). Si no hay representación concreta, vuelve al "
                f"presentador con A_ROLL")
        intent = (rs.get("semanticIntent") or "").strip()
        reason = (rs.get("reason") or "").strip()
        if not reason:
            problems.append(
                f"segmento {si}: falta 'reason'. Si no puedes decir por qué existe "
                f"este segmento, sobra")
        elif reason.lower() == intent.lower():
            problems.append(
                f"segmento {si}: 'reason' repite 'semanticIntent'. La razón explica la "
                f"DECISIÓN de edición, no el contenido de la frase")
        for tname, tval in (("transitionIn", rs.get("transitionIn", "CUT")),
                            ("transitionOut", rs.get("transitionOut"))):
            if tval is not None and tval not in TRANSITIONS:
                problems.append(f"segmento {si}: {tname} '{tval}' desconocida")

        events = [e for e in (_parse_event(r, si, ei, problems)
                              for ei, r in enumerate(rs.get("events", [])))
                  if e is not None]
        segments.append(Segment(
            words=(int(w[0]), int(w[1])), semantic_intent=intent,
            scene_type=st if st in SCENE_TYPES else "A_ROLL", reason=reason,
            camera=cam if cam in CAMERAS else "MEDIUM", representation_type=rt,
            default_preset=rs.get("defaultPreset"),
            transition_in=rs.get("transitionIn", "CUT"),
            transition_out=rs.get("transitionOut"),
            hold=bool(rs.get("hold", False)), events=tuple(events)))

    if not segments:
        raise EdlError(problems + ["el EDL no tiene segmentos"])

    # ── cobertura, contigüidad y rangos ──────────────────────────────────────
    n = len(wt.words)
    if segments[0].words[0] != 0 or segments[-1].words[1] != n - 1:
        problems.append(
            f"los segmentos no cubren el transcript entero: van de "
            f"{segments[0].words[0]} a {segments[-1].words[1]} y hay {n} palabras "
            f"(0..{n-1}). Toda palabra dicha necesita una decisión editorial")
    for i, seg in enumerate(segments):
        a, b = seg.words
        if b < a:
            problems.append(f"segmento {i}: rango invertido [{a}, {b}]")
        if not (0 <= a < n and 0 <= b < n):
            problems.append(
                f"segmento {i}: rango [{a}, {b}] fuera de las {n} palabras de "
                f"{wt.transcript.name}")
        if i + 1 < len(segments):
            nxt = segments[i + 1].words[0]
            if nxt > b + 1:
                problems.append(
                    f"hueco entre los segmentos {i} y {i+1}: la palabra {b+1} "
                    f"('{wt.words[b+1].text}') no pertenece a ninguno")
            elif nxt <= b:
                problems.append(
                    f"los segmentos {i} y {i+1} se solapan en la palabra {nxt}")

    # ── captions y keywords ──────────────────────────────────────────────────
    for si, seg in enumerate(segments):
        caps = [e for e in seg.events if e.type == "CAPTION"]
        if seg.scene_type == "KINETIC_TYPE" and caps:
            problems.append(
                f"segmento {si}: CAPTION prohibido en KINETIC_TYPE — si la tipografía "
                f"es el gráfico, un subtítulo repitiéndola es decorar (§5)")
        a, b = seg.words
        for e in seg.events:
            if e.type in ("CAPTION", "KEYWORD", "TYPE_BEAT") and e.words:
                if e.words[0] < a or e.words[1] > b:
                    problems.append(
                        f"segmento {si}: {e.type} {list(e.words)} cae fuera del "
                        f"segmento [{a}, {b}]")
        for kw in (e for e in seg.events if e.type == "KEYWORD"):
            if not kw.words:
                problems.append(f"segmento {si}: KEYWORD sin rango de palabras")
                continue
            if not any(c.words and c.words[0] <= kw.words[0] <= kw.words[1] <= c.words[1]
                       for c in caps):
                problems.append(
                    f"segmento {si}: la keyword {list(kw.words)} "
                    f"('{wt.text_of(*kw.words)}') no está dentro de ningún CAPTION "
                    f"del segmento")

    try:
        manifest = load_manifest(project_root / "assets" / "manifest.json")
    except FileNotFoundError:
        manifest = None
    _check_assets(segments, manifest, problems)
    _check_cards(segments, wt, problems)
    _check_slots(segments, problems)
    _check_instances(segments, problems)
    _check_transitions(segments, problems)

    layout = raw.get("layout") or {}
    problems += validate_layout(layout, segments, CANVAS_H[raw.get("format", "REEL").upper()])

    # ── overrides ────────────────────────────────────────────────────────────
    overrides: list[Override] = []
    for i, ro in enumerate(raw.get("plan_overrides", [])):
        target, why = ro.get("target", ""), (ro.get("why") or "").strip()
        prop = target.rsplit(".", 1)[-1]
        if prop not in OVERRIDE_WHITELIST:
            problems.append(
                f"override {i}: '{prop}' no está en la whitelist "
                f"{sorted(OVERRIDE_WHITELIST)}. La escotilla está acotada a propósito "
                f"para que no sea un bypass del compilador")
        if not why:
            problems.append(f"override {i} ({target}): falta 'why'")
        overrides.append(Override(target=target, value=ro.get("value"), why=why))

    if problems:
        raise EdlError(problems)

    return Edl(src=path, fmt=raw.get("format", "REEL").upper(),
               piece=int(raw.get("piece", 0)),
               style_profile=raw.get("style_profile", "motion-explainer"),
               wt=wt, segments=tuple(segments), overrides=tuple(overrides),
               voice_gain=float(raw.get("voice_gain", 0.70)),
               music=raw.get("music", {}), planner=raw.get("planner", {}),
               layout=layout)
