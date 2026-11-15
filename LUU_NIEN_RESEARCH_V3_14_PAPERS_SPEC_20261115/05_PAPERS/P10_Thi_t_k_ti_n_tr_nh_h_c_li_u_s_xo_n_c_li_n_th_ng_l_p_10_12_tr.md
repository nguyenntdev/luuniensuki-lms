# P10 — Thiết kế tiến trình học liệu số xoắn ốc liên thông lớp 10–12 trong giáo dục di sản địa phương
**Venue định hướng:** Tạp chí Giáo dục (HĐGSNN); luôn xác minh CFP, rank 2027 và fit. **Ưu tiên:** P0. **Trạng thái V3:** PEDAGOGICAL_VALIDATION_REQUIRED.
**Reuse V1/V2:** LN-01 planner; heritage lesson records, curriculum mappings need expert verification. **Không được suy từ đó rằng bài P đã có thực nghiệm ngoài.**

## 1. Đóng góp riêng và ranh giới xuất bản
P10 là công trình thiết kế và thẩm định sư phạm, không tuyên bố tối ưu thuật toán như P02.

**Research Question.** Tính liên tục, tăng độ sâu nhận thức và phù hợp CTGDPT của chuỗi học liệu di sản số theo 3 lớp được chuyên gia đánh giá như thế nào?

**H0 bắt buộc công bố nếu không bác bỏ:** Chuỗi xoắn ốc không có ưu thế nhất quán theo rubric so với chuỗi chuẩn do giáo viên xây dựng.

**Điều kiện chỉ nhận là novelty nếu đạt:** phương pháp/protocol mới được định nghĩa rõ, so sánh thật với baseline liên quan, có failure analysis và không trùng primary outcome của P khác. Nếu chỉ thắng sanity baseline hoặc rules-oracle synthetic thì không được gọi SOTA.

## 2. Nguồn dữ liệu ngoài và khả năng suy luận
- **HueSources** — https://www.hueworldheritage.org.vn/. Gate: evaluate exactly which available fields measure this RQ; document DOI, license, version and checksum.

- Bài toán chỉ được coi DATA_READY khi có source/version/license/hashes + exact schema for task outcome.
- Cần đặt trường `status: BLOCKED` nếu data không có nhãn đúng mục tiêu; không tự tạo "real ground truth" từ heuristic.
- Ràng buộc tách tập: Tách bộ học liệu thiết kế và bộ chuyên gia đánh giá; ẩn tên phương pháp khi chấm; không dùng HS thử nghiệm khi thiếu duyệt đạo đức.
- T3 synthetic V2 chỉ dùng như regression/canary, không gộp vào external test score để nâng n.

## 3. Formal method and implementation contract
**Candidate mechanism (hypothesis, not proven):** Phân tích CTGDPT/CTGDDP theo năm học; xây dựng ma trận mục tiêu—nguồn—hoạt động—đánh giá; thiết kế chuỗi xoắn ốc qua các cấp độ Bloom; Delphi/chấm độc lập của giáo viên.

Requirements for code agent:
1. Define exact input/output dataclasses and type/constraint invariants, with configurable `NOT_APPLICABLE` and `ABSTAIN` distinct from negative predictions.
2. Specify objective/equations or state transition rules in `METHOD.md` before writing engine; separate learned weights and fixed constraints.
3. Make all learned parameters fit only on permitted training data. For optimization methods identify certificates, heuristics and runtime caps.
4. Record which components are genuinely novel versus standard reused libraries; cite originals in implementation and manuscript.
5. Add adversarial/mutation tests; never use hidden benchmark or holdout oracle in model class, prompts or error messages.
6. Publish algorithm pseudocode, computational complexity, limitations, compute and artifacts required for replication.

**Proposed modules (suggested, not existing):** `curriculum/spiral_grade_10_12.csv`, `study/P10_expert_form.md`, `analysis/P10_content_validity.py`, `reports/P10_alignment_table.tex`.

## 4. Baseline matrix (not a claim that they are already implemented)
- B00: chuỗi tuyến tính theo niên đại — pin implementation/version; confirm target task parity; record if adaptation alters authors' method.
- B01: giáo án phổ biến — pin implementation/version; confirm target task parity; record if adaptation alters authors' method.
- B02: chuỗi theo chủ đề không xoắn ốc — pin implementation/version; confirm target task parity; record if adaptation alters authors' method.
- B03: expert-designed reference — pin implementation/version; confirm target task parity; record if adaptation alters authors' method.

Benchmark rules: same input information, preprocessing, hyperparameter search, model training selection, inference budgets and split manifests; verify codes/weights/licenses. Strongest compatible upstream baseline must be run or a dated, reproducible BLOCKED rationale must appear in results. Literature search shall add stronger 2026 papers if discovered.

## 5. Ablations and falsification counterexamples
- **A1:** bỏ cầu nối lớp (same split and compute; report expected failure family without assuming it will fail).
- **A2:** không nâng độ sâu Bloom (same split and compute; report expected failure family without assuming it will fail).
- **A3:** không truy nguyên sử liệu (same split and compute; report expected failure family without assuming it will fail).
- **A4:** chuỗi ngẫu nhiên (same split and compute; report expected failure family without assuming it will fail).

**High-risk strata / required stress suites**
- kiến thức vượt lớp: create deterministic generator and external data slice where applicable; do not declare outcomes before running.
- phụ thuộc nguồn chưa thẩm định: create deterministic generator and external data slice where applicable; do not declare outcomes before running.
- hai hoạt động đạt cùng mục tiêu: create deterministic generator and external data slice where applicable; do not declare outcomes before running.
- không lặp lại có tiến triển: create deterministic generator and external data slice where applicable; do not declare outcomes before running.

**Fail-closed:** no stratum/ablation family may be omitted because proposed method fails; no editing frozen test labels; evidence includes confusion matrices and failure logs by stratum.

## 6. Evaluation and inference
**Primary/secondary metrics (register one primary and fixed contrast prior to testing):** Curriculum alignment;spiral progression rubric;expert CVI;interrater agreement;teacher feasibility;revision yield.

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
- `P10-T01` Research question, estimand, null and nearest prior work: **Freeze hypothesis, title and collision checks with other P papers**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T02` Dataset rights assessment and source selection: **Source URLs, license snapshot, version, hash; restrict unlicensed files**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T03` Data and target schema definition: **Type-check units/labels, missingness, group and temporal keys**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T04` Raw ingestion and immutable provenance: **SHA256 for raw + processed, source snapshot reproducibility**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T05` Leakage-proof preprocessing and split: **No future, group cross-over, duplicates or gold in train features**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T06` External descriptive baseline and distribution checks: **Report coverage/missingness/shift before fitting anything**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T07` Strong classical baseline with matched inputs: **Same data/splits and fair tuning/compute budget**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T08` Closest published implementation or honest BLOCKED card: **Exact version/license/reimplementation status disclosed**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T09` Method implementation and invariant proofs: **Unit contract, algebra/optimizer state, typed failures**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T10` Independent ablations and mutation counterexamples: **Ablations remove named mechanism; counterexamples separate**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T11` Training/calibration with frozen hyperparameter budget: **Model cards, GPU/CPU/time, no frozen test tuning**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T12` Full preregistered matrix on external data: **Every cell has manifest, predictions and strict exit code**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T13` Robustness, shift, subgroup, resource and stress: **Report all failure strata, not only positive average**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T14` Statistical tests and uncertainty: **Correct unit/CI/multiplicity, effect size, negative result**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T15` Source-to-table generator and independent replication: **No hand-entered metrics; checksum round trip**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T16` Scientific failure review and collision audit: **Falsification and salami-slicing decisions preserved**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T17` Manuscript methods/limitations/figures/appendix build: **Evidence IDs for every numeric and causal claim**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T18` External reviewer reproduction and frozen release: **Rerun from clean clone, validate artifacts and open issues**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T19` Ethics/human annotation/license approval (human-only): **Documented actual signatures/approvals, no simulated success**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T20` Novelty and nearest-work signoff (research lead): **Most recent full texts and closest overlap matrix**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.
- `P10-T21` Coauthor/venue/submission signoff (human-only): **Authorship, venue fit, full rights and formatting approval**. Output under `research_v3/` and `research_artifacts_v3/`; status TODO until executed.

**Done means:** all 21 numbered tasks have verifiable artifacts and human signoffs where indicated, the novelty gate passes and release status is legitimately `SCIENTIFIC_REVIEW_READY` / `SUBMISSION_READY`. Unverifiable human tasks remain blocked, never silently accepted.
