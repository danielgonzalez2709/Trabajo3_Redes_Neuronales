"""CA-5: modelos de referencia de M1 contra el protocolo `Pronosticador` (núcleo §5.3). Fixtures pequeños y deterministas.

Cubre: ingenuo estacional con un caso a mano; esquema de salida (columnas, h 1..30); cuantiles monótonos y >= 0; las reglas
contra fuga 1–4 del §5.3 (lista blanca, inicio de entrenamiento, solo fechas <= origen, parámetros solo con fechas <=
fin_entrenamiento, días sin_registro fuera de la estimación); `main` con una config pequeña. Ninguna usa internet.
"""

from __future__ import annotations

import hashlib
import json
import socket
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from src.comun.config import apply_overrides, load_config
from src.m1_demanda import calendario as calmod
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
            "fin_de_anio": (f.month == 12) & (f.day >= 10) | (f.month == 1) & (f.day <= 15),
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


def assert_mismos_parametros(a, b) -> None:
    """Los dos modelos ajustados tienen exactamente los mismos parámetros (claves y arreglos)."""
    pa, pb = a.parametros(), b.parametros()
    assert pa.keys() == pb.keys()
    for r in pa:
        assert pa[r].keys() == pb[r].keys()
        for k in pa[r]:
            np.testing.assert_array_equal(pa[r][k], pb[r][k])


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
    # `tras_origen` solo cambia fechas > ORIGEN (2023-03-01), que son posteriores al fin de train: los parámetros no varían.
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
    assert_mismos_parametros(a, b)


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
    assert_mismos_parametros(a, b)
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
    assert_mismos_parametros(a, b)


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
    assert_mismos_parametros(a, b)
    pd.testing.assert_frame_equal(a.pronosticar(ORIGEN, 30, CUANTILES), b.pronosticar(ORIGEN, 30, CUANTILES))


def test_origen_fuera_de_la_historia_falla():
    m = ajustados()[1]
    with pytest.raises(ValueError):
        m.pronosticar(date(2024, 1, 1), 30, [0.5])


def test_n_parametros_y_busqueda():
    ing, reg = ajustados()
    assert ing.n_parametros() == 0 and ing.n_configuraciones_busqueda() == 0
    # (3 medias + 6 dummies de día + 5 indicadores de calendario + vacaciones + h) coeficientes + intercepto, por ruta
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


# ------------------------------------------------------------------------------------------- «conocible desde» (regla 0.9)

RUTA_PASTO = "52001-52356"
INICIO_REAL = pd.Timestamp("2021-06-01")


def serie_pasto(fin="2022-06-30") -> pd.DataFrame:
    """Serie sintética de la ruta Pasto-Ipiales (la ruta fija qué columna de vacaciones usa el modelo)."""
    f = pd.date_range("2021-06-01", fin, freq="D")
    rng = np.random.default_rng(3)
    y = np.rint(300 + 40 * (f.day_of_week.to_numpy() >= 5) + rng.normal(0, 10, len(f))).astype(int)
    return pd.DataFrame({"ruta_id": RUTA_PASTO, "fecha": f.date, "pasajeros": y, "sin_registro": False})


@pytest.fixture(scope="module")
def calendario_real() -> pd.DataFrame:
    return calmod.construir_calendario()


def reg_pasto(cal: pd.DataFrame, fin_train="2022-03-31") -> ref.RegresionCalendario:
    m = ref.RegresionCalendario(inicio=INICIO_REAL, fin=fin_train, tramos=TRAMOS, alpha=1.0, ventana_corta=7,
                                ventana_larga=28, semanas_mismo_dia=4)
    m.ajustar(serie_pasto(), cal)
    return m


def vacacion_vista(m: ref.RegresionCalendario, origen: str, objetivo: str) -> float:
    """Valor de la variable de vacaciones (última de las de calendario) que ve el modelo para el par (origen, objetivo)."""
    t0 = (pd.Timestamp(origen) - m.inicio).days
    h = np.array([(pd.Timestamp(objetivo) - pd.Timestamp(origen)).days])
    X = m._matriz(RUTA_PASTO, m._v[RUTA_PASTO], np.array([t0]), h)
    return float(X[0, -2])  # penúltima columna; la última es h / horizonte_máximo


def test_pasto_origen_antes_de_la_resolucion_no_ve_la_vacacion(calendario_real):
    fila = calendario_real[calendario_real["fecha"] == date(2022, 1, 4)].iloc[0]
    assert fila["vacaciones_escolares_52001"] == True  # noqa: E712
    assert fila["vacaciones_escolares_52001_conocible_desde"] == pd.Timestamp("2021-12-07")  # Res. 2706 de 2021
    m = reg_pasto(calendario_real)
    assert vacacion_vista(m, "2021-12-05", "2022-01-04") == 0.0  # origen < 2021-12-07
    assert vacacion_vista(m, "2021-12-06", "2022-01-04") == 0.0
    assert vacacion_vista(m, "2021-12-07", "2022-01-04") == 1.0  # el mismo día de la expedición ya es conocible
    assert vacacion_vista(m, "2021-12-08", "2022-01-04") == 1.0


def test_conocible_desde_se_aplica_tambien_al_entrenamiento_y_al_pronostico(calendario_real):
    """Con conocible_desde en el futuro lejano, vacaciones vale 0 siempre: igual que un calendario sin receso."""
    lejano = calendario_real.copy()
    lejano["vacaciones_escolares_52001_conocible_desde"] = pd.Timestamp("2100-01-01")
    sin_receso = calendario_real.drop(columns=[c for c in calendario_real.columns if c.endswith("_conocible_desde")])
    sin_receso["vacaciones_escolares_52001"] = pd.array([False] * len(sin_receso), dtype="boolean")
    a, b = reg_pasto(lejano), reg_pasto(sin_receso)
    assert_mismos_parametros(a, b)
    origen = date(2022, 4, 15)
    pd.testing.assert_frame_equal(a.pronosticar(origen, 30, CUANTILES), b.pronosticar(origen, 30, CUANTILES))
    # control: el calendario real (con la información conocible a tiempo) SÍ cambia los coeficientes
    real = reg_pasto(calendario_real)
    assert not np.array_equal(real.parametros()[RUTA_PASTO]["coef"], a.parametros()[RUTA_PASTO]["coef"])


def test_sin_columna_conocible_desde_no_se_anula_nada():
    cal = hacer_calendario()
    assert not any(c.endswith("_conocible_desde") for c in cal.columns)
    serie = hacer_serie()
    a = ajustados(serie, cal)[1]
    cal2 = cal.copy()
    cal2["vacaciones_escolares_00001_conocible_desde"] = pd.Timestamp("1900-01-01")  # siempre conocible
    cal2["vacaciones_escolares_00002_conocible_desde"] = pd.Timestamp("1900-01-01")
    b = ajustados(serie, cal2)[1]
    assert_mismos_parametros(a, b)


# ------------------------------------------------------------------------------------------- partición en la evidencia

def sha_particion(inicio: str, fin: str, origenes: list[str]) -> str:
    """Formato del §6: JSON ordenado y compacto de inicio, fin y rejilla de orígenes."""
    cuerpo = json.dumps({"inicio_entrenamiento": inicio, "fin_entrenamiento": fin, "origenes": origenes},
                        sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()


def test_evidencia_incluye_sha256_de_la_particion(tmp_path):
    assert ref.main(cfg_pequena(tmp_path)) == 0
    pres = json.loads((tmp_path / "out" / "referencia" / "presupuesto.json").read_text(encoding="utf-8"))
    esperado = sha_particion("2022-01-01", "2022-12-31", pres["origenes"])
    assert pres["origenes"] == ["2023-05-17", "2023-05-24", "2023-05-31"]
    for nombre in ("ingenuo_estacional", "regresion_calendario"):
        assert pres["modelos"][nombre]["evidencia"]["particion_sha256"] == esperado


def test_sha256_de_la_particion_cambia_con_la_particion(tmp_path):
    def sha(**sobre):
        sub = tmp_path / str(len(sobre)) / "x".join(sobre.values() if sobre else ["base"]).replace("/", "")
        sub.mkdir(parents=True)
        ref.main(cfg_pequena(sub, **sobre))
        pres = json.loads((sub / "out" / "referencia" / "presupuesto.json").read_text(encoding="utf-8"))
        return pres["modelos"]["ingenuo_estacional"]["evidencia"]["particion_sha256"]

    base = sha()
    assert sha(**{"datos.fin_entrenamiento": "2022-12-30"}) != base
    assert sha(**{"rejilla.n_origenes": "2"}) != base
    assert sha(**{"datos.inicio_entrenamiento": "2022-01-02"}) != base


# ------------------------------------------------------------------------------------------- bordes

def test_validar_tramos():
    assert ref._validar_tramos([[1, 7], [8, 14], [15, 30]]) == [(1, 7), (8, 14), (15, 30)]
    assert ref._validar_tramos([(1, 30)]) == [(1, 30)]
    for malo in ([], [[2, 7]], [[1, 7], [9, 14]], [[1, 7], [7, 14]], [[1, 0]]):
        with pytest.raises(ValueError, match="contiguos"):
            ref._validar_tramos(malo)


def test_fin_no_posterior_a_inicio_falla():
    for fin in ("2022-01-01", "2021-12-31"):
        with pytest.raises(ValueError, match="posterior"):
            ref.IngenuoEstacional(inicio=INICIO, fin=fin, tramos=TRAMOS, max_semanas_retroceso=4)
        with pytest.raises(ValueError, match="posterior"):
            ref.RegresionCalendario(inicio=INICIO, fin=fin, tramos=TRAMOS, alpha=1.0, ventana_corta=7, ventana_larga=28,
                                    semanas_mismo_dia=4)


@pytest.mark.parametrize("h", [0, -1, 31])
def test_horizonte_fuera_de_rango_falla(h):
    for m in ajustados():
        with pytest.raises(ValueError, match="horizonte"):
            m.pronosticar(ORIGEN, h, [0.5])


def test_origen_antes_del_primero_usable_falla():
    ing, reg = ajustados()
    with pytest.raises(ValueError, match="primer origen usable"):
        reg.pronosticar(INICIO + pd.Timedelta(days=reg.ventana - 2), 30, [0.5])  # un día antes del primero usable
    reg.pronosticar(INICIO + pd.Timedelta(days=reg.ventana - 1), 30, [0.5])  # el primero usable sí funciona
    with pytest.raises(ValueError, match="primer origen usable"):
        ing.pronosticar(INICIO - pd.Timedelta(days=1), 30, [0.5])


def test_train_demasiado_corto_falla_con_mensaje():
    serie, cal = hacer_serie(), hacer_calendario()
    corto = INICIO + pd.Timedelta(days=10)  # menos que la ventana de 28 días: ni una fila de entrenamiento
    ing = ref.IngenuoEstacional(inicio=INICIO, fin=corto, tramos=TRAMOS, max_semanas_retroceso=4)
    with pytest.raises(ValueError, match="Sin errores de train"):
        ing.ajustar(serie, cal)
    reg = ref.RegresionCalendario(inicio=INICIO, fin=corto, tramos=TRAMOS, alpha=1.0, ventana_corta=7, ventana_larga=28,
                                  semanas_mismo_dia=4)
    with pytest.raises(ValueError, match="Sin filas de entrenamiento"):
        reg.ajustar(serie, cal)


def test_tramo_sin_residuos_falla_con_mensaje():
    """Hay filas de entrenamiento (h pequeños) pero ninguna del tramo 15–30: no se inventan cuantiles."""
    reg = ref.RegresionCalendario(inicio=INICIO, fin=INICIO + pd.Timedelta(days=40), tramos=TRAMOS, alpha=1.0,
                                  ventana_corta=7, ventana_larga=28, semanas_mismo_dia=4)
    with pytest.raises(ValueError, match="Sin residuos de train"):
        reg.ajustar(hacer_serie(), hacer_calendario())


def test_ruta_sin_ningun_dato_valido_falla():
    serie = hacer_serie()
    serie.loc[serie["ruta_id"] == RUTAS[1], "sin_registro"] = True  # toda la ruta enmascarada
    reg = modelos()[1]
    with pytest.raises(ValueError, match="Sin filas de entrenamiento"):
        reg.ajustar(serie, hacer_calendario())


def test_ingenuo_con_todos_los_candidatos_nan_usa_la_media_de_la_historia():
    """Todos los jueves de la historia sin registro: el pronóstico de un jueves usa la media de la historia <= origen."""
    serie = hacer_serie()
    f = pd.to_datetime(serie["fecha"])
    malo = (f.dt.day_of_week == 3) & (f <= pd.Timestamp(ORIGEN))
    serie.loc[malo, ["sin_registro", "pasajeros"]] = [True, 0]
    ing = modelos()[0]
    ing.ajustar(serie, hacer_calendario())
    out = ing.pronosticar(ORIGEN, 30, [0.5])
    hist = serie[(f >= INICIO) & (f <= pd.Timestamp(ORIGEN)) & ~malo & (serie["ruta_id"] == RUTAS[0])]
    for _, fila in out[out.ruta_id == RUTAS[0]].iterrows():
        if pd.Timestamp(fila["fecha"]).day_of_week == 3:
            assert fila["punto"] == pytest.approx(hist["pasajeros"].mean())
        else:
            assert np.isfinite(fila["punto"])


@pytest.mark.parametrize("idx", [0, 1])
def test_serie_con_ceros_reales_da_pronosticos_finitos_y_no_negativos(idx):
    serie = hacer_serie()
    serie["pasajeros"] = 0  # ceros que SÍ son demanda (sin_registro = False)
    m = modelos()[idx]
    m.ajustar(serie, hacer_calendario())
    out = m.pronosticar(ORIGEN, 30, CUANTILES)
    cols = ["punto", "q0.5", "q0.75", "q0.9", "q0.95"]
    assert np.isfinite(out[cols].to_numpy()).all() and (out[cols] >= 0).all().all()
    assert out[cols].to_numpy().max() < 1e-6
