# External benchmark papers

These manuscripts use labels, revision histories, test expectations or mathematical constraints supplied by external sources. A paper on predictions describes recorded outcomes. A paper on a hypothetical decision describes whom that rule would select. Neither type of study measures the effect of deploying the LMS. The original V4.2 contracts and thresholds remain available in the [release register](../release/V42_TASK_REGISTER.csv). This portfolio changes several original scientific questions to ones answerable with public data.

The current goal is ten distinct proposed methods, with at least three strong wins and the rest equivalent or slightly better than the strongest appropriate controls. The [ten-method audit](TEN_METHODS.md) lists the selected questions, effect sizes and evidence levels. The [per-study comparisons](SUPERIORITY.md) preserve the original thresholds and follow-ups. Venue fit also depends on novelty, the measured endpoint and external validity.

The [fourteen-paper spec crosswalk](SPEC_COVERAGE.md) maps every V3/V4.2 paper to the evidence for its original question and identifies the ML and federated-learning comparisons.

## Manuscripts, results and readiness

The assessment is specific to the contribution and track. A ranked venue appearing in the table is a target, and its rank refers to the conference edition in the [venue and prior-work assessment](VENUES.md). The table includes failed comparisons. Closely related analyses must justify separate contributions.

| Manuscript | What the evidence supports | Publication assessment |
|---|---|---|
| [Withdrawal at the decision date](landmark/manuscript.md) | 63.75% of day-60 withdrawal AUC pairs involve an exited student. Their AUC is .953 versus .623 for pairs available for intervention. Three horizons, two endpoints, two models. | LAK short-paper candidate on the mechanism of the gap. One institution. A prior OULAD paper already compared eligibility definitions. |
| [Calibrated recall prediction](recall/manuscript.md) | CatBoost gained .00389 nats over author HLR in the primary test, missing the .005 margin. Follow-ups cover 9,134 additional learners. Gains depend on comparator choice. | AIED replication candidate. A scheduling or retention intervention claim lies outside the measured endpoint. |
| [Cross-course dropout](dropout/manuscript.md) | Across 17 Portuguese programs the spline lost to CatBoost. On 10,228 eligible UK registrations, a locally refit spline had the lowest mean module loss in a different task. | LAK negative-result candidate. Both published baselines are part of the primary conclusion. |
| [Selecting mathematics tutor responses](tutoring/manuscript.md) | Over 300 conversations the fixed tutor had 238 fully guiding responses, versus 198–209 for four refitted published graders. Two source tutors tied during selection with different transfer outcomes. | AIED benchmark note. The archived rating measures a single rubric dimension. |
| [Selective course-outcome prediction](coverage/manuscript.md) | The historical deficit disappeared on a strictly future holdout. Both methods got 350 of the same 552 OULAD registrations right. | LAK audit. This question concerns label changes under deferral. The landmark paper measures who remains eligible for intervention. |
| [Review allocation under fixed budgets](allocation/manuscript.md) | On university data, FA*IR changed 15 of 357 logistic-ranked slots where final proportional quotas changed 60. On secondary mathematics data, prefix repairs changed the order within the selected set. | LAK decision-policy candidate with two educational datasets. The primary dropout paper concerns probability quality. Review capacity is hypothetical. |
| [Fact verification on contrast sets](claim_only/manuscript.md) | Held-fixed evidence-aware scores give different accuracies under independent and group-constrained inference. VitaminC supplies a second corpus and an author-trained comparator. | EMNLP short replication and benchmark-methodology candidate. The decoder uses knowledge of the benchmark construction. |
| [Weighted set-cover search](set_cover/manuscript.md) | The original ten-instance decomposition is supplemented by 45 instances, seven families and a [published heuristic comparison](set_cover/multifamily/README.md). Ranking changes with search budget. | SEA experimental study. CPU effort differs between methods and superior algorithmic efficiency is unproven. |
| [Catalogue revision alerts](catalog_revisions/manuscript.md) | Three Tate releases show how record- and field-group alerts inflate exact-text review counts. | TPDL curation note. The unit is a possible citation, and a string change is its own reference standard. |
| [Museum image-rights declarations](media_rights/manuscript.md) | Four publishers distinguish catalogue reuse, recorded object status and available media. The Cleveland release has 768 CC0-labelled objects without a web-image URL. | TPDL metadata audit. The labels come from the publishers. Accuracy for legal authorization is unmeasured. |
| [Accessibility rule applicability](accessibility/manuscript.md) | Alfa led QualWeb on exact outcomes, 494 versus 473, across a 527-fixture union. On 455 common exercised cases QualWeb led 439 to 437. | ASSETS technical-note direction. Four published engines now cover 35 rules. The endpoint is fixture performance and excludes downstream user outcomes. |
| [Balanced curriculum scheduling](curriculum_plan/manuscript.md) | Across 448 requests, interval filtering avoided 234 integer searches. Time saving against the precedence-narrowed control was 0.90% (simultaneous interval −3.91% to +7.55%). | Held-out negative comparison. The target speedup and full-resolution requirement were missed. |
| [Federated withdrawal prediction](landmark/federated/manuscript.md) | Six Newton rounds recovered the pooled fit to numerical precision using 1,248 numerical bytes per client. Macro AUC .61587 trailed weak ridge (.63116) and neural half-transfer (.64578). | Reproducible optimization comparison on seven simulated course clients. Evidence for predictive superiority across institutions is missing. |

The [ASSIST2015 knowledge-tracing manuscript](knowledge_tracing/manuscript.md) adds a separately evaluated next-response task. The [anonymous reader-judgment manuscript](rater_agreement/manuscript.md) compares decision paths with binary votes on two question-disjoint releases. The [rater-distribution experiments](rater_agreement/prediction/README.md) cover additional released panel votes.

## Reproducing the primary analyses

Use a Python 3.12 virtual environment on Linux. Commands below start at the repository root. Write new runs to a separate directory so reviewed outputs stay available. Most legacy evaluators use runtime assertions for input checks and should run with Python optimization disabled. The download manifest includes source URLs and SHA-256 hashes. Each named study can be fetched separately. Allocation shares the primary UCI archive with dropout. Coverage replays the frozen V3 files included in the checkout. The museum and ACT manuscripts provide their own versioned acquisition commands.

```bash
set -euo pipefail
E=research_v4_2/external
R=private_data/raw
O=$(mktemp -d)
python3.12 -m venv "$O/venv"
P="$O/venv/bin/python"
"$P" -m pip install -r "$E/requirements.txt"
"$P" "$E/fetch.py" "$R" --study landmark --study dropout --study recall --study tutoring --study claim_only --study set_cover
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
"$P" "$E/landmark/evaluate.py" "$R/oulad/2013-2014/oulad.zip" "$O/landmark"
"$P" "$E/landmark/horizons.py" "$R/oulad/2013-2014/oulad.zip" > "$O/horizons.json"
"$P" "$E/dropout/evaluate.py" "$R/uci/dropout-697/source.zip" "$O/dropout"
"$P" research_v4_2/diagnostics/course_allocation.py "$R/uci/dropout-697/source.zip" > "$O/allocation.json"
"$P" "$E/recall/evaluate.py" "$R/duolingo-hlr/traces.csv.gz" "$R/duolingo-hlr/experiment.py" "$O/recall"
"$P" "$E/tutoring/evaluate.py" "$R/mrbench/mrbench_v3_devset.json" "$O/tutoring"
"$P" "$E/coverage/evaluate.py" research_artifacts_v3/runs/p01 > "$O/coverage.json"
"$P" "$E/claim_only/evaluate.py" "$R/fever" "$O/claim_only"
"$P" "$E/claim_only/symmetric.py" "$R/fever/symmetric_test.jsonl" > "$O/claim_only/symmetric.json"
"$P" "$E/set_cover/evaluate.py" "$R/orlib" > "$O/set_cover.json"
```

The test environment for these eight primary analyses contained only the dependencies installed into a fresh virtual environment. The two catalogue manuscripts report six byte-for-byte comparisons on fresh downloads. The accessibility paper gives separate local-browser and published-report checks. The [allocation replication](allocation/reproduce.md), [set-cover study](set_cover/multifamily/README.md) and each manuscript describe their extensions. [Input catalogue](downloads.json) · [Pinned Python packages](requirements.txt)

## Data use and interpretation

Duolingo distributes its traces under CC BY-NC 4.0. MRBench uses CC BY-SA 4.0 and builds on MathDial and Bridge. The FEVER symmetric and VitaminC releases identify Wikipedia's article terms and a CC BY-SA fallback. Tate's catalogue licence excludes the images it links. Each paper identifies its data creators and source versions. Raw downloads stay in the ignored cache. Reuse of a source or derivatives is subject to its own terms. [Duolingo](https://doi.org/10.7910/DVN/N8XJME) · [MRBench](https://github.com/kaushal0494/UnifyingAITutorEvaluation) · [FEVER Symmetric terms](https://github.com/TalSchuster/FeverSymmetric/blob/fa25d17e73ea0694edc78133ec654b9f32f6db73/DATA_LICENSE) · [VitaminC terms](https://huggingface.co/datasets/tals/vitaminc/blob/be6febb761b0b2807687e61e0b5282e459df2fa0/LICENSE) · [Tate](https://github.com/tategallery/collection#the-tate-collection)
