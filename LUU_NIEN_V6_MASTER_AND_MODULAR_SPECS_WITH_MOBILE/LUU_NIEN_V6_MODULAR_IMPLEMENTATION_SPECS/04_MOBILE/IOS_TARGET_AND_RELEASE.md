# MOBILE — iOS target creation, security and App Store release

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## Crucial repository reality

`mobile/ios/` was **not present** in the uploaded ZIP snapshot. Therefore no iOS binary, TestFlight, APNs entitlement, camera permission, Universal Links, WKWebView 3D or App Store metadata can be claimed implemented. Flutter source code alone does not prove iOS deployment compatibility.

## Prerequisites and creation sequence

1. Confirm Apple Developer Program membership, Bundle ID, team, iOS minimum deployment target, encryption/export documentation, privacy policy, age rating and parental/guardian flows. Obtain macOS/Xcode runner; do not attempt iOS release build on Linux.
2. On a clean branch and verified Flutter SDK matching `pubspec.lock`, run `flutter create --platforms=ios .` **from `mobile/` only after taking a source diff snapshot**. Review generated files before commit; do not overwrite app code or generated config silently.
3. Configure Xcode project/schemes for staging/production and `--dart-define`. Explicit iOS bundle IDs and app display name; release signing through managed Apple certificates/profiles/CI vault.
4. Integrate Firebase iOS app credentials, APNs auth key, background notification and push permissions as necessary; test token binding/logout/revoke, not just registration.
5. Add `NSCameraUsageDescription` only when AR/QR requires camera; add microphone/photo permissions only if features genuinely use them. Privacy manifest and App Privacy answers must match SDK telemetry.
6. Check 3D renderer/WebView support via real iOS simulator/device: load GLB, dispose on navigation, low-memory fallback, network/cache rights, any AR Quick Look capability. Feature flag off if native AR unsupported. 2D path always works.
7. Configure associated domains and Universal Links using verified HTTPS apple-app-site-association; sanitize external redirections and expired tokens.
8. Test iOS app lifecycle (termination, background refresh, cache schema upgrade, network handover, large dynamic type, VoiceOver, reduced motion, offloaded app, push revoke).
9. Produce IPA/TestFlight through Xcode on macOS, perform internal group test, App Store Review metadata, screenshots/age rating, staged release and incident rollback plan.

## Acceptance blockers

- iOS project absent: `BLOCKED_NOT_IMPLEMENTED`, no iOS-ready claim.
- macOS/Xcode signing not run: `NOT_RUN`, no App Store ready claim.
- AR/camera functionality cannot be validated or permission rationale absent: feature flag off + 2D fallback.
- App registration conflicts with Android/backend auth domain: fix identity and link delegation first.
- Privacy/child users review incomplete: no public release.

## Commands (macOS only, after explicit owner approval)

```bash
cd mobile
flutter doctor -v
flutter create --platforms=ios .
flutter pub get
flutter analyze
flutter test
flutter build ios --release --no-codesign --dart-define=API_BASE_URL=https://YOUR_VALIDATED_HOST
```

`--no-codesign` **does not** create a distributable signed IPA and is only an intermediate check.

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
