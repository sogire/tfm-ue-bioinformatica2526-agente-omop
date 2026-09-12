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

# --- Confirmación antes de desplegar ---
echo "--------------------------------------------------"
echo "PREPARANDO DESPLIEGUE"
echo "  Entorno (ENV):      ${ENV}"
echo "  Proyecto (PROJECT): ${PROJECT_ID}"
echo "  Servicio (SERVICE): ${SERVICE_NAME}"
echo "  Región (REGION):    ${REGION}"
echo "  Dockerfile:         Dockerfile.${ENV}"
echo "--------------------------------------------------"
read -p "¿Deseas continuar con el despliegue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Despliegue cancelado."
    return 1
fi

# --- Step 1: Build Image with Cloud Build ---
echo "🛠️  Step 1: Building Docker image..."

DOCKERFILE_PATH="Dockerfile.${ENV}"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${SERVICE_NAME}:latest"

# We use --config to point to our yaml and --substitutions to pass our variables
gcloud builds submit . \
  --project="$PROJECT_ID" \
  --config="cloudbuild.yaml" \
  --substitutions="_DOCKERFILE_PATH=$DOCKERFILE_PATH,_IMAGE_NAME=$IMAGE_NAME" \
  --quiet

# --- Paso 2: Desplegar la imagen a Cloud Run ---
echo "🚀 Paso 2: Desplegando la imagen en Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image "$IMAGE_NAME" \
  --project $PROJECT_ID \
  --region "$REGION" \
  --service-account $SERVICE_ACCOUNT \
  --no-allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,\
GOOGLE_CLOUD_LOCATION=$REGION,\
GOOGLE_GENAI_USE_VERTEXAI=TRUE,\
ENV=$ENV"


echo "✅ Despliegue para el entorno '${ENV}' completado."
