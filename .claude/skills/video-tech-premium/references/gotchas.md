# Trampas — todas ya pagadas una vez

Casi todas comparten la misma firma: **el navegador se ve bien y el MP4 sale mal.** Por
eso la verificación va siempre sobre el MP4.

---

## Renderer

### 1 · El fondo CSS de la página se descarta

La captura es por capas: `background` en `html`, `body` o `#stage` **no se pinta**, y todo
lo que no es video sale **negro** en el MP4.

El suelo tiene que ser un **elemento del DOM** (`#ground`). Los fondos de elementos
normales sí funcionan.

### 2 · El rect del `<video>` se resuelve una sola vez al cargar

Animar `width`/`height` con GSAP **no reescala el video**, solo lo recorta.

Por eso un **punch-in es un elemento nuevo**, no un tween: cada encuadre es un `<video>`
con geometría estática, y el salto entre dos es un corte duro. Vale también para los
`<video>` de un visual: geometría fija, su movimiento es el interno del clip.

### 3 · Media anidada en un elemento temporizado se congela

Un `<video>` o `<audio>` **no puede ir dentro** de un wrapper con `data-start`. Van
sueltos en el stage; el chrome se dibuja **alrededor**, no conteniéndolo.

### 4 · Un `<audio>` sin `id` se renderiza en silencio

El renderer descubre media **por `id`**. Sin él: se ve bien, valida la estructura, sale
mudo. Lo caza `media_missing_id`.

### 5 · La pista ordena el TIEMPO; el z-index ordena el APILADO

Es la trampa más cara de este sistema. `data-track-index` sirve para detectar solapes en
la línea de tiempo — **no decide qué se pinta encima**. Eso lo decide el z-index y, sin
él, el orden del DOM.

Como los `<video>` del metraje se emiten antes que los hosts de los visuales, el PiP del
creador quedaba **debajo** de cualquier mockup opaco. Y no se veía en las pruebas rápidas,
porque sobre la grabación de producto —cuyo host es transparente— se veía perfectamente.

Apilado explícito del sistema:

```
0 suelo   1 metraje   2 media de un visual   3 backdrop
4 tarjetas   5 takeover   6 PiP   7 subtítulos
```

Y en paralelo, dos clips a la vez en la **misma pista** sigue siendo un error de solape,
no un apilado.

### 6 · Un `off` que empieza a la vez que el takeover deja el frame vacío

Si el metraje se apaga en el mismo instante en que el gráfico empieza a fundir, durante
esos 0.15–0.25 s no hay nada debajo y el frame cae al suelo vacío. Se lee como un fallo,
no como una transición — y `blackdetect` lo caza:

```bash
ffmpeg -v info -i output.mp4 -vf "blackdetect=d=0.1:pix_th=0.10" -f null - 2>&1 | grep black
```

El encuadre se queda **hasta que el gráfico ya es opaco** (`start + fade_in`), y el
siguiente entra cuando el gráfico **empieza** a irse (`end − fade_out`).

⚠ **`pix_th=0.10` marca el propio suelo del sistema.** El fondo es `#0B0C10`, luma 12, así
que *cualquier* frame que sea solo fondo cuenta como negro con el umbral por defecto. Para
distinguir un hueco real de una transición legítima hay que bajar el umbral:

```bash
ffmpeg -v info -i output.mp4 -vf "blackdetect=d=0.05:pix_th=0.03" -f null - 2>&1 | grep black
```

Si a `0.03` no aparece nada, no hay negro real — solo el grafito de la casa.

### 6b · La entrada del contenido va PEGADA al fundido de su contenedor

Corolario de la anterior, y tiene una ventana estrecha entre dos fallos:

- **Si el contenido entra durante el fundido del host**, se multiplican las dos opacidades
  y el texto pasa unas décimas por debajo de 3:1 — lo caza el check de contraste.
- **Si entra demasiado tarde**, el host ya es opaco y no hay nada dentro: quedan 0.15–0.20 s
  de lienzo vacío que `blackdetect` caza y el ojo lee como un fallo.

La solución no es mover la entrada del contenido, es **acortar el fundido del host**
(`fade_in` ~0.12) y arrancar el contenido justo detrás. Ningún color de texto sobrevive un
fundido entero: medido sobre pastilla violeta, hasta el blanco cae a 3.21:1 al 35 % de
opacidad. El arreglo es temporal, no cromático.

### 7 · Un trazo SVG se prepara en t=0, no al dibujarlo

`stroke-dasharray` montado en el mismo instante en que arranca el tween deja la línea
**entera desde el primer frame**: el «dibujado» no dibuja nada, aparece ya hecho. El
`tl.set` del dash va en el segundo 0 del timeline.

### 8 · GSAP y los transforms

- `left`/`top` se cuantizan a píxel entero y **tartamudean** → usar `x`/`y`.
- Toda salida necesita un `tl.set(..., {opacity:0})` de **kill duro** en el borde.
- **Nada de `transform: translate(-50%,-50%)`** en un elemento que GSAP anime: toma el
  control del transform y descarta el centrado. Centrar con **flex**.
- Dos tweens sobre la misma propiedad del mismo elemento (dos clics seguidos sobre un
  cursor) necesitan `overwrite: "auto"`, o el resultado depende del orden de evaluación.
- Elementos que comparten posición a propósito necesitan `data-layout-allow-overlap`.

---

## CLI de HyperFrames

- Un `public/index.motion.json` de una composición **anterior** hace fallar `check` con
  `motion_selector_missing`: sus selectores ya no existen. Reescríbelo o bórralo.
- `npx hyperframes snapshot public --at 1.2,7.6,20.5` — lista **separada por comas**.
  Repetir `--at` **no acumula**.
- `snapshot` sobrescribe entre corridas y añade siempre un frame de fin de timeline.
- `check` sustituye a `validate` / `inspect`, deprecados.
- Los checks de **contraste solo corren si hay muestras**: si el informe dice `0/0`, no es
  que pase, es que no midió.
- Esperar un render por **el proceso**, nunca porque el archivo dejó de cambiar: si ya
  existe un `output.mp4` anterior, la condición se cumple al instante y acabas analizando
  el archivo viejo.
  ```bash
  npx hyperframes render public … & RENDER_PID=$!
  wait $RENDER_PID
  ```
  ⚠ **`pgrep -f "hyperframes render"` se caza a sí mismo.** El shell que ejecuta el bucle
  de espera lleva esa misma cadena en su línea de comando, así que `pgrep` lo encuentra, la
  condición nunca se cumple y parece que el render sigue eternamente cuando terminó hace
  rato. Esperar al **PID concreto** o mirar el final del log.
- Un render de ~47 s tarda **~2 min** con la máquina despejada; sube a ~5 si se lanza
  trabajo pesado en paralelo (otro ffmpeg, snapshots). Conviene no solaparlos.
- `| tail -N` sobre el log de un render no vuelca nada hasta que el proceso cierra.

---

## Audio

- **El metraje de iPhone llega pegado al techo.** La grabación de la pieza 2 trae 7690
  muestras a 0 dB *antes* de tocarla. Sumarle música y efectos satura la mezcla. Se le da
  cabecera a la voz (`voice_gain`) y se desplazan efectos y música **los mismos dB**, para
  que aparezca margen sin que cambie el balance.
- **`volumedetect` y `silencedetect` loguean a nivel info.** Con `-v error` no imprimen
  nada y la medición sale vacía en silencio.
- **El AAC mete ~21 ms de priming delay**, y el decodificado en float puede pasar de 1.0.
  Comparar muestra a muestra contra el original da resultados imposibles: alinear por
  correlación cruzada primero.

---

## Grabaciones de pantalla

- **Casi nunca llenan el archivo.** Si la ventana no cubría el monitor quedan barras
  negras: la grabación de la pieza 2 tiene contenido solo en x 96..1822 de 1920. Un
  recorte que las pise mete una franja negra en mitad del mockup, y «cabe» en el archivo
  perfectamente. `screen-tour.py` lo mide con `cropdetect` y falla antes de renderizar.
- El chrome del navegador de quien grabó (pestañas, marcadores) y el dock del sistema
  **siempre fuera**. Lo que se ve es el producto, no su navegador.

---

## ffmpeg

- **`lut3d` propaga las etiquetas de color del frame de entrada.** Sin `setparams`, el
  archivo convertido sigue marcado como HLG y Chrome vuelve a aplicar la curva. Los flags
  `-color_trc` / `-color_primaries` por sí solos **no bastan**.
- Puede que este ffmpeg **no traiga `zscale`** (sin libzimg ni libplacebo), y `tonemap`
  sin entrada lineal deja la imagen gris. Por eso el LUT propio.

---

## AssemblyAI

- `audio_duration` viene **redondeado al segundo**. Pasar siempre la duración real de
  `ffprobe` al planificar cortes.
- Puede no transcribir sonido audible (una duda, un "mmm"). Cruzar con `silencedetect` +
  `volumedetect`.

---

## Diseño

- **El troceo del subtítulo no puede ir solo por ancho.** Cortar por ancho pega el final
  de una idea con el principio de la siguiente («…empleados. Cuando…») y el espectador lee
  una frase que nadie dijo. La jerarquía es frase → cláusula → reparto parejo.
- **La altura del subtítulo se consulta por el PUNTO MEDIO del bloque**, no por su inicio:
  un bloque que arranca 20 ms antes del plano siguiente pertenece al plano siguiente, y
  midiendo por el inicio heredaba la altura del anterior — o la de un tramo `off`, que no
  tiene cara que esquivar, y salía un subtítulo a media pantalla.
- **Un mockup no puede adelantar el guion.** Tres logos visibles desde el primer frame
  parecen más limpios, pero el espectador lee «Excel» dos segundos antes de que se diga, y
  cuando llega la palabra ya no pasa nada. Cada elemento entra en **su** palabra.
- **El HUD da contexto, no repite el dato.** Si el tablero ya dice «3 herramientas ·
  0 conexiones», el HUD tiene que decir otra cosa.
- En REEL, **el 20 % inferior (y > 1536) es zona segura** de la plataforma. El hueco bajo
  el subtítulo no es un descuido. Y `cap_top` de un visual hay que calcularlo con la altura
  REAL de su contenido: bajarlo «para que no estorbe» metió el subtítulo del CTA en
  y1512..1647, justo donde Instagram pinta el usuario y los botones. Se mide sobre el MP4:
  ```bash
  ffmpeg -ss <t> -i output.mp4 -frames:v 1 f.png   # y luego las filas con tinta
  ```

---

## Entorno

- `opencv-python-headless` **5.x quitó `objdetect`/`CascadeClassifier`**. La medición de
  cara necesita `<5`.
- El render pide memoria. Si la máquina va justa, cerrar aplicaciones antes.
