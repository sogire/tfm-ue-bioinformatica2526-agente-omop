#!/bin/bash
# ==============================================================================
# PLANTILLA DE CONFIGURACIÓN DE ENTORNO (config-dev.template.sh)
# ==============================================================================
# Este archivo sirve como plantilla desidentificada para configurar las variables
# globales y de infraestructura necesarias para el despliegue y ejecución de los
# agentes en Google Cloud Platform (Cloud Run, Vertex AI, BigQuery, IAM).
#
# INSTRUCCIONES DE USO:
# 1. Copie esta plantilla asignándole el nombre del entorno deseado:
#      cp config-dev.template.sh config-dev.sh
#      (o bien config-tst.sh / config-prd.sh para entornos de prueba o producción)
# 2. Rellene los valores entre comillas con los datos reales de su proyecto en GCP.
# 3. Asegúrese de cargar las variables en su sesión o ejecutar los scripts de despliegue:
#      source ./config-dev.sh
#      ./deploy_cloudrun.sh dev
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Identificación del Proyecto en Google Cloud Platform (GCP)
# ------------------------------------------------------------------------------
# PROJECT_ID:
#   Identificador alfanumérico único del proyecto en Google Cloud (no el nombre visible).
#   Puede consultarse con: `gcloud config get-value project` o en la consola web de GCP.
#   Ejemplo: "mi-proyecto-omop-123456"
export PROJECT_ID="TU_PROJECT_ID_AQUI"

# PROJECT_NUMBER:
#   Número entero único de 12 dígitos asignado automáticamente por GCP a su proyecto.
#   Es necesario para la configuración de políticas IAM, Identity-Aware Proxy (IAP)
#   y permisos delegados a cuentas de servicio de Google.
#   Puede consultarse con: `gcloud projects describe $PROJECT_ID --format="value(projectNumber)"`
#   Ejemplo: "123456789012"
export PROJECT_NUMBER="TU_PROJECT_NUMBER_AQUI"

# ------------------------------------------------------------------------------
# 2. Región de Despliegue de Servicios
# ------------------------------------------------------------------------------
# REGION:
#   Región geográfica de GCP donde se desplegará el servicio en Cloud Run, se crearán
#   los repositorios en Artifact Registry y se consumirán los modelos en Vertex AI.
#   Recomendación: Elegir una región con soporte completo de Vertex AI y cercanía a los datos.
#   Ejemplo: "europe-west1" (Bélgica), "europe-west3" (Fráncfort), "us-central1" (Iowa).
export REGION="europe-west1"

# ------------------------------------------------------------------------------
# 3. Nombre del Servicio en Google Cloud Run
# ------------------------------------------------------------------------------
# SERVICE_NAME:
#   Nombre identificativo que recibirá el servicio web en Google Cloud Run.
#   Conviene incluir el sufijo del entorno (dev, tst, prd) para permitir coexistencia.
#   Ejemplo: "omop-agent-dev", "omop-agent-prd"
export SERVICE_NAME="omop-agent-dev"

# ------------------------------------------------------------------------------
# 4. Cuenta de Servicio de Ejecución (IAM Service Account)
# ------------------------------------------------------------------------------
# SERVICE_ACCOUNT:
#   Dirección de correo electrónico de la cuenta de servicio de IAM que asumirá el
#   contenedor de Cloud Run en tiempo de ejecución.
#   Esta cuenta requiere permisos mínimos para:
#     - Consultar BigQuery: roles/bigquery.dataViewer, roles/bigquery.user, roles/bigquery.jobUser
#     - Invocar modelos fundacionales de Gemini: roles/aiplatform.user
#     - Leer definiciones de fenotipos en GCS (si aplica): roles/storage.objectViewer
#   Ejemplo: "omop-training@${PROJECT_ID}.iam.gserviceaccount.com"
export SERVICE_ACCOUNT="nombre-cuenta-servicio@${PROJECT_ID}.iam.gserviceaccount.com"

# ------------------------------------------------------------------------------
# 5. Base de Datos / Catálogo OMOP CDM en Google BigQuery
# ------------------------------------------------------------------------------
# OMOP_DATASET:
#   Ruta completamente cualificada del conjunto de datos (dataset) de BigQuery que
#   aloja las tablas relacionales del modelo común de datos OMOP CDM 5.4
#   (concept, concept_ancestor, condition_occurrence, drug_exposure, person, etc.).
#   Estructura: "<PROJECT_ID>.<DATASET_NAME>"
#   Ejemplo: "${PROJECT_ID}.OMOP_54_A" o "hospital-data.omop_cdm_54"
export OMOP_DATASET="${PROJECT_ID}.NOMBRE_DATASET_OMOP"

# ------------------------------------------------------------------------------
# 6. Directorio de Definición de Agentes ADK
# ------------------------------------------------------------------------------
# AGENT_PATH:
#   Ruta relativa o absoluta hacia el directorio que contiene las subcarpetas de los
#   agentes desarrollados bajo Google Agent Development Kit (ADK).
#   Por defecto: "./agents-dev"
export AGENT_PATH="./agents-dev"
