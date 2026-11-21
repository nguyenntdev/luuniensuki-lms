# Ranking errors in electrical-machine knowledge classification

The UCI knowledge-modeling workbook describes study time, repetition, and exam performance on target and related material. Its authors assigned four knowledge levels using a modeling procedure. A learner-level identity and deployment timestamp are unavailable. We analyze agreement with these labels after the five predictors have been recorded. The screen uses the 258 rows of Training_Data and never loads Test_Data. The source is distributed under CC BY 4.0. [Dataset](https://doi.org/10.24432/C5231X) · [Kahraman, Sağiroğlu and Çolak](https://doi.org/10.1016/j.knosys.2012.08.009)

The same classifier made 23 errors across five outer folds. The proposed confidence combines an out-of-fold logistic correctness estimate with the correctness of neighboring examples. The candidate had the lowest mean AURC (.02186). Temperature-scaled maximum probability scored .02709, a gain of .00523 against the required .02. The candidate beat the learned error detector on two of five folds and beat the local-only component on all five. Only the comparison with neighbor class agreement cleared .02. Sorting each fold with perfect knowledge of the errors would yield .00530 AURC. Thus the required advantage over temperature scaling would need to capture at least 92% of the maximum available improvement in this development sample. The test sheet remains available for a future independently motivated method. No paper-level win follows from this screen. [Frozen design](protocol.md) · [All six contrasts](run/result.json) · [Fold signs and oracle](run/verification.json)

The scalar temperature model follows post-hoc calibration and shares the original predictions. Local agreement is an ordinary neighborhood control, and the detector gives a trained confidence model access to all five features and the original classifier's output. No claim of novelty for the combination or equivalence to earlier methods is made. [Maximum softmax](https://openreview.net/forum?id=Hkg4TI9xl) · [Guo et al., temperature scaling](https://proceedings.mlr.press/v70/guo17a.html)

Run from repository root with Python 3.12, NumPy, SciPy, scikit-learn, xlrd 2.0.2 and Node 24. The verifier recalculates all 35 method-by-fold AURCs directly from row scores. The local protocol hash records the file version without an external timestamp.

```bash
set -eu
d=research_v4_2/external/coverage/knowledge
raw=private_data/raw/user-knowledge
mkdir -p "$raw"
curl -fsSL 'https://archive.ics.uci.edu/static/public/257/user+knowledge+modeling.zip' -o "$raw/archive.zip"
(cd "$d" && sha256sum -c protocol.sha256)
out=$(mktemp -d)
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python "$d/screen.py" "$raw/archive.zip" "$out"
node --check "$d/verify.mjs"
node "$d/verify.mjs" "$out" > "$out/verification.json"
diff -r "$d/run" "$out"
```
