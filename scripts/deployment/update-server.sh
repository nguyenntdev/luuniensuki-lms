#!/bin/bash
set -e

# =============================================================================
# Quick Update Script for Luuniensuki LMS
# Updates code and re-seeds the database without full rebuild
# =============================================================================

SERVER_IP="36.50.26.18"
SERVER_USER="root"
SSH_PORT="22"
REMOTE_DIR="/opt/luuniensuki-lms"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo "  Luuniensuki LMS - Quick Update Script"
echo "  Target: lms.histolab.icu ($SERVER_IP)"
echo -e "==========================================${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
SKIP_SEED=false
REBUILD=false
SEED_ONLY=false
SERVER_PASS=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-seed) SKIP_SEED=true ;;
        --rebuild) REBUILD=true ;;
        --seed-only) SEED_ONLY=true ;;
        --password=*) SERVER_PASS="${1#*=}" ;;
        -p) SERVER_PASS="$2"; shift ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --skip-seed         Skip database seeding"
            echo "  --rebuild           Full rebuild of containers"
            echo "  --seed-only         Only run seed (no file sync)"
            echo "  --password=PASS     Server password for sshpass"
            echo "  -p PASS             Server password for sshpass"
            echo "  --help              Show this help"
            echo ""
            echo "Example:"
            echo "  $0 --password=yourpassword --rebuild"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

# Set up SSH and rsync commands with sshpass if password provided
if [ -n "$SERVER_PASS" ]; then
    if ! command -v sshpass &> /dev/null; then
        echo -e "${RED}Error: sshpass is not installed${NC}"
        echo "Install with: brew install sshpass (macOS) or apt install sshpass (Linux)"
        exit 1
    fi
    SSH_CMD="sshpass -p '$SERVER_PASS' ssh -o StrictHostKeyChecking=no -p $SSH_PORT"
    RSYNC_SSH="sshpass -p '$SERVER_PASS' ssh -o StrictHostKeyChecking=no -p $SSH_PORT"
else
    SSH_CMD="ssh -p $SSH_PORT"
    RSYNC_SSH="ssh -p $SSH_PORT"
fi

run_ssh() {
    if [ -n "$SERVER_PASS" ]; then
        sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no -p "$SSH_PORT" "${SERVER_USER}@${SERVER_IP}" "$@"
    else
        ssh -p "$SSH_PORT" "${SERVER_USER}@${SERVER_IP}" "$@"
    fi
}

if [ "$SEED_ONLY" = true ]; then
    echo ""
    echo -e "${YELLOW}[Seed Only Mode] Running database seed...${NC}"

    run_ssh << 'REMOTE_SCRIPT'
set -e
cd /opt/luuniensuki-lms

echo "Running database seed..."
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod run --rm api python -m backend.seed

echo ""
echo "Seed complete!"
REMOTE_SCRIPT

    echo -e "${GREEN}Done!${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}[Step 1/4] Uploading updated files to server...${NC}"

if [ -n "$SERVER_PASS" ]; then
    sshpass -p "$SERVER_PASS" rsync -avz --progress \
        --exclude '.git' \
        --exclude '.venv' \
        --exclude '__pycache__' \
        --exclude '.pytest_cache' \
        --exclude 'frontend/node_modules' \
        --exclude 'frontend/.next' \
        --exclude 'frontend/test-results' \
        --exclude 'frontend/playwright-report' \
        --exclude '.env' \
        --exclude '.env.local' \
        --exclude '*.pyc' \
        --exclude 'certbot' \
        -e "ssh -o StrictHostKeyChecking=no -p $SSH_PORT" \
        ./ "${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}/"
else
    rsync -avz --progress \
        --exclude '.git' \
        --exclude '.venv' \
        --exclude '__pycache__' \
        --exclude '.pytest_cache' \
        --exclude 'frontend/node_modules' \
        --exclude 'frontend/.next' \
        --exclude 'frontend/test-results' \
        --exclude 'frontend/playwright-report' \
        --exclude '.env' \
        --exclude '.env.local' \
        --exclude '*.pyc' \
        --exclude 'certbot' \
        -e "ssh -p $SSH_PORT" \
        ./ "${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}/"
fi

echo ""
echo -e "${YELLOW}[Step 2/4] Updating containers...${NC}"

if [ "$REBUILD" = true ]; then
    run_ssh << 'REMOTE_SCRIPT'
set -e
cd /opt/luuniensuki-lms

echo "Rebuilding containers..."
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod down
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod up -d --build

echo "Waiting for services to start..."
sleep 20
REMOTE_SCRIPT
else
    run_ssh << 'REMOTE_SCRIPT'
set -e
cd /opt/luuniensuki-lms

echo "Rebuilding only api and web containers..."
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod up -d --build api web

echo "Waiting for services to start..."
sleep 10
REMOTE_SCRIPT
fi

if [ "$SKIP_SEED" = false ]; then
    echo ""
    echo -e "${YELLOW}[Step 3/4] Running database seed...${NC}"

    run_ssh << 'REMOTE_SCRIPT'
set -e
cd /opt/luuniensuki-lms

echo "Running database seed..."
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod run --rm api python -m backend.seed
REMOTE_SCRIPT
else
    echo ""
    echo -e "${BLUE}[Step 3/4] Skipping database seed (--skip-seed flag)${NC}"
fi

echo ""
echo -e "${YELLOW}[Step 4/4] Running health checks...${NC}"

run_ssh << 'REMOTE_SCRIPT'
cd /opt/luuniensuki-lms

echo ""
echo "Testing API health..."
curl -s "https://lms.histolab.icu/health" || echo "Health check (may need a moment)"

echo ""
echo ""
echo "Container status:"
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod ps
REMOTE_SCRIPT

echo ""
echo -e "${GREEN}=========================================="
echo "  Update Complete!"
echo -e "==========================================${NC}"
echo ""
echo -e "Site: ${GREEN}https://lms.histolab.icu${NC}"
echo ""
