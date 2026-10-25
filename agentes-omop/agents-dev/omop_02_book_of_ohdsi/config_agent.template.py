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

# Endpoint de Vertex AI Search (Discovery Engine) para 'The Book of OHDSI'
DISCOVERY_ENGINE_URL = "https://discoveryengine.googleapis.com/v1alpha/projects/TU_PROJECT_NUMBER_AQUI/locations/global/collections/default_collection/engines/TU_ENGINE_ID_BOOK_OF_OHDSI/servingConfigs/default_search:search"

