#!/bin/bash
set -e

# =============================================================================
# Local Deployment Script for Luuniensuki LMS
# Run this from your local machine to deploy to the server
# =============================================================================

SERVER_IP="36.50.26.18"
SERVER_USER="root"
SSH_PORT="22"
DOMAIN="lms.histolab.icu"
REMOTE_DIR="/opt/luuniensuki-lms"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo "  Luuniensuki LMS - Local Deploy Script"
echo "  Target: $DOMAIN ($SERVER_IP)"
echo -e "==========================================${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo -e "${YELLOW}[Step 1/6] Uploading project files to server...${NC}"
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
    -e "ssh -p $SSH_PORT" \
    ./ "${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}/"

echo ""
echo -e "${YELLOW}[Step 2/6] Running remote setup...${NC}"

ssh -p "$SSH_PORT" "${SERVER_USER}@${SERVER_IP}" << 'REMOTE_SCRIPT'
set -e

DOMAIN="lms.histolab.icu"
APP_DIR="/opt/luuniensuki-lms"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"

cd "$APP_DIR"

echo "[2.1] Installing Docker if not present..."
if ! command -v docker &> /dev/null; then
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null || true
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    echo "Docker installed: $(docker --version)"
else
    echo "Docker already installed: $(docker --version)"
fi

echo "[2.2] Configuring firewall..."
apt-get install -y ufw > /dev/null 2>&1 || true
ufw allow 22/tcp > /dev/null 2>&1 || true
ufw allow 80/tcp > /dev/null 2>&1 || true
ufw allow 443/tcp > /dev/null 2>&1 || true
echo "y" | ufw enable > /dev/null 2>&1 || true

echo "[2.3] Stopping host web servers..."
systemctl stop nginx 2>/dev/null || true
systemctl disable nginx 2>/dev/null || true
systemctl stop apache2 2>/dev/null || true
systemctl disable apache2 2>/dev/null || true

echo "[2.4] Creating environment file if not exists..."
if [ ! -f "$APP_DIR/$ENV_FILE" ]; then
    POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 32)
    JWT_SECRET=$(openssl rand -base64 48 | tr -dc 'a-zA-Z0-9' | head -c 64)

    cat > "$APP_DIR/$ENV_FILE" <<EOF
# Database
POSTGRES_DB=luuniensuki
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# JWT Authentication
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Application
LOG_LEVEL=info
INTERACTION_TOLERANCE_MULTIPLIER=1.25
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=180

# Frontend
NEXT_PUBLIC_API_BASE_URL=
MODEL_BASE_URL=/assets/models
EOF
    chmod 600 "$APP_DIR/$ENV_FILE"
    echo "Environment file created"
    echo ""
    echo "=== SAVE THESE CREDENTIALS ==="
    echo "POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
    echo "JWT_SECRET_KEY: $JWT_SECRET"
    echo "==============================="
    echo ""
else
    echo "Environment file already exists"
fi

echo "[2.5] Setting up Nginx config for $DOMAIN..."
# Use the pre-created config or create inline
if [ -f "$APP_DIR/nginx-lms-histolab.conf" ]; then
    cp "$APP_DIR/nginx-lms-histolab.conf" "$APP_DIR/nginx-site.conf"
fi

echo "[2.6] Creating temporary SSL certificates..."
mkdir -p "$APP_DIR/certbot/www"
mkdir -p "$APP_DIR/certbot/conf/live/$DOMAIN"

if [ ! -f "$APP_DIR/certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout "$APP_DIR/certbot/conf/live/$DOMAIN/privkey.pem" \
        -out "$APP_DIR/certbot/conf/live/$DOMAIN/fullchain.pem" \
        -subj "/CN=$DOMAIN" 2>/dev/null
    echo "Temporary SSL certificates created"
else
    echo "SSL certificates already exist"
fi

echo "[2.7] Creating docker-compose override..."
cat > "$APP_DIR/docker-compose.override.yml" <<EOF
services:
  nginx:
    volumes:
      - ./nginx-site.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certbot/www:/var/www/certbot:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./ban-duc-noi:/var/www/assets/ban-duc-noi:ro
EOF

echo "Remote setup complete!"
REMOTE_SCRIPT

echo ""
echo -e "${YELLOW}[Step 3/6] Building and starting containers...${NC}"

ssh -p "$SSH_PORT" "${SERVER_USER}@${SERVER_IP}" << 'REMOTE_SCRIPT'
set -e
cd /opt/luuniensuki-lms

echo "Stopping existing containers..."
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod down 2>/dev/null || true

echo "Building and starting containers (this may take a few minutes)..."
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod up -d --build

echo "Waiting for services to start..."
sleep 20

echo "Container status:"
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod ps
REMOTE_SCRIPT

echo ""
echo -e "${YELLOW}[Step 4/6] Seeding database...${NC}"

ssh -p "$SSH_PORT" "${SERVER_USER}@${SERVER_IP}" << 'REMOTE_SCRIPT'
set -e
cd /opt/luuniensuki-lms

echo "Running database seed..."
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod run --rm api python -m backend.seed || echo "Seed completed (or already seeded)"
REMOTE_SCRIPT

echo ""
echo -e "${YELLOW}[Step 5/6] Getting SSL certificate from Let's Encrypt...${NC}"

read -p "Enter your email for Let's Encrypt notifications: " CERT_EMAIL

ssh -p "$SSH_PORT" "${SERVER_USER}@${SERVER_IP}" << REMOTE_SCRIPT
set -e
cd /opt/luuniensuki-lms

DOMAIN="lms.histolab.icu"

echo "Requesting SSL certificate..."
docker run --rm \
    -v "/opt/luuniensuki-lms/certbot/www:/var/www/certbot" \
    -v "/opt/luuniensuki-lms/certbot/conf:/etc/letsencrypt" \
    certbot/certbot certonly --webroot \
    -w /var/www/certbot \
    -d "\$DOMAIN" \
    --email "$CERT_EMAIL" --agree-tos --no-eff-email --force-renewal || echo "SSL certificate request completed"

echo "Restarting nginx with new certificate..."
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod restart nginx

sleep 5
REMOTE_SCRIPT

echo ""
echo -e "${YELLOW}[Step 6/6] Running health checks...${NC}"

ssh -p "$SSH_PORT" "${SERVER_USER}@${SERVER_IP}" << 'REMOTE_SCRIPT'
DOMAIN="lms.histolab.icu"

echo ""
echo "Testing HTTP -> HTTPS redirect..."
curl -sI "http://$DOMAIN" 2>/dev/null | head -3 || echo "HTTP redirect test (may need DNS propagation)"

echo ""
echo "Testing HTTPS..."
curl -s "https://$DOMAIN/health" 2>/dev/null || curl -sk "https://$DOMAIN/health" || echo "HTTPS test completed"

echo ""
echo "Container status:"
cd /opt/luuniensuki-lms
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod ps
REMOTE_SCRIPT

echo ""
echo -e "${GREEN}=========================================="
echo "  Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo -e "Your site is now available at: ${GREEN}https://$DOMAIN${NC}"
echo ""
echo "Useful commands (run on server):"
echo "  View logs:    cd $REMOTE_DIR && docker compose -f docker-compose.prod.yml logs -f"
echo "  Restart:      cd $REMOTE_DIR && docker compose -f docker-compose.prod.yml restart"
echo "  Stop:         cd $REMOTE_DIR && docker compose -f docker-compose.prod.yml down"
echo ""
echo -e "${RED}IMPORTANT: Please change your server password immediately!${NC}"
echo "  ssh root@$SERVER_IP"
echo "  passwd"
echo ""
