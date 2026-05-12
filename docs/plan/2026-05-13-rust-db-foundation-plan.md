# Phase: Rust DB foundation

## Mục tiêu

Đặt nền móng để Rust backend đọc PostgreSQL trực tiếp, trước khi migrate các endpoint DB-heavy như badges, tags, user collection và streak.

## Phạm vi

1. Đọc `DATABASE_URL` trong Rust settings.
2. Thêm endpoint health DB native để kiểm tra Rust có thể mở kết nối PostgreSQL và chạy query nhẹ.
3. Giữ `/health` hiện tại không đổi để không phá healthcheck cũ.
4. Cập nhật architecture/docs để ghi nhận Rust đã có DB foundation.
5. Build, test, deploy `api_rust`.

## Ngoài phạm vi

- Chưa migrate endpoint cần DB thật trong phase này.
- Chưa xoá FastAPI hoặc Docker image Python.
- Chưa đổi sang async framework như Axum/Tokio.

## Rủi ro

- Thêm PostgreSQL crate có thể làm build nặng hơn trên server ít RAM.
- Query DB trong Rust phải có timeout ngắn để không làm kẹt thread gateway.
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
