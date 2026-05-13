# Phase: Rust native tags endpoint

## Mục tiêu

Chuyển `GET /api/v1/tags` sang Rust native bằng PostgreSQL client std-only hiện có.

## Lý do chọn route

- Public read-only.
- Query đơn giản.
- Response nhỏ.
- Production hiện trả mảng rỗng, dễ giữ tương thích.

## Phạm vi

1. Thêm route native cho `/api/v1/tags`.
2. Hỗ trợ optional query `tag_type`.
3. Query bảng `tags` với `is_active = true`, sort theo `name`.
4. Giữ JSON shape giống FastAPI: `id`, `slug`, `name`, `tag_type`, `description`, `is_active`, `created_at`.
5. Thêm contract smoke test cho route tags.

## Rủi ro

GitNexus báo HIGH khi sửa các hàm query PostgreSQL shared với DB health. Mitigation:

- Không đổi auth/SCRAM behavior.
- Giữ `SELECT 1` health test.
- Thêm unit test row parsing/JSON shape.
- Chạy production contract public + auth.

## Validation

- `cargo fmt --check`
- `cargo test -j 1`
- deploy `api_rust`
- `GET /api/v1/tags` trả 200
- contract script pass
