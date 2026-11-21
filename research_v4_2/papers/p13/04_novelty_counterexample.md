# P13 Novelty Counterexample

## The Failure of Standard Time-Window Baselines
Standard time-window baselines (such as rolling 7-day or 14-day inactivity counters) assume a continuous and stationary observation opportunity. In real academic curricula, schedule breaks (e.g. Tet holiday, exam reading week) cause near-total cessation of student activity.
A standard baseline penalizes persistent students during week 4, generating hundreds of false dropout alerts.

## Candidate Winning Mechanism
The Schedule-Normalized Observation Process conditions the observed click intensity $A_t$ on the scheduled exposure mask $E_t$:
$$A^*_t = \frac{A_t}{E_t + \epsilon}$$
Inactivity during scheduled recess ($E_t \approx 0$) incurs negligible penalty, dramatically boosting AUROC and reducing false positive alarms.
