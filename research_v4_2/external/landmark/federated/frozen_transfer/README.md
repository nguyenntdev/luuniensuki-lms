# Frozen transfer of the seven-module OULAD fits to the MOOC stream

The federated Newton predictor attained AUROC .50087 on 3,755 eligible MOOC learners at the stream midpoint, versus .65400 for FedAvg, .66516 for the equal-weight average of seven local models, and .66546 for averaged regularized adaptations. The paired Newton-minus-local-average interval was [−.21215, −.11645] using simultaneous adjustment. The strongest individual source equation on this cohort was local DDD at .66803; its identity was learned by looking at destination performance. Few-actions-first, a training-free ranking, reached .65728. The exact optimizer's match to pooled ridge within OULAD provided little guidance about its ranking performance on this new release. [Full results](results.json)

Four activity measures were available on both streams. OULAD counts virtual-learning-environment clicks, days, recency and sites. The MOOC mapping uses action count, active days, days since the last action and distinct activity targets. Observation windows, activity granularity, selection into the roster and event definitions differ. The same equations were applied directly to these proxies. Destination data did not contribute to model fitting or equation recovery. Published numerical coefficients were used directly for the distributed and pooled Newton fits. Linear equations recovered from archived source probabilities reproduced every source forecast to within 1.0e−15. The local-model means avoid choosing a source client using destination labels. The analysis includes 41 score rules and simultaneous learner-level intervals for 40 paired comparisons. Uncertainty conditions on the source fits and one receiving stream. [Frozen design](design.md) · [Source FL evidence](../manuscript.md)

This exploratory study reuses the labeled stream from the queue analysis. A first flag on a last observed action is the destination endpoint. That flag has no verified contemporaneous delivery time. The exercise tests transport of a score function across data sources. There was one source university with seven simulated clients, a separate receiving dataset and zero rounds of cross-institution training. The source release supplies probabilities for stronger neural controls; it lacks the networks needed for out-of-source inference. A claim of improved federated prediction against the complete comparator set remains unestablished.

From the repository root, prepare the source design rows from the public OULAD archive. The scorer reads the MOOC CSV documented in the [external queue study](../../mooc_queue/README.md).

```sh
set -eu
d=research_v4_2/external/landmark/federated/frozen_transfer
p=$(mktemp)
(cd "$d" && sha256sum -c design.sha256)
OPENBLAS_NUM_THREADS=1 python "$d/../prepare.py" private_data/raw/oulad/2013-2014/oulad.zip "$p"
OPENBLAS_NUM_THREADS=1 python "$d/score.py" "$p" private_data/raw/act-mooc/author-mooc.csv | diff - "$d/results.json"
```
