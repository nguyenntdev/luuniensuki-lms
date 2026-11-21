# V4.2 master overview — redesign to maximize real, legitimate win potential

## Decision
Do NOT claim anyone can ensure held-out ML superiority. Require failure-driven novel algorithm and strongest task-compatible baseline. P02/P08 correctness can be formally proved; P04/P11 are primarily benchmark/measurement; P03/P05/P13 need genuine new externally verified lifts.

## V4.1 novelty audit — at a glance

### P01: Selective learner-risk transfer — risk HIGH
- **Observed V3:** Unfair comparison of prediction accuracy at 36.2% coverage; V3 base predictor 0.2091 vs logistic 0.5536 across unmatched denominators; inferential root cause unknown.
- **Residual novelty hypothesis:** Constrained human-review capacity combined with worst-course selective risk under natural term shift, AFTER matching base predictor and matched-coverage policies.
- **Win acceptance:** Primary: worst-course selective error or AURC at pre-fixed equal coverage and review budget; bound on group coverage, total risk non-inferiority and ID performance; Holm-corrected paired CI.
- **Fallback:** If no genuine worst-course discrepancy remains, report base model / allocation audit; no new algorithm paper.

### P02: Exact constrained path planning — risk MEDIUM
- **Observed V3:** Both V3 proposed and B&B solve 100% exactly; proposed p95 1.228ms, B&B 0.451ms on 1,620 toy instances. Quality is at ceiling.
- **Residual novelty hypothesis:** Repeated right-cleared heritage itinerary replanning with changes in crowd, opening windows, accessibility and evidence eligibility; no prior evidence this remains a speed gap vs existing exact solvers.
- **Win acceptance:** Primary: paired p95 end-to-end latency and geometric mean runtime vs fastest eligible exact solver on preregistered dynamic instances; zero invalid routes, zero wrong infeasible claims and proven optimal solutions.
- **Fallback:** If real end-to-end p95 is slower, publish reproducible dynamic-replanning benchmark/invalidation proof or drop speedup claim.

### P03: Pedagogically faithful generated AI tutor — risk HIGH
- **Observed V3:** Decision-layer score saturates at 1.0 and a C0 comparator also 1.0; real generated tutor turns and human teacher reference absent.
- **Residual novelty hypothesis:** Evidence-sufficiency versus misconception-targeted scaffolding in multi-turn math dialogue; not generic RAG or another instruction prompt.
- **Win acceptance:** Primary: blinded, randomized expert paired preference (pedagogical rubric) for real generated responses, same base LLM/token budget; co-primary answer leakage limit and grounding failure safety; no success from decision-layer accuracy alone.
- **Fallback:** If human-rated win not present, retain dataset/evaluation contribution; do not report 1.0 decision score as tutoring SOTA.

### P04: Curriculum-shift benchmark — risk MEDIUM
- **Observed V3:** V3 found shift degradation, but task invariance, comparable KT C2 baselines and true removal ablations still unverified.
- **Residual novelty hypothesis:** Verified grade/curriculum ontology shifts with fixed prediction semantics and documented provenance, not a generic synthetic OOD corruption pipeline.
- **Win acceptance:** Primary: benchmark discrimination: fraction of independently validated real failure strata recovered at pre-specified false-discovery limit versus strong generic OOD audit; rank reproducibility, not model AUC.
- **Fallback:** If all shift strata are artificial or models rank identically, release negative benchmark report, not a novel robustness claim.

### P05: Forgetting-aware knowledge tracing — risk VERY_HIGH
- **Observed V3:** V3 advantage +0.0088 AUC over one classical C1 on OULAD; no true LefoKT/HawkesKT/simpleKT comparator; course-level OULAD may not be KT supervision.
- **Residual novelty hypothesis:** Evidence for cross-concept interference with observation-time uncertainty after controlling skill difficulty and relative forgetting; both LefoKT and HawkesKT directly overlap with simple time decay.
- **Win acceptance:** Primary preregistered next-question NLL or AUC (choose before TEST); must beat max(dev-ranked C2 candidates) on test on >=2 datasets with Holm-corrected cluster bootstrap and no serious calibration regression; long-gap result supportive unless preregistered primary.
- **Fallback:** If no consistent C2 gap on DEV, end novel KT model track; reframe V3 OULAD as calibrated early warning. Never re-use dev experiments to select one-shot TEST.

### P06: Fair budget-limited teacher prioritization — risk HIGH
- **Observed V3:** V3 tied C1 on 6 contrasts; fairness constraint never bound; no observed teacher treatment effect.
- **Residual novelty hypothesis:** An externally observed nontrivial fairness–utility tradeoff under binding capacity constraints, not contrived allocation where a constraint never activates.
- **Win acceptance:** Primary worst-group recall/utility at equal K and equal permitted protected attributes, plus strict cap on total utility loss. Winner needs meaningful binding fairness constraint on held-out natural cohorts; no RCT/no causal effect claims.
- **Fallback:** If no natural disparity/constraint activation, stop superiority claim, report negative observational allocation audit.

### P07: Resource- and rights-aware multimedia selection — risk HIGH
- **Observed V3:** 8 external cases, 17 synthetic; nominal 8/8 vs 4/8 raw p=0.125, Holm 0.75; second provider, B00–B03 and licence checks missing.
- **Residual novelty hypothesis:** Independent rights eligibility and evidence completeness across multilingual cultural-media providers under per-session resource constraints, not just retrieval+knapsack.
- **Win acceptance:** Primary expert-rated rights-valid nDCG@k under matched candidate pool/budget; secondary false-permission rate 0 within defined policy, recall loss, source diversity. Compare to strongest rights-aware reranker/ILP.
- **Fallback:** If strong baseline does rights filtering equally well or media labels insufficient, contribute interoperable audit benchmark, not novel optimization SOTA.

### P08: Reward-integrity gamification — risk MEDIUM
- **Observed V3:** V3 shows mechanism contrast on synthetic attack fixtures, no authentic attack prevalence, no external independent attack authors.
- **Residual novelty hypothesis:** Formal invariants of distributed, multi-service replay/reordering and independently authored attacks under constrained transaction performance, beyond standard API idempotency.
- **Win acceptance:** Formal primary: zero double-award/unauthorized-award on a stated, independently reviewed threat model (all algorithms tested); quantitative secondary: throughput/p99 and false-reject vs strongest ledger baseline. A proof is a correctness claim, not statistical model win.
- **Fallback:** If ledger baseline already meets invariants at equal/better latency, release attack testbed and engineering best practices; no originality claim for mere idempotency.

### P09: Evidence-grounded heritage exploration — risk MEDIUM_HIGH
- **Observed V3:** Wikidata 51 claims, only 6 grounded, 0.118 grounding across all methods; structural guard lowers unsafe surfacing but not expert truth.
- **Residual novelty hypothesis:** Distinguishing truly independent primary historical sources from derivative citation loops with temporal revisions; AVeriTeC and CoVeGAT already cover generic claim verification.
- **Win acceptance:** Primary expert-judged grounded answer F1 at fixed coverage and fixed maximum false-support, compared to best citation-aware reranker; separate evidence recall from abstention.
- **Fallback:** If insufficient licensed Hue text/expert labels, support only structural claim-audit and stop historical truth superiority.

### P10: Spiral curriculum plan under evidence constraints — risk MEDIUM_HIGH
- **Observed V3:** V3 162 AI-generated objects, 27/30 anchors unreviewed; no expert teacher evidence.
- **Residual novelty hypothesis:** Minimum-correction teacher-review planning with verified anchor provenance, rather than generating routes on invented curriculum mappings.
- **Win acceptance:** Primary blind teacher correction time or number of correction actions under noninferior validity, compared to teacher-authored and exact DAG baselines; both graders blinded.
- **Fallback:** If teacher reviewers do not agree or no approved anchors, stay BLOCKED; no synthetic student outcome claim.

### P11: Reliability-aware historical reasoning rubric — risk MEDIUM
- **Observed V3:** No human raters, synthetic toy reliability cannot establish rubric gains.
- **Residual novelty hypothesis:** Source-chain-specific score categories and disagreement-guided adjudication for historical argumentation in Vietnamese heritage tasks; many established sourcing rubrics exist.
- **Win acceptance:** Primary Krippendorff α (or appropriate weighted κ) gain above predeclared practical margin on held-out real responses AND no construct validity/time penalty; cluster bootstrap by response/rater.
- **Fallback:** No raters => BLOCKED; if existing rubric same reliability, publish adaptation/validation not new scoring method.

### P12: Page-verifiable archival claim ledger — risk HIGH_OVERLAP
- **Observed V3:** 62/63 ABSTAIN, only hash-chain integrity verified; no real primary archive truth adjudication. Significant scope overlap with P09.
- **Residual novelty hypothesis:** Locator-level verification of archival text versions and chain-of-custody under source corrections; must be orthogonal to P09’s evidence retrieval.
- **Win acceptance:** Primary expert-adjudicated locator-correct support recall at fixed false-support limit, compared to exact-span/NLI; secondary tamper detection (formal/engineering).
- **Fallback:** If P09 shares same primary estimand and data, MERGE P12 into P09 technical appendix rather than duplicating publication.

### P13: Early-warning from clickstream (SRL claims gated) — risk VERY_HIGH
- **Observed V3:** V3 SRL-proxy model UNDERPERFORMS click-count (ΔAUC -0.008 group, -0.019 time), no validated measured SRL construct.
- **Residual novelty hypothesis:** Early warning risk under naturally irregular course schedule and measurement effort, beyond generic time-series encoder; no SRL construct claims without real instrument.
- **Win acceptance:** Primary AUROC or NLL at a fixed prediction horizon vs strongest time-window GBDT and temporal baseline, second cohort replication; worst-term stability and ECE noninferiority. Calling it measured SRL requires a completely separate instrument study.
- **Fallback:** If stronger temporal model never beats click/GBDT, redesign as negative-result early-warning study; do not mislabel it SRL.

### P14: Heritage learning-object accessibility — risk MEDIUM_HIGH
- **Observed V3:** V3 13 synthetic objects, automated criteria count but no user outcomes or realistic licensed media.
- **Residual novelty hypothesis:** Historical-media semantic alt-text appropriateness and source-grounded accessibility testing distinct from general WCAG source-code audits.
- **Win acceptance:** Primary expert-judged critical semantic-accessibility recall at same false-alarm burden versus axe/Pa11y+strong LLM baseline; secondary user task completion only if human study done.
- **Fallback:** Without actual human-labelled media, limit to conformance checker report and do not claim better learning accessibility.

## Non-negotiable prior-work blockers
- P01 cost-aware conformal deferral already appears in a 2026 publication, and CRC predates it. Avoid calling combined conformal gate novel.
- P05 time decay, relative forgetting attention, cross-skill temporal excitation and difficulty representations all have published counterparts. New mechanism needs a nearest-work formal counterexample.
- P06 fairness-constrained prediction optimization already appears in UAI 2024.
- P09/P12 claim citation graphs and temporal evidence insufficiency already appear in prior fact-checking work, so domain-specific source lineage + archival edition requirements are research hypotheses, not declared inventions.
- P13 SRL proxy construct absent; rename to early-warning risk unless actual validated self-regulation measurement occurs.

## Key source refs
See `08_REFERENCES/VERIFIED_CLOSEST_WORK.md` for URLs, publication, and methodological relevance. Full literature and code replication remain pending.

## Global win contract
See `02_WIN_CONTRACT/WIN_CONTRACT.md` (strongest DEV champion, effect Δ>=preregistered meaningful δ, adjusted uncertainty, all constraints and independent replication). Explicit separate status for formal software properties vs model superiority.
