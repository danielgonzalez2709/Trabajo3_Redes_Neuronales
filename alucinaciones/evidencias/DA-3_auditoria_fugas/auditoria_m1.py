"""Auditoría de fugas M1 (R2, DA-3/DA-4). Solo lectura del repo. Uso:
    cd <repo> && .venv/Scripts/python <ruta>/auditoria_m1.py
"""
import sys
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path.cwd()
sys.path.insert(0, str(REPO))
from src.m1_demanda import datos as D  # noqa: E402

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

cfg = yaml.safe_load(open(REPO / "configs/m1/datos.yaml", encoding="utf-8"))
diaria = pd.read_parquet(REPO / "data/processed/m1/demanda_diaria.parquet")
detalle = pd.read_parquet(REPO / "data/processed/m1/demanda_detalle.parquet")
marcas = pd.read_parquet(REPO / "data/processed/m1/marcas_anomalos.parquet")
INI_TEST = dt.date(2023, 7, 1)  # test = segundo semestre de 2023 (supuesto del prompt)
FIN = dt.date(2023, 12, 31)
H = 30


def titulo(t):
    print("\n" + "=" * 100 + f"\n{t}\n" + "=" * 100)


# ----------------------------------------------------------------------------------------------- 0. reproducibilidad
titulo("0. Las marcas publicadas se reproducen con datos.marcar_anomalos sobre la serie publicada")
base = diaria.drop(columns="anomalo").assign(anomalo=False)
m_rep, det_rep = D.marcar_anomalos(base, cfg["anomalos"])
igual = (m_rep[D.REGLAS].to_numpy() == marcas[D.REGLAS].to_numpy()).all()
print("marcas reproducidas == marcas_anomalos.parquet:", bool(igual))
print("anomalo == OR(reglas):", bool((marcas[D.REGLAS].any(axis=1).to_numpy() == diaria["anomalo"].to_numpy()).all()))

# ----------------------------------------------------------------------------------------------- 1. anómalos miran el futuro
titulo("1a. Dependencia de las marcas de datos de test: recalcular SOLO con fechas < 2023-07-01 y comparar en train")
train = diaria[diaria["fecha"] < INI_TEST].reset_index(drop=True)
m_tr, det_tr = D.marcar_anomalos(train.assign(anomalo=False), cfg["anomalos"])
m_full_tr = marcas[marcas["fecha"] < INI_TEST].reset_index(drop=True)
for r in D.REGLAS:
    dif = (m_tr[r] != m_full_tr[r])
    print(f"  {r:<30} marcas train (serie completa)={int(m_full_tr[r].sum()):>3}  (solo train)={int(m_tr[r].sum()):>3}  "
          f"días que cambian={int(dif.sum())}")
print("  sigma_MAD por ruta y regla: serie completa vs solo train")
for ruta in sorted(det_rep):
    for regla in D.REGLAS_ROBUSTAS:
        a, b = det_rep[ruta].get(regla, {}), det_tr[ruta].get(regla, {})
        print(f"    {ruta} {regla:<30} {a.get('sigma_mad')!s:>10} {b.get('sigma_mad')!s:>10}")

titulo("1b. Fuga por la ventana centrada: marca en t calculada con datos hasta t (causal) vs centrada; frontera de origen")
# Para cada origen rodante t0 (cada 7 días en test), la marca de los días t0-14..t0 usa datos de t0+1..t0+14.
ventana = int(cfg["anomalos"]["caida_robusta"]["ventana_dias"])
h = (ventana - 1) // 2
origenes = [INI_TEST + dt.timedelta(days=7 * k) for k in range(100)
            if INI_TEST + dt.timedelta(days=7 * k + H) <= FIN]
print(f"  orígenes de test (cada 7 días, horizonte {H}): {len(origenes)}; primero {origenes[0]}, último {origenes[-1]}")
cambios_por_origen = []
for t0 in origenes:
    hasta = diaria[diaria["fecha"] <= t0].reset_index(drop=True)
    mt, _ = D.marcar_anomalos(hasta.assign(anomalo=False), cfg["anomalos"])
    ref = marcas[marcas["fecha"] <= t0].reset_index(drop=True)
    a1 = mt[D.REGLAS].any(axis=1)
    a2 = ref[D.REGLAS].any(axis=1)
    cambios_por_origen.append(int((a1 != a2).sum()))
print(f"  días ≤ origen cuya marca `anomalo` cambia al recalcular con datos ≤ origen: {cambios_por_origen}")

titulo("1c. ¿Dónde caen los anómalos? (train < 2023-07-01 ≤ test)")
a = diaria[diaria["anomalo"]].copy()
a["particion"] = np.where(a["fecha"] < INI_TEST, "train+val", "test")
print(a.groupby(["ruta_id", "particion"]).size().unstack(fill_value=0))
print(marcas[diaria["anomalo"].to_numpy() & (diaria["fecha"] >= INI_TEST).to_numpy()]
      .merge(diaria[["ruta_id", "fecha", "pasajeros", "despachos"]], on=["ruta_id", "fecha"]).to_string())

titulo("1d. Efecto de excluir días `anomalo` del TEST sobre el error de un ingenuo estacional (h = 1..30)")
# Pronóstico ingenuo estacional desde cada origen: y_hat(t0+h) = y(t0 + h - 7*ceil(h/7)) (último valor ≤ t0 con el mismo día de semana)
rows = []
s = diaria.set_index(["ruta_id", "fecha"])
for ruta, g in diaria.groupby("ruta_id"):
    y = g.set_index("fecha")["pasajeros"]
    sr = g.set_index("fecha")["sin_registro"]
    an = g.set_index("fecha")["anomalo"]
    for t0 in origenes:
        for hh in range(1, H + 1):
            f = t0 + dt.timedelta(days=hh)
            k = -(-hh // 7)
            fb = f - dt.timedelta(days=7 * k)
            rows.append((ruta, t0, hh, f, y[f], y[fb], sr[f], an[f]))
P = pd.DataFrame(rows, columns=["ruta_id", "origen", "h", "fecha", "y", "yhat", "sin_reg", "anom"])
P["ae"] = (P["y"] - P["yhat"]).abs()
res = P.groupby("ruta_id").apply(lambda g: pd.Series({
    "MAE_todo": g["ae"].mean(),
    "MAE_sin_sinreg": g.loc[~g["sin_reg"], "ae"].mean(),
    "MAE_sin_sinreg_ni_anom": g.loc[~g["sin_reg"] & ~g["anom"], "ae"].mean(),
    "n_pred": len(g), "n_sinreg": int(g["sin_reg"].sum()), "n_anom": int(g["anom"].sum())}), include_groups=False)
print(res.round(1).to_string())

# ----------------------------------------------------------------------------------------------- 2. sin_registro = 0
titulo("2a. Días sin_registro: fechas y partición")
sr = diaria[diaria["sin_registro"]]
for ruta, g in sr.groupby("ruta_id"):
    fechas = sorted(g["fecha"])
    print(f"  {ruta}: {len(fechas)} días; test={sum(f >= INI_TEST for f in fechas)}; "
          f"{fechas[0]}..{fechas[-1]}; meses={sorted({f.strftime('%Y-%m') for f in fechas})}")

titulo("2b. Escala de MASE (ingenuo estacional 7 días, solo train < 2023-07-01): ceros imputados vs pares sin imputación")
for ruta, g in diaria[diaria["fecha"] < INI_TEST].groupby("ruta_id"):
    g = g.sort_values("fecha").reset_index(drop=True)
    y = g["pasajeros"].to_numpy(float)
    s_ = g["sin_registro"].to_numpy()
    d = np.abs(y[7:] - y[:-7])
    ok = ~(s_[7:] | s_[:-7])
    an = g["anomalo"].to_numpy()
    ok2 = ok & ~(an[7:] | an[:-7])
    q_all, q_ok, q_ok2 = d.mean(), d[ok].mean(), d[ok2].mean()
    print(f"  {ruta}: escala con 0 imputados={q_all:8.1f}  sin pares con sin_registro={q_ok:8.1f}  "
          f"(+ sin anómalos)={q_ok2:8.1f}  razón={q_all / q_ok:.3f}  pares afectados={int((~ok).sum())}")

titulo("2c. Rezagos contaminados: pronósticos desde orígenes de test cuyo rezago estacional cae en un día sin_registro")
lag_sr = []
for ruta, g in diaria.groupby("ruta_id"):
    sr_ = g.set_index("fecha")["sin_registro"]
    for t0 in origenes:
        for hh in range(1, H + 1):
            f = t0 + dt.timedelta(days=hh)
            fb = f - dt.timedelta(days=7 * -(-hh // 7))
            lag_sr.append((ruta, bool(sr_[fb])))
L = pd.DataFrame(lag_sr, columns=["ruta_id", "lag_sinreg"]).groupby("ruta_id")["lag_sinreg"].sum()
print(L.to_string())
# Rezagos 1..28 en todo el periodo: fracción de ventanas de 28 días previas a un origen (cada 7 días, todo el periodo)
# que contienen al menos un 0 imputado.
for ruta, g in diaria.groupby("ruta_id"):
    g = g.sort_values("fecha").reset_index(drop=True)
    s_ = g["sin_registro"].to_numpy()
    idx = range(28, len(g) - H, 7)
    n = sum(s_[i - 28 + 1:i + 1].any() for i in idx)
    print(f"  {ruta}: orígenes (cada 7 días, todo el periodo) con ≥1 cero imputado en los 28 rezagos: {n}/{len(idx)}")

titulo("2d. ¿Los 0 imputados son plausibles como demanda? Pasajeros mínimos en días con registro (para contraste)")
for ruta, g in diaria.groupby("ruta_id"):
    c = g[~g["sin_registro"]]["pasajeros"]
    print(f"  {ruta}: min con registro={c.min()}, p1={c.quantile(.01):.0f}, mediana={c.median():.0f}")

# ----------------------------------------------------------------------------------------------- 3. columnas no conocibles
titulo("3a. Columnas de demanda_diaria / detalle: ¿conocibles 30 días antes del día pronosticado?")
print("  demanda_diaria:", diaria.columns.tolist())
print("  demanda_detalle:", detalle.columns.tolist())
print("  Correlación (Spearman) pasajeros vs despachos del MISMO día, por ruta (solo días con registro):")
for ruta, g in diaria[~diaria["sin_registro"]].groupby("ruta_id"):
    rho_same = g["pasajeros"].corr(g["despachos"], method="spearman")
    g = g.sort_values("fecha")
    rho_lag30 = g["pasajeros"].corr(g["despachos"].shift(30), method="spearman")
    print(f"    {ruta}: rho(P_t, D_t)={rho_same:.3f}   rho(P_t, D_t-30)={rho_lag30:.3f}")
print("  Ganancia de usar D_t (no conocible) en una regresión log-log vs solo rezago estacional (train):")
for ruta, g in diaria.groupby("ruta_id"):
    g = g.sort_values("fecha").reset_index(drop=True)
    g["lag35"] = g["pasajeros"].shift(35)  # rezago conocible en el peor horizonte (h=30 → ≥ 30; múltiplo de 7)
    g = g[(~g["sin_registro"]) & g["lag35"].notna() & (g["pasajeros"] > 0) & (g["despachos"] > 0) & (g["lag35"] > 0)]
    tr, te = g[g["fecha"] < INI_TEST], g[g["fecha"] >= INI_TEST]
    def mae(cols):
        X = np.column_stack([np.ones(len(tr))] + [np.log(tr[c]) for c in cols])
        b = np.linalg.lstsq(X, np.log(tr["pasajeros"]), rcond=None)[0]
        Xt = np.column_stack([np.ones(len(te))] + [np.log(te[c]) for c in cols])
        return np.mean(np.abs(np.exp(Xt @ b) - te["pasajeros"]))
    print(f"    {ruta}: MAE test con lag35={mae(['lag35']):8.1f}   con lag35 + despachos_t={mae(['lag35', 'despachos']):8.1f}")

titulo("3b. Parámetros elegidos mirando la serie completa (incluye test)")
print("  configs/m1/datos.yaml: 'Umbrales elegidos mirando los residuos reales (2021–2023, DA-3)'")
r = yaml.safe_load(open(REPO / "data/processed/m1/rutas.yaml", encoding="utf-8"))
print("  criterio de rutas:", r["rutas"][0]["criterios_seleccion"][:160], "...")

# ----------------------------------------------------------------------------------------------- 4. tránsito 11001-15759
titulo("4a. % de pasajeros en TRANSITO por mes, rutas 11001-15759 y 15759-11001 (y comparación con el resto)")
det = detalle.assign(mes=pd.to_datetime(detalle["fecha"]).dt.to_period("M"))
t = det.groupby(["ruta_id", "mes", "tipo_despacho"])["pasajeros"].sum().unstack(fill_value=0)
t["pct_tr"] = 100 * t["TRANSITO"] / (t["ORIGEN"] + t["TRANSITO"])
t["total"] = t["ORIGEN"] + t["TRANSITO"]
for ruta in ["11001-15759", "15759-11001"]:
    x = t.loc[ruta]
    print(f"\n  {ruta}")
    print(x[["ORIGEN", "TRANSITO", "total", "pct_tr"]].round(1).to_string())
print("\n  % tránsito por semestre (todas las rutas):")
det["sem"] = pd.to_datetime(det["fecha"]).dt.year.astype(str) + "S" + ((pd.to_datetime(det["fecha"]).dt.month > 6) + 1).astype(str)
u = det.groupby(["ruta_id", "sem", "tipo_despacho"])["pasajeros"].sum().unstack(fill_value=0)
print((100 * u["TRANSITO"] / u.sum(axis=1)).unstack().round(1).to_string())

titulo("4b. Cambio de nivel de la serie total vs solo ORIGEN en 11001-15759 alrededor de nov-2022 (mediana diaria)")
for ruta in ["11001-15759", "15759-11001"]:
    g = det[det["ruta_id"] == ruta]
    day = g.groupby(["fecha", "tipo_despacho"])["pasajeros"].sum().unstack(fill_value=0)
    day["total"] = day.sum(axis=1)
    day.index = pd.to_datetime(day.index)
    for a_, b_ in [("2022-05-01", "2022-10-31"), ("2022-11-01", "2023-06-30"), ("2023-07-01", "2023-12-31")]:
        z = day.loc[a_:b_]
        print(f"  {ruta} {a_}..{b_}: mediana total={z['total'].median():7.0f}  ORIGEN={z.get('ORIGEN', pd.Series([0])).median():7.0f}  "
              f"TRANSITO={z.get('TRANSITO', pd.Series([0])).median():7.0f}")

titulo("4c. Fracción del train (< 2023-07-01) que ya está después del cambio (≥ 2022-11-01)")
n_tr = (dt.date(2023, 7, 1) - dt.date(2021, 1, 1)).days
n_post = (dt.date(2023, 7, 1) - dt.date(2022, 11, 1)).days
print(f"  días de train={n_tr}; posteriores al cambio={n_post} ({100 * n_post / n_tr:.1f} %)")
# Escala de MASE: antes vs después del cambio
g = diaria[(diaria["ruta_id"] == "11001-15759")].sort_values("fecha").reset_index(drop=True)
y = g["pasajeros"].to_numpy(float); f = g["fecha"].to_numpy()
d = np.abs(y[7:] - y[:-7]); ff = f[7:]
pre = d[ff < dt.date(2022, 11, 1)].mean(); post = d[(ff >= dt.date(2022, 11, 1)) & (ff < INI_TEST)].mean()
print(f"  11001-15759 escala MASE (|y_t - y_t-7| medio): pre-cambio={pre:.1f}  post-cambio (train)={post:.1f}  "
      f"train completo={d[ff < INI_TEST].mean():.1f}")

titulo("4d. Temporadas altas dentro del test 2023-07-01..2023-12-31 (fechas conocidas del calendario civil)")
print("  Ventanas de origen rodante que cubren 2023-12-15..2023-12-31 (fin de año):",
      [o.isoformat() for o in origenes if o + dt.timedelta(days=1) <= dt.date(2023, 12, 31) <= o + dt.timedelta(days=H)
       or (o + dt.timedelta(days=1) <= dt.date(2023, 12, 24) <= o + dt.timedelta(days=H))])
print("  Último origen con horizonte completo:", origenes[-1], "→ último día pronosticado", origenes[-1] + dt.timedelta(days=H))
print("  Calendario §5.2 debe cubrir hasta:", FIN + dt.timedelta(days=H), "(fin del periodo + 30 días)")
