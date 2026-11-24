"""Comprobaciones adicionales (R2). Uso: cd <repo> && PYTHONIOENCODING=utf-8 .venv/Scripts/python <ruta>/auditoria_m1_extra.py"""
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
cfg = yaml.safe_load(open(REPO / "configs/m1/datos.yaml", encoding="utf-8"))
diaria = pd.read_parquet(REPO / "data/processed/m1/demanda_diaria.parquet")
detalle = pd.read_parquet(REPO / "data/processed/m1/demanda_detalle.parquet")
marcas = pd.read_parquet(REPO / "data/processed/m1/marcas_anomalos.parquet")
INI_TEST, FIN, H = dt.date(2023, 7, 1), dt.date(2023, 12, 31), 30

print("E1. Todos los orígenes (cada 7 días desde 2021-02-01): días ≤ origen cuya marca cambia si se calcula con datos ≤ origen")
tot, peor = 0, []
o = dt.date(2021, 2, 1)
while o + dt.timedelta(days=H) <= FIN:
    hasta = diaria[diaria["fecha"] <= o].reset_index(drop=True)
    mt, _ = D.marcar_anomalos(hasta.assign(anomalo=False), cfg["anomalos"])
    ref = marcas[marcas["fecha"] <= o].reset_index(drop=True)
    dif = (mt[D.REGLAS].any(axis=1) != ref[D.REGLAS].any(axis=1))
    if dif.any():
        peor.append((o.isoformat(), int(dif.sum()),
                     sorted({(r, f.isoformat()) for r, f in ref.loc[dif, ["ruta_id", "fecha"]].itertuples(index=False)})[:6]))
    tot += 1
    o += dt.timedelta(days=7)
print(f"  orígenes revisados={tot}; con alguna diferencia={len(peor)}")
for p in peor:
    print("   ", p)

print("\nE2. Sensibilidad de la regla a la ventana centrada: umbral 5 MAD (más cercano al límite) con datos ≤ origen, test")
cfg5 = yaml.safe_load(yaml.safe_dump(cfg["anomalos"]))
for r in ("caida_robusta", "pico_robusto", "pasajeros_por_despacho_bajo"):
    cfg5[r]["umbral_mad"] = 4.0
mfull, _ = D.marcar_anomalos(diaria.assign(anomalo=False), cfg5)
n_dif, n_ori = 0, 0
o = INI_TEST
while o + dt.timedelta(days=H) <= FIN:
    hasta = diaria[diaria["fecha"] <= o].reset_index(drop=True)
    mt, _ = D.marcar_anomalos(hasta.assign(anomalo=False), cfg5)
    ref = mfull[mfull["fecha"] <= o].reset_index(drop=True)
    n_dif += int((mt[D.REGLAS].any(axis=1) != ref[D.REGLAS].any(axis=1)).sum())
    n_ori += 1
    o += dt.timedelta(days=7)
print(f"  con umbral 4 MAD: marcas totales={int(mfull[D.REGLAS].any(axis=1).sum())}, en test={int(mfull.loc[mfull['fecha'] >= INI_TEST, D.REGLAS].any(axis=1).sum())}; "
      f"diferencias acumuladas en {n_ori} orígenes de test={n_dif}")

print("\nE3. 11001-15759: despachos y pasajeros por tipo y por clase, semestres alrededor de nov-2022")
g = detalle[detalle["ruta_id"] == "11001-15759"].copy()
g["periodo"] = np.where(pd.to_datetime(g["fecha"]) < "2022-11-01", "a_2021-01..2022-10",
                        np.where(pd.to_datetime(g["fecha"]) < "2023-07-01", "b_2022-11..2023-06", "c_test_2023-07..12"))
x = g.groupby(["periodo", "tipo_despacho"])[["pasajeros", "despachos"]].sum()
dias = g.groupby("periodo")["fecha"].nunique()
print((x.div(dias, level="periodo", axis=0)).round(0).rename(columns=lambda c: c + "_por_dia").to_string())
print((g.groupby(["periodo", "tipo_despacho", "clase_vehiculo"])["pasajeros"].sum()
       .div(dias, level="periodo").round(0).unstack(fill_value=0)).to_string())
print("  Mes a mes 2022-09..2023-01 (TRANSITO): pasajeros, despachos, pasajeros/despacho")
gm = g[g["tipo_despacho"] == "TRANSITO"].assign(mes=pd.to_datetime(g["fecha"]).dt.to_period("M"))
gm = gm.groupby("mes")[["pasajeros", "despachos"]].sum()
gm["pax_por_desp"] = gm["pasajeros"] / gm["despachos"]
print(gm.loc["2022-08":"2023-02"].round(2).to_string())
print("  Fecha exacta del salto (mediana móvil de 14 días de pasajeros TRANSITO por día, 2022-10-15..2022-11-20):")
gd = g[g["tipo_despacho"] == "TRANSITO"].groupby("fecha")["pasajeros"].sum()
gd.index = pd.to_datetime(gd.index)
print(gd.loc["2022-10-20":"2022-11-15"].to_string())

print("\nE4. Normalización con ceros imputados: media/desv. de log1p(pasajeros) en train, con y sin días sin_registro")
for ruta, g in diaria[diaria["fecha"] < INI_TEST].groupby("ruta_id"):
    z = np.log1p(g["pasajeros"].astype(float))
    zc = z[~g["sin_registro"]]
    print(f"  {ruta}: con 0: media={z.mean():.3f} sd={z.std():.3f}   sin 0 imputados: media={zc.mean():.3f} sd={zc.std():.3f}  "
          f"z de un 0 imputado (normalizado con 0)={(0 - z.mean()) / z.std():.1f}")

print("\nE5. MASE del ingenuo estacional 7 días (un paso, en test) por ruta = MAE_test(|y_t - y_t-7|) / escala_train")
for ruta, g in diaria.groupby("ruta_id"):
    g = g.sort_values("fecha").reset_index(drop=True)
    y = g["pasajeros"].to_numpy(float); f = g["fecha"].to_numpy()
    d = np.abs(y[7:] - y[:-7]); ff = f[7:]
    esc = d[ff < INI_TEST].mean()
    esc_12m = d[(ff >= dt.date(2022, 7, 1)) & (ff < INI_TEST)].mean()
    print(f"  {ruta}: escala train={esc:7.1f}  escala últimos 12 m de train={esc_12m:7.1f}  MAE test 1 paso={d[ff >= INI_TEST].mean():7.1f}  "
          f"MASE={d[ff >= INI_TEST].mean() / esc:.2f} (con escala 12 m: {d[ff >= INI_TEST].mean() / esc_12m:.2f})")

print("\nE6. ¿Columnas de la serie que un pipeline 'select_dtypes(number|bool)' metería como entrada?")
print("  ", diaria.select_dtypes(include=["number", "bool"]).columns.tolist())
