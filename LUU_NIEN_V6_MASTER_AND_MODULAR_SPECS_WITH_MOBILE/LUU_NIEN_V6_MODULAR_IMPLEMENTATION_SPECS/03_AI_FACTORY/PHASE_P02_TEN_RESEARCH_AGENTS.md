# P02: TEN HISTORICAL RESEARCH AGENT PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.A.P02`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V4.A.P02 — Candidate metadata, rights and acquisition

**Mục tiêu chung:** Resolve source identity, editions, terms, rights and snapshots. **Input package:** `P01 candidate registry, policy registry`. **Output reducer:** `verified_sources/v1`. **Blocking gate:** Unknown rights/editions quarantined.

**Quy tắc 10-concurrent:** coordinator tạo `A01..A10` trong một wave, `input_manifest_sha256` giống nhau, kích hoạt qua worker độc lập và quan sát running overlap; thu 10 envelopes trước reduce. Tác vụ có thể trả `NO_EVIDENCE` khi phù hợp, không được invent tài liệu để đủ số lượng.

### Agent `P02-A01` — Bibliography verifier

**Assignment cụ thể:** Xác thực tác giả, ấn bản, ISBN, DOI và year.

**Input bắt buộc:** immutable manifest `P01 candidate registry, policy registry` với `run_id`, `phase=P02`, `wave`, `agent_index=1`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/acquisition.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``bib_verification.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `1` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Xác thực tác giả, ấn bản, ISBN, DOI và year” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Cùng tên sách nhưng nhầm ấn bản**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Cùng tên sách nhưng nhầm ấn bản` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P02: Unknown rights/editions quarantined.

**Gemini prompt fragment:** `Bạn đóng vai P02-A01 (Bibliography verifier). Chỉ làm Xác thực tác giả, ấn bản, ISBN, DOI và year. Xuất `bib_verification.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Cùng tên sách nhưng nhầm ấn bản.`

### Agent `P02-A02` — Canonical URL resolver

**Assignment cụ thể:** Định chuẩn URL và redirect, archive URL, access timestamp.

**Input bắt buộc:** immutable manifest `P01 candidate registry, policy registry` với `run_id`, `phase=P02`, `wave`, `agent_index=2`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/acquisition.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``canonical_urls.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `2` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Định chuẩn URL và redirect, archive URL, access timestamp” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **URL redirect sang bản không phải nguồn**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `URL redirect sang bản không phải nguồn` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P02: Unknown rights/editions quarantined.

**Gemini prompt fragment:** `Bạn đóng vai P02-A02 (Canonical URL resolver). Chỉ làm Định chuẩn URL và redirect, archive URL, access timestamp. Xuất `canonical_urls.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: URL redirect sang bản không phải nguồn.`

### Agent `P02-A03` — Authority verifier

**Assignment cụ thể:** Xác thực cơ quan/tác giả/nhà xuất bản và tính xác thực.

**Input bắt buộc:** immutable manifest `P01 candidate registry, policy registry` với `run_id`, `phase=P02`, `wave`, `agent_index=3`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/acquisition.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``authority_checks.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `3` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Xác thực cơ quan/tác giả/nhà xuất bản và tính xác thực” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Bài blog giả danh bảo tàng**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Bài blog giả danh bảo tàng` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P02: Unknown rights/editions quarantined.

**Gemini prompt fragment:** `Bạn đóng vai P02-A03 (Authority verifier). Chỉ làm Xác thực cơ quan/tác giả/nhà xuất bản và tính xác thực. Xuất `authority_checks.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Bài blog giả danh bảo tàng.`

### Agent `P02-A04` — Duplicate lineage analyzer

**Assignment cụ thể:** Gộp mirrors/đăng lại; ghi quan hệ phụ thuộc nguồn.

**Input bắt buộc:** immutable manifest `P01 candidate registry, policy registry` với `run_id`, `phase=P02`, `wave`, `agent_index=4`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/acquisition.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``source_lineage.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `4` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Gộp mirrors/đăng lại; ghi quan hệ phụ thuộc nguồn” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Hai mirror bị tính hai nguồn**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Hai mirror bị tính hai nguồn` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P02: Unknown rights/editions quarantined.

**Gemini prompt fragment:** `Bạn đóng vai P02-A04 (Duplicate lineage analyzer). Chỉ làm Gộp mirrors/đăng lại; ghi quan hệ phụ thuộc nguồn. Xuất `source_lineage.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Hai mirror bị tính hai nguồn.`

### Agent `P02-A05` — License analyst

**Assignment cụ thể:** Xác định quyền lưu, trích, hiển thị, dịch, TDM riêng.

**Input bắt buộc:** immutable manifest `P01 candidate registry, policy registry` với `run_id`, `phase=P02`, `wave`, `agent_index=5`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/acquisition.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``license_assessment.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `5` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Xác định quyền lưu, trích, hiển thị, dịch, TDM riêng” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **CC BY-NC coi như cho phép thương mại**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `CC BY-NC coi như cho phép thương mại` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P02: Unknown rights/editions quarantined.

**Gemini prompt fragment:** `Bạn đóng vai P02-A05 (License analyst). Chỉ làm Xác định quyền lưu, trích, hiển thị, dịch, TDM riêng. Xuất `license_assessment.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: CC BY-NC coi như cho phép thương mại.`

### Agent `P02-A06` — Access negotiator

**Assignment cụ thể:** Liệt kê nguồn cần xin phép/chuyển yêu cầu cho người phụ trách.

**Input bắt buộc:** immutable manifest `P01 candidate registry, policy registry` với `run_id`, `phase=P02`, `wave`, `agent_index=6`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/acquisition.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``permissions_queue.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `6` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Liệt kê nguồn cần xin phép/chuyển yêu cầu cho người phụ trách” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **AI tự gửi thư nhận quyền thành công**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `AI tự gửi thư nhận quyền thành công` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P02: Unknown rights/editions quarantined.

**Gemini prompt fragment:** `Bạn đóng vai P02-A06 (Access negotiator). Chỉ làm Liệt kê nguồn cần xin phép/chuyển yêu cầu cho người phụ trách. Xuất `permissions_queue.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: AI tự gửi thư nhận quyền thành công.`

### Agent `P02-A07` — Fetch planner

**Assignment cụ thể:** Quyết định PDF scan/HTML/API ưu tiên, giới hạn byte và nhịp.

**Input bắt buộc:** immutable manifest `P01 candidate registry, policy registry` với `run_id`, `phase=P02`, `wave`, `agent_index=7`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/acquisition.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``fetch_manifest.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `7` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Quyết định PDF scan/HTML/API ưu tiên, giới hạn byte và nhịp” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Tải hàng loạt vượt hạn mức**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Tải hàng loạt vượt hạn mức` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P02: Unknown rights/editions quarantined.

**Gemini prompt fragment:** `Bạn đóng vai P02-A07 (Fetch planner). Chỉ làm Quyết định PDF scan/HTML/API ưu tiên, giới hạn byte và nhịp. Xuất `fetch_manifest.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Tải hàng loạt vượt hạn mức.`

### Agent `P02-A08` — Malware/document sanitiser

**Assignment cụ thể:** Kiểm MIME, phần mở rộng, virus, PDF active content.

**Input bắt buộc:** immutable manifest `P01 candidate registry, policy registry` với `run_id`, `phase=P02`, `wave`, `agent_index=8`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/acquisition.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``security_scan.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `8` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Kiểm MIME, phần mở rộng, virus, PDF active content” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Tệp thực thi giả PDF vào worker**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Tệp thực thi giả PDF vào worker` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P02: Unknown rights/editions quarantined.

**Gemini prompt fragment:** `Bạn đóng vai P02-A08 (Malware/document sanitiser). Chỉ làm Kiểm MIME, phần mở rộng, virus, PDF active content. Xuất `security_scan.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Tệp thực thi giả PDF vào worker.`

### Agent `P02-A09` — Asset hash controller

**Assignment cụ thể:** SHA-256, byte_size, content_type, frozen object store.

**Input bắt buộc:** immutable manifest `P01 candidate registry, policy registry` với `run_id`, `phase=P02`, `wave`, `agent_index=9`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/acquisition.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``snapshots_plan.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `9` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “SHA-256, byte_size, content_type, frozen object store” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Snapshot đè ảnh nguồn**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Snapshot đè ảnh nguồn` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P02: Unknown rights/editions quarantined.

**Gemini prompt fragment:** `Bạn đóng vai P02-A09 (Asset hash controller). Chỉ làm SHA-256, byte_size, content_type, frozen object store. Xuất `snapshots_plan.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Snapshot đè ảnh nguồn.`

### Agent `P02-A10` — Acquisition QA auditor

**Assignment cụ thể:** Kiểm candidate/provenance/rights chain, quarantine nguồn lỗi.

**Input bắt buộc:** immutable manifest `P01 candidate registry, policy registry` với `run_id`, `phase=P02`, `wave`, `agent_index=10`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/acquisition.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``acquisition_gate.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `10` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Kiểm candidate/provenance/rights chain, quarantine nguồn lỗi” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Quyền chưa rõ lại được cho trích toàn văn**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Quyền chưa rõ lại được cho trích toàn văn` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P02: Unknown rights/editions quarantined.

**Gemini prompt fragment:** `Bạn đóng vai P02-A10 (Acquisition QA auditor). Chỉ làm Kiểm candidate/provenance/rights chain, quarantine nguồn lỗi. Xuất `acquisition_gate.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Quyền chưa rõ lại được cho trích toàn văn.`

**Phase reducer bắt buộc:** xác nhận 10/10 slot terminal, artifact hash hợp lệ, provenance complete, policy fail-closed, reducer deterministic, `observed_in_flight_peak` đo thực. Khi failure/uncertain, trạng thái `GATE_BLOCKED`, không khởi chạy phase sau.

