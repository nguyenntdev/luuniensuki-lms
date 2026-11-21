# Baseline selection policy and experimental parity

### Baseline discovery
Collect strong C1 and original-source C2 from 2015–2026, with recent 2026 cutoff. Register: `paper_id, title, DOI, code_url, commit_SHA, license, model_weights_hash, compatible_task, label, time_horizon, features, data_rights, metrics, train_compute, tuning_budget, run_receipt`. Never infer C2 equivalence from a name alone.

### Baseline champion
Choose the best baseline **on DEV** from registered task-matched candidates; freeze the selection algorithm, and do not exclude a strong baseline for being inconvenient. If no C2 is actually runnable, label `STRONG_COMPARATOR_MISSING` and prohibit SOTA claims. Equalize data and features or clearly justify non-overlapping feature regimes.

### Tuning budget
Pre-register GPU/CPU hours and trials before training. Start with equal per-family budgets and record every trial. New training recipe changes only after failed DEV trial and source-based rationale. Baseline best implementation can exceed candidate tuning if accepted as official pre-trained reference; otherwise justify constraints.

### Failure forensics
Require shared instance IDs; overlap/error-slice histogram; strata pre-registered from mechanism, not chosen based on test winners. Calculate sample size/power with learner/course/provider clustering. Never collapse P05 KT to P13 course dropout prediction.

### External data
Do not equate a link or licence category with actual dataset permission. Register the captured licence text and file digest; permission for raw redistribution is independent from permission for academic analysis. Keep raw datasets gitignored, tests fixture-safe and strict private integration separately. P03 teacher rating, P11 rater study, P10 curriculum validation, P12 archival truth and P14 accessibility usability need real human tasks/ethics.
