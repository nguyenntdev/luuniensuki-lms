# Literature review, real novelty and independence protocol

## Ownership
Research lead (not the implementation agent) is responsible for screening prior art, interpreting novelty, outlining manuscripts and verifying academic relevance. Code agents must surface evidence and suggest falsifiable gaps, NOT certify novelty unilaterally.

## Mandatory survey workflow before coding an algorithm
1. Define RQ in PICO-like form: target population/unit, decision/algorithm, comparator, objective, setting.
2. Search Google Scholar/DBLP/OpenAlex/ACL Anthology/ACM DL/IEEE/Springer and authors' repositories (2022–Nov 2026, plus foundational classics).
3. Maintain `literature_matrix.csv`: DOI/URL, publication venue/date, actual evaluation data, code/checkpoint available, license, baseline metric, limitation, novelty conflict score.
4. Open and read at least the 10 most closely overlapping full texts per P01–P07 before committing a proposed novelty claim; at least 5 closest per P08–P14; document unavailable works.
5. Include nearest **published** competing implementation wherever license and target/task fit permit. If impossible, mark C2 BLOCKED and adjust claim.
6. Document exact delta: input assumptions, objective, output semantics, proof/algorithm, evaluation, robustness and reproducibility. Not just renamed modules.
7. Evidence must invalidate a serious baseline under paired comparisons, not just exceed a weak sanity rule.
8. Record serious null results and negative transfer; failed proposed techniques may lead to a valuable benchmark/limitation paper but must not be marketed as superior.
9. Screen overlapping text, figures, tables, hypotheses with HCMUS poster, Q2 manuscript, 10 LN drafts, and other P papers.
10. Refresh search during author submission and venue 2027 CFP window; venue rank/acceptance is not a scientific metric.

## Required neighboring literature by theme (verify publication details directly)
- P01/P04: DKT, SAKT, AKT, GKT, SAINT+, domain adaptation, modern cross-domain KT (including DTransKT and RAG-KT mentioned in prior planning).
- P02: exact CP-SAT and MILP, prerequisite graph planning, robust optimization, set cover with alternatives, constrained RL.
- P03: MathTutorBench (EMNLP 2025), Socratic tutoring, source calibration, abstention/uncertainty, prompt injection defenses.
- P05: FSRS, half-life regression, time-aware KT, forgetting and interval recommendation with correct propensity limits.
- P06: EWS on OULAD, calibration, fair ranking and resource-constrained decision support; separate risk from action effect.
- P07/P14: Universal Design for Learning, WCAG 2.2 criteria, accessibility parity, task affordance and multimodal retrieval.
- P08/P09: design-science gamification and scholarly digital heritage interaction; compare actual user actions, not architecture diagrams.
- P10–P14: Vietnamese education sources, historical reasoning rubrics, content validity theory, SRL construct measurement and local heritage source criticism.

## Scientific contribution collision rules
- P01 vs P04: methods vs public benchmark protocol; merge if P04 cannot independently support a full reusable benchmark.
- P02 vs P10: algorithm/optimization vs instructional design/teacher validation.
- P03 vs P11 vs P12: tutor action policy vs validated human scoring rubric vs source curation protocol.
- P07 vs P14: external-object ranking vs human-centered UDL materials and outcomes.
- P08 vs LN-05: cannot simply republish anti-replay software QA as design-science evidence.
- P09 vs P12: user interface effectiveness vs historical source verification process.
- P06 vs P13: budget risk ranking vs SRL measurement; OULAD log overlap must be disclosed.

## Final novelty gate
Reviewer A writes strongest rejection argument, Reviewer B tries to reproduce closest published method, Reviewer C checks main tables/results overlap. If 'not independent' decision persists, mark `MERGE_REQUIRED` not `COMPLETE`.
