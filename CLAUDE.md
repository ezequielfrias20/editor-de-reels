# editor-videos — estilo "Tech Premium"

Proyecto de edición de video con **HyperFrames** (video renderizado desde HTML).

El objetivo de cada pieza es doble: **comunicar el contenido y demostrarlo visualmente**.
La prueba de fuego: **con el audio apagado se entiende la mayor parte del mensaje** — y
aun así la edición nunca compite con lo que se dice.

Idioma de trabajo y de los videos: **español**.

> **Nota de historia.** Hasta agosto de 2026 el proyecto usaba un estilo *Editorial
> Retro-Digital* (papel crema, tipografía didone, subtítulos karaoke, anotaciones a mano).
> Se sustituyó por completo: no gustaba y no encajaba con contenido de tecnología, IA y
> negocios. La skill se renombró de `editorial-retro-digital` a `video-tech-premium`. La
> pieza 1 quedó renderizada con el estilo viejo; re-renderizarla la traería al nuevo.

---

## 1. Formatos

Dos formatos. **El formato lo dicta el video fuente, no se pregunta.**

| | **REEL** | **YOUTUBE** |
| --- | --- | --- |
| Relación | 9:16 vertical | 16:9 apaisado |
| Canvas | 1080 × 1920 | 1920 × 1080 |
| FPS | 30 | 30 |
| Duración típica | 30–90 s | 60 s – 3 min |

### Regla de detección — obligatoria antes de crear el proyecto

```bash
scripts/detect-format.sh "VIDEOS ORIGINALES/2/video.MOV"
```

Relación < 1 → **REEL**; ≥ 1 → **YOUTUBE**. Contempla la **rotación embebida**: el footage
de iPhone se almacena apaisado con una display matrix de ±90°, así que `width`/`height`
crudo miente. Fuente casi cuadrada (0.95–1.05): avisa y **no decide**.

El metraje **no se re-edita**: se recortan pausas y se reencuadra digitalmente, pero el
color y la imagen del usuario no se reinterpretan.

---

## 2. Pipeline de producción

Orden fijo, todo re-ejecutable. Si cambia el plan de cortes, se vuelve a correr desde el 3.

| # | Paso | Comando |
| --- | --- | --- |
| 0 | Detectar formato | `scripts/detect-format.sh <src>` |
| 1 | Extraer audio | `ffmpeg -i <src> -vn -ac 1 -ar 16000 -c:a flac assets/audio/2.flac` |
| 2 | Transcribir | `scripts/transcribe.py assets/audio/2.flac transcripts/2.json` |
| 2b | **Cuadrar el transcript con el audio** | `scripts/refine-timings.py assets/audio/2.flac transcripts/2.json --write` |
| 3 | Planificar cortes | `scripts/plan-cuts.py transcripts/2.json cuts/2.json <dur_real>` |
| 4 | Corte bruto | `scripts/rough-cut.sh <src> cuts/2.json out/2-rough.mp4` |
| 5 | Medir la cara | `scripts/measure-face.py out/2-rough.mp4 assets/face-2.json` |
| 6 | Color, solo si es HDR (§8) | `scripts/calibrate-hlg.py` + `scripts/make-hlg-lut.py` |
| 7 | Recorrido de pantalla | `scripts/screen-tour.py videos/2/screen-tour.json --preview` |
| 8 | Música | `scripts/make-music-bed.py assets/music/bed-tech.mp3 --dur 70` |
| 9 | **Escribir el plan** | `videos/2/plan.json` ← **el trabajo creativo** |
| 10 | Componer | `scripts/build-composition.py --project . --piece 2` |
| 11 | Validar | `npx hyperframes check public` |
| 12 | Renderizar | `npx hyperframes render public --skill=talking-head-recut -o output.mp4 --fps 30 --sdr` |

### Transcripción — AssemblyAI, no Whisper

Whisper se come lo que se dice bajito. `transcribe.py` usa AssemblyAI y devuelve **timings
por palabra**, que es lo que alimenta todo el anclaje de la pieza.

**No fiarse solo del transcript.** El cruce con la energía real del audio ya no se hace a
mano: `scripts/refine-timings.py <audio> <transcript> [--write]` lo automatiza y hace tres
cosas que antes se descubrían tarde.

1. **Cuadra los bordes que dan a un hueco.** AssemblyAI clava el centro de cada palabra y
   recorta los bordes contra el silencio: la primera palabra tras una pausa aparece hasta
   240 ms tarde. Da igual para leer y es grave aquí, porque `plan-cuts.py` corta justo en
   esos huecos y un borde optimista se lleva el ataque de la palabra siguiente. En la
   pieza 3 movió 9 bordes; en la 4, diez.
2. **Avisa de sonido audible sin transcribir**, clasificado por espectro (más grave que
   agudo → vocalización; más agudo → respiración) y **por islas**: un hueco con dos
   soplidos sueltos se corta sin pensarlo, uno lleno de una duda de dos segundos no.
3. **Marca los tramos con la alineación rota** por ritmo silábico imposible (>12 síl/s).

**Ese tercer aviso salvó la pieza 3.** El tramo 27–35 s venía desplazado casi 2 s —cinco
palabras seguidas a más de 13 síl/s, «dólares» en 113 ms— y todos los beats de ese tramo
habrían caído fuera. El remedio no es este script: se **re-transcribe el tramo suelto**,
que sale bien porque el modelo deja de arrastrar el contexto largo, y se empalma.

⚠ **Y el transcript miente con las siglas.** «BCV» lo oye como «de ese B» porque él las
deletrea. Ninguna medición lo caza: hay que leer el texto contra el guion.

`silencedetect` y `volumedetect` **loguean a nivel info**: con `-v error` no imprimen nada.

### Plan de cortes

`plan-cuts.py` nunca corta dentro de una palabra. Los huecos largos se **colapsan a una
pausa natural**, no se eliminan. Cortes por debajo de 0.25 s se descartan.

Pasar **siempre la duración real** de `ffprobe`: el `audio_duration` de AssemblyAI viene
redondeado al segundo y desplaza el corte de cola. **Verificar re-transcribiendo el corte**
y comparando el número de palabras.

---

## 3. Sistema visual — grafito profundo + violeta eléctrico

Fondo casi negro, superficies flotando encima con hairline claro y sombra ancha,
tipografía grotesca pesada y un único acento violeta de alto voltaje por frame.

La fuente de verdad es `scripts/tokens.py`.

El violeta **no es decorativo**: sale del producto real que se muestra en pantalla (el
ERP). Así el gráfico y el screenshot pertenecen al mismo mundo.

```
/* suelo */                      /* texto */
--bg:        #0B0C10             --text:      #FFFFFF
--bg2:       #101218             --text2:     #A7ADBB
--surface:   #16181F             --text3:     #8C93A3
--surface2:  #1D2029
--surface3:  #252935
                                 /* señal */
/* acento */                     --go:        #34E39B
--violet:    #7C5CFF             --alert:     #FF5A5A
--violet-hi: #9B85FF             --warn:      #FFB84D
--violet-dk: #5B3FD6
```

**Nada de negro puro (#000) ni blanco puro como fondo.** El #0B0C10 deja respirar los
oscuros del metraje en vez de aplastarlos.

**Contrastes ya verificados** — no repetir el error:

| Combinación | Ratio | Uso |
| --- | --- | --- |
| text2 / surface | 7.88:1 | ✅ texto pequeño |
| **text3 / surface** | **5.76:1** | ✅ ya aguanta texto pequeño |
| violet / bg | 4.50:1 | solo texto grande |
| **violet-hi / bg** | **6.70:1** | ✅ el violeta cuando es TEXTO |
| blanco / violet | 4.35:1 | solo ≥24 px y en negrita |
| bg / go | 11.74:1 | sobre verde va tinta, **no blanco** |

`tokens.contrast(a, b)` mide cualquier par nuevo antes de renderizar.

### Tipografía

**Dos familias.** Una tercera hace que la pieza parezca un collage.

| Rol | Familia |
| --- | --- |
| Todo el texto | **Inter** 400–900 (900 para titulares y subtítulos) |
| Etiquetas de UI, datos, chips | **JetBrains Mono** 400/700, uppercase, tracking amplio |

Cuanto más grande el texto, más se cierra el tracking. Escala en `tokens.TYPE`.

✅ Las 8 woff2 están vendorizadas y verificadas en `assets/fonts/`. Se regeneran con
`scripts/fetch-fonts.py`.

⚠ **Trampa de Google Fonts:** el CSS devuelve varios `@font-face` por familia y el
**primero es el cirílico** — quedarse con el primer `src` baja un subset sin una sola
tilde. Hay que elegir el bloque cuyo `unicode-range` contenga `U+0000-00FF`.

### Textura y elevación

- Fondo: `vignette()` radial + `grid()` a `rgba(255,255,255,.022)` cada 72 px.
- **Hairline claro** como único borde. Sobre fondo oscuro una sombra negra no se ve: la
  elevación la dan la sombra *y* el hairline.
- Sombra: `0 2px 6px rgba(0,0,0,.45), 0 18px 50px rgba(0,0,0,.55)`. Nunca dura.
- Glow violeta **escaso**: solo el objeto protagonista del frame.
- Radios: `sm 10 · md 16 · lg 24 · xl 32 · pill 9999`.

---

## 4. El modelo de tres capas

Es lo que permite cambiar de imagen cada 1–2.5 s sin reescribir nada.

```
shots     el METRAJE. Desde cuándo, con qué layout y con cuánto zoom se ve al
          creador. Aquí viven los punch-ins.
cards     rótulos y gráficos que FLOTAN sobre el metraje.
visuals   lo que OCUPA el lienzo: mockups, grabación de producto, imágenes.
```

### shots — los punch-ins

`kind`: `full` · `split` · `pip` (arriba a la derecha, **por encima** del takeover) ·
`off` (lo tapa un visual: no se emite elemento).

**Un encuadre es un `<video>` nuevo, no un tween.** Cada uno es una caja sobredimensionada
con desborde negativo que el stage recorta; el salto entre dos es un **corte duro**.

Escala de zoom: **1.00 · 1.05 · 1.09 · 1.12 · 1.15**. El 1.15 es escaso.

### Zona segura

En REEL, **el 20 % inferior queda libre**: ahí pinta la plataforma su interfaz. El espacio
vacío bajo el subtítulo no es un descuido.

---

## 5. Captions

**Bloques de 3–6 palabras con UNA sola keyword resaltada.**

Resaltar todas las palabras convierte el subtítulo en un metrónomo y el ojo deja de leer.
Resaltar una —una cifra, una herramienta, el concepto— la convierte en el titular del
frame. El bloque entra entero y se queda quieto; lo único que se mueve es la keyword, en
el instante exacto en que se pronuncia.

El troceo va por **jerarquía**: frase → cláusula → reparto parejo. Cortar solo por ancho
pega el final de una idea con el principio de la siguiente («…empleados. Cuando…») y el
espectador lee una frase que nadie dijo.

Pieles: `on-dark` (sobre metraje — filete de grafito 7 px con `paint-order: stroke fill`,
que pinta el trazo detrás del relleno y no engorda la letra) · `on-surface` (sobre un
gráfico — sin filete).

### Nunca sobre la cara

La barbilla se **mide** (`measure-face.py`, Haar sobre 48 muestras; p95 = 0.5534 en la
pieza 2, 0.5521 en la 3, 0.5473 en la 4) y se proyecta al encuadre activo.

La **piel** la decide quién ocupa la mayor parte del bloque. La **altura** no: manda el
más bajo de todos los que el bloque toca, aunque solo los toque un instante. Un bloque que
se come 0.2 s del final de un takeover heredaba la altura de la cara —más arriba— y esos
0.2 s el subtítulo se sentaba encima del gráfico. Bajarlo no le quita nada al frame.

### La zona segura la calcula el generador

No basta con que el subtítulo **empiece** antes de y1536: la cuenta necesita el número de
líneas. `build-composition.py` mide el ancho, deduce si son una o dos líneas y baja el
tope a `0.80·H − líneas·1.14·tamaño`. Sin eso, un bloque de dos líneas colocado sobre un
gráfico (top 1430) metía la segunda línea 46 px dentro de la interfaz de la plataforma.
Verificado sobre el MP4: la tinta más baja fuera de plano lleno queda en y1533 (pieza 3) y
y1502 (pieza 4).

---

## 6. Motion

- **El movimiento actúa, no respira.** Prohibido el wobble ocioso. Quietud antes del
  clímax.
- **Si un elemento representa algo que se dice, su tiempo sale del transcript.**
- Todo contenedor entra por **opacidad**; lo que se mueve es el contenido de dentro. El
  recorrido y la escala de entrada son pequeños.

### Sin muelles

`back.out()` rebota como un resorte: es lenguaje de dibujo animado y choca con una pieza
de producto. **Ninguna entrada lo usa.**

| Gesto | Ease | Entra desde |
| --- | --- | --- |
| `punch` (titular) | `expo.out` | escala 1.045, y −8 |
| `stamp` (sello, cifra) | `power3.out` | escala 1.10 |
| `rise-in` (panel grande) | `power3.out` | y +26, escala 0.985 |
| `chip-in` (pastilla, nodo) | `power2.out` | escala 0.94, y +8 |
| `slide-in` (kicker, HUD) | `power2.out` | y +14 |
| `box-in` (caja delimitadora) | `power3.out` | escala 1.06 |

### Transiciones

**Cortes duros, zoom cuts y push.** Nada de paquetes genéricos.

### La curva de intensidad

Hook (0–3 s) lo más agresivo · cuerpo con descansos y picos · quietud antes del clímax ·
CTA simplificado a un solo elemento.

---

## 7. Sistema de visuales

**La técnica varía según qué es esa cosa.** Repetir siempre la misma es lo que hace que un
video parezca una plantilla.

| Momento | Técnica |
| --- | --- |
| Interfaz genérica | **mockup HTML** (`mockups.py`) |
| **Producto propio** | **grabación real** dirigida (`screen-tour.py` + `screen_overlay`) |
| Un dato, un concepto | cifra o palabra protagonista |
| Atmósfera | imagen generada con Kie AI, solo si aporta |

Regla de oro: **si se habla de un proyecto real, prioriza sus grabaciones por encima de
cualquier stock o generación.**

### Grabaciones de pantalla

`screen-tour.py` convierte una captura cruda en un recorrido: recorta el chrome del
navegador ajeno y el dock, encuadra el punto de interés por tramo, empuja la cámara y
corta en duro al ritmo del habla.

Encima, en coordenadas del lienzo: `clicks` (cursor sobredimensionado + anillo + etiqueta)
y `boxes` (caja delimitadora con oscurecido alrededor, que **dirige la mirada** al punto
exacto; sin ella el ojo barre la pantalla entera y se pierde la frase).

El clip se coloca con `rect` como **tarjeta**, no a sangre. Alrededor va un **panel
elevado (hairline + sombra), no un navegador**: la barra de `chrome` cuesta 74 px de alto
que salen directamente del tamaño de la interfaz, y en 9:16 eso es lo único que el
espectador necesita ver. `chrome` se reserva para cuando la URL sea el mensaje.

**Que se vea el flujo no se arregla con el contenedor, se arregla en el recorte.** La
salida del recorrido va **cuadrada** (1.2195), no apaisada: un origen apaisado dentro de un
lienzo vertical solo cabe grande si el recorte deja de ser apaisado. Medido — en la pieza 2
el recorte 1350×854 acababa a **0.73×** dentro del `rect` (la interfaz se veía más pequeña
que en el monitor original); en las piezas 3 y 4, recortes de 500–780 px en un panel de
1000×820 van a **1.28–2.0×**.

⚠ **Las barras negras.** Una grabación casi nunca llena el archivo: las tres tienen
contenido solo en x 96..1822 de 1920. Un recorte que las pise mete una franja negra en
mitad del panel y «cabe» en el archivo perfectamente. `screen-tour.py` lo mide con
`cropdetect` y falla antes de renderizar.

⚠ **Lo que no es el producto.** Una grabación de desarrollo trae dos cosas que la delatan
y que solo se ven unos segundos, así que no aparecen en el frame que uno mira al elegir el
recorte: el **indicador de dev** del framework (pastilla negra abajo a la izquierda) y un
**toast de error de validación**, que en un video de venta se lee como que el producto
falla. Se declaran una vez en `exclude` del spec —con su ventana de tiempo y su rect— y
`screen-tour.py` falla antes de renderizar si un tramo las pisa. Medidas: en la pieza 3 el
toast vive en 32.90–37.00; el indicador de dev, en seis ventanas repartidas.

⚠ **Las coordenadas de `clicks` y `boxes` NO se estiman.** Van en píxeles del lienzo y
entre el frame que uno mira y el lienzo hay tres transformaciones encadenadas. Estimándolas
a ojo, la caja de los métodos de pago cayó **300 px por debajo**, sobre otras filas. Dos
formas de acertar: `scripts/tour-map.py`, que hace la cuenta y además dice a qué tramo
pertenece el punto, o —más directo— renderizar el tramo al **tamaño exacto del panel**
(`-vf scale=1000:820`) y leer las coordenadas ahí, que ya son las del lienzo menos el
origen del `rect`.

### Librería de mockups

`app_switch` · `connection_map` · `stat_grid` · `chip_grid` · `rate_mismatch` ·
`keyword_hero` · `flow_steps` · `comment_ui` · `screen_panel` · `browser_frame` · `hud`.

`stat_grid` y `chip_grid` se confunden fácil y no son intercambiables: tres cifras grandes
contestan **cuánto**, una fila de etiquetas que se amontona contesta **cuántas cosas a la
vez**. Meter cinco métodos de pago en un `stat_grid` obliga a inventar cifras que nadie
dijo.

`flow_steps` acepta `tone: "fail"` para una cadena que se rompe. Ahí **solo el último paso
va en rojo** —teñirlos todos la convierte en un error de sistema en vez de en el precio de
haber llegado hasta ahí— y **los intermedios se quedan sin marca**: un ✓ verde junto a «No
hay stock» se lee justo al revés de lo que significa.

⚠ **Un mockup corto centrado deja medio frame vacío bajo el PiP.** `mock_pad_top` solo
empuja hacia abajo; el contrapeso es `mock_pad_bottom`. El bloque tiene que quedar centrado
hacia **y 820–880**, no en el centro del lienzo.

**Nada entra antes de su palabra.** Tres logos visibles desde el primer frame parecen más
limpios, pero el espectador lee «Excel» dos segundos antes de que se diga y, cuando llega
la palabra, ya no pasa nada en pantalla.

**El HUD da contexto, no repite** un dato que ya está dentro del gráfico.

### Kie AI — son dos rutas distintas

⚠ Los nombres de modelo de video **no existen** en la API de jobs (`veo3_fast` allí da
422), y la respuesta de Veo **no trae `state`**, trae `successFlag`. Sondear por `state`
cuelga la tarea hasta el timeout aunque haya terminado — y los créditos ya se gastaron.
Si pasa: `scripts/kie.py fetch --task <id>` baja el resultado sin volver a pagar.

Caché y ledger en `assets/gen/ledger.json`: el pipeline se puede volver a correr entero
sin pagar dos veces.

---

## 8. Color: si el metraje es HDR

**Lo menos obvio del flujo.** El iPhone puede grabar en **HLG / BT.2020**. Hay tres
caminos y dos son trampas:

| Camino | Metraje | Gráficos |
| --- | --- | --- |
| Render HDR (por defecto) | ✅ | ❌ los colores de marca se desvían |
| `--sdr` a secas | ❌ **lavado** | ✅ |
| `--sdr` + LUT calibrado | ✅ | ✅ |

**`--sdr` solo REETIQUETA, no convierte**: deja los píxeles con la curva HLG pero marca el
archivo bt709, así que el reproductor no aplica la curva y todo se ve opaco.

```bash
scripts/calibrate-hlg.py out/1-rough.mp4 5.5
scripts/make-hlg-lut.py assets/hlg-to-709.cube
ffmpeg -i out/1-rough.mp4 \
  -vf "lut3d=assets/hlg-to-709.cube,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv" \
  -c:v libx264 -crf 18 -g 30 -keyint_min 30 -pix_fmt yuv420p \
  -movflags +faststart -c:a aac videos/1/public/input-video.mp4
```

`setparams` es **obligatorio**: `lut3d` propaga las etiquetas de color del frame de
entrada, así que sin él el archivo sigue marcado como HLG. Los flags `-color_trc` /
`-color_primaries` por sí solos **no bastan**.

El objetivo del LUT **no es estilizar sino reproducir el original**; se recalibra por
pieza. Para la pieza 1: gamma 1.65, gain 0.85, lift +0.06, sat 1.20, error 6.6 (la
conversión física pura daba 53).

Enfoques descartados, no repetirlos: conversión física pura (sobresatura y aplasta los
negros) y curvas 1D por canal (manchas amarillas y azules en la piel).

**La fuente de la pieza 2 es SDR bt709**, así que ese tramo se salta. `--sdr` sigue siendo
lo correcto.

---

## 9. Trampas del renderer

Casi todas comparten la misma firma: **el navegador se ve bien y el MP4 sale mal.**

1. **El fondo CSS de la página se descarta.** `background` en `html`/`body`/`#stage` no se
   pinta. El suelo tiene que ser un elemento del DOM (`#ground`).
2. **El rect del `<video>` se resuelve una sola vez al cargar.** Animar `width`/`height`
   no reescala, solo recorta. Por eso un punch-in es un **elemento nuevo**.
3. **Media anidada en un elemento temporizado se congela.** Los `<video>`/`<audio>` van
   sueltos en el stage; el chrome se dibuja **alrededor**.
4. **Un `<audio>` sin `id` se renderiza en silencio.**
5. **La pista ordena el TIEMPO; el z-index ordena el APILADO.** Es la trampa más cara de
   este sistema. Como los `<video>` se emiten antes que los hosts, el PiP del creador
   quedaba **debajo** de cualquier mockup opaco — y no se notaba, porque sobre la
   grabación de producto, cuyo host es transparente, se veía perfectamente.
   Apilado: `0 suelo · 1 metraje · 2 media · 3 backdrop · 4 tarjetas · 5 takeover ·
   6 PiP · 7 subtítulos`.
6. **Un `off` que empieza a la vez que el takeover deja el frame vacío.** Durante el
   fundido no hay nada debajo y el frame cae al suelo: 0.15–0.25 s que se leen como un
   fallo. El encuadre se queda hasta `start + fade_in`, y el siguiente entra en
   `end − fade_out`. **Ya no hay que recordarlo**: `check_no_black()` lo comprueba en
   `build-composition.py` y falla dando el número exacto que falta. Cazó cuatro huecos en
   la pieza 3 y uno en la 4 antes de renderizar. Dos casos que enseñó:
   · entre **dos takeovers seguidos** el fundido cruzado también abre hueco — el `off` no
     empieza en el primero, sino cuando el segundo ya está del todo puesto (el `off` es
     solo un ahorro de decodificación, no cuesta nada retrasarlo);
   · **el último visual no se funde a la salida**: el CTA tiene que estar puesto en el
     último frame, que es el que se congela cuando el reel vuelve a empezar.
7. **Un trazo SVG se prepara en t=0, no al dibujarlo.** El `stroke-dasharray` montado en
   el mismo instante que el tween deja la línea entera desde el primer frame.
8. **GSAP**: `left`/`top` tartamudean → usar `x`/`y`. Toda salida necesita `tl.set` de
   kill duro. Nada de `translate(-50%,-50%)` en algo que GSAP anime — centrar con flex.
   Dos tweens sobre la misma propiedad necesitan `overwrite: "auto"`.

### CLI

- Un `public/index.motion.json` de una composición **anterior** hace fallar `check` con
  `motion_selector_missing`. Reescribirlo o borrarlo.
- `snapshot --at 1.2,7.6,20.5` — lista separada por comas; repetir `--at` no acumula.
- Los checks de **contraste solo corren si hay muestras**: `0/0` no es que pase, es que no
  midió.
- Esperar un render por **el PID concreto**, nunca porque el archivo dejó de cambiar ni
  con `pgrep -f "hyperframes render"`: el propio shell que espera lleva esa cadena en su
  línea de comando, se caza a sí mismo y el bucle no sale nunca.

---

## 10. Estructura del proyecto

```
editor-videos/                      ← el ESTUDIO: una carpeta, muchas piezas
├── CLAUDE.md                       ← bitácora
├── .env                            ← ASSEMBLYAI_API_KEY · KIE_API_KEY (chmod 600)
├── .claude/skills/
│   └── video-tech-premium/         ← LA SKILL: el estilo y el flujo completo
│       ├── SKILL.md
│       ├── references/             design · plan-schema · visuals · motion
│       │                           sound · color · gotchas
│       ├── scripts/                tokens · mockups · logos · build-composition
│       │                           screen-tour · tour-map · refine-timings
│       │                           make-music-bed · …
│       └── assets/                 8 fuentes · 19 efectos · GSAP
├── scripts/  →  enlace a los de la skill
│
├── VIDEOS ORIGINALES/<n>/          ← video.MOV · guion.md · pantalla.mov
├── VIDEOS EDITADOS/                ← copias finales para publicar
├── assets/
│   ├── audio/<n>.flac              ├── music/bed-tech.mp3
│   ├── gen/  (+ ledger.json)       ├── logos/
│   ├── face-<n>.json               └── hlg-params.json · hlg-to-709.cube
├── transcripts/<n>.json · cuts/<n>.json · out/<n>-rough.mp4
└── videos/<n>/
    ├── plan.json                   ← LA PIEZA
    ├── screen-tour.json            ← el recorrido de la grabación de pantalla
    ├── screen-tour-b.json          ← un SEGUNDO recorrido, si hace falta (ver abajo)
    ├── output.mp4                  ← ENTREGABLE
    └── public/                     ← index.html + input-video + assets copiados
```

**Dos momentos de la misma grabación separados por un gráfico son dos archivos, no dos
tramos.** El renderer arranca cada `<video>` en 0 (`data-media-start="0"`), así que un
segundo `screen-video` que apunte al mismo mp4 volvería a empezar por el principio. Por eso
la pieza 3 tiene `screen-tour.json` (tasa BCV → métodos → pago mixto) y
`screen-tour-b.json` (el equivalente en dólares), con el `keyword_hero` «USD + VES» en
medio.

**Un solo estudio, muchas piezas.** Lo que se reutiliza y justifica no abrir un proyecto
por video: la calibración de color, el ledger de assets de IA, la cama musical y el `.env`.

`scripts/` es un **enlace**, no una copia: las copias divergentes fueron un problema real.

---

## 11. Comandos y entorno

```bash
npx hyperframes check public     # validar
npx hyperframes preview          # Studio en localhost:3002
npx hyperframes snapshot public --at <s1,s2,s3>
npx hyperframes doctor
```

CLI **0.7.105**.

| Check | Estado |
| --- | --- |
| FFmpeg · Chrome · Node 24 | ✅ |
| **Memoria** | ⚠ Cerrar apps antes de renderizar |
| `zscale` en ffmpeg | ❌ Sin libzimg ni libplacebo → por eso el LUT propio |
| HeyGen (voz/música de catálogo) | ❌ Sin credencial → la música se sintetiza (§13) |
| Docker | ❌ Solo afecta al render containerizado |

Dependencias Python: `pillow`, `fonttools`, `brotli`, `numpy`,
`opencv-python-headless<5` (la 5.x quitó `CascadeClassifier`).

---

## 12. Sonido

Tres capas y una jerarquía que no se negocia: **la voz manda siempre**.

```
voz  pista 10   ·   música  pista 11   ·   efectos  pista 12+
```

### El efecto marca algo que pasa en imagen

No hay relleno ambiental. Si no puedes señalar en el frame qué marca ese efecto, sobra.
Los tiempos son **los mismos beats del transcript que mueven la imagen**.

### El volumen se CALCULA, no se escribe a mano

Hay **27 dB** entre el efecto más caliente (`impact-bass-1`, media −5.0 dB) y el más flojo
(`chime`, −32.4 dB). Puestos a un número parecido, el impacto tapa la voz y los clicks no
existen.

```
v = min( 10^((OBJETIVO_MEDIA − media)/20),   10^((TECHO_PICO − pico)/20),   1.0 )
```

Medido en la pieza 2: los impactos quedan en 0.035–0.053 y el chime en 0.436. La
calibración funcionando.

### La cabecera de la mezcla

**El metraje de iPhone llega pegado al techo**: la grabación de la pieza 2 trae 7690
muestras a 0 dB *antes* de tocarla — viene así de cámara. Sumarle música y efectos satura.

`voice_gain` (por defecto **0.70**) baja la voz para abrir margen, y el generador
**desplaza los mismos dB** los objetivos de efectos y música, así que el balance no cambia:

```
voz ×0.70 → −3.10 dB   ·   efectos −27→−30.1 dB   ·   música −34→−37.1 dB
```

Antes del ajuste: pico 1.62, **13 278 muestras saturadas**. Después: pico −2.5 dB, 64.

### Música

Cama **sintetizada** (`make-music-bed.py`): libre de licencia, offline y reproducible.
La Menor, 100 BPM, Am–F–C–G.

**El diseño importa más que el volumen.** Vive 14 dB bajo la voz, así que no compite por
nivel sino por **espectro**: deja **vacía la banda 300–3000 Hz** donde viven las
consonantes. Medido: sub −6.8 dB · pad −1.1 dB · **hueco de voz −18.1 dB** · aire −33 dB.

⚠ `volumedetect` **loguea a nivel info**.

---

## 13. Estado del proyecto

**Pieza 1 — terminada, con el estilo ANTERIOR.** `videos/1/output.mp4`, REEL 9:16, 38.9 s.
Fuente HEVC HLG 1920×1080 rot 90°. Corte 52.24 → 38.87 s, 79 = 79 palabras verificadas.
Sigue siendo la referencia de la calibración HLG (§8). Re-renderizarla la traería al
estilo nuevo.

**Pieza 2 — terminada con el estilo Tech Premium.** `videos/2/output.mp4`, copia
publicable en `VIDEOS EDITADOS/video-2-erp-reel.mp4`. REEL 9:16, **46.93 s**, 29.8 MB,
H.264 + AAC estéreo, 30 fps. Render en **2–5 min** según la RAM libre.

- Fuente `VIDEOS ORIGINALES/2/video.MOV`: 59.14 s, H.264 **SDR**, 1080×1920, 30 fps.
- Corte 59.14 → 46.93 s (21 % fuera). Las 125 palabras se conservan.
- **15 encuadres** en pantalla de 18 entradas, con punch-ins entre 1.00 y 1.15 y el
  creador en PiP durante los gráficos a pantalla completa.
- **6 visuales**, uno por función del guion:

  | t | Función | Visual | Técnica |
  | --- | --- | --- | --- |
  | 0.42–4.35 | tres sistemas desconectados | tablero con logos y conector roto | `app_switch` + PiP |
  | 19.30–20.34 | «un sistema llamado ERP» | la palabra como gráfico | `keyword_hero` |
  | 20.38–28.05 | los 7 módulos que conecta | mapa dibujado uno a uno | `connection_map` + PiP |
  | 28.05–36.00 | venta → stock → reportes → cliente | **el ERP real** en mockup de navegador | grabación + cursor, clics y cajas |
  | 38.50–40.62 | «una sola fuente de verdad» | la tesis como gráfico | `keyword_hero` |
  | 44.20–fin | «comenta ERP» | el comentario simulado | `comment_ui` |

- **5 tarjetas** flotantes y **33 bloques de subtítulo** (3–5 palabras, 1.4 s de media) con
  **14 keywords** resaltadas.
- El recorrido del ERP se rehízo con `screen-tour.py`: 4 tramos de 8 s clavados a
  venta/stock/reportes/cliente, sin chrome ajeno y sin barras negras.
- **30 efectos** en 3 pistas + cama musical.
- Validación: **0 errores** de estructura, runtime, layout y motion · **44/44 WCAG AA**.
- Verificado **sobre el MP4**: sin negro real (`blackdetect pix_th=0.03` no encuentra
  nada; con el 0.10 por defecto salta el propio suelo grafito, que es luma 12), pico
  −2.5 dB, ganancia de voz recuperada 0.695 frente a 0.70 declarada, música presente en la
  cola (−32.7 dB frente a −51.0 de la fuente) y **26/27 efectos con ataque detectable**
  sobre su propio entorno tras alinear por correlación cruzada (+21.3 ms de priming AAC).
  El subtítulo del CTA quedó en y1192..1327, fuera de la zona segura de la plataforma.

**Pieza 3 — terminada.** `videos/3/output.mp4`, copia en
`VIDEOS EDITADOS/video-3-monedas-reel.mp4`. REEL 9:16, **45.80 s**, 25.9 MB, H.264 + AAC.
Cobrar en USD y VES sin errores · CTA **MONEDA**.

- Fuente `VIDEOS ORIGINALES/3/video.MOV`: 55.68 s, HEVC **SDR bt709**, 1080×1920, rot 0.
- Corte 55.68 → 45.80 s (18 % fuera), 6 cortes. Barbilla p95 = 0.5521.
- **El transcript necesitó dos arreglos** antes de tocar nada (§2): «BCV» venía como «de
  ese B» —lo deletrea— y el tramo 27–35 s estaba desalineado casi 2 s. Re-transcrito
  suelto y empalmado; 113 palabras.
- **6 visuales**, técnica distinta en cada función:

  | t | Función | Visual | Técnica |
  | --- | --- | --- | --- |
  | 0.75–5.70 | la misma venta, dos totales | `rate_mismatch` + alerta | mockup |
  | 6.30–10.80 | cinco formas de cobro a la vez | `chip_grid` que se amontona | mockup |
  | 16.50–17.85 | «el ERP que desarrollé» | `keyword_hero` | mockup |
  | 17.90–28.05 | tasa BCV → métodos → pago mixto | **el ERP real**, 3 tramos | grabación |
  | 28.05–29.55 | «en una misma venta» | `keyword_hero` USD + VES | mockup |
  | 29.55–33.05 | el equivalente en dólares | **el ERP real** | grabación |
  | 42.60–fin | «comenta MONEDA» | `comment_ui` | mockup |

- 14 encuadres, 3 tarjetas, 29 bloques de subtítulo con 16 keywords, 27 efectos.
- Validación **0 errores** · **36/36 WCAG AA**. Verificado sobre el MP4: sin negro real,
  pico −2.0 dB, **0 muestras saturadas**, voz 0.696 frente a 0.700 declarada, música
  presente a −37.9 dB (aislada restando la voz alineada) y 25/26 efectos con ataque
  detectable. El `error` del hook queda +3.7 dB sobre su entorno porque cae justo en
  «perder dinero» y ya está a `volume 1.0`: la voz manda, y es lo correcto.

**Pieza 4 — terminada.** `videos/4/output.mp4`, copia en
`VIDEOS EDITADOS/video-4-inventario-reel.mp4`. REEL 9:16, **44.63 s**, 27.4 MB.
Inventario que avisa antes de quedarte en cero · CTA **STOCK**.

- Fuente `VIDEOS ORIGINALES/4/video.MOV`: 55.87 s, HEVC **SDR bt709**, 1080×1920, rot 0.
- Corte 55.87 → 44.63 s (20 % fuera), 7 cortes. Barbilla p95 = 0.5473. 102 palabras.
- ⚠ **La carpeta 4 venía sin guion** (`guion.md`, 0 bytes). La estructura salió del propio
  transcript: hook 0–6 · problema 6–15 · producto 15–24 · cifras 25–31 · tesis 31–38 ·
  CTA 38–fin. No hizo falta pedir nada: el transcript ES el guion.
- **5 visuales**:

  | t | Función | Visual | Técnica |
  | --- | --- | --- | --- |
  | 0.92–5.85 | pide → no hay → venta perdida | `flow_steps` `tone: fail` | mockup |
  | 15.50–24.20 | stock, ajuste y alerta | **el ERP real**, 3 tramos | grabación |
  | 25.70–31.40 | agotados · valor · SKUs | `stat_grid` con las cifras reales | mockup |
  | 37.55–38.95 | «hacer hoy» | `keyword_hero` | mockup |
  | 38.95–fin | «comenta STOCK» | `comment_ui` | mockup |

- El tramo del medio de la grabación es el hallazgo de esta pieza: el modal **«Ajustar
  inventario» rotula sus tres campos Stock / Reservado / Mínimo** con las mismas tres
  palabras que él dice, y debajo pone la sucursal. No hubo que dibujar ningún gráfico que
  lo explicara.
- 15 encuadres, 4 tarjetas, 28 bloques con 17 keywords, 23 efectos.
- Validación **0 errores** · **39/39 WCAG AA**. Sobre el MP4: sin negro real, pico
  −2.7 dB, **0 muestras saturadas**, voz 0.694, música a −36.0 dB, **22/22 efectos** con
  ataque detectable.

Avisos abiertos que no bloquean: `composition_file_too_large`, `timeline_track_too_dense`,
`pointer_events_none`.

---

## 14. Reglas duras

**Hacer**
- Correr `detect-format.sh` antes de crear el proyecto. El formato se mide.
- Medir la cara, no estimarla.
- **Cuadrar el transcript con el audio antes de cortar** (`refine-timings.py`), y
  re-transcribir suelto el tramo que salga con la alineación rota.
- Cada beat clavado a su palabra, sacado del transcript remapeado.
- **Recortar la grabación hasta que el flujo se lea**: salida cuadrada, sin navegador
  alrededor, y las coordenadas de clicks y cajas medidas, no estimadas.
- Un visual por función, con la técnica variada.
- Cambiar de imagen cada 1–2.5 s. El creador es el hilo conductor.
- Renderizar con `--sdr` (y con el LUT calibrado si la fuente es HLG).
- Verificar el resultado **sobre el MP4**, extrayendo frames y midiendo el audio.
- Dejar libre el 20 % inferior del lienzo en REEL.

**No hacer**
- Estilizar el metraje. El color reproduce el original. El usuario lo nota.
- Tapar la cara con subtítulos.
- Resaltar todas las palabras del subtítulo.
- Adelantar el guion: un logo no aparece antes de que se nombre.
- Blanco puro, negro puro ni sombras duras.
- Confundir pista con apilado.
- Meter dos clips a la vez en la misma pista.
- `back.out()` en una entrada.
- **Dejar el cursor aparcado** después del último clic: son segundos de un objeto enorme
  que ya no hace nada. `screen_overlay` lo funde solo, 1 s después.
- Poner un navegador alrededor de la grabación por costumbre: cuesta 74 px de interfaz.
- Dar por terminado un render mirando la fecha del archivo.
