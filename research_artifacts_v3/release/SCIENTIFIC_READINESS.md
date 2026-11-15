# Research V3 — Scientific Readiness (14-paper portfolio)

Basis: `research_artifacts_v3/release/progress.json` (318 tasks; 218 DONE / 100 BLOCKED;
44 human-only, always BLOCKED) and the run artifacts under `research_artifacts_v3/runs/p01..p14`.
Generated 2026-11-15 against source SHA `4e5a792e16250106b9d0a577849e864ab7007c92`.

**ZERO papers are submission-ready.** No paper has the required human-only signoffs
(T19 ethics, T20 novelty, T21 coauthor/venue) or an external double-blind rerun (V3-G19).

**"PASS" in this portfolio means**: a licensed external dataset (captured license-text
hash + verified file hash in the dataset registry) actually backs the primary claim, on
comparable baselines, with leakage audits and full negative-result disclosure. PASS is
never used for software success, demo behaviour, or synthetic-only evidence. In the
current state **no paper reaches full PASS**; P09 passes only at the provenance layer
(see table). Software success is not scientific validity.

| Paper | External dataset (real?) | Primary outcome | Baseline beaten? | Status | Why |
|---|---|---|---|---|---|
| P01 — Risk-controlled transfer gate | Yes — OULAD 2013-2014, CC BY 4.0, 32,593 rows, hash-verified (`runs/p01/status.json`) | Test accuracy of the selective risk-controlled gate (T_seed0, test n=3,228) | **NO** — C1 logreg 0.5536 vs proposed 0.2091 (coverage 0.362); preregistered null published (`runs/p01/status.json`, `runs/p01/T/metrics_C1_regularized_logistic.json` vs `metrics_proposed_rc_stg.json`) | **PARTIAL (honest null)** | Real data and clean leakage audit (PASS, 0 duplicates), but the proposed gate trades accuracy for abstention (64% abstained) and did not beat a plain logistic regression. Single dataset, observational; no SOTA claim. |
| P02 — Constrained path planning | No — synthetic benchmark with brute-force certified optima (1,620 instances, seed 20261115; `runs/p02/study_metric.json`) | Exact-match rate, false-infeasibility count, p95 latency | **TIE** vs C1 exact branch-and-bound (1.000 vs 1.000, Holm p=1.0); beats C0 greedy (Holm p=1.4e-25) but is ~2.7× **slower** at p95 (1.228 ms vs 0.451 ms) | **PARTIAL** | Proposed achieves exact optima with zero false infeasibility (C0: 560; A3: 819), i.e. equivalence with C1, not superiority — and a runtime disadvantage. No external routing dataset. |
| P03 — Evidence-calibrated tutoring | Yes — MRBench v3 devset, CC BY-SA 4.0 per repo README (no LICENSE file; APPROVED-WITH-CAVEAT), 272 frozen cases (`runs/p03/manifests/manifest_v1.json`, `runs/p03/raw/`) | Decision-layer: per-case win rate, answer-leakage rate, grounding | **YES on the decision layer** — win 1.000 (Wilson [0.986, 1.000], n=272), leakage 0.000 (CP [0, 0.0355]) vs C0 1.000 / C1 0.186; McNemar Holm p=4.7e-10 (`runs/p03/reports/summaries_v1.json`, `paired_stats_v1.json`) | **PARTIAL** | No real LLM evaluated (C2 BLOCKED: no licensed executable model, 2 GiB GPU, no API credentials); no human teacher reference (B05); decision-layer probe only, not generated-text scoring; single domain (math tutoring). |
| P04 — CurriculumShiftBench | Yes — OULAD (32,593) + UCI student-performance (1,044), both CC BY 4.0, APPROVED (`runs/p04/reference_eval/leaderboard.json`) | Benchmark protocol: per-stratum degradation matrix (S0–S4) for a predictor population | Protocol result: H0 (no new failure mode) does **not** stand — 4 CI-separated degradation strata (partial_mapping_20pct 0.0476, partial_mapping_50pct 0.0429, presentation_shift 0.0164, course_shift 0.0506); rank stability 1.0 (`runs/p04/reference_eval/leaderboard.json` null_assessment) | **PARTIAL** | Independence gate PROCEED (distinct estimand vs P01; `runs/p04/independence_decision.json`). C0/C1 measured honestly; KT baselines DKT/SAKT/AKT pending (T08/T10 TODO), ablations A1–A4 unexecuted, Holm over the confirmatory family pending T08. |
| P05 — Temporal forgetting KT | Yes — OULAD, 48,370 test attempts, day-strict causal cutoff (`runs/p05/run_manifest.json`) | AUC vs forgetting-aware features | **YES — small gain**: P05 0.7220 vs C1 0.7132, ΔAUC 0.0088, CI [0.0075, 0.0101], learner-clustered bootstrap, 2,000 resamples (`runs/p05/statistics.json`) | **PARTIAL** | CI-separated but small gain; C2 published KT comparator BLOCKED; single external dataset ("external generalization unverified", `runs/p05/experiment_card.json` protocol_deviations). |
| P06 — Budget-constrained prioritization | Yes — OULAD, time split, test n=11,260 (`runs/p06/split_manifest.json`) | Recall@k under capacity; fairness gap | **NO** — proposed ties C1 (all 6 preregistered contrasts null, p=1.0; `runs/p06/null_results.json`); equity floor never binds (risk already over-selects; `runs/p06/task_status.json` A4 note) | **PARTIAL (honest null)** | Real data, honest null published, non-causal attestation signed (`runs/p06/noncausal_attestation.json`: NONCAUSAL_UNTIL_PROVED). No intervention effect claimable. |
| P07 — Resource-aware multimodal selection | Yes — Smithsonian Open Access FSG, CC0 (99 CC0-cleared records captured per `research_v3/manuscripts/p07/DATA_STATUS.md`; 8 scored external cases + 17 synthetic stress; `runs/p07/p07-wave1/results.json`) | Select/reject decision correctness; affordance identifiability | **NO superiority** — external primary contrast raw p=0.125 (8 vs 4 correct, n=8), Holm p=0.75 (`results.json` multiple_testing) | **PARTIAL** | Mechanism IS identifiable: G16 POS/NEG pairs separated=true on both suites. n=8 external cases is not powered; single provider (Europeana 401, A3/A4/B00–B03 ablations dated BLOCKED in `runs/p07/BLOCKED_TASKS.md`). |
| P08 — Reward-integrity gamification | No external dataset — deterministic synthetic fixtures; classified SOFTWARE_SECURITY_EVALUATION (`runs/p08/evaluation_results.json`) | False-award rate; per-vector attack detection recall | Primary gate passed: 0 false awards over 1,000 honest + 3,000 adversarial deliveries; recall 1.0 on all 6 vectors; 100 duplicates → exactly 1 award; 30-burst → 5 grants (velocity cap) | **PARTIAL** | `human_outcomes_measured: false`; SS3 human-perception stratum NOT_APPLICABLE. LN-05 probed and measurably fails cross-session replay / forged-actor / velocity burst — that mechanism contrast is the contribution (`runs/p08/independence_decision.json`). |
| P09 — Provenance-aware heritage exploration | Yes — Wikidata CC0 corpus (23 discovery bindings / 51 claims, query+response SHA-256 pinned; `runs/p09/corpus/corpus_manifest.json`) | Unsupported-claim surfacing rate | **YES at the provenance layer** — 0.0 (CP [0, 0.070]) vs C0 surface-everything 0.882 and C1 keyword 0.784; counterexamples 4/4 pass (`runs/p09/eval/metrics.json`) | **PARTIAL** (PASS at provenance layer only) | Verification is a structural rule against the frozen snapshot, explicitly NOT expert adjudication; citation grounding 0.118 for all arms (only 6 grounded claims exist in the corpus); Huế corpus and Europeana BLOCKED. |
| P10 — Spiral heritage curriculum | No external dataset — AI-generated repo corpus (162 objects / 9 urns, `is_ai_generated_fraction: 1.0`, disclosed; `runs/p10/p10_run_20261115T112719Z.json`) | Spiral-DAG validity certificates (acyclicity, Bloom ascent, grade monotonicity, provenance gate) | N/A — design-gate evidence only: proposed valid; C0/C1/A2/A4 invalid; A3 (no provenance gate) accepts an invented anchor, demonstrating the gate's necessity | **BLOCKED** | Only 3/30 curriculum anchors are documented; 27 flagged `needs_expert_review`; 91/162 objects sit on documented anchors. The superiority H0 explicitly requires real teacher raters (P10-T19). No expert rating, CVI, or rubric score exists. |
| P11 — Historical-reasoning rubric | None — annotation pack prepared and unfilled (`runs/p11/status_manifest.json`) | Rubric reliability (Krippendorff α / κ / ICC) vs single-holistic scale | N/A — no raters exist; reliability harness verified only on synthetic toy data ("SYNTHETIC TOY verification only; never a result") | **BLOCKED** | `release_status: BLOCKED_RATER_AND_SAMPLE_REQUIRED`. Templates contain headers only — no annotator IDs, ratings, timestamps, or agreement numbers were fabricated. |
| P12 — Source evidence ledger | Documented repo claims, read-only (63 claims / 16 sources, all three input files SHA-256-pinned, network access none; `runs/p12/summary.json`) | Locator completeness; ABSTAIN routing; append-only hash chain | Engineering: PROPOSED locator completeness 1.0 vs C0 0.0; 62/63 claims correctly routed to ABSTAIN pending human review; chain of 63 events PASS | **BLOCKED** | `scientific_status: BLOCKED_PENDING_HUMAN_REVIEW`. Labels are inherited documented assertions, not machine-verified; Vietnamese primary archives (ĐNTL, HĐSL, ĐNNTC) BLOCKED for automated ingestion (page-level rights not cleared). |
| P13 — SRL behaviour analysis | Yes — OULAD clickstream (10,655,280 studentVle rows; 3,810,268 in the day 0–60 window; 32,593 learner-module-presentation rows; `runs/p13/FINDINGS.md`) | ΔAUC of phase-structured SRL proxies (C2) vs raw click count (C0) | **NO** — ΔAUC −0.0080 group (CI95 [−0.0253, 0.0063]) and −0.0190 time (CI95 [−0.0296, −0.0042]); preregistered 0.02 margin not met; H0 NOT rejected and published as a null (`runs/p13/summary.json`) | **PARTIAL (honest null)** | Construct validity guard enforced: every feature is `proxy_only`, `measured_construct: null` — clicks are NOT measured SRL, and no causal claim is made. |
| P14 — UDL/WCAG learning objects | No external media — synthetic 13-object manifest (`p14-synthetic-manifest-1.0.0`; Smithsonian API 403 and Europeana 401 without keys, recorded in `runs/p14/audit_report.json` rights cards) | Accessibility conformance of the audit (per-criterion, per-object) | Descriptive only: 97/112 criteria passed = 0.8661 (Wilson [0.7907, 0.9171]); the audit is stricter than the C0 has-image / C1 WCAG-checklist baselines, which miss UDL-principle failures the full audit catches (`runs/p14/metrics_summary.json`, `baseline_results.json`) | **PARTIAL** | 13 objects, 4 pass / 9 fail, 15 missing affordances; 4 mechanism-removal ablations trigger the named mechanism. No human user study; benefit/effect claims are rejected by the claims guard (`runs/p14/claims_ledger.json`, 3 rejected). Overlap vs P07 = KEEP_SEPARATE (`runs/p14/overlap_decision.json`). |

## Status counts

- **PASS: 0** — no paper has a fully licensed, externally validated, human-signed primary claim.
- **PARTIAL: 11** — P01, P02, P03, P04, P05, P06, P07, P08, P09, P13, P14. Real licensed data
  (OULAD, UCI, Smithsonian CC0, MRBench CC BY-SA, Wikidata CC0) and/or a complete software
  evaluation exist, but at least one of: null superiority, no human adjudication, no real-LLM
  baseline, or synthetic-only media.
- **BLOCKED: 3** — P10 (expert validation of curriculum anchors), P11 (no human raters),
  P12 (human archival review of 62/63 ABSTAIN claims).
- **Honest nulls preserved**: P01, P06, P07 (superiority), P13 — and a tie-with-runtime-cost
  in P02. None were tuned away; each is disclosed in its run artifacts and here.

## Not proven (explicit)

- **No human learning gains** — no study here measured a learner outcome change.
- **No expert consensus** — no expert adjudication, CVI, or inter-rater agreement from real raters exists anywhere in the portfolio.
- **No SOTA** — no state-of-the-art claim is made or supported; C2 published-model comparators are BLOCKED in P03/P05/P13.
- **No venue acceptance** — no paper has been submitted or accepted; T21 signoffs are human-only and unexecuted.
- No causal effect claims (P06 attests NONCAUSAL_UNTIL_PROVED; P13 makes none).
- No measured SRL or memory construct (P05/P13 use behavioural proxies only).
- No cross-provider media generalization (P07/P14: single provider or synthetic).
- No independent double-blind rerun (V3-G19 BLOCKED; only the request artifact is staged).

## Traceability

Every number above traces to a named file under `research_artifacts_v3/runs/`. The per-task
DONE/BLOCKED ledger is `research_artifacts_v3/release/progress.json`, regenerated only by
`python -m research_v3.scripts.progress_report` (fail-closed: tasks without a machine-readable
task-granular ledger stay BLOCKED; human-only tasks always BLOCKED). If a number cannot be
traced, treat it as UNVERIFIED and do not repeat it.
