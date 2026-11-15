# Research V3 — 14-Paper Research Program

A fail-closed research infrastructure for 14 preregistered papers (P01–P14) plus global
governance tasks (V3-G00..G23). Every stage — license gating, split freezing, baseline
verification, training, statistics, claim cross-verification — exits nonzero on any
unmet precondition. A missing license, missing ethics approval, blocked dataset, or
unverifiable claim produces a BLOCKED status, never a fabricated success.

Status of the science itself (which numbers are real, which are null, which are blocked):
read `research_artifacts_v3/release/SCIENTIFIC_READINESS.md` first. Current honest
headline: **0 papers submission-ready; 11 PARTIAL; 3 BLOCKED; 44 human-only tasks
permanently BLOCKED until real humans sign.**

## Architecture

```
           preregistration (yaml, sha256-pinned)
                          |
                          v
  +----------------------------------------------------------+
  | datasets/   registry.yaml + registry/ (license cards)     |
  |             fetchers/  adapters/  sanitized/ (stress)     |
  +----------------------------------------------------------+
        | only APPROVED cards back a primary claim
        v
  +----------------------------------------------------------+
  | contracts/cards.py   DatasetCard / ExperimentCard /       |
  |                      EvidenceCard / FrozenSplit            |
  | eval/  splitters.py (group/time, hashed, leakage-audited) |
  |        leakage.py  statistics.py  calibration.py          |
  |        result_integrity.py (recompute-from-raw gate)      |
  +----------------------------------------------------------+
        | frozen splits + frozen hyperparameter budget
        v
  +------------------------+     +---------------------------+
  | methods/p01..p14       |     | experiments/p01..p14      |
  | (typed schemas, policy | --> | (prereg yaml + run CLI,   |
  |  code, METHOD.md)      |     |  writes run manifests)    |
  +------------------------+     +---------------------------+
                                        |
                                        v
                        research_artifacts_v3/runs/pXX/
                        (metrics, predictions, null results,
                         experiment cards, task ledgers)
                                        |
                                        v
  +----------------------------------------------------------+
  | scripts/  audit_repo  verify_licenses  validate_splits    |
  |           cross_paper_dedup  cross_verify_claims          |
  |           progress_report  result_integrity  ethics ...   |
  +----------------------------------------------------------+
                                        |
                                        v
                research_artifacts_v3/release/ (readiness docs)
```

Request flow per paper: a preregistration YAML (hash recorded) fixes the research question,
estimand, null hypothesis, split protocol and hyperparameter budget **before** any run. The
run CLI writes every number plus its manifest into `research_artifacts_v3/runs/pXX/` — no
hand-entered metrics. Release docs may only quote numbers traceable to those artifacts, and
`cross_verify_claims` re-checks release claims against run manifests.

## Directory layout

| Path | Purpose |
|---|---|
| `datasets/registry.yaml` | License cards per dataset. Only `status: APPROVED` (captured license-text SHA-256 + verified file SHA-256 + positive sample count) may back a primary claim. Current APPROVED: `oulad-2013-2014` (CC BY 4.0), `uci-student-performance-2014` (CC BY 4.0), `smithsonian-open-access-fsg` (CC0); MRBench devset APPROVED in `datasets/registry/p03.yaml` (CC BY-SA 4.0, README-captured, caveat recorded). Everything else BLOCKED with an exact reason. |
| `config/papers/paper_datasets.yaml` | Which datasets each paper REQUIRES for its primary external claim (fail-closed against the registry). |
| `config/split_protocols/` | Frozen, hashed split protocols (currently P06, P13). |
| `contracts/cards.py` | Typed, validated dataclasses: `DatasetCard`, `ExperimentCard`, `EvidenceCard`, `FrozenSplit`. BLOCKED cards must carry a `blocked_reason`; APPROVED cards must carry hashes. |
| `eval/` | `splitters.py` (learner-group and time splits, salted hashes, `assert_no_leakage`), `leakage.py` (`audit_rows`), `statistics.py` (paired cluster bootstrap, Holm, Wilson/Clopper-Pearson, null-result disclosure helper), `calibration.py` (reliability bins, ECE, worst-group), `result_integrity.py` (recompute every metric from raw predictions + sealed gold; fails on tampering, R1–R11). |
| `methods/pXX/` | Per-paper method code, typed schemas, METHOD.md. Guarded where needed (e.g. P13's construct-validity guard fails any artifact claiming "measured SRL"). |
| `experiments/pXX/` | Preregistration YAML + runnable matrix/CLI per paper. |
| `baselines/registry/registry.yaml` | C0 (sanity) / C1 (serious classical reimplementation) / C2 (published model; requires real upstream snapshot hash, otherwise BLOCKED). No published number may be copied into a V3 table. |
| `annotations/tasks/` | Human annotation packs (e.g. `p11_annotation_pack/`) — shipped as templates only; unfilled until real raters exist. |
| `datasets/sanitized/` | Deterministic stress suites with SHA-256 manifests (LN-06 solver parity, LN-07 transcript failure, LN-09 small-cohort). |
| `data_frozen/` | Timestamped `source_lock_*.json` snapshots (append-only; each `audit_repo` run writes a fresh file). |
| `governance/claims/` | `claims_ledger.csv` — claim-ID ledger built read-only from the manuscripts. |
| `governance/ethics/` | Signed approval records. **Empty = BLOCKED, by design.** |
| `governance/audit_log/` | External-audit requests (the staged double-blind rerun request `request_2026q1-rerun.json` lives here). |
| `governance/G20_HUMAN_CLEARANCE.md` | Human-only clearance document; permanently BLOCKED until real signatures exist. |
| `manuscripts/pXX/` | Manuscript skeletons; numbers must be sourced from `research_artifacts_v3/runs/` only. |
| `scripts/` | One fail-closed CLI per G-task (see `REPRODUCE.md` for exact commands). |

## Contract cards

- **DatasetCard** (`contracts/cards.py:34`): provenance + rights per dataset version.
  `APPROVED` requires 64-hex `license_text_sha256` and `original_sha256`, a source URL and
  `sample_count > 0`; `BLOCKED` requires a `blocked_reason`. A public URL is not a license.
- **ExperimentCard** (`contracts/cards.py:87`): one preregistered run — paper, RQ, train/holdout
  dataset IDs, method hash, split hash, prereg SHA-256, frozen hyperparameter budget, seed,
  hardware, wall time, dependency lock, protocol deviations, status. All hashes must be 64-hex.
- **EvidenceCard** (`contracts/cards.py:129`): the claim-level evidence record (allowed wording,
  denominator, CIs, table cells, limitations) — e.g. P03's `runs/p03/manifests/manifest_v1.json`.
- **FrozenSplit**: immutable split with hash; `freeze_hash` + `assert_no_leakage` are the gate
  between data and modelling.

## Fail-closed rules

1. **Human-only tasks stay BLOCKED.** T19 (ethics), T20 (novelty), T21 (venue) and V3-G09/G20
   can never be completed by code; `scripts/ethics.py` BLOCKS unless a real signed record with
   a matching document hash exists (the directory is currently empty, status BLOCKED).
2. **No license, no claim.** `verify_licenses --all --strict` fails (currently 21 violations)
   while any paper-required dataset is not APPROVED. APPROVED requires captured license text
   AND verified file hashes.
3. **No metric without a manifest.** Release docs are cross-verified against run manifests
   (`cross_verify_claims`); prose-vs-disk mismatch exits nonzero.
4. **Nulls are published, never tuned away.** `eval/statistics.py:null_result` records honest
   nulls; P01, P06, P07, P13 and P02's tie all disclose theirs in their run artifacts.
5. **Deterministic vs stochastic.** Deterministic runs must be byte-identical; stochastic runs
   need ≥5 seeds, and identical hashes across seeds are reported as pseudo-replication.
6. **No relabeling of frozen gold** — `label_mismatch_audit` reports; it never rewrites.
7. **Construct guards.** Paper-specific guards (e.g. P13 `construct_validity.py`) abort the
   pipeline if an artifact overclaims (proxy ≠ construct, no causal wording).
8. **Raw external data stays out of git.** `private_data/` is gitignored; only hashes and
   derived, license-cleared artifacts are committed.
