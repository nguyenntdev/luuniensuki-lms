# Highest-priority independent source findings at main SHA `6debec2`

## CRITICAL FOR CLAIMS — CLI flags silently ineffective
The actual `research_v2/scripts/run_matrix.py` parses `--tier` and `--seed`, but does not use them to filter the loaded matrices. For instance `--all --tier T1,T2,T3 --strict` executes the YAML cells, presently T3 plus LN10 T3S. It DOES NOT imply T1/T2 external/expert evidence was executed.

**Required remediation:** make `--tier` and `--seed` effective, test selection against cells, or reject both unsupported arguments explicitly with a nonzero exit. `--dry-run` currently only verifies matrix-path existence rather than validating cell schema/data checks; create an actual dry-run preview that prints exact selected study/tier/method/seed, blocked reasons and counts. Add nonzero exit on empty selection unless explicitly allowed. Ensure every claim reports actual executed tiers from run manifests rather than CLI string.

## MEDIUM — benchmark appendix arithmetic documentation error
`BENCHMARK_APPENDIX.md` says “proposed + 6 comparators” while the matrices list proposed + B0 + C1 + A1 + A2 + A3, i.e. one method plus **five** comparators. Actual cell count is 10 × 6 × 3 + LN10 T3S 6 × 3 = 198. Fix the appendix wording and verify release counts against selected YAML, not hand-entered prose.

## MEDIUM — audit provenance head/pin
`research_v2/reports/G0_repo_audit.json` observes earlier SHA `6857442...` and pin `abcfab2...`, with dirty worktree flag recorded during previous run. This file is historical; regenerate a fresh actual-source lock and distinguish audit-worktree state from current checked GitHub commit. The CI success at current main does not turn stale JSON fields into current values.

## HIGH FOR SCIENTIFIC READINESS — unpublished comparators and data
`research_v2/data/manifest.json` has 10 T1 external and 10 T2 Huế expert entries as BLOCKED. C2 original published implementations are BLOCKED. Synthetic results (7 PASS, 3 PARTIAL) do not authorize external SOTA or human learning gain claims. Extend per-P externally evaluated runs before manuscripts.

## MEDIUM — near-ceiling rule-oracle saturation
Several policy proposed methods reach 1.000 accuracy against internally specified synthetic decision oracles. This shows rules conform to rules under stress samples; it is not evidence the model solves independently labeled learning problems. New manuscripts must use real external target outcomes and independent annotation where appropriate, with calibration and error analysis.

## HIGH — LN-06/07/09 mechanism identifiability
The frozen scored T3 set cannot distinguish select ablations (LN-06 A2/A3; LN-07 A1/A3; LN-09 A3). Add new *predeclared* external/stress strata (transcript required, small cohort n<5, alternative provider/cycle) and preserve the original T3 ties unchanged. Do not alter old frozen labels to force PASS.

## Workflow source verification
GitHub Actions head SHA `6debec2` reports Research V2, CI and Deploy workflow runs all `completed/success` by 15 Nov 2026 12:59 GMT+7. Those are software integration checks, not independent confirmation of scientific validity.

## Legacy completion must not be conflated with new 14-paper completion
Read `research/task_register_executed.csv`: all 720 entries (72 per LN-01..LN-10) have status `DONE`, with legacy validation commands/evidence references. This is a valuable completed implementation checklist and must not be rerun as 720 new tickets, but cannot establish external data, published SOTA comparator, independent 14 paper novelty or human-validated learning outcomes. V3 adds 318 new distinct tasks and tracks inherited legacy assets separately.
