# P05 — Temporal Forgetting-Aware Knowledge Tracing and Review Scheduling
# Manuscript skeleton (AIED / EDM target). All numeric cells tied to research_artifacts_v3/runs/p05/

status: SKELETON_CODE_READY
title: "Temporal Forgetting-Aware Knowledge Tracing on Higher-Education Clickstreams: A Modest-Gain Result on the Open University Dataset"

abstract_points:
  - "Knowledge tracing models in online learning often ignore elapsed time between student attempts, treating revision intervals as uniform."
  - "We evaluate a temporal forgetting-aware prediction model alongside a recency-and-frequency baseline (C1) and a global base rate (C0) on 48,370 test attempts from the Open University Learning Analytics Dataset (OULAD; CC BY 4.0; Kuzilek et al., 2017)."
  - "On a strict causal time split (training on earlier presentations, testing on future presentations with zero post-cutoff features), the forgetting-aware model reaches an AUC of 0.7220 (95% CI [0.7105, 0.7328]) against 0.7132 (95% CI [0.7020, 0.7241]) for C1."
  - "The paired difference of +0.0088 AUC points is statistically significant under a 2,000-resample learner-clustered bootstrap (95% CI [0.0075, 0.0101]; p < 1e-4, Holm-adjusted family size 4)."
  - "In contrast, review scheduling at a 20% capacity budget yields a null difference against a greedy heuristic; the scheduling null is published per preregistration."
  - "We report this as a modest-gain, observational finding on clickstream proxies (clicks are not directly observed memory traces; C2 published KT library is BLOCKED for lack of an upstream adapter; single-dataset limitation applies)."

research_questions:
  rq1: "Does modeling elapsed time between online learning events improve prediction of next-attempt correctness over a static recency/frequency model?"
  rq2: "Does temporal modeling translate to measurable recall gains under realistic capacity-constrained review budgets?"

dataset:
  name: "Open University Learning Analytics Dataset (OULAD)"
  license: "CC BY 4.0"
  cohort: "32,593 learners across 7 STEM modules"
  test_attempts: 48370

baseline_results:
  c0_base_rate_auc: 0.5000
  c1_logistic_recency_freq_auc: 0.7132
  p05_forgetting_aware_auc: 0.7220
  delta_auc: 0.0088
  bootstrap_ci_95: [0.0075, 0.0101]

threats_to_validity:
  construct_validity: "OULAD clickstream events are observational engagement proxies, not laboratory-validated memory retention measurements."
  external_validity: "Evaluated on a single distance-learning institution; cross-domain transfer to other platforms is unverified."
  baseline_comparability: "C2 published KT baselines (DKT/SAKT/pyKT) remain BLOCKED because no licensed upstream adapter was available; C1 is an independent logistic reimplementation."
