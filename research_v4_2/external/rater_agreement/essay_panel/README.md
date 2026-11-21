# Does disagreement between initial graders predict whose scores to trust?

Colin Campbell's public release contains scores for 76 IELTS essays by 38 writers, each scored by three instructors and four archived AI runs. We used four analytic traits and all three choices of withheld instructor to predict 912 released values. For each writer, we trained every correction and weighting parameter using only the other 37 writers. A scorer using the two available instructors attained mean absolute error .41996. A blend of corrected instructor and AI scores reached .40759. Conditioning its weights on disagreement between the two instructors yielded .40752. The extra gain was .000071 score points, with a simultaneous paired writer-bootstrap interval of −.00240 to .00216. [Study design](protocol.md) · [All eight comparisons](run/scores.json)

Three of eight contrasts cleared the .05-point development margin. The favorable comparisons were against the lower observed instructor score and the two automation-only forecasts. The candidate missed the margin against the mean of the observed instructors, the constant half blend, and its matched ablation. Between-writer bootstrap intervals describe variation in the scored writer losses conditional on these fitted predictions. The fits share training writers, and there are only three named instructor roles. The design cannot identify generalization to a new instructor or institution. It also cannot estimate agreement gains attributable to changing a rubric, the cost of review, or historical reasoning. The experiment uses each third instructor's published analytic score as the target. Facets-derived holistic scores were excluded.

## Provenance and reproduction

The publisher's codebook reports consent, anonymized IDs, two writing tasks and four analytic traits. The archived AI scores are treated as predictions made available by the source. All results here use version 19656187 of Colin Campbell's release under CC BY 4.0. The archive contains the source files and codebook. The public results below contain pseudonymous writer indices from the release and rubric scores. [Dataset and codebook](https://doi.org/10.5281/zenodo.19656187) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

From the repository root use Python 3.12, pandas and NumPy. A second scorer using the Python standard library reconstructs all nine forecasts directly from the raw panels and checks aggregate losses. [Verification receipt](run/verification.json)

```bash
set -eu
d=research_v4_2/external/rater_agreement/essay_panel
r=private_data/raw/ielts-raters
mkdir -p "$r"
src="$r/AI Assessment Scores.csv"
curl -fLsS --retry 3 'https://zenodo.org/api/records/19656187/files/AI%20Assessment%20Scores.csv/content' -o "$src"
(cd "$d" && sha256sum -c protocol.sha256)
out=$(mktemp -d)
OPENBLAS_NUM_THREADS=1 python "$d/evaluate.py" "$src" "$out"
python "$d/verify.py" "$src" "$out" > "$out/verification.json"
diff -r "$out" "$d/run"
```
