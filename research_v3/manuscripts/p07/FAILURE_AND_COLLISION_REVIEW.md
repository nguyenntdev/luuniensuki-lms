# P07 — Scientific Failure Review & Collision Audit (P07-T16)

**Reviewer role:** code agent (P07 scope) · **Date:** 2026-11-15 ·
**Human signoff:** NOT SUBSTITUTED (P07-T20 remains BLOCKED).

## 1. Falsification outcomes (preserved, not cherry-picked)

| Falsifiable claim | Outcome | Evidence |
|---|---|---|
| Proposed beats C1 after Holm correction (stress suite) | **NOT ESTABLISHED** — raw McNemar p=0.0078, Holm-adjusted p=0.125 ⇒ H0 not rejected at family-corrected α=0.05 | results.json → multiple_testing.family |
| Proposed eliminates false completion on stress strata | **ESTABLISHED** on this suite (0.000 vs ≥0.353 for all baselines; denominator 17) | results.json → suites.stress_synthetic.methods |
| Removing affordance coverage (A1) causes the named failure family | **CONFIRMED** — A1 flips exactly the paired transcript/inscription negatives to false completion | results.json → ablations; test_p07_stress_strata.py |
| Removing rights filtering (A5) causes rights violations | **CONFIRMED** — 1 violation / 16 selects (S5 all-unknown-license) | results.json → ablations.stress_synthetic__A5 |
| Removing device checks (A2) causes device-strata failures | **CONFIRMED** — A2 accepts bandwidth-heavy audio on the 120 kbps/100 KB budget case (fc 0.0625) and selects 3D for WebGL-less devices | results.json → ablations |
| Affordance-complete selection transfers to real provider metadata | **PARTIAL ONLY** — external suite n=8, single provider, p=0.125; pipeline runs, no population claim permitted | results.json → suites.external_smithsonian_fsg |
| Determinism / no pseudo-replication | **PASSED** — rerun produces identical prediction hash; no 3-identical-hashes-as-3-seeds trick used | results.json → determinism_check |

**Negative/null results are retained:** the primary Holm-corrected contrast is
null; the external suite is underpowered; A3/A4 ablations were NOT run (dated
rationale in matrix.yaml). None are dropped from the record.

## 2. Leakage audit

- `audit_rows` (research_v3/eval/leakage.py) over generated case rows: PASS
  (no gold keys in model inputs; no duplicate case_ids; no future-info keys).
- Gold verdicts derived from object affordance/license facts only
  (`runner.gold_from_cases`) — independent of any method output; verified by
  test_p07_evaluation.py::test_gold_derivation_is_independent_of_model_output.
- Selector consumes no oracle/gold fields at inference (unit-tested).

## 3. Collision audit (salami-slicing / duplicate outcomes)

| Paper | Overlap risk | Decision |
|---|---|---|
| **P14** (UDL pedagogy + human evaluation) | shares the affordance vocabulary concept | P07 owns the SELECTION ALGORITHM + algorithmic evaluation; P14 owns pedagogical design + human evaluation. No shared primary outcome table. Per task register: "P14 nhấn mạnh giá trị sư phạm...; P07 thử nghiệm retrieval/ranking. Không dùng chung một bảng làm outcome chính." RESPECTED. |
| **V2 LN-07** | same counterexample family (raster w/o inscription) | LN-07 is the internal predecessor; P07 does NOT reuse LN-07's T3 scores as external evidence (spec §2 rule). P07 rebuilds the stress suite under the V3 typed contract and adds real provider metadata + rights screen + identifiability pairs. Cited as prior internal work; not co-published as separate novelty for the same outcome. |
| **P06/P13** (observational ≠ causal) | none — P07 makes no causal claims | OK |
| **P08/P09/P14** (UX/human gains) | none — P07 claims zero learning gains | OK |

**Nearest external work:** constraint-aware object filtering in digital
libraries and WCAG-based accessibility checkers; classical knapsack/BM25/
CLIP retrieval families (B00–B03) target availability/similarity/budget, not
pedagogical affordance coverage. A formal nearest-work matrix with 2026
full-texts requires the human signoff task (P07-T20, BLOCKED) — this audit
records the internal collision decisions only.

## 4. Salami-slicing check

P07's single primary endpoint (task_feasibility_rate exact-match) and one
preregistered contrast family are used across both suites; no secondary
metric is re-featured as an independent primary claim. The identifiability
pairs are a stress diagnostic, not a headline win.

## 5. Decision

**Status: ENGINEERING_PASS / BENCHMARK_PARTIAL.** Not SCIENTIFIC_REVIEW_READY:
(a) primary H0 not rejected after correction — must be disclosed as a null
superiority result with mechanism-level evidence; (b) single external
provider; (c) B00–B03 baselines not runnable this wave (dated BLOCKED
rationale recorded in manuscript §7); (d) human signoffs (T19/T20/T21)
outstanding.
