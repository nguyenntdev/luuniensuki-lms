# LƯU NIÊN — RBPC 2026: API CONTRACTS SPECIFICATION

**Document Version:** 1.0.0 | **Date:** 18 October 2026 | **Gate:** G1 Candidate  
**Content Scope:** `RBPC_HUE` (Isolated from legacy `CUU_DINH`)  
**Base Commit SHA:** `e19aebc0e7f66f7863659fd658c204739e199687` | **Branch:** `feat/rbpc-cultural-bridge-2026`  
**Reference Pydantic Modules:** `backend/apischemas/heritage.py`, `backend/apischemas/rbpc.py`  

---

## 1. Architectural Overview & Request Routing

Per **ADR 02** (*API Namespacing & Route Dispatching*), all new endpoints for the LƯU NIÊN Living Heritage Platform are strictly additive and partitioned into two root namespaces:

1. `/api/v1/heritage/*` — Huế-wide heritage knowledge catalogue: places, relationships, bibliographic source evidence, rights-cleared media assets, 3D Sketchfab viewer embeds, and diacritic-tolerant search.
2. `/api/v1/rbpc/*` — Commercial MVP vertical slice: curated cultural stories, source-grounded AI Cultural Bridge, consented artisan profiles, cultural experience offerings, availability inquiries, and partner operations.

```text
Browser Client
   │ (HTTPS :443)
   ▼
Nginx Reverse Proxy
   │
   ├── /_next/*, /heritage/*, /explore, /create ────────► Next.js Frontend (:3000)
   │
   └── /api/v1/* ────────────────────────────────────────► Rust Gateway (:8001)
                                                               │
                                                               ├── Native Axum Handlers (Auth, Gamification, Classrooms)
                                                               └── Fallback (.fallback_to_python) ──► Python FastAPI (:8000)
                                                                                                        ├── /api/v1/heritage/*
                                                                                                        └── /api/v1/rbpc/*
```

### Strangler Fig Routing Policy
- Unmatched routes on the Rust Gateway (:8001) automatically proxy to FastAPI (:8000) via `gateway::fallback_to_python`.
- Route inventory is maintained via `scripts/dev/generate_route_inventory.py`.
- OpenAPI snapshots are pinned byte-for-byte in `tests/backend/fixtures/openapi_snapshot.json` and guarded by `tests/backend/test_openapi_snapshot.py`.

---

## 2. Global Error Envelope Standard

All API errors across `/api/v1/heritage/*` and `/api/v1/rbpc/*` strictly adhere to the repository standard envelope verified by `tests/backend/test_validation_error_envelope.py`:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable explanation in the requested locale",
    "details": {}
  }
}
```

### Standard Error Codes

| HTTP Status | Error Code (`error.code`) | Description & Typical Cause |
|---|---|---|
| `400 Bad Request` | `INVALID_INPUT` | Malformed parameters, invalid dates, or invalid query options. |
| `400 Bad Request` | `RBPC_CONSENT_REQUIRED` | Submitted inquiry without `consent.accepted: true`. |
| `400 Bad Request` | `RBPC_DATE_PAST` | `preferred_date` is in the past. |
| `401 Unauthorized` | `UNAUTHENTICATED` | Missing, expired, or invalid JWT access token in httpOnly cookie or Bearer header. |
| `403 Forbidden` | `FORBIDDEN_SCOPE` | Insufficient role or attempt to access another partner's private inquiries. |
| `403 Forbidden` | `RBPC_RIGHTS_RESTRICTED` | Attempted access to a resource whose copyright or artisan consent is unapproved or revoked. |
| `404 Not Found` | `HERITAGE_PLACE_NOT_FOUND` | Heritage place slug does not exist or is not in `published` status for public access. |
| `404 Not Found` | `RBPC_STORY_NOT_FOUND` | Story slug does not exist or is unreviewed/draft. |
| `404 Not Found` | `RBPC_INQUIRY_NOT_FOUND` | Provided status token or reference code does not match any record. |
| `409 Conflict` | `RBPC_IDEMPOTENCY_CONFLICT` | Replay of inquiry with same key but mismatched payload content. |
| `422 Unprocessable` | `VALIDATION_ERROR` | Pydantic v2 schema validation failure on request payload structure. |
| `429 Too Many Requests` | `RATE_LIMIT_EXCEEDED` | Request rate exceeded allowed burst or sliding window quota. |
| `502 Bad Gateway` | `AI_SERVICE_UNAVAILABLE` | External LLM upstream unavailable; triggers fail-closed curated fallback. |

---

## 3. Authentication & Authorization Matrix

The platform operates under four distinct caller authorization levels:

```text
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│      Guest      │      │  Standard User  │      │     Partner     │      │   Staff/Admin   │
│   (Anonymous)   │      │ (Student/Member)│      │    (Artisan)    │      │    (Curator)    │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │                        │
         ▼                        ▼                        ▼                        ▼
 ┌───────────────┐        ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
 │ Public Reads  │        │ Authenticated │        │ Provider      │        │ Full Editorial│
 │ AI Chat       │        │ History LMS   │        │ Inquiries     │        │ Rights Review │
 │ Inquiry Submit│        │ Saved Quests  │        │ Availability  │        │ Publishing    │
 │ Status Check  │        │ XP / Badges   │        │ Status Update │        │ Audit Trail   │
 └───────────────┘        └───────────────┘        └───────────────┘        └───────────────┘
```

### Authorization Rules Summary

1. **Guest / Anonymous:**
   - Identity: No token required.
   - Allowed: Public catalogue browsing (`editorial_status=published`), story reading, Cultural Bridge AI queries, booking inquiry creation, inquiry status check via high-entropy `status_token`.
   - Security Invariant: Public responses never expose unpublished drafts, revoked media, internal contact details, or PII.

2. **Standard User (`role: student`, `role: user`):**
   - Identity: Valid JWT in httpOnly cookie `luuniensuki_access` or `Authorization: Bearer <token>`.
   - Allowed: Guest capabilities plus gamified progress tracking, quest completion, and saved heritage places.

3. **Partner / Experience Provider (`role: partner` or assigned `provider_id`):**
   - Identity: Valid JWT containing partner identity claims.
   - Allowed: Access to own provider inbox (`GET /api/v1/rbpc/partner/inquiries`), state transitions on own inquiries (`PATCH /api/v1/rbpc/partner/inquiries/{id}`).
   - Security Invariant: Server-side provider scoping blocks horizontal privilege escalation. Accessing an inquiry belonging to another partner returns `404 Not Found` (anti-enumeration).

4. **Staff / Admin (`role: staff`, `role: admin`):**
   - Identity: Valid JWT with elevated roles.
   - Allowed: Editorial CRUD (`/api/v1/admin/heritage/*`), 3D Sketchfab copyright reviews, content publishing, and audit inspection.

---

## 4. Rate Limiting Limits & Abuse Protection

Rate limits are enforced at the gateway and application middleware levels. Rate limit headers are returned on all requests:
- `X-RateLimit-Limit`: Maximum requests permitted in window.
- `X-RateLimit-Remaining`: Requests remaining in current window.
- `X-RateLimit-Reset`: UTC epoch timestamp when window resets.
- `Retry-After`: Seconds to wait before retrying (on `429 Too Many Requests`).

| Endpoint Pattern | Method | Auth Level | Rate Limit (Window) | Enforcement Purpose |
|---|---|---|---|---|
| `/api/v1/heritage/places*` | `GET` | Guest | 120 req / 1 min / IP | Prevent catalogue scraping. |
| `/api/v1/heritage/search` | `GET` | Guest | 60 req / 1 min / IP | Protect full-text search index. |
| `/api/v1/rbpc/stories*` | `GET` | Guest | 120 req / 1 min / IP | Standard web browsing. |
| `/api/v1/rbpc/cultural-bridge` | `POST` | Guest | 10 req / 1 min / IP<br>30 req / 1 hr / session | Prevent LLM token depletion; enforce fair use. |
| `/api/v1/rbpc/inquiries` | `POST` | Guest | 5 req / 1 min / IP<br>15 req / 1 day / IP | Prevent spam inquiries to artisans; require idempotency. |
| `/api/v1/rbpc/inquiries/status/*` | `GET` | Guest | 30 req / 1 min / IP | Polling rate ceiling for status updates. |
| `/api/v1/rbpc/partner/*` | `ALL` | Partner | 60 req / 1 min / user | Operational partner dashboard activity. |
| `/api/v1/admin/heritage/*` | `ALL` | Staff/Admin | 120 req / 1 min / user | Administrative editorial actions. |

---

## 5. Detailed OpenAPI Specification Reference

### Group A: Heritage Knowledge Catalogue (`/api/v1/heritage/*`)

#### 1. `GET /api/v1/heritage/places`
**Description:** Browse and filter catalogued heritage places with cursor-based pagination. Only places with `editorial_status=published` and `content_scope=RBPC_HUE` are returned to public callers.

- **Auth Required:** None (Public)
- **Rate Limit:** 120 req / min
- **Query Parameters:**
  - `category` (optional, string): Filter by category (e.g. `imperial_architecture`, `royal_tomb`, `craft_living_culture`, `music_performance`, `religious_ritual`, `museum_documentary`).
  - `entity_type` (optional, string): Filter by entity type (`site`, `monument`, `building`, `object`, `landscape`, `intangible`, `community`, `collection`).
  - `has_3d` (optional, boolean): If `true`, returns only places with approved 3D models.
  - `cursor` (optional, string): Opaque pagination cursor.
  - `limit` (optional, integer, default: 20, min: 1, max: 100): Page size.
  - `q` (optional, string): Diacritic-tolerant keyword search string.

- **Response:** `200 OK` (`application/json`)
```json
{
  "items": [
    {
      "id": "7b8e1a23-4567-489a-bcde-f0123456789a",
      "slug": "lang-tu-duc",
      "name_vi": "Lăng Tự Đức",
      "name_en": "Tomb of Tu Duc",
      "entity_type": "site",
      "heritage_category": "royal_tomb",
      "parent_id": null,
      "official_designation": "UNESCO World Heritage Component",
      "official_reference_id": "678-007",
      "period_label": "Triều Tự Đức (1864-1867)",
      "historical_state": "standing",
      "location_lat": 16.4328,
      "location_lon": 107.5656,
      "geo_precision": "exact_gps",
      "current_access_status": "open",
      "visitor_summary_vi": "Quần thể lăng tẩm mang phong cách thơ mộng, hòa hợp tuyệt đối với thiên nhiên xứ Huế.",
      "visitor_summary_en": "An imperial tomb complex noted for its poetic harmony with natural water and pine landscapes.",
      "editorial_status": "published",
      "content_scope": "RBPC_HUE",
      "has_3d": true,
      "thumbnail_url": "/assets/heritage/lang-tu-duc-thumb.webp",
      "published_at": "2026-10-18T00:00:00Z",
      "created_at": "2026-10-17T10:00:00Z",
      "updated_at": "2026-10-18T00:00:00Z"
    }
  ],
  "next_cursor": "eyJpZCI6ICI3YjhlMWEyMy...IsICJjcmVhdGVkX2F0IjogMTcyOTI0ODAwMH0=",
  "has_more": true,
  "total_count": 14
}
```

---

#### 2. `GET /api/v1/heritage/places/{slug}`
**Description:** Retrieve the summary profile card of a specific published heritage place by slug.

- **Auth Required:** None (Public)
- **Path Parameters:** `slug` (string, required)
- **Response:** `200 OK` (Schema: `HeritagePlaceOut`)
- **Error Codes:** `404 HERITAGE_PLACE_NOT_FOUND`

---

#### 3. `GET /api/v1/heritage/places/{slug}/detail`
**Description:** Retrieve the deep composite representation of a heritage place including parent/child relationships, connected entities, verified bibliographic source citations, rights-cleared media assets, and commercial engagement CTAs.

- **Auth Required:** None (Public)
- **Path Parameters:** `slug` (string, required)
- **Response:** `200 OK` (`application/json`)
```json
{
  "id": "7b8e1a23-4567-489a-bcde-f0123456789a",
  "slug": "lang-tu-duc",
  "name_vi": "Lăng Tự Đức",
  "name_en": "Tomb of Tu Duc",
  "entity_type": "site",
  "heritage_category": "royal_tomb",
  "parent_id": null,
  "official_designation": "UNESCO World Heritage Component",
  "official_reference_id": "678-007",
  "period_label": "Triều Tự Đức (1864-1867)",
  "historical_state": "standing",
  "location_lat": 16.4328,
  "location_lon": 107.5656,
  "geo_precision": "exact_gps",
  "current_access_status": "open",
  "access_notes": "Mở cửa hàng ngày từ 07:00 đến 17:30. Vé tham quan theo quy định của Trung tâm BTDTCĐ Huế.",
  "visitor_summary_vi": "Quần thể lăng tẩm mang phong cách thơ mộng, hòa hợp tuyệt đối với thiên nhiên xứ Huế.",
  "visitor_summary_en": "An imperial tomb complex noted for its poetic harmony with natural water and pine landscapes.",
  "historical_summary_vi": "Khiêm Lăng được Hoàng đế Tự Đức tự quy hoạch và khởi công năm 1864, hoàn thành năm 1867 làm nơi nghỉ ngơi và lăng tẩm vĩnh hằng.",
  "historical_summary_en": "Khiem Lang was personally planned by Emperor Tu Duc in 1864 and completed in 1867 as both a summer retreat and permanent mausoleum.",
  "editorial_status": "published",
  "content_scope": "RBPC_HUE",
  "has_3d": true,
  "thumbnail_url": "/assets/heritage/lang-tu-duc-thumb.webp",
  "published_at": "2026-10-18T00:00:00Z",
  "created_at": "2026-10-17T10:00:00Z",
  "updated_at": "2026-10-18T00:00:00Z",
  "child_places": [],
  "relations": [
    {
      "id": "c1a2b3c4-d5e6-47a8-9b0c-1d2e3f4a5b6c",
      "from_place_id": "7b8e1a23-4567-489a-bcde-f0123456789a",
      "to_place_id": "8c9f2b34-5678-49ab-cdef-0123456789ab",
      "from_place_slug": "lang-tu-duc",
      "from_place_name": "Lăng Tự Đức",
      "to_place_slug": "kinh-thanh-hue",
      "to_place_name": "Kinh thành Huế",
      "relationship_type": "contained_in",
      "claim_id": null,
      "review_state": "verified",
      "created_at": "2026-10-17T12:00:00Z"
    }
  ],
  "sources": [
    {
      "id": "e2f3a4b5-c6d7-48e9-af01-2b3c4d5e6f7a",
      "place_id": "7b8e1a23-4567-489a-bcde-f0123456789a",
      "source_url": "https://whc.unesco.org/en/list/678",
      "source_title": "Complex of Hué Monuments - UNESCO World Heritage Centre",
      "source_author": "UNESCO World Heritage Committee",
      "publisher": "UNESCO",
      "publication_year": 1993,
      "cited_section": "Component 678-007",
      "cited_page": "Item 678-007",
      "retrieved_at": "2026-10-17T08:00:00Z",
      "statement": "Lăng Tự Đức (Khiêm Lăng) được chính thức ghi danh trong Quần thể Di tích Cố đô Huế theo tiêu chuẩn (iv).",
      "interpretation_note": "Tài liệu xác thực phạm vi bảo vệ di sản theo danh mục UNESCO.",
      "evidence_status": "verified",
      "reuse_rights": "public_domain",
      "content_scope": "RBPC_HUE"
    }
  ],
  "media": [
    {
      "id": "f3a4b5c6-d7e8-49fa-b012-3c4d5e6f7a8b",
      "place_id": "7b8e1a23-4567-489a-bcde-f0123456789a",
      "media_type": "sketchfab_embed",
      "source_platform": "sketchfab",
      "original_url": "https://sketchfab.com/3d-models/tomb-of-tu-duc-77728a86ad1d4964824b63844d50bfe7",
      "title": "Tomb of Tu Duc",
      "creator_name": "matousekfoto",
      "creator_url": "https://sketchfab.com/matousekfoto",
      "model_uid": "77728a86ad1d4964824b63844d50bfe7",
      "license_label": "CC BY 4.0",
      "license_url": "https://creativecommons.org/licenses/by/4.0/",
      "noai": false,
      "commercial_use_status": "permitted",
      "embed_permission_status": "permitted",
      "accuracy_grade": "measured_photogrammetry",
      "provenance_notes": "Mô hình đo đạc quang trắc ảnh dựa trên bộ dữ liệu CyArk / Open Heritage 3D.",
      "attribution_text": "Model by matousekfoto via Sketchfab, licensed under CC BY 4.0. Data courtesy of CyArk.",
      "content_status": "cleared_for_this_use",
      "embed_url": "https://sketchfab.com/models/77728a86ad1d4964824b63844d50bfe7/embed",
      "content_scope": "RBPC_HUE",
      "created_at": "2026-10-17T14:00:00Z"
    }
  ],
  "engagement": {
    "cta_kind": "story_journey",
    "target_slug": "tieng-chuong-khiem-cung",
    "title_vi": "Khám phá câu chuyện: Tiếng chuông Khiêm Cung",
    "title_en": "Discover Story: The Bells of Khiem Cung",
    "notice": "Hành trình trải nghiệm văn hóa kết nối di sản kiến trúc với làng nghề chế tác truyền thống."
  }
}
```

---

#### 4. `GET /api/v1/heritage/places/{slug}/3d`
**Description:** Retrieve rights-cleared 3D Sketchfab models for a heritage place. Models with `accuracy_grade=rejected_accuracy` (e.g. SF-020) or restricted licenses (`CC BY-NC-SA` commercial block) are strictly omitted.

- **Auth Required:** None (Public)
- **Path Parameters:** `slug` (string, required)
- **Response:** `200 OK` (Array of `HeritageMediaAssetOut`)
- **Security Invariant:** If no verified, rights-cleared 3D model exists, returns empty array `[]` so the frontend gracefully displays the licensed 2D photograph fallback.

---

#### 5. `GET /api/v1/heritage/search`
**Description:** Search heritage places across Vietnamese names, English names, official UNESCO IDs, and historical summaries with accent-tolerant matching.

- **Auth Required:** None (Public)
- **Query Parameters:**
  - `q` (string, required, min_length: 2): Search keyword (e.g. `Tu Duc`, `Ngọ Môn`, `Thanh Tien`).
  - `scope` (string, default: `RBPC_HUE`): Scope constraint.
- **Response:** `200 OK` (Schema: `HeritageSearchOut`)

---

### Group B: RBPC Commercial MVP & Cultural Bridge (`/api/v1/rbpc/*`)

#### 6. `GET /api/v1/rbpc/config`
**Description:** Returns platform runtime configuration, active feature flags, supported locales, and consent document versions. Zero secrets or API keys are exposed.

- **Auth Required:** None (Public)
- **Response:** `200 OK` (`application/json`)
```json
{
  "enabled": true,
  "ai_enabled": true,
  "inquiry_enabled": true,
  "supported_locales": ["vi", "en"],
  "default_locale": "vi",
  "demo_mode": true,
  "version": "1.0.0",
  "privacy_notice_url": "/privacy",
  "terms_url": "/terms",
  "consent_version": "rbpc-inquiry-v1"
}
```

---

#### 7. `GET /api/v1/rbpc/stories`
**Description:** Retrieve published curated cultural stories. Unreviewed or draft stories are omitted.

- **Auth Required:** None (Public)
- **Query Parameters:**
  - `locale` (optional, default: `vi`): Response language.
  - `category` (optional, string): Filter by story category.
- **Response:** `200 OK` (Schema: `RbpcStoryListOut`)

---

#### 8. `GET /api/v1/rbpc/stories/{slug}`
**Description:** Retrieve complete story narrative, verified claim evidence, connected artisan profile, and linked real-world experience offering.

- **Auth Required:** None (Public)
- **Path Parameters:** `slug` (string, required)
- **Response:** `200 OK` (`application/json`)
```json
{
  "id": "11112222-3333-4444-5555-666677778888",
  "slug": "tieng-chuong-khiem-cung",
  "title_vi": "Tiếng đồng Phường Đúc: Lửa nghề qua bốn trăm năm",
  "title_en": "The Bronze Casting of Phuong Duc: 400 Years of Sacred Fire",
  "intro_vi": "Từ thời các Chúa Nguyễn vào khai phá đất phương Nam, lò đúc Phường Đúc đã đỏ lửa...",
  "intro_en": "Since the Nguyen Lords journeyed south, the smelting furnaces of Phuong Duc have burned continuous...",
  "primary_asset_url": "/assets/rbpc/stories/phuong-duc-hero.webp",
  "category": "craft_heritage",
  "status": "published",
  "published_at": "2026-10-18T00:00:00Z",
  "reading_time_minutes": 5,
  "creator_slug": "nghe-nhan-duc-dong-tran-van",
  "experience_slug": "workshop-duc-chuong-dong",
  "heritage_place_slug": "kinh-thanh-hue",
  "content_scope": "RBPC_HUE",
  "created_at": "2026-10-17T12:00:00Z",
  "approved_summary_vi": "Làng đúc đồng Phường Đúc kế thừa kỹ nghệ chế tác chuông đồng, đỉnh đồng đỉnh cao từ thời chúa Nguyễn đến triều Nguyễn.",
  "approved_summary_en": "Phuong Duc bronze casting inherits monumental bell and urn smelting traditions refined across centuries.",
  "version": 1,
  "evidence_claims": [
    {
      "id": "22223333-4444-5555-6666-777788889999",
      "statement": "Nghề đúc đồng Phường Đúc có nguồn gốc từ thế kỷ XVII khi chúa Nguyễn dời lò đúc về bờ nam sông Hương.",
      "locale": "vi",
      "claim_category": "historical_fact",
      "source_title": "Đại Nam Nhất Thống Chí — Quyển Kinh Sư",
      "source_url": null,
      "support_type": "direct",
      "review_status": "verified",
      "citation_label": "ĐNNTC, Tập Kinh Sư, tr. 142"
    }
  ]
}
```

---

#### 9. `POST /api/v1/rbpc/cultural-bridge`
**Description:** Ask a source-grounded question to the AI Cultural Bridge scoped strictly to the selected published story and its verified claims. Responses require strict 5-check citation validation. When evidence is insufficient, fails closed to curated canonical text without hallucination.

- **Auth Required:** None (Public, Rate Limited)
- **Rate Limit:** 10 req / min / IP, 30 req / hr / session
- **Request Body:** (`application/json`)
```json
{
  "story_slug": "tieng-chuong-khiem-cung",
  "question": "Vì sao kỹ thuật làm khuôn sáp ong lại quan trọng trong việc đúc chuông Huế?",
  "locale": "vi"
}
```

- **Response:** `200 OK` (`application/json`)
```json
{
  "status": "supported",
  "locale": "vi",
  "answer": "Khuôn sáp ong và đất thó lòng sông Hương cho phép nghệ nhân khắc chạm các đường vân hoa văn sắc sảo trước khi rót hợp kim đồng nóng chảy. Khi sáp tan chảy, khoảng trống để lại giữ nguyên độ chính xác của hoa văn và độ dày thân chuông, yếu tố quyết định âm vang trầm ấm đặc trưng của chuông Huế.",
  "citations": [
    {
      "source_id": "src-phuong-duc-001",
      "title": "Kỹ thuật đúc đồng truyền thống Huế — Viện Nghiên cứu Văn hóa Dân gian",
      "support": "direct",
      "claim_id": "22223333-4444-5555-6666-777788889999",
      "locator": "Chương 3, tr. 78-82"
    }
  ],
  "context_boundary": "Tư liệu lịch sử được trích từ công trình nghiên cứu nghề đồng Huế; quy trình thực tế tại xưởng tuân theo sự hướng dẫn trực tiếp của nghệ nhân đương đại.",
  "epistemic_certainty": "high",
  "review_status": "published_human_approved_context",
  "model_version": "clara-gemini-3.8-flash-tiered-v1",
  "uncertainty_note": null,
  "suggested_followups": [
    "Quy trình pha trộn hợp kim đồng và thiếc tạo tiếng chuông diễn ra như thế nào?",
    "Nghệ nhân Phường Đúc hiện nay còn duy trì kỹ thuật đúc tượng không?"
  ]
}
```

- **Fail-Closed Fallback Response (Insufficient Evidence / Unscoped Query):**
```json
{
  "status": "insufficient_evidence",
  "locale": "vi",
  "answer": "Tài liệu nghiên cứu đã được phê duyệt hiện chưa ghi nhận chi tiết về câu hỏi này. Bạn có thể tham khảo tóm tắt lịch sử đã được kiểm chứng dưới đây hoặc trao đổi trực tiếp với nghệ nhân tại buổi trải nghiệm.",
  "citations": [],
  "context_boundary": "Hệ thống AI không tự suy đoán thông tin ngoài tư liệu lịch sử và chứng thực của nghệ nhân.",
  "epistemic_certainty": "insufficient_sources",
  "review_status": "editorial_fallback",
  "model_version": "clara-gemini-3.8-flash-tiered-v1",
  "uncertainty_note": "Chưa có nguồn kiểm chứng độc lập cho phạm vi câu hỏi này.",
  "suggested_followups": []
}
```

---

#### 10. `GET /api/v1/rbpc/creators/{slug}`
**Description:** Retrieve the profile of a living artisan practitioner. Returns only creators with verified written consent (`consent_status: consented`).

- **Auth Required:** None (Public)
- **Path Parameters:** `slug` (string, required)
- **Response:** `200 OK` (Schema: `RbpcCreatorOut`)
```json
{
  "id": "33334444-5555-6666-7777-888899990000",
  "slug": "nghe-nhan-duc-dong-tran-van",
  "public_name": "Nghệ nhân Trần Văn A",
  "craft_tradition_vi": "Đúc đồng Phường Đúc",
  "craft_tradition_en": "Phuong Duc Bronze Casting",
  "approved_bio_vi": "Hơn 40 năm gìn giữ kỹ thuật đúc đồng truyền thống, truyền nhân đời thứ 4 của gia đình gắn bó với lò đúc bên bờ sông Hương.",
  "approved_bio_en": "Over 40 years preserving traditional bronze casting techniques; 4th generation master smith.",
  "approved_portrait_url": "/assets/rbpc/creators/tran-van-a.webp",
  "public_region": "Phường Đúc, TP. Huế",
  "consent_status": "consented",
  "approved_story_slugs": ["tieng-chuong-khiem-cung"],
  "experience_slugs": ["workshop-duc-chuong-dong"],
  "years_of_practice": 42,
  "generation_lineage": "Đời thứ 4",
  "heritage_place_slug": "kinh-thanh-hue",
  "created_at": "2026-10-17T12:00:00Z"
}
```

---

#### 11. `GET /api/v1/rbpc/experiences/{slug}`
**Description:** Retrieve details of a cultural workshop offering. Explicitly discloses that this is an inquiry-only availability request workflow, NOT an instant payment booking.

- **Auth Required:** None (Public)
- **Path Parameters:** `slug` (string, required)
- **Response:** `200 OK` (`application/json`)
```json
{
  "id": "44445555-6666-7777-8888-999900001111",
  "slug": "workshop-duc-chuong-dong",
  "creator_slug": "nghe-nhan-duc-dong-tran-van",
  "creator_name": "Nghệ nhân Trần Văn A",
  "title_vi": "Trải nghiệm tạo tác khuôn sáp và đúc đồng truyền thống",
  "title_en": "Traditional Wax Mold Sculpting and Bronze Casting Workshop",
  "description_vi": "Tham quan lò đúc cổ truyền, tự tay điêu khắc hoa văn trên khuôn sáp và quan sát quy trình rót đồng nóng chảy.",
  "description_en": "Tour the heritage furnace, hand-carve traditional motifs in wax, and observe molten bronze pouring.",
  "area_public": "Phường Đúc, Huế",
  "duration_minutes": 150,
  "indicative_pricing_display": "Từ 450.000 VNĐ / khách",
  "indicative_price_amount": 450000.0,
  "currency": "VND",
  "availability_mode": "inquiry_only",
  "publication_state": "published",
  "cancellation_policy_text_vi": "Vui lòng thông báo trước 24 giờ nếu quý khách cần đổi ngày.",
  "cancellation_policy_text_en": "Please notify 24 hours in advance to reschedule.",
  "max_party_size": 8,
  "languages_supported": ["vi", "en"],
  "notice": "Yêu cầu trải nghiệm chỉ là bước liên hệ xác nhận lịch hẹn, không phải giao dịch thanh toán trực tuyến tức thì."
}
```

---

#### 12. `POST /api/v1/rbpc/inquiries`
**Description:** Submit a visitor availability request for a workshop experience. Requires client-generated UUID `idempotency_key`, explicit opt-in consent, and valid contact information.

- **Auth Required:** None (Public, Rate Limited)
- **Rate Limit:** 5 req / min / IP, 15 req / day / IP
- **Request Body:** (`application/json`)
```json
{
  "experience_slug": "workshop-duc-chuong-dong",
  "contact": {
    "name": "Lê Thị Thảo",
    "method": "email",
    "value": "thao.le@example.com"
  },
  "preferred_date": "2026-11-05",
  "party_size": 2,
  "message": "Chúng tôi muốn tham gia ca sáng thứ Bảy, có phiên dịch viên tiếng Anh.",
  "consent": {
    "version": "rbpc-inquiry-v1",
    "accepted": true,
    "privacy_accepted": true
  },
  "idempotency_key": "9a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"
}
```

- **Response:** `202 Accepted` (`application/json`)
```json
{
  "reference": "INQ-7F89-A23C",
  "status_token": "tok_sec_99a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4",
  "status": "new",
  "message": "Yêu cầu đã được ghi nhận. Nhà cung cấp sẽ liên hệ xác nhận lịch trống trong vòng 24 giờ.",
  "created_at": "2026-10-18T10:15:00Z"
}
```

- **Validation Rules & Invariants:**
  1. `consent.accepted` MUST be `true`. If `false`, returns `400 Bad Request` (`RBPC_CONSENT_REQUIRED`).
  2. `preferred_date` MUST NOT be in the past.
  3. `idempotency_key` (length 16-128 chars): repeated submission with identical key returns cached response without duplicate records.

---

#### 13. `GET /api/v1/rbpc/inquiries/status/{opaqueToken}`
**Description:** Check status of an inquiry using the client-held secret bearer token. **Zero PII is returned** in the response.

- **Auth Required:** None (Bearer token in path URL)
- **Path Parameters:** `opaqueToken` (string, required)
- **Response:** `200 OK` (`application/json`)
```json
{
  "reference": "INQ-7F89-A23C",
  "experience_title": "Trải nghiệm tạo tác khuôn sáp và đúc đồng truyền thống",
  "status": "contacted",
  "status_message": "Nhà cung cấp đã nhận thông tin và đang liên hệ với bạn để xác nhận chi tiết.",
  "preferred_date": "2026-11-05",
  "party_size": 2,
  "last_updated_at": "2026-10-18T14:30:00Z"
}
```

- **Privacy Invariant:** Field comparison guarantees that `email`, `phone`, `name`, `message`, and private partner notes are **never** present in this response.

---

#### 14. `GET /api/v1/rbpc/impact`
**Description:** Retrieve verified aggregate platform metrics. Strictly separates real observed counts from forward-looking commercial projections.

- **Auth Required:** None (Public)
- **Response:** `200 OK` (`application/json`)
```json
{
  "observed_metrics": {
    "published_stories_count": 3,
    "consented_creators_count": 1,
    "active_experiences_count": 1,
    "total_inquiries_received": 14,
    "verified_heritage_places_count": 14,
    "verified_source_citations_count": 28,
    "sponsor_support_vnd_verified": 202360638.0
  },
  "projected_metrics": {
    "estimated_monthly_demand": 120,
    "projected_local_value_addition_vnd": 54000000.0,
    "projection_basis": "Các số liệu dự phóng là giả định mô hình kinh doanh phục vụ nghiên cứu và đề án RBPC 2026, không phải doanh thu đã ghi nhận."
  },
  "scope": "RBPC_HUE",
  "generated_at": "2026-10-18T15:00:00Z"
}
```

- **Sponsorship Rule:** `sponsor_support_vnd_verified` is exactly `202,360,638 VND` based on signed in-kind documentation (BNIX + Phổ Tuệ). The unverified verbal claim of "206M" is rejected.

---

### Group C: Partner Operations (`/api/v1/rbpc/partner/*`)

#### 15. `GET /api/v1/rbpc/partner/inquiries`
**Description:** Retrieve incoming visitor inquiries for the authenticated provider's experience offerings.

- **Auth Required:** Partner / Staff JWT (`role: partner`, `role: staff`)
- **Response:** `200 OK` (Schema: `RbpcPartnerInquiryListOut`)
```json
{
  "items": [
    {
      "id": "55556666-7777-8888-9999-000011112222",
      "reference": "INQ-7F89-A23C",
      "experience_slug": "workshop-duc-chuong-dong",
      "experience_title": "Trải nghiệm tạo tác khuôn sáp và đúc đồng truyền thống",
      "contact_name": "Lê Thị Thảo",
      "contact_method": "email",
      "contact_value": "thao.le@example.com",
      "preferred_date": "2026-11-05",
      "party_size": 2,
      "message": "Chúng tôi muốn tham gia ca sáng thứ Bảy, có phiên dịch viên tiếng Anh.",
      "status": "new",
      "created_at": "2026-10-18T10:15:00Z",
      "updated_at": "2026-10-18T10:15:00Z"
    }
  ],
  "total": 1
}
```

---

#### 16. `PATCH /api/v1/rbpc/partner/inquiries/{id}`
**Description:** Transition inquiry status (`new` -> `contacted` -> `confirmed` / `declined` / `closed`).

- **Auth Required:** Partner / Staff JWT
- **Request Body:** (`application/json`)
```json
{
  "status": "contacted",
  "note": "Đã gửi email xác nhận lịch trống lúc 14:00 ngày 18/10."
}
```
- **Response:** `200 OK` (Updated `RbpcPartnerInquiryOut`)
- **Error Codes:**
  - `403 FORBIDDEN_SCOPE`: Inquiry does not belong to caller's provider account.
  - `404 RBPC_INQUIRY_NOT_FOUND`: Non-existent inquiry ID.

---

### Group D: Privileged Editorial & 3D Rights (`/api/v1/admin/heritage/*`)

#### 17. `POST /api/v1/admin/heritage/assets/{id}/rights-review`
**Description:** Record legal rights evaluation and clearance for a media asset or 3D Sketchfab model.

- **Auth Required:** Staff / Admin (`role: staff`, `role: admin`)
- **Request Body:** (`application/json`)
```json
{
  "license_label": "CC BY 4.0",
  "noai": false,
  "commercial_use_status": "permitted",
  "embed_permission_status": "permitted",
  "accuracy_grade": "measured_photogrammetry",
  "content_status": "cleared_for_this_use",
  "attribution_text": "Model by matousekfoto via Sketchfab, licensed under CC BY 4.0."
}
```
- **Response:** `200 OK` (`HeritageMediaAssetOut`)

---

## 6. Security, Rights, and Privacy Invariants

### 1. Zero PII Leakage
- Public status checks (`GET /api/v1/rbpc/inquiries/status/{opaqueToken}`) require high-entropy tokens and return only lifecycle metadata.
- Visitor email, phone, name, and notes are accessible **exclusively** to the assigned provider under authenticated, server-scoped endpoints (`/api/v1/rbpc/partner/*`).

### 2. Sketchfab 3D Rights Decision Gate (ADR 05)
- **Permanent Rejection:** `SF-020` (`nguyenduc0`) is permanently rejected as imagined/unverified architecture. It must NEVER be published as documentary heritage.
- **Commercial & AI Ingestion Block:** `SF-010` (Agisoft) and `SF-017` (Miguel Bandera) are tagged `CC BY-NC-SA` and `NoAI: true`. They are prohibited from commercial self-hosting or AI embedding corpus ingestion.
- **Allowed Embeds:** `SF-009`, `SF-011`, and `SF-016` (`CC BY 4.0`) are permitted for user-initiated lazy iframe embedding with prominent author attribution.
- **2D Fallback:** Any heritage place without cleared 3D rights returns a clean 2D still image and citation card.

### 3. Source-Grounded AI Cultural Bridge Citations (ADR 04)
Every AI answer citation must pass a 5-point verification pipeline before being served to the client:
1. **UUID Format Check:** Well-formed UUID or registered source slug.
2. **Database Existence Check:** Verified record exists in `heritage_source_evidence`.
3. **Retrieval Set Presence:** Cited claim was present in the retrieved context for the target story.
4. **Claim-Source Join:** The cited claim has an authentic join to the backing bibliographic source.
5. **Locator Sanity:** Volume, page, or decree reference matches known source bounds.

If any check fails, the API strips ungrounded text and returns `status: insufficient_evidence` with the human-approved canonical summary.

---

## 7. Migration & Deployment Synchronization Checklist

When this API contract is integrated into the active FastAPI application factory (`backend/app.py` in Phase 2):

1. **Schema Imports:** Verify `backend.apischemas.heritage` and `backend.apischemas.rbpc` import cleanly.
2. **Route Inventory:** Execute `python scripts/dev/generate_route_inventory.py` to index new paths.
3. **OpenAPI Snapshot:** Execute `REGENERATE_OPENAPI_SNAPSHOT=1 pytest tests/backend/test_openapi_snapshot.py` to synchronize contract snapshots.
4. **Rust Gateway Routing:** Ensure `backend-rust/config/route-modes.toml` directs `/api/v1/heritage/*` and `/api/v1/rbpc/*` through the fallback proxy to FastAPI until native Rust handlers are implemented.
5. **Frontend Typings:** Execute `cd frontend && npm run gen:api` to regenerate TypeScript types in `frontend/src/types/api.ts`.
