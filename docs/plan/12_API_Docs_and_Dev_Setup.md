# 12_API_Docs_and_Dev_Setup.md

## Goal

Make it easy for developers (and future agents) to:

- run the project locally
- understand API contracts
- test quickly without guessing

## API Documentation

### OpenAPI / Swagger

FastAPI provides:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- Raw schema: `/openapi.json`

**Tasks**

- [ ] **DOC-API-01**: Add `/api/v1` tag grouping in routers (auth, urns, motifs, progress, quiz, users, admin)
- [ ] **DOC-API-02**: Add clear response models and examples for key endpoints
- [ ] **DOC-API-03**: Document authentication in OpenAPI (Bearer)

### Postman / cURL Examples

Keep a small set of verified requests:

- register/login/me
- list urns/motifs
- unlock/complete-lesson/quiz-submit

**Tasks**

- [ ] **DOC-API-04**: Add `docs/implementation/api_examples.md` (or similar) with copy-paste curl snippets

## Developer Setup (Local)

### Prereqs

- Docker + Docker Compose plugin
- Node 20+ (if running frontend outside Docker)

### Backend + DB (Docker)

From repo root:

```bash
docker compose up -d db api
```

Seed:

```bash
docker compose run --rm api python -m backend.seed
```

Open API docs:

- `http://localhost:8000/docs`

### Frontend (Local Node)

```bash
cd frontend
npm install
npm run dev
```

- `http://localhost:3000`

### Env Vars (Reference)

Backend:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `LOG_LEVEL`
- `INTERACTION_TOLERANCE_MULTIPLIER`

Frontend:

- `NEXT_PUBLIC_API_BASE_URL` (default is same-origin/empty)

## Production Notes

- Domain: `lms.histolab.icu`
- Nginx routes `/api/*` to backend and `/` to frontend.
- If another stack (e.g. Dify) is using ports 80/443, move it away (see `docs/implementation/07_Deployment_Guide.md`).

## Definition of Done

- A new developer can go from `git clone` → running app locally in < 15 minutes.
- API docs clearly show auth requirements + request/response shapes.

