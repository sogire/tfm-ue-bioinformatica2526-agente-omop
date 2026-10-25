> 🏠 **[README Principal](../README.md)** · 🌐 **Idioma / Language:** **Español** | [English](README.en.md)

# Marco de Evaluación Text-to-SQL OMOP CDM 5.4 (`tfm-eval`)

Marco de trabajo (*benchmark*) automatizado y modular para la generación de estándares de oro, ejecución de pruebas multiturno y análisis cuantitativo/cualitativo de agentes Text-to-SQL especializados en el modelo común de datos biomédicos **OMOP CDM 5.4** en **Google BigQuery** (`bio-med-480108.OMOP_54_A`).

El objetivo principal es contrastar de forma sistemática el desempeño del agente (`omop_03_concepts_and_sql`) desplegado en Google Cloud Run frente a especificaciones de consulta validadas clínicamente.

---

## 📁 Estructura del Repositorio

```text
evaluacion-agente-omop-03/
├── README.md                              # Este documento
├── requirements.txt                       # Dependencias requeridas del proyecto
├── instructions_build_gold_standard.md    # Especificación para generación del Gold Standard
├── instructions_execute_evaluation.md      # Guía oficial del flujo de ejecución y métricas
├── evaluation/
│   ├── sources/
│   │   └── querylibrary/                  # 201 consultas clínicas Markdown de la OHDSI Query Library
│   ├── gold_standard/
│   │   └── querylibrary/                  # 201 especificaciones de prueba en YAML estándar BigQuery
│   ├── results/
│   │   ├── querylibrary/                  # Evaluaciones individuales generadas por el agente (.yaml)
│   │   └── analisis_*.xlsx                # Informes consolidados en Excel con marca temporal
│   └── sessions/                          # Directorio de control y trazabilidad de sesiones
└── scripts/
    ├── build_gold_standard/
    │   ├── build_gold_standard.py         # Generador de YAML Gold Standard desde Markdown
    │   ├── validate_gold_standard.py      # Validador sintáctico, de esquema y prefijos BigQuery
    │   └── spanish_questions.py           # Diccionario clínico con 201 preguntas en español
    └── execute_evaluation/
        ├── run_query_evaluation.py        # Ejecutor de evaluación multi-turno contra Cloud Run
        └── analyze_evaluation_results.py  # Consolidador y exportador de métricas a Excel
```

---

## ⚙️ Requisitos e Instalación

Para ejecutar los scripts del repositorio, instale las dependencias de Python especificadas en [`requirements.txt`](requirements.txt):

```bash
pip install -r requirements.txt
```

### Bibliotecas Requeridas
* **`PyYAML`** (>= 6.0.1): Carga, parseo y serialización de archivos YAML con soporte de literales multilínea (`|-`).
* **`requests`** (>= 2.31.0): Gestión de sesiones HTTP y streaming Server-Sent Events (SSE) con el agente en Google Cloud Run.
* **`pandas`** (>= 2.0.0): Construcción de DataFrames, transformaciones tabulares y cruce analítico de resultados.
* **`openpyxl`** (>= 3.1.2): Motor de exportación a hojas de cálculo Excel (`.xlsx`) con soporte para bordes, tipografías monoespaciadas y ajuste dinámico de columnas.
* **`sqlparse`** (>= 0.5.0): Formateo, limpieza sintáctica e inspección de sentencias SQL OMOP CDM.

---

## 🚀 Flujos de Trabajo (Pipelines)

### 1. Construcción y Validación del Estándar de Oro (*Gold Standard*)

Traduce las consultas Markdown originales a archivos YAML estructurados para BigQuery, determinando el nivel de complejidad SQL (`baja`, `intermedia`, `compleja`), identificando dominios OMOP principales y secundarios, y asociando preguntas clínicas en español.

```bash
# Generar todo el benchmark de la fuente por defecto (querylibrary)
python3 scripts/build_gold_standard/build_gold_standard.py

# Generar solo una subcarpeta o dominio clínico específico
python3 scripts/build_gold_standard/build_gold_standard.py --subfolder condition

# Generar un caso individual
python3 scripts/build_gold_standard/build_gold_standard.py --id C01 --verbose

# Validar el 100% de los archivos generados (sintaxis YAML, esquema y prefijos BigQuery)
python3 scripts/build_gold_standard/validate_gold_standard.py
```

> Más detalles en [instructions_build_gold_standard.md](instructions_build_gold_standard.md).

---

### 2. Ejecución Automatizada de la Evaluación

Interactúa con el agente en Google Cloud Run a través de HTTP/SSE (*Server-Sent Events*), gestionando sesiones y desambiguación multiturno de conceptos clínicos (hasta 3 turnos).

```bash
# Evaluar un caso individual
python3 scripts/execute_evaluation/run_query_evaluation.py C01

# Evaluar un rango correlativo de casos
python3 scripts/execute_evaluation/run_query_evaluation.py --range C01-C10

# Evaluar una lista específica de casos
python3 scripts/execute_evaluation/run_query_evaluation.py C01 C03 C06 C10

# Evaluar la colección completa
python3 scripts/execute_evaluation/run_query_evaluation.py --all
```

#### Protocolo Multiturno Progresivo Guiado por Juez LLM:
* **Parada Temprana:** Cuando la Validez Sintáctica y Estructural de un turno supere el `0.80` (> 0.80), no es necesario ejecutar el siguiente turno y la evaluación concluye de forma exitosa en el turno en curso.
* **Turno 1:** Envío de la pregunta clínica con directiva de generación SQL para BigQuery OMOP 5.4. La respuesta generada es evaluada por Gemini (LLM juez); si la Validez Sintáctica y Estructural supera el 0.80 (> 0.80), concluye la prueba en 1 turno sin necesidad de turno adicional.
* **Turno 2:** Si la Validez no supera el 0.80 (validez <= 0.80) o no emitió SQL, el evaluador inyecta la crítica detallada (`justificacion_gemini`) en la instrucción (*prompt*, `question_improvement`) para orientar al agente hacia la corrección de tablas, uniones (*JOINs*) y filtros. Si en este turno la Validez supera el 0.80 (> 0.80), concluye en 2 turnos.
* **Turno 3:** Si tras el Turno 2 la Validez aún no supera el 0.80 (validez <= 0.80), se inyecta la nueva justificación de Gemini del Turno 2 para la optimización final del SQL. El evaluador consolida finalmente la consulta y métricas del mejor turno ejecutado.
* **Resiliencia y Reintento Automático:** Si el agente experimenta agotamiento de recursos o cuota (HTTP 429) o deja de responder (*timeout* o desconexión), el evaluador notifica el `id_evaluacion` en proceso y realiza una pausa preventiva de 2 minutos antes de reintentar automáticamente.

---

### 3. Análisis, Cruce y Consolidación en Excel

Cruza las especificaciones de prueba ([evaluation/gold_standard/](evaluation/gold_standard/)) con las respuestas del agente ([evaluation/results/](evaluation/results/)), generando un informe estructurado en Excel con 27 columnas y tablas resumen en consola.

```bash
# Analizar la fuente por defecto (querylibrary)
python3 scripts/execute_evaluation/analyze_evaluation_results.py

# Analizar todas las fuentes disponibles
python3 scripts/execute_evaluation/analyze_evaluation_results.py --source all
```

El archivo resultante se almacena en:
```text
evaluation/results/<fuente>_analisis_YYYYMMDDHHMM.xlsx
```
Incluye formateo tipográfico monoespaciado (`Consolas`) para las consultas SQL y cálculo de medias por nivel de complejidad y dominio.

> Más detalles en [instructions_execute_evaluation.md](instructions_execute_evaluation.md).

---

## 📊 Métricas de Evaluación

| Métrica | Tipo | Rango | Descripción |
| :--- | :---: | :---: | :--- |
| **`validez_sintactica_y_estructural`** | Cuantitativa | `0.00` - `1.00` | Evalúa conjuntamente la ejecutabilidad (Criterio 1.1: máx. 0.10 pts) y la similitud SQL frente a `sql_base_gold_standard` evaluada por Gemini como modelo juez (*LLM-as-a-judge*) (Criterio 1.2: máx. 0.90 pts). |
| **`precision_terminologica_vocabulario`** | Cuantitativa | `0.00` - `1.00` | Índice de Jaccard entre los `concept_ids` utilizados por el agente y los requeridos por el estándar de oro ($\frac{\|C_{\text{agente}} \cap C_{\text{gold}}\|}{\|C_{\text{agente}} \cup C_{\text{gold}}\|}$). |
| **`metricas_por_turno`** | Cuantitativa / Histórica | Turnos 1 a 3 | Evolución métrica en cada turno conversacional, registrando el texto exacto empleado para asistir al agente (`question_improvement`). |
| **`evaluacion_cualitativa`** | Cualitativa | Texto multilínea | Diagnóstico sobre turnos requeridos, puntos de ejecución (0.10), justificación de similitud SQL emitida por Gemini (0.90) y adecuación clínica. |
| **`check_conexion`** | Técnico | `true` / Error | Estado de conectividad HTTP/SSE y autenticación con el servicio en Google Cloud Run. |

---

## 🧩 Formato de los Archivos de Resultados (YAML)

Cada ejecución individual en `evaluation/results/<fuente>/<ID>.yaml` se guarda con bloques multilínea limpios (`|-`):

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

---

## 🔄 Extensibilidad Multifuente

El sistema está diseñado para incorporar fácilmente nuevas fuentes de consultas clínicas (por ejemplo, `mimic`, `custom_ehr`, etc.):
1. Colocar las consultas origen en `evaluation/sources/<nueva_fuente>/`.
2. Procesar con `--source <nueva_fuente>` en los scripts correspondientes.
3. El estándar de oro, los resultados y el análisis se gestionarán automáticamente bajo sus respectivos subdirectorios `<nueva_fuente>`.
