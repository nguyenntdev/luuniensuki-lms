# Phase: Rust native content ratings

## Mục tiêu

Chuyển endpoint đọc tĩnh `GET /api/v1/content/ratings` sang Rust native để giảm thêm một request phải proxy qua FastAPI.

## Lý do chọn endpoint này

- Không cần database.
- Không cần gọi AI, LiveKit hoặc service ngoài.
- Response contract nhỏ và ổn định.
- Có thể test bằng unit test và smoke test production.

## Phạm vi thay đổi

1. Thêm route native trong `backend-rust/src/main.rs`.
2. Giữ response JSON giống FastAPI hiện tại.
3. Cập nhật README Rust để phản ánh scope mới.
4. Build, test, deploy `api_rust`.
5. Smoke test `/api/v1/content/ratings` trên production.

## Ngoài phạm vi

- Chưa xoá FastAPI route cũ vì Python vẫn là fallback cho phần backend chưa migrate.
- Chưa xoá Docker image/container cũ liên quan Python vì hệ thống production vẫn cần chúng.
- Chưa thêm Rust database client trong phase này.
