# Independent panel eligibility audit

Bulian et al. release separate human judgments of answer equivalence for machine-generated short answers. The repository carries Apache License 2.0. Each test JSONL row supplies one binary score. The four raw decision fields belong to that judgment. [Publisher](https://github.com/google-research-datasets/answer-equivalence-dataset) · [License](https://github.com/google-research-datasets/answer-equivalence-dataset/blob/main/LICENSE)

Grouping by question ID, candidate answer and gold reference index gives 5,831 items from 9,724 judgments. Exactly 4,098 have one rating, seven have two, 1,292 have three and 434 have four. All 9,724 rows lack both a writer ID and an evaluator ID. Thus 1,733 items support anonymous held-out judgment scoring, and zero support verification of writer-disjoint training and evaluator-disjoint calibration. The task assesses machine answer equivalence and cannot establish an effect on student essay grading.

The descriptive benchmark withholds each judgment in turn and predicts it with the mean of the other judgments on that item. Each item gets equal weight. Mean absolute error was 0.08011 across the 1,733 multiply rated items. No parameters are trained. Individual evaluator overlap cannot be checked, so the benchmark supports no rater-aware superiority claim.

Download the publisher's [test file](https://raw.githubusercontent.com/google-research-datasets/answer-equivalence-dataset/main/v1/ae_test.jsonl) and run `python audit.py /path/to/ae_test.jsonl` from this directory. The script checks the SHA-256 digest before scoring.
