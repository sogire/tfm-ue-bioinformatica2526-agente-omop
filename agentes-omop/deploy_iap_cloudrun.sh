#!/bin/bash
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

echo "🚀 Iniciando IAP in Cloud Run $SERVICE_NAME"

# IAP
EMAIL_ADDRESS=sergio.bermudez@sogire.com


gcloud config set project $GOOGLE_CLOUD_PROJECT



echo "--- Configuring IAP for Cloud Run service: ${SERVICE_NAME} ---"

# Step 1: Ensure the IAP service agent exists. This is safe to run multiple times.
gcloud beta services identity create --service=iap.googleapis.com --project=${PROJECT_ID}

# Step 2: Grant the IAP service agent permission to invoke THIS Cloud Run service.
# This is more secure than granting the role at the project level.
gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
  --project=${PROJECT_ID} \
  --region=${REGION} \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-iap.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# Step 3: Grant a user access to the service through IAP.
# This is the command that effectively "enables" IAP for the specified user.

gcloud beta iap web add-iam-policy-binding \
    --resource-type=cloud-run \
    --service=${SERVICE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --member=user:${EMAIL_ADDRESS} \
    --role=roles/iap.httpsResourceAccessor \
    --condition=None