# V2 engineering tickets R5 — extracted original

### R5-001 — AI approved-source indexing (P0)
**Baseline file:** `backend/services/history_tutor.py` — [EXISTING PATH]. **Dependency:** `R1-008`.
**Mục tiêu thay đổi:** Create retrieval releases from expert/editor reviewed claim snapshots only.
**Hợp đồng đầu ra / acceptance:** Queries never surface unreviewed/rejected/disputed as authoritative.
**Negative regression bắt buộc:** Seed ai_generated leaks to answers -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `rag-index-manifest`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R5-002 — Citation structural validator (P0)
**Baseline file:** `backend/services/history_tutor.py` — [EXISTING PATH]. **Dependency:** `R5-001`.
**Mục tiêu thay đổi:** Validate claim+source+locator+version per generated sentence before deliver.
**Hợp đồng đầu ra / acceptance:** Unsupported historical assertions rejected or answer abstains.
**Negative regression bắt buộc:** Fabricated citation passes because looks plausible -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `citation-gold-tests`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R5-003 — AI prompt injection suite (P0)
**Baseline file:** `backend/services/rbpc_ai.py` — [EXISTING PATH]. **Dependency:** `R5-001`.
**Mục tiêu thay đổi:** Red-team corpus in source excerpts, multi-turn, role spoofing, exfiltration attempts.
**Hợp đồng đầu ra / acceptance:** Attack strings do not become system commands or leak secrets.
**Negative regression bắt buộc:** “Ignore previous instruction” inside source changes system behavior -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `ai-redteam-results`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R5-004 — AI abstention and uncertainty UX (P1)
**Baseline file:** `frontend/src/app` — [EXISTING PATH]. **Dependency:** `R5-002`.
**Mục tiêu thay đổi:** Answer with citations or explicit insufficient-evidence, claim type labels.
**Hợp đồng đầu ra / acceptance:** No-context question does not hallucinate; reader sees what is unknown.
**Negative regression bắt buộc:** Source unavailable yet answer confident -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `ai-abstention-e2e`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R5-005 — Independent AI evaluation (P1)
**Baseline file:** `docs/rbpc/AI_EVAL.md` — [EXISTING PATH]. **Dependency:** `R5-003`.
**Mục tiêu thay đổi:** Curate gold cases, human ratings, threshold, reproducible eval release.
**Hợp đồng đầu ra / acceptance:** Metrics accompanied by denominator, source snapshot and adjudications.
**Negative regression bắt buộc:** Internal self-claim 100% without independent test cannot release.
**Evidence cần commit vào CI hoặc evidence vault:** `ai-evaluation-report`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R5-006 — AI tutor classroom boundary (P2)
**Baseline file:** `backend/routers/history_tutor.py` — [EXISTING PATH]. **Dependency:** `R5-001`.
**Mục tiêu thay đổi:** Prevent student prompt/context from exposing other classes or private assignments.
**Hợp đồng đầu ra / acceptance:** Context retrieval respects class permission; logs redact data.
**Negative regression bắt buộc:** Other student essay retrieved in prompt -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `ai-classroom-authz`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
