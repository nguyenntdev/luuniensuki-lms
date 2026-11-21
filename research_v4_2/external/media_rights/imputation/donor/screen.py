"""Evaluate label-donor compatibility using only fitting and development records."""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import log_loss

HERE = Path(__file__).resolve().parent
module = importlib.util.spec_from_file_location("met_ordered", HERE.parent/"ordered"/"screen.py")
ordered = importlib.util.module_from_spec(module)
module.loader.exec_module(ordered)

EXTRA = {"medium":"Medium","culture":"Culture","nation":"Artist Nationality",
         "birth":"Artist Begin Date","death":"Artist End Date","acc":"Object Number"}
CATS = ordered.CATEGORIES+["medium","culture","nation"]
NUMERIC = ["begin","end","year","oid","birth","death","acc_index"]


def records(source):
    data = ordered.masking.metadata(source)
    eligible = set(data.oid)
    rows = []
    with source.open(encoding="utf-8-sig",newline="") as handle:
        for r in csv.DictReader(handle):
            oid = int(r["Object ID"])
            if oid in eligible:
                rows.append([oid,*(r[key] for key in EXTRA.values())])
    more = pd.DataFrame(rows,columns=["oid",*EXTRA])
    data = data.merge(more,on="oid",validate="one_to_one")
    for key in ("birth","death"):
        data[key] = pd.to_numeric(data[key].str.split("|",regex=False).str[0].str.strip(),errors="coerce")
    training_acc = np.sort(data.loc[data.bucket.lt(60),"acc"].to_numpy())
    data["acc_index"] = np.searchsorted(training_acc,data.acc.to_numpy())
    # Use integer codes only for equality, never as ordinal model features.
    for key in ("family","artist","dept","class","name","medium"):
        codes = pd.factorize(data[key])[0]
        data["code_"+key] = np.where(data[key].ne(""),codes,-1)
    return data


def donors(ref, query, order):
    sort = ["oid"] if order == "id" else ["acc","oid"]
    ref = ref.sort_values(sort)
    if order == "id":
        pos = np.searchsorted(ref.oid,query.oid)
    else:
        # A sorted union precisely resolves equal accession strings using the ID.
        merged = pd.concat([ref[sort].assign(source=True),query[sort].assign(source=False)]).sort_values(sort)
        ranks = merged.source.astype(int).cumsum()
        pos = ranks[~merged.source].reindex(query.index).to_numpy()
    offsets = np.r_[np.arange(-8,0),np.arange(8)]
    neighbors = pos[:,None]+offsets
    valid = (neighbors>=0)&(neighbors<len(ref))
    ix = np.clip(neighbors,0,len(ref)-1)
    y = ref.y.to_numpy()[ix]
    weight = valid / np.sqrt(np.r_[np.arange(8,0,-1),np.arange(1,9)][None,:])
    prior = ref.y.mean()
    out = {}
    def save(tag,w):
        total = w.sum(axis=1)
        out[order+"_"+tag+"_rate"] = ((w*y).sum(axis=1)+2*prior)/(total+2)
        out[order+"_"+tag+"_count"] = total
    save("plain",weight)
    compatible = weight.copy()
    for key,bonus in [("family",3),("artist",4),("dept",2),("class",2),("name",3),("medium",3)]:
        q = query["code_"+key].to_numpy()[:,None]
        matched = (q>=0)&(q==ref["code_"+key].to_numpy()[ix])
        save(key,weight*matched)
        compatible *= np.where(matched,bonus,1.)
    date_gap = np.abs(query.end.to_numpy()[:,None]-ref.end.to_numpy()[ix])
    compatible *= np.where(date_gap<=3,3.,1.)
    save("compat",compatible)
    return pd.DataFrame(out,index=query.index)


def features(ref,query):
    assert not ref.oid.isin(query.oid).any()
    return pd.concat([ordered.ordered_features(ref,query,"global"),donors(ref,query,"id"),
                      donors(ref,query,"acc")],axis=1)


def run(source,previous,cpu,out):
    data = records(source)
    tr = data[data.bucket<60]
    dev = data[data.bucket>=60]
    design = pd.concat([features(tr[tr.fold!=k],tr[tr.fold==k]) for k in range(5)]
                       +[features(tr,dev)])
    table = data.join(design)
    base = CATS+NUMERIC
    global_cols = [c for c in design if c.startswith("global_")]
    plain = [c for c in design if "_plain_" in c]
    variants = {"metadata":base,"rich_global":base+global_cols,
                "two_orders":base+global_cols+plain,"compatible":base+design.columns.tolist()}
    dev_predictions = dev[["oid","y"]].copy()
    for name,path,col in (("previous_global",previous,"global"),("cpu_neighbor",cpu,"neighbor")):
        saved = pd.read_csv(path).set_index("oid").loc[dev.oid]
        assert np.array_equal(saved.y,dev.y)
        dev_predictions[name] = saved[col].to_numpy()
    dev_predictions["direct_rate"] = table.loc[dev.index,["id_compat_rate","acc_compat_rate"]].mean(axis=1)
    for name,cols in variants.items():
        model = CatBoostClassifier(iterations=350,depth=6,learning_rate=.12,random_seed=73,
            task_type="GPU",devices="0",gpu_ram_part=.32,thread_count=3,cat_features=CATS,
            allow_writing_files=False,verbose=False)
        model.fit(table.loc[tr.index,cols],tr.y)
        assert model.get_all_params()["task_type"]=="GPU"
        dev_predictions[name] = model.predict_proba(table.loc[dev.index,cols])[:,1]
        print(name,"GPU",flush=True)
    scores = {c:log_loss(dev.y,dev_predictions[c]) for c in dev_predictions if c not in ("oid","y")}
    gains = {c:v-scores["compatible"] for c,v in scores.items() if c!="compatible"}
    out.mkdir(exist_ok=True,parents=True)
    dev_predictions.to_csv(out/"dev.csv.gz",index=False,compression={"method":"gzip","mtime":0})
    result = dict(train=len(tr),development=len(dev),loss=scores,gain=gains,
                  pass_screen=all(v>=.005 for v in gains.values()))
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n")


if __name__=="__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("source","previous","cpu","out"):
        p.add_argument(arg,type=Path)
    a = p.parse_args()
    run(a.source,a.previous,a.cpu,a.out)
