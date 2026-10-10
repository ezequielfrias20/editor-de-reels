"""Contrato de los componentes Claude Code + Codex de la pieza 8."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import mockups_codex as M
import tokens as T


CASES = [
    (M.cc_gancho, {"variant": "piensa", "at": [.1, .5]}),
    (M.cc_gancho, {"variant": "ejecuta", "at": [.1, .5, .8], "lienzo": True}),
    (M.cc_gancho, {"variant": "fusion", "at": [.1, .5, .8]}),
    (M.cc_gancho, {"variant": "casa", "at": [.1, .5], "lienzo": True}),
    (M.plan_medidor, {"variant": "vacia", "at": [.1, .5, .8]}),
    (M.plan_medidor, {"variant": "calendario", "at": [.1, .5], "lienzo": True}),
    (M.cuenta_chatgpt, {"variant": "enchufe", "at": [.1, .4, .7, 1.0]}),
    (M.cuenta_chatgpt, {"variant": "conectada", "at": [.1, .5], "fondo": "oscuro"}),
    (M.instalacion, {"variant": "comandos", "at": [.1, .5, .9], "hechos": 0}),
    (M.instalacion, {"variant": "catalogo", "at": [.1, .5, .9], "hechos": 0, "lienzo": True}),
    (M.instalacion, {"variant": "plugin", "at": [.1, .5], "hechos": 1}),
    (M.instalacion, {"variant": "recarga", "at": [.1, .5, .9], "hechos": 2, "lienzo": True}),
    (M.instalacion, {"variant": "chequeo", "at": [.1, .5, .9], "hechos": 3}),
    (M.instalacion, {"variant": "enfoque", "at": [.1, .5, .9], "hechos": 0}),
    (M.error_trabado, {"variant": "traba", "at": [.1, .5, .9]}),
    (M.error_trabado, {"variant": "lampara", "at": [.1, .5, .9], "fondo": "oscuro", "lienzo": True}),
    (M.error_trabado, {"variant": "destraba", "at": [.1, .5]}),
    (M.revision_diff, {"variant": "revisa", "at": [.1, .4, .7, 1.0]}),
    (M.revision_diff, {"variant": "grandes", "at": [.1, .5], "lienzo": True}),
    (M.bloque_cuestiona, {"at": [.1, .7]}),
    (M.claude_md, {"variant": "claude", "at": [.1, .3, .5, .7, .9], "lienzo": True}),
    (M.claude_md, {"variant": "codex", "at": [.1, .5]}),
    (M.claude_md, {"variant": "vuelve", "at": [.1, .5, .9]}),
    (M.claude_md, {"variant": "reparto", "at": [.1, .5, .9], "lienzo": True}),
    (M.marcador_fallas, {"at": [.1, .7, 1.1]}),
]


@pytest.mark.parametrize("fn,kw", CASES,
                         ids=lambda value: getattr(value, "__name__", str(value)))
def test_cada_componente_y_variante_devuelve_contrato_selectores_reales(fn, kw):
    css, html, anims = fn("pieza8", **kw)
    assert css and html and isinstance(anims, list)
    ids = re.findall(r'(?<![-\w])id="([^"]+)"', html)
    assert ids and len(ids) == len(set(ids))
    assert all(i.startswith("pieza8-") for i in ids)
    for anim in anims:
        assert anim[1].startswith("#") and not anim[1].startswith(".viz[")
        assert anim[1][1:] in ids, anim


@pytest.mark.parametrize("fn,kw", [
    (M.cc_gancho, {"variant": "inventada", "at": [0, 1]}),
    (M.plan_medidor, {"variant": "inventada", "at": [0, 1]}),
    (M.cuenta_chatgpt, {"variant": "inventada", "at": [0, 1]}),
    (M.instalacion, {"variant": "inventada", "at": [0, 1]}),
    (M.error_trabado, {"variant": "inventada", "at": [0, 1]}),
    (M.revision_diff, {"variant": "inventada", "at": [0, 1]}),
    (M.claude_md, {"variant": "inventada", "at": [0, 1]}),
])
def test_variante_mal_escrita_lanza(fn, kw):
    with pytest.raises(ValueError):
        fn("x", **kw)


@pytest.mark.parametrize("fn,kw", [
    (M.cc_gancho, {"variant": "piensa", "at": [0]}),
    (M.plan_medidor, {"variant": "vacia", "at": [0, 1]}),
    (M.cuenta_chatgpt, {"variant": "enchufe", "at": [0, 1, 2]}),
    (M.instalacion, {"variant": "comandos", "at": [0, 1]}),
    (M.error_trabado, {"variant": "traba", "at": [0, 1]}),
    (M.revision_diff, {"variant": "revisa", "at": [0, 1, 2]}),
    (M.bloque_cuestiona, {"at": [0]}),
    (M.claude_md, {"variant": "claude", "at": [0, 1, 2, 3]}),
    (M.marcador_fallas, {"at": [0, 1]}),
])
def test_at_con_largo_incorrecto_lanza(fn, kw):
    with pytest.raises(ValueError):
        fn("x", **kw)


@pytest.mark.parametrize("bad", [[-1, 1], [2, 1], [1, float("inf")], [1, "dos"]])
def test_at_fuera_de_dominio_u_orden_lanza(bad):
    with pytest.raises(ValueError):
        M.bloque_cuestiona("x", bad)


@pytest.mark.parametrize("fn,kw", [
    (M.cc_gancho, {"variant": "piensa", "at": [0, 1]}),
    (M.plan_medidor, {"variant": "vacia", "at": [0, 1, 2]}),
    (M.cuenta_chatgpt, {"variant": "enchufe", "at": [0, 1, 2, 3]}),
    (M.instalacion, {"variant": "comandos", "at": [0, 1, 2]}),
    (M.error_trabado, {"variant": "traba", "at": [0, 1, 2]}),
    (M.revision_diff, {"variant": "revisa", "at": [0, 1, 2, 3]}),
    (M.bloque_cuestiona, {"at": [0, 1]}),
    (M.claude_md, {"variant": "codex", "at": [0, 1]}),
    (M.marcador_fallas, {"at": [0, 1, 2]}),
])
def test_fondo_mal_escrito_lanza(fn, kw):
    with pytest.raises(ValueError):
        fn("x", fondo="neon", **kw)


def test_pose_y_personaje_desconocidos_lanzan():
    with pytest.raises(ValueError):
        M._personaje("x", "cangrejo", "vuela", 200)
    with pytest.raises(ValueError):
        M._personaje("x", "robot", "saluda", 200)


def _text(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


def test_chatgpt_no_existe_en_dom_y_su_logo_espera_apagado_su_palabra():
    _, html, anims = M.cuenta_chatgpt("chat", "enchufe", [0, 1, 2, 3])
    assert "ChatGPT" not in _text(html)
    assert ("type-word", "#chat-account-name", 3, .36, "ChatGPT") in anims
    # El logo es SVG: va en su hueco a opacidad 0 y se enciende en su palabra
    # (un `set` de innerHTML con números lo interpolaba desde 0, ver `_encender`).
    assert 'id="chat-account-logo-hon" style="opacity:0"' in html
    assert ("fade-to", "#chat-account-logo-hon", 3, .01, 1) in anims
    assert not any(a[0] == "html-on" for a in anims)


def test_reparto_conserva_el_archivo_fuente_y_nombra_el_destino_en_su_at():
    _, html, anims = M.claude_md("md", "reparto", [0, 1, 2], lienzo=True)
    assert '<span class="cx-file-name" id="md-file-name">CLAUDE.md</span>' in html
    assert '<span class="cx-file-name" id="md-dest-file-name"></span>' in html
    assert _text(html).count("CLAUDE.md") == 1
    assert ("type-word", "#md-dest-file-name", 2, .36, "CLAUDE.md") in anims


def test_mosaicos_fusionados_aterrizan_visibles_dentro_del_slot_con_glow():
    css, html, anims = M.cc_gancho("home", "casa", [0, 1], lienzo=True)
    slot = re.search(r'id="home-plugin-slot"[^>]*>(.*?)</span></div>', html)
    assert slot and 'id="home-home-plugin"' in slot.group(1)
    assert 'style="width:72px;height:72px"' in slot.group(1)
    assert ("stamp", "#home-home-plugin", 0, .20) in anims
    assert ("fade-to", "#home-home-glow", 1, .18, 1) in anims
    assert "box-shadow:" in css

    css, html, anims = M.instalacion("plug", "plugin", [0, 1], hechos=1)
    slot = re.search(r'id="plug-plugin-slot"[^>]*>(.*?)</span></div>', html)
    assert slot and 'id="plug-landed"' in slot.group(1)
    assert 'style="width:72px;height:72px"' in slot.group(1)
    assert ("stamp", "#plug-landed", 1, .20) in anims
    assert ("fade-to", "#plug-landed-glow", 1, .18, 1) in anims
    assert ("fade-to", "#plug-fly", 1, .01, 0) in anims
    assert "box-shadow:" in css


def test_conectada_materializa_la_cuarta_tilde_en_at_cero():
    _, html, anims = M.cuenta_chatgpt("linked", "conectada", [0, 1], fondo="oscuro")
    assert 'id="linked-checkmark3-hon" style="opacity:0"' in html
    assert ("fade-to", "#linked-checkmark3-hon", 0, .01, 1) in anims
    assert not any(a[0] == "html-on" for a in anims)


def test_diff_grandes_es_gigante_sin_footer_y_con_cinta_larga():
    css, html, anims = M.revision_diff("big", "grandes", [0, 1], lienzo=True)
    assert "Modificados:" not in _text(html)
    assert "Guardar" not in _text(html)
    assert len(re.findall(r'id="big-diff\d+"', html)) == 40
    assert ".cx-diff{position:absolute;left:0;top:120px;width:980px;height:1000px" in css
    assert ".cx-diff-line{height:58px}" in css
    assert 'id="big-worker"' in html and "z-index:5" in css
    assert ("cursor-to", "#big-diff-roll", 0, 2, 0, -1600) in anims


def test_reparto_separa_fuente_destino_y_deja_caer_una_copia():
    css, html, anims = M.claude_md("share", "reparto", [0, 1, 2], lienzo=True)
    assert "cx-source-file" in html and "cx-dest-file" in html
    assert ".cx-source-file{position:absolute;top:10px;width:940px;height:500px;display:block}" in css
    assert ".cx-dest-file{position:absolute;top:590px;width:940px;height:560px;display:block;opacity:0}" in css
    assert ("fade-to", "#share-dest-wrap", 1, .18, 1) in anims
    assert ("chip-in", "#share-share-copy", 1, .18) in anims
    assert ("cursor-to", "#share-share-copy-travel", 1, .42, 0, 360) in anims
    assert 'id="share-dest-file-ok-hon" style="opacity:0"' in html
    assert ("fade-to", "#share-dest-file-ok-hon", 2, .01, 1) in anims


def test_enchufe_arranca_el_cable_en_el_cinturon_y_lo_cuelga_al_medidor():
    _, html, _ = M.cuenta_chatgpt("wire", "enchufe", [0, 1, 2, 3])
    assert 'viewBox="0 0 980 1180"' in html
    assert 'id="wire-cable-loose" d="M190 985 C250 1080 330 1090 390 1045"' in html
    assert 'id="wire-cable" d="M190 985 C275 825 345 500 500 330"' in html


def test_caja_de_claude_es_rectangular_con_cinta_y_solapa_visible():
    css, html, anims = M.claude_md("box", "claude", [0, 1, 2, 3, 4], lienzo=True)
    assert 'class="cx-box" id="box-box"' in html
    assert 'class="cx-box-flap" id="box-box-lid"' in html
    assert 'class="cx-box-tape"' in html
    assert ".cx-box{position:absolute;left:440px;bottom:24px;width:230px;height:170px" in css
    assert ".cx-box>i{position:absolute;left:8px;top:-42px;width:210px;height:54px" in css
    assert ("rise-in", "#box-box", 4, .28) in anims
    assert ("rot-to", "#box-box-lid", 4, .24, -24) in anims


def test_comandos_exactos_no_estan_en_dom_y_solo_enfoque_crea_copia_nitida():
    _, html, anims = M.instalacion("focus", "enfoque", [0, 1, 2])
    text = _text(html)
    assert all(command not in text for command in M._COMANDOS)
    assert sum(a[0] == "caret-off" and a[1].endswith("-n") for a in anims) == 4
    _, html2, anims2 = M.instalacion("blur", "comandos", [0, 1, 2])
    assert all(command not in _text(html2) for command in M._COMANDOS)
    assert not any(a[1].endswith("-n") for a in anims2)


@pytest.mark.parametrize("fn_name,kw", [
    ("cc_gancho", {"variant": "piensa", "at": [0, 1]}),
    ("cc_gancho", {"variant": "ejecuta", "at": [0, 1, 2]}),
    ("cc_gancho", {"variant": "fusion", "at": [0, 1, 2]}),
    ("cc_gancho", {"variant": "casa", "at": [0, 1]}),
    ("plan_medidor", {"variant": "vacia", "at": [0, 1, 2]}),
    ("plan_medidor", {"variant": "calendario", "at": [0, 1]}),
    ("cuenta_chatgpt", {"variant": "enchufe", "at": [0, 1, 2, 3]}),
    ("cuenta_chatgpt", {"variant": "conectada", "at": [0, 1]}),
    ("instalacion", {"variant": "enfoque", "at": [0, 1, 2]}),
    ("error_trabado", {"variant": "lampara", "at": [0, 1, 2]}),
    ("revision_diff", {"variant": "grandes", "at": [0, 1]}),
    ("bloque_cuestiona", {"at": [0, 1]}),
    ("claude_md", {"variant": "claude", "at": [0, 1, 2, 3, 4]}),
    ("claude_md", {"variant": "codex", "at": [0, 1]}),
    ("claude_md", {"variant": "vuelve", "at": [0, 1, 2]}),
    ("claude_md", {"variant": "reparto", "at": [0, 1, 2]}),
    ("marcador_fallas", {"at": [0, 1, 2]}),
])
def test_assets_de_coincide_exactamente_con_imagenes_del_html(fn_name, kw):
    want = M.assets_de(fn_name, kw)
    _, html, _ = getattr(M, fn_name)("assets", **kw)
    got = list(dict.fromkeys(re.findall(r'src="(personajes-8/[^"]+\.png)"', html)))
    assert got == want


def test_assets_de_y_personajes_rechazan_nombres_desconocidos():
    with pytest.raises(ValueError):
        M.assets_de("no_existe", {})
    with pytest.raises(ValueError):
        M.assets_de("cc_gancho", {"variant": "no_existe"})


def test_todas_las_imagenes_del_contrato_existen(project_root):
    all_assets = []
    for fn_name, kw in [
        ("cc_gancho", {"variant": v}) for v in ("piensa", "ejecuta", "fusion", "casa")
    ] + [
        ("error_trabado", {"variant": v}) for v in ("traba", "lampara", "destraba")
    ] + [
        ("claude_md", {"variant": v}) for v in ("claude", "codex", "vuelve", "reparto")
    ]:
        all_assets.extend(M.assets_de(fn_name, kw))
    for rel in set(all_assets):
        assert (Path(project_root) / "assets" / rel).is_file()


def test_paleta_devuelve_copia_sin_mutar_c():
    T.use("claro")
    before = dict(T.C)
    dark = T.paleta("oscuro")
    assert dark["bg"] == T.PALETTES_BASE["oscuro"]["bg"]
    assert T.C == before and T.PALETTE == "claro"
    dark["bg"] = "cambiado"
    assert T.C == before


def test_colores_claudecode_viven_en_brands():
    assert T.BRANDS["claudecode"] == {
        "bg": "#1A1918", "surface": "#262422", "line": "#3A3734",
        "text": "#EDEAE5", "text2": "#9C978F", "accent": "#D97757",
        "ok": "#6BC07F", "err": "#E5675A",
    }


def test_modulo_no_embebe_imagenes_ni_escribe_hex_a_mano(project_root):
    src = (project_root / "scripts" / "mockups_codex.py").read_text()
    assert "data:image" not in src
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", src)
    assert "!important" not in src


def test_build_composition_importa_y_despacha_los_nueve(project_root):
    src = (project_root / "scripts" / "build-composition.py").read_text()
    assert "import mockups_codex" in src
    for name in ("cc_gancho", "plan_medidor", "cuenta_chatgpt", "instalacion",
                 "error_trabado", "revision_diff", "bloque_cuestiona",
                 "claude_md", "marcador_fallas"):
        assert f'"{name}": mockups_codex.{name}' in src
