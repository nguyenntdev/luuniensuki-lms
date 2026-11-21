# Do the letters chosen on earlier questions predict the next answer?

On 8,981 development responses from 240 EdNet learners, adding which wrong option was selected yielded the lowest micro log loss among the 17 saved prediction columns. Its loss of .576231 improved by .000397 over the strongest clock-only control (simultaneous 95% interval −.002111 to .002890). The gain over the matched four-lag correctness model was .001631 (−.000519 to .003959). Nine of 16 contrasts cleared the frozen .015-nat and positive-lower-bound requirements. Some archived models have identical predictions. This screen supports a small observed gain and leaves practical superiority and population equivalence open. [Frozen design](protocol.md) · [All comparisons](run/result.json)

Both fits used CatBoost on an RTX 4060 Ti. Every lag comes from a previously completed bundle. A prior answer without a recorded letter uses the missing category in both models, as does missing history. The four lag fields contained 31, 31, 22 and 21 blank values across the training and screening table. The full candidate retained a/b/c/d on recorded wrong responses, whereas the matched control pooled them. These are choice-position categories across questions. They do not identify which misconception a learner held. The reserved learner buckets remained outside feature preparation and scoring.

Use the [EdNet source and preparation commands](../temporal/README.md). After creating the parent cache, run the following from the repository root. Run the fit on a CUDA host with CatBoost. Transfer the derived train/screen table to that host and return the estimates to the indicated path for local scoring. GPU fitting can introduce numerical variation. CPU rescoring of the archived forecasts is deterministic.

```sh
set -eu
d=research_v4_2/external/knowledge_tracing/distractors
r=private_data/raw/ednet/temporal
(cd "$d" && sha256sum -c protocol.sha256)
python "$d/features.py" "$r" "$r/cache/choice_lags.csv.gz"
python "$d/train.py" "$r/cache/choice_lags.csv.gz" "$d/run/estimates.csv.gz"
OPENBLAS_NUM_THREADS=1 python "$d/score.py" "$d"
```
