#!/bin/bash
set -e

# =============================================================================
# Deployment Script for Luuniensuki LMS
# Target: lms.histolab.icu
# Server: 36.50.26.18
# =============================================================================

DOMAIN="lms.histolab.icu"
APP_DIR="/opt/luuniensuki-lms"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"

echo "=========================================="
echo "  Luuniensuki LMS Deployment Script"
echo "  Domain: $DOMAIN"
echo "=========================================="

# -----------------------------------------------------------------------------
# Step 1: Update system and install Docker
# -----------------------------------------------------------------------------
install_docker() {
    echo "[1/10] Installing Docker..."

    apt-get update -y
    apt-get install -y ca-certificates curl gnupg lsb-release

    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null || true
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Add the repository to Apt sources
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Start Docker
    systemctl enable docker
    systemctl start docker

    echo "Docker installed: $(docker --version)"
}

# -----------------------------------------------------------------------------
# Step 2: Configure firewall
# -----------------------------------------------------------------------------
configure_firewall() {
    echo "[2/10] Configuring firewall..."

    # Install ufw if not present
    apt-get install -y ufw || true

    # Allow SSH, HTTP, HTTPS
    ufw allow 22/tcp || true
    ufw allow 80/tcp || true
    ufw allow 443/tcp || true

    # Enable firewall (if not already)
    echo "y" | ufw enable || true

    echo "Firewall configured."
}

# -----------------------------------------------------------------------------
# Step 3: Stop any existing nginx/apache on host
# -----------------------------------------------------------------------------
stop_host_webservers() {
    echo "[3/10] Stopping host web servers (if any)..."

    systemctl stop nginx 2>/dev/null || true
    systemctl disable nginx 2>/dev/null || true
    systemctl stop apache2 2>/dev/null || true
    systemctl disable apache2 2>/dev/null || true

    # Check if ports are free
    if ss -tulpn | grep -E ":(80|443)\b" | grep -v docker; then
        echo "WARNING: Ports 80/443 may still be in use!"
    else
        echo "Ports 80 and 443 are available."
    fi
}

# -----------------------------------------------------------------------------
# Step 4: Create app directory
# -----------------------------------------------------------------------------
create_app_directory() {
    echo "[4/10] Creating app directory..."

    mkdir -p "$APP_DIR"
    cd "$APP_DIR"

    echo "App directory: $APP_DIR"
}

# -----------------------------------------------------------------------------
# Step 5: Create environment file
# -----------------------------------------------------------------------------
create_env_file() {
    echo "[5/10] Creating environment file..."

    # Generate secure passwords
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

# Frontend (leave empty for same-origin API calls through Nginx)
NEXT_PUBLIC_API_BASE_URL=
MODEL_BASE_URL=/assets/models
EOF

    chmod 600 "$APP_DIR/$ENV_FILE"

    echo "Environment file created at $APP_DIR/$ENV_FILE"
    echo ""
    echo "IMPORTANT: Save these credentials securely!"
    echo "  POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
    echo "  JWT_SECRET_KEY: $JWT_SECRET"
    echo ""
}

# -----------------------------------------------------------------------------
# Step 6: Update nginx config for new domain
# -----------------------------------------------------------------------------
update_nginx_config() {
    echo "[6/10] Updating Nginx config for $DOMAIN..."

    # Use the new nginx config file
    if [ -f "$APP_DIR/nginx-lms-histolab.conf" ]; then
        cp "$APP_DIR/nginx-lms-histolab.conf" "$APP_DIR/nginx-site.conf"
    else
        # Create nginx config inline if file doesn't exist
        cat > "$APP_DIR/nginx-site.conf" <<'NGINX_EOF'
upstream api_upstream {
  server api:8000;
  keepalive 32;
}

upstream web_upstream {
  server web:3000;
  keepalive 32;
}

server {
  listen 80;
  server_name lms.histolab.icu;

  location /.well-known/acme-challenge/ {
    root /var/www/certbot;
  }

  location / {
    return 301 https://$host$request_uri;
  }
}

server {
  listen 443 ssl http2;
  server_name lms.histolab.icu;

  ssl_certificate     /etc/letsencrypt/live/lms.histolab.icu/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/lms.histolab.icu/privkey.pem;

  ssl_session_timeout 1d;
  ssl_session_cache shared:SSL:10m;
  ssl_session_tickets off;
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_prefer_server_ciphers off;

  # Security headers
  add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
  add_header X-Frame-Options "SAMEORIGIN" always;
  add_header X-Content-Type-Options "nosniff" always;
  add_header Referrer-Policy "strict-origin-when-cross-origin" always;
  add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

  client_max_body_size 50m;

  proxy_http_version 1.1;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_connect_timeout 10s;
  proxy_send_timeout 180s;
  proxy_read_timeout 180s;

  gzip on;
  gzip_comp_level 5;
  gzip_min_length 1024;
  gzip_proxied any;
  gzip_vary on;
  gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml application/xml+rss image/svg+xml;
  gzip_disable "msie6";

  location ^~ /api/ {
    proxy_pass http://api_upstream;
  }

  location = /health {
    proxy_pass http://api_upstream;
  }

  location ^~ /assets/models/ {
    proxy_ssl_server_name on;
    proxy_ssl_name store.histolab.icu;
    proxy_set_header Host store.histolab.icu;
    proxy_buffering off;
    proxy_pass https://store.histolab.icu/;
    access_log off;
    expires 30d;
    add_header Cache-Control "public, max-age=2592000, immutable";
  }

  location ^~ /assets/ {
    root /var/www;
    access_log off;
    expires 30d;
    add_header Cache-Control "public, max-age=2592000, immutable";
  }

  location ^~ /motifs/ {
    proxy_pass http://api_upstream;
  }

  location ^~ /progress/ {
    proxy_pass http://api_upstream;
  }

  location / {
    if ($request_method !~ ^(GET|HEAD|OPTIONS)$) {
      return 405;
    }
    proxy_pass http://web_upstream;
  }
}
NGINX_EOF
    fi

    echo "Nginx config created."
}

# -----------------------------------------------------------------------------
# Step 7: Create temporary SSL certificates
# -----------------------------------------------------------------------------
create_temp_certs() {
    echo "[7/10] Creating temporary SSL certificates..."

    mkdir -p "$APP_DIR/certbot/www"
    mkdir -p "$APP_DIR/certbot/conf/live/$DOMAIN"

    # Generate self-signed certificate for initial startup
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout "$APP_DIR/certbot/conf/live/$DOMAIN/privkey.pem" \
        -out "$APP_DIR/certbot/conf/live/$DOMAIN/fullchain.pem" \
        -subj "/CN=$DOMAIN" 2>/dev/null

    echo "Temporary SSL certificates created."
}

# -----------------------------------------------------------------------------
# Step 8: Update docker-compose for new nginx config
# -----------------------------------------------------------------------------
create_docker_compose_override() {
    echo "[8/10] Creating docker-compose override..."

    cat > "$APP_DIR/docker-compose.override.yml" <<EOF
services:
  nginx:
    volumes:
      - ./nginx-site.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certbot/www:/var/www/certbot:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./ban-duc-noi:/var/www/assets/ban-duc-noi:ro
EOF

    echo "Docker compose override created."
}

# -----------------------------------------------------------------------------
# Step 9: Build and start containers
# -----------------------------------------------------------------------------
start_containers() {
    echo "[9/10] Building and starting containers..."

    cd "$APP_DIR"

    # Build and start
    docker compose -f "$COMPOSE_FILE" -f docker-compose.override.yml --env-file "$ENV_FILE" up -d --build

    # Wait for services to be healthy
    echo "Waiting for services to start..."
    sleep 15

    # Check status
    docker compose -f "$COMPOSE_FILE" -f docker-compose.override.yml --env-file "$ENV_FILE" ps

    echo "Containers started."
}

# -----------------------------------------------------------------------------
# Step 10: Seed database
# -----------------------------------------------------------------------------
seed_database() {
    echo "[10/10] Seeding database..."

    cd "$APP_DIR"

    # Run database migrations and seed
    docker compose -f "$COMPOSE_FILE" -f docker-compose.override.yml --env-file "$ENV_FILE" run --rm api python -m backend.seed || true

    echo "Database seeded."
}

# -----------------------------------------------------------------------------
# Get real SSL certificate
# -----------------------------------------------------------------------------
get_ssl_certificate() {
    echo "Getting SSL certificate from Let's Encrypt..."

    cd "$APP_DIR"

    read -p "Enter your email for Let's Encrypt notifications: " CERT_EMAIL

    docker run --rm \
        -v "$APP_DIR/certbot/www:/var/www/certbot" \
        -v "$APP_DIR/certbot/conf:/etc/letsencrypt" \
        certbot/certbot certonly --webroot \
        -w /var/www/certbot \
        -d "$DOMAIN" \
        --email "$CERT_EMAIL" --agree-tos --no-eff-email

    # Restart nginx to use new cert
    docker compose -f "$COMPOSE_FILE" -f docker-compose.override.yml --env-file "$ENV_FILE" restart nginx

    echo "SSL certificate installed!"
}

# -----------------------------------------------------------------------------
# Health check
# -----------------------------------------------------------------------------
health_check() {
    echo ""
    echo "Running health checks..."
    echo ""

    # Check HTTP redirect
    echo "Testing HTTP redirect..."
    curl -sI "http://$DOMAIN" | head -3 || echo "HTTP check failed (might need DNS propagation)"

    echo ""
    echo "Testing HTTPS (with self-signed cert)..."
    curl -sk "https://$DOMAIN/health" || echo "HTTPS check failed"

    echo ""
    echo "=========================================="
    echo "  Deployment Complete!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Verify DNS is pointing to this server"
    echo "  2. Run: ./deploy-lms.sh ssl"
    echo "     to get a real SSL certificate"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    docker compose -f $COMPOSE_FILE logs -f"
    echo "  Restart:      docker compose -f $COMPOSE_FILE restart"
    echo "  Stop:         docker compose -f $COMPOSE_FILE down"
    echo ""
    echo "Access your site at: https://$DOMAIN"
    echo "(Use -k flag with curl until SSL cert is installed)"
    echo ""
}

# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------
main() {
    if [ "$1" == "ssl" ]; then
        get_ssl_certificate
        exit 0
    fi

    if [ "$1" == "check" ]; then
        health_check
        exit 0
    fi

    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        echo "Please run as root (sudo)"
        exit 1
    fi

    echo "This script will deploy Luuniensuki LMS to this server."
    echo "Domain: $DOMAIN"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi

    install_docker
    configure_firewall
    stop_host_webservers
    create_app_directory

    echo ""
    echo "Please upload the project files to $APP_DIR"
    echo "You can use: rsync -az --exclude '.git' --exclude 'node_modules' --exclude '.next' ./ root@36.50.26.18:$APP_DIR/"
    echo ""
    read -p "Press Enter when files are uploaded..."

    create_env_file
    update_nginx_config
    create_temp_certs
    create_docker_compose_override
    start_containers
    seed_database
    health_check
}

main "$@"
