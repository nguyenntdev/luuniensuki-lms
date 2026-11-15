# P04 METHOD — CurriculumShiftBench protocol (frozen 2026-11-15)

Status: `PROCEED` per `research_artifacts_v3/runs/p04/independence_decision.json`.
This document specifies the benchmark BEFORE any tuned claim; reference numbers
live in `research_artifacts_v3/runs/p04/reference_eval/leaderboard.json` and are
measured, not illustrative.

## 1. Estimand and hypothesis

- **RQ.** Do predictors degrade systematically and reproducibly under realistic
  incomplete/ambiguous skill mappings, and can a portable frozen benchmark
  quantify these failures across a population of predictors?
- **Estimand.** Per-stratum AUC degradation
  `delta_s = AUC(model, S0 in-domain test) - AUC(model, S_s test)`,
  with learner-cluster bootstrap 95% CIs (unit = `group_id`, 1000 resamples,
  seed 42).
- **H0 (published if not rejected).** No reliable new failure mode beyond known
  cross-domain splits: every stratum's shifted AUC CI contains the same
  predictor's in-domain AUC, and rank stability across strata is perfect.
- **H1.** At least one frozen shift stratum produces a CI-separated AUC
  degradation for the reference population.

Decision rule (frozen in `pre_registration.yaml`): a failure is *reliable*
iff the shifted-AUC bootstrap CI's upper bound is below the same predictor's
in-domain AUC. The reference run found reliable failures on S1@20%, S1@50%,
S3 presentation shift, S3 course shift (C1); H0 therefore does NOT stand for
the reference population — reported as a measured result, not a claim of
novelty (P04-T20 human signoff pending).

## 2. Protocol components (novel vs reused)

| Component | Status | Notes |
|---|---|---|
| Strata definitions S0-S4 + A1-A4 | novel (this protocol) | frozen names, params, salts |
| Mapping-noise injector (`hide_bridge_edges`) | novel | deterministic, salt-ranked edge hiding |
| Annotation-budget bridge (S2) | novel | real unseen-category mechanism |
| Canonical ontology `cso-p04-1.0` | novel annotation | edges verified against `vle.csv` |
| NOT_APPLICABLE / ABSTAIN scoring contract | novel (as a benchmark contract) | distinct classes, explicit denominators |
| Learner-cluster bootstrap | reused standard | Efron; group resampling standard in EDM |
| Rank AUC (Mann-Whitney) | reused standard | tie-correct, O(n log n) |
| Group/time splitters | reused (`research_v3.eval.splitters`) | vetted shared implementation |
| Logistic regression | reused (scikit-learn 1.8.0) | C1 baseline, frozen config |

## 3. Data flow and invariants

```
private_data/raw (hash-frozen) ──> adapters (labels outside input)
   ├──> frozen splits (group p04-v1 / time) ──> split hash (p04_splits.json)
   └──> activity_type per learner (60-day window mode) ──> ontology bridge
            ├──> S0 in-domain reference cells (per predictor)
            ├──> S1: hide verified edges (20/50/80%) ──> remap ──> score
            ├──> S2: annotation budget (train courses only) ──> score
            ├──> S3: presentation / course / subject shift ──> score
            └──> S4: cold-start slice (early_click_total == 0) ──> score
```

Invariants (enforced by tests in `tests/research_v3/method/test_p04_protocol.py`):

1. `final_result`/`G3` never appear in model inputs (adapter + leakage audit).
2. Splits are group-disjoint; hash reproducible; `assert_no_leakage` passes.
3. ABSTAIN is never counted as a negative prediction; NOT_APPLICABLE rows are
   excluded and counted (`n_not_applicable`, `n_no_activity`,
   `annotation_gap_rows`).
4. Empty denominators yield `None` (never a fabricated number).
5. Injectors touch only mapping information, never gold labels.
6. Rerunning the evaluation on the same raw snapshot is deterministic
   (verified: two full runs produce identical canonical JSON).

## 4. Complexity and compute

- Splitting: O(N) hashing. Bridge mapping: O(N). AUC: O(n log n) per cell.
- Bootstrap: O(1000 · n) per cell. Reference run wall time: < 2 min single
  core, no GPU. All artifacts reproducible from frozen raw hashes.

## 5. Limitations (disclosed in every table caption)

- External generalization beyond OULAD + UCI student-performance is UNVERIFIED
  while ASSISTments/Junyi/EdNet remain BLOCKED.
- C0/C1 are reference baselines; no KT-system baseline (DKT/SAKT/AKT/GKT) has
  been run yet — those are P04-T08/T11 tasks and remain TODO.
- UCI n=1044 with 59-case por in-domain test cell carries `small_n_warning`.
- OULAD captured license is CC BY-NC 4.0: benchmark artifacts are academic,
  non-commercial.
- Ablations A1-A4 are defined in the protocol but not yet executed (TODO).
