#!/usr/bin/env python3
"""Pieza 6 — escribe videos/6/plan-cuerpo.json, plan-cta-instagram.json y plan-cta-tiktok.json.

Los tiempos salen de `armar-version.py palabras` (línea del corte), por índice de palabra, y
cada índice se comprueba contra la palabra que se espera.

    .venv/bin/python videos/6/armar-plan.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIEZA = ROOT / "videos" / "6"
sys.path.insert(0, str(ROOT / "scripts"))
import mockups_chatgpt  # noqa: E402

ANCHOR_BAND = 0.535           # armar-version.py anchor: instagram [0.5076, 0.7572] · tiktok [0.5214, 0.7604]
ANCHOR_FULL = 0.46            # centroide de cara medido (46 % del alto)
CAP_TOP = 1400                # subtítulo bajo los gráficos a lienzo

# ── palabras (línea del corte) ────────────────────────────────────────────────
out = subprocess.run([sys.executable, str(ROOT / "scripts" / "armar-version.py"), "palabras",
                      "--piece", "6", "--plataforma", "instagram"],
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


def fin(i):
    return W[i][1]


# ── beats ─────────────────────────────────────────────────────────────────────
shots, visuals, sfx = [], [], []


def mock(vid, start, end, fn, kw, formato, nota):
    kw = dict(kw)
    if formato == "grafico":
        kw["lienzo"] = True
    v = {"id": vid, "role": "takeover", "kind": "mockup", "start": round(start, 3), "end": round(end, 3),
         "fade_in": 0.0, "fade_out": 0.0, "absolute_times": True, "_": nota, "mock": [fn, kw],
         "assets": mockups_chatgpt.assets_de(fn, kw)}
    if formato == "partida":
        v["band"] = "top"
        shots.append({"at": round(start, 3), "kind": "band", "anchor": ANCHOR_BAND})
    else:
        v["cap_top"] = CAP_TOP
        shots.append({"at": round(start, 3), "kind": "off"})
    visuals.append(v)


def cara(at, zoom):
    shots.append({"at": round(at, 3), "kind": "full", "zoom": zoom, "anchor": ANCHOR_FULL})


def fx(at, f, vol, nota):
    sfx.append([round(at, 3), f, vol, nota])


def chat(vid, start, end, comando, resultado, previo, foco, tecleo, envio, respuesta, nota, cursor=False):
    kw = {"variant": "enviar", "at": [foco, tecleo, envio, respuesta, end],
          "comando": comando, "resultado": resultado}
    if previo:
        kw["previo"] = previo
    if cursor:
        kw["cursor"] = True
    mock(vid, start, end, "chatgpt_chat", kw, "partida", nota)
    if tecleo < envio:
        fx(tecleo, "typing", .5, f"tecleo de {comando}")
    fx(envio, "click", .55, "clic de enviar")
    fx(respuesta, "whoosh-short", .3, "llega la respuesta: la imagen empieza a revelarse")


def resultado(vid, start, end, clave, comando, revelado, gesto, nota):
    mock(vid, start, end, "imagen_resultado",
         {"clave": clave, "comando": comando, "revelado": revelado, "at": [start, gesto]}, "grafico", nota)


# b1 · 0–1.7 s · «Estos códigos ocultos» — gancho en partida
e1 = t(3, "cambian")
mock("v-b1-oculto", 0.0, e1, "chatgpt_chat",
     {"variant": "oculto", "comando": "/blueprint", "at": [t(0, "Estos"), t(2, "ocultos")]}, "partida",
     "GANCHO: la ventana de ChatGPT con la foto del reloj ya adjunta desde el primer cuadro; en «ocultos» se "
     "descorre la banda negra que tapaba el comando a medio escribir.")
fx(t(2), "whoosh-short", .45, "la banda que se descorre y destapa el comando")

# b2 · «cambian tu imagen por completo» — parpadeo de tres estados a lienzo
e2 = t(8, "Mira")
mock("v-b2-parpadeo", e1, e2, "parpadeo_estados", {"at": [t(5, "imagen"), t(7, "completo")]}, "grafico",
     "Corte de patrón: el reloj a lienzo, un barrido de luz en «imagen» y en «completo» plano técnico, "
     "despiece y radiografía en un parpadeo; frena en la foto original.")
fx(t(5), "whoosh", .35, "el barrido de luz cruza la foto")
for k, dt in enumerate((0, .16, .30)):
    fx(t(7) + dt, "glitch-1", .45, f"golpe seco del estado {k + 1}")

# b3 · «Mira, pones este» — primer comando, /blueprint
s3, e3 = e2, round(t(12, "sale") - .04, 3)  # un frame antes: si cae justo en «sale», el bloque «pones este y sale» no se parte
chat("v-b3-blueprint", s3, e3, "/blueprint", "blueprint", None,
     foco=t(8, "Mira"), tecleo=t(9, "pones"), envio=t(10, "este"), respuesta=round(t(10) + .10, 3),
     cursor=True,
     nota="En «Mira» entra el cursor y hace clic en el campo; en «pones» se teclea /blueprint, en «este» se "
          "envía y la respuesta empieza a revelar la imagen como en ChatGPT.")
fx(t(8), "click-soft", .45, "el cursor se planta en el campo")

# b4 · «y sale este» — el plano técnico a lienzo
s4, e4 = e3, t(14, "cambias")
resultado("v-b4-blueprint", s4, e4, "blueprint", "/blueprint", "barrido", t(13, "este"),
          "En «sale» la imagen salta a pantalla completa terminando de revelarse; en «este» el barrido de luz.")
fx(s4, "chime", .5, "el plano técnico queda terminado")

# b5 · «Cambias el código, te» — /explodedview
s5, e5 = e4, t(18, "devuelve")
chat("v-b5-exploded", s5, e5, "/explodedview", "explodedview", "blueprint",
     foco=t(14, "cambias"), tecleo=t(15, "el"), envio=fin(16), respuesta=round(fin(16) + .08, 3),
     nota="La misma conversación (el plano asoma arriba): en «cambias» se enciende el campo con la foto otra "
          "vez adjunta, en «el código» se teclea /explodedview y se envía.")

# b6 · «devuelve este otro» — el despiece a lienzo
s6, e6 = e5, t(21, "y")
resultado("v-b6-exploded", s6, e6, "explodedview", "/explodedview", "despiece", t(19, "este"),
          "En «devuelve» el despiece a pantalla completa, las franjas se acomodan en su sitio.")
fx(s6, "impact-bass-2", .45, "las piezas se separan: golpe grave")

# b7 · «y con este» — /xray entra de un golpe (corte de patrón)
s7, e7 = e6, t(24, "así")
chat("v-b7-xray", s7, e7, "/xray", "xray", "explodedview",
     foco=t(21, "y"), tecleo=t(22, "con"), envio=t(23, "este"), respuesta=round(t(23) + .08, 3),
     nota="Corte de patrón: en «con» el comando entra entero de un golpe, sin tecleo; en «este» se envía.")
fx(t(22), "pop", .5, "el comando entra de un saque")

# b8 · «así queda» — la radiografía a lienzo
s8, e8 = e7, t(26, "Uno")
resultado("v-b8-xray", s8, e8, "xray", "/xray", "escaneo", t(25, "queda"),
          "En «así» la radiografía a pantalla completa; en «queda» la línea de escaneo sube.")
fx(s8, "sparkle", .5, "la luz atraviesa el reloj")

# b9 · «Uno más,» — único respiro, cara
cara(e8, 1.15)
s9 = t(28, "este")

# b10 · «este código,» — /handwritten, tecleo al doble de velocidad
e10 = t(30, "este")
chat("v-b10-handwritten", s9, e10, "/handwritten", "handwritten", "xray",
     foco=s9, tecleo=s9, envio=t(29, "código"), respuesta=round(t(29) + .10, 3),
     nota="El campo se enciende en «este» y /handwritten se teclea al doble de velocidad; en «código» se envía "
          "y la imagen se revela más despacio, en la pausa antes del clímax.")

# b11 · «este resultado.» — el clímax, el dibujo a mano a lienzo
s11, e11 = e10, t(32, "Si")
resultado("v-b11-handwritten", s11, e11, "handwritten", "/handwritten", "trazo", round(s11 + .7, 3),
          "CLÍMAX: el boceto a mano a pantalla completa, revelado como un trazo de izquierda a derecha.")
fx(s11, "whoosh-cinematic", .4, "el trazo que dibuja el boceto")
fx(t(31, "resultado"), "impact-bass-1", .4, "el boceto queda terminado")

# b12 · «Si quieres» — cara
cara(e11, 1.09)

# b13 · «todos los códigos ocultos en una sola lista,» — la lista con el quinto bajo candado
s13 = t(34, "todos")
mock("v-b13-lista", s13, CTA, "lista_codigos",
     {"at": [s13, t(36, "códigos"), t(37, "ocultos"), t(41, "lista")]}, "partida",
     "Los cuatro resultados bajan a una lista con su comando; en «ocultos» entra el quinto renglón borroso con "
     "candado (/stickynotes no se muestra nunca); en «lista» el borde los junta en una tarjeta.")
for k in range(4):
    fx(s13 + k * .08, "pop", .35, f"baja la miniatura {k + 1}")
fx(t(37), "key-press", .55, "el candado del quinto renglón")
fx(t(41), "whoosh-short", .35, "el borde cierra la tarjeta")

keywords = ["códigos", "ocultos", "imagen", "completo", "código", "resultado", "lista"]
plan = {
    "_": "Pieza 6 — «Escribes una palabra al lado de la foto y te la devuelve convertida». Plan del CUERPO en "
         f"segundos del corte (0 → {CTA}, donde arranca el CTA dicho a cámara en «comenta»). Lo escribe "
         "videos/6/armar-plan.py.",
    "_brief": "Brief de plan-edicion (Reels/plan-edicion/planes/2026-09-29-6.md) respetado en estructura y "
              "anclas. Pedido de Ezequiel (2026-10-07): el objeto es un Rolex (original.jpg) y los resultados "
              "son los reales de ChatGPT; el chat con el look real de ChatGPT tecleando cada comando, y en la "
              "palabra del resultado la imagen salta a pantalla completa. /stickynotes es el quinto, con candado.",
    "_fuente": "cuerpo.MOV 1080×1920 SDR bt709: sin LUT. El audio del MOV arranca 0,746 s después del video: "
               "out/6-fuente.mov lo rellena desde 0 y el transcript se corrió 746 ms.",
    "_fondos": "La propuesta anota claro/oscuro por beat; el compilador aún no cambia el suelo por escena, así "
               "que la pieza va entera en `oscuro` (ChatGPT en modo oscuro).",
    "_musica": "El brief pide cortar la música en «Uno más»: el compilador solo hace fundidos de entrada y "
               "salida, así que la cama sigue debajo.",
    "format": "REEL", "palette": "oscuro", "layout": {"mode": "formatos"}, "voice_gain": 0.7,
    "music": {"src": "assets/music/bed-tech.mp3", "fade_in": 1.0, "fade_out": 2.4, "target_mean": -34.0},
    "keywords": keywords, "shots": shots, "cards": [], "visuals": visuals, "sfx": sfx,
}
(PIEZA / "plan-cuerpo.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1))

# ── CTA de Instagram (dicho en el cuerpo, desde «comenta») ───────────────────
palabra = next(s for i, (s, _, w) in W.items() if i > 42 - 1 and s >= CTA and w.lower().startswith("códigos"))
cta = {
    "_": "CTA de Instagram dicho a cámara: «comenta códigos y te los mando por privado». En segundos de la "
         f"VERSIÓN, desde {CTA}. Cierra en cara (trampa 6c: el último cuadro es la cara con CÓDIGOS puesta).",
    "_palabra": "La palabra es CÓDIGOS (la que se dice). Configurar el disparador de ManyChat con CÓDIGOS. La caja "
                "de comentarios del brief no se dibuja: mismo criterio que las piezas 4 y 5.",
    "shots": [{"at": CTA, "kind": "full", "zoom": 1.09, "anchor": ANCHOR_FULL}],
    "visuals": [],
    "cta_palabra": {"texto": "CÓDIGOS", "desde": palabra, "hasta": None},
    "sfx": [[palabra, "pop", .6, "aterriza CÓDIGOS"]],
}
(PIEZA / "plan-cta-instagram.json").write_text(json.dumps(cta, ensure_ascii=False, indent=1))

# ── CTA de TikTok (el clip de la pieza 4: «Ve al link de la bio y encuentra el acceso.») ──
cta_tt = {
    "_": "CTA de TikTok: el clip cta-tiktok.mov de la pieza 4 (pedido de Ezequiel, 2026-10-07), «Ve al link de "
         f"la bio y encuentra el acceso.». En segundos de la VERSIÓN, desde {CTA}: el cuerpo se corta en «comenta» "
         "y la promesa «Si quieres todos los códigos ocultos en una sola lista,» queda como parte común.",
    "_cara": "Cierra en cara, como Instagram: es otra toma y no hay palabra clave que dibujar. Sin visual: el "
             "último cuadro es la cara (trampa 6c).",
    "shots": [{"at": CTA, "kind": "full", "zoom": 1.09, "anchor": ANCHOR_FULL}],
    "visuals": [],
    "sfx": [],
}
(PIEZA / "plan-cta-tiktok.json").write_text(json.dumps(cta_tt, ensure_ascii=False, indent=1))

# ── reparto ───────────────────────────────────────────────────────────────────
rep = {"cara": 0.0, "partida": 0.0, "grafico": 0.0}
nom = {"full": "cara", "band": "partida", "off": "grafico"}
seq = sorted(shots, key=lambda s: s["at"]) + [{"at": CTA, "kind": "full"}]
for a, b in zip(seq, seq[1:] + [{"at": DUR}]):
    rep[nom[a["kind"]]] += b["at"] - a["at"]
print(f"✓ plan-cuerpo.json · {len(visuals)} visuales · {len(shots)} encuadres · {len(sfx)} efectos · CTA {CTA}")
print("  reparto: " + " · ".join(f"{k} {v / DUR:.0%}" for k, v in rep.items()))
print(f"✓ plan-cta-instagram.json · CÓDIGOS en {palabra}")
print("✓ plan-cta-tiktok.json · cara desde", CTA)
