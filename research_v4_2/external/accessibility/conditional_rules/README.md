# Pairwise fusion of published ACT engine outcomes

Adding pairwise interactions reduced equal-rule exact accuracy from **67.03% to 59.11%** on 605 published Accessibility Conformance Testing (ACT) examples across 50 held-out proposed rules. The paired difference was **−7.93 percentage points** against the earlier additive logistic stack, with a 97.5% interval of **−13.88 to −0.37 points** after resampling linked rule clusters. The comparison against smoothed confusion-matrix naive Bayes was also negative in the point estimate. The frozen improvement criterion failed. [Analysis plan](protocol.md) · [Machine-readable results](result.json)

## Data and matched design

The previous studies measured example-level agreement and coverage across published implementations, then tested an additive ensemble on proposed rules. This follow-up asks whether a model can interpret one engine's outcome in light of another engine's outcome. It uses the same W3C archive, 11 automated engine/linter reports, weights, and inventory as the rule-transfer study. The original fixture comparison and additive study motivated this analysis. The 50 proposed rules had already been scored publicly, so this is a retrospective method comparison. [Earlier accessibility study](../manuscript.md) · [Previous evaluation](../confirmatory/protocol.md) · [Pinned publisher snapshot](https://github.com/w3c/wcag-act-rules/tree/4ce3d61b6f7b04cbf2df0082a3446e97248b9124)

We trained on 558 examples from 37 approved rules and tested on 605 examples from 50 proposed rules. The prior protocol excluded 13 of 618 eligible proposed-rule cases because of shared testcase IDs or normalized contents with the approved training fixtures or the earlier four-engine reference inventory. The evaluator rechecks that training and test rules, testcase IDs and normalized content hashes are disjoint. It reproduces every earlier held-out prediction and expected label before fitting any interaction model. The controls and new models predict on the same complete inventory, including 67 examples for which every eligible engine reported untested or had no result. No fresh reserved dataset was used. [Aligned predictions](predictions.csv) · [Earlier release](../confirmatory/predictions.csv)

Logistic regression used the original five outcome indicators per engine and equal total training weight per rule. The primary model added one indicator for each realized pair of exercised outcomes. An engine's request for manual review is an exercised outcome. The diagnostic models added only interactions involving at least one untested engine or added the full set of pair interactions. All models used the same L2 penalty with C=1 and the same all-untested abstention rule. The diagnostic models have different feature counts. [Evaluator](evaluate.py)

## Complete-inventory results

| Method | Equal-rule exact | Exact fixtures | Expected failures detected | Other failure alerts |
|---|---:|---:|---:|---:|
| Earlier additive logistic | 67.03% | 430/605 | 130/206 | 19 |
| Missingness interactions | 65.75% | 433/605 | 113/206 | 0 |
| Earlier naive Bayes | 64.86% | 427/605 | 113/206 | 0 |
| Full interactions | 60.10% | 411/605 | 112/206 | 1 |
| **Paired exercised outcomes** | **59.11%** | **403/605** | **112/206** | **0** |

All five methods abstained on the same 67 fixtures. The primary model fired 19 fewer false alerts and detected 18 fewer labeled failures than the additive control. These single operating points do not estimate performance at a common alert budget. The missingness interaction diagnostic gained three exact fixtures over the additive control while losing 1.28 points when each rule received equal weight. [All engine and ensemble scores](result.json)

| Primary contrast | Equal-rule difference | Linked-rule interval | Individual-rule interval | Rule wins / ties / losses |
|---|---:|---:|---:|---:|
| Paired outcomes minus additive logistic | −7.93 pp | [−13.88, −0.37] pp | [−12.22, −3.85] pp | 2 / 27 / 21 |
| Paired outcomes minus naive Bayes | −5.76 pp | [−11.86, +1.34] pp | [−9.65, −2.01] pp | 4 / 26 / 20 |

The 50 held-out rules form 28 connected components when linked by shared testcase IDs or normalized contents. The largest component contains 10 rules. The wider linked-rule interval for naive Bayes spans zero. Both contrasts use two-sided 97.5% percentile intervals for nominal 95% joint coverage. Estimates condition on fitted models and may still miss semantic dependence between fixtures. [Cluster memberships and paired estimates](result.json)

## Where the result changed

Among 158 fixtures with one exercised engine, the pair model matched 70 labels and the additive control matched 101. This accounts for a net loss of 31 exact predictions within that slice. Although the interaction features are zero on those fixtures, jointly fitting the main effects with the interaction coefficients can change their predictions. Among 380 fixtures with at least two exercised engines, the pair model matched 333 versus 329, while its equal-rule accuracy was lower at 84.35% versus 86.80%. On 129 fixtures with conflicting decisive votes, both methods matched 123 and had the same equal-rule accuracy. The original four-engine common-support slice contained only 79 examples from five rules. Both methods matched 77 there. These descriptive slices do not isolate a causal effect of the interaction features. [Support slices](result.json)

These results describe exact agreement with published ACT example labels. W3C implementation consistency permits some example outcomes that differ from the expected example label. The report archive supplies no sampling design for estimating real-site accuracy or evidence for semantic accessibility and user outcomes. [W3C implementation consistency guidance](https://www.w3.org/WAI/standards-guidelines/act/implementations/)

## Reproduce

Run from the repository root using Python 3.12, on permitted CPUs. The frozen run used NumPy 2.4.4, SciPy 1.17.1, scikit-learn 1.8.0, threadpoolctl 3.6.0, and PyYAML 6.0.1. The evaluator verifies the archive, analysis plan, earlier evaluator and released prediction hashes before fitting new models. Supply an existing copy of the archive to skip the download.

```sh
set -eu
study=research_v4_2/external/accessibility/conditional_rules
revision=4ce3d61b6f7b04cbf2df0082a3446e97248b9124
work=$(mktemp -d)
python3.12 -m venv "$work/venv"
"$work/venv/bin/pip" install numpy==2.4.4 scipy==1.17.1 scikit-learn==1.8.0 threadpoolctl==3.6.0 PyYAML==6.0.1
curl -fsSL "https://codeload.github.com/w3c/wcag-act-rules/tar.gz/$revision" -o "$work/w3c.tgz"
PYTHONDONTWRITEBYTECODE=1 taskset -c 0-9 "$work/venv/bin/python" "$study/evaluate.py" "$work/w3c.tgz" "$work/run"
cmp "$study/result.json" "$work/run/result.json"
cmp "$study/predictions.csv" "$work/run/predictions.csv"
```
