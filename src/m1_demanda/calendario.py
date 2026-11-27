"""M1 — calendario exógeno (CA-1, núcleo §5.2). Sin red. Todo es conocible 30 días antes (regla 0.9).

Salida: ``data/processed/m1/calendario.parquet``, una fila por ``fecha`` (sin huecos) del periodo de
``data/externos/m1/calendario_fuentes.yaml`` (por defecto 2021-01-01..2024-12-31). Ejecutar:
``python -m src.m1_demanda.calendario [--salida RUTA] [--fuentes RUTA] [--inicio AAAA-MM-DD] [--fin AAAA-MM-DD]``.

Columnas: ``fecha`` (date), ``dia_semana`` (0 = lunes), ``festivo``, ``festivo_nombre``, ``festivo_trasladado``, ``puente``,
``semana_santa``, ``jueves_viernes_santo``, ``vacaciones_escolares_<DIVIPOLA>`` (11001, 76001, 15759, 52001, 52356;
booleano anulable), ``vacaciones_escolares`` (= la de Bogotá, 11001, por compatibilidad con §5.2) y ``fin_de_anio``.

Reglas (fuentes y supuestos en ``data/fuentes.md``, sección «Calendario exógeno de M1»):
  * Festivos: Ley 51 de 1983. Fijos sin traslado: 1-ene, 1-may, 20-jul, 7-ago, 8-dic, 25-dic, Jueves y Viernes Santo.
    Con traslado al lunes siguiente si no caen en lunes: 6-ene, 19-mar, 29-jun, 15-ago, 12-oct, 1-nov, 11-nov, Ascensión,
    Corpus Christi y Sagrado Corazón. Pascua con ``dateutil.easter``; desfases del informe CA-1 §1.1.
    TODO(cita): fuente primaria de los desfases de Corpus Christi (Pascua+60) y Sagrado Corazón (Pascua+68).
  * ``puente`` (supuesto): sábado, domingo y lunes si el lunes es festivo; viernes, sábado y domingo si el festivo cae en viernes.
  * ``semana_santa``: lunes a domingo que termina en el Domingo de Pascua (informe §1.1).
  * ``fin_de_anio`` (supuesto): del 15-dic al 15-ene, ambos inclusive.
  * Vacaciones: rangos de receso del yaml (versión original de cada calendario). Dentro de la ``cobertura`` de la ciudad
    lo que no es receso es falso; fuera de ella, o en los ``vacios`` del yaml (días que ningún acto cubre), es nulo
    (sin fuente, no se imputa).
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yaml
from dateutil.easter import easter

RAIZ = Path(__file__).resolve().parents[2]
FUENTES = RAIZ / "data" / "externos" / "m1" / "calendario_fuentes.yaml"
SALIDA = RAIZ / "data" / "processed" / "m1" / "calendario.parquet"

# Ley 51 de 1983, art. 1: (mes, día, nombre, ¿se traslada al lunes?)
_FIJOS = [
    (1, 1, "Año Nuevo", False),
    (1, 6, "Reyes Magos", True),
    (3, 19, "San José", True),
    (5, 1, "Día del Trabajo", False),
    (6, 29, "San Pedro y San Pablo", True),
    (7, 20, "Independencia", False),
    (8, 7, "Batalla de Boyacá", False),
    (8, 15, "Asunción", True),
    (10, 12, "Día de la Raza", True),
    (11, 1, "Todos los Santos", True),
    (11, 11, "Independencia de Cartagena", True),
    (12, 8, "Inmaculada Concepción", False),
    (12, 25, "Navidad", False),
]


def cargar_fuentes(ruta: Path | str | None = None) -> dict:
    with open(ruta or FUENTES, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _al_lunes(d: date) -> date:
    """Lunes siguiente si ``d`` no es lunes (art. 1 num. 2)."""
    return d if d.weekday() == 0 else d + timedelta(days=7 - d.weekday())


def festivos_del_anio(anio: int, desfases: dict | None = None) -> dict[date, tuple[str, bool]]:
    """{fecha observada: (nombre, trasladado)} de los festivos del año."""
    if desfases is None:
        desfases = cargar_fuentes()["supuestos"]["desfases_pascua"]
    pascua = easter(anio)
    out: dict[date, tuple[str, bool]] = {}

    def poner(original: date, nombre: str, traslada: bool) -> None:
        obs = _al_lunes(original) if traslada else original
        if obs in out:  # no hay regla en el informe para esta colisión: no se inventa
            raise ValueError(f"dos festivos el {obs}: {out[obs][0]} y {nombre}; sin regla en el informe CA-1")
        out[obs] = (nombre, obs != original)

    for mes, dia, nombre, traslada in _FIJOS:
        poner(date(anio, mes, dia), nombre, traslada)
    poner(pascua + timedelta(days=desfases["jueves_santo"]), "Jueves Santo", False)
    poner(pascua + timedelta(days=desfases["viernes_santo"]), "Viernes Santo", False)
    poner(pascua + timedelta(days=desfases["ascension"]), "Ascensión", True)
    poner(pascua + timedelta(days=desfases["corpus_christi"]), "Corpus Christi", True)  # TODO(cita)
    poner(pascua + timedelta(days=desfases["sagrado_corazon"]), "Sagrado Corazón", True)  # TODO(cita)
    return out


def _vacaciones(fechas: pd.Series, ciudad: dict) -> pd.Series:
    ini_c, fin_c = (date.fromisoformat(x) for x in ciudad["cobertura"])
    receso = set()
    for b in ciudad["bloques"]:
        for ini, fin in b["rangos"]:
            d, f = date.fromisoformat(ini), date.fromisoformat(fin)
            while d <= f:
                receso.add(d)
                d += timedelta(days=1)

    # `vacios` (opcional): días dentro de la cobertura que ningún acto cubre (p. ej. 1-ene-2024 de Pasto e Ipiales) -> nulo
    vacios = [(date.fromisoformat(a), date.fromisoformat(b)) for a, b in ciudad.get("vacios", [])]

    def valor(d: date):
        if d < ini_c or d > fin_c or any(a <= d <= b for a, b in vacios):
            return pd.NA
        return d in receso

    return pd.Series([valor(d) for d in fechas], index=fechas.index, dtype="boolean")


def construir_calendario(fuentes: dict | Path | str | None = None, inicio: str | None = None, fin: str | None = None) -> pd.DataFrame:
    if not isinstance(fuentes, dict):
        fuentes = cargar_fuentes(fuentes)
    ini = date.fromisoformat(inicio or fuentes["periodo"]["inicio"])
    fin_ = date.fromisoformat(fin or fuentes["periodo"]["fin"])
    sup = fuentes["supuestos"]
    des = sup["desfases_pascua"]

    # solo los años del periodo (ningún festivo ni la Semana Santa cruzan de año)
    festivos: dict[date, tuple[str, bool]] = {}
    for a in range(ini.year, fin_.year + 1):
        festivos.update(festivos_del_anio(a, des))

    fechas = [ini + timedelta(days=i) for i in range((fin_ - ini).days + 1)]
    df = pd.DataFrame({"fecha": fechas})
    df["dia_semana"] = [d.weekday() for d in fechas]
    df["festivo"] = [d in festivos for d in fechas]
    df["festivo_nombre"] = pd.Series([festivos[d][0] if d in festivos else None for d in fechas], dtype=object)
    df["festivo_trasladado"] = [bool(festivos[d][1]) if d in festivos else False for d in fechas]

    # puente (supuesto): lunes festivo -> sáb, dom, lun; viernes festivo -> vie, sáb, dom
    puente: set[date] = set()
    for d in festivos:
        if d.weekday() == 0:
            puente.update({d - timedelta(days=2), d - timedelta(days=1), d})
        elif d.weekday() == 4:
            puente.update({d, d + timedelta(days=1), d + timedelta(days=2)})
    df["puente"] = [d in puente for d in fechas]

    # Semana Santa y Jueves/Viernes Santo
    ss, jv = set(), set()
    for a in range(ini.year, fin_.year + 1):
        p = easter(a)
        ss.update(p - timedelta(days=k) for k in range(sup["semana_santa"]["dias_antes_de_pascua"] + 1))
        jv.update({p + timedelta(days=des["jueves_santo"]), p + timedelta(days=des["viernes_santo"])})
    df["semana_santa"] = [d in ss for d in fechas]
    df["jueves_viernes_santo"] = [d in jv for d in fechas]

    # fin de año (supuesto): 15-dic .. 15-ene
    m1, d1 = (int(x) for x in sup["fin_de_anio"]["inicio_mes_dia"].split("-"))
    m2, d2 = (int(x) for x in sup["fin_de_anio"]["fin_mes_dia"].split("-"))
    df["fin_de_anio"] = [(d.month, d.day) >= (m1, d1) or (d.month, d.day) <= (m2, d2) for d in fechas]

    cols = {}
    for ciudad in fuentes["ciudades"].values():
        cols[f"vacaciones_escolares_{ciudad['divipola']}"] = _vacaciones(df["fecha"], ciudad)
    for k, v in cols.items():
        df[k] = v
    df["vacaciones_escolares"] = df["vacaciones_escolares_11001"]  # Bogotá, compatibilidad §5.2
    orden = ["fecha", "dia_semana", "festivo", "festivo_nombre", "festivo_trasladado", "puente", "semana_santa",
             "jueves_viernes_santo", "vacaciones_escolares"] + list(cols) + ["fin_de_anio"]
    return df[orden]


def main(argv: list[str] | None = None) -> pd.DataFrame:
    ap = argparse.ArgumentParser(description="Calendario exógeno de M1 (CA-1)")
    ap.add_argument("--fuentes", default=str(FUENTES))
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--inicio", default=None)
    ap.add_argument("--fin", default=None)
    a = ap.parse_args(argv)
    df = construir_calendario(a.fuentes, a.inicio, a.fin)
    salida = Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(salida, index=False)
    print(f"{salida}: {len(df)} filas, {df['fecha'].min()} .. {df['fecha'].max()}")
    for c in df.columns:
        if c in ("fecha", "dia_semana", "festivo_nombre"):
            continue
        print(f"  {c}: verdadero={int((df[c] == True).sum())}  nulos={int(df[c].isna().sum())}")  # noqa: E712
    print(f"  festivo_nombre: no nulos={int(df['festivo_nombre'].notna().sum())}")
    return df


if __name__ == "__main__":
    main()
