# Layout `triband` — diseño

**Fecha:** 2026-09-14 · **Estado:** **propuesto** — pendiente de revisión
**Ámbito:** evolución en sitio de la skill `video-tech-premium`
**Empieza a aplicarse en:** pieza **15** (`VIDEOS ORIGINALES/1`). Las piezas 1–14 quedan
**congeladas** y deben recompilar bit a bit igual.

> ## Principio central
>
> **El triband no es un layout más: es una promesa de simultaneidad.**
>
> Tres cosas a la vez —la demostración, la frase y quien la dice— en vez de tres cosas por
> turnos. Todo lo que sigue existe para que esa simultaneidad no cueste legibilidad.

---

## 0. Qué se decidió, y qué se descartó

| Decisión | Elegido | Descartado |
| --- | --- | --- |
| Alcance | **Modo nuevo por pieza** (`layout` en el EDL) | Reemplazar el estilo entero · hornearlo a mano en el `plan.json` |
| Proporciones | **Equilibrado** — 43 / 16 / 42 % | Animación protagonista (50/14/36) · Hablante protagonista (36/15/49) |
| Logos | **Oficiales + gate de resolución** | Híbrido · wordmarks tipográficos de la casa |
| Hook y tesis | **Se abren a plano lleno** | Triband permanente · abrir solo en el hook |
| Manus (grabación clara) | **Se deja clara, a propósito**, con marco más marcado | Regrabarla en oscuro · buscarle un tramo oscuro |

### Por qué un modo y no un reemplazo

Las piezas 10, 12, 13 y 14 tienen golden del `plan.json` compilado en `tests/golden/`. Un
reemplazo del layout por defecto los rompe todos a la vez y deja de haber forma barata de
saber si la rotura es intencional o un efecto colateral. Con un modo, la ausencia de
`layout` en el EDL **es** la prueba de regresión: si el golden sigue verde, el camino viejo
no se movió.

De esos cuatro, solo el de la pieza 10 puede ejecutarse hoy — ver la corrección en §7.

---

## 1. Geometría

Lienzo REEL 1080 × 1920.

```
banda      rect                       contenido
──────────────────────────────────────────────────────────────────────
top        0 ‥ 820     1080×820      card flotante 960×540 (16:9),
                                     centrada en y410, radio lg 24
text       820 ‥ 1120  1080×300      subtítulo, tope fijo y844
speaker    1120 ‥ 1920 1080×800      pantalla.MOV, object-fit cover
```

Las bandas **no van a hueso**: entre ellas queda suelo grafito visible. Es lo que hace que
la card de arriba flote en vez de parecer un recorte pegado, y es la misma razón por la que
la elevación del sistema son hairline + sombra ancha y no un borde duro.

### La banda del hablante

Fuente 1080×1920 en ventana 1080×800 con `object-fit: cover` → escala 1.0, visible el
**42 % vertical** del cuadro: plano de pecho para arriba.

El `anchor` **no se estima**: sale de `measure-face.py` sobre el rough, como en toda pieza,
y se ajusta para que la barbilla caiga hacia **y1350** — 186 px por encima de y1536.

El metraje llega al borde inferior del lienzo. La interfaz de la plataforma se superpone
sobre el pecho, que es donde no cuesta información. La regla del 20 % prohíbe poner
*información* ahí, no metraje: en `full` el metraje ya llega al borde hoy.

---

## 2. El contrato en el EDL

### `camera: "BAND"`

`CAMERAS` pasa de `{WIDE, MEDIUM, CLOSE, OFF}` a `{WIDE, MEDIUM, CLOSE, BAND, OFF}`.

Hoy `edl_compile.emit()` mapea cámara → `kind: "full"` con zoom de la escalera, o
`kind: "off"`. `BAND` añade una tercera salida: `kind: "band"`, **sin zoom** — el encuadre
de la banda ya es un recorte fuerte y una escalera encima lo haría irreconocible.

### El bloque `layout`

Se declara **una sola vez** en la cabecera del EDL:

```json
"layout": {
  "mode": "triband",
  "bands": {
    "top":     [0,    820],
    "text":    [820,  1120],
    "speaker": [1120, 1920]
  }
}
```

Un EDL sin `layout` compila por el camino de siempre. Un EDL con `layout` pero sin ningún
segmento `BAND` es un error de validación, no un silencio: declarar geometría que nadie usa
casi siempre significa que alguien olvidó marcar los segmentos.

### Por qué la geometría es global y la activación por segmento

Repetir los rects en cada segmento invita a que dos contiguos declaren bandas distintas, y
eso salta en el frame sin que nada lo impida. Con geometría global, el único grado de
libertad por segmento es *estoy o no estoy en triband*, que es exactamente la decisión
editorial que se quiere tomar.

El corte entre un segmento `CLOSE` y uno `BAND` es un **corte duro**, igual que entre dos
encuadres: cada uno es un `<video>` nuevo, no un tween de geometría. Eso ya es doctrina del
proyecto (trampa 2 del renderer) y aquí sale gratis.

---

## 3. La banda de arriba

### Dos estados por herramienta

**Estado 1 — card de logo**, clavada a la palabra que nombra la herramienta.

```
        ╭──────────────────────────────╮
        │                              │
        │   ◀── ▣    anime.js          │   ▣ logo:   x −72 → 0, power2.out, 0.45 s
        │           ANIMACIONES  ▼     │   ▼ nombre: y −22 → 0, power3.out, +0.08 s
        │                              │
        ╰──────────────────────────────╯
             ↑ la card entra por OPACIDAD (0.35 s), no se mueve
```

El contenedor entra fundiendo y lo que viaja es su contenido. Es doctrina de §6 y no se
negocia: mover el contenedor entero es lo que hace que una pieza parezca una plantilla. La
petición de «entra de derecha a izquierda» y «el nombre de arriba hacia abajo» se cumple
**dentro** de la card, que es donde se lee.

Los dos recorridos son deliberadamente distintos —uno horizontal, otro vertical— para que
el ojo lea dos elementos y no un bloque. Ninguno usa `back.out()`.

**Estado 2 — card de grabación**, cuando empieza a explicarla. **Corte duro**, no
transición: la grabación es un `<video>` nuevo.

El logo **no desaparece**: queda como chip en la cabecera de la card. Es lo que mantiene
atada la grabación a su nombre durante los 6–8 s que dura — el mismo mecanismo que la marca
en la cabecera de `chat_unanswered`.

**Nada entra antes de su palabra.** Ninguna card de logo aparece antes de que se pronuncie
el nombre de su herramienta.

### El zoom es obligatorio, no opcional

1280×720 dentro de una card de 960×540 sale a **0.75×**: la interfaz se vería más pequeña
que en el monitor original. Es la trampa ya documentada de la pieza 2 (recorte 1350×854 a
0.73×).

Recorte objetivo **~720×405 → 1.33×**, encuadrando por tramo el punto del que se habla.
`screen-tour.py` produce hoy salida cuadrada (1.2195) para uso a lienzo completo; aquí la
card es 16:9 y la salida del recorrido debe serlo también.

### El aspecto 3D

`perspective()` + `rotateY()` **estáticos** en un wrapper hijo; GSAP toca solo
`opacity`/`scale`/`x`/`y` del div exterior. Es como está construida la librería de objetos,
y es lo que impide que el render se descuadre. Más hairline claro y sombra ancha, que sobre
fondo oscuro son quienes dan la elevación.

### Estado verificado de las cinco grabaciones

Medido con `cropdetect=limit=0.06` sobre 4 s de cada una: **sin barras negras**, contenido
en el cuadro completo (`crop=1280:720:0:0` en las cinco). Ninguna lleva chrome de navegador.

| Grabación | Dur. | Hallazgo | Tratamiento |
| --- | --- | --- | --- |
| `animejs.mov` | 16.9 s | limpia | recorte + zoom |
| `motiondev.mov` | 9.8 s | limpia | recorte + zoom |
| `kokonutui.mov` | 7.5 s | **barra promocional rosa** en el borde superior | se recorta fuera |
| `bklitui.mov` | 10.5 s | **URL en el tooltip de estado**, abajo a la izquierda | se recorta fuera |
| `manusia.mov` | 12.1 s | **fondo claro**, única de las cinco | se deja, con marco más marcado |

Las dos primeras filas de hallazgo son la misma clase de problema que el indicador de dev y
el toast de error de la pieza 3: cosas que delatan la grabación y que no se ven en el frame
que uno mira al elegir el recorte. Se declaran en `exclude` con su ventana y su rect, y
`screen-tour.py` falla antes de renderizar si un tramo las pisa.

**Manus clara es una decisión, no un descuido.** Es la quinta y última herramienta, y la
única que no es una librería de componentes. El salto de luminancia cae donde el guion ya
cambia de registro. Se le da marco más marcado para que el borde de la card no se pierda
contra el frame oscuro.

### Los logos

Ninguna de las cinco está en Simple Icons (`animejs`, `anime`, `motion`, `manus`,
`kokonut`, `bklit` → todos 404 en v16). `framer` sí existe, pero Motion ya no es Framer
Motion: sería la marca equivocada.

| Marca | Fuente verificada | Formato |
| --- | --- | --- |
| Motion | `motion.dev/favicon.svg` | **SVG** — fondo `#0B0B0C`, casi el suelo del sistema |
| Manus | `manus.im/icon.svg` | **SVG** — tile blanco con marca oscura |
| Bklit UI | `bklit.com/apple-icon.png` | PNG 1024 |
| Kokonut UI | `kokonutui.com/icon.png` | PNG 253 |
| Anime.js | og-image 1200×600 (el favicon es 64×64, **insuficiente**) | PNG, a extraer |

`fetch-logos.py` se extiende para vendorizar marcas que no son de Simple Icons, registrando
en `meta.json` la URL, la fecha de descarga y el formato. **Gate de resolución:** una marca
raster debe tener al menos 2× el alto al que se pinta en la card, o la vendorización falla.
Es lo que evita que el favicon de 64 px de Anime.js entre estirado sin que nadie lo note.

Si Anime.js no supera el gate desde ninguna fuente, **se para y se pregunta** — no se
sustituye por una marca inventada, igual que `fetch-logos.py` hoy sale con error ante un
slug no verificado.

---

## 4. La banda de texto

### El subtítulo deja de perseguir la barbilla

Hoy la altura la decide `chin_at()` proyectando la medición de cara al encuadre activo, y
`floor_top` de `caption_metrics.py:72` existe para no invadir el 20 % de la plataforma.

En triband **no hay metraje entre y820 y y1120**: solo suelo grafito. El subtítulo no puede
tapar la cara porque la cara está 300 px más abajo. Toda esa maquinaria queda en silencio —
no se borra, deja de aplicar en este modo.

```
y820  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  techo de banda
y844  ┌─────────────────────────┐  ← tope FIJO
      │ LA PRIMERA ES ▁ANIME.JS▁│     línea 1   ┐
      │ UNA LIBRERÍA DE          │    línea 2   ┘ 2 × 92 = 184 px
y1028 ┆ · · · · · · · · · · · · ┆  ← tinta más baja con 2 líneas
y1104 └─────────────────────────┘  ← suelo del gate (76 px de holgura)
y1120 ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  empieza el hablante
```

Tres reglas:

1. **Tope fijo, no centrado.** Un bloque de una línea y otro de dos empiezan en la misma y,
   o el ojo ve el texto saltar entre bloques. Crecen hacia abajo.
2. **Piel `on-surface`, sin filete.** El filete de grafito de 7 px existe para sobrevivir
   sobre metraje. Sobre suelo limpio sobra, y quitarlo afina la letra.
3. **Máximo dos líneas.** Subtítulo base 66 px; con keyword, `66 × 1.22 = 81` y caja de
   línea `81 × 1.14 = 92`. Dos líneas son 184 px → la tinta acaba en **y1028**, con 76 px
   de holgura sobre el suelo. Tres líneas son 276 px → **y1120 exactos**, o sea encima de
   la banda del hablante: el gate las rechaza. Con 907 px útiles caben ~22 caracteres por
   línea y un bloque de 3–6 palabras casi nunca pide una tercera. El troceo por jerarquía
   (frase → cláusula → reparto) no cambia.

El resaltado sigue siendo **una sola keyword por bloque**.

### El gate cambia de sitio, no desaparece

Donde en `full` hay una comprobación de «no invadir el 20 % inferior», en triband va una de
**«no invadir la banda del hablante»**: tinta más baja ≤ y1104.

Se calcula con la misma mecánica que ya existe —repartir palabras en líneas como lo hace el
navegador, medir cada una a SU tamaño, usar el tamaño de la keyword para la caja de línea—
porque los dos bugs que esa mecánica cazó (la tercera línea de la pieza 11 a 58 px dentro de
la interfaz, la segunda línea de un bloque sobre gráfico a 46 px) ocurrirían igual aquí con
otro suelo.

Un bloque que se pase **falla la compilación**. No se descubre mirando el MP4.

---

## 5. Estructura de la pieza 15

Fuente: `VIDEOS ORIGINALES/1/pantalla.MOV` — 1080×1920, HEVC, 78.94 s, 30 fps.

### Por qué slot 15 y no slot 1

`transcripts/1.json` y `cuts/1.json` son de la pieza 1 **vieja**, que `CLAUDE.md` §13 marca
como la referencia viva de la calibración HLG. Escribir en el slot 1 la destruiría.

Esto no es nuevo: §13 ya avisa de que **la numeración de las carpetas no es la de las
piezas**. Queda anotado que `VIDEOS ORIGINALES/1` → pieza **15**.

### Mapa editorial

| Tramo | Guion | Layout | Banda de arriba |
| --- | --- | --- | --- |
| Hook | «guárdate estas cinco herramientas…» | **full** | — |
| 1 | Anime.js — animaciones | **band** | logo → `animejs.mov` |
| 2 | Motion — transiciones y scroll | **band** | logo → `motiondev.mov` |
| 3 | Kokonut UI — componentes visuales | **band** | logo → `kokonutui.mov` |
| 4 | Bklit UI — gráficos y datos | **band** | logo → `bklitui.mov` |
| 5 | Manus — de idea a prototipo | **band** | logo → `manusia.mov` |
| Tesis | «no es conocer más herramientas… es darle mejores ingredientes» | **full** | — |
| CTA | «comenta WEBS» | **band** | `comment_ui` |

El guion dice «Coconut UI»; el producto se llama **Kokonut UI** y así se rotula. El
subtítulo transcribe lo que se dice; el rótulo nombra lo que es.

Los tiempos salen del transcript remapeado, no de esta tabla.

---

## 6. Plan de trabajo

| # | Paso | Produce |
| --- | --- | --- |
| 0 | `detect-format.sh` sobre `pantalla.MOV` | confirma REEL — se mide, no se supone |
| 1–3 | audio → AssemblyAI → `refine-timings.py` | `transcripts/15.json` cuadrado |
| 4 | `plan-cuts.py --audio` + `audit-breaths.py` | `cuts/15.json`, cero respiraciones |
| 5 | `measure-face.py` sobre el rough | `assets/face-15.json` |
| 6 | Vendorizar 5 logos + gate de resolución | `assets/logos/` + `meta.json` |
| 7 | **Código nuevo** (§2, §3, §4) | scripts + tests |
| 8 | 5 recorridos a ~720×405, 16:9 | `videos/15/screen-tour-*.json` |
| 9 | `edl.json` → compilar → renderizar `--sdr` | `videos/15/output.mp4` |
| 10 | Verificar **sobre el MP4** | frames extraídos + audio medido |

El paso 7 es el único que toca el sistema. Todo lo demás es el flujo de siempre.

---

## 7. Verificación

**Tests que acompañan al paso 7:**

- Geometría de las tres bandas en `test_shot_geometry.py` — rects exactos, y que `BAND` no
  aplique zoom.
- El gate del suelo de la banda de texto — un bloque de dos líneas que se pasa **debe**
  fallar la compilación.
- `layout` declarado sin ningún segmento `BAND` → error de validación.
- **El golden de la pieza 10 intacto.** Es la prueba de que el camino viejo no se movió.

⚠ **Corrección sobre lo que esta spec decía al escribirse.** Prometía los cuatro golden
(10, 12, 13 y 14). Al medir la suite resultó que **solo la pieza 10 es utilizable**: los
`videos/12|13|14/edl.json` se borraron sin haber llegado nunca a un commit, y no están en
HEAD, ni en el stash, ni en ningún commit colgante. Sus golden (`tests/golden/*.plan.json`)
sobreviven, pero sin entrada no hay nada que compilar.

La pieza 10 cubre cámaras, captions, keywords, MOTION_STAGE, instancias y SFX — o sea,
todo lo que este cambio toca. Lo que queda **sin cobertura** son las **tarjetas**: la pieza
10 no usa ninguna (`test_cards_sigue_vacio_la_pieza_10_no_usa_tarjetas`). Ningún paso de
este diseño toca `build_cards`, así que el riesgo es bajo, pero queda dicho en vez de
supuesto.

Los tests de las piezas 12–14 se saltan con razón explícita —el mismo trato que `audio14`
con su FLAC gitignoreado— para que un fallo NUEVO se vea en vez de perderse entre 8 errores
de partida.

**Verificación sobre el MP4** (no sobre la fecha del archivo):

- Sin negro real (`blackdetect pix_th=0.03`).
- Tinta más baja del subtítulo ≤ y1104 en los tramos `band`; ≤ zona segura en los `full`.
- La barbilla por encima de y1536 en los tramos `band`.
- Contraste WCAG AA en cada par nuevo que introduzcan las cards de logo.
- Audio: pico, muestras saturadas, ganancia de voz recuperada frente a la declarada.

---

## 8. Riesgos conocidos

| Riesgo | Mitigación |
| --- | --- |
| Anime.js sin fuente de logo que pase el gate | Se para y se pregunta. No se inventa marca. |
| El recorte 1.33× deja texto de UI ilegible en alguna grabación | Se mide sobre el frame renderizado al tamaño del panel, no se estima. |
| La card clara de Manus rompe el frame más de lo previsto | Decisión tomada a sabiendas; reversible cambiando un recorte. |
| Dos líneas no bastan para algún bloque | El troceo genera un bloque más. El gate lo fuerza. |
| `screen-tour.py` asume salida cuadrada | El paso 8 lo parametriza a 16:9; es cambio de parámetro, no de mecánica. |
