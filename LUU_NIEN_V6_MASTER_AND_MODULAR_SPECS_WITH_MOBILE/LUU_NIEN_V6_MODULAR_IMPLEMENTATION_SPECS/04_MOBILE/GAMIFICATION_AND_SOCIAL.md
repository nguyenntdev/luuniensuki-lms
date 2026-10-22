# MOBILE — Real practice, quests, FSRS, XP/hearts/gems, achievements and friends

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## 1. Mục tiêu và ranh giới
Gamification phải là dữ liệu server-truth có thể audit; không thay thành tích học tập bằng số lần bấm, không dùng mock rank/due/question trong production. Kích hoạt tương tác xã hội có cân nhắc an toàn trẻ vị thành niên.

## 2. Code hiện có phải đọc và xác minh
- `mobile/lib/features/{practice,quiz,learning_path,hearts,gems,daily_goals,streak,achievements,social}/`.
- `practice_provider.dart`, `quiz_session_provider.dart`, `practice_home_screen.dart`, `friends_provider.dart` và `notifications_provider.dart` có đường mock ghi trong source.

## 3. State machine và tình huống giao diện
QUEST_LIST → ACCEPTED → IN_PROGRESS → CLAIM_REWARD_PENDING → REWARD_GRANTED / REJECTED. PRACTICE_DUE → SESSION → SERVER_EVALUATION → FSRS_UPDATE; FRIEND_REQUEST → PENDING → ACCEPTED/DECLINED/BLOCKED.

## 4. Luồng E2E và transaction boundaries
Server issues signed reward rules and challenges→user performs verifiable action→server validates event/scope and records reward ledger→client refreshes balance. FSRS updates require reviewed question identity and server-authoritative outcome; friend requests allow block/report and disable for age policy.

## 5. API/data contract `[TARGET]`
[TARGET] `GET /api/v1/practice/due`, `POST /practice/sessions`, `POST /quiz/{id}/submit`, `GET /gamification/wallet`, `GET/POST /quests`, `POST /friends/requests`, `POST /friends/{id}/block`. Verify existing routes and reuse them.

## 6. Quy tắc implement chi tiết
- Eliminate `MockQuizData` reads in actual routes; seed in fixture/test only.
- XP/hearts/gems use append-only server ledger, no client mutable totals; no purchases until financial/legal readiness.
- Social discovery off by default for minors unless consent and safety review; private by default, no precise student school/location publicly exposed.
- Streaks should not manipulate compulsive activity or penalize access barriers; optional reminders and quiet hours.

## 7. Test và failure injection
- Duplicate reward POST yields single grant; edit request to +1e9 gems rejected.
- Fresh account has genuinely empty friends/quests and realistic zero progress; test disabled route not placeholder.
- Friend block stops messaging and search visibility.
- Due count must match server/test fixture and cannot be hardcoded.

## 8. Ticket bàn giao Gemini (không sửa chồng file)
M02-A07 real practice; M02-A08 quests; M02-A09 wallets/rewards; M02-A10 friends/privacy; M04-A07 abuse tests.

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
