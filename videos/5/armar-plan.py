#!/usr/bin/env python3
"""Pieza 5 — escribe videos/5/plan-cuerpo.json y videos/5/plan-cta-instagram.json.

El plan se arma con un script (y no a mano) por dos cosas que se calculan:
· los tiempos salen de `armar-version.py palabras` (línea del corte), por índice de palabra;
· las cajas sobre las capturas salen del recorte de `capturas.py` (coordenadas MEDIDAS, §7).

    .venv/bin/python videos/5/armar-plan.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIEZA = ROOT / "videos" / "5"
CAPS = json.loads((ROOT / "assets" / "capturas-5" / "capturas.json").read_text())
ANCHOR_BAND = 0.7496          # armar-version.py anchor: válido en [0.7420, 0.7572]
ANCHOR_FULL = 0.46            # centroide de cara medido (46.2 % del alto)
HEAD = 84                     # cabecera opaca de tool_recording
CAP_TOP = 1400                # subtítulo bajo los gráficos a lienzo

# ── palabras (línea del corte) ────────────────────────────────────────────────
out = subprocess.run([sys.executable, str(ROOT / "scripts" / "armar-version.py"), "palabras",
                      "--piece", "5", "--plataforma", "instagram"],
                     capture_output=True, text=True, cwd=ROOT, check=True).stdout
W, CTA = {}, None
for ln in out.splitlines():
    p = ln.split()
    if len(p) >= 4 and p[0].isdigit():
        W[int(p[0])] = (float(p[1]), float(p[2]), " ".join(p[3:]))
    elif "CTA desde" in ln:
        CTA = float(ln.split("CTA desde")[1].split()[0])
if CTA is None:
    raise SystemExit("armar-version.py palabras no marcó dónde empieza el CTA")
DUR = W[max(W)][1]


def t(i, txt=None):
    """Inicio de la palabra i, comprobando que es la que se espera."""
    s, _, w = W[i]
    if txt and not w.lower().strip(".,:;").startswith(txt.lower()):
        raise SystemExit(f"palabra {i} es {w!r}, se esperaba {txt!r}")
    return s


# ── capturas: rect y cajas medidas ────────────────────────────────────────────
def rect_de(cap):
    h = CAPS[cap]["h"]
    return [20, round(40 + (760 - h) / 2), 1040, h]


def caja(cap, tramo, t_in, t_out, ox, oy, ow, oh, start, pad=8):
    """Una caja en coordenadas del LIENZO a partir de coordenadas del cuadro original.
    Contempla el recorte, la escala, la cabecera y el empuje ×1.00→×1.03 (a mitad de la caja)."""
    rx, ry, rw, rh = rect_de(cap)
    tramos = CAPS[cap]["tramos"]
    (cx, cy, cw, ch), dur = tramos[tramo]
    t0 = start + sum(d for _, d in tramos[:tramo])
    s = rw / cw
    hc = rh - HEAD
    z = 1 + .03 * min(1, max(0, ((t_in + t_out) / 2 - t0) / dur))
    mx, my = rx + rw / 2, ry + HEAD + hc / 2

    def X(o):
        return mx + ((rx + (o - cx) * s) - mx) * z

    def Y(o):
        return my + ((ry + HEAD + (o - cy) * s) - my) * z
    x0, y0, x1, y1 = X(ox) - pad, Y(oy) - pad, X(ox + ow) + pad, Y(oy + oh) + pad
    return [round(t_in, 3), round(t_out, 3), round(x0), round(y0), round(x1 - x0), round(y1 - y0)]


# ── beats ─────────────────────────────────────────────────────────────────────
shots, visuals, sfx = [], [], []


def mock(vid, start, end, fn, kw, formato, nota):
    v = {"id": vid, "role": "takeover", "kind": "mockup", "start": round(start, 3), "end": round(end, 3),
         "fade_in": 0.0, "fade_out": 0.0, "absolute_times": True, "_": nota, "mock": [fn, kw]}
    if formato == "partida":
        v["band"] = "top"
    else:
        v["cap_top"] = CAP_TOP
        kw["lienzo"] = True
    visuals.append(v)
    shots.append({"at": round(start, 3), "kind": "band", "anchor": ANCHOR_BAND} if formato == "partida"
                 else {"at": round(start, 3), "kind": "off"})


def captura(vid, start, end, cap, slug, nombre, cajas, nota):
    visuals.append({"id": vid, "role": "takeover", "kind": "screen-video", "band": "top",
                    "start": round(start, 3), "end": round(end, 3), "fade_in": 0.0, "fade_out": 0.0,
                    "src": f"capturas-5/{cap}.mp4", "rect": rect_de(cap),
                    "tool_recording": {"slug": slug, "name": nombre, "hairline": 2},
                    "boxes": cajas, "_": nota})
    shots.append({"at": round(start, 3), "kind": "band", "anchor": ANCHOR_BAND})


def cara(at, zoom):
    shots.append({"at": round(at, 3), "kind": "full", "zoom": zoom, "anchor": ANCHOR_FULL})


def fx(at, f, vol, nota):
    sfx.append([round(at, 3), f, vol, nota])


# b1 · 0–3 s · gancho
b = t(7, "instala")
mock("v-b1-barrera", 0.0, b, "terminal_barrera", {"at": [t(4, "abrir"), t(6, "Code")]}, "partida",
     "GANCHO en comic: la terminal de Claude Code (barra de título desde el primer cuadro) se abre en «abrir» y en «Code» baja la barrera a rayas y la congela.")
fx(t(4), "whoosh-short", .45, "la terminal arranca a abrirse")
fx(t(6), "impact-bass-2", .55, "la barrera baja de golpe y la congela")
# b2 · el zócalo
e = t(11, "1")
mock("v-b2-zocalo", b, e, "zocalo", {"variant": "instala", "at": [b, t(9, "5"), t(10, "plugins")]}, "grafico",
     "El zócalo de cinco huecos alrededor de la terminal: se dibuja en «instala», caen cinco mosaicos en blanco en «5» y en «plugins» se encienden y la barrera se levanta.")
for k in range(5):
    fx(t(9) + k * .09, "click-soft", .55, f"encastre del mosaico {k + 1}")
fx(t(10), "chime", .5, "los cinco huecos se encienden juntos")
# b3 · 1, OmniRoute
s3, e3 = t(11, "1"), t(13, "conecta")
mock("v-b3-omni", s3, e3, "zocalo", {"variant": "enciende", "puestos": 0, "at": [s3, t(12, "OmniRoute")]}, "partida",
     "Hueco 1 se ilumina en «1»; en «OmniRoute» su contorno se dibuja con neón y cae la pastilla. Mismo gesto en los cinco plugins.")
fx(t(12), "sparkle", .5, "trazo de neón del logo (motivo de la lista)")
# b4 · captura OmniRoute
s4, e4 = e3, t(19, "200")
captura("v-b4-cap-omni", s4, e4, "omni-proveedores", "omniroute", "OmniRoute",
        [caja("omni-proveedores", 0, t(16, "con"), e4, 280, 262, 524, 214, s4)],
        "CAPTURA REAL (pedido de Ezequiel): el panel de proveedores de OmniRoute; en «con más de» la caja marca los Free Tier Providers.")
fx(t(16), "click-soft", .5, "la caja marca los proveedores gratis")
# b5 · +200 proveedores
s5, e5 = e4, t(21, "gratis")
mock("v-b5-anillo", s5, e5, "anillo_proveedores", {"at": [s5, t(20, "proveedores")]}, "grafico",
     "Claude Code en el centro y el anillo de proveedores (logos del propio repo de OmniRoute) que se completa en «200» con el contador a +200; en «proveedores» viajan partículas al centro.")
for k, dt in enumerate((0, .09, .17, .24, .30, .35, .39, .42)):
    fx(s5 + dt, "ping", .42, f"tick {k + 1} del contador, acelera y frena en 200")
# b6 · gratis de API de IA
s6, e6 = e5, t(26, "Resultado")
mock("v-b6-llaves", s6, e6, "costo_llaves", {"at": [s6, t(23, "API"), t(25, "IA")]}, "partida",
     "Tres fichas con su costo: cae a $0 en «gratis», giran y son llaves de API en «API», detrás se encienden los modelos en «IA».")
fx(s6, "click", .45, "el costo cae a cero")
fx(t(23), "whoosh-short", .45, "las fichas se dan vuelta")
# b7 · cara (la quietud antes del clímax)
cara(e6, 1.05)
cara(t(30, "Se"), 1.12)
# b8 · salta al siguiente modelo
s8, e8 = t(35, "salta"), t(41, "Hasta")
mock("v-b8-piedras", s8, e8, "piedras_modelo", {"at": [s8, t(38, "siguiente"), t(40, "modelo")]}, "partida",
     "La mascota (Higgsfield) salta de un modelo apagado al siguiente, que se enciende; la fila sigue fuera de cuadro.")
fx(s8, "whoosh-short", .5, "salto de la mascota")
fx(t(38), "pop", .55, "aterriza y el mosaico se enciende")
# b9 · CLÍMAX 1600 millones
s9, e9 = e8, t(46, "gratis")
mock("v-b9-tokens", s9, e9, "contador_tokens", {"at": [t(42, "1600"), t(43, "millones"), t(45, "tokens")]}, "grafico",
     "CLÍMAX: el contador corre a 1.600.000.000, crece hasta el ancho en «millones» y detrás se apila la montaña de fichas en «tokens».")
fx(s9, "riser", .35, "sube hacia el clímax")
for k in range(10):
    fx(t(42) + k * .11, "ping", .40, f"tick desbordado {k + 1}")
fx(t(43), "impact-bass-1", .6, "la cifra aterriza a todo el ancho")
# b10 · captura 1.62B
s10, e10 = e9, t(49, "2")
captura("v-b10-cap-tokens", s10, e10, "omni-tokens", "omniroute", "OmniRoute", [],
        "CAPTURA REAL: «~1.62B FREE TOKENS / MONTH» del README de OmniRoute, en «gratis al mes».")
# b11 · 2, Claude Mem
s11, e11 = e10, t(52, "memoria")
mock("v-b11-mem", s11, e11, "zocalo", {"variant": "enciende", "puestos": 1, "at": [s11, t(50, "Claude")]}, "partida",
     "Hueco 2 + neón de Claude Mem. Mismo gesto que OmniRoute.")
fx(t(50), "sparkle", .5, "trazo de neón del logo (motivo de la lista)")
# b12 · memoria entre sesiones
s12, e12 = e11, t(59, "Se")
mock("v-b12-terminales", s12, e12, "dos_terminales", {"at": [s12, t(55, "sesión"), t(58, "siguiente")]}, "grafico",
     "Dos terminales: el hilo de luz sale de la llena, la sesión se cierra y el hilo entra en la vacía y la llena.")
fx(t(55), "click", .5, "la sesión se cierra en seco")
fx(t(58), "whoosh", .4, "el hilo entra en la sesión nueva (medio segundo de nada antes)")
# b13 · captura Claude Mem
s13, e13 = e12, t(67, "No")
captura("v-b13-cap-mem", s13, e13, "mem-sesiones", "claudemem", "Claude Mem",
        [caja("mem-sesiones", 1, t(63, "proyectos") + .1, e13, 165, 506, 688, 66, s13)],
        "CAPTURA REAL: el README de Claude Mem; en «proyectos» la caja marca «preserves context across sessions… continuity of knowledge about projects».")
fx(t(63) + .1, "click-soft", .5, "la caja marca el párrafo")
# b14 · cara
cara(e13, 1.09)
# b15 · 3. Headroom
s15, e15 = t(72, "3"), t(74, "se")
mock("v-b15-headroom", s15, e15, "zocalo", {"variant": "enciende", "puestos": 2, "at": [s15, t(73, "Headroom")]}, "partida",
     "Hueco 3 + neón de Headroom.")
fx(t(73), "sparkle", .5, "trazo de neón del logo (motivo de la lista)")
# b16 · se pone en el medio
s16, e16 = e15, t(79, "entre")
mock("v-b16-cable", s16, e16, "cable_headroom", {"variant": "clavar", "at": [t(75, "pone"), t(78, "medio")]}, "partida",
     "El mosaico de Headroom baja en «pone» y se clava en el medio del cable en «medio».")
fx(t(78), "impact-bass-2", .45, "encastre en el cable")
# b17 · entre tú y el modelo
s17, e17 = e16, t(84, "comprime")
mock("v-b17-chat", s17, e17, "cable_headroom", {"variant": "chat", "at": [t(80, "tú"), t(83, "modelo")]}, "grafico",
     "La misma escena a lienzo: el chat a la izquierda en «tú», el modelo a la derecha en «modelo».")
fx(t(80), "pop", .45, "aparece el chat")
fx(t(83), "pop", .45, "aparece el modelo y el cable se cierra")
# b18 · comprime, corta lo que sobra
s18, e18 = e17, t(90, "solo")
mock("v-b18-prensa", s18, e18, "prensa", {"at": [s18, t(85, "corta"), t(88, "sobra")]}, "partida",
     "COMIC: la prensa aplasta el bloque de contexto en «comprime», los bordes se recortan en «corta» y caen en «sobra».")
fx(s18, "impact-bass-1", .45, "la prensa baja")
fx(t(85), "click", .5, "tijeretazo")
fx(t(88), "whoosh-short", .4, "los recortes caen")
# b19 · cara
cara(e18, 1.12)
# b20 · mismo resultado
s20, e20 = t(96, "Mismo"), t(98, "mucho")
mock("v-b20-salidas", s20, e20, "dos_salidas", {"at": [s20, t(97, "resultado")]}, "grafico",
     "Dos salidas idénticas con su check en «Mismo»; en «resultado» la pila de la derecha se desmorona.")
fx(s20, "chime", .45, "dos checks a la vez")
# b21 · captura Headroom
s21, e21 = e20, t(101, "4")
captura("v-b21-cap-head", s21, e21, "head-tokens", "headroom", "Headroom",
        [caja("head-tokens", 0, t(99, "menos"), e21, 198, 240, 516, 84, s21)],
        "CAPTURA REAL: la barra de Headroom 55.957 → 24.340 tokens; en «menos» la caja marca la barra y «57% fewer input tokens».")
fx(t(99), "click-soft", .5, "la caja marca la barra")
# b22 · 4. Claude Code Setup
s22, e22 = e21, t(105, "es")
mock("v-b22-setup", s22, e22, "zocalo", {"variant": "enciende", "puestos": 3, "at": [s22, t(102, "Claude")]}, "partida",
     "Hueco 4 + neón de Claude Code Setup.")
fx(t(102), "sparkle", .5, "trazo de neón del logo (motivo de la lista)")
# b23 · oficial de Anthropic
s23, e23 = e22, t(109, "revisa")
mock("v-b23-oficial", s23, e23, "sello_oficial", {"at": [t(106, "oficial"), t(108, "Anthropic")]}, "partida",
     "Insignia de verificado estampada en «oficial»; el logo de Anthropic con resplandor en «Anthropic».")
fx(t(106), "impact-bass-2", .4, "el sello se estampa")
fx(t(108), "sparkle", .35, "resplandor de Anthropic")
# b24 · revisa todo tu código
s24, e24 = e23, t(113, "y")
mock("v-b24-arbol", s24, e24, "arbol_escaneo", {"at": [s24, t(112, "código")]}, "grafico",
     "El árbol de un proyecto; la línea de luz lo barre desde «revisa» y los archivos se encienden en «código».")
fx(s24, "whoosh-cinematic", .3, "barrido de escáner")
# b25 · captura Setup: hooks, skills, subagentes
s25, e25 = e24, t(121, "hasta")
c25 = [caja("setup-lista", 0, t(117, "hooks"), t(118, "skills"), 372, 409, 442, 20, s25),
       caja("setup-lista", 0, t(118, "skills"), t(119, "subagentes"), 372, 386, 358, 19, s25),
       caja("setup-lista", 0, t(119, "subagentes"), e25, 372, 432, 450, 20, s25)]
captura("v-b25-cap-setup", s25, e25, "setup-lista", "claudecode", "Claude Code Setup", c25,
        "CAPTURA REAL: el README de Claude Code Setup; la caja salta a Hooks, Skills y Subagents en su palabra.")
for k, i in enumerate((117, 118, 119)):
    fx(t(i), "click-soft", .5, f"la caja salta a la categoría {k + 1}")
# b26 · servidores MCP (grafico) y aterrizan en el proyecto (partida)
s26, m26, e26 = e25, t(124, "le"), t(129, "y")
mock("v-b26-mcp", s26, m26, "servidor_mcp", {"variant": "conectar", "at": [t(122, "servidores"), t(123, "MCP")]}, "grafico",
     "El servidor se dibuja en «servidores» y en «MCP» salen tres líneas a tres servicios.")
fx(t(123), "click", .45, "las conexiones enganchan")
mock("v-b26b-mcp", m26, e26, "servidor_mcp", {"variant": "aterrizar", "at": [t(128, "proyecto")]}, "partida",
     "La misma escena en partida: las líneas aterrizan en el árbol del proyecto en «proyecto».")
fx(t(128), "click-soft", .5, "aterrizan y encajan")
# b27 · cara
cara(e26, 1.05)
# b28 · 5, Task Observer
s28, e28 = t(135, "Y"), t(139, "Mira")
mock("v-b28-task", s28, e28, "zocalo", {"variant": "enciende", "puestos": 4, "at": [t(136, "5"), t(137, "Task")]}, "partida",
     "Hueco 5: el zócalo queda completo; neón de Task Observer (marca GitHub: es una skill de un repo).")
fx(t(137), "sparkle", .6, "el mismo trazo de neón, cierra la lista")
# b29 · mira cómo trabaja
s29, e29 = e28, t(146, "Con")
mock("v-b29-cuaderno", s29, e29, "mascota_cuaderno", {"at": [s29, t(141, "trabaja"), t(145, "estilo")]}, "grafico",
     "La mascota asoma con el cuaderno en «Mira», el cursor repite la rutina en «trabaja» y los trazos forman una firma en «estilo».")
fx(t(141), "typing", .35, "garabateo siguiendo al cursor")
# b30 · captura Task Observer
s30, e30 = e29, t(152, "todo")
captura("v-b30-cap-task", s30, e30, "task-titulo", "github", "Task Observer",
        [caja("task-titulo", 0, t(148, "mejora"), e30, 347, 481, 700, 20, s30)],
        "CAPTURA REAL: el SKILL.md de Task Observer; en «mejora» la caja marca «the meta-skill that builds and improves all your skills».")
fx(t(148), "click-soft", .5, "la caja marca la frase")
# b31 · todo el tiempo, en segundo plano
s31, e31 = e30, t(158, "sin")
mock("v-b31-reloj", s31, e31, "reloj_fondo", {"at": [t(154, "tiempo"), t(157, "plano")]}, "grafico",
     "El reloj gira y las barras suben solas en «tiempo»; en «plano» la fila se va al fondo y delante queda la terminal.")
fx(t(154), "ping", .3, "tictac que se aleja")
# b32–b33 · cara
cara(e31, 1.09)
cara(t(162, "Si"), 1.12)
# b34 · la lista con los links (rima con el zócalo del gancho)
s34, e34 = t(168, "5"), CTA
mock("v-b34-lista", s34, e34, "zocalo", {"variant": "lista", "at": [s34, t(171, "link")]}, "partida",
     "LOOP: el zócalo se desarma en una lista con los cinco plugins en «5» y a cada fila se le engancha su link en «link».")
for k in range(5):
    fx(t(171) + k * .08, "click-soft", .45, f"engancha el link {k + 1}")

shots.sort(key=lambda s: s["at"])
visuals.sort(key=lambda v: v["start"])
keywords = ["Claude", "5", "plugins", "OmniRoute", "200", "gratis", "1600", "Mem", "memoria", "Headroom",
            "comprime", "tokens", "Setup", "Anthropic", "hooks", "skills", "MCP", "Task", "Observer",
            "estilo", "plano", "link"]
plan = {
    "_": "Pieza 5 — «No uses Claude Code hasta instalar estos 5 plugins». Plan del CUERPO en segundos del corte "
         f"(0 → {CTA}, donde arranca el CTA dicho a cámara en «comenta»). Lo escribe videos/5/armar-plan.py.",
    "_brief": "Brief de plan-edicion (Reels/plan-edicion/planes/2026-09-29-5.md) respetado beat a beat. Pedido de "
              "Ezequiel (2026-10-06): además, capturas REALES de cada plugin (sus grabaciones de pantalla) en la "
              "banda de arriba, donde la página dice lo mismo que se está diciendo; contador en +200 (lo que dice), no 358.",
    "_eje": "El zócalo de cinco huecos cruza el video: vacío en el gancho, cada plugin enciende su hueco con el MISMO "
            "gesto (neón + pastilla), y en el CTA se desarma en la lista con los links (loop).",
    "_fuente": "cuerpo.MOV 1080×1920 SDR bt709: sin LUT; cara topa en ×1,20.",
    "_mascota": "Sprites pixelados generados con Higgsfield (assets/mascota), regla de Ezequiel: lo generado, con Higgsfield.",
    "_fondos": "La propuesta anota claro/oscuro/comic por beat; el compilador aún no cambia el suelo por escena, "
               "así que la pieza va entera en `oscuro` y el comic lo da la trama de semitono.",
    "format": "REEL", "palette": "oscuro", "layout": {"mode": "formatos"}, "voice_gain": 0.7,
    "music": {"src": "assets/music/bed-tech.mp3", "fade_in": 1.0, "fade_out": 2.4, "target_mean": -34.0},
    "keywords": keywords, "shots": shots, "cards": [], "visuals": visuals, "sfx": sfx,
}
(PIEZA / "plan-cuerpo.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1))

# ── CTA de Instagram (dicho en el cuerpo, desde «comenta») ───────────────────
palabra = next(s for i, (s, _, w) in W.items() if i >= 175 and w.lower().startswith("plugins"))
cta = {
    "_": "CTA de Instagram dicho a cámara: «comenta plugins y te lo mando por privado». En segundos de la VERSIÓN, "
         f"desde {CTA}. Cierra en cara (trampa 6c: el último cuadro es la cara con PLUGINS puesta).",
    "_palabra": "La palabra es PLUGINS (la que se dice). Configurar el disparador de ManyChat con PLUGINS. La caja de "
                "comentarios en una esquina del brief no se dibuja: no hay visual de esquina sobre `full`, y la "
                "palabra ya la escribe `cta_palabra` (mismo criterio que la pieza 4).",
    "shots": [{"at": CTA, "kind": "full", "zoom": 1.09, "anchor": ANCHOR_FULL}],
    "visuals": [],
    "cta_palabra": {"texto": "PLUGINS", "desde": palabra, "hasta": None},
    "sfx": [[palabra, "pop", .6, "aterriza PLUGINS"]],
}
(PIEZA / "plan-cta-instagram.json").write_text(json.dumps(cta, ensure_ascii=False, indent=1))

# ── CTA de TikTok (el clip de la pieza 4: «Ve al link de la bio y encuentra el acceso.») ──
cta_tt = {
    "_": "CTA de TikTok: el clip cta-tiktok.mov de la pieza 4 (pedido de Ezequiel, 2026-10-06), «Ve al link de "
         f"la bio y encuentra el acceso.». En segundos de la VERSIÓN, desde {CTA}: el cuerpo se corta en «comenta» y "
         "la promesa «Si quieres la lista de los 5 plugins, el link de cada uno,» queda como parte común.",
    "_cara": "Cierra en cara, como Instagram: es otra toma (encuadre nuevo en el empalme) y no hay palabra clave "
             "que dibujar; «link de la bio» no se rotula (repetiría el subtítulo). La lista con los links ya se "
             "vio justo antes, en la parte común. Sin visual: el último cuadro es la cara (trampa 6c).",
    "shots": [{"at": CTA, "kind": "full", "zoom": 1.09, "anchor": ANCHOR_FULL}],
    "visuals": [],
    "sfx": [],
}
(PIEZA / "plan-cta-tiktok.json").write_text(json.dumps(cta_tt, ensure_ascii=False, indent=1))
print("✓ plan-cta-tiktok.json · cara desde", CTA)

# ── reparto ───────────────────────────────────────────────────────────────────
rep = {"cara": 0.0, "partida": 0.0, "grafico": 0.0}
nom = {"full": "cara", "band": "partida", "off": "grafico"}
seq = shots + [{"at": CTA, "kind": "full"}]
for a, b in zip(seq, seq[1:] + [{"at": DUR}]):
    rep[nom[a["kind"]]] += b["at"] - a["at"]
print(f"✓ plan-cuerpo.json · {len(visuals)} visuales · {len(shots)} encuadres · {len(sfx)} efectos · CTA {CTA}")
print("  reparto: " + " · ".join(f"{k} {v / DUR:.0%}" for k, v in rep.items()))
print(f"✓ plan-cta-instagram.json · PLUGINS en {palabra}")
