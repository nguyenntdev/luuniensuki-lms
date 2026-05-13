# Phase: Rust gateway contract tests

## Mục tiêu

Thêm contract smoke test cho các route Rust native hiện tại để mỗi phase migration sau có baseline rõ ràng.

## Phạm vi

1. Thêm script test gọi production hoặc local gateway qua `BASE_URL`.
2. Kiểm tra HTTP status và shape JSON cho:
   - `/health`
   - `/api/v1/content/ratings`
   - `/api/v1/internal/db-health`
   - `/api/v1/ranks` khi chưa auth
   - `/api/v1/ranks` sau login nếu có credential test
3. Ghi rõ cách chạy trong docs.

## Ngoài phạm vi

- Không migrate endpoint mới trong phase này.
- Không xoá Python fallback.
- Không thêm dependency mới.

## Validation

- Chạy script với production URL.
- Chạy GitNexus `detect_changes`.
- Commit nhỏ, push, PR, merge.
