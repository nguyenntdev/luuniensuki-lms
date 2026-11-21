#!/usr/bin/env python3
"""Recompute fixed-fit module deletion estimates from archived probabilities."""
from pathlib import Path
import pandas as pd
from sklearn.metrics import roc_auc_score

here = Path(__file__).resolve().parent
keys = ["row", "learner", "code_module", "code_presentation", "y"]
def read(study):
    return pd.read_csv(here.parent / study / "run/predictions.csv.gz").set_index(keys)

base = read("sufficient_stats")
schedule = read("schedule")
assert base.index.is_unique and base.index.equals(schedule.index)
base["schedule"] = schedule.adapted
base["mlp_half"] = schedule.mlp_half
assert len(base) == 8815 and base.index.get_level_values("learner").nunique() == 8505
scores = {}
for module, rows in base.groupby(level="code_module"):
    scores[module] = rows.apply(lambda p: roc_auc_score(rows.index.get_level_values("y"), p))
modules = pd.DataFrame(scores)
assert modules.shape[1] == 7
results = {"all": modules.mean(axis=1)}
for module in modules:
    results[module] = modules.drop(columns=module).mean(axis=1)
pd.DataFrame(results).rename_axis("model").to_csv(here / "macro_auc.csv", float_format="%.9f")
