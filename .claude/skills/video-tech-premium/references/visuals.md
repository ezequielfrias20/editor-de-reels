# Visuales — qué técnica usa cada momento

**La técnica varía según qué es esa cosa.** Repetir siempre la misma es lo que hace que un
video parezca una plantilla.

| Momento | Técnica | Cómo |
| --- | --- | --- |
| **Interfaz genérica** — herramientas, un mapa de módulos, un flujo | **mockup HTML** (`mockups.py`) | Dibujado con los tokens. Nunca una captura real: no encaja en la paleta y envejece |
| **Producto propio** — tu app, tu dashboard | **grabación real** dirigida (`screen-tour.py` + `screen_overlay`) | Manda sobre cualquier imagen generada |
| **Un dato, un concepto** | **cifra o palabra protagonista** (`stat_grid`, `keyword_hero`) | El texto ES el gráfico |
| **Atmósfera** — un lugar, un objeto | **imagen generada** con Kie AI | Con Ken Burns y velo, y solo si aporta |

Regla de oro: **si se habla de un proyecto real, prioriza imágenes y grabaciones del
proyecto por encima de cualquier stock o generación.**

---

## Grabaciones de pantalla

Una grabación cruda es el peor b-roll posible: apaisada, llena de chrome ajeno y con el
punto de interés ocupando el 8 % del cuadro. `screen-tour.py` la convierte en un
recorrido:

1. **Recorta el chrome** — pestañas, barra de direcciones, marcadores y dock fuera. Lo que
   se ve es el **producto**, no el navegador de quien grabó.
2. **Encuadra el punto de interés** — un recorte distinto por tramo, elegido por lo que se
   está diciendo en ese segundo.
3. **Empuja la cámara** — un zoom lento dentro de cada tramo, para que no se lea como una
   imagen fija.
4. **Corta en duro** entre tramos, al ritmo del habla.

```jsonc
{"label": "STOCK", "at": 49.20, "dur": 2.75,
 "crop": [642, 260, 1180, 747], "zoom": [1.02, 1.09]}
```

⚠ **Las barras negras.** Una grabación casi nunca llena el archivo. El script mide el
contenido real con `cropdetect` y **falla antes de renderizar** si un recorte las pisa —
porque un recorte que las incluye «cabe» en el archivo perfectamente y solo se descubre
mirando el resultado.

### En la composición

El clip se coloca con `rect` como **tarjeta**, no a sangre: una captura apaisada a pantalla
completa en 9:16 obliga a recortar tanto que se pierde el contexto de la interfaz.

**Alrededor va un panel elevado, no un navegador.** El panel es hairline + sombra, lo mismo
que sostiene cualquier otra superficie del sistema (§3), y **no gasta alto en nada que
leer**. La barra de navegador cuesta 74 px más pestañas y una URL que nadie lee, y en 9:16
ese alto sale directamente del tamaño de la interfaz — que es lo único que el espectador
necesita ver. Se reserva `chrome` para cuando la pieza tenga que declarar «esto es la web»,
y aun así se paga el precio a sabiendas.

| | `panel` (por defecto) | `chrome` |
| --- | --- | --- |
| Alto que consume | 0 px | 74 px + el aro |
| Qué dice | «esto es una superficie del sistema» | «esto es un navegador» |
| Cuándo | **siempre que se enseñe el producto** | solo si la URL es el mensaje |

```jsonc
"rect": [40, 430, 1000, 980],
"panel": {"label": "PUNTO DE VENTA"}   // el chip es opcional; el HUD suele bastar
```

**El recorte manda sobre el marco.** Que se vea el flujo no se arregla con el contenedor,
se arregla en `screen-tour.json`: un `crop` estrecho sobre la zona que se está nombrando,
y una salida cuadrada — un origen apaisado dentro de un lienzo vertical solo cabe grande
si el recorte deja de ser apaisado. Referencia medida: en la pieza 2 el recorte
1350×854 acababa a **0.73×** dentro del `rect` (la interfaz se veía más pequeña que en el
monitor original); un recorte de ~900×880 en un panel de 1000×980 va a **1.11×**.

Encima van, en coordenadas del **lienzo**:

| Elemento | Para qué |
| --- | --- |
| `clicks` | cursor sobredimensionado + anillo + etiqueta. La acción se ve ocurrir |
| `boxes` | caja delimitadora con oscurecido alrededor. **Dirige la mirada** al punto exacto; sin ella el ojo barre la pantalla entera y se pierde la frase |

---

## Librería de mockups

| Función | Para qué | Tiempos |
| --- | --- | --- |
| `app_switch` | herramientas desconectadas; el conector **roto** dibuja la desconexión | `switch_at`, `alert_at` |
| `connection_map` | un núcleo y sus módulos, dibujados uno a uno | `draw_at` |
| `stat_grid` | tres cifras protagonistas — responde **cuánto** | `at` |
| `chip_grid` | una enumeración que se amontona — responde **cuántas cosas a la vez** | `at`, `alert_at` |
| `rate_mismatch` | el mismo dato calculado dos veces, con dos resultados | `at`, `verdict_at` |
| `keyword_hero` | una idea que cabe en una palabra | — |
| `flow_steps` | una acción y lo que dispara. `tone: "fail"` para una cadena que se rompe | `at` |
| `comment_ui` | el CTA simulado: la palabra grande, el tecleo y el envío | `type_at`, `send_at` |
| `screen_panel` | panel elevado alrededor de un `rect` — **el marco por defecto** | — |
| `browser_frame` | chrome de navegador alrededor de un `rect` — cuesta 74 px | — |
| `hud` | etiqueta de contexto del visual | — |

`stat_grid` y `chip_grid` se confunden fácil y no son intercambiables: tres cifras grandes
contestan «cuánto», una fila de etiquetas contesta «cuántas cosas a la vez». Meter cinco
métodos de pago en un `stat_grid` obliga a inventar cifras que nadie dijo.

En una cadena de fallo (`tone: "fail"`) **solo el último paso va en rojo**: teñirlos todos
la convierte en un error de sistema en vez de en el precio de haber llegado hasta ahí.

### Reglas al escribir uno nuevo

- **Nada entra antes de su palabra.** Tres logos visibles desde el primer frame parecen
  más limpios, pero el espectador lee «Excel» dos segundos antes de que se diga y, cuando
  llega la palabra, ya no pasa nada en pantalla.
- **La desconexión se dibuja, no se explica.** Un hueco entre tarjetas es un gap; dos
  muñones y un vacío es una conexión rota.
- **Se centra con flex**, nunca con `transform: translate(-50%,-50%)`: en cuanto GSAP le
  mete un `y` o un `scale`, toma el transform y descarta el centrado.
- **Contraste medido antes de renderizar**: `tokens.contrast(a, b)`. `logos.mark()` ya
  devuelve el ratio y el mockup debe **fallar** si baja de 3:1.
- **Un solo momento violeta de alto voltaje por frame.**
- El **HUD da contexto, no repite** un dato que ya está dentro del gráfico.

---

## Cards de herramienta (`triband`)

Dos componentes de `mockups.py`, pensados para la coreografía «se nombra la herramienta →
se ve su grabación» del layout `triband` (`references/triband.md`):

| Componente | Cuándo | Qué hace |
| --- | --- | --- |
| `tool_card` | al NOMBRAR la herramienta | marca + nombre, en una card sobre `band: "top"` |
| `tool_recording` | durante SU grabación (6–8 s) | el mismo logo persiste como **chip** en la cabecera del panel |

El logo persistiendo en la cabecera de `tool_recording` es lo que ata la grabación a su
nombre durante los 6–8 s que dura: sin él, pasados esos segundos el espectador ya no sabe
qué está mirando. Los fragmentos exactos de `plan.json` para invocar cada uno —verificados
contra la pieza 15— están en `references/triband.md`.

**`tool_recording` se despacha al nivel de `chrome`/`panel`**, dentro de un visual
`kind: "screen-video"`, no como un mockup suelto: los tres son alternativas de lo que se
dibuja ALREDEDOR de un `<video>` que vive suelto en el stage (un `<video>` anidado en un
elemento temporizado se congela — `references/gotchas.md`), así que ninguno de los tres
envuelve el clip, solo lo enmarca. Si el visual declara `tool_recording`, gana sobre
`chrome`; si no declara ninguno de los dos, cae a `panel` por defecto, igual que siempre.

`hairline` (grosor del marco en px) lo decide **quien llama**, no el componente: de las
cinco grabaciones de la pieza 15, la de Manus es la única con fondo CLARO y necesita un
marco más grueso para no perderse contra un fondo también claro. El componente no conoce
ningún slug especial — es una decisión de la pieza.

**El aspecto 3D es estático, no animado.** `perspective()`+`rotateY()` viven en un wrapper
HIJO que GSAP nunca toca; lo que se anima es `opacity`/`scale`/`x`/`y` del elemento de
dentro (mismo mecanismo que los objetos de `objects.py`, §7 del CLAUDE.md). En
`tool_recording` el tilt va **solo en el chip** de la cabecera (40×40 px), nunca en el
marco ni en la cabecera entera: el `<video>` real se coloca PLANO en el mismo `rect`, y un
marco inclinado dejaría de coincidir con su borde. Probado también al revés: el mismo
`rotateY` sobre la cabecera entera (una franja ancha pegada al borde superior) se ve ROTA,
no elegante — abre un hueco visible en la esquina donde el fondo se asoma por debajo. Un
elemento pequeño y cuadrado como el chip no tiene ese problema.

---

## Logos de terceros

`logos.mark(slug, size, tone)` desde Simple Icons, vendorizados en `assets/logos/`.

Sobre superficie oscura el color de marca hay que **aclararlo**: el verde de WhatsApp o el
de Excel a su valor nominal se hunden en el fondo. `brand_tone()` mezcla hacia blanco
hasta pasar 3:1 y devuelve el ratio medido.

### Marcas fuera de Simple Icons

No todas las marcas están ahí — ninguna de las cinco herramientas de la pieza 15 lo
estaba. `fetch-logos.py --vendor <slug>` las descarga directo del sitio oficial, con dos
gates antes de guardar nada:

- **Resolución.** La marca se pinta a ~110 px en la card; una marca raster (PNG) por
  debajo de 2× ese alto (220 px) se ve blanda, así que el script la **rechaza** en vez de
  vendorizar algo que entraría estirado sin que nadie lo note.
- **Saneado del SVG.** Un SVG vendorizado entra VERBATIM al HTML que renderiza Chrome —
  `logos.mark()` solo le toca el `width`/`height` del `<svg>` raíz, nada de su contenido.
  El fetcher rechaza cualquier SVG con `<script>`, un manejador `on...=` o
  `<foreignObject>` **antes de escribirlo a disco**.

`logos.mark()` devuelve `(html, ratio)` para las dos familias de marca (Simple Icons y
vendorizada), pero el `ratio` de una marca vendorizada **puede ser `None`**: si la marca es
transparente y no trae un tile de fondo propio, no hay nada contra qué medir contraste, y
quien llama tiene que tratar ese caso — no asumir que siempre hay un número.

`assets/logos/meta.json` guarda además `tile`: el color de fondo dominante que la marca
trae consigo (de un `<rect>` a lienzo completo en el SVG, o de las esquinas del PNG), para
poder medir si ese tile se distingue del `surface` del sistema — `None` si la marca es
transparente.

---

## Imágenes y video generados con IA

Solo cuando aportan atmósfera que no se puede dibujar. Todo pasa por `scripts/kie.py`.

| | Imagen | Video |
| --- | --- | --- |
| Endpoint | `POST /api/v1/jobs/createTask` | `POST /api/v1/veo/generate` |
| Modelo | `google/nano-banana` | `veo3_fast` · `veo3` · `veo3_lite` |
| Sondeo | `GET /api/v1/jobs/recordInfo` | `GET /api/v1/veo/record-info` |
| Estado | campo **`state`** | campo **`successFlag`** (0 gen · 1 ok · 2-3 falló) |
| Coste medido | 4 créditos | 60 créditos (8 s · 720p · veo3_fast) |

⚠ **La trampa cara.** Los nombres de modelo de video **no existen** en la API de jobs
(`veo3_fast` allí da 422), y la respuesta de Veo **no trae ningún campo `state`**. Sondear
por `state` deja el video colgado hasta el timeout aunque haya terminado — y los créditos
ya se gastaron. Si pasa: `scripts/kie.py fetch --task <id>` baja el resultado sin volver a
pagar.

**Caché y ledger.** La clave es el hash de (ruta, modelo, prompt, parámetros). Todo queda
en `assets/gen/ledger.json` con prompt, modelo, taskId y créditos. El pipeline se puede
volver a correr entero sin pagar dos veces.

**Prompts.** Pedir explícitamente `no text, no letters, no words, no numbers` — los
generadores meten texto ilegible que delata el asset. Nombrar la paleta del proyecto
(*deep graphite, electric violet, near-black*) hace que el resultado caiga dentro del
sistema en lugar de tener que corregirlo después.
