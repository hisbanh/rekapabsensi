# SIPA YAUMI - Google Cloud Run Deployment Guide

Panduan lengkap untuk deploy aplikasi SIPA YAUMI ke Google Cloud Run.

## Prerequisites

1. **Google Cloud Account** dengan billing enabled
2. **gcloud CLI** terinstall ([Install Guide](https://cloud.google.com/sdk/docs/install))
3. **Docker** terinstall (opsional, untuk testing lokal)
4. **Git** untuk version control

## Setup Awal

### 1. Install gcloud CLI

```bash
# macOS
brew install google-cloud-sdk

# Atau download dari: https://cloud.google.com/sdk/docs/install
```

### 2. Login dan Setup Project

```bash
# Login ke Google Cloud
gcloud auth login

# Buat project baru (atau gunakan yang sudah ada)
gcloud projects create sipa-yaumi-prod --name="SIPA YAUMI Production"

# Set project sebagai default
gcloud config set project sipa-yaumi-prod

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

## Deployment Options

### Option 1: Deploy dengan SQLite (Simple, untuk testing)

**Kelebihan:**
- Setup cepat
- Tidak perlu database eksternal
- Cocok untuk testing/demo

**Kekurangan:**
- Data hilang saat container restart
- Tidak scalable
- Tidak recommended untuk production

**Steps:**

1. Update `.env` atau set environment variables:
```bash
DEBUG=False
ALLOWED_HOSTS=*.run.app
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=/app/data/db.sqlite3
```

2. Deploy:
```bash
./deploy.sh
```

### Option 2: Deploy dengan Cloud SQL PostgreSQL (Recommended)

**Kelebihan:**
- Data persistent
- Scalable
- Production-ready
- Automatic backups

**Kekurangan:**
- Setup lebih kompleks
- Ada biaya tambahan

**Steps:**

#### 1. Create Cloud SQL Instance

```bash
# Create PostgreSQL instance
gcloud sql instances create sipa-yaumi-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=asia-southeast2

# Set root password
gcloud sql users set-password postgres \
    --instance=sipa-yaumi-db \
    --password=YOUR_SECURE_PASSWORD

# Create database
gcloud sql databases create sipa_yaumi_db \
    --instance=sipa-yaumi-db
```

#### 2. Update Environment Variables

Edit `.env.production`:
```bash
DB_ENGINE=django.db.backends.postgresql
DB_NAME=sipa_yaumi_db
DB_USER=postgres
DB_PASSWORD=YOUR_SECURE_PASSWORD
DB_HOST=/cloudsql/PROJECT_ID:asia-southeast2:sipa-yaumi-db
DB_PORT=5432
```

#### 3. Update requirements.txt

Tambahkan PostgreSQL adapter:
```bash
echo "psycopg2-binary==2.9.9" >> requirements.txt
```

#### 4. Deploy dengan Cloud SQL Connection

```bash
gcloud run deploy sipa-yaumi \
    --image gcr.io/PROJECT_ID/sipa-yaumi \
    --platform managed \
    --region asia-southeast2 \
    --allow-unauthenticated \
    --add-cloudsql-instances PROJECT_ID:asia-southeast2:sipa-yaumi-db \
    --set-env-vars "DB_HOST=/cloudsql/PROJECT_ID:asia-southeast2:sipa-yaumi-db"
```

## Manual Deployment Steps

### 1. Build Container Image

```bash
# Build locally (optional, untuk testing)
docker build -t sipa-yaumi .

# Test locally
docker run -p 8080:8080 -e PORT=8080 sipa-yaumi

# Build di Cloud
gcloud builds submit --tag gcr.io/PROJECT_ID/sipa-yaumi
```

### 2. Deploy to Cloud Run

```bash
gcloud run deploy sipa-yaumi \
    --image gcr.io/PROJECT_ID/sipa-yaumi \
    --platform managed \
    --region asia-southeast2 \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --set-env-vars "DEBUG=False,DJANGO_SETTINGS_MODULE=sipa_yaumi.settings"
```

### 3. Run Migrations

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe sipa-yaumi --region asia-southeast2 --format 'value(status.url)')

# Run migrations via Cloud Run Jobs (recommended)
gcloud run jobs create migrate-job \
    --image gcr.io/PROJECT_ID/sipa-yaumi \
    --region asia-southeast2 \
    --command python \
    --args manage.py,migrate,--noinput

gcloud run jobs execute migrate-job --region asia-southeast2

# Atau via SSH ke container (alternatif)
gcloud run services proxy sipa-yaumi --region asia-southeast2
```

### 4. Create Superuser

```bash
# Via Cloud Run Jobs
gcloud run jobs create createsuperuser-job \
    --image gcr.io/PROJECT_ID/sipa-yaumi \
    --region asia-southeast2 \
    --command python \
    --args manage.py,createsuperuser,--noinput,--username=admin,--email=admin@example.com

# Set password via Django shell
gcloud run jobs create shell-job \
    --image gcr.io/PROJECT_ID/sipa-yaumi \
    --region asia-southeast2 \
    --command python \
    --args manage.py,shell
```

### 5. Collect Static Files

Static files sudah di-collect saat build (di Dockerfile).
Jika perlu update:

```bash
# Rebuild dan redeploy
gcloud builds submit --tag gcr.io/PROJECT_ID/sipa-yaumi
gcloud run deploy sipa-yaumi --image gcr.io/PROJECT_ID/sipa-yaumi --region asia-southeast2
```

## Configuration

### Environment Variables

Set via Cloud Run console atau CLI:

```bash
gcloud run services update sipa-yaumi \
    --region asia-southeast2 \
    --set-env-vars "
DEBUG=False,
SECRET_KEY=your-secret-key-here,
ALLOWED_HOSTS=*.run.app,
DB_ENGINE=django.db.backends.postgresql,
DB_NAME=sipa_yaumi_db,
DB_USER=postgres,
DB_PASSWORD=your-password,
DB_HOST=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
"
```

### Update ALLOWED_HOSTS

Setelah deploy, update `settings.py`:

```python
ALLOWED_HOSTS = [
    'sipa-yaumi-xxxxx.run.app',  # Cloud Run URL
    'your-custom-domain.com',     # Custom domain (optional)
]
```

## Custom Domain (Optional)

### 1. Verify Domain

```bash
gcloud domains verify your-domain.com
```

### 2. Map Domain to Cloud Run

```bash
gcloud run domain-mappings create \
    --service sipa-yaumi \
    --domain your-domain.com \
    --region asia-southeast2
```

### 3. Update DNS Records

Tambahkan DNS records yang diberikan oleh Google Cloud.

## Monitoring & Logs

### View Logs

```bash
# Real-time logs
gcloud run services logs tail sipa-yaumi --region asia-southeast2

# Recent logs
gcloud run services logs read sipa-yaumi --region asia-southeast2 --limit 100
```

### Monitoring Dashboard

Akses di: https://console.cloud.google.com/run

## Troubleshooting

### Container Fails to Start

```bash
# Check logs
gcloud run services logs read sipa-yaumi --region asia-southeast2

# Common issues:
# 1. Missing environment variables
# 2. Database connection failed
# 3. Static files not collected
```

### Database Connection Issues

```bash
# Test Cloud SQL connection
gcloud sql connect sipa-yaumi-db --user=postgres

# Check instance status
gcloud sql instances describe sipa-yaumi-db
```

### Static Files Not Loading

```bash
# Rebuild with static files
docker build -t gcr.io/PROJECT_ID/sipa-yaumi .
gcloud builds submit --tag gcr.io/PROJECT_ID/sipa-yaumi
gcloud run deploy sipa-yaumi --image gcr.io/PROJECT_ID/sipa-yaumi --region asia-southeast2
```

## Cost Estimation

### Cloud Run (512Mi RAM, 1 CPU)
- **Free tier**: 2 million requests/month
- **After free tier**: ~$0.00002400 per request
- **Idle**: No charge

### Cloud SQL (db-f1-micro)
- **Cost**: ~$7-10/month
- **Storage**: $0.17/GB/month
- **Backup**: $0.08/GB/month

### Total Estimated Cost
- **Small app**: $10-20/month
- **Medium traffic**: $20-50/month

## Security Best Practices

1. **Secret Key**: Generate strong SECRET_KEY
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

2. **Database Password**: Use strong password
3. **HTTPS**: Enabled by default on Cloud Run
4. **Environment Variables**: Never commit secrets to Git
5. **IAM**: Restrict access to Cloud SQL

## Backup & Recovery

### Database Backup

```bash
# Enable automatic backups
gcloud sql instances patch sipa-yaumi-db \
    --backup-start-time=03:00

# Manual backup
gcloud sql backups create --instance=sipa-yaumi-db

# List backups
gcloud sql backups list --instance=sipa-yaumi-db

# Restore from backup
gcloud sql backups restore BACKUP_ID --backup-instance=sipa-yaumi-db
```

## CI/CD with GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - uses: google-github-actions/setup-gcloud@v0
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
      
      - name: Build and Deploy
        run: |
          gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/sipa-yaumi
          gcloud run deploy sipa-yaumi --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/sipa-yaumi --region asia-southeast2
```

## Support

Untuk bantuan lebih lanjut:
- Google Cloud Documentation: https://cloud.google.com/run/docs
- Django Deployment: https://docs.djangoproject.com/en/5.0/howto/deployment/

---

**Created**: January 2026
**Last Updated**: January 2026
**Version**: 1.0
