# Lưu Niên Sử Kí — Interactive Historical Atlas of the Nine Dynastic Urns

Bách khoa tương tác về Cửu Đỉnh — nền tảng kiến thức lịch sử và học tập tập trung vào **Cửu Đỉnh triều Nguyễn**: 9 đỉnh đồng, 162 hình đúc, bản đồ di sản, dòng thời gian, nguồn tư liệu và bằng chứng, 3D, và lớp học tập (quiz, FSRS, mastery, gamification).

Production: `https://lms.histolab.icu`

Đây là bản rebuild **history-first**: khám phá lịch sử công khai (không cần đăng nhập) là trải nghiệm chính; gamification là lớp động lực phụ trợ. Xem master spec tại `docs/specs/HISTORY_FIRST_MASTER_SPEC.md`.

## Ứng Dụng Làm Gì

- Khám phá công khai: Cửu Đỉnh, Atlas 162 hình đúc, bản đồ di sản, dòng thời gian, câu chuyện, nguồn tư liệu — không bắt buộc đăng nhập.
- Thực thể lịch sử có nguồn và bằng chứng: entity / claim / source, trạng thái kiểm chứng, quan hệ liên kết.
- Học: bài học, quiz đa dạng, ôn tập giãn cách (FSRS), mastery, rank, huy hiệu, streak.
- Giáo viên và admin: lớp học, phiên học live, trail, nội dung, phân tích dữ liệu và kiểm duyệt nguồn.
- Web app có trải nghiệm di sản 3D, AI History Tutor grounded theo nguồn, LiveKit cho lớp học live.
- Các job nền cho Giáo viên AI vẫn chạy song song với API chính.

## Kiến Trúc Hiện Tại

```text
Browser
  -> Nginx
  -> Next.js web
  -> Rust API gateway
       -> endpoint Rust native khi đã migrate
       -> fallback sang FastAPI cũ khi chưa migrate
  -> PostgreSQL
```

Các service chính:

- `frontend/` - Next.js, React, Tailwind, React Three Fiber.
- `backend-rust/` - Rust API gateway và các endpoint native đang được migrate dần.
- `backend/` - FastAPI backend cũ, vẫn dùng làm fallback trong giai đoạn migration.
- `ai_teacher_agent` - worker Python cho các tác vụ Giáo viên AI live.
- `livekit` - hạ tầng lớp học live/audio.
- `db` - PostgreSQL.
- `nginx` - reverse proxy production.

Phạm vi Rust hiện tại:

- API gateway đứng trước Python backend; route dispatch config-driven (`config/route-modes.toml`), default **native** cho mọi route đã đăng ký trong `backend-rust/src/routes/*` (auth, users, content, lessons, quizzes, progress, quests, classrooms, leaderboards, admin, timeline, trails, FSRS, streak, live...).
- Proxy fallback sang FastAPI cho route chưa native (hiện chỉ live AI teacher + AI tutor + live demo-enter).
- Chặn unauthenticated native cho một số API read.

## Chạy Local

Tạo file môi trường:

```bash
cp .env.example .env
```

Khởi động stack chính:

```bash
docker compose up -d db api api_rust web
```

URL local:

- Web: `http://127.0.0.1:3000`
- Rust API gateway: `http://127.0.0.1:8001`
- Legacy Python API: `http://127.0.0.1:8000`

Kiểm tra nhanh:

```bash
curl -s http://127.0.0.1:8001/health
curl -i http://127.0.0.1:8001/api/v1/ranks
```

Chạy riêng frontend:

```bash
cd frontend
npm install
npm run dev
```

Chạy riêng Rust:

```bash
cd backend-rust
cargo fmt --check
cargo test
cargo run
```

## Deploy Production

Production dùng `docker-compose.prod.yml`.

Deploy toàn bộ stack:

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

Chỉ deploy Rust gateway:

```bash
docker compose -f docker-compose.prod.yml build api_rust
docker compose -f docker-compose.prod.yml up -d api_rust
```

Smoke test sau deploy:

```bash
for path in / /dashboard /practice /profile /ai /health; do
  curl -k -sS -o /dev/null -w "$path %{http_code}\n" "https://lms.histolab.icu$path"
done

curl -k -sS -o /dev/null -w "/api/v1/ranks %{http_code}\n" \
  https://lms.histolab.icu/api/v1/ranks
```

Kết quả public mong đợi:

- các trang web trả `200`
- `/api/v1/ranks` khi chưa đăng nhập trả `401`

## Quy Tắc Migration Sang Rust

Backend đang được chuyển từ Python sang Rust theo từng phase nhỏ.

- Migrate từng nhóm endpoint ổn định.
- Giữ response shape tương thích với frontend hiện tại.
- Giữ Python fallback cho tới khi route Rust có test và smoke test production.
- Commit nhỏ, PR nhỏ; không gom nhiều migration không liên quan vào một commit.
- Chạy Rust test trước khi deploy.
- Chạy API smoke test sau khi deploy.

Các target Rust nên ưu tiên là endpoint đọc dữ liệu, ít side effect, response contract đơn giản. Chưa nên chuyển sớm các luồng AI, LiveKit, auth write, admin mutation và các phần nhiều side effect nếu chưa có contract test đủ mạnh.

## Cấu Trúc Repo

- `backend/` - FastAPI app cũ, models, services, schemas, routes.
- `backend-rust/` - Rust gateway và native routes.
- `frontend/` - Next.js app.
- `mobile/` - mobile client code.
- `docs/` - tài liệu deploy, kế hoạch migration, bảo mật.
- `migrations/` - database migrations.
- `scripts/` - helper vận hành và test.
- `docker-compose.yml` - local/dev stack.
- `docker-compose.prod.yml` - production stack.
- `nginx-lms.conf` - Nginx config production.

## Tài Liệu Chính

- [Documentation Index](docs/DOCUMENTATION_INDEX.md) - bản đồ tài liệu technical, architecture, proposal, business, UI/UX, planning và scientific research.
- [Architecture](docs/ARCHITECTURE.md) - kiến trúc production hiện tại và hướng migration sang Rust.
- [Rust Backend Refactor Plan](docs/plan/2026-05-12-rust-backend-refactor-plan.md) - kế hoạch chuyển backend sang Rust theo phase.

## Lưu Ý Vận Hành

- Không commit secrets, token hoặc credential thật.
- Production secrets nằm ngoài git.
- Bản server tại `/opt/luuniensuki-lms` có thể không phải git checkout; dùng clone GitHub để commit và tạo PR.
- Nếu GitNexus báo index cũ, chạy `npx gitnexus analyze` trước khi dựa vào impact data.
