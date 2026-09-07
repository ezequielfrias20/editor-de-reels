# Lenguaje de edición EDL + Motion Design — diseño

**Fecha:** 2026-09-07 · **Estado:** **aprobado** — spec cerrada, lista para plan de implementación
**Ámbito:** evolución en sitio de la skill `video-tech-premium`
**Empieza a aplicarse en:** pieza 10. Las piezas 1–9 quedan **congeladas**.

> ## Principio central
>
> **No decorar el diálogo. VISUALIZAR el diálogo.**
>
> Todo lo que sigue existe para hacer ese principio *verificable* en vez de aspiracional.

---

## 0. Decisión de herramienta y alcance

### HyperFrames se queda. Remotion no aporta nada que falte

El brief de motion design no pide ninguna capacidad que HyperFrames no tenga. Pide **otra
doctrina editorial y otro sistema visual**, que son capas por encima del renderer.

| Brief | Estado |
| --- | --- |
| 3 cámaras virtuales con corte duro | Ya es el modelo `shots` |
| Captions semánticos 2–6 palabras, una keyword | Ya es la doctrina de `CLAUDE.md` §5 |
| Motion Stage a pantalla completa | Ya es `visuals` con `role: takeover` |
| Acumulación visual | Blueprint `overwhelm-surround` |
| Kinetic typography | Blueprint `kinetic-type-beats` |
| Objetos 3D | Adapter `three` (Three.js dirigido por `hf-seek`) + TypeGPU |
| Iconos animados | Regla `svg-icon-enrichment` + adapter Lottie |
| Motion blur | Regla `motion-blur-streak` |
| UI demonstrations | `screen-tour.py` — **mejor que el brief**: grabación real dirigida |
| SFX atados a presets, voz por encima | Ya existe, con volumen **calculado** por medición |
| EDL antes de renderizar | Lo único genuinamente nuevo |

Cambiar a Remotion costaría reescribir la única capa que hoy funciona y perdería los gates
que ya cazaron bugs reales: `check_no_black()` (4 huecos en la pieza 3, 1 en la 4), los
checks de contraste WCAG (44/44 en la pieza 2), el `cropdetect` de barras negras y el
`exclude` del indicador de dev. Todo lo de *arriba* del renderer —transcribe,
refine-timings, plan-cuts, measure-face, screen-tour, el LUT HLG, la cama musical— es
ffmpeg y Python y se queda igual con cualquiera de los dos. Señal adicional: existe una
skill `remotion-to-hyperframes`, y va en esa dirección.

### El sistema visual actual se conserva

El brief pide charcoal-azul `#101823` + acento cyan + Poppins. **Se traduce a los tokens
existentes, no se copia literal.** Razón: `CLAUDE.md` documenta que el violeta *sale del
producto real que se muestra en pantalla (el ERP), así que el gráfico y el screenshot
pertenecen al mismo mundo.* Con cyan, cada aparición del ERP rompería esa pertenencia.
Además conserva las 8 woff2 vendorizadas y los ~44 pares de contraste ya verificados.

---

## 1. Gramática editorial y reglas de decisión

### El procedimiento de tres preguntas

Por segmento, en este orden:

1. **¿Qué se dice?** → del transcript remapeado. Nunca se reescribe.
2. **¿Qué significa?** → `semanticIntent`, una frase propia.
3. **¿Existe una representación concreta de esto mediante un objeto, un estado, una
   cantidad, una relación, una secuencia, un contraste o una interfaz?**
   Si no existe ninguna de las siete, **vuelve al presentador**.

La tercera pregunta es el filtro anti-decoración. Para que ampliarla no la convierta en una
puerta abierta, `representationType` es un **enum cerrado y obligatorio** en todo segmento
con visual.

| `representationType` | Se visualiza como | Ejemplo (pieza 10) |
| --- | --- | --- |
| `OBJECT` | El objeto | «el teléfono» → teléfono |
| `STATE_CHANGE` | El mismo objeto, transformado | «contestaste a las 7» → el reloj de las 11 con las agujas movidas |
| `QUANTITY` | La cifra o la repetición | «escribió a 3 clínicas más» → 3 burbujas |
| `RELATION` | Origen → operador → destino | mensaje → IA → respuesta |
| `SEQUENCE` | Pasos encadenados | `flow_steps` |
| `CONTRAST` | Dos estados enfrentados | `rate_mismatch` |
| `INTERFACE` | La grabación real | el ERP |

### Tabla de decisión — qué HACE la frase, no de qué habla

| Lo que la frase HACE | `sceneType` | Por qué |
| --- | --- | --- |
| Afirma, provoca, pregunta, remata | `A_ROLL` + `CLOSE` | La cara **es** el argumento |
| Nombra una cosa concreta de pasada | `A_ROLL_ICON` | No merece perder al presentador |
| Nombra algo que se puede ver | `MOTION_STAGE` | El objeto explica más rápido |
| Enumera carga, exceso, «todo a la vez» | `MOTION_STAGE` acumulativo | Los objetos **se quedan** |
| Es la tesis y cabe en 1–4 palabras | `KINETIC_TYPE` | La palabra es el gráfico |
| Habla del producto real | `UI_DEMO` | La grabación gana a cualquier gráfico |
| Pide una acción | `CTA` | Vuelve el presentador, un solo elemento |
| Nada de lo anterior | `BROLL` | Último recurso |

### Los dos números del brief, convertidos en métricas

**Presencia del presentador** — banda editorial configurable, no criterio rígido:

```jsonc
"presenter_share": {
  "target": [0.45, 0.60],     // informa
  "warn":   [0.35, 0.70],     // avisa
  "fail":   [0.20, 0.85],     // falla: extremos, no criterio
  "exclude_ui_demo": true
}
```

`exclude_ui_demo` saca del denominador el tiempo de demostración de producto. Sin eso, un
reel cuya demo legítima dura 15 s obligaría a volver al presentador solo para cuadrar un
porcentaje. Se informan las dos cifras, la cruda y la ajustada.

**Ritmo, en dos niveles.** Los captions por sí solos no pueden satisfacer la regla:

| Nivel | Eventos que cuentan | Hueco máximo |
| --- | --- | --- |
| `micro` | todos los macro **+** `CAPTION`, `KEYWORD` | 2.5 s |
| `macro` | `SCENE`, `CAMERA`, `OBJECT_IN`, `OBJECT_EXIT`, `OBJECT_STATE`, `STAGE_CLEAR`, `THEME_CHANGE`, `TYPE_BEAT`, `UI_ACTION` | 4.5 s |

`SFX` no cuenta en ninguno: no es un cambio visual. La excepción a ambos es `"hold": true`
con su `reason` — el brief pide *quietud antes del clímax*, y una quietud deliberada debe
estar **escrita**, no colada en silencio.

---

## 2. Contrato del EDL

`videos/<n>/edl.json` sustituye a `plan.json` **como el archivo que se escribe**.
`plan.json` pasa a ser un artefacto compilado que ya no se edita a mano.

```jsonc
{
  "format": "REEL",
  "piece": 10,
  "style_profile": "motion-explainer",
  "transcript": {
    "src": "transcripts/10-rough.json",   // ← la línea del CORTE, no la del fuente
    "fingerprint": "sha256:…"             // falla si el transcript cambió
  },
  "planner": { … },                    // trazabilidad, §11 — NO entra en compilación
  "voice_gain": 0.70,
  "music": { … },                      // igual que hoy
  "segments": [ … ],
  "plan_overrides": [ … ]              // lista tipada con whitelist
}
```

### El segmento

`spokenText`, `startTime` y `endTime` **no son campos que se escriban**. El compilador los
deriva del transcript y los reescribe como `_spokenText` / `_t`, usando la convención `_`
que el generador ya ignora: legibles para un humano, sin autoridad sobre nada.

| Campo | Papel |
| --- | --- |
| `words` | `[57, 72]` — índices en el transcript. **La única fuente de tiempo** |
| `semanticIntent` | Lo que la frase significa |
| `sceneType` | `A_ROLL`·`A_ROLL_ICON`·`MOTION_STAGE`·`KINETIC_TYPE`·`UI_DEMO`·`BROLL`·`CTA` |
| `representationType` | Enum de 7, obligatorio si hay visual |
| `camera` | `WIDE`·`MEDIUM`·`CLOSE`·`OFF` |
| `defaultPreset` | Preset por defecto; cada evento puede sobrescribirlo |
| `transitionIn` / `transitionOut` | En el límite. Reglas abajo |
| `events` | El segundo nivel temporal |
| `hold` | Opcional. Autoriza la excepción a los gates de ritmo |
| `reason` | Obligatorio. No puede repetir `semanticIntent` |

### Los eventos

Sin este segundo nivel, el compilador acabaría decidiendo *cuándo* entra cada objeto — que
es trabajo creativo disfrazado de código.

Tres verbos para los objetos:

| Evento | Qué hace | Consecuencia |
| --- | --- | --- |
| `OBJECT_IN` | Crea la instancia. Una vez por `instanceId` y stage | — |
| `OBJECT_STATE` | La muta: transform, tono, o estado propio (`{"time":"19:00"}`) | — |
| `OBJECT_EXIT` | La retira | Su `instanceId` queda quemado en ese stage |
| `STAGE_CLEAR` | Retira **todas** las instancias vivas, con preset de salida | El stage sobrevive y los `instanceId` **vuelven a estar libres** |
| `THEME_CHANGE` | Cambia el lenguaje semántico de color | El stage sobrevive (§7) |

Más `CAPTION`, `KEYWORD`, `CAMERA`, `TYPE_BEAT`, `UI_ACTION` y `SFX`.

**Todos los eventos se anclan a una palabra**, no a un float: `atWord` + `offset` opcional.
Si `refine-timings.py` corrige un borde —movió 9 en la pieza 3 y 10 en la 4— **todos los
beats se mueven solos**. Hoy son floats hardcodeados que se desincronizan en silencio. Un
`offset` por debajo de −0.12 s **avisa**, por la regla dura de no adelantar el guion.

`CAPTION` y `KEYWORD` **también van por rango de palabras**. Esto hace que la comprobación
«la keyword está dentro del caption» sea exacta, y que el instante en que la keyword se
enciende salga del `start` de su propia palabra — literalmente *«en el instante exacto en
que se pronuncia»*, hoy estimado a mano.

### Qué transcript referencia el EDL — la trampa de las dos líneas de tiempo

Cada pieza tiene **dos transcripts**, y el EDL solo puede usar uno:

| Archivo | Línea de tiempo | Ejemplo (pieza 10) |
| --- | --- | --- |
| `transcripts/<n>.json` | **Fuente**, antes de cortar | 131 palabras, 0.42 → 46.21 |
| `transcripts/<n>-rough.json` | **Corte**, después de `rough-cut.sh` | 130 palabras, 0.18 → 43.88 |

**El EDL referencia el del CORTE**, porque la regla ya establecida es que *todos los tiempos
van en la línea del corte, no en la del fuente*. Apuntar al del fuente produce un EDL que
valida perfectamente y cuyos beats caen todos desplazados — en la pieza 10, hasta **3 s** al
final.

Y las dos no son solo un desplazamiento constante: en la pieza 10 el corte se llevó **una
palabra entera** (131 → 130), así que a partir de ese punto **los índices tampoco coinciden**.
No hay forma de convertir uno en otro sin volver a alinear.

> Por eso `transcript.src` es un campo **obligatorio y explícito** en el EDL, y el
> `fingerprint` se calcula sobre ese archivo concreto. Es la única defensa contra un EDL que
> parece bien y está entero desplazado.

### Dónde fueron los 14 campos del brief

El brief original describía el EDL como **una tabla plana de 14 campos por segmento**. Con
el segundo nivel temporal, esos campos se **reparten** entre los dos niveles, y dos de ellos
desaparecen como campos escritos:

| Campo del brief | Dónde vive ahora |
| --- | --- |
| `startTime` · `endTime` · `spokenText` | **Derivados** de `words` — ya no se escriben |
| `semanticIntent` · `sceneType` · `camera` · `reason` | Segmento |
| `transition` | Segmento, desdoblado en `transitionIn` / `transitionOut` |
| `caption` · `keyword` | Eventos `CAPTION` / `KEYWORD`, por rango de palabras |
| `visualAsset` · `assetStyle` | Evento `OBJECT_IN`, unificados en **`asset`** — una referencia resuelta como `object:clock@1` ya lleva dentro la técnica, así que `assetStyle` sobra |
| `animationPreset` | `defaultPreset` en el segmento, `preset` por evento |
| `soundEffect` | Evento `SFX`, o `sfx: "auto"` en el evento que lo dispara |
| — | **`representationType`** y **`hold`** son nuevos |

### Vida de las instancias — el stage

Un **stage** es una serie maximal de segmentos contiguos cuyo `sceneType` es
`MOTION_STAGE` o `KINETIC_TYPE`. **Lo deriva el compilador**, no se escribe. Un
`instanceId` vive dentro de su stage.

Consecuencia editorial buena: en la pieza 10 el reloj de las 11 **no desaparece** durante
el beat de los pacientes; se queda siendo la presión, y luego le barren las agujas.

### `transitionIn` / `transitionOut` — quién manda en el límite

- Si los dos lados de un límite declaran una transición distinta de `CUT`, **el compilador
  falla** y pregunta cuál manda. No elige en silencio.
- `transitionOut` está **prohibido en el último segmento**: ese frame es el que se congela
  al reiniciar el reel (gotcha #6).
- `OBJECT_MATCH_CUT` tiene condición verificable: **debe existir al menos un `instanceId`
  vivo a ambos lados del límite, y el segmento entrante debe contener un `OBJECT_STATE`
  sobre esa instancia.** Si no, error. Es lo que impide que «match cut» signifique «corte
  normal con nombre bonito».

### Las cinco validaciones que hacen que el contrato sirva

1. **Fingerprint del transcript.** `ls transcripts/` muestra `3.raw.json`,
   `5-remapped.json`, `6-remapped.json`, `7-remapped.json`, `8-remapped.json`:
   re-transcribir tramos es rutina, y **renumera las palabras**, desplazando en silencio
   todas las referencias. Si el fingerprint no cuadra, falla y dice qué segmentos revisar.
2. **Segmentos contiguos:** `segments[i].endTime == segments[i+1].startTime`. Es media
   `check_no_black()` resuelta antes de generar nada.
3. **`keyword` ⊂ `caption` ⊂ `spokenText`**, por rangos de palabras. Un subtítulo no puede
   decir algo que nadie dijo.
4. **`reason` obligatorio y distinto de `semanticIntent`.** Lista negra («para mantener la
   atención», «para dar dinamismo», «para que no sea aburrido») → **warning**. Es el
   principio central hecho ejecutable.
5. **Todo `asset` de evento llega resuelto** (§11). Si no, falla.

### `plan_overrides` — escotilla con whitelist

```jsonc
[ { "target": "visuals[stage-a].cap_top", "value": 1180,
    "why": "el bloque de dos líneas se metía 46 px en la zona de la plataforma" } ]
```

Propiedades permitidas: `cap_top` · `anchor` · `anchorX` · `mock_pad_top` ·
`mock_pad_bottom` · `fade_in` · `fade_out` · `rect` (todas con `target`
`visuals[<id>].<prop>` o `shots[<i>].<prop>`) y `trim` (con `target`
`sfx[<t>].trim`). Cualquier otra → error.
`why` obligatorio. El compilador **imprime la tabla de overrides aplicados**. Existe porque
hay cosas que se descubren midiendo y sin ella acabarías editando el `plan.json` generado;
está acotada para que no degenere en bypass del compilador.

---

### Dos ejemplos completos, con datos reales de la pieza 10

El tercero —el reloj, que demuestra `instanceId`, `OBJECT_STATE` y `OBJECT_MATCH_CUT`— está
en el trazado end-to-end de §15.

#### `A_ROLL` — el hook

Palabras 0–13, **0.18 → 3.67** (línea del corte):
*«La clínica de al lado no es mejor que la tuya, simplemente contestó primero.»*

```jsonc
{ "words": [0, 13],
  "semanticIntent": "no perdiste por calidad, perdiste por velocidad",
  "sceneType": "A_ROLL", "camera": "CLOSE",
  "transitionIn": "CUT",
  "events": [
    { "atWord": 0,  "type": "CAPTION", "words": [0, 4]  },
    { "atWord": 5,  "type": "CAPTION", "words": [5, 10] },
    { "atWord": 11, "type": "CAPTION", "words": [11, 13] },
    { "atWord": 12, "type": "KEYWORD", "words": [12, 13], "preset": "punch" },
    { "atWord": 12, "type": "SFX", "sfx": "impact-bass-1" }
  ],
  "reason": "es la acusación que abre la pieza; su cara sostiene el golpe y un gráfico se lo robaría" }
```

Sin visual y sin `representationType`: la respuesta a la tercera pregunta fue «no existe
representación concreta», y **eso es una respuesta legítima**, no un hueco por rellenar.

#### `MOTION_STAGE` acumulativo — cuatro tareas a la vez

Palabras 57–72, **18.53 → 23.30** (línea del corte). El beat es literal en el guion:
*«Nadie puede atender en el sillón, el teléfono, el cobro y el Instagram al mismo tiempo.»*

```jsonc
{ "words": [57, 72],
  "semanticIntent": "cuatro trabajos incompatibles cayendo sobre la misma persona",
  "sceneType": "MOTION_STAGE", "representationType": "QUANTITY",
  "camera": "OFF", "defaultPreset": "float-in",
  "transitionIn": "DIAGONAL_WIPE",
  "events": [
    { "atWord": 57, "type": "CAPTION",   "words": [57, 59] },

    { "atWord": 62, "type": "OBJECT_IN", "asset": "object:dental-chair@1",
      "instanceId": "task-chair", "slot": "center", "sfx": "auto" },
    { "atWord": 60, "type": "CAPTION",   "words": [60, 64] },

    { "atWord": 64, "type": "OBJECT_IN", "asset": "object:phone@1",
      "instanceId": "task-phone", "slot": "orbit-1" },
    { "atWord": 66, "type": "OBJECT_IN", "asset": "object:card-payment@1",
      "instanceId": "task-pay",   "slot": "orbit-2" },
    { "atWord": 65, "type": "CAPTION",   "words": [65, 69] },
    { "atWord": 69, "type": "OBJECT_IN", "asset": "object:instagram@1",
      "instanceId": "task-ig",    "slot": "orbit-3" },

    { "atWord": 70, "type": "CAPTION",      "words": [70, 72] },
    { "atWord": 71, "type": "KEYWORD",      "words": [71, 72] },
    { "atWord": 71, "type": "OBJECT_STATE", "instanceId": "task-phone",
      "crowd": true, "preset": "crowd-in", "sfx": "auto" },
    { "atWord": 71, "type": "OBJECT_STATE", "instanceId": "task-pay",  "crowd": true },
    { "atWord": 71, "type": "OBJECT_STATE", "instanceId": "task-ig",   "crowd": true }
  ],
  "reason": "los cuatro objetos SE QUEDAN: la escena se llena al ritmo en que él los nombra, y en «al mismo tiempo» se cierran sobre el sillón. La carga no se dice, se ve" }
```

Lo que este ejemplo demuestra:

- **Nada sale de la escena.** Cuatro `OBJECT_IN` a 19.77 · 20.30 · 21.18 · 22.08 — huecos de
  0.53, 0.88 y 0.90 s, muy por debajo del gate macro de 4.5 s.
- **La acumulación es el mensaje.** Los tres `OBJECT_STATE` con `crowd` en «al mismo tiempo»
  son el cierre radial de `overwhelm-surround`: **el sillón no se mueve, el mundo se le echa
  encima.**
- **El SFX es opt-in y se colapsa.** Solo dos eventos declaran `sfx: "auto"`. Si los cuatro
  `OBJECT_IN` lo declararan, la regla de colapso de iguales en 250 ms no los tocaría —están a
  más de 500 ms— y sonarían cuatro `pop` seguidos. Por eso el cierre lleva **un solo**
  `impact-bass-1` y las entradas van casi en silencio.
- **Los assets llegan resueltos** (`object:phone@1`), no como `"phone"`. Ver §11.

---

## 3. Motion Stage y sistema de objetos

### El stage es UN visual, no uno por segmento

Hoy dos takeovers seguidos son dos entradas de `visuals` con su propio `fade_in`/`fade_out`,
y el cruce abre un hueco de 0.15–0.25 s que se lee como un fallo — la razón de existir de
`check_no_black()`.

Con stages, la serie contigua entera es **una sola entrada**: un `fade_in` al principio,
un `fade_out` al final, y todo lo de dentro son anims sobre un fondo que nunca se va.
**La clase entera de bug desaparece**, y es también lo que permite que una instancia
sobreviva varios segmentos.

### Identidad visual — traducida a los tokens existentes

| Brief | Implementación |
| --- | --- |
| dark charcoal + subtle gradient + soft vignette | `vignette()` **ya existe**: radial en 50% 42%, `bg2 → bg → #07080B` |
| top-centered spotlight | `spotlight()` nuevo: radial elíptico en 50% 0%, blanco a **alpha ≤ 0.05** |
| subtle grain | `grain()` nuevo: `feTurbulence` con **`seed` fijo**, filtro **estático**, opacidad baja |
| background graphics (grids, low opacity) | `grid()` **ya existe** a `.022` cada 72 px |
| cinematic depth | Tres planos z (decorativos · objetos · tipografía) con escalas distintas |

El grain con semilla fija es la única forma determinista: `Math.random` sin semilla está
prohibido por el contrato de render, y un grain animado desincronizaría al muestrear frames
en paralelo.

**Techo del spotlight, medido.** Aclara el fondo y se come contraste:

| alpha | `bg` resultante | `violet`/bg | `violet_hi`/bg |
| --- | --- | --- | --- |
| 0.03 | `#121317` | 4.27 ⚠ | 6.36 |
| **0.05** | `#17181C` | 4.08 | **6.08 ✅** |
| 0.07 | `#1C1D21` | 3.87 | 5.77 |

Límite **alpha ≤ 0.05**, y dentro de un stage iluminado el violeta **como texto** tiene que
ser `violet_hi`; `violet` queda para rellenos. `tokens.contrast()` lo verifica en el build.

### Slots — la retícula de acumulación

Las posiciones se **calculan en Python al compilar**, nunca en el navegador (el blueprint
`overwhelm-surround` lo exige y el contrato de determinismo también).

| Slot | Uso |
| --- | --- |
| `center` | El protagonista. Centrado hacia **y 820–880**, no al centro del lienzo |
| `orbit-1…6` | Seis posiciones en elipse alrededor del centro |
| `stack-1…4` | Lista vertical |

`crowd: true` mueve la instancia desde su órbita hacia el centro por un delta también
precalculado.

**La zona segura se aplica también a los objetos.** Hoy solo las captions respetan el 20 %
inferior; un objeto en `orbit-5` puede caer dentro de la interfaz de la plataforma y nada lo
comprueba. El stage valida que ningún slot ocupado baje de `0.80·H` menos la reserva de
subtítulo.

### `objects.py` — y por qué es menos trabajo de lo que parece

El enum `representationType` **dice qué librería lo sirve**, y cinco de los siete ya están
construidos:

| `representationType` | Servido por |
| --- | --- |
| `OBJECT` | **`objects.py` (nuevo)** |
| `STATE_CHANGE` | **`objects.py` con `state` (nuevo)** |
| `QUANTITY` | `objects.py` repetido · o `stat_grid` / `chip_grid` ✅ |
| `RELATION` | `connection_map` ✅ |
| `SEQUENCE` | `flow_steps` ✅ |
| `CONTRAST` | `rate_mismatch` ✅ |
| `INTERFACE` | `screen-tour.py` + `screen_overlay` ✅ |

`objects.py` sigue el patrón de `mockups.py` (devuelve `css, html, anims`) y cada objeto
acepta `state`:

```python
def clock(cid, iid, state, slot):      # state: {"time": "19:00"}
def chat(cid, iid, state, slot):       # state: {"count": 3, "unread": True}
def box_stock(cid, iid, state, slot):  # state: {"qty": 0, "tone": "alert"}
```

Los ángulos de las agujas se calculan **en Python** desde `state.time`; el `hands-sweep` es
un tween de `rotation`, que está en el allowlist. Cero trucos.

**Coste real:** dibujar los objetos es el grueso del trabajo de implementación, más que el
compilador. Se empieza por los **6 que la pieza 10 necesita** —`clock`, `chat`, `phone`,
`card-payment`, `instagram`, `dental-chair`— y la librería **crece por demanda real, no por
catálogo**. Candidatos posteriores: `calendar`, `whatsapp`, `patient-record`, `user`,
`box-stock`, `robot-ai`, `money`, `document-report`, `workflow`.

### 3D real — 2.5D por defecto

El vocabulario base es SVG con profundidad 2.5D (`perspective()` estático + sombra en capas
+ `rotateY` de reposo). El 3D real con Three.js queda reservado a momentos héroe y
**bloqueado tras un spike** (§14).

---

## 4. Biblioteca de presets y transiciones

### El overshoot, sin rebote

Los presets actuales ya hacen overshoot **monótono**: `punch` entra en escala 1.045 y
**baja** a 1.0 con `expo.out`, sin cruzar el objetivo. El `65 → 108 → 100` del brief sí lo
cruza, y ninguna ease sola hace eso sin resorte. Se hace con **dos tweens encadenados**:

```js
// float-in — overshoot con vuelta controlada, sin back.out()
tl.fromTo(sel, { opacity: 0, scale: 0.65, y: 18 },
  { opacity: 1, scale: 1.08, y: 0, duration: 0.26, ease: "power2.out" }, t);
tl.to(sel, { scale: 1.00, duration: 0.09, ease: "power3.inOut",
             overwrite: "auto" }, t + 0.26);
```

350 ms totales, dentro de la banda 250–500 del brief. La diferencia con `back.out` es que
ahí la vuelta la decide la curva y deja una cola elástica; con dos tweens la duración y la
ease del retorno se controlan por separado, así que 90 ms con `power3.inOut` frena en seco y
lee como masa asentándose. `overwrite: "auto"` es obligatorio: dos tweens sobre `scale` del
mismo elemento (gotcha #9).

**El `blur 15px → 0` del brief no entra en las entradas:** `filter` no está en el allowlist
de propiedades animables. Sustituto: el eco fantasma del rule `motion-blur-streak` — 2 capas
duplicadas a opacidad y escala decrecientes que colapsan en la principal. Solo `opacity` y
`scale`, determinista, y lee como velocidad.

| Preset | Equivalente en el brief | Para |
| --- | --- | --- |
| `float-in` | POP_IN / la entrada 65→108→100 | `OBJECT_IN` por defecto |
| `drop-in` | OBJECT_DROP | Objetos con peso |
| `slide-blur` | SLIDE_BLUR | Entrada lateral rápida, con eco |
| `hands-sweep` | — (nuevo, de estado) | `OBJECT_STATE` del reloj |
| `crowd-in` | close-in radial | La acumulación cerrándose |
| `type-beat` | kinetic typography | `KINETIC_TYPE` |
| `punch` · `stamp` · `rise-in` · `chip-in` · `slide-in` · `box-in` · `scale-pop` · `grow-x` | — | **Sin tocar.** Verificados en 4 piezas |

### Las cinco transiciones — todas con propiedades del allowlist

La prohibición es **animar** `filter`, no usarlo: un blur estático es solo rendering.

| Transición | Implementación | Anima |
| --- | --- | --- |
| `CUT` | Nada | — |
| `DIAGONAL_WIPE` | Panel a sangre con `skew` **estático**, cruza el frame | `x` ✅ |
| `BLUR_WIPE` | El mismo panel, con `filter: blur()` **estático** y máscara horneada | `x` ✅ |
| `SCALE_BLUR` | `scale` sobre el plano saliente + 2 capas de eco | `scale`, `opacity` ✅ |
| `OBJECT_MATCH_CUT` | **Ningún efecto**: corte duro y la instancia compartida muta | `rotation` ✅ |

Ninguna necesita hackear el allowlist. Y la transición más potente del brief es la que no
dibuja nada.

---

## 5. Captions y kinetic typography

### Lo que NO se toca

El troceo por jerarquía (frase → cláusula → reparto parejo), la medición de la barbilla, la
piel elegida por solapamiento mayoritario, la altura mandada por el más bajo de todos los
que el bloque toca, la zona segura de la plataforma y el filete de 7 px con
`paint-order: stroke fill`. Verificado sobre MP4 en cuatro piezas.

### Los tres cambios

**1 — Contraste por caja.** Hoy **todas** las palabras van en mayúsculas. Pasan a **caja de
frase**, y la mayúscula queda solo para la keyword. Es un diferenciador más fuerte que el
tamaño, no cuesta nada en layout, y ataca lo que la doctrina ya quiere evitar: la mayúscula
continua convierte la banda de subtítulo en un metrónomo. **Es el cambio más visible del
rediseño: verificar con `snapshot` antes de comprometerlo.**

**2 — La keyword crece a 1.22×**, no al 1.30 del brief: a 66 px de base, 1.30 son 86 px y el
presupuesto de zona segura de un bloque de dos líneas se queda sin margen.

Esto obliga a dos correcciones, ambas encapsuladas en **`scripts/caption_metrics.py`**:

```python
def measure_block(words, base_size, keyword_range, fmt) -> dict:
    """→ {n_lines, max_size, line_h, floor_top, width}"""
```

- `floor_top` usa hoy `CAPTION_SIZE` para todas las líneas:
  `floor_top = 0.80·H − n_lines · round(CAPTION_SIZE · 1.14)`.
  Con una keyword a 1.22× la caja de línea crece y un bloque de dos líneas **se mete en la
  interfaz de la plataforma** — el bug de los 46 px ya documentado. Tiene que usar el
  tamaño **máximo** del bloque.
- La medida de ancho que decide `n_lines` tiene que pesar los caracteres de la keyword a su
  tamaño real, o un bloque medido como una línea se renderiza como dos.

`build-composition.py` pasa de calcular a **preguntar**. Beneficio secundario: es la primera
pieza del pipeline **testeable unitariamente** — hoy la zona segura solo se verifica
renderizando y midiendo el MP4, el ciclo más caro que existe.

**3 — La marca de la keyword.** Hoy es una pastilla violeta detrás de la palabra. Pasa a
**texto en `violet_hi`** + mayúscula + ExtraBold + 1.22×. Medido: **6.70:1 sobre `bg`,
6.07:1 sobre `surface`**. Para keywords que además funden, `violet_lt` da 8.64:1.
(`violet` a secas sobre `surface` da 4.08 — no llega para texto normal.)

### `KINETIC_TYPE` — escala dedicada

Mapear `small→hero` a `body 34 / display 132` daría 3.9×, que **no** es la jerarquía de
150–250 % del brief. Escala propia, anclada a `display`, que ya está verificada:

| Nivel | Factor | REEL | YOUTUBE |
| --- | --- | --- | --- |
| `small` | 1.00 | 60 px | 51 px |
| `medium` | 1.55 | 93 px | 79 px |
| `hero` | 2.20 | **132 px** = `TYPE.display` | **112 px** = `TYPE.display` |
| `mega` | 2.80 | 168 px | 143 px |

`hero` cae exactamente en el `display` de cada formato: la escala nueva no inventa tamaños,
extiende la que ya existe. `mega` **avisa si aparece más de una vez por pieza** — si todo es
excepción, no hay jerarquía.

**`CAPTION` está prohibido dentro de un segmento `KINETIC_TYPE`.** Si la tipografía es el
gráfico, un subtítulo debajo diciendo lo mismo es la definición de decorar. En
`MOTION_STAGE` las captions siguen permitidas con piel `on-surface`, como hoy.

---

## 6. Cámaras virtuales y punch cuts

### Los dos mecanismos son distintos de verdad

| | `HARD_CROP_CUT` | `PUNCH_ZOOM` |
| --- | --- | --- |
| Qué es | Cambio instantáneo de encuadre | Zoom animado breve |
| Implementación | **Pendiente de spike** (§14) | Tween de `scale` sobre el vídeo activo |
| Uso | **El 85 %+ de los cambios de cámara** | ≤2 por pieza |

Hoy `shot_rect()` no anima nada: devuelve una **caja CSS estática** con `left`/`top`
negativos y `width`/`height` sobredimensionados, y el stage recorta por overflow. El corte
duro es un elemento nuevo **por construcción**, no porque un transform no funcione — nadie
lo ha probado. Ver el spike A en §14.

### La escalera, adaptativa por resolución

El factor de reescalado al alza es `zoom · W_canvas / W_fuente`, así que:

```
close_max = (W_fuente / W_canvas) · max_upscale          # max_upscale = 1.20
```

| Fuente | `close_max` | Comentario |
| --- | --- | --- |
| 1080 vertical | **1.20** | El perfil aprobado. `WIDE` 1.00 · `MEDIUM` 1.12 · `CLOSE` 1.20 |
| 4K vertical (2160) | **2.40** | A `z = 2.00` el reescalado es **1.00×: sigue en nativo** |

El `1.25` del brief queda descartado **para fuente 1080**: por encima de ~1.2 el reescalado
de H.264 a 1080 de ancho ablanda la piel de forma visible, y es probablemente la razón por
la que la bitácora marca el 1.15 actual como «escaso». La solución para crops más agresivos
no es software, es **grabar en 4K**. El profile pide la escalera que quiera; el compilador la
recorta por la fórmula y **avisa** si tuvo que recortar.

### Anclaje al sujeto

`assets/face-<n>.json` hoy trae solo `chin_px` y `chin_frac`. `measure-face.py` gana
`cx_frac` / `cy_frac` sobre las mismas 48 muestras Haar que ya corre, horneadas una vez por
take. El crop ocurre alrededor de la cara, no del centro geométrico.

En `shot_rect()` es una generalización de una línea y **retrocompatible bit a bit**: hoy
`left = -(w - W) / 2`, que es exactamente `anchorX = 0.5`; pasa a `left = -(w - W) * anchorX`
y un JSON sin `cx_frac` da el comportamiento actual idéntico.

### Reglas de asignación y ritmo

| Momento | Cámara |
| --- | --- |
| Hook, afirmación fuerte, pregunta, remate | `CLOSE` |
| Se abre una explicación nueva | `WIDE` |
| Cuerpo por defecto | `MEDIUM` |
| `MOTION_STAGE` / `KINETIC_TYPE` | `OFF` |

- **`camera_min_gap = 0.70 s`**, con exención en el hook (`hook_exempt_until = 3.0`). Es lo
  que separa el jump cut multicámara del jitter.
- **Al volver de un stage, la cámara debería ser distinta** de la que había antes de entrar:
  si vuelve la misma, el espectador ve el plano *reanudarse* y lee un fallo de edición.
  **Warning, no obligación** — si narrativamente conviene volver al mismo plano, se puede.

---

## 7. Color semántico

Los cinco colores del brief **ya existen** en `tokens.py`. Lo que faltaba no era la paleta,
era sistematizarla.

| Brief | Token | Medido |
| --- | --- | --- |
| PRIMARY / TECHNOLOGY | `violet` (fills) · `violet_hi` (texto) | 6.07:1 sobre `surface` |
| NEGATIVE / PROBLEM | `alert` `#FF5A5A` | 5.79:1 sobre `surface` |
| WARNING | `warn` `#FFB84D` | 10.31:1 sobre `surface` |
| SUCCESS | `go` `#34E39B` | 10.64:1 sobre `surface` |
| NEUTRAL | `text` blanco | 17.7:1+ |

### Los temas del stage

`THEME_CHANGE` gobierna **stage, fills, objetos, glow y fondos**.

| `theme` | Acento | Suelo | Cuándo |
| --- | --- | --- | --- |
| `primary` | violet | `vignette()` normal | Por defecto |
| `problem` | alert | `vignette()` + glow rojo bajo | La escena negativa del brief |
| `warning` | warn | normal | Atención |
| `success` | go | normal | Resuelto |
| `neutral` | blanco | normal | El dato puro |

### Cuatro guardarraíles

1. **La capa de subtítulos es independiente del tema.** En A-roll la identidad de caption y
   keyword es estable; solo se mueve con un override explícito `keywordTheme` en el evento
   `KEYWORD`. Si el tema pudiera tintar el subtítulo entero, todo el trabajo de legibilidad
   habría que re-litigarlo cinco veces.
2. **El tema cambia en límites estructurales, nunca por frase.** Si el color siguiera el
   sentimiento oración a oración, una pieza con arco problema → solución parpadearía
   rojo–violeta–verde y se vería como un semáforo. `THEME_CHANGE` va donde cambia el
   **bloque**; **warning por encima de 2 por pieza**.
3. **El glow del tema `problem` tiene techo medido**, igual que el spotlight: se mide con
   `tokens.contrast()` en el build, no se ajusta a ojo.
4. **Sobre relleno ámbar va tinta `bg`, nunca blanco.** Medido: `warn/bg` = 11.37:1 pero
   **`text/warn` = 1.72:1** — blanco sobre ámbar es ilegible. El ámbar es color de *texto y
   trazo* sobre oscuro, no de fondo con texto encima. Misma regla que ya está escrita para
   el verde (`bg/go` = 11.74:1).

---

## 8. Sound design

La jerarquía no se negocia: **voz** pista 10 · **música** pista 11 · **efectos** pista 12+.
`voice_gain = 0.70`, y el generador desplaza los mismos dB a efectos y música para que
bajar la voz no cambie el balance. La cabecera de mezcla se conserva: el metraje de iPhone
llega pegado al techo (7690 muestras a 0 dB antes de tocarlo) y esa es la razón del 0.70.

### Qué gana el sonido con el EDL

Con `atWord`, un SFX cae en el `start` exacto de su palabra en vez de en un float copiado a
mano, y **se mueve solo** cuando `refine-timings.py` corrige un borde. El brief pide que
*«los tiempos sean los mismos beats del transcript que mueven la imagen»*; con `atWord` no
es una intención, es la misma fuente de datos.

### El SFX es opt-in

Cada preset tiene un efecto por defecto, pero **solo suena si el evento declara
`sfx: "auto"`**. Esto convierte *«do not add SFX to every animation»* en el comportamiento
por defecto en vez de en disciplina: el silencio no hay que recordarlo.

| Preset | SFX por defecto |
| --- | --- |
| `float-in` | `pop` |
| `drop-in` | `impact-bass-2` |
| `slide-blur` | `whoosh-short` |
| `hands-sweep` | `whoosh-short` |
| `crowd-in` | `impact-bass-1` |
| `type-beat` | `key-press` · `click-soft` |
| `punch` | `impact-bass-1` |
| `box-in` | `click` |

### Concurrencia y prioridad

1. **Iguales dentro de 250 ms** → colapsan en uno. El caso es real: cuatro `OBJECT_IN` con
   `pop` en 2.3 s son cuatro pops seguidos. Colapsados, la acumulación suena a una cosa que
   crece, no a una ametralladora. Por eso `crowd-in` lleva **un solo** `impact-bass-1` en el
   cierre radial, no uno por objeto.
2. **Distintos dentro de `sfx_concurrency_window` (180 ms)** → gana el de clase más alta,
   los demás se descartan y el informe dice cuáles.

| Clase | Efectos |
| --- | --- |
| 1 — impacto | `impact-bass-1` · `impact-bass-2` · `error` |
| 2 — movimiento | `whoosh` · `whoosh-short` · `whoosh-cinematic` · `riser` |
| 3 — interfaz | `click` · `click-soft` · `key-press` · `pop` · `typing` |
| 4 — adorno | `chime` · `sparkle` · `ping` · `notification` |

### El `trim`: qué significa el tercer elemento de un SFX en `plan.json`

Verificado en `build_sfx()`:

```python
v = min(10 ** ((SFX_TARGET_MEAN - mean) / 20),
        10 ** ((SFX_PEAK_CAP  - peak) / 20), 1.0)
data_volume = round(max(0.02, v * trim), 3)
```

- El nivel absoluto se **mide y se calcula** por archivo. Hay **27 dB** entre el efecto más
  caliente (`impact-bass-1`, media −5.0 dB) y el más flojo (`chime`, −32.4 dB); un número
  escrito a mano tapa la voz con unos y hace inaudibles otros.
- El tercer elemento de la tupla es **`trim`: un multiplicador relativo aplicado DESPUÉS de
  la ganancia calculada.** Por defecto **`1.0`** = «acepto el nivel calculado». El `0.85` de
  la pieza 4 significa «este efecto un 15 % por debajo de su nivel calculado».
- El `1.0` de dentro del `min(...)` es otra cosa: un **techo de unidad** para no amplificar
  nunca por encima del archivo original.
- Suelo `0.02`: un `trim` no puede silenciar del todo un efecto.
- La **duración** sale de `ffprobe` sobre el archivo, no del plan. Los efectos que se solapan
  reciben pistas separadas automáticamente. Un archivo ausente **avisa y se omite**, nunca
  bloquea el render.

> **Regla:** el EDL **nunca** fija dB absolutos. Un evento puede llevar `trim` opcional
> (relativo, por defecto 1.0) con su razón; todo lo demás se calcula.

---

## 9. `edl-compile.py`

### La frontera: quién decide qué

| Decisión | Dueño |
| --- | --- |
| Qué significa la frase | **EDL** — `semanticIntent` |
| Si merece visual, y de qué tipo | **EDL** — `sceneType`, `representationType` |
| Qué objeto, y **en qué palabra** entra | **EDL** — `OBJECT_IN`, `atWord` |
| Qué estado tiene el objeto | **EDL** — `state` |
| Qué palabra se resalta | **EDL** — `KEYWORD` |
| Qué cámara y en qué límite | **EDL** — `camera`, `transitionIn` |
| Con qué recurso concreto se hace | **Asset Resolver** (§11) |
| Cómo se ve un `float-in` por dentro | **Preset** — código |
| Qué SFX trae un preset | **Preset** — tabla |
| Px de `hero`, escalera de zoom, umbrales de gates | **Style profile** — datos |
| Coordenadas exactas de un slot | Compilador — aritmética |
| Tiempo absoluto de un `atWord` | Compilador — lookup + `q()` |
| Agrupar segmentos contiguos en stages | Compilador — derivación |
| Retardos de `off` para no abrir negro | Compilador — aritmética del gotcha #6 |
| Altura, piel y nº de líneas de cada caption | Compilador — `caption_metrics` |
| Ángulos de las agujas desde `state.time` | Compilador — trigonometría |
| Volumen de cada SFX | Compilador — la fórmula existente |
| **Qué objeto representa mejor una idea** | **Nunca el compilador** |
| **Cuándo entra algo** | **Nunca el compilador** |
| **Si un segmento merece visual** | **Nunca el compilador** |
| **Qué recurso usar si el asset no llega resuelto** | **Nunca el compilador — falla** |

> **Regla para los casos dudosos:** si una decisión podría razonablemente ser distinta en
> manos de otro editor, **no es del compilador**. El compilador solo hace aritmética,
> lookup, derivación y aplicación de fórmulas. No elige nunca.

### Las ocho fases

```
1  cargar EDL + transcript, verificar fingerprint      → falla si el transcript cambió
2  resolver words → tiempos, y atWord → instantes, vía q()
3  derivar stages (series contiguas MOTION_STAGE|KINETIC_TYPE)
4  validar CORE                                        → falla estructural
5  calcular métricas y correr los gates del profile    → fail / warn según datos
6  emitir shots · cards · visuals · sfx
7  aplicar plan_overrides (whitelist) e imprimir la tabla
8  escribir plan.json + informe
```

La fase 6 es la que menos parece y más importa: el stage entero sale como **una sola entrada
de `visuals`** con `kind: "mockup"` y `mock: ["motion_stage", {…}]`. En
`build-composition.py` eso es **una línea** en el dict de despacho:
`"motion_stage": objects.motion_stage`. Las otras ~1290 líneas ven un plan que ya conocen.

---

## 10. Integración con el pipeline

| # | Paso | Estado |
| --- | --- | --- |
| 0–2b | detect-format · ffmpeg · transcribe · **refine-timings** | ✅ **sin tocar** |
| 3–4 | plan-cuts · rough-cut | ✅ sin tocar |
| 5 | measure-face | ⚙ **+ `cx_frac` / `cy_frac`** |
| 6 | color HLG | ✅ sin tocar |
| 7 | screen-tour | ✅ sin tocar — sirve `INTERFACE` |
| 8 | make-music-bed | ✅ sin tocar |
| **8b** | **Creative Planner → `edl.draft.json`** | 🆕 §11 |
| **8c** | **Asset Resolver → assets resueltos y versionados** | 🆕 §11 |
| **8d** | **Validación CORE → `edl.json`** (contrato congelado) | 🆕 §11 |
| **9** | **`videos/<n>/edl.json`** | 🆕 el contrato congelado |
| **9b** | **`edl-compile.py` → `plan.json`** | 🆕 |
| 10 | build-composition | ⚙ **3 cambios quirúrgicos** |
| 11–12 | `hyperframes check` · `render --sdr` | ✅ sin tocar |

Los tres cambios en `build-composition.py`, y nada más:

1. Una línea en el despacho de mockups: `"motion_stage"`.
2. `left = -(w - W) * anchorX` en `shot_rect()` — retrocompatible bit a bit.
3. Métricas de caption delegadas a `caption_metrics.py`.

**Intactos:** capas, apilado de 8 niveles, `check_no_black()`, contrastes WCAG, la fórmula
de volumen, la cabecera de mezcla, la zona segura de captions. Y las piezas 1–9 siguen
compilando desde su `plan.json`: el camino viejo no se retira.

### Estructura de archivos nueva

```
.claude/skills/video-tech-premium/
├── references/
│   ├── motion.md          ← Motion Stage, gramática de movimiento, presets  (reescrito)
│   ├── plan-schema.md     ← contrato del EDL                                (reescrito)
│   ├── visuals.md         ← vocabulario visual, objetos, acumulación        (reescrito)
│   ├── planner.md          ← Creative Planner + Asset Resolver              🆕
│   └── design · color · sound · gotchas                                     (sin cambios)
├── scripts/
│   ├── edl-compile.py      ← EDL → plan.json                                🆕
│   ├── objects.py          ← librería de objetos con estado                 🆕
│   ├── caption_metrics.py  ← métricas de caption encapsuladas               🆕
│   ├── asset-resolve.py    ← Asset Resolver                                 🆕
│   ├── build-composition.py ← 3 cambios quirúrgicos                         ⚙
│   ├── measure-face.py     ← + cx_frac / cy_frac                            ⚙
│   └── (el resto)                                                           sin cambios
└── styles/
    └── motion-explainer.json  ← escalas, umbrales, severidades              🆕
```

---

## 11. Creative Planner + Asset Resolver

El producto final **no debe requerir escribir a mano el EDL de cada reel**. Esta sección
separa las cinco responsabilidades y fija dónde empieza el determinismo.

### El flujo completo

```
video → transcript → [Creative Planner]  → videos/<n>/edl.draft.json
                   → [Asset Resolver]    → (assets resueltos)
                   → [CORE validation]   → videos/<n>/edl.json      ← contrato congelado
                   → [edl-compile.py]    → videos/<n>/plan.json
                   → [build-composition] → public/index.html
                   → [hyperframes render]→ output.mp4
```

### Dos archivos, no uno: `edl.draft.json` vs `edl.json`

La distinción no es organizativa, es la frontera de determinismo hecha archivo.

| | `edl.draft.json` | `edl.json` |
| --- | --- | --- |
| Lo produce | Creative Planner (o un humano) | Asset Resolver + validación CORE |
| Assets | **Pueden ser semánticos o pendientes** (`"clock"`, `"?calendar"`) | **Solo referencias resueltas y versionadas** |
| Estado | Candidato, editable, se puede regenerar | **Contrato congelado** |
| ¿Lo acepta `edl-compile.py`? | **No** | **Sí, y solo este** |
| Determinista | ❌ | ✅ desde aquí en adelante |

`edl-compile.py` recibe **únicamente** `edl.json`. Si se le pasa un draft, o un `edl.json`
con un `asset` sin resolver, **falla**. No busca, no diseña, no elige un sustituto parecido,
no improvisa.

El draft se versiona en git igual que el EDL final: es el registro de qué propuso el Planner
frente a qué se aprobó, y es lo que permite mejorar el Planner comparando ambos.

| Capa | Decide | Determinista |
| --- | --- | --- |
| **Creative Planner** (LLM) | **QUÉ** editar | ❌ — y está bien |
| **Asset Resolver** | **CON QUÉ** recurso | ⚠ cachea, así que es reproducible tras la primera resolución |
| **`edl.json`** | **el contrato congelado** | **— es el límite** |
| **`edl-compile.py`** | **CÓMO** se vuelve valores | ✅ |
| **build-composition + renderer** | ejecuta | ✅ |

> **La frontera de determinismo.** Todo lo anterior a `edl.json` puede variar entre corridas;
> todo lo posterior, no.
>
> **Mismo `edl.json` + mismo transcript + mismos assets resueltos + mismo style profile
> = mismo `plan.json`, byte a byte.**

### Creative Planner

**Entrada:** transcript remapeado (con `wordId`), style profile, y opcionalmente `guion.md`
y notas de la pieza.
**Salida:** un **EDL draft** — los mismos campos que el EDL final, salvo que el `asset` de
cada evento es **semántico** (`"calendar"`, `"clock"`) y todavía no una referencia
resuelta.

Genera: `semanticIntent` · `sceneType` · `representationType` · `camera` · `events` (con
`atWord`) · `keyword` · `asset` semántico · `state` · `preset` solicitado ·
`transitionIn`/`transitionOut` · `sfx: "auto"` opt-in · `reason`.

Restricciones que debe respetar:

- **No inventa palabras.** Solo referencia `wordId` del transcript.
- **No fija tiempos.** Solo `atWord` + `offset`.
- **No fija dB, ni px, ni coordenadas.**
- **Rellena `reason` con una razón real.** La lista negra le aplica igual.

> **El Planner no es una autoridad, es un candidato.** El EDL draft pasa por exactamente el
> mismo CORE gate que un EDL escrito a mano. Eso es lo que hace seguro que sea no
> determinista. Y su salida es un archivo editable: el Planner **acelera, no sustituye**.

### Asset Resolver

Convierte el `asset` semántico de cada evento en una **referencia concreta y cacheada**.
**Prioridad estricta — reutilizar antes que generar:**

| # | Fuente | Ejemplo de salida |
| --- | --- | --- |
| 1 | **Asset Library existente** (`objects.py`, `mockups.py`) | `object:clock@1` |
| 2 | **Asset configurable / 2.5D** (mismo objeto, variante o `state`) | `object:clock@1?face=roman` |
| 3 | **UI o grabación real** (`screen-tour.py`) | `recording:screen-tour-2#seg1` |
| 4 | **Asset generado** (Higgsfield / Kie, con ledger) | `gen:calendar-premium-01` |
| 5 | **B-roll** — buscado, licenciado o generado | `broll:clinic-reception-03` |

Reglas:

- Solo se **baja de nivel** cuando el de arriba no puede servir la petición, y se anota por
  qué en el propio EDL: `resolvedVia` + `resolveReason`.
- Todo lo generado entra en el **ledger que ya existe** (`assets/gen/ledger.json`), así que
  el pipeline se re-corre entero sin volver a pagar.
- La salida es una **referencia estable y versionada**, no un archivo temporal.

### Referencias de asset: estables, versionadas e inmutables

```
object:clock@1          object:chat@2          recording:crm-demo@1
gen:calendar-premium@1  broll:clinic-reception@3
```

> **La regla que hace que el versionado sirva de algo: `@1` es INMUTABLE.**
>
> Rediseñar el reloj **no** edita `object:clock@1`: crea `object:clock@2`. Si `@1` se
> pudiera editar en sitio, el sufijo no protegería nada — y el problema real es que
> **cambiar un asset en silencio modificaría renders históricos**. Una pieza publicada hace
> tres meses tiene que poder re-renderizarse idéntica.

### `assets/manifest.json` y el informe de compilación

Cada referencia resuelta vive en un manifest con su hash:

```jsonc
{
  "manifest_version": "2026-09-07.3",
  "assets": {
    "object:clock@1":     { "hash": "sha256:1a9f…", "kind": "object",    "added": "2026-09-07" },
    "object:chat@2":      { "hash": "sha256:c40b…", "kind": "object",    "added": "2026-09-07" },
    "recording:crm-demo@1": { "hash": "sha256:77e2…", "kind": "recording", "added": "2026-08-30" }
  }
}
```

El **informe de compilación registra el `manifest_version` y el hash de cada asset
realmente usado**. Así una pieza histórica es reproducible por referencia: el informe dice
con qué versión exacta de qué objeto se renderizó, y el hash detecta si alguien editó un
`@n` que debía ser inmutable.

El hash del manifest **no** entra en el hash creativo del EDL: son dos preguntas distintas
—«¿es la misma decisión creativa?» y «¿son los mismos píxeles?»— y mezclarlas haría que
añadir un objeto nuevo a la librería invalidara el hash creativo de todas las piezas.
- **El B-roll deja de estar limitado a metraje propio.** Sigue siendo el último recurso,
  pero puede ser licenciado, buscado o generado cuando el Planner lo justifique en su
  `reason`.

### El compilador falla si llega un asset sin resolver

Regla dura, en CORE: **todo `asset` de evento tiene que llegar resuelto.** Si `edl-compile.py`
recibe `"calendar"` a secas, **falla**. No busca, no diseña, no elige un sustituto parecido,
no improvisa. Es la frontera de §9 aplicada a los assets: *el compilador no elige nunca*.

### Metadata de trazabilidad — no entra en compilación

```jsonc
"planner": {
  "plannerVersion": "0.3.1",
  "styleProfile":   "motion-explainer",
  "promptVersion":  "2026-09-07-a",
  "generatedAt":    "2026-09-07T14:22:03Z"    // ← excluido del hash creativo
}
```

Ninguno de estos campos entra en el `plan.json` ni afecta a una sola decisión de
compilación. `generatedAt` está **explícitamente excluido del hash creativo**: si entrara,
dos corridas del mismo EDL darían hashes distintos y la prueba de determinismo sería
inútil.

**Hash creativo:** `sha256` del EDL canonicalizado (claves ordenadas, separadores fijos)
**sin** `planner.generatedAt` y **sin** las claves que empiezan por `_`. Identifica «esta
decisión creativa» y es lo que compara el golden test.

---

## 12. Gates consolidados

### CORE — dentro del compilador, como código

El EDL está mal; no es cuestión de gusto.

- Fingerprint del transcript no cuadra
- Rangos de palabras inválidos o fuera de orden
- Segmentos no contiguos (hueco o solape)
- `keyword` ⊄ `caption`, o `caption` ⊄ `spokenText`
- `OBJECT_IN` duplicado sobre una instancia viva del mismo stage
- `OBJECT_MATCH_CUT` sin instancia compartida a ambos lados, o sin `OBJECT_STATE`
- Transiciones en conflicto en un mismo límite
- `transitionOut` en el último segmento
- `plan_overrides` fuera de whitelist, o sin `why`
- `reason` ausente
- `CAPTION` dentro de un segmento `KINETIC_TYPE`
- Slot de objeto por debajo de la zona segura
- **`asset` de evento sin resolver**, o referencia de asset sin versión (`object:clock` en
  vez de `object:clock@1`)
- Se le pasa un `edl.draft.json` en vez de un `edl.json`
- Un asset usado no existe en `assets/manifest.json`, o su hash no cuadra

### STYLE_PROFILE — fuera del compilador, como datos

`styles/motion-explainer.json`:

```jsonc
{
  "camera":  { "ladder": {"WIDE":1.00,"MEDIUM":1.12,"CLOSE":1.20},
               "max_upscale": 1.20, "min_gap": 0.70, "hook_exempt_until": 3.0 },
  "kinetic": { "small":1.00, "medium":1.55, "hero":2.20, "mega":2.80 },
  "caption": { "keyword_scale": 1.22 },
  "stage":   { "spotlight_alpha": 0.05 },
  "sfx":     { "collapse_same": 0.25, "concurrency_window": 0.18 },
  "gates": [
    { "metric": "presenter_share",          "in": [0.45,0.60],
      "warn_in": [0.35,0.70], "fail_in": [0.20,0.85] },
    { "metric": "max_micro_gap",            "max": 2.5,  "severity": "fail" },
    { "metric": "max_macro_gap",            "max": 4.5,  "severity": "fail" },
    { "metric": "punch_zoom_count",         "max": 2,    "severity": "warn" },
    { "metric": "theme_change_count",       "max": 2,    "severity": "warn" },
    { "metric": "mega_count",               "max": 1,    "severity": "warn" },
    { "metric": "special_transition_ratio", "max": 0.20, "severity": "warn" },
    { "metric": "sfx_per_macro",            "max": 0.50, "severity": "warn" },
    { "metric": "decorative_reason_count",  "max": 0,    "severity": "warn" }
  ]
}
```

> **La clave arquitectónica:** el compilador calcula **métricas** (lista fija y cerrada, en
> código); el profile decide **umbrales y severidad** (datos). Un `styles/clean.json` mañana
> es un archivo nuevo y **cero líneas** de compilador.

Los gates de ritmo admiten la excepción autorizada `"hold": true` con su `reason`.

---

## 13. Determinismo y pruebas

`edl-compile.py` es una **función pura** de cinco entradas: `edl.json` ·
`transcripts/<n>.json` · `styles/<perfil>.json` · `objects.py` · `tokens.py`.

| Riesgo | Cómo se cierra |
| --- | --- |
| Reloj de pared / aleatoriedad | Prohibidos. Ni `time`, ni `random`, ni red |
| `planner.generatedAt` | Excluido del hash creativo y de toda salida |
| Orden de claves en el JSON | `json.dump(..., sort_keys=True)`, separadores fijos |
| Coma flotante en los tiempos | **Un solo punto de cuantización**: el `q()` existente, `round(round(t·30)/30, 4)`. Los empates IEEE754 se resuelven igual en cada corrida porque hay una sola llamada |
| Coordenadas de slots | `cos`/`sin` de una tabla fija de ángulos, redondeadas a entero |
| Orden de eventos con el mismo `atWord` | Orden estable por `(atWord, índice en el archivo)` |

### La prueba

```bash
edl-compile.py --piece 10 -o /tmp/a.json && edl-compile.py --piece 10 -o /tmp/b.json
cmp /tmp/a.json /tmp/b.json                  # byte-idénticos
cmp /tmp/a.report.txt /tmp/b.report.txt
```

Más un **golden file** versionado, `tests/golden/10.plan.json`, comparado byte a byte en
cada cambio. Efecto secundario que vale por sí solo: si mañana se mueve un slot en
`objects.py` o un token en `tokens.py`, el golden **se rompe y obliga a mirar** en vez de
descubrirlo tres piezas después.

Y `caption_metrics.py` es la primera pieza con **test unitario real**: entradas conocidas →
`floor_top` esperado, sin renderizar nada.

---

## 14. Spikes bloqueantes

**Los dos spikes NO bloquean lo mismo, y ninguno está en el camino crítico de la pieza 10.**

| | Spike A — cámaras | Spike B — Three.js |
| --- | --- | --- |
| Bloquea | La **implementación definitiva** de las cámaras virtuales | **Solo habilitar 3D real** |
| ¿Bloquea la pieza 10? | **No.** Se construye sobre la arquitectura actual (un `<video>` por encuadre), que ya funciona en 4 piezas publicadas | **No.** El 2.5D es la estrategia principal, no un plan B |
| Si falla | Se adopta el fallback de 3 capas persistentes, o se mantiene el statu quo | El 3D real no entra nunca y el 2.5D cubre todo el vocabulario |
| Camino crítico | Optimización de arquitectura, posterior a la vertical slice | **Tarea independiente**, fuera del camino crítico |

Dicho de otro modo: si el Spike B nunca se ejecuta, **no pasa nada**. El vocabulario de
objetos es 2.5D por diseño (§3), y el 3D real siempre fue un extra para momentos héroe.

### Spike A — `HARD_CROP_CUT` sin un `<video>` por encuadre

**Hipótesis:** un solo `<video>` dentro de un wrapper, y en cada corte un
`tl.set({scale, x, y})` de duración cero sobre el **wrapper**.

| # | Qué se prueba | Por qué es la incógnita |
| --- | --- | --- |
| a | Que la inyección de frames sobreviva a un ancestro transformado | El productor inyecta por `getElementById` en el `<video>`; un transform arriba *no debería* importar, pero no está documentado |
| b | Que el `set` vaya al **wrapper**, nunca al `<video>` | El contrato permite `tl.set` de duración cero solo en no-clips o wrappers dentro de un clip |
| c | Nitidez a `CLOSE`, comparando snapshots | Hoy el remuestreo ocurre en layout; con transform, en el compositor. Si sale más blando, pierde |

**Resultados por preferencia:** (1) un vídeo + sets en el wrapper — un decoder para toda la
pieza · (2) tres capas persistentes WIDE/MEDIUM/CLOSE, cada una en su wrapper, con el corte
como set de opacidad — tres decoders, frente a los **15–16 elementos por pieza** de hoy ·
(3) statu quo.

### Spike B — Three.js determinista

Renderizar 90 frames de un objeto rotando a 1080×1920 y comprobar:

1. El mismo frame pedido dos veces sale **byte-idéntico**.
2. `data-duration` manual se respeta (el adapter `three` no infiere duración).
3. WebGL no revienta con la memoria justa que `CLAUDE.md` ya marca en aviso.

Si falla cualquiera de las tres, el 3D real no entra y el 2.5D cubre todo el vocabulario.

---

## 15. Trazado end-to-end — el reloj de la pieza 10

Material real: `transcripts/10-rough.json`, 130 palabras, **línea del corte**. El reel trata
sobre clínicas que pierden pacientes por contestar tarde.

**1 · palabras del transcript** — `transcripts/10-rough.json`, índices 31–37
`Contestaste(31) a(32) las(33) 7(34) de(35) la(36) tarde.(37)` · **9.39 → 11.21**

**2 · `semanticIntent`** → *«pasaron ocho horas»*

**3 · representación** → `STATE_CHANGE`. **No** es `OBJECT`: el reloj ya existe desde la
palabra 18. Esa distinción es la que produce el match cut en vez de un gráfico nuevo.

**4 · segmento** → `words: [31, 37]` · `MOTION_STAGE` · `camera: OFF` ·
`transitionIn: OBJECT_MATCH_CUT`

**5 · eventos** → `CAPTION`[31,33] · `CAPTION`[34,37] · `KEYWORD`[34,34] ·
`OBJECT_STATE` en `atWord: 34` · `SFX` en `atWord: 34`

**6 · objeto y estado** → `clock-main`: `{"time":"11:00"}` → `{"time":"19:00"}`.
El compilador convierte a ángulos, **siempre hacia delante**:

| Aguja | Desde | Hasta | Recorrido |
| --- | --- | --- | --- |
| Horaria | 330° | 570° | **+240°** |
| Minutera | 0° | 2880° | **+2880°** (8 vueltas) |

Que el sentido sea obligatoriamente horario no es un detalle: `330° → 210°` es el camino
corto, son **−120°**, y el reloj **iría hacia atrás**. Ocho horas perdidas se leerían como
ocho horas recuperadas.

**7 · preset `hands-sweep`** → dos tweens de `rotation`, `power2.inOut`, 0.42 s. Ocho
vueltas de minutera en 0.42 s se difuminan solas: el motion blur no hay que fingirlo.

**8 · `edl.json`**

```jsonc
{ "words": [31, 37], "semanticIntent": "pasaron ocho horas",
  "sceneType": "MOTION_STAGE", "representationType": "STATE_CHANGE",
  "camera": "OFF", "transitionIn": "OBJECT_MATCH_CUT",
  "events": [
    { "atWord": 31, "type": "CAPTION", "words": [31, 33] },
    { "atWord": 34, "type": "CAPTION", "words": [34, 37] },
    { "atWord": 34, "type": "KEYWORD", "words": [34, 34] },
    { "atWord": 34, "type": "OBJECT_STATE", "instanceId": "clock-main",
      "state": { "time": "19:00" }, "preset": "hands-sweep", "sfx": "auto" }
  ],
  "reason": "es EL MISMO reloj con las agujas barridas: las ocho horas se ven en vez de calcularse" }
```

**9 · `edl-compile.py`** → `atWord 34` → `words[34].start = 10.28` →
`q(10.28) = round(round(10.28·30)/30, 4) = 308/30 =` **`10.2667`**.
Deriva el stage: los tres segmentos contiguos `MOTION_STAGE` —`[14,21]` «te
escribieron a las 11 de la mañana», `[22,30]` «estabas con un paciente adelante y con
otro después» y `[31,37]`— forman **un solo stage**, palabras 14–37 →
`q(4.10) = 4.1` a `q(11.21) = 11.2`. Las palabras 38–56 rompen la contigüidad,
así que el beat de acumulación (57–72) es **otro** stage.
Valida el match cut: `clock-main` vive a ambos lados ✅ y el segmento entrante lo muta ✅.

**10 · `plan.json`** (generado, no editado)

```jsonc
"visuals": [{ "id": "stage-a", "role": "takeover", "kind": "mockup",
  "start": 4.1, "end": 11.2, "skin": "on-surface",
  "fade_in": 0.22, "fade_out": 0.18, "hud": ["EL PROBLEMA", "01"],
  "mock": ["motion_stage", { "theme": "problem",
    "objects": [{ "id": "clock-main", "kind": "clock", "slot": "center",
                  "state": {"time":"11:00"}, "in": 5.0 }],
    "at": [{ "t": 10.2667, "op": "state", "id": "clock-main",
             "hour": 570, "minute": 2880, "preset": "hands-sweep" }] }] }],
"shots": [{ "at": 4.3333, "kind": "off" }, … ],
"sfx":   [[10.2667, "whoosh-short", 1.0, "las agujas barren ocho horas"]]
```

El `off` en **4.3333** y no en 4.1 es la aritmética del gotcha #6: el encuadre se queda
hasta `start + fade_in` para que el cruce no caiga al suelo. Y el `1.0` del SFX es el
**`trim` por defecto** (§8): «acepto el nivel calculado».

**11 · `build-composition.py`** → DOM + timeline GSAP + `caption_metrics` colocando los dos
bloques.

**12 · `render --sdr`** → MP4, y verificación **sobre el archivo**: `blackdetect`, tinta más
baja, pico de audio y ataque de efectos.

---

## 16. Qué NO se toca y qué queda fuera

### Intacto

Transcripción AssemblyAI y `refine-timings.py` · `plan-cuts.py` · `rough-cut.sh` ·
calibración HLG y el LUT · `screen-tour.py` con sus `exclude` y su `cropdetect` ·
`make-music-bed.py` · el apilado de 8 capas · `check_no_black()` · los checks WCAG · la
fórmula de volumen de SFX · la cabecera de mezcla y `voice_gain` · el troceo de captions por
jerarquía · la medición de la barbilla · la zona segura de la plataforma · los 8 presets de
animación verificados · el sistema de color de `tokens.py`.

### Fuera de alcance

- **Re-renderizar las piezas 1–9.** Congeladas. El lenguaje nuevo empieza en la 10.
- **Cambiar el sistema visual** a charcoal-azul + cyan + Poppins. El brief se traduce a los
  tokens existentes.
- **`back.out()` y cualquier muelle** en una entrada.
- **Animar `filter` o `clip-path`.** Fuera del allowlist; las cinco transiciones se
  implementan sin ellos.
- **Estilizar el metraje.** El color reproduce el original.

---

## Estado de las decisiones

| Sección | Estado |
| --- | --- |
| 0 Herramienta y alcance | ✅ aprobado |
| 1 Gramática editorial | ✅ congelado |
| 2 Contrato del EDL | ✅ congelado |
| 3 Motion Stage y objetos | ✅ congelado |
| 4 Presets y transiciones | ✅ congelado |
| 5 Captions y kinetic type | ✅ congelado |
| 6 Cámaras | ✅ congelado (arquitectura pendiente del spike A) |
| 7 Color semántico | ✅ congelado |
| 8 Sound design | ✅ congelado |
| 9 `edl-compile.py` | ✅ congelado |
| 10 Integración | ✅ congelado |
| 11 Planner + Asset Resolver | ✅ congelado |
| 12 Gates consolidados | ✅ congelado |
| 13 Determinismo y pruebas | ✅ congelado |
| 14 Spikes | ✅ congelado — ninguno en el camino crítico de la pieza 10 |
| 15 Trazado end-to-end | ✅ congelado |
| 16 Fuera de alcance | ✅ congelado |

**Siguiente paso tras la aprobación:** plan de implementación (skill `writing-plans`) y
construcción de la pieza 10 end-to-end.

---

## Regla de implementación

> **Primero hacer que una pieza real funcione de punta a punta; después generalizar.**

El plan prioriza una **vertical slice de la pieza 10 end-to-end** antes de construir
capacidades completas. Consecuencias concretas:

- La librería de objetos empieza con los **6 que la pieza 10 usa**, no con las 15
  candidatas.
- `edl-compile.py` empieza **mínimo**: lo que la pieza 10 necesita para compilar, no las
  ocho fases completas.
- El Asset Resolver y el Planner llegan **al final**, cuando ya hay un EDL real y compilado
  contra el que validarlos.
- El Spike B (Three.js) es una **tarea independiente**, fuera del camino crítico.
