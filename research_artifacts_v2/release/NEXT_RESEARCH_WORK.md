# Next Research Work — Research V2

This file records what is **not** finished, honestly. The V2 stack produces
reproducible synthetic-policy evidence; it does not yet produce human-validated
or externally-licensed evidence.

## 1. Blocked on external prerequisites

| Item | Why blocked | Action to unblock |
|---|---|---|
| **T1 external datasets (all 10 studies)** | No licensed external dataset was supplied with a verifiable source URL, version and file hash. | Provide a license-cleared dataset + provenance; register it in `research_v2/data/manifest.json` as `external-licensed`. |
| **T2 real Huế heritage expert annotations** | No real human annotation trail exists. Synthetic templates must never be relabeled as human expert consensus. | Recruit real annotators, run the blind labeling interface, record adjudication logs and inter-annotator agreement (Cohen/Fleiss κ). |
| **C2 original published models** | No source, weights or compatible license for these policy tasks. | Obtain upstream code/weights with a compatible license and build a matched output adapter; verify the task is comparable before use. |
| **Real LLM inference baseline (LN-04 C1)** | Current C1 is a rule-based *simulated* proxy, not a real model. | Run an actual model under a documented budget and terms of service; record provider, model id, version, temperature and cost. |

## 2. Known scientific limits

- Primary endpoints are **software-policy decisions** on synthetic scenarios, not
  longitudinal classroom learning outcomes.
- Statistical significance is over correlated, template-generated cases; it is
  **not** independent human evidence. CIs use Wilson/Clopper–Pearson and a
  group-cluster bootstrap to avoid overstating precision.
- Group-level splits respect template family, but no true learner or time split
  exists because no real learner data exists.
- Two studies (LN-06/07/09) have ablations that are not separable on the
  synthetic T3 distribution; this is disclosed, not tuned.

## 3. Engineering follow-ups

- Promote the LN-06 minimum-cost subset fix from `research_v2/methods/ln06/` into
  the legacy engine under change control (feature-flagged) with the existing
  regression tests.
- Add a real dataset ingestion pipeline once T1/T2 data arrives, including
  de-duplication and distribution-shift checks (spec 03 sections 16–23).
- Add plotting/table generation from `metrics.json` (currently CSV + markdown).

## 4. What must NOT be claimed

- No claim of Q1/A* acceptance, journal acceptance, or venue likelihood.
- No claim of human expert agreement, institutional endorsement, or learning gains.
- No claim that synthetic ablations tied on T3 imply a mechanism is unnecessary.
