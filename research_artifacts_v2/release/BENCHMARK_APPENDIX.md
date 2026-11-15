# Research V2 Benchmark Appendix

> Every baseline actually executed, including failures. No published number was
> copied into this appendix. C2 (original published model) was **not run**.

| Tier | Method | Attribution | Comparable task | Status | Notes |
|---|---|---|---|---|---|
| C0 | `baselines_b0` | Reimplementation (sanity) | yes | RUN | Cannot support any SOTA claim. May be trivially beaten. |
| C1 | `baselines_c1` | Reimplementation of a classical algorithm | yes | RUN | Serious comparator required by the charter. Not the authors' code. |
| C1-ablation | `ablations_a1` | Proposed policy minus mechanism 1 | yes | RUN | Mechanism isolation. |
| C1-ablation | `ablations_a2` | Proposed policy minus mechanism 2 | yes | RUN | Mechanism isolation. |
| C1-ablation | `ablations_a3` | Proposed policy minus mechanism 3 | yes | RUN | Mechanism isolation. |
| C2 | `c2_published` | NOT RUN | n/a | **BLOCKED** | No source/weights/license compatible with these policy tasks. Published metrics were NOT imported. |

## Failure / negative results (preserved)

- LN-06, LN-07, LN-09: at least one ablation ties the proposed policy on this
  synthetic dataset. Reported as PARTIAL, not tuned away.
- LN-07 `ablations_a1`: no transcript-failure stratum exists in the T3 gold, so
  the ablation is observationally identical there. Disclosed in the study prereg.
- LN-09 `ablations_a3`: no small-cohort (n<5) cases exist in T3; k-anonymity
  divergence is proven only on a targeted counterexample test.

## Resource and determinism notes

- All cells run with fixed seeds 11/23/37; identical `predictions_sha256`
  across seeds for deterministic policy methods.
- Wall time and environment are recorded per cell in `run_manifest.json`.
- Statistics: exact McNemar on paired cases, Holm-Bonferroni across 10 studies,
  cluster bootstrap (by group) for paired differences.
