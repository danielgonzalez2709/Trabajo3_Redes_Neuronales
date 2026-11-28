import numpy as np, pandas as pd, json
R = r"C:\Repositorios\Trabajo3_Redes_Neuronales"
z = np.load(r"C:/Users/juanj/AppData/Local/Temp/claude/92481566dd5b376c/7690fb16-ed9d-4177-8666-ce080137b320/scratchpad/jj5/S0.npz", allow_pickle=True)
S, U, V, b, k_i, tipo, cat, up = z["S"], z["U"], z["V"], z["b"], z["k_i"], z["tipo"], z["cat"], z["uprueba"]
print("rango por usuario: min %.4f mediana %.4f max %.4f" % tuple(np.percentile(S.max(1)-S.min(1), [0, 50, 100])))
print("‖u‖ min/max %.3f/%.3f   ‖v_i‖ min/max %.3f/%.3f   |b| max %.3f" % (np.linalg.norm(U,axis=1).min(), np.linalg.norm(U,axis=1).max(), np.linalg.norm(V,axis=1).min(), np.linalg.norm(V,axis=1).max(), np.abs(b).max()))
# descomposición de S: media + efecto usuario + efecto destino + interacción
mu = S.mean(); fu = S.mean(1, keepdims=True) - mu; fi = S.mean(0, keepdims=True) - mu; E = S - mu - fu - fi
tot = ((S-mu)**2).sum()
print("varianza: usuario %.4f | destino %.4f | interacción %.4f (fracciones)" % ((fu**2).sum()*S.shape[1]/tot, (fi**2).sum()*S.shape[0]/tot, (E**2).sum()/tot))
print("personalizacion del código (media_i std_u s_ui, ddof0) = %.5f ; sobre S doble-centrada = %.5f" % (S.std(0).mean(), E.std(0).mean()))
# rankings: ¿iguales entre usuarios? (todo el catálogo, sin excluir historial)
top10 = np.argsort(-S, 1)[:, :10]
print("listas top-10 (catálogo completo) distintas:", len({tuple(r) for r in top10}), "de", len(top10), "; destinos distintos:", len(np.unique(top10)))
orden_b = np.argsort(-b)[:10]
print("solapamiento medio top-10 del usuario con top-10 de b_i:", np.mean([len(set(r) & set(orden_b)) for r in top10]))
from scipy.stats import spearmanr
rho = [spearmanr(S[i], fi.ravel()).correlation for i in range(len(S))]
print("Spearman(s_u·, efecto de destino): min %.3f mediana %.3f" % (np.min(rho), np.median(rho)))
# fríos: índice 0 → puntaje sólo por tipo
frio = k_i == 0
print("fríos:", frio.sum())
for t in np.unique(tipo):
    m = frio & (tipo == t)
    if m.any():
        dif = float(np.abs(S[:, m] - S[:, m][:, :1]).max())
        pct = np.mean([(S[i, m][0] < np.sort(S[i, ~frio])[::-1][9]) for i in range(len(S))])
        print(f"  tipo {t}: {m.sum()} fríos, max dif entre fríos del mismo tipo = {dif:.1e}; usuarios con frío por debajo del 10.º no frío: {pct:.3f}")
# posición del mejor frío respecto de los cálidos
pos = [int((S[i, ~frio] > S[i, frio].max()).sum()) for i in range(len(S))]
print("número de no fríos por encima del mejor frío: min", min(pos), "mediana", int(np.median(pos)))
print("b_i fríos: media %.3f ; cálidos: media %.3f" % (b[frio].mean(), b[~frio].mean()))
# por semilla: diagnósticos
ds = [json.load(open(R + rf"\results\data\m3\semillas\red_seed{s}.json", encoding="utf-8"))["diagnosticos"] for s in range(30)]
print("degenerado en alguna semilla:", any(d["degenerado"] for d in ds), " min rango:", min(d["rango_max_por_usuario"] for d in ds), " min producto normas:", min(d["max_norma_u_por_norma_v"] for d in ds))
print("semillas con ndcg5_validacion_mejor = 0:", [s for s, d in enumerate(ds) if d["ndcg5_validacion_mejor"] == 0], " mejor_epoca de ellas:", [d["mejor_epoca"] for d in ds if d["ndcg5_validacion_mejor"] == 0])
print("epoca_parada − mejor_epoca:", sorted({d["epoca_parada"] - d["mejor_epoca"] for d in ds}), " ¿alguna llegó a max_epocas?", any(d["epoca_parada"] == 100 for d in ds))
print("mejor_epoca por semilla:", [d["mejor_epoca"] for d in ds])
