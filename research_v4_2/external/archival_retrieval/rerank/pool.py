"""Independently measure fixed candidate-pool recall and the attainable nDCG."""
import argparse
import hashlib
import json
import math
import tarfile
from pathlib import Path


def dcg(count):
    return sum(1/math.log2(j+2) for j in range(min(10,count)))


def audit(archive, inputs):
    with tarfile.open(archive) as f:
        queries={r["id"]:r for line in f.extractfile("data/claims_train.jsonl")
                 if (r:=json.loads(line))["evidence"]}
        documents={r["doc_id"]:r for line in f.extractfile("data/corpus.jsonl") if (r:=json.loads(line))}
    rows=[json.loads(line) for line in inputs.open()]
    assert len(rows)==16*len(queries)
    visited=set()
    summary={}
    for start in range(0,len(rows),16):
        block=rows[start:start+16]
        first=block[0]
        q=queries[first["query"]]
        refs={int(k) for k in q["evidence"]}
        assert q["id"] not in visited and len({b["doc"] for b in block})==16
        visited.add(q["id"])
        for rec in block:
            d=documents[rec["doc"]]
            assert rec["query"]==q["id"] and rec["claim"]==q["claim"]
            assert rec["abstract"]==d["title"]+" "+" ".join(d["abstract"])
            assert rec["hit"]==(d["doc_id"] in refs) and rec["nrel"]==len(refs)
        split="screen" if first["screen"] else "tune"
        obs=summary.setdefault(split,dict(queries=0,annotations=0,shortlisted=0,zero_hit=0,oracle_ndcg10=0.))
        count=len(refs.intersection(r["doc"] for r in block))
        obs["queries"]+=1
        obs["annotations"]+=len(refs)
        obs["shortlisted"]+=count
        obs["zero_hit"]+=int(count==0)
        obs["oracle_ndcg10"]+=dcg(count)/dcg(len(refs))
    assert visited==set(queries)
    for obs in summary.values():obs["oracle_ndcg10"]/=obs["queries"]
    with inputs.open("rb") as f:summary["input_sha256"]=hashlib.file_digest(f,"sha256").hexdigest()
    return summary


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("archive",type=Path)
    p.add_argument("inputs",type=Path)
    args=p.parse_args()
    print(json.dumps(audit(args.archive,args.inputs),indent=2))
