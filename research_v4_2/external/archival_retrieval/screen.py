"""Screen citation retrieval on source-disjoint subsets of the SciFact training release."""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from dense import data


def groups(queries):
    parent = {}
    def root(k):
        parent.setdefault(k,k)
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k=parent[k]
        return k
    links=[]
    for q in queries:
        sources=sorted(set(q["cited_doc_ids"]) | set(map(int,q["evidence"])))
        anchor=root(sources[0])
        for s in sources[1:]:
            parent[root(s)]=anchor
        links.append(sources)
    components=defaultdict(list)
    for s in parent:
        components[root(s)].append(s)
    return [",".join(map(str,sorted(components[root(ss[0])]))) for ss in links]


def bm25(texts, queries, k, b):
    cv=CountVectorizer(token_pattern=r"(?u)\b\w+\b")
    x=cv.fit_transform(texts).astype(np.float32).tocsr()
    length=np.asarray(x.sum(axis=1)).ravel()
    df=np.asarray((x>0).sum(axis=0)).ravel()
    idf=np.log1p((len(texts)-df+.5)/(df+.5))
    norm=k*(1-b+b*length/length.mean())
    x.data=(idf[x.indices]*(k+1)*x.data/(x.data+np.repeat(norm,np.diff(x.indptr)))).astype(np.float32)
    q=cv.transform(queries).astype(bool)
    return (q@x.T).toarray()


def rank(scores):
    order=np.argsort(-scores,axis=1,kind="stable")
    return np.argsort(order,axis=1).astype(np.int32)+1


def evaluate(raw,out):
    docs,all_q=data(raw)
    selected=[i for i,q in enumerate(all_q) if q["evidence"]]
    q=[all_q[i] for i in selected]
    texts=[x["claim"] for x in q]
    # Include the non-evidence rows when constructing source components.
    components=np.array(groups(all_q))[selected]
    screen=np.array([int.from_bytes(hashlib.sha256(s.encode()).digest()[:8],"big")%3==0 for s in components])
    ids={str(x["doc_id"]):i for i,x in enumerate(docs)}
    rows,cols=np.array([(j,ids[d]) for j,x in enumerate(q) for d in x["evidence"]]).T
    ideal=np.array([sum(1/np.log2(np.arange(2,2+min(10,len(x["evidence"]))))) for x in q])
    def metric(r):
        ranks=r[rows,cols]
        return np.bincount(rows,weights=np.where(ranks<=10,1/np.log2(1+ranks),0),minlength=len(q))/ideal
    document=[x["title"]+" "+" ".join(x["abstract"]) for x in docs]
    sentences=[s for x in docs for s in ([x["title"]]+x["abstract"])]
    offsets=np.cumsum([0]+[1+len(x["abstract"]) for x in docs[:-1]])
    scores={}
    tuning={}
    ranks={}
    for name, values in [("document",document),("sentence",sentences)]:
        champion=-1
        for k,b in itertools.product((.6,1.2,1.8),(.25,.75)):
            m=bm25(values,texts,k,b)
            if name=="sentence":
                m=np.maximum.reduceat(m,offsets,axis=1)
            r=rank(m)
            n=metric(r)
            fit=n[~screen].mean()
            if fit>champion:
                champion=fit
                ranks[name]=r
                scores[name]=n
                tuning[name]=[k,b]
    # Match the vectorizer settings in the authors' abstract_retrieval/tfidf.py.
    cv=TfidfVectorizer(stop_words="english",ngram_range=(1,2))
    x=cv.fit_transform(document)
    scores["tfidf"]=metric(rank((cv.transform(texts)@x.T).toarray()))
    def ensemble(name, grids, combine):
        best=-1
        for params in itertools.product(*grids):
            r=rank(combine(*params))
            v=metric(r)
            value=v[~screen].mean()
            if value>best:
                best=value
                tuning[name]=list(params)
                scores[name]=v
    doc,sen=ranks["document"],ranks["sentence"]
    ensemble("lexical_fusion",[(10,60),(.25,.5,1,2)],lambda c,s:1/(c+doc)+s/(c+sen))
    vectors=np.load(raw/"bge_vectors.npy")
    assert vectors.shape==(len(docs)+len(all_q),384)
    dense=rank(vectors[len(docs):][selected]@vectors[:len(docs)].T)
    scores["bge"]=metric(dense)
    ensemble("hybrid",[(10,60),(.5,1,2)],lambda c,d:1/(c+doc)+d/(c+dense))
    ensemble("candidate",[(10,60),(.5,1,2),(.25,.5,1,2)],
             lambda c,d,s:1/(c+doc)+d/(c+dense)+s/(c+sen))
    keys=[name for name in scores if name!="candidate"]
    ledger=pd.DataFrame({"claim":[x["id"] for x in q],"component":components,"screen":screen,**scores})
    obs=ledger[screen]
    out.mkdir(exist_ok=True,parents=True)
    ledger.to_csv(out/"metrics.csv",index=False)
    cluster=obs.groupby("component")[keys+["candidate"]].sum()
    counts=obs.groupby("component").size().to_numpy()
    rng=np.random.default_rng(20261121)
    weight=rng.multinomial(len(counts),np.ones(len(counts))/len(counts),size=5000)
    gain=cluster[["candidate"]].values-cluster[keys].values
    delta=weight@gain/(weight@counts)[:,None]
    bounds=np.quantile(delta,[.025/len(keys),1-.025/len(keys)],axis=0)
    contrasts={key:{"gain":float((obs.candidate-obs[key]).mean()),"ci":bounds[:,i].tolist()} for i,key in enumerate(keys)}
    result=dict(queries=len(q),fit=int((~screen).sum()),screen=int(screen.sum()),components=len(counts),
                documents=len(docs),tuning=tuning,mean=obs[keys+["candidate"]].mean().to_dict(),
                contrasts=contrasts,advance=all(v["gain"]>=.02 and v["ci"][0]>0 for v in contrasts.values()))
    (out/"result.json").write_text(json.dumps(result,indent=2)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("raw",type=Path)
    p.add_argument("out",type=Path)
    args=p.parse_args()
    evaluate(args.raw,args.out)
