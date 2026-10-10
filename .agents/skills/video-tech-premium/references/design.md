# Sistema visual — las dos paletas de la marca

Estilo: **contenido educativo premium de tecnología, IA y negocios**. Superficies flotando
sobre un suelo liso con hairline y sombra suave, tipografía grotesca pesada y un único
momento de acento terracota por frame. **Dos paletas, la misma marca**: `claro` (suelo
crema, tinta casi negra) y `oscuro` (suelo casi negro cálido, texto crema).

La fuente de verdad es `scripts/tokens.py`. Un cambio ahí se propaga a toda la pieza.

---

## Color

Los valores BASE se copian del dashboard del proyecto
(`Marketing/dashboard/web/src/app/theme.css`) y no se inventan en `tokens.py`: así el video
y el dashboard son la misma marca. Todo lo demás se **deriva con una regla** y se **mide**
en `tests/test_paletas.py`.

### La paleta se declara por pieza

`"palette": "claro" | "oscuro"` es **obligatorio** en la raíz de `plan.json` y de
`edl.json` (y `edl-plan.py --palette`). `build-composition.py` falla si falta y, si está,
llama a `tokens.use(palette)` antes de emitir nada. Si la pieza viene de un brief de
`plan-edicion`, se usa la que trae.

⚠ No confundir con `theme`: ese es el **tema semántico** (`primary` · `problem` ·
`warning` · `success` · `neutral`) que cambia `THEME_CHANGE` dentro de un stage. El tema
cambia acento, relleno y glow; nunca el color del texto.

### Las bases

| token | `claro` | `oscuro` | uso |
| --- | --- | --- | --- |
| `bg` | `#ECE7DE` | `#161412` | suelo |
| `surface` | `#F7F4EE` | `#201D1A` | tarjeta / panel |
| `surface2` | `#E4DED2` | `#2B2723` | elevado (fila activa, celda destacada) |
| `text` | `#1C1A16` | `#EEE8DF` | tinta principal |
| `text2` | `#6F695F` | `#A39C91` | secundario |
| `line` | `#D8D1C4` | `#36312B` | hairline |
| `accent` | `#C45F38` | `#E27B52` | PRIMARIO: fills, barras, pastillas |
| `accent_soft` | `#F1DDD2` | `#3A2419` | fondo suave de acento |
| `on_accent` | `#FFFFFF` | `#1A0F0A` | texto sobre `accent`, solo grande y en negrita |
| `go` | `#3F7D4E` | `#7CC08C` | resuelto · conectado · CTA |
| `warn` | `#A66A12` | `#E0A64A` | aviso |
| `alert` | `#B23A2E` | `#EC7B6E` | problema · desconectado |

### Los derivados — reglas, no valores

| token | regla (`tokens._derive`) |
| --- | --- |
| `bg2` | `bg`→`surface` al 50 %: centro del viñeteado |
| `bg_edge` | `bg` hacia negro, 30 % (`oscuro`) / 6 % (`claro`): borde del viñeteado |
| `surface3` | `surface2`→`text` al 6 %: bordes internos de UI, tracks de barra |
| `text3` | el paso más tenue de `text2` hacia `surface` que aún da ≥4.5:1 |
| `accent_hi` | acento hacia `text` hasta ≥4.5:1 contra el suelo iluminado por el foco (`lift(bg, SPOTLIGHT_MAX)`): **el acento como TEXTO** |
| `accent_lt` | acento hacia `text` hasta ≥7:1: texto de acento que va a FUNDIR |
| `accent_pill` | acento hacia el suelo hasta que `text` encima dé ≥4.5:1: pastilla del karaoke, rótulos, fondos con texto encima |
| `LINE_HI` | `line`→`text` al 15 %: el hairline que tiene que separar más |
| `INK_ON_FILL` | la tinta (`bg` o `text`) que más contrasta con `go`/`warn` |

**Si un par no llega a su mínimo, se arregla la regla en `tokens.py`, nunca el
componente.**

### Cómo se usa

- `tokens.use(nombre)` muta en su lugar `C`, `FILL`, `THEME` e `INK_ON_FILL` y reasigna los
  escalares `LINE`, `LINE_HI`, `SHADOW`, `SHADOW_LIFT`, `GLOW`. Los escalares se leen como
  `TK.LINE` (`import tokens as TK`), **nunca** con `from tokens import LINE`: quedarían
  congelados en la paleta de arranque.
- Helpers: `accent_a(a)`, `ink_a(a)` (hairlines, rejilla), `shade_a(a)` (velos, halos de
  texto), `mix(a, b, t)`, `rgba(hex, a)`.
- **Ningún componente escribe un color a mano.** Lo vigila
  `tests/test_paletas_consumidores.py`.
- `logos.brand_tone()` mueve el color de marca hacia el `text` de la paleta hasta 3:1
  contra `surface`: aclara en `oscuro`, oscurece en `claro`.
- `scripts/palette-sheet.py` genera una hoja HTML estática de los mockups en las dos
  paletas: se revisa a ojo cada vez que se toca `tokens.py`.

**Nada de negro puro ni blanco puro como fondo.** Un suelo casi negro deja respirar los
oscuros del metraje en vez de aplastarlos; un crema no quema como un blanco.

**Regla de escasez:** un solo momento de acento de alto voltaje por frame. Si el subtítulo
lleva su pastilla de acento, el titular de la tarjeta no la lleva.

### Contraste

Mínimos: **texto chico 4.5:1**; **texto grande (≥24 px en negrita), chips y logos 3:1**.
Los fija `tests/test_paletas.py` en las dos paletas, en vez de una tabla de números que
envejece con la primera paleta nueva. De ahí salen tres reglas de uso:

- El acento como texto es **`accent_hi`**, nunca `accent` a secas.
- Sobre un relleno de señal (`go`, `warn`) va **`INK_ON_FILL`**, no un blanco por costumbre.
- `on_accent` sobre `accent` solo en texto grande y en negrita; para texto chico, `text`
  sobre `accent_pill`.

`tokens.contrast(a, b)` mide cualquier par nuevo antes de renderizar, que es cuando cuesta
barato.

---

## Tipografía

**Dos familias.** Una tercera es lo que hace que una pieza parezca un collage.

| Rol | Familia | Notas |
| --- | --- | --- |
| Todo el texto | **Inter** 400–900 | 900 para titulares y subtítulos |
| Etiquetas de UI, datos, chips | **JetBrains Mono** 400/700 | uppercase, tracking amplio |

Cuanto más grande el texto, **más se cierra el tracking**. Es lo que hace que un titular
pesado se lea como un producto y no como un cartel.

| Rol | REEL px | YOUTUBE px | tracking |
| --- | --- | --- | --- |
| chip | 26 | 22 | `.16em` |
| label | 24 | 20 | `.12em` |
| body | 34 | 29 | `0` |
| card-title | 52 | 44 | `-.02em` |
| headline | 96 | 80 | `-.032em` |
| display | 132 | 112 | `-.038em` |
| hero-num | 200 | 168 | `-.04em` |
| caption | 66 | 54 | `-.02em` |

Las 8 woff2 están vendorizadas y verificadas en `assets/fonts/` (glifos del español
comprobados con fontTools). Se regeneran con `scripts/fetch-fonts.py`.

⚠ **Trampa de Google Fonts:** el CSS devuelve varios `@font-face` por familia y el
**primero es el cirílico** — quedarse con el primer `src` baja un subset sin una sola
tilde. Hay que elegir el bloque cuyo `unicode-range` contenga `U+0000-00FF`.
`fetch-fonts.py` ya lo hace y lo verifica.

---

## Superficie y elevación

- Fondo: `vignette()` — radial de `bg2` a `bg` a `bg_edge`. Empuja la mirada al centro;
  sin él un 1080×1920 de color plano se ve muerto.
- `grid()` — rejilla técnica a `ink_a(.022)` cada 72 px. Casi invisible; le da al fondo
  textura de plano en vez de degradado de plantilla.
- **Hairline** (`TK.LINE`, o `TK.LINE_HI` cuando tiene que separar más) como único borde.
- Sombra (`TK.SHADOW`): en `claro` la del dashboard, `0 1px 2px rgba(28,26,22,.06),
  0 8px 24px rgba(28,26,22,.08)`; en `oscuro`, `0 2px 6px rgba(0,0,0,.45),
  0 18px 50px rgba(0,0,0,.55)` — sobre suelo oscuro una sombra negra apenas se ve, así que
  la elevación la dan la sombra *y* el hairline. Nunca dura.
- **Glow de acento escaso** (`TK.GLOW`): solo el objeto protagonista del frame.
- Radios: `sm 10 · md 16 · lg 24 · xl 32 · pill 9999`.

---

## Layout

### Encuadres del metraje (`shots`)

| kind | Geometría |
| --- | --- |
| `full` | caja sobredimensionada con desborde negativo; el stage recorta |
| `split` | 9:16 → gráfico arriba, sujeto abajo desde el 40 % · 16:9 → gira a vertical |
| `pip` | ventana **arriba a la derecha**, por encima del takeover |
| `off` | lo tapa un visual; no se emite elemento |

El PiP va arriba a la derecha **por eliminación**: la banda de abajo es del subtítulo —que
no se mueve de ahí— y el centro es del gráfico.

### Zona segura

En REEL, **el 20 % inferior queda libre**: ahí pinta la plataforma su propia interfaz
(usuario, descripción, botones). El espacio vacío bajo el subtítulo no es un descuido,
es la zona segura.

### Mockups

Se diseñan sobre 1080×1920 con un ancho de trabajo de **980 px**. Se centran con **flex**,
nunca con `transform: translate(-50%,-50%)`: en cuanto GSAP les mete un `y` o un `scale`,
toma el control del transform y descarta el centrado.

`mock_pad_top` empuja el mockup hacia abajo para que no se pise con el PiP.

---

## Subtítulos

Bloques de 3–6 palabras, Inter 900 en mayúsculas, centrados.

| Piel | Cuándo | Tratamiento |
| --- | --- | --- |
| `on-dark` | sobre el metraje (`full`/`pip`) | filete del color del suelo (`bg`) de 7 px con `paint-order: stroke fill` + sombra — letra crema con filete oscuro en `oscuro`, al revés en `claro` |
| `on-surface` | sobre un gráfico, o sobre suelo liso en `triband` | sin filete, solo sombra |

`paint-order: stroke fill` pinta el trazo **detrás** del relleno: la letra no engorda y la
grotesca conserva su peso. Con un borde normal Inter 900 se convierte en una mancha.

### El karaoke — tratamiento único del subtítulo

Todas las palabras de un bloque van al **mismo tamaño y color**. Lo que se mueve es un
fondo de acento con esquinas redondeadas que aparece DETRÁS de la palabra en el instante
exacto en que se pronuncia (su `start` en el transcript remapeado) y se apaga en cuanto
arranca la siguiente: el resaltado VIAJA, nunca hay dos fondos encendidos a la vez, y al
terminar el bloque no queda nada pintado. Ya no existe la keyword agrandada 1.22× y sola
que resaltaba una sola palabra mientras las demás quedaban quietas — competía por la
atención con el fondo que viaja, y se quitó.

- **El fondo usa `accent_pill`, no `accent`.** El acento a su valor de marca no garantiza
  4.5:1 con texto chico encima; `accent_pill` es el acento empujado hacia el suelo justo
  hasta que `text` encima pasa 4.5:1, en las dos paletas (fijado en
  `tests/test_paletas.py`).
- **El fundido de cada palabra se ESCALA a su propia ventana**, no a un valor fijo: con
  habla rápida una palabra puede durar menos que un fundido fijo, y `hyperframes check` lo
  caza como `overlapping_gsap_tweens` (`references/gotchas.md`).
- La keyword sigue existiendo como concepto — se declara en `plan.json` o se detecta sola
  en una cifra — pero ya no cambia el RENDERIZADO: solo hace el cálculo de zona segura más
  conservador, midiéndola como si fuera 1.22× más grande aunque no se pinte así.

### El anclaje en `triband`

En `full`/`pip` el subtítulo persigue la barbilla proyectada (`measure-face.py` sobre el
encuadre activo), porque el metraje está detrás y puede taparla.

En `triband` no: entre el techo y el suelo de la banda de texto **no hay metraje**, así
que no hay barbilla que esquivar. El bloque se ancla por el **suelo** de su banda (el techo
de la banda `speaker` menos un margen) y crece hacia ARRIBA según cuántas líneas tenga, no
al revés. Anclado por arriba, un bloque corto dejaba ~200 px de hueco muerto justo encima
de la cara del presentador: el ojo usa de referencia la separación con la cara, no el
techo de la banda de texto. El gate falla si el bloque crece tanto que su techo invade la
banda de la animación de arriba — la geometría completa está en `references/triband.md`.

Sin metraje detrás de la letra, la piel es `on-surface` sin filete — el filete existe para
que la letra sobreviva encima de imagen, y ahí no la hay.
