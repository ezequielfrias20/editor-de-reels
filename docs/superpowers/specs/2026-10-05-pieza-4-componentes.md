# Pieza 4 — componentes nuevos (Instagram, monigotes, Claude)

Pieza: «No tengo diseñador ni editor y publico 30 reels al mes». Paleta `oscuro`,
layout `formatos`. La propuesta está en `videos/4/propuesta.json` y las respuestas
(todas por defecto) en `VIDEOS ORIGINALES/4/respuestas.json`.

Instagram es el escenario de toda la pieza. **La miniatura de reel es el objeto que
cruza el video y cambia de estado**: nace en la grilla de un perfil, se guarda, suelta
su problema (el nudo), pasa por Claude, vuelve con la cara de Ezequiel, se multiplica
por 25 y al final una sola se despega y se vuelve viral. Por eso los componentes
comparten primitivas (la miniatura, el avatar, los glifos de IG, el monigote) y la
MISMA geometría entre variantes: es lo que hace que se lea «la misma cosa» y no
dieciséis gráficos.

## Dónde vive

- Módulo nuevo `.claude/skills/video-tech-premium/scripts/mockups_reels.py`
  (`scripts/` es un enlace a esa carpeta). Importa de `mockups` lo que reutilice
  (`text_px`, `_cursor`, `_cursor_css`, `BOARD_W`) y de `tokens`/`logos`/`icons`
  como hace `mockups.py`.
- `build-composition.py`: `import mockups_reels` y una entrada por componente en el
  diccionario de despacho de `build_visuals` (junto a `"inspector_archivo"`).
- Todos los tiempos van en **`at: list`**, que el compilador ya remapea a offsets del
  visual (`absolute_times`). Ningún componente nuevo usa otra clave de tiempo: así no
  hay que tocar la lista de remapeo.
- `count-roll` gana un sufijo opcional (ver `ig_busqueda`).
- Dos gestos nuevos en `emit_anim` (`build-composition.py`), con test en
  `tests/test_motion_gestos.py`:
  - `flip-out`: `tl.to(sel, {scaleX: 0, duration: d, ease: "power2.in", overwrite: "auto"}, t)`
  - `flip-in`: `tl.fromTo(sel, {scaleX: 0}, {scaleX: 1, duration: d, ease: "power2.out", overwrite: "auto"}, t)`
  Para desplazar cualquier elemento ya existe `cursor-to` (es un `tl.to` de `x`/`y`
  genérico, sirve para cualquier selector).

## Contrato (el de `mockups.py`, sin excepciones)

Cada componente devuelve `(css, html, anims)`; `anims` con selectores RELATIVOS
(`#{cid}-algo`), nunca prefijados con `.viz[...]`. Reglas del `CLAUDE.md` que
aplican directo (§3, §6, §7, §9):

1. **Ningún color a mano.** Todo de `tokens` (`C[...]`, `TK.LINE`, `TK.LINE_HI`,
   `TK.SHADOW`, `TK.GLOW`, `accent_a`, `ink_a`, `shade_a`, `mix`, `rgba`). Lo vigila
   `tests/test_paletas_consumidores.py`, que ya barre todo `scripts/*.py`.
   Excepciones toleradas: sombras `rgba(0,0,0,…)`.
2. **Nada entra antes de su palabra, y eso es sobre el DOM.** Un texto que se dice
   en `at[i]` no puede estar en el HTML antes (ni a opacidad 0): se escribe con
   `type-word` o se emite vacío y se llena con `caret-off`. Los contadores arrancan
   en su valor inicial y suben con `count-roll`.
3. **El CHROME está desde el primer cuadro.** Marcos, cabeceras de perfil, rejillas
   vacías, la caja de chat: lo que no nombra nada entra en t=0 (sin anim; el host ya
   entra por opacidad). Así la banda de arriba nunca nace vacía (§4).
4. Centrar con flex, nunca `translate(-50%,-50%)` en algo que GSAP anime. Todo
   contenedor entra por opacidad; lo que se mueve es el contenido.
5. Sin `back.out`. Gestos de la tabla de §6 (`chip-in`, `rise-in`, `drop-in`,
   `stamp`, `punch`, `fade-to`, `badge-out`, `rise-bar`, `count-roll`, `draw`,
   `cursor-to`, `click`, `jitter`, `rot-to`, `cam-push`, `type-word`, `caret-off`,
   `send-on`, `alert-hit`, `scale-pop`, `glide-x`, `box-in`) + `flip-out`/`flip-in`.
6. **Dos tweens sobre la misma propiedad del mismo elemento** se pisan: el recorrido
   va en un HIJO y la opacidad en el padre (lo hace `_sello`). Un elemento que recibe
   varios `fromTo` necesita base `set-hidden`/estado declarado.
7. IDs únicos por instancia (`{cid}-…`) y `logos.mark(slug, px, uid=f"{cid}-…")`
   SIEMPRE con `uid`.
8. Sin emojis: glifos SVG en `currentColor`.
9. **Determinista**: nada de `random`. Tonos, vistas y posiciones salen de fórmulas
   (`(i*37) % n`, como `spreadsheet`).
10. **Una variante mal escrita lanza `ValueError`**, nunca cae a un `else`.
11. Texto en pantalla SOLO como interfaz: @usuario, contadores, nombre de colección,
    opciones de un menú, el prompt (b23/b24). Nada de titulares ni kickers.
12. Un objeto con texto dentro que quede bajo otra capa: `data-layout-allow-occlusion`
    en el ocluido; dos textos que se pisan a propósito: `data-layout-allow-overlap`.

## Las dos geometrías

Un mismo componente se usa en `partida` (banda de arriba) o en `grafico` (lienzo
entero). Parámetro común **`lienzo: bool = False`**:

- `lienzo=False` (partida): el host es la banda `top`, 1080×960, y el compilador alinea
  el contenido ABAJO con 160 px de margen (`BAND_FORMATOS_MARGIN`). **Alto máximo del
  componente: 760 px; ancho máximo 980.**
- `lienzo=True` (grafico): host a lienzo entero 1080×1920, contenido centrado en los
  1613 px de arriba (el compilador resta el 16 % inferior). **Alto máximo 1180 px**,
  porque el subtítulo va debajo (`cap_top` ~1400 en el plan). El componente puede
  crecer (más filas, tipos más grandes) o escalar un wrapper ESTÁTICO.

En `lienzo=True` el suelo ya lo pinta el host (viñeta + rejilla). Fondo **comic**
(monigotes): una capa de trama de semitono `position:absolute; inset:0` como primer
hijo (cubre el host entero, en las dos geometrías), con `radial-gradient(ink_a(.10) …)`
a ~14 px — misma receta que `.amtrama` de `archivo_marcado`.

## Primitivas compartidas (privadas, `_algo`)

- **`_miniatura(iid, n, vistas=None, avatar=None, w=…)`** — un reel en vertical 9:16
  con radio `md`: fondo con un tono determinista entre `surface2`, `accent_soft`,
  `mix(surface,accent,.35)`… según `n`; una silueta de busto (cabeza + hombros) en
  `ink_a(.18)`; el glifo ▶ de reels arriba a la derecha. Si `vistas` (texto tipo
  `"1,2 M"`), una fila abajo a la izquierda con el glifo ▶ + la cifra en Inter 800
  sobre una sombra `shade_a(.55)` — esa fila va en su propio `<span id="{iid}-v">`
  para poder encenderla aparte. **Es el MISMO encuadre en todos los componentes**
  (la del clímax rima con la grilla del primer cuadro).
- **`_avatar(iid, quien, n=0, px=…)`** — círculo. `quien="propio"`: la foto de
  Ezequiel, `assets/perfil.PNG` reducida a 200 px y embebida como data URI JPEG
  (generarla una vez en `assets/avatar-propio.jpg`; leerla con caché de módulo). Con
  un aro degradado de historia de IG hecho con `accent`→`accent_hi`.
  `quien="ref"`: un avatar genérico de referente — círculo de tono `n`, con la
  silueta de busto en `ink_a(.30)`. Nada de iniciales ni nombres.
- **`_glifo(nombre, px)`** — SVG de línea en `currentColor` (trazo ~1.9 sobre 24×24)
  de la interfaz de Instagram: `heart`, `heart-fill`, `comment`, `share` (avión de
  papel), `bookmark`, `bookmark-fill`, `grid`, `reels`, `play`, `search`, `dm`,
  `pause`, `sort` (líneas de orden), `pin` (chincheta), `knot` (ya existe en
  `icons.py`, reutilizarlo). Probar cada uno a 40 px en un snapshot: si no se
  reconoce, se redibuja (§7, los iconos que no sobrevivieron).
- **`_monigote(iid, pose)`** — figura de línea (cabeza círculo, cuerpo, brazos,
  piernas) en `C['text']`, trazo 6 px, ~300 px de alto, con un accesorio según `pose`:
  `tableta` (tableta de diseño con un lápiz), `timeline` (una línea de tiempo de
  edición con tres clips), `mira` (de perfil, mirando a la derecha), `cuaderno`
  (sentado con cuaderno y lápiz). Mismo dibujo base en todas: es el mismo personaje.
- **`_contador(iid, desde, prefijo="", sufijo="")`** — un `<span>` con el valor
  inicial, para `count-roll`.

## Los componentes

`at` en offsets del visual. Entre corchetes, el beat de la propuesta.

### 1. `ig_perfil(cid, variant, at, lienzo=False, handle="ezequielfrias.ia")`

La pantalla de perfil de Instagram en la pestaña de Reels: cabecera (avatar, @handle en
pastilla, tres contadores: publicaciones / seguidores / seguidos), la fila de pestañas
(`grid` · `reels` activo) y la grilla de miniaturas.

| variante | dónde | `at` | qué pasa |
| --- | --- | --- | --- |
| `llenar` | b1 partida | `[t_30, t_mes]` | Avatar propio y `@ezequielfrias.ia`. Grilla de **6×5 = 30** huecos discontinuos (chrome). En `t_30` el contador de publicaciones corre 0→30 (`count-roll`, ~0.7 s) y las 30 miniaturas entran en escalera al mismo ritmo (`chip-in`, paso ~0.022 s, en orden de lectura). En `t_mes` se dibuja alrededor de la grilla el marco de un mes de calendario (`box-in`): borde `TK.LINE_HI`, cabecera con «OCTUBRE» en mono y la fila L M X J V S D; la grilla cabe adentro. El logo de Instagram (`logos.mark("instagram", 40)`) entra en la cabecera en `t_30`. |
| `ordenar` | b6 grafico, `lienzo=True` | `[t_cuenta, t_ordena, t_reels]` | Avatar de referente (`ref`, n=1), handle `referente_1`. En t=0: grilla 3×3 de huecos + fila de pestañas (chrome). En `t_cuenta` la cabecera se arma (avatar `stamp`, handle y contadores `slide-in` escalonados) y las 9 miniaturas (sin vistas) entran. En `t_ordena` se abre un menú de orden (`rise-in`) con tres opciones «Más recientes» · «Más vistos» · «Más antiguos» y un foco de luz encima (círculo `accent_a(.18)` difuso, `chip-in`); el cursor (`_cursor` de mockups) entra y va a «Más vistos». En `t_reels` click en «Más vistos» (se resalta con `accent_pill`), el menú se va (`badge-out`) y las miniaturas **cambian de lugar** (`cursor-to` de cada una a su celda nueva, ~0.45 s, `power2.inOut`): orden nuevo = permutación determinista. |
| `vistas` | b7 partida | `[t_vista]` | La misma grilla 3×3 ya ordenada (miniaturas presentes desde t=0, sin cifras). En `t_vista` se encienden las cifras de vistas de las nueve, de la primera a la última (`slide-in` paso 0.09 s): `2,4 M · 1,8 M · 1,1 M · 640 K · 410 K · 320 K · 250 K · 190 K · 120 K`. Las tres primeras con su fila en `accent_pill` (son los outliers que vienen). |

### 2. `ig_barras(cid, at, lienzo=True)` — [b8 grafico]

La grilla convertida en barras. Nueve barras verticales en fila con las mismas cifras de
`vistas` (altura proporcional), cada una con su miniatura chiquita al pie (la rima con
b7), y una **línea punteada horizontal del promedio** con la etiqueta mono «PROMEDIO».
En t=0 todo presente, barras en `text3`. `at = [t_arriba, t_outliers]`: en `t_arriba` las
tres primeras se despegan y suben un poco (`cursor-to` y −40 en un hijo); en `t_outliers`
esas tres crecen (`cam-push` de escala en Y desde abajo, en el hijo) hasta salirse del
cuadro por arriba atravesando el promedio y se tiñen de `accent` con `TK.GLOW` (capa de
relleno de acento que se enciende con `chip-in`). Las otras seis no reciben ni un tween
(la lección de `tradeoff_bars`).

### 3. `ig_busqueda(cid, at, query="inteligencia artificial", lienzo=False)` — [b5 partida]

La barra de búsqueda de IG (glifo `search` + campo en `surface2`, chrome desde t=0) y
debajo cinco filas de perfil de resultado. En t=0 la query se empieza a teclear
(`type-word`, ~0.5 s) — el verbo «busco» es el arranque del visual. `at =
[t_5, t_nicho]`: en `t_5` caen las cinco filas una tras otra (`drop-in`, paso 0.11 s):
avatar `ref` n=1..5, `@referente_1`…`@referente_5` y un contador de seguidores en 0.
En `t_nicho` los cinco contadores corren hasta `2,4 M · 1,9 M · 1,2 M · 860 K · 640 K`:
`count-roll` de 0 al entero en miles (2400, 1900…) con sufijo « K» durante ~0.5 s y, al
terminar, un `caret-off` que fije el texto final con su formato («2,4 M»). Para el sufijo,
`count-roll` gana un 8.º elemento opcional `sufijo` (compatible hacia atrás: sin él emite
exactamente lo de hoy; test en `test_motion_gestos.py`). Logo de Instagram en la barra:
entra en `t_5`, no en t=0.

### 4. `ig_guardar(cid, at, coleccion="Outliers", lienzo=False)` — [b10 partida]

Un reel abierto (miniatura grande a la izquierda, ~300×533, con la columna de acciones
de IG a su derecha: `heart`, `comment`, `share`, `bookmark`) y a la derecha una
**tarjeta de colección** vacía con su nombre «Outliers» (chrome). `at = [t_guarda,
t_cada]`: en `t_guarda + .12` el `bookmark` se rellena de golpe (`bookmark-fill` encima,
`stamp`) y una copia chiquita de la miniatura viaja a la colección (`cursor-to`, 0.4 s) y
se queda dentro. En `t_cada` se apilan detrás otras cuatro miniaturas (`drop-in`, paso
0.08 s, desplazadas en abanico corto), cinco en total.

### 5. `monigote(cid, variant, at, lienzo=…)` — fondo comic

| variante | dónde | `at` | qué pasa |
| --- | --- | --- | --- |
| `desinflar` | b2 grafico | `[t_disenador, t_editor]` | Trama de semitono a sangre. Dos monigotes lado a lado: `tableta` y `timeline`, presentes desde t=0. En cada `at` el suyo se desinfla (`cam-push` de escala Y a .08 y caída al suelo en un hijo, ~0.3 s) y en su lugar una nubecita de tres círculos `ink_a(.25)` hace `chip-in` y `badge-out`. Queda el lienzo vacío con la trama. |
| `pregunta` | b11 grafico | `[t_problema, t_resuelve]` | Monigote `mira` a la izquierda, una miniatura grande a la derecha con tres signos «?» flotando (Inter 900, `text2`; flotan con `fade-to` entre .55 y 1, no wobble). En `t_problema` la miniatura se abre como una caja (dos mitades: la de arriba `rot-to` −24°) y cae un nudo (`icons` `knot`, 120 px, en `accent`) que rebota UNA vez (`drop-in` + `cam-push` corto). En `t_resuelve` el brazo del monigote se levanta (`rot-to` del brazo) y el nudo sube a su mano (`cursor-to`). Los «?» se apagan con `badge-out` en `t_resuelve`. |
| `copiar` | b16 partida | `[t_mano]` | Monigote `cuaderno` a la izquierda copiando (la mano con el lápiz hace un vaivén corto con `jitter` en t≈0.1); a la derecha una pila de 4 miniaturas. En `t_mano` la pila crece de golpe (+6 miniaturas `drop-in` paso 0.05) hasta taparle la cabeza al monigote. |

### 6. `nudo_viaje(cid, at, lienzo=False)` — [b13 partida]

A la izquierda el avatar de un referente (`ref`, n=1, 150 px) con el nudo pegado; a la
derecha el avatar propio (150 px); entre los dos una **flecha curva discontinua** (SVG
`path` con `stroke-dasharray`, en `text3`) — todo chrome desde t=0. `at = [t_llevar,
t_nicho]`: en `t_llevar` el nudo arranca a viajar siguiendo la curva (dos o tres
`cursor-to` encadenados que aproximen el arco, ~0.9 s en total); en `t_nicho` aterriza
sobre el avatar propio, cambia de color (una segunda capa del nudo en `C['go']` que se
enciende con `chip-in` mientras la de `accent` se apaga) y se asienta (`stamp`).

### 7. `ideas_notas(cid, at, lienzo=True)` — [b14 grafico]

Cinco miniaturas en columna a la izquierda (chrome desde t=0). `at = [t_outlier,
t_idea]`: en `t_outlier` la primera se abre por la mitad (dos mitades que se separan en
x, `cursor-to` ±30). En `t_idea` de cada miniatura sale una nota adhesiva (cuadro
`accent_soft` con tres rayas `ink_a(.25)`, sin texto) que cruza el lienzo y se apila a la
derecha formando un taco (`cursor-to` 0.35 s, paso 0.09 s).

### 8. `claude_chat(cid, variant, at, lienzo=…)`

La caja de chat de Claude: cabecera con `logos.mark("claude", 44)` + «Claude», campo
grande con el placeholder «Escribe un mensaje…» y la barra de abajo con el botón de
enviar (flecha en círculo). Chrome desde t=0.

| variante | dónde | `at` | qué pasa |
| --- | --- | --- | --- |
| `arrastrar` | b18 grafico | `[t_video, t_ganador]` | El cursor entra con una miniatura «en la mano» y la suelta dentro del campo en `t_video` (`cursor-to` del grupo + la ficha queda como adjunto: miniatura chica 90×160 con su cifra de vistas). En `t_ganador` caen las otras dos fichas (`drop-in` paso 0.1) y las tres cifras de vistas se encienden (`slide-in`). El placeholder se apaga con la primera ficha. Logo de Instagram chiquito en cada ficha. |
| `enviar` | b19 partida | `[t_pasas, t_claude]` | Las tres fichas ya adjuntas desde t=0 (rima con b18). En `t_pasas` un foco de luz se enciende sobre el campo y el cursor viaja al botón de enviar. En `t_claude` `click` + `send-on` del botón. |

### 9. `escaneo(cid, at, lienzo=True)` — [b20 grafico]

Una miniatura grande arriba (chrome desde t=0) y debajo un panel de transcripción con
seis renglones vacíos (rayas `ink_a(.10)`) y el logo de Claude en su cabecera. `at =
[t_de, t_transcripcion]`: en `t_de` una línea de luz `accent` con `TK.GLOW` barre la
miniatura de arriba abajo (`cam-push` en Y, ~0.9 s, como el láser de
`archivo_marcado`); en `t_transcripcion` los seis renglones se llenan (barras de texto
`rgba(text2,.30)` que crecen con `grow-x`, paso 0.08 s) detrás de la línea.

### 10. `prompt_encaje(cid, at, lienzo=False)` — [b21 partida]

La transcripción (panel con seis renglones llenos, el estado final de `escaneo`)
presente desde t=0. `at = [t_textos, t_prompt]`: en `t_textos` el panel se encoge a
tarjeta (`cam-push` a escala .55 en un hijo); en `t_prompt` baja desde arriba un bloque
«prompt» (tarjeta `surface` con borde `accent`, un glifo `>_` mono y tres rayas) y
encaja encima (`drop-in` + `stamp` corto). Logo de Claude en la cabecera desde t=0.

### 11. `prompt_hoja(cid, variant, at, lineas, lienzo=…)`

El prompt, el entregable del video y el único texto largo. Panel `surface` con
cabecera chica (glifo `>_` + «PROMPT» mono) y las `lineas` en **JetBrains Mono 700**
(lienzo: 30 px; banda: 23 px), interlineado 1.45. Medir con `text_px` que la línea más
larga cabe; si no, reducir el tamaño y fallar si baja de 20 px.

| variante | dónde | `at` | qué pasa |
| --- | --- | --- | --- |
| `desplegar` | b23 grafico | `[t_prompt, t_pantalla]` | Panel desde t=0, vacío. Desde `t_prompt` hasta `t_pantalla` las líneas se teclean una tras otra (`type-word` + `caret-off`, repartidas en el intervalo). En `t_pantalla` termina y queda quieto. |
| `copiar` | b24 partida | `[t_pauses, t_copies]` | Las líneas YA escritas desde t=0 (rima). Abajo del panel, la barra de progreso de un reel (track `ink_a(.15)` + relleno `C['text']` al 62 %) y un glifo `pause`. En `t_pauses` el glifo `pause` hace `stamp` y la barra se frena (`jitter`). En `t_copies` el cursor barre el bloque y cada línea queda resaltada (capa `accent_a(.28)` detrás, `grow-x` paso 0.05). |
| `absorber` | b26 partida | `[t_claude]` | La tarjeta del prompt en chico a la izquierda y el mosaico de Claude (`logos.mark("claude", 120)` en marco `surface`) a la derecha, apagado (`opacity .45`), desde t=0. En `t_claude` la tarjeta se desliza dentro del mosaico (`cursor-to` + `fade-to` .0) y el mosaico se enciende (`fade-to` 1 + un halo `accent_a` detrás, `chip-in`). |

Texto del prompt (lo usa el plan, el componente lo recibe en `lineas`):

```
Te paso la transcripción de un reel viral:
[PEGA AQUÍ LA TRANSCRIPCIÓN]
Mi nicho: [TU NICHO]. Mi audiencia: [A QUIÉN LE HABLAS].
1. Marca el gancho, la estructura y el remate.
2. Dime qué problema concreto resuelve.
3. Reescríbelo para mi nicho con mis palabras:
   misma estructura y duración, sin copiar frases.
4. Dame 3 ganchos alternativos.
```

### 12. `tablero(cid, at, lienzo=True)` — [b27 grafico]

Un tablero de corcho-estrategia (panel `surface2` con rejilla `ink_a(.06)`) presente
desde t=0, vacío. `at = [t_experto, t_marketing]`: en `t_experto` entra al costado el
mosaico de Claude encendido (`logos.mark("claude", 110)`, halo `accent_a`) con un
puntero (`icons` `pointer` o `_cursor`). En `t_marketing` se clavan cuatro miniaturas
con chinchetas (`stamp` paso 0.09, glifo `pin` en `accent`) y el puntero señala una
(`cursor-to`); esa recibe un aro `accent` (`box-in`).

### 13. `reel_tarjeta(cid, variant, at, lienzo=…)`

Una tarjeta de reel grande (la `_miniatura` a ~360×640) con la fila de autor encima
(avatar + @handle) y su contador de vistas abajo.

| variante | dónde | `at` | qué pasa |
| --- | --- | --- | --- |
| `llega` | b28 partida | `[t_toma, t_idea, t_ganadora]` | Autor `ref` n=2, `@referente_2`, cifra «1,8 M» apagada. En `t_toma` entra por la izquierda (`glide-x` invertido: `cursor-to` desde x −700) y sigue avanzando; en `t_idea` se frena en el centro (`jitter` corto); en `t_ganadora` su contador se enciende (`stamp`, fila en `accent_pill`). |
| `girar` | b29 grafico | `[t_ajustas, t_mensaje]` | La misma tarjeta, ya en el centro, cara A (referente, 1,8 M). En `t_ajustas` `flip-out` (0.22 s). Entre medias la cara A se oculta (`badge-out` 0.01) y la cara B (avatar propio, `@ezequielfrias.ia`, tono propio con `accent`, contador «0») se prepara. En `t_mensaje` `flip-in` de la cara B (0.28 s). Las dos caras son hermanas en el mismo slot; el flip se aplica al wrapper común. |
| `cruce` | CTA partida | `[t_prompt, t_outliers, t_claude]` | En `t_prompt` entra en el centro el bloque de prompt chico (tarjeta de `prompt_encaje`); el mosaico de Claude apagado a la derecha desde t=0 (chrome). En `t_outliers` una miniatura de referente entra por la izquierda y cruza el bloque (`cursor-to` ~0.6 s). En `t_claude` sale por la derecha con el avatar propio (cara B, como en `girar`) y el mosaico se enciende. |

### 14. `reel_cascada(cid, at, lienzo=True)` — [b31 grafico]

Cinco avatares de referente en fila arriba (chrome desde t=0) y abajo un contador grande
en 0. `at = [t_5, t_videos, t_referentes]`: desde `t_5` caen de cada avatar cinco
miniaturas chicas en cascada (columna por avatar; `drop-in` paso ~0.06, los cuatro
primeros avatares escalonados); en `t_videos` el contador arranca a sumar y llega a 20
(`count-roll`, hasta el final del visual); en `t_referentes` el quinto avatar suelta su
tanda y la fila queda completa.

### 15. `ig_grilla(cid, variant, at, lienzo=…)` — la grilla de 25

Grilla de **5×5 miniaturas** (la misma `_miniatura`).

| variante | dónde | `at` | qué pasa |
| --- | --- | --- | --- |
| `contar` | b32 partida | `[t_25, t_videos]` | Arriba el contador grande en 20 (desde t=0); en `t_25` corre 20→25, frena (`jitter`) y crece (`cam-push` escala 1.6); en `t_videos` las 25 miniaturas se acomodan en la grilla (`chip-in` paso 0.015) y el contador baja a su sitio sobre ella. |
| `respirar` | b36 grafico | `[t_25]` | La grilla de 25 apagada (`opacity .35`) desde t=0, cada una con su cifra chica y pareja («12 K»… variaciones mínimas). En `t_25` se enciende (`fade-to` 1, 0.5 s). Quietud: nada más se mueve. |
| `viral` | b37 partida | `[t_uno, t_viral]` | La grilla encendida desde t=0. En `t_uno` UNA miniatura (la del centro) se despega y crece hasta ocupar el espacio (`cam-push`, escala ~3, centrada) mientras las otras bajan (`fade-to` .25). En `t_viral` su contador se dispara (`count-roll` 12→2400 con sufijo « K» o equivalente) y estallan alrededor los glifos `heart-fill` (en `alert`), `comment`, `share` (ocho a diez glifos que salen del centro con `cursor-to` + `chip-in`, paso 0.04). Es el clímax: el único momento de `TK.GLOW` fuerte. |

### 16. `guion_esqueleto(cid, variant, at, lienzo=…)`

| variante | dónde | `at` | qué pasa |
| --- | --- | --- | --- |
| `voltear` | b33 grafico | `[t_estructura, t_guion, t_exacta]` | Una miniatura grande en el centro (desde t=0). En `t_estructura` `flip-out` y `flip-in` del dorso: tres bloques apilados vacíos (bordes discontinuos) con una regla vertical al costado. En `t_guion` los bloques se llenan de renglones de arriba abajo (barras `grow-x`). En `t_exacta` la regla marca el alto de cada bloque (tres marcas `accent` que se dibujan con `draw`). |
| `replicar` | b34 partida | `[t_pegas, t_replicas]` | El esqueleto (dorso lleno) sobre su miniatura a la izquierda y a la derecha una grilla de 24 tarjetas en blanco (6×4, bordes discontinuos), desde t=0. En `t_pegas` el esqueleto se despega (`cam-push` y −30 + sombra) y flota; en `t_replicas` cae sobre la grilla (`cursor-to`) y las 24 tarjetas se llenan a la vez (capa de renglones `chip-in` paso 0.01). |

## Verificación que se pide

- `tests/test_mockups_reels.py`: cada componente × cada variante renderiza en `claro` y
  en `oscuro` (`tokens.use`), sus `anims` apuntan a ids que existen en el HTML, ningún
  selector va prefijado con `.viz[`, una variante inventada lanza `ValueError`, y los
  `at` de longitud equivocada también lanzan.
- Test de `flip-out`/`flip-in` en `tests/test_motion_gestos.py`.
- La suite entera en verde: `.venv/bin/python -m pytest tests -q`.
- Un render de prueba: `tests/fixtures` no; usar `scripts/palette-sheet.py` si es fácil
  añadirlos, o compilar un plan mínimo. No es obligatorio: la revisión de frames la hago yo
  sobre la pieza.
