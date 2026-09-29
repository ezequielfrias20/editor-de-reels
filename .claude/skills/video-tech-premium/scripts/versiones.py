#!/usr/bin/env python3
"""Una VERSIÓN de una pieza = el cuerpo seguido del CTA de una plataforma, en una sola
línea de tiempo. Su id es `<n>-<plataforma>` (`7-instagram`) y se comporta como una pieza
más: `transcripts/7-instagram.json`, `cuts/7-instagram.json`, `videos/7-instagram/`.

Siempre salen dos, `instagram` y `tiktok` (decisión de Ezequiel, 2026-09-27). El cuerpo
suele cerrar con el CTA de Instagram dicho a cámara («comenta PARALELO y te lo mando por
privado»); `videos/<n>/cta-cuerpo.json` anota en qué palabra empieza. Cada versión toma el
cuerpo HASTA esa palabra (la parte común) y le suma su CTA:

    instagram   el clip de CTA de Instagram si se subió; si no, el que se dijo en el cuerpo
    tiktok      el clip de CTA de TikTok si se subió; si no, nada (el «comenta…» no sirve ahí)

La parte común va PRIMERO, así que sus índices de palabra y sus segundos son los mismos en
todas las versiones y su EDL o su plan se reusa tal cual. El EDL del CTA
(`videos/<n>/cta-<p>.json`) se escribe con índices relativos al CTA (0..C-1) y aquí se
desplaza al final.
"""
from __future__ import annotations

import copy
import re
import unicodedata

# Todos los campos de un evento del EDL que guardan un índice de palabra (edl_schema).
INDICES_EVENTO = ("atWord", "untilWord", "ctaAtWord")


def version_id(n: int | str, plataforma: str) -> str:
    return f"{n}-{plataforma}"


def unir_transcripts(cuerpo: dict, cta: dict | None, offset: float) -> dict:
    """Palabras del cuerpo + las del CTA corridas `offset` segundos (AssemblyAI usa ms)."""
    out = copy.deepcopy(cuerpo)
    if cta is None:
        return out
    off = round(offset * 1000)
    out["words"] = out["words"] + [{**w, "start": w["start"] + off, "end": w["end"] + off}
                                   for w in cta["words"]]
    out["text"] = f"{cuerpo.get('text', '')} {cta.get('text', '')}".strip()
    out["utterances"] = None  # nadie las lee y desplazarlas a medias sería peor
    if cuerpo.get("audio_duration") is not None and cta.get("audio_duration") is not None:
        out["audio_duration"] = cuerpo["audio_duration"] + cta["audio_duration"]
    return out


def unir_cortes(cuerpo: dict, cta: dict | None, offset: float) -> dict:
    if cta is None:
        return copy.deepcopy(cuerpo)

    def correr(xs):
        return [{**x, "start": round(x["start"] + offset, 3), "end": round(x["end"] + offset, 3)}
                for x in xs]

    return {
        "source_duration": round(offset + cta["source_duration"], 3),
        "final_duration": round(cuerpo["final_duration"] + cta["final_duration"], 3),
        "removed": round(cuerpo["removed"] + cta["removed"], 3),
        "cuts": copy.deepcopy(cuerpo["cuts"]) + correr(cta["cuts"]),
        "keeps": copy.deepcopy(cuerpo["keeps"]) + correr(cta["keeps"]),
    }


# ── el CTA de Instagram dicho en el cuerpo ─────────────────────────────────────

def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", t)).strip()


def leer_cta_cuerpo(dato: dict, palabras: list[dict]) -> int | None:
    """`{"desde_palabra": k, "texto": "…"}` → k, o None si el cuerpo no dice CTA. El texto
    tiene que ser EXACTAMENTE la cola del cuerpo desde k: un CTA que no llega al final dejaría
    su resto pegado delante del CTA de TikTok."""
    if "desde_palabra" not in dato:
        raise ValueError('falta "desde_palabra" (null si el cuerpo no dice CTA)')
    k = dato["desde_palabra"]
    if k is None:
        return None
    if not isinstance(k, int) or not 0 < k < len(palabras):
        raise ValueError(f"palabra {k} fuera del cuerpo: el CTA empieza entre la 1 y la "
                         f"{len(palabras) - 1}")
    antes = palabras[k - 1]["text"].strip()
    if not antes.endswith((".", "?", "!", "…")):
        raise ValueError(f"el cuerpo quedaría cortado a mitad de frase, en «{antes}»: el CTA "
                         f"empieza al principio de su oración («Si quieres …, comenta …»)")
    cola = " ".join(w["text"] for w in palabras[k:])
    if normalizar(cola) != normalizar(dato.get("texto", "")):
        raise ValueError(f"desde la palabra {k} el cuerpo dice «{cola}», no "
                         f"«{dato.get('texto', '')}»: el CTA tiene que ser el final del cuerpo")
    return k


def recortar_cuerpo(tr: dict, cortes: dict, k: int | None) -> tuple[dict, dict]:
    """El cuerpo hasta la palabra k (sin ella). Corta en medio del silencio que la precede,
    con 300 ms de aire como mucho después de la última palabra que queda."""
    if k is None:
        return copy.deepcopy(tr), copy.deepcopy(cortes)
    w = tr["words"]
    fin_ant, ini_cta = w[k - 1]["end"] / 1000, w[k]["start"] / 1000
    t = round(min((fin_ant + ini_cta) / 2, fin_ant + 0.3), 3)

    def hasta(xs):
        out = []
        for x in xs:
            if x["start"] >= t:
                continue
            e = min(x["end"], t)
            out.append({**x, "end": e, "dur": round(e - x["start"], 3)})
        return out

    tr_out = copy.deepcopy(tr)
    tr_out["words"] = copy.deepcopy(w[:k])
    tr_out["text"] = " ".join(x["text"] for x in w[:k])
    tr_out["utterances"] = None
    keeps = hasta(cortes["keeps"])
    final = round(sum(x["dur"] for x in keeps), 3)
    cu_out = {**copy.deepcopy(cortes), "keeps": keeps, "cuts": hasta(cortes["cuts"]),
              "final_duration": final, "removed": round(cortes["source_duration"] - final, 3)}
    return tr_out, cu_out


def desplazar_segmento(seg: dict, k: int) -> dict:
    s = copy.deepcopy(seg)
    s["words"] = [s["words"][0] + k, s["words"][1] + k]
    for ev in s.get("events", []):
        for key in INDICES_EVENTO:
            if key in ev:
                ev[key] += k
        if ev.get("words"):
            ev["words"] = [ev["words"][0] + k, ev["words"][1] + k]
    return s


def _rango(segs: list[dict], n: int, que: str) -> None:
    if not segs:
        raise ValueError(f"el EDL {que} no tiene segmentos")
    a, b = segs[0]["words"][0], segs[-1]["words"][1]
    if a != 0:
        raise ValueError(f"el EDL {que} tiene que empezar en la palabra 0 y empieza en {a}")
    if b != n - 1:
        raise ValueError(f"el EDL {que} tiene que terminar en la palabra {n - 1} "
                         f"(su transcript tiene {n}) y termina en {b}")


def unir_edl(cuerpo_edl: dict, cta_segmentos: list[dict], palabras_cuerpo: int,
             palabras_cta: int, pieza: str, words_rel: str, cuts_rel: str,
             fingerprint: str) -> dict:
    _rango(cuerpo_edl["segments"], palabras_cuerpo, "del cuerpo")
    if palabras_cta:
        _rango(cta_segmentos, palabras_cta, "del CTA")
    edl = copy.deepcopy(cuerpo_edl)
    edl["piece"] = pieza
    edl["transcript"] = {"words": words_rel, "cuts": cuts_rel, "fingerprint": fingerprint}
    edl["segments"] = edl["segments"] + [desplazar_segmento(s, palabras_cuerpo)
                                         for s in cta_segmentos]
    return edl


# ── el camino del plan.json ────────────────────────────────────────────────────
# El compilador del EDL solo emite stages a lienzo completo: la banda de arriba del
# triband (tool_card, mockups con `band: "top"`) se escribe a mano en plan.json (§2, paso 9).
# El plan del cuerpo va en segundos del corte del cuerpo, que son los mismos en todas las
# versiones. El del CTA va YA en segundos de la versión (arranca en `final_duration` de
# `cuts/<n>.json`): los mockups guardan tiempos dentro de `mock` y ninguna función puede
# desplazarlos sin saber cuáles son, así que unir es concatenar.

LISTAS_PLAN = ("shots", "visuals", "sfx", "cards", "keywords")
TOL = 0.0005


def _tiempos(clave: str, x) -> tuple[float, float | None]:
    """(inicio, fin) de un elemento del plan; `fin` None si no tiene."""
    if clave == "shots":
        return x["at"], None
    if clave == "sfx":
        return x[0], None
    if clave in ("visuals", "cards"):
        return x["start"], x.get("end")
    return 0.0, None                      # keywords: texto, sin tiempo


def unir_plan(cuerpo: dict, cta: dict | None, fin_cuerpo: float) -> dict:
    for que, p in (("del cuerpo", cuerpo), ("del CTA", cta or {})):
        if "captions" in p:
            raise ValueError(f"el plan {que} declara `captions`: sácalos, build-composition.py "
                             f"trocea solo el cuerpo y el CTA")
    if cta is None:
        return copy.deepcopy(cuerpo)
    otras = [k for k in cta if k not in LISTAS_PLAN and k != "cta_palabra" and not k.startswith("_")]
    if otras:
        raise ValueError(f"el plan del CTA solo lleva {', '.join(LISTAS_PLAN)} y cta_palabra; "
                         f"{', '.join(otras)} va en plan-cuerpo.json")
    if "cta_palabra" in cta:
        desde = float(cta["cta_palabra"].get("desde", -1))
        if desde < fin_cuerpo - TOL:
            raise ValueError(f"cta_palabra del CTA empieza en {desde:.3f}, antes de que acabe el "
                             f"cuerpo ({fin_cuerpo:.3f}): va en segundos de la versión")
    for clave in LISTAS_PLAN[:-1]:
        for x in cuerpo.get(clave, []):
            ini, fin = _tiempos(clave, x)
            if clave in ("visuals", "cards") and fin is None:
                raise ValueError(f"{clave} del cuerpo sin `end` ({x.get('id', ini)}): llegaría "
                                 f"hasta el final del CTA; ciérralo en {fin_cuerpo:.3f}")
            if ini >= fin_cuerpo - TOL or (fin is not None and fin > fin_cuerpo + TOL):
                raise ValueError(f"{clave} del cuerpo {x.get('id', '') if isinstance(x, dict) else ''} "
                                 f"termina en {fin if fin is not None else ini:.3f}, dentro del CTA "
                                 f"(el cuerpo acaba en {fin_cuerpo:.3f})")
        for x in cta.get(clave, []):
            ini, _ = _tiempos(clave, x)
            if ini < fin_cuerpo - TOL:
                raise ValueError(f"{clave} del CTA empieza en {ini:.3f}, antes de que acabe el "
                                 f"cuerpo ({fin_cuerpo:.3f}): el plan del CTA va en segundos de "
                                 f"la versión")
    out = copy.deepcopy(cuerpo)
    for clave in LISTAS_PLAN:
        if clave in cta:
            out[clave] = out.get(clave, []) + copy.deepcopy(cta[clave])
    if "cta_palabra" in cta:
        out["cta_palabra"] = copy.deepcopy(cta["cta_palabra"])
    ids = [v["id"] for v in out.get("visuals", []) if "id" in v]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    if repetidos:
        raise ValueError(f"id de visual repetido entre cuerpo y CTA: {', '.join(repetidos)}")
    return out


# ── el anchor de la banda `speaker` ────────────────────────────────────────────
# La misma fórmula que `chin_at` y `check_face_top_clear` en build-composition.py
# (references/triband.md, «Cómo se deriva el anchor»): la barbilla por encima del 20 %
# inferior del lienzo, donde la plataforma pinta su interfaz, y el borde de la cara por
# debajo del techo de la banda.

def rango_anchor(face: dict, speaker: list, W: int = 1080, H: int = 1920) -> tuple[float, float]:
    top, h = speaker[0], speaker[1] - speaker[0]
    drawn_h = face["height"] * max(W / face["width"], h / face["height"])
    sobra = drawn_h - h
    if sobra <= 0:
        return 0.0, 1.0                   # la fuente entra justa: el anchor no mueve nada
    lo = (top + face["chin_frac"] * drawn_h - 0.8 * H) / sobra
    hi = face["top_frac"] * drawn_h / sobra if "top_frac" in face else 1.0
    return max(0.0, lo), min(1.0, hi)


def anchor_recomendado(lo: float, hi: float) -> float | None:
    """0.40 (el centro del 0.38–0.42 de la doctrina) si cabe con aire; si la ventana es
    angosta, su centro. Cuatro decimales: los que conserva el object-position."""
    if lo > hi:
        return None
    m = min(0.01, (hi - lo) / 2)
    return round(min(max(0.40, lo + m), hi - m), 4)
