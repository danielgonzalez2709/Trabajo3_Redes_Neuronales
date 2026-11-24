"""Pruebas mínimas del estilo común de figuras."""

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from src.viz import estilo  # noqa: E402


def test_aplicar_estilo_actualiza_rcparams():
    estilo.aplicar_estilo()
    assert mpl.rcParams["axes.spines.top"] is False
    assert mpl.rcParams["figure.dpi"] == estilo.DPI


def test_guardar_figura(tmp_path):
    estilo.aplicar_estilo()
    fig, ax = plt.subplots()
    ax.plot([0, 1], [1, 2])
    destino = estilo.guardar_figura(fig, tmp_path / "sub" / "f.png")
    assert destino.exists() and destino.stat().st_size > 0
    assert not plt.fignum_exists(fig.number)  # la figura se cierra


def test_mapa_secuencial():
    assert estilo.mapa_secuencial()(0.5)
