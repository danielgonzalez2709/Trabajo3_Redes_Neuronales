"""M3 — datos procesados (JJ-1, fase B) y secciones 1–2 de la plantilla común (núcleo §5.12). Sin red.

Entrada: los 4 CSV de «Travel Recommendation Dataset» (Kaggle, Aman Mehra) y su ``archive.zip`` en ``data/raw/m3/`` (descarga
manual; SHA-256 verificados contra la config) y los metadatos crudos de la API de Kaggle (``JJ-1_kaggle_metadata.json``).
Salida: ``destinos.parquet``, ``usuarios.parquet`` e ``interacciones.parquet`` (núcleo §5.7) y, en ``results/data/m3/eda/``
(núcleo §5.12), ``ficha.json``, ``calidad.csv`` y ``diccionario.json``.

Decisiones [DECIDIDO, Juan José, 25-nov] (docs/spec/partes/juanjose.md §3.1):
  D1  interacción = unión de Reviews y UserHistory como retroalimentación implícita; ``Rating`` / ``ExperienceRating`` se
      conservan como ``calificacion`` con su ``origen``; un par (usuario, destino) repetido es error (no se fusiona en silencio).
  D2  destino = cada ``DestinationID``; ``lugar`` agrupa los ids con el mismo nombre (clave en minúsculas con guiones bajos).
  D3  ``VisitDate`` queda solo descriptiva (``fecha_visita``); la partición NO se hace aquí (es de JJ-3: no hay ``split``).
  D4  la ficha cita literal la fuente y lista las señales MEDIDAS de datos generados.
  D5  licencia: el campo formal de Kaggle y la contradicción con la descripción.
  D6  ``Name``, ``Email`` y ``ReviewText`` no pasan a ninguna salida.

Toda cifra de las salidas la calcula este módulo desde los CSV o el JSON; toda cita de la config se comprueba como subcadena
exacta de la descripción de la fuente. Las salidas son deterministas (sin fechas de ejecución ni rutas absolutas añadidas).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from src.comun.eda import escribir_ficha, tabla_calidad
from src.comun.results import save_json

COL_DESTINOS = ["DestinationID", "Name", "State", "Type", "Popularity", "BestTimeToVisit"]
COL_RESENAS = ["ReviewID", "DestinationID", "UserID", "Rating", "ReviewText"]
COL_HISTORIAL = ["HistoryID", "UserID", "DestinationID", "VisitDate", "ExperienceRating"]
COL_USUARIOS = ["UserID", "Name", "Email", "Preferences", "Gender", "NumberOfAdults", "NumberOfChildren"]
COLUMNAS_INTERACCIONES = ["usuario_id", "destino_id", "origen", "id_origen", "calificacion", "fecha_visita"]
COLUMNAS_DESTINOS = ["destino_id", "nombre", "lugar", "estado", "tipo", "mejor_epoca", "popularidad"]
RESENA, HISTORIAL = "resena", "historial"      # valores de la columna ``origen`` de interacciones
ORIGENES = (RESENA, HISTORIAL)
ROLES = ("destinos", "resenas", "historial", "usuarios")   # claves de ``raw`` y de ``cfg["entrada"]``
TIPO_FECHA = "texto con forma AAAA-MM-DD"
CLAVES_CITAS_OBLIGATORIAS = ("generado", "diversidad_de_genero", "uso", "licencia")
SEPARADOR_OPCIONES = ", "
PREFIJO_PREFERENCIA = "pref_"
FORMATO_FECHA = "%Y-%m-%d"
PATRON_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SIGNIFICADO_NO_DOCUMENTADO = "no documentado por la fuente"
NOTA_CORRESPONDENCIA = ("La correspondencia archivo ↔ componente de la descripción es inferencia nuestra: la fuente no "
                        "nombra los archivos ni las columnas.")
MOTIVO_PRIVACIDAD = ("Privacidad (D6): identifica a la persona; no pasa a data/processed/ ni a results/. Se describe "
                     "solo con conteos.")
MAX_EN_MENSAJE = 10  # ids o pares que se listan como máximo dentro de un mensaje de error

# Columna cruda → nombre procesado; ``None`` = excluida (D6).
MAPA_DESTINOS = {"DestinationID": "destinos.destino_id", "Name": "destinos.nombre", "State": "destinos.estado",
                 "Type": "destinos.tipo", "Popularity": "destinos.popularidad", "BestTimeToVisit": "destinos.mejor_epoca"}
MAPA_RESENAS = {"ReviewID": "interacciones.id_origen", "DestinationID": "interacciones.destino_id",
                "UserID": "interacciones.usuario_id", "Rating": "interacciones.calificacion", "ReviewText": None}
MAPA_HISTORIAL = {"HistoryID": "interacciones.id_origen", "UserID": "interacciones.usuario_id",
                  "DestinationID": "interacciones.destino_id", "VisitDate": "interacciones.fecha_visita",
                  "ExperienceRating": "interacciones.calificacion"}
MAPA_USUARIOS = {"UserID": "usuarios.usuario_id", "Name": None, "Email": None, "Preferences": "usuarios.preferencias",
                 "Gender": "usuarios.genero", "NumberOfAdults": "usuarios.n_adultos",
                 "NumberOfChildren": "usuarios.n_ninos"}


# --------------------------------------------------------------------------- utilidades
def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _clave_texto(texto) -> str:
    """Minúsculas ASCII con guiones bajos: «Taj Mahal» → ``taj_mahal``."""
    s = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^0-9a-z]+", "_", s).strip("_")


def clave_lugar(nombre) -> str:
    clave = _clave_texto(nombre)
    if not clave:
        raise ValueError(f"el nombre {nombre!r} no produce una clave de lugar")
    return clave


def _lista(valores) -> list:
    return [v.item() if isinstance(v, np.generic) else v for v in valores]


def _recortar(valores: list) -> str:
    extra = f" … (+{len(valores) - MAX_EN_MENSAJE})" if len(valores) > MAX_EN_MENSAJE else ""
    return f"{valores[:MAX_EN_MENSAJE]}{extra}"


def periodo_minimo(valores, ids, k_max: int) -> int | None:
    """Menor k ≤ ``k_max`` tal que ``valores`` es función exacta de ``ids mod k`` (cada clase de residuo tiene un solo valor);
    ``None`` si no hay. Con k mayor o igual al número de filas el resultado es trivial; aquí k_max ≪ filas."""
    v = pd.Series(list(valores)).reset_index(drop=True)
    i = np.asarray(list(ids))
    for k in range(1, k_max + 1):
        if int(v.groupby(i % k).nunique().max()) == 1:
            return k
    return None


def chi2_y_v(tabla) -> dict:
    """χ² de independencia (sin corrección de continuidad), grados de libertad, p (cola derecha) y V de Cramér de una tabla
    de contingencia de conteos. Con menos de 2 filas o 2 columnas no hay asociación definida (valores ``None``)."""
    t = np.asarray(tabla, dtype=float)
    r, c = t.shape
    n = float(t.sum())
    gl = (r - 1) * (c - 1)
    if min(r, c) < 2 or n == 0:
        return {"chi2": None, "gl": gl, "p": None, "v_de_cramer": None}
    esperado = np.outer(t.sum(axis=1), t.sum(axis=0)) / n
    ok = esperado > 0
    chi2 = float((((t - esperado) ** 2)[ok] / esperado[ok]).sum())
    return {"chi2": chi2, "gl": gl, "p": float(stats.chi2.sf(chi2, gl)),
            "v_de_cramer": float(np.sqrt(chi2 / (n * (min(r, c) - 1))))}


# --------------------------------------------------------------------------- entrada: hashes, CSV y metadatos
def verificar_archivos(ent: dict, esperados: dict) -> dict[str, str]:
    """SHA-256 de los 4 CSV y del .zip. Error si falta un archivo o un hash no coincide con la config (no se escribe nada)."""
    nombres = [ent[k] for k in ("destinos", "resenas", "historial", "usuarios", "zip")]
    carpeta = Path(ent["carpeta"])
    faltan = [n for n in nombres if not (carpeta / n).is_file()]
    if faltan:
        raise FileNotFoundError(f"Faltan en {carpeta}: {faltan}. Descárgalos de Kaggle (ver data/fuentes.md §M3).")
    sin_hash = [n for n in nombres if n not in esperados]
    if sin_hash:
        raise ValueError(f"sha256_esperado no tiene el hash de {sin_hash}")
    hashes = {n: sha256(carpeta / n) for n in nombres}
    distintos = [f"{n}: esperado {esperados[n]}, obtenido {hashes[n]}" for n in nombres if hashes[n] != esperados[n]]
    if distintos:
        raise ValueError("SHA-256 distinto del esperado en: " + "; ".join(distintos))
    return hashes


def leer_csv(ruta: Path, columnas: list[str]) -> pd.DataFrame:
    """Lee un CSV de la fuente y devuelve su DataFrame. Error si las columnas no son exactamente ``columnas`` (nombres y
    orden), si no tiene filas o si tiene valores faltantes (las tablas procesadas no imputan nada)."""
    nombre = Path(ruta).name
    df = pd.read_csv(ruta)
    if list(df.columns) != columnas:
        raise ValueError(f"{nombre}: se esperaban las columnas {columnas}; hay {list(df.columns)}")
    if df.empty:
        raise ValueError(f"{nombre}: no tiene filas de datos; se esperaba al menos una")
    if df.isna().any().any():
        raise ValueError(f"{nombre}: hay valores faltantes; las tablas procesadas no imputan nada, corrige o excluye esas filas")
    return df


def leer_metadatos(ruta: Path) -> dict:
    """Del JSON de respuestas crudas de la API de Kaggle: descripción, licencia formal, fecha de la versión 1 y archivos."""
    respuestas = json.loads(Path(ruta).read_text(encoding="utf-8"))["respuestas"]
    cuerpos = [r.get("cuerpo") for r in respuestas]

    def primero(extraer, que):
        for cuerpo in cuerpos:
            try:
                valor = extraer(cuerpo)
            except (KeyError, TypeError, IndexError):
                continue
            if valor:
                return valor
        raise ValueError(f"{ruta}: no se encontró {que} en las respuestas de la API")

    return {
        "descripcion": primero(lambda c: c["info"]["description"], "info.description"),
        "licencias": primero(lambda c: [x["name"] for x in c["info"]["licenses"]], "info.licenses[].name"),
        "fecha_creacion": primero(lambda c: c["versions"][0]["creationDate"], "versions[0].creationDate"),
        "archivos": primero(lambda c: c["datasetFiles"], "datasetFiles"),
    }


def columnas_documentadas(meta: dict) -> int:
    """Número de columnas que la fuente documenta en ``datasetFiles[].columns`` (hoy 0: la lista viene vacía)."""
    return sum(len(f.get("columns") or []) for f in meta["archivos"])


def verificar_citas(cfg: dict, meta: dict) -> None:
    """Cada cita y cada fragmento de componente de la config debe ser subcadena exacta de la descripción; la fecha de la
    versión debe coincidir con el JSON; la fuente no debe documentar columnas (si lo hiciera, el diccionario sería falso)."""
    desc = meta["descripcion"]
    citas = cfg["citas_literales"]
    faltan = [k for k in CLAVES_CITAS_OBLIGATORIAS if k not in citas]
    if faltan:
        raise ValueError(f"citas_literales: faltan las claves obligatorias {faltan}")
    for clave, fragmento in citas.items():
        if fragmento not in desc:
            raise ValueError(f"citas_literales.{clave}: no es subcadena exacta de la descripción de la fuente: {fragmento!r}")
    ent = cfg["entrada"]
    for archivo in (ent["destinos"], ent["resenas"], ent["historial"], ent["usuarios"]):
        fragmento = cfg["componentes"].get(archivo)
        if fragmento is None:
            raise ValueError(f"componentes: falta el fragmento de {archivo}")
        if fragmento not in desc:
            raise ValueError(f"componentes.{archivo}: no es subcadena exacta de la descripción: {fragmento!r}")
    fecha = str(cfg["fuente"]["fecha_creacion_version"])
    if fecha != meta["fecha_creacion"]:
        raise ValueError(f"fuente.fecha_creacion_version ({fecha}) no coincide con versions[0].creationDate del JSON "
                         f"({meta['fecha_creacion']})")
    documentadas = columnas_documentadas(meta)
    if documentadas:
        raise ValueError(f"datasetFiles[].columns ya no está vacío ({documentadas} columnas documentadas): la fuente cambió; "
                         "actualiza el diccionario antes de seguir")


# --------------------------------------------------------------------------- tablas procesadas
def _enteros(s: pd.Series, nombre: str) -> pd.Series:
    if not (s == s.round()).all():
        raise ValueError(f"{nombre}: se esperaban enteros")
    return s.astype("int64")


def construir_destinos(raw: pd.DataFrame) -> pd.DataFrame:
    """D2: una fila por ``DestinationID``; ``lugar`` = clave del nombre. Error si un nombre tiene más de una combinación
    (estado, tipo, mejor_epoca) o si dos nombres distintos dan la misma clave."""
    d = pd.DataFrame({"destino_id": _enteros(raw["DestinationID"], "DestinationID"), "nombre": raw["Name"].astype(str),
                      "estado": raw["State"].astype(str), "tipo": raw["Type"].astype(str),
                      "mejor_epoca": raw["BestTimeToVisit"].astype(str),
                      "popularidad": raw["Popularity"].astype("float64")})
    if d["destino_id"].duplicated().any():
        raise ValueError("DestinationID repetido en la tabla de destinos")
    n_comb = d.groupby("nombre")[["estado", "tipo", "mejor_epoca"]].nunique()
    malos = _lista(n_comb[(n_comb > 1).any(axis=1)].index)
    if malos:
        raise ValueError(f"nombre(s) de destino con más de una combinación (estado, tipo, mejor_epoca): {_recortar(malos)}")
    d["lugar"] = d["nombre"].map(clave_lugar)
    nombres_por_lugar = d.groupby("lugar")["nombre"].nunique()
    repetidos = _lista(nombres_por_lugar[nombres_por_lugar > 1].index)
    if repetidos:
        raise ValueError(f"la clave de lugar {_recortar(repetidos)} sale de más de un nombre de destino")
    return d[COLUMNAS_DESTINOS].sort_values("destino_id", kind="stable").reset_index(drop=True)


def separar_opciones(texto: str) -> list[str]:
    """«Historical, Beaches» → ['Beaches', 'Historical'] (sin espacios sobrantes, sin repetidas, orden alfabético)."""
    return sorted({p.strip() for p in str(texto).split(",") if p.strip()})


def construir_usuarios(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Usuarios sin ``Name`` ni ``Email`` (D6): ``preferencias`` normalizada y una columna booleana por opción medida."""
    opciones_por_usuario = raw["Preferences"].map(separar_opciones)
    opciones = sorted({o for lista in opciones_por_usuario for o in lista})
    columnas = {o: PREFIJO_PREFERENCIA + _clave_texto(o) for o in opciones}
    if len(set(columnas.values())) != len(columnas):
        raise ValueError(f"dos opciones de Preferences dan el mismo nombre de columna: {columnas}")
    u = pd.DataFrame({"usuario_id": _enteros(raw["UserID"], "UserID"),
                      "preferencias": opciones_por_usuario.map(SEPARADOR_OPCIONES.join)})
    if u["usuario_id"].duplicated().any():
        raise ValueError("UserID repetido en la tabla de usuarios")
    for o in sorted(opciones, key=lambda x: columnas[x]):
        u[columnas[o]] = opciones_por_usuario.map(lambda lista, o=o: o in lista).astype(bool)
    u["genero"] = raw["Gender"].astype(str)
    u["n_adultos"] = _enteros(raw["NumberOfAdults"], "NumberOfAdults")
    u["n_ninos"] = _enteros(raw["NumberOfChildren"], "NumberOfChildren")
    return u.sort_values("usuario_id", kind="stable").reset_index(drop=True), opciones


def construir_interacciones(res: pd.DataFrame, hist: pd.DataFrame, usuarios: pd.DataFrame,
                            destinos: pd.DataFrame) -> pd.DataFrame:
    """D1: unión de reseñas e historial. Error si un id no existe en las maestras o si un par (usuario, destino) se repite
    (dentro de un archivo o entre los dos); no se fusiona en silencio."""
    vacia = pd.Series(pd.NaT, index=res.index, dtype="datetime64[ns]")
    de_res = pd.DataFrame({"usuario_id": _enteros(res["UserID"], "UserID"),
                           "destino_id": _enteros(res["DestinationID"], "DestinationID"), "origen": RESENA,
                           "id_origen": _enteros(res["ReviewID"], "ReviewID"),
                           "calificacion": _enteros(res["Rating"], "Rating"), "fecha_visita": vacia})
    de_hist = pd.DataFrame({"usuario_id": _enteros(hist["UserID"], "UserID"),
                            "destino_id": _enteros(hist["DestinationID"], "DestinationID"), "origen": HISTORIAL,
                            "id_origen": _enteros(hist["HistoryID"], "HistoryID"),
                            "calificacion": _enteros(hist["ExperienceRating"], "ExperienceRating"),
                            "fecha_visita": pd.to_datetime(hist["VisitDate"], format=FORMATO_FECHA).astype("datetime64[ns]")})
    inter = pd.concat([de_res, de_hist], ignore_index=True)
    sin_usuario = _lista(sorted(set(inter["usuario_id"]) - set(usuarios["usuario_id"])))
    if sin_usuario:
        raise ValueError(f"usuario_id sin fila en la tabla maestra de usuarios: {_recortar(sin_usuario)}")
    sin_destino = _lista(sorted(set(inter["destino_id"]) - set(destinos["destino_id"])))
    if sin_destino:
        raise ValueError(f"destino_id sin fila en la tabla maestra de destinos: {_recortar(sin_destino)}")
    rep = inter[inter.duplicated(["usuario_id", "destino_id"], keep=False)]
    if len(rep):
        pares = sorted(map(tuple, rep[["usuario_id", "destino_id"]].drop_duplicates().to_numpy().tolist()))
        raise ValueError(f"pares (usuario_id, destino_id) repetidos, {len(pares)}: {_recortar(pares)}")
    return inter[COLUMNAS_INTERACCIONES].sort_values(["usuario_id", "destino_id"], kind="stable").reset_index(drop=True)


# --------------------------------------------------------------------------- medidas de la ficha
def escala(s: pd.Series) -> dict:
    """Escala medida de una calificación: mínimo, máximo, valores distintos y frecuencia de cada uno (claves en texto)."""
    valores = sorted(s.unique())
    return {"minimo": int(s.min()), "maximo": int(s.max()), "valores": [int(v) for v in valores],
            "frecuencias": {str(int(v)): int((s == v).sum()) for v in valores}}


def densidad(n: int, usuarios: int, destinos: int, usuarios_que_aparecen: int, destinos_que_aparecen: int) -> dict:
    """Interacciones sobre (a) usuarios × destinos de las maestras y (b) usuarios × destinos que aparecen."""
    maestras, aparecen = usuarios * destinos, usuarios_que_aparecen * destinos_que_aparecen
    return {"interacciones": n, "denominador_maestras": maestras, "maestras": n / maestras if maestras else None,
            "denominador_los_que_aparecen": aparecen, "los_que_aparecen": n / aparecen if aparecen else None}


def usuarios_por_numero(inter: pd.DataFrame, ids_maestros: pd.Series, tope: int) -> dict:
    """Usuarios maestros con 0, 1, …, tope-1 y ``tope``+ interacciones (los que no aparecen cuentan como 0)."""
    n = inter.groupby("usuario_id").size().reindex(ids_maestros, fill_value=0)
    salida = {str(k): int((n == k).sum()) for k in range(tope)}
    salida[f"{tope}+"] = int((n >= tope).sum())
    return salida


def clasificar_tipo(s: pd.Series) -> str:
    """Tipo medido de una columna; es la única clasificación y su nombre es el mismo en la ficha y en el diccionario:
    «booleano», «entero», «decimal», «texto con forma AAAA-MM-DD» (todos los valores) o «texto»."""
    if pd.api.types.is_bool_dtype(s):
        return "booleano"
    if pd.api.types.is_integer_dtype(s):
        return "entero"
    if pd.api.types.is_float_dtype(s):
        return "decimal"
    if s.astype(str).map(lambda x: bool(PATRON_FECHA.match(x))).all():
        return TIPO_FECHA
    return "texto"


def describir_contenido(df: pd.DataFrame, columnas: list[str]) -> dict:
    """Por columna de contenido: su tipo (``clasificar_tipo``) y, si es decimal, mínimo, máximo y valores distintos; si no,
    su número de categorías."""
    out = {}
    for c in columnas:
        s = df[c]
        tipo = clasificar_tipo(s)
        if tipo == "decimal":
            out[c] = {"tipo": tipo, "minimo": float(s.min()), "maximo": float(s.max()),
                      "n_valores_distintos": int(s.nunique())}
        else:
            out[c] = {"tipo": tipo, "n_categorias": int(s.nunique())}
    return out


def _publicacion(meta: dict) -> dt.date:
    """Fecha (sin hora) de la versión 1 del conjunto en Kaggle, de ``versions[0].creationDate``."""
    return dt.datetime.fromisoformat(meta["fecha_creacion"].replace("Z", "+00:00")).date()


def senales(raw: dict[str, pd.DataFrame], destinos: pd.DataFrame, meta: dict, fic: dict, asoc: dict) -> dict:
    """Señales de datos generados, todas medidas aquí desde los CSV y el JSON (ver el bloque ``real_o_sintetico``)."""
    kmax = int(fic["k_max_periodicidad"])
    dest, res, hist, usr = raw["destinos"], raw["resenas"], raw["historial"], raw["usuarios"]
    publicacion = _publicacion(meta)
    fechas = pd.to_datetime(hist["VisitDate"], format=FORMATO_FECHA).dt.date
    correo_es_nombre = (usr["Email"].str.contains("@", regex=False)
                        & (usr["Email"].str.split("@").str[0] == usr["Name"].str.lower()))
    por_lugar = destinos.groupby("lugar").size()
    return {
        "destinos": {"ids": int(len(destinos)), "lugares": int(len(por_lugar)),
                     "ids_por_lugar": {str(k): int(v) for k, v in sorted(por_lugar.items())}},
        "resenas": {"filas": int(len(res)), "textos_distintos": int(res["ReviewText"].nunique()),
                    "conteos_por_texto": sorted((int(n) for n in res["ReviewText"].value_counts()), reverse=True),
                    "asociacion_con_el_lugar_del_destino": asoc},
        "visit_date": {"filas": int(len(hist)), "valores_distintos": sorted(map(str, hist["VisitDate"].unique())),
                       "fecha_publicacion": publicacion.isoformat(),
                       "filas_posteriores_a_la_publicacion": int((fechas > publicacion).sum())},
        "usuarios": {"ids": int(len(usr)), "nombres_distintos": int(usr["Name"].nunique()),
                     "correos_nombre_en_minusculas_mas_dominio": int(correo_es_nombre.sum()),
                     "combinaciones_de_preferencias": int(usr["Preferences"].map(
                         lambda t: SEPARADOR_OPCIONES.join(separar_opciones(t))).nunique())},
        "periodicidad_con_el_id": {
            "k_max_buscado": kmax,
            "nombre_de_destino": periodo_minimo(dest["Name"], dest["DestinationID"], kmax),
            "review_text": periodo_minimo(res["ReviewText"], res["ReviewID"], kmax),
            "visit_date": periodo_minimo(hist["VisitDate"], hist["HistoryID"], kmax),
            "preferences": periodo_minimo(usr["Preferences"], usr["UserID"], kmax)},
    }


def asociacion_texto_lugar(res: pd.DataFrame, destinos: pd.DataFrame) -> dict:
    """χ² y V de Cramér entre ``ReviewText`` y el lugar del destino reseñado (no se guarda ni se lista ningún texto)."""
    lugar = res["DestinationID"].map(destinos.set_index("destino_id")["lugar"])
    return chi2_y_v(pd.crosstab(res["ReviewText"], lugar).to_numpy())


def texto_periodicidad(k: int | None, columna_id: str) -> str:
    """Fragmento de frase sobre la periodicidad medida: ``""`` si no hay (k es None), «, constante» si k = 1 (la columna no
    cambia) o «, función exacta de <id> mod k»."""
    if k is None:
        return ""
    return ", constante" if k == 1 else f", función exacta de {columna_id} mod {k}"


# --------------------------------------------------------------------------- inconsistencias, licencia y frases
def _inc_tipo_buscado(tipos: list[str], desc: str, palabra: str) -> dict:
    """El tipo que cita la descripción de la fuente frente a los valores medidos de ``Type``."""
    menciona = palabra.lower() in desc.lower()
    ninguno = not any(palabra.lower() in t.lower() for t in tipos)
    return {"id": "tipo_buscado_ausente", "se_presenta": menciona and ninguno,
            "descripcion": (f"La descripción {'menciona' if menciona else 'no menciona'} «{palabra}»; "
                            f"{'ningún valor' if ninguno else 'algún valor'} de Type lo contiene."),
            "medido": {"descripcion_menciona_el_tipo": menciona, "tipo_buscado": palabra, "tipos_medidos": tipos,
                       "ningun_tipo_lo_contiene": ninguno}}


def _inc_ids_vs_lugares(dest: dict, k: int | None) -> dict:
    """Cuántos ``DestinationID`` hay frente a cuántos lugares distintos."""
    return {"id": "ids_vs_lugares", "se_presenta": dest["lugares"] < dest["ids"],
            "descripcion": (f"{dest['ids']} DestinationID corresponden a {dest['lugares']} lugares; los ids de un mismo "
                            "lugar comparten nombre, estado, tipo y temporada (comprobado al construir destinos)."),
            "medido": {"ids": dest["ids"], "lugares": dest["lugares"], "ids_por_lugar": dest["ids_por_lugar"],
                       "k_minimo_destinationid_nombre": k}}


def _inc_visit_date(vd: dict, k: int | None) -> dict:
    """``VisitDate``: valores distintos, periodicidad con ``HistoryID`` y filas posteriores a la publicación."""
    post = vd["filas_posteriores_a_la_publicacion"]
    return {"id": "visitdate_periodica_y_posterior", "se_presenta": (k is not None and k > 1) or post > 0,
            "descripcion": (f"VisitDate tiene {len(vd['valores_distintos'])} valores distintos"
                            + texto_periodicidad(k, "HistoryID")
                            + f"; {post} de {vd['filas']} filas son posteriores a la publicación del conjunto "
                              f"({vd['fecha_publicacion']})."),
            "medido": {"filas": vd["filas"], "valores_distintos": vd["valores_distintos"], "k_minimo_historyid": k,
                       "fecha_publicacion": vd["fecha_publicacion"], "filas_posteriores_a_la_publicacion": post}}


def _inc_review_text(rt: dict, k: int | None) -> dict:
    """``ReviewText``: textos distintos, conteos, periodicidad con ``ReviewID`` y asociación con el lugar reseñado."""
    asoc = rt["asociacion_con_el_lugar_del_destino"]
    asociacion = (f"; su asociación con el lugar del destino reseñado es V de Cramér = {asoc['v_de_cramer']:.3f} "
                  f"(χ² p = {asoc['p']:.3f})." if asoc["v_de_cramer"] is not None else ".")
    return {"id": "reviewtext_plantilla", "se_presenta": rt["textos_distintos"] < rt["filas"],
            "descripcion": (f"ReviewText toma {rt['textos_distintos']} valores en {rt['filas']} reseñas"
                            + texto_periodicidad(k, "ReviewID") + asociacion),
            "medido": {"filas": rt["filas"], "textos_distintos": rt["textos_distintos"],
                       "conteos_por_texto": rt["conteos_por_texto"], "k_minimo_reviewid": k,
                       "asociacion_con_el_lugar_del_destino": asoc}}


def _inc_vocabularios(opciones: list[str], tipos: list[str]) -> dict:
    """Opciones de ``Preferences`` frente a valores de ``Type`` (diferencia de conjuntos)."""
    a, b = set(opciones), set(tipos)
    return {"id": "vocabularios_preferencias_vs_type", "se_presenta": a != b,
            "descripcion": descripcion_vocabularios(opciones, tipos),
            "medido": {"opciones_de_preferencias": opciones, "valores_de_type": tipos,
                       "solo_en_preferencias": sorted(a - b), "solo_en_type": sorted(b - a), "en_ambos": sorted(a & b)}}


def _inc_licencias(meta: dict, cfg: dict) -> dict:
    """Licencia formal de Kaggle frente a la sección «License» de la descripción (y la sección «Usage»)."""
    citas, formales = cfg["citas_literales"], meta["licencias"]
    en_license = formal_en_license(meta, cfg)
    return {"id": "licencias_contradictorias", "se_presenta": not en_license,
            "descripcion": (f"El campo formal de licencia de Kaggle ({', '.join(formales)}) "
                            f"{'aparece' if en_license else 'no aparece'} en la sección «License» de la descripción; "
                            "las citas literales de «License» y «Usage» están en `medido`."),
            "medido": {"campo_formal": formales, "formal_aparece_en_license": en_license, "license": citas["licencia"],
                       "usage": citas["uso"]}}


def inconsistencias(destinos: pd.DataFrame, opciones: list[str], meta: dict, cfg: dict, sen: dict) -> list[dict]:
    """Lista de las 6 inconsistencias de la fuente: cada una la arma su función ``_inc_*`` con ``medido`` (cifras) y
    ``se_presenta`` (lo que concluye la medición)."""
    per = sen["periodicidad_con_el_id"]
    return [_inc_tipo_buscado(sorted(destinos["tipo"].unique()), meta["descripcion"], str(cfg["ficha"]["tipo_mencionado_sin_datos"])),
            _inc_ids_vs_lugares(sen["destinos"], per["nombre_de_destino"]),
            _inc_visit_date(sen["visit_date"], per["visit_date"]),
            _inc_review_text(sen["resenas"], per["review_text"]),
            _inc_vocabularios(opciones, sorted(destinos["tipo"].unique())),
            _inc_licencias(meta, cfg)]


def descripcion_vocabularios(opciones: list[str], tipos: list[str]) -> str:
    """Frase derivada de la diferencia medida entre las opciones de Preferences y los valores de Type."""
    solo_pref, solo_tipo = sorted(set(opciones) - set(tipos)), sorted(set(tipos) - set(opciones))
    if not solo_pref and not solo_tipo:
        return f"Las {len(opciones)} opciones de Preferences coinciden con los valores de Type."
    comunes = len(set(opciones) & set(tipos))
    return (f"{comunes} de {len(opciones)} opciones de Preferences coinciden con valores de Type; solo en Preferences: "
            f"{', '.join(solo_pref) or 'ninguna'}; solo en Type: {', '.join(solo_tipo) or 'ninguno'}. Cruzarlos exige un "
            "emparejamiento que es supuesto nuestro, no de la fuente.")


def formal_en_license(meta: dict, cfg: dict) -> bool:
    """¿El nombre de la licencia formal de Kaggle aparece (como palabra) en la sección «License» de la descripción?"""
    return any(re.search(rf"\b{re.escape(f)}\b", cfg["citas_literales"]["licencia"]) for f in meta["licencias"])


def texto_contradiccion(meta: dict, cfg: dict, en_license: bool) -> str:
    """Texto de ``licencia.contradiccion``: solo lo leído del JSON (campo formal, «License», «Usage») y el resultado de
    ``formal_en_license``; ninguna interpretación normativa."""
    citas = cfg["citas_literales"]
    formal = ", ".join(meta["licencias"])
    partes = [f"Campo formal de licencia de Kaggle: «{formal}». Sección «License» de la descripción: «{citas['licencia']}». "
              f"Sección «Usage»: «{citas['uso']}»."]
    partes.append("El campo formal aparece en la sección «License»." if en_license else
                  "El campo formal no aparece en la sección «License»: las declaraciones son distintas.")
    return " ".join(partes)


def palabra_en_la_fuente(cfg: dict, meta: dict) -> bool:
    """¿La palabra de ``ficha.palabra_sintetico`` aparece (sin distinguir mayúsculas) en la descripción o en los nombres de
    archivo de la fuente?"""
    palabra = str(cfg["ficha"]["palabra_sintetico"]).lower()
    nombres = [str(f.get("name", "")) for f in meta["archivos"]]
    return palabra in meta["descripcion"].lower() or any(palabra in n.lower() for n in nombres)


# --------------------------------------------------------------------------- ficha, calidad, diccionario
def texto_periodo(cfg: dict, raw: dict[str, pd.DataFrame], sen: dict) -> str:
    """Texto de ``ficha.periodo``: columnas con forma de fecha medidas y lo medido de ``VisitDate``."""
    ent = cfg["entrada"]
    vd, per = sen["visit_date"], sen["periodicidad_con_el_id"]
    columnas = [f"{ent[rol]} ({c})" for rol in ROLES for c in raw[rol].columns if clasificar_tipo(raw[rol][c]) == TIPO_FECHA]
    return (f"Columnas con forma de fecha (AAAA-MM-DD): {', '.join(columnas) or 'ninguna'}. VisitDate tiene "
            f"{len(vd['valores_distintos'])} valores distintos ({', '.join(vd['valores_distintos'])})"
            + texto_periodicidad(per["visit_date"], "HistoryID")
            + f"; {vd['filas_posteriores_a_la_publicacion']} de {vd['filas']} filas son posteriores a la publicación del "
              f"conjunto ({vd['fecha_publicacion']}). Interpretación (D3): no es un periodo observado; solo descriptiva.")


def construir_ficha(cfg: dict, raw: dict[str, pd.DataFrame], hashes: dict[str, str], destinos: pd.DataFrame,
                    usuarios: pd.DataFrame, inter: pd.DataFrame, meta: dict, sen: dict) -> dict:
    """Contenido de ``ficha.json``: las 10 claves de la plantilla común (núcleo §5.12) más ``real_o_sintetico`` y
    ``licencia``; los conteos propios de M3 van bajo ``conteos``."""
    fte, fic, ent = cfg["fuente"], cfg["ficha"], cfg["entrada"]
    tope = int(fic["tope_usuarios_por_interacciones"])
    partes = {**{o: inter[inter["origen"] == o] for o in ORIGENES}, "union": inter}
    u_tot, d_tot = len(usuarios), len(destinos)
    u_ap = {k: int(v["usuario_id"].nunique()) for k, v in partes.items()}
    d_ap = {k: int(v["destino_id"].nunique()) for k, v in partes.items()}
    ids = usuarios["usuario_id"]
    return {
        "fuente": f"{fte['nombre']} ({fte['autor']}, Kaggle {fte['ref']})",
        "cita": " ".join(str(fte["cita"]).split()),
        "url": fte["url"],
        "fecha_descarga": str(fte["fecha_descarga"]),
        "sha256": hashes,
        "unidad_de_observacion": ("Par (usuario, destino) con una interacción implícita: una reseña (Reviews) o una visita "
                                  "registrada (UserHistory); la calificación es un atributo, no el objetivo (D1)."),
        "n_registros": int(len(inter)),
        "n_variables": int(sum(raw[rol].shape[1] for rol in ROLES)),
        "periodo": texto_periodo(cfg, raw, sen),
        "conteos": {
            "usuarios_maestra": int(u_tot), "destinos_maestra": int(d_tot), "lugares": sen["destinos"]["lugares"],
            "variables_por_archivo": {ent[rol]: int(raw[rol].shape[1]) for rol in ROLES},
            "interacciones": {k: int(len(v)) for k, v in partes.items()},
            "usuarios_que_aparecen": u_ap, "destinos_que_aparecen": d_ap,
            "escala_calificacion": {k: escala(v["calificacion"]) for k, v in partes.items()},
            "densidad": {k: densidad(len(v), u_tot, d_tot, u_ap[k], d_ap[k]) for k, v in partes.items()},
            "usuarios_por_numero_de_interacciones": {k: usuarios_por_numero(v, ids, tope) for k, v in partes.items()},
            "variables_de_contenido": {
                "usuarios": describir_contenido(usuarios, [c for c in usuarios.columns if c != "usuario_id"]),
                "destinos": describir_contenido(destinos, [c for c in destinos.columns if c != "destino_id"])},
        },
        "real_o_sintetico": {
            "citas_literales": dict(cfg["citas_literales"]),
            "palabra_synthetic_en_la_fuente": palabra_en_la_fuente(cfg, meta),
            "senales_medidas": sen,
            "conclusion": " ".join(str(cfg["conclusion_real_o_sintetico"]).split()),
        },
        "licencia": {
            "campo_formal": meta["licencias"],
            "en_la_descripcion": {"license": cfg["citas_literales"]["licencia"], "usage": cfg["citas_literales"]["uso"]},
            "contradiccion": texto_contradiccion(meta, cfg, formal_en_license(meta, cfg)),
        },
    }


def tabla_de_calidad(tablas: list[tuple[str, pd.DataFrame, list[str]]]) -> pd.DataFrame:
    """Por tabla procesada: ``tabla, filas, duplicados_clave`` + columnas de ``tabla_calidad`` (mismo formato que M1)."""
    partes = [tabla_calidad(df).assign(tabla=nombre, filas=len(df), duplicados_clave=int(df.duplicated(clave).sum()))
              for nombre, df, clave in tablas]
    cal = pd.concat(partes, ignore_index=True)
    primeras = ["tabla", "filas", "duplicados_clave"]
    return cal.reindex(columns=[*primeras, *[c for c in cal.columns if c not in primeras]])


def construir_diccionario(cfg: dict, raw: dict[str, pd.DataFrame], opciones: list[str], meta: dict, sen: dict, asoc: dict,
                          incons: list[dict]) -> dict:
    """Contenido de ``diccionario.json``: una entrada por columna de los 4 CSV (nombre procesado o ``None`` si se excluye,
    tipo medido, significado «no documentado por la fuente», fragmento del componente y motivo de exclusión) y las
    inconsistencias calculadas."""
    ent = cfg["entrada"]
    mapas = {"destinos": MAPA_DESTINOS, "resenas": MAPA_RESENAS, "historial": MAPA_HISTORIAL, "usuarios": MAPA_USUARIOS}
    usr, usuarios_sen, rt = raw["usuarios"], sen["usuarios"], sen["resenas"]
    v = asoc["v_de_cramer"]
    motivos = {
        ("usuarios", "Name"): (f"{MOTIVO_PRIVACIDAD} {usuarios_sen['nombres_distintos']} nombres distintos en "
                               f"{usuarios_sen['ids']} usuarios."),
        ("usuarios", "Email"): (f"{MOTIVO_PRIVACIDAD} {int(usr['Email'].nunique())} correos distintos en "
                                f"{usuarios_sen['ids']} usuarios; {usuarios_sen['correos_nombre_en_minusculas_mas_dominio']} "
                                "tienen la forma nombre en minúsculas + dominio."),
        ("resenas", "ReviewText"): (f"No pasa a lo procesado (D6): {rt['textos_distintos']} textos distintos en {rt['filas']} "
                                    f"reseñas (conteos por texto {rt['conteos_por_texto']}); asociación con el lugar del "
                                    "destino reseñado: V de "
                                    + (f"Cramér = {v:.3f}, χ² p = {asoc['p']:.3f}." if v is not None else "Cramér no definida.")),
    }
    derivadas = {("destinos", "Name"): ["destinos.lugar"],
                 ("usuarios", "Preferences"): [f"usuarios.{PREFIJO_PREFERENCIA}{_clave_texto(o)}" for o in opciones]}
    variables = []
    for rol in ROLES:
        for col, procesado in mapas[rol].items():
            fila = {"archivo": ent[rol], "columna_original": col, "nombre_procesado": procesado,
                    "tipo": clasificar_tipo(raw[rol][col]), "significado": SIGNIFICADO_NO_DOCUMENTADO,
                    "descripcion_del_archivo_en_la_fuente": " ".join(str(cfg["componentes"][ent[rol]]).split()),
                    "nota_correspondencia": NOTA_CORRESPONDENCIA}
            if (rol, col) in derivadas:
                fila["columnas_derivadas"] = derivadas[(rol, col)]
            if procesado is None:
                fila["excluida_motivo"] = motivos[(rol, col)]
            variables.append(fila)
    n_doc = columnas_documentadas(meta)
    return {
        "fuente_del_diccionario": (
            f"Se revisaron datasetFiles[].columns (columns) e info.description de {Path(ent['metadatos_fuente']).as_posix()}: "
            f"la fuente documenta {n_doc} columnas ({len(meta['archivos'])} archivos listados); solo describe cada "
            "componente en la descripción narrativa."),
        "columnas_documentadas_por_la_fuente": n_doc,
        "variables": variables,
        "inconsistencias": incons,
    }


# --------------------------------------------------------------------------- escritura
def _escribir_parquet(df: pd.DataFrame, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    df.to_parquet(tmp, index=False)
    tmp.replace(ruta)


def _escribir_csv(df: pd.DataFrame, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    df.to_csv(tmp, index=False, encoding="utf-8", lineterminator="\n")
    tmp.replace(ruta)


def main(cfg: dict) -> int:
    ent, sal = cfg["entrada"], cfg["salida"]
    # 1) Todo se lee y se valida antes de escribir: si algo falla, no queda ninguna salida a medias.
    hashes = verificar_archivos(ent, cfg["sha256_esperado"])
    meta = leer_metadatos(Path(ent["metadatos_fuente"]))
    verificar_citas(cfg, meta)
    carpeta = Path(ent["carpeta"])
    columnas = {"destinos": COL_DESTINOS, "resenas": COL_RESENAS, "historial": COL_HISTORIAL, "usuarios": COL_USUARIOS}
    raw = {rol: leer_csv(carpeta / ent[rol], columnas[rol]) for rol in ROLES}
    destinos = construir_destinos(raw["destinos"])
    usuarios, opciones = construir_usuarios(raw["usuarios"])
    inter = construir_interacciones(raw["resenas"], raw["historial"], usuarios, destinos)

    asoc = asociacion_texto_lugar(raw["resenas"], destinos)
    sen = senales(raw, destinos, meta, cfg["ficha"], asoc)
    incons = inconsistencias(destinos, opciones, meta, cfg, sen)
    ficha = construir_ficha(cfg, raw, hashes, destinos, usuarios, inter, meta, sen)
    calidad = tabla_de_calidad([("destinos", destinos, ["destino_id"]), ("usuarios", usuarios, ["usuario_id"]),
                                ("interacciones", inter, ["usuario_id", "destino_id"])])
    diccionario = construir_diccionario(cfg, raw, opciones, meta, sen, asoc, incons)

    if ficha["real_o_sintetico"]["palabra_synthetic_en_la_fuente"]:
        raise ValueError(f"La fuente usa la palabra «{cfg['ficha']['palabra_sintetico']}» (en la descripción o en los nombres "
                         "de archivo): revisa conclusion_real_o_sintetico en la config, que afirma que no la usa, antes de "
                         "volver a correr")

    # 2) Escritura.
    salida = Path(sal["carpeta"])
    eda = Path(sal["eda"])
    _escribir_parquet(destinos, salida / sal["destinos"])
    _escribir_parquet(usuarios, salida / sal["usuarios"])
    _escribir_parquet(inter, salida / sal["interacciones"])
    escribir_ficha(eda / "ficha.json", ficha)
    _escribir_csv(calidad, eda / "calidad.csv")
    save_json(eda / "diccionario.json", diccionario)
    _imprimir(ficha, [salida / sal[k] for k in ("destinos", "usuarios", "interacciones")]
              + [eda / "ficha.json", eda / "calidad.csv", eda / "diccionario.json"])
    return 0


def _imprimir(ficha: dict, archivos: list[Path]) -> None:
    c = ficha["conteos"]
    print(f"Usuarios: {c['usuarios_maestra']} · destinos: {c['destinos_maestra']} · lugares: {c['lugares']}")
    print("Interacciones: " + " · ".join(f"{k} {v}" for k, v in c["interacciones"].items()))
    d = c["densidad"]["union"]
    print(f"Densidad de la unión: {d['maestras']:.6f} (maestras) · "
          + (f"{d['los_que_aparecen']:.6f}" if d["los_que_aparecen"] is not None else "-") + " (los que aparecen)")
    for f in archivos:
        print(f"  {f.as_posix()} ({f.stat().st_size} B)")
