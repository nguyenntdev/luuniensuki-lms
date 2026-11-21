"""Prepare equal BM25 shortlists without reading any official evaluation file."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from screen import bm25, data, groups


def prepare(raw, output):
    corpus, claims = data(raw)
    elig = [i for i,q in enumerate(claims) if q["evidence"]]
    queries = [claims[i]["claim"] for i in elig]
    text = [d["title"]+" "+" ".join(d["abstract"]) for d in corpus]
    ranks = np.argsort(-bm25(text,queries,1.2,.75),axis=1,kind="stable")[:,:16]
    sentences = [s for d in corpus for s in d["abstract"]]
    offsets = np.cumsum([0]+[len(d["abstract"]) for d in corpus])
    strength = bm25(sentences,queries,1.2,.75)
    clusters = groups(claims)
    with output.open("w") as out:
        for n,i in enumerate(elig):
            q = claims[i]
            digest = hashlib.sha256(clusters[i].encode()).digest()
            for j in ranks[n]:
                d = corpus[j]
                assert d["abstract"]
                local = strength[n,offsets[j]:offsets[j+1]]
                chosen = sorted(np.argsort(-local,kind="stable")[:3])
                entry = dict(query=q["id"],doc=d["doc_id"],claim=q["claim"],abstract=text[j],
                             focus=d["title"]+" "+" ".join(d["abstract"][s] for s in chosen),
                             sentence=float(local.max()),cluster=clusters[i],
                             screen=int.from_bytes(digest[:8],"big")%3==0,
                             hit=str(d["doc_id"]) in q["evidence"],nrel=len(q["evidence"]))
                print(json.dumps(entry,ensure_ascii=False),file=out)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("raw",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    prepare(args.raw,args.output)
