"""Audit the released AE test panel. Pass ae_test.jsonl as the sole argument."""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

data = Path(sys.argv[1]).read_bytes()
assert hashlib.sha256(data).hexdigest() == "7470acdfae03fa662740fb453b508de4e2c4dd1ec113a49142c017d59554202f"
panels = defaultdict(list)
for line in data.splitlines():
    row = json.loads(line)
    assert set(row) == set("candidate context gold_index label qid question raw_rating reference score".split())
    panels[row["qid"], row["candidate"], row["gold_index"]].append(row["score"])

errors = []
for ratings in panels.values():
    if len(ratings) < 2:
        continue
    errors.append(sum(abs(y - (sum(ratings) - y) / (len(ratings) - 1)) for y in ratings) / len(ratings))
print("Panel size frequencies", sorted(Counter(map(len, panels.values())).items()))
print("Equal-item leave-one-rating-out mean absolute error", sum(errors) / len(errors))
