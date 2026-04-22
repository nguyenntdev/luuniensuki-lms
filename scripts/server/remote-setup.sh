#!/bin/bash
set -e

# =============================================================================
# Remote Setup Script for Luuniensuki LMS
# Run this script ON THE SERVER after uploading the project files
# =============================================================================

DOMAIN="lms.histolab.icu"
APP_DIR="/opt/luuniensuki-lms"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"

echo "=========================================="
echo "  Luuniensuki LMS - Server Setup Script"
echo "  Domain: $DOMAIN"
echo "=========================================="

cd "$APP_DIR"

# Step 1: Install Docker
echo ""
echo "=== [1/8] Installing Docker ==="
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
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
    echo "Docker installed successfully!"
else
    echo "Docker already installed."
fi
echo "Docker version: $(docker --version)"

# Step 2: Configure firewall
echo ""
echo "=== [2/8] Configuring firewall ==="
apt-get install -y ufw > /dev/null 2>&1 || true
ufw allow 22/tcp > /dev/null 2>&1 || true
ufw allow 80/tcp > /dev/null 2>&1 || true
ufw allow 443/tcp > /dev/null 2>&1 || true
echo "y" | ufw enable > /dev/null 2>&1 || true
echo "Firewall configured (ports 22, 80, 443 open)"

# Step 3: Stop host web servers
echo ""
echo "=== [3/8] Stopping host web servers ==="
systemctl stop nginx 2>/dev/null || true
systemctl disable nginx 2>/dev/null || true
systemctl stop apache2 2>/dev/null || true
systemctl disable apache2 2>/dev/null || true
echo "Host web servers stopped"

# Step 4: Create environment file
echo ""
echo "=== [4/8] Creating environment file ==="
if [ ! -f "$APP_DIR/$ENV_FILE" ]; then
    POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 32)
    JWT_SECRET=$(openssl rand -base64 48 | tr -dc 'a-zA-Z0-9' | head -c 64)

    cat > "$APP_DIR/$ENV_FILE" << ENVEOF
POSTGRES_DB=luuniensuki
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

LOG_LEVEL=info
INTERACTION_TOLERANCE_MULTIPLIER=1.25
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=180

NEXT_PUBLIC_API_BASE_URL=
MODEL_BASE_URL=/assets/models
ENVEOF

    chmod 600 "$APP_DIR/$ENV_FILE"
    echo "Environment file created!"
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  SAVE THESE CREDENTIALS SECURELY!                             ║"
    echo "╠════════════════════════════════════════════════════════════════╣"
    echo "║  POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
    echo "║  JWT_SECRET_KEY: $JWT_SECRET"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
else
    echo "Environment file already exists, skipping..."
fi

# Step 5: Setup Nginx config
echo ""
echo "=== [5/8] Setting up Nginx config ==="
if [ -f "$APP_DIR/nginx-lms-histolab.conf" ]; then
    cp "$APP_DIR/nginx-lms-histolab.conf" "$APP_DIR/nginx-site.conf"
    echo "Nginx config copied"
else
    echo "ERROR: nginx-lms-histolab.conf not found!"
    exit 1
fi

# Step 6: Create temporary SSL certificates
echo ""
echo "=== [6/8] Creating temporary SSL certificates ==="
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

# Step 7: Create docker-compose override
echo ""
echo "=== [7/8] Creating docker-compose override ==="
cat > "$APP_DIR/docker-compose.override.yml" << OVERRIDEEOF
services:
  nginx:
    volumes:
      - ./nginx-site.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certbot/www:/var/www/certbot:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./ban-duc-noi:/var/www/assets/ban-duc-noi:ro
OVERRIDEEOF
echo "Docker compose override created"

# Step 8: Build and start containers
echo ""
echo "=== [8/8] Building and starting containers ==="
echo "This may take several minutes..."

docker compose -f "$COMPOSE_FILE" -f docker-compose.override.yml --env-file "$ENV_FILE" down 2>/dev/null || true
docker compose -f "$COMPOSE_FILE" -f docker-compose.override.yml --env-file "$ENV_FILE" up -d --build

echo ""
echo "Waiting for services to start (30 seconds)..."
sleep 30

echo ""
echo "Container status:"
docker compose -f "$COMPOSE_FILE" -f docker-compose.override.yml --env-file "$ENV_FILE" ps

# Seed database
echo ""
echo "=== Seeding database ==="
docker compose -f "$COMPOSE_FILE" -f docker-compose.override.yml --env-file "$ENV_FILE" run --rm api python -m backend.seed || echo "Seed completed (or already seeded)"

# Health check
echo ""
echo "=== Running health check ==="
sleep 5
curl -sk "https://localhost/health" || curl -s "http://localhost:8000/health" || echo "Health check - waiting for services..."

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Next step: Get SSL certificate from Let's Encrypt"
echo "Run: ./get-ssl.sh"
echo ""
echo "Your site will be available at: https://$DOMAIN"
echo "(Currently using self-signed cert until Let's Encrypt cert is obtained)"
echo ""
