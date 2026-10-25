> 🏠 **[Main README](../README.en.md)** · 🌐 **Language / Idioma:** [Español](README.md) | **English**

# OMOP CDM 5.4 Text-to-SQL Evaluation Framework (`tfm-eval`)

Automated and modular benchmark framework for *Gold Standard* generation, multi-turn test execution, and quantitative/qualitative analysis of Text-to-SQL agents specialized in the **OMOP CDM 5.4** biomedical common data model on **Google BigQuery** (`bio-med-480108.OMOP_54_A`).

Its primary objective is to systematically evaluate the performance of the agent (`omop_03_concepts_and_sql`) deployed on Google Cloud Run against clinically validated query specifications.

---

## 📁 Repository Structure

```text
evaluacion-agente-omop-03/
├── README.md                                 # Spanish documentation
├── README.en.md                              # This document (English)
├── requirements.txt                          # Required project dependencies
├── instructions_build_gold_standard.md       # Gold Standard generation specification (ES)
├── instructions_build_gold_standard.en.md    # Gold Standard generation specification (EN)
├── instructions_execute_evaluation.md        # Official execution workflow and metrics guide (ES)
├── instructions_execute_evaluation.en.md     # Official execution workflow and metrics guide (EN)
├── evaluation/
│   ├── sources/
│   │   └── querylibrary/                     # 201 clinical Markdown queries from OHDSI Query Library
│   ├── gold_standard/
│   │   └── querylibrary/                     # 201 test specifications in standard BigQuery YAML
│   ├── results/
│   │   ├── querylibrary/                     # Individual agent evaluation outputs (.yaml)
│   │   └── analisis_*.xlsx                   # Consolidated timestamped Excel reports
│   └── sessions/                             # Session control and traceability directory
└── scripts/
    ├── build_gold_standard/
    │   ├── build_gold_standard.py            # Gold Standard YAML generator from Markdown
    │   ├── validate_gold_standard.py         # YAML syntax, schema, and BigQuery prefix validator
    │   └── spanish_questions.py              # Clinical dictionary with 201 questions in Spanish
    └── execute_evaluation/
        ├── run_query_evaluation.py           # Multi-turn evaluation runner against Cloud Run
        └── analyze_evaluation_results.py     # Metric consolidator and Excel exporter
```

---

## ⚙️ Requirements and Installation

To run the scripts in this repository, install the Python dependencies specified in [`requirements.txt`](requirements.txt):

```bash
pip install -r requirements.txt
```

### Required Libraries
* **`PyYAML`** (>= 6.0.1): Loading, parsing, and serializing YAML files with multi-line literal support (`|-`).
* **`requests`** (>= 2.31.0): HTTP session management and Server-Sent Events (SSE) streaming with the agent on Google Cloud Run.
* **`pandas`** (>= 2.0.0): DataFrame construction, tabular transformations, and analytical cross-referencing of results.
* **`openpyxl`** (>= 3.1.2): Excel spreadsheet (`.xlsx`) export engine supporting cell borders, monospaced fonts, and dynamic column sizing.
* **`sqlparse`** (>= 0.5.0): Formatting, syntactic cleanup, and inspection of OMOP CDM SQL statements.

---

## 🚀 Workflows (Pipelines)

### 1. Building and Validating the *Gold Standard*

Translates the original Markdown queries into structured YAML files for BigQuery, determining the SQL complexity level (`baja` [low], `intermedia` [intermediate], `compleja` [complex]), identifying primary and secondary OMOP domains, and pairing them with clinical questions in Spanish.

```bash
# Generate the full benchmark from the default source (querylibrary)
python3 scripts/build_gold_standard/build_gold_standard.py

# Generate only a specific subfolder or clinical domain
python3 scripts/build_gold_standard/build_gold_standard.py --subfolder condition

# Generate an individual case
python3 scripts/build_gold_standard/build_gold_standard.py --id C01 --verbose

# Validate 100% of the generated files (YAML syntax, schema, and BigQuery prefixes)
python3 scripts/build_gold_standard/validate_gold_standard.py
```

> More details in [instructions_build_gold_standard.en.md](instructions_build_gold_standard.en.md) ([Spanish version](instructions_build_gold_standard.md)).

---

### 2. Automated Evaluation Execution

Interacts with the agent on Google Cloud Run over HTTP/SSE (*Server-Sent Events*), managing sessions and multi-turn disambiguation of clinical concepts (up to 3 turns).

```bash
# Evaluate a single case
python3 scripts/execute_evaluation/run_query_evaluation.py C01

# Evaluate a sequential range of cases
python3 scripts/execute_evaluation/run_query_evaluation.py --range C01-C10

# Evaluate a specific list of cases
python3 scripts/execute_evaluation/run_query_evaluation.py C01 C03 C06 C10

# Evaluate the entire collection
python3 scripts/execute_evaluation/run_query_evaluation.py --all
```

#### Progressive Multi-Turn Protocol Guided by an LLM Judge:
* **Early Stopping:** Whenever the Syntactic and Structural Validity of a turn exceeds `0.80` (> 0.80), no subsequent turn is needed and the evaluation concludes successfully on the current turn.
* **Turn 1:** Submission of the clinical question with an explicit BigQuery OMOP 5.4 SQL generation directive. The generated response is evaluated by Gemini (LLM judge); if Syntactic and Structural Validity exceeds 0.80 (> 0.80), the test concludes in 1 turn without requiring additional turns.
* **Turn 2:** If Validity does not exceed 0.80 (validity <= 0.80) or no SQL was emitted, the evaluator injects the detailed critique (`justificacion_gemini`) into the follow-up prompt (`question_improvement`) to guide the agent toward correcting tables, *JOINs*, and filters. If Validity exceeds 0.80 (> 0.80) on this turn, the evaluation concludes in 2 turns.
* **Turn 3:** If Validity still does not exceed 0.80 (validity <= 0.80) after Turn 2, the new Gemini justification from Turn 2 is injected for final SQL optimization. The evaluator then consolidates the query and metrics from the best executed turn.
* **Resilience and Automatic Retry:** If the agent experiences resource or quota exhaustion (HTTP 429) or stops responding (*timeout* or disconnection), the evaluator logs the active `id_evaluacion` and performs a preventive 2-minute pause before automatically retrying.

---

### 3. Analysis, Cross-Referencing, and Consolidation in Excel

Cross-references the test specifications ([evaluation/gold_standard/](evaluation/gold_standard/)) with the agent's responses ([evaluation/results/](evaluation/results/)), generating a structured 27-column Excel report and summary tables in the console.

```bash
# Analyze the default source (querylibrary)
python3 scripts/execute_evaluation/analyze_evaluation_results.py

# Analyze all available sources
python3 scripts/execute_evaluation/analyze_evaluation_results.py --source all
```

The resulting file is saved at:
```text
evaluation/results/<source>_analisis_YYYYMMDDHHMM.xlsx
```
It includes monospaced typographic formatting (`Consolas`) for SQL queries and mean calculations grouped by complexity level and domain.

> More details in [instructions_execute_evaluation.en.md](instructions_execute_evaluation.en.md) ([Spanish version](instructions_execute_evaluation.md)).

---

## 📊 Evaluation Metrics

| Metric | Type | Range | Description |
| :--- | :---: | :---: | :--- |
| **`validez_sintactica_y_estructural`** | Quantitative | `0.00` - `1.00` | Jointly evaluates executability (Criterion 1.1: max. 0.10 pts) and SQL similarity against `sql_base_gold_standard` assessed by Gemini as an *LLM-as-a-judge* (Criterion 1.2: max. 0.90 pts). |
| **`precision_terminologica_vocabulario`** | Quantitative | `0.00` - `1.00` | Jaccard index between the `concept_ids` used by the agent and those required by the gold standard ($\frac{\|C_{\text{agent}} \cap C_{\text{gold}}\|}{\|C_{\text{agent}} \cup C_{\text{gold}}\|}$). |
| **`metricas_por_turno`** | Quantitative / Historical | Turns 1 to 3 | Metric progression across each conversational turn, recording the exact prompt text used to assist the agent (`question_improvement`). |
| **`evaluacion_cualitativa`** | Qualitative | Multi-line text | Diagnostic summary covering required turns, execution score (0.10), SQL similarity justification issued by Gemini (0.90), and clinical adequacy. |
| **`check_conexion`** | Technical | `true` / Error | HTTP/SSE connectivity and authentication status with the Google Cloud Run service. |

---

## 🧩 Results File Format (YAML)

Each individual execution in `evaluation/results/<source>/<ID>.yaml` is stored using clean multi-line literal blocks (`|-`):

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

## 🔄 Multi-Source Extensibility

The system is designed to seamlessly incorporate new clinical query sources (e.g., `mimic`, `custom_ehr`, etc.):
1. Place the source queries in `evaluation/sources/<new_source>/`.
2. Process them using `--source <new_source>` in the corresponding scripts.
3. The gold standard, results, and analysis will be automatically managed under their respective `<new_source>` subdirectories.

