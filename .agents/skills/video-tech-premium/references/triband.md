# El layout `triband`

**Desde la doctrina de 2026-09-15, es el layout por defecto de TODOS los reels de este
proyecto** — ya no un modo que una pieza elige aparte. Toda pieza REEL declara el bloque
`layout`, aunque sea para renunciar a él a sabiendas con `"layout": {"mode": "none"}`
(la escotilla; ver `check_layout_default` más abajo). YOUTUBE queda fuera: el triband
reparte el lienzo en tres bandas verticales y no tiene sentido en 16:9 apaisado.

Dentro de una pieza sigue conviviendo con el `full`/`split`/`pip` de siempre y se activa
**por segmento**: declarar `layout` no obliga a que TODO el metraje viva en banda, solo
declara la geometría disponible para quien quiera usarla. En vez de que el metraje ocupe
el lienzo entero o una esquina, el lienzo REEL se parte en tres bandas fijas que lo cubren
de arriba a abajo **sin huecos**:

```
top      animación — card de logo, grabación de producto: lo que se está explicando
text     el subtítulo (la excepción de anclaje, ver `references/design.md`)
speaker  el hablante, SIEMPRE visible detrás del takeover
```

Medidas (REEL, 1080×1920):

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
no: el rect de la banda `speaker` (960 px de alto, contra los 1920 del
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

**Es el bug que más costó.** Antes de que `band` existiera como opción de visual, una card
de logo a lienzo completo con host opaco tapaba al hablante entero mientras duraba: sobre
el MP4, la banda `speaker` salía plana y del color del suelo (luma máxima 28 con el suelo
oscuro), donde debía verse la camiseta clara del presentador (~253). ⚠ En la paleta
`claro` ese umbral de luma no delata nada —un host opaco crema también pasa de 200—: ahí se
mira que la banda no sea plana, o se extrae el frame. Declarar `"band": "top"` en el visual arregla el fondo;
`mock_pad_bottom` (que solo EMPUJA el gráfico hacia arriba con relleno) no basta, porque no
toca la opacidad del host — son dos mecanismos distintos y solo uno resuelve el tapado.

Sin `layout` en el plan, declarar `band` en un visual falla igual que un encuadre `band`
suelto: no hay rect de dónde sacarlo.

## Los tres gates de `build-composition.py`

Los tres viven uno al lado del otro, con la misma filosofía: el error no tiene arreglo en
post (o, en el caso del primero, es un olvido que nadie va a ver hasta que el reel ya está
publicado), así que paran la compilación en vez de colarse hasta el MP4.

### `check_layout_default`

Falla si el plan es REEL y **no trae bloque `layout`**. Es el gate de la doctrina: antes
`layout` era opt-in y una pieza sin él caía en silencio al full/pip/split de siempre; ahora
la ausencia de `layout` en un REEL es indistinguible de un olvido, así que el compilador la
trata como tal. No corre en YOUTUBE — el triband es un reparto vertical y no hay banda de
arriba que llenar en 16:9.

La escotilla es `"layout": {"mode": "none"}`: cualquier bloque `layout` no vacío satisface
el gate, sea la geometría real del triband o esta renuncia explícita. El mensaje de error
nombra las dos salidas — declarar el triband o declarar la renuncia — porque un gate sin
salida documentada es un gate que alguien acaba comentando la primera vez que estorba.

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

### Ejemplo resuelto

`chin_frac = 0.4531`, `top_frac = 0.2812` (una medición real de `measure-face.py`, 48/48
muestras; se mide en cada pieza, nunca se reutiliza). Banda `speaker`: `top = 960`, `h = 960` → `1920 − h = 960`.

```
barbilla   = 960 − 960·anchor + 0.4531·1920 = 1830.0 − 960·anchor
borde_cara = 960 − 960·anchor + 0.2812·1920 = 1499.9 − 960·anchor
```

Restricción 1 (`barbilla ≤ 1536`): `anchor ≥ 0.306`.
Restricción 2 (`borde_cara ≥ 960`): `anchor ≤ 0.562`.

Cualquier `anchor` en `[0.31, 0.56]` es válido. Con **`anchor = 0.38`**:

```
barbilla   = 1830.0 − 960·0.38 = 1465.2   (70.8 px de margen bajo y1536)
borde_cara = 1499.9 − 960·0.38 = 1135.1   (175 px de margen sobre el techo y960)
```

`0.38` se bajó desde el `0.5714` por defecto del estilo: con la banda `speaker` más alta
que en el montaje inicial (960 en vez de 1120), ese default subía demasiado el recorte y
se llevaba la coronilla — el gate lo habría cazado.

## Cards de herramienta — los fragmentos exactos

La coreografía de un reel de herramientas, repetida para cada una: card de logo
(`tool_card`, banda `top`) clavada a la palabra que nombra la herramienta → grabación
dirigida (`tool_recording`) durante los 6–8 s que dura. La doctrina de cada componente
—qué hace, por qué se despacha donde se despacha, el aspecto 3D— está en
`references/visuals.md`; esto es lo que se escribe en `plan.json`, verificado contra
`build_visuals`.

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
centrarse, así que las cards de logo, las grabaciones y la card del CTA
comparten el mismo borde inferior y el frame se lee como una fila, no como piezas sueltas.

La variación habitual entre grabaciones es `hairline`:

```jsonc
"tool_recording": {"slug": "manus", "name": "Manus", "hairline": 3}
```

porque una grabación de fondo del mismo valor que el suelo de la paleta (una web clara
en `claro`, una oscura en `oscuro`) necesita un marco más marcado para no perderse contra
él. El componente no conoce el slug
`"manus"`; quien escribe el plan decide el grosor por grabación.

## La banda `top` nunca se queda vacía

Doctrina de 2026-09-15, a petición del usuario: **«en la parte de animaciones siempre se
debe mostrar algo, en cualquier segundo, nunca debe estar el fondo vacío»**. Sin esta
regla, un reel de cinco herramientas dejaba la banda de arriba en suelo liso **más de una
cuarta parte** de sus tramos `band`, repartida en siete huecos — desde menos de un segundo
(el arranque, antes de la primera card) hasta casi seis (un beat de guion entero sin
visual).

### La tensión con «nada entra antes de su palabra», y cómo se resuelve

Esta regla choca de frente con la de siempre (`references/visuals.md`, §7 de `CLAUDE.md`):
no se puede adelantar la card SIGUIENTE para tapar el hueco que la precede, porque
entonces el espectador lee el nombre de la herramienta antes de que se diga.

**La salida es sostener el visual ANTERIOR, nunca adelantar el siguiente.** El visual que
ya está en pantalla —la grabación de Anime.js, por ejemplo— se queda puesto (se extiende
su `end`) hasta que entra la card de Motion; la card de Motion sigue esperando su propia
palabra, sin moverse ni un frame. El visual saliente cubre el hueco con algo que YA se
dijo; el entrante no adelanta nada. Es la misma idea que ya usa `check_no_black` para el
metraje (§9 de `CLAUDE.md`), aplicada aquí a los visuales de la banda `top` en vez de al
metraje de la banda `speaker`.

Documéntalo así porque es exactamente el tipo de arreglo que alguien intenta deshacer mal
dentro de seis meses: la tentación, viendo un hueco antes de "Motion", es adelantar la
card de Motion medio segundo — parece un arreglo más simple y ROMPE la regla de oro. El
arreglo correcto siempre mira hacia ATRÁS en el tiempo, nunca hacia delante.

Un solo hueco no se arregla sosteniendo, por no tener nada delante que sostener: el
arranque del propio tramo `band`, si el encuadre cambia a `band` antes de que la primera
card entre. Ahí la salida es mover el `at` del encuadre para que coincida con la entrada
de esa primera card — el hook a plano lleno dura un poco más, no hay banda de arriba
vacía que llenar porque todavía no hay banda.

Y un hueco puede no ser un problema técnico sino un beat de guion sin visual asignado:
«he juntado estas y varias más en una guía…» no nombra ninguna herramienta nueva que
clavar — todas se dijeron antes. Ahí la resolución no es sostener nada de lo anterior (la
última grabación ya cerró su propia cola), es un visual NUEVO: las marcas juntas, en fila,
entrando mientras él dice «estas y varias más» — no adelanta nada porque todas ya tuvieron
su palabra. Ver `tool_lineup` más
abajo.

### `check_band_top_covered`

Falla si en cualquier instante de un tramo `kind: "band"` ningún visual ocupa la banda
`top` — mismo lugar de `build-composition.py` que los otros tres gates de este documento,
misma filosofía: el hueco no tiene arreglo en post, así que para la compilación en vez de
colarse hasta el MP4. El mensaje lista los huecos con sus tiempos exactos (como la tabla
de arriba), porque un gate que solo dice «hay un hueco» obliga a buscarlo a mano.

**«Ocupar la banda» tiene DOS mecanismos**, los mismos que ya conviven en `build_visuals`,
y el gate tiene que reconocer los dos o falla en falso contra piezas que sí cumplen la
regla:

1. Un `kind: "mockup"` con `band: "top"` (una card de logo, el CTA) confina su host al
   rect exacto de esa banda — cubre por definición.
2. Un `kind: "screen-video"` (una grabación) **nunca declara `band`**: su `<video>` real
   se coloca con `rect` en coordenadas de LIENZO, con host transparente por ser
   `screen-video` sin que `band` tenga que ver nada. El gate lo detecta comprobando que el
   `rect` solapa verticalmente con la banda `top`.

⚠ **Mirar solo `v.get("band") == "top"` deja fuera las grabaciones enteras** — el
primer intento de este gate lo hizo así, y contra un `plan.json` real
marcó como «vacíos» los 4-10 segundos completos de CADA grabación, no solo los huecos de
verdad entre ellas. Se cazó verificando el gate nuevo contra el plan SIN arreglar antes de
tocar nada: los huecos que reportaba no coincidían con la tabla medida a mano.

La cuenta usa las ventanas CRUDAS `start`/`end` de cada visual, **sin** el margen de
`fade_in`/`fade_out` que sí aplica `check_no_black`. Es a propósito: dos visuales de banda
que se TOCAN exactamente —la card de logo y su propia grabación, contiguas en cada
herramienta— hacen un cruce de opacidades legítimo en ese instante, no un hueco.
Medirlo con el margen de fundido marcaría en falso cada una de esas transiciones que ya
funcionan (⁓0.5 s cada una). Tolerancia de un frame (1/FPS), igual
que `check_band_speaker_clear`, para no fallar por redondeo de cuantización.

### `tool_lineup` — el beat de «la guía»

El componente para el hueco que no se arregla sosteniendo: las herramientas ya nombradas,
juntas en fila, construido sobre el mismo marco de logo que usa `tool_card`
(`.tc-logoframe`: hairline `LINE_HI` + fondo `bg`) en vez de un componente nuevo desde
cero. Se descartaron los otros dos candidatos de la librería que dibujan algo parecido:

- `chip_grid` pinta **texto** en pastillas, no marcas — no sirve para «las marcas juntas».
- `app_switch` sí dibuja logos, pero está diseñado para sistemas AISLADOS con un
  conector ROTO entre tarjetas — la frase de este beat es la contraria («las he
  juntado»), así que usarlo diría lo opuesto de lo que se cuenta.

```jsonc
{
  "id": "v-tool-lineup", "role": "takeover", "kind": "mockup",
  "start": 61.805, "end": 67.785,
  "band": "top", "absolute_times": true,
  "mock": ["tool_lineup", {
    "tools": [["animejs", "Anime.js"], ["motion", "Motion"],
              ["kokonutui", "Kokonut UI"], ["bklitui", "Bklit UI"], ["manus", "Manus"]],
    "at": [62.547, 62.740, 63.108, 63.173, 63.493]
  }]
}
```

⚠ **`logos.mark()` devuelve `(html, ratio)` y `ratio` puede ser `None`** para una marca
transparente (animejs, kokonutui aquí) — no hay tile que perderse contra el fondo. Y para
las que SÍ traen un tile (Motion, Bklit UI: casi negro), el ratio que devuelve
`mark()` está medido contra `surface` (su fondo por defecto), no contra `bg` — el fondo
real de `.tlframe`/`.tc-logoframe` — así que un número bajo no describe lo que de verdad
se renderiza. `tool_lineup` descarta el ratio a propósito, exactamente igual que
`tool_card` con el mismo marco: no hay gate de contraste que tocar aquí, y si alguna vez
se añade uno, tiene que tratar el caso `None` o revienta con la primera marca transparente
de la lista — ya mordió una vez en un componente distinto.
