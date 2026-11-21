# Does donor compatibility improve catalogue-flag reconstruction?

For each artificially masked Met declaration, we search the preceding and following eight observed objects under inventory-ID order and again under the full accession string's lexical order. Object ID resolves duplicate accession strings. The donor features use earlier available training labels for records with similar descriptive fields. Within training, each query uses donors from the four other object-hash folds. Development queries use every training object. The binary target is the museum's published object-level flag. The experiment concerns retrospective quality control of structured metadata. Its endpoint omits individual images and rights-holder adjudication. [Source and terms](https://github.com/metmuseum/openaccess/tree/15d35b4b1f7f87baa8d42cc24481f68f76817d20) · [Scientific design](design.md)

A donor at distance rank *r* receives weight 1/√*r*. The compatible rate multiplies this weight by 3 for matching accession family, 4 for artist, 2 each for department and classification, 3 each for object name and medium, and 3 for object end dates within three years. Missing identifiers earn no match bonus. Each rate adds two pseudo-observations at the training donor prevalence. A simple control averages the two compatible rates directly. A learned classifier sees the rates, the total donor weights and the individual matching-field rates. Its matched control sees both plain local rates and their total weights. The preceding GPU global model and CPU neighbour model enter this comparison from their saved object-level forecasts.

The four new CatBoost fits share 350 rounds, depth 6, learning rate .12 and seed 73. Every fit receives the original fields, raw inventory ID, lexical accession position, medium, culture, artist nationality and the first artist's begin and end years. The base classifier receives no donor labels. Adding earlier global-ID window features provides the richer one-order control. These comparisons concern a single fixed configuration. Even a development pass would leave published repair-system comparisons and external repair outcomes to establish. [CatBoost](https://papers.nips.cc/paper_files/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html) · [HoloClean](https://doi.org/10.14778/3137628.3137631) · [MissForest](https://doi.org/10.1093/bioinformatics/btr597)

## Results on the development records

The compatible predictor's log loss was **.13473 nats per object** on 100,875 development objects after fitting 302,046 training objects. It improved over the previous global-window model by .00255 and over the original CPU neighbour model by .00446. Both gains missed the .005 margin. The rich two-order control achieved **.12918**, improving on the compatible predictor by .00555. Two of six comparisons cleared the margin. The independent verifier matched 201,750 prior-control forecasts to their object IDs and recomputed every loss using the source labels. The reserved objects remain unopened. [Results](run/summary.json) · [Verification](run/verification.json)

| Predictor | Mean log loss |
|---|---:|
| Direct compatible neighbour mean | .17451 |
| Rich metadata alone | .14312 |
| Earlier CPU neighbour classifier | .13920 |
| Earlier GPU global-ID windows | .13728 |
| Compatible donors plus both orders | .13473 |
| Rich metadata and global windows | .13140 |
| Rich metadata, global windows and plain two-order donors | **.12918** |

The second ordering reduced loss by .00222 relative to the richer global-ID control. This leaves a gap below .005 even if one provisionally treats the simplest two-order estimator as a future hypothesis. Results are development-screen estimates after earlier Met experiments, with no confirmatory uncertainty inference. They supply no additional qualifying paper.

## Reproduction

Use Python 3.12 with the [portfolio package versions](../../../requirements.txt), CatBoost 1.2.8 with CUDA, and Node. Acquire the pinned Met CSV and run the preceding CPU and ordered-GPU comparisons or use their saved prediction ledgers. Run from the repository root, providing an empty output directory. GPU fitting can vary numerically across runs. The independent verifier compares original source labels, membership, both prior-control forecasts, mean losses and the all-control decision.

```bash
d=research_v4_2/external/media_rights/imputation/donor
r=private_data/raw/met/MetObjects.csv
out=$(mktemp -d)
(cd "$d" && sha256sum -c design.sha256)
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 python "$d/screen.py" "$r" \
    "$d/../ordered/run/dev.csv.gz" "$d/../run/dev.csv.gz" "$out"
node --check "$d/verify.mjs"
node "$d/verify.mjs" "$r" "$out" "$d/../ordered/run/dev.csv.gz" "$d/../run/dev.csv.gz"
```
