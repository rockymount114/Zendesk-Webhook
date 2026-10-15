#!/bin/bash
set -e

APP_DIR="$HOME/docker/zendesk-webhook"

echo "========================================"
echo "Zendesk Webhook Deployment"
echo "========================================"

cd "$APP_DIR"

echo "[1/4] Checking Infisical..."
infisical run --env=prod -- sh -c 'echo "Infisical authentication OK"'

echo "[2/4] Pulling latest Docker image..."
docker compose pull zendesk-dashboard

echo "[3/4] Recreating container with latest secrets..."
infisical run --env=prod -- \
    docker compose up -d --pull always --force-recreate

echo "[4/4] Checking container..."
docker compose ps

echo ""
echo "Deployment completed."
