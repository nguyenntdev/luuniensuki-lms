# P13 run findings (auto-generated; construct guard passed)

Generated: 2026-11-15T12:10:39.281126+00:00

## Data (real OULAD, CC BY 4.0, sha256-verified)
- studentVle rows: 10,655,280 total; 3,810,268 inside the day 0-60 feature window
- learner-module-presentation rows: 32,593 (zero clicks in window: 4,247)
- outcomes: {'Pass': 12361, 'Fail': 7052, 'Withdrawn': 10156, 'Distinction': 3024}

## Classification (Pass vs rest; fixed logistic regression)
- group split  : C0 AUC 0.7150 | C1 AUC 0.7357 | C2 AUC 0.7070
- temporal holdout (test=2014J): C0 AUC 0.7200 | C1 AUC 0.7424 | C2 AUC 0.7010
- C2 vs C0 (group): delta -0.0080 CI95 [-0.025342013878104287, 0.006277889420492154]
- C2 vs C0 (time) : delta -0.0190 CI95 [-0.029635148280617245, -0.0042273183631776476]

H0 verdict: H0_primary NOT rejected: C2 phase-structured SRL proxies do not beat C0 raw click count by the preregistered 0.02 AUC margin (delta=-0.0080, CI95 [-0.0253, 0.0063]). Per the preregistration this null result is published: SRL proxy structure adds no classification value beyond generic activity volume in this setup.

## Construct validity (central limitation)
All SRL features are clickstream proxies flagged construct_validity:
proxy_only. OULAD contains no SRL instrument; SRL was NOT measured,
and no causal claim is made anywhere in this study.

Full metrics: metrics_full.json | splits: splits_manifest.json
