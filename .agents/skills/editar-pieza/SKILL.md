---
name: editar-pieza
description: Edita SIN PREGUNTAR una pieza pedida desde el dashboard Cubo Marketing, en tres pasadas (propuesta, editar, corregir). La lanza el dashboard con `Codex -p "/editar-pieza <n> <pasada>"`; nadie mira la conversación. Para editar conversando con el usuario se usa video-tech-premium, no esta.
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

**La doctrina es la del `AGENTS.md` de este proyecto** y se aplica completa: tres formatos en REEL
(`cara`, `partida`, `grafico`, §4 y `references/formatos.md` de la skill video-tech-premium),
mostrar sin escribir (§7), la banda de arriba de `partida` nunca vacía, nada entra antes de su palabra, cambio
de formato o de visual cada 1–3 s, logo de cada herramienta que se nombra, los gates de `build-composition.py`, sonido (§12),
color si es HDR (§8), trampas del renderer (§9). Léelo antes de escribir la propuesta o el
plan. Esta skill solo dice el ORDEN y los ARCHIVOS de una pieza del dashboard.

## La pieza

- `VIDEOS ORIGINALES/<n>/pedido.json`: título, `origen`, `prompt` (puede estar vacío),
  `paleta` y los clips con su rol (`cuerpo` en `orden`, `cta` con `plataforma`, `pantalla`,
  `apoyo`). Lo escribe el dashboard; no lo toques.
- **Sale `<n>-instagram` siempre y `<n>-tiktok` SOLO si el pedido trae el clip `cta` de
  tiktok** (regla de Ezequiel, 2026-10-05). Sin ese clip no se hace la versión de TikTok:
  ni se prepara, ni se planea, ni se renderiza. Las versiones que salen las da
  `Pedido.plataformas` (`scripts/pieza.py`).
  El cuerpo suele cerrar con el CTA de Instagram dicho a cámara («Si quieres el prompt,
  comenta PARALELO y te lo mando por privado»). Cada versión toma el cuerpo HASTA la palabra
  «comenta» (la promesa «Si quieres…» es común) y le suma el suyo:
  - **instagram**: el clip `cta` de instagram si se subió; si no, el CTA que se dijo en el cuerpo.
  - **tiktok**: el clip `cta` de tiktok (el «comenta…» es de ManyChat, solo Instagram). Sin
    clip, no hay versión de TikTok.
  `scripts/armar-version.py` hace ese recorte; tú solo anotas dónde empieza el CTA dicho
  (paso 4 de la propuesta).
- Si `prompt` es un brief de `plan-edicion` (empieza con `Video fuente:`), úsalo como en el
  paso 3b: sus anclas se cuadran con el transcript y cada momento trae su formato,
  fondo y visual: se respetan. Lo que el editor no tenga todavía, se construye (o va como pregunta si
  pediría un servicio pago).

## Pasada `propuesta`

1. `.venv/bin/python scripts/unir-cuerpo.py --piece <n>` → `out/<n>-fuente.mov`. Si sale `ERROR:`, termina con ese error.
2. `scripts/detect-format.sh out/<n>-fuente.mov`. Si no decide (casi cuadrada), termina con `ERROR:`.
3. Cuerpo, pasos 1–3 del pipeline con `<n>`: audio → `.venv/bin/python scripts/transcribe.py` →
   `.venv/bin/python scripts/refine-timings.py … --write` → `.venv/bin/python scripts/plan-cuts.py … --audio …`.
   Revisa los avisos de `refine-timings` como dice §2 (re-transcribir un tramo si hace falta).
4. Escribe `videos/<n>/cta-cuerpo.json`: dónde empieza el CTA de Instagram que se dice al
   final del cuerpo, con el índice de palabra de `transcripts/<n>.json` y el texto EXACTO desde
   ahí hasta el final. **El corte va en la palabra «comenta»**, no al principio de la oración
   (regla de Ezequiel, 2026-10-05): en «Si quieres el prompt exacto que uso para eso, comenta
   paralelo y te lo mando por privado.» es `{"desde_palabra": 190, "texto": "comenta paralelo
   y te lo mando por privado."}`. La promesa de delante («Si quieres el prompt exacto que uso
   para eso,») es PARTE COMÚN: sale en las dos versiones, y en TikTok el clip de CTA («ve al
   link de la bio») entra justo donde se iba a decir «comenta». `armar-version.py` rechaza un
   `desde_palabra` que no caiga en «comenta». Si el brief trae la palabra clave, búscala. Si el
   cuerpo no dice CTA: `{"desde_palabra": null}`.
5. Cada clip `cta` del pedido, lo mismo que el paso 3 con el id `<n>-cta-<plataforma>` y el
   clip como fuente: `assets/audio/<n>-cta-<p>.flac`, `transcripts/<n>-cta-<p>.json`,
   `cuts/<n>-cta-<p>.json`.
6. Cada versión que sale: `scripts/preparar-version.sh <n> instagram` y, si hay clip de TikTok,
   `scripts/preparar-version.sh <n> tiktok`. Si la auditoría de respiraciones falla, arregla los cortes como dice §2 (paso
   4b) y vuelve a correrlo. Si no se puede arreglar, termina con `ERROR:`.
7. Logos: cada herramienta que se nombra lleva su logo. Los que falten, con
   `.venv/bin/python scripts/fetch-logos.py`. Si uno no se consigue, va a `avisos`.
8. Escribe `videos/<n>/propuesta.json` (formato abajo). Los beats y sus tiempos son del
   **cuerpo**, en la línea del corte (remapeados). Lo que no cuadra va a `preguntas`, con
   `opciones` y una `propuesta_por_defecto` que se pueda ejecutar sin preguntar. `versiones`
   lleva las versiones que salen, cada una con el texto del CTA que le toca (sin clip de
   TikTok, solo `instagram`).
9. `.venv/bin/python scripts/validar-propuesta.py --piece <n>`. Corrige SOLO lo reportado y repite hasta ✓.
10. Respuesta final: `Propuesta <n>: <N> beats · <P> preguntas · versiones <las que salen>`.

```json
{
  "pieza": 7, "generado": "2026-09-26T15:08:40", "formato": "REEL", "duracion_corte": 58.4,
  "paleta": "claro",
  "beats": [{ "id": "b1", "desde": 0.0, "hasta": 4.2, "texto": "…", "ancla": "frase exacta del transcript",
              "formato": "partida", "fondo": "claro", "visual": "qué objeto aparece y qué hace",
              "logos": ["Codex"], "material": ["pantalla-3.mov"] }],
  "preguntas": [{ "id": "q1", "beat": "b3", "pregunta": "…", "opciones": ["…", "…"],
                  "propuesta_por_defecto": "…" }],
  "versiones": [{ "plataforma": "instagram", "cta_texto": "comenta PARALELO y te lo mando por privado.", "duracion": 58.4 },
                { "plataforma": "tiktok", "cta_texto": "Ve al link de mi perfil", "duracion": 57.9 }],
  "avisos": [{ "tipo": "audio | alineacion | material | formato", "mensaje": "…" }]
}
```

Cada beat lleva `"formato"` (`cara` · `partida` · `grafico`), `"fondo"` (`claro` · `oscuro` · `comic`, no va con `cara`) y `"visual"` (vacío solo con `cara`). Mientras el fondo por escena no esté en el compilador, la pieza sale en la paleta del pedido: el `fondo` se anota igual.

## Pasada `editar`

**La pieza va por `plan.json` escrito a mano (§2, paso 9), no por el EDL.** `edl-compile.py`
solo emite stages a lienzo completo: no sabe poner un visual en la banda de arriba. El plan
va en tres formatos; la geometría, los encuadres de cada formato y un plan de ejemplo están
en `references/formatos.md` de la skill video-tech-premium, y el fragmento de cada
componente en `references/visuals.md`.

1. Lee `videos/<n>/propuesta.json` y `VIDEOS ORIGINALES/<n>/respuestas.json`. Las respuestas
   mandan sobre la propuesta: `beats[].formato` y `beats[].visual` reemplazan los del beat, y cada
   pregunta trae su `respuesta` (si `por_defecto: true`, el usuario no la tocó).
2. Recorridos de pantalla (paso 7) y música (paso 8) si hacen falta. La cama musical dura lo
   que la versión más larga.
3. Por cada versión que sale (`instagram` y, si hay clip, `tiktok`):
   - `.venv/bin/python scripts/armar-version.py palabras --piece <n> --plataforma <p>`: cada
     palabra con sus tiempos YA en la línea del corte (los que usa `build-composition.py`) y
     dónde arranca el CTA. Todo tiempo del plan sale de aquí; los de `transcripts/` están en la
     línea de la fuente y descolocan cada beat.
   - `.venv/bin/python scripts/armar-version.py anchor --piece <n> --plataforma <p>`: el
     `anchor` de los encuadres `band`. Con varias versiones, el cuerpo usa uno que valga en
     todas. Si sale `⚠`, úsalo igual y cópialo al final de tu respuesta.
4. Escribe `videos/<n>/plan-cuerpo.json`: el plan del CUERPO en segundos del corte, que son
   los mismos en todas las versiones. Lleva `format`, la `palette` del pedido, `layout`
   `{"mode": "formatos"}`, `voice_gain`, `music`, `keywords`, `shots` (cada beat según su formato:
   `partida` = `kind: "band"` con el `anchor` del paso 3; `cara` = `kind: "full"` con zoom;
   `grafico` = `kind: "off"`), `visuals` (en `partida` con `band: "top"`; en `grafico` sin `band`), `sfx` y `cards`. Sin `captions`: el
   compositor trocea solo. Nada del cuerpo pasa de donde `palabras` marca el CTA. La promesa
   del CTA («Si quieres el prompt…,») es el último tramo del CUERPO: va aquí, sale igual en
   las dos versiones, y en TikTok la sigue directo el clip del link.
5. Por cada versión que tiene CTA (`palabras` marca dónde empieza; si dice «sin CTA», no se
   escribe), `videos/<n>/plan-cta-<p>.json` = `{"shots": […], "visuals": […], "sfx": […]}` en
   segundos de la VERSIÓN, desde esa marca: un solo elemento visual, como pide la curva de
   intensidad (§6), con ids distintos de los del cuerpo. El CTA de Instagram dicho en el
   cuerpo, desde «comenta», va aquí, en `plan-cta-instagram.json`, no en `plan-cuerpo.json`. Si el CTA dice una
   palabra clave («comenta MARCA»), agrega `"cta_palabra": {"texto": "MARCA", "desde": <s>,
   "hasta": null}` con `desde` en la palabra, en segundos de la versión. El CTA va en `cara`
   (encuadre `full`): sobre un encuadre `band` la compilación para.
6. Por cada versión: `.venv/bin/python scripts/armar-version.py plan --piece <n> --plataforma <p>` →
   `.venv/bin/python scripts/input-video.py --piece <n> --plataforma <p>` (voz limpia, §12; con
   `--lut` si la fuente es HDR, §8) →
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
   `preparar-version.sh` de las versiones que salen y, en `videos/<n>/propuesta.json`, deja
   `versiones` con esas. Si el cuerpo decía el CTA de Instagram, lo que el plan tenía desde
   ahí sale de `plan-cuerpo.json` y va a `plan-cta-instagram.json`; si tiktok no tiene clip,
   no hay versión de TikTok: borra `plan-cta-tiktok.json`. `armar-version.py palabras` y `anchor` (paso 3 de `editar`)
   dan los tiempos y el encuadre de la versión nueva.
3. Ajusta `plan-cuerpo.json` y/o `plan-cta-<p>.json`. No re-transcribas ni re-cortes salvo que la nota
   lo pida; si lo pide, vuelve a correr `preparar-version.sh` de las versiones afectadas.
4. Repite el paso 6 de `editar` para cada versión que sale con `--version <k>`, y valida con
   `.venv/bin/python scripts/validar-salida.py --piece <n> --version v<k>`.
5. Si una nota choca con una regla dura del AGENTS.md (§13), aplica el resto y agrega al final
   de tu respuesta `No apliqué: <nota> — <regla>`.
6. Respuesta final: `Pieza <n> v<k>: <lista de MP4>`.
