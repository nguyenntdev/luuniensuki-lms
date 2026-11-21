"""Recompute Met development membership, labels, stratum counts and paired losses."""
import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path


def verify(source, run):
    with source.open("rb") as handle:
        assert hashlib.file_digest(handle,"sha256").hexdigest()=="f53eb3bd6e321a051ce11ad40bd7f5ee204c6c534cb07508f0f617d03bea0d3a"
    train_families, dev = set(), {}
    training = 0
    with source.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            key = row["Object ID"]
            bucket = int.from_bytes(hashlib.sha256(key.encode()).digest()[:6],"big")%100
            if bucket >= 80:
                continue
            family = row["Object Number"].rpartition(".")[0]
            if bucket < 60:
                training += 1
                if family:
                    train_families.add(family)
            else:
                flag = {"True":1,"False":0}[row["Is Public Domain"]]
                assert key not in dev
                dev[key] = (flag,family)
    receipt = json.loads((run/"summary.json").read_text())
    assert training == receipt["train"]
    seen_ids = set()
    with gzip.open(run/"dev.csv.gz","rt",newline="") as f:
        reader = csv.DictReader(f)
        names = [k for k in reader.fieldnames if k not in ("oid","y")]
        totals = {s:{k:0.0 for k in names} for s in ("all","seen_family","unseen_family")}
        counts = dict.fromkeys(totals,0)
        positives = dict.fromkeys(totals,0)
        for row in reader:
            key = row["oid"]
            assert key not in seen_ids
            seen_ids.add(key)
            y, family = dev[key]
            assert int(row["y"]) == y
            subset = "seen_family" if family in train_families else "unseen_family"
            for s in ("all",subset):
                counts[s] += 1
                positives[s] += y
                for name in names:
                    p = float(row[name])
                    assert math.isfinite(p) and 0 <= p <= 1
                    p = min(1-2**-52, max(2**-52,p))
                    totals[s][name] -= math.log(p) if y else math.log1p(-p)
    assert seen_ids == set(dev)
    means = {s:{k:v/counts[s] for k,v in t.items()} for s,t in totals.items()}
    if "full" in names:
        candidate = "full"
        assert counts["all"] == receipt["development"] and positives["all"] == receipt["positives"]
        summaries = {"all":receipt["loss"]}
    else:
        candidate = "neighbor"
        summaries = {}
        for s, r in receipt["development"].items():
            assert counts[s] == r["n"] and positives[s] == r["positives"]
            summaries[s] = r["loss"]
    for s, scores in summaries.items():
        assert set(scores) == set(names)
        for k in names:
            assert math.isclose(scores[k],means[s][k],abs_tol=1e-10)
    gains = {k:v-means["all"][candidate] for k,v in means["all"].items() if k!=candidate}
    assert receipt["pass_screen"] == all(v >= .005 for v in gains.values())
    if "gain" in receipt:
        assert set(gains) == set(receipt["gain"])
        assert all(abs(v-receipt["gain"][k])<1e-10 for k,v in gains.items())
    return dict(training=training,counts=counts,positives=positives,mean_loss=means,
                all_object_gain=gains,pass_screen=receipt["pass_screen"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("run",type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.source,args.run),indent=2))
