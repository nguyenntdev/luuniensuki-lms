# Phase: Rust PostgreSQL SCRAM client

## Mục tiêu

Nâng `GET /api/v1/internal/db-health` từ kiểm tra TCP sang chạy SQL `SELECT 1` thật từ Rust, không thêm crate ngoài.

## Lý do

- PostgreSQL trong Docker đang dùng `scram-sha-256` cho host auth.
- Crate `postgres` kéo dependency tree quá nặng cho host hiện tại.
- Rust gateway đã có SHA-256, HMAC và base64 nội bộ, có thể mở rộng thành SCRAM/PBKDF2 tối thiểu.

## Phạm vi

1. Parse `DATABASE_URL` thành user, password, host, port, db name.
2. Implement PostgreSQL startup/auth SCRAM-SHA-256 tối thiểu bằng std-only.
3. Implement simple query protocol đủ cho `SELECT 1::INT`.
4. Giữ timeout ngắn.
5. Cập nhật docs: DB health là SQL health, không chỉ TCP.

## Ngoài phạm vi

- Chưa build connection pool.
- Chưa migrate route nghiệp vụ DB.
- Chưa support TLS hoặc auth method khác ngoài cleartext/SCRAM.

## Validation

- `cargo fmt`
- `cargo test`
- deploy `api_rust`
- `/api/v1/internal/db-health` trả `200` và `database:"ok"`
- contract smoke script pass public + auth
