# V2 original archival technical chapter — SECTION_15

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 15. CI/CD, DATABASE MIGRATIONS, QUALITY GATES

### 15.1 Pipeline proposed

```text
PR (any branch)
  ├─ format/lint + compile + static typing
  ├─ dependency/SBOM/secrets/license
  ├─ migration graph + schema diff + backward compatibility
  ├─ unit Python/Rust/Vitest/Flutter
  ├─ API contract Rust-vs-Python
  ├─ migration up/backup/down test against disposable PostgreSQL
  ├─ Playwright user journeys + a11y
  ├─ content checker (162 coverage + claim-source + rights)
  ├─ AI benchmark offline deterministic mode
  └─ signed staging artifact
STAGING
  ├─ smoke API; visual regression; backup/restore; rights/consent
  ├─ AI live provider benchmark conditional, quota-limited
  └─ human signoff historian + QA + privacy + lead
PRODUCTION (manual protected approval)
  ├─ pre-migration backup & zero unsafe heads
  ├─ migration succeed OR STOP (never || true)
  ├─ canary release/health/metrics
  └─ rollback + publish immutable manifest
```

### 15.2 Test commands baseline + production gate

```bash
# Baseline — requires installed pinned dependencies and disposable PG
python -m compileall -q backend tests
python -m pytest tests/backend tests/unit -q
cd frontend && npm ci && npm run type-check && npm run lint:ci && npm run test && npm run build && npx playwright test
cd ../backend-rust && cargo fmt --check && cargo test && cargo clippy --all-targets -- -D warnings
cd ../mobile && flutter pub get && flutter analyze && flutter test
cd .. && alembic heads --verbose && alembic upgrade heads
```

**Cảnh báo:** `alembic upgrade heads` chỉ được dùng trong **disposable test DB** sau khi rà soát migrations. Production phải có merge/reconciliation plan và một head rõ ràng (hoặc chính sách multi-head có chủ đích được chứng minh).

### 15.3 Tests bắt buộc theo domain

| Test ID | Scenario | Expected |
|---|---|---|
| T-DB-001 | Alembic graph with conflicting branch heads | CI fails with actionable diff |
| T-DATA-001 | 162 AI-generated records lack sources | all quarantined; no published claim leakage |
| T-DATA-002 | 9 urn/162 verified identity catalog | count exact after mapping; no misplaced label |
| T-SOURCE-001 | remove source of published claim | publish blocked / claim rolled back |
| T-SOURCE-002 | disputed sources | both visible with epistemic label |
| T-MEDIA-001 | unlicensed Sketchfab model | no rehost; 2D fallback |
| T-MEDIA-002 | 3D WebGL fails | full lesson completable in 2D |
| T-MEDIA-003 | media rights `needs_rights_review`/`unreviewed` | no public `has_3d` and no 3D listing |
| T-LMS-001 | observe → claim → evidence → revise | versioned artifact with rubric |
| T-LMS-002 | student ID tampering | cannot access other student work |
| T-RESEARCH-001 | raw CSV to published 1502 table | deterministic counts; denominators preserved |
| T-RESEARCH-002 | multi-select 4506 count | validation flags exact 3 per person condition |
| T-INQ-001 | backend unreachable on inquiry submission | error displayed, no fake reference |
| T-INQ-002 | empty authorized partner inbox | no seed inquiries appear |
| T-INQ-003 | unauthorized provider tries foreign ID | 403/404 and audit event |
| T-AI-001 | no verified source context | abstains without fabrication |
| T-AI-002 | forged citation UUID | rejected before display |
| T-AI-003 | nonpublished creator PII | no retrieval/disclosure |
| T-AUTH-001 | forged X-Forwarded-For | cannot bypass limiter if untrusted |
| T-REL-001 | migration failure | deployment stops automatically |
| T-CALL-001 | no language task content | CALL module not advertised as tested |
| T-A11Y-001 | no camera/device | entire source task completed |

---

