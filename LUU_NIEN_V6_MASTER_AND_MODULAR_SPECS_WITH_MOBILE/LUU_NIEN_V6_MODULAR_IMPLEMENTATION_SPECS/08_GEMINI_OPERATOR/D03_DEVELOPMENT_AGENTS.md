# D03 engineering wave agent assignments

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.C/D03`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `D03` — Historical truth chain (10 concurrent lanes)

**Dependent tickets:** `AIR-019..AIR-024`. **Coordinator input:** frozen base commit, selected ticket packet, repo tree and limited file pointers. **Global rule:** exactly 10 task leases, code changes isolated, runtime peak measured.

### `D03-A01` — Atomic claim schema

- Assignment: Atomic claim schema; chỉ làm đúng phần của `D03`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D03-A01: Atomic claim schema. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D03-A02` — Quote verifier

- Assignment: Quote verifier; chỉ làm đúng phần của `D03`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D03-A02: Quote verifier. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D03-A03` — Source independence

- Assignment: Source independence; chỉ làm đúng phần của `D03`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D03-A03: Source independence. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D03-A04` — Chronology reviewer

- Assignment: Chronology reviewer; chỉ làm đúng phần của `D03`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D03-A04: Chronology reviewer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D03-A05` — Geographic precision reviewer

- Assignment: Geographic precision reviewer; chỉ làm đúng phần của `D03`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D03-A05: Geographic precision reviewer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D03-A06` — Contradictions detector

- Assignment: Contradictions detector; chỉ làm đúng phần của `D03`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D03-A06: Contradictions detector. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D03-A07` — Claim UI reviewer

- Assignment: Claim UI reviewer; chỉ làm đúng phần của `D03`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D03-A07: Claim UI reviewer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D03-A08` — Dossier assembler

- Assignment: Dossier assembler; chỉ làm đúng phần của `D03`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D03-A08: Dossier assembler. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D03-A09` — Evidence tests author

- Assignment: Evidence tests author; chỉ làm đúng phần của `D03`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D03-A09: Evidence tests author. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D03-A10` — Human historiography reviewer

- Assignment: Human historiography reviewer; chỉ làm đúng phần của `D03`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D03-A10: Human historiography reviewer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

**Barrier:** coordinator chờ đủ 10 reports; sắp xếp PR patch với file-owner single-writer, chạy test sau mỗi merge; mọi risk P0 => stop. 10 roles concurrent không có nghĩa 10 PR cùng lúc.

