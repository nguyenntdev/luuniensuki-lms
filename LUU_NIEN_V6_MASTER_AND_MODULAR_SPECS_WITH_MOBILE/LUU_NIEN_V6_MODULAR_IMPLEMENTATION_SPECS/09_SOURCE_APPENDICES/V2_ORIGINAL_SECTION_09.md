# V2 original archival technical chapter — SECTION_09

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 9. API v1/v2 CONTRACTS — CỤ THỂ ĐỂ TRIỂN KHAI

### 9.1 Quy ước

- API namespace `/api/v2`; backward compat `/api/v1` tối thiểu 2 releases hoặc documented deprecation.
- Standard success `{data,meta:{request_id,revision,source_snapshot}}`; error `{error:{code,message,details,request_id}}`.
- `ETag/If-Match` cho mutation conflict; `Idempotency-Key` cho submission/inquiry; pagination cursor; rate-limit headers.
- Bắt buộc staff+scope guard và audit trên mutate; không trả `editor_notes` trong public DTO.

### 9.2 Public heritage routes

```http
GET /api/v2/collections?type=documentary_heritage
GET /api/v2/collections/cuu-dinh/urns
GET /api/v2/urns/{urnId}/motifs?theme=&cursor=&limit=
GET /api/v2/motifs/{motifId}?include=images,claims,sources
GET /api/v2/motifs/{motifId}/source-packet
GET /api/v2/claims/{claimId}/evidence
GET /api/v2/sources/{sourceId}
GET /api/v2/media/{assetId}/variants?device=low|medium|high
GET /api/v2/heritage/search?q=&lang=&type=
GET /api/v2/heritage/places?registry=world_heritage
GET /api/v2/timeline?collection_id=&from=&to=
```

**Example motif response:**

```json
{
  "data": {
    "id": "uuid",
    "canonical_code": "MOTIF-URN-CAO-001",
    "urn_id": "uuid",
    "editorial_status": "published",
    "names": [{"lang":"vi","value":"...","reviewed":true}],
    "media": [{"id":"uuid","type":"image","fallback":true,"rights":"cleared"}],
    "claims": [{"id":"uuid","statement_vi":"...","certainty":"editor_reviewed","sources":[{"source_id":"uuid","locator":"vol/page"}]}]
  },
  "meta": {"content_version":"2026.10.x","request_id":"uuid"}
}
```

No claim published unless `claim.sources` non-empty and source `status >= editor_reviewed` or contains documented exception of non-factual observation.

### 9.3 Learning APIs

```http
GET    /api/v2/learning-objects/{elloId}/versions/{version}
POST   /api/v2/teacher/learning-objects
PATCH  /api/v2/teacher/learning-objects/{elloId}/draft
POST   /api/v2/teacher/learning-objects/{elloId}/submit-review
POST   /api/v2/editor/learning-objects/{elloId}/decision
POST   /api/v2/classes/{classId}/assignments
POST   /api/v2/inquiry-attempts
PATCH  /api/v2/inquiry-attempts/{attemptId}/steps/{step}
POST   /api/v2/inquiry-attempts/{attemptId}/submit
GET    /api/v2/inquiry-attempts/{attemptId}/rubric
POST   /api/v2/rubric-scores
POST   /api/v2/inquiry-attempts/{attemptId}/revisions
GET    /api/v2/students/me/learning-history
GET    /api/v2/teachers/classes/{classId}/evidence-report
```

`POST /inquiry-attempts` response includes assignment-fixed ELLO version and source packet hash. API validates `student_id` from auth token, never from trusted body field. Submission freezes raw text and evidence references; feedback does not alter original version.

### 9.4 Research APIs (private; separate network)

```http
POST /internal/research/studies/{studyId}/imports/google-forms [upload csv/xlsx]
GET  /internal/research/studies/{studyId}/import-audit/{batchId}
POST /internal/research/studies/{studyId}/validate-aggregates
GET  /internal/research/studies/{studyId}/tables?version=...
POST /internal/research/studies/{studyId}/freeze
GET  /internal/research/studies/{studyId}/provenance-report
```

No public access to raw survey. Authorization requires `research_analyst` and explicit `study_id` scope, step-up MFA for export; download expires, logs purpose, excludes PII except explicit lawful review.

### 9.5 AI APIs

```http
POST /api/v2/ai/history/ask      {question,context_scope,lesson_version,locale}
POST /api/v2/ai/history/critique {student_draft,evidence_ids,rubric_version}
GET  /api/v2/ai/evaluations/{runId} [staff]
```

Mandatory response `answer,claims[],citations[],abstained,uncertainty,knowledge_snapshot_id,evaluation_model_id`; no uncited confident historical assertions; do not send minors' personally identifying data to model.

### 9.6 Inquiry APIs

```http
POST /api/v2/inquiries
GET  /api/v2/inquiries/status/{opaqueToken}
GET  /api/v2/partner/inquiries
PATCH /api/v2/partner/inquiries/{id} [If-Match + Idempotency-Key]
POST /api/v2/partner/creators/{id}/consent-revoke
```

`POST` returns 202 *only after durable database commit*; if upstream unreachable return 503 + local UI queued-but-not-sent badge when explicitly allowed, never simulated success. Retention/revocation processes use verified identity, audit event and data purge plan.

---

