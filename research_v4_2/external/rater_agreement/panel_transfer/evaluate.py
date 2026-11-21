"""Reproduce the frozen Wikipedia second-worker forecast from staged TSVs."""

import argparse
import csv
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from statistics import NormalDist

HERE = Path(__file__).resolve().parent
SPLITS = ("train", "dev", "test")
COMMENTS = "attack_annotated_comments.tsv"
RATINGS = "attack_annotations.tsv"
COMMENT_HEADER = ("rev_id", "comment", "year", "logged_in", "ns", "sample", "split")
RATING_HEADER = (
    "rev_id", "worker_id", "quoting_attack", "recipient_attack",
    "third_party_attack", "other_attack", "attack",
)
BINARY_LITERALS = {"0.0": 0, "1.0": 1}
STRENGTHS = (0, 0.25, 1, 2, 8, 32, 128, 512, 2048, math.inf)
FIXED_STRENGTH = 2
INTEGER = re.compile(r"[+-]?[0-9]+")
SIGNATURES = tuple(product((0, 1), repeat=5))
METRICS = ("brier", "log_loss")


@dataclass
class Item:
    group: int
    pairs: int
    # Each row gives a first-worker signature and second-worker negative/positive counts.
    outcomes: tuple


def verify_hashes(directory, manifest, expected_names):
    entries = [line.split() for line in manifest.read_text().splitlines()]
    if [name for _, name in entries] != list(expected_names):
        raise ValueError(f"Unexpected entries in {manifest.name}")
    for expected, name in entries:
        with (directory / name).open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != expected:
            raise ValueError(f"SHA-256 mismatch for {name}")


def read_tsv(path, header):
    with path.open(encoding="utf-8", newline="") as stream:
        # The publisher escapes tabs, newlines and double quotes in comment text.
        reader = csv.reader(stream, delimiter="\t", quoting=csv.QUOTE_NONE)
        if tuple(next(reader, ())) != header:
            raise ValueError(f"Unexpected header in {path.name}")
        for line, row in enumerate(reader, 2):
            if len(row) != len(header):
                raise ValueError(f"{path.name}:{line}: unexpected field count")
            yield line, row


def integer(value, location):
    if not INTEGER.fullmatch(value):
        raise ValueError(f"{location}: expected integer ID")
    return int(value)


def normalized_text(comment):
    comment = unicodedata.normalize("NFKC", comment)
    comment = comment.replace("NEWLINE_TOKEN", " ").replace("TAB_TOKEN", " ")
    return " ".join(comment.casefold().split())


def read_comments(directory):
    revisions = {}
    text_groups = {}
    group_splits = defaultdict(set)
    for line, (revision, comment, _, _, _, _, split) in read_tsv(
        directory / COMMENTS, COMMENT_HEADER
    ):
        revision = integer(revision, f"{COMMENTS}:{line}")
        if revision in revisions or split not in SPLITS:
            raise ValueError(f"{COMMENTS}:{line}: duplicate revision or invalid split")
        group = text_groups.setdefault(normalized_text(comment), len(text_groups))
        revisions[revision] = (split, group)
        group_splits[group].add(split)
    if {split for split, _ in revisions.values()} != set(SPLITS):
        raise ValueError("Expected all three official splits")
    return revisions, group_splits


def signature_key(signature):
    vote, *flags = signature
    return f"{vote}:" + "".join(map(str, flags))


def read_panels(directory, revisions, audit):
    panels = defaultdict(lambda: defaultdict(set))
    discrepancies = {split: Counter() for split in SPLITS}
    for line, (revision, worker, *ratings) in read_tsv(directory / RATINGS, RATING_HEADER):
        location = f"{RATINGS}:{line}"
        revision = integer(revision, location)
        worker = integer(worker, location)
        if worker < 0 or any(value not in BINARY_LITERALS for value in ratings):
            raise ValueError(f"{location}: invalid worker ID or non-binary rating")
        if revision not in revisions:
            raise ValueError(f"{location}: revision absent from comments table")
        split, _ = revisions[revision]
        audit[split]["source_rating_rows"] += 1
        *flags, vote = (BINARY_LITERALS[value] for value in ratings)
        signature = (vote, *flags)
        if vote != any(flags):
            discrepancies[split][signature_key(signature)] += 1
        worker_records = panels[revision][worker]
        if signature in worker_records:
            audit[split]["redundant_rating_rows"] += 1
        worker_records.add(signature)
    if panels.keys() != revisions.keys():
        raise ValueError("Comments and annotations do not have identical revision sets")
    for split, counts in discrepancies.items():
        audit[split]["binary_or_discrepancy_rows"] = sum(counts.values())
        audit[split]["binary_or_discrepancies_by_signature"] = dict(sorted(counts.items()))
    return panels


def item_counts(group, signatures):
    counts = Counter(signatures)
    size = counts.total()
    positives = sum(signature[0] * count for signature, count in counts.items())
    outcomes = []
    for signature, count in sorted(counts.items()):
        # A first worker cannot also be the second worker.
        positive_pairs = count * (positives - signature[0])
        outcomes.append((signature, count * (size - 1) - positive_pairs, positive_pairs))
    return Item(group, size * (size - 1), tuple(outcomes))


def load_items(directory):
    revisions, group_splits = read_comments(directory)
    split_audit = {
        split: dict.fromkeys((
            "source_items", "source_rating_rows", "redundant_rating_rows",
            "conflicting_revision_workers", "distinct_rating_rows_removed_for_conflicts",
            "cross_split_items_excluded", "empty_panels", "singleton_panels",
        ), 0)
        for split in SPLITS
    }
    panels = read_panels(directory, revisions, split_audit)
    items = {split: [] for split in SPLITS}
    groups = {split: set() for split in SPLITS}
    eligible_workers = {split: set() for split in SPLITS}
    for revision, (split, group) in revisions.items():
        audit = split_audit[split]
        audit["source_items"] += 1
        groups[split].add(group)
        clean = {}
        for worker, records in panels.pop(revision).items():
            if len(records) == 1:
                clean[worker] = records.pop()
            else:
                audit["conflicting_revision_workers"] += 1
                audit["distinct_rating_rows_removed_for_conflicts"] += len(records)
        if len(group_splits[group]) > 1:
            audit["cross_split_items_excluded"] += 1
        elif not clean:
            audit["empty_panels"] += 1
        elif len(clean) == 1:
            audit["singleton_panels"] += 1
        else:
            items[split].append(item_counts(group, clean.values()))
            eligible_workers[split].update(clean)

    for split, audit in split_audit.items():
        split_items = items[split]
        split_groups = groups[split]
        audit.update(
            source_groups=len(split_groups),
            cross_split_groups_excluded=sum(len(group_splits[g]) > 1 for g in split_groups),
            eligible_items=len(split_items),
            eligible_groups=len({item.group for item in split_items}),
            eligible_workers=len(eligible_workers[split]),
            ordered_pairs=sum(item.pairs for item in split_items),
        )
    cross_split_groups = Counter(
        "+".join(split for split in SPLITS if split in members)
        for members in group_splits.values()
        if len(members) > 1
    )
    train, dev, test = (eligible_workers[split] for split in SPLITS)
    audit = {
        "splits": split_audit,
        "source_groups_across_all_splits": len(group_splits),
        "cross_split_groups_by_membership": dict(sorted(cross_split_groups.items())),
        "eligible_worker_overlap": {
            "train_dev": len(train & dev),
            "train_test": len(train & test),
            "dev_test": len(dev & test),
            "train_dev_test": len(train & dev & test),
            "train_plus_dev_test": len((train | dev) & test),
        },
    }
    return items, audit


def summarize(items):
    # Accumulate integer counts by denominator before converting to item mass.
    negative = Counter()
    positive = Counter()
    for item in items:
        for signature, n, y in item.outcomes:
            negative[signature, item.pairs] += n
            positive[signature, item.pairs] += y
    keyed_pairs = defaultdict(list)
    for signature, pairs in sorted(negative):
        keyed_pairs[signature].append((pairs, negative[signature, pairs], positive[signature, pairs]))
    return {
        signature: {
            "ordered_pairs": sum(n + y for _, n, y in keyed_pairs[signature]),
            "positive_pairs": sum(y for _, _, y in keyed_pairs[signature]),
            "negative_mass": math.fsum(n / pairs for pairs, n, _ in keyed_pairs[signature]),
            "positive_mass": math.fsum(y / pairs for pairs, _, y in keyed_pairs[signature]),
        }
        for signature in SIGNATURES
    }


def fit(support):
    cells = {}
    for signature, row in support.items():
        positive = row["positive_mass"]
        cells[signature] = (row["negative_mass"] + positive, positive)
    binary = {}
    for vote in (0, 1):
        n = math.fsum(n for s, (n, _) in cells.items() if s[0] == vote)
        y = math.fsum(y for s, (_, y) in cells.items() if s[0] == vote)
        binary[vote] = {"mass": n, "positive_mass": y, "probability": y / n}
    marginal = (
        math.fsum(row["positive_mass"] for row in binary.values())
        / math.fsum(row["mass"] for row in binary.values())
    )
    return cells, binary, marginal


def clip(probability):
    return max(0.01, min(0.99, probability))


def smoother(cells, binary, strength):
    predictions = {}
    for signature, (n, y) in cells.items():
        backoff = binary[signature[0]]["probability"]
        probability = backoff if not n or math.isinf(strength) else (
            (y + strength * backoff) / (n + strength)
        )
        predictions[signature] = clip(probability)
    return predictions


def outcome_losses(probability, metric):
    if metric == "brier":
        return probability**2, (1 - probability)**2
    return -math.log1p(-probability), -math.log(probability)


def support_mean(support, predictions, metric, mass):
    terms = []
    for signature, row in support.items():
        negative, positive = outcome_losses(predictions[signature], metric)
        terms.extend((row["negative_mass"] * negative, row["positive_mass"] * positive))
    return math.fsum(terms) / mass


def tune(train, dev, dev_items):
    cells, binary, _ = fit(train)
    scores = {}
    for strength in STRENGTHS:
        predictions = smoother(cells, binary, strength)
        scores[strength] = support_mean(dev, predictions, "brier", dev_items)
    chosen = min(STRENGTHS, key=lambda strength: (scores[strength], -strength))
    return chosen, [
        {"strength": json_strength(strength), "brier": scores[strength]} for strength in STRENGTHS
    ]


def json_strength(strength):
    return "infinity" if math.isinf(strength) else strength


def score_test(items, support, models):
    group_sizes = Counter(item.group for item in items)
    n, g = len(items), len(group_sizes)
    critical = {
        "marginal_95": NormalDist().inv_cdf(1 - 0.05 / 2),
        "bonferroni_simultaneous_95": NormalDist().inv_cdf(1 - 0.05 / (2 * 2)),
    }
    scores = {name: {} for name in models}
    contrasts = {name: {} for name in models if name != "fixed"}
    for metric in METRICS:
        loss_tables = {
            name: {signature: outcome_losses(p, metric) for signature, p in predictions.items()}
            for name, predictions in models.items()
        }
        item_losses = {}
        for name, table in loss_tables.items():
            item_losses[name] = [
                math.fsum(
                    negative * table[signature][0] + positive * table[signature][1]
                    for signature, negative, positive in item.outcomes
                ) / item.pairs
                for item in items
            ]
            scores[name][metric] = math.fsum(item_losses[name]) / n
        for name, contrast in contrasts.items():
            group_deltas = defaultdict(float)
            for item, candidate, comparator in zip(items, item_losses["fixed"], item_losses[name]):
                group_deltas[item.group] += candidate - comparator
            delta = math.fsum(group_deltas.values()) / n
            se = math.sqrt(g / (g - 1) * math.fsum(
                (total - group_sizes[group] * delta)**2 for group, total in group_deltas.items()
            )) / n
            interval_type = (
                "bonferroni_simultaneous_95"
                if metric == "brier" and name in {"binary", "dev_tuned"}
                else "marginal_95"
            )
            halfwidth = critical[interval_type] * se
            contrast[metric] = {
                "difference": delta, "cluster_se": se,
                "interval": [delta - halfwidth, delta + halfwidth],
                "interval_type": interval_type,
            }

    strata = {}
    for vote in (0, 1):
        vote_support = {s: row for s, row in support.items() if s[0] == vote}
        mass = math.fsum(row["negative_mass"] + row["positive_mass"] for row in vote_support.values())
        vote_scores = {
            name: {
                metric: support_mean(vote_support, predictions, metric, mass) for metric in METRICS
            }
            for name, predictions in models.items()
        }
        strata[vote] = {
            "ordered_pairs": sum(row["ordered_pairs"] for row in vote_support.values()),
            "mass": mass,
            "mass_share": mass / n,
            "scores": vote_scores,
            "fixed_minus_comparator": {
                name: {metric: vote_scores["fixed"][metric] - vote_scores[name][metric]
                       for metric in METRICS}
                for name in contrasts
            },
        }
    return {
        "items": n, "groups": g, "ordered_pairs": sum(item.pairs for item in items),
        "scores": scores, "fixed_minus_comparator": contrasts, "normal_critical_values": critical,
        "first_vote_strata": strata,
    }


def evaluate(directory):
    verify_hashes(HERE, HERE / "protocol.sha256", ("protocol.md", "sources.sha256"))
    verify_hashes(directory, HERE / "sources.sha256", (COMMENTS, RATINGS))
    items, audit = load_items(directory)
    train, dev, test = (items[split] for split in SPLITS)
    chosen, grid = tune(summarize(train), summarize(dev), len(dev))
    final_support = summarize(train + dev)
    cells, binary, marginal = fit(final_support)
    models = {
        "fixed": smoother(cells, binary, FIXED_STRENGTH),
        "dev_tuned": smoother(cells, binary, chosen),
        "binary": smoother(cells, binary, math.inf),
        "unsmoothed": smoother(cells, binary, 0),
        "marginal": dict.fromkeys(SIGNATURES, clip(marginal)),
        "repeat": {signature: clip(signature[0]) for signature in SIGNATURES},
    }
    test_support = summarize(test)
    test_results = score_test(test, test_support, models)
    return {
        "audit": audit,
        "dev_tuning": {"selected_strength": json_strength(chosen), "grid": grid},
        "final_fit": {
            "items": len(train) + len(dev),
            "fixed_strength": FIXED_STRENGTH,
            "binary_cells": binary,
            "marginal_probability": marginal,
            "signature_cells": {
                signature_key(s): {
                    **final_support[s],
                    "mass": n,
                    "predictions": {name: predictions[s] for name, predictions in models.items()},
                }
                for s, (n, _) in cells.items()
            },
        },
        "test": {
            **test_results,
            "signature_support": {
                signature_key(s): {**row, "mass": row["negative_mass"] + row["positive_mass"]}
                for s, row in test_support.items()
            },
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.source_directory), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
