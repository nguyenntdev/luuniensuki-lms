"""Read-only inference using frozen source equations on a second educational event stream."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from scipy.stats import norm
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parent
FEATURES = ["clicks","days","recency","sites"]
KEYS = ["row","learner","code_module","code_presentation","y"]


def design(frame):
    return np.column_stack((np.ones(len(frame)), np.log1p(frame[FEATURES])/4))


def recover(frame, methods):
    x = design(frame)
    coefficients, _, rank, _ = np.linalg.lstsq(x, logit(frame[methods]), rcond=None)
    assert rank == x.shape[1]
    err = np.abs(expit(x @ coefficients) - frame[methods].to_numpy()).max()
    assert err < 1e-9
    return {name: coef for name,coef in zip(methods, coefficients.T)}, float(err)


def placements(y, pred):
    def midrank(a, b):
        ref = np.sort(b)
        return (ref.searchsorted(a,"left")+ref.searchsorted(a,"right"))/(2*len(ref))
    pos, neg = pred[y],pred[~y]
    return midrank(pos,neg), 1-midrank(neg,pos)


def run(source_rows, stream):
    with stream.open("rb") as f:
        assert hashlib.file_digest(f,"sha256").hexdigest()=="5e29679063c6e416c2ae741d94a8f2b8e996f21e7cbf278488687fb6cb1df15a"
    rows = pd.read_csv(source_rows).query("split=='dev'").reset_index(drop=True)
    parent = pd.read_csv(HERE.parent/"run/predictions.csv.gz",float_precision="round_trip")
    newton = pd.read_csv(HERE.parent/"sufficient_stats/run/predictions.csv.gz",float_precision="round_trip")
    for frame in (parent,newton):
        pd.testing.assert_frame_equal(frame[KEYS],rows[KEYS])
    coefs = json.loads((HERE.parent/"sufficient_stats/run/execution.json").read_text())
    audit = {}
    equations = {}
    for name, archive in (("newton","distributed"),("pooled_newton","pooled")):
        equations[name] = np.array(coefs[archive]["weights"])
        audit[name] = float(np.abs(expit(design(rows) @ equations[name]) - newton[name]).max())
        assert audit[name] < 1e-9
    shared = ["pooled","fedavg","fedprox"]
    private = ["local","intercept_only","weak_ridge","adapted"]
    frame = rows.join(parent[shared+private])
    common, audit["shared"] = recover(frame,shared)
    equations.update(common)
    modules = sorted(frame.code_module.unique())
    for module, group in frame.groupby("code_module"):
        local, audit[module] = recover(group,private)
        equations.update({f"{method}-{module}": w for method,w in local.items()})
    events = pd.read_csv(stream,skiprows=1,header=None,usecols=[0,1,2,3],names=["user","item","time","label"])
    mid = (events.time.min() + events.time.max())/2
    earlier = events.loc[events.time<=mid].copy()
    earlier["day"] = np.floor(earlier.time/86400)
    features = earlier.groupby("user").agg(clicks=("time","size"),days=("day","nunique"),
                                         recency=("day","max"),sites=("item","nunique"))
    features["recency"] = np.floor(mid/86400)-features.recency
    flags = events.loc[events.label==1].groupby("user").time.min().reindex(features.index)
    eligible = flags.isna() | (flags>mid)
    features = features[eligible]
    y = flags[eligible].notna().to_numpy()
    assert (len(y),int(y.sum()))==(3755,1256)
    x = design(features)
    scores = {name:expit(x @ w) for name,w in equations.items()}
    for method in private:
        scores[f"{method}-mean"] = np.mean([scores[f"{method}-{m}"] for m in modules],axis=0)
    # Fixed queue controls use exact event time as in the external queue study.
    gaps = mid-earlier.groupby("user").time.max().reindex(features.index).to_numpy()
    methods = {**scores,"inactivity":gaps,"recent_activity":-gaps,
               "many_actions":features.clicks.to_numpy(),"few_actions":-features.clicks.to_numpy()}
    ref = placements(y,methods["newton"])
    ref_auc = roc_auc_score(y,methods["newton"])
    z = norm.isf(.025/(len(methods)-1))
    results = {}
    for name,pred in methods.items():
        a = roc_auc_score(y,pred)
        values = placements(y,pred)
        assert np.isclose(a,values[0].mean()) and np.isclose(a,values[1].mean())
        se = np.sqrt(sum((v-r).var(ddof=1)/len(r) for v,r in zip(values,ref)))
        gain = ref_auc-a
        results[name] = dict(auc=a, newton_gain=gain, simultaneous_ci95=[gain-z*se,gain+z*se],
                             brier=float(np.square(pred-y).mean()) if name in scores else None)
    return dict(eligible=len(y),cases=int(y.sum()),decision_seconds=mid,
                max_reconstruction_errors=audit,results=results)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_rows",type=Path)
    parser.add_argument("stream",type=Path)
    args=parser.parse_args()
    print(json.dumps(run(args.source_rows,args.stream),indent=2))
