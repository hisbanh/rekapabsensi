#!/bin/bash

# SIPA YAUMI - Cloud Run Deployment Script
# This script deploys the application to Google Cloud Run

set -e

echo "🚀 Starting deployment to Google Cloud Run..."

# Configuration
PROJECT_ID="your-project-id"
REGION="asia-southeast2"
SERVICE_NAME="sipa-yaumi"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Set project
echo "📦 Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Build the container
echo "🔨 Building container image..."
gcloud builds submit --tag ${IMAGE_NAME}

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
    --set-env-vars "DJANGO_SETTINGS_MODULE=sipa_yaumi.settings"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📝 Next steps:"
echo "1. Update ALLOWED_HOSTS in settings.py with: ${SERVICE_URL}"
echo "2. Run migrations: gcloud run jobs execute migrate-job"
echo "3. Create superuser if needed"
echo "4. Configure Cloud SQL if using PostgreSQL"
