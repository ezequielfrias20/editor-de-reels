"""Contrato de los componentes de ChatGPT de la pieza 6."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import mockups_chatgpt as M
import tokens as T


CASES = [
    (M.chatgpt_chat, {"variant": "oculto", "at": [.2, .8],
                      "comando": "/blueprint"}),
    (M.chatgpt_chat, {"variant": "enviar", "at": [.1, .4, 1.0, 1.3, 2.2],
                      "comando": "/blueprint", "resultado": "blueprint",
                      "cursor": True}),
    (M.chatgpt_chat, {"variant": "enviar", "at": [.1, .4, 1.0, 1.3, 2.2],
                      "comando": "/xray", "resultado": "xray",
                      "previo": "explodedview"}),
    (M.imagen_resultado, {"clave": "blueprint", "at": [.1, .8],
                          "comando": "/blueprint", "revelado": "barrido"}),
    (M.imagen_resultado, {"clave": "explodedview", "at": [.1, .8],
                          "revelado": "despiece"}),
    (M.imagen_resultado, {"clave": "xray", "at": [.1, .8],
                          "revelado": "escaneo"}),
    (M.imagen_resultado, {"clave": "handwritten", "at": [.1, .8],
                          "revelado": "trazo"}),
    (M.parpadeo_estados, {"at": [.2, .7]}),
    (M.lista_codigos, {"at": [.1, .4, .9, 1.4]}),
]


@pytest.mark.parametrize("fn,kw", CASES,
                         ids=lambda value: getattr(value, "__name__", str(value)))
def test_cada_componente_devuelve_el_contrato_y_selectores_reales(fn, kw):
    result = fn("pieza6", **kw)
    assert isinstance(result, tuple) and len(result) == 3
    css, html, anims = result
    assert css and html and isinstance(anims, list)

    found = re.findall(r'(?<![-\w])id="([^"]+)"', html)
    assert len(found) == len(set(found)), "ningún id puede repetirse"
    assert found and all(i.startswith("pieza6-") for i in found)
    ids = set(found)
    for anim in anims:
        selector = anim[1]
        assert not selector.startswith(".viz[")
        assert selector.startswith("#"), anim
        assert selector[1:] in ids, anim


def test_enviar_no_adelanta_el_comando_y_lo_teclea_en_su_palabra():
    _, html, anims = M.chatgpt_chat(
        "chat", "enviar", [.1, .4, 1.0, 1.3, 2.2],
        comando="/blueprint", resultado="blueprint")
    text_nodes = re.sub(r"<[^>]+>", "", html)
    assert "/blueprint" not in text_nodes
    typed = [a for a in anims if a[0] == "type-word"]
    assert typed == [("type-word", "#chat-command", .4, .6, "/blueprint")]
    assert ("badge-out", "#chat-placeholder", .4, .12) in anims
    assert any(a[0] == "chatgpt-send-on" and a[2] == .4 for a in anims)
    assert any(a[0] == "chatgpt-send-off" and a[2] > 1.0 for a in anims)


def test_enviar_sin_intervalo_de_tecleo_entra_entero_de_golpe():
    _, html, anims = M.chatgpt_chat(
        "cut", "enviar", [.1, .4, .4, .8, 1.5],
        comando="/xray", resultado="xray")
    text_nodes = re.sub(r"<[^>]+>", "", html)
    assert "/xray" not in text_nodes
    assert not any(a[0] == "type-word" for a in anims)
    assert ("caret-off", "#cut-command", .4, .01, "/xray") in anims


def test_lista_no_adelanta_codigos_y_jamas_revela_stickynotes():
    _, html, anims = M.lista_codigos("lista", [.1, .4, .9, 1.4])
    text_nodes = re.sub(r"<[^>]+>", "", html)
    for command in ("/blueprint", "/explodedview", "/xray", "/handwritten"):
        assert command not in text_nodes
        assert any(a[0] == "type-word" and a[4] == command for a in anims)
    assert "/stickynotes" not in text_nodes
    assert "/stickynotes" not in repr(anims)


def test_lista_apaga_cada_caret_despues_de_terminar_su_tecleo():
    _, _, anims = M.lista_codigos("lista", [.1, .4, .9, 1.4])
    for i in range(4):
        typed = next(a for a in anims if a[0] == "type-word" and a[1] == f"#lista-code{i}")
        off = next(a for a in anims if a[0] == "caret-off" and a[1] == f"#lista-code{i}")
        assert off[2] > typed[2] + typed[3]


def test_parpadeo_deja_dos_frames_de_destello_entre_estados():
    _, _, anims = M.parpadeo_estados("blink", [.2, .7])
    flashes = [a for a in anims if a[1] == "#blink-flash"]
    assert len(flashes) == 6
    for on, off in zip(flashes[::2], flashes[1::2]):
        assert off[2] - on[2] >= 2 / 30


@pytest.mark.parametrize("fn,kw", [
    (M.chatgpt_chat, {"variant": "inventada", "at": [1, 2]}),
    (M.chatgpt_chat, {"variant": "enviar", "at": [1, 2, 3, 4, 5],
                      "resultado": "blueprint"}),
    (M.chatgpt_chat, {"variant": "enviar", "at": [1, 2, 3, 4, 5],
                      "comando": "/blueprint"}),
    (M.imagen_resultado, {"clave": "inventada", "at": [1, 2]}),
    (M.imagen_resultado, {"clave": "xray", "at": [1, 2],
                          "revelado": "inventado"}),
    (M.parpadeo_estados, {"at": [1, 2], "claves": ("xray", "inventada")}),
])
def test_variantes_claves_y_gestos_desconocidos_lanzan(fn, kw):
    with pytest.raises(ValueError):
        fn("x", **kw)


@pytest.mark.parametrize("fn,kw", [
    (M.chatgpt_chat, {"variant": "oculto", "at": [1], "comando": "/blue"}),
    (M.chatgpt_chat, {"variant": "enviar", "at": [1, 2, 3, 4],
                      "comando": "/xray", "resultado": "xray"}),
    (M.imagen_resultado, {"clave": "xray", "at": [1]}),
    (M.parpadeo_estados, {"at": [1]}),
    (M.lista_codigos, {"at": [1, 2, 3]}),
])
def test_at_de_longitud_incorrecta_lanza(fn, kw):
    with pytest.raises(ValueError):
        fn("x", **kw)


@pytest.mark.parametrize("bad", [[-1, 1], [2, 1], [1, float("inf")], [1, "dos"]])
def test_at_fuera_de_dominio_u_orden_lanza(bad):
    with pytest.raises(ValueError):
        M.imagen_resultado("x", "xray", bad)


@pytest.mark.parametrize("fn_name,kw,want", [
    ("chatgpt_chat", {"variant": "oculto", "at": [0, 1],
                      "comando": "/blueprint"},
     ["imagenes-6/original.jpg"]),
    ("chatgpt_chat", {"variant": "enviar", "at": [0, 1, 2, 3, 4],
                      "comando": "/xray", "resultado": "xray",
                      "previo": "blueprint"},
     ["imagenes-6/original.jpg", "imagenes-6/xray.jpg",
      "imagenes-6/blueprint.jpg"]),
    ("imagen_resultado", {"clave": "handwritten", "at": [0, 1]},
     ["imagenes-6/handwritten.jpg"]),
    ("parpadeo_estados", {"at": [0, 1]},
     ["imagenes-6/original.jpg", "imagenes-6/blueprint.jpg",
      "imagenes-6/explodedview.jpg", "imagenes-6/xray.jpg"]),
    ("lista_codigos", {"at": [0, 1, 2, 3]},
     ["imagenes-6/blueprint.jpg", "imagenes-6/explodedview.jpg",
      "imagenes-6/xray.jpg", "imagenes-6/handwritten.jpg",
      "imagenes-6/stickynotes.jpg"]),
])
def test_assets_de_coincide_exactamente_con_las_imagenes_del_html(fn_name, kw, want):
    got = M.assets_de(fn_name, kw)
    assert got == want
    _, html, _ = getattr(M, fn_name)("assets", **kw)
    refs = list(dict.fromkeys(re.findall(r'src="(imagenes-6/[^"]+\.jpg)"', html)))
    assert refs == want


def test_assets_de_rechaza_funcion_desconocida():
    with pytest.raises(ValueError):
        M.assets_de("no_existe", {})


def test_colores_chatgpt_viven_en_un_unico_token_literal():
    assert T.BRANDS["chatgpt"] == {
        "bg": "#212121", "surface": "#303030", "line": "#3a3a3a",
        "text": "#ececec", "text2": "#afafaf", "send_bg": "#ececec",
        "send_fg": "#0d0d0d", "send_off": "#676767",
    }


def test_mockup_chatgpt_no_escribe_hex_a_mano(project_root):
    src = (project_root / "scripts" / "mockups_chatgpt.py").read_text()
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", src)


def test_visual_con_asset_generico_ausente_falla_nombrando_el_archivo(
        bc, project_root, monkeypatch):
    monkeypatch.setattr(bc, "ROOT", project_root)
    monkeypatch.setattr(bc, "W", 1080)
    monkeypatch.setattr(bc, "H", 1920)
    monkeypatch.setattr(bc, "VISUALS", [{
        "id": "asset-gate", "role": "takeover", "kind": "image",
        "start": 0.0, "end": 1.0, "src": "imagenes-6/original.jpg",
        "assets": ["imagenes-6/no-existe.jpg"],
    }])
    with pytest.raises(SystemExit) as exc:
        bc.build_visuals(1.0)
    assert "imagenes-6/no-existe.jpg" in str(exc.value)


def test_todas_las_imagenes_del_contrato_existen(project_root):
    for rel in M.assets_de("lista_codigos", {"at": [0, 1, 2, 3]}) + [
            "imagenes-6/original.jpg"]:
        assert (Path(project_root) / "assets" / rel).is_file()
