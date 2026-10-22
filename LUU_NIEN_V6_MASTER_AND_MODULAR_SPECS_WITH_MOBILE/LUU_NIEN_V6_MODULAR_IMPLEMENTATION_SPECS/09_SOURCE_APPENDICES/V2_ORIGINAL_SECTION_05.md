# V2 original archival technical chapter — SECTION_05

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 5. KNOWLEDGE MODEL: 9 URNS, 162 MOTIFS, HERITAGE, EVIDENCE

### 5.1 Chính sách canonical identity

- `heritage_collection`: slug `cuu-dinh`, collection scope, UNESCO register reference (đừng gộp hai loại danh hiệu UNESCO).
- `urn`: 9 bản ghi chính xác theo kiểm kê chuẩn; mỗi `urn_id` UUID bất biến + `canonical_code` (VD `URN-CAO`).
- `motif`: exactly 162 bản ghi **sau khi đối chiếu danh mục chuẩn**; canonical ID kiểu `MOTIF-URN-CAO-001` với mapping provenance; `urn_id` FK; vị trí `(panel, orientation, row, order)` khi nguồn cho phép.
- `motif_image`: ảnh chụp scan raw/curated/version; SHA, photographer, rights, crop mapping, source file.
- `script_label`: chữ Hán nguyên văn, phiên âm Hán Việt, Quốc ngữ, English gloss, dịch thuật và người kiểm chứng (không tự động đồng nhất chữ Nôm với Hán).
- `claim`: tách nhìn thấy, phiên âm, niên đại, địa danh, biểu tượng, suy luận, phục dựng; confidence + epistemic label.
- `source`: bibliographic authority, edition/volume/page/folio, archive URL, rights/license, date accessed, ISBN/DOI nếu có.
- `claim_source`: binding role `supports/challenges/contextualizes`, page locator, quoted span ngắn đúng quyền, reviewer confidence.
- `historical_period`, `place`, `person`, `event`, `relation`: nguồn gốc + validity-time + uncertainty.
- `translation`: field-level reviewed VI/EN/Hán; fallback không đánh lừa là bản dịch đã duyệt.

### 5.2 Mẫu record nguồn–hiện vật–học liệu (YAML chuẩn đích)

```yaml
schema_version: '1.0'
collection_id: 'cuu-dinh'
urn:
  canonical_id: 'URN-CAO'
  verified_name_vi: null    # MUST verify before publish
motif:
  canonical_id: 'MOTIF-URN-CAO-001'
  legacy_ids: ['urn_cao_dinh_01']
  identification_status: 'candidate'
  name_vi: null
  han_glyph: null
  han_review_status: 'unreviewed'
  relief_index_verified: false
  media_asset_ids: []
claims:
  - claim_key: 'IDENTITY-001'
    kind: 'identification'
    statement_vi: null
    certainty: 'unreviewed'
    source_bindings: []
    publishable: false
lessons: []
review:
  original_import: 'data/05_Data_CaoDinh.json'
  ai_seed: true
  historians: []
  editorial_status: 'quarantined'
```

### 5.3 Pipeline kiểm dữ liệu 162: ETL + adjudication

`ingest → checksum/deduplicate → parse → normalize identifiers → compare authority inventory → align photo → language/epigraphy review → separate claims → attach sources → rights review → subject review → publish → versioning`.

**Bắt buộc phân loại:** `AI_DRAFT`, `HUMAN_DRAFT`, `SOURCE_ATTACHED`, `EDITOR_REVIEWED`, `EXPERT_VERIFIED`, `PUBLISHED`, `DISPUTED`, `WITHDRAWN`. `is_ai_generated=true` không tự động là sai, nhưng **không đủ làm sự thật published**. Claim “N” khi chưa thấy nguồn phải bị chặn bởi API hiển thị lịch sử, AI RAG và quiz assessment.

### 5.4 Chỉ số kiểm kê dữ liệu bắt buộc

| Metric | Baseline ZIP | Release gate |
|---|---:|---|
| Số item JSON theo 9 file | 162 | 162/162 đã *reconciled* với authority catalog |
| Ảnh JPG gốc | 162 | mapping 162/162 đến motif verified, rights + checksum |
| Item có cờ AI-generated | 162/162 | mọi mục AI-draft được duyệt trước public |
| Item có `source(s)/bibliography/source_url` trực tiếp | 0/162 | published claim 100% có claim–source binding |
| Item có quiz questions | 162/162 | published quiz 100% link answer evidence/rubric |
| Hán/Nôm không rỗng | 158/162 | 162/162 có status rõ; thiếu được ghi null, không sáng tác |
| Canonical motif count | 162 item chưa đối chiếu | 162 verified relief entities, không trộn nhãn urn |
| 3D hiện có | Cao Đỉnh GLB LOD variants | không bắt buộc 9 GLB nếu 2D fallback đủ, nhưng label rõ coverage |

### 5.5 Quy trình đối chiếu tri thức

- Hai vòng: editor di sản sàng lọc, reviewer sử học/phiên âm độc lập ký duyệt.
- Mỗi claim giữ raw text, normalized text, source locator, evidence grade, revision history.
- Khi hai nguồn mâu thuẫn: ghi song song, không ép thành “một fact”; hiển thị phương pháp chọn nguồn.
- UNESCO: phân biệt đăng ký 162 bản đúc nổi vào *Memory of the World Asia-Pacific Regional Register 2024* với danh hiệu *Complex of Huế Monuments* của World Heritage; model phải có `registry_type`, `inscription_date`, `official_designation`, `register_identifier`, `source_url`.
- 9 urn / 162 motif: verify physical relationships từ hồ sơ gốc, không dùng tổng số trong JSON làm căn cứ duy nhất.
- Hán tự: thêm `han_unicode_verified`, `paleographic_image_ref`, `reading_vi_reviewed`, `translation_status`; không tự dịch tên bằng máy cho nội dung high-stakes historical.

---

