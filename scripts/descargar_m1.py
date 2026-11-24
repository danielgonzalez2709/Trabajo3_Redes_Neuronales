"""Descarga de los datos de M1 desde datos.gov.co (único código con red del proyecto; los experimentos no usan internet).

Subcomandos:
  ranking   muestra de un día por mes (2021-01 a 2023-12) -> data/raw/m1/ranking_rutas.csv y resumen
  descargar rutas elegidas, por mes -> data/raw/m1/rutas/AAAA-MM.parquet (reanudable)
  divipola  DIVIPOLA (gdxc-w37w) -> data/processed/m1/divipola.csv

Uso: .venv\\Scripts\\python scripts/descargar_m1.py <subcomando> [opciones]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parents[1]
BASE = "https://www.datos.gov.co/resource"
ID_M1 = "eh75-8ah6"
ID_DIVIPOLA = "gdxc-w37w"
URL_M1 = f"{BASE}/{ID_M1}.json"
URL_DIVIPOLA = f"{BASE}/{ID_DIVIPOLA}.json"
RAW = RAIZ / "data" / "raw" / "m1"
LOG = RAW / "consultas_log.jsonl"
FECHA_MAX_VALIDA = "2100-01-01"  # excluye las fechas imposibles (2202, 2222, 6202)
PAGINA = 50000


# --------------------------------------------------------------------------- consulta con reintentos
def _registrar(registro: dict, log: Path | None = None) -> None:
    log = LOG if log is None else log
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def consultar(params: dict, timeout: float = 300, reintentos: int = 3, url: str = URL_M1,
              espera: float = 5.0, sesion=None, log: Path | None = None) -> list[dict]:
    """GET con reintentos y espera creciente ante timeout, error de conexión o 5xx. Registra cada intento
    (URL completa, duración, filas, error). Lanza la última excepción si se agotan los reintentos.
    Un 4xx no se reintenta (la consulta está mal)."""
    get = (sesion or requests).get
    ultimo: Exception | None = None
    for intento in range(1, reintentos + 1):
        t0 = time.time()
        registro = {"momento": datetime.now(timezone.utc).isoformat(timespec="seconds"), "intento": intento}
        try:
            r = get(url, params=params, timeout=timeout)
            registro["url"] = r.url
            registro["segundos"] = round(time.time() - t0, 2)
            registro["http"] = r.status_code
            if r.status_code >= 500:
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            r.raise_for_status()
            filas = r.json()
            registro["filas"] = len(filas)
            _registrar(registro, log)
            return filas
        except requests.HTTPError as e:
            registro["error"] = str(e)[:200]
            _registrar(registro, log)
            ultimo = e
            if e.response is not None and e.response.status_code < 500:
                raise
        except (requests.Timeout, requests.ConnectionError) as e:
            registro.setdefault("url", url + "?" + "&".join(f"{k}={v}" for k, v in params.items()))
            registro["segundos"] = round(time.time() - t0, 2)
            registro["error"] = f"{type(e).__name__}: {str(e)[:150]}"
            _registrar(registro, log)
            ultimo = e
        if intento < reintentos:
            time.sleep(espera * intento)
    assert ultimo is not None
    raise ultimo


def paginar(params: dict, pagina: int = PAGINA, consulta=consultar, **kw) -> list[dict]:
    """Pagina con $limit/$offset; `params` debe traer un $order estable."""
    if "$order" not in params:
        raise ValueError("la paginación exige $order estable")
    filas: list[dict] = []
    offset = 0
    while True:
        p = {**params, "$limit": pagina, "$offset": offset}
        bloque = consulta(p, **kw)
        filas.extend(bloque)
        if len(bloque) < pagina:
            return filas
        offset += pagina


# --------------------------------------------------------------------------- construcción de consultas SoQL
def fin_exclusivo(anio: int, mes: int) -> date:
    return date(anio + (mes == 12), mes % 12 + 1, 1)


def where_rutas(rutas: list[tuple[str, str]]) -> str:
    if not rutas:
        raise ValueError("lista de rutas vacía")
    for o, d in rutas:
        if not (len(o) == 5 and len(d) == 5 and o.isdigit() and d.isdigit()):
            raise ValueError(f"código de municipio no válido: {o!r}, {d!r}")
    pares = " OR ".join(f"(municipio_origen_ruta='{o}' AND municipio_destino_ruta='{d}')" for o, d in rutas)
    return f"({pares})"


def where_mes(anio: int, mes: int, rutas: list[tuple[str, str]] | None = None) -> str:
    ini, fin = date(anio, mes, 1), fin_exclusivo(anio, mes)
    w = (f'fecha_despacho >= "{ini:%Y-%m-%d}T00:00:00" AND fecha_despacho < "{fin:%Y-%m-%d}T00:00:00" '
         f'AND fecha_despacho < "{FECHA_MAX_VALIDA}"')
    return w + (" AND " + where_rutas(rutas) if rutas else "")


def params_descarga_mes(anio: int, mes: int, rutas: list[tuple[str, str]], pagina: int = PAGINA, offset: int = 0) -> dict:
    claves = "municipio_origen_ruta, municipio_destino_ruta, fecha_despacho, tipo_despacho, clase_vehiculo"
    return {
        "$select": claves + ", sum(pasajeros) as pasajeros, sum(despachos) as despachos",
        "$where": where_mes(anio, mes, rutas),
        "$group": claves,
        "$order": claves,
        "$limit": pagina,
        "$offset": offset,
    }


def params_ranking_dia(dia: date) -> dict:
    return {
        "$select": ("municipio_origen_ruta, municipio_destino_ruta, sum(pasajeros) as pasajeros, "
                    "sum(despachos) as despachos, count(*) as filas"),
        "$where": f'fecha_despacho = "{dia:%Y-%m-%d}T00:00:00" AND fecha_despacho < "{FECHA_MAX_VALIDA}"',
        "$group": "municipio_origen_ruta, municipio_destino_ruta",
        "$order": "municipio_origen_ruta, municipio_destino_ruta",
        "$limit": PAGINA,
    }


def segundo_miercoles(anio: int, mes: int) -> date:
    primero = date(anio, mes, 1)
    return primero + timedelta(days=(2 - primero.weekday()) % 7 + 7)


def dias_muestra(desde=(2021, 1), hasta=(2023, 12)) -> list[date]:
    out, (a, m) = [], desde
    while (a, m) <= hasta:
        out.append(segundo_miercoles(a, m))
        a, m = (a + (m == 12), m % 12 + 1)
    return out


# --------------------------------------------------------------------------- ranking
def armar_ranking(muestras: dict[str, list[dict]], n_dias: int | None = None) -> pd.DataFrame:
    """`muestras`: {fecha ISO: filas devueltas por params_ranking_dia}. Devuelve un renglón por par dirigido
    (origen, destino) sin rutas intramunicipales, con pasajeros y despachos de la muestra, días con registros y datos
    del sentido de regreso."""
    n_dias = len(muestras) if n_dias is None else n_dias
    partes = []
    for dia, filas in muestras.items():
        if not filas:
            continue
        d = pd.DataFrame(filas)
        d["fecha"] = dia
        partes.append(d)
    cols = ["origen", "destino", "pasajeros", "despachos", "filas", "dias_con_registros",
            "pasajeros_regreso", "despachos_regreso", "dias_regreso", "min_ida_regreso", "n_dias_muestra"]
    if not partes:
        return pd.DataFrame(columns=cols)
    t = pd.concat(partes, ignore_index=True).rename(
        columns={"municipio_origen_ruta": "origen", "municipio_destino_ruta": "destino"})
    for c in ("pasajeros", "despachos", "filas"):
        t[c] = pd.to_numeric(t[c]).astype("int64")
    t = t[t["origen"] != t["destino"]]
    g = t.groupby(["origen", "destino"], as_index=False).agg(
        pasajeros=("pasajeros", "sum"), despachos=("despachos", "sum"), filas=("filas", "sum"),
        dias_con_registros=("fecha", "nunique"))
    reg = g.rename(columns={"origen": "destino", "destino": "origen", "pasajeros": "pasajeros_regreso",
                            "despachos": "despachos_regreso", "dias_con_registros": "dias_regreso"})
    g = g.merge(reg[["origen", "destino", "pasajeros_regreso", "despachos_regreso", "dias_regreso"]],
                on=["origen", "destino"], how="left")
    for c in ("pasajeros_regreso", "despachos_regreso", "dias_regreso"):
        g[c] = g[c].fillna(0).astype("int64")
    g["min_ida_regreso"] = g[["pasajeros", "pasajeros_regreso"]].min(axis=1)
    g["n_dias_muestra"] = n_dias
    return g.sort_values(["min_ida_regreso", "pasajeros"], ascending=False, kind="stable").reset_index(drop=True)[cols]


def pares_ida_regreso(ranking: pd.DataFrame, divipola: pd.DataFrame | None = None, n: int = 15) -> pd.DataFrame:
    """Un renglón por par no ordenado (primero el sentido con código de origen menor), solo si existe el regreso,
    ordenado por el mínimo de los dos sentidos. Agrega nombres y departamentos si se da `divipola`."""
    r = ranking[ranking["pasajeros_regreso"] > 0]
    r = r[r["origen"] < r["destino"]].sort_values(["min_ida_regreso", "pasajeros"], ascending=False, kind="stable").head(n)
    r = r.rename(columns={"pasajeros": "pasajeros_ida", "dias_con_registros": "dias_ida"}).reset_index(drop=True)
    if divipola is not None:
        nom = divipola.set_index("cod_mpio")
        for lado in ("origen", "destino"):
            r[f"{lado}_nombre"] = r[lado].map(nom["nom_mpio"])
            r[f"{lado}_dpto"] = r[lado].map(nom["dpto"])
    return r


def codigos_fuera_de_divipola(ranking: pd.DataFrame, divipola: pd.DataFrame) -> list[str]:
    conocidos = set(divipola["cod_mpio"])
    return sorted((set(ranking["origen"]) | set(ranking["destino"])) - conocidos)


def leer_divipola(ruta: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(ruta or RAIZ / "data" / "processed" / "m1" / "divipola.csv", dtype=str)


def cmd_ranking(args) -> int:
    dias = dias_muestra()
    muestras: dict[str, list[dict]] = {}
    fallidos: dict[str, str] = {}

    def una(dia: date):
        t0 = time.time()
        try:
            filas = paginar(params_ranking_dia(dia), timeout=args.timeout, reintentos=args.reintentos)
            return dia, filas, None, time.time() - t0
        except Exception as e:  # se registra y se sigue
            return dia, None, f"{type(e).__name__}: {str(e)[:150]}", time.time() - t0

    with ThreadPoolExecutor(max_workers=min(args.paralelo, 4)) as ex:
        for dia, filas, err, seg in ex.map(una, dias):
            if err:
                fallidos[dia.isoformat()] = err
                print(f"{dia} FALLO tras reintentos ({seg:.0f} s): {err}", flush=True)
            else:
                muestras[dia.isoformat()] = filas
                print(f"{dia} {len(filas)} pares ({seg:.0f} s)", flush=True)
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "ranking_dias.json").write_text(json.dumps({"muestras": muestras, "fallidos": fallidos}, ensure_ascii=False),
                                           encoding="utf-8")
    rk = armar_ranking(muestras, n_dias=len(dias))
    rk.to_csv(RAW / "ranking_rutas.csv", index=False)
    print(f"\nDias con datos: {len(muestras)}/{len(dias)}; faltantes: {sorted(fallidos) or 'ninguno'}")
    print(f"Guardado {RAW / 'ranking_rutas.csv'} ({len(rk)} pares dirigidos)")
    try:
        dv = leer_divipola()
    except FileNotFoundError:
        print("Falta divipola.csv: corre antes el subcomando divipola")
        return 0
    top = pares_ida_regreso(rk, dv, 15)
    pd.set_option("display.width", 250, "display.max_columns", 30)
    print(top.to_string())
    top.to_csv(RAW / "ranking_top15_pares.csv", index=False)
    print("Codigos fuera de DIVIPOLA:", codigos_fuera_de_divipola(rk, dv) or "ninguno")
    return 0


# --------------------------------------------------------------------------- descarga por mes
def meses_entre(ini: date, fin: date) -> list[tuple[int, int]]:
    out, (a, m) = [], (ini.year, ini.month)
    while (a, m) <= (fin.year, fin.month):
        out.append((a, m))
        a, m = (a + (m == 12), m % 12 + 1)
    return out


def descargar_rutas(rutas: list[tuple[str, str]], ini: date, fin: date, destino: Path | None = None,
                    consulta=consultar, **kw) -> list[Path]:
    """Un parquet por mes en `destino` (reanudable: si el mes ya existe, lo salta)."""
    destino = destino or RAW / "rutas"
    destino.mkdir(parents=True, exist_ok=True)
    escritos = []
    for anio, mes in meses_entre(ini, fin):
        f = destino / f"{anio}-{mes:02d}.parquet"
        if f.exists():
            print(f"{f.name} ya existe: se salta")
            continue
        filas = paginar(params_descarga_mes(anio, mes, rutas), consulta=consulta, **kw)
        cols = ["municipio_origen_ruta", "municipio_destino_ruta", "fecha_despacho", "tipo_despacho",
                "clase_vehiculo", "pasajeros", "despachos"]
        df = pd.DataFrame(filas, columns=cols)
        df["fecha_despacho"] = pd.to_datetime(df["fecha_despacho"])
        for c in ("pasajeros", "despachos"):
            df[c] = pd.to_numeric(df[c]).astype("int64")
        tmp = f.with_suffix(".parquet.tmp")
        df.to_parquet(tmp, index=False)
        tmp.replace(f)
        print(f"{f.name}: {len(df)} filas")
        escritos.append(f)
    return escritos


def leer_rutas(texto: str) -> list[tuple[str, str]]:
    """'05001-11001,11001-05001' -> [('05001', '11001'), ('11001', '05001')]"""
    out = []
    for p in texto.split(","):
        if p.strip():
            o, d = p.strip().split("-")
            out.append((o, d))
    return out


def cmd_descargar(args) -> int:
    descargar_rutas(leer_rutas(args.rutas), date.fromisoformat(args.desde), date.fromisoformat(args.hasta),
                    timeout=args.timeout, reintentos=args.reintentos)
    return 0


# --------------------------------------------------------------------------- DIVIPOLA
def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cmd_divipola(args) -> int:
    filas = paginar({"$order": "cod_mpio"}, pagina=2000, url=URL_DIVIPOLA, timeout=args.timeout, reintentos=args.reintentos)
    df = pd.DataFrame(filas)
    salida = RAIZ / "data" / "processed" / "m1" / "divipola.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(salida, index=False, encoding="utf-8", lineterminator="\n")
    print(f"{salida}: {len(df)} filas, columnas {list(df.columns)}")
    print(f"URL: {URL_DIVIPOLA}  fecha: {date.today()}  SHA-256: {sha256(salida)}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nombre, fn in (("ranking", cmd_ranking), ("descargar", cmd_descargar), ("divipola", cmd_divipola)):
        s = sub.add_parser(nombre)
        s.add_argument("--timeout", type=float, default=300)
        s.add_argument("--reintentos", type=int, default=3)
        if nombre == "ranking":
            s.add_argument("--paralelo", type=int, default=4)
        if nombre == "descargar":
            s.add_argument("--rutas", required=True, help="'05001-11001,11001-05001' (origen-destino, separados por coma)")
            s.add_argument("--desde", required=True, help="AAAA-MM-DD")
            s.add_argument("--hasta", required=True, help="AAAA-MM-DD")
        s.set_defaults(fn=fn)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
