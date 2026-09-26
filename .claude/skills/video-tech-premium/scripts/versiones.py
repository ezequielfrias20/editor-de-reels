#!/usr/bin/env python3
"""Una VERSIÓN de una pieza = el cuerpo seguido del CTA de una plataforma, en una sola
línea de tiempo. Su id es `<n>-<plataforma>` (`7-instagram`) y se comporta como una pieza
más: `transcripts/7-instagram.json`, `cuts/7-instagram.json`, `videos/7-instagram/`.

El cuerpo va PRIMERO, así que sus índices de palabra son los mismos en todas las
versiones y su EDL (`videos/<n>/edl-cuerpo.json`) se reusa tal cual. El EDL del CTA
(`videos/<n>/cta-<p>.json`) se escribe con índices relativos al transcript del CTA
(0..C-1) y aquí se desplaza al final. Sin CTA, la versión `general` es el cuerpo solo.
"""
from __future__ import annotations

import copy

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
