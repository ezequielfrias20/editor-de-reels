#!/usr/bin/env python3
"""Pieza 8 — escribe videos/8/plan-cuerpo.json, plan-cta-instagram.json y plan-cta-tiktok.json.

Los tiempos salen de `armar-version.py palabras` (línea del corte), por índice de palabra, y
cada índice se comprueba contra la palabra que se espera.

    .venv/bin/python videos/8/armar-plan.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIEZA = ROOT / "videos" / "8"
sys.path.insert(0, str(ROOT / "scripts"))
import mockups_codex  # noqa: E402

ANCHOR_BAND = 0.515           # armar-version.py anchor: instagram [0.4986, 0.7500] · tiktok [0.4966, 0.7520]
ANCHOR_FULL = 0.46            # centroide de cara medido (45.7 % del alto)
CAP_TOP = 1400                # subtítulo bajo los gráficos a lienzo

# ── palabras (línea del corte) ────────────────────────────────────────────────
out = subprocess.run([sys.executable, str(ROOT / "scripts" / "armar-version.py"), "palabras",
                      "--piece", "8", "--plataforma", "instagram"],
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
    if txt and not w.lower().strip("¿?.,:;").startswith(txt.lower()):
        raise SystemExit(f"palabra {i} es {w!r}, se esperaba {txt!r}")
    return s


# ── beats ─────────────────────────────────────────────────────────────────────
shots, visuals, sfx = [], [], []


def mock(vid, start, end, fn, kw, formato, nota):
    kw = dict(kw)
    if formato == "grafico":
        kw["lienzo"] = True
    v = {"id": vid, "role": "takeover", "kind": "mockup", "start": round(start, 3), "end": round(end, 3),
         "fade_in": 0.0, "fade_out": 0.0, "absolute_times": True, "_": nota, "mock": [fn, kw],
         "assets": mockups_codex.assets_de(fn, kw)}
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


# Sonidos que son HILO (brief): siempre el mismo archivo.
ENCASTRE = "impact-bass-2"    # el mosaico fusionado que encaja (gancho y «instala el plugin»)
MOTOR = "glitch-2"            # la barra trabada (traba) y la misma soltándose (destraba)
DERRUMBE = "impact-bass-1"    # las dos fallas de Codex, idénticas

# ── Beat 1 (gancho, oscuro) ───────────────────────────────────────────────────
# b1 · «Claude piensa» — partida
e = t(2, "Codex")
mock("v-b1-piensa", 0.0, e, "cc_gancho", {"variant": "piensa", "at": [t(0, "Claude"), t(1, "piensa")],
                                          "fondo": "oscuro"}, "partida",
     "GANCHO: la ventana de Claude Code ya encendida en el primer cuadro; en «Claude» se asoma el cangrejo, "
     "en «piensa» se infla el globo con el tablero de plan.")
fx(t(0), "click-soft", .35, "el cangrejo se asoma")
for k in range(3):
    fx(t(1) + .12 * k, "pop", .25, f"trazo {k + 1} del plan en el globo")

# b2 · «Codex ejecuta» — grafico
s, e = e, t(4, "y")
golpe2 = round(t(3, "ejecuta") + .32, 3)
mock("v-b2-ejecuta", s, e, "cc_gancho", {"variant": "ejecuta", "at": [t(2), t(3), golpe2], "fondo": "oscuro"},
     "grafico", "El tablero cae al piso de la ventana; en «Codex» entra el obrero con su caja; en «ejecuta» dos "
     "martillazos y el tablero queda bloque.")
fx(t(2), "whoosh-short", .35, "entra el obrero")
fx(t(3), "impact-bass-1", .5, "martillazo 1")
fx(golpe2, "impact-bass-1", .5, "martillazo 2: el bloque encastra")

# b3 · «y ahora los dos viven dentro de» — partida
s, e = e, t(11, "tu")
mock("v-b3-fusion", s, e, "cc_gancho", {"variant": "fusion", "at": [t(7, "dos"), t(8, "viven"), t(9, "dentro")],
                                        "fondo": "oscuro"}, "partida",
     "Los dos mosaicos entran de cada borde en «dos», se fusionan en «viven» y bajan a la barra en «dentro».")
fx(t(7), "pop", .4, "mosaico Claude")
fx(t(7) + .1, "pop", .4, "mosaico Codex")
fx(t(8), ENCASTRE, .5, "ENCASTRE (hilo): los dos se vuelven uno")

# b4 · «tu Claude Code» — grafico
s, e = e, t(14, "Te")
mock("v-b4-casa", s, e, "cc_gancho", {"variant": "casa", "at": [t(11), t(12, "Claude")], "fondo": "oscuro"},
     "grafico", "La ventana se abre a lienzo y el mosaico se posa en la barra de plugins; en «Claude Code» se "
     "enciende y los dos personajes se acomodan, uno por renglón.")
fx(t(11), "whoosh", .35, "la ventana se abre")
fx(t(12), "sparkle", .4, "el mosaico queda encendido")

# ── Beat 2 (problema, comic) ──────────────────────────────────────────────────
# b5 · «¿Te quedas sin plan de Claude» — partida
s, e = e, t(20, "antes")
mock("v-b5-medidor", s, e, "plan_medidor", {"variant": "vacia", "at": [t(16, "sin"), t(17, "plan"),
                                                                       t(19, "Claude")], "fondo": "comic"},
     "partida", "El medidor del plan se vacía en «sin»; la tarjeta del plan en «plan»; el cangrejo encogido y el "
     "logo en «Claude».")
fx(t(16), "riser", .25, "el aire que se escapa (la barra que se vacía)")
fx(t(19), "error", .3, "el cangrejo se encoge")

# b6 · «antes de fin de mes?» — grafico
s, e = e, t(25, "Eso")
mock("v-b6-calendario", s, e, "plan_medidor", {"variant": "calendario", "at": [t(22, "fin"), t(24, "mes")],
                                               "fondo": "comic"}, "grafico",
     "Las hojas del calendario pasan y frenan en el 15; el medidor toca el cero con polvo.")
fx(t(22), "whoosh-short", .35, "hojas que pasan")
fx(t(24), "impact-bass-2", .45, "frena en seco y el medidor llega a cero")

# b7 · «Eso se acabó.» — cara, sin nada
cara(e, 1.12)

# b8 · «Codex trabaja con tu cuenta de ChatGPT,» — grafico claro
s, e = t(28, "Codex"), t(35, "incluso")
mock("v-b8-enchufe", s, e, "cuenta_chatgpt", {"variant": "enchufe", "at": [t(28), t(29, "trabaja"),
                                                                           t(32, "cuenta"), t(34, "ChatGPT")],
                                              "fondo": "claro"}, "grafico",
     "El obrero vuelve con el cable colgando; se estira en «trabaja»; se enchufa en la tarjeta en «cuenta»; el "
     "logo y la luz por el cable en «ChatGPT».")
fx(t(32), "click", .5, "el cable se enchufa")
fx(t(34), "ping", .4, "la cuenta queda conectada y corre la luz")

# b9 · «incluso con la gratis. Instalarlo toma un minuto. En» — cara (dos encuadres)
cara(e, 1.09)
cara(t(39, "Instalarlo"), 1.15)

# ── Beat 3 (instalación, claro) ───────────────────────────────────────────────
# b11 · «Claude Code escribes 4 comandos:» — partida (empieza en «Claude»: el logo de la cabecera)
s, e = t(44, "Claude"), t(49, "uno")
mock("v-b11-comandos", s, e, "instalacion", {"variant": "comandos", "hechos": 0,
                                             "at": [t(44), t(47, "4"), t(48, "comandos")]}, "partida",
     "La ventana con su logo en «Claude»; cuatro renglones vacíos y el 0/4 en «4»; el primer comando entra "
     "borroso en «comandos».")
for k in range(4):
    fx(t(47) + .1 * k, "click-soft", .3, f"renglón {k + 1}")
fx(t(48), "whoosh-short", .3, "el comando entra barrido")

# b12 · «uno suma el catálogo oficial de OpenAI,» — grafico
s, e = e, t(56, "otro")
mock("v-b12-catalogo", s, e, "instalacion", {"variant": "catalogo", "hechos": 0,
                                             "at": [t(50, "suma"), t(52, "catálogo"), t(55, "OpenAI")]},
     "grafico", "La estantería se despliega en «suma», se llena en «catálogo», el logo de OpenAI y el 1/4 en "
     "«OpenAI».")
fx(t(50), "whoosh", .3, "la estantería se abre como acordeón")
for k in range(4):
    fx(t(52) + .14 * k, "pop", .22, f"mosaicos {2 * k + 1}–{2 * k + 2}")
fx(t(55), "chime", .45, "1/4")

# b13 · «otro instala el plugin,» — partida
s, e = e, t(60, "otro")
mock("v-b13-plugin", s, e, "instalacion", {"variant": "plugin", "hechos": 1,
                                           "at": [t(57, "instala"), t(59, "plugin")]}, "partida",
     "El mosaico fusionado vuela de la estantería a la barra en «instala» y encaja en «plugin»: 2/4.")
fx(t(57), "whoosh-short", .4, "el mosaico vuela")
fx(t(59), ENCASTRE, .5, "ENCASTRE (hilo): el plugin queda puesto")

# b14 · «otro recarga los comandos nuevos,» — grafico
s, e = e, t(65, "y")
mock("v-b14-recarga", s, e, "instalacion", {"variant": "recarga", "hechos": 2,
                                            "at": [t(61, "recarga"), t(63, "comandos"), t(64, "nuevos")]},
     "grafico", "El menú de comandos gira como rodillo; tres renglones nuevos en «comandos»; resaltados y 3/4 en "
     "«nuevos».")
fx(t(61), "whoosh", .3, "el rodillo gira")
for k in range(3):
    fx(t(63) + .12 * k, "pop", .3, f"comando nuevo {k + 1}")
fx(t(64), "chime", .45, "3/4")

# b15 · «y el último chequea que todo esté bien» — partida
s, e = e, t(73, "en")
mock("v-b15-chequeo", s, e, "instalacion", {"variant": "chequeo", "hechos": 3,
                                            "at": [t(68, "chequea"), t(70, "todo"), t(72, "bien")]}, "partida",
     "Baja la lista de verificación en «chequea»; tildes en «todo»; el último queda girando en «bien».")
for k, at in enumerate((t(68), t(70), t(70) + .25)):
    fx(at, "ping", .2 + .05 * k, f"tilde {k + 1}, sube de tono")

# b16 · «en tu ChatGPT.» — grafico OSCURO (el escalón más alto)
s, e = e, t(76, "Ahora")
mock("v-b16-conectada", s, e, "cuenta_chatgpt", {"variant": "conectada", "at": [t(74, "tu"), t(75, "ChatGPT")],
                                                 "fondo": "oscuro"}, "grafico",
     "Vira a oscuro: el ítem pendiente se tilda en «tu»; la tarjeta sube con «Conectado» y el 4/4 en «ChatGPT».")
fx(t(75), "whoosh-cinematic", .35, "resplandor de la cuenta conectada")
fx(t(75), "chime", .5, "4/4")

# ── Beat 4 (Codex trabajando) ─────────────────────────────────────────────────
# b17 · «Ahora Codex le pasa lo que más consume.» — cara
cara(e, 1.09)

# b18 · «Un comando para errores trabajados,» — partida comic
s, e = t(84, "Un"), t(89, "él")
mock("v-b18-traba", s, e, "error_trabado", {"variant": "traba", "at": [t(85, "comando"), t(87, "errores"),
                                                                       t(88, "trabajados")], "fondo": "comic"},
     "partida", "El comando borroso en «comando»; la tarjeta de error baja en «errores»; se encaja en la barra y "
     "la traba en «trabajados».")
fx(t(87), "error", .35, "la tarjeta de error")
fx(t(88), MOTOR, .4, "MOTOR (hilo): la barra trabada")

# b19 · «él investiga la causa y lo arregla.» — grafico OSCURO
s, e = e, t(96, "Otro")
mock("v-b19-lampara", s, e, "error_trabado", {"variant": "lampara", "at": [t(90, "investiga"), t(92, "causa"),
                                                                           t(95, "arregla")], "fondo": "oscuro"},
     "grafico", "A oscuras, el obrero barre la traza con la linterna; una línea en rojo en «causa»; en «arregla» "
     "golpea, la tarjeta se da vuelta a verde y la barra se suelta.")
fx(t(90), "whoosh-cinematic", .3, "el haz recorre la traza")
fx(t(92), "ping", .45, "la línea culpable")
fx(t(95), "impact-bass-1", .45, "el golpe y la barra que se suelta")

# b20 · «Otro revisa tus cambios sin modificar nada,» — partida
s, e = e, t(103, "y")
mock("v-b20-revisa", s, e, "revision_diff", {"variant": "revisa", "at": [t(97, "revisa"), t(99, "cambios"),
                                                                        t(101, "modificar"), t(102, "nada")]},
     "partida", "La lupa recorre el panel en «revisa»; verdes, rojos y notas en «cambios»; candado en «modificar»; "
     "el contador clavado en 0 en «nada».")
for k in range(3):
    fx(t(99) + .25 * k, "pop", .25, f"nota {k + 1}")
fx(t(101), "key-press", .5, "el candado cierra")

# b21 · «y otro cuestiona tu solución» — grafico
s, e = e, t(108, "antes")
mock("v-b21-cuestiona", s, e, "bloque_cuestiona", {"at": [t(105, "cuestiona"), t(107, "solución")]}, "grafico",
     "El obrero rodea el bloque con signos de pregunta en «cuestiona»; lo golpea y se abre por la junta en "
     "«solución».")
for k in range(3):
    fx(t(105) + .2 * k, "pop", .3, f"signo de pregunta {k + 1}")
fx(t(107), "glitch-1", .4, "la junta que cede")

# b22 · «antes de que la guardes. Y anótalo en tu CLAUDE.md así:» — cara (dos encuadres)
cara(e, 1.09)
cara(t(113, "Y"), 1.15)

# ── Beat 5 (el reparto en el CLAUDE.md) ───────────────────────────────────────
# b24 · «Claude planea, decide y controla lo que vuelve.» — grafico
s, e = t(119, "Claude"), t(127, "Codex")
mock("v-b24-claude", s, e, "claude_md", {"variant": "claude",
                                         "at": [t(119), t(120, "planea"), t(121, "decide"), t(123, "controla"),
                                                t(126, "vuelve")]}, "grafico",
     "El archivo a lienzo, el cangrejo en su renglón: plan en «planea», sello en «decide», lupa en «controla», "
     "la caja que sube en «vuelve».")
fx(t(120), "pop", .3, "el tablero de plan")
fx(t(121), "impact-bass-2", .4, "el sello")
fx(t(123), "whoosh-short", .3, "la lupa")
fx(t(126), "whoosh", .3, "la caja que sube")

# b25 · «Codex construye» — partida
s, e = e, t(129, "grandes")
mock("v-b25-codex", s, e, "claude_md", {"variant": "codex", "at": [t(127), t(128, "construye")]}, "partida",
     "Se enciende el segundo renglón en «Codex»; el obrero apila bloques en «construye».")
for k in range(4):
    fx(t(128) + .18 * k, "click", .3, f"bloque {k + 1}")

# b26 · «grandes cambios» — grafico
s, e = e, t(131, "y")
mock("v-b26-grandes", s, e, "revision_diff", {"variant": "grandes", "at": [t(129), t(130, "cambios")]},
     "grafico", "El obrero carga la pila al hombro mientras la cinta de cambios baja; el contador sube a 148 en "
     "«cambios».")
fx(t(130), "typing", .35, "el contador que repiquetea")

# b27 · «y destraba errores.» — partida comic (rima con b18)
s, e = e, t(134, "Si")
mock("v-b27-destraba", s, e, "error_trabado", {"variant": "destraba", "at": [t(132, "destraba"),
                                                                             t(133, "errores")], "fondo": "comic"},
     "partida", "LA MISMA barra trabada del b18: el obrero tira de la tarjeta en «destraba» y la barra corre.")
fx(s, MOTOR, .35, "MOTOR (hilo): el mismo motor trabado")
fx(t(132), "whoosh-short", .45, "el tirón: se suelta")

# b28 · «Si Codex falla 2 veces,» — grafico comic
s, e = e, t(139, "el")
mock("v-b28-fallas", s, e, "marcador_fallas", {"at": [t(136, "falla"), t(137, "2"), t(138, "veces")]},
     "grafico", "Derrumbe y cruz 1 en «falla»; el mismo derrumbe y cruz 2 en «2»; laten juntas en «veces».")
fx(t(136), DERRUMBE, .45, "DERRUMBE (hilo) 1")
fx(t(137), DERRUMBE, .45, "DERRUMBE (hilo) 2, idéntico")

# b29 · «el trabajo vuelve a Claude.» — partida
s, e = e, t(144, "No")
mock("v-b29-vuelve", s, e, "claude_md", {"variant": "vuelve", "at": [t(140, "trabajo"), t(141, "vuelve"),
                                                                     t(143, "Claude")]}, "partida",
     "La tarjeta de tarea se despega en «trabajo», sube en arco en «vuelve» y aterriza en el cangrejo en "
     "«Claude».")
fx(t(141), "whoosh", .35, "la tarea sube")
fx(t(143), "pop", .45, "llega a Claude")

# b30 · «No hay tercer intento. Así de simple. Si quieres» — cara (dos encuadres)
cara(e, 1.15)
cara(t(148, "Así"), 1.09)

# ── Beat 6 (clímax y CTA) ─────────────────────────────────────────────────────
# b32 · «el paso a paso con los comandos exactos» — partida, CLÍMAX
s, e = round(t(153, "el") - .04, 3), round(t(161, "y") - .04, 3)
mock("v-b32-enfoque", s, e, "instalacion", {"variant": "enfoque", "hechos": 0,
                                            "at": [t(154, "paso"), t(159, "comandos"), t(160, "exactos")]},
     "partida", "CLÍMAX: vuelven los cuatro comandos borrosos en «paso», la onda los recorre en «comandos» y "
     "entran en foco uno por uno en «exactos». Única vez que se leen.")
fx(t(159), "whoosh-cinematic", .3, "la onda que recorre")
for k in range(4):
    fx(t(160) + .22 * k, "click-soft", .45, f"enfoque {k + 1}")

# b33 · «y el reparto listo para pegar en tu CLAUDE.md,» — grafico
s = e
mock("v-b33-reparto", s, CTA, "claude_md", {"variant": "reparto", "at": [t(163, "reparto"), t(166, "pegar"),
                                                                         t(169, "CLAUDE.md")]}, "grafico",
     "El reparto se condensa en un bloque con botón de copiar en «reparto»; se copia y cae en un archivo vacío "
     "en «pegar»; la pestaña se nombra en «CLAUDE.md».")
fx(t(166), "click", .5, "copiar")
fx(t(166) + .3, "pop", .4, "la copia cae en su lugar")

keywords = ["piensa", "ejecuta", "plan", "gratis", "minuto", "comandos", "catálogo", "plugin", "nuevos",
            "consume", "causa", "nada", "solución", "CLAUDE.md", "construye", "2", "tercer", "exactos"]
plan = {
    "_": "Pieza 8 — «Codex dentro de Claude Code: Claude decide y Codex lo hace». Plan del CUERPO en segundos "
         f"del corte (0 → {CTA}, donde arranca el CTA dicho a cámara en «comenta»). Lo escribe "
         "videos/8/armar-plan.py.",
    "_brief": "Brief de plan-edicion (Reels/plan-edicion/planes/2026-10-08-1001.md) respetado en estructura, "
              "formatos y anclas. Ezequiel (2026-10-09): personajes de Higgsfield (assets/personajes-8/), "
              "interfaces recreadas, comandos legibles solo en el clímax.",
    "_cara": "Los momentos `cara` del brief con un visual «en una esquina» van a cara pelada: el formato cara no "
             "lleva visual encima (references/formatos.md), mismo criterio que las piezas 4–6.",
    "_fondos": "El compilador pinta el suelo `claro`; cada componente pinta su escena `oscuro` o `comic` con "
               "su propio suelo (spec 2026-10-09-pieza-8-componentes).",
    "_musica": "El brief pide cortes de música (en «Se acabó» y de «No hay tercer intento» a «Así de simple»): "
               "el compilador solo hace fundidos de entrada y salida, así que la cama sigue debajo.",
    "_fuente": "cuerpo.MOV 1080×1920 SDR: sin LUT. El audio arrancaba 83 ms tarde: out/8-fuente.mov lo rellena "
               "desde 0 (aresample first_pts=0).",
    "format": "REEL", "palette": "claro", "layout": {"mode": "formatos"}, "voice_gain": 0.7,
    "music": {"src": "assets/music/bed-tech.mp3", "fade_in": 1.0, "fade_out": 2.4, "target_mean": -34.0},
    "keywords": keywords, "shots": shots, "cards": [], "visuals": visuals, "sfx": sfx,
}
(PIEZA / "plan-cuerpo.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1))

# ── CTA de Instagram (dicho en el cuerpo, desde «comenta») ───────────────────
palabra = next(s for i, (s, _, w) in W.items() if s >= CTA and w.lower().startswith("plugin"))
cta = {
    "_": "CTA de Instagram dicho a cámara: «comenta plugin y te lo mando por privado». En segundos de la "
         f"VERSIÓN, desde {CTA}. Cierra en cara (trampa 6c: el último cuadro es la cara con PLUGIN puesta).",
    "_palabra": "La palabra es PLUGIN. Configurar el disparador de ManyChat con PLUGIN. La caja de comentarios "
                "del brief no se dibuja: el CTA va en cara, mismo criterio que las piezas 4–6.",
    "shots": [{"at": CTA, "kind": "full", "zoom": 1.09, "anchor": ANCHOR_FULL}],
    "visuals": [],
    "cta_palabra": {"texto": "PLUGIN", "desde": palabra, "hasta": None},
    "sfx": [[palabra, "pop", .6, "aterriza PLUGIN"]],
}
(PIEZA / "plan-cta-instagram.json").write_text(json.dumps(cta, ensure_ascii=False, indent=1))

# ── CTA de TikTok (cta_tiktok.MOV: «Ve al link de la bio y encuentra el acceso.») ──
cta_tt = {
    "_": "CTA de TikTok: el clip cta_tiktok.MOV de la carpeta 8, «Ve al link de la bio y encuentra el acceso.». "
         f"En segundos de la VERSIÓN, desde {CTA}: el cuerpo se corta en «comenta» y la promesa «Si quieres el "
         "paso a paso…» queda como parte común.",
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
largos = [(v["id"], round(v["end"] - v["start"], 2)) for v in visuals
          if "band" not in v and v["end"] - v["start"] > 3.2]
print(f"✓ plan-cuerpo.json · {len(visuals)} visuales · {len(shots)} encuadres · {len(sfx)} efectos · CTA {CTA}")
print("  reparto: " + " · ".join(f"{k} {v / DUR:.0%}" for k, v in rep.items()))
if largos:
    print("  ⚠ gráficos de más de 3,2 s:", largos)
print(f"✓ plan-cta-instagram.json · PLUGIN en {palabra}")
print("✓ plan-cta-tiktok.json · cara desde", CTA)
