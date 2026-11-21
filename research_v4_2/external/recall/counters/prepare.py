"""Build development-only samples and a frozen CPU comparator forecast."""
import argparse
import hashlib
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "confirmatory"))
import study

KEYS = ["user_id", "lexeme", "timestamp"]
PREVIOUS = ["prev_seen", "prev_right", "prev_session", "prev_success", "observed_gap"]
ABILITY = ["learner_residual", "pos_residual", "last_block_residual"]
DELTA = ["excess_seen", "excess_correct", "excess_rate", "clock_difference", "clock_ratio"]


def residuals(f, keys, name):
    blocks = f.groupby(keys + ["timestamp"], sort=True, as_index=False).agg(
        residual_sum=("residual", "sum"), count=("residual", "size"))
    group = blocks.groupby(keys)
    total = group.residual_sum.cumsum() - blocks.residual_sum
    number = group["count"].cumsum() - blocks["count"]
    blocks[name] = total / (10+number)
    cols = [name]
    if len(keys) == 1:
        blocks["block_mean"] = blocks.residual_sum/blocks["count"]
        blocks["last_block_residual"] = blocks.groupby(keys).block_mean.shift()
        cols.append("last_block_residual")
    return f.merge(blocks[keys+["timestamp"]+cols], on=keys+["timestamp"], validate="many_to_one")


def enrich(f):
    prior = f.groupby(KEYS, sort=True, as_index=False).agg(
        prev_seen=("history_seen","min"), high_seen=("history_seen","max"),
        prev_right=("history_correct","min"), high_right=("history_correct","max"),
        prev_session=("session_seen","sum"), prev_success=("session_correct","sum"))
    prior.loc[prior.high_seen!=prior.prev_seen,"prev_seen"] = np.nan
    prior.loc[prior.high_right!=prior.prev_right,"prev_right"] = np.nan
    group = prior.groupby(KEYS[:2],sort=False)
    prior["observed_gap"] = group.timestamp.diff()
    prior[PREVIOUS[:4]] = group[PREVIOUS[:4]].shift()
    f = f.merge(prior[KEYS+PREVIOUS],on=KEYS,validate="many_to_one")
    f["excess_seen"] = f.history_seen - f.prev_seen - f.prev_session
    f["excess_correct"] = f.history_correct - f.prev_right - f.prev_success
    valid = (f.excess_seen>0)&(f.excess_correct>=0)&(f.excess_correct<=f.excess_seen)
    f["excess_rate"] = ((f.excess_correct+4.5)/(f.excess_seen.clip(lower=0)+5)).where(valid)
    f["clock_difference"] = f.observed_gap - f.delta
    f["clock_ratio"] = np.log1p(f.observed_gap)-np.log1p(f.delta)
    f["residual"] = f.gold-f.item_difficulty
    return residuals(residuals(f,["user_id"],ABILITY[0]),["user_id","pos"],ABILITY[1])


def prepare(out):
    assert study.digest(study.ARCHIVE)==json.loads((study.ROOT.parent/"protocol.json").read_text())["dataset_sha256"]
    raw = study.cohort(10,13)
    frames = [study.features(raw[raw.bucket.between(a,b)]) for a,b in [(10,11),(12,12),(13,13)]]
    tr,cal,dev = frames
    lookup=study.lookup(tr)
    folds=tr.user_id.map({u:hashlib.sha256(u.encode()).digest()[4]%5 for u in tr.user_id.unique()})
    for k in range(5):
        tr.loc[folds==k,"item_difficulty"]=study.encode(tr[folds==k],study.lookup(tr[folds!=k]))
    for f in [cal,dev]:
        f["item_difficulty"]=study.encode(f,lookup)
    frozen=study.ROOT/"run"
    seal=json.loads((frozen/"freeze.json").read_text())
    assert study.digest(frozen/"models.pkl")==seal["sha256"]["models.pkl"]
    study.load_reference()
    with (frozen/"models.pkl").open("rb") as fp:
        models, _, _=pickle.load(fp)
    model, coef=models["matched_catboost"]
    dev["earlier_cpu"]=study.calibrated(model.predict_proba(dev[study.RICH+study.CATS],thread_count=2)[:,1],coef)
    cols=study.RICH+study.CATS+PREVIOUS+ABILITY+DELTA
    data=[]
    for frame in frames:
        f=enrich(frame)
        data.append(f[cols+["gold","user_id","bucket"]+(["earlier_cpu"] if frame is dev else [])])
    pd.concat(data,ignore_index=True).to_csv(out,index=False,compression={"method":"gzip","compresslevel":1,"mtime":0})


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("out",type=Path)
    prepare(parser.parse_args().out)
