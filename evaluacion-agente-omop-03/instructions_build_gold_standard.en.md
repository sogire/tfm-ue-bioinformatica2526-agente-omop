> 🏠 **[Main README](../README.en.md)** › **[Evaluation Framework](README.en.md)** · 🌐 **Language / Idioma:** [Español](instructions_build_gold_standard.md) | **English**

# Instructions: Generating *Gold Standard* Evaluation YAML Files (OMOP CDM 5.4)

## Objective
Generate standardized YAML configuration files for the *Gold Standard* of the natural language query evaluation benchmark over an OMOP CDM 5.4 database on Google BigQuery.

Each source query file in Markdown format (`.md`) located under `evaluation/sources/<source>/` (for example, `evaluation/sources/querylibrary/`) produces a corresponding *Gold Standard* YAML file (`.yaml`) under `evaluation/gold_standard/<source>/` (for example, `evaluation/gold_standard/querylibrary/`).

> [!NOTE]
> **Multi-source extensibility:**
> `querylibrary` is the initial source of SQL queries (originating from the *OHDSI Query Library*). The evaluation framework is fully modular: new query sources (e.g., `mimic`, `custom_ehr`, etc.) can be added under `evaluation/sources/<new_source>/` and processed seamlessly via the `--source` parameter.

---

## Directory Structure and Scripts

* **Sources directory:** `evaluation/sources/<source>/` (for example, `evaluation/sources/querylibrary`, containing 201 queries organized across 15 subfolders).
* **Gold standard directory:** `evaluation/gold_standard/<source>/` (for example, `evaluation/gold_standard/querylibrary/`).
* **Automation scripts directory:** `scripts/build_gold_standard/`
  * [`build_gold_standard.py`](scripts/build_gold_standard/build_gold_standard.py): Automated generator that translates Markdown queries into the Gold Standard YAML format. Supports `--source <source_name>` (default: `querylibrary`).
  * [`validate_gold_standard.py`](scripts/build_gold_standard/validate_gold_standard.py): Automated validator that verifies 100% of the YAML syntax, schema compliance, and BigQuery SQL prefixes, and generates dataset metric reports. Supports `--source <source_name>` (default: `querylibrary`).
  * [`spanish_questions.py`](scripts/build_gold_standard/spanish_questions.py): Comprehensive clinical dictionary with verified natural language questions in Spanish for the benchmark queries.

---

## Python Script Workflow

Whenever you need to generate, update, or validate Gold Standard evaluation files, run the Python scripts provided in `scripts/build_gold_standard/`:

### 1. Build all Gold Standard evaluations (full benchmark)
To iterate over all Markdown files of a source, translate queries, assign complexity/domains, and generate all YAML files:
```bash
# Default source (querylibrary)
python3 scripts/build_gold_standard/build_gold_standard.py

# Explicit source (e.g., querylibrary or a future source)
python3 scripts/build_gold_standard/build_gold_standard.py --source querylibrary
```

### 2. Build by specific subfolder (batch execution)
To generate or regenerate the YAML files for a specific subfolder (for example, `condition`, `drug_exposure`, `condition_occurrence`):
```bash
python3 scripts/build_gold_standard/build_gold_standard.py --subfolder condition
```

### 3. Build an individual case
To generate or regenerate a single evaluation file (for example, `C01`):
```bash
python3 scripts/build_gold_standard/build_gold_standard.py --id C01 --verbose
```

### 4. *Dry-Run* mode
To test and inspect parsing and translation without modifying or writing files to disk:
```bash
python3 scripts/build_gold_standard/build_gold_standard.py --dry-run --verbose
```

### 5. Validate generated files
After any generation or modification, run the validator script to guarantee 100% syntactic compliance, schema integrity, and zero errors:
```bash
# Validate default source (querylibrary)
python3 scripts/build_gold_standard/validate_gold_standard.py

# Validate a specific source
python3 scripts/build_gold_standard/validate_gold_standard.py --source querylibrary
```

---

## Translation and Processing Rules (Implemented in Scripts)

1. **`id_evaluacion`**: Format `"<source>_<ID>"` (for example, `"querylibrary_C01"`, `"querylibrary_CO05"`, or `<new_source>_<ID>`).
2. **`nivel_complejidad`**: Automatically assigned based on structural SQL complexity:
   * `"baja"` (low): Direct queries with basic filters; may query a single table or include at least one simple join (e.g., standard lookup with `concept` or `concept_synonym`), without complex subqueries, nested logic, or heavy aggregations.
   * `"intermedia"` (intermediate): Moderate queries with multiple joins, subqueries, conditional logic (`CASE`), `GROUP BY`, `ORDER BY`, or string/date manipulation.
   * `"compleja"` (complex): Advanced queries with multiple complex joins, nested subqueries, Common Table Expressions (`WITH`), window functions, or aggregated calculations over large OMOP tables.
3. **`domain_main`**: Domain of the primary OMOP table used in the SQL query representing the core clinical objective (for example, `"condition_occurrence"`, `"drug_exposure"`, `"condition_era"`, `"concept"`, `"person"`, `"cost"`, `"observation_period"`).
4. **`domain_others`**: Secondary OMOP table domains referenced or joined in the query, formatted as a comma-separated string list (for example, `"person, concept"`, `"visit_occurrence"`). If no secondary domains are used, an empty string `""` is provided.
5. **`pregunta_lenguaje_natural`**: Natural language description in **Spanish** explaining the clinical/biomedical objective of the query. Formatted using YAML folded scalar style (`>-`). Any `concept_id` must be replaced by its equivalent clinical name (do not include raw numeric identifiers in this field). If the clinical concept name is not available in the source query text, consult Athena (`https://athena.ohdsi.org/search-terms/terms/<concept_id>`) to retrieve it.
6. **`sql_base_gold_standard`**: 
   * References to generic OMOP CDM syntax (`@vocab.table`, `@cdm.table`, `table`) are translated into **Google BigQuery SQL** using the explicit dataset prefix: **`` `bio-med-480108.OMOP_54_A.table_name` ``**.
   * Formatted using YAML literal scalar style (`|`) with indented SQL for readability.
7. **`concept_ids_gold_standard`**: Explicit `concept_id` numbers hardcoded directly in `WHERE` or `JOIN` clauses as a comma-separated string (for example, `"192671"` or `"8507, 201826"`). If no concepts are directly hardcoded, an empty string `""` is provided.
8. **Deprecated fields**: The `fichero_csv_resultados_gold_standard` field is deprecated and must **never** be included.

---

## Output Template Structure

```yaml
id_evaluacion: "<FILE_ID>"
nivel_complejidad: "<baja|intermedia|compleja>"
domain_main: "<primary_omop_domain>"
domain_others: "<comma_separated_secondary_omop_domains_or_empty>"
pregunta_lenguaje_natural: >-
  <Clinical question in Spanish explaining the objective in natural language, replacing any concept_id with its equivalent clinical name (consult Athena https://athena.ohdsi.org/search-terms/terms/<concept_id> if not available in the text)>
sql_base_gold_standard: |
  <Multi-line formatted BigQuery SQL>
concept_ids_gold_standard: "<comma_separated_concept_ids_or_empty>"
```

