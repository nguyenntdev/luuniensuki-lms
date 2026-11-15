# Research V3 — Reproduce

All commands run from the repository root. Python 3.11+ (CI uses 3.11; the run artifacts
recorded here were produced on 3.12.3, x86_64). Runtime deps: `numpy`, `scipy`, `pyyaml`.

`private_data/` is **gitignored** (line 90 of `.gitignore`). Raw licensed archives (OULAD
zip + extraction, UCI student-performance, Smithsonian captures) live only there. Without
those files, the data-dependent run CLIs fail closed; the audit/gate CLIs and the test
suite do not need them.

## 0. Environment sanity

```bash
python -m compileall -q research_v3
```

Expected: no output (all modules compile). CI: `.github/workflows/research-v3.yml` step
"Compile research_v3 (strict)".

## 1. Test suite

```bash
python -m pytest -q tests/research_v3
```

Collected: **675 tests**. Last full run (2026-11-15): **1 failed, 671 passed, 3 skipped** —
the single failure is `tests/research_v3/method/test_p13_corpus_guard.py::
test_run_artifacts_pass_guard_when_present`, which fails because
`research_artifacts_v3/runs/p13/task_status.json` contains phrasing the P13
construct-validity guard forbids ("measured srl", "srl measurement"). The artifact must be
reworded/regenerated; see `NEXT_RESEARCH_WORK.md` §2. The guard itself is working as
designed — it aborts on overclaiming artifacts.

Known-good subsets (verified 2026-11-15):

```bash
python -m pytest -q tests/research_v3/contracts tests/research_v3/baseline \
  tests/research_v3/data tests/research_v3/evaluation \
  tests/research_v3/privacy tests/research_v3/scientific   # 62 passed, 2 skipped
python -m pytest -q tests/research_v3/integration          # 28 passed
```

## 2. Governance gates (fail-closed)

```bash
# G00/G11 — pin source lock: git SHA + SHA-256 file inventory into a fresh
# data_frozen/source_lock_*.json. Fails on a dirty tree unless --allow-dirty.
python -m research_v3.scripts.audit_repo --source-sha "$(git rev-parse HEAD)" --allow-dirty --strict
# Last verified: OK, head=4e5a792e1625... files=319

# G02 — license gate. Currently FAILS (21 violations) while paper-required
# datasets are BLOCKED / unregistered. That failure is the honest state.
python -m research_v3.scripts.verify_licenses --all --strict

# G03 — contract round-trip validation
python -m research_v3.scripts.validate_contracts

# G05 — baseline registry verification
python -m research_v3.baselines.verification.verify_baselines

# G09 — ethics audit (expected BLOCKED, exit 20, until a signed record exists
# under research_v3/governance/ethics/)
python -m research_v3.scripts.ethics --json
```

## 3. Split protocol validation (G04)

```bash
# Requires a JSONL rows file with case_id/group_id/time_key/input/label.
# CI builds a 200-row synthetic fixture; the real data variant needs private_data/.
python -m research_v3.scripts.validate_splits --paper P06 --rows <rows.jsonl> --protocol group
python -m research_v3.scripts.validate_splits --paper P13 --rows <rows.jsonl> --protocol time
```

## 4. Per-paper run CLIs (write into research_artifacts_v3/runs/pXX/)

Each CLI is deterministic under its recorded seed and writes a run manifest + experiment
card. Data-dependent ones require `private_data/raw/...` (gitignored).

```bash
# P01 — preregistered risk-controlled gate evaluation on OULAD (needs private_data)
python -m research_v3.experiments.p01.run_p01 --out research_artifacts_v3/runs/p01 --seed 0

# P02 — synthetic benchmark with certified optima (self-contained)
python -m research_v3.methods.p02.benchmark \
  --instances-per-cell 30 --seed 20261115 --out research_artifacts_v3/runs/p02

# P03 — MRBench decision-layer matrix (fetch step needs network)
python -m research_v3.experiments.p03.run_matrix --seed 20261115

# P04 — reference leaderboard on OULAD + UCI (needs private_data; no CLI flags)
python -m research_v3.methods.p04.run_reference_eval

# P05 — forgetting-aware KT matrix on OULAD (needs private_data)
python -m research_v3.methods.p05.run_p05_matrix            # add --quick for a fast pass

# P06 — budgeted prioritization matrix on OULAD (needs private_data)
python -m research_v3.experiments.p06.run_experiment        # add --verify-only to recheck

# P07 — frozen selection matrix (Smithsonian CC0 + synthetic stress)
python -m research_v3.experiments.p07.run_matrix --out research_artifacts_v3/runs/p07

# P08 — reward-integrity campaign (self-contained, deterministic fixtures)
python -m research_v3.methods.p08.runner --out research_artifacts_v3/runs/p08

# P09 — Wikidata provenance pipeline (build/evaluate/all; evaluate works offline
# against the frozen snapshot; build needs network)
python -m research_v3.experiments.p09.run_p09 all

# P10 — spiral curriculum design certificates (self-contained)
python -m research_v3.methods.p10.cli run --seed 42

# P12 — source-audit ledger (self-contained; add --with-wikidata for the CC0 probe)
python -m research_v3.methods.p12.audit_cli --out research_artifacts_v3/runs/p12

# P13 — SRL proxy analysis on OULAD (needs private_data; ~5 min CPU)
python -m research_v3.methods.p13.run_p13 --boot 2000

# P14 — UDL/WCAG object audit (self-contained synthetic manifest by default)
python -m research_v3.methods.p14.cli_audit --out research_artifacts_v3/runs/p14 --baselines
# or: python -m research_v3.experiments.p14.run_experiment
```

P11 has no run CLI: it is BLOCKED pending human raters
(`python3 research_v3/methods/p11/reliability.py` runs the synthetic-only harness smoke,
which is never a result). P11 status: `python -m research_v3.experiments.p11.p11_status`.

## 5. Release accounting

```bash
# Regenerate release/progress.json from on-disk ledgers + artifacts (fail-closed;
# the register's own status column is ignored).
python -m research_v3.scripts.progress_report
# Last verified output: 318 tasks | 274 non-human | 44 human-only
# 98 DONE / 220 BLOCKED (non-human: 98 DONE / 176 BLOCKED)

# G18 — cross-paper primary-claim dedup (nonzero exit on collision)
python -m research_v3.scripts.cross_paper_dedup
# Last verified: OK, no duplicated primary claim — but 5 prereg YAMLs (p05, p08,
# p10, p13, p14) are SKIPPED as unparseable; fix before trusting full coverage.

# G23 — cross-verify release tier claims against executed manifests
python -m research_v3.scripts.cross_verify_claims \
  --runs-root research_artifacts_v2/runs --release research_artifacts_v2/release
# Last verified: OK (198 manifests, all PASS)

# G23 for the V3 tree — release docs vs V3 run manifests
python -m research_v3.scripts.cross_verify_claims \
  --runs-root research_artifacts_v3/runs --release research_artifacts_v3/release
```

## 6. Result-integrity audit (anti-distortion)

Recomputes reported metrics from raw predictions + sealed gold; fails on tampering,
dropped cases, gold leaks, stale hashes, non-finite values:

```bash
# V2 tree (CI hard gate, --min-cells 190)
python -m research_v3.scripts.result_integrity --runs-root research_artifacts_v2/runs --min-cells 190

# Single cell or the V3 tree (adjust --pattern to the tree layout)
python -m research_v3.scripts.result_integrity --cell <path/to/run/cell>
python -m research_v3.scripts.result_integrity --runs-root <dir> --pattern '*/*/*/*/metrics.json' --json
```

## 7. Stress parity suites (G15–G17)

```bash
python -m research_v3.scripts.stress_parity --suite ln06_external_solver_parity
python -m research_v3.scripts.stress_parity --suite ln07_transcript_failure
python -m research_v3.scripts.stress_parity --suite ln09_small_cohort
```

## Notes

- Deterministic reruns must reproduce the recorded artifact hashes byte-for-byte; the
  replication guard (`python -m research_v3.scripts.replicate --runs-root <runs> --kind
  deterministic|stochastic`) enforces this.
- Anything that cannot be reproduced by the commands above should be treated as UNVERIFIED
  and must not be quoted in release docs.
- Do not commit `private_data/` or freshly generated `data_frozen/source_lock_*.json`
  files produced by local reruns unless the release process calls for it.
