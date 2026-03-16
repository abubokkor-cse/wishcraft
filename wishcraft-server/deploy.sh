#!/bin/bash
# Deploy WishCraft backend to Google Cloud Run + Cloud Storage
# Usage: ./deploy.sh [PROJECT_ID] [GEMINI_API_KEY]

PROJECT_ID="${1:-$(gcloud config get-value project)}"
GEMINI_API_KEY="${2:-$GEMINI_API_KEY}"
SERVICE_NAME="wishcraft-server"
REGION="us-central1"
GCS_BUCKET="wishcraft-sync"

echo "🧞 Deploying WishCraft to Google Cloud..."
echo "   Project: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region:  $REGION"
echo "   Bucket:  $GCS_BUCKET"
echo ""

# Create Cloud Storage bucket for encrypted sync (if not exists)
echo "☁️ Creating Cloud Storage bucket..."
gsutil mb -l $REGION -p $PROJECT_ID gs://$GCS_BUCKET 2>/dev/null || echo "   Bucket already exists"

# Enable required APIs
echo "🔧 Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  --project $PROJECT_ID 2>/dev/null

# Build and deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --project $PROJECT_ID \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=$GEMINI_API_KEY,GCS_BUCKET=$GCS_BUCKET" \
  --memory 1Gi \
  --cpu 1 \
  --timeout 60 \
  --max-instances 5

# Get the deployed URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format="value(status.url)" 2>/dev/null)

echo ""
echo "✅ Deployment complete!"
echo "   Service URL: $SERVICE_URL"
echo "   Health:      ${SERVICE_URL}/api/health"
echo "   Token:       POST ${SERVICE_URL}/api/token"
echo ""
echo "💡 Set this URL in WishCraft Settings > Server URL"
echo "🔗 Service URL:"
gcloud run services describe $SERVICE_NAME --project $PROJECT_ID --region $REGION --format 'value(status.url)'
