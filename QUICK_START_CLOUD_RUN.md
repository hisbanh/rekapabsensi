# Quick Start - Deploy ke Google Cloud Run

Panduan cepat untuk deploy SIPA YAUMI ke Google Cloud Run dalam 10 menit.

## Prerequisites

- Google Cloud account dengan billing enabled
- gcloud CLI terinstall

## Step 1: Install gcloud CLI

```bash
# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Windows
# Download dari: https://cloud.google.com/sdk/docs/install
```

## Step 2: Login dan Setup

```bash
# Login
gcloud auth login

# Buat project baru
gcloud projects create sipa-yaumi-prod --name="SIPA YAUMI"

# Set project
gcloud config set project sipa-yaumi-prod

# Enable APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com
```

## Step 3: Deploy (Simple - SQLite)

```bash
# Edit deploy.sh - ganti PROJECT_ID
nano deploy.sh

# Jalankan deployment
./deploy.sh
```

## Step 4: Akses Aplikasi

Setelah deploy selesai, Anda akan mendapat URL seperti:
```
https://sipa-yaumi-xxxxx-as.a.run.app
```

## Step 5: Setup Admin

```bash
# Get service name
SERVICE_URL=$(gcloud run services describe sipa-yaumi --region asia-southeast2 --format 'value(status.url)')

# SSH ke container (untuk run migrations dan create superuser)
# Cara 1: Via Cloud Console
# 1. Buka https://console.cloud.google.com/run
# 2. Klik service "sipa-yaumi"
# 3. Klik tab "Logs"
# 4. Klik "Cloud Shell"

# Cara 2: Via gcloud (advanced)
# Buat job untuk migrations
gcloud run jobs create migrate \
    --image gcr.io/sipa-yaumi-prod/sipa-yaumi \
    --region asia-southeast2 \
    --command python \
    --args manage.py,migrate,--noinput

gcloud run jobs execute migrate --region asia-southeast2
```

## Troubleshooting

### Error: "gcloud: command not found"
```bash
# Install gcloud CLI terlebih dahulu
```

### Error: "Permission denied"
```bash
# Login ulang
gcloud auth login
```

### Error: "Billing not enabled"
```bash
# Enable billing di: https://console.cloud.google.com/billing
```

## Next Steps

1. **Setup Database Production**: Gunakan Cloud SQL PostgreSQL (lihat CLOUD_RUN_DEPLOYMENT.md)
2. **Custom Domain**: Tambahkan domain sendiri
3. **CI/CD**: Setup GitHub Actions untuk auto-deploy
4. **Monitoring**: Setup alerts dan monitoring

## Biaya

- **Free tier**: 2 juta requests/bulan gratis
- **Setelah free tier**: ~$0.000024 per request
- **Estimasi**: $10-20/bulan untuk aplikasi kecil

## Support

Dokumentasi lengkap: `CLOUD_RUN_DEPLOYMENT.md`
