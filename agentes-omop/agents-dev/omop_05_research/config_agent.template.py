# ==============================================================================
# PLANTILLA DE CONFIGURACIÓN DEL AGENTE (config_agent.template.py)
# ==============================================================================
# Copie este archivo como `config_agent.py` en este mismo directorio y rellene
# los valores correspondientes a su proyecto en Google Cloud Platform (GCP):
#   cp config_agent.template.py config_agent.py
# ==============================================================================

MODEL_NAME = "gemini-2.5-flash"

# Configuración de trazabilidad y logs en Google BigQuery
BQ_LOG_PROJECT = "TU_PROJECT_ID_AQUI"
BQ_LOG_DATASET = "OMOP_AGENTS"
BQ_LOG_TABLE = "LOGS_V00"
BQ_LOG_LOCATION = "EU"

# Tablas y datasets de referencia OMOP CDM en BigQuery
DATASET_TABLE_CONCEPTS = "TU_PROJECT_ID_AQUI.NOMBRE_DATASET_VOCABULARIO.concept"
DATASET_FOR_VALIDATIONS = "TU_PROJECT_ID_AQUI.NOMBRE_DATASET_OMOP"


# Shared protocols as modular constants
OPERATIONAL_PROTOCOL = """
1. CLASSIFY: Determine if the request is for:
   - Clinical Characterization (Describing a population)
   - Population-Level Estimation (Causal inference/Comparison)
   - Patient-Level Prediction (Predicting future outcomes)
"""

TCO_TAR_STRUCTURE = """
2. STRUCTURING (T-C-O-TAR): Define:
   - Target Cohort (T): Who are the patients? Define the index event.
   - Comparator (C): Only for Estimation. Who is the control group?
   - Outcome (O): What is the clinical event of interest?
   - Time-at-Risk (TAR): What is the window of observation?
"""

CDM_MAPPING = """
3. CDM MAPPING: Identify involved OMOP tables (e.g., CONDITION_OCCURRENCE, DRUG_EXPOSURE) 
   and prioritize Standard Concepts (SNOMED, RxNorm).
"""

SQL_BLUEPRINT_GUIDE = """
Conclude with a 'SQL Logic Blueprint' describing the joins and filters needed for BigQuery.
"""

