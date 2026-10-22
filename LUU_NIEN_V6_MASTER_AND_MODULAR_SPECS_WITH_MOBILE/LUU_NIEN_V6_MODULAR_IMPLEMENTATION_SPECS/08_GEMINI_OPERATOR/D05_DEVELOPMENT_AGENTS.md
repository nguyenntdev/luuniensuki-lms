# D05 engineering wave agent assignments

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.C/D05`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `D05` — QA and publish (10 concurrent lanes)

**Dependent tickets:** `AIR-031..AIR-038`. **Coordinator input:** frozen base commit, selected ticket packet, repo tree and limited file pointers. **Global rule:** exactly 10 task leases, code changes isolated, runtime peak measured.

### `D05-A01` — QA runner

- Assignment: QA runner; chỉ làm đúng phần của `D05`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D05-A01: QA runner. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D05-A02` — Prompt injection red team

- Assignment: Prompt injection red team; chỉ làm đúng phần của `D05`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D05-A02: Prompt injection red team. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D05-A03` — Rights red team

- Assignment: Rights red team; chỉ làm đúng phần của `D05`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D05-A03: Rights red team. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D05-A04` — Human approval flow

- Assignment: Human approval flow; chỉ làm đúng phần của `D05`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D05-A04: Human approval flow. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D05-A05` — Editorial diff UX

- Assignment: Editorial diff UX; chỉ làm đúng phần của `D05`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D05-A05: Editorial diff UX. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D05-A06` — Atomic release transaction

- Assignment: Atomic release transaction; chỉ làm đúng phần của `D05`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D05-A06: Atomic release transaction. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D05-A07` — History Tutor integration

- Assignment: History Tutor integration; chỉ làm đúng phần của `D05`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D05-A07: History Tutor integration. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D05-A08` — Public article UI

- Assignment: Public article UI; chỉ làm đúng phần của `D05`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D05-A08: Public article UI. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D05-A09` — Correction cascade

- Assignment: Correction cascade; chỉ làm đúng phần của `D05`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D05-A09: Correction cascade. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D05-A10` — Full release e2e tester

- Assignment: Full release e2e tester; chỉ làm đúng phần của `D05`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D05-A10: Full release e2e tester. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

**Barrier:** coordinator chờ đủ 10 reports; sắp xếp PR patch với file-owner single-writer, chạy test sau mỗi merge; mọi risk P0 => stop. 10 roles concurrent không có nghĩa 10 PR cùng lúc.

