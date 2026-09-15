"""El paso 4b: la red que faltaba.

`plan-cuts --audio` QUITA las respiraciones; esto comprueba que no quedó
ninguna, y sale con código 1 si queda. Existe porque la pieza 14 se entregó con
900 ms de inspiración dentro del hook y la cazó el usuario, no el flujo.
"""
import pytest


def _args(project_root, pieza, **extra):
    out = ["--project", str(project_root), "--piece", str(pieza)]
    for k, v in extra.items():
        out += [f"--{k}", str(v)]
    return out


def test_la_pieza_14_pasa_el_gate(ab, project_root, audio14):
    """La regresión que importa: el corte que se entregó no conserva ninguna."""
    if not (project_root / "out" / "14-rough.mp4").exists():
        pytest.skip("out/14-rough.mp4 no está")
    assert ab.main(_args(project_root, 14)) == 0


def test_el_gate_SABE_fallar(ab, project_root, audio14):
    """Un gate que nunca ha fallado no es un gate. Con margen 0 el ataque y la
    cola de cada palabra dejan de estar cubiertos y aparece una isla — la
    prueba de que el camino de fallo existe y de para qué está el margen."""
    if not (project_root / "out" / "14-rough.mp4").exists():
        pytest.skip("out/14-rough.mp4 no está")
    assert ab.main(_args(project_root, 14, margin=0.0)) == 1


def test_falta_un_camino_NO_es_un_aprobado(ab, project_root, tmp_path):
    """«0/0 no es que pase, es que no midió» vale igual aquí: si el corte o la
    fuente no están, el gate sale con 2 y no con 0. Un aprobado por ausencia
    sería justo el fallo que este paso existe para impedir."""
    assert ab.main(["--project", str(tmp_path), "--piece", "99"]) == 2


def test_sin_piece_y_sin_caminos_no_adivina(ab, project_root):
    with pytest.raises(SystemExit):
        ab.main(["--project", str(project_root)])
