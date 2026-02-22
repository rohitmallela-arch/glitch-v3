#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-theglitchapp}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-glitch-webhook}"

echo "=== SERVICE / TRAFFIC (prove active revision) ==="
gcloud run services describe "$SERVICE" --project "$PROJECT_ID" --region "$REGION" --format=json \
| jq -r '{name:.metadata.name,url:.status.url,traffic:.status.traffic}'

ACTIVE_REV="$(gcloud run services describe "$SERVICE" --project "$PROJECT_ID" --region "$REGION" --format=json \
| jq -r '.status.traffic[] | select(.percent==100) | .revisionName')"
echo "ACTIVE_REV=$ACTIVE_REV"

echo
echo "=== ENV KEYS (active revision) ==="
ENV_KEYS="$(gcloud run revisions describe "$ACTIVE_REV" --project "$PROJECT_ID" --region "$REGION" --format=json \
| jq -r '.spec.containers[0].env[]?.name' | sort)"
echo "$ENV_KEYS"

required=(
  OPERATOR_AUTH_AUDIENCE
  APP_BASE_URL
  STRIPE_API_KEY
  STRIPE_WEBHOOK_SECRET
  STRIPE_PRICE_ID
  TELEGRAM_BOT_TOKEN
)

echo
echo "=== REQUIRED KEYS CHECK ==="
missing=0
for k in "${required[@]}"; do
  if ! echo "$ENV_KEYS" | grep -qx "$k"; then
    echo "MISSING: $k"
    missing=1
  else
    echo "OK: $k"
  fi
done

if [ "$missing" -ne 0 ]; then
  echo "FAIL: missing required env keys"
  exit 2
fi

echo "PASS: required env keys present"
