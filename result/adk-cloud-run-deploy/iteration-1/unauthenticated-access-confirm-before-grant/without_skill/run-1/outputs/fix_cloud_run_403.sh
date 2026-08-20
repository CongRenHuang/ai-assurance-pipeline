#!/usr/bin/env bash
# Makes an ADK Cloud Run demo service publicly reachable (unauthenticated).
#
# Cloud Run requires the caller to hold roles/run.invoker by default.
# `adk deploy cloud_run` does not grant this to allUsers unless you pass
# an --allow_unauthenticated-style flag, so anonymous curl/browser hits
# get a 403 straight from Cloud Run's IAM layer.
#
# Usage:
#   ./fix_cloud_run_403.sh SERVICE_NAME REGION [PROJECT_ID]
#
# Requires: gcloud CLI installed and authenticated (gcloud auth login),
# and an active project with the Cloud Run Admin / IAM permission to
# modify the service's IAM policy (roles/run.admin or equivalent).

set -euo pipefail

SERVICE_NAME="${1:?Usage: $0 SERVICE_NAME REGION [PROJECT_ID]}"
REGION="${2:?Usage: $0 SERVICE_NAME REGION [PROJECT_ID]}"
PROJECT_ID="${3:-$(gcloud config get-value project 2>/dev/null)}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "No project set. Pass PROJECT_ID as the 3rd argument or run: gcloud config set project YOUR_PROJECT" >&2
  exit 1
fi

echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region:  $REGION"
echo

echo "== Current IAM policy on the service =="
gcloud run services get-iam-policy "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format=yaml

echo
echo "== Granting roles/run.invoker to allUsers =="
gcloud run services add-iam-policy-binding "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --member="allUsers" \
  --role="roles/run.invoker"

echo
echo "== Service URL =="
gcloud run services describe "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format='value(status.url)'

cat <<'EOF'

If the binding above fails with something like
"One or more users named in the policy do not belong to a permitted customer",
your GCP organization enforces the "Domain restricted sharing"
(constraints/iam.allowedPolicyMemberDomains) org policy, which blocks
allUsers/allAuthenticatedUsers entirely. In that case a public demo URL
isn't possible under that org's policy without an exception from an org
admin — the workaround is to front the service with a proxy (e.g. Cloud
Run + Identity-Aware Proxy for specific users, or Cloud Load Balancing
with a Cloud Armor/IAP setup) rather than making the Cloud Run service
itself public.
EOF
