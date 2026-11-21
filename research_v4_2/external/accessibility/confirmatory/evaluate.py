"""Run the frozen rule-transfer experiment on the verified W3C source archive."""
import argparse
import csv
import hashlib
import json
import re
import tarfile
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import binomtest
from sklearn.linear_model import LogisticRegression

REV = "4ce3d61b6f7b04cbf2df0082a3446e97248b9124"
ARCHIVE = "d9f88266ad0a6664b76169ed9d19583441cbaad75629d87ea4e8d115d08898ad"
PROTOCOL = "5340dbb205b964dd3f7e16b60f8a1f0dc18f91fa3bf34266c3761a513dc66abc"
LABELS = ["failed", "passed", "inapplicable"]
OUTCOMES = LABELS + ["cantTell", "untested"]
PRIORITY = ["failed", "cantTell", "passed", "inapplicable", "untested"]
OLD = ["axe-core", "alfa", "equal-access", "qualweb"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dataset(archive):
    if digest(archive.read_bytes()) != ARCHIVE:
        raise ValueError("Source archive hash mismatch")
    prefix = f"wcag-act-rules-{REV}/"
    meta = "_data/wcag-act-rules/"
    assets = "content-assets/wcag-act-rules/"
    files = {}
    with tarfile.open(archive, mode="r|gz") as tar:
        for member in tar:
            path = member.name.removeprefix(prefix)
            if member.isfile() and (path == "wcag-mapping.json" or path.startswith((meta, assets + "testcases"))):
                files[path] = tar.extractfile(member).read()
    read = files.__getitem__
    rules = {r["frontmatter"]["id"]: r for r in json.loads(read("wcag-mapping.json"))["act-rules"]}
    rows = {}
    for r in json.loads(read(assets + "testcases.json"))["testcases"]:
        key = (r["ruleId"], r["testcaseId"])
        assert key not in rows
        raw = read(assets + r["relativePath"])
        normalized = b" ".join(re.sub(rb"<!--.*?-->", b"", raw, flags=re.S).split())
        rows[key] = dict(label=r["expected"], approved=r.get("approved", False),
                         sha256=digest(normalized), output={})

    tools = {}
    prior = set()
    for tool in yaml.safe_load(read(meta + "act-implementations.yml")):
        name = tool["uniqueKey"]
        data = read(meta + "implementations/" + name + ".json")
        report = json.loads(data)
        tools[name] = dict(mode=tool["type"], version=report.get("version"), sha256=digest(data))
        for r in report["actRuleMapping"]:
            rid = r["ruleId"]
            assert not rules[rid]["proposed"] == r["ruleApproved"]
            for case in r["testCaseResults"]:
                key = (rid, case["testcaseId"])
                row = rows[key]
                assert row["label"] == case["expected"] and row["approved"] == case["testCaseApproved"]
                if r["ruleApproved"] and case["testCaseApproved"] and name in OLD:
                    prior.add(rid)
                outcomes = {v for proc in case["procedureResults"] for v in proc["outcomes"]}
                assert outcomes <= set(PRIORITY) and name not in row["output"]
                row["output"][name] = next((v for v in PRIORITY if v in outcomes), "untested")
    approved = {rid for rid, r in rules.items() if not r["proposed"]}
    train = sorted(k for k, r in rows.items() if k[0] in approved and r["approved"] and not rules[k[0]]["deprecated"])
    eligible = sorted(k for k in rows if k[0] not in approved and not rules[k[0]]["deprecated"])
    reference = set(train) | {k for k in rows if k[0] in prior}
    seen_ids = {k[1] for k in reference}
    seen_hashes = {rows[k]["sha256"] for k in reference}
    exclusions = [{"rule": k[0], "id": k[1], "duplicate_id": k[1] in seen_ids,
                   "duplicate_content": rows[k]["sha256"] in seen_hashes} for k in eligible
                  if k[1] in seen_ids or rows[k]["sha256"] in seen_hashes]
    excluded = {(e["rule"], e["id"]) for e in exclusions}
    test = [k for k in eligible if k not in excluded]
    assert not {k[0] for k in test} & (prior | {k[0] for k in train})
    audit = dict(prior_rules=sorted(prior), training_rules=sorted({k[0] for k in train}),
                 test_rules=sorted({k[0] for k in test}), training_cases=len(train),
                 proposed_eligible=len(eligible), test_cases=len(test), exclusions=exclusions,
                 reference_cases=len(reference))
    return rows, tools, train, test, audit


def rule_weights(keys):
    counts = Counter(k[0] for k in keys)
    return np.array([len(keys) / (len(counts) * counts[k[0]]) for k in keys])


def predictions(rows, tools, train, test):
    panel = sorted(t for t, info in tools.items() if info["mode"] in {"Automated tool", "Linter"})
    keys = train + test
    n = len(train)
    gold = np.array([LABELS.index(rows[k]["label"]) for k in train])
    weights = rule_weights(train)
    preds = {t: np.array([OUTCOMES.index(rows[k]["output"].get(t, "untested")) for k in keys]) for t in tools}
    x = np.column_stack([preds[t] for t in panel])
    available = (x != 4).any(axis=1)

    def abstain(values):
        return np.where(available, values, 4)

    feature = (x[:, :, None] == np.arange(5)).reshape(len(keys), -1)
    model = LogisticRegression(C=1, max_iter=2000, tol=1e-9)
    model.fit(feature[:n], gold, sample_weight=weights)
    preds["logistic_fusion"] = abstain(model.predict(feature))
    vote = (x[:, :, None] == np.arange(3))

    def choose(counts):
        return np.where(counts.sum(axis=1) > 0, counts.argmax(axis=1), 4)

    counts = vote.sum(axis=1)
    preds["plurality"] = choose(counts)
    other = counts.copy()
    other[:, 0] = 0
    preds["any_failure"] = np.where(counts[:, 0] > 0, 0, choose(other))
    # A review is an exercised tool that did not vote for failure.
    unanimous = (counts[:, 0] > 0) & (counts[:, 0] == (x != 4).sum(axis=1))
    preds["unanimous_failure"] = np.where(unanimous, 0, choose(other))
    reliability = np.average(x[:n] == gold[:, None], weights=weights, axis=0)
    preds["weighted_vote"] = choose((vote * reliability[None, :, None]).sum(axis=1))
    ranked = x[:, np.argsort(-reliability, kind="stable")]
    preds["ranked_fallback"] = np.where((ranked < 3).any(axis=1),
                                        ranked[np.arange(len(keys)), (ranked < 3).argmax(axis=1)], 4)
    logscore = []
    for cls in range(3):
        w = weights * (gold == cls)
        class_score = np.full(len(keys), np.log((w.sum() + 1) / (n + 3)))
        for i in range(len(panel)):
            freq = 1 + np.bincount(x[:n, i], weights=w, minlength=5)
            class_score += np.log(freq[x[:, i]] / freq.sum())
        logscore.append(class_score)
    preds["naive_bayes"] = abstain(np.argmax(logscore, axis=0))
    best_score = -1
    for size in range(1, len(panel) + 1):
        for subset in combinations(range(len(panel)), size):
            pred = choose(vote[:n, subset].sum(axis=1))
            score = np.average(pred == gold, weights=weights)
            if score > best_score + 1e-12:
                best_score, best = score, subset
    preds["train_selected_plurality"] = choose(vote[:, best].sum(axis=1))
    return {name: p[n:] for name, p in preds.items()}, [panel[i] for i in best]


def accuracy_summary(y, groups, p):
    return dict(exact=int((y == p).sum()), micro=float(np.mean(y == p)),
                macro=float(np.mean([np.mean((y == p)[groups == r]) for r in np.unique(groups)])),
                expected_failures=int((y == 0).sum()), failures_detected=int(((p == 0) & (y == 0)).sum()),
                false_alerts=int(((p == 0) & (y != 0)).sum()))


def analyze(archive, out):
    assert digest(Path(__file__).with_name("protocol.md").read_bytes()) == PROTOCOL
    rows, tools, train, test, audit = dataset(archive)
    preds, subset = predictions(rows, tools, train, test)
    groups = np.array([k[0] for k in test])
    y = np.array([LABELS.index(rows[k]["label"]) for k in test])
    out.mkdir(parents=True, exist_ok=True)
    with (out / "predictions.csv").open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["rule", "testcase", "content_hash", "expected", *preds])
        for i, k in enumerate(test):
            writer.writerow([*k, rows[k]["sha256"], LABELS[y[i]], *(OUTCOMES[p[i]] for p in preds.values())])
    scores = {name: accuracy_summary(y, groups, p) for name, p in preds.items()}
    fusion = preds["logistic_fusion"]
    comparisons = {}
    for name, p in preds.items():
        if name == "logistic_fusion":
            continue
        diffs = [int(np.sum((fusion == y)[groups == r]) - np.sum((p == y)[groups == r])) for r in sorted(set(groups))]
        w = sum(d > 0 for d in diffs)
        l = sum(d < 0 for d in diffs)
        comparisons[name] = dict(delta=scores["logistic_fusion"]["macro"] - scores[name]["macro"],
                                 wins=w, ties=len(diffs)-w-l, losses=l,
                                 p=float(binomtest(w, w+l, alternative="greater").pvalue) if w+l else 1.)
    bound = 0.
    for i, value in enumerate(sorted(comparisons.values(), key=lambda c: c["p"])):
        bound = max(bound, min(1., (len(comparisons)-i)*value["p"]))
        value["holm_p"] = bound
    applicable = [v for k, v in comparisons.items() if tools.get(k, {}).get("mode", "Automated tool") in {"Automated tool", "Linter"}]
    shared = np.logical_and.reduce([preds[t] != 4 for t in OLD])
    result = dict(archive_sha256=ARCHIVE, protocol_sha256=PROTOCOL, audit=audit, reports=tools,
                  best_subset=subset, primary=scores, paired=comparisons, shared_cases=int(shared.sum()),
                  shared_rules=len(set(groups[shared])),
                  shared={name: accuracy_summary(y[shared], groups[shared], p[shared]) for name,p in preds.items()} if shared.any() else {},
                  count=int(all(v["delta"] > 0 and v["holm_p"] < .05 for v in applicable)))
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    analyze(args.archive, args.output)
