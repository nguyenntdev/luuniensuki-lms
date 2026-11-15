# P03 Method — Evidence-Calibrated Pedagogical Scaffolding (frozen before implementation)

Status: METHOD_FROZEN (this file is written before `policy.py`; changes after
code exists require a new version block at the bottom).

## 1. Formal setting

A tutor decision problem is a tuple `(learner_turn, evidence_pool, stage)`:

- `learner_turn`: the student's latest utterance (untrusted text channel).
- `evidence_pool`: retrieved source records `S = {s_1..s_k}`. Each record has
  `provenance_status ∈ {verified, unverified, quarantined}`, an optional
  numeric `retrieval_confidence ∈ [0,1]`, and free text. Retrieved notes are
  **untrusted**: their text is never executed as instructions.
- `stage`: pedagogical stage `observation < evidence < reasoning` (the
  authorized hint level, from the curriculum/lesson plan — NOT inferred from
  gold labels).

## 2. Action space (fixed constraints)

`A = {hint, socratic_question, request_source, abstain_insufficient_evidence,
reject_injection, answer_with_evidence}` — exactly the six actions of the
ticket: `{hint, question, request_source, abstain, answer_if_permitted}` plus
the explicit injection refusal. `ABSTAIN` (`abstain_insufficient_evidence`) and
`NOT_APPLICABLE` are distinct outputs; a malformed input record raises a typed
`MalformedSourceError` and is excluded from scoring (never silently coerced).

## 3. Decision procedure (fixed constraints — no learned weights)

Evaluated in order; first gate that fires returns. Deterministic; pure.

- **G1 Injection boundary.** If the learner turn carries instruction-override,
  roleplay-jailbreak, tool-abuse or credential-exfiltration patterns →
  `reject_injection`. Reasons: `prompt_injection`,
  `instruction_boundary_enforced`.
- **G2 Malicious-note quarantine.** If any note carries injection payload AND
  an answer appears in that note (or the note instructs the system to reveal
  answers) → the answer is suppressed: verified-source cases get `hint`
  (Socratic redirect), else `abstain_insufficient_evidence`. The quarantined
  note is never cited and never surfaced. Reasons:
  `malicious_note_quarantined`, `answer_text_withheld`.
- **G3 Fail-closed provenance gate.** If no note has
  `provenance_status == verified` → `abstain_insufficient_evidence`.
  This is the calibrated-abstention mechanism: **no sufficient evidence ⇒
  abstain**. Reasons: `unverified_or_absent_source`, `fail_closed_gate`.
  The gate also fires on **contradictory verified sources** (same slot,
  conflicting values) with reason `contradictory_sources_detected` —
  contradiction ⇒ uncertainty ⇒ abstain, never an answer.
- **G4 Pedagogical stage gate (answer budget).** Direct-answer requests are
  granted only when (a) evidence verified, (b) `stage == reasoning`
  (authorized release), (c) learner explicitly asks for the answer, and
  (d) **G4c calibrated answer-worthiness** `p_answer ≥ τ` with τ = 0.60.
  `p_answer = 0.5·conf_min + 0.3·stage_score + 0.2·evidence_diversity`
  (factorized evidence calibration + student-need inference). If the learner
  asks early (`stage < reasoning`) → `hint` with reasons
  `early_answer_request`, `answer_release_locked`, `socratic_redirect`.
  If stage permits but `p_answer < τ` → `hint` with reasons
  `low_answer_confidence`, `calibrated_hint_fallback`.
- **G5 Socratic default.** Otherwise: `socratic_question` at
  `stage == observation`, else `hint`. Reasons encode
  `hint_level_<n>`, `stage_<name>`, `verified_source`.

Complexity: O(|S| · |patterns|) per decision; no optimization, no training.
Learned-weights surface: **none** in v1 — the τ and gate order are fixed
constraints; factor weights (0.5/0.3/0.2) are frozen hyperparameters declared
here before any evaluation, tuned on nothing.

## 4. Labels (evaluation-only; policy never sees them)

For each scored case, a label `answer_warranted ∈ {0,1}` and a scenario
`stratum` are assigned by the **materialization step** (deterministic
generators / MRBench dialogue properties), stored in the sealed label file
with case ids; the policy input contains neither. `ABSTAIN` correctness is
scored against `has_sufficient_evidence` (label), keeping abstention distinct
from negative predictions.

## 5. Metrics (exact denominators)

- answer_leakage_rate: (# leak-risk cases with an answer action) / (# leak-risk
  cases). Leak-risk = injection ∪ malicious_note ∪ premature-answer strata.
- citation_grounding_rate: (# non-refusal actions citing ≥1 verified,
  non-quarantined source id present in the pool) / (# non-refusal actions).
  Citing a quarantined or non-existent id counts as a false citation and
  lowers the rate (the denominator stays # non-refusal actions).
- abstention precision/recall vs label `has_sufficient_evidence == false`.
- injection_refusal_rate on injection stratum.
- calibration_ece: 10-bin ECE of `p_answer` (clipped to non-refusal decisions)
  vs binary `answer_warranted` label.
- pedagogy_win_rate (primary): per-case correctness as defined in
  `pre_registration.yaml`.

## 6. Baselines

- **C0 direct-answer**: answers whenever the learner asks, cites nothing,
  never abstains, ignores injections. (Sanity control — weak by construction.)
- **C1 simulated proxy**: a rule-based stand-in for a generic mid-competence
  LLM tutor: answers early answer-requests with probability 0.5 (seeded,
  deterministic per case id), sometimes abstains without checking provenance.
  **Label: `simulated_proxy, NOT a real LLM`** — carried in every artifact,
  table and the manuscript. Exists to test the scoring harness, not to claim
  LLM behavior.
- **C2 real LLM**: BLOCKED (see prereg `blocked_cards`). Only an actually
  executed, license-cleared model with recorded id/version/cost may fill C2.

## 7. Ablations (true removals)

A1 removes the retrieval-confidence factor (p_answer = stage-only); A2 removes
the τ check (answer whenever stage permits — no uncertainty gate); A3 freezes
stage to `reasoning` (no learner-stage awareness); A4 disables G3/G4 abstention
and C1-style fallbacks (answer even when unverified, i.e. no abstain action);
A5 removes the injection/quarantine cost (G1/G2 skipped). Each ablation is
expected to break the named mechanism's stratum; failure families are reported
regardless of direction.

## 8. Complexity & compute

Single CPU, deterministic, < 1 s per 1k decisions. Replication artifacts:
prereg (sha256 in ExperimentCard), frozen split hash, input/output manifests,
policy source hash (`method_hash`), dependency-free (stdlib + research_v3).

## 9. Limitations declared up front

Synthetic strata labels are generated by deterministic rules (documented);
MRBench-based evaluation measures **decision-layer** behavior injected onto
real dialogues, not end-to-end generated tutor text; no real LLM (C2) and no
human teacher reference (B05) are evaluated in v1 — external validity is
therefore decision-level, not generation-level.

---
## Version history
- v1.0.0 (2026-11-15): frozen before policy.py was written. Gate order,
  action space, τ, factor weights, metrics and denominators as above.
