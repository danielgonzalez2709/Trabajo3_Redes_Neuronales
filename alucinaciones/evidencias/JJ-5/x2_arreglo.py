import numpy as np, json
R = r"C:\Repositorios\Trabajo3_Redes_Neuronales"
def frac(S, tol_rel=None):
    S = np.asarray(S, float); n_u, n_i = S.shape; mu = S.mean()
    a = S.mean(1) - mu; b = S.mean(0) - mu
    E = S - S.mean(1, keepdims=True) - S.mean(0, keepdims=True) + mu
    e2 = float((E**2).sum()); den = e2 + n_i*float((a**2).sum()) + n_u*float((b**2).sum())
    return 0.0 if den == 0 else e2/den
rng = np.random.default_rng(1); out = []
for v in (0.7, -0.2513, 0.3, 123.456, 1e6):
    for sh in [(5, 20), (606, 1000)]:
        for _ in range(5):
            Sc = v + rng.integers(-3, 4, size=sh)*np.spacing(v); out.append(frac(Sc))
            Sc = np.full(sh, v); Sc[rng.integers(sh[0]), rng.integers(sh[1])] = np.nextafter(v, np.inf); out.append(frac(Sc))
            out.append(frac(np.full(sh, v)))
out = np.array(out); print("arreglo propuesto: min", out.min(), "max", out.max(), "todos en [0,1]:", bool(((out>=0)&(out<=1)).all()))
S = rng.normal(size=(50, 80)); tot = ((S-S.mean())**2).sum(); E = S - S.mean(1, keepdims=True) - S.mean(0, keepdims=True) + S.mean()
print("en S genérica coincide con el actual:", frac(S), (E**2).sum()/tot)
z = np.load(r"C:/Users/juanj/AppData/Local/Temp/claude/92481566dd5b376c/7690fb16-ed9d-4177-8666-ce080137b320/scratchpad/jj5/S0.npz", allow_pickle=True)
S0 = z["S"]; E0 = S0 - S0.mean(1, keepdims=True) - S0.mean(0, keepdims=True) + S0.mean()
print("S0: actual", (E0**2).sum()/((S0-S0.mean())**2).sum(), " arreglo", frac(S0))
fr = [json.load(open(R + rf"\results\data\m3\semillas\red_seed{i}.json", encoding="utf-8"))["diagnosticos"] for i in range(30)]
print("30 semillas: frac min %.4f max %.4f ; degeneradas: %d ; rango_max min %.4g" % (min(d["fraccion_varianza_interaccion"] for d in fr), max(d["fraccion_varianza_interaccion"] for d in fr), sum(d["degenerado"] for d in fr), min(d["rango_max_por_usuario"] for d in fr)))
