# Pieza 6 — componentes nuevos (chat de ChatGPT, resultados de imagen)

Pieza: «Escribes una palabra al lado de la foto y te la devuelve convertida». Paleta `oscuro`,
layout `formatos`. Brief de plan-edicion: `Marketing/Reels/plan-edicion/planes/2026-09-29-6.md`
(el brief habla de un zapato: **el objeto real es un Rolex Datejust**, `original.jpg`). Se
edita en conversación con Ezequiel (no desde el dashboard).

**Lo que pidió Ezequiel (2026-10-07):** que se vea el chat de ChatGPT escribiendo cada
comando y el resultado. Look **real de ChatGPT** (modo oscuro, su campo de mensaje, su botón
de enviar, la imagen de la respuesta revelándose como cuando genera). En la palabra del
resultado, la imagen salta a pantalla completa. Cuatro comandos se ven (`/blueprint`,
`/explodedview`, `/xray`, `/handwritten`); el quinto (`/stickynotes`) solo aparece en la lista
del CTA, borroso y con candado.

**La foto del reloj es el objeto que cruza el video.** Siempre la misma, adjunta en el campo
del chat; cada comando la devuelve convertida. Los cuatro chats tienen que rimar: misma
geometría, mismo campo, misma miniatura adjunta; lo único que cambia es el comando tecleado y
la imagen que vuelve.

## Dónde vive

- Módulo nuevo `.claude/skills/video-tech-premium/scripts/mockups_chatgpt.py` (`scripts/` es un
  enlace a esa carpeta). Reutiliza de `mockups_reels` (`_host`, `_need_at`, `_shared_css`,
  `_glifo`) y de `mockups_plugins` (`_need_at` con dominio y orden) lo que sirva, y de
  `mockups` (`text_px`, `_cursor`, `_cursor_css`).
- `build-composition.py`: `import mockups_chatgpt` y una entrada por componente en el
  diccionario de despacho de `build_visuals`.
- Todos los tiempos van en **`at: list`** (offsets del visual; el compilador los remapea con
  `absolute_times`). Ninguna otra clave de tiempo.
- Tests nuevos en `tests/test_mockups_chatgpt.py`.

## Contrato

**El mismo de `docs/superpowers/specs/2026-10-05-pieza-4-componentes.md`, sección «Contrato»,
sin excepciones** (léela entera antes de escribir código): `(css, html, anims)` con selectores
RELATIVOS; nada entra antes de su palabra y eso es sobre el DOM (texto tecleado → `type-word`
sobre un span vacío + `caret-off`); el CHROME está desde t=0; centrar con flex; sin
`back.out`; dos tweens sobre la misma propiedad → el recorrido en un HIJO; ids `{cid}-…`;
`logos.mark(slug, px, uid=f"{cid}-…")` SIEMPRE con `uid`; sin emojis; determinista; variante
mal escrita → `ValueError`; texto en pantalla SOLO como interfaz.

Las dos geometrías (`lienzo=False` partida: banda 1080×960, alto máx 760, ancho máx 980;
`lienzo=True` grafico: lienzo entero 1080×1920 con `cap_top` ~1400) son las de esa spec.

**Excepción de color, a sabiendas:** la interfaz de ChatGPT es interfaz LITERAL (como el
semáforo de macOS o el cursor): sus colores no salen de la paleta de la marca. Van en **un
solo lugar**, `tokens.BRANDS["chatgpt"]` (junto a Excel y WhatsApp), con estos valores del
modo oscuro real, y el componente los lee de ahí — nunca un hex suelto en el módulo:

| clave | valor | uso |
| --- | --- | --- |
| `bg` | `#212121` | fondo de la ventana del chat |
| `surface` | `#303030` | campo de mensaje y burbuja del usuario |
| `line` | `#3a3a3a` | hairline del campo |
| `text` | `#ececec` | texto |
| `text2` | `#afafaf` | placeholder, rótulos secundarios |
| `send_bg` | `#ececec` | botón de enviar activo (círculo) |
| `send_fg` | `#0d0d0d` | flecha del botón activo |
| `send_off` | `#676767` | botón de enviar sin texto |

Si `test_paletas_consumidores.py` se queja de estos valores, se agrega la excepción en el test
con un comentario que diga por qué (interfaz literal de un tercero), igual que el semáforo.

**Fallos que Codex ya tuvo en las piezas 4 y 5 y NO se pueden repetir** (los vigilo en la
revisión): radios sin `px` en el CSS; `!important` que bloquea un tween; `jitter` que deja `x`
en 0; un `fromTo` sin `immediateRender:false` cuando el elemento ya tiene un estado declarado
antes; selectores ya prefijados.

## Las imágenes

En `assets/imagenes-6/`: `original.jpg` (736×1387), `blueprint.jpg` (1536×1024, APAISADA),
`explodedview.jpg`, `xray.jpg`, `handwritten.jpg` (1024×1536) y `stickynotes.jpg` (540×720).
Claves: `original`, `blueprint`, `explodedview`, `xray`, `handwritten`, `stickynotes`; una
clave que no existe → `ValueError`.

**No se embeben como data URI** (son 3 MB entre todas y se repiten en una docena de visuales).
El componente las referencia con ruta relativa `imagenes-6/<clave>.jpg`, y
`build-composition.py` aprende un campo genérico nuevo: **un visual puede declarar
`"assets": ["imagenes-6/blueprint.jpg", …]`** y esas rutas (relativas a `assets/`) se suman
al conjunto que ya se copia a `public/` (el mismo `assets.add` que usan `image` y
`screen-video`). Un asset declarado que no existe en disco → la compilación falla con el
nombre. Para que el plan no tenga que adivinar la lista, el módulo expone
**`mockups_chatgpt.assets_de(fn_name, kw) -> list[str]`**, que devuelve las rutas que usará
esa llamada.

## Primitivas compartidas (privadas)

- **`_ventana(cid, w, h)`** — la ventana de ChatGPT: rectángulo `BRANDS.chatgpt.bg`, radio
  `xl`, hairline `line`, sombra `TK.SHADOW`. Cabecera de 76 px: el logo `openai` a 34 px
  (`logos.mark("openai", 34, uid=…)`, en `text`) + «ChatGPT» Inter 600 28 px + un chevron
  hacia abajo en `text2`. Sin nombre de usuario, sin historial lateral.
- **`_campo(cid, adjunto=True)`** — el campo de mensaje real: píldora `surface` de ~900×128
  (alto que crezca si hace falta para la miniatura), radio 34 px. Arriba a la izquierda, dentro
  del campo, la **miniatura adjunta** de `original` (88×88, radio 14, `object-fit:cover`) con
  su pequeña × circular. Debajo, la línea de texto: un `+` a la izquierda (glifo `text2`), el
  span del texto (vacío) con el placeholder «Pregunta lo que quieras» en `text2` que se apaga
  con la PRIMERA letra, y a la derecha el botón de enviar: círculo de 52 px `send_off` con la
  flecha hacia arriba, que pasa a `send_bg`/`send_fg` cuando hay texto (`send-on` o
  `color-to`). Comando en **Inter 500 32 px** (así se ve en ChatGPT; no mono).
- **`_burbuja_usuario(cid, comando)`** — lo que queda en la conversación al enviar: la
  miniatura de `original` (160×160, radio 18) arriba y debajo la burbuja `surface` con el
  comando, alineadas a la derecha, como en ChatGPT.
- **`_respuesta(cid, clave)`** — la respuesta del asistente, alineada a la izquierda: el
  rótulo «Creando imagen» en `text2` con un brillo que lo recorre (shimmer: un degradado
  que se desplaza con `x` en un hijo con `overflow:hidden`), y debajo el marco de la imagen
  (radio 20) con la imagen de `clave` revelándose **como en ChatGPT: de arriba hacia abajo,
  la parte ya revelada nítida y el resto borroso**. Se arma con dos capas de la misma imagen:
  abajo la copia con `filter: blur(28px)` y un velo, encima la nítida dentro de un contenedor
  cuyo alto (o una máscara que baja con `y`) crece de 0 al 100 % — transform, nunca `height`
  (§6); si hace falta un gesto nuevo (por ejemplo `wipe-down` con `clip-path: inset()`),
  se agrega al emisor de `build-composition.py` con su test. El rótulo se apaga cuando la
  imagen termina de revelarse.

## Componentes

### 1. `chatgpt_chat(cid, variant, at, comando="", resultado=None, previo=None, lienzo=False)`

La ventana de ChatGPT dentro de la banda de arriba (partida): ~980×740.

- **`variant="oculto"`** (gancho, «Estos códigos ocultos»), `at=[t_estos, t_ocultos]`: la
  ventana con el campo y la foto adjunta desde el primer cuadro; en el campo, el comando a
  medio escribir (`comando[:k]`, p. ej. «/blue») TAPADO por una banda negra (`#0d0d0d`,
  radio 8, que cubre justo el texto). En `t_ocultos` la banda se descorre hacia la derecha
  (`glide-x` o `grow-x` en un hijo) y deja ver el texto con su cursor parpadeando. El texto a
  medio escribir puede estar en el DOM desde t=0: está tapado y el gancho lo enseña así.
  Sin respuesta, sin burbuja.
- **`variant="enviar"`** (cada comando), `at=[t_foco, t_tecleo, t_envio, t_respuesta,
  t_revelado_fin]`:
  - `t_foco`: el campo se enciende (hairline `text2` → un poco más claro) y, si
    `cursor=True` (kw opcional, por defecto False), el cursor grande entra y hace clic en el
    campo (`cursor-enter` + `click`).
  - `t_tecleo` → `t_envio`: el comando se teclea letra por letra (`type-word`; su duración es
    `t_envio − t_tecleo`, así el plan decide la velocidad). Con `t_tecleo == t_envio` el
    comando entra **entero de un golpe** (el corte de patrón de «Y con este»). El
    placeholder se apaga con la primera letra; el botón de enviar se activa con ella.
  - `t_envio`: clic de envío: el botón hace un pulso (`scale-pop`), el campo se vacía (texto
    y miniatura salen) y en la conversación aparece la burbuja del usuario (miniatura +
    comando) desde abajo (`rise-in`).
  - `t_respuesta`: aparece la respuesta con «Creando imagen» y la imagen de `resultado`
    empieza a revelarse; termina de revelarse en `t_revelado_fin`.
  - `previo` (clave opcional): la imagen de la respuesta ANTERIOR asomando arriba de la
    conversación, cortada por el borde superior (se ve su tercio de abajo, apagada al 55 %),
    para que se lea que es la misma conversación que sigue. Está desde t=0 (es historial).
  - La conversación tiene que caber: burbuja del usuario arriba, respuesta debajo; el marco de
    la imagen de la respuesta, ~420 px de ancho y alto según la proporción de la imagen
    (`blueprint` apaisada, las demás 2:3), recortado por el borde inferior de la zona de
    conversación si no entra entero — el campo de mensaje siempre visible abajo.
- `variant` desconocida → `ValueError`; `enviar` sin `comando` o sin `resultado` → `ValueError`.

### 2. `imagen_resultado(cid, clave, at, comando="", revelado="barrido", lienzo=True)`

La imagen a pantalla completa (grafico), `at=[t_entrada, t_gesto]`.

- **Encaje:** las verticales (2:3) a sangre con `object-fit: cover` sobre 1080×1920. La
  `blueprint` (apaisada) NO a sangre: de fondo, la misma imagen a `cover` con
  `blur(36px)` y un velo `shade_a(.55)`; encima, la imagen entera a todo el ancho (1080×720)
  centrada hacia y≈700, con hairline y sombra. Todo lo demás con `cam-push` lento
  (1.00 → 1.05) durante el visual.
- **`t_entrada`:** la imagen entra continuando el revelado del chat: nítida desde arriba con
  un último tramo borroso abajo que se resuelve en ~0.30 s (o `blur-to` 14px → 0 sobre la
  capa entera). Corte seco, sin fundido desde negro.
- **Etiqueta del comando** (si `comando`): una píldora estilo ChatGPT (`surface` 88 %, texto
  `text`, Inter 500 30 px) arriba, centrada en y≈150, con el comando («/blueprint»). Es
  interfaz (es lo que se tecleó), y es lo que hace que la pieza se entienda sin audio. Entra
  con la imagen.
- **`t_gesto`, según `revelado`:**
  - `"barrido"`: una franja de luz diagonal (degradado blanco al 0→22 %→0, ancho ~260 px,
    `mix-blend-mode: screen`) cruza la imagen de izquierda a derecha en 0.6 s.
  - `"escaneo"` (para `xray`): una línea de escaneo cian con glow sube de abajo hacia arriba
    en 0.7 s (el color sale de un token de señal o de un derivado; si no hay cian en la
    paleta, `text` con glow).
  - `"trazo"` (para `handwritten`): un borde de «tinta» recorre la imagen — una máscara
    `surface` de la paleta que se retira de izquierda a derecha con `glide-x`, dejando ver
    la imagen como si se dibujara, en 0.7 s, empezando en `t_entrada` (en ese caso `t_gesto`
    marca el final).
  - `"despiece"` (para `explodedview`): la imagen entra partida en 3 franjas horizontales
    ligeramente separadas en y (±40 px) que se acomodan en su sitio en 0.45 s.
  - Desconocido → `ValueError`.

### 3. `parpadeo_estados(cid, at, claves=("blueprint", "explodedview", "xray"), lienzo=True)`

El corte de patrón del gancho («cambian tu imagen por completo»), a pantalla completa,
`at=[t_imagen, t_completo]`.

- Desde t=0: `original` a sangre (`cover`), quieta.
- `t_imagen`: un barrido de luz (el mismo de `imagen_resultado`) la cruza.
- `t_completo`: tres estados en un parpadeo, cada uno ~0.14 s, cortes secos con un destello
  blanco de 2 frames entre ellos (un velo `#fff` al 35 % que sube y baja): `claves[0]`,
  `claves[1]`, `claves[2]` y **frena de golpe en `original`**, que queda quieta hasta el
  final del visual. La `blueprint` en este parpadeo va a `cover` (se recorta, da igual: dura
  0.14 s).

### 4. `lista_codigos(cid, at, lienzo=False)`

La lista del CTA en la banda de arriba, `at=[t_todos, t_codigos, t_ocultos, t_lista]`.

- Cinco renglones de ~124 px dentro de un ancho de 900: a la izquierda la miniatura del
  resultado (104×104, radio 14, `cover`), a la derecha el comando en **JetBrains Mono 700
  34 px** sobre una píldora `surface2`.
- Renglones 1–4: `blueprint`, `explodedview`, `xray`, `handwritten`. En `t_todos` las cuatro
  miniaturas bajan a su sitio escalonadas (0.08 s), de arriba abajo (`drop-in`). En
  `t_codigos` se teclean sus comandos, escalonados (cada uno con `type-word` sobre un span
  vacío).
- Renglón 5, en `t_ocultos`: la miniatura de `stickynotes` con `blur(10px)` y un velo, y en
  vez del comando **tres barras grises redondeadas** (`rgba(text2,.30)`) — el texto real del
  quinto comando NO va en el DOM — y a la derecha un candado cerrado (glifo de línea en
  `currentColor`, 40 px, `text2`) que entra con un `stamp`.
- `t_lista`: un borde (`TK.LINE_HI` → acento) se dibuja alrededor de los cinco renglones
  (`draw` sobre un `<rect>` SVG preparado en t=0) y los junta en una tarjeta `surface`.

## Tests (`tests/test_mockups_chatgpt.py`)

- Cada componente devuelve `(css, html, anims)`, selectores relativos, ids con prefijo `cid`.
- Nada antes de su palabra: en `enviar`, el comando no está en el HTML (span vacío) y su
  `type-word` arranca en `t_tecleo`; en `lista_codigos` ningún comando de 1–4 está en el HTML
  y **`/stickynotes` no aparece en ningún lado del HTML ni de las anims**.
- `enviar` con `t_tecleo == t_envio` no emite tecleo letra por letra (entra de un golpe).
- Variantes, claves y `revelado` desconocidos → `ValueError`; `at` de largo incorrecto →
  `ValueError`.
- `assets_de` devuelve exactamente las imágenes que referencia el HTML.
- `build-composition.py` con un visual que declara un asset inexistente falla con su nombre
  (camino de fallo del gate).
- Ningún hex escrito a mano en `mockups_chatgpt.py`: los colores de ChatGPT salen de
  `tokens.BRANDS["chatgpt"]`.
- La suite completa sigue en verde (`.venv/bin/python -m pytest -q`).

## Hoja de muestra

Al terminar, un HTML estático en `out/pieza-6-muestra/index.html` con cada componente en su
estado FINAL (todas las anims aplicadas) en su geometría real, para revisarlo a ojo:
`chatgpt_chat` oculto y enviar (con y sin `previo`), `imagen_resultado` con las cuatro
claves, `parpadeo_estados` y `lista_codigos`.
