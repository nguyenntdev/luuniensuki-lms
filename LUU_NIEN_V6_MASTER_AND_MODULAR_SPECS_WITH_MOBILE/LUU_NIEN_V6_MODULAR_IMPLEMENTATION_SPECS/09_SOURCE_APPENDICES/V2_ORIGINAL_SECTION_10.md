# V2 original archival technical chapter — SECTION_10

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 10. RESEARCH DATA WAREHOUSE & GOOGLE FORMS INGESTION

### 10.1 Source files cần nhóm cung cấp (không có trong ZIP)

1. Original Google Forms structure exported with question text, item type, choice options, optional/required, branching, form version, created/updated timestamps.
2. Raw anonymized response export (CSV/XLSX), không chứa tên/email/IP/điện thoại/mã học sinh thật.
3. Raw vs valid vs excluded counts, duplicate policy and missing-data policy; school sample counts, recruitment dates, survey venue, response rates nếu có.
4. Instrument provenance, teacher/school permissions and parental/student assent where applicable, secondary research data use authorization.
5. Exact resource version(s) seen, mode exposure (independent/group demo/class), duration, survey sequence; absence phải ghi unknown.
6. Research team author/data provenance and source study rights (dossier năm 2026 được dùng lại).

### 10.2 Data mapping / validation rules

- Form item code stable: `AWARE_01`, `CHANNEL_01_MULTI`, `WANT_DIGITAL_01`, `INTEREST_FORMAT_01`, `APPRAISAL_*`, `PRIDE_*`.
- Không ép chung hai nhóm câu hỏi thành pre/post nếu không có participant_id and timestamps credible.
- `N_i` = số response hợp lệ của từng câu hỏi; không tự lấy 1.502 cho mọi item nếu có skips; báo `N_total` riêng.
- Multiple response: lưu từng selection với `(participant,item,choice)` unique; `sum selections` ≤ `maxChoices × answeredPeople`, kiểm `4.506=3×1.502` bằng original form.
- Kiểm cặp `aware=no` và `textbooks=yes` xem wording và skip logic; không suy luận mâu thuẫn khi đang hỏi “bản đúc nổi được ghi danh” vs “Cửu Đỉnh nói chung”.
- Cross-school analysis nếu có codes, tính design effect/ICC trước inferential p-values; không mặc định independent simple random sample.
- Survey constructs không đồng nhất: familiarity, preference, engagement perception, self-reported understanding, preservation attitude; reliability chỉ khi item set đo cùng construct và có lý thuyết đo phù hợp.
- Nếu chỉ cảm nhận: không nói “knowledge increased”/“historical reasoning improved”, mà chỉ “self-reported perceived understanding”; outcome direct requires independent rubric/test.

### 10.3 Các bảng phải tái lập được

**Fixed published checkpoints từ bài báo (cần đối chiếu raw):**

| Code | n | Published % | Type |
|---|---:|---:|---|
| NO_PRIOR_AWARENESS | 958 | 63.8 | binary awareness |
| WANT_DIGITAL | 1412 | 94.0 | combined ordinal |
| INTEREST_NEW_FORMAT | 1308 | 87.1 | combined ordinal |
| POSITIVE_CONTENT | 1413 | 94.1 | combined ordinal |
| PERCEIVED_UNDERSTANDING | 1420 | 94.5 | subjective evaluation |
| PERCEIVED_IMPLEMENTATION | 1435 | 95.5 | subjective evaluation |
| PERCEIVED_PRESERVATION | 1465 | 97.5 | subjective change perception |
| READY_TO_SHARE | 1393 | 92.7 | intent |
| VIRTUAL_3D_PREFERENCE | 1350 | 89.9 | multi-response |
| HANDBOOK_PREFERENCE | 1250 | 83.2 | multi-response |
| WEB_VIDEO_PREFERENCE | 1220 | 81.2 | multi-response |
| EXPERIENTIAL_PREFERENCE | 686 | 45.7 | multi-response |

**Acceptance:** reproducibility script từ pseudonymized CSV xuất ra các bảng có `count`, `valid_N`, `rate`, `source_item`, `filter`, `code_hash` và diff = 0 đối với số đã xác minh; sai lệch phải tạo audit exception, tuyệt đối không sửa bảng ngầm.

### 10.4 Privacy/security của research

- Tách raw identified input (nếu có) khỏi pseudonymized analytic dataset; khóa mapping trong hệ thống riêng không đưa vào GitHub.
- Encrypt at rest, import audit, role-based exports, DPA với nhà cung cấp dịch vụ, policy lưu/xóa theo thẩm quyền và sự đồng ý.
- Thống kê n nhỏ có nguy cơ tái nhận diện phải suppress theo ngưỡng được quy định trước; không chia quá nhỏ trường/lớp.
- Mọi báo cáo Q2/HCMUS phải gắn `research_snapshot_id`, codecommit, form_version, aggregate script hash.
- Dữ liệu người chưa thành niên: quyền sửa/xóa đồng thuận và giới hạn mục đích; không dùng để huấn luyện AI mặc định.

### 10.5 Thiết kế nghiên cứu tiếp theo (CHƯA LÀM)

**Hypothesis H1:** guided 3D source-linked lesson vs equivalent well-designed 2D lesson có khác biệt về điểm sử dụng chứng cứ sau hoạt động không? Chọn lớp/cluster randomization nếu khả thi; pre-register outcome; similar time, teacher, source and objectives; có blinded scoring, ICC/power calculation; delayed transfer task. Kết quả khi chưa chạy: `NOT_MEASURED`; không gán 1.502 survey là 1.502 experimental participants.

---

