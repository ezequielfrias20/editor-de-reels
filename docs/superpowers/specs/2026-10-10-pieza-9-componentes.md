# Pieza 9 — componentes nuevos (DaVinci Resolve + MCP)

Pieza: «DaVinci Resolve abrió su MCP: Claude te edita los videos». Paleta `claro`, layout
`formatos`. Brief de plan-edicion: `Marketing/Reels/plan-edicion/planes/2026-10-09-1009.md`
(léelo: dice qué hace cada momento y por qué). Se edita en conversación con Ezequiel.

**Decisiones de Ezequiel (2026-10-10):**
- **DaVinci Resolve se recrea animado** (no hay grabaciones): la ventana real de DaVinci
  (gris casi negro, línea de tiempo con pistas V/A, visor, barra de páginas abajo, ruedas de
  color, osciloscopio, árbol de nodos). Es la herramienta que hay que MOSTRAR: que se
  reconozca DaVinci y que todo pase adentro de ella.
- **Las miniaturas de los clips salen de su propio video** (`assets/imagenes-9/toma-*.jpg`):
  la línea de tiempo edita su reel.
- El cangrejo de Claude en 4 poses nuevas de Higgsfield, ya recortadas
  (`assets/personajes-9/`), más las de la pieza 8 si hacen falta.
- El plano que «Claude genera» es una imagen de Higgsfield (`assets/imagenes-9/plano.jpg`):
  EL MISMO archivo pasa de ruido/borroso a nítido.
- **Los pedidos son ilegibles (borrosos) todo el video y se leen nítidos solo en el clímax**
  (`dv_guia` variante `pedidos`), igual que los comandos de la pieza 8.

**El objeto que cruza el video es la ventana de DaVinci** (`_davinci`). Es SIEMPRE la misma
primitiva, con la misma barra de título, el mismo visor, la misma línea de tiempo y la misma
barra de páginas; en cada componente cambia lo que pasa dentro o se muestra un recorte de
ella (solo la línea de tiempo, o solo la página de color). Si dos componentes muestran la
ventana, tiene que leerse que es la misma.

## Dónde vive

- Módulo nuevo `.claude/skills/video-tech-premium/scripts/mockups_davinci.py` (`scripts/` es
  un enlace). Reutiliza de `mockups_codex`: `_suelo`, `_P`, `_svg`, `_check`, `_logo`,
  `_personaje` (generalízalo o copia su patrón para aceptar `personajes-9` además de
  `personajes-8`), `_wrap`, `_encender`, `_pose`. No dupliques lo que ya existe: impórtalo.
- `build-composition.py`: `import mockups_davinci` y una entrada por componente en el
  diccionario de despacho de `build_visuals` (junto a los de `mockups_codex`).
- Todos los tiempos van en **`at: list`** (offsets del visual; el compilador los remapea con
  `absolute_times`). Ninguna otra clave de tiempo.
- Tests nuevos en `tests/test_mockups_davinci.py`.

## Contrato

**El mismo de `docs/superpowers/specs/2026-10-05-pieza-4-componentes.md` («Contrato» y
«Las dos geometrías») y de `2026-10-09-pieza-8-componentes.md` («Contrato», «Gestos», «Los
fondos por escena»), sin excepciones.** Léelas enteras antes de escribir código.
Resumen: `(css, html, anims)` con selectores RELATIVOS; nada entra antes de su palabra y eso
es sobre el DOM; el CHROME está desde t=0; centrar con flex; sin `back.out`; dos tweens sobre
la misma propiedad → el recorrido en un HIJO; ids `{cid}-…`; `logos.mark(slug, px,
uid=f"{cid}-…")` SIEMPRE con `uid`; sin emojis; determinista; variante/fondo/pose mal escritos
→ `ValueError`; `at` con largo equivocado → `ValueError`; texto en pantalla SOLO como
interfaz. Geometrías: `lienzo=False` (partida) alto máx 760, ancho máx 980; `lienzo=True`
(grafico) alto máx 1180 (el subtítulo va debajo con `cap_top` 1400).

**Fallos que Codex ya tuvo y NO se pueden repetir** (los reviso uno por uno): radios sin
`px`; `!important` que bloquea un tween; `jitter` que deja `x` en 0; un `fromTo` sin
`immediateRender:false` cuando el elemento ya tiene un estado declarado; selectores ya
prefijados; una imagen embebida en vez de referenciada; `#{{cid}}` en f-strings y un
`.replace` que nunca casa; poner con `html-on` un innerHTML con números dentro de un SVG
(GSAP interpola los `d` desde 0) — para encender algo, `_encender` (span a opacidad 0 +
`fade-to`).

Gestos: solo los que ya existen en `emit_anim` (míralos en `build-composition.py` y respeta
sus firmas). Si de verdad falta uno, se agrega al emisor con su test en
`tests/test_motion_gestos.py` y se dice en el reporte. Cambio de pose = `fade-to` 0.01 s.

## Fondos (`fondo`)

`"claro" | "oscuro" | "comic"`, con `_suelo` de `mockups_codex` como primer hijo. La ventana
de DaVinci es interfaz LITERAL y es oscura en los tres fondos: sobre crema y terracota flota
como una ventana oscura con `TK.SHADOW`; sobre `oscuro` lleva además un resplandor
`accent` muy suave detrás (`paleta("oscuro")`). Lo que NO es la ventana (balanza, cables,
mosaicos, etiqueta de precio, burbujas, hoja de guía) sale de `P = _P(fondo)`.

## Interfaz literal de DaVinci Resolve

Sus colores no salen de la paleta: van en un solo lugar, **`tokens.BRANDS["davinci"]`**
(dict, como `claudecode`), y el módulo los lee de ahí, nunca un hex suelto. Excepción en
`test_paletas_consumidores.py` si hace falta, con comentario.

| clave | valor | uso |
| --- | --- | --- |
| `bg` | `#1B1B1E` | fondo de la ventana y de la línea de tiempo |
| `panel` | `#25252A` | paneles (visor, inspector, cabeceras de pista) |
| `panel2` | `#2F2F35` | barras, botones, pista vacía |
| `line` | `#3B3B42` | hairlines |
| `text` | `#D6D6DA` | texto |
| `text2` | `#8B8B93` | secundario, regla de tiempo |
| `video` | `#3F72AF` | clips de video (V1) |
| `video2` | `#7A5AA8` | clips de gráficos/títulos (pista V2) |
| `audio` | `#3E8A5E` | clips de audio |
| `music` | `#2F7D8C` | pista de música |
| `playhead` | `#E5484D` | el cabezal y su manija |
| `tc` | `#F2A93B` | timecode y página activa |
| `ok` | `#5FBF7A` | conectado, verificado |

## Imágenes (referenciadas, no embebidas)

- `personajes-9/cangrejo-<pose>.png`: `arrastra` (tira de un cabezal rojo vertical; el
  cabezal es parte de la imagen, a su derecha), `rueda` (gira una rueda de color con las dos
  pinzas), `asoma` (inclinado hacia adelante mirando abajo), `pinta` (pincel en alto). RGBA,
  pixel art: `image-rendering: pixelated`.
- `personajes-8/cangrejo-<pose>.png` (las de la pieza 8: `piensa`, `saluda`, `sello`,
  `lupa`, `caja`, `encogido`) por si hacen falta.
- `imagenes-9/toma-2.jpg`, `toma-12.jpg`, `toma-22.jpg`, `toma-38.jpg`: cuadros 9:16 de su
  video (360×640). `imagenes-9/plano.jpg`: el plano generado (608×1080, 9:16).

`mockups_davinci.assets_de(fn_name, kw) -> list[str]` devuelve exactamente las imágenes que
esa llamada referencia (mismo contrato que `mockups_codex.assets_de`).

## Logos

`davinciresolve`, `modelcontextprotocol`, `adobepremierepro`, `higgsfield` (nuevos, ya en
`assets/logos/` y `meta.json`), `claude`, `openai` (Codex se pinta con `openai`, como en la
pieza 8), `instagram`. Siempre por `logos.mark(..., uid=...)` y cada logo entra en la palabra
que nombra su herramienta (no antes).

## Los pedidos (texto exacto, en este orden)

```
1. Corrige el color de todos los clips: más contraste y la piel natural.
2. Arma un título animado con mi nombre al entrar cada sección.
3. Corta en multicámara siguiendo a quien habla.
4. Pon un whoosh en cada corte y un pop cuando aparezca un texto.
5. Ajusta la música para que los golpes caigan sobre los cortes.
6. Si falta un plano entre dos escenas, genéralo con Higgsfield y ponlo en el hueco.
```

Constante `PEDIDOS` en el módulo (Ezequiel puede cambiarlos: que salgan de un solo lugar).

## Primitivas compartidas (privadas)

- **`_davinci(cid, w, h, *, visor=None, pistas=..., pagina="edit", body_extra="")`** — LA
  ventana. Rectángulo `dv.bg`, radio `md`, hairline `dv.line`, sombra. Barra de título de
  36 px `dv.panel` con el semáforo macOS y, centrado, «DaVinci Resolve» en Inter 600 15 px
  `dv.text2` SOLO si se pasa `nombre=True` (el nombre se dice en el gancho; por defecto no
  va). Debajo, si `visor` es una imagen, el **visor**: panel `dv.panel` con la imagen 9:16
  centrada (`object-fit:cover`), un timecode `dv.tc` mono 18 px debajo (`00:00:12:04`,
  determinista) y los tres botones de transporte (glifos). Debajo, la **línea de tiempo**
  (`_timeline`). Abajo del todo, la **barra de páginas**: 7 glifos de línea simples (Media,
  Cut, Edit, Fusion, Color, Fairlight, Deliver) con su rótulo en Inter 500 12 px `dv.text2`;
  la `pagina` activa en `dv.tc`. Es interfaz: va desde t=0.
- **`_timeline(iid, w, h, pistas)`** — regla de tiempo arriba (marcas cada 40 px, tres
  timecodes mono 13 px `dv.text2`), cabeceras de pista a la izquierda (56 px, «V2», «V1»,
  «A1», «A2»… mono 14 px) y, por pista, sus clips: cada clip es un bloque con radio `3px`,
  borde superior más claro (`mix(color, #FFF, .25)` vía tokens), nombre-barra (barra
  `rgba(text,.35)`, no texto) y, en las pistas de video, la miniatura (`<img>` de una toma,
  recortada al alto de la pista, `object-fit:cover`, opacidad .85). Los clips de audio llevan
  una forma de onda SVG determinista (barras verticales simétricas). El **cabezal**
  (`{iid}-ph`): línea vertical 2 px `dv.playhead` de alto completo + manija de 14 px
  arriba; se mueve con `cursor-to` x en un hijo. `pistas` es una lista de pistas, cada una
  una lista de clips `(x, w, tipo, toma)`; ids `{iid}-c{pista}-{n}` para que los componentes
  los animen. Medidores de audio (`{iid}-vu`): dos barras verticales a la derecha que
  rebotan (`rise-bar` en bucle determinista) cuando el componente lo pide.
- **`_conector(iid, P, px=120)`** — EL conector del MCP: una pieza tipo enchufe (cuerpo
  redondeado `P.text` con dos patas, contorno `accent_hi` de 3 px) con el logo
  `modelcontextprotocol` en blanco/tinta centrado (el logo entra cuando lo pida el
  componente, no antes de «MCP»). La MISMA forma en `dv_gancho/mcp`, `dv_enchufe`,
  `dv_higgsfield` y `dv_guia`. `neon=True`: el contorno se dibuja con `draw` (path SVG) antes
  de rellenarse.
- **`_zocalo(iid, P)`** — el zócalo donde encastra el conector: rectángulo hundido con dos
  ranuras; `{iid}-luz` se enciende (`fade-to`) al encastrar.
- **`_mosaico(iid, slug, P, px=150, nombre=None)`** — mosaico de app (cuadrado radio 24 %,
  `surface`, el logo centrado) con una pastilla debajo; el `nombre` de la pastilla se escribe
  con `type-word` en su palabra (vacía hasta entonces). Si `mockups_codex._mosaico` sirve,
  úsalo.
- **`_burbuja(iid, texto, P, legible=False, vacia=False)`** — burbuja de pedido: globo
  `surface` radio `lg` con cola abajo a la izquierda, ancho máx. 640, texto Inter 600 24 px
  `P.text`. **Borrosa**: el texto en un hijo `{iid}-b` con `filter: blur(7px)`, opacidad .8.
  Para el enfoque, una SEGUNDA copia nítida `{iid}-n` apilada a opacidad 0 (enfocar =
  `fade-to` de `-b` a 0 y de `-n` a 1). Fuera del clímax solo se emite la copia borrosa.
  `vacia`: el globo con tres barras grises en lugar de texto.
- **`_personaje`** — el de `mockups_codex`, aceptando `personajes-9`.

## Componentes

Cada «en at[i]» es el instante exacto en que eso EMPIEZA. Tamaños orientativos: la ventana
≈980×700 en partida y ≈980×1100 en grafico; cangrejo 160–220 px en partida, 240–320 en
grafico. **En casi todos hay algo moviéndose siempre** (el cabezal que corre, los medidores):
la ventana nunca está congelada.

### 1. `dv_gancho(cid, variant, at, lienzo=False, fondo="oscuro")`

- **`abre`** (partida, `at=[t_DaVinci, t_Resolve]`). La ventana completa (visor con
  `toma-2.jpg`, línea de tiempo V2/V1/A1/A2 llena) YA corriendo desde el primer cuadro: el
  cabezal avanza todo el visual (`cursor-to` x lineal) y los medidores rebotan. En at[0] el
  nombre «DaVinci Resolve» de la barra de título se escribe (`type-word`). En at[1] el
  mosaico `davinciresolve` (110 px) se posa en la esquina superior derecha de la ventana
  (`drop-in`) con su pastilla «DaVinci Resolve» (`type-word`).
- **`mcp`** (grafico, `at=[t_servidor, t_MCP, t_oficial]`). La misma ventana a lienzo, un
  poco a la izquierda (deja sitio a la derecha), cabezal corriendo. En at[0] el costado
  derecho de la ventana se abre: un `_zocalo` se desliza hacia afuera (`glide-x` desde
  −120). En at[1] el `_conector` se dibuja en neón (`draw`) a la derecha, viaja hasta el
  zócalo (`cursor-to` x) y encastra: el zócalo se enciende (`TK.GLOW` vía capa `fade-to`) y
  entra el logo `modelcontextprotocol` en el conector. En at[2] un sello de verificado
  (círculo `dv.ok` con tilde, 120 px) baja y se estampa sobre el encastre (`stamp`).

### 2. `dv_precio(cid, at, lienzo=False, fondo="claro")`

`at=[t_editor, t_gratis]`. Desde t=0 la ventana chica (≈620×420) centrada, cabezal
corriendo. En at[0] la ventana se encoge (×.35, `cursor-to` en un wrapper) hasta volverse el
mosaico `davinciresolve` (crossfade a `_mosaico` de 180 px, con pastilla «DaVinci Resolve»
ya escrita: se nombró antes). En at[1] cuelga del mosaico una etiqueta de precio (tarjeta
`surface` con agujero y cordel SVG, `drop-in` + leve `rot-to` −6° → 0) con «US$ 295»
(Inter 900 72 px) que rueda hacia abajo hasta **0** (`count-roll` 295 → 0, `power3.out`,
0.7 s) y el 0 queda encendido (`color-to` `accent` + `TK.GLOW`).

### 3. `dv_balanza(cid, at, lienzo=True, fondo="claro")`

`at=[t_pelea, t_igual, t_Premiere, t_Pro]`. Una balanza de dos platos (poste `text`,
travesaño 640 px, platos colgando con cuerdas SVG; el travesaño rota sobre su centro y los
platos quedan siempre verticales: rotación inversa en los hijos). Desde t=0 la balanza
vacía, quieta. En at[0] el mosaico `davinciresolve` (150 px) cae al plato izquierdo
(`drop-in`) y el travesaño se inclina a −14° (`rot-to`, `power2.out`). En at[1] el
travesaño empieza a volver hacia 0 pero se queda en −6° balanceándose. En at[2] el mosaico
`adobepremierepro` cae al plato derecho (`drop-in`) con su logo estampado (`stamp`). En at[3]
el travesaño frena EN SECO a 0° (`rot-to` 0.12 s, `power4.out`) y los dos platos brillan
igual (`TK.GLOW` en los dos a la vez).

### 4. `dv_linea(cid, variant, at, lienzo=..., fondo=...)`

La línea de tiempo sola (`_timeline` grande, sin visor), salvo donde se diga.

- **`subtitulos`** (partida, `fondo="comic"`, `at=[t_ponerle, t_subtitulos]`). Desde t=0 la
  línea de tiempo con 4 pistas llenas y el cabezal corriendo. En at[0] todas las pistas
  menos V1 se apagan (`fade-to` .08, escalonado .06 s) y V1 adelgaza (scaleY .55 en un hijo);
  una tira de subtítulos (pista `ST1` amarillo apagado: `mix(dv.tc, dv.panel, .5)`) cae
  encima (`drop-in`). En at[1] los bloques-palabra de la tira (6 rectángulos cortos, sin
  texto) se llenan de a uno (`fade-to` 1, escalón .1 s).
- **`tijeras`** (grafico, `fondo="comic"`, `at=[t_cortar, t_4, t_veces]`). La pista V1 flaca
  sola, grande, en el medio (980 de ancho), y a la derecha un contador «Cortes» con un 0
  (Inter 900 96 px; el rótulo es interfaz). Unas tijeras (glifo SVG de línea, 180 px, `text`)
  — en at[0] entran desde la izquierda y dan el primer tijeretazo: la pista se parte (una
  línea vertical se dibuja) y el contador pasa a 1 (`count-roll`). En at[1] tres tijeretazos
  más, escalón .18 s, contador 2, 3, 4 (las tijeras avanzan en x). En at[2] las tijeras salen
  por la derecha y los pedazos de la pista se van (`fade-to` 0) salvo uno: un muñón corto
  en medio del lienzo vacío.
- **`produccion`** (partida, `fondo="oscuro"`, `at=[t_edicion, t_nivel, t_produccion]`).
  Desde t=0 el muñón del componente anterior en el centro. En at[0] el muñón se estira hacia
  los dos costados (`grow-x` desde el centro) hasta ser la línea de tiempo entera. En at[1]
  las pistas se apilan una sobre otra como una escalera (V1, V2, V3, A1, A2, A3 `rise-in`
  escalonado .08 s). En at[2] arriba se encienden tres paneles de la ventana, uno al lado del
  otro: las **ruedas de color** (tres círculos con aro de tono y punto), el **osciloscopio**
  (forma de onda verde: columnas de puntos deterministas) y el **árbol de nodos** (tres
  nodos rectangulares unidos por curvas), con `chip-in` escalonado y resplandor
  `TK.GLOW` detrás; el cabezal arranca a correr.

### 5. `dv_enchufe(cid, at, lienzo=True, fondo="claro")`

`at=[t_enchufas, t_Claude, t_Codex]`. Arriba, la ventana chica (≈620×360) con el
`_conector` ya encastrado en su costado (se mostró en el gancho). Abajo, dos mosaicos
apagados (opacidad .35, sin logo): izquierda y derecha. En at[0] del conector brotan dos
cables (paths SVG gruesos 10 px `text`, `draw` 0.5 s) que bajan y se estiran hacia los
mosaicos. En at[1] el cable izquierdo llega y se enchufa (`click`), el mosaico se enciende
(`fade-to` 1) con el logo `claude` y la pastilla «Claude Code» (`type-word`). En at[2] lo
mismo a la derecha con `openai` y «Codex». Al enchufarse, una luz `accent_hi` corre por cada
cable (dash animado en bucle hasta el final).

### 6. `dv_pedido(cid, at, lienzo=False, fondo="claro")`

`at=[t_pides, t_necesites]`. Abajo de la banda, la línea de tiempo (≈980×300) con el
cabezal corriendo. En at[0] una onda de voz (tres arcos SVG `accent` que se expanden y se
apagan, `scale-pop` + `fade-to`) y en su lugar se infla la `_burbuja` del pedido 1, BORROSA
(`chip-in` desde la izquierda). En at[1] detrás de ella se apilan cuatro burbujas `vacia`
más, cada una un poco más chica y desplazada (`chip-in` escalón .1 s).

### 7. `dv_color(cid, at, lienzo=True, fondo="claro")`

`at=[t_corrige, t_color]`. La página Color de la ventana (`pagina="color"`): visor grande con
`toma-12.jpg` **plano y gris** (`filter: grayscale(1) contrast(.7) brightness(1.05)`), debajo
las tres ruedas de color (Lift, Gamma, Gain: rótulos de interfaz mono 13 px) y a la derecha
el osciloscopio vacío. Arriba a la izquierda, chica, la `_burbuja` del pedido 1 borrosa
(desde t=0). Abajo a la derecha, el cangrejo `rueda` (240 px). En at[0] los puntos de las
tres ruedas giran (`rot-to` 0 → 140°/−90°/60°, 0.6 s, en hijos) y el cangrejo da un
`punch`. En at[1] una línea divisoria vertical (3 px `text` con sombra) barre el visor de
izquierda a derecha (0.7 s) y detrás de ella queda la MISMA imagen con color (una segunda
copia sin filtro, `filter: saturate(1.25) contrast(1.12)`, revelada con `clip-path:
inset(0 X 0 0)` animado o con un contenedor `overflow:hidden` que crece con `grow-x`), y el
osciloscopio se llena al mismo ritmo (columnas `rise-bar` escalonadas).

### 8. `dv_graficos(cid, at, lienzo=False, fondo="claro")`

`at=[t_arme, t_graficos, t_movimiento]`. La ventana (≈980×720) con visor (`toma-22.jpg`) y
la línea de tiempo V1/A1; arriba a la izquierda la `_burbuja` del pedido 2 borrosa. En at[0]
se abre una pista nueva V2 vacía sobre V1 (`grow-x` de una franja `dv.panel2`). En at[1]
sobre la imagen del visor una forma se arma sola pieza por pieza: un tercio inferior
(rectángulo `accent` con radio + un círculo + una barra, `chip-in` escalón .1 s) y en V2
aparece su clip `dv.video2`. En at[2] caen en V2 cuatro fotogramas clave en rombo (`drop-in`
escalón .12 s), se dibuja la curva entre ellos (`draw`) y la forma del visor empieza a
moverse (`cursor-to` x ida y vuelta, `sine.inOut`, hasta el final).

### 9. `dv_multicam(cid, at, lienzo=True, fondo="claro")`

`at=[t_corte, t_multicamara]`. La ventana con el visor grande y la línea de tiempo abajo;
arriba a la izquierda la `_burbuja` del pedido 3 borrosa. Desde t=0 el visor con un solo
ángulo (`toma-2.jpg`). En at[0] el visor se parte en una rejilla 2×2 de cuatro ángulos de la
misma escena: `toma-2`, `toma-12`, `toma-22`, `toma-38`, cada uno con un encuadre distinto
(`object-position` y escala deterministas: general, cerrado, izquierda, derecha) y su número
de ángulo (1–4, mono, interfaz). En at[1] un marco encendido (`dv.playhead` 5 px) salta de
ángulo en ángulo 4 veces (escalón .22 s: 1→3→2→4) y por cada salto se clava un corte en V1
(una línea vertical `text` `draw` de alto de pista) y el clip de V1 cambia de miniatura.

### 10. `dv_sonido(cid, at, lienzo=False, fondo="claro")`

`at=[t_meta, t_efectos, t_sonido]`. La línea de tiempo (≈980×600, sin visor) con V1 cortado
en 4 clips (los cortes de la multicámara) y la `_burbuja` del pedido 4 borrosa arriba a la
izquierda; a la derecha los medidores. En at[0] se abre una pista de audio vacía A3 debajo
(`grow-x`). En at[1] caen en A3 tres bloques de onda cortos (`drop-in` escalón .16 s), cada
uno justo debajo de un corte. En at[2] cada bloque dibuja su forma de onda (`draw` o
`rise-bar` de sus barras, escalón .16 s) y los medidores pegan un salto por bloque.

### 11. `dv_musica(cid, at, lienzo=True, fondo="oscuro")`

`at=[t_calce, t_musica, t_montaje]`. La línea de tiempo grande: V1 con 5 cortes marcados
(líneas `text` .5) y una pista de música `dv.music` con su forma de onda de picos claros
(6 picos altos deterministas), DESFASADA: los picos no caen sobre los cortes. Arriba a la
izquierda la `_burbuja` del pedido 5 borrosa. En at[0] la forma de onda de la música se
estira como un elástico (scaleX 1 → 1.12 → .96 en un hijo, `cursor-to`/`grow-x` de dos
tramos). En at[1] se encienden uno a uno marcadores de compás (rombos `dv.tc` sobre la
regla, escalón .1 s). En at[2] la onda se corre hasta que cada pico queda sobre un corte
(`cursor-to` x a su posición final) y la línea de tiempo entera late una vez (`punch` en el
contenedor + `TK.GLOW`).

### 12. `dv_pozo(cid, at, lienzo=True, fondo="comic")`

`at=[t_falta, t_plano, t_dos, t_escenas]`. La línea de tiempo grande con V1 = tres clips con
miniatura (`toma-2`, `toma-12`, `toma-38`), A1 debajo. En at[0] el clip del medio salta
fuera de la pista y sale de cuadro girando (`cursor-to` y −500 + `rot-to` 200°) y donde
estaba queda un pozo negro. En at[1] en el pozo parpadea el contorno discontinuo de un
cuadro vacío (`fade-to` 1/.3/1). En at[2] los dos clips vecinos se separan hacia los bordes
(`glide-x` ±60) y el pozo se agranda. En at[3] el cabezal cruza desde la izquierda, llega al
pozo, tropieza (se clava en el borde) y queda vibrando (`jitter` 3 px hasta el final, sobre
un HIJO del cabezal, no sobre el que lleva el `cursor-to`).

### 13. `dv_genera(cid, at, lienzo=True, fondo="oscuro")`

`at=[t_Claude, t_genera]`. Grande en el centro, el cuadro vacío del pozo (marco 9:16, 520×924,
contorno discontinuo `text2`), a oscuras; debajo, un trozo de la línea de tiempo con el pozo.
En at[0] el logo `claude` (56 px) entra arriba del marco y el cangrejo `asoma` (220 px)
aparece al borde inferior del marco mirando adentro (`rise-in`). En at[1] el cangrejo pasa a
`pinta` y salta adentro del marco (`cursor-to` y −80) y la imagen `plano.jpg` se arma: arranca
con `filter: blur(28px) brightness(.5)` + una capa de ruido (SVG `feTurbulence` estático,
opacidad .6) y en 1.1 s pasa a nítida (dos copias: la borrosa se apaga y la nítida se enciende,
mientras el ruido se apaga), con un resplandor `accent` detrás (luz de atrás). Es EL MISMO
archivo en los dos estados.

### 14. `dv_encastra(cid, at, lienzo=False, fondo="claro")`

`at=[t_deja, t_puesto, t_tiempo]`. La línea de tiempo (≈980×520) con el pozo entre los dos
clips separados (como terminó `dv_pozo`) y el cabezal trabado al borde del pozo, vibrando
desde t=0. En at[0] la miniatura de `plano.jpg` baja desde arriba hacia el pozo (`drop-in`).
En at[1] encastra (`stamp`) y los dos vecinos se cierran contra ella (`glide-x` de vuelta) sin
dejar junta; el cabezal deja de vibrar. En at[2] el cabezal cruza de punta a punta sin
tropezar (`cursor-to` x lineal 0.8 s) y los medidores rebotan.

### 15. `dv_higgsfield(cid, at, lienzo=False, fondo="oscuro")`

`at=[t_algo, t_genere, t_imagenes, t_Higgsfield]`. A la izquierda la ventana chica con el
`_conector` encastrado; de él cuelga un tercer cable suelto que se bambolea desde t=0
(`rot-to` ±8° en bucle). A la derecha un mosaico apagado (sin logo) y un zócalo. En at[0] el
cable se tensa hacia el zócalo del mosaico y hace clic (`draw` del path tenso + `click`). En
at[1] el mosaico se enciende (`fade-to` 1, borde `accent_hi`). En at[2] del mosaico salen
cuatro cuadritos (miniaturas de `plano.jpg`, 48×85) que viajan por el cable hasta la ventana
(`cursor-to` en dos tramos, escalón .15 s) y se posan en su línea de tiempo. En at[3] el logo
`higgsfield` se estampa en el mosaico (`stamp`) con su pastilla «Higgsfield» (`type-word`) y
un resplandor detrás.

### 16. `dv_editor(cid, at, lienzo=True, fondo="claro")`

`at=[t_hace, t_dentro, t_editor]`. La ventana completa al 82 % (wrapper), con TODO lo del
video ya puesto: visor con `toma-12.jpg` con color, V2 con el clip de gráficos y sus rombos,
V1 cortado en multicámara con el `plano.jpg` en su hueco, A3 con los bloques de efectos y la
pista de música con los marcadores. En at[0] el cangrejo `arrastra` (200 px) aparece sobre la
línea de tiempo arrastrando el cabezal (`cursor-to` x del cangrejo y del cabezal juntos) y las
pistas se completan a su paso (un barrido de brillo `fade-to` en cada pista, escalón .08 s).
En at[1] la cámara entra al panel: el wrapper pasa de .82 a 1.0 (`cursor-to`/escala en el
wrapper estático, 0.5 s, `power2.inOut`). En at[2] el mosaico `davinciresolve` (90 px) se
enciende en la esquina superior derecha de la ventana (`stamp` + `TK.GLOW`).

### 17. `dv_guia(cid, variant, at, lienzo=False, fondo="claro")`

**La hoja de guía**: tarjeta `surface` 980 de ancho, radio `lg`, con una cabecera chica (el
`_conector` a la izquierda cuando corresponda) y renglones numerados (1–5: número en Inter
800 26 px `accent` + una barra borrosa de texto `rgba(text,.35)` con `blur(4px)`).

- **`despliega`** (partida, `at=[t_guia, t_conectarlo]`). Desde t=0 la línea de tiempo chica
  abajo (cabezal corriendo). En at[0] la hoja se despliega como acordeón (cada renglón
  `rise-bar` desde arriba, escalón .08 s) con sus renglones borrosos. En at[1] el `_conector`
  baja desde arriba y encastra en el primer renglón (`drop-in` + `stamp`, el renglón 1 se
  enciende con `TK.GLOW`).
- **`pedidos`** (partida, CLÍMAX, `at=[t_pedidos, t_exactos, t_hago]`). Desde t=0 la hoja
  compacta arriba (solo cabecera + conector, 980×90). En at[0] las seis burbujas de
  `PEDIDOS` se apilan en columna debajo, BORROSAS (`chip-in` escalón .07 s; burbujas de 22 px,
  ancho 980, alineadas a la izquierda; comprobar con `text_px` que cada pedido entra en dos
  renglones como mucho). En at[1] una onda de luz (franja con degradado `accent` →
  transparente, 980×80) las recorre de arriba a abajo (`cursor-to` y, 0.6 s). En at[1]+0.15
  cada burbuja entra en foco una después de otra, escalón .16 s: `fade-to` de la borrosa a 0
  y de la nítida a 1. Es la única vez que se leen. En at[2] la columna y la hoja se juntan en
  un solo bloque (un marco `surface` común las envuelve: `fade-to` de su borde + `punch`).

## Verificación que se pide

1. Tests en `tests/test_mockups_davinci.py`: cada componente y variante devuelve
   `(css, html, anims)`; variante/fondo mal escritos → `ValueError`; `at` con largo
   equivocado → `ValueError`; los textos que se DICEN («DaVinci Resolve» en `abre`, «Claude
   Code» y «Codex» en `dv_enchufe`, «Higgsfield») no están en el HTML antes de su `at`
   (tecleados); los pedidos nítidos solo están en `dv_guia/pedidos`; `assets_de` devuelve
   exactamente las imágenes que el html referencia; ningún hex suelto fuera de
   `BRANDS["davinci"]`.
2. La suite entera pasa: `.venv/bin/python -m pytest -q`.
3. El plan real lo escribo yo (`videos/9/armar-plan.py`). Sí hace falta que
   `build-composition.py` importe el módulo y despache los 17 componentes.
4. En el reporte: qué gestos usaste por componente, cualquier gesto nuevo, y cualquier
   excepción agregada a los tests de paleta con su motivo.
