# Deployment Guide

This guide covers both local development with Docker and production deployment to Google Cloud.

## Local Development with Docker Compose

### Prerequisites
- Docker and Docker Compose installed
- Git

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd inspyer-ping-pong
   ```

2. **Start all services:**
   ```bash
   docker-compose up --build
   ```

3. **Run database migrations (first time only):**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

4. **Create a superuser (optional):**
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

5. **Access the application:**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - Django Admin: http://localhost:8000/admin

### Development Commands

```bash
# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after dependency changes
docker-compose up --build

# Reset database
docker-compose down -v  # This removes the postgres volume
docker-compose up --build
```

---

## Google Cloud Production Deployment

### Phase 1: Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

### Phase 2: Create Cloud SQL Instance

1. **Create the PostgreSQL instance:**
   ```bash
   gcloud sql instances create ping-pong-db \
     --database-version=POSTGRES_15 \
     --tier=db-f1-micro \
     --region=us-central1 \
     --root-password=YOUR_ROOT_PASSWORD
   ```

2. **Create a database:**
   ```bash
   gcloud sql databases create pingpong --instance=ping-pong-db
   ```

3. **Create a user:**
   ```bash
   gcloud sql users create django_user \
     --instance=ping-pong-db \
     --password=YOUR_DJANGO_USER_PASSWORD
   ```

### Phase 3: Create Artifact Registry

```bash
gcloud artifacts repositories create ping-pong-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Ping Pong Elo Tracker Docker images"
```

### Phase 4: Create Secrets in Secret Manager

1. **Create the Django secret key:**
   ```bash
   echo -n "your-production-secret-key-here" | \
     gcloud secrets create django-secret-key --data-file=-
   ```

2. **Create the database password secret:**
   ```bash
   echo -n "YOUR_DJANGO_USER_PASSWORD" | \
     gcloud secrets create django-db-password --data-file=-
   ```

3. **Grant Cloud Run access to secrets:**
   ```bash
   PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')

   gcloud secrets add-iam-policy-binding django-secret-key \
     --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"

   gcloud secrets add-iam-policy-binding django-db-password \
     --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

### Phase 5: Set Up CI/CD with Cloud Build

1. **Go to Cloud Console > Cloud Build > Triggers**

2. **Click "Connect Repository":**
   - Select GitHub
   - Authenticate and select your repository

3. **Create a trigger:**
   - Name: `deploy-on-push`
   - Event: Push to branch
   - Branch: `^main$` or `^master$`
   - Configuration: Cloud Build configuration file
   - Location: `cloudbuild.yaml`

4. **Grant Cloud Build permissions:**
   ```bash
   PROJECT_ID=$(gcloud config get-value project)
   PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

   # Grant Cloud Run admin
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
     --role="roles/run.admin"

   # Grant service account user
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
     --role="roles/iam.serviceAccountUser"

   # Grant Cloud SQL client
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
     --role="roles/cloudsql.client"

   # Grant Secret Manager accessor
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

### Phase 6: Deploy

**Option A: Automatic Deployment (recommended)**
Push to your main branch, and Cloud Build will automatically build and deploy.

```bash
git add .
git commit -m "Add cloud deployment configuration"
git push origin main
```

**Option B: Manual First Deployment**
Trigger the build manually in Cloud Console > Cloud Build > Triggers.

### Phase 7: Configure Frontend for Production

After the first deployment, get the backend URL:

```bash
BACKEND_URL=$(gcloud run services describe ping-pong-backend \
  --region=us-central1 --format='value(status.url)')
echo $BACKEND_URL
```

Update `cloudbuild.yaml` to pass the backend URL to the frontend build, or configure the frontend to use a relative API path.

### Phase 8: Update CORS Settings

Update the backend's CORS settings with the production frontend URL:

```bash
FRONTEND_URL=$(gcloud run services describe ping-pong-frontend \
  --region=us-central1 --format='value(status.url)')

# Add this URL to CORS_ALLOWED_ORIGINS in your deployment
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Google Cloud                            │
│                                                             │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │   Cloud Run     │         │   Cloud Run     │           │
│  │   (Frontend)    │────────▶│   (Backend)     │           │
│  │   Nginx + Vue   │         │   Gunicorn +    │           │
│  │                 │         │   Django        │           │
│  └─────────────────┘         └────────┬────────┘           │
│                                       │                     │
│                                       ▼                     │
│                              ┌─────────────────┐           │
│                              │   Cloud SQL     │           │
│                              │   PostgreSQL    │           │
│                              └─────────────────┘           │
│                                                             │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │ Artifact        │         │ Secret          │           │
│  │ Registry        │         │ Manager         │           │
│  │ (Docker images) │         │ (Credentials)   │           │
│  └─────────────────┘         └─────────────────┘           │
│                                                             │
│  ┌─────────────────────────────────────────────┐           │
│  │             Cloud Build (CI/CD)              │           │
│  │  Triggered by GitHub push to main branch     │           │
│  └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Database Connection Issues
- Verify Cloud SQL instance is running
- Check that the Cloud Run service has the `--add-cloudsql-instances` flag
- Ensure the `DB_HOST` starts with `/cloudsql/`

### Secret Access Errors
- Verify secrets exist in Secret Manager
- Check IAM bindings for the service account

### Build Failures
- Check Cloud Build logs in the console
- Verify Dockerfile syntax
- Ensure all dependencies are in requirements.txt

### CORS Errors
- Add the production frontend URL to `CORS_ALLOWED_ORIGINS`
- Ensure `CSRF_TRUSTED_ORIGINS` includes the backend URL

---

## Cost Optimization Tips

1. **Cloud Run:** Set `min-instances: 0` to scale to zero when idle
2. **Cloud SQL:** Use the smallest tier (`db-f1-micro`) for development
3. **Artifact Registry:** Clean up old images periodically
4. **Cloud Build:** Use caching for faster builds
