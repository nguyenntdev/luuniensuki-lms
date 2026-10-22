# D01 engineering wave agent assignments

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.C/D01`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `D01` — Scheduler and storage (10 concurrent lanes)

**Dependent tickets:** `AIR-002..AIR-009`. **Coordinator input:** frozen base commit, selected ticket packet, repo tree and limited file pointers. **Global rule:** exactly 10 task leases, code changes isolated, runtime peak measured.

### `D01-A01` — Run schema designer

- Assignment: Run schema designer; chỉ làm đúng phần của `D01`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D01-A01: Run schema designer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D01-A02` — Phase schema designer

- Assignment: Phase schema designer; chỉ làm đúng phần của `D01`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D01-A02: Phase schema designer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D01-A03` — Job leases engineer

- Assignment: Job leases engineer; chỉ làm đúng phần của `D01`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D01-A03: Job leases engineer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D01-A04` — Queue retry reviewer

- Assignment: Queue retry reviewer; chỉ làm đúng phần của `D01`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D01-A04: Queue retry reviewer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D01-A05` — Provider quotas engineer

- Assignment: Provider quotas engineer; chỉ làm đúng phần của `D01`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D01-A05: Provider quotas engineer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D01-A06` — Artifact hashes engineer

- Assignment: Artifact hashes engineer; chỉ làm đúng phần của `D01`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D01-A06: Artifact hashes engineer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D01-A07` — RBAC safety reviewer

- Assignment: RBAC safety reviewer; chỉ làm đúng phần của `D01`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D01-A07: RBAC safety reviewer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D01-A08` — API error contract tester

- Assignment: API error contract tester; chỉ làm đúng phần của `D01`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D01-A08: API error contract tester. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D01-A09` — Race-condition tester

- Assignment: Race-condition tester; chỉ làm đúng phần của `D01`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D01-A09: Race-condition tester. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D01-A10` — Migration impact reviewer

- Assignment: Migration impact reviewer; chỉ làm đúng phần của `D01`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D01-A10: Migration impact reviewer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

**Barrier:** coordinator chờ đủ 10 reports; sắp xếp PR patch với file-owner single-writer, chạy test sau mỗi merge; mọi risk P0 => stop. 10 roles concurrent không có nghĩa 10 PR cùng lúc.

