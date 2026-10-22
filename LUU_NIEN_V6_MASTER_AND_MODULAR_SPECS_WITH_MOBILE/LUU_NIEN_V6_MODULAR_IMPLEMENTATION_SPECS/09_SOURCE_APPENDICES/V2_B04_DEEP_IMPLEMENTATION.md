# V2 B4: source-derived engineering detail

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V2.B4`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## B4. API DESIGN SYSTEM — CÁC CONTRACT ĐỦ VIẾT CODE VÀ TEST

### B4.1 Endpoint naming và error envelope (TARGET)

Prefix `/api/v2`. Input snake_case đúng Python/Pydantic; frontend generated TS types từ OpenAPI, không duy trì nhiều bản interface viết tay thiếu đồng bộ. Timestamp RFC3339 offset-aware. `PATCH` yêu cầu optimistic concurrency `If-Match: "<etag>"` hoặc `expected_version`, trả 409/412 khi conflict. Danh sách dùng keyset cursor gồm sort key cố định và stable tiebreaker ID; không trộn offset và cursor trên cùng contract.

```json
{
  "error": {
    "code": "HERITAGE_SOURCE_REQUIRED",
    "message": "Cần nguồn tư liệu có thể truy xuất trước khi công bố nhận định.",
    "request_id": "req_example_nonsecret",
    "details": {"claim_id": "00000000-0000-4000-8000-000000000001", "missing": ["source_locator"]}
  }
}
```

- 400: JSON/field không hợp lệ về mặt cơ bản; 401: chưa đăng nhập; 403: scope không đủ; 404: không tồn tại **hoặc bị ẩn để tránh leak**, tùy threat model; 409: state/uniqueness conflict; 412: version mismatch; 422: business-validation failure; 429: throttled; 503: dependency unavailable.
- Mutating request có side effect cần `Idempotency-Key`, server lưu key + actor + route + normalized payload hash + result; khác payload cùng key trả 409.
- Không trả `user.email`, contact details hoặc raw student answer khi anonymous/public.

### B4.2 Public Heritage contracts (TARGET)

| Method / URI | Role | Query/body | Response success | Error cases phải test |
|---|---|---|---|---|
| `GET /api/v2/heritage/urns` | public | `language`, cursor, limit<=50 | {items,next_cursor,catalog_release} | invalid cursor, data review-only leak |
| `GET /api/v2/heritage/urns/{urn_code}` | public | `include=reliefs` optional | urn + published relief listing | unknown/withdrawn urn |
| `GET /api/v2/heritage/reliefs/{id}` | public | `locale`, `include=evidence,media` | dossier with claim status/source locators | private draft claim leak |
| `GET /api/v2/heritage/reliefs/{id}/sources` | public | `claim_id` optional | source citations and locators | unreviewed binding, forbidden attachment |
| `GET /api/v2/heritage/reliefs/{id}/media` | public | `purpose=explore|classroom`, `mode=2d|3d|ar` | rights-filtered renditions only | expired rights, blocked_nc, unknown grant |
| `GET /api/v2/heritage/search` | public | `q`, `lang`, `entity_types[]`, cursor | safe results, disambiguation | whitespace, accent variation, malicious chars |
| `GET /api/v2/heritage/taxonomy` | public | `version` | canonical taxonomy tree | unknown version |
| `GET /api/v2/heritage/map-features` | public | bbox, precision filter | GeoJSON with uncertainty disclosure | coordinate ranges, precise location leak |

`GET relief` response mẫu (chỉ minh họa schema, không phải hiện vật cụ thể đã kiểm chứng):

```json
{
  "id": "00000000-0000-4000-8000-000000000001",
  "canonical_code": "URN-EXAMPLE-RELIEF-01",
  "urn_code": "URN-EXAMPLE",
  "names": {"vi": "Tên đã duyệt", "en": "Reviewed label", "han": null},
  "publication_state": "published",
  "catalog_release": "release_2026_example",
  "visual_description": "Mô tả đúng phần quan sát được; không gộp suy luận.",
  "claims": [{
    "claim_id": "00000000-0000-4000-8000-000000000002",
    "version": 2,
    "text": "Nhận định có giới hạn và nguồn dẫn.",
    "epistemic_status": "editor_reviewed",
    "source_locators": [{"source_id": "00000000-0000-4000-8000-000000000003", "locator": "p. 12"}]
  }],
  "media": [{"asset_id": "00000000-0000-4000-8000-000000000004", "kind": "image", "public_url": "/safe/example.jpg", "rights_label": "Permission recorded"}],
  "capabilities": {"has_2d": true, "has_3d": false, "has_ar": false}
}
```

### B4.3 Editorial claim/source APIs (TARGET)

| Method / URI | Role | Nội dung | Rules |
|---|---|---|---|
| `POST /api/v2/editor/sources` | source_editor | bibliographic metadata + rights | validate locator scheme / duplicates |
| `POST /api/v2/editor/sources/{id}/locators` | source_editor | page/folio/timecode/scan quote | only if source exists and allowable access |
| `POST /api/v2/editor/claims` | history_editor | entity, statement, claim_type, origin | default `draft`; no author self-approval |
| `POST /api/v2/editor/claims/{id}/evidence` | history_editor | locator id + relation/support role | cannot bind stale/hidden source |
| `POST /api/v2/editor/claims/{id}/submit-review` | history_editor | expected_version | requires valid source(s) |
| `POST /api/v2/editor/claims/{id}/review` | expert_reviewer | approve/reject/request changes + rationale | reviewer != originating author; audit |
| `POST /api/v2/editor/catalog/releases` | publisher | list entity/claim/asset snapshots | two-person sign-off + deterministic hash |
| `POST /api/v2/editor/assets/{id}/withdraw` | rights_manager | reason, effective_at | immediately block serving + invalidate CDN |
| `GET /api/v2/editor/qa/coverage` | curator | urn, status, error classes | returns 9x18 coverage board |

**Editorial review payload:**

```json
{
  "expected_version": 3,
  "decision": "approved",
  "rationale": "Đã đối chiếu đúng trang và cách dịch.",
  "evidence_locator_ids": ["00000000-0000-4000-8000-000000000003"],
  "review_policy_version": "historian-review-v1"
}
```

Test cases: same author review -> 403; wrong expected version -> 412; absent locator -> 422; source document withdrawn -> 409; reviewer role missing -> 403; double submit same idempotency key -> same review without duplicate; audit log immutable.

### B4.4 ELLO authoring/learning APIs (TARGET)

| Method / URI | Auth | Request / response | Test focus |
|---|---|---|---|
| `POST /api/v2/learning/ellos` | teacher | `{entity_id, title, objective_codes}` -> draft | source item must be approved |
| `PATCH /api/v2/learning/ellos/{id}` | owner/editor | stage definitions with expected_version | concurrency, ownership |
| `POST /api/v2/learning/ellos/{id}/validate` | owner/editor | returns machine-checkable issues | rubric/source/fallback matrix |
| `POST /api/v2/learning/ellos/{id}/submit-review` | owner/editor | draft -> review | cannot skip validation |
| `POST /api/v2/learning/ellos/{id}/publish` | publisher | frozen `release_id`, content_hash | audit, two-person approval |
| `POST /api/v2/classes/{id}/assignments` | teacher | `{lesson_release_id, due_at, audience}` | teacher owns classroom |
| `GET /api/v2/assignments/{id}` | student | stage descriptions, allowed assets, permissions | no rubrics answer key leak |
| `POST /api/v2/assignments/{id}/attempts` | student | starts attempt + idempotency | unique active draft per configured policy |
| `PATCH /api/v2/attempts/{id}/draft` | student | answer draft + version | own attempt only |
| `POST /api/v2/attempts/{id}/submit` | student | answers/evidence ids + key | source references valid, atomic |
| `POST /api/v2/attempts/{id}/feedback` | teacher/rater | rubric scores + reasoning | blinded rater workflow if study |
| `POST /api/v2/attempts/{id}/revision` | student | revised response referencing prior version | append-only; no overwrite original |
| `GET /api/v2/classes/{id}/learning-analytics` | teacher | aggregate and authorized student progress | per-class scope; no cross-school leak |

**ELLO validation response example:**

```json
{
  "valid": false,
  "ello_version": 4,
  "issues": [
    {"code": "MISSING_SOURCE_LOCATOR", "severity": "blocker", "path": "stages[2].source_refs"},
    {"code": "MISSING_2D_FALLBACK", "severity": "blocker", "path": "representations[1]"},
    {"code": "RUBRIC_UNANCHORED_CRITERION", "severity": "warning", "path": "rubric.criteria[3]"}
  ]
}
```

**Student submission example:**

```json
{
  "lesson_release_id": "00000000-0000-4000-8000-000000000010",
  "attempt_version": 2,
  "observations": [{"item_key": "surface_detail_1", "text": "Quan sát mô tả, chưa diễn giải."}],
  "provisional_claim": "Giả thuyết của học sinh.",
  "evidence_uses": [{"source_locator_id": "00000000-0000-4000-8000-000000000003", "supports_which_sentence": "Câu số 2"}],
  "historical_explanation": "Đoạn giải thích phân biệt quan sát và nguồn.",
  "uncertainty_statement": "Điểm chưa thể kết luận từ nguồn hiện tại."
}
```

DoD: backend lưu snapshot bài làm và exact release; reject missing required evidence with actionable error; không kiểm correctness tự luận bằng exact string matching; người chấm có thể xem source cited và rubric dimensions.

### B4.5 AI tutor contract (TARGET)

`POST /api/v2/ai/heritage/ask` request fields: `question` (1..2000 ký tự), `locale`, `entity_ids` allowlisted, `lesson_release_id?`, `mode=learning_assistant|public_explore`, `consent_context`, `client_request_id`. Response: `answer`, `status=answered|insufficient_evidence|refused`, `citations[{claim_id,claim_version,source_id,locator,confidence}]`, `uncertainties[]`, `retrieval_release`, `model_id` (internally log or conditionally shown), `safety_notices[]`, `evaluation_tags[]`. No streaming of final-answer text before citation verifier passes; if streaming, buffer/verify per sentence or draft then stream validated chunks.

**AI failure examples:** sources all `unreviewed` -> abstain; prompt injection inside excerpt -> ignore instruction; contradictory sources -> show disagreement and attribution; revoked source -> no citation; invented publication year -> assertion flagged; claim in wrong scope -> abstain; LLM API timeout -> deterministic approved excerpt or 503 (clearly labeled), never fabricate.

### B4.6 Media authorization response (TARGET)

`GET /api/v2/media/{id}/access?purpose=classroom_education` returns `{allowed, reason_code, rendition, rights_disclosure, valid_until}` only if caller authorized, or 403/404 fail-closed; separate 2D thumbnail from 3D high-resolution download rights. Service verifies purpose against signed grant; direct origin protected or remote embed governed by documented rights. Cache TTL không vượt grant expiry/withdrawal horizon.

### B4.7 Research export contract (TARGET — private)

`POST /internal/research/studies/{id}/imports` service-to-service or research_admin with signed manifest; import is asynchronous. `GET /internal/research/imports/{job_id}` returns validated counts, parse warnings, schema drift and quarantined records. `POST /internal/research/studies/{id}/analysis-releases` creates immutable `analysis_snapshot`. `GET /internal/research/studies/{id}/aggregates/{version}` returns only aggregate results under privacy threshold; never permit a public filter chain reconstructing an individual.

### B4.8 Inquiry production repair contract

Preserve existing `POST /api/v1/rbpc/inquiries` while changing **frontend error handling** to fail closed. `202` chỉ khi DB commit thành công. Add optional `server_receipt_id` for audit, `status_token` chỉ cấp từ server. Status lookup yêu cầu opaque token, rate-limited and no sensitive contact returned. Retry same idempotency key must return same server receipt; changing payload returns 409; backend down => visible error, không tạo synthetic ref. Partner status transitions scope to provider; partner không được đọc inquiry của partner khác.

---

