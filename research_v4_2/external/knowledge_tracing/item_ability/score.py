"""Join predictions to both published development ledgers and compute paired contrasts."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

KEY = ["uid","row","start","y"]


def score(study):
    past = pd.read_csv(study.parent / "temporal/run/screen.csv.gz").drop(columns="gap_s")
    upstream = pd.read_csv(study.parent / "published_simplekt/run/screen.csv.gz")
    out = study/"run"
    extra = pd.read_csv(out/"estimates.csv.gz")
    df = past.merge(upstream[KEY+["items","skill_only"]], on=KEY, validate="one_to_one")
    df = df.merge(extra, on=KEY, validate="one_to_one")
    assert len(df) == len(past) == len(upstream) == len(extra)
    names = [k for k in df if k not in KEY+["question_support"]]
    pred = df[names].to_numpy()
    assert ((pred > 0) & (pred < 1)).all()
    losses = pd.DataFrame(np.where(df.y.to_numpy()[:,None], -np.log(pred), -np.log1p(-pred)), columns=names)
    controls = [k for k in names if k != "ability"]
    summed = losses[controls].sub(losses.ability, axis=0).groupby(df.uid).sum()
    sizes = df.groupby("uid").size().reindex(summed.index).to_numpy()
    n = len(sizes)
    draws = np.random.default_rng(732).multinomial(n, np.ones(n)/n, size=5000)
    lo,hi = np.quantile((draws @ summed)/(draws @ sizes)[:,None],
                        [.025/len(controls), 1-.025/len(controls)], axis=0)
    mean = losses.mean()
    contrasts = {k:dict(gain=mean[k]-mean.ability, ci=[lo[j],hi[j]],
                        passed=bool(mean[k]-mean.ability > .015 and lo[j] > 0))
                 for j,k in enumerate(controls)}
    bands = pd.cut(df.question_support, bins=[-1,0,5,19,float("inf")], labels=["unseen","1_to_5","6_to_19","20_plus"])
    strata = {}
    for b in bands.cat.categories:
        mask = bands == b
        strata[b] = dict(rows=int(mask.sum()), learners=df.uid[mask].nunique(),
                         loss=losses.loc[mask,["clock","matched","ability"]].mean().to_dict())
    results = dict(rows=len(df), learners=n, loss=mean.to_dict(), contrasts=contrasts, strata=strata,
                   passes=sum(x["passed"] for x in contrasts.values()), advances=all(x["passed"] for x in contrasts.values()))
    (out/"result.json").write_text(json.dumps(results, indent=2)+"\n")


if __name__ == "__main__":
    score(Path(sys.argv[1]))
