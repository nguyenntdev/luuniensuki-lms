# MOBILE — Authentication, school accounts, consent and guardians

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## 1. Mục tiêu và ranh giới
Đối tượng gồm học sinh có thể chưa thành niên, giáo viên, cán bộ biên tập, khách dùng thử. Server xác nhận vai trò, trường, lớp, quyền truy cập và đồng thuận. Không suy ra tuổi từ thiết bị; phụ huynh chỉ có quyền sau khi có cơ chế xác minh.

## 2. Code hiện có phải đọc và xác minh
- `mobile/lib/features/auth/` và `mobile/lib/core/network/interceptors/{auth_interceptor.dart,token_refresh_interceptor.dart}`.
- `mobile/lib/core/storage/secure_storage.dart`; `mobile/lib/routing/app_router.dart`.

## 3. State machine và tình huống giao diện
UNAUTHENTICATED → LOGGING_IN → SESSION_READY / CONSENT_REQUIRED / MFA_REQUIRED / LOCKED. Refresh: VALID → EXPIRED → REFRESHING → VALID/REVOKED; chỉ một refresh đồng thời, retry request tối đa một lần và không replay mutation không idempotent.

## 4. Luồng E2E và transaction boundaries
Login→server session→fetch `/auth/me`→role membership→consent→route. Logout→revoke server session→clear refresh/access tokens and tenant-local caches/queues after export/discard consent→no previous user record on re-login. Guardian consent requests never reveal student details to unverified email.

## 5. API/data contract `[TARGET]`
`POST /api/v1/auth/login`, `POST /refresh`, `GET /auth/me` = inspect existing; [TARGET] `GET/POST /api/v1/consents`, `POST /api/v1/auth/revoke`, `GET /api/v1/school-membership` subject to server contract. Session envelope `{user_id,roles,scopes,consent_state,expires_at}`; no JWT claims trusted without verification.

## 6. Quy tắc implement chi tiết
- Secure storage key isolation per user/tenant; encryption platform keystore/keychain; no credential in Hive/log.
- Auth redirect sanitization and deep-link replay protection.
- CSRF/token refresh semantics consistent with gateway; do not mix cookie and bearer arbitrarily.
- Parent guardian: verified relationship, least privilege, withdrawal cascade; no public leaderboard identities of minors.
- Rate limiting and account enumeration prevention server-side.

## 7. Test và failure injection
- Attacker requests other school `school_id` → 403; teacher A cannot view class B; consent revoked disables sensitive events.
- Token expires mid-upload/offline sync → no duplicate; old session queue cannot sync under new user.
- Two concurrent 401s call refresh once; failed refresh does not loop.
- Device screenshot logs and push previews contain no PII by default.

## 8. Ticket bàn giao Gemini (không sửa chồng file)
M00-A04 session isolation; M01-A01 login/session refresh; M01-A03 guardian/consent; M04-A10 mobile security regression.

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
