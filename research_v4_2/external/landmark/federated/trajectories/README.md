# Day-60 activity trajectories in personalized federated prediction

This experiment compares sharing a common slope vector, fitting module-specific models, and jointly estimating common slopes and private deviations. Six activity windows retain when activity occurred during the first 61 days. Matched cumulative-feature models isolate the effect of timing. Centralized CatBoost and archived neural predictions provide nonlinear controls. The [design](design.md) fixes the comparison and metric before evaluation.

Preparation reproduced all 8,815 published development registration keys and outcomes. Both sets of window counts sum to the parent totals for all 24,878 training and development registrations. The remote fitting input omits the development labels. The fitting and scoring scripts below are staged for the GPU run. No performance estimate is claimed from data preparation.

From the repository root, prepare the data in a temporary directory. The archive, license and original neural controls are documented in the [parent study](../README.md).

```sh
set -eu
d=research_v4_2/external/landmark/federated/trajectories
tmp=$(mktemp -d)
(cd "$d" && sha256sum -c design.sha256)
OPENBLAS_NUM_THREADS=1 python "$d/prepare.py" private_data/raw/oulad/2013-2014/oulad.zip "$tmp"
```

Copy only train.csv, dev.csv and fit.py to a CUDA host with PyTorch, CatBoost, NumPy and pandas. Run `python fit.py .` from that directory, then copy forecasts.csv and audit.json back to the local staging directory. Run `python "$d/score.py" "$tmp" "$tmp/run"` locally. The fit checks coefficient agreement against a dense centralized solve of the same objective. The scorer verifies the registration keys and uses the parent simultaneous learner-cluster procedure. Seven modules are simulated clients within one university.
