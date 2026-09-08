# Spike B — ¿Three.js es determinista bajo `hf-seek`?

**Fecha:** 2026-09-08 · **Tarea 14** del plan `edl-motion-design`, fuera del camino crítico.
**Entorno:** HyperFrames CLI **0.8.31** · Chrome con GPU hardware (ANGLE Metal, Apple M5
Pro) · adaptador `three` documentado en
`.agents/skills/hyperframes-animation/adapters/three.md` · Three.js **0.181.2** vía CDN
(`jsdelivr` ESM).

## La pregunta

El vocabulario de objetos del proyecto es 2.5D por diseño (SVG + `perspective()` +
`rotateY()` estáticos, ver `objects.py`). El 3D real con Three.js siempre fue un extra
posible para momentos héroe — nunca el camino principal — y nadie había probado si
sobrevive al contrato de determinismo del proyecto: **mismo instante pedido dos veces →
mismos bytes, siempre**, que es la base de todo el pipeline (`edl-compile.py` →
`build-composition.py` → render).

## El montaje

`spikes/three-determinism/` (desechable, fuera de git): lienzo REEL 1080×1920,
`data-duration="3.0000"` explícito en la raíz (el adaptador `three` **no infiere
duración** — sin esto el render falla con «Composition has zero duration», documentado en
el propio adapter). Un icosaedro (`IcosahedronGeometry`, subdivisión 4) rotando en
`rotation.y`/`rotation.x` como función pura de `time`, recibido por el evento `hf-seek` —
nunca `Date.now()`, `performance.now()` ni `requestAnimationFrame` como fuente de verdad.

`npx hyperframes lint` pedía además `data-no-timeline` en la raíz (sin GSAP no hay
`window.__timelines` que registrar, y sin el atributo el productor espera 45 s de sondeo
por nada). Con eso: **0 errores, 0 warnings.**

## Las tres respuestas

### (1) El mismo frame dos veces → ¿bytes idénticos? — **SÍ**

```
snapshot --at 1.5,1.5           frame-00  233ad84a78e4…
                                 frame-01  233ad84a78e4…   ← idéntico
snapshot (proceso aparte, --at 1.5)   frame-00  233ad84a78e4…   ← idéntico
```

SHA-256 iguales dentro del mismo proceso **y** entre procesos separados. `renderAt(time)`
como función pura de `time` es suficiente — Three.js/WebGL no meten no-determinismo propio
aquí (nada de física, nada de partículas con estado, nada de post-procesado dependiente de
frames previos).

### (2) `data-duration` manual se respeta — **SÍ**

```
render → 90 frames capturados (3.0 s × 30 fps), sin fallo de "zero duration"
ffprobe -show_entries format=duration  →  3.000000
```

Exacto, sin redondeo perdido.

### (3) WebGL no revienta con la memoria justa — **SÍ**

Render completo de 90 frames a 1080×1920 (`nb_frames=90`, confirmado con `ffprobe`), sin
OOM, sin frames corruptos ni pérdida de contexto WebGL. Frames 0/45/89 inspeccionados:
rotación consistente y visible entre ellos (la silueta facetada del icosaedro gira), sin
un solo frame verde/negro/congelado. 366 KB para 3 s a densidad de píxel 1 — nada que
sugiera presión de memoria a esta escala.

## Decisión

Las tres pasan → según la tabla de la Tarea 14:

> El 3D real **puede** entrar como opción para momentos héroe, con el patrón documentado
> en `hyperframes-animation/adapters/three.md` (tiempo desde `hf-seek`, nunca reloj de
> pared; `data-duration` siempre explícito; assets cargados antes del primer seek).

**Lo que este spike NO ha probado**, y habría que cubrir antes de usar Three.js en una
pieza real:

1. Solo un material `MeshStandardMaterial` liso y una luz. Nada de `GLTFLoader`,
   `AnimationMixer`, ni texturas/HDRIs cargados de red — esas rutas tienen su propio
   riesgo de no-determinismo (`assets cargados antes del seek`, no en el momento del seek).
2. Una sola malla. Una escena con partículas, múltiples mallas o post-procesado
   necesitaría su propia comprobación de determinismo — el compositor puede introducir
   dependencia del historial de frames que aquí no existe.
3. No se probó **en composición**, mezclado con el resto del stack (GSAP, capas HTML,
   subtítulos) — solo aislado. Un `<canvas>` de Three.js conviviendo con las 8 capas del
   stage (§10 de `CLAUDE.md`) es una integración aparte.

**Por eso este spike no cambia nada del vocabulario de objetos actual.** El 2.5D sigue
siendo la estrategia principal, no un plan B — este resultado solo confirma que la puerta
al 3D real está abierta para cuando un momento héroe concreto lo justifique, con el patrón
exacto a seguir cuando llegue ese día.
