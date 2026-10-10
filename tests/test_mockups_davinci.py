"""Contrato de los componentes DaVinci Resolve + MCP de la pieza 9."""

from __future__ import annotations

import importlib
import importlib.util
import re
from pathlib import Path

import pytest

import tokens as T


CASES = [
    ("dv_gancho", {"variant": "abre", "at": [.1, .5]}),
    ("dv_gancho", {"variant": "mcp", "at": [.1, .5, .9], "lienzo": True}),
    ("dv_precio", {"at": [.1, .5]}),
    ("dv_balanza", {"at": [.1, .4, .7, 1.0], "lienzo": True}),
    ("dv_linea", {"variant": "subtitulos", "at": [.1, .5], "fondo": "comic"}),
    ("dv_linea", {"variant": "tijeras", "at": [.1, .5, .9], "lienzo": True,
                   "fondo": "comic"}),
    ("dv_linea", {"variant": "produccion", "at": [.1, .5, .9],
                   "fondo": "oscuro"}),
    ("dv_enchufe", {"at": [.1, .5, .9], "lienzo": True}),
    ("dv_pedido", {"at": [.1, .5]}),
    ("dv_color", {"at": [.1, .5], "lienzo": True}),
    ("dv_graficos", {"at": [.1, .5, .9]}),
    ("dv_multicam", {"at": [.1, .5], "lienzo": True}),
    ("dv_sonido", {"at": [.1, .5, .9]}),
    ("dv_musica", {"at": [.1, .5, .9], "lienzo": True, "fondo": "oscuro"}),
    ("dv_pozo", {"at": [.1, .4, .7, 1.0], "lienzo": True, "fondo": "comic"}),
    ("dv_genera", {"at": [.1, .5], "lienzo": True, "fondo": "oscuro"}),
    ("dv_encastra", {"at": [.1, .5, .9]}),
    ("dv_higgsfield", {"at": [.1, .4, .7, 1.0], "fondo": "oscuro"}),
    ("dv_editor", {"at": [.1, .5, .9], "lienzo": True}),
    ("dv_guia", {"variant": "despliega", "at": [.1, .5]}),
    ("dv_guia", {"variant": "pedidos", "at": [.1, .5, 1.4]}),
]


def _M():
    spec = importlib.util.find_spec("mockups_davinci")
    assert spec is not None, "falta el módulo mockups_davinci"
    return importlib.import_module("mockups_davinci")


def _text(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


@pytest.mark.parametrize("fn_name,kw", CASES)
def test_cada_componente_y_variante_devuelve_contrato_selectores_reales(fn_name, kw):
    M = _M()
    css, html, anims = getattr(M, fn_name)("pieza9", **kw)
    assert css and html and isinstance(anims, list)
    ids = re.findall(r'(?<![-\w])id="([^"]+)"', html)
    assert ids and len(ids) == len(set(ids))
    for anim in anims:
        assert anim[1].startswith("#") and not anim[1].startswith(".viz[")
        assert anim[1][1:] in ids, anim
        assert anim[0] != "html-on", "los SVG diferidos deben pasar por _encender"
    assert "back.out" not in css + html + repr(anims)
    assert "!important" not in css


@pytest.mark.parametrize("fn_name,kw", [
    ("dv_gancho", {"variant": "inventada", "at": [0, 1]}),
    ("dv_linea", {"variant": "inventada", "at": [0, 1]}),
    ("dv_guia", {"variant": "inventada", "at": [0, 1]}),
])
def test_variante_mal_escrita_lanza(fn_name, kw):
    with pytest.raises(ValueError):
        getattr(_M(), fn_name)("x", **kw)


@pytest.mark.parametrize("fn_name,kw", CASES)
def test_at_con_largo_incorrecto_lanza(fn_name, kw):
    bad = dict(kw)
    bad["at"] = bad["at"][:-1]
    with pytest.raises(ValueError):
        getattr(_M(), fn_name)("x", **bad)


@pytest.mark.parametrize("fn_name,kw", CASES)
def test_fondo_mal_escrito_lanza(fn_name, kw):
    bad = dict(kw, fondo="neon")
    with pytest.raises(ValueError):
        getattr(_M(), fn_name)("x", **bad)


@pytest.mark.parametrize("bad", [[-1, 1], [2, 1], [1, float("inf")], [1, "dos"]])
def test_at_fuera_de_dominio_u_orden_lanza(bad):
    with pytest.raises(ValueError):
        _M().dv_precio("x", bad)


def test_nombres_dichos_no_existen_en_dom_y_se_teclean_en_su_at():
    M = _M()
    _, html, anims = M.dv_gancho("hook", "abre", [1, 2])
    assert "DaVinci Resolve" not in _text(html)
    assert ("type-word", "#hook-title-name", 1, .36, "DaVinci Resolve") in anims
    assert ("type-word", "#hook-dv-name", 2, .36, "DaVinci Resolve") in anims

    _, html, anims = M.dv_enchufe("plug", [1, 2, 3], lienzo=True)
    assert "Claude Code" not in _text(html) and "Codex" not in _text(html)
    assert ("type-word", "#plug-claude-name", 2, .30, "Claude Code") in anims
    assert ("type-word", "#plug-codex-name", 3, .24, "Codex") in anims

    _, html, anims = M.dv_higgsfield("higgs", [1, 2, 3, 4], fondo="oscuro")
    assert "Higgsfield" not in _text(html)
    assert ("type-word", "#higgs-higgs-name", 4, .30, "Higgsfield") in anims


def test_pedidos_exactos_solo_se_materializan_en_el_climax():
    M = _M()
    for fn_name, kw in CASES:
        _, html, anims = getattr(M, fn_name)("orders", **kw)
        # El texto real solo puede estar en el HTML dentro de la copia BORROSA (-b-text);
        # la nítida se llena en el clímax y en ningún otro componente.
        sin_borrosas = re.sub(r'<span id="[^"]*-b-text">[^<]*</span>', "", html)
        assert all(pedido not in _text(sin_borrosas) for pedido in M.PEDIDOS)
        exactos = [a for a in anims if a[0] == "caret-off" and a[4] in M.PEDIDOS]
        if fn_name == "dv_guia" and kw.get("variant") == "pedidos":
            assert len(exactos) == len(M.PEDIDOS)
        else:
            assert not exactos


ASSET_CASES = [
    ("dv_gancho", {"variant": "abre"}, ["imagenes-9/toma-2.jpg"]),
    ("dv_gancho", {"variant": "mcp"}, ["imagenes-9/toma-2.jpg"]),
    ("dv_precio", {}, ["imagenes-9/toma-2.jpg"]),
    ("dv_balanza", {}, []),
    ("dv_linea", {"variant": "subtitulos"}, ["imagenes-9/toma-2.jpg"]),
    ("dv_linea", {"variant": "tijeras"}, ["imagenes-9/toma-2.jpg"]),
    ("dv_linea", {"variant": "produccion"}, ["imagenes-9/toma-2.jpg",
                                                 "imagenes-9/toma-12.jpg",
                                                 "imagenes-9/toma-22.jpg",
                                                 "imagenes-9/toma-38.jpg"]),
    ("dv_enchufe", {}, ["imagenes-9/toma-2.jpg"]),
    ("dv_pedido", {}, ["imagenes-9/toma-2.jpg"]),
    ("dv_color", {}, ["imagenes-9/toma-12.jpg", "personajes-9/cangrejo-rueda.png"]),
    ("dv_graficos", {}, ["imagenes-9/toma-22.jpg"]),
    ("dv_multicam", {}, ["imagenes-9/toma-2.jpg", "imagenes-9/toma-12.jpg",
                          "imagenes-9/toma-22.jpg", "imagenes-9/toma-38.jpg"]),
    ("dv_sonido", {}, ["imagenes-9/toma-2.jpg", "imagenes-9/toma-12.jpg",
                        "imagenes-9/toma-22.jpg", "imagenes-9/toma-38.jpg"]),
    ("dv_musica", {}, ["imagenes-9/toma-2.jpg"]),
    ("dv_pozo", {}, ["imagenes-9/toma-2.jpg", "imagenes-9/toma-12.jpg",
                      "imagenes-9/toma-38.jpg"]),
    ("dv_genera", {}, ["imagenes-9/plano.jpg", "personajes-9/cangrejo-asoma.png",
                        "personajes-9/cangrejo-pinta.png"]),
    ("dv_encastra", {}, ["imagenes-9/toma-2.jpg", "imagenes-9/plano.jpg",
                          "imagenes-9/toma-38.jpg"]),
    ("dv_higgsfield", {}, ["imagenes-9/toma-2.jpg", "imagenes-9/plano.jpg"]),
    ("dv_editor", {}, ["imagenes-9/toma-2.jpg", "imagenes-9/toma-12.jpg",
                        "imagenes-9/toma-22.jpg", "imagenes-9/toma-38.jpg",
                        "imagenes-9/plano.jpg", "personajes-9/cangrejo-arrastra.png"]),
    ("dv_guia", {"variant": "despliega"}, ["imagenes-9/toma-2.jpg"]),
    ("dv_guia", {"variant": "pedidos"}, []),
]


@pytest.mark.parametrize("fn_name,kw,want", ASSET_CASES)
def test_assets_de_coincide_exactamente_con_imagenes_del_html(fn_name, kw, want):
    M = _M()
    call_kw = dict(kw)
    variant_lengths = {
        "dv_gancho": {"abre": 2, "mcp": 3},
        "dv_linea": {"subtitulos": 2, "tijeras": 3, "produccion": 3},
        "dv_guia": {"despliega": 2, "pedidos": 3},
    }
    plain_lengths = {
        "dv_precio": 2, "dv_balanza": 4, "dv_enchufe": 3,
        "dv_pedido": 2, "dv_color": 2, "dv_graficos": 3,
        "dv_multicam": 2, "dv_sonido": 3, "dv_musica": 3,
        "dv_pozo": 4, "dv_genera": 2, "dv_encastra": 3,
        "dv_higgsfield": 4, "dv_editor": 3,
    }
    length = (variant_lengths[fn_name][kw["variant"]]
              if fn_name in variant_lengths else plain_lengths[fn_name])
    call_kw["at"] = [0] * length
    got = M.assets_de(fn_name, kw)
    _, html, _ = getattr(M, fn_name)("assets", **call_kw)
    referenced = list(dict.fromkeys(re.findall(
        r'src="((?:personajes-(?:8|9)|imagenes-9)/[^"]+\.(?:png|jpg))"', html)))
    assert got == want
    assert referenced == want


def test_assets_de_rechaza_componente_y_variante_desconocidos():
    M = _M()
    with pytest.raises(ValueError):
        M.assets_de("no_existe", {})
    with pytest.raises(ValueError):
        M.assets_de("dv_gancho", {"variant": "no_existe"})


def test_todas_las_imagenes_del_contrato_existen(project_root):
    for _, _, paths in ASSET_CASES:
        for rel in paths:
            assert (Path(project_root) / "assets" / rel).is_file(), rel


def test_personaje_compartido_acepta_las_poses_de_pieza_9():
    import mockups_codex

    html = mockups_codex._personaje("crab", "cangrejo", ("rueda", "pinta"), 220)
    assert 'src="personajes-9/cangrejo-rueda.png"' in html
    assert 'src="personajes-9/cangrejo-pinta.png"' in html
    with pytest.raises(ValueError):
        mockups_codex._personaje("crab", "cangrejo", "vuela", 220)


def test_colores_davinci_viven_en_brands():
    assert T.BRANDS["davinci"] == {
        "bg": "#1B1B1E", "panel": "#25252A", "panel2": "#2F2F35",
        "line": "#3B3B42", "text": "#D6D6DA", "text2": "#8B8B93",
        "video": "#3F72AF", "video2": "#7A5AA8", "audio": "#3E8A5E",
        "music": "#2F7D8C", "playhead": "#E5484D", "tc": "#F2A93B",
        "ok": "#5FBF7A",
    }


def test_modulo_no_embebe_imagenes_ni_escribe_hex_a_mano(project_root):
    src = (project_root / "scripts" / "mockups_davinci.py").read_text()
    assert "data:image" not in src
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", src)
    assert "!important" not in src
    assert "#{{cid}}" not in src


@pytest.mark.parametrize("fn_name,kw", CASES)
def test_radios_css_llevan_px_y_jitter_vive_en_un_hijo(fn_name, kw):
    M = _M()
    css, _, anims = getattr(M, fn_name)("radii", **kw)
    for value in re.findall(r"border-radius:([^;}]+)", css):
        numeric = re.findall(r"(?:^|\s)(\d+(?:\.\d+)?)([a-z%]*)", value.strip())
        assert numeric and all(unit == "px" for _, unit in numeric), value
    for anim in anims:
        if anim[0] == "jitter":
            assert anim[1].endswith("-jitter"), anim


def test_build_composition_importa_y_despacha_los_diecisiete(project_root):
    src = (project_root / "scripts" / "build-composition.py").read_text()
    assert "import mockups_davinci" in src
    for name in (
        "dv_gancho", "dv_precio", "dv_balanza", "dv_linea", "dv_enchufe",
        "dv_pedido", "dv_color", "dv_graficos", "dv_multicam", "dv_sonido",
        "dv_musica", "dv_pozo", "dv_genera", "dv_encastra", "dv_higgsfield",
        "dv_editor", "dv_guia",
    ):
        assert f'"{name}": mockups_davinci.{name}' in src


@pytest.mark.parametrize("fn_name,kw", CASES)
def test_todos_los_gestos_tienen_emisor(fn_name, kw, bc):
    _, _, anims = getattr(_M(), fn_name)("gestures", **kw)
    for anim in anims:
        assert bc.emit_anim(anim), anim


@pytest.mark.parametrize("fn_name,kw", CASES)
def test_ambas_geometrias_respetan_su_altura_maxima(fn_name, kw):
    """Ninguna caja con alto declarado puede salirse del host 760/1180."""
    css, html, _ = getattr(_M(), fn_name)("bounds", **kw)
    max_h = 1180 if kw.get("lienzo", False) else 760
    assert f".cx-scene{{height:{max_h}px}}" in css
    heights = [int(n) for n in re.findall(
        r"(?<!max-)(?<!min-)height:\s*(\d+)px", css + html
    )]
    assert heights and max(heights) <= max_h, (fn_name, kw, max(heights))


def test_pozo_partida_es_un_bloque_centrado_que_cabe_en_760():
    css, html, _ = _M().dv_pozo("pit", [0, 1, 2, 3], lienzo=False)
    assert 'class="dv-pozo-layout"' in html
    assert ".dv-pozo-layout{position:relative;width:960px;height:520px}" in css
    assert ".dv-pozo-layout .dv-timeline{position:absolute;inset:0}" in css
    assert ".dv-timeline{position:absolute;top:300px}" not in css


def test_gancho_mcp_llena_el_lienzo_y_agranda_conector_y_zocalo():
    css, html, _ = _M().dv_gancho("hookbig", "mcp", [0, 1, 2], lienzo=True)
    assert 'style="width:980px;height:1040px;' in html
    assert 'id="hookbig-plug" style="width:260px;height:239px;' in html
    assert ".dv-hook-socket .dv-socket{width:220px;height:160px" in css


def test_balanza_tiene_mosaicos_de_200_en_platos_suspendidos_reales():
    css, html, _ = _M().dv_balanza("scale", [0, 1, 2, 3], lienzo=True)
    assert 'class="dv-scale"' in html and "width:980px;height:1000px" in css
    assert html.count("width:200px;height:200px") == 2
    assert html.count('class="dv-pan-string') == 4
    assert html.count('class="dv-pan-dish"') == 2
    assert ".dv-pan-dish{position:absolute;left:20px;bottom:0;width:220px" in css
    assert "border-bottom:6px solid" in css


def test_enchufe_es_grande_y_los_cables_terminan_en_los_puertos():
    css, html, _ = _M().dv_enchufe("plugbig", [0, 1, 2], lienzo=True)
    assert 'style="width:900px;height:520px;' in html
    assert html.count("width:200px;height:200px") == 2
    assert html.count('class="dv-app-port"') == 2
    assert html.count("245 904") == 2
    assert html.count("735 904") == 2
    assert ".dv-end-app .dv-app-name" in css and "font-size:18px" in css


def test_tijeras_crece_sin_salirse_por_la_izquierda_o_derecha():
    css, html, anims = _M().dv_linea(
        "cut", "tijeras", [0, 1, 2], lienzo=True, fondo="comic"
    )
    assert 'style="width:960px;height:260px"' in html
    assert 'width="220" height="220"' in html
    assert ".dv-timeline{position:absolute;top:650px}" in css
    moves = [a for a in anims if a[0] == "cursor-to" and a[1] == "#cut-scissors"]
    assert moves and max(a[4] for a in moves) <= 680


def test_produccion_cambia_stub_por_timeline_multicapa_real():
    css, html, anims = _M().dv_linea(
        "prod", "produccion", [0, 1, 2], fondo="oscuro"
    )
    assert 'class="dv-prod-stub"' in html
    assert len(re.findall(r'id="prod-tl-track\d+"', html)) == 5
    assert len(re.findall(r'id="prod-tl-c0-\d+"', html)) == 4
    for image in ("toma-2.jpg", "toma-12.jpg", "toma-22.jpg", "toma-38.jpg"):
        assert f'src="imagenes-9/{image}"' in html
    assert 'class="dv-clip dv-video2"' in html
    assert html.count('class="dv-clip dv-audio"') >= 2
    assert 'class="dv-clip dv-music"' in html
    assert any(a[:2] == ("fade-to", "#prod-prod-stub") for a in anims)
    assert all(f"#prod-tl-track{i}" in {a[1] for a in anims} for i in range(1, 5))
    assert "dv-stairs" not in html


def test_pedido_tiene_burbuja_grande_texto_oscuro_onda_y_pila():
    css, html, anims = _M().dv_pedido("ask", [0, 1], lienzo=False)
    assert ".dv-order-main .dv-bubble{width:820px" in css
    assert ".dv-voice{position:absolute;left:0;top:52px;width:160px;height:160px" in css
    assert re.search(r"\.dv-bubble-b\{[^}]*filter:blur\((9|1\d)px\)", css)
    assert html.count('class="dv-order-back"') == 4
    assert _M().PEDIDOS[0] in html and not any(a[0] == "caret-off" and a[1] == "#ask-order0-b" for a in anims)


def test_color_no_tiene_timeline_y_si_viewer_grande_panel_ruedas_scope_y_wipe():
    css, html, anims = _M().dv_color("grade", [0, 1], lienzo=True)
    assert 'class="dv-timeline"' not in html
    assert 'style="width:980px;height:1120px;' in html
    assert ".dv-color-window .dv-viewer{height:790px}" in css
    assert ".dv-color-window .dv-viewer>img{width:422px;height:750px" in css
    assert 'class="dv-color-tools"' in html
    assert ".dv-color-tools{position:absolute" in css and "height:220px" in css
    assert ".dv-color-tools .dv-wheel{width:170px;height:190px" in css
    assert ".dv-color-tools .dv-scope{width:330px;height:180px" in css
    assert any(a[:2] == ("grow-x", "#grade-grade") and a[4] == 422 for a in anims)
    assert 'src="personajes-9/cangrejo-rueda.png"' in html


@pytest.mark.parametrize("fn_name,kw", [
    ("dv_multicam", {"at": [0, 1], "lienzo": True}),
    ("dv_editor", {"at": [0, 1, 2], "lienzo": True}),
])
def test_multicam_y_editor_clamp_pistas_y_v1_con_miniaturas(fn_name, kw):
    css, html, _ = getattr(_M(), fn_name)("tracks", **kw)
    heights = [int(n) for n in re.findall(
        r'class="dv-track"[^>]+style="height:(\d+)px"', html
    )]
    assert heights and all(90 <= h <= 110 for h in heights)
    v1 = re.search(
        r'id="tracks-tl-track\d+"[^>]*><b class="dv-track-head">V1</b>(.*?)</div>',
        html,
    )
    assert v1 and v1.group(1).count("<img ") >= 4
    if fn_name == "dv_multicam":
        assert ".dv-multi-cuts i{position:absolute;top:0;width:3px;height:100%" in css
    else:
        assert 'style="width:980px;height:1120px;' in html
        assert 'src="personajes-9/cangrejo-arrastra.png"' in html
        assert "width:240px;height:240px" in css


def test_guia_pedidos_cabe_en_760_con_texto_30px_y_dos_lineas():
    M = _M()
    css, html, anims = M.dv_guia("guide", "pedidos", [0, 1, 2])
    assert ".dv-guide-climax{position:relative;width:980px;height:760px}" in css
    assert "height:60px" in css
    assert re.search(r"\.dv-guide-bubble \.dv-bubble-n\{[^}]*font-size:30px", css)
    assert all(M.text_px(pedido, 30, 600) <= 932 * 2 for pedido in M.PEDIDOS)
    tops = [int(n) for n in re.findall(r"\.dv-guide-bubble:nth-of-type\(\d+\)\{top:(\d+)px", css)]
    assert tops == [68, 182, 296, 410, 524, 638]
    assert re.search(r"\.dv-bubble-b\{[^}]*filter:blur\((9|1\d)px\)", css)
    assert not [a for a in anims if a[0] == "caret-off" and a[1].endswith("-b")]
    assert all(pedido in html for pedido in M.PEDIDOS)
