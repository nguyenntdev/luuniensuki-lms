# MOBILE — Push notification inbox, deep links, user controls

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## 1. Mục tiêu và ranh giới
Thông báo phải được tạo từ sự kiện server thật, không phát dữ liệu mock dưới tên giáo viên hay bạn bè. Nội dung đẩy tới màn hình khóa giảm tối đa thông tin về trẻ vị thành niên.

## 2. Code hiện có phải đọc và xác minh
- `mobile/lib/features/notifications/`; `mobile/lib/main.dart`; `mobile/pubspec.yaml` có Firebase/FCM.
- `notifications_provider.dart`: mock data path; `mobile/PUSH_NOTIFICATIONS_BACKEND_API.md` là tài liệu, chưa chứng minh API chạy.

## 3. State machine và tình huống giao diện
NOTIFICATION_INBOX_EMPTY/READY; DEVICE_UNREGISTERED → PERMISSION_DECISION → TOKEN_REGISTERED → ROTATED/REVOKED. Deep link received logged-out → sanitized pending route → login/consent → route scope check → destination.

## 4. Luồng E2E và transaction boundaries
Backend event saved inbox + outbox→FCM/APNs message data references notification id rather than raw PII→client fetches authorized detail→mark read atomically→server updated across devices. Quiet-hours and school controls applied server-side.

## 5. API/data contract `[TARGET]`
[TARGET] `POST /api/v1/notifications/devices`, `DELETE /devices/{id}`, `GET /api/v1/notifications`, `POST /notifications/{id}/read`, `PUT /notification-preferences`. Data keys `{notification_id,link_path,event_type}` only allowlisted paths.

## 6. Quy tắc implement chi tiết
- No push content if consent revoked, account deleted or token rotated.
- Device token stored hashed/secured, bound to one user+installation.
- Deep link blocked across tenant; no untrusted `http` URL redirects.
- Android 13+ notification permission, iOS APNs entitlements/config only after iOS scaffold.

## 7. Test và failure injection
- Unauthorized fetch by notification ID → 403/404.
- Old FCM token after logout must not deliver student info.
- 500 displays retry, never inserts fake notices.
- Invalid link redirects to safe screen, not browser open redirect.

## 8. Ticket bàn giao Gemini (không sửa chồng file)
M03-A06 notification inbox API; M03-A07 push token lifecycle; M03-A08 deep-link security; M04-A09 push integration smoke.

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
