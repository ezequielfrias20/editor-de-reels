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
| 3 | Planificar cortes | `scripts/plan-cuts.py transcripts/2.json cuts/2.json <dur_real> --audio assets/audio/2.flac` |
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
`keyword_hero` · `flow_steps` · `comment_ui` · `chat_unanswered` · `screen_panel` ·
`browser_frame` · `hud`.

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
