# External studies and publication fit

Assessed 21 November 2026. The most developed comparisons are the learner-recall replication, the day-60 withdrawal audit and the nested cross-course dropout benchmark. Each has a defensible, bounded result. The recall comparison missed its practical margin, the withdrawal study has a close published precedent, and the spline missed its joint superiority criterion. The current [ten-method audit](TEN_METHODS.md) records zero strong wins against every required comparator.

## Venue ranks and submission formats

Ranks below come from the **ICORE 2026** conference list. Formats come from the indicated organizers' calls and are examples from those editions. They describe plausible submission routes for future editions. A parent conference's rank does not establish a rank for a colocated workshop.

| Conference | Rank source | Relevant edition and format |
|---|---|---|
| Learning Analytics and Knowledge (LAK) | [ICORE 2026 A](https://portal.core.edu.au/conf-ranks/2268/) | LAK26 short research paper, up to ten single-column pages including references. The reviewers explicitly ask what a replication adds to knowledge. [Submission guidelines](https://www.solaresearch.org/events/lak/lak26/submission-guidelines/) · [Reviewer guidelines](https://www.solaresearch.org/events/lak/lak26/reviewer-guidelines/) |
| Educational Data Mining (EDM) | [ICORE 2026 B](https://portal.core.edu.au/conf-ranks/446/) | Potential audience for the recall replication and the withdrawal risk-set audit. Check the edition-specific track and dates before submission. |
| Artificial Intelligence in Education (AIED) | [ICORE 2026 A](https://portal.core.edu.au/conf-ranks/1961/) | AIED 2026 full or short research papers in technical, human and societal tracks. The technical track fits offline models of learning and tutoring. [General call](https://aied-conference.org/2026/call-for-paper) |
| Empirical Methods in Natural Language Processing (EMNLP) | [ICORE 2026 A*](https://portal.core.edu.au/conf-ranks/448/) | EMNLP 2026 main conference short paper. The call explicitly welcomes negative findings and reproduction studies alongside original empirical work. [Main conference call](https://2026.emnlp.org/calls/main_conference_papers/) |
| ACM SIGACCESS Conference on Computers and Accessibility (ASSETS) | [ICORE 2026 A](https://portal.core.edu.au/conf-ranks/2258/) | ASSETS 2026 short technical paper, 4,000–5,000 words excluding references. The impact on accessibility must be evident. [Technical papers call](https://assets26.sigaccess.org/technical_papers.html) |
| Theory and Practice of Digital Libraries (TPDL) | [ICORE 2026 B](https://portal.core.edu.au/conf-ranks/2013/) | TPDL 2026 short and late-breaking results, eight pages plus references. Metadata, curation, provenance and citation are named topics. [Call](https://tpdl2026.ualg.pt/call-for-papers/) |
| ACM Conference on Information and Knowledge Management (CIKM) | [ICORE 2026 A](https://portal.core.edu.au/conf-ranks/25/) | CIKM 2026 resource papers fit a released, reusable data-management benchmark. A local analysis of existing downloads alone has limited value for this track. [Resource call](https://cikm2026.diag.uniroma1.it/resource-papers/) |
| Symposium on Experimental Algorithms (SEA) | [ICORE 2026 B](https://portal.core.edu.au/conf-ranks/1378/) | SEA 2025 research papers on algorithm engineering and experimental evaluation. [Call](https://regindex.github.io/sea2025.github.io/call_for_papers.html) |
| Principles and Practice of Constraint Programming (CP) | [ICORE 2026 A](https://portal.core.edu.au/conf-ranks/1175/) | CP 2026 application track asks how constraint programming helps solve a real problem. A binary integer-programming certificate alone offers little evidence for this track. [Call](https://cp2026.a4cp.org/cfp.html) |

## Initial study assessments

The following assessment records the evidence available before the follow-up experiments. For current results and readiness, see the [updated study index](README.md).

### Learner recall — AIED technical short paper

**Executed.** The authors' half-life regression (HLR) code and CatBoost both received learner-disjoint tuning and recalibration on Duolingo traces. On 360 held-out learners, boosting gained 0.00389 nats per learner (95% interval 0.00198–0.00593). The point estimate missed the stated 0.005 practical margin. The model comparison changes the original HLR split and metric. [Local protocol and run](recall/manuscript.md) · [Settles and Meeder, ACL 2016](https://aclanthology.org/P16-1174/) · [Author implementation](https://github.com/duolingo/halflife-regression/tree/0041df0dcd436bf1b4aa7a17a020d9c670db70d8)

**Contribution and next evidence.** A calibrated, learner-weighted comparison against the original implementation makes a plausible replication paper. HLR already models practice history and time since review. Explain the unusually small HLR calibration slope (0.0071) by reporting raw and calibrated distributions by lag and item frequency, checking the author configuration at full training size, and repeating the contrast on another cohort. A scheduling claim would additionally require observing retention under competing schedules.

### Day-60 withdrawal risk — LAK short research paper

**Executed.** On the 2014J OULAD holdout, the same CatBoost scores yielded AUC 0.834 across 11,249 registrations and 0.623 among the 8,815 still eligible for intervention. Logistic regression showed a similar gap. The local run also refitted on eligible students. A 2026 *Computers* paper already contrasts landmark and all-registered OULAD estimands, including a day-56 analysis. Its target and features differ, and its pipeline was not rerun here. [Local design and run](landmark/manuscript.md) · [Published OULAD landmark comparison](https://www.mdpi.com/2073-431X/15/9/560)

**Contribution and next evidence.** The estimated size of the day-60 gap under fixed scores and learner exclusion is the transferable question. A claim to introduce the risk-set distinction would duplicate prior work. Reproduce the published target at its original horizon, then vary target, horizon and eligibility one at a time. Independent dated withdrawals would show whether the gap recurs in a second institution.

### Cross-course dropout — LAK short research paper

**Executed.** Seventeen held-out courses supplied paired losses for additive logistic splines, CatBoost and XGBoost under equal tuning budgets. Mean course loss was 0.487, 0.453 and 0.500 respectively. The spline lost to CatBoost and its advantage over XGBoost was uncertain. Both published boosting families actually ran. Realinho et al. already published phased predictions of dropout and academic performance on this educational setting. Their multiclass pipeline was not reproduced under the local binary resolved-outcome definition. [Local comparison](dropout/manuscript.md) · [CatBoost](https://proceedings.neurips.cc/paper_files/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html) · [XGBoost](https://doi.org/10.1145/2939672.2939785) · [Realinho et al., 2023](https://www.mdpi.com/2076-3417/13/8/4702)

**Contribution and next evidence.** The distinctive evidence concerns transfer to an unseen course and sensitivity to the choice of boosting baseline. Reconcile the published three-class target with exclusion of unresolved students, show which course-level calibration failures account for the paired loss differences, and repeat with an independent institution before generalizing portability.

### Selective course-outcome prediction — LAK short research paper

**Executed.** A replay of archived four-class OULAD predictions compared the gate, unrestricted logistic regression, logistic labels on the gate's exact cases and two confidence-based selectors. On the temporal split the gate got 675 of 1,167 accepted cases right, versus 761 for logistic on those same IDs. The learner-group split had a two-case deficit. The archive includes training registrations from the latest presentation. Published confidence ranking motivates the selectors. A 2026 OULAD withdrawal paper already reports selective prediction for a different, binary outcome. Neither publication's pipeline was rerun. [Local replay](coverage/manuscript.md) · [Hendrycks and Gimpel, ICLR 2017](https://openreview.net/forum?id=Hkg4TI9xl) · [Published OULAD selective prediction](https://doi.org/10.1371/journal.pone.0352867)

**Contribution and next evidence.** The paired counts identify how often a label change hurts after conditioning on acceptance. Establish a strictly future-presentation holdout, estimate risk across coverage levels with uncertainty by learner or course, and test whether the same-case deficit persists. An operator study or observed referral costs would be needed to value deferral.

### Fixed-budget allocation — LAK short research paper

**Executed.** For the Portuguese dropout cohort, logistic and gradient-boosting scores fed two policies at the same course capacity. The proportional policy exchanged 60 of 357 logistic-ranked slots and reduced worst-group recall from 24.0% to 16.4%. Capacity was hypothetical and no contact outcome was recorded. FA*IR enforces protected representation across ranking prefixes. The local largest-remainder quota at final capacity is a different policy. [Local allocations](allocation/manuscript.md) · [Zehlike et al., CIKM 2017](https://doi.org/10.1145/3132847.3132938)

**Contribution and next evidence.** A numerical example of representation and recall diverging adds little algorithmic novelty. Compare FA*IR and an opportunity-oriented rule on identical out-of-course scores, plot case capture against representation across feasible budgets, and obtain practitioner evidence for the capacity and objective. This direction shares students and dropout labels with the cross-course study. A combined decision-policy section is credible until there is independent allocation evidence.

### Mathematics tutor selection — AIED technical short paper

**Executed.** The training-selected fixed tutor earned a full guidance label on 46 of 52 held-out conversations, versus 38 for the lexical logistic response selector. The held-out set contained 34 opening-prompt groups. All responses and labels came from a shared-task archive. MRBench introduced the pedagogical taxonomy, and BEA participants already trained assessors for these responses. Neither their systems nor live tutors were run locally. Their three-class macro-F1 measures annotation prediction, while the local outcome is the guidance rate of the single selected response. [Local decisions](tutoring/manuscript.md) · [MRBench, NAACL 2025](https://aclanthology.org/2025.naacl-long.57/) · [BEA 2025 shared-task findings](https://aclanthology.org/2025.bea-1.77/)

**Contribution and next evidence.** A fixed-tutor control is inexpensive and reveals how much a selector gains from tutor identity. Use a published assessor to rank the same six candidates, ablate identity and response text separately, then repeat with held-out generator families and fresh rubric judgments. Claims about learning require learner outcomes.

### Claim-only verification — EMNLP main conference short replication

**Executed.** On 19,998 FEVER development cases, unigram/bigram logistic regression reached 52.47% versus 33.33% for majority prediction. An enumeration of contradictory labels for identical strings gives a deterministic ceiling of 356/712 on FEVER Symmetric v0.2. No evidence-aware system ran. Schuster et al. had already demonstrated claim-only artifacts and designed the symmetric challenge to break them. The ceiling follows from inspecting the released pairs. [Local models and certificate](claim_only/manuscript.md) · [FEVER](https://aclanthology.org/N18-1074/) · [Schuster et al., EMNLP-IJCNLP 2019](https://aclanthology.org/D19-1341/)

**Contribution and next evidence.** The certificate makes a strong evaluation control, with little standalone novelty. A stronger short paper would pair the control with an evidence-aware verifier on identical examples, intervene on the evidence, and show where the distinction changes conclusions on an independently annotated corpus. Claims about Vietnamese historical sources require a licensed, expert-labeled heritage test set.

### Catalog revisions — TPDL short paper, with CIKM resource potential

**Executed.** Comparing two Tate snapshots by stable ID found 4,243 changed records among 69,201. Of 270,420 nonempty potential field citations, file-level, record-level and field-level policies flagged 270,420, 16,503 and 4,285 respectively. The last count matches the definition of a changed cited string. These are potential references. The evaluator did not observe actual citations or editorial judgments. The RDA already specifies versioned, query-level citation, and Buneman et al. develop citation at database subset granularity. Neither system was executed. [Local counts](catalog_revisions/result.json) · [RDA recommendations](https://doi.org/10.15497/RDA00016) · [Buneman et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC5687090/)

**Contribution and next evidence.** A Tate-specific workload estimate fits a curation note. Sample real citations, have curators label changes that alter their meaning, measure missed consequential changes as well as unnecessary alerts, and repeat over additional providers and revisions. A released revision benchmark with these labels and stable retrieval instructions would make the CIKM resource route plausible.

### Museum media rights — TPDL short paper, with CIKM resource potential

**Executed.** A metadata census counted 58,415 Tate thumbnail links, including 14,239 with copyright notices. Six Smithsonian FSG shards contained 179 image entries with explicit CC0 designations. The evaluator counted fields and made no independent determination of permission for each asset. RightsStatements.org already publishes an object-level vocabulary and technical requirements for machine-readable rights. A populated notice and a CC0 grant have different meanings. [Local counts](media_rights/result.json) · [RightsStatements.org technical white paper](https://rightsstatements.org/files/180117requirements_for_the_technical_infrastructure_for_standardized_international_rights_statements_v1.2.1.pdf) · [Usage guidelines](https://rightsstatements.org/en/documentation/usage_guidelines)

**Contribution and next evidence.** Useful as a data-quality case study. Define a concrete reuse task and compare record-level inference with explicit per-media evidence and an abstain option. Curators should adjudicate cases including missing, ambiguous and conflicting terms. Report coverage and false authorizations across providers. A redistributable benchmark could contain references and judgments even where images cannot be included.

### Accessibility rule execution — ASSETS short technical paper

**Executed.** axe-core 4.11.0 in Chromium evaluated five ACT rule mappings. Across 83 fixtures, all 35 expected passes and 30 expected failures agreed. Of 18 expected inapplicable examples, 11 agreed, three returned pass, one was incomplete and three were unexecuted. These outcomes concern the local example harness. W3C already hosts Deque's axe implementation report, and Vigo et al. benchmarked multiple accessibility tools against expert judgments. The local run used one engine. [Local fixture results](accessibility/result.json) · [W3C-hosted vendor report](https://www.w3.org/WAI/standards-guidelines/act/implementations/axe-core/) · [Vigo et al., W4A 2013](https://ro.ecu.edu.au/ecuworks2013/236/)

**Contribution and next evidence.** First reproduce each discrepancy with the vendor's own version, configuration and target-element semantics. Then test whether confirmed differences affect assistive-technology users on real course tasks. Until then the result supports a harness regression report. It cannot quantify the accessibility of the LMS or a learner's ability to complete a task.

### Weighted set cover — SEA experimental paper or CP application study

**Executed.** On ten OR-Library set 4 instances, weighted greedy, greedy plus reverse deletion and certified HiGHS integer programming gave summed costs of 5,695, 5,282 and 5,100. Every pruned plan remained above the optimum. The local greedy run implements Chvátal's rule. The stronger Caprara–Fischetti–Toth heuristic combines pricing, subgradient optimization and column fixing and was not executed. [Local witnesses](set_cover/result.json) · [Chvátal, 1979](https://doi.org/10.1287/moor.4.3.233) · [Caprara et al., 1999](https://doi.org/10.1287/opre.47.5.730) · [OR-Library](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/scpinfo.html)

**Contribution and next evidence.** The 69.4% of aggregate excess cost removed is a reproducible diagnostic on one family. A competitive SEA paper needs several instance families, a strong heuristic under equal time limits and an explanation of when deletion helps. For CP, first demonstrate a real planning problem with interacting constraints such as timing or precedence, implement a CP formulation and compare feasible plans and bounds against integer programming on that problem.

The [closest-work tables](COMPETITION.md) supersede the initial novelty assessment. The [withdrawal manuscript](landmark/manuscript.md) now reproduces the day-84 capacity benchmark and tests two rankings on an independent MOOC release. A LAK (A) or EDM (B) measurement submission would center the contribution on how status availability changes queue value, the limits of what missing predictions identify, and the mechanism that did or did not transfer. The reported ranks describe these venues. Acceptance likelihood and current deadlines have not been estimated.
