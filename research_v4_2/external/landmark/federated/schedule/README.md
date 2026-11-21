# P13 schedule conditioning on OULAD

On 8,815 eligible registrations from 8,505 learners in seven simulated course clients, conditioning activity slopes on the number of assessments due through day 60 raised macro AUC from .62528 to .62678. The paired gain of .00150 (simultaneous 95% interval .00045 to .00255) fell below .02. Weak ridge reached .63116 and the all-MLP half-transfer control reached .64578. The candidate cleared zero of three comparisons. The endpoint concerns withdrawal among learners still registered at day 60 in one previously examined presentation. The archive does not track schedule revisions or establish when earlier final labels became available.

Use the parent prepare.py on the pinned archive to generate input.csv. Extract assessments.csv from that same archive. With the parent directory on PYTHONPATH and its dependencies installed, run the following fit on CUDA, then run verification locally. The recorded fits used an RTX 4060 Ti over SSH. Controls use archived predictions. The matched fit reproduced the parent adapted probabilities to absolute tolerance 1e-12.

```sh
PYTHONPATH=.. python fit.py input.csv assessments.csv preds.csv
taskset -c 31-45 python verify.py preds.csv /path/to/oulad.zip
```

[Protocol](protocol.md) · [All paired intervals](run/summary.json) · [Course scores](run/scores.csv)
