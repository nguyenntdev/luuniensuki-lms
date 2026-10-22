# MOBILE — Android production release engineering

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## Source finding requiring immediate remediation (P0)

`mobile/android/app/build.gradle` currently assigns release signing as `signingConfigs.release` **if** `key.properties` exists; **else** it uses `signingConfigs.debug`. This is unacceptable for production. The app Android namespace / applicationId observed: `com.luuniensuki.lms`. `mobile/pubspec.yaml` version snapshot `1.5.0+6`.

## Implementation steps, no destructive shortcuts

1. Confirm Google Play package ownership and chosen package id; do not rename `applicationId` after published app without migration. Verify `minSdk`, `targetSdk`, Kotlin/Gradle/plugin compatibility against installed SDK; do not assume latest versions are safe.
2. Make Gradle **fail the release build** when signing material is missing; secrets from managed CI vault, not tracked `key.properties` or shared debug keystore. Separate Play upload signing key vs Play App Signing key, document rotation and owner.
3. Verify manifest permissions for INTERNET, CAMERA, notification, deep-link intent filters and any location. Remove unnecessary permissions; per-feature runtime request.
4. Build flavors `staging`, `production`, stable API host and bundle IDs if necessary; disable debug diagnostics and verbose error traces in release.
5. Manage Android keystore and mapping files via secure CI artifact; symbols uploaded privately to crash service. Verify network security config disallows cleartext except debug-only explicit policy.
6. Generate signed `appbundle` (.aab), never distribute debug `.apk` as production. Release checklist includes app privacy disclosure and data safety answers grounded in actual network behavior.
7. Test install/update/uninstall on 2 API levels, cold boot with offline, background/foreground and push permission denial, 3D GLB low memory, release AAB sign verification.
8. Internal testing track → closed testing → staged production rollout with measured crash-free and ANR metrics. Owner must hold Play Console role and rollback procedure.

## Exact guard acceptance

- Without release keystore CI should exit nonzero; never fall back to debug.
- Release bundle signature/certificate fingerprint matches approved upload keystore (record fingerprint in restricted evidence, not password).
- `flutter analyze`, `flutter test`, Gradle verification, Android emulator smoke have captured exit codes.
- App user A logout → user B login does not expose A's cached data, notification, saved draft, AI transcripts.
- Offline/403/429/500 shows real states, not data seed/mock.

## Sample non-destructive commands (adapt Flutter/Gradle versions)

```bash
cd mobile
flutter --version
flutter pub get
flutter analyze
flutter test
flutter build appbundle --release --dart-define=API_BASE_URL=https://YOUR_VALIDATED_HOST
```

**Do not execute release upload until signed artifact verification, privacy review and server contract gates pass.**

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
