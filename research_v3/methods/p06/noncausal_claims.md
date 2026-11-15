# P06 NON-CAUSAL CLAIMS LEDGER (frozen)

Status: **NONCAUSAL_UNTIL_PROVED** — permanent for this study unless an RCT or
propensity-adjusted design is added. P06 spec section 1 forbids efficacy claims
without RCT/propensities.

## What the evidence supports (allowed wording)

| Claim ID | Evidence | Allowed wording |
|---|---|---|
| P06-C01 | preregistered matrix, test partitions | "under budget k, the equity-constrained selector captured X% (CI) of realized Fail cases vs Y% (CI) for calibrated top-k" |
| P06-C02 | same | "improve identification / coverage / prioritization of at-risk learners" |
| P06-C03 | calibration module | "risk scores were calibrated on a held-out calibration partition (Brier, ECE reported)" |
| P06-C04 | fairness-gap metric | "the equity floor raised covered share of the disability subgroup from A to B without statistically detectable loss of failure capture (or: with a loss of X, reported as a null/limitation)" |

## What is NEVER claimable (banned wording)

- "interventions avert/reduce/prevent failures" — no intervention was applied;
  OULAD is observational.
- "selected learners improved because of prioritization" — outcome labels are
  realized results, not treatment effects.
- "the teacher's action would have changed the outcome" — counterfactual
  unsupported.
- "SOTA" from beating C0 or a rules-oracle only (spec §1 novelty gate).
- Any causal verb attached to a selection metric.

## Hard boundary statement for the manuscript (verbatim, Methods + Limitations)

> "OULAD is an observational dataset: no intervention was assigned or delivered
> in this study. All metrics measure the agreement between a selection policy
> and *already realized* outcomes. We therefore make no claim that intervening
> on a selected learner would improve their outcome; the ranking's value is
> limited to identifying whom a teacher with capacity k might review first.
> Estimating intervention effectiveness requires an experiment (RCT) or
> observational causal identification (e.g., propensity adjustment), which is
> out of scope."

## H0 disclosure rule

If the preregistered Holm family shows no material advantage of PROPOSED over
C1 (primary Recall@k), the paper MUST publish H0 as not rejected: "constrained
ranking adds no material benefit over calibrated top-K risk ranking", and the
fairness/coverage trade-off is reported as the main finding instead.
