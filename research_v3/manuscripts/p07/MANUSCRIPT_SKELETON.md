# P07 — Manuscript Skeleton

**Venue target:** ICALT (CORE B) — CFP, rank and fit to be re-verified at
submission time (P07-T21, human-only). **Status: skeleton; no submission
claim.**

---

## Title (working)

*Selecting Cognitively Equivalent Multimodal Learning Objects under Device,
Bandwidth and Accessibility Constraints: An Affordance-Complete, Rights-Aware
Selector with Identifiability Stress Testing*

## 1. Introduction

- Multimodal heritage learning objects (3D models, 2D rasters/rubbings, text
  transcripts, audio) are routinely treated as interchangeable by retrieval
  systems that check availability, not pedagogical sufficiency.
- **RQ:** Does task-affordance coverage under bandwidth/device/accessibility
  constraints prevent false modality equivalence better than conventional
  multi-object retrieval?
- **H0 (must be disclosed if not rejected):** constraint-aware choice does
  not outperform basic hard filtering after controlling annotation quality
  and retrieval depth.
- Contribution boundary: P07 = selection algorithm + evaluation; pedagogical
  UDL design and human evaluation = P14 (no shared primary outcome table).

## 2. Related Work

- **UDL & accessibility:** WCAG 2.1 success criteria (1.2.1 audio
  transcript, 2.1.1 keyboard, 4.1.2 name/role/value) as affordance axes;
  UDL multiple-means-of-representation principle (CAST) as motivation —
  cited for design, NOT as evidence of learning gains.
- **Multimodal retrieval:** metadata filtering and CLIP-style retrieval
  baselines check availability/similarity, not affordance coverage (B02/B01
  families, not run in this wave — see §7).
- **Resource-aware delivery:** adaptive bitrate and device-capability gating
  treat bandwidth, but not pedagogical equivalence.
- **Prior internal work:** V2 LN-07 established the image-without-inscription
  counterexample class on synthetic data; P07 generalizes it to a typed
  selection contract with real provider metadata and an identifiability
  stress protocol.
- **Novelty condition (spec §1):** the method/protocol is defined precisely;
  comparisons here are sanity/classical baselines only. No SOTA claim is
  made or implied. If only sanity/rules-oracle baselines are runnable, the
  win is NOT framed as novelty evidence.

## 3. Method

- Affordance ontology (11 axes, tri-state), task requirements, device
  constraints, provider-recorded license status (`METHOD.md` E1).
- Selector: rights screen → device/bandwidth feasibility → affordance
  coverage → deterministic minimal-payload choice; typed failures
  (`reject_missing_affordance` / `reject_rights_violation` /
  `reject_infeasible` / `abstain`).
- External affordances from derivational facts only (Smithsonian CC0
  records); ambiguous records → curator abstain.

## 4. Evaluation Design

- **Preregistered** primary endpoint: exact-match decision accuracy
  (task_feasibility_rate); contrast: proposed vs C1 static-image-fallback;
  McNemar exact, Holm correction across the declared family; cluster
  bootstrap CIs (group_id), Cliff's delta.
- **Stress strata (S1–S7):** mandatory image-exists-missing-inscription,
  audio-no-transcript, keyboard-inaccessible 3D, low-bandwidth positive
  control, license ambiguity, G16 identifiability pairs (differ in exactly
  one affordance axis), empty-pool abstain.
- **External suite:** 8 Smithsonian CC0 cases (4 POS/NEG pairs) validating
  the derivational-fact pipeline on real records.

## 5. Results (filled from frozen artifacts only)

- Stress suite (n=17): proposed 1.000 [CI], C0/C1/b05 ≤ 0.647; false
  completion 0.000 vs ≥ 0.353; missing-affordance recall 1.000 vs 0.000.
  Paired contrasts: vs C1 diff=0.471, McNemar p=0.0078 raw, CI95 [0.312,
  0.625]; Holm-adjusted across the 9-test family: not significant
  (p_holm=0.125 for the primary contrast — DISCLOSED; the primary contrast
  raw p=0.0078, Holm p=0.125 ⇒ H0 NOT rejected at family-corrected α=0.05).
- External suite (n=8): proposed 1.000 vs baselines 0.5; p=0.125 (n too
  small; no claim).
- Ablations: A1 (no affordance coverage) reproduces false completions
  exactly on the paired negatives (mechanism identifiable); A2 diverges on
  device strata; A5 produces rights violations (1/16) — evidence the rights
  screen is load-bearing. A3/A4 deferred with dated rationale.
- All numbers sourced from `research_artifacts_v3/runs/p07/p07-wave1/results.json`
  (SHA-256SUMS manifest). Every numeric claim must cite its evidence ID from
  that file. The Holm-adjusted primary contrast is NOT significant: the
  honest headline is *mechanism identifiability + failure-mode elimination*,
  not superiority.

## 6. Threats to Validity

- **Internal:** gold verdicts are derivational-fact oracles (rule-based, not
  human); the oracle and the selector share the affordance vocabulary by
  construction — the identifiability pairs mitigate but do not eliminate
  circularity risk; no learned parameters removes tuning bias.
- **External:** single provider (Smithsonian FSG unit); n=8; media kb
  modeled at a studied delivery size, not measured; external generalization
  UNVERIFIED (preregistered as such).
- **Construct:** affordances are proxies for pedagogical sufficiency; task
  coverage ≠ cognitive equivalence in the learning-science sense; WCAG
  compliance is NOT certified (manual audit required).
- **Synthetic media:** stress suites are synthetic and labeled; they
  establish identifiability and regression safety only. If external media
  validation remains blocked/partial, the study stays PARTIAL — no claim of
  external validation is permitted.
- **Statistical:** small n; Holm family spans all contrasts; the
  primary-contrast H0 is NOT rejected after correction and must be reported.
- **No learning-gain claim:** this study measures selection behavior, not
  human learning outcomes; any UDL benefit language is prohibited (P14's
  scope, and requires real human evaluation).

## 7. Baseline disclosure (spec §4 gate)

Run: C0 (URL-present sanity), C1 (static-image-fallback classical),
B05 (random eligible). NOT run: B00 BM25, B01 CLIP retrieval, B02 metadata
filtering, B03 knapsack, B04 rule-based accessibility filter — all require
implementation and, for B01, model weights; dated BLOCKED rationale required
in the results section before any submission. Strongest-compatible-upstream
baseline comparison is therefore INCOMPLETE (preregistered as PARTIAL).

## 8. Artifacts & Reproducibility

- Code: `research_v3/methods/p07/` (selector, baselines, ablations, metrics,
  external adapter, synthetic generator), `research_v3/experiments/p07/`
  (prereg, matrix, CLI).
- Data: `research_v3/methods/p07/data/smithsonian_fsg_external.jsonl`;
  raw snapshot + license text in gitignored `private_data/raw/` with pinned
  SHA-256; synthetic suite generated deterministically from seed.
- Results: `research_artifacts_v3/runs/p07/p07-wave1/` (predictions JSONL,
  results.json, SHA256SUMS.txt; determinism check: identical prediction hash
  on rerun).
- Tests: `tests/research_v3/method/test_p07_*.py` (55 passed, 1 skipped when
  raw snapshot absent).

## 9. Ethics & Compliance

No human subjects; no student PII; media used only under CC0 with per-item
rights verification; ambiguous-rights and ambiguous-inscription records are
excluded, not guessed. Europeana metadata NOT used (API-key BLOCKED card).
Human-only tasks P07-T19/T20/T21 remain BLOCKED and are not simulated.
