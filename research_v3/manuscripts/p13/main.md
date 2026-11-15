# P13 — Phân tích hành vi tự điều chỉnh học tập trong môi trường học trực tuyến
# (Analysing self-regulated learning behaviour in online learning environments)
# Manuscript skeleton — all numbers are placeholders filled from
# research_artifacts_v3/runs/p13/ ONLY (E12 rule: no hand-entered metrics).

> STATUS: CONSTRUCT_VALIDATION_REQUIRED. This skeleton deliberately avoids any
> SRL-construct claim: proxies only. Venue target per spec: Tạp chí Khoa học
> và Giáo dục – ĐH Sư phạm Huế (HĐGSNN), verify CFP/rank at submission time (P13-T21 human).

## 1. Introduction
- RQ (frozen in preregistration): Which observable clickstream behaviour
  patterns — operationalised as Zimmerman phase-structured SRL *proxies* —
  differ across outcome groups (Pass vs Fail vs Withdrawn), and how far can
  outcome be predicted from those proxies alone within a leakage-safe
  early observation window (day 0–60)?
- Positioning: descriptive/observational learning-analytics study.
  NOT a study of the SRL psychological construct itself; NOT an intervention study.

## 2. Related work
- Zimmerman (2000) phased SRL model; Winne & Hadwin (1998) studying-as-SRL.
- Zimmerman & Martinez-Pons (1988) strategy construct validation (what a real
  measurement requires — contrast with our proxy limitations).
- Learning analytics on behavioural traces: Jovanović et al. (2017) forum
  indicators; Gašević et al. (2016) low-inference metric critique;
  Kizilcec et al. (2013) temporal engagement patterns.
- OULAD baseline literature: Kuzilek et al. (2017) dataset paper; risk-prediction
  strands (overlap with P06 disclosed: same data, different estimand — P06
  ranks budget-constrained interventions, P13 describes SRL-proxy structure).

## 3. Data and provenance
- OULAD (CC BY 4.0), sha256-verified snapshot; 10,655,280 studentVle rows;
  32,593 learner-module-presentation rows; 22 presentations; label
  final_result. (Table: counts from runs/p13/metrics_full.json §data.)
- Feature window: day 0–60 only; rows with zero in-window clicks retained and
  flagged (never silently dropped).

## 4. SRL proxy operationalisation (construct_validity: proxy_only)
- Table from methods/p13/srl_operationalisation.md (11 proxies × Zimmerman
  phase × citation × threat-to-validity). NO proxy may be reported as an SRL
  level; no composite "SRL score" is formed.

## 5. Method
- Baselines: C0 raw click count; C1 session/time descriptive; C2 phase-
  structured SRL proxy profile. All: fixed L2 logistic regression (C=1.0,
  no search), identical splits and compute.
- Ablations A1–A4 as true removals (feature sets verified by test).
- Splits: learner-grouped (70/10/10/10, salted hash) and temporal
  (train 2013B/J+2014B → test 2014J; recurring learners purged from train).
- Statistics: Cliff's delta with learner-cluster bootstrap CIs; Holm within
  preregistered family; paired AUC via cluster bootstrap; Brier/ECE.

## 6. Results (all cells auto-generated; evidence IDs in runs/p13/)
### 6.1 Descriptive group differences
- [T1 group_contrasts] Placeholder: Pass vs Fail / Pass vs Withdrawn /
  Fail vs Withdrawn × 11 proxies with CI95.
- Honest summary from the executed run: largest Pass-vs-Withdrawn gaps
  (Δ effort_mean_daily_clicks ≈ +0.43, Δ plan_regularity ≈ +0.39); Fail sits
  between; Withdrawn differs most — but "withdrawn" students stopped clicking,
  so late-window proxies partly reflect withdrawal itself, not SRL (circular
  exposure risk, stated openly).
### 6.2 Classification (Pass vs rest)
- [T2 conditions] Placeholder: AUC/Brier/ECE per condition × split.
- Executed-run result to report as PRIMARY: C2 does NOT beat C0 by the
  preregistered 0.02 AUC margin on either split (group: Δ = −0.008, CI95
  [−0.025, 0.006]; time: Δ = −0.019, CI95 [−0.030, −0.004]).
- **H0_primary NOT rejected → published.** SRL proxy structure adds no
  classification value beyond generic activity volume in this setup.
### 6.3 Calibration
- ECE per condition; reliability curves in figures/.
### 6.4 Robustness & subgroups
- Subgroup AUCs (presentation, gender, age, IMD, education, disability) with
  min_n=20 guard; presentation profile shows temporal shift (forum share fell
  from 0.23 to 0.09 across years) — proxies are NOT presentation-invariant.

## 7. Threats to validity (CENTRAL: construct validity)
1. **Construct validity (central limitation): clicks ≠ SRL.** Every feature
   counts platform events; none measures cognitive self-regulation. The
   machine-checkable guard (research_v3/methods/p13/construct_validity.py)
   fails any artifact that overclaims a construct-level result. No proxy may
   be promoted.
2. **Withdrawal circularity:** Withdrawn students mechanically have fewer
   in-window clicks; group contrasts partially restate the outcome.
3. **Course-structure confounding:** deadlines (TMAs day 19/54) shape
   regularity/late-activity proxies; differences may reflect pacing, not
   planning.
4. **Forum proxy weakness:** studentVle records forum page loads, not posts;
   help-seeking is under-identified.
5. **External validity:** one dataset, one national ODL context; external
   generalization UNVERIFIED (prereg rule).
6. **Temporal validity:** presentation drift (forum share 0.23→0.09) means
   proxy meanings shift across years.
7. **No causal inference is possible** from this design; any causal wording is
   structurally rejected by the guard.

## 8. Discussion
- Null result on phase-structure increment (H0 published per prereg).
- Implication for learning analytics: behavioural regularity is real signal
  for outcome association but adds little beyond volume here; SRL claims need
  instrument-anchored designs (survey/logs with consent), not click counts.

## 9. Limitations & failure analysis
- All strata reported (subgroup tables incl. below-min_n groups flagged).
- A2 ablation quantifies how much ordering information the features carry.
- Negative results retained: E04 (no re-runnable published comparator →
  BLOCKED card), E11 (single dataset → BLOCKED card).

## 10. Ethics
- Public research dataset, CC BY 4.0, no individual consent required per
  provider terms; no re-identification attempted; raw data never committed.
- P13-T19 (ethics sign-off), P13-T20 (novelty sign-off), P13-T21 (authorship/
  venue sign-off) remain BLOCKED for human owners — never simulated.

## Appendices
- A: operationalisation table (full citations)
- B: split manifests + hashes
- C: reproducibility (command, seeds, dependency hashes)
