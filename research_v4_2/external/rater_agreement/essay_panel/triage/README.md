# Prioritizing essays for a third instructor at fixed capacity

For each held-out instructor and each writer fold, a policy could refer seven of 38 essays. An essay's value for this simulated review was the average absolute difference between the third instructor and the midpoint of the first two, across four analytic traits. Higher values identify larger discrepancies. The third score and all other scores by the target instructor for writers in that pool were excluded from fitting. This tests selection using archived ratings from Campbell's 76 IELTS essays; it leaves the outcome and cost of actual adjudication unmeasured. [Source and licence](https://doi.org/10.5281/zenodo.19656187) · [Design](design.md)

At 42 review slots, supervised ranking found .45387 score points of discrepancy per review. The matched model with the directional features removed found .45238. Simply prioritizing essays by the gap between the AI mean and the two-instructor midpoint found .51488, compared with .41996 expected under uniform random selection and .81994 under the oracle. The candidate cleared the .05-point development margin only against the peer-gap control. The actual writer cohort is small and reused, and the three instructor rotations reuse the same essays. These estimates support a comparison of review policies on this archive. A gain in rubric reliability would require a separate endpoint. [All decisions](run/decisions.csv) · [Outcomes by policy](run/result.json)

Follow the parent study's instructions to obtain the pinned source CSV. This run uses Python 3.12, NumPy, pandas and scikit-learn. The independent verifier checks all reference discrepancies, simple scores, pool assignments, tie keys, and 1,596 binary review decisions against the recorded rankings. The model fits can be reproduced separately using the screen.

```bash
set -eu
d=research_v4_2/external/rater_agreement/essay_panel/triage
src='private_data/raw/ielts-raters/AI Assessment Scores.csv'
out=$(mktemp -d)
(cd "$d" && sha256sum -c design.sha256)
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python "$d/screen.py" "$src" "$out"
python "$d/verify.py" "$src" "$out" > "$out/verification.json"
diff -r "$out" "$d/run"
```
