# P07: TEN HISTORICAL RESEARCH AGENT PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.A.P07`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V4.A.P07 — Full VI/EN educational drafting

**Mục tiêu chung:** Generate structured text, captions, scripts and teaching tasks. **Input package:** `P06 approved dossier; license scope`. **Output reducer:** `full_content_drafts/v1`. **Blocking gate:** Do not create new facts absent from dossier.

**Quy tắc 10-concurrent:** coordinator tạo `A01..A10` trong một wave, `input_manifest_sha256` giống nhau, kích hoạt qua worker độc lập và quan sát running overlap; thu 10 envelopes trước reduce. Tác vụ có thể trả `NO_EVIDENCE` khi phù hợp, không được invent tài liệu để đủ số lượng.

### Agent `P07-A01` — Vietnamese long-form historian writer

**Assignment cụ thể:** Viết bài đầy đủ tiếng Việt 1.500–3.000 từ tùy đủ chứng cứ.

**Input bắt buộc:** immutable manifest `P06 approved dossier; license scope` với `run_id`, `phase=P07`, `wave`, `agent_index=1`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/writers.py [TARGET];backend/routers/history_learning.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``article_vi_full.md` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `1` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Viết bài đầy đủ tiếng Việt 1.500–3.000 từ tùy đủ chứng cứ” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Đoạn dài mới không có claim id**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Đoạn dài mới không có claim id` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P07: Do not create new facts absent from dossier.

**Gemini prompt fragment:** `Bạn đóng vai P07-A01 (Vietnamese long-form historian writer). Chỉ làm Viết bài đầy đủ tiếng Việt 1.500–3.000 từ tùy đủ chứng cứ. Xuất `article_vi_full.md` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Đoạn dài mới không có claim id.`

### Agent `P07-A02` — English historical writer

**Assignment cụ thể:** Viết bài tiếng Anh dựa trên dossier; không dịch mù.

**Input bắt buộc:** immutable manifest `P06 approved dossier; license scope` với `run_id`, `phase=P07`, `wave`, `agent_index=2`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/writers.py [TARGET];backend/routers/history_learning.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``article_en_full.md` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `2` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Viết bài tiếng Anh dựa trên dossier; không dịch mù” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Dịch sai tính chưa chắc chắn**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Dịch sai tính chưa chắc chắn` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P07: Do not create new facts absent from dossier.

**Gemini prompt fragment:** `Bạn đóng vai P07-A02 (English historical writer). Chỉ làm Viết bài tiếng Anh dựa trên dossier; không dịch mù. Xuất `article_en_full.md` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Dịch sai tính chưa chắc chắn.`

### Agent `P07-A03` — Short museum label writer

**Assignment cụ thể:** Viết 80–150 từ bản nhãn trưng bày có định danh.

**Input bắt buộc:** immutable manifest `P06 approved dossier; license scope` với `run_id`, `phase=P07`, `wave`, `agent_index=3`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/writers.py [TARGET];backend/routers/history_learning.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``museum_label_vi_en.md` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `3` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Viết 80–150 từ bản nhãn trưng bày có định danh” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Nhãn khẳng định giả thuyết là sự thật**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Nhãn khẳng định giả thuyết là sự thật` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P07: Do not create new facts absent from dossier.

**Gemini prompt fragment:** `Bạn đóng vai P07-A03 (Short museum label writer). Chỉ làm Viết 80–150 từ bản nhãn trưng bày có định danh. Xuất `museum_label_vi_en.md` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Nhãn khẳng định giả thuyết là sự thật.`

### Agent `P07-A04` — Han-Nom editorial note writer

**Assignment cụ thể:** Viết mục nguyên văn/phiên âm/dịch nghĩa gắn phiên bản.

**Input bắt buộc:** immutable manifest `P06 approved dossier; license scope` với `run_id`, `phase=P07`, `wave`, `agent_index=4`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/writers.py [TARGET];backend/routers/history_learning.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``hannom_editorial.md` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `4` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Viết mục nguyên văn/phiên âm/dịch nghĩa gắn phiên bản” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Tự sinh glyph chưa được duyệt**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Tự sinh glyph chưa được duyệt` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P07: Do not create new facts absent from dossier.

**Gemini prompt fragment:** `Bạn đóng vai P07-A04 (Han-Nom editorial note writer). Chỉ làm Viết mục nguyên văn/phiên âm/dịch nghĩa gắn phiên bản. Xuất `hannom_editorial.md` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Tự sinh glyph chưa được duyệt.`

### Agent `P07-A05` — 3D/AR narration writer

**Assignment cụ thể:** Tạo chú giải hotspot/tường thuật âm thanh/caption.

**Input bắt buộc:** immutable manifest `P06 approved dossier; license scope` với `run_id`, `phase=P07`, `wave`, `agent_index=5`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/writers.py [TARGET];backend/routers/history_learning.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``interactive_script.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `5` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tạo chú giải hotspot/tường thuật âm thanh/caption” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Hotspot gắn sai bề mặt**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Hotspot gắn sai bề mặt` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P07: Do not create new facts absent from dossier.

**Gemini prompt fragment:** `Bạn đóng vai P07-A05 (3D/AR narration writer). Chỉ làm Tạo chú giải hotspot/tường thuật âm thanh/caption. Xuất `interactive_script.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Hotspot gắn sai bề mặt.`

### Agent `P07-A06` — Timeline/map article writer

**Assignment cụ thể:** Viết mô tả không gian-thời gian với provenance.

**Input bắt buộc:** immutable manifest `P06 approved dossier; license scope` với `run_id`, `phase=P07`, `wave`, `agent_index=6`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/writers.py [TARGET];backend/routers/history_learning.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``spacetime_blocks.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `6` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Viết mô tả không gian-thời gian với provenance” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Vẽ đường biên chính xác giả**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Vẽ đường biên chính xác giả` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P07: Do not create new facts absent from dossier.

**Gemini prompt fragment:** `Bạn đóng vai P07-A06 (Timeline/map article writer). Chỉ làm Viết mô tả không gian-thời gian với provenance. Xuất `spacetime_blocks.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Vẽ đường biên chính xác giả.`

### Agent `P07-A07` — Source-based ELLO lesson author

**Assignment cụ thể:** Viết 6-step inquiry, mục tiêu, tài liệu và nhiệm vụ.

**Input bắt buộc:** immutable manifest `P06 approved dossier; license scope` với `run_id`, `phase=P07`, `wave`, `agent_index=7`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/writers.py [TARGET];backend/routers/history_learning.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``ello_lesson.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `7` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Viết 6-step inquiry, mục tiêu, tài liệu và nhiệm vụ” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Nhiệm vụ không yêu cầu học sinh trích chứng cứ**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Nhiệm vụ không yêu cầu học sinh trích chứng cứ` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P07: Do not create new facts absent from dossier.

**Gemini prompt fragment:** `Bạn đóng vai P07-A07 (Source-based ELLO lesson author). Chỉ làm Viết 6-step inquiry, mục tiêu, tài liệu và nhiệm vụ. Xuất `ello_lesson.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Nhiệm vụ không yêu cầu học sinh trích chứng cứ.`

### Agent `P07-A08` — Assessment/rubric author

**Assignment cụ thể:** Sinh câu hỏi nguồn, đáp án, distractors, rubric feedback.

**Input bắt buộc:** immutable manifest `P06 approved dossier; license scope` với `run_id`, `phase=P07`, `wave`, `agent_index=8`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/writers.py [TARGET];backend/routers/history_learning.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``assessment_pack.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `8` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Sinh câu hỏi nguồn, đáp án, distractors, rubric feedback” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Quiz dựa trên claim disputed**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Quiz dựa trên claim disputed` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P07: Do not create new facts absent from dossier.

**Gemini prompt fragment:** `Bạn đóng vai P07-A08 (Assessment/rubric author). Chỉ làm Sinh câu hỏi nguồn, đáp án, distractors, rubric feedback. Xuất `assessment_pack.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Quiz dựa trên claim disputed.`

### Agent `P07-A09` — Accessibility and reading-level writer

**Assignment cụ thể:** Sinh 2D fallback, alt text, A11y và bản dễ đọc.

**Input bắt buộc:** immutable manifest `P06 approved dossier; license scope` với `run_id`, `phase=P07`, `wave`, `agent_index=9`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/writers.py [TARGET];backend/routers/history_learning.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``accessibility_pack.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `9` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Sinh 2D fallback, alt text, A11y và bản dễ đọc” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Alt text chứa phỏng đoán chưa kiểm**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Alt text chứa phỏng đoán chưa kiểm` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P07: Do not create new facts absent from dossier.

**Gemini prompt fragment:** `Bạn đóng vai P07-A09 (Accessibility and reading-level writer). Chỉ làm Sinh 2D fallback, alt text, A11y và bản dễ đọc. Xuất `accessibility_pack.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Alt text chứa phỏng đoán chưa kiểm.`

### Agent `P07-A10` — Citation editor and content assembler

**Assignment cụ thể:** Ghép 9 đầu ra, citations inline, bibliography, all gaps.

**Input bắt buộc:** immutable manifest `P06 approved dossier; license scope` với `run_id`, `phase=P07`, `wave`, `agent_index=10`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/writers.py [TARGET];backend/routers/history_learning.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``content_bundle_draft.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `10` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Ghép 9 đầu ra, citations inline, bibliography, all gaps” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Bản full bài không có nguồn cho section**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Bản full bài không có nguồn cho section` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P07: Do not create new facts absent from dossier.

**Gemini prompt fragment:** `Bạn đóng vai P07-A10 (Citation editor and content assembler). Chỉ làm Ghép 9 đầu ra, citations inline, bibliography, all gaps. Xuất `content_bundle_draft.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Bản full bài không có nguồn cho section.`

**Phase reducer bắt buộc:** xác nhận 10/10 slot terminal, artifact hash hợp lệ, provenance complete, policy fail-closed, reducer deterministic, `observed_in_flight_peak` đo thực. Khi failure/uncertain, trạng thái `GATE_BLOCKED`, không khởi chạy phase sau.

