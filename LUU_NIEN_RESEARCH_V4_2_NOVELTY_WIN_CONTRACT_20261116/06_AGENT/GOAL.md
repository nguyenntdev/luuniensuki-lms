/goal
Repo: nguyenntdev/luuniensuki-lms main. Execute V4.2 novelty-first research programme starting from commit 331c581f540ba4a6d41618b49222a0f56fdf0042, first refresh HEAD and reconcile git history. Read `00_START/READ_ME_FIRST.md`, `01_NOVELTY/PAPER_BY_PAPER_SCREENING.md`, `02_WIN_CONTRACT/WIN_CONTRACT.md`, all 14 `03_PAPERS/*`, and `07_TICKETS/V42_TASK_REGISTER.csv` before writing code. Do not mark proposal as a demonstrated win.

Deploy exactly 10 cooperating agents with file ownership and no simultaneous write collisions:
1. CI/provenance integrator: fix pytest false green, public vs private gates, canonical release evidence; owns workflow/gate infra.
2. Systematic literature/novelty reviewer: recent direct prior works, DOI/author-source cross-check and overlap red-team; owns literature cards, does not invent approvals.
3. Data rights+splits: licence/rights cards, immutable raw hashes, dataset parity; human rights approvals stay BLOCKED.
4. Strong baseline replication KT+learner prediction: P01/P05/P13 with pyKT and tabular models.
5. Exact search/constraint mechanisms: P02 and P06, proof of invariant and fair allocation limits.
6. LLM teacher+method validity: P03/P11, real generation versus human rubric, respect protected samples.
7. Shift/benchmark+curriculum: P04/P10, non-fabricated ontology and blind teacher review requirements.
8. Multimodal evidence and accessibility: P07/P14, rights, source-language tasks, no unlicensed media.
9. Security, provenance and archival: P08/P09/P12, ensure distinct paper estimands and archive permission.
10. Scientific auditor/release: per-claim CI, effect size, blinded one-shot validation, independent replication, cross-paper dedup, manuscript tables, no fake win.

Workflow mandatory:
- Step A: Fix CI and prove negative canary fails. Reconcile 211/107 vs 218/100. Reproduce V3 raw-case failures.
- Step B: Complete closest-work matrices and run ALL task-compatible recent strong baselines at matched budget; generate champion B* on DEV.
- Step C: Identify residual baseline failure; if absent, status NO_RESIDUAL_GAP. Novelty review must be signed by human (cannot fabricate).
- Step D: Propose mechanism only if evidence supports; implement only for candidates with formal mathematical distinction from nearest prior art.
- Step E: Train/tune on TRAIN/DEV only within prereg budget; no sealed test access by agents designing method.
- Step F: Freeze hypothesis, method, metric, δ, alpha, code hashes and evaluator; one-shot TEST with corrected CIs and full safety constraints.
- Step G: New independent replication (when available), ethical/legal/human signoff; release only supported claims. Negative/null result is acceptable and must be retained.

Conditions: NEVER choose weak baseline intentionally, cherry-pick test cases, fake data/annotations, auto-mark human-only approvals, compare mismatched coverage/horizons, tune after seeing test, or call a synthetic score SOTA. No promise of win. Work until all automatable tasks are evidence-verified, explicitly document every blocker, and do not claim async continuation.
