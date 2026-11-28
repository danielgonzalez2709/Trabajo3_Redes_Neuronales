import ast, math, json, sys
import numpy as np
R = r"C:\Repositorios\Trabajo3_Redes_Neuronales"
src = open(R + r"\src\m3_recomendacion\red.py", encoding="utf-8").read()
tree = ast.parse(src)
fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "medidas_personalizacion"][0]
ns = {"np": np}
exec(compile(ast.Module(body=[fn], type_ignores=[]), "red_medidas", "exec"), ns)
f = ns["medidas_personalizacion"]

def ref(S, k=10):
    # implementación independiente: ANOVA de dos vías con bucles
    S = np.asarray(S, float); n, m = S.shape
    mu = S.sum() / (n * m)
    a = np.array([S[u].sum() / m - mu for u in range(n)])
    b = np.array([S[:, i].sum() / n - mu for i in range(m)])
    E = np.empty_like(S)
    for u in range(n):
        for i in range(m):
            E[u, i] = S[u, i] - mu - a[u] - b[i]
    pers = np.mean([math.sqrt(np.mean((E[:, i] - E[:, i].mean()) ** 2)) for i in range(m)])
    tot = ((S - mu) ** 2).sum()
    # identidad de ANOVA
    ident = (m * (a ** 2).sum() + n * (b ** 2).sum() + (E ** 2).sum(), tot)
    listas = set()
    tops = []
    for u in range(n):
        o = sorted(range(m), key=lambda i: (-S[u, i], i))[:k]
        listas.add(tuple(o)); tops.append(o[0])
    vals, c = np.unique(tops, return_counts=True)
    return dict(personalizacion=pers, fraccion_varianza_interaccion=(E ** 2).sum() / tot if tot > 0 else 0.0,
                listas_top10_distintas=len(listas), fraccion_mismo_top1=c.max() / n), ident

rng = np.random.default_rng(1)
for caso in range(5):
    n, m = rng.integers(2, 30), rng.integers(11, 60)
    S = rng.normal(size=(n, 1)) * 3 + rng.normal(size=(1, m)) + 0.3 * rng.normal(size=(n, m))
    a, ident = f(S), ref(S)
    r, ident = ref(S)
    print(caso, {k: (round(a[k], 10), round(float(r[k]), 10)) for k in a}, "ANOVA", np.isclose(*ident))
# test a mano
u = np.array([1.0, -1.0, 2.0, -2.0]); v = np.linspace(-1, 1, 12); S = np.outer(u, v)
print("interacción pura:", f(S), " a mano sqrt(2.5)*6/11 =", math.sqrt(2.5) * 6 / 11, " mean|v| =", np.abs(v).mean(), 6/11)
alfa = np.array([0.0, 5.0, -3.0, 10.0]); beta = np.linspace(1, 0, 12); S = alfa[:, None] + beta[None, :]
print("aditiva:", f(S), " std(alfa) =", alfa.std())
# casos borde
print("constante:", f(np.full((5, 20), 0.7)))
print("un usuario:", f(np.random.default_rng(0).normal(size=(1, 20))))
Se = np.zeros((3, 20)); Se[:, :] = 1.0; Se[0, 15] = 2  # empates masivos
print("empates:", f(Se), "orden estable usuario 1:", np.argsort(-Se[1], kind='stable')[:10])
print("k > n destinos:", f(np.random.default_rng(0).normal(size=(4, 5))))
try:
    print("vacío:", f(np.zeros((0, 20))))
except Exception as e:
    print("vacío -> excepción:", type(e).__name__, e)
# invariancia: S + c_u (desplazamiento por usuario) no cambia nada; S*escala escala personalizacion
S = np.random.default_rng(3).normal(size=(50, 100))
c = np.random.default_rng(4).normal(size=(50, 1)) * 10
A, B = f(S), f(S + c)
print("invariancia a alfa_u:", {k: np.isclose(A[k], B[k]) for k in A})
print("escala x3:", f(3 * S)["personalizacion"] / A["personalizacion"])
for cte in (0.7, 0.1, 1.0, 0.5, 0.3, -0.2513):
    for shp in ((5, 20), (606, 1000), (326, 1000), (1, 10)):
        Sc = np.full(shp, cte)
        r = f(Sc)
        tot = float(((Sc - Sc.mean()) ** 2).sum())
        print(f"constante {cte} {shp}: frac={r['fraccion_varianza_interaccion']:.4g} pers={r['personalizacion']:.3g} total={tot:.3g}")
