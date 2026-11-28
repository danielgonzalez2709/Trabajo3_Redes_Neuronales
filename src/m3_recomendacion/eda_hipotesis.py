"""M3 — veredictos y textos de las hipótesis del análisis descriptivo (JJ-2; núcleo §5.12, sección 7).

Recibe las pruebas ya calculadas por ``eda.py`` (con su p ajustado) y arma ``hipotesis.json``: una función por hipótesis
(``hipotesis_1`` … ``hipotesis_9``). El criterio de veredicto es el de ``configs/m3/eda.yaml`` (``regla_de_veredicto``):
``veredicto_de_prueba`` lo implementa y una prueba fija que el texto de la config y la función concuerdan. El veredicto
de cada prueba se calcula UNA vez (en ``Contexto``) y se reutiliza en todos los textos. Los datos son generados (D4).
"""

from __future__ import annotations

ADVERTENCIA = " Datos generados (D4): el patrón, si lo hay, no se atribuye a comportamiento real de turistas."
CIERRE_PENDIENTE = "La figura o tabla sale de JJ-6; la hipótesis se cierra en JJ-10"


# =========================================================================== formato (coma decimal)
def _f(x, dec: int = 3) -> str:
    if abs(x) >= 1000:
        dec = 1
    return f"{x:.{dec}f}".replace(".", ",")


def _fp(p: float) -> str:
    return _f(p, 4) if p < 0.001 else _f(p, 3)


def _ic_txt(ic) -> str:
    return f"[{_f(ic[0])}; {_f(ic[1])}]"


# =========================================================================== criterio de veredicto
def veredicto_de_prueba(p_ajustado: float, efecto: float, ic: tuple[float, float], minimo: float, alfa: float,
                        alternativa: str) -> str:
    """«cumple» / «refuta» / «indeterminada» según la ``regla_de_veredicto`` de ``configs/m3/eda.yaml``.

    cumple: p ajustado < alfa y efecto >= mínimo (``mayor``) o |efecto| >= mínimo (``dos_colas``).
    refuta: p ajustado >= alfa, el IC 95 % contiene el 0 y queda dentro de (−mínimo, +mínimo) (``dos_colas``); con
    ``mayor``, el IC 95 % empieza en 0 o antes y termina por debajo de +mínimo (compatible con cero o con un efecto
    contrario): efecto compatible con cero y lo bastante estrecho para excluir un efecto de la magnitud mínima. Si el IC
    excluye el 0, aunque el p ajustado no alcance alfa por el ajuste, no se refuta.
    Un efecto detectable pero menor que el mínimo no cumple (queda «indeterminada»)."""
    lo, hi = ic
    grande = efecto >= minimo if alternativa == "mayor" else abs(efecto) >= minimo
    if p_ajustado < alfa and grande:
        return "cumple"
    if alternativa == "mayor":
        estrecho = lo <= 0 and hi < minimo
    else:
        estrecho = lo <= 0 <= hi and lo > -minimo and hi < minimo
    if p_ajustado >= alfa and estrecho:
        return "refuta"
    return "indeterminada"


def veredicto_de_hipotesis(resultados: list[str]) -> str:
    """confirmada si alguna prueba cumple; refutada si todas refutan; en otro caso, no concluyente."""
    if any(r == "cumple" for r in resultados):
        return "confirmada"
    if resultados and all(r == "refuta" for r in resultados):
        return "refutada"
    return "no concluyente"


def en_el_limite(ic: tuple[float, float], minimo: float, tolerancia: float, alternativa: str) -> bool:
    """True si un límite del IC está a menos de ``tolerancia`` del mínimo (+mínimo; y −mínimo si es bilateral).

    El veredicto depende entonces del ruido de Monte Carlo y no debe leerse como hallazgo."""
    lo, hi = ic
    cerca = abs(hi - minimo) < tolerancia
    if alternativa != "mayor":
        cerca = cerca or abs(lo + minimo) < tolerancia
    return bool(cerca)


def limite_que_decide(p_ajustado: float, ic: tuple[float, float], minimo: float, alfa: float, alternativa: str):
    """«inferior» / «superior» si la prueba es «indeterminada» con p ajustado >= alfa y un solo límite del IC lo decide.

    Superior: el IC llega al mínimo (o más). Inferior: el IC ya está por debajo del mínimo pero excluye el 0 (o,
    bilateral, llega a −mínimo). En cualquier otro caso no hay un límite que decida y devuelve ``None``."""
    lo, hi = ic
    if p_ajustado < alfa:
        return None
    if alternativa == "mayor":
        estrecho = lo <= 0 and hi < minimo
    else:
        estrecho = lo <= 0 <= hi and lo > -minimo and hi < minimo
    if estrecho:                       # la prueba refuta: ningún límite «decide» una indeterminación
        return None
    if hi >= minimo:
        return "superior"
    if alternativa != "mayor" and lo <= -minimo:
        return "inferior"
    return "inferior" if lo > 0 else "superior"


def frase_limite(pruebas: list[dict], cfg: dict) -> str:
    """Aviso para el ``resultado`` de las pruebas marcadas ``en_el_limite`` (vacío si ninguna), nombrando el límite del IC
    que decide el veredicto y, si es otro, también el que está cerca del mínimo."""
    tol, alfa = cfg["tolerancia_limite"], cfg["alfa"]
    avisos = []
    for p in pruebas:
        e = p["efecto"]
        if not e.get("en_el_limite"):
            continue
        minimo = cfg["efecto_minimo"][e["umbral"]]
        lo, hi = e["ic95"]
        base = f"Atención: el veredicto de {p['id_prueba']} está en el límite del criterio y no debe leerse como hallazgo"
        decide = limite_que_decide(p["p_ajustado"], (lo, hi), minimo, alfa, p["alternativa"])
        if decide == "inferior":
            base += (f": lo decide el límite inferior del IC 95 % ({_f(lo, 4)}), pegado al 0 (si fuera <= 0 la prueba "
                     "refutaría)")
        elif decide == "superior":
            base += f": lo decide el límite superior del IC 95 % ({_f(hi, 4)}), pegado al mínimo ({_f(minimo, 4)})"
            if lo <= 0:
                base += " (si quedara por debajo del mínimo la prueba refutaría)"
        else:
            base += f": un límite del IC 95 % está a menos de {_f(tol)} del mínimo ({_f(minimo, 4)})"
        if decide != "superior" and abs(hi - minimo) < tol:
            base += (f"; además el límite superior ({_f(hi, 4)}) está a menos de {_f(tol)} del mínimo "
                     f"({_f(minimo, 4)})")
        avisos.append(base + ".")
    return " ".join(avisos)


# =========================================================================== búsqueda por nombre (sin posiciones)
def buscar_prueba(pruebas: list[dict], id_prueba: str) -> dict:
    for p in pruebas:
        if p["id_prueba"] == id_prueba:
            return p
    raise KeyError(f"no hay una prueba con id_prueba {id_prueba!r}")


def efecto_adicional(prueba: dict, nombre: str) -> dict:
    for e in prueba.get("efectos_adicionales", []):
        if e["nombre"] == nombre:
            return e
    raise KeyError(f"la prueba {prueba['id_prueba']} no tiene el efecto adicional {nombre!r}")


# =========================================================================== contexto compartido
class Contexto:
    """Lo que comparten las hipótesis: la config, las pruebas por id y el veredicto de cada prueba (calculado una vez)."""

    def __init__(self, cfg: dict, pruebas: list[dict]):
        self.cfg, self.pruebas = cfg, pruebas
        self.minimo = cfg["efecto_minimo"]
        self.alfa_txt = _f(cfg["alfa"], 2)
        self.salida = cfg["salida"]["carpeta"].rstrip("/")
        self.confirmatorias = [p for p in pruebas if p["familia"] == "confirmatoria"]
        self.m = len(self.confirmatorias)
        self.resultado_prueba = {
            p["id_prueba"]: veredicto_de_prueba(p["p_ajustado"], p["efecto"]["valor"], tuple(p["efecto"]["ic95"]),
                                                self.minimo[p["efecto"]["umbral"]], cfg["alfa"], p["alternativa"])
            for p in self.confirmatorias}

    def prueba(self, id_prueba: str) -> dict:
        return buscar_prueba(self.pruebas, id_prueba)

    def de(self, hipotesis: str) -> list[dict]:
        """Pruebas confirmatorias de una hipótesis, en el orden de la familia."""
        return [p for p in self.confirmatorias if p["hipotesis"] == hipotesis]

    def veredicto(self, hipotesis: str) -> str:
        return veredicto_de_hipotesis([self.resultado_prueba[p["id_prueba"]] for p in self.de(hipotesis)])

    def umbral(self, p: dict) -> float:
        return self.minimo[p["efecto"]["umbral"]]

    def criterio(self, ps: list[dict]) -> str:
        partes = [f"{p['id_prueba']}: {self.resultado_prueba[p['id_prueba']]} "
                  f"(mínimo {p['efecto']['umbral']} = {_f(self.umbral(p))})" for p in ps]
        aviso = frase_limite(ps, self.cfg)
        return "Criterio por prueba: " + "; ".join(partes) + "." + (" " + aviso if aviso else "")

    def cifras(self, p: dict) -> str:
        e = p["efecto"]
        return (f"{p['id_prueba']}: estadístico {p['estadistico']['nombre']} = {_f(p['estadistico']['valor'], 4)}, "
                f"p crudo {_fp(p['p_crudo'])}, p ajustado (Holm, m = {self.m}) {_fp(p['p_ajustado'])}, "
                f"{e['nombre']} {_f(e['valor'])} (IC 95 % {_ic_txt(e['ic95'])})")

    def razon(self, veredicto: str, ps: list[dict]) -> str:
        """Frase que explica el veredicto con el criterio de la config (sin interpretar más allá de las cifras)."""
        alfa = self.alfa_txt
        if veredicto == "confirmada":
            return (f"Veredicto «confirmada»: al menos una prueba tiene p ajustado < {alfa} y un efecto igual o mayor "
                    "que el mínimo declarado en la config.")
        if veredicto == "refutada":
            return (f"Veredicto «refutada»: ninguna prueba tiene p ajustado < {alfa} y el IC 95 % del efecto de todas "
                    "contiene el 0 (o está por debajo en las unilaterales) y queda por debajo del mínimo declarado: el "
                    "efecto es compatible con cero y se excluye un efecto de esa magnitud.")
        motivos = [self._motivo(p) for p in ps if self.resultado_prueba[p["id_prueba"]] == "indeterminada"]
        return "Veredicto «no concluyente»: " + "; ".join(motivos) + "."

    def _motivo(self, p: dict) -> str:
        e, alfa = p["efecto"], self.alfa_txt
        lo, hi = e["ic95"]
        minimo = _f(self.umbral(p))
        if p["p_ajustado"] < self.cfg["alfa"]:
            return (f"{p['id_prueba']}: efecto detectable (p ajustado {_fp(p['p_ajustado'])}) pero menor que el mínimo "
                    f"{minimo}; no se declara «confirmada» y se describe su tamaño")
        if lo > 0 or hi < 0:
            return (f"{p['id_prueba']}: el IC 95 % del efecto excluye el 0 ({_ic_txt((lo, hi))}) y es menor que el "
                    f"mínimo {minimo}, pero el p ajustado ({_fp(p['p_ajustado'])}; crudo {_fp(p['p_crudo'])}) no llega "
                    f"a {alfa}: ni se confirma ni se refuta")
        return (f"{p['id_prueba']}: el IC 95 % ({_ic_txt((lo, hi))}) no queda por debajo del mínimo {minimo}, así que no "
                "se descarta un efecto de esa magnitud")

    def dictamen(self, hipotesis: str) -> tuple[str, str]:
        """(veredicto, texto «criterio por prueba + razón») de una hipótesis confirmatoria."""
        v, ps = self.veredicto(hipotesis), self.de(hipotesis)
        return v, f"{self.criterio(ps)} {self.razon(v, ps)}"

    def evidencia(self, ps: list[dict], *archivos: str) -> str:
        ids = ", ".join(p["id_prueba"] for p in ps)
        return f"{self.salida}/pruebas_hipotesis.json ({ids}); " + "; ".join(f"{self.salida}/{a}" for a in archivos)


def _hipotesis(id_: str, enunciado: str, justificacion: str, esperada: str, figura: str, resultado: str,
               veredicto: str, evidencia: str) -> dict:
    return {"id": id_, "enunciado": enunciado, "justificacion": justificacion, "evidencia_esperada": esperada,
            "figura_o_tabla": figura, "resultado": resultado, "veredicto": veredicto, "evidencia": evidencia}


# =========================================================================== H-M3-1
def _texto_ajuste_h1(ctx: Contexto, h1: dict, p1: dict) -> str:
    """Efecto, p crudo y ajustado, IC 95 % sin ajustar e IC ajustado por multiplicidad (nivel 1 − alfa/m)."""
    g, aj, mn = h1["global"], h1["global"]["diferencia_exacta_ic_ajustado"], ctx.minimo["diferencia_tasa"]
    lo, hi = g["diferencia_exacta_ic95"]
    lo_a, hi_a = aj["ic"]
    menor = "menor" if g["diferencia_exacta"] < mn else "igual o mayor"
    return (
        f"Efecto de {_f(100 * g['diferencia_exacta'], 1)} puntos porcentuales ({menor} que el mínimo de "
        f"{_f(100 * mn, 1)}); p crudo {_fp(p1['p_crudo'])} y p ajustado (Holm, m = {ctx.m}) {_fp(p1['p_ajustado'])}. "
        f"El IC 95 % sin ajustar {_ic_txt((lo, hi))} {'excluye' if hi < mn else 'no excluye'} un efecto >= {_f(mn)} y "
        f"{'excluye' if lo > 0 else 'incluye'} el 0. El IC ajustado por multiplicidad (nivel {_f(100 * aj['nivel'], 1)} % "
        f"= 1 − alfa/m con m = {aj['m_familia']}, mismo bootstrap por usuarios) {_ic_txt((lo_a, hi_a))} "
        f"{'incluye' if lo_a <= 0 <= hi_a else 'excluye'} el 0 y {'incluye' if lo_a <= mn <= hi_a else 'excluye'} "
        f"el mínimo {_f(mn)}. ")


def _texto_chi2_h1(x1: dict) -> str:
    """Residuo máximo de la tabla combinación × tipo y reparto del χ² entre celdas coincidentes y no coincidentes."""
    ap, rm = x1["aporte"], x1["residuo_maximo_absoluto"]
    return (
        "Residuos estandarizados ajustados de la tabla combinación × tipo: el residuo máximo en valor absoluto es "
        f"{_f(rm['valor'], 2)} en «{rm['combinacion']}» × {rm['tipo']} (residuo de Pearson de esa celda "
        f"{_f(rm['valor_de_pearson'], 2)}). Las {ap['n_celdas_coincidentes']} celdas coincidentes aportan "
        f"{_f(ap['celdas_coincidentes'], 2)} del χ² de {_f(x1['chi2'], 2)} y las {ap['n_celdas_no_coincidentes']} no "
        f"coincidentes {_f(ap['celdas_no_coincidentes'], 2)}. ")


def hipotesis_1(ctx: Contexto, h1: dict) -> dict:
    p1, c1 = ctx.prueba("H1_permutacion_tasa"), ctx.prueba("C_H1_chi2_combinacion_tipo")
    g, v_dictamen = h1["global"], ctx.dictamen("H-M3-1")
    por_combinacion = "; ".join(f"«{c}»: tasa {_f(x['tasa'])} frente a {_f(x['linea_base_exacta'])} (n = {x['n']})"
                                for c, x in h1["por_combinacion"].items())
    v_sin_corregir = efecto_adicional(c1, "V de Cramér sin corregir")["valor"]
    resultado = (
        f"Tasa de coincidencia {_f(g['tasa'])} ({g['n_coinciden']} de {g['n']} interacciones) frente a una línea base de "
        f"azar exacta de {_f(g['linea_base_exacta'])} (diferencia {_f(g['diferencia_exacta'])}, IC 95 % "
        f"{_ic_txt(g['diferencia_exacta_ic95'])}, bootstrap por usuarios) y de {_f(g['linea_base_marginal'])} con la "
        f"distribución marginal de tipos observada. Por combinación: {por_combinacion}. {ctx.cifras(p1)}. "
        f"{_texto_ajuste_h1(ctx, h1, p1)}{_texto_chi2_h1(h1['chi2_combinacion_tipo'])}"
        f"χ² combinación × tipo: {_f(c1['estadistico']['valor'], 2)} (gl {c1['gl']}, p asintótico {_fp(c1['p_crudo'])}), "
        f"V de Cramér {_f(v_sin_corregir)} sin corregir; con corrección de sesgo {_f(c1['efecto']['valor'])} "
        f"(IC 95 % {_ic_txt(c1['efecto']['ic95'])}). {v_dictamen[1]} El emparejamiento preferencia→tipo es léxico y "
        "nuestro: con otro, el resultado cambia. Los IC y la permutación son por usuario porque cada uno aporta varias "
        "interacciones." + ADVERTENCIA)
    return _hipotesis(
        "H-M3-1",
        "Las preferencias declaradas de un usuario explican el TIPO de destino con el que interactúa: la proporción de "
        "sus interacciones con destinos de un tipo que cubren sus preferencias supera lo esperado si eligiera un "
        "destino al azar del catálogo.",
        "Preferences (usuario) y Type (destino) son las variables de contenido de la fuente que podrían relacionarse. "
        "Para compararlas se empareja cada opción con el tipo del mismo nombre (Beaches→Beach, Historical→Historical, "
        "City→City, Adventure→Adventure, Nature→Nature): es un emparejamiento léxico NUESTRO, la fuente no documenta esa "
        "correspondencia. Si las preferencias no importaran, la coincidencia esperada sería la fracción del catálogo "
        "cuyo tipo está en las preferencias del usuario (línea base exacta).",
        f"Si es cierta: tasa de coincidencia mayor que la línea base exacta en al menos {_f(ctx.minimo['diferencia_tasa'])} "
        f"(IC 95 % por usuarios por encima de 0) y p ajustado < {ctx.alfa_txt} en la permutación. Si es falsa: la tasa "
        "cae dentro de la variación de la permutación y la diferencia es compatible con cero.",
        "preferencias_tipo.png; matriz_preferencias_tipo.csv; coincidencia_preferencias.json",
        resultado, v_dictamen[0],
        ctx.evidencia([p1, c1], "coincidencia_preferencias.json", "matriz_preferencias_tipo.csv"))


# =========================================================================== H-M3-2 y H-M3-3
def hipotesis_2(ctx: Contexto) -> dict:
    p2, c2 = ctx.prueba("H2_permutacion_calificacion"), ctx.prueba("C_H2_mann_whitney_calificacion")
    v, dictamen = ctx.dictamen("H-M3-2")
    dif = efecto_adicional(p2, "diferencia de medias de calificación")
    resultado = (
        f"Media de la calificación cuando el tipo coincide {_f(p2['medias']['coincide'])} "
        f"(n = {p2['n_por_grupo']['coincide']}) frente a {_f(p2['medias']['no_coincide'])} cuando no coincide "
        f"(n = {p2['n_por_grupo']['no_coincide']}); diferencia {_f(p2['estadistico']['valor'])} "
        f"(IC 95 % {_ic_txt(dif['ic95'])}). {ctx.cifras(p2)}. Mann–Whitney unilateral (complementaria): p asintótico "
        f"{_fp(c2['p_crudo'])}. {dictamen} El p viene de permutar combinaciones entre usuarios (respeta que un usuario "
        "aporta varias interacciones); Mann–Whitney supone independencia." + ADVERTENCIA)
    return _hipotesis(
        "H-M3-2",
        "La calificación (1–5) de una interacción es mayor cuando el tipo del destino está cubierto por las preferencias "
        "del usuario.",
        "Si las preferencias reflejaran gusto, una interacción con un destino del tipo preferido debería calificarse "
        "mejor. Usa el mismo emparejamiento léxico nuestro de H-M3-1 (no documentado por la fuente). La calificación es "
        "un atributo de la interacción, no el objetivo de los modelos (D1).",
        f"Si es cierta: diferencia de medias positiva, delta de Cliff >= {_f(ctx.minimo['delta_de_cliff'])} y p ajustado "
        f"< {ctx.alfa_txt}. Si es falsa: la diferencia es compatible con cero con un IC estrecho.",
        "pruebas_hipotesis.json (H2_permutacion_calificacion); calificaciones.csv", resultado, v,
        f"{ctx.salida}/pruebas_hipotesis.json (H2_permutacion_calificacion, C_H2_mann_whitney_calificacion)")


def hipotesis_3(ctx: Contexto) -> dict:
    p3 = ctx.prueba("H3_spearman_popularidad")
    v, dictamen = ctx.dictamen("H-M3-3")
    resultado = (f"{ctx.cifras(p3)}; {p3['destinos_con_cero']} de {p3['n']} destinos tienen 0 interacciones, por lo que "
                 f"hay muchos empates (rangos medios). {dictamen}" + ADVERTENCIA)
    return _hipotesis(
        "H-M3-3",
        "La popularidad del destino (Popularity de la fuente) se relaciona con su número de interacciones: ρ de "
        "Spearman a nivel destino_id distinto de cero.",
        "Popularity es la única variable de contenido del destino que cambia entre los 1 000 ids (nombre, estado, tipo y "
        "temporada son constantes por lugar, D2); un puntaje de popularidad debería acompañar a la demanda. La fuente no "
        "dice cómo se calculó.",
        f"Si es cierta: |ρ| >= {_f(ctx.minimo['rho_de_spearman'])} y p ajustado < {ctx.alfa_txt}. Si es falsa: ρ "
        "compatible con 0 con IC estrecho.",
        "interacciones_por_destino.csv; pruebas_hipotesis.json (H3_spearman_popularidad)", resultado, v,
        ctx.evidencia([p3], "interacciones_por_destino.csv"))


# =========================================================================== H-M3-4
def hipotesis_4(ctx: Contexto) -> dict:
    ps = ctx.de("H-M3-4")
    v, dictamen = ctx.dictamen("H-M3-4")
    detalle = "; ".join(
        f"{p['id_prueba']}: χ² {_f(p['estadistico']['valor'], 2)} (gl {p['gl']}), p crudo {_fp(p['p_crudo'])}, "
        f"p ajustado {_fp(p['p_ajustado'])}, V sin corregir "
        f"{_f(efecto_adicional(p, 'V de Cramér sin corregir')['valor'])}, V corregida {_f(p['efecto']['valor'])} "
        f"(IC 95 % {_ic_txt(p['efecto']['ic95'])})" for p in ps)
    return _hipotesis(
        "H-M3-4",
        "La demografía del usuario (género, número de adultos, número de niños) se relaciona con el tipo de destino "
        "elegido (p. ej. familias con niños eligen más playa).",
        "Es la hipótesis de sentido común sobre quién va adónde; el conjunto trae esas tres variables del usuario. Tipo y "
        "lugar son la misma partición de los destinos (cada lugar tiene un solo tipo), así que una sola prueba por "
        "variable cubre ambos. Un usuario aporta varias interacciones: el p sale de permutar la variable ENTRE usuarios.",
        f"Si es cierta: V de Cramér >= {_f(ctx.minimo['v_de_cramer'])} y p ajustado < {ctx.alfa_txt} en al menos una "
        "variable. Si es falsa: V compatible con ruido (IC por debajo del mínimo) en las tres.",
        "demografia_tipo.csv; pruebas_hipotesis.json (H4_*)", f"{detalle}. {dictamen}" + ADVERTENCIA, v,
        ctx.evidencia(ps, "demografia_tipo.csv"))


# =========================================================================== H-M3-5
def _texto_nivel_h5(nombre: str, info: dict, clave_top: str) -> str:
    """Gini, HHI y cuota del top de un nivel de concentración, con la referencia del reparto uniforme."""
    obs, az = info["observado"], info["azar_uniforme"]
    top = az["cuota_top"][clave_top]
    return (f"{nombre} ({info['n_entidades']} entidades): Gini {_f(obs['gini'])} (azar: media {_f(az['gini']['media'])}, "
            f"IC 95 % {_ic_txt(az['gini']['ic95'])}), HHI {_f(obs['hhi'], 5)} (azar {_f(az['hhi']['media'], 5)}), cuota "
            f"del {_f(100 * float(clave_top), 0)} % más popular {_f(obs['cuota_top'][clave_top])} "
            f"(azar {_f(top['media'])}).")


def hipotesis_5(ctx: Contexto, conc: dict) -> dict:
    ps = ctx.de("H-M3-5")
    v, dictamen = ctx.dictamen("H-M3-5")
    clave_top = f"{ctx.cfg['fracciones_top'][0]:g}"
    niveles = " ".join(_texto_nivel_h5(n, i, clave_top) for n, i in conc["niveles"].items())
    resultado = (niveles + " " + "; ".join(ctx.cifras(p) for p in ps) + f". {dictamen} La referencia es un reparto "
                 "multinomial uniforme (no impone pares usuario–destino únicos)." + ADVERTENCIA)
    return _hipotesis(
        "H-M3-5",
        "Las interacciones se concentran en pocos destinos más de lo esperado si las mismas interacciones se repartieran "
        "uniformemente al azar (cola larga más allá del azar), a nivel destino_id o lugar.",
        "El enunciado pide la concentración en populares. Un reparto uniforme ya produce desigualdad por azar (unos "
        "destinos reciben 0 y otros varias); por eso se compara el Gini, el HHI y la cuota top con su distribución bajo "
        "reparto uniforme simulado y no con 0.",
        f"Si es cierta: Gini observado mayor que la media del azar en al menos {_f(ctx.minimo['exceso_de_gini'])} y "
        f"fuera de su IC 95 %, p ajustado < {ctx.alfa_txt}. Si es falsa: el observado cae dentro de la banda del azar.",
        "cola_larga.png; lorenz.png; concentracion.json", resultado, v, ctx.evidencia(ps, "concentracion.json"))


# =========================================================================== H-M3-6
def hipotesis_6(ctx: Contexto) -> dict:
    ps = ctx.de("H-M3-6")
    v, dictamen = ctx.dictamen("H-M3-6")
    resultado = ("; ".join(ctx.cifras(p) for p in ps) + f". {dictamen} Los tests suponen independencia entre "
                 "interacciones y la misma persona puede aparecer en ambos orígenes." + ADVERTENCIA)
    return _hipotesis(
        "H-M3-6",
        "Las reseñas y el historial se comportan distinto: difieren en los tipos de destino o en la distribución de las "
        "calificaciones.",
        "D1 unió los dos archivos como una sola interacción implícita. Esa unión solo es inocua si ambos orígenes se "
        "parecen; si difirieran, habría que modelar el origen aparte.",
        f"Si es cierta: V de Cramér >= {_f(ctx.minimo['v_de_cramer'])} (origen × tipo) o delta de Cliff >= "
        f"{_f(ctx.minimo['delta_de_cliff'])} (calificación), con p ajustado < {ctx.alfa_txt}. Si es falsa: ambos efectos "
        "compatibles con cero.",
        "calificaciones_origen.png; calificaciones.csv; pruebas_hipotesis.json (H6_*)", resultado, v,
        ctx.evidencia(ps, "calificaciones.csv"))


# =========================================================================== H-M3-7 a H-M3-9 (se cierran al modelar)
def hipotesis_7() -> dict:
    return _hipotesis(
        "H-M3-7",
        "Una red con variables de contenido (preferencias del usuario, tipo del destino) no supera a la línea base de "
        "popularidad por más que la variabilidad entre semillas (NDCG@5, 30 semillas).",
        "Con datos generados donde la relación preferencias–tipo es débil o nula, el contenido puede no aportar; el "
        "enunciado pide comparar de forma justa y con 30 semillas.",
        "Falsable: si la media de NDCG@5 de la red menos la de popularidad supera la desviación estándar entre las 30 "
        "semillas de la red, la hipótesis se refuta; si no, se confirma.",
        "Se cierra al modelar (JJ-10): results/data/m3/summary.json",
        "Pendiente: se cierra en JJ-10, cuando existan la red, la línea base de popularidad y las 30 semillas.",
        "pendiente", "Aún no existe (results/data/m3/summary.json lo produce JJ-5).")


def hipotesis_8() -> dict:
    return _hipotesis(
        "H-M3-8",
        "El acierto medido por lugar (5 lugares) es mucho mayor que el medido por destino_id (1 000 ids) en todos los "
        "modelos.",
        "Los 1 000 ids son 5 lugares repetidos 200 veces (D2): acertar el lugar es un problema de 5 clases y acertar el "
        "id exacto, de 1 000.",
        "Falsable: Recall@K por lugar menor o igual que Recall@K por destino_id en algún modelo y algún K refuta la "
        "hipótesis.",
        CIERRE_PENDIENTE,
        "Pendiente: se cierra en JJ-10, con las métricas por lugar y por destino_id de todos los modelos.",
        "pendiente", "Aún no existe.")


def hipotesis_9(ctx: Contexto) -> dict:
    p_max = ctx.cfg["actividad"]["pocas_max"]
    return _hipotesis(
        "H-M3-9",
        f"Los usuarios con pocas interacciones (1 a {p_max}) obtienen un NDCG@5 menor que los de muchas "
        f"({p_max + 1} o más) tanto en la popularidad como en la red.",
        "Con D3 los usuarios con pocas interacciones tienen una sola interacción de entrenamiento, así que los modelos "
        "colaborativos y de contenido tienen menos información sobre ellos.",
        "Falsable: NDCG@5 de «pocas» mayor o igual que el de «muchas» en algún modelo refuta la hipótesis.",
        CIERRE_PENDIENTE,
        "Pendiente: se cierra en JJ-10, con el desempeño separado por grupo de actividad.",
        "pendiente", "Aún no existe.")


def construir_hipotesis(cfg: dict, pruebas: list[dict], h1: dict, conc: dict) -> list[dict]:
    """Las 9 hipótesis de ``hipotesis.json``: 1–6 con veredicto de las pruebas y 7–9 pendientes de modelar."""
    ctx = Contexto(cfg, pruebas)
    return [hipotesis_1(ctx, h1), hipotesis_2(ctx), hipotesis_3(ctx), hipotesis_4(ctx), hipotesis_5(ctx, conc),
            hipotesis_6(ctx), hipotesis_7(), hipotesis_8(), hipotesis_9(ctx)]
