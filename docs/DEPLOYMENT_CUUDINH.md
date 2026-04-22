# Huong dan deploy chi tiet (cuudinh.histolab.icu)

Muc tieu: dua he thong Luuniensuki LMS len server `47.84.95.59` voi domain `cuudinh.histolab.icu`.

## 0) Yeu cau truoc khi deploy

- DNS A record: `cuudinh.histolab.icu -> 47.84.95.59`
- Mo cong 80/443 tren VPS (UFW/Firewall)
- Co quyen `root` (hoac user co quyen Docker)

## 1) Dang nhap VPS

```bash
ssh root@47.84.95.59
```

## 2) Cai Docker + Compose

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

## 3) Mo cong 80/443

```bash
ufw allow 80/tcp || true
ufw allow 443/tcp || true
```

Neu VPS dang chay nginx host (khong phai container), hay dung no:

```bash
systemctl stop nginx || true
systemctl disable nginx || true
ss -tulpn | grep -E ":(80|443)\\b" || true
```

## 4) Dua source len server

### Cach A: rsync tu may local

```bash
rsync -az --exclude '.git' --exclude '.venv' --exclude '.pytest_cache' \
  --exclude 'frontend/node_modules' --exclude 'frontend/.next' \
  ./ root@47.84.95.59:/opt/luuniensuki-lms/
```

### Cach B: clone tu Git

```bash
git clone <REPO_URL> /opt/luuniensuki-lms
cd /opt/luuniensuki-lms
```

## 5) Tao file .env.prod

Xem mau va danh sach secrets o: `docs/SECRETS.md`.

Vi du (chinh sua gia tri that, khong commit len git):

```bash
cd /opt/luuniensuki-lms
cat > .env.prod <<'EOF_ENV'
POSTGRES_DB=luuniensuki
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_ME

JWT_SECRET_KEY=CHANGE_ME
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

LOG_LEVEL=info
INTERACTION_TOLERANCE_MULTIPLIER=1.25

NEXT_PUBLIC_API_BASE_URL=
MODEL_BASE_URL=/assets/models
EOF_ENV

chmod 600 .env.prod
```

## 6) Tao cert tam (truoc khi co cert that)

Nginx can file cert de khoi dong, tao tam self-signed:

```bash
mkdir -p certbot/www certbot/conf/live/cuudinh.histolab.icu
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
  -keyout certbot/conf/live/cuudinh.histolab.icu/privkey.pem \
  -out certbot/conf/live/cuudinh.histolab.icu/fullchain.pem \
  -subj "/CN=cuudinh.histolab.icu" >/dev/null 2>&1 || true
```

## 7) Start stack production

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build db api web nginx
```

## 8) Seed database

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod run --rm api python -m backend.seed
```

## 9) Kiem tra he thong

```bash
# Nginx se redirect HTTP -> HTTPS
curl -I http://cuudinh.histolab.icu

# Trong giai doan cert tam, dung -k
curl -k https://cuudinh.histolab.icu/health
```

## 10) Lay SSL that bang Certbot

Sau khi DNS da tro dung IP:

```bash
cd /opt/luuniensuki-lms

docker run --rm \
  -v "$PWD/certbot/www:/var/www/certbot" \
  -v "$PWD/certbot/conf:/etc/letsencrypt" \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot \
  -d cuudinh.histolab.icu \
  --email you@example.com --agree-tos --no-eff-email

# Reload nginx container
docker compose -f docker-compose.prod.yml --env-file .env.prod restart nginx
```

## 11) Renew cert (goi y)

```bash
# Test renew
docker run --rm \
  -v "$PWD/certbot/www:/var/www/certbot" \
  -v "$PWD/certbot/conf:/etc/letsencrypt" \
  certbot/certbot renew --dry-run
```

Co the tao cron job chay renew hang thang.

## 12) Lenh kiem tra va debug

```bash
# Xem trang thai
docker compose -f docker-compose.prod.yml --env-file .env.prod ps

# Log tung service
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f api

docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f web

docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f nginx
```

## Ghi chu quan trong

- `nginx-lms.conf` da su dung domain `cuudinh.histolab.icu` va cert path tuong ung.
- `docker-compose.prod.yml` map cong `80:80` va `443:443`.
- Thu muc `ban-duc-noi/` duoc Nginx serve o `/assets/ban-duc-noi/...`.
