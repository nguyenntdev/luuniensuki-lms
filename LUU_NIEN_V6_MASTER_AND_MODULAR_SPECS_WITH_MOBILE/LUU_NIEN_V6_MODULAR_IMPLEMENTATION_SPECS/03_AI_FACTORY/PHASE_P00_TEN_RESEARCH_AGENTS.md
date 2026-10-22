# P00: TEN HISTORICAL RESEARCH AGENT PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.A.P00`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V4.A.P00 — Research charter, identity and plan

**Mục tiêu chung:** Canonical 162 identities, scope, draft research questions, rights risk. **Input package:** `research_sources_seed, 9 urn identity registry`. **Output reducer:** `identity_catalog/v1`. **Blocking gate:** No duplicates, no inferred original characters, all 10 envelopes.

**Quy tắc 10-concurrent:** coordinator tạo `A01..A10` trong một wave, `input_manifest_sha256` giống nhau, kích hoạt qua worker độc lập và quan sát running overlap; thu 10 envelopes trước reduce. Tác vụ có thể trả `NO_EVIDENCE` khi phù hợp, không được invent tài liệu để đủ số lượng.

### Agent `P00-A01` — Inventory auditor

**Assignment cụ thể:** Xác định đúng 9 đỉnh × 18 phù điêu theo khóa chuẩn, phát hiện duplicate.

**Input bắt buộc:** immutable manifest `research_sources_seed, 9 urn identity registry` với `run_id`, `phase=P00`, `wave`, `agent_index=1`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `data/05_Data_CaoDinh.json;backend/history_models.py;scripts/history/validate_history_content.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``identity_inventory.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `1` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Xác định đúng 9 đỉnh × 18 phù điêu theo khóa chuẩn, phát hiện duplicate” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Trộn tên đỉnh với tên bản đúc**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Trộn tên đỉnh với tên bản đúc` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P00: No duplicates, no inferred original characters, all 10 envelopes.

**Gemini prompt fragment:** `Bạn đóng vai P00-A01 (Inventory auditor). Chỉ làm Xác định đúng 9 đỉnh × 18 phù điêu theo khóa chuẩn, phát hiện duplicate. Xuất `identity_inventory.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Trộn tên đỉnh với tên bản đúc.`

### Agent `P00-A02` — Scope owner

**Assignment cụ thể:** Định nghĩa scope `NINE_URNS` / `RBPC_HUE` / `CALL` và object linkage.

**Input bắt buộc:** immutable manifest `research_sources_seed, 9 urn identity registry` với `run_id`, `phase=P00`, `wave`, `agent_index=2`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `data/05_Data_CaoDinh.json;backend/history_models.py;scripts/history/validate_history_content.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``scope_plan.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `2` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Định nghĩa scope `NINE_URNS` / `RBPC_HUE` / `CALL` và object linkage” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Chạy cross-scope retrieval**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Chạy cross-scope retrieval` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P00: No duplicates, no inferred original characters, all 10 envelopes.

**Gemini prompt fragment:** `Bạn đóng vai P00-A02 (Scope owner). Chỉ làm Định nghĩa scope `NINE_URNS` / `RBPC_HUE` / `CALL` và object linkage. Xuất `scope_plan.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Chạy cross-scope retrieval.`

### Agent `P00-A03` — Question designer

**Assignment cụ thể:** Tạo research questions: nhận diện, xuất xứ, niên đại, ý nghĩa, nguồn.

**Input bắt buộc:** immutable manifest `research_sources_seed, 9 urn identity registry` với `run_id`, `phase=P00`, `wave`, `agent_index=3`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `data/05_Data_CaoDinh.json;backend/history_models.py;scripts/history/validate_history_content.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``question_bank_draft.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `3` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tạo research questions: nhận diện, xuất xứ, niên đại, ý nghĩa, nguồn” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Câu hỏi tiên định kết luận**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Câu hỏi tiên định kết luận` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P00: No duplicates, no inferred original characters, all 10 envelopes.

**Gemini prompt fragment:** `Bạn đóng vai P00-A03 (Question designer). Chỉ làm Tạo research questions: nhận diện, xuất xứ, niên đại, ý nghĩa, nguồn. Xuất `question_bank_draft.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Câu hỏi tiên định kết luận.`

### Agent `P00-A04` — Taxonomy specialist

**Assignment cụ thể:** Thiết lập taxonomy sông núi/động thực vật/địa danh/văn hóa.

**Input bắt buộc:** immutable manifest `research_sources_seed, 9 urn identity registry` với `run_id`, `phase=P00`, `wave`, `agent_index=4`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `data/05_Data_CaoDinh.json;backend/history_models.py;scripts/history/validate_history_content.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``taxonomy_candidates.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `4` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Thiết lập taxonomy sông núi/động thực vật/địa danh/văn hóa” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Gán taxonomy chỉ do suy đoán**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Gán taxonomy chỉ do suy đoán` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P00: No duplicates, no inferred original characters, all 10 envelopes.

**Gemini prompt fragment:** `Bạn đóng vai P00-A04 (Taxonomy specialist). Chỉ làm Thiết lập taxonomy sông núi/động thực vật/địa danh/văn hóa. Xuất `taxonomy_candidates.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Gán taxonomy chỉ do suy đoán.`

### Agent `P00-A05` — Han-Nom risk mapper

**Assignment cụ thể:** Đánh dấu mục chữ Hán–Nôm cần chuyên gia, đề nghị phương thức kiểm.

**Input bắt buộc:** immutable manifest `research_sources_seed, 9 urn identity registry` với `run_id`, `phase=P00`, `wave`, `agent_index=5`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `data/05_Data_CaoDinh.json;backend/history_models.py;scripts/history/validate_history_content.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``han_nom_queue.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `5` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Đánh dấu mục chữ Hán–Nôm cần chuyên gia, đề nghị phương thức kiểm” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Tự coi OCR là phiên âm chuẩn**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Tự coi OCR là phiên âm chuẩn` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P00: No duplicates, no inferred original characters, all 10 envelopes.

**Gemini prompt fragment:** `Bạn đóng vai P00-A05 (Han-Nom risk mapper). Chỉ làm Đánh dấu mục chữ Hán–Nôm cần chuyên gia, đề nghị phương thức kiểm. Xuất `han_nom_queue.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Tự coi OCR là phiên âm chuẩn.`

### Agent `P00-A06` — Geography risk mapper

**Assignment cụ thể:** Liệt kê tên xưa/nay, tọa độ cần đối chiếu, mức chính xác.

**Input bắt buộc:** immutable manifest `research_sources_seed, 9 urn identity registry` với `run_id`, `phase=P00`, `wave`, `agent_index=6`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `data/05_Data_CaoDinh.json;backend/history_models.py;scripts/history/validate_history_content.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``geography_risk.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `6` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Liệt kê tên xưa/nay, tọa độ cần đối chiếu, mức chính xác” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Map địa danh lịch sử thành tọa độ hiện đại chắc chắn**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Map địa danh lịch sử thành tọa độ hiện đại chắc chắn` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P00: No duplicates, no inferred original characters, all 10 envelopes.

**Gemini prompt fragment:** `Bạn đóng vai P00-A06 (Geography risk mapper). Chỉ làm Liệt kê tên xưa/nay, tọa độ cần đối chiếu, mức chính xác. Xuất `geography_risk.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Map địa danh lịch sử thành tọa độ hiện đại chắc chắn.`

### Agent `P00-A07` — Legal source planner

**Assignment cụ thể:** Gợi ý loại nguồn, yêu cầu quyền lưu trữ/trích dẫn theo nhóm.

**Input bắt buộc:** immutable manifest `research_sources_seed, 9 urn identity registry` với `run_id`, `phase=P00`, `wave`, `agent_index=7`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `data/05_Data_CaoDinh.json;backend/history_models.py;scripts/history/validate_history_content.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``rights_plan.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `7` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Gợi ý loại nguồn, yêu cầu quyền lưu trữ/trích dẫn theo nhóm” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Mặc nhiên tài liệu online là public domain**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Mặc nhiên tài liệu online là public domain` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P00: No duplicates, no inferred original characters, all 10 envelopes.

**Gemini prompt fragment:** `Bạn đóng vai P00-A07 (Legal source planner). Chỉ làm Gợi ý loại nguồn, yêu cầu quyền lưu trữ/trích dẫn theo nhóm. Xuất `rights_plan.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Mặc nhiên tài liệu online là public domain.`

### Agent `P00-A08` — Teaching objectives planner

**Assignment cụ thể:** Gắn mục tiêu Lịch sử–Địa lí–liên môn và khả năng đánh giá.

**Input bắt buộc:** immutable manifest `research_sources_seed, 9 urn identity registry` với `run_id`, `phase=P00`, `wave`, `agent_index=8`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `data/05_Data_CaoDinh.json;backend/history_models.py;scripts/history/validate_history_content.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``curriculum_targets.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `8` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Gắn mục tiêu Lịch sử–Địa lí–liên môn và khả năng đánh giá” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Gắn bài học chưa tồn tại là đã có**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Gắn bài học chưa tồn tại là đã có` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P00: No duplicates, no inferred original characters, all 10 envelopes.

**Gemini prompt fragment:** `Bạn đóng vai P00-A08 (Teaching objectives planner). Chỉ làm Gắn mục tiêu Lịch sử–Địa lí–liên môn và khả năng đánh giá. Xuất `curriculum_targets.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Gắn bài học chưa tồn tại là đã có.`

### Agent `P00-A09` — Coverage and cost estimator

**Assignment cụ thể:** Ước lượng số nguồn/candidate và token/requests cho mỗi đối tượng.

**Input bắt buộc:** immutable manifest `research_sources_seed, 9 urn identity registry` với `run_id`, `phase=P00`, `wave`, `agent_index=9`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `data/05_Data_CaoDinh.json;backend/history_models.py;scripts/history/validate_history_content.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``budget_and_coverage.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `9` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Ước lượng số nguồn/candidate và token/requests cho mỗi đối tượng” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Nhân 162×10 request vượt budget**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Nhân 162×10 request vượt budget` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P00: No duplicates, no inferred original characters, all 10 envelopes.

**Gemini prompt fragment:** `Bạn đóng vai P00-A09 (Coverage and cost estimator). Chỉ làm Ước lượng số nguồn/candidate và token/requests cho mỗi đối tượng. Xuất `budget_and_coverage.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Nhân 162×10 request vượt budget.`

### Agent `P00-A10` — Run-manifest verifier

**Assignment cụ thể:** Kiểm tra khóa, hash, config, version, provider quotas.

**Input bắt buộc:** immutable manifest `research_sources_seed, 9 urn identity registry` với `run_id`, `phase=P00`, `wave`, `agent_index=10`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `data/05_Data_CaoDinh.json;backend/history_models.py;scripts/history/validate_history_content.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``run_manifest.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `10` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Kiểm tra khóa, hash, config, version, provider quotas” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Không đủ inventory vẫn khởi động**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Không đủ inventory vẫn khởi động` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P00: No duplicates, no inferred original characters, all 10 envelopes.

**Gemini prompt fragment:** `Bạn đóng vai P00-A10 (Run-manifest verifier). Chỉ làm Kiểm tra khóa, hash, config, version, provider quotas. Xuất `run_manifest.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Không đủ inventory vẫn khởi động.`

**Phase reducer bắt buộc:** xác nhận 10/10 slot terminal, artifact hash hợp lệ, provenance complete, policy fail-closed, reducer deterministic, `observed_in_flight_peak` đo thực. Khi failure/uncertain, trạng thái `GATE_BLOCKED`, không khởi chạy phase sau.

