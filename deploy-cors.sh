#!/bin/bash
# Deploy nginx CORS configuration to server
# Server: vm01082101.bnixvps.io.vn (36.50.26.18)

set -e

SERVER="root@36.50.26.18"
REMOTE_PATH="/root/luuniensuki-lms"

echo "=== Deploying CORS Configuration to Server ==="
echo ""

# Copy nginx configs
echo "1. Uploading nginx configuration files..."
scp -o StrictHostKeyChecking=no nginx-lms.conf ${SERVER}:${REMOTE_PATH}/nginx-lms.conf
scp -o StrictHostKeyChecking=no nginx-lms-histolab.conf ${SERVER}:${REMOTE_PATH}/nginx-lms-histolab.conf

echo "2. Reloading nginx in Docker..."
ssh -o StrictHostKeyChecking=no ${SERVER} "cd ${REMOTE_PATH} && docker compose -f docker-compose.prod.yml exec nginx nginx -s reload"

echo ""
echo "=== CORS Configuration Deployed Successfully ==="
echo ""
echo "Testing CORS headers:"
echo "  curl -I https://lms.histolab.icu/assets/models/CAO-DINH-v1.glb"
echo ""
echo "Expected headers:"
echo "  Access-Control-Allow-Origin: *"
echo "  Access-Control-Allow-Methods: GET, OPTIONS"
echo "  Access-Control-Allow-Headers: Origin, Content-Type, Accept, Range"

