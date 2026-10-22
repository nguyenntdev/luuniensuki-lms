# V2 engineering tickets R0 — extracted original

### R0-001 — Pin & fingerprint source snapshot (P0)
**Baseline file:** `README.md` — [EXISTING PATH]. **Dependency:** `none`.
**Mục tiêu thay đổi:** Ghi SHA ZIP, hash manifest, version toolchain, tạo SBOM có khả năng tái lập và owner dữ liệu.
**Hợp đồng đầu ra / acceptance:** Re-run trên cùng source cho manifest byte-identical; log branch ZIP là snapshot, không giả HEAD.
**Negative regression bắt buộc:** File gốc bị thay một byte phát hiện hash mismatch.
**Evidence cần commit vào CI hoặc evidence vault:** `snapshot-manifest.json`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R0-002 — Build backend reproducibly (P0)
**Baseline file:** `backend/requirements.txt` — [EXISTING PATH]. **Dependency:** `R0-001`.
**Mục tiêu thay đổi:** Pin dependencies và Python version; tạo disposable Postgres/Redis dev compose + bootstrap script.
**Hợp đồng đầu ra / acceptance:** `pytest` chạy được trong CI sạch; logs và dependency hash lưu artifact.
**Negative regression bắt buộc:** Thiếu psycopg hoặc DB bootstrap làm CI đỏ, không được bỏ test.
**Evidence cần commit vào CI hoặc evidence vault:** `backend-test-report.xml`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R0-003 — Add Rust/Flutter CI (P0)
**Baseline file:** `.github/workflows/ci.yml` — [EXISTING PATH]. **Dependency:** `R0-001`.
**Mục tiêu thay đổi:** Thêm cargo fmt/clippy/test và flutter analyze/test theo matrix; cache pin version.
**Hợp đồng đầu ra / acceptance:** CI chạy trên PR integration branch, thất bại sẽ block merge.
**Negative regression bắt buộc:** Không chạy cargo/flutter nhưng hiển thị badge pass bị chặn.
**Evidence cần commit vào CI hoặc evidence vault:** `ci-matrix-report`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R0-004 — Prohibit migration swallow (P0)
**Baseline file:** `.github/workflows/deploy.yml` — [EXISTING PATH]. **Dependency:** `R0-002`.
**Mục tiêu thay đổi:** Bỏ `alembic upgrade head` với toán tử bỏ qua lỗi trong deploy script, kiểm schema head trước health và chỉ promote khi pass.
**Hợp đồng đầu ra / acceptance:** Forced migration failure làm deploy fail, app cũ vẫn phục vụ.
**Negative regression bắt buộc:** Migration thất bại nhưng release báo success là regression P0.
**Evidence cần commit vào CI hoặc evidence vault:** `migration-failure-drill`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R0-005 — Readiness vs liveness (P0)
**Baseline file:** `backend-rust/src/main.rs` — [EXISTING PATH]. **Dependency:** `R0-002`.
**Mục tiêu thay đổi:** Tách /livez khỏi /readyz; /readyz kiểm DB pool, schema, workers cần thiết.
**Hợp đồng đầu ra / acceptance:** DB down cho liveness 200 nhưng readiness non-200, pod không nhận traffic.
**Negative regression bắt buộc:** Pool None mà service vẫn marked ready bị chặn.
**Evidence cần commit vào CI hoặc evidence vault:** `readiness-integration`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R0-006 — Reconcile Alembic heads (P0)
**Baseline file:** `migrations/versions` — [EXISTING PATH]. **Dependency:** `R0-002`.
**Mục tiêu thay đổi:** Đồ thị revision, detect branch heads/cycles/missing down_revision; chọn merge migration có test.
**Hợp đồng đầu ra / acceptance:** Migrate từ empty và sanitized snapshot đều đạt cùng head.
**Negative regression bắt buộc:** Down_revision mất node hoặc revision conflict block release.
**Evidence cần commit vào CI hoặc evidence vault:** `migration-graph.json`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R0-007 — Production safe configuration (P0)
**Baseline file:** `.env.example` — [EXISTING PATH]. **Dependency:** `R0-001`.
**Mục tiêu thay đổi:** Phân biệt demo/staging/prod, validate required env tại startup, đóng mock fallback production.
**Hợp đồng đầu ra / acceptance:** No required secret or DB -> startup fails safe; no example credentials in prod.
**Negative regression bắt buộc:** DEMO_MODE true trên prod bị policy reject.
**Evidence cần commit vào CI hoặc evidence vault:** `config-audit`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R0-008 — OpenAPI ownership registry (P1)
**Baseline file:** `backend/main.py` — [EXISTING PATH]. **Dependency:** `R0-002`.
**Mục tiêu thay đổi:** Liệt kê canonical owner route Rust/Python; generate OpenAPI và detect duplicate semantics.
**Hợp đồng đầu ra / acceptance:** Mỗi external route có một owner + test fixture; có parity status/payload.
**Negative regression bắt buộc:** Native và fallback trả khác status/body trên cùng request gây CI fail.
**Evidence cần commit vào CI hoặc evidence vault:** `openapi-diff`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R0-009 — Secrets/license scans (P1)
**Baseline file:** `.github/workflows/ci.yml` — [EXISTING PATH]. **Dependency:** `R0-001`.
**Mục tiêu thay đổi:** Secret scanning, dependency vulnerability scan, lockfile check, artifact SBOM.
**Hợp đồng đầu ra / acceptance:** Không merge khi phát hiện credential hoặc CVE vượt threshold phê duyệt.
**Negative regression bắt buộc:** Hardcoded key giả định là thật phải điều tra, không tự công khai.
**Evidence cần commit vào CI hoặc evidence vault:** `security-ci-scan`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R0-010 — Document live architecture (P1)
**Baseline file:** `docker-compose.prod.yml` — [EXISTING PATH]. **Dependency:** `R0-008`.
**Mục tiêu thay đổi:** Tạo C4 runtime diagram từ container/env/route logs thực, so với docs và reconcile.
**Hợp đồng đầu ra / acceptance:** Architecture map chỉ ra entrypoints hoạt động thực và routing chain.
**Negative regression bắt buộc:** Legacy root main.py bị xóa trước khi chứng minh không dùng bị chặn.
**Evidence cần commit vào CI hoặc evidence vault:** `runtime-topology`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
