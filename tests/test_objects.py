import pytest
import tokens
from objects import REGISTRY, crowd_delta, motion_stage


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
@pytest.mark.parametrize("paleta", ["claro", "oscuro"])
def test_el_spotlight_no_rompe_el_contraste_del_acento_texto(paleta):
    """El foco aclara el suelo; `accent_hi` se deriva para aguantar 4.5:1
    hasta SPOTLIGHT_MAX (tokens._derive)."""
    tokens.use(paleta)
    try:
        lit = tokens.lift(tokens.C["bg"], tokens.SPOTLIGHT_MAX)
        assert tokens.contrast(tokens.C["accent_hi"], lit) >= 4.5
    finally:
        tokens.use("oscuro")


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


# ── el reloj ────────────────────────────────────────────────────────────────
def test_las_agujas_van_siempre_hacia_delante():
    """330° -> 210° es el camino corto y son -120°: el reloj iría HACIA ATRÁS,
    y ocho horas perdidas se leerían como ocho horas recuperadas."""
    from objects import hand_angles
    a = hand_angles("11:00", "19:00")
    assert a["hour_from"] == 330 and a["hour_to"] == 570      # +240°, horario
    assert a["minute_from"] == 0 and a["minute_to"] == 2880   # 8 vueltas
    assert a["hour_to"] > a["hour_from"] and a["minute_to"] > a["minute_from"]


def test_cruzar_medianoche_tambien_va_hacia_delante():
    from objects import hand_angles
    a = hand_angles("23:30", "01:15")
    assert a["hour_to"] > a["hour_from"]


def test_un_salto_de_minutos_mueve_las_dos_agujas():
    from objects import hand_angles
    a = hand_angles("11:00", "11:45")
    assert a["minute_to"] - a["minute_from"] == 270           # 45 min × 6°
    assert a["hour_to"] - a["hour_from"] == pytest.approx(22.5)


def test_el_mismo_estado_no_mueve_nada():
    from objects import hand_angles
    a = hand_angles("11:00", "11:00")
    assert a["hour_to"] == a["hour_from"]


def test_una_hora_mal_formada_falla_claro():
    from objects import hand_angles
    with pytest.raises(ValueError, match="HH:MM"):
        hand_angles("11:00", "las siete")


def test_el_reloj_marca_su_estado_inicial():
    from objects import clock
    o = clock("stage-a", "clock-main", {"time": "11:00"}, "center")
    assert 'id="stage-a-clock-main"' in o["html"]
    assert "rotate(330" in o["html"], "la hora inicial se hornea, no se anima"


# ── acumulación (Tarea 9) ────────────────────────────────────────────────────
def test_crowd_mueve_hacia_el_centro_por_un_delta_horneado():
    dx, dy = crowd_delta("orbit-1", fraction=0.42)
    cx, cy = tokens.SLOTS["center"]
    ox, oy = tokens.SLOTS["orbit-1"]
    assert (dx, dy) == (round((cx - ox) * 0.42), round((cy - oy) * 0.42))
    assert isinstance(dx, int) and isinstance(dy, int)


def test_el_centro_no_se_mueve_al_acumular():
    """La claustrofobia viene de que el mundo se le echa encima al sujeto,
    no de que el sujeto se acerque: si el centro se mueve, se lee como zoom."""
    assert crowd_delta("center", fraction=0.42) == (0, 0)


def test_crowd_delta_usa_una_fraccion_de_reserva():
    """La llamada del compilador es `crowd_delta(slot)`, sin fracción — tiene
    que quedar un valor por defecto, no un `TypeError`."""
    assert crowd_delta("orbit-1") == crowd_delta("orbit-1", fraction=0.42)


def test_los_cuatro_objetos_de_la_pieza_10_existen():
    """Claves kebab-case: son las que escribe el EDL (`object:dental-chair@1`
    -> kind `dental-chair`) — `ASSET_RE` solo admite `[a-z0-9-]+`, así que un
    asset de dos palabras nunca lleva guion bajo. `objects.dental_chair` etc.
    (guion bajo) son los NOMBRES DE FUNCIÓN Python, un namespace distinto."""
    for k in ("dental-chair", "phone", "card-payment", "instagram"):
        assert k in REGISTRY


def test_cada_objeto_devuelve_html_y_un_id_unico():
    vistos = set()
    for k in ("dental-chair", "phone", "card-payment", "instagram"):
        o = REGISTRY[k]("stage-b", f"task-{k}", {}, "orbit-1")
        assert o["eid"] not in vistos
        vistos.add(o["eid"])


def test_los_cuatro_objetos_se_posicionan_por_slot():
    """`left`/`top` salen de `tokens.SLOTS[slot]`, no de un valor fijo: el
    mismo objeto en dos slots distintos tiene que caer en sitios distintos."""
    for k in ("phone", "card-payment", "instagram"):
        a = REGISTRY[k]("s", "x", {}, "orbit-1")
        b = REGISTRY[k]("s", "x", {}, "orbit-2")
        assert a["html"] != b["html"]


def test_el_sillon_no_se_declara_crowd_en_la_pieza_10(fixtures_root, project_root):
    """El sillón es el punto fijo hacia el que convergen los demás — si
    alguien le añade `crowd: true` por error, la escena se cierra sobre un
    objeto que también se está moviendo y el efecto se rompe."""
    import json
    edl = json.loads((fixtures_root / "videos" / "10" / "edl.json").read_text())
    seg = next(s for s in edl["segments"] if s["words"] == [57, 72])
    crowd_ids = {e["instanceId"] for e in seg["events"]
                if e["type"] == "OBJECT_STATE" and e.get("crowd")}
    chair_id = next(e["instanceId"] for e in seg["events"]
                    if e["type"] == "OBJECT_IN" and "dental-chair" in e["asset"])
    assert chair_id not in crowd_ids


def test_los_cuatro_objetos_entran_sin_solaparse_demasiado(fixtures_root, project_root):
    """Huecos de 0.56, 0.88 y 0.90 s entre los cuatro OBJECT_IN — muy por
    debajo del gate macro de 4.5 s, tal como dice el plan."""
    import json
    from edl_words import load_words
    edl = json.loads((fixtures_root / "videos" / "10" / "edl.json").read_text())
    seg = next(s for s in edl["segments"] if s["words"] == [57, 72])
    wt = load_words(fixtures_root / "transcripts" / "10.json",
                    fixtures_root / "cuts" / "10.json")
    ins = sorted(e["atWord"] for e in seg["events"] if e["type"] == "OBJECT_IN")
    assert len(ins) == 4
    times = [wt.at(w) for w in ins]
    gaps = [round(b - a, 2) for a, b in zip(times, times[1:])]
    assert gaps == [pytest.approx(0.56, abs=0.02), pytest.approx(0.88, abs=0.02),
                    pytest.approx(0.90, abs=0.02)]


def test_el_css_del_stage_usa_el_atributo_data_viz_id_no_un_id_literal():
    """Regresión: `cid` nunca es el id LITERAL de un elemento — el host lleva
    `id="host-{cid}"` y `data-viz-id="{cid}"` es un ATRIBUTO. Un selector
    `#{cid}` no matchea nada y deja `.obj.accent`/`currentColor` sin color:
    los objetos se pintan, pero invisibles contra el fondo oscuro. Bug real,
    cazado renderizando la pieza 10 y comparando snapshots antes/después."""
    css, _, _ = motion_stage("stage-x", theme="primary", objects=[], at=[])
    assert '.viz[data-viz-id="stage-x"] .obj.accent' in css
    assert "#stage-x " not in css and "#stage-x." not in css and "#stage-x{" not in css


# ── el cuello de botella (Tarea 11 — sexto y último objeto) ─────────────────
def test_el_cuello_de_botella_existe():
    assert "bottleneck" in REGISTRY


def test_el_cuello_de_botella_devuelve_html_con_id():
    o = REGISTRY["bottleneck"]("stage-c", "task-bottleneck", {}, "center")
    assert 'id="stage-c-task-bottleneck"' in o["html"]
