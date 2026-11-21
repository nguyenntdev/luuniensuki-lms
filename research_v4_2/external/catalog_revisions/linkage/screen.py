"""Train matched baselines and evaluate the prespecified validation screen."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import f1_score, precision_recall_curve

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("features", type=Path)
parser.add_argument("out", type=Path)
args = parser.parse_args()
args.out.mkdir(exist_ok=True, parents=True)
methods = {"flat":range(5),"aligned":range(25),"matrix":range(85),
           "pooled":[*range(5),*range(85,125)], "candidate":range(125)}
summary = {}
for dataset in ["DBLP-ACM","DBLP-GoogleScholar"]:
    df = pd.read_csv(args.features / f"{dataset}.csv", header=None)
    fit,cal,val = (df[1].eq(k) for k in ["fit","calibration","validation"])
    values, target = df.iloc[:,5:].to_numpy(), df[2].to_numpy()
    assert values.shape[1] == 125
    decisions = df.loc[val,[0,2,3,4]].copy()
    decisions.columns = ["id","label","left_hash","right_hash"]
    training_pairs = set(zip(df.loc[~val,3],df.loc[~val,4]))
    duplicate_pairs = sum((a,b) in training_pairs for a,b in zip(df.loc[val,3],df.loc[val,4]))
    summary[dataset] = dict(fit=int(fit.sum()),calibration=int(cal.sum()),validation=int(val.sum()),
                            validation_positive=int(target[val].sum()), prior_pair_count=duplicate_pairs, models={})
    for method,columns in methods.items():
        X = values[:,columns]
        model = HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=15,learning_rate=.07,
                                                early_stopping=False,l2_regularization=1,random_state=731)
        model.fit(X[fit],target[fit])
        p,r,thresholds = precision_recall_curve(target[cal],model.predict_proba(X[cal])[:,1])
        f = 2*p[:-1]*r[:-1]/np.maximum(1e-20,p[:-1]+r[:-1])
        threshold = float(thresholds[np.flatnonzero(f==f.max())[-1]])
        decisions[method] = (model.predict_proba(X[val])[:,1]>=threshold).astype(int)
        summary[dataset]["models"][method] = dict(threshold=threshold,calibration_f1=float(f.max()),
                                                  f1=float(f1_score(target[val],decisions[method])))
    results = summary[dataset]["models"]
    summary[dataset]["smallest_gain"] = min(results["candidate"]["f1"]-v["f1"] for k,v in results.items() if k!="candidate")
    decisions.to_csv(args.out / f"{dataset}.csv",index=False)
(args.out / "summary.json").write_text(json.dumps(summary,indent=2)+"\n")
