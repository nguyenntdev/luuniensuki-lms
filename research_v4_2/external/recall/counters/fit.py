"""Fit all approaches on aligned development data and retain per-learner loss."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from scipy.optimize import minimize
from scipy.special import expit,logit
from scipy.stats import t

RICH = ["log_days","log_right","log_wrong","item_history_rate","log_gap","prior_user","recent_user",
        "last_user","log_user_exposure","prior_item","last_item","log_item_exposure","hour_sin","hour_cos","item_difficulty"]
CATS = ["lexeme","course","lemma","pos"]
PRIMITIVE = ["prev_seen","prev_right","prev_session","prev_success","observed_gap"]
ABILITY = ["learner_residual","pos_residual","last_block_residual"]
DIFF = ["excess_seen","excess_correct","excess_rate","clock_difference","clock_ratio"]


def loss(y,p):
    p=np.clip(p,1e-8,1-1e-8)
    return -y*np.log(p)-(1-y)*np.log1p(-p)


def calibrate(cal,pred,w):
    logits=[logit(np.clip(p,1e-8,1-1e-8)) for p in pred]
    def objective(v):
        return np.average(loss(cal.gold,expit(v[0]+v[1]*logits[0])),weights=w)
    fitted=minimize(objective,[0.,1.],method="L-BFGS-B",bounds=[(-10,10),(0,10)])
    assert fitted.success
    c=min(([0.,1.],fitted.x),key=objective)
    return expit(c[0]+c[1]*logits[1]),list(c)


def run(source,out):
    data=pd.read_csv(source,compression="gzip",float_precision="round_trip",keep_default_na=False,
                     na_values={k:[""] for k in PRIMITIVE+DIFF+ABILITY+["earlier_cpu"]})
    train=data[data.bucket<12]
    cal=data[data.bucket==12]
    dev=data[data.bucket==13]
    assert set(data.bucket.unique())=={10,11,12,13}
    w=1/cal.groupby("user_id").user_id.transform("size")
    forecasts={"previous_cpu":dev.earlier_cpu.to_numpy()}
    fit_coef={}
    forecasts["simple_rate"],fit_coef["simple_rate"]=calibrate(cal,[f.item_history_rate.to_numpy() for f in (cal,dev)],w)
    for name,extra in {"previous_gpu":[], "counter_inputs":PRIMITIVE,"ability":ABILITY,
                       "matched":PRIMITIVE+ABILITY,"reconciled":PRIMITIVE+ABILITY+DIFF}.items():
        cols=RICH+CATS+extra
        model=CatBoostClassifier(loss_function="CrossEntropy",iterations=500,depth=6,learning_rate=.05,
                                 thread_count=2,random_seed=42,cat_features=CATS,task_type="GPU",
                                 devices="0",gpu_ram_part=.32,verbose=False,allow_writing_files=False)
        model.fit(train[cols],train.gold)
        assert model.get_all_params()["task_type"]=="GPU"
        pred=[model.predict_proba(f[cols],thread_count=2)[:,1] for f in (cal,dev)]
        forecasts[name],fit_coef[name]=calibrate(cal,pred,w)
        print(name,flush=True)
    losses=pd.DataFrame({k:loss(dev.gold,p) for k,p in forecasts.items()}).groupby(dev.user_id).mean()
    ids=dev.user_id.map({v:i for i,v in enumerate(losses.index)})
    out.mkdir(parents=True,exist_ok=True)
    with gzip.GzipFile(str(out/"forecasts.csv.gz"),"wb",mtime=0) as handle:
        pd.DataFrame(dict(learner=ids,y=dev.gold,**forecasts)).to_csv(handle,index=False)
    other=losses.drop(columns="reconciled").sub(losses.reconciled,axis=0)
    n=len(other)
    threshold=t.isf(.025/other.shape[1],n-1)
    means=other.mean()
    half=threshold*other.sem()
    ci={k:[means[k]-half[k],means[k]+half[k]] for k in other}
    result=dict(rows=len(dev),learners=n,training=len(train),calibration=len(cal),mean_learner_loss=losses.mean().to_dict(),
                cal_coefficients=fit_coef,gains=means.to_dict(),simultaneous_ci95=ci,
                advance=all(means[k]>=.005 and ci[k][0]>0 for k in other))
    (out/"result.json").write_text(json.dumps(result,indent=2)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("source", type=Path);p.add_argument("out",type=Path)
    args=p.parse_args()
    run(args.source,args.out)
