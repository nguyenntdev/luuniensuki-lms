# V5.4 — TARGET_ARCHITECTURE

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.4`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.4 — TARGET ARCHITECTURE VÀ HỢP ĐỒNG TRIỂN KHAI

### 4.1. Kiến trúc dùng chính stack hiện có (không rewrite vô cớ)

```text
Web Next.js / Flutter Mobile / Teacher Admin / Partner Portal
                  │ HTTPS, auth, consent
                  ▼
        Nginx + Rust Axum Gateway
        ├─ native endpoints existing
        └─ routes Python-only (explicit route registry)
                   ▼
         FastAPI domain services
      ┌───────┬──────────┬─────────┬────────┐
      │source │ learning │ market  │ AI jobs│
      └──┬────┴────┬─────┴────┬────┴───┬────┘
         │         │          │        │
      PostgreSQL  Object Store       Redis/Queue*
      audit + DB  versioned rights   global limit*
         │            │            │
         └───── Observability / backup / CI ─────┘
```

`*` Thành phần Redis/queue là lựa chọn đích, phải kiểm tra services đang cài; có thể bắt đầu bằng PostgreSQL `SKIP LOCKED`/lease để giảm phụ thuộc, nhưng cần multi-instance-safe semaphore và restart recovery. Không hardcode nhà cung cấp AI. Route Rust hoặc proxy được xác nhận qua registry; client chỉ gọi API public contract, không phụ thuộc chi tiết backend chạy Rust/Python.

### 4.2. Bounded contexts bắt buộc

1. `IDENTITY`: user, role, school, class, partner, staff, MFA, consent.
2. `HERITAGE`: canonical urn/relief/monument, translations, provenance, categories, search.
3. `EVIDENCE`: source/version/edition/page/snippet/claim/conflict/rights/reviewer.
4. `MEDIA`: image/video/audio/glTF/AR, media attribution, source rights, manifest.
5. `LEARNING`: source-linked lessons, rubric, enrollment, attempts, feedback, gradebook.
6. `AI_RESEARCH`: 12 historical phases x 10 jobs, result envelopes, review gates.
7. `AI_TUTOR`: verified retrieval, citation-backed answer, hint-first, evaluation.
8. `EXPERIENCES`: creator consent, listings, inventory, inquiry status, confirmation.
9. `COMMERCE`: negotiated commissions, settlement evidence, refunds/disputes only after legal/payment readiness.
10. `ANALYTICS`: strictly separated product telemetry, education research consent, business conversion events.
11. `OPS`: releases, feature flags, audit, queues, status, health, backups.

**Context principle:** `source_id`, `heritage_object_id`, `partner_id`, `school_id` are stable and never reused. No cross-tenant joins outside privileged reviewed jobs. Every public item has `content_scope`, `published_revision`, `rights_status`, `review_status`.

### 4.3. Cross-cutting engineering requirements

- REST/JSON consistent `request_id`, typed error envelope `{error:{code,message,request_id,details?}}` with no PII; OpenAPI contract-generated clients; no silent fallback.
- Auth: server validated permissions, partner scope by verified `provider_id` membership (never by `?provider=`), classroom/guardian separation for minors.
- Content editor: draft/review/approved/published/retired, immutable version and signed audit trace; AI never signs off on human review.
- DB: Alembic additive migration first, DB preflight, backward-compatible deploy, backfill, new read path, finally old column retirement (expand/contract).
- Media: upload malware/size/type checks, signed private URLs, public CDN only approved rights, offline 2D fallback, alt and transcript.
- AI: structured output schema, tool allowlists, provenance, bounded context, global provider cost governor, replay-safe workers, human gates.
- Data analytics: server events for commercial conversion; survey 1.502 is respondent self-report only, not baseline for learning gains.

### 4.4. Sample error and mutation semantics

```json
{
  "error": {
    "code": "INQUIRY_UNAVAILABLE",
    "message": "Không thể ghi nhận yêu cầu. Vui lòng thử lại.",
    "request_id": "<server-generated>",
    "details": {"retryable": true}
  }
}
```

`POST /api/v1/rbpc/inquiries`: server returns `202` only when inquiry is committed or durably accepted into outbox (with explicit status), not when browser generated local reference. Partner PATCH uses transactional compare-and-swap + transition permission + audit + idempotency. Client may optimistically render `updating…` but not `confirmed` before commit.

### 4.5. Architectural decision records

| ADR | Decision | Alternative | Reason | Revisit trigger |
|---|---|---|---|---|
| ADR-001 | reuse modular FastAPI + Rust gateway | full rewrite | preserve proven routers; small-team feasibility | verified throughput bottleneck |
| ADR-002 | PostgreSQL source of truth for grades/inquiries | localStorage | multi-user integrity & audit | never |
| ADR-003 | verified source claim graph | prose-only AI | fact-check and citations | never |
| ADR-004 | inquiry-first not fake checkout | instant payment | no provider inventory/payment contract verified | legal + payments pilot passed |
| ADR-005 | AI research write draft only | AI publish autonomously | protect heritage accuracy and creator rights | independent approval governance |
| ADR-006 | two product offers on one corpus | duplicated school/tourist DB | coherent provenance, reduced upkeep | load/cost observed |
| ADR-007 | functional slices behind flags | big-bang release | reduces migration & operational risk | never |

