# MOBILE — Nine Bronze Urns, 162 reliefs, claims and citations

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## 1. Mục tiêu và ranh giới
Mục tiêu là duyệt 9 đỉnh × 18 hình đúc nổi một cách trung thực. 162 seed record không đồng nghĩa 162 hồ sơ đã kiểm chứng. Public chỉ hiển thị revision đã duyệt, nguồn có locator, trạng thái bản quyền và thuyết minh rõ mức chắc chắn.

## 2. Code hiện có phải đọc và xác minh
- `mobile/lib/features/explore/`, `mobile/lib/features/lesson/presentation/screens/motif_detail_screen.dart`, `mobile/lib/features/history/`.
- `data/*Data*Dinh.json`: kiểm chứng id/alias/source; `backend/services/heritage_import.py` có hướng import, cần xem lại review status.

## 3. State machine và tình huống giao diện
CATALOG_LOADING → NINE_URNS_READY → RELIEF_LIST → DETAIL_VERIFIED / DRAFT_RESTRICTED / NO_SOURCE / UNAVAILABLE. Khi offline: `OFFLINE_VERIFIED_CACHE` chỉ cho revision có license và TTL phù hợp.

## 4. Luồng E2E và transaction boundaries
Browse urn→select relief→display photo/3D/2D fallback→open claim→view exact source version/page/quotation→compare competing interpretations→save local bookmark. Nếu nguồn bị thu hồi, purge CDN/local manifest và khóa citation không còn quyền.

## 5. API/data contract `[TARGET]`
[TARGET] `GET /api/v1/heritage/urns`, `/reliefs?urn_id=`, `/reliefs/{id}?revision=`, `/claims/{id}/sources`, `/sources/{id}/passages/{passage_id}`. Responses include `review_status`, `rights_scope`, `citation_locator`, `content_sha256`.

## 6. Quy tắc implement chi tiết
- Canonical `urn_id` 1–9, `relief_id`, aliases (chữ Hán, phiên âm, tên Việt/Anh) có provenance.
- Cấm infer Unicode glyph thành nghĩa lịch sử; phân biệt source transcription/translation/interpretation.
- Search/filter by chủ đề, đỉnh, motif; index cache isolate by language and published revision.
- Hiển thị ước lượng nguồn dưới dạng verified/corroborated/contested thay vì số confidence do AI tự cho.

## 7. Test và failure injection
- Golden 9×18 coverage and unique canonical IDs.
- Seed AI-generated blocked from public detail unless human approved.
- Cross-source disagreement surfaced; absent locator blocks quote.
- 404/unpublished never masquerades published, even with stale cached seed.

## 8. Ticket bàn giao Gemini (không sửa chồng file)
M02-A01 typed catalog + discovery; M02-A02 evidence detail; M02-A03 verified offline cache; M04-A02 localization and Hán–Nôm rendering.

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
