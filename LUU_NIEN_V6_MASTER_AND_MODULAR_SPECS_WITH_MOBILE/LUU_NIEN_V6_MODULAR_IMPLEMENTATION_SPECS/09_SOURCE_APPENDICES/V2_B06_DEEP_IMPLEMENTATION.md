# V2 B6: source-derived engineering detail

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V2.B6`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## B6. CHUẨN HÓA TOÀN BỘ 162 BẢN GHI — IMPORT, SOURCE AUDIT, HUMAN REVIEW

### B6.1 Những con số đo trực tiếp từ ZIP (không được gộp với nguồn kiểm chứng bên ngoài)

- Chín JSON `data/05_Data_CaoDinh.json` đến `data/13_Data_HuyenDinh.json`, mỗi file 18 bản ghi, tổng **162**.
- **162/162** mang `is_ai_generated: true`; mô tả lịch sử, chữ Hán, biểu tượng, niên đại, “fun fact”, giải thích quiz phải xử lý như **bản nháp AI**, không xem là sử liệu đã duyệt.
- Field `source`, `sources`, `references` **0/162** trong nhóm JSON đó; không đồng nghĩa các phân hệ DB khác hoàn toàn thiếu nguồn.
- `name_han_nom` xuất hiện ở **158/162**, còn **4** thiếu/blank; giá trị đầu của 9 file đều là ký tự `艇` theo snapshot, đây là chỉ báo **cần kiểm chữ bằng đối chiếu thực địa**, không tự kết luận cách đọc/chữ gốc nào đúng.
- `name_vi`: 162/162 nhưng chỉ **161 chuỗi duy nhất**; một tên lặp có thể hợp lệ khi thuộc hai đỉnh, nên kiểm theo `(urn, motif)` chứ không dedupe toàn quốc bằng tên.
- `name_en`: 162/162 nhưng có **160 chuỗi duy nhất**; cần điều tra overlap và tên dịch do AI sinh.
- `3d_mesh_id`: 162/162 chuỗi khác nhau; hiện diện của chuỗi ID **không chứng minh** file GLB/hotspot tương ứng tồn tại.
- `thumbnail_url`: 162/162 có path; kiểm `url_decode`, path traversal, file tồn tại và quyền ảnh riêng.
- `quiz_questions`: 162/162 có trường câu hỏi; từng câu cần kiểm sự phụ thuộc vào claim đã duyệt và answer key.

### B6.2 Quy trình import 11 bước — không bỏ bước đánh giá học thuật

| Bước | Đầu vào | Xử lý | Đầu ra | Chặn phát hành khi |
|---|---|---|---|---|
| 01 freeze | 9 JSON + 162 JPG | hash manifest, preserve bytes | `source_snapshot.json` | không truy xuất được snapshot |
| 02 parse | raw JSON | JSON schema, encoding NFC, required fields | `parse_report` | sai schema/lỗi tệp |
| 03 classify | raw record | xác định record mô tả urn hay relief; kiểm ordinal | `identity_candidates` | ghép urn/relief không xác định |
| 04 canonicalize | candidates | normalize aliases, map 9 urn + motif | `entity_id_map` | 2 candidates conflict |
| 05 image map | JPG + thumbnail | basename/path -> asset hash -> candidate | `media_binding_proposals` | ảnh trùng/không xác định |
| 06 claim split | prose fields | chia mô tả quan sát, mệnh đề thực chứng, diễn giải, truyền thuyết | `claim_drafts` | xuất hiện claim không phân biệt |
| 07 source assignment | source register/sách/biên mục | gắn từng claim với locator | `source_bindings` | claim cần kiểm không có căn cứ |
| 08 historical review | claim+source | reviewer duyệt và ghi rationale | `review_decisions` | thiếu người duyệt hoặc xung đột |
| 09 media rights | asset+grants | policy check theo purpose | `asset_clearance` | unknown/expired/blocked |
| 10 pedagogical QA | quiz/ELLO | kiểm answer key, rubric, 2D fallback | `lesson_candidates` | prompt học sinh dựa trên claim sai |
| 11 release | approved content | immutable catalog release + smoke | `release_manifest` | checklist chưa pass |

### B6.3 Mẫu validation report mỗi bản ghi

```yaml
raw_id: urn_cao_dinh_01
raw_file: data/05_Data_CaoDinh.json
source_snapshot_sha256: TO_BE_FILLED_BY_PIPELINE
canonical_entity_id: null        # never invent before mapping
record_kind: unresolved          # urn|relief|other
identity_review: pending
han_nom_review: pending
names:
  vi: "Cao Đỉnh"
  han_nom_seed: "艇"               # unverified: copied from AI draft, not an authoritative correction
validation:
  parse: pass
  ai_generated: true
  has_bibliographic_source: false
  image_path_resolves: to_be_verified
  mesh_asset_resolves: to_be_verified
  rights_grant: unknown
  claim_review: blocked
  eligible_for_public_authority: false
issues:
  - code: MISSING_SOURCE_LOCATOR
    severity: blocker
  - code: HAN_NOM_NOT_VERIFIED
    severity: blocker
  - code: MESH_REFERENCE_UNVERIFIED
    severity: warning
review_owners:
  historian: unassigned
  rights_manager: unassigned
```

### B6.4 Quy tắc phân tách claim khỏi câu văn AI

Một trường `description_educational` có thể chứa nhiều mệnh đề: thời điểm đúc, hình tượng, quan hệ với một vị vua, ý nghĩa biểu tượng, vị trí và suy luận chính trị. Chia thành claim atomic theo câu có thể xác minh, không sao chép cả paragraph vào một claim duy nhất rồi ghi `verified=true`. Câu “đây là biểu tượng của …” có thể cần phân loại interpretation, không gán factual nếu nguồn chỉ phản ánh diễn giải hiện đại. Phải giữ source AI seed dưới `draft_origin_text` để thấy chỗ được sửa.

### B6.5 Quy tắc nguồn lịch sử và thẩm định

- **Primary**: bản đúc nổi/inscription, hồ sơ bảo tàng, chỉ dụ và bản chụp tư liệu; gắn bản phiên/ảnh có xuất xứ.
- **Secondary**: ấn phẩm nghiên cứu có tác giả, nhà xuất bản, trang; khi trích diễn giải phải ghi ai diễn giải.
- **Interpretation**: có thể chấp nhận nhiều quan điểm; không ép `true/false` khi chứng cứ chưa phân giải.
- **Hán–Nôm**: lưu `image_crop`, `transcription_original`, `transliteration`, `translation`, `reviewer`, `confidence`; bản chữ và bản dịch là hai sản phẩm khác nhau, version độc lập.
- **UNESCO**: xác nhận chính xác loại danh mục/khu vực ghi danh của bộ sưu tập; không tự suy ra UNESCO thẩm định tất cả diễn giải trong sản phẩm.
- **Source withdrawn**: giữ metadata audit, ngừng public excerpt/media nếu quyền hết hiệu lực, tái đánh giá các claim chỉ còn nguồn ấy.

### B6.6 Quy tắc phân biệt số lượng

`162 JSON rows ≠ 162 verified historical entities ≠ 162 cleared media ≠ 162 usable 3D meshes ≠ 162 evidence-linked lessons`. Dashboard phải hiện từng bộ đếm riêng với định nghĩa, thời điểm chốt, hash snapshot. Công khai danh sách trạng thái `raw / mapped / sourced / reviewed / published` để người đọc tránh hiểu “đầy đủ” theo nghĩa quá rộng.

### B6.7 Quản lý sản phẩm 3D và hotspot

Mỗi mesh phải có file tồn tại và hash; inspect GLB header/meshes/materials, mesh coordinate transformations, performance budget và version; hotspots map với IDs relief thật và phải test nằm trong bounds. Mỗi urn không nhất thiết có một GLB riêng khi dùng mô hình phân chia, nhưng quy tắc asset→urn→relief phải giải thích bằng manifest được kiểm. `3d_mesh_id` placeholder không tạo capability `has_3d=true`.

**Asset acceptance sample:**

```yaml
asset_id: UUID_FROM_IMPORT
entity_id: UUID_FROM_CANONICAL_CATALOG
kind: glb
storage_object_key: assets/urns/.../model.glb
content_sha256: MEASURE_AFTER_IMPORT
source_photo_session_id: null
source_license_id: null
accuracy: unreviewed
units: m
lod_profile: mobile
hotspots: []
rights_status: review_required
viewer_test: not_run
public_access: false
```

### B6.8 Kiểm thử pipeline import

TC-162-01: đúng 9 input groups x18 được report; nếu 17/19 báo mismatch. TC-162-02: duplicate `raw_id` fail; alias cùng tên giữa các urn không auto merge. TC-162-03: Unicode Hán Nôm không bị transliteration tự động. TC-162-04: thiếu image không chặn import draft nhưng chặn publish media claim. TC-162-05: missing source ngăn claim approved. TC-162-06: unknown rights không được public. TC-162-07: re-import cùng hash không nhân đôi record. TC-162-08: modified source tạo version mới và diff. TC-162-09: rollback release không mất audit. TC-162-10: quyền rút làm 3D/thumbnail khỏi public path và CDN sau thời gian SLA định nghĩa.

### B6.9 Dashboard quản trị dữ liệu di sản

Hiển thị lưới 9x18 với các cột trạng thái: entity type, canonical ID, raw JSON origin, media existence, rights cleared, source locator count, factual claims reviewed, disputed claims, Han-Nom verified, lesson ready, QA issue count. Click ô vào checklist/đường dẫn bằng chứng. Bulk approve bị cấm; bulk import/draft allowed có audit.

---

