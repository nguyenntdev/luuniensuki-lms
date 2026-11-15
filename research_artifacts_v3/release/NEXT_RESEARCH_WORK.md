# Research V3 — Next Research Work (per-paper blockers and exact unblock actions)

Nothing below is claimed complete. Each item names the missing human, license, or
infrastructure prerequisite that code cannot supply. Counts of DONE/BLOCKED tasks per
paper come from `research_artifacts_v3/release/progress.json` (98 DONE / 220 BLOCKED;
44 human-only BLOCKED portfolio-wide).

## 0. Portfolio-wide blockers

| Blocker | Affects | Exact unblock action |
|---|---|---|
| Ethics / annotation / license approval (T19) | All 14 papers | File a real signed approval record under `research_v3/governance/ethics/` (currently 0 records; `python -m research_v3.scripts.ethics` reports status BLOCKED). Cannot be simulated. |
| Novelty & nearest-work signoff (T20) | All 14 papers | Research lead reviews the 2026 literature and signs the overlap matrix. |
| Coauthor / venue / submission signoff (T21) | All 14 papers | Human lead signs at submission time. |
| Independent double-blind rerun (V3-G19) | Portfolio | An external reviewer executes the staged request `research_v3/governance/audit_log/request_2026q1-rerun.json` and returns independent hashes/results. |
| License gate | P01–P05, P07, P08, P10–P12, P14 | `python -m research_v3.scripts.verify_licenses --all --strict` currently FAILS with 21 non-APPROVED required datasets (APPROVED: 3 — `oulad-2013-2014`, `uci-student-performance-2014`, `mrbench-v3-devset`; BLOCKED: 5; several paper-required IDs not registered). Papers cannot claim primary external results on those datasets until each card is APPROVED with captured license-text hash and verified file hash. |

## 1. Per-paper remaining work

### P01 — Risk-controlled transfer gate (status: PARTIAL, honest null)
- **Tasks**: 18 DONE / 3 BLOCKED (T19–T21 human-only) — per `runs/p01/status.json`.
- **BLOCKED**: KT baselines DKT/SAKT/AKT (required transfer baselines in the spec) —
  ASSISTments BLOCKED (terms unreviewed), Junyi NOT REGISTERED, EdNet BLOCKED (CC BY-NC).
- **Unblock**: pick and license one KT dataset (version selection + signed license capture +
  registry card), then run the transfer pair; file T19–T21 signoffs.

### P02 — Constrained path planning (status: PARTIAL, tie + runtime cost)
- **Tasks**: 0 DONE / 21 BLOCKED — no task-granular ledger exists (`runs/p02/` holds only
  paper-level artifacts: 4 files). Per `progress.json` rule, per-task DONE requires a
  machine-readable task ledger.
- **Unblock (mechanical)**: write `runs/p02/task_status.json` mapping P02-T01..T18 to
  statuses with evidence paths, then re-run `progress_report`.
- **BLOCKED (research)**: no external routing/trail dataset; junyi NOT REGISTERED.
- **Unblock**: register a real POI/travel dataset with objective costs, or state the
  benchmark's scope as synthetic-only in the manuscript.

### P03 — Evidence-calibrated tutoring (status: PARTIAL)
- **Tasks**: 0 DONE / 21 BLOCKED — same missing-ledger situation as P02 (`runs/p03/` has
  8 paper-level files, no `task_status.json`).
- **Unblock (mechanical)**: write `runs/p03/task_status.json` from the evidence already on
  disk (reports, manifest, license capture), then re-run `progress_report`.
- **BLOCKED (research)**: C2 real-LLM baseline — no licensed executable model (2 GiB GPU,
  no ollama/vllm/llama-cli, no API credentials; recorded in
  `runs/p03/manifests/manifest_v1.json` c2_status). No human teacher reference (B05).
- **Unblock**: an LLM API budget or a licensed local model; record model id/version/cost in
  the evidence card; recruit a teacher reference; score generated utterances against the
  BEA rubrics.

### P04 — CurriculumShiftBench (status: PARTIAL)
- **Tasks**: 9 DONE / 12 BLOCKED — T08, T10, T18 TODO; T11–T14, T17 PARTIAL
  (`runs/p04/status/p04_status.json`).
- **BLOCKED**: KT baselines (T08) and true-removal ablations A1–A4 (T10) unexecuted;
  Holm correction over the confirmatory family pending T08 (T14).
- **Unblock**: pinned DKT/SAKT/AKT/GKT implementations (or a dated BLOCKED card per the
  status file's own rule), then execute A1–A4 and the corrected family.

### P05 — Temporal forgetting KT (status: PARTIAL, small CI-separated gain)
- **Tasks**: 0 DONE / 21 BLOCKED — no task-granular ledger (`runs/p05/` has 10 paper-level
  files).
- **Unblock (mechanical)**: write `runs/p05/task_status.json`, re-run `progress_report`.
- **BLOCKED (research)**: C2 published KT comparator (`research_v3/experiments/p05/blocked_cards.yaml`);
  ASSISTments and EdNet BLOCKED; single external domain.
- **Unblock**: license a second KT dataset; find a re-runnable published comparator
  (code + license) or publish the dated BLOCKED card in the manuscript.

### P06 — Budget-constrained prioritization (status: PARTIAL, honest null)
- **Tasks**: ledger shows T01–T17 DONE_ENGINEERING; T18–T21 BLOCKED
  (`runs/p06/task_status.json`); `progress.json` records 0/21 because the ledger statuses
  (DONE_ENGINEERING) predate the completed-status list — do not inflate; treat as
  engineering-complete, scientifically null.
- **BLOCKED**: the equity-floor mechanism never binds on OULAD (null published); no causal
  intervention study (NONCAUSAL_UNTIL_PROVED attestation).
- **Unblock**: a real intervention RCT with consent (T19) or reframe the contribution as
  selection-quality measurement only.

### P07 — Resource-aware multimodal selection (status: PARTIAL)
- **Tasks**: 0 DONE / 21 BLOCKED — no task-granular ledger (`runs/p07/` has 17 files).
- **Unblock (mechanical)**: write `runs/p07/task_status.json`, re-run `progress_report`.
- **BLOCKED** (dated, `runs/p07/BLOCKED_TASKS.md`):
  - Europeana portion of T02: HTTP 401 without wskey → register an API key at
    https://pro.europeana.eu/page/apis and capture per-item media rights.
  - A3 provenance ablation: needs ≥2 external providers (currently only Smithsonian FSG CC0).
  - A4 hard-rejection ablation and B00–B03 baselines (BM25/CLIP/metadata/knapsack):
    need pinned model weights and an instance-space spec.
  - Affordance-annotation agreement: needs ≥2 independent human raters with a codebook;
    compute Krippendorff α.
- **Unblock order**: Europeana key → A3/A4/B00–B03 → human raters.

### P08 — Reward-integrity gamification (status: PARTIAL, engineering)
- **Tasks**: 15 DONE / 6 BLOCKED (`runs/p08/task_status.json`) — T02 BLOCKED (no external
  reward-attack dataset exists: assistments/ednet BLOCKED; OULAD lacks attack semantics),
  T18 PENDING (external reviewer), T19–T21 human-only.
- **Unblock**: file T19–T21 signoffs; commission the external double-blind rerun (V3-G19,
  request already staged). Human motivation/learning claims additionally require a
  controlled consented study — out of scope for a code agent.

### P09 — Provenance-aware heritage exploration (status: PARTIAL; PASS at provenance layer)
- **Tasks**: 0 DONE / 21 BLOCKED — no task-granular ledger (`runs/p09/` has 36 files).
- **Unblock (mechanical)**: write `runs/p09/task_status.json`, re-run `progress_report`.
- **BLOCKED (research)**: Wikidata (CC0) is secondary evidence — 51 claims, verification is
  structural, not expert adjudication; citation grounding is 0.118 for every arm because
  only 6 grounded claims exist in the corpus.
- **Unblock**: a real Huế expert corpus (written archival permission + expert annotation
  trail; `hue-heritage-corpus` BLOCKED in the registry) and independent expert adjudication.

### P10 — Spiral heritage curriculum (status: BLOCKED)
- **Tasks**: 17 DONE / 4 BLOCKED (`research_v3/manuscripts/p10/TASK_LEDGER.yaml`) —
  T19/T20/T21 human-only plus expert validation.
- **BLOCKED**: 27 of 30 GDPT-2018 competency anchors are `needs_expert_review`; only 3
  documented; superiority H0 requires real teacher raters.
- **Unblock**: recruit history teachers to resolve the 27 anchors (CVI or equivalent
  documented agreement), then run the preregistered rubric comparison.

### P11 — Historical-reasoning rubric (status: BLOCKED)
- **Tasks**: 7 DONE / 14 BLOCKED (`runs/p11/status_manifest.json`;
  release_status BLOCKED_RATER_AND_SAMPLE_REQUIRED).
- **BLOCKED**: no human raters. Annotation pack
  (`research_v3/annotations/tasks/p11_annotation_pack/`) is prepared and unfilled —
  6 constructed cases labeled CONSTRUCTED_NOT_HUMAN; templates contain headers only.
- **Unblock**: recruit ≥2–3 independent raters per the codebook, collect ratings, compute
  Krippendorff α / κ / ICC against the C0 keyword baseline and the holistic comparator.

### P12 — Source evidence ledger (status: BLOCKED)
- **Tasks**: 11 DONE / 10 BLOCKED (`runs/p12/progress.json`).
- **BLOCKED**: 62/63 documented claims route to ABSTAIN pending human archival review;
  Vietnamese primary archives (ĐNTL, HĐSL, ĐNNTC) BLOCKED for automated ingestion
  (page-level rights not cleared); T14 confirmatory human sample missing; T19–T21
  human-only.
- **Unblock**: archival access with page-level permissions; human reviewers to convert
  ABSTAIN → verified/rejected; then re-run the confirmatory family frozen in the prereg.

### P13 — SRL behaviour analysis (status: PARTIAL, honest null)
- **Tasks**: 0 DONE / 21 BLOCKED in `progress.json` (ledger
  `runs/p13/task_status.json` shows 16 DONE_ENGINEERING / 1 PARTIAL / 4 BLOCKED, but the
  construct-validity guard currently rejects its phrasing — see §2).
- **BLOCKED (research)**: E04 C2 published SRL-proxy comparator (no re-runnable published
  implementation with code + license); E11 single dataset; any construct-level or causal
  claim stays BLOCKED by the guard (clicks ≠ measured SRL).
- **Unblock**: an instrument-based SRL dataset (survey/reflection logs) with real consent
  and ethics signoff; a second dataset for temporal generalization.

### P14 — UDL/WCAG learning objects (status: PARTIAL)
- **Tasks**: 0 DONE / 21 BLOCKED — no task-granular ledger (`runs/p14/` has 10 files).
- **Unblock (mechanical)**: write `runs/p14/task_status.json`, re-run `progress_report`.
- **BLOCKED**: no external media — Smithsonian API 403 without api.data.gov key, Europeana
  401 without wskey, Huế corpus unlicensed (all three recorded as BLOCKED rights cards in
  `runs/p14/audit_report.json`); no human user study (P14-T19); benefit claims rejected by
  the claims guard.
- **Unblock order**: api.data.gov key → Europeana wskey → rights-cleared annotated media
  set → human user study under T19.

## 2. Known mechanical defects to fix before the next release

- `python -m pytest tests/research_v3` currently reports **1 failed, 671 passed, 3 skipped**:
  `tests/research_v3/method/test_p13_corpus_guard.py::test_run_artifacts_pass_guard_when_present`
  fails because `research_artifacts_v3/runs/p13/task_status.json` contains phrases the
  construct-validity guard forbids ("measured srl", "srl measurement"). The artifact must be
  reworded (proxy-level language only) or regenerated via
  `python -m research_v3.methods.p13.run_p13` — the runner enforces the same guard.
- `python -m research_v3.scripts.cross_paper_dedup` now parses all canonical
  preregistrations (p05/p08/p10/p13/p14 were repaired from invalid YAML to valid
  YAML without changing their scientific content) and reports no duplicated
  primary claim. Papers using non-canonical filenames (p01 `preregistration.yaml`,
  p07 `prereg.yaml`) and papers without a prereg (p11, p12) are covered by the
  primary-claim ledger instead.


## 3. What must NOT be claimed

- No SOTA, no venue acceptance, no human learning gain, no expert consensus.
- Proxy/synthetic results never generalize to real classrooms.
- PASS is only used where a licensed external dataset actually backs the claim; no paper
  currently reaches full PASS.
