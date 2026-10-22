# V5.7 — HERITAGE_162_RECORDS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.7`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.7 — HOÀN THIỆN 162 BẢN ĐÚC NỔI VÀ KHO DI SẢN CÓ THỂ CÔNG BỐ

### 7.1. Việc bắt buộc làm trước khi gọi 162 bài là hoàn chỉnh

`data/05_Data_CaoDinh.json` ... `data/13_Data_HuyenDinh.json` chứa tổng cộng 162 records. Mỗi record hiện có `is_ai_generated=true`; nhiều trường văn xuôi như `description_educational`, `historical_context`, `symbolism`, `fun_fact`, `quiz_questions`, `name_han_nom`, `3d_mesh_id`. Một `3d_mesh_id` là **tham chiếu ý định**, không xác nhận asset GLB/GLTF tồn tại, không xác nhận hình học mô tả đúng motif hoặc quyền sử dụng. `name_han_nom` có thể có ký tự cần kiểm tra từng bản, tuyệt đối không tự sửa bằng suy đoán Unicode.

### 7.2. Data contract mỗi object

```yaml
object_id: "urn_cao_dinh_02"              # target canonical id; validate mapping
urn_id: "cao-dinh"
relief_sequence: 2
object_type: "relief"
name_vi: "..."
name_en: "..."
original_script:
  text: "..."
  transcription_method: human_verified
  reviewer_id: "<real-editor-id>"
  confidence: reviewed
content_status: approved_for_publication
historical_claims:
  - claim_id: "<uuid>"
    statement: "..."
    epistemic_status: documented
    source_bindings:
      - source_id: "<uuid>"
        edition: "..."
        locator: "volume/page/plate"
        excerpt_rights: "citation_only"
        support_relation: supports
media:
  - asset_id: "<uuid>"
    kind: image
    rights_status: approved
    checksum: "sha256:..."
    alt_text_vi: "..."
  - asset_id: "<uuid>"
    kind: glb
    geometry_review: verified
    fallback_image_asset_id: "<uuid>"
learning:
  observed_features: ["..."]
  evidence_question: "..."
  rubric_version: "1.0"
review:
  historical_editor_id: "<uuid>"
  rights_editor_id: "<uuid>"
  approved_at: "<timestamp>"
  published_revision: 1
```

### 7.3. 162-stage ingestion protocol

1. Backup nguồn ZIP + checksum file gốc; import vào staging only, không public.
2. Validate count 9 urns × 18 records; duplicate id, missing names, images path, invalid ranges, inconsistent urn id; xuất `catalog_audit.csv` nội bộ (được xuất qua CLI, không đặt trong repo với PII).
3. Create canonical object id, map legacy id, attach media checksum; không thay file seed làm nguồn chân lý khi DB đã là canonical.
4. Normalize original script, log nghi vấn Hán–Nôm per object; assign reviewer; không tự chọn chữ nếu không có ảnh chụp inscription đủ phân giải.
5. Split every paragraph into atomic historical claims (quan sát/nguồn văn bản/suy luận/tranh luận/chưa xác minh). A single paragraph may need multiple sources or conflicting readings.
6. Link bibliographic source edition + locator, allowed excerpt, digitisation provenance and rights decision.
7. Run AI drafts through V4 P00–P11 with 10 real concurrent jobs per phase; AI never writes approved revision.
8. Human expert reviews all externally published claims; teacher checks activities and grades; owner approves image/model rights.
9. Publish only approved subset, not necessarily all 162 simultaneously; release page shows coverage dashboard.
10. After publication, schedule controlled re-review on source change/conflict, revoke rights, version old content and invalidate caches.

### 7.4. Coverage matrix và release numbers

For each of 162 objects, track 18 boolean/enum fields: `record_exists`, `source_exists`, `page_locator`, `name_verified`, `han_nom_verified_or_NA`, `image_rights`, `model3d_exists`, `model3d_rights`, `geometry_verified`, `alt_text`, `translation_vi`, `translation_en`, `historical_claims_reviewed`, `conflicts_resolved_or_flagged`, `quiz_reviewed`, `learning_object_reviewed`, `published`, `last_reviewed_at`. Compute numerical coverage from actual DB, report denominator and exclusions. **Claim "162 fully documented" only when appropriate fields truly pass.** If 162 images verified but 4 models missing, disclose `3D coverage=158/162`, not 162/162.

### 7.5. Copyright/AI policy

Do not scrape copyrighted books indiscriminately. Respect robots/access and terms; no bypass paywalls/captcha; restricted scans go into permission workflow. Store metadata+locator where excerpt reuse unavailable. Content involving living traditions needs practitioner/community permission and ability to withdraw. Publication must indicate which parts are restoration, interpretation, translation, or verified primary observation.

