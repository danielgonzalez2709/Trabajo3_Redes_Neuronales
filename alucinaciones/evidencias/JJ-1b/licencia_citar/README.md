# Candidato (sin numerar): «las tres licencias piden citar la fuente»

- **Quién lo afirmó:** la sesión orquestadora (Claude Opus 5.5) en la fase A de JJ-1, al redactar
  `docs/investigacion/JJ-1_fuentes_m3.md` §3.2 en respuesta al prompt `alucinaciones/prompts/JJ-1a.md`. El implementador
  (Sonnet) de la fase B lo copió y lo amplió en la clave `fuente.lectura_licencia` de `configs/m3/datos.yaml`, en
  `results/data/m3/eda/ficha.json` (`licencia.contradiccion`) y en `data/fuentes.md` (prompt
  `alucinaciones/prompts/JJ-1b-implementador.md`; respuesta `../respuesta-implementador.md`, §4.1).
- **Texto original de la fase A (literal):** «Para este trabajo académico no comercial las tres permiten el uso, y todas
  coinciden en pedir que se cite la fuente.»
- **Texto del implementador (literal, `configs/m3/datos.yaml`, antes de corregir):** «Para este trabajo académico no comercial
  las tres declaraciones permiten el uso y todas piden citar la fuente».
- **Cómo se detectó:** el revisor-spec (R1, Sonnet) lo marcó como bloqueante B-1 (`../respuesta-revisor-spec-1.md`).
- **Evidencia:** `verificar.py` → `salida.txt`: en la respuesta cruda de Kaggle, solo la sección «Usage» contiene «cite»; la
  sección «License» («CC0: Public Domain - … can be used without restrictions.») no pide citar ni atribuir. Lo que exigen los
  textos oficiales de MIT y CC0 lo contrasta el cazador-alucinaciones (R3) con https://opensource.org/license/mit y
  https://creativecommons.org/publicdomain/zero/1.0/.
- **Corrección:** `JJ-1_fuentes_m3.md` §3.2 corregido por el orquestador; `lectura_licencia` eliminada y `data/fuentes.md`
  corregido por el implementador (ver `alucinaciones/prompts/JJ-1b-implementador-2.md`).
