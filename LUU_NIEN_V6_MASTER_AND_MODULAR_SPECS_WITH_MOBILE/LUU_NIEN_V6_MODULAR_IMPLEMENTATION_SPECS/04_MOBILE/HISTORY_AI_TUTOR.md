# MOBILE — Grounded history tutor, uncertainty and safety

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## 1. Mục tiêu và ranh giới
AI hỗ trợ khám phá lịch sử từ nguồn đã kiểm duyệt. Không tự tạo trích dẫn, không mặc định AI response là đúng, và không cung cấp năng lực AI nếu server không có provider/authorization thực.

## 2. Code hiện có phải đọc và xác minh
- `mobile/lib/features/ai_chat/`; backend `backend/routers/ai.py`, `backend/routers/history.py` và History Tutor hiện có.
- V3 research factory khác AI tutor: 12 phase/120 roles soạn nội dung, tutor chỉ truy xuất nguồn đã phát hành.

## 3. State machine và tình huống giao diện
CHAT_READY → QUESTION_SENT → RETRIEVING → ANSWER_WITH_CITATIONS / ABSTAIN / BLOCKED_SAFETY / UNAVAILABLE. Citation tap opens source page + locator; revoked source invalidates old answer and shows correction.

## 4. Luồng E2E và transaction boundaries
Student asks about motif→server retrieval allowed school/rights-scoped passages→LLM produces schema with claim/passage ids→deterministic validator checks existence/version/license/quote→return supported answer or abstain→optional hint first→teacher can inspect anonymized evaluation (not raw minor chat by default).

## 5. API/data contract `[TARGET]`
[TARGET] `POST /api/v1/history-tutor/answers` `{question,heritage_object_id,lesson_context_id?,language,mode}` → `{answer,claims:[{claim_id,citation:{source_id,passage_id,locator}}],abstained,reason,model_version,request_id}`.

## 6. Quy tắc implement chi tiết
- Disable fallback to generic ungrounded answer in prod; model cannot assign `review_status=approved`.
- Tool output and OCR are untrusted; strip instructions from retrieved documents.
- Student interactions require privacy minimization/retention controls and age-appropriate limits.
- Distinguish language practice CALL from historical QA; no misleading "language learning effectiveness" claims.

## 7. Test và failure injection
- Fake source id should fail server validation; zero valid passages => abstain not fictional quote.
- Prompt injection in OCR quote cannot override system; rate-limit across sessions/tenants.
- Unsupported internet/AI service => clearly unavailable; errors do not show mock-generated successful response.

## 8. Ticket bàn giao Gemini (không sửa chồng file)
M04-A01 AI view; M04-A03 citations panel; M04-A05 local AI state/cost; M05-A09 adversarial cases.

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
