"""Compare four published ACT implementations with distinct availability denominators."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

TOOLS = ["axe-core", "alfa", "equal-access", "qualweb"]
PRIORITY = ["failed", "cantTell", "passed", "inapplicable", "untested"]


def read_report(path):
    data = json.loads(path.read_bytes())
    cases = {}
    for rule in data["actRuleMapping"]:
        if not rule["ruleApproved"]:
            continue
        for case in rule["testCaseResults"]:
            if not case["testCaseApproved"]:
                continue
            key = (rule["ruleId"], case["testcaseId"])
            outcomes = {v for procedure in case["procedureResults"] for v in procedure["outcomes"]}
            if key in cases or outcomes.difference(PRIORITY):
                raise ValueError(f"Invalid procedure outcomes for {key}")
            outcome = next((v for v in PRIORITY if v in outcomes), "untested")
            cases[key] = (case["expected"], outcome)
    return cases


def metrics(keys, labels, outcomes):
    available = [k for k in keys if outcomes.get(k, "untested") != "untested"]
    return dict(n=len(keys), exercised=len(available), exact=sum(labels[k] == outcomes[k] for k in available),
                expected_fail=sum(labels[k] == "failed" for k in keys),
                flagged=sum(outcomes.get(k) == "failed" for k in keys),
                true_fail=sum(labels[k] == outcomes.get(k) == "failed" for k in keys),
                review=sum(outcomes.get(k) == "cantTell" for k in keys))


def compare(root):
    raw = {t: read_report(root / f"{t}.json") for t in TOOLS}
    gold = {}
    for cases in raw.values():
        for key, (expected, _) in cases.items():
            if gold.setdefault(key, expected) != expected:
                raise ValueError(f"Conflicting fixture expectation at {key}")
    predictions = {t: {k: pred for k, (_, pred) in raw[t].items()} for t in TOOLS}
    union = sorted(gold)
    shared = [k for k in union if all(p.get(k, "untested") != "untested" for p in predictions.values())]
    results = {}
    for name, keys in [("union", union), ("shared", shared)]:
        scores = {t: metrics(keys, gold, p) for t, p in predictions.items()}
        results[name] = dict(expectations=dict(Counter(gold[k] for k in keys)),
                             rules=len({k[0] for k in keys}), tools=scores, pairs={})
        for a,b in combinations(TOOLS,2):
            left, right = predictions[a], predictions[b]
            flagged = [k for k in keys if left.get(k) == "failed" or right.get(k) == "failed"]
            results[name]["pairs"][a+" + "+b] = dict(
                flagged=len(flagged), true_fail=sum(gold[k] == "failed" for k in flagged),
                both_failed=sum(left.get(k) == right.get(k) == "failed" for k in keys))
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.source), indent=2))
