# Lenguaje de edición EDL + Motion Design — plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que la pieza 10 se renderice de punta a punta desde un `edl.json` anclado al transcript, con Motion Stage, el match cut del reloj, acumulación de objetos y captions nuevas — sin tocar los gates que ya funcionan.

**Architecture:** Se añade un compilador determinista (`edl-compile.py`) entre el trabajo creativo y `build-composition.py`. El EDL referencia índices de palabra del transcript del fuente y el compilador los remapea a la línea del corte con el mismo `remap()` que usa el renderer; luego deriva stages y emite el `plan.json` que las 1296 líneas existentes ya saben consumir.

**Tech Stack:** Python 3 (stdlib + `pillow`, `fonttools`, `numpy`, `opencv-python-headless<5`), pytest (a instalar), HyperFrames CLI 0.7.105, GSAP, ffmpeg.

**Spec:** `docs/superpowers/specs/2026-09-07-edl-motion-design-design.md` — leer §2 (contrato), §9 (frontera del compilador) y §13 (determinismo) antes de empezar.

## Global Constraints

- **Regla rectora:** primero hacer que la pieza 10 funcione de punta a punta; después generalizar. La librería de objetos empieza con **6**, no con 15.
- **`build-composition.py` admite exactamente 4 cambios**, ninguno más: (1) una línea en el dict de despacho de mockups, (2) `left = -(w - W) * anchorX` en `shot_rect()`, (3) delegar métricas de caption a `caption_metrics.py`, (4) consumir captions explícitas del plan cuando existan, conservando el troceo automático como fallback.
- **Intacto y sin excepciones:** apilado de 8 capas · `check_no_black()` · checks de contraste WCAG · la fórmula de volumen de SFX · la cabecera de mezcla y `voice_gain` · la medición de barbilla · la zona segura de la plataforma · los 8 presets verificados (`punch`, `stamp`, `rise-in`, `chip-in`, `slide-in`, `box-in`, `scale-pop`, `grow-x`).
- **Piezas 1–9 congeladas.** No se re-renderizan ni se modifican sus `plan.json`.
- **La línea de tiempo:** el EDL referencia **índices** de `transcripts/<n>.json` (fuente) y el compilador aplica el **mismo `remap()`** que `build-composition.py` usando los `keeps` de `cuts/<n>.json`. `transcripts/<n>-rough.json` es verificación del corte y **no es entrada de nada**.
- **Un solo punto de cuantización:** `q(t) = round(round(float(t) * 30) / 30, 4)`. Ningún módulo redondea tiempos por su cuenta.
- **Prohibido en el navegador:** `Math.random` sin semilla, relojes de pared, red, `repeat: -1`, `back.out()` en entradas, animar `filter` o `clip-path`, animar `width`/`height` de un `<video>`.
- **Propiedades animables:** solo `opacity`, `x`, `y`, `scale`, `rotation`, `color`, `backgroundColor`, `borderRadius` y transforms.
- **`scripts/` es un symlink** a `.claude/skills/video-tech-premium/scripts`. Editar siempre por la ruta de la skill; nunca crear copias.
- **Ningún spike está en el camino crítico.** Spike A (Tarea 8) puede caer al statu quo; Spike B (Tarea 14) es independiente y opcional.

## Estado de partida — la pieza 10 ya está preparada

Verificado en disco. **No repetir estos pasos:**

| Artefacto | Estado |
| --- | --- |
| `out/10-rough.mp4` | ✅ 25 MB |
| `cuts/10.json` | ✅ `keeps` que remapean 49.157 → **44.327 s** |
| `assets/face-10.json` | ✅ `chin_frac` **0.4324**, 48/48 muestras |
| `transcripts/10.json` | ✅ **131 palabras** — lo que el EDL referencia |
| `transcripts/10-rough.json` | ⚠ 130 palabras, verificación del corte — **no usar** |
| `videos/10/` | Existe y está **vacía** |

Contenido: clínicas que pierden pacientes por contestar tarde.

### Tiempos remapeados de referencia (verificados con `remap()` real)

Los tests de todo el plan usan estos valores. Índice del fuente → `remap(start)` → `q()`:

| # | Palabra | `remap` | `q()` |
| --- | --- | --- | --- |
| 0 | La | 0.150 | 0.1333 |
| 13 | primero. | 3.355 (fin **3.724**) | 3.3667 |
| 14 | Te | 4.124 | 4.1333 |
| 18 | 11 | 5.021 | 5.0333 |
| 21 | mañana, | (fin **5.774**) | — |
| 22 | estabas | 6.063 | 6.0667 |
| 30 | después. | (fin **8.979**) | — |
| 31 | Contestaste | 9.412 | 9.4 |
| 34 | 7 | **10.293** | **10.3** |
| 37 | tarde. | (fin **11.222**) | 11.2 |
| 57 | Nadie | 18.417 | 18.4333 |
| 62 | sillón | 19.799 | 19.8 |
| 64 | teléfono, | 20.360 | 20.3667 |
| 66 | cobro | 21.241 | 21.2333 |
| 69 | Instagram | 22.139 | 22.1333 |
| 72 | tiempo. | (fin **23.312**) | 23.0 |

## File Structure

| Archivo | Responsabilidad | Tarea |
| --- | --- | --- |
| `scripts/edl_words.py` | Cargar transcript + cuts, remapear, fingerprint, resolver rangos y `atWord` → tiempo | 1 |
| `scripts/edl_schema.py` | Forma del EDL y validadores CORE estructurales | 2 |
| `scripts/edl-compile.py` | Las 8 fases: EDL → `plan.json` | 3, 6, 9, 10 |
| `scripts/edl_metrics.py` | Métricas de estilo (lista fija) + motor genérico de gates | 4 |
| `styles/motion-explainer.json` | Escalas, umbrales y severidades — **datos, no código** | 4 |
| `scripts/objects.py` | Librería de objetos con estado + `motion_stage` | 5, 6, 9 |
| `scripts/caption_metrics.py` | Ancho, nº de líneas y `floor_top` con keyword grande | 7 |
| `scripts/tokens.py` | + `spotlight()`, `grain()`, `THEME`, `KINETIC` | 5, 7, 9 |
| `scripts/build-composition.py` | **4 cambios quirúrgicos** | 5, 7, 8 |
| `scripts/measure-face.py` | + `cx_frac` / `cy_frac` | 8 |
| `scripts/asset_resolve.py` | Asset Resolver con prioridad y manifest | 12 |
| `videos/10/edl.json` | La pieza | 3→11 |
| `tests/` | pytest: unitarios + golden | 1→13 |

### Orden y dependencias

```
1 palabras ─→ 2 schema ─→ 3 compilador mínimo ─→ 4 gates
                              │
                              ├─→ 5 Motion Stage ─→ 6 reloj+match cut ─→ 9 acumulación
                              ├─→ 7 captions/keyword
                              ├─→ 8 spike A + cámaras
                              └─→ 10 SFX
                                        └─→ 11 PIEZA 10 COMPLETA (hito)
                                                  └─→ 12 Resolver ─→ 13 Planner

14 spike B (Three.js) ── independiente, fuera del camino crítico
```

---

## Task 1: Palabras remapeadas y fingerprint

Todo depende de convertir un `atWord` en un instante de la línea del corte. Y hoy no hay ni pytest ni `tests/`.

**Files:**
- Create: `.claude/skills/video-tech-premium/scripts/edl_words.py`
- Create: `tests/conftest.py`
- Create: `tests/test_edl_words.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `load_words(transcript: Path, cuts: Path) -> WordTable`
  - `WordTable.words: tuple[Word, ...]` con `.start`, `.end` (segundos, **ya remapeados**), `.text`
  - `WordTable.duration: float` — suma de los `keeps`, la duración real de la pieza
  - `WordTable.fingerprint: str` — `"sha256:<hex>"`, **cubre transcript y cuts**
  - `WordTable.at(i) -> float` · `.span(i, j) -> tuple[float, float]` · `.text_of(i, j) -> str`

- [ ] **Step 1: Instalar pytest**

```bash
cd /Users/ezequielfrias/Documents/Cubo/mi-universo/marca-personal/editor-videos
.venv/bin/python -m pip install -q pytest && .venv/bin/python -m pytest --version
```

Esperado: imprime una versión. Si `.venv/bin/pip` no existe, usar `uv pip install pytest`.

- [ ] **Step 2: Crear `tests/conftest.py`**

`scripts/` es un symlink dentro de la skill y no es un paquete importable.

```python
"""Deja los scripts de la skill importables desde los tests."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "video-tech-premium" / "scripts"))

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def w10(project_root):
    """Las palabras de la pieza 10, remapeadas a la línea del corte."""
    from edl_words import load_words
    return load_words(project_root / "transcripts" / "10.json",
                      project_root / "cuts" / "10.json")
```

- [ ] **Step 3: Escribir el test que falla**

`tests/test_edl_words.py`. Los valores salen de correr `remap()` sobre los archivos reales, no de estimar.

```python
import pytest
from edl_words import load_words


def test_carga_las_131_palabras_del_fuente(w10):
    assert len(w10.words) == 131


def test_la_duracion_es_la_suma_de_los_keeps(w10):
    assert w10.duration == pytest.approx(44.327)


def test_remapea_a_la_linea_del_corte(w10):
    # "La" empieza en 0.42 en el fuente y en 0.150 tras quitar la cabeza muerta.
    assert w10.words[0].text == "La"
    assert w10.at(0) == pytest.approx(0.150, abs=1e-3)


def test_at_devuelve_el_start_remapeado(w10):
    # La palabra 34 es el "7" de "7 de la tarde": 10.83 en el fuente, 10.293 remapeado.
    assert w10.at(34) == pytest.approx(10.293, abs=1e-3)
    # La palabra 18 es el "11" de "11 de la mañana".
    assert w10.at(18) == pytest.approx(5.021, abs=1e-3)


def test_span_devuelve_inicio_de_i_y_fin_de_j(w10):
    a, b = w10.span(31, 37)          # el segmento del reloj
    assert (a, b) == pytest.approx((9.412, 11.222), abs=1e-3)
    a, b = w10.span(0, 13)           # el hook
    assert (a, b) == pytest.approx((0.150, 3.724), abs=1e-3)


def test_ninguna_palabra_pasa_de_la_duracion(w10):
    assert max(x.end for x in w10.words) <= w10.duration + 1e-6


def test_los_tiempos_no_retroceden(w10):
    ts = [x.start for x in w10.words]
    assert ts == sorted(ts)


def test_text_of_une_el_rango(w10):
    assert w10.text_of(11, 13) == "simplemente contestó primero."


def test_fingerprint_es_estable(w10, project_root):
    otro = load_words(project_root / "transcripts" / "10.json",
                      project_root / "cuts" / "10.json")
    assert w10.fingerprint == otro.fingerprint and w10.fingerprint.startswith("sha256:")


def test_el_fingerprint_cambia_si_cambian_los_cortes(w10, project_root, tmp_path):
    """Recortar de nuevo la pieza mueve TODOS los beats sin tocar el transcript.
    Si el fingerprint no cubriera cuts/, ese cambio pasaría en silencio."""
    import json
    cu = json.loads((project_root / "cuts" / "10.json").read_text())
    cu["keeps"][0]["dur"] += 0.5
    p = tmp_path / "cuts.json"
    p.write_text(json.dumps(cu))
    assert load_words(project_root / "transcripts" / "10.json", p).fingerprint \
        != w10.fingerprint


def test_usar_el_rough_como_transcript_da_otro_fingerprint(w10, project_root):
    """El -rough.json parece un atajo razonable y da 130 palabras y tiempos
    16-60 ms distintos: valida y está mal."""
    rough = load_words(project_root / "transcripts" / "10-rough.json",
                       project_root / "cuts" / "10.json")
    assert len(rough.words) == 130
    assert rough.fingerprint != w10.fingerprint


def test_indice_fuera_de_rango_falla_claro(w10):
    with pytest.raises(IndexError, match="131 palabras"):
        w10.at(131)


def test_span_invertido_falla(w10):
    with pytest.raises(ValueError, match="invertido"):
        w10.span(13, 0)
```

- [ ] **Step 4: Correr los tests y verificar que fallan**

```bash
.venv/bin/python -m pytest tests/test_edl_words.py -v
```

Esperado: FAIL — `ModuleNotFoundError: No module named 'edl_words'`.

- [ ] **Step 5: Implementar `edl_words.py`**

`remap` es **una copia literal** de la de `build-composition.py:212-220`. No mejorarla: si las dos divergen, el EDL y el render dejan de hablar de los mismos instantes.

```python
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
```

- [ ] **Step 6: Correr los tests y verificar que pasan**

```bash
.venv/bin/python -m pytest tests/test_edl_words.py -v
```

Esperado: 13 passed.

- [ ] **Step 7: Ignorar la caché de pytest**

```bash
grep -q '.pytest_cache' .gitignore || printf '\n.pytest_cache/\n' >> .gitignore
```

- [ ] **Step 8: Commit**

```bash
git add tests/conftest.py tests/test_edl_words.py .gitignore \
        .claude/skills/video-tech-premium/scripts/edl_words.py
git commit -m "feat(edl): palabras remapeadas a la línea del corte y fingerprint

El EDL ancla cada beat a un índice de palabra, así que esta es la pieza de
la que depende el resto. Copia literal del remap() de build-composition.py
para que el EDL y el render hablen de los mismos instantes.

El fingerprint cubre transcript Y cuts: volver a recortar la pieza mueve
todos los beats sin tocar una palabra, y sin esto pasaría en silencio.

Un test documenta la trampa del -rough.json: 130 palabras frente a 131 y
tiempos 16-60 ms distintos.

Primer test unitario del proyecto: instala pytest y crea tests/."
```

---
## Task 2: Schema del EDL, derivación de stages y validadores CORE

El contrato congelado. Un EDL que pasa `load_edl` es **estructuralmente ejecutable**; lo que quede mal a partir de aquí es gusto, y eso lo miden los gates del style profile (Tarea 4), que viven en datos.

Dos validaciones se dejan para más tarde porque necesitan piezas que aún no existen: **zona segura de slots** → Tarea 5 (necesita `objects.py`), **asset presente en el manifest** → Tarea 12 (necesita el Resolver). El formato versionado del asset sí se valida aquí.

**Files:**
- Create: `.claude/skills/video-tech-premium/scripts/edl_schema.py`
- Create: `tests/test_edl_schema.py`

**Interfaces:**
- Consumes: `edl_words.load_words`, `WordTable.at/span/text_of/duration/fingerprint`
- Produces:
  - `SCENE_TYPES`, `REPRESENTATION_TYPES`, `EVENT_TYPES`, `TRANSITIONS`, `CAMERAS`, `STAGE_TYPES`, `OVERRIDE_WHITELIST` — `frozenset`s
  - `load_edl(path: Path, project_root: Path) -> Edl` — carga, resuelve palabras y **valida**; lanza `EdlError` con **todos** los fallos juntos
  - `Edl.segments: tuple[Segment, ...]`, `.wt: WordTable`, `.fmt`, `.piece`, `.style_profile`, `.overrides`, `.voice_gain`, `.music`, `.planner`
  - `Segment.words: tuple[int, int]`, `.semantic_intent`, `.scene_type`, `.representation_type`, `.camera`, `.default_preset`, `.transition_in`, `.transition_out`, `.hold`, `.reason`, `.events: tuple[Event, ...]`
  - `Segment.t(wt) -> tuple[float, float]`
  - `Event.type`, `.at_word`, `.offset`, `.words`, `.instance_id`, `.asset`, `.state`, `.preset`, `.sfx`, `.slot`, `.crowd`, `.theme`, `.roles`, `.trim`
  - `Event.t(wt) -> float` — `wt.at(at_word) + offset`, **sin cuantizar**
  - `derive_stages(segments) -> tuple[Stage, ...]` con `Stage.first`, `.last`
  - `EdlError(Exception)` con `.problems: list[str]`

- [ ] **Step 1: Escribir el test que falla**

`tests/test_edl_schema.py`.

```python
import json
import pytest
from edl_schema import EdlError, derive_stages, load_edl


@pytest.fixture
def edl_min(w10):
    """El EDL más pequeño que es válido: un A_ROLL que cubre las 131 palabras."""
    return {
        "format": "REEL", "piece": 10, "style_profile": "motion-explainer",
        "transcript": {"words": "transcripts/10.json", "cuts": "cuts/10.json",
                       "fingerprint": w10.fingerprint},
        "voice_gain": 0.70,
        "segments": [{
            "words": [0, 130],
            "semanticIntent": "la pieza entera de una",
            "sceneType": "A_ROLL", "camera": "CLOSE", "transitionIn": "CUT",
            "events": [{"atWord": 0, "type": "CAPTION", "words": [0, 4]}],
            "reason": "andamiaje mínimo para los tests del schema",
        }],
    }


@pytest.fixture
def write_edl(tmp_path, project_root):
    def _w(data):
        p = tmp_path / "edl.json"
        p.write_text(json.dumps(data, ensure_ascii=False))
        return load_edl(p, project_root)
    return _w


def problems_of(write_edl, data):
    with pytest.raises(EdlError) as ei:
        write_edl(data)
    return " | ".join(ei.value.problems)


def _stage_edl(base, events, **kw):
    seg = {"words": [0, 130], "semanticIntent": "un stage",
           "sceneType": "MOTION_STAGE", "representationType": "OBJECT",
           "camera": "OFF", "transitionIn": "CUT", "events": events,
           "reason": "probar el ciclo de vida de las instancias"}
    seg.update(kw)
    return dict(base, segments=[seg])


# ── lo que debe pasar ────────────────────────────────────────────────────────
def test_un_edl_minimo_valido_carga(write_edl, edl_min):
    edl = write_edl(edl_min)
    assert len(edl.segments) == 1
    assert edl.segments[0].t(edl.wt) == pytest.approx((0.150, 43.933), abs=1e-2)


def test_el_instante_de_un_evento_sale_de_su_palabra_remapeada(write_edl, edl_min):
    edl_min["segments"][0]["events"] = [
        {"atWord": 34, "type": "CAPTION", "words": [34, 37]}]
    edl = write_edl(edl_min)
    assert edl.segments[0].events[0].t(edl.wt) == pytest.approx(10.293, abs=1e-3)


def test_el_offset_se_suma_sin_cuantizar(write_edl, edl_min):
    edl_min["segments"][0]["events"] = [
        {"atWord": 34, "type": "CAPTION", "words": [34, 37], "offset": -0.08}]
    edl = write_edl(edl_min)
    assert edl.segments[0].events[0].t(edl.wt) == pytest.approx(10.213, abs=1e-3)


def test_offset_que_adelanta_demasiado_falla(write_edl, edl_min):
    edl_min["segments"][0]["events"] = [
        {"atWord": 34, "type": "CAPTION", "words": [34, 37], "offset": -0.4}]
    assert "adelanta el guion" in problems_of(write_edl, edl_min)


# ── fingerprint ─────────────────────────────────────────────────────────────
def test_fingerprint_que_no_cuadra_falla(write_edl, edl_min):
    edl_min["transcript"]["fingerprint"] = "sha256:0000"
    assert "fingerprint" in problems_of(write_edl, edl_min)


def test_apuntar_al_rough_falla(write_edl, edl_min):
    edl_min["transcript"]["words"] = "transcripts/10-rough.json"
    assert "fingerprint" in problems_of(write_edl, edl_min)


def test_falta_cuts_falla(write_edl, edl_min):
    del edl_min["transcript"]["cuts"]
    with pytest.raises(EdlError, match="cuts"):
        write_edl(edl_min)


# ── cobertura y contigüidad ─────────────────────────────────────────────────
def test_los_segmentos_deben_cubrir_todas_las_palabras(write_edl, edl_min):
    edl_min["segments"][0]["words"] = [0, 100]
    assert "no cubren" in problems_of(write_edl, edl_min)


def test_hueco_entre_segmentos_falla(write_edl, edl_min):
    edl_min["segments"] = [dict(edl_min["segments"][0], words=[0, 13]),
                           dict(edl_min["segments"][0], words=[20, 130])]
    assert "hueco" in problems_of(write_edl, edl_min)


def test_solape_entre_segmentos_falla(write_edl, edl_min):
    edl_min["segments"] = [dict(edl_min["segments"][0], words=[0, 20]),
                           dict(edl_min["segments"][0], words=[13, 130])]
    assert "solap" in problems_of(write_edl, edl_min)


# ── captions y keywords ─────────────────────────────────────────────────────
def test_caption_fuera_del_segmento_falla(write_edl, edl_min):
    edl_min["segments"] = [
        dict(edl_min["segments"][0], words=[0, 13],
             events=[{"atWord": 0, "type": "CAPTION", "words": [0, 40]}]),
        dict(edl_min["segments"][0], words=[14, 130], events=[])]
    assert "fuera del segmento" in problems_of(write_edl, edl_min)


def test_keyword_fuera_de_todo_caption_falla(write_edl, edl_min):
    edl_min["segments"][0]["events"] = [
        {"atWord": 0,  "type": "CAPTION", "words": [0, 4]},
        {"atWord": 12, "type": "KEYWORD", "words": [12, 13]}]
    assert "keyword" in problems_of(write_edl, edl_min)


def test_keyword_dentro_de_su_caption_pasa(write_edl, edl_min):
    edl_min["segments"][0]["events"] = [
        {"atWord": 11, "type": "CAPTION", "words": [11, 13]},
        {"atWord": 12, "type": "KEYWORD", "words": [12, 13]}]
    assert len(write_edl(edl_min).segments[0].events) == 2


def test_caption_prohibido_en_kinetic_type(write_edl, edl_min):
    edl_min["segments"][0].update(sceneType="KINETIC_TYPE",
                                  representationType="OBJECT", camera="OFF")
    assert "KINETIC_TYPE" in problems_of(write_edl, edl_min)


# ── reason y representationType ─────────────────────────────────────────────
def test_reason_ausente_falla(write_edl, edl_min):
    del edl_min["segments"][0]["reason"]
    assert "reason" in problems_of(write_edl, edl_min)


def test_reason_que_repite_el_intent_falla(write_edl, edl_min):
    edl_min["segments"][0]["reason"] = edl_min["segments"][0]["semanticIntent"]
    assert "repite" in problems_of(write_edl, edl_min)


def test_motion_stage_sin_representation_type_falla(write_edl, edl_min):
    edl_min["segments"][0].update(sceneType="MOTION_STAGE", camera="OFF")
    assert "representationType" in problems_of(write_edl, edl_min)


def test_a_roll_no_necesita_representation_type(write_edl, edl_min):
    assert write_edl(edl_min).segments[0].representation_type is None


# ── instancias ──────────────────────────────────────────────────────────────
def test_object_in_duplicado_en_el_mismo_stage_falla(write_edl, edl_min):
    data = _stage_edl(edl_min, [
        {"atWord": 0,  "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "center"},
        {"atWord": 10, "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "center"}])
    assert "ya existe" in problems_of(write_edl, data)


def test_object_state_sobre_instancia_inexistente_falla(write_edl, edl_min):
    data = _stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_STATE", "instanceId": "fantasma",
         "state": {"time": "19:00"}}])
    assert "no existe" in problems_of(write_edl, data)


def test_object_state_tras_exit_falla(write_edl, edl_min):
    data = _stage_edl(edl_min, [
        {"atWord": 0,  "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "center"},
        {"atWord": 5,  "type": "OBJECT_EXIT", "instanceId": "c"},
        {"atWord": 10, "type": "OBJECT_STATE", "instanceId": "c",
         "state": {"time": "19:00"}}])
    assert "retirada" in problems_of(write_edl, data)


def test_stage_clear_libera_los_instance_id(write_edl, edl_min):
    data = _stage_edl(edl_min, [
        {"atWord": 0,  "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "center"},
        {"atWord": 5,  "type": "STAGE_CLEAR"},
        {"atWord": 10, "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "center"}])
    assert len(write_edl(data).segments[0].events) == 3


# ── assets ──────────────────────────────────────────────────────────────────
def test_asset_semantico_sin_resolver_falla(write_edl, edl_min):
    data = _stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "asset": "clock",
         "instanceId": "c", "slot": "center"}])
    assert "sin resolver" in problems_of(write_edl, data)


def test_asset_sin_version_falla(write_edl, edl_min):
    data = _stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "asset": "object:clock",
         "instanceId": "c", "slot": "center"}])
    assert "versión" in problems_of(write_edl, data)


def test_asset_resuelto_y_versionado_pasa(write_edl, edl_min):
    data = _stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "center"}])
    assert write_edl(data).segments[0].events[0].asset == "object:clock@1"


# ── transiciones ────────────────────────────────────────────────────────────
def test_transition_out_en_el_ultimo_segmento_falla(write_edl, edl_min):
    edl_min["segments"][0]["transitionOut"] = "BLUR_WIPE"
    assert "último segmento" in problems_of(write_edl, edl_min)


def test_transiciones_en_conflicto_en_un_limite_fallan(write_edl, edl_min):
    edl_min["segments"] = [
        dict(edl_min["segments"][0], words=[0, 13], transitionOut="BLUR_WIPE"),
        dict(edl_min["segments"][0], words=[14, 130], transitionIn="DIAGONAL_WIPE")]
    assert "conflicto" in problems_of(write_edl, edl_min)


def test_match_cut_sin_instancia_compartida_falla(write_edl, edl_min):
    edl_min["segments"] = [
        dict(edl_min["segments"][0], words=[0, 13]),
        dict(edl_min["segments"][0], words=[14, 130],
             transitionIn="OBJECT_MATCH_CUT")]
    assert "OBJECT_MATCH_CUT" in problems_of(write_edl, edl_min)


def test_match_cut_sin_object_state_falla(write_edl, edl_min):
    base = {"semanticIntent": "el reloj", "sceneType": "MOTION_STAGE",
            "representationType": "OBJECT", "camera": "OFF",
            "reason": "un match cut que no muta nada"}
    edl_min["segments"] = [
        dict(base, words=[0, 30], transitionIn="CUT", events=[
            {"atWord": 18, "type": "OBJECT_IN", "asset": "object:clock@1",
             "instanceId": "clock-main", "slot": "center",
             "state": {"time": "11:00"}}]),
        dict(base, words=[31, 130], transitionIn="OBJECT_MATCH_CUT", events=[])]
    assert "no las muta" in problems_of(write_edl, edl_min)


def test_match_cut_valido_pasa(write_edl, edl_min):
    """El caso del reloj: la instancia vive a ambos lados y el entrante la muta."""
    base = {"semanticIntent": "el reloj", "sceneType": "MOTION_STAGE",
            "representationType": "OBJECT", "camera": "OFF",
            "reason": "probar un match cut legítimo"}
    edl_min["segments"] = [
        dict(base, words=[0, 30], transitionIn="CUT", events=[
            {"atWord": 18, "type": "OBJECT_IN", "asset": "object:clock@1",
             "instanceId": "clock-main", "slot": "center",
             "state": {"time": "11:00"}}]),
        dict(base, words=[31, 130], transitionIn="OBJECT_MATCH_CUT",
             representationType="STATE_CHANGE", events=[
            {"atWord": 34, "type": "OBJECT_STATE", "instanceId": "clock-main",
             "state": {"time": "19:00"}, "preset": "hands-sweep"}])]
    assert write_edl(edl_min).segments[1].transition_in == "OBJECT_MATCH_CUT"


# ── overrides ───────────────────────────────────────────────────────────────
def test_override_fuera_de_whitelist_falla(write_edl, edl_min):
    edl_min["plan_overrides"] = [
        {"target": "visuals[stage-a].zoom", "value": 2, "why": "porque"}]
    assert "whitelist" in problems_of(write_edl, edl_min)


def test_override_sin_why_falla(write_edl, edl_min):
    edl_min["plan_overrides"] = [
        {"target": "visuals[stage-a].cap_top", "value": 1180}]
    assert "why" in problems_of(write_edl, edl_min)


def test_override_valido_pasa(write_edl, edl_min):
    edl_min["plan_overrides"] = [
        {"target": "visuals[stage-a].cap_top", "value": 1180,
         "why": "el bloque de dos líneas se metía 46 px en la zona segura"}]
    assert len(write_edl(edl_min).overrides) == 1


# ── draft ───────────────────────────────────────────────────────────────────
def test_un_draft_es_rechazado(edl_min, tmp_path, project_root):
    p = tmp_path / "edl.draft.json"
    p.write_text(json.dumps(edl_min, ensure_ascii=False))
    with pytest.raises(EdlError, match="draft"):
        load_edl(p, project_root)


# ── stages ──────────────────────────────────────────────────────────────────
class _S:
    def __init__(self, st):
        self.scene_type = st


def test_los_segmentos_contiguos_de_stage_forman_uno_solo():
    segs = [_S("A_ROLL"), _S("MOTION_STAGE"), _S("KINETIC_TYPE"),
            _S("MOTION_STAGE"), _S("A_ROLL"), _S("MOTION_STAGE")]
    assert [(s.first, s.last) for s in derive_stages(segs)] == [(1, 3), (5, 5)]


def test_una_pieza_sin_stages_no_deriva_ninguno():
    assert derive_stages([_S("A_ROLL"), _S("CTA")]) == ()


# ── el error junta todos los problemas ──────────────────────────────────────
def test_todos_los_problemas_se_reportan_juntos(write_edl, edl_min):
    del edl_min["segments"][0]["reason"]
    edl_min["transcript"]["fingerprint"] = "sha256:0000"
    with pytest.raises(EdlError) as ei:
        write_edl(edl_min)
    assert len(ei.value.problems) >= 2
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

```bash
.venv/bin/python -m pytest tests/test_edl_schema.py -v
```

Esperado: FAIL — `ModuleNotFoundError: No module named 'edl_schema'`.

- [ ] **Step 3: Implementar `edl_schema.py`**

Cuatro cosas que el implementador **no debe improvisar**:

1. Los problemas se **acumulan** y se lanzan juntos. Un EDL recién escrito tiene varios fallos; reportar uno por corrida convierte escribir un EDL en un bucle de una corrección por vez.
2. El ciclo de vida de instancias se simula **stage a stage**, recorriendo eventos por `(at_word, orden en el archivo)`.
3. `Event.t()` **no cuantiza**. La cuantización es del compilador y ocurre en un único sitio.
4. Regex del asset resuelto: `^(object|recording|gen|broll|mock):[a-z0-9-]+@\d+(\?.*)?$`. Sin `:` → «sin resolver». Con `:` y sin `@n` → «sin versión». Son **dos mensajes distintos** porque son dos errores distintos y el arreglo es distinto.

```python
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

from edl_words import WordTable, load_words

SCENE_TYPES = frozenset({"A_ROLL", "A_ROLL_ICON", "MOTION_STAGE",
                         "KINETIC_TYPE", "UI_DEMO", "BROLL", "CTA"})
REPRESENTATION_TYPES = frozenset({"OBJECT", "STATE_CHANGE", "QUANTITY", "RELATION",
                                  "SEQUENCE", "CONTRAST", "INTERFACE"})
EVENT_TYPES = frozenset({"OBJECT_IN", "OBJECT_STATE", "OBJECT_EXIT", "STAGE_CLEAR",
                         "THEME_CHANGE", "CAPTION", "KEYWORD", "CAMERA",
                         "TYPE_BEAT", "UI_ACTION", "SFX"})
TRANSITIONS = frozenset({"CUT", "DIAGONAL_WIPE", "BLUR_WIPE",
                         "OBJECT_MATCH_CUT", "SCALE_BLUR"})
CAMERAS = frozenset({"WIDE", "MEDIUM", "CLOSE", "OFF"})

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
    )


def _check_assets(segments, problems: list[str]) -> None:
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

    _check_assets(segments, problems)
    _check_instances(segments, problems)
    _check_transitions(segments, problems)

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
               music=raw.get("music", {}), planner=raw.get("planner", {}))
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

```bash
.venv/bin/python -m pytest tests/test_edl_schema.py -v
```

Esperado: ~35 passed. Si alguno falla por el texto de un mensaje, ajustar el **mensaje** para que sea más útil al editor humano — nunca el test para que pase.

- [ ] **Step 5: Correr la suite entera**

```bash
.venv/bin/python -m pytest tests/ -q
```

Esperado: 0 fallos.

- [ ] **Step 6: Commit**

```bash
git add tests/test_edl_schema.py \
        .claude/skills/video-tech-premium/scripts/edl_schema.py
git commit -m "feat(edl): schema, derivación de stages y validadores CORE

Un EDL que pasa load_edl es estructuralmente ejecutable. Valida
fingerprint, cobertura y contigüidad de palabras, subconjuntos
caption/keyword, ciclo de vida de instancias por stage,
OBJECT_MATCH_CUT con instancia compartida Y mutada, conflictos de
transición en un límite, transitionOut final, whitelist de overrides,
representationType obligatorio y formato versionado de assets.

Los problemas se acumulan y se lanzan juntos: reportar uno por corrida
convierte escribir un EDL en un bucle de una corrección por vez.

Los stages se DERIVAN de series contiguas de MOTION_STAGE/KINETIC_TYPE.
Es lo que da ámbito a instanceId y lo que permitirá emitir el stage como
una sola entrada de visuals.

Pendientes por dependencia: zona segura de slots (Tarea 5, necesita
objects.py) y presencia en el manifest (Tarea 12, necesita el Resolver)."
```

---
## Task 3: Compilador mínimo — la pieza 10 renderiza desde un EDL

**El hito más importante del plan.** Al terminar esta tarea existe un MP4 de la pieza 10 generado desde un `edl.json`, y `build-composition.py` **no se ha tocado ni una línea**.

El truco para conseguirlo: el EDL de esta tarea es **todo `A_ROLL`**, y el compilador emite `keywords` como lista de strings, que es lo que el motor de captions actual ya consume. Motion Stage, objetos y captions explícitas llegan después, convirtiendo segmentos concretos.

**Files:**
- Create: `.claude/skills/video-tech-premium/scripts/edl-compile.py`
- Create: `.claude/skills/video-tech-premium/styles/motion-explainer.json`
- Create: `videos/10/edl.json`
- Create: `tests/test_edl_compile.py`

**Interfaces:**
- Consumes: `edl_schema.load_edl`, `edl_words.WordTable`
- Produces:
  - `load_style(name: str, skill_root: Path) -> dict`
  - `compile_edl(edl: Edl, style: dict) -> dict` — **función pura**, devuelve el `plan.json` como dict
  - `q(t: float) -> float` — `round(round(t * 30) / 30, 4)`, **el único punto de cuantización**
  - `write_plan(plan: dict, out: Path) -> None` — `sort_keys=True`, separadores fijos, `\n` final
  - CLI: `edl-compile.py --project . --piece 10 [-o videos/10/plan.json] [--report path]`

- [ ] **Step 1: Crear el style profile (sin gates todavía)**

`.claude/skills/video-tech-premium/styles/motion-explainer.json`. Los gates llegan en la Tarea 4; aquí solo la configuración que el compilador mínimo necesita.

```json
{
  "name": "motion-explainer",
  "camera": {
    "ladder": { "WIDE": 1.00, "MEDIUM": 1.12, "CLOSE": 1.20 },
    "max_upscale": 1.20,
    "min_gap": 0.70,
    "hook_exempt_until": 3.0,
    "default_anchor": 0.42
  },
  "kinetic": { "small": 1.00, "medium": 1.55, "hero": 2.20, "mega": 2.80 },
  "caption": { "keyword_scale": 1.22 },
  "stage": { "spotlight_alpha": 0.05, "fade_in": 0.22, "fade_out": 0.18 },
  "sfx": { "collapse_same": 0.25, "concurrency_window": 0.18 },
  "gates": []
}
```

- [ ] **Step 2: Escribir el EDL grueso de la pieza 10**

`videos/10/edl.json`. **Nueve segmentos, uno por frase**, con los límites ya calculados sobre el transcript real. Todo `A_ROLL` — las conversiones a `MOTION_STAGE` llegan en las Tareas 6 y 9.

El `fingerprint` no se inventa; se obtiene así:

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, '.claude/skills/video-tech-premium/scripts')
from edl_words import load_words
print(load_words('transcripts/10.json', 'cuts/10.json').fingerprint)"
```

```jsonc
{
  "format": "REEL",
  "piece": 10,
  "style_profile": "motion-explainer",
  "transcript": {
    "words": "transcripts/10.json",
    "cuts": "cuts/10.json",
    "fingerprint": "PEGAR AQUÍ LA SALIDA DEL COMANDO DE ARRIBA"
  },
  "voice_gain": 0.70,
  "music": { "src": "assets/music/bed-tech.mp3", "fade_in": 1.0, "fade_out": 2.6 },

  "segments": [
    { "words": [0, 13], "sceneType": "A_ROLL", "camera": "CLOSE",
      "semanticIntent": "no perdiste por calidad, perdiste por velocidad",
      "transitionIn": "CUT",
      "events": [
        { "atWord": 0,  "type": "CAPTION", "words": [0, 4] },
        { "atWord": 5,  "type": "CAPTION", "words": [5, 10] },
        { "atWord": 11, "type": "CAPTION", "words": [11, 13] },
        { "atWord": 12, "type": "KEYWORD", "words": [12, 13], "preset": "punch" }
      ],
      "reason": "es la acusación que abre la pieza; su cara sostiene el golpe y un gráfico se lo robaría" },

    { "words": [14, 30], "sceneType": "A_ROLL", "camera": "MEDIUM",
      "semanticIntent": "te escribieron mientras estabas ocupado",
      "events": [
        { "atWord": 14, "type": "CAPTION", "words": [14, 17] },
        { "atWord": 18, "type": "CAPTION", "words": [18, 21] },
        { "atWord": 18, "type": "KEYWORD", "words": [18, 18] },
        { "atWord": 22, "type": "CAPTION", "words": [22, 26] },
        { "atWord": 27, "type": "CAPTION", "words": [27, 30] }
      ],
      "reason": "la hora concreta es el dato que hace que el espectador se reconozca" },

    { "words": [31, 37], "sceneType": "A_ROLL", "camera": "CLOSE",
      "semanticIntent": "pasaron ocho horas",
      "events": [
        { "atWord": 31, "type": "CAPTION", "words": [31, 33] },
        { "atWord": 34, "type": "CAPTION", "words": [34, 37] },
        { "atWord": 34, "type": "KEYWORD", "words": [34, 34] }
      ],
      "reason": "el contraste 11 → 7 es el corazón del problema; en la Tarea 6 pasa a MOTION_STAGE con el match cut del reloj" },

    { "words": [38, 48], "sceneType": "A_ROLL", "camera": "MEDIUM",
      "semanticIntent": "para cuando contestaste ya había tres competidores",
      "events": [
        { "atWord": 38, "type": "CAPTION", "words": [38, 41] },
        { "atWord": 42, "type": "CAPTION", "words": [42, 45] },
        { "atWord": 46, "type": "CAPTION", "words": [46, 48] },
        { "atWord": 46, "type": "KEYWORD", "words": [46, 46] }
      ],
      "reason": "la cifra 3 es lo que convierte la anécdota en pérdida medible" },

    { "words": [49, 56], "sceneType": "A_ROLL", "camera": "WIDE",
      "semanticIntent": "descarta al culpable obvio antes de dar el diagnóstico",
      "events": [
        { "atWord": 49, "type": "CAPTION", "words": [49, 53] },
        { "atWord": 54, "type": "CAPTION", "words": [54, 56] },
        { "atWord": 56, "type": "KEYWORD", "words": [56, 56] }
      ],
      "reason": "abre una explicación nueva, así que WIDE; el giro necesita aire" },

    { "words": [57, 72], "sceneType": "A_ROLL", "camera": "MEDIUM",
      "semanticIntent": "cuatro trabajos incompatibles cayendo sobre la misma persona",
      "events": [
        { "atWord": 57, "type": "CAPTION", "words": [57, 59] },
        { "atWord": 60, "type": "CAPTION", "words": [60, 64] },
        { "atWord": 65, "type": "CAPTION", "words": [65, 69] },
        { "atWord": 70, "type": "CAPTION", "words": [70, 72] },
        { "atWord": 71, "type": "KEYWORD", "words": [71, 72] }
      ],
      "reason": "la enumeración ES la carga; en la Tarea 9 pasa a MOTION_STAGE acumulativo" },

    { "words": [73, 87], "sceneType": "A_ROLL", "camera": "MEDIUM",
      "semanticIntent": "contratar no arregla nada, solo mueve el cuello de botella",
      "events": [
        { "atWord": 73, "type": "CAPTION", "words": [73, 76] },
        { "atWord": 77, "type": "CAPTION", "words": [77, 79] },
        { "atWord": 80, "type": "CAPTION", "words": [80, 83] },
        { "atWord": 84, "type": "CAPTION", "words": [84, 87] },
        { "atWord": 83, "type": "KEYWORD", "words": [83, 85] }
      ],
      "reason": "desmonta la solución que el espectador ya estaba pensando" },

    { "words": [88, 109], "sceneType": "A_ROLL", "camera": "WIDE",
      "semanticIntent": "el problema no es la velocidad, es la dependencia",
      "events": [
        { "atWord": 88,  "type": "CAPTION", "words": [88, 92] },
        { "atWord": 93,  "type": "CAPTION", "words": [93, 96] },
        { "atWord": 97,  "type": "CAMERA",  "camera": "MEDIUM" },
        { "atWord": 97,  "type": "CAPTION", "words": [97, 101] },
        { "atWord": 102, "type": "CAPTION", "words": [102, 105] },
        { "atWord": 106, "type": "CAPTION", "words": [106, 109] }
      ],
      "reason": "es la tesis de la pieza; el cambio de cámara a mitad evita 6.8 s del mismo plano" },

    { "words": [110, 130], "sceneType": "A_ROLL", "camera": "CLOSE",
      "semanticIntent": "la primera respuesta sostiene, no cierra",
      "events": [
        { "atWord": 110, "type": "CAPTION", "words": [110, 114] },
        { "atWord": 115, "type": "CAPTION", "words": [115, 118] },
        { "atWord": 119, "type": "CAMERA",  "camera": "MEDIUM" },
        { "atWord": 119, "type": "CAPTION", "words": [119, 123] },
        { "atWord": 124, "type": "CAPTION", "words": [124, 130] },
        { "atWord": 121, "type": "KEYWORD", "words": [121, 121] }
      ],
      "reason": "cierra con la reformulación; CLOSE porque es la frase que se recuerda" }
  ]
}
```

⚠ Los rangos de `CAPTION` son un **primer troceo**. Si `load_edl` se queja de que una keyword no cae dentro de su caption, ajustar el rango del caption — **no** mover la keyword: la keyword la elige el sentido de la frase, el corte del bloque es lo negociable.

- [ ] **Step 3: Escribir el test que falla**

`tests/test_edl_compile.py`.

```python
import json
import pytest
from edl_compile import compile_edl, load_style, q, write_plan
from edl_schema import load_edl


@pytest.fixture(scope="module")
def skill_root(project_root):
    return project_root / ".claude" / "skills" / "video-tech-premium"


@pytest.fixture(scope="module")
def style(skill_root):
    return load_style("motion-explainer", skill_root)


@pytest.fixture(scope="module")
def edl10(project_root):
    return load_edl(project_root / "videos" / "10" / "edl.json", project_root)


@pytest.fixture(scope="module")
def plan10(edl10, style):
    return compile_edl(edl10, style)


# ── cuantización ────────────────────────────────────────────────────────────
def test_q_cuantiza_a_la_rejilla_de_30fps():
    assert q(10.293) == 10.3          # 308.79 -> 309 -> 309/30
    assert q(4.124) == 4.1333
    assert q(0.150) == 0.1333


# ── forma del plan ──────────────────────────────────────────────────────────
def test_el_plan_tiene_las_claves_que_build_composition_espera(plan10):
    for k in ("format", "keywords", "music", "voice_gain",
              "shots", "cards", "visuals", "sfx"):
        assert k in plan10, f"falta '{k}'"
    assert plan10["format"] == "REEL"
    assert plan10["voice_gain"] == 0.70


def test_hay_un_encuadre_por_segmento_mas_los_eventos_camera(plan10):
    # 9 segmentos + 2 eventos CAMERA
    assert len(plan10["shots"]) == 11


def test_los_encuadres_van_ordenados_y_empiezan_en_cero(plan10):
    ats = [s["at"] for s in plan10["shots"]]
    assert ats == sorted(ats)
    assert ats[0] == 0.0, "el primer encuadre arranca la pieza, no su primera palabra"


def test_la_camara_se_traduce_por_la_escalera_del_perfil(plan10):
    # Segmento 0: CLOSE -> 1.20
    assert plan10["shots"][0]["zoom"] == 1.20
    assert plan10["shots"][0]["kind"] == "full"


def test_el_evento_camera_emite_su_propio_encuadre(plan10, edl10):
    # El CAMERA de la palabra 97 baja a MEDIUM a mitad del segmento 7.
    t = q(edl10.wt.at(97))
    sh = next(s for s in plan10["shots"] if s["at"] == t)
    assert sh["zoom"] == 1.12


def test_las_keywords_salen_de_los_eventos_keyword(plan10):
    ks = plan10["keywords"]
    assert ks == sorted(set(ks)), "ordenadas y sin repetir, para que el plan sea estable"
    assert "CONTESTÓ" in ks and "PRIMERO" in ks


def test_el_minimo_no_emite_visuales_ni_efectos(plan10):
    assert plan10["visuals"] == [] and plan10["sfx"] == [] and plan10["cards"] == []


# ── determinismo ────────────────────────────────────────────────────────────
def test_compilar_dos_veces_da_el_mismo_dict(edl10, style):
    assert compile_edl(edl10, style) == compile_edl(edl10, style)


def test_el_json_escrito_es_byte_identico(plan10, tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    write_plan(plan10, a)
    write_plan(plan10, b)
    assert a.read_bytes() == b.read_bytes()


def test_el_json_va_con_claves_ordenadas(plan10, tmp_path):
    p = tmp_path / "p.json"
    write_plan(plan10, p)
    raw = p.read_text()
    assert raw.index('"cards"') < raw.index('"format"') < raw.index('"shots"')
    assert raw.endswith("\n")


def test_ningun_tiempo_del_plan_esta_sin_cuantizar(plan10):
    for sh in plan10["shots"]:
        assert sh["at"] == q(sh["at"]), f"{sh} sin cuantizar"


# ── el compilador no improvisa ──────────────────────────────────────────────
def test_un_perfil_inexistente_falla_claro(skill_root):
    with pytest.raises(FileNotFoundError, match="motion-explainer|no-existe"):
        load_style("no-existe", skill_root)
```

- [ ] **Step 4: Correr los tests y verificar que fallan**

```bash
.venv/bin/python -m pytest tests/test_edl_compile.py -v
```

Esperado: FAIL — `ModuleNotFoundError: No module named 'edl_compile'`.

⚠ El módulo se llama `edl_compile` pero el archivo es `edl-compile.py` (guion, para que la CLI case con el resto del pipeline). Crear **también** `edl_compile.py` como módulo real y dejar `edl-compile.py` como envoltorio de una línea:

```python
#!/usr/bin/env python3
from edl_compile import main
main()
```

- [ ] **Step 5: Implementar `edl_compile.py`**

Lo que el implementador **no debe improvisar**:
- `q()` es una **copia literal** de `build-composition.py:81-83`. Si divergen, el EDL y el render dejan de hablar de los mismos frames.
- El primer encuadre va en **0.0**, no en el `start` de la primera palabra: antes de la primera palabra hay imagen y tiene que haber encuadre.
- `keywords` va **ordenada y deduplicada**. Un `set` iterado sin ordenar rompe el determinismo, y es el error más fácil de cometer aquí.
- El compilador **no elige nada**. Traduce: cámara → zoom por tabla, palabra → tiempo por lookup, y ya.

```python
#!/usr/bin/env python3
"""EDL → plan.json. Determinista, y sin decidir nada.

FRONTERA (spec §9): este módulo hace aritmética, lookup, derivación y
aplicación de fórmulas. NO elige objetos, ni instantes, ni si un segmento
merece visual. Si una decisión podría ser razonablemente distinta en manos de
otro editor, no es de aquí.

Mínimo a propósito: emite `keywords` como lista de strings, que es lo que el
motor de captions actual ya consume, así que `build-composition.py` no se toca.
Las captions explícitas llegan en la Tarea 7.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from edl_schema import Edl, EdlError, load_edl

FPS = 30


def q(t: float) -> float:
    """Cuantiza a frame y recorta a 4 decimales.

    Copia literal de build-composition.py. EL ÚNICO punto de cuantización del
    compilador: un segundo sitio que redondee haría que dos rutas dieran
    instantes distintos para la misma palabra.
    """
    return round(round(float(t) * FPS) / FPS, 4)


def load_style(name: str, skill_root: Path) -> dict:
    p = Path(skill_root) / "styles" / f"{name}.json"
    if not p.exists():
        disponibles = sorted(x.stem for x in (Path(skill_root) / "styles").glob("*.json"))
        raise FileNotFoundError(
            f"no existe el style profile '{name}' en {p.parent}. "
            f"Disponibles: {disponibles or '(ninguno)'}")
    return json.loads(p.read_text())


def _shots(edl: Edl, style: dict) -> list[dict]:
    """La capa de metraje. Un encuadre por segmento, más los eventos CAMERA."""
    ladder = style["camera"]["ladder"]
    anchor = style["camera"]["default_anchor"]
    out: list[dict] = []

    def push(at: float, camera: str) -> None:
        if camera == "OFF":
            out.append({"at": q(at), "kind": "off"})
        else:
            out.append({"at": q(at), "kind": "full",
                        "zoom": ladder[camera], "anchor": anchor})

    for i, seg in enumerate(edl.segments):
        # El primer encuadre arranca la PIEZA, no la primera palabra: antes de
        # que él hable ya hay imagen en pantalla.
        start = 0.0 if i == 0 else seg.t(edl.wt)[0]
        push(start, seg.camera)
        for ev in sorted(seg.events, key=lambda e: (e.at_word,)):
            if ev.type == "CAMERA":
                push(ev.t(edl.wt), ev.state.get("camera") or ev.theme or "MEDIUM")

    out.sort(key=lambda s: s["at"])
    return out


def _keywords(edl: Edl) -> list[str]:
    """Las palabras que el motor de captions actual debe resaltar.

    Ordenadas y deduplicadas: un set iterado sin ordenar rompe el determinismo.
    """
    ks: set[str] = set()
    for seg in edl.segments:
        for ev in seg.events:
            if ev.type == "KEYWORD" and ev.words:
                for w in edl.wt.words[ev.words[0]:ev.words[1] + 1]:
                    ks.add(w.text.strip().rstrip(",.:;!?").upper())
    return sorted(ks)


def compile_edl(edl: Edl, style: dict) -> dict:
    """Función PURA: mismas entradas, mismo dict, siempre."""
    return {
        "format": edl.fmt,
        "voice_gain": edl.voice_gain,
        "music": edl.music,
        "keywords": _keywords(edl),
        "shots": _shots(edl, style),
        "cards": [],
        "visuals": [],
        "sfx": [],
        "_": f"generado por edl-compile desde {edl.src.name} — NO editar a mano",
    }


def write_plan(plan: dict, out: Path) -> None:
    Path(out).write_text(
        json.dumps(plan, ensure_ascii=False, indent=2,
                   sort_keys=True, separators=(",", ": ")) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Compila un edl.json a plan.json")
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--piece", required=True)
    ap.add_argument("-o", "--out", type=Path, default=None)
    a = ap.parse_args(argv)

    root = a.project.resolve()
    work = root / "videos" / str(a.piece)
    skill = root / ".claude" / "skills" / "video-tech-premium"

    try:
        edl = load_edl(work / "edl.json", root)
    except EdlError as e:
        print(f"✗ {len(e.problems)} problema(s) en el EDL de la pieza {a.piece}:\n",
              file=sys.stderr)
        for p in e.problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    plan = compile_edl(edl, load_style(edl.style_profile, skill))
    out = a.out or (work / "plan.json")
    write_plan(plan, out)
    print(f"✓ {out}  ·  {len(edl.segments)} segmentos  ·  "
          f"{len(plan['shots'])} encuadres  ·  {len(plan['keywords'])} keywords")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Correr los tests y verificar que pasan**

```bash
.venv/bin/python -m pytest tests/test_edl_compile.py -v
```

Esperado: todos pasan. Si `load_edl` falla, **leer los problemas y arreglar el EDL**, no el validador: para eso están.

- [ ] **Step 7: Compilar y renderizar la pieza 10 de verdad**

```bash
.venv/bin/python scripts/edl-compile.py --project . --piece 10
.venv/bin/python scripts/build-composition.py --project . --piece 10
npx hyperframes check videos/10/public
```

Esperado: `check` con **0 hallazgos**. Si aparece `motion_selector_missing`, borrar `videos/10/public/index.motion.json` y volver a componer.

```bash
npx hyperframes render videos/10/public --skill=talking-head-recut \
  -o videos/10/output.mp4 --fps 30 --sdr
```

Esperado: MP4 de ~44.3 s. Esperar por el **PID concreto**, nunca con `pgrep -f "hyperframes render"` — el propio shell que espera lleva esa cadena y se caza a sí mismo.

- [ ] **Step 8: Verificar sobre el MP4, no sobre el HTML**

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 videos/10/output.mp4
ffmpeg -v info -i videos/10/output.mp4 -vf blackdetect=d=0.05:pix_th=0.03 -f null - 2>&1 | grep -i black || echo "sin negro real"
```

Esperado: duración ≈ 44.3 s y **sin negro real**. (Con el `pix_th` por defecto de 0.10 salta el propio suelo grafito, que es luma 12 — por eso 0.03.)

- [ ] **Step 9: Commit**

```bash
git add .claude/skills/video-tech-premium/scripts/edl_compile.py \
        .claude/skills/video-tech-premium/scripts/edl-compile.py \
        .claude/skills/video-tech-premium/styles/motion-explainer.json \
        videos/10/edl.json videos/10/plan.json tests/test_edl_compile.py
git commit -m "feat(edl): compilador mínimo — la pieza 10 renderiza desde un EDL

Primer MP4 generado desde un edl.json, y build-composition.py sin tocar
una línea: el EDL de esta tarea es todo A_ROLL y el compilador emite
keywords como lista de strings, que es lo que el motor de captions actual
ya consume.

compile_edl es una función pura y write_plan escribe con sort_keys, así
que compilar dos veces da bytes idénticos. q() es copia literal de la de
build-composition.py: si divergieran, el EDL y el render dejarían de
hablar de los mismos frames.

El style profile ya existe como datos, todavía sin gates.

Los 9 segmentos salen de los límites de frase reales del transcript."
```

---

## Task 4: Métricas de estilo y motor de gates

Aquí se cumple el requisito arquitectónico: **el compilador calcula métricas, el perfil decide umbrales y severidad.** Un `styles/clean.json` mañana debe ser un archivo nuevo y **cero líneas** de compilador.

**Files:**
- Create: `.claude/skills/video-tech-premium/scripts/edl_metrics.py`
- Create: `tests/test_edl_metrics.py`
- Modify: `.claude/skills/video-tech-premium/styles/motion-explainer.json` (rellenar `gates`)
- Modify: `.claude/skills/video-tech-premium/scripts/edl_compile.py` (fase 5 + informe)

**Interfaces:**
- Consumes: `edl_schema.Edl`, `derive_stages`
- Produces:
  - `MACRO_EVENTS`, `MICRO_EVENTS` — `frozenset`s
  - `measure(edl: Edl) -> dict[str, float]` — la **lista fija y cerrada** de métricas
  - `run_gates(metrics: dict, style: dict) -> list[Finding]` con `Finding.metric`, `.severity` (`"fail"`/`"warn"`), `.message`
  - `GateError(Exception)` con `.findings`

- [ ] **Step 1: Rellenar los `gates` del perfil**

```json
"gates": [
  { "metric": "presenter_share",          "in": [0.45, 0.60],
    "warn_in": [0.35, 0.70], "fail_in": [0.20, 0.85] },
  { "metric": "max_micro_gap",            "max": 2.5,  "severity": "fail" },
  { "metric": "max_macro_gap",            "max": 4.5,  "severity": "fail" },
  { "metric": "punch_zoom_count",         "max": 2,    "severity": "warn" },
  { "metric": "theme_change_count",       "max": 2,    "severity": "warn" },
  { "metric": "mega_count",               "max": 1,    "severity": "warn" },
  { "metric": "special_transition_ratio", "max": 0.20, "severity": "warn" },
  { "metric": "sfx_per_macro",            "max": 0.50, "severity": "warn" },
  { "metric": "decorative_reason_count",  "max": 0,    "severity": "warn" }
]
```

- [ ] **Step 2: Escribir el test que falla**

`tests/test_edl_metrics.py`.

```python
import pytest
from edl_metrics import measure, run_gates


@pytest.fixture(scope="module")
def m10(edl10):
    return measure(edl10)


# ── presencia del presentador ───────────────────────────────────────────────
def test_una_pieza_toda_a_roll_da_presencia_1(m10):
    assert m10["presenter_share"] == pytest.approx(1.0)


def test_ui_demo_sale_del_denominador(edl10, monkeypatch):
    """El caso del reel de ChatGPT: 15 s de demo legítima no deben obligar a
    volver al presentador para cuadrar un porcentaje."""
    segs = list(edl10.segments)
    segs[5] = type(segs[5])(**{**segs[5].__dict__, "scene_type": "UI_DEMO",
                               "representation_type": "INTERFACE", "camera": "OFF"})
    edl = type(edl10)(**{**edl10.__dict__, "segments": tuple(segs)})
    m = measure(edl)
    assert m["presenter_share"] == pytest.approx(1.0)
    assert m["presenter_share_raw"] < 1.0


# ── ritmo ───────────────────────────────────────────────────────────────────
def test_los_captions_solos_no_satisfacen_el_gate_macro(m10):
    """La razón de existir de los dos niveles: si micro y macro fueran lo
    mismo, un plano fijo de 15 s pasaría por cambiar de subtítulo."""
    assert m10["max_macro_gap"] > m10["max_micro_gap"]


def test_el_hueco_macro_de_la_pieza_10_cabe_en_el_gate(m10):
    assert m10["max_macro_gap"] <= 4.5, (
        f"hay {m10['max_macro_gap']:.2f} s sin un cambio macro")


def test_un_segmento_con_hold_no_cuenta_para_el_gate(edl10):
    """El brief pide quietud antes del clímax; una quietud deliberada debe
    estar ESCRITA, no colada en silencio."""
    segs = list(edl10.segments)
    segs[7] = type(segs[7])(**{**segs[7].__dict__, "events": (), "hold": True})
    edl = type(edl10)(**{**edl10.__dict__, "segments": tuple(segs)})
    assert measure(edl)["max_macro_gap"] <= 4.5


# ── el motor genérico ───────────────────────────────────────────────────────
def test_un_gate_max_superado_produce_un_finding():
    style = {"gates": [{"metric": "punch_zoom_count", "max": 2, "severity": "warn"}]}
    fs = run_gates({"punch_zoom_count": 5}, style)
    assert len(fs) == 1 and fs[0].severity == "warn" and "5" in fs[0].message


def test_una_banda_produce_warn_o_fail_segun_lo_lejos_que_este():
    style = {"gates": [{"metric": "presenter_share", "in": [0.45, 0.60],
                        "warn_in": [0.35, 0.70], "fail_in": [0.20, 0.85]}]}
    assert run_gates({"presenter_share": 0.50}, style) == []
    assert run_gates({"presenter_share": 0.32}, style)[0].severity == "warn"
    assert run_gates({"presenter_share": 0.10}, style)[0].severity == "fail"


def test_un_perfil_sin_gates_no_produce_nada():
    assert run_gates({"punch_zoom_count": 99}, {"gates": []}) == []


def test_una_metrica_desconocida_en_el_perfil_falla_claro():
    """Un gate sobre una métrica que nadie calcula es un typo silencioso."""
    with pytest.raises(KeyError, match="metrica_inventada"):
        run_gates({"punch_zoom_count": 1},
                  {"gates": [{"metric": "metrica_inventada", "max": 1}]})


def test_anadir_un_gate_no_toca_el_compilador():
    """El requisito arquitectónico: umbrales y severidad son DATOS."""
    style = {"gates": [{"metric": "theme_change_count", "max": 0, "severity": "fail"}]}
    assert run_gates({"theme_change_count": 1}, style)[0].severity == "fail"
```

Añadir a `tests/conftest.py`:

```python
@pytest.fixture(scope="session")
def edl10(project_root):
    from edl_schema import load_edl
    return load_edl(project_root / "videos" / "10" / "edl.json", project_root)
```

- [ ] **Step 3: Correr los tests y verificar que fallan**

```bash
.venv/bin/python -m pytest tests/test_edl_metrics.py -v
```

Esperado: FAIL — `ModuleNotFoundError: No module named 'edl_metrics'`.

- [ ] **Step 4: Implementar `edl_metrics.py`**

```python
#!/usr/bin/env python3
"""Métricas de estilo y motor genérico de gates.

LA SEPARACIÓN QUE IMPORTA: aquí se CALCULAN métricas — una lista fija y
cerrada, en código. Los UMBRALES y la SEVERIDAD viven en `styles/*.json`.
Un perfil nuevo es un archivo nuevo y cero líneas de este módulo.
"""
from __future__ import annotations

from dataclasses import dataclass

from edl_schema import Edl, derive_stages

# Un cambio macro es un cambio de MUNDO; uno micro, de lectura.
MACRO_EVENTS = frozenset({"CAMERA", "OBJECT_IN", "OBJECT_EXIT", "OBJECT_STATE",
                          "STAGE_CLEAR", "THEME_CHANGE", "TYPE_BEAT", "UI_ACTION"})
MICRO_EVENTS = frozenset({"CAPTION", "KEYWORD"})
# SFX no cuenta en ninguno: no es un cambio visual.

PRESENTER_TYPES = frozenset({"A_ROLL", "A_ROLL_ICON", "CTA"})

DECORATIVE = ("mantener la atención", "dar dinamismo", "que no sea aburrido",
              "rellenar", "para que se vea bien", "dinamismo")


@dataclass(frozen=True)
class Finding:
    metric: str
    severity: str          # "fail" | "warn"
    message: str


def _beats(edl: Edl, kinds: frozenset) -> list[float]:
    """Instantes de cambio visual, más los límites de segmento (SCENE)."""
    ts = [0.0]
    for seg in edl.segments:
        ts.append(seg.t(edl.wt)[0])          # SCENE: el límite es macro y micro
        for ev in seg.events:
            if ev.type in kinds:
                ts.append(ev.t(edl.wt))
    ts.append(edl.wt.duration)
    return sorted(ts)


def _max_gap(edl: Edl, kinds: frozenset) -> float:
    """Hueco mayor, saltando los segmentos con `hold` autorizado."""
    holds = [seg.t(edl.wt) for seg in edl.segments if seg.hold]
    ts = _beats(edl, kinds)
    peor = 0.0
    for a, b in zip(ts, ts[1:]):
        if any(ha <= a and b <= hb for ha, hb in holds):
            continue
        peor = max(peor, b - a)
    return round(peor, 4)


def measure(edl: Edl) -> dict[str, float]:
    """La lista FIJA de métricas. Añadir una es tocar código, a propósito."""
    total = edl.wt.duration
    dur = {}
    for seg in edl.segments:
        a, b = seg.t(edl.wt)
        dur[seg.scene_type] = dur.get(seg.scene_type, 0.0) + (b - a)

    presenter = sum(v for k, v in dur.items() if k in PRESENTER_TYPES)
    ui = dur.get("UI_DEMO", 0.0)
    # `exclude_ui_demo`: la demostración de producto sale del denominador.
    ajustado = total - ui

    macro = sum(1 for s in edl.segments for e in s.events if e.type in MACRO_EVENTS)
    sfx = sum(1 for s in edl.segments for e in s.events if e.type == "SFX")
    especiales = sum(1 for s in edl.segments if s.transition_in != "CUT")
    limites = max(1, len(edl.segments) - 1)

    return {
        "presenter_share": round(presenter / ajustado, 4) if ajustado > 0 else 0.0,
        "presenter_share_raw": round(presenter / total, 4) if total > 0 else 0.0,
        "max_micro_gap": _max_gap(edl, MACRO_EVENTS | MICRO_EVENTS),
        "max_macro_gap": _max_gap(edl, MACRO_EVENTS),
        "punch_zoom_count": sum(
            1 for s in edl.segments for e in s.events
            if e.type == "CAMERA" and e.preset == "punch-zoom"),
        "theme_change_count": sum(
            1 for s in edl.segments for e in s.events if e.type == "THEME_CHANGE"),
        "mega_count": sum(
            1 for s in edl.segments for e in s.events
            if e.type == "TYPE_BEAT" and "mega" in (e.roles or {}).values()),
        "special_transition_ratio": round(especiales / limites, 4),
        "sfx_per_macro": round(sfx / macro, 4) if macro else 0.0,
        "decorative_reason_count": sum(
            1 for s in edl.segments
            if any(d in s.reason.lower() for d in DECORATIVE)),
        "stage_count": float(len(derive_stages(edl.segments))),
        "segment_count": float(len(edl.segments)),
    }


def run_gates(metrics: dict, style: dict) -> list[Finding]:
    out: list[Finding] = []
    for g in style.get("gates", []):
        name = g["metric"]
        if name not in metrics:
            raise KeyError(
                f"el perfil declara un gate sobre '{name}', que no es una métrica "
                f"calculada. Disponibles: {sorted(metrics)}")
        v = metrics[name]

        if "max" in g and v > g["max"]:
            out.append(Finding(name, g.get("severity", "warn"),
                               f"{name} = {v} supera el máximo {g['max']}"))
        if "min" in g and v < g["min"]:
            out.append(Finding(name, g.get("severity", "warn"),
                               f"{name} = {v} no llega al mínimo {g['min']}"))
        if "in" in g:
            lo, hi = g["in"]
            if not (lo <= v <= hi):
                fl, fh = g.get("fail_in", (float("-inf"), float("inf")))
                wl, wh = g.get("warn_in", g["in"])
                sev = "fail" if not (fl <= v <= fh) else (
                    "warn" if not (wl <= v <= wh) else "warn")
                out.append(Finding(name, sev,
                                   f"{name} = {v} fuera de la banda objetivo [{lo}, {hi}]"))
    return out
```

- [ ] **Step 5: Enganchar la fase 5 en el compilador**

En `edl_compile.py`, dentro de `main()` y **después** de `load_edl`:

```python
from edl_metrics import measure, run_gates

    metrics = measure(edl)
    findings = run_gates(metrics, style)
    for f in findings:
        marca = "✗" if f.severity == "fail" else "⚠"
        print(f"  {marca} {f.message}", file=sys.stderr)
    if any(f.severity == "fail" for f in findings):
        print("\n✗ gates de estilo en fallo; el plan no se escribe", file=sys.stderr)
        return 1

    print("  métricas: " + " · ".join(
        f"{k} {v}" for k, v in sorted(metrics.items())))
```

- [ ] **Step 6: Correr los tests y verificar que pasan**

```bash
.venv/bin/python -m pytest tests/ -q
```

Esperado: 0 fallos.

- [ ] **Step 7: Comprobar los gates sobre la pieza real**

```bash
.venv/bin/python scripts/edl-compile.py --project . --piece 10
```

Esperado: compila e imprime las métricas. **`presenter_share` saldrá en 1.0 y disparará un warn** — es correcto: la pieza es todo `A_ROLL` y baja a la banda cuando lleguen los Motion Stage de las Tareas 6 y 9. Si `max_macro_gap` supera 4.5 s, añadir un evento `CAMERA` en el segmento largo que lo cause; el mensaje dice cuál.

- [ ] **Step 8: Commit**

```bash
git add .claude/skills/video-tech-premium/scripts/edl_metrics.py \
        .claude/skills/video-tech-premium/scripts/edl_compile.py \
        .claude/skills/video-tech-premium/styles/motion-explainer.json \
        tests/test_edl_metrics.py tests/conftest.py
git commit -m "feat(edl): métricas de estilo y motor genérico de gates

El compilador calcula métricas (lista fija, en código); el perfil decide
umbrales y severidad (datos). Un styles/clean.json mañana es un archivo
nuevo y cero líneas de compilador.

Ritmo en dos niveles: si micro y macro fueran lo mismo, un plano fijo de
15 s pasaría el gate por cambiar de subtítulo. Los segmentos con hold
quedan exentos, porque una quietud deliberada debe estar escrita.

presenter_share excluye UI_DEMO del denominador: 15 s de demostración
legítima no deben obligar a volver al presentador para cuadrar un
porcentaje.

Un gate sobre una métrica inexistente falla en vez de ignorarse en
silencio."
```

---
## Task 5: Motion Stage — el escenario persistente

El stage sale como **una sola entrada de `visuals`** que abarca toda su serie de segmentos. Eso cierra la clase de bug que motivó `check_no_black()`: con un único `fade_in` y un único `fade_out` no hay cruces entre takeovers donde el frame caiga al suelo.

**Files:**
- Create: `.claude/skills/video-tech-premium/scripts/objects.py`
- Create: `tests/test_objects.py`
- Modify: `scripts/tokens.py` (+ `spotlight()`, `grain()`, `THEME`, `SLOTS`, `KINETIC`)
- Modify: `scripts/build-composition.py` — **cambio quirúrgico nº 1**, una línea
- Modify: `scripts/edl_schema.py` (validar zona segura de slots)

**Interfaces:**
- Consumes: `tokens.C`, `tokens.vignette`, `tokens.grid`, `tokens.contrast`
- Produces:
  - `tokens.spotlight(alpha: float) -> str` · `tokens.grain(seed: int, opacity: float) -> str`
  - `tokens.THEME: dict[str, dict]` — `primary` · `problem` · `warning` · `success` · `neutral`
  - `tokens.SLOTS: dict[str, tuple[int, int]]` — coordenadas **horneadas** del lienzo REEL
  - `tokens.KINETIC: dict[str, dict]` — px por formato y nivel
  - `objects.motion_stage(cid, theme, objects, at, **kw) -> tuple[str, str, list]` — el trío `(css, html, anims)` que `build-composition.py` ya espera de cualquier mockup
  - `objects.REGISTRY: dict[str, callable]`

- [ ] **Step 1: Escribir el test que falla**

`tests/test_objects.py`.

```python
import pytest
import tokens
from objects import REGISTRY, motion_stage


# ── slots ───────────────────────────────────────────────────────────────────
def test_los_slots_estan_horneados_y_son_enteros():
    """Calculados en Python al compilar, nunca con cos/sin en el navegador:
    el contrato de determinismo lo exige."""
    for name, (x, y) in tokens.SLOTS.items():
        assert isinstance(x, int) and isinstance(y, int), name


def test_ningun_slot_invade_la_zona_de_la_plataforma():
    """En REEL el 20% inferior lo pinta la app. Hoy solo las captions lo
    respetan; un objeto en orbit-5 puede caer dentro y nada lo comprueba."""
    limite = int(1920 * 0.80)
    for name, (_, y) in tokens.SLOTS.items():
        assert y < limite, f"{name} cae en y{y}, dentro de la interfaz de la app"


def test_el_centro_esta_donde_manda_la_bitacora():
    """Un mockup corto centrado deja medio frame vacío: el bloque va hacia
    y 820-880, no al centro del lienzo."""
    _, cy = tokens.SLOTS["center"]
    assert 820 <= cy <= 880


def test_hay_seis_orbitas():
    assert sum(1 for k in tokens.SLOTS if k.startswith("orbit-")) == 6


# ── spotlight ───────────────────────────────────────────────────────────────
def test_el_spotlight_no_rompe_el_contraste_del_violeta_texto():
    """Medido: aclara el fondo y a alpha 0.07 el violet_hi cae a 5.77."""
    lit = tokens.lift(tokens.C["bg"], 0.05)
    assert tokens.contrast(tokens.C["violet_hi"], lit) >= 6.0


def test_un_spotlight_demasiado_fuerte_falla():
    with pytest.raises(ValueError, match="0.05"):
        tokens.spotlight(0.12)


# ── grain ───────────────────────────────────────────────────────────────────
def test_el_grain_lleva_semilla_fija():
    """Math.random sin semilla está prohibido; y un grain ANIMADO
    desincronizaría al muestrear frames en paralelo."""
    a, b = tokens.grain(seed=7), tokens.grain(seed=7)
    assert a == b and 'seed="7"' in a
    assert "animate" not in a.lower()


# ── el stage ────────────────────────────────────────────────────────────────
def test_el_stage_devuelve_el_trio_que_espera_build_composition():
    css, html, anims = motion_stage("stage-a", theme="primary", objects=[], at=[])
    assert isinstance(css, str) and isinstance(html, str) and isinstance(anims, list)


def test_el_suelo_del_stage_es_un_elemento_del_dom():
    """Trampa nº1 del renderer: el background CSS de la página se descarta."""
    _, html, _ = motion_stage("stage-a", theme="primary", objects=[], at=[])
    assert 'class="stage-ground"' in html


def test_el_tema_problem_tiñe_el_acento_pero_no_el_texto():
    css_p, _, _ = motion_stage("s", theme="primary", objects=[], at=[])
    css_x, _, _ = motion_stage("s", theme="problem", objects=[], at=[])
    assert tokens.C["alert"] in css_x and tokens.C["alert"] not in css_p
    assert tokens.C["text"] in css_x, "el blanco del texto no depende del tema"


def test_compilar_el_mismo_stage_dos_veces_da_lo_mismo():
    a = motion_stage("s", theme="primary", objects=[], at=[])
    b = motion_stage("s", theme="primary", objects=[], at=[])
    assert a == b


def test_un_tema_inexistente_falla_claro():
    with pytest.raises(KeyError, match="turquesa"):
        motion_stage("s", theme="turquesa", objects=[], at=[])


def test_el_registry_expone_motion_stage():
    assert REGISTRY["motion_stage"] is motion_stage
```

- [ ] **Step 2: Correr el test y verificar que falla**

```bash
.venv/bin/python -m pytest tests/test_objects.py -v
```

Esperado: FAIL — `ModuleNotFoundError: No module named 'objects'`.

- [ ] **Step 3: Ampliar `tokens.py`**

Añadir al final, **sin tocar nada de lo existente**:

```python
# ── el Motion Stage ───────────────────────────────────────────────────────────
def lift(hex_bg: str, alpha: float) -> str:
    """El color que resulta de poner blanco a `alpha` encima de `hex_bg`.

    Sirve para MEDIR el contraste dentro de un stage iluminado antes de
    renderizar, que es cuando cuesta barato.
    """
    b = hex_bg.lstrip("#")
    rgb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(round(c * (1 - alpha) + 255 * alpha) for c in rgb)


# Medido: a alpha 0.05 el violet_hi sobre el fondo iluminado da 6.08:1; a 0.07
# cae a 5.77 y deja de aguantar texto normal. El techo no es una opinión.
SPOTLIGHT_MAX = 0.05


def spotlight(alpha: float = SPOTLIGHT_MAX) -> str:
    """Foco cenital centrado. Empuja la mirada arriba, donde vive el objeto."""
    if alpha > SPOTLIGHT_MAX:
        raise ValueError(
            f"spotlight alpha {alpha} pasa del techo medido {SPOTLIGHT_MAX}: por "
            f"encima, el violeta como texto cae por debajo de AA sobre el fondo "
            f"iluminado")
    return (f"radial-gradient(120% 62% at 50% 0%, rgba(255,255,255,{alpha}) 0%, "
            f"rgba(255,255,255,0) 58%)")


def grain(seed: int = 7, opacity: float = 0.035) -> str:
    """Grano como data-URI SVG con SEMILLA FIJA y filtro ESTÁTICO.

    Es la única forma determinista: `Math.random` sin semilla está prohibido por
    el contrato de render, y un grano animado desincronizaría en cuanto el
    renderer muestree frames en paralelo.
    """
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'>"
           f"<filter id='g'><feTurbulence type='fractalNoise' baseFrequency='0.82' "
           f"numOctaves='2' seed=\"{seed}\"/></filter>"
           f"<rect width='160' height='160' filter='url(#g)' opacity='{opacity}'/>"
           f"</svg>")
    from urllib.parse import quote
    return f"url(\"data:image/svg+xml,{quote(svg)}\")"


# El tema cambia ACENTO, relleno y glow. Nunca el color del texto: si lo
# cambiara, todo el trabajo de legibilidad habría que re-litigarlo cinco veces.
THEME = {
    "primary": {"accent": C["violet"], "accent_text": C["violet_hi"],
                "fill": FILL["violet"], "glow": GLOW},
    "problem": {"accent": C["alert"], "accent_text": C["alert"],
                "fill": FILL["alert"],
                "glow": "0 0 0 1px rgba(255,90,90,.32), 0 18px 60px rgba(255,90,90,.20)"},
    "warning": {"accent": C["warn"], "accent_text": C["warn"],
                "fill": FILL["warn"],
                "glow": "0 0 0 1px rgba(255,184,77,.30), 0 18px 60px rgba(255,184,77,.18)"},
    "success": {"accent": C["go"], "accent_text": C["go"], "fill": FILL["go"],
                "glow": "0 0 0 1px rgba(52,227,155,.30), 0 18px 60px rgba(52,227,155,.18)"},
    "neutral": {"accent": C["text"], "accent_text": C["text"], "fill": FILL["white"],
                "glow": SHADOW},
}

# ⚠ Sobre un relleno `warn` va TINTA, nunca blanco: text/warn = 1.72:1. Misma
# regla que ya está escrita para el verde (bg/go = 11.74:1).
INK_ON_FILL = {"warning": C["bg"], "success": C["bg"]}

# Coordenadas HORNEADAS del lienzo REEL 1080×1920. Se calculan aquí, en Python,
# no con cos/sin en el navegador. El centro va hacia y 820-880 porque un bloque
# centrado en el lienzo deja medio frame vacío bajo el PiP.
def _bake_slots(cx=540, cy=850, rx=330, ry=250):
    import math
    s = {"center": (cx, cy)}
    for i in range(6):
        a = math.radians(-90 + i * 60)
        s[f"orbit-{i+1}"] = (round(cx + rx * math.cos(a)), round(cy + ry * math.sin(a)))
    for i in range(4):
        s[f"stack-{i+1}"] = (cx, round(cy - 240 + i * 160))
    return s


SLOTS = _bake_slots()

# Escala dedicada de kinetic typography. `hero` cae EXACTAMENTE en TYPE.display
# de cada formato, así que extiende la escala verificada en vez de inventar una.
KINETIC = {
    "REEL":    {"small": 60, "medium": 93, "hero": 132, "mega": 168},
    "YOUTUBE": {"small": 51, "medium": 79, "hero": 112, "mega": 143},
}
```

- [ ] **Step 4: Implementar `objects.py`**

Sigue el patrón exacto de `mockups.py`: cada función recibe `cid` y devuelve `(css, html, anims)`. En esta tarea el stage se emite **vacío** (suelo, viñeta, grid, spotlight y grano); los objetos entran en las Tareas 6 y 9.

```python
#!/usr/bin/env python3
"""Objetos con estado y el escenario que los sostiene.

Mismo contrato que `mockups.py`: cada función devuelve `(css, html, anims)`.

EL STAGE ES UNO, NO UNO POR SEGMENTO. La serie entera de segmentos contiguos
sale como una sola entrada de `visuals`, con un `fade_in` al principio y un
`fade_out` al final. Dos takeovers seguidos abrían un hueco de 0.15-0.25 s en el
cruce que se leía como un fallo — la razón de existir de `check_no_black()`.
Con un stage continuo esa clase de bug no puede ocurrir.
"""
from __future__ import annotations

import tokens as t


def motion_stage(cid: str, theme: str = "primary", objects=None, at=None,
                 spotlight_alpha: float = t.SPOTLIGHT_MAX, seed: int = 7, **_):
    if theme not in t.THEME:
        raise KeyError(f"tema '{theme}' desconocido; hay {sorted(t.THEME)}")
    th = t.THEME[theme]
    objects, at = list(objects or []), list(at or [])

    css = f"""
/* Motion Stage — suelo continuo de una serie de segmentos.
   El fondo va en un ELEMENTO del DOM: el `background` de la página se descarta
   en el render (trampa nº1), y el fill de una escena a pantalla completa nunca
   va en la raíz de la composición. */
#{cid} .stage-ground{{position:absolute;inset:0;
  background:{t.spotlight(spotlight_alpha)},{t.grid()},{t.vignette()}}}
#{cid} .stage-grain{{position:absolute;inset:0;pointer-events:none;
  background-image:{t.grain(seed)};background-repeat:repeat}}
#{cid} .stage-plane{{position:absolute;inset:0}}
#{cid} .obj{{position:absolute;display:block;opacity:0;
  transform-origin:50% 50%;filter:drop-shadow({t.SHADOW.split(',')[0]})}}
#{cid} .obj.accent{{color:{th['accent_text']}}}
#{cid} .obj .fill{{background:{th['fill']}}}
#{cid} .obj.hero{{box-shadow:{th['glow']}}}
#{cid} .stage-type{{color:{t.C['text']};font-family:{t.FONT};font-weight:900}}
"""
    cuerpo = "".join(o["html"] for o in objects)
    html = (f'<div class="stage-ground"></div>'
            f'<div class="stage-plane">{cuerpo}</div>'
            f'<div class="stage-grain"></div>')

    anims: list = []
    for o in objects:
        anims.extend(o.get("anims", []))
    for op in at:
        anims.extend(op.get("anims", []))
    return css, html, anims


REGISTRY = {"motion_stage": motion_stage}
```

- [ ] **Step 5: Cambio quirúrgico nº 1 en `build-composition.py`**

En el dict de despacho de mockups (~línea 386), añadir **una línea**:

```python
        import objects
        MOCKS = {
            "app_switch": mockups.app_switch,
            "keyword_hero": mockups.keyword_hero,
            # … el resto, sin tocar …
            "motion_stage": objects.motion_stage,      # ← ÚNICA línea nueva
        }
```

- [ ] **Step 6: Validar la zona segura de slots en CORE**

En `edl_schema.py`, dentro de `load_edl`, junto al resto de validaciones:

```python
    import tokens as _t
    for si, seg in enumerate(segments):
        for ev in seg.events:
            if ev.type == "OBJECT_IN" and ev.slot:
                if ev.slot not in _t.SLOTS:
                    problems.append(
                        f"segmento {si}: slot '{ev.slot}' no existe; hay "
                        f"{sorted(_t.SLOTS)}")
```

Y añadir a `tests/test_edl_schema.py`:

```python
def test_slot_inexistente_falla(write_edl, edl_min):
    data = _stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "asset": "object:clock@1",
         "instanceId": "c", "slot": "orbit-99"}])
    assert "no existe" in problems_of(write_edl, data)
```

- [ ] **Step 7: Correr la suite entera**

```bash
.venv/bin/python -m pytest tests/ -q
```

Esperado: 0 fallos.

- [ ] **Step 8: Commit**

```bash
git add .claude/skills/video-tech-premium/scripts/objects.py \
        .claude/skills/video-tech-premium/scripts/tokens.py \
        .claude/skills/video-tech-premium/scripts/build-composition.py \
        .claude/skills/video-tech-premium/scripts/edl_schema.py \
        tests/test_objects.py tests/test_edl_schema.py
git commit -m "feat(stage): Motion Stage continuo con spotlight, grano y temas

El stage abarca su serie entera de segmentos como UNA entrada de visuals:
un fade_in y un fade_out para todo. Dos takeovers seguidos abrían un hueco
de 0.15-0.25 s en el cruce, que es lo que check_no_black() existe para
cazar; con un stage continuo esa clase de bug no puede ocurrir.

El spotlight tiene techo MEDIDO (alpha 0.05): por encima, el violeta como
texto cae por debajo de AA sobre el fondo iluminado. El grano lleva semilla
fija y filtro estático, que es la única forma determinista.

Los slots se hornean en Python, nunca con cos/sin en el navegador, y ahora
CORE valida que ninguno invada el 20% inferior que pinta la plataforma:
hoy solo las captions lo respetan.

Sobre relleno ámbar va tinta, no blanco: text/warn = 1.72:1.

build-composition.py: UNA línea en el dict de despacho."
```

---

## Task 6: El reloj — `OBJECT_STATE`, `hands-sweep` y `OBJECT_MATCH_CUT`

El caso que demuestra el principio central: no se busca otro asset, **se transforma el mismo objeto**.

**Files:**
- Modify: `scripts/objects.py` (+ `clock`, `hand_angles`)
- Modify: `scripts/edl_compile.py` (emitir stages como `visuals`)
- Modify: `videos/10/edl.json` (segmentos 1 y 2 → `MOTION_STAGE`)
- Modify: `tests/test_objects.py`, `tests/test_edl_compile.py`

**Interfaces:**
- Produces:
  - `objects.hand_angles(desde: str, hasta: str) -> dict` → `{"hour_from", "hour_to", "minute_from", "minute_to"}`, **siempre hacia delante**
  - `objects.clock(cid, iid, state, slot) -> dict` → `{"html", "anims"}`
  - `edl_compile._visuals(edl, style) -> list[dict]` — una entrada por stage

- [ ] **Step 1: Escribir el test que falla**

```python
# tests/test_objects.py
from objects import clock, hand_angles


def test_las_agujas_van_siempre_hacia_delante():
    """330° -> 210° es el camino corto y son -120°: el reloj iría HACIA ATRÁS,
    y ocho horas perdidas se leerían como ocho horas recuperadas."""
    a = hand_angles("11:00", "19:00")
    assert a["hour_from"] == 330 and a["hour_to"] == 570      # +240°, horario
    assert a["minute_from"] == 0 and a["minute_to"] == 2880   # 8 vueltas
    assert a["hour_to"] > a["hour_from"] and a["minute_to"] > a["minute_from"]


def test_cruzar_medianoche_tambien_va_hacia_delante():
    a = hand_angles("23:30", "01:15")
    assert a["hour_to"] > a["hour_from"]


def test_un_salto_de_minutos_mueve_las_dos_agujas():
    a = hand_angles("11:00", "11:45")
    assert a["minute_to"] - a["minute_from"] == 270           # 45 min × 6°
    assert a["hour_to"] - a["hour_from"] == pytest.approx(22.5)


def test_el_mismo_estado_no_mueve_nada():
    a = hand_angles("11:00", "11:00")
    assert a["hour_to"] == a["hour_from"]


def test_una_hora_mal_formada_falla_claro():
    with pytest.raises(ValueError, match="HH:MM"):
        hand_angles("11:00", "las siete")


def test_el_reloj_marca_su_estado_inicial():
    o = clock("stage-a", "clock-main", {"time": "11:00"}, "center")
    assert 'id="stage-a-clock-main"' in o["html"]
    assert "rotate(330" in o["html"], "la hora inicial se hornea, no se anima"
```

```python
# tests/test_edl_compile.py
def test_un_stage_sale_como_UNA_entrada_de_visuals(plan10):
    """La serie contigua entera, no una entrada por segmento."""
    stages = [v for v in plan10["visuals"] if v["mock"][0] == "motion_stage"]
    assert len(stages) == 1
    v = stages[0]
    assert v["start"] == 4.1333 and v["end"] == 11.2


def test_el_off_se_retrasa_por_el_fade_in(plan10):
    """Gotcha #6: un `off` que empieza a la vez que el takeover deja el frame
    vacío durante el fundido."""
    off = next(s for s in plan10["shots"] if s["kind"] == "off")
    assert off["at"] == 4.3333            # 4.1333 + fade_in 0.22, cuantizado


def test_el_estado_del_reloj_se_emite_como_angulos(plan10):
    v = next(v for v in plan10["visuals"] if v["mock"][0] == "motion_stage")
    op = next(o for o in v["mock"][1]["at"] if o["id"] == "clock-main")
    assert op["t"] == 10.3 and op["hour"] == 570 and op["minute"] == 2880
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

```bash
.venv/bin/python -m pytest tests/test_objects.py tests/test_edl_compile.py -v
```

Esperado: FAIL — `cannot import name 'clock'`.

- [ ] **Step 3: Implementar `hand_angles` y `clock` en `objects.py`**

```python
def hand_angles(desde: str, hasta: str) -> dict:
    """Ángulos de las agujas, SIEMPRE hacia delante.

    Que el sentido sea obligatoriamente horario no es un detalle de pulido:
    de 11:00 a 19:00, el camino corto de la aguja horaria es 330° -> 210°, o
    sea -120°, y el reloj iría hacia atrás. Ocho horas PERDIDAS se leerían
    como ocho horas recuperadas — justo lo contrario de lo que dice la frase.

    Se deriva todo de los minutos transcurridos: la minutera gira 6°/min y la
    horaria 0.5°/min, así que ambas salen positivas por construcción.
    """
    def parse(s: str) -> int:
        try:
            h, m = s.split(":")
            h, m = int(h), int(m)
            if not (0 <= h < 24 and 0 <= m < 60):
                raise ValueError
        except Exception:
            raise ValueError(f"hora '{s}' mal formada; se espera HH:MM en 24 h")
        return h * 60 + m

    a, b = parse(desde), parse(hasta)
    transcurridos = (b - a) % (24 * 60)          # cruzar medianoche va hacia delante
    hour_from = (a / 60 % 12) * 30
    return {
        "hour_from": round(hour_from, 3),
        "hour_to": round(hour_from + transcurridos * 0.5, 3),
        "minute_from": round((a % 60) * 6, 3),
        "minute_to": round((a % 60) * 6 + transcurridos * 6, 3),
    }


def clock(cid: str, iid: str, state: dict, slot: str = "center", **_) -> dict:
    """Reloj 2.5D. Las agujas se hornean en su ángulo inicial y se mueven con
    `rotation`, que sí está en el allowlist de propiedades animables."""
    x, y = t.SLOTS[slot]
    a = hand_angles(state.get("time", "12:00"), state.get("time", "12:00"))
    eid = f"{cid}-{iid}"
    html = f"""
<div class="obj" id="{eid}" style="left:{x - 150}px;top:{y - 150}px;
     width:300px;height:300px">
  <svg viewBox="0 0 300 300" width="300" height="300">
    <circle cx="150" cy="150" r="140" fill="{t.C['surface']}"
            stroke="{t.LINE_HI}" stroke-width="2"/>
    <circle cx="150" cy="150" r="120" fill="none" stroke="{t.LINE}" stroke-width="1"/>
    <g id="{eid}-h" style="transform:rotate({a['hour_from']}deg);
       transform-origin:150px 150px">
      <rect x="144" y="78" width="12" height="76" rx="6" fill="{t.C['text']}"/>
    </g>
    <g id="{eid}-m" style="transform:rotate({a['minute_from']}deg);
       transform-origin:150px 150px">
      <rect x="146" y="46" width="8" height="108" rx="4" fill="{t.C['text2']}"/>
    </g>
    <circle cx="150" cy="150" r="10" fill="{t.C['violet']}"/>
  </svg>
</div>"""
    return {"html": html, "anims": [], "eid": eid}


REGISTRY = {"motion_stage": motion_stage, "clock": clock}
```

- [ ] **Step 4: Emitir stages en el compilador**

En `edl_compile.py`, una función `_visuals(edl, style)` que:
1. recorre `derive_stages(edl.segments)`;
2. por cada stage calcula `start` = inicio del primer segmento, `end` = fin del último;
3. construye `objects` desde los `OBJECT_IN` (uno por instancia, con su `state` inicial y su `slot`);
4. construye `at` desde los `OBJECT_STATE`, convirtiendo `state.time` con `hand_angles` **desde el último estado conocido de esa instancia**;
5. emite una entrada `{"id": f"stage-{chr(97+i)}", "role": "takeover", "kind": "mockup", "start": q(...), "end": q(...), "skin": "on-surface", "fade_in": …, "fade_out": …, "mock": ["motion_stage", {...}]}`.

Y en `_shots`, el segmento con `camera: "OFF"` dentro de un stage emite su `off` en **`q(start + fade_in)`**, no en `start` — gotcha #6.

- [ ] **Step 5: Convertir los segmentos 1 y 2 del EDL a `MOTION_STAGE`**

En `videos/10/edl.json`, el segmento `[14, 30]` gana `sceneType: "MOTION_STAGE"`, `representationType: "OBJECT"`, `camera: "OFF"` y un `OBJECT_IN` del reloj en la palabra 18; el segmento `[31, 37]` pasa a `MOTION_STAGE` / `STATE_CHANGE` / `OFF` con `transitionIn: "OBJECT_MATCH_CUT"` y el `OBJECT_STATE` en la palabra 34, tal y como está escrito en §15 de la spec.

- [ ] **Step 6: Correr, compilar, renderizar y mirar el frame**

```bash
.venv/bin/python -m pytest tests/ -q
.venv/bin/python scripts/edl-compile.py --project . --piece 10
.venv/bin/python scripts/build-composition.py --project . --piece 10
npx hyperframes check videos/10/public
npx hyperframes snapshot videos/10/public --at 5.5,9.0,10.5,11.0
```

Esperado: `check` con 0 hallazgos. En los snapshots, el reloj marca **las 11 a los 5.5 s** y **las 7 a los 11.0 s**, y **es el mismo reloj**: no desaparece entre medias.

- [ ] **Step 7: Commit**

```bash
git add -A .claude/skills/video-tech-premium/scripts videos/10/edl.json \
           videos/10/plan.json tests/
git commit -m "feat(stage): el reloj, OBJECT_STATE y el match cut

El caso que demuestra el principio: no se busca otro asset, se transforma
el mismo objeto. clock-main entra a las 11:00 en la palabra 18, sobrevive
el beat de los pacientes, y en la palabra 34 le barren las agujas a las
19:00.

hand_angles deriva ambas agujas de los minutos transcurridos, así que el
giro es positivo por construcción. Importa: 330 -> 210 es el camino corto
y son -120 grados; el reloj iría hacia atrás y ocho horas perdidas se
leerían como ocho horas recuperadas.

El stage sale como una entrada de visuals de 4.1333 a 11.2, y el off se
retrasa hasta start + fade_in para que el cruce no caiga al suelo."
```

---
## Task 7: Captions explícitas, métricas encapsuladas y la keyword nueva

Dos cambios quirúrgicos, y el más delicado de todo el plan: **la keyword crece y eso mueve la zona segura**. El bug ya ocurrió una vez (46 px dentro de la interfaz de la plataforma) y el arreglo tiene que ser una función testeable, no una línea más dentro de 1296.

**Files:**
- Create: `.claude/skills/video-tech-premium/scripts/caption_metrics.py`
- Create: `tests/test_caption_metrics.py`
- Modify: `scripts/build-composition.py` — **cambios quirúrgicos nº 3 y nº 4**
- Modify: `scripts/edl_compile.py` (emitir `captions` explícitas)

**Interfaces:**
- Produces:
  - `caption_metrics.measure_block(words, base_size, keyword_range, fmt, canvas_h) -> dict` → `{"n_lines", "max_size", "line_h", "floor_top", "width"}`
  - `caption_metrics.KEYWORD_SCALE_MAX = 1.22`
  - `edl_compile._captions(edl) -> list[dict]` → `{"start", "end", "words", "keyword", "skin"}`

- [ ] **Step 1: Escribir el test que falla**

```python
# tests/test_caption_metrics.py
import pytest
from caption_metrics import KEYWORD_SCALE_MAX, measure_block

H = 1920


def test_un_bloque_corto_es_una_linea():
    m = measure_block(["La", "clínica", "de"], 66, None, "REEL", H)
    assert m["n_lines"] == 1 and m["max_size"] == 66


def test_la_keyword_agranda_la_caja_de_linea():
    """Es lo que rompe floor_top si se calcula con CAPTION_SIZE a secas."""
    sin = measure_block(["simplemente", "contestó", "primero"], 66, None, "REEL", H)
    con = measure_block(["simplemente", "contestó", "primero"], 66, (1, 2), "REEL", H)
    assert con["max_size"] == round(66 * KEYWORD_SCALE_MAX)
    assert con["line_h"] > sin["line_h"]


def test_floor_top_usa_el_tamano_maximo_no_el_base():
    """El bug de los 46 px: dos líneas con keyword grande se metían en la
    interfaz de la plataforma."""
    con = measure_block(["si", "tienes", "una", "clínica", "que", "atiende",
                         "pacientes", "todos", "los", "días"], 66, (3, 3), "REEL", H)
    assert con["n_lines"] == 2
    assert con["floor_top"] == round(H * 0.80) - 2 * con["line_h"]
    sin = measure_block(["si", "tienes", "una", "clínica", "que", "atiende",
                         "pacientes", "todos", "los", "días"], 66, None, "REEL", H)
    assert con["floor_top"] < sin["floor_top"], "la keyword grande baja el techo"


def test_ninguna_tinta_cae_en_el_20_por_ciento_inferior():
    m = measure_block(["comenta", "STOCK", "y", "te", "escribo"], 66, (1, 1), "REEL", H)
    assert m["floor_top"] + m["n_lines"] * m["line_h"] <= round(H * 0.80)


def test_la_keyword_ancha_puede_forzar_dos_lineas():
    """Si el ancho se midiera con el tamaño base, un bloque medido como una
    línea se renderizaría como dos y la cuenta de la zona segura fallaría."""
    base = measure_block(["contestar", "más", "rápido", "siempre"], 66, None, "REEL", H)
    grande = measure_block(["contestar", "más", "rápido", "siempre"], 66, (0, 3),
                           "REEL", H)
    assert grande["width"] > base["width"]


def test_una_escala_de_keyword_por_encima_del_tope_falla():
    with pytest.raises(ValueError, match="1.22"):
        measure_block(["a"], 66, (0, 0), "REEL", H, keyword_scale=1.5)


def test_youtube_usa_su_propia_escala():
    r = measure_block(["hola", "mundo"], 66, None, "REEL", H)
    y = measure_block(["hola", "mundo"], 54, None, "YOUTUBE", 1080)
    assert y["floor_top"] != r["floor_top"]
```

- [ ] **Step 2: Correr el test y verificar que falla**

```bash
.venv/bin/python -m pytest tests/test_caption_metrics.py -v
```

Esperado: FAIL — `ModuleNotFoundError: No module named 'caption_metrics'`.

- [ ] **Step 3: Implementar `caption_metrics.py`**

Reutiliza `measure_font()` de `build-composition.py` (Inter 900 real vía `fontTools`); **no** contar letras.

```python
#!/usr/bin/env python3
"""Métricas de un bloque de subtítulo. Extraídas de build-composition.py.

POR QUÉ EXISTE ESTE MÓDULO. La keyword pasa a ser 1.22× más grande que el
resto del bloque, y eso cambia dos cuentas que antes eran triviales:

  1. `floor_top` usaba `CAPTION_SIZE` para todas las líneas. Con una keyword
     grande la caja de línea crece y un bloque de dos líneas se mete en el 20%
     inferior que pinta la plataforma. Ese bug ya ocurrió: 46 px dentro.
  2. El ancho que decide si el bloque es de una o dos líneas tiene que pesar
     los caracteres de la keyword a SU tamaño, o un bloque medido como una
     línea se renderiza como dos y la cuenta de arriba falla igual.

Encapsularlo aquí lo hace testeable sin renderizar, que es el ciclo caro.
"""
from __future__ import annotations

# Tope medido: a 66 px de base, 1.30 son 86 px y un bloque de dos líneas se
# queda sin presupuesto de zona segura.
KEYWORD_SCALE_MAX = 1.22

LINE_RATIO = 1.14          # el line-height del .cap actual
SAFE_BOTTOM = 0.80         # el 20% inferior lo pinta la plataforma
MARGIN_RATIO = 0.07
MAXW_RATIO = 0.84


def _text_width(words, sizes) -> float:
    """Ancho real con Inter 900. Importado perezosamente para no cargar
    fontTools en los tests que no lo necesitan."""
    from build_composition_fonts import measure_font   # ver Step 4
    total = 0.0
    for w, s in zip(words, sizes):
        adv = measure_font(s)
        total += sum(adv.get(ch, adv.get("?", s * 0.55)) for ch in w) + s * 0.27
    return total


def measure_block(words, base_size: int, keyword_range, fmt: str, canvas_h: int,
                  canvas_w: int = 1080, keyword_scale: float = KEYWORD_SCALE_MAX) -> dict:
    if keyword_scale > KEYWORD_SCALE_MAX:
        raise ValueError(
            f"keyword_scale {keyword_scale} pasa del tope {KEYWORD_SCALE_MAX}: por "
            f"encima, un bloque de dos líneas se queda sin zona segura")

    kw_size = round(base_size * keyword_scale)
    lo, hi = keyword_range if keyword_range else (-1, -2)
    sizes = [kw_size if lo <= i <= hi else base_size for i in range(len(words))]

    max_size = max(sizes) if sizes else base_size
    line_h = round(max_size * LINE_RATIO)
    width = _text_width(words, sizes)
    n_lines = 1 if width <= round(canvas_w * MAXW_RATIO) else 2

    # LA CUENTA QUE IMPORTA: con `max_size`, no con `base_size`.
    floor_top = round(canvas_h * SAFE_BOTTOM) - n_lines * line_h

    return {"n_lines": n_lines, "max_size": max_size, "line_h": line_h,
            "floor_top": floor_top, "width": round(width, 2)}
```

⚠ `measure_font()` vive hoy dentro de `build-composition.py`, que no es importable (guion en el nombre). Extraerlo a `build_composition_fonts.py` y que `build-composition.py` lo importe desde ahí. Es un movimiento sin cambio de comportamiento.

- [ ] **Step 4: Cambios quirúrgicos nº 3 y nº 4 en `build-composition.py`**

**nº 3 — delegar la cuenta.** Donde hoy está:

```python
        n_lines = 1 if width(ch) <= CAPTION_MAXW else 2
        floor_top = round(H * 0.80) - n_lines * round(CAPTION_SIZE * 1.14)
```

pasa a:

```python
        import caption_metrics
        m = caption_metrics.measure_block(
            [u for _, u in ch], CAPTION_SIZE,
            (key_idx, key_idx) if key_idx >= 0 else None, FMT, H, W)
        n_lines, floor_top = m["n_lines"], m["floor_top"]
```

**nº 4 — consumir captions explícitas cuando existan.** Al principio de `build_captions`:

```python
    # El EDL declara sus bloques por rango de palabras. Si el plan los trae, se
    # usan tal cual; si no, se trocean como siempre. Las piezas 1-9 no tienen
    # `captions` en su plan y siguen funcionando igual.
    explicit = plan.get("captions")
    if explicit:
        chunks = [[(words[i], words[i]["text"].strip().rstrip(",.:;!?").upper())
                   for i in range(c["words"][0], c["words"][1] + 1)]
                  for c in explicit]
    else:
        … el troceo actual, sin tocar …
```

Y la keyword deja de elegirse por `is_key(up, KEYWORDS)` cuando hay captions explícitas: viene dada por `c["keyword"]`.

**El CSS de la keyword** pasa de pastilla a texto:

```css
.cap .w.key{{font-size:{round(CAPTION_SIZE * 1.22)}px;font-weight:800;
  color:{C['violet_hi']};text-transform:uppercase}}
```

y las palabras normales pierden el `text-transform: uppercase` global.

- [ ] **Step 5: Emitir `captions` en el compilador**

`_captions(edl)` recorre los eventos `CAPTION`, y por cada uno busca el `KEYWORD` contenido. El `end` de un bloque es el `start` del siguiente menos 0.03 s, o el fin de su última palabra más 0.22 s, lo que sea menor — **la misma regla que el troceo actual**, para no cambiar el ritmo de lectura sin querer.

- [ ] **Step 6: Verificar sobre el MP4, que es donde este bug se ve**

```bash
.venv/bin/python -m pytest tests/ -q
.venv/bin/python scripts/edl-compile.py --project . --piece 10
.venv/bin/python scripts/build-composition.py --project . --piece 10
npx hyperframes check videos/10/public
npx hyperframes render videos/10/public --skill=talking-head-recut \
  -o videos/10/output.mp4 --fps 30 --sdr
```

Extraer los frames de los bloques de **dos líneas con keyword** y medir la tinta más baja:

```bash
ffmpeg -v error -ss 3.2 -i videos/10/output.mp4 -frames:v 1 /tmp/f1.png
.venv/bin/python -c "
import numpy as np
from PIL import Image
a = np.array(Image.open('/tmp/f1.png').convert('L'))
filas = np.where(a.max(axis=1) > 200)[0]
print('tinta más baja en y', filas.max(), '· límite de zona segura', int(1920*0.80))
assert filas.max() <= 1536"
```

Esperado: tinta más baja **≤ y1536**. En las piezas 3 y 4 quedó en y1533 y y1502; si esta sale por encima, el `floor_top` está mal y **no** se arregla con un `plan_override`.

- [ ] **Step 7: Commit**

```bash
git add -A .claude/skills/video-tech-premium/scripts tests/ videos/10/
git commit -m "feat(captions): bloques explícitos, métricas encapsuladas y keyword nueva

Las captions dejan de trocearse solas: el EDL las declara por rango de
palabras, así que la keyword se enciende en el start exacto de SU palabra
en vez de estimarse. El troceo automático se conserva como fallback y las
piezas 1-9 siguen compilando igual.

La keyword pasa de pastilla violeta a texto en violet_hi, mayúscula,
ExtraBold y 1.22x, con las palabras normales en caja de frase. Medido:
6.70:1 sobre bg y 6.07:1 sobre surface.

caption_metrics.py saca de build-composition.py la cuenta de la zona
segura, que ahora usa el tamaño MÁXIMO del bloque y no el base. Sin eso,
un bloque de dos líneas con keyword grande se mete en la interfaz de la
plataforma: el bug de los 46 px que ya ocurrió una vez.

Primera pieza del pipeline testeable sin renderizar."
```

---

## Task 8: Spike A y las cámaras definitivas

**No bloquea la pieza 10:** si el spike falla, la arquitectura actual (un `<video>` por encuadre) ya funciona en 4 piezas publicadas y se conserva.

**Files:**
- Create: `spikes/camera-transform/` (desechable)
- Create: `docs/superpowers/spikes/2026-09-07-hard-crop-cut.md`
- Modify: `scripts/measure-face.py` (+ `cx_frac`, `cy_frac`)
- Modify: `scripts/build-composition.py` — **cambio quirúrgico nº 2**
- Modify: `scripts/edl_compile.py` (tope de escalera por resolución, `camera_min_gap`)

- [ ] **Step 1: Montar el spike**

Composición mínima con **un** `<video>` de `out/10-rough.mp4` dentro de un wrapper, y tres `tl.set({scale, x, y})` de duración cero sobre el **wrapper** (nunca sobre el `<video>`, que es del framework).

- [ ] **Step 2: Las tres comprobaciones**

```bash
npx hyperframes snapshot spikes/camera-transform --at 1.0,1.0
# (a) el mismo instante pedido dos veces -> ¿bytes idénticos?
npx hyperframes snapshot spikes/camera-transform --at 2.5
# (b) ¿se ve el frame del vídeo, o el transform rompió la inyección?
# (c) comparar nitidez a CLOSE contra la ruta actual de caja sobredimensionada
```

- [ ] **Step 3: Escribir el resultado**

`docs/superpowers/spikes/2026-09-07-hard-crop-cut.md` con las tres respuestas y la decisión:

| Resultado | Decisión |
| --- | --- |
| Las tres pasan | **Un vídeo + sets en el wrapper.** Un decoder para toda la pieza |
| (a) o (b) fallan | **Tres capas persistentes** WIDE/MEDIUM/CLOSE, cada una en su wrapper, corte por opacidad. Tres decoders frente a los 15-16 elementos de hoy |
| (c) sale más blando | **Statu quo.** La nitidez de la cara no se negocia |

- [ ] **Step 4: `cx_frac` / `cy_frac` en `measure-face.py`**

Sobre las mismas 48 muestras Haar que ya corre, emitir también el centroide horizontal. Test: `assets/face-10.json` regenerado conserva `chin_frac` **0.4324** y gana `cx_frac` en `[0, 1]`.

- [ ] **Step 5: Cambio quirúrgico nº 2**

En `shot_rect()`, `kind == "full"`:

```python
        # antes: left=round(-(w - W) / 2)   ← equivale a anchorX = 0.5
        return dict(left=round(-(w - W) * anchor_x),
                    top=round(-(h - H) * anchor), width=w, height=h, objpos="50% 50%")
```

Con `anchor_x = shot.get("anchorX", 0.5)`. Un plan sin `anchorX` da el comportamiento actual **bit a bit** — verificarlo recompilando la pieza 4 y comparando su `public/index.html` con el commiteado.

- [ ] **Step 6: Tope de escalera por resolución y ritmo de cámara**

```python
def cap_ladder(ladder: dict, src_w: int, canvas_w: int, max_upscale: float) -> dict:
    """El reescalado al alza es zoom · canvas_w / src_w. Con fuente 1080 el
    CLOSE tope es 1.20; con 4K, 2.40 — a z=2.00 sigue en nativo."""
    techo = (src_w / canvas_w) * max_upscale
    return {k: min(v, techo) for k, v in ladder.items()}
```

Y una métrica nueva `min_camera_gap` en `edl_metrics.py`, con gate `warn` por debajo de 0.70 s salvo dentro de `hook_exempt_until`.

- [ ] **Step 7: Commit**

```bash
git add -A docs/superpowers/spikes .claude/skills/video-tech-premium/scripts tests/
git commit -m "feat(camera): anclaje al sujeto, escalera adaptativa y spike del corte duro

measure-face.py emite cx_frac/cy_frac sobre las mismas 48 muestras, así
que el crop ocurre alrededor de la cara y no del centro geométrico. Un
plan sin anchorX da el comportamiento actual bit a bit.

La escalera se recorta por resolución: el reescalado al alza es
zoom · canvas_w / src_w, así que con fuente 1080 el CLOSE tope es 1.20 y
con 4K es 2.40 — a z=2.00 sigue en nativo. El 1.25 del brief queda
descartado solo para fuente 1080.

Spike A documentado con sus tres comprobaciones y la decisión."
```

---

## Task 9: Acumulación — cuatro tareas a la vez

El beat literal del guion, palabras 57-72. Nada sale de la escena: los objetos se quedan y en «al mismo tiempo» se cierran sobre el sillón.

**Files:**
- Modify: `scripts/objects.py` (+ `phone`, `card_payment`, `instagram`, `dental_chair`, `crowd_delta`)
- Modify: `videos/10/edl.json` (segmento `[57, 72]` → `MOTION_STAGE`)
- Modify: `tests/test_objects.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_crowd_mueve_hacia_el_centro_por_un_delta_horneado():
    dx, dy = crowd_delta("orbit-1", fraction=0.42)
    cx, cy = tokens.SLOTS["center"]
    ox, oy = tokens.SLOTS["orbit-1"]
    assert (dx, dy) == (round((cx - ox) * 0.42), round((cy - oy) * 0.42))
    assert isinstance(dx, int) and isinstance(dy, int)


def test_el_centro_no_se_mueve_al_acumular():
    """La claustrofobia viene de que el mundo se le echa encima al sujeto,
    no de que el sujeto se acerque: si el centro se mueve, se lee como zoom."""
    assert crowd_delta("center", fraction=0.42) == (0, 0)


def test_los_cuatro_objetos_de_la_pieza_10_existen():
    for k in ("dental_chair", "phone", "card_payment", "instagram"):
        assert k in REGISTRY


def test_cada_objeto_devuelve_html_y_un_id_unico():
    vistos = set()
    for k in ("dental_chair", "phone", "card_payment", "instagram"):
        o = REGISTRY[k]("stage-b", f"task-{k}", {}, "orbit-1")
        assert o["eid"] not in vistos
        vistos.add(o["eid"])
```

- [ ] **Step 2: Implementar los cuatro objetos y `crowd_delta`**

Cada uno es un SVG construido desde `tokens` (hairline `LINE`, `SHADOW`, `RADIUS`, acento del tema). Profundidad 2.5D con `perspective()` **estático** y un `rotateY` de reposo; lo que se anima es solo `opacity`, `scale`, `x`, `y`.

- [ ] **Step 3: Convertir el segmento en el EDL**

Cuatro `OBJECT_IN` en las palabras 62 · 64 · 66 · 69 (19.799 · 20.360 · 21.241 · 22.139 — huecos de 0.56, 0.88 y 0.90 s), y tres `OBJECT_STATE` con `crowd: true` en la palabra 71. `transitionIn: "DIAGONAL_WIPE"`.

- [ ] **Step 4: Verificar sobre snapshots**

```bash
npx hyperframes snapshot videos/10/public --at 19.9,20.5,21.4,22.3,23.1
```

Esperado: la escena **se llena progresivamente** — 1, 2, 3, 4 objetos — y en 23.1 los tres orbitales están más cerca del sillón que en 22.3. Ningún objeto por debajo de y1536.

- [ ] **Step 5: Commit**

```bash
git add -A .claude/skills/video-tech-premium/scripts videos/10/ tests/
git commit -m "feat(stage): acumulación de objetos en el beat de las cuatro tareas

Los cuatro objetos entran en la palabra que los nombra y NO salen: la
escena se llena al ritmo en que él los enumera, que es lo que convierte la
carga en algo que se ve en vez de algo que se dice.

En 'al mismo tiempo' los tres orbitales se cierran sobre el sillón por un
delta horneado. El centro no se mueve: si se moviera, el cierre se leería
como un zoom en vez de como el mundo echándosele encima."
```

---

## Task 10: SFX opt-in, colapso y concurrencia

**Files:**
- Modify: `scripts/edl_compile.py` (+ `_sfx`)
- Modify: `scripts/edl_metrics.py` (métrica `sfx_per_macro` ya existe; añadir `sfx_dropped`)
- Create: `tests/test_edl_sfx.py`

- [ ] **Step 1: Escribir el test que falla**

```python
from edl_compile import PRESET_SFX, PRIORITY, resolve_sfx


def test_sin_declarar_nada_no_suena():
    """`do not add SFX to every animation` como comportamiento por defecto,
    no como disciplina: el silencio no hay que recordarlo."""
    assert resolve_sfx([{"t": 1.0, "preset": "float-in", "sfx": None}]) == []


def test_auto_toma_el_efecto_del_preset():
    out = resolve_sfx([{"t": 1.0, "preset": "float-in", "sfx": "auto"}])
    assert out[0][1] == PRESET_SFX["float-in"] == "pop"


def test_dos_iguales_dentro_de_250ms_colapsan():
    out = resolve_sfx([{"t": 1.00, "preset": "float-in", "sfx": "auto"},
                       {"t": 1.15, "preset": "float-in", "sfx": "auto"}])
    assert len(out) == 1


def test_dos_iguales_separados_no_colapsan():
    out = resolve_sfx([{"t": 1.00, "preset": "float-in", "sfx": "auto"},
                       {"t": 1.60, "preset": "float-in", "sfx": "auto"}])
    assert len(out) == 2


def test_distintos_dentro_de_180ms_gana_la_clase_mas_alta():
    """impact + whoosh + pop casi simultáneos son una metralleta sonora."""
    out = resolve_sfx([{"t": 1.00, "sfx": "pop"},
                       {"t": 1.05, "sfx": "whoosh-short"},
                       {"t": 1.10, "sfx": "impact-bass-1"}])
    assert len(out) == 1 and out[0][1] == "impact-bass-1"
    assert PRIORITY["impact-bass-1"] < PRIORITY["pop"]


def test_el_trim_es_relativo_y_por_defecto_1():
    """El EDL nunca fija dB: el nivel absoluto lo calcula la fórmula de
    build_sfx a partir de la medición del archivo."""
    out = resolve_sfx([{"t": 1.0, "sfx": "pop", "trim": 0.85}])
    assert out[0][2] == 0.85
    assert resolve_sfx([{"t": 2.0, "sfx": "pop"}])[0][2] == 1.0


def test_la_tupla_es_la_que_espera_build_sfx():
    t, nombre, trim, por_que = resolve_sfx([{"t": 1.0, "sfx": "pop",
                                             "why": "entra el reloj"}])[0]
    assert (t, nombre, trim, por_que) == (1.0, "pop", 1.0, "entra el reloj")
```

- [ ] **Step 2: Implementar en `edl_compile.py`**

```python
# Cada preset trae su efecto, pero SOLO suena si el evento declara sfx:"auto".
PRESET_SFX = {"float-in": "pop", "drop-in": "impact-bass-2",
              "slide-blur": "whoosh-short", "hands-sweep": "whoosh-short",
              "crowd-in": "impact-bass-1", "type-beat": "key-press",
              "punch": "impact-bass-1", "box-in": "click"}

# Clase 1 gana a clase 4. El orden sale del peso narrativo, no del volumen.
PRIORITY = {"impact-bass-1": 1, "impact-bass-2": 1, "error": 1,
            "whoosh": 2, "whoosh-short": 2, "whoosh-cinematic": 2, "riser": 2,
            "click": 3, "click-soft": 3, "key-press": 3, "pop": 3, "typing": 3,
            "chime": 4, "sparkle": 4, "ping": 4, "notification": 4}

COLLAPSE_SAME, CONCURRENCY = 0.25, 0.18
```

`resolve_sfx` ordena por `(t, prioridad)`, descarta un igual dentro de `COLLAPSE_SAME`, y dentro de `CONCURRENCY` se queda con el de clase más baja. Devuelve tuplas `(q(t), nombre, trim, why)` — **exactamente** lo que `build_sfx` desempaqueta.

- [ ] **Step 3: Marcar los `sfx: "auto"` en el EDL de la pieza 10**

Solo donde marcan algo que pasa en imagen: el `punch` del hook (palabra 12), la entrada del reloj (18), el barrido de agujas (34), la entrada del sillón (62) y el cierre radial (71). **Cinco**, no veinte.

- [ ] **Step 4: Verificar el ataque sobre el MP4**

```bash
ffmpeg -v error -i videos/10/output.mp4 -af "volumedetect" -f null - 2>&1 | tail -5
```

Esperado: pico por debajo de −2 dB y **0 muestras saturadas**.

- [ ] **Step 5: Commit**

```bash
git add -A .claude/skills/video-tech-premium/scripts videos/10/ tests/
git commit -m "feat(sfx): opt-in por preset, colapso de iguales y concurrencia

Un preset trae su efecto, pero solo suena si el evento declara auto: el
silencio pasa a ser el comportamiento por defecto en vez de una disciplina
que hay que recordar.

Dos iguales dentro de 250 ms colapsan — cuatro OBJECT_IN con pop en 2.3 s
son cuatro pops seguidos — y entre distintos dentro de 180 ms gana la clase
más alta, para que impact + whoosh + pop no suenen a metralleta.

El EDL nunca fija dB: trim es relativo y por defecto 1.0, y el nivel
absoluto lo sigue calculando la fórmula que mide cada archivo."
```

---

## Task 11: La pieza 10 completa — el hito

**Files:**
- Modify: `videos/10/edl.json` (revisión final)
- Create: `tests/golden/10.plan.json`
- Create: `tests/test_golden.py`
- Create: `VIDEOS EDITADOS/video-10-clinica-reel.mp4`

- [ ] **Step 1: Golden file y prueba de determinismo**

```python
# tests/test_golden.py
def test_el_plan_de_la_pieza_10_no_ha_cambiado(edl10, style, project_root):
    from edl_compile import compile_edl, write_plan
    import json, tempfile, pathlib
    esperado = json.loads((project_root / "tests" / "golden" / "10.plan.json").read_text())
    assert compile_edl(edl10, style) == esperado, (
        "el plan compilado cambió. Si es intencionado, regenera el golden y "
        "MIRA el diff: un slot movido o un token tocado llega hasta aquí")


def test_compilar_dos_veces_da_bytes_identicos(edl10, style, tmp_path):
    from edl_compile import compile_edl, write_plan
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    write_plan(compile_edl(edl10, style), a)
    write_plan(compile_edl(edl10, style), b)
    assert a.read_bytes() == b.read_bytes()
```

- [ ] **Step 2: Comprobar los gates finales**

```bash
.venv/bin/python scripts/edl-compile.py --project . --piece 10
```

Esperado: `presenter_share` **dentro de [0.45, 0.60]** ahora que hay tres Motion Stage, `max_micro_gap` ≤ 2.5 s, `max_macro_gap` ≤ 4.5 s, y ningún `fail`.

- [ ] **Step 3: Render y validación**

```bash
.venv/bin/python scripts/build-composition.py --project . --piece 10
npx hyperframes check videos/10/public
npx hyperframes render videos/10/public --skill=talking-head-recut \
  -o videos/10/output.mp4 --fps 30 --sdr
```

Esperado: `check` **0 errores** de estructura, runtime, layout, motion y contraste. Ojo: los checks de contraste **solo corren si hay muestras** — un `0/0` no es que pase, es que no midió.

- [ ] **Step 4: Verificación sobre el MP4 — la que cuenta**

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 videos/10/output.mp4
ffmpeg -v info -i videos/10/output.mp4 -vf blackdetect=d=0.05:pix_th=0.03 -f null - 2>&1 | grep -i black || echo "sin negro real"
ffmpeg -v error -i videos/10/output.mp4 -af volumedetect -f null - 2>&1 | tail -4
```

Checklist, todo medido y ninguno estimado:

- [ ] duración ≈ **44.3 s**
- [ ] **sin negro real** con `pix_th=0.03`
- [ ] pico **≤ −2 dB**, **0 muestras** saturadas
- [ ] tinta más baja **≤ y1536** en todos los bloques de dos líneas
- [ ] el reloj marca **11:00** a los 5.5 s y **19:00** a los 11.0 s, y es el mismo
- [ ] los cuatro objetos de la acumulación **siguen en pantalla** en 23.1 s
- [ ] la cara **nunca** queda tapada por un subtítulo

- [ ] **Step 5: Publicar y commitear**

```bash
cp videos/10/output.mp4 "VIDEOS EDITADOS/video-10-clinica-reel.mp4"
git add -A videos/10 tests/ "VIDEOS EDITADOS/video-10-clinica-reel.mp4"
git commit -m "feat: pieza 10 completa desde EDL — el lenguaje nuevo funciona

REEL 9:16, 44.3 s. Primera pieza editada con el lenguaje EDL de punta a
punta: Motion Stage continuo, el reloj 11:00 -> 19:00 con match cut,
acumulación de cuatro objetos, captions explícitas con keyword en
violet_hi y SFX opt-in.

Golden file versionado: si mañana se mueve un slot en objects.py o un
token en tokens.py, el test se rompe y obliga a mirar en vez de
descubrirlo tres piezas después.

Verificado sobre el MP4, no sobre el HTML."
```

- [ ] **Step 6: Actualizar `CLAUDE.md`**

Añadir la pieza 10 a §13 con sus cifras reales, y reescribir §2 (pipeline) con los pasos 9/9b. La bitácora es lo que hace que la próxima pieza no repita los errores de esta.

---
## Task 12: Asset Resolver y manifest

Solo **después** de que la pieza 10 funcione. Antes no hay contra qué validar el Resolver: los assets se escribieron a mano y eso está bien.

**Files:**
- Create: `.claude/skills/video-tech-premium/scripts/asset_resolve.py`
- Create: `assets/manifest.json`
- Create: `tests/test_asset_resolve.py`
- Modify: `scripts/edl_schema.py` (validar presencia en el manifest)
- Modify: `scripts/edl_compile.py` (registrar `manifest_version` y hashes en el informe)

**Interfaces:**
- Produces:
  - `resolve(semantic: str, ctx: dict, manifest: dict) -> Resolution` con `.ref`, `.resolved_via` (`"library"`·`"configurable"`·`"recording"`·`"generated"`·`"broll"`), `.reason`
  - `resolve_edl(draft: dict, manifest: dict) -> dict` — devuelve el EDL con `asset`, `resolvedVia` y `resolveReason` rellenos
  - `load_manifest(path) -> dict` · `asset_hash(ref, manifest) -> str`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_la_prioridad_es_reutilizar_antes_que_generar(manifest):
    r = resolve("clock", {}, manifest)
    assert r.ref == "object:clock@1" and r.resolved_via == "library"


def test_solo_baja_de_nivel_si_el_de_arriba_no_sirve(manifest):
    r = resolve("recepcion-de-clinica", {}, manifest)
    assert r.resolved_via in ("generated", "broll")
    assert r.reason, "bajar de nivel sin anotar por qué es lo que hace la librería inauditable"


def test_una_referencia_resuelta_siempre_lleva_version(manifest):
    for s in ("clock", "chat", "phone"):
        assert "@" in resolve(s, {}, manifest).ref


def test_un_asset_que_no_esta_en_el_manifest_falla_en_core(write_edl, edl_min):
    data = _stage_edl(edl_min, [
        {"atWord": 0, "type": "OBJECT_IN", "asset": "object:inventado@1",
         "instanceId": "c", "slot": "center"}])
    assert "manifest" in problems_of(write_edl, data)


def test_el_hash_detecta_que_alguien_edito_una_version_inmutable(manifest, tmp_path):
    """@1 es inmutable: rediseñar el reloj crea @2. Si alguien edita @1, los
    renders históricos cambian en silencio."""
    import objects
    real = asset_hash("object:clock@1", manifest)
    assert real == manifest["assets"]["object:clock@1"]["hash"]


def test_el_informe_registra_manifest_version_y_hashes(edl10, style, manifest):
    from edl_compile import compile_report
    r = compile_report(edl10, style, manifest)
    assert r["manifest_version"] == manifest["manifest_version"]
    assert all(h.startswith("sha256:") for h in r["assets_used"].values())
```

- [ ] **Step 2: Crear `assets/manifest.json`**

```jsonc
{
  "manifest_version": "2026-09-07.1",
  "assets": {
    "object:clock@1":        { "hash": "sha256:…", "kind": "object", "added": "2026-09-07" },
    "object:dental-chair@1": { "hash": "sha256:…", "kind": "object", "added": "2026-09-07" },
    "object:phone@1":        { "hash": "sha256:…", "kind": "object", "added": "2026-09-07" },
    "object:card-payment@1": { "hash": "sha256:…", "kind": "object", "added": "2026-09-07" },
    "object:instagram@1":    { "hash": "sha256:…", "kind": "object", "added": "2026-09-07" },
    "object:chat@1":         { "hash": "sha256:…", "kind": "object", "added": "2026-09-07" }
  }
}
```

Los hashes se generan del código fuente de cada función de `objects.py` (`inspect.getsource`), que es lo que **define** el asset. Un script `scripts/manifest-sync.py` los recalcula y **falla si un `@n` existente cambió** — que es exactamente la garantía de inmutabilidad.

- [ ] **Step 3: Implementar el Resolver con la prioridad estricta**

```python
PRIORIDAD = ("library", "configurable", "recording", "generated", "broll")
```

Cada nivel se intenta en orden y solo se baja si el de arriba no puede servir la petición. Lo generado entra en `assets/gen/ledger.json`, que **ya existe**, así que el pipeline se re-corre sin volver a pagar. El B-roll **ya no está limitado a metraje propio**: puede ser licenciado, buscado o generado si el Planner lo justifica.

- [ ] **Step 4: Validar en CORE la presencia en el manifest**

En `edl_schema.load_edl`, junto a `_check_assets`: si el `asset` no está en `assets/manifest.json`, o su hash no cuadra, **falla**.

- [ ] **Step 5: Commit**

```bash
git add -A .claude/skills/video-tech-premium/scripts assets/manifest.json tests/
git commit -m "feat(assets): Asset Resolver con prioridad, manifest y hashes

Reutilizar antes que generar, en orden estricto, y anotando resolvedVia y
resolveReason cuando baja de nivel: sin ese rastro, dentro de tres meses
no se sabe si un gen: existe porque hacía falta o porque nadie miró la
librería.

Las referencias son inmutables: rediseñar el reloj crea object:clock@2 y
nunca edita @1, porque cambiar un asset en silencio modificaría renders
históricos. manifest-sync.py falla si un @n existente cambió.

El informe de compilación registra manifest_version y el hash de cada
asset usado, así que una pieza vieja es reproducible por referencia.

CORE falla si llega un asset que no está en el manifest."
```

---

## Task 13: Creative Planner

El último eslabón, y el único no determinista. Llega al final **a propósito**: ahora existe un EDL real, compilado y renderizado contra el que medir si el Planner acierta.

**Files:**
- Create: `.claude/skills/video-tech-premium/references/planner.md`
- Create: `.claude/skills/video-tech-premium/scripts/edl-plan.py`
- Create: `tests/test_planner_contract.py`

- [ ] **Step 1: Escribir el contrato del Planner**

`references/planner.md`: entrada (transcript con `wordId`, style profile, `guion.md` si existe), salida (`videos/<n>/edl.draft.json`), y las cuatro restricciones — no inventa palabras, no fija tiempos (solo `atWord` + `offset`), no fija dB ni px ni coordenadas, y rellena `reason` con una razón real.

- [ ] **Step 2: El test que importa no es del Planner, es del pipeline**

```python
def test_un_draft_del_planner_pasa_por_el_mismo_core(tmp_path, project_root):
    """El Planner es un CANDIDATO, no una autoridad. Que sea no determinista
    es seguro precisamente porque nada de lo que produce se acepta sin
    validar."""
    from asset_resolve import resolve_edl, load_manifest
    draft = json.loads((project_root / "videos" / "10" / "edl.draft.json").read_text())
    resuelto = resolve_edl(draft, load_manifest(project_root / "assets" / "manifest.json"))
    p = tmp_path / "edl.json"
    p.write_text(json.dumps(resuelto, ensure_ascii=False))
    load_edl(p, project_root)          # no lanza -> el draft era ejecutable


def test_generated_at_no_entra_en_el_hash_creativo(project_root):
    """Si entrara, dos corridas del mismo EDL darían hashes distintos y la
    prueba de determinismo sería inútil."""
    from edl_compile import creative_hash
    a = json.loads((project_root / "videos" / "10" / "edl.json").read_text())
    b = json.loads(json.dumps(a))
    b.setdefault("planner", {})["generatedAt"] = "2030-01-01T00:00:00Z"
    assert creative_hash(a) == creative_hash(b)


def test_el_hash_creativo_ignora_las_claves_subrayadas(project_root):
    a = json.loads((project_root / "videos" / "10" / "edl.json").read_text())
    b = json.loads(json.dumps(a))
    b["segments"][0]["_spokenText"] = "lo que sea"
    assert creative_hash(a) == creative_hash(b)


def test_el_hash_creativo_SI_cambia_con_una_decision_editorial(project_root):
    a = json.loads((project_root / "videos" / "10" / "edl.json").read_text())
    b = json.loads(json.dumps(a))
    b["segments"][0]["camera"] = "WIDE"
    assert creative_hash(a) != creative_hash(b)
```

- [ ] **Step 3: Implementar `creative_hash` y el CLI del Planner**

`creative_hash`: `sha256` del EDL canonicalizado (`sort_keys`, separadores fijos) **sin** `planner.generatedAt` y **sin** las claves que empiezan por `_`.

- [ ] **Step 4: Commit**

```bash
git add -A .claude/skills/video-tech-premium tests/
git commit -m "feat(planner): contrato del Creative Planner y hash creativo

El Planner produce un edl.draft.json que pasa por el Asset Resolver y por
exactamente el mismo CORE que un EDL escrito a mano. Que sea no
determinista es seguro precisamente porque nada de lo que produce se
acepta sin validar: es un candidato, no una autoridad.

creative_hash excluye planner.generatedAt y las claves subrayadas. Si
generatedAt entrara, dos corridas del mismo EDL darían hashes distintos y
la prueba de determinismo sería inútil."
```

---

## Task 14: Spike B — Three.js determinista (independiente)

**Fuera del camino crítico.** Si nunca se ejecuta, no pasa nada: el vocabulario de objetos es 2.5D por diseño y el 3D real siempre fue un extra para momentos héroe.

**Files:**
- Create: `spikes/three-determinism/` (desechable)
- Create: `docs/superpowers/spikes/2026-09-07-three-determinism.md`

- [ ] **Step 1: Montar la escena mínima**

Composición 1080×1920 con un icosaedro rotando dirigido por `hf-seek`, `data-duration` **explícito** en la raíz (el adapter `three` no infiere duración y sin él el render falla con «Composition has zero duration»).

- [ ] **Step 2: Las tres comprobaciones**

| # | Prueba | Cómo |
| --- | --- | --- |
| 1 | El mismo frame dos veces es **byte-idéntico** | `snapshot --at 1.5` dos veces, `cmp` |
| 2 | `data-duration` manual se respeta | render de 3 s → `ffprobe` da 3 s |
| 3 | WebGL no revienta con la memoria justa | render de 90 frames a 1080×1920 sin OOM |

- [ ] **Step 3: Escribir el resultado y decidir**

Si falla cualquiera de las tres, **el 3D real no entra** y el 2.5D cubre todo el vocabulario. Documentarlo en `docs/superpowers/spikes/` y cerrar.

```bash
git add docs/superpowers/spikes/2026-09-07-three-determinism.md
git commit -m "spike: determinismo de Three.js bajo hf-seek

Resultado de las tres comprobaciones y decisión sobre habilitar 3D real.
Fuera del camino crítico: el 2.5D es la estrategia principal, no un plan B."
```

---

## Cobertura de la spec

| Sección de la spec | Tarea |
| --- | --- |
| §0 Herramienta y alcance | — (decisión, sin código) |
| §1 Gramática y reglas de decisión | 2 (`representationType`, `reason`), 4 (bandas y ritmo) |
| §2 Contrato del EDL | 1, 2 |
| §3 Motion Stage y objetos | 5, 6, 9 |
| §4 Presets y transiciones | 6 (`hands-sweep`), 9 (`crowd-in`), 10 (SFX por preset) |
| §5 Captions y kinetic type | 7 |
| §6 Cámaras | 3 (escalera), 8 (anclaje, tope, ritmo, spike A) |
| §7 Color semántico | 5 (`THEME`, tinta sobre ámbar y verde) |
| §8 Sound design | 10 |
| §9 `edl-compile.py` | 3, 4, 6, 10 |
| §10 Integración con el pipeline | 3, 5, 7, 8, 11 |
| §11 Planner + Asset Resolver | 12, 13 |
| §12 Gates CORE / STYLE | 2 (CORE), 4 (STYLE), 5 y 12 (los diferidos) |
| §13 Determinismo y pruebas | 3 (pureza y bytes), 11 (golden), 13 (hash creativo) |
| §14 Spikes | 8 (A), 14 (B) |
| §15 Trazado end-to-end | 6 (el reloj), 11 (la pieza entera) |
| §16 Fuera de alcance | Constraints globales |

**Sin cobertura, y a propósito:** `KINETIC_TYPE` con `TYPE_BEAT` (la pieza 10 no lo necesita — la escala está definida en la Tarea 5 y el `sceneType` validado en la 2, pero no hay renderizador hasta que una pieza lo pida), `BLUR_WIPE` / `SCALE_BLUR` / `DIAGONAL_WIPE` más allá del uso en la Tarea 9, y los 9 objetos restantes de la librería candidata. Todo eso entra por demanda real, que es la regla rectora.

## Riesgos conocidos

| Riesgo | Mitigación |
| --- | --- |
| El troceo de captions del EDL no case con el que hoy hace `build_captions` y cambie el ritmo de lectura | La Tarea 7 conserva la misma regla de `end` y el fallback automático; comparar snapshots antes y después |
| `measure_font` no sea extraíble limpiamente de `build-composition.py` | Es un movimiento sin cambio de comportamiento; verificar recompilando la pieza 4 y comparando su `index.html` con el commiteado |
| El spike A salga blando y haya que quedarse con 15-16 elementos | La pieza 10 no depende de él; es optimización |
| Los 6 objetos SVG lleven más tiempo que el compilador entero | Es lo esperado (§3 de la spec). Empezar por `clock`, que es el único que la Tarea 6 necesita |

---

## Fixtures compartidas — `tests/conftest.py`

⚠ **Varias fixtures se usan desde más de un archivo de test** (`style` en las Tareas 4 y 11; `edl10` en la 4, 11 y 12; `write_edl` / `edl_min` / `_stage_edl` / `problems_of` en la 2, 5 y 12). pytest **solo las comparte si viven en `conftest.py`** — definidas dentro de un archivo de test son invisibles para los demás y el error (`fixture 'style' not found`) aparece tarde y despista.

Este es el `conftest.py` **final**. Cada tarea añade su bloque aquí, no en su propio archivo:

```python
"""Deja los scripts de la skill importables y comparte las fixtures."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / ".claude" / "skills" / "video-tech-premium"
sys.path.insert(0, str(SKILL / "scripts"))

import pytest


# ── Tarea 1 ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def skill_root() -> Path:
    return SKILL


@pytest.fixture(scope="session")
def w10(project_root):
    """Las palabras de la pieza 10, remapeadas a la línea del corte."""
    from edl_words import load_words
    return load_words(project_root / "transcripts" / "10.json",
                      project_root / "cuts" / "10.json")


# ── Tarea 2 ──────────────────────────────────────────────────────────────────
@pytest.fixture
def edl_min(w10):
    """El EDL más pequeño que es válido: un A_ROLL sobre las 131 palabras."""
    return {
        "format": "REEL", "piece": 10, "style_profile": "motion-explainer",
        "transcript": {"words": "transcripts/10.json", "cuts": "cuts/10.json",
                       "fingerprint": w10.fingerprint},
        "voice_gain": 0.70,
        "segments": [{
            "words": [0, 130], "semanticIntent": "la pieza entera de una",
            "sceneType": "A_ROLL", "camera": "CLOSE", "transitionIn": "CUT",
            "events": [{"atWord": 0, "type": "CAPTION", "words": [0, 4]}],
            "reason": "andamiaje mínimo para los tests del schema"}],
    }


@pytest.fixture
def write_edl(tmp_path, project_root):
    from edl_schema import load_edl

    def _w(data):
        p = tmp_path / "edl.json"
        p.write_text(json.dumps(data, ensure_ascii=False))
        return load_edl(p, project_root)
    return _w


@pytest.fixture
def problems_of(write_edl):
    from edl_schema import EdlError

    def _p(data):
        with pytest.raises(EdlError) as ei:
            write_edl(data)
        return " | ".join(ei.value.problems)
    return _p


@pytest.fixture
def stage_edl():
    """Un EDL de un solo MOTION_STAGE, para los tests de instancias."""
    def _s(base, events, **kw):
        seg = {"words": [0, 130], "semanticIntent": "un stage",
               "sceneType": "MOTION_STAGE", "representationType": "OBJECT",
               "camera": "OFF", "transitionIn": "CUT", "events": events,
               "reason": "probar el ciclo de vida de las instancias"}
        seg.update(kw)
        return dict(base, segments=[seg])
    return _s


# ── Tarea 3 ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def style(skill_root):
    from edl_compile import load_style
    return load_style("motion-explainer", skill_root)


@pytest.fixture(scope="session")
def edl10(project_root):
    from edl_schema import load_edl
    return load_edl(project_root / "videos" / "10" / "edl.json", project_root)


@pytest.fixture(scope="session")
def plan10(edl10, style):
    from edl_compile import compile_edl
    return compile_edl(edl10, style)


# ── Tarea 12 ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def manifest(project_root):
    from asset_resolve import load_manifest
    return load_manifest(project_root / "assets" / "manifest.json")
```

**Consecuencias para los tests escritos arriba:** en `test_edl_schema.py` y `test_edl_compile.py` hay que **borrar** las definiciones locales de `edl_min`, `write_edl`, `style`, `edl10`, `plan10` y `skill_root`, dejar solo los `import` de lo que se prueba, y sustituir la función auxiliar `_stage_edl(...)` por la fixture `stage_edl(...)` y `problems_of(write_edl, data)` por `problems_of(data)`.

**Nota sobre `edl10` y el orden de las tareas:** la fixture carga `videos/10/edl.json`, que no existe hasta la Tarea 3. Los tests de las Tareas 1 y 2 no la usan, así que no hay problema — pero si se ejecutan las tareas fuera de orden, el fallo será `FileNotFoundError` sobre ese archivo y no un bug.

---

## Notas de auto-repaso

Tres cosas que este plan corrige respecto a versiones anteriores del diseño, y que conviene no re-introducir:

1. **La línea de tiempo.** El EDL referencia `transcripts/<n>.json` **+** `cuts/<n>.json` y aplica el mismo `remap()` que el renderer. Usar `transcripts/<n>-rough.json` da un EDL que valida y está mal: 130 palabras frente a 131 y tiempos 16–60 ms distintos.
2. **`build-composition.py` necesita 4 cambios, no 3.** El cuarto (consumir captions explícitas) apareció al leer que hoy el troceo lo hace él mismo desde el transcript. Se mitiga conservando el troceo automático como fallback, así que las piezas 1–9 no se tocan.
3. **El `trim` de un SFX no es volumen.** Es un multiplicador **relativo aplicado después** de la ganancia calculada por medición, con techo de unidad y suelo 0.02. El EDL nunca fija dB.
