# MOBILE — Durable offline cache, outbox sync and conflict recovery

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## 1. Mục tiêu và ranh giới
Offline-first cho nội dung đã duyệt, không offline-authoritative cho điểm/giao dịch. Nâng cấp queue hiện có để rõ retry, account isolation, transaction/idempotency. Rủi ro vì `/api/v1/offline/sync` trong Dart chưa xác nhận là route backend hợp lệ.

## 2. Code hiện có phải đọc và xác minh
- `mobile/lib/core/offline/offline_queue_service.dart`: lưu queue trong Hive, trạng thái pending/syncing/completed/failed và POST `/api/v1/offline/sync`.
- `mobile/lib/core/storage/hive_storage.dart`; `mobile/lib/core/network/network_info.dart`; `backend/routers/` tìm route có liên quan, nếu không có phải tạo contract `[TARGET]`.

## 3. State machine và tình huống giao diện
LOCAL_DRAFT → QUEUED → SYNCING → ACKED / RETRYABLE / CONFLICT / PERMANENT_REJECTED / CANCELLED. Acknowledged outbox item ghi server_receipt; không xóa trước durable ack; logout chuyển queue thành xóa/xuất theo policy.

## 4. Luồng E2E và transaction boundaries
Offline quiz→save encrypted local operation with tenant/account and revision→reconnect→POST batch→backend atomically deduplicate by `operation_id/idempotency_key`→return per-item ack/conflict→UI displays server status; kill app between request and ack then retry same key without duplicate.

## 5. API/data contract `[TARGET]`
[TARGET] `POST /api/v1/offline/sync` `{client_schema_version,device_install_id,operations:[{idempotency_key,resource,resource_version,payload,created_at}]}` → `{results:[{key,state,server_receipt,server_version,conflict?}],cursor}`. Backend must validate user and resource role; accept only allowlisted resource types.

## 6. Quy tắc implement chi tiết
- Outbox includes schema migration/version TTL and retry exponential backoff with jitter; max attempts -> manual retry path.
- Do not queue payment/booking confirmation/grade approval while offline; only eligible draft/progress operations.
- Cache offline source only if rights allow; revoked object purge scheduled and at login/reconnect.
- Conflict UI: keep both local and server, surface readable diff; server grade and approved sources win for authoritative fields.

## 7. Test và failure injection
- Network drop exactly after server commit before client ack; retry same key yields one mutation.
- Two devices edit same draft: 409 with merge/resubmit, not last-write-wins silently.
- Logout/login B must not replay A queue; expired rights purge verified.
- Queue migration + app update cannot corrupt operations; test fake 5xx and backend restart.

## 8. Ticket bàn giao Gemini (không sửa chồng file)
M00-A05 backend route inventory; M01-A06 sync contract; M01-A07 outbox storage; M01-A08 conflicts/retries; M04-A08 load and fault tests.

## Nguyên tắc bất biến cho mọi luồng

- Một mutation chỉ được hiển thị `success_confirmed` nếu server xác nhận đã ghi bền vững và đúng tài khoản, hoặc hiển thị rõ `pending_sync` nếu chỉ ghi local outbox.
- Dữ liệu lịch sử phải có `published_revision`, `review_status`, `rights_status` và đường dẫn nguồn có thể xác minh. AI draft không được trình bày như sử liệu đã kiểm chứng.
- Mỗi request dùng `request_id`; các mutation retry nhận `Idempotency-Key`, có xử lý 401/403/404/409/422/429/5xx và mạng mất kết nối.
- Không gửi PII của học sinh, token, thông tin đối tác chưa được phép tới model AI/analytics/crash reporting. Ngắt đồng ý = dừng thu thập và yêu cầu xóa theo chính sách.
- Bất kỳ route đã hiện diện trong Flutter nhưng thiếu server contract phải được đánh dấu `BLOCKED_BY_BACKEND` hoặc triển khai contract thật trước; cấm chế dữ liệu làm như backend đã chạy.

## Chuẩn nghiệm thu dùng chung

1. Đã có test happy-path + unauthorized + offline/timeout + conflict + retry cùng idempotency + logout rồi đăng nhập account khác; lưu stdout/exit code.
2. Android emulator thật chạy smoke, iOS simulator chạy khi có dự án iOS và runner macOS; thiếu môi trường thì `NOT_RUN`, không PASS.
3. API contract integration kiểm tra request/response bản phát hành, type-safe DTO; nếu đổi DB có migration/rollback forward-fix bằng DB disposable.
4. UI kiểm tra VoiceOver/TalkBack, dynamic text size, tương phản, thao tác không cần gesture duy nhất, và phương án 2D khi 3D/AR lỗi.
5. Release gate dừng khi còn P0: debug signing, dữ liệu cá nhân lộ, fake success, lớp học cross-tenant, dữ liệu lịch sử chưa duyệt được công khai.
