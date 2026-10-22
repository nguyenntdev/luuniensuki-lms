# V2 engineering tickets R4 — extracted original

### R4-001 — Pseudonymized survey data import (P0)
**Baseline file:** `data` — [EXISTING PATH]. **Dependency:** `R0-001`.
**Mục tiêu thay đổi:** Import Google Forms export into isolated vault after owner supplies approved version.
**Hợp đồng đầu ra / acceptance:** N raw, missing, duplicates, item wordings logged; no PII in outputs.
**Negative regression bắt buộc:** Email/phone leaks in public aggregate -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `survey-import-validation`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R4-002 — Questionnaire and skip-logic freeze (P0)
**Baseline file:** `data` — [EXISTING PATH]. **Dependency:** `R4-001`.
**Mục tiêu thay đổi:** Version original Forms wording, answer codes, maximum choices, skip paths.
**Hợp đồng đầu ra / acceptance:** Can reconstruct exact options and who could answer each item.
**Negative regression bắt buộc:** Same label in two survey revisions silently merged -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `survey-dictionary.yaml`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R4-003 — Reproduce 1,502 tables (P0)
**Baseline file:** `data` — [EXISTING PATH]. **Dependency:** `R4-002`.
**Mục tiêu thay đổi:** Versioned deterministic aggregation with item-level denominator and rounding.
**Hợp đồng đầu ra / acceptance:** All published counts match or discrepancy log specifies reason.
**Negative regression bắt buộc:** Hardcoded 1,502 hides missing valid responses -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `paper-table-reproduction`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R4-004 — Resolve multi-select 4,506 (P0)
**Baseline file:** `data` — [EXISTING PATH]. **Dependency:** `R4-003`.
**Mục tiêu thay đổi:** Count per-person #checked, verify max3 rule and other choices.
**Hợp đồng đầu ra / acceptance:** Histogram and 4506 reconciliation audit report signed.
**Negative regression bắt buộc:** Assume user picked exactly 3 without raw check -> blocked.
**Evidence cần commit vào CI hoặc evidence vault:** `multi-select-audit`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R4-005 — Reconcile awareness vs source channel (P1)
**Baseline file:** `data` — [EXISTING PATH]. **Dependency:** `R4-002`.
**Mục tiêu thay đổi:** Compare literal question wording, branching, dates/populations for 544 vs 812.
**Hợp đồng đầu ra / acceptance:** Written interpretation grounded in original form version.
**Negative regression bắt buộc:** Calling contradiction without questionnaire proof -> fail review.
**Evidence cần commit vào CI hoặc evidence vault:** `question-wording-audit`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R4-006 — Research code/data snapshot (P1)
**Baseline file:** `data` — [EXISTING PATH]. **Dependency:** `R4-003`.
**Mục tiêu thay đổi:** Store source SHA, transformation commit, dictionary version and aggregate output.
**Hợp đồng đầu ra / acceptance:** Peer reviewer can reproduce tables on authorized anonymized data.
**Negative regression bắt buộc:** Manual spreadsheet edits without script/diff -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `analysis-release-bundle`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R4-007 — Consent and ethics audit (P1)
**Baseline file:** `docs` — [EXISTING PATH]. **Dependency:** `R4-001`.
**Mục tiêu thay đổi:** Document status/permissions separately; obtain verifiable records from custodian.
**Hợp đồng đầu ra / acceptance:** Ethical report accurately says verified/pending/not applicable with basis.
**Negative regression bắt buộc:** Missing proof reworded as “approved” -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `ethics-traceability`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R4-008 — Descriptive school/grade analysis (P2)
**Baseline file:** `data` — [EXISTING PATH]. **Dependency:** `R4-003`.
**Mục tiêu thay đổi:** Only if respondent-level school/grade and sampling allow; analyze with clustering caveats.
**Hợp đồng đầu ra / acceptance:** Methods, missing counts, limitations documented; no causal claims.
**Negative regression bắt buộc:** Unadjusted school comparison marketed nationally -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `survey-strata-notebook`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
