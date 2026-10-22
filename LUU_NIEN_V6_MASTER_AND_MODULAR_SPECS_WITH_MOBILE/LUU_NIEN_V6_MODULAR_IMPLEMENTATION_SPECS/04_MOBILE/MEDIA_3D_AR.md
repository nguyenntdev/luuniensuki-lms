# MOBILE — 3D, AR, media rights and accessible 2D fallback

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## 1. Mục tiêu và ranh giới
Trình xem 3D/AR là phương tiện nhận diện hiện vật/quan hệ không gian; không chứng minh kết quả học tập. Hỗ trợ thiết bị yếu và người không cấp quyền camera. iOS AR chỉ được nhận là supported nếu plugin/platform target và thiết bị thật xác nhận.

## 2. Code hiện có phải đọc và xác minh
- `mobile/lib/features/urn_viewer/`, `mobile/lib/core/services/model_preloader.dart`, `mobile/scripts/compress-models.*`.
- `mobile/pubspec.yaml` includes `model_viewer_plus`; model-specific source licensing phải review.

## 3. State machine và tình huống giao diện
ASSET_MANIFEST_FETCH → LICENSE_ALLOWED → DOWNLOAD/CACHE_VALIDATED → RENDERING_3D / STATIC_2D → DEGRADED/UNAVAILABLE. AR_REQUEST → PERMISSION_REQUEST → SUPPORTED/UNSUPPORTED/DENIED → 2D/3D fallback.

## 4. Luồng E2E và transaction boundaries
Detail→fetch rights-safe asset manifest→select texture/GLB LOD→verify checksum→preview→tap hotspot→open approved claim and photo evidence. Invalid texture/GLB → static licensed image + explicit badge. Never upload camera frames by default.

## 5. API/data contract `[TARGET]`
[TARGET] `GET /api/v1/media/objects/{id}/manifest?platform=ios|android`, `GET /api/v1/media/assets/{id}/signed-url`. Manifest includes `sha256,size_bytes,mime,rights_status,expires_at,render_modes,hotspots,source_heritage_id,alt_text`.

## 6. Quy tắc implement chi tiết
- Cân bằng GPU/memory/bandwidth, prefetch only Wi-Fi or opt-in; respect metered network, storage quota and user download control.
- Render fallback 2D preserves same learning evidence/object ID; no forced AR.
- Hotspot coordinates/version must match geometry revision; invalid mapping disables hotspot.
- Signed rights-protected URLs must not be reused after expiry/revocation; local purge receipt.
- Android camera permissions just-in-time; iOS Info.plist descriptions if platform created.

## 7. Test và failure injection
- Test damaged GLB, checksum mismatch, 403 media revoked, offline, low RAM, camera denied, no AR capability, accessibility alt text.
- Verify frame rate and cold start on representative devices, report measured values rather than guessed SLA.
- 2D path completes same ELLO task; metadata no fabricated source.

## 8. Ticket bàn giao Gemini (không sửa chồng file)
M02-A04 asset manifest; M02-A05 3D load/fallback; M02-A06 AR device gates; M04-A04 performance budget.

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
