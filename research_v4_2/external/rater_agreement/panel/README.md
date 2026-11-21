# Can four new votes predict the rest of a 100-person rating panel?

The empirical Bayes forecaster beat unconditional Dirichlet shrinkage on both held-out ChaosNLI cohorts. Its apparent gain disappeared when a comparator conditioned on both the old and new vote histograms. The saturated table agreed with every forecast to within 2.6 × 10⁻¹⁵. A regularized multinomial regression achieved lower loss on MultiNLI. This line contributes zero qualifying papers.

| Method | SNLI log loss | MultiNLI matched log loss |
|---|---:|---:|
| Empirical panel mixture | .64333 | .82598 |
| Four new votes with Jeffreys smoothing | .69817 | .89122 |
| Five old and four new votes with Jeffreys smoothing | .68504 | .83942 |
| Global Dirichlet-multinomial | .68233 | .87855 |
| Old-histogram-specific Dirichlet-multinomial | .64722 | .82659 |
| Saturated conditional table | .64333 | .82598 |
| Multinomial logistic regression | .64265 | .82123 |

The published archives contain 100 newly elicited votes per disputed pair. The prior five-vote experiments had examined some of the source items. The new information here is the distribution of the new panel's votes. We averaged over all possible four-vote draws without replacement. This removes Monte Carlo noise and gives each item equal weight. Earlier annotator identities and the ordering of new votes are unavailable. The empirical results describe this collection protocol. [Nie, Zhou and Bansal, EMNLP 2020](https://aclanthology.org/2020.emnlp-main.734/) · [Author archive and reuse guidance](https://github.com/easonnie/ChaosNLI/tree/2a999dc4a672df4ef87b9c7134247201352dee81)

A hash split by normalized premise held out 330 SNLI items (273 premises) and 318 MultiNLI items (277 premises). Seven SNLI items lacked five eligible earlier labels. All 1,599 MultiNLI items qualified. The corpora had no normalized premises in common. We tested all six controls, requiring a gain of .005 nats and a positive simultaneous lower bound for each in both corpora. The gain over local Dirichlet shrinkage was .00389 nats on SNLI and .00061 on MultiNLI. The gain over logistic regression on MultiNLI was −.00476 nats (simultaneous interval −.00722 to −.00169). All intervals condition on the fitted models, with resampling at the premise level. [SNLI results](run/snli/result.json) · [MultiNLI results](run/mnli_m/result.json) · [Locally frozen protocol](protocol.md)

The equality follows from summing the same probabilities in two orders. For each input histogram, a training panel contributes its weight times the probability of drawing that histogram times the fraction of each class left in the panel. The candidate averages these contributions across empirical panels and normalizes. The conditional table accumulates the identical joint counts first and normalizes the corresponding cell. Equal backoff and smoothing therefore give equal predictions everywhere. Text-based distribution predictors answer a broader information question. The study establishes no superiority over them. [Distributed NLI model and reported task](https://github.com/easonnie/ChaosNLI/tree/2a999dc4a672df4ef87b9c7134247201352dee81/distnli)

## Replay from the repository root

The downloader checks the authors' pinned SHA-256 values. The evaluator uses NumPy, SciPy, scikit-learn and Python 3.12. The Node verification computes every saved item loss independently by enumerating ordered draws rather than using hypergeometric coefficients. Public artifacts contain IDs, hashed groups, aggregate losses and model probabilities. The source files and text stay in the ignored raw cache.

```bash
set -eu
d=research_v4_2/external/rater_agreement/panel
r=private_data/raw/chaosnli
mkdir -p "$r"
curl -fsSL https://raw.githubusercontent.com/easonnie/ChaosNLI/2a999dc4a672df4ef87b9c7134247201352dee81/scripts/download_data.py -o "$r/download_data.py"
python "$r/download_data.py" --output-dir "$r"
(cd "$d" && sha256sum -c protocol.sha256 && sha256sum -c implementation.sha256)
o=$(mktemp -d)
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python "$d/evaluate.py" "$r" "$o"
node --check "$d/verify.mjs"
node "$d/verify.mjs" "$r" "$o"
diff -r "$d/run" "$o"
```
