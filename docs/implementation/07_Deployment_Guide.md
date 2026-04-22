# 07_Deployment_Guide.md

Deployment pack for **Lưu Niên Sử Kí** on a fresh Ubuntu VPS.

**Target domain:** `lms.histolab.icu`  
**Stack:** Next.js (Frontend) + FastAPI (Backend) + PostgreSQL + Nginx (reverse proxy)

> Security: do **not** commit `.env.prod` (contains DB/JWT secrets). Do not store SSH/root credentials in git.

---

## Quick Deploy (Fresh VPS)

```bash
sudo -i
ufw allow 80/tcp || true
ufw allow 443/tcp || true
export REPO_URL="https://github.com/<you>/luuniensuki-lms.git"
export DOMAIN="lms.histolab.icu"
bash setup.sh
```

## Port Conflicts (If VPS Already Runs Dify / Another Nginx)

If something else is already binding **80/443**, you have two options:

1) **Keep LMS on 80/443** (recommended) and move the other stack.
   - Example (Dify): edit `/root/dify/docker/.env`:
     - `EXPOSE_NGINX_PORT=8080`
     - `EXPOSE_NGINX_SSL_PORT=8443`
   - Then: `cd /root/dify/docker && docker compose up -d nginx`

2) Or move LMS to other ports (requires changing the `nginx` service `ports:` in `docker-compose.prod.yml`, and updating your DNS/proxy accordingly).

## 1) Production Docker Compose — `docker-compose.prod.yml`

Runs:

- `db`: Postgres 15 with persistent volume
- `api`: FastAPI via **Gunicorn + UvicornWorker**
- `web`: Next.js server (`next start`) (expects a valid Next.js app in `./frontend/`)
- `nginx`: reverse proxy + TLS termination

```yaml
services:
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 5s
      retries: 20

  api:
    build:
      context: .
      dockerfile: backend/Dockerfile
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      LOG_LEVEL: ${LOG_LEVEL:-info}
      INTERACTION_TOLERANCE_MULTIPLIER: ${INTERACTION_TOLERANCE_MULTIPLIER:-1.25}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      JWT_ALGORITHM: ${JWT_ALGORITHM:-HS256}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES:-60}
      REFRESH_TOKEN_EXPIRE_DAYS: ${REFRESH_TOKEN_EXPIRE_DAYS:-30}
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./ban-duc-noi:/app/ban-duc-noi:ro
    command: >
      /bin/sh -c
      "gunicorn -k uvicorn.workers.UvicornWorker
      -w ${GUNICORN_WORKERS:-2}
      -b 0.0.0.0:8000
      --timeout ${GUNICORN_TIMEOUT:-60}
      backend.main:app"

  web:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      NODE_ENV: production
    depends_on:
      - api

  nginx:
    image: nginx:1.25-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certbot/www:/var/www/certbot:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./ban-duc-noi:/var/www/assets/ban-duc-noi:ro
    depends_on:
      - web
      - api

volumes:
  postgres_data:
```

---

## 2) Nginx Configuration — `nginx.conf`

Requirements:

- Route `/api/*` to backend (`api`)
- Route `/` to frontend (`web`)
- TLS stub for Certbot
- Proxy `/assets/models/*` to `store.histolab.icu` (model store) as same-origin assets (avoids CORS)

> Note: current backend also exposes `/motifs/*` and `/progress/*` at root, so they’re proxied to `api` too.

```nginx
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

  # ACME challenge (Certbot webroot mode)
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

  # Certbot-managed cert paths (stub; created after first issuance)
  ssl_certificate     /etc/letsencrypt/live/lms.histolab.icu/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/lms.histolab.icu/privkey.pem;

  # Reasonable TLS defaults (replace with certbot includes if preferred)
  ssl_session_timeout 1d;
  ssl_session_cache shared:SSL:10m;
  ssl_session_tickets off;

  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_prefer_server_ciphers off;

  client_max_body_size 10m;

  proxy_http_version 1.1;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;

  # Backend routes
  location ^~ /api/ {
    proxy_pass http://api_upstream;
  }

  # 3D models are hosted on store.histolab.icu (no CORS headers), so proxy them as same-origin assets.
  location ^~ /assets/models/ {
    proxy_ssl_server_name on;
    proxy_ssl_name store.histolab.icu;
    proxy_set_header Host store.histolab.icu;
    proxy_buffering off;
    proxy_pass https://store.histolab.icu/;

    access_log off;
    expires 7d;
  }

  # Static assets (images/models). Served directly by Nginx.
  location ^~ /assets/ {
    root /var/www;
    access_log off;
    expires 7d;
  }

  # Current backend also exposes these at root (not under /api)
  location ^~ /motifs/ {
    proxy_pass http://api_upstream;
  }

  location ^~ /progress/ {
    proxy_pass http://api_upstream;
  }

  # Frontend (Next.js)
  location / {
    # We don't use Next.js Server Actions; reject non-GET to reduce noise/attack surface.
    if ($request_method !~ ^(GET|HEAD|OPTIONS)$) {
      return 405;
    }
    proxy_pass http://web_upstream;
  }
}
```

---

## 3) One-Command VPS Bootstrap — `setup.sh`

This script:

1) Installs Docker + Compose
2) Clones/pulls the repo
3) Creates `.env.prod` (if missing)
4) Builds and starts the production stack
5) Runs `seed.py` to create schema and initial data

```bash
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
  - API:   http://${DOMAIN}/api/v1/auth/me

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
```

---

## Commands (Operator Cheat Sheet)

From the repo root on the VPS:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f nginx
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f api
```

Re-seed (creates tables if missing):

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod run --rm api python -m backend.seed
```

Test auth quickly:

```bash
curl -s -X POST https://lms.histolab.icu/api/v1/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"dev@example.com","password":"dev-only-1234","display_name":"Dev"}'
```
