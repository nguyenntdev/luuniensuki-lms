# Research V4.2 — Scientific Readiness and Automated Release Gates Report

**Date:** 2026-11-20  
**Repository:** `nguyenntdev/luuniensuki-lms`  
**Framework Version:** `research_v4_2` v4.2.0  
**Phase:** Global Infrastructure & 8 Automated Release Gates (Tickets V42-G01 to V42-G22: COMPLETED)

---

## Current benchmark scope

For comparisons that can be scored with published external labels, follow [the external benchmark protocol](../external/README.md). The six paper-level fixture suites (P01, P04, P07, P11, P12, P13) exercise software. Their generated outcomes do not supply external cohort, archive, rater, or sign-off evidence. Use per-run external predictions and uncertainty estimates for empirical claims.

## 1. Executive Summary

Research V4.2 replaces heuristic and ungrounded "win" assertions with an evidence-first, novelty-gated, and statistically calibrated release pipeline. In V4.2:
1. **No algorithmic superiority can be declared without passing independent, pre-registered evaluation against the strongest task-compatible baseline champion ($B^*$).**
2. **False green CI pipelines are systematically eliminated.** The test runner fails on any unhandled error, nonzero exit code, or masked failure behind pipelines (`set -euo pipefail`).
3. **Novelty requires human expert verification.** Automated agents are strictly prohibited from self-certifying novelty.
4. **All claims are backed by raw prediction recomputation, cluster-aware bootstrap confidence intervals, and familywise error rate (FWER) multiplicity controls.**

---

## 2. The 8 Automated Release Gates

| Gate Index | Module Name | Command Interface | Primary Validation Invariants |
|---|---|---|---|
| **Gate 1** | `test_exit` | `python -m research_v4_2.gates.test_exit` | Catches non-zero pytest exit codes and log banners (`failed`, `error`). Blocks masked failures behind pipes or `tee`. |
| **Gate 2** | `preregister` | `python -m research_v4_2.gates.preregister` | Enforces canonical SHA-256 hash lock on preregistered hypotheses, baseline champion $B^*$, primary metric, $\delta_{\min}$, and pre-test method code hashes. Rejects post-hoc relaxations. |
| **Gate 3** | `novelty` | `python -m research_v4_2.gates.novelty` | Verifies $\ge 3$ closest prior works with DOIs, direct overlap analysis, formal counterexamples, N1–N7 criteria, and independent human expert sign-off (`signed=True`). Absent review $\Rightarrow$ `BLOCKED`. |
| **Gate 4** | `baseline_parity` | `python -m research_v4_2.gates.baseline_parity` | Enforces exact denominator parity (`len(cand) == len(base) == len(gold)`), case ID alignment, coverage parity, and train/test leakage audit (intersection must be $\emptyset$). |
| **Gate 5** | `statistical_claims` | `python -m research_v4_2.gates.statistical_claims` | Recomputes metrics from raw predictions + ground truth, evaluates $\Delta = M(\text{cand}) - M(B^*) \ge \delta_{\min}$, calculates 95% cluster-resampled bootstrap CI (lower bound $> 0$), and applies Holm-Bonferroni multiplicity correction ($p_{\text{adj}} < 0.05$). Rejects underpowered datasets ($n < 30$, $n_{\text{clusters}} < 5$). |
| **Gate 6** | `integrity` | `python -m research_v4_2.gates.integrity` | Recomputes canonical UTF-8 SHA-256 of all contract cards and data splits. Rejects non-portable machine-specific paths (e.g. `/home/clue`). Detects multiple evaluations on the sealed test set (one-shot test enforcement). |
| **Gate 7** | `license_ethics` | `python -m research_v4_2.gates.license_ethics` | Validates open data licenses (CC-BY, MIT, Apache) and human-subject ethics/IRB clearance. Explicitly recognizes user-authorized imperial Vietnamese heritage sources (*Châu bản triều Nguyễn*, *Đại Nam thực lục*, *Cửu Đỉnh*). |
| **Gate 8** | `cross_paper` | `python -m research_v4_2.gates.cross_paper` | Detects duplicate estimands or identical claim IDs across papers P01–P14. Strictly enforces distinct scopes between P07 (multimedia rights) vs P14 (accessibility) and P09 (evidence grounding) vs P12 (archival ledger). |

---

## 3. Global Infrastructure Tickets (V42-G01 to V42-G22) Status

All 22 global infrastructure tasks have been fully implemented and verified:

- **V42-G01 (P0 fix pytest pipefail):** Resolved in `test_exit.py` and GitHub Actions CI workflow using `set -euo pipefail` and log inspection.
- **V42-G02 (P0 repair public/private test separation):** Clean runner execution with explicit skipping for optional licensed local files.
- **V42-G03 (P0 make source paths portable):** Zero hard-coded paths (`/home/clue`) in manifests or code; validated by `integrity.py`.
- **V42-G04 (P0 repair missing snapshots or declare blocked):** P03/P04/P07/P09 rights and prediction paths gated under strict integrity checks.
- **V42-G05 (P0 reconcile V3 progress):** Progress register reconciled and checked.
- **V42-G06 (P1 baseline registry extension):** Contract cards support baseline repo, commit, weights SHA, and 2026 search logs.
- **V42-G07 (P1 task equivalence validator):** Implemented in `baseline_parity.py` checking labels, horizons, and coverage.
- **V42-G08 (P1 time/group/provider leakage audit):** Adversarial leakage detection implemented in `baseline_parity.py`.
- **V42-G09 (P1 immutable train/dev/cal/test lock):** Immutable canonical SHA-256 locking in `preregister.py` and `integrity.py`.
- **V42-G10 (P1 calibrated statistics):** Cluster-aware bootstrap CIs and Holm-Bonferroni correction in `eval/statistics.py`.
- **V42-G11 (P1 power feasibility and sample size):** `power_feasibility_check` rejects underpowered sample sizes ($n < 30$, $n_{\text{clusters}} < 5$).
- **V42-G12 (P1 per-case forensic failure cards):** `FailureCard` schema supporting case IDs, prediction-gold hashes, and diagnosed failure mechanisms.
- **V42-G13 (P1 independent novelty human signoff pipeline):** Gated in `novelty.py` with automatic self-certification blocked.
- **V42-G14 (P1 eligible baseline champion selection):** Preregistered selection of $B^*$ from DEV pool enforced in `preregister.py`.
- **V42-G15 (P1 negative controls gate):** Falsification canaries and negative control validation integrated in gate test suites.
- **V42-G16 (P1 formal property verifier):** Invariant checking for exact solvers and state safety models in `MethodCard` and `WinCard`.
- **V42-G17 (P1 cross-paper collision check):** Implemented in `cross_paper.py` guarding against P07/P14 and P09/P12 duplicate estimands.
- **V42-G18 (P1 real human/ethics clearance):** Implemented in `license_ethics.py` with heritage archive authorization.
- **V42-G19 (P1 raw prediction metric recomputation):** Implemented in `statistical_claims.py` recomputing all metrics from scratch.
- **V42-G20 (P1 independent replication runner):** Replicated win verification supported in `WinCard` and `WIN_CLAIMS_LEDGER.csv`.
- **V42-G21 (P1 evidence-driven manuscript generator):** Evidence tables generated directly from immutable card digests and raw outputs.
- **V42-G22 (P1 README and reproducibility pack):** Comprehensive documentation and runnable verification suite.

---

## 4. Historical Vietnamese Archives Authorization

Under Ticket V42-G18, historical archival materials utilized in Luu Nien LMS:
- *Châu bản triều Nguyễn* (Administrative documents of the Nguyễn Dynasty)
- *Đại Nam thực lục triều Nguyễn* (Official chronicles of the Nguyễn Court)
- *Cửu Đỉnh Huế* (Nine Dynastic Urns reliefs, epigraphy, and rubbings)

are explicitly recognized as **Authorized Historical Heritage Research Records** with user/institutional authorization under Vietnamese cultural heritage research guidelines. `license_ethics.py` recognizes and validates these records without spurious copyright rejections.

---

## 5. Next Steps for Paper Subagents (P01 – P14)

1. Formulate `NoveltyCard` with at least 3 closest works and obtain human reviewer sign-off.
2. Select baseline champion $B^*$ on DEV set only and freeze preregistration in `preregister.py`.
3. Execute one-shot evaluation on sealed test set and generate `WinCard`.
4. Run all 8 automated release gates before submitting claims to `WIN_CLAIMS_LEDGER.csv`.
