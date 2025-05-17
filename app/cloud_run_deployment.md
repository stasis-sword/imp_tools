# Deploying imp_tools to Google Cloud Run

This document provides instructions for deploying the imp_tools bundle generator 
service to Google Cloud Run. If for some reason you want to do that.

## Prerequisites

1. A Google Cloud Platform account with billing enabled
2. Google Cloud SDK installed on your local machine
3. Docker installed on your local machine
4. Firebase service account credentials with Firestore read/write permissions

## Setup Steps

### 1. Configure Service Account

Create a service account in your Google Cloud project with the following roles:
- Cloud Run Admin
- Storage Admin
- Artifact Registry Reader/Writer
- Firestore Reader/Writer

Download the service account key as JSON and save it securely.

### 2. Configure Firebase Authentication

For production deployment on Cloud Run, you have three options for providing Firebase credentials:

#### Option A: Using Secret Manager (Recommended for production)

1. Create a secret in Google Cloud Secret Manager:
   ```bash
   gcloud secrets create firebase-credentials --data-file=service_account.json
   ```

2. Grant access to your Cloud Run service account:
   ```bash
   gcloud secrets add-iam-policy-binding firebase-credentials \
     --member=serviceAccount:YOUR-SERVICE-ACCOUNT@YOUR-PROJECT.iam.gserviceaccount.com \
     --role=roles/secretmanager.secretAccessor
   ```

3. Mount the secret when deploying:
   ```bash
   gcloud run deploy imp-tools \
     --image gcr.io/YOUR_PROJECT_ID/imp-tools \
     --set-secrets=FIREBASE_SERVICE_ACCOUNT=firebase-credentials:latest
   ```

#### Option B: Using IAM (Simplest for production)

1. Set up the service account with the appropriate IAM roles:
   - Ensure your Cloud Run service account has the required Firebase Admin SDK permissions
   - Use Application Default Credentials (ADC) automatically

2. Deploy without specifying credentials:
   ```bash
   gcloud run deploy imp-tools --image gcr.io/YOUR_PROJECT_ID/imp-tools
   ```

#### Option C: Using a service account file (Development only)

For local development, place your `service_account.json` file in the imp_tools 
root directory.

**Note**: Never include your service account file in your Docker image or source control. The Dockerfile is set up to handle the absence of this file.

### 3. Build and Deploy to Cloud Run

Run the following commands to build and deploy:

```powershell
# Navigate to the imp_tools directory
cd imp_tools

# Build the container image using Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/imp-tools

# Deploy to Cloud Run
# the ` syntax is for powershell; use \ in bash instead
gcloud run deploy imp-tools `
  --image gcr.io/YOUR_PROJECT_ID/imp-tools `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1
```

Replace `YOUR_PROJECT_ID` with your Google Cloud project ID.

## API Endpoints

The service provides the following endpoints:

### Health Check

```
GET /health
```

Returns status 200 if the service is running properly.

### Generate Bundle for a Collection

```
POST /generate-bundle
```

Request body:
```json
{
  "collection_path": "imps/username/trophies2025",
  "save_bundle": false
}
```

- When `save_bundle` is `false` (default), returns the bundle data as JSON
- When `save_bundle` is `true`, saves the bundle to the specified output 
directory and returns metadata

### Generate All Bundles

```
POST /generate-all-bundles
```

Request body (all fields optional):
```json
{
  "year": 2025,
  "output_dir": "/tmp/bundles"
}
```

Generates bundles for all imp trophy collections and returns the list of 
generated files.

### Random Flag

```
GET /images/random-flag
```

Redirects the requests to a random flag url selected from a list of flags hosted on the Something Awful server.

### Random Flag with Creator

```
GET /images/random-flag-with-creator
```

Redirects the requests to a random flag url selected from a list of flags hosted on the Something Awful server. Appends the creator of the flag to the end of the url as a parameter query, e.g. `flag-name?by=Arch Nemesis`.

## Environment Variables

The service supports the following environment variables:

- `PORT`: HTTP port to listen on (set automatically by Cloud Run)
- `FIREBASE_SERVICE_ACCOUNT`: Path to the service account key file (if mounted as a secret)

## Troubleshooting

### Authentication Errors

If you encounter Firebase authentication errors:

1. Check that your service account has the necessary permissions
2. Verify that the secret is properly mounted or IAM roles are correctly assigned
3. Check the Cloud Run logs for detailed error messages

## Testing Locally

To test locally before deploying:

### On macOS/Linux:

```bash
# Build the Docker image
docker build -t imp-tools .

# Run the container (using a local service account file)
docker run -p 8080:8080 -v $(pwd)/service_account.json:/app/service_account.json imp-tools

# Or without a service account file (if using Application Default Credentials)
docker run -p 8080:8080 -v ~/.config/gcloud:/root/.config/gcloud imp-tools
```

### On Windows (PowerShell):

```powershell
# Build the Docker image
docker build -t imp-tools .

# Run the container (using a local service account file)
docker run -p 8080:8080 -v ${PWD}/service_account.json:/app/service_account.json imp-tools

# Or without a service account file (if using Application Default Credentials)
docker run -p 8080:8080 -v $env:USERPROFILE\.config\gcloud:/root/.config/gcloud imp-tools
```

Then access the API at http://localhost:8080/ 