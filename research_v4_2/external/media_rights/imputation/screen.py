"""Artificial masking development experiment. The reserved flags are never accessed."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import log_loss


def metadata(path):
    digest = "f53eb3bd6e321a051ce11ad40bd7f5ee204c6c534cb07508f0f617d03bea0d3a"
    with path.open("rb") as f:
        assert hashlib.file_digest(f,"sha256").hexdigest()==digest
    records = []
    with path.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            oid = row["Object ID"]
            h = int(hashlib.sha256(oid.encode()).hexdigest()[:12],16)
            bucket = h%100
            if bucket>=80:
                continue
            key = row["Object Number"].rpartition(".")[0]
            artist = row["Constituent ID"].split("|")[0].strip()
            flag = row["Is Public Domain"].lower()
            assert flag in {"true","false"}
            records.append([int(oid),bucket,(h//100)%5,int(flag=="true"),key,artist,
                row["Department"],row["Classification"],row["Object Name"],
                row["AccessionYear"][:4],row["Object Begin Date"],row["Object End Date"]])
    data = pd.DataFrame(records,columns=["oid","bucket","fold","y","family","artist","dept","class","name","year","begin","end"])
    assert data.oid.is_unique
    for col in ("year","begin","end"):
        data[col]=pd.to_numeric(data[col],errors="coerce")
    data["joint"] = (data.family+"\t"+data.artist).where(data.family.ne("") & data.artist.ne(""),"")
    return data


def neighbors(fit, query):
    features = {}
    prior = fit.y.mean()
    for key in ("family","artist","joint"):
        known=fit[fit[key].ne("")].sort_values("oid")
        counts=known.groupby(key).y.agg(["sum","count"])
        n=query[key].map(counts["count"]).fillna(0)
        total=query[key].map(counts["sum"]).fillna(0)
        features[key+"_rate"]=(total+8*prior)/(n+8)
        features[key+"_count"]=np.log1p(n)
        # Nearest catalog ID is an acquisition proxy. It uses no held-out labels.
        a=query.loc[query[key].ne(""),["oid",key]].sort_values("oid")
        b=known[["oid",key,"y"]].rename(columns={"oid":"source_id"})
        closest=pd.merge_asof(a,b,by=key,left_on="oid",right_on="source_id",direction="nearest")
        closest.index=a.index
        features[key+"_neighbor"]=closest.y.reindex(query.index).fillna(prior)
        features[key+"_distance"]=np.log1p((closest.oid-closest.source_id).abs()).reindex(query.index)
    return pd.DataFrame(features,index=query.index)


def run(source, out, device="CPU"):
    data = metadata(source)
    train=data[data.bucket<60]; dev=data[data.bucket>=60]
    ex=pd.concat([neighbors(train[train.fold!=k],train[train.fold==k]) for k in range(5)]+[neighbors(train,dev)])
    table=data.join(ex)
    cats=["family","artist","dept","class","name"]
    base=cats+["begin","end","year"]
    means=["family_rate","family_count","artist_rate","artist_count"]
    preds={"family_rate":table.loc[dev.index,"family_rate"].to_numpy()}
    for name, cols in [("catboost",base),("pooled",base+means),("neighbor",base+list(ex.columns))]:
        model=CatBoostClassifier(iterations=350,depth=6,learning_rate=.12,thread_count=3,random_seed=73,
                                 allow_writing_files=False,verbose=False,cat_features=cats,task_type=device)
        model.fit(table.loc[train.index,cols],train.y)
        assert model.get_all_params()["task_type"] == device
        print(f"{name} fitted on {device}", flush=True)
        preds[name]=model.predict_proba(table.loc[dev.index,cols])[:,1]
    seen=table.loc[dev.index,"family_count"].to_numpy()>0
    summary={}
    for subset,keep in [("all",np.ones(len(dev),dtype=bool)),("seen_family",seen),("unseen_family",~seen)]:
        summary[subset]=dict(n=int(keep.sum()), positives=int(dev.y.to_numpy()[keep].sum()),
                loss={name:float(log_loss(dev.y.to_numpy()[keep],p[keep],labels=[0,1])) for name,p in preds.items()})
    out.mkdir(parents=True,exist_ok=True)
    dev[["oid","y"]].assign(**preds).to_csv(out/"dev.csv.gz",index=False,compression={"method":"gzip","mtime":0})
    losses=summary["all"]["loss"]
    receipt=dict(device=device,train=len(train),development=summary,pass_screen=all(losses[k]-losses["neighbor"]>=.005 for k in preds if k!="neighbor"))
    (out/"summary.json").write_text(json.dumps(receipt,indent=2)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("--device", choices=["CPU","GPU"], default="CPU")
    a=p.parse_args()
    run(a.source,a.out,a.device)
