---
name: video-tech-premium
description: Edita un video de talking head de punta a punta en un lenguaje visual moderno de contenido educativo sobre tecnología, IA y negocios — grafito profundo, violeta eléctrico, mockups de producto, punch-ins, subtítulos por bloques con keyword, grabaciones de pantalla dirigidas, sound design y música — y lo renderiza con HyperFrames. Úsala SIEMPRE que el usuario entregue un video suyo (.MOV/.mp4/grabación a cámara) para editar, montar, "dejarlo listo" para Reels/TikTok/Shorts/YouTube, quitarle pausas, ponerle subtítulos, gráficos, b-roll, mockups o sonido — aunque no nombre el estilo, aunque solo diga "edítame esto" o "hazme un reel con este video". Úsala también para retomar, ajustar o re-renderizar una pieza ya montada con este flujo, y para planificar cortes o transcribir con AssemblyAI dentro de él.
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
| 4 | Corte bruto | `scripts/rough-cut.sh <src> cuts/2.json out/2-rough.mp4` |
| 5 | Medir la cara | `scripts/measure-face.py out/2-rough.mp4 assets/face-2.json` |
| 6 | Color (solo si es HDR) | `scripts/calibrate-hlg.py` + `scripts/make-hlg-lut.py` (§6) |
| 7 | Recorrido de pantalla | `scripts/screen-tour.py videos/2/screen-tour.json --preview` |
| 8 | Música | `scripts/make-music-bed.py assets/music/bed-tech.mp3 --dur 70` |
| 9 | **Escribir el plan** | `videos/2/plan.json` — **aquí está el trabajo creativo** |
| 10 | Componer | `scripts/build-composition.py --project . --piece 2` |
| 11 | Validar | `npx hyperframes check public` |
| 12 | Renderizar | `npx hyperframes render public --skill=talking-head-recut -o output.mp4 --fps 30 --sdr` |

Los pasos 1–8 son mecánicos. **El 9 es donde se decide la pieza.**

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
derecha, **por encima** de un takeover) · `off` (lo tapa un visual: no se emite elemento).

**Un encuadre es un elemento `<video>` nuevo, no un tween.** El renderer resuelve el rect
del `<video>` una sola vez al cargar, así que animar la geometría no reescala la imagen
—solo la recorta. Cada encuadre es una caja sobredimensionada con desborde negativo que
el stage recorta, y el salto entre dos es un **corte duro**, que además es el lenguaje que
pide la pieza.

Escala de zoom: **1.00 · 1.05 · 1.09 · 1.12 · 1.15**. El 1.15 es escaso — se reserva para
el remate del hook y para un clímax.

### cards — rótulos flotantes

`place`: `top` · `center` · `bottom`. `key` pinta de violeta una palabra del titular.
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

**Bloques de 3–6 palabras con UNA sola keyword resaltada.**

Resaltar todas las palabras convierte el subtítulo en un metrónomo y el ojo deja de leer.
Resaltar una —una cifra, una herramienta, el concepto— convierte esa palabra en el titular
del frame. El bloque entra entero y se queda quieto; lo único que se mueve es la keyword,
en el instante exacto en que se pronuncia.

El troceo va por **jerarquía**: frase → cláusula → reparto parejo. Cortar solo por ancho
pega el final de una idea con el principio de la siguiente («…empleados. Cuando…») y el
espectador lee una frase que nadie dijo.

Las keywords se declaran en `plan.json`; las cifras se detectan solas.

**Nunca sobre la cara.** La altura sale de proyectar la barbilla medida
(`measure-face.py`) al encuadre activo, y se consulta por el **punto medio** del bloque,
no por su inicio.

Pieles: `on-dark` (sobre metraje — filete de grafito con `paint-order: stroke fill`, que
pinta el trazo detrás del relleno y no engorda la letra) · `on-surface` (sobre un gráfico
— sin filete, solo sombra).

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
while pgrep -f "hyperframes render" >/dev/null; do sleep 15; done
```

Esperar al **proceso**, no a que el archivo deje de cambiar: si ya existe un `output.mp4`
anterior la condición se cumple al instante y acabas analizando el archivo viejo.

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

---

## Referencias

| Necesitas | Lee |
| --- | --- |
| Todos los campos de `plan.json` | `references/plan-schema.md` |
| Paleta, tipografía, layout, subtítulos | `references/design.md` |
| Mockups, grabaciones de pantalla, IA | `references/visuals.md` |
| Eases, punch-ins, sincronía con el habla | `references/motion.md` |
| Efectos, música y cálculo de ganancia | `references/sound.md` |
| Calibración HLG y enfoques descartados | `references/color.md` |
| Trampas del renderer y de las APIs | `references/gotchas.md` |

`references/gotchas.md` es el que más tiempo ahorra: fallos que **solo aparecen en el
MP4** y que ya están pagados una vez.
