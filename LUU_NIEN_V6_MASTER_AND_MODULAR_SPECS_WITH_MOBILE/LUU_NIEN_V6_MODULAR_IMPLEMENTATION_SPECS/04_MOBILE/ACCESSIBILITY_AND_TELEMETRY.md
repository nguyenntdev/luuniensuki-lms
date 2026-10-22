# MOBILE — Inclusive learning, privacy-safe analytics and performance

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## 1. Mục tiêu và ranh giới
Ứng dụng phải hỗ trợ học sinh không có AR/camera, thiết bị yếu, kết nối giới hạn hoặc nhu cầu tiếp cận khác nhau. Analytics vận hành/khởi nghiệp tách biệt với nghiên cứu Google Forms 1.502 học sinh.

## 2. Code hiện có phải đọc và xác minh
- `mobile/lib/core/theme/`, `mobile/lib/features/settings/`, Flutter media/3D widgets; server analytic domains separate.
- Existing sample survey is self-reported perceived attitudes and cannot measure learning gain.

## 3. State machine và tình huống giao diện
ACCESSIBILITY_DEFAULT → CUSTOMIZED → PERSISTED; analytics state NOT_CONSENTED → CONSENTED → WITHDRAWN. Offline-only users must remain fully able to browse verified 2D and perform saved learning drafts.

## 4. Luồng E2E và transaction boundaries
User opens settings→chooses text scale/high contrast/reduced motion/data saver/2D mode→preferences persist per device→ALL learning journeys still achievable. Event instrumentation opt-in where required; deletion/withdrawal verified server-side.

## 5. API/data contract `[TARGET]`
[TARGET] `POST /api/v1/analytics/events` with allowlisted event codes and pseudonymous session; `/api/v1/privacy/preferences`, `POST /api/v1/privacy/delete-request`. Never include typed free-text answers, exact location, grade or access token in event payload.

## 6. Quy tắc implement chi tiết
- Minimum WCAG-compatible semantics and touch targets; TalkBack/VoiceOver labels for icons/3D controls.
- Reduced motion disables confetti/animations; app remains usable with 200% text size.
- Course content offline via verified text+2D; cannot gate curriculum behind camera permission.
- Product conversion analytics use event provenance; do not combine with identifiable survey responses.

## 7. Test và failure injection
- Dark/light contrast tests, keyboard/focus order, screen reader checks, weak GPU, audio off.
- Consent withdrawal stops analytics and new push; instrumentation logs redact PII.
- Synthetic trials only in pitch until real metrics audited.

## 8. Ticket bàn giao Gemini (không sửa chồng file)
M03-A09 accessibility; M03-A10 analytics contract; M05-A07 external learner pilot; M05-A08 consent/privacy review.

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
