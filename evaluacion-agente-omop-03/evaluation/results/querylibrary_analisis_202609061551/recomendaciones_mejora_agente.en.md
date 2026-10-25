> 🏠 **[Main README](../../../../README.en.md)** › **[Evaluation Framework](../../../README.en.md)** · 🌐 **Language / Idioma:** [Español](recomendaciones_mejora_agente.md) | **English**

# Improvement Recommendations for the OMOP CDM Text-to-SQL Agent

## 1. Architectural and Clinical Guidelines for the System Prompt

To directly mitigate the errors observed during the first conversational turn in the experimental evaluation, it is recommended to incorporate the following **architectural and clinical guidelines** into the *System Prompt* of the `omop_03_concepts_and_sql` agent:

```markdown
### ARCHITECTURAL AND CLINICAL GUIDELINES FOR OMOP CDM 5.4 (BIGQUERY)

1. TABLE SELECTION: RAW EVENTS VS. CONTINUOUS EPISODES (ERAS):
   - If the query requests "continuous treatment episodes", "drug persistence", or "disease duration", you MUST use the clinical aggregation tables: `drug_era` or `condition_era`.
   - Use `drug_exposure`, `condition_occurrence`, `procedure_occurrence`, or `measurement` ONLY when the question refers to visits, discrete dispensations, specific routes of administration, or laboratory values.

2. HIERARCHICAL EXPANSION AND VOCABULARY MAPPINGS:
   - To include clinical subtypes or specialties of a diagnosis or active ingredient, you MUST expand hierarchically using the `concept_ancestor` table:
     INNER JOIN `concept_ancestor` ca ON ca.descendant_concept_id = t.condition_concept_id
     WHERE ca.ancestor_concept_id = <PARENT_CONCEPT_ID>
   - When mapping source codes to standard concepts, use the `concept_relationship` table strictly applying the filters:
     WHERE relationship_id = 'Maps to' AND invalid_reason IS NULL

3. OMOP VOCABULARY INTEGRITY RULES:
   - In any query against the `concept` table, unless specified otherwise:
     * Always enforce valid standard concepts: `standard_concept = 'S'` AND `invalid_reason IS NULL`.
     * Explicitly filter by `domain_id` (e.g., 'Condition', 'Drug', 'Measurement') and `vocabulary_id` (e.g., 'SNOMED', 'RxNorm') to prevent cross-vocabulary collisions.

4. NATIVE GOOGLE BIGQUERY TEMPORAL SYNTAX:
   - Date difference in days: Exclusively use `DATE_DIFF(end_date, start_date, DAY)`.
   - Interval addition: Use `DATE_ADD(date_col, INTERVAL n [YEAR|MONTH|DAY])`.
   - Calendar year vs. Rolling window:
     * If a specific calendar year is requested: filter with `EXTRACT(YEAR FROM date_col) = YYYY` or between 'YYYY-01-01' and 'YYYY-12-31'.
     * If a rolling window is requested: use `DATE_SUB(CURRENT_DATE(), INTERVAL n DAY)`.

5. GRANULARITY AND EPIDEMIOLOGICAL AGGREGATION:
   - "Patient count" or "persons": Always use `COUNT(DISTINCT person_id)`.
   - "Event count", "prescriptions", or "occurrences": Use `COUNT(*)`.
   - For percentiles and medians in BigQuery, structure clean analytical subqueries using:
     `PERCENTILE_CONT(field, 0.5) OVER(...)` or window aggregate functions.

6. DYNAMIC LEXICAL SEARCH:
   - When the intent is to search for concepts or records by a term or keyword, formulate the SQL query using dynamic text matching (`LOWER(concept_name) LIKE '%term%'` or `REGEXP_CONTAINS(LOWER(concept_name), r'...')`) and DO NOT replace the search with a list of pre-discovered static IDs.

7. STRUCTURING WITH CTEs (WITH):
   - In complex or multi-level queries (e.g., cohort building, days elapsed between events, or aggregated statistics), organize the code using Common Table Expressions starting with a single `WITH` clause, ensuring clear and independent aliases.
```

---

## 2. Expected Benefits of These Additions

* **Early Resolution in Turn 1:** By eliminating the recurring confusion between `_exposure` and `_era` tables (47.5% of observed cases), approximately 70 cases that currently require refinement in Turn 2 or Turn 3 would be resolved successfully in **Turn 1**.
* **Increase in Overall Mean Syntactic Validity:** Estimated to rise from **84.91% to over 92–94%**, by ensuring the exclusive use of native BigQuery date functions and proper application of integrity filters on vocabulary tables.

---

## 3. Related Documentation

* [`querylibrary_estadisticas_tfm.xlsx`](querylibrary_estadisticas_tfm.xlsx): Excel workbook with consolidated analytical tables and detailed metrics.
* [`querylibrary_analisis_202609061551.xlsx`](../querylibrary_analisis_202609061551.xlsx): Source file containing the raw case-by-case results from the experimental evaluation.

