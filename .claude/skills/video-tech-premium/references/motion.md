# Movimiento

Cargar **`/motion-doctrine` antes de animar** si está disponible. Lo de aquí es lo
específico de este sistema.

---

## Los dos principios

**1 · El movimiento actúa, no respira.** Prohibido el wobble ocioso. Si un elemento se
mueve, es porque algo pasa en ese instante. Quietud antes del clímax.

**2 · Si un elemento representa algo que se dice, su tiempo sale del transcript.** Nunca
de un escalonado decorativo. Es el error que más rápido se cuela porque la composición
valida, se ve bien en un frame suelto y solo se nota viendo el MP4 entero.

---

## El corte duro es la transición por defecto

Este sistema **no usa paquetes de transiciones**. El vocabulario es:

| Transición | Cómo se hace |
| --- | --- |
| corte duro | dos encuadres consecutivos: un `<video>` termina, otro empieza |
| zoom cut | corte duro entre dos encuadres con zoom distinto |
| push | un takeover con `fade_in` corto (~0.14 s) |
| fundido cruzado | el encuadre se queda hasta `start + fade_in` del takeover |

**El punch-in es un corte, no un tween.** El renderer resuelve el rect del `<video>` una
sola vez al cargar, así que animar la geometría no reescala la imagen. Cada encuadre es un
elemento nuevo con su caja sobredimensionada.

Escala de encuadres: **1.00 · 1.05 · 1.09 · 1.12 · 1.15**. El 1.15 es escaso.

---

## Entradas: manda la opacidad

Todo contenedor entra por **opacidad**; lo que se mueve es el contenido de dentro. El
recorrido y la escala de entrada son **pequeños**. Si un elemento entra desde `scale:
0.72` se está anunciando; desde `0.955`, simplemente llega.

### Vocabulario de eases — sin muelles

`back.out()` rebota como un resorte: se lee bien, pero es lenguaje de dibujo animado y
choca con una pieza de producto. **Ninguna entrada lo usa.**

| Gesto | Ease | Entra desde | Por qué |
| --- | --- | --- | --- |
| `punch` (titular) | `expo.out` | escala 1.045, y −8 | Frena muy fuerte al final, como se para algo con masa |
| `stamp` (sello, cifra, tarjeta de app) | `power3.out` | escala 1.10 | Una prensa baja y para en seco |
| `rise-in` (panel grande) | `power3.out` | y +26, escala 0.985 | Sube poco y aterriza en plano |
| `chip-in` (pastilla, nodo, badge) | `power2.out` | escala 0.94, y +8 | Aparece, no salta |
| `slide-in` (kicker, HUD) | `power2.out` | y +14 | El desplazamiento solo acompaña al fundido |
| `box-in` (caja delimitadora) | `power3.out` | escala 1.06 | Se clava sobre el punto de interés |
| `scale-pop` | `power2.out` | escala 0.955 | |
| `cam-push` / `cam-kb` | `power2.inOut` / `none` | — | Empuje pegado a un beat · Ken Burns continuo |

**El peso manda en la duración.** Un visual a pantalla completa tarda más en aparecer que
una tarjeta porque es más grande.

---

## Subtítulos

El bloque **entra entero y se queda quieto** (0.14 s, `power2.out`, desde escala 0.97).
Lo único que se mueve dentro es la **keyword**: su pastilla violeta entra en 0.16 s
justo en el instante en que se pronuncia la palabra, y el texto da un pulso de 1.06.

Resaltar palabra a palabra —el karaoke del sistema anterior— convierte el subtítulo en un
metrónomo y el ojo deja de leer el contenido.

---

## Movimiento de los mockups

| Tipo | Qué es |
| --- | --- |
| `stamp` | una herramienta o una cifra se **sella** al nombrarse |
| `draw` | una conexión se **dibuja** al nombrarse el módulo |
| `type-word` | el CTA se **teclea** solo, carácter a carácter |
| `click` + `cursor-to` | el puntero **actúa** sobre el producto real |
| `box-in` | la caja **dirige la mirada** al punto exacto que se nombra |

`type-word` se escribe con un `tl.set` por carácter en su propio instante, no con un
`onUpdate`: así el estado no depende de por dónde iba la reproducción y el render es
determinista y seek-safe.

Dos tweens sobre la misma propiedad del mismo elemento (dos clics seguidos sobre un
cursor) necesitan `overwrite: "auto"`.

---

## La curva de intensidad

| Tramo | Qué hace |
| --- | --- |
| **Hook** (0–3 s) | lo más agresivo de la pieza: encuadre cerrado, takeover, corte duro en el remate |
| **Cuerpo** | alterna descansos (zoom 1.00, plano abierto) con picos (1.06–1.09) |
| **Puntos importantes** | vuelve a subir: cifra grande, sello, impacto |
| **Clímax** | quietud justo antes |
| **CTA** | se simplifica. Un solo elemento en pantalla |

Un cambio de imagen cada **1–2.5 s**, contando encuadres, entradas de tarjeta, beats de
mockup y bloques de subtítulo — no solo los cortes de metraje.
