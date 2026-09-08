import pytest
import tokens
from objects import REGISTRY, motion_stage


# ── slots ───────────────────────────────────────────────────────────────────
def test_los_slots_estan_horneados_y_son_enteros():
    """Calculados en Python al compilar, nunca con cos/sin en el navegador:
    el contrato de determinismo lo exige."""
    for name, (x, y) in tokens.SLOTS.items():
        assert isinstance(x, int) and isinstance(y, int), name


def test_ningun_slot_invade_la_zona_de_la_plataforma():
    """En REEL el 20% inferior lo pinta la app. Hoy solo las captions lo
    respetan; un objeto en orbit-5 puede caer dentro y nada lo comprueba."""
    limite = int(1920 * 0.80)
    for name, (_, y) in tokens.SLOTS.items():
        assert y < limite, f"{name} cae en y{y}, dentro de la interfaz de la app"


def test_el_centro_esta_donde_manda_la_bitacora():
    """Un mockup corto centrado deja medio frame vacío: el bloque va hacia
    y 820-880, no al centro del lienzo."""
    _, cy = tokens.SLOTS["center"]
    assert 820 <= cy <= 880


def test_hay_seis_orbitas():
    assert sum(1 for k in tokens.SLOTS if k.startswith("orbit-")) == 6


# ── spotlight ───────────────────────────────────────────────────────────────
def test_el_spotlight_no_rompe_el_contraste_del_violeta_texto():
    """Medido: aclara el fondo y a alpha 0.07 el violet_hi cae a 5.77."""
    lit = tokens.lift(tokens.C["bg"], 0.05)
    assert tokens.contrast(tokens.C["violet_hi"], lit) >= 6.0


def test_un_spotlight_demasiado_fuerte_falla():
    with pytest.raises(ValueError, match="0.05"):
        tokens.spotlight(0.12)


# ── grain ───────────────────────────────────────────────────────────────────
def test_el_grain_lleva_semilla_fija():
    """Math.random sin semilla está prohibido; y un grain ANIMADO
    desincronizaría al muestrear frames en paralelo."""
    from urllib.parse import unquote
    a, b = tokens.grain(seed=7), tokens.grain(seed=7)
    assert a == b
    assert 'seed="7"' in unquote(a)
    assert "animate" not in a.lower()


# ── el stage ────────────────────────────────────────────────────────────────
def test_el_stage_devuelve_el_trio_que_espera_build_composition():
    css, html, anims = motion_stage("stage-a", theme="primary", objects=[], at=[])
    assert isinstance(css, str) and isinstance(html, str) and isinstance(anims, list)


def test_el_suelo_del_stage_es_un_elemento_del_dom():
    """Trampa nº1 del renderer: el background CSS de la página se descarta."""
    _, html, _ = motion_stage("stage-a", theme="primary", objects=[], at=[])
    assert 'class="stage-ground"' in html


def test_el_tema_problem_tiñe_el_acento_pero_no_el_texto():
    css_p, _, _ = motion_stage("s", theme="primary", objects=[], at=[])
    css_x, _, _ = motion_stage("s", theme="problem", objects=[], at=[])
    assert tokens.C["alert"] in css_x and tokens.C["alert"] not in css_p
    assert tokens.C["text"] in css_x, "el blanco del texto no depende del tema"


def test_compilar_el_mismo_stage_dos_veces_da_lo_mismo():
    a = motion_stage("s", theme="primary", objects=[], at=[])
    b = motion_stage("s", theme="primary", objects=[], at=[])
    assert a == b


def test_un_tema_inexistente_falla_claro():
    with pytest.raises(KeyError, match="turquesa"):
        motion_stage("s", theme="turquesa", objects=[], at=[])


def test_el_registry_expone_motion_stage():
    assert REGISTRY["motion_stage"] is motion_stage
