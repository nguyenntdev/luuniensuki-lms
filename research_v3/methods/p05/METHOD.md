# P05 Method Specification — Temporal Forgetting-Aware Knowledge Tracing

**Status:** METHOD_FROZEN_2026-11-15 (written before any test-window evaluation)
**Paper:** P05 — Temporal Forgetting-Aware Knowledge Tracing and Review Scheduling
**Data:** OULAD 2013–2014 (real temporal learner data), attempt-level sequences.

---

## 1. Problem formalization

For learner $s$ in module-presentation $m$ (the OULAD "course instance"), let
assessment attempts be ordered by submission day $t_1 < t_2 < \dots < t_n$
(days since module start, from `studentAssessment.date_submitted` joined to
`assessments.date`). Each attempt $i$ has:

- outcome $y_i \in \{0,1\}$: pass ($\text{score} \ge 40$) vs fail, observed only at $t_i$;
- a score $r_i \in [0,100]$ (observed at $t_i$);
- engagement stream: daily click totals from `studentVle` at days $< t_i$.

**Task:** predict $P(y_i = 1 \mid \text{history}_i)$ for the *next* attempt,
using only information available strictly before $t_i$ (feature cutoff = $t_i$).

**Not a classic KT task.** OULAD has no per-skill interaction stream with
binary correctness per item; assessments are summative, multi-item, and
irregularly spaced. We therefore define the temporal KT analogue honestly:
**next-assessment outcome prediction over irregular intervals**, which is
exactly where a forgetting/decay mechanism can be tested on real data. We do
NOT claim to replicate BKT/DKT item-level KT numbers, and we do not fabricate
per-item correctness that OULAD does not contain.

## 2. Candidate mechanism (hypothesis, not proven)

**Forgetting-aware retrieval state.** Following half-life regression
(Pavlík et al. 2009; Moèri et al. 2016 — see citations in manuscript) and
FSRS-style exponential stability (Jarrett, open-source FSRS), each attempt's
predicted correctness is driven by a *retrieval strength* that decays
exponentially with elapsed time:

$$
\theta_i = \alpha\, m_i \cdot 2^{-\Delta_i / h}
$$

- $\Delta_i = t_i - t^{\text{act}}_i$ = days between the attempt and the learner's
  last activity (last assessment or last click day, whichever is later);
- $m_i$ = ability proxy = exponentially-weighted mean of past scores
  (half-life $h_m = 45$ days, fixed a priori);
- $h$ = per-learner-module forgetting half-life in days, one of a small fixed
  grid $\{10, 20, 35, 50, 80, 120\}$ selected on the **calibration window only**;
- $\alpha$ = monotone link: $\alpha \in (0,1)$ via a fixed logistic transform;
  larger $\alpha$ means slower forgetting (monotone constraint: $d\theta/d\Delta < 0$).

**Feature assembly (all causal, cutoff-safe).** The final feature vector is:

| group | features | ablation that removes it |
|---|---|---|
| decay kernel | $\theta_i$ (retrieval strength), $\Delta_i$, $\log(1+\Delta_i)$ | A1 |
| recency | days since last attempt, days since last click, count of attempts in last 14 days | A5 |
| frequency | total past attempts, total past active days, mean past click rate | A4 |
| ability | mean/std/min/max of past scores, past-fail count | A3 |
| context | module one-hot, assessment-type one-hot (TMA/CMA/Exam), assessment weight | none (kept in all models) |

Final probability: logistic regression over these features plus a
*temperature-calibrated* output (temperature fit on the calibration window,
A2 ablation skips it). Learned weights: logistic coefficients only — fitted on
the train window (2013B/2013J) with L2 (C grid on calibration window).
Fixed constraints: monotone decay form of $\theta_i$; the half-life grid; the
cutoff rule. No learned parameter ever sees calibration-window or test-window
outcomes for the test prediction.

**Distinct from C1:** C1 uses the *same* recency/frequency/ability/context
features but **no $\theta_i$ / $\Delta$-decay features** — i.e., identical
information except elapsed-time decay structure. That is the honest matched
contrast: same data, same model family, same tuning budget; the only delta is
the forgetting mechanism.

## 3. Review scheduler

For every at-risk pair (learner-module in test window with an upcoming
assessment whose outcome is unknown), compute risk $= 1 - \hat p(\text{pass})$.
Rank descending by risk. **Decay-ranked scheduler:** when two pairs tie on
predicted risk, order by shorter elapsed gap $\Delta$ (the pair that has been
idle longest among equally-risky pairs is reviewed first — this is the
scheduling decision the decay model uniquely motivates). Budget $k\%$ of
ranked pairs is "reviewed"; a review "succeeds" if the pair's eventual outcome
is a failure. Recall of failures at budget $k$ is the utility metric.
Controls: C1-frequency ranking (same risk model as C1, no decay tie-break)
and a random ranking (seeded, deterministic).

## 4. Objective, optimizer state, certificates

- Objective: log-loss (NLL) of attempt outcomes; L2-regularized logistic
  regression solved by liblinear (deterministic at fixed data/order/seed).
- Optimizer state: converges; we record `n_iter` and declare convergence.
- Runtime cap: full matrix must finish < 30 min CPU; grid sizes are small.
- No stochastic training: a single scored seed (11) plus byte-identical
  rerun check (determinism test).

## 5. Novel vs reused components (attribution)

| component | status |
|---|---|
| `research_v3/eval/*` splitters, statistics, calibration | **reused** (repo standard) |
| OULAD adapter concept | **reused** (`research_v3/datasets/adapters/oulad.py`); attempt-level extension is **ours** |
| logistic regression, AUC/Brier/NLL | **standard** (scikit-learn) |
| half-life retrieval strength $\theta_i = \alpha m 2^{-\Delta/h}$ | **adaptation** of half-life regression / FSRS concepts, implemented from equations above; no upstream code used |
| decay tie-break in scheduler ranking | **ours** (simple, stated as such) |
| C0/C1 baselines | **ours**, standard constructions |

## 6. Complexity

Feature assembly $O(A \log A + C)$ where $A$ = attempts, $C$ = click rows;
training $O(A \cdot d)$ per grid point ($d \approx 30$ features); full grid
$O(|H| \cdot |C_{\text{grid}}| \cdot A \cdot d)$. Everything fits in RAM
(< 1 GB for OULAD-scale).

## 7. Limitations declared in advance

1. OULAD clicks and assessment scores are **proxies**, not measured memory.
2. Scores of high-stakes exams are noisy labels for "retrieval success".
3. Single external domain (OULAD): external generalization **unverified**.
4. C2 (published KT comparator) BLOCKED — see `experiments/p05/blocked_cards.yaml`.
5. PASS-at-40 is a coarse dichotomization of a 0–100 score.
6. The scheduler is evaluated in **logged-policy replay**: outcomes were
   produced under whatever study behavior actually happened, not under our
   policy; off-policy bias is a real threat and is discussed in the manuscript.
