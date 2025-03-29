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

Download the service account key as JSON and save it securely.

### 2. Configure Firebase Authentication

For production deployment on Cloud Run, you'll need to set up authentication 
using IAM:

1. Navigate to the Firebase Console
2. Go to Project Settings > Service Accounts
3. Generate a new private key for the Firebase Admin SDK

You have two options for providing Firebase credentials:

#### Option A: Using environment variables (Recommended for production)

Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable in Cloud Run to 
point to the mounted secret.

#### Option B: Using a service account file (Development only)

For local development, place your `service_account.json` file in the imp_tools 
root directory.

### 3. Build and Deploy to Cloud Run

Run the following commands to build and deploy:

```bash
# Navigate to the imp_tools directory
cd imp_tools

# Build the container image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/imp-tools

# Deploy to Cloud Run
gcloud run deploy imp-tools \
  --image gcr.io/YOUR_PROJECT_ID/imp-tools \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "BUNDLE_OUTPUT_DIR=/tmp/bundles"
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
  "collection_path": "imps/username/trophies2023",
  "save_bundle": false
}
```

- When `save_bundle` is `false` (default), returns the bundle data as JSON
- When `save_bundle` is `true`, saves the bundle to the specified output 
directory and returns metadata

### Download Bundle

```
POST /download-bundle
```

Request body:
```json
{
  "collection_path": "imps/username/trophies2023"
}
```

Returns the bundle as a downloadable JSON file.

### Generate All Bundles

```
POST /generate-all-bundles
```

Request body (all fields optional):
```json
{
  "year": 2023,
  "output_dir": "/tmp/bundles"
}
```

Generates bundles for all imp trophy collections and returns the list of 
generated files.

## Environment Variables

The service supports the following environment variables:

- `PORT`: HTTP port to listen on (set automatically by Cloud Run)
- `BUNDLE_OUTPUT_DIR`: Directory to save bundle files (default: "bundles")
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to the service account key file

## Testing Locally

To test locally before deploying:

```bash
# Build the Docker image
docker build -t imp-tools .

# Run the container
docker run -p 8080:8080 -v $(pwd)/service_account.json:/app/service_account.json imp-tools
```

Then access the API at http://localhost:8080/ 