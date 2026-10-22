# V5.5 — DATA_API_EVENT_CONTRACTS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.5`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.5 — HỢP ĐỒNG DỮ LIỆU ĐÍCH (DB / API / EVENTS)

### 5.1. CATALOG / EVIDENCE

**Các bảng mới đề xuất sau khi so sánh với schema thực** (KHÔNG thêm trùng các model đã có `backend/history_models.py`, `backend/models_rbpc.py`):

| Logical entity | Cột tối thiểu | Invariant |
|---|---|---|
| `heritage_object` | uuid, canonical_slug, object_type, urn_id, status, modified_at | unique canonical slug per scope |
| `heritage_object_name` | object_id, locale, name, original_script, transliteration, review_state | Hán–Nôm separate human verification |
| `historical_source` | id, title, author_org, edition, published_year, rights_status, stable_url, checksum | source ownership/edition recorded |
| `source_passage` | id, source_id, page_start/end, anchor, excerpt, language, checksum, rights_policy | locator + excerpt within licensed length |
| `historical_claim` | id, object_id, statement, language, epistemic_status, review_status, revision | no published unsupported claim |
| `claim_evidence` | claim_id, passage_id, relation, confidence_class, rationale | supporting/conflicting relation explicit |
| `media_asset` | id, object_id, type, uri, checksum, size, width/height, attribution, rights_status, verify_state | signed/public only after license gate |
| `ai_draft` | id, object_id, version, source_set_hash, model_id, prompt_hash, body, status | AI text immutable per version |
| `editorial_review` | review_id, draft_id, editor_id, decision, rubric_version, reason, signed_at | editor != AI actor |
| `published_article` | object_id, locale, version, body, evidence_manifest_hash, published_at | immutable signed revision |
| `content_change_event` | record, before/after hash, actor, scope, request_id, created_at | append-only |

Do not store unlicensed full-text books in the source DB. Keep excerpts minimal for verifiability; store stable bibliographic locator, owner contact, reuse rationale, public/private release status. Specific schema types and names are illustrative until migration review.

### 5.2. LEARNING / SCHOOL

| Logical entity | Fields | Invariant |
|---|---|---|
| `school` | id, name, district, verification_state | school data independently verified |
| `classroom` | id, school_id, teacher_id, grade_band, term, access_code_hash | one teacher authorized per role |
| `enrollment` | class_id, student_id, joined_at, state | no cross-school leakage |
| `learning_object` | object_id, objective, source_set, representation_mode, task, feedback_rule, rubric_version | 6-step ELLO complete |
| `lesson_assignment` | learning_object_id, class_id, due_at, options, state | version locked per assignment |
| `student_submission` | id, assignment_id, student_id, content, submitted_at, version | idempotent, server-owned |
| `grade` | submission_id, reviewer_id, rubric_version, rubric_scores, feedback, graded_at | immutable grade revisions, teacher scope |
| `consent_record` | subject_id, purpose, basis, guardian_relation_if_applicable, version, withdrawn_at | withdraw effects propagated |

Student real names should not be preseeded into localStorage; guest demos use visibly synthetic anonymized labels with no implied actual school/teacher.

### 5.3. EXPERIENCES / PARTNER / COMMERCE

| Logical entity | Fields | Invariant |
|---|---|---|
| `provider_membership` | user_id, provider_id, role, verified_at | read access scoped to membership |
| `creator_consent` | creator_id, rights_scope, approved_media, effective/expires, revoked_at | revocation hides media/listings quickly |
| `experience_listing` | provider_id, price_display, inclusions, safety_age, locale, availability_mode, review | visible only with consent + rights |
| `slot_inventory` | listing_id, start/end, capacity, reserved, version | one canonical inventory if enabled |
| `inquiry` | id, ref, provider_id, customer_contact_enc, request, state, idempotency_hash | unique ref, no seed production |
| `inquiry_event` | id, inquiry_id, from_state, to_state, actor, at, reason | append-only |
| `completion_evidence` | inquiry_id, partner_attest, customer_confirmation, amount_actual, currency, verified_at | not inferred from `confirmed` |
| `payout/commission` | partner_id, inquiry_id, agreed_fee, payable, paid_at, evidence | only after commercial/legal approval |
| `support_case` | ticket_id, inquiry_id, type, SLA, owner, resolution | user protection & dispute trail |
| `conversion_event` | event_type, anonymous_device/session, attribution, consent, timestamp | business KPIs only from observed events |

*Payment processing is OPTIONAL at pilot start.* Never assume VND card charging/refunds/tax flows are live because revenue spreadsheet exists. Require provider contracts, consumer-protection review and payment gateway before enabling.

### 5.4. AI JOBS / 10 CONCURRENT SUBAGENTS

Key entities: `research_run`, `phase_run`, `agent_assignment`, `agent_attempt`, `source_candidate`, `evidence_check`, `human_review`, `publication_candidate`, `cost_usage`. Global unique indexes on `(run_id, phase_id, agent_slot)` and `(job_id, idempotency_key)` where applicable. Worker lease includes `owner_id`, `lease_expires_at`, `attempt_count`; status: `QUEUED → LEASED → RUNNING → SUCCEEDED | FAILED | CANCELLED | EXPIRED`, with `CAPACITY_BLOCKED` distinguishable from system failure. Finish barrier requires 10 terminal envelopes, mandatory safety/copyright reviewers passed, budget ledger reconciled; never treat one model call with 10 role prompts as 10 concurrent jobs.

### 5.5. API contract catalogue (new endpoints are TARGET until reviewed)

| Endpoint | Role | Behavior / negative contract |
|---|---|---|
| `GET /api/v1/heritage/objects?scope=&cursor=` | public | cursor paging, only published + rights-safe; empty `[]` valid |
| `GET /api/v1/heritage/objects/{slug}` | public | canonical 404 vs embargo 404, include source badges |
| `GET /api/v1/heritage/objects/{id}/evidence` | public | page locators and licensed excerpts, no private scans |
| `GET /api/v1/media/{id}/manifest` | public | rights, model capability, 2D fallback, checksum |
| `POST /api/v1/classes` | teacher | school-scoped role, CSRF protection |
| `POST /api/v1/classes/{id}/assignments` | teacher | version locked task/rubric |
| `POST /api/v1/assignments/{id}/submissions` | student | auth/class membership, idempotency |
| `POST /api/v1/submissions/{id}/grade` | teacher | ownership/rubric validation/audit |
| `GET /api/v1/classes/{id}/gradebook` | teacher/admin | school boundary enforced, export permission |
| `POST /api/v1/rbpc/inquiries` | public | durable 202, 409 for duplicate/conflict, 429 rate limit |
| `PATCH /api/v1/rbpc/partner/inquiries/{id}` | partner | state machine, member scoping, audit |
| `POST /api/v1/rbpc/inquiries/{id}/complete` | partner+verification | no completed without experience evidence |
| `GET /api/v1/rbpc/partner/analytics` | partner | only verified provider, no sample dashboard metrics |
| `POST /api/v1/admin/research-factory/runs` | research-admin | audited, quota, idempotent |
| `POST /api/v1/admin/editorial/{id}/approve` | human-editor | real signature, cannot auto-approve |
| `POST /api/v1/support/cases` | authorized visitor | minimal PII, attachments sanitized |
| `POST /api/v1/analytics/events` | consented client | anti-bot, dedup, privacy-safe |

### 5.6. Error taxonomy

`INVALID_INPUT` 422; `UNAUTHENTICATED` 401; `FORBIDDEN_SCOPE` 403; `NOT_FOUND` 404; `CONSENT_REVOKED` 410/404 based privacy; `VERSION_CONFLICT` 409; `RATE_LIMITED` 429; `SOURCE_UNVERIFIED` 422; `NO_LICENSE` 403; `PROVIDER_UNAVAILABLE` 503; `RESEARCH_CAPACITY_BLOCKED` 503; `NOT_IMPLEMENTED` 501 only in staging/internal; `INTERNAL_ERROR` 500. Every mutation fails closed, logs redacted request_id and no PII.

### 5.7. Event dictionary v1

`heritage_view`, `source_open`, `claim_compare`, `model3d_open`, `ar_start`, `lesson_start`, `lesson_submit`, `teacher_feedback`, `creator_profile_view`, `experience_detail_view`, `inquiry_started`, `inquiry_submitted_server`, `partner_contacted`, `inquiry_confirmed`, `experience_completed_verified`, `support_case_opened`, `consent_withdrawn`, `ai_answer_with_citation`, `ai_abstained`, `editorial_approved`. **Never** send raw student text/contact to third-party analytics. Each event requires schema_version, event_id, pseudonymous identifier where consented, timestamp, scope, server trust flag, idempotency.

