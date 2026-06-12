# Kiến Trúc Hệ Thống

Tài liệu canonical mô tả kiến trúc hiện tại của **Lưu Niên Sử Kí LMS** (Cửu Đỉnh Ký). Hệ thống là một monorepo gồm backend Python/FastAPI (đã modular hoá), backend Rust/axum (gateway + native routes đang mở rộng), frontend Next.js (TypeScript), PostgreSQL, và lớp media live (LiveKit / Janus). Production chạy bằng Docker Compose sau Nginx, domain `lms.histolab.icu`.

## Bức Tranh Tổng Quan

```text
Người dùng / Mobile
  -> Nginx (TLS, gzip, security routing) — nginx-lms.conf
       -> web        : Next.js (TypeScript)            :3000
       -> api_rust   : Rust axum gateway + native API  :8001  (mọi /api/*, /health)
            -> api   : FastAPI backend (fallback)       :8000  (route chưa migrate)
       -> livekit    : WebRTC media (LiveKit)
       -> janus      : WebRTC signaling (Janus, tuỳ chọn)
  -> PostgreSQL (db) :5432

Background
  -> ai_teacher_agent : Python realtime worker (AI giáo viên)
```

Điểm quan trọng: Nginx **không** gọi thẳng FastAPI nữa. Mọi request `/api/*` và `/health` đều đi vào **Rust gateway** (`api_rust:8001`); gateway xử lý native route đã migrate và **proxy fallback** sang FastAPI (`api:8000`) cho phần còn lại.

## Service Chính

| Service | Vai trò | Stack | Trạng thái |
| --- | --- | --- | --- |
| `web` | Frontend | Next.js 15 + React 19 + TypeScript | Production |
| `api_rust` | API gateway + native endpoint | Rust + axum + sqlx/tokio-postgres | Đang mở rộng, là điểm vào API |
| `api` | Backend nghiệp vụ (fallback) | Python 3.11/3.12 + FastAPI | Production, bắt buộc cho phần chưa migrate |
| `db` | Cơ sở dữ liệu | PostgreSQL 15 | Production |
| `ai_teacher_agent` | Worker Giáo viên AI realtime | Python | Production |
| `livekit` | Media WebRTC (audio/video lớp live) | LiveKit Server | Production |
| `janus-gateway` | Signaling WebRTC thay thế (phased) | Janus | Tuỳ chọn theo `LIVE_MEDIA_BACKEND` |
| `nginx` | Reverse proxy, TLS, static assets | Nginx | Production |

## Backend Python (FastAPI) — Package Đã Modular Hoá

`backend/main.py` từng là một module khổng lồ. Theo spec `backend-modularization`, app construction và các nhóm shared logic đã được tách ra; `main.py` giờ chủ yếu lắp ráp app từ factory và đăng ký route. Cấu trúc package hiện tại:

```text
backend/
├── app.py              # create_app(): factory dựng FastAPI (exception handlers,
│                       #   CORS, middleware security-headers + rate-limit, static mounts,
│                       #   include_router cho các router đã tách)
├── main.py             # app = create_app(); phần lớn route hiện vẫn đăng ký ở đây
├── config.py           # Settings (pydantic-settings) + fail-closed production validator
├── db.py               # engine, SessionLocal, get_db() dependency
├── deps.py             # auth/session/ownership dependencies, RBAC guards, OAuth2 scheme
├── security.py         # hash_password / verify_password (bcrypt), create_jwt_token
├── rbac.py             # ADMIN_ROLES / STAFF_ROLES
├── errors.py           # AppError + exception handlers (envelope lỗi chuẩn)
├── models.py           # SQLAlchemy 2.0 models (Mapped[])
├── schemas.py          # schema dùng chung cũ
├── domain/             # business logic thuần
│   ├── gamification.py     # XP_RANKS, _compute_rank, _update_streak, _award_badge, _issue_certificate
│   └── auth_session.py     # cookie helpers, refresh-token revoke/check, build /auth/me
├── apischemas/         # Pydantic request/response models theo nhóm
│   ├── auth.py  users.py  content.py  quests.py  ai.py  progress.py  admin.py
├── routers/            # APIRouter đã tách khỏi main
│   └── auth.py             # router auth (login/register/refresh/logout/...)
└── services/           # service layer (analytics, daily_goal_settings, AI, live, ...)
```

Quy ước import là một chiều để tránh vòng lặp: `main` → `app` → `routers` → `domain`/`apischemas`/`deps`/`db`/`config`. `app.py` import router lazy bên trong `create_app()` nên không bao giờ import ngược về `main`.

Entry point production: `backend.main:app` (chạy qua Gunicorn + UvicornWorker).

## Backend Rust (axum) — Gateway & Native Routes

`backend-rust/` là gateway Rust dựa trên axum, vừa phục vụ native endpoint vừa proxy fallback sang FastAPI. Cấu trúc:

```text
backend-rust/src/
├── main.rs          # load Settings::from_env() -> Settings::validate() (fail-closed) -> build DB pool, router, jobs
├── config.rs        # Settings + validate(): chặn secret sentinel trong production
├── db.rs            # PostgreSQL pool
├── gateway.rs       # proxy fallback sang FastAPI legacy (LEGACY_API_HOST/PORT)
├── dispatcher.rs    # định tuyến native vs fallback theo route-modes.toml / route-inventory
├── auth.rs          # xác thực JWT (HS256, iss/aud/exp) — chung contract với Python
├── rate_limit.rs    # rate limiting
├── observability.rs # logging / metrics
├── inventory.rs     # route inventory
├── error.rs         # error shape
├── routes/  services/  models/  jobs/   # native handlers, service layer, jobs (live media…)
└── config/route-modes.toml              # bật/tắt native theo từng route
```

Rust gateway đảm nhiệm thêm phần **media/live control plane** (Janus signaling, TURN credentials, internal token cho worker AI). Các route DB-heavy/AI-heavy chưa có native implementation vẫn proxy sang FastAPI cho tới khi có contract test tương ứng.

## Frontend (Next.js + TypeScript)

`frontend/` đã chuyển sang TypeScript:

- `tsconfig.json` + `prebuild` chạy `tsc --noEmit` (type-check trước khi build).
- `src/lib/api.ts` — fetch wrapper gọi API cùng origin (`/api/...`), inject token.
- `src/stores/authStore.ts` — Zustand store cho auth (các store khác đang dần TS hoá).
- `middleware.ts` — middleware bảo vệ route, dùng `jose` để verify JWT phía edge.
- `src/types/api.ts` — kiểu sinh từ OpenAPI (`npm run gen:api`).
- App Router (`src/app/`), component 3D bằng `@react-three/fiber` + `@react-three/drei` + `three`, media live bằng `livekit-client`.

Pipeline chất lượng: `npm run lint:ci` (ESLint, `--max-warnings=0`), `npm run build`, `npm test` (vitest), và Playwright e2e (`@smoke`).

## Kiến Trúc Bảo Mật (Security Hardening)

Theo spec `security-hardening-remediation`, hệ thống đã được làm cứng nhiều lớp. Cả hai backend dùng chung **JWT contract** (HS256, cùng `JWT_SECRET_KEY`, cùng `iss`/`aud`).

- **Fail-closed config validation** — khi `ENVIRONMENT=production` (Python) / `APP_ENV=production` (Rust), service **từ chối khởi động** nếu thiếu secret thật.
  - Python `backend/config.py` → `_validate_production_security`: chặn `JWT_SECRET_KEY` sentinel và cấu hình `CORS_ORIGINS='*'` đi kèm `allow_credentials=True`.
  - Rust `backend-rust/src/config.rs` → `Settings::validate()`: chặn sentinel cho `JWT_SECRET_KEY`, `JANUS_ADMIN_SECRET`, `JANUS_API_SECRET`, `LIVE_INTERNAL_TOKEN`, `TURN_STATIC_AUTH_SECRET`. Lỗi chỉ nêu **tên key**, không in giá trị. Xem [SECRETS.md](SECRETS.md).
- **CORS allowlist** — production yêu cầu danh sách origin tường minh; wildcard + credentials bị hạ cấp/loại bỏ (defense-in-depth trong `create_app()`).
- **Security headers** — middleware gắn `Content-Security-Policy` (`default-src 'self'; frame-ancestors 'none'; object-src 'none'`), `Strict-Transport-Security` (HSTS), `X-Content-Type-Options: nosniff` cho mọi response.
- **Secure cookies** — token JWT đặt trong cookie; cờ `Secure` bật theo môi trường (`cookie_secure_effective`: bật ở production), `SameSite=lax`.
- **JWT iss/aud/exp + refresh-token revocation** — token mang claim `iss`/`aud`/`exp` (rollout kiểu issue-then-enforce qua `jwt_validate_new_claims`); refresh token có thể thu hồi qua bảng `revoked_refresh_tokens` (migration `0047`).
- **Server-authoritative exam grading** — chấm quiz/urn-exam phía server; client không quyết định điểm/đỗ.
- **Magic-byte upload validation** — ảnh avatar được xác thực bằng nội dung thật (Pillow / magic-byte), không tin `Content-Type`; giới hạn kích thước.
- **Rate limiting** — middleware fixed-window cho `/api/v1/auth/*` (Python) và rate limiting trong Rust gateway; thêm rate limit riêng cho live/AI.
- **RBAC / IDOR guards** — `deps.py` + `rbac.py` cung cấp `require_admin`, `get_staff_user`, kiểm tra quyền sở hữu (`_ensure_owner_or_404`) chống truy cập tài nguyên người khác.

## Database & Migrations

PostgreSQL 15 là nguồn dữ liệu chính. Schema quản lý bằng **Alembic** (`alembic.ini` + `migrations/`), tới `0047_revoked_refresh_tokens`. Áp dụng migration khi deploy:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod \
  run --rm api alembic upgrade head
```

Rust có PostgreSQL pool riêng (`db.rs`) cho native route; route DB-heavy chưa native vẫn proxy sang FastAPI.

## Triển Khai (Tóm Tắt)

- Dev: `docker-compose.yml` (+ `docker-compose.override.yml`). Nginx bật qua profile `with-nginx`.
- Prod: `docker-compose.prod.yml` (+ `docker-compose.override.yml`), env từ `.env.prod`, Nginx dùng `nginx-lms.conf` (domain `lms.histolab.icu`), Certbot cấp TLS.
- Chi tiết từng bước: [DEPLOYMENT_CUUDINH.md](DEPLOYMENT_CUUDINH.md) và [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md).
- CI/CD: GitHub Actions (`.github/workflows/ci.yml`, `deploy.yml`) — xem [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md).

## Nguyên Tắc Migration Sang Rust

- Chuyển từng nhóm endpoint nhỏ, ưu tiên route read-only ít side effect.
- Không fake dữ liệu DB chỉ để gọi là "đã migrate".
- Giữ FastAPI fallback cho tới khi có native implementation + contract test + smoke test production + rollback plan.
- Mỗi phase có plan trong `docs/plan/`, commit nhỏ, test, deploy, smoke test.
- Chỉ cleanup route FastAPI cũ khi đã chắc không còn traffic production phụ thuộc.

## Cleanup Strategy

- Docker: prune build cache, dangling image, container dừng, volume không dùng.
- Code: xoá route FastAPI theo nhóm đã fully migrated + có contract test; không xoá sớm cả backend.
- Docs: cập nhật tài liệu này và [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) sau mỗi phase lớn.
- Data: không xoá volume DB hoặc uploads nếu chưa backup và chưa có xác nhận rõ ràng.
