#!/bin/bash

# --- Validación de Entorno ---
if [ -z "$1" ]; then
  echo "❌ Error: Debes especificar un entorno (dev, tst, prd)."
  echo "Uso: $0 <entorno>"
  read -p "Presiona Enter para salir..."
  return 1
fi

ENV=$1
CONFIG_FILE="./config-${ENV}.sh"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ Error: El archivo de configuración '$CONFIG_FILE' no existe."
  read -p "Presiona Enter para salir..."
  return 1
fi

source $CONFIG_FILE

# 1. Grant permission to see and read the BigQuery data
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/bigquery.dataViewer"

# 2. Grant permission to run query jobs (compute the results)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/bigquery.jobUser"

# 3. Grant permission to use Vertex AI (to call Gemini)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/discoveryengine.viewer"