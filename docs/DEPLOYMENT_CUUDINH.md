# Hướng dẫn deploy chi tiết (VPS)

Hướng dẫn từng bước đưa **Lưu Niên Sử Kí LMS** lên một VPS Ubuntu sạch bằng Docker Compose.

> Quan trọng về domain/cert: file `nginx-lms.conf` (được `docker-compose.prod.yml` mount vào service `nginx`) hiện **hard-code domain `lms.histolab.icu`** và đường dẫn cert `/etc/letsencrypt/live/lms.histolab.icu/...`. Nếu deploy lên domain khác (ví dụ `cuudinh.histolab.icu`), bạn phải sửa `server_name` và các đường dẫn cert trong `nginx-lms.conf`, đồng thời cấp Certbot cho đúng domain đó. Các ví dụ dưới đây dùng biến `DOMAIN` để bạn thay thế.

```bash
export DOMAIN="lms.histolab.icu"   # đổi sang domain thật của bạn
export SERVER_IP="47.84.95.59"     # đổi sang IP thật của VPS
```

## 0) Yêu cầu trước khi deploy

- DNS A record: `$DOMAIN -> $SERVER_IP`.
- Mở cổng vào VPS (xem ghi chú port ở mục 7 — stack map `8088`/`8443`, thường có reverse-proxy host phía trước cho 80/443).
- Có quyền `root` hoặc user thuộc group `docker`.

## 1) Đăng nhập VPS

```bash
ssh root@$SERVER_IP
```

## 2) Cài Docker + Compose plugin

```bash
apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

docker version
```

## 3) Đưa source lên server

### Cách A: clone từ Git

```bash
git clone <REPO_URL> /opt/luuniensuki-lms
cd /opt/luuniensuki-lms
```

### Cách B: rsync từ máy local

```bash
rsync -az --exclude '.git' --exclude '.venv' --exclude '.pytest_cache' \
  --exclude 'frontend/node_modules' --exclude 'frontend/.next' \
  ./ root@$SERVER_IP:/opt/luuniensuki-lms/
```

## 4) Tạo file `.env.prod`

Xem danh sách secret bắt buộc ở [SECRETS.md](SECRETS.md) và mẫu đầy đủ ở `.env.example`. Lưu ý cơ chế **fail-closed**: thiếu secret thật thì backend sẽ không khởi động.

```bash
cd /opt/luuniensuki-lms
cat > .env.prod <<'EOF_ENV'
# Môi trường — bật fail-closed validation
ENVIRONMENT=production
APP_ENV=production

# Postgres
POSTGRES_DB=luuniensuki
POSTGRES_USER=postgres
POSTGRES_PASSWORD=__STRONG_PASSWORD__

# DB URL (Python dùng +psycopg, Rust dùng postgres://)
DATABASE_URL=postgresql+psycopg://postgres:__STRONG_PASSWORD__@db:5432/luuniensuki

# JWT — PHẢI GIỐNG NHAU ở cả Python và Rust
JWT_SECRET_KEY=__STRONG_RANDOM__
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS allowlist tường minh (không dùng '*' kèm credentials)
CORS_ORIGINS=https://lms.histolab.icu

# Live media / Rust gateway secrets (bắt buộc ở prod)
LIVE_MEDIA_BACKEND=livekit
JANUS_ADMIN_SECRET=__STRONG__
JANUS_API_SECRET=__STRONG__
LIVE_INTERNAL_TOKEN=__STRONG__
TURN_STATIC_AUTH_SECRET=__STRONG__

# LiveKit
LIVEKIT_API_KEY=__KEY__
LIVEKIT_API_SECRET=__AT_LEAST_32_CHARS__
LIVEKIT_PUBLIC_URL=wss://lms.histolab.icu/livekit/

# Frontend gọi cùng origin -> để trống
NEXT_PUBLIC_API_BASE_URL=

# Tuỳ chọn
LOG_LEVEL=info
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=180
EOF_ENV

chmod 600 .env.prod
```

Sinh chuỗi ngẫu nhiên mạnh: `python -c "import secrets; print(secrets.token_urlsafe(64))"`.

## 5) Tạo cert tạm (trước khi có cert thật)

Nginx cần file cert để khởi động. Tạo self-signed tạm cho đúng `$DOMAIN`:

```bash
mkdir -p certbot/www "certbot/conf/live/$DOMAIN"
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
  -keyout "certbot/conf/live/$DOMAIN/privkey.pem" \
  -out "certbot/conf/live/$DOMAIN/fullchain.pem" \
  -subj "/CN=$DOMAIN" >/dev/null 2>&1 || true
```

## 6) Khởi động stack production

Dùng `docker-compose.prod.yml` **cùng** `docker-compose.override.yml` (override map port Nginx và mount `nginx-lms.conf`):

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod up -d --build
```

Lệnh này dựng đầy đủ service: `db`, `api`, `api_rust`, `web`, `ai_teacher_agent`, `livekit`, `janus-gateway`, `nginx`.

## 7) Áp dụng migration & seed database

```bash
# Migration (mới nhất: 0047_revoked_refresh_tokens)
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod \
  run --rm api alembic upgrade head

# Seed nội dung (nếu DB mới)
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod \
  run --rm api python -m backend.seed
```

## 8) Kiểm tra hệ thống

```bash
# Nginx redirect HTTP -> HTTPS
curl -I http://$DOMAIN

# Health đi qua Rust gateway (giai đoạn cert tạm dùng -k)
curl -k https://$DOMAIN/health
```

## 9) Lấy SSL thật bằng Certbot

Sau khi DNS đã trỏ đúng IP:

```bash
cd /opt/luuniensuki-lms
docker run --rm \
  -v "$PWD/certbot/www:/var/www/certbot" \
  -v "$PWD/certbot/conf:/etc/letsencrypt" \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot \
  -d "$DOMAIN" \
  --email you@example.com --agree-tos --no-eff-email

# Reload nginx
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod restart nginx
```

## 10) Renew cert

```bash
docker run --rm \
  -v "$PWD/certbot/www:/var/www/certbot" \
  -v "$PWD/certbot/conf:/etc/letsencrypt" \
  certbot/certbot renew --dry-run
```

Tham khảo `renew-ssl.sh` trong repo và tạo cron job chạy renew định kỳ.

## 11) Lệnh debug

```bash
COMPOSE="docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod"

$COMPOSE ps
$COMPOSE logs -f api        # FastAPI fallback
$COMPOSE logs -f api_rust   # Rust gateway (điểm vào /api/*)
$COMPOSE logs -f web
$COMPOSE logs -f nginx
```

## Ghi chú quan trọng

- **Điểm vào API là `api_rust` (Rust gateway)**: mọi `/api/*` và `/health` đi vào Rust rồi proxy fallback sang FastAPI (`api`) cho route chưa migrate.
- `docker-compose.override.yml` map Nginx ra **`8088:80`** và **`8443:443`** (thường có reverse-proxy/host nginx phía trước nhận 80/443 và forward vào đây). Nếu muốn Nginx của stack nhận trực tiếp 80/443, sửa phần `ports` trong override.
- `nginx-lms.conf` hard-code `lms.histolab.icu` — đổi domain thì phải sửa file này + đường dẫn cert.
- Thư mục `ban-duc-noi/` được Nginx serve tại `/assets/ban-duc-noi/...`; model 3D proxy qua `/assets/models/` từ `store.histolab.icu`.
