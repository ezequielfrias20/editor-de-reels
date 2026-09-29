# Los tres formatos (layout `formatos`)

Doctrina de 2026-09-29, a pedido de Ezequiel: los reels se editan como los de su referente. Casi nada de texto en pantalla, objetos de interfaz que actúan lo que se dice, y tres formatos que se alternan con corte seco. Spec: `docs/specs/2026-09-29-edicion-animada-design.md` en el repo de Marketing.

| Formato | Encuadre | Qué se ve | Cuándo |
|---|---|---|---|
| `cara` | `"kind": "full"` con `zoom` | Ezequiel a lienzo completo, acercado | Remates, opiniones, tesis, CTA |
| `partida` | `"kind": "band"` + visual con `"band": "top"` | Arriba el visual (y 0–960), abajo Ezequiel en plano medio (y 960–1920) | Algo se muestra y la cara sostiene la frase |
| `grafico` | `"kind": "off"` bajo un visual opaco sin `band` | Todo el lienzo es visual | La demostración |

- **Reparto:** cerca de un tercio de cada formato.
- **Ritmo:** cambio de formato o de visual cada 1 a 3 s, y un tramo `grafico` no pasa de unos 3 s seguidos.
- **Movimiento:** en `partida` y `grafico` siempre hay algo moviéndose.

## La geometría

`"layout": {"mode": "formatos"}` y nada más: `layout_formatos.resolver` completa las bandas, `top` = `[0, 960]` y `speaker` = `[960, 1920]`. La línea de división (costura) cae en y960. Si un plan declara otras bandas, la compilación para.

## El subtítulo

- **`partida`:** el bloque se centra sobre la costura, con la piel de filete (`on-dark`). Si al bajar pisaría la cara (el `top_frac` de `measure-face.py` proyectado al encuadre), la compilación para: se trocea el bloque o se baja el `anchor`.
- **`cara`:** el bloque esquiva la barbilla, como siempre.
- **`grafico`:** va donde lo ponga el visual (`cap_top`) y respeta el 20 % de abajo.

## El acercamiento de `cara`

`check_cara_zoom` para la compilación por encima de:
- `ZOOM_MAX_1080` = ×1,20 si el lado corto de la fuente es menor que 2160 px;
- `ZOOM_MAX_4K` = ×1,40 con una fuente 4K.

El primer plano cerrado de la referencia está en ×1,4: para llegar ahí, hay que grabar en 4K.

## La palabra clave del CTA

En `plan-cta-<p>.json`:

```json
"cta_palabra": {"texto": "MARCA", "desde": 41.20, "hasta": null}
```

- En segundos de la versión: `hasta: null` llega al final.
- Se dibuja en Fraunces Italic 800, 1,45 veces el tamaño del subtítulo, entre comillas curvas y 12 px debajo del bloque que suena. Queda fija mientras dura el CTA.
- Los bloques de su ventana dejan sitio para ella por encima del 20 % de la plataforma.
- `armar-version.py plan` la pasa al plan de la versión.

## Un plan de ejemplo

```json
{
  "format": "REEL", "palette": "claro", "layout": {"mode": "formatos"},
  "shots": [
    {"at": 0.00, "kind": "band", "anchor": 0.40},
    {"at": 3.10, "kind": "off"},
    {"at": 5.60, "kind": "full", "zoom": 1.12, "anchor": 0.44},
    {"at": 7.40, "kind": "band", "anchor": 0.40}
  ],
  "visuals": [
    {"id": "v-repo", "role": "takeover", "kind": "mockup", "band": "top",
     "start": 0.00, "end": 3.10, "mock": ["tool_card", {"slug": "github", "name": "GitHub"}]},
    {"id": "v-demo", "role": "takeover", "kind": "mockup", "fade_in": 0.0, "fade_out": 0.0,
     "start": 3.10, "end": 5.60, "mock": ["claude_prompt", {"…": "…"}]},
    {"id": "v-cifra", "role": "takeover", "kind": "mockup", "band": "top",
     "start": 7.40, "end": 10.00, "mock": ["stat_grid", {"…": "…"}]}
  ]
}
```

- **`partida`:** el encuadre `band` va con su visual en `band: "top"`, que ocupa la banda de arriba.
- **`grafico`:** el visual opaco entra y sale con **corte seco** (`fade_in` y `fade_out` en 0). El `off` y el visual tienen el mismo tramo (3.10–5.60), y el visual de `partida` de antes termina justo donde empieza (3.10).
  - Con fundido no se puede, por dos controles: `check_band_speaker_clear` no deja que un visual opaco se solape con un encuadre `band`, y `check_no_black` no deja que el `off` empiece antes de que el visual tape del todo.
  - Tampoco pueden convivir dos visuales en la misma pista.
- **`cara`:** el `full` con su zoom, sin visual encima.
- **Los controles de siempre siguen valiendo:** `check_band_speaker_clear`, `check_face_top_clear`, `check_band_top_covered` (la banda de arriba de `partida` nunca queda vacía) y `check_no_black`.

## Mostrar, no escribir

En pantalla solo hay texto cuando es parte de una interfaz: un archivo, un botón, un contador, un nombre de perfil. `keyword_hero`, `step_grid` y `chip_grid` no se usan como visual principal de un momento, porque repiten con palabras lo que ya dice el subtítulo. El visual muestra la cosa, y el verbo de la frase es lo que se mueve.
