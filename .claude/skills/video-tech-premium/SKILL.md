---
name: video-tech-premium
description: Edita un video de talking head de punta a punta en un lenguaje visual moderno de contenido educativo sobre tecnología, IA y negocios — dos paletas de la marca (claro crema y oscuro casi negro, acento terracota), mockups de producto, punch-ins, subtítulos karaoke palabra a palabra, layout de bandas, grabaciones de pantalla dirigidas, sound design y música — y lo renderiza con HyperFrames. Úsala SIEMPRE que el usuario entregue un video suyo (.MOV/.mp4/grabación a cámara) para editar, montar, "dejarlo listo" para Reels/TikTok/Shorts/YouTube, quitarle pausas, ponerle subtítulos, gráficos, b-roll, mockups o sonido — aunque no nombre el estilo, aunque solo diga "edítame esto" o "hazme un reel con este video". Úsala también para retomar, ajustar o re-renderizar una pieza ya montada con este flujo, y para planificar cortes o transcribir con AssemblyAI dentro de él.
---

# Video Tech Premium

Flujo completo para convertir una grabación de talking head en una pieza terminada.

El objetivo de cada video es doble: **comunicar el contenido y demostrarlo visualmente**.
La prueba de fuego: **con el audio apagado se entiende la mayor parte del mensaje** — y
aun así la edición nunca compite con lo que se dice.

Idioma de trabajo y de las piezas: **español**.

El metraje **no se re-edita**: se recortan pausas y se reencuadra digitalmente, pero el
color y la imagen del usuario no se reinterpretan.

---

## 1 · Antes de empezar

```bash
python3 -c "import PIL, fontTools, cv2, numpy"   # deps
ffmpeg -version | head -1
npx hyperframes doctor
```

Faltantes habituales: `pip install pillow fonttools brotli numpy 'opencv-python-headless<5'`
(la 5.x quitó `CascadeClassifier` y la medición de cara deja de funcionar).

Claves en `<proyecto>/.env`, `chmod 600`, en `.gitignore`:

```
ASSEMBLYAI_API_KEY=...
KIE_API_KEY=...          # solo si la pieza lleva visuales generados
```

En un proyecto montado, `scripts/` es un enlace a los de esta skill. Si no existe:

```bash
ln -s .claude/skills/video-tech-premium/scripts scripts
```

---

## 2 · El pipeline

| # | Paso | Comando |
| --- | --- | --- |
| — | Andamio de la pieza | `scripts/new-piece.sh "VIDEOS ORIGINALES/2/video.MOV"` |
| 0 | Detectar formato | `scripts/detect-format.sh <src>` |
| 1 | Extraer audio | `ffmpeg -i <src> -vn -ac 1 -ar 16000 -c:a flac assets/audio/2.flac` |
| 2 | Transcribir | `scripts/transcribe.py assets/audio/2.flac transcripts/2.json` |
| 3 | Planificar cortes | `scripts/plan-cuts.py transcripts/2.json cuts/2.json <dur_real>` |
| 3b | **Preguntar las animaciones de la banda de arriba** | conversación con el usuario — sin script, ver más abajo |
| 4 | Corte bruto | `scripts/rough-cut.sh <src> cuts/2.json out/2-rough.mp4` |
| 5 | Medir la cara | `scripts/measure-face.py out/2-rough.mp4 assets/face-2.json` |
| 6 | Color (solo si es HDR) | `scripts/calibrate-hlg.py` + `scripts/make-hlg-lut.py` (§6) |
| 7 | Recorrido de pantalla | `scripts/screen-tour.py videos/2/screen-tour.json --preview` |
| 8 | Música | `scripts/make-music-bed.py assets/music/bed-tech.mp3 --dur 70` |
| 9 | **Escribir el plan** | `videos/2/plan.json` — **aquí está el trabajo creativo** |
| 10 | Componer | `scripts/build-composition.py --project . --piece 2` |
| 11 | Validar | `npx hyperframes check public` |
| 12 | Renderizar | `npx hyperframes render public --skill=talking-head-recut -o output.mp4 --fps 30 --sdr` |

En el paso 9 (o en su EDL) **se declara `"palette": "claro" | "oscuro"`**, obligatorio: sin
él `build-composition.py` falla. Si la pieza viene de un brief de `plan-edicion`, se usa la
que trae; si no, se pregunta en el 3b. Ver `references/design.md`.

Los pasos 1–8 son mecánicos. **El 9 es donde se decide la pieza** — y el 3b es donde el
usuario decide una parte de ella antes de que exista nada que montar.

### 3b — preguntar las animaciones, no decidirlas solo

**Si el usuario pega un brief de `plan-edicion`** (empieza con `Video fuente:` y trae
beats anclados a frases), ese brief ES la propuesta por beat:

1. Toma la `palette` que indica el brief para el plan/EDL.
2. Cuadra cada frase ancla con el transcript ya remapeado (paso 3). Una frase que no
   se dijo igual se busca por sentido y se le muestra al usuario el cambio.
3. Pregunta **solo** lo que no cuadra: frases que no aparecen, material marcado como
   faltante que no está en `VIDEOS ORIGINALES/<n>/`, componentes marcados *nuevo*,
   logos marcados *descargar* (`scripts/fetch-logos.py`).
4. La sección **"Ideas para sumar al editor"** se lista aparte como no soportada; no
   se construye en esta pieza salvo que el usuario lo pida.

Sin brief, el paso 3b sigue igual.

El triband le da a cada beat una banda de arriba que hay que llenar con algo — y ese algo
no se improvisa mientras se escribe el plan: se pregunta antes, con el transcript ya
remapeado al corte (paso 3) y **todavía nada construido** (ni corte bruto, ni recorrido de
pantalla, ni plan). Es el momento en que ya se sabe qué se dice y se puede hablar de qué se
ve sin comprometerse con nada todavía.

Lo que se le presenta al usuario, por cada beat del guion:

- **Los tiempos**, sacados del transcript remapeado (la función `remap()`, §4 punto 3) — no
  del transcript crudo, que vive en la línea del fuente.
- **El material disponible** en `VIDEOS ORIGINALES/<n>/`: grabaciones de pantalla, capturas,
  logos. Lo que hay decide lo que se puede proponer; inventar un mockup para algo que ya
  existe grabado va contra la regla de oro de b-roll semántico.
- **Una propuesta por beat** de qué ocupa la banda de arriba, para que el usuario confirme o
  cambie — nunca para montarla directo.

El vocabulario que hace la pregunta respondible (sin él, "qué animación" es una pregunta
abierta que nadie sabe contestar): `tool_card` (marca cuando se nombra algo),
`tool_recording` (grabación dirigida con chip de marca), los mockups de la librería
(`keyword_hero`, `stat_grid`, `chip_grid`, `flow_steps`, `comment_ui`, `chat_unanswered`…),
los objetos de `objects.py`, y `tool_lineup` (varias marcas en fila, para un beat que las
recoge todas).

**Dejar la banda vacía NO es una opción.** La banda `top` muestra algo en cualquier
segundo de un tramo `band`, y `check_band_top_covered` falla la compilación si no —
ver `references/triband.md`. Esto cambia la forma de la pregunta: no es «qué animación
quieres en este beat», es **«qué animación quieres en este beat, sabiendo que algo tiene
que haber»**. Un beat sin material no se queda en blanco: o se sostiene el visual
anterior, o se le inventa uno, y esa es la decisión que el usuario tiene que tomar.

Los dos criterios de la casa que chocan aquí, y cómo se resuelven:

- **Nada entra antes de su palabra** (§9): un logo no aparece antes de que se nombre. Así
  que el hueco anterior a un visual NO se tapa adelantándolo.
- **La banda nunca se queda vacía**: ese hueco se tapa **sosteniendo el visual anterior**
  hasta que entra el siguiente. El saliente cubre; el entrante sigue esperando su palabra.

El único hueco que no se arregla sosteniendo es el del primer visual de la pieza, porque
no hay nada delante. Ahí se mueve el inicio del tramo `band` para que coincida con su
entrada — el plano lleno dura un poco más y el triband empieza cuando hay algo que poner
en él.

---

## 3 · El modelo de tres capas

Es lo que hace posible cambiar de imagen cada 1–2.5 s sin reescribir nada. Las tres capas
son independientes y se cruzan por tiempo.

```
shots     el METRAJE. Una lista de encuadres: desde cuándo, con qué layout y
          con cuánto zoom se ve al creador. Aquí viven los punch-ins.
cards     rótulos y gráficos que FLOTAN sobre el metraje.
visuals   lo que OCUPA el lienzo: mockups, grabación de producto, imágenes.
```

### shots — los punch-ins

```jsonc
{"at": 0.00,  "kind": "full", "zoom": 1.12, "anchor": 0.42},
{"at": 0.42,  "kind": "pip",  "anchor": 0.30},
{"at": 19.30, "kind": "off"}
```

`kind`: `full` (a sangre) · `split` (gráfico + sujeto) · `pip` (ventana arriba a la
derecha, **por encima** de un takeover) · `off` (lo tapa un visual: no se emite elemento) ·
`band` (confina el metraje a la banda de abajo del layout `triband` — ver más abajo).

**Un encuadre es un elemento `<video>` nuevo, no un tween.** El renderer resuelve el rect
del `<video>` una sola vez al cargar, así que animar la geometría no reescala la imagen
—solo la recorta. Cada encuadre es una caja sobredimensionada con desborde negativo que
el stage recorta, y el salto entre dos es un **corte duro**, que además es el lenguaje que
pide la pieza.

Escala de zoom: **1.00 · 1.05 · 1.09 · 1.12 · 1.15**. El 1.15 es escaso — se reserva para
el remate del hook y para un clímax.

### El layout `triband`

**Desde ahora, el layout por defecto de TODOS los reels de este proyecto** — ya no un modo
que una pieza elige aparte. En vez de `full`/`pip` a lienzo entero, el lienzo REEL se parte
en tres bandas fijas — animación arriba, subtítulo en medio, hablante abajo — y el metraje
se confina a la de abajo. La geometría se declara **una sola vez** en `layout`; qué banda
ocupa el metraje en cada instante se activa **por segmento** con `kind: "band"` (o
`camera: "BAND"` en un EDL). Declarar `layout` no obliga a que todo el metraje viva en
banda: sigue conviviendo con `full`/`split`/`pip` segmento a segmento.

**Una pieza REEL sin `layout` falla la compilación** (`check_triband_default`, al lado de
los otros dos gates de abajo): la ausencia ya no es un estilo, es un olvido. YOUTUBE queda
fuera del gate — el triband es un reparto vertical y no tiene sentido en 16:9. La escotilla
para renunciar a él a sabiendas en una pieza concreta es `"layout": {"mode": "none"}`; el
mensaje de error del gate la nombra.

Un visual puede vivir DENTRO de una banda con `"band": "top"` — sin eso, un mockup normal
es opaco a lienzo completo y **tapa al hablante**, aunque en el navegador no se note nada
raro. Otros dos gates paran la compilación en vez de dejarlo llegar al MP4: uno si un
visual opaco solapa con un encuadre `band`, otro si el `anchor` de un encuadre `band`
cortaría la cabeza por arriba. Ninguno de los tres se salta a ojo — la geometría, la
fórmula del `anchor` y los `plan.json` que lo invocan están en `references/triband.md`.

### cards — rótulos flotantes

`place`: `top` · `center` · `bottom`. `key` pinta una palabra del titular en el acento como texto (`accent_hi`).
`body`: `none` · `stat` · `chips` · `cta`. `beats` son tiempos **absolutos** de la línea
del corte; el generador los convierte a offsets.

### visuals — lo que ocupa el lienzo

`role`: `takeover` (sustituye) · `backdrop` (va debajo, la tarjeta sigue encima).
`kind`: `mockup` · `screen-video` · `video` · `image`.
`cap_top` baja el subtítulo cuando el visual ocupa el centro.
`mock_pad_top` empuja el mockup para dejarle sitio al PiP.
`rect` coloca una grabación como tarjeta; alrededor va un **panel** (hairline + sombra,
sin navegador y sin gastar alto). `chrome` dibuja la barra de navegador solo si la URL es
parte del mensaje — cuesta 74 px que salen del tamaño de la interfaz.

---

## 4 · Las decisiones creativas

**1 · Cada frase importante necesita saber qué recurso la explica.** Analiza el transcript
y divide en unidades semánticas antes de tocar nada. Para cada una: ¿esto se entiende
mejor con un mockup, con el producto real, con una cifra grande, o con su cara?

**2 · B-roll semántico, nunca decorativo.** Si se nombra una herramienta, sale su logo o
su interfaz. Si se habla de un proyecto real, **manda la grabación del proyecto** por
encima de cualquier imagen generada.

**3 · Todos los beats salen del transcript.** Es el error que más se cuela: clavas la
entrada del visual y dejas sus animaciones internas con offsets bonitos. Si un elemento
representa algo que se dice, su tiempo va en `beats` (tarjetas), `draw_at`/`switch_at`
(mockups) o `clicks`/`boxes` (grabaciones).

Para pasar del timeline del fuente al del corte:

```python
def remap(t, keeps):
    acc = 0.0
    for k in keeps:
        if t < k["start"]: return acc
        if t <= k["end"]:  return acc + (t - k["start"])
        acc += k["dur"]
    return acc
```

**4 · Un visual por idea, no dos.** Si un takeover cubre la idea, la tarjeta que solape se
queda con kicker + titular.

**5 · La curva de intensidad.** El hook (0–3 s) es lo más agresivo de la pieza. El cuerpo
alterna descansos (zoom 1.00, plano abierto) con picos. **Quietud antes del clímax.** El
CTA simplifica: un solo elemento en pantalla.

---

## 5 · Subtítulos

**Bloques de 3–6 palabras, todas al mismo tamaño y color.** El bloque entra entero y se
queda quieto; lo que se mueve es un fondo de acento (`accent_pill`, no `accent`: el
acento empujado hacia el suelo hasta que el texto encima pase 4.5:1) que viaja
palabra a palabra, encendiéndose bajo la que se pronuncia en ese instante exacto y
apagándose en cuanto arranca la siguiente — nunca dos encendidos a la vez, y al terminar el
bloque no queda nada pintado. Es el **karaoke**, tratamiento único del subtítulo en toda la
pieza, también sobre metraje a plano lleno. Ya no hay una keyword agrandada y sola:
resaltar todas las palabras igual y a la vez sería un metrónomo, pero resaltar solo una
mientras el fondo viaja competiría por la atención — detalle completo en
`references/design.md`.

El troceo va por **jerarquía**: frase → cláusula → reparto parejo. Cortar solo por ancho
pega el final de una idea con el principio de la siguiente («…empleados. Cuando…») y el
espectador lee una frase que nadie dijo.

Las keywords se declaran en `plan.json`; las cifras se detectan solas. Ya no cambian el
render, solo hacen más conservador el cálculo de zona segura.

**Nunca sobre la cara.** La altura sale de proyectar la barbilla medida
(`measure-face.py`) al encuadre activo, y se consulta por el **punto medio** del bloque,
no por su inicio. En `triband` esto no aplica: ahí no hay metraje detrás del subtítulo, así
que se ancla por el suelo de su banda y crece hacia arriba (`references/design.md`).

Pieles: `on-dark` (sobre metraje — filete del color del suelo `bg` con `paint-order: stroke
fill`, que pinta el trazo detrás del relleno y no engorda la letra) · `on-surface` (sobre un gráfico,
o sobre suelo liso en `triband` — sin filete, solo sombra).

---

## 6 · Color

Si el metraje es **HLG/HDR** (`ffprobe` reporta `arib-std-b67`), hay que calibrar un LUT o
los colores de marca se desvían. Si es SDR (bt709), se convierte directo.

```bash
scripts/calibrate-hlg.py out/2-rough.mp4 5.5
scripts/make-hlg-lut.py assets/hlg-to-709.cube
ffmpeg -i out/2-rough.mp4 \
  -vf "lut3d=assets/hlg-to-709.cube,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv" \
  -c:v libx264 -crf 18 -g 30 -keyint_min 30 -pix_fmt yuv420p \
  -movflags +faststart -c:a aac videos/2/public/input-video.mp4
```

`setparams` es **obligatorio**: `lut3d` propaga las etiquetas de color de entrada.
Detalles: `references/color.md`.

---

## 7 · Sonido

**El efecto marca algo que pasa en imagen.** No hay relleno ambiental.

El volumen **se calcula, no se escribe**: los archivos tienen 27 dB de diferencia entre el
más caliente y el más flojo. `build_sfx()` mide cada uno y lo lleva a −27 dB de media con
techo de pico en −12 dB.

La **música** es una cama sintetizada (`make-music-bed.py`), libre de licencia y offline.
Vive 14 dB bajo la voz y, más importante, **deja vacía la banda 300–3000 Hz** donde viven
las consonantes. Una cama con energía ahí emborrona la voz aunque esté bajita.

⚠ `volumedetect` y `silencedetect` **loguean a nivel info**: con `-v error` no imprimen
nada y la medición sale vacía en silencio.

---

## 8 · Validar y renderizar

```bash
cd videos/2
npx hyperframes check public      # 0 errores antes de renderizar, siempre
npx hyperframes render public --skill=talking-head-recut -o output.mp4 --fps 30 --sdr
```

Avisos que no bloquean: `composition_file_too_large`, `timeline_track_too_dense`,
`pointer_events_none`.

Si existe un `public/index.motion.json` de una composición anterior, sus selectores ya no
existen y `check` falla con `motion_selector_missing`. **Reescríbelo o bórralo.**

### Verificar SIEMPRE sobre el MP4

```bash
npx hyperframes render public … & RENDER_PID=$!
wait $RENDER_PID
```

Esperar al **PID concreto**, no a que el archivo deje de cambiar (si ya existe un
`output.mp4` anterior la condición se cumple al instante y acabas analizando el archivo
viejo) ni a `pgrep -f "hyperframes render"`, que se caza a sí mismo y no sale nunca.

`npx hyperframes snapshot public --at 1.2,7.6,20.5` — lista separada por comas; repetir
`--at` no acumula.

---

## 9 · Reglas duras

**Hacer**
- Medir el formato y medir la cara. No estimar ninguna de las dos.
- Cada beat clavado a su palabra, sacado del transcript remapeado.
- Un visual por función, con la técnica variada: mockup para una interfaz, grabación real
  para un producto propio, cifra grande para un dato.
- **Recortar la grabación hasta que el flujo se lea.** Salida cuadrada y un `crop` sobre la
  zona que se nombra: un origen apaisado dentro de un lienzo vertical solo cabe grande si
  el recorte deja de ser apaisado. Sin navegador alrededor.
- Cambiar de imagen cada 1–2.5 s. El creador es el hilo conductor; el PiP lo mantiene en
  pantalla incluso durante un gráfico a pantalla completa.
- Verificar el resultado sobre el MP4, extrayendo frames.
- Dejar libre el **20 % inferior** del lienzo en REEL: ahí va la interfaz de la plataforma.
- Declarar `palette` en cada pieza y revisar `scripts/palette-sheet.py` cuando se toque
  `tokens.py`.

**No hacer**
- Estilizar el metraje. El color reproduce el original.
- Tapar la cara con subtítulos.
- Resaltar todas las palabras del subtítulo.
- Adelantar el guion: un logo no aparece antes de que se nombre.
- Dos clips a la vez en la misma pista.
- Confundir pista con apilado: el **índice de pista ordena el tiempo, el z-index ordena
  el apilado**.
- `back.out()` en una entrada: rebota como muelle y es lenguaje de dibujo animado.
- Dar por terminado un render mirando la fecha del archivo.
- Escribir un color a mano en un componente: todo sale de `tokens` (lo vigila
  `test_paletas_consumidores.py`).

---

## Referencias

| Necesitas | Lee |
| --- | --- |
| Todos los campos de `plan.json` | `references/plan-schema.md` |
| Las dos paletas, tipografía, layout, subtítulos | `references/design.md` |
| El layout `triband`: geometría, gates, `anchor`, cards de herramienta | `references/triband.md` |
| Mockups, grabaciones de pantalla, IA | `references/visuals.md` |
| Eases, punch-ins, sincronía con el habla | `references/motion.md` |
| Efectos, música y cálculo de ganancia | `references/sound.md` |
| Calibración HLG y enfoques descartados | `references/color.md` |
| Trampas del renderer y de las APIs | `references/gotchas.md` |

`references/gotchas.md` es el que más tiempo ahorra: fallos que **solo aparecen en el
MP4** y que ya están pagados una vez.
