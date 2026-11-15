# P06 Main results (PRIMARY: time split, test = 2014J)

Selection quality on realized outcomes. NON-CAUSAL: no intervention
effect is claimed or estimable (observational data).

| Arm | k | n_rounds | Precision@k (Wilson95) | Recall@k = failure capture (Wilson95) | NDCG@k | Fairness gap (Y−N) | Capacity violations |
|---|---|---|---|---|---|---|---|
| C0 random-eligible | 25 | 29 | 0.199 [0.171, 0.229] | 0.054 [0.046, 0.063] | 0.217 | 0.061 | 0 |
| C0 random-eligible | 50 | 29 | 0.216 [0.195, 0.238] | 0.114 [0.103, 0.127] | 0.293 | 0.027 | 0 |
| C0 random-eligible | 100 | 29 | 0.221 [0.206, 0.237] | 0.219 [0.203, 0.235] | 0.433 | -0.079 | 0 |
| C1 risk-only top-k | 25 | 29 | 0.410 [0.374, 0.446] | 0.110 [0.099, 0.123] | 0.461 | 0.805 | 0 |
| C1 risk-only top-k | 50 | 29 | 0.356 [0.331, 0.381] | 0.188 [0.174, 0.203] | 0.509 | 0.199 | 0 |
| C1 risk-only top-k | 100 | 29 | 0.303 [0.286, 0.321] | 0.299 [0.282, 0.317] | 0.617 | -0.012 | 0 |
| PROPOSED budget+equity+gates | 25 | 29 | 0.408 [0.373, 0.444] | 0.110 [0.099, 0.122] | 0.460 | 0.805 | 0 |
| PROPOSED budget+equity+gates | 50 | 29 | 0.356 [0.331, 0.381] | 0.188 [0.174, 0.203] | 0.509 | 0.199 | 0 |
| PROPOSED budget+equity+gates | 100 | 29 | 0.303 [0.286, 0.321] | 0.299 [0.282, 0.317] | 0.617 | -0.012 | 0 |
| A1 no calibrated uncertainty | 25 | 29 | 0.408 [0.373, 0.444] | 0.110 [0.099, 0.122] | 0.460 | 0.805 | 0 |
| A1 no calibrated uncertainty | 50 | 29 | 0.356 [0.331, 0.381] | 0.189 [0.174, 0.204] | 0.511 | 0.199 | 0 |
| A1 no calibrated uncertainty | 100 | 29 | 0.303 [0.286, 0.321] | 0.300 [0.283, 0.317] | 0.619 | -0.041 | 0 |
| A2 no capacity constraint | 25 | 29 | 0.201 [0.194, 0.208] | 0.935 [0.925, 0.943] | 0.462 | -9.295 | 29 |
| A2 no capacity constraint | 50 | 29 | 0.201 [0.194, 0.208] | 0.935 [0.925, 0.943] | 0.510 | -3.277 | 27 |
| A2 no capacity constraint | 100 | 29 | 0.201 [0.194, 0.208] | 0.935 [0.925, 0.943] | 0.617 | -0.912 | 22 |
| A3 no evidence/risk gates | 25 | 29 | 0.367 [0.333, 0.403] | 0.099 [0.088, 0.111] | 0.417 | 0.945 | 0 |
| A3 no evidence/risk gates | 50 | 29 | 0.335 [0.311, 0.360] | 0.178 [0.164, 0.193] | 0.469 | 0.125 | 0 |
| A3 no evidence/risk gates | 100 | 29 | 0.286 [0.269, 0.303] | 0.287 [0.270, 0.304] | 0.574 | 0.040 | 0 |
| A4 no equity bound | 25 | 29 | 0.410 [0.374, 0.446] | 0.110 [0.099, 0.123] | 0.461 | 0.805 | 0 |
| A4 no equity bound | 50 | 29 | 0.356 [0.331, 0.381] | 0.188 [0.174, 0.203] | 0.509 | 0.199 | 0 |
| A4 no equity bound | 100 | 29 | 0.303 [0.286, 0.321] | 0.299 [0.282, 0.317] | 0.617 | -0.012 | 0 |

Recall@k = |selected ∩ Fail| / |Fail| per cohort, pooled over the 7
test cohorts (denominator = all Fail cases in scored cohorts).
Suppressed cells (n<5) propagate as —, never as fabricated numbers.
