# V2 engineering tickets R7 — extracted original

### R7-001 — CALL course objective definition (P1)
**Baseline file:** `frontend/src/lib/rbpc/learnModules.ts` — [EXISTING PATH]. **Dependency:** `R3-001`.
**Mục tiêu thay đổi:** Define language target, reading/vocabulary tasks, source-approved content, SME review.
**Hợp đồng đầu ra / acceptance:** Each CALL module has actual language objectives and tests.
**Negative regression bắt buộc:** Only bilingual interface counted as CALL outcome -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `call-curriculum-review`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R7-002 — Source-grounded Hán–Nôm learning (P1)
**Baseline file:** `data/05_Data_CaoDinh.json` — [EXISTING PATH]. **Dependency:** `R1-004`.
**Mục tiêu thay đổi:** Link inscription image, original verified transcription, transliteration, translation, feedback.
**Hợp đồng đầu ra / acceptance:** Every published Hán–Nôm question has reviewer, crop and locator.
**Negative regression bắt buộc:** AI seed character treated as authentic -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `han-nom-call-test`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R7-003 — CALL evaluation protocol (P2)
**Baseline file:** `docs` — [EXISTING PATH]. **Dependency:** `R7-001`.
**Mục tiêu thay đổi:** Pilot reading/vocab tasks with language rubric/measurement, consent as appropriate.
**Hợp đồng đầu ra / acceptance:** Outcomes measure language explicitly; dataset separate from historical survey.
**Negative regression bắt buộc:** 94% 3D interest used as language gains -> invalid.
**Evidence cần commit vào CI hoặc evidence vault:** `call-protocol`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R7-004 — ICTIM visitor-study boundary (P2)
**Baseline file:** `docs` — [EXISTING PATH]. **Dependency:** `R6-007`.
**Mục tiêu thay đổi:** Create separate visitor/experience instruments if tourism outcome asserted.
**Hợp đồng đầu ra / acceptance:** Only report visitor outcome after valid visitor data collected.
**Negative regression bắt buộc:** 1,502 students labeled tourists -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `ictim-study-protocol`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R7-005 — Q2 reproducible evidence bundle (P2)
**Baseline file:** `docs` — [EXISTING PATH]. **Dependency:** `R4-006`.
**Mục tiêu thay đổi:** Version-lock ELLO, sources, app, dataset, rubric and claim register.
**Hợp đồng đầu ra / acceptance:** Each figure and claim maps to immutable release and analysis artifact.
**Negative regression bắt buộc:** Screenshots from another release labeled as experiment -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `paper-evidence-pack`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.
### R7-006 — EAUT architecture benchmarks (P2)
**Baseline file:** `backend-rust` — [EXISTING PATH]. **Dependency:** `R0-010`.
**Mục tiêu thay đổi:** Benchmark architecture against defined baselines with build/deploy reliability.
**Hợp đồng đầu ra / acceptance:** Latency/load/complexity measures repeatable and limits stated.
**Negative regression bắt buộc:** Claims “high scalability” without measured workload -> fail.
**Evidence cần commit vào CI hoặc evidence vault:** `architecture-benchmark`. Đính kèm log test, fixture ID, bản thay đổi schema/API nếu có, người duyệt và `release_gate` liên quan.
**Bước thực hiện đề xuất:** (1) chụp baseline và viết failing test; (2) cập nhật design/contract; (3) triển khai nhỏ trong domain owner; (4) chạy unit/integration/e2e phù hợp; (5) kiểm security/rights/science impact; (6) staging smoke; (7) PR review; (8) release gate + rollback procedure.
**Definition of Done:** test pass trên môi trường được mô tả; migration/backfill idempotent nếu có; không làm sai dữ liệu quá khứ; log/audit/metrics đầy đủ; tài liệu vận hành và trạng thái thực tế được cập nhật.

**Tổng tickets V2:** 64; phân bố ưu tiên P0: 29, P1: 26, P2: 9. Mọi effort và ETA cần xác nhận sau khi kiểm CI thực tế.

---

