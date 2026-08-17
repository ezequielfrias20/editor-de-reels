# Higgsfield, logos de marca y mockups que se usan — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que la skill `editorial-retro-digital` genere sus visuales con Higgsfield (Kie como respaldo automático), incorpore logos de marcas reales entintados dentro de la paleta, y anime los mockups como interfaces que alguien usa.

**Architecture:** Se extiende en sitio. `gen.py` añade la capa de proveedor y comparte el ledger y la caché de `kie.py` importándolos (nunca reimplementándolos). `logos.py` + `fetch-logos.py` vendorizan Simple Icons y calculan el entintado por contraste. `anims.py` se extrae de `build-composition.py` y recibe los siete kinds de gesto de interfaz. `mockups.py` gana cursor, logos y `app_switch`.

**Tech Stack:** Python 3.11 (stdlib + Pillow + fontTools + OpenCV), pytest, GSAP 3, HyperFrames CLI 0.7.72, ffmpeg 8.1.2, Higgsfield MCP, Kie AI REST.

**Spec:** [`docs/superpowers/specs/2026-08-09-higgsfield-logos-mockups-design.md`](../specs/2026-08-09-higgsfield-logos-mockups-design.md)

---

## Mapa de archivos

| Archivo | Responsabilidad |
| --- | --- |
| `scripts/anims.py` **(nuevo)** | `FPS`, `q()`, `emit()` — traducción kind → GSAP; `gestures_to_offsets()` |
| `scripts/logos.py` **(nuevo)** | `brand_tone()` (contraste calculado) y `mark()` (SVG entintado) |
| `scripts/fetch-logos.py` **(nuevo)** | Vendoriza SVG de Simple Icons + `meta.json` |
| `scripts/gen.py` **(nuevo)** | `plan` · `import` · `fallback` · `credits`. Importa la caché de `kie.py` |
| `scripts/kie.py` | **No se toca.** Pasa a ser el respaldo |
| `scripts/mockups.py` | Cursor, logos en cabecera, gestos, `app_switch`, tokens de señal |
| `scripts/build-composition.py` | Importa `anims`; `build_visuals` entiende `gestures`, `logo` y `gen` |
| `scripts/new-piece.sh`, `detect-format.sh` | Aceptan `VIDEOS ORIGINALES/<n>/video.MOV` |
| `tests/` **(nuevo)** | pytest sobre las partes puras |

**Convención de tuplas que NO cambia:** los mockups siguen emitiendo
`(kind, selector_relativo, offset_s, dur_s, *extra)` y el offset sigue siendo
relativo al inicio del visual.

---

### Task 0: Andamio — git, pytest y el paquete de tests

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_smoke.py`

- [ ] **Step 1: Inicializar git**

El proyecto no es un repo y el plan commitea en cada tarea. El `.gitignore` ya
existe y excluye `VIDEOS ORIGINALES/`, `out/`, `assets/audio/` y los renders, así
que no entra nada pesado.

```bash
cd /Users/ezequielfrias/Documents/mi-universo/marca-personal/editor-videos
git init
git add -A
git status --short | wc -l
```

Esperado: un número por debajo de 200. Si aparece algún `.MOV`, `.mp4` o `.flac`
en `git status`, PARAR y revisar `.gitignore` antes de commitear.

- [ ] **Step 2: Verificar que no se cuela nada pesado**

```bash
git status --short | grep -E '\.(MOV|mp4|flac|wav)$' || echo "limpio"
```

Esperado: `limpio`

- [ ] **Step 3: Commit inicial**

```bash
git commit -q -m "chore: inicializar repositorio del estudio"
git log --oneline
```

- [ ] **Step 4: Instalar pytest**

```bash
python3 -m pip install pytest
python3 -m pytest --version
```

Esperado: `pytest 8.x.x`

- [ ] **Step 5: Crear `tests/conftest.py`**

Los scripts viven dentro de la skill y se importan por ruta; `conftest.py` los
pone en `sys.path` para que los tests hagan `import logos`, `import anims`.

```python
"""Pone los scripts de la skill en sys.path.

`scripts/` es un enlace a .claude/skills/editorial-retro-digital/scripts, así que
se resuelve el enlace para importar los módulos reales y no una copia.
"""
import sys
from pathlib import Path

SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
sys.path.insert(0, str(SCRIPTS))
```

- [ ] **Step 6: Crear `tests/test_smoke.py`**

```python
def test_los_scripts_son_importables():
    import mockups
    assert mockups.C["ink"] == "#2A241F"
```

- [ ] **Step 7: Ejecutar**

Run: `python3 -m pytest tests/ -q`
Expected: `1 passed`

- [ ] **Step 8: Commit**

```bash
git add tests/
git commit -q -m "test: andamio de pytest para los scripts de la skill"
```

---

### Task 1: `anims.py` — extraer `FPS`, `q()` y `emit()`

Extracción pura: **el HTML generado tiene que salir byte a byte idéntico.**

**Files:**
- Create: `scripts/anims.py`
- Modify: `scripts/build-composition.py` (imports; líneas 1079-1151)
- Test: `tests/test_anims.py`

- [ ] **Step 1: Guardar la referencia de oro ANTES de tocar nada**

```bash
cd /Users/ezequielfrias/Documents/mi-universo/marca-personal/editor-videos
scripts/build-composition.py --project . --piece 1
cp videos/1/public/index.html /tmp/oro-index.html
wc -l /tmp/oro-index.html
```

Esperado: ~657 líneas. Si el comando falla, PARAR: hay que arreglar eso antes de
refactorizar.

- [ ] **Step 2: Escribir el test que falla**

`tests/test_anims.py`:

```python
import anims


def test_q_cuantiza_a_frame():
    assert anims.q(1.0 / 3) == 0.3333
    assert anims.q(0.51) == 0.5
    assert anims.q(2) == 2.0


def test_emit_slide_in_guiado_por_opacidad():
    js = anims.emit("slide-in", "#x", 1.0, 0.30)
    linea = "\n".join(js)
    assert "opacity: 0, y: 16" in linea
    assert 'ease: "power2.out"' in linea
    assert "1.0000" in linea


def test_emit_no_usa_muelles_en_ninguna_entrada():
    """§7: back.out rebota como resorte y es lenguaje de dibujo animado."""
    for kind in ("slide-in", "drop-in", "title", "scale-pop", "punch",
                 "stamp", "hud-in"):
        assert "back." not in "\n".join(anims.emit(kind, "#x", 0.0, 0.3))


def test_emit_kind_desconocido_falla_ruidosamente():
    import pytest
    with pytest.raises(ValueError, match="kind desconocido"):
        anims.emit("no-existe", "#x", 0.0, 0.3)
```

- [ ] **Step 3: Verificar que falla**

Run: `python3 -m pytest tests/test_anims.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'anims'`

- [ ] **Step 4: Crear `scripts/anims.py`**

Mover **literalmente** el cuerpo del bucle `for a in anims:` de
`build-composition.py` (líneas 1079-1151), incluidos todos sus comentarios, a una
función. Cada rama pasa de `js.append(...)` a `out.append(...)`.

```python
#!/usr/bin/env python3
"""Traducción de gestos a tweens de GSAP, y de tiempos absolutos a offsets.

Extraído de build-composition.py: es la parte que más crece —cada mockup nuevo
trae gestos nuevos— y la comparten las tarjetas y los mockups.

El contrato de entrada no cambia:

    (kind, selector, offset_s, dur_s, *extra)

`FPS` vive aquí porque `q()` lo necesita y los dos formatos del proyecto son de
30 fps (CLAUDE.md §1).
"""

FPS = 30


def q(t):
    """Cuantiza a frame y recorta a 4 decimales."""
    return round(round(float(t) * FPS) / FPS, 4)


def emit(kind, sel, t, d, *extra):
    """Devuelve las líneas de JS/GSAP de un gesto. `t` se cuantiza aquí."""
    t = q(t)
    out = []
    a = (kind, sel, t, d) + extra          # compat con el desempaquetado a[4], a[5]

    if kind == "slide-in":
        # Guiado por la OPACIDAD: el desplazamiento solo acompaña al fundido.
        out.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, y: 16 }}, '
                   f'{{ opacity: 1, y: 0, duration: {round(d*1.25,4)}, '
                   f'ease: "power2.out" }}, {t:.4f});')
    # ... (el resto de ramas, copiadas TAL CUAL de build-composition.py:1082-1151:
    #      drop-in, title, scale-pop, grow-x, grow-x-pct, count, punch, sweep,
    #      typein, stamp, hud-in, cam-kb, cam-push)
    else:
        raise ValueError(f"kind desconocido: {kind!r}")
    return out
```

**Importante:** conservar los comentarios largos de cada rama. Documentan
decisiones ya pagadas (por qué `expo.out` y no `back.out`, por qué el sweep tiene
recorrido y el karaoke no). Perderlos en la extracción es perder la bitácora.

- [ ] **Step 5: Verificar los tests**

Run: `python3 -m pytest tests/test_anims.py -q`
Expected: `4 passed`

- [ ] **Step 6: Conectar `build-composition.py`**

Reemplazar `def q(t)` (líneas 161-163) y `FPS = 30` (línea 30) por el import, y
el bucle emisor por la llamada:

```python
import anims  # noqa: E402  — emisor de tweens GSAP
from anims import FPS, q  # noqa: E402
```

```python
    for a in anims_list:
        js.extend(anims.emit(a[0], a[1], a[2], a[3], *a[4:]))
```

Renombrar la variable local `anims` a `anims_list` en `build()` para que no tape
al módulo. Verificar que no queda ningún otro uso:

```bash
grep -n "for a in anims\|anims\b" scripts/build-composition.py | head -20
```

- [ ] **Step 7: Verificar que el HTML sale IDÉNTICO**

Es la prueba real de que la extracción fue pura.

```bash
scripts/build-composition.py --project . --piece 1
diff /tmp/oro-index.html videos/1/public/index.html && echo "IDÉNTICO"
```

Expected: `IDÉNTICO`. Si hay diferencias, la extracción cambió comportamiento:
volver al paso 4.

- [ ] **Step 8: Commit**

```bash
git add scripts/anims.py scripts/build-composition.py tests/test_anims.py
git commit -q -m "refactor: extraer el emisor de tweens GSAP a anims.py"
```

---

### Task 2: `anims.py` — `gestures_to_offsets()`

**Files:**
- Modify: `scripts/anims.py`
- Test: `tests/test_anims.py`

- [ ] **Step 1: Escribir el test que falla**

Añadir a `tests/test_anims.py`:

```python
import pytest


def test_gestures_pasan_de_absoluto_a_offset():
    g = [{"do": "scroll", "at": 19.80, "dy": -120},
         {"do": "click",  "at": 21.35, "target": "r2"},
         {"do": "badge",  "at": 22.60}]
    r = anims.gestures_to_offsets(g, visual_start=18.45)
    assert r["scroll_at"] == [(1.35, -120)]
    assert r["click_at"] == [(2.90, "r2")]
    assert r["badge_at"] == [4.15]


def test_gesto_antes_del_visual_es_un_error_de_plan():
    """Sin la guarda, un gesto mal declarado animaría en t=0 sin avisar."""
    with pytest.raises(ValueError, match="antes del inicio"):
        anims.gestures_to_offsets([{"do": "badge", "at": 5.0}], visual_start=10.0)


def test_gesto_desconocido_falla():
    with pytest.raises(ValueError, match="gesto desconocido"):
        anims.gestures_to_offsets([{"do": "bailar", "at": 1.0}], visual_start=0.0)


def test_switch_lleva_target():
    r = anims.gestures_to_offsets(
        [{"do": "switch", "at": 28.40, "target": "notion"}], visual_start=27.0)
    assert r["switch_at"] == [(1.40, "notion")]
```

- [ ] **Step 2: Verificar que falla**

Run: `python3 -m pytest tests/test_anims.py -q`
Expected: FAIL — `AttributeError: module 'anims' has no attribute 'gestures_to_offsets'`

- [ ] **Step 3: Implementar**

Añadir a `scripts/anims.py`:

```python
# Cada gesto del plan se declara con su tiempo ABSOLUTO de la línea del corte
# (spec §4.4: un gesto de interfaz sin palabra detrás no existe, y la palabra
# vive en esa línea). El mockup los recibe ya relativos a su propio inicio.
_GESTOS = {"click":  ("click_at",  "target"),
           "scroll": ("scroll_at", "dy"),
           "switch": ("switch_at", "target"),
           "state":  ("state_at",  "target"),
           "badge":  ("badge_at",  None)}


def gestures_to_offsets(gestures, visual_start):
    """Tiempos absolutos del corte → offsets por parámetro con nombre del mockup."""
    out = {p: [] for p, _ in _GESTOS.values()}
    for g in gestures:
        do = g.get("do")
        if do not in _GESTOS:
            raise ValueError(f"gesto desconocido: {do!r} (usa {sorted(_GESTOS)})")
        param, arg = _GESTOS[do]
        off = round(float(g["at"]) - float(visual_start), 4)
        if off < 0:
            raise ValueError(
                f"el gesto {do}@{g['at']} cae antes del inicio del visual "
                f"({visual_start}) — revisa el remapeo del transcript")
        out[param].append(off if arg is None else (off, g[arg]))
    return out
```

- [ ] **Step 4: Verificar**

Run: `python3 -m pytest tests/test_anims.py -q`
Expected: `8 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/anims.py tests/test_anims.py
git commit -q -m "feat: traducir gestos de tiempo absoluto a offsets del visual"
```

---

### Task 3: `anims.py` — los siete kinds de gesto de interfaz

**Files:**
- Modify: `scripts/anims.py`
- Test: `tests/test_anims.py`

- [ ] **Step 1: Escribir los tests que fallan**

```python
def test_cursor_to_viaja_con_x_y_no_con_left_top():
    """§9: left/top se cuantizan a píxel entero y tartamudean."""
    js = "\n".join(anims.emit("cursor-to", "#cur", 1.0, 0.42, 300, 780))
    assert "x: 300" in js and "y: 780" in js
    assert "left:" not in js and "top:" not in js
    assert 'ease: "power2.inOut"' in js


def test_click_hunde_el_cursor_y_abre_un_anillo():
    js = "\n".join(anims.emit("click", "#cur", 2.0, 0.30))
    assert "scale: 0.88" in js          # el cursor se hunde
    assert "#cur-ring" in js            # y el anillo se abre
    assert "opacity: 0" in js           # y se apaga


def test_scroll_desplaza_la_lista():
    js = "\n".join(anims.emit("scroll", "#list", 1.0, 0.55, -120))
    assert "y: -120" in js
    assert 'ease: "power2.inOut"' in js


def test_count_to_acepta_sufijo_y_no_esta_cableado_a_porciento():
    js = "\n".join(anims.emit("count-to", "#n", 1.0, 0.8, 40, " ventas"))
    assert '" ventas"' in js
    assert '"%"' not in js


def test_draw_usa_stroke_dashoffset():
    js = "\n".join(anims.emit("draw", "#bar", 1.0, 0.6))
    assert "strokeDashoffset" in js


def test_badge_in_pulsa_una_sola_vez():
    """§7: el movimiento actúa, no respira. Nada de repeat."""
    js = "\n".join(anims.emit("badge-in", "#b", 1.0, 0.34))
    assert "repeat" not in js


def test_row_state_saca_el_chip_viejo_y_sella_el_nuevo():
    js = "\n".join(anims.emit("row-state", "#viejo", 1.0, 0.34, "#nuevo"))
    assert "#viejo" in js and "#nuevo" in js
    assert "scale: 1.1" in js           # el nuevo llega de más grande
```

- [ ] **Step 2: Verificar que fallan**

Run: `python3 -m pytest tests/test_anims.py -q -k "cursor or click or scroll or count_to or draw or badge or row_state"`
Expected: 7 FAILED con `ValueError: kind desconocido`

- [ ] **Step 3: Implementar las siete ramas**

Insertar en `emit()`, antes del `else: raise`:

```python
    elif kind == "cursor-to":
        # El cursor VIAJA. x/y y nunca left/top: §9, left/top se cuantizan a
        # píxel entero y tartamudean. power2.inOut porque una mano acelera y
        # frena, no arranca de golpe.
        out.append(f'tl.to(\'{sel}\', {{ x: {a[4]}, y: {a[5]}, '
                   f'duration: {d}, ease: "power2.inOut" }}, {t:.4f});')
    elif kind == "click":
        # El tap son dos cosas a la vez: el cursor se hunde un instante y un
        # anillo se abre desde el punto y se apaga. El hundimiento es corto
        # (0.06 s) porque un clic real no tiene duración apreciable.
        out.append(f'tl.to(\'{sel}\', {{ scale: 0.88, duration: 0.06, '
                   f'ease: "power2.out" }}, {t:.4f});')
        out.append(f'tl.to(\'{sel}\', {{ scale: 1, duration: 0.10, '
                   f'ease: "power2.out" }}, {t + 0.06:.4f});')
        out.append(f'tl.fromTo(\'{sel}-ring\', {{ opacity: 0.55, scale: 0.25 }}, '
                   f'{{ opacity: 0, scale: 1, duration: {d}, '
                   f'ease: "power2.out" }}, {t:.4f});')
    elif kind == "scroll":
        # La lista se desplaza. Es contenido moviéndose dentro de un marco
        # quieto, así que la curva es la de una mano: power2.inOut.
        out.append(f'tl.to(\'{sel}\', {{ y: {a[4]}, duration: {d}, '
                   f'ease: "power2.inOut" }}, {t:.4f});')
    elif kind == "row-state":
        # El estado de una fila CAMBIA: el chip viejo sale y el nuevo se sella
        # encima. Mismo gesto que `stamp` pero con relevo, porque aquí hay algo
        # que se sustituye, no algo que llega a un hueco vacío.
        out.append(f'tl.to(\'{sel}\', {{ opacity: 0, scale: 0.96, '
                   f'duration: {round(d*0.45,4)}, ease: "power2.in" }}, {t:.4f});')
        out.append(f'tl.fromTo(\'{a[4]}\', {{ opacity: 0, scale: 1.1 }}, '
                   f'{{ opacity: 1, scale: 1, duration: {round(d*0.8,4)}, '
                   f'ease: "power3.out" }}, {t + round(d*0.35,4):.4f});')
    elif kind == "count-to":
        # Contador genérico. El `count` de siempre está cableado a "%", que solo
        # servía para el embudo de la pieza 1; aquí el sufijo es un parámetro.
        out.append('(function(){ const o = { v: 0 }; tl.to(o, { v: ' + str(a[4]) +
                   f', duration: {d}, ease: "power2.out", onUpdate: function() {{'
                   f' const el = document.querySelector(\'{sel}\');'
                   f' if (el) el.textContent = Math.round(o.v) + "{a[5]}"; }} }}, '
                   f'{t:.4f}); }})();')
    elif kind == "draw":
        # La barra se DIBUJA. stroke-dashoffset en vez de width porque así el
        # trazo crece por su propio recorrido y no reflowea la caja.
        out.append(f'tl.fromTo(\'{sel}\', {{ strokeDashoffset: 1 }}, '
                   f'{{ strokeDashoffset: 0, duration: {d}, '
                   f'ease: "power2.inOut" }}, {t:.4f});')
    elif kind == "badge-in":
        # Llega una notificación: el badge se sella y el logo acusa el golpe UNA
        # vez. Sin `repeat`: §7 prohíbe el wobble ocioso, y un badge que late en
        # bucle es exactamente eso.
        out.append(f'tl.fromTo(\'{sel}\', {{ opacity: 0, scale: 1.18 }}, '
                   f'{{ opacity: 1, scale: 1, duration: {round(d*1.2,4)}, '
                   f'ease: "power3.out" }}, {t:.4f});')
```

- [ ] **Step 4: Verificar**

Run: `python3 -m pytest tests/test_anims.py -q`
Expected: `15 passed`

- [ ] **Step 5: Verificar que la pieza 1 sigue idéntica**

Los kinds nuevos no los usa nadie todavía, así que el HTML no puede cambiar.

```bash
scripts/build-composition.py --project . --piece 1
diff /tmp/oro-index.html videos/1/public/index.html && echo "IDÉNTICO"
```

Expected: `IDÉNTICO`

- [ ] **Step 6: Commit**

```bash
git add scripts/anims.py tests/test_anims.py
git commit -q -m "feat: siete kinds de gesto de interfaz (cursor, clic, scroll, estado)"
```

---

### Task 4: `logos.py` — `brand_tone()` calculado

**Files:**
- Create: `scripts/logos.py`
- Test: `tests/test_logos.py`

- [ ] **Step 1: Escribir el test que falla**

`tests/test_logos.py`:

```python
import logos


def test_contraste_conocido():
    """Referencias ya verificadas en CLAUDE.md §4."""
    assert round(logos.contrast("#2A241F", "#DC9E5A"), 2) == 6.63
    assert round(logos.contrast("#2A241F", "#EFEAE0"), 2) == 12.78


def test_whatsapp_crudo_no_se_lee_sobre_crema():
    """El verde oficial da 1.88:1 — por debajo del mínimo de 3:1."""
    assert logos.contrast("#25D366", logos.CARD) < 3.0


def test_brand_tone_entinta_hasta_que_se_lee():
    c = logos.brand_tone("#25D366")
    assert c == "#269E51"
    assert logos.contrast(c, logos.CARD) >= 3.0


def test_el_30_por_ciento_es_un_SUELO_de_paleta_no_solo_de_legibilidad():
    """Excel ya se lee crudo (5.53:1) y aun así se entinta: el suelo del 30 %
    es lo que lo hace pertenecer a la paleta apagada, no lo que lo hace legible."""
    assert logos.contrast("#217346", logos.CARD) > 3.0
    assert logos.brand_tone("#217346") == "#245B3A"


def test_una_marca_negra_nunca_devuelve_negro_puro():
    """Notion es #000000. Mezclarlo hacia la tinta da #0D0B09 — MÁS oscuro que
    --ink, o sea negro puro, que §4 prohíbe explícitamente."""
    assert logos.brand_tone("#000000") == logos.INK


def test_brand_tone_nunca_devuelve_algo_ilegible():
    for h in ("#25D366", "#217346", "#000000", "#EA4335", "#D97757", "#FFFF00"):
        assert logos.contrast(logos.brand_tone(h), logos.CARD) >= 3.0
```

- [ ] **Step 2: Verificar que falla**

Run: `python3 -m pytest tests/test_logos.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'logos'`

- [ ] **Step 3: Implementar**

`scripts/logos.py`:

```python
#!/usr/bin/env python3
"""Logos de marca reales dentro de la paleta crema/tinta.

Los SVG salen de Simple Icons (CC0), vendorizados en assets/logos/ por
fetch-logos.py. Aquí solo se entintan y se maquetan.

El color de marca NO se escribe a mano: se calcula, igual que la ganancia de los
efectos (§13), la barbilla (§6) y el LUT (§8).
"""

INK = "#2A241F"
CARD = "#F9F9F7"
PAPER = "#EFEAE0"

# Suelo de mezcla hacia la tinta. No es un mínimo de legibilidad —muchas marcas
# ya se leen crudas— sino el peaje que las hace PERTENECER a la paleta apagada
# del proyecto. La escalera sube solo cuando además hace falta para leerse.
_MIX = (0.30, 0.40, 0.50, 0.60, 0.70)


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(t):
    return "#%02X%02X%02X" % t


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(h):
    r, g, b = _rgb(h)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a, b):
    x, y = luminance(a), luminance(b)
    x, y = max(x, y), min(x, y)
    return (x + 0.05) / (y + 0.05)


def _lerp(a, b, t):
    return _hex(tuple(round(x + (y - x) * t) for x, y in zip(_rgb(a), _rgb(b))))


def brand_tone(hex_marca, ratio_min=3.0, surface=CARD):
    """Color de marca bajado a la paleta: se mezcla HACIA LA TINTA.

    Mezclarlo hacia el crema —el instinto— lo ACLARA y lo vuelve ilegible sobre
    papel crema. Hacia la tinta desatura y oscurece a la vez, que es lo que hace
    una imprenta al bajar un color de marca a papel crudo.

    `ratio_min` es 3.0 y no 4.5 porque un logo es un objeto gráfico no textual.
    """
    # Una marca ya más oscura que la tinta (Notion es #000000) no se puede
    # entintar: mezclar hacia --ink la ACLARARÍA hacia el negro puro que §4
    # prohíbe. Se queda en tinta y ya está.
    if luminance(hex_marca) <= luminance(INK):
        return INK
    for mix in _MIX:
        c = _lerp(hex_marca, INK, mix)
        if contrast(c, surface) >= ratio_min:
            return c
    return INK
```

- [ ] **Step 4: Verificar**

Run: `python3 -m pytest tests/test_logos.py -q`
Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/logos.py tests/test_logos.py
git commit -q -m "feat: entintado de logos de marca calculado por contraste"
```

---

### Task 5: `fetch-logos.py` — vendorizar Simple Icons

**Files:**
- Create: `scripts/fetch-logos.py`
- Create: `assets/logos/` (lo crea el script)

- [ ] **Step 1: Implementar**

`scripts/fetch-logos.py` (gemelo de `fetch-fonts.py`):

```python
#!/usr/bin/env python3
"""Vendoriza logos de marca desde Simple Icons.

    scripts/fetch-logos.py whatsapp microsoftexcel

Se vendoriza por lo mismo que las fuentes y los efectos: la CDN puede caerse o
cambiar y el proyecto tiene que seguir renderizando igual.

Los archivos SVG de Simple Icons son CC0. Las marcas siguen siendo de sus
dueños; el uso del proyecto es editorial-nominativo (se nombra la herramienta
que nombra el guion).
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

CDN = "https://cdn.jsdelivr.net/npm/simple-icons@v16/icons/{slug}.svg"
API = "https://raw.githubusercontent.com/simple-icons/simple-icons/master/_data/simple-icons.json"


def _root():
    cwd = Path.cwd().resolve()
    for d in (cwd, *cwd.parents):
        if (d / ".env").exists() or (d / "VIDEOS ORIGINALES").is_dir():
            return d
    return cwd


ROOT = _root()
OUT = ROOT / "assets" / "logos"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "editor-videos/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode()


def check(svg, slug):
    """Contrato de Simple Icons: viewBox 0 0 24 24 y UN solo path.

    Se verifica porque el entintado da por hecho esa forma. Un SVG con otra
    estructura entraría y saldría mal coloreado sin que nadie se entere.
    """
    if 'viewBox="0 0 24 24"' not in svg:
        sys.exit(f"{slug}: viewBox inesperado — no es un icono de Simple Icons")
    paths = re.findall(r"<path\b[^>]*\bd=\"([^\"]+)\"", svg)
    if len(paths) != 1:
        sys.exit(f"{slug}: {len(paths)} paths, se esperaba 1")
    return paths[0]


def main():
    slugs = sys.argv[1:]
    if not slugs:
        sys.exit("uso: fetch-logos.py <slug> [<slug> ...]")

    OUT.mkdir(parents=True, exist_ok=True)
    meta_path = OUT / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    catalogo = {i["slug"] if "slug" in i else "": i for i in json.loads(get(API))["icons"]} \
        if False else None   # el catálogo se consulta por título más abajo
    todos = json.loads(get(API))["icons"]
    por_slug = {}
    for i in todos:
        s = i.get("slug") or re.sub(r"[^a-z0-9]", "", i["title"].lower())
        por_slug[s] = i

    for slug in slugs:
        if slug not in por_slug:
            sys.exit(f"«{slug}» no existe en Simple Icons — busca el slug en "
                     f"https://simpleicons.org (no inventes un logo)")
        try:
            svg = get(CDN.format(slug=slug))
        except urllib.error.HTTPError as e:
            sys.exit(f"{slug}: HTTP {e.code} bajando el SVG")
        d = check(svg, slug)
        (OUT / f"{slug}.svg").write_text(svg, encoding="utf-8")
        meta[slug] = {"title": por_slug[slug]["title"],
                      "hex": "#" + por_slug[slug]["hex"], "d": d}
        print(f"✓ {slug:18} {meta[slug]['title']:22} #{por_slug[slug]['hex']}")

    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"→ {meta_path.relative_to(ROOT)}  ({len(meta)} marcas)")


if __name__ == "__main__":
    main()
```

Borrar la línea muerta `catalogo = ... if False else None` al escribirlo — está
aquí solo para señalar que **no** se debe consultar el catálogo dos veces.

- [ ] **Step 2: Ejecutar con los slugs que piden los guiones**

```bash
chmod +x scripts/fetch-logos.py
scripts/fetch-logos.py whatsapp microsoftexcel
```

Expected:
```
✓ whatsapp           WhatsApp               #25D366
✓ microsoftexcel     Microsoft Excel        #217346
→ assets/logos/meta.json  (2 marcas)
```

- [ ] **Step 3: Verificar que un slug inexistente falla ruidosamente**

```bash
scripts/fetch-logos.py estamarcanoexiste; echo "salida=$?"
```

Expected: mensaje `«estamarcanoexiste» no existe en Simple Icons` y `salida=1`.

- [ ] **Step 4: Comprobar el hex frente al valor esperado**

```bash
python3 -c "
import json; m=json.load(open('assets/logos/meta.json'))
assert m['whatsapp']['hex']=='#25D366', m['whatsapp']
assert m['whatsapp']['d'].startswith('M'), 'el path no se guardó'
print('meta.json correcto')"
```

- [ ] **Step 5: Versionar los logos**

Son ligeros (unos 500 bytes) y son la fuente de verdad offline: se versionan.

```bash
git add scripts/fetch-logos.py assets/logos/
git commit -q -m "feat: vendorizar logos de marca desde Simple Icons"
```

---

### Task 6: `logos.py` — `mark()`

**Files:**
- Modify: `scripts/logos.py`
- Test: `tests/test_logos.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_mark_en_tinta_por_defecto():
    css, html = logos.mark("viz-01", "whatsapp", 64)
    assert 'viewBox="0 0 24 24"' in html
    assert logos.INK.lower() in html.lower()


def test_mark_en_brand_usa_el_tono_calculado():
    css, html = logos.mark("viz-01", "whatsapp", 64, tone="brand")
    assert "#269E51" in html


def test_el_css_va_prefijado_por_el_id_del_visual():
    """Dos mockups en la misma composición no se pueden pisar."""
    css, _ = logos.mark("viz-01", "whatsapp", 64)
    for regla in css.strip().split("}"):
        if regla.strip():
            assert '[data-viz-id="viz-01"]' in regla


def test_mark_no_lleva_transform_de_colocacion():
    """§9: GSAP toma el transform en cuanto anima y descarta el centrado."""
    css, html = logos.mark("viz-01", "whatsapp", 64)
    assert "translate(-50%" not in css + html


def test_marca_desconocida_falla():
    import pytest
    with pytest.raises(KeyError, match="microsoftword"):
        logos.mark("viz-01", "microsoftword", 64)
```

- [ ] **Step 2: Verificar que falla**

Run: `python3 -m pytest tests/test_logos.py -q -k mark`
Expected: 5 FAILED con `AttributeError: module 'logos' has no attribute 'mark'`

- [ ] **Step 3: Implementar**

Añadir a `scripts/logos.py`:

```python
import json
from pathlib import Path


def _root():
    cwd = Path.cwd().resolve()
    for d in (cwd, *cwd.parents):
        if (d / ".env").exists() or (d / "VIDEOS ORIGINALES").is_dir():
            return d
    return cwd


_META = None


def meta():
    """Lee assets/logos/meta.json una vez."""
    global _META
    if _META is None:
        p = _root() / "assets" / "logos" / "meta.json"
        if not p.exists():
            raise FileNotFoundError(
                "falta assets/logos/meta.json — corre scripts/fetch-logos.py <slug>")
        _META = json.loads(p.read_text())
    return _META


def mark(cid, slug, size, tone="ink"):
    """Un logo sobre pastilla crema. Devuelve (css, html) como los mockups.

    El <svg> va inline: no es media, así que no necesita `id` (la trampa del §13
    es de <audio> y <video>). Pero sí le aplica §9: nada de transform de
    colocación, que GSAP descartaría al animarlo.
    """
    m = meta()
    if slug not in m:
        raise KeyError(f"{slug}: no vendorizado — corre scripts/fetch-logos.py {slug}")
    fill = INK if tone == "ink" else brand_tone(m[slug]["hex"])
    pad = round(size * 0.28)
    sel = f'.viz[data-viz-id="{cid}"]'
    css = f"""
{sel} .lg {{ display:flex; align-items:center; justify-content:center;
  width:{size + pad * 2}px; height:{size + pad * 2}px; background:{CARD};
  border:1px solid rgba(42,36,31,.12); border-radius:{round(size * 0.22)}px;
  box-shadow:0 1px 3px rgba(42,36,31,.08),0 4px 16px rgba(42,36,31,.04); }}
{sel} .lg svg {{ width:{size}px; height:{size}px; display:block; }}
"""
    html = (f'<div class="lg" title="{m[slug]["title"]}">'
            f'<svg viewBox="0 0 24 24" role="img" aria-label="{m[slug]["title"]}">'
            f'<path d="{m[slug]["d"]}" fill="{fill}"/></svg></div>')
    return css, html
```

- [ ] **Step 4: Verificar**

Run: `python3 -m pytest tests/test_logos.py -q`
Expected: `11 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/logos.py tests/test_logos.py
git commit -q -m "feat: mark() — logo entintado sobre pastilla crema"
```

---

### Task 7: Tokens de señal en la paleta

Los guiones piden alerta roja y CTA en verde/azul (spec D7, §3.5).

**Files:**
- Modify: `scripts/mockups.py` (dict `C`, líneas 25-32)
- Test: `tests/test_logos.py`

- [ ] **Step 1: Escribir el test que falla**

```python
import mockups


def test_los_tokens_de_senal_existen():
    for t in ("alert", "go", "cool"):
        assert t in mockups.C


def test_los_tokens_de_senal_pasan_AA_sobre_papel_y_con_crema_encima():
    """Sirven tanto de tinta de titular como de pastilla con texto crema."""
    for t in ("alert", "go", "cool"):
        c = mockups.C[t]
        assert logos.contrast(c, logos.PAPER) >= 4.5, (t, c)
        assert logos.contrast(logos.PAPER, c) >= 4.5, (t, c)


def test_senal_y_anotacion_son_colores_distintos():
    """§3.5 regla 2: la mano que anota y el sistema que avisa no se mezclan."""
    assert mockups.C["go"] != mockups.C["green"]
    assert mockups.C["alert"] != mockups.C["redwood"]
```

- [ ] **Step 2: Verificar que falla**

Run: `python3 -m pytest tests/test_logos.py -q -k senal`
Expected: 3 FAILED con `KeyError: 'alert'`

- [ ] **Step 3: Implementar**

En `scripts/mockups.py`, añadir al dict `C` tras la línea de `green`/`redwood`:

```python
    # — señal — solo CTA y alerta, nunca superficie ni texto corrido.
    # Los guiones de las piezas 2 y 3 piden alerta roja y CTA en verde/azul.
    # Dos reglas los sujetan: (1) la señal SUSTITUYE al naranja en ese frame,
    # no se suma —la escasez de §4 no se relaja—; (2) señal ≠ anotación: green
    # y redwood siguen viviendo solo en la capa manuscrita.
    "alert": "#A33B31", "go": "#286B47", "cool": "#2A5490",
```

- [ ] **Step 4: Verificar**

Run: `python3 -m pytest tests/ -q`
Expected: todo pasa

- [ ] **Step 5: Verificar que la pieza 1 no cambió**

Nadie usa los tokens todavía.

```bash
scripts/build-composition.py --project . --piece 1
diff /tmp/oro-index.html videos/1/public/index.html && echo "IDÉNTICO"
```

- [ ] **Step 6: Commit**

```bash
git add scripts/mockups.py tests/test_logos.py
git commit -q -m "feat: tokens de senal --alert --go --cool con contraste verificado"
```

---

### Task 8: `mockups.py` — el cursor

**Files:**
- Modify: `scripts/mockups.py`
- Test: `tests/test_mockups.py`

- [ ] **Step 1: Escribir el test que falla**

`tests/test_mockups.py`:

```python
import mockups


def test_el_cursor_empieza_fuera_de_cuadro():
    """/oversized-cursor: entra desde fuera, no aparece por arte de magia."""
    css, html = mockups.cursor("viz-01", canvas_h=1920)
    assert "cur" in html and "ring" in html
    assert "1920" in css or "2000" in css


def test_el_cursor_no_lleva_transform_de_colocacion():
    css, html = mockups.cursor("viz-01", canvas_h=1920)
    assert "translate(-50%" not in css


def test_el_cursor_va_en_tinta_con_filete_crema():
    """Tiene que sobrevivir sobre óleo oscuro, mockup crema y foto."""
    css, html = mockups.cursor("viz-01", canvas_h=1920)
    assert mockups.C["ink"] in css + html
    assert mockups.C["paper"] in css + html
```

- [ ] **Step 2: Verificar que falla**

Run: `python3 -m pytest tests/test_mockups.py -q`
Expected: FAIL — `AttributeError: module 'mockups' has no attribute 'cursor'`

- [ ] **Step 3: Implementar**

Añadir a `scripts/mockups.py`:

```python
# ── cursor sobredimensionado ──────────────────────────────────────────────────
def cursor(cid: str, canvas_h: int = 1920, size: int = 64) -> tuple[str, str]:
    """El cursor de la casa. Devuelve (css, html); los gestos van aparte.

    Entra desde FUERA de cuadro y sale al terminar. No hay cursor en reposo:
    §7 prohíbe el wobble ocioso y un cursor parado en pantalla es exactamente
    eso — un elemento que respira sin actuar.

    En tinta con filete crema de 2 px para sobrevivir sobre cualquier fondo:
    el visual de detrás cambia en cada pieza (óleo oscuro, mockup crema, foto).

    Toda posición se anima con x/y desde 0,0 (§9: left/top se cuantizan a píxel
    entero y tartamudean), así que aquí NO se coloca con transform.
    """
    sel = f'.viz[data-viz-id="{cid}"]'
    css = f"""
{sel} .cur {{ position:absolute; left:0; top:{canvas_h + 80}px;
  width:{size}px; height:{size}px; pointer-events:none; z-index:9; }}
{sel} .cur svg {{ width:100%; height:100%; display:block;
  filter:drop-shadow(0 2px 6px rgba(42,36,31,.22)); }}
{sel} .ring {{ position:absolute; left:{round(size * 0.16)}px;
  top:{round(size * 0.16)}px; width:{round(size * 0.9)}px;
  height:{round(size * 0.9)}px; border-radius:9999px;
  border:3px solid {C["terracotta"]}; opacity:0; pointer-events:none; }}
"""
    html = (f'<div class="cur" id="{cid}-cur">'
            f'<svg viewBox="0 0 24 24"><path d="M5 2.5 L5 19 L9.2 15.2 L11.8 21 '
            f'L14.6 19.7 L12 14 L18 13.8 Z" fill="{C["ink"]}" '
            f'stroke="{C["paper"]}" stroke-width="1.4" stroke-linejoin="round"/>'
            f'</svg><div class="ring" id="{cid}-cur-ring"></div></div>')
    return css, html
```

El id del anillo es `{cid}-cur-ring` porque el kind `click` construye su selector
como `{sel}-ring` a partir del selector del cursor (`#{cid}-cur`).

- [ ] **Step 4: Verificar**

Run: `python3 -m pytest tests/test_mockups.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/mockups.py tests/test_mockups.py
git commit -q -m "feat: cursor sobredimensionado que entra desde fuera de cuadro"
```

---

### Task 9: `whatsapp_chaos` con logo real, scroll y badge

**Files:**
- Modify: `scripts/mockups.py` (`whatsapp_chaos`, líneas 155-204)
- Test: `tests/test_mockups.py`

- [ ] **Step 1: Escribir el test que falla**

```python
FILAS = [("Ana", "hola, precios?", "lead"),
         ("Proveedor", "factura", "prov"),
         ("Luis", "sigue disponible?", "lead")]


def test_whatsapp_lleva_el_logo_real_en_la_cabecera():
    css, html, anims = mockups.whatsapp_chaos("viz-02", FILAS)
    assert 'viewBox="0 0 24 24"' in html


def test_los_gestos_producen_sus_anims():
    css, html, anims = mockups.whatsapp_chaos(
        "viz-02", FILAS, scroll_at=[(1.35, -120)], badge_at=[4.15])
    kinds = [a[0] for a in anims]
    assert "scroll" in kinds
    assert "badge-in" in kinds


def test_los_gestos_conservan_su_offset():
    _, _, anims = mockups.whatsapp_chaos(
        "viz-02", FILAS, scroll_at=[(1.35, -120)], badge_at=[4.15])
    scroll = [a for a in anims if a[0] == "scroll"][0]
    assert scroll[2] == 1.35 and scroll[4] == -120


def test_sin_gestos_el_mockup_sigue_funcionando():
    """Retrocompatible: la pieza 1 no declara gestos."""
    _, _, anims = mockups.whatsapp_chaos("viz-02", FILAS)
    assert [a for a in anims if a[0] == "scroll"] == []


def test_las_filas_entran_pegadas_a_su_contenedor():
    """§12: con las filas en 0.30 s se veía medio segundo de panel vacío."""
    _, _, anims = mockups.whatsapp_chaos("viz-02", FILAS)
    primera_fila = min(a[2] for a in anims if "-r" in a[1])
    assert primera_fila <= 0.20
```

- [ ] **Step 2: Verificar que falla**

Run: `python3 -m pytest tests/test_mockups.py -q -k whatsapp`
Expected: FAILED — `TypeError: whatsapp_chaos() got an unexpected keyword argument 'scroll_at'`

- [ ] **Step 3: Implementar**

Cambiar la firma y añadir el logo y los gestos:

```python
def whatsapp_chaos(cid: str, rows: list[tuple[str, str, str]],
                   logo: str = "whatsapp",
                   scroll_at: list | None = None,
                   badge_at: list | None = None,
                   click_at: list | None = None) -> tuple[str, str, list]:
```

`logo` es parámetro con valor por defecto —y no una constante— para que el plan
pueda apuntar a otra mensajería sin tocar el código.

Cambios dentro, en orden:

1. Importar arriba del módulo, junto a los demás: `import logos`.
2. Cabecera del teléfono — insertar el logo y concatenar su css:

```python
    lg_css, lg_html = logos.mark(cid, logo, 44)
    css += lg_css
    # ...y en el html de la cabecera, delante del título:
    #   f'<div class="hd">{lg_html}<span class="hd-t">Mensajes</span>'
    #   f'<div class="badge" id="{cid}-badge">12</div></div>'
```

3. El badge de notificación, en el css del mockup. Va en `--alert` sobre pastilla
   crema, no en alerta suelta: el fondo de detrás cambia según el visual.

```python
    css += f"""
{sel} .badge {{ margin-left:auto; min-width:52px; padding:6px 14px;
  background:{C["card"]}; color:{C["alert"]}; border-radius:9999px;
  border:1px solid rgba(42,36,31,.12); font:700 30px/1 Inter, sans-serif;
  text-align:center; opacity:0; }}
"""
```

4. Envolver las filas en un contenedor desplazable, que es lo que mueve `scroll`:

```python
    html += f'<div class="list" id="{cid}-list">{"".join(filas)}</div>'
    css += f'{sel} .list {{ position:relative; }}\n'
```

5. Añadir el cursor solo si hay clics — un cursor sin gesto sería wobble ocioso:

```python
    if click_at:
        cur_css, cur_html = cursor(cid)
        css += cur_css
        html += cur_html
```

6. Al final, antes del `return`, traducir los gestos a anims:

```python
    # Los gestos vienen ya en offsets relativos al visual (anims.gestures_to_offsets).
    # Sus tiempos salen del transcript, no de una progresión estética: §4.4 del
    # spec — un gesto de interfaz sin palabra detrás no existe.
    for off, dy in (scroll_at or []):
        anims.append(("scroll", f"#{cid}-list", off, 0.55, dy))
    for off in (badge_at or []):
        anims.append(("badge-in", f"#{cid}-badge", off, 0.34))
    for off, target in (click_at or []):
        anims.append(("cursor-to", f"#{cid}-cur", max(0.0, off - 0.42), 0.42,
                      *_punto(cid, target)))
        anims.append(("click", f"#{cid}-cur", off, 0.34))
```

7. Añadir el helper de geometría, que es del mockup porque **el mockup es dueño
   de dónde están sus filas**:

```python
def _punto(cid, target):
    """Coordenadas del objetivo de un clic dentro del mockup.

    Vive aquí y no en el plan porque la geometría es del mockup: el plan dice
    QUÉ se pulsa ("r2"), no dónde cae en píxeles.
    """
    if target.startswith("r"):
        i = int(target[1:])
        return (250, 470 + i * 132)
    raise ValueError(f"objetivo de clic desconocido: {target!r}")
```

- [ ] **Step 4: Verificar**

Run: `python3 -m pytest tests/test_mockups.py -q`
Expected: `8 passed`

- [ ] **Step 5: Verificar la regresión de la pieza 1**

La pieza 1 usa `whatsapp_chaos` sin gestos. El HTML **sí** va a cambiar (entra el
logo), así que aquí el `diff` deja de servir; lo que se comprueba es que valida.

```bash
scripts/build-composition.py --project . --piece 1
cd videos/1 && npx hyperframes check public 2>&1 | tail -20; cd ../..
```

Expected: `0 errores`. Refrescar la referencia de oro:
`cp videos/1/public/index.html /tmp/oro-index.html`

- [ ] **Step 6: Commit**

```bash
git add scripts/mockups.py tests/test_mockups.py
git commit -q -m "feat: whatsapp_chaos con logo real, scroll, badge y clic"
```

---

### Task 10: `crm_registry` con clic y `claude_code_terminal` con logo real

**Files:**
- Modify: `scripts/mockups.py` (`crm_registry` 208-272; `claude_code_terminal` 92-151)
- Test: `tests/test_mockups.py`

- [ ] **Step 1: Escribir el test que falla**

```python
CRM = [("Ana", "WhatsApp", "preguntó"),
       ("Luis", "Instagram", "agendó"),
       ("Sara", "WhatsApp", "desapareció")]


def test_crm_acepta_clic_ademas_del_sello():
    _, _, anims = mockups.crm_registry(
        "viz-03", CRM, stamp_at=[0.5, 1.5, 2.5], click_at=[(1.0, "r1")])
    kinds = [a[0] for a in anims]
    assert "stamp" in kinds and "click" in kinds and "cursor-to" in kinds


def test_el_cursor_llega_ANTES_de_hacer_clic():
    _, _, anims = mockups.crm_registry("viz-03", CRM, click_at=[(2.0, "r1")])
    viaje = [a for a in anims if a[0] == "cursor-to"][0]
    clic = [a for a in anims if a[0] == "click"][0]
    assert viaje[2] < clic[2]


def test_el_terminal_usa_el_logo_real_de_claude():
    _, html, _ = mockups.claude_code_terminal(
        "viz-04", "claude", [("brand", "Claude Code"), ("out", "listo")])
    assert 'viewBox="0 0 24 24"' in html
```

- [ ] **Step 2: Verificar que falla**

Run: `python3 -m pytest tests/test_mockups.py -q -k "crm or terminal"`
Expected: FAILED — `TypeError: crm_registry() got an unexpected keyword argument 'click_at'`

- [ ] **Step 3: Vendorizar el logo de Claude**

```bash
scripts/fetch-logos.py claude
```

Si el slug no existe, probar `anthropic`. Si tampoco, **parar y preguntar** — no
dibujar una marca a mano: el objetivo del encargo es logo real.

- [ ] **Step 4: Implementar**

`crm_registry`: añadir `click_at: list | None = None` a la firma y, al final:

```python
    for off, target in (click_at or []):
        anims.append(("cursor-to", f"#{cid}-cur", max(0.0, off - 0.42), 0.42,
                      *_punto_crm(cid, target)))
        anims.append(("click", f"#{cid}-cur", off, 0.34))
```

con su `_punto_crm` (las filas del CRM tienen otra geometría que las de WhatsApp)
y el cursor incluido en el html cuando `click_at` no es `None`.

`claude_code_terminal`: sustituir el glifo `✻` dibujado por
`logos.mark(cid, "claude", 34)`, concatenando su css.

- [ ] **Step 5: Verificar**

Run: `python3 -m pytest tests/ -q`
Expected: todo pasa

- [ ] **Step 6: Commit**

```bash
git add scripts/mockups.py assets/logos/ tests/test_mockups.py
git commit -q -m "feat: clic en el CRM y logo real de Claude en el terminal"
```

---

### Task 11: `app_switch` — el mockup que justifica los logos

**Files:**
- Modify: `scripts/mockups.py`
- Test: `tests/test_mockups.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_app_switch_pinta_un_logo_por_herramienta():
    css, html, anims = mockups.app_switch(
        "viz-05", ["whatsapp", "microsoftexcel"])
    assert html.count('viewBox="0 0 24 24"') == 2


def test_el_foco_salta_al_nombrarse_cada_herramienta():
    _, _, anims = mockups.app_switch(
        "viz-05", ["whatsapp", "microsoftexcel"],
        switch_at=[(0.10, "whatsapp"), (1.40, "microsoftexcel")])
    focos = [a for a in anims if a[0] == "cam-push"]
    assert len(focos) == 2
    assert focos[0][2] == 0.10 and focos[1][2] == 1.40


def test_solo_una_herramienta_en_color_de_marca_a_la_vez():
    """§3.5: un solo momento de alto voltaje por frame."""
    _, html, _ = mockups.app_switch("viz-05", ["whatsapp", "microsoftexcel"],
                                    brand="whatsapp")
    assert html.count("#269E51") == 1


def test_una_herramienta_sin_vendorizar_falla():
    import pytest
    with pytest.raises(KeyError):
        mockups.app_switch("viz-05", ["figma"])
```

- [ ] **Step 2: Verificar que falla**

Run: `python3 -m pytest tests/test_mockups.py -q -k app_switch`
Expected: 4 FAILED — `AttributeError: module 'mockups' has no attribute 'app_switch'`

- [ ] **Step 3: Implementar**

```python
# ── fila de herramientas ──────────────────────────────────────────────────────
def app_switch(cid: str, apps: list[str], switch_at: list | None = None,
               brand: str | None = None) -> tuple[str, str, list]:
    """La fila de herramientas que nombra el guion; el foco salta de una a otra.

    Es el mockup que justifica la capa de logos: sin logos reales es una fila de
    cajas grises. Uno solo va en color de marca (`brand`) y el resto en tinta —
    §3.5, un solo momento de alto voltaje por frame.
    """
    sel = f'.viz[data-viz-id="{cid}"]'
    css = f"""
{sel} .row {{ display:flex; gap:38px; align-items:center; justify-content:center; }}
{sel} .slot {{ opacity:.45; }}
"""
    marcas, htmls = [], []
    for i, slug in enumerate(apps):
        c, h = logos.mark(cid, slug, 96,
                          tone="brand" if slug == brand else "ink")
        marcas.append(c)
        htmls.append(f'<div class="slot" id="{cid}-a{i}">{h}</div>')
    css += "\n".join(dict.fromkeys(marcas))     # el css de mark() se repite
    html = f'<div class="row">{"".join(htmls)}</div>'

    anims = [("scale-pop", f"#{cid}-a{i}", 0.06 + i * 0.05, 0.40)
             for i in range(len(apps))]
    idx = {s: i for i, s in enumerate(apps)}
    for off, slug in (switch_at or []):
        if slug not in idx:
            raise ValueError(f"{slug} no está en la fila {apps}")
        # El foco es un empuje pegado al beat, no un latido continuo (§7).
        anims.append(("cam-push", f"#{cid}-a{idx[slug]}", off, 0.34, 1.06, 0))
    return css, html, anims
```

- [ ] **Step 4: Verificar**

Run: `python3 -m pytest tests/test_mockups.py -q`
Expected: todo pasa

- [ ] **Step 5: Commit**

```bash
git add scripts/mockups.py tests/test_mockups.py
git commit -q -m "feat: app_switch — fila de herramientas con el foco saltando"
```

---

### Task 12: `gen.py` — ledger con `provider` e `import`

**Files:**
- Create: `scripts/gen.py`
- Test: `tests/test_gen.py`

- [ ] **Step 1: Escribir el test que falla**

`tests/test_gen.py`:

```python
import json
import gen
import kie


def test_gen_reusa_la_cache_de_kie_no_la_reimplementa():
    """§10: dos copias de un script divergen. Ya pasó una vez en este proyecto."""
    assert gen.cache_key is kie.cache_key
    assert gen.ledger_put is kie.ledger_put


def test_una_entrada_sin_provider_se_lee_como_kie():
    """Las dos entradas que ya existen en el ledger no se migran."""
    assert gen.provider_of({"model": "veo3_fast"}) == "kie"
    assert gen.provider_of({"provider": "higgsfield"}) == "higgsfield"


def test_el_mapeo_de_modelos_cubre_las_tres_tecnicas():
    for t in ("hero-still", "hero-anim", "support"):
        assert "higgsfield" in gen.PROVIDER_MODELS[t]
        assert "kie" in gen.PROVIDER_MODELS[t]
```

- [ ] **Step 2: Verificar que falla**

Run: `python3 -m pytest tests/test_gen.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'gen'`

- [ ] **Step 3: Implementar el núcleo**

`scripts/gen.py`:

```python
#!/usr/bin/env python3
"""Capa de proveedor para los visuales generados.

    gen.py plan videos/2/plan.json [--json]
    gen.py import --url <url> --out assets/gen/hero.mp4 --provider higgsfield \\
           --model kling3_0_turbo --task <job_id> --prompt "..." \\
           --params '{...}' --credits 7.5
    gen.py fallback image|video --prompt "..." --out ... [--dry-run]
    gen.py credits

Higgsfield NO se llama desde aquí: solo existe como MCP, así que lo invoca el
agente. Este script hace lo que sí puede hacer un script — planificar, importar
y respaldar.

La caché y el ledger se IMPORTAN de kie.py, no se reimplementan: §10 del
CLAUDE.md ya pagó el precio de tener dos copias divergentes de un generador.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kie import (ROOT, cache_key, cached, credits, download,  # noqa: E402
                 ledger_load, ledger_put)

PROVIDER_MODELS = {
    "hero-still": {"higgsfield": ("nano_banana_pro", {"resolution": "1k"}),
                   "kie": ("google/nano-banana", {})},
    "hero-anim":  {"higgsfield": ("kling3_0_turbo", {"resolution": "720p"}),
                   "kie": ("veo3_fast", {"resolution": "720p"})},
    "support":    {"higgsfield": ("nano_banana_pro", {"resolution": "1k"}),
                   "kie": ("google/nano-banana", {})},
}


def provider_of(rec):
    """Las entradas viejas del ledger no tienen `provider`: son de Kie."""
    return rec.get("provider", "kie")


def do_import(url, out, provider, model, prompt, params, credits_spent, task):
    out = Path(out) if Path(out).is_absolute() else ROOT / out
    ck = cache_key(out, model, prompt, params)
    if cached(out, ck):
        print(f"⋯ caché  {out.relative_to(ROOT)}  (no se vuelve a bajar)")
        return out
    download(url, out)
    ledger_put(ck, dict(file=str(out.relative_to(ROOT)), provider=provider,
                        kind="video" if out.suffix == ".mp4" else "image",
                        model=model, prompt=prompt, params=params, taskId=task,
                        credits=float(credits_spent), source=url,
                        at=__import__("time").strftime("%Y-%m-%d %H:%M:%S")))
    print(f"✓ {out.relative_to(ROOT)}  ({out.stat().st_size // 1024} KB, "
          f"{credits_spent} cr, {provider})")
    return out
```

- [ ] **Step 4: Verificar**

Run: `python3 -m pytest tests/test_gen.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/gen.py tests/test_gen.py
git commit -q -m "feat: gen.py — ledger con provider e import idempotente"
```

---

### Task 13: `gen.py plan` — qué falta por generar

**Files:**
- Modify: `scripts/gen.py`
- Test: `tests/test_gen.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_plan_lista_solo_lo_que_falta(tmp_path):
    p = tmp_path / "plan.json"
    p.write_text(json.dumps({"format": "REEL", "scenes": [], "visuals": [
        {"id": "viz-01", "kind": "ai-video", "src": "gen/no-existe.mp4",
         "gen": {"provider": "auto", "tecnica": "hero-anim",
                 "prompt": "óleo", "dur": 5}},
        {"id": "viz-02", "kind": "mockup", "body": "whatsapp"}]}))
    faltan = gen.plan_missing(p)
    assert len(faltan) == 1
    assert faltan[0]["id"] == "viz-01"
    assert faltan[0]["higgsfield"]["model"] == "kling3_0_turbo"
    assert faltan[0]["kie"]["model"] == "veo3_fast"


def test_un_visual_sin_bloque_gen_no_se_genera(tmp_path):
    p = tmp_path / "plan.json"
    p.write_text(json.dumps({"visuals": [
        {"id": "viz-02", "kind": "mockup", "body": "whatsapp"}]}))
    assert gen.plan_missing(p) == []


def test_tecnica_desconocida_falla(tmp_path):
    p = tmp_path / "plan.json"
    p.write_text(json.dumps({"visuals": [
        {"id": "v", "kind": "ai-image", "src": "gen/x.png",
         "gen": {"tecnica": "inventada", "prompt": "x"}}]}))
    import pytest
    with pytest.raises(ValueError, match="técnica desconocida"):
        gen.plan_missing(p)
```

- [ ] **Step 2: Verificar que falla**

Run: `python3 -m pytest tests/test_gen.py -q -k plan`
Expected: FAILED — `AttributeError: module 'gen' has no attribute 'plan_missing'`

- [ ] **Step 3: Implementar**

```python
def plan_missing(plan_path):
    """Assets que el plan pide y no están todavía.

    NO consulta coste: el coste real de Higgsfield lo preflightea el agente con
    get_cost (que es gratis y no encola nada). Este script dice QUÉ falta; el
    agente decide CUÁNTO cuesta y con quién se paga.
    """
    plan = json.loads(Path(plan_path).read_text())
    faltan = []
    for v in plan.get("visuals", []):
        g = v.get("gen")
        if not g:
            continue
        tecnica = g.get("tecnica")
        if tecnica not in PROVIDER_MODELS:
            raise ValueError(
                f"{v['id']}: técnica desconocida {tecnica!r} "
                f"(usa {sorted(PROVIDER_MODELS)})")
        out = ROOT / "assets" / v["src"]
        hf_model, hf_params = PROVIDER_MODELS[tecnica]["higgsfield"]
        kie_model, kie_params = PROVIDER_MODELS[tecnica]["kie"]
        params = {**hf_params, **{k: g[k] for k in ("dur", "ratio") if k in g}}
        if cached(out, cache_key(out, hf_model, g["prompt"], params)):
            continue
        if out.exists() and out.stat().st_size > 0:
            continue
        faltan.append({"id": v["id"], "src": v["src"], "out": str(out),
                       "tecnica": tecnica, "prompt": g["prompt"],
                       "from": g.get("from"), "dur": g.get("dur"),
                       "provider": g.get("provider", "auto"),
                       "higgsfield": {"model": hf_model, "params": hf_params},
                       "kie": {"model": kie_model, "params": kie_params}})
    return faltan
```

- [ ] **Step 4: Verificar**

Run: `python3 -m pytest tests/test_gen.py -q`
Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/gen.py tests/test_gen.py
git commit -q -m "feat: gen.py plan — inventario de assets pendientes"
```

---

### Task 14: `gen.py fallback` — el respaldo, con `--dry-run`

**Files:**
- Modify: `scripts/gen.py`
- Test: `tests/test_gen.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_fallback_construye_la_llamada_a_kie_sin_lanzarla():
    cmd = gen.fallback_cmd("video", prompt="óleo", out="assets/gen/h.mp4",
                           tecnica="hero-anim", ratio="9:16", dur=8)
    assert cmd[1].endswith("kie.py")
    assert "video" in cmd
    assert "--model" in cmd and "veo3_fast" in cmd
    assert "--dur" in cmd and "8" in cmd


def test_el_fallback_de_imagen_usa_nano_banana():
    cmd = gen.fallback_cmd("image", prompt="recepción", out="assets/gen/c.png",
                           tecnica="support", ratio="9:16")
    assert "image" in cmd
    assert "--dur" not in cmd


def test_veo_solo_acepta_4_6_u_8_segundos():
    """kling acepta 3-15 y Veo no: una duración de 5 s tiene que subir a 6."""
    cmd = gen.fallback_cmd("video", prompt="x", out="assets/gen/h.mp4",
                           tecnica="hero-anim", ratio="9:16", dur=5)
    assert cmd[cmd.index("--dur") + 1] == "6"
```

- [ ] **Step 2: Verificar que falla**

Run: `python3 -m pytest tests/test_gen.py -q -k fallback`
Expected: FAILED — `AttributeError: module 'gen' has no attribute 'fallback_cmd'`

- [ ] **Step 3: Implementar**

```python
# Veo solo acepta 4, 6 u 8 s (kie.VIDEO_DURATIONS); kling acepta 3-15. Una
# duración válida en Higgsfield puede no serlo en Kie, y un parámetro inválido
# no falla en la llamada sino en la tarea, minutos después. Se ajusta aquí.
def _dur_kie(d):
    return min((4, 6, 8), key=lambda v: (abs(v - d), v < d))


def fallback_cmd(kind, prompt, out, tecnica, ratio="9:16", dur=None):
    """La llamada a kie.py equivalente. No la lanza: devolverla la hace testable."""
    model, _ = PROVIDER_MODELS[tecnica]["kie"]
    cmd = [sys.executable, str(Path(__file__).resolve().parent / "kie.py"),
           kind, "--prompt", prompt, "--out", out, "--ratio", ratio]
    if kind == "video":
        cmd += ["--model", model, "--dur", str(_dur_kie(int(dur or 8)))]
    return cmd
```

- [ ] **Step 4: Escribir el `main()` completo**

Es la única parte de `gen.py` que no cubren los tests (es E/S y argparse), así
que se escribe entera aquí y se prueba a mano en el paso 6.

```python
def main():
    ap = argparse.ArgumentParser(description="Capa de proveedor para visuales")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("credits", help="créditos de Kie (los de Higgsfield: balance() del MCP)")

    pp = sub.add_parser("plan", help="assets que el plan pide y no están")
    pp.add_argument("plan")
    pp.add_argument("--json", action="store_true")

    pi = sub.add_parser("import", help="registra un asset ya generado")
    pi.add_argument("--url", required=True)
    pi.add_argument("--out", required=True)
    pi.add_argument("--provider", required=True, choices=["higgsfield", "kie"])
    pi.add_argument("--model", required=True)
    pi.add_argument("--prompt", required=True)
    pi.add_argument("--params", default="{}")
    pi.add_argument("--credits", default="0")
    pi.add_argument("--task", default="")

    pf = sub.add_parser("fallback", help="delega en kie.py")
    pf.add_argument("kind", choices=["image", "video"])
    pf.add_argument("--prompt", required=True)
    pf.add_argument("--out", required=True)
    pf.add_argument("--tecnica", required=True, choices=sorted(PROVIDER_MODELS))
    pf.add_argument("--ratio", default="9:16")
    pf.add_argument("--dur", type=int, default=8)
    pf.add_argument("--dry-run", action="store_true", dest="dry_run")

    a = ap.parse_args()

    if a.cmd == "credits":
        print(f"{credits():g} créditos en Kie")
    elif a.cmd == "plan":
        faltan = plan_missing(a.plan)
        if a.json:
            print(json.dumps(faltan, indent=2, ensure_ascii=False))
        elif not faltan:
            print("nada que generar — todo está en el ledger")
        else:
            for f in faltan:
                print(f"· {f['id']:8} {f['tecnica']:11} → {f['src']}")
                print(f"    higgsfield: {f['higgsfield']['model']}"
                      f"   kie: {f['kie']['model']}")
                print(f"    {f['prompt'][:72]}…")
            print(f"\n{len(faltan)} pendientes. Preflightea cada uno con "
                  f"get_cost y compáralo con balance() antes de generar.")
    elif a.cmd == "import":
        do_import(a.url, a.out, a.provider, a.model, a.prompt,
                  json.loads(a.params), a.credits, a.task)
    elif a.cmd == "fallback":
        cmd = fallback_cmd(a.kind, a.prompt, a.out, a.tecnica, a.ratio, a.dur)
        if a.dry_run:
            print(" ".join(cmd))
            return
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Verificar**

Run: `python3 -m pytest tests/test_gen.py -q`
Expected: `9 passed`

- [ ] **Step 6: Probar el respaldo de verdad, sin gastar créditos**

```bash
chmod +x scripts/gen.py
scripts/gen.py fallback video --prompt "óleo de prueba" \
    --out assets/gen/prueba.mp4 --tecnica hero-anim --dur 5 --dry-run
scripts/gen.py plan videos/1/plan.json
```

Expected: la primera imprime una línea con
`kie.py video --prompt ... --model veo3_fast --dur 6`; la segunda,
`nada que generar — todo está en el ledger` (la pieza 1 ya tiene sus assets).

- [ ] **Step 7: Commit**

```bash
git add scripts/gen.py tests/test_gen.py
git commit -q -m "feat: gen.py fallback con --dry-run y ajuste de duración a Veo"
```

---

### Task 15: `build_visuals` — `gestures`, `logo` y `gen`

**Files:**
- Modify: `scripts/build-composition.py` (`build_visuals`, línea 538; dict de mockups línea 567)
- Test: `tests/test_anims.py`

- [ ] **Step 1: Escribir el test que falla**

Los gestos se traducen con `anims.gestures_to_offsets`, ya probado en Task 2.
Lo que falta probar es el registro del mockup nuevo:

```python
def test_app_switch_esta_registrado_en_el_generador():
    """Un mockup sin registrar da KeyError en mitad del render."""
    import importlib.util
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / "scripts" / "build-composition.py"
    fuente = p.read_text()
    assert '"app_switch": mockups.app_switch' in fuente
```

- [ ] **Step 2: Verificar que falla**

Run: `python3 -m pytest tests/test_anims.py -q -k app_switch`
Expected: FAILED

- [ ] **Step 3: Implementar en `build_visuals`**

En el dict de mockups (línea 567):

```python
            fn = {"whatsapp": mockups.whatsapp_chaos,
                  "crm": mockups.crm_registry,
                  "terminal": mockups.claude_code_terminal,
                  "hero": mockups.hero_title,
                  "app_switch": mockups.app_switch}[which]
```

Y antes de llamar a `fn`, traducir los gestos:

```python
        # Los gestos del plan vienen en tiempo ABSOLUTO de la línea del corte
        # —igual que `beats`— y el mockup los quiere relativos a su inicio.
        kw = {}
        if v.get("gestures"):
            kw = anims.gestures_to_offsets(v["gestures"], v["start"])
            kw = {k: val for k, val in kw.items() if val}   # solo lo declarado
        # Una LISTA de logos es la fila de app_switch; una cadena es el logo de
        # cabecera de un mockup concreto. Son parámetros distintos porque son
        # cosas distintas: una fila de herramientas y una marca que preside.
        if isinstance(v.get("logo"), list):
            kw["apps"] = v["logo"]
        elif v.get("logo"):
            kw["logo"] = v["logo"]
        # Cuál de la fila va en color de marca. §3.5: uno solo por frame, así
        # que es un campo escalar y no una lista — el esquema impide el error.
        if v.get("brand"):
            kw["brand"] = v["brand"]
```

pasando `**kw` a `fn`. Los mockups que no aceptan `logo` (`hero_title`) nunca lo
reciben, porque el plan solo lo declara donde hay una marca que pintar.

- [ ] **Step 4: Verificar**

Run: `python3 -m pytest tests/ -q`
Expected: todo pasa

- [ ] **Step 5: Verificar que la pieza 1 sigue validando**

```bash
scripts/build-composition.py --project . --piece 1
cd videos/1 && npx hyperframes check public 2>&1 | tail -20; cd ../..
```

Expected: `0 errores`

- [ ] **Step 6: Commit**

```bash
git add scripts/build-composition.py tests/test_anims.py
git commit -q -m "feat: build_visuals entiende gestures, logo y app_switch"
```

---

### Task 16: `new-piece.sh` y `detect-format.sh` — la disposición nueva

El metraje pasó de `VIDEOS ORIGINALES/2.MOV` a `VIDEOS ORIGINALES/2/video.MOV`
con un `guion.md` al lado.

**Files:**
- Modify: `scripts/new-piece.sh`
- Modify: `scripts/detect-format.sh`

- [ ] **Step 1: Leer los dos scripts**

```bash
cat scripts/new-piece.sh scripts/detect-format.sh
```

- [ ] **Step 2: Comprobar el comportamiento actual**

```bash
scripts/detect-format.sh "VIDEOS ORIGINALES/2/video.MOV"
```

Expected: `FORMAT`, `LABEL` y `CANVAS`. `detect-format.sh` recibe una ruta y no
le importa la disposición, así que probablemente ya funcione. Si funciona, **no
tocarlo** — YAGNI.

- [ ] **Step 3: Adaptar `new-piece.sh` para aceptar la carpeta**

Que acepte tanto `VIDEOS ORIGINALES/2` como `VIDEOS ORIGINALES/2/video.MOV`:

```bash
SRC="$1"
if [ -d "$SRC" ]; then
  N="$(basename "$SRC")"
  SRC="$SRC/video.MOV"
fi
[ -f "$SRC" ] || { echo "no existe: $SRC" >&2; exit 1; }
```

y que, si hay un `guion.md` al lado, lo mencione en los pasos que imprime:

```bash
GUION="$(dirname "$SRC")/guion.md"
[ -s "$GUION" ] && echo "  · guion del usuario: $GUION  (léelo antes del paso 8)"
```

- [ ] **Step 4: Probar en seco con la pieza 2**

```bash
scripts/new-piece.sh "VIDEOS ORIGINALES/2"
```

Expected: numera la pieza 2, detecta REEL, extrae el audio, crea
`videos/2/plan.json` y menciona `VIDEOS ORIGINALES/2/guion.md`.

- [ ] **Step 5: Commit**

```bash
git add scripts/new-piece.sh scripts/detect-format.sh
git commit -q -m "feat: aceptar la disposicion VIDEOS ORIGINALES/<n>/video.MOV"
```

---

### Task 17: Regresión completa de la pieza 1

**Files:** ninguno — es verificación.

- [ ] **Step 1: Regenerar**

```bash
scripts/build-composition.py --project . --piece 1
```

- [ ] **Step 2: Validar**

```bash
cd videos/1 && npx hyperframes check public 2>&1 | tail -30; cd ../..
```

Expected: **0 errores** y **65/65 WCAG AA**. Avisos permitidos:
`composition_file_too_large` y `timeline_track_too_dense`.

- [ ] **Step 3: Comprobar que no se regeneró ningún asset**

```bash
git diff --stat assets/gen/ledger.json
```

Expected: sin cambios — la caché sigue sirviendo.

- [ ] **Step 4: Snapshots de los momentos que cambiaron**

`whatsapp_chaos` y el terminal ahora llevan logo real.

```bash
cd videos/1 && npx hyperframes snapshot public --at 19.5,27.5,34.0; cd ../..
```

Revisar los PNG: el logo tiene que verse entintado sobre pastilla crema, sin
romper el layout de la bandeja.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -q -m "test: regresion de la pieza 1 tras la capa de logos"
```

---

### Task 18: Documentación

**Files:**
- Modify: `CLAUDE.md` (§4, §12, §16)
- Modify: `.claude/skills/editorial-retro-digital/SKILL.md` (§1, §2, §7)
- Modify: `.claude/skills/editorial-retro-digital/references/visuals.md`
- Modify: `.claude/skills/editorial-retro-digital/references/design.md`
- Create: `.claude/skills/editorial-retro-digital/references/logos.md`
- Modify: `.claude/skills/editorial-retro-digital/references/gotchas.md`

- [ ] **Step 1: `CLAUDE.md` §12 — reescribir la cabecera de proveedores**

Sustituir la tabla de Kie por:

```markdown
### Higgsfield primero, Kie de respaldo

Higgsfield es el generador primario y solo existe como **MCP**: lo invoca el
agente, no un script. `scripts/gen.py` hace lo que sí puede hacer un script —
planificar, importar y respaldar.

| | Kie (respaldo) | Higgsfield (primario) |
| --- | --- | --- |
| Imagen | 4 cr (`google/nano-banana`) | **2 cr** (`nano_banana_pro` 1k) |
| Video | 60 cr (`veo3_fast` 8 s) | **7.5 cr** (`kling3_0_turbo` 5 s 720p) |

**El hero se hace en dos pasos**: se genera el óleo fijo (2 cr) y se anima con
ese still en `start_image` (7.5 cr) = **9.5 cr**. No es solo 6× más barato: se
dirige el arte iterando a 2 créditos en vez de tirar 60 a ciegas.

Regla de ruteo, por asset y en orden del plan: se preflightea con `get_cost`
(gratis), y si el saldo no cubre esa generación, cae a Kie. Si el MCP no
responde, todo cae a Kie.
```

- [ ] **Step 2: `CLAUDE.md` §4 — los tokens de señal**

Añadir tras el bloque de anotación manuscrita:

```markdown
/* — señal — solo CTA y alerta — */
--alert:  #A33B31   /* alerta · tensión     5.43:1 sobre papel */
--go:     #286B47   /* CTA afirmativo       5.33:1 sobre papel */
--cool:   #2A5490   /* CTA secundario       6.32:1 sobre papel */
```

Con las dos reglas: la señal **sustituye** al naranja en ese frame (la escasez no
se relaja) y **señal ≠ anotación** (`--green` y `--redwood` siguen siendo solo de
la capa manuscrita).

- [ ] **Step 3: `CLAUDE.md` — sección nueva de logos**

Fuente (Simple Icons, CC0, vendorizado), entintado calculado, la regla de un solo
logo en color por frame, y la trampa de Notion: una marca más oscura que `--ink`
devuelve `--ink`, porque mezclarla daría negro puro.

- [ ] **Step 4: `CLAUDE.md` §16 — reglas duras nuevas**

En **Hacer**: «Un gesto de interfaz se declara con su tiempo absoluto del corte:
un clic sin palabra detrás no existe.»
En **No hacer**: «Dibujar a mano una marca que existe — se vendoriza de Simple
Icons» y «Poner dos colores de señal, o señal + naranja, en el mismo frame».

- [ ] **Step 5: `SKILL.md` §2 — el paso 7**

```markdown
| 7 | Generar visuales | `scripts/gen.py plan videos/<n>/plan.json` → generar con
las tools de Higgsfield → `scripts/gen.py import ...` |
```

Y en §1, marcar `KIE_API_KEY` como **opcional (respaldo)**.

- [ ] **Step 6: `references/logos.md` (nuevo)**

Slugs vendorizados, `fetch-logos.py`, `mark()`, `brand_tone()` con la tabla de
valores reales (whatsapp `#25D366` → `#269E51`, 3.27:1) y la guarda de negro.

- [ ] **Step 7: `references/visuals.md` — reescribir**

Higgsfield primario con sus dos rutas, la ruta de dos pasos del hero, y `gen.py`.
Conservar la sección de la trampa cara de Kie: sigue vigente cuando se usa el
respaldo.

- [ ] **Step 8: `references/gotchas.md` — las trampas nuevas**

- Una marca negra (Notion `#000000`) no se puede entintar hacia `--ink`: daría
  negro puro. Se devuelve `--ink`.
- El anillo del clic se llama `{cid}-cur-ring` porque el kind `click` lo deriva
  del selector del cursor.
- Veo acepta 4/6/8 s y kling 3-15: al caer al respaldo hay que ajustar la
  duración o la tarea falla minutos después, no en la llamada.

- [ ] **Step 9: Commit**

```bash
git add CLAUDE.md .claude/skills/editorial-retro-digital/
git commit -q -m "docs: Higgsfield primario, capa de logos y gestos de interfaz"
```

---

### Task 19: Pieza 2 de punta a punta

La prueba real. `VIDEOS ORIGINALES/2/video.MOV` — «Ventas, inventario y reportes
desconectados», CTA `ERP`.

**Files:**
- Create: `transcripts/2.json`, `cuts/2.json`, `videos/2/plan.json`, `videos/2/output.mp4`

- [ ] **Step 1: Formato, audio, transcripción**

```bash
scripts/detect-format.sh "VIDEOS ORIGINALES/2/video.MOV"
ffmpeg -i "VIDEOS ORIGINALES/2/video.MOV" -vn -ac 1 -ar 16000 -c:a flac assets/audio/2.flac
scripts/transcribe.py assets/audio/2.flac transcripts/2.json
```

- [ ] **Step 2: Cruzar con la energía real del audio**

```bash
ffmpeg -i "VIDEOS ORIGINALES/2/video.MOV" -af silencedetect=n=-30dB:d=0.3 -f null - 2>&1 | grep silence
```

Recordar: `silencedetect` loguea a nivel **info**; con `-v error` no imprime nada.

- [ ] **Step 3: Cortar y verificar**

```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "VIDEOS ORIGINALES/2/video.MOV")
scripts/plan-cuts.py transcripts/2.json cuts/2.json "$DUR"
scripts/rough-cut.sh "VIDEOS ORIGINALES/2/video.MOV" cuts/2.json out/2-rough.mp4
```

Re-transcribir el corte y comparar el número de palabras contra `transcripts/2.json`.

- [ ] **Step 4: Cara y color**

```bash
scripts/measure-face.py out/2-rough.mp4 assets/face-2.json
scripts/calibrate-hlg.py out/2-rough.mp4 5.5
scripts/make-hlg-lut.py assets/hlg-to-709.cube
mkdir -p videos/2/public
ffmpeg -i out/2-rough.mp4 \
  -vf "lut3d=assets/hlg-to-709.cube,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv" \
  -c:v libx264 -crf 18 -g 30 -keyint_min 30 -pix_fmt yuv420p \
  -movflags +faststart -c:a aac videos/2/public/input-video.mp4
```

- [ ] **Step 5: Escribir `videos/2/plan.json`** — el trabajo creativo

Leer `VIDEOS ORIGINALES/2/guion.md`, incluida su sección «Visuales y edición».
Traducir cada indicación a una escena o un visual, con **todos los tiempos
remapeados del transcript**:

| Lo que pide el guion | Cómo se resuelve |
| --- | --- |
| «tres ventanas: Excel, WhatsApp y un sistema de ventas» | `app_switch` con `microsoftexcel` + `whatsapp` + el ERP, `switch_at` en las palabras |
| «VENTAS / INVENTARIO / REPORTES» | tarjeta con `beats` en las tres palabras |
| «vibración o alerta roja» en «tres problemas» | `--alert`; ese frame **sin naranja** |
| «grabación del dashboard del ERP» | visual con la grabación del usuario (**dependencia externa**: hace falta el archivo) |
| «líneas conectando POS, inventario y reportes» | mockup con `draw` |
| «COMENTA: ERP a pantalla completa 2 s» | tarjeta CTA con un color de señal |

- [ ] **Step 6: Generar los visuales**

```bash
scripts/gen.py plan videos/2/plan.json
```

Para cada asset que falte: preflight con `get_cost`, comparar contra `balance()`,
generar con Higgsfield e importar con `gen.py import`. Si el saldo no cubre uno,
`gen.py fallback`.

- [ ] **Step 7: Componer y validar**

```bash
scripts/build-composition.py --project . --piece 2
cd videos/2 && npx hyperframes check public 2>&1 | tail -30; cd ../..
```

Expected: **0 errores**. No renderizar con errores abiertos.

- [ ] **Step 8: Snapshots antes de renderizar**

```bash
cd videos/2 && npx hyperframes snapshot public --at 2.0,8.5,16.0,24.0,38.0; cd ../..
```

Lista **separada por comas**: repetir `--at` no acumula, se queda con el último.

- [ ] **Step 9: Renderizar**

```bash
cd videos/2 && npx hyperframes render public --skill=talking-head-recut \
    -o output.mp4 --fps 30 --sdr
```

Esperar al **proceso**, no a la fecha del archivo:

```bash
while pgrep -f "hyperframes render" >/dev/null; do sleep 15; done
```

- [ ] **Step 10: Verificar sobre el MP4**

Extraer frames del MP4 —nunca del navegador— y comprobar los criterios del spec:

1. Un asset generado con Higgsfield, con su entrada de ledger (`provider`,
   `taskId`, créditos).
2. Un logo en tinta y uno en `brand`.
3. Un mockup con gestos cuyos tiempos salgan del transcript.
4. El CTA en color de señal, y ese frame **sin naranja**.

```bash
ffmpeg -v error -i videos/2/output.mp4 -vf "select='eq(n\,60)+eq(n\,480)+eq(n\,1140)'" \
   -vsync 0 /tmp/p2-%02d.png && ls /tmp/p2-*.png
```

- [ ] **Step 11: Commit**

```bash
git add -A
git commit -q -m "feat: pieza 2 montada con Higgsfield, logos y mockups usados"
```

- [ ] **Step 12: Actualizar `CLAUDE.md` §14**

Añadir la pieza 2 al estado del proyecto: duración, cortes, visuales con su
técnica y proveedor, créditos gastados, y el resultado de la validación.

```bash
git add CLAUDE.md && git commit -q -m "docs: estado de la pieza 2"
```

---

## Dependencias externas

| Qué | Bloquea | Estado |
| --- | --- | --- |
| Grabación del dashboard del ERP | Task 19 Step 5 | **Pendiente** — el usuario confirmó que la tiene; falta la ruta del archivo |
| Slug de Claude en Simple Icons | Task 10 Step 3 | Verificar `claude`, si no `anthropic` |
| Créditos de Higgsfield (219.94) | Task 19 Step 6 | Suficientes: ~25 cr por pieza |
