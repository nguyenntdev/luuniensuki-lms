"""Writer-disjoint prediction of an unsupplied third analytic rubric score."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TRAITS = ["task_achievement", "coherence_cohesion", "lexical_resource", "grammar_accuracy"]
METHODS = ["human", "human_corrected", "low", "high", "ai", "ai_corrected", "half", "ungated", "candidate"]
GROUP = ["target_rater", "trait"]
STRATA = GROUP + ["task"]


def examples(source):
    assert hashlib.sha256(source.read_bytes()).hexdigest() == "3cb2afa8048b2924dbc0b91d4993fe697375fce8c616b52a10d4de59dd2cc877"
    rows = []
    for (writer, task), frame in pd.read_csv(source).groupby(["student_id", "task"]):
        humans = frame.loc[frame.rater_type == "Human"].set_index("rater_id")
        ai = frame.loc[frame.rater_type == "AI"]
        assert len(humans) == humans.index.nunique() == 3 and ai.gpt_run.nunique() == len(ai) == 4
        for rater, trait in itertools.product(humans.index, TRAITS):
            peers = humans.loc[humans.index != rater, trait]
            rows.append([writer, task, rater, trait, humans.at[rater,trait], peers.mean(), peers.min(),
                         peers.max(), ai[trait].mean(), peers.max()-peers.min() >= 1])
    return pd.DataFrame(rows, columns=["writer","task","target_rater","trait","y","human","low","high","ai","discord"])


def fit_predict(training, test):
    train, dev = training.copy(), test.copy()
    for name in ("human", "ai"):
        # Residuals used to estimate the gating weights are cross-fitted by writer.
        train["residual"] = train.y-train[name]
        groups = train.groupby(GROUP).residual
        own = train.groupby(GROUP+["writer"]).residual
        bias = (groups.transform("sum")-own.transform("sum"))/(groups.transform("size")-own.transform("size")+8)
        train[name+"_sq"] = (train.residual-bias)**2
        overall = (groups.sum()/(groups.size()+8)).rename("bias")
        dev = dev.join(overall,on=GROUP,validate="many_to_one")
        dev[name+"_corrected"] = dev[name]+dev.pop("bias")
    errors = ["human_sq", "ai_sq"]
    base = train.groupby(STRATA)[errors].mean()
    strata = STRATA+["discord"]
    stratified = train.groupby(strata)[errors].sum().join(train.groupby(strata).size().rename("n"))
    dev = dev.join(base,on=STRATA,validate="many_to_one")
    dev = dev.join(stratified.add_suffix("_local"),on=strata,validate="many_to_one")
    for name in errors:
        dev[name+"_adjusted"] = (dev[name+"_local"].fillna(0)+8*dev[name])/(dev.n_local.fillna(0)+8)
    for method, suffix in [("ungated",""), ("candidate","_adjusted")]:
        human, ai = dev["human_sq"+suffix], dev["ai_sq"+suffix]
        weight = np.divide(human, human+ai, out=np.full(len(dev),.5), where=(human+ai)>0)
        dev[method] = (1-weight)*dev.human_corrected + weight*dev.ai_corrected
    dev["half"] = .5*(dev.human_corrected+dev.ai_corrected)
    return dev[["writer","task","target_rater","trait","y","discord",*METHODS]]


def run(source, out):
    rows = examples(source)
    scores = pd.concat([fit_predict(rows.loc[rows.writer != w], part) for w,part in rows.groupby("writer")])
    assert len(scores) == 38*2*3*4 and scores.notna().all().all()
    errors = scores[METHODS].sub(scores.y,axis=0).abs().groupby(scores.writer).mean()
    diff = errors.iloc[:,:-1].sub(errors.candidate,axis=0)
    rng = np.random.default_rng(407)
    bs = diff.to_numpy()[rng.integers(len(diff), size=(10000,len(diff)))].mean(axis=1)
    q = .025/diff.shape[1]
    ci = np.quantile(bs,[q,1-q],axis=0).T
    contrasts = {name:dict(gain=float(diff[name].mean()),interval=interval.tolist(),
                           passes=bool(diff[name].mean()>=.05 and interval[0]>0))
                 for name,interval in zip(diff.columns,ci)}
    report = dict(writers=len(diff), forecasts=len(scores)*len(METHODS),targets=len(scores),
                  mae=errors.mean().to_dict(),contrasts=contrasts,advance=all(v["passes"] for v in contrasts.values()))
    out.mkdir(parents=True,exist_ok=True)
    scores.to_csv(out/"forecasts.csv.gz",index=False,compression={"method":"gzip","mtime":0})
    (out/"scores.json").write_text(json.dumps(report,indent=2)+"\n")


if __name__ == "__main__":
    run(*map(Path,sys.argv[1:]))
