# Evidence-Calibrated Pedagogical Scaffolding for AI Tutors: A Grounding-First Socratic Decision Policy with Calibrated Abstention

**Paper ID:** P03 · **Manuscript skeleton** (P03-T17) · Status: SKELETON — not submission-ready. Venue target ITS (CORE B); CFP/rank must be re-verified at submission time. Release status: `ENGINEERING_PASS` + external-validity **PASS at decision-layer** (see §7 Threats to Validity for what this does NOT mean).

---

## 1. Research Question

**RQ.** Can a tutor *decision policy* decide when to hint, ask a Socratic question, request a source, abstain, or answer — using both **evidence sufficiency** and **pedagogical stage** — without ever leaking a direct answer before evidence is verified, while remaining **calibrated** (abstaining when sources are insufficient)?

**Estimand.** Per-case binary success on the preregistered strict win rate (`pedagogy_win_rate_strict`, pre_registration.yaml), compared paired per dialogue against baselines on identical frozen cases.

**Null hypothesis (H0, preregistered).** The multi-gate strategy does not improve the primary endpoint at matched answer-leak risk and response budget relative to the strongest executed baseline.

**Collision statement.** P03 studies tutor *decision quality*; P09 studies user interaction with provenance and contradictions; P11 is instrument validation for human scoring; P12 is source curation. No other paper shares this sample, RQ and principal table (audit: `research_artifacts_v3/runs/p03/manifests/manifest_v1.json` → evidence card).

## 2. Contributions (calibrated wording)

1. A deterministic, typed, gate-ordered Socratic decision policy (G1 injection refusal → G2 malicious-note quarantine → G3 fail-closed provenance/contradiction gate → G4 stage+calibrated answer budget → G5 Socratic default), with explicit reason codes and cite-only provenance (`research_v3/methods/p03/policy.py`).
2. A fail-closed metric suite (answer-leakage, citation-grounding, false-citation, abstention precision/recall, injection-refusal, release-worthiness ECE) with exact denominators and Wilson/CP CIs (`research_v3/methods/p03/metrics.py`).
3. A preregistered, hash-frozen evaluation over a **real external tutoring benchmark** (MRBench devset, BEA 2025, CC BY-SA 4.0) with deterministic adversarial scenario injection and five true ablations (`research_v3/experiments/p03/run_matrix.py`).

**What we do NOT claim.** No SOTA claim (only sanity C0 and rule-based proxy C1 executed; C2 real LLM BLOCKED). No pedagogical effectiveness claim (no student outcomes measured). No novelty certification (P03-T20 is a human task and remains BLOCKED).

## 3. Related work (verified publications only)

- **Socratic tutoring with LLMs.** Macina et al., *MathDial* (ACL 2023 Findings); Daheim et al. (2024, targetedness/correctness/actionability criteria); Macina et al., *MathTutorBench* (EMNLP 2025 Main, DOI 10.18653/v1/2025.emnlp-main.11) — teacher-grounded evaluation of seven tutoring tasks; leaderboard evidence that strong problem solvers are not strong tutors.
- **Pedagogical evaluation taxonomy.** Maurya et al., *Unifying AI Tutor Evaluation* (NAACL 2025, DOI 10.18653/v1/2025.naacl-long.57) — MRBench, eight pedagogical dimensions; the BEA 2025 shared task on pedagogical ability assessment.
- **Retrieval-grounded generation.** Standard RAG provenance practice; cite-only attribution guard; fail-closed abstention on unverified provenance (cf. production invariant V5-T061/W06 in this repository's own audit trail, internal only).
- **Abstention / selective prediction.** Selective risk–coverage trade-offs; our release-worthiness score follows risk-coverage semantics, NOT outcome prediction (declared in metrics).
- **Prompt-injection defenses.** Instruction-boundary patterns; untrusted-channel treatment of retrieved text (G2 quarantine).
*Literature matrix with DOI/URL, venue/date, code availability and overlap scores: `research_v3/methods/p03/literature_matrix.csv`.*

## 4. Method (summary; full contract in METHOD.md)

Input: typed `TutorDecisionInput(learner_turn, sources[], stage, wants_answer)`; output: typed `TutorDecision(action, reason_codes, evidence_ids, p_answer)`. Six actions. τ = 0.60 release threshold; factor weights 0.5/0.3/0.2 (confidence-min, stage, evidence diversity) frozen before evaluation. Complexity O(|S|·|patterns|). No learned weights, no oracle access, no network. `ABSTAIN` and `NOT_APPLICABLE` are distinct from negative predictions; malformed source records raise typed `MalformedSourceError` (fail-closed).

## 5. Evaluation (from frozen artifacts; no hand-entered numbers)

Data: MRBench v3 devset (300 conversations, MathDial+Bridge derived, CC BY-SA 4.0), sha256 `a395feab801de50d44b73e1e9b88f84824a1f1d92e15ae86842d90c2b6dbf33c`; group split by `conversation_id` (197/29/40/34, split hash `9b3fbfd586337fb4912b52eaf684c7c8741245134bbffb097bdb0918809b72a8`); 8 preregistered strata × 34 test conversations = 272 test cases; leakage audit PASS (0 findings).

**Table 1 (primary; 95% Wilson CIs; n=272).**

| System | Win rate [CI] | Leak rate (n=102) [CI] | Grounding | Refusal | Abst. P / R | ECE |
|---|---|---|---|---|---|---|
| Proposed multi-gate | 1.000 [0.986, 1.000] | 0.000 [0.000, 0.036] | 1.000 [0.973, 1.000] | 1.000 [0.898, 1.000] | 1.000 / 0.600 [0.525, 0.671] | 0.414 (sel. 0.288, AUROC 1.00) |
| A1 no provenance confidence | 0.875 [0.830, 0.909] | 0.000 | 1.000 | 1.000 | — | 0.233 (sel. AUROC 0.50) |
| A2 no uncertainty calibration | 0.875 [0.830, 0.909] | 0.000 | 1.000 | 1.000 | — | 0.414 (sel. 0.288, AUROC 1.00) |
| A3 no learner stage | 0.875 [0.830, 0.909] | **0.333** | 1.000 | 1.000 | — | 0.358 |
| A4 no abstention | 0.750 [0.690, 0.803] | 0.000 | 1.000 | 1.000 | — | 0.414 |
| A5 no action cost | 0.875 [0.830, 0.909] | 0.000 | 1.000 | **0.000** | — | 0.414 |
| C0 direct answer | 0.250 [0.202, 0.305] | **1.000** | 0.750 | 0.000 | — | — |
| C1 *simulated_proxy, NOT a real LLM* | 0.423 [0.366, 0.482] | **0.186** | 0.750 | 0.000 | — | — |

**Table 2 (paired, Holm-corrected within the preregistered family).** Every contrast is significant after Holm (all adj. p < 1e-9) — but see §7: C1 is a harness test, not an LLM comparison. Cluster bootstrap (2 000 draws, conversation clusters) and McNemar exact per contrast in `research_artifacts_v3/runs/p03/reports/paired_stats_v1.json`.

**Table 3 (per-stratum, fail-closed).** All eight strata reported for every system in `summaries_v1.json`; the proposed policy never leaks on any leak-risk stratum (k=0/102); A3 leaks on 1/3 of premature-request cases; A5 loses all injection refusals.

**Mechanism check (ablation→named-mechanism coupling).** A1 → selective AUROC collapses to 0.50 (confidence factor carries discrimination); A2 → answers low-confidence cases (calibration gate removed); A3 → leaks on premature requests; A4 → answers insufficient-evidence cases (abstain gone); A5 → refuses nothing.

## 6. External benchmark obtainability record (P03-T02)

| Source | URL checked (2026-11-15) | Outcome |
|---|---|---|
| MathTutorBench | https://eth-lre.github.io/mathtutorbench/ · https://github.com/eth-lre/mathtutorbench · datasets/mathdial_bridge.json (sha256 96609c80…) | Site + repo live, CC BY-SA 4.0 badge, data downloadable. **BLOCKED for direct scoring**: all seven tasks require an LLM to generate tutor utterances; no executable LLM available (C2 card). Raw file fetched + hashed for provenance only. |
| BEA 2025 shared task (MRBench) | https://sig-edu.org/sharedtask/2025 · https://github.com/kaushal0494/UnifyingAITutorEvaluation · mrbench_v3_devset.json (sha256 a395feab…) | **DATA_READY, APPROVED-WITH-CAVEAT**: CC BY-SA 4.0 per README License section (no LICENSE file in repo — caveat recorded in registry card). Used as the external substrate. |
| Pedagogical reward-model data | https://huggingface.co/datasets/dmacjam/pedagogical-rewardmodel-data | cc-by-4.0 confirmed via HF API. RESERVED as replication collection (not used in v1 matrix). |
| C2 real LLM | environment probe: GTX 950 2 GiB GPU, 3.2 GiB disk free, no ollama/vllm/llama-cli, no API credentials | **BLOCKED.** No real LLM was evaluated. |
| B05 human teacher reference | requires human annotation approvals (P03-T19) | **BLOCKED.** |

## 7. Threats to Validity (required disclosures)

- **No real LLM evaluated.** C2 is BLOCKED; C1 is a rule-based *simulated_proxy, NOT a real LLM*. Any phrasing suggesting an LLM comparison is prohibited (evidence-card wording enforced).
- **Decision-layer probe, not generation scoring.** The policy is evaluated as a decision layer over MRBench-derived dialogue identity + deterministic scenario injection; we do NOT score generated tutor text against MRBench teacher ground truth or the pedagogical reward model. Benchmark scores published by MathTutorBench/MRBench authors are not comparable to ours.
- **Synthetic scenario ground truth.** Strata labels are generated by documented deterministic rules (`dataset.py`); they verify the *policy contract* under adversarial inputs, not human-validated pedagogy. The scenario answers (numbers) are synthetic placeholders; no claim is made about real task solutions.
- **Single external collection.** External generalization beyond math-tutoring dialogues is unverified (prereg requires two domains for full external generality).
- **Ceiling effects.** The proposed policy scores 1.000 on the strict endpoint under this generator; the generator was built to make every preregistered mechanism falsifiable (ablations do break), but the clean-vs-adversarial separation is known by construction.
- **Calibration semantics.** p_answer is release-worthiness (risk-coverage), not an outcome prediction; prereg-literal ECE (0.414) is dominated by intentional conservative withholding on stage-locked cases; release-scope selective ECE (0.288) and AUROC (1.00) are reported alongside.
- **Deterministic single-seed.** The policy is deterministic; per reliability rules this is one scored seed with byte-for-byte reproducibility, not independent stochastic seeds.
- **Human tasks outstanding.** P03-T19 (ethics/human annotation), T20 (novelty signoff), T21 (coauthor/venue signoff) remain BLOCKED — human-only; no simulated approvals (ETHICS_AND_INTEGRITY.md §10).

## 8. Study status

- Engineering: **PASS** (59/59 tests; strict exit codes; checksum round trips).
- External validity: **PASS at decision-layer** (one licensed external collection executed end-to-end; generation-level and second-domain external validity remain unverified).
- Release: **NOT SUBMISSION_READY.** Blocked on C2 (or an explicit claim adjustment), human annotation (T19), novelty signoff (T20), and coauthor/venue signoff (T21).

## 9. Reproduction

```bash
python3 -m research_v3.experiments.p03.run_matrix            # full frozen matrix
python3 -m research_v3.experiments.p03.run_matrix --fetch-only
python3 -m pytest tests/research_v3/method/test_p03_policy.py tests/research_v3/method/test_p03_eval.py
```

Artifacts: `research_artifacts_v3/runs/p03/{raw,reports,manifests}/` (all SHA256-pinned; manifest re-verifies checksums on every run and fails closed on mismatch).
