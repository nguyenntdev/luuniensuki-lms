# Does the P05 advantage persist in longer histories on another platform?

Among responses with at least 32 eligible earlier answers, ASSIST2015's full blend gained **0.00014 nats per answer** over its strongest archived control, the blend without streaks. On EdNet KT1, the joint temporal predictor **lost 0.00233 nats per answer** to the strongest control in that stratum, the clock tree. Both simultaneous intervals include zero. Neither cohort cleared the frozen 0.015-nat margin against its strongest control. The sources share a next-response endpoint, but the feature additions differ. This is evidence about two locally fitted predictors and their respective ablations. Exact feature replication and frozen-model transfer remain untested. [Design](protocol.md) · [Complete scores](run/result.json)

## Matched contrasts

A positive gain favors the candidate. Counts refer to responses and contributing learners. Learners can appear in several history bins. The intervals are learner-cluster percentile intervals with a Bonferroni correction across 98 predeclared comparisons. They condition on the archived fits and evaluation cohorts.

| Source | Eligible prior answers | Responses | Learners | Correct | Repeated current skill | Gain over the matched control, nats [simultaneous 95% interval] |
|---|---:|---:|---:|---:|---:|---:|
| ASSIST2015 | All | 134,640 | 3,818 | 98,733 | 113,676 | +0.000137 [−0.000163, +0.000418] |
| ASSIST2015 | 1–16 | 47,307 | 3,818 | 35,432 | 38,828 | +0.000035 [−0.000347, +0.000416] |
| ASSIST2015 | 17–31 | 26,513 | 2,174 | 19,698 | 21,917 | +0.000312 [−0.000295, +0.000849] |
| ASSIST2015 | 32+ | 60,820 | 1,388 | 43,603 | 52,931 | +0.000139 [−0.000391, +0.000642] |
| EdNet KT1 | All | 8,981 | 240 | 5,274 | 3,925 | −0.000554 [−0.003570, +0.002445] |
| EdNet KT1 | 1–16 | 2,579 | 240 | 1,203 | 537 | +0.000376 [−0.004037, +0.004747] |
| EdNet KT1 | 17–31 | 1,387 | 110 | 705 | 258 | +0.004129 [−0.003591, +0.012125] |
| EdNet KT1 | 32+ | 5,015 | 67 | 3,366 | 3,130 | −0.002328 [−0.006610, +0.002361] |

The gain at 32+ minus the gain at 1–16 was +0.000103 nats on ASSIST [−0.000534, +0.000711] and −0.002704 on EdNet [−0.008749, +0.003324]. This comparison uses the same resampled learners across bins within a source. It describes how the observed gain changes with the amount of available history under that platform's selection policy. It leaves the effect of extending access to earlier answers unidentified. The EdNet long bin contains 56% of its screen responses from only 67 of 240 learners. The wide intervals reflect learner-level variation. The most extreme simultaneous quantiles are approximated by about five draws per tail per contrast. None of the decisions about the strongest controls is close to the practical threshold. [Full intervals and counts](run/result.json)

### What the stronger controls explain

- **ASSIST.** At 32+, the full blend improved over DKT by .004030 nats [.002543, .005532], while the matched control recovered about 97% of that point gain. Both blends gave DKT a weight of .5. Both trees had full eligible-prefix counts and last-skill response features. The extra predictors were the current same-skill run length and correct/incorrect streaks. The tree-only comparison gained .000544 nats [−.000583, .001581] at 32+. Each tree selected its leaf budget separately on development data. The comparison estimates the incremental value of these predictors under that tuning rule. [ASSIST manuscript](../manuscript.md) · [Development selection](../run/development.json)
- **EdNet.** At 32+, the joint predictor improved over SAKT by .064016 nats [.027510, .119442] and over item-aware simpleKT by .057002 [.024943, .106290]. Both neural models used the last sixteen eligible answers. The clock and joint trees used full available history summaries, current item and measured times. The joint predictor added intervening practice features to the clock tree. Tuning assigned zero attention weight to all four blends, so the tree and corresponding blend forecasts coincide. The clock tree was the strongest control at 32+ (.550553 versus .552881). The option-lag tree was strongest overall (.576231 versus .577183), a candidate gain of −.000952 nats [−.004555, +.002424]. In the 17–31 bin the joint tree ties its candidate blend by construction, and the best distinct forecasts come from the clock tree and its duplicate blend. [Temporal study](../temporal/README.md) · [simpleKT](../published_simplekt/README.md) · [Option lags](../distractors/README.md)
- All seven ASSIST models and seventeen EdNet models remain in the machine-readable results, including controls that outperform the candidate and the coincident forecast columns. The P05 comparator register also includes BKT, HawkesKT, DKT-Forget, FoLiBi, AKT, DTransformer, LêFoKT and a separate recency-aware KT baseline. None has an aligned forecast ledger here. Item-aware and skill-only simpleKT are available for this EdNet screen only. Published scores from other splits or protocols provide context. [P05 comparator register](../../../../LUU_NIEN_RESEARCH_V4_2_NOVELTY_WIN_CONTRACT_20261116/03_PAPERS/P05_NOVELTY_AND_WIN_METHOD.md) · [All observed losses](run/result.json)

## What is comparable across releases?

| Dimension | ASSIST2015 | EdNet KT1 |
|---|---|---|
| Platform and cohort | ASSISTments mathematics skill builders, pyKT official held-out learners | Santa TOEIC practice, development hash buckets 70–79 from the first 2,500 complete learner members in ZIP order |
| Label and cutoff | Released binary response at step `t`, using the skill at `t` and the ordered prefix through `t−1` | Submitted option equals the publisher answer key. Prediction at first presentation of the current bundle, using only bundles whose latest presentation plus elapsed time is strictly earlier |
| Depth and identifiers | Count all prior released responses. Key is learner ID and step. Concept IDs are local to ASSIST. This split has no item ID or timestamps. | Count eligible completed-bundle responses among the first 160 chronological rows, dropping bundles split by the cap. Key is learner file stem and original zero-based row. Item ID and first tag come from the question catalog. |
| Increment beyond the strong match | Contiguous same-skill practice and correctness streaks | Count and correctness since the last same primary skill, recent same-part/different-skill practice and skill switches |
| Split and training | Dataset-local fitting with a separate tuning fold and released test learners | Dataset-local fitting and tuning on separate learners. Development forecasts are reused by several studies. Reserved buckets 80–99 remained compressed. |

The shared endpoint is natural-log loss conditional on reaching an observed opportunity with at least one eligible prior response. Raw NLL levels reflect different prevalence, available predictors and practice selection policies. Count bins align the number of observable answers. They leave the duration, item mix and nature of prior practice different. At 32+, the same skill had appeared earlier on 87.0% of ASSIST events and 62.4% of EdNet events. ASSIST streaks exploit contiguous skill-builder practice. EdNet's joint terms include practice in other skills and rely on an estimated completion cutoff. The negative point gain on EdNet concerns these EdNet features. It cannot decide how the ASSIST streak ablation would behave there. A cross-platform weight transfer would also need a shared feature definition and skill/item mapping, plus archived target forecasts from an unchanged source model. A test of added history access would need forecasts that vary the available history window while holding the model and features fixed. [ASSIST publisher](https://sites.google.com/site/assistmentsdata/datasets/2015-assistments-skill-builder-data) · [Pinned pyKT release](https://github.com/pykt-team/pykt-toolkit/tree/ccbaf37b07e3e7ff7b2415475b2faacb967d54ea) · [EdNet publisher](https://github.com/riiid/ednet) · [EdNet paper](https://doi.org/10.1007/978-3-030-52240-7_13)

## Closest published comparisons

| Work | Prediction, information and evaluation | What this evidence adds |
|---|---|---|
| Knowledge Tracing Machines | Factorization machines model learner, item, skill and prior outcome counts for correctness prediction. The ASSIST2009 experiment reports AUC and compares factorization against simpler feature models. | Prior counts are established inputs. This archive measures run and streak increments in NLL above a DKT blend already using counts, on a different release. [Vie and Kashima](https://arxiv.org/abs/1811.03388) |
| stableKT | Trains on shorter histories and tests attention at longer sequence lengths on Algebra 2005–06, Bridge to Algebra 2006–07 and NIPS34. Reports response-prediction AUC. | Closest length-generalization comparator. Our strata sort on observed eligible depth after local fitting, with no input-horizon intervention. There are no stableKT forecasts on these events. [Li et al.](https://www.ijcai.org/proceedings/2024/0654.pdf) |
| LêFoKT | Relative forgetting attention and position encoding are compared on Algebra 2005–06, Bridge to Algebra 2006–07 and NIPS34. The paper reports AUC and accuracy and includes longer-sequence extrapolation. | Its ablations directly overlap the forgetting and length questions. Nothing in the saved ledgers ranks it on the before-bundle EdNet endpoint. [Bai et al.](https://ojs.aaai.org/index.php/AAAI/article/download/34998/37153) |
| HawkesKT | Models time-sensitive cross-skill effects of earlier responses. The upstream evaluation includes timestamped ASSISTments 2009–10. | Closest mechanistic competitor for the EdNet interference question. The clock-tree ablation asks a related question under the local before-bundle cutoff. Item/timing parity is unavailable in the pinned ASSIST2015 sequence files. [Wang et al. implementation and paper](https://github.com/THUwangcy/HawkesKT) |
| simpleKT | Predicts correctness with item-specific difficulty and attention. The paper benchmarks AUC across seven public datasets. | The EdNet archive supplies a direct comparison on every screen response under the same decision cutoff, while using different history representations. On the shared NLL endpoint the locally fitted clock control is stronger. [Liu et al.](https://arxiv.org/abs/2302.06881) · [Local replay](../published_simplekt/README.md) |

The result supports a limited, practical conclusion across the two releases. Adding richer history features did not reach a .015-nat gain over the closest strong controls on longer observed histories. The tested feature additions differ, the EdNet cohort is a reused development screen, and the intervals leave the direction of the smaller effects uncertain. This analysis supplies no two-dataset strong win or novelty clearance.

## Reproduction and audit

Use the raw inputs and pinned parent forecast ledgers listed in [inputs.sha256](inputs.sha256). The parent studies document [ASSIST downloads](../manuscript.md#reproduction), [EdNet downloads](../temporal/README.md#data-and-reproduction), and the [upstream simpleKT pin](../published_simplekt/README.md#reproduction). Use Python 3.12 with NumPy, pandas, PyTorch and scikit-learn, and Node.js with unzip for the independent parent checks. Run from the repository root in a shell restricted to CPU cores 24–33. All commands below prepare inputs or score saved predictions. EdNet data carry the publisher's CC BY-NC 4.0 licence. The new result contains only aggregate statistics.

```bash
set -eu
export CUDA_VISIBLE_DEVICES= OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
d=research_v4_2/external/knowledge_tracing
h=$d/history_attribution
a=private_data/raw/assist2015
r=private_data/raw/ednet/temporal
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
(cd "$h" && sha256sum -c protocol.sha256)
sha256sum -c "$h/inputs.sha256"
python "$d/temporal/prepare.py" "$r" "$out/cache"
ln -s "$PWD/$r/KT1.prefix" "$PWD/$r/contents.zip" "$out/"
python "$d/published_simplekt/prepare_items.py" "$out" "$out/cache/simplekt.npz"
python "$h/score.py" "$out/cache" "$out/result.json"
cmp "$out/result.json" "$h/run/result.json"
node "$d/verify.mjs" "$a" "$d/run"
node "$d/published_simplekt/verify.mjs" "$r" "$d/published_simplekt/run"
python -m pytest -q tests/research_v4_2 "$d/test_history.py"
```

The scorer checks exact release coverage and correctness for 143,621 events and aligns 1,095,157 archived forecasts. Independent prefix slices verify ASSIST's input features for every scored event. EdNet completion histories are independently reconstructed for each screen event. The audit checks item and skill IDs, labels, history counts, delays, recency and interference summaries, sixteen-event neural windows and training-only item support. The freshly reconstructed EdNet feature table and windows also matched the existing feature cache. The parent Node verifiers replay source labels and blend equations. The supplementary control models are rescored from their saved probabilities. Model fitting itself is outside this audit. [Source audit](source.py) · [Scorer](score.py)
