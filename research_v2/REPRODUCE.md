# Reproduce — Research V2

All Research V2 data are **synthetic held-out test sets**. No real learner,
expert, or external dataset is involved. Legacy `research/` and
`research_artifacts/` are read-only historical evidence and are never modified
by these commands.

Run from the repository root:

```bash
# 0. Dependencies
pip install -r backend/requirements.txt -r backend/requirements-dev.txt numpy scipy pyyaml

# 1. Byte-compile the V2 package
python -m compileall -q research_v2

# 2. Run the V2 test suite (contracts, auditing, integration, all 10 studies)
python -m pytest -q tests/research_v2

# 3. Repository inspection (writes research_v2/reports/G0_repo_audit.json)
python -m research_v2.scripts.inspect_repo --strict

# 4. Integrity verification (fail-closed; legacy 1,200 holdout rows + V2 manifest)
python -m research_v2.scripts.verify_integrity --legacy-and-v2 --strict

# 5. Materialize synthetic V2 datasets from the frozen legacy holdouts
python -m research_v2.scripts.materialize_datasets --all

# 6. Experiment matrix — dry-run first, then the full locked run
python -m research_v2.scripts.run_matrix --study LN-06 --tier T3 --seed 11 --dry-run
python -m research_v2.scripts.run_matrix --all --tier T1,T2,T3 --strict

# 7. Aggregate metrics into the evidence matrix
python -m research_v2.scripts.aggregate --all --preregistered-only

# 8. Freeze a release (asserts a clean source tree; generated artifacts allowed)
python -m research_v2.scripts.freeze_release --all --assert-clean
```

## Outputs

- `research_artifacts_v2/runs/<STUDY>/<TIER>/<METHOD>/seed<N>/`
  - `predictions.jsonl` — oracle-free predictions
  - `metrics.json` — accuracy, error rate, Wilson + Clopper-Pearson CIs
  - `run_manifest.json` — commit, dataset SHA-256, seed, wall time, status
- `research_artifacts_v2/release/`
  - `evidence_matrix.csv`, `aggregate_summary.json`, `paired_statistics.json`
  - `SCIENTIFIC_READINESS.md`, `BENCHMARK_APPENDIX.md`, `NEXT_RESEARCH_WORK.md`
  - `release_manifest.json` — SHA-256 of every V2 source/test file

## Invariants enforced

- Gold labels are read **only** by the evaluator, after predictions are written.
- Model inputs never contain `oracle`, `expected_decision`, `fault_id`, `cohort`,
  `gold`, or `label` keys, at any nesting depth.
- No `||` fallback can mask a failing study; strict mode aborts on any cell error.
- All data are labeled synthetic; nothing claims human adjudication.
