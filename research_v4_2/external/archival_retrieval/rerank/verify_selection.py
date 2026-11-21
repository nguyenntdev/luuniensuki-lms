"""Audit all fit-only rank-fusion settings and clustered intervals from pair scores."""
import csv
import hashlib
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


def one(values):
    order=sorted(range(len(values)),key=lambda i:(-values[i],i))
    result=[0]*len(order)
    for rank,i in enumerate(order,1):result[i]=rank
    return result


def audit(inputs, output):
    with inputs.open() as f:data=[json.loads(line) for line in f]
    with (output/"scores.csv").open() as f:scores=list(csv.DictReader(f))
    decision=json.loads((output/"result.json").read_text())
    totals=defaultdict(float)
    screens=[]
    weights=(.5,1,2,4)
    grid={"doc_full":list(itertools.product((1,),weights,(0,))),
          "doc_focus":list(itertools.product((1,),(0,),weights)),
          "ce_pair":list(itertools.product((0,),weights,weights)),
          "candidate":list(itertools.product((1,),weights,weights))}
    settings=set(s for rows in grid.values() for s in rows)
    for start in range(0,len(data),16):
        block=data[start:start+16]; first=block[0]; rows=scores[start:start+16]
        early=first["cluster"]
        assigned=int.from_bytes(hashlib.sha256(early.encode()).digest()[:8],"big")%3==0
        assert assigned==first["screen"]
        gold=[j for j,r in enumerate(block) if r["hit"]]
        norm=sum(1/math.log2(i+2) for i in range(min(10,first["nrel"])))
        def ndcg(ranks):
            return sum(1/math.log2(ranks[i]+1) for i in gold if ranks[i]<=10)/norm
        abstract, focus=[one([float(p[k]) for p in rows]) for k in ("abstract","focus")]
        doc=list(range(1,17))
        def fusion(s):
            a,b,c=s
            return ndcg(one([a/(10+d)+b/(10+u)+c/(10+v) for d,u,v in zip(doc,abstract,focus)]))
        if not assigned:
            for s in settings:totals[s]+=fusion(s)
        else:
            screens.append((early,{"abstract":ndcg(abstract),"focus":ndcg(focus),"document":ndcg(doc),
                                  "sentence":ndcg(one([r["sentence"] for r in block])),
                                  **{k:fusion(v) for k,v in decision["tuned_weights"].items()}}))
    for method,g in grid.items():
        choice=tuple(decision["tuned_weights"][method])
        assert choice in g and abs(totals[choice]-max(totals[s] for s in g))<1e-10
    groups=sorted(set(s for s,_ in screens))
    assert len(groups)==decision["components"]
    draws=np.random.default_rng(731).multinomial(len(groups),[1/len(groups)]*len(groups),5000)
    n=np.asarray([sum(key==s for key,_ in screens) for s in groups])
    passes=[]
    for k,reported in decision["contrasts"].items():
        sums=np.array([sum(r["candidate"]-r[k] for group,r in screens if group==s) for s in groups])
        samples=np.sum(draws*sums,axis=1)/np.sum(draws*n,axis=1)
        alpha=.025/len(decision["contrasts"])
        ci=np.quantile(samples,[alpha,1-alpha])
        assert np.allclose(ci,reported["ci"],atol=1e-12)
        gain=sums.sum()/n.sum()
        assert abs(gain-reported["gain"])<1e-12
        passes.append(bool(gain>=.02 and ci[0]>0))
    assert all(passes)==decision["advance"]
    return dict(queries=len(data)//16,screen=len(screens),components=len(groups),
                settings_checked={k:len(g) for k,g in grid.items()},
                margin_passes=sum(passes),comparisons=len(passes))


if __name__=="__main__":
    print(json.dumps(audit(Path(sys.argv[1]),Path(sys.argv[2])),indent=2))
