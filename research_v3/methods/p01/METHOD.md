# P01 — Method specification (frozen before implementation of the engine)

Paper: **Risk-Controlled Knowledge Transfer under Partial Skill Alignment**
Status at freeze: `PREREGISTERED` (see `research_v3/experiments/p01/preregistration.yaml`).

## 1. Problem statement (operationalized)

The spec's candidate mechanism (two-stage probabilistic skill-graph alignment +
uncertainty-aware source gating + a KT backbone) requires interaction-level
skill graphs and multi-domain KT corpora. The only APPROVED dataset card in this
environment is `oulad-2013-2014` (Kuzilek, Hlosta & Zdrahal 2017, CC BY 4.0),
which is **learner x module-presentation level** with a frozen 60-day early
click window and a separate final-outcome label (`final_result`:
Distinction/Pass/Fail/Withdrawn). There is no skill graph and no second domain.

We therefore implement the **risk-controlled core** of the proposal on the real
OULAD rows and declare the un-executable parts explicitly:

- Executed: a risk-controlled *selective transfer gate* over a source
  ("pre-2014J presentations") learned classifier, transferring to the held-out
  future presentation 2014J ("target platform"), with a conformal-style
  per-class threshold calibrated ONLY on the calibration split and an explicit
  ABSTAIN decision.
- NOT executed (BLOCKED, do not claim): skill-graph alignment (`partial_alignment.py`),
  KT backbones B00–B02/B04/B06 (DKT/SAKT/AKT need interaction sequences and a
  second platform), and any human learning-gain claim. OULAD is observational;
  click counts are behaviour proxies, not interventions.

The unit of "partial skill alignment" available in this data is presentation
shift: the source presentations share curricula with the target 2014J but with
different cohort composition and VLE site mixes — a genuine, preregistered
partial-alignment proxy, not a simulated one.

## 2. Data contract (input only; the label is never a feature)

Adapter: `research_v3.datasets.adapters.oulad.load_students` — 32,593 rows, one
per (student, module, presentation).

```
row := {
  case_id:  "oulad-<module>-<presentation>-<id_student>",
  group_id: id_student,          # learner-level grouping key
  time_key: code_presentation,   # chronological key (2013B < 2013J < 2014B < 2014J)
  input: { code_module, code_presentation, gender, region, highest_education,
           imd_band, age_band, num_of_prev_attempts, studied_credits,
           disability, early_click_total, early_active_sites,
           observation_window_days },
  label: final_result            # OUTSIDE input; withheld from the model
}
```

Labels are ordered `Distinction < Fail < Pass < Withdrawn` (fixed vocabulary,
ALPHA order is irrelevant; the order is frozen in code). Any `input` containing
a gold key (`label`, `gold`, `is_correct`, ...) or future-hint key must be
rejected before training (`research_v3.eval.leakage.audit_rows`, strict).

## 3. Featurization (deterministic, artifact-pinned)

- Categorical fields (8): `code_module, code_presentation, gender, region,
  highest_education, imd_band, age_band, disability` — one-hot over a fixed
  vocabulary sorted lexicographically, built from **train rows only** and saved
  to `research_artifacts_v3/runs/p01/features/vocabulary.json`. Unseen values
  (possible on 2014J) map to all-zeros for that field (documented behaviour,
  no crash, no invented category).
- Numeric fields (4): `num_of_prev_attempts, studied_credits, early_click_total,
  early_active_sites` — standardized with train-split mean/std, also saved.
- `observation_window_days` is constant (60) and carries no information; it is
  dropped from the design matrix but recorded in the vocabulary artifact.
- Feature order is fixed by the ordered field lists above; the design matrix is
  a deterministic function of (rows, vocabulary artifact).

## 4. Models

### C0 — sanity majority predictor
Predicts the modal training label for every case. No parameters beyond the
modal label. Purpose: non-trivial negative control; a win over C0 alone
justifies no superiority claim.

### C1 — matched classical baseline (regularized multinomial logistic regression)
- Objective: L2-regularized multinomial cross-entropy,
  `min_W,b (1/n) * sum_i CE(softmax(x_i W + b), y_i) + (lambda/n) * ||W||_2^2`
- Optimizer: full-batch gradient descent, fixed iterations/lr from the frozen
  config; numpy only. Optimizer state is reported as `heuristic_gradient_descent`
  (no optimality certificate is claimed).
- Hyperparameters are frozen at `lambda=1.0, iters=250, lr=0.5` BEFORE the
  confirmatory run (no tuning on test; a small dev-set sweep is recorded in
  `hyperparameter_search.json` but the frozen values are used regardless).
- Softmax probabilities are the model's scores.

### Proposed — Risk-Calibrated Selective Transfer Gate (RC-STG)
- Base: the C1 model, retrained identically (same budget) on the same train rows.
- Calibration split is used ONLY to choose thresholds; test labels are never
  touched until after freeze.
- Notation: `p(x) in R^4` softmax; `j(x) = argmax_k p_k(x)`; `m = p_{j(x)}`
  (margin proxy); `f = p_Fail`.
- Two conformal-style thresholds, both computed on calibration rows:
  1. `tau_conf` = ceil((1 - alpha_conf) * (n+1))/n quantile (higher-is-better,
     conservative) of `m` over calibration rows where the C1 argmax was
     **CORRECT**. Semantics: a new case is trusted only if its margin exceeds
     what correct-but-unconfident calibration cases showed; because correct
     margins stochastically dominate wrong margins (verified empirically:
     median correct margin 0.523 vs median wrong margin 0.472 on the T
     calibration split), the ABSTAIN region concentrates the model's errors.
     This is a *risk-control proxy*, not a finite-sample conformal guarantee
     under shift.
  2. `tau_fail` = quantile of `f` over calibration rows whose TRUE label is not
     Fail, at level `1 - alpha_fail` (higher-is-better). Semantics: bounds the
     false-alarm rate of re-routing a case to Fail at approximately
     `alpha_fail` on the target.
- Decision rule `decide(x)`:
  ```
  if m(x) < tau_conf:  return ABSTAIN          # do-not-transfer state
  if f(x) >= tau_fail: return Fail             # risk-gated re-route
  return class j(x)
  ```
- `ABSTAIN` and `NOT_APPLICABLE` are distinct decision values, disjoint from the
  4 class labels (contract requirement). Every prediction carries
  `reason_codes` (e.g. `gated_abstain_low_margin`, `gated_fail_reroute`,
  `ungated_argmax`) so the mechanism is auditable.
- Scope honesty: the bound is exchangeability-based (calibration and test rows
  i.i.d.-exchangeable conditional on the frozen rule). Under presentation shift
  it is an approximation; the preregistered evaluation measures whether the
  empirical risk on 2014J respects it, it does not assume it.

### Ablations (true removals, same splits/compute)
- `A1_no_gate`: skip both thresholds (identical to C1 decision path).
- `A2_no_fail_gate`: keep confidence ABSTAIN, drop the Fail re-route.
- `A3_no_abstention`: keep Fail re-route, never ABSTAIN.
- `A4_random_gate`: thresholds replaced by a seeded pseudo-random per-case
  gate with the same marginal ABSTAIN rate (measures whether the *learned*
  gate matters, not just abstention volume).
- `A5_shuffled_thresholds`: thresholds drawn from the marginal distribution of
  calibration margins (destroys the per-case coupling).

## 5. Splits (frozen once, hashed)

Two protocols, both materialized by `research_v3.eval.splitters` and audited by
`research_v3.eval.leakage`:

- **G (learner-group)**: `group_split(group_key="group_id")`, fractions
  0.70/0.10/0.10/0.10, salt `p01-v3`. Same presentations appear in all
  partitions but no learner does.
- **T (temporal transfer)**: `time_split(time_key="time_key")` with
  train_fraction 0.70 — empirically train=2013B/2013J/2014B + a small 2014J
  tail, test=2014J only. Learners appearing in a later partition are REMOVED
  from all earlier partitions (earlier-in-time yields) so no learner spans two
  partitions; the row yield is recorded in `splits_manifest.json`.

The preregistered primary analysis is protocol T (transfer to the unseen
presentation). Protocol G is a secondary robustness analysis.

## 6. Estimand, null, metrics

- Primary estimand: per-case 4-class accuracy of the proposed gate vs C1 on the
  frozen T-test rows (2014J), paired per case.
- H0 (preregistered): the gate does not improve T-test accuracy over C1.
  Because the gate trades accuracy for abstention/risk control, the null is
  expected to survive; a surviving null is reported as an explicit null result,
  never tuned away.
- Secondary: macro-F1, per-class recall, Wilson + Clopper-Pearson CIs, ECE +
  reliability bins (on the margin of the predicted class), exact McNemar vs C0
  and C1 (paired), Holm correction across the declared family
  {proposed-vs-C1, proposed-vs-C0}, worst-group robustness by region /
  age_band / disability / imd_band, coverage (non-ABSTAIN fraction).
- AUC is not defined for the ABSTAIN decision; where reported it is computed on
  the non-abstained subset and labeled as such.

## 7. Artifacts (fail-closed)

`research_artifacts_v3/runs/p01/<protocol>/`:
`predictions_{model}.jsonl`, `metrics_{model}.json`, `statistical_tests.json`,
`calibration_{model}.json`, `robustness_{model}.json`, `null_result.json`,
`splits_manifest.json`, `features/vocabulary.json`, `experiment_card.json`,
`status.json`. All JSON strict (no NaN/Infinity). Metric JSONs must be
recomputable from the saved predictions + sealed gold (tested).

## 8. Compute and determinism

CPU-only, numpy. Full run wall time target < 10 min. One scored seed (0);
determinism is verified by rerunning with the same seed and comparing
prediction bytes (no "3 identical hashes = 3 seeds" fiction).

## 9. What would falsify the mechanism

If removing the gate (A1) matches the proposed method's metrics, the gate adds
nothing. If A4/A5 (degenerate gates) match the real gate, the learned thresholds
add nothing beyond abstention volume. If the proposed method beats C1 only by
excluding hard cases via ABSTAIN without a coverage disclosure, that is
reported as a coverage-cost result, not a win.
