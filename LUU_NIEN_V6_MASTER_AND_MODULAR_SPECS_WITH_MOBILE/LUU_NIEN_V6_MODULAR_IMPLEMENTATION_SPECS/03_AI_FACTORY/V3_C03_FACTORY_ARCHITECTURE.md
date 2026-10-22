# V3.C3: research factory deep specification

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V3.C3`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## C3. Database schema & migrations: proof chain từ nguồn đến câu lịch sử

### C3.1. Quy tắc tích hợp bảng hiện có

- `historical_sources`: canonical bibliography cấp tác phẩm/ấn bản. Không thay thế `title/doi/url/language/rights_status/verification_status` hiện có.
- `historical_claims`: canonical atomic historical claims, `origin=ai_generated` khi do AI đề nghị, `verification_status` đúng Enum hiện có (`unreviewed`, `source_attached`, `editor_reviewed`, `expert_verified`, `disputed`, ...).
- `historical_claim_sources`: mối liên hệ claim–source existing; phải bổ sung `source_passage_id` qua new binding extension hoặc nullable FK khi migration an toàn. Không dùng `source_id` trần làm bằng chứng quote nếu thiếu locator.
- `history_stories`: bản trình bày block-based đã có; chỉ tạo story mới sau khi human approve; giữ `blocks` versioned, không cho subagents edit trực tiếp.
- `historical_content_audit_log`: audit hiện có, nhưng machine pipeline có bảng append-only riêng và archive policy; không ghi prompt chứa PII vào audit công khai.
- Dùng Alembic revision mới sau khi xử lý multi-head anomaly ở V2 `R0-006`; không tạo migration song song mất `down_revision`.

### C3.2. Các bảng mới `[TARGET]`

| Bảng (PostgreSQL) | Primary key và cột quan trọng | Index / constraint bắt buộc | Mục đích |
|---|---|---|---|
| `research_runs` | `id, scope_id, subject_ids, source_release_id, status, mode, config_hash, cost_budget, created_by` | unique idempotency nonce; GIN subject_ids | version toàn run |
| `research_phases` | `id, run_id, phase_code, wave, input_sha, state, gate_sha` | UNIQUE(run_id,phase_code,wave), state index | trạng thái barrier |
| `research_agent_jobs` | `id, phase_id, slot_number, agent_role, state, attempt, lease_until, idempotency_key` | CHECK slot 1..10; unique phase/slot/wave; unique idempotency | 10 concurrent jobs |
| `research_agent_artifacts` | `id, job_id, uri, sha256, schema_version, source_manifest, metrics` | unique(job_id,sha256), audit access | output immutable |
| `source_candidates` | `id, run_id, url, provider, metadata, discovery_trace, canonical_fingerprint` | dedup fingerprint per scope | kết quả search chưa kiểm |
| `source_access_policies` | `id, source_id, source_version, license, fetch_allowed, store_allowed, quote_allowed, derivative_allowed, tdm_allowed, display_allowed, evidence_uri, reviewed_by` | restrict by policy; no default allow | kiểm soát bản quyền |
| `source_snapshots` | `id, historical_source_id, sha256, mime, byte_size, storage_uri, accession_time, edition_key, rights_decision_id` | unique source/hash; immutable after insert | đúng phiên bản tài liệu |
| `source_pages` | `id, snapshot_id, pdf_index, printed_page_label, image_uri, text_uri, extraction_version, quality_flags` | unique(snapshot,pdf_index), idx printed label | OCR/trang thật |
| `source_passages` | `id, snapshot_id, page_id, start_offset, end_offset, bbox_json, literal_text_sha256, short_quote, language, transcript_version, review_status` | source FK; hash; non-overlap validation optional | trích đoạn có locator |
| `source_text_variants` | `id, passage_id, script, edition, original, transcription, transliteration, translation, reviewer_id, verified_at` | unique(passage,script,edition,version) | bảo tồn dị bản Hán–Nôm |
| `historical_claim_evidence` | `id, claim_id, passage_id, support_type, rationale, confidence_rubric_version, reviewed_by` | unique(claim,passage,support); FK | mệnh đề–đoạn bằng chứng |
| `source_dependency_edges` | `from_source_id, to_source_id, relation_type, rationale` | unique edge, DAG validation where applicable | tránh double-count nguồn |
| `ai_content_drafts` | `id, entity_id, run_id, language, audience, status, outline_sha, revision_no` | unique(entity/run/language/audience/revision) | full nội dung AI |
| `ai_content_blocks` | `id, draft_id, block_key, section_kind, text_uri, word_count, claim_refs, locator_refs, review_status` | FK, block order, non-null claim refs for facts | nội dung theo section |
| `ai_validation_findings` | `id, draft_id, agent_job_id, severity, rule_id, text_span, claim_id, message, resolution_status` | severity index, trace | kết quả red-team |
| `ai_editorial_approvals` | `id, draft_id, reviewer_user_id, reviewer_role, decision, signed_at, source_snapshot_sha, comment` | reviewer can't equal draft generator; immutable | human signature |
| `ai_publication_releases` | `id, run_id, manifest_sha, artifact_uri, approved_at, published_at, status, previous_release_id` | unique manifest_sha; partial unique active per scope | atomic public release |
| `ai_correction_events` | `id, release_id, trigger_type, source_id, previous_claim_id, new_claim_id, rationale, opened_at` | idx affected artifacts | corrections/retractions |
| `ai_agent_provider_usage` | `id, job_id, provider, model, input_tokens, output_tokens, spend, API_calls, timestamp` | per run/phase rollups | cost audit |

**Mọi FK với learner/student tables mặc định không được tạo.** Dữ liệu khảo sát Google Forms không được tự đưa vào corpus AI tạo sử liệu. `research_runs` của historical content khác bảng research survey và khác hệ thống inquiry của RBPC.

### C3.3. DDL cốt lõi minh họa (sửa kiểu/namespace trong migration thật)

```sql
-- TARGET DDL sketch: cần được chuyển thành migration Alembic khi triển khai.
CREATE TABLE research_phases (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES research_runs(id),
    phase_code TEXT NOT NULL CHECK (phase_code IN
        ('P00','P01','P02','P03','P04','P05','P06','P07','P08','P09','P10','P11')),
    wave INTEGER NOT NULL DEFAULT 1 CHECK (wave >= 1),
    state TEXT NOT NULL CHECK (state IN
        ('QUEUED','DISPATCHED','RUNNING','FAN_IN','GATED','BLOCKED','FAILED','CANCELED')),
    input_sha256 CHAR(64) NOT NULL,
    gate_manifest_sha256 CHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(run_id,phase_code,wave)
);
CREATE TABLE research_agent_jobs (
    id UUID PRIMARY KEY,
    phase_id UUID NOT NULL REFERENCES research_phases(id),
    slot_number SMALLINT NOT NULL CHECK (slot_number BETWEEN 1 AND 10),
    role_key TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    state TEXT NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 0,
    lease_until TIMESTAMPTZ,
    output_sha256 CHAR(64),
    completed_at TIMESTAMPTZ,
    UNIQUE(phase_id,slot_number)
);
CREATE INDEX research_job_leases_idx ON research_agent_jobs(state,lease_until);
CREATE TABLE source_snapshots (
    id UUID PRIMARY KEY,
    historical_source_id UUID NOT NULL REFERENCES historical_sources(id),
    sha256 CHAR(64) NOT NULL,
    storage_uri TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    rights_decision_id UUID NOT NULL REFERENCES source_access_policies(id),
    edition_key TEXT NOT NULL,
    acquired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(historical_source_id,sha256)
);
CREATE TABLE source_passages (
    id UUID PRIMARY KEY,
    source_snapshot_id UUID NOT NULL REFERENCES source_snapshots(id),
    page_index INTEGER NOT NULL CHECK (page_index >= 0),
    page_label TEXT,
    start_offset INTEGER CHECK (start_offset >= 0),
    end_offset INTEGER,
    text_sha256 CHAR(64) NOT NULL,
    bbox JSONB,
    extraction_method TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'UNREVIEWED',
    CHECK (end_offset IS NULL OR end_offset >= start_offset)
);
CREATE INDEX source_passages_snapshot_idx ON source_passages(source_snapshot_id,page_index);
CREATE TABLE historical_claim_evidence (
    id UUID PRIMARY KEY,
    claim_id UUID NOT NULL REFERENCES historical_claims(id),
    passage_id UUID NOT NULL REFERENCES source_passages(id),
    support_type TEXT NOT NULL,
    analysis_note TEXT,
    review_status TEXT NOT NULL DEFAULT 'UNREVIEWED',
    UNIQUE(claim_id,passage_id,support_type)
);
```

**Không copy DDL sketch trực tiếp vào production:** FK phải khớp schema thực; `research_runs` và `source_access_policies` cần được khai báo trước; model classes, Enum definitions, triggers và policies phải được thiết kế trong các migration Alembic có thứ tự. Một số ràng buộc quan trọng (cấm agent tự duyệt, one active release, publication precondition) phải ở service transaction và database trigger/constraint nơi phù hợp.

### C3.4. Nội dung mỗi record `source_passage` tối thiểu

```json
{
  "passage_id":"uuid",
  "source_id":"historical_sources.uuid",
  "snapshot_id":"immutable-source-snapshot.uuid",
  "edition":"ấn bản A; lần in B",
  "pdf_page_index":12,
  "printed_page":"trang 9",
  "bbox":[48.1,102.2,480.5,196.4],
  "extract_method":"ocr|native_pdf|manual_transcript",
  "exact_transcription_sha256":"<hex>",
  "source_language":"vi|zh-Hant|en|other",
  "quote_display_permission":"allowed|limited|not_allowed",
  "claim_ids":["uuid"],
  "locator_verified_at":null,
  "human_verified_by":null
}
```

`bbox` phải chỉ rõ coordinate space (PDF points / image pixels / normalized 0–1), page rotation và crop URI, không chỉ có bốn số không rõ đơn vị. Nếu không có PDF page, dùng section+paragraph ID hoặc `document_range` với canonical source snapshot. Phân biệt `pdf_page_index=12` và `printed_page=9` khi dẫn tài liệu.

### C3.5. Quy tắc citation chain ở từng cấp

- Search candidate **không phải** nguồn lịch sử đã kiểm; `source_candidates` không được nối thẳng với `historical_claims`.
- Metadata DOI có thể hợp lệ nhưng không chứng minh một phát biểu xuất hiện trong full text.
- `source_snapshot` là nội dung đọc thực sự tại một thời điểm, checksum ghi bất biến.
- `source_passage` cần text literal hoặc snapshot crop + locator, với quality flags.
- `historical_claim_evidence` thể hiện quan hệ `supports`/`contradicts`/`contextualizes` có lý do, không chỉ citation list.
- `ai_content_block` phải trỏ claim versions đã kiểm; không dùng toàn bộ bibliography để hợp thức hóa đoạn dài.
- Public frontend bấm vào citation phải dẫn được **record nguồn và locator** phù hợp quyền; nếu nguồn có bản quyền không được hiển thị excerpt thì vẫn cho citation metadata và đường đến trang nhà xuất bản hợp lệ.
- Rút quyền một source: cascade flag `RIGHTS_REVOKED`, re-evaluate source excerpts, citation display và dependent documents; không xóa audit gốc.

### C3.6. Transactions, locks, migration & row-level access

1. Upsert candidate dùng normalized DOI/ISBN/URL/content hash + edition, không lấy title làm PK.
2. Raw snapshot immutable; regenerate tạo version mới, không overwrite object key cũ.
3. `claim` từ AI gắn `origin=ai_generated`, `verification_status=unreviewed`, rồi `source_attached`; `expert_verified` chỉ qua human workflow.
4. Duyệt claim và duyệt quyền media là hai transaction khác nhau; public cần cả hai đúng.
5. `SERIALIZABLE` hoặc transaction lock phù hợp cho đổi public release pointer, retry theo conflict.
6. Optimistic version check (`If-Match`/`revision_no`) cho biên tập nội dung.
7. Content scope check ở mọi query, kể cả vector index và search cache.
8. Object storage private; agent chỉ nhận pre-signed URI ngắn hạn trong scope đã cho.
9. Retention policies được pháp chế/người quản trị quyết định; không đồng nhất logs AI với phản hồi học sinh.
10. Backfill chạy dry-run và checksum trước; rollback là migration/feature flag có kế hoạch, không drop data production.

---
