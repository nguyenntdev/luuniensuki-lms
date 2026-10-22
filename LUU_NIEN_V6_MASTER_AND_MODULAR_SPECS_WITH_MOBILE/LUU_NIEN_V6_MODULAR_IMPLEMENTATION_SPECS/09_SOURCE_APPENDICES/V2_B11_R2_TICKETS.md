# V2 engineering tickets R2 — extracted original

### R2-001 — Rights predicate fail-closed (P0)
**Baseline file:** `backend/routers/heritage.py` — [EXISTING PATH]. **Dependency:** `R1-003`.
**Mục tiêu thay đổi:** Tạo một `can_serve_asset` allowlist cho embed/hosting/commercial/purpose/expiry.
**Hợp đồng đầu ra / acceptance:** Unreviewed/unknown/blocked/expired assets absent from public lists and 3D APIs.
**Negative regression bắt buộc:** Predicate `!= blocked` trở lại -> tests catch.
**Evidence cần commit vào CI hoặc evidence vault:** `rights-enum-contract-tests`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R2-002 — Asset grant evidence vault (P0)
**Baseline file:** `backend/models_rbpc.py` — [EXISTING PATH]. **Dependency:** `R2-001`.
**Mục tiêu thay đổi:** Gắn grant proof/reference, holder, scope, rights expiry, withdrawal.
**Hợp đồng đầu ra / acceptance:** Public asset has right-proof object and valid permission for explicit purpose.
**Negative regression bắt buộc:** Chỉ có screenshot hoặc URL không được đánh dấu commercial cleared.
**Evidence cần commit vào CI hoặc evidence vault:** `media-rights-ledger`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R2-003 — GLB single origin and hash (P1)
**Baseline file:** `frontend/public/assets/models` — [EXISTING PATH]. **Dependency:** `R2-001`.
**Mục tiêu thay đổi:** Inventory duplicates, manifest original/LODs/hotspots, move via safe redirect plan.
**Hợp đồng đầu ra / acceptance:** App views same content hash; old URLs remain compatible during transition.
**Negative regression bắt buộc:** Missing mesh but has_3d true bị test chặn.
**Evidence cần commit vào CI hoặc evidence vault:** `glb-hash-and-lod-report`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R2-004 — 2D fallback on all lessons (P1)
**Baseline file:** `frontend/src/app` — [EXISTING PATH]. **Dependency:** `R2-003`.
**Mục tiêu thay đổi:** Implement image/text route and equivalent inquiry task if WebGL/AR fails.
**Hợp đồng đầu ra / acceptance:** Keyboard learner finishes same core historical task without 3D.
**Negative regression bắt buộc:** 3D load timeout blocks assignment -> e2e fail.
**Evidence cần commit vào CI hoặc evidence vault:** `accessibility-fallback-test`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R2-005 — Hotspot geometry calibration (P1)
**Baseline file:** `motif-coordinates-cao-dinh.json` — [EXISTING PATH]. **Dependency:** `R2-003`.
**Mục tiêu thay đổi:** Map hotspot IDs to real relief, transform axes and bbox, reviewer for coordinates.
**Hợp đồng đầu ra / acceptance:** Every published hotspot resolves canonical relief and within bounds.
**Negative regression bắt buộc:** Legacy coordinate points to wrong urn -> visible block.
**Evidence cần commit vào CI hoặc evidence vault:** `hotspot-validation.json`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R2-006 — CDN rights revocation (P1)
**Baseline file:** `nginx.conf` — [EXISTING PATH]. **Dependency:** `R2-002`.
**Mục tiêu thay đổi:** Protected origin, invalidate served renditions on right/consent withdrawal.
**Hợp đồng đầu ra / acceptance:** After revocation no public media exposure beyond approved SLA.
**Negative regression bắt buộc:** Guessed direct object path remains public -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `cdn-revoke-drill`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R2-007 — XR performance budgets (P2)
**Baseline file:** `frontend/src/components` — [EXISTING PATH]. **Dependency:** `R2-004`.
**Mục tiêu thay đổi:** Instrument LOD choice, device memory and fallback usage; optimize assets.
**Hợp đồng đầu ra / acceptance:** Performance measured on defined mobile/desktop device matrix, track p95.
**Negative regression bắt buộc:** Marketing claim fast without measurement is prohibited.
**Evidence cần commit vào CI hoặc evidence vault:** `xr-perf-report`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
