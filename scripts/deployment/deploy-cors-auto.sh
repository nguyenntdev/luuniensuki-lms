#!/bin/bash
# Deploy nginx CORS configuration to server using sshpass
# Server: vm01082101.bnixvps.io.vn (36.50.26.18)
# Usage: ./deploy-cors-auto.sh

set -e

SERVER="root@36.50.26.18"
PASSWORD="3Ys29nxTpAMmS7cF"
REMOTE_PATH="/root/luuniensuki-lms"

echo "=== Deploying CORS Configuration to Server ==="
echo ""

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "sshpass not found. Installing with brew..."
    brew install hudochenkov/sshpass/sshpass || {
        echo "Failed to install sshpass. Please install manually or use SSH key auth."
        echo ""
        echo "Manual commands to run on server:"
        echo "  cd ${REMOTE_PATH}"
        echo "  # Upload nginx-lms.conf and nginx-lms-histolab.conf"
        echo "  docker compose -f docker-compose.prod.yml exec nginx nginx -s reload"
        exit 1
    }
fi

# Copy nginx configs
echo "1. Uploading nginx configuration files..."
sshpass -p "${PASSWORD}" scp -o StrictHostKeyChecking=no nginx-lms.conf ${SERVER}:${REMOTE_PATH}/nginx-lms.conf
sshpass -p "${PASSWORD}" scp -o StrictHostKeyChecking=no nginx-lms-histolab.conf ${SERVER}:${REMOTE_PATH}/nginx-lms-histolab.conf

echo "2. Reloading nginx in Docker..."
sshpass -p "${PASSWORD}" ssh -o StrictHostKeyChecking=no ${SERVER} "cd ${REMOTE_PATH} && docker compose -f docker-compose.prod.yml exec -T nginx nginx -s reload"

echo ""
echo "=== CORS Configuration Deployed Successfully ==="
echo ""
echo "3. Testing CORS headers..."
curl -sI "https://lms.histolab.icu/assets/models/CAO-DINH-v1.glb" | grep -i "access-control"

echo ""
echo "Done!"

