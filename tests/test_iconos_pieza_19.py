"""Los iconos de línea de la pieza 19, y las reglas que los hacen medibles.

La petición del usuario («que las animaciones lleven iconos, no solo textos y
recuadros») se paga con una librería nueva, y lo que estos tests fijan no es el
dibujo —eso cambia— sino las cuatro propiedades de las que depende que un icono
no repita el 💡 de la pieza 18: va en `currentColor`, no trae ids, comparte
lienzo y trazo con los demás, y el roster no se encoge en silencio.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import icons  # noqa: E402


# Los que la pieza 19 usa de verdad. Si alguien borra uno, el plan deja de
# compilar — y este test lo dice antes y con nombre.
EN_USO = {"code", "megaphone", "doc", "people", "gear",
          "strategy", "build", "inspect",
          "download", "check", "agent", "repo", "stack", "knot"}


def test_el_roster_cubre_lo_que_usa_la_pieza_19():
    assert EN_USO <= set(icons.names())


@pytest.mark.parametrize("name", sorted(EN_USO))
def test_todo_icono_va_en_currentcolor_y_nunca_en_un_color_propio(name):
    """La lección del 💡 de la pieza 18, convertida en gate.

    Un emoji se pinta con la paleta del navegador y el linter de contraste lee
    el `color` heredado: midió 1.11:1 contra el grafito para un glifo que en el
    frame se veía perfecto. Un icono que trajera un `fill="#…"` propio tendría
    el mismo problema al revés — se vería distinto de lo que el linter mide.
    """
    svg = icons.icon(name, 40)
    assert 'stroke="currentColor"' in svg
    assert not re.search(r'(fill|stroke)="#', svg), \
        f"{name}: trae un color literal; todo va en currentColor"
    for m in re.finditer(r'fill="([^"]+)"', svg):
        assert m.group(1) in ("none", "currentColor"), \
            f"{name}: fill={m.group(1)!r} no es none ni currentColor"


@pytest.mark.parametrize("name", sorted(EN_USO))
def test_ningun_icono_declara_un_id(name):
    """`check_unique_element_ids` falla sobre el HTML ensamblado si un id se
    repite, y un icono se inlinea muchas veces por pieza: `agent` sale 12 veces
    solo en el hook. Es la trampa 7bis de §9 vista desde el lado barato — estos
    no tienen gradientes que renombrar porque no tienen ids que colisionar."""
    assert not re.search(r'(?<![-\w])id="', icons.icon(name, 40))


@pytest.mark.parametrize("name", sorted(EN_USO))
def test_todos_comparten_lienzo_y_trazo(name):
    """Una tercera geometría hace que la pieza parezca un collage, igual que
    una tercera familia tipográfica (§3)."""
    svg = icons.icon(name, 40)
    assert f'viewBox="{icons.VIEWBOX}"' in svg
    assert f'stroke-width="{icons.STROKE}"' in svg
    assert 'stroke-linecap="round"' in svg and 'stroke-linejoin="round"' in svg


def test_el_trazo_no_se_escala_con_el_tamano():
    """A propósito: un icono de 64 px con trazo proporcional es una mancha y
    uno de 22 px con trazo fino desaparece."""
    chico, grande = icons.icon("gear", 28), icons.icon("gear", 48)
    assert 'stroke-width="1.8"' in chico and 'stroke-width="1.8"' in grande
    assert 'width="28"' in chico and 'width="48"' in grande


def test_un_icono_desconocido_LANZA_en_vez_de_renderizar_un_hueco():
    """El camino de FALLO. Un gate que nunca ha fallado no es un gate: sin
    esto, un nombre mal escrito en el plan compilaría un `<svg>` vacío y el
    error se descubriría sobre el MP4, que es donde este proyecto ya ha pagado
    demasiadas veces."""
    with pytest.raises(KeyError) as e:
        icons.icon("engranaje")
    assert "engranaje" in str(e.value)


def test_los_alias_apuntan_al_mismo_dibujo_que_su_concepto():
    assert icons.icon("ingenieria", 40) == icons.icon("gear", 40)
    assert icons.icon("comunidad", 40) == icons.icon("people", 40)
