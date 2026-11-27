"""CA-1: calendario exógeno de M1 (núcleo §5.2). Las fechas esperadas se transcriben de las tablas de
``docs/investigacion/CA-1_fuentes_calendario.md`` §2 (18 festivos por año, 2021–2024), no del código bajo prueba."""
from datetime import date, timedelta

import pandas as pd
import pytest

from src.m1_demanda import calendario as cal

# (fecha ISO, nombre) — informe §2.
INFORME = {
    2021: """2021-01-01 Año Nuevo|2021-01-11 Reyes Magos|2021-03-22 San José|2021-04-01 Jueves Santo|2021-04-02 Viernes Santo|
2021-05-01 Día del Trabajo|2021-05-17 Ascensión|2021-06-07 Corpus Christi|2021-06-14 Sagrado Corazón|
2021-07-05 San Pedro y San Pablo|2021-07-20 Independencia|2021-08-07 Batalla de Boyacá|2021-08-16 Asunción|
2021-10-18 Día de la Raza|2021-11-01 Todos los Santos|2021-11-15 Independencia de Cartagena|2021-12-08 Inmaculada Concepción|
2021-12-25 Navidad""",
    2022: """2022-01-01 Año Nuevo|2022-01-10 Reyes Magos|2022-03-21 San José|2022-04-14 Jueves Santo|2022-04-15 Viernes Santo|
2022-05-01 Día del Trabajo|2022-05-30 Ascensión|2022-06-20 Corpus Christi|2022-06-27 Sagrado Corazón|
2022-07-04 San Pedro y San Pablo|2022-07-20 Independencia|2022-08-07 Batalla de Boyacá|2022-08-15 Asunción|
2022-10-17 Día de la Raza|2022-11-07 Todos los Santos|2022-11-14 Independencia de Cartagena|2022-12-08 Inmaculada Concepción|
2022-12-25 Navidad""",
    2023: """2023-01-01 Año Nuevo|2023-01-09 Reyes Magos|2023-03-20 San José|2023-04-06 Jueves Santo|2023-04-07 Viernes Santo|
2023-05-01 Día del Trabajo|2023-05-22 Ascensión|2023-06-12 Corpus Christi|2023-06-19 Sagrado Corazón|
2023-07-03 San Pedro y San Pablo|2023-07-20 Independencia|2023-08-07 Batalla de Boyacá|2023-08-21 Asunción|
2023-10-16 Día de la Raza|2023-11-06 Todos los Santos|2023-11-13 Independencia de Cartagena|2023-12-08 Inmaculada Concepción|
2023-12-25 Navidad""",
    2024: """2024-01-01 Año Nuevo|2024-01-08 Reyes Magos|2024-03-25 San José|2024-03-28 Jueves Santo|2024-03-29 Viernes Santo|
2024-05-01 Día del Trabajo|2024-05-13 Ascensión|2024-06-03 Corpus Christi|2024-06-10 Sagrado Corazón|
2024-07-01 San Pedro y San Pablo|2024-07-20 Independencia|2024-08-07 Batalla de Boyacá|2024-08-19 Asunción|
2024-10-14 Día de la Raza|2024-11-04 Todos los Santos|2024-11-11 Independencia de Cartagena|2024-12-08 Inmaculada Concepción|
2024-12-25 Navidad""",
}


def _tabla(anio):
    out = {}
    for item in INFORME[anio].replace("\n", "").split("|"):
        f, nombre = item.strip().split(" ", 1)
        out[date.fromisoformat(f)] = nombre
    return out


@pytest.fixture(scope="module")
def df():
    return cal.construir_calendario()


def fila(df, iso):
    return df[df["fecha"] == date.fromisoformat(iso)].iloc[0]


@pytest.mark.parametrize("anio", [2021, 2022, 2023, 2024])
def test_festivos_igual_a_tablas_del_informe(anio):
    esperado = _tabla(anio)
    assert len(esperado) == 18
    calculado = {f: n for f, (n, _t) in cal.festivos_del_anio(anio).items()}
    assert calculado == esperado


@pytest.mark.parametrize("anio", [2021, 2022, 2023, 2024])
def test_festivos_en_dataframe(df, anio):
    esperado = _tabla(anio)
    sub = df[df["fecha"].map(lambda d: d.year) == anio]
    marcados = dict(zip(sub.loc[sub["festivo"], "fecha"], sub.loc[sub["festivo"], "festivo_nombre"]))
    assert marcados == esperado
    assert sub.loc[~sub["festivo"], "festivo_nombre"].isna().all()


def test_sin_huecos_y_esquema(df):
    fechas = pd.to_datetime(df["fecha"])
    rango = pd.date_range("2021-01-01", "2024-12-31", freq="D")
    assert len(df) == len(rango) and list(fechas) == list(rango)
    for c in ["festivo", "puente", "semana_santa", "jueves_viernes_santo", "fin_de_anio", "festivo_trasladado"]:
        assert df[c].dtype == bool, c
    cols_vac = ["vacaciones_escolares"] + [f"vacaciones_escolares_{d}" for d in ("11001", "76001", "15759", "52001", "52356")]
    for c in cols_vac:
        assert str(df[c].dtype) == "boolean", c
    assert df["dia_semana"].between(0, 6).all()
    assert fila(df, "2021-01-04")["dia_semana"] == 0  # lunes
    assert (df["vacaciones_escolares"].fillna(-1) == df["vacaciones_escolares_11001"].fillna(-1)).all()


def test_trasladado_y_no_trasladado(df):
    r = fila(df, "2021-01-11")  # Reyes: 6-ene (mié) -> lunes
    assert r["festivo"] and r["festivo_trasladado"]
    r = fila(df, "2022-07-20")  # Independencia: fija
    assert r["festivo"] and not r["festivo_trasladado"]
    r = fila(df, "2023-05-01")  # 1-may cae lunes, no se mueve
    assert r["festivo"] and not r["festivo_trasladado"]
    r = fila(df, "2022-08-15")  # trasladable que ya cae lunes
    assert r["festivo"] and not r["festivo_trasladado"]
    r = fila(df, "2021-05-01")  # 1-may en sábado: fijo, no se traslada
    assert r["festivo"] and not r["festivo_trasladado"]
    assert not fila(df, "2021-01-06")["festivo"]
    assert fila(df, "2023-11-13")["festivo_trasladado"]  # 11-nov en sábado


@pytest.mark.parametrize("jueves,viernes,pascua", [
    ("2021-04-01", "2021-04-02", "2021-04-04"), ("2022-04-14", "2022-04-15", "2022-04-17"),
    ("2023-04-06", "2023-04-07", "2023-04-09"), ("2024-03-28", "2024-03-29", "2024-03-31")])
def test_semana_santa(df, jueves, viernes, pascua):
    assert fila(df, jueves)["jueves_viernes_santo"] and fila(df, viernes)["jueves_viernes_santo"]
    assert fila(df, jueves)["festivo_nombre"] == "Jueves Santo"
    p = date.fromisoformat(pascua)
    sub = df[df["semana_santa"]]["fecha"]
    # ventana del informe: lunes a domingo que termina en Pascua
    assert fila(df, pascua)["semana_santa"]
    assert fila(df, (p - timedelta(days=6)).isoformat())["semana_santa"]
    assert not fila(df, (p - timedelta(days=7)).isoformat())["semana_santa"]
    assert not fila(df, (p + timedelta(days=1)).isoformat())["semana_santa"]
    assert len(sub) == 28 and int(df["jueves_viernes_santo"].sum()) == 8


def test_puente_lunes_y_viernes(df):
    # lunes festivo 2022-10-17: sáb 15, dom 16 y lun 17
    assert [bool(fila(df, d)["puente"]) for d in ("2022-10-14", "2022-10-15", "2022-10-16", "2022-10-17", "2022-10-18")] == [
        False, True, True, True, False]
    # festivo en viernes 2023-12-08 (Inmaculada): vie, sáb, dom
    assert [bool(fila(df, d)["puente"]) for d in ("2023-12-07", "2023-12-08", "2023-12-09", "2023-12-10", "2023-12-11")] == [
        False, True, True, True, False]
    # festivo en martes/jueves no genera puente (supuesto)
    assert not fila(df, "2022-12-08")["puente"]
    # festivo en sábado no trasladado: sin lunes festivo
    assert not fila(df, "2021-12-25")["puente"]


def test_fin_de_anio_bordes(df):
    assert not fila(df, "2021-12-14")["fin_de_anio"] and fila(df, "2021-12-15")["fin_de_anio"]
    assert fila(df, "2022-01-15")["fin_de_anio"] and not fila(df, "2022-01-16")["fin_de_anio"]
    assert fila(df, "2021-01-01")["fin_de_anio"] and fila(df, "2024-12-31")["fin_de_anio"]


def test_vacaciones_por_ciudad(df):
    # un receso por ciudad (informe §3.3)
    casos = {
        "11001": ("2022-06-20", "2022-06-19"),  # Bogotá 20-jun a 10-jul 2022
        "76001": ("2022-06-27", "2022-06-20"),  # Cali 27-jun a 24-jul 2022 (Bogotá ya en receso)
        "15759": ("2023-06-19", "2023-06-18"),  # Sogamoso
        "52001": ("2022-07-11", "2022-07-10"),  # Pasto vacaciones 11-31 jul 2022
        "52356": ("2023-10-16", "2023-10-15"),  # Ipiales receso de octubre 2023 el 16-22
    }
    for d, (dentro, fuera) in casos.items():
        c = f"vacaciones_escolares_{d}"
        assert fila(df, dentro)[c] is True or fila(df, dentro)[c] == True  # noqa: E712
        assert fila(df, fuera)[c] == False  # noqa: E712
    # Cali en receso, Bogotá no
    assert fila(df, "2022-06-27")["vacaciones_escolares_76001"] == True  # noqa: E712
    assert fila(df, "2022-06-27")["vacaciones_escolares_11001"] == True  # noqa: E712
    assert fila(df, "2022-06-20")["vacaciones_escolares_76001"] == False  # noqa: E712
    # Pasto: desarrollo institucional cuenta como sin clases; Semana Santa 2022 no es receso en Pasto pero sí en Bogotá
    assert fila(df, "2022-01-20")["vacaciones_escolares_52001"] == True  # noqa: E712
    assert fila(df, "2022-04-13")["vacaciones_escolares_52001"] == False  # noqa: E712
    assert fila(df, "2022-04-13")["vacaciones_escolares_11001"] == True  # noqa: E712
    # Ipiales 2024: receso de mayo
    assert fila(df, "2024-05-15")["vacaciones_escolares_52356"] == True  # noqa: E712
    # el extremo de un receso que cruza el año se recorta al periodo
    assert fila(df, "2024-12-31")["vacaciones_escolares_11001"] == True  # noqa: E712


def test_vacios_son_nulos(df):
    for iso in ("2021-01-01", "2021-01-17"):
        assert pd.isna(fila(df, iso)["vacaciones_escolares_76001"])  # Cali: sin calendario 2020
        assert pd.isna(fila(df, iso)["vacaciones_escolares_15759"])
    for iso in ("2021-01-01", "2021-01-03"):
        assert pd.isna(fila(df, iso)["vacaciones_escolares_52001"])
        assert pd.isna(fila(df, iso)["vacaciones_escolares_52356"])
    assert not pd.isna(fila(df, "2021-01-01")["vacaciones_escolares_11001"])
    assert not pd.isna(fila(df, "2021-01-18")["vacaciones_escolares_76001"])
    # Sogamoso 2024: sin decreto
    assert pd.isna(fila(df, "2024-06-17")["vacaciones_escolares_15759"])
    assert not pd.isna(fila(df, "2024-01-14")["vacaciones_escolares_15759"])
    assert df["vacaciones_escolares_11001"].notna().all()


def test_fuentes_yaml_trae_cita_por_bloque():
    fuentes = cal.cargar_fuentes()
    for ciudad in fuentes["ciudades"].values():
        for b in ciudad["bloques"]:
            for k in ("acto", "fecha_acto", "url", "consulta", "anio_lectivo", "rangos"):
                assert k in b, (ciudad.get("nombre"), b)


def test_parquet_se_escribe(tmp_path):
    ruta = tmp_path / "calendario.parquet"
    cal.main(["--salida", str(ruta)])
    out = pd.read_parquet(ruta)
    assert len(out) == 1461 and "vacaciones_escolares_52356" in out.columns
