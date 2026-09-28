---
name: editar-pieza
description: Edita SIN PREGUNTAR una pieza pedida desde el dashboard Cubo Marketing, en tres pasadas (propuesta, editar, corregir). La lanza el dashboard con `claude -p "/editar-pieza <n> <pasada>"`; nadie mira la conversación. Para editar conversando con el usuario se usa video-tech-premium, no esta.
---

# /editar-pieza <n> <pasada>

`<n>` es el número de la pieza y `<pasada>` es `propuesta`, `editar` o `corregir`.

**Los scripts de Python se corren con `.venv/bin/python`**: el `python3` del sistema no trae
`cv2` ni `numpy` y el pipeline falla a mitad de camino.

**Los pasos largos se corren con el timeout máximo del Bash tool (`timeout: 600000`)**:
`scripts/unir-cuerpo.py`, `scripts/preparar-version.sh` y `scripts/renderizar-version.py`
recodifican o renderizan y pasan de los 2 minutos por defecto; si el tool los corta, no
los relances en bucle: termina con `ERROR:`.

**No generes nada con servicios pagos** (`scripts/kie.py`, `scripts/gen.py`, Higgsfield u
otros): sin nadie mirando, lo único que sale a la red es `transcribe.py` (AssemblyAI) y
`fetch-logos.py`. Si un beat pediría un visual generado, va como pregunta en la propuesta.

**Nadie mira esta conversación.** Nunca hagas preguntas ni esperes respuesta:
- lo que en el paso 3b sería una pregunta va a `propuesta.json → preguntas` (pasada `propuesta`);
- si falta algo para seguir, termina con una sola línea: `ERROR: <qué pasó y cómo arreglarlo>`.

**La doctrina es la del `CLAUDE.md` de este proyecto** y se aplica completa: triband en REEL
(§4), la banda `top` nunca vacía, nada entra antes de su palabra (§7), cambio de visual cada
1–2,5 s, logo de cada herramienta que se nombra, los gates de `build-composition.py`, sonido (§12),
color si es HDR (§8), trampas del renderer (§9). Léelo antes de escribir la propuesta o el
plan. Esta skill solo dice el ORDEN y los ARCHIVOS de una pieza del dashboard.

## La pieza

- `VIDEOS ORIGINALES/<n>/pedido.json`: título, `origen`, `prompt` (puede estar vacío),
  `paleta` y los clips con su rol (`cuerpo` en `orden`, `cta` con `plataforma`, `pantalla`,
  `apoyo`). Lo escribe el dashboard; no lo toques.
- **Siempre salen dos versiones**, `<n>-instagram` y `<n>-tiktok`, haya o no clips de `cta`.
  El cuerpo suele cerrar con el CTA de Instagram dicho a cámara («comenta PARALELO y te lo
  mando por privado»). Cada versión toma el cuerpo HASTA ese CTA y le suma el suyo:
  - **instagram**: el clip `cta` de instagram si se subió; si no, el CTA que se dijo en el cuerpo.
  - **tiktok**: el clip `cta` de tiktok si se subió; si no, ningún CTA (el «comenta…» es de
    ManyChat, solo Instagram).
  `scripts/armar-version.py` hace ese recorte; tú solo anotas dónde empieza el CTA dicho
  (paso 4 de la propuesta).
- Si `prompt` es un brief de `plan-edicion` (empieza con `Video fuente:`), úsalo como en el
  paso 3b: su paleta manda, sus anclas se cuadran con el transcript, sus "Ideas para sumar
  al editor" NO se construyen.

## Pasada `propuesta`

1. `.venv/bin/python scripts/unir-cuerpo.py --piece <n>` → `out/<n>-fuente.mov`. Si sale `ERROR:`, termina con ese error.
2. `scripts/detect-format.sh out/<n>-fuente.mov`. Si no decide (casi cuadrada), termina con `ERROR:`.
3. Cuerpo, pasos 1–3 del pipeline con `<n>`: audio → `.venv/bin/python scripts/transcribe.py` →
   `.venv/bin/python scripts/refine-timings.py … --write` → `.venv/bin/python scripts/plan-cuts.py … --audio …`.
   Revisa los avisos de `refine-timings` como dice §2 (re-transcribir un tramo si hace falta).
4. Escribe `videos/<n>/cta-cuerpo.json`: dónde empieza el CTA de Instagram que se dice al
   final del cuerpo, con el índice de palabra de `transcripts/<n>.json` y el texto EXACTO desde
   ahí hasta el final. El CTA es la ORACIÓN entera que lleva al «comenta», no solo el
   «comenta»: `{"desde_palabra": 183, "texto": "Si quieres el prompt exacto que uso para eso,
   comenta paralelo y te lo mando por privado."}`. Lo que queda antes es el final de TikTok:
   tiene que cerrar una frase. Si el brief trae la palabra clave, búscala. Si el cuerpo no dice
   CTA: `{"desde_palabra": null}`.
5. Cada clip `cta` del pedido, lo mismo que el paso 3 con el id `<n>-cta-<plataforma>` y el
   clip como fuente: `assets/audio/<n>-cta-<p>.flac`, `transcripts/<n>-cta-<p>.json`,
   `cuts/<n>-cta-<p>.json`.
6. Las dos versiones: `scripts/preparar-version.sh <n> instagram` y `scripts/preparar-version.sh
   <n> tiktok`. Si la auditoría de respiraciones falla, arregla los cortes como dice §2 (paso
   4b) y vuelve a correrlo. Si no se puede arreglar, termina con `ERROR:`.
7. Logos: cada herramienta que se nombra lleva su logo. Los que falten, con
   `.venv/bin/python scripts/fetch-logos.py`. Si uno no se consigue, va a `avisos`.
8. Escribe `videos/<n>/propuesta.json` (formato abajo). Los beats y sus tiempos son del
   **cuerpo**, en la línea del corte (remapeados). Lo que no cuadra va a `preguntas`, con
   `opciones` y una `propuesta_por_defecto` que se pueda ejecutar sin preguntar. `versiones`
   lleva las dos, cada una con el texto del CTA que le toca (`""` si tiktok sale sin CTA).
9. `.venv/bin/python scripts/validar-propuesta.py --piece <n>`. Corrige SOLO lo reportado y repite hasta ✓.
10. Respuesta final: `Propuesta <n>: <N> beats · <P> preguntas · versiones instagram, tiktok`.

```json
{
  "pieza": 7, "generado": "2026-09-26T15:08:40", "formato": "REEL", "duracion_corte": 58.4,
  "paleta": "claro",
  "beats": [{ "id": "b1", "desde": 0.0, "hasta": 4.2, "texto": "…", "ancla": "frase exacta del transcript",
              "banda_arriba": "qué se ve", "componente": { "nombre": "tool_card", "existe": true },
              "logos": [{ "slug": "claude", "estado": "disponible" }], "material": ["pantalla-3.mov"] }],
  "preguntas": [{ "id": "q1", "beat": "b3", "pregunta": "…", "opciones": ["…", "…"],
                  "propuesta_por_defecto": "…" }],
  "versiones": [{ "plataforma": "instagram", "cta_texto": "Si quieres el prompt…, comenta PARALELO y te lo mando por privado.", "duracion": 58.4 },
                { "plataforma": "tiktok", "cta_texto": "Ve al link de mi perfil", "duracion": 57.9 }],
  "avisos": [{ "tipo": "audio | alineacion | material | formato", "mensaje": "…" }]
}
```

## Pasada `editar`

**La pieza va por `plan.json` escrito a mano (§2, paso 9), no por el EDL.** `edl-compile.py`
solo emite stages a lienzo completo: no sabe poner un visual en la banda `top`, un stage
suyo taparía al hablante (`check_band_speaker_clear`) y sus gates miden presentador *contra*
stage, lo contrario del triband. Un plan triband completo de referencia:
`tests/fixtures/videos/18/plan.json`; el fragmento de cada componente, `references/triband.md`
y `references/visuals.md` de la skill video-tech-premium.

1. Lee `videos/<n>/propuesta.json` y `VIDEOS ORIGINALES/<n>/respuestas.json`. Las respuestas
   mandan sobre la propuesta: `beats[].banda_arriba` reemplaza el texto del beat, y cada
   pregunta trae su `respuesta` (si `por_defecto: true`, el usuario no la tocó).
2. Recorridos de pantalla (paso 7) y música (paso 8) si hacen falta. La cama musical dura lo
   que la versión más larga.
3. Por cada versión (`instagram` y `tiktok`):
   - `.venv/bin/python scripts/armar-version.py palabras --piece <n> --plataforma <p>`: cada
     palabra con sus tiempos YA en la línea del corte (los que usa `build-composition.py`) y
     dónde arranca el CTA. Todo tiempo del plan sale de aquí; los de `transcripts/` están en la
     línea de la fuente y descolocan cada beat.
   - `.venv/bin/python scripts/armar-version.py anchor --piece <n> --plataforma <p>`: el
     `anchor` de los encuadres `band`. Con varias versiones, el cuerpo usa uno que valga en
     todas. Si sale `⚠`, úsalo igual y cópialo al final de tu respuesta.
4. Escribe `videos/<n>/plan-cuerpo.json`: el plan del CUERPO en segundos del corte, que son
   los mismos en todas las versiones. Lleva `format`, la `palette` del pedido, `layout`
   triband, `voice_gain`, `music`, `keywords`, `shots` (`kind: "band"` con el `anchor` del
   paso 3), `visuals` (cada beat con `band: "top"`), `sfx` y `cards`. Sin `captions`: el
   compositor trocea solo. Nada del cuerpo pasa de donde `palabras` marca el CTA.
5. Por cada versión que tiene CTA (`palabras` marca dónde empieza; si dice «sin CTA», no se
   escribe), `videos/<n>/plan-cta-<p>.json` = `{"shots": […], "visuals": […], "sfx": […]}` en
   segundos de la VERSIÓN, desde esa marca: un solo elemento visual, como pide la curva de
   intensidad (§6), con ids distintos de los del cuerpo. El CTA de Instagram dicho en el
   cuerpo va aquí, en `plan-cta-instagram.json`, no en `plan-cuerpo.json`.
6. Por cada versión: `.venv/bin/python scripts/armar-version.py plan --piece <n> --plataforma <p>` →
   color e `input-video.mp4` como dice §8 (con `out/<n>-<p>-rough.mp4`) →
   `.venv/bin/python scripts/build-composition.py --project . --piece <n>-<p>` →
   `.venv/bin/python scripts/renderizar-version.py --piece <n> --plataforma <p> --version 1`.
   Si un gate falla, corrige `plan-cuerpo.json` o `plan-cta-<p>.json` y repite desde
   `armar-version.py plan`.
7. `.venv/bin/python scripts/validar-salida.py --piece <n> --version v1`. Corrige hasta ✓.
8. Respuesta final: `Pieza <n> v1: <lista de MP4>`.

## Pasada `corregir`

1. Lee el `VIDEOS ORIGINALES/<n>/notas-v<k>.json` de `k` más alto: `{"desde": "v<k-1>", "notas": "…"}`.
2. **Una pieza de antes de las dos versiones fijas** (le falta `videos/<n>/cta-cuerpo.json` o
   `assets/face-<n>-instagram.json`): escribe `cta-cuerpo.json` (paso 4 de la propuesta), corre
   `preparar-version.sh` de las DOS versiones y, en `videos/<n>/propuesta.json`, deja
   `versiones` con las dos. Si el cuerpo decía el CTA de Instagram, lo que el plan tenía desde
   ahí sale de `plan-cuerpo.json` y va a `plan-cta-instagram.json`; si tiktok no tiene clip,
   borra `plan-cta-tiktok.json`. `armar-version.py palabras` y `anchor` (paso 3 de `editar`)
   dan los tiempos y el encuadre de la versión nueva.
3. Ajusta `plan-cuerpo.json` y/o `plan-cta-<p>.json`. No re-transcribas ni re-cortes salvo que la nota
   lo pida; si lo pide, vuelve a correr `preparar-version.sh` de las versiones afectadas.
4. Repite el paso 6 de `editar` para las DOS versiones con `--version <k>`, y valida con
   `.venv/bin/python scripts/validar-salida.py --piece <n> --version v<k>`.
5. Si una nota choca con una regla dura del CLAUDE.md (§13), aplica el resto y agrega al final
   de tu respuesta `No apliqué: <nota> — <regla>`.
6. Respuesta final: `Pieza <n> v<k>: <lista de MP4>`.
