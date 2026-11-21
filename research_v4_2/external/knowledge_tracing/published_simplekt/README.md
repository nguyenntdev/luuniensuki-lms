# P05 comparison with published simpleKT on EdNet

On 8,981 next-question predictions for 240 development learners, simpleKT with item difficulty achieved **.62181 nats per answer**. The previously fitted joint temporal predictor achieved **.57718**. Its paired gain over simpleKT was .04463 nats (simultaneous 95% learner-bootstrap interval .02934–.06354), clearing the .015-nat margin. The clock-only tree scored **.57663**. Adding intervening-skill features therefore missed the same margin against the strongest measured control. Three of the four comparisons in this follow-up cleared the development rule. This addresses one of the published comparators requested by P05. The full contract also requests stronger temporal comparators, a second dataset and confirmation. [P05 specification](../../../../LUU_NIEN_RESEARCH_V4_2_NOVELTY_WIN_CONTRACT_20261116/03_PAPERS/P05_NOVELTY_AND_WIN_METHOD.md) · [Paired contrasts](run/result.json) · [Earlier eight controls](../temporal/README.md)

| Method | NLL per answer | Correct at threshold .5 |
|---|---:|---:|
| Clock-only tree | .57663 | 6,233 |
| Joint temporal predictor | .57718 | 6,248 |
| simpleKT with item difficulty | .62181 | 5,861 |
| simpleKT using skills alone | .62912 | 5,835 |
| SAKT | .62932 | 5,829 |

We ran Liu et al.’s unchanged pyKT implementation using the EdNet first-tag concept, original question ID and previous correct/incorrect responses. The upstream model estimates a question-specific difficulty vector. Its matched ablation uses the same code with item difficulty disabled. Both fits used a single RTX 4060 Ti. Different model sizes and optimization trajectories limit any architectural inference. Training and checkpoint selection covered 1,456 and 226 disjoint learners. Both neural comparators see the last sixteen available practice events. Trees also see earlier history summaries, current question and elapsed time. The experiment compares prediction procedures under a common information cutoff. [Original paper](https://arxiv.org/abs/2302.06881) · [Pinned simpleKT implementation](https://github.com/pykt-team/pykt-toolkit/blob/ccbaf37b07e3e7ff7b2415475b2faacb967d54ea/pykt/models/simplekt.py) · [Training details](run/fit.json)

A prior solving bundle becomes eligible only after all of its questions have completed strictly before the current bundle starts. The item reconstruction checked every stored skill and outcome in the input windows against the raw release. Both simpleKT variants gave identical output on every development example when the current-response placeholder was switched from zero to one. The independent JavaScript replay rebuilt source membership and labels, compared the existing model columns, and checked all 240 learner loss sums and all 44,905 threshold decisions. All models in the table were evaluated on the same development answers. The original study's tuning selected zero weight on SAKT for both the clock and joint trees. [Source replay](run/verification.json) · [Learner sums](run/learner_sums.csv) · [Design](protocol.md)

## Reproduction

Acquire EdNet and the upstream utilities and build the cache using the [earlier reproduction instructions](../temporal/README.md). Run from the repository root. Use the frozen earlier predictions under temporal/run. The GPU needs only the prepared simplekt.npz and the two pinned upstream modules under the paths shown. Copy its fit output back under cache/simplekt_fit for CPU scoring.

```bash
set -eu
d=research_v4_2/external/knowledge_tracing/published_simplekt
r=private_data/raw/ednet/temporal
base=https://raw.githubusercontent.com/pykt-team/pykt-toolkit/ccbaf37b07e3e7ff7b2415475b2faacb967d54ea/pykt/models
curl -fsSL "$base/simplekt.py" -o "$r/upstream/simplekt.py"
sha256sum -c "$d/source.sha256"
(cd "$d" && sha256sum -c design.sha256)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
python "$d/prepare_items.py" "$r" "$r/cache/simplekt.npz"
# CUDA host
python "$d/fit.py" "$r" "$r/cache/simplekt_fit"
# CPU scoring
out=$(mktemp -d)
python "$d/score.py" "$r" "$d/../temporal/run" "$out"
node --check "$d/verify.mjs"
node "$d/verify.mjs" "$r" "$out"
```
