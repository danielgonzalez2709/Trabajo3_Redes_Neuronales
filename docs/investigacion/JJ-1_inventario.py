#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""JJ-1 fase A (A1): inventario medido del conjunto Travel Recommendation Dataset (Kaggle, M3).

Solo archivos locales (data/raw/m3/), sin internet y sin aleatoriedad (no se usa ninguna semilla: todo es determinista).
Dependencias: biblioteca estandar + pandas + numpy (+ scipy si esta instalado; si no, las p se calculan con una
implementacion explicita de la funcion gamma incompleta y Kruskal-Wallis/Spearman quedan como TODO(dato-faltante)).

Regenerar la salida desde la raiz del repositorio:
    .venv\\Scripts\\python -I docs/investigacion/JJ-1_inventario.py

Escribe docs/investigacion/JJ-1_inventario_salida.txt (UTF-8) y la imprime.

Los CSV y el .zip se tratan como datos no confiables: solo se leen (el .zip se lee en memoria con zipfile, sin extraer).
Este script mide; no describe el significado de las columnas ni decide nada de modelado.
"""
import csv
import hashlib
import io
import math
import re
import sys
import warnings
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

try:  # scipy es opcional
    from scipy import stats as sps
    HAY_SCIPY = True
except Exception:  # pragma: no cover
    sps = None
    HAY_SCIPY = False

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw" / "m3"
SALIDA = RAIZ / "docs" / "investigacion" / "JJ-1_inventario_salida.txt"

OUT = []
S = {}  # numeros clave para el resumen final (A1.14)


def P(*a):
    linea = " ".join(str(x) for x in a)
    OUT.append(linea)
    print(linea)


def H(cod, titulo):
    P("")
    P(f"## {cod} {titulo}")
    P("")


def sha(b):
    return hashlib.sha256(b).hexdigest()


# --------------------------------------------------------------------------- estadistica auxiliar
def _gammaincc(a, x):
    """Gamma incompleta regularizada superior Q(a, x) (serie / fraccion continua, Numerical Recipes)."""
    if x <= 0:
        return 1.0
    gln = math.lgamma(a)
    if x < a + 1.0:
        ap, s, d = a, 1.0 / a, 1.0 / a
        for _ in range(1000):
            ap += 1.0
            d *= x / ap
            s += d
            if abs(d) < abs(s) * 1e-15:
                break
        return 1.0 - s * math.exp(-x + a * math.log(x) - gln)
    b = x + 1.0 - a
    c = 1.0 / 1e-300
    d = 1.0 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1.0 / d
        dl = d * c
        h *= dl
        if abs(dl - 1.0) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - gln) * h


def chi2_sf(x, gl):
    if HAY_SCIPY:
        return float(sps.chi2.sf(x, gl))
    return _gammaincc(gl / 2.0, x / 2.0)


def chi2_uniforme(conteos):
    """chi2 = sum (O-E)^2/E con E = n/k, gl = k-1."""
    c = np.asarray(conteos, dtype=float)
    k, n = len(c), c.sum()
    e = n / k
    chi = float(((c - e) ** 2 / e).sum())
    gl = k - 1
    return chi, gl, chi2_sf(chi, gl), float(c.min()), float(c.max())


def chi2_indep(tabla):
    """chi2 de independencia sobre una tabla de contingencia (DataFrame); devuelve chi2, gl, p, V de Cramer, n."""
    t = tabla.loc[tabla.sum(axis=1) > 0, tabla.sum(axis=0) > 0]
    obs = t.values.astype(float)
    r, c = obs.sum(axis=1, keepdims=True), obs.sum(axis=0, keepdims=True)
    n = obs.sum()
    if obs.shape[0] < 2 or obs.shape[1] < 2:
        return float("nan"), 0, float("nan"), float("nan"), n
    esp = r @ c / n
    chi = float(((obs - esp) ** 2 / esp).sum())
    gl = (obs.shape[0] - 1) * (obs.shape[1] - 1)
    v = math.sqrt(chi / (n * (min(obs.shape) - 1)))
    return chi, gl, chi2_sf(chi, gl), v, n


def kruskal(grupos):
    if not HAY_SCIPY:
        return None
    grupos = [np.asarray(g) for g in grupos if len(g) > 0]
    if len(grupos) < 2:
        return None
    h, p = sps.kruskal(*grupos)
    return float(h), float(p)


def f4(x):
    if isinstance(x, (float, np.floating)):
        if math.isnan(x):
            return "nan"
        return f"{x:.4g}" if (abs(x) < 1e-3 or abs(x) >= 1e6) and x != 0 else f"{x:.4f}"
    return str(x)


def descr(x):
    x = np.asarray(x, dtype=float)
    q = np.percentile(x, [0, 25, 50, 75, 100])
    return {"min": q[0], "q1": q[1], "mediana": q[2], "q3": q[3], "max": q[4], "media": x.mean(),
            "unicos": len(np.unique(x))}


def descr_txt(x):
    d = descr(x)
    return ", ".join(f"{k}={f4(v)}" for k, v in d.items())


def frec(serie, orden="indice", maxn=40):
    """Lineas 'valor: n (p%)' con la frecuencia de cada valor."""
    vc = serie.value_counts(dropna=False)
    vc = vc.sort_index() if orden == "indice" else vc.sort_values(ascending=False, kind="stable")
    tot = len(serie)
    res = []
    for i, (v, n) in enumerate(vc.items()):
        if i >= maxn:
            res.append(f"    ... ({len(vc) - maxn} valores mas)")
            break
        res.append(f"    {v!r}: {n} ({100.0 * n / tot:.2f}%)")
    return res


def es_texto(s):
    return not pd.api.types.is_numeric_dtype(s)


def tipo_inferido(s):
    if pd.api.types.is_bool_dtype(s):
        return "booleano"
    if pd.api.types.is_integer_dtype(s):
        return "entero"
    if pd.api.types.is_float_dtype(s):
        return "decimal"
    x = s.dropna().astype(str)
    if len(x) and x.str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
        return "texto (todos con forma AAAA-MM-DD)"
    return "texto"


def periodicidad(ids, vals, kmax=60):
    """Pureza de 'vals' dentro de cada clase de residuo ids mod k, k=1..kmax; devuelve (pureza por k, k minimo determinista)."""
    ids = np.asarray(ids)
    v = pd.Series(np.asarray(vals)).reset_index(drop=True)
    pur, kmin = {}, None
    for k in range(1, kmax + 1):
        ct = pd.crosstab(pd.Series(ids % k), v)
        p = ct.max(axis=1).sum() / ct.values.sum()
        pur[k] = float(p)
        if kmin is None and p == 1.0:
            kmin = k
    return pur, kmin


def es_contador(s):
    """True si la columna entera es exactamente 1..n en el orden del archivo."""
    return pd.api.types.is_integer_dtype(s) and bool((s.values == np.arange(1, len(s) + 1)).all())


# --------------------------------------------------------------------------- carga
def cargar():
    if not RAW.is_dir():
        raise SystemExit(f"No existe {RAW}")
    crudos = {p.name: p.read_bytes() for p in sorted(RAW.iterdir()) if p.is_file()}
    zips = [n for n in crudos if n.lower().endswith(".zip")]
    csvs = [n for n in crudos if n.lower().endswith(".csv")]
    dfs = {n: pd.read_csv(io.BytesIO(crudos[n])) for n in csvs}
    return crudos, zips, csvs, dfs


CRUDOS, ZIPS, CSVS, DFS = cargar()
USER_PAT, DEST_PAT = r"^user.?id$", r"^destination.?id$"


def cols(df, pat):
    return [c for c in df.columns if re.search(pat, c, re.I)]


def rol(nombre):
    df = DFS[nombre]
    u, d = bool(cols(df, USER_PAT)), bool(cols(df, DEST_PAT))
    return "interaccion" if u and d else "usuarios" if u else "destinos" if d else "otro"


ROLES = {n: rol(n) for n in CSVS}
NOM_U = [n for n, r in ROLES.items() if r == "usuarios"]
NOM_D = [n for n, r in ROLES.items() if r == "destinos"]
NOM_R = [n for n in CSVS if ROLES[n] == "interaccion" and "review" in n.lower()]
NOM_H = [n for n in CSVS if ROLES[n] == "interaccion" and "history" in n.lower()]
assert len(NOM_U) == len(NOM_D) == len(NOM_R) == len(NOM_H) == 1, ROLES
NOM_U, NOM_D, NOM_R, NOM_H = NOM_U[0], NOM_D[0], NOM_R[0], NOM_H[0]
U, D, R, HI = DFS[NOM_U], DFS[NOM_D], DFS[NOM_R], DFS[NOM_H]
UC = cols(U, USER_PAT)[0]          # id de usuario en la tabla maestra
DC = cols(D, DEST_PAT)[0]          # id de destino en la tabla maestra
INTER = {"Reviews": (R, NOM_R), "UserHistory": (HI, NOM_H)}
UCOL = {k: cols(v[0], USER_PAT)[0] for k, v in INTER.items()}
DCOL = {k: cols(v[0], DEST_PAT)[0] for k, v in INTER.items()}
RCOL = {k: cols(v[0], "rating")[0] for k, v in INTER.items()}
assert all(len(cols(v[0], "rating")) == 1 for v in INTER.values())
ETQ = {NOM_U: "Users", NOM_D: "Destinations", NOM_R: "Reviews", NOM_H: "UserHistory"}
ORDEN = [NOM_D, NOM_R, NOM_H, NOM_U]


# =========================================================================== A1.1
def a11():
    H("A1.1", "Archivos")
    P("Ruta (relativa a la raiz): data/raw/m3/ ; SHA-256 de los bytes tal como estan en disco.")
    P(f"Entorno: Python {sys.version.split()[0]}, pandas {pd.__version__}, numpy {np.__version__}, "
      f"scipy {'%s' % __import__('scipy').__version__ if HAY_SCIPY else 'NO instalado'}")
    P("")
    for n, b in CRUDOS.items():
        P(f"- {n}: {len(b)} bytes, sha256={sha(b)}")
    otros = [n for n in CRUDOS if n not in ZIPS and n not in CSVS]
    P(f"Archivos que no son .zip ni .csv en la carpeta: {otros if otros else 'ninguno'}")
    for z in ZIPS:
        P("")
        P(f"Miembros de {z} (leidos en memoria, sin extraer):")
        with zipfile.ZipFile(io.BytesIO(CRUDOS[z])) as zf:
            malos = zf.testzip()
            P(f"  testzip (CRC): {'sin errores' if malos is None else 'MIEMBRO CON ERROR ' + malos}")
            miembros = []
            for info in zf.infolist():
                seguro = (not info.filename.startswith(("/", "\\"))) and ".." not in Path(info.filename).parts
                if info.file_size > 50_000_000 or not seguro:
                    P(f"  {info.filename}: OMITIDO (tamano o ruta sospechosos)")
                    continue
                datos = zf.read(info)
                miembros.append(info.filename)
                suelto = CRUDOS.get(Path(info.filename).name)
                igual = "no hay CSV suelto con ese nombre" if suelto is None else (
                    "CSV suelto IDENTICO byte a byte" if suelto == datos else "CSV suelto DIFERENTE")
                P(f"  {info.filename}: tamano={info.file_size} (comprimido {info.compress_size}), "
                  f"sha256={sha(datos)}; {igual}")
            sueltos_sin = [n for n in CSVS if n not in [Path(m).name for m in miembros]]
            P(f"  CSV sueltos que no estan en el .zip: {sueltos_sin if sueltos_sin else 'ninguno'}")
    P("")
    P("Codificacion, fin de linea y filas (csv de la biblioteca estandar vs pandas):")
    for n in ORDEN:
        b = CRUDOS[n]
        bom = b.startswith(b"\xef\xbb\xbf")
        try:
            txt = b.decode("utf-8")
            dec = "utf-8 estricto valido"
        except UnicodeDecodeError as e:
            txt = b.decode("utf-8", errors="replace")
            dec = f"utf-8 INVALIDO ({e})"
        no_ascii = sum(1 for ch in txt if ord(ch) > 127)
        crlf = b.count(b"\r\n")
        lf = b.count(b"\n") - crlf
        cr = b.count(b"\r") - crlf
        filas_csv = [f for f in csv.reader(io.StringIO(txt, newline="")) if f]
        largos = sorted({len(f) for f in filas_csv})
        n_csv = len(filas_csv) - 1
        P(f"- {n}: {dec}; BOM={'si' if bom else 'no'}; caracteres no ASCII={no_ascii}; "
          f"fin de linea CRLF={crlf}, LF solo={lf}, CR solo={cr}; termina en salto de linea={b.endswith((b'\n', b'\r'))}")
        P(f"    filas de datos con csv estandar={n_csv}; con pandas={len(DFS[n])}; "
          f"{'coinciden' if n_csv == len(DFS[n]) else 'NO COINCIDEN'}; "
          f"numero de campos por fila (valores distintos)={largos}; lineas vacias ignoradas="
          f"{sum(1 for f in csv.reader(io.StringIO(txt, newline='')) if not f)}")
        S[f"filas {ETQ[n]}"] = len(DFS[n])
    P("")
    P("Roles detectados por nombre de columna (no por significado): "
      + "; ".join(f"{ETQ[n]}={ROLES[n]}" for n in ORDEN))


# =========================================================================== A1.2
def a12():
    H("A1.2", "Estructura por archivo")
    for n in ORDEN:
        df = DFS[n]
        P(f"### {ETQ[n]} ({n}): {len(df)} filas x {df.shape[1]} columnas")
        for c in df.columns:
            s = df[c]
            falt = int(s.isna().sum())
            extra = ""
            if es_texto(s):
                vac = int((s.dropna().astype(str).str.strip() == "").sum())
                esp = int((s.dropna().astype(str) != s.dropna().astype(str).str.strip()).sum())
                extra = f", cadenas vacias={vac}, con espacios en los extremos={esp}"
            ej = list(dict.fromkeys(s.dropna().tolist()))[:3]
            P(f"  - {c}: dtype pandas={s.dtype}; tipo inferido={tipo_inferido(s)}; faltantes={falt}{extra}; "
              f"valores unicos={s.nunique(dropna=True)}; ejemplos={ej}")
        dup = int(df.duplicated().sum())
        P(f"  Filas duplicadas exactas: {dup}")
        prim = df.columns[0]
        if es_contador(df[prim]):
            d2 = int(df.drop(columns=[prim]).duplicated().sum())
            P(f"  La primera columna ({prim}) es un contador 1..{len(df)} sin huecos y en orden: SI (medido).")
            P(f"  Filas duplicadas ignorando {prim}: {d2} (filas sobrantes; filas distintas sin ella: "
              f"{len(df) - d2})")
        else:
            P(f"  La primera columna ({prim}) NO es un contador 1..n en orden: no se calcula duplicados ignorandola.")
        P("")


# =========================================================================== A1.3
def a13():
    H("A1.3", "Claves e integridad referencial")
    P("Columnas candidatas a id (por nombre): usuario ~ '^user.?id$', destino ~ '^destination.?id$'; "
      "otras terminadas en 'ID' = id de fila.")
    for n in ORDEN:
        df = DFS[n]
        for c in df.columns:
            if re.search(r"id$", c, re.I):
                s = df[c]
                ent = pd.api.types.is_integer_dtype(s)
                linea = f"- {ETQ[n]}.{c}: entero={ent}; n={len(s)}; unicos={s.nunique()}; unica={s.is_unique}"
                if ent:
                    lo, hi = int(s.min()), int(s.max())
                    ausentes = sorted(set(range(lo, hi + 1)) - set(s.tolist()))
                    linea += (f"; rango=[{lo}, {hi}]; huecos en el rango={len(ausentes)}"
                              + (f" (primeros: {ausentes[:10]})" if ausentes else ""))
                P(linea)
    P("")
    P(f"Tabla maestra de usuarios: {ETQ[NOM_U]}.{UC} (unica: {U[UC].is_unique}); "
      f"tabla maestra de destinos: {ETQ[NOM_D]}.{DC} (unica: {D[DC].is_unique})")
    mu, md = set(U[UC]), set(D[DC])
    S["usuarios (maestra)"] = len(mu)
    S["destinos (maestra)"] = len(md)
    P("")
    P("Integridad referencial (identificadores de las interacciones que no estan en la tabla maestra):")
    for k, (df, n) in INTER.items():
        for ent, col, maestro in (("usuario", UCOL[k], mu), ("destino", DCOL[k], md)):
            fuera = ~df[col].isin(maestro)
            P(f"- {k}.{col} ({ent}): filas sin maestro={int(fuera.sum())}; "
              f"identificadores distintos sin maestro={df.loc[fuera, col].nunique()}; "
              f"identificadores distintos usados={df[col].nunique()}; "
              f"rango usado=[{df[col].min()}, {df[col].max()}]")
    P("")
    P("Maestro que no aparece en cada interaccion se mide en A1.5.")


# =========================================================================== A1.4
def a14():
    H("A1.4", "Calificaciones y puntajes (escala medida)")
    P("Cuartiles con interpolacion lineal (numpy.percentile).")
    for k, (df, n) in INTER.items():
        c = RCOL[k]
        s = df[c]
        vals = sorted(s.unique().tolist())
        P(f"### {k}.{c}: minimo={s.min()}, maximo={s.max()}, valores distintos={len(vals)} -> {vals}; "
          f"faltantes={int(s.isna().sum())}")
        P("  Frecuencia por valor:")
        for ln in frec(s):
            P(ln)
        P(f"  Resumen: {descr_txt(s)}")
        S[f"escala {k}.{c}"] = f"min={s.min()}, max={s.max()}, distintos={len(vals)} {vals}"
    P("")
    for n in (NOM_D, NOM_U):
        df = DFS[n]
        for c in df.columns:
            if pd.api.types.is_float_dtype(df[c]) or (re.search(r"popular|score|puntaj|rating", c, re.I)
                                                      and pd.api.types.is_numeric_dtype(df[c])):
                s = df[c]
                P(f"### {ETQ[n]}.{c} (numerica): {descr_txt(s)}; faltantes={int(s.isna().sum())}")
                S[f"{ETQ[n]}.{c}"] = f"min={f4(float(s.min()))}, max={f4(float(s.max()))}, unicos={s.nunique()}"
    P("")
    P("Otras columnas numericas enteras de las tablas maestras (no son calificaciones por nombre; se reportan por completitud):")
    for n in (NOM_D, NOM_U):
        df = DFS[n]
        for c in df.columns:
            if pd.api.types.is_integer_dtype(df[c]) and not re.search(r"id$", c, re.I):
                P(f"- {ETQ[n]}.{c}: {descr_txt(df[c])}")
                for ln in frec(df[c]):
                    P(ln)


# =========================================================================== A1.5
def conteos_rep(titulo, cuenta, maestro):
    """Resume conteos por id (Series indexada por id) frente a la lista maestra."""
    aparecen = cuenta
    n_ap = len(aparecen)
    en_m = len(set(aparecen.index) & set(maestro))
    P(f"  {titulo}")
    P(f"    aparecen={n_ap} (de ellos en la maestra={en_m}); maestra que NO aparece={len(set(maestro) - set(aparecen.index))}")
    P(f"    solo los que aparecen: min={aparecen.min()}, mediana={f4(float(aparecen.median()))}, "
      f"media={f4(float(aparecen.mean()))}, max={aparecen.max()}")
    ex = {i: int((aparecen == i).sum()) for i in (1, 2, 3, 4)}
    P("    exactamente 1/2/3/4 y >=5: " + ", ".join(f"{i}={v}" for i, v in ex.items()) + f", >=5={int((aparecen >= 5).sum())}")
    full = aparecen.reindex(list(maestro), fill_value=0)
    P(f"    contando 0 a la maestra que no aparece (n={len(full)}): min={full.min()}, "
      f"mediana={f4(float(full.median()))}, media={f4(float(full.mean()))}, max={full.max()}; "
      f"con 0={int((full == 0).sum())}, 1={int((full == 1).sum())}, 2={int((full == 2).sum())}, "
      f"3={int((full == 3).sum())}, 4={int((full == 4).sum())}, >=5={int((full >= 5).sum())}")


def densidad(npares, nu, nd):
    return npares / (nu * nd)


def a15():
    H("A1.5", "Interacciones por archivo (Reviews y UserHistory por separado)")
    mu, md = list(U[UC]), list(D[DC])
    for k, (df, n) in INTER.items():
        u, d, r = UCOL[k], DCOL[k], RCOL[k]
        P(f"### {k}: {len(df)} filas")
        pares = df[[u, d]].drop_duplicates()
        g = df.groupby([u, d]).size()
        rep = g[g > 1]
        P(f"  Pares (usuario, destino) distintos: {len(pares)}")
        P(f"  Pares repetidos (aparecen > 1 vez): {len(rep)}; filas sobrantes por repeticion: {int((rep - 1).sum())}; "
          f"max repeticiones de un par={int(g.max())}")
        if len(rep):
            nr = df.groupby([u, d])[r].nunique()
            P(f"  En los pares repetidos, calificaciones iguales entre repeticiones: "
              f"{int((nr[rep.index] == 1).sum())} de {len(rep)}")
        conteos_rep("Interacciones (filas) por usuario:", df.groupby(u).size(), mu)
        conteos_rep("Pares distintos por usuario:", pares.groupby(u).size(), mu)
        conteos_rep("Interacciones (filas) por destino:", df.groupby(d).size(), md)
        conteos_rep("Pares distintos por destino:", pares.groupby(d).size(), md)
        # densidad
        nu_m, nd_m = len(set(mu)), len(set(md))
        nu_a, nd_a = pares[u].nunique(), pares[d].nunique()
        da = densidad(len(pares), nu_m, nd_m)
        db = densidad(len(pares), nu_a, nd_a)
        P(f"  Densidad = pares distintos / (usuarios x destinos):")
        P(f"    (a) maestras: {len(pares)} / ({nu_m} x {nd_m}) = {da:.6f} ({100 * da:.4f}%)")
        P(f"    (b) que aparecen: {len(pares)} / ({nu_a} x {nd_a}) = {db:.6f} ({100 * db:.4f}%)")
        S[f"pares distintos {k}"] = len(pares)
        S[f"densidad (a) {k}"] = f"{da:.6f}"
        S[f"densidad (b) {k}"] = f"{db:.6f}"
        P("")


# =========================================================================== A1.6
def pares_de(k):
    df = INTER[k][0]
    return df[[UCOL[k], DCOL[k]]].rename(columns={UCOL[k]: "u", DCOL[k]: "d"}).drop_duplicates()


def a16():
    H("A1.6", "Solapamiento Reviews vs. UserHistory")
    pr, ph = pares_de("Reviews"), pares_de("UserHistory")
    sr, sh = set(map(tuple, pr.values)), set(map(tuple, ph.values))
    ambos, solo_r, solo_h = sr & sh, sr - sh, sh - sr
    P(f"Pares en ambos: {len(ambos)}; solo en Reviews: {len(solo_r)}; solo en UserHistory: {len(solo_h)}; "
      f"union: {len(sr | sh)}")
    S["pares en ambos"] = len(ambos)
    S["pares solo Reviews"] = len(solo_r)
    S["pares solo UserHistory"] = len(solo_h)
    ur, uh = set(pr["u"]), set(ph["u"])
    dr, dh = set(pr["d"]), set(ph["d"])
    P(f"Usuarios en ambos archivos: {len(ur & uh)} (solo Reviews {len(ur - uh)}, solo UserHistory {len(uh - ur)}); "
      f"destinos en ambos: {len(dr & dh)} (solo Reviews {len(dr - dh)}, solo UserHistory {len(dh - dr)})")
    a = R[[UCOL["Reviews"], DCOL["Reviews"], RCOL["Reviews"]]].rename(
        columns={UCOL["Reviews"]: "u", DCOL["Reviews"]: "d", RCOL["Reviews"]: "r_reviews"})
    b = HI[[UCOL["UserHistory"], DCOL["UserHistory"], RCOL["UserHistory"]]].rename(
        columns={UCOL["UserHistory"]: "u", DCOL["UserHistory"]: "d", RCOL["UserHistory"]: "r_history"})
    m = a.merge(b, on=["u", "d"], how="inner")
    P(f"Filas del cruce (fila de Reviews x fila de UserHistory) en pares comunes: {len(m)}")
    if len(m):
        iguales = int((m["r_reviews"] == m["r_history"]).sum())
        P(f"  Calificaciones iguales: {iguales}; distintas: {len(m) - iguales}")
        P("  Tabla cruzada (filas = Rating de Reviews, columnas = ExperienceRating de UserHistory):")
        P(pd.crosstab(m["r_reviews"], m["r_history"]).to_string())
    else:
        P("  No hay pares en comun: no hay calificaciones que comparar.")
    S["calificaciones iguales en pares comunes"] = (f"{iguales} de {len(m)}" if len(m) else "0 de 0")


# =========================================================================== A1.7
OPC = {}


def a17():
    H("A1.7", "Opciones de 'interaccion' (solo medidas; no se elige ninguna)")
    pr, ph = pares_de("Reviews"), pares_de("UserHistory")
    union = pd.concat([pr, ph]).drop_duplicates()
    inter = pr.merge(ph, on=["u", "d"], how="inner")
    OPC.update({"(i) solo Reviews": pr, "(ii) solo UserHistory": ph, "(iii) union de pares": union,
                "(iv) interseccion de pares": inter})
    mu, md = list(U[UC]), list(D[DC])
    for nombre, p in OPC.items():
        P(f"### {nombre}")
        nu_a, nd_a = p["u"].nunique(), p["d"].nunique()
        da, db = densidad(len(p), len(mu), len(md)), (densidad(len(p), nu_a, nd_a) if nu_a * nd_a else float("nan"))
        P(f"  pares distintos={len(p)}; usuarios que aparecen={nu_a}; destinos que aparecen={nd_a}")
        P(f"  densidad (a) maestras {len(p)}/({len(mu)}x{len(md)})={da:.6f}; "
          f"(b) que aparecen {len(p)}/({nu_a}x{nd_a})={db:.6f}")
        cu = p.groupby("u").size()
        cd = p.groupby("d").size()
        if len(cu):
            P(f"  pares por usuario (solo los que aparecen): min={cu.min()}, mediana={f4(float(cu.median()))}, "
              f"media={f4(float(cu.mean()))}, max={cu.max()}")
            P(f"  usuarios que aparecen con < 2: {int((cu < 2).sum())}; < 3: {int((cu < 3).sum())}; < 5: {int((cu < 5).sum())}")
            nofig = len(set(mu) - set(cu.index))
            full = cu.reindex(mu, fill_value=0)
            P(f"  contando 0 a los {nofig} usuarios maestros que no aparecen: con < 2: {int((full < 2).sum())}; "
              f"< 3: {int((full < 3).sum())}; < 5: {int((full < 5).sum())} (de {len(mu)}); "
              f"min={full.min()}, mediana={f4(float(full.median()))}, media={f4(float(full.mean()))}, max={full.max()}")
        if len(cd):
            P(f"  pares por destino (solo los que aparecen): min={cd.min()}, mediana={f4(float(cd.median()))}, "
              f"media={f4(float(cd.mean()))}, max={cd.max()}")
        S[f"{nombre}: pares / usuarios / destinos / dens(a) / dens(b)"] = (
            f"{len(p)} / {nu_a} / {nd_a} / {da:.6f} / {db:.6f}")
        P("")


# =========================================================================== A1.8
def a18():
    H("A1.8", "Fechas y horas")
    fecha_re = r"\d{4}-\d{2}-\d{2}"
    cand = []
    for n in ORDEN:
        df = DFS[n]
        for c in df.columns:
            por_nombre = bool(re.search(r"date|time|fecha|hora|dia|day|month|mes|year|ano", c, re.I))
            por_valor = es_texto(df[c]) and df[c].dropna().astype(str).str.fullmatch(fecha_re).mean() > 0.5
            if por_nombre or por_valor:
                cand.append((n, c, por_nombre, por_valor))
    P("Columnas candidatas (por nombre o porque >50% de sus valores tiene forma AAAA-MM-DD):")
    for n, c, a, b in cand:
        P(f"- {ETQ[n]}.{c} (por nombre={a}, por forma de valor={b})")
    S["columnas de fecha (forma AAAA-MM-DD)"] = [f"{ETQ[n]}.{c}" for n, c, a, b in cand if b] or "ninguna"
    for n, c, a, b in cand:
        df = DFS[n]
        s = df[c]
        P("")
        P(f"### {ETQ[n]}.{c}: dtype={s.dtype}; faltantes={int(s.isna().sum())}; valores distintos={s.nunique()}")
        st = s.dropna().astype(str)
        iso = pd.to_datetime(st, format="%Y-%m-%d", errors="coerce")
        mixto = pd.to_datetime(st, format="mixed", errors="coerce")
        P(f"  parsean como AAAA-MM-DD: {int(iso.notna().sum())} de {len(st)}; con analisis flexible (pandas 'mixed'): "
          f"{int(mixto.notna().sum())} de {len(st)}")
        if iso.notna().all() and len(st):
            P(f"  rango: {iso.min().date()} .. {iso.max().date()}; dias entre extremos={(iso.max() - iso.min()).days}")
            S[f"fecha {ETQ[n]}.{c}"] = (f"{iso.min().date()} .. {iso.max().date()}; "
                                         f"{s.nunique()} valores distintos")
        if s.nunique() <= 30:
            P("  frecuencia de cada valor:")
            for ln in frec(s):
                P(ln)
        else:
            P(f"  (mas de 30 valores distintos; no se lista la frecuencia)")
        P(f"  primeros 12 valores en el orden del archivo: {s.head(12).tolist()}")
        prim = df.columns[0]
        if es_contador(df[prim]) and pd.api.types.is_integer_dtype(df[prim]) and s.nunique() > 1:
            pur, kmin = periodicidad(df[prim].values, s.astype(str).values, kmax=60)
            P(f"  Patron periodico contra {prim} (pureza = fraccion de filas cuyo valor es el valor mas frecuente de su "
              f"clase {prim} mod k):")
            P("    " + ", ".join(f"k={k}:{pur[k]:.3f}" for k in range(1, 13)))
            P(f"    k minimo con pureza exacta 1.0 (k<=60): {kmin if kmin else 'ninguno'}")
            if kmin and kmin > 1:
                P(f"    Tabla {prim} mod {kmin} contra el valor:")
                ct = pd.crosstab(df[prim] % kmin, s.astype(str))
                P(ct.to_string())
            S[f"periodo de {ETQ[n]}.{c} respecto a {prim}"] = f"k minimo={kmin if kmin else 'ninguno'}"
        # usuarios con interacciones en mas de una fecha
        if n in (NOM_R, NOM_H):
            k = "Reviews" if n == NOM_R else "UserHistory"
            nd = df.groupby(UCOL[k])[c].nunique()
            P(f"  Usuarios con interacciones: {len(nd)}; con > 1 fecha distinta: {int((nd > 1).sum())}; "
              f"con exactamente 1: {int((nd == 1).sum())}")
            P("  distribucion del numero de fechas distintas por usuario:")
            for ln in frec(nd):
                P(ln)
            S[f"usuarios con >1 fecha ({k})"] = f"{int((nd > 1).sum())} de {len(nd)}"
    if not any(b for _, _, _, b in cand):
        P("No se encontro ninguna columna con forma de fecha.")


# =========================================================================== A1.9
PERIODO = {}


def minimo_k_tabla(df, col_id, columnas, etiqueta, kmax=60):
    P(f"  Patron periodico respecto a {col_id} (k minimo con pureza exacta 1.0, k<={kmax}; pureza para k=2..8):")
    for c in columnas:
        pur, kmin = periodicidad(df[col_id].values, df[c].astype(str).values, kmax)
        PERIODO[(etiqueta, c)] = kmin
        P(f"    {c}: k minimo={kmin if kmin else 'ninguno'}; pureza " + ", ".join(f"{k}:{pur[k]:.3f}" for k in range(2, 9)))


def a19():
    H("A1.9", "Destinos")
    nc = [c for c in D.columns if re.search(r"^name$|nombre", c, re.I)]
    assert len(nc) == 1, nc
    nc = nc[0]
    flotantes = [c for c in D.columns if pd.api.types.is_float_dtype(D[c])]
    otros = [c for c in D.columns if c not in (DC, nc) + tuple(flotantes)]
    P(f"Columna de nombre: {nc}; columnas decimales continuas: {flotantes}; demas atributos: {otros}")
    cnt = D.groupby(nc)[DC].nunique()
    P(f"Nombres distintos={D[nc].nunique()}; identificadores distintos={D[DC].nunique()}; filas={len(D)}")
    S["destinos: nombres distintos"] = D[nc].nunique()
    rep = cnt[cnt > 1]
    P(f"Nombres con mas de un identificador: {len(rep)}; identificadores por nombre: min={cnt.min()}, "
      f"mediana={f4(float(cnt.median()))}, max={cnt.max()}")
    S["destinos: nombres repetidos con distintos ids"] = f"{len(rep)} nombres (de {len(cnt)}), "\
                                                         f"{int(cnt.min())}-{int(cnt.max())} ids por nombre"
    filas = []
    for nom, gdf in D.groupby(nc, sort=False):
        fila = {nc: nom, "ids": gdf[DC].nunique(),
                "combinaciones distintas de demas atributos": len(gdf[otros].drop_duplicates())}
        for c in otros:
            fila[f"{c} distintos"] = gdf[c].nunique()
        for c in flotantes:
            fila[f"{c} min"] = round(float(gdf[c].min()), 4)
            fila[f"{c} media"] = round(float(gdf[c].mean()), 4)
            fila[f"{c} max"] = round(float(gdf[c].max()), 4)
        filas.append(fila)
    tabla = pd.DataFrame(filas)
    P("Por nombre (hasta 30 nombres):")
    P(tabla.head(30).to_string(index=False))
    cambian = int((cnt.index.map(lambda x: len(D.loc[D[nc] == x, otros].drop_duplicates())) > 1).sum())
    P(f"Nombres cuyos demas atributos CAMBIAN entre sus identificadores: {cambian} de {len(cnt)}")
    combos = D[[nc] + otros].drop_duplicates()
    P(f"Combinaciones distintas de (nombre + demas atributos): {len(combos)}")
    P("")
    minimo_k_tabla(D, DC, [nc] + otros, "Destinations")
    P(f"  Primeros 12 nombres en orden de {DC}: {D.sort_values(DC)[nc].head(12).tolist()}")
    S["destinos: periodo del nombre"] = f"k minimo={PERIODO[('Destinations', nc)]}"


# =========================================================================== A1.10
def a110():
    H("A1.10", "Usuarios")
    nc = [c for c in U.columns if re.search(r"^name$|nombre", c, re.I)][0]
    ec = [c for c in U.columns if re.search(r"mail|correo", c, re.I)][0]
    cnt = U.groupby(nc)[UC].nunique()
    P(f"Nombres distintos={U[nc].nunique()}; identificadores distintos={U[UC].nunique()}; filas={len(U)}")
    P(f"Nombres con mas de un identificador: {int((cnt > 1).sum())}; ids por nombre: min={cnt.min()}, "
      f"mediana={f4(float(cnt.median()))}, max={cnt.max()}")
    ne = U.groupby([nc, ec])[UC].nunique()
    P(f"Combinaciones ({nc}, {ec}) distintas={len(ne)}; con mas de un identificador={int((ne > 1).sum())}; "
      f"ids por combinacion: min={ne.min()}, mediana={f4(float(ne.median()))}, max={ne.max()}")
    S["usuarios: nombres distintos"] = U[nc].nunique()
    S["usuarios: combinaciones (nombre, correo) distintas"] = len(ne)
    P("")
    dom = U[ec].astype(str).str.split("@").str[-1]
    P(f"Dominios de correo (conteo): { {str(k): int(v) for k, v in dom.value_counts().items()} }")
    P(f"Correos sin '@' o con mas de una '@': {int((U[ec].astype(str).str.count('@') != 1).sum())}")
    local = U[ec].astype(str).str.split("@").str[0]
    exacto = (local == U[nc].astype(str).str.lower())
    P(f"Coherencia nombre-correo: parte local == nombre en minusculas (exacto): {int(exacto.sum())} de {len(U)}; "
      f"no coinciden: {int((~exacto).sum())}")
    if (~exacto).any():
        P(f"  ejemplos de no coincidencia: {U.loc[~exacto, [nc, ec]].drop_duplicates().head(5).values.tolist()}")
    S["usuarios: correo = nombre en minusculas + dominio"] = f"{int(exacto.sum())} de {len(U)}"
    P("")
    sex = [c for c in U.columns if re.search(r"gender|sexo|genero", c, re.I)]
    for gc in sex:
        gn = U.groupby(nc)[gc].nunique()
        P(f"{gc} por nombre: nombres con mas de un valor de {gc}: {int((gn > 1).sum())} de {len(gn)}")
        tb = pd.crosstab(U[nc], U[gc])
        P(tb.to_string())
    P("")
    cat = [c for c in U.columns if c != UC]
    minimo_k_tabla(U, UC, cat, "Users")
    conj = ["Users_conjunto"]
    pur, kmin = periodicidad(U[UC].values, U[cat].astype(str).agg("|".join, axis=1).values, 60)
    P(f"  Combinacion de TODAS las columnas salvo id: k minimo={kmin if kmin else 'ninguno'}; "
      f"combinaciones distintas={len(U[cat].drop_duplicates())}")
    PERIODO[("Users", "(todas)")] = kmin
    P("")
    P("Cruces entre columnas de usuarios (filas = primera, columnas = segunda); chi2 de independencia:")
    pares = [(a, b) for a in ("Preferences", "Gender", "NumberOfAdults", "NumberOfChildren")
             for b in ("Preferences", "Gender", "NumberOfAdults", "NumberOfChildren") if a < b and a in U and b in U]
    for a, b in pares:
        tb = pd.crosstab(U[a], U[b])
        chi, gl, p, v, n = chi2_indep(tb)
        P(f"- {a} x {b}: chi2={f4(chi)}, gl={gl}, p={f4(p)}, V de Cramer={f4(v)}")
        P(tb.to_string())


# =========================================================================== A1.11
LISTAS = {}


def a111():
    H("A1.11", "Variables de contenido de usuarios y destinos")
    for n in (NOM_U, NOM_D):
        df = DFS[n]
        P(f"### {ETQ[n]}")
        for c in df.columns:
            if c in (UC, DC):
                continue
            s = df[c]
            if pd.api.types.is_float_dtype(s):
                P(f"- {c}: decimal continua, {s.nunique()} valores distintos de {len(s)}; {descr_txt(s)}")
                continue
            k = s.nunique()
            tipo = "entero" if pd.api.types.is_integer_dtype(s) else "texto"
            P(f"- {c}: {tipo}, {k} categorias")
            if k <= 30:
                for ln in frec(s, orden="conteo"):
                    P(ln)
            sep = [sp for sp in (",", ";", "|") if es_texto(s) and s.astype(str).str.contains(re.escape(sp)).any()]
            if sep:
                sp = sep[0]
                P(f"  LISTA EN TEXTO: separador {sp!r} (otros separadores presentes: {sep[1:]}); se separa y se quitan espacios")
                partes = s.astype(str).str.split(sp).apply(lambda l: [x.strip() for x in l])
                planas = pd.Series([x for l in partes for x in l])
                P(f"  opciones distintas={planas.nunique()}; frecuencia de cada opcion (sobre {len(s)} filas):")
                for ln in frec(planas, orden="conteo"):
                    P(ln)
                nopc = partes.apply(len)
                P("  numero de opciones por fila:")
                for ln in frec(nopc):
                    P(ln)
                ordenadas = partes.apply(lambda l: tuple(sorted(l)))
                P(f"  combinaciones distintas (como texto original)={s.nunique()}; como conjunto (sin importar el orden)="
                  f"{ordenadas.nunique()}; opciones repetidas dentro de una fila: "
                  f"{int((partes.apply(lambda l: len(set(l))) != nopc).sum())}")
                P("  combinaciones (conjunto) y frecuencia:")
                for ln in frec(ordenadas.astype(str), orden="conteo"):
                    P(ln)
                LISTAS[(n, c)] = (sp, partes)
                S[f"{ETQ[n]}.{c}: opciones distintas / combinaciones"] = f"{planas.nunique()} / {ordenadas.nunique()}"
        P("")


# =========================================================================== A1.12
def a112():
    H("A1.12", "Textos libres")
    P("### Patron periodico de las columnas categoricas de Reviews y UserHistory respecto a su id de fila")
    for k, (df, n) in INTER.items():
        cc = [c for c in df.columns if c not in (UCOL[k], DCOL[k]) and not es_contador(df[c]) and df[c].nunique() <= 30]
        minimo_k_tabla(df, df.columns[0], cc, k)
    P("")
    for k, (df, n) in INTER.items():
        txt = [c for c in df.columns if es_texto(df[c]) and c not in (UCOL[k], DCOL[k])
               and not df[c].astype(str).str.fullmatch(r"\d{4}-\d{2}-\d{2}").all()]
        if not txt:
            P(f"{k}: sin columnas de texto libre (no fecha).")
            continue
        m = df.merge(D.add_prefix("d_"), left_on=DCOL[k], right_on="d_" + DC, how="left")
        m = m.merge(U.add_prefix("u_"), left_on=UCOL[k], right_on="u_" + UC, how="left")
        assert len(m) == len(df)
        for c in txt:
            s = df[c]
            P(f"### {k}.{c}: textos distintos={s.nunique()}; filas={len(s)}")
            for ln in frec(s, orden="conteo"):
                P(ln)
            S[f"textos distintos {k}.{c}"] = s.nunique()
            tb = pd.crosstab(m[c], m[RCOL[k]])
            chi, gl, p, v, _ = chi2_indep(tb)
            P(f"  Texto x {RCOL[k]}: chi2={f4(chi)}, gl={gl}, p={f4(p)}, V de Cramer={f4(v)}")
            P(tb.to_string())
            # contra cada atributo categorico de destinos (agrupados por particion identica)
            vistos = {}
            for dcn in D.columns:
                if dcn in (DC,) or pd.api.types.is_float_dtype(D[dcn]) or D[dcn].nunique() > 30:
                    continue
                clave = tuple(pd.factorize(D[dcn])[0])
                vistos.setdefault(clave, []).append(dcn)
            for grupo in vistos.values():
                cabeza = grupo[0]
                tb = pd.crosstab(m[c], m["d_" + cabeza])
                chi, gl, p, v, _ = chi2_indep(tb)
                P(f"  Texto x destino.{cabeza} (misma particion de destinos: {grupo}): "
                  f"chi2={f4(chi)}, gl={gl}, p={f4(p)}, V de Cramer={f4(v)}")
                P(tb.to_string())
                dom = tb.max(axis=1) / tb.sum(axis=1)
                P("  por texto, fraccion de filas en su columna modal: " + ", ".join(f"{i!r}:{x:.3f}" for i, x in dom.items()))
            for (nn, lc), (sp, partes) in LISTAS.items():
                if nn != NOM_U:
                    continue
                m["_pref"] = m["u_" + lc]
                tb = pd.crosstab(m[c], m["_pref"].rename("preferencias del usuario"))
                chi, gl, p, v, _ = chi2_indep(tb)
                P(f"  Texto x preferencias del usuario ({lc}): chi2={f4(chi)}, gl={gl}, p={f4(p)}, V de Cramer={f4(v)}")
                P(tb.to_string())
            P("")


# =========================================================================== A1.13
MAPA = {"Beaches": "Beach"}  # SUPUESTO DEL ANALISIS (no es significado de la fuente): singular/plural de una etiqueta


def a113():
    H("A1.13", "Senales de datos generados (solo medidas, sin concluir)")
    P("### A1.13a Uniformidad de las distribuciones (chi2 de bondad de ajuste a la uniforme; gl = categorias - 1)")
    P(f"p calculada con {'scipy.stats.chi2.sf' if HAY_SCIPY else 'implementacion explicita de la gamma incompleta'}.")
    if HAY_SCIPY:
        a, b = chi2_sf(7.5, 4), _gammaincc(2.0, 3.75)
        P(f"Autoverificacion de la implementacion explicita contra scipy en (chi2=7.5, gl=4): {a:.10f} vs {b:.10f}")
    P("")
    P("archivo.columna | categorias | n | min..max frecuencia | razon max/min | chi2 | gl | p")
    filas = 0
    for n in ORDEN:
        df = DFS[n]
        for c in df.columns:
            s = df[c]
            if pd.api.types.is_float_dtype(s) or s.nunique() > 30 or s.nunique() < 2 or es_contador(s):
                continue
            vc = s.value_counts()
            chi, gl, p, mn, mx = chi2_uniforme(vc.values)
            P(f"{ETQ[n]}.{c} | {len(vc)} | {len(s)} | {int(mn)}..{int(mx)} | {mx / mn:.3f} | {chi:.4f} | {gl} | {f4(p)}")
            filas += 1
    for (nn, lc), (sp, partes) in LISTAS.items():
        planas = pd.Series([x for l in partes for x in l])
        vc = planas.value_counts()
        chi, gl, p, mn, mx = chi2_uniforme(vc.values)
        P(f"{ETQ[nn]}.{lc} (opciones separadas) | {len(vc)} | {len(planas)} | {int(mn)}..{int(mx)} | {mx / mn:.3f} | "
          f"{chi:.4f} | {gl} | {f4(p)}")
    P("")
    P("### A1.13b Dispersion de interacciones por usuario y por destino frente a una asignacion uniforme al azar")
    P("Indice de dispersion = varianza / media de los conteos por id de la maestra (incluidos los ceros); bajo una asignacion "
      "uniforme e independiente (multinomial con m filas en N ids) vale 1 - 1/N, aprox. 1. Ceros esperados = N*(1-1/N)^m.")
    for k, (df, n) in INTER.items():
        for ent, col, maestra in (("usuario", UCOL[k], U[UC]), ("destino", DCOL[k], D[DC])):
            cuenta = df.groupby(col).size().reindex(list(maestra), fill_value=0)
            N, m = len(cuenta), int(cuenta.sum())
            P(f"- {k} por {ent}: N={N}, m={m}, media={cuenta.mean():.4f}, varianza={cuenta.var(ddof=0):.4f}, "
              f"indice de dispersion={cuenta.var(ddof=0) / cuenta.mean():.4f} (esperado {1 - 1 / N:.4f}); "
              f"ceros observados={int((cuenta == 0).sum())}, esperados={N * (1 - 1 / N) ** m:.1f}; max={cuenta.max()}")
    P("")
    P("### A1.13c Patrones periodicos respecto al identificador (de A1.8-A1.10; k minimo con pureza exacta)")
    for (et, c), kmin in PERIODO.items():
        P(f"- {et}.{c}: {kmin if kmin else 'ninguno'}")
    P("")
    # ---- afinidad preferencias / tipo de destino
    P("### A1.13d Preferencias declaradas del usuario vs tipo de destino de sus interacciones")
    lista_u = [(nn, lc) for (nn, lc) in LISTAS if nn == NOM_U]
    tcol = [c for c in D.columns if re.search(r"^type$|categ|tipo", c, re.I)]
    if not lista_u or len(tcol) != 1:
        P("TODO(dato-faltante): no hay columna de preferencias en lista o no hay una unica columna de tipo de destino.")
    else:
        lc, tc = lista_u[0][1], tcol[0]
        opciones = sorted({x for l in LISTAS[lista_u[0]][1] for x in l})
        tipos = sorted(D[tc].unique())
        P(f"SUPUESTO DEL ANALISIS (no es significado de la fuente): emparejamiento explicito de vocabularios {MAPA}; "
          f"el resto de etiquetas se compara por igualdad exacta.")
        P(f"Opciones de {lc}: {opciones}; valores de {tc}: {tipos}")
        mapeo = {o: MAPA.get(o, o) for o in opciones}
        P(f"Emparejamiento aplicado: {mapeo}")
        sin = [o for o, t in mapeo.items() if t not in tipos]
        sin2 = [t for t in tipos if t not in mapeo.values()]
        P(f"Opciones sin tipo equivalente tras el emparejamiento: {sin if sin else 'ninguna'}; "
          f"tipos sin opcion equivalente: {sin2 if sin2 else 'ninguno'}")
        sep = LISTAS[lista_u[0]][0]
        prefs = U.set_index(UC)[lc].astype(str).apply(
            lambda t: frozenset(mapeo[x.strip()] for x in t.split(sep)))
        tipo_d = D.set_index(DC)[tc]
        cuota = D[tc].value_counts(normalize=True)
        P(f"Cuota de cada tipo en el catalogo maestro ({len(D)} destinos): "
          + ", ".join(f"{t}={cuota[t]:.3f}" for t in tipos))
        pu_cache = {}

        def pu(fs):
            if fs not in pu_cache:
                pu_cache[fs] = float(sum(cuota.get(t, 0.0) for t in fs))
            return pu_cache[fs]

        P("Para cada opcion de interaccion (mismos pares distintos de A1.7): "
          "tasa observada = fraccion de pares con tipo del destino en las preferencias del usuario; "
          "tasa esperada si el destino se eligiera al azar del catalogo maestro = media de P(tipo en preferencias) "
          "sobre los mismos pares; z = (obs - esp)/sqrt(suma p(1-p)).")
        for nombre, p in OPC.items():
            q = p[p["u"].isin(prefs.index) & p["d"].isin(tipo_d.index)]
            if not len(q):
                P(f"- {nombre}: sin pares")
                continue
            fs = q["u"].map(prefs)
            td = q["d"].map(tipo_d)
            coin = np.array([t in f for t, f in zip(td, fs)])
            pe = np.array([pu(f) for f in fs])
            obs, esp = coin.mean(), pe.mean()
            var = (pe * (1 - pe)).sum()
            z = (coin.sum() - pe.sum()) / math.sqrt(var) if var > 0 else float("nan")
            pz = math.erfc(abs(z) / math.sqrt(2)) if not math.isnan(z) else float("nan")
            P(f"- {nombre}: pares usados={len(q)} (descartados por id sin maestro: {len(p) - len(q)}); "
              f"observada={obs:.4f}; esperada al azar={esp:.4f}; razon={obs / esp:.3f}; z={z:.3f}; p bilateral={f4(pz)}")
            S[f"afinidad {nombre}: obs / esperada / z"] = f"{obs:.4f} / {esp:.4f} / {z:.2f}"
            tb = pd.crosstab(fs.apply(lambda f: ", ".join(sorted(f))).rename("preferencias (emparejadas)"),
                             td.rename("tipo de destino"))
            chi, gl, pp, v, _ = chi2_indep(tb)
            P(f"    Preferencias x tipo de destino: chi2={f4(chi)}, gl={gl}, p={f4(pp)}, V de Cramer={f4(v)}")
            P(tb.to_string())
    P("")
    # ---- asociacion de la calificacion con otras variables
    P("### A1.13e Asociacion de la calificacion con otras variables")
    P("Por factor: media de la calificacion por grupo (n), chi2 de independencia calificacion x grupo y Kruskal-Wallis "
      "(H, p). Los factores de usuario/destino se unen por id desde las tablas maestras (prefijos u_ y d_). "
      "Columnas de las maestras con particion identica a otra ya incluida se agrupan en una sola.")
    for k, (df, n) in INTER.items():
        m = df.merge(D.add_prefix("d_"), left_on=DCOL[k], right_on="d_" + DC, how="left")
        m = m.merge(U.add_prefix("u_"), left_on=UCOL[k], right_on="u_" + UC, how="left")
        assert len(m) == len(df)
        r = RCOL[k]
        factores, particiones = {}, {}
        propios = [c for c in df.columns if c not in (UCOL[k], DCOL[k], r) and es_texto(df[c]) and df[c].nunique() <= 30]
        for c in propios:
            factores[f"{k}.{c}"] = m[c].astype(str)
        for pref, tabla, idc in (("d_", D, DC), ("u_", U, UC)):
            for c in tabla.columns:
                if c == idc or pd.api.types.is_float_dtype(tabla[c]) or tabla[c].nunique() > 30:
                    continue
                clave = (pref, tuple(pd.factorize(tabla[c])[0]))
                if clave in particiones:
                    particiones[clave].append(c)
                    continue
                particiones[clave] = [c]
                factores[f"{pref}{c}"] = m[pref + c].astype(str)
        for clave, grupo in particiones.items():
            if len(grupo) > 1:
                P(f"  (misma particion: {[clave[0] + g for g in grupo]}; se usa {clave[0] + grupo[0]})")
        # coincidencia con preferencias
        if lista_u and len(tcol) == 1:
            sep = LISTAS[lista_u[0]][0]
            mm = {o: MAPA.get(o, o) for o in opciones}
            tdest = m["d_" + tcol[0]]
            coinc = [(t in {mm[x.strip()] for x in str(pf).split(sep)}) for t, pf in zip(tdest, m["u_" + lista_u[0][1]])]
            factores["coincide_tipo_con_preferencias (supuesto de emparejamiento)"] = pd.Series(coinc, index=m.index).astype(str)
        P(f"#### {k} (calificacion = {r}, n={len(m)})")
        for fn, f in factores.items():
            tb = pd.crosstab(f, m[r])
            chi, gl, p, v, _ = chi2_indep(tb)
            gr = [m.loc[f == v_, r].values for v_ in sorted(f.unique())]
            kw = kruskal(gr)
            medias = m.groupby(f)[r].agg(["size", "mean"])
            P(f"- {fn}: grupos={len(medias)}; chi2={f4(chi)}, gl={gl}, p={f4(p)}, V={f4(v)}; "
              f"Kruskal-Wallis=" + (f"H={f4(kw[0])}, p={f4(kw[1])}" if kw else "TODO(dato-faltante)"))
            P("    medias: " + ", ".join(f"{i}: {row['mean']:.3f} (n={int(row['size'])})" for i, row in medias.head(30).iterrows()))
        if HAY_SCIPY:
            pop = [c for c in D.columns if pd.api.types.is_float_dtype(D[c])]
            for pc in pop:
                ok = m["d_" + pc].notna()
                rho, pr = sps.spearmanr(m.loc[ok, "d_" + pc], m.loc[ok, r])
                P(f"- Spearman entre {pc} del destino y {r}: rho={rho:.4f}, p={f4(float(pr))}, n={int(ok.sum())}")
                cd = df.groupby(DCOL[k]).size().reindex(D[DC].values, fill_value=0)
                rho2, p2 = sps.spearmanr(D[pc].values, cd.values)
                P(f"- Spearman entre {pc} del destino y el numero de filas de {k} del destino (sobre toda la maestra): "
                  f"rho={rho2:.4f}, p={f4(float(p2))}, n={len(cd)}")
        P("")


# =========================================================================== A1.14
def a114():
    H("A1.14", "Resumen final (numeros clave medidos)")
    P("clave | valor")
    P("--- | ---")
    for k, v in S.items():
        P(f"{k} | {v}")


def main():
    P("# JJ-1 A1 - Inventario medido del conjunto Travel Recommendation Dataset (data/raw/m3/)")
    P("Generado por docs/investigacion/JJ-1_inventario.py; solo archivos locales; sin aleatoriedad.")
    a11()
    a12()
    a13()
    a14()
    a15()
    a16()
    a17()
    a18()
    a19()
    a110()
    a111()
    a112()
    a113()
    a114()
    SALIDA.write_text("\n".join(OUT) + "\n", encoding="utf-8", newline="\n")
    print(f"\n[escrito] {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
