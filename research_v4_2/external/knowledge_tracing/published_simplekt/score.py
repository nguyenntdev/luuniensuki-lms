"""Score four paired contrasts on previously screened learners."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def score(raw, previous, out):
    table = pd.read_pickle(raw / "cache/rows.pkl").query("70 <= bucket < 80")
    forecast = pd.read_csv(raw / "cache/simplekt_fit/probabilities.csv")
    existing = pd.read_csv(previous / "screen.csv.gz",float_precision="round_trip")
    for name in ["uid","row","y","start","gap_s"]:
        np.testing.assert_array_equal(existing[name],table[name])
    assert len(forecast) == len(existing) and existing.uid.nunique() == 240
    method = "blend_joint"
    controls = ["clock","sakt","items","skill_only"]
    pred = pd.concat((existing[["uid","row","start","gap_s","y",method,"clock","sakt"]],forecast),axis=1)
    names = [method,*controls]
    probabilities = np.clip(pred[names].to_numpy(),1e-7,1-1e-7)
    y = pred.y.to_numpy()[:,None]
    losses = pd.DataFrame(-np.where(y,np.log(probabilities),np.log1p(-probabilities)),columns=names)
    groups = losses.groupby(pred.uid).sum()
    sizes = pred.groupby("uid").size()
    rng = np.random.default_rng(732)
    draws = rng.multinomial(len(sizes),np.full(len(sizes),1/len(sizes)),size=5000)
    gains = groups[controls].to_numpy()-groups[[method]].to_numpy()
    intervals = np.quantile((draws@gains)/(draws@sizes.to_numpy())[:,None],
                            [.025/len(controls),1-.025/len(controls)],axis=0)
    delta = gains.sum(axis=0)/len(pred)
    contrasts = {k:dict(gain=g,interval=b.tolist(),pass_margin=bool(g>.015 and b[0]>0))
                 for k,g,b in zip(controls,delta,intervals.T)}
    summary = dict(rows=len(pred),learners=len(groups),loss=losses.mean().to_dict(),contrasts=contrasts,
                   correct={n:int(((pred[n]>=.5)==pred.y).sum()) for n in names},
                   advance=all(v["pass_margin"] for v in contrasts.values()))
    pred.to_csv(out/"screen.csv.gz",index=False,compression={"method":"gzip","mtime":0})
    groups.assign(rows=sizes).to_csv(out/"learner_sums.csv")
    (out/"result.json").write_text(json.dumps(summary,indent=2)+"\n")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ["raw","previous","out"]:
        parser.add_argument(name,type=Path)
    args=parser.parse_args()
    score(args.raw,args.previous,args.out)
