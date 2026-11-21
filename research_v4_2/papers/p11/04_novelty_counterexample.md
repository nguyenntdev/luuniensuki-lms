# P11 Novelty Counterexample

## The Failure of Closest Prior Art (Standard Analytic Rubrics)
Standard analytic rubrics (such as Stanford SHEG or generic 4-tier inquiry scales) instruct scorers to evaluate 'sourcing' on an abstract Likert scale. When confronted with a student submission citing a plausible but entirely fabricated imperial edict (e.g. Case CC05: 'Châu bản số 9999'), human raters and LLM baselines award top scores (Level 3) because formal citation syntax is present.

## Candidate Winning Mechanism
Evidence-Anchored Adjudication binds scoring directly to verified archival span digests and applies deterministic caps:
1. If cited span `verified == False`, `CAP_FABRICATION` immediately restricts authenticity and corroboration to Level <= 1.
2. If rater score discrepancy across facets exceeds `discrepancy_threshold` (1.0), active targeted arbitration is triggered exclusively for the discordant facets, boosting Krippendorff's alpha from ~0.72 to >= 0.88 without requiring full re-reading of concordant items.
