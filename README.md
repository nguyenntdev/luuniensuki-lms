# Cửu Đỉnh Ký

Nền tảng học tập gamified về di sản Cửu Đỉnh (triều Nguyễn).

Production domain: `cuudinh.histolab.icu`

## Công nghệ chính

- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Frontend: Next.js + TailwindCSS + React Three Fiber
- Hạ tầng: Docker Compose + Nginx

## Chạy local (quick start)

```bash
# DB + API
docker compose up -d

# Frontend
cd frontend
npm install
npm run dev
```

Kiểm tra nhanh:

```bash
curl -s http://localhost:8000/health
```

## Deploy production

- Hướng dẫn chi tiết: `docs/DEPLOYMENT_CUUDINH.md`
- Quản lý secrets: `docs/SECRETS.md`

## Cấu trúc thư mục

- `backend/` - FastAPI API
- `frontend/` - Next.js app
- `docker-compose.yml` - dev stack
- `docker-compose.prod.yml` - prod stack
- `nginx-lms.conf` - Nginx config prod
