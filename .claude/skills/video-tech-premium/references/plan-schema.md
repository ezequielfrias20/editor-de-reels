# `videos/<n>/plan.json` — todos los campos

Describe la pieza entera. Es lo único que cambia entre videos.
**Todos los tiempos van en la línea del CORTE**, no en la del fuente.

```jsonc
{
  "format": "REEL",                  // REEL 1080×1920 · YOUTUBE 1920×1080
  "keywords": ["ERP", "stock"],      // palabras que el subtítulo resalta
  "caption_size": 66,                // opcional; por defecto la escala del formato
  "sfx_target_mean": -27.0,          // opcional
  "sfx_peak_cap": -12.0,             // opcional

  "music": {
    "src": "assets/music/bed-tech.mp3",
    "fade_in": 1.0, "fade_out": 2.6,
    "offset": 0.0,                   // desde qué segundo del archivo
    "target_mean": -34.0             // dB de media; la voz está en −19.8
  },

  "layout": {                         // opcional; solo si algún shot usa kind:"band"
    "mode": "triband",
    "bands": {"top": [0, 660], "text": [660, 960], "speaker": [960, 1920]}
  },

  "shots":   [ … ],                  // el METRAJE
  "cards":   [ … ],                  // rótulos FLOTANTES
  "visuals": [ … ],                  // lo que OCUPA el lienzo
  "sfx":     [ … ]
}
```

`layout` declara la geometría del layout `triband` **una sola vez** para toda la pieza —
`references/triband.md` tiene la geometría completa, la fórmula del `anchor` y los gates
que fallan si algo no cuadra. Un encuadre `kind: "band"` o un visual con `"band": "top"`
sin este bloque hace fallar la compilación: no hay lienzo-completo por defecto.

Cualquier clave que empiece por `_` es un comentario y el generador la ignora. Úsalas para
dejar escrito **por qué** un beat cae donde cae.

---

## `shots` — la capa de metraje

Una entrada por encuadre. Cada una vale hasta la siguiente.

```jsonc
{"at": 0.00, "kind": "full", "zoom": 1.12, "anchor": 0.42}
```

| Campo | Qué hace |
| --- | --- |
| `at` | desde cuándo, en la línea del corte |
| `kind` | `full` · `split` · `pip` · `off` · `band` |
| `zoom` | solo en `full`. Escala: 1.00 · 1.05 · 1.09 · 1.12 · 1.15 |
| `anchor` | fracción vertical del encuadre. 0.42–0.46 en `full`, 0.30 en `pip` |

`off` no emite elemento: es el tramo que un visual está tapando, y mantener ahí un
`<video>` invisible solo gasta memoria de decodificación.

`band` confina el metraje a la banda `speaker` del bloque `layout` (requiere `layout` en
el plan) y **no lleva `zoom`**: el rect de la banda ya recorta fuerte, y una escalera
encima dejaría la cara irreconocible. Su `anchor` no es cosmético — se deriva con una
fórmula a partir de dos mediciones de `measure-face.py` (`chin_frac`, `top_frac`) y dos
gates de compilación lo verifican (`check_band_speaker_clear`, `check_face_top_clear`).
Ver `references/triband.md`.

**El `anchor` mueve la barbilla, y la barbilla decide la altura del subtítulo.** No hay
que calcularlo a mano: el generador proyecta la medición de `measure-face.py` a cada
encuadre.

---

## `cards` — rótulos flotantes

```jsonc
{
  "start": 11.60, "end": 16.55, "place": "top",
  "kicker": "EL RETO", "title": "Todo a la vez", "key": "Todo",
  "sub": "texto secundario opcional",
  "body": "stat", "accent": 2,
  "items": [["VARIAS", "SUCURSALES"], ["CIENTOS", "PRODUCTOS"]],
  "beats": [11.89, 13.33, 15.49]
}
```

| Campo | Qué hace |
| --- | --- |
| `place` | `top` · `center` · `bottom` |
| `key` | palabra del titular que se pinta en violeta |
| `body` | `none` · `stat` · `chips` · `cta` |
| `accent` | índice de la celda que lleva el voltaje (solo una) |
| `beats` | tiempos **absolutos**; el generador los pasa a offsets |
| `cta_at` | tiempo absoluto del botón, en `body: "cta"` |

---

## `visuals` — lo que ocupa el lienzo

```jsonc
{
  "id": "viz-map", "role": "takeover", "kind": "mockup",
  "start": 20.38, "end": 28.05,
  "skin": "on-surface", "cap_top": 1440,
  "fade_in": 0.20, "fade_out": 0.14,
  "hud": ["LA SOLUCIÓN", "02"],
  "mock_pad_top": 260,
  "absolute_times": true,
  "mock": ["connection_map", { "nodes": […], "draw_at": [21.43, …] }]
}
```

| Campo | Qué hace |
| --- | --- |
| `role` | `takeover` sustituye lo que haya · `backdrop` va debajo, la tarjeta sigue encima |
| `kind` | `mockup` · `screen-video` · `video` · `image` |
| `start` / `end` | `end: null` llega al final de la pieza |
| `band` | confina el host de este visual al rect de esa banda del `layout` (`"top"` · `"text"` · `"speaker"`) y hace su fondo transparente en vez de opaco. Requiere `layout` en el plan. Ver `references/triband.md` |
| `skin` | piel del subtítulo mientras el visual está en pantalla |
| `cap_top` | baja el subtítulo: un takeover ocupa el centro |
| `hud` | `[etiqueta, índice]`. Da **contexto**, no repite un dato que ya está dentro |
| `mock_pad_top` | empuja el mockup hacia abajo para dejarle sitio al PiP |
| `mock_pad_bottom` | el contrapeso: lo sube. Un mockup corto centrado en el lienzo deja medio frame vacío bajo el PiP. El bloque debe quedar centrado hacia **y 820-880** |
| `absolute_times` | los tiempos del `mock` están en la línea del corte, no en offsets |
| `veil` | velo grafito sobre una imagen, para casarla con el fondo |
| `cam` | `{at, scale, y}` empuje · `{at, scale, to_scale}` Ken Burns |
| `fade_in` / `fade_out` | por defecto 0.28 / 0.26. Bájalos a ~0.14 para un corte duro |

### `kind: "screen-video"` — la grabación de producto

```jsonc
{
  "rect": [40, 430, 1000, 980],
  "panel": {"label": "PUNTO DE VENTA"},
  "clicks": [[28.94, 300, 980, "VENTA"]],
  "boxes":  [[29.50, 32.05, 560, 900, 440, 250]]
}
```

- `rect` coloca el clip como **tarjeta** dentro del lienzo. Una captura apaisada a sangre
  en 9:16 obliga a recortar tanto que se pierde el contexto de la interfaz.
- `panel` es el marco **por defecto**: hairline + sombra, sin nada que leer y sin gastar
  alto, así que la interfaz entra lo más grande posible. `label` es un chip mono opcional.
  `"panel": false` lo quita del todo.
- `chrome` `{url, brand}` dibuja en su lugar la barra de navegador — cuesta 74 px de alto
  y solo se justifica si la URL forma parte del mensaje. Ver `references/visuals.md`.
- `tool_recording` `{slug, name, hairline}` — dibuja el panel de una card de herramienta en
  `triband`: el logo persiste como chip en la cabecera. Gana sobre `chrome`/`panel` si
  está declarado. `hairline` (grosor del marco en px, por defecto 1) lo decide quien
  escribe el plan, no el componente. Ver `references/visuals.md` y `references/triband.md`.
- `clicks` = `[t, x, y, etiqueta]` en píxeles del **lienzo**.
- `boxes` = `[t_entra, t_sale, x, y, w, h]` — caja delimitadora con oscurecido alrededor.
  Es lo que dirige la mirada al punto exacto; sin ella el ojo barre la pantalla entera y
  se pierde la frase.

### Mockups disponibles

| Nombre | Para qué | Parámetros con tiempo |
| --- | --- | --- |
| `app_switch` | herramientas desconectadas | `switch_at`, `alert_at` |
| `connection_map` | un núcleo y sus módulos | `draw_at` |
| `stat_grid` | tres cifras protagonistas | `at` |
| `chip_grid` | una enumeración que se amontona | `at`, `alert_at` |
| `rate_mismatch` | el mismo dato con dos resultados distintos | `at`, `verdict_at` |
| `keyword_hero` | una idea que cabe en una palabra | — |
| `flow_steps` | una acción y lo que dispara (`tone`: `ok` · `fail`) | `at` |
| `comment_ui` | el CTA, simulado | `type_at`, `send_at` |
| `tool_card` | marca de una herramienta al nombrarla — pensada para `band: "top"` | — |

---

## `sfx`

`[t, nombre, trim, "por qué"]`. El `trim` solo matiza un nivel **ya normalizado por
medición** — no es el volumen.

El comentario no es decorativo: si no puedes señalar en el frame qué marca ese efecto,
el efecto sobra.
