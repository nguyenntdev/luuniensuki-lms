# Luuniensuki LMS

Nen tang hoc tap gamified ve di san Cuu Dinh (trieu Nguyen).

Production domain: `cuudinh.histolab.icu`

## Cong nghe chinh

- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Frontend: Next.js + TailwindCSS + React Three Fiber
- Ha tang: Docker Compose + Nginx

## Chay local (quick start)

```bash
# DB + API
docker compose up -d

# Frontend
cd frontend
npm install
npm run dev
```

Kiem tra nhanh:

```bash
curl -s http://localhost:8000/health
```

## Deploy production

- Huong dan chi tiet: `docs/DEPLOYMENT_CUUDINH.md`
- Quan ly secrets: `docs/SECRETS.md`

## Cau truc thu muc

- `backend/` - FastAPI API
- `frontend/` - Next.js app
- `docker-compose.yml` - dev stack
- `docker-compose.prod.yml` - prod stack
- `nginx-lms.conf` - Nginx config prod
