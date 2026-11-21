# Which contribution survives its closest comparison?

The portfolio's first manuscript is the day-60 withdrawal study (P13 in the original specification). The contract called P01 concerns selective multiclass prediction. The two share OULAD and several precedents. They answer different questions about the same learner: is the learner eligible for contact, and should a classifier issue a label? Results below use the strongest matched control even when a more famous published algorithm performed worse. A published number on another cohort is a design comparison. The [ten-method audit](TEN_METHODS.md) retains its original denominator and thresholds. Every original contract has its own endpoint, minimum effect and designated comparator. These appear below exactly as recorded, including formal contracts with zero numerical margin. A replacement public-data endpoint has a separate interpretation. The 10 audited methods have **zero strong spec-level wins**.

## Paper 1. Can a stale enrollment register reverse the value of an alert queue?

| Closest primary study | Population, decision time, target and actual comparator | Endpoint and published result | What the local design adds |
|---|---|---|---|
| [Kovari, Computers, August 2026, §§3.6 and 4.3](https://doi.org/10.3390/computers15090560) | OULAD, nine same-module/period year pairs, days 14 and 56. Unsuccessful completion includes failure and withdrawal. Score-free logistic models, landmark vs all registered, with pooled sensitivity and LightGBM checks. | Day-56 pooled AUC .776 landmark and .856 all registered. Cohort definitions and reliability under shift are already published. | At the same horizons we vary target and test membership with predictions held fixed. At day 60 the withdrawal-only gap is .2107. Already-exited positives account for 63.75% of positive–negative pairs and win 95.33% of those comparisons. The pair identity explains the observed gap exactly. |
| [Sánchez Trujillo et al., Data, October 2026, §3 and Table 7](https://doi.org/10.3390/data11110281) | OULAD, eligible registrations at days 28, 56 and 84, future withdrawal, 2014J temporal test. Assessment trajectories, LR, RF and XGBoost, calibrated forecasts, fixed thresholds and 5/10/20% contact budgets. | Day-84 LR AUC .7102 and RF .7104. Top-decile LR precision 34.0%, recall 25.7%. Explicitly measures workload on an eligible roster. | We freeze module-specific seats and scores and vary administrative reporting lag, including whether already-exited learners can consume seats. The difference between 34.0% on their day-84 roster and 32.46% on our day-60 roster cannot identify a model effect. |
| [Wu, Duan and Luo, PLOS ONE, July 2026, workload and split-stability analyses](https://doi.org/10.1371/journal.pone.0352867) | OULAD, days 0–27, binary withdrawal, course-presentation group split, 4,359 held-out records. Nine classifier families, calibrated histogram gradient boosting for deployment analyses. Ranks top 10/20/30% for alerts. | At 10%, 435 alerts, precision .834 and recall .318. Results depend on the group split and eligibility definition. | Our denominator is a fixed number of seats per module based on active registrations. The numerator counts captured **subsequent** withdrawals. It permits the same trained ranking to be compared under timely and delayed registers. |
| [Wu et al., selective prediction and subsequent figure correction](https://doi.org/10.1371/journal.pone.0355736) | Same study and population as the preceding row. Confidence-based abstention changes which automated decisions are issued. | From full to 50% coverage, their reported alert precision rose from .721 to .894 and overall recall fell from .472 to .236. The August correction replaces the reference-threshold confusion-matrix figure. | P01 separately measures label changes on identical accepted IDs for a multiclass gate. The withdrawal queue study measures capture at fixed outreach capacity. The two Wu analyses supply one prior cohort. |

| Question | Answer supported by the local data |
|---|---|
| What is the contribution? | A fixed-score decomposition and a decision consequence. Ranking all registrants can make retrospective discrimination look better while spending review seats on people who have already left. Prior work already establishes landmark conditioning, top-budget alerts and abstention. |
| How large is the effect? | At 878 seats, current-status CatBoost captured 285 cases. With 7 days' lag it captured 278, with 30 days 236, and with no filter 47.73 in expectation under cutoff ties. The corresponding current/unfiltered uniform counts were 137.83/107.23. The advantage over uniform changed from +16.76 to −6.78 actionable cases per 100 seats, simultaneous intervals [13.13,20.07] and [−8.30,−5.26]. The measurement study registered no minimum useful service effect. |
| What is the decisive comparison? | The **identical CatBoost scores and seats** under each eligibility policy isolate the register effect. Logistic ranking also reversed, 279 versus 40.83 captured. Uniform measures the value of prioritization at the same capacity. We reproduced the day-84 published LR/RF/XGBoost queues from the authors’ eight score exports. At 857 seats those three assessment models captured 291/288/280. Under a 30-day delay the LR capture bounds are 199–291, wholly above uniform (109.37); the unfiltered bounds include uniform. Calibrated HGB from Wu et al. remains a published-only comparison. No result here ranks the local CatBoost over them on day 60. |
| Which result travels? | Two fixed activity rules reproduced the direction in three more offerings at the **same UK university**. The 2014J intervals resample learners conditional on scores, roster and capacity. Delays were imposed. A second provider with enrollment starts, dated exits, features as available at decision time and preferably status-delivery timestamps would identify the corresponding between-provider effect. The two rules were also run unchanged on an independent MOOC action stream. At its midpoint only inactivity reversed (+18.82 to −8.19 cases per 100 seats vs uniform); fewer-actions-first stayed favorable in both conditions. The target is a first flag defined using the last observed action. Current flag visibility is therefore an oracle condition, with a different roster and follow-up. |
| Does the result justify a separate paper? | Plausible measurement contribution for LAK/EDM if framed around the queue reversal, with the above prior work in the main text. A first landmark method, a superior withdrawal predictor and prevented withdrawals each exceed the evidence. |

[Manuscript and horizon-by-target sensitivity](landmark/manuscript.md) · [Fixed-budget evidence](landmark/status_lag/README.md) · [Published models on identical cases](landmark/published_capacity/README.md) · [Day-84 bounds](landmark/status_bounds/README.md) · [Cross-provider fixed-rule transfer](landmark/mooc_queue/README.md)

## Educational prediction and decision policies

Each table identifies the closest verified published task or method, the decision being tested, the endpoint and margin, the strongest executed comparison, and the boundaries on a separate contribution.

### P01 selective classification

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [Wu et al.](https://doi.org/10.1371/journal.pone.0352867) use binary withdrawal, calibrated HGB, day 27 and risk–coverage curves. [Maximum confidence](https://openreview.net/forum?id=Hkg4TI9xl) ranks confidence for error detection. |
| Increment, decision and endpoint | Does changing the accepted label add accuracy at the same coverage? Four OULAD outcomes at day 60. Original contract targets worst-course selective risk at equal budget. Decomposition is descriptive. |
| Original registered endpoint and threshold | `aurc`, minimum effect 0.02, designated control `C2_CRC_CONFORMAL`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | Confidence-only argmax and rerouting got 350 of the same 552 accepted cases right. In the day-zero follow-up, the covariate-augmented selector's worst-course error was **1.30 points higher** than the confidence-and-margin control (95% CI .55–2.08). |
| External validity and separate contribution | Later OULAD term tests time shift. Three-class Portuguese enrollment data test the mechanism with another institution and target. Exchanging the frozen confidence cutoffs moves acceptance materially in both directions. Bounded diagnostic paper about who is scored. [Matched replay](coverage/manuscript.md) · [Cutoff exchange](coverage/threshold_transfer/results.json) |

### P03 tutoring

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [MRBench](https://aclanthology.org/2025.naacl-long.57/) and the [BEA shared task](https://aclanthology.org/2025.bea-1.77/) assess responses on pedagogical dimensions. |
| Increment, decision and endpoint | Choose a response after a math prompt. Endpoint is a released fully-guiding judgment on the selected answer, with a two-point margin for pairwise switching. |
| Original registered endpoint and threshold | `expert_rubric_win_rate`, minimum effect 0.1, designated control `C2_CHAIN_OF_THOUGHT`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | The training-selected fixed tutor reached 238/300. Four refitted published DLSU graders achieved 198–209. Gated pairwise selection returned exactly the fixed tutor, and ungated selection achieved 231. |
| External validity and separate contribution | Prompt-disjoint folds; Bridge/MathDial source transfer stays inside MRBench. A tie between training tutors reversed a transfer conclusion. A response-selection benchmark can study selection instability. Tutor improvement and learning gains remain untested. [Decisions](tutoring/pairwise/README.md) |

### P04 curriculum shift

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [Rienties and Toetenel](https://doi.org/10.1016/j.chb.2016.02.074) mapped learning design and student behavior across 151 modules. Their unit is a module rather than a labeled revision between offerings. [WILDS](https://proceedings.mlr.press/v139/koh21a.html) benchmarks group/domain shift with held-out domains. [OULAD](https://doi.org/10.1038/sdata.2017.171) supplies dated activity and assessment inventories. These sources do not supply a reference set of pedagogically consequential revision events. |
| Increment, decision and endpoint | After two consecutive offerings, recover documented changes at a false-discovery limit .10, with AP gain .05 and improved recall. |
| Original registered endpoint and threshold | `spearman_rho`, minimum effect 0.05, designated control `C2_GENERIC_OOD`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | Weekly quizzes gave AP .50 against inventory 1.00, two positive edges out of 15. The one count-preserving weight change ranked ninth versus first for raw clicks and full activity. |
| External validity and separate contribution | Same university and shared modules. Independent Odin edits change the target to a path-derived repository label. Perfect holdout path agreement reconstructs the labeling rule. There is insufficient evidence for a general drift detector. [Revision test](curriculum_shift/revisions/README.md) · [Label provenance](curriculum_shift/path_labels/README.md) |

### Cross-course dropout companion

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [Realinho et al.](https://doi.org/10.3390/app13084702) predict Portuguese dropout and academic success at different academic phases. |
| Increment, decision and endpoint | Predict after the first semester in a previously unseen course. Primary outcome excludes still-enrolled students. Compare equal-course mean log loss under nested tuning. |
| Strongest matched comparison | Splines .487, CatBoost .453, XGBoost .500. The CatBoost loss and uncertainty against XGBoost both matter. In one course, 180/215 learners had zero registered first-semester units, a value absent from the training courses. |
| External validity and separate contribution | A refit on 10,228 eligible UK registrations reversed the point ordering; institution, date, features and target changed together. Supports a benchmark on support shift. It cannot attribute the reversal to country. [Manuscript](dropout/manuscript.md) |

### P05 knowledge tracing

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [DKT](https://papers.nips.cc/paper/5654-deep-knowledge-tracing), [simpleKT](https://pykt.org/simplekt) and [attention-based forgetting](https://ojs.aaai.org/index.php/AAAI/article/view/34998) model next-response correctness using earlier interactions. |
| Increment, decision and endpoint | Incremental learner-weighted NLL for history beyond matched short-history/count/clock features, before the next response. Required gain .015 nats with uncertainty on two datasets. |
| Original registered endpoint and threshold | `nll`, minimum effect 0.015, designated control `C2_LEFOKT`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | ASSIST2015 gain over the matched short blend .000137 [−.000078,.000352]. In EdNet development the temporal model beat executed simpleKT by .04463 but **lost .00055** to the clock-only tree. The cited AAAI family is a relevant unexecuted comparator. |
| External validity and separate contribution | Different educational platforms, item systems and split roles. Matched ablations answer whether extra history helps inside each design. A universal forgetting mechanism remains unestablished. [ASSIST](knowledge_tracing/manuscript.md) · [EdNet](knowledge_tracing/published_simplekt/README.md) |

### Learner-recall companion

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [Settles and Meeder](https://aclanthology.org/P16-1174/) use Duolingo practice histories and estimated half-life to forecast recall. |
| Increment, decision and endpoint | Before a review, compare forecasts on unseen learners using equally learner-weighted log loss and calibrated author HLR. Margin .005 nats. |
| Strongest matched comparison | Primary gain .00389 [.00198,.00593]. On additional learners the gain over log-feature weighted logistic was .00255 [.00192,.00321]. Additional same-release wins against HLR cannot replace the primary contrast. |
| External validity and separate contribution | Different learners, same platform and historical review schedule. Anki source/schema audit did not yield matched frozen predictions. Viable as a bounded replication about calibration and comparator choice. [Manuscript](recall/manuscript.md) · [Transfer feasibility](recall/transfer_design/README.md) |

### P06 capacity and fairness

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [FA*IR](https://doi.org/10.1145/3132847.3132938) enforces representation throughout ranked prefixes; [Wu et al.](https://doi.org/10.1371/journal.pone.0352867) audit educational alerts at fixed volume. |
| Increment, decision and endpoint | With fixed risk scores and seats, can a policy increase worst-group recall while giving up at most one precision point? Review decisions are hypothetical. |
| Original registered endpoint and threshold | `worst_group_recall`, minimum effect 0.03, designated control `C2_UAI24_FAIR_OPT`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | OULAD tied the point-threshold control. Quotas won on the Portuguese holdout. On development CatBoost scores, even outcome-aware allocation preserving both within-group orders could capture only 185/201 required cases on OULAD and 101/104 in Portugal. |
| External validity and separate contribution | Two institutions and different outcome definitions. The lower bound concerns feasible replacements for these scores. Its contrast with a policy question is empirically testable without observing treatment benefits. [Held-out decisions](allocation/manuscript.md) · [Exact frontier](allocation/precision_frontier/README.md) |

### P11 rater prediction

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [Bulian et al.](https://github.com/google-research-datasets/answer-equivalence-dataset) collect intermediate judgments for answer equivalence; [Wulczyn et al.](https://doi.org/10.1145/3038912.3052591) release attack judgments. |
| Increment, decision and endpoint | Given one archived rating, predict the next rating. Does preserving the subtype or reasoning path improve item-weighted Brier loss beyond the first binary vote? Separately, a third IELTS instructor's analytic-score MAE has a .05-point margin. |
| Original registered endpoint and threshold | `krippendorff_alpha`, minimum effect 0.08, designated control `C2_STANFORD_SHEG_RUBRIC`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | Wikipedia test Brier .10894103 versus .11045548 with binary votes. Against dev-tuned smoothing the difference was −.00000010 [−.00000160,.00000140]. IELTS gating gained .000071 over ungated. |
| External validity and separate contribution | 23,001 held-out Wikipedia revisions independently test the **representation/estimation procedure**, refitted for the new task. No shared label semantics with answer equivalence. Evidence supports preserving richer judgments. A superior shrinkage rule or better history rubric remains unproven. [Reader study](rater_agreement/manuscript.md) · [Cross-source test](rater_agreement/panel_transfer/README.md) |

### P13 federated prediction

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [FedAvg](https://proceedings.mlr.press/v54/mcmahan17a.html), [FedProx](https://arxiv.org/abs/1812.06127) and [FedMD](https://arxiv.org/abs/1910.03581) address cross-client training or heterogeneous models. These papers use other tasks. |
| Increment, decision and endpoint | Does sharing improve day-60 withdrawal ranking after strong local adaptation? Seven OULAD modules, equal-module AUC, required gain .02 and positive simultaneous lower bound against all controls. |
| Original registered endpoint and threshold | `roc_auc`, minimum effect 0.02, designated control `C2_TIME_WINDOW_GBDT`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | Regularized adaptation trails weak ridge by .00588. A later ranking gate beat FedAvg by .04140 and trailed fixed neural half-transfer by .00250 [−.00582,.00081]. Even perfect hindsight choices among five weights could gain only .00628 over half-transfer on this roster. |
| External validity and separate contribution | Seven simulated clients at **one** university, repeated development evaluation. Numerical parity with pooled ridge and a smaller logical payload answer an optimization question. Applying the frozen equations to a separate MOOC stream with 3,755 eligible learners yielded AUC .50087 for Newton and .66516 for averaged local models. This is a cross-source score test with a proxy exit label. Multi-institution FL training, privacy guarantees and physical communication costs remain open. [Frozen transfer](landmark/federated/frozen_transfer/README.md) [FL manuscript](landmark/federated/manuscript.md) · [Weight comparison](landmark/federated/rank_gate/README.md) |


## Evidence retrieval, accessibility and computational studies

### P02 exact replanning

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | The [Connection Scan Algorithm](https://arxiv.org/abs/1703.05997) computes timetable journeys. [Dynamic shortest paths](https://doi.org/10.1006/jagm.1996.0046) reuse unaffected solutions. |
| Increment, decision and endpoint | Return a full exact path after a known trip cancellation. Require 10% lower batch p95 and geometric-mean latency before and after charging setup. |
| Original registered endpoint and threshold | `p95_latency_ms`, minimum effect 10.0, designated control `C2_OR_TOOLS_B_AND_B`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | Compare against indexed chronological scan, signature-only repair and matched signature indexing. Memoized reconstruction slowed amortized geometric-mean latency relative to signature-only on both Boston workloads in both runs. |
| External validity and separate contribution | Two request patterns on one MBTA timetable. The witness verifier checks correctness on that projection. Useful result on when repeated starts repay indexing; general network speedup unproven. [Timings and witnesses](replanning/route_memo/README.md) |

### P07 media rights

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | The [Europeana Data Model](https://pro.europeana.eu/page/edm-documentation) distinguishes a supplied object, aggregation and web resource. [RightsStatements.org](https://rightsstatements.org/en/documentation/usage_guidelines) defines declarations. |
| Increment, decision and endpoint | Can an object-level or link-based proxy recover an image declaration at selection time? Spec endpoint is rights-valid nDCG at fixed budget with zero false permissions. Local tests measure declaration matching or masked-field Brier loss. |
| Original registered endpoint and threshold | `rights_valid_ndcg10`, minimum effect 0.04, designated control `C2_RIGHTS_AWARE_ILP`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | One published Europeana object contradicts propagation. Direct resource lookup matches 3/3 sets, propagation 1/3, two sets empty. On Met masked fields, plain two-order donors beat compatibility-weighted donors (.12918 vs .13473 loss). |
| External validity and separate contribution | Different publishers expose different declarations. A counterexample identifies a failure of a rule; one resolved object supplies no error rate for the population. Source declarations alone do not measure legal permission or relevance. Metadata audit only. [External resource comparison](media_rights/web_resources/README.md) · [Masked-field controls](media_rights/imputation/README.md) |

### P08 reward ledger

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [Idempotent API design](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) already handles repeated requests using caller-supplied identifiers and atomic operations. |
| Increment, decision and endpoint | At retry/replay time, does the proposed ledger preserve safety under the specified failures at less operating cost than an ordinary transactional ledger? |
| Original registered endpoint and threshold | `unauthorized_award_rate`, minimum effect 0.0, designated control `C2_STANDARD_IDEMPOTENT_LEDGER`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | The relevant control is a transactional ledger with idempotency keys on the identical concurrent workload. The fixture archive does not contain this empirical head-to-head. No measured numerical margin is available. |
| External validity and separate contribution | No external retry workload or deployment comparison. Engineering invariant and paper-level cost advantage require different evidence. Keep this contract outside the qualifying count. [Fixture evidence](../../research_artifacts_v3/runs/p08/evaluation_results.json) |

### P09 claim verification

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [Schuster et al.](https://aclanthology.org/D19-1341/) use symmetric FEVER, [VitaminC](https://aclanthology.org/2021.naacl-main.52/) uses real revision contrast sets, and [global consistency repair](https://aclanthology.org/2026.emnlp-main.364/) already exploits relations between claims. |
| Increment, decision and endpoint | At inference, hold verifier scores fixed and vary access to neighboring test items. Accuracy on isolated versus linked cases measures the advantage from the information available to the decoder. Confirmatory decoder requires ≥1 point and corrected uncertainty against all controls. |
| Original registered endpoint and threshold | `grounded_answer_f1`, minimum effect 0.05, designated control `C2_AVERITEC_RERANKER`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | Individual BART 617/712, joint decoder 704/712. A residualized threshold tied counts on six FEVER contrasts. On 1,335 VitaminC examples the paired stack got 1,230 right against **1,232** for the paired uniform ensemble. |
| External validity and separate contribution | Two benchmark sources, including author-trained VitaminC scores. External transfer concerns batch-context effects; neither benchmark supplies Vietnamese historical grounding. Evaluation-protocol finding remains distinct from proposing a better verifier. [Paper and controls](claim_only/manuscript.md) |

### P09 sentence retrieval companion

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [Wadden et al.](https://aclanthology.org/2020.emnlp-main.609/) evaluate scientific claims, rationale retrieval and verification in SciFact. |
| Increment, decision and endpoint | Given the annotated document, rank its evidence sentences using a learned positional prior. Primary endpoint MRR, positive simultaneous lower bound against every matched positional and lexical control. No registered practical MRR margin. |
| Original registered endpoint and threshold | `grounded_answer_f1`, minimum effect 0.05, designated control `C2_AVERITEC_RERANKER`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | MRR .78624 vs lexical .70085, but **.77009 for matched later-first**. Gain .01615 [−.01102,.04567]. No established increment from learning the prior. |
| External validity and separate contribution | 129 pairs from the official **training** release, with documents disjoint internally. This serves as an internal mechanism test. Transfer to another corpus requires running the frozen settings with comparable evidence annotations. [All ranks and raw contrasts](archival_retrieval/evidence_sentences/position/README.md) |

### P10 curriculum planning, historical evidence

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [Balanced academic curriculum problem revisited](https://doi.org/10.1007/s10732-011-9158-2) already treats precedence and load. |
| Increment, decision and endpoint | At request arrival, can screening change end-to-end service time at identical correctness and resolution? Target ≥10% against every matched solver. |
| Original registered endpoint and threshold | `mean_correction_seconds`, minimum effect 15.0, designated control `C2_EXACT_DAG_PLANNER`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | 234 fewer integer searches, yet only .90% mean time saved over precedence-narrowed control [−3.91%,7.55%]. Subsequent probing cost 7.33% more service time than matched interval screening. Counts cannot substitute for elapsed time. |
| External validity and separate contribution | 14 held-out benchmark curricula and simulated requests, with no teacher correction outcomes. Archived negative comparison. This line is closed to further experiments by owner direction. [Frozen comparison](curriculum_plan/term_requests/confirmation/README.md) · [Measured service time](curriculum_plan/term_requests/probe_service/README.md) |

### Set cover companion

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [Caprara, Fischetti and Toth](https://doi.org/10.1287/opre.47.5.730) publish a Lagrangian heuristic for weighted set cover. |
| Increment, decision and endpoint | Can multicolumn repair lower feasible cover cost at the same five-second incumbent deadline on new matrices? Registered relative gain 1%. |
| Strongest matched comparison | Single-drop repair limited gain to .957%, CFT achieved lower average cost. Different-effort SetCoverPy results describe budget sensitivity and cannot replace equal-time comparisons. |
| External validity and separate contribution | Multiple OR-Library families, one benchmark lineage. Feasible witnesses establish cost on the instances. Classroom planning quality remains unmeasured. [Equal-budget results](set_cover/equal_budget/summary.json) |

### P12 catalogue revisions and citation relocation

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [Buneman et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC5687090/) describe citations to database subsets; [W3C selectors](https://www.w3.org/TR/annotation-model/#selectors) specify text-position and quotation anchoring. |
| Increment, decision and endpoint | After a revision, how many field-change alerts correspond to changed cited strings? Can a heading with a persistent reference be relocated without observing its ID? Report exact matches; the archival contract requires locator-correct support at bounded false support. |
| Original registered endpoint and threshold | `tamper_detection_rate`, minimum effect 0.0, designated control `C2_MERKLE_LOG_AUDIT`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | With no changed paths in 185 observed page–path pairs, silence ties exact-path monitoring. Among renamed headings, global assignment recovered 19/21 PEP and 12/13 Sphinx, versus 20/21 and 12/13 for independent assignment with identical scores. Body overlap alone recovered 13/13 Sphinx. |
| External validity and separate contribution | Two independently maintained documentation histories, few eligible renames. Tate revisions test strings, not changing historical support. A benchmark of ID-preserving edits is supportable if failures and censoring are included. [Tate](catalog_revisions/manuscript.md) · [Matched assignment](catalog_revisions/lineage/reciprocal/README.md) |

### P14 accessibility

| Comparison question | Evidence |
|---|---|
| Closest verified work and task | [Vigo et al.](https://doi.org/10.1145/2461121.2461124) benchmark automated tools; the [W3C implementation reports](https://www.w3.org/WAI/standards-guidelines/act/implementations/) align tools with ACT fixtures. |
| Increment, decision and endpoint | After engine execution, can combining outcomes improve exact rule-macro accuracy? Gain must be positive and pass adjusted sign tests against all matched controls. |
| Original registered endpoint and threshold | `semantic_accessibility_recall`, minimum effect 0.05, designated control `C2_AXE_PLUS_LLM`. [Original claim register](../release/WIN_CLAIMS_LEDGER.csv) |
| Strongest matched comparison | Additive fusion .6703 vs naive Bayes .6486, adjusted p=.549. Adding pairwise terms reduced accuracy to .5911 on the same 605 examples. Missing engine results are part of the denominator. |
| External validity and separate contribution | Held-out rule IDs within W3C; same public corpus reused for the pairwise follow-up. VizWiz caption availability measures another target. A report about engine disagreement is possible; semantic accessibility for heritage learners remains unmeasured. [Pairwise fusion](accessibility/conditional_rules/README.md) · [Caption audit](accessibility/semantic/README.md) |


### External validation by scientific question

The sources must identify the same observable question before a cross-source number can support generalization. The UK–Portugal exchange estimates coverage under a foreign decision threshold using locally fitted classifiers. In the shared next-response analysis, ASSIST and EdNet both forecast the next observed answer. Among events with at least 32 earlier answers, the gain against the strongest control was .00014 nats on ASSIST and −.00233 on EdNet. Both intervals include zero. The features added to the base models differ. This is evidence about the pattern under two implementations. A frozen-model transfer estimate requires compatible features and item semantics. [Cross-source event and history audit](knowledge_tracing/history_attribution/README.md)

The P11 Wikipedia evaluation supplies a distinct community and annotation task: preserving a reader's extra responses improves prediction of another released judgment on both archives. The pooled results supply no estimate across universities, course schedules or evaluator populations. P13's client-resampling and course-deletion analyses cannot supply those units. For the administrative delay question in paper 1, only an independently sourced dated registration cohort with a corresponding contact-eligibility rule could test the same operational reversal. [Wikipedia test](rater_agreement/panel_transfer/README.md) · [FL sensitivity](landmark/federated/client_sensitivity/macro_auc.csv)

Scope of the literature comparison: primary sources and the portfolio's published comparator implementations were inspected for overlap in data, decision information, metric and evaluation unit. Some contracts have only adjacent published work and normative specifications. An absent matched study in this table does not establish priority. The dates and ranks in the [venue assessment](VENUES.md) address potential audiences separately from this evidence.
