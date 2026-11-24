"""`src/comun/torch_utils.py`: dispositivo, determinismo y conversión numpy ↔ tensor (núcleo §3 y §7.1)."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from src.comun import torch_utils
from src.comun.torch_utils import a_numpy, a_tensor, activar_determinismo, resolver_device


def test_resolver_device_cpu_tal_cual():
    assert resolver_device("cpu") == torch.device("cpu")


@pytest.mark.parametrize("hay_gpu, esperado", [(True, "cuda"), (False, "cpu")])
def test_resolver_device_auto_segun_el_hardware(monkeypatch, hay_gpu, esperado):
    monkeypatch.setattr(torch_utils.torch.cuda, "is_available", lambda: hay_gpu)
    assert resolver_device("auto").type == esperado


def test_resolver_device_cuda_sin_gpu_es_error_no_degrada(monkeypatch):
    monkeypatch.setattr(torch_utils.torch.cuda, "is_available", lambda: False)
    with pytest.raises(RuntimeError, match="cuda"):
        resolver_device("cuda")


def test_resolver_device_cuda_con_gpu(monkeypatch):
    monkeypatch.setattr(torch_utils.torch.cuda, "is_available", lambda: True)
    assert resolver_device("cuda").type == "cuda"


@pytest.mark.parametrize("nombre", ["gpu", "CPU", "", "cuda:0"])
def test_resolver_device_nombre_desconocido(nombre):
    with pytest.raises(ValueError, match="device"):
        resolver_device(nombre)


def test_activar_determinismo_en_cpu():
    anterior = torch.are_deterministic_algorithms_enabled()
    try:
        torch.use_deterministic_algorithms(False)
        activar_determinismo("cpu")
        assert torch.are_deterministic_algorithms_enabled()
    finally:
        torch.use_deterministic_algorithms(anterior)


@pytest.mark.parametrize("malo", [np.nan, np.inf, -np.inf])
@pytest.mark.parametrize("columna", [False, True])
def test_a_tensor_rechaza_no_finitos(malo, columna):
    with pytest.raises(ValueError, match="no finitos"):
        a_tensor([1.0, malo, 3.0], "cpu", columna=columna)


def test_a_tensor_rechaza_no_finitos_en_matriz():
    with pytest.raises(ValueError, match="no finitos"):
        a_tensor(np.array([[1.0, 2.0], [np.nan, 4.0]]), "cpu")


def test_a_tensor_float32_y_formas():
    t = a_tensor(np.arange(3, dtype=np.float64), "cpu")
    assert t.dtype == torch.float32 and t.shape == (3,)
    assert a_tensor([1, 2, 3], "cpu", columna=True).shape == (3, 1)
    assert a_tensor(np.zeros((4, 2)), "cpu").shape == (4, 2)


def test_a_tensor_formas_invalidas():
    with pytest.raises(ValueError, match="vector"):
        a_tensor(np.zeros((3, 2)), "cpu", columna=True)
    with pytest.raises(ValueError, match="1-D o 2-D"):
        a_tensor(np.zeros((2, 2, 2)), "cpu")


def test_a_numpy_ida_y_vuelta():
    x = np.array([0.5, 1.5, -2.0])
    np.testing.assert_allclose(a_numpy(a_tensor(x, "cpu", columna=True)), x)
    salida = a_numpy(a_tensor(x, "cpu"))
    assert salida.dtype == np.float64 and salida.shape == (3,)


def test_a_numpy_rechaza_otras_formas():
    with pytest.raises(ValueError, match="forma"):
        a_numpy(torch.zeros(3, 2))
