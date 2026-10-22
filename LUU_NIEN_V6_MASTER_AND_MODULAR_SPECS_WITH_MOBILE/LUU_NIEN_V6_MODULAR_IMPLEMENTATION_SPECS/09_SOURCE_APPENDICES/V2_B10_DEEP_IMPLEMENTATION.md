# V2 B10: source-derived engineering detail

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V2.B10`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## B10. TRIỂN KHAI THEO RELEASE GATES — DEPENDENCIES, EFFORT, HANDOFF

### B10.1 8 releases thay vì một big-bang rewrite

| Release | Goal | Dependency | Artifact quan sát được | Gate |
|---|---|---|---|---|
| R0 | snapshot, CI, environment, migration safety | raw ZIP, secrets+DB access with owner | reproducible dev env + green baseline tests | G0 |
| R1 | canonical urn/162 + evidence registry | R0, historian review | 9x18 audit board + import report | G1 |
| R2 | asset rights + reliable 2D/3D | R1, rights files | safe viewer + asset ledger | G1/G3/G4 |
| R3 | complete ELLO creator + student runner | R1/R2 | lesson release, attempt, rubric feedback | G2/G3 |
| R4 | research vault + Google Forms tables | R0 + verified survey files | frozen analysis snapshot and tables | G6 |
| R5 | trustworthy AI grounded in approved corpus | R1/R3 | eval dataset + AI with abstention | G5 |
| R6 | living heritage inquiry production | R0 + consent/partner auth | no-fake inquiry + audited partner inbox | G4/G8 |
| R7 | selected CALL/AI/ICTIM innovations | each domain's evidence | research-specific modules and results | G7 |

**Parallelism:** R4 can run after R0 independently of R1 if research files are available. R6 can be hardened separately from R3. R5 depends on R1 source quality; launching AI sooner increases risk. R7 is conditional; not required for core history LMS.

### B10.2 Team roles & approval ownership (minimum)

| Role | Responsibility | Cannot self-approve |
|---|---|---|
| Product owner | priority, scope, feature flags, release plan | scientific content if not reviewer |
| Tech lead | architecture, migration, API contracts | historical accuracy and image rights |
| Backend engineer | models, authz, services, APIs | ethics use of research data |
| Frontend/mobile | accessible flows, 2D/3D presentation | publication of unsupported claims |
| Historian/Hán-Nôm reviewer | names, inscriptions, historical context, evidence | grant rights they don't own |
| Rights/consent manager | asset rights, living heritage consents | replace historical reviewer |
| Teacher/instructional designer | ELLO learning objectives, rubrics | claim causal improvement without assessment |
| Research data custodian | survey data, pseudonymization, analysis hash | change results without audit |
| QA/security reviewer | test/penetration protocol, release gates | unverified product claims |

### B10.3 Pull-request structure and review

Use short-lived feature branches `feat/<ticket-id>-<slug>` from current integration baseline; PR title carries issue ID; attach migration dry-run, tests, screenshots/video for UI, OpenAPI diff for API, data lineage for import. No secrets or raw student dataset in PR. A blocker issue cannot be merged behind a “temporary fallback” that makes production falsely claim success.

### B10.4 Definition of Ready

Ticket ready only if: owner, affected paths, `AS-IS`, expected `TO-BE`, API/schema impact, acceptance cases, rollback, data source, dependency tickets, test fixture plan, security/privacy consequence identified. If historical claim needs verification but no source exists, ticket remains `BLOCKED_BY_SOURCE` instead of guessed completion.

### B10.5 Release checklist per environment

**DEV:** seed is clearly labeled demo; signed-in student and teacher flows compile; DB disposable; no prod credentials. **STAGING:** same migration head as production plan, sanitized datasets, real queue/rate limiter, E2E all negative paths, mobile smoke, QA signoff. **PROD:** feature flag rollout, backup restore verification, migration success, readiness probe, error dashboard, rights clearance, science/legal signoffs, post-deploy synthetic checks, canary metrics. **RESEARCH RELEASE:** independent data hash + protocol + software snapshot; never automatically equals production release.

---


