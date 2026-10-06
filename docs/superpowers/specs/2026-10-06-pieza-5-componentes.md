# Pieza 5 — componentes nuevos (zócalo de plugins, Claude Code)

Pieza: «No uses Claude Code hasta instalar estos 5 plugins». Paleta `oscuro`, layout
`formatos`. Brief de plan-edicion: `Marketing/Reels/plan-edicion/planes/2026-09-29-5.md`.
Se edita en conversación con Ezequiel (no desde el dashboard): `VIDEOS ORIGINALES/5/pedido.json`
existe solo para que corran `pieza.py`/`armar-version.py`.

**El zócalo es el objeto que cruza el video y cambia de estado**: cinco huecos alrededor de la
terminal de Claude Code. En el gancho está vacío y la terminal frenada por una barrera; cada
plugin enciende SU hueco cuando se lo nombra (siempre el mismo gesto: el mosaico se dibuja con
línea de neón y cae su pastilla con el nombre); en el CTA el zócalo se desarma en una lista
con un link por fila. Por eso los componentes comparten primitivas y la MISMA geometría del
zócalo entre variantes: es lo que hace que se lea «la misma cosa».

La mascota pixelada (sprites generados con Higgsfield) aparece en `piedras_modelo` (salta) y en
`mascota_cuaderno` (espía con un cuaderno).

## Dónde vive

- Módulo nuevo `.claude/skills/video-tech-premium/scripts/mockups_plugins.py` (`scripts/` es un
  enlace a esa carpeta). Reutiliza de `mockups_reels` lo que sirva (`_host`, `_need_at`,
  `_shared_css`, `_halftone`, `_contador`, `_glifo`) y de `mockups` (`text_px`, `_cursor`,
  `_cursor_css`); colores de `tokens` como hace `mockups_reels.py`.
- `build-composition.py`: `import mockups_plugins` y una entrada por componente en el
  diccionario de despacho de `build_visuals` (junto a los de `mockups_reels`).
- Todos los tiempos van en **`at: list`** (offsets del visual; el compilador ya los remapea con
  `absolute_times`). Ninguna otra clave de tiempo.
- Tests nuevos en `tests/test_mockups_plugins.py` (ver «Tests»).

## Contrato

**El mismo de `docs/superpowers/specs/2026-10-05-pieza-4-componentes.md`, sección «Contrato»,
sin excepciones** (léela entera antes de escribir código): `(css, html, anims)` con selectores
RELATIVOS; ningún color a mano (todo de `tokens`; excepción: sombras `rgba(0,0,0,…)` y los
colores propios DENTRO de los SVG/PNG de marca, que se embeben tal cual); nada entra antes de
su palabra y eso es sobre el DOM (texto dicho → `type-word` o span vacío + `caret-off`;
contadores con `count-roll` desde su valor inicial); el CHROME está desde t=0; centrar con flex;
sin `back.out`; dos tweens sobre la misma propiedad → el recorrido en un HIJO; ids `{cid}-…`;
`logos.mark(slug, px, uid=f"{cid}-…")` SIEMPRE con `uid`; sin emojis; determinista; variante
mal escrita → `ValueError`; texto en pantalla SOLO como interfaz.

Las dos geometrías (`lienzo=False` partida: banda 1080×960, alto máx 760, ancho máx 980;
`lienzo=True` grafico: alto máx 1180, `cap_top` ~1400) y el fondo **comic** (`_halftone`) son
los de esa spec.

**Fallos que Codex ya tuvo en la pieza 4 y NO se pueden repetir** (los vigilo en la revisión):
radios sin `px` en el CSS; `!important` que bloquea un tween (`grow-x`); `jitter` que deja `x`
en 0 al terminar; un `fromTo` sin `immediateRender:false` cuando el elemento ya tiene un estado
declarado antes.

## Primitivas compartidas (privadas)

- **`_mosaico(iid, slug, px=150, nombre=None)`** — un mosaico de app: cuadrado con radio `lg`,
  fondo `surface2`, hairline `TK.LINE_HI`, el logo centrado a ~60 % (`logos.mark(slug, …,
  uid=iid)`). Debajo, opcional, la **pastilla con el nombre** (`nombre`): Inter 800 ~26 px en
  `text` sobre `surface`, borde `TK.LINE`, radio pill, emitida VACÍA y llenada con `type-word`
  en su palabra (o, si el nombre ya se dijo antes, presente). Slugs de la pieza: `omniroute`,
  `claudemem` (PNG), `headroom`, `claudecode`, `github` (Task Observer no tiene marca propia: la
  de un repo es GitHub), `anthropic`, `instagram`. Los vendorizados ya están en `assets/logos/`.
- **`_neon(iid, w, h, r)`** — el contorno de neón de un hueco/mosaico: un `<svg>` con un
  `<rect rx=r>` de trazo 4 px en `C['accent']` con `filter: drop-shadow(0 0 10px accent_a(.8))`,
  `stroke-dasharray`/`dashoffset` preparados en t=0 (trampa 7 de §9) para dibujarse con `draw`.
  **Es el gesto que se repite idéntico en los cinco plugins**: la rima de la lista.
- **`_terminal(iid, w, h, lineas=0)`** — una ventana de terminal: barra con el semáforo macOS
  (excepción de color permitida), cuerpo `surface` con hairline, prompt `>` en `accent_hi` mono
  y un cursor de bloque que parpadea; `lineas` renglones de barras de contenido
  (`rgba(text2,.30)`, anchos deterministas). El logo `claudecode` chico en la barra.
- **`_sprite(iid, pose, px)`** — la mascota: `<img>` con `assets/mascota/mascota-{pose}.png`
  embebida como data URI PNG (caché de módulo, como `_avatar_data` de `mockups_reels`),
  `image-rendering: pixelated`. Poses: `salto`, `espia`, `espaldas`.
- **`_proveedor(iid, nombre, px)`** — ficha redonda `surface2` con el SVG de
  `assets/proveedores/{nombre}.svg` embebido como data URI `<img>` (son SVG de OmniRoute con
  colores propios; como `<img>` no colisionan ids). Disponibles: cerebras cohere deepseek
  fireworks gemini groq huggingface kimi mistral nvidia openrouter perplexity qwen sambanova xai.

## La geometría del zócalo (fija, la comparten todas sus variantes)

En el centro, `_terminal` de 420×300. Alrededor, **cinco huecos de 150×150** en arco: dos a la
izquierda, uno arriba, dos a la derecha (posiciones absolutas fijas dentro de un tablero de
980×700; el mismo tablero en partida y en grafico, en grafico escalado con un wrapper ESTÁTICO
×1.25). Un hueco vacío = borde discontinuo `TK.LINE_HI` 3 px, sin relleno. Orden de los huecos:
1 izquierda-arriba, 2 izquierda-abajo, 3 arriba, 4 derecha-arriba, 5 derecha-abajo. Los
mosaicos que ya se nombraron en beats anteriores aparecen YA PUESTOS (presentes desde t=0,
encendidos en `accent_a(.15)` de fondo del hueco), los que no, como huecos vacíos.

Plugins por hueco: 1 `omniroute` «OmniRoute» · 2 `claudemem` «Claude Mem» · 3 `headroom`
«Headroom» · 4 `claudecode` «Claude Code Setup» · 5 `github` «Task Observer».

## Los componentes

Entre corchetes, el beat. `at` son los instantes de las palabras, en orden.

### 1. `terminal_barrera(cid, at, lienzo=False)` — [b1 partida, fondo comic]

`at = [t_abrir, t_code]`. Trama de semitono. En t=0 (chrome): una terminal CERRADA, una barra
fina centrada de 420×44 (la barra de título sola, con el semáforo). En `t_abrir` la ventana se
abre hacia abajo hasta 420×300 (`cam-push`/escala Y desde arriba en un hijo) y aparece el cursor
parpadeando. En `t_code` baja de golpe desde arriba una **barrera a rayas** (rayas diagonales
`accent` / `bg`, 600×70, con dos postes) que se clava delante de la terminal (`drop-in` rápido,
0.18 s) y la terminal queda congelada: el cursor deja de parpadear y la ventana baja a
`fade-to` .55. Sin texto.

### 2. `zocalo(cid, variant, at, lienzo=False, puestos=0)` — [b2, b3, b11, b15, b22, b28, b34]

| variante | dónde | `at` | qué pasa |
|---|---|---|---|
| `instala` | b2 grafico, `lienzo=True` | `[t_instala, t_5, t_plugins]` | En t=0 la terminal del centro y la barrera a rayas de `terminal_barrera` delante (el estado en que terminó b1). En `t_instala` se dibujan los cinco huecos vacíos (`draw` de sus bordes discontinuos, escalonado 0.06 s). En `t_5` caen cinco mosaicos EN BLANCO (sin logo: todavía no se nombró ninguno) uno por uno, 0.09 s de paso, y encajan en su hueco (`drop-in`). En `t_plugins` los cinco huecos se encienden a la vez (`chip-in` de un halo `accent_a(.25)` detrás de cada uno) y la barrera sube y se va (`cursor-to` y −500 + `badge-out`). |
| `enciende` | b3, b11, b15, b22, b28 partida | `[t_numero, t_nombre]` | `puestos` = cuántos plugins ya se nombraron antes (0..4): esos huecos llevan su mosaico con logo ya puesto. El hueco `puestos+1` es el protagonista: en `t_numero` se ilumina (halo + el resto del tablero `fade-to` .45, «queda solo en pantalla»); en `t_nombre` su contorno se DIBUJA con `_neon` (`draw`, 0.35 s), el logo aparece dentro (`chip-in`) y cae la pastilla con el nombre debajo (`type-word`). Para `puestos=4` (Task Observer) el zócalo queda completo: en `t_numero` además los cinco halos se encienden juntos un instante (el compás que cierra). |
| `lista` | b34 partida | `[t_5, t_link]` | En t=0 el zócalo completo (los cinco mosaicos con logo). En `t_5` los cinco mosaicos se despegan y se acomodan en una **lista vertical** (`cursor-to` de cada uno a su fila, 0.45 s, `power2.inOut`; la terminal y los huecos `badge-out`), cada fila: mosaico de 96 px + su nombre (ya dicho, presente). En `t_link` a cada fila se le engancha a la derecha una **pastilla de link** (glifo de cadena en `currentColor` + texto mono «link»), de arriba abajo, 0.08 s de paso (`chip-in`). |

### 3. `anillo_proveedores(cid, at, lienzo=True)` — [b5 grafico, oscuro]

`at = [t_200, t_proveedores]`. En t=0 (chrome): el mosaico de Claude Code en el centro (200 px)
con el mosaico chico de OmniRoute pegado a su lado (es el que conecta) y un anillo punteado
vacío alrededor (radio ~380). En `t_200` el anillo se completa de golpe: 15 fichas de proveedor
(`_proveedor`, 96 px) entran escalonadas 0.03 s (`chip-in`) con una línea `draw` desde el centro
a cada una, y un contador en el medio, debajo del mosaico, corre de 0 a **200** con prefijo «+»
(`count-roll`, 0.7 s; Inter 900 ~110 px en `accent_hi`). En `t_proveedores` las fichas se
encienden (halo) y por cada línea viaja una partícula (punto `accent` de 10 px, `cursor-to` desde
la ficha al centro, escalonado). **No se escribe «358» en ninguna parte**: el guion dice «más de
200».

### 4. `costo_llaves(cid, at, lienzo=False)` — [b6 partida]

`at = [t_gratis, t_api, t_ia]`. Tres fichas grandes de proveedor (`_proveedor` 150 px: groq,
gemini, openrouter) en fila, cada una con un contador de costo debajo «$ 20» (mono). En
`t_gratis` los tres contadores caen a «$ 0» (`count-roll` con prefijo «$ ») y se apagan
(`fade-to` .4). En `t_api` las tres fichas giran (`flip-out` / `flip-in`) y del otro lado son
**llaves de API**: una tarjeta con un glifo de llave (`currentColor`) y una cadena mono enmascarada
`sk-••••••` (es interfaz). En `t_ia` detrás de las llaves se encienden tres mosaicos chicos de
modelo (siluetas de ficha `surface2` con un destello `accent`), `chip-in`.

### 5. `piedras_modelo(cid, at, lienzo=False)` — [b8 partida]

`at = [t_salta, t_siguiente, t_modelo]`. Una fila de 6 mosaicos de modelo (`_proveedor`:
deepseek, mistral, qwen, kimi, cerebras, nvidia) como piedras en un río (línea ondulada
`accent_a(.15)` debajo). La mascota (`_sprite` `salto`, 170 px) parada sobre la primera. En
`t_salta` la primera se apaga (`fade-to` .3, gris) y la mascota salta en arco a la segunda
(`cursor-to` en x + un hijo con `cursor-to` en y arriba/abajo, 0.45 s). En `t_siguiente` la
que la recibe se enciende (halo `accent_a(.3)`). En `t_modelo` la fila entera se desplaza a la
izquierda (`glide-x` −260) y entran por la derecha dos mosaicos más esperando su turno.

### 6. `contador_tokens(cid, at, lienzo=True)` — [b9 grafico, CLÍMAX]

`at = [t_1600, t_millones, t_tokens]`. Sobre el suelo, un contador mono que arranca en
«0». En `t_1600` corre hasta **1.600.000.000** (`count-roll` 1.2 s, separador de miles «.»,
Inter 900 ~90 px). En `t_millones` la cifra crece hasta ocupar el ancho del lienzo
(`cam-push` ×1.6 en un wrapper, `expo.out`) y pasa a `accent_hi`. En `t_tokens` detrás se apila
una montaña de fichas de token (círculos `surface2` con hairline y un glifo «T» mono adentro,
~40 fichas, posiciones deterministas, `drop-in` escalonado 0.012 s, de abajo hacia arriba
hasta el borde de arriba). Es el único momento de la pieza con `TK.GLOW` en la cifra.

### 7. `dos_terminales(cid, at, lienzo=True)` — [b12 grafico]

`at = [t_memoria, t_sesion, t_siguiente]`. Dos `_terminal` lado a lado (440×520 cada una): la
izquierda llena de renglones, la derecha vacía (chrome, t=0). En `t_memoria` de la izquierda se
desprende un **hilo de luz** (un trazo SVG curvo `accent` con glow, `draw` 0.4 s) que queda
flotando entre las dos. En `t_sesion` la terminal izquierda se cierra (escala Y a 0 en un hijo +
`badge-out`) y el hilo queda solo (un pulso de opacidad). En `t_siguiente` el hilo entra en la
derecha (el trazo se termina de dibujar hasta ella) y la llena de renglones de arriba abajo
(`rise-bar`/`chip-in` escalonado 0.04 s).

### 8. `cable_headroom(cid, variant, at, lienzo=False)` — [b16 partida, b17 grafico]

La MISMA escena en dos variantes (rima): un cable grueso horizontal (barra 18 px `text3` con
borde) que cruza el ancho.

| variante | dónde | `at` | qué pasa |
|---|---|---|---|
| `clavar` | b16 partida | `[t_pone, t_medio]` | En t=0 el cable entero. En `t_pone` el mosaico de Headroom (`_mosaico headroom` 170 px) baja desde arriba (`drop-in`). En `t_medio` se clava en el centro (`stamp`) y el cable queda partido en dos tramos que entran y salen de él (el tramo central `badge-out`, dos puntas de enchufe aparecen a los lados del mosaico). |
| `chat` | b17 grafico, `lienzo=True` | `[t_tu, t_modelo]` | En t=0: Headroom en el centro con los dos tramos de cable (el estado final de `clavar`). En `t_tu` a la izquierda se arma una caja de chat (`rise-in`) con el cursor de texto adentro. En `t_modelo` a la derecha aparece el mosaico del modelo (`_mosaico claude` sin pastilla, `chip-in`) y el cable queda completo de punta a punta (dos tramos extra `grow-x`), con una partícula que viaja de izquierda a derecha. |

### 9. `prensa(cid, at, lienzo=False)` — [b18 partida, fondo comic]

`at = [t_comprime, t_corta, t_sobra]`. Trama de semitono. Un bloque altísimo de contexto
(columna de 30 renglones de barras, 320×620) en el centro, y arriba una prensa (placa gruesa
`text2` con un vástago). En `t_comprime` la prensa baja y el bloque se aplasta a un tercio de
su alto (`cam-push` escala Y en un hijo, origen abajo). En `t_corta` los renglones de los bordes
(los 8 de arriba y los 8 de abajo del bloque original, ahora apretados) se desprenden como
recortes de papel (`rot-to` ±12° + `cursor-to` hacia afuera). En `t_sobra` los recortes caen
fuera de cuadro (`cursor-to` y +700) y se amontonan abajo.

### 10. `dos_salidas(cid, at, lienzo=True)` — [b20 grafico, oscuro]

`at = [t_mismo, t_resultado]`. Dos pantallas de salida idénticas lado a lado (400×300, los
mismos renglones), cada una con un check en un círculo `go` (glifo en `INK_ON_FILL["success"]`)
apagado. Debajo de cada una su pila de fichas de token (12 fichas, la misma altura). En
`t_mismo` se encienden los dos checks a la vez (`stamp`). En `t_resultado` la pila de la
derecha se desmorona hasta un tercio (las 8 de arriba `cursor-to` hacia abajo y `badge-out`).
**La pila de la izquierda no recibe ni un tween** (lección de `tradeoff_bars`).

### 11. `sello_oficial(cid, at, lienzo=False)` — [b23 partida, oscuro]

`at = [t_oficial, t_anthropic]`. En t=0 el mosaico de Claude Code Setup (`_mosaico claudecode`
170 px con su pastilla «Claude Code Setup», ya dicha) en el centro. En `t_oficial` se le estampa
encima, en la esquina de arriba a la derecha, una **insignia de verificado** (círculo `go` con
check, 64 px, `stamp`). En `t_anthropic` debajo de la pastilla se dibuja el logo de Anthropic
(`logos.mark("anthropic", 90, uid=…)`, `chip-in`) con un resplandor detrás (`accent_a(.22)`
difuso, `fade-to`).

### 12. `arbol_escaneo(cid, at, lienzo=True)` — [b24 grafico]

`at = [t_revisa, t_codigo]`. El árbol de archivos de un proyecto a lienzo completo: ~14 filas
(carpetas y archivos con glifo de carpeta/archivo en `currentColor`, nombres mono genéricos
de proyecto: `src/`, `app.ts`, `api/`, `routes.ts`, `db.ts`, `tests/`, `package.json`,
`README.md`, `.claude/`, `CLAUDE.md`…, sangría por nivel), todas en `text3` (chrome, t=0). En
`t_revisa` una línea de luz horizontal (`accent` con glow, ancho completo) arranca a barrer
de arriba abajo (`cursor-to` y, 1.3 s, lineal). En `t_codigo` las filas se encienden a `text`
justo detrás de la línea (escalonado igual al barrido: cada fila en el instante en que la línea
la cruza).

### 13. `servidor_mcp(cid, variant, at, lienzo=…)` — [b26 grafico + b26b partida]

La misma escena en dos variantes. Un servidor (rack de 3 unidades, 260×200, con 3 puertos-LED
por unidad) arriba al centro; tres servicios (fichas con glifo: base de datos, navegador,
documento) en arco; el árbol del proyecto (versión chica de `arbol_escaneo`, 6 filas) abajo.

| variante | dónde | `at` | qué pasa |
|---|---|---|---|
| `conectar` | b26 grafico, `lienzo=True` | `[t_servidores, t_mcp]` | En t=0 nada más que el suelo y el contorno discontinuo del servidor (chrome). En `t_servidores` el servidor se dibuja (`draw` + `rise-in`) y se encienden sus puertos de a uno (0.08 s). En `t_mcp` salen tres líneas (`draw`) hacia los tres servicios (`chip-in`) y empiezan a viajar partículas. |
| `aterrizar` | b26b partida | `[t_proyecto]` | En t=0 servidor + servicios + líneas ya puestos (el estado final de `conectar`), partículas viajando en bucle determinista (3 pasadas), y el árbol del proyecto abajo en `text3`. En `t_proyecto` las tres líneas aterrizan en el árbol (`draw` de un tramo final) y encajan con un destello en tres filas (`chip-in` de un halo). |

### 14. `mascota_cuaderno(cid, at, lienzo=True)` — [b29 grafico]

`at = [t_mira, t_trabaja, t_estilo]`. En el centro una `_terminal` (520×340) con un cursor de
ratón (`_cursor`). En t=0 la terminal y el borde izquierdo del lienzo vacío. En `t_mira` la
mascota (`_sprite espia`, 260 px) asoma por el borde izquierdo (`cursor-to` x desde −300) y se le
«encienden los ojos» (un destello `accent_a(.5)` sobre la cara, `chip-in`). En `t_trabaja` el
cursor repite la misma rutina tres veces (tres `cursor-to` ida y vuelta + `click`, 0.35 s cada
una) y de cada movimiento sale un trazo (`draw` de un garabato SVG chico) que vuela al cuaderno
de la mascota. En `t_estilo` los trazos se juntan en el cuaderno en una **firma** (un trazo SVG
largo, `draw` 0.5 s, en `accent_hi`).

### 15. `reloj_fondo(cid, at, lienzo=True)` — [b31 grafico, oscuro]

`at = [t_tiempo, t_plano]`. Una fila de cuatro tarjetas de skill (glifo + barra de nivel
`rise-bar`, sin texto) en el centro; un reloj (círculo con dos agujas, `rot-to`) al costado
derecho. En `t_tiempo` la aguja larga gira una vuelta (`rot-to` 360, 1.2 s) y las barras de las
tarjetas suben solas un escalón cada una (escalonado). En `t_plano` toda la fila se va al fondo:
`cam-push` ×0.78 + `fade-to` .35 + `filter: blur(6px)` (un `tl.to` de `filter` en el wrapper;
si `emit_anim` no tiene un gesto de blur, agregar `blur-to` con test, como `flip-in`), y delante
se planta una `_terminal` de Claude Code trabajando (`rise-in`, renglones que siguen entrando
de a uno).

## Tests (`tests/test_mockups_plugins.py`)

Por cada componente y variante: compila en `oscuro` y en `claro` sin lanzar; devuelve
`(css, html, anims)`; todos los selectores de `anims` existen en el `html` (por id); ningún
id se repite; los `at` fuera de rango o con la longitud equivocada lanzan `ValueError`; una
variante inexistente lanza `ValueError`; ningún hex/rgba escrito a mano fuera de las excepciones
(lo barre ya `test_paletas_consumidores.py`). Casos de DOM-antes-de-palabra: en `zocalo
enciende` la pastilla del protagonista está vacía en el HTML; en `anillo_proveedores` el
contador arranca en «0». Correr la suite entera: `.venv/bin/python -m pytest -q` en verde.

## Fuera de alcance

No tocar `plan-cuerpo.json`, `plan-cta-*.json`, `propuesta.json`, transcripts, cortes ni
renders: el plan lo escribe Claude. No renderizar nada. No generar imágenes ni llamar
servicios pagos.
