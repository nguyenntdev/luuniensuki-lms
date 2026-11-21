"""Evaluate all matched rerankers on source-disjoint SciFact training queries."""
import argparse
import csv
import itertools
import json
from pathlib import Path

import numpy as np


def rank(values):
    return np.argsort(np.argsort(-values,axis=1,kind="stable"),axis=1)+1


def score(source, outputs, directory):
    rows=[json.loads(s) for s in source.open()]
    with outputs.open() as f:
        predicted=list(csv.DictReader(f))
    assert len(rows)==len(predicted)
    for r,p in zip(rows,predicted):
        assert (r["query"],r["doc"])==(int(p["query"]),int(p["doc"]))
    assert all(len({r["doc"] for r in rows[i:i+16]})==16 and
               len({r["query"] for r in rows[i:i+16]})==1 for i in range(0,len(rows),16))
    queries=rows[::16]
    held=np.asarray([r["screen"] for r in queries])
    y=np.asarray([r["hit"] for r in rows]).reshape(-1,16)
    idcg=np.asarray([sum(1/np.log2(2+np.arange(min(10,r["nrel"])))) for r in queries])
    def metric(r):
        return (y*np.where(r<=10,1/np.log2(r+1),0)).sum(axis=1)/idcg
    doc=np.broadcast_to(np.arange(1,17),(len(queries),16))
    sent=rank(np.array([r["sentence"] for r in rows]).reshape(-1,16))
    ranks=[rank(np.array([float(p[k]) for p in predicted]).reshape(-1,16)) for k in ("abstract","focus")]
    methods={k:metric(r) for k,r in zip(("document","sentence","abstract","focus"),[doc,sent,*ranks])}
    selected={}
    weights=(.5,1.,2.,4.)
    for k, first, second, third in (("doc_full",[1],weights,[0]),("doc_focus",[1],[0],weights),
                                    ("ce_pair",[0],weights,weights),("candidate",[1],weights,weights)):
        best=-1.
        for a,b,c in itertools.product(first,second,third):
            v=metric(rank(a/(10+doc)+b/(10+ranks[0])+c/(10+ranks[1])))
            tune=v[~held].mean()
            if tune>best:
                best=tune
                methods[k]=v
                selected[k]=[a,b,c]
    names=[k for k in methods if k!="candidate"]
    clusters=np.array([r["cluster"] for r in queries])[held]
    unique,idx=np.unique(clusters,return_inverse=True)
    n=np.bincount(idx)
    w=np.random.default_rng(731).multinomial(len(n),np.ones(len(n))/len(n),5000)
    result={}
    for k in names:
        d=(methods["candidate"]-methods[k])[held]
        values=(w@np.bincount(idx,weights=d))/(w@n)
        p=.025/len(names)
        result[k]=dict(gain=d.mean(),ci=np.quantile(values,[p,1-p]).tolist())
    rec=dict(shortlist=16,tune=int((~held).sum()),screen=int(held.sum()),components=len(n),
             pool_recall=float(y[held].sum()/sum(q["nrel"] for q in queries if q["screen"])),
             tuned_weights=selected,mean={k:v[held].mean() for k,v in methods.items()},contrasts=result,
             advance=all(x["gain"]>=.02 and x["ci"][0]>0 for x in result.values()))
    directory.mkdir(exist_ok=True,parents=True)
    with (directory/"metrics.csv").open("w",newline="") as f:
        writer=csv.writer(f,lineterminator="\n")
        writer.writerow(["query","screen","component",*methods])
        writer.writerows((r["query"],int(r["screen"]),r["cluster"],*[v[i] for v in methods.values()])
                         for i,r in enumerate(queries))
    (directory/"result.json").write_text(json.dumps(rec,indent=2)+"\n")
    print(json.dumps(rec))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    for arg in ("source","outputs","directory"):p.add_argument(arg,type=Path)
    a=p.parse_args()
    score(a.source,a.outputs,a.directory)
