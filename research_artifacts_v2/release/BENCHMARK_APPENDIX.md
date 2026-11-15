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

## Execution matrix

- 10 studies x (proposed + 6 comparators) x 3 seeds, plus one extra LN-10
  stress cell (T3S) exercising same-version divergent offline edits.
- Every cell writes `predictions.jsonl` (oracle-free), `run_manifest.json`
  (commit, dataset SHA, seed, wall time, status) and `metrics.json`.

## Failure / negative results (preserved)

- LN-06, LN-07, LN-09: at least one ablation ties the proposed policy on this
  synthetic dataset. Reported as PARTIAL, not tuned away.
- LN-07 `ablations_a1`: no transcript-failure stratum exists in the T3 gold, so
  the ablation is observationally identical there. Disclosed in the study prereg.
- LN-09 `ablations_a3`: no small-cohort (n<5) cases exist in T3; k-anonymity
  divergence is proven only on a targeted counterexample test.
- LN-05 `ablations_a1`: 0.800 (restored after a task-identity regression that
  was caught by the review and fixed; no tuning).

## Resource and determinism notes

- All cells run with fixed seeds 11/23/37; deterministic policy methods produce
  identical `predictions_sha256` across seeds, so the seeds add no variance
  information today (disclosed, not hidden).
- Wall time and environment are recorded per cell in `run_manifest.json`.
- Statistics: exact McNemar on paired cases, Holm-Bonferroni across 10 studies,
  group-cluster bootstrap for paired differences.

## Independent review findings (addressed)

Results were reviewed in rotating pairs (A01<->A06, A02<->A07, A03<->A08,
A04<->A09, A05<->A10); reviewers could not self-sign. Findings:

- **LN-05 (critical):** the replay identity previously included delivery-variant
  fields (`timestamp`, `event_id`), so a redelivery with a mutated timestamp
  could earn a second award. A mis-named test tolerated the bypass. Fixed to a
  normalized submission identity; the test now asserts rejection; canaries added.
- **Core contracts:** the forbidden-key scan was one level deep; now recursive to
  arbitrary nesting. `features` is deep-frozen after validation.
- **Metrics:** the gold-smuggle filter was expanded; coverage now rejects extra
  predictions and duplicate case ids (two-sided, fail-closed).
- **verify_integrity:** now fail-closed by default (nonzero exit on issues) and
  recomputes manifest SHA-256 and case counts against disk.
- **freeze_release:** assert-clean is now the default; generated artifacts stay
  allowlisted so a release can be frozen right after a run.
- **Runner:** a metrics failure now marks the cell FAIL and aborts strict runs;
  a declared-but-missing gold file is a hard failure.
- **LN-10:** added a V2-authored T3S stress dataset (24 cases, pair-grouped) that
  exercises same-version divergent offline edits inside the matrix, not only in
  unit fixtures.
- **LN-09:** `splits.yaml` corrected to the true 5x24 distribution; it now states
  that no small-cohort and no descriptive-only cases exist in T3.
- **LN-03:** the invalid-generative-assignment denominator is now explicit and
  the numerator can no longer exceed it.
- **LN-06:** the brute-force rubric now implements cycle detection independently
  of the policy under audit.
- **LN-01:** every prediction is validated against the study's native frozen
  gold vocabulary.
- **LN-02:** typed guards for `None` and boolean score/threshold inputs.

## Known limitations (do not over-read these results)

- All data are synthetic held-out test sets with programmatic oracles.
- No real students, no human expert adjudication, no external LLM inference.
- Significance is computed over correlated, template-generated cases and is NOT
  independent human evidence.
- T1 (licensed external) and T2 (real Huế expert annotations) datasets are
  BLOCKED; see `NEXT_RESEARCH_WORK.md`.
