# Higgsfield, logos de marca y mockups que se usan

**Fecha:** 2026-08-09
**Proyecto:** editor-videos · skill `editorial-retro-digital`
**Estado:** diseño aprobado, pendiente de plan de implementación

---

## Objetivo

Tres cambios en la **capa de visuales** de la skill:

1. **Higgsfield sustituye a Kie** como generador primario de imagen y video. Kie
   queda como respaldo automático cuando se acaben los créditos de Higgsfield o
   el MCP no responda.
2. **Los logos de marcas reales se buscan y se añaden** — WhatsApp, Notion, Gmail,
   Claude, lo que nombre el guion — dentro de la paleta crema/tinta.
3. **Los mockups se usan, no se muestran**: cursor que apunta y hace clic, listas
   que scrollean, estados que cambian, contadores que cuentan; todo clavado a la
   palabra del transcript.

No se toca nada de lo que ya funciona: metraje, LUT, plan de cortes, subtítulos,
sonido y el pipeline de render se quedan como están.

---

## Contexto medido

Verificado en esta sesión, no asumido:

| Dato | Valor |
| --- | --- |
| Higgsfield MCP | responde · **219.94 créditos** · plan `starter` |
| Higgsfield `unlim` | **no disponible** en este plan (`unlim.available: false`) |
| Coste imagen Higgsfield | **2 cr** (`nano_banana_pro`, 1k) — preflight `get_cost` |
| Coste video Higgsfield | **7.5 cr** (`kling3_0_turbo`, 5 s, 720p, 9:16) |
| Coste imagen Kie | 4 cr (`google/nano-banana`) |
| Coste video Kie | 60 cr (`veo3_fast`, 8 s, 720p) |
| Simple Icons | 3.400+ marcas · **CC0-1.0** sobre los SVG · hex oficial incluido |
| `build-composition.py` | 1264 líneas · `mockups.py` 325 |
| Metraje pendiente | `VIDEOS ORIGINALES/<n>/video.MOV` + `guion.md` (n = 2, 3, 4) |

**El metraje cambió de disposición** durante esta sesión: de `VIDEOS ORIGINALES/2.MOV`
a `VIDEOS ORIGINALES/2/video.MOV`, con un `guion.md` al lado que trae el guion
hablado **y una sección «Visuales y edición»** escrita por el usuario.
`new-piece.sh` y `detect-format.sh` tienen que aceptar la disposición nueva.

**La asimetría que decide la arquitectura:** Kie es una API con clave y un script
la llama sola desde el shell. Higgsfield **solo existe como MCP**, así que ningún
script puede invocarlo — solo el agente. El paso 7 del pipeline pasa a ser
agente + script de registro.

---

## Decisiones tomadas

| # | Decisión | Por qué |
| --- | --- | --- |
| D1 | Paso 7 = agente genera por MCP + `gen.py import` registra | Sin claves nuevas, un solo ledger, caché preservada |
| D2 | Fuente de logos: **Simple Icons vendorizado** | CC0, un trazo, hex oficial, se entinta; nunca IA |
| D3 | Logos en **tinta por defecto, color de marca escaso** | Misma regla de escasez que el naranja (§4) |
| D4 | Mockups con **vocabulario de gestos de interfaz** | §0: la pieza demuestra capacidad de edición |
| D5 | **Extender en sitio**, extrayendo solo `anims.py` | La pieza 1 valida hoy con 0 errores; no arriesgarla |
| D6 | Hero en **dos pasos** (still + animación) | 9.5 cr vs 60, y se dirige el arte cuando cuesta 2 |
| D7 | **Mandan los guiones** sobre el §4: entran `--alert`, `--go`, `--cool` | Decisión del usuario tras plantearle el choque. Se acotan con dos reglas duras (§3.5) |
| D8 | El dashboard del ERP es **grabación real**, no mockup | Es producto propio del usuario, no una captura de terceros — la razón del §12 (no encaja en la paleta, envejece) no aplica igual |

---

## 1 · Alcance

```
scripts/
  gen.py          ← NUEVO    proveedor + ledger unificado + import + plan
  kie.py                     INTACTO — pasa a ser el respaldo
  logos.py        ← NUEVO    slug de marca → SVG entintado
  fetch-logos.py  ← NUEVO    vendoriza de Simple Icons
  anims.py        ← EXTRAÍDO de build-composition.py
  mockups.py                 crece: gestos + logos + app_switch
  build-composition.py       1264 → ~1100 líneas
assets/
  logos/          ← NUEVO    *.svg vendorizados + meta.json
```

**Fuera de alcance:** trocear `build-composition.py` en `compose/`; tocar el
pipeline de color, cortes, subtítulos o sonido; montar las piezas 3 y 4.

---

## 2 · `gen.py` — la capa de proveedores

`gen.py` no llama a Higgsfield. Hace las tres cosas que sí puede hacer un script:
**planificar, importar y respaldar.**

### 2.1 · CLI

```bash
gen.py plan videos/2/plan.json [--json]
# Lista los assets que el plan pide y no están en el ledger, con id, kind,
# modelo por proveedor, prompt y parámetros. NO consulta coste: el coste real
# de Higgsfield lo preflightea el agente con get_cost (gratis).

gen.py import --url <url> --out assets/gen/hero.mp4 \
      --provider higgsfield --model kling3_0_turbo --task <job_id> \
      --prompt "..." --params '{"aspect_ratio":"9:16","duration":5}' \
      --credits 7.5
# Descarga, guarda y anota en el ledger. Idempotente.

gen.py fallback image|video --prompt "..." --out ... [--ratio ...] [--dur ...] [--dry-run]
# Delega en kie.py con el modelo equivalente de la tabla de mapeo.
# --dry-run imprime la llamada que haría y no la lanza: permite probar el
# respaldo sin gastar créditos.

gen.py credits
# Saldo de Kie (el de Higgsfield lo consulta el agente con balance()).
```

### 2.2 · Ledger compartido

`assets/gen/ledger.json` no cambia de forma; gana **un campo**:

```jsonc
{
  "<cache_key>": {
    "file": "assets/gen/hero.mp4",
    "provider": "higgsfield",        // ← NUEVO. Ausente se lee como "kie".
    "kind": "video",
    "model": "kling3_0_turbo",
    "prompt": "...",
    "params": {...},
    "taskId": "<job_id>",
    "credits": 7.5,
    "source": "https://...",
    "at": "2026-08-09 10:12:00"
  }
}
```

**No se migra nada.** Las dos entradas existentes se leen como `kie` por ausencia
del campo.

### 2.3 · Caché — una sola fuente de verdad

`gen.py` **importa** de `kie.py` (`cache_key`, `ledger_load`, `ledger_put`,
`cached`, `download`, `ROOT`). No los reimplementa. §10 del CLAUDE.md ya pagó el
precio de tener copias divergentes de un script; esa lección aplica igual dentro
del mismo directorio.

Consecuencia: `gen.py import` calcula la misma clave que `kie.py` —
`sha256([ruta, modelo, prompt, params])[:16]`— así que un asset ya generado no se
vuelve a bajar ni a pagar al re-correr el pipeline.

### 2.4 · Mapeo de modelos

**El plan declara la técnica, no el modelo.** `hero-anim` sobrevive a que Kie
cambie de versión de Veo o a que Higgsfield jubile `kling3_0_turbo`; un
`"model": "kling3_0_turbo"` escrito en el plan, no. Un solo diccionario en
`gen.py` traduce técnica → modelo por proveedor:

```python
PROVIDER_MODELS = {
  "hero-still": {"higgsfield": ("nano_banana_pro",  {"resolution": "1k"}),
                 "kie":        ("google/nano-banana", {})},
  "hero-anim":  {"higgsfield": ("kling3_0_turbo",   {"resolution": "720p"}),
                 "kie":        ("veo3_fast",        {"resolution": "720p"})},
  "support":    {"higgsfield": ("nano_banana_pro",  {"resolution": "1k"}),
                 "kie":        ("google/nano-banana", {})},
}
```

### 2.5 · La regla de ruteo

Mecánica, por asset, en el orden del plan. Nada a ojo:

```
saldo ← balance()                       # MCP; si falla → todo a Kie
para cada asset que falta, en orden del plan:
    coste ← get_cost(modelo, params)    # preflight MCP, gratis
    si saldo ≥ coste:
        generar en Higgsfield · saldo ← saldo − coste
        gen.py import --provider higgsfield ...
    si no:
        gen.py fallback ...             # Kie
```

Sin margen de reserva ni umbrales mágicos: se compara el coste real de esa
generación contra el saldo real.

### 2.6 · El hero en dos pasos

El cambio de calidad, no solo de precio:

| | Kie (hoy) | Higgsfield (propuesto) |
| --- | --- | --- |
| Hero animado | `veo3_fast` 8 s → **60 cr por tirada** | `nano_banana_pro` óleo fijo (**2 cr**) → `kling3_0_turbo` con ese still en `start_image` (**7.5 cr**) = **9.5 cr** |
| Apoyo | `nano-banana` → 4 cr | `nano_banana_pro` 1k → **2 cr** |

Se dirige el óleo iterando a 2 créditos y solo se anima el que convence. Si la
animación no sirve, se re-tira solo el paso 2 (7.5 cr) conservando el still.

El still se pasa a `generate_video` como `medias: [{role: "start_image", value: <job_id>}]`
— el `job_id` de la imagen sirve directamente, sin subir el archivo.

**Los prompts no cambian de doctrina:** siguen pidiendo `no text, no letters, no
words, no numbers` y nombrando la paleta del proyecto.

---

## 3 · La capa de logos

### 3.1 · `fetch-logos.py`

```bash
scripts/fetch-logos.py whatsapp microsoftexcel
```

Los slugs que piden los guiones de las piezas 2 y 3: **`whatsapp`** y
**`microsoftexcel`**. El ERP y la tasa BCV **no llevan logo** — el ERP es producto
propio y va como mockup, y el BCV no está en Simple Icons.

Gemelo de `fetch-fonts.py`. Por cada slug:

1. Baja `https://cdn.jsdelivr.net/npm/simple-icons@v16/icons/<slug>.svg`.
2. **Verifica el contrato de Simple Icons**: `viewBox="0 0 24 24"` y exactamente
   un `<path>`. Si no cumple, falla ruidosamente — un SVG con estructura distinta
   rompería el entintado silenciosamente.
3. Guarda `assets/logos/<slug>.svg` y anota en `assets/logos/meta.json` el
   `title` y el `hex` oficial de la marca.

Si un slug no existe en Simple Icons, el script lo dice y no inventa nada.

**Vendorizado**, por lo mismo que las fuentes y los SFX: la CDN puede caerse y el
proyecto tiene que seguir renderizando igual.

### 3.2 · `logos.py`

```python
mark(slug, size, tone="ink") -> (css, html)
```

Devuelve un `<svg viewBox="0 0 24 24">` inline con el `<path>` de Simple Icons,
sobre pastilla `--card` con hairline y radio `sm`. CSS prefijado por el id del
contenedor, igual que los mockups.

- **`tone="ink"`** (por defecto) → `fill: #2A241F`.
- **`tone="brand"`** (el logo protagonista del frame) → color calculado:

```python
INK, CARD = "#2A241F", "#F9F9F7"

def brand_tone(hex_marca, ratio_min=3.0):
    """Mezcla el color de marca HACIA LA TINTA hasta que contrasta sobre crema.

    Mezclarlo hacia el crema —el instinto— lo ACLARA y lo vuelve ilegible sobre
    papel crema. Hacia la tinta desatura y oscurece a la vez, que es lo que hace
    una imprenta al bajar un color de marca a papel crudo.
    """
    for mix in (0.30, 0.40, 0.50, 0.60, 0.70):
        c = lerp(hex_marca, INK, mix)
        if contrast(c, CARD) >= ratio_min:
            return c
    return INK
```

Se devuelve la **primera** proporción que pasa: la menos entintada que es legible.
Calculado, no escrito a mano — misma doctrina que la ganancia de los SFX (§13),
la barbilla (§6) y el LUT (§8).

`ratio_min = 3.0` porque un logo es un objeto gráfico no textual; el mínimo de
texto (4.5:1) no aplica.

### 3.3 · Reglas de estilo

- **Un solo logo en `brand` por frame.** Es la regla de escasez del naranja
  extendida al color de marca. El resto va en tinta.
- Los logos **no se deforman ni se recomponen**: se usa el trazo oficial de
  Simple Icons tal cual, solo se cambia el `fill`.
- Uso editorial-nominativo: se nombra la herramienta que nombra el guion. Los
  archivos SVG son CC0; las marcas siguen siendo de sus dueños.
- Un `<svg>` inline **no es media**, así que no necesita `id` (la trampa de §13
  aplica a `<audio>` y `<video>`, no a esto). Pero sí le aplica §9: nada de
  `transform` de colocación si GSAP lo va a animar.

---

## 3.5 · Colores de señal — ampliación del sistema

Los guiones piden alerta roja y un CTA en verde y azul. Manda el guion (D7), así
que el sistema se amplía con **tres tokens de señal**, elegidos calculando el
contraste, no a ojo:

```
/* — señal — solo CTA y alerta, nunca superficie ni texto corrido — */
--alert:  #A33B31   /* alerta · tensión        5.43:1 sobre papel */
--go:     #286B47   /* CTA afirmativo          5.33:1 sobre papel */
--cool:   #2A5490   /* CTA secundario          6.32:1 sobre papel */
```

Los tres pasan **AA como texto sobre papel** y **AA con crema encima**, así que
sirven tanto para tinta de titular como para pastilla con texto crema:

| token | vs `--paper` | vs `--card` | crema encima |
| --- | --- | --- | --- |
| `--alert` `#A33B31` | 5.43 | 6.17 | 5.43 |
| `--go` `#286B47` | 5.33 | 6.07 | 5.33 |
| `--cool` `#2A5490` | 6.32 | 7.19 | 6.32 |

### Las dos reglas que impiden que esto rompa el sistema

1. **La señal SUSTITUYE al naranja en ese frame, no se suma.** La regla de
   escasez de §4 no se relaja: sigue habiendo **un solo momento de alto voltaje
   por frame**. Si el CTA va en `--go`, ese frame no lleva naranja.
2. **Señal ≠ anotación.** `--green #678E6D` y `--redwood #9B5446` siguen viviendo
   solo en la capa manuscrita. `--go` y `--alert` son otra cosa y no se mezclan
   con ellos: uno es la mano que anota, el otro es el sistema que avisa.

`--cool` es la concesión que más se desvía de la doctrina («ni grises fríos»).
Se elige el azul más oscuro que aún se lee como azul, para que caiga del lado
del navy impreso y no del azul de pantalla.

---

## 4 · Mockups que se usan

### 4.1 · `anims.py` — la extracción

El despacho por `kind` de `build-composition.py` (~líneas 1075-1180) sale a
`scripts/anims.py`:

```python
def emit(kind, sel, t, d, *extra) -> list[str]   # líneas de JS/GSAP
```

`build-composition.py` lo importa. `mockups.py` no lo necesita: sigue emitiendo
solo tuplas. Se extrae porque es la parte que más crece con este cambio y la
comparten tarjetas y mockups.

### 4.2 · Kinds nuevos

| kind | Firma | Qué hace |
| --- | --- | --- |
| `cursor-to` | `(sel, t, d, x, y)` | el cursor viaja a un punto · `power2.inOut` |
| `click` | `(sel, t, d)` | el cursor se hunde 0.06 s y un anillo se abre y se apaga |
| `scroll` | `(sel, t, d, dy)` | la lista se desplaza · `power2.inOut` |
| `row-state` | `(sel_viejo, t, d, sel_nuevo)` | el chip viejo sale, el nuevo se sella |
| `count-to` | `(sel, t, d, v, sufijo)` | contador genérico (el `count` de hoy está cableado a `%`) |
| `draw` | `(sel, t, d)` | una barra o línea se dibuja por `stroke-dashoffset` |
| `badge-in` | `(sel, t, d)` | el badge se sella y el logo pulsa **una vez** |

Todos con desplazamiento y escala pequeños y la opacidad haciendo el trabajo
(§7). Ningún `back.out`.

### 4.3 · El cursor

- **Entra desde fuera de cuadro** y sale al terminar. No hay cursor en reposo:
  §7 prohíbe el wobble ocioso y un cursor parado es exactamente eso.
- Sobredimensionado, ~64 px en 9:16, en tinta con filete crema de 2 px para
  sobrevivir sobre cualquier fondo (óleo oscuro, mockup crema, foto).
- Un elemento por mockup que declare gestos: `#{cid}-cur`, más `#{cid}-ring`
  para el tap.
- **Toda posición va por `x`/`y`**, nunca `left`/`top` — §9: se cuantizan a píxel
  entero y tartamudean.

### 4.4 · La regla dura

> **Un gesto de interfaz sin palabra detrás no existe.** Todo clic, scroll,
> cambio de estado y contador se declara con su **tiempo absoluto de la línea del
> corte**, sacado del transcript remapeado.

Es el error de §12 —«no basta con clavar la ENTRADA del visual»— extendido al
cursor. Nada de escalonados decorativos para contenido con palabra propia.

### 4.5 · Mockups tocados

| Mockup | Cambio |
| --- | --- |
| `whatsapp_chaos` | logo real en la cabecera · `scroll_at` · `badge_at` |
| `crm_registry` | `click_at` además del `stamp_at` que ya tiene |
| `claude_code_terminal` | la ✻ dibujada pasa a ser el logo real de Claude |
| `app_switch` | **NUEVO** — fila de logos de las herramientas que nombra el guion; el foco salta de una a otra al mencionarse (`switch_at`) |

`app_switch` es el mockup que justifica la capa de logos: sin logos reales es una
fila de cajas grises.

Los mockups reciben **parámetros con nombre** (`click_at`, `scroll_at`,
`badge_at`), como el `stamp_at` que ya existe — no un blob de `gestures`. El
mockup es dueño de su geometría: `click_at = [(t, "r2")]` y él sabe dónde está
`r2`.

---

## 5 · El esquema del plan

Dos campos nuevos en `videos/<n>/plan.json`, ambos siguiendo convenciones que ya
existen:

```jsonc
{
  "visuals": [
    {"id": "viz-02", "kind": "mockup", "body": "whatsapp",
     "logo": "whatsapp",                    // slug de Simple Icons
     "gestures": [                          // tiempos ABSOLUTOS de la línea del corte
       {"do": "scroll", "at": 19.80, "dy": -120},
       {"do": "click",  "at": 21.35, "target": "r2"},
       {"do": "badge",  "at": 22.60}]},

    {"id": "viz-03", "kind": "mockup", "body": "app_switch",
     "logo": ["whatsapp", "notion", "gmail"],   // lista → la fila de app_switch
     "brand": "whatsapp",                       // escalar: uno solo en color (§3.5)
     "gestures": [                              // el foco salta al nombrarse cada una
       {"do": "switch", "at": 27.10, "target": "whatsapp"},
       {"do": "switch", "at": 28.40, "target": "notion"},
       {"do": "switch", "at": 29.75, "target": "gmail"}]},

    {"id": "viz-01", "kind": "ai-video", "src": "gen/hero.mp4",
     "gen": {"provider": "auto",            // auto = §2.5 · o "higgsfield" / "kie"
             "tecnica": "hero-anim",        // NO el nombre del modelo: la técnica
             "from": "gen/hero-still.png",  // el paso 1 del hero en dos pasos
             "prompt": "…", "dur": 5}}
  ]
}
```

`build_visuals()` convierte `gestures` a offsets restando el inicio real del
visual y los reparte en los parámetros con nombre del mockup — exactamente como
ya hace con `beats` y `stamp_at`.

`logo` acepta también una lista para `app_switch`.

---

## 6 · Documentación

| Archivo | Cambio |
| --- | --- |
| `CLAUDE.md` §12 | se reescribe: Higgsfield primario, tabla de costes reales, hero en dos pasos, regla de ruteo |
| `CLAUDE.md` §nuevo | capa de logos |
| `CLAUDE.md` §4 | paleta: entran `--alert`, `--go`, `--cool` con sus dos reglas |
| `references/design.md` | los mismos tres tokens |
| `CLAUDE.md` §16 | reglas duras nuevas (gesto sin palabra, un logo en color por frame) |
| `SKILL.md` §2 | paso 7 del pipeline |
| `SKILL.md` §1 | `.env` — `KIE_API_KEY` pasa a ser opcional/respaldo |
| `references/visuals.md` | se reescribe |
| `references/logos.md` | **nuevo** |
| `references/gotchas.md` | trampas nuevas que aparezcan durante la implementación |

---

## 7 · Verificación y criterios de aceptación

### Regresión — la pieza 1 no se rompe

1. `scripts/build-composition.py --project . --piece 1` corre sin error.
2. `npx hyperframes check public` → **0 errores** y **65/65 WCAG AA**, igual que hoy.
3. Ningún asset se vuelve a generar: el ledger existente sigue sirviendo de caché.

### Prueba real — la pieza 2

De punta a punta con `VIDEOS ORIGINALES/2/video.MOV` («Ventas, inventario y
reportes desconectados», CTA `ERP`). El `plan.json` se deriva del `guion.md` que
viene al lado, incluida su sección «Visuales y edición».

**Leer el `guion.md` es trabajo del agente al escribir el plan, no de un script.**
No se construye ningún parser: §12 ya dice que el paso 8 es el trabajo creativo.

1. Formato detectado con `detect-format.sh`, no asumido.
2. Al menos **un asset generado con Higgsfield** e importado con `gen.py import`,
   con su entrada de ledger completa (`provider: "higgsfield"`, taskId, créditos).
3. Al menos **un logo real** en tinta y **uno** en `brand`, con el ratio calculado
   y ≥3:1 verificado.
4. Al menos **un mockup con gestos** cuyos tiempos salgan del transcript.
5. El **dashboard del ERP** entra como grabación real del usuario, compuesta como
   visual y tratada para casarla con el papel crema (§D8). Es una **dependencia
   externa**: hace falta el archivo antes de montar esa escena.
6. El CTA `ERP` usa un color de señal de §3.5 y ese frame **no lleva naranja**.
7. `npx hyperframes check public` → 0 errores y **ningún aviso de contraste nuevo**
   por los tokens de señal.
8. **Verificado extrayendo frames del MP4**, nunca del navegador — y esperando al
   proceso del render, no a la fecha del archivo.

### Fallback — que el respaldo respalde de verdad

Probado sin gastar créditos: forzar `provider: "kie"` en un asset ya cacheado y
comprobar que `gen.py fallback` construye la llamada correcta a `kie.py` (modelo
mapeado, ratio, duración) sin lanzarla.

---

## Riesgos

| Riesgo | Mitigación |
| --- | --- |
| `kling3_0_turbo` no da el movimiento de óleo que daba Veo | El still se conserva; re-tirar solo el paso 2 cuesta 7.5 cr. Si un hero concreto lo exige, `provider: "kie"` explícito |
| El slug de Claude/Anthropic no existe en Simple Icons | `fetch-logos.py` falla ruidosamente; se verifica al implementar antes de depender de él |
| El MCP de Higgsfield no responde en una sesión futura | Es justo el caso que cubre la regla de ruteo: cae a Kie |
| Recolorear un logo se desvía de su brand guideline | Uso editorial-nominativo; Simple Icons es monocromo por diseño. Nunca se deforma el trazo |
| 219.94 créditos se agotan | ~8 piezas completas a 25 cr. Al agotarse, Kie sigue funcionando sin tocar nada |
| Los colores de señal diluyen la identidad de la marca | Acotados por las dos reglas de §3.5: sustituyen al naranja en vez de sumarse, y no se mezclan con la capa manuscrita. Si tras la pieza 2 el resultado se ve disperso, se revisa |
| La grabación del ERP no casa con el papel crema | Se trata como gráfico, no como metraje: §12 permite graduar un gráfico. Si el desvío es grande, se enmarca en mockup con chrome del proyecto |

---

## Alternativas descartadas

- **API REST de Higgsfield desde un script** — exigiría una clave nueva y
  duplicaría lo que el MCP ya hace conectado.
- **Generar los logos con IA** — un logo inventado se nota al instante y es lo
  contrario de lo pedido.
- **Color de marca siempre** — mete verdes y azules fríos en un sistema que los
  prohíbe (§4) y compite con el único momento naranja.
- **Interfaces animadas generadas con IA** — texto ilegible (§12 ya lo prohíbe) e
  imposible clavar un beat al segundo, a 7.5 cr por intento sin control.
- **Trocear `build-composition.py` en `compose/`** — refactor grande antes de lo
  pedido, arriesgando una pieza que hoy valida con 0 errores. Se pospone.
- **MCP sin ledger** — se perdería la caché y volver a correr el pipeline volvería
  a pagar.
