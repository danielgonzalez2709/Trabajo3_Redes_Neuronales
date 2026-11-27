"""CA-5: modelos de referencia de M1 contra el protocolo `Pronosticador` (núcleo §5.3). Fixtures pequeños y deterministas.

Cubre: ingenuo estacional con un caso a mano; esquema de salida (columnas, h 1..30); cuantiles monótonos y >= 0; las reglas
contra fuga 1–4 del §5.3 (lista blanca, inicio de entrenamiento, solo fechas <= origen, parámetros solo con fechas <=
fin_entrenamiento, días sin_registro fuera de la estimación); `main` con una config pequeña. Ninguna usa internet.
"""

from __future__ import annotations

import json
import socket
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from src.comun.config import apply_overrides, load_config
from src.m1_demanda import referencia as ref

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "m1" / "referencia.yaml"

INICIO = pd.Timestamp("2022-01-01")
FIN_TRAIN = pd.Timestamp("2022-12-31")
FIN_SERIE = pd.Timestamp("2023-06-30")
RUTAS = ["00001-00002", "00002-00001"]
TRAMOS = [[1, 7], [8, 14], [15, 30]]
CUANTILES = [0.5, 0.75, 0.9, 0.95]
ORIGEN = date(2023, 3, 1)  # miércoles; > fin de train; origen + 30 <= fin de la serie


@pytest.fixture(autouse=True)
def sin_red(monkeypatch):
    def prohibido(*a, **k):
        raise AssertionError("las pruebas no usan internet")

    monkeypatch.setattr(socket.socket, "connect", prohibido)


def hacer_calendario(inicio="2021-12-01", fin="2023-12-31") -> pd.DataFrame:
    f = pd.date_range(inicio, fin, freq="D")
    n = len(f)
    return pd.DataFrame(
        {
            "fecha": f.date,
            "dia_semana": f.day_of_week,
            "festivo": (f.day == 8) & (f.month % 2 == 0),
            "puente": (f.day == 9) & (f.month % 2 == 0),
            "semana_santa": (f.month == 4) & (f.day >= 10) & (f.day <= 16),
            "jueves_viernes_santo": (f.month == 4) & (f.day >= 13) & (f.day <= 14),
            "fin_de_anio": (f.month == 12) & (f.day >= 15) | (f.month == 1) & (f.day <= 15),
            "vacaciones_escolares_00001": pd.array(np.arange(n) % 90 < 20, dtype="boolean"),
            "vacaciones_escolares_00002": pd.array(np.arange(n) % 70 < 15, dtype="boolean"),
        }
    )


def hacer_serie(fin=FIN_SERIE, inicio="2021-12-01", semilla=0) -> pd.DataFrame:
    rng = np.random.default_rng(semilla)
    f = pd.date_range(inicio, fin, freq="D")
    filas = []
    for i, r in enumerate(RUTAS):
        base = 500 + 100 * i + 8 * (f.day_of_week.to_numpy() == 4) * 10 + 20 * (f.day_of_week.to_numpy() >= 5) * 10
        y = np.rint(base + 0.2 * np.arange(len(f)) + rng.normal(0, 15, len(f))).astype(int)
        filas.append(
            pd.DataFrame(
                {
                    "ruta_id": r,
                    "origen_divipola": r[:5],
                    "destino_divipola": r[6:],
                    "fecha": f.date,
                    "pasajeros": y,
                    "despachos": y // 20,
                    "sin_registro": False,
                    "anomalo": False,
                }
            )
        )
    return pd.concat(filas, ignore_index=True)


def modelos(**kw):
    ing = ref.IngenuoEstacional(inicio=INICIO, fin=FIN_TRAIN, tramos=TRAMOS, max_semanas_retroceso=4)
    reg = ref.RegresionCalendario(
        inicio=INICIO, fin=FIN_TRAIN, tramos=TRAMOS, alpha=1.0, ventana_corta=7, ventana_larga=28,
        semanas_mismo_dia=4, **kw,
    )
    return ing, reg


def ajustados(serie=None, cal=None):
    serie = hacer_serie() if serie is None else serie
    cal = hacer_calendario() if cal is None else cal
    out = modelos()
    for m in out:
        m.ajustar(serie, cal)
    return out


def tras_origen(serie: pd.DataFrame, origen: date, valor=None, rng_semilla=1) -> pd.DataFrame:
    """Copia de la serie con todos los valores de fechas > origen cambiados (aleatorios o un valor fijo)."""
    s = serie.copy()
    m = pd.to_datetime(s["fecha"]) > pd.Timestamp(origen)
    rng = np.random.default_rng(rng_semilla)
    s.loc[m, "pasajeros"] = valor if valor is not None else rng.integers(0, 5000, int(m.sum()))
    return s


# ------------------------------------------------------------------------------------------- ingenuo a mano

def test_ingenuo_estacional_caso_a_mano():
    """y(d) = número de día desde 2021-12-01 (único por día): punto(h) = y(t0 + h − 7·⌈h/7⌉)."""
    serie = hacer_serie()
    f = pd.to_datetime(serie["fecha"])
    serie["pasajeros"] = (f - pd.Timestamp("2021-12-01")).dt.days + 1000
    ing = modelos()[0]
    ing.ajustar(serie, hacer_calendario())
    out = ing.pronosticar(ORIGEN, 30, CUANTILES)
    o = pd.Timestamp(ORIGEN)
    for h in (1, 6, 7, 8, 14, 15, 30):
        k = -(-h // 7)
        esperado = (o + pd.Timedelta(days=h - 7 * k) - pd.Timestamp("2021-12-01")).days + 1000
        fila = out[(out.ruta_id == RUTAS[0]) & (out.h == h)].iloc[0]
        assert fila["punto"] == esperado
        assert pd.Timestamp(fila["fecha"]) == o + pd.Timedelta(days=h)
        # el día usado es del mismo día de la semana que el objetivo y es <= origen
        assert (h - 7 * k) <= 0 and (h - 7 * k) % 7 == (h % 7)


def test_ingenuo_salta_dia_sin_registro_a_la_semana_anterior():
    serie = hacer_serie()
    f = pd.to_datetime(serie["fecha"])
    serie["pasajeros"] = (f - pd.Timestamp("2021-12-01")).dt.days + 1000
    o = pd.Timestamp(ORIGEN)
    dia_malo = o + pd.Timedelta(days=1 - 7)  # base de h = 1
    m = (f == dia_malo)
    serie.loc[m, ["sin_registro", "pasajeros"]] = [True, 0]
    ing = modelos()[0]
    ing.ajustar(serie, hacer_calendario())
    out = ing.pronosticar(ORIGEN, 30, [0.5])
    fila = out[(out.ruta_id == RUTAS[0]) & (out.h == 1)].iloc[0]
    assert fila["punto"] == (dia_malo - pd.Timedelta(days=7) - pd.Timestamp("2021-12-01")).days + 1000


# ------------------------------------------------------------------------------------------- esquema

@pytest.mark.parametrize("idx", [0, 1])
def test_columnas_horizontes_y_cuantiles_monotonos(idx):
    m = ajustados()[idx]
    out = m.pronosticar(ORIGEN, 30, CUANTILES)
    assert list(out.columns) == ["ruta_id", "fecha", "h", "punto", "q0.5", "q0.75", "q0.9", "q0.95"]
    assert sorted(out.h.unique()) == list(range(1, 31))
    assert sorted(out.ruta_id.unique()) == sorted(RUTAS)
    assert len(out) == 30 * len(RUTAS)
    assert out[["punto", "q0.5", "q0.75", "q0.9", "q0.95"]].notna().all().all()
    assert (out[["q0.5", "q0.75", "q0.9", "q0.95"]] >= 0).all().all()
    assert (out["punto"] >= 0).all()
    assert (out["q0.5"] <= out["q0.75"]).all() and (out["q0.75"] <= out["q0.9"]).all()
    assert (out["q0.9"] <= out["q0.95"]).all()


def test_pronosticar_horizonte_menor_y_cuantiles_a_pedido():
    m = ajustados()[1]
    out = m.pronosticar(ORIGEN, 10, [0.9])
    assert list(out.columns) == ["ruta_id", "fecha", "h", "punto", "q0.9"]
    assert out.h.max() == 10


def test_nombres_del_protocolo():
    ing, reg = modelos()
    assert ing.nombre == "ingenuo_estacional" and reg.nombre == "regresion_calendario"


def test_regresion_recupera_una_serie_deterministica():
    """Serie sin ruido con patrón semanal exacto: la regresión con rezagos pronostica casi exacto."""
    serie = hacer_serie()
    f = pd.to_datetime(serie["fecha"])
    serie["pasajeros"] = 400 + 50 * f.dt.day_of_week
    reg = modelos()[1]
    reg.ajustar(serie, hacer_calendario())
    out = reg.pronosticar(ORIGEN, 30, [0.5])
    esperado = 400 + 50 * pd.to_datetime(out["fecha"]).dt.day_of_week
    assert np.abs(out["punto"] - esperado).max() < 5


# ------------------------------------------------------------------------------------------- reglas contra fuga

@pytest.mark.parametrize("idx", [0, 1])
def test_fuga_valores_posteriores_al_origen_no_cambian_el_pronostico(idx):
    serie = hacer_serie()
    cal = hacer_calendario()
    a, b = modelos()[idx], modelos()[idx]
    a.ajustar(serie, cal)
    b.ajustar(tras_origen(serie, ORIGEN), cal)
    # `tras_origen` cambia también días de train? No: ORIGEN (2023-03-01) > fin de train.
    pd.testing.assert_frame_equal(
        a.pronosticar(ORIGEN, 30, CUANTILES), b.pronosticar(ORIGEN, 30, CUANTILES)
    )
    # y con un valor constante enorme
    c = modelos()[idx]
    c.ajustar(tras_origen(serie, ORIGEN, valor=10**7), cal)
    pd.testing.assert_frame_equal(
        a.pronosticar(ORIGEN, 30, CUANTILES), c.pronosticar(ORIGEN, 30, CUANTILES)
    )


@pytest.mark.parametrize("idx", [0, 1])
def test_fuga_parametros_solo_con_fechas_hasta_fin_entrenamiento(idx):
    serie = hacer_serie()
    cal = hacer_calendario()
    a, b = modelos()[idx], modelos()[idx]
    a.ajustar(serie, cal)
    b.ajustar(tras_origen(serie, FIN_TRAIN.date()), cal)
    pa, pb = a.parametros(), b.parametros()
    assert pa.keys() == pb.keys()
    for r in pa:
        for k in pa[r]:
            np.testing.assert_array_equal(pa[r][k], pb[r][k])


@pytest.mark.parametrize("idx", [0, 1])
def test_inicio_entrenamiento_se_respeta_tambien_en_las_ventanas(idx):
    """Cambiar valores anteriores a 2022-01-01 no altera parámetros ni pronósticos."""
    serie = hacer_serie()
    cal = hacer_calendario()
    s2 = serie.copy()
    m = pd.to_datetime(s2["fecha"]) < INICIO
    s2.loc[m, "pasajeros"] = 10**6
    a, b = modelos()[idx], modelos()[idx]
    a.ajustar(serie, cal)
    b.ajustar(s2, cal)
    for r in a.parametros():
        for k in a.parametros()[r]:
            np.testing.assert_array_equal(a.parametros()[r][k], b.parametros()[r][k])
    pd.testing.assert_frame_equal(a.pronosticar(ORIGEN, 30, CUANTILES), b.pronosticar(ORIGEN, 30, CUANTILES))


@pytest.mark.parametrize("idx", [0, 1])
def test_lista_blanca_anomalo_despachos_y_extras_no_afectan(idx):
    serie = hacer_serie()
    cal = hacer_calendario()
    s2 = serie.copy()
    rng = np.random.default_rng(5)
    s2["anomalo"] = rng.random(len(s2)) < 0.3
    s2["despachos"] = rng.integers(0, 10**6, len(s2))
    s2["columna_extra"] = rng.random(len(s2))
    cal2 = cal.copy()
    cal2["festivo_nombre"] = "x"
    a, b = modelos()[idx], modelos()[idx]
    a.ajustar(serie, cal)
    b.ajustar(s2, cal2)
    pd.testing.assert_frame_equal(a.pronosticar(ORIGEN, 30, CUANTILES), b.pronosticar(ORIGEN, 30, CUANTILES))
    for r in a.parametros():
        for k in a.parametros()[r]:
            np.testing.assert_array_equal(a.parametros()[r][k], b.parametros()[r][k])


@pytest.mark.parametrize("idx", [0, 1])
def test_dias_sin_registro_quedan_fuera_de_la_estimacion(idx):
    """Un día `sin_registro` no aporta su valor (0 o basura): da igual qué valor traiga."""
    serie = hacer_serie()
    cal = hacer_calendario()
    f = pd.to_datetime(serie["fecha"])
    mal = (f >= "2022-03-01") & (f <= "2022-03-10") | (f == pd.Timestamp("2023-02-20"))
    s1, s2 = serie.copy(), serie.copy()
    s1.loc[mal, ["sin_registro", "pasajeros"]] = [True, 0]
    s2.loc[mal, ["sin_registro", "pasajeros"]] = [True, 10**6]
    a, b = modelos()[idx], modelos()[idx]
    a.ajustar(s1, cal)
    b.ajustar(s2, cal)
    for r in a.parametros():
        for k in a.parametros()[r]:
            np.testing.assert_array_equal(a.parametros()[r][k], b.parametros()[r][k])
    pd.testing.assert_frame_equal(a.pronosticar(ORIGEN, 30, CUANTILES), b.pronosticar(ORIGEN, 30, CUANTILES))


def test_origen_fuera_de_la_historia_falla():
    m = ajustados()[1]
    with pytest.raises(ValueError):
        m.pronosticar(date(2024, 1, 1), 30, [0.5])


def test_n_parametros_y_busqueda():
    ing, reg = ajustados()
    assert ing.n_parametros() == 0 and ing.n_configuraciones_busqueda() == 0
    # (3 medias + 6 dummies de día + 6 indicadores de calendario + vacaciones + h) coeficientes + intercepto, por ruta
    assert reg.n_parametros() == len(RUTAS) * (3 + 6 + 5 + 1 + 1 + 1)
    assert reg.n_configuraciones_busqueda() == 0


# ------------------------------------------------------------------------------------------- rejilla y main

def test_rejilla_origenes_anclada_al_final():
    r = ref.rejilla_origenes(date(2023, 12, 1), 5, 7, date(2022, 12, 31))
    assert r[-1] == date(2023, 12, 1) and r == sorted(r)
    assert all((b - a).days == 7 for a, b in zip(r, r[1:]))
    with pytest.raises(ValueError):
        ref.rejilla_origenes(date(2023, 12, 1), 500, 7, date(2022, 12, 31))  # llegaría antes del fin de train


def cfg_pequena(tmp_path: Path, **sobre) -> dict:
    serie = hacer_serie(fin="2023-06-30")
    cal = hacer_calendario()
    serie.to_parquet(tmp_path / "demanda.parquet", index=False)
    cal.to_parquet(tmp_path / "cal.parquet", index=False)
    cfg = load_config(CONFIG)
    sets = [
        f"datos.diaria={tmp_path / 'demanda.parquet'}",
        f"datos.calendario={tmp_path / 'cal.parquet'}",
        "datos.inicio_entrenamiento=2022-01-01",
        "datos.fin_entrenamiento=2022-12-31",
        "rejilla.ultimo_origen=2023-05-31",
        "rejilla.n_origenes=3",
        f"salida.carpeta={tmp_path / 'out'}",
        f"salida.carpeta_referencia={tmp_path / 'out' / 'referencia'}",
    ] + [f"{k}={v}" for k, v in sobre.items()]
    return apply_overrides(cfg, sets)


def test_config_real_tiene_las_claves_del_prompt():
    cfg = load_config(CONFIG)
    assert str(cfg["datos"]["inicio_entrenamiento"]) == "2021-06-01"
    assert str(cfg["datos"]["fin_entrenamiento"]) == "2022-12-31"
    assert str(cfg["rejilla"]["ultimo_origen"]) == "2023-12-01"
    assert cfg["rejilla"]["paso_dias"] == 7 and cfg["rejilla"]["horizonte"] == 30
    assert cfg["horizontes"]["tramos"] == TRAMOS


def test_main_escribe_predicciones_y_presupuesto(tmp_path, capsys):
    cfg = cfg_pequena(tmp_path)
    assert ref.main(cfg) == 0
    salida = capsys.readouterr().out
    assert "fin_entrenamiento" in salida  # imprime la config resuelta
    out = tmp_path / "out"
    cols = ["origen", "ruta_id", "fecha", "h", "y", "punto", "q0.5", "q0.75", "q0.9", "q0.95"]
    serie = hacer_serie(fin="2023-06-30")
    serie["fecha"] = pd.to_datetime(serie["fecha"])
    for nombre in ("ingenuo_estacional", "regresion_calendario"):
        df = pd.read_parquet(out / f"pred_test_{nombre}.parquet")
        assert list(df.columns) == cols
        assert len(df) == 3 * 30 * len(RUTAS)
        assert sorted(pd.to_datetime(df["origen"]).dt.date.unique()) == [
            date(2023, 5, 17), date(2023, 5, 24), date(2023, 5, 31)
        ]
        assert (pd.to_datetime(df["origen"]) >= FIN_TRAIN).all()
        unido = df.assign(fecha=pd.to_datetime(df["fecha"])).merge(
            serie[["ruta_id", "fecha", "pasajeros"]], on=["ruta_id", "fecha"], how="left"
        )
        assert (unido["y"] == unido["pasajeros"]).all()
        assert (pd.to_datetime(df["fecha"]) - pd.to_datetime(df["origen"])).dt.days.eq(df["h"]).all()
    pres = json.loads((out / "referencia" / "presupuesto.json").read_text(encoding="utf-8"))
    for nombre in ("ingenuo_estacional", "regresion_calendario"):
        p = pres["modelos"][nombre]
        for k in ("n_parametros", "n_configuraciones_busqueda", "tiempo_total_s", "device", "evidencia"):
            assert k in p
        assert p["device"] == "cpu"
        assert len(p["evidencia"]["demanda_diaria_sha256"]) == 64 and len(p["evidencia"]["calendario_sha256"]) == 64
    assert pres["modelos"]["regresion_calendario"]["n_parametros"] > 0


def test_main_con_un_solo_modelo_y_override(tmp_path):
    cfg = cfg_pequena(tmp_path, **{"modelos": "[ingenuo_estacional]"})
    assert ref.main(cfg) == 0
    assert (tmp_path / "out" / "pred_test_ingenuo_estacional.parquet").exists()
    assert not (tmp_path / "out" / "pred_test_regresion_calendario.parquet").exists()


@pytest.mark.parametrize("idx", [0, 1])
def test_control_cambiar_valores_previos_al_origen_si_cambia_el_pronostico(idx):
    """Control de las pruebas de fuga: sin él, 'no cambia' podría ser trivial."""
    serie = hacer_serie()
    cal = hacer_calendario()
    s2 = serie.copy()
    m = (pd.to_datetime(s2["fecha"]) > pd.Timestamp(ORIGEN) - pd.Timedelta(days=10)) & (
        pd.to_datetime(s2["fecha"]) <= pd.Timestamp(ORIGEN))
    s2.loc[m, "pasajeros"] = 9999
    a, b = modelos()[idx], modelos()[idx]
    a.ajustar(serie, cal)
    b.ajustar(s2, cal)
    assert not a.pronosticar(ORIGEN, 30, [0.5]).equals(b.pronosticar(ORIGEN, 30, [0.5]))
