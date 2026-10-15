#!/bin/bash
# Deploy nginx CORS configuration to server
# Server: vm01082101.bnixvps.io.vn (36.50.26.18)
# Usage: ./deploy-cors-auto.sh

set -euo pipefail

SERVER="${PROD_SSH_USER:-root}@${PROD_SSH_HOST:-36.50.26.18}"
REMOTE_PATH="${PROD_PATH:-/root/luuniensuki-lms}"

# Optional password file
SECRETS_FILE="${HOME}/.deploy-secrets"
if [[ -f "$SECRETS_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$SECRETS_FILE"
fi

echo "=== Deploying CORS Configuration to Server ==="
echo ""

run_scp() {
    local src="$1"
    local dest="$2"
    if [[ -n "${PROD_SSH_PASSWORD:-}" ]]; then
        if ! command -v sshpass &> /dev/null; then
            echo "PROD_SSH_PASSWORD set but sshpass is not installed." >&2
            exit 1
        fi
        SSHPASS="${PROD_SSH_PASSWORD}" sshpass -e scp -o StrictHostKeyChecking=accept-new "$src" "$dest"
    else
        scp -o StrictHostKeyChecking=accept-new "$src" "$dest"
    fi
}

run_ssh() {
    local cmd="$1"
    if [[ -n "${PROD_SSH_PASSWORD:-}" ]]; then
        if ! command -v sshpass &> /dev/null; then
            echo "PROD_SSH_PASSWORD set but sshpass is not installed." >&2
            exit 1
        fi
        SSHPASS="${PROD_SSH_PASSWORD}" sshpass -e ssh -o StrictHostKeyChecking=accept-new "${SERVER}" "$cmd"
    else
        ssh -o StrictHostKeyChecking=accept-new "${SERVER}" "$cmd"
    fi
}

# Copy nginx configs
echo "1. Uploading nginx configuration files..."
run_scp nginx-lms.conf "${SERVER}:${REMOTE_PATH}/nginx-lms.conf"
run_scp nginx-lms-histolab.conf "${SERVER}:${REMOTE_PATH}/nginx-lms-histolab.conf"

echo "2. Reloading nginx in Docker..."
run_ssh "cd ${REMOTE_PATH} && docker compose -f docker-compose.prod.yml exec -T nginx nginx -s reload"

echo ""
echo "=== CORS Configuration Deployed Successfully ==="
echo ""
echo "3. Testing CORS headers..."
curl -sI "https://lms.histolab.icu/assets/models/CAO-DINH-v1.glb" | grep -i "access-control" || true

echo ""
echo "Done!"

