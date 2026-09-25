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

**Desde la doctrina de 2026-09-15, todo REEL usa el layout `triband` por defecto** (§4) —
no un modo que se elige pieza a pieza. YOUTUBE no lo lleva: el triband reparte el lienzo en
tres bandas verticales y no tiene sentido en 16:9. `check_triband_default`, en
`build-composition.py`, para la compilación de un REEL sin `layout`; la escotilla para
renunciar a él a sabiendas en una pieza concreta es `"layout": {"mode": "none"}`.

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
| 3 | Planificar cortes | `scripts/plan-cuts.py transcripts/2.json cuts/2.json <dur_real> --audio assets/audio/2.flac` |
| 3b | **Preguntar las animaciones de la banda de arriba** | conversación con el usuario — sin script, ver más abajo |
| 4 | Corte bruto | `scripts/rough-cut.sh <src> cuts/2.json out/2-rough.mp4` |
| 4b | **Auditar respiraciones — no se sigue si falla** | `scripts/audit-breaths.py --project . --piece 2` |
| 5 | Medir la cara | `scripts/measure-face.py out/2-rough.mp4 assets/face-2.json` |
| 6 | Color, solo si es HDR (§8) | `scripts/calibrate-hlg.py` + `scripts/make-hlg-lut.py` |
| 7 | Recorrido de pantalla | `scripts/screen-tour.py videos/2/screen-tour.json --preview` |
| 8 | Música | `scripts/make-music-bed.py assets/music/bed-tech.mp3 --dur 70` |
| 9 | **Escribir el plan** | `videos/2/plan.json` ← **el trabajo creativo** (piezas 1–9) |
| 9b | **o escribir el EDL y compilarlo** | `videos/10/edl.json` ← el trabajo creativo, anclado a ÍNDICES DE PALABRA · `scripts/edl-compile.py --project . --piece 10` escribe `plan.json` |
| 10 | Componer | `scripts/build-composition.py --project . --piece 2` |
| 11 | Validar | `npx hyperframes check public` |
| 12 | Renderizar | `npx hyperframes render public --skill=talking-head-recut -o output.mp4 --fps 30 --sdr` |

### 3b — preguntar las animaciones, no decidirlas solo

Doctrina de 2026-09-15, a petición del usuario: el triband le da a cada beat una banda de
arriba que hay que llenar con algo, y ese algo dejó de decidirse sobre la marcha mientras
se escribe el plan. Se pregunta ANTES, en el hueco exacto entre saber qué se dice y
construir cualquier cosa — el transcript ya está cortado (paso 3, con `refine-timings` ya
aplicado), pero no existe corte bruto, ni recorrido de pantalla, ni `plan.json`.

Lo que se presenta, por cada beat del guion:

- **Los tiempos**, del transcript ya remapeado a la línea del corte (paso 3, con
  `refine-timings` ya aplicado) — no del transcript crudo, que vive en la línea del fuente.
- **El material de origen disponible** en `VIDEOS ORIGINALES/<n>/`: grabaciones de pantalla,
  capturas, logos. Proponer un mockup para algo que ya está grabado va contra la regla de
  oro de b-roll semántico (§7): si existe la grabación real, ella manda.
- **Una propuesta por beat** de qué ocupa la banda de arriba, para que el usuario confirme o
  cambie — no para montarla directo con la primera idea razonable.

El vocabulario que hace la pregunta respondible: `tool_card` (marca cuando se nombra algo),
`tool_recording` (grabación dirigida con chip de marca), los mockups de la librería
(`keyword_hero`, `stat_grid`, `chip_grid`, `flow_steps`, `comment_ui`, `chat_unanswered`…),
los objetos de `objects.py` (§7), y `tool_lineup` (varias marcas en fila, para un beat que
las recoge todas).

**Dejar la banda vacía NO es una opción.** La banda `top` muestra algo en cualquier segundo
de un tramo `band`, y `check_band_top_covered` falla la compilación si no (§4). Eso cambia
la forma de la pregunta: no es «qué animación quieres aquí», es «qué animación quieres
aquí, sabiendo que algo tiene que haber». Un beat sin material no se queda en blanco — o se
sostiene el visual anterior, o se le inventa uno, y ESA es la decisión del usuario.

Los dos criterios que chocan aquí, y cómo se resuelven:

- **Nada entra antes de su palabra** (§7): la propuesta para un beat no puede adelantar un
  logo ni una cifra que el guion todavía no dijo. El hueco previo a un visual NO se tapa
  adelantándolo.
- **La banda nunca se queda vacía** (§4): ese hueco se tapa **sosteniendo el visual
  anterior** hasta que entra el siguiente. El saliente cubre; el entrante espera su palabra.

El único que no se arregla sosteniendo es el hueco del primer visual, porque no hay nada
delante: ahí se mueve el inicio del tramo `band` para que coincida con su entrada.

**Desde la pieza 10, el paso 9 tiene dos caminos.** El de siempre: escribir `plan.json` a
mano. El nuevo: escribir un `edl.json` que referencia **índices de palabra** del transcript
(no floats copiados a mano) y dejar que `edl-compile.py` derive shots, stages, captions y
SFX — con gates de estilo que fallan antes de escribir nada si `presenter_share`, el ritmo
de cambios o la proporción de transiciones especiales se salen de banda. El paso 10 no
cambia: `build-composition.py` consume el `plan.json` que sea, sin saber de cuál de los dos
caminos vino. Ver `docs/superpowers/plans/2026-09-07-edl-motion-design.md` y
`docs/superpowers/specs/2026-09-07-edl-motion-design-design.md`.

**Desde la pieza 12 el EDL también emite RÓTULOS** (evento `CARD`). Hasta entonces el
camino del EDL escribía `"cards": []` fijo, así que lo único que podía acompañar al
presentador era el subtítulo. Un rótulo no es un stage pequeño: **el stage sustituye la cara
y el rótulo la acompaña**, y hay frases —«escalar a un humano», dicha por un humano— en las
que esa diferencia ES el argumento. Los dos bordes salen de una palabra (`atWord` /
`untilWord`, que usa el FINAL de la suya), así que un borde corregido por `refine-timings`
los mueve solos.

⚠ **Un `CARD` dentro de un segmento de stage falla, y no es gusto: es apilado.** Las
tarjetas van en la pista 4 y el takeover en la 5 (gotcha #5), así que el rótulo se
renderizaría debajo de un fondo opaco. Y **no basta con mirar el segmento en que se
declara**: el rótulo se extiende hasta `untilWord` y ese borde puede caer ya dentro del
stage siguiente. Las dos comprobaciones están en `_check_cards`.

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

### Voz no es sonido — `voicing.py`

⚠ **Se entregó un reel con una inspiración de 900 ms a −10.4 dB dentro del
hook.** Entre «decisión.» y «Una», más fuerte que media frase, y la oyó el
usuario. La cadena de errores merece leerse entera porque cada eslabón parecía
razonable:

1. AssemblyAI cerró «decisión.» en 5.595 — **bien**.
2. `refine-timings` vio sonido continuo hasta 6.44 y estiró el borde hasta su
   tope de `MAX_SHIFT` (500 ms), porque medía ENERGÍA.
3. Al revisarlo se leyó la envolvente —que sube sin un frame de silencio— y se
   concluyó que era la sílaba tónica de la palabra. **Se alargó a mano a 6.440.**
4. Con la respiración YA DENTRO del span de la palabra, ningún detector
   posterior podía verla: el censo de sonido fuera de palabra daba cero.

**La envolvente no distingue una vocal sostenida de una respiración de
proximidad**, porque el micro cercano le sube los graves. Lo que sí las
distingue es si hay TONO, y ahora vive en `scripts/voicing.py`:

| | armonicidad | energía >400 Hz |
| --- | --- | --- |
| vocal | 0.35–0.69 | 0.11–0.93 |
| fricativa (la «s») | 0.24 | 0.90 |
| **respiración** | **0.06–0.25** | **0.01–0.11** |

Hacen falta las DOS medidas: la armonicidad sola marcaría la «s» como
respiración —y cortaría el final de cada plural—; la energía alta sola daría
por voz cualquier soplido. **Un frame es voz si tiene tono O aire alto.**

Tres cosas cambiaron con eso:

- **`refine-timings` estira los bordes solo sobre voz.** En la pieza 14 pasó de
  mover 9 bordes a mover 6, y los tres que dejó de mover eran los tres que se
  comían una respiración. Su aviso de isla también dejó de llamarlas
  «vocalización» —lo eran por reparto grave/agudo— y ahora dice «respiración».
- **`plan-cuts --audio` coloca la pausa que queda sobre SILENCIO.** No cambia
  cuánta pausa deja, cambia de qué está hecha: cada lado se recorta hasta donde
  empieza la respiración. Sin `--audio` se comporta como siempre, para que las
  piezas anteriores se vuelvan a cortar igual.
- **Los márgenes de cabeza y cola también.** La última inspiración de la toma
  entraba en el reel por `TAIL_PAD`.
- **Y una red que lo comprueba: `audit-breaths.py` (paso 4b).** Quitar la respiración es
  del paso 3; comprobar que no quedó ninguna es de este, y falla con código 1 para que
  un reel con una inspiración dentro no llegue a renderizarse por descuido. Pasa en las
  piezas 11, 12 y 14; **falla en la 13**, señalando 6.140–6.215 s a −15.1 dB.

⚠ **Auditar un corte exige el umbral de la FUENTE.** El suelo sale del
percentil 10 de la propia envolvente y un corte ya no contiene los silencios de
los que estimarlo: medido, «sube» de −52.0 a −41.9 dB y el umbral con él, de
−42.0 a −31.9. Con el umbral equivocado una ráfaga de −11.7 dB se quedaba en
75 ms y caía por debajo de `min_dur`.

⚠ **Y una isla CORTA pero FUERTE cuenta igual.** Fue esa regla —no el faldón—
la que movió el corte de «ingresos.» de 33.18 a 33.07: la respiración arranca
con ráfagas de 35–55 ms a −13 dB que `min_dur` descartaba una por una.

⚠ **El detector es ciego al transcript a propósito**, así que también caza las
plosivas y las nasales apagándose DENTRO de una palabra. Quien lo use filtra
por spans de palabra: una ráfaga de 25 ms sobre el ataque de «Una» dejaría la
pausa de ese lado en cero.

⚠ **Auditar el MP4 mezclado da falsos positivos: la cama musical no tiene tono.**
La auditoría se hace sobre `out/<n>-rough.mp4`, que es voz sola.

⚠ **Y no se prueba con ruido sintético.** Un ruido gaussiano limitado en banda
es cuasi-periódico y su armonicidad se queda en 0.27–0.44, pegada al umbral.
La clasificación se prueba contra el audio real de la pieza; lo sintético solo
vale para lo que no depende de modelar una respiración.

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

### El layout `triband`

**Desde la doctrina de 2026-09-15, es el layout por defecto de TODOS los reels de este
proyecto** (§1) — ya no un modo que una pieza elige aparte. `check_triband_default`, en
`build-composition.py`, para la compilación de cualquier pieza REEL sin bloque `layout`; no
corre en YOUTUBE, porque el triband reparte el lienzo en tres bandas verticales y en 16:9
no hay banda de arriba que llenar. La escotilla para renunciar a él a sabiendas en una
pieza REEL concreta es `"layout": {"mode": "none"}` — el gate la nombra en su mensaje de
error, porque una salida sin documentar es una salida que nadie usa y un gate que alguien
acaba comentando.

Un quinto `kind`, junto a `full` · `split` · `pip` · `off`: **`band`**. En vez de que el
metraje ocupe el lienzo entero o una esquina, lo confina a la franja de ABAJO de tres
bandas que cubren el lienzo de arriba a abajo **sin huecos** (medidas de la pieza 15, REEL,
tras la Mejora 1 — la división pasó a la MITAD exacta del lienzo; antes era `top` [0,820] ·
`text` [820,1120] · `speaker` [1120,1920], con el hablante en menos de la mitad de abajo):

```
top      y    0– 660   card de logo, grabación de producto — lo que se está explicando
text     y  660– 960   el subtítulo (la excepción de §5)
speaker  y  960–1920   el hablante, SIEMPRE visible detrás del takeover — la mitad de abajo
```

La geometría se declara **una sola vez**, en el bloque `layout` del plan
(`layout.mode: "triband"`, `layout.bands`) — `triband_panels()` la lee de ahí para las tres
bandas, y el validador falla si no cubren `0..H` contiguas o si falta alguna. Un segmento la
activa con `camera: "BAND"` en el EDL (o `kind: "band"` a mano en el plan, para quien no pase
por el compilador). `BAND` no lleva escalera de zoom a propósito: el rect de la banda ya
recorta fuerte, y una escalera encima dejaría la cara irreconocible — el reencuadre vertical
lo hace `object-position` con el `anchor` de siempre.

**Un visual puede declarar `"band": "top"` para vivir DENTRO de una banda en vez de tapar el
lienzo.** Convive con `role`, no lo sustituye: `role` sigue decidiendo la PISTA
(`backdrop`/`takeover`); `band` decide la GEOMETRÍA del host. Antes de esto, una card de logo
a lienzo completo con host opaco tapaba al hablante entero durante las cinco cards de logo
de la pieza 15 — luma máxima **28** medida sobre el MP4, donde debía verse la camiseta
blanca del presentador. Declarar `band` en un visual (o `camera: "BAND"` en un segmento) sin
que el plan traiga `layout` **falla** en vez de caer a un lienzo completo por defecto: la
geometría de las bandas no tiene un valor implícito razonable.

### Que nunca se corte la cara (Mejora 2)

Con `object-fit: cover` en un encuadre `band`, un `anchor` demasiado alto recorta más del
techo de la FUENTE y se lleva la coronilla por delante — el mismo tipo de error que el de
la banda tapada de arriba, sin arreglo en post. `check_face_top_clear` (al lado de
`check_band_speaker_clear` en `build-composition.py`) lo caza en tiempo de compilación:
proyecta `top_frac` —el borde superior de la caja de cara, un campo nuevo de
`measure-face.py`, percentil 5 (el espejo del p95 de la barbilla) sobre las MISMAS
muestras Haar— con la fórmula de `chin_at` para `band`, y si el resultado cae por encima
del techo de la banda `speaker`, `sys.exit()` antes de renderizar. `top_frac` ausente
(una medición de antes de esta mejora) salta el gate limpio, no rompe piezas viejas.

Medido en la pieza 15 (`assets/face-15.json`, 48/48 muestras): borde superior p5 =
**0.2812** del alto de la fuente, barbilla `chin_frac` **0.4531**. Con la banda `speaker`
en [960,1920] y `anchor` **0.38** (bajado desde el 0.5714 por defecto del estilo), el
borde superior de la cara proyectado cae en **y1135**, 175 px por debajo del techo de la
banda — la coronilla entra con aire.

### La banda `top` nunca se queda vacía

Doctrina de 2026-09-15, a petición del usuario: **«en la parte de animaciones siempre se
debe mostrar algo, en cualquier segundo, nunca debe estar el fondo vacío»**. Medido en la
pieza 15 antes de esta regla: durante sus tramos `band`, la banda de arriba se quedaba en
suelo grafito liso 15.0 s de 55.3 s (27 %), en siete huecos.

Choca de frente con «nada entra antes de su palabra» (§7): no se puede adelantar la card
SIGUIENTE para tapar el hueco que la precede, porque el espectador leería el nombre de la
herramienta antes de que se diga. **La resolución es sostener el visual ANTERIOR, nunca
adelantar el siguiente** — se extiende su `end` hasta que entra el que viene; el que viene
sigue esperando su propia palabra. Es la misma idea que `check_no_black` ya aplica al
metraje, aquí aplicada a los visuales de la banda `top`. El hueco de ARRANQUE (nada
delante que sostener) se cierra al revés: moviendo el `at` del propio encuadre `band` para
que coincida con la entrada de la primera card. Y un hueco puede ser un beat de guion sin
visual asignado, no un fallo de sostenido — en la pieza 15, «he juntado estas y varias más
en una guía» no nombra nada nuevo que clavar, así que entra un visual nuevo (`tool_lineup`:
las cinco marcas ya nombradas, juntas en fila) en vez de estirar la grabación anterior.

`check_band_top_covered` (junto a los otros tres gates de arriba) para la compilación si
algún instante de un tramo `band` no tiene ningún visual sobre la banda `top`, listando los
huecos con sus tiempos.

⚠ **Lo que ese gate garantiza es COBERTURA DECLARADA, no luma renderizada**, y conviene no
leer su nombre como más de lo que mide. Medido sobre el MP4 de la pieza 18 y confirmado en
el de la 17: en cada relevo entre dos visuales la banda cae al suelo grafito (luma ~26)
durante **unos 130 ms**, porque el fundido de relevo lo aplica el runtime de HyperFrames a
los elementos `class="clip"` y la composición no lo gobierna.

⚠ **Y en la pieza 19 ese hueco llegó a 663 ms sin que el gate dijera nada** — cinco veces
el suelo del sistema. La causa no es el relevo: es que **el primer elemento del visual
ENTRANTE espera su palabra desde dentro**, y ese retraso se SUMA al fundido en vez de
esconderse dentro de él. Un visual declarado en 7.820 cuya tarjeta entra en 8.347 deja
medio segundo de banda vacía, y `check_band_top_covered` lo da por bueno con razón: el
visual está declarado. Seis de sus trece relevos estaban así (200–663 ms). La regla que
sale de ahí: **el `start` de un visual es la palabra de su PRIMER elemento**, no la del
beat; si el primer elemento no puede entrar antes, se sostiene el visual anterior o se
mueve el límite del segmento (la trampa 6b), nunca se deja el visual entrando en vacío.
Tras aplicarlo, el suelo desnudo (luma ≤32) de la 19 queda en **33–166 ms, o sea 1–5
frames**, medido en los trece relevos.

⚠ **Y el arranque de la pieza es el caso que ningún gate ve.** La 19 abría con la banda en
luma **27 hasta 0.955 s** porque el visual estaba declarado desde 0.000 y su primera
pastilla esperaba a «open». Ahí no hay nada delante que sostener. La salida es la misma que
`agent_editor` usa para su lienzo vacío: entra la ESTRUCTURA —un marco, unos huecos
discontinuos— con la primera palabra, y lo que espera su palabra es el CONTENIDO. El marco
no nombra nada, así que no adelanta el guion, y de paso el frame plantea la pregunta que la
palabra siguiente contesta. No es el problema que esta
doctrina vino a resolver —aquel eran **15.0 s de 55.3 en siete huecos**, beats enteros sin
material— y a tres o cuatro frames se lee como el CORTE DURO que pide §6. Queda anotado en
`tests/test_band_top_alcance.py`, con un test que obliga a actualizar esta nota si alguien
le añade al gate una medición de luma. Detalle completo —incluida la trampa de mirar solo `band=="top"` y
dejar fuera las grabaciones, que se posicionan con `rect`— en `references/triband.md`.

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
líneas. `caption_metrics.py` mide el ancho de cada palabra a SU tamaño, **reparte las
palabras en líneas como lo hace el navegador** y baja el tope a `0.80·H − líneas·1.14·tamaño`.

⚠ **El número de líneas se reparte, no se divide, y no se topa en dos.** `ancho_total /
ancho_útil` falla por los dos lados: el sobrante de cada línea se pierde y una palabra muy
larga rompe la línea antes de agotar el ancho. Medido en la pieza 11 — «PACIENTES
AUTOMÁTICAMENTE POR WHATSAPP» suma exactamente 2.00 veces el ancho útil, o sea dos líneas
por división, y el navegador lo envuelve a **tres**. El cálculo viejo topaba en dos, así
que descontaba una línea de menos y la tercera entraba **58 px** dentro de la interfaz de
la plataforma. Cazó dos bloques de la misma pieza.

Y la caja de línea se mide con el tamaño de la **keyword**, no con el base: usando
`CAPTION_SIZE` a secas, un bloque de dos líneas sobre un gráfico (top 1430) metía la
segunda línea 46 px dentro de la interfaz.

Verificado sobre el MP4: la tinta más baja fuera de plano lleno queda en y1533 (pieza 3),
y1502 (pieza 4), y1518 (pieza 11) y **y1531 (pieza 12)**. El 1531 no es un descuido: es
`floor_top` haciendo su trabajo en un bloque de dos líneas sin keyword (1536 − 2·75), o sea
el tope exacto que calcula el generador. Cuando el margen sale de 5 px, la cuenta está
apretando bien.

### La excepción `triband`

Se llama «excepción» por el mecanismo de anclaje, no por lo rara que es: desde que el
triband es el layout por defecto de todo REEL (§4), este es el camino que toma la mayoría
de las piezas nuevas, no el caso raro.

En `full` · `split` · `pip` el subtítulo persigue la barbilla porque el metraje está detrás
y puede taparla. En `triband` no: entre el techo de la banda de texto y el techo de la banda
del hablante (§4) **no hay metraje**, es suelo grafito, así que no hay barbilla que
esquivar — perseguirla ahí sería mover el subtítulo sin ningún motivo. Los números de abajo
son los de la pieza 15 tras la Mejora 1 (bandas a la mitad: `text` [660,960],
`speaker` [960,1920]); antes eran y820/y1120 con el mismo mecanismo.

- **Tope fijo en y684** (`bands.text.top` + 24 px de aire, no la barbilla).
- **Piel `on-surface`, sin filete.** El filete de grafito de 7 px existe para que la letra
  sobreviva encima de metraje que puede ser claro; sobre suelo liso no hace falta, y solo
  engordaría la letra sin razón.
- **Gate en y944** (`bands.speaker.top` − 16 px de margen): el bloque no puede invadir la
  banda del hablante, y si la cuenta lo cruza el compilador **para** en vez de recortar en
  silencio — «trocea el bloque más corto» en el mensaje de error.
- **Máximo dos líneas**, y sale de medir, no de una regla puesta a mano. La cuenta de ancho
  se queda tal cual estaba (conservadora a propósito, ver Mejora 3 más abajo): base
  **66 px**, un tamaño de referencia 66×1.22 = **81**, caja de línea 81×1.14 = **92**. Dos
  líneas = 184 px → la tinta cae en **y868** (684+184), 76 px de margen bajo el gate — el
  mismo margen de siempre, porque el techo y el suelo bajaron los mismos 160 px. Tres
  líneas = 276 px → **y960**, 16 px por encima del gate (944) — el gate lo rechaza antes de
  renderizar.

### El karaoke del triband (Mejora 3)

El resto de la doctrina de arriba —«resalta SOLO la keyword, agrandada y violeta»— **no
aplica dentro de `band`**, a petición del usuario: ahí todas las palabras comparten tamaño
y color, y lo que se mueve es un **fondo violeta con esquinas redondeadas** detrás de la
palabra que suena en el instante exacto en que se pronuncia (su `start` en el transcript
remapeado) — se apaga en cuanto arranca la siguiente, así que nunca hay dos fondos
encendidos a la vez y al terminar el bloque no queda nada pintado. En `full`/`pip` (hook y
tesis) nada cambió.

- **Fuera el agrandado**: si la palabra además crece, el texto salta y se lee peor.
- El fondo bleedea 8 px horizontal / 4 px vertical más allá del texto vía un `inset`
  ABSOLUTO (`.wbg` dentro de `.w.kw`), así que no le añade nada al ancho que mide
  `caption_metrics` — el cálculo de arriba (con la keyword "de referencia" a 1.22x) sigue
  siendo válido para el gate, solo que ahora es más conservador de lo que hace falta en
  vez de exacto: nunca deja pasar un bloque que de verdad desborde.
- El fade de cada palabra se ESCALA a su propia ventana (`min(0.05, ventana×0.35)` de
  entrada, `min(0.08, ventana×0.35)` de salida): con habla rápida, una palabra puede durar
  menos que el fade fijo de 0.05+0.08s, y `hyperframes check` lo cazaba como
  `overlapping_gsap_tweens`.
- **Contraste**: blanco sobre `violet` (el de siempre, `#7C5CFF`) da 4.35:1 — por debajo del
  4.5:1 que pide la doctrina para texto pequeño. El fondo del karaoke usa `violet_dk`
  (`#5B3FD6`, más oscuro): **6.72:1**, medido con `tokens.contrast()`.

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
| `fade-to` (bajar sin apagar) | `power2.inOut` | a la opacidad que se le pase |

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

⚠ **Un tramo largo sobre una página que SCROLLEA no enseña lo que enseñaba el frame con
el que se eligió el recorte.** El recorte es fijo; el contenido, no. En la pieza 16 el
primer montaje eran dos tramos de 2.2 s: el primero arrancaba en la cabecera «Claude
Cowork» y a los 1.9 s ya había pasado de largo, y el segundo terminaba en el selector de
cuenta de Google del final de la grabación —fuera de mensaje, y con datos de una cuenta
ajena en pantalla—. El remedio son **tramos cortos (1.3–1.6 s), cada uno verificado en su
frame de ENTRADA y en el de SALIDA**, no solo en el que se usó para elegirlo. Es la
hermana de la lección de Kokonut UI en la pieza 15: allí el metraje útil se acababa, aquí
se mueve.

⚠ **La cabecera de `tool_recording` es OPACA desde la pieza 16.** Nació con
`rgba(11,12,16,.72)`, que sobre las grabaciones oscuras de la 15 se leía como un cristal
elegante; sobre documentación con fondo BLANCO el texto de la página se transparentaba por
detrás del chip y del nombre, dos textos superpuestos. La legibilidad de esa barra no puede
depender de lo que haya debajo, y el alto de 84 px se paga igual. Blanco sobre `surface`,
17.73:1.

⚠ **Las coordenadas de `clicks` y `boxes` NO se estiman.** Van en píxeles del lienzo y
entre el frame que uno mira y el lienzo hay tres transformaciones encadenadas. Estimándolas
a ojo, la caja de los métodos de pago cayó **300 px por debajo**, sobre otras filas. Dos
formas de acertar: `scripts/tour-map.py`, que hace la cuenta y además dice a qué tramo
pertenece el punto, o —más directo— renderizar el tramo al **tamaño exacto del panel**
(`-vf scale=1000:820`) y leer las coordenadas ahí, que ya son las del lienzo menos el
origen del `rect`.

### Librería de mockups

`app_switch` · `connection_map` · `stat_grid` · `chip_grid` · `rate_mismatch` ·
`keyword_hero` · `flow_steps` · `comment_ui` · `chat_unanswered` · `screen_panel` ·
`browser_frame` · `hud` · `tool_card` · `tool_recording` · `tool_lineup` (pieza 15)
· `tool_pair` · `claude_prompt` · `layer_stack` (pieza 16)
· `step_grid` · `cv_echo` · `cv_vs_offer` · `offer_stack` · `rewrite_line` ·
`interview_chat` (pieza 17)
· `keyframe_grind` · `agent_editor` · `motion_demo` · `idea_fate` · `idea_veneer`
(pieza 18)
· `agent_swarm` · `desktop_manager` · `split_problem` (pieza 19), más `icons.py` y el
campo `icons_` de `chip_grid` y `flow_steps`
· `video_pipeline` · `money_button` · `video_output` · `tradeoff_bars` (pieza 20).

**Los cuatro de la 20 salen de un guion que ES una cadena** —tema → guion → material →
narración → subtítulos → música → render— y la usa TRES veces: para decir que hacerla
entera cuesta, para enseñar que la herramienta la automatiza, y para señalar la pieza que
NO pone. `video_pipeline` es esa cadena en tres estados (`manual`, `auto`, `gap`), que es
`agent_swarm` de la 19 aplicado a un flujo en vez de a un reparto. ⚠ **La geometría no
cambia entre variantes**: es lo único que hace que el espectador lea «la misma cadena» y
no tres gráficos, y siete celdas de 130 px con 12 de hueco suman los 980 de `BOARD_W`
exactos.

⚠ **Un `info` del linter de layout es fácil de pasar por alto y se ve en el frame.** En la
variante `gap` el hueco de delante le quita ancho a la fila y la casilla baja a 107 px;
«SUBTÍTULOS» a 17 px y tracking .08em ocupa **123** y desbordaba 4.5 px por lado. `check`
lo dio como `text_box_overflow` con **0 errores y 0 avisos**. A 15 px y .03em mide 104.
El tamaño de un rótulo dentro de una rejilla se MIDE contra la casilla más estrecha, no
contra la que se tenía delante al escribirlo.

`money_button` contesta en MECÁNICA lo que el guion pregunta en palabras: el cursor pulsa y
el corte duro deja la bandeja vacía. ⚠ **La bandeja está dibujada desde el primer frame.**
Si apareciera con el «No», el frame diría «y entonces salió una bandeja»; lo que dice la
frase es que siempre estuvo vacía y pulsar no la llena. Y **nada se tiñe de rojo**: el
botón funciona perfectamente, lo que no existe es lo que se esperaba que saliera.

`video_output` es la máquina ya montada escupiendo vídeos, y lo que lo vuelve incómodo es
el RITMO, no el dato — el mecanismo de `keyframe_grind`. ⚠ **El cero no va en rojo ni lleva
✕**: no es un error. Sus dos fichas de entrada llevan el contenido como barra
DISCONTINUA porque lo que las descalifica no es lo que dicen, es que da igual lo que digan.

`tradeoff_bars` son dos magnitudes y lo que le pasa a cada una. ⚠ **La barra que no cambia
NO recibe ni un tween** (la lección de `idea_veneer`): si se encogiera un poco o se tiñera,
el frame diría «y a esta también le pasó algo».

⚠ **Un `else` sin gate renderiza en silencio.** `video_pipeline` nació con
`if variant == "manual": … else: …`, así que una variante mal escrita en el plan caía al
segundo brazo y dibujaba una cadena VACÍA sin que nada fallara. Lo encontró el test del
camino de fallo, no la compilación — y es el mismo modo de error que §14 persigue en todo
lo demás.

**Los tres de la 19 salen de una frase del usuario, no de un beat del guion**: «me gusta
que las animaciones también lleven iconos y así, no solo textos y recuadros». La librería
estaba hecha casi entera de pastillas, tarjetas y titulares —que es lo correcto para
ENUNCIAR y demasiado plano para una enumeración de especialidades, donde cada una tiene
una forma reconocible antes de leerse—. Nace `scripts/icons.py`: 16 glifos de línea en un
lienzo de 24×24 y trazo 1.8, todos en `currentColor`.

⚠ **Cinco de los dieciséis no sobrevivieron a 40 px, y eso solo lo dijo el frame.** La
multitud dibujada con arcos finos salía como una mancha, el engranaje de ocho marcas
sueltas se leía como un **sol**, el tablero de estrategia como un borrón, el martillo como
un alfiler y la maraña como una rayita. Un icono no es correcto porque el `path` lo sea:
lo es cuando se reconoce al tamaño en que se va a ver. Es la misma regla que §14 aplica a
las animaciones, aquí a 24 píxeles de SVG.

`agent_swarm` es **el mismo tablero de agentes en cuatro estados** —`fanout` (el repo, la
marca y la rejilla llenándose), `solo` (uno y todo lo que se le echa encima), `roster` (los
146, y la mayoría bajando) y `team` (tres, con su icono)— porque el guion hace ese
recorrido y dibujarlo con cuatro componentes rompería la rima. Es `idea_fate` llevado a una
enumeración. ⚠ **Los 143 que sobran BAJAN de intensidad, no se apagan**: a opacidad 0 el
frame diría que dejaron de existir y la frase dice que siguen ahí sin usarse. Y son **un
solo tween** (`fade-to`, el gesto nuevo, sobre un selector que casa con los 143), no 143
decisiones editoriales — la «coreografía interna» de la pieza 12. ⚠ **A 0.18 el punto se
confunde con la retícula del suelo** y la frase pasa de «no los necesitas todos» a «solo
hay tres»: 0.26.

⚠ **Las medidas del `roster` salen de que la banda `top` mide 660 px.** Con puntos de 52 y
hueco de 12, los 146 ocupan 11 filas de 64 = 704 px y el CONTADOR quedaba empujado por
encima de y0: sobre el frame se veía una rejilla sin cifra, o sea el dato del beat, fuera
de cuadro. A 40 px con hueco de 10 caben 18 por fila y el bloque entero suma 586.

`desktop_manager` existe porque **la grabación no la tiene**: la web de Agency Agents
resuelve la instalación con una línea de terminal, o sea lo contrario de «una aplicación de
escritorio». Mismo caso que `agent_editor` en la 18. Lo que la hace de ESCRITORIO y no un
navegador es el semáforo y la ausencia de barra de direcciones — `browser_chrome` alrededor
diría «esto es una web», que es la frase anterior del guion.

`split_problem` encadena las dos mitades de la tesis tachando la primera en su sitio (el
mecanismo de `rewrite_line`) y repartiendo la segunda por bajantes dibujadas (el de
`layer_stack`). ⚠ **El parámetro se llama `specialists` y no `parts`**: el remapeo de
`absolute_times` trata `parts` como la lista de DICTS de `rewrite_line` y le resta el
inicio a `pt["at"]`, así que una lista de tuplas con ese nombre revienta la compilación con
un `TypeError`. Dos componentes no pueden compartir el nombre de un campo que el compilador
interpreta.

⚠ **Los selectores que devuelve un mockup son RELATIVOS** — `build_visuals` les antepone
`.viz[data-viz-id="…"]`. Escribirlos ya prefijados los duplica, GSAP no encuentra el
destino y `check` lo reporta como `console_warning` con **0 errores**: el gesto
sencillamente no ocurre. Misma firma que el tachado de `rewrite_line` en la 17. Costó los
cuatro tweens del roster —ni entraban los 146 puntos ni bajaban los 143— y no se vio en
ningún frame porque el frame que se miró era anterior al tween.

**Los cinco de la 18 salen de un guion que habla de ANIMACIÓN**, y eso obliga a que el
gráfico haga lo que enuncia en vez de nombrarlo. `motion_demo` es el caso puro: sus cuatro
variantes (`text`, `chart`, `captions`, `audio`) son los cuatro ejemplos que el guion
recita, hechos. El de captions usa **el mismo mecanismo del karaoke del triband** (§5) — el
ejemplo de captions de la pieza son sus propios captions, que es la lectura más corta que
había. Una quinta variante, `recap`, cierra la enumeración: las cuatro capacidades
pequeñas y quietas, más un hueco discontinuo que ninguna llena, y que solo rellena
«criterio».

`keyframe_grind` dibuja un precio, no un objeto: arriba un vídeo que no hace NADA y abajo
los rombos cayendo **de uno en uno** con el contador subiendo. Un montón de keyframes ya
puestos diría «hay muchos»; el RITMO dice «esto lo pone alguien uno a uno», que es la frase
del hook. ⚠ Y el escenario de arriba es lo único de la pieza que no recibe ningún tween
después de entrar: cualquier gesto ahí contradiría el rótulo SIN MOTION que lleva pegado.

`agent_editor` es un editor con un chat debajo, y existe porque **la grabación no lo
tenía**: `hyperframes.mov` es la WEB del producto, no su Studio. La regla de oro manda usar
la grabación real *cuando existe*; para ese beat no existía. ⚠ **Un lienzo vacío no puede
ser un rectángulo negro.** El primer montaje dejaba 980×244 de negro durante los cuatro
segundos del tecleo y el frame de t=12 se leía como el panel roto que `knowledge-base`
documenta con `reveal`. Lo arregla lo mismo que enseña un editor de verdad sin nada puesto:
el ÁREA de trabajo dibujada —marco discontinuo, marcas de esquina, cruz de centro y la
pastilla de resolución—. Son CHROME, así que están desde el primer frame sin adelantar
nada del guion.

`idea_fate` es **la misma idea en dos estados**, no dos ideas: una instancia apagada con
sus dos salidas tachadas y otra viva, con un CORTE DURO entre ellas — la rima visual de la
pieza 12 aplicada a un estado, y el contraste se lee porque el corte deja ver qué cambió
(el mecanismo de `chat_unanswered`). Las salidas van apagadas, **no en rojo**: rojo diría
«esto falla» y lo que pasa es que la idea se quedó fuera. Y entra en dos tiempos, con el
nombre esperando su palabra sobre un hueco discontinuo, como `tool_pair` y `step_grid`.

`idea_veneer` dibuja la tesis literal: la tarjeta gris y, ENCIMA, la animación más lucida
de la pieza, que se apaga dejándola intacta. ⚠ **La tarjeta no recibe ni un tween al
apagarse lo de arriba.** Si se encogiera o se tiñera, el frame diría «y entonces pasó
algo»; lo que la frase dice es que no pasó nada.

⚠ **`data-layout-allow-occlusion` NO cubre `data-layout-allow-overlap`.** Son dos avisos
que miden cosas distintas —un panel opaco tapando texto, y dos bloques de texto que se
pisan— y `idea_veneer` necesita los dos. El linter cazó el solape de texto con la oclusión
ya declarada.

⚠ **Una barra que crece no crece con `chip-in`.** `chip-in` escala desde el CENTRO y eso se
lee como una barra que aparece, no como una que crece. `rise-bar` es el gesto: escala en Y
desde el borde de abajo, transform y nunca `height`, que sería reflow (§6). Y cuando una
barra recibe VARIOS `fromTo` —los tres golpes de la onda de `audio`— necesita una base
declarada (`set-hidden` en t=0): GSAP aplica los valores `from` al AUTORARLOS, así que sin
ella el reposo lo decide cuál se escribió el último, que es un orden y no una decisión.

**Los seis de la 17 salen de un guion que enumera un MÉTODO**, que es una forma
que la librería no sabía dibujar. `flow_steps` es la que más se le parece y no
sirve: encadena pasos con flechas y los marca ✓/✕, o sea contesta «qué dispara
qué», y cuatro pasos de un método no se disparan entre sí. Y sobre todo
`flow_steps` **no tiene estado intermedio** —sus pasos existen o no existen— y
aquí hacía falta que EXISTAN VACÍOS y se llenen treinta segundos después.

`step_grid` es esa rejilla, y su hallazgo es de proceso más que de dibujo:
resuelve de frente el choque entre lo que pidió el usuario («muestra primero los
4 pasos») y «nada entra antes de su palabra». La estructura entra entera al
anunciarse y cada NOMBRE espera — cuatro huecos numerados, el mismo idioma que
`calendar` usa para la hora sin paciente. Se le preguntó al usuario con las tres
lecturas posibles dibujadas y eligió esta. Vuelve al final con los mismos slots
y los cuatro VERBOS del guion: la rima visual de la pieza 12, aquí sobre el
método.

⚠ **Tres trampas del hueco que se llena, las tres cazadas sobre frames.**
· El relleno **no puede ser una clase estática** sobre la casilla: dársela a
  todo slot con `at` la dibujaba sólida y VACÍA durante los segundos previos,
  que es la lectura de «panel roto» que `knowledge-base` ya documenta con
  `reveal`. Es una capa aparte (`.sgfill`) que se enciende en la misma palabra
  que el texto, y la raya se apaga en ese instante.
· El texto **se queda en el flujo**. Sacarlo con `position:absolute` para que la
  raya no lo empujara lo montó encima del número: **14 errores de
  `content_overlap`** de golpe. Lo que sale del flujo es la RAYA, que es la
  decoración que desaparece.
· Y el span del texto **se emite siempre, vacío si la casilla está pendiente**,
  para que llena y vacía midan lo mismo y la rejilla no dé un salto de layout.
  ⚠ Vacío de verdad: emitirlo con el nombre a opacidad 0 mete «ENTREVISTA» en
  el DOM veintinueve segundos antes de decirse. **«Nada entra antes de su
  palabra» es sobre el DOM, no sobre lo que se ve** — y esto lo cazó un test,
  no un frame.

`claude_prompt` gana `attachment`: la ficha del archivo que se sube al campo. El
beat del guion es «lo subes a una IA **y** escribes», dos acciones en ese orden,
y un adjunto que apareciera con el texto las fundiría en una. Va dentro del campo
y no en la barra porque ahí es donde lo pone la UI real: la barra es para lo que
MODIFICA el envío (el conector), no para su contenido. **El placeholder se apaga
con lo PRIMERO que entra**, sea el adjunto o la línea — si solo lo apagara el
texto, el campo pasaría unos frames con la ficha puesta y «Escribe / para ver
habilidades» debajo, un estado que la UI real nunca tiene.

`cv_echo` son dos documentos con **las mismas barras** y solo las etiquetas
cambiadas, y el `=` que lo dice. El `=` entra el ÚLTIMO: puesto desde el primer
frame contaría el final antes del principio, y lo que hace el beat es dejar que
el espectador lea un antes y un después antes de que el signo le diga que son lo
mismo.

⚠ **Una pastilla en el eje de un par necesita que el HUECO la quepa.** `cv_echo`
y `cv_vs_offer` nacieron con dos tarjetas de 452 y 24 px de aire, y la pastilla
de 76 se montó sobre la tarjeta derecha: «Growth Marketing Manager» se leía
**«3rowth»**. 442 + 96 + 442 = 980 y cabe centrada con 10 px por lado. Compilaba
limpio y pasaba `check`; se vio en el frame.

⚠ **Y un aro que señala una fila se ancla a las FILAS, no a la tarjeta.** Las
marcas de desajuste de `cv_vs_offer` colgaban de la tarjeta con un `top`
calculado a mano sumando la cabecera; al subir la etiqueta a su propia fila, las
tres quedaron **una fila por encima de la suya** — y el `top` era correcto
cuando se escribió. Dentro del contenedor de filas solo dependen del pitch
(28 + 7 + 12 + 13 = 60), que es lo único que la posición debería mirar.

`rewrite_line` teclea la línea pobre, la TACHA en su sitio y baja la buena
debajo: dos tarjetas sueltas lado a lado dirían «hay dos estilos», y la frase es
que uno sustituye al otro. Los tres fragmentos que el guion nombra se realzan
con un `inset` absoluto detrás del texto, el mismo mecanismo del karaoke (§5),
así que encenderlos no le añade ancho a la línea y el texto no salta.

⚠ **El tachado es un trazo, y un trazo se prepara en t=0** (§9, trampa 7, con
otra cara). Nació inyectándose con `caret-off` en el instante de dibujarse, y
GSAP no encontraba el destino al montar el timeline: `target #…-st not found` en
los avisos de runtime, y la raya **no se dibujaba nunca**. Vive en el HTML desde
el primer frame con ancho 0, y fuera de `.rwbefore` — porque `type-word`
reescribe el innerHTML de su destino y se llevaría por delante lo que haya
dentro.

⚠ **Y mide el TEXTO, no la tarjeta.** `grow-x` anima un `width` en píxeles, así
que `width:100%` cruzaría también el vacío detrás de la última palabra y se
leería como una raya suelta. `mockups.text_px()` lo mide con la MISMA woff2
vendorizada que renderiza el navegador —545 px para «Era responsable de las
campañas» a 34/700— en vez de contar letras, que es justo lo que §7 prohíbe con
las coordenadas de `clicks` y `boxes`.

`offer_stack` reparte el beat más largo de la pieza en tres alturas porque el
guion dice tres cosas: las ofertas entran, de ellas suben las competencias que
aparecen SIEMPRE, y al final se dibuja lo que falta. **Lo que falta va con borde
discontinuo, no en rojo**: un chip rojo diría «esta competencia tiene un
problema» y un hueco dice «aquí no hay nada», que es la frase.

`interview_chat` pone en el frame la respuesta floja Y lo que viene después de
ella, porque el paso 4 del guion no es «haz que te pregunte» sino «haz que
REPREGUNTE cuando una respuesta sea débil». **El orden de entrada es el del
guion, no el de la lógica**: la repregunta en «repreguntando» y el sello de
débil dos segundos más tarde, en «débil». Así el frame plantea primero que la IA
insiste y solo al final dice por qué, que es como está escrita la frase.

⚠ **Una barra de contenido en `surface3` sobre `surface` no se ve.** Las barras
del CV y de las ofertas se leían como huecos en el panel en vez de como texto
resumido. `rgba(167,173,187,.30)` —`text2` al 30 %— sí. No es un par WCAG (no es
texto) pero sí es información, y medir contraste no lo cubre: se ve en el frame.

**Los tres de la 16 salen de tres preguntas que la librería no sabía contestar.**

`tool_pair` son DOS marcas y el `+` que las une, cada pieza clavada a su palabra —
`tool_card` clava una sola y `tool_lineup` reúne marcas que ya se dijeron todas. Su
hallazgo es qué hacer con la segunda marca mientras no se ha nombrado: **el hueco se
dibuja**, con borde discontinuo y sin relleno, el mismo idioma que `calendar` usa para la
hora sin paciente. Montar la card ya ancha con la mitad derecha lisa se lee como un panel
roto; hacerla crecer anima `width`, que es reflow. Con el hueco puesto, los 3.6 s de
espera son el beat: el frame plantea la pregunta que la palabra siguiente contesta. Y la
reaparición de la pareja YA formada no pasa por el hueco — con `t_slot == t_right` no se
emite ningún tween sobre él, porque un `chip-in` y un `badge-out` sobre la misma
`opacity` en el mismo instante dependen del orden de evaluación.

`claude_prompt` es el compositor de un asistente escribiéndose línea a línea, cada una en
su palabra. Es un MOCKUP declarado, no la captura redibujada: lleva la tipografía y el
grafito del sistema, y lo que lo ata a la marca es el logo de la cabecera. ⚠ **Una línea
terminada necesita que le quiten el cursor.** `type-word` mete el `<span class="ccaret">`
DENTRO del innerHTML de su destino, así que con cuatro líneas seguidas acabarían cuatro
parpadeando a la vez; `caret-off` —el kind nuevo, la otra mitad de `type-word`— reescribe
la línea sin él en el instante en que arranca la siguiente. La última se queda
parpadeando, que es lo que hace una caja de texto con el foco puesto.

`layer_stack` es una capa por encima de una fila de herramientas, y **entra en dos
tiempos porque ese reparto ES el argumento**: primero la fila sola, en «la oportunidad no
es automatizar Canva» —lo que la frase descarta—, y solo en «capa» baja el panel con sus
bajantes. Las bajantes se dibujan con `draw`, no con un fundido: lo que se afirma es que
la capa ALCANZA cada herramienta. ⚠ **Y el kicker entra con la CAPA, no con la fila**: si
el rótulo dice «UNA CAPA ENCIMA» desde el primer frame, el espectador lee la palabra casi
cinco segundos antes de oírla — «nada entra antes de su palabra» aplica al texto igual
que a un logo, y esto se coló hasta un snapshot.

⚠ **`connection_map` está dibujado para 7 módulos.** Con tres nodos usa las tres
posiciones de arriba, todas las líneas salen del hub hacia arriba y la mitad inferior
del tablero queda vacía. Para tres cosas, `chip_grid`. Y el hub aguanta rótulos muy
cortos: el círculo mide 230 px y «ASISTENTE IA» desbordaba 66 px por lado.

`chat_unanswered` es un mensaje enviado y el hueco debajo; lo que comunica es la
AUSENCIA. Con `reply` abre una burbuja entrante y el mismo componente sirve para el
caso contrario: **dos instancias con corte duro entre ellas** es como se lee un
contraste, porque la rima visual deja ver qué cambió. La marca va en la cabecera y
eso ata el visual a su palabra — no puede entrar antes de que se nombre la app.

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

### Librería de objetos — 15, y crece por demanda

`clock` · `dental-chair` · `phone` · `card-payment` · `instagram` · `bottleneck` (pieza 10)
· `msg-card` · `answer-counter` · `knowledge-base` · `answer-approved` (pieza 12)
· `calendar` · `appointment-timeline` · `confirm-buttons` (pieza 13)
· `spreadsheet` · `kpi-card` (pieza 14).

⚠ **Una REJILLA no es una lista, y `knowledge-base` no sirve de hoja de cálculo.** El
documento de la pieza 12 apila filas y comunica «esto existe suelto»; «una hoja con cientos
de filas» necesita **columnas con separadores**, porque una columna de barras grises se lee
como una lista de pendientes. `spreadsheet` es la rejilla: cabecera de archivo, fila de
columnas y 11 filas de barras **deterministas** (`(i*37 + j*53) % 41` — un golden file no
puede depender de un `random`, y el dato concreto no es el argumento: el VOLUMEN lo es).

⚠ **La cifra enterrada se pone ENCIMA de la barra, no en su lugar.** Si la celda naciera
vacía esperando su palabra, la rejilla tendría un hueco durante los segundos previos y se
leería como un panel roto — la misma trampa que `knowledge-base` ya documenta con `reveal`.
Y es **una celda entre 44**: el beat no es que el dato exista, es que está enterrado.

Los tres interrogantes de `spreadsheet` van en **`currentColor`**, así que los tiñe el tema
del stage (`problem` → alert) en vez de traer un color propio que habría que volver a
justificar en cada uso.

⚠ **La pastilla de acción de `kpi-card` es verde en las cuatro, y no es descuido.** Teñir
«REVISAR» de ámbar y «REPONER» de rojo convertiría la serie en un **semáforo de estados**,
que es otra frase. Lo que se afirma es que CADA indicador produce una decisión, y lo que
esas cuatro palabras tienen en común es que son accionables, no su gravedad. Sobre relleno
`go` va tinta `bg` (11.74:1), nunca blanco (1.66:1) — la regla de `msg-card`.

**La 13 solo necesitó TRES objetos nuevos para cinco funciones**, porque los mensajes de
su secuencia se sirven con `msg-card` de la 12 y su `seal` verde carga la **ventana de
envío** (INMEDIATA · DÍA ANTERIOR · 3 H ANTES) en vez de un estado. Es el nivel `library`
del Resolver haciendo su trabajo: en la 12 ese mismo sello decía AUTOMATIZADO y aquí dice
cuándo sale el mensaje — el componente no cambió una línea.

⚠ **Un hueco solo cuenta el tiempo si algo lo mide.** `appointment-timeline` nació con dos
paradas (Reserva y Cita) y un tramo discontinuo de 244 px en medio, y sobre frames eso
**no se leía como días pasando: se leía como un panel a medio hacer**. Con los días
intermedios puestos como nodos huecos **sin evento**, la misma ausencia se convierte en la
frase: hay un día que existe y no pasó nada en él. Y la discontinua va a `text3`, no a
`LINE_HI`: a alpha .16 se perdía contra el suelo del panel.

⚠ **Una franja vacía se dibuja como HUECO, no como fila en rojo.** En `calendar`, la hora
sin paciente va con borde discontinuo y sin relleno, y es **más alta** que las demás. Una
fila roja con texto se lee como «esta cita tiene un problema»; un hueco se lee como «aquí
no hay nadie», que es la frase. Misma lógica que `chat_unanswered` en la pieza 11: lo que
comunica es la AUSENCIA. El punto verde solo va en las franjas ocupadas.

**Los cuatro de la 12 trajeron tres mecanismos que valen más que los dibujos.**

1. **Coreografía interna.** Los `anims` que devuelve la función de render llegan relativos
   a la ENTRADA del objeto y `motion_stage` los desplaza a la línea del stage. Una lista
   que se apila fila a fila es **un gesto, no seis decisiones editoriales**: declararlo con
   seis `OBJECT_STATE` metería en el contrato creativo un escalonado de 130 ms que no sale
   del transcript.
2. **`reveal`.** `OBJECT_STATE {"reveal": "r3"}` enciende el sub-elemento `{eid}-r3`. Es
   lo contrario del punto 1 y por eso conviven: cuando cada fila SÍ cae en su palabra —el
   enunciado de categorías— el ritmo es del EDL, no del objeto.
3. **`count`.** El contador que sube, con el `count_from` rastreado por el compilador desde
   el estado anterior, igual que las agujas del reloj. Mismo patrón probado: se tuenea un
   número **puro** y el `onUpdate` reescribe el texto.

⚠ **Un objeto con TEXTO dentro necesita `data-layout-allow-occlusion`.** El texto de un
objeto vive por debajo de `.stage-grain`, que es a sangre. El grano está al **3.5 %** de
opacidad y no oculta nada, pero el linter de layout no puede ver a través de un
`background-image` y cuenta la capa como opaca: **seis errores de golpe** en la pieza 12 y
ninguno en la 10, cuyos seis objetos eran SVG puro. El atributo va en el elemento
**ocluido** (probado en el grano primero: los seis errores no se movieron) y **no** en
`_object_html`, para que los seis objetos de la 10 conserven la comprobación.

Y tiene un precio que hay que pagar a mano: los pares de contraste de ese texto **dejan de
muestrearse** (30/30 → 18/18). `0/0 no es que pase, es que no midió` vale igual para 18/18:
los 12 pares que desaparecen se miden con `tokens.contrast()` y se anotan.

⚠ **El ✓ verde solo va en una fila CON nombre.** Un check junto a una barra en bruto se lee
como «esto ya está resuelto», que es lo contrario del beat en que el documento aparece sin
organizar. Es la misma trampa que `flow_steps` ya documenta con «✓ junto a No hay stock».

⚠ **Con `reveal`, el HUECO se queda puesto y lo que entra es su CONTENIDO.** Animando la
fila entera, el panel conservaba su alto de seis filas con solo cuatro visibles: el tercio
de abajo quedaba vacío **dentro del marco** y se leía como un panel roto, no como una lista
llenándose.

**Dos slots nuevos, `head` (540, 440) y `foot` (540, 1250)**, para un flujo origen →
operador → destino. En 9:16 ese flujo **no cabe en horizontal**: a 1080 de ancho, tres
paneles legibles se quedan en 340 px cada uno y el del medio —el que lleva la información—
deja de leerse. En vertical el operador se queda en `center` a tamaño de héroe. El `foot`
en 1250 está medido contra el subtítulo del stage (y1352 con dos líneas): 48 px de margen.

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
6b. **Un stage EN PANTALLA SIN OBJETOS no cae a negro, y por eso no se veía.** Es la
   hermana de la trampa 6 y nace del mismo fallo: el suelo del stage **sí se pinta** —con
   su viñeta y su retícula—, así que `check_no_black()` no encuentra nada. Lo que se ve es
   un fondo grafito vacío con un subtítulo encima, y se lee como un error de montaje.
   Medido: **1.63 s** en el stage de la secuencia de la pieza 13 y **0.97 s** en el de su
   línea de tiempo; y, ya entregada, **0.90 / 1.38 / 0.73 s** en los tres stages de la
   pieza 10. Ahora lo mide `edl_metrics.bare_stage_gaps()` y lo reporta la métrica
   `max_bare_stage`.

   **El arreglo es mover el LÍMITE del segmento, no el evento.** La ventana de un segmento
   empieza en su primera palabra, así que hacer que el stage empiece en la palabra del
   objeto cierra el hueco **sin adelantar el guion** — que es lo que pasaría adelantando el
   objeto a una palabra que todavía no lo nombra. En la 13 salió gratis: «Puedes
   automatizar» y «Si una persona» volvieron al presentador, donde además estaban mejor.

6c. **El visual que llega al FINAL no se funde a la salida — y el emisor no lo cumplía.**
   La regla ya estaba escrita en la trampa 6 («el CTA tiene que estar puesto en el último
   frame, que es el que se congela cuando el reel vuelve a empezar») pero el emisor de
   visuales le ponía `fade_out` a TODOS, así que un CTA con `end: null` pasaba sus últimos
   0.26 s apagándose. Medido sobre un snapshot en t=56.8 de la pieza 16: el titular
   «CANVA» en gris a medio fundir. **La pieza 15 se entregó con el mismo defecto.**
   `check_no_black` no lo caza porque solo mide la cobertura ENTRE visuales, no la cola.
   Arreglado en `build-composition.py`: si `ve >= dur − 1/FPS`, no se emiten ni el `to` ni
   el `set` de salida.

7bis. **Un SVG de marca inlineado dos veces se renderiza VACÍO la segunda vez.** La marca
   de Canva trae seis `<radialGradient>` con ids fijos de exportador (`_2002046508__a`…) y
   seis `fill="url(#…)"` que los apuntan; la pieza 16 la pinta CINCO veces. El navegador
   resuelve cada `url(#id)` al PRIMER elemento con ese id del documento, así que en cuanto
   el renderer oculta el host de esa primera instancia las otras cuatro pierden el relleno:
   **el marco se sigue viendo y la marca desaparece.** Cazado sobre snapshots en t=15.5 y
   t=17.5, nunca en el JSON. Dos capas de arreglo: `logos.mark(uid=…)` renombra los ids por
   instancia (sufijo de sha1 del `uid`, no un contador — un contador dependería del ORDEN de
   las llamadas y el mismo plan compilado dos veces daría HTML distinto), y
   `check_unique_element_ids` en `build-composition.py` falla sobre el HTML ya ensamblado si
   algún id se repite. Llamar a `mark()` sin `uid` sobre un SVG con referencias internas
   ahora **lanza**, en vez de renderizar un hueco en silencio. ⚠ El regex del gate va con
   `(?<![-\w])id="`, no con `\bid="`: con `\b` casa dentro de `data-viz-id="…"` y los doce
   visuales salían como duplicados — un falso positivo que paró una compilación buena.

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

### El ATAQUE también se calcula — y estuvo mal hasta la pieza 18

Mismo error de forma que el volumen escrito a mano, y por eso vivió diecisiete piezas:
**dar por hecho que los ficheros vienen alineados.** `data-start` se escribía con el
tiempo del beat, pero el navegador empieza a REPRODUCIR ahí y **16 de los 19 efectos de la
librería traen silencio de cabecera**:

| efecto | cabecera | efecto | cabecera |
| --- | --- | --- | --- |
| `riser` | **1727 ms** | `ping` | 323 ms |
| `whoosh-cinematic` | **1553 ms** | `glitch-3` | 244 ms |
| `error` | **604 ms** | `pop` | 116 ms |
| `typing` | 437 ms | `glitch-1` | 114 ms |
| `chime` | 416 ms | `whoosh` / `whoosh-short` | 76 ms |

Un `error` declarado en «no sabías hacerla» sonaba **sobre la palabra siguiente**. Se oye
—por eso nadie lo vio— pero marca otra cosa, y §12 dice que el efecto marca algo que pasa
en imagen. `_lead_in()` lo mide (envolvente al 5 % del pico del propio fichero, no un
umbral absoluto en dB, que castigaría a los efectos flojos) y `build_sfx` **adelanta el
`data-start` esa cabecera**, así que lo que el plan declara es cuándo se OYE el efecto.
Por debajo de `SFX_LEAD_MIN` (30 ms, menos de dos frames) no se compensa: eso es ruido de
medición, no retraso.

Cuando la cabecera no cabe antes del segundo 0 —un efecto declarado en `t=0.0`— la
compilación **avisa con el número** en vez de callarse: en la pieza 18, `whoosh-short`
suena 76 ms tarde y está escrito en la salida.

⚠ **Cómo se encontró, que importa más que el arreglo.** El filtro adaptado de la pieza 2
—correlar la forma de onda del efecto contra el residuo del MP4— daba **correlación cero**
para `error`. La primera lectura fue «el efecto no está». La segunda, al abrir el fichero,
fue que la plantilla de 350 ms con la que se correlaba era **silencio puro**. *El fallo del
test era el hallazgo*: cuando una medición da un cero imposible, lo primero que se revisa
es la medición, y a veces eso destapa el bug de verdad.

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

**Piezas 5–9.** Editadas y sin documentar aquí una por una.

⚠ **La numeración de las piezas NO es la de los reels.** `VIDEOS ORIGINALES/` se reorganizó
en carpetas `REEL <n> — <título>` con su `GUION.MD`, y esa numeración es del calendario de
publicación, no del estudio. La pieza **10** ya trata el tema del REEL 9 con **otra toma**
(49 s, conversacional); la **11** es ese mismo reel grabado siguiendo el guion. Antes de
abrir un slot, mirar de qué habla el transcript, no el número de la carpeta.

**Pieza 10 — terminada, primera desde un `edl.json`.** `videos/10/output.mp4`, REEL 9:16,
**44.33 s**, 29.8 MB, H.264 + AAC. Clínicas que pierden pacientes por contestar tarde.

- Fuente: 49.16 s, corte a 44.33 s (10 % fuera, 5 cortes). Barbilla p95 = **0.4324**,
  48/48 muestras; centroide `cx_frac` **0.4861** (Tarea 8: el punch-in recorta alrededor
  de la CARA, no del centro geométrico). 131 palabras.
- **El hito del plan `docs/superpowers/plans/2026-09-07-edl-motion-design.md`**: de punta a
  punta desde un `videos/10/edl.json` que referencia índices de palabra, no floats a mano.
  `edl-compile.py` deriva shots, stages, captions y SFX y aplica los gates de estilo antes
  de escribir el plan — ver §9 arriba y la spec en `docs/superpowers/specs/`.
- **3 Motion Stage**, cada uno una serie contigua de segmentos con un solo `fade_in`/
  `fade_out` (nunca uno por segmento — la clase de bug de `check_no_black()` no puede
  ocurrir con un stage continuo):

  | Palabras | t | Qué visualiza | Objeto(s) |
  | --- | --- | --- | --- |
  | 14–37 | 4.13–11.33 | la hora exacta a la que escribieron, y las 8 horas que pasan | el reloj, **match cut** 11:00 → 19:00 sobre la MISMA instancia |
  | 57–72 | 18.43–23.87 | cuatro trabajos incompatibles a la vez | sillón + teléfono + tarjeta + Instagram, **acumulativos** — se quedan, y en «al mismo tiempo» los tres orbitales se cierran sobre el sillón por un delta horneado |
  | 80–87 | 26.47–28.80 | contratar mueve el cuello de botella, no lo quita | el embudo — sexto y último objeto de la librería inicial |

- **Librería de objetos completa en 6**: `clock` · `dental-chair` · `phone` ·
  `card-payment` · `instagram` · `bottleneck`. Cada uno un SVG sobre tokens con
  `perspective()`/`rotateY()` ESTÁTICOS en un wrapper hijo — GSAP solo toca
  `opacity`/`scale`/`x`/`y` del div exterior.
- **SFX opt-in**: 6 declaraciones (`sfx:"auto"` en el punch del hook, la entrada del reloj,
  el barrido de agujas, la entrada del sillón, el cierre radial y la entrada del embudo),
  **0 colapsadas** — caen lo bastante separadas.
- 10 segmentos, 12 encuadres, 33 bloques de subtítulo con 12 keywords, 6 efectos en 1
  pista + cama musical.
- `presenter_share` **0.66** — dentro del `warn_in` [0.35, 0.70] del perfil, fuera de la
  banda ideal [0.45, 0.60] pero sin bloquear (severidad `warn`, no `fail`). Subirlo más
  habría exigido inventar un séptimo objeto sin `reason` real o forzar `MOTION_STAGE` en
  la tesis/cierre, que sus propios `reason` argumentan que deben quedarse en cámara —
  se dejó así a propósito.
- Validación **0 errores** de estructura, runtime, layout y motion · **19/19 WCAG AA**.
  Sobre el MP4: duración 44.333 s, sin negro real (`pix_th=0.03`), pico **−3.3 dB**,
  **0 muestras saturadas**, media −22.9 dB. Tinta más baja del bloque de dos líneas más
  bajo (Task 9's acumulación pasa por el mismo cálculo): **y1518**, dentro de la zona
  segura. El reloj: `rotate(330...)` al entrar (11:00) y `570 % 360 = 210°` al final del
  barrido (19:00, la posición del «7»), mismo `id` en las dos puntas.
- Golden file en `tests/golden/10.plan.json` — congela el `plan.json` compilado; un slot
  movido en `objects.py` o un token tocado en `tokens.py` rompe `test_golden.py` en vez de
  descubrirse tres piezas después.

**Pieza 11 — terminada.** `videos/11/output.mp4`, copia en
`VIDEOS EDITADOS/video-11-clinica-whatsapp-reel.mp4`. REEL 9:16, **41.40 s**, 20.7 MB,
H.264 + AAC. La clínica que pierde pacientes en WhatsApp · CTA **CLÍNICA**.

- Fuente `VIDEOS ORIGINALES/REEL 9 — …/video.mov`: 60.02 s, H.264 **SDR bt709**, 1080×1920,
  rot 0. Corte 60.02 → 41.41 s (31 % fuera, 6 cortes). Barbilla p95 = 0.5436, 48/48.
  90 palabras, verificadas re-transcribiendo el bruto: 90 = 90.
- **Dos bordes de corte se movieron a mano.** `refine-timings.py` avisó de cuatro huecos con
  sonido audible; midiendo la envolvente RMS en ventanas de 50 ms, dos de esas islas eran
  **ataques separados** del final de palabra —un blip de 380 ms tras «clínica.» y una
  vacilación de 600 ms a −20 dB antes del CTA— y el corte automático caía **encima**,
  dejando 80 y 160 ms truncados. El borde va antes del ataque, no dentro. La lección:
  el aviso dice *dónde* mirar; **la envolvente dice si la isla es la cola de la palabra o
  un sonido nuevo**, y solo eso decide si el corte la parte o la elimina entera.
- ⚠ **AssemblyAI devolvió una palabra con el final desbordado 2.3 s** («interés», pisando a
  las cuatro siguientes). No lo caza ningún aviso de `refine-timings`: se ve comparando
  cada `end` con el `start` siguiente. Recortado al inicio de la siguiente.
- **5 visuales**, cuatro técnicas:

  | t | Función | Visual | Técnica |
  | --- | --- | --- | --- |
  | 7.05–11.05 | pregunta, espera, silencio | `chat_unanswered` + espera ámbar | mockup |
  | 11.05–13.90 | escribe a otra clínica, y le contestan | el MISMO chat, con `reply` | mockup |
  | 16.75–23.30 | responder, identificar, pedir datos | `chip_grid` que se amontona | mockup |
  | 23.30–28.85 | dirige → cita → persona | `flow_steps` `tone: ok` | mockup |
  | 35.30–fin | «comenta CLÍNICA» | `comment_ui` | mockup |

- Los dos tramos de **cara pelada** son el hook y el matiz («no reemplaza la atención
  humana»): los dos momentos en los que un gráfico le roba el argumento.
- 13 encuadres, 4 tarjetas, 21 bloques con 21 keywords, 32 efectos.
- Validación **0 errores** · **38/38 WCAG AA**. Sobre el MP4: sin negro real, pico
  **−2.53 dB**, **0 muestras saturadas**, voz 0.695 frente a 0.700 declarada, música en la
  cola y **28/32 efectos** con ataque detectable (los cuatro restantes son `riser` y
  `typing` —que por diseño no tienen ataque— y dos `ping` bajo voz). Tinta más baja fuera
  de plano lleno: **y1518**, 18 px de margen.

**Pieza 12 — terminada.** `videos/12/output.mp4`, copia en
`VIDEOS EDITADOS/video-12-respuestas-reel.mp4`. REEL 9:16, **41.70 s**, 27.8 MB,
H.264 + AAC. Responder lo mismo todos los días · CTA **RESPUESTAS**.

- Fuente `VIDEOS ORIGINALES/REEL 10 — …/video.mov`: 60.04 s, H.264 **SDR bt709**,
  1080×1920, rot 0. Corte 60.04 → 41.70 s (31 % fuera, 6 cortes). Barbilla p95 = 0.6608 —
  **la más baja de la serie**, 48/48 muestras; centroide `cx_frac` 0.5106. 87 palabras.
- **El aviso de alineación imposible resultó ser un falso positivo, y comprobarlo fue
  barato.** `refine-timings.py` marcó «otra» (146 ms) y «todavía» (292 ms) a 13.7 síl/s.
  Re-transcrito el tramo 4.6–10.4 s suelto, los timings volvieron **a 90 ms de los
  originales**: ahí no hay desfase, habla rápido. Se empalmó el tramo aislado igual, porque
  su cola de «todavía» sale 48 ms más larga y ese borde es donde corta `plan-cuts`. La
  lección de la pieza 3 se mantiene —el aviso dice dónde mirar—, pero **mirar puede
  confirmar que no pasa nada**, y eso también es un resultado.
- **4 Motion Stage y 5 rótulos**, repartidos para que el presentador nunca desaparezca más
  de un beat sin razón:

  | Palabras | t | Qué visualiza | Cómo |
  | --- | --- | --- | --- |
  | 4–9 | 1.85–4.51 | la misma pregunta, 27 veces | 4 `msg-card` apilándose + `answer-counter` 12→18→27, tema `problem` |
  | 19–26 | 9.19–12.95 | las respuestas ya existen, sueltas | `knowledge-base` con 6 filas **sin etiqueta**, en cascada interna |
  | 37–53 | 16.49–27.50 | pregunta → base → respuesta aprobada | el flujo vertical `head`/`center`/`foot`, con las 6 categorías encendiéndose **en su palabra** y el sello en «aprobada» |
  | 63–70 | 32.30–35.57 | esas cuatro preguntas ya no las contesta nadie | **las MISMAS 4 tarjetas** del hook, en los mismos slots, selladas AUTOMATIZADO a la vez, tema `success` |

- **La rima visual es la estructura de la pieza.** Las cuatro tarjetas del hook vuelven al
  final con el mismo texto y en el mismo slot; lo único que cambia es el sello y el tema.
  Eso es lo que deja ver *qué* cambió — misma lógica que las dos instancias de
  `chat_unanswered` en la pieza 11.
- **El documento aparece dos veces y no es repetición**: primero **sin nombres** (nadie ha
  dicho ninguna categoría todavía, y etiquetarlas ahí adelantaría el guion) y luego con
  ellos, uno por palabra. Dos instancias, dos stages, el mismo objeto en sus dos modos.
- `transitionIn` especiales: **OBJECT_MATCH_CUT** en el sello (es el mismo documento
  mutando, no una escena nueva) y **DIAGONAL_WIPE** en el remate. 2 de 10 límites = el tope
  exacto del gate.
- 11 segmentos, 15 encuadres (10 en pantalla), 24 bloques con 15 keywords, **15 efectos**
  en 2 pistas + cama musical.
- **Todos los gates en verde a la primera**: `presenter_share` **0.5039** —dentro de la
  banda ideal [0.45, 0.60], no solo del `warn_in`, que es donde se quedó la 10 con 0.66—
  `max_micro_gap` 2.461 · `max_macro_gap` 3.532 · `min_camera_gap` 1.289 ·
  `theme_change_count` 2 · `decorative_reason_count` 0 · `sfx_dropped` 0.
- Validación **0 errores** · **18/18 WCAG AA por el checker + 12 pares medidos a mano**
  con `tokens.contrast()` (peor caso 5.76:1), los que el
  `data-layout-allow-occlusion` saca del muestreo. Ver §7.
- Sobre el MP4: duración **41.700 s** exacta, sin negro real (`pix_th=0.03`), pico por canal
  **−2.83 / −2.80 dB**, **0 muestras saturadas**, voz **0.697** frente a 0.700 declarada,
  música aislada restando la voz alineada a −35…−39 dB (objetivo −37.1) y tinta más baja
  fuera de plano lleno **y1531**.
- **15/15 efectos** localizados por **filtro adaptado** a la forma de onda real de cada
  archivo, con desfase submilimétrico. La envolvente sola solo veía 10: los otros cinco
  caen bajo habla fuerte, donde el residuo del **códec** sube ~14 dB por debajo de la voz y
  se come un `pop` de volumen 0.254. **El salto de envolvente mide si el efecto DESTACA;
  el filtro adaptado mide si ESTÁ.** Son dos preguntas distintas y solo la segunda dice si
  la mezcla se escribió bien.
- ⚠ **Y el `chime` necesitó una tercera pasada.** Con filtro adaptado sobre 300 ms daba
  correlación 0.12: es una campana de **2.5 s** de ataque lento, y 300 ms de ella no
  identifican nada. Con la campana completa y la banda limitada a su parcial dominante
  (3512 Hz): correlación **1.04** a +3.0 ms, y su propia banda sube **+24.8 dB**. La
  ventana del filtro tiene que cubrir el efecto, no el ataque que uno espera que tenga.
- Golden en `tests/golden/12.plan.json`. La suite pasa de **191 a 235 tests**: 16 del
  evento `CARD` —la mayoría sobre lo que NO se puede escribir— y 26 de los objetos y sus
  tres mecanismos.

**Pieza 13 — terminada.** `videos/13/output.mp4`, copia en
`VIDEOS EDITADOS/video-13-citas-reel.mp4`. REEL 9:16, **41.53 s**, 24.9 MB, H.264 + AAC.
Pacientes que no se presentan a sus citas · CTA **CITAS**.

- Fuente `VIDEOS ORIGINALES/REEL 11 — …/video.mov`: 60.03 s, H.264 **SDR bt709**,
  1080×1920, rot 0. Corte 60.03 → 41.52 s (31 % fuera, 6 cortes). Barbilla p95 = 0.6376,
  47/48 muestras; centroide `cx_frac` 0.5442. 88 palabras.
- ⚠ **La carpeta del reel y el pedido no coincidían.** Se pidió «el reel 12» con
  instrucciones tituladas REEL 11 y con el guion de citas (CTA CITAS); el REEL 12 es
  «Tener datos sin saber qué hacer con ellos». **Manda el contenido del brief, no el
  número**, y las dos carpetas tenían metraje nuevo. Es la misma trampa que ya avisa la
  nota de numeración de arriba, vista desde el otro lado.
- **El take más sucio hasta ahora, y todo se resolvió midiendo.** `refine-timings.py` dio
  10 bordes que cuadrar, **4 huecos con sonido audible** y **2 tramos con alineación
  imposible**:
  · **Los dos desfases eran reales.** «olvide» venía en 213 ms (14.1 síl/s) y «todo» en
    162 ms. Re-transcritos sueltos: 393 y 247 ms. Se empalman los TIEMPOS y se conserva el
    TEXTO del pase de contexto largo — el aislado oyó «aumenta» donde el guion dice
    «aumentan». Cada pase es mejor en una cosa distinta.
  · **Las 4 islas de sonido no eran cola de palabra.** Re-transcritas sueltas dieron **0
    palabras** (ningún arranque en falso), y la envolvente RMS las situó a **1.6–2.4 s de
    silencio real** de la palabra anterior: sonidos aparte en mitad de las pausas. Una iba
    a **−8 dB**, más fuerte que el habla (p90 = −12.8 dB). Al caer enteras dentro de las
    pausas que `plan-cuts` colapsa, **se eliminaron completas sin que ningún borde las
    partiera** — verificado contra los `keeps` antes de cortar, y sobre el MP4 después.
    Distinto de la pieza 11, donde dos islas SÍ eran cola de palabra y hubo que mover el
    borde a mano. **El aviso dice dónde mirar; la envolvente dice qué es; y solo eso decide
    si el corte la parte o se la lleva entera.**
- **4 Motion Stage y 5 rótulos**:

  | Palabras | t | Qué visualiza | Cómo |
  | --- | --- | --- | --- |
  | 3–8 | 1.56–3.59 | la franja de las 11 no tiene a nadie | `calendar`, con el hueco discontinuo y HORA PERDIDA entrando en «culpa», tema `problem` |
  | 18–23 | 7.36–9.86 | siete días entre reservar y venir | `appointment-timeline` vertical, 4 paradas |
  | 24–28 | 9.86–11.72 | en esos días nadie escribe | LA MISMA línea de tiempo, por **match cut**: SIN MENSAJES y el aro de riesgo en el nodo final |
  | 39–51 | 17.26–24.40 | tres mensajes, cada uno con su hora de salida | 3 × `msg-card`, y el sello cae en la palabra que lo nombra |
  | 56–59 | 26.01–29.16 | confirmar o reprogramar en un toque | `msg-card` + `confirm-buttons`, con el check en «reprogramar» |

- **El beat sin sonido es una decisión, no un olvido.** El stage del silencio (24–28) es el
  único de la pieza sin efecto: ponerle sonido al silencio lo contradice.
- El stage de los botones se queda en tema **`primary`** y el verde vive **solo en el botón
  que se espera pulsar**. Teñir la escena de éxito convertiría una opción del paciente en
  un mensaje de sistema — y así `theme_change_count` se queda en 2.
- **Un bloque de subtítulo de DOS palabras, a propósito.** «Puedes automatizar» es una
  cláusula completa; partirla para llegar a tres pegaría «la cita.» con «Puedes», que es
  exactamente lo que la doctrina de troceo prohíbe.
- 11 segmentos, 18 encuadres (11 en pantalla), 23 bloques con 16 keywords, **8 efectos** en
  2 pistas + cama musical.
- **Todos los gates en verde**: `presenter_share` **0.5982** · `max_bare_stage` **0.0** ·
  `max_micro_gap` 2.004 · `max_macro_gap` 2.924 · `min_camera_gap` 0.966 ·
  `theme_change_count` 2 · `special_transition_ratio` 0.2 · `decorative_reason_count` 0 ·
  `sfx_dropped` 0.
- Validación **0 errores** · **27/27 WCAG AA**. Sobre el MP4: duración **41.533 s**, sin
  negro real, pico por canal **−2.46 / −2.42 dB**, **0 muestras saturadas**, voz **0.696**
  frente a 0.700, música aislada a −34…−39 dB (objetivo −37.1), tinta más baja fuera de
  plano lleno **y1518** (18 px de margen) y **8/8 efectos** localizados por filtro adaptado
  con desfase submilimétrico.
- El `error` del hook queda **+3.4 dB** sobre la voz de su tramo porque ya está a
  `volume 1.0` — el mismo caso documentado en la pieza 3, y por la misma razón: la voz
  manda y el efecto cae en la palabra que lo justifica.
- Golden en `tests/golden/13.plan.json`. La suite pasa de **235 a 261 tests**: 10 de
  `max_bare_stage` y 15 de los tres objetos y el reuso de `msg-card`.

**Pieza 14 — terminada, y re-entregada.** `videos/14/output.mp4`, copia en
`VIDEOS EDITADOS/video-14-datos-reel.mp4`. REEL 9:16, **39.17 s**, 23.9 MB,
H.264 + AAC. Tener datos sin saber qué hacer con ellos · CTA **DATOS**.

- Fuente `VIDEOS ORIGINALES/REEL 12 — …/video.mov`: 60.03 s, H.264 **SDR bt709**,
  1080×1920, rot 0. Corte 60.03 → 39.17 s (**35 % fuera**, 6 cortes). Barbilla p95 =
  **0.7297** —la más baja de la serie, 48/48 muestras—; centroide `cx_frac` 0.5755.
  92 palabras.
- **Esta vez el número del reel SÍ era el del brief**, al contrario que en la 13.
  Comprobarlo cuesta un minuto y se comprueba igual.
- ⚠ **AssemblyAI se comió una palabra entera, y ninguna medición lo caza.** El guion
  dice «qué producto necesita reposición» y el transcript traía «producto necesita
  reposición». Re-transcrito el tramo 26.0–29.6 s suelto, el aislado **sí oye «qué»** a
  27.243–27.407. Insertada a mano: 91 → **92 palabras**. Hermana de la trampa de las
  siglas (§2): **el transcript se lee contra el guion**, porque una palabra que falta no
  rompe ningún número.
- **Los dos avisos de alineación imposible eran falsos positivos.** «envío» (178 ms) y
  «para» (162 ms) re-transcritos sueltos dieron **177 y 161 ms**: a 1 ms de los
  originales. No se empalmó nada, y confirmarlo también es un resultado.

**⚠ La primera entrega salió con una respiración dentro del hook, y la cazó el
usuario.** 900 ms a −10.4 dB entre «decisión.» y «Una». La causa raíz, el arreglo y
las cuatro trampas que destapó están en §2 («Voz no es sonido»); aquí queda lo que le
pasó a la pieza:

- El primer corte daba **41.63 s**; con los bordes atados a la voz y las pausas
  colocadas sobre silencio, **39.17 s**. Los 2.46 s de diferencia son respiraciones.
- `refine-timings` pasó de mover **9 bordes a 6**: los tres que dejó de mover
  —«decisión.», «acción.» y «accionables.»— eran los tres que se tragaban una
  inspiración de 500 ms cada uno. Y destapó **una cuarta a −7.0 dB** tras «ingresos.»,
  que hasta entonces vivía escondida dentro de la palabra.
- Auditado el corte nuevo con el umbral de la fuente: **0 respiraciones audibles fuera
  de un span de palabra**. Verificado también sobre el MP4: tras «decisión.» el nivel
  cae a −42 dB (la cama musical) y se queda ahí hasta «Una».
- **La misma auditoría sobre las piezas ya publicadas**: la 11 y la 12 limpias, la
  **13 tiene una a −15.1 dB** entre «seguimiento.» y «Si». Su hueco es de 3.99 s, así
  que se arregla volviendo a cortar con `--audio` — no hace falta herramienta nueva.

- **2 Motion Stage y 4 rótulos.** La pieza se parte en dos mitades y cada una tiene su
  objeto:

  | Palabras | Qué visualiza | Cómo |
  | --- | --- | --- |
  | 13–22 | una hoja con cientos de filas, y una cifra enterrada | `spreadsheet`, tema `problem`; «1.284 FILAS» en «cientos» y `$ 4.820` en «valiosa» |
  | 23–32 | encontrarla obliga a buscar a mano | LA MISMA hoja, por **match cut**: tres interrogantes en «manualmente» |
  | 44–47 | el primer indicador y su decisión | `kpi-card` en `stack-1`, pastilla en «más» |
  | 48–59 | la sucursal bajo meta y el producto sin stock | dos `kpi-card` más, `stack-2` y `stack-3` |
  | 60–67 | el método que concentra ingresos | el cuarto en `stack-4`; la pastilla cierra en «ingresos» |

- **El panel se ACUMULA, no se sustituye.** Primera pieza que apila cuatro instancias
  del MISMO objeto en los cuatro slots `stack`: sustituirlas habría dejado cuatro
  gráficos sueltos en vez de un panel, y el argumento necesita verlos juntos.
- **La regla es un RÓTULO, no un stage**: «DATO SIN ACCIÓN = RUIDO» la formula él, así
  que acompaña su cara en vez de sustituirla. Entra en «provocar», no antes.
- **El límite del stage se movió para cerrar el suelo desnudo** (gotcha #6b): el A_ROLL
  se queda con «te ayuda a detectar» y el stage arranca en la palabra del objeto.
- 9 segmentos, 15 encuadres (10 en pantalla), 21 bloques con 21 keywords, **14 efectos**
  en 1 pista + cama musical.
- **Todos los gates en verde**: `presenter_share` **0.5111** —banda ideal—
  `max_bare_stage` **0.0** · `max_micro_gap` 2.07 · `max_macro_gap` 2.945 ·
  `min_camera_gap` 1.048 · `theme_change_count` **1** · `special_transition_ratio` 0.125
  · `punch_zoom_count` 0 · `decorative_reason_count` 0 · `sfx_dropped` 0.
- Validación **0 errores** de estructura, runtime, layout y motion.
- ⚠ **Los dos avisos de contraste son del FUNDIDO, no del diseño, y este take los
  provoca.** El muestreo cae dentro de la entrada o la salida de un rótulo —340 y 280 ms—
  **sobre la pared más clara de la serie**, que aquí ocupa medio frame porque la barbilla
  está en 0.730. Medido sobre los PNG, en las dos entregas:

  | rótulo | en pleno fundido | asentado |
  | --- | --- | --- |
  | `card-04` kicker / titular (entrada, t+220 ms) | 2.11:1 · 1.84:1 | 5.31:1 · **6.70:1** |
  | `card-03` kicker / pastilla (salida, t−75 ms) | 1.46:1 · 1.79:1 | 5.23:1 · **10.64:1** |

  El 6.70 es exactamente el `violet_hi/bg` que declaran los tokens. **La pared clara es
  de este take; el fundido es de todas las piezas** — arreglarlo sería tocar el fundido
  de las tarjetas de todo el proyecto, así que queda medido y no tocado.
- Sobre el MP4: duración **39.167 s** exacta, sin negro real (`pix_th=0.03`), pico por
  canal **−2.43 / −2.45 dB**, **0 muestras saturadas**, voz **0.692** frente a 0.700
  declarada, música aislada a **−35.2…−39.7 dB** (objetivo −37.1) y tinta más baja
  **y1531**, 5 px de margen — el mismo `floor_top` apretando que en la pieza 12.
- **14/14 efectos** localizados por filtro adaptado, desfase **submilimétrico** y
  amplitud al **96–100 %** de la declarada. El `chime` vuelve a ser la excepción
  conocida (cola de 2.5 s solapada con la música en el residuo): presente y localizado,
  pero su amplitud no se mide bien con la plantilla entera — ver la pieza 12.
- ⚠ **Medir la tinta del subtítulo por luminancia sola miente sobre metraje claro.**
  «píxel > 205» daba **y1919** en un frame sin una sola letra ahí: era la pared. La firma
  del subtítulo sobre metraje es el **filete grafito de 7 px** — píxel casi blanco con
  grafito pegado a menos de 9 px. Con esa firma, y1531.
- Golden en `tests/golden/14.plan.json`. La suite pasa de **261 a 291 tests**: 11 de los
  dos objetos nuevos, 4 del plan compilado, **11 de `voicing.py`** —incluido el que falla
  si «decisión.» vuelve a estirarse sobre la respiración— y **4 del gate 4b**, uno de
  ellos con margen 0 para probar que el camino de FALLO existe: un gate que nunca ha
  fallado no es un gate.

⚠ **Medir el pico con `-ac 1` miente.** La mezcla a mono de ffmpeg **suma** los dos canales
(+3 dB): daba pico +0.26 dB y 17 muestras saturadas sobre un archivo cuyos canales reales
van a −2.53 dB sin una sola saturada. El pico se mide **por canal**.

Y **no solo el pico**: en la pieza 12 la misma trampa dio una ganancia de voz de **0.493**
frente a 0.700 declarada —parecía un fallo de mezcla— porque la referencia se había
decodificado con `-ac 1`. 0.493 × 1.414 = 0.697. **Cualquier razón entre dos archivos se
mide con los dos en estéreo.**

⚠ **`mockups.py` perdió `chat_unanswered` entre la pieza 9 y hoy** — el árbol de trabajo
quedó en la versión del commit inicial y el mockup solo sobrevivía en el `index.html`
renderizado de la 9, cuyo `plan.json` ya no compilaba. Restaurado desde ahí y ampliado con
`reply`. **`keyword_hero(mark=…)`, que la pieza 9 también usa, sigue sin existir.**

Avisos abiertos que no bloquean: `composition_file_too_large`, `timeline_track_too_dense`,
`pointer_events_none` y **`gsap_repeated_fromto_without_baseline`** sobre los elementos de
keyword (12 en la pieza 10, 15 en la 12). Es del emisor de keywords de
`build-composition.py`, no de ninguna pieza: dos `fromTo` sobre el mismo `#cNkM` sin un
`tl.set` de base a t=0. Sin efecto visible —el bloque de subtítulo está a opacidad 0 hasta
su propio instante— pero es deuda real y crece con cada keyword.

⚠ **Los EDL de las piezas 12, 13 y 14 se perdieron.** `videos/` se borró sin commitear en
algún punto y esos tres `edl.json` nunca llegaron a HEAD ni a ningún commit colgante — se
buscaron los dos sitios antes de darlos por perdidos. Los golden (`tests/golden/12.plan.json`
· `13.plan.json` · `14.plan.json`) sí sobreviven, pero sin su EDL de origen no hay nada que
compilar y comparar contra ellos: `tests/conftest.py` hace `pytest.skip` en `edl12`/`edl13`/
`edl14` con el motivo escrito, en vez de fallar o fingir que la fixture existe. **La única
no-regresión viva del camino EDL es la pieza 10** (`test_el_plan_de_la_pieza_10_no_ha_cambiado`,
que sí tiene su `edl.json`) — si se toca `edl_compile.py` o `edl_schema.py`, ese es el test
que hay que mirar, porque los otros tres están apagados y no van a avisar.

**Pieza 15 — terminada, primera en `triband`.** `videos/15/output.mp4`, REEL 9:16,
**69.87 s**, H.264 + AAC. 5 herramientas para construir webs con Claude (Anime.js, Motion,
Kokonut UI, Bklit UI, Manus) · CTA **WEBS**.

- ⚠ **`VIDEOS ORIGINALES/1` → pieza 15.** La numeración de la carpeta fuente NO es la de
  pieza, la misma trampa que ya avisa la nota de la pieza 10 — y aquí confundió otra vez
  antes de escribirlo: se busca por lo que dice el `guion.md` y el transcript, no por el
  número de carpeta.
- Fuente `VIDEOS ORIGINALES/1/pantalla.MOV`: **78.94 s → 69.87 s** (11.5 % fuera, 9 cortes).
  178 palabras. Barbilla `chin_frac` **0.4531**, borde superior `top_frac` **0.2812**,
  48/48 muestras.
- **Tres mejoras sobre el montaje inicial** (rama `triband-layout`, tras el primer render):
  1. **La división de bandas pasa a la MITAD del lienzo** — `top` [0,660] · `text` [660,960]
     · `speaker` [960,1920], antes 820/1120. Los `rect` de las cinco grabaciones bajan de
     `[60,140,960,540]` a `[60,60,960,540]` (mismo 16:9, margen simétrico de 60 px arriba y
     abajo dentro de los 660 px de la banda nueva).
  2. **El `anchor` de los encuadres `band` baja de 0.5714 a 0.38** — con la banda `speaker`
     más alta ahora (960 en vez de 1120) el default del estilo subía demasiado el recorte y
     se llevaba la coronilla. `check_face_top_clear` (§4) es el gate nuevo que lo habría
     cazado; con 0.38 el borde superior de la cara proyectado cae en y1135, 175 px de
     margen sobre el techo de la banda.
  3. **Karaoke en vez de keyword única dentro de `band`** (§5): fondo violeta (`violet_dk`,
     contraste 6.72:1) que viaja palabra a palabra. `full`/`pip` no cambiaron.
- **Cinco herramientas, la misma coreografía para las cinco**: card de logo (`tool_card`,
  `band: "top"`) clavada a su nombre → grabación dirigida (`tool_recording`, `screen-tour.py`)
  en triband. El hook y la tesis se quedan a **plano lleno** (`kind: "full"`), porque ahí la
  cara sola es el argumento y una banda la recortaría sin necesidad.
- **El recorrido de Kokonut UI se rehízo entero.** El primero mostraba, en el segundo exacto
  en que el guion dice «aquí tienes componentes visuales que puedes usar como referencia o
  integrar en tus proyectos», la sección **«What People Are Saying»** de la web — testimonios,
  no componentes: la prueba de fuego del proyecto (arriba del todo) falla con el audio
  apagado ahí. Barrida la grabación (`kokonutui.mov`, 7.47 s) cada 0.5 s: el scroll pasa
  limpio por la fila de tarjetas nombradas (`particle-button` · `liquid-glass-card` ·
  `shimmer-text` · `ai-prompt`) y el registry (`@kokonutui/…`) hasta t≈4.1 s, y de ahí al
  final es testimonios fijos — el scroll frena en seco y ya no hay nada más que mostrar.
  Ventana útil real: **3.8 s**, no los 6.6 s que pide el hueco del EDL. Arreglo en
  `videos/15/screen-tour-kokonut.json`: dos tramos sobre la MISMA ventana de tiempo pero con
  **dos encuadres distintos** (uno recorta la mitad de arriba de la pantalla —el titular
  «Components humans browse. Agents ship.» y el comando de instalación—, el otro la de abajo
  —la rejilla de tarjetas y el registry completos—), en vez de estirar un solo encuadre sobre
  metraje que ya no existe.
- Validación **0 errores**. Verificado sobre el MP4 en el segundo exacto del hallazgo: en
  t=32.0 el encuadre de Kokonut ahora enseña «Get started in seconds» con las tarjetas
  Browse/Install/Customize, y el hablante sigue visible en la banda de abajo (luma máxima
  **232** en y1120–1920, sobre el umbral de 200 — medido ANTES de la Mejora 1; la banda del
  hablante de ese momento era [1120,1920]). Las otras cuatro herramientas no se tocaron: sus
  `screen-tour-*.json` y el `plan.json` quedan sin diff.
- **Re-verificado tras las tres mejoras** sobre el MP4 renderizado con las bandas nuevas:
  barrido de luma cada 2 s en la banda `speaker` [960,1920] — máxima entre **251.2 y 255.0**
  en los 30 puntos que caen dentro de un tramo `band`, todos sobre el umbral de 200. Borde
  superior de la caja de cara (Haar, un frame de cada una de las cinco herramientas):
  y1140–y1147, 180–187 px de margen sobre el techo de la banda (y960) en los cinco casos.
  `blackdetect pix_th=0.03` sin resultados (sin negro real). Detalle completo, con la tabla
  entera del barrido, en `.superpowers/sdd/2026-09-14-triband-layout/task-mejoras-report.md`.
- Suite: **369 passed, 0 failed, 0 errors** (11 skipped — los de arriba, más 12 tests nuevos
  de las mejoras: 6 de `check_face_top_clear`, 6 del karaoke).

**Pieza 16 — terminada.** `videos/16/output.mp4`. REEL 9:16, **56.93 s**, H.264 + AAC.
Claude ahora puede trabajar con Canva · CTA **CANVA**.

- ⚠ **`VIDEOS ORIGINALES/2` → pieza 16**, no pieza 2 (que es el reel del ERP, de agosto).
  La misma trampa de numeración que ya avisan la pieza 10 y la 15.
- Fuente `VIDEOS ORIGINALES/2/pantalla.MOV`: 62.18 s, HEVC **SDR bt709**, 1080×1920, rot 0
  → corte **56.93 s** (8 % fuera, solo 3 cortes: dos pausas de fin de oración y 4.44 s de
  cola muerta). 146 palabras, confianza 0.99. Cara `chin_frac` **0.4542**, `top_frac`
  **0.2625**, 48/48 muestras — con `anchor` 0.38 el borde superior proyectado cae en
  **y1099**, 139 px bajo el techo de la banda `speaker`.
- **Los seis avisos de alineación imposible eran palabras cortas dichas rápido, no deriva**,
  y confirmarlo fue barato: verificado frame a frame que «aplicaciones.» cierra en 17.286
  sobre silencio real (−75 dB en el hueco) y que «Y» arranca en 17.849 justo en el ataque de
  voz. No se re-transcribió nada. La lección de la pieza 12 otra vez: mirar puede confirmar
  que no pasa nada, y eso también es un resultado.
- El transcript oye **«Composeo»** por Composio — no mueve ningún tiempo, pero es la trampa
  de las siglas (§2) vista con un nombre propio, y solo se caza leyendo contra el guion.
- **Doce visuales, sin dos técnicas seguidas iguales**:

  | t | Función | Visual | Técnica |
  | --- | --- | --- | --- |
  | 1.30–8.99 | «una integración de Claude… Canva» | Claude, el `+`, el hueco, Canva | `tool_pair` |
  | 8.99–14.59 | crear · buscar · plantillas · exportar | un chip por palabra | `chip_grid` |
  | 14.59–19.64 | «sin saltar entre aplicaciones» | la pareja ya formada | `tool_pair` |
  | 19.64–22.75 | «Claude, ¿puede hacerme un post?» | el prompt pobre, tecleado | `claude_prompt` |
  | 22.75–24.74 | «el flujo completo» | la palabra como gráfico | `keyword_hero` |
  | 24.74–35.50 | contexto · formato · idea · referencias | cuatro líneas y el conector | `claude_prompt` |
  | 35.50–39.41 | «más allá de Canva» | la bisagra | `keyword_hero` |
  | 39.41–40.05 | «Composio» | card de logo | `tool_card` |
  | 40.05–44.38 | «conectar el agente» | **la grabación real**, 3 tramos | `tool_recording` |
  | 44.38–51.83 | «no automatizar Canva… una capa encima» | la fila, y la capa que cae | `layer_stack` |
  | 51.83–55.20 | «mi configuración» | las tres marcas en fila | `tool_lineup` |
  | 55.20–fin | «comenta CANVA» | el comentario simulado | `comment_ui` |

- **Las dos cards de chat son la estructura de la pieza**, no dos usos del mismo mockup: la
  misma card vacía, corte duro entre las dos, y lo único que cambia es qué se teclea dentro.
  Es la rima visual de `chat_unanswered` en la 11 y de las cuatro tarjetas de la 12.
- **Tres marcas nombradas, tres logos** (regla del usuario). Ninguno entra antes de su
  palabra, y los tres huecos del guion se cubren SOSTENIENDO el visual saliente.
- ⚠ **Canva no publica icono cuadrado vendorizable**: `canva.com` responde 403 a favicon,
  manifest y apple-touch, y el único que sale mide 32 px (el gate pide 220). Se vendoriza el
  **wordmark oficial** (80×30) desde `static.canva.com`, que `_fit_svg` contiene sin
  deformar — el caso que ya documentaba el wordmark 580×118 de Anime.js. Quien lo pinta le
  sube el `logo_px` para que llene el marco (118 en un marco de 140), o al tamaño por
  defecto pesa la mitad que el icono cuadrado que tiene al lado.
- De Composio se vendoriza la variante **blanca**: la negra es tinta #000 sobre transparente
  y desaparecería sobre el fondo `bg` del marco de logo.
- **Dos bugs de la herramienta, los dos cazados sobre frames y arreglados en la herramienta**
  —no en el plan—: el SVG inlineado dos veces (§9, trampa 7bis) y el último visual fundiéndose
  a la salida (§9, trampa 6c). Los dos afectaban también a la pieza 15.
- El recorrido de Composio se rehízo de dos tramos de 2.2 s a **tres de 1.3–1.6 s** tras
  verificarlo sobre el MP4: la página scrollea y un tramo largo no enseña lo que enseñaba el
  frame con el que se eligió el recorte (§7).
- Validación **0 errores** de estructura, runtime, layout y motion · **41/41 WCAG AA**.
- **Verificado sobre el MP4**, no sobre el plan: duración **56.933 s** exacta, 50.8 MB,
  sin negro real (`blackdetect pix_th=0.03`), pico por canal **−2.2 / −2.4 dB** y
  **0 muestras saturadas** (`astats`), música presente en la cola a −31.3 dB donde el corte
  de voz sola está a −61.3.
  · Barrido de luma cada ~4 s: banda `speaker` [960,1920] entre **253 y 255** en los 15
    puntos (umbral 200) — el hablante nunca desaparece detrás del takeover; banda `top`
    nunca por debajo de **174**, muy lejos del suelo grafito (~25), así que
    `check_band_top_covered` se cumple también en píxeles.
  · Borde superior de la caja de cara (Haar sobre 6 frames): **y1092–y1120**, 132–160 px de
    margen sobre el techo de la banda — el gate predecía y1099.
  · Último frame con el CTA ENCENDIDO (la trampa 6c), comprobado extrayéndolo con `-sseof`.
- Copia publicable en `VIDEOS EDITADOS/video-16-claude-canva-reel.mp4`.
- Suite: **408 passed, 11 skipped** (+22 tests nuevos, con el camino de FALLO de cada gate).


**Pieza 17 — terminada.** `videos/17/output.mp4`, copia en
`VIDEOS EDITADOS/video-17-cv-ia-reel.mp4`. REEL 9:16, **59.87 s**, 42.2 MB,
H.264 + AAC. Cómo usar IA para mejorar un CV de verdad · CTA **CV**.

- ⚠ **`VIDEOS ORIGINALES/3` → pieza 17**, no pieza 3 (que es el reel de las
  monedas, de agosto). La tercera vez que avisa esta nota y la tercera que hacía
  falta.
- Fuente `VIDEOS ORIGINALES/3/pantalla.MOV`: 63.95 s, HEVC **SDR bt709**,
  1080×1920, rot 0 → corte **59.88 s** (6 % fuera, 4 cortes: tres pausas de fin
  de oración y 3.18 s de cola muerta). **El take más limpio de la serie.**
  138 palabras, confianza 0.99. Cara `chin_frac` **0.4422**, `top_frac`
  **0.2594**, 48/48 muestras.
- **Los tres avisos de alineación imposible eran falsos positivos**, y
  comprobarlo costó tres re-transcripciones sueltas: «currículum.» (208 ms,
  19.2 síl/s) volvió en **214 ms**, «para» en 171 frente a 160 y «como» en 166
  frente a 161 — los tres a menos de 35 ms de los originales. No se empalmó
  nada. La lección de las piezas 12, 14 y 16 otra vez: mirar puede confirmar que
  no pasa nada, y eso también es un resultado.
- `audit-breaths` en verde a la primera: 4 islas sin voz, **0 fuera de un span
  de palabra**.
- **Catorce visuales, y la rejilla de pasos es la espina**:

  | t | Función | Visual | Técnica |
  | --- | --- | --- | --- |
  | 2.66–5.96 | «lo subes a una IA y escribes mejora mi currículum» | el CV adjunto y el prompt pobre | `claude_prompt` + `attachment` |
  | 5.96–10.48 | «estás desaprovechando casi todo» | el mismo CV dos veces, y el `=` | `cv_echo` |
  | 10.48–15.13 | «lo dividiría en 4 pasos» → «Primero: diagnóstico» | cuatro huecos numerados; se llena el 01 | `step_grid` |
  | 15.13–19.14 | «el currículum contra la vacante, y los desajustes» | los dos documentos y los tres aros | `cv_vs_offer` |
  | 19.14–22.58 | «Segundo: keywords y competencias» | se llena el 02 | `step_grid` |
  | 22.58–29.44 | «varias ofertas… cuáles faltan» | ofertas → chips → huecos | `offer_stack` |
  | 29.44–31.24 | «Tercero, reescritura» | se llena el 03 | `step_grid` |
  | 31.24–38.39 | «en lugar de era responsable de… resultado, métrica e impacto» | la línea tachada y la reescrita | `rewrite_line` |
  | 38.39–40.16 | «Y cuarto, entrevista» | se llena el 04 | `step_grid` |
  | 40.16–44.92 | «dale la descripción del puesto» | la MISMA card, otro adjunto | `claude_prompt` |
  | 44.92–48.08 | «repreguntando cuando una respuesta sea débil» | la respuesta floja y la repregunta | `interview_chat` |
  | 48.08–52.04 | «analizar, detectar huecos, reescribir, practicar» | la misma rejilla, los cuatro verbos | `step_grid` |
  | 55.72–57.78 | «tengo los 4 prompts preparados» | la cifra sola | `keyword_hero` |
  | 57.78–fin | «comenta CV» | el comentario simulado | `comment_ui` |

- **Las dos cards de chat vuelven a ser la estructura**, como en la 16: la misma
  card, y lo único que cambia es qué se le da —un CV y «mejora mi currículum» la
  primera, la descripción del puesto y un rol la segunda—. Ese contraste es el
  argumento entero de la pieza.
- **El hook y la tesis se quedan a plano lleno** (`kind: "full"`), los dos
  momentos en los que un gráfico le roba el argumento. Son los únicos dos tramos
  con keyword única; el resto va en karaoke, como pide el triband.
- **La banda `top` se cubre entera sosteniendo**, nunca adelantando: `cv_echo`
  se estira hasta «4» (10.481) y la rejilla hasta «currículum» (15.129), en vez
  de que el comparador entre antes de que se nombre la vacante.
- 10 encuadres, **0 tarjetas** (la banda de arriba hace el trabajo y un rótulo
  competiría), 40 bloques de subtítulo, 29 efectos en 2 pistas + cama musical.
- Validación **0 errores** de estructura, runtime, layout y motion ·
  **59/59 WCAG AA**, más el par que saca del muestreo el
  `data-layout-allow-occlusion` del tachado, medido a mano con
  `tokens.contrast()`: `text3`/`surface` **5.76:1** y `alert`/`surface`
  **5.79:1**.
- **Verificado sobre el MP4**: duración **59.867 s** exacta, sin negro real
  (`blackdetect pix_th=0.03`), pico por canal **−2.99 / −2.96 dB** (nada puede
  saturar por debajo de 0 dBFS).
  · Barrido de luma en 14 puntos: banda `speaker` [960,1920] entre **249 y 253**
    (umbral 200) — el hablante nunca desaparece; banda `top` a 255 salvo en la
    rejilla de huecos (**159**, el borde discontinuo), muy lejos del suelo
    grafito (~25).
  · Borde superior de la caja de cara (Haar sobre 6 frames dentro de tramos
    `band`): **y1100–y1113**, 140–153 px de margen sobre el techo de la banda.
  · Tinta más baja del subtítulo: **y1221** en plano lleno (tope y1536) y
    **y833** en triband (gate y944).
  · Último frame con el CTA **encendido** (la trampa 6c), extraído con `-sseof`.
- ⚠ **Medir la ganancia de voz sobre TODAS las ventanas con voz la sobreestima,
  y converge en las más fuertes.** Mediana sobre las 449 ventanas de 100 ms con
  voz: **0.743**; filtrando por el p50 de energía: 0.723; p70: 0.711; p85:
  0.704; **p95: 0.701**, frente a 0.700 declarada. Lo que sobra en las ventanas
  flojas es la cama musical y el residuo del códec sumando por debajo — la misma
  física que documenta la pieza 12 cuando el filtro adaptado encontró efectos
  que la envolvente no veía. **La razón entre dos archivos se mide donde la
  señal domina al fondo**, no en promedio.
- ⚠ **Una compilación con la salida en `/dev/null` es una compilación que puede
  fallar sin que nadie se entere.** `build-composition.py … >/dev/null 2>&1 &&
  npx hyperframes check` cortocircuitó en un `UnboundLocalError` y el `check`
  siguiente validó —y dio por bueno— el `index.html` ANTERIOR. El síntoma fue
  desconcertante: el CSS emitido no contenía un cambio que sí estaba en el
  fuente. **La salida de una compilación se mira siempre.**
- Golden en `tests/golden/17.plan.json`. La suite pasa de **408 a 430 tests**:
  22 de los seis componentes nuevos, casi todos sobre fallos que `check` daba
  por buenos y que solo se vieron extrayendo el frame.

---

**Pieza 18 — terminada.** `videos/18/output.mp4`, copia en
`VIDEOS EDITADOS/video-18-motion-hyperframes-reel.mp4`. REEL 9:16, **53.5 s**,
H.264 + AAC. Motion design con Claude Code y HyperFrames · CTA **MOTION**.

- ⚠ **`VIDEOS ORIGINALES/4` → pieza 18**, no pieza 4 (que es el reel del ERP de
  inventario, de agosto). La cuarta vez que esta nota hace falta.
- Fuente `VIDEOS ORIGINALES/4/pantalla.MOV`: 64.24 s, HEVC **SDR bt709**,
  1080×1920, rot 0 → corte **53.48 s** (17 % fuera, 11 cortes). 138 palabras.
  Cara `chin_frac` **0.4768**, `top_frac` **0.2911**, 48/48 muestras.
- **La pieza la encargó el usuario con `instrucciones.md`**, y las cuatro
  decisiones abiertas se le preguntaron ANTES de construir nada (paso 3b):
  keyframes a mano para el hook · la grabación real en «de HeyGen» y en «cambia
  el flujo» · los cuatro ejemplos SUCEDIÉNDOSE con corte duro · la animación
  espectacular encima de la idea gris para la tesis. Eligió las cuatro
  propuestas, incluida la última sabiendo que choca con «quietud antes del
  clímax».
- ⚠ **Dos de los diez avisos de alineación imposible eran REALES**, y eso
  invierte la lección de la 17. «HeyGen» volvió de la re-transcripción suelta
  en 8.765–9.041 frente a 9.009–9.131 (**244 ms** de arranque perdido, con un
  hueco de 227 ms entre «de» y «HeyGen» que era parte de la palabra), y
  «Antes» en 24.348–24.659 frente a 24.496–24.657. Esos **148 ms** son
  exactamente el blob audible sin transcribir que `refine-timings` marcaba en
  24.275–24.485: **los dos avisos eran el mismo hecho visto desde dos medidas
  distintas.** Con el borde corregido, el corte que separa «flujo.» de «Antes»
  pasó de terminar en 24.296 —dentro del ataque— a 24.08. Los otros ocho
  volvieron a menos de 65 ms: falsos positivos. **La conclusión de la pieza
  anterior no se hereda; se vuelve a medir.**
- El modelo oye «Cloud Code» y «Hyperframe». Se corrige el TEXTO de cuatro
  palabras (el audio no se toca) para que el subtítulo escriba las marcas
  bien, como la 15 con Kokonut UI.
- `audit-breaths` en verde a la primera: 13 islas sin voz, **0 fuera de un
  span de palabra**.
- **Quince visuales, y la banda `top` no se queda vacía ni un instante**: el
  `end` de cada uno ES el `start` del siguiente, sin un solo hueco que tapar
  sosteniendo. Es la primera pieza en la que eso sale sin esfuerzo, porque el
  usuario pidió material para TODOS los beats.

  | t | Función | Visual | Técnica |
  | --- | --- | --- | --- |
  | 0.00–6.30 | «animar todo a mano era demasiado trabajo» | el vídeo muerto y los rombos cayendo uno a uno | `keyframe_grind` |
  | 6.30–8.17 | «un plugin para Claude Code llamado HyperFrames» | las dos marcas, con el hueco dibujado | `tool_pair` |
  | 8.17–9.42 | «de HeyGen» | la landing REAL | grabación + `tool_recording` |
  | 9.42–19.58 | «describir · composiciones · generar · llevar» | el editor con el chat debajo | `agent_editor` |
  | 19.58–21.09 | «eso cambia bastante el flujo» | «Motion, sound & effects» de la doc REAL | grabación + `tool_recording` |
  | 21.09–28.67 | «podías descartarla: no sabías hacerla o no compensaba» | la idea y sus dos salidas tachadas | `idea_fate` |
  | 28.67–30.88 | «ahora puedes prototiparla con IA» | LA MISMA idea, viva | `idea_fate` (revive) |
  | 30.88–32.40 | «textos que entran» | cada palabra en su palabra | `motion_demo` text |
  | 32.40–34.06 | «gráficos animados» | barras que crecen y una línea que se dibuja | `motion_demo` chart |
  | 34.06–35.01 | «captions» | el karaoke del triband, como ejemplo de sí mismo | `motion_demo` captions |
  | 35.01–37.81 | «elementos que reaccionan al audio» | la onda, en tres golpes | `motion_demo` audio |
  | 37.81–41.46 | «ninguna herramienta arregla… el criterio» | las cuatro quietas y un hueco que solo llena «criterio» | `motion_demo` recap |
  | 41.46–48.46 | «una animación espectacular encima de una idea aburrida» | el espectáculo que se apaga sobre la tarjeta gris | `idea_veneer` |
  | 48.46–51.29 | «te mando HyperFrames» | la marca sola | `tool_card` |
  | 51.29–fin | «comenta MOTION» | el comentario simulado | `comment_ui` |

- **La grabación es la WEB de HyperFrames, no su Studio**, así que el editor
  con el chat que pidió el usuario tuvo que ser un mockup. La regla de oro de
  §7 manda usar la grabación real *cuando existe*; para ese beat no existía.
- ⚠ **El tramo de la doc cayó en la trampa de la pieza 16 y se arregló
  MIDIENDO.** El primer montaje (at=23.5, 1.9 s) tenía un frame de salida que
  ya se había ido a «Workflows & integrations». En vez de tantear otro recorte,
  una correlación cruzada columna a columna entre frames dio el mapa del
  scroll: salto de ~140 px entre 23.6 y 23.9, y **meseta perfecta de 23.9 a
  25.4** (seis muestras con desplazamiento idéntico). El tramo vive entero
  dentro de esa meseta. **Mirar dos frames confirma o desmiente el recorte que
  ya elegiste; medir te dice dónde está el bueno.**
- Marca nueva vendorizada: `hyperframes`, desde `hyperframes.heygen.com`. ⚠
  `hyperframes.dev/favicon.svg` responde **200** y NO es la marca — devuelve un
  icono titulado «EdgeNova App Icon». Un 200 no verifica que el archivo sea el
  logo; eso solo lo dice abrirlo. Trae dos gradientes con id propio y se
  inlinea TRES veces en la pieza, así que el `uid=` de §14 no es teórico aquí.
- 14 encuadres, **0 tarjetas**, 35 bloques de subtítulo, 38 efectos en 3 pistas
  + cama musical.
- Validación **0 errores** de estructura, runtime, layout y motion ·
  **42/42 WCAG AA**, más los siete pares que sacan del muestreo los
  `data-layout-allow-*` de `idea_veneer` y el destello de `idea_fate`, medidos
  a mano con `tokens.contrast()`: lo peor es blanco/`violet` **4.35:1** sobre
  texto de 92 px y peso 900 (AA-grande, umbral 3:1).
- ⚠ **El 💡 de `idea_fate` tiraba la pieza entera.** El navegador pinta un
  emoji con su propia paleta, pero el linter lee el `color` heredado del
  elemento —negro, al no declararlo— y midió **1.11:1** contra el grafito. Se
  veía perfecto en el frame. Sustituido por un destello dibujado en
  `currentColor`, que además lo tiñe el estado de la tarjeta: **6.35:1**
  apagado y **6.70:1** vivo.
- **Verificado sobre el MP4**: 53.50 s / 1605 frames, sin negro real
  (`blackdetect pix_th=0.03`), pico por canal **−2.29 / −2.63 dB**.
  · Barrido de luma en 19 puntos: banda `speaker` **254–255** siempre (el
    hablante nunca desaparece) y banda `top` nunca por debajo de **152** —
    la petición de «que siempre se muestre algo» se cumple medida, no de oído.
  · Borde superior de la caja de cara (Haar sobre 8 frames): **y1158–y1180**,
    198–220 px de aire bajo el techo de la banda `speaker`.
  · Tinta del subtítulo: el máximo llega a y945 contra un gate de y944, pero
    **cero píxeles de tinta plena (>220) por debajo de y944** — es un solo
    píxel de antialias a luma 154, y quedan **15 px de grafito limpio** hasta
    la banda del hablante. El gate apretando bien, como el margen de 5 px de
    la 17.
  · Último frame con el CTA **encendido** (la trampa 6c), luma 255.
  · Ganancia de voz: mediana sobre las 467 ventanas con voz **0.719**; p50
    0.706 · p70 0.704 · p85 0.703 · **p95 0.703** frente a 0.700 declarada.
    La misma convergencia que documenta la 17.
- ⚠ **Y el arreglo que se llevó por delante diecisiete piezas: el ATAQUE de los
  efectos** (§12). El filtro adaptado daba correlación CERO para `error`; la
  plantilla con la que se correlaba era silencio puro, porque `error.mp3` trae
  **604 ms** de cabecera. 16 de los 19 efectos la tienen. `build_sfx` ahora
  adelanta el `data-start` esa cabecera: **34 de los 38 efectos de esta pieza
  estaban sonando tarde**. No es un arreglo de la pieza 18 — es del sistema, y
  lo que lo destapó fue un test que fallaba por el motivo equivocado.
- La suite pasa de **430 a 479 tests**: 37 de los cinco componentes nuevos, 7
  del ataque de los efectos y 4 que fijan qué garantiza —y qué no—
  `check_band_top_covered`, más el roster de marcas vendorizadas.


---

**Pieza 19 — terminada.** `videos/19/output.mp4`, copia en
`VIDEOS EDITADOS/video-19-agency-agents-reel.mp4`. REEL 9:16, **58.87 s**,
53.3 MB, H.264 + AAC. Agency Agents: una agencia entera dentro de Claude
Code · CTA **AGENCY**.

- ⚠ **`VIDEOS ORIGINALES/7` → pieza 19**, no pieza 7. La quinta vez que esta
  nota hace falta (1→15, 2→16, 3→17, 4→18, 7→19). Las carpetas 5 y 6 siguen
  sin editar, así que el número de carpeta ya ni siquiera va en orden.
- Fuente `VIDEOS ORIGINALES/7/pantalla.MOV`: 72.72 s, HEVC **SDR bt709**,
  1080×1920, rot 0 → corte **58.87 s** (19 % fuera, 14 cortes). 144 palabras,
  confianza 0.987. Cara `chin_frac` **0.4778**, `top_frac` **0.3031**, 48/48
  muestras. `anchor` **0.42**.
- **La pieza la encargó el usuario con `instrucciones.md`**, y la frase que la
  define no es sobre un beat sino sobre el lenguaje: «me gusta que las
  animaciones también lleven iconos y así, no solo textos y recuadros». De ahí
  sale `icons.py` y los cinco componentes que lo usan (§7). Las cuatro
  decisiones abiertas se le preguntaron ANTES de construir nada (paso 3b):
  triband desde el segundo 0 · mockup de gestor de escritorio para la app ·
  cinco chips con icono, uno por palabra · la lectura fácil tachada y el
  problema partiéndose en tres. Eligió las cuatro propuestas.
- ⚠ **Los cuatro avisos de alineación imposible eran falsos positivos, y el
  cuarto solo se pudo descartar MIDIENDO.** Tres volvieron de la
  re-transcripción suelta a menos de 35 ms. «especialistas.» volvió en
  4.746–5.674 frente a 4.782–5.217: **457 ms más larga**, lo que habría
  convertido el hueco de 516 ms anterior a «Se» en uno de 114 y movido el
  corte. La envolvente y `voicing.py` sobre ese tramo dicen que entre 5.22 y
  5.71 el audio está en el **suelo de ruido** (−52 a −71 dB, umbral −45):
  silencio real. **La re-transcripción suelta estiró la palabra sobre el
  silencio y el transcript largo tenía razón.** La 18 enseñó que el aislado
  puede acertar donde el largo falla; la 19 enseña el caso contrario, y que
  quien desempata no es la segunda transcripción sino el audio.
- El modelo oye «Cloud Code», «Agency Agent.» y «agency». Se corrige el TEXTO
  de tres palabras (el audio no se toca), como la 15 con Kokonut UI.
- `audit-breaths` en verde a la primera: 7 islas sin voz, **0 fuera de un span
  de palabra**.
- **Catorce visuales**, y el `start` de cada uno es la palabra de su primer
  elemento (§4):

  | t | Función | Visual | Técnica |
  | --- | --- | --- | --- |
  | 0.00–6.19 | «un proyecto open source que convierte Claude Code en una agencia llena de especialistas» | el marco y los doce huecos, la marca y la rejilla llenándose | `agent_swarm` fanout |
  | 6.19–7.82 | «Se llama Agency Agents» | la marca sola | `tool_card` |
  | 7.82–10.46 | «un único asistente haciendo de todo» | uno, y lo que se le echa encima | `agent_swarm` solo |
  | 10.46–13.75 | «reúne agentes con funciones diferentes» | las 13 divisiones REALES | grabación + `tool_recording` |
  | 13.75–18.76 | «frontend · marketing · contenido · comunidad · ingeniería» | un chip con icono por palabra | `chip_grid` + `icons_` |
  | 18.76–21.09 | «sus propias instrucciones» | «Roles think» de la página REAL | grabación + `tool_recording` |
  | 21.09–23.22 | «forma de trabajar y entregables» | los tres chips del kit | `chip_grid` + `icons_` |
  | 23.22–27.38 | «no necesitas utilizar todos» | los 146, y 143 bajando | `agent_swarm` roster |
  | 27.38–32.04 | «un pequeño equipo según la tarea» | tres, con su icono | `agent_swarm` team |
  | 32.04–39.92 | «plantea · construye · busca problemas» | la cadena de tres | `flow_steps` + `icons_` |
  | 39.92–45.62 | «una aplicación de escritorio» | la ventana nativa con su lista | `desktop_manager` |
  | 45.62–54.55 | «no un empleado gratis: dividir problemas entre especialistas» | la lectura tachada y el reparto | `split_problem` |
  | 54.55–56.88 | «si quieres el repo» | el hero REAL con «View on GitHub» | grabación + `tool_recording` |
  | 56.88–fin | «comenta AGENCY» | el comentario simulado | `comment_ui` |

- **La grabación NO tiene la aplicación de escritorio**, que es el beat más
  largo del guion (5.7 s): la web resuelve la instalación con una línea de
  terminal. La regla de oro de §7 manda usar la grabación real *cuando
  existe*; para ese beat no existía.
- ⚠ **El hallazgo de los tours.** Las mesetas se midieron por correlación
  cruzada como en la 18, y la métrica descartó por «cambio» la ventana
  1.9–2.5 s del hero. Al mirarla: la maqueta **no se mueve**, lo que cambia
  son los CONTADORES de la propia página animándose (86→112→130→140 agentes,
  35k+→57k+ estrellas). Una medida de desplazamiento no distingue un scroll de
  un número subiendo, y esa ventana resultó ser la mejor del tour. **La
  métrica dice dónde mirar; lo que hay ahí lo dice el frame.**
- ⚠ **Dos tours necesitaron DOS RECORTES DE LA MISMA VENTANA QUIETA** porque
  el beat duraba más que la meseta (hero 1.30 s para 2.33; roles 1.70 para
  2.33) — el arreglo de Kokonut UI de la pieza 15. Y el gate de barras negras
  rechazó cuatro recortes: en el hero el contenido real vive en y 8..576.
- Marca nueva vendorizada: `agencyagents`. ⚠ **La trampa de `hyperframes.dev`
  otra vez y peor**: `favicon.svg`, `icon.svg`, `apple-touch-icon.png` y
  `logo.svg` responden **200 con `text/html`** — el fallback de la SPA. La
  única imagen real es `favicon.ico`. Y traía **fondo blanco OPACO** alrededor
  del tile redondeado, que sobre grafito habría pintado un cuadrado blanco: se
  le devolvió el alfa con un relleno por inundación desde las cuatro esquinas
  y se recortó al tile. `tile` #9C79DF, 5.25:1 contra `surface`.
- 14 encuadres, **0 tarjetas**, 38 bloques de subtítulo, 30 efectos en 2
  pistas + cama musical.
- Validación **0 errores** de estructura, runtime, layout y motion ·
  **36/36 WCAG AA**.
- **Verificado sobre el MP4**: **58.867 s** / 1766 frames, sin negro real
  (`blackdetect pix_th=0.03`), pico por canal **−3.31 / −3.31 dB**.
  · Barrido de luma **cada 0.5 s en 117 puntos** (no cada 2 s: un barrido
    grueso salta por encima de los relevos, que es donde vive el hueco): banda
    `speaker` **254–255** siempre — el hablante nunca desaparece. Banda `top`
    en suelo desnudo (luma ≤32) **33–166 ms por relevo**, o sea 1–5 frames, en
    los trece relevos.
  · Borde superior de la caja de cara (Haar sobre 9 frames): **y1131–y1175**,
    171–215 px de aire bajo el techo de la banda `speaker`. El gate predecía
    y1139.
  · Tinta plena del subtítulo: **y943** contra un gate de y944 — 1 px. El gate
    apretando exactamente, como los 5 px de la 17.
  · Último frame con el CTA **encendido** (la trampa 6c), luma 255.
  · Ganancia de voz: mediana sobre las 545 ventanas con voz 0.733; p50 0.705 ·
    p70 0.703 · **p85 0.700 · p95 0.698** frente a 0.700 declarada. La misma
    convergencia que documentan la 17 y la 18.
  · **30/30 efectos** localizados por filtro adaptado, desfase medio 9.7 ms y
    máximo 35 ms (un frame). ⚠ El `riser` daba 0.21 con plantilla de 300 ms y
    **0.82 con una de 1.6 s**: es una rampa de 10 s y 300 ms de ella no
    identifican nada — la lección del `chime` de la pieza 12, que sigue
    valiendo.
- La suite pasa de **479 a 554 tests**: 75 de los iconos, los tres componentes
  nuevos y las dos extensiones, con el camino de FALLO de cada gate (una
  variante desconocida de `agent_swarm`, un icono que no existe) y el test que
  fija que `chip_grid` y `flow_steps` **sin** `icons_` emiten exactamente el
  marcado de siempre — que es lo que deja intactas a las piezas 3, 4, 11 y 16.


---

**Pieza 20 — terminada.** `videos/20/output.mp4`, copia en
`VIDEOS EDITADOS/video-20-moneyprinterturbo-reel.mp4`. REEL 9:16, **55.13 s**,
51.7 MB, H.264 + AAC. MoneyPrinterTurbo: automatizar vídeos faceless con IA ·
CTA **TURBO**.

- ⚠ **`VIDEOS ORIGINALES/9` → pieza 20**, y la numeración de la carpeta ya ni
  siquiera va en orden: 1→15, 2→16, 3→17, 4→18, 7→19, 9→20, con la 5, la 6 y
  la 8 todavía sin editar. Sexta vez que esta nota hace falta.
- Fuente `VIDEOS ORIGINALES/9/pantalla.MOV`: 67.95 s, HEVC **SDR bt709**,
  1080×1920, rot 0 → corte **55.13 s** (19 % fuera, 17 cortes). 151 palabras,
  confianza 0.988. Cara `chin_frac` **0.4795**, `top_frac` **0.3089**, 48/48
  muestras. `anchor` **0.42**.
- ⚠ **EL HALLAZGO DE LA PIEZA no estaba en ninguno de los ocho avisos de
  alineación: estaba en el aviso de «sonido audible sin transcribir».**
  `refine-timings` marcó 330 ms en 35.925–36.255 con pico −21.3 dB y lo
  clasificó como voz. Lo era — armonicidad **0.74–0.80**, ataque limpio desde
  −71 dB— y es la palabra **«No.»**, el beat que sostiene el guion entero.
  AssemblyAI la había puesto en 37.212–37.277: **1.2 s tarde y de 65 ms**. Tal
  cual venía, `plan-cuts` veía una pausa de 2.1 s entre «dinero?» y «No.» y la
  colapsaba — el corte se comía la palabra. Con el span medido, los cortes 11
  y 12 la dejan intacta. **Ese aviso no es solo un detector de respiraciones:
  también encuentra palabras que el transcript colocó en otro sitio.**
- ⚠ **Y los dos avisos reales de alineación enseñan la lección desde los dos
  lados.** «contenido.» acababa 117 ms antes de que su vocal se apagara
  (medido: sigue sonorizada hasta 30.25). Y en «Optimizar» el pase AISLADO
  devolvió 42.536 mientras `refine-timings` decía 42.280 — **y el audio da la
  razón al segundo**: salta de −75 dB a −35 exactamente en 42.28, o sea que el
  aislado se comió la plosiva inicial. En la 19 el aislado estiró una palabra
  sobre silencio; aquí recortó un ataque. **La re-transcripción suelta es una
  segunda opinión, no un árbitro.** Los otros seis avisos, falsos positivos.
- El modelo oye «Money Printing Turbo» (tres palabras) y «turbo». Se funden
  las tres en `MoneyPrinterTurbo` conservando el span y se pasa el CTA a
  `TURBO`. ⚠ **Y una que NO se corrige**: el guion escrito dice «Automatizar
  la producción no automatiza el criterio» y él dice **«Optimizar»**. El
  aislado lo confirma. El subtítulo transcribe lo DICHO — cambiarlo sería
  reescribirle la frase, no arreglarle una marca.
- ⚠ **`instrucciones.md` llegó TRUNCADO a media palabra** (302 bytes, acaba en
  «Qu»), así que su última frase se desconoce. Se montó con lo legible y se le
  avisó al entregar; las cuatro decisiones abiertas se preguntaron antes de
  construir nada (paso 3b) y eligió: el botón que se pulsa y no da nada · la
  cadena de siete pasos con icono · solo las dos ventanas quietas de la
  grabación · la máquina escupiendo vídeos a cero.
- `audit-breaths` en verde a la primera: 3 islas sin voz, **0 fuera de un span
  de palabra**.
- **La espina de la pieza es la CADENA DE PRODUCCIÓN**, que aparece tres veces
  con la misma geometría: sin nombres en el hook, llenándose palabra a palabra
  en la enumeración, y con un hueco delante en la tesis.

  | t | Función | Visual | Técnica |
  | --- | --- | --- | --- |
  | 0.00–5.98 | «automatiza casi todo el flujo de un vídeo faceless» | las siete etapas sin nombre, y lo que producen | `video_pipeline` manual |
  | 5.98–9.24 | «Se llama MoneyPrinterTurbo» | la cabecera REAL del repo, 125k estrellas | grabación + `tool_recording` |
  | 9.24–21.72 | «tema · guion · material · narración · subtítulos · música · render» | las mismas siete casillas, una por palabra | `video_pipeline` auto |
  | 21.72–25.78 | «diferentes formatos y varias versiones» | la galería REAL «Portrait 9:16» | grabación + `tool_recording` |
  | 25.78–30.02 | «¿un botón para ganar dinero?» → «No.» | se pulsa y la bandeja sigue vacía | `money_button` |
  | 30.02–37.71 | «la parte que casi siempre se omite… el criterio» | la misma cadena, y el hueco de delante | `video_pipeline` gap |
  | 37.71–45.42 | «una forma más rápida de crear un vídeo que nadie quiere ver» | la máquina escupiendo vídeos a cero | `video_output` |
  | 45.42–50.08 | «comprimir la ejecución, no saltarte la estrategia» | una se encoge, la otra no se toca | `tradeoff_bars` |
  | 50.08–53.39 | «el proyecto y mi flujo» | la card del repo | `tool_card` |
  | 53.39–fin | «comenta TURBO» | el comentario simulado | `comment_ui` |

- ⚠ **La grabación solo tenía 2.5 s de metraje quieto.** Es la página de GitHub
  del repo y son 17.5 s de scroll continuo por el README: el WebUI, la API,
  los patrocinadores y la lista de features pasan de largo sin que la página se
  pare en ninguno. Mesetas medidas: **solo dos**, 0.00–1.10 y 15.90–17.30. El
  usuario eligió usar solo esas dos y dibujar el resto.
- ⚠ **Y la meseta que da el detector es CONSERVADORA.** Medido frame a frame
  sobre el recorte real, la cabecera es idéntica píxel a píxel hasta **1.03**,
  deriva 5 px a 1.13, 24 a 1.23 y se pierde del todo a 1.63 — así que tramos
  de 1.09 s caben dentro de una deriva invisible aunque el detector cierre la
  meseta en 1.10, porque exige correlación ≥0.99.
- ⚠ **Los tres recortes de la cabecera son un EMPUJE DE CÁMARA, no tres
  encuadres.** La cabecera solo tiene 706 px de alto y todo está apilado, así
  que bajar el recorte da frames casi idénticos; y ninguno puede ser más
  estrecho de 880 px desde x330, porque la línea de descripción mide x 354..1197
  y cualquier recorte más cerrado la parte por la mitad. Se vio en el frame.
- Marca nueva vendorizada: **`github`** (Simple Icons v16). MoneyPrinterTurbo
  no tiene marca propia —es un REPO, no un producto con logo— y la marca
  honesta de un repo es la de GitHub, que es donde vive. Inventarle un
  logotipo habría sido dibujar una identidad que no existe.
- 10 encuadres, **0 tarjetas**, 38 bloques de subtítulo, 28 efectos en 3
  pistas + cama musical.
- Validación **0 errores** de estructura, runtime, layout y motion ·
  **27/27 WCAG AA**.
- **Verificado sobre el MP4**: **55.133 s** / 1654 frames, sin negro real
  (`blackdetect pix_th=0.03`), pico por canal **−3.15 / −3.14 dB**.
  · Barrido de luma cada 0.5 s en 110 puntos: banda `speaker` **254–255**
    siempre. Banda `top` en suelo desnudo (luma ≤32) **≤199 ms (6 frames)** en
    los nueve relevos. ⚠ El primer montaje daba **733 ms** en el relevo a
    `video_output`, otra vez por lo mismo que la pieza 19: el visual abría en
    «Si» y su primer elemento esperaba a «tema». Cerrado sosteniendo el
    tablero anterior — que además encaja, porque el criterio es justo lo que
    la frase dice que falta.
  · Coronilla (Haar sobre 8 frames): **y1149–y1162**, 189–202 px de aire bajo
    el techo de la banda. El gate predecía y1150.
  · Tinta plena del subtítulo: **y943** contra un gate de y944 — 1 px, el gate
    apretando exactamente como en la 19.
  · Último frame con el CTA **encendido** (la trampa 6c), luma 255.
  · Ganancia de voz: mediana 0.740 sobre 518 ventanas; p50 0.708 · p70 0.703 ·
    **p85 0.700 · p95 0.699** frente a 0.700 declarada.
  · **28/28 efectos** localizados por filtro adaptado, desfase medio 8.5 ms y
    máximo **15.9 ms** (medio frame). El `riser` y el `chime` se correlan con
    plantilla de 1.6 s, no de 300 ms: la lección de la pieza 12 sobre cubrir
    el efecto y no el ataque que uno espera que tenga.
- La suite pasa de **554 a 590 tests**: 36 de los cuatro componentes nuevos y
  sus nueve iconos, incluido el camino de FALLO que destapó que
  `video_pipeline` renderizaba una cadena vacía en silencio con una variante
  mal escrita.

---

## 14. Reglas duras

**Hacer**
- Correr `detect-format.sh` antes de crear el proyecto. El formato se mide.
- Medir la cara, no estimarla.
- **Cuadrar el transcript con el audio antes de cortar** (`refine-timings.py`), y
  re-transcribir suelto el tramo que salga con la alineación rota.
- **Cortar con `--audio`** (`plan-cuts.py … --audio assets/audio/<n>.flac`): la pausa
  que queda tiene que ser SILENCIO, no una respiración.
- **Correr `audit-breaths.py` antes de seguir** (paso 4b). Sale con código 1 si queda
  una respiración en el corte, y ahí se para el flujo: **cero islas sin voz fuera de un
  span de palabra, o no se entrega.** Audita el CORTE —voz sola— con el umbral de la
  FUENTE; el MP4 mezclado da falsos positivos porque la cama musical tampoco tiene tono.
- Cada beat clavado a su palabra, sacado del transcript remapeado.
- **Recortar la grabación hasta que el flujo se lea**: salida cuadrada, sin navegador
  alrededor, y las coordenadas de clicks y cajas medidas, no estimadas.
- Un visual por función, con la técnica variada.
- Cambiar de imagen cada 1–2.5 s. El creador es el hilo conductor.
- Renderizar con `--sdr` (y con el LUT calibrado si la fuente es HLG).
- Verificar el resultado **sobre el MP4**, extrayendo frames y midiendo el audio.
- Dejar libre el 20 % inferior del lienzo en REEL.
- **Verificar el recorrido de pantalla en el frame de ENTRADA y en el de SALIDA de cada
  tramo**, no solo en el que se usó para elegir el recorte: la página scrollea debajo.
- **Pasar `uid=` a `logos.mark()`.** Un SVG de marca con gradientes o clip-paths propios
  inlineado dos veces se renderiza vacío la segunda, y el JSON no lo dice.
- **Mirar la salida de `build-composition.py`.** Mandarla a `/dev/null` deja que una
  compilación fallida pase por buena: el `check` siguiente valida el `index.html`
  anterior y todo parece en orden (pieza 17).
- **Medir la ganancia de voz donde la señal domina al fondo** (p95 de energía), no en
  promedio: la cama musical suma por debajo y la sobreestima (pieza 17).
- **Verificar la grabación de pantalla con la maquetación MEDIDA, no mirada.** Una
  correlación cruzada columna a columna entre frames dice en qué tramos la página está
  quieta de verdad; elegir el recorte a ojo y comprobar dos frames no encuentra la meseta,
  solo confirma o desmiente el tramo que ya se eligió (pieza 18).
- **Empezar un visual en la palabra de su PRIMER elemento, no en la del beat.** El
  retraso del entrante se suma a los 130 ms del relevo en vez de esconderse dentro: en la
  pieza 19 seis relevos pasaban entre 200 y 663 ms con la banda en suelo grafito y
  `check_band_top_covered` los daba por buenos, porque mide cobertura declarada y no luma.
- **Barrer la luma de la banda `top` cada 0.5 s, no cada 2.** Un barrido grueso salta
  justo por encima de los relevos, que es donde vive el hueco (piezas 15–18 lo midieron
  así y por eso no lo vieron).
- **Probar un icono al TAMAÑO en que se va a ver.** Cinco de los dieciséis de la pieza 19
  compilaban perfectos y no se reconocían a 40 px.
- **Leer el aviso de «sonido audible sin transcribir» como una PALABRA posible, no solo
  como una respiración.** En la pieza 20 ese aviso era el «No.» del guion —330 ms,
  armonicidad 0.74-0.80, pico −21 dB— y AssemblyAI lo había colocado 1.2 s más tarde:
  `plan-cuts` veía una pausa de 2.1 s y se comía la palabra que sostiene la pieza.
- **Re-transcribir suelto TODO tramo con alineación imposible.** En la 17 los tres avisos
  eran falsos positivos y en la 18 dos de diez eran reales, uno de ellos un corte sobre el
  ataque de una palabra. La conclusión no se hereda de la pieza anterior.

**No hacer**
- Estilizar el metraje. El color reproduce el original. El usuario lo nota.
- Tapar la cara con subtítulos.
- **Estirar el borde de una palabra sobre un sonido que no tiene tono.** Suena, y hasta
  suena fuerte, pero es una respiración — y una vez dentro del span ya no la ve nadie.
- Fiarse de la envolvente para decidir QUÉ es un sonido. Dice cuánto, no qué.
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
- **Programar un efecto en el tiempo de su beat sin mirar su cabecera.** Lo que cae ahí es
  el principio del FICHERO, y 16 de los 19 traen silencio delante (§12). Lo arregla
  `build_sfx` solo; lo que no se puede es volver a escribir `data-start = beat`.
- **Meter un emoji en un mockup.** El navegador lo pinta con su propia paleta pero el
  linter lee el `color` heredado, que sin declarar es negro: el 💡 de `idea_fate` daba
  **1.11:1** contra el grafito y tiraba la pieza entera, viéndose perfecto en pantalla. Un
  glifo dibujado en `currentColor` lo tiñe el estado del componente y además se puede medir.
- **Escribir un selector ya prefijado en un mockup.** `build_visuals` le antepone
  `.viz[data-viz-id="…"]`; duplicado, GSAP no encuentra el destino y `check` lo cuenta como
  aviso de runtime con 0 errores — el gesto no ocurre y nada falla (pieza 19).
- **Tratar la re-transcripción suelta como un árbitro.** Es una segunda opinión: en la
  pieza 19 estiró una palabra sobre silencio y en la 20 se comió la plosiva inicial de
  «Optimizar», dando la razón al pase largo. **El árbitro es el audio** (`voicing.py` +
  la envolvente), que es lo único que distingue un ataque de un silencio.
- **Fiarse de una medición de desplazamiento para decidir si una grabación está quieta.**
  Una correlación cruzada no distingue un scroll de un CONTADOR de la página animándose:
  en la pieza 19 descartó por «cambio» la ventana 1.9–2.5 s, que resultó ser la mejor del
  tour (las cifras reales trepando). La métrica dice dónde mirar; lo que hay ahí lo dice el
  frame.
- **Dar por buena una animación sin mirar el frame.** Los dos bugs de la pieza 16 —la marca
  vacía y el CTA apagándose— compilaban limpios, pasaban `check` con 0 errores y se veían
  en un snapshot.
