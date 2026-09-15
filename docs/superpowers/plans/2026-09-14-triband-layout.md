# Layout triband — plan de implementación

> **Para trabajadores agénticos:** SUB-SKILL OBLIGATORIA: usa
> `superpowers:subagent-driven-development` (recomendada) o
> `superpowers:executing-plans` para ejecutar este plan tarea a tarea. Los pasos llevan
> checkbox (`- [ ]`) para seguimiento.

**Objetivo:** añadir a `video-tech-premium` un layout `triband` —animación arriba, texto en
medio, hablante abajo— como modo opcional por pieza, y renderizar con él la pieza 15.

**Arquitectura:** un valor de cámara nuevo (`BAND`) activa el modo por segmento; un bloque
`layout` en la cabecera del EDL declara la geometría **una sola vez**. El compilador emite
`kind: "band"` y `build-composition.py` lo convierte en el rect de la banda del hablante.
Los subtítulos dejan de perseguir la barbilla en los tramos `band` y pasan a un tope fijo
con un gate que impide invadir la banda del hablante.

**Stack:** Python 3.12, pytest, HyperFrames CLI 0.7.105, ffmpeg, GSAP.

**Spec:** `docs/superpowers/specs/2026-09-14-triband-layout-design.md`

## Global Constraints

- **Las piezas 1–14 quedan congeladas.** El golden de la pieza 10
  (`tests/golden/10.plan.json`) debe seguir pasando byte a byte tras cada tarea.
- Lienzo REEL **1080 × 1920**, 30 fps. Bandas: `top` 0–820 · `text` 820–1120 ·
  `speaker` 1120–1920.
- Suelo del subtítulo en triband: **y1104**. Tope fijo: **y844**.
- Subtítulo base **66 px**; `KEYWORD_SCALE_MAX = 1.22`; `LINE_RATIO = 1.14`.
- **Nada entra antes de su palabra** (`OFFSET_FLOOR = -0.12`).
- **Ninguna entrada usa `back.out()`.**
- Nada de negro puro (`#000`) ni blanco puro como fondo.
- Ejecutar los tests con `.venv/bin/python -m pytest`.
- Los scripts viven en `.claude/skills/video-tech-premium/scripts/`; `scripts/` es un
  **enlace**, no una copia. Editar siempre a través de `scripts/`.
- Idioma de código, comentarios y commits: **español**.

---

## Estado de partida (medido 2026-09-14)

`.venv/bin/python -m pytest -q` → **280 passed, 3 skipped, 8 errors**.

Los 8 errores son de los EDL de las piezas 12, 13 y 14, que **no existen**: nunca se
commitearon y se borraron del árbol de trabajo. No están en HEAD, ni en el stash, ni en
ningún commit colgante. Los golden (`tests/golden/12|13|14.plan.json`) sí existen, pero sin
su EDL de entrada no hay nada que compilar.

**Consecuencia para este plan:** la única prueba de no-regresión disponible es la **pieza
10**. Cubre cámaras, captions, keywords, MOTION_STAGE, instancias y SFX. **No** cubre
tarjetas (`test_edl_cards`, la pieza 10 no usa). La Tarea 0 deja ese hueco visible en vez
de ruidoso.

---

## Estructura de archivos

| Archivo | Responsabilidad | Tareas |
| --- | --- | --- |
| `tests/conftest.py` | Fixtures. Se saltan si falta su EDL. | 0 |
| `scripts/edl_schema.py` | Contrato congelado: `BAND`, bloque `layout`, validación. | 1, 2 |
| `scripts/edl_compile.py` | `BAND` → `kind: "band"`; `layout` al plan. | 3 |
| `scripts/build-composition.py` | Geometría de bandas, subtítulo y gestos nuevos. | 4, 5, 7 |
| `scripts/caption_metrics.py` | `floor_px` explícito además del 20 % de plataforma. | 5 |
| `scripts/fetch-logos.py` | Vendorizar marcas fuera de Simple Icons + gate. | 6 |
| `scripts/mockups.py` | `tool_card` y `tool_recording`: la banda de arriba. | 8 |
| `tests/test_triband.py` | **Nuevo.** Schema y compilador del triband. | 1–3 |
| `tests/test_triband_geometry.py` | **Nuevo.** Las tres bandas y `chin_at`. | 4 |
| `tests/test_caption_band.py` | **Nuevo.** Tope fijo y gate del suelo. | 5 |
| `tests/test_logos_gate.py` | **Nuevo.** Gate de resolución. | 6 |
| `tests/test_motion_gestos.py` | **Nuevo.** `glide-x` y `drop-in`. | 7 |
| `tests/test_tool_card.py` | **Nuevo.** Las dos cards de herramienta. | 8 |
| `CLAUDE.md` | Bitácora: §4, §5, §13. | 10 |

**Orden de dependencias.** 1 → 2 → 3 → 4 → 5 fijan el contrato y la geometría; 6, 7 y 8
producen los materiales de la banda de arriba y pueden hacerse en cualquier orden entre
ellas una vez cerrada la 4; la 9 los consume todos; la 10 documenta lo que quedó.

---

### Task 0: Dejar la suite verde y el hueco visible

Los 8 errores actuales enmascaran cualquier rotura nueva: un ejecutor no puede distinguir
«esto ya estaba roto» de «lo rompí yo». Se saltan con razón explícita, siguiendo el patrón
que el proyecto ya usa para `audio14` (fixture que hace `pytest.skip` cuando el FLAC
gitignoreado no está).

**Files:**
- Modify: `tests/conftest.py` — fixtures `edl12`, `edl13`, `edl14`

**Interfaces:**
- Consumes: nada.
- Produces: las fixtures `edl12`/`edl13`/`edl14` hacen `pytest.skip` en vez de reventar.

- [ ] **Step 1: Ver el estado real**

```bash
cd editor-videos
.venv/bin/python -m pytest -q --no-header 2>&1 | tail -3
```

Esperado: `280 passed, 3 skipped, 8 errors`.

- [ ] **Step 2: Hacer que las fixtures se salten**

En `tests/conftest.py`, sustituir las tres fixtures `edl12`, `edl13`, `edl14` por esta
forma (una por pieza, cambiando el número):

```python
@pytest.fixture(scope="session")
def edl12(project_root):
    """El EDL de la pieza 12.

    ⚠ No está: `videos/` se borró sin commitear y estos EDL nunca llegaron a
    HEAD. El golden `tests/golden/12.plan.json` sí sobrevive, pero sin su
    entrada no hay nada que compilar. Se salta con razón en vez de reventar
    —el mismo trato que `audio14`— para que un fallo NUEVO se vea.
    """
    from edl_schema import load_edl
    p = project_root / "videos" / "12" / "edl.json"
    if not p.exists():
        pytest.skip("videos/12/edl.json no está: se perdió al borrar videos/ "
                    "sin commitear. La no-regresión la cubre la pieza 10.")
    return load_edl(p, project_root)
```

- [ ] **Step 3: Verificar que no queda ni un error**

```bash
.venv/bin/python -m pytest -q --no-header 2>&1 | tail -3
```

Esperado: `280 passed, 11 skipped` — **0 failed, 0 errors**.

- [ ] **Step 4: Commit**

```bash
git add tests/conftest.py
git commit -m "test: salta los tests de las piezas 12-14 — su EDL se perdió

Enmascaraban cualquier rotura nueva: con 8 errores de partida no se
distingue lo que ya estaba roto de lo que rompe un cambio. Se saltan con
razón explícita, igual que audio14 con el FLAC gitignoreado.

La no-regresión del triband la cubre la pieza 10, que ejercita cámaras,
captions, keywords, stages, instancias y SFX. Las tarjetas se quedan sin
cobertura: la pieza 10 no usa."
```

---

### Task 1: `camera: "BAND"` en el contrato

**Files:**
- Modify: `scripts/edl_schema.py:37`
- Test: `tests/test_triband.py` (crear)

**Interfaces:**
- Consumes: `CAMERAS`, `load_edl`, fixtures `edl_min`, `write_edl`, `problems_of`.
- Produces: `CAMERAS` incluye `"BAND"`. Un `Segment.camera == "BAND"` es válido.

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_triband.py`:

```python
"""El layout triband: animación arriba, texto en medio, hablante abajo.

Un modo por pieza, no un reemplazo. Lo que estos tests protegen es que un
EDL SIN `layout` compile exactamente igual que antes.
"""
import pytest


def test_band_es_una_camara_valida(edl_min, write_edl):
    """`BAND` entra en el mismo sitio que WIDE/MEDIUM/CLOSE/OFF."""
    from edl_schema import CAMERAS
    assert "BAND" in CAMERAS


def test_una_camara_inventada_sigue_rechazandose(edl_min, problems_of):
    """Añadir BAND no puede abrir la puerta a cualquier cosa."""
    malo = dict(edl_min)
    seg = dict(malo["segments"][0], camera="CINEMATIC")
    malo["segments"] = [seg]
    assert "camera 'CINEMATIC' desconocida" in problems_of(malo)
```

- [ ] **Step 2: Correr y ver que falla**

```bash
.venv/bin/python -m pytest tests/test_triband.py -v
```

Esperado: FAIL — `assert 'BAND' in CAMERAS`.

- [ ] **Step 3: Implementación mínima**

En `scripts/edl_schema.py`, línea 37:

```python
# `BAND` es el layout triband: el metraje ocupa solo la banda de abajo y no
# lleva escalera de zoom — el encuadre de la banda ya es un recorte fuerte y
# una escalera encima lo haría irreconocible.
CAMERAS = frozenset({"WIDE", "MEDIUM", "CLOSE", "BAND", "OFF"})
```

- [ ] **Step 4: Correr y ver que pasa**

```bash
.venv/bin/python -m pytest tests/test_triband.py -v
.venv/bin/python -m pytest -q --no-header 2>&1 | tail -3
```

Esperado: los dos nuevos PASS · la suite entera sin failed ni errors.

- [ ] **Step 5: Commit**

```bash
git add scripts/edl_schema.py tests/test_triband.py
git commit -m "feat(edl): camera BAND, el valor que activa el triband"
```

---

### Task 2: El bloque `layout` en la cabecera del EDL

La geometría se declara **una vez** y la comparten todos los segmentos. Repetirla por
segmento invita a que dos contiguos declaren bandas distintas y eso salta en el frame.

**Files:**
- Modify: `scripts/edl_schema.py` — constantes, dataclass `Edl`, `load_edl`
- Test: `tests/test_triband.py`

**Interfaces:**
- Consumes: `Edl`, `EdlError`, `load_edl`, `CANVAS_H`.
- Produces: `Edl.layout: dict` — `{}` si el EDL no lo declara, o
  `{"mode": "triband", "bands": {"top": [0,820], "text": [820,1120], "speaker": [1120,1920]}}`.
  Función `validate_layout(layout, segments, canvas_h) -> list[str]`.

- [ ] **Step 1: Escribir los tests que fallan**

Añadir a `tests/test_triband.py`:

```python
LAYOUT_OK = {"mode": "triband",
             "bands": {"top": [0, 820], "text": [820, 1120], "speaker": [1120, 1920]}}


def _con_layout(edl_min, layout, camera="BAND"):
    base = dict(edl_min, layout=layout)
    base["segments"] = [dict(base["segments"][0], camera=camera)]
    return base


def test_un_edl_sin_layout_no_declara_ninguno(edl_min, write_edl):
    """La ausencia de `layout` ES la prueba de regresión: camino viejo intacto."""
    assert write_edl(edl_min).layout == {}


def test_el_layout_valido_se_carga_entero(edl_min, write_edl):
    edl = write_edl(_con_layout(edl_min, LAYOUT_OK))
    assert edl.layout["mode"] == "triband"
    assert edl.layout["bands"]["text"] == [820, 1120]


def test_un_modo_desconocido_se_rechaza(edl_min, problems_of):
    malo = _con_layout(edl_min, dict(LAYOUT_OK, mode="cuatribanda"))
    assert "layout.mode 'cuatribanda' desconocido" in problems_of(malo)


def test_las_bandas_tienen_que_cubrir_el_lienzo_entero(edl_min, problems_of):
    """Un hueco entre bandas es suelo grafito que nadie decidió dejar."""
    malo = _con_layout(edl_min, {"mode": "triband", "bands": {
        "top": [0, 820], "text": [820, 1100], "speaker": [1120, 1920]}})
    assert "no son contiguas" in problems_of(malo)


def test_una_banda_invertida_se_rechaza(edl_min, problems_of):
    malo = _con_layout(edl_min, {"mode": "triband", "bands": {
        "top": [0, 820], "text": [1120, 820], "speaker": [1120, 1920]}})
    assert "banda 'text' invertida" in problems_of(malo)


def test_layout_declarado_sin_ningun_segmento_band_es_error(edl_min, problems_of):
    """Declarar geometría que nadie usa casi siempre es un olvido, no un estilo."""
    malo = _con_layout(edl_min, LAYOUT_OK, camera="CLOSE")
    assert "ningún segmento usa camera BAND" in problems_of(malo)


def test_un_segmento_band_sin_layout_es_error(edl_min, problems_of):
    malo = dict(edl_min)
    malo["segments"] = [dict(malo["segments"][0], camera="BAND")]
    assert "camera BAND sin bloque 'layout'" in problems_of(malo)
```

- [ ] **Step 2: Correr y ver que fallan**

```bash
.venv/bin/python -m pytest tests/test_triband.py -v
```

Esperado: FAIL — `Edl` no tiene atributo `layout`.

- [ ] **Step 3: Implementación**

En `scripts/edl_schema.py`, junto a las demás constantes (tras `CAMERAS`):

```python
LAYOUT_MODES = frozenset({"triband"})
# El orden IMPORTA: es el de arriba abajo, y con él se comprueba la contigüidad.
BAND_ORDER = ("top", "text", "speaker")
CANVAS_H = {"REEL": 1920, "YOUTUBE": 1080}
```

Añadir el campo a la dataclass `Edl` (tras `planner: dict`):

```python
    layout: dict = field(default_factory=dict)
```

Añadir la función de validación (antes de `load_edl`):

```python
def validate_layout(layout: dict, segments, canvas_h: int) -> list[str]:
    """Las bandas tienen que cubrir el lienzo entero, en orden y sin huecos.

    Un hueco entre dos bandas es suelo grafito que nadie decidió dejar, y en un
    lienzo de 1920 px pasa desapercibido en el JSON y no en el frame.
    """
    problems: list[str] = []
    usa_band = any(s.camera == "BAND" for s in segments)

    if not layout:
        if usa_band:
            problems.append(
                "hay un segmento con camera BAND sin bloque 'layout' en la cabecera: "
                "la geometría de las tres bandas se declara una sola vez y se comparte")
        return problems

    mode = layout.get("mode")
    if mode not in LAYOUT_MODES:
        problems.append(f"layout.mode '{mode}' desconocido; hay {sorted(LAYOUT_MODES)}")
        return problems

    bands = layout.get("bands") or {}
    faltan = [k for k in BAND_ORDER if k not in bands]
    if faltan:
        problems.append(f"layout.bands: faltan {faltan}; el triband pide {list(BAND_ORDER)}")
        return problems

    for k in BAND_ORDER:
        v = bands[k]
        if not isinstance(v, list) or len(v) != 2:
            problems.append(f"layout.bands.{k} tiene que ser [y0, y1]")
            return problems
        if v[1] <= v[0]:
            problems.append(f"layout: banda '{k}' invertida o vacía {v}")

    ys = [bands[k] for k in BAND_ORDER]
    if ys[0][0] != 0 or ys[-1][1] != canvas_h:
        problems.append(
            f"layout: las bandas tienen que cubrir 0..{canvas_h}, y van de "
            f"{ys[0][0]} a {ys[-1][1]}")
    for a, b, ka, kb in zip(ys, ys[1:], BAND_ORDER, BAND_ORDER[1:]):
        if a[1] != b[0]:
            problems.append(
                f"layout: las bandas '{ka}' y '{kb}' no son contiguas "
                f"({a[1]} → {b[0]}): un hueco entre bandas es suelo que nadie decidió")

    if not usa_band:
        problems.append(
            "layout declarado pero ningún segmento usa camera BAND: declarar geometría "
            "que nadie usa casi siempre significa que faltó marcar los segmentos")
    return problems
```

En `load_edl`, justo antes del bloque `# ── overrides ──`:

```python
    layout = raw.get("layout") or {}
    problems += validate_layout(layout, segments, CANVAS_H[raw.get("format", "REEL").upper()])
```

Y en el `return Edl(...)`, añadir el argumento:

```python
               music=raw.get("music", {}), planner=raw.get("planner", {}),
               layout=layout)
```

- [ ] **Step 4: Correr y ver que pasan**

```bash
.venv/bin/python -m pytest tests/test_triband.py -v
.venv/bin/python -m pytest -q --no-header 2>&1 | tail -3
```

Esperado: todos PASS · suite sin failed ni errors · **el golden de la pieza 10 verde**.

- [ ] **Step 5: Commit**

```bash
git add scripts/edl_schema.py tests/test_triband.py
git commit -m "feat(edl): bloque layout con las tres bandas y su validación

La geometría se declara una vez en la cabecera y la comparten todos los
segmentos. Un hueco entre bandas, una banda invertida, un layout que
nadie usa o un BAND sin layout fallan la carga en vez del frame."
```

---

### Task 3: El compilador emite `kind: "band"`

**Files:**
- Modify: `scripts/edl_compile.py:104-110` (`emit` dentro de `_shots`)
- Modify: `scripts/edl_compile.py` — `compile_edl`, para pasar `layout` al plan
- Test: `tests/test_triband.py`

**Interfaces:**
- Consumes: `Edl.layout` (Tarea 2), `CAMERAS` con `BAND` (Tarea 1).
- Produces: entradas de `plan["shots"]` con `{"at": float, "kind": "band", "anchor": float}`
  — **sin clave `zoom`**. `plan["layout"]` con el bloque del EDL, ausente si no se declara.

- [ ] **Step 1: Escribir los tests que fallan**

Añadir a `tests/test_triband.py`:

```python
def test_un_segmento_band_emite_un_encuadre_band(edl_min, write_edl, style):
    from edl_compile import compile_edl
    plan = compile_edl(write_edl(_con_layout(edl_min, LAYOUT_OK)), style)
    assert plan["shots"][0]["kind"] == "band"


def test_el_encuadre_band_no_lleva_zoom(edl_min, write_edl, style):
    """La banda ya es un recorte fuerte: una escalera encima lo haría ilegible."""
    from edl_compile import compile_edl
    plan = compile_edl(write_edl(_con_layout(edl_min, LAYOUT_OK)), style)
    assert "zoom" not in plan["shots"][0]


def test_el_layout_viaja_al_plan(edl_min, write_edl, style):
    from edl_compile import compile_edl
    plan = compile_edl(write_edl(_con_layout(edl_min, LAYOUT_OK)), style)
    assert plan["layout"]["bands"]["speaker"] == [1120, 1920]


def test_un_edl_sin_layout_no_mete_la_clave_en_el_plan(edl_min, write_edl, style):
    """Una clave nueva en el plan de una pieza vieja rompería su golden."""
    from edl_compile import compile_edl
    plan = compile_edl(write_edl(edl_min), style)
    assert "layout" not in plan
```

> **No escribas un test del golden de la pieza 10 aquí.** Ya existe:
> `tests/test_golden.py::test_el_plan_de_la_pieza_10_no_ha_cambiado`, y corre en cada
> `pytest`. Un segundo test idéntico es duplicación, no cobertura.

- [ ] **Step 2: Correr y ver que fallan**

```bash
.venv/bin/python -m pytest tests/test_triband.py -v -k "band or layout or golden"
```

Esperado: FAIL — `kind` sale `"full"`, no `"band"`.

- [ ] **Step 3: Implementación**

En `scripts/edl_compile.py`, dentro de `_shots`, sustituir `emit`:

```python
    def emit(at: float, camera: str) -> None:
        if camera == "OFF":
            out.append({"at": q(at), "kind": "off"})
        elif camera == "BAND":
            # Sin zoom a propósito: el rect de la banda ya recorta fuerte y la
            # escalera encima dejaría la cara irreconocible. El reencuadre
            # vertical lo hace `object-position` con `anchor`.
            out.append({"at": q(at), "kind": "band", "anchor": anchor})
        else:
            out.append({"at": q(at), "kind": "full",
                        "zoom": ladder[camera], "anchor": anchor})
```

`compile_edl` (`scripts/edl_compile.py:322`) devuelve **un dict literal**, así que no hay
dónde insertar nada. Reestructurarlo mínimamente:

```python
    plan = {
        "format": edl.fmt,
        ...            # las mismas claves de ahora, sin tocar una sola
        "_": f"generado por edl-compile desde {edl.src.name} — NO editar a mano",
    }
    # Condicional a propósito: una clave incondicional cambiaría el plan de
    # TODAS las piezas viejas y rompería el golden de la 10.
    if edl.layout:
        plan["layout"] = edl.layout
    return plan
```

El orden de inserción no importa: el JSON se escribe con `sort_keys` y el golden compara
dicts.

- [ ] **Step 4: Correr y ver que pasan**

```bash
.venv/bin/python -m pytest tests/test_triband.py -v
.venv/bin/python -m pytest -q --no-header 2>&1 | tail -3
```

Esperado: todos PASS · suite sin failed ni errors.

- [ ] **Step 5: Commit**

```bash
git add scripts/edl_compile.py tests/test_triband.py
git commit -m "feat(edl): BAND compila a kind band, sin zoom

La clave layout solo entra en el plan si el EDL la declara: meterla
siempre rompería el golden de la pieza 10, que es la única prueba de
no-regresión que sobrevive."
```

---

### Task 4: La geometría de las tres bandas

**Files:**
- Modify: `scripts/build-composition.py` — `triband_panels()`, `shot_geometry`, `chin_at`,
  `configure`, `build_shots`
- Test: `tests/test_triband_geometry.py` (crear)

**Interfaces:**
- Consumes: `plan["layout"]` (Tarea 3).
- Produces: global `LAYOUT` en `build-composition`. `triband_panels() -> dict` con
  `{"top"|"text"|"speaker": {"left","top","width","height"}}`.
  `shot_geometry("band", zoom, anchor, anchor_x)` devuelve el rect de la banda `speaker`.

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/test_triband_geometry.py`:

```python
"""La geometría de las tres bandas.

`shot_geometry` lee globals (W, H, LAYOUT), no recibe parámetros de lienzo:
los tests los fijan igual que hace `configure()`.
"""
import pytest

BANDS = {"top": [0, 820], "text": [820, 1120], "speaker": [1120, 1920]}


@pytest.fixture(autouse=True)
def lienzo(bc):
    bc.W, bc.H = 1080, 1920
    bc.LAYOUT = {"mode": "triband", "bands": BANDS}
    yield
    bc.LAYOUT = {}


def test_las_tres_bandas_salen_a_ancho_completo(bc):
    p = bc.triband_panels()
    for k in ("top", "text", "speaker"):
        assert (p[k]["left"], p[k]["width"]) == (0, 1080), k


def test_la_banda_del_hablante_mide_800(bc):
    p = bc.triband_panels()
    assert (p["speaker"]["top"], p["speaker"]["height"]) == (1120, 800)


def test_band_usa_el_rect_del_hablante(bc):
    g = bc.shot_geometry("band", 1.0, 0.45)
    assert (g["left"], g["top"], g["width"], g["height"]) == (0, 1120, 1080, 800)


def test_band_ignora_el_zoom(bc):
    """El zoom no aplica: el rect es el de la banda, venga el zoom que venga."""
    a = bc.shot_geometry("band", 1.0, 0.45)
    b = bc.shot_geometry("band", 1.15, 0.45)
    assert a == b


def test_band_ignora_anchorx(bc):
    """Como split y pip: el reencuadre horizontal lo hace object-position."""
    assert bc.shot_geometry("band", 1.0, 0.45) == bc.shot_geometry("band", 1.0, 0.45, 0.2)


def test_el_anchor_va_a_object_position(bc):
    assert bc.shot_geometry("band", 1.0, 0.45)["objpos"] == "50% 45%"


def test_la_barbilla_cae_sobre_la_banda_del_hablante(bc):
    """Con el metraje 1080x1920 en una ventana de 1080x800 la escala es 1.0."""
    bc.SRC_W, bc.SRC_H, bc.CHIN = 1080, 1920, 0.55
    y = bc.chin_at({"kind": "band", "zoom": 1.0, "anchor": 0.45})
    assert 1120 <= y <= 1920
    assert y < 1536, "la barbilla no puede caer en la zona de la plataforma"


def test_sin_layout_band_falla_claro(bc):
    """Un `band` sin layout es un bug del compilador, no un default silencioso."""
    bc.LAYOUT = {}
    with pytest.raises(Exception):
        bc.shot_geometry("band", 1.0, 0.45)
```

- [ ] **Step 2: Correr y ver que fallan**

```bash
.venv/bin/python -m pytest tests/test_triband_geometry.py -v
```

Esperado: FAIL — `bc` no tiene `triband_panels`.

- [ ] **Step 3: Implementación**

En `scripts/build-composition.py`, añadir tras `pip_panel()`:

```python
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
```

En `shot_geometry`, añadir la rama **antes** del `return` de `pip`:

```python
    if kind == "band":
        b = dict(triband_panels()["speaker"])
        b["objpos"] = f"50% {round(anchor * 100)}%"
        return b
```

En `chin_at`, cambiar la línea que elige el panel:

```python
    if kind == "band":
        b = triband_panels()["speaker"]
    else:
        b = split_panel() if kind == "split" else pip_panel()
```

En `configure`, añadir `LAYOUT` a los `global` y cargarlo:

```python
    global SHOTS, CARDS, VISUALS, SFX, MUSIC, KEYWORDS, CAPTIONS, LAYOUT
    ...
    LAYOUT = plan.get("layout") or {}
```

Y declarar `LAYOUT = {}` a nivel de módulo, junto a los demás globals, para que los tests
y un plan sin layout lo encuentren definido.

En `build_shots`, añadir `band` al mapa de clases:

```python
        cls = {"full": "vid", "split": "vid panel",
               "pip": "vid pip", "band": "vid band"}[s["kind"]]
```

- [ ] **Step 4: Correr y ver que pasan**

```bash
.venv/bin/python -m pytest tests/test_triband_geometry.py tests/test_shot_geometry.py -v
.venv/bin/python -m pytest -q --no-header 2>&1 | tail -3
```

Esperado: todos PASS · suite sin failed ni errors.

- [ ] **Step 5: Commit**

```bash
git add scripts/build-composition.py tests/test_triband_geometry.py
git commit -m "feat(layout): geometría de las tres bandas

Un `band` sin layout revienta con mensaje en vez de caer a un default
silencioso: sería un bug del compilador disfrazado de encuadre raro."
```

---

### Task 5: El subtítulo en banda y el gate del suelo

El cambio conceptual del plan: entre y820 y y1120 no hay metraje, así que el subtítulo no
puede tapar la cara. `chin_at()` deja de mandar y el gate se muda de «no invadir el 20 %
de la plataforma» a «no invadir la banda del hablante».

**Files:**
- Modify: `scripts/caption_metrics.py:36-75` (`measure_block`)
- Modify: `scripts/build-composition.py:1000-1040` (`build_captions`)
- Test: `tests/test_caption_band.py` (crear)

**Interfaces:**
- Consumes: `LAYOUT`, `triband_panels()` (Tarea 4).
- Produces: `measure_block(..., floor_px: int | None = None)` — cuando se pasa, `floor_top`
  se calcula contra ese suelo absoluto en vez de contra `canvas_h * SAFE_BOTTOM`.
  Constantes en `build-composition.py`: `BAND_CAP_PAD = 24` (aire bajo el techo de banda)
  y `BAND_CAP_MARGIN = 16` (holgura sobre la banda del hablante).

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/test_caption_band.py`:

```python
"""El subtítulo en la banda de texto del triband.

Deja de perseguir la barbilla —no hay metraje entre y820 y y1120— y pasa a
tope FIJO. Lo que se protege aquí es el gate: un bloque que se pase invade
la banda del hablante, y eso tiene que fallar la compilación, no el frame.
"""
import pytest

BASE = 66          # CAPTION_SIZE en REEL
FLOOR = 1104       # y1120 menos 16 px de holgura


def test_floor_px_manda_sobre_el_20_por_ciento(project_root):
    """Sin `floor_px` el suelo es 0.80*H; con él, el que se pase."""
    import caption_metrics as cm
    libre = cm.measure_block(["hola", "mundo"], BASE, None, "REEL", 1920,
                             cache_dir=project_root / "videos" / "10")
    band = cm.measure_block(["hola", "mundo"], BASE, None, "REEL", 1920,
                            floor_px=FLOOR,
                            cache_dir=project_root / "videos" / "10")
    assert libre["floor_top"] == 1536 - libre["n_lines"] * libre["line_h"]
    assert band["floor_top"] == FLOOR - band["n_lines"] * band["line_h"]


def test_dos_lineas_con_keyword_caben_en_la_banda(project_root):
    """66 x 1.22 = 81; 81 x 1.14 = 92. Dos líneas son 184 px desde y844 -> y1028."""
    import caption_metrics as cm
    m = cm.measure_block(["la", "primera", "es", "anime.js"], BASE, (3, 3), "REEL",
                         1920, floor_px=FLOOR,
                         cache_dir=project_root / "videos" / "10")
    assert m["max_size"] == 81
    assert m["line_h"] == 92
    assert 844 + 2 * m["line_h"] <= FLOOR


def test_tres_lineas_no_caben(project_root):
    """3 x 92 = 276; 844 + 276 = 1120, o sea encima de la banda del hablante."""
    assert 844 + 3 * 92 > FLOOR
```

- [ ] **Step 2: Correr y ver que fallan**

```bash
.venv/bin/python -m pytest tests/test_caption_band.py -v
```

Esperado: FAIL — `measure_block() got an unexpected keyword argument 'floor_px'`.

- [ ] **Step 3: Implementación en `caption_metrics.py`**

Cambiar la firma y la cuenta final de `measure_block`:

```python
def measure_block(words, base_size: int, keyword_range, fmt: str, canvas_h: int,
                  canvas_w: int = 1080, keyword_scale: float = KEYWORD_SCALE_MAX,
                  cache_dir=None, floor_px: int | None = None) -> dict:
```

Y sustituir la línea de `floor_top`:

```python
    # LA CUENTA QUE IMPORTA: con `max_size`, no con `base_size`.
    # En `full` el suelo es el 20 % que pinta la plataforma. En triband no: el
    # suelo es la banda del hablante, que está MUCHO más arriba, y lo pasa
    # quien llama con `floor_px`.
    suelo = floor_px if floor_px is not None else round(canvas_h * SAFE_BOTTOM)
    floor_top = suelo - n_lines * line_h
```

Actualizar el docstring del módulo añadiendo una tercera razón de existir:

```
  3. En el layout `triband` el suelo NO es el 20% de la plataforma sino el
     techo de la banda del hablante. La cuenta es la misma; cambia el suelo.
```

- [ ] **Step 4: Implementación en `build-composition.py`**

Añadir las constantes junto a los demás globals:

```python
# Aire bajo el techo de la banda de texto, y holgura sobre la del hablante.
# El tope es FIJO: un bloque de una línea y otro de dos tienen que empezar en
# la misma y, o el ojo ve el texto saltar entre bloques.
BAND_CAP_PAD = 24
BAND_CAP_MARGIN = 16
```

En `build_captions`, dentro del bucle, sustituir el bloque que va desde
`if sh and sh["kind"] == "pip":` hasta `top = min(top, floor_top)` por:

```python
        if sh and sh["kind"] == "band":
            # En triband el subtítulo no persigue la barbilla: entre el techo y
            # el suelo de su banda NO hay metraje, así que no puede tapar la
            # cara. Tope fijo, piel sin filete —el filete existe para sobrevivir
            # encima del metraje— y un gate que impide invadir al hablante.
            bandas = triband_panels()
            top = bandas["text"]["top"] + BAND_CAP_PAD
            suelo = bandas["speaker"]["top"] - BAND_CAP_MARGIN
            skin = "on-surface"
            m = caption_metrics.measure_block(disp, CAPTION_SIZE, krange, FMT, H, W,
                                              cache_dir=WORK, floor_px=suelo)
            bajo = top + m["n_lines"] * m["line_h"]
            if bajo > suelo:
                sys.exit(
                    f"bloque {ci} «{' '.join(u for _, u in ch)}»: {m['n_lines']} líneas "
                    f"acaban en y{bajo} y la banda del hablante empieza en "
                    f"y{bandas['speaker']['top']}. Trocea el bloque más corto.")
            n_lines = m["n_lines"]
        else:
            if sh and sh["kind"] == "pip":
                if not tops:
                    skin = "on-dark"
                tops.append(round(H * 0.60))
            elif sh and sh["kind"] != "off":
                tops.append(round(min(chin_at(sh) + H * 0.030, H * 0.80)))
            top = max(tops) if tops else round(H * 0.72)

            m = caption_metrics.measure_block(disp, CAPTION_SIZE, krange, FMT, H, W,
                                              cache_dir=WORK)
            n_lines, floor_top = m["n_lines"], m["floor_top"]
            top = min(top, floor_top)
```

Mantener intacto el bucle de `viz_skins` que precede a este bloque.

- [ ] **Step 5: Correr y ver que pasan**

```bash
.venv/bin/python -m pytest tests/test_caption_band.py tests/test_caption_metrics.py -v
.venv/bin/python -m pytest -q --no-header 2>&1 | tail -3
```

Esperado: todos PASS · suite sin failed ni errors · golden de la pieza 10 verde (no usa
`band`, así que entra por la rama `else`, idéntica a la de antes).

- [ ] **Step 6: Commit**

```bash
git add scripts/caption_metrics.py scripts/build-composition.py tests/test_caption_band.py
git commit -m "feat(captions): tope fijo y gate de banda en triband

El subtítulo deja de perseguir la barbilla: entre y820 y y1120 no hay
metraje. El gate se muda de 'no invadir el 20 % de la plataforma' a 'no
invadir la banda del hablante', con la misma mecánica de medida — que es
la que cazó la tercera línea de la pieza 11 y los 46 px de la 12."
```

---

### Task 6: Vendorizar los cinco logos con gate de resolución

Ninguna de las cinco marcas está en Simple Icons v16 (verificado: `animejs`, `anime`,
`motion`, `manus`, `kokonut`, `bklit` → 404).

**Files:**
- Modify: `scripts/fetch-logos.py`
- Test: `tests/test_logos_gate.py` (crear)

**Interfaces:**
- Consumes: nada.
- Produces: `check_raster(path, render_h) -> tuple[int, bool]` — `(alto_real, pasa)`.
  `VENDOR` dict con las cinco marcas y su URL verificada.

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_logos_gate.py`:

```python
"""El gate de resolución de las marcas raster.

Un favicon de 64 px pintado a 110 px en una card se ve blando, y es la clase
de error que no se nota en el JSON y sí en el frame. Se exige 2x.
"""
import importlib.util
import pytest

from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


@pytest.fixture(scope="session")
def fl():
    spec = importlib.util.spec_from_file_location("fetch_logos", SCRIPTS / "fetch-logos.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_64px_no_sirve_para_pintar_a_110(fl, tmp_path):
    from PIL import Image
    p = tmp_path / "chico.png"
    Image.new("RGBA", (64, 64)).save(p)
    alto, pasa = fl.check_raster(p, 110)
    assert alto == 64 and not pasa


def test_1024px_sirve_de_sobra(fl, tmp_path):
    from PIL import Image
    p = tmp_path / "grande.png"
    Image.new("RGBA", (1024, 1024)).save(p)
    alto, pasa = fl.check_raster(p, 110)
    assert alto == 1024 and pasa


def test_el_limite_es_exactamente_el_doble(fl, tmp_path):
    from PIL import Image
    for alto, esperado in ((220, True), (219, False)):
        p = tmp_path / f"m{alto}.png"
        Image.new("RGBA", (alto, alto)).save(p)
        assert fl.check_raster(p, 110)[1] is esperado


def test_las_cinco_marcas_estan_declaradas(fl):
    assert set(fl.VENDOR) == {"animejs", "motion", "kokonutui", "bklitui", "manus"}
```

- [ ] **Step 2: Correr y ver que falla**

```bash
.venv/bin/python -m pytest tests/test_logos_gate.py -v
```

Esperado: FAIL — `fetch_logos` no tiene `check_raster`.

- [ ] **Step 3: Implementación**

Añadir a `scripts/fetch-logos.py`:

```python
# Las cinco marcas de la pieza 15. NINGUNA está en Simple Icons v16
# (animejs, anime, motion, manus, kokonut, bklit → 404), así que se vendorizan
# desde su sitio oficial. `framer` sí existe pero Motion ya no es Framer
# Motion: sería la marca equivocada.
VENDOR = {
    "motion":    ("Motion",      "https://motion.dev/favicon.svg",      "svg"),
    "manus":     ("Manus",       "https://manus.im/icon.svg",           "svg"),
    "bklitui":   ("Bklit UI",    "https://bklit.com/apple-icon.png",    "png"),
    "kokonutui": ("Kokonut UI",  "https://kokonutui.com/icon.png",      "png"),
    # El favicon de Anime.js es 64x64 y NO pasa el gate. Se extrae del
    # og-image; si tampoco pasa, se para y se pregunta — no se sustituye por
    # una marca inventada.
    "animejs":   ("Anime.js", "https://animejs.com/media/pages/home/"
                              "066c76f87b-1787698629/generated-og-image.en.png", "png"),
}

# La marca se pinta a ~110 px en la card. Por debajo de 2x se ve blanda.
RASTER_MIN_SCALE = 2


def check_raster(path, render_h: int) -> tuple[int, bool]:
    """(alto_real, pasa_el_gate). Una marca raster necesita 2x su tamaño de render."""
    from PIL import Image
    with Image.open(path) as im:
        alto = im.height
    return alto, alto >= render_h * RASTER_MIN_SCALE
```

- [ ] **Step 4: Correr y ver que pasan**

```bash
.venv/bin/python -m pytest tests/test_logos_gate.py -v
.venv/bin/python -m pytest -q --no-header 2>&1 | tail -3
```

Esperado: todos PASS · suite sin failed ni errors.

- [ ] **Step 5: Descargar las cinco y comprobar el gate**

```bash
.venv/bin/python scripts/fetch-logos.py --vendor motion manus bklitui kokonutui animejs
ls -la assets/logos/
```

Si Anime.js no pasa el gate: **parar y preguntar**. No sustituir por otra marca.

- [ ] **Step 6: Commit**

```bash
git add scripts/fetch-logos.py tests/test_logos_gate.py assets/logos/ 
git commit -m "feat(logos): vendoriza las cinco marcas con gate de resolución

Ninguna está en Simple Icons v16. El gate de 2x es lo que impide que el
favicon de 64 px de Anime.js entre estirado sin que nadie lo note."
```

---

### Task 7: Los dos gestos nuevos — `glide-x` y `drop-in`

Ninguna animación existente entra en horizontal: `slide-in` viene de abajo (`y +14`),
`chip-in` escala. La petición —logo de derecha a izquierda, nombre de arriba abajo— pide
dos gestos que no están en la tabla de §6.

**Files:**
- Modify: `scripts/build-composition.py:1204` (el emisor de animaciones)
- Test: `tests/test_motion_gestos.py` (crear)

**Interfaces:**
- Consumes: el contrato de `anims`: `(kind, selector, delay, dur, *extra)`.
- Produces: `emit_anim(anim: tuple) -> str` — el JS de UNA animación, unido por `\n`.
  Dos `kind` nuevos aceptados:
  `("glide-x", sel, delay, dur)` → `x: 72 → 0`, `power2.out`, entrada por opacidad.
  `("drop-in", sel, delay, dur)` → `y: −22 → 0`, `power3.out`, entrada por opacidad.

> **El idioma del emisor.** No es `gsap.fromTo` suelto: es `tl.fromTo(sel, desde, hasta,
> t)` sobre una **timeline con tiempo absoluto**, donde `t = q(a[2])` sale de la tupla.
> La cadena desempaqueta `kind, sel, t, d = a[0], a[1], q(a[2]), a[3]`. Cualquier gesto
> nuevo tiene que respetar esa forma o quedará fuera de la línea de tiempo.

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/test_motion_gestos.py`:

```python
"""Los dos gestos del triband: horizontal y descendente.

`slide-in` entra desde ABAJO y `chip-in` escala; ninguno sirve para «de
derecha a izquierda». Recorrido pequeño a propósito (§6: el contenedor entra
por opacidad y lo que se mueve es su contenido).
"""
import pytest

GLIDE_X = 72
DROP_Y = -22


def test_glide_x_viaja_en_horizontal_y_acaba_en_cero(bc):
    js = bc.emit_anim(("glide-x", "#logo", 0.10, 0.45))
    assert f"x:{GLIDE_X}" in js.replace(" ", "")
    assert "x:0" in js.replace(" ", "")


def test_glide_x_no_usa_muelle(bc):
    """back.out() es lenguaje de dibujo animado y choca con una pieza de producto."""
    assert "back.out" not in bc.emit_anim(("glide-x", "#logo", 0.10, 0.45))
    assert "power2.out" in bc.emit_anim(("glide-x", "#logo", 0.10, 0.45))


def test_drop_in_cae_desde_arriba(bc):
    js = bc.emit_anim(("drop-in", "#nombre", 0.18, 0.40)).replace(" ", "")
    assert f"y:{DROP_Y}" in js
    assert "power3.out" in js


def test_los_dos_entran_por_opacidad(bc):
    for kind in ("glide-x", "drop-in"):
        assert "opacity:0" in bc.emit_anim((kind, "#x", 0.1, 0.4)).replace(" ", "")


def test_el_recorrido_es_pequeno(bc):
    """§6: «el recorrido y la escala de entrada son pequeños»."""
    assert GLIDE_X <= 80 and abs(DROP_Y) <= 30
```

> **Nota para el ejecutor:** el emisor vive dentro de una función más grande
> (`build-composition.py`, el `for a in anims:` de la línea ~1203). Antes de escribir estos
> tests, extrae la cadena `if kind == …` a una función de módulo:
>
> ```python
> def emit_anim(a) -> str:
>     """El JS de UNA animación. Extraído para poder probar un gesto sin renderizar."""
>     kind, sel, t, d = a[0], a[1], q(a[2]), a[3]
>     js: list[str] = []
>     ...  # la cadena entera, tal cual, sin tocar una línea
>     return "\n".join(js)
> ```
>
> y sustituye el cuerpo del bucle por `js.append(emit_anim(a))`. Es refactor **sin cambio
> de comportamiento**: la suite tiene que dar el mismo recuento antes y después.

- [ ] **Step 2: Correr y ver que fallan**

```bash
.venv/bin/python -m pytest tests/test_motion_gestos.py -v
```

Esperado: FAIL — `bc` no tiene `emit_anim`, o el `kind` no se reconoce.

- [ ] **Step 3: Extraer `emit_anim` y verificar que nada cambió**

```bash
.venv/bin/python -m pytest -q --no-header 2>&1 | tail -3
```

Esperado: **el mismo recuento que antes de tocar nada.** Si cambia, la extracción no fue
neutral: revertir y rehacerla.

- [ ] **Step 4: Añadir los dos gestos**

En la cadena de `emit_anim`, junto a los demás:

```python
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
```

- [ ] **Step 5: Correr y ver que pasan**

```bash
.venv/bin/python -m pytest tests/test_motion_gestos.py -v
.venv/bin/python -m pytest -q --no-header 2>&1 | tail -3
```

Esperado: todos PASS · suite sin failed ni errors.

- [ ] **Step 6: Commit**

```bash
git add scripts/build-composition.py tests/test_motion_gestos.py
git commit -m "feat(motion): glide-x y drop-in, los dos gestos del triband

Ninguno de los existentes entra en horizontal. Recorridos distintos a
propósito: el ojo lee dos elementos y no un bloque. Sin back.out()."
```

---

### Task 8: La card de logo y la card de grabación

El componente que ocupa la banda de arriba. Dos estados: la marca cuando se nombra la
herramienta, y la grabación cuando se explica — con el logo persistiendo de chip en la
cabecera, que es lo que ata la grabación a su palabra.

**Files:**
- Modify: `scripts/mockups.py` — añadir `tool_card` y `tool_recording`
- Test: `tests/test_tool_card.py` (crear)

**Interfaces:**
- Consumes: `glide-x`, `drop-in` (Tarea 7); `logos.mark()`; `triband_panels()` (Tarea 4).
- Produces:
  `tool_card(cid, slug, name, kicker="") -> (css, html, anims)` — la card de marca.
  `tool_recording(cid, slug, name, rect) -> (css, html, anims)` — la card de grabación con
  el chip de marca en cabecera. `rect` es `(left, top, w, h)` en coordenadas del lienzo.

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/test_tool_card.py`:

```python
"""Las cards de la banda de arriba.

Lo que protegen: que la card entre por OPACIDAD y lo que viaje sea su
contenido (§6), que el logo siga presente en la card de grabación, y que los
radios y la elevación salgan de los tokens y no a mano.
"""
import pytest


@pytest.fixture(scope="session")
def mk():
    import mockups
    return mockups


def test_la_card_no_viaja_su_contenido_si(mk):
    """§6: todo contenedor entra por opacidad; lo que se mueve es lo de dentro."""
    _, _, anims = mk.tool_card("tc", "motion", "Motion")
    kinds = {a[0] for a in anims}
    assert "glide-x" in kinds and "drop-in" in kinds
    sels = {a[1] for a in anims}
    assert not any(s.endswith("-card") for s in sels), "la card no se anima, entra fundiendo"


def test_el_logo_entra_en_horizontal_y_el_nombre_cae(mk):
    _, _, anims = mk.tool_card("tc", "motion", "Motion")
    por_kind = {a[0]: a[1] for a in anims}
    assert por_kind["glide-x"].endswith("-logo")
    assert por_kind["drop-in"].endswith("-name")


def test_el_nombre_entra_despues_del_logo(mk):
    """El retraso es lo que hace que se lean como dos elementos."""
    _, _, anims = mk.tool_card("tc", "motion", "Motion")
    d = {a[0]: a[2] for a in anims}
    assert d["drop-in"] > d["glide-x"]


def test_la_card_de_grabacion_conserva_la_marca(mk):
    """Sin el chip, 8 s de grabación se desatan de su nombre."""
    _, html, _ = mk.tool_recording("tr", "motion", "Motion", (60, 140, 960, 540))
    assert "Motion" in html


def test_ninguna_card_usa_negro_puro(mk):
    for css, _, _ in (mk.tool_card("a", "motion", "Motion"),
                      mk.tool_recording("b", "motion", "Motion", (60, 140, 960, 540))):
        low = css.lower().replace(" ", "")
        assert "#000000" not in low and "#000;" not in low


def test_el_radio_sale_de_los_tokens(mk):
    import tokens
    css, _, _ = mk.tool_card("tc", "motion", "Motion")
    assert f"{tokens.RADIUS['lg']}px" in css
```

- [ ] **Step 2: Correr y ver que fallan**

```bash
.venv/bin/python -m pytest tests/test_tool_card.py -v
```

Esperado: FAIL — `mockups` no tiene `tool_card`.

- [ ] **Step 3: Implementar los dos componentes**

Seguir el patrón de `keyword_hero` (`scripts/mockups.py:515`): devolver `(css, html, anims)`,
usar `C`, `FONT`, `MONO`, `RADIUS` de `tokens`, y `logos.mark(slug, size)` para la marca.

Reglas que los tests ya fijan y que el CSS tiene que cumplir:
- Radio `RADIUS['lg']` (24 px) y elevación con **hairline claro + sombra ancha**
  (`0 2px 6px rgba(0,0,0,.45), 0 18px 50px rgba(0,0,0,.55)`), nunca sombra dura.
- El aspecto 3D con `perspective()` + `rotateY()` **estáticos en un wrapper hijo**; GSAP
  solo toca `opacity`/`scale`/`x`/`y` del div exterior.
- `tool_recording` da a la grabación `border-radius` y `overflow:hidden`, con el chip de
  marca en una cabecera de altura fija.
- Manus lleva marco más marcado (su grabación es clara): parametrizar el grosor del
  hairline, no hornear un caso especial.

- [ ] **Step 4: Correr y ver que pasan**

```bash
.venv/bin/python -m pytest tests/test_tool_card.py -v
.venv/bin/python -m pytest -q --no-header 2>&1 | tail -3
```

Esperado: todos PASS · suite sin failed ni errors.

- [ ] **Step 5: Commit**

```bash
git add scripts/mockups.py tests/test_tool_card.py
git commit -m "feat(mockups): tool_card y tool_recording, la banda de arriba

El logo persiste de chip en la card de grabación: sin él, 8 s de
grabación se desatan del nombre que los justifica."
```

---

### Task 9: La pieza 15, de punta a punta

Producción, no código. Sigue el pipeline de `CLAUDE.md` §2 sin saltarse ningún paso.

**Files:**
- Create: `transcripts/15.json`, `cuts/15.json`, `assets/face-15.json`
- Create: `videos/15/edl.json`, `videos/15/screen-tour-{animejs,motiondev,kokonutui,bklitui,manusia}.json`
- Create: `videos/15/output.mp4`

- [ ] **Step 1: Formato, audio y transcripción**

```bash
scripts/detect-format.sh "VIDEOS ORIGINALES/1/pantalla.MOV"     # espera REEL
ffmpeg -i "VIDEOS ORIGINALES/1/pantalla.MOV" -vn -ac 1 -ar 16000 -c:a flac assets/audio/15.flac
.venv/bin/python scripts/transcribe.py assets/audio/15.flac transcripts/15.json
.venv/bin/python scripts/refine-timings.py assets/audio/15.flac transcripts/15.json
```

`refine-timings.py` sin `--write` solo informa. Re-transcribir suelto y empalmar cualquier
tramo con la alineación rota; después, volver a correrlo con `--write`.

- [ ] **Step 2: Cortes y respiraciones**

```bash
.venv/bin/python scripts/plan-cuts.py transcripts/15.json cuts/15.json \
    --audio assets/audio/15.flac
scripts/rough-cut.sh "VIDEOS ORIGINALES/1/pantalla.MOV" cuts/15.json out/15-rough.mp4
.venv/bin/python scripts/audit-breaths.py --piece 15
```

`audit-breaths.py` sale con código 1 si queda una respiración: **ahí se para el flujo.**
Audita el CORTE —voz sola— con el umbral de la FUENTE.

- [ ] **Step 3: Medir la cara**

```bash
.venv/bin/python scripts/measure-face.py out/15-rough.mp4 assets/face-15.json
```

Ajustar el `anchor` del EDL para que la barbilla caiga hacia y1350 — **por encima de
y1536**, que es lo que comprueba `test_la_barbilla_cae_sobre_la_banda_del_hablante`.

- [ ] **Step 4: Los cinco recorridos, a 16:9**

Salida **16:9** (la card lo es), recorte ~720×405 → 1.33×. Declarar en `exclude`:
- `kokonutui.mov`: la barra promocional rosa del borde superior.
- `bklitui.mov`: el tooltip de URL, abajo a la izquierda.

**Las coordenadas de `clicks` y `boxes` no se estiman.** Renderizar el tramo al tamaño
exacto de la card (`-vf scale=960:540`) y leerlas ahí.

- [ ] **Step 5: Escribir el EDL**

Cabecera con el bloque `layout` de la Tarea 2. Segmentos según §5 de la spec: hook y tesis
en `CLOSE`, las cinco herramientas y el CTA en `BAND`. El rótulo dice **Kokonut UI** aunque
el subtítulo transcriba «Coconut UI».

- [ ] **Step 6: Compilar y renderizar**

```bash
.venv/bin/python scripts/edl-compile.py --piece 15
.venv/bin/python scripts/build-composition.py --piece 15
npx hyperframes check videos/15/public
npx hyperframes render videos/15/public --sdr
```

Si `check` falla con `motion_selector_missing`, borrar `videos/15/public/index.motion.json`
(es de una composición anterior).

- [ ] **Step 7: Verificar SOBRE EL MP4**

```bash
ffprobe -v error -show_entries format=duration videos/15/output.mp4
ffmpeg -i videos/15/output.mp4 -vf blackdetect=d=0.05:pix_th=0.03 -f null - 2>&1 | grep black
```

Comprobar además: tinta más baja del subtítulo ≤ y1104 en los tramos `band`, barbilla por
encima de y1536, contraste WCAG AA de cada par nuevo de las cards, pico de audio y ganancia
de voz recuperada frente a la declarada.

**No dar por terminado un render mirando la fecha del archivo.** Esperar por el **PID
concreto**, nunca con `pgrep -f "hyperframes render"` — el propio shell que espera lleva
esa cadena y se caza a sí mismo.

- [ ] **Step 8: Commit**

```bash
git add transcripts/15.json cuts/15.json assets/face-15.json videos/15/
git commit -m "feat: pieza 15 en triband — 5 recursos para construir con Claude"
```

---

### Task 10: Documentar el modo en CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` §4 (modelo de capas), §5 (captions), §13 (estado)

- [ ] **Step 1: §4 — el layout triband junto a `full`/`split`/`pip`/`off`**

Documentar `band` como cuarto `kind`, la geometría de las tres bandas, y que la activación
es por segmento (`camera: "BAND"`) con geometría global.

- [ ] **Step 2: §5 — la excepción del subtítulo**

Dejar escrito que en triband el subtítulo NO persigue la barbilla, con los números:
tope y844, suelo y1104, dos líneas máximo, `66 × 1.22 = 81`, `81 × 1.14 = 92`.

- [ ] **Step 3: §13 — la pieza 15**

Anotar que `VIDEOS ORIGINALES/1` → **pieza 15** (la numeración de carpeta no es la de
pieza), y que los EDL de las piezas 12–14 se perdieron: su golden está saltado con razón.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: el layout triband y la pieza 15 en la bitácora"
```
