# Recovering a masked museum declaration from neighbouring records

The Met development partition contains 100,875 objects, including 52,259 with a positive declaration. The 302,046 training objects supply all labels available to a predictor. A learner can use an object's catalogue ID and accession number at query time. The endpoint is retrospective reconstruction of the publisher's field. [First design](design.md) · [Met dataset and licence](https://github.com/metmuseum/openaccess/tree/15d35b4b1f7f87baa8d42cc24481f68f76817d20)

| Development comparison | Candidate log loss | Strongest control | Gain in nats per object |
|---|---:|---:|---:|
| First screen, CPU, nearest accession/artist records | .13920 | .15601, metadata CatBoost | +.01681 |
| Same screen, GPU, nearest accession/artist records | .15362 | .15927, metadata CatBoost | +.00566 |
| GPU, two-sided inventory-ID and grouped windows | .13778 | .13728, inventory-ID windows | −.00050 |
| Rich metadata with compatibility-weighted donors | .13473 | .12918, plain donors under both orderings | −.00555 |

The first method cleared its .005 development margin against three controls under both CatBoost backends. The fits share a nominal depth, iteration budget and learning rate. CPU and GPU CatBoost have different implementation defaults, so the differences between rows cannot be attributed to floating-point precision alone. Adding the index as a standalone control changed the scientific interpretation. Simply measuring nearby labels on either side of an object ID captured much of the apparent family signal. The full window model lost to its ungrouped counterpart for both the 97,141 objects with training-family support and the 3,734 without. The follow-up using richer metadata and two orderings further reduced absolute loss, with the simpler comparison method leading. [CPU screen](run/summary.json) · [GPU screen](gpu_run/summary.json) · [Ordered method and ablations](ordered/design.md) · [Ordered results by support](ordered/run/verification.json) · [Richer donor analysis](donor/README.md)

An inventory ID can reflect a publisher's batching practices. A syntactic accession prefix can also join many unrelated items. The masked cases sample the same snapshot as the training objects. This design therefore measures interpolation under random masking. On two Minneapolis releases, all 17 initially blank fields in the training partition remained blank. Among 57 observed transitions from a pending to a substantive declaration, only two had an earlier sibling with a substantive label. The real missingness problem remains unresolved. [Independent collection feasibility](transfer/README.md)

## Reproduction

Download the frozen CSV through Git LFS. The evaluator verifies the source digest before computing any features. From the repository root run the commands below with the pinned external Python requirements, using a CUDA-capable CatBoost installation for the GPU fits. Each study writes a separate output directory. The verifier independently checks hash-bucket membership, publisher flags, support counts, losses and gate decisions from saved predictions. GPU retraining can yield different forecasts. The saved predictions support exact score auditing.

```bash
set -eu
e=research_v4_2/external/media_rights/imputation
r=private_data/raw/met/MetObjects.csv
mkdir -p "$(dirname "$r")"
curl -fLsS --retry 3 https://media.githubusercontent.com/media/metmuseum/openaccess/15d35b4b1f7f87baa8d42cc24481f68f76817d20/MetObjects.csv -o "$r"
out=$(mktemp -d)
python "$e/screen.py" "$r" "$out/cpu" --device CPU
python "$e/screen.py" "$r" "$out/gpu" --device GPU
python "$e/ordered/screen.py" "$r" "$out/ordered"
for saved in "$e/run" "$e/gpu_run" "$e/ordered/run"; do
    python "$e/verify.py" "$r" "$saved" | diff - "$saved/verification.json"
done
```
