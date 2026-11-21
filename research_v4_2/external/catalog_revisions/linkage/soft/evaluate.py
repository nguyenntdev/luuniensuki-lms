"""Fit the ordered and assignment ablations with calibration-only thresholds."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_curve


def score(y, probability, role):
    cal, val = role == "calibration", role == "validation"
    p,r,cut = precision_recall_curve(y[cal],probability[cal])
    curve = 2*p[:-1]*r[:-1]/np.maximum(1e-20,p[:-1]+r[:-1])
    threshold = cut[np.flatnonzero(curve==curve.max())[-1]]
    predictions = (probability[val]>=threshold).astype(int)
    tn,fp,fn,tp = confusion_matrix(y[val],predictions).ravel().tolist()
    return predictions, dict(threshold=float(threshold), calibration_f1=float(curve.max()),
                             f1=float(f1_score(y[val],predictions)), tp=tp,fp=fp,fn=fn,tn=tn)


def run(work, out, dataset):
    previous_dir = Path(__file__).resolve().parent.parent / "run"
    old_dev = pd.read_csv(previous_dir / f"{dataset}.csv")
    previous_summary = json.loads((previous_dir / "summary.json").read_text())[dataset]
    original = pd.read_csv(work / f"{dataset}.csv",header=None)
    role,y = original[1].to_numpy(),original[2].to_numpy()
    fit,val = role=="fit",role=="validation"
    assert old_dev.id.tolist()==original.loc[val,0].tolist()
    decisions = old_dev.iloc[:,:4].copy()
    x = original.iloc[:,5:].to_numpy()
    soft = np.load(work / f"{dataset}-soft.npy")
    assert soft.shape == (len(role),60)
    char,flat,assignment,prefix = np.split(soft, [20,23,55],axis=1)
    published = np.atleast_1d(np.loadtxt(work / f"{dataset}-published.csv"))
    assert published.shape==(len(role),) and np.isfinite(published).all()
    models = {}
    for name in previous_summary["models"]:
        key = "original_"+name
        values = old_dev[name]
        tn,fp,fn,tp = confusion_matrix(y[val],values).ravel().tolist()
        models[key] = {**previous_summary["models"][name], "tp":tp,"fp":fp,"fn":fn,"tn":tn}
        decisions[key] = values
    decisions["secondstring"], models["secondstring"] = score(y,published,role)
    decisions["p_secondstring"] = published[val]
    matrices = dict(char=[x,char],flat_soft=[x,char,flat],assignment=[x,char,flat,assignment],
                    ordered=[x,char,flat,prefix],candidate=[x,char,flat,assignment,prefix])
    for name,parts in matrices.items():
        matrix = np.column_stack(parts)
        model = HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=15,learning_rate=.07,
                                               early_stopping=False,l2_regularization=1,random_state=731)
        model.fit(matrix[fit], y[fit])
        scores = model.predict_proba(matrix)[:,1]
        decisions[name], models[name] = score(y,scores,role)
        decisions["p_"+name] = scores[val]
    decision = decisions["candidate"].to_numpy()
    competitors = {}
    for name in models:
        if name=="candidate":
            continue
        other = decisions[name].to_numpy()
        competitors[name] = dict(gain=models["candidate"]["f1"]-models[name]["f1"],
                                 fixed=int(((decision==y[val]) & (other!=y[val])).sum()),
                                 lost=int(((decision!=y[val]) & (other==y[val])).sum()))
    worst = min(competitors, key=lambda k: competitors[k]["gain"])
    out.mkdir(parents=True, exist_ok=True)
    decisions.to_csv(out / f"{dataset}.csv",index=False)
    result = dict(fit=int(fit.sum()),calibration=int((role=="calibration").sum()),validation=int(val.sum()),
                  models=models, contrasts=competitors, strongest_competitor=worst,
                  smallest_gain=competitors[worst]["gain"], passes_one_point=competitors[worst]["gain"]>=.01)
    print(dataset, models["candidate"]["f1"], worst, result["smallest_gain"], flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    parser.add_argument("out", type=Path)
    args=parser.parse_args()
    result = {d:run(args.work,args.out,d) for d in ["DBLP-ACM","DBLP-GoogleScholar"]}
    (args.out / "summary.json").write_text(json.dumps(result,indent=2)+"\n")
