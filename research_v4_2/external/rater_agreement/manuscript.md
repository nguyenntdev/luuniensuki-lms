# What survives the reduction of a reader's decision path to a binary vote?

## Abstract

Can the intermediate answers a reader already supplied help forecast the judgment of a second reader? We studied two releases of repeated human judgments of answer equivalence for machine-generated short answers. In 1,733 repeatedly rated items, learning how strongly to trust a binary vote improved Brier loss over repeating that vote by .00489. We show that the fitted binary rule equals an ordinary conditional frequency estimator on these folds. A second experiment asked whether the information discarded by binary scoring matters. A table fitted on the first release and evaluated on 770 items from 380 different questions reduced Brier loss from .05323 to .04847 when it retained the first reader's full response path. An unsmoothed path table achieved .04907. The evidence supports retaining the path for this forecasting task. It gives little basis for choosing between the two path estimators.

## Question and data

Bulian and colleagues collected human judgments to assess equivalence between candidate and reference answers. Each released record supplies one evaluator's four intermediate responses and a final binary score. A downstream consumer can store the binary answer alone or preserve the intermediate responses at the same labeling cost. Predicting how another recorded evaluator scored the item provides an observable endpoint for comparing those representations. The individual evaluator IDs are unavailable. The item key combines question ID, candidate answer and reference index. [Source data and paper](https://github.com/google-research-datasets/answer-equivalence-dataset) · [Panel eligibility audit](second_panel/README.md)

## Estimand and comparison

For an item with k recorded judgments, sample two different judgment *positions* in order. Use the first position's response to forecast the binary score at the second. We enumerated all k(k−1) pairs and averaged loss within item before averaging equally across items. This weighting prevents a four-vote panel from contributing twice as much as a three-vote panel. The data cannot identify distinct people behind two positions. We clipped all probabilities to [.01,.99] before computing Brier and natural log loss.

In the first experiment we partitioned the 831 questions of the official test release into five folds by a hash of question ID. Fitting used the other four folds. An empirical Bayes estimator learned a coefficient between zero and one for shrinking an observed binary vote toward the fitted population mean. We evaluated the fitted mean alone, the observed vote alone, Laplace smoothing, and fixed smoothing with two pseudo-observations centered at the same fitted mean. [Protocol, fitted coefficients and results](panel_shrinkage/README.md)

In the second experiment the official test release became the fitting set, after its binary results were known. We fixed the comparison before evaluating on the official dev file. All 1,144 dev question IDs were absent from the fitting release. Of these, 380 questions contributed the 770 multiply rated items. The path estimator tabulated second votes separately by the first reader's decision path, with two pseudo-observations centered at the fitted binary conditional probability. A matched ablation used the same path counts with zero pseudo-observations. In either case an unseen path backs off to its binary conditional probability. [Frozen design and executable comparison](decision_paths/README.md)

## Results

The first experiment gave Brier .07372 for empirical Bayes, .07861 for the observed vote, .24775 for the population prior, .13682 for fixed smoothing and .13781 for Laplace smoothing. The paired difference from the observed vote was −.00489 (95% interval −.00663 to −.00314). There is a simple explanation for the estimator's success. Let m be the item-weighted mean first vote and t the item-weighted product of the two votes. The two marginal means agree because both orders of each pair are scored. Given first vote 1, the training frequency of a second positive vote is t/m. Given first vote 0, it is (m−t)/(1−m). Substituting the unconstrained moment estimate (t−m²)/(m(1−m)) into the shrinkage formula gives these two frequencies exactly. All five coefficients lay strictly inside the clipping bounds for that coefficient.

| Forecast on reverse-split transfer | Brier | Log loss |
|---|---:|---:|
| First reader's observed vote | .05483 | .26666 |
| Training marginal | .24515 | .68342 |
| Trained transition given the binary vote | .05323 | .21911 |
| Trained transition given the path | .04907 | .19491 |
| Path counts shrunk toward the binary transition | .04847 | .19285 |

The full method improved Brier over the trained binary transition by .00476 (paired 95% interval .00200 to .00752). Its improvement over the unsmoothed path table was .00060 (−.00085 to .00206). The study therefore localizes most of the observed gain to retaining intermediate decisions. Each interval clusters item losses by question and conditions on the fitted tables. Intervals are marginal across comparisons. [All paired contrasts](decision_paths/result.json)

## Scope and reproducibility

These estimates apply to archived answers with multiple judgments. They cannot identify evaluator-specific bias, the correctness of the candidate answer, or the effect of changing an educational rubric. The two releases share an annotation task and provider. A writer-disjoint [essay study](essay_panel/README.md) provides a boundary on transfer: conditioning a blend on instructor disagreement improved mean absolute error by only .000071 score points over its ablation. That ordinal, three-instructor outcome has a different scale and population and is kept separate.

Both evaluation scripts verify the source SHA-256 before scoring. Their linked protocols reproduce every reported loss from the publisher's files using the Python standard library. All annotations were already public. No additional judgments were collected.
