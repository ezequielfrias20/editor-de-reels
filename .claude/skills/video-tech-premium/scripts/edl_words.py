#!/usr/bin/env python3
"""Las palabras del transcript, remapeadas a la línea del corte.

El EDL ancla cada beat a un ÍNDICE DE PALABRA, así que esta es la pieza de la
que depende todo lo demás.

⚠ LA LÍNEA DE TIEMPO. `build-composition.py` no lee ningún transcript del
corte: lee `transcripts/<n>.json` (fuente) y remapea cada palabra con los
`keeps` de `cuts/<n>.json`. El EDL tiene que usar EXACTAMENTE el mismo par de
archivos y el mismo remapeo, o sus tiempos y los del render dejan de coincidir.

`transcripts/<n>-rough.json` es una re-transcripción de VERIFICACIÓN del corte,
no una entrada. Para la pieza 10 tiene 130 palabras frente a 131 y sus tiempos
difieren 16-60 ms de los remapeados: parecido de sobra para colar en una
revisión, distinto de sobra para descolocar cada beat.

El `fingerprint` cubre los DOS archivos, porque volver a recortar la pieza mueve
todos los beats sin tocar una sola palabra.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Word:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class WordTable:
    transcript: Path
    cuts: Path
    words: tuple[Word, ...]
    duration: float
    fingerprint: str

    def _check(self, i: int) -> None:
        if not 0 <= i < len(self.words):
            raise IndexError(
                f"palabra {i} fuera de rango: {self.transcript.name} tiene "
                f"{len(self.words)} palabras (índices 0..{len(self.words) - 1})")

    def at(self, i: int) -> float:
        """El instante, YA REMAPEADO, en que empieza a pronunciarse la palabra."""
        self._check(i)
        return self.words[i].start

    def span(self, i: int, j: int) -> tuple[float, float]:
        self._check(i)
        self._check(j)
        if j < i:
            raise ValueError(f"rango invertido: [{i}, {j}]")
        return self.words[i].start, self.words[j].end

    def text_of(self, i: int, j: int) -> str:
        self._check(i)
        self._check(j)
        if j < i:
            raise ValueError(f"rango invertido: [{i}, {j}]")
        return " ".join(w.text for w in self.words[i:j + 1])


def load_words(transcript: Path, cuts: Path) -> WordTable:
    transcript, cuts = Path(transcript), Path(cuts)
    tr_raw = transcript.read_text()
    cu_raw = cuts.read_text()
    tr, cu = json.loads(tr_raw), json.loads(cu_raw)

    if "words" not in tr:
        raise ValueError(f"{transcript} no parece un transcript de AssemblyAI")
    if "keeps" not in cu:
        raise ValueError(f"{cuts} no tiene 'keeps'")

    keeps = cu["keeps"]
    duration = round(sum(k["dur"] for k in keeps), 3)

    def remap(t: float) -> float:
        """Copia literal de build-composition.py. NO tocar: si divergen, el EDL
        y el render dejan de hablar de los mismos instantes."""
        acc = 0.0
        for k in keeps:
            if t < k["start"]:
                return acc
            if t <= k["end"]:
                return acc + (t - k["start"])
            acc += k["dur"]
        return acc

    words = tuple(
        Word(start=remap(w["start"] / 1000), end=remap(w["end"] / 1000), text=w["text"])
        for w in tr["words"]
    )
    if not words:
        raise ValueError(f"{transcript} no tiene palabras")

    # El fingerprint cubre los bytes de los DOS archivos de entrada.
    h = hashlib.sha256()
    h.update(tr_raw.encode("utf-8"))
    h.update(b"\x00")
    h.update(cu_raw.encode("utf-8"))
    return WordTable(transcript=transcript, cuts=cuts, words=words,
                     duration=duration, fingerprint=f"sha256:{h.hexdigest()}")
