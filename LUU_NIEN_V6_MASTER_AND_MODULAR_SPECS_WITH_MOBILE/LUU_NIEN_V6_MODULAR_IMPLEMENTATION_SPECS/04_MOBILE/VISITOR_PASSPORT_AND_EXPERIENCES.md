# MOBILE — Verified heritage passport, QR tours, partner inquiry

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## 1. Mục tiêu và ranh giới
Startup extension: passport di sản có xác thực, tuyến tham quan và gửi yêu cầu trải nghiệm với nghệ nhân/đối tác thật. Không biến QR hoặc inquiry thành bằng chứng khách đã mua/hoàn thành trải nghiệm.

## 2. Code hiện có phải đọc và xác minh
- `frontend/src/lib/rbpc/inquiries.ts`, `frontend/src/app/rbpc/partner/page.tsx`, `backend/routers/rbpc.py` để tránh tái tạo mock đang có web.
- Mobile mới: `mobile/lib/features/passport/` và `experiences/` `[TARGET]`.

## 3. State machine và tình huống giao diện
PASSPORT_EMPTY → OBJECT_SCANNED → PROOF_PENDING/VALIDATED → STAMP_GRANTED; EXPERIENCE_LIST → REQUEST_DRAFT → SUBMITTED_SERVER → PARTNER_ACK → CONFIRMED/DECLINED/CANCELLED; không `confirmed` khi partner chưa xác nhận.

## 4. Luồng E2E và transaction boundaries
Scan QR→validate signed location/time proof server (or explicitly non-attendance discovery)→award badge if accepted→browse verified partner listing→choose slot/request→server stores inquiry→partner updates scoped status→user receives real notification. Availability must not be made up.

## 5. API/data contract `[TARGET]`
[TARGET] `POST /api/v1/passport/stamps/claims`, `GET /experiences?heritage_id=`, `POST /rbpc/inquiries` use existing RBPC after verification, `GET /rbpc/inquiries/{id}/status`. Client writes `Idempotency-Key`, no fabricated reference.

## 6. Quy tắc implement chi tiết
- GPS/location permission optional; QR signature + replay policy and event venue consent; no student precise location analytics.
- No fake partner names, booking confirmations, dates, prices or traction.
- Commerce/payment out-of-scope until legal policy, inventory, refunds, receipts and compliance pass.
- Accessibility: manual code/teacher-led alternative when camera disabled.

## 7. Test và failure injection
- Fake QR, expired nonce or duplicate scan cannot mint reward.
- Partner A cannot see inquiry for B.
- Backend 503 must show failed/pending, never `success` reference.
- Zero partner listing shows onboarding/invite, not sample real people.

## 8. Ticket bàn giao Gemini (không sửa chồng file)
M05-A01 Passport; M05-A02 QR integrity; M05-A03 listing; M05-A04 inquiry; M05-A05 partner notifications; M05-A06 rollout metrics.

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
