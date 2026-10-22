# LƯU NIÊN V6 — MASTER IMPLEMENTATION SPEC

**Source branch:** `feat/rbpc-cultural-bridge-2026` (ZIP provided; SHA must be pinned from local git before implementation).  
**Status:** Design and static-audit-derived implementation specifications; **NOT** a claim that production or mobile releases have passed.  
**Primary users:** CTO/technical lead, Gemini Flash coding implementer, historian/source reviewers, teachers/researchers, product/startup lead.  
**Canonical scope:** Web Next.js, Flutter Android + prospective iOS, Rust gateway, FastAPI, PostgreSQL, verified heritage data, source-linked LMS, AI Research Factory, AI Tutor, marketplace, operations, privacy, research and startup.

## 0. Cách dùng bộ spec này (bắt buộc)

1. Đọc `MASTER_SPEC.md` và `README.md` trước. Không nạp toàn bộ các file hay bản gốc V5 vào một context của Gemini.
2. Xác thực checkout ZIP/branch và snapshot commit SHA, chạy baseline tests trong môi trường disposable; lưu `artifacts/implementation/SOURCE_LOCK.json` và command receipts.
3. Đọc chính xác **một** `V5-Txxx` ticket hoặc **một** `Mxx-Ayy` mobile ticket hoặc **một** `AIR-xxx` agent infra ticket, cộng một spec miền có liên quan.
4. Tìm đúng source files: không tự tạo backend/router trùng, không chỉnh root legacy monolith khi route live thuộc `backend/` và Rust gateway; đọc AGENTS.md của repo.
5. Test lỗi trước, sửa diff nhỏ, chạy test hẹp → test rộng, nộp report file:line, exit code, SHA, API/schema diff và PR. Không nói PASS nếu không chạy.
6. Các agent cùng wave dùng worktree/file lock; 10 slot trong spec nghĩa cần scheduler/worker thực sự chạy đồng thời, có trace; quota thấp hơn thì ghi `CAPACITY_BLOCKED`.
7. Human expert phải xác nhận nguồn sử liệu, Hán–Nôm, quyền media và phát hành. AI tự tìm/trích/viết không được tự phê duyệt.
8. Khi chưa biết route, credentials, source rights, consent hoặc migration: trạng thái `BLOCKED`, không bịa dữ liệu, API, hoặc kết quả thử nghiệm.

## 1. Nguyên tắc bất biến ở cấp chương trình

- **NO MOCK IN PRODUCTION:** không fake-success, fake-partner, fake-booking, fake-grade, fake-citation, fake-progress, fake-traction; demo fixtures chỉ trong tenant/chế độ demo đã cô lập.
- **SINGLE SOURCE OF TRUTH:** server sở hữu identity, roles, historical approvals, lesson/rubric versions, grading, wallet ledger, partner inquiry. Flutter và Next.js là client của API contract thống nhất.
- **162 DISTINCT SUBJECTS:** 9 urns × 18 reliefs; record hiện có từng đánh dấu AI-generated, cần xác minh sử liệu và quyền trước khi công bố, không tự giả sử đủ mesh 3D hoặc đủ trích nguồn.
- **MINOR SAFETY:** dữ liệu học sinh tối thiểu, quyền truy cập trường/lớp chặt, consent/guardian theo bối cảnh áp dụng, xóa/thu hồi có audit; không gửi PII tới LLM.
- **RESEARCH HONESTY:** 1.502 Google Forms là khảo sát cảm nhận; không chứng minh cải thiện tư duy lịch sử khi thiếu bài đánh giá trực tiếp.
- **CONCURRENCY TRUTH:** 12 historical phases × 10 research subagents là kiến trúc đích; 13 V5 dev waves × 10 và 6 mobile waves × 10 là kế hoạch điều phối, không khẳng định code đã chạy concurrent.
- **NO BIG BANG:** migrate expand/contract, review schema before merge, pilot 1 → 3 → gradually 162 reliefs; feature flags, monitoring, rollback.

## 2. Trạng thái spec và trách nhiệm

| Nhãn | Định nghĩa | Cách dùng |
|---|---|---|
| `SOURCE_OBSERVED` | Quan sát trong ZIP, có đường dẫn/sha | không suy ra runtime pass |
| `V5_INHERITED` | Nội dung đã có trong V5 được giữ theo module | rà soát lại trước code |
| `V6_TARGET` | Thiết kế/tính năng bổ sung | chỉ implement sau contract owner |
| `BLOCKED` | Thiếu nguồn, quyền, infrastructure hoặc API | yêu cầu owner giải quyết |
| `NOT_RUN` | Chưa thực thi test/build | không được PASS |
| `VERIFIED_PASS` | Có exit code, log, SHA và reviewer signoff | mới đóng ticket |

## 3. Kiến trúc hệ thống đích

```text
Next.js Web / Teacher Admin / Partner Portal   Flutter Android / iOS [TARGET]
                 \                                    /
               HTTPS, auth, consent, feature flags
                            |
                 Reverse proxy / Rust Axum gateway
                            |
           route registry / FastAPI domain routers
                            |
       ┌───────────────┬─────────────┬───────────────┐
       │ Heritage      │ Learning    │ RBPC partner  │
       │ Evidence      │ Gradebook   │ Inquiry       │
       │ Media         │ Wallet      │ Experience    │
       └───────────────┴─────────────┴───────────────┘
                            |
               PostgreSQL + rights-aware object store
                            |
     AI Research Factory [12 phase x 10 concurrent agent jobs]
                            |
            signed historical review / release manifest
                            |
          approved source-only Retrieval + AI Tutor
                            |
              Observability / Backups / CI-CD
```

All dotted/target services require repository investigation; diagram is desired architecture, not deployment proof.

## 4. Critical path — khi Gemini triển khai

| Gate | Must be delivered | Main specs |
|---|---|---|
| G0 | SHA lock, baseline tests, inventory of mocks, migration/router authority | `01_CORE/V5_02_CODEBASE_BASELINE.md`, `01_CORE/V5_03_MOCK_AUDIT.md`, `07_DELIVERY/W00_10_CONCURRENT_DEVELOPMENT_AGENTS.md` |
| G1 | No fake inquiry/grade and server RBAC; stable identity | `07_DELIVERY/W01_10_CONCURRENT_DEVELOPMENT_AGENTS.md`, `04_MOBILE/AUTH_AND_GUARDIAN.md` |
| G2 | Verified heritage/claims/media and approved 1→3 pilot reliefs | `01_CORE/V5_07_HERITAGE_162_RECORDS.md`, `03_AI_FACTORY/PHASE_P00_TEN_RESEARCH_AGENTS.md` |
| G3 | Server-graded ELLO, genuine practice and mobile parity | `07_DELIVERY/W03_10_CONCURRENT_DEVELOPMENT_AGENTS.md`, `04_MOBILE/LMS_ELLO_CLASSROOM.md` |
| G4 | AI jobs/citation evaluation, human review, no source hallucinations | `03_AI_FACTORY/V3_C02_FACTORY_ARCHITECTURE.md`, `03_AI_FACTORY/AIR_001_TO_005_ENGINEERING_PACKETS.md` |
| G5 | Android release hardening; iOS target only after macOS/Apple signoff | `04_MOBILE/ANDROID_RELEASE.md`, `04_MOBILE/IOS_TARGET_AND_RELEASE.md` |
| G6 | Visitor partner journeys and real verified startup traction | `05_CROSS_PLATFORM/PRODUCT_PRODUCTION_AND_STARTUP_GATES.md` |
| G7 | Observability, backup/restore, privacy, release review | `01_CORE/V5_11_PRODUCTION_SECURITY_SRE.md`, `04_MOBILE/MOBILE_QA_AND_APP_STORE.md` |

## 5. How to run ten agents without merge collisions

- Research P00–P11: dispatch ten **role-specific** packets from `03_AI_FACTORY/PHASE_Pxx_TEN_RESEARCH_AGENTS.md`; immutable artifact per worker; barrier before next phase; typed provenance; cost/time/lease monitoring.
- Development W00–W12: dispatch ten V5 ticket packets from one `07_DELIVERY/Wxx_10_CONCURRENT_DEVELOPMENT_AGENTS.md` into different worktrees; coordinator owns shared migrations and merge order.
- Mobile M00–M05: dispatch ten mobile tickets from `04_MOBILE/MOBILE_60_TICKET_ROADMAP.md`; cross-stack owner handles Flutter/client-generation and shared backend migrations.
- A 10-slot dispatch must actually observe concurrency in telemetry. Never present sequential LLM messages as concurrent workers. Failed/blocked slot cannot be silently replaced by fictitious success.

## 6. Mobile apps are full product targets, not a landing-page wrapper

- Android source present but release signing can fallback to debug: a P0 launch gate.
- iOS folder absent in supplied ZIP: deliver new iOS target via macOS/Xcode and run TestFlight evidence; do not claim existing support.
- Flutter app currently has Quest placeholders and multiple mock runtime practice/friends/notifications; these are explicit completion tickets.
- Offline queue calls `/api/v1/offline/sync` and requires server route verification plus conflict/idempotency design.
- Flutter web and native must use same approved historical corpus, source passage/citation, lessons, AI Tutor and RBPC partner rules.

## 7. Research, rights and startup product constraints

- AI-generated articles should be stored as unpublished drafts with sentence-level claim-source traceability and independent historical expertise review.
- Article and survey claims map into `06_RESEARCH/PAPER_TO_CODE_TRACEABILITY.md`, not simulated gains or fabricated evaluations.
- Startup business metrics are observed real events with evidence ledger; projections must be identified as assumptions.
- Shop/payments must remain gated pending inventory, partner permissions, legal/tax/returns and actual customer study.

## 8. Navigation — primary modules

Primary reading: `01_CORE` (V5 functional baseline) → `05_CROSS_PLATFORM` (ownership) → one of `04_MOBILE` / `03_AI_FACTORY` / `07_DELIVERY` → `08_GEMINI_OPERATOR` (prompts/tests) → `09_SOURCE_APPENDICES` (deep source evidence if needed). `99_ARCHIVE` is for provenance only, never preload into model context.

### 01_CORE

| Spec file | Purpose | Lines |
|---|---|---:|
| [`01_CORE/V5_00_HOW_TO_USE.md`](01_CORE/V5_00_HOW_TO_USE.md) | V5 main chapter 0 | 16 |
| [`01_CORE/V5_01_PRODUCT_MISSION.md`](01_CORE/V5_01_PRODUCT_MISSION.md) | V5 main chapter 1 | 36 |
| [`01_CORE/V5_02_CODEBASE_BASELINE.md`](01_CORE/V5_02_CODEBASE_BASELINE.md) | V5 main chapter 2 | 27 |
| [`01_CORE/V5_03_MOCK_AUDIT.md`](01_CORE/V5_03_MOCK_AUDIT.md) | V5 main chapter 3 | 45 |
| [`01_CORE/V5_04_TARGET_ARCHITECTURE.md`](01_CORE/V5_04_TARGET_ARCHITECTURE.md) | V5 main chapter 4 | 83 |
| [`01_CORE/V5_05_DATA_API_EVENT_CONTRACTS.md`](01_CORE/V5_05_DATA_API_EVENT_CONTRACTS.md) | V5 main chapter 5 | 93 |
| [`01_CORE/V5_06_END_TO_END_JOURNEYS.md`](01_CORE/V5_06_END_TO_END_JOURNEYS.md) | V5 main chapter 6 | 39 |
| [`01_CORE/V5_07_HERITAGE_162_RECORDS.md`](01_CORE/V5_07_HERITAGE_162_RECORDS.md) | V5 main chapter 7 | 78 |
| [`01_CORE/V5_08_AI_FACTORY_OVERVIEW.md`](01_CORE/V5_08_AI_FACTORY_OVERVIEW.md) | V5 main chapter 8 | 57 |
| [`01_CORE/V5_09_NEW_FEATURE_ROADMAP.md`](01_CORE/V5_09_NEW_FEATURE_ROADMAP.md) | V5 main chapter 9 | 52 |
| [`01_CORE/V5_10_STARTUP_GTM_BUSINESS.md`](01_CORE/V5_10_STARTUP_GTM_BUSINESS.md) | V5 main chapter 10 | 82 |
| [`01_CORE/V5_11_PRODUCTION_SECURITY_SRE.md`](01_CORE/V5_11_PRODUCTION_SECURITY_SRE.md) | V5 main chapter 11 | 59 |
| [`01_CORE/V5_12_GOOGLE_FORMS_ANALYTICS.md`](01_CORE/V5_12_GOOGLE_FORMS_ANALYTICS.md) | V5 main chapter 12 | 23 |
| [`01_CORE/V5_13_RELEASE_ROADMAP.md`](01_CORE/V5_13_RELEASE_ROADMAP.md) | V5 main chapter 13 | 23 |
| [`01_CORE/V5_15_HANDOFF_AND_REVIEW.md`](01_CORE/V5_15_HANDOFF_AND_REVIEW.md) | V5 15 HANDOFF AND REVIEW | 92 |

### 03_AI_FACTORY

| Spec file | Purpose | Lines |
|---|---|---:|
| [`03_AI_FACTORY/AIR_001_TO_005_ENGINEERING_PACKETS.md`](03_AI_FACTORY/AIR_001_TO_005_ENGINEERING_PACKETS.md) | Engineering AI ticket AIR 1-5 | 235 |
| [`03_AI_FACTORY/AIR_006_TO_010_ENGINEERING_PACKETS.md`](03_AI_FACTORY/AIR_006_TO_010_ENGINEERING_PACKETS.md) | Engineering AI ticket AIR 6-10 | 235 |
| [`03_AI_FACTORY/AIR_011_TO_015_ENGINEERING_PACKETS.md`](03_AI_FACTORY/AIR_011_TO_015_ENGINEERING_PACKETS.md) | Engineering AI ticket AIR 11-15 | 235 |
| [`03_AI_FACTORY/AIR_016_TO_020_ENGINEERING_PACKETS.md`](03_AI_FACTORY/AIR_016_TO_020_ENGINEERING_PACKETS.md) | Engineering AI ticket AIR 16-20 | 235 |
| [`03_AI_FACTORY/AIR_021_TO_025_ENGINEERING_PACKETS.md`](03_AI_FACTORY/AIR_021_TO_025_ENGINEERING_PACKETS.md) | Engineering AI ticket AIR 21-25 | 235 |
| [`03_AI_FACTORY/AIR_026_TO_030_ENGINEERING_PACKETS.md`](03_AI_FACTORY/AIR_026_TO_030_ENGINEERING_PACKETS.md) | Engineering AI ticket AIR 26-30 | 235 |
| [`03_AI_FACTORY/AIR_031_TO_035_ENGINEERING_PACKETS.md`](03_AI_FACTORY/AIR_031_TO_035_ENGINEERING_PACKETS.md) | Engineering AI ticket AIR 31-35 | 235 |
| [`03_AI_FACTORY/AIR_036_TO_040_ENGINEERING_PACKETS.md`](03_AI_FACTORY/AIR_036_TO_040_ENGINEERING_PACKETS.md) | Engineering AI ticket AIR 36-40 | 235 |
| [`03_AI_FACTORY/AIR_041_TO_045_ENGINEERING_PACKETS.md`](03_AI_FACTORY/AIR_041_TO_045_ENGINEERING_PACKETS.md) | Engineering AI ticket AIR 41-45 | 236 |
| [`03_AI_FACTORY/ENGINEERING_AIR_INDEX.md`](03_AI_FACTORY/ENGINEERING_AIR_INDEX.md) | ENGINEERING AIR INDEX | 9 |
| [`03_AI_FACTORY/PHASE_P00_TEN_RESEARCH_AGENTS.md`](03_AI_FACTORY/PHASE_P00_TEN_RESEARCH_AGENTS.md) | AI research phase P00 | 353 |
| [`03_AI_FACTORY/PHASE_P01_TEN_RESEARCH_AGENTS.md`](03_AI_FACTORY/PHASE_P01_TEN_RESEARCH_AGENTS.md) | AI research phase P01 | 353 |
| [`03_AI_FACTORY/PHASE_P02_TEN_RESEARCH_AGENTS.md`](03_AI_FACTORY/PHASE_P02_TEN_RESEARCH_AGENTS.md) | AI research phase P02 | 353 |
| [`03_AI_FACTORY/PHASE_P03_TEN_RESEARCH_AGENTS.md`](03_AI_FACTORY/PHASE_P03_TEN_RESEARCH_AGENTS.md) | AI research phase P03 | 353 |
| [`03_AI_FACTORY/PHASE_P04_TEN_RESEARCH_AGENTS.md`](03_AI_FACTORY/PHASE_P04_TEN_RESEARCH_AGENTS.md) | AI research phase P04 | 353 |
| [`03_AI_FACTORY/PHASE_P05_TEN_RESEARCH_AGENTS.md`](03_AI_FACTORY/PHASE_P05_TEN_RESEARCH_AGENTS.md) | AI research phase P05 | 353 |
| [`03_AI_FACTORY/PHASE_P06_TEN_RESEARCH_AGENTS.md`](03_AI_FACTORY/PHASE_P06_TEN_RESEARCH_AGENTS.md) | AI research phase P06 | 353 |
| [`03_AI_FACTORY/PHASE_P07_TEN_RESEARCH_AGENTS.md`](03_AI_FACTORY/PHASE_P07_TEN_RESEARCH_AGENTS.md) | AI research phase P07 | 353 |
| [`03_AI_FACTORY/PHASE_P08_TEN_RESEARCH_AGENTS.md`](03_AI_FACTORY/PHASE_P08_TEN_RESEARCH_AGENTS.md) | AI research phase P08 | 353 |
| [`03_AI_FACTORY/PHASE_P09_TEN_RESEARCH_AGENTS.md`](03_AI_FACTORY/PHASE_P09_TEN_RESEARCH_AGENTS.md) | AI research phase P09 | 353 |
| [`03_AI_FACTORY/PHASE_P10_TEN_RESEARCH_AGENTS.md`](03_AI_FACTORY/PHASE_P10_TEN_RESEARCH_AGENTS.md) | AI research phase P10 | 353 |
| [`03_AI_FACTORY/PHASE_P11_TEN_RESEARCH_AGENTS.md`](03_AI_FACTORY/PHASE_P11_TEN_RESEARCH_AGENTS.md) | AI research phase P11 | 354 |
| [`03_AI_FACTORY/V3_C00_FACTORY_ARCHITECTURE.md`](03_AI_FACTORY/V3_C00_FACTORY_ARCHITECTURE.md) | V3 C00 FACTORY ARCHITECTURE | 49 |
| [`03_AI_FACTORY/V3_C01_FACTORY_ARCHITECTURE.md`](03_AI_FACTORY/V3_C01_FACTORY_ARCHITECTURE.md) | V3 C01 FACTORY ARCHITECTURE | 384 |
| [`03_AI_FACTORY/V3_C02_FACTORY_ARCHITECTURE.md`](03_AI_FACTORY/V3_C02_FACTORY_ARCHITECTURE.md) | V3 C02 FACTORY ARCHITECTURE | 144 |
| [`03_AI_FACTORY/V3_C03_FACTORY_ARCHITECTURE.md`](03_AI_FACTORY/V3_C03_FACTORY_ARCHITECTURE.md) | V3 C03 FACTORY ARCHITECTURE | 159 |
| [`03_AI_FACTORY/V3_C04_FACTORY_ARCHITECTURE.md`](03_AI_FACTORY/V3_C04_FACTORY_ARCHITECTURE.md) | V3 C04 FACTORY ARCHITECTURE | 104 |
| [`03_AI_FACTORY/V3_C05_FACTORY_ARCHITECTURE.md`](03_AI_FACTORY/V3_C05_FACTORY_ARCHITECTURE.md) | V3 C05 FACTORY ARCHITECTURE | 113 |
| [`03_AI_FACTORY/V3_C06_FACTORY_ARCHITECTURE.md`](03_AI_FACTORY/V3_C06_FACTORY_ARCHITECTURE.md) | V3 C06 FACTORY ARCHITECTURE | 125 |
| [`03_AI_FACTORY/V3_C07_FACTORY_ARCHITECTURE.md`](03_AI_FACTORY/V3_C07_FACTORY_ARCHITECTURE.md) | V3 C07 FACTORY ARCHITECTURE | 115 |
| [`03_AI_FACTORY/V3_C08_FACTORY_ARCHITECTURE.md`](03_AI_FACTORY/V3_C08_FACTORY_ARCHITECTURE.md) | V3 C08 FACTORY ARCHITECTURE | 68 |
| [`03_AI_FACTORY/V3_C09_FACTORY_ARCHITECTURE.md`](03_AI_FACTORY/V3_C09_FACTORY_ARCHITECTURE.md) | V3 C09 FACTORY ARCHITECTURE | 73 |
| [`03_AI_FACTORY/V3_C10_FACTORY_ARCHITECTURE.md`](03_AI_FACTORY/V3_C10_FACTORY_ARCHITECTURE.md) | V3 C10 FACTORY ARCHITECTURE | 271 |
| [`03_AI_FACTORY/V3_RESEARCH_FACTORY_INTRO.md`](03_AI_FACTORY/V3_RESEARCH_FACTORY_INTRO.md) | V3 RESEARCH FACTORY INTRO | 13 |

### 04_MOBILE

| Spec file | Purpose | Lines |
|---|---|---:|
| [`04_MOBILE/ACCESSIBILITY_AND_TELEMETRY.md`](04_MOBILE/ACCESSIBILITY_AND_TELEMETRY.md) | ACCESSIBILITY AND TELEMETRY | 52 |
| [`04_MOBILE/ANDROID_RELEASE.md`](04_MOBILE/ANDROID_RELEASE.md) | ANDROID RELEASE | 58 |
| [`04_MOBILE/APP_ARCHITECTURE.md`](04_MOBILE/APP_ARCHITECTURE.md) | APP ARCHITECTURE | 56 |
| [`04_MOBILE/AUTH_AND_GUARDIAN.md`](04_MOBILE/AUTH_AND_GUARDIAN.md) | AUTH AND GUARDIAN | 54 |
| [`04_MOBILE/EXPLORE_AND_EVIDENCE.md`](04_MOBILE/EXPLORE_AND_EVIDENCE.md) | EXPLORE AND EVIDENCE | 53 |
| [`04_MOBILE/GAMIFICATION_AND_SOCIAL.md`](04_MOBILE/GAMIFICATION_AND_SOCIAL.md) | GAMIFICATION AND SOCIAL | 53 |
| [`04_MOBILE/HISTORY_AI_TUTOR.md`](04_MOBILE/HISTORY_AI_TUTOR.md) | HISTORY AI TUTOR | 52 |
| [`04_MOBILE/IOS_TARGET_AND_RELEASE.md`](04_MOBILE/IOS_TARGET_AND_RELEASE.md) | IOS TARGET AND RELEASE | 60 |
| [`04_MOBILE/LMS_ELLO_CLASSROOM.md`](04_MOBILE/LMS_ELLO_CLASSROOM.md) | LMS ELLO CLASSROOM | 53 |
| [`04_MOBILE/MEDIA_3D_AR.md`](04_MOBILE/MEDIA_3D_AR.md) | MEDIA 3D AR | 53 |
| [`04_MOBILE/MOBILE_60_TICKET_ROADMAP.md`](04_MOBILE/MOBILE_60_TICKET_ROADMAP.md) | 60 concrete mobile development tickets; 6 waves × 10 | 791 |
| [`04_MOBILE/MOBILE_API_CONTRACTS.md`](04_MOBILE/MOBILE_API_CONTRACTS.md) | Web/Flutter/backend shared mobile API contracts | 91 |
| [`04_MOBILE/MOBILE_MASTER_SPEC.md`](04_MOBILE/MOBILE_MASTER_SPEC.md) | MOBILE MASTER SPEC | 98 |
| [`04_MOBILE/MOBILE_QA_AND_APP_STORE.md`](04_MOBILE/MOBILE_QA_AND_APP_STORE.md) | Release QA and app store readiness | 63 |
| [`04_MOBILE/MOBILE_SOURCE_AUDIT.md`](04_MOBILE/MOBILE_SOURCE_AUDIT.md) | MOBILE SOURCE AUDIT | 22 |
| [`04_MOBILE/NOTIFICATIONS_AND_DEEPLINK.md`](04_MOBILE/NOTIFICATIONS_AND_DEEPLINK.md) | NOTIFICATIONS AND DEEPLINK | 53 |
| [`04_MOBILE/OFFLINE_AND_SYNC.md`](04_MOBILE/OFFLINE_AND_SYNC.md) | OFFLINE AND SYNC | 53 |
| [`04_MOBILE/VISITOR_PASSPORT_AND_EXPERIENCES.md`](04_MOBILE/VISITOR_PASSPORT_AND_EXPERIENCES.md) | VISITOR PASSPORT AND EXPERIENCES | 53 |

### 05_CROSS_PLATFORM

| Spec file | Purpose | Lines |
|---|---|---:|
| [`05_CROSS_PLATFORM/CROSS_PLATFORM_CONTRACT_MATRIX.md`](05_CROSS_PLATFORM/CROSS_PLATFORM_CONTRACT_MATRIX.md) | Shared API, source and data ownership across web and mobile | 35 |
| [`05_CROSS_PLATFORM/PRODUCT_PRODUCTION_AND_STARTUP_GATES.md`](05_CROSS_PLATFORM/PRODUCT_PRODUCTION_AND_STARTUP_GATES.md) | Production completion gates plus startup prioritization | 49 |

### 06_RESEARCH

| Spec file | Purpose | Lines |
|---|---|---:|
| [`06_RESEARCH/PAPER_TO_CODE_TRACEABILITY.md`](06_RESEARCH/PAPER_TO_CODE_TRACEABILITY.md) | PAPER TO CODE TRACEABILITY | 71 |

### 07_DELIVERY

| Spec file | Purpose | Lines |
|---|---|---:|
| [`07_DELIVERY/W00_10_CONCURRENT_DEVELOPMENT_AGENTS.md`](07_DELIVERY/W00_10_CONCURRENT_DEVELOPMENT_AGENTS.md) | V5 wave W00 | 165 |
| [`07_DELIVERY/W01_10_CONCURRENT_DEVELOPMENT_AGENTS.md`](07_DELIVERY/W01_10_CONCURRENT_DEVELOPMENT_AGENTS.md) | V5 wave W01 | 165 |
| [`07_DELIVERY/W02_10_CONCURRENT_DEVELOPMENT_AGENTS.md`](07_DELIVERY/W02_10_CONCURRENT_DEVELOPMENT_AGENTS.md) | V5 wave W02 | 165 |
| [`07_DELIVERY/W03_10_CONCURRENT_DEVELOPMENT_AGENTS.md`](07_DELIVERY/W03_10_CONCURRENT_DEVELOPMENT_AGENTS.md) | V5 wave W03 | 165 |
| [`07_DELIVERY/W04_10_CONCURRENT_DEVELOPMENT_AGENTS.md`](07_DELIVERY/W04_10_CONCURRENT_DEVELOPMENT_AGENTS.md) | V5 wave W04 | 165 |
| [`07_DELIVERY/W05_10_CONCURRENT_DEVELOPMENT_AGENTS.md`](07_DELIVERY/W05_10_CONCURRENT_DEVELOPMENT_AGENTS.md) | V5 wave W05 | 165 |
| [`07_DELIVERY/W06_10_CONCURRENT_DEVELOPMENT_AGENTS.md`](07_DELIVERY/W06_10_CONCURRENT_DEVELOPMENT_AGENTS.md) | V5 wave W06 | 165 |
| [`07_DELIVERY/W07_10_CONCURRENT_DEVELOPMENT_AGENTS.md`](07_DELIVERY/W07_10_CONCURRENT_DEVELOPMENT_AGENTS.md) | V5 wave W07 | 165 |
| [`07_DELIVERY/W08_10_CONCURRENT_DEVELOPMENT_AGENTS.md`](07_DELIVERY/W08_10_CONCURRENT_DEVELOPMENT_AGENTS.md) | V5 wave W08 | 165 |
| [`07_DELIVERY/W09_10_CONCURRENT_DEVELOPMENT_AGENTS.md`](07_DELIVERY/W09_10_CONCURRENT_DEVELOPMENT_AGENTS.md) | V5 wave W09 | 165 |
| [`07_DELIVERY/W10_10_CONCURRENT_DEVELOPMENT_AGENTS.md`](07_DELIVERY/W10_10_CONCURRENT_DEVELOPMENT_AGENTS.md) | V5 wave W10 | 165 |
| [`07_DELIVERY/W11_10_CONCURRENT_DEVELOPMENT_AGENTS.md`](07_DELIVERY/W11_10_CONCURRENT_DEVELOPMENT_AGENTS.md) | V5 wave W11 | 165 |
| [`07_DELIVERY/W12_10_CONCURRENT_DEVELOPMENT_AGENTS.md`](07_DELIVERY/W12_10_CONCURRENT_DEVELOPMENT_AGENTS.md) | V5 wave W12 | 167 |
| [`07_DELIVERY/WAVES_POLICY.md`](07_DELIVERY/WAVES_POLICY.md) | WAVES POLICY | 51 |

### 08_GEMINI_OPERATOR

| Spec file | Purpose | Lines |
|---|---|---:|
| [`08_GEMINI_OPERATOR/D00_DEVELOPMENT_AGENTS.md`](08_GEMINI_OPERATOR/D00_DEVELOPMENT_AGENTS.md) | D00 DEVELOPMENT AGENTS | 131 |
| [`08_GEMINI_OPERATOR/D01_DEVELOPMENT_AGENTS.md`](08_GEMINI_OPERATOR/D01_DEVELOPMENT_AGENTS.md) | D01 DEVELOPMENT AGENTS | 131 |
| [`08_GEMINI_OPERATOR/D02_DEVELOPMENT_AGENTS.md`](08_GEMINI_OPERATOR/D02_DEVELOPMENT_AGENTS.md) | D02 DEVELOPMENT AGENTS | 131 |
| [`08_GEMINI_OPERATOR/D03_DEVELOPMENT_AGENTS.md`](08_GEMINI_OPERATOR/D03_DEVELOPMENT_AGENTS.md) | D03 DEVELOPMENT AGENTS | 131 |
| [`08_GEMINI_OPERATOR/D04_DEVELOPMENT_AGENTS.md`](08_GEMINI_OPERATOR/D04_DEVELOPMENT_AGENTS.md) | D04 DEVELOPMENT AGENTS | 131 |
| [`08_GEMINI_OPERATOR/D05_DEVELOPMENT_AGENTS.md`](08_GEMINI_OPERATOR/D05_DEVELOPMENT_AGENTS.md) | D05 DEVELOPMENT AGENTS | 131 |
| [`08_GEMINI_OPERATOR/D06_DEVELOPMENT_AGENTS.md`](08_GEMINI_OPERATOR/D06_DEVELOPMENT_AGENTS.md) | D06 DEVELOPMENT AGENTS | 132 |
| [`08_GEMINI_OPERATOR/TEST_COMMANDS_AND_PASS_POLICY.md`](08_GEMINI_OPERATOR/TEST_COMMANDS_AND_PASS_POLICY.md) | TEST COMMANDS AND PASS POLICY | 113 |
| [`08_GEMINI_OPERATOR/V4_DEVELOPMENT_WAVES_POLICY.md`](08_GEMINI_OPERATOR/V4_DEVELOPMENT_WAVES_POLICY.md) | V4 DEVELOPMENT WAVES POLICY | 9 |
| [`08_GEMINI_OPERATOR/V4_GEMINI_RUNBOOK.md`](08_GEMINI_OPERATOR/V4_GEMINI_RUNBOOK.md) | V4 GEMINI RUNBOOK | 883 |

### 09_SOURCE_APPENDICES

| Spec file | Purpose | Lines |
|---|---|---:|
| [`09_SOURCE_APPENDICES/V2_AUDIT_AND_INVENTORY.md`](09_SOURCE_APPENDICES/V2_AUDIT_AND_INVENTORY.md) | V2 AUDIT AND INVENTORY | 2096 |
| [`09_SOURCE_APPENDICES/V2_B00_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B00_DEEP_IMPLEMENTATION.md) | V2 B00 DEEP IMPLEMENTATION | 35 |
| [`09_SOURCE_APPENDICES/V2_B01_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B01_DEEP_IMPLEMENTATION.md) | V2 B01 DEEP IMPLEMENTATION | 68 |
| [`09_SOURCE_APPENDICES/V2_B02_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B02_DEEP_IMPLEMENTATION.md) | V2 B02 DEEP IMPLEMENTATION | 90 |
| [`09_SOURCE_APPENDICES/V2_B03_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B03_DEEP_IMPLEMENTATION.md) | V2 B03 DEEP IMPLEMENTATION | 144 |
| [`09_SOURCE_APPENDICES/V2_B04_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B04_DEEP_IMPLEMENTATION.md) | V2 B04 DEEP IMPLEMENTATION | 158 |
| [`09_SOURCE_APPENDICES/V2_B05_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B05_DEEP_IMPLEMENTATION.md) | V2 B05 DEEP IMPLEMENTATION | 67 |
| [`09_SOURCE_APPENDICES/V2_B06_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B06_DEEP_IMPLEMENTATION.md) | V2 B06 DEEP IMPLEMENTATION | 119 |
| [`09_SOURCE_APPENDICES/V2_B07_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B07_DEEP_IMPLEMENTATION.md) | V2 B07 DEEP IMPLEMENTATION | 82 |
| [`09_SOURCE_APPENDICES/V2_B08_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B08_DEEP_IMPLEMENTATION.md) | V2 B08 DEEP IMPLEMENTATION | 43 |
| [`09_SOURCE_APPENDICES/V2_B09_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B09_DEEP_IMPLEMENTATION.md) | V2 B09 DEEP IMPLEMENTATION | 147 |
| [`09_SOURCE_APPENDICES/V2_B10_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B10_DEEP_IMPLEMENTATION.md) | V2 B10 DEEP IMPLEMENTATION | 51 |
| [`09_SOURCE_APPENDICES/V2_B11_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B11_DEEP_IMPLEMENTATION.md) | V2 B11 DEEP IMPLEMENTATION | 524 |
| [`09_SOURCE_APPENDICES/V2_B12_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B12_DEEP_IMPLEMENTATION.md) | V2 B12 DEEP IMPLEMENTATION | 276 |
| [`09_SOURCE_APPENDICES/V2_B13_DEEP_IMPLEMENTATION.md`](09_SOURCE_APPENDICES/V2_B13_DEEP_IMPLEMENTATION.md) | V2 B13 DEEP IMPLEMENTATION | 68 |
| [`09_SOURCE_APPENDICES/V2_ENGINEERING_BLUEPRINT_INTRO.md`](09_SOURCE_APPENDICES/V2_ENGINEERING_BLUEPRINT_INTRO.md) | V2 ENGINEERING BLUEPRINT INTRO | 9 |

### 99_ARCHIVE

| Spec file | Purpose | Lines |
|---|---|---:|

## 9. Daily Gemini handoff template

```json
{
  "ticket_id": "M02-A07",
  "baseline_source_sha": "<verified SHA>",
  "allowed_paths": ["mobile/lib/features/practice/"],
  "status": "NOT_RUN",
  "changes": [],
  "contracts": {"api": "pending verification", "migration": "none/owned by coordinator"},
  "tests": [{"command":"flutter test ...", "exit_code":null, "evidence_path":null}],
  "negative_test": {"scenario":"mock quiz removed", "result":"NOT_RUN"},
  "reviewer": null,
  "next_action": "test and handoff"
}
```

## 10. Handoff non-negotiables

- Read current `AGENTS.md`, pin branch SHA and exact files before edits.
- All contract paths in V6 are proposals until code/OpenAPI confirms existing router behavior.
- No production data or minors' PII in AI prompts, generated screenshots, tests or logs.
- Specs and test instructions are not implementation. Actual release status remains `NOT_VERIFIED` until signed evidence.

## 11. Split indexes for smaller Gemini context

- [Mobile 60-ticket index](04_MOBILE/MOBILE_60_TICKET_ROADMAP.md): split into six M00–M05 wave files, each with ten role tickets.
- [V2 original audit inventory](09_SOURCE_APPENDICES/V2_AUDIT_AND_INVENTORY.md): split into content/route/test/162-record chapters.
- [V2 technical ticket catalog](09_SOURCE_APPENDICES/V2_B11_DEEP_IMPLEMENTATION.md): split into R0–R7 owner-specific ticket groups.

## 12. Initial Gemini loader and verification

- [Gemini start prompt](GEMINI_START_HERE.md): minimal session and 10-subagent dispatch instructions.
- [V6 validation report](VALIDATION_REPORT.md): what has/has not been tested.
- [`TOOLS/validate_spec_pack.py`](TOOLS/validate_spec_pack.py): check Markdown package links and agent counts only.
