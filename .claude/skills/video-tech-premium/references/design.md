# Sistema visual — grafito profundo + violeta eléctrico

Estilo: **contenido educativo premium de tecnología, IA y negocios**. Fondo casi negro,
superficies flotando encima con hairline claro y sombra ancha, tipografía grotesca pesada
y un único acento violeta de alto voltaje por frame.

La fuente de verdad es `scripts/tokens.py`. Un cambio ahí se propaga a toda la pieza.

---

## Color

El violeta no es decorativo: sale del **producto real** que se muestra en pantalla (el
ERP). Así el gráfico y el screenshot pertenecen al mismo mundo en vez de convivir a la
fuerza. Si en otra pieza el producto tiene otro color de marca, el acento se cambia aquí
y el sistema entero se recoloca.

```
/* — suelo — */
--bg:        #0B0C10   grafito profundo, con una pizca de azul
--bg2:       #101218   borde del viñeteado
--surface:   #16181F   tarjeta / panel
--surface2:  #1D2029   elevado (fila activa, celda destacada)
--surface3:  #252935   bordes internos de UI, tracks de barra

/* — texto — */
--text:      #FFFFFF
--text2:     #A7ADBB   secundario
--text3:     #8C93A3   metadatos

/* — acento (voltaje) — */
--violet:    #7C5CFF   PRIMARIO: fills, barras, pastillas, keyword
--violet-hi: #9B85FF   el violeta cuando es TEXTO sobre oscuro
--violet-dk: #5B3FD6   profundidad

/* — señal — */
--go:        #34E39B   resuelto · conectado · CTA
--alert:     #FF5A5A   problema · desconectado
--warn:      #FFB84D
```

**Nada de negro puro (#000) ni blanco puro como fondo.** El #0B0C10 deja respirar los
oscuros del metraje en vez de aplastarlos.

**Regla de escasez:** un solo momento violeta de alto voltaje por frame. Si la keyword del
subtítulo lleva pastilla violeta, el titular de la tarjeta no la lleva.

### Contrastes ya verificados — no repetir el error

| Combinación | Ratio | Uso |
| --- | --- | --- |
| blanco / bg | 19.55:1 | ✅ todo |
| blanco / surface | 17.73:1 | ✅ todo |
| text2 / surface | 7.88:1 | ✅ texto pequeño |
| **text3 / surface** | **5.76:1** | ✅ ya aguanta texto pequeño |
| violet / bg | 4.50:1 | solo texto grande |
| **violet-hi / bg** | **6.70:1** | ✅ el violeta cuando es TEXTO |
| blanco / violet | 4.35:1 | solo ≥24 px y en negrita |
| bg / go | 11.74:1 | sobre verde va tinta, **no blanco** |
| blanco / alert | 3.06:1 | solo texto grande |

`tokens.contrast(a, b)` mide cualquier par nuevo antes de renderizar, que es cuando cuesta
barato.

---

## Tipografía

**Dos familias.** Una tercera es lo que hace que una pieza parezca un collage.

| Rol | Familia | Notas |
| --- | --- | --- |
| Todo el texto | **Inter** 400–900 | 900 para titulares y subtítulos |
| Etiquetas de UI, datos, chips | **JetBrains Mono** 400/700 | uppercase, tracking amplio |

Cuanto más grande el texto, **más se cierra el tracking**. Es lo que hace que un titular
pesado se lea como un producto y no como un cartel.

| Rol | REEL px | YOUTUBE px | tracking |
| --- | --- | --- | --- |
| chip | 26 | 22 | `.16em` |
| label | 24 | 20 | `.12em` |
| body | 34 | 29 | `0` |
| card-title | 52 | 44 | `-.02em` |
| headline | 96 | 80 | `-.032em` |
| display | 132 | 112 | `-.038em` |
| hero-num | 200 | 168 | `-.04em` |
| caption | 66 | 54 | `-.02em` |

Las 8 woff2 están vendorizadas y verificadas en `assets/fonts/` (glifos del español
comprobados con fontTools). Se regeneran con `scripts/fetch-fonts.py`.

⚠ **Trampa de Google Fonts:** el CSS devuelve varios `@font-face` por familia y el
**primero es el cirílico** — quedarse con el primer `src` baja un subset sin una sola
tilde. Hay que elegir el bloque cuyo `unicode-range` contenga `U+0000-00FF`.
`fetch-fonts.py` ya lo hace y lo verifica.

---

## Superficie y elevación

- Fondo: `vignette()` — radial de `bg2` a `bg` a `#07080B`. Empuja la mirada al centro;
  sin él un 1080×1920 de color plano se ve muerto.
- `grid()` — rejilla técnica a `rgba(255,255,255,.022)` cada 72 px. Casi invisible; le da
  al fondo textura de plano en vez de degradado de plantilla.
- **Hairline claro** (`rgba(255,255,255,.09)`) como único borde. Sobre fondo oscuro una
  sombra negra no se ve: la elevación la dan la sombra *y* el hairline.
- Sombra: `0 2px 6px rgba(0,0,0,.45), 0 18px 50px rgba(0,0,0,.55)`. Nunca dura.
- **Glow violeta escaso**: solo el objeto protagonista del frame.
- Radios: `sm 10 · md 16 · lg 24 · xl 32 · pill 9999`.

---

## Layout

### Encuadres del metraje (`shots`)

| kind | Geometría |
| --- | --- |
| `full` | caja sobredimensionada con desborde negativo; el stage recorta |
| `split` | 9:16 → gráfico arriba, sujeto abajo desde el 40 % · 16:9 → gira a vertical |
| `pip` | ventana **arriba a la derecha**, por encima del takeover |
| `off` | lo tapa un visual; no se emite elemento |

El PiP va arriba a la derecha **por eliminación**: la banda de abajo es del subtítulo —que
no se mueve de ahí— y el centro es del gráfico.

### Zona segura

En REEL, **el 20 % inferior queda libre**: ahí pinta la plataforma su propia interfaz
(usuario, descripción, botones). El espacio vacío bajo el subtítulo no es un descuido,
es la zona segura.

### Mockups

Se diseñan sobre 1080×1920 con un ancho de trabajo de **980 px**. Se centran con **flex**,
nunca con `transform: translate(-50%,-50%)`: en cuanto GSAP les mete un `y` o un `scale`,
toma el control del transform y descarta el centrado.

`mock_pad_top` empuja el mockup hacia abajo para que no se pise con el PiP.

---

## Subtítulos

Bloques de 3–6 palabras, Inter 900 en mayúsculas, centrados.

| Piel | Cuándo | Tratamiento |
| --- | --- | --- |
| `on-dark` | sobre el metraje | filete de grafito 7 px con `paint-order: stroke fill` + sombra |
| `on-surface` | sobre un gráfico | sin filete, solo sombra |

`paint-order: stroke fill` pinta el trazo **detrás** del relleno: la letra no engorda y la
grotesca conserva su peso. Con un borde normal Inter 900 se convierte en una mancha.

**Keyword**: pastilla violeta que aparece bajo la palabra en el instante en que se
pronuncia. Blanco sobre `#7C5CFF` da 4.35:1 — AA para texto grande, y este lo es con
mucho margen.
