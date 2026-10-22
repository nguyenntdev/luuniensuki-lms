# P09: TEN HISTORICAL RESEARCH AGENT PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.A.P09`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V4.A.P09 — Human editorial prep and signoff

**Mục tiêu chung:** Prepare review packet and record authenticated human decisions. **Input package:** `P08 resolved QA, rights report`. **Output reducer:** `editorial_review/v1`. **Blocking gate:** Agents cannot forge approvals.

**Quy tắc 10-concurrent:** coordinator tạo `A01..A10` trong một wave, `input_manifest_sha256` giống nhau, kích hoạt qua worker độc lập và quan sát running overlap; thu 10 envelopes trước reduce. Tác vụ có thể trả `NO_EVIDENCE` khi phù hợp, không được invent tài liệu để đủ số lượng.

### Agent `P09-A01` — Historical expert packet preparer

**Assignment cụ thể:** Tạo bản đối chiếu câu–nguồn cho sử gia.

**Input bắt buộc:** immutable manifest `P08 resolved QA, rights report` với `run_id`, `phase=P09`, `wave`, `agent_index=1`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/approvals.py [TARGET];backend/deps.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``historian_packet.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `1` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tạo bản đối chiếu câu–nguồn cho sử gia” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Bỏ câu nhiều nguồn bất đồng**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Bỏ câu nhiều nguồn bất đồng` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P09: Agents cannot forge approvals.

**Gemini prompt fragment:** `Bạn đóng vai P09-A01 (Historical expert packet preparer). Chỉ làm Tạo bản đối chiếu câu–nguồn cho sử gia. Xuất `historian_packet.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Bỏ câu nhiều nguồn bất đồng.`

### Agent `P09-A02` — Han-Nom expert packet preparer

**Assignment cụ thể:** Tạo crop, bản chép, dị bản, điểm nghi vấn.

**Input bắt buộc:** immutable manifest `P08 resolved QA, rights report` với `run_id`, `phase=P09`, `wave`, `agent_index=2`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/approvals.py [TARGET];backend/deps.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``hannom_packet.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `2` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tạo crop, bản chép, dị bản, điểm nghi vấn” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Ép chuyên gia duyệt khi chưa nhìn scan**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Ép chuyên gia duyệt khi chưa nhìn scan` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P09: Agents cannot forge approvals.

**Gemini prompt fragment:** `Bạn đóng vai P09-A02 (Han-Nom expert packet preparer). Chỉ làm Tạo crop, bản chép, dị bản, điểm nghi vấn. Xuất `hannom_packet.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Ép chuyên gia duyệt khi chưa nhìn scan.`

### Agent `P09-A03` — Museum/heritage curator packet preparer

**Assignment cụ thể:** Chuẩn hóa tên và tính hợp lệ mô tả hiện vật.

**Input bắt buộc:** immutable manifest `P08 resolved QA, rights report` với `run_id`, `phase=P09`, `wave`, `agent_index=3`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/approvals.py [TARGET];backend/deps.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``curator_packet.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `3` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Chuẩn hóa tên và tính hợp lệ mô tả hiện vật” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Tên sáng tác thay tên catalog**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Tên sáng tác thay tên catalog` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P09: Agents cannot forge approvals.

**Gemini prompt fragment:** `Bạn đóng vai P09-A03 (Museum/heritage curator packet preparer). Chỉ làm Chuẩn hóa tên và tính hợp lệ mô tả hiện vật. Xuất `curator_packet.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Tên sáng tác thay tên catalog.`

### Agent `P09-A04` — Translation reviewer packet preparer

**Assignment cụ thể:** Liệt kê chỗ song ngữ lệch hoặc có ngữ nghĩa yếu.

**Input bắt buộc:** immutable manifest `P08 resolved QA, rights report` với `run_id`, `phase=P09`, `wave`, `agent_index=4`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/approvals.py [TARGET];backend/deps.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``translation_packet.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `4` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Liệt kê chỗ song ngữ lệch hoặc có ngữ nghĩa yếu” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Khẳng định dịch đúng không có người duyệt**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Khẳng định dịch đúng không có người duyệt` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P09: Agents cannot forge approvals.

**Gemini prompt fragment:** `Bạn đóng vai P09-A04 (Translation reviewer packet preparer). Chỉ làm Liệt kê chỗ song ngữ lệch hoặc có ngữ nghĩa yếu. Xuất `translation_packet.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Khẳng định dịch đúng không có người duyệt.`

### Agent `P09-A05` — Legal/permissions packet preparer

**Assignment cụ thể:** Tổng hợp nguồn và quyền cho từng loại khai thác.

**Input bắt buộc:** immutable manifest `P08 resolved QA, rights report` với `run_id`, `phase=P09`, `wave`, `agent_index=5`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/approvals.py [TARGET];backend/deps.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``rights_packet.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `5` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tổng hợp nguồn và quyền cho từng loại khai thác” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **License hết hạn vẫn public**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `License hết hạn vẫn public` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P09: Agents cannot forge approvals.

**Gemini prompt fragment:** `Bạn đóng vai P09-A05 (Legal/permissions packet preparer). Chỉ làm Tổng hợp nguồn và quyền cho từng loại khai thác. Xuất `rights_packet.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: License hết hạn vẫn public.`

### Agent `P09-A06` — Teacher reviewer packet preparer

**Assignment cụ thể:** Soạn preview 2D/ELLO/rubric để giáo viên nhận xét.

**Input bắt buộc:** immutable manifest `P08 resolved QA, rights report` với `run_id`, `phase=P09`, `wave`, `agent_index=6`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/approvals.py [TARGET];backend/deps.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``teacher_packet.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `6` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Soạn preview 2D/ELLO/rubric để giáo viên nhận xét” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Một cuộc duyệt dùng cho mọi khối lớp**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Một cuộc duyệt dùng cho mọi khối lớp` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P09: Agents cannot forge approvals.

**Gemini prompt fragment:** `Bạn đóng vai P09-A06 (Teacher reviewer packet preparer). Chỉ làm Soạn preview 2D/ELLO/rubric để giáo viên nhận xét. Xuất `teacher_packet.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Một cuộc duyệt dùng cho mọi khối lớp.`

### Agent `P09-A07` — Accessibility reviewer packet preparer

**Assignment cụ thể:** Đưa WCAG checklist/caption/alt/fallback.

**Input bắt buộc:** immutable manifest `P08 resolved QA, rights report` với `run_id`, `phase=P09`, `wave`, `agent_index=7`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/approvals.py [TARGET];backend/deps.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``a11y_packet.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `7` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Đưa WCAG checklist/caption/alt/fallback” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **A11y chỉ do AI tự chứng nhận**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `A11y chỉ do AI tự chứng nhận` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P09: Agents cannot forge approvals.

**Gemini prompt fragment:** `Bạn đóng vai P09-A07 (Accessibility reviewer packet preparer). Chỉ làm Đưa WCAG checklist/caption/alt/fallback. Xuất `a11y_packet.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: A11y chỉ do AI tự chứng nhận.`

### Agent `P09-A08` — Research integrity packet preparer

**Assignment cụ thể:** Đối chiếu claim khoa học, provenance, reused data.

**Input bắt buộc:** immutable manifest `P08 resolved QA, rights report` với `run_id`, `phase=P09`, `wave`, `agent_index=8`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/approvals.py [TARGET];backend/deps.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``research_packet.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `8` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Đối chiếu claim khoa học, provenance, reused data” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Khẳng định khảo sát đo learning gains**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Khẳng định khảo sát đo learning gains` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P09: Agents cannot forge approvals.

**Gemini prompt fragment:** `Bạn đóng vai P09-A08 (Research integrity packet preparer). Chỉ làm Đối chiếu claim khoa học, provenance, reused data. Xuất `research_packet.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Khẳng định khảo sát đo learning gains.`

### Agent `P09-A09` — Editorial conflicts coordinator

**Assignment cụ thể:** Tạo diff/suggestion, xung đột nguồn cần adjudication.

**Input bắt buộc:** immutable manifest `P08 resolved QA, rights report` với `run_id`, `phase=P09`, `wave`, `agent_index=9`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/approvals.py [TARGET];backend/deps.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``reconciliation_packet.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `9` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tạo diff/suggestion, xung đột nguồn cần adjudication” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Agent tự resolve tranh chấp**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Agent tự resolve tranh chấp` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P09: Agents cannot forge approvals.

**Gemini prompt fragment:** `Bạn đóng vai P09-A09 (Editorial conflicts coordinator). Chỉ làm Tạo diff/suggestion, xung đột nguồn cần adjudication. Xuất `reconciliation_packet.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Agent tự resolve tranh chấp.`

### Agent `P09-A10` — Human-signoff verifier

**Assignment cụ thể:** Kiểm chữ ký của reviewer thật qua IAM, 4-eyes rule.

**Input bắt buộc:** immutable manifest `P08 resolved QA, rights report` với `run_id`, `phase=P09`, `wave`, `agent_index=10`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/approvals.py [TARGET];backend/deps.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``human_gate.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `10` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Kiểm chữ ký của reviewer thật qua IAM, 4-eyes rule” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **AI impersonate reviewer hoặc approve chính mình**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `AI impersonate reviewer hoặc approve chính mình` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P09: Agents cannot forge approvals.

**Gemini prompt fragment:** `Bạn đóng vai P09-A10 (Human-signoff verifier). Chỉ làm Kiểm chữ ký của reviewer thật qua IAM, 4-eyes rule. Xuất `human_gate.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: AI impersonate reviewer hoặc approve chính mình.`

**Phase reducer bắt buộc:** xác nhận 10/10 slot terminal, artifact hash hợp lệ, provenance complete, policy fail-closed, reducer deterministic, `observed_in_flight_peak` đo thực. Khi failure/uncertain, trạng thái `GATE_BLOCKED`, không khởi chạy phase sau.

