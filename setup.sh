#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/luuniensuki-lms}"
REPO_URL="${REPO_URL:-}"
REPO_BRANCH="${REPO_BRANCH:-main}"
DOMAIN="${DOMAIN:-lms.histolab.icu}"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 1; }
}

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root (or via sudo)." >&2
  exit 1
fi

echo "[1/7] Installing base packages..."
apt-get update -y
apt-get install -y ca-certificates curl git gnupg lsb-release openssl

echo "[2/7] Installing Docker Engine + Compose plugin..."
if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" \
    > /etc/apt/sources.list.d/docker.list

  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

need docker
docker version >/dev/null

echo "[3/7] Fetching code..."
mkdir -p "$(dirname "$APP_DIR")"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch --all --prune
  git -C "$APP_DIR" checkout "$REPO_BRANCH"
  git -C "$APP_DIR" pull --ff-only
else
  if [ -z "$REPO_URL" ]; then
    echo "Set REPO_URL to your git repo URL (e.g. export REPO_URL=https://github.com/you/luuniensuki-lms.git)" >&2
    exit 1
  fi
  git clone --branch "$REPO_BRANCH" --depth 1 "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

echo "[4/7] Creating .env.prod (if missing)..."
if [ ! -f .env.prod ]; then
  POSTGRES_DB="${POSTGRES_DB:-luuniensuki}"
  POSTGRES_USER="${POSTGRES_USER:-postgres}"
  POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -hex 16)}"
  JWT_SECRET_KEY="${JWT_SECRET_KEY:-$(openssl rand -hex 32)}"

  cat > .env.prod <<EOF
# Domain
DOMAIN=${DOMAIN}

# Postgres
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# API
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=60

# Optional runtime config
LOG_LEVEL=info
INTERACTION_TOLERANCE_MULTIPLIER=1.25
EOF

  chmod 600 .env.prod
  echo "Created .env.prod (chmod 600)."
else
  echo "Found existing .env.prod; leaving as-is."
fi

if [ ! -f "frontend/package.json" ]; then
  echo "WARNING: frontend/package.json not found; the 'web' service build may fail." >&2
fi

echo "[5/7] Ensuring TLS directory exists (dummy cert for first boot)..."
mkdir -p "certbot/www" "certbot/conf/live/${DOMAIN}"
if [ ! -f "certbot/conf/live/${DOMAIN}/fullchain.pem" ] || [ ! -f "certbot/conf/live/${DOMAIN}/privkey.pem" ]; then
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "certbot/conf/live/${DOMAIN}/privkey.pem" \
    -out "certbot/conf/live/${DOMAIN}/fullchain.pem" \
    -subj "/CN=${DOMAIN}" >/dev/null 2>&1 || true
fi

echo "[6/7] Starting production stack..."
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build db api web nginx

echo "[7/7] Initializing DB schema + seed data..."
docker compose -f docker-compose.prod.yml --env-file .env.prod run --rm api python -m backend.seed

echo "Next steps (real SSL)..."
cat <<EOF

Stack is up:
  - HTTP:  http://${DOMAIN}
  - API:   http://${DOMAIN}/api/v1/auth/me (after you proxy SSL or keep HTTP)

To enable HTTPS (recommended):
  1) Temporarily keep port 80 open (already mapped by nginx).
  2) Run Certbot (webroot) to generate certs into ./certbot/conf:

     docker run --rm \\
       -v "$PWD/certbot/www:/var/www/certbot" \\
       -v "$PWD/certbot/conf:/etc/letsencrypt" \\
       certbot/certbot certonly --webroot \\
       -w /var/www/certbot \\
       -d ${DOMAIN} \\
       --email you@example.com --agree-tos --no-eff-email

  3) Restart nginx:
     docker compose -f docker-compose.prod.yml --env-file .env.prod restart nginx

If you don't want HTTPS yet, remove the port-80 redirect in nginx.conf.
EOF
