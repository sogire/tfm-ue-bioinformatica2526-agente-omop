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

echo "🛠️  Habilitando APIs para el proyecto: $PROJECT_ID..."

# 2. Configurar el proyecto activo (por seguridad)
gcloud config set project $PROJECT_ID

# 3. Habilitar los servicios solicitados
# Agregamos 'iam.googleapis.com' porque es necesaria para gestionar el Service Account
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    iam.googleapis.com \
    artifactregistry.googleapis.com \
    cloudresourcemanager.googleapis.com \
    vectorsearch.googleapis.com

echo "✅ APIs habilitadas correctamente."