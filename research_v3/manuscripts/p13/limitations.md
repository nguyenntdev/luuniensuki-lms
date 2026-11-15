# P13 — Limitations (supplementary; spec §3 proposed module reports/P13_limitations.md)

This file passes the construct-validity guard by construction: it states only
proxy-level claims. Any future edit claiming construct-level SRL evidence
will make the runner fail (enforce_proxy_guard) — that is the point.

## 1. Construct validity — the central limitation
OULAD clickstream records *that* a VLE page was requested, never *why*.
Zimmerman's SRL phases are cognitive-motivational processes; our features are
frequencies, gaps, entropies and ratios over page-load events. The mapping
(methods/p13/srl_operationalisation.md) is an analogy licensed by prior
learning-analytics work (Jovanović et al., 2017; Kizilcec et al., 2013;
Gašević et al., 2016), not a construct-validation study. There is no criterion
measure in OULAD to validate against, so convergent validity is UNTESTABLE
here — stated as unresolvable within this dataset.

## 2. Withdrawal circularity
Withdrawn students stop clicking; several proxies (days_since_last_activity,
reflect_late_activity, effort totals) mechanically differ once withdrawal
occurs. Contrasts vs Withdrawn therefore partially restate the label. The
Pass-vs-Fail contrast is the cleanest of the three and shows the smallest
effects — consistent with the circularity explanation rather than a strong
behavioural-SRL signal.

## 3. Confounding by course structure
TMA deadlines (day 19/54 per assessments.csv) and exam scheduling drive
activity regularity. plan_regularity and reflect_late_activity cannot separate
learner-generated pacing from institutional pacing.

## 4. Help-seeking proxy weakness
forumng clicks count page loads; OULAD does not distinguish reading from
posting. help_seeking_* features under-identify actual help-seeking behaviour.

## 5. Statistical limitations
- Learner-cluster bootstrap (2000 resamples) treats presentations as fixed;
  presentation-level randomness is not captured (only 22 presentations exist;
  a mixed model was considered and rejected as over-parameterised for 4
  calendar periods).
- Mann-Whitney p-values with n>10^4 are near-degenerate; effect sizes with CIs
  are the primary descriptive evidence, p-values are secondary.
- ECE is computed on un-recalibrated fixed-C logistic outputs by design; it
  quantifies the honest operating point, not a tuned optimum.

## 6. External validity
Single dataset (OULAD), one institution, one national distance-learning
context. External generalization marked UNVERIFIED in the preregistration; no
cross-institution claim may be made.

## 7. Temporal drift
Presentation profiles (runs/p13/metrics_full.json §E07_presentation_profile)
show forum share falling 0.23 → 0.09 across 2013B→2014J: the *meaning* of
click-mix features drifts across presentations. Any deployment-flavoured
statement would be unwarranted.

## 8. What this study does NOT support
- No claim that SRL was measured (guard-enforced).
- No claim that any intervention changes SRL or outcomes.
- No claim that the proxies validate Zimmerman's model.
- No claim that Pass-vs-Withdrawn gaps are SRL deficits.
