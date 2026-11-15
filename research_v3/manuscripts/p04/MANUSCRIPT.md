# P04 Manuscript — CurriculumShiftBench: Evaluation under Incomplete Skill Mappings

**Venue target:** EDM (CORE B) — CFP, rank-2027 and fit verification pending (P04-T21, human).
**Status:** `ENGINEERING_PASS` (protocol + reference evaluation done; human signoffs pending).
**Independence:** `PROCEED` — see `research_artifacts_v3/runs/p04/independence_decision.json`.

> Every numeric claim below cites an evidence ID: `E-<claim>` pointing to
> `research_artifacts_v3/runs/p04/reference_eval/leaderboard.json`
> (sha256 of the file is recorded in the experiment card; no hand-entered
> numbers).

## 1. Contribution and boundary with P01

P04 contributes a **benchmark protocol**, not a transfer method: frozen shift
strata over a verified ontology bridge, a scoring contract where NOT_APPLICABLE
and ABSTAIN are first-class classes, a leaderboard schema with honest
denominators, and reproducible reference cells. P01 contributes a **transfer
gate method** judged on standard target-domain metrics. The primary tables are
structurally different (rows=strata x predictors with degradation/CIs vs
rows=baselines with target metrics); sample overlap (OULAD) is disclosed.

## 2. Protocol (METHOD.md summary)

- Data: OULAD 2013-2014 (32,593 rows, CC BY-NC 4.0, hash-frozen) and UCI
  student-performance (1,044 rows, CC BY 4.0) [E-rights].
- Splits: learner-level group split (salt `p04-v1`) and 2013->2014 time split,
  hashed in `research_v3/methods/p04/protocols/p04_splits.json` [E-splits].
- Strata: S0 in-domain reference; S1 partial mappings (20/50/80% edges hidden);
  S2 annotation-budget unknown categories (real unseen BBB/EEE `quiz`
  categories, 31 gap rows); S3 domain shift (presentation, course, subject);
  S4 cold start (zero early clicks) [E-strata].
- Estimand: per-stratum AUC degradation with learner-cluster bootstrap 95% CI
  (1000 resamples, seed 42) [E-prereg].

## 3. Reference results (measured, C1 logistic regression)

| Stratum | Scenario | AUC | delta vs S0 | 95% CI | n_scored |
|---|---|---|---|---|---|
| S0 | in-domain (OULAD) | 0.808485 | — | [0.7938, 0.8234] | 3327 |
| S1 | partial 20% | 0.760892 | 0.047593 | [0.7400, 0.7813] | 2279 |
| S1 | partial 50% | 0.765536 | 0.042949 | [0.7407, 0.7873] | 1661 |
| S1 | partial 80% | None | — | — | 0 (coverage 0) |
| S2 | annotation budget | 0.727809 | 0.080676 | (see artifact) | 914 |
| S3 | presentation shift | 0.792101 | 0.016384 | [0.7859, 0.7989] | 19064 |
| S3 | course shift | 0.757891 | 0.050594 | [0.7490, 0.7668] | 10296 |
| S3 | subject shift (UCI) | 0.745355 | vs UCI S0 0.840659 | (see artifact) | 649 |
| S4 | cold start | 0.650029 | 0.158456 | (small-n) | 435 |

C0 majority: AUC 0.5 on every scored cell (constant-probability predictor) —
sanity check passes [E-c0].

**Null assessment.** Under the frozen decision rule, H0 does NOT stand: four
strata show CI-separated degradation for C1 (S1@20%, S1@50%, S3-presentation,
S3-course). Rank stability across strata is 1.0 for the 2-model reference
population (trivially; rank stability becomes informative only with >=3
submitted models). S1@80% yields an empty denominator (coverage 0) — reported
as an honest structural failure of extreme mapping loss, not imputed [E-null].

**Interpretation guard.** These are reference-baseline numbers establishing
that the protocol measures real, reproducible degradation. They are NOT a
comparison against published KT systems (P04-T08/T11 pending) and must not be
cited as SOTA or as evidence about DKT/SAKT/AKT/GKT behavior.

## 4. Failure analysis by stratum

- S2 (annotation budget): 192/1106 test rows unmappable (31 genuine
  unknown-category gaps + 161 no-activity rows); worst group
  `gender=F/age=35-55` accuracy 0.458 (n=179) [E-s2].
- S4 (cold start): largest degradation (+0.158); small-n warning active
  [E-s4].
- ECE degrades under shift (e.g. S2 C1 ECE 0.246 vs S0) [E-ece].

## 5. Limitations

1. Two datasets only; external generalization UNVERIFIED (ASSISTments/Junyi/
   EdNet BLOCKED with recorded reasons) [E-blocked].
2. Reference population is C0/C1 only; KT baselines pending (T08/T11).
3. Ablations A1-A4 defined but not yet executed (protocol rows reserved).
4. OULAD license is CC BY-NC 4.0: no commercial use of any P04 artifact.
5. UCI cells carry small_n warnings; CIs on those cells are exploratory.

## 6. Reproduction

```bash
python -m research_v3.methods.p04.run_reference_eval
python -m pytest tests/research_v3/method/test_p04_protocol.py
```

Requires `private_data/raw/oulad/2013-2014` and
`private_data/raw/uci/student-performance-2014` with matching sha256 (verified
automatically). Determinism: two consecutive runs produce identical canonical
JSON [E-determinism].
