"""Replay all per-writer predictions directly from the released analytic scores."""
import csv
import gzip
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

source, run = map(Path, sys.argv[1:])
with source.open() as f:
    raw = list(csv.DictReader(f))
panels = defaultdict(list)
for row in raw:
    panels[row["student_id"],row["task"]].append(row)
report = json.loads((run/"scores.json").read_text())
errors = defaultdict(list)
with gzip.open(run/"forecasts.csv.gz","rt") as f:
    saved = {(r["writer"],r["task"],r["target_rater"],r["trait"]):r for r in csv.DictReader(f)}
for trait, rater in itertools.product(("task_achievement","coherence_cohesion","lexical_resource","grammar_accuracy"),
                                      sorted({r["rater_id"] for r in raw if r["rater_type"]=="Human"})):
    records = {}
    for key, panel in panels.items():
        peer = [float(r[trait]) for r in panel if r["rater_type"]=="Human" and r["rater_id"]!=rater]
        gold, = [float(r[trait]) for r in panel if r["rater_id"]==rater]
        ai = mean(float(r[trait]) for r in panel if r["rater_type"]=="AI")
        records[key] = (gold,mean(peer),ai,min(peer),max(peer))
    for (w,t), (y,h,a,low,high) in records.items():
        train = [(key,v) for key,v in records.items() if key[0]!=w]
        estimates = {"human":h,"ai":a,"low":low,"high":high}
        mse = []
        for i,name in [(1,"human_corrected"), (2,"ai_corrected")]:
            residuals = defaultdict(list)
            for (writer,_),v in train:
                residuals[writer].append(v[0]-v[i])
            total = sum(map(sum,residuals.values()))
            estimates[name] = (h if i==1 else a) + total/(len(train)+8)
            same_task, same_gap = [], []
            for (writer,task),v in train:
                if task != t: continue
                bias = (total-sum(residuals[writer]))/(len(train)-len(residuals[writer])+8)
                sq = (v[0]-v[i]-bias)**2
                same_task.append(sq)
                if (v[4]-v[3]>=1)==(high-low>=1): same_gap.append(sq)
            base = mean(same_task)
            mse.append((base,(sum(same_gap)+8*base)/(len(same_gap)+8)))
        hc, ac = estimates["human_corrected"], estimates["ai_corrected"]
        estimates["half"] = (hc+ac)/2
        for j,model in enumerate(("ungated","candidate")):
            sh,sa = mse[0][j],mse[1][j]
            estimates[model]=(sa*hc+sh*ac)/(sa+sh) if sa+sh else (hc+ac)/2
        row = saved.pop((w,t,rater,trait))
        assert float(row["y"])==y
        for name,p in estimates.items():
            assert math.isclose(p,float(row[name]),abs_tol=1e-12)
            errors[name].append(abs(y-p))
assert not saved and all(math.isclose(mean(v),report["mae"][k]) for k,v in errors.items())
print(json.dumps({"source_panels":len(panels),"methods":len(errors),"forecasts_verified":sum(map(len,errors.values()))}))
