# P11 Adjudication Protocol

## Principle
First-round ratings are immutable evidence. Adjudication creates a *third* record; it never
overwrites the original two. The reliability analysis reports both the pre-adjudication
agreement (primary) and post-adjudication agreement (secondary), so adjudication cannot
inflate the headline number.

## Triggers
A unit enters adjudication when, for any criterion:
- the two raters differ by **≥ 2 levels** (e.g., 1 vs 3), or
- either rater marked **ABSTAIN**, or
- either rater flagged `uncertain=1` and the other rating differs at all, or
- the declared structure is suspected incomplete (`EXTRACTION_GAP`).

## Process
1. Both first-round ratings are copied verbatim into `adjudication_log_template.csv`.
2. An adjudicator (a third qualified rater, or both original raters *jointly* with the
   divergence documented) re-examines the unit against the codebook **without seeing which
   rating belonged to which rater** (de-identified as `rating_1` / `rating_2`).
3. The adjudicated value is recorded with a rationale referencing the codebook rule
   (§4 decision rules) — not "compromise" averaging.
4. If adjudication reveals a codebook ambiguity, the codebook is versioned and the incident
   logged; already-rated units are NOT re-rated retroactively unless the calibration round
   rule in CODEBOOK §5 applies.
5. Systematic patterns (one rater consistently −1 level) are recorded as a *rater effect*
   finding, not silently corrected.

## Output
- `adjudication_log_template.csv` filled rows: unit_id, criterion, rating_1, rating_2,
  adjudicated, rationale, adjudicator_pseudonym, decided_at.
- Pre/post adjudication agreement both reported; pre-adjudication is primary.
- Zero fabricated entries: rows exist only after real adjudication sessions.
