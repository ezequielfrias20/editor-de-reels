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
import json
import math
import re
import subprocess
import sys
from pathlib import Path

from PIL import ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import caption_fonts  # noqa: E402
import caption_metrics  # noqa: E402
import mockups  # noqa: E402
import objects  # noqa: E402
from tokens import C, FILL, FONT, GLOW, LINE, LINE_HI, MONO, RADIUS  # noqa: E402
from tokens import SHADOW, SHADOW_LIFT, TRACK, TYPE, grid, vignette  # noqa: E402

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
SHOTS = CARDS = VISUALS = SFX = MUSIC = None
KEYWORDS = None
CAPTIONS = None
LAYOUT = {}         # bloque `layout` del plan (Tarea 3); {} si el plan no trae ninguno

# Cuánto más grande es la keyword que el resto del bloque. El tope está
# medido en `caption_metrics`: por encima, un bloque de dos líneas se queda
# sin presupuesto de zona segura.
KW_SCALE = caption_metrics.KEYWORD_SCALE_MAX
CAPTION_SIZE = CAPTION_MAXW = CAPTION_MARGIN = None


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

    Van a ancho completo y NO a hueso: entre ellas queda suelo grafito, que es
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
        b["objpos"] = f"50% {round(anchor * 100)}%"
        return b
    if kind == "band":
        b = dict(triband_panels()["speaker"])
        b["objpos"] = f"50% {round(anchor * 100)}%"
        return b
    b = dict(pip_panel())
    b["objpos"] = f"50% {round(anchor * 100)}%"
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
    global ROOT, WORK, PUB, PIECE, W, H, FMT, T, SRC_W, SRC_H, CHIN, CX
    global SHOTS, CARDS, VISUALS, SFX, MUSIC, KEYWORDS, CAPTIONS, LAYOUT
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

    SHOTS = plan["shots"]
    CARDS = plan.get("cards", [])
    VISUALS = plan.get("visuals", [])
    SFX = [tuple(x) for x in plan.get("sfx", [])]
    MUSIC = plan.get("music")
    KEYWORDS = plan.get("keywords", [])
    # Bloques declarados por el EDL (rangos de palabras). Si no vienen,
    # `build_captions` trocea como siempre: las piezas 1-9 no los traen.
    CAPTIONS = plan.get("captions") or None
    LAYOUT = plan.get("layout") or {}
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
    grafito se leen como un fallo del video. En el navegador no se nota porque
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
                for key in ("switch_at", "draw_at", "at", "stamp_at"):
                    if key in kw:
                        kw[key] = [q(t - s) for t in kw[key]]
                for key in ("alert_at", "type_at", "send_at"):
                    if key in kw:
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
            radius = (f"0 0 {RADIUS['lg']}px {RADIUS['lg']}px" if v.get("chrome")
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
            if v.get("chrome"):
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

        # Un mockup necesita fondo OPACO o se ve el metraje por detrás.
        opaque = v["kind"] == "mockup"
        bg = f"{grid()},{vignette()}" if opaque else "transparent"
        css.append(f"""
.viz[data-viz-id="{vid}"] .vizbg{{position:absolute;inset:0;background:{bg}}}""")
        css.append(hud_css)
        if body_css:
            css.append(body_css)

        veil = (f'<div class="vizveil" style="background:rgba(11,12,16,{v["veil"]})"></div>'
                if v.get("veil") else "")
        camcls = "vizcam mock" if v["kind"] == "mockup" else "vizcam"
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
        inner = (f'<div class="vizbg"></div>'
                 f'<div class="{camcls}" id="{vid}-cam">{body_html_}</div>'
                 f'{veil}{hud_html}')
        vcls = "viz clip" if v["role"] == "backdrop" else "viz over clip"
        (hosts_back if v["role"] == "backdrop" else hosts_over).append(
            f'<div class="{vcls}" data-viz-id="{vid}" id="host-{vid}" '
            f'data-start="{s:.4f}" data-duration="{d:.4f}" '
            f'data-track-index="{track}" data-layout-allow-overlap '
            f'style="left:0px;top:0px;width:{W}px;height:{H}px;'
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


def build_sfx(dur):
    """Los efectos, con el volumen CALCULADO por medición.

    Los archivos no vienen igualados —hay 27 dB entre el más caliente y el más
    flojo—, así que un número escrito a mano tapa la voz con unos y hace
    inaudibles otros. Se lleva la media de cada uno al objetivo y se recorta si
    el transitorio se pasa del techo; manda el más restrictivo.
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
        s = q(start)
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
  letter-spacing:.10em;color:{C['text2']};background:rgba(22,24,31,.9);
  border:1px solid {LINE};border-radius:{RADIUS['pill']}px;padding:14px 24px;opacity:0}}"""
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
{p} .mcell{{flex:1;background:rgba(22,24,31,.94);border:1px solid {LINE};
  border-radius:{RADIUS['lg']}px;padding:28px 14px 24px;text-align:center;
  box-shadow:{SHADOW};opacity:0}}
{p} .mcell.hot{{border-color:rgba(124,92,255,.5);
  background:linear-gradient(180deg,{FILL['violet']} 0%,rgba(22,24,31,.94) 72%)}}
{p} .mval{{font-family:{FONT};font-weight:900;font-size:{round(T['card_title']*1.35)}px;
  line-height:.98;letter-spacing:-.04em;color:{C['text']}}}
{p} .mcell.hot .mval{{color:{C['violet_hi']}}}
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
  border:1px solid {LINE_HI};border-radius:{RADIUS['md']}px;
  box-shadow:{SHADOW};opacity:0}}
{p} .mtdot{{width:14px;height:14px;border-radius:50%;background:{C['violet']};
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
  border:1px solid {LINE_HI};border-radius:{RADIUS['lg']}px;padding:30px 32px;
  display:flex;flex-direction:column;gap:18px;box-shadow:{SHADOW};
  filter:blur(5px);opacity:.85}}
{p} .tsbar{{height:30px;width:52%;border-radius:8px;background:{C['violet']};
  margin-bottom:8px}}
{p} .tsrow{{height:20px;border-radius:10px;background:{LINE_HI};display:block}}
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
  color:{C['bg']};box-shadow:0 18px 50px rgba(52,227,155,.28);opacity:0}}"""
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
        # pastilla, y el titular con el MISMO filete de grafito que el
        # subtítulo (`paint-order: stroke fill`, el trazo detrás del relleno,
        # que no engorda la letra). Una sombra sola no basta: se difumina y
        # deja el violeta de la keyword por debajo de 3:1 en cuanto el fondo
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
  background:rgba(11,12,16,.72);border:1px solid {LINE};
  border-radius:{RADIUS['pill']}px;padding:12px 22px;white-space:nowrap;opacity:0}}
{p} .kick s{{width:10px;height:10px;border-radius:50%;background:{C['violet']};
  display:block;text-decoration:none}}
{p} .ttl{{display:flex;flex-direction:column;align-items:center;gap:2px;
  font-family:{FONT};font-weight:900;font-size:{T['headline']}px;line-height:1.02;
  letter-spacing:{TRACK['headline']};color:{C['text']};text-align:center;
  -webkit-text-stroke:7px {C['bg']};paint-order:stroke fill;
  text-shadow:0 3px 18px rgba(11,12,16,.85),0 1px 3px rgba(11,12,16,.9)}}
{p} .tline{{display:block}}
/* La keyword del titular lleva SU PROPIO suelo opaco, no solo el filete.
   El filete salva la tinta blanca, pero el violeta sobre una pared iluminada
   se queda en 1.4:1 — medido. Con la pastilla grafito el par es siempre
   violet_hi sobre bg = 6.70:1, pase lo que pase detrás en el metraje, y
   además rima con la pastilla del kicker. */
{p} .tkey{{color:{C['violet_hi']};background:{C['bg']};-webkit-text-stroke:0;
  border-radius:{RADIUS['sm']}px;padding:0 .10em;
  -webkit-box-decoration-break:clone;box-decoration-break:clone}}
{p} .sub{{font-family:{FONT};font-weight:500;font-size:{T['body']}px;line-height:1.32;
  color:{C['text2']};text-align:center;max-width:{round(W*0.76)}px;
  text-shadow:0 2px 12px rgba(11,12,16,.9);opacity:0}}
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


def build_captions(words, dur, shots, viz_skins):
    """Bloques de 2–6 palabras. Se resalta SOLO la keyword.

    Doctrina, y es lo contrario del karaoke que usaba el sistema anterior:
    resaltar todas las palabras convierte el subtítulo en un metrónomo y el ojo
    deja de leer. Resaltar una sola —una cifra, una herramienta, el concepto—
    convierte esa palabra en el titular del frame.

    El bloque entra entero y se queda quieto; lo único que se mueve es la
    keyword, en el instante exacto en que se pronuncia.
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
        chunks = merged
        # una sola keyword por bloque: la primera que califique
        for ch in chunks:
            i = next((i for i, (_, up) in enumerate(ch)
                      if is_key(up, KEYWORDS)), -1)
            key_ranges.append((i, i) if i >= 0 else None)

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

        # Las palabras normales van en CAJA DE FRASE y solo la keyword en
        # MAYÚSCULA: el contraste de caja es lo que la convierte en el titular
        # del frame. La mayúscula continua convertía la banda entera en un
        # metrónomo y el ojo dejaba de leer.
        parts, disp = [], []
        for i, (w, up) in enumerate(ch):
            en_key = klo <= i <= khi
            txt = up if en_key else w["text"].strip().rstrip(",.:;!?")
            disp.append(txt)
            if en_key:
                wid = f"c{ci}k{i}"
                parts.append(f'<span class="w key" id="{wid}">{esc(txt)}</span>')
                key_anims.append((wid, q(max(w["start"], s))))
            else:
                parts.append(f'<span class="w">{esc(txt)}</span>')

        # La altura la decide LO QUE HAY DETRÁS en ese frame: el encuadre activo
        # (que mueve la barbilla) o el visual a pantalla completa que lo tape.
        # Se consulta por el PUNTO MEDIO del bloque, no por su inicio: un bloque
        # que arranca 20 ms antes de que entre el plano siguiente pertenece al
        # plano siguiente, y midiendo por el inicio heredaba la altura del
        # anterior — o la de un tramo `off`, que no tiene cara que esquivar.
        sh = shot_at(shots, (s + e) / 2)
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
        if sh and sh["kind"] == "pip":
            if not tops:
                skin = "on-dark"
            tops.append(round(H * 0.60))
        elif sh and sh["kind"] != "off":
            tops.append(round(min(chin_at(sh) + H * 0.030, H * 0.80)))
        top = max(tops) if tops else round(H * 0.72)

        # ZONA SEGURA: en REEL el 20 % inferior lo pinta la plataforma con su
        # propia interfaz, así que ahí no puede caer TINTA — no basta con que
        # empiece antes de 1536. La cuenta necesita el número de líneas Y el
        # tamaño MÁXIMO del bloque (la keyword mide 1.22x), así que vive en
        # `caption_metrics`, testeable sin renderizar. Sin esto un bloque de
        # dos líneas colocado sobre un gráfico metía la segunda línea 46 px
        # dentro de la interfaz.
        # Se mide el texto que de verdad se pinta (`disp`: caja de frase salvo
        # la keyword), no la versión en mayúsculas: la mayúscula es más ancha y
        # habría subido el techo sin necesidad.
        m = caption_metrics.measure_block(disp, CAPTION_SIZE, krange, FMT, H, W,
                                          cache_dir=WORK)
        n_lines, floor_top = m["n_lines"], m["floor_top"]
        top = min(top, floor_top)

        spans.append(f'<div class="cap {skin}" id="cap{ci}" data-layout-allow-overlap '
                     f'style="top:{top}px">{"".join(parts)}</div>')
        anims.append((f"#cap{ci}", s, e))
        rows.append((ci, s, e, top, " ".join(u for _, u in ch),
                     ch[key_idx][1] if key_idx >= 0 else ""))
    return spans, anims, key_anims, rows


# ── construcción ──────────────────────────────────────────────────────────────
def build():
    words, dur = load()
    dur = q(dur)
    PUB.mkdir(parents=True, exist_ok=True)
    (PUB / "cards").mkdir(exist_ok=True)
    (PUB / "fonts").mkdir(exist_ok=True)
    (PUB / "vendor").mkdir(exist_ok=True)

    for src in sorted((SKILL / "assets" / "fonts").glob("*.woff2")):
        dst = PUB / "fonts" / src.name
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            dst.write_bytes(src.read_bytes())
    gsap = SKILL / "assets" / "gsap.min.js"
    dst = PUB / "vendor" / "gsap.min.js"
    if gsap.exists() and (not dst.exists() or dst.stat().st_size != gsap.stat().st_size):
        dst.write_bytes(gsap.read_bytes())

    shots, vid_els = build_shots(dur)
    check_no_black(shots, dur)
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

    pip = pip_panel()
    style = f"""{ff}
{viz_css}
{card_css}
:root{{--bg:{C['bg']};--surface:{C['surface']};--text:{C['text']};
  --violet:{C['violet']};--go:{C['go']};--alert:{C['alert']};
  --accent-0:{C['violet']};--accent-1:{C['go']};--accent-2:{C['warn']};
  --accent-3:{C['violet_hi']};--accent-4:{C['alert']}}}
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
.vid.pip{{border-radius:{RADIUS['lg']}px;box-shadow:{SHADOW_LIFT};
  outline:3px solid rgba(255,255,255,.14);outline-offset:-3px;z-index:6}}
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
   separarse del fondo sin engordar: filete de grafito con `paint-order: stroke
   fill`, que pinta el trazo DETRÁS del relleno, más una sombra que lo asienta.
   Un borde normal engorda la letra y le quita el peso de grotesca. */
.cap{{position:absolute;left:{CAPTION_MARGIN}px;right:{CAPTION_MARGIN}px;
  text-align:center;opacity:0;font-family:{FONT};font-weight:900;
  font-size:{CAPTION_SIZE}px;line-height:1.14;letter-spacing:{TRACK['caption']};
  pointer-events:none}}
.cap .w{{display:inline-block;margin:0 9px;position:relative}}
.cap.on-dark .w{{color:{C['text']};-webkit-text-stroke:7px {C['bg']};
  paint-order:stroke fill;text-shadow:0 4px 22px rgba(11,12,16,.8)}}
.cap.on-surface .w{{color:{C['text']};-webkit-text-stroke:0;
  text-shadow:0 2px 16px rgba(11,12,16,.95)}}
/* La keyword ya no es una pastilla: es TEXTO. Cuatro rasgos a la vez la
   convierten en el titular del frame sin añadir un objeto — mayúscula (las
   demás van en caja de frase), ExtraBold, {round(CAPTION_SIZE * KW_SCALE)}px
   ({KW_SCALE}x) y violeta. Medido: violet_hi da 6.70:1 sobre bg y 6.07:1
   sobre surface, así que aguanta texto normal en los dos suelos; `violet` a
   secas se queda en 4.08:1 sobre surface y NO llega.
   El color arranca en blanco y se enciende en el instante exacto en que la
   palabra se pronuncia — el tamaño es estático para que el bloque no
   reflowee. */
.cap .w.key{{font-size:{round(CAPTION_SIZE * KW_SCALE)}px;font-weight:800;
  color:{C['text']}}}
.cap.on-dark .w.key{{-webkit-text-stroke:7px {C['bg']};paint-order:stroke fill}}
.cap.on-surface .w.key{{-webkit-text-stroke:0}}"""

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
        js.append(f'tl.to(\'{sel}\', {{ opacity: 0, duration: {d_out}, '
                  f'ease: "power1.inOut" }}, {max(vs, ve-d_out):.4f});')
        js.append(f'tl.set(\'{sel}\', {{ opacity: 0, visibility: "hidden" }}, {ve:.4f});')

    for a in anims:
        kind, sel, t, d = a[0], a[1], q(a[2]), a[3]
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
            hv, mv = f"_hv{len(js)}", f"_mv{len(js) + 1}"
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
            cv = f"_cv{len(js)}"
            js.append(f'const {cv} = {{ v: {n_from} }};')
            js.append(f'tl.to({cv}, {{ v: {n_to}, duration: {d}, '
                      f'ease: "power2.out", onUpdate: function() {{ '
                      f'const e = document.querySelector({sel!r}); '
                      f'if (e) e.textContent = {json.dumps(prefix)} + '
                      f'Math.round({cv}.v); }} }}, {t:.4f});')
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
                      f'{{ opacity: 0, scale: 1.6, duration: {d}, ease: "power2.out" }}, {t:.4f});')
        elif kind == "focus-app":
            js.append(f'tl.fromTo(\'{sel}\', {{ scale: 1, borderColor: "{LINE}" }}, '
                      f'{{ scale: 1.04, borderColor: "rgba(255,90,90,.6)", '
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
        elif kind == "send-on":
            js.append(f'tl.set(\'{sel}\', {{ color: "{C["go"]}" }}, {t:.4f});')
            js.append(f'tl.fromTo(\'{sel}\', {{ scale: 1 }}, '
                      f'{{ scale: 1.12, duration: {d*.4:.4f}, yoyo: true, repeat: 1, '
                      f'ease: "power2.out" }}, {t:.4f});')
        elif kind == "cam-kb":
            js.append(f'tl.fromTo(\'{sel}\', {{ scale: {a[4]} }}, '
                      f'{{ scale: {a[5]}, duration: {d}, ease: "none" }}, {t:.4f});')
        elif kind == "cam-push":
            js.append(f'tl.to(\'{sel}\', {{ scale: {a[4]}, y: {a[5]}, '
                      f'duration: {d}, ease: "power2.inOut" }}, {t:.4f});')

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

    js.append("// keyword — el violeta se ENCIENDE justo al pronunciarse")
    for wid, at in key_anims:
        # Solo `color` y `scale`, los dos en el allowlist. El TAMAÑO no se
        # anima: es estático en el CSS para que el bloque no reflowee a mitad
        # de lectura. Lo que se mueve es el color, en el instante exacto en que
        # la palabra suena, más un golpe corto de escala.
        js.append(f'tl.fromTo("#{wid}", {{ color: "{C["text"]}" }}, '
                  f'{{ color: "{C["violet_hi"]}", duration: 0.16, '
                  f'ease: "power3.out" }}, {at:.4f});')
        js.append(f'tl.fromTo("#{wid}", {{ scale: 1 }}, '
                  f'{{ scale: 1.06, duration: 0.14, yoyo: true, repeat: 1, '
                  f'ease: "power2.out", overwrite: false }}, {at:.4f});')

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
    (PUB / "index.html").write_text(doc, encoding="utf-8")

    (WORK / "storyboard.json").write_text(json.dumps(dict(
        schemaVersion=3,
        composition=dict(fps=FPS, width=W, height=H, durationSeconds=dur,
                         layout="portrait" if FMT == "REEL" else "landscape",
                         themeId="graphite-violet", seed=42),
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
