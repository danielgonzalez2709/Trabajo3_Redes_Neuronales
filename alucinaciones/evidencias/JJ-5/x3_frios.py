import numpy as np, pandas as pd
R = r"C:\Repositorios\Trabajo3_Redes_Neuronales"
z = np.load(r"C:/Users/juanj/AppData/Local/Temp/claude/92481566dd5b376c/7690fb16-ed9d-4177-8666-ce080137b320/scratchpad/jj5/S0.npz", allow_pickle=True)
S, cat, up, tipo, k_i, V, b = z["S"], z["cat"], z["uprueba"], z["tipo"], z["k_i"], z["V"], z["b"]
inter = pd.read_parquet(R + r"\data\processed\m3\interacciones.parquet")
tr = set(inter[inter.split == "train"].destino_id.astype(int))
frio = np.array([int(c) not in tr for c in cat]); print("fríos en catálogo:", frio.sum(), " k_i==0 coincide con frío:", bool(((k_i == 0) == frio).all()))
# todos los fríos de un mismo tipo: mismo v_i, b_i y mismo puntaje
for t in np.unique(tipo):
    m = frio & (tipo == t)
    if m.sum(): print(f"  tipo {t:10s} fríos {m.sum():3d}  ptp V {np.ptp(V[m], axis=0).max():.2e}  ptp b {np.ptp(b[m]):.2e}  ptp S por usuario {np.ptp(S[:, m], axis=1).max():.2e}")
conocido = inter[inter.split.isin(["train", "validacion"])].groupby("usuario_id").destino_id.apply(lambda s: set(map(int, s))).to_dict()
col = {int(c): j for j, c in enumerate(cat)}
rk_mejor_frio, supera_alguno, n_frio_top10, gap = [], [], [], []
for r, u in enumerate(up):
    cand = np.array([j for c, j in col.items() if c not in conocido.get(int(u), set())])
    s = S[r, cand]; f = frio[cand]
    orden = np.argsort(-s, kind="stable")
    rango = np.empty(len(s), int); rango[orden] = np.arange(1, len(s) + 1)
    rk_mejor_frio.append(rango[f].min())
    supera_alguno.append(s[f].max() > s[~f].min())
    n_frio_top10.append(int(f[orden[:10]].sum()))
    gap.append(np.sort(s[~f])[-10] - s[f].max())   # 10.º no frío − mejor frío
rk = np.array(rk_mejor_frio); g = np.array(gap)
print("usuarios:", len(up))
print("mejor posición de un frío entre los candidatos: min", rk.min(), " mediana", np.median(rk), " max", rk.max())
print("usuarios donde algún frío supera a algún destino con train:", int(np.sum(supera_alguno)), "/", len(up))
print("fríos en el top-10 (orden estable, sin desempate al azar): total", int(np.sum(n_frio_top10)))
print("margen (10.º no frío − mejor frío): min %.4f mediana %.4f" % (g.min(), np.median(g)))
# fracción de no fríos que el mejor frío supera, por usuario
print("fracción de destinos con train superados por el mejor frío (mediana por usuario): %.3f" % np.median([(rk_mejor_frio[i]) for i in range(len(up))]) if False else "")
pos = []
for r, u in enumerate(up):
    cand = np.array([j for c, j in col.items() if c not in conocido.get(int(u), set())]); s = S[r, cand]; f = frio[cand]
    pos.append(np.mean(s[~f] < s[f].max()))
pos = np.array(pos); print("fracción de destinos con train por debajo del mejor frío: min %.3f mediana %.3f max %.3f" % (pos.min(), np.median(pos), pos.max()))
