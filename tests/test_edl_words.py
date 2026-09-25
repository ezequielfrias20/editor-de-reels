import pytest
from edl_words import load_words


def test_carga_las_131_palabras_del_fuente(w10):
    assert len(w10.words) == 131


def test_la_duracion_es_la_suma_de_los_keeps(w10):
    assert w10.duration == pytest.approx(44.327)


def test_remapea_a_la_linea_del_corte(w10):
    # "La" empieza en 0.42 en el fuente y en 0.150 tras quitar la cabeza muerta.
    assert w10.words[0].text == "La"
    assert w10.at(0) == pytest.approx(0.150, abs=1e-3)


def test_at_devuelve_el_start_remapeado(w10):
    # La palabra 34 es el "7" de "7 de la tarde": 10.83 en el fuente, 10.293 remapeado.
    assert w10.at(34) == pytest.approx(10.293, abs=1e-3)
    # La palabra 18 es el "11" de "11 de la mañana".
    assert w10.at(18) == pytest.approx(5.021, abs=1e-3)


def test_span_devuelve_inicio_de_i_y_fin_de_j(w10):
    a, b = w10.span(31, 37)          # el segmento del reloj
    assert (a, b) == pytest.approx((9.412, 11.222), abs=1e-3)
    a, b = w10.span(0, 13)           # el hook
    assert (a, b) == pytest.approx((0.150, 3.724), abs=1e-3)


def test_ninguna_palabra_pasa_de_la_duracion(w10):
    assert max(x.end for x in w10.words) <= w10.duration + 1e-6


def test_los_tiempos_no_retroceden(w10):
    ts = [x.start for x in w10.words]
    assert ts == sorted(ts)


def test_text_of_une_el_rango(w10):
    assert w10.text_of(11, 13) == "simplemente contestó primero."


def test_fingerprint_es_estable(fixtures_root, w10, project_root):
    otro = load_words(fixtures_root / "transcripts" / "10.json",
                      fixtures_root / "cuts" / "10.json")
    assert w10.fingerprint == otro.fingerprint and w10.fingerprint.startswith("sha256:")


def test_el_fingerprint_cambia_si_cambian_los_cortes(fixtures_root, w10, project_root, tmp_path):
    """Recortar de nuevo la pieza mueve TODOS los beats sin tocar el transcript.
    Si el fingerprint no cubriera cuts/, ese cambio pasaría en silencio."""
    import json
    cu = json.loads((fixtures_root / "cuts" / "10.json").read_text())
    cu["keeps"][0]["dur"] += 0.5
    p = tmp_path / "cuts.json"
    p.write_text(json.dumps(cu))
    assert load_words(fixtures_root / "transcripts" / "10.json", p).fingerprint \
        != w10.fingerprint


def test_usar_el_rough_como_transcript_da_otro_fingerprint(fixtures_root, w10, project_root):
    """El -rough.json parece un atajo razonable y da 130 palabras y tiempos
    16-60 ms distintos: valida y está mal."""
    rough = load_words(fixtures_root / "transcripts" / "10-rough.json",
                       fixtures_root / "cuts" / "10.json")
    assert len(rough.words) == 130
    assert rough.fingerprint != w10.fingerprint


def test_indice_fuera_de_rango_falla_claro(w10):
    with pytest.raises(IndexError, match="131 palabras"):
        w10.at(131)


def test_span_invertido_falla(w10):
    with pytest.raises(ValueError, match="invertido"):
        w10.span(13, 0)
