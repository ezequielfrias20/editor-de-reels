# El layout `triband`

Un modo de pieza, no de sistema: convive con el `full`/`split`/`pip` de siempre y se activa
**por segmento**. En vez de que el metraje ocupe el lienzo entero o una esquina, el lienzo
REEL se parte en tres bandas fijas que lo cubren de arriba a abajo **sin huecos**:

```
top      animación — card de logo, grabación de producto: lo que se está explicando
text     el subtítulo (la excepción de anclaje, ver `references/design.md`)
speaker  el hablante, SIEMPRE visible detrás del takeover
```

Medidas de la pieza 15 (REEL, 1080×1920):

```
top      y    0– 660
text     y  660– 960
speaker  y  960–1920
```

La división cae en la **mitad exacta** del lienzo (960 = H/2): el hablante ocupa la mitad
de abajo, ni más ni menos.

## Por qué la geometría es global y la activación es por segmento

Las tres bandas se declaran **una sola vez**, en el bloque `layout` del plan:

```jsonc
"layout": {
  "mode": "triband",
  "bands": {"top": [0, 660], "text": [660, 960], "speaker": [960, 1920]}
}
```

`triband_panels()` (en `build-composition.py`) lee esas coordenadas y las usa para
CUALQUIER encuadre o visual que pida una banda — no hay una geometría distinta por
segmento, porque cambiar el alto de la banda `speaker` a media pieza rompería el anclaje
del subtítulo y el `anchor` ya medido de cada encuadre `band`. La geometría es una
propiedad de LA PIEZA; qué banda ocupa el metraje en cada instante es una propiedad de
CADA SEGMENTO.

Esa segunda parte se activa con `kind: "band"` en un encuadre del plan (o `camera: "BAND"`
en un EDL, que `edl_compile.py` traduce 1:1 a `kind: "band"`). Cuando el EDL trae un
bloque `layout`, `edl_schema.validate_layout()` exige que:

- `mode` sea uno de los conocidos (`triband`, hoy el único),
- las tres bandas (`top`, `text`, `speaker`) estén presentes,
- cada una sea `[y0, y1]` válida (no invertida ni vacía),
- **cubran `0..H` de forma contigua** — sin huecos ni solapes entre bandas,
- y que si se declara `layout` haya al menos un segmento `camera: "BAND"`, y viceversa: un
  segmento `BAND` sin `layout` en la cabecera falla antes de compilar.

Si el plan se escribe a mano (sin pasar por el EDL), esa validación no corre — el gate
equivalente en `build-composition.py` es que `triband_panels()` **revienta** con un
`RuntimeError` explícito si un encuadre `kind: "band"` aparece sin bloque `layout` en el
plan: no hay un lienzo-completo por defecto silencioso, porque la geometría de las bandas
no tiene un valor implícito razonable.

## `band` no lleva escalera de zoom

Un encuadre `full` recorre la escalera 1.00 · 1.05 · 1.09 · 1.12 · 1.15. Un encuadre `band`
no: el rect de la banda `speaker` (960 px de alto en la pieza 15, contra los 1920 del
lienzo) ya recorta fuerte, y una escalera de zoom ENCIMA de eso dejaría la cara
irreconocible. El reencuadre vertical dentro de la banda lo hace `object-position` con el
`anchor` de siempre — ver la fórmula más abajo.

```jsonc
{"at": 8.216, "kind": "band", "anchor": 0.38}
```

## `band` en un visual

Un visual (`kind: "mockup"`, `"screen-video"`, …) puede declarar `"band": "top"` para vivir
DENTRO de una banda en vez de ocupar el lienzo entero:

```jsonc
{
  "id": "v-tool-1", "role": "takeover", "kind": "mockup",
  "start": 9.076, "end": 10.747,
  "band": "top",
  "mock": ["tool_card", {"slug": "animejs", "name": "Anime.js", "kicker": "LIBRERÍA"}]
}
```

`band` convive con `role` (que sigue decidiendo la PISTA: `backdrop`/`takeover`), no lo
sustituye — solo cambia la GEOMETRÍA del host: en vez de `{left:0, top:0, width:W,
height:H}` recibe el rect exacto de esa banda, y **el fondo pasa a transparente en vez de
opaco**. Sin `band`, un visual `kind: "mockup"` recibe un host opaco a lienzo completo
(`grid()+vignette()` detrás) porque eso es lo correcto para un mockup que SUSTITUYE el
metraje — pero un visual que vive en la banda `top` tiene que dejar ver la banda `speaker`
por debajo, donde sigue el hablante.

**Es el bug que más costó de la sesión.** Antes de que `band` existiera como opción de
visual, una card de logo a lienzo completo con host opaco tapaba al hablante entero
durante las cinco cards de logo de la pieza 15: **luma máxima 28** medida sobre el MP4 en
la banda `speaker`, donde debía verse la camiseta blanca del presentador (**~253**
esperado con el hablante visible). Declarar `"band": "top"` en el visual arregla el fondo;
`mock_pad_bottom` (que solo EMPUJA el gráfico hacia arriba con relleno) no basta, porque no
toca la opacidad del host — son dos mecanismos distintos y solo uno resuelve el tapado.

Sin `layout` en el plan, declarar `band` en un visual falla igual que un encuadre `band`
suelto: no hay rect de dónde sacarlo.

## Los dos gates de `build-composition.py`

Ambos viven uno al lado del otro, con la misma filosofía: el error no tiene arreglo en
post, así que para la compilación en vez de colarse hasta el MP4.

### `check_band_speaker_clear`

Falla si un visual `kind: "mockup"` **sin** `band` (por tanto opaco, a lienzo completo)
solapa en el tiempo con un encuadre `kind: "band"` — ese encuadre confina el metraje a la
banda `speaker` precisamente para que el hablante se siga viendo, y un host opaco por
encima lo tapa igual que taparía cualquier otro metraje. El solape se compara con
tolerancia de 1 frame; si algo excede eso, el mensaje de error dice qué visual y qué
encuadre chocan y sugiere el arreglo (`"band": "top"`).

### `check_face_top_clear`

Con `object-fit: cover`, un `anchor` demasiado ALTO en un encuadre `band` recorta más del
techo de la fuente y se lleva la coronilla por delante. Este gate proyecta el borde
superior medido de la cara (`top_frac`, ver más abajo) con la MISMA fórmula que decide
dónde cae la barbilla, y si el resultado cae por encima del techo de la banda `speaker`,
compila con error explicando el `anchor` y el `y` calculado.

`top_frac` es un campo nuevo de `measure-face.py` (junto al ya existente `chin_frac`): el
percentil 5 de la altura de la caja de cara sobre las mismas 48 muestras Haar que ya median
la barbilla (percentil 95) — el espejo del p95, para que un frame donde Haar detecta más
alto de lo normal (falso positivo raro) no arruine el resultado igual que el p95 protege
contra un falso positivo bajo. Una medición de ANTES de esta mejora no trae `top_frac`, y
el gate lo trata como "no verificable": se salta limpio, no rompe piezas viejas que nunca
midieron ese campo.

## Cómo se deriva el `anchor` de una banda

Es aritmética, no gusto. Con `object-fit: cover`, un metraje fuente de 1080×1920 dentro de
una banda de alto `h` (ancho completo, 1080 px, así que la escala de cover la fija
exactamente el alto):

```
barbilla    = banda.top − (1920 − h)·anchor + chin_frac · 1920
borde_cara  = banda.top − (1920 − h)·anchor + top_frac  · 1920
```

Dos restricciones:

1. **La barbilla por encima de y1536** (el 20 % inferior del lienzo REEL, donde la
   plataforma pinta su interfaz).
2. **El borde superior de la cara por debajo del techo de la banda `speaker`** (no se
   corta la cabeza — `check_face_top_clear`).

### Ejemplo resuelto — pieza 15

`chin_frac = 0.4531`, `top_frac = 0.2812` (medidos, `assets/face-15.json`, 48/48
muestras). Banda `speaker`: `top = 960`, `h = 960` → `1920 − h = 960`.

```
barbilla   = 960 − 960·anchor + 0.4531·1920 = 1830.0 − 960·anchor
borde_cara = 960 − 960·anchor + 0.2812·1920 = 1499.9 − 960·anchor
```

Restricción 1 (`barbilla ≤ 1536`): `anchor ≥ 0.306`.
Restricción 2 (`borde_cara ≥ 960`): `anchor ≤ 0.562`.

Cualquier `anchor` en `[0.31, 0.56]` es válido. La pieza 15 usa **`anchor = 0.38`**:

```
barbilla   = 1830.0 − 960·0.38 = 1465.2   (70.8 px de margen bajo y1536)
borde_cara = 1499.9 − 960·0.38 = 1135.1   (175 px de margen sobre el techo y960)
```

`0.38` se bajó desde el `0.5714` por defecto del estilo: con la banda `speaker` más alta
que en el montaje inicial (960 en vez de 1120), ese default subía demasiado el recorte y
se llevaba la coronilla — el gate lo habría cazado.

## Cards de herramienta — los fragmentos exactos

Coreografía de la pieza 15, repetida para sus cinco herramientas: card de logo
(`tool_card`, banda `top`) clavada a la palabra que nombra la herramienta → grabación
dirigida (`tool_recording`) durante los 6–8 s que dura. La doctrina de cada componente
—qué hace, por qué se despacha donde se despacha, el aspecto 3D— está en
`references/visuals.md`; esto es lo que se escribe en `plan.json`, verificado contra
`videos/15/plan.json` y `build_visuals`.

**La card de logo** — un visual `kind: "mockup"` con `band: "top"`:

```jsonc
{
  "id": "v-tool-1", "role": "takeover", "kind": "mockup",
  "start": 9.076, "end": 10.747,
  "band": "top",
  "mock": ["tool_card", {"slug": "animejs", "name": "Anime.js", "kicker": "LIBRERÍA"}]
}
```

**La grabación** — un visual `kind: "screen-video"` con `tool_recording` en vez de
`chrome`/`panel`:

```jsonc
{
  "id": "v-rec-1", "role": "takeover", "kind": "screen-video",
  "start": 10.747, "end": 15.648,
  "src": "animejs-tour.mp4",
  "rect": [60, 100, 960, 540],
  "tool_recording": {"slug": "animejs", "name": "Anime.js", "hairline": 1}
}
```

`rect` es 16:9 sin deformar (960×540) pegado al suelo de la banda `top`: `ry` 100 + alto
540 = 640, 20 px hasta el techo de la banda `text` (y660) — el mismo margen
(`BAND_MOCK_MARGIN = 20`) que usa `tool_card` para alinearse al final de su banda en vez de
centrarse, así que las cinco cards de logo, las cinco grabaciones y la card del CTA
comparten el mismo borde inferior y el frame se lee como una fila, no como piezas sueltas.

La única variación entre las cinco es `hairline`, y solo en Manus:

```jsonc
"tool_recording": {"slug": "manus", "name": "Manus", "hairline": 3}
```

porque su grabación es la única de las cinco con fondo CLARO y necesita un marco más
marcado para no perderse contra un fondo también claro. El componente no conoce el slug
`"manus"`; quien escribe el plan decide el grosor por grabación.
