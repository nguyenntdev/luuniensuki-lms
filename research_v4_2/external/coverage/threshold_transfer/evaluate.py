"""Exchange frozen confidence cutoffs between two local classifiers."""
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "secondary_run"


def compare(frame, local, foreign):
    score = frame.max_probability
    error = frame.argmax != frame.truth
    reroute_error = frame.rerouted_at_full_coverage != frame.truth
    masks = {"local": score >= local, "foreign": score >= foreign, "full": score >= 0}
    local_labels = frame.gate[masks["local"]]
    assert (local_labels == frame.rerouted_at_full_coverage[masks["local"]]).all()
    assert frame.gate[~masks["local"]].nunique() == 1
    assert not set(frame.gate[~masks["local"]]) & set(frame.truth)
    counts = {}
    for name, chosen in masks.items():
        counts[name] = dict(accepted=int(chosen.sum()), coverage=chosen.mean(),
                            argmax_errors=int(error[chosen].sum()), argmax_risk=error[chosen].mean(),
                            rerouted_errors=int(reroute_error[chosen].sum()))
    moved = masks["local"] ^ masks["foreign"]
    components = np.column_stack((np.ones(len(frame)), masks["local"], masks["foreign"],
                                  masks["local"] & error, masks["foreign"] & error))
    groups = pd.DataFrame(components).groupby(frame.learner_cluster).sum().to_numpy()
    rng = np.random.default_rng(20261122)
    def effects(totals):
        n, loc, ext, le, ee = totals
        return [(ext-loc)/n, ee/ext-le/loc]
    draws = [effects(groups[rng.integers(len(groups), size=len(groups))].sum(axis=0)) for _ in range(2000)]
    intervals = np.quantile(draws, [.025/4, 1-.025/4], axis=0).T
    return dict(rows=len(frame), clusters=len(groups), local_cutoff=local, foreign_cutoff=foreign,
                policies=counts, moved=int(moved.sum()), moved_argmax_errors=int(error[moved].sum()),
                foreign_minus_local={name:dict(difference=value, simultaneous_ci95=ci.tolist())
                for name, value, ci in zip(("coverage", "argmax_risk"), effects(groups.sum(axis=0)), intervals)})


if __name__ == "__main__":
    subprocess.run(["sha256sum","--check","--status","protocol.sha256"], cwd=HERE, check=True)
    meta = json.loads((SOURCE / "results.json").read_text())
    cutoffs = {key: data["thresholds"]["tau_conf"] for key, data in meta.items()}
    output = {}
    for receiver, donor in (("oulad","uci"), ("uci","oulad")):
        frame = pd.read_csv(SOURCE / f"{receiver}_predictions.csv", float_precision="round_trip")
        output[receiver] = compare(frame, cutoffs[receiver], cutoffs[donor])
    print(json.dumps(output, indent=2))
