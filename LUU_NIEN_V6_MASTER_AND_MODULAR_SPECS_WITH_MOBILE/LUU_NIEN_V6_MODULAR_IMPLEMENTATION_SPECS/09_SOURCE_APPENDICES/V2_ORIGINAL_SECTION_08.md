# V2 original archival technical chapter — SECTION_08

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 8. RELATIONAL DATA CONTRACTS — DB ĐÍCH

### 8.1 Nguyên tắc schema

- UUID primary keys, unique business identifiers, `created_at/updated_at`, `status`, `version`, soft withdrawal khi yêu cầu audit.
- Core reused: `historical_entities`, `historical_sources`, `historical_claims`, `historical_claim_sources`; mở rộng bằng migration additive.
- `content_scope` là domain guard bắt buộc, nhưng không thay được RBAC/row-level ownership.
- Timezone UTC storage, UI địa phương; `valid_time` khác `system_time` (bitemporal cho dữ kiện lịch sử quan trọng).
- Files/rights không bỏ trong free-text JSON duy nhất; có tables and unique constraints.
- Mọi export public có schema version và data dictionary.

### 8.2 Bảng core/mở rộng và constraints

| Table | Columns tối thiểu | Unique/FK/index | Kiểm tra nghiệp vụ |
|---|---|---|---|
| `heritage_collections` | `id,slug,type,title_vi,title_en,registry_type,registry_ref,status` | unique(slug) | UNESCO category đúng |
| `heritage_urns` | `id,collection_id,canonical_code,name_vi,display_order,status` | FK, unique(code) | đúng 9 canonical |
| `heritage_motifs` | `id,urn_id,canonical_code,legacy_id,theme,position,identification_status` | FK, unique(code), index urn | đúng 162 verified trước release |
| `motif_names` | `motif_id,lang,script,transcription,review_state,reviewer_id` | composite unique | chữ Hán có reviewer |
| `historical_claims` | reuse existing | existing + indexes | nguồn và trạng thái |
| `historical_claim_sources` | reuse existing | unique(claim_id,source_id,role,locator) | locator non-empty for published |
| `asset_versions` | `asset_id,sha256,mime,size,version,license,proof_ref,geo_accuracy` | unique(hash,version) | provenance verified |
| `media_hotspots` | `motif_id,asset_version_id,mesh_anchor,confidence` | FK unique(motif,asset,anchor) | only validated hotspot public |
| `content_rights_grants` | `subject_id,subject_type,granted_by,scope,proof_uri,status,expiry` | index subject,status | withdraw audit |
| `learning_objects` | `id,entity_id,title,objective,version,status,author_id` | composite unique(object,version) | complete lesson spec |
| `ello_claim_bindings` | `ello_version_id,claim_id,source_packet_role` | FKs | only approved claims |
| `source_packets` | `id,ello_version_id,annotation,source_set_hash` | unique(ello,version) | exact frozen sources |
| `inquiry_tasks` | `id,ello_version_id,task_type,prompt,answer_format,rubric_id` | FKs | task aligns objective |
| `rubrics` | `id,version,criteria_json,validated_status` | unique(id,version) | 0–10 rubric manual |
| `lesson_assignments` | `id,class_id,ello_version_id,opens_at,closes_at` | indexes | frozen version |
| `inquiry_attempts` | `id,student_id,assignment_id,status,started_at,submitted_at` | composite school scope | access own work |
| `attempt_steps` | `attempt_id,step_type,payload_json,source_ids,version` | FK, index attempt | observation vs inference |
| `student_submissions` | `id,attempt_id,version,answer_text,evidence_refs` | unique(attempt,version) | immutable submitted attempts |
| `rubric_scores` | `submission_id,rubric_version,criterion_id,score,grader_id` | unique(submission,criterion,grader) | blinded scoring support |
| `feedback_revisions` | `submission_id,parent_version,new_version,feedback_id` | FK | preserve changes |
| `research_studies` | `id,protocol_version,ethics_ref,sampling_frame,study_status` | unique(protocol) | research isolation |
| `research_questionnaires` | `study_id,form_version,question_key,wording,choice_mode` | unique(study,version,key) | original wording |
| `research_participants` | `study_id,pseudonym,school_code,grade,consent_status` | unique(study,pseudonym) | no email/public |
| `research_responses` | `participant_token,question_key,choice_code,responded_at` | FK/index | multiple choice separate rows |
| `research_aggregates` | `study_id,item_key,category,n,N,percent,script_hash` | unique(study,item,category,revision) | replicable count |
| `ai_evaluation_runs` | `corpus_version,model_id,prompt_version,benchmark_id,metrics` | unique(run id) | evaluated not declared |
| `data_import_batches` | `sha256,source_uri,parser_version,imported_at,errors,status` | hash unique | idempotency |
| `editorial_decisions` | `entity_id,claim_id,reviewer_id,decision,reason,timestamp` | index claim,decision | trace human |
| `security_audit_events` | `actor_id,action,target,correlation_id,redacted_payload_hash` | restricted append only | no raw PII |

### 8.3 Ví dụ migration SQL — CHỈ LÀ THIẾT KẾ (không chạy vào production)

```sql
CREATE TABLE IF NOT EXISTS heritage_motifs (
  id UUID PRIMARY KEY,
  urn_id UUID NOT NULL REFERENCES heritage_urns(id),
  canonical_code TEXT NOT NULL UNIQUE,
  legacy_id TEXT,
  identification_status TEXT NOT NULL DEFAULT 'candidate',
  theme_code TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (identification_status IN ('candidate','source_backed','expert_verified','published','withdrawn'))
);
CREATE INDEX IF NOT EXISTS idx_motif_urn ON heritage_motifs(urn_id);

CREATE TABLE IF NOT EXISTS learning_objects (
  id UUID NOT NULL,
  version INTEGER NOT NULL CHECK (version > 0),
  heritage_entity_id UUID NOT NULL REFERENCES historical_entities(id),
  title_vi TEXT NOT NULL,
  status TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (id,version),
  CHECK(status IN ('draft','source_check','reviewed','published','withdrawn'))
);
```

**Migration gate:** review schema compatibility với SQLAlchemy hiện tại và Rust SQLx, nhất là enum text, PostgreSQL constraints và version semantics. Schema trên không giải quyết trực tiếp 26 heads; phải làm trước.

---

