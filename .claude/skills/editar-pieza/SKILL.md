---
name: editar-pieza
description: Edita SIN PREGUNTAR una pieza pedida desde el dashboard Cubo Marketing, en tres pasadas (propuesta, editar, corregir). La lanza el dashboard con `claude -p "/editar-pieza <n> <pasada>"`; nadie mira la conversación. Para editar conversando con el usuario se usa video-tech-premium, no esta.
---

# /editar-pieza <n> <pasada>

`<n>` es el número de la pieza y `<pasada>` es `propuesta`, `editar` o `corregir`.

**Los scripts de Python se corren con `.venv/bin/python`**: el `python3` del sistema no trae
`cv2` ni `numpy` y el pipeline falla a mitad de camino.

**Nadie mira esta conversación.** Nunca hagas preguntas ni esperes respuesta:
- lo que en el paso 3b sería una pregunta va a `propuesta.json → preguntas` (pasada `propuesta`);
- si falta algo para seguir, termina con una sola línea: `ERROR: <qué pasó y cómo arreglarlo>`.

**La doctrina es la del `CLAUDE.md` de este proyecto** y se aplica completa: triband en REEL
(§4), la banda `top` nunca vacía, nada entra antes de su palabra (§7), cambio de visual cada
1–2,5 s, logo de cada herramienta que se nombra, gates del EDL (§2, paso 9b), sonido (§12),
color si es HDR (§8), trampas del renderer (§9). Léelo antes de escribir la propuesta o el
EDL. Esta skill solo dice el ORDEN y los ARCHIVOS de una pieza del dashboard.

## La pieza

- `VIDEOS ORIGINALES/<n>/pedido.json`: título, `origen`, `prompt` (puede estar vacío),
  `paleta` y los clips con su rol (`cuerpo` en `orden`, `cta` con `plataforma`, `pantalla`,
  `apoyo`). Lo escribe el dashboard; no lo toques.
- Cada `cta` es una **versión**: `<n>-<plataforma>`. Sin `cta`, la única versión es `<n>-general`.
- Si `prompt` es un brief de `plan-edicion` (empieza con `Video fuente:`), úsalo como en el
  paso 3b: su paleta manda, sus anclas se cuadran con el transcript, sus "Ideas para sumar
  al editor" NO se construyen.

## Pasada `propuesta`

1. `.venv/bin/python scripts/unir-cuerpo.py --piece <n>` → `out/<n>-fuente.mov`. Si sale `ERROR:`, termina con ese error.
2. `scripts/detect-format.sh out/<n>-fuente.mov`. Si no decide (casi cuadrada), termina con `ERROR:`.
3. Cuerpo, pasos 1–3 del pipeline con `<n>`: audio → `.venv/bin/python scripts/transcribe.py` →
   `.venv/bin/python scripts/refine-timings.py … --write` → `.venv/bin/python scripts/plan-cuts.py … --audio …`.
   Revisa los avisos de `refine-timings` como dice §2 (re-transcribir un tramo si hace falta).
4. Cada CTA, lo mismo con el id `<n>-cta-<plataforma>` y el clip del pedido como fuente:
   `assets/audio/<n>-cta-<p>.flac`, `transcripts/<n>-cta-<p>.json`, `cuts/<n>-cta-<p>.json`.
5. Cada versión: `scripts/preparar-version.sh <n> <plataforma>`. Si la auditoría de
   respiraciones falla, arregla los cortes como dice §2 (paso 4b) y vuelve a correrlo.
   Si no se puede arreglar, termina con `ERROR:`.
6. Logos: cada herramienta que se nombra lleva su logo. Los que falten, con
   `.venv/bin/python scripts/fetch-logos.py`. Si uno no se consigue, va a `avisos`.
7. Escribe `videos/<n>/propuesta.json` (formato abajo). Los beats y sus tiempos son del
   **cuerpo**, en la línea del corte (remapeados). Lo que no cuadra va a `preguntas`, con
   `opciones` y una `propuesta_por_defecto` que se pueda ejecutar sin preguntar.
8. `.venv/bin/python scripts/validar-propuesta.py --piece <n>`. Corrige SOLO lo reportado y repite hasta ✓.
9. Respuesta final: `Propuesta <n>: <N> beats · <P> preguntas · versiones <lista>`.

```json
{
  "pieza": 7, "generado": "2026-09-26T15:08:40", "formato": "REEL", "duracion_corte": 58.4,
  "paleta": "claro",
  "beats": [{ "id": "b1", "desde": 0.0, "hasta": 4.2, "texto": "…", "ancla": "frase exacta del transcript",
              "banda_arriba": "qué se ve", "componente": { "nombre": "tool_card", "existe": true },
              "logos": [{ "slug": "claude", "estado": "disponible" }], "material": ["pantalla-3.mov"] }],
  "preguntas": [{ "id": "q1", "beat": "b3", "pregunta": "…", "opciones": ["…", "…"],
                  "propuesta_por_defecto": "…" }],
  "versiones": [{ "plataforma": "instagram", "cta_texto": "transcript del CTA", "duracion": 4.1 }],
  "avisos": [{ "tipo": "audio | alineacion | material | formato", "mensaje": "…" }]
}
```

## Pasada `editar`

1. Lee `videos/<n>/propuesta.json` y `VIDEOS ORIGINALES/<n>/respuestas.json`. Las respuestas
   mandan sobre la propuesta: `beats[].banda_arriba` reemplaza el texto del beat, y cada
   pregunta trae su `respuesta` (si `por_defecto: true`, el usuario no la tocó).
2. Recorridos de pantalla (paso 7) y música (paso 8) si hacen falta. La cama musical dura lo
   que la versión más larga.
3. Escribe `videos/<n>/edl-cuerpo.json`: el EDL del CUERPO con `transcripts/<n>.json` +
   `cuts/<n>.json`, `palette` del pedido, cubriendo todas sus palabras.
4. Por cada CTA, `videos/<n>/cta-<p>.json` = `{"segments": […]}` con índices del transcript
   del CTA (0..C-1): un solo elemento visual, como pide la curva de intensidad (§6).
5. Por cada versión: `.venv/bin/python scripts/armar-version.py edl --piece <n> --plataforma <p>` →
   `.venv/bin/python scripts/edl-compile.py --project . --piece <n>-<p>` → color e
   `input-video.mp4` como dice §8 (con `out/<n>-<p>-rough.mp4`) →
   `.venv/bin/python scripts/build-composition.py --project . --piece <n>-<p>` →
   `.venv/bin/python scripts/renderizar-version.py --piece <n> --plataforma <p> --version 1`.
   Si un gate falla, corrige el EDL y repite desde `armar-version.py edl`.
6. `.venv/bin/python scripts/validar-salida.py --piece <n> --version v1`. Corrige hasta ✓.
7. Respuesta final: `Pieza <n> v1: <lista de MP4>`.

## Pasada `corregir`

1. Lee el `VIDEOS ORIGINALES/<n>/notas-v<k>.json` de `k` más alto: `{"desde": "v<k-1>", "notas": "…"}`.
2. Ajusta `edl-cuerpo.json` y/o `cta-<p>.json`. No re-transcribas ni re-cortes salvo que la nota
   lo pida; si lo pide, vuelve a correr `preparar-version.sh` de las versiones afectadas.
3. Repite el paso 5 de `editar` para TODAS las versiones con `--version <k>`, y valida con
   `.venv/bin/python scripts/validar-salida.py --piece <n> --version v<k>`.
4. Si una nota choca con una regla dura del CLAUDE.md (§13), aplica el resto y agrega al final
   de tu respuesta `No apliqué: <nota> — <regla>`.
5. Respuesta final: `Pieza <n> v<k>: <lista de MP4>`.
