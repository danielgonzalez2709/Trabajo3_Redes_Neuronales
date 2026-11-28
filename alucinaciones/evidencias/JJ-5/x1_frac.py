import ast, numpy as np
R = r"C:\Repositorios\Trabajo3_Redes_Neuronales"
src = open(R + r"\src\m3_recomendacion\red.py", encoding="utf-8").read()
fn = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "medidas_personalizacion"][0]
ns = {"np": np}; exec(compile(ast.Module(body=[fn], type_ignores=[]), "m", "exec"), ns); f = ns["medidas_personalizacion"]
rng = np.random.default_rng(0)
# 0) identidad exacta: ||S-mu||^2 = nI||a||^2 + nU||b||^2 + ||E||^2 (ANOVA ortogonal)
S = rng.normal(size=(50, 80)); mu = S.mean(); a = S.mean(1) - mu; b = S.mean(0) - mu
E = S - S.mean(1, keepdims=True) - S.mean(0, keepdims=True) + mu
print("identidad ANOVA |dif|:", abs(((S-mu)**2).sum() - (80*(a**2).sum() + 50*(b**2).sum() + (E**2).sum())))
print("aleatoria:", f(S)["fraccion_varianza_interaccion"], " solo α_u+β_i:", f(a[:,None]+b[None,:]+mu)["fraccion_varianza_interaccion"])
# 1) constante exacta (los tres casos de la prueba)
for v, sh in [(0.7, (5, 20)), (-0.2513, (606, 1000)), (0.3, (326, 1000))]:
    Sc = np.full(sh, v); tot = ((Sc - Sc.mean())**2).sum(); Ec = Sc - Sc.mean(1, keepdims=True) - Sc.mean(0, keepdims=True) + Sc.mean()
    print("constante", v, sh, "ptp", np.ptp(Sc), "tot", tot, "||E||^2", (Ec**2).sum(), "-> f:", f(Sc))
# 2) casi constante: ruido de 1..k ulp, y ruido de amplitud relativa 1e-16..1e-10
peor = {}
for v in (0.7, -0.2513, 0.3, 123.456, 1e6):
    for sh in [(5, 20), (606, 1000), (326, 1000)]:
        for modo in ("ulp1", "ulp_rand", "una_celda", "fila", "col"):
            for rep in range(3):
                Sc = np.full(sh, v)
                if modo == "ulp1":
                    m = rng.random(sh) < 0.5; Sc[m] = np.nextafter(v, np.inf)
                elif modo == "ulp_rand":
                    Sc = v + rng.integers(-3, 4, size=sh) * np.spacing(v)
                elif modo == "una_celda":
                    Sc[rng.integers(sh[0]), rng.integers(sh[1])] = np.nextafter(v, np.inf)
                elif modo == "fila":
                    Sc[rng.integers(sh[0]), :] = np.nextafter(v, np.inf)
                else:
                    Sc[:, rng.integers(sh[1])] = np.nextafter(v, np.inf)
                r = f(Sc)["fraccion_varianza_interaccion"]
                key = (v, sh, modo)
                peor[key] = max(peor.get(key, -np.inf), r) if np.isfinite(r) else np.nan
fuera = {k: r for k, r in peor.items() if not (0 <= r <= 1)}
print("casos casi-constantes con fracción fuera de [0,1]:", len(fuera), "de", len(peor))
for k, r in list(fuera.items())[:25]: print("  ", k, r)
# 3) amplitud relativa creciente: desde cuándo vuelve a [0,1]
for v in (0.7, -0.2513):
    for rel in (1e-16, 1e-15, 1e-14, 1e-13, 1e-12, 1e-10, 1e-8):
        rs = [f(v + v*rel*rng.normal(size=(606, 1000)))["fraccion_varianza_interaccion"] for _ in range(3)]
        print(f"v={v} ruido relativo {rel:.0e}: fracción min {min(rs):.4g} max {max(rs):.4g}")
# 4) NaN y escala
Sn = rng.normal(size=(4, 6)); Sn[0, 0] = np.nan; print("con NaN:", f(Sn)["fraccion_varianza_interaccion"])
S1 = rng.normal(size=(30, 40)); print("escala x10: pers", f(S1)["personalizacion"], f(10*S1)["personalizacion"], " frac", f(S1)["fraccion_varianza_interaccion"], f(10*S1)["fraccion_varianza_interaccion"])
# 5) E != 0 con el mismo orden para todos: S_ui = a_u * beta_i, a_u > 0
a = rng.uniform(0.5, 3, size=(30, 1)); bb = rng.normal(size=(1, 40)); S2 = a * bb
m2 = f(S2); print("multiplicativo: E≠0 pers", m2["personalizacion"], "frac", m2["fraccion_varianza_interaccion"], "listas", m2["listas_top10_distintas"], "top1", m2["fraccion_mismo_top1"])
