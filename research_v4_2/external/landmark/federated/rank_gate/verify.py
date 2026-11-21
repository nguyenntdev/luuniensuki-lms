"""Independently score the saved switch decisions and bound the five-weight family."""
import json
from pathlib import Path
from statistics import mean

import numpy as np
import pandas as pd
from scipy.stats import rankdata


def auc(labels, values):
    positive = labels == 1
    n = positive.sum()
    return (rankdata(values)[positive].sum() - n*(n+1)/2) / (n*(len(labels)-n))


root = Path(__file__).resolve().parent
base = pd.read_csv(root.parent / "shadow/run/predictions.csv.gz", float_precision="round_trip")
scores = pd.read_csv(root / "run/predictions.csv.gz", float_precision="round_trip")
pd.testing.assert_frame_equal(base.iloc[:,:5], scores.iloc[:,:5])
gate = json.loads((root / "run/weights.json").read_text())
summary = json.loads((root / "run/summary.json").read_text())
groups = []
for module, frame in base.groupby("code_module"):
    labels = frame.y.to_numpy()
    local, transfer = frame.mlp_local, frame.mlp_transfer
    choices = {}
    for weight in (0, .25, .5, .75, 1):
        candidate = local + weight * (transfer-local)
        if weight == .5:
            candidate = frame.mlp_half
        elif weight == 1:
            candidate = transfer
        choices[weight] = auc(labels, candidate)
        for method in ("gated", "ungated"):
            if gate[module][method] == weight:
                np.testing.assert_allclose(candidate, scores.loc[frame.index, method], atol=2e-16, rtol=0)
    groups.append(dict(module=module, fixed=choices[.5], gated=choices[gate[module]["gated"]],
                       ungated=choices[gate[module]["ungated"]], oracle=max(choices.values()),
                       auc_by_weight=choices))
for method in ("fixed","gated","ungated"):
    name = "mlp_half" if method == "fixed" else method
    assert np.isclose(mean(g[method] for g in groups), summary["macro_auc"][name], atol=1e-12, rtol=0)
upper = mean(g["oracle"] - g["fixed"] for g in groups)
print(json.dumps(dict(clients=groups, oracle_gain_over_fixed=upper), indent=2))
