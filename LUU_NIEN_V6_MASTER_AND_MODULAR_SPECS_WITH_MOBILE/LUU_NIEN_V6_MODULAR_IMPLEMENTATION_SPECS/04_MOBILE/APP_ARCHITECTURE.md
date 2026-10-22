# MOBILE — App architecture, environment, DI and typed clients

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## 1. Mục tiêu và ranh giới
Flutter dùng một codebase, feature-first modular. Server là system of record; UI chỉ dựa trên model và API contract được version hóa. Chưa thay Riverpod/GoRouter/Dio khi chưa có bằng chứng hạn chế.

## 2. Code hiện có phải đọc và xác minh
- `mobile/lib/main.dart`: init Firebase Messaging callback và Hive trước ProviderScope.
- `mobile/lib/core/network/{api_client.dart,dio_provider.dart,interceptors/}`.
- `mobile/lib/core/constants/api_constants.dart`: prod URL hardcode.
- `mobile/lib/routing/{app_router.dart,route_names.dart}`; `mobile/pubspec.yaml`.

## 3. State machine và tình huống giao diện
BOOTSTRAP → CONFIG_LOADED → SESSION_CHECKING → AUTHENTICATED/ANONYMOUS → READY; lỗi config/asset/migration → STARTUP_RECOVERABLE/STARTUP_BLOCKED. Không log session token hoặc PII khi ở chế độ debug.

## 4. Luồng E2E và transaction boundaries
1) Parse build flavor → validate HTTPS host allowlist → load feature flags signed/typed → initialize storage schema → refresh session once → boot router. 2) Persist snapshot-independent non-sensitive preferences. 3) Deep link pending auth phải được phục hồi sau login nhưng không redirect sang domain tùy ý.

## 5. API/data contract `[TARGET]`
`GET /api/v1/mobile/bootstrap` [TARGET] → `{min_supported_version,api_contract_version,features,content_manifest_rev,maintenance}`. Base URL qua `--dart-define=API_BASE_URL=...`; OpenAPI generator dùng pinned schema. Error `{error:{code,message,request_id,details}}`.

## 6. Quy tắc implement chi tiết
- Tách `ApiConfig` (flavor staging/prod), `ApiClient`, typed DTO, `ErrorMapper`, `SessionState`, `ConnectivityState`, `ReleaseCapabilities`.
- Không dùng `contains()` chung chung cho path public; so khớp path chuẩn hóa và method.
- Không gọi `/health` thay cho feature readiness.
- Không fallback sang mock khi 500 hoặc network failure; trạng thái UI tương ứng.
- Quản lý cache bằng revision/tenant, không dùng cache cross-account.

## 7. Test và failure injection
- Config: thiếu `API_BASE_URL` prod phải fail build; URL http/plaintext bị chặn; redirect bên ngoài allowlist bị reject.
- Unit: 401 refresh singleflight, 403 không refresh vô hạn, 409 giữ draft, 429 backoff.
- Integration: backend drift schema → CI fail; `flutter analyze`, `flutter test`, build Android profile.
- Feature flags: disabled route không hiển thị và backend cũng không cho phép.

## 8. Ticket bàn giao Gemini (không sửa chồng file)
M00-A01 environment; M00-A02 typed error/DTO; M00-A03 route guard; M01-A02 auth client. Mỗi agent edit đường dẫn riêng, coordinator merge common bootstrap.

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
