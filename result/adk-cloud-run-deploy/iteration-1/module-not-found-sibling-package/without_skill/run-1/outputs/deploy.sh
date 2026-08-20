#!/usr/bin/env bash
# Deploys my_agent + shared_lib to Cloud Run using the Dockerfile in this
# folder, instead of `adk deploy cloud_run` (which only packages the
# single agent directory and drops sibling packages like shared_lib/).
#
# Usage:
#   1. Copy Dockerfile and this script into the parent directory that
#      contains both my_agent/ and shared_lib/.
#   2. Set PROJECT_ID, REGION, SERVICE_NAME below or export them.
#   3. ./deploy.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID env var}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-my-agent-service}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${SERVICE_NAME}"

if [[ ! -d my_agent || ! -d shared_lib ]]; then
  echo "error: run this from the parent directory containing both my_agent/ and shared_lib/" >&2
  exit 1
fi

gcloud builds submit . \
  --project "${PROJECT_ID}" \
  --tag "${IMAGE}"

gcloud run deploy "${SERVICE_NAME}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --image "${IMAGE}" \
  --allow-unauthenticated
