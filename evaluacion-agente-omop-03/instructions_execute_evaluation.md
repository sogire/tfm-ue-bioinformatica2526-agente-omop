# Guía de Ejecución y Evaluación del Agente OMOP

Este documento describe el flujo oficial y unificado de evaluación para contrastar las consultas generadas por el agente de Text-to-SQL OMOP (`omop_03_concepts_and_sql`) frente al estándar de oro (*Gold Standard*) definido en los archivos YAML de evaluación bajo [evaluation/gold_standard/](evaluation/gold_standard/), generados según las directrices de [instructions_build_gold_standard.md](instructions_build_gold_standard.md).

> [!NOTE]
> **Modularidad y Nuevas Fuentes de Consultas SQL:**
> La fuente actual de consultas evaluada es `querylibrary` (procedente de OHDSI Query Library). El sistema está diseñado para ser multifuente: en el futuro se pueden incorporar nuevas fuentes de consultas SQL (ej. `mimic`, `custom_ehr`, etc.) bajo `evaluation/sources/<nueva_fuente>/`, generando su estándar de oro en `evaluation/gold_standard/<nueva_fuente>/` y almacenando los resultados de ejecución en `evaluation/results/<nueva_fuente>/`. Todos los scripts admiten el parámetro `--source` (por defecto `querylibrary`).

Todas las evaluaciones y análisis posteriores se ejecutan de forma estandarizada y automatizada mediante los scripts organizados bajo el directorio **[`scripts/execute_evaluation/`](scripts/execute_evaluation/)**.

---

## Estructura de Directorios y Scripts

* **Estándar de Oro (Casos de prueba):** `evaluation/gold_standard/<fuente>/` (por defecto: `evaluation/gold_standard/querylibrary/` con 201 casos).
* **Resultados de Evaluación:** `evaluation/results/<fuente>/` (por defecto: `evaluation/results/querylibrary/` con archivos YAML por caso).
* **Sesiones Forenses:** `evaluation/results/<fuente>/sessions/` (archivos JSON con la traza completa de la sesión ADK).
* **Informes Consolidados:** `evaluation/results/<fuente>_analisis_yyyymmddhhmm.xlsx`.
* **Dependencias de Entorno:** [`requirements.txt`](requirements.txt) (`pip install -r requirements.txt`).
* **Scripts de Ejecución y Análisis:** `scripts/execute_evaluation/`
  * [`run_query_evaluation.py`](scripts/execute_evaluation/run_query_evaluation.py): Ejecutor de pruebas contra el agente en Google Cloud Run. Admite `--source <fuente>` (por defecto `querylibrary`).
  * [`analyze_evaluation_results.py`](scripts/execute_evaluation/analyze_evaluation_results.py): Consolidador y analizador de resultados en Excel (`evaluation/results/<fuente>_analisis_yyyymmddhhmm.xlsx`). Admite `--source <fuente>` (o `all`).

---

## 1. Ejecución Automatizada con `run_query_evaluation.py`

El script [`run_query_evaluation.py`](scripts/execute_evaluation/run_query_evaluation.py) gestiona de forma transparente el ciclo de vida de la sesión con el agente en Google Cloud Run, el envío de la instrucción (*prompt*) con directiva SQL, la resolución de diálogos de desambiguación terminológica en dos turnos, la extracción de la consulta SQL y el cálculo de métricas tanto cuantitativas como cualitativas.

### A. Evaluación de un Caso Individual
Para evaluar un único caso de prueba (por ejemplo, `C01` de `querylibrary`):
```bash
# Fuente por defecto (querylibrary)
python3 scripts/execute_evaluation/run_query_evaluation.py C01

# Indicando la fuente explícitamente
python3 scripts/execute_evaluation/run_query_evaluation.py --source querylibrary C01
```

### B. Evaluación por Rangos (Lotes / Batch)
Para evaluar un bloque secuencial de casos de forma continua (por ejemplo, del caso `C01` al `C10`):
```bash
python3 scripts/execute_evaluation/run_query_evaluation.py --range C01-C10
```

### C. Evaluación de una Lista Específica de Casos
Para evaluar casos concretos no correlativos:
```bash
python3 scripts/execute_evaluation/run_query_evaluation.py C01 C03 C06 C10
```

### D. Evaluación Completa de la Colección
Para evaluar automáticamente la totalidad de los archivos YAML presentes en `evaluation/gold_standard/<fuente>/`:
```bash
python3 scripts/execute_evaluation/run_query_evaluation.py --all
```

> [!TIP]
> **Parámetros Opcionales:**
> * `--source <nombre>`, `-s`: Identificador o tipo de fuente de consultas (por defecto: `querylibrary`).
> * `--delay <segundos>`, `-d`: Configura el tiempo de espera en segundos entre consultas consecutivas al agente (por defecto `1.5` s).
> * `--base-dir <ruta>`: Especifica manualmente la raíz del proyecto si se ejecuta desde otro directorio de trabajo (por defecto: autodetectado).
> * `-h` / `--help`: Muestra la ayuda y opciones disponibles en la línea de comandos.

---

## 2. Métricas de Evaluación y Formato de Salida

Cada evaluación analiza el comportamiento del agente mediante dos métricas cuantitativas, una tercera métrica cualitativa en bloque multilínea y un indicador técnico de conectividad:

### Métrica 1: `validez_sintactica_y_estructural` (0.00 a 1.00)
* **Naturaleza:** Métrica cuantitativa continua en escala de `[0.00, 1.00]`.
* **Objetivo:** Evaluar conjuntamente la ejecutabilidad y validez técnica de la consulta SQL y su fidelidad lógica y estructural respecto a la consulta de referencia estándar (`sql_base_gold_standard`).
* **Cálculo y Ponderación por Criterios:**
  $$\text{validez\_sintactica\_y\_estructural} = \text{Criterio 1.1} + \text{Criterio 1.2}$$
  * **Criterio 1.1 — Ejecución y Validez Técnica (máximo 0.10 puntos):**
    * **0.10:** Si la consulta generada es sintácticamente correcta, estructurada para Google BigQuery OMOP CDM 5.4 y validada exitosamente por la herramienta interna del agente (`validate_omop_sql`) o emite una sentencia `SELECT` ejecutable.
    * **0.00:** Si la consulta presenta errores de sintaxis, no compila contra el catálogo o si el agente no llegó a formular SQL ejecutable.
  * **Criterio 1.2 — Grado de Similitud SQL frente a Gold Standard (máximo 0.90 puntos):**
    * **Obtención:** Esta puntuación es evaluada por **Gemini como modelo juez (*LLM-as-a-judge*)** comparando la consulta SQL del agente frente a `sql_base_gold_standard`.
    * **Criterios de similitud:** Lógica de negocio, tablas del modelo OMOP empleadas, condiciones de filtrado (`WHERE`), uniones (`JOIN`), agrupaciones (`GROUP BY`) y adecuación a la intención clínica.
    * **Flexibilidad en proyección:** No hace falta que los alias o nombres de campos en la cláusula `SELECT` se denominen idénticamente, siempre que la consulta responda a la misma necesidad clínica y seleccione la información pertinente.
    * **0.00:** Si el agente no generó consulta SQL ejecutable (Criterio 1.1 = 0.00) o si la consulta generada es completamente errónea respecto a la necesidad clínica.

### Métrica 2: `precision_terminologica_vocabulario` (0.00 a 1.00)
* **Naturaleza:** Métrica cuantitativa continua.
* **Objetivo:** Evaluar la fidelidad en la identificación de conceptos frente a los definidos en `concept_ids_gold_standard`.
* **Cálculo:** Índice de Jaccard entre los conceptos utilizados por el agente ($C_{\text{agente}}$) y los requeridos por el estándar ($C_{\text{gold}}$):
  $$\text{Jaccard} = \frac{|C_{\text{agente}} \cap C_{\text{gold}}|}{|C_{\text{agente}} \cup C_{\text{gold}}|}$$
  *(En consultas de carácter exploratorio donde el estándar no fija conceptos numéricos obligatorios, el valor asignado es 1.00).*

### Métrica 3: `evaluacion_cualitativa` (Bloque Multilínea YAML)
* **Naturaleza:** Métrica cualitativa descriptiva formateada en bloques de texto multilínea (`|-`).
* **Objetivo:** Proporcionar un análisis semántico, clínico y técnico estructurado del comportamiento del modelo ante el caso evaluado.
* **Contenido evaluado:**
  * **Resolución conversacional y ejecución técnica:** Indica si el agente generó la consulta directamente en un único turno o si necesitó turnos adicionales de diálogo o desambiguación, así como la puntuación técnica obtenida (Criterio 1.1: 0.10 pts).
  * **Similitud SQL evaluada por Gemini:** Resumen técnico y clínico emitido por Gemini justificando la puntuación otorgada sobre 0.90 puntos (Criterio 1.2).
  * **Tablas y modelo OMOP:** Documenta las tablas CDM involucradas en la consulta generada (ej. `concept`, `concept_relationship`, `condition_occurrence`, `measurement`, `specimen`).
  * **Alineación clínica y terminológica:** Explica la pertinencia de los conceptos mapeados respecto a la intención médica original.
  * **Diagnóstico de abstención o fallo:** En los casos donde no se formula SQL (ej. falta de mapeo cruzado SNOMED-MedDRA o diferenciación entre organismo patógeno y evento clínico), documenta la justificación médica emitida por el agente.

### Indicador Técnico: `check_conexion`
* **Objetivo:** Registrar el estado de la comunicación HTTP/SSE con el servicio Cloud Run del agente.
* **Valores:**
  * `true`: Conexión establecida con éxito y sesión ADK ejecutada correctamente.
  * `Fallo de conexión: <detalle>`: En caso de tiempo de espera agotado (*timeout*), error HTTP (500, 503) o caída del servicio remoto.

---

### Formato del Archivo Resultante YAML
Cada caso evaluado genera su archivo correspondiente en [evaluation/results/<fuente>/](evaluation/results/querylibrary/) (por defecto: `evaluation/results/querylibrary/`) con formato multilínea limpio y validación sintáctica estricta:

```yaml
id_evaluacion: querylibrary_C03
session_id: "09c86a27-e43c-423c-a22f-1962a3eece7d"
session_file: "sessions/C03.json"
turnos_ejecutados: 1
sql_generada_agente: |-
  SELECT c1.concept_id AS source_concept_id,
         c1.concept_name AS source_concept_name,
         c1.vocabulary_id AS source_vocabulary_id,
         cr.relationship_id,
         r.relationship_name,
         c2.concept_id AS target_concept_id,
         c2.concept_name AS target_concept_name,
         c2.vocabulary_id AS target_vocabulary_id,
         c2.domain_id AS target_domain_id
  FROM `concept` AS c1
  JOIN `concept_relationship` AS cr ON c1.concept_id = cr.concept_id_1
  JOIN `relationship` AS r ON cr.relationship_id = r.relationship_id
  JOIN `concept` AS c2 ON cr.concept_id_2 = c2.concept_id
  WHERE c1.concept_id = 312327
  ORDER BY r.relationship_name,
           c2.concept_name;
concept_ids_identificados_agente:
- 312327
metricas_evaluacion:
  validez_sintactica_y_estructural: 0.75
  precision_terminologica_vocabulario: 1.0
  detalle_validez_sintactica:
    criterio_1_1_ejecucion: 0.10
    criterio_1_2_similitud_sql_gemini: 0.65
    justificacion_gemini: |-
      La consulta generada implementa adecuadamente la unión entre concept, concept_relationship y relationship para encontrar relaciones del concepto 312327, pero omite filtrar por c.invalid_reason IS NULL.
  metricas_por_turno:
    turno_1:
      validez_sintactica_y_estructural: 0.75
      precision_terminologica_vocabulario: 1.0
      question_improvement: ""
evaluacion_cualitativa: |-
  Consulta SQL ejecutable (0.10 pts) sobre tabla(s) concept, concept_relationship, relationship generada en el Turno 1 tras la confirmación de los conceptos iniciales ofrecidos por el agente.
  Similitud SQL evaluada por Gemini (0.65/0.90 pts): La consulta generada implementa adecuadamente la unión entre concept, concept_relationship y relationship para encontrar relaciones del concepto 312327, pero omite filtrar por c.invalid_reason IS NULL.
  Precisión terminológica óptima: identificó y utilizó todos los conceptos requeridos ([312327]).
check_conexion: true
```

> [!NOTE]
> **Estructura Multi-Turno y Métricas Detalladas:**
> * `session_id` / `session_file`: Identificador único y ruta relativa al volcado JSON de auditoría forense descargado directamente del punto de conexión (*endpoint*) de sesiones de Google ADK en Cloud Run (`/apps/{appName}/users/{userId}/sessions/{sessionId}`) y preservado en `evaluation/results/<fuente>/sessions/<caso>.json`.
> * `turnos_ejecutados`: Número de turnos requeridos por el agente (1 si la Validez Sintáctica y Estructural superó 0.80 en la primera ronda; 2 si la superó tras la primera retroalimentación; o 3 si requirió agotar los 3 turnos).
> * `metricas_por_turno`: Desglose granular que refleja la evolución métrica en cada turno (`turno_1`, `turno_2`, `turno_3`).
> * `question_improvement`: Contiene la instrucción (*prompt*) enriquecida utilizada en los turnos posteriores (Turnos 2 y 3) incorporando la `justificacion_gemini` del juez LLM del turno previo para orientar al agente hacia la consulta óptima. En `turno_1` queda en blanco (`""`).

---

## 3. Arquitectura y Funcionamiento Interno de `run_query_evaluation.py`

El script [`run_query_evaluation.py`](scripts/execute_evaluation/run_query_evaluation.py) encapsula las siguientes funciones especializadas:

1. **Gestión de Sesión remota con ADK / Cloud Run (`create_agent_session`, `send_message_sse`):**
   * Abre una nueva sesión (`POST /apps/{APP_NAME}/users/{USER_ID}/sessions/{SESSION_ID}`).
   * Envía la pregunta en lenguaje natural junto con la directiva explícita de requerimiento de consulta SQL para BigQuery OMOP 5.4 mediante Server-Sent Events (`POST .../run_sse`).
2. **Ciclo de Retroalimentación Multi-Turno Guiado por Juez LLM (`justificacion_gemini`):**
   * **Criterio de Parada Temprana:** Cuando la **Validez Sintáctica y Estructural** de un turno supere el `0.80` (`validez_sintactica_y_estructural > 0.80`), no es necesario ejecutar el siguiente turno y la evaluación concluye de forma exitosa en el turno actual.
   * **Turno 1 (Pregunta Clínica y Evaluación Inicial):** Envío de la pregunta original requiriendo directamente la formulación SQL ejecutable para BigQuery OMOP 5.4. Si el agente ofrece conceptos candidatos iniciales para validación, la confirmación inmediata de dichos conceptos por parte del evaluador forma parte integral del **Turno 1**. La respuesta obtenida (SQL generado o respuesta textual) es evaluada por el juez LLM Gemini (`judge_sql_similarity_with_gemini`), obteniendo la puntuación continua (`criterio_1_2_similitud_sql_gemini`) y la crítica detallada (`justificacion_gemini`). Si la Validez Sintáctica y Estructural supera el 0.80 (> 0.80), la interacción concluye con éxito en `turnos_ejecutados = 1` sin necesidad de ejecutar el siguiente turno.
   * **Turno 2 (Mejora Guiada por Juez LLM):** Si la Validez Sintáctica y Estructural del Turno 1 no supera el 0.80 (validez <= 0.80) o el agente no formuló SQL, el evaluador construye una instrucción enriquecida (`question_improvement`) inyectando íntegramente la retroalimentación técnica y clínica de `justificacion_gemini` del Turno 1 (indicando tablas, filtros `WHERE`, uniones `JOIN` y dominios que faltan). El agente procesa esta retroalimentación dentro de la misma sesión y genera una versión corregida, evaluada nuevamente por Gemini. Si en este turno la Validez Sintáctica y Estructural supera el 0.80 (> 0.80), concluye en `turnos_ejecutados = 2` sin necesidad de ejecutar el Turno 3.
   * **Turno 3 (Optimización Final Guiada por Juez LLM):** Si tras el Turno 2 la Validez Sintáctica y Estructural aún no supera el 0.80 (validez <= 0.80), el evaluador inyecta la nueva `justificacion_gemini` devuelta por el juez LLM en el Turno 2 en la instrucción de insistencia (`question_improvement`), requiriendo al agente resolver las observaciones señaladas y emitir la sentencia SQL SELECT definitiva y óptima para BigQuery OMOP CDM 5.4. El evaluador concluye en `turnos_ejecutados = 3` y consolida finalmente la consulta y métricas del mejor turno ejecutado.
3. **Extracción y Validación de SQL (`extract_sql_from_events`):**
   * Inspecciona las llamadas y respuestas a herramientas (`validate_omop_sql`, `search_omop_official_concepts`) en los eventos SSE.
   * Extrae la consulta final y el veredicto de validación en BigQuery.
4. **Cálculo de Métricas y Serialización Segura:**
   * Registra las métricas por cada turno ejecutado e incorpora el campo `question_improvement`.
   * Utiliza una clase personalizada `LiteralStr` con un representador PyYAML dedicado para asegurar que tanto el código SQL como el texto cualitativo se serialicen con el indicador multilínea literal `|-`, eliminando caracteres de escape redundantes.
5. **Auditoría Forense y Persistencia de Sesión ADK:**
   * Descarga automáticamente el estado completo de la sesión vía `GET /apps/{appName}/users/{userId}/sessions/{sessionId}` y lo guarda en `evaluation/results/<fuente>/sessions/<caso>.json`.
   * La sesión JSON contiene la traza forense completa: eventos, llamadas y respuestas a herramientas, razonamiento del modelo, consumo de tókenes (`usageMetadata`) y marcas temporales.
6. **Resiliencia ante Agotamiento y Falta de Respuesta (`request_with_retry`):**
   * Si el agente OMOP experimenta agotamiento de cuotas (HTTP 429 / `RESOURCE_EXHAUSTED` / límite de tasa), sobrecarga de servicio (HTTP 500/502/503/504) o interrupción de comunicaciones (*timeout*, fallo de conexión o respuesta SSE vacía), el evaluador captura el evento, imprime de forma inmediata y visible el `id_evaluacion` en curso para conocimiento del usuario y realiza una pausa preventiva de **2 minutos (120 segundos)** antes de reintentar la operación (hasta 5 reintentos).

---

## 4. Análisis y Consolidación en Excel (`analyze_evaluation_results.py`)

Como último paso del flujo de evaluación, y una vez que el usuario apruebe procesar y consolidar los resultados obtenidos en las ejecuciones contra el agente, se ejecuta el script [`analyze_evaluation_results.py`](scripts/execute_evaluation/analyze_evaluation_results.py).

### Propósito y Flujo de Datos
1. **Extracción de Casos de Prueba (`test`):** Lee recursivamente los archivos YAML bajo [evaluation/gold_standard/<fuente>/](evaluation/gold_standard/) y construye el DataFrame `test` con los campos:
   * `source`
   * `id_evaluacion`
   * `nivel_complejidad`
   * `domain_main`
   * `domain_others`
   * `pregunta_lenguaje_natural`
   * `sql_base_gold_standard`
2. **Extracción de Resultados del Agente (`result`):** Lee recursivamente los archivos YAML bajo [evaluation/results/<fuente>/](evaluation/results/) y construye el DataFrame `result` con los campos:
   * `id_evaluacion`
   * `session_id`
   * `check_conexion`
   * `turnos_ejecutados`
   * `validez_sintactica_y_estructural`
   * `criterio_1_1_ejecucion`
   * `criterio_1_2_similitud_sql_gemini`
   * `precision_terminologica_vocabulario`
   * `turno_1_validez_sintactica_y_estructural`
   * `turno_1_precision_terminologica_vocabulario`
   * `turno_1_question_improvement`
   * `turno_2_validez_sintactica_y_estructural`
   * `turno_2_precision_terminologica_vocabulario`
   * `turno_2_question_improvement`
   * `turno_3_validez_sintactica_y_estructural`
   * `turno_3_precision_terminologica_vocabulario`
   * `turno_3_question_improvement`
   * `evaluacion_cualitativa`
   * `evaluacion_llm_juez`
   * `sql_generada_agente`
3. **Cruce y Consolidación:** Realiza la combinación de ambos DataFrames cruzando por `id_evaluacion` y ordenando los casos de forma natural según su identificador. Incluye las 27 columnas ordenadas de forma lógica con `source` en primera posición:
   * Metadatos: `source`, `id_evaluacion`, `session_id`, `session_file`, `nivel_complejidad`, `domain_main`, `domain_others`, `pregunta_lenguaje_natural`
   * Ejecución y métricas globales: `check_conexion`, `turnos_ejecutados`, `validez_sintactica_y_estructural`, `criterio_1_1_ejecucion`, `criterio_1_2_similitud_sql_gemini`, `precision_terminologica_vocabulario`
   * Desglose por turnos: `turno_1_validez_sintactica_y_estructural`, `turno_1_precision_terminologica_vocabulario`, `turno_1_question_improvement`, `turno_2_validez_sintactica_y_estructural`, `turno_2_precision_terminologica_vocabulario`, `turno_2_question_improvement`, `turno_3_validez_sintactica_y_estructural`, `turno_3_precision_terminologica_vocabulario`, `turno_3_question_improvement`
   * Consultas y análisis: `evaluacion_cualitativa`, `evaluacion_llm_juez`, `sql_base_gold_standard`, `sql_generada_agente`.
4. **Exportación a Excel:** Genera un libro de cálculo `.xlsx` bajo el directorio `evaluation/results/` con diseño profesional, tipografía monoespaciada para las columnas SQL (`Consolas`), cabeceras estilizadas, ajuste de anchos y alineación multilínea:
   ```text
   evaluation/results/<fuente>_analisis_yyyymmddhhmm.xlsx
   ```
   donde `<fuente>` es la fuente evaluada (ej. `querylibrary`) y `yyyymmddhhmm` corresponde al año, mes, día, hora y minuto exactos del momento de la ejecución.

### Comando de Ejecución
```bash
# Fuente por defecto (querylibrary)
python3 scripts/execute_evaluation/analyze_evaluation_results.py

# Analizar una fuente concreta o todas ('all')
python3 scripts/execute_evaluation/analyze_evaluation_results.py --source querylibrary
python3 scripts/execute_evaluation/analyze_evaluation_results.py --source all
```

> [!TIP]
> **Parámetros Opcionales de Análisis:**
> * `--source <fuente>`, `-s`: Identificador de la fuente a analizar (por defecto: `querylibrary`, o `all` para todas las fuentes).
> * `--eval-dir <ruta>`, `-e`: Directorio base de archivos de prueba (por defecto: `evaluation/gold_standard/<fuente>`).
> * `--results-dir <ruta>`, `-r`: Directorio base de archivos de resultado (por defecto: `evaluation/results/<fuente>`).
> * `--output <nombre.xlsx>`, `-o`: Especificar un nombre o ruta personalizada para el archivo Excel (por defecto: `evaluation/results/<fuente>_analisis_yyyymmddhhmm.xlsx`).
> * `--base-dir <ruta>`, `-b`: Directorio raíz del proyecto (por defecto: autodetectado).

### Resumen Producido en Consola
Al ejecutarse, el script muestra una tabla agregada con el promedio de métricas agrupadas por `nivel_complejidad` y el desglose caso por caso:

```text
Resumen promedio por nivel de complejidad:
                  validez_sintactica_y_estructural  ... precision_terminologica_vocabulario
                                             count  ...                                mean
nivel_complejidad                                   ...                                    
baja                                             4  ...                                 1.0
compleja                                         2  ...                                 1.0
intermedia                                       4  ...                                 1.0

Detalle de filas consolidadas:
 • querylibrary_C01       | Complejidad: intermedia  | Dominio: concept                    | Sintaxis: 1.00 | Vocabulario: 1.00 | Conexión: True
 • querylibrary_C02       | Complejidad: baja        | Dominio: concept (+concept_synonym) | Sintaxis: 1.00 | Vocabulario: 1.00 | Conexión: True
 ...
```
