# Predicting a second anonymous judgment
From this directory, reproduce on CPUs 20–29 with Python 3.10+ and the publisher's public release.
```sh
taskset -c 20-29 curl -fsSL https://raw.githubusercontent.com/google-research-datasets/answer-equivalence-dataset/main/v1/ae_test.jsonl -o /tmp/ae_shrinkage_test.jsonl
sha256sum -c protocol.sha256
taskset -c 20-29 python evaluate.py /tmp/ae_shrinkage_test.jsonl | diff - result.json
```
On 1,733 repeatedly rated items, learned smoothing reduced Brier loss from 0.07861 for the observed vote to 0.07372. The paired 95% interval for the difference was −0.00663 to −0.00314. Log loss fell from 0.37817 to 0.27924 under the specified 1% clipping rule. The training mean and both two-pseudo-vote rules scored worse on both metrics. The classical Laplace rule supplies a published statistical comparator. The matched fixed rule shares the EB prior mean, but its concentration is stronger than the fitted concentration. This experiment does not establish superiority over every fixed smoothing strength.

Results concern another human judgment of machine answer equivalence. Evaluator overlap is unknown, and the study establishes neither answer correctness nor transfer to student essay grading. Intervals condition on fitted folds and omit uncertainty from repeated training. See result.json for fold fits and all paired intervals.
