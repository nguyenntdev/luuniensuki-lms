# P01: TEN HISTORICAL RESEARCH AGENT PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.A.P01`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V4.A.P01 — Source discovery

**Mục tiêu chung:** Queries for official archives, historical editions, scholarly sources, Han-Nom. **Input package:** `P00 charter, provider allowlist`. **Output reducer:** `source_candidates/v1`. **Blocking gate:** Candidate is not proof; DOI/URL existence check.

**Quy tắc 10-concurrent:** coordinator tạo `A01..A10` trong một wave, `input_manifest_sha256` giống nhau, kích hoạt qua worker độc lập và quan sát running overlap; thu 10 envelopes trước reduce. Tác vụ có thể trả `NO_EVIDENCE` khi phù hợp, không được invent tài liệu để đủ số lượng.

### Agent `P01-A01` — Official heritage registry scout

**Assignment cụ thể:** Tìm nguồn UNESCO/MOWCAP/cơ quan di sản có hồ sơ gốc.

**Input bắt buộc:** immutable manifest `P00 charter, provider allowlist` với `run_id`, `phase=P01`, `wave`, `agent_index=1`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/discovery.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``candidates_official.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `1` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tìm nguồn UNESCO/MOWCAP/cơ quan di sản có hồ sơ gốc” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Gọi trang giới thiệu là bản gốc đủ cho mọi claim**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Gọi trang giới thiệu là bản gốc đủ cho mọi claim` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P01: Candidate is not proof; DOI/URL existence check.

**Gemini prompt fragment:** `Bạn đóng vai P01-A01 (Official heritage registry scout). Chỉ làm Tìm nguồn UNESCO/MOWCAP/cơ quan di sản có hồ sơ gốc. Xuất `candidates_official.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Gọi trang giới thiệu là bản gốc đủ cho mọi claim.`

### Agent `P01-A02` — Dynastic chronicles scout

**Assignment cụ thể:** Tìm ấn bản Đại Nam thực lục, Khâm định ... liên quan.

**Input bắt buộc:** immutable manifest `P00 charter, provider allowlist` với `run_id`, `phase=P01`, `wave`, `agent_index=2`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/discovery.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``candidates_chronicles.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `2` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tìm ấn bản Đại Nam thực lục, Khâm định ... liên quan” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Bịa số quyển, trang khi không truy cập**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Bịa số quyển, trang khi không truy cập` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P01: Candidate is not proof; DOI/URL existence check.

**Gemini prompt fragment:** `Bạn đóng vai P01-A02 (Dynastic chronicles scout). Chỉ làm Tìm ấn bản Đại Nam thực lục, Khâm định ... liên quan. Xuất `candidates_chronicles.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Bịa số quyển, trang khi không truy cập.`

### Agent `P01-A03` — Royal document scout

**Assignment cụ thể:** Tìm châu bản, tài liệu cung đình có chỉ mục hợp lệ.

**Input bắt buộc:** immutable manifest `P00 charter, provider allowlist` với `run_id`, `phase=P01`, `wave`, `agent_index=3`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/discovery.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``candidates_royal.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `3` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tìm châu bản, tài liệu cung đình có chỉ mục hợp lệ” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Xem ảnh không rõ nguồn là bản lưu trữ xác thực**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Xem ảnh không rõ nguồn là bản lưu trữ xác thực` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P01: Candidate is not proof; DOI/URL existence check.

**Gemini prompt fragment:** `Bạn đóng vai P01-A03 (Royal document scout). Chỉ làm Tìm châu bản, tài liệu cung đình có chỉ mục hợp lệ. Xuất `candidates_royal.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Xem ảnh không rõ nguồn là bản lưu trữ xác thực.`

### Agent `P01-A04` — Museum catalogue scout

**Assignment cụ thể:** Tìm catalog bảo tàng, mô tả hiện vật, ảnh có số kiểm kê.

**Input bắt buộc:** immutable manifest `P00 charter, provider allowlist` với `run_id`, `phase=P01`, `wave`, `agent_index=4`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/discovery.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``candidates_museum.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `4` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tìm catalog bảo tàng, mô tả hiện vật, ảnh có số kiểm kê” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Nhập media thiếu quyền**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Nhập media thiếu quyền` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P01: Candidate is not proof; DOI/URL existence check.

**Gemini prompt fragment:** `Bạn đóng vai P01-A04 (Museum catalogue scout). Chỉ làm Tìm catalog bảo tàng, mô tả hiện vật, ảnh có số kiểm kê. Xuất `candidates_museum.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Nhập media thiếu quyền.`

### Agent `P01-A05` — Peer-reviewed literature scout

**Assignment cụ thể:** Tìm nghiên cứu học thuật về Cửu Đỉnh, ý nghĩa hình tượng.

**Input bắt buộc:** immutable manifest `P00 charter, provider allowlist` với `run_id`, `phase=P01`, `wave`, `agent_index=5`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/discovery.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``candidates_scholarly.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `5` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tìm nghiên cứu học thuật về Cửu Đỉnh, ý nghĩa hình tượng” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Trộn trích dẫn gián tiếp với chứng cứ sơ cấp**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Trộn trích dẫn gián tiếp với chứng cứ sơ cấp` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P01: Candidate is not proof; DOI/URL existence check.

**Gemini prompt fragment:** `Bạn đóng vai P01-A05 (Peer-reviewed literature scout). Chỉ làm Tìm nghiên cứu học thuật về Cửu Đỉnh, ý nghĩa hình tượng. Xuất `candidates_scholarly.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Trộn trích dẫn gián tiếp với chứng cứ sơ cấp.`

### Agent `P01-A06` — Historical maps scout

**Assignment cụ thể:** Tìm bản đồ xưa và bản đồ địa danh được cơ quan tin cậy cung cấp.

**Input bắt buộc:** immutable manifest `P00 charter, provider allowlist` với `run_id`, `phase=P01`, `wave`, `agent_index=6`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/discovery.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``candidates_maps.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `6` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tìm bản đồ xưa và bản đồ địa danh được cơ quan tin cậy cung cấp” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Gán tọa độ chính xác giả**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Gán tọa độ chính xác giả` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P01: Candidate is not proof; DOI/URL existence check.

**Gemini prompt fragment:** `Bạn đóng vai P01-A06 (Historical maps scout). Chỉ làm Tìm bản đồ xưa và bản đồ địa danh được cơ quan tin cậy cung cấp. Xuất `candidates_maps.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Gán tọa độ chính xác giả.`

### Agent `P01-A07` — Han-Nom editions scout

**Assignment cụ thể:** Tìm bản khắc/in, phiên âm, bản dịch có provenance.

**Input bắt buộc:** immutable manifest `P00 charter, provider allowlist` với `run_id`, `phase=P01`, `wave`, `agent_index=7`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/discovery.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``candidates_hannom.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `7` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tìm bản khắc/in, phiên âm, bản dịch có provenance” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Lấy Unicode của AI làm nguyên tác**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Lấy Unicode của AI làm nguyên tác` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P01: Candidate is not proof; DOI/URL existence check.

**Gemini prompt fragment:** `Bạn đóng vai P01-A07 (Han-Nom editions scout). Chỉ làm Tìm bản khắc/in, phiên âm, bản dịch có provenance. Xuất `candidates_hannom.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Lấy Unicode của AI làm nguyên tác.`

### Agent `P01-A08` — Image and 3D rights scout

**Assignment cụ thể:** Tìm asset hiện trạng, license, nguồn ảnh rõ ràng.

**Input bắt buộc:** immutable manifest `P00 charter, provider allowlist` với `run_id`, `phase=P01`, `wave`, `agent_index=8`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/discovery.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``candidates_media.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `8` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tìm asset hiện trạng, license, nguồn ảnh rõ ràng” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Mặc định cho phép tải lại ảnh**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Mặc định cho phép tải lại ảnh` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P01: Candidate is not proof; DOI/URL existence check.

**Gemini prompt fragment:** `Bạn đóng vai P01-A08 (Image and 3D rights scout). Chỉ làm Tìm asset hiện trạng, license, nguồn ảnh rõ ràng. Xuất `candidates_media.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Mặc định cho phép tải lại ảnh.`

### Agent `P01-A09` — Open scholarly metadata scout

**Assignment cụ thể:** Tra DOI/ISBN/ISSN/thư viện, repository, metadata resolvers.

**Input bắt buộc:** immutable manifest `P00 charter, provider allowlist` với `run_id`, `phase=P01`, `wave`, `agent_index=9`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/discovery.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``candidates_metadata.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `9` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Tra DOI/ISBN/ISSN/thư viện, repository, metadata resolvers” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Tin DOI do LLM tạo mà không resolver**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Tin DOI do LLM tạo mà không resolver` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P01: Candidate is not proof; DOI/URL existence check.

**Gemini prompt fragment:** `Bạn đóng vai P01-A09 (Open scholarly metadata scout). Chỉ làm Tra DOI/ISBN/ISSN/thư viện, repository, metadata resolvers. Xuất `candidates_metadata.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Tin DOI do LLM tạo mà không resolver.`

### Agent `P01-A10` — Contrarian/coverage scout

**Assignment cụ thể:** Chủ động tìm nghiên cứu bất đồng và khoảng trống nguồn.

**Input bắt buộc:** immutable manifest `P00 charter, provider allowlist` với `run_id`, `phase=P01`, `wave`, `agent_index=10`, approved `scope`, versioned artifact refs, allowlist, `budget_remaining`. Không nhận personal student data.

**Code integration:** kiểm đường dẫn `backend/services/research_factory/discovery.py [TARGET];backend/history_models.py`; chỉ đọc API/source đã cho phép, mọi path `[TARGET]` phải được tạo ở ticket tương ứng trước khi gọi.

**Deliverable:** ``candidates_disputes.json` + provenance, warnings, SHA`; bên trong bắt buộc có `schema_version`, `subject_refs[]`, `source_version_refs[]`, `evidence_locator_refs[]`, `findings[]`, `uncertainty[]`, `blockers[]`, `artifact_sha256` và `tool_usage`. Với card chuyên quyền, ghi `rights_decision` thay cho suy đoán; với card biên soạn, ghi `sentence_claim_refs`.

**Trình tự để Gemini thực thi (one task):**

1. Verify job slot `10` lease và input digest; nếu mismatch → `BLOCKED_INPUT_VERSION`.

2. Kiểm valid role-specific source IDs + permissions; loại source không có quyền dùng.

3. Thực hiện đúng mục tiêu “Chủ động tìm nghiên cứu bất đồng và khoảng trống nguồn” trên **phần dữ liệu được chia**, không lấy thêm nguồn ngoài connector policy.

4. Tách facts/observations/inferences; gắn source edition + page/offset cho từng mệnh đề lịch sử.

5. Soát negative case: **Chỉ chọn nguồn xác nhận luận điểm sẵn có**. Nếu xảy ra thì thêm blocker và không tự bịa bản thay thế.

6. Validate JSON schema và SHA-256 qua code deterministic; lưu output vào private immutable store, rồi commit envelope.

7. Không ký duyệt, không sửa published content, không tự đánh dấu historical claim verified.

**Acceptance tests cho role:**
- Role negative: `Chỉ chọn nguồn xác nhận luận điểm sẵn có` phải trả blocker/review, không PASS giả.
- Payload schema: missing `source_version_refs` hoặc malformed locator bị reject nếu kết quả có factual claim.
- Idempotency: cùng input hash + role + wave không tạo hai artifact public.
- Gate chung P01: Candidate is not proof; DOI/URL existence check.

**Gemini prompt fragment:** `Bạn đóng vai P01-A10 (Contrarian/coverage scout). Chỉ làm Chủ động tìm nghiên cứu bất đồng và khoảng trống nguồn. Xuất `candidates_disputes.json` + provenance, warnings, SHA. Không dùng kiến thức nội tại thay source; không tự phê duyệt. Test trường hợp: Chỉ chọn nguồn xác nhận luận điểm sẵn có.`

**Phase reducer bắt buộc:** xác nhận 10/10 slot terminal, artifact hash hợp lệ, provenance complete, policy fail-closed, reducer deterministic, `observed_in_flight_peak` đo thực. Khi failure/uncertain, trạng thái `GATE_BLOCKED`, không khởi chạy phase sau.

