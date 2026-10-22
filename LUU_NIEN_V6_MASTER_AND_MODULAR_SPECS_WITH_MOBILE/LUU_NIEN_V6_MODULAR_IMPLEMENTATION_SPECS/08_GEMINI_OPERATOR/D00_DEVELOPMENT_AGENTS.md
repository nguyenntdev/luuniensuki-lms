# D00 engineering wave agent assignments

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.C/D00`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `D00` — Baseline and audit (10 concurrent lanes)

**Dependent tickets:** `AIR-001`. **Coordinator input:** frozen base commit, selected ticket packet, repo tree and limited file pointers. **Global rule:** exactly 10 task leases, code changes isolated, runtime peak measured.

### `D00-A01` — Repo graph/invariants

- Assignment: Repo graph/invariants; chỉ làm đúng phần của `D00`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D00-A01: Repo graph/invariants. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D00-A02` — SQLAlchemy schema

- Assignment: SQLAlchemy schema; chỉ làm đúng phần của `D00`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D00-A02: SQLAlchemy schema. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D00-A03` — Alembic graph

- Assignment: Alembic graph; chỉ làm đúng phần của `D00`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D00-A03: Alembic graph. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D00-A04` — Rust gateway routing

- Assignment: Rust gateway routing; chỉ làm đúng phần của `D00`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D00-A04: Rust gateway routing. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D00-A05` — Next.js API consumers

- Assignment: Next.js API consumers; chỉ làm đúng phần của `D00`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D00-A05: Next.js API consumers. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D00-A06` — Research source data

- Assignment: Research source data; chỉ làm đúng phần của `D00`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `SCOPED_WRITE_OR_READ_REVIEW`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D00-A06: Research source data. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D00-A07` — Auth/RBAC

- Assignment: Auth/RBAC; chỉ làm đúng phần của `D00`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D00-A07: Auth/RBAC. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D00-A08` — Test/CI baselines

- Assignment: Test/CI baselines; chỉ làm đúng phần của `D00`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D00-A08: Test/CI baselines. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D00-A09` — Privacy/rights risks

- Assignment: Privacy/rights risks; chỉ làm đúng phần của `D00`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D00-A09: Privacy/rights risks. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

### `D00-A10` — Consolidation reviewer

- Assignment: Consolidation reviewer; chỉ làm đúng phần của `D00`, chỉ sử dụng files từ packet được coordinator phân công.

- Mode: `READ_ONLY`; nếu hai lanes chạm cùng file, biến lane phụ thành `READ_ONLY` và đề xuất patch, không ghi đè.

- Output: `agent_report.json` gồm `base_sha`, `requested_paths`, `actual_paths`, `findings`, `proposed_diff_sha`, `tests`, `risks`, `blocked_by`; tất cả claim status kèm evidence.

- Negative: reject wrong branch, conflicting file ownership, token/API key disclosure, migration without DB graph, unauthorised release.

- Prompt: `Bạn là D00-A10: Consolidation reviewer. Input only assigned subset. Do not merge or deploy. Produce a concise verifiable JSON report and stop.`

**Barrier:** coordinator chờ đủ 10 reports; sắp xếp PR patch với file-owner single-writer, chạy test sau mỗi merge; mọi risk P0 => stop. 10 roles concurrent không có nghĩa 10 PR cùng lúc.

