"""Cross-fitted prediction of anonymous binary panel judgments."""
import hashlib
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

data = Path(sys.argv[1]).read_bytes()
assert hashlib.sha256(data).hexdigest() == "7470acdfae03fa662740fb453b508de4e2c4dd1ec113a49142c017d59554202f"
panels = defaultdict(list)
for line in data.splitlines():
    row = json.loads(line)
    panels[row["qid"], row["candidate"], row["gold_index"]].append(row["score"])
items = []
for (qid, _, _), votes in panels.items():
    if len(votes) >= 2:
        fold = int(hashlib.sha256(str(qid).encode()).hexdigest(), 16) % 5
        items.append((fold, qid, list(itertools.permutations(votes, 2))))

scores = defaultdict(list)
fits = []
for fold in range(5):
    train = [pairs for f, _, pairs in items if f != fold]
    m = mean(mean(x for x, y in pairs) for pairs in train)
    t = mean(mean(x*y for x, y in pairs) for pairs in train)
    r = max(0, min(1, (t-m*m)/(m*(1-m))))
    fits.append(dict(fold=fold, mean=m, weight=r, training_items=len(train)))
    for f, qid, pairs in items:
        if f != fold:
            continue
        losses = defaultdict(list)
        for x, y in pairs:
            for model, p in dict(eb=m+r*(x-m), vote=x, prior=m,
                                 fixed=(x+2*m)/3, laplace=(x+1)/3).items():
                p = max(.01, min(.99, p))
                losses[model, "brier"].append((p-y)**2)
                losses[model, "log"].append(-math.log(p if y else 1-p))
        for key, values in losses.items():
            scores[key].append((qid, mean(values)))

out = {}
for (model, metric), rows in scores.items():
    clusters = defaultdict(list)
    for (qid, value), (other, eb) in zip(rows, scores["eb", metric], strict=True):
        assert qid == other
        clusters[qid].append(eb-value)
    n = len(rows)
    g = len(clusters)
    delta = sum(map(sum, clusters.values()))/n
    se = math.sqrt(g/(g-1)*sum((sum(v)-len(v)*delta)**2 for v in clusters.values()))/n
    out[model+"_"+metric] = dict(score=mean(v for _, v in rows), delta=delta,
                                 interval=[delta-1.96*se, delta+1.96*se])
print(json.dumps(dict(items=n, questions=g, fits=fits, results=out), indent=2))
