# Does a local shadow validation set identify beneficial cross-model transfers?

On 8,815 registrations from 8,505 learners in OULAD 2014J, a client-local gate reached macro-course AUC **.62321**. Giving a fixed half weight to transferred predictions reached **.63820** on the same seven modules and same alternating roster of architectures. Local-only prediction reached .62354 and accepting the transfer throughout reached .63364. All four predictions use identical preceding learner partitions, trained networks, and course-specific calibration offsets. The gate selected zero transfer weight in all three risk strata in three courses. It improved on local-only AUC in three courses, lost in one, and tied in three. The estimated macro difference against local-only was −.00033 (simultaneous 95% interval −.00649 to .00582). [Scores and 30 contrasts](run/summary.json) · [Individual course results](run/scores.csv) · [Calibration gates](run/gate.json)

We varied the architecture assigned to each simulated course client, exchanged model outputs on 512 shared synthetic activity profiles, and measured whether held-out earlier learners could identify useful transfers under a later term shift. FedMD introduced cross-architecture consensus distillation. The proposed screen uses a single exchange, deterministic synthetic feature anchors, and a peer-only equal consensus. Each client uploads 512 double-precision scores and receives 512, a combined 8,192 bytes of logical payload per course excluding transport and pre-shared anchor generation. Earlier FedAvg controls exchange parameter vectors with a different number of rounds. No heterogeneous method reads a peer's examples. The centralized models use the concatenated training set as an information-rich reference. The logistic and MLP models read the same four day-60 features. Seven course codes simulate participants inside one university. Learners can take multiple courses. The evaluation conditions on these seven clients, a single fixed assignment and seed. No privacy mechanism or real multi-institution deployment was evaluated. [FedMD](https://arxiv.org/abs/1910.03581) · [FedAvg](https://proceedings.mlr.press/v54/mcmahan17a.html) · [Personalized cross-silo FL](https://arxiv.org/abs/2007.03797) · [Source and earlier controls](../README.md)

The earlier cohort supplies 9,235 fitting learners and 5,981 disjoint calibration learners (6,322 calibration registrations). Entire learners stay in one partition across courses. The gated predictor reuses earlier calibration labels to fit the intercepts and mixture weights. This design can overfit small-course calibration partitions. The gate optimizes calibration log loss, while the prespecified primary endpoint measures course-average AUC. Both facts may contribute to divergence between the selected gate and the fixed mixture; the experiment does not isolate their effects. [Protocol fixed before fitting](protocol.md) · [Implementation](train.py)

The gate's tenth-percentile course AUC was .54289 versus .57272 for fixed half transfer. Weak-ridge adaptation on the same fitting learners reached .63496, while the earlier weak-ridge control trained on all earlier learners reached .63116. The highest macro AUC among recorded controls was .64578 for fixed half transfer with all clients using MLPs. That roster was compared as a prespecified architectural control. The candidate cleared zero of 30 simultaneous comparisons under the .02-AUC decision margin. Several controls make identical rankings because of the monotonic intercept adjustments. These related comparisons are retained in the joint family. The old 2014J cohort was reused for development. [Tail, mean log loss and negative transfer frequency](run/client_metrics.csv) · [Development decisions](run/predictions.csv.gz)

## Reproduction

Generate the deidentified feature matrix with the preceding [OULAD acquisition and preparation](../README.md). Python with CUDA-enabled PyTorch, pandas and the preceding experiment's dependencies is required. Node and unzip are needed for independent checks. All participant fits, offsets and gate selection ran on the RTX 4060 Ti. Scoring verified 273,265 forecasts against released membership and outcomes and recomputed 31 macro AUCs. A separate verifier reselected every calibrated gate weight and checked 52,890 resulting decisions. Its calibration check starts from the deidentified feature table. Source-level registration checks use the pinned archive.

```bash
set -eu
d=research_v4_2/external/landmark/federated/shadow
archive=private_data/raw/oulad/2013-2014/oulad.zip
work=$(mktemp -d)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
(cd "$d" && sha256sum -c protocol.sha256)
python "$d/../prepare.py" "$archive" "$work/input.csv"
# Run with the prepared table on a CUDA host and copy back its run folder.
python "$d/train.py" "$work/input.csv" "$d/../train.py" "$work/run"
python "$d/evaluate.py" "$work/run"
node --check "$d/verify.mjs"
node "$d/../verify.mjs" "$archive" "$work/run"
node "$d/verify.mjs" "$work/input.csv" "$work/run"
```
