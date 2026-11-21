"""Quantify the effect of day-60 risk-set membership on retrospective AUC."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

KEY = ["code_module","code_presentation","id_student"]
FEATURES = ["clicks","days","recency","sites"]
ARCHIVE = "f2ed1902616c1fe8d2824d872c0b7d2d72be435bf0124d077044fe4be2c6d3e4"


def prepare(path):
    with path.open("rb") as source:
        assert hashlib.file_digest(source,"sha256").hexdigest() == ARCHIVE
    with zipfile.ZipFile(path) as archive:
        def read(name):
            with archive.open(name+".csv") as stream:
                return pd.read_csv(stream, na_values=["?"])
        info = read("studentInfo").merge(read("studentRegistration"),on=KEY,validate="one_to_one")
        with archive.open("studentVle.csv") as stream:
            chunks = [c.loc[c.date.between(0,60)] for c in pd.read_csv(stream,chunksize=250000)]
        clicks = pd.concat(chunks).groupby(KEY).agg(clicks=("sum_click","sum"),days=("date","nunique"),
                                                   last=("date","max"),sites=("id_site","nunique"))
    info = info.merge(clicks,on=KEY,how="left",validate="one_to_one")
    info["recency"] = 60-info["last"].fillna(-1)
    info[FEATURES] = info[FEATURES].fillna(0)
    info["outcome"] = info.final_result == "Withdrawn"
    info["eligible"] = info.date_unregistration.isna() | (info.date_unregistration>60)
    return info.loc[info.date_registration <= 60].copy()


def evaluate(path, output):
    frame = prepare(path)
    test = frame.loc[frame.code_presentation == "2014J"].copy()
    train = frame.loc[(frame.code_presentation != "2014J") & ~frame.id_student.isin(test.id_student)]
    out = test[["eligible","outcome"]].copy()
    out["learner"] = pd.factorize(test.id_student,sort=True)[0]
    summary = {"train_rows": len(train), "eligible_train":int(train.eligible.sum()),
               "test_rows":len(test), "eligible_test":int(test.eligible.sum()),"auc":{}}
    for label, fit_rows in [("all",train), ("risk",train[train.eligible])]:
        for name, model in [("logit",make_pipeline(StandardScaler(),LogisticRegression())),
                            ("catboost",CatBoostClassifier(iterations=200,depth=4,learning_rate=.05,
                             random_seed=42,verbose=False,thread_count=2,allow_writing_files=False))]:
            col = name+"_"+label
            model.fit(fit_rows[FEATURES],fit_rows.outcome)
            out[col] = model.predict_proba(test[FEATURES])[:,1]
            summary["auc"][col] = {k:roc_auc_score(f.outcome,f[col]) for k,f in
                                   [("all",out),("eligible",out.loc[out.eligible])]}
    y, p, eligible = (out[k].to_numpy() for k in ("outcome","catboost_all","eligible"))
    users = out.learner.to_numpy()
    rng = np.random.default_rng(42)
    diffs = []
    for _ in range(2000):
        weights = rng.multinomial(users.max()+1,np.full(users.max()+1,1/(users.max()+1)))[users]
        diffs.append(roc_auc_score(y,p,sample_weight=weights)-
                     roc_auc_score(y[eligible],p[eligible],sample_weight=weights[eligible]))
    summary["all_minus_eligible_catboost_ci95"] = np.quantile(diffs,[.025,.975]).tolist()
    output.mkdir(parents=True,exist_ok=True)
    out.to_csv(output/"predictions.csv.gz",index=False,compression={"method":"gzip","mtime":0})
    (output/"result.json").write_text(json.dumps(summary,indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive",type=Path)
    parser.add_argument("output",type=Path)
    args = parser.parse_args()
    evaluate(args.archive,args.output)
