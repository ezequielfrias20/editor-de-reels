#!/usr/bin/env python3
"""Genera la composición HyperFrames de una pieza a partir de su plan.

    scripts/build-composition.py --project <dir> --piece 2

Lee `<project>/videos/<piece>/plan.json` (encuadres, tarjetas, visuales, sonido)
más el transcript y el plan de cortes, y escribe `public/index.html`,
`public/cards/` y `storyboard.json`.

Todo se deriva de los datos: los tiempos de palabra se remapean del timeline
original al del corte, así que si cambia el plan de cortes basta con volver a
ejecutar esto. Nada de tiempos escritos a mano en el HTML.

── EL MODELO DE TRES CAPAS ────────────────────────────────────────────────────

    shots     la capa de METRAJE. Una lista de encuadres: cada entrada dice
              desde cuándo, con qué layout y con cuánto zoom se ve al creador.
              Aquí viven los punch-ins.
    cards     rótulos y gráficos que FLOTAN sobre el metraje.
    visuals   lo que OCUPA el lienzo entero: mockups, grabación de producto,
              imágenes generadas.

Las tres son independientes y se cruzan por tiempo, que es lo que permite
cambiar de imagen cada 1–2.5 s sin reescribir la estructura.
"""
import argparse
import itertools
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import caption_fonts  # noqa: E402
import caption_metrics  # noqa: E402
import layout_formatos  # noqa: E402
import mockups  # noqa: E402
import mockups_chatgpt  # noqa: E402
import mockups_codex  # noqa: E402
import mockups_davinci  # noqa: E402
import mockups_plugins  # noqa: E402
import mockups_reels  # noqa: E402
import objects  # noqa: E402
import tokens as TK  # noqa: E402
from tokens import C, FILL, FONT, MONO, RADIUS, TRACK, TYPE, grid, vignette  # noqa: E402
from tokens import accent_a, ink_a, shade_a  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
FPS = 30
COMP_ID = "talking-head-recut"

# ── pistas ─────────────────────────────────────────────────────────────────────
# Lo que va en una pista más alta tapa a lo de abajo. Dos clips a la vez en la
# MISMA pista es un error de solape, no un apilado.
TRK_VIDEO = 1       # metraje (los shots son consecutivos, nunca se solapan)
TRK_VIZ_MED = 2     # <video> de un visual — pista propia: comparte tramo con su host
TRK_BACKDROP = 3    # host del visual de fondo (velo + HUD)
TRK_CARD = 4        # tarjetas flotantes
TRK_TAKEOVER = 5    # visual que ocupa el lienzo
TRK_PIP = 6         # el creador en ventana, POR ENCIMA del takeover: cuando un
                    # gráfico ocupa el lienzo él sigue siendo el hilo conductor
TRK_CAPTION = 7     # subtítulos, siempre lo último
TRK_AUDIO = 10      # audio del metraje
TRK_MUSIC = 11      # cama musical
TRK_SFX = 12        # efectos, a partir de aquí (se reparten si se solapan)

# La voz de la pieza mide −19.8 dB de media. Todo lo demás vive por debajo.
SFX_TARGET_MEAN, SFX_PEAK_CAP = -27.0, -12.0
MUSIC_TARGET_MEAN = -34.0   # ~14 dB bajo la voz: se siente, no se escucha

# El metraje de iPhone llega con el audio PEGADO AL TECHO — la grabación de esta
# pieza ya trae 7690 muestras a 0 dB antes de que la toquemos. Sumarle música y
# efectos encima satura la mezcla, así que la voz se baja un poco para abrir
# cabecera. Y para que bajarla no cambie el balance, TODO lo demás se desplaza
# los mismos dB: el resultado suena igual, solo que sin recortar picos.
VOICE_GAIN = 0.70

ROOT = WORK = PUB = PIECE = None
W = H = None
FMT = "REEL"
T = None                     # escala tipográfica del formato
SRC_W = SRC_H = CHIN = CX = None
# El borde superior de la caja de cara (Mejora 2). `None` en una medición
# vieja sin `top_frac` — `check_face_top_clear` se salta limpio en ese caso,
# no rompe las piezas que ya están publicadas.
TOP_FRAC = None
SHOTS = CARDS = VISUALS = SFX = MUSIC = None
KEYWORDS = None
CAPTIONS = None
LAYOUT = {}         # bloque `layout` del plan (Tarea 3); {} si el plan no trae ninguno
CTA_PALABRA = None  # {"texto", "desde", "hasta"} del plan del CTA; None si no hay

CAPTION_SIZE = CAPTION_MAXW = CAPTION_MARGIN = None

# Holgura sobre la banda del hablante. El bloque se ancla por ABAJO (Mejora 5,
# a petición del usuario — antes era por arriba, con `BAND_CAP_PAD` de aire
# bajo el techo): el suelo es fijo y el techo del bloque sube o baja según
# cuántas líneas tenga, así que ya no hace falta un margen de aire por debajo
# del techo de la banda de texto — ese techo pasa a ser el LÍMITE del gate,
# no un punto de partida.
BAND_CAP_MARGIN = 16

# Margen al suelo de la banda `top` para un visual `band` sin `rect` (card de
# logo, CTA) — Mejora 6, a petición del usuario. Mismo valor que ya deja el
# `rect` de las grabaciones al suelo de esa banda (ry 100 + alto 540 = 640,
# 20px hasta y660): las cards de logo, las grabaciones y la card del CTA
# comparten el mismo borde inferior.
BAND_MOCK_MARGIN = 20
# En `formatos` el subtitulo se CENTRA sobre la costura (y960), asi que su mitad
# de arriba cae DENTRO de la banda del visual — que es lo contrario de `triband`,
# donde el subtitulo tenia una banda propia y el visual podia bajar hasta 20 px
# de su suelo. Con el margen de `triband` un mockup de la banda de arriba acaba
# en y940 y el bloque de subtitulo mas alto que el troceo puede producir (tres
# lineas de 92 px, techo en y822) se le monta encima: 118 px de texto sobre
# grafico. El margen de aqui deja el contenido acabando en y800, 22 px por
# encima de ese techo, y se calcula en vez de escribirse a mano:
#   H//2 - 3*linea_de_caption/2 - aire
# El 3 es el peor caso REAL del troceo, no un numero redondo: `CAPTION_MAXW*1.9`
# presupuesta dos lineas y la tercera es la que `caption_metrics` documenta como
# posible (el bloque que se envolvia a tres cuando la division daba dos).
BAND_FORMATOS_MARGIN = 160

# El primer plano de `cara` (encuadre `full`) se acerca hasta donde la fuente lo aguanta
# sin que se note el pixelado (doctrina 2026-09-29): con 1080×1920 hasta ×1,20; con una
# fuente 4K (lado corto ≥ 2160) hasta ×1,40, el primer plano cerrado de la referencia.
ZOOM_MAX_1080 = 1.20
ZOOM_MAX_4K = 1.40

# La palabra clave del CTA (doctrina 2026-09-29): serif itálica, 1,45 veces el tamaño del
# subtítulo, 12 px debajo de él, fija mientras dura el CTA.
CTA_KW_RATIO = 1.45
CTA_KW_GAP = 12


def q(t):
    """Cuantiza a frame y recorta a 4 decimales."""
    return round(round(float(t) * FPS) / FPS, 4)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── geometría ─────────────────────────────────────────────────────────────────
def canvas(fmt):
    return (1080, 1920) if fmt == "REEL" else (1920, 1080)


def split_panel():
    """Panel del metraje en modo split. En 9:16 el gráfico va arriba y el
    sujeto abajo; en 16:9 apilar deja franjas ilegibles, así que gira a
    vertical: gráfico a la izquierda, sujeto a la derecha."""
    if FMT == "YOUTUBE":
        x = round(W * 0.63)
        return dict(left=x, top=0, width=W - x, height=H)
    y = round(H * 0.40)
    return dict(left=0, top=y, width=W, height=H - y)


def pip_panel():
    """Ventana del creador. Va ARRIBA A LA DERECHA por eliminación: la banda de
    abajo es del subtítulo —que no se mueve de ahí— y el centro es del gráfico."""
    if FMT == "YOUTUBE":
        return dict(left=W - 420, top=100, width=380, height=340)
    return dict(left=W - 340, top=118, width=300, height=376)


def triband_panels():
    """Las tres bandas del layout triband, en coordenadas del lienzo.

    Van a ancho completo y NO a hueso: entre ellas queda suelo, que es
    lo que hace que la card de arriba flote en vez de parecer un recorte
    pegado. La geometría viene del EDL, no se inventa aquí.
    """
    if not LAYOUT:
        raise RuntimeError(
            "encuadre 'band' sin bloque `layout` en el plan: la geometría de las tres "
            "bandas la declara el EDL y el compilador la copia al plan")
    return {k: dict(left=0, top=v[0], width=W, height=v[1] - v[0])
            for k, v in LAYOUT["bands"].items()}


def shot_geometry(kind, zoom, anchor, anchor_x=0.5):
    """El rect ESTÁTICO del <video> de un encuadre.

    En `full` el truco del punch-in es una caja SOBREDIMENSIONADA con desborde
    negativo: el stage recorta y el sujeto crece. No se anima nada — el rect del
    <video> se resuelve una sola vez al cargar, así que un tween de geometría no
    reescala la imagen, solo la recorta (trampa 2 del renderer). Un encuadre
    nuevo es un ELEMENTO nuevo, y el salto entre ellos es el corte duro que pide
    el lenguaje de la pieza.

    `anchor` reparte el desborde VERTICAL y `anchor_x` el HORIZONTAL. El 0.5 por
    defecto es exactamente el `-(w - W) / 2` de siempre, así que una pieza que no
    declare `anchorX` —y una medición de cara sin `cx_frac`— dan el rect de antes
    bit a bit. Con `cx_frac` el crop ocurre alrededor de la CARA y no del centro
    geométrico del cuadro, que es la diferencia que se nota cuando el sujeto no
    está clavado en el medio.
    """
    if kind == "full":
        w, h = round(W * zoom), round(H * zoom)
        return dict(left=round(-(w - W) * anchor_x), top=round(-(h - H) * anchor),
                    width=w, height=h, objpos="50% 50%")
    if kind == "split":
        b = dict(split_panel())
        b["objpos"] = f"50% {round(anchor * 100, 2):g}%"
        return b
    if kind == "band":
        b = dict(triband_panels()["speaker"])
        b["objpos"] = f"50% {round(anchor * 100, 2):g}%"
        return b
    b = dict(pip_panel())
    b["objpos"] = f"50% {round(anchor * 100, 2):g}%"
    return b


def chin_at(shot):
    """Dónde cae la barbilla del sujeto EN EL LIENZO con este encuadre.

    Es lo que decide la altura del subtítulo. La barbilla se mide sobre el
    metraje (`measure-face.py`), nunca se estima: taparle la cara al creador es
    el error que más se nota y el único que no tiene arreglo en post.
    """
    kind, zoom, anchor = shot["kind"], shot["zoom"], shot["anchor"]
    if kind == "full":
        h = H * zoom
        return -(h - H) * anchor + CHIN * h
    if kind == "band":
        b = triband_panels()["speaker"]
    else:
        b = split_panel() if kind == "split" else pip_panel()
    # object-fit: cover — la escala la fija el lado que sobra
    scale = max(b["width"] / SRC_W, b["height"] / SRC_H)
    drawn_h = SRC_H * scale
    top = b["top"] - (drawn_h - b["height"]) * anchor
    return top + CHIN * drawn_h


# ── carga ─────────────────────────────────────────────────────────────────────
def configure(project, piece):
    global ROOT, WORK, PUB, PIECE, W, H, FMT, T, SRC_W, SRC_H, CHIN, CX, TOP_FRAC
    global SHOTS, CARDS, VISUALS, SFX, MUSIC, KEYWORDS, CAPTIONS, LAYOUT, CTA_PALABRA
    global CAPTION_SIZE, CAPTION_MAXW, CAPTION_MARGIN
    global SFX_TARGET_MEAN, SFX_PEAK_CAP, MUSIC_TARGET_MEAN, VOICE_GAIN

    ROOT, PIECE = project, str(piece)
    WORK = ROOT / "videos" / PIECE
    PUB = WORK / "public"
    plan_path = WORK / "plan.json"
    if not plan_path.exists():
        sys.exit(f"falta el plan de la pieza: {plan_path}\n"
                 f"Descríbela ahí (encuadres, tarjetas, visuales, sonido).")
    plan = json.loads(plan_path.read_text())
    palette = plan.get("palette")
    if palette not in TK.PALETTES:
        sys.exit(f"palette {palette!r} en {plan_path}: cada pieza declara la paleta de la "
                 f"marca, \"claro\" u \"oscuro\" (tokens.PALETTES). No hay paleta por defecto.")
    TK.use(palette)

    FMT = plan.get("format", "REEL").upper()
    W, H = canvas(FMT)
    T = TYPE[FMT]

    face_path = ROOT / "assets" / f"face-{PIECE}.json"
    if not face_path.exists():
        sys.exit(f"falta la medición de la cara: {face_path}\n"
                 f"Ejecuta: scripts/measure-face.py out/{PIECE}-rough.mp4 {face_path}")
    face = json.loads(face_path.read_text())
    SRC_W, SRC_H, CHIN = face["width"], face["height"], face["chin_frac"]
    # Una medición de antes de la Tarea 8 no trae centroide. El 0.5 de reserva
    # es el centro geométrico: exactamente lo que se venía haciendo, así que las
    # piezas 1-9 recompilan idénticas.
    CX = float(face.get("cx_frac", 0.5))
    # `top_frac` es de la Mejora 2: una medición de antes no lo trae, y
    # `check_face_top_clear` lo trata como "no verificable" en vez de inventar
    # un valor — más vale no comprobar que comprobar con un número que nadie
    # midió.
    TOP_FRAC = float(face["top_frac"]) if "top_frac" in face else None

    SHOTS = plan["shots"]
    CARDS = plan.get("cards", [])
    VISUALS = plan.get("visuals", [])
    SFX = [tuple(x) for x in plan.get("sfx", [])]
    MUSIC = plan.get("music")
    KEYWORDS = plan.get("keywords", [])
    # Bloques declarados por el EDL (rangos de palabras). Si no vienen,
    # `build_captions` trocea como siempre: las piezas 1-9 no los traen.
    CAPTIONS = plan.get("captions") or None
    try:
        LAYOUT = layout_formatos.resolver(plan.get("layout"), H)
    except layout_formatos.LayoutError as e:
        sys.exit(f"{plan_path}: {e}")
    CTA_PALABRA = plan.get("cta_palabra") or None
    if CTA_PALABRA is not None and (not str(CTA_PALABRA.get("texto", "")).strip()
                                    or not isinstance(CTA_PALABRA.get("desde"), (int, float))):
        sys.exit(f"{plan_path}: `cta_palabra` necesita `texto` y `desde` (segundos de la versión)")
    SFX_TARGET_MEAN = plan.get("sfx_target_mean", -27.0)
    SFX_PEAK_CAP = plan.get("sfx_peak_cap", -12.0)

    # Un solo mando: bajar la voz desplaza la mezcla entera los mismos dB, así
    # que la cabecera aparece sin que cambie la relación voz / efectos / música.
    VOICE_GAIN = float(plan.get("voice_gain", 0.70))
    shift = 20 * math.log10(max(0.01, VOICE_GAIN))
    SFX_TARGET_MEAN += shift
    SFX_PEAK_CAP += shift
    MUSIC_TARGET_MEAN = plan.get("music", {}).get("target_mean", -34.0) + shift
    print(f"  mezcla: voz ×{VOICE_GAIN} ({shift:+.2f} dB) · efectos "
          f"{SFX_TARGET_MEAN:.1f} dB media / {SFX_PEAK_CAP:.1f} dB pico · "
          f"música {MUSIC_TARGET_MEAN:.1f} dB")

    CAPTION_SIZE = plan.get("caption_size", T["caption"])
    CAPTION_MAXW = round(W * 0.84)
    CAPTION_MARGIN = round(W * 0.07)


def load():
    tr = json.loads((ROOT / "transcripts" / f"{PIECE}.json").read_text())
    plan = json.loads((ROOT / "cuts" / f"{PIECE}.json").read_text())
    keeps = plan["keeps"]
    dur = round(sum(k["dur"] for k in keeps), 3)

    def remap(t):
        acc = 0.0
        for k in keeps:
            if t < k["start"]:
                return acc
            if t <= k["end"]:
                return acc + (t - k["start"])
            acc += k["dur"]
        return acc

    words = [{"text": w["text"], "start": remap(w["start"] / 1000),
              "end": remap(w["end"] / 1000)} for w in tr["words"]]
    return words, dur


def measure_font(size):
    """Inter 900 real, para cortar los bloques con métricas y no contando letras.

    Delegado a `caption_fonts` para que `caption_metrics` pueda medir sin
    importar este archivo (que no es importable: lleva guion). El .ttf se
    sigue cacheando en el directorio de la PIEZA, igual que antes.
    """
    return caption_fonts.measure_font(size, cache_dir=WORK)


# ── capa de METRAJE — encuadres y punch-ins ───────────────────────────────────
def build_shots(dur):
    """Un <video> estático por encuadre. Ese es todo el secreto del punch-in.

    Los encuadres `off` no emiten elemento: son los tramos que un visual a
    pantalla completa está tapando, y mantener ahí un <video> invisible solo
    gastaría memoria de decodificación.
    """
    shots = []
    for i, s in enumerate(SHOTS):
        kind = s.get("kind", "full")
        shots.append(dict(
            start=q(s["at"]), kind=kind,
            zoom=float(s.get("zoom", 1.0)),
            anchor=float(s.get("anchor", 0.5 if kind == "full" else 0.40)),
            # El plan manda sobre la medición: un encuadre puede pedir otro
            # anclaje (dejar aire a un lado para un rótulo, por ejemplo).
            anchor_x=float(s.get("anchorX", CX)),
        ))
    shots.sort(key=lambda x: x["start"])
    for i, s in enumerate(shots):
        s["end"] = shots[i + 1]["start"] if i + 1 < len(shots) else q(dur)

    els = []
    for i, s in enumerate(shots):
        if s["kind"] == "off" or s["end"] - s["start"] < 1.0 / FPS:
            continue
        g = shot_geometry(s["kind"], s["zoom"], s["anchor"], s["anchor_x"])
        cls = {"full": "vid", "split": "vid panel",
               "pip": "vid pip", "band": "vid band"}[s["kind"]]
        track = TRK_PIP if s["kind"] == "pip" else TRK_VIDEO
        els.append(
            f'  <video class="{cls} clip" id="shot-{i:02d}" src="input-video.mp4"\n'
            f'         muted playsinline\n'
            f'         style="left:{g["left"]}px;top:{g["top"]}px;'
            f'width:{g["width"]}px;height:{g["height"]}px;'
            f'object-position:{g["objpos"]}"\n'
            f'         data-start="{s["start"]:.4f}" '
            f'data-duration="{s["end"] - s["start"]:.4f}"\n'
            f'         data-media-start="{s["start"]:.4f}" '
            f'data-track-index="{track}"></video>')
    return shots, els


def shot_at(shots, t):
    for s in shots:
        if s["start"] <= t < s["end"]:
            return s
    return shots[-1] if shots else None


def check_no_black(shots, dur):
    """Ningún instante puede quedarse sin metraje NI sin visual opaco.

    Es la trampa 6 del renderer y la más difícil de ver revisando el plan: un
    `off` que empieza en el mismo segundo que el takeover deja el frame vacío
    justo mientras el takeover está fundiendo, y esos 0.15-0.25 s de suelo
    liso se leen como un fallo del video. En el navegador no se nota porque
    uno no mira ese cuarto de segundo; en el MP4 sí.

    La regla es fija, así que no hace falta recordarla: el encuadre se queda
    hasta `start + fade_in` del visual que lo tapa, y el siguiente entra en
    `end - fade_out`. Aquí se comprueba y se dice el número exacto que falta.
    """
    # tramos con el creador en pantalla
    cover = [(s["start"], s["end"]) for s in shots if s["kind"] != "off"]
    # + tramos en los que un visual OPACO ya está del todo puesto
    for v in VISUALS:
        if v.get("role") == "backdrop":
            continue                      # deja ver el metraje: no tapa nada
        s = float(v["start"])
        e = float(v["end"]) if v.get("end") is not None else dur
        cover.append((s + float(v.get("fade_in", 0.28)),
                      e - float(v.get("fade_out", 0.26))))

    cover.sort()
    holes, cursor = [], 0.0
    for a, b in cover:
        if a > cursor + 1.0 / FPS:
            holes.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < dur - 1.0 / FPS:
        holes.append((cursor, dur))

    if not holes:
        return
    msg = ["el plan deja el frame VACÍO (trampa 6: se ve negro en el MP4):"]
    for a, b in holes:
        msg.append(f"  {a:6.2f} - {b:6.2f}  ({b - a:.2f}s sin metraje ni visual)")
        nxt = min((v for v in VISUALS if float(v["start"]) >= a - 0.01),
                  key=lambda v: float(v["start"]), default=None)
        if nxt and abs(float(nxt["start"]) - a) < 0.6:
            fi = float(nxt.get("fade_in", 0.28))
            msg.append(f"     el `off` debe empezar en "
                       f"{float(nxt['start']) + fi:.2f} "
                       f"(start {float(nxt['start']):.2f} + fade_in {fi:.2f}) "
                       f"de «{nxt['id']}», no antes")
        prv = max((v for v in VISUALS
                   if v.get("end") is not None and float(v["end"]) <= b + 0.01),
                  key=lambda v: float(v["end"]), default=None)
        if prv and abs(float(prv["end"]) - b) < 0.6:
            fo = float(prv.get("fade_out", 0.26))
            msg.append(f"     el encuadre siguiente debe entrar en "
                       f"{float(prv['end']) - fo:.2f} "
                       f"(end {float(prv['end']):.2f} − fade_out {fo:.2f}) "
                       f"de «{prv['id']}», no después")
    sys.exit("\n".join(msg))


def check_band_speaker_clear(shots, dur):
    """El hablante de la banda `speaker` no puede quedar tapado por un mockup opaco.

    Es la comprobación que falta para que la Tarea 9c no vuelva a saltarse: hoy
    conviven DOS mecanismos que suben un visual a la banda de arriba —`band`,
    que confina el host al rect de la banda y deja el fondo transparente
    (`build_visuals`), y `mock_pad_bottom`, que solo EMPUJA el gráfico hacia
    arriba con relleno, sin tocar la opacidad del host— y nada avisaba si un
    plan usaba el segundo sin el primero. Le pasó al `v-cta` de la pieza 15:
    se quedó con `mock_pad_bottom` y sin `band`, así que conservó un host a
    lienzo completo con fondo opaco encima de un encuadre `kind: "band"` — los
    últimos 2 s de la pieza, luma máxima 41 en la banda del hablante donde
    debía verse el presentador.

    La regla: un visual `kind: "mockup"` sin `band` es OPACO (`build_visuals`,
    `opaque = v["kind"] == "mockup" and not band`) y ocupa el lienzo entero, así
    que NO puede solapar en el tiempo con un encuadre `kind: "band"` — ese
    encuadre confina el metraje a la banda de abajo precisamente para que el
    hablante se siga viendo, y un host opaco por encima lo tapa igual que
    taparía cualquier otro metraje.
    """
    band_shots = [s for s in shots if s["kind"] == "band"]
    if not band_shots:
        return
    for v in VISUALS:
        if v.get("kind") != "mockup" or v.get("band"):
            continue          # con `band` el host se confina y el fondo es transparente
        s = q(float(v["start"]))
        e = q(dur if v.get("end") is None else min(float(v["end"]), dur))
        for shot in band_shots:
            lo, hi = max(s, shot["start"]), min(e, shot["end"])
            if hi - lo > 1.0 / FPS:
                sys.exit(
                    f"visual «{v['id']}» es un mockup OPACO (kind:\"mockup\" sin "
                    f"`band`) y solapa {lo:.2f}-{hi:.2f}s con el encuadre "
                    f"`band` {shot['start']:.2f}-{shot['end']:.2f}s: su host a "
                    f"lienzo completo tapa al hablante en la banda `speaker` "
                    f"durante ese tramo.\n"
                    f"  arréglalo declarando `\"band\": \"top\"` en «{v['id']}» "
                    f"— confina el host al rect de esa banda y deja el fondo "
                    f"transparente. `mock_pad_bottom` NO basta: solo sube el "
                    f"gráfico, no toca la opacidad del host.")


def face_top_y(shot):
    """El borde superior de la cara EN EL LIENZO en un encuadre `band`.

    La misma cuenta que `chin_at` para `band` (el rect de la banda `speaker`, la escala de
    `object-fit: cover` y el reparto del desborde por `anchor`), proyectando `TOP_FRAC`
    en vez de `CHIN`. None si la medición de la cara no trae `top_frac`.
    """
    if TOP_FRAC is None:
        return None
    b = triband_panels()["speaker"]
    scale = max(b["width"] / SRC_W, b["height"] / SRC_H)
    drawn_h = SRC_H * scale
    top = b["top"] - (drawn_h - b["height"]) * shot["anchor"]
    return top + TOP_FRAC * drawn_h


def check_face_top_clear(shots, dur):
    """La cara no puede entrar CORTADA por arriba en un encuadre `band` (Mejora 2).

    Es la restricción dura de la ronda: con `object-fit: cover`, un `anchor`
    demasiado ALTO recorta más del techo de la fuente y se lleva la coronilla
    por delante — el error no tiene arreglo en post, así que tiene que parar
    la compilación, no colarse hasta el MP4 (la misma filosofía que
    `check_band_speaker_clear`, al lado de la cual vive esta función).

    La cuenta reutiliza la MISMA fórmula que `chin_at` para el kind `band`
    —el rect de la banda `speaker`, la escala de `object-fit: cover` y el
    reparto del desborde vertical por `anchor`— pero proyecta `TOP_FRAC` (el
    borde superior de la caja de cara, medido por `measure-face.py`) en vez de
    `CHIN`. Si ese punto cae POR ENCIMA del techo de la banda `speaker` —en
    coordenadas de lienzo, un y menor que `triband_panels()["speaker"]["top"]`—
    la cabeza queda cortada y el compilador para.

    `TOP_FRAC` es `None` en una medición de antes de la Mejora 2
    (`assets/face-N.json` sin el campo): el gate se salta limpio en vez de
    reventar, para no romper ninguna pieza vieja.
    """
    if TOP_FRAC is None:
        return
    band_shots = [s for s in shots if s["kind"] == "band"]
    if not band_shots:
        return
    speaker_top = triband_panels()["speaker"]["top"]
    for shot in band_shots:
        face_top = face_top_y(shot)
        if face_top < speaker_top:
            sys.exit(
                f"encuadre `band` {shot['start']:.2f}-{shot['end']:.2f}s: con "
                f"anchor {shot['anchor']:.2f} el borde superior de la cara cae "
                f"en y{face_top:.0f}, POR ENCIMA del techo de la banda "
                f"`speaker` (y{speaker_top}) — la cabeza queda cortada.\n"
                f"  baja el `anchor` de ese encuadre (con object-fit: cover, a "
                f"menos anchor se ve más del techo de la fuente) y vuelve a "
                f"medir con `measure-face.py` si hace falta, nunca a ojo.")


def zoom_max():
    """El acercamiento máximo de `cara` para la resolución de esta fuente."""
    return ZOOM_MAX_4K if min(SRC_W, SRC_H) >= 2160 else ZOOM_MAX_1080


def check_cara_zoom(shots):
    """Ningún encuadre `full` se acerca más de lo que la fuente aguanta."""
    tope = zoom_max()
    for s in shots:
        if s["kind"] == "full" and s["zoom"] > tope + 1e-9:
            sys.exit(
                f"encuadre `full` {s['start']:.2f}s con zoom {s['zoom']:.2f}: con una fuente "
                f"de {SRC_W}×{SRC_H} el acercamiento llega a ×{tope:.2f} sin que se note el "
                f"pixelado. Baja el zoom a {tope:.2f}, o graba en 4K para llegar a "
                f"×{ZOOM_MAX_4K:.2f}.")


def check_band_top_covered(shots, dur):
    """La banda `top` no puede quedarse vacía durante un tramo `band`.

    Doctrina de 2026-09-15, a petición del usuario: «en la parte de
    animaciones siempre se debe mostrar algo, en cualquier segundo, nunca
    debe estar el fondo vacío». Medido en la pieza 15 antes de este gate: la
    banda de arriba se quedaba en suelo liso **15.0 s de 55.3 s
    (27 %)** de sus tramos `band`, en siete huecos — desde 0.86 s (el
    arranque, antes de la primera card) hasta 5.98 s (el beat de la guía,
    antes del CTA).

    **La resolución de la tensión, y no se toca**: esta regla choca con
    «nada entra antes de su palabra» (§7 / `references/visuals.md`) — no se
    puede adelantar la card SIGUIENTE para tapar el hueco, porque entonces el
    espectador lee el nombre de la herramienta antes de que se diga. La
    salida es **sostener el visual ANTERIOR hasta que entra el siguiente**
    (extender su `end`, nunca adelantar el `start` del que viene): el visual
    saliente cubre el hueco con algo que ya fue dicho, el entrante sigue
    esperando su palabra. Es la misma idea que ya usa `check_no_black` para
    el metraje, aplicada aquí a los visuales de la banda `top`. El hueco de
    ARRANQUE (nada delante que sostener) se cierra al revés: moviendo el
    `at` del propio encuadre `band` para que coincida con la entrada de la
    primera card, no con un visual.

    **«Ocupar la banda» tiene DOS mecanismos, no uno** — los mismos que ya
    conviven en `build_visuals`: un `kind: "mockup"` con `band: "top"` (una
    card de logo, el CTA) confina su host al rect exacto de esa banda; un
    `kind: "screen-video"` (una grabación) nunca declara `band` — su
    `<video>` real se coloca con `rect` en coordenadas de LIENZO, siempre con
    host transparente por ser `screen-video` — así que cuenta si su `rect`
    solapa verticalmente con la banda `top`. Mirar solo `band=="top"` se
    comprobó y deja fuera las cinco grabaciones enteras de la pieza 15 —
    falso positivo del tamaño de la pieza, cazado verificando este mismo
    gate contra el plan sin arreglar antes de escribir el fix.

    La cuenta usa las ventanas CRUDAS `start`/`end` de cada visual que ocupa
    la banda, sin el margen de `fade_in`/`fade_out` que sí aplica
    `check_no_black`: dos visuales de banda que se TOCAN exactamente (la
    card de logo y su propia grabación, ya contiguas en las cinco
    herramientas) hacen un cruce de opacidades legítimo en ese instante, no
    un hueco — medirlo con margen de fundido marcaría en falso esas cinco
    transiciones que ya funcionan. Tolerancia de un frame (1/FPS), igual que
    `check_band_speaker_clear`, para no fallar por redondeo de cuantización.
    """
    band_shots = [s for s in shots if s["kind"] == "band"]
    if not band_shots:
        return
    frame = 1.0 / FPS
    top = triband_panels()["top"]
    top_y0, top_y1 = top["top"], top["top"] + top["height"]

    def covers_top(v):
        if v.get("band") == "top":
            return True
        rect = v.get("rect")
        if not rect:
            return False
        _, ry, _, rh = rect
        return ry < top_y1 and ry + rh > top_y0

    # tramos `band` fundidos en intervalos contiguos (varios encuadres band
    # seguidos, cada uno con su propio anchor, cuentan como un solo tramo)
    band_ranges = sorted((s["start"], s["end"]) for s in band_shots)
    merged = []
    for a, b in band_ranges:
        if merged and a <= merged[-1][1] + frame:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))

    cover = sorted(
        (q(float(v["start"])), q(dur if v.get("end") is None else min(float(v["end"]), dur)))
        for v in VISUALS if covers_top(v))

    holes = []
    for band_start, band_end in merged:
        cursor = band_start
        for a, b in cover:
            a, b = max(a, band_start), min(b, band_end)
            if b <= a:
                continue
            if a > cursor + frame:
                holes.append((cursor, a))
            cursor = max(cursor, b)
        if cursor < band_end - frame:
            holes.append((cursor, band_end))

    if not holes:
        return
    msg = ["la banda `top` queda VACÍA durante un tramo `band` — la doctrina "
           "exige que siempre se muestre algo, en cualquier segundo:"]
    for a, b in holes:
        msg.append(f"  {a:6.2f} - {b:6.2f}  ({b - a:.2f}s de banda `top` vacía)")
    msg.append(
        "  arréglalo SOSTENIENDO el visual `band: \"top\"` ANTERIOR hasta que "
        "entra el siguiente (extiende su `end`) — nunca adelantando el "
        "siguiente antes de su palabra. Si el hueco es el de ARRANQUE (nada "
        "delante que sostener), mueve el `at` del propio encuadre `band` "
        "para que coincida con la entrada de la primera card.")
    sys.exit("\n".join(msg))


def check_layout_default():
    """Todo REEL declara su layout.

    Desde la doctrina de 2026-09-29 el de por defecto es `formatos` (cara · partida ·
    gráfico, references/formatos.md); el `triband` queda para las piezas de antes y
    `none` es la escotilla para renunciar a sabiendas. YOUTUBE queda fuera: los dos son
    repartos verticales y en 16:9 no hay banda de arriba que llenar. Un gate sin salida
    documentada acaba comentado, así que el mensaje dice las dos salidas.
    """
    if FMT != "REEL" or LAYOUT:
        return
    sys.exit(
        "pieza REEL sin bloque `layout` en el plan: desde la doctrina de 2026-09-29 todo "
        "reel va en tres formatos (cara · partida · gráfico).\n"
        "  declara `\"layout\": {\"mode\": \"formatos\"}` (references/formatos.md), o si "
        "esta pieza concreta de verdad no lo necesita, renuncia a sabiendas con la "
        "escotilla documentada: `\"layout\": {\"mode\": \"none\"}`.")


# ── capa de VISUALES ──────────────────────────────────────────────────────────
def build_visuals(dur):
    """Materializa VISUALS. Devuelve (css, media suelta, hosts, anims, skins).

    Los <video> van al NIVEL RAÍZ del stage, no dentro de su host: media
    anidada en un elemento temporizado se CONGELA en el render.
    """
    css, media, anims, skins = [], [], [], []
    hosts_back, hosts_over = [], []
    assets = set()

    for v in VISUALS:
        vid = v["id"]
        s = q(v["start"])
        e = q(dur if v.get("end") is None else min(v["end"], dur))
        d = e - s
        track = TRK_BACKDROP if v["role"] == "backdrop" else TRK_TAKEOVER
        skins.append((s, e, v.get("skin", "on-dark"), v.get("cap_top")))

        # Assets auxiliares de un mockup (imágenes referenciadas desde su
        # HTML, no media raíz). Las rutas son relativas a assets/ y entran al
        # mismo conjunto que `image`/`screen-video`, para que build() las
        # copie a public/ con su jerarquía. El gate vive aquí —antes de
        # despachar el componente— para fallar con el nombre declarado y no
        # entregar una imagen rota al navegador.
        for rel in v.get("assets", []):
            if not isinstance(rel, str) or not (ROOT / "assets" / rel).is_file():
                sys.exit(f"visual «{vid}»: asset declarado no existe: {rel}")
            assets.add(rel)

        # `band` confina el HOST de este visual a una banda del triband en vez
        # de dárselo el lienzo entero. Convive con `role`, no lo sustituye:
        # `role` sigue decidiendo la PISTA (`backdrop`/`takeover`, línea de
        # arriba); `band` decide la GEOMETRÍA. Una card de logo sigue siendo
        # un takeover en el apilado — solo que su rect ya no es el lienzo.
        # Sin bloque `layout` no hay bandas de dónde sacar el rect, y eso no
        # cae a un default silencioso (arreglo de la Tarea 9c: con el host a
        # lienzo completo, el `.vizbg` opaco del mockup tapaba la banda del
        # hablante durante las cinco cards de logo — luma máxima 28 medida
        # sobre el MP4 donde debía verse la camiseta blanca).
        band = v.get("band")
        if band:
            if not LAYOUT:
                sys.exit(
                    f"visual «{vid}» declara band:\"{band}\" pero el plan no "
                    f"trae bloque `layout`: la geometría de las bandas la pone "
                    f"el EDL, no hay default silencioso — añade `layout` al "
                    f"plan o quita `band` de «{vid}»")
            host_rect = triband_panels()[band]
        else:
            host_rect = dict(left=0, top=0, width=W, height=H)

        if v.get("hud"):
            hud_css, hud_html, hud_anims = mockups.hud(vid, *v["hud"])
        else:
            hud_css, hud_html, hud_anims = "", "", []
        body_css, body_html_, body_anims = "", "", []

        if v["kind"] == "mockup":
            which, kw = v["mock"]
            kw = dict(kw)
            # Los tiempos de un mockup se escriben en la línea del CORTE (que es
            # donde vive el transcript) y aquí se pasan a offsets del visual.
            if v.get("absolute_times"):
                for key in ("switch_at", "draw_at", "at", "stamp_at",
                            "offer_at", "common_at"):
                    if key in kw:
                        # `step_grid` (pieza 17) trae `None` en los slots que
                        # todavía son un hueco: ese None es el DATO —esta
                        # casilla no se llena en esta instancia— y tiene que
                        # sobrevivir al remapeo, no reventarlo.
                        kw[key] = [None if t is None else q(t - s)
                                   for t in kw[key]]
                # `rewrite_line` lleva su tiempo DENTRO de cada fragmento, así
                # que el bucle de claves planas no lo alcanza. Se escribe en la
                # línea del corte como todo lo demás y aquí baja a offsets.
                # Pieza 3. `archivos_fila` y `abanico_archivos` llevan
                # el tiempo DENTRO de cada archivo de la lista, igual que
                # `parts` en `rewrite_line`: un archivo sabe cuando suelta SU
                # patron, y sacarlo a una lista paralela de tiempos obligaria a
                # contar posiciones a mano. Sin este remapeo llegarian al
                # componente en la linea del corte y se sumarian dos veces, la
                # trampa que documenta `motion_stage`.
                for key in ("items", "slots"):
                    if key in kw and kw[key] and isinstance(kw[key][0], dict):
                        kw[key] = [d if d.get("at") is None
                                   else dict(d, at=q(d["at"] - s))
                                   for d in kw[key]]
                if "parts" in kw:
                    kw["parts"] = [dict(pt, at=q(pt["at"] - s))
                                   for pt in kw["parts"]]
                # Pieza 18. `idea_fate` y `agent_editor` llevan el tiempo
                # DENTRO de cada tupla (etiqueta, t) en vez de en una lista
                # aparte, igual que `parts` en `rewrite_line`: sin esto
                # llegarían al componente en la línea del corte y se sumarían
                # dos veces, que es la trampa que documenta `motion_stage`.
                for key in ("exits", "layers"):
                    if key in kw:
                        kw[key] = [[lab, q(t - s)] for lab, t in kw[key]]
                # `fill_at` es el escalar de `motion_demo` en su variante
                # `recap` — el instante en que la palabra rellena el hueco.
                if kw.get("fill_at") is not None:
                    kw["fill_at"] = q(kw["fill_at"] - s)
                # Escalares. `connector_at` y `layer_at` los trajo la pieza
                # 16: la pastilla del conector de `claude_prompt` y la bajada
                # de la capa de `layer_stack` se escriben en la línea del
                # corte como todo lo demás, y sin estar en esta lista
                # llegarían al componente como tiempo ABSOLUTO y se sumarían
                # dos veces (la misma trampa que documenta `motion_stage`).
                for key in ("alert_at", "type_at", "send_at", "connector_at",
                            "layer_at", "attach_at", "gap_at", "missing_at",
                            "strike_at", "after_at",
                            # pieza 3
                            "scan_at", "cerrar_at", "nombre_at",
                            "sello_at", "kicker_at"):
                    if kw.get(key) is not None:
                        kw[key] = q(kw[key] - s)
            fn = {"app_switch": mockups.app_switch,
                  "connection_map": mockups.connection_map,
                  "stat_grid": mockups.stat_grid,
                  "keyword_hero": mockups.keyword_hero,
                  "flow_steps": mockups.flow_steps,
                  "rate_mismatch": mockups.rate_mismatch,
                  "chip_grid": mockups.chip_grid,
                  "comment_ui": mockups.comment_ui,
                  "chat_unanswered": mockups.chat_unanswered,
                  "tool_card": mockups.tool_card,
                  "tool_lineup": mockups.tool_lineup,
                  "tool_pair": mockups.tool_pair,
                  "claude_prompt": mockups.claude_prompt,
                  "layer_stack": mockups.layer_stack,
                  "step_grid": mockups.step_grid,
                  "cv_echo": mockups.cv_echo,
                  "cv_vs_offer": mockups.cv_vs_offer,
                  "offer_stack": mockups.offer_stack,
                  "rewrite_line": mockups.rewrite_line,
                  "interview_chat": mockups.interview_chat,
                  "keyframe_grind": mockups.keyframe_grind,
                  "agent_editor": mockups.agent_editor,
                  "motion_demo": mockups.motion_demo,
                  "idea_fate": mockups.idea_fate,
                  "idea_veneer": mockups.idea_veneer,
                  "agent_swarm": mockups.agent_swarm,
                  "desktop_manager": mockups.desktop_manager,
                  "split_problem": mockups.split_problem,
                  "video_pipeline": mockups.video_pipeline,
                  "money_button": mockups.money_button,
                  "video_output": mockups.video_output,
                  "tradeoff_bars": mockups.tradeoff_bars,
                  "archivo_marcado": mockups.archivo_marcado,
                  "archivos_fila": mockups.archivos_fila,
                  "abanico_archivos": mockups.abanico_archivos,
                  "contador_horas": mockups.contador_horas,
                  "teclado_enter": mockups.teclado_enter,
                  "repo_card": mockups.repo_card,
                  "inspector_archivo": mockups.inspector_archivo,
                  "ig_perfil": mockups_reels.ig_perfil,
                  "ig_barras": mockups_reels.ig_barras,
                  "ig_busqueda": mockups_reels.ig_busqueda,
                  "ig_guardar": mockups_reels.ig_guardar,
                  "monigote": mockups_reels.monigote,
                  "nudo_viaje": mockups_reels.nudo_viaje,
                  "ideas_notas": mockups_reels.ideas_notas,
                  "claude_chat": mockups_reels.claude_chat,
                  "escaneo": mockups_reels.escaneo,
                  "prompt_encaje": mockups_reels.prompt_encaje,
                  "prompt_hoja": mockups_reels.prompt_hoja,
                  "tablero": mockups_reels.tablero,
                  "reel_tarjeta": mockups_reels.reel_tarjeta,
                  "reel_cascada": mockups_reels.reel_cascada,
                  "ig_grilla": mockups_reels.ig_grilla,
                  "guion_esqueleto": mockups_reels.guion_esqueleto,
                  "chatgpt_chat": mockups_chatgpt.chatgpt_chat,
                  "imagen_resultado": mockups_chatgpt.imagen_resultado,
                  "parpadeo_estados": mockups_chatgpt.parpadeo_estados,
                  "lista_codigos": mockups_chatgpt.lista_codigos,
                  "cc_gancho": mockups_codex.cc_gancho,
                  "plan_medidor": mockups_codex.plan_medidor,
                  "cuenta_chatgpt": mockups_codex.cuenta_chatgpt,
                  "instalacion": mockups_codex.instalacion,
                  "error_trabado": mockups_codex.error_trabado,
                  "revision_diff": mockups_codex.revision_diff,
                  "bloque_cuestiona": mockups_codex.bloque_cuestiona,
                  "claude_md": mockups_codex.claude_md,
                  "marcador_fallas": mockups_codex.marcador_fallas,
                  "dv_gancho": mockups_davinci.dv_gancho,
                  "dv_precio": mockups_davinci.dv_precio,
                  "dv_balanza": mockups_davinci.dv_balanza,
                  "dv_linea": mockups_davinci.dv_linea,
                  "dv_enchufe": mockups_davinci.dv_enchufe,
                  "dv_pedido": mockups_davinci.dv_pedido,
                  "dv_color": mockups_davinci.dv_color,
                  "dv_graficos": mockups_davinci.dv_graficos,
                  "dv_multicam": mockups_davinci.dv_multicam,
                  "dv_sonido": mockups_davinci.dv_sonido,
                  "dv_musica": mockups_davinci.dv_musica,
                  "dv_pozo": mockups_davinci.dv_pozo,
                  "dv_genera": mockups_davinci.dv_genera,
                  "dv_encastra": mockups_davinci.dv_encastra,
                  "dv_higgsfield": mockups_davinci.dv_higgsfield,
                  "dv_editor": mockups_davinci.dv_editor,
                  "dv_guia": mockups_davinci.dv_guia,
                  "terminal_barrera": mockups_plugins.terminal_barrera,
                  "zocalo": mockups_plugins.zocalo,
                  "anillo_proveedores": mockups_plugins.anillo_proveedores,
                  "costo_llaves": mockups_plugins.costo_llaves,
                  "piedras_modelo": mockups_plugins.piedras_modelo,
                  "contador_tokens": mockups_plugins.contador_tokens,
                  "dos_terminales": mockups_plugins.dos_terminales,
                  "cable_headroom": mockups_plugins.cable_headroom,
                  "prensa": mockups_plugins.prensa,
                  "dos_salidas": mockups_plugins.dos_salidas,
                  "sello_oficial": mockups_plugins.sello_oficial,
                  "arbol_escaneo": mockups_plugins.arbol_escaneo,
                  "servidor_mcp": mockups_plugins.servidor_mcp,
                  "mascota_cuaderno": mockups_plugins.mascota_cuaderno,
                  "reloj_fondo": mockups_plugins.reloj_fondo,
                  "motion_stage": objects.motion_stage}[which]
            body_css, body_html_, body_anims = fn(vid, **kw)
        elif v["kind"] == "image":
            assets.add(v["src"])
            body_html_ = f'<img class="vizimg" id="{vid}-img" src="{v["src"]}" alt="" />'
        elif v["kind"] in ("video", "screen-video"):
            assets.add(v["src"])
            # `rect` coloca el clip como una TARJETA dentro del lienzo en vez de
            # a sangre. Lo que la rodea decide cuánta interfaz se ve: el panel
            # (por defecto) no gasta alto en nada que leer, así que la captura
            # entra más grande; `chrome` dibuja la barra de navegador y cuesta
            # 74 px de alto — solo cuando hace falta declarar que es la web.
            rx, ry, rw, rh = v.get("rect", [0, 0, W, H])
            # Las esquinas superiores cuadradas son SOLO para la barra de
            # `chrome` (`.bframe`, 74 px encima del rect): si `tool_recording`
            # gana el despacho de más abajo, `.tr-panel` redondea las CUATRO
            # esquinas y el <video> que enmarca tiene que ir parejo, o la
            # esquina cuadrada de `chrome` asoma bajo el marco (Tarea 8b,
            # ronda de revisión 1).
            radius = (f"0 0 {RADIUS['lg']}px {RADIUS['lg']}px"
                      if v.get("chrome") and not v.get("tool_recording")
                      else f"{RADIUS['lg']}px")
            media.append(
                f'  <video class="vizmed clip" id="{vid}-med" src="{v["src"]}"\n'
                f'         muted playsinline\n'
                f'         style="left:{rx}px;top:{ry}px;width:{rw}px;height:{rh}px;'
                f'border-radius:{radius}"\n'
                f'         data-start="{s:.4f}" data-duration="{d:.4f}"\n'
                f'         data-media-start="0.0000" data-track-index="{TRK_VIZ_MED}"></video>')
            if v["kind"] == "screen-video":
                clicks = [(q(t - s), x, y, label) for t, x, y, label in v.get("clicks", [])]
                boxes = [(q(a - s), q(b - s), x, y, bw, bh)
                         for a, b, x, y, bw, bh in v.get("boxes", [])]
                body_css, body_html_, body_anims = mockups.screen_overlay(vid, clicks, boxes)
            if v.get("tool_recording"):
                # Igual trato que `chrome`/`panel`: no dibuja el <video>, se
                # dibuja ALREDEDOR de su `rect` — por eso lee `rect` directo
                # del visual y no de un `kw` de mockup (Tarea 8b).
                tr = v["tool_recording"]
                c_css, c_html, c_anims = mockups.tool_recording(
                    vid, tr["slug"], tr["name"], (rx, ry, rw, rh),
                    tr.get("hairline", 1))
            elif v.get("chrome"):
                ch = v["chrome"]
                c_css, c_html, c_anims = mockups.browser_frame(
                    vid, (rx, ry, rw, rh), ch.get("url", ""), ch.get("brand", ""))
            elif v.get("rect") and v.get("panel") is not False:
                # Solo si es una TARJETA: a sangre no hay nada que enmarcar y el
                # aro acabaría dibujando un borde alrededor del lienzo entero.
                pn = v.get("panel") if isinstance(v.get("panel"), dict) else {}
                c_css, c_html, c_anims = mockups.screen_panel(
                    vid, (rx, ry, rw, rh), pn.get("label", ""))
            else:
                c_css, c_html, c_anims = "", "", []
            body_css += c_css
            body_html_ += c_html
            body_anims = list(body_anims) + c_anims

        # Un mockup necesita fondo OPACO o se ve el metraje por detrás — pero
        # eso es lo correcto para un mockup que SUSTITUYE el metraje (kind
        # "takeover" a lienzo completo), no para uno que vive dentro de una
        # banda y tiene que dejar ver el metraje de las OTRAS bandas (la del
        # hablante). Con `band`, el fondo es transparente siempre.
        opaque = v["kind"] == "mockup" and not band
        bg = f"{grid()},{vignette()}" if opaque else "transparent"
        css.append(f"""
.viz[data-viz-id="{vid}"] .vizbg{{position:absolute;inset:0;background:{bg}}}""")
        css.append(hud_css)
        if body_css:
            css.append(body_css)

        veil = (f'<div class="vizveil" style="background:{shade_a(v["veil"])}"></div>'
                if v.get("veil") else "")
        # `.vizcam.mock` resta un 16% de alto para dejar la zona segura de la
        # PLATAFORMA (el 20% inferior del LIENZO ENTERO) libre de mockup. Con
        # el host ya confinado a una banda ese cálculo no aplica — la banda de
        # arriba no toca la zona segura — así que un visual con `band` centra
        # a secas, sin restar nada.
        camcls = ("vizcam" if band else
                  "vizcam mock" if v["kind"] == "mockup" else "vizcam")
        # Cuando el creador acompaña al gráfico en PiP, su ventana se come la
        # esquina superior derecha del lienzo: `mock_pad_top` empuja el mockup
        # hacia abajo lo justo para que no se pisen.
        # `mock_pad_top` solo empuja hacia ABAJO, y con el creador en PiP eso deja
        # un vacío de medio lienzo entre su ventana y un mockup corto: el frame se
        # lee a medio montar. `mock_pad_bottom` es el contrapeso — sube el gráfico
        # hasta debajo del PiP sin tener que inventarle alto al componente.
        if v.get("mock_pad_top") or v.get("mock_pad_bottom"):
            pads = []
            if v.get("mock_pad_top"):
                pads.append(f'padding-top:{v["mock_pad_top"]}px')
            if v.get("mock_pad_bottom"):
                pads.append(f'padding-bottom:{v["mock_pad_bottom"]}px')
            css.append(f'\n.viz[data-viz-id="{vid}"] .vizcam.mock'
                       f'{{{";".join(pads)}}}')
        if band:
            # Mejora 6 (a petición del usuario): un mockup sin `rect` (card de
            # logo, CTA) se centraba VERTICALMENTE en el host entero de la
            # banda, y con un componente corto eso dejaba tanto aire arriba
            # como abajo — la banda `top` mide 660px y una card de ~300px de
            # alto quedaba flotando en medio, con el mismo hueco muerto por
            # debajo que las grabaciones (Mejora 1 ya arregladas con `rect`).
            # Se alinea al FINAL del host en vez de al centro, con el mismo
            # margen que ya usan las grabaciones al suelo de la banda (rect
            # `ry` 100 + alto 540 = 640, 20px hasta y660) para que las cinco
            # cards de logo, las cinco grabaciones y la card del CTA compartan
            # el mismo borde inferior y el frame se lea como una sola fila, no
            # como piezas sueltas a alturas distintas.
            # `mock_pad_top`/`mock_pad_bottom` NO sirven aquí sin tocar su
            # selector: apuntan a `.vizcam.mock`, y `camcls` (arriba) NUNCA le
            # da la clase `mock` a un visual con `band` — ese padding nació
            # para el 16% de zona segura de la plataforma en un mockup a
            # lienzo completo, un caso distinto. Cambiar `align-items` es más
            # directo y no puede afectar a ningún visual viejo: `band` es
            # exclusivo del triband (pieza 15 en adelante).
            # El margen depende del LAYOUT, no del componente: en `formatos` el
            # subtitulo se come la mitad de arriba de la costura y el visual
            # tiene que dejarle sitio. Ponerlo aqui y no en cada mockup es lo
            # que evita que los diez componentes de una pieza lleven cada uno su
            # `lift` y que el once lo olvide.
            margen = (BAND_FORMATOS_MARGIN
                      if LAYOUT.get("mode") == "formatos" and band == "top"
                      else BAND_MOCK_MARGIN)
            css.append(f'\n.viz[data-viz-id="{vid}"] .vizcam'
                       f'{{align-items:flex-end;padding-bottom:{margen}px}}')
        inner = (f'<div class="vizbg"></div>'
                 f'<div class="{camcls}" id="{vid}-cam">{body_html_}</div>'
                 f'{veil}{hud_html}')
        vcls = "viz clip" if v["role"] == "backdrop" else "viz over clip"
        (hosts_back if v["role"] == "backdrop" else hosts_over).append(
            f'<div class="{vcls}" data-viz-id="{vid}" id="host-{vid}" '
            f'data-start="{s:.4f}" data-duration="{d:.4f}" '
            f'data-track-index="{track}" data-layout-allow-overlap '
            f'style="left:{host_rect["left"]}px;top:{host_rect["top"]}px;'
            f'width:{host_rect["width"]}px;height:{host_rect["height"]}px;'
            f'visibility:hidden;opacity:0;">{inner}</div>')

        for a in list(body_anims) + list(hud_anims):
            kind, sel = a[0], f'.viz[data-viz-id="{vid}"] {a[1]}'
            anims.append((kind, sel, s + a[2], a[3]) + tuple(a[4:]))

        cam = v.get("cam")
        if cam:
            sel = f'.viz[data-viz-id="{vid}"] #{vid}-cam'
            if "to_scale" in cam:
                anims.append(("cam-kb", sel, s + cam["at"], round(d - cam["at"], 4),
                              cam["scale"], cam["to_scale"]))
            else:
                anims.append(("cam-push", sel, s + cam["at"], 0.9,
                              cam["scale"], cam.get("y", 0)))

    return "\n".join(css), media, hosts_back, hosts_over, anims, skins, assets


# ── capa de SONIDO ────────────────────────────────────────────────────────────
def _measure(path, cache={}):
    """Media y pico reales. `volumedetect` LOGUEA A NIVEL INFO: con `-v error`
    no imprime nada y la medición sale vacía en silencio."""
    key = str(path)
    if key not in cache:
        out = subprocess.run(
            ["ffmpeg", "-v", "info", "-i", str(path), "-af", "volumedetect",
             "-f", "null", "-"], capture_output=True, text=True).stderr
        g = lambda k: next((float(l.split()[-2]) for l in out.splitlines() if k in l), -20.0)
        cache[key] = (g("mean_volume"), g("max_volume"))
    return cache[key]


# Por debajo de esto, el silencio de cabecera de un efecto no se oye como
# retraso: son menos de dos frames a 30 fps y no se compensa, para no mover
# tiempos por ruido de medición.
SFX_LEAD_MIN = 0.030

# Efectos VETADOS por Ezequiel (2026-10-10, pieza 9): el `glitch-2` como «motor trabado»
# le sonó feo y pidió no volver a usarlo en ninguna pieza. Se veta la familia entera: los
# tres son el mismo ruido digital destemplado. Un plan que los pida no compila.
SFX_VETADOS = {"glitch-1", "glitch-2", "glitch-3"}


def _lead_in(path, cache={}):
    """Cuánto SILENCIO trae un efecto antes de sonar de verdad.

    ⚠ Medido en la pieza 18, y estaba mal en TODAS las anteriores: `data-start`
    se escribía con el tiempo del beat y el navegador empieza a REPRODUCIR ahí,
    pero 16 de los 19 archivos de la librería tienen silencio de cabecera —
    `error` 604 ms, `typing` 437, `chime` 416, `ping` 323, `riser` 1727. Un
    efecto declarado en «no sabías hacerla» sonaba sobre la palabra siguiente.

    Es el mismo error de forma que el volumen escrito a mano que documenta §12
    —dar por hecho que los archivos vienen iguales— y se arregla igual: se
    MIDE. El nivel ya se medía; el ataque no, y nadie lo vio porque el efecto
    sí suena y el desfase solo se nota si se busca.

    Se detectó con un filtro adaptado sobre el MP4: la plantilla de 350 ms de
    `error` correlaba CERO contra la mezcla porque esos 350 ms del archivo son
    silencio. El fallo del test era el hallazgo.
    """
    key = str(path)
    if key not in cache:
        raw = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "48000",
             "-f", "s16le", "-"], capture_output=True).stdout
        a = np.frombuffer(raw, np.int16).astype(np.float32)
        if a.size == 0:
            cache[key] = 0.0
        else:
            env = np.abs(a)
            on = np.flatnonzero(env > env.max() * 0.05)
            cache[key] = float(on[0]) / 48000.0 if on.size else 0.0
    return cache[key]


def build_sfx(dur):
    """Los efectos, con el volumen y el ATAQUE calculados por medición.

    Los archivos no vienen igualados —hay 27 dB entre el más caliente y el más
    flojo—, así que un número escrito a mano tapa la voz con unos y hace
    inaudibles otros. Se lleva la media de cada uno al objetivo y se recorta si
    el transitorio se pasa del techo; manda el más restrictivo.

    Y tampoco vienen alineados: el `data-start` se adelanta el silencio de
    cabecera de cada archivo (`_lead_in`) para que lo que caiga en el beat sea
    el SONIDO y no el principio del fichero. Lo que el plan declara es cuándo
    se OYE el efecto, que es lo único que el espectador puede notar.
    """
    src_dir = SKILL / "assets" / "sfx"
    out_dir = PUB / "sfx"
    out_dir.mkdir(parents=True, exist_ok=True)

    def gain(path, trim):
        mean, peak = _measure(path)
        v = min(10 ** ((SFX_TARGET_MEAN - mean) / 20),
                10 ** ((SFX_PEAK_CAP - peak) / 20), 1.0)
        return round(max(0.02, v * trim), 3)

    els, lanes = [], []
    compensados, tarde = 0, []
    vetados = sorted({name for _, name, _, _ in SFX if name in SFX_VETADOS})
    if vetados:
        sys.exit(f"{PIECE}: efectos vetados en el plan: {', '.join(vetados)} "
                 "(Ezequiel no quiere el ruido digital `glitch` en ninguna pieza; "
                 "§12 del CLAUDE.md)")
    for start, name, trim, why in sorted(SFX):
        src = src_dir / f"{name}.mp3"
        if not src.exists():
            print(f"  ⚠ efecto ausente, se omite: {name}")   # nunca bloquea el render
            continue
        dst = out_dir / src.name
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            dst.write_bytes(src.read_bytes())

        d = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip())
        # El beat es cuándo se OYE. Si el archivo trae silencio delante, se
        # empieza a reproducir antes para que el ataque caiga en su sitio.
        lead = _lead_in(src)
        s = q(max(0.0, start - lead)) if lead >= SFX_LEAD_MIN else q(start)
        if lead >= SFX_LEAD_MIN:
            real = s + lead
            if real - start > 0.034:   # no cupo: el efecto vive antes del 0
                tarde.append((name, start, round(real - start, 3)))
            compensados += 1
        e = q(min(s + d, dur))
        if e <= s:
            continue

        lane = next((i for i, end in enumerate(lanes) if end <= s), len(lanes))
        if lane == len(lanes):
            lanes.append(e)
        else:
            lanes[lane] = e

        # El `id` no es decorativo: el renderer descubre media POR id, y un
        # <audio> sin él se renderiza en silencio sin avisar en el navegador.
        els.append(f'  <!-- {why} -->\n'
                   f'  <audio id="sfx-{len(els):02d}-{name}" class="clip" '
                   f'src="sfx/{src.name}" data-start="{s:.4f}" '
                   f'data-duration="{e - s:.4f}" data-track-index="{TRK_SFX + lane}" '
                   f'data-volume="{gain(src, trim)}"></audio>')
    if compensados:
        print(f"  efectos: {compensados} con silencio de cabecera compensado "
              f"(el ataque cae en el beat, no el principio del fichero)")
    for name, beat, off in tarde:
        # No bloquea: es un aviso con número, no un misterio. Pasa cuando el
        # efecto se declara tan al principio que su cabecera no cabe antes
        # del 0 — la única salida es mover el beat o recortar el archivo.
        print(f"  ⚠ «{name}» en {beat:.3f}s no cabe entero: suena {off*1000:.0f} ms "
              f"tarde porque su cabecera no entra antes del segundo 0")
    return els, len(lanes)


def build_music(dur):
    """Cama musical: se recorta a la duración exacta con entrada y salida ya
    horneadas, porque el HTML no sabe hacer un fundido de audio.

    El nivel también se calcula: la música no compite, sostiene. Queda ~14 dB
    bajo la voz, que es donde se siente sin que se escuche.
    """
    if not MUSIC:
        return []
    src = ROOT / MUSIC["src"]
    if not src.exists():
        print(f"  ⚠ música ausente, se omite: {src}")
        return []
    out_dir = PUB / "music"
    out_dir.mkdir(parents=True, exist_ok=True)
    bed = out_dir / "bed.mp3"

    fade_in = MUSIC.get("fade_in", 1.2)
    fade_out = MUSIC.get("fade_out", 2.2)
    offset = MUSIC.get("offset", 0.0)
    if not bed.exists() or bed.stat().st_mtime < src.stat().st_mtime:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-ss", str(offset),
             "-i", str(src), "-t", f"{dur:.3f}",
             "-af", f"afade=t=in:st=0:d={fade_in},"
                    f"afade=t=out:st={max(0, dur - fade_out):.3f}:d={fade_out}",
             "-c:a", "libmp3lame", "-b:a", "160k", str(bed)],
            check=True)

    mean, peak = _measure(bed)
    vol = round(max(0.01, min(10 ** ((MUSIC_TARGET_MEAN - mean) / 20), 1.0)), 4)
    target = MUSIC_TARGET_MEAN
    print(f"  música: media {mean:.1f} dB → objetivo {target} dB · volume {vol}")
    return [f'  <audio id="music-bed" class="clip" src="music/bed.mp3" '
            f'data-start="0" data-duration="{dur:.4f}" '
            f'data-track-index="{TRK_MUSIC}" data-volume="{vol}"></audio>']


# ── capa de TARJETAS ──────────────────────────────────────────────────────────
def card_body(kind, cid, cfg):
    """Cuerpos de tarjeta. Son gráficos PEQUEÑOS que acompañan al rótulo; lo
    grande vive en la capa de visuales."""
    p = f'.card[data-card-id="{cid}"]'
    if kind == "chips":
        items = cfg.get("items", [])
        cells = "".join(
            f'<div class="cchip" id="{cid}-c{i}">{esc(x)}</div>'
            for i, x in enumerate(items))
        css = f"""
{p} .crow{{display:flex;flex-wrap:wrap;gap:14px;justify-content:center}}
{p} .cchip{{font-family:{MONO};font-weight:700;font-size:{T['chip']}px;
  letter-spacing:.10em;color:{C['text2']};background:{TK.rgba(C["surface"], .9)};
  border:1px solid {TK.LINE};border-radius:{RADIUS['pill']}px;padding:14px 24px;opacity:0}}"""
        at = cfg.get("beats_rel") or [0.30 + i * 0.12 for i in range(len(items))]
        return css, f'<div class="crow">{cells}</div>', [
            ("chip-in", f"#{cid}-c{i}", at[i] if i < len(at) else 0.3 + i * .12, 0.30)
            for i in range(len(items))]

    if kind == "stat":
        items = cfg.get("items", [])
        cells = "".join(
            f'<div class="mcell{" hot" if i == cfg.get("accent", -1) else ""}" id="{cid}-m{i}">'
            f'<div class="mval">{esc(v)}</div><div class="mlab">{esc(l)}</div></div>'
            for i, (v, l) in enumerate(items))
        css = f"""
{p} .mrow{{display:flex;gap:16px;width:100%}}
{p} .mcell{{flex:1;background:{TK.rgba(C["surface"], .94)};border:1px solid {TK.LINE};
  border-radius:{RADIUS['lg']}px;padding:28px 14px 24px;text-align:center;
  box-shadow:{TK.SHADOW};opacity:0}}
{p} .mcell.hot{{border-color:{accent_a(.5)};
  background:linear-gradient(180deg,{FILL['accent']} 0%,{TK.rgba(C["surface"], .94)} 72%)}}
{p} .mval{{font-family:{FONT};font-weight:900;font-size:{round(T['card_title']*1.35)}px;
  line-height:.98;letter-spacing:-.04em;color:{C['text']}}}
{p} .mcell.hot .mval{{color:{C['accent_hi']}}}
{p} .mlab{{font-family:{MONO};font-weight:700;font-size:{T['label']-4}px;
  letter-spacing:.14em;color:{C['text3']};margin-top:14px}}"""
        at = cfg.get("beats_rel") or [0.30 + i * 0.16 for i in range(len(items))]
        return css, f'<div class="mrow">{cells}</div>', [
            ("stamp", f"#{cid}-m{i}", at[i] if i < len(at) else 0.3 + i * .16, 0.38)
            for i in range(len(items))]

    if kind == "msgteaser":
        # Las cuatro piezas del lead magnet, en miniatura y entrando rápido.
        #
        # NO va borroso, al contrario que `teaser`. La diferencia es qué se
        # está protegiendo: en la pieza 12 el entregable era UN documento y
        # enseñarlo legible era entregarlo, así que el blur era el mensaje.
        # Aquí el entregable es una SECUENCIA, y lo que hay que enseñar es
        # cuántos mensajes trae y en qué orden — no su redacción. Los rótulos
        # son el TIPO de cada mensaje, nunca su texto: se ve la forma del
        # paquete y sigue habiendo razón para pedirlo.
        items = cfg.get("items", [])
        filas = "".join(
            f'<span class="mtrow" id="{cid}-mt{i}">'
            f'<span class="mtdot"></span><span class="mttxt">{esc(x)}</span>'
            f'<span class="mtnum">{i + 1}</span></span>'
            for i, x in enumerate(items))
        css = f"""
{p} .mtwrap{{display:flex;flex-direction:column;gap:12px;
  width:{round(W*0.72)}px}}
{p} .mtrow{{display:flex;align-items:center;gap:16px;height:74px;
  box-sizing:border-box;padding:0 22px;background:{C['surface']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['md']}px;
  box-shadow:{TK.SHADOW};opacity:0}}
{p} .mtdot{{width:14px;height:14px;border-radius:50%;background:{C['accent']};
  flex:0 0 auto}}
{p} .mttxt{{font-family:{FONT};font-weight:600;font-size:{T['body']-2}px;
  color:{C['text']};white-space:nowrap}}
{p} .mtnum{{margin-left:auto;font-family:{MONO};font-weight:700;
  font-size:{T['chip']-4}px;letter-spacing:.10em;color:{C['bg']};
  background:{C['go']};border-radius:{RADIUS['pill']}px;padding:6px 14px}}"""
        # 110 ms entre filas: «entrando rápidamente», no una lista que se lee.
        at = cfg.get("beats_rel") or [0.14 + i * 0.11 for i in range(len(items))]
        return css, f'<div class="mtwrap">{filas}</div>', [
            ("chip-in", f"#{cid}-mt{i}", at[i] if i < len(at) else 0.14 + i * .11,
             0.26) for i in range(len(items))]

    if kind == "teaser":
        # El adelanto del lead magnet: se ve QUE existe, no QUÉ dice. El
        # blur es ESTÁTICO — la prohibición del contrato es *animar* `filter`,
        # no usarlo; un blur fijo es solo rendering, igual que el de
        # `BLUR_WIPE`. Y es lo que hace que enseñarlo no sea entregarlo.
        # DOS NÚMEROS MEDIDOS, los dos a la baja respecto al primer intento.
        #
        # `blur(7px)` sobre filas de 14 px dejaba un BORRÓN de 605x239: se veía
        # una mancha oscura sobre la pared clara, no un documento — y el teaser
        # solo funciona si se reconoce QUÉ tipo de cosa es. A 5 px con filas de
        # 20 px se lee «documento» y sigue siendo ilegible palabra por palabra,
        # que es justo lo que se busca.
        #
        # Y NO LLEVA PASTILLA VERDE. Con kicker + titular + documento + pastilla
        # el rótulo del CTA sumaba cuatro elementos apilados, y el CTA es donde
        # el brief pide no saturar. Lo que la pastilla decía («te la envío al
        # comentar») ya lo está diciendo su voz en ese mismo instante.
        rows = "".join(
            f'<span class="tsrow" style="width:{w}%"></span>'
            for w in (86, 64, 78, 52, 71, 44, 68))
        css = f"""
{p} .tsdoc{{position:relative;width:{round(W*0.60)}px;background:{C['surface']};
  border:1px solid {TK.LINE_HI};border-radius:{RADIUS['lg']}px;padding:30px 32px;
  display:flex;flex-direction:column;gap:18px;box-shadow:{TK.SHADOW};
  filter:blur(5px);opacity:.85}}
{p} .tsbar{{height:30px;width:52%;border-radius:8px;background:{C['accent']};
  margin-bottom:8px}}
{p} .tsrow{{height:20px;border-radius:10px;background:{TK.LINE_HI};display:block}}
{p} .tswrap{{position:relative;display:flex;flex-direction:column;
  align-items:center;opacity:0}}"""
        html = (f'<div class="tswrap" id="{cid}-ts">'
                f'<div class="tsdoc"><span class="tsbar"></span>{rows}</div>'
                f'</div>')
        return css, html, [("rise-in", f"#{cid}-ts", 0.16, 0.40)]

    if kind == "cta":
        label = esc(cfg.get("cta_text", "COMENTA"))
        css = f"""
{p} .ctabtn{{background:{C['go']};border-radius:{RADIUS['pill']}px;
  padding:26px 54px;font-family:{FONT};font-weight:900;
  font-size:{round(T['card_title']*1.12)}px;letter-spacing:-.02em;
  color:{C['bg']};box-shadow:0 18px 50px {TK.rgba(C["go"], .28)};opacity:0}}"""
        return css, f'<div class="ctabtn" id="{cid}-cta">{label}</div>', [
            ("stamp", f"#{cid}-cta", cfg.get("cta_at", 0.34), 0.44)]

    return "", "", []


def build_cards(dur):
    """Rótulos flotantes. Entran por opacidad y su contenido es lo que se mueve."""
    hosts, anims, story = [], [], []
    css_all = []
    for i, sc in enumerate(CARDS, 1):
        cid = f"card-{i:02d}"
        s, e = q(sc["start"]), q(min(sc["end"], dur))
        if e <= s:
            continue
        place = sc.get("place", "top")
        p = f'.card[data-card-id="{cid}"]'

        beats_rel = [max(0.04, round(b - s, 4)) for b in sc.get("beats", [])]
        cfg = dict(sc)
        if beats_rel:
            cfg["beats_rel"] = beats_rel
        if "cta_at" in sc:
            cfg["cta_at"] = max(0.04, round(sc["cta_at"] - s, 4))
        bcss, bhtml, banims = card_body(sc.get("body", "none"), cid, cfg)

        # Sobre el metraje el rótulo necesita su propio suelo: la tinta clara
        # sobre una pared iluminada se pierde. El kicker lo resuelve con su
        # pastilla, y el titular con el MISMO filete del suelo que el
        # subtítulo (`paint-order: stroke fill`, el trazo detrás del relleno,
        # que no engorda la letra). Una sombra sola no basta: se difumina y
        # deja el acento de la keyword por debajo de 3:1 en cuanto el fondo
        # es una pared iluminada — medido, no supuesto.
        pad_top = {"top": round(H * 0.075), "center": 0,
                   "bottom": 0}[place]
        justify = {"top": "flex-start", "center": "center", "bottom": "flex-end"}[place]
        pad_bottom = round(H * 0.30) if place == "bottom" else round(H * 0.055)

        kicker = sc.get("kicker", "")
        title = sc.get("title", "")
        sub = sc.get("sub", "")
        key = sc.get("key")          # palabra del titular que lleva el voltaje

        def tline(l):
            if key and key in l:
                a, _, b = l.partition(key)
                return (f'<span class="tline">{esc(a)}'
                        f'<span class="tkey">{esc(key)}</span>{esc(b)}</span>')
            return f'<span class="tline">{esc(l)}</span>'

        title_html = "".join(tline(l) for l in title.split("\n")) if title else ""
        css_all.append(f"""
{p} .root{{width:100%;height:100%;display:flex;flex-direction:column;
  justify-content:{justify};align-items:center;gap:22px;
  padding:{pad_top}px {round(W*0.06)}px {pad_bottom}px;background:transparent}}
{p} .kick{{display:flex;align-items:center;gap:12px;font-family:{MONO};font-weight:700;
  font-size:{T['chip']}px;letter-spacing:{TRACK['chip']};color:{C['text2']};
  background:{shade_a(.72)};border:1px solid {TK.LINE};
  border-radius:{RADIUS['pill']}px;padding:12px 22px;white-space:nowrap;opacity:0}}
{p} .kick s{{width:10px;height:10px;border-radius:50%;background:{C['accent']};
  display:block;text-decoration:none}}
{p} .ttl{{display:flex;flex-direction:column;align-items:center;gap:2px;
  font-family:{FONT};font-weight:900;font-size:{T['headline']}px;line-height:1.02;
  letter-spacing:{TRACK['headline']};color:{C['text']};text-align:center;
  -webkit-text-stroke:7px {C['bg']};paint-order:stroke fill;
  text-shadow:0 3px 18px {shade_a(.85)},0 1px 3px {shade_a(.9)}}}
{p} .tline{{display:block}}
/* La keyword del titular lleva SU PROPIO suelo opaco, no solo el filete.
   El filete salva la tinta, pero el acento sobre una pared iluminada se
   queda muy por debajo de 3:1 — medido. Con la pastilla del suelo el par es
   siempre accent_hi sobre bg (≥ 4.5:1, lo fija tests/test_paletas.py), pase
   lo que pase detrás en el metraje, y además rima con la pastilla del kicker. */
{p} .tkey{{color:{C['accent_hi']};background:{C['bg']};-webkit-text-stroke:0;
  border-radius:{RADIUS['sm']}px;padding:0 .10em;
  -webkit-box-decoration-break:clone;box-decoration-break:clone}}
{p} .sub{{font-family:{FONT};font-weight:500;font-size:{T['body']}px;line-height:1.32;
  color:{C['text2']};text-align:center;max-width:{round(W*0.76)}px;
  text-shadow:0 2px 12px {shade_a(.9)};opacity:0}}
{bcss}""")

        html = (f'<div class="card" data-card-id="{cid}">\n'
                f'<div class="root">\n'
                + (f'  <div class="kick" id="{cid}-kick"><s></s>{esc(kicker)}</div>\n'
                   if kicker else "")
                + (f'  <div class="ttl" id="{cid}-ttl">{title_html}</div>\n'
                   if title else "")
                + (f'  <div class="sub" id="{cid}-sub">{esc(sub)}</div>\n' if sub else "")
                + f'  {bhtml}\n</div>\n</div>')
        (PUB / "cards" / f"{cid}.html").write_text(html, encoding="utf-8")

        hosts.append(
            f'<div class="card-host clip" id="host-{cid}" data-card-id="{cid}" '
            f'data-start="{s:.4f}" data-duration="{e-s:.4f}" '
            f'data-track-index="{TRK_CARD}" data-layout-allow-overlap '
            f'style="left:0px;top:0px;width:{W}px;height:{H}px;'
            f'visibility:hidden;opacity:0;">\n{html}\n</div>')

        if kicker:
            anims.append(("slide-in", f'{p} #{cid}-kick', s + 0.06, 0.30))
        if title:
            anims.append(("punch", f'{p} #{cid}-ttl', s + 0.14, 0.44))
        if sub:
            anims.append(("slide-in", f'{p} #{cid}-sub', s + 0.34, 0.34))
        for a in banims:
            anims.append((a[0], f'{p} {a[1]}', s + a[2], a[3]) + tuple(a[4:]))

        story.append(dict(id=cid, intent=f'{kicker} — {title}'.strip(" —"),
                          startSec=s, endSec=e, accentIndex=i % 5,
                          zone="video-overlay",
                          contentHints=dict(kicker=kicker, title=title,
                                            body=sc.get("body", "none"), place=place)))
    return "\n".join(css_all), hosts, anims, story


# ── capa de SUBTÍTULOS — bloques cortos con una keyword ───────────────────────
KEY_AUTO = re.compile(r"^\d+([.,]\d+)?%?$|^\d+$")


def is_key(word_up, extra):
    w = word_up.strip("¿?¡!.,:;")
    if KEY_AUTO.match(w):
        return True
    return any(w == k.upper() for k in extra)


def split_at_shot_kind(chunks, shots):
    """Parte un bloque donde cambia el TIPO de encuadre (cara · partida · grafico).

    La altura de un bloque se resuelve una sola vez, con el encuadre de su punto medio,
    así que un bloque que cruza de `band` a `off` (o de `full` a `band`) se queda con la
    altura de uno de los dos durante todo el bloque. En la pieza 5 «EL MEDIO ENTRE TÚ»
    cruzaba de `partida` a `grafico` y en el tramo de `partida` se sentaba ENCIMA de la
    cara, a la altura del gráfico. Cada palabra va con el encuadre de su `start`.
    """
    if not shots:
        return chunks

    def kind(t):
        sh = shot_at(shots, t)
        return sh.get("kind") if sh else None

    out = []
    for ch in chunks:
        cur = [ch[0]]
        for item in ch[1:]:
            if kind(item[0]["start"]) != kind(cur[-1][0]["start"]):
                out.append(cur)
                cur = []
            cur.append(item)
        out.append(cur)
    return out


def build_captions(words, dur, shots, viz_skins):
    """Bloques de 2–6 palabras. Karaoke en TODA la pieza (Mejora 4).

    El bloque entra entero y se queda quieto; lo que se mueve es un fondo
    de acento con esquinas redondeadas que va DETRÁS de la palabra que suena en
    cada instante y viaja con ella: nunca hay más de una encendida, y el
    tamaño y el color del texto no cambian en ninguna palabra —resaltarlas
    IGUAL Y A LA VEZ convertiría el subtítulo en un metrónomo y el ojo dejaría
    de leer; lo que evita eso aquí no es dejar una sola quieta y grande (la
    keyword agrandada y de acento del esquema anterior a esta Mejora), sino que el
    resaltado se MUEVA con la voz.

    Nació limitado a `band` (Mejora 3, a petición del usuario): ahí el
    subtítulo vive sobre suelo liso (§ triband en CLAUDE.md), no sobre
    metraje, así que la keyword agrandada y de acento de fuera de `band` no
    tenía nada que esquivar y el karaoke era la única función que le quedaba
    al resaltado. Esta Mejora quita esa frontera a petición del usuario: el
    karaoke pasa a ser el tratamiento único, también en `full`/`pip` (el hook
    y la tesis). Lo que NO cambia ahí es la PIEL: el subtítulo sigue ENCIMA
    del metraje, así que sigue siendo `on-dark` con su filete del suelo de
    7px — el filete existe para que la letra sobreviva sobre imagen, y eso no
    lo decide el resaltado.
    """
    fnt = measure_font(CAPTION_SIZE)

    def width(items):
        return fnt.getlength(" ".join(u for _, u in items)) + 22 * len(items)

    # Presupuesto de ancho: DOS líneas. El bloque envuelve solo con el flujo del
    # texto, así que medir contra una sola línea troceaba de tres en tres
    # palabras y el subtítulo salía tartamudo.
    budget = CAPTION_MAXW * 1.9
    MAX_WORDS, MAX_SECS = 6, 2.1

    # El troceo va por JERARQUÍA, no por un solo criterio: frase → cláusula →
    # reparto parejo. Cortar solo por ancho pega el final de una idea con el
    # principio de la siguiente («…empleados. Cuando…») y el espectador lee una
    # frase que nadie dijo.
    def split_units(ws, enders):
        units, cur = [], []
        for w, up in ws:
            cur.append((w, up))
            if w["text"].rstrip().endswith(enders):
                units.append(cur)
                cur = []
        if cur:
            units.append(cur)
        return units

    def even_split(unit):
        """Reparte una cláusula en partes PAREJAS. El reparto glotón deja
        huérfanas —una palabra sola en pantalla 0.3 s parpadea y no se lee."""
        n = len(unit)
        span = unit[-1][0]["end"] - unit[0][0]["start"]
        parts = max(1, math.ceil(n / 5), math.ceil(span / MAX_SECS),
                    math.ceil(width(unit) / budget))
        if parts == 1:
            return [unit]
        size = math.ceil(n / parts)
        # con trozos de 1 palabra el reparto no compensa: se prefieren menos partes
        while parts > 1 and n - size * (parts - 1) < 1:
            parts -= 1
            size = math.ceil(n / parts)
        return [unit[i:i + size] for i in range(0, n, size)]

    flat = [(w, w["text"].strip().rstrip(",.:;!?").upper()) for w in words
            if w["text"].strip().rstrip(",.:;!?")]

    # `key_ranges[i]` es el rango LOCAL (lo, hi) inclusive de la keyword del
    # bloque `i`, o None. Con captions explícitas viene del EDL; con el troceo
    # automático se deduce con `is_key` más abajo.
    key_ranges: list[tuple[int, int] | None] = []

    if CAPTIONS:
        # EL EDL MANDA. Los bloques llegan como rangos de palabras sobre el
        # transcript SIN filtrar, que es el mismo índice que usa `edl_words`,
        # así que se indexa `words` directamente y no `flat`.
        chunks = []
        for c in CAPTIONS:
            lo, hi = c["words"]
            ch = [(words[i], words[i]["text"].strip().rstrip(",.:;!?").upper())
                  for i in range(lo, hi + 1)
                  if words[i]["text"].strip().rstrip(",.:;!?")]
            if not ch:
                continue
            chunks.append(ch)
            kw = c.get("keyword")
            key_ranges.append((kw[0] - lo, kw[1] - lo) if kw else None)
    else:
        chunks = []
        for sent in split_units(flat, (".", "?", "!")):
            for clause in split_units(sent, (",", ";", ":")):
                chunks.extend(even_split(clause))

        # Una cláusula de una sola palabra («…y,») se pega a su vecina DENTRO
        # de la misma frase; nunca a través de un punto.
        merged = []
        for ch in chunks:
            prev = merged[-1] if merged else None
            crosses_sentence = bool(
                prev and prev[-1][0]["text"].rstrip().endswith((".", "?", "!")))
            if (prev and len(ch) == 1 and not crosses_sentence
                    and len(prev) + 1 <= MAX_WORDS
                    and width(prev + ch) <= budget
                    and ch[-1][0]["end"] - prev[0][0]["start"] <= MAX_SECS + 0.4):
                merged[-1] = prev + ch
            else:
                merged.append(ch)
        chunks = split_at_shot_kind(merged, shots)
        # una sola keyword por bloque: la primera que califique
        for ch in chunks:
            i = next((i for i, (_, up) in enumerate(ch)
                      if is_key(up, KEYWORDS)), -1)
            key_ranges.append((i, i) if i >= 0 else None)

    # La palabra del CTA va DEBAJO de los bloques que suenan en su ventana, así que esos
    # bloques se miden con el suelo subido lo que ella ocupa: la palabra nunca cae en el
    # 20 % que pinta la plataforma.
    cta = None
    if CTA_PALABRA:
        hasta = CTA_PALABRA.get("hasta")
        cta = (q(float(CTA_PALABRA["desde"])),
               q(dur if hasta is None else min(float(hasta), dur)))
    kw_alto = round(round(CAPTION_SIZE * CTA_KW_RATIO) * caption_metrics.LINE_RATIO)
    reserva = CTA_KW_GAP + kw_alto
    bottoms = []
    spans, anims, key_anims, rows = [], [], [], []
    for ci, ch in enumerate(chunks):
        s = q(max(0.0, ch[0][0]["start"] - 0.06))
        e = ch[-1][0]["end"] + 0.22
        if ci + 1 < len(chunks):
            e = min(e, chunks[ci + 1][0][0]["start"] - 0.03)
        e = q(max(min(e, dur), s + 0.28))

        krange = key_ranges[ci] if ci < len(key_ranges) else None
        klo, khi = krange if krange else (-1, -2)
        key_idx = klo if krange else -1

        # La altura depende de LO QUE HAY DETRÁS en ese frame, así que el
        # encuadre se resuelve ANTES de montar las palabras. Se consulta por
        # el PUNTO MEDIO del bloque, no por su inicio: un bloque que arranca
        # 20 ms antes de que entre el plano siguiente pertenece al plano
        # siguiente, y midiendo por el inicio heredaba la altura del anterior
        # — o la de un tramo `off`, que no tiene cara que esquivar.
        sh = shot_at(shots, (s + e) / 2)

        # Karaoke (Mejora 4, a petición del usuario): tratamiento ÚNICO del
        # subtítulo, sin excepción de encuadre — nació limitado a `band` en la
        # Mejora 3 y aquí pierde esa frontera. TODAS las palabras van al mismo
        # tamaño y color; lo único que se mueve es un fondo de acento con
        # esquinas redondeadas detrás de la palabra que suena en el instante
        # exacto en que se pronuncia (`w["start"]`, del transcript remapeado)
        # y se apaga en cuanto arranca la siguiente: el resaltado viaja, no se
        # acumula, y al terminar el bloque no queda nada pintado.
        # `disp` (lo que MIDE el gate de zona segura) sigue viendo la keyword
        # en mayúscula aunque ya no se RENDERICE agrandada — es más
        # conservador de lo que hace falta, nunca menos, así que nunca deja
        # pasar un bloque que de verdad desborde (mismo razonamiento que ya
        # valía para `band` en la Mejora 3, ahora vale en todas partes).
        parts, disp = [], []
        for i, (w, up) in enumerate(ch):
            en_key = klo <= i <= khi
            frase = w["text"].strip().rstrip(",.:;!?")
            txt = up if en_key else frase
            disp.append(txt)
            wid = f"c{ci}w{i}"
            parts.append(f'<span class="w kw" id="{wid}">'
                         f'<span class="wbg" id="{wid}-bg"></span>{esc(frase)}</span>')
            start_at = q(max(w["start"], s))
            end_at = (q(ch[i + 1][0]["start"]) if i + 1 < len(ch)
                      else q(min(w["end"], e)))
            end_at = max(end_at, q(start_at + 1.0 / FPS))
            # El fade IN/OUT se ESCALA a la ventana de la propia palabra: a
            # 0.05/0.08 fijos, una palabra corta —muy pegada a la siguiente,
            # habla rápida— deja la entrada de una encimada con la salida de
            # la anterior (`overlapping_gsap_tweens` en `hyperframes check`).
            # 0.35 de la ventana para cada lado deja siempre un 30% en medio a
            # opacidad plena, por corta que sea la palabra, y nunca se pisan.
            win = end_at - start_at
            d_in = round(min(0.05, win * 0.35), 4)
            d_out = round(min(0.08, win * 0.35), 4)
            key_anims.append((wid, start_at, end_at, d_in, d_out))

        skin = "on-dark"
        # La PIEL la decide quién ocupa la mayor parte del bloque. La ALTURA no:
        # ahí manda el más bajo de todos los que el bloque toca, aunque solo
        # los toque un instante. Un bloque que se come 0.2 s del final de un
        # takeover heredaba la altura de la cara —más arriba— y esos 0.2 s el
        # subtítulo se sentaba ENCIMA del gráfico. Bajarlo no le quita nada al
        # frame; subirlo tapa el único sitio donde estaba la información.
        tops = []
        for vs, ve, vskin, vtop in viz_skins:
            ov = min(e, ve) - max(s, vs)
            if ov > (e - s) * 0.5:
                skin = vskin
            if ov > 0.12 and vtop is not None:
                tops.append(vtop)
        if sh and sh["kind"] == "band" and LAYOUT.get("mode") == "formatos":
            # Formatos (doctrina 2026-09-29): el bloque se CENTRA sobre la línea de
            # división, mitad sobre el visual y mitad sobre el hablante. La mitad de abajo
            # cae encima del metraje, así que lleva la piel con filete (`on-dark`).
            # Nunca sobre la cara (§13): si centrado la pisaría —las tomas de Ezequiel
            # dejan la cara empezando justo en la costura, top_frac 0.18–0.21—, el bloque
            # SUBE hasta quedar BAND_CAP_MARGIN por encima de ella. Frenar la compilación
            # obligaría a bajar el `anchor` y la barbilla caería en el 20 % de la plataforma.
            skin = "on-dark"
            m = caption_metrics.measure_block(disp, CAPTION_SIZE, krange, FMT, H, W,
                                              cache_dir=WORK)
            alto = m["n_lines"] * m["line_h"]
            top = layout_formatos.costura(LAYOUT) - alto // 2
            cara = face_top_y(sh)
            if cara is not None and top + alto > cara - BAND_CAP_MARGIN:
                top = math.floor(cara) - BAND_CAP_MARGIN - alto
            n_lines = m["n_lines"]
        elif sh and sh["kind"] == "band":
            # En triband el subtítulo no persigue la barbilla: entre el techo y
            # el suelo de su banda NO hay metraje, así que no puede tapar la
            # cara. Piel sin filete —el filete existe para sobrevivir encima
            # del metraje, y aquí no lo hay.
            #
            # Ancla por ABAJO (Mejora 5, a petición del usuario). Antes el
            # tope era FIJO (`text.top` + aire) y el bloque crecía hacia
            # abajo: un bloque corto dejaba ~200px de hueco muerto entre el
            # subtítulo y el metraje del hablante, porque el ancla visual real
            # es esa separación, no el techo de la banda de texto. Ahora el
            # SUELO es el fijo —la tinta más baja se apoya en él, igual que
            # antes— y el tope sube según cuántas líneas tenga el bloque:
            # `top = suelo − líneas × alto_de_línea`.
            bandas = triband_panels()
            techo = bandas["text"]["top"]
            suelo = bandas["speaker"]["top"] - BAND_CAP_MARGIN
            skin = "on-surface"
            m = caption_metrics.measure_block(disp, CAPTION_SIZE, krange, FMT, H, W,
                                              cache_dir=WORK, floor_px=suelo)
            top = suelo - m["n_lines"] * m["line_h"]
            # El gate CAMBIA DE SENTIDO pero no desaparece: antes fallaba si
            # la tinta se pasaba del suelo (creciendo hacia abajo desde un
            # tope fijo); ahora falla si el tope sube por encima del TECHO de
            # la banda de texto, porque eso invadiría la banda de la
            # animación de arriba. Mismo rigor, otro borde.
            if top < techo:
                sys.exit(
                    f"bloque {ci} «{' '.join(u for _, u in ch)}»: {m['n_lines']} líneas "
                    f"empiezan en y{top}, por encima del techo de la banda de texto "
                    f"(y{techo}) — invade la banda de la animación. Trocea el bloque "
                    f"más corto.")
            n_lines = m["n_lines"]
        else:
            if sh and sh["kind"] == "pip":
                if not tops:
                    skin = "on-dark"
                tops.append(round(H * 0.60))
            elif sh and sh["kind"] != "off":
                tops.append(round(min(chin_at(sh) + H * 0.030, H * 0.80)))
            top = max(tops) if tops else round(H * 0.72)

            # ZONA SEGURA: en REEL el 20 % inferior lo pinta la plataforma con
            # su propia interfaz, así que ahí no puede caer TINTA — no basta
            # con que empiece antes de 1536. La cuenta necesita el número de
            # líneas Y el tamaño MÁXIMO del bloque (la keyword mide 1.22x), así
            # que vive en `caption_metrics`, testeable sin renderizar. Sin esto
            # un bloque de dos líneas colocado sobre un gráfico metía la
            # segunda línea 46 px dentro de la interfaz.
            # Se mide el texto que de verdad se pinta (`disp`: caja de frase
            # salvo la keyword), no la versión en mayúsculas: la mayúscula es
            # más ancha y habría subido el techo sin necesidad.
            en_cta = bool(cta) and min(e, cta[1]) - max(s, cta[0]) > 0
            suelo_cta = round(H * caption_metrics.SAFE_BOTTOM) - reserva if en_cta else None
            m = caption_metrics.measure_block(disp, CAPTION_SIZE, krange, FMT, H, W,
                                              cache_dir=WORK, floor_px=suelo_cta)
            n_lines, floor_top = m["n_lines"], m["floor_top"]
            top = min(top, floor_top)

        if cta and min(e, cta[1]) - max(s, cta[0]) > 0:
            bottoms.append(top + m["n_lines"] * m["line_h"])
        spans.append(f'<div class="cap {skin}" id="cap{ci}" data-layout-allow-overlap '
                     f'style="top:{top}px">{"".join(parts)}</div>')
        anims.append((f"#cap{ci}", s, e))
        rows.append((ci, s, e, top, " ".join(u for _, u in ch),
                     ch[key_idx][1] if key_idx >= 0 else ""))
    if cta:
        # El CTA cierra en `cara` (encuadre full): en `partida` la palabra caería sobre la
        # cara del hablante, debajo del subtítulo de la costura.
        en_band = [sh for sh in shots if sh["kind"] == "band"
                   and min(sh["end"], cta[1]) - max(sh["start"], cta[0]) > 1.0 / FPS]
        if en_band:
            sys.exit(
                f"la palabra del CTA «{CTA_PALABRA['texto']}» ({cta[0]:.2f}–{cta[1]:.2f}s) "
                f"cae sobre el encuadre `band` de {en_band[0]['start']:.2f}s: el CTA cierra en "
                f"`cara` (encuadre `full`), porque en `partida` la palabra quedaría encima de "
                f"la cara. Pon el CTA en `full` o mueve `cta_palabra.desde`.")
        kw_top = (max(bottoms) if bottoms else round(H * 0.62)) + CTA_KW_GAP
        spans.append(f'<div class="cta-kw" id="cta-kw" data-layout-allow-overlap '
                     f'style="top:{kw_top}px">“{esc(str(CTA_PALABRA["texto"]))}”</div>')
        anims.append(("#cta-kw", cta[0], cta[1]))
    return spans, anims, key_anims, rows


_ANIM_NONCE = itertools.count()
# Nonce para nombres de variable JS únicos (`_hv`/`_mv`/`_cv`). DE MÓDULO A
# PROPÓSITO, no local a `emit_anim`: un `js: list[str] = []` fresco en cada
# llamada reinicia `len(js)` en cada una, y dos animaciones del MISMO kind en
# el MISMO documento sacarían el MISMO nombre. No es hipotético — la pieza 12
# sube su contador en dos tramos (12→18→27, mismo id "counter", ver
# tests/golden/12.plan.json:466-479) y eso son DOS tuplas count-roll en el
# mismo plan. Con un contador local, las dos declararían `const _cv0` y el
# script ENTERO de la pieza rompería con `SyntaxError: Identifier '_cv0' has
# already been declared` — no solo esa animación. Ver el test de regresión en
# tests/test_motion_gestos.py que reproduce justo este caso: si alguien
# "simplifica" esto de vuelta a `len(js)`, ese test se pone en rojo.


def emit_anim(a) -> str:
    """El JS de UNA animación. Extraído del bucle `for a in anims:` para
    poder probar un gesto sin renderizar la composición entera."""
    kind, sel, t, d = a[0], a[1], q(a[2]), a[3]
    js: list[str] = []
    if kind == "slide-in":
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, y: 14 }}, '
                  f'{{ opacity: 1, y: 0, duration: {round(d*1.25,4)}, '
                  f'ease: "power2.out" }}, {t:.4f});')
    elif kind == "rise-in":
        # Entrada de un panel grande: sube muy poco y aterriza en plano. El
        # recorrido acompaña al fundido, nunca lo protagoniza.
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, y: 26, scale: 0.985 }}, '
                  f'{{ opacity: 1, y: 0, scale: 1, duration: {round(d*1.35,4)}, '
                  f'ease: "power3.out" }}, {t:.4f});')
    elif kind == "chip-in":
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, scale: 0.94, y: 8 }}, '
                  f'{{ opacity: 1, scale: 1, y: 0, duration: {round(d*1.25,4)}, '
                  f'ease: "power2.out" }}, {t:.4f});')
    elif kind == "glide-x":
        # De derecha a izquierda. Recorrido corto a propósito: lo que entra
        # por opacidad es la CARD, y dentro de ella el logo solo se desliza
        # lo justo para que el ojo lea una llegada, no un barrido.
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, x: 72 }}, '
                  f'{{ opacity: 1, x: 0, duration: {d}, '
                  f'ease: "power2.out" }}, {t:.4f});')
    elif kind == "drop-in":
        # De arriba abajo, distinto del `glide-x` a propósito: dos
        # recorridos distintos hacen que el ojo lea DOS elementos.
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, y: -22 }}, '
                  f'{{ opacity: 1, y: 0, duration: {d}, '
                  f'ease: "power3.out" }}, {t:.4f});')
    elif kind == "scale-pop":
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, scale: 0.955 }}, '
                  f'{{ opacity: 1, scale: 1, duration: {round(d*1.30,4)}, '
                  f'ease: "power2.out" }}, {t:.4f});')
    elif kind == "crowd-in":
        # El cierre radial de la acumulación (`objects.crowd_delta`): el
        # mundo se le echa encima al sujeto, el sujeto no se acerca a él.
        # `x`/`y` de GSAP son transform RELATIVO a la posición natural
        # del elemento — el `left`/`top` que ya le dio su slot horneado
        # — así que animar hacia (dx, dy) lo desplaza sin tocar layout.
        # El `scale` leve es la única concesión de "impacto": aquí sí es
        # intencional, no un artefacto que limpiar.
        dx, dy = a[4], a[5]
        js.append(f'tl.to(\'{sel}\', {{ x: {dx}, y: {dy}, scale: 1.06, '
                  f'duration: {d}, ease: "power2.inOut" }}, {t:.4f});')
    elif kind == "set-hidden":
        # La base explícita de un elemento que va a recibir VARIOS `fromTo`.
        # Sin ella, el estado previo al primer tween es el que dejó el último
        # `fromTo` autorado, que es un orden, no una decisión.
        js.append(f'tl.set(\'{sel}\', {{ opacity: 0, scaleY: 0.04 }}, {t:.4f});')
    elif kind == "rise-bar":
        # Una barra que CRECE. `chip-in` escala desde el centro y una barra que
        # sale de su propio centro no se lee como una barra que crece: se lee
        # como una barra que aparece. El origen lo pone el CSS del componente
        # (`transform-origin:50% 100%` en `.mdbar`), aquí solo se escala en Y —
        # transform, nunca `height`, que sería reflow (§6).
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, scaleY: 0.04 }}, '
                  f'{{ opacity: 1, scaleY: 1, duration: {round(d*1.30,4)}, '
                  f'ease: "power3.out" }}, {t:.4f});')
    elif kind == "fade-to":
        # Bajar la intensidad de un grupo SIN apagarlo. Nace del roster de la
        # pieza 19: «no necesitas utilizar todos» apaga 143 agentes de 146, y
        # `badge-out` no sirve porque los deja en opacidad 0 — el frame diría
        # que esos agentes ya no existen, y lo que dice la frase es que siguen
        # ahí sin usarse. El selector puede casar con MUCHOS elementos a la
        # vez: GSAP los tuenea como uno solo, que es lo que evita escribir 143
        # decisiones editoriales para un único gesto (la lección de
        # «coreografía interna» de la pieza 12).
        js.append(f'tl.to(\'{sel}\', {{ opacity: {a[4]}, duration: {d}, '
                  f'ease: "power2.inOut", overwrite: "auto" }}, {t:.4f});')
    elif kind == "grow-x":
        js.append(f'tl.fromTo(\'{sel}\', {{ width: 0 }}, '
                  f'{{ width: {a[4]}, duration: {d}, ease: "power2.out" }}, {t:.4f});')
    elif kind == "punch":
        # El titular ATERRIZA: entra corto, algo pasado de tamaño, y asienta.
        # `expo.out` frena muy fuerte al final, como se para algo con masa.
        # Nada de `back.out`: rebota como muelle y es lenguaje de dibujo animado.
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, scale: 1.045, y: -8 }}, '
                  f'{{ opacity: 1, scale: 1, y: 0, duration: {round(d*1.45,4)}, '
                  f'ease: "expo.out" }}, {t:.4f});')
    elif kind == "stamp":
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, scale: 1.10 }}, '
                  f'{{ opacity: 1, scale: 1, duration: {round(d*1.35,4)}, '
                  f'ease: "power3.out" }}, {t:.4f});')
    elif kind == "box-in":
        # Caja delimitadora sobre el producto: se clava, no se desliza.
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, scale: 1.06 }}, '
                  f'{{ opacity: 1, scale: 1, duration: {d}, '
                  f'ease: "power3.out" }}, {t:.4f});')
    elif kind == "hands-sweep":
        # El barrido de las agujas de un reloj de objects.py: dos
        # rotaciones simultáneas, SIEMPRE hacia delante (objects.hand_
        # angles ya resolvió el sentido — el compilador no vuelve a
        # decidirlo aquí, solo emite el tween).
        #
        # NO se anima `rotation` de GSAP. Depurado con un dump del
        # `transform` computado: en cuanto GSAP toca la propiedad
        # `rotation` de un `<g>` SVG, el pivote que reporta el navegador
        # es "0px 0px" pese a cualquier `transform-origin`/`svgOrigin`
        # declarado, y un SEGUNDO tween sobre la misma propiedad añade
        # además una traslación espuria. En vez de pelear con eso, se
        # anima un objeto plano `{v: ángulo}` y en cada `onUpdate` —
        # determinista: GSAP lo llama con el valor YA interpolado en
        # cada seek, nunca por reloj de pared — se reescribe a mano el
        # atributo SVG NATIVO `rotate(v, 150, 150)`, que lleva el pivote
        # incrustado en su propia sintaxis y no depende de ningún origen
        # que resolver.
        hour_from, hour_to, min_sel, min_from, min_to = a[4], a[5], a[6], a[7], a[8]
        hv, mv = f"_hv{next(_ANIM_NONCE)}", f"_mv{next(_ANIM_NONCE)}"
        js.append(f'const {hv} = {{ v: {hour_from} }};')
        js.append(f'tl.to({hv}, {{ v: {hour_to}, duration: {d}, '
                  f'ease: "power2.inOut", onUpdate: function() {{ '
                  f'document.querySelector({sel!r})?.setAttribute('
                  f'"transform", "rotate(" + {hv}.v + " 150 150)"); '
                  f'}} }}, {t:.4f});')
        js.append(f'const {mv} = {{ v: {min_from} }};')
        js.append(f'tl.to({mv}, {{ v: {min_to}, duration: {d}, '
                  f'ease: "power2.inOut", onUpdate: function() {{ '
                  f'document.querySelector({min_sel!r})?.setAttribute('
                  f'"transform", "rotate(" + {mv}.v + " 150 150)"); '
                  f'}} }}, {t:.4f});')
    elif kind == "count-roll":
        # El contador que sube (`objects.answer_counter`). MISMO patrón
        # que `hands-sweep` y por la misma razón: se tuenea un número
        # PURO y en cada `onUpdate` se reescribe el texto del span. GSAP
        # llama al onUpdate con el valor ya interpolado en cada seek, así
        # que el frame 312 pinta lo mismo se llegue a él reproduciendo o
        # buscando — que es lo que exige el contrato de determinismo.
        #
        # El prefijo va FUERA del número interpolado: metido dentro, un
        # `Math.round` sobre la cadena daría NaN.
        n_from, n_to, prefix = a[4], a[5], a[6]
        cv = f"_cv{next(_ANIM_NONCE)}"
        js.append(f'const {cv} = {{ v: {n_from} }};')
        if len(a) < 8:
            # Retrocompatibilidad estricta: esta rama es byte por byte la
            # emisión anterior a la pieza 4.
            js.append(f'tl.to({cv}, {{ v: {n_to}, duration: {d}, '
                      f'ease: "power2.out", onUpdate: function() {{ '
                      f'const e = document.querySelector({sel!r}); '
                      f'if (e) e.textContent = {json.dumps(prefix)} + '
                      f'Math.round({cv}.v); }} }}, {t:.4f});')
        else:
            suffix = a[7]
            js.append(f'tl.to({cv}, {{ v: {n_to}, duration: {d}, '
                      f'ease: "power2.out", onUpdate: function() {{ '
                      f'const e = document.querySelector({sel!r}); '
                      f'if (e) e.textContent = {json.dumps(prefix)} + '
                      f'Math.round({cv}.v) + {json.dumps(suffix)}; }} }}, {t:.4f});')
    elif kind in ("cursor-enter", "cursor-to"):
        x, y = a[4], a[5]
        if kind == "cursor-enter":
            js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, x: {x + 130}, y: {y + 230} }}, '
                      f'{{ opacity: 1, x: {x}, y: {y}, duration: {d}, '
                      f'ease: "power3.out" }}, {t:.4f});')
        else:
            js.append(f'tl.to(\'{sel}\', {{ x: {x}, y: {y}, duration: {d}, '
                      f'ease: "power2.inOut" }}, {t:.4f});')
    elif kind == "click":
        # `overwrite: "auto"` porque dos clics seguidos animan la MISMA
        # propiedad del mismo cursor: sin él, el tween de vuelta a escala 1
        # y el de bajada del clic siguiente se solapan y el resultado
        # depende del orden de evaluación, que es justo lo que rompe un
        # render determinista.
        ring = a[4]
        js.append(f'tl.to(\'{sel}\', {{ scale: 0.86, duration: 0.08, '
                  f'ease: "power2.in", overwrite: "auto" }}, {t:.4f});')
        js.append(f'tl.to(\'{sel}\', {{ scale: 1, duration: 0.15, '
                  f'ease: "power2.out", overwrite: "auto" }}, {t + .08:.4f});')
        js.append(f'tl.fromTo(\'{ring}\', {{ opacity: .8, scale: .30 }}, '
                  f'{{ opacity: 0, scale: 1.6, duration: {d}, ease: "power2.out", '
                  f'immediateRender: false }}, {t:.4f});')
    elif kind == "focus-app":
        js.append(f'tl.fromTo(\'{sel}\', {{ scale: 1, borderColor: "{TK.LINE}" }}, '
                  f'{{ scale: 1.04, borderColor: "{TK.rgba(C["alert"], .6)}", '
                  f'duration: {d * .45:.4f}, ease: "power2.out", yoyo: true, repeat: 1 }}, '
                  f'{t:.4f});')
    elif kind == "alert-hit":
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, scale: 1.08 }}, '
                  f'{{ opacity: 1, scale: 1, duration: {d * .55:.4f}, ease: "power3.out" }}, '
                  f'{t:.4f});')
        js.append(f'tl.to(\'{sel}\', {{ x: 7, duration: .055, yoyo: true, repeat: 3, '
                  f'ease: "power1.inOut" }}, {t + d * .55:.4f});')
        js.append(f'tl.set(\'{sel}\', {{ x: 0 }}, {t + d * .55 + .25:.4f});')
    elif kind == "draw":
        js.append('(function(){ const p = document.querySelector(' + repr(sel) + '); '
                  'if (!p) return; const n = p.getTotalLength(); '
                  'tl.set(p, { strokeDasharray: n, strokeDashoffset: n }, 0); '
                  f'tl.to(p, {{ strokeDashoffset: 0, duration: {d}, ease: "power2.out" }}, {t:.4f}); }})();')
    elif kind == "badge-out":
        # Toda salida necesita su `set` de kill duro en el borde: un seek
        # puede aterrizar después del fundido y dejar el elemento encendido
        # con estado obsoleto. El linter lo exige y tiene razón.
        js.append(f'tl.to(\'{sel}\', {{ opacity: 0, scale: .97, duration: {d}, '
                  f'ease: "power2.in" }}, {t:.4f});')
        js.append(f'tl.set(\'{sel}\', {{ opacity: 0 }}, {q(t + d):.4f});')
    elif kind == "type-word":
        # Tecleo por caracteres. Es determinista y seek-safe porque cada
        # estado se escribe con un `set` en su propio instante, no con un
        # onUpdate que dependa de por dónde iba la reproducción.
        word = a[4]
        n = len(word)
        step = round(d / max(1, n), 4)
        for ci in range(n + 1):
            txt = esc(word[:ci])
            js.append(f'tl.set(\'{sel}\', {{ innerHTML: '
                      f'{json.dumps(txt + "<span class=\'ccaret\'></span>")} }}, '
                      f'{t + ci * step:.4f});')
    elif kind == "caret-off":
        # La otra mitad de `type-word`, y existe porque `type-word` deja el
        # cursor DENTRO del innerHTML de su destino: con varias líneas
        # tecleándose una tras otra (el prompt de la pieza 16) cada línea
        # terminada conserva su cursor y al llegar la cuarta hay cuatro
        # parpadeando a la vez. Esto reescribe la línea sin el `<span
        # class="ccaret">`, y nada más — el texto se vuelve a pasar entero
        # en vez de recortar el span por DOM, para que el estado de este
        # instante no dependa de cuál fue el anterior (mismo contrato de
        # seek que `type-word`: un `set` por instante, sin `onUpdate`).
        js.append(f'tl.set(\'{sel}\', {{ innerHTML: '
                  f'{json.dumps(esc(a[4]))} }}, {t:.4f});')
    elif kind == "html-on":
        # Logos y otros fragmentos de interfaz que no pueden existir en el
        # DOM antes de que se nombren. El destino (un slot vacío) sí es
        # chrome y vive desde t=0; el markup se inyecta exactamente en `t`.
        js.append(f'tl.set(\'{sel}\', {{ innerHTML: {json.dumps(a[4])} }}, '
                  f'{t:.4f});')
    elif kind == "send-on":
        js.append(f'tl.set(\'{sel}\', {{ color: "{C["go"]}" }}, {t:.4f});')
        js.append(f'tl.fromTo(\'{sel}\', {{ scale: 1 }}, '
                  f'{{ scale: 1.12, duration: {d*.4:.4f}, yoyo: true, repeat: 1, '
                  f'ease: "power2.out" }}, {t:.4f});')
    elif kind == "jitter":
        # Algo que se FRENA EN SECO y vibra. Nace del contador de horas de la
        # pieza 3: la cifra es lo unico en cuadro y un frenazo sin vibracion se
        # lee como un corte de montaje, no como algo que se detuvo. Es la
        # segunda mitad de `alert-hit` sin su entrada —aqui el elemento ya esta
        # puesto y acaba de terminar su `count-roll`, asi que volver a hacerle
        # un `fromTo` de opacidad lo apagaria y lo encenderia— y lleva su `set`
        # de kill duro, porque un seek puede aterrizar a mitad del yoyo y dejar
        # la cifra descuadrada para siempre.
        js.append(f'tl.to(\'{sel}\', {{ x: 6, duration: .048, yoyo: true, '
                  f'repeat: 5, ease: "power1.inOut" }}, {t:.4f});')
        js.append(f'tl.set(\'{sel}\', {{ x: 0 }}, {q(t + d):.4f});')
    elif kind == "rot-to":
        # Un abanico que se CIERRA. Es el unico sitio del sistema donde se
        # anima `rotation`, y va sobre un `<div>`, no sobre un `<g>` de SVG: el
        # aviso de `hands-sweep` es especifico de SVG, donde el pivote que
        # reporta el navegador se va a "0px 0px" en cuanto GSAP toca la
        # propiedad. En un div el `transform-origin` del CSS se respeta, y el
        # componente lo declara (`.abtilt`, 50% 92%) para que las tarjetas
        # giren desde su BASE y no desde el centro, que es como se cierra una
        # baraja de verdad.
        js.append(f'tl.to(\'{sel}\', {{ rotation: {a[4]}, duration: {d}, '
                  f'ease: "power3.out", overwrite: "auto" }}, {t:.4f});')
    elif kind == "flip-out":
        js.append(f'tl.to(\'{sel}\', {{ scaleX: 0, duration: {d}, '
                  f'ease: "power2.in", overwrite: "auto" }}, {t:.4f});')
    elif kind == "flip-in":
        # `immediateRender: false`: el `from` (scaleX 0) de un fromTo se pinta
        # al MONTAR el timeline, así que sin esto el elemento nace plegado y
        # se queda invisible hasta el giro — el `flip-out` previo pliega algo
        # que ya estaba en cero (pieza 4: la tarjeta de b29 y la miniatura de
        # b33 desaparecían el beat entero hasta su palabra).
        js.append(f'tl.fromTo(\'{sel}\', {{ scaleX: 0 }}, '
                  f'{{ scaleX: 1, duration: {d}, ease: "power2.out", '
                  f'overwrite: "auto", immediateRender: false }}, {t:.4f});')
    elif kind == "blur-to":
        # Se aplica sobre un wrapper que ya está visible. Un fromTo pintaría
        # el estado inicial al montar el timeline y adelantaría el efecto.
        js.append(f'tl.to(\'{sel}\', {{ filter: "blur({a[4]}px)", duration: {d}, '
                  f'ease: "power2.inOut", overwrite: "auto" }}, {t:.4f});')
    elif kind == "scale-y-to":
        js.append(f'tl.to(\'{sel}\', {{ scaleY: {a[4]}, duration: {d}, '
                  f'ease: "power2.inOut", overwrite: "auto" }}, {t:.4f});')
    elif kind == "color-to":
        js.append(f'tl.to(\'{sel}\', {{ color: "{a[4]}", duration: {d}, '
                  f'ease: "power2.inOut", overwrite: "auto" }}, {t:.4f});')
    elif kind == "wipe-down":
        # La capa nítida ya nace recortada en CSS. Animar clip-path mantiene
        # la geometría estable (height provocaría reflow) y, al ser `to`, no
        # aplica un estado `from` al montar el timeline.
        js.append(f'tl.to(\'{sel}\', {{ clipPath: "inset(0 0 0% 0)", '
                  f'duration: {d}, ease: "power2.inOut", overwrite: "auto" }}, '
                  f'{t:.4f});')
    elif kind == "chatgpt-send-on":
        brand = TK.BRANDS["chatgpt"]
        js.append(f'tl.to(\'{sel}\', {{ backgroundColor: "{brand["send_bg"]}", '
                  f'color: "{brand["send_fg"]}", duration: {d}, '
                  f'ease: "power2.out", overwrite: "auto" }}, {t:.4f});')
    elif kind == "chatgpt-send-off":
        brand = TK.BRANDS["chatgpt"]
        js.append(f'tl.to(\'{sel}\', {{ backgroundColor: "{brand["send_off"]}", '
                  f'color: "{brand["send_fg"]}", duration: {d}, '
                  f'ease: "power2.inOut", overwrite: "auto" }}, {t:.4f});')
    elif kind == "settle-y":
        # El estado separado empieza cuando arranca el gesto, no al autorar el
        # timeline. `immediateRender:false` evita que el `from` adelante el
        # desplazamiento sobre un elemento que ya tiene estado declarado.
        js.append(f'tl.fromTo(\'{sel}\', {{ y: {a[4]} }}, '
                  f'{{ y: 0, duration: {d}, ease: "power2.out", '
                  f'overwrite: "auto", immediateRender: false }}, {t:.4f});')
    elif kind == "cam-kb":
        js.append(f'tl.fromTo(\'{sel}\', {{ scale: {a[4]} }}, '
                  f'{{ scale: {a[5]}, duration: {d}, ease: "none" }}, {t:.4f});')
    elif kind == "cam-push":
        js.append(f'tl.to(\'{sel}\', {{ scale: {a[4]}, y: {a[5]}, '
                  f'duration: {d}, ease: "power2.inOut" }}, {t:.4f});')
    return "\n".join(js)


# ── construcción ──────────────────────────────────────────────────────────────
def check_unique_element_ids(doc: str):
    """Ningún `id` se repite en la composición.

    ⚠ **Un SVG de marca inlineado dos veces se renderiza VACÍO la segunda vez,
    y el frame parece correcto hasta que miras el hueco.** La marca de Canva
    trae seis `<radialGradient>` con ids fijos de exportador y seis
    `fill="url(#…)"` que los apuntan; la pieza 16 la pinta cinco veces. El
    navegador resuelve cada referencia al PRIMER id del documento, así que en
    cuanto el renderer oculta el host de esa primera instancia las otras
    cuatro pierden su relleno: el marco se sigue viendo, la marca no. Medido
    sobre snapshots (t=15.5 y t=17.5 de la pieza 16) antes de que
    `logos.namespace_svg_ids` existiera.

    `logos.mark(uid=…)` es quien lo evita, renombrando los ids por instancia.
    Este gate es la red: comprueba el HTML YA ENSAMBLADO, así que caza también
    una colisión entre dos componentes distintos que `logos.py` no puede ver
    desde dentro de una sola llamada.
    """
    # `(?<![-\w])` y no `\b`: con `\b` el patrón casa DENTRO de
    # `data-viz-id="…"` (el límite de palabra cae en el guion) y los doce
    # visuales salían como ids repetidos — un falso positivo que llegó a
    # parar una compilación buena antes de afinarlo.
    ids = re.findall(r'(?<![-\w])id="([^"]+)"', doc)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        muestra = ", ".join(dupes[:6]) + (" …" if len(dupes) > 6 else "")
        sys.exit(
            f"{len(dupes)} id(s) repetidos en la composición: {muestra}\n"
            f"  Un id duplicado es HTML inválido, y si algo lo apunta con "
            f"`url(#id)` —un gradiente o un clip-path de una marca "
            f"vendorizada— la segunda copia se renderiza vacía.\n"
            f"  Si viene de un logo, pasa `uid=` a `logos.mark()` con algo "
            f"único por instancia.")


def build():
    words, dur = load()
    dur = q(dur)
    PUB.mkdir(parents=True, exist_ok=True)
    (PUB / "cards").mkdir(exist_ok=True)
    (PUB / "fonts").mkdir(exist_ok=True)
    (PUB / "vendor").mkdir(exist_ok=True)
    (PUB / "logos").mkdir(exist_ok=True)

    for src in sorted((SKILL / "assets" / "fonts").glob("*.woff2")):
        dst = PUB / "fonts" / src.name
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            dst.write_bytes(src.read_bytes())
    gsap = SKILL / "assets" / "gsap.min.js"
    dst = PUB / "vendor" / "gsap.min.js"
    if gsap.exists() and (not dst.exists() or dst.stat().st_size != gsap.stat().st_size):
        dst.write_bytes(gsap.read_bytes())
    # `logos.mark()` emite `<img src="logos/<slug>.png">` para las marcas
    # vendorizadas en formato PNG (Bklit UI, Kokonut UI): sin este paso esa
    # ruta no resuelve en el render y la card sale con la imagen rota. Se
    # copia el directorio entero, no un slug a mano, para que una marca PNG
    # nueva no necesite tocar este script.
    logos_src = ROOT / "assets" / "logos"
    if logos_src.exists():
        for src in sorted(logos_src.glob("*.png")):
            dst = PUB / "logos" / src.name
            if not dst.exists() or dst.stat().st_size != src.stat().st_size:
                dst.write_bytes(src.read_bytes())

    check_layout_default()
    shots, vid_els = build_shots(dur)
    check_no_black(shots, dur)
    check_band_speaker_clear(shots, dur)
    check_face_top_clear(shots, dur)
    check_cara_zoom(shots)
    check_band_top_covered(shots, dur)
    (viz_css, viz_media, viz_back, viz_over,
     viz_anims, viz_skins, viz_assets) = build_visuals(dur)
    card_css, card_hosts, card_anims, story_cards = build_cards(dur)
    sfx_els, sfx_lanes = build_sfx(dur)
    music_els = build_music(dur)

    anims = list(viz_anims) + list(card_anims)

    for rel in sorted(viz_assets):
        src = ROOT / "assets" / rel
        dst = PUB / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            dst.write_bytes(src.read_bytes())

    spans, cap_anims, key_anims, cap_rows = build_captions(words, dur, shots, viz_skins)

    # ── CSS ────────────────────────────────────────────────────────────────────
    faces = [("Inter", "Inter-400", 400), ("Inter", "Inter-500", 500),
             ("Inter", "Inter-600", 600), ("Inter", "Inter-700", 700),
             ("Inter", "Inter-800", 800), ("Inter", "Inter-900", 900),
             ("JetBrains Mono", "JetBrainsMono-400", 400),
             ("JetBrains Mono", "JetBrainsMono-700", 700)]
    ff = "\n".join(
        f"@font-face{{font-family:'{n}';src:url('fonts/{f}.woff2') format('woff2');"
        f"font-weight:{wg};font-style:normal;font-display:block}}"
        for n, f, wg in faces)
    ff += ("\n@font-face{font-family:'Fraunces';src:url('fonts/Fraunces-Italic800.woff2') "
           "format('woff2');font-weight:800;font-style:italic;font-display:block}")

    pip = pip_panel()
    style = f"""{ff}
{viz_css}
{card_css}
:root{{--bg:{C['bg']};--surface:{C['surface']};--text:{C['text']};
  --accent:{C['accent']};--go:{C['go']};--alert:{C['alert']};
  --accent-0:{C['accent']};--accent-1:{C['go']};--accent-2:{C['warn']};
  --accent-3:{C['accent_hi']};--accent-4:{C['alert']}}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;width:100%;height:100%;overflow:hidden;
  background:{C['bg']};font-family:{FONT}}}
#stage{{position:relative;width:100%;height:100%;overflow:hidden;background:{C['bg']}}}
/* El suelo DEBE ser un elemento del DOM, no el background de la página: la
   captura es por capas y descarta el fondo de html/body/#stage, con lo que todo
   lo que no es video saldría negro en el MP4 (en el navegador se ve bien, así
   que solo se detecta mirando el render). */
#ground{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;z-index:0;
  background:{grid()},{vignette()}}}
/* Geometría ESTÁTICA por encuadre. El renderer resuelve el rect del <video> una
   sola vez al cargar: animar width/height no reescala la imagen, solo la
   recorta. Por eso un punch-in es un ELEMENTO nuevo y el salto entre encuadres
   es un corte duro — que además es el lenguaje que pide la pieza. */
.vid{{position:absolute;object-fit:cover;display:block;z-index:1}}
.vid.panel{{border-radius:{RADIUS['xl']}px {RADIUS['xl']}px 0 0;
  box-shadow:0 -10px 50px rgba(0,0,0,.6)}}
/* El PiP se pinta POR ENCIMA del takeover. El índice de pista ordena el
   TIEMPO, no el apilado: eso lo decide el z-index (y, sin él, el orden del
   DOM). Como los <video> se emiten antes que los hosts, sin esta regla el
   mockup opaco se comía la ventana del creador — y solo se notaba en los
   visuales con fondo, porque sobre la grabación, que es transparente, se veía
   perfectamente. */
.vid.pip{{border-radius:{RADIUS['lg']}px;box-shadow:{TK.SHADOW_LIFT};
  outline:3px solid {ink_a(.14)};outline-offset:-3px;z-index:6}}
/* ── capa de visuales ──────────────────────────────────────────────────────
   `.vizcam` es la CÁMARA: el único elemento que GSAP escala o desplaza, para
   que ni el mockup ni la imagen tengan que ceder su propio transform. */
/* Apilado explícito, de abajo a arriba: suelo · metraje · media de un visual ·
   fondo · tarjetas · takeover · PiP · subtítulos. */
.viz{{position:absolute;pointer-events:none;overflow:hidden;z-index:3}}
.viz.over{{z-index:5}}
.vizcam{{position:absolute;inset:0;display:flex;align-items:center;
  justify-content:center;will-change:transform}}
.vizcam.mock{{padding-bottom:{round(H*0.16)}px}}
.vizimg{{width:100%;height:100%;object-fit:cover;display:block}}
.vizveil{{position:absolute;inset:0;pointer-events:none}}
.vizmed{{position:absolute;object-fit:cover;display:block;z-index:2}}
.card-host{{position:absolute;pointer-events:none;overflow:hidden;z-index:4}}
.card-host .card{{position:relative;width:100%;height:100%;overflow:hidden}}
#caption-host{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;
  pointer-events:none;overflow:hidden;z-index:7}}
/* ── subtítulos ───────────────────────────────────────────────────────────
   Bloques cortos, Inter 900 en mayúsculas. Sobre metraje el texto necesita
   separarse del fondo sin engordar: filete del suelo con `paint-order: stroke
   fill`, que pinta el trazo DETRÁS del relleno, más una sombra que lo asienta.
   Un borde normal engorda la letra y le quita el peso de grotesca. */
.cap{{position:absolute;left:{CAPTION_MARGIN}px;right:{CAPTION_MARGIN}px;
  text-align:center;opacity:0;font-family:{FONT};font-weight:900;
  font-size:{CAPTION_SIZE}px;line-height:1.14;letter-spacing:{TRACK['caption']};
  pointer-events:none}}
.cap .w{{display:inline-block;margin:0 9px;position:relative}}
.cap.on-dark .w{{color:{C['text']};-webkit-text-stroke:7px {C['bg']};
  paint-order:stroke fill;text-shadow:0 4px 22px {shade_a(.8)}}}
.cap.on-surface .w{{color:{C['text']};-webkit-text-stroke:0;
  text-shadow:0 2px 16px {shade_a(.95)}}}
/* Karaoke (Mejora 4, a petición del usuario, ver `build_captions`): trata-
   miento ÚNICO del subtítulo, SIN excepción de encuadre — ya no hay una
   keyword agrandada y de acento en `full`/`pip` (lo que había antes de esta
   ronda; el karaoke nació limitado a `band` en la Mejora 3 y ahora pierde esa
   frontera). `.w.kw` es CUALQUIER palabra del bloque —todas al mismo tamaño y
   color— y lo único que se mueve es `.wbg`, un rectángulo de acento detrás de
   la palabra que GSAP enciende y apaga por `opacity` (nunca por color, que
   reflowearía nada porque el tamaño no cambia, pero SÍ obligaría a
   interpolar un color sobre otro sin necesidad). `z-index:0` en `.w.kw` abre
   un contexto de apilamiento PROPIO para que el `z-index:-1` de `.wbg` quede
   contenido ahí dentro — sin él, un z-index negativo se escapa por debajo de
   TODO el documento (incluida la capa de vídeo) en vez de quedarse solo
   detrás de su propia palabra. El texto no lleva ninguna clase nueva: al no
   estar posicionado, pinta por delante de `.wbg` sin necesidad de otro
   z-index, y hereda el color y el filete de `.cap.on-dark .w` / `.cap.on-
   surface .w` de arriba según la PIEL del bloque — lo que cambia con esta
   Mejora es el resaltado, no la piel: en `full`/`pip` el subtítulo sigue
   ENCIMA del metraje, así que ahí sigue con `on-dark` y su filete del suelo
   de 7px; en `triband` sigue sin filete (`on-surface`, suelo liso, sin
   metraje detrás).
   El bleed (-8px horizontal, -4px vertical) es el padding: como es un
   `inset` de un elemento ABSOLUTO no cuenta para el ancho que mide
   `caption_metrics` (que sigue viendo solo el texto + su margen de
   siempre), así que no puede desajustar el reparto en líneas ni el gate de
   zona segura (el 20% de la plataforma en `full`/`pip`, la banda del
   hablante en `triband`).
   Contraste: la palabra lleva el color de TEXTO de la paleta y el fondo
   del karaoke es `accent_pill` —el acento empujado hacia el suelo hasta que
   ese texto pase 4.5:1 encima (tokens._derive, fijado en
   tests/test_paletas.py)—, en las dos paletas. */
.cap .w.kw{{z-index:0}}
.cap .wbg{{position:absolute;left:-8px;right:-8px;top:-4px;bottom:-4px;
  background:{C['accent_pill']};border-radius:{RADIUS['sm']}px;z-index:-1;
  opacity:0;pointer-events:none}}
.cta-kw{{position:absolute;left:{CAPTION_MARGIN}px;right:{CAPTION_MARGIN}px;
  text-align:center;opacity:0;font-family:'Fraunces',Georgia,serif;font-style:italic;
  font-weight:800;font-size:{round(CAPTION_SIZE * CTA_KW_RATIO)}px;line-height:1.14;
  color:{C['text']};-webkit-text-stroke:7px {C['bg']};paint-order:stroke fill;
  text-shadow:0 4px 22px {shade_a(.8)};pointer-events:none}}"""

    # ── timeline ───────────────────────────────────────────────────────────────
    js = ["const tl = window.gsap.timeline({ paused: true });"]

    for i, sc in enumerate(CARDS, 1):
        cid = f"card-{i:02d}"
        s, e = q(sc["start"]), q(min(sc["end"], dur))
        if e <= s:
            continue
        sel = f'.card-host[data-card-id="{cid}"]'
        js.append(f'tl.set(\'{sel}\', {{ visibility: "visible" }}, {s:.4f});')
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0 }}, '
                  f'{{ opacity: 1, duration: 0.34, ease: "power1.inOut" }}, {s:.4f});')
        js.append(f'tl.to(\'{sel}\', {{ opacity: 0, duration: 0.28, ease: "power1.inOut" }}, '
                  f'{max(s, e-0.28):.4f});')
        js.append(f'tl.set(\'{sel}\', {{ visibility: "hidden" }}, {e:.4f});')

    for v in VISUALS:
        vs = q(v["start"])
        ve = q(dur if v.get("end") is None else min(v["end"], dur))
        sel = f'.viz[data-viz-id="{v["id"]}"]'
        d_in = v.get("fade_in", 0.28)
        d_out = v.get("fade_out", 0.26)
        js.append(f'tl.set(\'{sel}\', {{ visibility: "visible" }}, {vs:.4f});')
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0 }}, '
                  f'{{ opacity: 1, duration: {d_in}, ease: "power1.inOut" }}, {vs:.4f});')
        # ⚠ **El visual que llega al final NO se funde a la salida.** Es una
        # regla que la bitácora ya escribía (§9, trampa 6) y que este emisor
        # no cumplía: le ponía a TODOS un `fade_out` que termina justo en `ve`,
        # así que un CTA con `end: null` pasaba sus últimos 0.26 s
        # apagándose y el último frame —el que congela la plataforma cuando
        # el reel vuelve a empezar— quedaba casi vacío. Medido sobre un
        # snapshot en t=56.8 de la pieza 16: el titular «CANVA» en gris a
        # medio fundir. La pieza 15 se entregó con el mismo defecto.
        if ve < dur - 1.0 / FPS:
            js.append(f'tl.to(\'{sel}\', {{ opacity: 0, duration: {d_out}, '
                      f'ease: "power1.inOut" }}, {max(vs, ve-d_out):.4f});')
            js.append(f'tl.set(\'{sel}\', '
                      f'{{ opacity: 0, visibility: "hidden" }}, {ve:.4f});')

    for a in anims:
        # `emit_anim` devuelve varias líneas unidas por "\n" cuando un gesto
        # necesita más de una sentencia (p. ej. `hands-sweep`). `extend` las
        # reparte de vuelta como entradas SUELTAS de `js`, igual que antes de
        # extraer la cadena — si no, la plantilla de abajo (que antepone la
        # indentación línea a línea) solo sangra la primera de cada gesto.
        js.extend(emit_anim(a).split("\n"))

    js.append("// bloques de subtítulo — entran enteros y se quedan quietos")
    frame = 1.0 / FPS
    for sel, s, e in cap_anims:
        d_in = round(min(0.14, (e - s) * 0.28), 4)
        d_out = round(min(0.10, (e - s) * 0.22), 4)
        out_t = q(e - d_out)
        if out_t < s + d_in + frame:
            out_t = q(s + d_in + frame)
            d_out = max(0.04, round(e - out_t, 4))
        js.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, scale: 0.97, y: 8 }}, '
                  f'{{ opacity: 1, scale: 1, y: 0, duration: {d_in}, '
                  f'ease: "power2.out" }}, {s:.4f});')
        js.append(f'tl.to(\'{sel}\', {{ opacity: 0, duration: {d_out}, '
                  f'ease: "power2.in" }}, {out_t:.4f});')
        js.append(f'tl.set(\'{sel}\', {{ opacity: 0 }}, {e:.4f});')

    js.append("// karaoke — el fondo de acento viaja palabra a palabra")
    # Karaoke en toda la pieza (Mejora 4): `key_anims` es siempre una 5-tupla
    # `(wid, at, hasta, d_in, d_out)`, una por PALABRA, no una sola por
    # bloque — antes de la Mejora 4 convivía con un esquema de 2-tuplas
    # (`full`/`pip`, una sola keyword por bloque, el texto cambiando de
    # color), que desapareció junto con la excepción de encuadre.
    for wid, at, until, d_in, d_out in key_anims:
        # El fondo aparece justo cuando suena la palabra y se apaga en cuanto
        # arranca la siguiente (o al acabar la propia palabra, si es la
        # última del bloque): por eso NO acumula — nunca hay dos fondos
        # encendidos a la vez, y al terminar el bloque no queda nada pintado.
        # Solo `opacity`: el texto no cambia de tamaño ni de color, así que no
        # hay nada más que animar. `d_in`/`d_out` ya vienen escalados a la
        # ventana de la palabra (`build_captions`), así que la entrada y la
        # salida nunca se pisan aunque la palabra dure menos que 0.05+0.08s.
        js.append(f'tl.fromTo("#{wid}-bg", {{ opacity: 0 }}, '
                  f'{{ opacity: 1, duration: {d_in}, ease: "power1.out" }}, '
                  f'{at:.4f});')
        js.append(f'tl.to("#{wid}-bg", {{ opacity: 0, duration: {d_out}, '
                  f'ease: "power1.in" }}, {until:.4f});')

    js.append('window.__timelines = window.__timelines || {};')
    js.append(f'window.__timelines["{COMP_ID}"] = tl;')

    doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<style>
{style}
</style>
</head>
<body>
<div id="stage" data-composition-id="{COMP_ID}" data-start="0" data-duration="{dur:.4f}"
     data-fps="{FPS}" data-width="{W}" data-height="{H}">

  <div id="ground"></div>

{chr(10).join(vid_els)}

{chr(10).join(viz_media)}

  <audio id="source-audio" src="input-video.mp4" data-start="0"
         data-duration="{dur:.4f}" data-track-index="{TRK_AUDIO}"
         data-volume="{VOICE_GAIN}"></audio>

{chr(10).join(music_els)}

{chr(10).join(sfx_els)}

{chr(10).join(viz_back)}

{chr(10).join(card_hosts)}

{chr(10).join(viz_over)}

  <!-- los bloques comparten posición a propósito: solo uno es visible a la vez -->
  <div id="caption-host" class="clip" data-layout-allow-overlap data-start="0"
       data-duration="{dur:.4f}" data-track-index="{TRK_CAPTION}">
{chr(10).join('    ' + s for s in spans)}
  </div>

  <script src="vendor/gsap.min.js"></script>
  <script>
  (function () {{
{chr(10).join('    ' + l for l in js)}
  }})();
  </script>
</div>
</body>
</html>
"""
    check_unique_element_ids(doc)
    (PUB / "index.html").write_text(doc, encoding="utf-8")

    (WORK / "storyboard.json").write_text(json.dumps(dict(
        schemaVersion=3,
        composition=dict(fps=FPS, width=W, height=H, durationSeconds=dur,
                         layout="portrait" if FMT == "REEL" else "landscape",
                         themeId=f"marca-{TK.PALETTE}", seed=42),
        videoTrack=dict(sourcePath="input-video.mp4", startSec=0, endSec=dur,
                        bounds=dict(x=0, y=0, width=W, height=H)),
        subtitles=dict(enabled=True, style="chunk-keyword"),
        cards=story_cards), ensure_ascii=False, indent=2), encoding="utf-8")

    # ── informe ────────────────────────────────────────────────────────────────
    live = [s for s in shots if s["kind"] != "off"]
    print(f"\nencuadres ({len(live)} en pantalla de {len(shots)}):")
    for i, s in enumerate(shots):
        print(f"  {i:>2} [{s['start']:5.2f}-{s['end']:5.2f}] {s['kind']:<5} "
              f"zoom {s['zoom']:.2f} anchor {s['anchor']:.2f}")
    print(f"\n{len(cap_rows)} bloques de subtítulo:")
    for ci, s, e, top, txt, key in cap_rows:
        k = f"  ⟨{key}⟩" if key else ""
        print(f"  {ci:>2} [{s:5.2f}-{e:5.2f}] top={top:<4} {txt}{k}")
    gaps = []
    for i in range(len(cap_rows) - 1):
        g = cap_rows[i + 1][1] - cap_rows[i][2]
        if g > 0.9:
            gaps.append((cap_rows[i][2], round(g, 2)))
    print()
    print(f"duración      {dur}s")
    print(f"encuadres     {len(live)}  (cambio medio cada "
          f"{dur/max(1,len(live)):.1f}s)")
    print(f"tarjetas      {len(CARDS)}")
    print(f"visuales      {len(VISUALS)}")
    print(f"bloques cap   {len(cap_rows)}  ·  keywords {len(key_anims)}")
    print(f"efectos       {len(sfx_els)} en {sfx_lanes} pista(s)"
          f"{'  · música ✓' if music_els else ''}")
    print(f"sentencias JS {len(js)}")
    print(f"-> {PUB/'index.html'}")


def main():
    ap = argparse.ArgumentParser(description="Genera la composición de una pieza")
    ap.add_argument("--project", default=".", help="raíz del proyecto de edición")
    ap.add_argument("--piece", default="1", help="identificador de la pieza")
    a = ap.parse_args()
    configure(Path(a.project).resolve(), a.piece)
    build()


if __name__ == "__main__":
    main()
