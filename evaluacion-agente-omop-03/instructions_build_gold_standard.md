> 🏠 **[README Principal](../README.md)** › **[Marco de Evaluación](README.md)** · 🌐 **Idioma / Language:** **Español** | [English](instructions_build_gold_standard.en.md)

# Instrucciones: Generación de Evaluaciones YAML del Estándar de Oro (*Gold Standard*) (OMOP CDM 5.4)

## Objetivo
Generar archivos de configuración estandarizados en formato YAML para el estándar de oro (*Gold Standard*) del banco de pruebas (*benchmark*) de evaluación de consultas en lenguaje natural sobre una base de datos OMOP CDM 5.4 en Google BigQuery.

Cada archivo de consulta origen en formato Markdown (`.md`) ubicado bajo `evaluation/sources/<fuente>/` (por ejemplo, `evaluation/sources/querylibrary/`) produce su correspondiente archivo YAML de estándar de oro (`.yaml`) bajo `evaluation/gold_standard/<fuente>/` (por ejemplo, `evaluation/gold_standard/querylibrary/`).

> [!NOTE]
> **Extensibilidad multifuente:**
> `querylibrary` es la fuente inicial de consultas SQL (procedente de la biblioteca de consultas de OHDSI, *OHDSI Query Library*). El marco de evaluación es totalmente modular: se pueden añadir nuevas fuentes de consultas (ej. `mimic`, `custom_ehr`, etc.) bajo `evaluation/sources/<nueva_fuente>/` y procesarlas de forma transparente mediante el parámetro `--source`.

---

## Estructura de Directorios y Scripts

* **Directorio de fuentes:** `evaluation/sources/<fuente>/` (por ejemplo, `evaluation/sources/querylibrary`, que contiene 201 consultas organizadas en 15 subcarpetas).
* **Directorio del estándar de oro:** `evaluation/gold_standard/<fuente>/` (por ejemplo, `evaluation/gold_standard/querylibrary/`).
* **Directorio de scripts de automatización:** `scripts/build_gold_standard/`
  * [`build_gold_standard.py`](scripts/build_gold_standard/build_gold_standard.py): Generador automatizado que traduce las consultas Markdown al formato YAML del estándar de oro. Admite `--source <nombre_fuente>` (por defecto: `querylibrary`).
  * [`validate_gold_standard.py`](scripts/build_gold_standard/validate_gold_standard.py): Validador automatizado que verifica al 100 % la sintaxis YAML, la conformidad con el esquema, los prefijos SQL de BigQuery y genera informes con las métricas del conjunto de datos. Admite `--source <nombre_fuente>` (por defecto: `querylibrary`).
  * [`spanish_questions.py`](scripts/build_gold_standard/spanish_questions.py): Diccionario clínico exhaustivo con preguntas verificadas en lenguaje natural en español para las consultas del banco de pruebas.

---

## Flujo de Trabajo con Scripts de Python

Siempre que sea necesario generar, actualizar o validar archivos de evaluación del estándar de oro, ejecute los scripts de Python proporcionados en `scripts/build_gold_standard/`:

### 1. Construcción de todas las evaluaciones del estándar de oro (banco de pruebas completo)
Para iterar sobre todos los archivos Markdown de una fuente, traducir las consultas, asignar complejidad/dominios y generar todos los archivos YAML:
```bash
# Fuente por defecto (querylibrary)
python3 scripts/build_gold_standard/build_gold_standard.py

# Fuente explícita (ej. querylibrary o una fuente futura)
python3 scripts/build_gold_standard/build_gold_standard.py --source querylibrary
```

### 2. Construcción por subcarpeta específica (ejecución por lotes)
Para generar o regenerar los archivos YAML de una subcarpeta concreta (por ejemplo, `condition`, `drug_exposure`, `condition_occurrence`):
```bash
python3 scripts/build_gold_standard/build_gold_standard.py --subfolder condition
```

### 3. Construcción de un caso individual
Para generar o regenerar un único archivo de evaluación (por ejemplo, `C01`):
```bash
python3 scripts/build_gold_standard/build_gold_standard.py --id C01 --verbose
```

### 4. Modo de simulación (*Dry-Run*)
Para probar e inspeccionar el análisis y traducción sin modificar ni escribir archivos en el disco:
```bash
python3 scripts/build_gold_standard/build_gold_standard.py --dry-run --verbose
```

### 5. Validación de los archivos generados
Tras cualquier generación o modificación, ejecute el script validador para garantizar el 100 % de conformidad sintáctica, integridad del esquema y ausencia de errores:
```bash
# Validar la fuente por defecto (querylibrary)
python3 scripts/build_gold_standard/validate_gold_standard.py

# Validar una fuente específica
python3 scripts/build_gold_standard/validate_gold_standard.py --source querylibrary
```

---

## Reglas de Traducción y Procesamiento (Implementadas en los Scripts)

1. **`id_evaluacion`**: Formato `"<fuente>_<ID>"` (por ejemplo, `"querylibrary_C01"`, `"querylibrary_CO05"` o `<nueva_fuente>_<ID>`).
2. **`nivel_complejidad`**: Asignado automáticamente según la complejidad estructural del SQL:
   * `"baja"`: Consultas directas con filtros básicos; pueden ser sobre una sola tabla o incluir al menos una unión simple (*join*, ej. búsqueda estándar con `concept` o `concept_synonym`), sin subconsultas complejas, lógica anidada ni agregaciones pesadas.
   * `"intermedia"`: Consultas moderadas con múltiples uniones (*joins*), subconsultas, lógica condicional (`CASE`), `GROUP BY`, `ORDER BY` o manipulación de cadenas/fechas.
   * `"compleja"`: Consultas avanzadas con múltiples uniones complejas, subconsultas anidadas, expresiones de tabla comunes o CTEs (`WITH`), funciones de ventana (*window functions*) o cálculos agregados sobre tablas OMOP de gran tamaño.
3. **`domain_main`**: Dominio de la tabla OMOP principal empleada en la consulta SQL que representa el objetivo clínico central (por ejemplo, `"condition_occurrence"`, `"drug_exposure"`, `"condition_era"`, `"concept"`, `"person"`, `"cost"`, `"observation_period"`).
4. **`domain_others`**: Dominios de tablas OMOP secundarias referenciadas o unidas en la consulta, en formato de lista de texto separada por comas (por ejemplo, `"person, concept"`, `"visit_occurrence"`). Si no se emplean dominios secundarios, se proporciona una cadena vacía `""`.
5. **`pregunta_lenguaje_natural`**: Descripción en lenguaje natural en **español** que explica el objetivo clínico/biomédico de la consulta. Formateada con estilo escalar plegado de YAML (`>-`). Cualquier `concept_id` debe sustituirse por su nombre clínico equivalente (no incluir identificadores numéricos sin procesar en este campo). Si el nombre clínico del concepto no está disponible en el texto de la consulta de origen, consúltese Athena (`https://athena.ohdsi.org/search-terms/terms/<concept_id>`) para obtenerlo.
6. **`sql_base_gold_standard`**: 
   * Las referencias a la sintaxis genérica de OMOP CDM (`@vocab.table`, `@cdm.table`, `table`) se traducen a **Google BigQuery SQL** empleando el prefijo explícito del conjunto de datos: **`` `bio-med-480108.OMOP_54_A.nombre_tabla` ``**.
   * Formateada con estilo escalar literal de YAML (`|`) con el SQL sangrado para facilitar su lectura.
7. **`concept_ids_gold_standard`**: Números de `concept_id` explícitos codificados directamente en cláusulas `WHERE` o `JOIN` como una cadena de texto separada por comas (por ejemplo, `"192671"` o `"8507, 201826"`). Si no hay conceptos codificados directamente, se proporciona una cadena vacía `""`.
8. **Campos obsoletos**: El campo `fichero_csv_resultados_gold_standard` está obsoleto y **nunca** debe incluirse.

---

## Estructura de la Plantilla de Salida

```yaml
id_evaluacion: "<ID_FICHERO>"
nivel_complejidad: "<baja|intermedia|compleja>"
domain_main: "<dominio_omop_principal>"
domain_others: "<dominios_omop_secundarios_separados_por_coma_o_vacio>"
pregunta_lenguaje_natural: >-
  <Pregunta clínica en español que explica el objetivo en lenguaje natural, sustituyendo cualquier concept_id por su nombre clínico equivalente (consultar Athena https://athena.ohdsi.org/search-terms/terms/<concept_id> si no está disponible en el texto)>
sql_base_gold_standard: |
  <SQL de BigQuery formateado en varias líneas>
concept_ids_gold_standard: "<concept_ids_separados_por_coma_o_vacio>"
```