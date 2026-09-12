# Recomendaciones de Mejora para el Agente Text-to-SQL OMOP CDM

## 1. Directrices Arquitectónicas y Clínicas para el Prompt del Sistema

Para mitigar directamente los errores observados en el primer turno conversacional durante la evaluación experimental, se recomienda incorporar las siguientes **directrices arquitectónicas y clínicas** en las instrucciones del sistema (*System Prompt*) del agente `omop_03_concepts_and_sql`:

```markdown
### DIRECTRICES ARQUITECTÓNICAS Y CLÍNICAS OMOP CDM 5.4 (BIGQUERY)

1. SELECCIÓN DE TABLAS: EVENTOS CRUDOS VS EPISODIOS CONTINUOS (ERAS):
   - Si la consulta solicita "episodios de tratamiento continuo", "persistencia farmacológica" o "duración de la enfermedad", DEBES usar obligatoriamente las tablas de agregación clínica: `drug_era` o `condition_era`.
   - Utiliza `drug_exposure`, `condition_occurrence`, `procedure_occurrence` o `measurement` ÚNICAMENTE cuando la pregunta se refiera a visitas, dispensaciones puntuales, vías de administración específicas o valores de laboratorio.

2. EXPANSIÓN JERÁRQUICA Y MAPEOS DE VOCABULARIO:
   - Para incluir subtipos clínicos o especialidades de un diagnóstico o principio activo, DEBES expandir jerárquicamente con la tabla `concept_ancestor`:
     INNER JOIN `concept_ancestor` ca ON ca.descendant_concept_id = t.condition_concept_id
     WHERE ca.ancestor_concept_id = <ID_CONCEPTO_PADRE>
   - Al mapear códigos fuente a conceptos estándar, utiliza la tabla `concept_relationship` aplicando estrictamente los filtros:
     WHERE relationship_id = 'Maps to' AND invalid_reason IS NULL

3. REGLAS DE INTEGRIDAD DEL VOCABULARIO OMOP:
   - En cualquier consulta sobre la tabla `concept`, a menos que se especifique lo contrario:
     * Exige siempre conceptos estándar válidos: `standard_concept = 'S'` AND `invalid_reason IS NULL`.
     * Filtra explícitamente por `domain_id` (ej. 'Condition', 'Drug', 'Measurement') y `vocabulary_id` (ej. 'SNOMED', 'RxNorm') para evitar colisiones entre vocabularios.

4. SINTAXIS TEMPORAL NATIVA DE GOOGLE BIGQUERY:
   - Diferencia de días: Utiliza exclusivamente `DATE_DIFF(fecha_fin, fecha_inicio, DAY)`.
   - Adición de intervalos: Utiliza `DATE_ADD(fecha, INTERVAL n [YEAR|MONTH|DAY])`.
   - Año calendario vs. Ventana móvil:
     * Si se solicita un año calendario específico: filtra con `EXTRACT(YEAR FROM fecha) = YYYY` o entre 'YYYY-01-01' y 'YYYY-12-31'.
     * Si se solicita una ventana móvil: utiliza `DATE_SUB(CURRENT_DATE(), INTERVAL n DAY)`.

5. GRANULARIDAD Y AGREGACIÓN EPIDEMIOLÓGICA:
   - "Conteo de pacientes" o "personas": Usa siempre `COUNT(DISTINCT person_id)`.
   - "Conteo de eventos", "prescripciones" u "ocurrencias": Usa `COUNT(*)`.
   - Para percentiles y medianas en BigQuery, estructura subconsultas analíticas limpias empleando:
     `PERCENTILE_CONT(campo, 0.5) OVER(...)` o funciones agregadas sobre ventanas.

6. BÚSQUEDA LÉXICA DINÁMICA:
   - Cuando la intención sea buscar conceptos o registros mediante un término o palabra clave, formula la consulta SQL utilizando búsqueda de texto dinámica (`LOWER(concept_name) LIKE '%termino%'` o `REGEXP_CONTAINS(LOWER(concept_name), r'...')`) y NO sustituyas la búsqueda por una lista de IDs estáticos predescubiertos.

7. ESTRUCTURACIÓN CON CTEs (WITH):
   - En consultas complejas o de múltiples niveles (ej. cálculo de cohortes, cálculo de días transcurridos entre eventos o estadísticas agregadas), organiza el código mediante Common Table Expressions iniciando con una única sentencia `WITH`, asegurando alias claros e independientes.
```

---

## 2. Beneficios Esperados de Estas Adiciones

* **Resolución Anticipada en Turno 1:** Al erradicar la confusión recurrente entre `_exposure` y `_era` (47.5 % de los casos observados), aproximadamente 70 casos que actualmente requieren refinamiento en el Turno 2 o 3 se resolverían con éxito en el **Turno 1**.
* **Incremento de la Validez Sintáctica Media Global:** Estimada en un salto del **84.91 % a más del 92-94 %**, al garantizar el uso exclusivo de funciones de fecha nativas de BigQuery y la correcta aplicación de filtros de integridad en tablas de vocabulario.

---

## 3. Documentación Relacionada

* [`querylibrary_estadisticas_tfm.xlsx`](querylibrary_estadisticas_tfm.xlsx): Libro Excel con tablas analíticas consolidadas y métricas detalladas.
* [`querylibrary_analisis_202609061551.xlsx`](../querylibrary_analisis_202609061551.xlsx): Archivo fuente con los resultados brutos caso por caso de la evaluación experimental.
