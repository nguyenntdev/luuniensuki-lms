# P06 Ablations (true removals of named mechanisms)

Per spec §5. Every ablation runs on the SAME splits, seeds and compute as the
main matrix; results recorded whether favorable or not (fail-closed).

| ID | Removed mechanism | Operationalization | Expected family (registered BEFORE running) |
|----|-------------------|--------------------|----------------------------------------------|
| A1 | calibrated uncertainty | raw margins min-max squashed, same model (``P06RiskModel(raw=True)``) | worse/misordered probabilities; Brier/ECE degrade; ranking may shift modestly |
| A2 | capacity constraint | k := |eligible| per cohort | precision@k collapses toward prevalence; recall rises trivially by selecting everyone |
| A3 | missingness/evidence gating | gate off: zero-evidence and sub-threshold learners become selectable | zero-evidence learners (13.0% of OULAD rows; 86% Withdrawn among them) enter selection without actionable evidence — the LN-09 failure mode this gate blocks |
| A4 | equity bound | ``enforce_equity=False`` | identical to C1 when quota floors are slack; quantifies the floor's cost when binding |

## Required stress strata (spec §5; deterministic generators, no outcome declared before running)

- **high predicted risk, no actionable evidence** — must surface as ABSTAIN
  (never selected "as if evidence existed"); test
  ``tests/research_v3/method/test_p06_selection.py::test_high_risk_no_evidence_abstains``.
- **small cohort privacy (n < 5 cells)** — per-subgroup stats suppressed;
  test ``test_p06_metrics.py::test_k_anonymity_suppression``.
- **missing VLE logs** — zero-click rows (4,247 in full OULAD) are exactly the
  ABSTAIN class; cohort-level counts reported in run artifacts.
- **capacity lower than eligible count** — binding-budget rounds; capacity
  violation counter must remain 0; test
  ``test_p06_selection.py::test_budget_never_exceeded``.

Results are written to ``research_artifacts_v3/runs/p06/ablations.json`` by the
runner; no stratum may be omitted because the proposed method fails.
