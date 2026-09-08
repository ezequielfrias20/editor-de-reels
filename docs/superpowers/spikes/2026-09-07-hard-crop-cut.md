# Spike A — ¿el corte duro puede ser un transform sobre el wrapper?

**Fecha:** 2026-09-07 · **Tarea 8** del plan `edl-motion-design`
**Entorno:** HyperFrames CLI **0.8.31** · Chrome con GPU hardware (ANGLE Metal,
Apple M5 Pro) · fuente `out/10-rough.mp4`, 1080×1920, lienzo 1080×1920.

## La pregunta

Hoy un punch-in es un **elemento nuevo**: `shot_geometry()` devuelve una caja CSS
estática sobredimensionada con `left`/`top` negativos y el stage recorta por
desborde. Eso viene de la trampa 2 del renderer — «el rect del `<video>` se
resuelve una sola vez al cargar» — pero **nadie había probado** si un `transform`
sobre un *wrapper* del `<video>` funciona. Si funcionara, la pieza entera cabría
en **un solo decoder** en vez de los 15-16 elementos de hoy.

## El montaje

Dos proyectos hermanos y desechables en `spikes/`, con el **mismo** fuente y los
**mismos** tres encuadres (`WIDE` 1.00 a t=0 · `MEDIUM` 1.12 a t=2 · `CLOSE` 1.20
a t=4), para que la única variable sea la técnica:

| | `camera-transform/` | `camera-baseline/` |
| --- | --- | --- |
| Elementos | **1** `<video>` a 1080×1920 dentro de un `.wrap` sin `data-start` | **3** `<video>`, uno por encuadre |
| Técnica | `tl.set('#cam', {scale, x, y})` de duración cero sobre el wrapper | caja sobredimensionada estática, sin animar nada |

El anclaje vertical se traduce con `y = -H · (zoom - 1) · (anchor - 0.5)`, que
reproduce el `top = -(h - H) · anchor` de `shot_geometry()`. Con `anchor` 0.42:
`y` = 0 · 18.4320 · 30.7200 px.

## Las tres respuestas

### (a) El mismo instante pedido dos veces → ¿bytes idénticos? — **SÍ**

```
snapshot --at 5.0,5.0   frame-00  ca9b8ee9c94c4ce1…
                        frame-01  ca9b8ee9c94c4ce1…   ← idéntico
snapshot (proceso aparte, --at 2.5,5.0)  frame-01  ca9b8ee9c94c4ce1…   ← idéntico
```

SHA-256 iguales **dentro del mismo proceso y entre procesos distintos**. El
transform no introduce no-determinismo.

### (b) ¿Se ve el frame del vídeo, o el transform rompió la inyección? — **SE VE**

El frame sale con el sujeto correctamente reencuadrado. La clave es que el
wrapper **no lleva `data-start`**: la trampa 3 congela la media anidada en un
elemento *temporizado*, no en un `<div>` normal. Diferencia contra el baseline en
el mismo instante: **MAE 0.681** a `MEDIUM` y **0.215** a `CLOSE` (t=1 s, donde
ninguna de las dos rutas escala, sale **MAE 0.000**: bit a bit).

### (c) Nitidez a CLOSE contra la caja sobredimensionada — **EMPATE, con una condición**

ROI fija de 486×486 sobre la cara, idéntica en las dos rutas (comparar dos cajas
Haar distintas mezcla nitidez con tamaño de caja y no mide nada):

| | Laplaciano.var | Tenengrad | Ratio de alta frecuencia |
| --- | --- | --- | --- |
| **`MEDIUM` 1.12** | −0.28 % | −0.03 % | −0.19 % |
| **`CLOSE` 1.20** | **+0.79 %** | +0.10 % | +0.26 % |

Todo por debajo del 1 %: ruido. La ruta del transform **no ablanda la cara**.

> ⚠ **La condición, y es el hallazgo que más valor tiene de este spike.** En el
> primer montaje el wrapper llevaba `will-change: transform`, y con él la cara
> salía **claramente más blanda**: Laplaciano **−29.6 %** a `MEDIUM` y **−9.8 %** a
> `CLOSE`. La promoción de capa hace que Chrome rasterice a 1× y escale el ráster
> ya compuesto — un **doble remuestreo**. Sin `will-change`, el compositor escala
> la textura decodificada una sola vez, igual que la caja sobredimensionada.
>
> Cualquier cosa que promueva la capa del wrapper (`will-change`, `filter`,
> `backdrop-filter`) reintroduce la pérdida **sin avisar y sin verse en el
> navegador**. Si esta ruta se adopta, eso es un check de lint, no una nota.

## Decisión

Las tres pasan → según la tabla de la Tarea 8:

> **Un vídeo + sets en el wrapper.** Un decoder para toda la pieza.

**Lo que este spike NO ha probado**, y hay que cubrir antes de migrar:

1. Solo se ha medido `tl.set` de duración cero — el **corte duro**. El
   `punch-zoom` animado sobre el wrapper es otro camino de rasterizado.
2. Un solo `<video>` continuo. La pieza real tiene tramos `off`, `split` y `pip`,
   que hoy son elementos con geometría propia.
3. `check_no_black()` razona sobre encuadres como elementos. Con un solo vídeo
   persistente, la pregunta que contesta cambia de forma.

**Por eso la Tarea 8 no migra nada.** La arquitectura de un `<video>` por
encuadre lleva 4 piezas publicadas y se conserva; lo que queda registrado es que
la puerta está abierta y con qué condición. La migración es trabajo aparte, con
su propia verificación sobre el MP4 y no sobre el HTML.
