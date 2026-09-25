# Sonido

Tres capas, y una jerarquía que no se negocia: **la voz manda siempre**.

```
voz        la narración del metraje          pista 10
música     una cama continua                 pista 11
efectos    marcan lo que pasa en imagen      pista 12+
```

---

## Doctrina de los efectos

**El efecto marca algo que pasa en imagen** — una entrada, una cifra que aterriza, un
sello, un clic. No hay relleno ambiental.

La prueba: si no puedes señalar en el frame qué marca ese efecto, el efecto sobra. Por eso
la cuarta columna de `sfx` en `plan.json` es el **porqué**, y no es decorativa.

Los tiempos de los efectos son **los mismos beats del transcript que mueven la imagen**.
El sonido no tiene un calendario propio.

---

## El volumen se CALCULA, no se escribe a mano

La librería no viene igualada. Medido sobre los archivos de `assets/sfx/`:

| Efecto | media | pico |
| --- | --- | --- |
| `impact-bass-1` | −5.0 dB | −0.4 dB |
| `whoosh` | −19.1 dB | −2.1 dB |
| `pop` | −26.2 dB | −3.2 dB |
| `notification` | −28.1 dB | −2.7 dB |
| `click` | −30.7 dB | −5.4 dB |
| `chime` | −32.4 dB | −9.3 dB |

Hay **27 dB** entre el más caliente y el más flojo. Puestos todos a un número parecido,
el impacto tapa la voz y los clicks no existen.

`build_sfx()` mide cada archivo con `volumedetect` y resuelve:

```
v = min( 10^((OBJETIVO_MEDIA − media)/20),    # lleva la media al objetivo
         10^((TECHO_PICO    − pico )/20),     # y recorta si el pico se pasa
         1.0 )
```

Manda el más restrictivo: en los efectos calientes gana la media, en los cortos y flojos
gana el pico. Un efecto nuevo entra bien calibrado sin tocar nada. El `trim` de la tabla
solo matiza el nivel **ya normalizado**.

---

## La cabecera de la mezcla

**El metraje de iPhone llega pegado al techo.** Puede traer miles de muestras a 0 dB
*antes* de que lo toquemos: no es algo que introduzca el pipeline, viene así de cámara. Sumarle música y efectos encima satura.

`voice_gain` (por defecto **0.70**) baja la voz para abrir margen. Y para que bajarla no
cambie el balance, el generador **desplaza los mismos dB** los objetivos de efectos y
música:

```
voz ×0.70  →  −3.10 dB
efectos:  −27.0 → −30.1 dB de media   ·   techo de pico −12.0 → −15.1 dB
música:   −34.0 → −37.1 dB de media
```

Suena igual; solo deja de recortar picos. Es un mando único, no tres números sueltos que
haya que mantener sincronizados a mano.

---

## Música

Es una cama **sintetizada** (`scripts/make-music-bed.py`): libre de licencia, offline y
reproducible — el mismo comando da el mismo archivo. Se vendoriza por lo mismo que las
fuentes: si mañana cambia una skill o caduca una credencial, la pieza tiene que seguir
renderizando igual.

**El diseño importa más que el volumen.** La cama vive 14 dB bajo la voz, así que no
compite por nivel sino por **espectro**. Una cama con energía en 300–3000 Hz emborrona las
consonantes aunque esté bajita — ese es el error que hace que un video se sienta «con
música encima» en vez de «con música debajo».

Reparto medido de la cama actual:

| Banda | Contenido | Energía relativa |
| --- | --- | --- |
| 20–120 Hz | sub / pulso | −6.8 dB |
| 120–300 Hz | pad | −1.1 dB |
| **300–3000 Hz** | **hueco de la voz** | **−18.1 dB** |
| 3–8 kHz | aire / arpegio | −33.0 dB |

La Menor, 100 BPM, progresión Am–F–C–G. Neutra a propósito: sirve de suelo sin pedir
atención.

`build_music()` la recorta a la duración exacta con entrada y salida **ya horneadas**,
porque el HTML no sabe hacer un fundido de audio.

---

## Reglas de emisión

- **Un `<audio>` sin `id` se renderiza en silencio.** El renderer descubre media por `id`.
  Se ve bien en el navegador, valida la estructura, sale mudo. Lo caza `media_missing_id`.
- Los efectos son media: **sueltos en el stage**, nunca dentro de un elemento temporizado.
- **Dos clips a la vez en la misma pista es un error de solape.** `build_sfx()` reparte
  cada efecto en la pista libre más baja desde la 12.
- **Sin match → se omite, no se falla.** Un efecto ausente escribe un aviso y sigue: el
  sonido nunca bloquea un render.

⚠ `volumedetect` **loguea a nivel info**: con `-v error` no imprime nada y la medición
sale vacía en silencio.

---

## Verificación sobre el MP4

```bash
ffmpeg -v info -i output.mp4 -af volumedetect -f null - 2>&1 | grep -E "mean_volume|max_volume"
```

Y el recuento de muestras saturadas, que es lo que `max_volume: 0.0 dB` no distingue de
«justo en el techo»:

```python
x = np.frombuffer(raw_f32, dtype=np.float32)
print(np.max(np.abs(x)), np.sum(np.abs(x) >= 0.999))
```

El AAC decodificado en float **puede pasar de 1.0**: un pico de 1.62 significa que la
mezcla ya venía recortada, no que el decodificador se equivoque.
