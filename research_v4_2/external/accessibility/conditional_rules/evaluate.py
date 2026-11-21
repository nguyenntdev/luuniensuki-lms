"""Evaluate pairwise fusion on the existing public ACT rule-transfer partition."""

import argparse
import csv
import hashlib
import importlib.util
import json
import warnings
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "confirmatory"
PROTOCOL_SHA = "5293369babae433f744aaa654b3d6dd794e189931d140ee8b25827035104228b"
EVALUATOR_SHA = "54d1e0d2d99d058579c4afe427724f5f0982efc05db228b4cb1b11be78110553"
PREDICTIONS_SHA = "358c30b1035f919d295a1c895f12ac395e1f1a8c8faee4b1cd7767cbf3324d31"
UNTESTED = 4
PRIMARY = "paired_outcomes"
REFERENCES = ("logistic_fusion", "naive_bayes")
DRAWS = 50_000


def verify_hash(path, expected):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"SHA-256 mismatch for {path.name}")


def load_prior():
    verify_hash(HERE / "protocol.md", PROTOCOL_SHA)
    if (HERE / "protocol.sha256").read_text().strip() != PROTOCOL_SHA:
        raise ValueError("Protocol checksum record differs from evaluator")
    source = PRIOR / "evaluate.py"
    verify_hash(source, EVALUATOR_SHA)
    verify_hash(PRIOR / "predictions.csv", PREDICTIONS_SHA)
    spec = importlib.util.spec_from_file_location("act_confirmatory", source)
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    return prior


def verify_split(rows, train, test):
    for train_values, test_values, field in (
        ({k[0] for k in train}, {k[0] for k in test}, "rule ID"),
        ({k[1] for k in train}, {k[1] for k in test}, "testcase ID"),
        ({rows[k]["sha256"] for k in train}, {rows[k]["sha256"] for k in test},
         "normalized content hash"),
    ):
        if train_values & test_values:
            raise ValueError(f"Training/test overlap by {field}")


def validate_release(rows, test, frozen, prior):
    with (PRIOR / "predictions.csv").open(newline="") as file:
        released = csv.DictReader(file)
        columns = ["rule", "testcase", "content_hash", "expected", *frozen]
        if released.fieldnames != columns:
            raise ValueError("Released columns differ from reproduced prior evaluation")
        for i, (key, row) in enumerate(zip(test, released, strict=True)):
            expected = (
                *key, rows[key]["sha256"], rows[key]["label"],
                *(prior.OUTCOMES[values[i]] for values in frozen.values()),
            )
            if tuple(row[name] for name in columns) != expected:
                raise ValueError(f"Released labels or predictions differ for {key}")


def feature_blocks(outcomes):
    categories = np.arange(UNTESTED + 1)
    indicators = outcomes[:, :, None] == categories
    pairs = np.array(list(combinations(range(outcomes.shape[1]), 2)))
    left, right = pairs.T
    pair_categories = categories[:, None] * len(categories) + categories
    observed = (categories[:, None] != UNTESTED) & (categories != UNTESTED)
    pair_codes = outcomes[:, left] * len(categories) + outcomes[:, right]
    main = indicators.reshape(len(outcomes), -1)
    return main, {
        PRIMARY: (pair_codes[:, :, None] == pair_categories[observed]).reshape(len(main), -1),
        "missingness_interactions": (
            pair_codes[:, :, None] == pair_categories[~observed]
        ).reshape(len(main), -1),
    }


def interaction_predictions(rows, reports, train, test, prior):
    panel = sorted(name for name, report in reports.items()
                   if report["mode"] in {"Automated tool", "Linter"})
    outcomes = np.array([
        [prior.OUTCOMES.index(rows[k]["output"].get(name, "untested")) for name in panel]
        for k in train + test
    ])
    gold = [prior.LABELS.index(rows[k]["label"]) for k in train]
    weights = prior.rule_weights(train)
    n = len(train)
    exercised = (outcomes[n:] != UNTESTED).sum(axis=1)
    main, blocks = feature_blocks(outcomes)
    features = {
        PRIMARY: (main, blocks[PRIMARY]),
        "missingness_interactions": (main, blocks["missingness_interactions"]),
        "full_interactions": (main, *blocks.values()),
    }
    predictions = {}
    for name, feature in features.items():
        x = np.column_stack(feature)
        model = LogisticRegression(C=1, tol=1e-9, max_iter=2000)
        model.fit(x[:n], gold, sample_weight=weights)
        predictions[name] = np.where(exercised > 0, model.predict(x[n:]), UNTESTED)
    return predictions, panel, outcomes[n:], exercised, {
        "logistic_fusion": main.shape[1],
        **{name: sum(block.shape[1] for block in feature) for name, feature in features.items()},
    }


def rule_components(rows, test):
    neighbors = {rule: {rule} for rule, _ in test}
    by_identity = defaultdict(set)
    for rule, testcase in test:
        by_identity["testcase", testcase].add(rule)
        by_identity["content", rows[rule, testcase]["sha256"]].add(rule)
    for shared in by_identity.values():
        for rule in shared:
            neighbors[rule].update(shared)
    components = []
    unseen = set(neighbors)
    while unseen:
        pending = {min(unseen)}
        component = set()
        while pending:
            rule = pending.pop()
            component.add(rule)
            pending.update(neighbors[rule] - component)
        unseen -= component
        components.append(sorted(component))
    return components


def bootstrap(per_rule_deltas, blocks, seed):
    """Use common samples for all contrasts and weight rules equally within a draw."""
    block_sums = np.array([per_rule_deltas[block].sum(axis=0) for block in blocks])
    sizes = np.array([len(block) for block in blocks])
    random = np.random.Generator(np.random.PCG64(seed))
    sampled = random.integers(len(blocks), size=(DRAWS, len(blocks)))
    means = block_sums[sampled].sum(axis=1) / sizes[sampled].sum(axis=1)[:, None]
    return np.quantile(means, [0.0125, 0.9875], axis=0, method="linear").T


def comparisons(scores, per_rule, components):
    rules = sorted(per_rule)
    indices = {rule: i for i, rule in enumerate(rules)}
    correct = np.array([
        [per_rule[rule][PRIMARY] - per_rule[rule][name] for name in REFERENCES]
        for rule in rules
    ])
    cases = np.array([per_rule[rule]["cases"] for rule in rules])
    deltas = correct / cases[:, None]
    component_ci = bootstrap(deltas, [[indices[r] for r in c] for c in components], 42014)
    rule_ci = bootstrap(deltas, [[i] for i in range(len(rules))], 42015)
    return {
        name: {
            "macro_delta": scores[PRIMARY]["macro"] - scores[name]["macro"],
            "rule_wins": int((correct[:, i] > 0).sum()),
            "rule_ties": int((correct[:, i] == 0).sum()),
            "rule_losses": int((correct[:, i] < 0).sum()),
            "component_interval_97_5": component_ci[i].tolist(),
            "rule_interval_97_5": rule_ci[i].tolist(),
        }
        for i, name in enumerate(REFERENCES)
    }


def summarize(gold, groups, predictions, prior):
    return {
        name: {
            **prior.accuracy_summary(gold, groups, pred),
            "abstentions": int((pred == UNTESTED).sum()),
            "reviews": int((pred == prior.OUTCOMES.index("cantTell")).sum()),
        }
        for name, pred in predictions.items()
    }


def write_predictions(path, rows, test, predictions, prior):
    with path.open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["rule", "testcase", "content_hash", "expected", *predictions])
        for i, key in enumerate(test):
            row = rows[key]
            writer.writerow([
                *key, row["sha256"], row["label"],
                *(prior.OUTCOMES[values[i]] for values in predictions.values()),
            ])


def analyze(archive, output):
    prior = load_prior()
    rows, reports, train, test, audit = prior.dataset(archive)
    verify_split(rows, train, test)
    frozen, _ = prior.predictions(rows, reports, train, test)
    validate_release(rows, test, frozen, prior)
    new, panel, outcomes, exercised, features = interaction_predictions(
        rows, reports, train, test, prior
    )
    predictions = {**new, **frozen}
    gold = np.array([prior.LABELS.index(rows[key]["label"]) for key in test])
    groups = np.array([key[0] for key in test])
    components = rule_components(rows, test)
    per_rule = {}
    for rule in sorted(set(groups)):
        mask = groups == rule
        per_rule[rule] = {
            "cases": int(mask.sum()),
            **{name: int((values[mask] == gold[mask]).sum())
               for name, values in predictions.items()},
        }
    scores = summarize(gold, groups, predictions, prior)
    decisive = np.column_stack([(outcomes == i).any(axis=1) for i in range(len(prior.LABELS))])
    slices = {
        "zero_exercised": exercised == 0,
        "one_exercised": exercised == 1,
        "two_or_more_exercised": exercised >= 2,
        "conflicting_decisive_labels": decisive.sum(axis=1) >= 2,
        "original_four_exercised": (outcomes[:, [panel.index(t) for t in prior.OLD]] != UNTESTED).all(axis=1),
    }
    paired = comparisons(scores, per_rule, components)
    result = {
        "protocol_sha256": PROTOCOL_SHA,
        "source_archive_sha256": prior.ARCHIVE,
        "prior_evaluator_sha256": EVALUATOR_SHA,
        "prior_predictions_sha256": PREDICTIONS_SHA,
        "split": audit,
        "reports": reports,
        "panel": panel,
        "feature_counts": features,
        "scores": scores,
        "per_rule_exact_counts": per_rule,
        "bootstrap_draws": DRAWS,
        "linked_rule_components": components,
        "primary_comparisons": paired,
        "improvement_gate_passed": all(p["component_interval_97_5"][0] > 0 for p in paired.values()),
        "support_slices": {
            name: {
                "cases": int(mask.sum()),
                "rules": len(set(groups[mask])),
                "scores": summarize(gold[mask], groups[mask], {
                    name: p[mask] for name, p in predictions.items()
                }, prior) if mask.any() else {},
            }
            for name, mask in slices.items()
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    write_predictions(output / "predictions.csv", rows, test, predictions, prior)
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with threadpool_limits(limits=1), warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        analyze(args.archive, args.output)
