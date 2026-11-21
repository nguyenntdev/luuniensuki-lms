"""Score fixed forecasts with a paired learner-cluster bootstrap and tied-score midranks."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


def score(path):
    d = pd.read_csv(path)
    names = ["history_tree","current_tree","logistic","gru","blend"]
    y = d.LABEL.to_numpy()
    ids, group = np.unique(d.USERID, return_inverse=True)
    scores = {}
    # Ranking only depends on forecasts and stays fixed across bootstrap samples.
    bins = [np.unique(d[k], return_inverse=True)[1] for k in names]
    def aucs(w):
        out = []
        for b in bins:
            pos = np.bincount(b, weights=w*y)
            neg = np.bincount(b, weights=w*(1-y))
            out.append(pos @ (neg.cumsum() - .5*neg) / (pos.sum()*neg.sum()))
        return np.array(out)
    point = aucs(np.ones(len(d)))
    for name, auc in zip(names, point):
        assert np.isclose(auc, roc_auc_score(y, d[name]))
        scores[name] = dict(auc=float(auc), ap=float(average_precision_score(y, d[name])))
    rng = np.random.default_rng(731)
    contrasts = []
    for _ in range(2000):
        w = np.bincount(rng.integers(len(ids), size=len(ids)), minlength=len(ids))[group]
        if 0 < w@y < w.sum():
            values = aucs(w)
            contrasts.append(values[-1] - values[:-1])
    bounds = np.quantile(contrasts, [.025/4, 1-.025/4], axis=0)
    for i, name in enumerate(names[:-1]):
        scores[name].update(blend_gain=float(point[-1]-point[i]), simultaneous_ci=bounds[:,i].tolist())
    return dict(events=len(d), learners=len(ids), positives=int(y.sum()), paired_draws=len(contrasts),
                estimates=scores, stage_pass=bool(np.all(point[-1]-point[:-1]>=.01) and np.all(bounds[0]>0)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    run = parser.parse_args().run
    (run/"result.json").write_text(json.dumps(score(run/"predictions.csv.gz"), indent=2)+"\n")
