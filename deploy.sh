#!/bin/bash
set -e

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="docker compose -f $BASE_DIR/docker-compose.yml -f $BASE_DIR/docker-compose.prod.yml"
NGINX_CONTAINER="base-nginx-1"
HEALTH_URL="http://localhost"
HEALTH_HOST="prod.cirrostrats.us"
HEALTH_INTERVAL=5
HEALTH_TIMEOUT=180  # max seconds to wait for frontend

switch_nginx() {
    local config="$1"
    docker cp "$BASE_DIR/nginx/$config" "$NGINX_CONTAINER:/etc/nginx/nginx.conf"
    docker exec "$NGINX_CONTAINER" nginx -t
    docker exec "$NGINX_CONTAINER" nginx -s reload
    echo "[nginx] Loaded $config"
}

echo "==> Switching to maintenance mode (cirrostrats.us -> stage)"
switch_nginx nginx.maintenance.conf

echo "==> Building images"
$COMPOSE build frontend backend

echo "==> Restarting frontend and backend"
$COMPOSE up -d --no-deps --force-recreate frontend backend

echo "==> Waiting for frontend to become healthy (timeout: ${HEALTH_TIMEOUT}s)"
elapsed=0
until curl -sf -o /dev/null -H "Host: $HEALTH_HOST" "$HEALTH_URL"; do
    if [ "$elapsed" -ge "$HEALTH_TIMEOUT" ]; then
        echo "[ERROR] Frontend did not come up after ${HEALTH_TIMEOUT}s. Staying in maintenance mode."
        exit 1
    fi
    echo "  Not ready yet... (${elapsed}s elapsed)"
    sleep "$HEALTH_INTERVAL"
    elapsed=$((elapsed + HEALTH_INTERVAL))
done

echo "==> Frontend healthy. Restoring production nginx config"
switch_nginx nginx.conf

echo "==> Deploy complete."
