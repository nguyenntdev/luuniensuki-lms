# Intervening skills and elapsed time in EdNet response prediction

Returning to a skill after a break exposes two kinds of information. The clock gives the age of an observation, while the intervening attempts show what else the learner practised. A high count of unrelated attempts can signal learner persistence even when the elapsed time is short. Practice selection on the platform also affects both quantities. We tested their predictive contribution by supplying them separately and together to matched trees, then comparing each tree and its attention-model blend. Earlier KT models already study recency, forgetting and cross-skill effects. The study tests the incremental benefit on a specified trace without claiming the first use of these features. [EdNet dataset and original paper](https://github.com/riiid/ednet) · [Self-Attentive Knowledge Tracing](https://arxiv.org/abs/1907.06837) · [pyKT upstream attention implementation](https://github.com/pykt-team/pykt-toolkit/blob/ccbaf37b07e3e7ff7b2415475b2faacb967d54ea/pykt/models/sakt.py) · [Frozen design](protocol.md)

The response label compares the released submitted option with the answer in the publisher's question table. The forecast uses the currently presented question and strictly earlier, completed bundles for that learner. Presentation timestamps can differ across questions in a single solving ID. Predicting all questions from the information available when that bundle first appears prevents a sibling answer from entering another question's predictors. For earlier bundles we conservatively wait until every presentation time plus its released elapsed time is in the past. Other ways of reconstructing availability could produce a different eligible history. The true moment at which an instructor would have received feedback was unobserved.

Each learner contributes at most their first 160 ordered rows. We drop a bundle if the cutoff splits any of its questions. Full earlier histories up to the cutoff supply the tree summaries. The upstream attention model sees at most 16 preceding responses, with one fixed, primary tag per question and the actual history length for its batch. The attention-only comparison therefore differs in information as well as model class. The matched blend comparisons hold the attention component fixed. Within completed simultaneous history events the original row number resolves positional ties. Predictions describe the adaptive practice stream under an early-trace horizon. Their NLL is specific to this target and cohort. [Feature construction](prepare.py) · [Fitting, ablations and cluster intervals](screen.py)

## Development screen

**Elapsed time accounted for the observed improvement.** Among 8,981 development-screen responses from 240 learners, the clock tree scored 0.57663 NLL, the combined tree 0.57718, and upstream SAKT 0.62932. The full candidate's paired gain over the clock tree was -0.00055 nats, with simultaneous 95% interval [-0.00285, 0.00181]. Tuning chose zero SAKT weight for every blend and epoch four for the standalone checkpoint. The resulting candidate exactly reproduced the combined tree's forecasts. Only the SAKT-alone comparison cleared the .015 margin. This screen contributes zero qualifying papers. [Scores, weights and intervals](run/result.json) · [Source audit](run/verification.json)

| Time since latest eligible practice | Screen responses | Clock tree NLL | With interference |
|---|---:|---:|---:|
| Under one hour | 8,448 | 0.57474 | 0.57536 |
| One hour to under one day | 273 | 0.59147 | 0.59268 |
| At least one day | 260 | 0.62226 | 0.62001 |

The RTX 4060 Ti fit used 56,259 responses from 1,456 training learners and 8,025 from 226 separate tuning learners. An independent reader checked the source-answer labels and strict availability cutoff for every screening prediction, all 80,829 forecasts’ aggregate losses and the four blend equations. A second implementation recovered all eight learner-bootstrap intervals from the released scores. The reserved learner records remained compressed. [Interval check](check_intervals.py)

## Data and reproduction

Only the first 32 MiB of the original KT1 ZIP are needed. Range support and a checksum make this prefix independently retrievable; the incomplete final member plays no role. Archive order is a convenience sample. Reserved learner ZIP entries are skipped before decompression. Use the README's Google Drive release IDs and verify both the prefix and question metadata. The EdNet data are licensed CC BY-NC 4.0. The saved development forecasts identify learners by the publisher's pseudonymous file stem. [Publisher documentation and licence](https://github.com/riiid/ednet#license) · [Pinned input hashes](input.sha256)

From the repository root use Python 3.12 with NumPy, pandas, PyArrow, scikit-learn, CatBoost 1.2.8 and CUDA-enabled PyTorch 2.6.0. The separate verifier requires Node.js and unzip. Keep training artifacts and source files under the ignored raw directory. Transfer the prepared cache and upstream modules to the GPU host preserving the paths below, or execute the two stages on one appropriately configured machine.

```bash
set -eu
e=research_v4_2/external/knowledge_tracing/temporal
r=private_data/raw/ednet/temporal
mkdir -p "$r/upstream"
u=https://drive.usercontent.google.com/download
curl -fLsS --retry 3 --range 0-33554431 "$u?id=1AmGcOs5U31wIIqvthn9ARqJMrMTFTcaw&export=download&confirm=t&study=32mb" -o "$r/KT1.prefix"
curl -fLsS --retry 3 "$u?id=117aYJAWG3GU48suS66NPaB82HwFj6xWS&export=download&confirm=t&study=meta" -o "$r/contents.zip"
base=https://raw.githubusercontent.com/pykt-team/pykt-toolkit/ccbaf37b07e3e7ff7b2415475b2faacb967d54ea/pykt/models
for mod in sakt utils; do curl -fLsS "$base/$mod.py" -o "$r/upstream/$mod.py"; done
pins=$PWD/$e/input.sha256
(cd "$r" && sha256sum -c "$pins")
(cd "$e" && sha256sum -c protocol.sha256)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=1
python "$e/prepare.py" "$r" "$r/cache"
out=$(mktemp -d)
python "$e/screen.py" "$r" "$out"
node --check "$e/verify.mjs"
node "$e/verify.mjs" "$r" "$out"
python "$e/check_intervals.py" "$out"
```
