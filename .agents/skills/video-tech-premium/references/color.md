# Color — solo importa si el metraje es HDR

Lo menos obvio del flujo, y donde más fácil se estropea la pieza sin notarlo.

El iPhone **puede** grabar en HLG / BT.2020 (HDR). Comprobar siempre:

```bash
ffprobe -v error -show_entries stream=color_transfer,color_primaries,color_space \
  -select_streams v:0 -of default=nw=1 <src>
```

`color_transfer=arib-std-b67` → es HLG y hay que calibrar. Si no aparece, el metraje es
SDR (bt709) y **este documento no aplica**: se convierte directo y `--sdr` sigue siendo lo
correcto.

> Lo habitual es SDR bt709: este tramo se salta. Cuando una toma sale HLG, se calibra por
> pieza.

---

## Tres caminos, dos son trampas

| Camino | Metraje | Gráficos |
| --- | --- | --- |
| Render HDR (por defecto) | ✅ correcto | ❌ los colores de marca se desvían |
| `--sdr` a secas | ❌ **lavado** | ✅ correcto |
| `--sdr` + LUT calibrado | ✅ | ✅ |

**`--sdr` solo REETIQUETA, no convierte.** Deja los píxeles con la curva HLG pero marca el
archivo como bt709, así que el reproductor no aplica la curva y todo se ve opaco y sin
saturación. Se detecta comparando la etiqueta contra el contenido.

---

## La conversión correcta

```bash
python3 scripts/make-hlg-lut.py assets/hlg-to-709.cube
ffmpeg -i out/1-rough.mp4 \
  -vf "lut3d=assets/hlg-to-709.cube,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv" \
  -c:v libx264 -crf 18 -g 30 -keyint_min 30 -pix_fmt yuv420p \
  -movflags +faststart -c:a aac videos/1/public/input-video.mp4
```

`setparams` es **obligatorio**: `lut3d` **propaga las etiquetas de color del frame de
entrada**, así que sin él el archivo convertido sigue marcado como HLG y Chrome vuelve a
aplicar la curva. Los flags `-color_trc` / `-color_primaries` por sí solos **no bastan**.

---

## Cómo se calibra

El objetivo **no es estilizar sino reproducir el original**. Cada metraje puede necesitar
parámetros distintos (luz, exposición, cámara), así que se recalibra por pieza:

```bash
python3 scripts/calibrate-hlg.py out/1-rough.mp4 5.5   # -> assets/hlg-params.json
python3 scripts/make-hlg-lut.py assets/hlg-to-709.cube # lee ese json
```

La referencia sale de `qlmanage`, que aplica el mismo pipeline de color que QuickTime. Con
ella se buscan los parámetros que minimizan el error en saturación, negros, luminancia
media y altas luces.

Una calibración real de iPhone HLG quedó en **gamma 1.65, gain 0.85, lift +0.06, sat 1.20**,
error 6.6 sobre las cuatro métricas (la conversión física pura daba 53).

Se usa un modelo de **curva tonal** porque HLG está diseñado para ser retrocompatible con
SDR: su señal ya está cerca de una gamma.

---

## Dos enfoques descartados — no repetirlos

- **Conversión física pura** (inversa OETF HLG + matriz BT.2020→BT.709): sobresatura
  (33 % contra 24 % de la referencia) y aplasta los negros. Al calibrar, el ajuste eligió
  por su cuenta gamut 0.00 — la matriz no ayuda aquí.
- **Curvas 1D por canal ajustadas a la referencia**: producen manchas amarillas y azules
  en la piel. Inservible.

---

## Notas de entorno

Este ffmpeg puede **no traer `zscale`** (sin libzimg ni libplacebo), y `tonemap` sin
entrada lineal deja la imagen gris. Por eso el LUT propio.

Bonus: SDR habilita la ruta de composición rápida en el render.
