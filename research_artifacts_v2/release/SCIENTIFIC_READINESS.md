# Research V2 Scientific Readiness

> Auto-generated from sealed T3 holdout runs. PASS requires proposed > C1 and
> proposed > every ablation on the declared primary endpoint. All data are
> synthetic held-out test sets with programmatic oracles — NOT human-adjudicated.

| Study | proposed | C1 | B0 | ablations (a1/a2/a3) | Status |
|---|---|---|---|---|---|
| LN-01 | 1.000 | 0.600 | 0.200 | 0.800 / 0.800 / 0.800 | PASS |
| LN-02 | 1.000 | 0.483 | 0.400 | 0.600 / 0.800 / 0.800 | PASS |
| LN-03 | 1.000 | 0.400 | 0.200 | 0.800 / 0.800 / 0.800 | PASS |
| LN-04 | 1.000 | 0.200 | 0.000 | 0.800 / 0.600 / 0.800 | PASS |
| LN-05 | 1.000 | 0.500 | 0.200 | 0.800 / 0.800 / 0.800 | PASS |
| LN-06 | 1.000 | 0.600 | 0.800 | 0.800 / 1.000 / 1.000 | PARTIAL (ablation ties proposed on this synthetic set) |
| LN-07 | 1.000 | 0.200 | 0.200 | 1.000 / 0.800 / 1.000 | PARTIAL (ablation ties proposed on this synthetic set) |
| LN-08 | 0.800 | 0.392 | 0.400 | 0.400 / 0.600 / 0.600 | PASS |
| LN-09 | 1.000 | 0.400 | 0.200 | 0.800 / 0.600 / 1.000 | PARTIAL (ablation ties proposed on this synthetic set) |
| LN-10 | 1.000 | 0.600 | 0.200 | 0.600 / 0.800 / 0.800 | PASS |

## Interpretation

- PASS = the proposed policy beats the serious classical baseline and every ablation
  on this synthetic held-out set. It is NOT evidence of classroom learning gains.
- PARTIAL = at least one ablation is not separable on this dataset (an honest
  negative result, disclosed rather than tuned away).
- B0 is a sanity baseline; C1 is a reimplementation, not the authors' original code.
- No real students, no human adjudication, no external LLM inference is claimed.
