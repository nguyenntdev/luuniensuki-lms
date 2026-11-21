# Minimum departures from archived score prefixes

This retrospective P06 development diagnostic uses the archived CatBoost point
scores on the same OULAD 2013J and UCI 697 cohorts. Prior aggregate results were
available when this design was written. Freeze all settings below before
opening evaluation outcomes in this replay. The original policies were frozen
using their training data and unlabeled evaluation covariates. Reuse their
archived outcomes as controls. There is no new predictive fit, calibration,
policy selection or evaluation-label-dependent rule proposed for use.

The original one-point precision allowance is relative to unrestricted
logistic ranking. Its absolute capture requirement is the primary floor.
The prior boosted study found it impossible under fixed CatBoost score order
on both cohorts. Keep the same course-specific budgets, FA*IR prefix tables,
eligibility and lexical score ties. Ask how many same-group replacements to
score prefixes even a decision maker with outcomes would need to reach that
floor, with and without a practical recall target. Require an improvement
of at least two percentage points over the highest archived worst-group
recall among prefix-constrained policies across the logistic and CatBoost
studies, separately on each cohort. Compute both group capture requirements
by exact rational ceilings from the archived counts. Use the scorer-relative
one-point floor as a control, keeping the same recall target.

For each course and feasible group seat split, take the corresponding
CatBoost score prefix in each group as the reference. One replacement removes
one selected member and admits one unselected member of that same group and
course. Count replacements across all courses. For a cutoff at n, the
eligible removal ranks in a band of width w are n-w+1 through n, and eligible
admission ranks are n+1 through n+w, clipped to the group size. Fix widths
zero, one, five, ten and unrestricted before evaluation. Width zero
reproduces the fixed-order oracle. At unrestricted width, the maximum-recall
and maximum-capture controls reproduce the prior free-order oracle. The
reference seat split can vary in every arm at zero cost, so the bound is
optimistic relative to modifying any single existing policy. Within each
group, keep score order among the chosen learners when interleaving the
lists to satisfy FA*IR. The metric counts membership changes relative to the
lexically tie-broken prefixes, even when two scores are exactly equal.

At any split, useful replacements exchange a selected non-case for an
unselected case. The capacity for such improvements is the smaller of these
two counts within the band. Every integer up to the capacity is attainable.
Neutral and harmful replacements can be removed while preserving or improving
both outcomes and decreasing cost. An integer program finds the minimum
replacement count, and a separate budget-indexed dynamic program verifies
the minimum and rejects a budget one smaller. Use all band capacities to
identify impossible targets and report maximum capture and recall
regardless of replacement count. Check the zero-width and unrestricted
arms against the saved oracles. Retain all impossible targets and all
archived policy failures. These label-informed bounds concern finite cohort
attainability under fixed hypothetical budgets. They cannot establish a
paired precision confidence bound or the effect of offering support.
