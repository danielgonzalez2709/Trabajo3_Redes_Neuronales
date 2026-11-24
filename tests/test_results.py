"""`src/comun/results.py`: JSON sin NaN/inf y escritura atómica (núcleo §5.9)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from src.comun import results
from src.comun.results import load_json, save_json, to_jsonable


@pytest.mark.parametrize("malo", [float("nan"), float("inf"), float("-inf"), np.float64("nan"), np.float32("inf")])
def test_save_json_rechaza_no_finitos_y_no_crea_el_archivo(tmp_path: Path, malo):
    destino = tmp_path / "salida" / "r.json"
    with pytest.raises(ValueError, match=r"no finito.*\$\.history\[1\]\.f_best"):
        save_json(destino, {"history": [{"f_best": 1.0}, {"f_best": malo}]})
    assert not destino.exists()
    assert not list(tmp_path.rglob("*.tmp"))


def test_save_json_rechaza_no_finitos_en_arreglos_numpy(tmp_path: Path):
    with pytest.raises(ValueError, match="no finito"):
        save_json(tmp_path / "r.json", {"x": np.array([1.0, np.nan])})


def test_save_json_no_toca_el_archivo_anterior_si_hay_nan(tmp_path: Path):
    destino = save_json(tmp_path / "r.json", {"ok": 1})
    antes = destino.read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        save_json(destino, {"ok": float("nan")})
    assert destino.read_text(encoding="utf-8") == antes


def test_save_json_ida_y_vuelta_con_tipos_numpy(tmp_path: Path):
    datos = {"a": np.int64(3), "b": np.float32(0.5), "c": (1, 2), "d": np.array([[1, 2], [3, 4]]),
             "ruta": Path("x") / "y", "texto": "ñandú", "ok": np.bool_(True)}
    destino = save_json(tmp_path / "carpeta" / "r.json", datos)
    assert load_json(destino) == {"a": 3, "b": 0.5, "c": [1, 2], "d": [[1, 2], [3, 4]], "ruta": "x/y",
                                  "texto": "ñandú", "ok": True}
    texto = destino.read_text(encoding="utf-8")
    assert "ñandú" in texto and texto.endswith("\n") and "\r" not in texto


def test_save_json_compacto(tmp_path: Path):
    destino = save_json(tmp_path / "r.json", {"a": [1, 2]}, sangria=None)
    assert destino.read_text(encoding="utf-8") == '{"a":[1,2]}\n'


def test_save_json_escritura_atomica_si_falla_el_reemplazo(tmp_path: Path, monkeypatch):
    """Si `os.replace` falla, el archivo anterior queda intacto y no sobra el temporal."""
    destino = save_json(tmp_path / "r.json", {"version": 1})
    antes = destino.read_bytes()

    def falla(origen, objetivo):
        raise OSError("disco lleno simulado")

    monkeypatch.setattr(results.os, "replace", falla)
    with pytest.raises(OSError, match="disco lleno"):
        save_json(destino, {"version": 2})
    monkeypatch.undo()
    assert destino.read_bytes() == antes
    assert [p.name for p in tmp_path.iterdir()] == ["r.json"]


def test_save_json_escribe_en_un_temporal_de_la_misma_carpeta(tmp_path: Path, monkeypatch):
    vistos: list[tuple[Path, Path]] = []
    reemplazar = os.replace

    def espia(origen, objetivo):
        vistos.append((Path(origen), Path(objetivo)))
        reemplazar(origen, objetivo)

    monkeypatch.setattr(results.os, "replace", espia)
    destino = save_json(tmp_path / "r.json", {"a": 1})
    assert len(vistos) == 1
    temporal, objetivo = vistos[0]
    assert temporal.parent == destino.parent and temporal != objetivo and objetivo == destino
    assert not temporal.exists()


def test_save_json_error_de_tipo_no_deja_archivo(tmp_path: Path):
    with pytest.raises(TypeError, match=r"\$\.x"):
        save_json(tmp_path / "r.json", {"x": object()})
    assert list(tmp_path.iterdir()) == []


def test_to_jsonable_clave_no_texto_es_error():
    with pytest.raises(TypeError):
        to_jsonable({1: "a"})


def test_load_json_rechaza_nan_literal(tmp_path: Path):
    ruta = tmp_path / "nan.json"
    ruta.write_text('{"x": NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="NaN"):
        load_json(ruta)
    assert json.loads('{"x": 1}') == {"x": 1}
