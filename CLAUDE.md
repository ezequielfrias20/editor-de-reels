# editor-videos — estilo "Tech Premium"

Proyecto de edición de video con **HyperFrames** (video renderizado desde HTML).

El objetivo de cada pieza es doble: **comunicar el contenido y demostrarlo visualmente**.
La prueba de fuego: **con el audio apagado se entiende la mayor parte del mensaje** — y
aun así la edición nunca compite con lo que se dice.

Idioma de trabajo y de los videos: **español**.

> **Nota de historia.** Hasta agosto de 2026 hubo un estilo Editorial Retro-Digital (papel
> crema, didone, anotaciones a mano) que se descartó. El tema `claro` actual es otro
> sistema: grotesca pesada, terracota, hairlines. En septiembre de 2026 el sistema
> grafito + violeta pasó a las dos paletas de la marca (§3).
>
> Todo el material de las piezas anteriores se borró: el proyecto empieza de cero con
> ediciones nuevas. Los datos que usan los tests viven en `tests/fixtures/`.

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

⚠ **El número de carpeta de `VIDEOS ORIGINALES/` no es el de la pieza.** Las carpetas se
numeran por calendario de publicación o por orden de grabación, se editan salteadas, y un
mismo tema puede venir en dos tomas distintas. El número del pedido tampoco garantiza
nada: puede apuntar a la carpeta de otro guion. **Antes de abrir un slot se identifica el
material por lo que dicen el `guion.md` y el transcript**, no por el número; manda el
contenido del brief. Comprobarlo cuesta un minuto y se comprueba siempre, también cuando
parece que coincide.

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
| 9 | **Escribir el plan** | `videos/2/plan.json` ← **el trabajo creativo**, a mano |
| 9b | **o escribir el EDL y compilarlo** | `videos/2/edl.json` ← el trabajo creativo, anclado a ÍNDICES DE PALABRA · `scripts/edl-compile.py --project . --piece 2` escribe `plan.json` |
| 10 | Componer | `scripts/build-composition.py --project . --piece 2` |
| 11 | Validar | `npx hyperframes check public` |
| 12 | Renderizar | `npx hyperframes render public --skill=talking-head-recut -o output.mp4 --fps 30 --sdr` |

En los pasos 9/9b **el plan/EDL declara `palette` (`claro` | `oscuro`)**, obligatorio
(§3); si la pieza viene de un brief de `plan-edicion`, se usa la que trae. El andamio
`scripts/edl-plan.py` también la exige (`--palette`).

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

Tres casos del material que cambian la conversación:

- **Una carpeta sin guion** (`guion.md` vacío) no bloquea: el transcript ES el guion, y la
  estructura (hook · problema · producto · cifras · tesis · CTA) sale de leerlo. No hace
  falta pedir nada.
- **Unas instrucciones que llegan truncadas** se montan con lo legible, se pregunta lo que
  falta en este paso y se avisa al entregar de qué parte no se pudo leer.
- **Una grabación con poco metraje quieto** (una página que scrollea sin parar) se mide
  antes de proponer (§7, mesetas), y la pregunta incluye la opción de usar solo las
  ventanas quietas y dibujar el resto.

El usuario puede elegir una propuesta que choca con una doctrina de la casa (una animación
espectacular justo antes del clímax, por ejemplo). Se le dice con qué choca y **decide
él**: la doctrina informa la pregunta, no la sustituye.

**El paso 9 tiene dos caminos.** El de siempre: escribir `plan.json` a mano. El otro:
escribir un `edl.json` que referencia **índices de palabra** del transcript (no floats
copiados a mano) y dejar que `edl-compile.py` derive shots, stages, captions y SFX — con
gates de estilo que fallan antes de escribir nada si `presenter_share`, el ritmo de cambios
o la proporción de transiciones especiales se salen de banda. El paso 10 no cambia:
`build-composition.py` consume el `plan.json` que sea, sin saber de cuál de los dos caminos
vino. Ver `docs/superpowers/plans/2026-09-07-edl-motion-design.md` y
`docs/superpowers/specs/2026-09-07-edl-motion-design-design.md`.

Las métricas que miran los gates del EDL: `presenter_share` (banda ideal [0.45, 0.60];
`warn_in` [0.35, 0.70], donde avisa sin bloquear —severidad `warn`, no `fail`—),
`max_bare_stage`, `max_micro_gap`, `max_macro_gap`, `min_camera_gap`, `theme_change_count`,
`special_transition_ratio` (tope 0.2: dos transiciones especiales de cada diez límites),
`punch_zoom_count`, `decorative_reason_count` y `sfx_dropped`. Un `presenter_share` en
`warn_in` puede ser correcto: subirlo a la banda ideal obligaría a inventar un objeto sin
`reason` real o a sacar de cámara una tesis que su propio `reason` argumenta que va en
cámara. Se deja así a sabiendas y se escribe por qué.

Las transiciones especiales tienen un sentido cada una: **`OBJECT_MATCH_CUT`** cuando es el
MISMO objeto mutando (un documento que recibe su sello, un reloj que salta de hora sobre
la misma instancia y el mismo `id`), no una escena nueva; **`DIAGONAL_WIPE`** para un
remate.

**El EDL también emite RÓTULOS** (evento `CARD`). Un rótulo no es un stage pequeño: **el
stage sustituye la cara y el rótulo la acompaña**, y hay frases —«escalar a un humano»,
dicha por un humano— en las que esa diferencia ES el argumento. Por lo mismo, **una regla
que formula él** («dato sin acción = ruido») va en rótulo y no en stage: acompaña su cara
en vez de sustituirla, y entra en la palabra que la provoca, no antes. Los dos bordes salen
de una palabra (`atWord` / `untilWord`, que usa el FINAL de la suya), así que un borde
corregido por `refine-timings` los mueve solos.

⚠ **Un `CARD` dentro de un segmento de stage falla, y no es gusto: es apilado.** Las
tarjetas van en la pista 4 y el takeover en la pista 5 (trampa 5 de §9), así que el rótulo se
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
   esos huecos y un borde optimista se lleva el ataque de la palabra siguiente. Lo normal
   es que mueva entre 6 y 10 bordes por toma.
2. **Avisa de sonido audible sin transcribir**, clasificado por tono (`voicing.py`, más
   abajo) y **por islas**: un hueco con dos soplidos sueltos se corta sin pensarlo, uno
   lleno de una duda de dos segundos no.
3. **Marca los tramos con la alineación rota** por ritmo silábico imposible (>12 síl/s).

**Ese tercer aviso puede salvar la pieza.** Un tramo entero puede venir desplazado casi
2 s —cinco palabras seguidas a más de 13 síl/s, una de tres sílabas en 113 ms— y todos los
beats de ese tramo caerían fuera. El remedio no es este script: se **re-transcribe el tramo
suelto**, que sale bien porque el modelo deja de arrastrar el contexto largo, y se empalma.

Cómo leer los avisos, porque cada uno dice dónde mirar y ninguno dice qué hay:

- **Un aviso de alineación imposible puede ser falso**: una palabra corta dicha rápido da
  el mismo ritmo que un desfase. Re-transcrita suelta vuelve a <35–90 ms de la original, o
  un frame a frame muestra la palabra cerrando sobre silencio real y la siguiente
  arrancando en el ataque. **Confirmar que no pasa nada también es un resultado**, y es
  barato. Aun así, si el pase aislado alarga la cola de una palabra que cae en un borde de
  corte, se empalma ese tramo: ese borde es donde corta `plan-cuts`.
- **Al empalmar se toman los TIEMPOS del pase aislado y se conserva el TEXTO del pase
  largo** cuando el aislado oye peor (un «aumenta» donde el guion dice «aumentan»). Cada
  pase es mejor en una cosa distinta.
- **Dos avisos distintos pueden ser el mismo hecho.** Un arranque de palabra perdido
  aparece a la vez como alineación imposible en esa palabra y como sonido audible sin
  transcribir justo antes: con el borde corregido, los dos desaparecen.
- **La re-transcripción suelta es una segunda opinión, no un árbitro.** Puede estirar una
  palabra sobre silencio (el pase largo tenía razón) o comerse la plosiva inicial (la
  tenía `refine-timings`). Quien desempata es el audio: la envolvente y `voicing.py` dicen
  si en ese tramo hay ataque o suelo de ruido.
- **La conclusión de una toma no se hereda a la siguiente.** En una todos los avisos son
  falsos positivos y en la otra dos de diez son reales, uno de ellos un corte sobre el
  ataque de una palabra. Se vuelve a medir cada vez.
- **Una isla de sonido audible puede ser cola de palabra o un sonido aparte.** El aviso
  dice dónde mirar; **la envolvente RMS (ventanas de 50 ms) dice qué es**, y solo eso decide
  si el corte la parte o se la lleva entera. Un ataque separado (un blip tras la palabra,
  una vacilación antes del CTA) con el corte automático encima deja la palabra truncada: el
  borde va ANTES del ataque, no dentro. Una isla a 1.6–2.4 s de silencio real de la palabra
  anterior, que re-transcrita da 0 palabras, es un sonido aparte: si cae entera dentro de
  una pausa que `plan-cuts` colapsa, se elimina sin que ningún borde la parta — se verifica
  contra los `keeps` antes de cortar, y sobre el MP4 después.
- **Y el aviso de «sonido audible sin transcribir» puede ser una PALABRA**, no solo una
  respiración. Con armonicidad alta (0.74–0.80) y ataque limpio desde el suelo de ruido es
  voz: AssemblyAI puede haber colocado esa palabra 1.2 s más tarde y con 65 ms de duración.
  Tal cual viene, `plan-cuts` ve una pausa larga donde está la palabra y se la come. Se
  mide el span real y se corrige antes de cortar.

⚠ **Y el transcript miente con las siglas y los nombres propios.** Una sigla que él
deletrea («BCV») la oye como «de ese B»; una marca sale partida o mal escrita («Composeo»,
«Cloud Code», «Money Printing Turbo»). Ninguna medición lo caza: hay que leer el texto
contra el guion. Se corrige el TEXTO (el audio no se toca) para que el subtítulo escriba
bien la marca; si el modelo la partió en varias palabras, se funden en una conservando el
span completo.

⚠ **Pero el subtítulo transcribe lo DICHO, no el guion escrito.** Si el guion dice
«Automatizar» y él dice «Optimizar», se queda «Optimizar»: cambiarlo sería reescribirle la
frase, no arreglarle una marca.

⚠ **AssemblyAI puede comerse una palabra entera**, y ninguna medición lo caza: un «qué» que
falta no rompe ningún número. Se ve leyendo el transcript contra el guion; se re-transcribe
suelto el tramo, que sí la oye, y se inserta a mano con su span.

⚠ **Y puede devolver un `end` desbordado** sobre las palabras siguientes (una palabra con el
final 2.3 s más tarde, pisando a las cuatro que vienen detrás). No lo caza ningún aviso de
`refine-timings`: se ve **comparando cada `end` con el `start` siguiente**, y se recorta al
inicio de la siguiente.

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

- **`refine-timings` estira los bordes solo sobre voz.** Los bordes que deja de
  mover con esta regla son justo los que se comían una respiración (en la toma que
  lo destapó, tres de nueve, de ~500 ms cada una, y una cuarta a −7 dB que vivía
  escondida dentro de una palabra). Su aviso de isla también dejó de llamarlas
  «vocalización» —lo eran por reparto grave/agudo— y ahora dice «respiración».
  Quitarlas de una toma de 41.6 s la dejó en 39.2: **la diferencia eran
  respiraciones**.
- **`plan-cuts --audio` coloca la pausa que queda sobre SILENCIO.** No cambia
  cuánta pausa deja, cambia de qué está hecha: cada lado se recorta hasta donde
  empieza la respiración. Sin `--audio` se comporta como siempre, para que las
  piezas anteriores se vuelvan a cortar igual.
- **Los márgenes de cabeza y cola también.** La última inspiración de la toma
  entraba en el reel por `TAIL_PAD`.
- **Y una red que lo comprueba: `audit-breaths.py` (paso 4b).** Quitar la respiración es
  del paso 3; comprobar que no quedó ninguna es de este, y falla con código 1 para que
  un reel con una inspiración dentro no llegue a renderizarse por descuido. El
  resultado esperado es **cero islas sin voz fuera de un span de palabra**; si falla,
  señala el tramo y el nivel (p. ej. 75 ms a −15.1 dB), y se arregla volviendo a cortar
  con `--audio`, no con una herramienta nueva. Su test incluye un caso con margen 0 para
  probar que el camino de FALLO existe: un gate que nunca ha fallado no es un gate.

⚠ **Auditar un corte exige el umbral de la FUENTE.** El suelo sale del
percentil 10 de la propia envolvente y un corte ya no contiene los silencios de
los que estimarlo: medido, «sube» de −52.0 a −41.9 dB y el umbral con él, de
−42.0 a −31.9. Con el umbral equivocado una ráfaga de −11.7 dB se quedaba en
75 ms y caía por debajo de `min_dur`.

⚠ **Y una isla CORTA pero FUERTE cuenta igual.** Una respiración puede arrancar
con ráfagas de 35–55 ms a −13 dB que `min_dur` descartaría una por una; contarlas
movió un corte 110 ms, lo justo para dejarla fuera.

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

## 3. Sistema visual — las dos paletas de la marca

Superficies flotando sobre un suelo liso con hairline y sombra suave, tipografía grotesca
pesada y un único momento de acento terracota por frame. **Dos paletas, la misma marca**:
`claro` (suelo crema, tinta casi negra) y `oscuro` (suelo casi negro cálido, texto
crema). Cada pieza elige una.

La fuente de verdad es `scripts/tokens.py`. Los valores BASE se copian del dashboard del
proyecto (`Marketing/dashboard/web/src/app/theme.css`) y no se inventan aquí: así el video
y el dashboard son la misma marca. Todo lo demás se **deriva con una regla** y se **mide**
en `tests/test_paletas.py`.

### La paleta se declara por pieza

`"palette": "claro" | "oscuro"` es **obligatorio** en la raíz de `plan.json` y de
`edl.json` (y `scripts/edl-plan.py --palette` también lo exige). `build-composition.py`
**falla** si falta o no existe, y si está bien llama a `tokens.use(palette)` antes de
emitir nada. Si la pieza viene de un brief de `plan-edicion`, se usa la que trae; si no, se
pregunta en el paso 3b junto con las animaciones.

⚠ El campo se llama `palette`, no `theme`: `theme` sigue siendo el **tema semántico**
(`primary` · `problem` · `warning` · `success` · `neutral`) que cambia `THEME_CHANGE` en un
stage. El tema cambia acento, relleno y glow; **nunca el color del texto**, que ya está
medido contra cada superficie.

### Las bases

| token | `claro` | `oscuro` | uso |
| --- | --- | --- | --- |
| `bg` | `#ECE7DE` | `#161412` | suelo |
| `surface` | `#F7F4EE` | `#201D1A` | tarjeta / panel |
| `surface2` | `#E4DED2` | `#2B2723` | elevado (fila activa, celda destacada) |
| `text` | `#1C1A16` | `#EEE8DF` | tinta principal |
| `text2` | `#6F695F` | `#A39C91` | secundario |
| `line` | `#D8D1C4` | `#36312B` | hairline (`TK.LINE`) |
| `accent` | `#C45F38` | `#E27B52` | el acento: fills, barras, pastillas |
| `accent_soft` | `#F1DDD2` | `#3A2419` | fondo suave de acento |
| `on_accent` | `#FFFFFF` | `#1A0F0A` | texto sobre `accent` — solo grande y en negrita |
| `go` | `#3F7D4E` | `#7CC08C` | resuelto · conectado · CTA |
| `warn` | `#A66A12` | `#E0A64A` | aviso |
| `alert` | `#B23A2E` | `#EC7B6E` | problema · desconectado |

Las marcas de terceros (`BRANDS`: Excel, WhatsApp) no dependen de la paleta.

### Los derivados — reglas, no valores

Cada derivado es una regla en `tokens._derive`. Si un par no llega a su mínimo, **se
arregla la regla, nunca el componente**.

| token | regla |
| --- | --- |
| `bg2` | mezcla `bg`→`surface` al 50 %: centro del viñeteado |
| `bg_edge` | `bg` hacia negro, 30 % en `oscuro` / 6 % en `claro`: borde del viñeteado |
| `surface3` | `surface2`→`text` al 6 %: bordes internos de UI, tracks de barra |
| `text3` | el paso **más tenue** de `text2` hacia `surface` que aún da ≥4.5:1 |
| `accent_hi` | el acento hacia `text` hasta ≥4.5:1 contra el suelo iluminado por el foco (`lift(bg, SPOTLIGHT_MAX)`): **el acento cuando es TEXTO** |
| `accent_lt` | el acento hacia `text` hasta ≥7:1: texto de acento que va a FUNDIR |
| `accent_pill` | el acento hacia el suelo hasta que `text` encima dé ≥4.5:1: pastilla del karaoke, rótulos, fondos con texto encima |
| `LINE_HI` | `line`→`text` al 15 %: el hairline que tiene que separar más |
| `INK_ON_FILL` | la tinta (`bg` o `text`) que más contrasta con `go` / `warn`: lo que va ENCIMA de un relleno de señal |

`FILL` (rellenos translúcidos de acento y señal), `THEME` y `GLOW` también se recalculan
con la paleta. `SPOTLIGHT_MAX` (0.05) es el techo del foco cenital de un stage:
`spotlight()` falla por encima, porque ahí `accent_hi` dejaría de pasar AA.

### Cómo se usa desde el código

- **`tokens.use(nombre)`** activa una paleta: muta **en su lugar** `C`, `FILL`, `THEME` e
  `INK_ON_FILL` (quien los importó por nombre ve el cambio) y **reasigna** los escalares
  `LINE`, `LINE_HI`, `SHADOW`, `SHADOW_LIFT` y `GLOW`.
- Los escalares se leen **siempre como atributo**: `TK.LINE`, con `import tokens as TK`
  (alias `TK` porque `build-composition.py` ya usa `T` para la escala tipográfica).
  **Nunca `from tokens import LINE`**: quedaría congelado en la paleta de arranque.
- Helpers para las transparencias: `accent_a(a)` (acento), `ink_a(a)` (texto: hairlines,
  rejilla), `shade_a(a)` (suelo: velos, halos de texto), `mix(a, b, t)` y `rgba(hex, a)`.
- **Ningún componente escribe un color a mano.** Todo sale de `tokens`: un hex o un
  `rgba(255,255,255,…)` escrito en un mockup se queda igual en las dos paletas y en una de
  ellas deja de leerse. Lo vigila `tests/test_paletas_consumidores.py`: caza los colores y
  claves del sistema viejo (grafito, violeta y las señales neón `go`/`alert`/`warn` de
  antes), los escalares importados por nombre, y que cada mockup de muestra renderice
  distinto en `claro` y en `oscuro` sin arrastrar el acento de la otra. ⚠ El guardián
  conoce los valores VIEJOS: un color nuevo escrito a mano no lo caza, así que la regla
  se cumple al escribir, no solo al testear. Excepciones a sabiendas, iguales en las dos
  paletas porque son interfaz literal: el cursor blanco (con filete de la tinta más
  oscura, `_ink_dark()`), el semáforo de ventana macOS y las sombras `rgba(0,0,0,…)`.
- `logos.brand_tone()` mueve el color de una marca hacia el `text` de la paleta hasta 3:1
  contra `surface`: en `oscuro` lo aclara (el verde de WhatsApp a su valor nominal se hunde
  en el fondo), en `claro` lo oscurece. Misma regla, dos direcciones.
- **`scripts/palette-sheet.py`** genera una hoja HTML estática (`out/palette-sheet/`) con los
  mockups más usados en su estado final, en las dos paletas lado a lado. Se revisa a ojo
  **cada vez que se toca `tokens.py`**: los tests miden pares, la hoja enseña si el conjunto
  se lee.

### Contraste

Mínimos: **texto chico 4.5:1**; **texto grande (≥24 px en negrita), chips y logos 3:1**. Los
fija `tests/test_paletas.py` para las dos paletas —`text`/`text2`/`text3` sobre `surface`,
`accent_hi` sobre el suelo y bajo el foco, `accent_lt` a 7:1, `text` sobre `accent_pill`,
`on_accent` sobre `accent` (solo grande), `INK_ON_FILL` sobre `go`/`warn`— en vez de una
tabla de números que envejece con la primera paleta nueva. `tokens.contrast(a, b)` mide
cualquier par nuevo antes de renderizar, que es cuando cuesta barato.

Consecuencias que se leen directo de los mínimos:

- **El acento como texto es `accent_hi`**, nunca `accent` a secas.
- **Sobre un relleno de señal (`go`, `warn`) va `INK_ON_FILL`**, no un blanco por costumbre:
  en `oscuro` el verde es claro y el blanco encima no se lee.
- **`on_accent` sobre `accent` solo en texto grande y en negrita.** Para texto chico sobre
  un fondo de acento, `text` sobre `accent_pill`.

**Nada de negro puro ni blanco puro como fondo** (`test_paletas` lo comprueba para `bg`,
`bg2` y las `surface`). Un suelo casi negro deja respirar los oscuros del metraje en vez
de aplastarlos; un crema no quema como un blanco.

### Tipografía

**Dos familias.** Una tercera hace que la pieza parezca un collage.

| Rol | Familia |
| --- | --- |
| Todo el texto | **Inter** 400–900 (900 para titulares y subtítulos) |
| Etiquetas de UI, datos, chips | **JetBrains Mono** 400/700, uppercase, tracking amplio |

Cuanto más grande el texto, más se cierra el tracking. Escala en `tokens.TYPE`.

✅ Las 8 woff2 están vendorizadas y verificadas en
`.claude/skills/video-tech-premium/assets/fonts/`. Se regeneran con `scripts/fetch-fonts.py`.

⚠ **Trampa de Google Fonts:** el CSS devuelve varios `@font-face` por familia y el
**primero es el cirílico** — quedarse con el primer `src` baja un subset sin una sola
tilde. Hay que elegir el bloque cuyo `unicode-range` contenga `U+0000-00FF`.

### Textura y elevación

- Fondo: `vignette()` radial (`bg2` → `bg` → `bg_edge`) + `grid()` a `ink_a(.022)` cada
  72 px.
- **Hairline** (`TK.LINE`) como único borde, `TK.LINE_HI` cuando tiene que separar más.
- Sombra (`TK.SHADOW`): en `claro`, la del dashboard —`0 1px 2px rgba(28,26,22,.06),
  0 8px 24px rgba(28,26,22,.08)`—; en `oscuro`, `0 2px 6px rgba(0,0,0,.45),
  0 18px 50px rgba(0,0,0,.55)`. Sobre suelo oscuro una sombra negra apenas se ve: la
  elevación la dan la sombra *y* el hairline. Nunca dura.
- Glow de acento **escaso** (`TK.GLOW`): solo el objeto protagonista del frame.
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

**El punch-in recorta alrededor de la CARA, no del centro geométrico**: `measure-face.py`
mide también el centroide horizontal (`cx_frac`), y un creador que no está centrado en el
cuadro sale del encuadre si el zoom se abre desde el centro.

**Los tramos de cara pelada son decisiones.** El hook y el matiz («no reemplaza la
atención humana»), la tesis: son los momentos en que un gráfico le roba el argumento a la
cara, y van a plano lleno (`kind: "full"`) aunque la pieza sea triband.

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
bandas que cubren el lienzo de arriba a abajo **sin huecos**. La división cae en la MITAD
exacta del lienzo: con el hablante en menos de la mitad de abajo, la cara quedaba chica y
el recorte se llevaba la coronilla.

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
(`backdrop`/`takeover`); `band` decide la GEOMETRÍA del host. Sin `band`, una card de logo a
lienzo completo con host opaco tapa al hablante entero mientras dura — en el navegador no se
nota nada raro, y sobre el MP4 la banda `speaker` sale plana, del color del suelo. Declarar
`band` en un visual (o `camera: "BAND"` en un segmento) sin que el plan traiga `layout`
**falla** en vez de caer a un lienzo completo por defecto: la geometría de las bandas no
tiene un valor implícito razonable.

**En triband los rótulos (`cards`) suelen sobrar.** La banda de arriba ya hace el trabajo
de acompañar lo que se dice, y un rótulo encima compite con ella: una pieza triband puede
salir con cero rótulos y es lo normal.

### Que nunca se corte la cara

Con `object-fit: cover` en un encuadre `band`, un `anchor` demasiado alto recorta más del
techo de la FUENTE y se lleva la coronilla por delante — el mismo tipo de error que el de
la banda tapada de arriba, sin arreglo en post. `check_face_top_clear` (al lado de
`check_band_speaker_clear` en `build-composition.py`) lo caza en tiempo de compilación:
proyecta `top_frac` —el borde superior de la caja de cara que da `measure-face.py`,
percentil 5 (el espejo del p95 de la barbilla) sobre las MISMAS muestras Haar— con la
fórmula de `chin_at` para `band`, y si el resultado cae por encima del techo de la banda
`speaker`, `sys.exit()` antes de renderizar. Una medición sin `top_frac` salta el gate
limpio.

El `anchor` sale de aritmética, no de gusto (fórmula en `references/triband.md`). Con la
banda `speaker` en [960,1920], valores típicos de `chin_frac` ~0.44–0.48 y `top_frac`
~0.26–0.31 dejan válido un `anchor` entre ~0.31 y ~0.56; **0.38–0.42** deja la coronilla con
140–220 px de aire bajo el techo de la banda. El `0.5714` por defecto del estilo subía
demasiado el recorte y se la llevaba. La y del borde de la cara que predice el gate la
confirma Haar sobre el MP4 dentro de unas decenas de px.

### La banda `top` nunca se queda vacía

Doctrina de 2026-09-15, a petición del usuario: **«en la parte de animaciones siempre se
debe mostrar algo, en cualquier segundo, nunca debe estar el fondo vacío»**. Sin esta
regla, un reel de cinco herramientas dejaba la banda de arriba en suelo liso más de una
cuarta parte de sus tramos `band`, repartida en siete huecos.

Choca de frente con «nada entra antes de su palabra» (§7): no se puede adelantar la card
SIGUIENTE para tapar el hueco que la precede, porque el espectador leería el nombre de la
herramienta antes de que se diga. **La resolución es sostener el visual ANTERIOR, nunca
adelantar el siguiente** — se extiende su `end` hasta que entra el que viene; el que viene
sigue esperando su propia palabra. Es la misma idea que `check_no_black` ya aplica al
metraje, aquí aplicada a los visuales de la banda `top`. El hueco de ARRANQUE (nada
delante que sostener) se cierra al revés: moviendo el `at` del propio encuadre `band` para
que coincida con la entrada de la primera card. Y un hueco puede ser un beat de guion sin
visual asignado, no un fallo de sostenido — una frase como «he juntado estas y varias más
en una guía» no nombra nada nuevo que clavar, así que entra un visual nuevo (`tool_lineup`:
las marcas ya nombradas, juntas en fila) en vez de estirar la grabación anterior.

`check_band_top_covered` (junto a los otros tres gates de arriba) para la compilación si
algún instante de un tramo `band` no tiene ningún visual sobre la banda `top`, listando los
huecos con sus tiempos.

⚠ **Lo que ese gate garantiza es COBERTURA DECLARADA, no luma renderizada**, y conviene no
leer su nombre como más de lo que mide. En cada relevo entre dos visuales la banda cae al
suelo durante **unos 130 ms**, porque el fundido de relevo lo aplica el runtime de
HyperFrames a los elementos `class="clip"` y la composición no lo gobierna.

⚠ **El `start` de un visual es la palabra de su PRIMER elemento**, no la del beat. Si el
primer elemento entra más tarde que el visual, ese retraso se suma al fundido de relevo
(~130 ms) y deja la banda de arriba vacía sin que `check_band_top_covered` lo detecte: el
gate mide cobertura declarada, no luma. Un visual declarado en 7.820 cuya tarjeta entra en
8.347 deja medio segundo de banda vacía, y el gate lo da por bueno con razón: el visual
está declarado. Así se han visto relevos de 200–733 ms. Si el primer elemento no puede
entrar antes, se sostiene el visual anterior o se mueve el límite del segmento (la trampa
6b), nunca se deja el visual entrando en vacío. Bien hecho, el suelo desnudo queda en
**1–5 frames por relevo** (33–166 ms).

⚠ **Y el arranque de la pieza es el caso que ningún gate ve.** Un visual declarado desde
0.000 cuya primera pastilla espera a la tercera palabra deja la banda en suelo casi un
segundo, y ahí no hay nada delante que sostener. La salida es la misma que `agent_editor`
usa para su lienzo vacío: entra la ESTRUCTURA —un marco, unos huecos discontinuos— con la
primera palabra, y lo que espera su palabra es el CONTENIDO. El marco no nombra nada, así
que no adelanta el guion, y de paso el frame plantea la pregunta que la palabra siguiente
contesta. No es el problema que esta doctrina vino a resolver —aquel eran beats enteros
sin material— y a tres o cuatro frames se lee como el CORTE DURO que pide §6. Queda anotado
en `tests/test_band_top_alcance.py`, con un test que obliga a actualizar esta nota si
alguien le añade al gate una medición de luma. Detalle completo —incluida la trampa de
mirar solo `band=="top"` y dejar fuera las grabaciones, que se posicionan con `rect`— en
`references/triband.md`.

### Verificar el triband sobre el MP4

Los gates miden el plan; el frame se mide aparte, con un **barrido de luma cada 0.5 s**
(no cada 2 s: un barrido grueso salta por encima de los relevos, que es donde vive el
hueco):

- **Banda `speaker`**: la luma máxima tiene que ser la del metraje (una prenda clara llega
  a 250–255), no la del suelo. ⚠ En `claro` ese umbral no sirve: un host opaco crema
  también pasa de 200. Ahí se mira que la banda no sea plana o se extrae el frame.
- **Banda `top`**: el suelo desnudo se reconoce por la luma del `bg` de la paleta (≈20
  en `oscuro`, ≈230 en `claro`), no por un umbral fijo; lo que se cuenta es cuántos frames
  pasa cada relevo en ese valor.
- **Borde de la cara**: Haar sobre 6–9 frames de tramos `band`, contra la y que predijo
  `check_face_top_clear`.
- **Último frame**: el CTA encendido (trampa 6c), extraído con `-sseof`.

### Zona segura

En REEL, **el 20 % inferior queda libre**: ahí pinta la plataforma su interfaz. El espacio
vacío bajo el subtítulo no es un descuido.

---

## 5. Captions

**Bloques de 3–6 palabras, todas al mismo tamaño y color, con un fondo de acento que viaja
palabra a palabra** (el karaoke, más abajo).

Resaltar todas las palabras IGUAL Y A LA VEZ convierte el subtítulo en un metrónomo y el
ojo deja de leer. Lo que lo evita no es dejar una sola keyword quieta y grande, sino que el
resaltado se MUEVA con la voz: el bloque entra entero y se queda quieto; lo único que se
mueve es el fondo detrás de la palabra que suena, en el instante exacto en que se
pronuncia.

El troceo va por **jerarquía**: frase → cláusula → reparto parejo. Cortar solo por ancho
pega el final de una idea con el principio de la siguiente («…empleados. Cuando…») y el
espectador lee una frase que nadie dijo. Por lo mismo, **un bloque de dos palabras es
correcto si es una cláusula completa** («Puedes automatizar»): partirlo para llegar a tres
pegaría el final de la frase anterior con el principio de esta, que es lo que la jerarquía
prohíbe.

Pieles: `on-dark` (sobre metraje — filete del color del suelo, `bg`, de 7 px con
`paint-order: stroke fill`, que pinta el trazo detrás del relleno y no engorda la letra;
en `oscuro` es letra crema con filete casi negro, en `claro` letra casi negra con filete
crema) · `on-surface` (sobre un gráfico o sobre suelo liso — sin filete).

### Nunca sobre la cara

La barbilla se **mide** (`measure-face.py`, Haar sobre 48 muestras, p95) y se proyecta al
encuadre activo. Varía mucho de una toma a otra (de ~0.43 a ~0.73 del alto de la fuente):
nunca se reutiliza la de otra pieza.

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
larga rompe la línea antes de agotar el ancho. «PACIENTES AUTOMÁTICAMENTE POR WHATSAPP»
suma exactamente 2.00 veces el ancho útil —dos líneas por división— y el navegador lo
envuelve a **tres**. Topado en dos, se descontaba una línea de menos y la tercera entraba
**58 px** dentro de la interfaz de la plataforma.

Y la caja de línea se mide con el tamaño de **referencia de la keyword** (1.22× el base),
no con el base: usando `CAPTION_SIZE` a secas, un bloque de dos líneas sobre un gráfico
(top 1430) metía la segunda línea 46 px dentro de la interfaz. La keyword ya no se pinta
más grande (karaoke), pero se sigue midiendo así: la cuenta queda conservadora a propósito.

Cuando el margen de la tinta más baja sobre y1536 sale de 5 px (y1531 = 1536 − 2·75 en un
bloque de dos líneas sin keyword), no es un descuido: es `floor_top` dando el tope exacto.
La cuenta está apretando bien.

⚠ **Medir la tinta del subtítulo por luminancia sola miente sobre metraje claro.** Un
umbral tipo «píxel > 205» da tinta en y1919 en un frame sin una sola letra ahí: era la
pared. La firma del subtítulo sobre metraje es el **filete de 7 px**: un píxel del color
`text` con el color `bg` pegado a menos de 9 px (en `claro` la firma se invierte —tinta
oscura, filete claro—; la regla no). Y se cuenta la **tinta plena**, no el antialias: un
píxel suelto a media luma por debajo del gate es borde de letra, no tinta.

### La excepción `triband`

Se llama «excepción» por el mecanismo de anclaje, no por lo rara que es: desde que el
triband es el layout por defecto de todo REEL (§4), este es el camino que toma la mayoría
de las piezas, no el caso raro.

En `full` · `split` · `pip` el subtítulo persigue la barbilla porque el metraje está detrás
y puede taparla. En `triband` no: entre el techo de la banda de texto y el techo de la banda
del hablante (§4) **no hay metraje**, es suelo liso, así que no hay barbilla que esquivar —
perseguirla ahí sería mover el subtítulo sin ningún motivo.

- **Anclado por ABAJO, en y944** (`bands.speaker.top` − `BAND_CAP_MARGIN` 16 px): la tinta
  más baja se apoya ahí y el techo del bloque sube según cuántas líneas tenga
  (`top = suelo − líneas × alto_de_línea`). Anclado por arriba, un bloque corto dejaba
  ~200 px de hueco muerto justo encima de la cara: el ojo usa de referencia la separación
  con la cara, no el techo de la banda de texto.
- **Piel `on-surface`, sin filete.** El filete existe para que la letra sobreviva encima de
  metraje que puede tener cualquier valor; sobre suelo liso no hace falta, y solo
  engordaría la letra sin razón.
- **Gate en y660** (`bands.text.top`): si el techo del bloque sube por encima de la banda de
  texto, invadiría la animación de arriba, y el compilador **para** en vez de recortar en
  silencio — «trocea el bloque más corto» en el mensaje de error.
- La cuenta de líneas sale de medir: base **66 px**, tamaño de referencia 66×1.22 = **81**,
  caja de línea 81×1.14 = **92**. Dos líneas = 184 px → techo en **y760**; tres = 276 →
  y668, todavía dentro. El troceo presupuesta dos líneas (`CAPTION_MAXW × 1.9`), así que
  el gate es la red, no la regla.

### El karaoke

Tratamiento **único** del subtítulo en toda la pieza, sin excepción de encuadre: nació
limitado a `band` y hoy va también en `full`/`pip` (el hook y la tesis). Lo que no cambia
entre encuadres es la PIEL: sobre metraje sigue `on-dark`, con su filete.

Todas las palabras comparten tamaño y color; lo que se mueve es un **fondo de acento con
esquinas redondeadas** detrás de la palabra que suena en el instante exacto en que se
pronuncia (su `start` en el transcript remapeado) — se apaga en cuanto arranca la
siguiente, así que nunca hay dos fondos encendidos a la vez y al terminar el bloque no
queda nada pintado.

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
- **Contraste**: la palabra va en `text` y el fondo es **`accent_pill`**, no `accent`. El
  acento a su valor de marca no garantiza 4.5:1 con texto chico encima; `accent_pill` es
  el acento empujado hacia el suelo justo hasta que `text` encima pasa 4.5:1, en las dos
  paletas (regla en `tokens._derive`, fijada en `tests/test_paletas.py`).
- La keyword sigue existiendo como concepto —se declara en `plan.json` o se detecta sola en
  una cifra— pero ya no cambia el RENDERIZADO: solo hace más conservador el cálculo de
  zona segura.

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

| Gesto | Ease | Entra desde (× = escala) |
| --- | --- | --- |
| `punch` (titular) | `expo.out` | ×1.045, y −8 |
| `stamp` (sello, cifra) | `power3.out` | ×1.10 |
| `rise-in` (panel grande) | `power3.out` | y +26, ×0.985 |
| `chip-in` (pastilla, nodo) | `power2.out` | ×0.94, y +8 |
| `slide-in` (kicker, HUD) | `power2.out` | y +14 |
| `box-in` (caja delimitadora) | `power3.out` | ×1.06 |
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
cualquier stock o generación.** La regla manda usar la grabación *cuando existe*: si la
grabación es la WEB de un producto y el beat habla de su editor, o la instalación se
resuelve con una línea de terminal y el beat dice «una aplicación de escritorio», para ese
beat no existe y va un mockup declarado.

**Cada marca nombrada lleva su logo** (regla del usuario), y ninguno entra antes de su
palabra.

**La rima visual es estructura, no repetición.** Dos instancias del MISMO componente con un
corte duro entre ellas —la misma card de chat vacía y lo único que cambia es qué se teclea
dentro; las mismas tarjetas del hook que vuelven al final en los mismos slots y solo
cambian el sello y el tema— dejan ver *qué* cambió. Es como se lee un contraste.

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
lienzo vertical solo cabe grande si el recorte deja de ser apaisado. Medido — un recorte
1350×854 acababa a **0.73×** dentro del `rect` (la interfaz se veía más pequeña que en el
monitor original); recortes de 500–780 px en un panel de 1000×820 van a **1.28–2.0×**.

**Antes de dibujar un gráfico que explique una pantalla, mirar si la pantalla ya lo
rotula.** Un modal que titula sus campos con las mismas palabras que él dice (Stock /
Reservado / Mínimo) es mejor explicación que cualquier mockup, y no hay que dibujarlo.

⚠ **Las barras negras.** Una grabación casi nunca llena el archivo: es habitual tener
contenido solo en x 96..1822 de 1920, o solo en y 8..576 en una captura de una web. Un
recorte que las pise mete una franja negra en mitad del panel y «cabe» en el archivo
perfectamente. `screen-tour.py` lo mide con `cropdetect` y falla antes de renderizar
—rechazar varios recortes seguidos por este gate es normal, no un fallo del gate—.

⚠ **Lo que no es el producto.** Una grabación de desarrollo trae dos cosas que la delatan
y que solo se ven unos segundos, así que no aparecen en el frame que uno mira al elegir el
recorte: el **indicador de dev** del framework (pastilla negra abajo a la izquierda) y un
**toast de error de validación**, que en un video de venta se lee como que el producto
falla. Se declaran una vez en `exclude` del spec —con su ventana de tiempo y su rect— y
`screen-tour.py` falla antes de renderizar si un tramo las pisa.

⚠ **Un tramo largo sobre una página que SCROLLEA no enseña lo que enseñaba el frame con
el que se eligió el recorte.** El recorte es fijo; el contenido, no. Un tramo de 2.2 s
puede arrancar en la cabecera y a los 1.9 s haber pasado de largo, o terminar en un
selector de cuenta de Google con datos ajenos en pantalla. El remedio son **tramos cortos
(1.3–1.6 s), cada uno verificado en su frame de ENTRADA y en el de SALIDA**, no solo en el
que se usó para elegirlo.

⚠ **Y se comprueba que lo que se ve es lo que se dice.** Barrer la grabación cada 0.5 s
contra el guion: un scroll puede pasar por la sección de testimonios en el segundo exacto
en que la frase habla de componentes, y con el audio apagado el beat dice otra cosa —la
prueba de fuego del proyecto falla ahí—.

**Las mesetas se MIDEN, no se miran.** Una correlación cruzada columna a columna entre
frames da el mapa del scroll: saltos, y **mesetas** donde el desplazamiento es idéntico
entre muestras seguidas. El tramo vive entero dentro de una meseta. Mirar dos frames
confirma o desmiente el recorte que ya elegiste; medir te dice dónde está el bueno. Tres
matices, los tres pagados:

- **La meseta que da el detector es CONSERVADORA**: exige correlación ≥0.99, así que puede
  cerrarla en 1.10 s cuando el recorte real es idéntico píxel a píxel hasta 1.03, deriva
  5 px a 1.13 y 24 a 1.23. Un tramo algo más largo que la meseta medida cabe dentro de una
  deriva invisible; se comprueba frame a frame sobre el recorte real.
- **Una medida de desplazamiento no distingue un scroll de un CONTADOR animándose.** Una
  ventana descartada por «cambio» puede ser una maqueta quieta con las cifras de la página
  trepando (86→112→130→140 agentes), y resultar la mejor del tour. La métrica dice dónde
  mirar; lo que hay ahí lo dice el frame.
- **Si el beat dura más que la meseta, dos recortes DISTINTOS de la misma ventana quieta**
  (uno la mitad de arriba —el titular y el comando—, otro la de abajo —la rejilla—), en vez
  de estirar un solo encuadre sobre metraje que ya no existe o que ya se movió. Si lo que
  hay quieto es una cabecera baja con todo apilado, varios recortes dan frames casi
  idénticos: se montan como un **empuje de cámara**, no como tres encuadres. Y ningún
  recorte puede ser más estrecho que la línea de texto más ancha que contiene: partirla por
  la mitad se ve en el frame.

⚠ **La cabecera de `tool_recording` es OPACA** (`surface`). Con un velo translúcido, que
sobre grabaciones oscuras se lee como un cristal elegante, sobre documentación de fondo
claro el texto de la página se transparentaba por detrás del chip y del nombre: dos textos
superpuestos. La legibilidad de esa barra no puede depender de lo que haya debajo, y el
alto de 84 px se paga igual.

⚠ **Las coordenadas de `clicks` y `boxes` NO se estiman.** Van en píxeles del lienzo y
entre el frame que uno mira y el lienzo hay tres transformaciones encadenadas. Estimándolas
a ojo, una caja cayó **300 px por debajo**, sobre otras filas. Dos formas de acertar:
`scripts/tour-map.py`, que hace la cuenta y además dice a qué tramo pertenece el punto, o
—más directo— renderizar el tramo al **tamaño exacto del panel** (`-vf scale=1000:820`) y
leer las coordenadas ahí, que ya son las del lienzo menos el origen del `rect`.

### Librería de mockups

`app_switch` · `connection_map` · `stat_grid` · `chip_grid` · `rate_mismatch` ·
`keyword_hero` · `flow_steps` · `comment_ui` · `chat_unanswered` · `screen_panel` ·
`browser_frame` · `hud` · `tool_card` · `tool_recording` · `tool_lineup` · `tool_pair` ·
`claude_prompt` · `layer_stack` · `step_grid` · `cv_echo` · `cv_vs_offer` · `offer_stack` ·
`rewrite_line` · `interview_chat` · `keyframe_grind` · `agent_editor` · `motion_demo` ·
`idea_fate` · `idea_veneer` · `agent_swarm` · `desktop_manager` · `split_problem` ·
`video_pipeline` · `money_button` · `video_output` · `tradeoff_bars`, más `icons.py` y el
campo `icons_` de `chip_grid` y `flow_steps`.

⚠ **`keyword_hero(mark=…)` no existe.** Un plan que lo pase no compila. Y un mockup puede
perderse del árbol de trabajo sin que nada avise hasta que un plan lo llama: un componente
que solo sobrevive en un `index.html` renderizado se restaura desde ahí.

`video_pipeline` es una cadena de producción —tema → guion → material → narración →
subtítulos → música → render— en tres estados (`manual`, `auto`, `gap`): sin nombres para
decir que hacerla entera cuesta, llenándose palabra a palabra para enseñar que la
herramienta la automatiza, y con un hueco delante para señalar la pieza que NO pone. Es
`agent_swarm` aplicado a un flujo en vez de a un reparto. ⚠ **La geometría no cambia entre
variantes**: es lo único que hace que el espectador lea «la misma cadena» y no tres
gráficos, y siete celdas de 130 px con 12 de hueco suman los 980 de `BOARD_W` exactos.

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
camino de fallo, no la compilación — y es el mismo modo de error que §13 persigue en todo
lo demás.

**`icons.py` y el campo `icons_` salen de una frase del usuario**: «me gusta que las
animaciones también lleven iconos y así, no solo textos y recuadros». La librería estaba
hecha casi entera de pastillas, tarjetas y titulares —que es lo correcto para ENUNCIAR y
demasiado plano para una enumeración de especialidades, donde cada una tiene una forma
reconocible antes de leerse—. `icons.py`: glifos de línea en un lienzo de 24×24 y trazo
1.8, todos en `currentColor`. `chip_grid` y `flow_steps` **sin** `icons_` emiten
exactamente el marcado de siempre (lo fija un test).

⚠ **Cinco de los dieciséis primeros iconos no sobrevivieron a 40 px, y eso solo lo dijo el
frame.** La multitud dibujada con arcos finos salía como una mancha, el engranaje de ocho
marcas sueltas se leía como un **sol**, el tablero de estrategia como un borrón, el martillo
como un alfiler y la maraña como una rayita. Un icono no es correcto porque el `path` lo
sea: lo es cuando se reconoce al tamaño en que se va a ver. Es la misma regla que §13
aplica a las animaciones, aquí a 24 píxeles de SVG.

`agent_swarm` es **el mismo tablero de agentes en cuatro estados** —`fanout` (el repo, la
marca y la rejilla llenándose), `solo` (uno y todo lo que se le echa encima), `roster` (los
146, y la mayoría bajando) y `team` (tres, con su icono)— porque el guion hace ese
recorrido y dibujarlo con cuatro componentes rompería la rima. Es `idea_fate` llevado a una
enumeración. ⚠ **Los 143 que sobran BAJAN de intensidad, no se apagan**: a opacidad 0 el
frame diría que dejaron de existir y la frase dice que siguen ahí sin usarse. Y son **un
solo tween** (`fade-to`, sobre un selector que casa con los 143), no 143 decisiones
editoriales — la «coreografía interna» de los objetos. ⚠ **A 0.18 el punto se confunde con
la retícula del suelo** y la frase pasa de «no los necesitas todos» a «solo hay tres»: 0.26.

⚠ **Las medidas del `roster` salen de que la banda `top` mide 660 px.** Con puntos de 52 y
hueco de 12, los 146 ocupan 11 filas de 64 = 704 px y el CONTADOR quedaba empujado por
encima de y0: sobre el frame se veía una rejilla sin cifra, o sea el dato del beat, fuera
de cuadro. A 40 px con hueco de 10 caben 18 por fila y el bloque entero suma 586.

`desktop_manager` existe para el beat «una aplicación de escritorio» cuando la grabación no
la tiene. Lo que la hace de ESCRITORIO y no un navegador es el semáforo y la ausencia de
barra de direcciones — `browser_chrome` alrededor diría «esto es una web», que suele ser la
frase anterior del guion.

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
sencillamente no ocurre. Misma firma que el tachado de `rewrite_line`. Puede costar todos
los tweens de un componente —ni entraban los 146 puntos del roster ni bajaban los 143— y no
se ve en ningún frame si el frame que se mira es anterior al tween.

**Cuando el guion habla de ANIMACIÓN, el gráfico hace lo que enuncia en vez de nombrarlo.**
`motion_demo` es el caso puro: sus cuatro variantes (`text`, `chart`, `captions`, `audio`)
son cuatro ejemplos hechos. El de captions usa **el mismo mecanismo del karaoke** (§5) — el
ejemplo de captions de la pieza son sus propios captions, que es la lectura más corta que
hay. Una quinta variante, `recap`, cierra la enumeración: las cuatro capacidades pequeñas y
quietas, más un hueco discontinuo que ninguna llena, y que solo rellena «criterio».

`keyframe_grind` dibuja un precio, no un objeto: arriba un vídeo que no hace NADA y abajo
los rombos cayendo **de uno en uno** con el contador subiendo. Un montón de keyframes ya
puestos diría «hay muchos»; el RITMO dice «esto lo pone alguien uno a uno», que es la frase
del hook. ⚠ Y el escenario de arriba no recibe ningún tween después de entrar: cualquier
gesto ahí contradiría el rótulo SIN MOTION que lleva pegado.

`agent_editor` es un editor con un chat debajo, para cuando la grabación del producto no
enseña su editor. ⚠ **Un lienzo vacío no puede ser un rectángulo negro.** Un área de
980×244 en negro durante los cuatro segundos del tecleo se lee como el panel roto que
`knowledge-base` documenta con `reveal`. Lo arregla lo mismo que enseña un editor de verdad
sin nada puesto: el ÁREA de trabajo dibujada —marco discontinuo, marcas de esquina, cruz de
centro y la pastilla de resolución—. Son CHROME, así que están desde el primer frame sin
adelantar nada del guion.

`idea_fate` es **la misma idea en dos estados**, no dos ideas: una instancia apagada con
sus dos salidas tachadas y otra viva, con un CORTE DURO entre ellas — la rima visual
aplicada a un estado, y el contraste se lee porque el corte deja ver qué cambió (el
mecanismo de `chat_unanswered`). Las salidas van apagadas, **no en rojo**: rojo diría
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

**Un guion que enumera un MÉTODO necesita una forma que `flow_steps` no tiene.**
`flow_steps` encadena pasos con flechas y los marca ✓/✕, o sea contesta «qué dispara qué»,
y cuatro pasos de un método no se disparan entre sí. Y sobre todo `flow_steps` **no tiene
estado intermedio** —sus pasos existen o no existen— y un método necesita que EXISTAN
VACÍOS y se llenen treinta segundos después.

`step_grid` es esa rejilla, y su hallazgo es de proceso más que de dibujo: resuelve de
frente el choque entre «muestra primero los 4 pasos» y «nada entra antes de su palabra». La
estructura entra entera al anunciarse y cada NOMBRE espera — cuatro huecos numerados, el
mismo idioma que `calendar` usa para la hora sin paciente. Vuelve al final con los mismos
slots y los cuatro VERBOS del guion: la rima visual aplicada al método. Cuando hay varias
lecturas posibles de un beat así, se le dibujan al usuario y elige (paso 3b).

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

`offer_stack` reparte un beat largo en tres alturas cuando el guion dice tres cosas: las
ofertas entran, de ellas suben las competencias que aparecen SIEMPRE, y al final se dibuja
lo que falta. **Lo que falta va con borde discontinuo, no en rojo**: un chip rojo diría
«esta competencia tiene un problema» y un hueco dice «aquí no hay nada», que es la frase.

`interview_chat` pone en el frame la respuesta floja Y lo que viene después de
ella, porque el paso no es «haz que te pregunte» sino «haz que REPREGUNTE cuando
una respuesta sea débil». **El orden de entrada es el del guion, no el de la
lógica**: la repregunta en «repreguntando» y el sello de débil dos segundos más
tarde, en «débil». Así el frame plantea primero que la IA insiste y solo al
final dice por qué, que es como está escrita la frase.

⚠ **Una barra de contenido en `surface3` sobre `surface` no se ve.** Las barras
de un documento resumido se leen como huecos en el panel en vez de como texto.
`text2` al 30 % (`rgba(text2, .30)`) sí. No es un par WCAG (no es texto) pero sí
es información, y medir contraste no lo cubre: se ve en el frame — y hay que
mirarlo en las dos paletas.

`tool_pair` son DOS marcas y el `+` que las une, cada pieza clavada a su palabra —
`tool_card` clava una sola y `tool_lineup` reúne marcas que ya se dijeron todas. Su
hallazgo es qué hacer con la segunda marca mientras no se ha nombrado: **el hueco se
dibuja**, con borde discontinuo y sin relleno, el mismo idioma que `calendar` usa para la
hora sin paciente. Montar la card ya ancha con la mitad derecha lisa se lee como un panel
roto; hacerla crecer anima `width`, que es reflow. Con el hueco puesto, los segundos de
espera son el beat: el frame plantea la pregunta que la palabra siguiente contesta. Y la
reaparición de la pareja YA formada no pasa por el hueco — con `t_slot == t_right` no se
emite ningún tween sobre él, porque un `chip-in` y un `badge-out` sobre la misma
`opacity` en el mismo instante dependen del orden de evaluación.

`claude_prompt` es el compositor de un asistente escribiéndose línea a línea, cada una en
su palabra. Es un MOCKUP declarado, no la captura redibujada: lleva la tipografía y el
suelo de la paleta, y lo que lo ata a la marca es el logo de la cabecera. ⚠ **Una línea
terminada necesita que le quiten el cursor.** `type-word` mete el `<span class="ccaret">`
DENTRO del innerHTML de su destino, así que con cuatro líneas seguidas acabarían cuatro
parpadeando a la vez; `caret-off` —la otra mitad de `type-word`— reescribe la línea sin él
en el instante en que arranca la siguiente. La última se queda parpadeando, que es lo que
hace una caja de texto con el foco puesto.

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

### Logos de terceros

`logos.mark()` pinta la marca (Simple Icons, entintada con `brand_tone()` para la paleta
activa, o vendorizada en `assets/logos/`); `scripts/fetch-logos.py --vendor <slug>` baja
las que no están en Simple Icons, con gates de resolución y de saneado del SVG. Las trampas
de vendorizar, todas pagadas:

- ⚠ **Un 200 no verifica que el archivo sea el logo.** Un `favicon.svg` puede responder 200
  y ser el icono de otra app (una plantilla sin cambiar); eso solo lo dice abrirlo.
- ⚠ **Una SPA responde 200 con `text/html`** a `favicon.svg`, `icon.svg`,
  `apple-touch-icon.png` o `logo.svg`: es su fallback, no una imagen. Se mira el
  `Content-Type` y el contenido; a veces la única imagen real es `favicon.ico`.
- ⚠ **Un favicon puede traer fondo blanco OPACO** alrededor de su tile redondeado, que sobre
  el suelo pintaría un cuadrado blanco. Se le devuelve el alfa con un relleno por
  inundación desde las cuatro esquinas y se recorta al tile.
- **Una marca sin icono cuadrado vendorizable** (403 a favicon, manifest y apple-touch, o
  uno de 32 px cuando el gate pide 220) se vendoriza como **wordmark oficial**; `_fit_svg`
  lo contiene sin deformar. Quien lo pinta le sube el `logo_px` para que llene el marco
  (≈118 en un marco de 140): al tamaño por defecto pesa la mitad que un icono cuadrado al
  lado.
- **Una marca vendorizada SVG sin `tile` lleva placa cuando el suelo no la sostiene.**
  `logos.mark_plate()` lee sus colores (fill, stroke, stop-color) y elige entre el suelo
  (`bg`) y la tinta (`text`) la placa que deja legibles (≥3:1) más colores de la marca;
  `mark()` la pinta detrás. Composio (toda blanca), Anime.js y HyperFrames van sobre
  placa de tinta en `claro`. Lo fija `tests/test_logos_paletas.py`. ⚠ `tool_card` NO mira
  el ratio que devuelve `mark()`: una marca PNG sin tile no la mide ningún gate y se
  revisa a ojo en las dos paletas.
- **Un repositorio no tiene marca propia**: la marca honesta de un repo es la de GitHub,
  que es donde vive. Inventarle un logotipo sería dibujar una identidad que no existe.
- Un SVG de marca con ids internos (gradientes, clip-paths) necesita `uid=` en cada
  `logos.mark()` (§9, trampa 7bis).

### Librería de objetos — 15, y crece por demanda

`clock` · `dental-chair` · `phone` · `card-payment` · `instagram` · `bottleneck` ·
`msg-card` · `answer-counter` · `knowledge-base` · `answer-approved` · `calendar` ·
`appointment-timeline` · `confirm-buttons` · `spreadsheet` · `kpi-card`.

Cada objeto es un SVG sobre tokens con `perspective()`/`rotateY()` ESTÁTICOS en un wrapper
hijo: GSAP solo toca `opacity`/`scale`/`x`/`y` del div exterior, así que el tilt no se
descuadra con un tween posterior. Un Motion Stage es **una serie contigua de segmentos con
un solo `fade_in`/`fade_out`** —nunca uno por segmento—: con un stage continuo, la clase de
bug de `check_no_black()` no puede ocurrir. Los objetos pueden ser **acumulativos** (se
quedan, y un delta horneado los cierra sobre el protagonista) o **sustituirse**, y esa
diferencia es una frase: cuatro trabajos incompatibles «al mismo tiempo» se acumulan.

⚠ **Una REJILLA no es una lista, y `knowledge-base` no sirve de hoja de cálculo.** El
documento de `knowledge-base` apila filas y comunica «esto existe suelto»; «una hoja con
cientos de filas» necesita **columnas con separadores**, porque una columna de barras
grises se lee como una lista de pendientes. `spreadsheet` es la rejilla: cabecera de
archivo, fila de columnas y 11 filas de barras **deterministas** (`(i*37 + j*53) % 41` — un
golden file no puede depender de un `random`, y el dato concreto no es el argumento: el
VOLUMEN lo es).

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
`go` va la tinta de `INK_ON_FILL["success"]`, nunca un blanco por costumbre — la regla de
`msg-card`.

**Un panel que se ACUMULA no se sustituye.** Cuatro instancias del MISMO objeto en los
cuatro slots `stack`: sustituirlas dejaría cuatro gráficos sueltos en vez de un panel, y el
argumento («cada indicador, una decisión») necesita verlos juntos.

**Un componente de librería se reutiliza cambiando lo que carga, no su código.** Una
secuencia de mensajes se sirve con `msg-card` y su `seal` verde carga la **ventana de
envío** (INMEDIATA · DÍA ANTERIOR · 3 H ANTES) en vez de un estado: el mismo sello que en
otro guion decía AUTOMATIZADO dice aquí cuándo sale el mensaje. Tres objetos nuevos pueden
bastar para cinco funciones. Es el nivel `library` del Resolver haciendo su trabajo.

**El tema de un stage es una frase.** Un stage de botones de confirmación se queda en
`primary` y el verde vive **solo en el botón que se espera pulsar**: teñir la escena de
`success` convertiría una opción del paciente en un mensaje de sistema — y además gasta un
`THEME_CHANGE`.

⚠ **Un hueco solo cuenta el tiempo si algo lo mide.** `appointment-timeline` nació con dos
paradas (Reserva y Cita) y un tramo discontinuo de 244 px en medio, y sobre frames eso
**no se leía como días pasando: se leía como un panel a medio hacer**. Con los días
intermedios puestos como nodos huecos **sin evento**, la misma ausencia se convierte en la
frase: hay un día que existe y no pasó nada en él. Y la discontinua va a `text3`, no a
`LINE_HI`: el hairline se pierde contra el suelo del panel.

⚠ **Una franja vacía se dibuja como HUECO, no como fila en rojo.** En `calendar`, la hora
sin paciente va con borde discontinuo y sin relleno, y es **más alta** que las demás. Una
fila roja con texto se lee como «esta cita tiene un problema»; un hueco se lee como «aquí
no hay nadie», que es la frase. Misma lógica que `chat_unanswered`: lo que comunica es la
AUSENCIA. El punto verde solo va en las franjas ocupadas.

**Un objeto puede aparecer dos veces sin repetirse**: primero **sin nombres** (nadie ha
dicho ninguna categoría todavía, y etiquetarlas adelantaría el guion) y luego con ellos, uno
por palabra. Dos instancias, dos stages, el mismo objeto en sus dos modos.

**Tres mecanismos de los objetos que valen más que los dibujos.**

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
`background-image` y cuenta la capa como opaca: **seis errores de golpe** en cuanto un
objeto lleva texto, y ninguno con objetos de SVG puro. El atributo va en el elemento
**ocluido** (probado en el grano primero: los seis errores no se movieron) y **no** en
`_object_html`, para que los objetos de SVG puro conserven la comprobación.

Y tiene un precio que hay que pagar a mano: los pares de contraste de ese texto **dejan de
muestrearse** (30/30 → 18/18). `0/0 no es que pase, es que no midió` vale igual para 18/18:
los pares que desaparecen se miden con `tokens.contrast()` y se anotan — en la paleta de
la pieza.

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

**Prompts:** pedir `no text, no letters, no words, no numbers`, y nombrar la paleta de la
pieza para que el resultado caiga dentro del sistema: `warm cream, terracotta, near-black
ink` (`claro`) · `warm near-black, terracotta, cream` (`oscuro`).

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
scripts/calibrate-hlg.py out/<n>-rough.mp4 5.5
scripts/make-hlg-lut.py assets/hlg-to-709.cube
ffmpeg -i out/<n>-rough.mp4 \
  -vf "lut3d=assets/hlg-to-709.cube,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv" \
  -c:v libx264 -crf 18 -g 30 -keyint_min 30 -pix_fmt yuv420p \
  -movflags +faststart -c:a aac videos/<n>/public/input-video.mp4
```

`setparams` es **obligatorio**: `lut3d` propaga las etiquetas de color del frame de
entrada, así que sin él el archivo sigue marcado como HLG. Los flags `-color_trc` /
`-color_primaries` por sí solos **no bastan**.

El objetivo del LUT **no es estilizar sino reproducir el original**; se recalibra por
pieza. Una calibración real de iPhone HLG quedó en gamma 1.65, gain 0.85, lift +0.06,
sat 1.20, error 6.6 (la conversión física pura daba 53); sus parámetros viven en
`assets/hlg-params.json`.

Enfoques descartados, no repetirlos: conversión física pura (sobresatura y aplasta los
negros) y curvas 1D por canal (manchas amarillas y azules en la piel).

**Si la fuente es SDR bt709** (lo habitual), este tramo se salta. `--sdr` sigue siendo lo
correcto.

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
   `build-composition.py` y falla dando el número exacto que falta, antes de renderizar.
   Dos casos que enseñó:
   · entre **dos takeovers seguidos** el fundido cruzado también abre hueco — el `off` no
     empieza en el primero, sino cuando el segundo ya está del todo puesto (el `off` es
     solo un ahorro de decodificación, no cuesta nada retrasarlo);
   · **el último visual no se funde a la salida**: el CTA tiene que estar puesto en el
     último frame, que es el que se congela cuando el reel vuelve a empezar.

   ⚠ Sobre el MP4 se comprueba con `blackdetect … pix_th=0.03`. Con el 0.10 por defecto,
   en `oscuro` salta el propio suelo de la paleta (luma ~20) y cualquier frame que sea solo
   fondo cuenta como negro. Si a 0.03 no aparece nada, no hay negro real.
6b. **Un stage EN PANTALLA SIN OBJETOS no cae a negro, y por eso no se veía.** Es la
   hermana de la trampa 6 y nace del mismo fallo: el suelo del stage **sí se pinta** —con
   su viñeta y su retícula—, así que `check_no_black()` no encuentra nada. Lo que se ve es
   un suelo vacío con un subtítulo encima, y se lee como un error de montaje. Huecos así
   de 0.7–1.6 s llegaron a entregarse. Ahora lo mide `edl_metrics.bare_stage_gaps()` y lo
   reporta la métrica `max_bare_stage`.

   **El arreglo es mover el LÍMITE del segmento, no el evento.** La ventana de un segmento
   empieza en su primera palabra, así que hacer que el stage empiece en la palabra del
   objeto cierra el hueco **sin adelantar el guion** — que es lo que pasaría adelantando el
   objeto a una palabra que todavía no lo nombra. Suele salir gratis: las palabras previas
   vuelven al presentador, donde además suelen estar mejor.

6c. **El visual que llega al FINAL no se funde a la salida — y el emisor no lo cumplía.**
   La regla ya estaba escrita en la trampa 6 pero el emisor de visuales le ponía
   `fade_out` a TODOS, así que un CTA con `end: null` pasaba sus últimos 0.26 s
   apagándose: en el último frame, el titular del CTA a medio fundir. `check_no_black` no
   lo caza porque solo mide la cobertura ENTRE visuales, no la cola. Arreglado en
   `build-composition.py`: si `ve >= dur − 1/FPS`, no se emiten ni el `to` ni el `set` de
   salida. Se verifica extrayendo el último frame con `-sseof`.

7bis. **Un SVG de marca inlineado dos veces se renderiza VACÍO la segunda vez.** Una marca
   como la de Canva trae seis `<radialGradient>` con ids fijos de exportador
   (`_2002046508__a`…) y seis `fill="url(#…)"` que los apuntan. El navegador resuelve cada
   `url(#id)` al PRIMER elemento con ese id del documento, así que en cuanto el renderer
   oculta el host de esa primera instancia las demás pierden el relleno: **el marco se
   sigue viendo y la marca desaparece.** Se caza sobre snapshots, nunca en el JSON. Dos
   capas de arreglo: `logos.mark(uid=…)` renombra los ids por instancia (sufijo de sha1 del
   `uid`, no un contador — un contador dependería del ORDEN de las llamadas y el mismo plan
   compilado dos veces daría HTML distinto), y `check_unique_element_ids` en
   `build-composition.py` falla sobre el HTML ya ensamblado si algún id se repite. Llamar a
   `mark()` sin `uid` sobre un SVG con referencias internas ahora **lanza**, en vez de
   renderizar un hueco en silencio. ⚠ El regex del gate va con `(?<![-\w])id="`, no con
   `\bid="`: con `\b` casa dentro de `data-viz-id="…"` y los doce visuales salían como
   duplicados — un falso positivo que paró una compilación buena.

7. **Un trazo SVG se prepara en t=0, no al dibujarlo.** El `stroke-dasharray` montado en
   el mismo instante que el tween deja la línea entera desde el primer frame.
8. **GSAP**: `left`/`top` tartamudean → usar `x`/`y`. Toda salida necesita `tl.set` de
   kill duro. Nada de `translate(-50%,-50%)` en algo que GSAP anime — centrar con flex.
   Dos tweens sobre la misma propiedad necesitan `overwrite: "auto"`.
9. **Un emoji en un mockup rompe el check de contraste sin verse.** El navegador lo pinta
   con su propia paleta, pero el linter lee el `color` heredado del elemento —negro si no
   se declara— y mide un par imposible (1.11:1 contra un suelo oscuro) que tira la pieza
   entera, viéndose perfecto en el frame. Un glifo dibujado en `currentColor` lo tiñe el
   estado del componente y además se puede medir.
10. **El contraste de un rótulo durante su FUNDIDO es una limitación conocida.** El
    muestreo de `check` puede caer dentro de la entrada o la salida de un rótulo
    (200–350 ms), y ahí el texto se compone con lo que haya detrás: sobre una pared de
    fondo del mismo valor que la tinta, el par cae a 1.5–2.1:1 en pleno fundido y vuelve a
    su valor asentado (5–10:1) al terminar. Es del fundido de las tarjetas de todo el
    proyecto, no del diseño de un rótulo: queda medido y no tocado, y el aviso se
    comprueba sobre el PNG asentado antes de darlo por bueno.

### CLI

- Un `public/index.motion.json` de una composición **anterior** hace fallar `check` con
  `motion_selector_missing`. Reescribirlo o borrarlo.
- `snapshot --at 1.2,7.6,20.5` — lista separada por comas; repetir `--at` no acumula.
- Los checks de **contraste solo corren si hay muestras**: `0/0` no es que pase, es que no
  midió.
- Esperar un render por **el PID concreto**, nunca porque el archivo dejó de cambiar ni
  con `pgrep -f "hyperframes render"`: el propio shell que espera lleva esa cadena en su
  línea de comando, se caza a sí mismo y el bucle no sale nunca.
- **La salida de una compilación se mira siempre.** `build-composition.py … >/dev/null 2>&1
  && npx hyperframes check` cortocircuitó en un `UnboundLocalError` y el `check` siguiente
  validó —y dio por bueno— el `index.html` ANTERIOR. El síntoma fue desconcertante: el CSS
  emitido no contenía un cambio que sí estaba en el fuente.
- Avisos abiertos que no bloquean: `composition_file_too_large`,
  `timeline_track_too_dense`, `pointer_events_none` y
  **`gsap_repeated_fromto_without_baseline`** sobre los elementos de keyword. Este último
  es **deuda real del emisor de keywords** de `build-composition.py`, no de ninguna pieza:
  dos `fromTo` sobre el mismo `#cNkM` sin un `tl.set` de base a t=0. Sin efecto visible
  —el bloque de subtítulo está a opacidad 0 hasta su propio instante— pero crece con cada
  keyword (del orden de una docena por pieza).

---

## 10. Estructura del proyecto

```
editor-videos/                      ← el ESTUDIO: una carpeta, muchas piezas
├── CLAUDE.md                       ← bitácora
├── .env                            ← ASSEMBLYAI_API_KEY · KIE_API_KEY (chmod 600)
├── .claude/skills/
│   └── video-tech-premium/         ← LA SKILL: el estilo y el flujo completo
│       ├── SKILL.md
│       ├── references/             design · plan-schema · planner · triband · visuals
│       │                           motion · sound · color · gotchas
│       ├── scripts/                tokens · mockups · objects · icons · logos
│       │                           build-composition · edl-* · screen-tour · tour-map
│       │                           refine-timings · voicing · audit-breaths
│       │                           palette-sheet · make-music-bed · …
│       ├── styles/                 perfiles de estilo del EDL (motion-explainer)
│       └── assets/                 8 fuentes · 19 efectos · GSAP
├── scripts/  →  enlace a los de la skill
├── docs/superpowers/               ← planes, specs y spikes de diseño
├── tests/                          ← la suite (pytest)
│   ├── fixtures/                   ← datos de piezas pasadas, SOLO como datos de prueba
│   │                                 (misma estructura que un proyecto: transcripts/,
│   │                                 cuts/, videos/<n>/, assets/)
│   └── golden/10.plan.json         ← el plan compilado de la fixture 10, congelado
│
├── assets/                         ← lo que se reutiliza entre piezas
│   ├── music/bed-tech.mp3          ├── logos/ (+ meta.json)
│   ├── gen/ledger.json             ├── sfx/
│   └── hlg-params.json · hlg-to-709.cube · manifest.json
│
│   — lo que el pipeline crea al editar una pieza (fuera del repo lo pesado) —
├── VIDEOS ORIGINALES/<n>/          ← video.MOV · guion.md · pantalla.mov
├── VIDEOS EDITADOS/                ← copias finales para publicar
├── assets/audio/<n>.flac · assets/face-<n>.json
├── transcripts/<n>.json · cuts/<n>.json
├── out/<n>-rough.mp4 · out/palette-sheet/
└── videos/<n>/
    ├── edl.json                    ← LA PIEZA, si va por el camino del EDL
    ├── plan.json                   ← LA PIEZA (o lo que compila el EDL)
    ├── screen-tour.json            ← el recorrido de la grabación de pantalla
    ├── screen-tour-b.json          ← un SEGUNDO recorrido, si hace falta (ver abajo)
    ├── output.mp4                  ← ENTREGABLE
    └── public/                     ← index.html + input-video + assets copiados
```

`VIDEOS ORIGINALES/`, `VIDEOS EDITADOS/`, `out/`, el audio intermedio y los MP4 están en
`.gitignore`. **El `edl.json` y el `plan.json` de cada pieza sí se commitean**: si `videos/`
se borra sin commit, no hay de dónde recompilar la pieza ni contra qué comparar su golden.

La no-regresión del camino EDL es `tests/golden/10.plan.json`, compilado desde
`tests/fixtures/videos/10/edl.json` (`test_golden.py`): un slot movido en `objects.py` o un
cambio en `edl_compile.py` que mueva un tiempo lo rompe en vez de descubrirse tres piezas
después. Si se toca el compilador o el schema, ese es el test que hay que mirar.

**Dos momentos de la misma grabación separados por un gráfico son dos archivos, no dos
tramos.** El renderer arranca cada `<video>` en 0 (`data-media-start="0"`), así que un
segundo `screen-video` que apunte al mismo mp4 volvería a empezar por el principio. Por eso
una pieza puede llevar `screen-tour.json` (la primera parte del recorrido) y
`screen-tour-b.json` (la segunda), con un `keyword_hero` en medio.

**Un solo estudio, muchas piezas.** Lo que se reutiliza y justifica no abrir un proyecto
por video: la calibración de color, el ledger de assets de IA, la cama musical, los logos
vendorizados y el `.env`.

`scripts/` es un **enlace**, no una copia: las copias divergentes fueron un problema real.

---

## 11. Comandos y entorno

```bash
npx hyperframes check public     # validar
npx hyperframes preview          # Studio en localhost:3002
npx hyperframes snapshot public --at <s1,s2,s3>
npx hyperframes doctor
scripts/palette-sheet.py         # hoja de las dos paletas → out/palette-sheet/
```

CLI **0.7.105**.

| Check | Estado |
| --- | --- |
| FFmpeg · Chrome · Node 24 | ✅ |
| **Memoria** | ⚠ Cerrar apps antes de renderizar |
| `zscale` en ffmpeg | ❌ Sin libzimg ni libplacebo → por eso el LUT propio |
| HeyGen (voz/música de catálogo) | ❌ Sin credencial → la música se sintetiza (§12) |
| Docker | ❌ Solo afecta al render containerizado |

Dependencias Python: `pillow`, `fonttools`, `brotli`, `numpy`,
`opencv-python-headless<5` (la versión 5.x quitó `CascadeClassifier`).

---

## 12. Sonido

Tres capas y una jerarquía que no se negocia: **la voz manda siempre**.

```
voz  pista 10   ·   música  pista 11   ·   efectos  pista 12+
```

### El efecto marca algo que pasa en imagen

No hay relleno ambiental. Si no puedes señalar en el frame qué marca ese efecto, sobra.
Los tiempos son **los mismos beats del transcript que mueven la imagen**.

**Un beat sin sonido puede ser una decisión.** Un stage que dibuja el silencio («en esos
días nadie escribe») va sin efecto: ponerle sonido al silencio lo contradice.

### El volumen se CALCULA, no se escribe a mano

Hay **27 dB** entre el efecto más caliente (`impact-bass-1`, media −5.0 dB) y el más flojo
(`chime`, −32.4 dB). Puestos a un número parecido, el impacto tapa la voz y los clicks no
existen.

```
v = min( 10^((OBJETIVO_MEDIA − media)/20),   10^((TECHO_PICO − pico)/20),   1.0 )
```

Con la fórmula, los impactos quedan en ~0.035–0.053 y el chime en ~0.44: la calibración
funcionando.

Un efecto que ya está a `volume 1.0` y cae sobre habla fuerte (el `error` de un hook, en la
palabra que lo justifica) queda solo +3–4 dB sobre su entorno. **Es correcto**: la voz
manda, y no se sube a costa de ella.

### El ATAQUE también se calcula

Mismo error de forma que el volumen escrito a mano: **dar por hecho que los ficheros
vienen alineados.** `data-start` se escribía con el tiempo del beat, pero el navegador
empieza a REPRODUCIR ahí y **16 de los 19 efectos de la librería traen silencio de
cabecera**:

| efecto | cabecera | efecto | cabecera |
| --- | --- | --- | --- |
| `riser` | **1727 ms** | `ping` | 323 ms |
| `whoosh-cinematic` | **1553 ms** | `glitch-3` | 244 ms |
| `error` | **604 ms** | `pop` | 116 ms |
| `typing` | 437 ms | `glitch-1` | 114 ms |
| `chime` | 416 ms | `whoosh` / `whoosh-short` | 76 ms |

Un `error` declarado en «no sabías hacerla» sonaba **sobre la palabra siguiente**. Se oye
—por eso nadie lo vio— pero marca otra cosa, y esta sección dice que el efecto marca algo
que pasa en imagen. Llegó a haber 34 de 38 efectos de una pieza sonando tarde.
`_lead_in()` lo mide (envolvente al 5 % del pico del propio fichero, no un umbral absoluto
en dB, que castigaría a los efectos flojos) y `build_sfx` **adelanta el `data-start` esa
cabecera**, así que lo que el plan declara es cuándo se OYE el efecto. Por debajo de
`SFX_LEAD_MIN` (30 ms, menos de dos frames) no se compensa: eso es ruido de medición, no
retraso.

Cuando la cabecera no cabe antes del segundo 0 —un efecto declarado en `t=0.0`— la
compilación **avisa con el número** en vez de callarse (un `whoosh-short` en t=0 suena
76 ms tarde, y queda escrito en la salida).

⚠ **Cómo se encontró, que importa más que el arreglo.** El filtro adaptado —correlar la
forma de onda del efecto contra el residuo del MP4— daba **correlación cero** para
`error`. La primera lectura fue «el efecto no está». La segunda, al abrir el fichero, fue
que la plantilla de 350 ms con la que se correlaba era **silencio puro**. *El fallo del
test era el hallazgo*: cuando una medición da un cero imposible, lo primero que se revisa
es la medición, y a veces eso destapa el bug de verdad.

### La cabecera de la mezcla

**El metraje de iPhone llega pegado al techo**: puede traer miles de muestras a 0 dB
*antes* de tocarlo — viene así de cámara. Sumarle música y efectos satura.

`voice_gain` (por defecto **0.70**) baja la voz para abrir margen, y el generador
**desplaza los mismos dB** los objetivos de efectos y música, así que el balance no cambia:

```
voz ×0.70 → −3.10 dB   ·   efectos −27→−30.1 dB   ·   música −34→−37.1 dB
```

Sin el ajuste, la mezcla llegaba a pico 1.62 con más de 13 000 muestras saturadas; con él,
el pico queda en −2…−3.3 dB por canal y 0 muestras saturadas.

### Música

Cama **sintetizada** (`make-music-bed.py`): libre de licencia, offline y reproducible.
La Menor, 100 BPM, Am–F–C–G.

**El diseño importa más que el volumen.** Vive 14 dB bajo la voz, así que no compite por
nivel sino por **espectro**: deja **vacía la banda 300–3000 Hz** donde viven las
consonantes. Medido: sub −6.8 dB · pad −1.1 dB · **hueco de voz −18.1 dB** · aire −33 dB.

⚠ `volumedetect` **loguea a nivel info**.

### Verificar la mezcla sobre el MP4

Cada medición tiene una trampa, y todas se pagaron:

- ⚠ **El pico se mide POR CANAL.** La mezcla a mono de ffmpeg (`-ac 1`) **suma** los dos
  canales (+3 dB): da pico +0.26 dB y 17 muestras saturadas sobre un archivo cuyos canales
  reales van a −2.53 dB sin una sola saturada. Se mide con `astats` por canal.
- ⚠ **Y no solo el pico: cualquier razón entre dos archivos se mide con los dos en
  estéreo.** Una ganancia de voz de 0.493 frente a 0.700 declarada parecía un fallo de
  mezcla y era la referencia decodificada con `-ac 1`: 0.493 × 1.414 = 0.697.
- ⚠ **La ganancia de voz se mide donde la señal domina al fondo**, no en promedio. La
  mediana sobre todas las ventanas de 100 ms con voz la sobreestima (0.72–0.74) porque en
  las flojas suman la cama musical y el residuo del códec; filtrando por energía converge
  (p50 ~0.71 · p85 ~0.70 · **p95 ~0.70**) al valor declarado.
- **El AAC mete ~21 ms de priming**: antes de comparar muestra a muestra contra el
  original, se alinea por correlación cruzada.
- **La música se comprueba aislándola**: restando la voz alineada del MP4, la cama queda
  en −35…−39 dB (objetivo −37.1); en la cola, donde no hay voz, se ve directa (−31 dB
  frente a −61 del corte de voz sola).
- **Los efectos se localizan por FILTRO ADAPTADO a la forma de onda real de cada archivo**,
  no por envolvente. El salto de envolvente mide si el efecto DESTACA; el filtro adaptado
  mide si ESTÁ. Bajo habla fuerte el residuo del códec sube ~14 dB por debajo de la voz y se
  come un `pop` de volumen 0.25: la envolvente ve 10 de 15 efectos y el filtro los 15, con
  desfase submilimétrico. `riser` y `typing` no tienen ataque por diseño y no los ve la
  envolvente nunca.
- ⚠ **La plantilla del filtro tiene que cubrir el efecto entero, no el ataque que uno
  espera que tenga.** El `chime` es una campana de 2.5 s de ataque lento: con 300 ms da
  correlación 0.12; con la campana completa y la banda limitada a su parcial dominante
  (3512 Hz), **1.04** a +3.0 ms. El `riser` es una rampa de 10 s: 0.21 con 300 ms, **0.82**
  con 1.6 s. Aun así la amplitud del `chime` no se mide bien con la plantilla entera,
  porque su cola se solapa con la música en el residuo: presente y localizado, amplitud
  sin medir.

---

## 13. Reglas duras

**Hacer**
- Correr `detect-format.sh` antes de crear el proyecto. El formato se mide.
- Identificar el material por su guion y su transcript, no por el número de carpeta.
- Medir la cara, no estimarla.
- **Cuadrar el transcript con el audio antes de cortar** (`refine-timings.py`), y
  re-transcribir suelto el tramo que salga con la alineación rota.
- **Leer el transcript contra el guion**: siglas, marcas, palabras que faltan. Y comparar
  cada `end` con el `start` siguiente.
- **Cortar con `--audio`** (`plan-cuts.py … --audio assets/audio/<n>.flac`): la pausa
  que queda tiene que ser SILENCIO, no una respiración.
- **Correr `audit-breaths.py` antes de seguir** (paso 4b). Sale con código 1 si queda
  una respiración en el corte, y ahí se para el flujo: **cero islas sin voz fuera de un
  span de palabra, o no se entrega.** Audita el CORTE —voz sola— con el umbral de la
  FUENTE; el MP4 mezclado da falsos positivos porque la cama musical tampoco tiene tono.
- **Declarar `palette` en cada pieza y revisar `scripts/palette-sheet.py` cuando se toque
  `tokens.py`.**
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
  anterior y todo parece en orden.
- **Medir la ganancia de voz donde la señal domina al fondo** (p95 de energía), no en
  promedio: la cama musical suma por debajo y la sobreestima.
- **Medir el pico por canal**, y cualquier razón entre archivos con los dos en estéreo:
  `-ac 1` suma los canales (+3 dB).
- **Verificar la grabación de pantalla con la maquetación MEDIDA, no mirada.** Una
  correlación cruzada columna a columna entre frames dice en qué tramos la página está
  quieta de verdad; elegir el recorte a ojo y comprobar dos frames no encuentra la meseta,
  solo confirma o desmiente el tramo que ya se eligió.
- **Empezar un visual en la palabra de su PRIMER elemento, no en la del beat.** El
  retraso del entrante se suma a los ~130 ms del relevo en vez de esconderse dentro, y
  `check_band_top_covered` no lo ve, porque mide cobertura declarada y no luma.
- **Barrer la luma de la banda `top` cada 0.5 s, no cada 2.** Un barrido grueso salta
  justo por encima de los relevos, que es donde vive el hueco.
- **Probar un icono al TAMAÑO en que se va a ver.** Un icono puede compilar perfecto y no
  reconocerse a 40 px.
- **Leer el aviso de «sonido audible sin transcribir» como una PALABRA posible, no solo
  como una respiración.** Con tono (armonicidad alta) y ataque limpio es voz, y AssemblyAI
  puede haberla colocado en otro sitio: `plan-cuts` vería una pausa y se comería la
  palabra.
- **Re-transcribir suelto TODO tramo con alineación imposible.** Unas veces todos los
  avisos son falsos positivos y otras alguno es real, a veces un corte sobre el ataque de
  una palabra. La conclusión no se hereda de la pieza anterior.
- **Probar el camino de FALLO de cada gate nuevo.** Un gate que nunca ha fallado no es un
  gate: su test incluye el caso que lo hace saltar.
- **Commitear el `edl.json` y el `plan.json` de cada pieza.** Lo pesado está fuera del
  repo a propósito; lo que define la pieza no.

**No hacer**
- Estilizar el metraje. El color reproduce el original. El usuario lo nota.
- Tapar la cara con subtítulos.
- **Estirar el borde de una palabra sobre un sonido que no tiene tono.** Suena, y hasta
  suena fuerte, pero es una respiración — y una vez dentro del span ya no la ve nadie.
- Fiarse de la envolvente para decidir QUÉ es un sonido. Dice cuánto, no qué.
- Corregir en el subtítulo lo que él dijo distinto del guion escrito: se corrigen marcas
  mal oídas, no frases.
- Resaltar todas las palabras del subtítulo a la vez.
- Adelantar el guion: un logo no aparece antes de que se nombre.
- **Escribir un color a mano en un componente: todo sale de `tokens` (lo vigila
  `test_paletas_consumidores.py`).**
- Importar un escalar de color por nombre (`from tokens import LINE`): queda congelado en
  la paleta de arranque. Se lee `TK.LINE`.
- Arreglar un contraste en el componente: se arregla la regla de derivación en
  `tokens.py`.
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
  linter lee el `color` heredado, que sin declarar es negro: da un contraste imposible y
  tira la pieza entera, viéndose perfecto en pantalla. Un glifo dibujado en `currentColor`
  lo tiñe el estado del componente y además se puede medir.
- **Escribir un selector ya prefijado en un mockup.** `build_visuals` le antepone
  `.viz[data-viz-id="…"]`; duplicado, GSAP no encuentra el destino y `check` lo cuenta como
  aviso de runtime con 0 errores — el gesto no ocurre y nada falla.
- **Tratar la re-transcripción suelta como un árbitro.** Es una segunda opinión: puede
  estirar una palabra sobre silencio o comerse la plosiva inicial y dar la razón al pase
  largo. **El árbitro es el audio** (`voicing.py` + la envolvente), que es lo único que
  distingue un ataque de un silencio.
- **Fiarse de una medición de desplazamiento para decidir si una grabación está quieta.**
  Una correlación cruzada no distingue un scroll de un CONTADOR de la página animándose:
  puede descartar por «cambio» la mejor ventana del tour (las cifras reales trepando). La
  métrica dice dónde mirar; lo que hay ahí lo dice el frame.
- **Dar por buena una animación sin mirar el frame.** Una marca vacía o un CTA apagándose
  compilan limpios, pasan `check` con 0 errores y se ven en un snapshot.
- **Vendorizar un logo sin abrirlo.** Un 200 no verifica que sea el logo, y una SPA
  devuelve `text/html` con 200 a cualquier ruta de icono.
