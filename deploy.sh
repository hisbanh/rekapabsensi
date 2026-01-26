#!/bin/bash

# SIPA YAUMI - Cloud Run Deployment Script
# This script deploys the application to Google Cloud Run

set -e

echo "🚀 Starting deployment to Google Cloud Run..."

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="asia-southeast2"
SERVICE_NAME="sipa-yaumi"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if PROJECT_ID is set
if [ "$PROJECT_ID" = "your-project-id" ]; then
    echo "❌ Please set GCP_PROJECT_ID environment variable or edit this script"
    echo "Example: export GCP_PROJECT_ID=my-project-123"
    exit 1
fi

# Set project
echo "📦 Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Build the container using Cloud Build
echo "🔨 Building container image..."
gcloud builds submit --tag ${IMAGE_NAME} --timeout=20m

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

# Deploy to Cloud Run
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "DJANGO_SETTINGS_MODULE=sipa_yaumi.settings,DEBUG=False"

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed!"
    exit 1
fi

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📝 Next steps:"
echo "1. Update ALLOWED_HOSTS in settings.py with: ${SERVICE_URL}"
echo "2. Set SECRET_KEY environment variable"
echo "3. Run migrations (see CLOUD_RUN_DEPLOYMENT.md)"
echo "4. Create superuser"
echo ""
echo "To set environment variables:"
echo "gcloud run services update ${SERVICE_NAME} --region ${REGION} --set-env-vars SECRET_KEY=your-secret-key"
