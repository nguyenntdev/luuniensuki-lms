# Research V2 Scientific Readiness

> Auto-generated from sealed synthetic held-out runs (tiers: T3, T3S).
> STRICT rule: PASS requires proposed > C1 AND proposed > EVERY ablation on the
> mean primary endpoint. Equality with an ablation is PARTIAL, never PASS.
> All data are synthetic held-out test sets with programmatic oracles — NOT
> human-adjudicated external validation.

| Study | proposed | C1 | B0 | ablations (a1/a2/a3) | Status |
|---|---|---|---|---|---|
| LN-01 | 1.000 | 0.600 | 0.200 | 0.800 / 0.800 / 0.800 | PASS |
| LN-02 | 1.000 | 0.483 | 0.400 | 0.600 / 0.800 / 0.800 | PASS |
| LN-03 | 1.000 | 0.400 | 0.200 | 0.800 / 0.800 / 0.800 | PASS |
| LN-04 | 1.000 | 0.200 | 0.000 | 0.800 / 0.600 / 0.800 | PASS |
| LN-05 | 1.000 | 0.500 | 0.200 | 0.800 / 0.800 / 0.800 | PASS |
| LN-06 | 1.000 | 0.600 | 0.800 | 0.800 / 1.000 / 1.000 | PARTIAL (ties a2/a3) |
| LN-07 | 1.000 | 0.200 | 0.200 | 1.000 / 0.800 / 1.000 | PARTIAL (ties a1/a3) |
| LN-08 | 0.800 | 0.392 | 0.400 | 0.400 / 0.600 / 0.600 | PASS |
| LN-09 | 1.000 | 0.400 | 0.200 | 0.800 / 0.600 / 1.000 | PARTIAL (ties a3) |
| LN-10 | 1.000 | 0.383 | 0.183 | 0.800 / 0.483 / 0.900 | PASS |

**Summary: 7 PASS, 3 PARTIAL, 0 BLOCKED of 10 studies.**

## Interpretation

- PASS = the proposed policy strictly beats the serious classical baseline and every
  ablation on these synthetic held-out sets. NOT evidence of classroom learning gains.
- PARTIAL = at least one ablation is not separable on the available synthetic data
  (honest negative result, disclosed rather than tuned away). It does NOT mean the
  mechanism is unnecessary; it means this dataset cannot separate it.
- B0 is a sanity baseline; C1 is a reimplementation, not the authors' original code.
- No real students, no human adjudication, no external LLM inference is claimed.
- LN-10 adds a V2-authored T3S stress cell exercising same-version divergent offline
  edits (the mandatory counterexample) inside the matrix run.
