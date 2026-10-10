# Pieza 8 — componentes nuevos (Claude Code + Codex, cangrejo y obrero)

Pieza: «Codex dentro de Claude Code: Claude decide y Codex lo hace». Paleta `claro`, layout
`formatos`. Brief de plan-edicion: `Marketing/Reels/plan-edicion/planes/2026-10-08-1001.md`
(léelo: dice qué hace cada momento y por qué). Se edita en conversación con Ezequiel.

**Decisiones de Ezequiel (2026-10-09):**
- Los dos personajes son **imágenes de Higgsfield** ya recortadas con alfa, en
  `assets/personajes-8/`: el cangrejo pixelado de Claude y el obrero que es Codex. El
  movimiento se arma con transform/opacity sobre las imágenes y **cambiando de pose** (dos
  `<img>` apiladas, se apaga una y se enciende la otra). No se dibujan personajes en SVG.
- **Todas las interfaces se recrean** (no hay grabaciones): la ventana de Claude Code, el
  catálogo, la cuenta de ChatGPT, el CLAUDE.md, el panel de cambios.
- **Los comandos se ven borrosos todo el video y se leen nítidos solo en el clímax**
  (`instalacion` variante `enfoque`).

**El objeto que cruza el video es la ventana de Claude Code** (una terminal). Es SIEMPRE la
misma primitiva `_terminal`, con la misma cabecera, el mismo campo y la misma barra de
estado; en cada componente cambia lo que pasa dentro. La rima es estructura: si dos
componentes muestran la terminal, tiene que leerse que es la misma.

## Dónde vive

- Módulo nuevo `.claude/skills/video-tech-premium/scripts/mockups_codex.py` (`scripts/` es un
  enlace). Reutiliza de `mockups_reels` (`_host`), de `mockups_plugins` (`_need_at` con
  dominio y orden), de `mockups` (`text_px`) y el patrón de imágenes de `mockups_chatgpt`
  (`assets_de`).
- `build-composition.py`: `import mockups_codex` y una entrada por componente en el
  diccionario de despacho de `build_visuals` (junto a `chatgpt_chat`).
- Todos los tiempos van en **`at: list`** (offsets del visual; el compilador los remapea con
  `absolute_times`). Ninguna otra clave de tiempo.
- Tests nuevos en `tests/test_mockups_codex.py`.

## Contrato

**El mismo de `docs/superpowers/specs/2026-10-05-pieza-4-componentes.md`, sección «Contrato»,
sin excepciones** (léela entera antes de escribir código): `(css, html, anims)` con
selectores RELATIVOS; nada entra antes de su palabra y eso es sobre el DOM; el CHROME está
desde t=0; centrar con flex; sin `back.out`; dos tweens sobre la misma propiedad → el
recorrido en un HIJO; ids `{cid}-…`; `logos.mark(slug, px, uid=f"{cid}-…")` SIEMPRE con
`uid`; sin emojis; determinista; variante mal escrita → `ValueError`; texto en pantalla SOLO
como interfaz. Las dos geometrías (`lienzo=False` partida: alto máx 760, ancho máx 980;
`lienzo=True` grafico: alto máx 1180, el subtítulo va debajo con `cap_top` ~1400) son las de
esa spec.

**Fallos que Codex ya tuvo en las piezas 4, 5 y 6 y NO se pueden repetir** (los reviso uno
por uno): radios sin `px` en el CSS; `!important` que bloquea un tween; `jitter` que deja
`x` en 0; un `fromTo` sin `immediateRender:false` cuando el elemento ya tiene un estado
declarado antes; selectores ya prefijados; una imagen embebida en vez de referenciada.

### Gestos

Solo los que ya existen en `emit_anim` (`chip-in`, `rise-in`, `drop-in`, `stamp`, `punch`,
`fade-to`, `badge-out`, `rise-bar`, `grow-x`, `count-roll`, `draw`, `cursor-to`, `click`,
`jitter`, `rot-to`, `type-word`, `caret-off`, `send-on`, `alert-hit`, `scale-pop`,
`glide-x`, `box-in`, `flip-out`, `flip-in`, `set-hidden`, `color-to`…; míralos en
`build-composition.py` antes de usarlos y respeta sus firmas). Si de verdad falta uno, se
agrega al emisor con su test en `tests/test_motion_gestos.py` y se dice en el reporte. Un
cambio instantáneo de pose es un `fade-to` de 0.01 s en las dos imágenes.

## Los fondos por escena (`fondo`)

El compilador pinta el suelo de la paleta de la pieza (`claro`) y no cambia por escena.
Cada componente recibe **`fondo: "claro" | "oscuro" | "comic"`** y, si no es `claro`, pinta
su propio suelo como PRIMER hijo, `position:absolute; inset:0`, cubriendo el host entero en
las dos geometrías:

- **`oscuro`**: el suelo de la paleta oscura con su viñeta y su retícula. Los colores de TODO
  el componente salen de esa paleta, no de `C`. Para eso, `tokens.py` gana
  **`paleta(nombre) -> dict`**: devuelve una COPIA de `_derive(nombre)` sin activar nada
  (no muta `C`). El componente hace `P = TK.paleta("oscuro") if fondo == "oscuro" else C` y
  escribe todo con `P[...]`. Test: `paleta("oscuro")` no cambia `C` y da el `bg` oscuro.
- **`comic`**: suelo `accent` (terracota) con trama de semitono encima
  (`radial-gradient(ink_a(.16) 22%, transparent 24%)` a ~16 px, la receta de `.amtrama`),
  colores de `C`. Es el «problema».
- **`claro`**: nada; el host ya trae el suelo.

`fondo` mal escrito → `ValueError`. Si `test_paletas_consumidores.py` se queja de que un
componente con `fondo="oscuro"` renderiza igual en las dos paletas, se agrega la excepción
en el test con un comentario que diga por qué (el fondo de escena es fijo a propósito).

## Interfaz literal de Claude Code

La terminal de Claude Code es interfaz LITERAL (como ChatGPT en la pieza 6): sus colores no
salen de la paleta y van en un solo lugar, **`tokens.BRANDS["claudecode"]`**, y el módulo
los lee de ahí, nunca un hex suelto:

| clave | valor | uso |
| --- | --- | --- |
| `bg` | `#1A1918` | fondo de la terminal |
| `surface` | `#262422` | campo de entrada, barra de estado, menú |
| `line` | `#3A3734` | hairlines y bordes del campo |
| `text` | `#EDEAE5` | texto |
| `text2` | `#9C978F` | secundario |
| `accent` | `#D97757` | el naranja de Claude (marco del campo, `✻`, prompt) |
| `ok` | `#6BC07F` | tildes |
| `err` | `#E5675A` | error |

La tarjeta de cuenta de ChatGPT usa `BRANDS["chatgpt"]` (ya existe). Excepción de colores
en el test si hace falta, con comentario.

## Imágenes

`assets/personajes-8/<quien>-<pose>.png` (RGBA, ~640 px el lado mayor, con borde de pegatina
crema; se leen sobre crema, terracota y oscuro):

- `cangrejo`: `piensa`, `sello`, `lupa`, `caja`, `encogido`, `saluda`
- `obrero`: `caja-herramientas`, `martillo`, `linterna`, `carga`, `camina`, `tira`
  (en `tira` la soga sale por el borde derecho de la imagen: se tapa con lo que se tira)

**No se embeben**: ruta relativa `personajes-8/<quien>-<pose>.png`, y el visual las declara
en `"assets"`. `mockups_codex.assets_de(fn_name, kw) -> list[str]` devuelve las que usará esa
llamada (mismo contrato que `mockups_chatgpt.assets_de`). Pose o quien que no existe →
`ValueError`.

## Logos

`claude` y `openai` están vendorizados. **Codex y ChatGPT son productos de OpenAI y no tienen
marca vendorizable propia: se pintan con `openai`** (la marca honesta, mismo criterio que un
repo con GitHub). Helper `_logo(iid, slug, px)` que mapea `codex`/`chatgpt` → `openai` y
llama `logos.mark(..., uid=iid)`.

## Primitivas compartidas (privadas)

- **`_suelo(cid, fondo)`** — lo de arriba.
- **`_terminal(cid, w, h, P, logo_at=None)`** — LA ventana. Rectángulo `cc.bg`, radio
  `lg`, hairline `cc.line`, sombra `TK.SHADOW`. Barra de título de 48 px con el semáforo
  macOS (excepción ya tolerada) y, centrado, `claude` en mono `cc.text2`. Debajo, la
  cabecera de Claude Code: un recuadro con borde `cc.accent` 2 px y radio `md` con `✻`
  (glifo SVG, no carácter si da problemas de fuente) + «Claude Code» Inter 700 26 px en
  `cc.text`; si `logo_at` es un offset, el logo `claude` a 30 px a su izquierda entra en
  ese instante (antes no está en el DOM); si es `None`, no hay logo en la cabecera. Abajo
  del todo, el campo de entrada (borde `cc.line`, radio `md`, prompt `>` en `cc.accent` y
  un caret que parpadea) y, debajo del campo, la **barra de plugins**: una franja `cc.surface`
  de 56 px con un hueco discontinuo (el slot del plugin) a la izquierda. El cuerpo (entre
  cabecera y campo) es un contenedor `{cid}-body` donde cada componente pone lo suyo.
  Devuelve el html; su CSS va en `_css`.
- **`_personaje(iid, quien, poses, px)`** — un wrapper `{iid}` (el que se MUEVE) con una
  `<img>` por pose (`{iid}-<pose>`), todas apiladas en la misma caja (`position:absolute`,
  abajo-centro). Solo la primera visible; las otras a opacidad 0 desde el CSS. `px` = alto
  de la caja. Cambiar de pose = `fade-to` 0.01 s de la saliente a 0 y la entrante a 1.
- **`_tablero(iid, P)`** — el plan: tarjeta `surface` 220×150 radio `md` con tres renglones,
  cada uno una casilla cuadrada + una barra (`rgba(text2,.30)`). Los renglones se dibujan
  con `draw`/`grow-x` cuando el componente lo pide.
- **`_bloque(iid, P)`** — el bloque sólido que construye el obrero: un prisma 200×150 hecho
  con tres caras planas (frente `accent`, tapa `mix(accent, surface, .35)`, lateral
  `mix(accent, text, .25)`), con una junta vertical en el frente (`{iid}-junta`, una línea
  `text` a opacidad 0 que se enciende cuando el bloque «se abre») y las dos mitades del
  frente en hijos separados (`{iid}-izq`, `{iid}-der`) para poder separarlas.
- **`_mosaico(iid, slug, P, px=150)`** — mosaico de app: cuadrado radio 24 % con el logo
  centrado. `fusionado`: el mismo cuadrado partido al medio por una costura vertical,
  mitad izquierda `surface` con `claude`, mitad derecha `text` (oscuro) con `openai`; las
  dos mitades son hijos (`{iid}-a`, `{iid}-b`) para que entren por separado.
- **`_comando(iid, texto, legible=False)`** — un renglón de comando: `>` en `cc.accent` +
  el texto en JetBrains Mono 500 24 px `cc.text`. **Borroso**: `filter: blur(7px)` y
  opacidad .85 en un hijo `{iid}-b`. Para el enfoque, una SEGUNDA copia nítida en
  `{iid}-n` apilada encima a opacidad 0: enfocar = `fade-to` de `-b` a 0 y de `-n` a 1 (sin
  gesto nuevo). Fuera del clímax solo se emite la copia borrosa. Los cuatro comandos (en
  ese orden, exactos):
  1. `/plugin marketplace add openai/codex-plugin-cc`
  2. `/plugin install codex@openai-codex`
  3. `/reload-plugins`
  4. `/codex:setup`
  Y los de Codex del beat 4: `/codex:rescue`, `/codex:review`, `/codex:adversarial-review`.
- **`_medidor(iid, P, valor=100)`** — barra de uso: pista `surface3` 600×44 radio `pill`,
  relleno `accent` (escala X desde la izquierda: `rise-bar` no, `grow-x`/`scaleX` con
  `transform-origin:left`) y el porcentaje en Inter 800 30 px dentro (`count-roll`). Rótulo
  «Uso» en mono `text2` arriba a la izquierda (interfaz).
- **`_barra_trabada(iid, P)`** — la barra de progreso del error: pista 640×36, relleno al
  52 %, y la **tarjeta de error** `{iid}-err` (180×110, `alert`, radio `md`, glifo ✕ en
  `INK_ON_FILL`-equivalente y dos barras) encajada de costado en el borde del relleno. Es
  la MISMA en `error_trabado` `traba` y `destraba`: misma geometría, mismos ids relativos.
- **`_marcador(iid, P, n=2)`** — casillas de intentos 96×96 con borde `text` 4 px.

Todo lo que se mueve en un personaje (entrar, girar alrededor, cargar) va en el wrapper;
la pose cambia en las `<img>`.

## Componentes

Tamaños orientativos: personajes a 260–340 px de alto en `lienzo=True`, 180–230 en partida.
Cada «en at[i]» es el instante exacto en que eso EMPIEZA.

### 1. `cc_gancho(cid, variant, at, lienzo=False, fondo="oscuro")`

- **`piensa`** (partida, `at=[t_claude, t_piensa]`). La terminal ocupa la banda (≈980×700)
  y está encendida desde el primer cuadro, con el caret parpadeando (chrome, sin logo en la
  cabecera hasta at[0]: `logo_at=at[0]`). En at[0] el cangrejo `piensa` (190 px) se asoma
  desde el borde inferior del cuerpo (sube y +60 → 0 dentro de un contenedor con
  `overflow:hidden`). En at[1] se infla sobre su cabeza un globo de pensamiento (dos
  circulitos + nube, `scale-pop` escalonado) y adentro se dibuja `_tablero` (los tres
  renglones `grow-x` escalonados .12 s).
- **`ejecuta`** (grafico, `at=[t_codex, t_ejecuta, t_golpe2]`). La misma terminal a lienzo
  (≈980×1100). Desde t=0 el tablero cae del globo al piso del cuerpo (`drop-in`); el
  cangrejo `piensa` queda chico arriba a la izquierda. En at[0] entra el obrero
  `caja-herramientas` desde la izquierda (`glide-x`) y se planta junto al tablero. En at[1]
  pasa a `martillo` y el primer golpe: el tablero `punch` y se transforma a medias en
  `_bloque` (crossfade). En at[2] el segundo golpe: el bloque queda entero, `stamp`, con
  `TK.GLOW`. `at[2]` lo pone el plan ~0.32 s después de at[1].
- **`fusion`** (partida, `at=[t_dos, t_viven, t_dentro]`). Arriba, sobre el suelo oscuro,
  dos mosaicos (150 px): `claude` y `openai` (Codex). En at[0] entran uno desde cada borde
  (`glide-x` desde ±420 px). En at[1] se tocan en el centro y se FUSIONAN: los dos se
  apagan y en su lugar `stamp` el `fusionado` (las dos mitades juntas), con una pastilla
  debajo con el glifo de un enchufe (sin texto). En at[2] el fusionado se encoge (×.55) y
  baja (`cursor-to` y +220) hacia la barra de plugins de la terminal, que se ve abajo de la
  banda (solo su franja superior + la barra, como si la ventana asomara).
- **`casa`** (grafico, `at=[t_tu, t_claude]`). La terminal a lienzo. En at[0] se abre
  (`rise-in` desde ×.92) y el fusionado (ya chico) se posa en el slot de la barra de
  plugins (`stamp`). En at[1] el mosaico queda encendido (`TK.GLOW` vía `fade-to` de una
  capa de brillo) y el cuerpo se parte en dos renglones con un hairline: arriba el
  cangrejo `saluda` (`chip-in`), abajo el obrero `caja-herramientas` (`chip-in` +.15 s).
  El logo de la cabecera entra en at[1] (`logo_at=at[1]`).

### 2. `plan_medidor(cid, variant, at, lienzo=False, fondo="comic")`

- **`vacia`** (partida, `at=[t_sin, t_plan, t_claude]`). Chrome desde t=0: `_medidor` lleno
  al 100 %. En at[0] el relleno se vacía de derecha a izquierda hasta el 18 % en 1.0 s
  (`power2.in`) y el número baja 100 → 18 (`count-roll`, sufijo «%»). En at[1] debajo se
  dibuja la tarjeta del plan (`surface`, radio `md`): «Plan Pro» Inter 800 34 px y
  «20 US$/mes» Inter 600 26 px `text2` (`type-word`), SIN logo. En at[2] el logo `claude`
  (40 px) entra en la tarjeta y el cangrejo `encogido` (170 px) entra al lado del medidor
  (`chip-in`) y se aplasta un poco más (`punch` ×.96 en Y en su hijo).
- **`calendario`** (grafico, `at=[t_fin, t_mes]`). Un calendario de bloque (hoja 420×480,
  cabecera `accent` con anillas, número del día en Inter 900 220 px). En at[0] las hojas
  pasan rápido: el número sube 1 → 15 (`count-roll` con `power3.out`, así frena) y cada
  pocas hojas una hoja se va volando (3 hojas, `rot-to` + y, escalonadas). En at[1] frena en
  15 con el número resaltado (`stamp`, aro `alert`), y abajo el mismo `_medidor` (en 18 %)
  llega a 0 con un golpe: 8 cuadraditos de polvo (`P['text2']`) que salen en abanico
  (posiciones deterministas).

### 3. `cuenta_chatgpt(cid, variant, at, lienzo=True, fondo=...)`

La **tarjeta de cuenta** (`_cuenta`): 440×200, look de ChatGPT modo oscuro
(`BRANDS["chatgpt"]`): avatar circular genérico, el logo `openai` (entra en su palabra) y el
nombre «ChatGPT» (`type-word` en su palabra), y un **puerto** a la izquierda (donde se
enchufa el cable). El **cable**: un `path` SVG grueso (10 px, `text`) desde el cinturón del
obrero; la luz que corre es un segundo trazo encima, `accent_hi`, con `stroke-dasharray`
preparado en t=0 y animado.

- **`enchufe`** (`fondo="claro"`, `at=[t_codex, t_trabaja, t_cuenta, t_chatgpt]`). A la
  derecha un `_bloque` a medio construir. En at[0] entra el obrero `camina` → planta
  `caja-herramientas`; su cable cuelga flojo hasta un medidor chico en 0 % (gris). En at[1]
  el cable se estira hacia la derecha (el path flojo se apaga y se dibuja con `draw` un path
  tenso que sube hacia donde va a estar la tarjeta). En at[2] la tarjeta se dibuja
  (`rise-in`, sin logo ni nombre) y el extremo del cable entra al puerto con un `click`. En
  at[3] `stamp` del logo + «ChatGPT» tecleado, y la luz empieza a correr por el cable hacia
  el bloque (dashoffset en bucle hasta el final del visual); el bloque gana un renglón.
- **`conectada`** (`fondo="oscuro"`, `at=[t_tu, t_chatgpt]`). Desde t=0, a la izquierda, la
  lista de chequeo de `instalacion/chequeo` en chico (3 tildes y el 4.º ítem girando) y el
  contador «3/4» arriba a la derecha. En at[0] el 4.º ítem deja de girar y se tilda. En at[1]
  la tarjeta (ya con logo y nombre: se nombró antes) sube al centro (`rise-in` y −40) con
  una insignia «Conectado» (punto `go` + texto) y un resplandor detrás (`TK.GLOW` en
  `paleta("oscuro")`); el cable del obrero (abajo a la izquierda, `caja-herramientas`) queda
  corriendo luz; el contador `count-roll` 3 → 4.

### 4. `instalacion(cid, variant, at, lienzo=False, fondo="claro")`

**Siempre la misma `_terminal`** con, en el cuerpo, una lista de **cuatro renglones** de
comando (slots de 64 px con borde discontinuo `cc.line` mientras están vacíos) y un
**contador «n/4»** en mono 700 30 px arriba a la derecha del cuerpo. Un renglón lleno lleva
`_comando` borroso y, si ya pasó, una tilde `cc.ok` a la derecha. Parámetro común
**`hechos: int`** = cuántos renglones están llenos y tildados desde t=0 (lo que pasó en
visuales anteriores); el plan lo pasa.

- **`comandos`** (partida, `at=[t_claude, t_cuatro, t_comandos]`, `hechos=0`). En at[0] la
  terminal con su logo (`logo_at=at[0]`), cuerpo vacío. En at[1] se dibujan los cuatro slots
  vacíos uno debajo del otro (`chip-in` escalonado .1 s) y el contador «0/4». En at[2] en el
  primer renglón aparece `>` y el comando 1 entra barrido y borroso (`glide-x` −40 → 0).
- **`catalogo`** (grafico, `at=[t_suma, t_catalogo, t_openai]`, `hechos=0`; el renglón 1 ya
  tiene su comando borroso). La terminal abajo (≈980×560); desde el renglón 1 se despliega
  hacia arriba una **estantería**: panel `surface` 980×480 con 2 filas × 4 casillas. En
  at[0] la estantería se abre como acordeón (cada fila `rise-bar` desde abajo, escalonadas
  .12 s). En at[1] las 8 casillas se llenan de mosaicos de plugin genéricos (glifos de
  línea de `icons.py` sobre tonos deterministas, `chip-in` .07 s de escalón); uno de ellos,
  el 3.º, es el `fusionado` (vuelve a usarse en `plugin`). En at[2] el logo `openai` (56 px)
  `stamp` en la cabecera de la estantería, el contador `count-roll` 0 → 1 y el renglón 1
  gana su tilde.
- **`plugin`** (partida, `at=[t_instala, t_plugin]`, `hechos=1`). Arriba la estantería
  compacta (una fila de 4, el fusionado en la 3.ª casilla); abajo la terminal (renglones +
  la barra de plugins con su slot vacío). En at[0] el renglón 2 recibe su comando borroso y
  el fusionado se desprende de la estantería y viaja en arco hasta el slot de la barra
  (`cursor-to` en dos tramos: x/y con `power2.inOut`). En at[1] encaja (`stamp` + `TK.GLOW`),
  la estantería se pliega (`fade-to` 0 + scaleY .8 en su hijo), contador 1 → 2, tilde en el
  renglón 2.
- **`recarga`** (grafico, `at=[t_recarga, t_comandos, t_nuevos]`, `hechos=2`). Sobre la
  terminal se abre el **menú de comandos de barra** (como el autocompletado de Claude Code:
  panel `cc.surface`, renglones de 52 px con `/xxx` borroso + una barra de descripción). En
  at[0] la lista gira como un rodillo: el contenido sube 6 renglones en .6 s y vuelve
  (`cursor-to` en un hijo), y el renglón 3 de la terminal recibe su comando borroso. En at[1]
  frena y entran arriba tres renglones nuevos con un pop (`chip-in` .12 s), cada uno con el
  logo `openai` chico como ícono y el texto borroso. En at[2] los tres se resaltan
  (`fade-to` de un fondo `cc.accent` al 22 %), contador 2 → 3, tilde en el renglón 3.
- **`chequeo`** (partida, `at=[t_chequea, t_todo, t_bien]`, `hechos=3`). En at[0] el renglón
  4 recibe su comando borroso y debajo baja (`drop-in`) un panel de verificación de cuatro
  ítems: «Plugin», «Comandos», «Codex», «Cuenta» (Inter 600 26 px `cc.text`), cada uno con
  un círculo a la izquierda; el primero se tilda (`draw` de la tilde `cc.ok`). En at[1] se
  tildan el 2 y el 3 (+.25 s). En at[2] el 4 queda con un spinner girando (`rot-to` 0 → 720°
  lineal hasta el final del visual) y todo lo demás en verde.
- **`enfoque`** (partida, CLÍMAX, `at=[t_paso, t_comandos, t_exactos]`, `hechos=0`). La
  terminal sin contador ni tildes, con los cuatro renglones. En at[0] los cuatro comandos
  entran borrosos (`chip-in` escalonado .1 s). En at[1] una onda de luz (franja con
  degradado `cc.accent` a transparente, 980×90) recorre los renglones de arriba a abajo
  (`cursor-to` y). En at[2] cada renglón entra en foco uno después del otro, .22 s de
  escalón: `fade-to` de la copia borrosa a 0 y de la nítida a 1. Es la única vez que se
  leen: comprobar con `text_px` que el comando 1 cabe en el ancho del renglón a 24 px; si
  no, bajar a 22.

### 5. `error_trabado(cid, variant, at, lienzo=..., fondo=...)`

- **`traba`** (partida, `fondo="comic"`, `at=[t_comando, t_errores, t_trabajados]`). Una
  `_terminal` baja (solo cuerpo de un renglón + campo, ≈980×260) abajo de la banda y
  `_barra_trabada` arriba, sin la tarjeta. En at[0] el renglón recibe `/codex:rescue`
  borroso. En at[1] la tarjeta de error baja desde arriba (`drop-in`). En at[2] se encaja de
  costado en el borde del relleno (`cursor-to` x/y + `rot-to` −8°) y la barra queda
  vibrando (`jitter` sobre la barra hasta el final; amplitud 3 px; ojo con la trampa de
  `jitter` que deja x en 0).
- **`lampara`** (grafico, `fondo="oscuro"`, `at=[t_investiga, t_causa, t_arregla]`). A la
  derecha una **traza**: 14 renglones de código en mono (barras de ancho determinista con
  algún token legible tipo `at login()` en `text2`), en una cinta que sube despacio todo el
  visual. A la izquierda el obrero `linterna`. En at[0] un cono de luz (degradado radial
  `rgba(accent_hi, .35)` → transparente, en forma de cuña) sale de la linterna y barre la
  traza de arriba a abajo; los renglones se iluminan a su paso (`fade-to` .4 → 1 escalonado).
  En at[1] un solo renglón (el 9.º) se pone `alert` (fondo `rgba(alert,.25)` + texto
  `alert`) y el resto baja a .25. En at[2] el obrero pasa a `martillo` y golpea; la tarjeta
  de error (la misma de `_barra_trabada`, chica junto al renglón) hace `flip-out` y vuelve
  con `flip-in` en `go` con una tilde, y una `_barra_trabada` chica abajo se suelta: el
  relleno llega al 100 % (`grow-x`) en `go`.
- **`destraba`** (partida, `fondo="comic"`, `at=[t_destraba, t_errores]`). LA MISMA
  `_barra_trabada` del `traba`, con la tarjeta ya encajada y la barra vibrando desde t=0.
  El obrero `tira` a la derecha, con su soga llegando a la tarjeta. En at[0] tira: la tarjeta
  sale despedida hacia la derecha (`cursor-to` x +380 + `rot-to` 160°) y la barra corre al
  100 % (`grow-x`, `power3.out`) y se pone `go`. En at[1] la tarjeta termina de salir de
  cuadro girando y el obrero se endereza (`fade-to` a `caja-herramientas`).

### 6. `revision_diff(cid, variant, at, lienzo=..., fondo="claro")`

**Panel de diferencias**: tarjeta `surface` con pestaña de archivo, canalón con números de
línea y renglones de código como barras. Renglones `+` (fondo `rgba(go,.16)`) y `−`
(`rgba(alert,.14)`), patrón determinista.

- **`revisa`** (partida, `at=[t_revisa, t_cambios, t_modificar, t_nada]`). Chrome desde t=0:
  el panel con los renglones en neutro, el botón «Guardar» abajo a la derecha y el contador
  «Modificados: 0» abajo a la izquierda (Inter 700 26 px). En at[0] entra una lupa grande
  (glifo SVG de línea 120 px, `text`) y empieza a bajar por el panel (`cursor-to` y hasta el
  final del visual). En at[1] los renglones se tiñen de verde/rojo a su paso (escalonado
  .12 s) y brotan tres notas al margen (globos `accent_soft` con dos barras, `chip-in`). En
  at[2] un candado (glifo) se cierra sobre «Guardar» (`stamp`) y el botón baja a .45. En
  at[3] el 0 del contador tiembla (`jitter` corto, 0.4 s).
- **`grandes`** (grafico, `at=[t_grandes, t_cambios]`). El panel gigante (980×1000) con 40
  renglones `+`/`−` en una cinta que baja sin parar (`cursor-to` y −1600 lineal hasta el
  final). A la izquierda, delante del panel, el obrero `carga` (330 px). En at[0] la cinta
  arranca y el obrero entra desde abajo (`rise-in`). En at[1] el contador «archivos
  tocados» (arriba, Inter 900 64 px) sube 3 → 148 (`count-roll`, `power2.out`).

### 7. `bloque_cuestiona(cid, at, lienzo=True, fondo="claro")`

`at=[t_cuestiona, t_solucion]`. El `_bloque` del gancho al centro, grande (×1.6). En at[0]
el obrero `camina` lo rodea: pasa por detrás (×.86, z-index bajo, de derecha a izquierda) y
vuelve por delante (×1, de izquierda a derecha) — dos `cursor-to` sobre el wrapper y un
cambio de `z-index` instantáneo; brotan tres «?» (glifo SVG, Inter 900 no: dibujados) en
`accent_hi` alrededor del bloque, uno por medio-recorrido (`chip-in`). En at[1] el obrero pasa
a `martillo` y golpea una cara: la junta del frente se enciende y las dos mitades se
separan unos grados (`rot-to` ±6° + x ±14 en `-izq` y `-der`), dejando ver la junta mal
pegada.

### 8. `claude_md(cid, variant, at, lienzo=..., fondo="claro")`

**El archivo CLAUDE.md**: la misma `_terminal` NO; es un editor de archivo: tarjeta
`surface` con una pestaña «CLAUDE.md» (Inter 600 24 px; ya se nombró en el beat anterior, va
desde t=0) y un cuerpo de **dos renglones altos** separados por hairline: renglón 1 = el
lugar del cangrejo (con el logo `claude` a la izquierda cuando corresponda), renglón 2 = el
del obrero (logo `openai`). Mismo dibujo en las cuatro variantes.

- **`claude`** (grafico, `at=[t_claude, t_planea, t_decide, t_controla, t_vuelve]`). El
  archivo ocupa el lienzo; renglón 2 apagado (.35). En at[0] el cangrejo `saluda` se sienta
  en el renglón 1 (`chip-in`) y entra el logo `claude`. En at[1] pasa a `piensa` y a su lado
  se despliega `_tablero` (renglones `grow-x`). En at[2] aparecen dos tarjetas de opción
  (`chip-in`) y el cangrejo pasa a `sello`: un sello (círculo `go` con tilde) `stamp` sobre
  la segunda, la otra baja a .4. En at[3] pasa a `lupa` y la lupa del cangrejo se desliza
  (`glide-x` del wrapper +60). En at[4] una caja (rectángulo cartón: `mix(accent, warn, .5)`
  con cinta) sube desde el renglón 2 y queda delante del cangrejo, con la tapa abierta
  (`rot-to` de la tapa).
- **`codex`** (partida, `at=[t_codex, t_construye]`). El archivo compacto; renglón 1 con el
  cangrejo `saluda` apagado (.35). En at[0] el renglón 2 se enciende (`fade-to` 1) y entra
  el logo `openai`. En at[1] el obrero `martillo` aparece y apila 4 bloquecitos (`drop-in`
  escalonado .18 s, uno sobre otro).
- **`vuelve`** (partida, `at=[t_trabajo, t_vuelve, t_claude]`). Los dos renglones encendidos;
  en el 2, una tarjeta de tarea (180×100, `surface2`, dos barras) junto al obrero
  `caja-herramientas`. En at[0] la tarjeta se despega (`punch` + sombra). En at[1] sube en
  arco al renglón 1 (`cursor-to` en dos tramos). En at[2] aterriza delante del cangrejo, que
  pasa de `lupa` a `caja` (la sostiene en alto), y el logo `claude` hace `punch`.
- **`reparto`** (grafico, `at=[t_reparto, t_pegar, t_claudemd]`). El archivo arriba. En
  at[0] los dos renglones se despegan y se condensan en un **bloque de texto** (tarjeta
  `surface2` 980×300, mono 22 px `text`), con el reparto escrito en dos líneas:
  `Claude: planea, decide y revisa lo que vuelve.` /
  `Codex: construye, cambios grandes, destraba errores. 2 fallas → vuelve a Claude.`
  (entran con `type-word`), y un botón «Copiar» (glifo de dos hojas + texto) a su derecha. En
  at[1] el botón se aprieta solo (`click`), el bloque se duplica (una copia `chip-in` encima
  desplazada) y la copia cae (`drop-in` y +360) dentro de un archivo vacío abajo (tarjeta
  con pestaña VACÍA). En at[2] la pestaña de ese archivo se escribe «CLAUDE.md»
  (`type-word`) y el archivo queda con una tilde `go` en la pestaña.

### 9. `marcador_fallas(cid, at, lienzo=True, fondo="comic")`

`at=[t_falla, t_2, t_veces]`. El `_bloque` a la izquierda con el obrero `martillo` al lado; a
la derecha `_marcador` de dos casillas vacías. En at[0] el bloque se DERRUMBA: el frente y
la tapa se separan en 4 pedazos que caen (`cursor-to` y +120 con `rot-to` deterministas) y
una cruz (`alert`, dos trazos `draw`) se estampa en la casilla 1. Entre at[0]+.45 y at[1] el
bloque se vuelve a armar (los pedazos vuelven a su sitio). En at[1] el MISMO derrumbe
(mismos valores, copiado) y la cruz 2. En at[2] las dos cruces laten juntas (`punch`) y el
borde del marcador pasa a sólido `alert`.

## Verificación que se pide

1. Tests en `tests/test_mockups_codex.py`: cada componente y cada variante devuelve
   `(css, html, anims)`; variante/fondo/pose mal escritos → `ValueError`; `at` con largo
   equivocado → `ValueError`; nada de los textos que se DICEN («ChatGPT», «CLAUDE.md» en
   `reparto`, el logo) está en el HTML antes de su `at` (tecleado o vacío); `assets_de`
   devuelve exactamente las imágenes que el html referencia; `tokens.paleta` no muta `C`.
2. La suite entera pasa: `.venv/bin/python -m pytest -q`.
3. Un plan de prueba mínimo NO hace falta: el plan real lo escribo yo
   (`videos/8/armar-plan.py`). Sí hace falta que `build-composition.py` importe el módulo y
   despache los 9 componentes.
4. En el reporte: qué gestos usaste por componente, cualquier gesto nuevo, y cualquier
   excepción agregada a los tests de paleta con su motivo.
