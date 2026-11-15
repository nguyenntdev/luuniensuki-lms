# External data acquisition, rights and scientific compatibility

**Strict gate:** no dataset may be marked DOWNLOADED, LICENSED or USABLE merely because a public URL is present. First fetch the original official terms, save the terms and exact file checksum, and have a reviewer confirm allowed academic uses and derivative/redistribution rights.

| Source | Best use | Known / check before use | URL |
|---|---|---|---|
| ASSISTments | KT, partial concept mapping, temporal labels | select a year/version; platform schema differs; check dataset-specific terms | https://sites.google.com/site/assistmentsdata/datasets |
| Junyi | KT and learning activity sequencing | verify upstream canonical version, license, concept graph and time column semantics | https://www.kaggle.com/datasets/junyiacademy/learning-activity-public-dataset |
| EdNet | KT + session time | upstream states CC BY-NC 4.0; commercial reuse forbidden; dataset huge, stream with deterministic subset policy | https://github.com/riiid/ednet |
| OULAD | risk ranking, SRL behavior proxies | observational; click logs are NOT interventions or measured SRL | https://research.stem.open.ac.uk/ouanalyse/dataset/ |
| CausalEdu | conditional causal graph / treatment analysis | inspect available CATE labels, dataset split, license and task fit; A/B dataset is math, NOT heritage learning gain | https://github.com/Eedi/CausalEdu |
| MOOCCubeX | activities, concepts, course graphs | licensing and data fields require direct verification; graph not necessarily alternative pedagogic providers | https://github.com/THU-KEG/MOOCCubeX |
| MathTutorBench | LLM tutor pedagogy | benchmark may combine components with distinct licenses; check subdataset terms and keep math vs heritage results separate | https://eth-lre.github.io/mathtutorbench/ |
| BEA tasks | tutoring/student reasoning | track exact year/task, terms and splits; don't conflate different BEA tasks | https://sig-edu.org/sharedtask/2025 |
| Europeana | heritage metadata, affordance tasks | metadata generally reusable under CC0 policy; object media and Europeana providers have item-level rights | https://pro.europeana.eu/page/apis |
| Smithsonian Open Access | rights-cleared object metadata/media | only items specifically marked open access/CC0; some record metadata available with media withheld | https://www.si.edu/openaccess/devtools |
| Wikidata | provenance graph linking | data CC0 generally; source statements require independent factual review | https://www.wikidata.org/wiki/Wikidata:Data_access |
| Huế historical sources | primary claims, local curriculum, archival photos | permission and page-level citations must be checked item-by-item; treat sources as unlicensed until approved | https://www.hueworldheritage.org.vn/ |

## Pipeline A00–A09 per source
- A00: open authoritative dataset page and capture terms/date/DOI/version.
- A01: legal-use matrix: academic analysis, derived artifacts, text/media copying, commercial use, redistribution, fine-tuning, third-party APIs.
- A02: download to `private_data/raw/<provider>/<version>/` outside Git; record SHA-256, byte size, provenance.
- A03: schema audit (IDs, timestamps, concept labels, missingness, duplicate records, leakage fields).
- A04: normalized adapter with deterministic unit tests + reference row transformation examples.
- A05: deidentification and re-identification risk review; release only aggregated or license-permitted examples.
- A06: preregister learner/course/time/skill splits; materialize train/calibration/dev/frozen test once, hash each.
- A07: leakage scan: future information, metadata-derived labels, duplicate sources, shared learners across domains.
- A08: datasheet/model card/representation risks, bias and subgroup coverage.
- A09: signed dataset release card; if any item fails, mark `BLOCKED`, never silently substitute synthetic cases.

## Annotation / human evidence pipeline
- Ethics and age-appropriate school permissions BEFORE collecting real student/teacher data.
- Two independent raters + predefined codebook + blinded sample; disagreement adjudicated with timestamps and original decisions preserved.
- Record Krippendorff α or suitable weighted κ/ICC only where assumptions apply. No fabricated annotator IDs or 'expert consensus'.
- For museum media, annotate task affordances (inscription, shape, source context, audio transcript, alt text) and rights separately.
- For human learning outcomes: design a controlled pre/post measure, not survey satisfaction or programmatic policy correctness.

## Data manifest sample
See `09_REFERENCE/DATASET_REGISTRY_TEMPLATE.yaml`. Before running a study, every `required_for_primary_claim` dataset must have `status: APPROVED` and a verifiable SHA.
