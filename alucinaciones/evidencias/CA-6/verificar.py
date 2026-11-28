"""Verificación CA-6: busca cada fragmento literal citado en las copias de las fuentes primarias.

Uso: python -I verificar.py  (desde cualquier carpeta; las rutas son relativas a este archivo).
Imprime CONFIRMADA / NO ENCONTRADA por fragmento. Copias descargadas el 2026-11-27.
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def leer(nombre: str) -> str:
    texto = (AQUI / nombre).read_text(encoding="utf-8", errors="replace")
    return re.sub(r"\s+", " ", texto)


FUENTES = {
    "fp1079": "fp_decreto1079.txt",  # Función Pública, Decreto 1079/2015, versión al 21-sep-2025
    "fp1017": "fp_decreto1017_2025.txt",  # Función Pública, Decreto 1017/2025
    "do1017": "ramajudicial_decreto1017_2025.txt",  # Diario Oficial 53.250 (copia Rama Judicial)
    "sj1048": "sisjur_decreto1048_2026.txt",  # SISJUR Bogotá, Decreto 1048/2026
    "sjcomp": "sisjur_decreto1079_compilatorio.txt",  # SISJUR, compilatorio de modificaciones del 1079
    "r264": "res_264_2020_mintransporte.txt",  # Resolución 264/2020 MinTransporte (OCR de copia firmada)
    "l336": "senado_ley_336_1996.txt",  # Secretaría del Senado, Ley 336/1996
    "bol": "ictip_bol_IIItrim2026.txt",  # DANE, boletín ICTIP III-2026
    "met": "ictip_met_v2.txt",  # DANE, DSO-ICTIP-MET-001 v2
    "dane": "dane_encuesta_costos_vinculados.txt",  # DANE, página de la encuesta
}

FRAGMENTOS = [
    # (id, fuente, fragmento literal)
    ("L-1a", "fp1079", "Las empresas deberán acreditar como mínimo el 3% de capacidad transportadora mínima de su propiedad y/o de sus socios, que en ningún caso podrá ser inferior a un (1) vehículo, incluyéndose dentro de este porcentaje los vehículos adquiridos bajo arrendamiento financiero."),
    ("L-1b", "fp1079", "Los vehículos que sean de propiedad de la empresa habilitada, se entenderán vinculados a la misma sin que para ello sea necesario la celebración del contrato de vinculación."),
    ("L-2a", "fp1079", "sólo podrán hacerlo con equipos registrados en el servicio público."),
    ("L-2b", "fp1079", "La vinculación de un vehículo a una empresa de transporte público es la incorporación de éste al parque automotor de dicha empresa. Se formaliza con la celebración del respectivo contrato entre el propietario del vehículo y la empresa y se oficializa con la expedición de la tarjeta de operación por parte del Ministerio de Transporte."),
    ("L-2c", "fp1079", "El Ministerio de Transporte expedirá la tarjeta de operación únicamente a los vehículos legalmente vinculados a las empresas de transporte público debidamente habilitadas, de acuerdo con la capacidad transportadora fijada a cada una de ellas."),
    ("L-3", "fp1079", "La capacidad transportadora máxima no podrá ser superior a la capacidad mínima incrementada en un veinte por ciento (20%). El parque automotor no podrá estar por fuera de los límites de la capacidad transportadora mínima y máxima fijada a la empresa."),
    ("L-4", "fp1079", "Los convenios se efectuarán exclusivamente sobre servicios previamente autorizados a alguna de las empresas involucradas, quien para todos los efectos continuará con la responsabilidad acerca de su adecuada prestación."),
    ("L-5", "fp1079", "PARÁGRAFO . En épocas de temporada alta, las empresas de transporte de pasajeros por carretera podrán celebrar contratos con empresas de servicio especial para prestar el servicio exclusivamente en las rutas autorizadas. (Decreto 171 de 2001, artículo 42)."),
    ("L-6", "fp1079", "Ocasional (o Expreso). Cuando el Ministerio de Transporte autoriza a las empresas habilitadas en esta modalidad la realización de un viaje dentro o fuera de sus rutas autorizadas, para transportar un grupo homogéneo de pasajeros"),
    ("L-7", "fp1079", "El acuerdo, que bajo ninguna circunstancia implica incremento de las capacidades transportadoras de las empresas, debe garantizar que la demanda será suficiente Y debidamente atendida"),
    ("6.3.5-ant", "fp1079", "en períodos de alta demanda que defina el Ministerio de Transporte"),
    ("cab-1079", "fp1079", "(Adicionado y modificado por el Decreto 1017 de 2025)"),
    ("cab-1079b", "fp1079", "ÚLTIMA FECHA DE ACTUALIZACIÓN: 21 DE SEPTIEMBRE DE 2025"),
    ("1017-obj", "fp1017", "Por el cual se modifican, adicionan y derogan unos artículos del Capítulo 7 del Título 1 de la Parte 2 del Libro 2 del Decreto 1079 de 2015"),
    ("1017-DO", "do1017", "Edición 53.250"),
    ("1048-obj", "sj1048", "Por el cual se modifican y derogan unos artículos del Capítulo 6 del Título 1 de la Parte 2 del Libro 2 del Decreto 1079 de 2015"),
    ("1048-635", "sj1048", "podrán suplir la necesidad de parque automotor en periodos de alta demanda definidos por el Ministerio de Transporte"),
    ("1048-r264", "sj1048", "de acuerdo con la Resolución 264 de 2020 del Ministerio de Transporte, o la norma que la modifique o sustituya."),
    ("1048-681", "sj1048", "su término de duración, que no podrá ser superior a dos (2) años"),
    ("1048-681b", "sj1048", "No podrá pactarse en el contrato de vinculación de flota las renovaciones automáticas del mismo."),
    ("r264-art8", "r264", "Artículo 8. Periodos de alta demanda para la definición de contratos."),
    ("r264-dic", "r264", "Del 10 de diciembre al 15 de enero del año siguiente."),
    ("r264-conv", "r264", "tendrán un término de vigencia no superior a dos (2) años"),
    ("l336-22", "l336", "el Reglamento determinara la forma de vinculación de los equipos a las empresas, señalando el porcentaje de su propiedad y las formas alternas de cumplir y acreditar el mismo."),
    ("C-1", "bol", "Combustibles 31,00 -0,06 -0,02 0,77 0,22 Insumos 8,78 0,68 0,06 -0,06 0,00 Costos fijos 32,99 -0,77 -0,28 0,46 0,16 Peajes y uso de terminales 20,39"),
    ("C-1b", "bol", "6,84 0,46 0,03 0,36 0,02 vehículo Total 100,00 -0,13 -0,13 0,45 0,45"),
    ("C-1fecha", "bol", "Boletín técnico Bogotá 22 de octubre de 2026"),
    ("C-2a", "bol", "el ICTIP obtuvo una variación trimestral de -0,13%"),
    ("C-2b", "bol", "el ICTIP evidenció una variación año corrido de 7,77%"),
    ("C-2c", "bol", "Mano de obra conductor(es) y ayudante(s) 22,11 4,72"),
    ("C-2per", "bol", "En el tercer trimestre (julio-septiembre) de 2026 en comparación al último trimestre de 2025 (octubre-diciembre)"),
    ("C-2cf", "bol", "Costos fijos 32,99 14,07 4,83"),
    ("base", "bol", "La base del índice es el cuarto trimestre de 2015"),
    ("C-3", "met", "la ausencia de un mercado establecido de alquiler de vehículos de pasajeros, repercutió en que la respuesta de los encuestados refiriera valores que incluían otros costos ya contabilizados previamente"),
    ("C-3b", "met", "¿En cuánto alquilaría su vehículo mensualmente?"),
    ("C-4", "met", "Excluye los costos y los gastos asumidos por las empresas de transporte, debido a que no es posible asignar un costo (gasto) específico al vehículo."),
    ("C-5", "met", "para este caso se calcula como el 20% del valor de compra promedio del vehículo"),
    ("CF", "met", "costos fijos (parqueaderos, seguros, costo del vehículo, impuestos y mano de obra)"),
    ("act", "met", "únicamente puede ser actualizada a partir de la aplicación y procesamiento de información de una encuesta básica"),
    ("ICTC", "dane", "Índice de Costos de Transporte Intermunicipal de Pasajeros (ICTC)"),
]

# Fragmentos que NO deben aparecer (afirmaciones de ausencia)
AUSENCIAS = [
    ("1017-no-cap4", "fp1017", "2.2.1.4."),
    ("1017-no-cap4-DO", "do1017", "2.2.1.4."),
]


def main() -> int:
    textos = {k: leer(v) for k, v in FUENTES.items()}
    fallos = 0
    for ident, fuente, frag in FRAGMENTOS:
        ok = re.sub(r"\s+", " ", frag) in textos[fuente]
        fallos += not ok
        print(f"{'CONFIRMADA   ' if ok else 'NO ENCONTRADA'} {ident:12s} [{FUENTES[fuente]}]")
    for ident, fuente, frag in AUSENCIAS:
        ok = frag not in textos[fuente]
        fallos += not ok
        print(f"{'AUSENTE (ok) ' if ok else 'PRESENTE     '} {ident:12s} [{FUENTES[fuente]}] «{frag}»")
    # Menciones literales de «temporada alta» en el Decreto 1079 (versión FP)
    n = len(re.findall(r"temporada alta", textos["fp1079"], flags=re.I))
    print(f"menciones de «temporada alta» en Decreto 1079 (FP): {n}")
    # Decretos 2025-2026 en el compilatorio SISJUR y si su epígrafe toca el Capítulo 4
    print("decretos 2025-2026 en el compilatorio SISJUR:",
          sorted(set(re.findall(r"Decreto \d+ de 202[56]", textos["sjcomp"]))))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
