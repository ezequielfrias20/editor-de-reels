# Creative Planner + Asset Resolver — el contrato

El producto final no debería requerir escribir a mano el EDL de cada pieza. Esta
referencia fija dónde acaba el criterio y empieza el determinismo.

```
video → transcript → [Creative Planner]  → videos/<n>/edl.draft.json
                   → [Asset Resolver]    → (assets resueltos)
                   → [CORE validation]   → videos/<n>/edl.json      ← contrato congelado
                   → [edl-compile.py]    → videos/<n>/plan.json
                   → [build-composition] → public/index.html
                   → [hyperframes render]→ output.mp4
```

## La frontera de determinismo

| Capa | Decide | Determinista |
| --- | --- | --- |
| **Creative Planner** (LLM o humano) | **QUÉ** editar | ❌ — y está bien |
| **Asset Resolver** | **CON QUÉ** recurso | ⚠ cachea, así que es reproducible tras la primera resolución |
| **`edl.json`** | el contrato congelado | **— es el límite** |
| **`edl-compile.py`** | **CÓMO** se vuelve valores | ✅ |
| **build-composition + renderer** | ejecuta | ✅ |

**Mismo `edl.json` + mismo transcript + mismos assets resueltos + mismo style profile =
mismo `plan.json`, byte a byte.** Todo lo anterior a `edl.json` puede variar entre corridas;
todo lo posterior, no.

## Dos archivos, no uno

| | `edl.draft.json` | `edl.json` |
| --- | --- | --- |
| Lo produce | Creative Planner (o un humano) | Asset Resolver + validación CORE |
| Assets | **Semánticos**: `"clock"`, no `"object:clock@1"` | **Solo referencias resueltas y versionadas** |
| Estado | Candidato, editable, se puede regenerar | **Contrato congelado** |
| ¿Lo acepta `edl-compile.py`? | **No** — `load_edl` rechaza cualquier `*.draft.json` | **Sí, y solo este** |
| Determinista | ❌ | ✅ desde aquí en adelante |

El draft se versiona en git igual que el EDL final: es el registro de qué propuso el
Planner frente a qué se aprobó, y es lo que permite mejorar el Planner comparando ambos.

> **El Planner no es una autoridad, es un candidato.** El EDL draft pasa por
> `asset_resolve.resolve_edl()` y por exactamente el mismo CORE (`edl_schema.load_edl`) que
> un EDL escrito a mano. Eso es lo que hace seguro que sea no determinista: nada de lo que
> produce se acepta sin validar. Y su salida es un archivo editable — el Planner
> **acelera, no sustituye**.

## Entrada y salida del Creative Planner

**Entrada:** transcript remapeado (con índices de palabra), style profile, y opcionalmente
`GUION.MD` y notas de la pieza.

**Salida:** un EDL draft — los mismos campos que el EDL final, salvo que el `asset` de
cada `OBJECT_IN` es **semántico** (`"clock"`, `"calendar"`), todavía no una referencia
resuelta. Genera `semanticIntent` · `sceneType` · `representationType` · `camera` ·
`events` (con `atWord`) · `keyword` · `asset` semántico · `state` · `preset` solicitado ·
`transitionIn`/`transitionOut` · `sfx: "auto"` opt-in · `reason`.

### Las cuatro restricciones

1. **No inventa palabras.** Solo referencia índices de palabra que existen en el transcript.
2. **No fija tiempos.** Solo `atWord` + `offset` — nunca un float copiado a mano. El
   compilador es quien remapea a la línea del corte y cuantiza a frame.
3. **No fija dB, ni px, ni coordenadas.** Esas cifras salen de medir el metraje
   (`measure-face.py`), de `tokens.py`, o de la fórmula de volumen — nunca de una
   estimación del Planner.
4. **Rellena `reason` con una razón real.** La lista negra de `edl_schema.py` (§1, el
   filtro anti-decoración: «para mantener la atención», «para dar dinamismo», «para que
   no sea aburrido»…) le aplica exactamente igual que a un EDL escrito a mano — es un
   `warning`, no una excepción para el Planner.

## Asset Resolver

Convierte el `asset` semántico de cada evento en una referencia concreta y cacheada, con
**prioridad estricta — reutilizar antes que generar** (`asset_resolve.PRIORIDAD`):

| # | Nivel | Ejemplo de salida |
| --- | --- | --- |
| 1 | `library` | `object:clock@1` — ya existe en `objects.REGISTRY` |
| 2 | `configurable` | `object:clock@1?face=roman` — mismo objeto, otra variante |
| 3 | `recording` | `recording:screen-tour-2#seg1` — metraje propio ya capturado |
| 4 | `generated` | `gen:calendar-premium@1` — IA, con ledger (`assets/gen/ledger.json`) |
| 5 | `broll` | `broll:clinic-reception@3` — licenciado, buscado o generado |

Solo se baja de nivel cuando el de arriba no puede servir la petición, y **siempre se
anota por qué**: `resolvedVia` + `resolveReason` en el propio evento. Sin ese rastro,
dentro de tres meses no se sabe si un `gen:` existe porque hacía falta o porque nadie miró
la librería primero.

Las referencias son **estables, versionadas e inmutables**: `@1` nunca se edita en sitio.
Rediseñar el reloj crea `object:clock@2`, porque cambiar un asset en silencio modificaría
renders históricos — una pieza publicada hace tres meses tiene que poder re-renderizarse
idéntica. `assets/manifest.json` guarda el hash de cada referencia (`asset_hash()`,
definido por el código fuente de la función en `objects.py`, no por lo que el manifest
*dice* que es) y `manifest-sync.py` falla si un `@n` existente cambió.

## El compilador falla si llega un asset sin resolver

Regla dura, en CORE (`edl_schema._check_assets`): **todo `asset` de evento tiene que
llegar resuelto, existir en el manifest y tener el hash que el manifest dice.** Si
`edl-compile.py` recibe un semántico a secas, un asset ausente del manifest, o un hash que
ya no cuadra, **falla antes de escribir nada**. No busca, no diseña, no elige un sustituto
parecido, no improvisa — es la frontera de §9 (`edl_compile.py`) aplicada a los assets: el
compilador no elige nunca.

## Metadata de trazabilidad — no entra en compilación

```jsonc
"planner": {
  "plannerVersion": "0.1.0",
  "styleProfile":   "motion-explainer",
  "promptVersion":  "2026-09-07-a",
  "generatedAt":    "2026-09-07T14:22:03Z"    // ← excluido del hash creativo
}
```

Ninguno de estos campos entra en el `plan.json` ni afecta a una sola decisión de
compilación — `Edl.planner` (el dataclass) los guarda tal cual, sin interpretarlos.

**Hash creativo** (`edl_compile.creative_hash`): `sha256` del EDL canonicalizado (claves
ordenadas, separadores fijos) **sin** `planner.generatedAt` y **sin** las claves que
empiezan por `_` (la misma convención de comentario que documenta
`references/plan-schema.md` para `plan.json`). Identifica «esta decisión creativa», no
«estos bytes exactos»: dos corridas del Planner sobre el mismo transcript que produjeran
el mismo EDL, solo con `generatedAt` distinto, tienen el MISMO hash creativo. Sin esa
exclusión la prueba de determinismo sería inútil — todo cambiaría de hash en cada corrida
por el reloj de pared, nunca por una decisión real.

El hash del **manifest** (`compile_report`, Tarea 12) es una pregunta distinta —«¿son los
mismos píxeles?»— y nunca entra en el hash creativo: mezclarlas invalidaría el hash
creativo de toda pieza vieja cada vez que se añade un objeto nuevo a la librería.

## `edl-plan.py` — el andamiaje determinista, no el Planner

```bash
scripts/edl-plan.py --project . --piece 12 --palette claro|oscuro [--style motion-explainer]
```

Escribe un `edl.draft.json` **mínimo y honesto**: un segmento `A_ROLL` por frase del
transcript (dividido en los signos de puntuación que ya trae AssemblyAI), con un único
`CAPTION` que cubre todo el rango de palabras y `reason: "borrador sin revisar — decidir
sceneType, objetos y cámara"`. **No elige `MOTION_STAGE`, no asigna objetos, no resalta
keywords** — esas son las decisiones no deterministas de verdad, y este script no las
toma por nadie. Es el punto de partida mecánico que un agente o un humano termina de
editar; el primer EDL completo (hoy la fixture `tests/fixtures/videos/10/edl.json`) se
escribió sin este andamiaje, a mano, palabra por palabra — `edl-plan.py` ahorra exactamente esa parte repetitiva, no la
parte creativa.
