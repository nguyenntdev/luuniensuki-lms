# P04 datasheet — CurriculumShiftBench data sources (P04-T02/T04)

Frozen: 2026-11-15. Every hash below was recomputed from `private_data/raw/…`
on the authoring machine and matches `provenance.json` written at download time.

## 1. oulad-2013-2014 — APPROVED for academic benchmark use

| Field | Value |
|---|---|
| Provider | Open University (distributed via UCI ML Repository, dataset 349) |
| Source URL | https://archive.ics.uci.edu/static/public/349/open+university+learning+analytics+dataset.zip |
| DOI | 10.1038/sdata.2017.171 (Kuzilek, Hlosta & Zdrahal, 2017, Scientific Data 4:170171) |
| Version | 2013J/2013B/2014J/2014B (32,593 student-module-presentation rows) |
| Archive sha256 | `f2ed1902616c1fe8d2824d872c0b7d2d72be435bf0124d077044fe4be2c6d3e4` |
| License text sha256 | `41003d4a74749c0220e33dd415042164b5a1093ed401f36277234f772d22d3d0` |
| License family | **CC BY-NC 4.0** (captured LICENSE.txt is Attribution-NonCommercial) |
| Allowed uses in P04 | academic_analysis, derived_artifacts (attribution, non-commercial) |
| Prohibited | commercial use; any claim that P04 artifacts are commercially usable |

Per-file sha256 (raw snapshot):

| File | sha256 |
|---|---|
| studentInfo.csv | `815fbc3e2de29f79900bc63f0345a35db62c9146afaa1d86e7107b8b3beffc60` |
| studentVle.csv | `52668253d876c5becbcb72185977152700cecab2942aca807fecc3dd54b937f0` |
| vle.csv | `d7a146497edd0e47ef536144b58796c07b554002d3753e848b8e4cd8a56f4c38` |
| courses.csv | `4f16eee7454b15e109b0a21a0e43be820e6846ed6f9301bb7feb5ab5ad737a75` |
| assessments.csv | `9ce92381e4a0ac457f8e251b2eb2c179ed51e023ab30d1d671a0268bd62316ba` |
| studentAssessment.csv | `b1839e17618a5de36b6d189a242d3123f7939a56c8c9ccef0c17b9199c614a6b` |

Use in P04: (a) scenario source — course shift (7 modules), presentation/time
shift (22 presentations), demographic subgroup strata; (b) ontology bridge
source — `vle.csv` activity types are REAL VLE resource categories (20 distinct)
that anchor the canonical skill ontology; the NOT_APPLICABLE stratum is grounded
in the fact that course AAA exposes no resource whose activity type falls in the
`assessment` canonical category.

## 2. uci-student-performance-2014 — APPROVED

| Field | Value |
|---|---|
| Provider | P. Cortez & A. Silva (2008), UCI ML Repository, dataset 320 |
| Source URL | https://archive.ics.uci.edu/static/public/320/student+performance.zip |
| DOI | 10.24432/C5TG7T |
| Version | 2014 (student-mat.csv 395 rows; student-por.csv 649 rows) |
| Archive sha256 | `82ae9d66437b9808df42e8c89d2bb179c46e9cfbcf06f38abc1d20b3b747e177` |
| License text sha256 | `9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411` |
| License family | **CC BY 4.0** |
| Allowed uses | academic_analysis, derived_artifacts, redistribution (attribution) |

Use in P04: second domain for cross-domain shift strata (school shift; mat→por
subject shift). Labels are G3 grades; G1/G2 are excluded from features for the
pass/fail target as recorded in the registry leakage audit.

## 3. BLOCKED sources (exact terms checked 2026-11-15)

| Source | Status | Exact reason |
|---|---|---|
| ASSISTments (https://sites.google.com/site/assistmentsdata/datasets) | BLOCKED | Dataset-specific terms not yet reviewed; version selection and signed license capture pending (registry `assistments: BLOCKED`). P04 downloads nothing. |
| Junyi Academy (https://www.kaggle.com/datasets/junyiacademy/learning-activity-public-dataset) | BLOCKED | Kaggle Terms of Use not captured/hash-pinned; no local snapshot; redistribution rights unverified. |
| EdNet (https://github.com/riiid/ednet) | BLOCKED | CC BY-NC forbids commercial use and redistribution of derivatives; no deterministic subset policy approved. |
| Europeana / HUE heritage corpus | BLOCKED | Out of P04 scope (no task labels). |

## 4. Consequence for external generalization

P04 runs its frozen strata on OULAD (primary) and UCI student-performance
(secondary domain). With the third platform (ASSISTments/Junyi/EdNet) blocked,
P04 **must disclose**: "external generalization beyond two education datasets
is unverified" in every table caption and the manuscript limitations section
(SCIENTIFIC_EVALUATION.md §5 E11).

## 5. Frozen split manifests

Splits are materialized by `research_v3.methods.p04.bench` through the shared
`research_v3.eval.splitters` and hashed; the hash and partition sizes are
recorded in `research_v3/methods/p04/protocols/p04_splits.json` and must be
reproducible from the raw hashes above. Benchmark authors may not tune on
`test` partitions of any stratum.
