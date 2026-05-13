# Phase: Rust DB foundation

## Mục tiêu

Đặt nền móng để Rust backend kiểm tra đường kết nối PostgreSQL trực tiếp, trước khi migrate các endpoint DB-heavy như badges, tags, user collection và streak.

## Phạm vi

1. Đọc `DATABASE_URL` trong Rust settings.
2. Thêm endpoint health DB native để kiểm tra Rust có thể mở kết nối TCP tới PostgreSQL.
3. Giữ `/health` hiện tại không đổi để không phá healthcheck cũ.
4. Cập nhật architecture/docs để ghi nhận Rust đã có DB foundation.
5. Build, test, deploy `api_rust`.

## Ngoài phạm vi

- Chưa chạy SQL query từ Rust trong phase này, vì PostgreSQL crate làm build vượt ngưỡng RAM hiện tại.
- Chưa migrate endpoint cần DB thật trong phase này.
- Chưa xoá FastAPI hoặc Docker image Python.
- Chưa đổi sang async framework như Axum/Tokio.

## Rủi ro

- PostgreSQL crate hiện làm build nặng hơn ngưỡng server ít RAM, nên phase này giữ std-only.
- TCP health chỉ xác nhận DB reachable, chưa xác nhận query/schema.
- Không được fake response DB chỉ để tăng số endpoint Rust native.

## Validation

- `cargo fmt --check`
- `cargo test`
- `docker compose -f docker-compose.prod.yml build api_rust`
- `docker compose -f docker-compose.prod.yml up -d api_rust`
- Smoke test:
  - `/health`
  - `/api/v1/internal/db-health`
  - routes native hiện có
  - login + ranks auth
