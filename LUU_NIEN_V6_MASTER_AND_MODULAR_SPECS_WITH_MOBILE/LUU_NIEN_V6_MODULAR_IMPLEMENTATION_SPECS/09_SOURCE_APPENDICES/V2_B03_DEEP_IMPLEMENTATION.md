# V2 B3: source-derived engineering detail

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V2.B3`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## B3. CANONICAL DATA MODEL — DATA CONTRACT Ở MỨC FIELD

### B3.1 Quy tắc chung

- PK: UUIDv7 hoặc UUIDv4 thống nhất theo ADR, public key là slug bất biến có alias chuyển hướng; không lấy ordinal 01–18 làm identity vĩnh viễn.
- Thời gian: `timestamptz` UTC; hiển thị Asia/Ho_Chi_Minh theo người dùng; ghi precision/range cho niên đại lịch sử thay vì ép mọi sự kiện thành một ngày Gregorian chính xác.
- Text: Unicode NFC, duy trì bản gốc Hán–Nôm có `script`, bản phiên âm có `transliteration_scheme`, bản dịch có translator/source/version.
- Số 3D: coordinate system, đơn vị `m`, transform, bbox, LOD, format, hashing, asset source.
- File storage: `object_key` private; public signed URL do API cấp nếu quyền cho phép; URL không là bằng chứng quyền sử dụng.
- Mỗi claim có `source_locator` đủ tìm lại bằng tài liệu gốc (trang, mục, số ảnh, timestamp media), không chỉ URL domain.
- Bất cứ field nhập từ AI: `origin=ai_generated`, `verified=false` mặc định; không đổi thành verified bằng batch script không có reviewer.

### B3.2 Bảng dữ liệu đề xuất — Heritage

| Table | Fields tối thiểu (TARGET) | Ràng buộc nghiệp vụ |
|---|---|---|
| `heritage_urn` | `id`, `canonical_code`, `name_vi`, `name_han`, `display_order`, `location_id`, `record_version`, `publication_state` | đúng 9 canonical urn được đối chiếu; không dùng tên làm khóa |
| `heritage_relief` | `id`, `urn_id`, `canonical_code`, `source_ordinal`, `name_vi`, `name_han`, `category_id`, `visual_description`, `publication_state` | unique `(urn_id, source_ordinal)` nếu danh mục duyệt thống nhất; không publish thiếu bằng chứng định danh |
| `heritage_relief_alias` | `id`, `relief_id`, `alias`, `language`, `authority_source_id`, `is_preferred` | alias Hán–Nôm/văn tự/phiên âm không ghi đè label gốc |
| `heritage_classification` | `id`, `taxonomy_version`, `code`, `label_vi`, `label_en`, `parent_code` | quản lý version, 9 category AI seed chưa được coi taxonomy học thuật chuẩn |
| `heritage_relationship` | `id`, `subject_id`, `predicate`, `object_id`, `claim_id`, `review_state` | quan hệ quan trọng phải gắn claim/citation |
| `heritage_georeference` | `id`, `entity_id`, `geometry`, `historical_period`, `precision`, `source_id`, `uncertainty_radius_m` | tọa độ giả định có nhãn approximate, tránh vị trí chính xác giả |

### B3.3 Source, claim, claim–source evidence

| Table | Fields tối thiểu (TARGET) | Rules |
|---|---|---|
| `sources` | `id`, `source_type`, `title`, `creator`, `publisher`, `year`, `edition`, `language`, `canonical_uri`, `checksum`, `rights_id`, `record_status` | unique theo ISBN/DOI/ID khi có; có nguồn không đồng nghĩa đã đối chiếu |
| `source_locators` | `id`, `source_id`, `locator_type`, `page_range`, `section`, `folio`, `timecode`, `quote_excerpt`, `archive_ref` | tối thiểu một locator khi dùng để kiểm chứng claim |
| `historical_claims_v` | `claim_id`, `version`, `entity_id`, `statement`, `claim_type`, `certainty`, `origin`, `author_id`, `editorial_status`, `valid_from`, `supersedes_version` | composite unique `(claim_id, version)`, immutable after published |
| `claim_evidence` | `claim_id`, `claim_version`, `source_locator_id`, `relation`, `strength`, `reviewer_id`, `reviewed_at`, `notes` | relation enum `supports/contradicts/contextualizes/primary_evidence_for` |
| `review_decisions` | `id`, `target_type`, `target_id`, `target_version`, `actor`, `decision`, `reason`, `evidence_hash`, `timestamp` | append-only, creator != final reviewer |
| `content_release` | `id`, `content_version`, `catalog_snapshot_hash`, `source_snapshot_hash`, `claim_snapshot_hash`, `asset_manifest_hash`, `published_at` | toàn bộ bài học trỏ snapshot release để tái lập |

**Điểm thiết kế:** `backend/history_models.py` đã có `HistoricalEntity`, `HistoricalSource`, `HistoricalClaim`, `HistoricalClaimSource`, `HistoricalContentAuditLog`; trước khi tạo bảng mới phải mapping với các model legacy. Ưu tiên mở rộng hệ thống hiện hữu bằng migration an toàn; chỉ thêm `*_v` nếu immutable version không thể retrofit đúng cách.

### B3.4 Media/3D registry

| Field | Type/constraint | Ý nghĩa |
|---|---|---|
| `asset_id` | UUID PK | một định danh media bất biến |
| `heritage_entity_id` | UUID FK nullable | chủ thể liên quan |
| `media_kind` | enum `image/glb/audio/video/embed/document/scan` | loại hiển thị |
| `source_file_sha256` | char(64) unique per binary | chống trùng file và sửa lặng |
| `storage_object_key` | text | vị trí origin, không lưu token trong DB |
| `lod_level` | enum `preview/mobile/standard/high` nullable | mục đích chất lượng |
| `mesh_coordinate_system` | text nullable | gốc/trục tọa độ |
| `mesh_units` | enum `m/cm/mm` nullable | quy đổi kích thước |
| `mesh_bounds` | JSONB | bbox, camera fit, hotspot validation |
| `capture_method` | text | photogrammetry/scan/illustrative/manual |
| `accuracy_grade` | enum + `measurement_report_id` | độ tin cậy hình khối |
| `source_object_rights_id` | UUID FK | quyền bản gốc và dẫn xuất |
| `host_permission` | enum approved/denied/unknown | hosting |
| `embed_permission` | enum approved/denied/unknown | nhúng |
| `commercial_permission` | enum approved/denied/unknown | mục đích thương mại |
| `public_visibility` | enum draft/approved/published/withdrawn | trạng thái hiển thị |
| `rights_expiry_at` | datetime nullable | tự chặn khi hết hạn |
| `derivative_of_asset_id` | UUID nullable | truy xuất tài sản gốc |

**Policy:** `can_serve_asset(user, asset, purpose, region, now)` = rights valid AND content published AND not withdrawn AND accuracy disclosure set AND audience authorized. `has_3d` là kết quả predicate này theo mục đích `public_explore`, không được chỉ kiểm `!= blocked`.

### B3.5 Pedagogy / Evidence-Linked Learning Object (ELLO)

| Table | Trường bắt buộc | Invariant |
|---|---|---|
| `learning_object` | `id`, `canonical_entity_id`, `title`, `summary`, `language`, `school_level`, `curriculum_tags`, `status`, `version` | có canonical entity duyệt |
| `learning_object_claim` | `ello_id`, `claim_id`, `claim_version`, `role` | claim `provisional` của học sinh khác claim authority của học liệu |
| `learning_object_source` | `ello_id`, `source_locator_id`, `purpose`, `release_id` | nguồn duyệt và có locator |
| `learning_object_representation` | `ello_id`, `asset_id`, `learning_purpose`, `fallback_asset_id`, `fallback_equivalence_note` | thiếu AR vẫn hoàn thành cùng learning outcome |
| `learning_object_task` | `id`, `ello_id`, `stage`, `prompt`, `response_type`, `max_words`, `evidence_requirements`, `scoring_policy` | không dùng câu hỏi chỉ “ấn nút” làm inquiry task |
| `learning_object_rubric` | `id`, `ello_id`, `version`, `criteria`, `level_descriptors`, `rater_notes` | rubric đóng băng theo release |
| `lesson_release` | `id`, `ello_id`, `version`, `asset_manifest_hash`, `claim_release_hash`, `review_state`, `published_by` | immutable after publish |
| `class_assignment` | `id`, `classroom_id`, `lesson_release_id`, `available_from/to`, `due_at`, `accessibility_policy` | classroom ACL |
| `student_attempt` | `id`, `assignment_id`, `pseudonymous_actor_id`, `version`, `state`, `submitted_at`, `idempotency_key` | submission chỉ do server xác nhận |
| `attempt_response` | `id`, `attempt_id`, `task_id`, `response_version`, `text`, `attached_evidence_ids`, `submitted_at` | lưu bản sửa khác nhau, không ghi đè |
| `attempt_feedback` | `id`, `attempt_id`, `rubric_version`, `rater_type`, `score`, `criterion_scores`, `evidence_note`, `revision_required` | AI suggest ≠ human authoritative score |
| `assessment_rater` | `id`, `role`, `training_version`, `blinded_assignment_ref` | phục vụ reliability nếu nghiên cứu |

### B3.6 Google Forms research vault (nằm ngoài core LMS)

| Entity | Fields | Bảo vệ |
|---|---|---|
| `study_protocol` | `study_id`, `version`, `design`, `eligibility`, `sampling`, `ethics_status`, `consent_basis`, `locked_at` | project-level RBAC |
| `questionnaire_version` | `form_id`, `revision`, `question_text`, `question_type`, `options`, `skip_logic`, `is_multi_select` | snapshot trước mapping |
| `raw_import_file` | `file_id`, `sha256`, `imported_by`, `import_time`, `encrypted_object_key`, `source_export_name` | chỉ vault, không public |
| `research_participant` | `pid`, `study_id`, `school_code`, `grade_band`, `recruitment_group` | pseudonymization; không giữ email trong analysis set |
| `survey_response` | `response_id`, `pid`, `form_revision`, `submitted_at`, `item_id`, `coded_value`, `missing_reason` | scope giới hạn; mọi export log |
| `analysis_snapshot` | `id`, `study_id`, `source_sha256`, `transform_commit`, `dictionary_version`, `counts_sha256` | tái lập paper figures |
| `research_release` | `id`, `abstract/manuscript_id`, `analysis_snapshot_id`, `publication_status`, `approved_by` | xuất bảng tổng hợp không PII |

**Không yêu cầu** dữ liệu Google Forms phục vụ mục tiêu vận hành LMS thường ngày; không trộn lịch sử học sinh vào tracking tiếp thị. Nếu có trẻ chưa thành niên, phải có căn cứ đạo đức và quy chế xử lý dữ liệu được phê duyệt phù hợp bối cảnh thực tế.

### B3.7 SQL target samples — chạy trên sandbox mới sau khi ADR được ký

```sql
-- TARGET example only; reconcile with existing alembic and models before implementation.
CREATE TABLE IF NOT EXISTS heritage_review_decisions (
    id uuid PRIMARY KEY,
    target_type text NOT NULL,
    target_id uuid NOT NULL,
    target_version integer NOT NULL CHECK (target_version > 0),
    decision text NOT NULL CHECK (decision IN ('approved','rejected','needs_changes','disputed','withdrawn')),
    reviewer_id uuid NOT NULL,
    evidence_locator_id uuid,
    rationale text NOT NULL,
    decided_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_review_actor_target_decision
  ON heritage_review_decisions (target_type, target_id, target_version, reviewer_id, decision);

CREATE TABLE IF NOT EXISTS learning_object_releases (
    id uuid PRIMARY KEY,
    learning_object_id uuid NOT NULL,
    version integer NOT NULL CHECK(version > 0),
    snapshot jsonb NOT NULL,
    snapshot_sha256 char(64) NOT NULL,
    status text NOT NULL CHECK(status IN ('draft','approved','published','withdrawn')),
    published_at timestamptz,
    UNIQUE (learning_object_id, version)
);
CREATE INDEX IF NOT EXISTS idx_lesson_release_status
  ON learning_object_releases(status, published_at DESC);

CREATE TABLE IF NOT EXISTS learning_attempt_events (
    id uuid PRIMARY KEY,
    attempt_id uuid NOT NULL,
    event_kind text NOT NULL,
    actor_id uuid,
    request_id text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    happened_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (attempt_id, request_id, event_kind)
);
```

**Migration methodology:** chạy `alembic heads`/`history` với repo thực; tạo expand migration nullable/additive; deploy readers compatible; backfill idempotent theo batch (mỗi batch có checksum); xác minh FK/unique trên sample; bật writer mới qua feature flag; contract test trên staging; sau ít nhất một release ổn định mới `contract/remove legacy`. Không xóa DB column khi chưa kiểm tra app mobile đang dùng.

---

