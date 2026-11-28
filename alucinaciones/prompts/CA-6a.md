# Prompt CA-6a — investigador-fuentes (Sonnet) — 2026-11-27 — orquesta: Camila

Repo /Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales, rama dev/camila. Solo escribes el informe
`docs/investigacion/CA-6_costos_flota.md`; no toques ningún otro archivo, no hagas `git add`, `git commit` ni `git push`.

## Para qué
Pregunta de negocio 4 del Módulo 1 (enunciado literal en `docs/spec/SPEC.md`, Anexo, «Módulo 1 → Preguntas de negocio», punto 4):
«Para la próxima temporada alta del horizonte de prueba […] ¿cuántos vehículos y conductores adicionales se requieren en
comparación con una semana normal? ¿Recomendarían flota propia, arrendada o convenios con otras empresas?». Camila decidió
(27-nov) buscar fuentes de costos antes de recomendar. El modelo de flota es el de `src/m1_demanda/operacion.py` y los parámetros
en `configs/m1/operacion.yaml` (léelo: clases de vehículo BUS, BUSETA, MICROBUS…, rutas Bogotá–Cali, Bogotá–Sogamoso, Pasto–Ipiales,
y cómo se citan las normas ahí). Contexto normativo previo: `docs/investigacion/CA-2_normativa_operacion.md` y
`docs/investigacion/CA-2_verificacion.md`.

## Qué buscar (Colombia, transporte público terrestre automotor de pasajeros por carretera)
1. **Marco legal de las tres opciones**: ¿qué permite la norma vigente sobre (a) vehículos propios vs. vinculados, (b) arrendamiento
   o uso temporal de vehículos de otra empresa, (c) convenios de colaboración empresarial entre empresas habilitadas, y (d)
   servicios extraordinarios o refuerzos de temporada alta? Requisitos y restricciones (p. ej. autorización, misma modalidad,
   capacidad transportadora). Cita el artículo exacto del Decreto 1079 de 2015 u otra norma, desde la fuente oficial, con su vigencia.
2. **Costos**, solo si hay fuente oficial o institucional verificable (MinTransporte, Supertransporte, DANE, ANDI/Fasecolda u
   otra entidad; también licitaciones o tarifas publicadas por entidades públicas): costo operativo por vehículo-día o por km de
   bus intermunicipal, precio de compra de un bus/buseta/microbus, tarifa de alquiler de bus con conductor o sin él, costo de
   un convenio. Para cada cifra: valor, unidad, año, clase de vehículo, alcance y cita.
3. Si una cifra solo aparece en medios, blogs o anuncios comerciales, repórtala aparte como **no citable** y con su URL; no la
   presentes como dato.

## Reglas
- **Prohibido inventar** cifras, artículos, fechas o URL. Lo que no encuentres: `TODO(dato-faltante)` o `TODO(cita)` y dilo.
- Cada afirmación con cita APA 7, URL y fecha de consulta; para normas, el fragmento literal que la sostiene.
- Distingue lo verificado en la fuente primaria de lo que solo viste en un resumen o buscador.

## Entrega
El informe con: resumen (qué se encontró y qué no), tabla de marco legal, tabla de costos citables, tabla de cifras no citables,
lista de `TODO`, y una sección «Qué se puede concluir con esto» que diga qué comparación de costos es defendible y cuál no.
