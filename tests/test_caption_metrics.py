import pytest
from caption_metrics import KEYWORD_SCALE_MAX, measure_block

H = 1920


def test_un_bloque_corto_es_una_linea():
    m = measure_block(["La", "clínica", "de"], 66, None, "REEL", H)
    assert m["n_lines"] == 1 and m["max_size"] == 66


def test_la_keyword_agranda_la_caja_de_linea():
    """Es lo que rompe floor_top si se calcula con CAPTION_SIZE a secas."""
    sin = measure_block(["simplemente", "contestó", "primero"], 66, None, "REEL", H)
    con = measure_block(["simplemente", "contestó", "primero"], 66, (1, 2), "REEL", H)
    assert con["max_size"] == round(66 * KEYWORD_SCALE_MAX)
    assert con["line_h"] > sin["line_h"]


def test_floor_top_usa_el_tamano_maximo_no_el_base():
    """El bug de los 46 px: dos líneas con keyword grande se metían en la
    interfaz de la plataforma."""
    palabras = ["si", "tienes", "una", "clínica", "que", "atiende",
                "pacientes", "todos", "los", "días"]
    con = measure_block(palabras, 66, (3, 3), "REEL", H)
    # El presupuesto se descuenta con las líneas que de verdad salen. Antes
    # aquí había un `== 2` fijo, que era el tope del cálculo viejo y no una
    # medida: diez palabras no caben en dos líneas.
    assert con["floor_top"] == round(H * 0.80) - con["n_lines"] * con["line_h"]
    sin = measure_block(palabras, 66, None, "REEL", H)
    assert con["floor_top"] < sin["floor_top"], "la keyword grande baja el techo"


def test_una_palabra_larga_fuerza_una_tercera_linea():
    """La regresión de la pieza 11. El bloque suma 1.67x el ancho útil —que
    dividiendo da dos líneas— pero «AUTOMÁTICAMENTE» rompe la línea antes de
    agotarlo y el navegador lo envuelve a TRES. Con la cuenta topada en dos, la
    tercera línea entraba 58 px dentro del 20 % que pinta la plataforma."""
    m = measure_block(["PACIENTES", "AUTOMÁTICAMENTE", "POR", "WHATSAPP"],
                      66, (0, 0), "REEL", H)
    assert m["n_lines"] == 3
    maxw = round(1080 * 0.84)
    por_division = -(-round(m["width"]) // maxw)      # techo de ancho/ancho_util
    assert por_division == 2, "dividiendo el total salen 2: por eso no vale dividir"
    assert m["floor_top"] + m["n_lines"] * m["line_h"] <= round(H * 0.80)


def test_ninguna_tinta_cae_en_el_20_por_ciento_inferior():
    m = measure_block(["comenta", "STOCK", "y", "te", "escribo"], 66, (1, 1), "REEL", H)
    assert m["floor_top"] + m["n_lines"] * m["line_h"] <= round(H * 0.80)


def test_la_keyword_ancha_puede_forzar_dos_lineas():
    """Si el ancho se midiera con el tamaño base, un bloque medido como una
    línea se renderizaría como dos y la cuenta de la zona segura fallaría."""
    base = measure_block(["contestar", "más", "rápido", "siempre"], 66, None, "REEL", H)
    grande = measure_block(["contestar", "más", "rápido", "siempre"], 66, (0, 3),
                           "REEL", H)
    assert grande["width"] > base["width"]


def test_una_escala_de_keyword_por_encima_del_tope_falla():
    with pytest.raises(ValueError, match="1.22"):
        measure_block(["a"], 66, (0, 0), "REEL", H, keyword_scale=1.5)


def test_youtube_usa_su_propia_escala():
    r = measure_block(["hola", "mundo"], 66, None, "REEL", H)
    y = measure_block(["hola", "mundo"], 54, None, "YOUTUBE", 1080)
    assert y["floor_top"] != r["floor_top"]


def test_un_formato_desconocido_falla():
    with pytest.raises(ValueError, match="VERTICAL_RARO"):
        measure_block(["a"], 66, None, "VERTICAL_RARO", H)


def test_una_keyword_de_una_palabra_solo_agranda_esa():
    """El resto del bloque se queda en el tamaño base: la keyword es el
    titular del frame, no un cambio de escala de todo el subtítulo."""
    m = measure_block(["tiene", "que", "SOSTENER", "a"], 66, (2, 2), "REEL", H)
    assert m["max_size"] == round(66 * KEYWORD_SCALE_MAX)
    solo_base = measure_block(["tiene", "que", "SOSTENER", "a"], 66, None, "REEL", H)
    assert m["width"] > solo_base["width"]
