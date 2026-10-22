# MOBILE MASTER SPEC — Flutter Android + iOS

> **Trạng thái:** Đặc tả triển khai V6 (`[TARGET]`), không đồng nghĩa đã hoàn thiện trong code. Các dẫn chiếu `mobile/...` được đối chiếu trong ZIP branch `feat/rbpc-cultural-bridge-2026`. Các endpoint `/api/v1/...` mô tả bên dưới là **contract đề xuất**, phải đối chiếu OpenAPI và router thật trước khi ghi code.
>
> **Cách thực hiện:** Mở `MASTER_SPEC.md` trước; 1 ticket/1 lượt Gemini; viết test fail trước; backend và Flutter dùng chung schema; không dựng mock-success, không tự công bố nguồn sử liệu chưa duyệt. Nếu không thể chạy lệnh, ghi `NOT_RUN` kèm nguyên nhân.


## 0. Định hướng sản phẩm

Ứng dụng dành cho học sinh, giáo viên (trong những luồng được ủy quyền), khách tham quan và người dùng di sản. Không thiết kế hệ thống mobile thứ hai tách biệt khỏi backend LƯU NIÊN; Flutter dùng chung catalogue/evidence/ELLO/AI/experience API có version và quyền rõ. Mobile không phải nguồn chân lý cho điểm, XP, giao dịch, dữ liệu sử liệu hay trạng thái đối tác.

## 1. Baseline đã đối chiếu

- `mobile/pubspec.yaml`: Flutter SDK `^3.5.4`; `flutter_riverpod`, `go_router`, `dio`, `hive_flutter`, `flutter_secure_storage`, `model_viewer_plus`, Firebase Messaging, `flutter_local_notifications`.
- `mobile/lib/routing/app_router.dart`: Quest và Quest Detail đi qua `QuestsPlaceholder`, `QuestDetailPlaceholder`; các lớp Placeholder khác tồn tại nhưng cần phân biệt active route và dead code.
- `mobile/lib/features/practice/`: một số provider/session/screens dùng `MockQuizData` và giá trị giả.
- `mobile/lib/features/social/presentation/providers/friends_provider.dart`: có routine tạo mock friends.
- `mobile/lib/features/notifications/presentation/providers/notifications_provider.dart`: dữ liệu thông báo mô phỏng.
- `mobile/lib/core/offline/offline_queue_service.dart`: đã có local outbox, đang POST `/api/v1/offline/sync`; backend router này chưa xác minh đầy đủ trong audit tĩnh.
- `mobile/android/app/build.gradle`: release ký bằng debug signing nếu thiếu `key.properties`, **chặn phát hành**.
- `mobile/android/` có; `mobile/ios/` không có trong ZIP — iOS là **target mới** cần tạo và kiểm chứng trên macOS.
- `mobile/lib/core/constants/api_constants.dart`: `baseUrl` đang hardcode, cần stage/prod routing bằng build flavor.

## 2. Kiến trúc module đích

```text
Flutter presentation (GoRouter, Riverpod)
  -> feature application controller
  -> typed repository interface
  -> Dio API / cached verified read model / outbox
  -> Rust gateway -> FastAPI/Rust domain -> PostgreSQL
  -> object storage (signed asset URLs for rights-protected media)
```

### Contract identity

- `user_id`, `school_id`, `classroom_id`, `partner_id`, `heritage_object_id` do server cấp; Flutter không tạo hoặc thay role/scope.
- `content_revision`, `course_revision`, `rubric_revision`, `asset_manifest_revision` để pin nội dung khi offline.
- `sync_cursor`, `operation_id`, `idempotency_key`, `device_install_id` (pseudonymous, rotate/delete), `request_id` dùng để phục hồi đồng bộ.

### Chuẩn màn hình

`loading`, `empty`, `ready`, `offline_verified_cache`, `pending_sync`, `sync_failed`, `conflict`, `unauthorized`, `forbidden`, `needs_review`, `unavailable`, `success_confirmed`.

## 3. Modules và tài liệu bắt buộc

| Module | Spec | Scope | Release gate |
|---|---|---|---|
| Android platform | [ANDROID_RELEASE.md](ANDROID_RELEASE.md) | signing, manifest, Play policies | No debug release signing |
| iOS platform | [IOS_TARGET_AND_RELEASE.md](IOS_TARGET_AND_RELEASE.md) | create project, signing, entitlements | Real macOS iOS CI |
| Core config & networking | [APP_ARCHITECTURE.md](APP_ARCHITECTURE.md) | DI, env, DTO, auth lifecycle | contract tests |
| Auth/privacy | [AUTH_AND_GUARDIAN.md](AUTH_AND_GUARDIAN.md) | session, school/minor rules | isolation + consent |
| Explore/corpus | [EXPLORE_AND_EVIDENCE.md](EXPLORE_AND_EVIDENCE.md) | nine urns/162 reliefs, citations | published only |
| 3D/AR | [MEDIA_3D_AR.md](MEDIA_3D_AR.md) | viewer, fallback, rights | 2D equivalent |
| Learning | [LMS_ELLO_CLASSROOM.md](LMS_ELLO_CLASSROOM.md) | six-stage ELLO, rubric | server grade only |
| AI tutor | [HISTORY_AI_TUTOR.md](HISTORY_AI_TUTOR.md) | citations, hint first | approved sources only |
| Offline sync | [OFFLINE_AND_SYNC.md](OFFLINE_AND_SYNC.md) | outbox, conflict/version | no dup/false success |
| Game + social | [GAMIFICATION_AND_SOCIAL.md](GAMIFICATION_AND_SOCIAL.md) | XP/hearts/friends/quests | no mock/profile leak |
| Push | [NOTIFICATIONS_AND_DEEPLINK.md](NOTIFICATIONS_AND_DEEPLINK.md) | FCM/APNs/consent | server-owned inbox |
| Visitors/partners | [VISITOR_PASSPORT_AND_EXPERIENCES.md](VISITOR_PASSPORT_AND_EXPERIENCES.md) | proof, QR, inquiry | no fake booking |
| Accessibility/analytics | [ACCESSIBILITY_AND_TELEMETRY.md](ACCESSIBILITY_AND_TELEMETRY.md) | minors, accessibility, events | no sensitive leaks |
| API | [MOBILE_API_CONTRACTS.md](MOBILE_API_CONTRACTS.md) | authoritative contracts to align | typecheck + integration |
| Testing/release | [MOBILE_QA_AND_APP_STORE.md](MOBILE_QA_AND_APP_STORE.md) | CI/matrices/store evidence | signed prod builds |
| 6 waves × 10 | [MOBILE_60_TICKET_ROADMAP.md](MOBILE_60_TICKET_ROADMAP.md) | Gemini parallelization | dependency gates |

## 4. Quy tắc phối hợp với 13 waves V5

- Mobile wave M00/M01 là blocking prerequisites cho V5 W05; phần mobile hoàn thiện liên quan W03 (LMS), W04 (media), W06 (AI), W09 (school), W10 (visitor).
- Shared migrations/API OpenAPI schema luôn do backend coordinator merge trước khi Flutter generated client cập nhật. Mobile agents không đồng thời tự sửa `backend/models.py` hoặc migrations.
- `flutter analyze`, `flutter test`, Android debug smoke, iOS simulator, offline failure matrix bắt buộc tùy môi trường. Kết quả `NOT_RUN` không được diễn giải thành `PASS`.

## 5. Release milestones mobile

- **M0**: deterministic build + Android signing fail-closed, iOS target scaffold, auth/network contract baseline.
- **M1**: no mobile runtime mocks in real user flows, published heritage browse, working real practice + quests.
- **M2**: lessons ELLO + server grade + offline sync proven + accessible 2D/3D.
- **M3**: grounded AI tutor, notification inbox, social permissions, visitor passport and verified inquiry.
- **M4**: staged rollout, ANR/crash monitoring, store distribution, incident/rollback runbooks.

## 6. Mobile definition of done

Khi một feature được gọi production-ready, bắt buộc có hành trình đăng ký/login → thực hiện tác vụ → server commit → reload → logout → tài khoản khác với dữ liệu phân tách; có test mạng rớt, token hết hạn, duplicate retry, conflict, thiết bị yếu, app kill/relaunch, app update. Đánh giá trên 2 platform hoặc ghi rõ platform chưa kiểm chứng.

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
