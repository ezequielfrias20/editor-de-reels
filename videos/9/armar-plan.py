#!/usr/bin/env python3
"""Pieza 9 — escribe videos/9/plan-cuerpo.json, plan-cta-instagram.json y plan-cta-tiktok.json.

Los tiempos salen de `armar-version.py palabras` (línea del corte), por índice de palabra, y
cada índice se comprueba contra la palabra que se espera.

    .venv/bin/python videos/9/armar-plan.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIEZA = ROOT / "videos" / "9"
sys.path.insert(0, str(ROOT / "scripts"))
import mockups_davinci  # noqa: E402

ANCHOR_BAND = 0.5172          # armar-version.py anchor: instagram [0.5072, 0.7584] · tiktok [0.5054, 0.7584]
ANCHOR_FULL = 0.46            # centroide de cara medido (46.2 % del alto)
CAP_TOP = 1400                # subtítulo bajo los gráficos a lienzo

# ── palabras (línea del corte) ────────────────────────────────────────────────
out = subprocess.run([sys.executable, str(ROOT / "scripts" / "armar-version.py"), "palabras",
                      "--piece", "9", "--plataforma", "instagram"],
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
    kw["lienzo"] = formato == "grafico"      # explícito: hay componentes con lienzo=True por defecto
    v = {"id": vid, "role": "takeover", "kind": "mockup", "start": round(start, 3), "end": round(end, 3),
         "fade_in": 0.0, "fade_out": 0.0, "absolute_times": True, "_": nota, "mock": [fn, kw],
         "assets": mockups_davinci.assets_de(fn, kw)}
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


# Sonido v2 (Ezequiel, 2026-10-10: «muy duro», «algo más armonioso», y el motor trabado de
# 36–42 s le sonó feo): la paleta es SOLO de efectos cortos y blandos (pop, click-soft,
# whoosh, sparkle, chime). Fuera los golpes graves (impact-bass), los largos que sonaban
# enteros bajo la voz (riser 10 s, whoosh-cinematic 5,5 s), el typing y el glitch (vetado en
# build-composition.py). De 62 efectos a ~30, y la media de efectos 2 dB más abajo.
# Hilo que queda: el encastre del conector del MCP, siempre el mismo archivo.
ENCASTRE = "click-soft"       # el conector del MCP que encastra (gancho y «guía para conectarlo»)

# ── Beat 1 (gancho, oscuro) ───────────────────────────────────────────────────
# b1 · «DaVinci Resolve acaba de sacar» — partida
e = t(5, "su")
mock("v-b1-abre", 0.0, e, "dv_gancho", {"variant": "abre", "at": [t(0, "DaVinci"), t(1, "Resolve")],
                                        "fondo": "oscuro"}, "partida",
     "GANCHO: la ventana de DaVinci ya corriendo en el primer cuadro (cabezal y medidores); el nombre en "
     "«DaVinci», el mosaico con su pastilla en «Resolve».")
fx(t(1), "pop", .3, "se posa el mosaico de DaVinci")

# b2 · «su servidor MCP oficial.» — grafico
s, e = e, t(9, "Y")
mock("v-b2-mcp", s, e, "dv_gancho", {"variant": "mcp", "at": [t(6, "servidor"), t(7, "MCP"), t(8, "oficial")],
                                     "fondo": "oscuro"}, "grafico",
     "El costado se abre con un zócalo en «servidor»; el conector del MCP se dibuja en neón y encastra en "
     "«MCP»; el sello de verificado en «oficial».")
fx(t(6), "whoosh-short", .25, "el zócalo se desliza")
fx(t(7) + .35, ENCASTRE, .45, "ENCASTRE (hilo): el conector queda puesto")

# b3 · «Y sí, es el editor gratis que» — partida claro
s, e = e, t(16, "pelea")
mock("v-b3-precio", s, e, "dv_precio", {"at": [t(13, "editor"), t(14, "gratis")], "fondo": "claro"}, "partida",
     "La ventana se encoge al mosaico en «editor»; cuelga la etiqueta y el precio rueda a 0 en «gratis».")
fx(t(14) + .7, "chime", .3, "toca el cero")

# b4 · «pelea de igual a igual con Premiere Pro.» — grafico claro
s, e = e, t(24, "Traducido")
mock("v-b4-balanza", s, e, "dv_balanza", {"at": [t(16), t(18, "igual"), t(22, "Premiere"), t(23, "Pro")],
                                          "fondo": "claro"}, "grafico",
     "DaVinci cae a un plato en «pelea»; el travesaño busca nivel en «igual»; Premiere cae al otro en "
     "«Premiere»; frena en seco horizontal en «Pro».")
fx(t(23), "click-soft", .4, "el empate se fija")

# b5 · «Traducido: Claude ya puede editarte los vídeos.» — cara (dos encuadres)
cara(e, 1.09)
cara(t(25, "Claude"), 1.15)

# ── Beat 2 (comic → oscuro) ───────────────────────────────────────────────────
# b6 · «Y no hablamos de ponerle subtítulos y» — partida comic
s, e = t(31, "Y"), t(38, "cortar")
mock("v-b6-subtitulos", s, e, "dv_linea", {"variant": "subtitulos", "at": [t(35, "ponerle"), t(36, "subtítulos")],
                                           "fondo": "comic"}, "partida",
     "Las pistas se apagan hasta quedar una flaca y cae la tira de subtítulos en «ponerle»; sus palabras se "
     "llenan en «subtítulos».")

# b7 · «cortar 4 veces,» — grafico comic
s, e = e, t(41, "hablamos")
mock("v-b7-tijeras", s, e, "dv_linea", {"variant": "tijeras", "at": [t(38), t(39, "4"), t(40, "veces")],
                                        "fondo": "comic"}, "grafico",
     "Primer tijeretazo en «cortar»; tres más y el contador a 4 en «4»; queda el muñón en «veces».")
fx(t(38), "click-soft", .28, "tijeretazo 1")
for k in range(3):
    fx(t(39) + .18 * k, "click-soft", .28, f"tijeretazo {k + 2}")

# b8 · «hablamos de edición de nivel de producción.» — partida oscuro
s, e = e, t(48, "Lo")
mock("v-b8-produccion", s, e, "dv_linea", {"variant": "produccion",
                                           "at": [t(43, "edición"), t(45, "nivel"), t(47, "producción")],
                                           "fondo": "oscuro"}, "partida",
     "El muñón se estira a línea de tiempo entera en «edición»; las pistas se apilan en «nivel»; ruedas, "
     "osciloscopio y nodos se encienden en «producción».")
fx(t(43), "whoosh", .25, "el muñón se estira")
fx(t(47), "sparkle", .3, "el panel entero se enciende")

# b9 · «Lo enchufas a Claude Code o a Codex» — grafico claro
s, e = e, t(56, "y")
mock("v-b9-enchufe", s, e, "dv_enchufe", {"at": [t(49, "enchufas"), t(51, "Claude"), t(55, "Codex")],
                                          "fondo": "claro"}, "grafico",
     "Del conector brotan dos cables en «enchufas»; uno enchufa en Claude Code y el otro en Codex.")
fx(t(51), "click-soft", .4, "enchufe Claude Code")
fx(t(55), "click-soft", .4, "enchufe Codex")

# b10 · «y maneja la línea de tiempo hablándole.» — cara
cara(e, 1.12)

# ── Beat 3 (la lista, claro) ──────────────────────────────────────────────────
# b11 · «Le pides lo que necesites,» — partida
s, e = t(63, "Le"), t(68, "que")
mock("v-b11-pedido", s, e, "dv_pedido", {"at": [t(64, "pides"), t(67, "necesites")], "fondo": "claro"}, "partida",
     "La onda de voz se vuelve la burbuja del pedido, borrosa, en «pides»; cuatro burbujas vacías detrás en "
     "«necesites».")
fx(t(64), "pop", .3, "la burbuja del pedido")

# b12 · «que corrige el color,» — grafico
s, e = e, t(72, "que")
mock("v-b12-color", s, e, "dv_color", {"at": [t(69, "corrige"), t(71, "color")], "fondo": "claro"}, "grafico",
     "La página Color: el cangrejo gira las ruedas en «corrige»; la línea barre el clip gris y deja el color "
     "en «color».")
fx(t(71), "whoosh", .25, "el barrido de color")

# b13 · «que arme gráficos en movimiento,» — partida
s, e = e, t(77, "que")
mock("v-b13-graficos", s, e, "dv_graficos", {"at": [t(73, "arme"), t(74, "gráficos"), t(76, "movimiento")],
                                             "fondo": "claro"}, "partida",
     "Pista nueva en «arme»; la forma se arma en «gráficos»; rombos, curva y movimiento en «movimiento».")
for k in range(2):
    fx(t(76) + .24 * k, "pop", .2, f"fotogramas clave {2 * k + 1}–{2 * k + 2}")

# b14 · «que corte en multicámara,» — grafico
s, e = e, t(81, "que")
mock("v-b14-multicam", s, e, "dv_multicam", {"at": [t(78, "corte"), t(80, "multicámara")], "fondo": "claro"},
     "grafico", "Rejilla de cuatro ángulos en «corte»; el marco salta 4 veces y clava cortes en «multicámara».")
for k in range(4):
    fx(t(80) + .22 * k, "click-soft", .22, f"salto de ángulo {k + 1}")

# b15 · «que meta efectos de sonido o» — partida
s, e = e, t(87, "que")
mock("v-b15-sonido", s, e, "dv_sonido", {"at": [t(82, "meta"), t(83, "efectos"), t(85, "sonido")],
                                         "fondo": "claro"}, "partida",
     "Pista de audio nueva en «meta»; caen tres bloques en «efectos»; dibujan su onda en «sonido».")
fx(t(85), "whoosh-short", .3, "efecto 1")
fx(t(85) + .16, "pop", .3, "efecto 2")
fx(t(85) + .32, "sparkle", .3, "efecto 3")

# b16 · «que calce la música con el montaje.» — grafico oscuro
s, e = e, t(94, "Te")
mock("v-b16-musica", s, e, "dv_musica", {"at": [t(88, "calce"), t(90, "música"), t(93, "montaje")],
                                         "fondo": "oscuro"}, "grafico",
     "La música se estira en «calce»; marcadores de compás en «música»; los picos caen en los cortes y la "
     "línea late en «montaje».")
fx(t(93), "chime", .3, "calza: la línea late")

# ── Beat 4 (el pozo) ──────────────────────────────────────────────────────────
# b17 · «¿Te falta un plano entre dos escenas?» — partida comic
s, e = e, t(101, "Se")
mock("v-b17-pozo", s, e, "dv_pozo", {"at": [t(95, "falta"), t(97, "plano"), t(99, "dos"), t(100, "escenas")],
                                     "fondo": "comic"}, "partida",
     "El clip salta fuera en «falta»; parpadea el cuadro vacío en «plano»; los vecinos se separan en «dos»; "
     "el cabezal tropieza y queda trabado en «escenas».")
fx(t(95), "whoosh-short", .25, "el clip salta")
fx(t(100), "click-soft", .25, "el cabezal tropieza en el pozo")

# b18 · «Se lo pides» — cara
cara(e, 1.12)

# b19 · «y Claude lo genera» — grafico oscuro
s, e = t(104, "y"), t(108, "y")
mock("v-b19-genera", s, e, "dv_genera", {"at": [t(105, "Claude"), t(107, "genera")], "fondo": "oscuro"}, "grafico",
     "El cangrejo se asoma al cuadro vacío en «Claude»; lo pinta y el plano resuelve del ruido en «genera».")
fx(t(107) + 1.0, "sparkle", .3, "el plano queda nítido")

# b20 · «y lo deja puesto en la línea de tiempo,» — partida claro
s, e = e, t(117, "siempre")
mock("v-b20-encastra", s, e, "dv_encastra", {"at": [t(110, "deja"), t(111, "puesto"), t(116, "tiempo")],
                                             "fondo": "claro"}, "partida",
     "El plano baja al pozo en «deja»; encastra y los vecinos se cierran en «puesto»; el cabezal cruza libre "
     "en «tiempo».")
fx(t(111), "click-soft", .4, "encastre del plano")
fx(t(116), "whoosh", .22, "el cabezal corre libre")

# b21 · «siempre que lo tengas conectado» — cara
cara(e, 1.09)

# b22 · «a algo que genere imágenes, como Higgsfield.» — partida oscuro
s, e = t(122, "a"), t(129, "Tú")
mock("v-b22-higgsfield", s, e, "dv_higgsfield", {"at": [t(123, "algo"), t(125, "genere"), t(126, "imágenes"),
                                                        t(128, "Higgsfield")], "fondo": "oscuro"}, "partida",
     "El tercer cable se enchufa en «algo»; el mosaico se enciende en «genere»; viajan las imágenes en "
     "«imágenes»; el logo se estampa en «Higgsfield».")
fx(t(123), "click-soft", .35, "el tercer cable hace clic")
fx(t(128), "sparkle", .3, "el logo se estampa con resplandor")

# ── Beat 5 (cierre y CTA) ─────────────────────────────────────────────────────
# b23 · «Tú decides qué quieres» — cara
cara(e, 1.15)

# b24 · «y él lo hace dentro del editor.» — grafico claro
s, e = t(133, "y"), t(140, "Si")
mock("v-b24-editor", s, e, "dv_editor", {"at": [t(136, "hace"), t(137, "dentro"), t(139, "editor")],
                                         "fondo": "claro"}, "grafico",
     "El cangrejo arrastra el cabezal y las pistas se completan en «hace»; la cámara entra al panel en "
     "«dentro»; el mosaico de DaVinci se enciende en «editor».")
fx(t(139), "sparkle", .28, "todo puesto")

# b25 · «Si quieres la guía para conectarlo» — partida
s, e = e, t(146, "y")
mock("v-b25-guia", s, e, "dv_guia", {"variant": "despliega", "at": [t(143, "guía"), t(145, "conectarlo")],
                                     "fondo": "claro"}, "partida",
     "La hoja de guía se despliega en «guía»; el conector del MCP encastra en el primer renglón en "
     "«conectarlo».")
fx(t(143), "whoosh", .22, "despliegue de acordeón")
fx(t(145) + .25, ENCASTRE, .45, "ENCASTRE (hilo): el mismo conector del gancho")

# b26 · «y los pedidos exactos que le hago,» — partida, CLÍMAX
s = e
mock("v-b26-pedidos", s, CTA, "dv_guia", {"variant": "pedidos",
                                          "at": [t(148, "pedidos"), t(149, "exactos"), t(152, "hago")],
                                          "fondo": "claro"}, "partida",
     "CLÍMAX: las seis burbujas borrosas se apilan en «pedidos», la onda las recorre y entran en foco una por "
     "una en «exactos»; se juntan con la guía en «hago». Única vez que se leen.")
fx(t(149), "whoosh", .22, "la onda que recorre")
for k in range(3):
    fx(t(149) + .15 + .32 * k, "click-soft", .2, f"enfoque {2 * k + 1}–{2 * k + 2}")

keywords = ["MCP", "oficial", "gratis", "igual", "subtítulos", "4", "producción", "Codex", "hablándole",
            "color", "movimiento", "multicámara", "sonido", "montaje", "plano", "genera", "Higgsfield",
            "editor", "exactos"]
plan = {
    "_": "Pieza 9 — «DaVinci Resolve abrió su MCP: Claude te edita los videos». Plan del CUERPO en segundos "
         f"del corte (0 → {CTA}, donde arranca el CTA dicho a cámara en «comenta»). Lo escribe "
         "videos/9/armar-plan.py.",
    "_brief": "Brief de plan-edicion (Reels/plan-edicion/planes/2026-10-09-1009.md) respetado en estructura, "
              "formatos y anclas. Ezequiel (2026-10-10): DaVinci recreado y animado, miniaturas de su propio "
              "video, cangrejo y plano generados con Higgsfield, pedidos legibles solo en el clímax.",
    "_cara": "Los momentos `cara` del brief con un visual «en una esquina» van a cara pelada: el formato cara no "
             "lleva visual encima. Tres momentos cambian de formato para que el hilo se vea: «Le pides lo que "
             "necesites» (la primera burbuja) y «lo deja puesto en la línea de tiempo» (el pozo que se cierra) "
             "van en partida; «¿Te falta un plano entre dos escenas?» es un solo tramo partida (0,66 s no da "
             "para dos formatos y dejaría 4 s de gráfico seguido).",
    "_fondos": "El compilador pinta el suelo `claro`; cada componente pinta su escena `oscuro` o `comic`.",
    "_musica": "El brief pide que la música se desarme y se corte (beat 2 y el pozo): el compilador solo hace "
               "fundidos de entrada y salida, así que la cama sigue debajo.",
    "_fuente": "cuerpo.MOV 1080×1920 SDR: sin LUT. El audio arrancaba 93 ms tarde: out/9-fuente.mov lo rellena "
               "desde 0 (aresample first_pts=0).",
    "format": "REEL", "palette": "claro", "layout": {"mode": "formatos"}, "voice_gain": 0.7,
    "sfx_target_mean": -29.0,
    "music": {"src": "assets/music/bed-tech.mp3", "fade_in": 1.0, "fade_out": 2.4, "target_mean": -34.0},
    "keywords": keywords, "shots": shots, "cards": [], "visuals": visuals, "sfx": sfx,
}
(PIEZA / "plan-cuerpo.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1))

# ── CTA de Instagram (dicho en el cuerpo, desde «comenta») ───────────────────
palabra = next(s for i, (s, _, w) in W.items() if s >= CTA and w.lower().startswith("montaje"))
cta = {
    "_": "CTA de Instagram dicho a cámara: «comenta montaje y te lo mando por privado». En segundos de la "
         f"VERSIÓN, desde {CTA}. Cierra en cara (el último cuadro es la cara con MONTAJE puesta).",
    "_palabra": "La palabra es MONTAJE. Configurar el disparador de ManyChat con MONTAJE. La caja de "
                "comentarios del brief no se dibuja: el CTA va en cara, mismo criterio que las piezas 4–8.",
    "shots": [{"at": CTA, "kind": "full", "zoom": 1.09, "anchor": ANCHOR_FULL}],
    "visuals": [],
    "cta_palabra": {"texto": "MONTAJE", "desde": palabra, "hasta": None},
    "sfx": [[palabra, "pop", .4, "aterriza MONTAJE"]],
}
(PIEZA / "plan-cta-instagram.json").write_text(json.dumps(cta, ensure_ascii=False, indent=1))

# ── CTA de TikTok (cta_tiktok.MOV de la pieza 8: «Ve al link de la bio y encuentra el acceso.») ──
cta_tt = {
    "_": "CTA de TikTok: el clip cta_tiktok.MOV de la carpeta 8 (copiado a la 9), «Ve al link de la bio y "
         f"encuentra el acceso.». En segundos de la VERSIÓN, desde {CTA}: el cuerpo se corta en «comenta» y la "
         "promesa «Si quieres la guía…» queda como parte común.",
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
print(f"✓ plan-cta-instagram.json · MONTAJE en {palabra}")
print("✓ plan-cta-tiktok.json · cara desde", CTA)
