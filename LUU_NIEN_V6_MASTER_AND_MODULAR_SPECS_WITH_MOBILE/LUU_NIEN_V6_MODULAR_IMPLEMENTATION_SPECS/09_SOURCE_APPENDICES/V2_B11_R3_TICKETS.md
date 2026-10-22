# V2 engineering tickets R3 — extracted original

### R3-001 — ELLO entities + migrations (P0)
**Baseline file:** `backend/models.py` — [EXISTING PATH]. **Dependency:** `R1-008`.
**Mục tiêu thay đổi:** Add source-linked learning object aggregate and release snapshot, via additive migration.
**Hợp đồng đầu ra / acceptance:** Can create draft ELLO referring approved entity; schema survives migration rerun.
**Negative regression bắt buộc:** Publish without sources/rubric/fallback impossible.
**Evidence cần commit vào CI hoặc evidence vault:** `ello-schema-tests`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R3-002 — Teacher ELLO authoring wizard (P0)
**Baseline file:** `frontend/src/app` — [EXISTING PATH]. **Dependency:** `R3-001`.
**Mục tiêu thay đổi:** Wizard entity -> claim -> source -> representation -> task -> feedback -> publish.
**Hợp đồng đầu ra / acceptance:** Teacher can create, preview and submit review without DB editing.
**Negative regression bắt buộc:** Unauthorized non-teacher publish -> 403.
**Evidence cần commit vào CI hoặc evidence vault:** `ello-author-e2e`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R3-003 — Student inquiry runner (P0)
**Baseline file:** `frontend/src/app/learn/page.tsx` — [EXISTING PATH]. **Dependency:** `R3-002`.
**Mục tiêu thay đổi:** Six stages with observation, provisional claim, source comparison, response, revision.
**Hợp đồng đầu ra / acceptance:** Saves versioned answers and source IDs; restore after refresh.
**Negative regression bắt buộc:** Source drawer empty yet allows final evidence claim -> block/guide.
**Evidence cần commit vào CI hoặc evidence vault:** `student-inquiry-e2e`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R3-004 — Historical reasoning rubric (P0)
**Baseline file:** `backend/services/history_learning.py` — [EXISTING PATH]. **Dependency:** `R3-001`.
**Mục tiêu thay đổi:** Add rubric 0..3 per dimension, examples, teacher score and feedback; separate from MCQ.
**Hợp đồng đầu ra / acceptance:** Manual rater can justify evidence scores, export scoring audit.
**Negative regression bắt buộc:** Auto exact match used for historical essay score -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `rubric-scoring-tests`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R3-005 — Immutable assignment version (P1)
**Baseline file:** `backend/models.py` — [EXISTING PATH]. **Dependency:** `R3-001`.
**Mục tiêu thay đổi:** Assignment points to release, not mutable draft, preserve source text and question version.
**Hợp đồng đầu ra / acceptance:** Old attempt readable after source update; new assignment uses new release.
**Negative regression bắt buộc:** Update draft changes old grade snapshot -> regression.
**Evidence cần commit vào CI hoặc evidence vault:** `assignment-version-test`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R3-006 — Draft sync and idempotent submit (P1)
**Baseline file:** `frontend/src/app/learn/page.tsx` — [EXISTING PATH]. **Dependency:** `R3-003`.
**Mục tiêu thay đổi:** Offline-safe queue with clear unsent state and server receipt; conflict via ETag.
**Hợp đồng đầu ra / acceptance:** Network failure shows unsent, retry creates 1 attempt/submit.
**Negative regression bắt buộc:** Client toast “submitted” without server receipt -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `offline-submit-test`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R3-007 — Two-rater blinded research scoring (P1)
**Baseline file:** `backend/models.py` — [EXISTING PATH]. **Dependency:** `R3-004`.
**Mục tiêu thay đổi:** Optional rater assignment and independent score snapshots; adjudication.
**Hợp đồng đầu ra / acceptance:** Raters cannot view each other's initial score; agreement export reproducible.
**Negative regression bắt buộc:** Rater identity leaked in blinded phase -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `rater-workflow-tests`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R3-008 — Teacher classroom authorization (P1)
**Baseline file:** `backend/routers/classrooms.py` — [EXISTING PATH]. **Dependency:** `R3-001`.
**Mục tiêu thay đổi:** Scope class/assignment/progress to authorized teacher and school tenancy.
**Hợp đồng đầu ra / acceptance:** Teacher A cannot grade/view unrelated class B.
**Negative regression bắt buộc:** Guessing assignment UUID grants read -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `classroom-idortests`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R3-009 — Curriculum objective tagging (P1)
**Baseline file:** `backend/models.py` — [EXISTING PATH]. **Dependency:** `R3-001`.
**Mục tiêu thay đổi:** Versioned learning objectives with grade level and alignment rationale.
**Hợp đồng đầu ra / acceptance:** Every published lesson includes objectives and rubric criterion mapping.
**Negative regression bắt buộc:** Content has flashy 3D but no measurable objective -> fail publish.
**Evidence cần commit vào CI hoặc evidence vault:** `curriculum-alignment-report`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R3-010 — FSRS vs historical inquiry separation (P2)
**Baseline file:** `backend/services/spaced_repetition.py` — [EXISTING PATH]. **Dependency:** `R3-004`.
**Mục tiêu thay đổi:** Keep spaced repetition for recall, reasoning assessed by rubric and transfer task.
**Hợp đồng đầu ra / acceptance:** Dashboard separates recall mastery and evidence reasoning.
**Negative regression bắt buộc:** Answer tap count displayed as reasoning gain -> regression.
**Evidence cần commit vào CI hoặc evidence vault:** `learning-metrics-spec`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
