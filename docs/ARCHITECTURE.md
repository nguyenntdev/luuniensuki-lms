# Kiến Trúc Hệ Thống

Tài liệu này mô tả kiến trúc hiện tại của Lưu Niên Sử Kí LMS trong giai đoạn chuyển backend từ Python sang Rust.

## Bức Tranh Tổng Quan

```text
Người dùng
  -> Nginx
  -> Next.js Web
  -> Rust API Gateway
       -> Rust native routes
       -> FastAPI fallback routes
  -> PostgreSQL

Background workers
  -> Python AI teacher worker
  -> LiveKit
  -> PostgreSQL
```

## Luồng Request Chính

1. Browser gọi web qua Nginx.
2. Next.js render UI và gọi API cùng origin qua `/api/...`.
3. Nginx chuyển API request sang `api_rust`.
4. Rust gateway xử lý route đã migrate.
5. Route chưa migrate được proxy sang FastAPI.
6. FastAPI vẫn là backend legacy cho phần DB-heavy, AI-heavy, LiveKit và admin mutation.

## Service Chính

| Service | Vai trò | Trạng thái |
| --- | --- | --- |
| `web` | Next.js frontend | Production |
| `api_rust` | Rust API gateway và native endpoint | Đang mở rộng |
| `api` | FastAPI backend legacy | Fallback bắt buộc |
| `db` | PostgreSQL | Production |
| `ai_teacher_agent` | Worker Giáo viên AI | Python, production |
| `livekit` | Live classroom/audio | Production |
| `nginx` | Reverse proxy, TLS, static assets | Production |

## Rust API Gateway

Rust hiện xử lý:

- `GET /health`
- `GET /api/v1/ranks`
- `GET /api/v1/content/ratings`
- `GET /api/v1/internal/db-health`
- 401 native cho một số route cần auth khi request không có token
- proxy fallback sang FastAPI cho route chưa migrate

Rust hiện vẫn dùng HTTP server tối giản bằng standard library để build ổn định trên server ít RAM. Rust đã có foundation để kiểm tra đường TCP tới PostgreSQL, nhưng chưa chạy SQL query trực tiếp. Các route DB-heavy vẫn cần DB client, contract test và build budget trước khi migrate khỏi FastAPI.

## Legacy FastAPI

FastAPI vẫn xử lý phần lớn nghiệp vụ:

- auth write: login, refresh, reset password, đổi mật khẩu
- user profile mutations
- lớp học, live sessions, LiveKit webhook
- AI tutor, AI insights, RAG, generated content
- quiz submit, lesson progress, quests, leaderboard nâng cao
- admin CRUD, content review, analytics
- các endpoint DB-heavy chưa có Rust contract test

Không xoá FastAPI cho tới khi các nhóm endpoint trên có Rust implementation, test tương thích response shape, smoke test production và rollback plan.

## Database

PostgreSQL là nguồn dữ liệu chính. Rust đã có endpoint health DB để kiểm tra PostgreSQL reachable qua TCP, nhưng route nghiệp vụ cần DB vẫn proxy sang FastAPI cho tới khi có implementation Rust và contract test tương ứng.

Phase DB migration cần quyết định:

- Rust DB crate: `sqlx`, `tokio-postgres`, hoặc `postgres`.
- async runtime: Axum/Tokio hoặc tiếp tục sync gateway trong ngắn hạn.
- contract test so sánh response Rust với FastAPI.
- migration rollback khi schema hoặc query lệch.

## Nguyên Tắc Migration Sang Rust

- Chuyển từng nhóm endpoint nhỏ.
- Ưu tiên route read-only, ít side effect, response ổn định.
- Không fake dữ liệu DB chỉ để gọi là migrate.
- Giữ Python fallback cho tới khi coverage đủ.
- Mỗi phase có plan MD, commit nhỏ, test, deploy, smoke test.
- Chỉ cleanup code cũ sau khi không còn traffic production phụ thuộc vào nó.

## Các Phase Đã Xong

| Phase | Kết quả |
| --- | --- |
| Rust sidecar | Thêm service `api_rust` |
| Rust gateway | Route API qua Rust, fallback sang FastAPI |
| Auth guard | Native 401 cho một số route read khi thiếu token |
| Ranks | `GET /api/v1/ranks` native |
| Content ratings | `GET /api/v1/content/ratings` native |
| DB foundation | Rust kiểm tra PostgreSQL reachable qua `GET /api/v1/internal/db-health` |

## Phase Nên Làm Tiếp

1. Contract testing: snapshot response FastAPI vs Rust cho các route đã migrate.
2. Rust DB foundation: chọn crate DB, query health, connection pool, error shape.
3. Read-only DB routes: badges, tags, content metadata, public profile summary.
4. Auth read routes: `/auth/me`, collection, user badges, streak.
5. Mutation routes ít side effect: profile update, daily goal settings.
6. Core learning routes: lesson progress, quiz submit, quests.
7. Heavy routes: AI, LiveKit, RAG, analytics, admin workflows.

## Cleanup Strategy

Cleanup chỉ làm khi có bằng chứng không còn dependency:

- Docker: prune build cache, dangling images, stopped containers, unused volumes.
- Code: xoá FastAPI route theo nhóm đã fully migrated, không xoá toàn bộ backend cũ sớm.
- Docs: cập nhật architecture và documentation index sau mỗi phase lớn.
- Data: không xoá volume DB hoặc uploads nếu chưa backup và chưa có xác nhận rõ.
