# V2 engineering tickets R6 — extracted original

### R6-001 — Remove production fake inquiry fallback (P0)
**Baseline file:** `frontend/src/lib/rbpc/inquiries.ts` — [EXISTING PATH]. **Dependency:** `R0-007`.
**Mục tiêu thay đổi:** Replace mock-success catch with fail-closed error; demo fixtures isolated by build flag.
**Hợp đồng đầu ra / acceptance:** Backend offline => no “new” receipt, retry preserves idempotency.
**Negative regression bắt buộc:** Synthetic reference shown as confirmed server submission -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `inquiry-network-e2e`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R6-002 — Shared rate limiter and trusted proxy (P0)
**Baseline file:** `backend/routers/rbpc.py` — [EXISTING PATH]. **Dependency:** `R0-002`.
**Mục tiêu thay đổi:** Replace process dictionary; trust only configured proxy XFF; avoid leaking IP.
**Hợp đồng đầu ra / acceptance:** 2-replica quota consistent; spoofed XFF ineffective.
**Negative regression bắt buộc:** Worker restart bypasses limit -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `distributed-rate-test`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R6-003 — Partner scoped inquiry RBAC (P0)
**Baseline file:** `backend/routers/rbpc.py` — [EXISTING PATH]. **Dependency:** `R6-001`.
**Mục tiêu thay đổi:** Tenant filter by provider, deny other partner's updates and read.
**Hợp đồng đầu ra / acceptance:** Partner A sees only A; administrator auditable broad access.
**Negative regression bắt buộc:** Cross-tenant UUID update succeeds -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `partner-scope-tests`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R6-004 — Idempotent inquiry concurrency (P1)
**Baseline file:** `backend/routers/rbpc.py` — [EXISTING PATH]. **Dependency:** `R6-001`.
**Mục tiêu thay đổi:** DB unique index key+scope; transactional insert on collision, payload hash check.
**Hợp đồng đầu ra / acceptance:** Concurrent requests create exactly one inquiry and consistent ref.
**Negative regression bắt buộc:** Double record or changed-body same ref -> regression.
**Evidence cần commit vào CI hoặc evidence vault:** `inquiry-concurrency-test`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R6-005 — Consent withdrawal cascade (P1)
**Baseline file:** `backend/models_rbpc.py` — [EXISTING PATH]. **Dependency:** `R6-003`.
**Mục tiêu thay đổi:** Creator consent revocation hides public stories/workshops and purges cached media.
**Hợp đồng đầu ra / acceptance:** No new inquiry for withdrawn creator; proof audited.
**Negative regression bắt buộc:** Old mobile cache still advertises available booking -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `consent-revoke-tests`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R6-006 — Status token privacy (P1)
**Baseline file:** `backend/routers/rbpc.py` — [EXISTING PATH]. **Dependency:** `R6-002`.
**Mục tiêu thay đổi:** Rate-limit lookup, prevent referrer leaking, short retention and authorized details.
**Hợp đồng đầu ra / acceptance:** Anon token returns only safe fields; sensitive contact not exposed.
**Negative regression bắt buộc:** Token guessing yields name/phone -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `status-token-test`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R6-007 — RBPC commercial transparency (P2)
**Baseline file:** `frontend/src/lib/rbpc/inquiries.ts` — [EXISTING PATH]. **Dependency:** `R6-005`.
**Mục tiêu thay đổi:** Explicit inquiry_only, no online charge, price provenance and partner consent.
**Hợp đồng đầu ra / acceptance:** User knows not a paid/confirmed booking; provider verifies contact.
**Negative regression bắt buộc:** Demo partner priced as verified real operator -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `visitor-disclosure-e2e`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
