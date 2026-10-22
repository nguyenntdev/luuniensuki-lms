# MOBILE — Source-linked lessons, rubric, classroom and server-authoritative grading

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## 1. Mục tiêu và ranh giới
Sáu bước ELLO: định danh → nhận định tạm → nguồn → phương tiện → lập luận → phản hồi/sửa; người dùng có thể quay lại bước trước. Không dùng số lần mở 3D hay thời lượng chạm để tuyên bố tăng tư duy lịch sử.

## 2. Code hiện có phải đọc và xác minh
- `mobile/lib/features/lesson/`, `mobile/lib/features/quiz/`, `mobile/lib/features/learning_path/`, `mobile/lib/features/practice/` và `mobile/lib/core/offline`.
- `backend/routers/history_learning.py`, `backend/routers/classrooms.py` để đối chiếu endpoints thật.

## 3. State machine và tình huống giao diện
ASSIGNED → STARTED → DRAFT_LOCAL → SUBMITTING → SUBMITTED_SERVER → TEACHER_REVIEW → FEEDBACK_READY → REVISION_PENDING → COMPLETED. Offline submission remains `pending_sync`, never `submitted` until ack.

## 4. Luồng E2E và transaction boundaries
Teacher creates immutable lesson/rubric version→student downloads manifest→observes relief + source→draft explanation→submit→backend freeze submission version→rubric human/authorized server grading→feedback→revision with history; teachers see own class only.

## 5. API/data contract `[TARGET]`
[TARGET] `GET /api/v1/lessons/{id}/manifest`, `POST /api/v1/assignments/{id}/attempts`, `POST /api/v1/attempts/{id}/submissions` with idempotency/version, `GET /api/v1/attempts/{id}/feedback`. Verify existing LMS contract first.

## 6. Quy tắc implement chi tiết
- Distinguish objective quiz instant server scoring vs evidence-based open response rubric; no client grade authority.
- Submit payload pins `lesson_revision`,`rubric_revision`,`approved_source_ids`; teacher grade includes reviewer and signed rubric version.
- Accessibility: capture plain text, audio alternative, 2D source view, adequate text size.
- Teacher dashboard should be web-first initially; mobile only operations authorized by API.

## 7. Test và failure injection
- Client score forging rejected; grade of student A hidden from B.
- Offline draft survives app restart, but unauthorized new account never inherits.
- Duplicate submit same key yields one attempt; changed revision creates conflict with recovery UI.
- Rubric answer may differ linguistically yet remain defensible; no LLM grade accepted as factual authority.

## 8. Ticket bàn giao Gemini (không sửa chồng file)
M03-A01 ELLO runner; M03-A02 source-link activity; M03-A03 submission/feedback; M03-A04 server grade compatibility; M03-A05 rubric a11y.

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
