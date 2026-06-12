# Production Deployment Checklist — Lưu Niên Sử Kí LMS

Checklist canonical để đưa hệ thống lên production (domain `lms.histolab.icu`). Đây là tài liệu hợp nhất; checklist content-verification/QA cũ đã được gộp vào đây và xoá bản trùng.

Liên quan:
- Hướng dẫn deploy từng bước: [DEPLOYMENT_CUUDINH.md](DEPLOYMENT_CUUDINH.md)
- Secrets bắt buộc và cơ chế fail-closed: [SECRETS.md](SECRETS.md)
- CI/CD: [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)
- Kiến trúc tổng thể: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 1. Cấu hình môi trường (`.env.prod`)

- [ ] Tạo `.env.prod` trên server (chmod 600), không commit vào git. Tham chiếu `.env.example` cho đầy đủ key.
- [ ] `ENVIRONMENT=production` (Python) và `APP_ENV=production` (Rust) — bật fail-closed validation.
- [ ] `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` đặt giá trị thật, mật khẩu mạnh.
- [ ] `DATABASE_URL` trỏ đúng DB production (Python dùng `postgresql+psycopg://`, Rust dùng `postgres://`).
- [ ] `NEXT_PUBLIC_API_BASE_URL` để **trống** ở production để frontend gọi cùng origin `/api/...` qua Nginx.

## 2. Bảo mật (fail-closed — service sẽ không khởi động nếu thiếu)

- [ ] `JWT_SECRET_KEY` là chuỗi ngẫu nhiên mạnh và **giống nhau ở cả Python và Rust** (chung JWT contract). Sinh bằng `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
- [ ] Không còn giá trị placeholder `CHANGE_ME*` / `dev-insecure-change-me` ở bất kỳ secret nào.
- [ ] `CORS_ORIGINS` là allowlist tường minh (không dùng `*` đi kèm credentials) — Python sẽ fail-closed nếu vi phạm.
- [ ] Rust secrets: `JANUS_ADMIN_SECRET`, `JANUS_API_SECRET`, `LIVE_INTERNAL_TOKEN`, `TURN_STATIC_AUTH_SECRET` đặt giá trị thật (xem [SECRETS.md](SECRETS.md)).
- [ ] HTTPS/SSL: Certbot đã cấp cert cho `lms.histolab.icu` và auto-renew (kiểm tra `renew-ssl.sh` / cron).
- [ ] Secure cookies bật (mặc định `cookie_secure_effective` = true ở production), `SameSite=lax`.
- [ ] Security headers (CSP, HSTS, `X-Content-Type-Options`) hoạt động — kiểm tra response header.
- [ ] Rate limiting auth (`/api/v1/auth/*`) và live/AI đang chạy.
- [ ] Đã chạy thử boot ở staging để xác nhận **cả Python và Rust khởi động không lỗi config**.

## 3. Cơ sở dữ liệu

- [ ] Áp dụng migration: `docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod run --rm api alembic upgrade head` (mới nhất: `0047_revoked_refresh_tokens`).
- [ ] Seed dữ liệu nội dung nếu DB mới: `... run --rm api python -m backend.seed` (162 motif / 9 đỉnh) + seed phụ (`seed_tags`, `seed_daily_missions`, `seed_weekly_quests`) nếu cần.
- [ ] Backup tự động đã bật (`backup-db.sh` qua cron, hoặc managed DB backup).
- [ ] Volume `postgres_data` được persist; không xoá khi rebuild.

## 4. Build & khởi động stack

- [ ] Build và start: `docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod up -d --build`.
- [ ] Các service chạy: `db`, `api`, `api_rust`, `web`, `ai_teacher_agent`, `livekit`, `janus-gateway`, `nginx`.
- [ ] Mọi `/api/*` và `/health` đi qua `api_rust:8001`; Rust proxy fallback sang `api:8000`.
- [ ] Nginx (`nginx-lms.conf`) map qua override: `8088:80` và `8443:443` (reverse-proxy host phía trước nếu cần 80/443 công khai).

## 5. Hiệu năng & độ tin cậy

- [ ] Gunicorn: `GUNICORN_WORKERS` và `GUNICORN_TIMEOUT` (mặc định 180s) phù hợp tài nguyên server.
- [ ] Nginx bật gzip (đã cấu hình trong `nginx-lms.conf`) và cache header dài cho `/assets/`.
- [ ] 3D models proxy qua `/assets/models/` (store.histolab.icu) với cache + CORS header.
- [ ] `restart: unless-stopped` cho mọi service.

## 6. Giám sát

- [ ] Uptime monitor ping `https://lms.histolab.icu/health`.
- [ ] Error tracking: `SENTRY_DSN` cấu hình nếu dùng Sentry.
- [ ] Log được rotate (Janus đã giới hạn json-file 10m x3; cấu hình tương tự cho service khác nếu cần).

## 7. Frontend & kiểm thử

- [ ] `npm run lint:ci` và `npm run build` (gồm `tsc --noEmit`) pass trong CI.
- [ ] Playwright smoke (`@smoke`) pass trong CI.
- [ ] Backend `pytest` pass trong CI.
- [ ] Nội dung enriched (historical_context, symbolism, fun_fact, quiz + explanation) hiển thị đúng và chấm điểm phía server.

## 8. CI/CD

- [ ] `.github/workflows/ci.yml` chạy trên mọi PR vào `main` (backend pytest + frontend lint/build/e2e).
- [ ] `.github/workflows/deploy.yml` deploy lên server qua SSH khi push `main` (cần secrets `SERVER_HOST`, `SERVER_USER`, `SSH_PRIVATE_KEY`, `SERVER_PORT`).
- [ ] Branch protection trên `main` (require status checks).

## 9. Kiểm tra sau deploy

```bash
# HTTP -> HTTPS redirect
curl -I http://lms.histolab.icu

# Health (đi qua Rust gateway)
curl -sf https://lms.histolab.icu/health

# Trạng thái container
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod ps
```

- [ ] `/health` trả 200.
- [ ] Đăng ký/đăng nhập hoạt động; cookie token có cờ `Secure`.
- [ ] Lớp live (LiveKit/Janus) kết nối được nếu bật.
