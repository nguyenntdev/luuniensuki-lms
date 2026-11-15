# P03 Scientific Failure Review & Collision Audit (P03-T16)

Date: 2026-11-15 · Reviewer role: implementation agent (independent human review still outstanding → T20 BLOCKED).

## 1. Falsification attempts executed (not post-hoc)

| Attempt | Result |
|---|---|
| Malicious-note answer exfiltration (mandatory counterexample) | Policy withholds: `answer_text_withheld` + abstain/hint; poisoned id never cited. Enforced by `test_malicious_note_answer_never_revealed`. |
| Prompt-injection via learner turn (4 variants) | All refused (G1); `test_injection_variants_refused`. |
| Abstention under insufficient/contradictory evidence | Abstains with explicit reason codes; `test_no_verified_source_abstains`, `test_contradictory_verified_sources_abstain`. |
| Calibration under low-confidence verified evidence | τ-gate withholds (p=0.417 < 0.60); `test_calibrated_abstention_on_low_confidence`. |
| Ablation mutation checks (A1–A5) | Every ablation demonstrably breaks its named mechanism (AUROC 0.50 for A1; leak 0.333 for A3; refusal 0.0 for A5). Mechanism coupling is real, not narrative. |
| Determinism | Byte-identical decisions across repeats; frozen decisions match fresh execution of pinned policy. |
| Fail-closed malformed inputs | 6 malformed source-record shapes raise typed `MalformedSourceError`; never coerced. |

## 2. Honest negative / limiting findings

1. **A1 paradox.** Removing the confidence factor *lowers* prereg-literal ECE (0.233 vs 0.414) because ECE measures calibration, not discrimination; A1's selective AUROC collapses to 0.50. Lesson recorded: report AUROC with ECE or a degenerate bin can look "better calibrated". Preserved in summaries; not hidden.
2. **Conservative-abstention ceiling.** Abstention recall is 0.600 [0.525, 0.671]: warranted-withholding on stage-locked cases counts against recall by the prereg definition. Reported as-is; no denominator tuning after the fact.
3. **C1 weakness acknowledged.** The simulated proxy exists to exercise the harness; its 0.423 win rate does not characterize any real LLM tutor.
4. **Single-seed determinism** is one scored seed + reproducibility check, NOT three independent stochastic seeds (portfolio reliability rule).
5. **Null-result protocol.** `paired_report` + `null_result()` flags are embedded per contrast in `paired_stats_v1.json`; had any contrast been non-significant it would be reported there as null, not dropped.

## 3. Salami-slicing / collision decisions

- P03 (decision policy) vs P09 (user interaction with provenance): no shared principal table; P03's table is per-case decision correctness, P09's is user-side interaction. No merge.
- P03 vs P11 (validated human scoring rubric): P03 uses no human scores. No merge.
- P03 vs P12 (source curation protocol): P03 consumes provenance statuses; it does not curate sources. No merge.
- MRBench usage is a decision-layer probe, NOT the BEA shared-task tracks 1–4 task; no overlap with any published leaderboard submission's principal table.
- MathTutorBench main tasks: NOT scored (BLOCKED card); the reward-model data subset is RESERVED and unused in v1 — prevents double-claiming the same collection.

## 4. Data/provenance integrity

- Raw MRBench devset pinned at sha256 `a395feab801de50d44b73e1e9b88f84824a1f1d92e15ae86842d90c2b6dbf33c`; `.sha256` sidecar; manifest re-verifies every artifact checksum per run (round-trip test).
- Prereg v1.1.0 amended BEFORE confirmatory freeze (strata addition only; metric/contrast/denominator unchanged); amendment note is inside the file; hash recorded in ExperimentCard.
- License caveat recorded: UnifyingAITutorEvaluation has no LICENSE file; terms captured from README License section verbatim into `runs/p03/raw/` capture note.

## 5. Open failures that keep the study from SCIENTIFIC_REVIEW_READY

- C2 real-LLM comparison missing (environment cannot host one) → strongest-baseline requirement unsatisfied at LLM level.
- No human teacher reference (B05) or human annotation of reason-code quality.
- Single external collection; second domain (reward-model data) reserved but not run.
- Human-only signoffs T19/T20/T21 outstanding.

These are recorded as BLOCKED/PARTIAL statuses, never silently accepted.
