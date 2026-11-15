# P06 METHOD — Budget-Constrained Teacher Intervention Prioritization (NON-CAUSAL)

Paper ID: `P06` — status **`NONCAUSAL_UNTIL_PROVED`** (frozen 2026-11-15).
This document is the implementation contract written BEFORE the engine code,
per the P06 spec (`05_PAPERS/P06_*.md`, section 3, requirement 2).

## 1. Research question and estimand

**RQ.** With a fixed teacher capacity of `k` interventions per selection round,
can *uncertainty-aware, equity-constrained* prioritization improve the
**identification and coverage** of at-risk learners over (C0) random selection
and (C1) risk-only top-k ranking — **without claiming any intervention effect**?

**Estimand (selection quality, NOT outcome change).** For a frozen test set and
a fixed budget `k` per cohort, the estimand is the *binary-label capture
quality of the selected set*:

- primary: **Recall@k** ("failure capture") = |{selected} ∩ {Fail}| / |{Fail}|, with
  `Fail` = OULAD `final_result == "Fail"` (see §3 for label semantics);
- secondary: Precision@k, NDCG@k, subgroup coverage, fairness gap, Brier, ECE.

**H0 (must be published if not rejected).** Constrained ranking adds no
material benefit over calibrated top-K risk ranking (C1) on failure capture.

**Causality boundary (HARD).** OULAD is observational: no learner was actually
assigned an intervention by this study. Every metric below measures
*ranking/selection quality against realized outcomes*. **No claim is permitted
that intervening on a selected learner would improve their outcome.** The words
"improve", "avert", "prevent", "reduce" applied to outcomes are banned in the
manuscript; only "identify", "capture", "prioritize", "rank", "select" are
allowed for what the method does. "Failures averted" may appear ONLY as the
name of the hypothetical optimization objective being *modeled*, never as a
measured result. See `noncausal_claims.md`.

## 2. Problem definition

Per cohort `c` (a course-presentation, e.g. `FFF/2014J`) with `n_c` enrolled
learners observed at the day-60 cut-off:

- each learner `i` has: covariates `x_i` (pre-cut-off only), a **calibrated**
  risk score `p_i = P(Fail | x_i)` from a model trained WITHOUT the test
  cohort (§5), a binary realized outcome `y_i ∈ {0,1}` (1 = Fail) known only to
  the sealed evaluator, and subgroup attributes `g_i = (region, disability)`.
- the teacher can act on **k** learners per round (`k ∈ {25, 50, 100}` in the
  preregistered matrix; capacity `k < n_c` in every selection round).
- optional per-subgroup **cost**: acting on subgroup `g` costs `cost(g) ≥ 0`;
  the total spend must respect the budget.

**Objective (modeled, not measured):** choose `S ⊆ cohort, |S| = k` maximizing
`Σ_{i∈S} p_i` — i.e., the *expected number of identified at-risk learners* —
subject to:

1. **Capacity**: `|S| ≤ k` (hard; tested, never violated).
2. **Evidence gating (abstention)**: a learner with NO actionable evidence
   (zero early VLE clicks AND zero active sites within the observation window)
   is **ineligible for selection** and gets decision `ABSTAIN`
   (a distinct state, not a negative prediction, not `NOT_APPLICABLE`).
   A high-risk learner without actionable evidence is NOT selected as if
   evidence existed — mirrors the LN-09 invariant `unsupported_action_rate → 0`.
   Learners with predicted risk below the **preregistered minimum actable risk**
   `p_min = 0.05` get `NOT_APPLICABLE` (below the actionable threshold), also
   ineligible. The selection pool is therefore the *eligible set*
   `E_c = {i : evidence_i ∧ p_i ≥ p_min}`; if `|E_c| < k`, only `|E_c|`
   learners are selected (capacity respected with slack, never padded).
3. **Equity floor (proportional representation)**: for the disability
   attribute (`Y` = declared disability, `N` = none), each group `g` is
   guaranteed a minimum number of seats
   `m_g = ceil(quota_g · π_g · k)` where `π_g = |E_g| / |E_c|` is the group's
   share of the eligible pool, with preregistered `quota_Y = 0.5`,
   `quota_N = 0.5`. Floors are feasible by construction (`Σ_g m_g ≤ k` since
   `Σ π_g = 1` and quotas ≤ 1); when a group's eligible pool is smaller than
   its floor (`|E_g| < m_g`), the constraint degrades gracefully to
   `min(|E_g|, m_g)` and the run records
   `fairness_constraint_feasible = false` for that group/round (never silently
   dropped, never blocking selection of eligible high-risk learners from other
   groups). As defense-in-depth, if user-supplied quotas sum above 1 and
   floors jointly exceed k, floors are scaled down proportionally and the
   round is flagged `capacity_conflict = true`.
4. **k-anonymity for reported statistics**: any per-subgroup statistic with
   `n < 5` is reported as `null` with reason `"suppressed_n_lt_5"`.

The equity floor is a *coverage* constraint, not a re-ranking of merit: within
the constraint, selection is strictly by risk. The optimizer is a two-phase
greedy: (i) reserve the group minima by taking the highest-risk eligible
members of each constrained group until its minimum is met; (ii) fill the
remaining budget by risk order over all eligible learners. This is optimal for
the separable objective `Σ p_i` under group minima (each reserved seat should
hold the group's highest-risk member; the rest is an unconstrained top-k on
the remainder), hence exact, not heuristic, for this objective family; the
runtime is `O(n log n)` per cohort. Deterministic tie-breaks: higher risk,
then lexically smaller case_id.

**Learned vs fixed components.** Learned (training/cohort splits only): the
risk model weights and its isotonic/Platt calibration. Fixed by preregistration
(never learned): `k ∈ {25,50,100}`, `p_min = 0.05`, the evidence gate rule, the
equity quotas, cost weights (`cost(disability='Y') = cost('N') = 1.0`, i.e.
cost-neutral by default; the cost interface exists for subgroup-varying
sensitivity analysis), k-anonymity threshold 5, all tie-break rules.

## 3. Labels and target semantics

Target = binary `is_fail = 1{final_result == "Fail"}`. `Pass`/`Distinction` → 0.
**`Withdrawn` learners are excluded from scoring and selection** (the estimand
"capturing learners who will fail while remaining enrolled" is undefined for
withdrawal; excluding them is preregistered, not post hoc; sensitivity of this
choice is a listed threat to validity). Prevalence on real OULAD rows
(non-withdrawn): 7,052 Fail / 22,437 non-withdrawn = 31.4%.

## 4. Data and splits (leakage rules)

Real OULAD 2013-2014 (CC BY 4.0 as recorded in `research_v3/datasets/registry.yaml`;
the local archive ships an NC variant of the license text — recorded as a
provenance caveat in the datasheet; the canonical OULAD release license,
per the dataset authors' Scientific Data paper, is CC BY 4.0. Non-commercial
use only is honored regardless.) Adapter: `research_v3/datasets/adapters/oulad.py`
(32,593 rows; features frozen at the day-60 window; `final_result` withheld).

Two split protocols, both materialized once and hashed:

- **S1 group split** (`group_split`, `group_key="group_id"`, salt `p06-v3`):
  learners are the exchange unit; a learner with several course-presentation
  rows lands wholly in one partition. Fractions 0.70/0.10/0.10/0.10.
- **S2 time split** (`time_split` on `time_key = code_presentation`):
  train `2013B+2013J`, calibration/dev `2014B`, test `2014J` — the default
  deployment-realistic protocol (train the past, select in the future).
  The preregistered *primary* analysis is **S2**; S1 is the preregistered
  sensitivity check (learner grouping), reported with the same full matrix.

Test evaluation always happens **per cohort** (one selection round per
course-presentation in the test partition); rows never cross cohorts, and the
risk model never sees any test-presentation row at train/calibration time.

## 5. Risk model (shared by all arms)

Pipeline (identical inputs/preprocessing for every arm):

1. `ColumnTransformer`: one-hot (`handle_unknown="ignore"`) for
   {gender, region, highest_education, imd_band, age_band, disability,
   code_module, code_presentation}; median-imputed + standardized numerics
   {num_of_prev_attempts, studied_credits, early_click_total,
   early_active_sites}. `imd_band` missingness (1,111 rows, 3.4%) is kept
   as its own imputed category; A3 ablates the missingness gating, not
   imputation.
2. Estimator: `LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs",
   class_weight="balanced", random_state=0)` — one pinned classical model for
   all arms (per spec §4 B00; XGBoost/LightGBM B01/B02 are recorded as
   environment-BLOCKED in the baseline ledger — not installed in the pinned
   environment — and are not needed for the C0/C1/proposed contrast).
3. Calibration: fit on the **calibration** partition only via
   `CalibratedClassifierCV(FrozenEstimator(pipe), method="sigmoid")`;
   the frozen base estimator cannot re-fit on calibration data (no leakage).
   Brier/ECE reported from the `reliability_bins`/`expected_calibration_error`
   helpers in `research_v3/eval/calibration.py`.

## 6. Arms (comparison family, preregistered)

- **C0 random**: uniform random selection among *eligible* learners
  (same evidence gate and NOT_APPLICABLE rule as proposed, so the contrast
  isolates the *policy*, not the gate; seed 2026, deterministic generator).
- **C1 risk-only top-k**: sort eligible by calibrated risk desc, take top-k.
  This is the serious classical baseline.
- **PROPOSED**: budget-aware selection with equity floor + evidence gating
  (§2 algorithm), identical risk model and identical eligibility.

Ablations (true removals of the named mechanism; all on the same splits):

- **A1 no calibrated uncertainty**: replace calibrated scores with raw
  decision_function margins (uncalibrated); isolates calibration's role.
- **A2 no capacity constraint**: `k = n_eligible` (select everyone eligible);
  shows what the capacity constraint *costs* (precision should fall).
- **A3 no missingness gating**: disable the evidence gate AND the p_min gate
  (select from the full cohort, treating no-evidence learners as selectable);
  shows what the gate protects (this is the LN-09 mechanism).
- **A4 no equity bound**: drop the equity floor (≡ C1 here; run and reported
  as an explicit removal for the record).

## 7. Metrics and inference

Per selection round (cohort × arm × k), on eligible, non-withdrawn test rows:

- Precision@k = |S ∩ Fail| / |S| (Wilson CI via `research_v3/eval/statistics.proportion_ci`).
- Recall@k (failure capture) = |S ∩ Fail| / |{Fail in cohort}| — the **primary** metric.
- NDCG@k with binary relevance `y_i` (log-discount), computed only over the
  eligible ranked list.
- Subgroup coverage: per constrained group, `|S ∩ g| / min(m_g, |E_g|)` (1.0
  means the floor is fully met); suppressed to `null` when `n < 5`.
- Fairness gap = `coverage_N − coverage_Y` (preregistered direction: gap ≤ 0
  desired, i.e., disability group not under-covered relative to non-disability).
- Capacity violations: count of rounds where `|S| > k` (must be 0 for every arm).

Inference: paired comparisons PROPOSED vs C1 (and vs C0) at each k on the
common set of selection rounds: exact McNemar on per-learner "captured by A,
not by B" indicators, cluster bootstrap (clusters = `group_id`) for the mean
difference in Recall@k, Cliff's delta effect size; Holm correction across the
preregistered family {k=25, k=50, k=100} × {vs C1, vs C0} = 6 tests.
Wilson and Clopper–Pearson CIs for all proportions. Negative/null results are
recorded explicitly via the `null_result` helper, never dropped.

Statistical limitations disclosed: test-set cohorts are few (S2: 6 cohorts,
one presentation), clusters are course-presentations and learners; bootstrap
CIs on few clusters are wide; single external dataset (OULAD only), so
**external generalization is marked unverified** per spec §6.

## 8. Complexity, determinism, certificates

- Risk model fit: O(n d) per fit; calibration: O(n_cal).
- Selection: `O(n_c log n_c)` per cohort (sort) — exact for the separable
  objective with group minima (§2); optimality certificate: the two-phase
  greedy solution dominates any feasible alternative with the same group
  seat counts, and group minima fix those counts; hence optimal. No
  approximate solver is used; no invented global optimum claim beyond this.
- Determinism: seeded splits (stable hash), pinned `random_state=0`, sorted
  tie-breaks; the runner supports byte-for-byte rerun verification
  (artifact hashes compared across two executions).
- Runtime cap: full matrix < 10 minutes single-core (measured in run log).

## 9. Modules (new, this paper)

- `research_v3/methods/p06/selection.py` — eligibility, selection, optimizer,
  k-anonymity suppression (new code, this paper).
- `research_v3/methods/p06/risk_model.py` — feature pipeline + frozen
  calibration (thin composition of scikit-learn primitives; sklearn is cited,
  not reimplemented).
- `research_v3/methods/p06/metrics.py` — P@k/R@k/NDCG@k/fairness gap/
  suppression (new; reuses `statistics.py` CIs).
- `research_v3/experiments/p06/run_experiment.py` — preregistered matrix
  runner and artifact writer (new).

Reused from the shared V3 stack (cited, not modified):
`research_v3/contracts/cards.py`, `research_v3/eval/{splitters,statistics,
calibration,leakage}.py`, `research_v3/datasets/adapters/oulad.py`,
`research_v2/evaluation/statistical_tests.py`.

## 10. Falsification

The proposed method's advantage is falsified if any preregistered test in the
{6-test Holm family} shows C1 ≥ PROPOSED on primary Recall@k, or if the equity
floor costs more capture than the preregistered indifference margin
Δ = 0.02 absolute Recall@k in every k — in that case the honest conclusion is
"constrained ranking adds no material benefit over calibrated top-K" (H0 not
rejected) and that null result is a first-class deliverable.
