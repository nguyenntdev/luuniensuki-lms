# Which information in an initial evaluation predicts a second judgment?

Across 770 machine-generated answers to 380 questions, the four-field path of the first evaluator predicted another evaluator's binary judgment better than the first evaluator's final vote alone. The path-conditioned estimate had Brier loss .04847 versus .05323 for a trained binary transition table. The paired difference was −.00476 (95% interval −.00752 to −.00200). The unsmoothed path table achieved .04907. The incremental difference from smoothing was −.00060 (−.00206 to +.00085). Log loss gave the same ordering. No question in the official dev file occurred in the fitting file. [All estimates and intervals](result.json)

The source provides repeated ratings and the decision path taken within each rating. For each ordered pair, only the first reader's path and vote are available to the estimator. The sibling [cross-fitted analysis](../panel_shrinkage/README.md) used the official test file before this experiment. We therefore used it for fitting and froze the method before evaluating on the official dev file. There were 5,672 ordered pairs of distinct judgments. Each item received equal weight, and intervals clustered by question condition on the fitted rule. Annotator identities are unavailable. The measured outcome is the second recorded binary judgment. A new essay grader or equivalence system would require a different evaluation. [Frozen design](design.md) · [Bulian et al. dataset](https://github.com/google-research-datasets/answer-equivalence-dataset)

One stronger binary comparator also clarifies the cross-fitted result. With item-weighted first-vote mean m and pair product moment t, the empirical probability of a positive second vote is t/m after a positive vote and (m−t)/(1−m) after a negative one. With an interior correlation estimate, those are exactly the two probabilities produced by the sibling empirical Bayes rule. The improvement against fixed smoothing does not establish a new binary estimator.

From this directory the following commands reproduce the stored table.

```sh
set -eu
base=https://raw.githubusercontent.com/google-research-datasets/answer-equivalence-dataset/5032298f3fe69bebab4a013de5606231a948cebc/v1
tmp=$(mktemp -d)
for split in dev test; do curl -fsSL "$base/ae_$split.jsonl" -o "$tmp/$split.jsonl"; done
sha256sum -c design.sha256
python evaluate.py "$tmp/test.jsonl" "$tmp/dev.jsonl" | diff - result.json
```
