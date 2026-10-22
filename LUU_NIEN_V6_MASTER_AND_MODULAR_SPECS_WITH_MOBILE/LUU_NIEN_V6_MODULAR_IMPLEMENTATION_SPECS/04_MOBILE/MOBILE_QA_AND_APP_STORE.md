# MOBILE QA, ANDROID/iOS STORES & OPERATIONS

> **Kết quả test:** chưa chạy build và store publish trong tác vụ xây spec. Mọi mục sau là release gates phải được xác minh; ghi `NOT_RUN` khi thiếu toolchain.

## Continuous Integration matrix

| Job | Environment | Required commands/tests | Failure gate |
|---|---|---|---|
| Flutter lint/unit | pinned Flutter SDK on Linux | `flutter pub get`, `flutter analyze`, `flutter test --coverage` | any failure |
| DTO generated | Linux | build_runner generate and `git diff --exit-code` | generated drift |
| Android debug integration | Android emulator | install, login, catalog, ELLO, offline, 3D, logout | UI/API regression |
| Android release | managed signing runner | signed AAB, signature verify, no fallback key | debug signing/P0 |
| iOS (only when created) | macOS, Xcode pinned | `flutter build ios`, simulator e2e, TestFlight IPA signed | missing iOS runner |
| Backend contract | disposable DB and Rust gateway | OpenAPI diff, RBAC, 5xx, 409/429, migration | type/schema mismatch |
| Privacy/security | staging | MITM-approved instrumentation, token redaction, tenant isolation | PII/token exposure |
| AI evidence | staging approved-source store | fake citations/injection/rights revoke | unsupported factual text |
| Media/offline | device farm | 3D GLB bad, 2D fallback, offline kill, rights purge | wrong state/fake data |

## Test cases with specific expected results

| ID | Scenario | Preconditions/action | Expected |
|---|---|---|---|
| MQ-01 | Empty new account | Create user, 0 friends/progress | 0 records + onboarding; no demo identities |
| MQ-02 | Backend 500 | Dashboard returns 500 | typed retry, no mock population |
| MQ-03 | 401 parallel | Ten protected requests at token expiry | 1 refresh flow, no lost authorizations |
| MQ-04 | Offline conflict | Draft updated on device B | 409 conflict with local draft retained |
| MQ-05 | Offline duplicate | Commit succeeds but ACK dropped | one server mutation after retry |
| MQ-06 | Cross-account queue | A queues then logs out, B logs in | A outbox never sync under B |
| MQ-07 | Unverified heritage | Source `review_status=draft` | no public verified detail |
| MQ-08 | Rights revoked | Downloaded GLB then revoked | media invalidated and fallback displayed |
| MQ-09 | Placeholder quest | Navigate Quest and Quest Detail | real route or explicit disabled feature, no skeleton UI |
| MQ-10 | Quiz score forgery | Alter HTTP score/XP field | server ignores/rejects forged grade |
| MQ-11 | Fake partner success | Inquiry API returns 503 | no confirmation/ref from client |
| MQ-12 | Gemini citation failure | AI returns source id absent | abstain, no citation shown |
| MQ-13 | Android release signing | CI lacks keystore | build fails; never debug-signed AAB |
| MQ-14 | iOS target | Check out ZIP on macOS before create | report iOS absent; no false PASS |
| MQ-15 | Push previous user | Logout A, login B, push to old token | no A content shown on B |
| MQ-16 | 2D equivalence | deny camera and use weak GPU | complete exact same learning objective |
| MQ-17 | Long text accessibility | 200% system font + TalkBack/VoiceOver | labels, navigation, no content clipping |
| MQ-18 | Data-deletion request | Authorized student/guardian as applicable | server receipt and scheduled erasure evidence |
| MQ-19 | AR no-capability | Unsupported device with AR flag | graceful 2D/3D; no crash or camera loop |
| MQ-20 | Crash reporting | Trigger exception with PII in local data | logged payload redacted/disabled per consent |

## Release evidence package per platform

- Pinned Git SHA, Flutter/Dart/Gradle/Xcode versions, OpenAPI hash, migration hash, signed release artifact hash.
- Device/OS test matrix; accessibility logs; privacy/security signoff; verified store listing privacy language and age audience; screenshots of screens used.
- Signed Android AAB and internal testing track receipt; TestFlight build number and App Review assets only once iOS project and Apple entitlement ready.
- Rollback: Android staged rollout halt/old compatible build; iOS phased release stop/new app update; server expand/contract backward compatibility with last two supported app clients.
- Operational owner for outages, crash thresholds, push deliverability, asset CDN, source revocation and child privacy incidents.

## Minimum first-pass commands

```bash
cd mobile
flutter pub get
flutter analyze
flutter test
# Android release only AFTER managed signing and review.
# iOS build only on macOS after Flutter iOS platform created.
```

No checkbox can be marked PASS without command output, exit code and environment evidence. Test skip/`NOT_RUN` is distinct from failure and success.
