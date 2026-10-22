# P10: TEN HISTORICAL RESEARCH AGENT PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.A.P10`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V4.A.P10 — Release preflight, publish transaction

**Mục tiêu chung:** Build immutable signed release with atomic pointer. **Input package:** `P09 signoffs + version-locked content`. **Output reducer:** `release_candidate/v1`. **Blocking gate:** No partial publish / stale content.

**Quy tắc 10-concurrent:** coordinator tạo `A01..A10` trong một wave, `input_manifest_sha256` giống nhau, kích hoạt qua worker độc lập và quan sát running overlap; thu 10 envelopes trước reduce. Tác vụ có thể trả `NO_EVIDENCE` khi phù hợp, không được invent tài liệu để đủ số lượng.

### Agent `P10-A01` — Content release manifest builder

**Assignment cụ thể:** Đóng gói phiên bản VI/EN, hash và review proof.

**Input bắt buộc:** immutable manifest `P09 signoffs + version-locked content` với `run_id`, `phase=P10`, `wave`, `agent_index=1`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/publication.py [TARGET];backend/services/history_tutor.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``release_manifest.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `1` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Đóng gói phiên bản VI/EN, hash và review proof” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Phát hành bản nháp chưa duyệt**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Phát hành bản nháp chưa duyệt` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P10: No partial publish / stale content.

**Gemini prompt fragment:** `Bạn đóng vai P10-A01 (Content release manifest builder). Chỉ làm Đóng gói phiên bản VI/EN, hash và review proof. Xuất `release_manifest.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Phát hành bản nháp chưa duyệt.`

### Agent `P10-A02` — Relief encyclopedia exporter

**Assignment cụ thể:** Tạo API records tách language và section.

**Input bắt buộc:** immutable manifest `P09 signoffs + version-locked content` với `run_id`, `phase=P10`, `wave`, `agent_index=2`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/publication.py [TARGET];backend/services/history_tutor.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``relief_api_payloads.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `2` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tạo API records tách language và section” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Thay đổi slug phá link cũ**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Thay đổi slug phá link cũ` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P10: No partial publish / stale content.

**Gemini prompt fragment:** `Bạn đóng vai P10-A02 (Relief encyclopedia exporter). Chỉ làm Tạo API records tách language và section. Xuất `relief_api_payloads.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Thay đổi slug phá link cũ.`

### Agent `P10-A03` — Historical graph synchronizer

**Assignment cụ thể:** Upsert claim/source binding version mới, giữ revision.

**Input bắt buộc:** immutable manifest `P09 signoffs + version-locked content` với `run_id`, `phase=P10`, `wave`, `agent_index=3`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/publication.py [TARGET];backend/services/history_tutor.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``graph_diff.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `3` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Upsert claim/source binding version mới, giữ revision” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Ghi đè claim đã approved**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Ghi đè claim đã approved` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P10: No partial publish / stale content.

**Gemini prompt fragment:** `Bạn đóng vai P10-A03 (Historical graph synchronizer). Chỉ làm Upsert claim/source binding version mới, giữ revision. Xuất `graph_diff.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Ghi đè claim đã approved.`

### Agent `P10-A04` — LMS/ELLO packager

**Assignment cụ thể:** Đóng gói lesson và rubric được giáo viên duyệt.

**Input bắt buộc:** immutable manifest `P09 signoffs + version-locked content` với `run_id`, `phase=P10`, `wave`, `agent_index=4`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/publication.py [TARGET];backend/services/history_tutor.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``ello_release.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `4` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Đóng gói lesson và rubric được giáo viên duyệt” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Quiz sử dụng claim chưa verified**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Quiz sử dụng claim chưa verified` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P10: No partial publish / stale content.

**Gemini prompt fragment:** `Bạn đóng vai P10-A04 (LMS/ELLO packager). Chỉ làm Đóng gói lesson và rubric được giáo viên duyệt. Xuất `ello_release.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Quiz sử dụng claim chưa verified.`

### Agent `P10-A05` — Media/hotspot integrator

**Assignment cụ thể:** Liên kết 2D/3D/AR assets đúng rights và coordinates.

**Input bắt buộc:** immutable manifest `P09 signoffs + version-locked content` với `run_id`, `phase=P10`, `wave`, `agent_index=5`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/publication.py [TARGET];backend/services/history_tutor.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``media_release.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `5` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Liên kết 2D/3D/AR assets đúng rights và coordinates” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Asset unreviewed trở thành public**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Asset unreviewed trở thành public` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P10: No partial publish / stale content.

**Gemini prompt fragment:** `Bạn đóng vai P10-A05 (Media/hotspot integrator). Chỉ làm Liên kết 2D/3D/AR assets đúng rights và coordinates. Xuất `media_release.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Asset unreviewed trở thành public.`

### Agent `P10-A06` — Search/embedding index builder

**Assignment cụ thể:** Index public approved only, citation-aware chunks.

**Input bắt buộc:** immutable manifest `P09 signoffs + version-locked content` với `run_id`, `phase=P10`, `wave`, `agent_index=6`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/publication.py [TARGET];backend/services/history_tutor.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``search_index_manifest.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `6` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Index public approved only, citation-aware chunks” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Tìm kiếm trả draft**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Tìm kiếm trả draft` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P10: No partial publish / stale content.

**Gemini prompt fragment:** `Bạn đóng vai P10-A06 (Search/embedding index builder). Chỉ làm Index public approved only, citation-aware chunks. Xuất `search_index_manifest.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Tìm kiếm trả draft.`

### Agent `P10-A07` — History Tutor retrieval updater

**Assignment cụ thể:** Tạo retrieval release từ graph approved immutable.

**Input bắt buộc:** immutable manifest `P09 signoffs + version-locked content` với `run_id`, `phase=P10`, `wave`, `agent_index=7`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/publication.py [TARGET];backend/services/history_tutor.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``tutor_release.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `7` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tạo retrieval release từ graph approved immutable” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Answer dùng bản superseded**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Answer dùng bản superseded` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P10: No partial publish / stale content.

**Gemini prompt fragment:** `Bạn đóng vai P10-A07 (History Tutor retrieval updater). Chỉ làm Tạo retrieval release từ graph approved immutable. Xuất `tutor_release.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Answer dùng bản superseded.`

### Agent `P10-A08` — Accessibility build verifier

**Assignment cụ thể:** Kiểm bản song ngữ/caption/print/no-AR path.

**Input bắt buộc:** immutable manifest `P09 signoffs + version-locked content` với `run_id`, `phase=P10`, `wave`, `agent_index=8`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/publication.py [TARGET];backend/services/history_tutor.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``a11y_release.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `8` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Kiểm bản song ngữ/caption/print/no-AR path” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Không có đường 2D khi AR fail**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Không có đường 2D khi AR fail` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P10: No partial publish / stale content.

**Gemini prompt fragment:** `Bạn đóng vai P10-A08 (Accessibility build verifier). Chỉ làm Kiểm bản song ngữ/caption/print/no-AR path. Xuất `a11y_release.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Không có đường 2D khi AR fail.`

### Agent `P10-A09` — Export/API compatibility checker

**Assignment cụ thể:** JSON, HTML, markdown, BibTeX, OpenAPI contract.

**Input bắt buộc:** immutable manifest `P09 signoffs + version-locked content` với `run_id`, `phase=P10`, `wave`, `agent_index=9`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/publication.py [TARGET];backend/services/history_tutor.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``compatibility_release.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `9` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “JSON, HTML, markdown, BibTeX, OpenAPI contract” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Client nhận field mới breaking**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Client nhận field mới breaking` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P10: No partial publish / stale content.

**Gemini prompt fragment:** `Bạn đóng vai P10-A09 (Export/API compatibility checker). Chỉ làm JSON, HTML, markdown, BibTeX, OpenAPI contract. Xuất `compatibility_release.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Client nhận field mới breaking.`

### Agent `P10-A10` — Atomic publish coordinator

**Assignment cụ thể:** Kiểm đủ 9 artifact, signer, sha và swap release pointer.

**Input bắt buộc:** immutable manifest `P09 signoffs + version-locked content` với `run_id`, `phase=P10`, `wave`, `agent_index=10`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/publication.py [TARGET];backend/services/history_tutor.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``publication_transaction.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `10` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Kiểm đủ 9 artifact, signer, sha và swap release pointer” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Partial publish khi index fail**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Partial publish khi index fail` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P10: No partial publish / stale content.

**Gemini prompt fragment:** `Bạn đóng vai P10-A10 (Atomic publish coordinator). Chỉ làm Kiểm đủ 9 artifact, signer, sha và swap release pointer. Xuất `publication_transaction.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Partial publish khi index fail.`

**Phase reducer bắt buộc:** xác nhận 10/10 slot terminal, artifact hash hợp lệ, provenance complete, policy fail-closed, reducer deterministic, `observed_in_flight_peak` đo thực. Khi failure/uncertain, trạng thái `GATE_BLOCKED`, không khởi chạy phase sau.

