"""Voz frente a sonido — el módulo que nació de una entrega con una
respiración dentro del hook.

La pieza 14 se entregó con una inspiración de 900 ms a −10.4 dB entre
«decisión.» y «Una»: más fuerte que media frase. Nadie la cazó porque las dos
herramientas del flujo medían ENERGÍA, y una respiración de proximidad tiene de
sobra. Peor: `refine-timings` la había METIDO DENTRO de la palabra al estirar
su borde 845 ms, así que ningún detector posterior podía verla.

⚠ LO QUE NO SE PUEDE PROBAR CON RUIDO SINTÉTICO. Un ruido gaussiano limitado en
banda es CUASI-PERIÓDICO: su armonicidad se queda en 0.27-0.44, pegada al
umbral, mientras una respiración real mide 0.06-0.25. Probar la clasificación
con ruido de banda mediría el generador, no el detector — así que esa parte se
prueba contra el audio real de la pieza, y lo sintético se reserva para las
propiedades que no dependen de modelar una respiración.
"""
import json

import numpy as np
import pytest

import voicing as v

SR = 16000


def vocal(dur=0.5, f0=120.0):
    """Vocal sostenida: F0 y sus armónicos. Es lo que tiene TONO."""
    t = np.arange(int(dur * SR)) / SR
    x = sum(np.sin(2 * np.pi * f0 * k * t) / k for k in range(1, 12))
    return (0.25 * x / np.abs(x).max()).astype(np.float32)


def ruido(dur=0.5, banda=(2000.0, 7000.0), semilla=7, nivel=1.0):
    n = int(dur * SR)
    x = np.random.default_rng(semilla).standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < banda[0]) | (f > banda[1])] = 0
    y = np.fft.irfft(X, n=n)
    return (nivel * 0.25 * y / np.abs(y).max()).astype(np.float32)


def sala(dur, semilla=3):
    """Tono de sala, NO silencio digital.

    ⚠ El suelo sale del percentil 10 de la propia envolvente: con silencio
    digital el suelo es −180 dB y el umbral degenera. Todo lo que se mida
    necesita aire real alrededor — la misma razón por la que auditar un corte
    exige el umbral de la FUENTE.
    """
    return (np.random.default_rng(semilla).standard_normal(int(dur * SR))
            * 0.0009).astype(np.float32)


# ── la medida ────────────────────────────────────────────────────────────────
def test_una_vocal_tiene_tono():
    harm, _ = v.voicing(vocal(), SR)
    assert np.median(harm) >= v.HARM_MIN


def test_una_fricativa_cuenta_COMO_VOZ_aunque_no_tenga_tono():
    """La «s» no tiene armónicos, y marcarla como respiración cortaría el
    final de cada plural. Se salva por la energía alta, no por el tono."""
    x = np.concatenate([sala(0.6), ruido(), sala(0.6)])
    db = v.envelope(x, SR)
    harm, alta = v.voicing(x, SR)
    _, thr = v.thresholds(db)
    fuerte = db > thr
    assert np.median(harm[fuerte]) < v.HARM_MIN       # no tiene tono…
    assert np.median(alta[fuerte]) >= v.HIGH_MIN      # …pero sí aire alto
    assert v.voice_mask(db, harm, alta, thr)[fuerte].mean() > 0.9
    assert not v.breath_islands(x, SR)


def test_voicing_devuelve_LOS_MISMOS_FRAMES_que_envelope():
    """La ventana de voz es más larga (40 ms frente a 25), así que sin
    rellenar salía un frame menos y cualquier `harm[db > thr]` reventaba con
    un IndexError. Lo pilló un test, no una entrega."""
    x = np.concatenate([sala(0.4), vocal(0.3), sala(0.4)])
    db = v.envelope(x, SR)
    harm, alta = v.voicing(x, SR)
    assert len(harm) == len(alta) == len(db)
    assert v.voice_mask(db, harm, alta, -45.0).shape == db.shape


def test_el_faldon_ensancha_la_isla_hasta_donde_deja_de_OIRSE():
    """Lo AUDIBLE es más ancho que lo que cruza el umbral de detección, y
    cortar en el borde estrecho deja el ataque dentro del material conservado.
    Con un umbral alto a propósito, los flancos flojos solo entran con faldón."""
    # banda GRAVE: con la aguda por defecto el ruido cuenta como fricativa —o
    # sea, como voz— y no hay isla ninguna que ensanchar.
    grave = dict(banda=(80.0, 700.0))
    x = np.concatenate([sala(0.6), ruido(0.3, nivel=0.06, **grave),
                        ruido(0.3, **grave),
                        ruido(0.3, semilla=9, nivel=0.06, **grave), sala(0.6)])
    cubre = lambda sk: sum(b - a for a, b, _ in
                           v.breath_islands(x, SR, thr=-30.0, skirt_db=sk))
    assert cubre(6.0) > cubre(60.0)


# ── la pausa del corte se coloca sobre silencio ─────────────────────────────
def test_clean_span_se_para_antes_de_la_respiracion(pc):
    islas = [(1.10, 1.60, -12.0)]
    assert pc.clean_span(1.00, 2.00, islas, True) == pytest.approx(0.07, abs=1e-9)
    assert pc.clean_span(1.00, 2.00, islas, False) == pytest.approx(0.37, abs=1e-9)


def test_clean_span_sin_islas_deja_el_hueco_entero(pc):
    """Sin respiración no hay de qué guardarse: el GUARD existe para no cortar
    pegado a un ataque, y sin ataque no se descuenta nada."""
    assert pc.clean_span(1.0, 2.0, [], True) == pytest.approx(1.0)
    assert pc.clean_span(1.0, 2.0, [], False) == pytest.approx(1.0)


# ── regresión sobre el audio real: LA respiración de la pieza 14 ────────────
VENTANA = (5.40, 6.70)


def test_el_tramo_de_la_pieza_14_suena_fuerte_y_NO_es_voz(audio14):
    a, sr = v.load_mono(audio14)
    db = v.envelope(a, sr)
    harm, alta = v.voicing(a, sr)
    _, thr = v.thresholds(db)
    i0, i1 = int(5.70 / v.HOP), int(6.40 / v.HOP)
    assert db[i0:i1].max() > -15, "suena, y más que media frase"
    assert np.median(harm[i0:i1]) < v.HARM_MIN, "sin tono"
    assert np.median(alta[i0:i1]) < v.HIGH_MIN, "sin aire alto"
    # No se pide 0 %: la autocorrelación de un ruido da frames sueltos por
    # encima del umbral. Lo que importa es que la inmensa mayoría no es voz.
    assert v.voice_mask(db, harm, alta, thr)[i0:i1].mean() < 0.25


def test_el_detector_la_encuentra_entera(audio14):
    a, sr = v.load_mono(audio14)
    islas = [x for x in v.breath_islands(a, sr)
             if x[1] > VENTANA[0] and x[0] < VENTANA[1]]
    assert islas
    assert sum(b - a_ for a_, b, _ in islas) > 0.60, "900 ms de respiración"
    assert min(a_ for a_, _, _ in islas) < 5.75


def test_una_isla_corta_pero_FUERTE_cuenta_igual(audio14):
    """Fue ESTA regla, y no el faldón, la que movió el corte de «ingresos.» de
    33.18 a 33.07: allí la respiración arranca con ráfagas de 35-55 ms a −13 dB
    que `min_dur` descartaba una por una."""
    a, sr = v.load_mono(audio14)
    en = lambda **kw: [x for x in v.breath_islands(a, sr, **kw)
                       if x[1] > 32.9 and x[0] < 33.6]
    assert len(en(min_dur=0.30, loud_db=-25.0)) >= 3
    assert en(min_dur=0.30, loud_db=0.0) == []


def test_auditar_un_corte_con_SU_umbral_esconde_respiraciones(audio14, project_root):
    """Un corte ya no contiene los silencios de los que se estima el suelo: en
    la pieza 14 sube de −52.0 a −41.9 dB y el umbral con él. Auditar con el
    umbral propio del corte veía MENOS de lo que hay."""
    corte = project_root / "out" / "14-rough.mp4"
    if not corte.exists():
        pytest.skip("out/14-rough.mp4 no está")
    a_src, sr = v.load_mono(audio14)
    thr_fuente = v.thresholds(v.envelope(a_src, sr))[1]
    a_cut, sr = v.load_mono(corte)
    thr_propio = v.thresholds(v.envelope(a_cut, sr))[1]
    assert thr_propio > thr_fuente + 5, "el corte «sube» el suelo estimado"
    assert len(v.breath_islands(a_cut, sr, thr=thr_fuente)) >= \
        len(v.breath_islands(a_cut, sr))


# ── y el resultado: el corte no conserva la respiración ─────────────────────
def test_el_corte_de_la_pieza_14_no_conserva_la_respiracion(project_root):
    """La pausa que queda tras «decisión.» tiene que ser SILENCIO. Se mide
    sobre `cuts/14.json`, que es lo que de verdad se cortó."""
    w = json.loads((project_root / "transcripts" / "14.json").read_text())["words"]
    assert w[12]["text"] == "decisión."
    fin = w[12]["end"] / 1000
    assert fin < 5.7, ("«decisión.» vuelve a estar estirada sobre la "
                       "respiración: ese es el bug original")
    cortes = json.loads((project_root / "cuts" / "14.json").read_text())["cuts"]
    tras = min((c for c in cortes if c["start"] > fin - 0.01),
               key=lambda c: c["start"])["start"]
    assert 0 < tras - fin <= 0.10, (
        f"el corte empieza {tras - fin:.3f} s tras la palabra: ahí cabe una "
        f"respiración entera, que es el fallo que este test existe para cazar")
