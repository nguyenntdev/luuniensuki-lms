"""Check discovery values and top-seven decisions against the released panel."""
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev

source,run=map(Path,sys.argv[1:])
panels=defaultdict(list)
with source.open() as f:
    for r in csv.DictReader(f):
        panels[r["student_id"],r["task"]].append(r)
traits=("task_achievement","coherence_cohesion","lexical_resource","grammar_accuracy")
with (run/"decisions.csv").open() as f:
    data=list(csv.DictReader(f))
summary=json.loads((run/"result.json").read_text())
writers=sorted({w for w,t in panels},key=lambda w:hashlib.sha256(("p11-triage-1:"+w).encode()).hexdigest())
groups=defaultdict(list)
seen=set()
for r in data:
    w,t,target=r["writer"],r["task"],r["target"]
    assert (w,t,target) not in seen
    seen.add((w,t,target))
    panel=panels[w,t]
    groups[(writers.index(w)//19,target)].append(r)
    assert int(r["fold"])==writers.index(w)//19
    assert r["tie"]==hashlib.sha256(f"review-order:{w}:{t}".encode()).hexdigest()
    measures=defaultdict(list)
    for trait in traits:
        a,b=[float(k[trait]) for k in panel if k["rater_type"]=="Human" and k["rater_id"]!=target]
        y,=[float(k[trait]) for k in panel if k["rater_id"]==target]
        ai=[float(k[trait]) for k in panel if k["rater_type"]=="AI"]
        mid=(a+b)/2
        for k,v in (("value",abs(y-mid)),("peer_gap",abs(a-b)),("ai_gap",abs(mean(ai)-mid)),("ai_spread",pstdev(ai))):
            measures[k].append(v)
    for k,l in measures.items():
        assert math.isclose(float(r[k]),mean(l),abs_tol=1e-12)
    assert math.isclose(float(r["equal_gaps"]),(mean(measures["ai_gap"])+mean(measures["peer_gap"]))/2,abs_tol=1e-12)
assert len(seen)==228 and len(groups)==6
for name,expected in summary["mean_discovered"].items():
    discovered=[]
    for pool in groups.values():
        assert len(pool)==38
        if name=="random_expectation":
            discovered.extend([mean(float(r["value"]) for r in pool)]*7)
            continue
        order=sorted(pool,key=lambda r:(-float(r["value" if name=="oracle" else name]),r["tie"]))
        for i,r in enumerate(order):
            assert int(float(r["chosen_"+name]))==int(i<7)
        discovered.extend(float(r["value"]) for r in order[:7])
    assert len(discovered)==42 and math.isclose(mean(discovered),expected)
print(json.dumps({"essay_rotations":len(seen),"ranking_pools":len(groups),"verified_binary_selections":7*len(seen)}))
