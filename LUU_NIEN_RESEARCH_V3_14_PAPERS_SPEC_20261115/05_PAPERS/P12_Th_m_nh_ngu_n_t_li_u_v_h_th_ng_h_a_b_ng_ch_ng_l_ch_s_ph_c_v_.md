# P12 — Thẩm định nguồn tư liệu và hệ thống hóa bằng chứng lịch sử phục vụ dạy học di sản Cửu Đỉnh–Đại Nội Huế
**Venue định hướng:** Tạp chí Khoa học Đại học Huế: KHXH&NV (chỉ bài thuộc Giáo dục học) (HĐGSNN); luôn xác minh CFP, rank 2027 và fit. **Ưu tiên:** P1. **Trạng thái V3:** HUMAN_HISTORICAL_REVIEW_REQUIRED.
**Reuse V1/V2:** LN-04/08 source gates; historical claim ledger needs human source scrutiny. **Không được suy từ đó rằng bài P đã có thực nghiệm ngoài.**

## 1. Đóng góp riêng và ranh giới xuất bản
Đóng góp quản trị và chất lượng sử liệu giáo dục, khác P09 là tương tác giao diện.

**Research Question.** Quy trình thẩm định nguồn—mệnh đề—trích dẫn theo phiên bản có nâng chất lượng học liệu giáo dục di sản so với thư mục thông thường không?

**H0 bắt buộc công bố nếu không bác bỏ:** Provenance ledger không giảm sai sót trích dẫn hoặc chi phí thẩm định so với checklist tối thiểu.

**Điều kiện chỉ nhận là novelty nếu đạt:** phương pháp/protocol mới được định nghĩa rõ, so sánh thật với baseline liên quan, có failure analysis và không trùng primary outcome của P khác. Nếu chỉ thắng sanity baseline hoặc rules-oracle synthetic thì không được gọi SOTA.

## 2. Nguồn dữ liệu ngoài và khả năng suy luận
- **HueSources** — https://www.hueworldheritage.org.vn/. Gate: evaluate exactly which available fields measure this RQ; document DOI, license, version and checksum.
- **Europeana** — https://pro.europeana.eu/page/apis. Gate: evaluate exactly which available fields measure this RQ; document DOI, license, version and checksum.

- Bài toán chỉ được coi DATA_READY khi có source/version/license/hashes + exact schema for task outcome.
- Cần đặt trường `status: BLOCKED` nếu data không có nhãn đúng mục tiêu; không tự tạo "real ground truth" từ heuristic.
- Ràng buộc tách tập: Giữ tập mệnh đề huấn luyện thẩm định tách tập đánh giá; blind source label; ghi provenance và phiên bản gốc.
- T3 synthetic V2 chỉ dùng như regression/canary, không gộp vào external test score để nâng n.

## 3. Formal method and implementation contract
**Candidate mechanism (hypothesis, not proven):** Thiết kế bộ mã provenance từng mệnh đề; phân biệt sử liệu gốc, thứ cấp, dịch thuật, bản trưng bày; hai chuyên gia đối chiếu và ghi bất đồng/chỉnh sửa.

Requirements for code agent:
1. Define exact input/output dataclasses and type/constraint invariants, with configurable `NOT_APPLICABLE` and `ABSTAIN` distinct from negative predictions.
2. Specify objective/equations or state transition rules in `METHOD.md` before writing engine; separate learned weights and fixed constraints.
3. Make all learned parameters fit only on permitted training data. For optimization methods identify certificates, heuristics and runtime caps.
4. Record which components are genuinely novel versus standard reused libraries; cite originals in implementation and manuscript.
5. Add adversarial/mutation tests; never use hidden benchmark or holdout oracle in model class, prompts or error messages.
6. Publish algorithm pseudocode, computational complexity, limitations, compute and artifacts required for replication.

**Proposed modules (suggested, not existing):** `heritage/claims_registry.csv`, `heritage/sources_registry.csv`, `study/P12_double_review.md`, `reports/P12_conflict_log.md`.

## 4. Baseline matrix (not a claim that they are already implemented)
- B00: bảng nguồn truyền thống — pin implementation/version; confirm target task parity; record if adaptation alters authors' method.
- B01: thư mục hyperlink — pin implementation/version; confirm target task parity; record if adaptation alters authors' method.
- B02: metadata-only provenance — pin implementation/version; confirm target task parity; record if adaptation alters authors' method.
- B03: single-editor review — pin implementation/version; confirm target task parity; record if adaptation alters authors' method.

Benchmark rules: same input information, preprocessing, hyperparameter search, model training selection, inference budgets and split manifests; verify codes/weights/licenses. Strongest compatible upstream baseline must be run or a dated, reproducible BLOCKED rationale must appear in results. Literature search shall add stronger 2026 papers if discovered.

## 5. Ablations and falsification counterexamples
- **A1:** không lịch sử phiên bản (same split and compute; report expected failure family without assuming it will fail).
- **A2:** không truy mệnh đề (same split and compute; report expected failure family without assuming it will fail).
- **A3:** không cờ mâu thuẫn (same split and compute; report expected failure family without assuming it will fail).
- **A4:** không double review (same split and compute; report expected failure family without assuming it will fail).

**High-risk strata / required stress suites**
- trích dẫn thiếu trang: create deterministic generator and external data slice where applicable; do not declare outcomes before running.
- Hán-Nôm nhiều bản dịch: create deterministic generator and external data slice where applicable; do not declare outcomes before running.
- bản sửa sai: create deterministic generator and external data slice where applicable; do not declare outcomes before running.
- nhầm họa tiết/đỉnh: create deterministic generator and external data slice where applicable; do not declare outcomes before running.
- bản quyền ảnh: create deterministic generator and external data slice where applicable; do not declare outcomes before running.

**Fail-closed:** no stratum/ablation family may be omitted because proposed method fails; no editing frozen test labels; evidence includes confusion matrices and failure logs by stratum.

## 6. Evaluation and inference
**Primary/secondary metrics (register one primary and fixed contrast prior to testing):** Verified claim rate;unsupported claims;citation specificity;annotation agreement;editor time;conflict resolution rate.

- Choose sign/direction, exact denominator, unit of resampling, confidence intervals, effect sizes and multiplicity family in `pre_registration.yaml`; disclose test data statistical limitations.
- At least two external domains/collections when task-fit and rights allow; if only one, mark external generalization unverified.
- Compare with strongest baseline, not just untrained C0. Include sensitivity to missingness, shift, subgroup fairness, compute and null result.
- Human measures require actual approvals/ratings where relevant; algorithmic proxy outcomes cannot be reinterpreted as student gains.

## 7. Independent reviewer checklist
- Could the strongest baseline solve the same formal problem just by switching parameters? If yes, revise RQ.
- Is the data capable of estimating the endpoint and is target observable without leakage? If no, BLOCKED.
- Are ablations true removals and do mutation tests reveal the named mechanism? If no, redesign the experiment.
- Does any other paper have the same sample, RQ and principal table? If yes, MERGE_REQUIRED or explicit justified secondary study.
- Are label and source provenances versioned; does held-out evaluation run without model access to gold?
- Are negative outcomes and failure cases in supplementary results?

## 8. Task tickets — code agent execution order (all TODO unless independent new evidence supplied)
- `P12-T01` Research question, estimand, null and nearest prior work: **Freeze hypothesis, title and collision checks with other P papers**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T02` Dataset rights assessment and source selection: **Source URLs, license snapshot, version, hash; restrict unlicensed files**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T03` Data and target schema definition: **Type-check units/labels, missingness, group and temporal keys**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T04` Raw ingestion and immutable provenance: **SHA256 for raw + processed, source snapshot reproducibility**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T05` Leakage-proof preprocessing and split: **No future, group cross-over, duplicates or gold in train features**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T06` External descriptive baseline and distribution checks: **Report coverage/missingness/shift before fitting anything**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T07` Strong classical baseline with matched inputs: **Same data/splits and fair tuning/compute budget**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T08` Closest published implementation or honest BLOCKED card: **Exact version/license/reimplementation status disclosed**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T09` Method implementation and invariant proofs: **Unit contract, algebra/optimizer state, typed failures**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T10` Independent ablations and mutation counterexamples: **Ablations remove named mechanism; counterexamples separate**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T11` Training/calibration with frozen hyperparameter budget: **Model cards, GPU/CPU/time, no frozen test tuning**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T12` Full preregistered matrix on external data: **Every cell has manifest, predictions and strict exit code**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T13` Robustness, shift, subgroup, resource and stress: **Report all failure strata, not only positive average**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T14` Statistical tests and uncertainty: **Correct unit/CI/multiplicity, effect size, negative result**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T15` Source-to-table generator and independent replication: **No hand-entered metrics; checksum round trip**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T16` Scientific failure review and collision audit: **Falsification and salami-slicing decisions preserved**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T17` Manuscript methods/limitations/figures/appendix build: **Evidence IDs for every numeric and causal claim**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T18` External reviewer reproduction and frozen release: **Rerun from clean clone, validate artifacts and open issues**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T19` Ethics/human annotation/license approval (human-only): **Documented actual signatures/approvals, no simulated success**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T20` Novelty and nearest-work signoff (research lead): **Most recent full texts and closest overlap matrix**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P12-T21` Coauthor/venue/submission signoff (human-only): **Authorship, venue fit, full rights and formatting approval**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.

**Done means:** all 21 numbered tasks have verifiable artifacts and human signoffs where indicated, the novelty gate passes and release status is legitimately `SCIENTIFIC_REVIEW_READY` / `SUBMISSION_READY`. Unverifiable human tasks remain blocked, never silently accepted.
