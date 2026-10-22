# MOBILE SOURCE AUDIT — BRANCH SNAPSHOT

> Các đường dẫn và hashes lấy từ ZIP nhánh `feat/rbpc-cultural-bridge-2026`; **đây là static audit, không phải kết quả runtime**. Các module tương lai trong đặc tả mobile là `[TARGET]`.

- `mobile/lib/core/constants/api_constants.dart` · sha256(prefix): `f2bfd640f08d13a1` · base URL hardcoded; environment config target
- `mobile/lib/routing/app_router.dart` · sha256(prefix): `b07f80c25e4224fe` · quest routes point to Placeholder; debug routing
- `mobile/lib/core/offline/offline_queue_service.dart` · sha256(prefix): `08f95492328bc013` · durable queue local, sync endpoint needs backend contract verification
- `mobile/lib/features/practice/presentation/providers/practice_provider.dart` · sha256(prefix): `aad7f332bc34fd47` · mock quiz data in runtime provider
- `mobile/lib/features/practice/presentation/screens/practice_home_screen.dart` · sha256(prefix): `5f68a1b7d649ca9a` · mock rank, due count and timer
- `mobile/lib/features/notifications/presentation/providers/notifications_provider.dart` · sha256(prefix): `ca0708630538a56b` · mock notifications
- `mobile/lib/features/social/presentation/providers/friends_provider.dart` · sha256(prefix): `3ea3e2240fcc6329` · demo friends loader
- `mobile/lib/features/learning_path/presentation/widgets/daily_lessons_widget.dart` · sha256(prefix): `1e50fded85f7a8c2` · fallback fake dashboard summary
- `mobile/lib/features/learning_path/presentation/widgets/urn_path_card.dart` · sha256(prefix): `891d254a6f170454` · mock urn fallback
- `mobile/android/app/build.gradle` · sha256(prefix): `2e5d36fd5d3f68e7` · release may fall back to debug signing
- `mobile/lib/core/network/interceptors/token_refresh_interceptor.dart` · sha256(prefix): `4d343587db5a2562` · refresh interceptor; verify lock and replay behavior
- `mobile/lib/main.dart` · sha256(prefix): `aec441cacf1c8872` · bootstrap Hive and Firebase messaging
- `mobile/pubspec.yaml` · sha256(prefix): `cacc6444e6f4e314` · Flutter dependencies and version 1.5.0+6

- Flutter code present: 228 `.dart` files (include generated).
- Platform directories: Android present=True; iOS present=False.
- Pubspec version: `1.5.0+6` in source snapshot.
- Existing tests: only four located below `mobile/test/`; their existence is not a passing result.
