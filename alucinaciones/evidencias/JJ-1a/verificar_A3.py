#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""JJ-1a / A3 (cazador-alucinaciones): verificacion adversarial de las afirmaciones [A1-n] y [A2-n].

Codigo propio e independiente: NO importa ni copia docs/investigacion/JJ-1_inventario.py. Recalcula todo desde los CSV
de data/raw/m3/ (leidos solo con pandas / csv / zipfile, en memoria) y desde docs/investigacion/JJ-1_kaggle_metadata.json.
La unica vez que se toca el script de A1 es en la seccion R (reproducibilidad): se ejecuta el original, sin modificarlo,
con Path.write_text interceptado para que NO sobrescriba la salida guardada de A1.

Ejecutar desde la raiz del repositorio (sin internet; la re-descarga de Kaggle ya esta en redescarga_A3/):
    .venv\\Scripts\\python -I alucinaciones/evidencias/JJ-1a/verificar_A3.py
Escribe alucinaciones/evidencias/JJ-1a/verificar_A3_salida.txt (UTF-8). Sin aleatoriedad.
"""
import collections
import contextlib
import csv
import hashlib
import io
import json
import math
import pathlib
import re
import runpy
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

AQUI = Path(__file__).resolve().parent
RAIZ = Path(__file__).resolve().parents[3]
RAW = RAIZ / "data" / "raw" / "m3"
META = RAIZ / "docs" / "investigacion" / "JJ-1_kaggle_metadata.json"
A1_SCRIPT = RAIZ / "docs" / "investigacion" / "JJ-1_inventario.py"
A1_SALIDA = RAIZ / "docs" / "investigacion" / "JJ-1_inventario_salida.txt"
A2_RESP = AQUI / "respuesta-investigador-fuentes.md"
REDESC = AQUI / "redescarga_A3"
SALIDA = AQUI / "verificar_A3_salida.txt"

LINEAS = []
CUENTA = collections.Counter()


def out(*a):
    s = " ".join(str(x) for x in a)
    LINEAS.append(s)
    print(s)


def sec(t):
    out("")
    out(f"## {t}")
    out("")


def py(x):
    """Convierte escalares de numpy a tipos de Python (solo para imprimir y comparar limpio)."""
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, (list, tuple)):
        return type(x)(py(v) for v in x)
    if isinstance(x, dict):
        return {py(k): py(v) for k, v in x.items()}
    if isinstance(x, set):
        return {py(v) for v in x}
    return x


def chk(cid, desc, afirmado, medido, ok=None):
    """Compara lo afirmado con lo medido. ok=None -> igualdad exacta."""
    afirmado, medido = py(afirmado), py(medido)
    if ok is None:
        ok = afirmado == medido
    CUENTA["OK" if ok else "DIFIERE"] += 1
    out(f"[{cid}] {'OK     ' if ok else 'DIFIERE'} | {desc} | afirmado: {afirmado} | medido: {medido}")
    return ok


def h256(b):
    return hashlib.sha256(b).hexdigest()


# ======================================================================================== carga (independiente)
F_D, F_R, F_H, F_U = ("Expanded_Destinations.csv", "Final_Updated_Expanded_Reviews.csv",
                      "Final_Updated_Expanded_UserHistory.csv", "Final_Updated_Expanded_Users.csv")
BYTES = {p.name: p.read_bytes() for p in sorted(RAW.iterdir()) if p.is_file()}
D = pd.read_csv(io.BytesIO(BYTES[F_D]))
R = pd.read_csv(io.BytesIO(BYTES[F_R]))
H = pd.read_csv(io.BytesIO(BYTES[F_H]))
U = pd.read_csv(io.BytesIO(BYTES[F_U]))

out("# JJ-1a / A3 - Verificacion adversarial de A1 (curador-datos) y A2 (investigador-fuentes)")
out(f"Python {sys.version.split()[0]}, pandas {pd.__version__}, numpy {np.__version__}, "
    f"scipy {__import__('scipy').__version__}. Sin internet; sin aleatoriedad.")

# ======================================================================================== A1: archivos
sec("V1 Archivos, zip, codificacion ([A1-1] a [A1-3])")
out("Archivos en data/raw/m3/:")
for n, b in BYTES.items():
    out(f"  {n}: {len(b)} B, sha256={h256(b)}")
chk("A1-1", "numero de archivos", 5, len(BYTES))
chk("A1-1", "archive.zip tamano", 34679, len(BYTES["archive.zip"]))
s_zip = h256(BYTES["archive.zip"])
chk("A1-1", "archive.zip sha256 empieza 117e3135 y termina d004d", True,
    s_zip.startswith("117e3135") and s_zip.endswith("d004d"))
with zipfile.ZipFile(io.BytesIO(BYTES["archive.zip"])) as z:
    malo = z.testzip()
    miembros = {i.filename: (z.read(i.filename), i.date_time, i.file_size, i.compress_size) for i in z.infolist()}
out("Miembros del zip: " + "; ".join(f"{k} ({v[2]} B, comprimido {v[3]}, fecha zip {v[1]})" for k, v in miembros.items()))
chk("A1-2", "CRC del zip sin errores (testzip None)", None, malo)
chk("A1-2", "los 4 CSV sueltos identicos byte a byte a los miembros", True,
    all(BYTES.get(Path(k).name) == v[0] for k, v in miembros.items()) and len(miembros) == 4)
for n in (F_D, F_R, F_H, F_U):
    b = BYTES[n]
    try:
        t = b.decode("utf-8", errors="strict")
        utf = True
    except UnicodeDecodeError:
        t, utf = b.decode("latin-1"), False
    no_ascii = sum(ch > 127 for ch in b)
    filas = list(csv.reader(io.StringIO(t, newline="")))
    filas = [f for f in filas if f]
    nf = {len(f) for f in filas}
    df_n = {F_D: D, F_R: R, F_H: H, F_U: U}[n]
    chk("A1-3", f"{n}: utf8 estricto, sin BOM, 0 bytes >127, solo LF, filas csv==pandas, campos constantes",
        (True, False, 0, 0, True, 1),
        (utf, b.startswith(b"\xef\xbb\xbf"), no_ascii, b.count(b"\r"), len(filas) - 1 == len(df_n), len(nf)))

# ======================================================================================== A1: estructura
sec("V2 Estructura, contadores, duplicados ([A1-4] a [A1-8])")
chk("A1-4", "filas D/R/H/U", (1000, 999, 999, 999), (len(D), len(R), len(H), len(U)))
chk("A1-5", "UserID maestro = 1..999 y DestinationID maestro = 1..1000 (conjuntos)", (True, True),
    (set(U.UserID) == set(range(1, 1000)), set(D.DestinationID) == set(range(1, 1001))))
faltan = {n: int(df.isna().sum().sum()) for n, df in (("D", D), ("R", R), ("H", H), ("U", U))}
vacias = {n: int(sum((df[c].astype(str).str.strip() == "").sum() for c in df.columns if df[c].dtype == object
                     or str(df[c].dtype) in ("str", "string")))
          for n, df in (("D", D), ("R", R), ("H", H), ("U", U))}
dups = {n: int(df.duplicated().sum()) for n, df in (("D", D), ("R", R), ("H", H), ("U", U))}
chk("A1-6", "faltantes / cadenas vacias / duplicados exactos en todos", (0, 0, 0),
    (sum(faltan.values()), sum(vacias.values()), sum(dups.values())))
contador = {n: list(df.iloc[:, 0]) == list(range(1, len(df) + 1)) for n, df in (("D", D), ("R", R), ("H", H), ("U", U))}
out(f"  primera columna: D={D.columns[0]}, R={R.columns[0]}, H={H.columns[0]}, U={U.columns[0]}")
chk("A1-6", "primera columna de cada archivo = 1..n en orden", {"D": True, "R": True, "H": True, "U": True}, contador)
sin_id = {n: (len(df) - len(df.iloc[:, 1:].drop_duplicates()), len(df.iloc[:, 1:].drop_duplicates()))
          for n, df in (("D", D), ("R", R), ("H", H), ("U", U))}
chk("A1-7", "Users sin UserID: filas sobrantes / combinaciones distintas", (657, 342), sin_id["U"])
chk("A1-7", "D, R, H sin su contador: 0 sobrantes", (0, 0, 0), (sin_id["D"][0], sin_id["R"][0], sin_id["H"][0]))
fuera = (int((~R.UserID.isin(U.UserID)).sum()), int((~R.DestinationID.isin(D.DestinationID)).sum()),
         int((~H.UserID.isin(U.UserID)).sum()), int((~H.DestinationID.isin(D.DestinationID)).sum()))
chk("A1-8", "filas de R/H con usuario o destino fuera de la maestra", (0, 0, 0, 0), fuera)

# ======================================================================================== A1: calificaciones
sec("V3 Calificaciones y Popularity ([A1-9] a [A1-11])")
fr = R.Rating.value_counts().sort_index().to_dict()
fh = H.ExperienceRating.value_counts().sort_index().to_dict()
chk("A1-9", "Rating frecuencias 1..5", {1: 198, 2: 199, 3: 185, 4: 216, 5: 201}, fr)
chk("A1-9", "Rating media (3 dec.)", 3.023, round(R.Rating.mean(), 3))
chk("A1-10", "ExperienceRating frecuencias 1..5", {1: 206, 2: 228, 3: 201, 4: 183, 5: 181}, fh)
chk("A1-10", "ExperienceRating media (3 dec.)", 2.905, round(H.ExperienceRating.mean(), 3))
p = D.Popularity
chk("A1-11", "Popularity distintos / min / max / mediana (4 dec.)", (1000, 7.5045, 9.4998, 8.4965),
    (p.nunique(), round(p.min(), 4), round(p.max(), 4), round(p.median(), 4)))

# ======================================================================================== A1: interacciones
sec("V4 Interacciones, densidad, distribuciones ([A1-12] a [A1-16])")


def pares(df):
    return set(zip(df.UserID, df.DestinationID))


PR, PH = pares(R), pares(H)
chk("A1-12", "Reviews: pares distintos, repetidos, usuarios, destinos", (999, 0, 624, 651),
    (len(PR), len(R) - len(PR), R.UserID.nunique(), R.DestinationID.nunique()))
chk("A1-12", "UserHistory: pares distintos, repetidos, usuarios, destinos", (999, 0, 642, 638),
    (len(PH), len(H) - len(PH), H.UserID.nunique(), H.DestinationID.nunique()))
NU, ND = U.UserID.nunique(), D.DestinationID.nunique()
dens = lambda npar, nu, nd: npar / (nu * nd)
chk("A1-13", "densidad (a) R y H (6 dec.)", (0.001000, 0.001000),
    (round(dens(len(PR), NU, ND), 6), round(dens(len(PH), NU, ND), 6)))
chk("A1-13", "densidad (b) R y H (6 dec.)", (0.002459, 0.002439),
    (round(dens(len(PR), 624, 651), 6), round(dens(len(PH), 642, 638), 6)))
chk("A1-14", "usuarios maestros ausentes R/H; destinos ausentes R/H", (375, 357, 349, 362),
    (len(set(U.UserID) - set(R.UserID)), len(set(U.UserID) - set(H.UserID)),
     len(set(D.DestinationID) - set(R.DestinationID)), len(set(D.DestinationID) - set(H.DestinationID))))


def perfil(serie_ids):
    c = collections.Counter(serie_ids)
    v = np.array(list(c.values()))
    return (float(np.median(v)), round(float(v.mean()), 3), int(v.max()),
            tuple(int((v == i).sum()) for i in (1, 2, 3, 4)) + (int((v >= 5).sum()),))


pu_r, pu_h = perfil(R.UserID), perfil(H.UserID)
chk("A1-15", "Reviews por usuario: mediana, media, max, 1/2/3/4/>=5", (1.0, 1.601, 5, (355, 190, 58, 15, 6)), pu_r)
chk("A1-15", "UserHistory por usuario: mediana, media, max, 1/2/3/4/>=5", (1.0, 1.556, 6, (384, 180, 60, 16, 2)), pu_h)
pd_r, pd_h = perfil(R.DestinationID), perfil(H.DestinationID)
chk("A1-16", "Reviews por destino: mediana, max, 1/2/3/4/>=5", (1.0, 5, (396, 178, 62, 14, 1)),
    (pd_r[0], pd_r[2], pd_r[3]))
chk("A1-16", "UserHistory por destino: max, 1/2/3/4/>=5", (6, (383, 177, 56, 17, 5)), (pd_h[2], pd_h[3]))

# ======================================================================================== A1: solapamiento y opciones
sec("V5 Solapamiento y opciones de interaccion ([A1-17] a [A1-20])")
chk("A1-17", "pares en ambos / solo R / solo H / union", (0, 999, 999, 1998),
    (len(PR & PH), len(PR - PH), len(PH - PR), len(PR | PH)))
ur, uh, dr, dh = set(R.UserID), set(H.UserID), set(R.DestinationID), set(H.DestinationID)
chk("A1-18", "usuarios ambos/solo R/solo H; destinos ambos/solo R/solo H", (408, 216, 234, 423, 228, 215),
    (len(ur & uh), len(ur - uh), len(uh - ur), len(dr & dh), len(dr - dh), len(dh - dr)))
UN = PR | PH
cu = collections.Counter(u for u, _ in UN)
vu = np.array(list(cu.values()))
chk("A1-19", "(iii) union: pares, usuarios, destinos", (1998, 858, 866), (len(UN), len(cu), len({d for _, d in UN})))
chk("A1-19", "(iii) densidad (a) y (b) (6 dec.)", (0.002000, 0.002689),
    (round(dens(len(UN), NU, ND), 6), round(dens(len(UN), len(cu), len({d for _, d in UN})), 6)))
chk("A1-19", "(iii) mediana por usuario y usuarios que aparecen con <2, <3, <5", (2.0, 252, 532, 806),
    (float(np.median(vu)), int((vu < 2).sum()), int((vu < 3).sum()), int((vu < 5).sum())))
chk("A1-19", "(iv) interseccion vacia", 0, len(PR & PH))


def menos_que(par_set):
    c = collections.Counter(u for u, _ in par_set)
    todos = np.array([c.get(u, 0) for u in U.UserID])  # incluye ceros de la maestra
    return tuple(int((todos < k).sum()) for k in (2, 3, 5))


chk("A1-20", "con ceros: (i) <2,<3,<5", (730, 920, 993), menos_que(PR))
chk("A1-20", "con ceros: (ii) <2,<3,<5", (741, 921, 997), menos_que(PH))
chk("A1-20", "con ceros: (iii) <2,<3,<5", (393, 673, 947), menos_que(UN))
out(f"  usuarios maestros sin ninguna interaccion en la union: {NU - len(cu)} (A1 seccion 3 dice 141)")

# ======================================================================================== A1: fechas
sec("V6 Fechas ([A1-21] a [A1-25])")
fechas_cols = []
for nom, df in (("D", D), ("R", R), ("H", H), ("U", U)):
    for c in df.columns:
        if df[c].dtype.kind in "iuf":
            continue
        ok = pd.to_datetime(df[c].astype(str), format="%Y-%m-%d", errors="coerce").notna().mean()
        out(f"  {nom}.{c}: fraccion que parsea AAAA-MM-DD = {ok:.3f}")
        if ok > 0:
            fechas_cols.append(f"{nom}.{c}")
chk("A1-21", "columnas de texto que parsean como fecha", ["H.VisitDate"], fechas_cols)
vd = H.VisitDate.value_counts().sort_index().to_dict()
chk("A1-21", "VisitDate valores y frecuencias", {"2024-01-01": 333, "2024-02-15": 333, "2024-03-20": 333}, vd)


def es_funcion_mod(ids, vals, k):
    return pd.DataFrame({"r": np.asarray(ids) % k, "v": np.asarray(vals)}).groupby("r")["v"].nunique().max() == 1


def k_min(ids, vals, kmax=60):
    for k in range(1, kmax + 1):
        if es_funcion_mod(ids, vals, k):
            return k
    return None


def pureza(ids, vals, k):
    t = pd.crosstab(np.asarray(ids) % k, np.asarray(vals))
    return t.max(axis=1).sum() / t.values.sum()


chk("A1-22", "VisitDate funcion exacta de HistoryID mod 3 (k minimo)", 3, k_min(H.HistoryID, H.VisitDate))
pur = {k: pureza(H.HistoryID, H.VisitDate, k) for k in range(1, 61)}
no3 = [pur[k] for k in pur if k % 3]
kmax_no3 = max((k for k in pur if k % 3), key=lambda k: pur[k])
out(f"  pureza VisitDate, k no multiplo de 3 (k<=60): min={min(no3):.4f}, max={max(no3):.4f} (en k={kmax_no3}); "
    f"multiplos de 3: {sorted({round(float(pur[k]), 4) for k in pur if k % 3 == 0})}")
out(f"  k no multiplos de 3 con pureza que redondea a 0.333: {[k for k in pur if k % 3 and round(pur[k], 3) == 0.333]}")
out("  pureza k=1..12: " + ", ".join(f"{k}:{pur[k]:.3f}" for k in range(1, 13)))
chk("A1-22", "'el resto de k son 0.333' (k no multiplo de 3, redondeo a 3 dec.)", "todas 0.333",
    f"de {min(no3):.3f} a {max(no3):.3f}", ok=round(max(no3), 3) == 0.333)
nf_u = H.groupby("UserID").VisitDate.nunique()
chk("A1-23", "usuarios H con >1 fecha; con 2; con 3; con 1", (195, 172, 23, 447),
    (int((nf_u > 1).sum()), int((nf_u == 2).sum()), int((nf_u == 3).sum()), int((nf_u == 1).sum())))
bt = D.BestTimeToVisit.astype(str)
chk("A1-24", "BestTimeToVisit: parsea AAAA-MM-DD, valores distintos, k minimo", (0, 5, 5),
    (int(pd.to_datetime(bt, format="%Y-%m-%d", errors="coerce").notna().sum()), bt.nunique(),
     k_min(D.DestinationID, bt)))
chk("A1-25", "Reviews no tiene columna de fecha", True, not any(x.startswith("R.") for x in fechas_cols))

# ======================================================================================== A1: destinos y usuarios
sec("V7 Destinos y usuarios ([A1-26] a [A1-34])")
por_nombre = D.groupby("Name").DestinationID.count().to_dict()
chk("A1-26", "5 nombres, 200 ids cada uno", (5, {200}), (D.Name.nunique(), set(por_nombre.values())))
chk("A1-26", "combinaciones Name+State+Type+BestTimeToVisit", 5,
    len(D[["Name", "State", "Type", "BestTimeToVisit"]].drop_duplicates()))
chk("A1-27", "Name/State/Type/BestTimeToVisit k minimo respecto a DestinationID", (5, 5, 5, 5),
    tuple(k_min(D.DestinationID, D[c]) for c in ("Name", "State", "Type", "BestTimeToVisit")))
ciclo = list(D.sort_values("DestinationID").Name.head(5))
chk("A1-27", "ciclo de nombres", ["Taj Mahal", "Goa Beaches", "Jaipur City", "Kerala Backwaters", "Leh Ladakh"], ciclo)
mp = D.groupby("Name").Popularity.mean()
chk("A1-27", "Popularity media por nombre, rango (2 dec.)", (8.49, 8.55), (round(mp.min(), 2), round(mp.max(), 2)))
ipn = U.groupby("Name").UserID.count()
dom = U.Email.str.split("@").str[1].value_counts().to_dict()
chk("A1-28", "usuarios: nombres, min-max ids por nombre, (Name,Email) distintas, dominios",
    (20, 38, 64, 20, {"example.com": 999}),
    (U.Name.nunique(), int(ipn.min()), int(ipn.max()), len(U[["Name", "Email"]].drop_duplicates()), dom))
chk("A1-29", "Email == lower(Name)+'@example.com'", 999, int((U.Email == U.Name.str.lower() + "@example.com").sum()))
chk("A1-30", "nombres con mas de un Gender", 0, int((U.groupby("Name").Gender.nunique() > 1).sum()))
chk("A1-31", "Preferences k minimo respecto a UserID", 3, k_min(U.UserID, U.Preferences))
chk("A1-31", "Name, Email, Gender, Adults, Children sin k<=60",
    (None,) * 5, tuple(k_min(U.UserID, U[c].astype(str)) for c in
                       ("Name", "Email", "Gender", "NumberOfAdults", "NumberOfChildren")))
combos = U.Preferences.value_counts().to_dict()
opciones = collections.Counter(x.strip() for s in U.Preferences for x in s.split(","))
nopc = set(U.Preferences.map(lambda s: len(s.split(","))))
chk("A1-32", "Preferences: combinaciones, opciones por fila, opciones sueltas",
    ({333}, {2}, {"Historical": 666, "Beaches": 333, "Nature": 333, "Adventure": 333, "City": 333}),
    (set(combos.values()), nopc, dict(opciones)))
chk("A1-33", "Gender, Adults, Children: conteos/valores",
    ({"Male": 503, "Female": 496}, [1, 2], [0, 1, 2]),
    (U.Gender.value_counts().to_dict(), sorted(U.NumberOfAdults.unique().tolist()),
     sorted(U.NumberOfChildren.unique().tolist())))
pvals = []
cols_u = ["Preferences", "Gender", "NumberOfAdults", "NumberOfChildren"]
for i in range(4):
    for j in range(i + 1, 4):
        t = pd.crosstab(U[cols_u[i]], U[cols_u[j]])
        chi, pv, gl, _ = stats.chi2_contingency(t, correction=False)
        chi_y, pv_y, _, _ = stats.chi2_contingency(t, correction=True)
        pvals.append(pv)
        out(f"  {cols_u[i]} x {cols_u[j]}: chi2={chi:.4f}, gl={gl}, p={pv:.4f} (con Yates si 2x2: p={pv_y:.4f})")
chk("A1-34", "min p de chi2 entre variables de usuario >= 0.20", True, round(min(pvals), 4), ok=min(pvals) >= 0.20)
out("  Nota: no rechazar H0 con p>=0.20 no prueba independencia; [A1-34] la enuncia como hecho ('son independientes').")
out("  Potencia del chi2 de independencia (alfa=0.05, n=999) frente a una dependencia de tamano w de Cohen "
    "(no centralidad n*w^2):")
for gl_ in (1, 2, 4):
    crit = stats.chi2.ppf(0.95, gl_)
    pot = {w: float(stats.ncx2.sf(crit, gl_, 999 * w * w)) for w in (0.05, 0.10)}
    out(f"    gl={gl_}: potencia(w=0.05)={pot[0.05]:.3f}; potencia(w=0.10)={pot[0.10]:.3f}")

# ======================================================================================== A1: textos
sec("V8 Textos ([A1-35], [A1-36])")
chk("A1-35", "ReviewText: 3 textos x 333; k minimo respecto a ReviewID",
    ({333}, 3), (set(R.ReviewText.value_counts().values), k_min(R.ReviewID, R.ReviewText)))
RM = R.merge(D, on="DestinationID", how="left").merge(U[["UserID", "Preferences"]], on="UserID", how="left")
for nombre, col, pa in (("Rating", "Rating", 0.5465), ("destino", "Name", 0.8836), ("preferencias", "Preferences", 0.2971)):
    t = pd.crosstab(RM.ReviewText, RM[col])
    chi, pv, gl, _ = stats.chi2_contingency(t, correction=False)
    v = math.sqrt(chi / (t.values.sum() * (min(t.shape) - 1)))
    chk("A1-36", f"ReviewText x {nombre}: p (4 dec.)", pa, round(pv, 4))
    out(f"      chi2={chi:.4f}, gl={gl}, V={v:.4f}")
lb = RM[RM.ReviewText == "Loved the beaches!"].Name.value_counts().to_dict()
out(f"  'Loved the beaches!' por destino: {lb}")
chk("A1-36", "'Loved the beaches!' aparece en los 5 destinos", 5, len(lb))

# ======================================================================================== A1: senales
sec("V9 Senales de datos generados ([A1-37] a [A1-43])")
gof = {}
for nom, df in (("D", D), ("R", R), ("H", H), ("U", U)):
    for c in df.columns[1:]:
        vc = df[c].value_counts()
        if 2 <= len(vc) <= 30:
            res = stats.chisquare(vc.values)
            gof[f"{nom}.{c}"] = (round(vc.max() / vc.min(), 3), float(res.statistic), float(res.pvalue))
for k, v in gof.items():
    out(f"  {k}: razon max/min={v[0]:.3f}, chi2={v[1]:.4f}, p={v[2]:.4f}")
fil_pref = U.Preferences.map(lambda s: frozenset(x.strip() for x in s.split(",")))
out("  Opciones sueltas de Preferences (fila 'opciones separadas' de A1.13a): cada fila aporta 2 opciones y las 3 "
    "combinaciones son " + str(sorted(sorted(c) for c in set(fil_pref))) + "; con 333 filas por combinacion la razon "
    "2:1 de 'Historical' queda fijada por la composicion, asi que la p del chi2 de bondad de ajuste sobre las 1998 "
    "opciones (no independientes) no es una prueba valida.")
exactas = sorted(k for k, v in gof.items() if v[0] == 1.0)
chk("A1-37", "columnas con razon max/min = 1.000",
    sorted(["D.Name", "D.State", "D.Type", "D.BestTimeToVisit", "R.ReviewText", "H.VisitDate", "U.Preferences"]),
    exactas)
resto = {k: v for k, v in gof.items() if v[0] != 1.0}
rr = (min(v[0] for v in resto.values()), max(v[0] for v in resto.values()))
rp = (min(v[2] for v in resto.values()), max(v[2] for v in resto.values()))
chk("A1-37", "demas: razones 1.014..1.684", (1.014, 1.684), rr)
chk("A1-37", "demas: p 0.12..0.83 (redondeo a 2 dec.)", (0.12, 0.83), (round(rp[0], 2), round(rp[1], 2)))
chk("A1-38", "Rating chi2 y p; ExperienceRating chi2 y p", (2.44, 0.656, 7.36, 0.118),
    (round(gof["R.Rating"][1], 2), round(gof["R.Rating"][2], 3),
     round(gof["H.ExperienceRating"][1], 2), round(gof["H.ExperienceRating"][2], 3)))
chk("A1-38", "Rating y ExperienceRating sin k<=60 respecto a su id", (None, None),
    (k_min(R.ReviewID, R.Rating), k_min(H.HistoryID, H.ExperienceRating)))
idx, ceros = [], []
for df in (R, H):
    for col, maestra in (("UserID", U.UserID), ("DestinationID", D.DestinationID)):
        c = df[col].value_counts().reindex(maestra, fill_value=0).values
        idx.append(c.var() / c.mean())  # var poblacional (ddof=0)
        ceros.append(int((c == 0).sum()))
esp0 = [999 * (1 - 1 / 999) ** 999, 1000 * (1 - 1 / 1000) ** 999]
out(f"  indices de dispersion R-u, R-d, H-u, H-d: {[round(x, 4) for x in idx]}; ceros: {ceros}; "
    f"ceros esperados (usuario, destino): {[round(x, 1) for x in esp0]}")
chk("A1-39", "rango indice de dispersion (3 dec.)", (0.918, 1.029), (round(min(idx), 3), round(max(idx), 3)))
chk("A1-39", "rango ceros observados; esperados (entero)", ((349, 375), (367, 368)),
    ((min(ceros), max(ceros)), (int(esp0[0]), int(esp0[1]))))

# afinidad preferencias-tipo, implementacion propia (vectorizada distinta) + prueba binomial exacta de control
tipo = dict(zip(D.DestinationID, D.Type))
prefs = {u: {("Beach" if x.strip() == "Beaches" else x.strip()) for x in s.split(",")} for u, s in zip(U.UserID, U.Preferences)}
cuota = D.Type.value_counts(normalize=True).to_dict()
afirm = {"(i)": (0.4294, 0.4000, 1.90, 0.058), "(ii)": (0.4174, 0.4000, 1.12, 0.26), "(iii)": (0.4234, 0.4000, 2.14, 0.033)}
for et, ps in (("(i)", PR), ("(ii)", PH), ("(iii)", UN)):
    hit = np.array([tipo[d] in prefs[u] for u, d in ps], dtype=float)
    pe = np.array([sum(cuota[t] for t in prefs[u]) for u, d in ps])
    z = (hit.sum() - pe.sum()) / math.sqrt((pe * (1 - pe)).sum())
    pz = 2 * stats.norm.sf(abs(z))
    pb = stats.binomtest(int(hit.sum()), len(hit), 0.4).pvalue if np.allclose(pe, 0.4) else float("nan")
    a = afirm[et]
    chk("A1-40", f"{et} observada, esperada, z, p", a,
        (round(hit.mean(), 4), round(pe.mean(), 4), round(z, 2), round(pz, 3) if et != "(ii)" else round(pz, 2)))
    out(f"      control: p binomial exacta (H0 p=0.4) = {pb:.4f}")
    t = pd.crosstab([", ".join(sorted(prefs[u])) for u, d in ps], [tipo[d] for u, d in ps])
    chi, pv, gl, _ = stats.chi2_contingency(t, correction=False)
    v = math.sqrt(chi / (t.values.sum() * (min(t.shape) - 1)))
    esperado41 = {"(i)": (0.171, 0.076), "(ii)": (0.026, 0.093), "(iii)": (0.019, 0.068)}[et]
    chk("A1-41", f"{et} chi2 Preferences x Type: p, V", esperado41, (round(pv, 3), round(v, 3)))

# asociacion calificacion - factores
for nombre_df, df, col in (("Reviews", R, "Rating"), ("UserHistory", H, "ExperienceRating")):
    M = df.merge(D, on="DestinationID", how="left", suffixes=("", "_d")).merge(
        U, on="UserID", how="left", suffixes=("", "_u"))
    M["coincide"] = [tipo[d] in prefs[u] for u, d in zip(M.UserID, M.DestinationID)]
    facs = ["Name", "Name_u", "Preferences", "Gender", "NumberOfAdults", "NumberOfChildren", "coincide"]
    facs += ["ReviewText"] if nombre_df == "Reviews" else ["VisitDate"]
    pc, pk = {}, {}
    for f in facs:
        t = pd.crosstab(M[f].astype(str), M[col])
        chi, pv, gl, _ = stats.chi2_contingency(t, correction=False)
        v = math.sqrt(chi / (t.values.sum() * (min(t.shape) - 1)))
        kw = stats.kruskal(*[g[col].values for _, g in M.groupby(M[f].astype(str))])
        pc[f], pk[f] = pv, kw.pvalue
        out(f"  {nombre_df} {col} x {f}: chi2 p={pv:.4f} (V={v:.4f}); Kruskal-Wallis p={kw.pvalue:.4f}")
    if nombre_df == "Reviews":
        chk("A1-42", "Reviews: min p chi2 >= 0.21", True, round(min(pc.values()), 4), ok=min(pc.values()) >= 0.21)
        chk("A1-42", "Reviews: min p Kruskal-Wallis >= 0.26 (literal)", True, round(min(pk.values()), 4),
            ok=min(pk.values()) >= 0.26)
    else:
        t = pd.crosstab(M.Preferences, M[col])
        chi, pv, gl, _ = stats.chi2_contingency(t, correction=False)
        v = math.sqrt(chi / (t.values.sum() * (min(t.shape) - 1)))
        chk("A1-42", "UserHistory Preferences x ExperienceRating: p chi2, V, p KW", (0.0074, 0.102, 0.18),
            (round(pv, 4), round(v, 3), round(pk["Preferences"], 2)))
        otros = [x for f, x in pc.items() if f != "Preferences"] + [x for f, x in pk.items() if f != "Preferences"]
        chk("A1-42", "UserHistory: resto de p >= 0.05", True, round(min(otros), 4), ok=min(otros) >= 0.05)
    rho1 = stats.spearmanr(M.Popularity, M[col])
    cdest = df.DestinationID.value_counts().reindex(D.DestinationID, fill_value=0).values
    rho2 = stats.spearmanr(D.Popularity.values, cdest)
    esperado43 = {"Reviews": (0.044, -0.041), "UserHistory": (0.028, 0.022)}[nombre_df]
    chk("A1-43", f"{nombre_df}: rho(Popularity, calif.), rho(Popularity, n del destino)", esperado43,
        (round(rho1.statistic, 3), round(rho2.statistic, 3)))
    chk("A1-43", f"{nombre_df}: ambas p > 0.16", True, (round(rho1.pvalue, 4), round(rho2.pvalue, 4)),
        ok=min(rho1.pvalue, rho2.pvalue) > 0.16)

# ======================================================================================== A1: observaciones extra
sec("V10 Observaciones adicionales de A3 (no afirmadas por A1)")
crea = pd.Timestamp("2024-01-23")
vdt = pd.to_datetime(H.VisitDate)
out(f"VisitDate posterior a la creacion de la version 1 en Kaggle (2024-01-23, versions[0].creationDate): "
    f"{int((vdt > crea).sum())} de {len(H)} filas; valores: {sorted(H.VisitDate[vdt > crea].unique())}")
out(f"Particion 'por tiempo' de UserHistory = particion por HistoryID mod 3 (VisitDate es funcion exacta de ese resto): "
    f"{es_funcion_mod(H.HistoryID, H.VisitDate, 3)}")
cortes = H.VisitDate.nunique() - 1
out(f"Fechas distintas={H.VisitDate.nunique()} -> a lo sumo {cortes} puntos de corte (3 bloques), no '3 cortes'.")
out(f"Tipo del destino por nombre: {D.drop_duplicates('Name').set_index('Name').Type.to_dict()}")

# ======================================================================================== A2
sec("W1 Integridad del JSON de A2 y comparacion con la re-descarga de A3")
J = json.loads(META.read_text(encoding="utf-8"))
RESP = J["respuestas"]
chk("A2-intro", "numero de respuestas", 5, len(RESP))
for i, r in enumerate(RESP):
    crudo = r["cuerpo_crudo"].encode("utf-8")
    chk("A2-intro", f"#{i} sha256(cuerpo_crudo utf-8) == sha256_cuerpo; json(cuerpo_crudo) == cuerpo; status 200",
        (True, True, 200), (h256(crudo) == r["sha256_cuerpo"], json.loads(r["cuerpo_crudo"]) == r["cuerpo"], r["status"]))
indice = [ln.split("|") for ln in (REDESC / "indice.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
mapa = {0: 0, 1: 1, 2: 3, 3: 4}  # re-descarga A3 -> indice de A2
for j, url, st, t in indice:
    b = (REDESC / f"r{j}.body").read_bytes()
    a2 = RESP[mapa[int(j)]]
    chk("A2-intro", f"re-descarga A3 r{j} ({t}, status {st}) identica byte a byte a A2 #{mapa[int(j)]}",
        (a2["url"], a2["sha256_cuerpo"]), (url, h256(b)))
chk("A2-intro", "#2 (barra final) identico a #0", RESP[0]["sha256_cuerpo"], RESP[2]["sha256_cuerpo"])
out("Fechas de consulta guardadas por A2: " + ", ".join(r["consultado_utc"] for r in RESP))

I0 = RESP[0]["cuerpo"]["info"]
F1 = RESP[1]["cuerpo"]["datasetFiles"]
V3 = RESP[3]["cuerpo"]
L4 = RESP[4]["cuerpo"]
chk("A2-intro", "#4 devuelve un solo conjunto", 1, len(L4))
L4 = L4[0]
DESC = I0["description"]

sec("W2 Campos y fragmentos literales ([A2-1] a [A2-20] y tablas)")
chk("A2-1", "titulo #0/#3/#4", ("Travel Recommendation Dataset",) * 3, (I0["title"], V3["title"], L4["title"]))
chk("A2-2", "primera linea de info.description", "### Title: India Travel Recommender System Dataset",
    DESC.splitlines()[0])
chk("A2-3", "creatorName/ownerName #3 y #4, versions[0].creatorName", ("Aman Mehra",) * 5,
    (V3["creatorName"], V3["ownerName"], L4["creatorName"], L4["ownerName"], V3["versions"][0]["creatorName"]))
chk("A2-3", "ownerRef #3/#4 y info.ownerUser #0", ("amanmehra23",) * 3, (V3["ownerRef"], L4["ownerRef"], I0["ownerUser"]))
chk("A2-4", "ref #3/#4; id #3/#4; datasetId #0",
    ("amanmehra23/travel-recommendation-dataset",) * 2 + (4345382,) * 3,
    (V3["ref"], L4["ref"], V3["id"], L4["id"], I0["datasetId"]))
chk("A2-5", "#3 versions: n, versionNumber, versionNotes, creationDate; currentVersionNumber #3/#4",
    (1, 1, "Initial release", "2024-01-23T17:07:26.487Z", 1, 1),
    (len(V3["versions"]), V3["versions"][0]["versionNumber"], V3["versions"][0]["versionNotes"],
     V3["versions"][0]["creationDate"], V3["currentVersionNumber"], L4["currentVersionNumber"]))
out(f"  nota: #4 trae versions={L4['versions']} (vacio); la unica lista de versiones es la de #3.")
chk("A2-6", "lastUpdated #3/#4", ("2024-01-23T17:07:26.487Z",) * 2, (V3["lastUpdated"], L4["lastUpdated"]))
arch = {f["name"]: (f["totalBytes"], f["creationDate"]) for f in F1}
chk("A2-7", "datasetFiles: nombres, tamanos y fechas", {
    "Expanded_Destinations.csv": (60768, "2024-01-23T17:07:28.041Z"),
    "Final_Updated_Expanded_Reviews.csv": (33710, "2024-01-23T17:07:28.068Z"),
    "Final_Updated_Expanded_UserHistory.csv": (24683, "2024-01-23T17:07:27.95Z"),
    "Final_Updated_Expanded_Users.csv": (58535, "2024-01-23T17:07:28.103Z")}, arch)
chk("A2-8", "suma de datasetFiles == totalBytes #3", (177696, 177696), (sum(v[0] for v in arch.values()), V3["totalBytes"]))
chk("A2-9", "columns [], description '', hasDescription False en los 4 archivos", True,
    all(f["columns"] == [] and f["description"] == "" and f["hasDescription"] is False for f in F1))
chk("A2-9", "#3 files [] y #0 info.data []", ([], []), (V3["files"], I0["data"]))
frag = {
    "A2-10": "This dataset was generated for educational and research purposes and is intended to be used in hackathons, "
             "academic projects, and by AI enthusiasts aiming to enhance the travel experience through technology.",
    "A2-11": "This dataset has been enriched with gender diversity and includes details on the number of adults and "
             "children for travel.",
    "A2-12": "User-generated reviews and ratings for the different destinations",
    "A2-15": "CC0: Public Domain - The dataset is in the public domain and can be used without restrictions.",
    "A2-16": "This dataset is free to use for non-commercial purposes. For commercial use, please contact the dataset provider.",
    "A2-sec6-Destinations": "Information about various travel destinations in India, including details like type of "
                            "destination (beach, mountain, historical site, etc.), popularity, and best time to visit.",
    "A2-sec6-Users-1": "Profiles of users including their preferences and demographic information.",
    "A2-sec6-Reviews": "User-generated reviews and ratings for the different destinations, offering insights into visitor "
                       "experiences and satisfaction.",
    "A2-sec6-UserHistory": "Records of users' past travel experiences, including destinations visited and ratings provided.",
    "A2-sec5-Usage": "This dataset is free to use for non-commercial purposes. For commercial use, please contact the "
                     "dataset provider. Remember to cite the source when using this dataset in your projects.",
}
for cid, f in frag.items():
    en_campo = f in DESC
    esc = json.dumps(f, ensure_ascii=False)[1:-1]
    # Kaggle escapa el apostrofo como ' en el crudo; se acepta esa forma (mismo texto al parsear el JSON)
    en_crudo = esc in RESP[0]["cuerpo_crudo"] or esc.replace("'", "\\u0027") in RESP[0]["cuerpo_crudo"]
    en_v3 = f in V3["description"]
    chk(cid, f"literal en info.description (#0), en cuerpo_crudo #0 (escapado JSON) y en description #3: '{f[:50]}...'",
        (True, True, True), (en_campo, en_crudo, en_v3))
chk("A2-sec3", "description #3 identica a info.description #0", True, V3["description"] == DESC)
# bloque de la descripcion copiado por A2 en su respuesta (seccion 3)
md = A2_RESP.read_text(encoding="utf-8")
bloque = md.split("## 3. Descripción completa", 1)[1].split("```", 2)[1].strip("\n")
chk("A2-sec3", "bloque '## 3' de la respuesta de A2 == info.description (exacto, con espacios finales)", True, bloque == DESC)
if bloque != DESC:
    out(f"  diferencia: len A2={len(bloque)} vs fuente={len(DESC)}; igual sin espacios finales de linea: "
        f"{[l.rstrip() for l in bloque.splitlines()] == [l.rstrip() for l in DESC.splitlines()]}")


def todos_valores(o, ruta=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from todos_valores(v, f"{ruta}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from todos_valores(v, f"{ruta}[{i}]")
    else:
        yield ruta, o


def todas_claves(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from todas_claves(v)
    elif isinstance(o, list):
        for v in o:
            yield from todas_claves(v)


chk("A2-14", "licencia #0 licenses[0].name; #3/#4 licenseName y licenseNameNullable; numero de licencias en #0",
    ("MIT",) * 5 + (1,), (I0["licenses"][0]["name"], V3["licenseName"], L4["licenseName"], V3["licenseNameNullable"],
                          L4["licenseNameNullable"], len(I0["licenses"])))
chk("A2-17", "keywords #0; tags #3/#4 (nombre, fullPath)",
    (["travel"], [("travel", "subject > people and society > business > travel")] * 2),
    (I0["keywords"], [[(t["name"], t["fullPath"]) for t in V3["tags"]][0], [(t["name"], t["fullPath"]) for t in L4["tags"]][0]]))
chk("A2-18", "usability #0, #3, #4", (0.5882352941176471, 0.5882353, 0.5882353),
    (I0["usabilityRating"], V3["usabilityRating"], L4["usabilityRating"]))
chk("A2-18", "descargas/vistas/votos #0; #3; #4; kernelCount #3/#4",
    ((4014, 18351, 15),) * 3 + ((1, 1),),
    ((I0["totalDownloads"], I0["totalViews"], I0["totalVotes"]), (V3["downloadCount"], V3["viewCount"], V3["voteCount"]),
     (L4["downloadCount"], L4["viewCount"], L4["voteCount"]), (V3["kernelCount"], L4["kernelCount"])))
chk("A2-20", "expectedUpdateFrequency; userSpecifiedSources; hasUserSpecifiedSources",
    ("not specified", "", False), (I0["expectedUpdateFrequency"], I0["userSpecifiedSources"], I0["hasUserSpecifiedSources"]))
chk("A2-tabla", "subtitle #0; collaborators #0; url #3; creatorUrl #3; url #4",
    ("", [], "", "", "https://www.kaggle.com/datasets/amanmehra23/travel-recommendation-dataset"),
    (I0["subtitle"], I0["collaborators"], V3["url"], V3["creatorUrl"], L4["url"]))
out(f"  nota: creatorUrl de #4 = {L4['creatorUrl']!r} (no es una URL).")

sec("W3 Ausencias (busqueda programatica, sin distinguir mayusculas)")
crudos = [r["cuerpo_crudo"] for r in RESP]
for palabra in ("synthetic", "simulated", "augmented", "sample", "scraped", "collected", "survey", "artificial",
                "fake", "mock", "generated", "enriched", "expanded", "real"):
    n_sub = sum(len(re.findall(re.escape(palabra), c, re.I)) for c in crudos)
    n_pal = sum(len(re.findall(rf"\b{palabra}\b", c, re.I)) for c in crudos)
    n_desc = len(re.findall(rf"\b{palabra}\b", DESC, re.I))
    out(f"  '{palabra}': subcadena en los 5 crudos={n_sub}; palabra completa en los 5 crudos={n_pal}; "
        f"palabra completa en info.description={n_desc}")
chk("A2-13", "'synthetic' en los 5 cuerpo_crudo (subcadena, sin mayusculas)", 0,
    sum(len(re.findall("synthetic", c, re.I)) for c in crudos))
chk("A2-sec4", "ninguna de synthetic/simulated/augmented/sample/scraped/collected/survey en info.description", 0,
    sum(len(re.findall(p, DESC, re.I)) for p in ("synthetic", "simulated", "augmented", "sample", "scraped",
                                                 "collected", "survey")))
chk("A2-sec4", "'real' como palabra completa en los 5 crudos (subcadena solo en 'realm')", 0,
    sum(len(re.findall(r"\breal\b", c, re.I)) for c in crudos))
chk("A2-sec4", "'expanded' en info.description (A2: solo en nombres de archivo)", 0,
    len(re.findall("expanded", DESC, re.I)))
doi_sub = sum(len(re.findall("doi", c, re.I)) for c in crudos)
doi_pat = sum(len(re.findall(r"10\.\d{4,9}/", c)) for c in crudos)
claves = set()
for r in RESP:
    claves |= set(todas_claves(r["cuerpo"]))
chk("A2-19", "'doi' (subcadena) y patron 10.NNNN/ en los 5 crudos; claves con 'doi'", (0, 0, []),
    (doi_sub, doi_pat, sorted(k for k in claves if "doi" in k.lower())))
chk("A2-tabla", "claves con 'publish'/'publication' (A2: no existe campo de publicacion)", [],
    sorted(k for k in claves if "publi" in k.lower()))
out("  claves con 'date' o 'updated': " + ", ".join(sorted(k for k in claves if re.search("date|updated", k, re.I))))
chk("A2-sec6", "la descripcion dice que cada componente es un CSV aparte (sin mapear nombres)", True,
    "Each of these components is presented in a separate CSV file" in DESC)

sec("W4 Fuente frente a archivos locales (tamanos y fechas)")
for n, (tb, fc) in arch.items():
    mz = miembros[n]
    chk("A2-7/local", f"{n}: totalBytes Kaggle == tamano local == tamano en el zip; fecha zip vs creationDate",
        (tb, tb), (len(BYTES[n]), mz[2]))
    out(f"      fecha del miembro en el zip (hora local sin zona): {mz[1]}; creationDate Kaggle: {fc}")
chk("A2-obs3", "totalBytes de #4 (34679) == tamano de archive.zip descargado", L4["totalBytes"], len(BYTES["archive.zip"]))
out(f"  suma de tamanos comprimidos de los miembros = {sum(v[3] for v in miembros.values())} "
    f"(+ cabeceras y directorio central = {len(BYTES['archive.zip'])})")

# ======================================================================================== R: reproducibilidad de A1
sec("R Reproducibilidad del script de A1 (ejecucion del original sin escribir a disco)")
guardada = A1_SALIDA.read_bytes()
out(f"SHA-256 de la salida guardada por A1: {h256(guardada)} ({len(guardada)} B, "
    f"{guardada.count(b'\n')} lineas, secciones '## A1.': {len(re.findall(rb'^## A1\.', guardada, re.M))})")
out(f"SHA-256 del script de A1: {h256(A1_SCRIPT.read_bytes())}")
original_wt = pathlib.Path.write_text
capt = []


def _intercepta(self, data, encoding=None, errors=None, newline=None):
    capt.append((str(self), data))
    return len(data)


hashes = []
for corrida in (1, 2):
    capt.clear()
    pathlib.Path.write_text = _intercepta
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(A1_SCRIPT), run_name="__main__")
    finally:
        pathlib.Path.write_text = original_wt
    destino, texto = capt[-1]
    hashes.append(h256(texto.encode("utf-8")))
    out(f"corrida {corrida}: el script intento escribir en {Path(destino).relative_to(RAIZ)}; "
        f"sha256 de lo que habria escrito = {hashes[-1]}")
chk("R", "salida regenerada (2 corridas) == salida guardada", (h256(guardada),) * 2, tuple(hashes))
chk("R", "la salida guardada no fue modificada por esta verificacion", h256(guardada), h256(A1_SALIDA.read_bytes()))

sec("Resumen de comprobaciones automaticas")
out(f"OK={CUENTA['OK']}; DIFIERE={CUENTA['DIFIERE']} (los DIFIERE se analizan uno a uno en el informe)")
SALIDA.write_bytes(("\n".join(LINEAS) + "\n").encode("utf-8"))
print(f"\n[escrito] {SALIDA.relative_to(RAIZ)}")
