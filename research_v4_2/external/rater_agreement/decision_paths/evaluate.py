"""Score anonymous second judgments under a frozen, question-disjoint transfer."""
import hashlib
import itertools
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

TEST = "7470acdfae03fa662740fb453b508de4e2c4dd1ec113a49142c017d59554202f"
DEV = "9ec7b8f1136a0363753fbbde0d73c32e5cf26551938378eda27d1c860743cd9f"


def load(filename, digest):
    data = Path(filename).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest
    panels = defaultdict(list)
    for line in data.splitlines():
        row = json.loads(line)
        key = row["qid"], row["candidate"], row["gold_index"]
        vote = row["score"]
        assert vote in (0, 1)
        panels[key].append((tuple(row["raw_rating"]), int(vote)))
    return panels


def fit(panels):
    mass, total = Counter(), Counter()
    for votes in panels.values():
        n = len(votes)
        if n < 2:
            continue
        weight = 1 / (n * (n - 1))
        for (path, x), (_, y) in itertools.permutations(votes, 2):
            for key in ("all", x, path):
                mass[key] += weight
                total[key] += weight * y
    return mass, total


def score(train, test):
    mass, total = fit(train)
    excluded = {key[0] for key in train}
    losses = defaultdict(list)
    counts = Counter()
    for (qid, _, _), votes in test.items():
        if len(votes) < 2 or qid in excluded:
            continue
        counts["items"] += 1
        item_losses = defaultdict(list)
        for (path, x), (_, y) in itertools.permutations(votes, 2):
            counts["ordered_pairs"] += 1
            binary = total[x] / mass[x]
            raw = total[path] / mass[path] if mass[path] else binary
            predictions = {
                "smoothed_path": (total[path] + 2 * binary) / (mass[path] + 2),
                "path": raw, "binary_transition": binary, "vote": x,
                "marginal": total["all"] / mass["all"],
            }
            for method, forecast in predictions.items():
                p = min(.99, max(.01, forecast))
                item_losses[method, "brier"].append((p - y)**2)
                item_losses[method, "log"].append(-math.log(p if y else 1 - p))
        for key, values in item_losses.items():
            losses[key].append((qid, mean(values)))
    questions = {key[0] for key in test}
    result = {"all_dev_questions": len(questions), "questions_overlapping_train": len(questions & excluded),
              **counts, "methods": {}}
    for (method, metric), rows in losses.items():
        paired = defaultdict(list)
        for (qid, value), (ref_qid, candidate) in zip(rows, losses["smoothed_path", metric], strict=True):
            assert qid == ref_qid
            paired[qid].append(candidate - value)
        n, g = len(rows), len(paired)
        delta = sum(map(sum, paired.values())) / n
        residual = sum((sum(v) - len(v)*delta)**2 for v in paired.values())
        se = math.sqrt(g/(g-1)*residual)/n
        result["scored_questions"] = g
        result["methods"].setdefault(method, {})[metric] = dict(
            loss=mean(v for _, v in rows), difference=delta, interval=[delta-1.96*se, delta+1.96*se])
    return result


if __name__ == "__main__":
    print(json.dumps(score(load(sys.argv[1], TEST), load(sys.argv[2], DEV)), indent=2))
