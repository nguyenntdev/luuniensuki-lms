# Reproducing the 10 Educational Research Studies (LN-01 to LN-10)

This repository contains the full executable suite and reproduction pipeline for all 10 studies on the 7,200 frozen synthetic scenarios across 5 conditions (36,000 policy executions total) plus 1,200 independent holdout scenarios across 10 studies.

All tools, fixtures, adapters, and reproduction scripts are completely self-contained within the repository.

## Prerequisites

- Python 3.11+ with `pip install -r backend/requirements.txt -r backend/requirements-dev.txt`
- Clean git checkout on a commit derived from ancestral commit `54da2beb71f3df70e1f00b215ae0fb1a850eb263`.

---

## One-Command Full Reproduction

To run the complete end-to-end reproduction pipeline (clean environment check, 50-condition benchmark matrix, 10 independent holdout evaluations, statistical significance metrics, publication tables, and release readiness verification):

```bash
python3 research/tools/reproduce_all.py --all
```

Or target specific reproduction phases:

```bash
# 1. Benchmark matrix only (50 conditions across LN-01..LN-10)
python3 research/tools/reproduce_all.py --benchmark --output /tmp/reproduction_output

# 2. Independent holdout evaluations (120 cases × 10 studies)
python3 research/tools/reproduce_all.py --holdout

# 3. Statistical significance metrics (McNemar, Risk Reduction, 95% CIs)
python3 research/tools/reproduce_all.py --statistics

# 4. Generate publication tables and verify release readiness
python3 research/tools/reproduce_all.py --verify
```

---

## Modular Step-by-Step Reproduction (Self-Contained)

### Step 1: Verify Sources and Fixtures Integrity

```bash
python3 research/tools/check_sources.py
```

Expected output:
```json
{
  "status": "PASS",
  "spec_verified": 11,
  "fixture_total": 7200,
  "issues": []
}
```

### Step 2: Execute All 50 Benchmark Runs

```bash
OUT_DIR="/tmp/reproduced_evidence_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT_DIR"

python3 research/tools/run_all.py \
  --output "$OUT_DIR" \
  --workers 10
```

### Step 3: Verify Technical Release Gate

```bash
python3 research/tools/verify_release.py --output "$OUT_DIR"
```

Expected output:
```json
{
  "status": "SOFTWARE_EVIDENCE_TECHNICALLY_COMPLETE",
  "verified_runs": 50,
  "case_executions": 36000,
  "blockers": []
}
```

### Step 4: Generate Verified LaTeX and CSV Table Fragments

```bash
python3 research/tools/generate_results_tables.py --output "$OUT_DIR"
```

Generates:
- `manuscript_tables/LN-01_results.tex` ... `LN-10_results.tex`
- `manuscript_tables/LN-01_results.csv` ... `LN-10_results.csv`
