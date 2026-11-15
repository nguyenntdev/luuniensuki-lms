# P06 Ablations & failure strata (time split; fail-closed reporting)

| Ablation | Removed mechanism | k=25 Precision | k=25 Recall | Verdict |
|---|---|---|---|---|
| A1 no calibrated uncertainty | A1 | 0.408 | 0.110 | ECE 0.050→0.412; capture at k=25 unchanged pooled (−0.0003), ranking order degrades |
| A2 no capacity constraint | A2 | 0.201 | 0.935 | precision collapses to prevalence 0.201; recall 0.935 by selecting everyone — trivial |
| A3 no evidence/risk gates | A3 | 0.367 | 0.099 | capture DROPS (0.099 vs 0.110) while admitting zero-evidence learners — gate has protective value |
| A4 no equity bound | A4 | 0.410 | 0.110 | identical to C1: proportional floors never bind on OULAD (mechanism, not noise) |

Stress strata (real OULAD, time-split test): zero-evidence learners ABSTAIN (never selected): 1479 across 7 cohorts at k=25; capacity violations outside A2: 0; k-anonymity suppression active (per-subgroup cells with n<5 reported as null).

Dataset: 32593 rows, 10156 Withdrawn (excluded from scoring), 4247 zero-evidence (13.0%); ks evaluated: [25, 50, 100]; seed 2026.
