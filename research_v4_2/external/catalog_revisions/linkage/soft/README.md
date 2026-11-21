# Does token order recover displaced bibliographic fields?

The revised matcher reached 96.970% positive-class F1 on Dirty DBLP–ACM and 93.787% on Dirty DBLP–Google Scholar. It gained 0.259 and 3.666 percentage points over the original exact-token candidate. A matched model using ordered title prefixes but omitting the cross-field assignment features was within 0.007 and 0.057 percentage points. Both margins fell below the original one-point development criterion. The official test releases remain unopened. [Development design](design.md) · [Per-method counts and paired contrasts](run/summary.json)

## Motivation and related work

DeepMatcher creates its dirty bibliographic records by moving attribute values into the title. A title can therefore contain a genuine title prefix followed by a venue or author names. On the preceding candidate's training-file calibration subset, ACM had 13 false positives and one false negative. Google Scholar had 83 and 39. Inspection found pairs sharing author names and topic phrases despite different titles, encoded diacritics and near-identical records with negative labels. These examples motivated testing whether matching two title prefixes in order distinguishes an intact title from incidental overlap. Each pair retains its released label. [DeepMatcher, SIGMOD 2018 and accompanying appendix](https://pages.cs.wisc.edu/~anhai/papers1/deepmatcher-sigmod18.pdf)

Approximate token matching and ordered alignment are established techniques. Cohen, Ravikumar and Fienberg compare hybrid TFIDF and Jaro–Winkler scores. Monge and Elkan study local string alignment for field matching. We ask the narrower empirical question of whether token order and field destinations each add value for titles with appended material. We ran TeamCohen's SoftTFIDF Java implementation at commit 44d67bb2c8af8e03c963717ce4c799ab051583ca. It greedily selects nonoverlapping approximate token matches at its default 0.9 Jaro–Winkler cutoff. The adapter supplies normalized flattened records, learns document frequencies from distinct flattened fitting records, and calibrates one decision threshold. We did not use the scores reported on the authors' different tasks. [Cohen et al.](https://www.cs.cmu.edu/~wcohen/postscript/ijcai-ws-2003.pdf) · [SecondString implementation](https://github.com/TeamCohen/secondstring/blob/44d67bb2c8af8e03c963717ce4c799ab051583ca/src/com/wcohen/ss/SoftTFIDF.java) · [Monge and Elkan, KDD 1996](https://www.aaai.org/Papers/KDD/1996/KDD96-044.pdf)

## Comparison

We first decode HTML entities, casefold text, strip combining marks, and tokenize each field into alphanumeric words. The character control extends the original model with edit similarities for each aligned field and the flattened record. The flattened soft-token model adds maximum-weight one-to-one token assignment across both entire records. Its edge weight multiplies Jaro–Winkler similarity of at least 0.9 by the smaller of the two tokens' training-fit IDF weights. A field-resolved variant also reports the resulting matched mass in all 16 source–destination combinations, normalized in each direction. These added features identify where tokens went while preserving the same assignment.

The ordered component computes a weighted longest common subsequence over the two title token lists using the same approximate token weights. It scores each pair of prefixes by twice the matched mass divided by their combined mass, then discounts low-support prefixes by a factor of 1 − exp(−matched mass / 15). Five features measure the best prefix and full-title alignment. The smoothing constant was fixed during method design. All new supervised rows share the earlier candidate features, fitting partition, booster settings and training-file-only threshold search. Validation files had been used in the first screen. [Implementation](extract.py) · [Fitting and threshold selection](evaluate.py)

| Method (F1, %) | DBLP–ACM | DBLP–Google Scholar |
|---|---:|---:|
| Original exact-token candidate | 96.711 | 90.122 |
| Published SoftTFIDF, flattened | 91.323 | 86.063 |
| Add character similarities to original | 96.597 | 92.221 |
| Also add flattened soft assignment | 96.567 | 91.979 |
| Flattened model plus field-resolved assignment | 96.567 | 92.787 |
| Flattened model plus ordered title prefixes | 96.963 | 93.730 |
| Flattened model plus both | **96.970** | **93.787** |

Against ordered prefixes alone, adding field destinations corrected one ACM decision and broke another. On Google Scholar it corrected 12 and broke 10. The full model produced 15 false positives and 12 false negatives on ACM, and 84 and 51 on Google Scholar. Relative to the original exact-token candidate on Google Scholar, it corrected 113 decisions and broke 29. The positive title-prefix result fits the benchmark's construction. Real catalogue citations can truncate, paraphrase or reorder titles differently. The reused development files and recurring bibliographic records limit inference. Ditto and DeepMatcher were not trained in this screen. This comparison contributes zero qualifying papers. [ACM decisions](run/DBLP-ACM.csv) · [Google Scholar decisions](run/DBLP-GoogleScholar.csv)

## Reproduction

Use the four SHA-256-checked inputs from the [original reproduction instructions](../README.md#reproduction). The run used OpenJDK 17, RapidFuzz 3.14.3, NumPy 2.4.4, SciPy 1.17.1, pandas 3.0.2 and scikit-learn 1.8.0. The shell script fetches pinned SecondString source, compiles the upstream Java scorer, regenerates features and forecasts, verifies all source pair hashes, confusion counts, saved probability decisions and paired contrasts, and compares the products byte for byte.

```bash
study=research_v4_2/external/catalog_revisions/linkage
bash "$study/soft/reproduce.sh" "$(mktemp -d)"
```
