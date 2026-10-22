# V2 engineering tickets R1 — extracted original

### R1-001 — Create source snapshot ledger (P0)
**Baseline file:** `data/05_Data_CaoDinh.json` — [EXISTING PATH]. **Dependency:** `R0-001`.
**Mục tiêu thay đổi:** Hash 9 JSON, 162 JPG; giữ raw và bản biến đổi tách nhau.
**Hợp đồng đầu ra / acceptance:** Pipeline report 9x18 và total 162, rerun idempotent.
**Negative regression bắt buộc:** 17/19 item hay duplicate raw id block release.
**Evidence cần commit vào CI hoặc evidence vault:** `162-import-manifest`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R1-002 — Resolve urn vs relief identities (P0)
**Baseline file:** `data/05_Data_CaoDinh.json` — [EXISTING PATH]. **Dependency:** `R1-001`.
**Mục tiêu thay đổi:** Map canonical 9 urn và relief thực; phân biệt raw pseudo-record với motif đã xác minh.
**Hợp đồng đầu ra / acceptance:** Identity board có `record_kind`, `urn_id`, `relief_id` và reviewer cho mỗi row.
**Negative regression bắt buộc:** Không tự coi “Cao Đỉnh” metadata là relief nếu hồ sơ nguồn không xác nhận.
**Evidence cần commit vào CI hoặc evidence vault:** `identity-adjudication.csv`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R1-003 — Historical source registry coverage (P0)
**Baseline file:** `backend/history_models.py` — [EXISTING PATH]. **Dependency:** `R1-002`.
**Mục tiêu thay đổi:** Gắn bibliographic source và locator cho từng fact/claim ưu tiên.
**Hợp đồng đầu ra / acceptance:** Approved factual claims có ít nhất một binding locator hợp lệ.
**Negative regression bắt buộc:** Claim không nguồn tuyệt đối không được published/AI-authority.
**Evidence cần commit vào CI hoặc evidence vault:** `source-coverage-report`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R1-004 — Han-Nom review pipeline (P0)
**Baseline file:** `data/05_Data_CaoDinh.json` — [EXISTING PATH]. **Dependency:** `R1-002`.
**Mục tiêu thay đổi:** OCR/AI chỉ gợi ý; Hán-Nôm SME đối chiếu crop, phiên âm, bản dịch, uncertainty.
**Hợp đồng đầu ra / acceptance:** 158 có seed script được rà; 4 missing flagged, 9 first-row `艇` reviewed individually.
**Negative regression bắt buộc:** Không batch sửa ký tự nghi vấn mà không lưu ảnh và reviewer.
**Evidence cần commit vào CI hoặc evidence vault:** `han-nom-review-ledger`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R1-005 — Split atomic claims (P0)
**Baseline file:** `backend/history_models.py` — [EXISTING PATH]. **Dependency:** `R1-003`.
**Mục tiêu thay đổi:** Trích một paragraph thành mệnh đề factual/interpretative/traditional; origin ai_generated.
**Hợp đồng đầu ra / acceptance:** Mỗi claim có class, status, source/need-source, reviewer.
**Negative regression bắt buộc:** Mệnh đề diễn giải bị gắn factual/verified không nguồn -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `atomic-claims-diff`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R1-006 — Two-person approval (P0)
**Baseline file:** `backend/history_models.py` — [EXISTING PATH]. **Dependency:** `R1-005`.
**Mục tiêu thay đổi:** Reviewer khác người tạo, append-only rationale, permissions riêng.
**Hợp đồng đầu ra / acceptance:** Self-approval 403, expert approval has audit event and source locator.
**Negative regression bắt buộc:** Lặp request tạo hai approval hoặc làm thay đổi audit bị chặn.
**Evidence cần commit vào CI hoặc evidence vault:** `approval-workflow-tests`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R1-007 — Canonical taxonomy and aliases (P1)
**Baseline file:** `backend/history_models.py` — [EXISTING PATH]. **Dependency:** `R1-002`.
**Mục tiêu thay đổi:** Giữ raw categories 9 nhãn, lập taxonomy versioned, aliases and transliteration.
**Hợp đồng đầu ra / acceptance:** Search tìm tên khác nhau map đúng ID mà không merge dị danh xung đột.
**Negative regression bắt buộc:** Tên trùng ở hai urn không auto dedupe.
**Evidence cần commit vào CI hoặc evidence vault:** `taxonomy-map.yaml`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R1-008 — Content release and provenance (P1)
**Baseline file:** `backend/history_models.py` — [EXISTING PATH]. **Dependency:** `R1-006`.
**Mục tiêu thay đổi:** Immutable snapshot entity+claim+source+asset hash; release signed by publisher.
**Hợp đồng đầu ra / acceptance:** Old lesson keeps old source version; diff and rollback explainable.
**Negative regression bắt buộc:** Sửa live claim làm đổi bài học đã chấm -> regression fail.
**Evidence cần commit vào CI hoặc evidence vault:** `catalog-release-manifest`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R1-009 — Dispute and correction workflow (P1)
**Baseline file:** `backend/history_models.py` — [EXISTING PATH]. **Dependency:** `R1-008`.
**Mục tiêu thay đổi:** Hỗ trợ challenged/disputed/withdrawn, source contrary; notify affected lessons/AI.
**Hợp đồng đầu ra / acceptance:** Disputed claim hidden from authoritative answer and flagged in editor.
**Negative regression bắt buộc:** AI dùng claim revoked qua cache bị chặn.
**Evidence cần commit vào CI hoặc evidence vault:** `dispute-workflow-e2e`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R1-010 — 9x18 reviewer dashboard (P1)
**Baseline file:** `frontend/src/app` — [EXISTING PATH]. **Dependency:** `R1-003`.
**Mục tiêu thay đổi:** View raw/mapped/sourced/reviewed/published per record with blockers.
**Hợp đồng đầu ra / acceptance:** Từng ô 9x18 drill-down to source and decision; export full unresolved list.
**Negative regression bắt buộc:** Counts 162 raw bị trình bày như 162 expert verified -> UI test fail.
**Evidence cần commit vào CI hoặc evidence vault:** `coverage-ui-e2e`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
