# D02 engineering wave agent assignments

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.C/D02`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `D02` — Source ingestion (10 concurrent lanes)

**Dependent tickets:** `AIR-011..AIR-018`. **Coordinator input:** frozen base commit, selected ticket packet, repo tree and limited file pointers. **Global rule:** exactly 10 task leases, code changes isolated, runtime peak measured.

### `D02-A01` — Official source adapter

- Assignment: Official source adapter; chỉ làm đúng phần của `D02`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D02-A01: Official source adapter. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D02-A02` — Academic metadata adapter

- Assignment: Academic metadata adapter; chỉ làm đúng phần của `D02`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D02-A02: Academic metadata adapter. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D02-A03` — Rights decision reviewer

- Assignment: Rights decision reviewer; chỉ làm đúng phần của `D02`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D02-A03: Rights decision reviewer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D02-A04` — Snapshot downloader

- Assignment: Snapshot downloader; chỉ làm đúng phần của `D02`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D02-A04: Snapshot downloader. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D02-A05` — PDF page parser

- Assignment: PDF page parser; chỉ làm đúng phần của `D02`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D02-A05: PDF page parser. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D02-A06` — HTML parser

- Assignment: HTML parser; chỉ làm đúng phần của `D02`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D02-A06: HTML parser. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D02-A07` — Han-Nom reviewer UI

- Assignment: Han-Nom reviewer UI; chỉ làm đúng phần của `D02`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D02-A07: Han-Nom reviewer UI. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D02-A08` — OCR fixtures author

- Assignment: OCR fixtures author; chỉ làm đúng phần của `D02`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D02-A08: OCR fixtures author. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D02-A09` — Citation offset tester

- Assignment: Citation offset tester; chỉ làm đúng phần của `D02`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D02-A09: Citation offset tester. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D02-A10` — Security injection tester

- Assignment: Security injection tester; chỉ làm đúng phần của `D02`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D02-A10: Security injection tester. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

**Barrier:** coordinator chờ đủ 10 reports; sắp xếp PR patch với file-owner single-writer, chạy test sau mỗi merge; mọi risk P0 => stop. 10 roles concurrent không có nghĩa 10 PR cùng lúc.

